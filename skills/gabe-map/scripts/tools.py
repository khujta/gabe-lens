#!/usr/bin/env python3
"""tools — the seven gabe-map v1 tool bodies over mapquery (READ-ONLY except who_calls' gated emit).

Every body returns a dict; the server renders it as ONE text block (D5/§5: the harness hides text
when structuredContent is present, so there is no second channel). Every list is capped and the
cap is named; every answer carries the map stamp; every missing block yields a `reason`, never a
crash. Contracts: skills/gabe-map/references/map-spec.md.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mapquery as mq  # noqa: E402

HTTP = re.compile(r"^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(/\S*)$", re.I)
TASK = re.compile(r"^TASK\s+(\S+)$", re.I)   # P1 (2026-09-06): a worker task root, addressed the way the map names it (endpoint:TASK <name>); kind says `task`, never `endpoint`
CID = re.compile(r"^C\d{1,6}$")
NO_MAP_HINT = "this project has no codebase map; Grep/Glob are the source of truth here. Build one: /gabe-cc-init."


def norm_path(p: str) -> str:
    p = re.sub(r"^/api/v\d+", "", p or "")
    p = re.sub(r"\$?\{[^}]*\}", "{}", p)
    return (p.rstrip("/") or "/")


def _ctx(args: dict, roots: list[str] | None):
    root, source = mq.resolve_root(args.get("root"), roots)
    center, reason = mq.open_center(root)
    return center, root, source, reason


def _absent(root: str, source: str, reason: str) -> dict:
    out = {"present": False, "root": root, "root_source": source, "reason": reason}
    if "ruling R8" not in reason:
        out["hint"] = NO_MAP_HINT
    return out


def _base(center: mq.Center, root: str, source: str) -> dict:
    return {"present": True, "root": root, "root_source": source, "center": str(center.dir), **mq.stamp(center)}


# ── map_status ─────────────────────────────────────────────────────────────────
def t_map_status(args: dict, roots) -> dict:
    center, root, source, reason = _ctx(args, roots)
    if not center:
        out = _absent(root, source, reason)
        out.update({"kdbp_present": os.path.isdir(os.path.join(root, ".kdbp")), "server_sha": mq.server_sha()})
        return out
    a, c = center.archmap, center.c4
    ents = center.entities()
    fi = a.get("function_insight") or {}
    out = _base(center, root, source)
    out["entities"] = sorted(ents)
    sch_rows = sum(len(e.get("schemas") or []) for e in ents.values())
    sch_distinct = len({(s_.get("cls"), s_.get("file")) for e in ents.values() for s_ in (e.get("schemas") or [])})
    out["counts"] = {
        "entities": len(ents),
        "endpoints": sum(len(e.get("endpoints") or []) for e in ents.values()),
        "models": sum(len(e.get("models") or []) for e in ents.values()),
        "schemas": sch_distinct,                       # F5: distinct (cls, file) — a schema several entities consume is ONE schema
        **({"schemas_rows": sch_rows} if sch_rows != sch_distinct else {}),
        "files_mapped": len(center.idx()["mapped_files"]),
        "functions_py": len(fi),
        "fe_pieces": len((c.get("fe") or {}).get("pieces") or []),
        "tasks": len(a.get("task_roots") or []),
        "streams": sum(1 for e in ents.values() for ep in (e.get("endpoints") or []) if ep.get("stream")),
        "providers": ((c.get("stats") or {}).get("providers") or {}).get("count") or 0,
        "app_middleware": len(a.get("app_middleware") or []),
    }
    out["map_health"] = mq.map_health(a, c)         # F5: where the map is PARTIAL — one helper, three homes (map_census · center_overview read the same object)
    census = a.get("file_census") or {}
    out["file_census"] = {"claimed": census.get("claimed"), "unclaimed": len(census.get("unclaimed") or [])} if census else {"reason": "no file_census block"}
    wiring = Path(root) / "graft" / ".graph" / "wiring.json"
    g = {"index_present": wiring.is_file()}
    if wiring.is_file():
        try:
            g["wiring_mtime"] = int(wiring.stat().st_mtime)
            g["live_index_hash"] = hashlib.sha256(wiring.read_bytes()).hexdigest()[:12]
        except OSError as exc:
            g["reason"] = str(exc)
    g["committed_index_hash"] = ((c.get("stats") or {}).get("graft") or {}).get("index_hash")
    if g.get("live_index_hash") and g.get("committed_index_hash"):
        g["match"] = g["live_index_hash"] == g["committed_index_hash"]
        if not g["match"]:
            g["note"] = "graft index refreshed since the map's regen — the map's calls/imports edges may lag the index; not source staleness"
    out["graft"] = g
    out["kdbp_present"] = os.path.isdir(os.path.join(root, ".kdbp"))
    infl = mq._load_json(center.dir / "inflight.json")
    if infl:
        out["inflight"] = {"head": infl.get("head"), "active": infl.get("active"), "current_phase": infl.get("current_phase")}
        if infl.get("head"):
            rc, cnt, _ = mq.sh(["git", "-C", root, "rev-list", "--count", "%s..HEAD" % infl["head"]])
            out["inflight"]["commits_behind"] = int(cnt.strip()) if rc == 0 and cnt.strip().isdigit() else None
    else:
        out["inflight"] = {"reason": "no inflight.json (E8 beat tail never ran here, or gitignored and absent)"}
    out["regen_cmd"] = "scripts/refresh_center.sh regen"
    out["server_sha"] = mq.server_sha()
    return out


# ── entity_context ─────────────────────────────────────────────────────────────
def _config_only(center: mq.Center) -> bool:
    """F7/F8 (2026-09-06): no adoption.json AND the c4 l1 nodes say status config-only → bootstrap_center.sh built this map
    from center.config.json alone; the entities are the registry, out loud (nothing is 'unregistered')."""
    if center.adoption:
        return False
    return any(isinstance(n, dict) and n.get("status") == "config-only" for n in ((center.c4.get("l1") or {}).get("nodes") or []))


CONFIG_ONLY = "config-only (bootstrap_center.sh — no adoption.json; /gabe-cc-init to adopt)"


def _app_mw(a: dict) -> tuple[list, str]:
    """F1: the ASGI-scope middleware — applies to EVERY request before the route's Depends; a list + its note."""
    rows = [{k: m.get(k) for k in ("cls", "file", "line", "order", "scope")} for m in (a.get("app_middleware") or []) if isinstance(m, dict)]
    if rows:
        return rows, "ASGI-scope — applies to EVERY request before the route's Depends"
    _, state = mq.health_key(a, "app_middleware")                  # P2 decides: the pass ran (sentinel) vs an older map
    return rows, ("none recorded — the app declares no ASGI middleware (the pass ran: route_mounts is on this map)" if state == "clean"
                  else "none recorded — this map never ran the app-middleware pass; regen to know")


def _entity_list(center: mq.Center) -> list[dict]:
    mapped = set(center.entities())
    rows, seen = [], set()
    cfg_only = _config_only(center)
    for s in (center.adoption.get("sections") or []):
        slug = s.get("entity")
        if not slug:
            continue
        seen.add(slug)
        rows.append({"slug": slug, "display_name": s.get("display_name") or s.get("label") or slug,
                     "rank": s.get("rank"), "status": s.get("status"), "mapped": slug in mapped})
    for slug in sorted(mapped - seen):
        rows.append({"slug": slug, "display_name": slug, "rank": None, "status": "config-only" if cfg_only else None, "mapped": True,
                     "note": "config-only registry" if cfg_only else "in archmap, not in adoption.json"})
    return rows


def _counts_with_streams(code: dict) -> dict:
    counts = dict(code.get("counts") or {})
    counts["streams"] = sum(1 for e in (code.get("endpoints") or []) if isinstance(e, dict) and e.get("stream"))
    return counts


def _project_pack(pack: dict, detail: str) -> dict:
    """brief = counts + names · full = capped projection · raw = untouched (parity with entity-context.py --json)."""
    if detail == "raw":
        return pack
    code = pack.get("code") or {}
    out = {k: v for k, v in pack.items() if k not in ("code",)}
    if not code:
        out["code"] = None
        return out
    files_by_layer: dict[str, list] = {}
    for row in code.get("files") or []:
        if len(row) >= 2:
            files_by_layer.setdefault(row[0], []).append(row[1])
    if detail == "brief":
        reg = out.get("registry") or {}
        if reg:
            out["registry"] = {k: reg.get(k) for k in ("rank", "status", "checklist_done", "checklist_total", "approved_walk")}
        b = out.get("bindings") or {}
        if b:
            out["bindings"] = {"test_rx": b.get("test_rx"), "proofs": len(b.get("proofs") or []),
                               "models_allowlist": len(b.get("models_allowlist") or []),
                               "code_globs": {k: len(v) for k, v in (b.get("code_globs") or {}).items()} if isinstance(b.get("code_globs"), dict) else b.get("code_globs")}
        rel = out.get("relations") or {}
        if rel:
            out["relations"] = {"related_entities": rel.get("related_entities"), "unresolved_tables": rel.get("unresolved_tables"),
                                "fk_out": len(rel.get("fk_out") or [])}
        eps, note_e = mq.cap_list(["%s %s%s" % (e.get("method"), e.get("path"), " ⚡" if e.get("stream") else "") for e in code.get("endpoints") or []])
        out["code"] = {"counts": _counts_with_streams(code),
                       "endpoints": eps, "endpoints_note": note_e,
                       "models": [m.get("cls") for m in code.get("models") or []][:mq.CAP],
                       "schemas": [s.get("cls") for s in code.get("schemas") or []][:mq.CAP],
                       "files_by_layer": {k: len(v) for k, v in files_by_layer.items()}}
        return out
    # full
    eps = [{"method": e.get("method"), "path": e.get("path"), "fn": e.get("fn"), "file": e.get("file"),
            "status": e.get("status"), "resp": e.get("resp"), "stream": bool(e.get("stream")),
            "gates": [m.get("name") for m in (e.get("middleware") or []) if isinstance(m, dict) and m.get("gate")]} for e in code.get("endpoints") or []]
    models = [{"cls": m.get("cls"), "table": m.get("table"), "file": m.get("file"), "cols": len(m.get("cols") or []),
               "cols_head": [c[0] for c in (m.get("cols") or [])[:10]], "fks": m.get("fks"), "doc": (m.get("doc") or "")[:160]}
              for m in code.get("models") or []]
    schemas = [{"cls": s.get("cls"), "file": s.get("file"), "fields": len(s.get("fields") or []), "doc": (s.get("doc") or "")[:160]}
               for s in code.get("schemas") or []]
    fbl = {}
    for k, v in files_by_layer.items():
        lst, note = mq.cap_list(v)
        fbl[k] = {"files": lst, "note": note}
    defines = {}
    for path, names in (code.get("defines") or {}).items():
        lst, note = mq.cap_list([n.rstrip("()") for n in names])
        defines[path] = lst + ([note] if note else [])
    e_l, e_n = mq.cap_list(eps); m_l, m_n = mq.cap_list(models); s_l, s_n = mq.cap_list(schemas)
    out["code"] = {"counts": _counts_with_streams(code), "endpoints": e_l, "endpoints_note": e_n, "models": m_l, "models_note": m_n,
                   "schemas": s_l, "schemas_note": s_n, "files_by_layer": fbl, "defines": dict(list(defines.items())[:mq.CAP])}
    return out


def t_entity_context(args: dict, roots) -> dict:
    center, root, source, reason = _ctx(args, roots)
    if not center:
        return _absent(root, source, reason)
    slug = (args.get("slug") or "").strip()
    detail = (args.get("detail") or "brief").lower()
    if detail not in ("brief", "full", "raw"):
        raise mq.MapStop("detail must be brief | full | raw")
    out = _base(center, root, source)
    if not slug or slug == "list":
        out["entities"] = _entity_list(center)
        if _config_only(center):
            out["registry"] = CONFIG_ONLY
        return out
    mod = mq.entity_context_module()
    pack = mod.build_pack(slug, center.dir, center.config, center.archmap, center.adoption)
    out["entity"] = _project_pack(pack, detail)
    out["detail"] = detail
    if detail != "raw":
        c = center.c4
        l1 = [e for e in ((c.get("l1") or {}).get("edges") or []) if e.get("source") == slug or e.get("target") == slug]
        out["c4"] = {"l1_edges": [{"source": e.get("source"), "target": e.get("target"), "weight": e.get("weight"), "kinds": e.get("kinds")} for e in l1][:mq.CAP],
                     "l1_note": "calls/imports are graft FLOORS (inferred cross-file); fk is exact",
                     "l2_node_kinds": {}, "providers": []}
        for n in ((c.get("l2") or {}).get(slug) or {}).get("nodes") or []:
            k = n.get("kind") or "?"
            if k == "endpoint" and str(n.get("id") or "").startswith("endpoint:TASK "):
                k = "task"                                   # F3: a worker task root is not an HTTP endpoint — counted apart
            if k == "provider":
                out["c4"]["providers"].append(n.get("label") or str(n.get("id") or "").split(":", 1)[-1])
            out["c4"]["l2_node_kinds"][k] = out["c4"]["l2_node_kinds"].get(k, 0) + 1
        out["c4"]["providers"] = sorted(set(out["c4"]["providers"]))
        homes = (c.get("fe") or {}).get("homes") or []
        fe_home = next((h for h in homes if isinstance(h, dict) and h.get("id") == "fe·%s" % slug), None)
        if fe_home:
            fe_home = dict(fe_home)
            fe_home["homing"] = ((c.get("stats") or {}).get("fe") or {}).get("homing")   # layout | config — which witness homed the pieces
        out["c4"]["fe_home"] = fe_home if fe_home else {"reason": "no fe·%s home in GABE_C4.fe" % slug}
        ent_code = (out.get("entity") or {}).get("code")
        if isinstance(ent_code, dict) and isinstance(ent_code.get("counts"), dict):
            ent_code["counts"]["tasks"] = out["c4"]["l2_node_kinds"].get("task", 0)
        if _config_only(center):
            out["registry"] = CONFIG_ONLY
        cov = (center.archmap.get("coverage") or {}).get(slug)
        out["coverage"] = cov if cov else {"reason": "no coverage row for %s" % slug}
    return out


# ── touches ────────────────────────────────────────────────────────────────────
def _cases_split(rows) -> tuple[list, list]:
    cases, files = [], []
    for grp in (rows or {}).values() if isinstance(rows, dict) else []:
        for r in grp or []:
            if r.get("state") == "file" or not r.get("cid"):
                files.append({"tfile": r.get("tfile"), "corpus": r.get("corpus"), "n": r.get("n")})
            else:
                cases.append({"cid": r.get("cid"), "name": r.get("name"), "state": r.get("state"), "corpus": r.get("corpus"), "tfile": r.get("tfile")})
    return cases, files


def detect_kind(target: str, center: mq.Center) -> tuple[str, object]:
    t = target.strip()
    idx = center.idx()
    m = HTTP.match(t)
    if m:
        return "endpoint", (m.group(1).upper(), m.group(2))
    m = TASK.match(t)
    if m:
        return "task", m.group(1)
    if "::" in t or "#" in t:
        return "function", t.replace("#", "::", 1)
    if "/" in t or t.endswith(mq.SRC_EXT):
        return "file", t
    if CID.match(t):
        return "case", t
    if t in center.entities():
        return "entity", t
    if t in idx["cls"]:
        return idx["cls"][t][1] or "model", t
    if t in idx["task_by_name"] and t not in idx["fn_by_bare"]:    # P1: the REGISTERED task name — only when function_insight never saw it (review 2026-09-06: 36 of 46 onyx names collide)
        return "task", t
    if t in idx["defines"] and t not in idx["fn_by_bare"]:
        return "define", t
    if t in idx["task_by_fn"] and t not in idx["fn_by_bare"]:      # the task fn when function_insight never saw it
        return "task", idx["task_by_fn"][t]["root"].get("path")
    return "function_bare", t


def _fn_record(center: mq.Center, key: str) -> dict:
    a, idx = center.archmap, center.idx()
    rec = (a.get("function_insight") or {}).get(key)
    if not rec:
        return {"key": key, "reason": "not in function_insight"}
    ti = a.get("test_insight") or {}
    qual = key.split("::", 1)[1]        # F2 (2026-09-06): join on the QUALIFIED name — a bare `search` must never bridge Svc.search to Other.search
    reaching, unverifiable = [], 0
    for (slug, nid), n in idx["c4_nodes"].items():
        if n.get("kind") != "endpoint":
            continue
        b = n.get("behind") or {}
        if qual in (b.get("names") or []):
            reaching.append(nid)
        elif b.get("names_more") or b.get("truncated"):
            unverifiable += 1
    cases, files = _cases_split((ti.get("by_function") or {}).get(key))
    gated = sum(1 for ent in center.entities().values() for ep in (ent.get("endpoints") or []) for m in (ep.get("middleware") or [])
                if isinstance(m, dict) and m.get("gate") and m.get("fn") == key)
    troot = next((name for name, r in idx["task_by_name"].items() if r.get("fnkey") == key.replace("::", "#", 1)), None)
    return {"key": key, "entity": rec.get("entity"), "layer": rec.get("layer"), "handler": rec.get("handler"),
            **({"gated_endpoints": {"count": gated, "see": "mcp__gabe-map__gates (by callee · fn key · argument string)"}} if gated else {}),
            **({"task_root": {"name": troot, "see": "touches 'TASK %s' — dispatchers, behind, the worker note" % troot}} if troot else {}),
            "handler_of": idx["handler_of"].get(key), "async": rec.get("async"), "lines": rec.get("lines"),
            "returns": rec.get("returns"), "doc": (rec.get("doc") or "")[:160], "usage": rec.get("usage"),
            "access_ops": (rec.get("access") or {}).get("ops"),
            "tests": {"cases": cases[:mq.CAP], "test_files": files[:mq.CAP]},
            "endpoints_reaching": {"found": reaching[:mq.CAP], "unverifiable": unverifiable,
                                   "floor": "behind.names is capped at 12 per endpoint and joins on the qualified name (Class.method) — a FLOOR, never an absence proof"}}


def t_touches(args: dict, roots) -> dict:
    center, root, source, reason = _ctx(args, roots)
    if not center:
        return _absent(root, source, reason)
    target = (args.get("target") or "").strip()
    if not target:
        raise mq.MapStop("target is required: a file path, model/schema/class name, function (bare or file::fn), entity slug, endpoint 'METHOD /path', task root 'TASK <name>', or case id")
    a, idx = center.archmap, center.idx()
    ti = a.get("test_insight") or {}
    kind, key = detect_kind(target, center)
    out = _base(center, root, source)
    out.update({"target": target, "kind": kind})
    if kind == "endpoint":
        method, path = key
        want = norm_path(path)
        found = None
        for slug, ent in center.entities().items():
            for ep in ent.get("endpoints") or []:
                if str(ep.get("method", "")).upper() == method and norm_path(ep.get("path", "")) == want:
                    found = (slug, ep)
                    break
            if found:
                break
        if not found:
            out.update({"matched": False, "normalized": "%s %s" % (method, want),
                        "reason": "no declared endpoint matches (normalization strips /api/vN and collapses {x})"})
            return out
        slug, ep = found
        fkey = "%s::%s" % (ep.get("file"), ep.get("fn"))
        nid = "endpoint:%s %s" % (method, ep.get("path"))
        node = idx["c4_nodes"].get((slug, nid)) or {}
        cases, files = _cases_split((ti.get("by_endpoint") or {}).get(fkey))
        mw_rows, mw_note = _app_mw(a)
        out.update({"matched": True, "entity": slug, "endpoint": {"method": method, "path": ep.get("path"), "handler": fkey,
                    "status": ep.get("status"), "resp": ep.get("resp"), "doc": (ep.get("doc") or "")[:160], "stream": bool(ep.get("stream")),
                    "middleware": ep.get("middleware"), "touches_own": ep.get("touches")},
                    "app_middleware": mw_rows, "app_middleware_note": mw_note,
                    "behind": node.get("behind") or {"reason": "no behind block (graft arm absent at regen)"},
                    "access": node.get("access") or {"reason": "no access block"},
                    "edges_out": [{"target": t, "kind": k} for t, k, _ in idx["edges_out"].get(nid, [])][:mq.CAP],
                    "screens_in": [{"source": s, "kind": k} for s, k, _ in idx["edges_in"].get(nid, []) if k == "bridge"][:mq.CAP],
                    "tests": {"cases": cases[:mq.CAP], "covered_by_test_files": files[:mq.CAP]}})
        web = ((center.c4.get("stats") or {}).get("web") or {})
        unm = web.get("unmatched") if isinstance(web.get("unmatched"), list) else []
        out["web_unmatched_fetches"] = [u for u in unm if isinstance(u, dict) and norm_path(str(u.get("p") or u.get("path") or "")) == want
                                        and str(u.get("m") or u.get("method") or "").upper() == method][:mq.CAP] or None   # the emitter writes m/p (review 2026-09-06)
        return out
    if kind == "task":                                             # F3: a worker task root, by its registered name
        rec = idx["task_by_name"].get(key)
        if not rec:
            out.update({"matched": False, "reason": "no task root named %r — task_roots lists %d registered task(s); a task registered under a "
                        "computed name is not on the map (tasks.stats.unresolved names those kinds)" % (key, len(idx["task_by_name"]))})
            return out
        root_, nid, slug = rec["root"], rec["nid"], rec["slug"]
        node = (idx["c4_nodes"].get((slug, nid)) or {}) if slug else {}
        fx = center.fn_index()
        disp = ([{"from": s_, "conf": cf} for s_, rel, cf in fx["fn_in"].get(rec["fnkey"] or "", []) if rel == "dispatches"][:mq.CAP]
                if fx["present"] else {"reason": "no levels.json — dispatch edges unread"})
        hkey = "%s::%s" % (root_.get("file"), root_.get("fn"))
        cases, files = _cases_split((ti.get("by_endpoint") or {}).get(hkey))
        out.update({"matched": True, "entity": slug,
                    "task": {"name": key, "fn": root_.get("fn"), "file": root_.get("file"), "handler": hkey, "doc": (root_.get("doc") or "")[:160]},
                    "dispatched_by": disp, "stream": False,
                    "app_middleware": [], "app_middleware_note": "ASGI middleware wraps HTTP requests — a worker task runs outside it",
                    "behind": node.get("behind") or {"reason": "no behind block (graft arm absent at regen, or the task is not on the c4 graph)"},
                    "access": node.get("access") or {"reason": "no access block"},
                    "edges_out": [{"target": t, "kind": k} for t, k, _ in idx["edges_out"].get(nid, [])][:mq.CAP],
                    "tests": {"cases": cases[:mq.CAP], "covered_by_test_files": files[:mq.CAP]},
                    "unresolved_dispatch_kinds": list(((a.get("tasks") or {}).get("stats") or {}).get("unresolved") or []),
                    "note": "a TASK root is a worker entrypoint dispatched by name (Celery / ARQ / Taskiq), never an HTTP endpoint; "
                            "tasks registered under a computed name are NOT on this list — grep the broker for the rest"})
        return out
    if kind == "function":
        out["function"] = _fn_record(center, key)
        return out
    if kind == "function_bare":
        keys = idx["fn_by_bare"].get(key) or []
        if not keys:
            trec = idx["task_by_fn"].get(key) or idx["task_by_name"].get(key)
            if trec:
                return t_touches({"target": "TASK %s" % trec["root"].get("path"), "root": root}, roots)
            out.update({"found": False, "reason": "no function, class, entity, file, endpoint or task root named %r in the map — a map miss or a new name; grep is the floor" % key})
            return out
        if len(keys) > 1:
            out.update({"ambiguous": [{"key": k, "entity": (a.get("function_insight") or {}).get(k, {}).get("entity")} for k in keys][:mq.CAP],
                        "reason": "%d functions share this bare name — pass file::name" % len(keys)})
            return out
        out["function"] = _fn_record(center, keys[0])
        return out
    if kind == "file":
        p = key
        owners = idx["file_owners"].get(p) or []
        mi = a.get("model_insight") or {}
        defined = [c for c, r in mi.items() if r.get("file") == p]
        referenced = sorted({c for c, r in mi.items() for ref in (r.get("internal_refs") or []) if ref.get("file") == p})
        is_test = "/tests/" in p or "/test_" in p or ".test." in p or ".spec." in p or "/__tests__/" in p
        pieces_here = [x for x in ((center.c4.get("fe") or {}).get("pieces") or []) if isinstance(x, dict) and x.get("file") == p]
        fe_pieces = [x.get("name") or x.get("id") for x in pieces_here]
        stem = re.sub(r"\.[a-z]+$", "", p)
        web = idx["web_by_stem"].get(stem)
        guard = (a.get("guard_insight") or {}).get("files", {}).get(p)
        defs = []
        for slug, ent in center.entities().items():
            defs += [n.rstrip("()") for n in (ent.get("defines") or {}).get(p, [])]
        out.update({"owners": [{"entity": s, "layer": l, "lines": n} for s, l, n in owners] or [],
                    "owned": bool(owners), "census": _census_entry(a, p),
                    "defines": mq.cap_list(sorted(set(defs)))[0], "functions": mq.cap_list(idx["fn_by_file"].get(p, []))[0],
                    "models_defined": defined[:mq.CAP], "models_referenced": referenced[:mq.CAP],
                    "tests_reaching": ((ti.get("by_file") or {}).get(p) or {}).get("reach", [])[:mq.CAP],
                    "guard": {"share": guard.get("share"), "unguarded": guard.get("unguarded"), "proven": guard.get("proven")} if guard else {"reason": "no guard row"},
                    "fe_pieces": fe_pieces[:mq.CAP],
                    "web_node": {"entity": web[0], "id": web[1].get("id")} if web else None})
        if pieces_here or web:                                     # F9 (2026-09-06): the screen→endpoint leg as FIELDS, not a tool
            _FEK = ("name", "kind", "hrole", "feClass", "fed2w", "channel", "cache", "sites", "wsites", "homed_by", "span")
            calls = [{"endpoint": t, "kind": k} for t, k, _ in idx["edges_out"].get(web[1].get("id"), [])] if web else []
            out["fe"] = {"pieces": [{k2: x.get(k2) for k2 in _FEK if x.get(k2) is not None} for x in pieces_here][:mq.CAP],
                         "pieces_more": max(0, len(pieces_here) - mq.CAP),
                         "calls": calls[:mq.CAP], "calls_note": "bridge = a fetch site in this file matched to the endpoint it names (the web arm, a FLOOR)"}
        if is_test:
            ex = (ti.get("exercises") or {}).get(p)
            out["exercises"] = ex if ex else {"reason": "test file not in test_insight.exercises"}
        return out
    if kind == "case":
        home = (ti.get("case_home") or {}).get(key)
        own = {k: v for k, v in (ti.get("case_own") or {}).items() if k.endswith("_" + key) or ("_%s" % key) in k}
        out.update({"case": key, "home": home or {"reason": "case id not in the map's case_home"}, "owns": dict(list(own.items())[:5])})
        return out
    if kind == "entity":
        ec = t_entity_context({"slug": key, "detail": "brief", "root": root}, roots)
        ec.update({"target": target, "kind": "entity"})
        return ec
    if kind in ("model", "schema"):
        return _model_touches(center, key, kind, out)
    if kind == "define":
        homes = idx["defines"].get(key) or []
        methods = sorted(k for k in (a.get("function_insight") or {}) if ("::%s." % key) in k)
        out.update({"defined_in": [{"entity": s, "file": f} for s, f in homes][:mq.CAP], "methods": methods[:mq.CAP],
                    "tests_reaching": sorted({t for _, f in homes for t in ((ti.get("by_file") or {}).get(f) or {}).get("reach", [])})[:mq.CAP]})
        return out
    out["reason"] = "unhandled kind %s" % kind
    return out


def _census_entry(a: dict, path: str):
    for row in (a.get("unparseable") or []):                       # F10: a file the scanners could not parse is BLIND by construction — and says why
        f, why = (row[0], str(row[1])) if isinstance(row, (list, tuple)) and len(row) > 1 else (row, "unparseable")
        if f == path:
            return {"claimed": False, "reason": why if why.startswith("unparseable") else "unparseable: %s" % why,
                    "note": "definitions here are absent because the scanner skipped the file, not because it is empty"}
    for row in (a.get("file_census") or {}).get("unclaimed") or []:
        if row.get("file") == path:
            return {"claimed": False, "reason": row.get("reason"), "fns": row.get("fns"), "routes": row.get("routes")}
    return {"claimed": True} if (a.get("file_census") or {}) else {"reason": "no file_census block"}


def _model_touches(center: mq.Center, cls: str, kind: str, out: dict) -> dict:
    a, idx = center.archmap, center.idx()
    mi = (a.get("model_insight") or {}).get(cls) or {}
    ti = a.get("test_insight") or {}
    defn = None
    for slug, ent in center.entities().items():
        for m in (ent.get("models") if kind == "model" else ent.get("schemas")) or []:
            if m.get("cls") == cls:
                defn = (slug, m)
                break
        if defn:
            break
    fk_in = []
    if defn and defn[1].get("table"):
        table = defn[1]["table"]
        for slug, ent in center.entities().items():
            for m in ent.get("models") or []:
                for col, ref in (m.get("fks") or {}).items():
                    if ref.split(".")[0] == table:
                        fk_in.append({"model": m.get("cls"), "col": col, "entity": slug})
    fns = [{"fn": k, "rw": rw} for k, rw in idx["model_fns"].get(cls, [])]
    nid = "%s:%s" % (kind, cls)
    edges = {}
    for s, k, slug in idx["edges_in"].get(nid, []):
        edges.setdefault(k, []).append({"source": s, "entity": slug})
    cases, files = _cases_split((ti.get("by_model") or {}).get(cls))
    out.update({"cls": cls, "entity": mi.get("entity") or (defn[0] if defn else None), "file": mi.get("file"),
                "definition": ({"table": defn[1].get("table"), "cols": len(defn[1].get("cols") or defn[1].get("fields") or []),
                                "fks": defn[1].get("fks"), "doc": (defn[1].get("doc") or "")[:160]} if defn else {"reason": "not in any entity's models/schemas"}),
                "insight": {k: mi.get(k) for k in ("fk_in", "internal", "touches", "usage", "god", "base") if k in mi},
                "fk_in_models": fk_in[:mq.CAP],
                "functions_rw": fns[:mq.CAP], "functions_rw_note": "from function_insight.access.ops (r/w per function)",
                "referenced_from": [{"file": r.get("file"), "defs": r.get("defs")} for r in (mi.get("internal_refs") or [])][:mq.CAP],
                "endpoint_edges": {k: v[:mq.CAP] for k, v in edges.items()},
                "endpoint_edges_note": "l2 ∪ cross_edges; kinds as emitted (touches/reads_from/writes_to/consumes; nests = schema composition)",
                "tests": {"cases": cases[:mq.CAP], "covered_by_test_files": files[:mq.CAP]}})
    return out


# ── who_calls ──────────────────────────────────────────────────────────────────
def _map_confidence(root: str) -> dict:
    """The S14 tally read as a per-answer field: ACTIVE missed edges for the callers arm (fresh tier, no store)."""
    ledger = os.path.join(root, ".kdbp", "map-deltas-rollup.jsonl")
    if not os.path.isfile(ledger):
        return {"active_missed_edges": None, "note": "no map-delta ledger yet — the index has not been contradicted by grep here"}
    rc, cnt, _ = mq.sh(["git", "-C", root, "rev-list", "--count", "HEAD"])
    n_now = int(cnt.strip()) if rc == 0 and cnt.strip().isdigit() else 0
    horizon = int(os.environ.get("MAP_DELTAS_H", "40"))
    active, total = 0, 0
    try:
        for line in open(ledger, encoding="utf-8"):
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            if o.get("v") != 2 or o.get("gen") != "_a3_graft.calls":
                continue
            total += 1
            if n_now - int(o.get("last_n") or 0) < horizon:
                active += 1
    except OSError:
        pass
    return {"active_missed_edges": active, "edges_total": total,
            "note": ("%d active missed caller edge(s) tallied — confirm with grep" % active) if active else "no active missed caller edges tallied"}


def t_who_calls(args: dict, roots) -> dict:
    sym = (args.get("symbol") or "").strip()
    if not mq.SYMBOL_RE.match(sym):
        raise mq.MapStop("symbol must be an identifier ([A-Za-z_][A-Za-z0-9_]*)")
    direction = (args.get("direction") or "in").lower()
    if direction not in ("in", "out"):
        raise mq.MapStop("direction must be in (callers) or out (callees)")
    depth = str(args.get("depth") or "1")
    if not (depth == "all" or depth.isdigit()):
        raise mq.MapStop("depth must be an integer or 'all'")
    root, source = mq.resolve_root(args.get("root"), roots)
    center, reason = mq.open_center(root)
    transitive = direction == "out" or depth != "1"
    emit = bool(args.get("emit", True)) and not os.environ.get("GABE_MAP_NO_EMIT") and not transitive
    cj, cstat = mq.graft_callers(sym, root, direction=direction, depth=depth)
    hits, gstat = mq.git_grep_hits(sym, root)
    allowed = list(roots or [])
    if os.environ.get("CLAUDE_PROJECT_DIR"):
        allowed.append(os.path.abspath(os.environ["CLAUDE_PROJECT_DIR"]))
    allowed = [mq.git_toplevel(p) or p for p in allowed] or None
    res = mq.two_arm(sym, root, cj, cstat, hits, gstat, emit=emit, cmd="mcp", allowed_roots=allowed)
    out = {"present": center is not None, "root": root, "root_source": source}
    if center:
        out.update(mq.stamp(center))
    else:
        out["map_note"] = reason
    out.update(res)
    out["direction"], out["depth"] = direction, depth
    if direction == "out":
        out["callees"] = out.pop("callers", [])
        out["callees_detail"] = out.pop("callers_detail", [])
    if transitive:
        out["emit_skipped"] = list(out.get("emit_skipped") or []) + ["transitive/callee queries never emit — the delta semantics are 'a DIRECT caller the index missed'"]
    out["map_confidence"] = _map_confidence(root) if center else None
    out["reach_line"] = mq.reach_line(res, root)
    out["floors"] = ["graft indexes .py/.ts/.tsx/.js/.jsx only; an empty reach is never an absence proof — grep -rn is",
                     "grep hits classified code vs prose (Python via tokenize, exact; others by line shape) — prose hits are listed, never emitted"]
    return out


# ── entity_shape ───────────────────────────────────────────────────────────────
def t_entity_shape(args: dict, roots) -> dict:
    center, root, source, reason = _ctx(args, roots)
    if not center:
        return _absent(root, source, reason)
    es = mq.pulse_module("entity_shape")
    endpoints, umap = es.load_project(Path(center.root))
    shape = es.entity_shape(endpoints, umap)
    out = _base(center, root, source)
    out["shape"] = shape
    out["one_line"] = es.one_line(shape) or "no finding — every URL domain is owned by exactly the entities the model expects"
    n_unres = len(((center.archmap.get("route_mounts") or {}).get("unresolved")) or [])
    out["mounts_unresolved"] = n_unres                              # F13: an unresolved include_router prefix = routes the domain table cannot see
    if n_unres:
        out["one_line"] += " · %d route mount(s) unresolved — the domain table is partial (map_census kind=mounts names them)" % n_unres
    domain = (args.get("domain") or "").strip().strip("/")
    if domain:
        owners: dict[str, int] = {}
        for e in endpoints:
            if es.url_domain(e.get("path", "")) == domain:
                owners[e.get("entity") or "(unclaimed)"] = owners.get(e.get("entity") or "(unclaimed)", 0) + 1
        out["domain"] = {"segment": domain, "owners": owners, "candidate": umap.get(domain),
                         "reason": None if owners else "no declared endpoint under /%s" % domain}
    base = (args.get("diff") or "").strip()
    if base:
        rc, text, err = mq.sh(["git", "-C", root, "diff", "--end-of-options", base])
        if rc != 0:
            out["diff"] = {"reason": "git diff %s failed: %s" % (base, err.strip()[:120])}
        else:
            new_routes = es.diff_new_routes(text)
            try:
                cls = es.classify_new_routes(new_routes, shape.get("owned") or {}, shape.get("orphans") or shape.get("orphan_domains") or [], umap)
            except Exception as exc:  # the classifier's shape may differ across versions — honest, never a crash
                cls = {"reason": "classifier unavailable: %s" % exc}
            out["diff"] = {"base": base, "new_routes": new_routes[:mq.CAP], "classified": cls}
    return out


# ── cases_for ──────────────────────────────────────────────────────────────────
_CID_TOKEN = re.compile(r"(?<![A-Za-z0-9])C(\d{1,5})(?:v\d+)?(?![0-9])")   # red-spec's canonical token (underscore-prefixed pytest names DO count)


def t_cases_for(args: dict, roots) -> dict:
    center, root, source, reason = _ctx(args, roots)
    if not center:
        return _absent(root, source, reason)
    target = (args.get("target") or "").strip()
    if not target:
        raise mq.MapStop("target is required: function (bare or file::fn), model, endpoint 'METHOD /path' or file::fn handler, task 'TASK <name>', file, or case id")
    a = center.archmap
    ti = a.get("test_insight") or {}
    idx = center.idx()
    out = _base(center, root, source)
    out["target"] = target
    kind, key = detect_kind(target, center)
    rows, via = None, None
    if kind == "function" or kind == "function_bare":
        keys = [key] if kind == "function" else (idx["fn_by_bare"].get(key) or [])
        if len(keys) > 1:
            out["ambiguous"] = keys[:mq.CAP]
        rows = {k: (ti.get("by_function") or {}).get(k) for k in keys[:1]} if keys else None
        rows = list(rows.values())[0] if rows else None
        via = "by_function"
        if rows is None and keys:
            rows = (ti.get("by_endpoint") or {}).get(keys[0]); via = "by_endpoint"
    elif kind in ("model", "schema"):
        rows, via = (ti.get("by_model") or {}).get(key), "by_model"
    elif kind == "endpoint":
        method, path = key
        want = norm_path(path)
        for slug, ent in center.entities().items():
            for ep in ent.get("endpoints") or []:
                if str(ep.get("method", "")).upper() == method and norm_path(ep.get("path", "")) == want:
                    rows = (ti.get("by_endpoint") or {}).get("%s::%s" % (ep.get("file"), ep.get("fn"))); via = "by_endpoint"
    elif kind == "task":                                            # F3: routed through P1; honest-empty by name
        rec = idx["task_by_name"].get(key)
        if rec:
            rows = (ti.get("by_endpoint") or {}).get("%s::%s" % (rec["root"].get("file"), rec["root"].get("fn"))); via = "by_endpoint"
        else:
            out["reason"] = "no task root named %r on the map" % key
    elif kind == "file":
        bf = (ti.get("by_file") or {}).get(key)
        out["test_files_reaching"] = (bf or {}).get("reach", [])[:mq.CAP]
        ex = (ti.get("exercises") or {}).get(key)
        if ex:
            out["exercises"] = ex
        via = "by_file"
    elif kind == "case":
        out["home"] = (ti.get("case_home") or {}).get(key) or {"reason": "not in case_home"}
        via = "case_home"
    cases, files = _cases_split(rows) if isinstance(rows, dict) else ([], [])
    out.update({"kind": kind, "via": via, "cases": cases[:mq.CAP], "covered_by_test_files": files[:mq.CAP],
                "census_note": "absence here = no census row in the map (a floor), not proof of no test"})
    if rows is None and kind not in ("file", "case") and "reason" not in out:
        out["reason"] = (("no by_endpoint row for TASK %s — task roots are not entity endpoints in test_insight; grep the task fn name in the tests" % key)
                         if kind == "task" else "no %s row for %s in the committed map" % (via or "test_insight", target))
    maxmap = 0
    for cid in (ti.get("case_home") or {}):
        m = _CID_TOKEN.search(cid)
        if m:
            maxmap = max(maxmap, int(m.group(1)))
    out["max_cid_in_map"] = maxmap or None
    rc, grep, _ = mq.sh(["git", "-C", root, "grep", "-ohIE", "(^|[^A-Za-z0-9])C[0-9]{1,5}(v[0-9]+)?([^0-9]|$)", "--",
                         ":(glob)**/*test*", ":(glob)**/*spec*", ":(glob)**/*Test*", ":(glob)**/tests/**",
                         ":(exclude,glob)docs/site/center/**", ":(exclude,glob)**/scripts/_a3_*.py", ":(exclude,glob)**/generators/**"], timeout=60)   # F11: the suite's own installs are not this repo's corpus
    if rc in (0, 1):
        found = [int(m.group(1)) for m in _CID_TOKEN.finditer(grep)]
        mx = max(found) if found else 0
        out["corpus"] = {"searched": "git grep -ohIE '(^|[^A-Za-z0-9])C[0-9]{1,5}(v[0-9]+)?([^0-9]|$)' -- '**/*test*' '**/*spec*' '**/tests/**' — excluding docs/site/center/** · scripts/_a3_*.py · **/generators/**",
                         "max_cid_seen": mx or None, "next_cid_floor": (mx + 1) if mx else None,
                         "note": "the corpus is the registry; the map may lag — re-grep before minting"}
        if not os.path.isdir(os.path.join(root, ".kdbp")):
            out["corpus"]["note"] = "no .kdbp/ — this repo mints no C-ids; the floor is a corpus artefact, not a registry"
    else:
        out["corpus"] = {"reason": "git grep unavailable (rc %d)" % rc}
    return out


# ── owner_of ───────────────────────────────────────────────────────────────────
def t_owner_of(args: dict, roots) -> dict:
    center, root, source, reason = _ctx(args, roots)
    if not center:
        return _absent(root, source, reason)
    paths = args.get("paths") or args.get("path") or []
    if isinstance(paths, str):
        paths = [paths]
    paths = [p.strip().lstrip("./") for p in paths if str(p).strip()]
    if not paths:
        raise mq.MapStop("path (or paths) is required")
    ws = mq.pulse_module("work_scope")
    globs = ws.entity_code_globs(center.config or {})
    idx = center.idx()
    a = center.archmap
    out = _base(center, root, source)
    out["results"] = []
    for p in paths[:mq.CAP]:
        is_dir = p.endswith("/") or (os.path.isdir(os.path.join(root, p)) and not os.path.isfile(os.path.join(root, p)))
        if is_dir:
            pre = p.rstrip("/") + "/"
            per: dict[str, int] = {}
            n = 0
            for f, owners in idx["file_owners"].items():
                if f.startswith(pre):
                    n += 1
                    for s, _, _ in owners:
                        per[s] = per.get(s, 0) + 1
            uncl = [r.get("file") for r in (a.get("file_census") or {}).get("unclaimed") or [] if str(r.get("file", "")).startswith(pre)]
            out["results"].append({"path": p, "kind": "dir", "mapped_files": n, "owners": per, "unclaimed_in_census": uncl[:mq.CAP]})
            continue
        owners = [{"entity": s, "layer": l, "lines": n} for s, l, n in idx["file_owners"].get(p, [])]
        glob_owners = sorted(s for s, pats in globs.items() if any(ws.matches(p, pat) for pat in pats))
        out["results"].append({"path": p, "kind": "file", "owners": owners, "owned": bool(owners),
                               "config_glob_owners": glob_owners, "census": _census_entry(a, p),
                               "note": None if owners else "unowned by the map — the map is BLIND here; the retro-trace found 82% of misses are coverage"})
    return out


# ── registry ───────────────────────────────────────────────────────────────────
def _schema(props: dict, required: list[str] | None = None) -> dict:
    s = {"type": "object", "properties": props, "additionalProperties": False}
    if required:
        s["required"] = required
    return s


ROOT_PROP = {"root": {"type": "string", "description": "Project root (defaults to the session's project; normalized to the git toplevel)."}}
RO = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}

TOOLS = [
    {"name": "map_status", "fn": t_map_status, "annotations": RO,
     "description": "Is there a codebase map here, how fresh, and where is it PARTIAL (map_health: mounts · unparseable · twin pass · web roots)? Entities, counts, graft state, regen command. Call first.",
     "inputSchema": _schema({**ROOT_PROP})},
    {"name": "entity_context", "fn": t_entity_context, "annotations": RO,
     "description": "One entity's slice: endpoints (⚡ stream; full adds gates), models, schemas, files by layer, FK relations, coverage, providers, tasks. Omit slug → the registered (or config-only) list. brief|full|raw.",
     "inputSchema": _schema({"slug": {"type": "string", "description": "Entity slug, or omit / 'list' for the registered entities."},
                             "detail": {"type": "string", "enum": ["brief", "full", "raw"], "description": "brief (default, ~300 tokens) · full (capped) · raw (uncapped pack)."}, **ROOT_PROP})},
    {"name": "touches", "fn": t_touches, "annotations": RO,
     "description": "What touches X in the map: a file, model/schema, function (bare or file::fn), entity, endpoint 'METHOD /path', task 'TASK <name>' or case id — owners, r/w functions, endpoints, gates, tests, edges.",
     "inputSchema": _schema({"target": {"type": "string", "description": "File path · Model/Schema/Class · function · file::fn · entity slug · 'GET /path' · 'TASK <name>' · C123"}, **ROOT_PROP}, ["target"])},
    {"name": "who_calls", "fn": t_who_calls, "annotations": {**RO, "readOnlyHint": False},
     "description": "Who calls / where is symbol X used (or what it calls: direction=out, depth=N|all): graft callers ∪ word-boundary git grep, hits code vs prose, misses emitted as deltas. Returns the Reach line.",
     "inputSchema": _schema({"symbol": {"type": "string", "description": "An identifier (function, class, hook name)."},
                             "direction": {"type": "string", "enum": ["in", "out"], "description": "in = callers (default) · out = callees."},
                             "depth": {"type": "string", "description": "1 (default), N hops, or 'all' — transitive blast radius via graft; only direction=in depth=1 emits deltas."},
                             "emit": {"type": "boolean", "description": "Append map-delta lines for code hits the map missed (default true; gated)."}, **ROOT_PROP}, ["symbol"])},
    {"name": "entity_shape", "fn": t_entity_shape, "annotations": RO,
     "description": "Which entity owns URL domain /x; detached URL domains and aspect entities, computed fresh from the map (caveated when route mounts are unresolved). Optional diff=<base> classifies routes a diff adds.",
     "inputSchema": _schema({"domain": {"type": "string", "description": "A URL domain segment to look up, e.g. 'settings'."},
                             "diff": {"type": "string", "description": "A git base (sha/branch) — classify routes added since it."}, **ROOT_PROP})},
    {"name": "cases_for", "fn": t_cases_for, "annotations": RO,
     "description": "Which test cases (C-ids) cover X — function, model, endpoint, task, file or case id — plus the corpus's max C-id and next-id floor (suite installs excluded). REUSE before NEW.",
     "inputSchema": _schema({"target": {"type": "string", "description": "function · file::fn · Model · 'GET /path' · 'TASK <name>' · file path · C123"}, **ROOT_PROP}, ["target"])},
    {"name": "owner_of", "fn": t_owner_of, "annotations": RO,
     "description": "Which entity owns these file paths (or a directory): map owners, center.config globs, and whether the census says the map is blind there — and why (unparseable files named).",
     "inputSchema": _schema({"path": {"type": "string", "description": "One repo-relative path or directory."},
                             "paths": {"type": "array", "items": {"type": "string"}, "description": "Several paths."}, **ROOT_PROP})},
]
BY_NAME = {t["name"]: t for t in TOOLS}

INSTRUCTIONS = """gabe-map: the project's committed codebase map as tools (read-only; who_calls may append gitignored map-delta lines).
When a project has a command center (docs/site/center/), ask the map BEFORE grepping:
- who calls X / where is X used → mcp__gabe-map__who_calls (both arms: index ∪ grep; hits marked code vs prose)
- what touches this file / model / endpoint / function → mcp__gabe-map__touches
- which entity owns this path or directory → mcp__gabe-map__owner_of
- which test cases cover X, next free C-id → mcp__gabe-map__cases_for
- one entity's endpoints/models/files → mcp__gabe-map__entity_context (omit slug to list entities)
- who owns URL domain /x, detached domains → mcp__gabe-map__entity_shape
- is there a map here, how stale → mcp__gabe-map__map_status (call first when unsure)
- find X by name (entity/endpoint/model/function/screen) → mcp__gabe-map__find · a file's definitions + signatures → mcp__gabe-map__outline
- orient in the codebase → mcp__gabe-map__center_overview · what does this change touch → mcp__gabe-map__blast_radius
- where is the map blind → mcp__gabe-map__map_census · how did the map change between refs → mcp__gabe-map__map_diff
- the center's actionable list → mcp__gabe-map__center_status · a review's drift subjects vs a base → mcp__gabe-map__review_drift
- which endpoints a gate / Permission.X guards; what ASGI middleware applies to every request → mcp__gabe-map__gates
- the ordered path from an endpoint or TASK to the models and providers it reaches (conf per hop) → mcp__gabe-map__trace
- a celery/background TASK root, a streaming endpoint, a provider (litellm · redis · …) → find / touches take "TASK <name>", stream=true, kind=provider
- where the map is PARTIAL (unparseable files · unresolved mounts · blocked twin pass · unscanned frontend roots) → mcp__gabe-map__map_census (map_status carries the one-line map_health)
The map is a FLOOR, never a scope: absence in an answer is not proof of absence — grep -rn remains the absence proof. A trace hop marked `inferred` is graft's guess, not a proof. Every answer stamps map@<head> · freshness. No center → the tools say so and point to Grep/Glob."""


def call(name: str, args: dict, roots: list[str] | None) -> tuple[dict, bool]:
    """→ (result, is_error). MapStop → an honest answer (is_error True so the model self-corrects on bad input)."""
    t = BY_NAME.get(name)
    if not t:
        raise KeyError(name)
    try:
        return t["fn"](args or {}, roots), False
    except mq.MapStop as exc:
        return {"stop": str(exc), "tool": name}, True


# ── wave 2 (the graft equivalents + map lifecycle) — registered after the helpers exist ──
import tools_wave2 as _w2  # noqa: E402
TOOLS.extend(_w2.TOOLS)
BY_NAME.update({t["name"]: t for t in _w2.TOOLS})
# ── wave 3 (2026-09-06, the repo-study tool pass): trace (the ordered path over levels.json) + gates (the inverse of middleware) ──
import tools_wave3 as _w3  # noqa: E402
TOOLS.extend(_w3.TOOLS)
BY_NAME.update({t["name"]: t for t in _w3.TOOLS})
