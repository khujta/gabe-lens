#!/usr/bin/env python3
"""bake-fdp.py — bake a DETERMINISTIC layout for a fixture with graphviz `fdp` + cluster subgraphs → layouts/<feed>.fdp.js

The scale sweep's strongest finding (docs/design/graph-renderers/sweeps/scale-labs/): fdp WITH `subgraph cluster_*` keeps every entity
intact — k=10 neighbour purity 0.996 on the example — while every live force sim scores below the seeded ring (0.888) and `sfdp`
silently IGNORES clusters (0.475). This baker is the generator-time half of ruling D7 (bake-when-present, live fallback): a page
loads layouts/<feed>.fdp.js and takes `?layout=baked`; the adapter reads window.GABE_BAKED[<feed>].pos[id] = [x, y, z].

    python3 bake-fdp.py                 # example (the committed station feed)
    python3 bake-fdp.py onyx --fn       # fixtures/onyx with the function layer

z is the sub-layer band (endpoints 75 · api 30 · web 75 · data −75 — half the station's LZ) plus a deterministic id-hash jitter, so a
3D page reads the layers as altitude while a 2D page ignores z. Positions are normalised into a 2000-unit box. Byte-identical on an
unchanged feed (`start=1` seeds fdp's RNG). Purity is printed and belongs in the commit message. EPL-1.0 tool at bake time only —
nothing is linked. A missing `fdp` is a loud exit 2, never a silent fallback.
"""
import collections, hashlib, json, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adapter import build, load_c4, load_levels

HERE = os.path.dirname(os.path.abspath(__file__))
EXAMPLE = os.path.join(HERE, "../../../../templates/center/shell/example/codebase-graph-station")
LZ = {"endpoints": 75, "api": 30, "web": 75, "data": -75}


def feed_paths(name):
    base = EXAMPLE if name == "example" else os.path.join(HERE, "fixtures", name)
    return os.path.join(base, "c4-graph.js"), os.path.join(base, "levels.json"), os.path.join(base, "levels.js")


def dot_for(feed):
    ids = {n["id"]: "n%d" % i for i, n in enumerate(feed["nodes"])}
    lines = ["graph G {", "  graph [overlap=prism, splines=false, start=1, K=0.6];", "  node [shape=point, width=0.08, fixedsize=true];"]
    by_ent = collections.defaultdict(lambda: collections.defaultdict(list))
    for n in feed["nodes"]:
        by_ent[n["ent"]][n["sub"]].append(ids[n["id"]])
    for ei, ent in enumerate(feed["ents"]):
        if ent not in by_ent:
            continue
        lines.append('  subgraph "cluster_e%d" {' % ei)
        for si, (sub, members) in enumerate(sorted(by_ent[ent].items())):
            if len(members) > 1:
                lines.append('    subgraph "cluster_e%d_s%d" {' % (ei, si))
                lines += ["      %s;" % m for m in members]
                lines.append("    }")
            else:
                lines += ["    %s;" % m for m in members]
        lines.append("  }")
    seen = set()
    for l in feed["links"]:
        a, b = ids.get(l["source"]), ids.get(l["target"])
        if not a or not b:
            continue
        key = (a, b) if a < b else (b, a)
        if key in seen:
            continue
        seen.add(key)
        lines.append("  %s -- %s;" % (a, b))
    lines.append("}")
    return "\n".join(lines).encode(), {v: k for k, v in ids.items()}


def run_fdp(dot):
    """fdp's prism overlap removal SEGFAULTS INTERMITTENTLY on this feed (graphviz 2.43 — the same DOT passes on one run and dies
    with -11 on the next), so the baker retries the same input three times before it gives up loudly. Determinism holds on a
    successful run (start=1); the retry never changes the input."""
    t0 = time.time()
    last = None
    for attempt in range(1, 4):
        try:
            r = subprocess.run(["fdp", "-Tjson"], input=dot, capture_output=True, timeout=600)
        except FileNotFoundError:
            print("bake-fdp: graphviz `fdp` is not on PATH — nothing baked (install graphviz; the pages stay on the live layout and say so)")
            sys.exit(2)
        if r.returncode == 0 and r.stdout:
            if attempt > 1:
                print("  (fdp crashed %d time(s) on this input before succeeding — the intermittent prism segfault)" % (attempt - 1))
            return json.loads(r.stdout), (time.time() - t0) * 1000
        last = r
    print("bake-fdp: fdp failed 3 times (last exit %s): %s" % (last.returncode, last.stderr[:300].decode(errors="replace") or "(no stderr — a crash inside fdp)"))
    sys.exit(2)


def purity(pos, grp, K=10):
    pts = [(pos[i][0], pos[i][1], grp[i]) for i in pos if i in grp]
    if len(pts) < K + 2:
        return 0.0
    xs = [p[0] for p in pts]
    cell = max(1.0, (max(xs) - min(xs)) / 60)
    grid = collections.defaultdict(list)
    for i, (x, y, _) in enumerate(pts):
        grid[(int(x // cell), int(y // cell))].append(i)
    tot = 0.0
    for i, (x, y, g) in enumerate(pts):
        cx, cy = int(x // cell), int(y // cell)
        cand, r = [], 1
        while len(cand) < K + 1 and r < 12:
            cand = []
            for a in range(cx - r, cx + r + 1):
                for b in range(cy - r, cy + r + 1):
                    cand += grid.get((a, b), [])
            r += 1
        d = sorted(((x - pts[j][0]) ** 2 + (y - pts[j][1]) ** 2, j) for j in cand if j != i)[:K]
        if d:
            tot += sum(1 for _, j in d if pts[j][2] == g) / len(d)
    return tot / len(pts)


def jitter(nid):
    return (int(hashlib.sha1(nid.encode()).hexdigest()[:6], 16) % 1000) / 1000.0 - 0.5


def main():
    name = next((a for a in sys.argv[1:] if not a.startswith("--")), "example")
    fn = "--fn" in sys.argv
    c4p, lvj, lvjs = feed_paths(name)
    c4 = load_c4(c4p)
    lv = (load_levels(lvj) if os.path.exists(lvj) else load_levels(lvjs)) if fn else None
    feed = build(c4, lv, fn=fn)
    print("feed %s @ %s: %d nodes · %d links · %d ents%s" % (name, feed["head"], feed["counts"]["nodes"], feed["counts"]["links"], feed["counts"]["ents"], " · fn" if fn else ""))
    dot, rev = dot_for(feed)
    doc, ms = run_fdp(dot)
    raw = {}
    for obj in doc.get("objects", []):
        p, nm = obj.get("pos"), obj.get("name")
        if p and nm in rev:
            x, y = p.split(",")[:2]
            raw[rev[nm]] = (float(x), float(y))
    if not raw:
        print("bake-fdp: fdp returned no positions"); sys.exit(2)
    xs, ys = [p[0] for p in raw.values()], [p[1] for p in raw.values()]
    k = 2000.0 / max(max(xs) - min(xs), max(ys) - min(ys), 1e-9)
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    pos = {}
    for n in feed["nodes"]:
        p = raw.get(n["id"])
        if not p:
            continue
        pos[n["id"]] = [round((p[0] - cx) * k, 2), round((p[1] - cy) * k, 2), round(LZ.get(n["sub"], 0) + jitter(n["id"]) * 40, 2)]
    grp = {n["id"]: n["ent"] for n in feed["nodes"]}
    pur = round(purity(pos, grp), 3)
    sub = {n["id"]: n["ent"] + "|" + n["sub"] for n in feed["nodes"]}
    pur_sub = round(purity(pos, sub), 3)
    key = name + (":fn" if fn else "")   # the adapter reads GABE_BAKED[fixture + (":fn" when the function layer is on)], falling back to the plain key
    meta = {"feed": name, "key": key, "head": feed["head"], "engine": "fdp+clusters(entity>sub)", "nodes": len(pos), "links": feed["counts"]["links"], "ents": feed["counts"]["ents"],
            "fn": fn, "purity_entity_k10": pur, "purity_subcluster_k10": pur_sub, "z": "sub-layer band ±20 jitter", "box": 2000}   # no wall clock in the file — byte-identical on an unchanged feed; the ms is printed only
    out = os.path.join(HERE, "layouts", "%s.%sfdp.js" % (name, "fn." if fn else ""))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    body = json.dumps({"meta": meta, "pos": pos}, sort_keys=True, separators=(",", ":"))
    with open(out, "w", encoding="utf-8") as f:
        f.write("/* GENERATED by bake-fdp.py — graphviz fdp + cluster subgraphs, deterministic (start=1). Do not hand-edit. */\n")
        f.write("window.GABE_BAKED=window.GABE_BAKED||{};window.GABE_BAKED[%s]=%s;\n" % (json.dumps(key), body))
    print("  fdp %d ms · entity purity k10 %.3f · sub-cluster purity %.3f · wrote %s (%d B)" % (ms, pur, pur_sub, os.path.relpath(out, HERE), os.path.getsize(out)))


if __name__ == "__main__":
    main()
