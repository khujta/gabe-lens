#!/usr/bin/env python3
"""_a3_levels.py — derive the rich LEVELS graph (window.GABE_LEVELS) the codebase
stations render, from the in-memory archmap + the already-built C4 graph.

The lab-native station renderer (level-lab grammar) reads ``window.GABE_LEVELS``:
entities · colours · L1 kind-edges · piece-level cross edges · per-entity pieces
(models · schemas · endpoints · intra FKs · USE-CASES · COMMUNITIES · use-fns) ·
FUNCTION nodes · USE edges · schema owners · per-element dossier detail.

Provenance (the flip, 2026-08-13): the station used to re-implement the lab grammar
over the slim ``GABE_C4`` topology, so the function / use-case / community lenses
were empty. This module feeds the ITERATED lab renderer directly instead — and the
rich lenses are NOT new data: they come from insight blocks the suite's own
``_a3_code`` already writes into the archmap on every build:

  * ``function_insight`` (per fn: entity · file · layer · god · handler · lines) → ``fn_nodes``
  * ``model_insight.internal_refs`` (which fns reference a model class)          → ``use_edges`` · ``usefns``
  * ``model_insight`` (fan-in ``usage`` · ``god``)                              → per-model ``hub``
  * ``guard_insight`` (declared validators per file)                            → per-endpoint ``guards``
  * ``test_insight`` (carried on each C4 node's ``det.cases``)                  → per-piece ``tests``
  * endpoint URL first segment                                                 → ``usecases``
  * intra FK ∪ shared-touch components                                          → ``communities``

Only the cross-file function CALL edges (``fn_edges``, the Layers cross-lane wires)
need the graft index; they are honest-empty when the arm is absent. Everything else
is pure archmap + C4 derivation — the same data, one host without a graft binary.

Determinism: a pure function of (amap, graph, graft index fp) with every list sorted;
same inputs ⇒ byte-identical output. Honest-empty: a missing insight block yields the
empty field, never a fabricated value; the lab degrades on its own ``||[]`` fallbacks.

Battery: tests/levels/run.sh (derive + honest-empty + determinism, mutation-proven).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def _strip(nid: str) -> str:
    """model:Recipe → Recipe (drop the kind prefix a C4 node id carries)."""
    return nid.split(":", 1)[1] if ":" in nid else nid


def _bare_cls(resp: str) -> str:
    """AUDIT #6: the bare schema class inside a container return type — list[X] · Optional[X]
    · Sequence[X] · list[X] | None → X — so schema_owner (keyed by bare class name) resolves
    it. Returns resp unchanged when there is no wrapper. Grabs the LAST CamelCase identifier
    (the payload type), which handles nested/optional/union wrappers without a real parser."""
    s = str(resp or "")
    ids = [i for i in re.findall(r"[A-Z][A-Za-z0-9_]+", s) if i != "None"]   # PEP-604 `X | None` ends in None; it is not the payload
    return ids[-1] if ids else s


def _method_of(label: str) -> str:
    tok = str(label).split(" ", 1)[0]
    return tok if tok.isupper() and tok.isalpha() else "GET"


def _path_of(label: str) -> str:
    parts = str(label).split(" ", 1)
    return parts[1] if len(parts) > 1 else label


def _tests_of(det: dict | None) -> dict[str, int]:
    """{api, web, n, red} — the real CASE count from a C4 node's det.cases (+ the capped
    remainder). AUDIT #7: det.cases is DISPLAY-CAPPED (element_detail caps at
    _DET_CASES_CAP), with the overflow count in det.cases_more; the old code missed it
    (undercounting >cap models like OwnershipScope 27→6) AND digit-parsed det.case_files
    (route-literal FILE coverage, NOT cases — a stray filename digit could inflate n). Now:
    count real cases + cases_more (attributed to api, the dominant corpus — cases_more
    carries no split), and IGNORE case_files (coverage-by-file is not a case count)."""
    out = {"api": 0, "web": 0, "n": 0, "red": 0}
    if not det:
        return out
    for c in det.get("cases", []) or []:
        out["n"] += 1
        if c.get("corpus") == "web":
            out["web"] += 1
        else:
            out["api"] += 1
        st = c.get("state")
        if st and st not in ("pass", "skip"):
            out["red"] += 1
    cm = int(det.get("cases_more", 0) or 0)
    if cm:
        out["n"] += cm
        out["api"] += cm
    return out


def _merge_det(old: dict, new: dict) -> dict:
    """Model + schema of the SAME name+entity share the ``cls:slug|label`` detail key
    (an ORM model and its same-named response schema). AUDIT #16: the second write
    clobbered the first — a schema det (cols, no cases) wiped a model det (29 cases)
    so the proof BADGE read the model's tests (29) while the PANEL read the schema's
    det (0). Merge instead: fill empty slots + keep the richer case set/overflow, so
    the panel shows the UNION (model cases + schema cols) and badge == panel."""
    out = dict(old)
    for key, val in new.items():
        if not out.get(key) and val:
            out[key] = val
    if len(new.get("cases", []) or []) > len(out.get("cases", []) or []):
        out["cases"] = new["cases"]
    if int(new.get("cases_more", 0) or 0) > int(out.get("cases_more", 0) or 0):
        out["cases_more"] = new["cases_more"]
    return out


def _store_det(lv: dict, key: str, det: dict) -> None:
    """Write a piece's element_detail under ``key``, MERGING with any prior entry
    (model/schema name collision) rather than overwriting — see ``_merge_det``."""
    prev = lv["detail"].get(key)
    d = _merge_det(prev["det"], det) if prev else det
    lv["detail"][key] = {"cases": d.get("cases", []), "det": d}


def _use_case_key(path: str, depth: int) -> str:
    """the leading non-parameter URL segments (up to ``depth``), joined by '/'
    — the use-case key (``root`` when the path has none)."""
    segs = [s for s in str(path).split("/") if s and s[0] not in ("{", ":")]
    return "/".join(segs[:depth]) if segs else "root"


def _use_case_depth(paths: list[str]) -> int:
    """adaptive grouping depth for one entity's routes. An entity whose endpoints
    spread across only ONE or TWO distinct first segments groups one level DEEPER
    — otherwise that first segment is a single coarse blob (``/cooking/*`` →
    ``cooking`` swallows the whole entity). Entities that already spread across ≥3
    first segments stay at depth 1. Fits the hand-derived fixture 65/67 (operator
    ruling 2026-08-13); the 2 residual are genuine curation, not a rule."""
    firsts = {_use_case_key(p, 1) for p in paths}
    return 2 if len(firsts) <= 2 else 1


def _fe_slim(nodes: list[dict[str, Any]]) -> dict[str, Any]:
    """Compact a homed frontend-piece list into the LEVELS feed shape: a per-kind
    count (the stacked BAND reads this) + the pieces themselves (the cluster CIRCLE
    draws these). Sorted → deterministic."""
    by_kind: dict[str, int] = {}
    pieces = []
    for n in sorted(nodes, key=lambda x: x["id"]):
        by_kind[n["kind"]] = by_kind.get(n["kind"], 0) + 1
        pieces.append({"id": n["id"], "n": n.get("name"), "k": n["kind"]})
    return {"count": len(nodes), "by_kind": dict(sorted(by_kind.items())), "pieces": pieces}


def build_levels(amap: dict[str, Any], graph: dict[str, Any],
                 graft: dict[str, Any] | None = None) -> dict[str, Any]:
    """Pure derivation of the LEVELS graph from the archmap + the C4 graph."""
    ents = amap.get("entities", {}) or {}
    FI = amap.get("function_insight", {}) or {}
    MI = amap.get("model_insight", {}) or {}
    GI = (amap.get("guard_insight", {}) or {}).get("files", {}) or {}

    l1_nodes = [n for n in graph.get("l1", {}).get("nodes", []) if n.get("kind") == "entity"]
    l2 = graph.get("l2", {}) or {}
    colors = graph.get("colors", {}) or {}

    # ── endpoint dedup + URL-home (round 27 decision — one endpoint, one entity) ──
    # An aspect entity whose center.config claims another entity's ROUTE files (e.g.
    # allergen ⊃ pantry/cooking/recipe routes) would re-draw 32 duplicate endpoints.
    # Home each (method, path) by its HANDLER's entity — function_insight already
    # resolved which entity the handler file belongs to — so the real owner keeps it
    # and the aspect becomes endpoint-less (allergen → an aspect, present via its
    # models/schemas + cross edges, not phantom route copies). Reproduces the fixture.
    ep_home: dict[str, str] = {}
    for _slug, _code in ents.items():
        for _ep in _code.get("endpoints", []) or []:
            _key = (str(_ep.get("method", "")) + " " + str(_ep.get("path", ""))).strip()
            _home = (FI.get((_ep.get("file", "") or "") + "::" + (_ep.get("fn", "") or ""), {}) or {}).get("entity")
            if _home:
                ep_home[_key] = _home
            else:
                ep_home.setdefault(_key, _slug)

    # class → owning entity (models + schemas), and file → entity (for fn homing)
    cls_ent: dict[str, str] = {}
    file_ent: dict[str, str] = {}
    for slug, code in ents.items():
        for m in code.get("models", []) or []:
            cls_ent[m["cls"]] = slug
        for s in code.get("schemas", []) or []:
            cls_ent.setdefault(s["cls"], slug)
    for fid, f in FI.items():
        if f.get("file") and f.get("entity"):
            file_ent[f["file"]] = f["entity"]

    lv: dict[str, Any] = {
        "note": "live from the archmap — functions · use-cases · communities · use-edges "
                "derived from function_insight + model_insight (cross-file call edges ride the graft arm)",
        "census_note": "workflow census not curated for this project yet",
        "colors": colors,
        "entities": [{"slug": n["slug"], "label": n.get("label", n["slug"]),
                      "counts": n.get("counts", {})} for n in l1_nodes],
        "l1_edges": [{"s": e["source"], "t": e["target"], "kinds": e.get("kinds", {"fk": 1})}
                     for e in graph.get("l1", {}).get("edges", [])
                     if e.get("source") and e.get("target")
                     and e["source"] != "__unclaimed__" and e["target"] != "__unclaimed__"],
        # FK cross-edges only — the C4 graph now also carries web→endpoint BRIDGE
        # edges (kind:'bridge', a station concept); they are NOT a LEVELS fact, so
        # the rich feed stays FK-only and byte-identical to the pre-bridge build.
        "cross_edges": [{"fs": e["from_slug"], "f": _strip(e["from"]),
                         "ts": e["to_slug"], "t": _strip(e["to"]), "via": e.get("via", "")}
                        for e in graph.get("cross_edges", [])
                        if e.get("kind") != "bridge"],
        "schema_owner": {},
        "detail": {},
        "fn_nodes": [],
        "fn_edges": [],
        # function → schema wires from the homing pass (returns · takes · uses): a SEPARATE feed,
        # never folded into fn_edges (whose consumers assume fn→fn calls). Honest-empty [].
        "schema_edges": sorted(({"s": w["fn"], "t": "schema:" + w["cls"], "rel": w["rel"]}
                                for w in ((amap.get("schema_homing") or {}).get("fn_wires") or [])
                                if w.get("fn") and w.get("cls")),
                               key=lambda e: (e["s"], e["t"], e["rel"])),
        "use_edges": [],
        "pressure": {},
        "census": {},
        "pieces": {},
    }

    # ── the DRAWN function set — the on-path fns the fixture draws, not all 461, so
    #    the trace stays legible and the communities cluster on FLOW. Three sources,
    #    homed first-wins (function_insight is authoritative over graft's file→entity):
    #      1. HANDLERS          — the API entry points, the trace roots
    #      2. cross-entity MODEL USERS — a fn reads/writes a model another entity owns
    #      3. graft handler-CALL TARGETS — the fns a handler invokes (so the call
    #         wires have both endpoints drawn; the lab drops an edge to an undrawn fn)
    drawn_fn: dict[str, str] = {}       # graft-style id (file#fn) → owning entity
    _handlers: set[str] = set()         # the handler ids — the ONLY roots of fn_edges
    # 1 · handlers (function_insight key is file::fn; the drawn id is graft's file#fn)
    for _k, _f in FI.items():
        if _f.get("handler") and _f.get("file") and _f.get("entity"):
            _hid = _f["file"] + "#" + _f["fn"]
            drawn_fn.setdefault(_hid, _f["entity"])
            _handlers.add(_hid)
    # rule 0 · class 7 · BOOT roots join the handler set (homed to __unclaimed__, main.py is
    # unclaimed) so rule 3 admits lifespan's graft calls and rule 3b pulls the seeder write-path.
    for _r in amap.get("boot_roots") or []:
        _bid = str(_r.get("file")) + "#" + str(_r.get("fn"))
        drawn_fn.setdefault(_bid, "__unclaimed__")
        _handlers.add(_bid)
    # rule 0b · class 13 · TASK roots (Celery/ARQ/Taskiq workers) join the handler set too — homed to the
    # entity that claims the task file, else __unclaimed__ — so a worker's chain draws past the queue.
    _f2s_t = {f: s for s, e in (amap.get("entities") or {}).items() if e for _l, f, _n in (e.get("files") or [])}
    for _r in amap.get("task_roots") or []:
        _tid = str(_r.get("file")) + "#" + str(_r.get("fn"))
        drawn_fn.setdefault(_tid, _f2s_t.get(str(_r.get("file")), "__unclaimed__"))
        _handlers.add(_tid)
    # 2 · use_edges + usefns — a fn references a model owned elsewhere
    usefns_by: dict[str, dict[str, int]] = {}
    for cls in sorted(MI):
        owner = cls_ent.get(cls)
        if not owner:
            continue
        for ref in MI[cls].get("internal_refs", []) or []:
            rfile = ref.get("file", "")
            using = file_ent.get(rfile) or owner
            for fn in ref.get("defs", []) or []:
                usefns_by.setdefault(using, {})
                usefns_by[using][fn] = usefns_by[using].get(fn, 0) + 1
                if using != owner:
                    lv["use_edges"].append({"fs": using, "cls": cls, "ts": owner, "fn": fn})
                    if rfile:
                        drawn_fn.setdefault(rfile + "#" + fn, using)  # a CROSS-entity model-user is drawn
    lv["use_edges"].sort(key=lambda e: (e["fs"], e["ts"], e["cls"], e["fn"]))
    # 3 · graft handler-rooted calls → fn_edges + their endpoints join the drawn set.
    #     Only calls WHOSE SOURCE IS A HANDLER are drawn (the fixture's edge rule); the
    #     cross-file call is graft-inferred, so this edge set is a FLOOR, never a census.
    _gf = (graft or {}).get("functions") or {}
    _fedges: list[dict[str, Any]] = []
    for c in _gf.get("calls") or []:
        if c["s"] not in _handlers:
            continue
        drawn_fn.setdefault(c["s"], c["ss"])
        drawn_fn.setdefault(c["t"], c["ts"])
        _fedges.append({"s": c["s"], "ss": c["ss"], "t": c["t"], "ds": c["ts"],
                        "rel": c.get("rel", "calls"), "conf": c.get("conf", "inferred")})  # class 6 + 13: event-bus AND task-enqueue edges keep rel:'dispatches'
    # 3a · class 8 · DEPENDS edges (the K1 gate chain): endpoint handler → its gate dependency —
    #      a SIGNATURE fact the framework injects before the body (graft has 0 call edges into a
    #      Depends target). Handler-rooted like calls; the dep joins drawn_fn so §3b descends its
    #      OWN write-path (get_auth_context → build_auth_context → the User commit) unaided.
    for d in (graft or {}).get("depends") or []:
        if d["s"] not in _handlers:
            continue
        drawn_fn.setdefault(d["s"], d["ss"])
        drawn_fn.setdefault(d["t"], d.get("ts") or d["ss"])
        _fedges.append({"s": d["s"], "ss": d["ss"], "t": d["t"], "ds": d.get("ts") or d["ss"],
                        "rel": "depends", "conf": d.get("conf", "extracted")})
    # 3b · WRITE-PATH enrichment — the mid-chain calls the handler-only rule hides.
    #     distance_to_write (reverse-BFS hops-to-a-write, per fn) makes write paths
    #     computable without drawing the whole call graph: an edge s→t is a step on a
    #     shortest write-path iff it DESCENDS the gradient (d2w(t) == d2w(s)−1); from a
    #     WRITE-ANCHOR (d2w 0 — own write op or commit) ANY write-reaching callee is a
    #     write path — the commit-boundary → writer hop (complete_setup → _upsert_*, both
    #     anchors, 0→0) and the boundary → DELEGATING writer hop (0→1, the delegate's own
    #     anchor sits one deeper: _upsert_exploration → upsert_exploration_preferences).
    #     BFS from the already-drawn set to fixpoint. Still a FLOOR, two ways: calls are
    #     graft-inferred, and d2w is computed over a WIDER substrate (functions AND class
    #     methods) than derive_functions draws — a write path whose next hop is a method
    #     (e.g. repo-class .save) carries d2w but dead-ends here undrawn. Honest-empty:
    #     no distance_to_write (graft absent / no faccess) → no new edges/nodes →
    #     byte-identical output.
    _d2w = (graft or {}).get("distance_to_write") or {}
    if _d2w:
        _adj: dict[str, list[dict[str, Any]]] = {}
        for c in _gf.get("calls") or []:
            _adj.setdefault(c["s"], []).append(c)
        _have = {(e["s"], e["t"]) for e in _fedges}
        _q = sorted(f for f in drawn_fn if f in _d2w)
        _seen = set(_q)
        while _q:
            _s = _q.pop(0)
            _ds = _d2w.get(_s)
            if _ds is None:
                continue
            for c in _adj.get(_s, []):
                _t, _dt = c["t"], _d2w.get(c["t"])
                if _dt is None or (_ds > 0 and _dt > _ds - 1):
                    continue                       # not a step toward the write
                drawn_fn.setdefault(_t, c["ts"])
                if (_s, _t) not in _have:
                    _have.add((_s, _t))
                    _fedges.append({"s": _s, "ss": c["ss"], "t": _t, "ds": c["ts"],
                                    "rel": c.get("rel", "calls"), "conf": c.get("conf", "inferred")})
                if _t not in _seen:
                    _seen.add(_t)
                    _q.append(_t)
    # both endpoints are now in drawn_fn by construction; keep the edge only if so
    _fedges = [e for e in _fedges if e["s"] in drawn_fn and e["t"] in drawn_fn]
    # class 9 · reaches — a drawn fn → provider:<name> (external SDK/LLM edge). The provider is NOT a
    # drawn fn, so it is appended AFTER the drawn-fn filter. A leaf wire (a provider has no outgoing).
    for _fid, _fslug in sorted(drawn_fn.items()):
        for _p in ((FI.get(_fid.replace("#", "::", 1), {}) or {}).get("externals") or []):
            _fedges.append({"s": _fid, "ss": _fslug, "t": "provider:" + _p, "ds": _fslug,
                            "rel": "reaches", "conf": "inferred"})
    _fedges.sort(key=lambda e: (e["ss"], e["ds"], e["s"], e["t"], e.get("rel", "")))
    lv["fn_edges"] = _fedges

    # per-entity HIDDEN functions — homed by graft (fn_slug) but NOT drawn on the trace: the honest
    # star-field count. A SET difference (id-by-id, never len−len which goes negative), grouped by the
    # fn's owning entity. Honest-empty: graft absent → fn_slug empty → no counts touched → byte-identical.
    _fn_slug = _gf.get("fn_slug") or {}
    _hidden: dict[str, int] = {}
    for _fid, _sl in _fn_slug.items():
        if _fid not in drawn_fn:
            _hidden[_sl] = _hidden.get(_sl, 0) + 1
    for _ent in lv["entities"]:
        _h = _hidden.get(_ent["slug"])
        if _h:                                        # new dict — never mutate the shared C4 node counts
            _ent["counts"] = {**(_ent["counts"] or {}), "hidden_fns": _h}

    # ── fn_nodes — the DRAWN functions only, enriched from function_insight where
    #    present; graft/TS fns (no function_insight) default their layer by file ext.
    _fn_behind = (graft or {}).get("fn_behind") or {}   # per-fn call-tree floor (hidden mass)
    _fn_roles = (graft or {}).get("fn_roles") or {}      # C1: accessor/caller/gate/pure per function
    _fn_d2w = (graft or {}).get("distance_to_write") or {}  # D2W: fn → hops-to-a-write (call-wire heat)
    for fid in sorted(drawn_fn):
        slug = drawn_fn[fid]
        rfile, _, name = fid.partition("#")
        f = FI.get(rfile + "::" + name, {})
        is_py = rfile.endswith(".py")
        _node = {
            "id": fid, "name": name, "slug": slug, "kind": "function",
            "lang": "py" if is_py else "ts",
            "layer": f.get("layer") or ("services" if is_py else "web"),
            "handler": bool(f.get("handler")), "god": bool(f.get("god")),
            # AUDIT #8: fan-in = ALL callers. function_insight.internal EXCLUDES api-layer
            # callers, so a service fn called only from handlers read 0 — inverting the
            # load-bearing signal. Total in-degree = internal + api.
            "hub": {"god": bool(f.get("god")), "usage": f.get("internal", 0) + f.get("api", 0)},
            # AUDIT #1: NO fabricated `tests`. The old field was function_insight reference
            # counts (api = code coupling, web = a key FI never writes → always 0), rendered
            # as green "all passing" pills on untested fns. Coverage is tracked per
            # endpoint/model, not per function (the panel already says so) → honest-empty.
        }
        # the CODE-BEHIND floor (out-degree): what functions this function pulls in
        # transitively — the hidden mass "under the rug". Honest-empty: a leaf fn (no
        # outgoing calls) has no fn_behind entry → the panel omits the Code-behind section.
        _bh = _fn_behind.get(fid)
        if _bh:
            _node["behind"] = _bh
        _role = _fn_roles.get(fid)   # C1: accessor/caller/gate/pure — the function-badge data (honest-empty without graft)
        if _role:
            _node["role"] = _role
        _dw = _fn_d2w.get(fid)       # D2W: hops-to-a-write — 0 is a real value (a writer), so test `is not None`
        if _dw is not None:
            _node["d2w"] = _dw
        # a fn's own ops draw for ANY role that carries them, not just accessor (B0/P3): a
        # gate that READS is labeled `gate` but its reads must still draw — else the precedence
        # swap would strip ensure_principal_household's Household/Location writes off the map.
        _acc = (FI.get(rfile + "::" + name, {}) or {}).get("access")
        if _acc and _acc.get("ops"):
            _node["access"] = _acc
        _sk = (FI.get(rfile + "::" + name, {}) or {}).get("sinks")   # C4: non-ORM sink categories (floor)
        if _sk:
            _node["sinks"] = _sk
        _flg = (FI.get(rfile + "::" + name, {}) or {}).get("flags")  # class 12: fn-level feature-flag walls (the step note)
        if _flg:
            _node["flags"] = _flg
        _ext = (FI.get(rfile + "::" + name, {}) or {}).get("externals")  # class 9: providers this fn reaches
        if _ext:
            _node["externals"] = _ext
        lv["fn_nodes"].append(_node)
        # fn DETAIL — the wider projection of function_insight the panel's Function
        # card reads (detailOf("fn:"+slug+"|"+name)), keyed exactly like the cls: rows.
        # Pure archmap, honest-empty PER FIELD: no docstring insight ⇒ no doc, a TS fn
        # with no function_insight ⇒ file only. Keeps the fn card off a blank without
        # a new source read; C4's element_detail dossier covers endpoints/models/schemas,
        # functions are the LEVELS feed's own territory so their detail is homed here.
        fdet: dict[str, Any] = {}
        if rfile:
            fdet["file"] = rfile
        if f.get("doc") and f["doc"] != "—":
            fdet["doc"] = f["doc"]
        if f.get("lines"):
            fdet["flines"] = f["lines"]
        _sig: dict[str, Any] = {}
        if f.get("returns"):
            _sig["returns"] = f["returns"]
        if f.get("async"):
            _sig["async"] = True
        if _sig:
            fdet["sig"] = _sig
        if fdet:
            lv["detail"]["fn:" + slug + "|" + name] = fdet

    # SWEEP-C: the GLOBAL endpoint-facing schema set — every class any entity's endpoint
    # touches (request body) or returns (bare resp), across ALL entities. The per-entity
    # prune below keeps a schema only if a LOCAL endpoint references it, which dropped a
    # schema OWNED by entity A but returned only by entity B's endpoints (gustify
    # MeResponse/SettingsResponse/AccountExportResponse → drawn nowhere, 7 return-wires
    # dangling). Prune against this union so a cross-entity-referenced schema survives.
    _global_touched: set = set()
    for _slug in l2:
        _g = l2[_slug]
        for _nd in _g.get("nodes", []):
            if _nd.get("kind") != "endpoint":
                continue
            for _e in _g.get("edges", []):
                if _e.get("kind") == "touches" and _e.get("source") == _nd["id"]:
                    _global_touched.add(_strip(_e["target"]))
            _r = _nd.get("resp")
            if _r and _r != "—":
                _global_touched.add(_bare_cls(_r))

    # ── per-entity pieces (from the C4 L2) + the rich lenses ──────────────────
    for slug in sorted(l2):
        g = l2[slug]
        nodes = g.get("nodes", [])
        edges = g.get("edges", [])
        model_id: dict[str, str] = {}
        models, schemas, endpoints = [], [], []
        for nd in nodes:
            det = nd.get("det")
            k = nd.get("kind")
            if k == "model":
                model_id[nd["id"]] = nd["label"]
                lv["schema_owner"].setdefault(nd["label"], slug)
                mi = MI.get(nd["label"], {})
                nfk = sum(1 for e in edges if e.get("kind") == "fk" and e.get("source") == nd["id"])
                models.append({"cls": nd["label"], "table": nd.get("table", ""), "nfk": nfk,
                               "hub": {"god": bool(mi.get("god")), "usage": mi.get("usage", 0)},
                               "tests": _tests_of(det)})
                if det:
                    _store_det(lv, "cls:" + slug + "|" + nd["label"], det)
            elif k == "schema":
                lv["schema_owner"][nd["label"]] = slug
                schemas.append({"cls": nd["label"], "tests": _tests_of(det)})
                if det:
                    # SWEEP-A: schemas key detail under `sch:` (models keep `cls:`). A model and
                    # a same-named schema in one entity (gastify StatementLine) shared the cls:
                    # key, so the merge showed the MODEL's cols/file/count on the SCHEMA panel.
                    # Distinct keys give each its own det; the showPiece read is kind-aware.
                    _store_det(lv, "sch:" + slug + "|" + nd["label"], det)
            elif k == "endpoint":
                if ep_home.get(nd["label"], slug) != slug:
                    continue    # deduped — this route is drawn by its handler's entity
                touch = sorted({_strip(e["target"]) for e in edges
                                if e.get("kind") == "touches" and e.get("source") == nd["id"]})
                efile = (det or {}).get("file", "")
                guards = int((GI.get(efile, {}) or {}).get("declared", 0)) if efile else 0
                _resp_full = (nd.get("resp") or "") if nd.get("resp") != "—" else ""
                endpoints.append({"m": _method_of(nd["label"]), "p": _path_of(nd["label"]),
                                  "fn": nd.get("fn", ""),
                                  # AUDIT #6: `resp` is the BARE payload class (list[X]/Optional[X] → X)
                                  # so EVERY schema_owner/pieceAt join on the page resolves it — a
                                  # container return used to bind to nothing (returns-wire dead, false
                                  # "documented nowhere"). The full type still shows in the panel via
                                  # det.sig.returns; resp_full carries it for any consumer that wants it.
                                  "resp": _bare_cls(_resp_full), "resp_full": _resp_full,
                                  "guards": guards, "touch": touch,
                                  # AUDIT #2: without this the graph proofBadge always drew the hollow
                                  # 'unproven' glyph even though the endpoint's real cases sit in det.cases.
                                  "tests": _tests_of(det)})
        # schemas are PRUNED to the endpoint-facing set — a schema is kept only if an
        # endpoint of THIS entity touches it (request body) or returns it (resp). The
        # nested component schemas (a *Block/*Summary that appears only INSIDE a response's
        # fields, never at an endpoint boundary) drop off, matching the fixture exactly.
        # AUDIT #11: an endpoint-LESS aspect entity (all its routes deduped to their handler
        # entity) has an empty `endpoints` list → an empty _touched → the prune would delete
        # ALL its schemas (allergen's 7 request bodies), contradicting the design's own intent
        # that the aspect stays "present via its models/schemas". Only prune when the entity
        # actually owns endpoints; an endpoint-less entity keeps its (elsewhere-referenced) schemas.
        # AUDIT #11: only prune when THIS entity owns endpoints (an endpoint-less aspect keeps
        # its elsewhere-referenced schemas). SWEEP-C: prune against the GLOBAL touched set, so a
        # schema returned by ANOTHER entity's endpoint is kept + drawn (not dropped for having no
        # LOCAL endpoint reference). The local set is folded in for parity/robustness.
        if endpoints:
            _touched = set(_global_touched)
            for _ep in endpoints:
                _touched.update(_ep.get("touch", []))
                if _ep.get("resp"):     # resp is now the BARE class (AUDIT #6) → a container-returned schema survives the prune
                    _touched.add(_ep["resp"])
            schemas = [s for s in schemas if s["cls"] in _touched]
        # intra: model→model FK inside the entity (via unknown at L2 → "")
        intra = sorted(({"s": model_id[e["source"]], "t": model_id[e["target"]], "via": ""}
                        for e in edges if e.get("kind") == "fk"
                        and e.get("source") in model_id and e.get("target") in model_id),
                       key=lambda x: (x["s"], x["t"]))
        # usecases: endpoints grouped by leading URL segments, at an entity-adaptive depth
        usecases: dict[str, dict[str, list]] = {}
        _uc_depth = _use_case_depth([ep["p"] for ep in endpoints])
        for ep in endpoints:
            seg = _use_case_key(ep["p"], _uc_depth)
            uc = usecases.setdefault(seg, {"cls": [], "eps": [], "fns": []})
            uc["eps"].append(ep["m"] + " " + ep["p"])
            if ep["fn"]:
                uc["fns"].append(ep["fn"])
            for c in ep["touch"]:
                if c not in uc["cls"]:
                    uc["cls"].append(c)
        # ── communities: the fixture algorithm — deterministic label-propagation over
        #    a graph of HANDLER functions + models + schemas, joined by touches + resp
        #    + intra-FK. Each cluster is a handler and the pieces it reads/returns, so
        #    the groups are function-named — the flow view. (Endpoints are the DEDUPED
        #    set, so an aspect entity's phantom routes never pollute the clustering.)
        adj: dict[str, set] = {}
        nodeset = {m["cls"] for m in models} | {s["cls"] for s in schemas}

        def _link(a: str, b: str) -> None:
            if a and b and a != b:
                nodeset.add(a); nodeset.add(b)
                adj.setdefault(a, set()).add(b)
                adj.setdefault(b, set()).add(a)

        for e in intra:
            _link(e["s"], e["t"])
        for ep in endpoints:
            h = ep["fn"]
            if not h:
                continue
            for c in ep["touch"]:
                _link(h, c)
            if ep["resp"]:
                _link(h, ep["resp"])
        label = {n: n for n in sorted(nodeset)}
        for _ in range(20):
            changed = False
            for n in sorted(nodeset):
                nb = adj.get(n)
                if not nb:
                    continue
                cnt: dict[str, int] = {}
                for m in nb:
                    cnt[label[m]] = cnt.get(label[m], 0) + 1
                best = min(sorted(cnt), key=lambda x: (-cnt[x], x))
                if best != label[n]:
                    label[n] = best; changed = True
            if not changed:
                break
        groups: dict[str, list[str]] = {}
        for n in nodeset:
            groups.setdefault(label[n], []).append(n)
        # the fixture keeps groups of >=3 and folds the rest into "misc"; hub = max degree
        communities: dict[str, list[str]] = {}
        misc: list[str] = []
        ci = 0
        for root in sorted(groups, key=lambda r: (-len(groups[r]), r)):
            mem = sorted(groups[root])
            if len(mem) < 3:
                misc.extend(mem)
                continue
            ci += 1
            hub = max(mem, key=lambda c: (len(adj.get(c, ())), c))
            communities["c%d·%s" % (ci, hub[:12])] = mem
        if misc:
            communities["misc"] = sorted(misc)

        # ── fk_communities: the operator's NEW "Cluster by FK" filter — models joined
        #    by foreign key only (union-find over intra FK). A data-shape view, distinct
        #    from the function-flow communities above; drawn when the FK cluster is picked.
        parent = {m["cls"]: m["cls"] for m in models}

        def find(x: str) -> str:
            while parent.get(x, x) != x:
                parent[x] = parent.get(parent[x], parent[x])
                x = parent[x]
            return x

        for e in intra:
            if e["s"] in parent and e["t"] in parent:
                parent[find(e["s"])] = find(e["t"])
        fkcomp: dict[str, list[str]] = {}
        for m in models:
            fkcomp.setdefault(find(m["cls"]), []).append(m["cls"])
        fk_communities: dict[str, list[str]] = {}
        fi = 0
        for root in sorted(fkcomp, key=lambda r: (-len(fkcomp[r]), r)):
            fi += 1
            mem = sorted(fkcomp[root])
            hub = max(mem, key=lambda c: (MI.get(c, {}).get("usage", 0), c))
            fk_communities["f%d·%s" % (fi, hub)] = mem

        usefns = sorted(({"fn": fn, "uses": n} for fn, n in (usefns_by.get(slug, {})).items()),
                        key=lambda x: (-x["uses"], x["fn"]))[:40]
        lv["pieces"][slug] = {"models": models, "schemas": schemas, "endpoints": endpoints,
                              "intra": intra, "usecases": usecases, "communities": communities,
                              "fk_communities": fk_communities, "usefns": usefns}

    # ── fn_edges — cross-file function CALLS (graft only; honest-empty else) ───
    if graft and graft.get("present") and graft.get("fn_edges"):
        lv["fn_edges"] = sorted(graft["fn_edges"],
                                key=lambda e: (e.get("ss", ""), e.get("ds", ""), e.get("s", ""), e.get("t", "")))

    # ── P2b: the FRONTEND arm — graft's classified TS pieces homed to entities +
    #    FE-native buckets (design-system · app-shell · UI-only-domain candidates).
    #    Two render forms read this: a stacked BAND in the Layers level (pieces[slug].
    #    frontend.by_kind) and a companion frontend CIRCLE per entity in the cluster
    #    graph (pieces[slug].frontend.pieces + the buckets). Scaffold rides SEPARATELY
    #    for a toggle. Honest-empty when the graft arm is absent or the repo has no TS.
    fe = (graft or {}).get("frontend") or {}
    fe_stats = fe.get("stats") or {}
    if fe_stats.get("total"):
        ent_slugs = {n["slug"] for n in l1_nodes}
        cand = {c["name"] for c in fe_stats.get("candidate_entities", [])}
        homed: dict[str, list[dict[str, Any]]] = {}
        for n in fe.get("nodes", []):
            homed.setdefault(n.get("home"), []).append(n)
        from _a3_graft import _fe_pair                          # the C split renamed matched homes fe·<ent> —
        folded: set[str] = set()                                # the lab folds them by their PAIR (review 52[0]:
        for home, fnodes in homed.items():                      # fold-by-slug matched nothing and every paired
            pair = _fe_pair(home)                               # estate mislabeled as "no backend entity")
            slug = pair if pair in ent_slugs else (home if home in ent_slugs else None)
            if slug:
                lv["pieces"].setdefault(slug, {})["frontend"] = _fe_slim(fnodes)
                folded.add(home)
        lv["fe_buckets"] = [                                    # ONLY true buckets + candidate features remain
            {"name": home, "candidate": home in cand, **_fe_slim(fnodes)}
            for home, fnodes in sorted(homed.items()) if home not in folded]
        lv["fe_edges"] = fe.get("edges", [])                   # FE composition wires (cluster render)
        lv["fe_scaffold"] = [{"id": n["id"], "n": n.get("name"), "k": n["kind"], "home": n.get("home")}
                             for n in sorted(fe.get("scaffold", []), key=lambda x: x["id"])]
        lv["frontend"] = {"present": True, "total": fe_stats["total"],
                          "by_home": fe_stats.get("by_home", {}),
                          "candidate_entities": fe_stats.get("candidate_entities", []),
                          "scaffold_total": fe_stats.get("scaffold_total", 0)}
    else:
        lv["frontend"] = {"present": False}
        lv["fe_buckets"] = []
        lv["fe_edges"] = []
        lv["fe_scaffold"] = []

    return lv


def emit(levels: dict[str, Any], center_out: Path) -> None:
    """Write levels.json (diffable) + levels.js (window.GABE_LEVELS)."""
    center_out.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(levels, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    (center_out / "levels.json").write_text(payload + "\n", encoding="utf-8")
    (center_out / "levels.js").write_text("window.GABE_LEVELS = " + payload + ";\n", encoding="utf-8")
