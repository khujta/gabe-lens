#!/usr/bin/env python3
"""tools_wave2 — the graft equivalents + map-lifecycle readers (operator ruling 2026-09-02, D10).

find (graft_find_code) · outline (graft_file_api) · center_overview (graft_repo_map) · blast_radius ·
map_census · map_diff · center_status · review_drift. All READ-ONLY; every list capped and the cap
named; every answer stamped; every missing block a `reason`. Registered into tools.TOOLS at import.
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
import tools as T  # noqa: E402

_WIRING: dict = {}


def load_wiring(root: str) -> tuple[dict | None, str]:
    """graft/.graph/wiring.json (10 MB on gustify) cached per (mtime, size); (None, reason) when absent."""
    p = Path(root) / "graft" / ".graph" / "wiring.json"
    if not p.is_file():
        return None, "no graft index (graft/.graph/wiring.json absent)"
    try:
        st = p.stat()
        key = (st.st_mtime_ns, st.st_size)
        hit = _WIRING.get(str(p))
        if hit and hit[0] == key:
            return hit[1], "index"
        data = json.loads(p.read_text(encoding="utf-8"))
        by_file: dict[str, list] = {}
        for n in data.get("nodes") or []:
            if isinstance(n, dict) and n.get("path") and n.get("kind") != "file":
                by_file.setdefault(n["path"], []).append(n)
        packed = {"by_file": by_file, "meta": data.get("meta") or {}, "hash": hashlib.sha256(p.read_bytes()).hexdigest()[:12]}
        _WIRING[str(p)] = (key, packed)
        return packed, "index"
    except (OSError, json.JSONDecodeError) as exc:
        return None, "unreadable graft index: %s" % exc


# ── find ───────────────────────────────────────────────────────────────────────
def _score(q: str, name: str, doc: str = "") -> int:
    n, d = (name or "").lower(), (doc or "").lower()
    if n == q: return 100
    if n.endswith("." + q) or n.endswith("::" + q) or n.split("/")[-1] == q: return 90
    if n.startswith(q): return 70
    if q in n: return 50
    if q in d: return 20
    return 0


_KIND_BONUS = {"entity": 25, "endpoint": 25, "task": 25, "model": 25, "provider": 25, "schema": 10, "function": 10}   # F4: a thing the map DECLARES outranks a generated define's prefix hit
_GEN_RX = re.compile(r"\.gen\.|/client/|/generated/")


def t_find(args: dict, roots) -> dict:
    center, root, source, reason = T._ctx(args, roots)
    if not center:
        return T._absent(root, source, reason)
    q = (args.get("query") or "").strip().lower()
    if len(q) < 2:
        raise mq.MapStop("query must be at least 2 characters")
    kinds = args.get("kind")
    kinds = {kinds} if isinstance(kinds, str) and kinds else None
    limit = max(1, min(int(args.get("limit") or 20), mq.CAP))
    stream_only = bool(args.get("stream"))
    a, c, idx = center.archmap, center.c4, center.idx()
    hits = []

    def add(kind, name, entity, file, extra=None, doc=""):
        s = _score(q, name, doc)
        if not s or (kinds is not None and kind not in kinds):
            return
        s += _KIND_BONUS.get(kind, 0)
        if file and _GEN_RX.search(file):
            s -= 30                                                    # a generated client (.gen. · /client/ · /generated/) is noise, not a definition
        hits.append((s, {"kind": kind, "name": name, "entity": entity, "file": file, **(extra or {})}))
    for slug, ent in center.entities().items():
        add("entity", slug, slug, None)
        for ep in ent.get("endpoints") or []:
            if stream_only and not ep.get("stream"):
                continue
            add("endpoint", "%s %s" % (ep.get("method"), ep.get("path")), slug, ep.get("file"), {"fn": ep.get("fn"), "stream": bool(ep.get("stream"))}, ep.get("doc") or "")
        for m in ent.get("models") or []:
            add("model", m.get("cls") or "", slug, m.get("file"), {"table": m.get("table")}, m.get("doc") or "")
        for s_ in ent.get("schemas") or []:
            add("schema", s_.get("cls") or "", slug, s_.get("file"), None, s_.get("doc") or "")
        for path, names in (ent.get("defines") or {}).items():
            for n in names:
                nm = n.rstrip("()")
                if nm not in idx["fn_by_bare"] and nm not in idx["cls"]:
                    add("define", nm, slug, path)
    for k, rec in (a.get("function_insight") or {}).items():
        add("function", k, rec.get("entity"), rec.get("file"), {"layer": rec.get("layer"), "handler": rec.get("handler")}, rec.get("doc") or "")
    for p in (c.get("fe") or {}).get("pieces") or []:
        if isinstance(p, dict):
            add("fe", p.get("name") or p.get("id") or "", p.get("home"), p.get("file"), {"piece_kind": p.get("kind")})
    for stem, (slug, node) in idx["web_by_stem"].items():
        add("screen", stem, slug, None)
    for name, rec in idx["task_by_name"].items():                       # F3: a task by its REGISTERED name or its fn name
        r_ = rec["root"]
        add("task", name, rec["slug"], r_.get("file"), {"fn": r_.get("fn"), "id": rec["nid"]}, r_.get("doc") or "")
        if r_.get("fn") and r_.get("fn") != name and _score(q, r_.get("fn")) > _score(q, name):
            add("task", r_.get("fn"), rec["slug"], r_.get("file"), {"registered_as": name, "id": rec["nid"]}, r_.get("doc") or "")
    provs: dict[str, dict] = {}
    for (slug, nid), n in idx["c4_nodes"].items():                      # F4: providers — every c4 provider node, once per name
        if n.get("kind") == "provider":
            pv = provs.setdefault(n.get("label") or nid.split(":", 1)[-1], {"slugs": set(), "pclass": n.get("pclass")})
            pv["slugs"].add(slug)
    for name, pv in provs.items():
        add("provider", name, ", ".join(sorted(s_ for s_ in pv["slugs"] if s_)), None, {"pclass": pv["pclass"], "id": "provider:%s" % name})
    # dedupe: a define twin of an fe piece (same name + file) folds into the fe hit; a schema/model several entities share (same cls + file) is ONE hit
    fe_keys = {(h["name"], h["file"]) for _, h in hits if h["kind"] == "fe"}
    hits = [(s_, h) for s_, h in hits if not (h["kind"] == "define" and (h["name"], h["file"]) in fe_keys)]
    merged, seen_sm = [], {}
    for s_, h in hits:
        if h["kind"] in ("schema", "model"):
            k = (h["kind"], h["name"], h["file"])
            if k in seen_sm:
                seen_sm[k].setdefault("entities", [seen_sm[k]["entity"]]).append(h["entity"])
                continue
            seen_sm[k] = h
        merged.append((s_, h))
    hits = merged
    for _s, h in hits:
        if h.get("entities"):
            h["entities"] = sorted({e for e in h["entities"] if e})   # a claim about ownership: one name per entity, sorted
    hits.sort(key=lambda h: (-h[0], h[1]["kind"], h[1]["name"]))
    out = T._base(center, root, source)
    out.update({"query": q, "hits": [h[1] for h in hits[:limit]], "total": len(hits),
                "note": ("+%d more (limit %d)" % (len(hits) - limit, limit)) if len(hits) > limit else None,
                "ranking": "exact 100 · qualified-tail 90 · prefix 70 · substring 50 · in-doc 20 · +25 entity/endpoint/task/model/provider · +10 schema/function "
                           "· −30 generated client (.gen. · /client/ · /generated/) · a define twin folds into its fe piece · a shared schema/model is one hit (entities: [...])",
                "floor": "searches the map's names and docs, not the source — a name the map lacks is a Grep question"})
    if stream_only:
        out["filter"] = "stream=true — only endpoints whose handler returns a streaming response (SSE / chunked)"
    if kinds and "task" in kinds and not idx["task_by_name"]:
        out["note"] = out["note"] or "no task_roots block on this map — no worker tasks found, or an older map (regen to know)"
    if kinds and "provider" in kinds and not provs:
        out["note"] = out["note"] or "no provider nodes in c4 — no SDK root reached, or an older map (regen to know)"
    return out


# ── outline ────────────────────────────────────────────────────────────────────
def t_outline(args: dict, roots) -> dict:
    center, root, source, reason = T._ctx(args, roots)
    if not center:
        return T._absent(root, source, reason)
    path = (args.get("file") or "").strip().lstrip("./")
    if not path:
        raise mq.MapStop("file is required (repo-relative path)")
    a, idx = center.archmap, center.idx()
    fi = a.get("function_insight") or {}
    wiring, wstat = load_wiring(root)
    out = T._base(center, root, source)
    out.update({"file": path, "exists": os.path.isfile(os.path.join(root, path)),
                "owners": [{"entity": s, "layer": l, "lines": n} for s, l, n in idx["file_owners"].get(path, [])]})
    defs = []
    if wiring and path in wiring["by_file"]:
        for n in sorted(wiring["by_file"][path], key=lambda x: int((x.get("span") or "L0").split("-")[0].lstrip("L") or 0)):
            nid = n.get("id") or ""
            qual = nid.split("#", 1)[1] if "#" in nid else n.get("name")   # W2-1: qualified (Class.method), never the bare name
            rec = fi.get("%s::%s" % (path, qual)) or fi.get("%s::%s" % (path, n.get("name"))) or {}
            defs.append({"span": n.get("span"), "kind": n.get("kind"), "name": qual, "signature": (n.get("signature") or "")[:200],
                         "exported": n.get("exported"), "returns": rec.get("returns"), "async": rec.get("async"),
                         "access_ops": (rec.get("access") or {}).get("ops"), "doc": (rec.get("doc") or "")[:120] or None})
        out["signatures"] = "graft index (%s)" % wiring["hash"]
    else:
        for k in idx["fn_by_file"].get(path, []):
            rec = fi[k]
            defs.append({"span": None, "kind": "method" if "." in k.split("::", 1)[1] else "function", "name": k.split("::", 1)[1],
                         "signature": None, "returns": rec.get("returns"), "async": rec.get("async"),
                         "access_ops": (rec.get("access") or {}).get("ops"), "doc": (rec.get("doc") or "")[:120] or None})
        out["signatures"] = "unavailable — %s; names/returns from function_insight" % wstat
    lst, note = mq.cap_list(defs)
    mi = a.get("model_insight") or {}
    ti = a.get("test_insight") or {}
    out.update({"definitions": lst, "definitions_note": note,
                "models_defined": [cls for cls, r in mi.items() if r.get("file") == path][:mq.CAP],
                "models_referenced": sorted({cls for cls, r in mi.items() for ref in (r.get("internal_refs") or []) if ref.get("file") == path})[:mq.CAP],
                "tests_reaching": ((ti.get("by_file") or {}).get(path) or {}).get("reach", [])[:mq.CAP],
                "census": T._census_entry(a, path)})
    return out


# ── center_overview ────────────────────────────────────────────────────────────
def t_center_overview(args: dict, roots) -> dict:
    center, root, source, reason = T._ctx(args, roots)
    if not center:
        return T._absent(root, source, reason)
    a, c = center.archmap, center.c4
    ad = {s.get("entity"): s for s in (center.adoption.get("sections") or [])}
    cov = a.get("coverage") or {}
    rows = []
    for slug, ent in sorted(center.entities().items()):
        s = ad.get(slug) or {}
        cv = cov.get(slug) or {}
        fe_home = next((h for h in ((c.get("fe") or {}).get("homes") or []) if isinstance(h, dict) and h.get("id") == "fe·%s" % slug), {})
        rows.append({"entity": slug, "rank": s.get("rank"), "status": s.get("status"),
                     "endpoints": len(ent.get("endpoints") or []), "models": len(ent.get("models") or []),
                     "schemas": len(ent.get("schemas") or []), "files": len(ent.get("files") or []),
                     "coverage": ("%s/%s" % (cv.get("covered"), cv.get("total"))) if cv else None,
                     "fe_pieces": fe_home.get("pieces")})
    st = c.get("stats") or {}
    web = st.get("web") or {}
    cfg_only = T._config_only(center)
    if cfg_only:
        for r in rows:
            r["status"] = "config-only"

    def gap(block, key="unclaimed"):                                   # F7: absent block → None (not emitted), never 0
        b = a.get(block)
        return len(b.get(key) or []) if isinstance(b, dict) and b else None
    out = T._base(center, root, source)
    out.update({"entities": rows,
                "arms": {"graft": (st.get("graft") or {}).get("present"), "web": web.get("present"), "web_extractor": web.get("extractor"),
                         "fe": {"present": bool((c.get("fe") or {}).get("pieces")), "homing": (st.get("fe") or {}).get("homing")},
                         "providers": sorted(((st.get("providers") or {}).get("by_provider") or {}).keys()),
                         "app_middleware": len(a.get("app_middleware") or []), "gate_endpoints": st.get("gate_endpoints"),
                         "tasks": len(a.get("task_roots") or [])},
                "census_gaps": {"files_unclaimed": gap("file_census"), "models_unclaimed": gap("model_census"), "routes_unclaimed": gap("route_census"),
                                "schemas_unwired": gap("schema_homing", "unwired"), "schemas_ambiguous": gap("schema_homing", "ambiguous")},
                "census_absent": [k for k in ("file_census", "model_census", "route_census", "schema_homing") if not (isinstance(a.get(k), dict) and a.get(k))],
                "census_note": "None = the census block is absent on this map (not emitted), never 0",
                "web": (({k: web.get(k) for k in ("extractor", "screens", "fetch_sites", "matched", "dynamic", "unhomed", "other_roots", "sse", "sdk_methods") if web.get(k) is not None}
                         | {"present": True, "unmatched": (len(web["unmatched"]) if isinstance(web.get("unmatched"), list) else (web.get("unmatched") or 0))})
                        if web.get("present") else {"present": False, "reason": web.get("reason")}),
                "map_health": mq.map_health(a, c),
                "stations": "codebase-graph.html · gabe-universe.html · architecture.html · board.html (docs/site/center/)"})
    if cfg_only:
        out["registry"] = T.CONFIG_ONLY                                # no adoption.json: nothing is "unregistered" — the config IS the registry
    else:
        out["unregistered"] = sorted(set(center.entities()) - set(ad))
    return out


# ── blast_radius ───────────────────────────────────────────────────────────────
def _changed_files(root: str) -> tuple[list[str], str]:
    files: set[str] = set()
    rc, out, _ = mq.sh(["git", "-C", root, "diff", "--name-only", "HEAD"])
    if rc != 0:
        return [], "git diff unavailable"
    files.update(l.strip() for l in out.splitlines() if l.strip())
    rc, st, _ = mq.sh(["git", "-C", root, "status", "--porcelain", "--untracked-files=all"])
    if rc == 0:
        files.update(l[3:].strip() for l in st.splitlines() if l.startswith("??"))
    return sorted(f for f in files if f.endswith(mq.SRC_EXT) and not mq.noise(f)), "worktree vs HEAD (+ untracked)"


def t_blast_radius(args: dict, roots) -> dict:
    center, root, source, reason = T._ctx(args, roots)
    if not center:
        return T._absent(root, source, reason)
    files = args.get("files")
    if isinstance(files, str):
        files = [files]
    if files:
        files, src = [f.strip().lstrip("./") for f in files if str(f).strip()], "argument"
    else:
        files, src = _changed_files(root)
    a, idx = center.archmap, center.idx()
    fi = a.get("function_insight") or {}
    ti = a.get("test_insight") or {}
    mi = a.get("model_insight") or {}
    touched: dict[str, int] = {}
    unowned, fns, models, endpoints, tests, fe = [], [], set(), {}, set(), []
    for f in files:
        owners = idx["file_owners"].get(f, [])
        if not owners:
            unowned.append(f)
        for s, _, _ in owners:
            touched[s] = touched.get(s, 0) + 1
        fns += idx["fn_by_file"].get(f, [])
        models.update(cls for cls, r in mi.items() if r.get("file") == f)
        tests.update(((ti.get("by_file") or {}).get(f) or {}).get("reach", []))
        fe += [p.get("name") for p in ((center.c4.get("fe") or {}).get("pieces") or []) if isinstance(p, dict) and p.get("file") == f]
    quals = {k.split("::", 1)[1] for k in fns}                          # F2: the QUALIFIED name (a plain function's qual is its bare name)
    for (slug, nid), n in idx["c4_nodes"].items():
        if n.get("kind") != "endpoint":
            continue
        hkey = None
        for ep_key, (s, m, p) in idx["handler_of"].items():
            if ep_key.split("::", 1)[0] in files and nid == "endpoint:%s %s" % (m, p):
                hkey = ep_key
        names = set((n.get("behind") or {}).get("names") or [])
        if hkey or (names & quals):
            endpoints[nid] = {"entity": slug, "via": "handler in changed file" if hkey else "behind.names (floor, cap 12)"}
    # F15 (2026-09-06): the dispatch arm — task roots DEFINED in the changed files are entry points; tasks DISPATCHED from the changed
    # functions ride levels.json's dispatches edges (conf per edge); either makes the reading cross-process
    tasks_defined = [rec["nid"] for name, rec in idx["task_by_name"].items() if rec["root"].get("file") in files]
    fx = center.fn_index()
    if fx["present"]:
        fk2t = {r["fnkey"]: r["nid"] for r in idx["task_by_name"].values() if r.get("fnkey")}
        tasks_dispatched = []
        for k in fns:
            fk = k.replace("::", "#", 1)
            for t_, rel, cf in fx["fn_out"].get(fk, []):
                if rel == "dispatches":
                    tasks_dispatched.append({"task": fk2t.get(t_, t_), "from": fk, "conf": cf})
        tasks_dispatched = tasks_dispatched[:mq.CAP]
    else:
        tasks_dispatched = {"reason": "no levels.json — dispatch edges unread"}
    fk_neighbors = set()
    for cls in models:
        for row in T._model_touches(center, cls, "model", {}).get("fk_in_models") or []:
            if row.get("entity"):
                fk_neighbors.add(row["entity"])
    n_ent = len(touched)
    reading = "contained" if n_ent <= 1 and not (fk_neighbors - set(touched)) else ("local" if n_ent <= 1 else "cross-cutting")
    if unowned and not touched:
        reading = "unmapped"
    if (isinstance(tasks_dispatched, list) and tasks_dispatched) or tasks_defined:
        reading = "cross-process"                                      # a task may run hours later on another worker — the honest word
    out = T._base(center, root, source)
    out.update({"files": files[:mq.CAP], "files_source": src, "files_more": max(0, len(files) - mq.CAP),
                "touched_entities": touched, "unowned_files": unowned[:mq.CAP],
                "functions": sorted(fns)[:mq.CAP], "models_defined": sorted(models)[:mq.CAP],
                "fk_neighbor_entities": sorted(fk_neighbors - set(touched)),
                "endpoints_reached": dict(list(endpoints.items())[:mq.CAP]),
                "tasks_defined": tasks_defined[:mq.CAP], "tasks_dispatched": tasks_dispatched,
                "tests_reaching": sorted(tests)[:mq.CAP], "fe_pieces": fe[:mq.CAP],
                "reading": reading,
                "floor": "map joins only (owners · handler files · behind.names capped 12, joined on the qualified name · by_file.reach · levels.json dispatches with conf per edge); "
                         "the sim's FK blast is exact, everything else is a floor — run who_calls on the changed symbols before trusting 'contained'"})
    return out


# ── map_census ─────────────────────────────────────────────────────────────────
def t_map_census(args: dict, roots) -> dict:
    center, root, source, reason = T._ctx(args, roots)
    if not center:
        return T._absent(root, source, reason)
    a, c = center.archmap, center.c4
    want = (args.get("kind") or "").strip()
    out = T._base(center, root, source)
    def block(name):
        b = a.get(name)
        if not b:
            return {"reason": "no %s block in this archmap (version %s)" % (name, a.get("version"))}
        uncl, note = mq.cap_list(b.get("unclaimed") or [])
        return {"claimed": b.get("claimed"), "scanned_dirs": b.get("scanned_dirs"), "unclaimed": uncl, "unclaimed_note": note}
    sh_ = a.get("schema_homing") or {}
    h = mq.map_health(a, c)
    rm, rm_s = mq.health_key(a, "route_mounts")
    up, up_s = mq.health_key(a, "unparseable")
    fs, fs_s = mq.health_key(a, "fn_similarity")
    tk = a.get("tasks") or {}
    web = (c.get("stats") or {}).get("web") or {}
    schema = ({"unwired": mq.cap_list(sh_.get("unwired") or [])[0], "ambiguous": mq.cap_list(sh_.get("ambiguous") or [])[0],
               "moved": len(sh_.get("moved") or []), "fn_wires": len(sh_.get("fn_wires") or [])} if sh_ else {"reason": "no schema_homing block"})
    schema["empty_arm"] = h["schemas_zero"]                            # 0 schemas across N endpoints = the arm produced NOTHING, not a clean estate
    unm = web.get("unmatched") if isinstance(web.get("unmatched"), list) else []
    sections = {"file": block("file_census"), "model": block("model_census"), "route": block("route_census"), "schema": schema,
                # the four sections the repo-study pass added (2026-09-06) — each with its P2 state word
                "unparseable": ({"state": up_s, "count": len(up), "rows": [{"file": r[0], "why": r[1]} for r in up if isinstance(r, (list, tuple)) and len(r) > 1][:mq.CAP],
                                 "text": "every mapped .py the AST scanners skipped — whatever those files define is missing from the map"} if up else {"state": up_s}),
                "mounts": ({"state": rm_s, "mounted": rm.get("mounted"), "routers": rm.get("routers"), "scanned": rm.get("scanned"),
                            "unresolved": [{"file": u.get("file"), "line": u.get("line"), "why": u.get("why")} for u in (rm.get("unresolved") or []) if isinstance(u, dict)][:mq.CAP],
                            "text": "an unresolved include_router() prefix = routes whose URL the map could not compute (labels may be missing their mount)"} if rm else {"state": rm_s})
                          | {"tasks_unresolved_kinds": list(((tk.get("stats") or {}).get("unresolved") or [])),
                             "tasks_note": "dispatch sites whose task name is computed (f-string / variable) — those tasks are NOT on task_roots"},
                "twins": ({"state": fs_s, "mode": fs.get("mode"), "sizable": fs.get("sizable"), "budget": fs.get("budget"), "pairs": fs.get("pairs"),
                           "text": "a pass that did not run exactly: %s sizable function(s) over the %s budget — twins were looked for only among functions sharing a rare identifier (%s candidate pairs); an approximation"
                                   % (fs.get("sizable"), fs.get("budget"), fs.get("pairs"))} if fs else
                          {"state": fs_s, "text": "the structural-twin pass ran exactly" if fs_s == "clean" else "regen to know — an older map never recorded the twin pass"}),
                "web": ({"extractor": web.get("extractor"), "other_roots": list(web.get("other_roots") or []),
                         "other_roots_note": "second frontends the ONE-root rule never scanned — nothing from them is on the map",
                         "unhomed": web.get("unhomed") or 0, "unmatched": len(unm) if unm or isinstance(web.get("unmatched"), list) else (web.get("unmatched") or 0),
                         "unmatched_named": ["%s %s" % (u.get("m") or u.get("method"), u.get("p") or u.get("path")) for u in unm if isinstance(u, dict)][:12],
                         "unmatched_note": ("first 12 of %d named" % len(unm)) if len(unm) > 12 else None}
                        if web.get("present") else {"present": False, "reason": web.get("reason") or "no web arm on this map"})}
    if want:
        if want not in sections:
            raise mq.MapStop("kind must be one of file | model | route | schema | unparseable | mounts | twins | web")
        out["census"] = {want: sections[want]}
    else:
        out["census"] = sections
    out["note"] = ("unclaimed = the map is BLIND there (pulse S11/S13 nag these); 'full coverage' holds only for archmap version ≥ 2 · "
                   "absent block = not emitted (older map) unless the study-pass sentinel route_mounts is present → clean")
    out["states"] = mq.HEALTH_STATES
    return out


# ── map_diff ───────────────────────────────────────────────────────────────────
def _map_at(root: str, ref: str | None):
    rel = mq.CENTER_REL + "/archmap.json"
    if ref in (None, "", "WORKTREE"):
        p = Path(root) / rel
        return (json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None), "worktree"
    rc, out, err = mq.sh(["git", "-C", root, "show", "--end-of-options", "%s:%s" % (ref, rel)])
    if rc != 0:
        return None, "git show failed: %s" % err.strip()[:120]
    try:
        return json.loads(out), ref
    except json.JSONDecodeError:
        return None, "unparseable archmap at %s" % ref


def _ent_sets(m: dict) -> dict:
    out = {}
    for slug, ent in (m.get("entities") or {}).items():
        out[slug] = {"endpoints": {"%s %s" % (e.get("method"), e.get("path")) for e in ent.get("endpoints") or []},
                     "models": {x.get("cls") for x in ent.get("models") or []},
                     "schemas": {x.get("cls") for x in ent.get("schemas") or []},
                     "files": {r[1] for r in ent.get("files") or [] if len(r) > 1}}
    return out


def _task_set(m: dict) -> set:
    return {r.get("path") for r in (m.get("task_roots") or []) if isinstance(r, dict) and r.get("path")}


def _health_n(m: dict, key: str) -> int | None:
    v, state = mq.health_key(m, key)
    if state == "not_emitted":
        return None
    if key == "route_mounts":
        return len((v or {}).get("unresolved") or [])
    return len(v or [])


def t_map_diff(args: dict, roots) -> dict:
    center, root, source, reason = T._ctx(args, roots)
    if not center:
        return T._absent(root, source, reason)
    base = (args.get("base") or "").strip()
    if not base:
        raise mq.MapStop("base is required (a sha, branch or tag whose committed archmap to compare against)")
    head = (args.get("head") or "").strip() or None
    A, a_src = _map_at(root, base)
    B, b_src = _map_at(root, head)
    out = T._base(center, root, source)
    if A is None or B is None:
        out["reason"] = "%s · %s" % (a_src, b_src)
        return out
    if A.get("head") == B.get("head"):
        out.update({"base": a_src, "head": b_src, "regenerated": False, "note": "both maps carry head %s — the map was not regenerated between these refs" % A.get("head")})
        return out
    ea, eb = _ent_sets(A), _ent_sets(B)
    per = {}
    for slug in sorted(set(ea) | set(eb)):
        if slug not in ea:
            per[slug] = {"entity": "added"}; continue
        if slug not in eb:
            per[slug] = {"entity": "removed"}; continue
        d = {}
        for k in ("endpoints", "models", "schemas", "files"):
            add, rem = sorted(eb[slug][k] - ea[slug][k]), sorted(ea[slug][k] - eb[slug][k])
            if add or rem:
                d[k] = {"added": add[:20], "removed": rem[:20], "more": max(0, len(add) + len(rem) - 40)}
        if d:
            per[slug] = d
    def cnt(m, k): return len((m.get(k) or {}).get("unclaimed") or []) if m.get(k) else None
    ta, tb = _task_set(A), _task_set(B)
    out.update({"base": a_src, "head": b_src, "regenerated": True, "map_heads": {"base": A.get("head"), "head": B.get("head")},
                "entities": per or {"note": "no entity-level change"},
                "tasks": {"added": sorted(tb - ta)[:20], "removed": sorted(ta - tb)[:20], "base": len(ta), "head": len(tb)},   # F14: task roots are a first-class delta
                "census_delta": {k: {"base": cnt(A, k), "head": cnt(B, k)} for k in ("file_census", "model_census", "route_census")},
                "health_delta": {"mounts_unresolved": [_health_n(A, "route_mounts"), _health_n(B, "route_mounts")],
                                 "unparseable": [_health_n(A, "unparseable"), _health_n(B, "unparseable")],
                                 "note": "[base, head]; None = not emitted on that map"},
                "functions": {"base": len(A.get("function_insight") or {}), "head": len(B.get("function_insight") or {})}})
    return out


# ── the generator resolver (WS-2, ruled 2026-09-02) ────────────────────────────
# A user-scope server auto-loads on EVERY project the operator opens, so running
# `<target repo>/scripts/<gen>.py` would execute arbitrary target-repo code. These two
# generators are suite-installed by /gabe-cc-init, so the suite's OWN copy is the one we
# run — with `-I` (isolated: no PYTHONPATH, no user site-packages, no cwd on sys.path),
# so nothing in the target tree can shadow an import. Measured 2026-09-02: the suite copy
# and both twins' copies of center_status.py, check_workflow_drift.py and the two siblings
# center_status.py imports (_center_data.py, _a3_evidence.py) are BYTE-IDENTICAL.
# BUT identical bytes are not identical behavior: `_center_data.REPO_ROOT` defaults to the
# generator's OWN parent tree, so running the suite's copy would read the SUITE's center
# unless the target root is passed explicitly. GABE_REPO_ROOT (the same lever the twin
# read-only regen recipe uses) is therefore REQUIRED here, not optional — without it the
# tool answers "not a center project" on a project that has one. `-I` implies `-E`, which
# strips PYTHON* only, so GABE_REPO_ROOT survives it.
# The target copy is never a fallback — if the suite has no copy the subject reports the
# absence, because "run the repo's version instead" is the thing this exists to prevent.
_GEN_DIRS = ("templates/gabe/center/generators",  # installed layout (~/.claude)
             "templates/center/generators")        # repo layout (suite checkout)


def suite_generator(name: str) -> Path | None:
    """The suite's own copy of a center generator, or None. Never the target repo's."""
    base = Path(__file__).resolve().parents[3]
    for rel in _GEN_DIRS:
        cand = base / rel / name
        if cand.is_file():
            return cand
    return None


# ── center_status ──────────────────────────────────────────────────────────────
def t_center_status(args: dict, roots) -> dict:
    center, root, source, reason = T._ctx(args, roots)
    if not center:
        return T._absent(root, source, reason)
    out = T._base(center, root, source)
    script = suite_generator("center_status.py")
    if script is None:
        out["status"] = {"reason": "the suite's own center_status.py is not installed beside this server; "
                                   "the target repo's copy is deliberately NOT run (WS-2)"}
        return out
    if not (center.dir / "center.config.json").is_file():
        out["status"] = {"reason": "no docs/site/center/center.config.json in this project (built by /gabe-cc-init)"}
        return out
    rc, text, err = mq.sh([sys.executable, "-I", str(script), root], cwd=root, timeout=60,
                          env={"GABE_REPO_ROOT": root})
    out["status"] = {"ran": rc == 0, "exit": rc, "text": text[:6000], "truncated": len(text) > 6000, "stderr": err.strip()[:300] or None}
    out["not_run"] = ["next_feature.py (backfill queue) and risk_sweep.py (P0–P3 ladder) are /gabe-cc-update's — heavier; not run here"]
    return out


# ── review_drift ───────────────────────────────────────────────────────────────
_REACH_RE = re.compile(r"- \*\*Reach:\*\* (.+?) \((graft|grep-only)@([0-9a-f]+)\)")
_DIFF_FILE_RX = re.compile(r"^diff --git a/(.+?) b/")


def _strip_center_hunks(diff: str) -> str:
    """F12 (2026-09-06): hunks under docs/site/center/ or a generators/ dir are the suite's own install — its template prose
    carries fetch('/x') literals that are not this project's fetches (both study repos showed the phantom). The comment/docstring
    guard proper belongs to gabe-pulse's fetch_bridge.py (backlog)."""
    keep = []
    for part in re.split(r"(?m)^(?=diff --git )", diff):
        m = _DIFF_FILE_RX.match(part)
        f = m.group(1) if m else ""
        if f.startswith("docs/site/center/") or "/generators/" in f or f.startswith("generators/"):
            continue
        keep.append(part)
    return "".join(keep)


def _phase_reach(root: str, phase_id: str | None) -> tuple[list[str], str | None, str | None]:
    plan = Path(root) / ".kdbp" / "PLAN.md"
    if not plan.is_file():
        return [], None, "no .kdbp/PLAN.md"
    text = plan.read_text(encoding="utf-8", errors="replace")
    if phase_id:
        m = re.search(r"### Phase %s\b.*?(?=\n### Phase |\n## |\Z)" % re.escape(phase_id), text, re.S)
        text = m.group(0) if m else ""
    if re.search(r"- \*\*Reach:\*\* no index\b", text):
        return [], None, "Reach: record reads `no index`%s — red ran with no graft index (REACH DRIFT NOT RUN — no graft index)" % (" for phase %s" % phase_id if phase_id else "")
    m = _REACH_RE.search(text)
    if not m:
        return [], None, "no Reach: record%s" % (" for phase %s" % phase_id if phase_id else "")
    files = [f.strip() for f in m.group(1).split("·") if f.strip() and f.strip() != "—"]
    return files, m.group(3), None


def t_review_drift(args: dict, roots) -> dict:
    center, root, source, reason = T._ctx(args, roots)
    if not center:
        return T._absent(root, source, reason)
    base = (args.get("base") or "").strip()
    if not base:
        raise mq.MapStop("base is required (the ref the phase's diff is measured against)")
    want = args.get("subjects")
    want = set(want) if isinstance(want, list) else None
    phase = (args.get("phase") or "").strip()
    if not phase:                                    # W2-2: default to PLAN.json current_phase for ALL subjects, not just entity
        pj = Path(root) / ".kdbp" / "PLAN.json"
        if pj.is_file():
            try:
                phase = (json.loads(pj.read_text(encoding="utf-8")).get("current_phase") or "").strip()
            except json.JSONDecodeError:
                phase = ""
    rc, diff, err = mq.sh(["git", "-C", root, "diff", "--end-of-options", base], timeout=60)
    if rc != 0:
        raise mq.MapStop("git diff %s failed: %s" % (base, err.strip()[:120]))
    rc, names, _ = mq.sh(["git", "-C", root, "diff", "--name-only", "--end-of-options", base])
    changed = sorted(l.strip() for l in names.splitlines() if l.strip()) if rc == 0 else []
    changed_src = [f for f in changed if f.endswith(mq.SRC_EXT) and not mq.noise(f)]
    out = T._base(center, root, source)
    out.update({"base": base, "changed_files": len(changed), "changed_source": changed_src[:mq.CAP], "subjects": {}})
    subj = out["subjects"]

    def run(name):
        return want is None or name in want
    if run("entity_shape"):
        try:
            es = mq.pulse_module("entity_shape")
            eps, umap = es.load_project(Path(center.root))
            shape = es.entity_shape(eps, umap)
            new_routes = es.diff_new_routes(diff)
            cls = es.classify_new_routes(new_routes, shape.get("owned") or {}, shape.get("orphans") or [], umap) if new_routes else {}
            subj["entity_shape"] = {"ran": True, "new_routes": new_routes[:mq.CAP], "classified": cls, "standing": es.one_line(shape) or "clean"}
        except Exception as exc:
            subj["entity_shape"] = {"ran": False, "reason": "%s: %s" % (type(exc).__name__, exc)}
    if run("web_bridge"):
        try:
            fb = mq.pulse_module("fetch_bridge")
            keys = fb.load_endpoint_keys(Path(center.root))
            new_f = fb.diff_new_fetches(_strip_center_hunks(diff))
            present, unmatched, why = fb.load_unmatched(Path(center.root))
            cls = fb.classify_new_fetches(new_f, keys) if new_f else {}
            subj["web_bridge"] = {"ran": True, "new_fetches": new_f[:mq.CAP], "classified": cls, "standing_unmatched": len(unmatched), "web_arm": present or why}
        except Exception as exc:
            subj["web_bridge"] = {"ran": False, "reason": "%s: %s" % (type(exc).__name__, exc)}
    if run("reach"):
        reach, sha, why = _phase_reach(root, phase or None)
        if why:
            subj["reach"] = {"ran": False, "reason": why}
        else:
            rs = set(reach)
            subj["reach"] = {"ran": True, "record": reach[:mq.CAP], "graft_at": sha,
                             "unreached": [f for f in changed_src if f not in rs][:mq.CAP],
                             "unused_reach": [f for f in reach if f not in set(changed)][:mq.CAP],
                             "note": "unreached = the graph missed an edge OR the change grew past its cases; compare the diff's distance from graft@%s" % sha}
    if run("entity"):
        declared = None
        pj = Path(root) / ".kdbp" / "PLAN.json"
        if pj.is_file():
            try:
                plan = json.loads(pj.read_text(encoding="utf-8"))
                ph = next((p for p in plan.get("phases") or [] if p.get("id") == phase), None)
                declared = (ph or {}).get("entities")
            except json.JSONDecodeError:
                declared = None
        idx = center.idx()
        touched = sorted({s for f in changed_src for s, _, _ in idx["file_owners"].get(f, [])})
        if declared is None:
            subj["entity"] = {"ran": False, "reason": "no PLAN.json phase with an entities list", "touched": touched}
        else:
            subj["entity"] = {"ran": True, "declared": declared, "touched": touched,
                              "undeclared_touched": sorted(set(touched) - set(declared)), "declared_untouched": sorted(set(declared) - set(touched))}
    if run("workflow_census"):
        censuses = sorted((center.dir / "workflows").glob("*.json")) if (center.dir / "workflows").is_dir() else []
        if not censuses:
            subj["workflow_census"] = {"ran": False, "reason": "no docs/site/center/workflows/*.json census on this project"}
        else:
            script = suite_generator("check_workflow_drift.py")
            if script is None:
                subj["workflow_census"] = {"ran": False, "reason": "census present but the suite's own "
                                           "check_workflow_drift.py is not installed beside this server; "
                                           "the target repo's copy is deliberately NOT run (WS-2)"}
            else:
                res = []
                archmap = center.dir / "archmap.json"
                for cpath in censuses[:10]:
                    cmd = [sys.executable, "-I", str(script), str(cpath), "--center", str(center.dir), "--json"]
                    if archmap.is_file():
                        cmd += ["--archmap", str(archmap)]
                    rc, o, e = mq.sh(cmd, cwd=root, timeout=90, env={"GABE_REPO_ROOT": root})
                    try:
                        res.append({"census": cpath.name, "exit": rc, "result": json.loads(o) if o.strip() else None})
                    except json.JSONDecodeError:
                        res.append({"census": cpath.name, "exit": rc, "text": o[:800]})
                subj["workflow_census"] = {"ran": True, "results": res,
                                           "not_run": ["claim-drift (junit half): no --junit passed — the results_out globs live in .kdbp/BEHAVIOR.md ## Verify Commands; hand form"]
                                                      + ([] if archmap.is_file() else ["census-lag: no docs/site/center/archmap.json to pass as --archmap"])}
    out["not_run"] = [k for k, v in subj.items() if not v.get("ran")]
    out["note"] = "STALE ANCHOR (PENDING rows' cited files moved past their Verified sha) lives in gabe-kdbp; pricing stays judgment (review D6)"
    return out


# ── registry (appended into tools.TOOLS by tools.py) ──────────────────────────
RO = T.RO
TOOLS = [
    {"name": "find", "fn": t_find, "annotations": RO,
     "description": "Find X by name/doc: entities, endpoints (stream filter), tasks (TASK <name>), models, schemas (deduped), functions, providers, screens, FE pieces; generated clients de-ranked (graft_find_code).",
     "inputSchema": T._schema({"query": {"type": "string", "description": "A name or fragment (≥ 2 chars)."},
                               "kind": {"type": "string", "enum": ["entity", "endpoint", "task", "model", "schema", "function", "define", "fe", "screen", "provider"], "description": "Restrict to one kind."},
                               "stream": {"type": "boolean", "description": "true → only endpoints whose handler returns a streaming response."},
                               "limit": {"type": "integer", "description": "Max hits (default 20, cap 40)."}, **T.ROOT_PROP}, ["query"])},
    {"name": "outline", "fn": t_outline, "annotations": RO,
     "description": "A file's outline without reading it: definitions with span, kind, signature (graft index), returns, r/w access; owner entity, models defined/referenced, tests reaching. graft_file_api's equivalent.",
     "inputSchema": T._schema({"file": {"type": "string", "description": "Repo-relative file path."}, **T.ROOT_PROP}, ["file"])},
    {"name": "center_overview", "fn": t_center_overview, "annotations": RO,
     "description": "Orientation by entity: rank, status, counts, coverage, FE pieces; arms (graft · web extractor · fe homing · providers · app middleware); census gaps (absent ≠ 0); registry mode; map_health.",
     "inputSchema": T._schema({**T.ROOT_PROP})},
    {"name": "blast_radius", "fn": t_blast_radius, "annotations": RO,
     "description": "What a change touches: worktree diff (or given files) → entities, functions, models, endpoints reached, tasks dispatched (levels.json, conf per edge), tests, FE pieces, a reading (a FLOOR).",
     "inputSchema": T._schema({"files": {"type": "array", "items": {"type": "string"}, "description": "Changed files; default = worktree vs HEAD + untracked."}, **T.ROOT_PROP})},
    {"name": "map_census", "fn": t_map_census, "annotations": RO,
     "description": "Where the map is blind: unclaimed files/models/routes, unwired schemas, unparseable files, unresolved route mounts, the blocked twin pass, unscanned frontend roots + unhomed fetches.",
     "inputSchema": T._schema({"kind": {"type": "string", "enum": ["file", "model", "route", "schema", "unparseable", "mounts", "twins", "web"], "description": "One section only."}, **T.ROOT_PROP})},
    {"name": "map_diff", "fn": t_map_diff, "annotations": RO,
     "description": "How the committed map changed between two refs: per entity, endpoints/models/schemas/files added or removed; task roots; census, health and function deltas; says so when not regenerated.",
     "inputSchema": T._schema({"base": {"type": "string", "description": "A sha/branch/tag."}, "head": {"type": "string", "description": "Default: the worktree's archmap."}, **T.ROOT_PROP}, ["base"])},
    {"name": "center_status", "fn": t_center_status, "annotations": RO,
     "description": "The command center's actionable list (scripts/center_status.py, relayed verbatim with its links and → next steps); never triggers a regen.",
     "inputSchema": T._schema({**T.ROOT_PROP})},
    {"name": "review_drift", "fn": t_review_drift, "annotations": RO,
     "description": "A review's deterministic drift subjects in one call vs a base ref: entity_shape, web_bridge, reach (vs the Reach record), entity (declared vs touched), workflow_census; NOT RUN is first-class.",
     "inputSchema": T._schema({"base": {"type": "string", "description": "The diff base (sha/branch)."}, "phase": {"type": "string", "description": "Phase id (default: PLAN.json current_phase)."},
                               "subjects": {"type": "array", "items": {"type": "string", "enum": ["entity_shape", "web_bridge", "reach", "entity", "workflow_census"]}}, **T.ROOT_PROP}, ["base"])},
]
