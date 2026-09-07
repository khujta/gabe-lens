#!/usr/bin/env python3
"""adapter.py — the Python TWIN of adapter.js for the baker (bake-fdp.py) and any offline check.

Same fold, same count law: L2 pieces deduplicated by id (an unknown kind is kept) + fe pieces homed by `home` − the web files
absorbed by the fe piece that fetches them (+ function nodes from levels.json when asked). Same link set (l2 edges · cross
edges re-targeted to the bridge's export or the absorbing piece · fe triples · fn/schema/access/handler wires). Deterministic.
If this file and adapter.js ever disagree on a count, adapter.js is the law (it is what the pages draw) — fix this one.

    from adapter import load_c4, build
    feed = build(load_c4("…/c4-graph.js"), load_levels("…/levels.json") or None, fn=False, fe=True)
    feed["nodes"]  # [{id, kind, ent, entClaim, sub, label, fe, tier}]   feed["links"]  # [{source, target, rel, kind, fe, cross}]
"""
import json, re, sys

KINDS = {  # kind → layer (the station's KINDS[kind].layer; mirrors adapter.js)
    "route": "web", "component": "web", "hook": "web", "store": "web", "type": "web", "screen": "web", "web": "web", "module": "web", "unknown": "web",
    "endpoint": "endpoints", "function": "api", "middleware": "api", "flag": "api", "element": "api",
    "schema": "data", "model": "data", "external": "data", "provider": "data", "prompt": "data", "entity": "data"}
FE_KIND = {"fe-type": "type", "fe-unknown": "unknown"}
FE_REL = {"uses-hook": "uses", "uses-store": "reads"}
REL2KIND = {"fk": "fk", "pk": "fk", "nests": "fk", "handler": "calls", "touch": "calls", "touches": "calls", "resp": "calls", "uses": "calls", "calls": "calls",
            "consumes": "calls", "fetches": "bridge", "bridge": "bridge", "renders": "imports", "mounts": "imports", "reads": "imports", "imports": "imports",
            "typed": "imports", "fecall": "calls", "bundle": "calls", "reads_from": "rollup", "writes_to": "rollup", "fnreads": "access", "fnwrites": "access",
            "depends": "calls", "gated_by": "calls", "dispatches": "dispatches", "serializes": "fk", "reaches": "calls", "walls": "access", "fnprompts": "calls"}
TIERS = [
    {"koff": {"function", "schema", "hook", "module", "unknown", "type", "middleware", "flag", "provider", "prompt", "external", "store", "element"}, "fcoff": {"private", "connector", "container", "leaf"}},
    {"koff": {"function", "hook", "module", "unknown", "type", "prompt", "element"}, "fcoff": {"private", "leaf"}},
    {"koff": {"module", "unknown", "type"}, "fcoff": {"leaf"}},
    {"koff": set(), "fcoff": set()}]


def _js_object(path, marker="{"):
    s = open(path, encoding="utf-8").read()
    i = s.index(marker)
    return json.JSONDecoder().raw_decode(s[i:])[0]


def load_c4(path):
    return _js_object(path)


def load_levels(path):
    try:
        if path.endswith(".json"):
            return json.load(open(path, encoding="utf-8"))
        return _js_object(path)
    except (OSError, ValueError):
        return None


def tier_of(kind, fe, fe_class, generic):
    k = "unknown" if generic else kind
    for t, T in enumerate(TIERS):
        if k in T["koff"]:
            continue
        if fe and fe_class and fe_class in T["fcoff"]:
            continue
        return t
    return 3


def build(c4, levels=None, fn=False, fe=True):
    ents = [e.get("slug") or e["id"] for e in (c4.get("l1") or {}).get("nodes", [])] or list((c4.get("l2") or {}).keys())
    ent_kind = {e: "entity" for e in ents}
    nodes, by_id, warn = [], {}, []

    def add(n):
        if n["id"] in by_id:
            return None
        by_id[n["id"]] = n
        nodes.append(n)
        return n

    for ent, blk in (c4.get("l2") or {}).items():
        for p in blk.get("nodes", []):
            generic = p["kind"] not in KINDS
            if generic:
                warn.append("kind %r unknown — kept generically" % p["kind"])
            add({"id": p["id"], "kind": p["kind"], "ent": ent, "entClaim": ent, "sub": KINDS.get(p["kind"], "data"), "label": p.get("label") or p["id"],
                 "fe": False, "fn": p.get("fn"), "det": p.get("det") or {}, "screen": None, "feClass": None, "generic": generic, "access": None})
    FE = c4.get("fe") if fe and c4.get("fe") and c4["fe"].get("pieces") else None
    if FE:
        for h in FE.get("homes", []):
            if h.get("kind") != "entity" and h["id"] not in ents:
                ents.append(h["id"]); ent_kind[h["id"]] = h.get("kind", "bucket")
        for p in FE["pieces"]:
            kind = FE_KIND.get(p["kind"], p["kind"])
            if p.get("home") not in ents:
                ents.append(p["home"]); ent_kind[p["home"]] = "bucket"; warn.append("fe home %r not in fe.homes — added" % p["home"])
            generic = kind not in KINDS
            add({"id": p["id"], "kind": kind, "ent": p["home"], "entClaim": p["home"], "sub": KINDS.get(kind, "data"), "label": p.get("name") or p["id"],
                 "fe": True, "fn": None, "screen": p.get("screen"), "feClass": p.get("feClass"), "generic": generic, "access": None})
    if fn and levels and levels.get("fn_nodes"):
        for f in levels["fn_nodes"]:
            ent = f.get("slug") or "__unclaimed__"
            if ent not in ents:
                ents.append(ent); ent_kind[ent] = "entity"
            add({"id": f["id"], "kind": "function", "ent": ent, "entClaim": ent, "sub": "api", "label": f.get("name") or f["id"].split("#")[-1],
                 "fe": False, "fn": None, "screen": None, "feClass": None, "generic": False, "access": f.get("access")})
    links = []

    def link(s, t, rel, **extra):
        l = {"source": s, "target": t, "rel": rel, "kind": REL2KIND.get(rel, "calls")}
        l.update(extra); links.append(l)

    for ent, blk in (c4.get("l2") or {}).items():
        for e in blk.get("edges", []):
            link(e["source"], e["target"], e.get("kind") or "calls")
    for e in c4.get("cross_edges", []):
        link(e["from"], e["to"], e.get("kind") or "fk", cross=True, xp=e.get("export"))
    absorbed = 0
    if FE:
        P = FE["pieces"]
        for e in FE.get("edges", []):
            a, b = P[e[0]] if e[0] < len(P) else None, P[e[1]] if e[1] < len(P) else None
            if a and b:
                link(a["id"], b["id"], FE_REL.get(e[2], e[2]), fe=True, chrome=(len(e) > 3 and e[3] == "chrome"), write=(len(e) > 3 and e[3] == "write"))
        ABS = {n["screen"]: n["id"] for n in nodes if n["fe"] and n.get("screen") and n["screen"] in by_id and by_id[n["screen"]]["kind"] == "web"}
        for l in links:
            if l.get("xp") and l["xp"] in by_id:
                l["source"] = l["xp"]
            elif l["source"] in ABS:
                l["source"] = ABS[l["source"]]
            if l["target"] in ABS:
                l["target"] = ABS[l["target"]]
        for w in ABS:
            by_id.pop(w, None)
        nodes = [n for n in nodes if n["id"] not in ABS]
        absorbed = len(ABS)
    if fn and levels and levels.get("fn_nodes"):
        for e in levels.get("fn_edges", []):
            link(e["s"], e["t"], e.get("rel") or "calls")
        for e in levels.get("schema_edges", []):
            link(e["s"], e["t"], e.get("rel") or "uses")
        for n in nodes:
            if n["kind"] == "function" and n.get("access") and n["access"].get("ops"):
                for op in n["access"]["ops"]:
                    if op.get("model") and ("model:" + op["model"]) in by_id:
                        link(n["id"], "model:" + op["model"], "fnwrites" if op.get("rw") == "w" else "fnreads")
            if n["kind"] == "endpoint" and n.get("fn"):
                key = str((n.get("det") or {}).get("file") or "").split(":")[0] + "#" + n["fn"]   # the station's key: det.file#fn
                if key in by_id:
                    link(n["id"], key, "handler")
    links = [l for l in links if l["source"] in by_id and l["target"] in by_id and l["source"] != l["target"]]
    for n in nodes:
        n["tier"] = tier_of(n["kind"], n["fe"], n.get("feClass"), n["generic"])
    return {"nodes": nodes, "links": links, "ents": ents, "entKind": ent_kind, "byId": by_id, "head": c4.get("head"),
            "counts": {"nodes": len(nodes), "links": len(links), "ents": len(ents), "absorbed": absorbed}, "warnings": warn}


if __name__ == "__main__":
    c4 = load_c4(sys.argv[1])
    lv = load_levels(sys.argv[2]) if len(sys.argv) > 2 else None
    f = build(c4, lv, fn=bool(lv))
    print(json.dumps(f["counts"]), "warnings:", len(f["warnings"]))
