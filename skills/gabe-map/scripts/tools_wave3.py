#!/usr/bin/env python3
"""tools_wave3 — the repo-study tool pass (2026-09-06; plan: docs/design/repo-study/legend-and-tools-plan.md Part B, D1/D2).

trace · the ORDERED path from an endpoint, a TASK root or a function to the models and providers it reaches, one hop per
        line with its confidence — read from levels.json `fn_edges` (P0), never from graft (whose `direction=out` returned
        nothing on tier0). The station's journeys are curated screen→endpoint walks; the fn-level order lives only here.
gates · the INVERSE of an endpoint's middleware: which endpoints a gate guards — by callee, by fn key, or by its argument
        string (Permission.MANAGE_LLMS) — plus the ASGI middleware that applies to every request.

Both READ-ONLY: no subprocess, no git, no emit path; every cap named; every answer stamped; honest-empty by name.
Registered into tools.TOOLS at import (after wave 2).
"""
from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mapquery as mq  # noqa: E402
import tools as T  # noqa: E402

_DEF_RELS = ("calls", "dispatches", "depends", "reaches")
_HOP_CAP = 120


# ── trace ──────────────────────────────────────────────────────────────────────
def _models_of(fi: dict, fk: str) -> list[str]:
    """The models a function reads/writes, from function_insight.access.ops — 'Model r/w' per model."""
    rec = fi.get(fk.replace("#", "::", 1)) or {}
    seen: dict[str, set] = {}
    for op in (rec.get("access") or {}).get("ops") or []:
        if isinstance(op, dict) and op.get("model"):
            seen.setdefault(op["model"], set()).add(op.get("rw") or "?")
    return ["%s %s" % (m, "/".join(sorted(rw))) for m, rw in seen.items()]


def _resolve_start(center: mq.Center, start: str) -> tuple:
    """→ (fnkey 'file#fn', header) or (None, reason-dict). Routes through detect_kind so a TASK/endpoint/function all land."""
    idx = center.idx()
    kind, key = T.detect_kind(start, center)
    if kind == "endpoint":
        method, path = key
        want = T.norm_path(path)
        for slug, ent in center.entities().items():
            for ep in ent.get("endpoints") or []:
                if str(ep.get("method", "")).upper() == method and T.norm_path(ep.get("path", "")) == want:
                    nid = "endpoint:%s %s" % (method, ep.get("path"))
                    node = idx["c4_nodes"].get((slug, nid)) or {}
                    return "%s#%s" % (ep.get("file"), ep.get("fn")), {
                        "kind": "endpoint", "entity": slug, "label": "%s %s" % (method, ep.get("path")), "stream": bool(ep.get("stream")),
                        "gates": [m.get("name") for m in (ep.get("middleware") or []) if isinstance(m, dict) and m.get("gate")],
                        "behind": node.get("behind")}
        return None, {"reason": "no declared endpoint matches %s %s (normalization strips /api/vN and collapses {x})" % (method, want)}
    if kind == "task":
        rec = idx["task_by_name"].get(key)
        if not rec or not rec.get("fnkey"):
            return None, {"reason": "no task root named %r on the map (task_roots lists %d)" % (key, len(idx["task_by_name"]))}
        node = (idx["c4_nodes"].get((rec["slug"], rec["nid"])) or {}) if rec.get("slug") else {}
        return rec["fnkey"], {"kind": "task", "entity": rec.get("slug"), "label": "TASK %s" % key, "stream": False, "gates": [],
                              "behind": node.get("behind"), "note": "a worker task root — no HTTP gate applies; dispatched by name"}
    if kind == "function":
        return key.replace("::", "#", 1), {"kind": "function", "label": key}
    if kind == "function_bare":
        keys = idx["fn_by_bare"].get(key) or []
        if len(keys) == 1:
            return keys[0].replace("::", "#", 1), {"kind": "function", "label": keys[0]}
        if len(keys) > 1:
            return None, {"reason": "%d functions share the bare name %r — pass file::name" % (len(keys), key), "ambiguous": keys[:mq.CAP]}
        return None, {"reason": "no function, endpoint or task root named %r in the map — grep is the floor" % key}
    return None, {"reason": "start must be an endpoint 'METHOD /path', a task 'TASK <name>', or a function file::fn / file#fn — %r resolves to kind %s" % (start, kind)}


def _tree_lines(fk: str, head: dict, hops: list[dict]) -> list[str]:
    first = "%s  [start%s]" % (fk, " · stream ⚡" if head.get("stream") else "")
    if head.get("gates"):
        first += "  gates: " + ", ".join(head["gates"])
    lines = [first]
    by_from: dict[str, list] = {}
    for h in hops:
        by_from.setdefault(h["from"], []).append(h)

    def walk(node, depth, seen):
        for h in by_from.get(node, []):
            tail = ("  models: " + " · ".join(h["models"])) if h.get("models") else ""
            if h.get("kind") == "task":
                tail += "  → " + h["task"]
            lines.append("%s%s (%s)  %s%s" % ("  " * depth, h["rel"], h["conf"], h["to"], tail))
            if h.get("kind") == "function" and h["to"] not in seen:
                seen.add(h["to"])
                walk(h["to"], depth + 1, seen)
    walk(fk, 1, {fk})
    return lines                                                   # bounded by the caller's hop cap (_HOP_CAP)


def t_trace(args: dict, roots) -> dict:
    center, root, source, reason = T._ctx(args, roots)
    if not center:
        return T._absent(root, source, reason)
    start = (args.get("start") or "").strip()
    if not start:
        raise mq.MapStop("start is required: 'METHOD /path' · 'TASK <name>' · file::fn · file#fn")
    try:
        depth = max(1, min(int(args.get("depth") or 4), 8))
        fanout = max(1, min(int(args.get("fanout") or 8), 20))
    except (TypeError, ValueError):
        raise mq.MapStop("depth and fanout must be integers (depth 1–8, fanout 1–20)")
    rels = args.get("rels")
    rels = set(rels) if isinstance(rels, list) and rels else set(_DEF_RELS)
    a, idx = center.archmap, center.idx()
    fi = a.get("function_insight") or {}
    out = T._base(center, root, source)
    out.update({"start": start, "depth": depth, "fanout": fanout, "rels": sorted(rels)})
    fx = center.fn_index()
    if not fx["present"]:
        out["reason"] = "no levels.json in this center — regen with the current generators (the fn-level order lives only there)"
        return out
    fk, head = _resolve_start(center, start)
    if not fk:
        out.update(head)
        return out
    out["from"] = head
    if head.get("kind") == "task":
        out["app_middleware"], out["app_middleware_note"] = [], "ASGI middleware wraps HTTP requests — a worker task runs outside it"
    else:
        out["app_middleware"] = [m.get("cls") for m in (a.get("app_middleware") or []) if isinstance(m, dict)]
    fk2task = {r["fnkey"]: name for name, r in idx["task_by_name"].items() if r.get("fnkey")}
    # the walk — BFS, depth-bounded, fanout per node (extracted edges first), rels filtered; every cap named below
    hops, visited, frontier, dropped = [], {fk}, [(fk, 0)], 0
    conf = {"extracted": 0, "inferred": 0, "other": 0}
    while frontier:
        cur, d = frontier.pop(0)
        if d >= depth:
            continue
        edges = [e for e in fx["fn_out"].get(cur, []) if e[1] in rels]
        edges.sort(key=lambda e: (0 if e[2] == "extracted" else 1, e[1], e[0]))
        if len(edges) > fanout:
            dropped += len(edges) - fanout
            edges = edges[:fanout]
        for t_, rel, cf in edges:
            conf["extracted" if cf == "extracted" else "inferred" if cf == "inferred" else "other"] += 1
            hop = {"depth": d + 1, "from": cur, "rel": rel, "conf": cf, "to": t_}
            if t_.startswith("provider:"):
                hop["kind"] = "provider"
            elif t_ in fk2task:
                hop["kind"], hop["task"] = "task", "endpoint:TASK %s" % fk2task[t_]
            else:
                hop["kind"] = "function"
                m = _models_of(fi, t_)
                if m:
                    hop["models"] = m
            hops.append(hop)
            if t_ not in visited and hop["kind"] == "function":
                visited.add(t_)
                frontier.append((t_, d + 1))
    # the honest denominator: every edge reachable with NO cap (depth ≤ 8, no fanout) — so the summary says what depth/fanout cut
    seen2, fr2, total = {fk}, [(fk, 0)], 0
    while fr2:
        cur, d = fr2.pop(0)
        if d >= 8:
            continue
        for t_, rel, _cf in fx["fn_out"].get(cur, []):
            if rel not in rels:
                continue
            total += 1
            if t_ not in seen2 and not t_.startswith("provider:") and t_ not in fk2task:
                seen2.add(t_)
                fr2.append((t_, d + 1))
    out.update({"hops": hops[:_HOP_CAP], "hops_more": max(0, len(hops) - _HOP_CAP),
                "tree": _tree_lines(fk, head, hops[:_HOP_CAP]),
                "start_models": _models_of(fi, fk) or None,
                "summary": "hops %d of %d reachable within 8 (fanout %d · depth %d named%s) · extracted %d / inferred %d — a FLOOR: cross-file calls are graft-inferred; grep before claiming absence"
                           % (len(hops), total, fanout, depth, (" · %d edge(s) beyond the fanout" % dropped) if dropped else "", conf["extracted"], conf["inferred"])})
    if head.get("behind"):
        out["behind_contrast"] = {"fns": head["behind"].get("fns"), "depth": head["behind"].get("depth"),
                                  "note": "the endpoint's behind block is the unordered MASS; this trace is the ORDER, capped"}
    if not hops:
        out["reason"] = "no %s edge(s) leave %s — cross-file calls are graft-inferred%s; grep is the floor" % (
            "/".join(sorted(rels)), fk, ("; the behind block says %s fn(s) exist" % head["behind"].get("fns")) if head.get("behind") else "")
    return out


# ── gates ──────────────────────────────────────────────────────────────────────
def _arg_of(name: str) -> str:
    if "(" in name and name.endswith(")"):
        return name[name.find("(") + 1:-1].strip()
    return ""


def _arg_head(name: str) -> str:
    """The first positional argument — `require_permission(Permission.X, allow_scope=True)` keys as `Permission.X`."""
    return _arg_of(name).split(",", 1)[0].strip()


def t_gates(args: dict, roots) -> dict:
    center, root, source, reason = T._ctx(args, roots)
    if not center:
        return T._absent(root, source, reason)
    gate = (args.get("gate") or "").strip()
    a, c = center.archmap, center.c4
    rows = []
    for slug, ent in center.entities().items():
        for ep in ent.get("endpoints") or []:
            rows.append((slug, "%s %s" % (ep.get("method"), ep.get("path")), [m for m in (ep.get("middleware") or []) if isinstance(m, dict)]))
    gated = [r for r in rows if any(m.get("gate") for m in r[2])]
    ungated = [r for r in rows if not any(m.get("gate") for m in r[2])]
    app_rows, app_note = T._app_mw(a)
    out = T._base(center, root, source)
    out.update({"endpoints_total": len(rows), "gated_total": len(gated),
                "ungated": {"count": len(ungated), "sample": [r[1] for r in ungated][:12]},
                "app_middleware": app_rows, "app_middleware_note": app_note + " · listed in order (every request, before the route's Depends)",
                "tasks": ("%d task root(s) run outside the HTTP gates — task roots carry no Depends" % len(a.get("task_roots") or [])) if a.get("task_roots") else "no task roots on this map"})
    sg = (c.get("stats") or {}).get("gate_endpoints")
    out["cross_check"] = ("stats say %s gated endpoint(s), this walk counts %d" % (sg, len(gated))) if sg is not None else "c4 stats carry no gate_endpoints count (older map)"
    if not any(r[2] for r in rows):
        out["reason"] = "the map recorded no Depends on any endpoint — router-level dependencies=[...] and ASGI middleware are not per-endpoint records"
    if not gate:                                                       # the census: every gate callee, how many endpoints it guards
        by_callee: dict[str, dict] = {}
        for slug, label, mws in rows:
            for m in mws:
                if not m.get("gate"):
                    continue
                k = m.get("callee") or m.get("name") or "?"
                rec = by_callee.setdefault(k, {"callee": k, "fn": m.get("fn"), "endpoints": 0, "via": set(), "args": set()})
                rec["endpoints"] += 1
                rec["via"].add(m.get("via") or "?")
                arg = _arg_of(m.get("name") or "")
                if arg:
                    rec["args"].add(arg)
        out["gates"] = sorted([{**r, "via": sorted(r["via"]), "args": len(r["args"])} for r in by_callee.values()], key=lambda r: (-r["endpoints"], r["callee"]))[:mq.CAP]
        out["gates_note"] = "pass gate=<callee | file::fn | argument substring> for the endpoint list and the by-argument split"
        return out

    def how(m):
        """callee · fn (exact) · argument · name-substring — or None. An exact hit is one gate; a substring may be several."""
        if not m.get("gate"):
            return None
        if m.get("callee") == gate or m.get("fn") == gate or str(m.get("fn") or "").endswith("::" + gate):
            return "callee" if m.get("callee") == gate else "fn"
        name = str(m.get("name") or "")
        if gate and gate in _arg_of(name):
            return "argument"
        if gate and gate in name:
            return "name-substring"
        return None
    found, non_gate = [], []
    for slug, label, mws in rows:
        for m in mws:
            name = m.get("name") or ""
            h = how(m)
            if h:
                found.append({"endpoint": label, "entity": slug, "dep": name, "callee": m.get("callee") or name.split("(")[0], "fn": m.get("fn"),
                              "via": m.get("via"), "arg": _arg_of(name) or None, "how": h})
            elif not m.get("gate") and (m.get("callee") == gate or name == gate or str(m.get("fn") or "").endswith("::" + gate)):
                non_gate.append({"endpoint": label, "entity": slug, "dep": name, "via": m.get("via")})
    exact = [r for r in found if r["how"] in ("callee", "fn")]
    if exact:                                                      # an exact callee/fn hit IS the gate — substring hits on other deps are named, not merged
        others = {}
        for r in found:
            if r["how"] not in ("callee", "fn"):
                others[r["callee"]] = others.get(r["callee"], 0) + 1
        found = exact
        if others:
            out["also_named_in"] = others
            out["also_named_note"] = "other gate dependencies whose NAME contains %r — not this gate; pass their callee to list them" % gate
    callees = sorted({r["callee"] for r in found})
    if len(callees) > 1:
        out["ambiguous_gate"] = "%r matched %d distinct dependencies (%s) by %s — pass the exact callee or file::fn to narrow" % (
            gate, len(callees), " · ".join(callees[:8]), "argument" if all(r["how"] == "argument" for r in found) else "name substring")
    by_arg: dict[str, int] = {}
    for r in found:
        k = _arg_head(r["dep"]) or "—"
        by_arg[k] = by_arg.get(k, 0) + 1
    out.update({"gate": gate, "callees": callees, "fn": sorted({r["fn"] for r in found if r.get("fn")}),
                "endpoints": found[:40], "endpoints_matched": len(found),
                "endpoints_note": ("cap 40 named of %d" % len(found)) if len(found) > 40 else None,
                "by_argument": dict(sorted(by_arg.items(), key=lambda kv: (-kv[1], kv[0]))[:30]),
                "by_argument_note": "keyed on the first positional argument; each row's `arg` carries the full call",
                "non_gate_deps": non_gate[:mq.CAP],
                "non_gate_note": "a dependency that is not a gate (a session, a settings object) — listed so it is never reported as one"})
    if not found:
        out["reason"] = ("no endpoint names %r in a param-dep or decorator — a router-level dependencies=[...] or an ASGI middleware is not in this list; app-scope above" % gate
                         + ("; %r appears only as a non-gate dependency (non_gate_deps)" % gate if non_gate else ""))
    return out


# ── registry (appended into tools.TOOLS by tools.py) ──────────────────────────
RO = T.RO
TOOLS = [
    {"name": "trace", "fn": t_trace, "annotations": RO,
     "description": "The ORDERED path from an endpoint, TASK root or function to the models and providers it reaches — one hop per line with its confidence (levels.json); depth/fanout named; a FLOOR.",
     "inputSchema": T._schema({"start": {"type": "string", "description": "'METHOD /path' · 'TASK <name>' · file::fn · file#fn"},
                               "depth": {"type": "integer", "description": "Hops to walk (default 4, max 8)."},
                               "fanout": {"type": "integer", "description": "Edges followed per node (default 8, max 20; extracted first)."},
                               "rels": {"type": "array", "items": {"type": "string", "enum": ["calls", "dispatches", "depends", "reaches"]}, "description": "Edge kinds to follow (default all four)."},
                               **T.ROOT_PROP}, ["start"])},
    {"name": "gates", "fn": t_gates, "annotations": RO,
     "description": "Which endpoints a gate guards — by callee, file::fn key or argument string (Permission.X) — split by argument, non-gate deps apart, ungated count, the ASGI middleware on every request. Omit → census.",
     "inputSchema": T._schema({"gate": {"type": "string", "description": "A gate callee (require_permission), its file::fn key, or an argument substring (Permission.MANAGE_LLMS). Omit for the census of all gates."},
                               **T.ROOT_PROP})},
]
