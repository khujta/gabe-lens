#!/usr/bin/env bash
# entity-models battery — the four entity models (claim · seeded · derived · proposed) and their prerequisite,
# the UNGATED element census (docs/design/entity-models/plan.md). Hermetic: a throwaway project tree + synthetic
# maps, python-stdlib only, zero-arg. Every FIRE has a SILENT sibling; every rule has a named mutation lever
# (a checker that cannot fail is non-evidence). Doctor auto-runs it (tests/*/run.sh).
#
# Phase 0 (2026-09-06) — element_census: the CLAIM ROOTS walked recursively; an unclaimed .py becomes an element
# row with its callables, tables, routes; bare files never listed; unparseable files listed with their reason;
# P5 honest-empty; byte-identical on a re-run. Mutation lever proven by hand: rglob → glob reddens the FIRE.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
GEN="$DIR/../../templates/center/generators"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
( cd "$GEN" && python3 - "$T" <<'PY'
import sys, json, pathlib
T = pathlib.Path(sys.argv[1])
sys.path.insert(0, ".")
import _a3_code as C
p = f = 0
def ck(c, m):
    global p, f
    if c: p += 1
    else: f += 1; print("  FAIL:", m)
def w(rel, text):
    q = T / rel; q.parent.mkdir(parents=True, exist_ok=True); q.write_text(text)

# ── the tree: pkg/api/a.py claimed · pkg/api/sub/b.py UNCLAIMED (recursive) · pkg/svc/c.py claimed by glob ·
#    pkg/svc/deep/d.py unclaimed with a table + a route · pkg/api/__init__.py bare · pkg/api/test_x.py a test ·
#    pkg/api/sub/bad.py unparseable · other/z.py OUTSIDE every claim root (never scanned) ──
w("pkg/api/a.py", "from fastapi import APIRouter\nrouter = APIRouter()\n@router.get('/a')\ndef get_a():\n    return 1\n")
w("pkg/api/sub/b.py", "def helper():\n    return 1\n\n\nclass Svc:\n    def run(self):\n        return 2\n\n    def __repr__(self):\n        return 'x'\n")
w("pkg/svc/c.py", "def c_one():\n    return 1\n")
w("pkg/svc/deep/d.py", "from fastapi import APIRouter\nrouter = APIRouter(prefix='/deep')\n\n\nclass Thing:\n    __tablename__ = 'things'\n\n\n@router.post('/things')\ndef make_thing():\n    return 1\n")
w("pkg/api/__init__.py", "")
w("pkg/api/test_x.py", "def test_x():\n    assert 1\n")
w("pkg/api/sub/bad.py", "def broken(:\n    pass\n")
w("other/z.py", "def zed():\n    return 1\n")
EC = {"alpha": {"api": ["pkg/api/a.py"], "services": ["pkg/svc/*.py"]}}

ck(C._claim_roots(EC) == ["pkg/api", "pkg/svc"], f"claim roots = the literal prefixes, shallowest ancestors ({C._claim_roots(EC)})")
ck(C._claim_roots({"e": {"api": ["pkg/api/a.py", "pkg/api/sub/*.py"], "web": ["web/src/**/*.ts"]}}) == ["pkg/api"],
   "a nested claim collapses into its ancestor; a frontend claim without .py never bounds the census")

out = C.element_census(T, entity_code=EC)
files = [r["file"] for r in out.get("elements", [])]
ck(files == ["pkg/api/sub/b.py", "pkg/api/sub/bad.py", "pkg/svc/deep/d.py"], f"FIRE: unclaimed files under the claim roots, recursively, sorted ({files})")
b = next(r for r in out["elements"] if r["file"] == "pkg/api/sub/b.py")
ck(b["fns"] == ["helper", "Svc.run"] and b["fns_n"] == 2 and b["tables"] == [] and b["routes"] == 0 and b["lines"] == 10, f"FIRE: callables named (no dunder), counts + lines carried ({b})")
d = next(r for r in out["elements"] if r["file"] == "pkg/svc/deep/d.py")
ck(d["tables"] == ["Thing"] and d["routes"] == 1 and d["fns"] == ["make_thing"], f"FIRE: a table class and a route in an unclaimed file are counted ({d})")
bad = next(r for r in out["elements"] if r["file"] == "pkg/api/sub/bad.py")
ck(bad["reason"].startswith("unparseable: syntax error") and bad["fns"] == [] and out["stats"]["unparseable"] == 1, f"an unparseable unclaimed file is listed with its reason and counted ({bad})")
ck(out["scanned_roots"] == ["pkg/api", "pkg/svc"] and out["claimed"] == {"py": 2} and out["stats"] == {"files": 3, "fns": 3, "tables": 1, "routes": 1, "unparseable": 1},
   f"the block carries roots · claimed count · stats ({out.get('scanned_roots')} {out.get('claimed')} {out.get('stats')})")
ck("pkg/api/__init__.py" not in files and "pkg/api/test_x.py" not in files and "other/z.py" not in files and "pkg/api/a.py" not in files,
   "SILENT: a bare __init__, a test file, a file outside every claim root and a claimed file are never listed")
ck(C.unparseable_files() == [] or all("bad.py" not in r[0] for r in C.unparseable_files()), "the census never records into unparseable_files (that list is for MAPPED files)")
ck(json.dumps(C.element_census(T, entity_code=EC), sort_keys=True) == json.dumps(out, sort_keys=True), "byte-identical on a re-run")
ck(C.element_census(T, entity_code={"alpha": {"api": ["pkg/api/a.py", "pkg/api/sub/*.py", "pkg/api/sub/bad.py"], "services": ["pkg/svc/**/*.py"]}}) == {},
   "P5 SILENT: everything claimed → no key at all (never {elements: []})")
ck(C.element_census(T, entity_code={"alpha": {"web": ["web/**/*.ts"]}}) == {}, "P5 SILENT: no python-bearing claim → {}")
ck(C.element_census(T, entity_code={}) == {}, "P5 SILENT: no config → {}")
# the mutation lever's shape: a non-recursive walk cannot see pkg/api/sub/b.py — assert the recursion is real
w("pkg/api/sub/sub2/e.py", "def e_one():\n    return 1\n")
ck("pkg/api/sub/sub2/e.py" in [r["file"] for r in C.element_census(T, entity_code=EC)["elements"]], "the walk is recursive at every depth (rglob → glob reddens this)")
ck(all("orphan" not in json.dumps(x) for x in (out, C.element_census.__doc__ or "")), "R10: no 'orphan' in the census or its doc")

# ── Phase 1 (2026-09-06) · _a3_models: dataflow · hubs · seeded · derived · proposed on a synthetic map ──
import _a3_models as M, _a3_homing as H
def ep(slug, method, path, fn, file, ops, mw=None):
    return {"method": method, "path": path, "fn": fn, "file": file, "touches": [], "middleware": mw or [],
            "_ops": ops}
AMAP = {"entities": {
    "alpha": {"files": [["api", "a/api.py", 9], ["services", "a/svc.py", 9]], "models": [{"cls": "T1", "table": "t1"}],
              "endpoints": [ep("alpha", "GET", "/x/a", "get_a", "a/api.py", [("T1", "w")], [{"name": "auth", "fn": "a/deps.py::auth", "gate": True, "via": "param-dep"}]),
                            ep("alpha", "POST", "/x/b", "post_b", "a/api.py", [("T1", "w")], [{"name": "auth", "fn": "a/deps.py::auth", "gate": True, "via": "param-dep"}]),
                            ep("alpha", "GET", "/y/c", "get_c", "a/api.py", [("T2", "w")]),
                            ep("alpha", "GET", "/z", "get_z", "a/api.py", [], [{"name": "auth", "fn": "a/deps.py::auth", "gate": True, "via": "param-dep"}]),
                            ep("alpha", "GET", "/y/g", "get_g", "a/api.py", [("T2", "r")]),                         # a READ-only atom in a written cluster
                            ep("alpha", "GET", "/r/1", "get_r", "a/api.py", [("T3", "r")])]},                       # a cluster nobody writes — anchored on reads
    "beta":  {"files": [["api", "b/api.py", 9], ["services", "b/svc.py", 9]], "models": [{"cls": "T2", "table": "t2"}],
              "endpoints": [ep("beta", "POST", "/y/d", "post_d", "b/api.py", [("T2", "w")], [{"name": "auth", "fn": "a/deps.py::auth", "gate": True, "via": "param-dep"}]),
                            ep("beta", "GET", "/y/f", "get_f", "b/api.py", [("T1", "r"), ("T1", "r"), ("T2", "w")])]},   # reads t1 twice, writes t2 once → anchored on t2 (a write is ownership)
    "gamma": {"files": [["services", "g/svc.py", 9]], "models": [], "endpoints": []},
    "delta": {"files": [["api", "d/api.py", 9]], "models": [{"cls": "T5", "table": "t5"}, {"cls": "T6", "table": "t6"}],
              "endpoints": [ep("delta", "GET", "/p/%d" % i, "p%d" % i, "d/api.py", [("T5", "w")]) for i in range(3)] +
                           [ep("delta", "GET", "/q/%d" % i, "q%d" % i, "d/api.py", [("T6", "w")]) for i in range(3)]},
    "holder": {"files": [["models", "h/models.py", 9]], "models": [{"cls": "T9", "table": "t9"}], "endpoints": []},
  },
  "function_insight": {
    "a/api.py::get_a": {"entity": "alpha", "access": {"ops": [{"model": "T1", "rw": "w"}]}},
    "a/svc.py::helper": {"entity": "alpha", "access": {"ops": []}},
    "a/svc.py::mover": {"entity": "alpha", "access": {"ops": [{"model": "T2", "rw": "r"}]}},
    "a/deps.py::auth": {"entity": "alpha", "access": {"ops": []}},
    "b/svc.py::b1": {"entity": "beta", "access": {"ops": []}}, "b/svc.py::b2": {"entity": "beta", "access": {"ops": []}},
  }, "task_roots": []}
def node(slug, e):
    return {"id": "endpoint:%s %s" % (e["method"], e["path"]), "kind": "endpoint", "label": "%s %s" % (e["method"], e["path"]), "fn": e["fn"], "det": {"file": e["file"]},
            "access": {"ops": [{"model": m, "table": m.lower(), "rw": rw} for m, rw in e["_ops"]]}}
GRAPH = {"head": "h1", "l1": {"nodes": [{"id": s, "kind": "entity", "slug": s} for s in AMAP["entities"]], "edges": []},
         "l2": {s: {"nodes": [node(s, e) for e in ent["endpoints"]] + [{"id": "model:%s" % m["cls"], "kind": "model", "table": m["table"]} for m in ent["models"]],
                    "edges": []} for s, ent in AMAP["entities"].items()},
         "cross_edges": [{"kind": "bridge", "from": "web:w/x", "from_slug": "alpha", "to": "endpoint:GET /x/a", "to_slug": "alpha", "export": "fe:w/x.ts#useX"},
                         {"kind": "bridge", "from": "web:w/x", "from_slug": "alpha", "to": "endpoint:POST /x/b", "to_slug": "alpha", "export": "fe:w/x.ts#useXPost"}],   # a second export of the SAME file, not an fe piece
         "fe": {"pieces": [{"id": "fe:w/x.ts#useX", "file": "w/x.ts", "home": "fe·alpha", "kind": "hook"},
                           {"id": "fe:w/p.tsx#P", "file": "w/p.tsx", "home": "fe·alpha", "kind": "component"},
                           {"id": "fe:w/q.tsx#Q", "file": "w/q.tsx", "home": "fe·beta", "kind": "component"},
                           {"id": "fe:w/api.ts#api", "file": "w/api.ts", "home": "design-system", "kind": "module", "mclass": "api"},
                           {"id": "fe:w/g.tsx#G", "file": "w/g.tsx", "home": "fe·gamma", "kind": "component"},
                           {"id": "fe:w/wander.tsx#W", "file": "w/wander.tsx", "home": "fe·alpha", "kind": "component"},
                           {"id": "fe:w/util.tsx#U", "file": "w/util.tsx", "home": "fe·alpha", "kind": "component"}],       # rendered from 3 homes, in-degree 3 — under the default floor (20)
                "edges": [[1, 0, "renders"], [2, 0, "uses-hook"], [1, 3, "fecall"], [2, 3, "fecall"], [4, 3, "fecall"], [2, 5, "renders"], [4, 5, "renders"],
                          [1, 6, "renders"], [2, 6, "renders"], [4, 6, "renders"]],
                "homes": [{"id": "fe·alpha", "kind": "fe", "pair": "alpha"}, {"id": "fe·beta", "kind": "fe", "pair": "beta"}, {"id": "fe·gamma", "kind": "fe", "pair": "gamma"}, {"id": "design-system", "kind": "bucket"}]},
         "stats": {"fe": {"present": True, "homing": "layout"}}}
GRAPH["l2"]["alpha"]["nodes"].append({"id": "schema:AOut", "kind": "schema"}); GRAPH["l2"]["alpha"]["edges"].append({"kind": "touches", "source": "endpoint:GET /x/a", "target": "schema:AOut"})
GRAPH["l2"]["__unclaimed__"] = {"nodes": [{"id": "endpoint:GET /orph/%d" % i, "kind": "endpoint", "label": "GET /orph/%d" % i, "fn": "o%d" % i, "det": {"file": "o/api.py"},
                                          "access": {"ops": [{"model": "T7", "table": "t7", "rw": "w"}]}} for i in range(2)], "edges": []}
LEVELS = {"fn_edges": [{"s": "a/api.py#get_a", "t": "a/svc.py#helper", "ss": "alpha", "ds": "alpha", "rel": "calls", "conf": "extracted"},
                       {"s": "b/svc.py#b1", "t": "a/svc.py#mover", "ss": "beta", "ds": "alpha", "rel": "calls", "conf": "extracted"},
                       {"s": "b/svc.py#b2", "t": "a/svc.py#mover", "ss": "beta", "ds": "alpha", "rel": "calls", "conf": "extracted"},
                       {"s": "a/api.py#get_a", "t": "a/deps.py#auth", "ss": "alpha", "ds": "alpha", "rel": "depends", "conf": "extracted"},
                       {"s": "b/api.py#post_d", "t": "a/deps.py#auth", "ss": "beta", "ds": "alpha", "rel": "depends", "conf": "extracted"},
                       {"s": "a/api.py#get_z", "t": "a/deps.py#auth", "ss": "alpha", "ds": "alpha", "rel": "depends", "conf": "extracted"},
                       {"s": "g/svc.py#g1", "t": "a/deps.py#auth", "ss": "gamma", "ds": "alpha", "rel": "calls", "conf": "inferred"}]}   # a third HOME consumes the gate — the homes bar (3) is the hub rule
HOM = H.evidence(AMAP, GRAPH, LEVELS)
mod = M.build(AMAP, GRAPH, LEVELS, hom=HOM)
V = mod["views"]; R = mod["rosters"]; HM = mod["homes"]
hubs = {r["id"]: r for r in mod["shared"]}
ck(hubs.get("a/deps.py#auth", {}).get("class") == "gate" and hubs["a/deps.py#auth"]["domains"] == 3, f"hub FIRE: a gate Depends on endpoints of two entities across 3 domains is a gate hub at floor 1 ({hubs.get('a/deps.py#auth')})")
ck(hubs.get("fe:w/api.ts#api", {}).get("class") == "api-client", f"hub FIRE: an fe module with mclass api consumed from 3 homes is an api-client hub ({hubs.get('fe:w/api.ts#api')})")
ck("a/svc.py#mover" not in hubs and "fe:w/wander.tsx#W" not in hubs, "hub SILENT: two consumers (mover) / two homes below the default floor (W) are not hubs — the homes bar and the floor both hold")
ck("fe:w/util.tsx#U" not in hubs, "hub SILENT (the FLOOR): a piece consumed from 3 homes with in-degree 3 stays under the default floor (20) — the homes bar alone does not make a hub")
ck(not hasattr(M, "_W"), "no dead weights: every edge counts once in the in-degree (write-primacy is per ATOM, in _atoms)")
ck(V["seeded"]["present"] and HM["seeded"].get("a/svc.py#mover") == "beta" and "a/svc.py#mover" not in mod["held"]["seeded"], f"seeded FIRE: Part C's move (2 beta callers + beta data) lands in homes.seeded ({HM['seeded']})")
ck(V["seeded"]["moved"] == len(HM["seeded"]) and "NOT free propagation" in V["seeded"]["note"], f"seeded: the view counts its delta and its note names the rate ({V['seeded']})")
ck(mod["bands"]["seeded"].get("move_share") == 0.6 and mod["bands"]["seeded"].get("move_min_users") == 2, "seeded: the band is copied from _a3_homing.rule verbatim")
feats = {r["id"]: r for r in R["derived"] if r["kind"] == "feature"}
ck(feats["d:t1"]["name"] == "x" and feats["d:t1"]["named_by"] == "domain" and feats["d:t1"]["depth"] == 1 and feats["d:t1"]["endpoints"] == 2 and feats["d:t1"]["purity"] == 1.0,
   f"derived FIRE: two alpha atoms writing t1 under /x → one feature named by its singleton domain ({feats.get('d:t1')})")
ck(feats["d:t2"]["claim_mix"] == {"alpha": 2, "beta": 2} and feats["d:t2"]["purity"] == 0.5 and feats["d:t2"]["name"] == "y", f"derived FIRE: a table written from two entities is ONE feature with a mixed claim ({feats.get('d:t2')})")
ck(HM["derived"].get("endpoint:GET /y/f") == "d:t2" and feats["d:t2"]["anchor_by"] == "write" and feats["d:t2"]["anchor_by_mix"] == {"read": 1, "write": 3},
   f"anchor_by FIRE: an atom reading t1 twice and writing t2 once anchors on t2 — a write is ownership; the read-only atom rides the row's anchor_by_mix ({feats['d:t2'].get('anchor_by')} · {feats['d:t2'].get('anchor_by_mix')})")
ck(feats["d:t3"]["anchor_by"] == "read" and "anchored on reads" in feats["d:t3"]["why"] and feats["d:t3"]["name"] == "r" and "anchor_by_mix" not in feats["d:t3"],
   f"anchor_by SILENT: a cluster nobody writes anchors on its read-majority table and the row SAYS so ({feats['d:t3'].get('why')})")
ck(feats["d:t1"]["anchor_cls"] == "T1" and feats["d:t1"]["anchor_table"] == "t1" and "write t1" in feats["d:t1"]["why"], f"the row carries the table AND the class, and the why's verb comes from anchor_by ({feats['d:t1'].get('why')})")
ck(feats["d:t1"]["screens"] == 1 and feats["d:t1"]["fetchers"] == 2 and "fe:w/x.ts#useXPost" not in HM["derived"] and "fe:w/x.ts#useXPost" not in HM["proposed"],
   f"screens counts FILES (two exports of w/x.ts = 1 screen · 2 fetchers) and an export that is not an fe piece is never homed ({feats['d:t1']['screens']} · {feats['d:t1']['fetchers']})")
ck(all(r["named_by"] in ("domain", "table") for r in feats.values()), "named_by ∈ {domain, table} — no unreachable rung")
_m1 = feats["d:t1"]["members"]; _ne = sum(1 for m in _m1 if m.startswith("endpoint:"))
ck(_ne >= 2 and all(m.startswith("endpoint:") for m in _m1[:_ne]) and not any(m.startswith("endpoint:") for m in _m1[_ne:]) and _m1[:_ne] == sorted(_m1[:_ne]),
   f"members: endpoint ids FIRST, each run sorted — a capped list never clips the labels a name is computed from (naming-plan; a plain sorted() reddens this) ({_m1[:4]})")
ck(all(HM["derived"].get(m) in (r["id"], r["twin"]) for r in feats.values() for m in r["members"]) and "members_more" in feats["d:t1"] and feats["d:t1"]["members_more"] == 0,
   "members are rebuilt from the FINAL homes — a card never names a piece the map homes elsewhere; the clipped-count sibling rides every row")
ck(HM["derived"].get("endpoint:GET /x/a") == "d:t1" and HM["derived"].get("schema:AOut") == "d:t1" and HM["derived"].get("a/api.py#get_a") == "d:t1" and HM["derived"].get("a/svc.py#helper") == "d:t1",
   f"derived: the endpoint, its schema, its handler and the handler's callee home to the feature ({ {k: HM['derived'].get(k) for k in ('endpoint:GET /x/a', 'schema:AOut', 'a/api.py#get_a', 'a/svc.py#helper')} })")
ck(feats["d:t1"]["twin"] == "fe·d:t1" and HM["derived"].get("fe:w/x.ts#useX") == "fe·d:t1" and HM["derived"].get("fe:w/p.tsx#P") == "fe·d:t1" and HM["derived"].get("fe:w/q.tsx#Q") == "fe·d:t1",
   f"derived: the fetching hook and the pieces that render / use it join the frontend TWIN fe·d:<table> ({ {k: HM['derived'].get(k) for k in ('fe:w/x.ts#useX', 'fe:w/p.tsx#P', 'fe:w/q.tsx#Q')} })")
ck("endpoint:GET /z" in mod["abstain"]["derived"] and "endpoint:GET /z" not in HM["derived"] and V["derived"]["abstained"] == 1, "derived ABSTAIN: an endpoint with no access ops keeps its claim and is listed, never guessed into a domain")
asp = {r["id"]: r for r in R["derived"] if r["kind"] == "aspect"}
ck("a:auth" in asp and asp["a:auth"]["detector"] == "gate-fan-in" and asp["a:auth"]["domains"] == 3 and HM["derived"].get("a/deps.py#auth") == "a:auth" and asp["a:auth"]["drawn"],
   f"derived ASPECT FIRE: a gate on endpoints of 3 URL domains moves to a:<gate>, drawn ({asp.get('a:auth')})")
ck("a:fe-shared" in asp and "fe:w/api.ts#api" in asp["a:fe-shared"]["members"] and "fe:w/api.ts#api" not in HM["derived"] and not asp["a:fe-shared"]["drawn"],
   f"derived ASPECT: a frontend piece consumed from ≥3 homes is REPORTED and held, never moved ({asp.get('a:fe-shared')})")
lay = {r["id"]: r for r in R["derived"] if r["kind"] == "layer"}
ck("l:gamma" in lay and "l:holder" in lay and lay["l:holder"]["tables"] == 1 and "consumption not weighed" in lay["l:holder"]["why"], f"derived LAYER rows: ONE predicate — no endpoint — files-only and table-holder alike, said honestly ({sorted(lay)})")
ck(feats["d:t5"]["name"] == "p" and feats["d:t6"]["name"] == "q", f"derived naming: two anchors under two domains name by their own singleton domains ({feats['d:t5']['name']} · {feats['d:t6']['name']})")
prop = {r["slug"]: r for r in R["proposed"]}
ck(prop["alpha"]["verdict"] == "ASPECT" and "auth" in prop["alpha"]["why"], f"proposed: an entity homing a 3-domain gate is an ASPECT (precedence over its features) ({prop['alpha']})")
ck(prop["delta"]["verdict"] == "SPLIT" and prop["delta"]["evidence"]["features"] == ["d:t5", "d:t6"] and HM["proposed"].get("endpoint:GET /p/0") == "d:t5" and HM["proposed"].get("endpoint:GET /q/0") == "d:t6",
   f"proposed SPLIT FIRE: 3+3 atoms on two anchors under two domains → SPLIT, and the as-if-accepted homes move each atom into its feature ({prop['delta']['evidence']})")
ck(prop["beta"]["verdict"] == "MERGE" and prop["beta"]["evidence"]["survivor"] == "alpha" and HM["proposed"].get("endpoint:POST /y/d") == "alpha",
   f"proposed MERGE FIRE: beta's one atom sits in a feature whose majority ties → alpha survives (sole-owns a domain) and beta's atom moves to it ({prop['beta']['evidence']})")
ck(prop["gamma"]["verdict"] == "LAYER" and prop["holder"]["verdict"] == "LAYER" and "table(s) held" in prop["holder"]["why"], f"proposed LAYER: no door — files-only and table-holder alike ({prop['gamma']['why']} · {prop['holder']['why']})")
ck(set(lay) == {"l:%s" % s for s, r in prop.items() if r["verdict"] == "LAYER"}, f"derive's layer rows and propose's LAYER verdicts are the SAME predicate ({sorted(lay)} vs {[s for s, r in prop.items() if r['verdict'] == 'LAYER']})")
ck(all("endpoint" not in k or not k.startswith("endpoint:GET /z") for k in HM["proposed"]) and not any(v.startswith("l:") or v.startswith("a:") for v in HM["proposed"].values()),
   "proposed: ASPECT / LAYER move nothing (no a:/l: home in the as-if-accepted delta)")
cands = {c["id"]: c for c in R["candidates"]}
ck("d:t7" in cands and HM["proposed"].get("endpoint:GET /orph/0") == "d:t7" and cands["d:t7"]["named_by"] == "domain" and cands["d:t7"]["name"] == "orph",
   f"proposed CANDIDATE FIRE: a feature whose atoms are all unclaimed is proposed, named by its domain, and its pieces move to it ({cands.get('d:t7')})")
ck(V["proposed"]["verdicts"] == {"FEATURE": 0, "SPLIT": 1, "MERGE": 1, "ASPECT": 1, "LAYER": 2} and V["proposed"]["candidates"] == 1, f"proposed: the tally ({V['proposed']['verdicts']} · {V['proposed']['candidates']})")
ck(cands["d:t7"]["suggested_slug"] == "orph" and "members_more" in cands["d:t7"] and mod["stats"]["truncated"] == [] and "shared_more" in mod,
   "candidates carry a suggested slug from the name and every clipped list its _more sibling; nothing truncated on this fixture")
ck(all(HM["proposed"].get(m) in (c["id"], "fe·" + c["id"]) for c in cands.values() for m in c["members"]),
   "homes.proposed agrees with the candidate roster — a candidate's members home to it, never to a partner's MERGE")
# ── the variant estate: unequal MERGE pairs · the loser re-stamp · the co-claimed ASPECT rule · a singleton under a shared domain ──
AMAP_M = json.loads(json.dumps(AMAP)); GRAPH_M = json.loads(json.dumps(GRAPH))
def add(slug, files, models, eps):
    AMAP_M["entities"][slug] = {"files": files, "models": models, "endpoints": eps}
    GRAPH_M["l1"]["nodes"].append({"id": slug, "kind": "entity", "slug": slug})
    GRAPH_M["l2"][slug] = {"nodes": [node(slug, e) for e in eps] + [{"id": "model:%s" % m["cls"], "kind": "model", "table": m["table"]} for m in models], "edges": []}
add("eps", [["api", "e/api.py", 9]], [], [ep("eps", "PUT", "/q/e%d" % i, "e%d" % i, "e/api.py", [("T6", "w")]) for i in range(2)])                       # 2 atoms in delta's d:t6 (3) → the partner has MORE atoms
add("yank", [["api", "k/api.py", 9]], [{"cls": "T8", "table": "t8"}], [ep("yank", "GET", "/w/%d" % i, "w%d" % i, "k/api.py", [("T8", "w")]) for i in (1, 2)])   # 2 atoms, sole-owns nothing
add("zed", [["api", "z/api.py", 9]], [], [ep("zed", "GET", "/w/3", "w3", "z/api.py", [("T8", "w")]), ep("zed", "GET", "/v/1", "v1", "z/api.py", [("T8", "w")])])  # 2 atoms, sole-owns /v
add("theta", [["api", "t/api.py", 9]], [{"cls": "T10", "table": "t10"}], [ep("theta", "GET", "/%s/t" % d, "t_%s" % d, "t/api.py", [("T10", "w")]) for d in ("x", "z", "p")])   # co-claims 3, sole-owns 0
add("iota", [["api", "i/api.py", 9]], [{"cls": "T11", "table": "t11"}], [ep("iota", "GET", "/%s/i" % d, "i_%s" % d, "i/api.py", [("T11", "w")]) for d in ("x", "p", "m1")])   # co-claims 2 + sole-owns 1 = 3 claimed — the LOOSE rule's false positive
AMAP_M["entities"]["alpha"]["endpoints"].append(ep("alpha", "GET", "/y/solo/1", "solo", "a/api.py", [("T4", "w")]))                                            # a singleton under a domain with >1 anchor
GRAPH_M["l2"]["alpha"]["nodes"].append(node("alpha", AMAP_M["entities"]["alpha"]["endpoints"][-1]))
mod_m = M.build(AMAP_M, GRAPH_M, LEVELS, hom=HOM); prop_m = {r["slug"]: r for r in mod_m["rosters"]["proposed"]}; feats_m = {r["id"]: r for r in mod_m["rosters"]["derived"] if r["kind"] == "feature"}; HM_m = mod_m["homes"]
ck(prop_m["eps"]["verdict"] == "MERGE" and prop_m["eps"]["evidence"]["survivor"] == "delta" and "more atoms" in prop_m["eps"]["why"] and HM_m["proposed"].get("endpoint:PUT /q/e0") == "delta" and prop_m["delta"]["verdict"] == "SPLIT",
   f"MERGE (unequal): the partner with MORE atoms in the feature survives; the loser's atoms move; the survivor's own verdict stands ({prop_m['eps'].get('why')})")
ck(prop_m["zed"]["verdict"] == "MERGE" and prop_m["zed"]["evidence"]["survivor"] == "zed" and "sole-owns" in prop_m["zed"]["why"], f"MERGE (tie on atoms): the one that sole-owns a domain survives ({prop_m['zed'].get('why')})")
ck(prop_m["yank"]["verdict"] == "MERGE" and prop_m["yank"]["evidence"].get("survivor") == "zed" and "partner's verdict" in prop_m["yank"]["why"] and prop_m["yank"]["suggested_edit"] == {"merge_into": "zed"}
   and HM_m["proposed"].get("endpoint:GET /w/1") == "zed",
   f"MERGE loser RE-STAMP: the majority slug that LOST the tie read FEATURE on its own row — it now says MERGE naming the survivor, and its atoms are homed there ({prop_m['yank']})")
ck(prop_m["theta"]["verdict"] == "ASPECT" and "co-claims 3" in prop_m["theta"]["why"] and prop_m["theta"]["evidence"]["co_claims"] == ["p", "x", "z"],
   f"ASPECT (entity_shape rule): co-claims ≥3 domains and sole-owns ≤1 → ASPECT ({prop_m['theta'].get('why')})")
ck(prop_m["iota"]["verdict"] == "FEATURE" and sorted(M._entity_shape_rule(AMAP_M)[2].get("iota", set())) == ["p", "x"], f"ASPECT SILENT: 2 co-claimed + 1 sole-owned = 3 claimed domains is a FEATURE — only CO-claimed domains count toward the ≥3 (entity_shape.py's rule) ({prop_m['iota'].get('verdict')})")
ck(feats_m["d:t4"]["name"] == "t4" and feats_m["d:t4"]["named_by"] == "table" and feats_m["d:t4"]["endpoints"] == 1 and feats_m["d:t1"]["named_by"] == "table",
   f"naming: a singleton under a domain holding >1 anchor never descends to its own endpoint path — the table names it (and a 2-atom cluster with no shared level-2 prefix likewise) ({feats_m['d:t4']['name']} · {feats_m['d:t1']['name']})")
ck(feats_m["d:t8"]["name"] == "w" and feats_m["d:t8"]["named_by"] == "domain", f"naming: a 4-atom cluster with a 3-atom majority prefix names by the domain ({feats_m['d:t8']['name']})")
# attach + levels slice: c4 side vs function side, disjoint; strip test lives in tests/arch-graph
g2 = json.loads(json.dumps(GRAPH)); M.attach(g2, mod)
ck(g2["stats"]["models"]["present"] and g2["stats"]["models"]["views"] == ["claim", "seeded", "derived", "proposed"] and "a/svc.py#mover" not in g2["models"]["homes"]["seeded"] and "endpoint:GET /x/a" in g2["models"]["homes"]["derived"],
   "attach: c4 carries the c4-id half of every delta (endpoints / schemas / fe pieces), never a function id")
sl = M.levels_slice(mod, GRAPH)
ck(sl["present"] and sl["homes"]["seeded"].get("a/svc.py#mover") == "beta" and sl["homes"]["derived"].get("a/api.py#get_a") == "d:t1" and "endpoint:GET /x/a" not in sl["homes"]["derived"],
   "levels slice: the function-id half only")
ck(all(not (set(g2["models"]["homes"][v]) & set(sl["homes"][v])) for v in ("seeded", "derived", "proposed")) and sl["head"] == g2["models"]["head"] and sl["dropped"] == [], "the two halves are DISJOINT and share the head; nothing dropped")
mod_g = json.loads(json.dumps(mod)); mod_g["homes"]["derived"]["endpoint:GET /ghost"] = "d:t1"; mod_g["homes"]["derived"]["fe:w/ghost.tsx#G"] = "fe·d:t1"
sl_g = M.levels_slice(mod_g, GRAPH)
ck("endpoint:GET /ghost" not in sl_g["homes"]["derived"] and "fe:w/ghost.tsx#G" not in sl_g["homes"]["derived"] and sl_g["dropped"] == ["endpoint:GET /ghost", "fe:w/ghost.tsx#G"],
   f"levels slice: a c4-SHAPED id the map does not carry is DROPPED and named, never passed off as a function ({sl_g['dropped']})")
ck(json.dumps(M.build(AMAP, GRAPH, LEVELS, hom=HOM), sort_keys=True) == json.dumps(mod, sort_keys=True), "byte-identical on a re-run (no wallclock, sorted ties)")
none = M.build(AMAP, GRAPH, None, hom=HOM); g3 = json.loads(json.dumps(GRAPH)); M.attach(g3, none)
ck(none["present"] is False and "levels" in none["reason"] and g3["stats"]["models"]["present"] is False and "models" not in g3 and M.levels_slice(none, GRAPH)["present"] is False,
   "honest-empty: no levels graph → present False with the reason, NO models key on c4, the slice says so")
mod_nh = M.build(AMAP, GRAPH, LEVELS, hom=None); mod_fh = M.build(AMAP, GRAPH, LEVELS, hom={"present": False, "reason": "no witness on this feed"})
ck(mod_nh["views"]["seeded"]["present"] is False and "no Part C homing block" in mod_nh["views"]["seeded"]["reason"] and "seeded" not in mod_nh["homes"] and "seeded" not in mod_nh["held"]
   and mod_nh["bands"]["seeded"].get("move_share") == H.MOVE_SHARE and "constants" in mod_nh["bands"]["seeded"]["text"],
   f"seeded honest-empty (hom None): the reason says the feed predates Part C, the view carries NO homes/held key, the band falls back to _a3_homing's constants ({mod_nh['views']['seeded']})")
ck(mod_fh["views"]["seeded"]["reason"] == "no witness on this feed" and "derived" in mod_fh["homes"] and "seeded" not in mod_fh["abstain"],
   f"seeded honest-empty (hom present False): the block's own reason is byte-copied; the present views keep their keys ({mod_fh['views']['seeded']})")
# mutation levers, applied in memory: every floor → 1 makes W (2 homes) still not a hub but the homes bar alone must hold; drop the tier clause → the bucket target would receive
import copy
_fl = dict(M.HUB_FLOOR); M.HUB_FLOOR.update({k: 1 for k in _fl}); mod_f = M.build(AMAP, GRAPH, LEVELS, hom=HOM); M.HUB_FLOOR.update(_fl)
ck("fe:w/wander.tsx#W" not in {r["id"] for r in mod_f["shared"]}, "lever (floors → 1): the HOMES bar still keeps a two-home piece out — the bar, not the floor, is the rule")
ck("fe:w/util.tsx#U" in {r["id"] for r in mod_f["shared"]}, "lever (floors → 1): the 3-home piece under the default floor becomes a hub — the floor is LIVE, not decoration")
HOM3 = json.loads(json.dumps(HOM)); HOM3["pieces"]["a/deps.py#auth"] = {"kind": "function", "home": "alpha", "by": "layout", "users": {"beta": 3}, "data": {}, "verdict": "move", "to": "beta", "to_kind": "entity", "share": 1.0, "others": 1}
mod_h = M.build(AMAP, GRAPH, LEVELS, hom=HOM3)
ck("a/deps.py#auth" in mod_h["held"]["seeded"] and "a/deps.py#auth" not in mod_h["homes"]["seeded"] and mod_h["views"]["seeded"]["held"] == 1, f"seeded HELD: a hub carrying a Part C move verdict is held out, never moved ({mod_h['held']['seeded']})")
_rc, _mc = M.ROSTER_CAP, M.MEMBER_CAP; M.ROSTER_CAP, M.MEMBER_CAP = 2, 1; mod_c = M.build(AMAP, GRAPH, LEVELS, hom=HOM); M.ROSTER_CAP, M.MEMBER_CAP = _rc, _mc
_fc = {r["id"]: r for r in mod_c["rosters"]["derived"] if r["kind"] == "feature"}
ck(["rosters.derived", len(feats) - 2] in mod_c["stats"]["truncated"] and len(_fc) == 2 and all(r["members_more"] >= 1 for r in _fc.values()), f"caps are PRINTED when they clip: stats.truncated names the roster cap, every clipped row its members_more ({mod_c['stats']['truncated']})")
HOM2 = json.loads(json.dumps(HOM)); HOM2["pieces"]["fe:w/p.tsx#P"] = {"kind": "fe:component", "home": "alpha", "by": "layout", "users": {"design-system": 2}, "data": {}, "verdict": "move", "to": "design-system", "to_kind": "fe-area", "share": 1.0, "others": 1}
mod_t = M.build(AMAP, GRAPH, LEVELS, hom=HOM2)
ck("fe:w/p.tsx#P" in mod_t["abstain"]["seeded"] and "fe:w/p.tsx#P" not in mod_t["homes"]["seeded"], "seeded ABSTAIN: a move whose target is a bucket (design-system) is refused and LISTED — buckets never receive")
ck(all("orphan" not in json.dumps(x) for x in (mod, M.__doc__)), "R10: no 'orphan' in the block or its doc")
print(f"entity-models battery: {p} passed, {f} failed")
sys.exit(1 if f else 0)
PY
)
