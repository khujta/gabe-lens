#!/usr/bin/env bash
# _a3_levels battery — the rich LEVELS graph (window.GABE_LEVELS) derivation.
# Hermetic (a synthetic archmap + the real _a3_graph topology), zero-arg,
# python-stdlib only. Proves the rich lenses come from the archmap insight blocks
# (function_insight → fn_nodes · model_insight.internal_refs → use_edges · URL →
# usecases · FK components → communities · guard_insight → guards), the honest-empty
# contract (missing block ⇒ empty field, graft-less ⇒ no fn_edges), determinism, and
# that stripping a block is DETECTABLE (mutation-proven — a checker that cannot fail
# is non-evidence). Doctor auto-runs it.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
GEN="$DIR/../../templates/center/generators"
python3 - "$GEN" <<'PY'
import sys, json, copy
sys.path.insert(0, sys.argv[1])
import _a3_graph, _a3_levels
p = f = 0
def ck(c, m):
    global p, f
    if c: p += 1
    else: f += 1; print("  FAIL:", m)

AMAP = {
  "head": "testsha",
  "entities": {
    "orders": {"models": [{"cls": "Order", "table": "orders", "cols": [["id", "uuid", ""]], "fks": {"user_id": "users.id"}},
                          {"cls": "OrderLine", "table": "order_lines", "cols": [["id", "uuid", ""]], "fks": {"order_id": "orders.id"}}],
               "schemas": [{"cls": "OrderResponse", "fields": []}],
               "endpoints": [{"method": "GET", "path": "/orders", "fn": "list_orders", "file": "api/orders.py", "touches": ["Order"], "resp": "OrderResponse"},
                             {"method": "POST", "path": "/orders/{id}/lines", "fn": "add_line", "file": "api/orders.py", "touches": ["OrderLine"], "resp": ""}],
               "files": [["api", "api/orders.py", 100]], "defines": {}},
    "users": {"models": [{"cls": "User", "table": "users", "cols": [["id", "uuid", ""]]}],
              "schemas": [], "endpoints": [{"method": "GET", "path": "/users", "fn": "list_users", "file": "api/users.py", "touches": ["User"], "resp": ""}],
              "files": [["api", "api/users.py", 50]], "defines": {}}},
  "function_insight": {
    "api/orders.py::list_orders": {"fn": "list_orders", "entity": "orders", "file": "api/orders.py", "layer": "api", "handler": True, "god": False, "internal": 2, "api": 3, "web": 0, "doc": "List all orders for the user.", "lines": 12, "returns": "OrderResponse", "async": True},
    "api/orders.py::add_line": {"fn": "add_line", "entity": "orders", "file": "api/orders.py", "layer": "api", "handler": True, "god": False, "internal": 0, "api": 1, "web": 0},
    "api/users.py::list_users": {"fn": "list_users", "entity": "users", "file": "api/users.py", "layer": "api", "handler": True, "god": False, "internal": 0, "api": 1, "web": 0},
    "svc/o.py::writer": {"fn": "writer", "entity": "orders", "file": "svc/o.py", "layer": "services", "handler": False, "god": False, "internal": 1, "api": 0, "web": 0, "access": {"ops": [{"model": "W", "table": "w", "rw": "w"}], "commits": True}}},
  "model_insight": {
    "Order": {"cls": "Order", "entity": "orders", "usage": 5, "god": True, "internal_refs": [{"file": "api/users.py", "defs": ["list_users"]}]},
    "User": {"cls": "User", "entity": "users", "usage": 1, "god": False, "internal_refs": []}},
  "guard_insight": {"files": {"api/orders.py": {"declared": 2, "entity": "orders", "names": ["a", "b"]}}},
  "test_insight": {},
}
graph = _a3_graph.build_c4_graph(AMAP)
lv = _a3_levels.build_levels(AMAP, graph)

_names = {n["name"] for n in lv["fn_nodes"]}
ck(len(lv["fn_nodes"]) == 3 and _names == {"list_orders", "add_line", "list_users"},
   "fn_nodes = the DRAWN set: handlers + cross-entity model-users (not every fn)")
ck(all(n.get("layer") and "slug" in n for n in lv["fn_nodes"]), "each fn_node carries layer + slug")
_lu = [n for n in lv["fn_nodes"] if n["name"] == "list_users"][0]
ck(_lu["slug"] == "users" and _lu["layer"] == "api",
   "the cross-entity model-user (users.list_users → orders.Order) is drawn + enriched")
ck(any(e["fs"] == "users" and e["cls"] == "Order" and e["ts"] == "orders" for e in lv["use_edges"]),
   "use_edge from model_insight.internal_refs (users.list_users → orders.Order, cross-entity)")
_om = [m for m in lv["pieces"]["orders"]["models"] if m["cls"] == "Order"][0]
ck(_om["hub"]["god"] and _om["hub"]["usage"] == 5, "per-model hub/god from model_insight")
_ouc = lv["pieces"]["orders"]["usecases"]
ck("orders" in _ouc, "usecase keyed on the leading URL segment")
# adaptive depth: orders spreads over ONE first segment (/orders/*) so it deepens to
# 2 segments — /orders/{id}/lines groups under "orders/lines", not the coarse "orders"
ck("orders/lines" in _ouc, "usecase depth adapts DEEPER for a single-prefix entity")
_oc = lv["pieces"]["orders"]["communities"]
ck(any(set(v) >= {"Order", "OrderLine"} for v in _oc.values()), "community groups FK-linked models")
# fk_communities: union-find over INTRA-entity FKs — OrderLine.order_id → Order groups them
_ofk = lv["pieces"]["orders"]["fk_communities"]
ck(any(set(v) >= {"Order", "OrderLine"} for v in _ofk.values()),
   "fk_communities groups models joined by an intra-entity foreign key")
ck(any(e["guards"] == 2 for e in lv["pieces"]["orders"]["endpoints"]), "per-endpoint guards from guard_insight")
# schemas PRUNED to the endpoint-facing set: OrderResponse is a resp (kept); a schema no
# endpoint touches (a nested component) is dropped — matching the fixture's curated list
_osc = {s["cls"] for s in lv["pieces"]["orders"]["schemas"]}
ck("OrderResponse" in _osc, "an endpoint-returned schema is kept in the piece")
_ms = copy.deepcopy(AMAP)
_ms["entities"]["orders"]["schemas"].append({"cls": "OrderInternalBlock", "fields": []})
_lvms = _a3_levels.build_levels(_ms, _a3_graph.build_c4_graph(_ms))
ck("OrderInternalBlock" not in {s["cls"] for s in _lvms["pieces"]["orders"]["schemas"]},
   "MUTATION: a schema no endpoint touches is PRUNED from the piece")
# colors ride WITH the graph — a renderer paints entities the center's hue
_lvc = _a3_levels.build_levels(AMAP, _a3_graph.build_c4_graph(AMAP, colors={"orders": "#112233", "users": "#445566"}))
ck(_lvc["colors"].get("orders") == "#112233", "per-entity colors carried from the C4 graph")
ck(lv["fn_edges"] == [], "fn_edges honest-empty without a graft arm")
# fn_edges FROM a graft arm — a handler-rooted call joins its target to the drawn set
GRAFT = {"present": True, "functions": {
    "fn_slug": {"api/orders.py#list_orders": "orders", "api/users.py#helper": "users"},
    "calls": [{"s": "api/orders.py#list_orders", "t": "api/users.py#helper",
               "ss": "orders", "ts": "users", "conf": "extracted"},
              # a NON-handler-rooted call must be ignored (helper is not a handler)
              {"s": "api/users.py#helper", "t": "api/orders.py#list_orders",
               "ss": "users", "ts": "orders", "conf": "inferred"}]},
    # the per-function CODE-BEHIND floor (hidden mass) — attaches to the drawn fn_node
    "fn_behind": {"api/orders.py#list_orders": {"fns": 1, "depth": 1, "names": ["helper"]}}}
_lvg = _a3_levels.build_levels(AMAP, graph, graft=GRAFT)
ck(len(_lvg["fn_edges"]) == 1, "fn_edges = handler-ROOTED graft calls only (non-handler source ignored)")
_fe = _lvg["fn_edges"][0]
ck(_fe["ss"] == "orders" and _fe["ds"] == "users" and _fe["rel"] == "calls" and _fe["conf"] == "extracted",
   "fn_edge reshaped {s·ss·t·ds·rel·conf} with the graft confidence carried")
ck(any(n["id"] == "api/users.py#helper" for n in _lvg["fn_nodes"]),
   "the call TARGET joins the drawn set (else the lab drops the edge to an undrawn node)")
# per-entity HIDDEN functions (fn_slug − drawn_fn) — the star-field floor. FIRE: a homed-but-undrawn fn.
_GH = {"present": True, "functions": {
    "fn_slug": {"api/orders.py#list_orders": "orders", "api/orders.py#dead": "orders"}, "calls": []}}
_lvh = _a3_levels.build_levels(AMAP, graph, graft=_GH)
_oent = next(e for e in _lvh["entities"] if e["slug"] == "orders")
ck(_oent["counts"].get("hidden_fns") == 1,
   "hidden_fns counts fns graft homes but the trace never draws (star-field floor), per entity")
# SILENT: no graft → no fn_slug → no hidden_fns anywhere (honest-empty, byte-identical)
ck(all("hidden_fns" not in (e.get("counts") or {}) for e in lv["entities"]),
   "hidden_fns is honest-empty when graft is absent")
# 3b · WRITE-PATH enrichment — the d2w gradient draws the mid-chain calls the handler
# rule hides: descent (d2w−1), the 0→0 writer→writer hop, the 0→1 anchor→delegating-
# writer hop; a LATERAL step (1→1, non-shortest) stays undrawn. SILENT without d2w.
_GW = {"present": True, "functions": {
    "fn_slug": {"api/orders.py#list_orders": "orders", "svc/o.py#svc_write": "orders",
                "svc/o.py#writer": "orders", "svc/o.py#boundary_peer": "orders",
                "svc/o.py#delegate": "orders", "svc/o.py#deep_writer": "orders",
                "svc/o.py#lateral": "orders", "svc/o.py#reader": "orders"},
    "calls": [
        {"s": "api/orders.py#list_orders", "t": "svc/o.py#svc_write", "ss": "orders", "ts": "orders", "conf": "extracted"},
        {"s": "svc/o.py#svc_write", "t": "svc/o.py#writer", "ss": "orders", "ts": "orders", "conf": "inferred"},
        {"s": "svc/o.py#writer", "t": "svc/o.py#boundary_peer", "ss": "orders", "ts": "orders", "conf": "inferred"},
        {"s": "svc/o.py#boundary_peer", "t": "svc/o.py#delegate", "ss": "orders", "ts": "orders", "conf": "inferred"},
        {"s": "svc/o.py#delegate", "t": "svc/o.py#deep_writer", "ss": "orders", "ts": "orders", "conf": "inferred"},
        {"s": "svc/o.py#svc_write", "t": "svc/o.py#lateral", "ss": "orders", "ts": "orders", "conf": "inferred"},
        # lateral's own path to an anchor (1→0) keeps its d2w=1 DERIVABLE, yet lateral is
        # never seeded/reached → stays undrawn; reader has NO d2w entry (a pure read path)
        {"s": "svc/o.py#lateral", "t": "svc/o.py#boundary_peer", "ss": "orders", "ts": "orders", "conf": "inferred"},
        {"s": "svc/o.py#writer", "t": "svc/o.py#reader", "ss": "orders", "ts": "orders", "conf": "inferred"}]},
    "distance_to_write": {"api/orders.py#list_orders": 2, "svc/o.py#svc_write": 1,
                          "svc/o.py#writer": 0, "svc/o.py#boundary_peer": 0,
                          "svc/o.py#delegate": 1, "svc/o.py#deep_writer": 0,
                          "svc/o.py#lateral": 1}}
_lvw = _a3_levels.build_levels(AMAP, graph, graft=_GW)
_we = {(e["s"], e["t"]) for e in _lvw["fn_edges"]}
ck(("svc/o.py#svc_write", "svc/o.py#writer") in _we,
   "3b FIRE: the d2w gradient draws the mid-chain call the handler rule hides")
ck(("svc/o.py#writer", "svc/o.py#boundary_peer") in _we,
   "3b: the writer→writer (0→0) commit-boundary hop is drawn")
ck(("svc/o.py#boundary_peer", "svc/o.py#delegate") in _we and ("svc/o.py#delegate", "svc/o.py#deep_writer") in _we,
   "3b: anchor→delegating-writer (0→1) + its own descent (1→0) are drawn")
ck(("svc/o.py#svc_write", "svc/o.py#lateral") not in _we,
   "3b: a LATERAL step (1→1, non-shortest write path) stays undrawn")
ck(("svc/o.py#writer", "svc/o.py#reader") not in _we,
   "3b: a call to a NO-d2w target (pure read path) is skipped, not crashed on")
_wids = {n["id"] for n in _lvw["fn_nodes"]}
ck("svc/o.py#deep_writer" in _wids and "svc/o.py#lateral" not in _wids and "svc/o.py#reader" not in _wids,
   "3b: write-path fns join the drawn set; lateral + reader stay hidden stars")
ck(next((n for n in _lvw["fn_nodes"] if n["id"] == "svc/o.py#writer"), {}).get("d2w") == 0,
   "3b: d2w rides onto the newly drawn write-path fn_nodes (0 is real)")
# P3 (B0): a drawn fn's own access draws for ANY role, not just accessor — writer has no fn_roles
# entry (role None) yet its access.ops must attach (else the precedence swap would strip a gate's writes)
_wn = next((n for n in _lvw["fn_nodes"] if n["id"] == "svc/o.py#writer"), {})
ck(bool(_wn.get("access") and _wn["access"].get("ops")),
   "P3: a drawn fn's access.ops attach regardless of role (access-for-any-role, not accessor-only)")
ck(json.dumps(_lvw, sort_keys=True) == json.dumps(_a3_levels.build_levels(AMAP, graph, graft=_GW), sort_keys=True),
   "3b: the enriched build is byte-deterministic (double-build equality ON the d2w arm)")
# class 8 (wave C): a graft `depends` edge draws a handler→gate-dep fn_edge (the K1 chain)
_GWd = {"present": True, "functions": {"fn_slug": {}, "calls": []},
        "depends": [{"s": "api/orders.py#list_orders", "t": "svc/auth.py#get_auth_context",
                     "ss": "orders", "ts": "orders", "rel": "depends", "conf": "extracted"}]}
_lvd = _a3_levels.build_levels(AMAP, graph, graft=_GWd)
_de = [e for e in _lvd["fn_edges"] if e.get("rel") == "depends"]
ck(len(_de) == 1 and _de[0]["s"] == "api/orders.py#list_orders" and _de[0]["t"] == "svc/auth.py#get_auth_context"
   and any(n["id"] == "svc/auth.py#get_auth_context" for n in _lvd["fn_nodes"]),
   "class 8: a graft depends edge draws a handler→gate-dep fn_edge + the dep joins the drawn set")
ck([e for e in _a3_levels.build_levels(AMAP, graph, graft={"present": True, "functions": {"fn_slug": {}, "calls": []}})["fn_edges"] if e.get("rel") == "depends"] == [],
   "class 8 honest-empty: no graft.depends → no depends fn_edge")
_GW0 = {"present": True, "functions": _GW["functions"]}
_lvw0 = _a3_levels.build_levels(AMAP, graph, graft=_GW0)
ck(len(_lvw0["fn_edges"]) == 1 and _lvw0["fn_edges"][0]["t"] == "svc/o.py#svc_write",
   "3b SILENT: no distance_to_write → handler-rooted edges only (honest-empty enrichment)")
# fn CODE-BEHIND: graft.fn_behind attaches to the matching drawn fn_node; a fn with no
# fn_behind entry (a leaf) carries no `behind` — honest-empty, the panel omits the section.
_lo = [n for n in _lvg["fn_nodes"] if n["id"] == "api/orders.py#list_orders"][0]
_hp = [n for n in _lvg["fn_nodes"] if n["id"] == "api/users.py#helper"][0]
ck(_lo.get("behind") == {"fns": 1, "depth": 1, "names": ["helper"]} and "behind" not in _hp,
   "fn_behind attaches the hidden-mass floor to its fn_node; a leaf fn stays behind-less")
ck(len(lv["entities"]) == 2 and len(lv["l1_edges"]) >= 1, "entities + L1 edges carried from the C4 topology")

# P2b — the FRONTEND arm wires into GABE_LEVELS: pieces fold into their entity, the rest
# become FE-native buckets (candidates flagged), scaffold + edges ride for the render.
_GFE = {"present": True, "frontend": {
    "nodes": [
        {"id": "web/src/features/orders/Cart.tsx#Cart", "name": "Cart", "kind": "component", "path": "web/src/features/orders/Cart.tsx", "home": "fe·orders"},
        {"id": "web/src/features/shopping/Bag.tsx#Bag", "name": "Bag", "kind": "component", "path": "web/src/features/shopping/Bag.tsx", "home": "shopping"}],
    "edges": [{"s": "web/src/features/orders/Cart.tsx#Cart", "t": "web/src/features/shopping/Bag.tsx#Bag", "rel": "calls"}],
    "scaffold": [{"id": "web/src/features/orders/Cart.stories.tsx#Demo", "name": "Demo", "kind": "component", "path": "web/src/features/orders/Cart.stories.tsx", "home": "orders"}],
    "stats": {"total": 2, "by_kind": {"component": 2}, "by_home": {"orders": 1, "shopping": 1},
              "edges": 1, "by_relation": {"calls": 1}, "scaffold_total": 1, "scaffold_by_kind": {"component": 1},
              "candidate_entities": [{"name": "shopping", "pieces": 1}]}}}
_lvfe = _a3_levels.build_levels(AMAP, graph, graft=_GFE)
ck(_lvfe["frontend"]["present"] and _lvfe["frontend"]["total"] == 2,
   "P2b: the frontend arm wires into GABE_LEVELS (present + total)")
ck(_lvfe["pieces"]["orders"].get("frontend", {}).get("count") == 1
   and _lvfe["pieces"]["orders"]["frontend"]["by_kind"] == {"component": 1},
   "P2b (C split): a fe·<ent> home FOLDS into its PAIRED entity — pieces[pair].frontend (the band + circle)")
ck(all(b["name"] != "fe·orders" for b in _lvfe["fe_buckets"]),
   "P2b (C split): a paired home must NEVER render as a 'no backend entity' bucket")
_fb = {b["name"]: b for b in _lvfe["fe_buckets"]}
ck(_fb.get("shopping", {}).get("candidate") is True and _fb["shopping"]["count"] == 1,
   "P2b: a piece with no backend entity becomes an FE-native bucket, flagged candidate")
ck(len(_lvfe["fe_edges"]) == 1 and len(_lvfe["fe_scaffold"]) == 1,
   "P2b: FE composition edges + the scaffold toggle layer are carried for the render")
ck(_lvg["frontend"] == {"present": False} and _lvg["fe_buckets"] == [] and lv["frontend"] == {"present": False},
   "P2b: frontend honest-empty when the graft arm has no frontend block (or no arm at all)")

# determinism — byte-identical across two independent builds
ck(json.dumps(lv, sort_keys=True) == json.dumps(_a3_levels.build_levels(AMAP, _a3_graph.build_c4_graph(AMAP)), sort_keys=True),
   "deterministic (byte-identical output)")

# MUTATION 1 — strip function_insight ⇒ fn_nodes must zero: it names the handlers
#   (the trace roots) AND carries the file→entity map that decides which references
#   cross an entity boundary — remove it and the drawn set has no seed (detectable)
_m1 = copy.deepcopy(AMAP); _m1["function_insight"] = {}
_lv1 = _a3_levels.build_levels(_m1, _a3_graph.build_c4_graph(_m1))
ck(len(_lv1["fn_nodes"]) == 0 and len(lv["fn_nodes"]) > 0, "MUTATION: removing function_insight zeroes fn_nodes")
# MUTATION 2 — strip internal_refs ⇒ use_edges must zero; the HANDLERS still draw (they
#   ride function_insight.handler, not internal_refs), so fn_nodes falls to just the 3 handlers
_m2 = copy.deepcopy(AMAP)
for _k in _m2["model_insight"]:
    _m2["model_insight"][_k]["internal_refs"] = []
_lv2 = _a3_levels.build_levels(_m2, _a3_graph.build_c4_graph(_m2))
ck(len(_lv2["use_edges"]) == 0 and len(_lv2["fn_nodes"]) == 3 and len(lv["use_edges"]) > 0,
   "MUTATION: removing internal_refs zeroes use_edges; handlers still draw")
# MUTATION 3 — strip guard_insight ⇒ endpoint guards must fall to 0 (detectable)
_m3 = copy.deepcopy(AMAP); _m3["guard_insight"] = {"files": {}}
_lv3 = _a3_levels.build_levels(_m3, _a3_graph.build_c4_graph(_m3))
ck(all(e["guards"] == 0 for e in _lv3["pieces"]["orders"]["endpoints"])
   and any(e["guards"] == 2 for e in lv["pieces"]["orders"]["endpoints"]),
   "MUTATION: removing guard_insight zeroes endpoint guards")
# MUTATION 4 — spread orders across 3 distinct first segments ⇒ adaptive depth drops
#   to 1, so "orders/lines" collapses back to the coarse "orders" (detectable)
_m4 = copy.deepcopy(AMAP)
_m4["entities"]["orders"]["endpoints"] += [
    {"method": "GET", "path": "/baskets", "fn": "list_baskets", "file": "api/orders.py", "touches": [], "resp": ""},
    {"method": "GET", "path": "/carts", "fn": "list_carts", "file": "api/orders.py", "touches": [], "resp": ""}]
_lv4 = _a3_levels.build_levels(_m4, _a3_graph.build_c4_graph(_m4))
ck("orders/lines" not in _lv4["pieces"]["orders"]["usecases"] and "orders/lines" in lv["pieces"]["orders"]["usecases"],
   "MUTATION: a 3rd first-segment flattens the adaptive use-case depth to 1")
# MUTATION 5 — strip OrderLine's intra FK ⇒ fk_communities no longer joins it to Order
_m5 = copy.deepcopy(AMAP)
for _m in _m5["entities"]["orders"]["models"]:
    if _m["cls"] == "OrderLine":
        _m["fks"] = {}
_lv5 = _a3_levels.build_levels(_m5, _a3_graph.build_c4_graph(_m5))
ck(not any(set(v) >= {"Order", "OrderLine"} for v in _lv5["pieces"]["orders"]["fk_communities"].values())
   and any(set(v) >= {"Order", "OrderLine"} for v in lv["pieces"]["orders"]["fk_communities"].values()),
   "MUTATION: removing the intra FK splits the fk_community")

# ── fn DETAIL projection (the panel's Function card feed): doc · file · signature
#    from function_insight, keyed "fn:"+slug+"|"+name like the cls: rows, honest-empty
#    per field. list_orders' FI carries a docstring + returns + async + line count.
_fd = lv["detail"].get("fn:orders|list_orders")
ck(bool(_fd) and _fd.get("doc") == "List all orders for the user." and _fd.get("file") == "api/orders.py"
   and _fd.get("flines") == 12 and _fd.get("sig", {}).get("returns") == "OrderResponse"
   and _fd.get("sig", {}).get("async") is True,
   "fn detail projects doc + file + flines + signature from function_insight")
# add_line's FI has file/entity but NO doc/lines/returns ⇒ file only, nothing fabricated
_fda = lv["detail"].get("fn:orders|add_line")
ck(bool(_fda) and _fda.get("file") == "api/orders.py" and "doc" not in _fda
   and "flines" not in _fda and "sig" not in _fda,
   "fn detail honest-empty: no docstring/signature insight ⇒ file only, no fabricated fields")
# MUTATION 6 — strip list_orders' doc + returns + async ⇒ its fn detail loses doc + sig,
#   keeping file (which comes from the drawn id, not the insight) — detectable
_m6 = copy.deepcopy(AMAP)
for _f in ("doc", "returns", "async", "lines"):
    _m6["function_insight"]["api/orders.py::list_orders"].pop(_f, None)
_lv6 = _a3_levels.build_levels(_m6, _a3_graph.build_c4_graph(_m6))
_fd6 = _lv6["detail"].get("fn:orders|list_orders")
ck(bool(_fd6) and "doc" not in _fd6 and "sig" not in _fd6 and "flines" not in _fd6
   and _fd6.get("file") == "api/orders.py" and bool(_fd) and _fd.get("doc"),
   "MUTATION: stripping the docstring/signature insight drops the fn detail doc + sig, keeps file")

# ── AUDIT LOCKS: the proof/detail invariants the badge-vs-panel audit exposed ────────
# (the pre-audit battery passed while all 16 defects existed — these pin the fixes)
# #1: fn_nodes NEVER carry a `tests` field — a function is not a test target; the badge
#     fabricated proof for functions. The feed must not emit one.
ck(all("tests" not in n for n in lv["fn_nodes"]),
   "AUDIT #1: fn_nodes carry NO tests field (no fabricated function proof)")
# #8: a fn_node's fan-in usage = internal + api callers (function_insight.internal EXCLUDES
#     the api layer; counting internal alone read a false 0 for a handler no internal fn calls).
_lo0 = [n for n in lv["fn_nodes"] if n["name"] == "list_orders"][0]
ck(_lo0["hub"]["usage"] == 5, "AUDIT #8: fn hub.usage = internal + api (2 + 3 = 5)")
_m8 = copy.deepcopy(AMAP); _m8["function_insight"]["api/orders.py::list_orders"]["api"] = 0
_lv8 = _a3_levels.build_levels(_m8, _a3_graph.build_c4_graph(_m8))
_lo8 = [n for n in _lv8["fn_nodes"] if n["name"] == "list_orders"][0]
ck(_lo8["hub"]["usage"] == 2 and _lo0["hub"]["usage"] == 5,
   "AUDIT #8 MUTATION: dropping api callers drops fan-in (5 → 2) — api IS counted")
# #2: every endpoint carries a tests{n,api,web,red} dict — missing → the page drew every
#     endpoint as the hollow 'unproven' glyph even when det.cases existed.
ck(all(isinstance(e.get("tests"), dict) and "n" in e["tests"]
       for s in lv["pieces"].values() for e in s["endpoints"]),
   "AUDIT #2: every endpoint carries a tests{n,...} dict (proof badge can render)")
# #6: a container return (list[X]/Optional[X]) is BARE in `resp` (so schema_owner joins)
#     with the full form kept in resp_full.
_mr = copy.deepcopy(AMAP)
_mr["entities"]["orders"]["endpoints"].append(
    {"method": "GET", "path": "/orders/recent", "fn": "recent", "file": "api/orders.py",
     "touches": [], "resp": "list[OrderResponse]"})
_lvr = _a3_levels.build_levels(_mr, _a3_graph.build_c4_graph(_mr))
_er = [e for e in _lvr["pieces"]["orders"]["endpoints"] if e["p"] == "/orders/recent"][0]
ck(_er["resp"] == "OrderResponse" and _er["resp_full"] == "list[OrderResponse]",
   "AUDIT #6: a container resp (list[X]) is BARE in resp, full in resp_full")
# #7/#14 (unit): _tests_of counts cases_more (the >cap overflow) in n — a >cap model
#     reported n=6 not the true count, so badge(29) ≠ panel — and IGNORES case_files
#     (coverage-by-file, not cases — a stray filename digit used to inflate n).
ck(_a3_levels._tests_of({"cases": [{"corpus": "api", "cid": "C1", "state": "pass"}], "cases_more": 5})["n"] == 6,
   "AUDIT #14: _tests_of.n includes cases_more (6 = 1 shown + 5 overflow)")
ck(_a3_levels._tests_of({"cases": [], "case_files": [{"corpus": "api", "name": "x"}]})["n"] == 0,
   "AUDIT #7: _tests_of ignores case_files (coverage-by-file, not a case count)")
# #16 (unit): _store_det MERGES a same-key write (model det then schema det, either order)
#     instead of clobbering — a schema (cols, no cases) wiped a model (29 cases) so the
#     badge read the model's tests while the panel read the schema's 0-case det.
_lvu = {"detail": {}}
_a3_levels._store_det(_lvu, "cls:x|Dup", {"cases": [{"cid": "C1"}], "cases_more": 3, "file": "m.py"})
_a3_levels._store_det(_lvu, "cls:x|Dup", {"cols": [["a", "int", ""]], "file": "s.py"})
_du = _lvu["detail"]["cls:x|Dup"]["det"]
ck(len(_du.get("cases", [])) == 1 and _du.get("cases_more") == 3 and bool(_du.get("cols")),
   "AUDIT #16: _store_det MERGES model cases + schema cols on a shared key (no clobber)")
_lvu2 = {"detail": {}}
_a3_levels._store_det(_lvu2, "cls:x|Dup", {"cols": [["a", "int", ""]], "file": "s.py"})
_a3_levels._store_det(_lvu2, "cls:x|Dup", {"cases": [{"cid": "C1"}], "cases_more": 3, "file": "m.py"})
_du2 = _lvu2["detail"]["cls:x|Dup"]["det"]
ck(len(_du2.get("cases", [])) == 1 and _du2.get("cases_more") == 3 and bool(_du2.get("cols")),
   "AUDIT #16: _store_det merge is order-independent (schema-first == model-first)")

# ── SWEEP LOCKS: the structural-audit fixes (model/schema identity + cross-entity prune) ──
# SWEEP-A: a model and a SAME-NAMED schema in one entity keep DISTINCT detail records —
#   model under cls:, schema under sch: — so the schema panel shows its OWN columns, not
#   the model's (gastify StatementLine: schema 20 fields/source_order vs model 23/id).
# SWEEP-C: a schema OWNED by entity A but returned only by entity B's endpoint survives the
#   per-entity prune (was dropped → drawn nowhere, gustify MeResponse/SettingsResponse).
_msw = copy.deepcopy(AMAP)
_msw["entities"]["orders"]["models"].append(
    {"cls": "Dup", "table": "dups", "cols": [["mid", "uuid", ""]], "fks": {}})
_msw["entities"]["orders"]["schemas"].append(
    {"cls": "Dup", "fields": [["sfield", "str", ""]]})
_msw["entities"]["orders"]["endpoints"].append(
    {"method": "GET", "path": "/dup", "fn": "get_dup", "file": "api/orders.py", "touches": [], "resp": "Dup"})
# UserExport is a users-owned schema returned by an ORDERS endpoint (cross-entity)
_msw["entities"]["users"]["schemas"].append({"cls": "UserExport", "fields": [["x", "str", ""]]})
_msw["entities"]["orders"]["endpoints"].append(
    {"method": "GET", "path": "/export", "fn": "export", "file": "api/orders.py", "touches": [], "resp": "UserExport"})
_lsw = _a3_levels.build_levels(_msw, _a3_graph.build_c4_graph(_msw))
_dm = (_lsw["detail"].get("cls:orders|Dup") or {}).get("det", {})
_ds = (_lsw["detail"].get("sch:orders|Dup") or {}).get("det", {})
ck((_dm.get("cols") or [[None]])[0][0] == "mid" and (_ds.get("cols") or [[None]])[0][0] == "sfield",
   "SWEEP-A: model (cls:) + same-named schema (sch:) keep DISTINCT detail — own columns each")
ck("UserExport" in {s["cls"] for s in _lsw["pieces"]["users"]["schemas"]},
   "SWEEP-C: a schema returned by ANOTHER entity's endpoint survives the prune (drawn, not dropped)")
# MUTATION — a schema NO endpoint anywhere touches/returns is still pruned (guard can fire)
_msw2 = copy.deepcopy(_msw)
_msw2["entities"]["users"]["schemas"].append({"cls": "NeverUsed", "fields": [["y", "str", ""]]})
_lsw2 = _a3_levels.build_levels(_msw2, _a3_graph.build_c4_graph(_msw2))
ck("NeverUsed" not in {s["cls"] for s in _lsw2["pieces"]["users"]["schemas"]},
   "SWEEP-C MUTATION: a schema referenced by NO endpoint (any entity) is still pruned")

# ── _bare_cls · PEP-604 optional (review finding 3) — `X | None` must resolve to X, not the literal 'None' ──
for _s, _exp in (("list[Recipe] | None", "Recipe"), ("Recipe | None", "Recipe"),
                 ("dict[str,Recipe] | None", "Recipe"), ("Optional[Recipe]", "Recipe"), ("list[Recipe]", "Recipe")):
    ck(_a3_levels._bare_cls(_s) == _exp and _a3_graph._bare_cls(_s) == _exp,
       f"_bare_cls({_s!r})→{_exp!r} in BOTH arms (was 'None' on the | None form)")

# ── schema_edges (2026-08-27 schema homing): the fn→schema wires ride a SEPARATE feed, never fn_edges ──
ck(lv.get("schema_edges") == [], "honest-empty: no schema_homing block upstream → schema_edges []")
_hm = copy.deepcopy(AMAP); _hm["schema_homing"] = {"moved": [], "ambiguous": [], "unwired": [],
    "fn_wires": [{"fn": "svc/lane.py#ingest", "cls": "OrderResponse", "rel": "returns", "slug": "orders"},
                 {"fn": "svc/a.py#mk", "cls": "OrderResponse", "rel": "uses", "slug": "orders"}]}
_lh = _a3_levels.build_levels(_hm, graph)
ck(_lh["schema_edges"] == [{"s": "svc/a.py#mk", "t": "schema:OrderResponse", "rel": "uses"},
                           {"s": "svc/lane.py#ingest", "t": "schema:OrderResponse", "rel": "returns"}], "schema_edges emitted from fn_wires, sorted, schema: ids (%r)" % _lh["schema_edges"])
ck(_lh["fn_edges"] == lv["fn_edges"], "fn_edges untouched by the homing feed (its consumers assume fn→fn)")

# ── legend pass (2026-09-06) · class 13: a handler-rooted graft call carrying rel:'dispatches' survives as its own rel;
#    a TASK root (archmap.task_roots) joins the handler set so the worker's chain draws downstream of the queue ──
_GWx = {"present": True, "functions": {"fn_slug": dict(_GW["functions"]["fn_slug"], **{"svc/tasks.py#reindex": "orders"}),
        "calls": [{"s": "api/orders.py#list_orders", "t": "svc/tasks.py#reindex", "ss": "orders", "ts": "orders", "conf": "extracted", "rel": "dispatches"},
                  {"s": "svc/tasks.py#reindex", "t": "svc/o.py#svc_write", "ss": "orders", "ts": "orders", "conf": "inferred"}]}}
_lvx = _a3_levels.build_levels(AMAP, graph, graft=_GWx)
_dx = [e for e in _lvx["fn_edges"] if e.get("rel") == "dispatches"]
ck(len(_dx) == 1 and _dx[0]["t"] == "svc/tasks.py#reindex", "class 13: a handler's dispatch edge keeps rel:'dispatches' in fn_edges")
ck(not any(e["s"] == "svc/tasks.py#reindex" for e in _lvx["fn_edges"]), "class 13 SILENT: without a task root the task fn is not a root — its own calls do not draw")
AMAPt = json.loads(json.dumps(AMAP)); AMAPt["task_roots"] = [{"method": "TASK", "path": "reindex", "fn": "reindex", "file": "svc/tasks.py", "touches": [], "touches_x": [], "doc": "", "resp": "—", "status": "—"}]
_lvt = _a3_levels.build_levels(AMAPt, graph, graft=_GWx)
ck(any(e["s"] == "svc/tasks.py#reindex" and e["t"] == "svc/o.py#svc_write" for e in _lvt["fn_edges"]) and any(n["id"] == "svc/tasks.py#reindex" for n in _lvt["fn_nodes"]),
   "class 13 FIRE: a task root joins the handler set — the worker's downstream call draws")
AMAPn = json.loads(json.dumps(AMAPt)); AMAPn.pop("task_roots", None)
ck(json.dumps(_a3_levels.build_levels(AMAPn, graph, graft=_GWx)["fn_edges"], sort_keys=True) == json.dumps(_lvx["fn_edges"], sort_keys=True)
   and json.dumps(_a3_levels.build_levels(AMAPn, graph, graft=_GWx)["fn_edges"], sort_keys=True) != json.dumps(_lvt["fn_edges"], sort_keys=True),
   "class 13 byte-identical: the task-root arm changes nothing when task_roots is absent — and something when present")
# entity-models (2026-09-06): a `models` key on the levels dict rides emit() untouched (the function-id half of the views)
import tempfile, pathlib, json as _j
_lv2 = copy.deepcopy(levels) if "levels" in dir() else _a3_levels.build_levels(AMAP, _a3_graph.build_c4_graph(AMAP, labels={}, status={}))
_lv2["models"] = {"present": True, "head": "testsha", "homes": {"seeded": {"api/orders.py#list_orders": "billing"}, "derived": {}, "proposed": {}}, "held": {"seeded": [], "derived": []}, "abstain": {"seeded": [], "derived": [], "proposed": []}}
_td = pathlib.Path(tempfile.mkdtemp()); _a3_levels.emit(_lv2, _td)
_back = _j.loads((_td / "levels.json").read_text(encoding="utf-8"))
ck(_back.get("models", {}).get("homes", {}).get("seeded", {}).get("api/orders.py#list_orders") == "billing", "entity-models: the levels.json mirror slice survives emit() (the station's function nodes and gabe-map read it there)")
print(f"levels battery: {p} passed, {f} failed")
sys.exit(1 if f else 0)
PY
