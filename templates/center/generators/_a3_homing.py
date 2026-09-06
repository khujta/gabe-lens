"""_a3_homing — the membership EVIDENCE: where a piece's witnesses disagree with its file (Part C, 2026-09-06).

Operator ruling (2026-09-06): a code piece is identified by its content, its functionality and its USAGE; where it
sits in the tree is an INDICATOR — a prior and a tie-breaker — never the DEFINITION of what it belongs to. Today's
entity definition IS the file claim (center.config `code.*` globs; the frontend by feature layout or config), so a
function whose callers and data all live in another entity is homed by its folder. This module never re-homes
anything: it weighs three witnesses per piece and records the verdict, so the station, the pulse and gabe-map can SAY
where usage disagrees. Re-homing is a later, opt-in switch (`homing: usage-first`) — see the plan.

Three witnesses (an absent witness abstains; `__unclaimed__` may consume, never receive):
  file  · today's home — the entity whose claim owns the file (endpoints: the l2 slug; fe pieces: `home`)
  users · who consumes the piece — callers' entities (levels fn_edges `ss` for calls · depends · dispatches),
          the screens that fetch an endpoint (bridge `from_slug`), the pieces that render / use / import a fe piece
  data  · what the piece touches — the entities that declare the models in its access ops (fn / endpoint), or the
          entities of the endpoints a fe piece fetches (bridge `to_slug`)

Verdict per piece, from the witnesses that exist:
  agree  — every present witness's majority is the file entity
  move   — ONE other entity holds ≥ MOVE_SHARE of the users AND data agrees with it or abstains (a move candidate)
  shared — ≥ SHARED_MIN distinct consuming entities and none holds ≥ MOVE_SHARE (a cross-cutting aspect)
  stay   — disagreement below both bars, or data contradicting the users: the file wins as the tie-breaker

Pure derivation over the in-memory archmap + c4 graph + levels graph — no source read, no new arm, honest-empty
without levels (`present: False` + the reason). Every threshold is printed in the stats so the reader knows the bar.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

MOVE_SHARE = 0.60          # the share of users ONE other entity must hold for a move candidate
MOVE_MIN_USERS = 2         # a single caller never flips a verdict — below this the disagreement reads `stay` with `to` named
SHARED_MIN = 3             # distinct consuming entities for a shared / aspect verdict
UNCLAIMED = "__unclaimed__"
_USER_RELS = ("calls", "depends", "dispatches")
_FE_USER_RELS = ("renders", "uses-hook", "uses-store", "imports", "fecall")
CAP_NAMED = 40


def _models_to_entity(amap: dict[str, Any]) -> dict[str, str]:
    m2s: dict[str, str] = {}
    for slug, ent in (amap.get("entities") or {}).items():
        for m in ent.get("models") or []:
            if m.get("cls"):
                m2s.setdefault(m["cls"], slug)
            if m.get("table"):
                m2s.setdefault(m["table"], slug)
    return m2s


def _files_to_entity(amap: dict[str, Any]) -> dict[str, str]:
    f2s: dict[str, str] = {}
    for slug, ent in (amap.get("entities") or {}).items():
        for row in ent.get("files") or []:
            if len(row) >= 2:
                f2s.setdefault(row[1], slug)
    return f2s


def _data_of_ops(ops: Any, m2s: dict[str, str]) -> Counter:
    c: Counter = Counter()
    for op in ops or []:
        if isinstance(op, dict):
            s = m2s.get(op.get("model") or "") or m2s.get(op.get("table") or "")
            if s:
                c[s] += 1
    return c


def _majority(w: Counter, slug: str | None) -> bool:
    """A strict majority (> half) — never a plurality, never an insertion-order tie-break (review 2026-09-06)."""
    return bool(slug) and w.get(slug, 0) * 2 > sum(w.values())


def verdict(home: str | None, users: Counter, data: Counter) -> tuple[str, str | None, float | None, int]:
    """→ (verdict, to, share, others). `others` = the consuming entities other than home (breadth, carried on the record so a
    move candidate with wide use says so). `home` None (unhomed) → nothing to compare: unweighed."""
    present = [w for w in (users, data) if w]
    if not present or not home:
        return "unweighed", None, None, 0
    distinct = len([s for s in users if s != home])
    if all(_majority(w, home) for w in present):
        return "agree", None, None, distinct
    if users:
        total = sum(users.values())
        others = [(s, n) for s, n in users.most_common() if s != home and s != UNCLAIMED]
        if others:
            top, n = others[0]
            share = n / total if total else 0.0
            data_ok = (not data) or _majority(data, top)
            if share >= MOVE_SHARE and data_ok and total >= MOVE_MIN_USERS:
                return "move", top, round(share, 2), distinct
            if distinct >= SHARED_MIN and share < MOVE_SHARE:
                return "shared", None, round(share, 2), distinct
            return "stay", top, round(share, 2), distinct
        return "stay", None, None, distinct
    # users abstain, data disagrees alone: the data witness names its majority, the file still wins
    top = data.most_common(1)[0][0]
    return "stay", (top if top != UNCLAIMED else None), None, distinct


def evidence(amap: dict[str, Any], graph: dict[str, Any] | None, levels: dict[str, Any] | None) -> dict[str, Any]:
    """The evidence block: `pieces` (only the pieces whose witnesses DISAGREE — the agree count rides `stats`), `stats`, `rule`."""
    rule = {"move_share": MOVE_SHARE, "move_min_users": MOVE_MIN_USERS, "shared_min": SHARED_MIN,
            "text": "agree = every witness names the file's entity · move candidate = ≥%d%% of ≥%d users in ONE other entity, data agrees or abstains · "
                    "shared = ≥%d consuming entities, none ≥%d%% · stay = below both bars, the file wins · evidence only, nothing re-homed"
                    % (round(MOVE_SHARE * 100), MOVE_MIN_USERS, SHARED_MIN, round(MOVE_SHARE * 100))}
    if not levels or not isinstance(levels, dict) or not levels.get("fn_edges") and not (graph or {}).get("fe"):
        reason = "no levels graph (graft arm absent) — the users witness cannot be read; nothing weighed"
        return {"present": False, "reason": reason, "pieces": {}, "stats": {"present": False, "pieces": 0, "reason": reason}, "rule": rule}
    graph = graph or {}
    m2s = _models_to_entity(amap)
    f2s = _files_to_entity(amap)
    fi = amap.get("function_insight") or {}
    ents = set((amap.get("entities") or {}).keys())
    fe_homing = ((graph.get("stats") or {}).get("fe") or {}).get("homing")     # layout | config — which witness homed the frontend
    pieces: dict[str, dict[str, Any]] = {}

    def _mk(kind: str, home: str | None, by: str, users: Counter, data: Counter, v: str, to: str | None, share: float | None, others: int, **extra: Any) -> dict[str, Any]:
        return {"kind": kind, "home": home, "by": by, "users": dict(users.most_common()), "data": dict(data.most_common()), "verdict": v, "to": to,
                "to_kind": (("entity" if to in ents else "fe-area") if to else None), "share": share, "others": others, **extra}
    # ── users from the levels fn_edges (callers → callee), keyed on the callee `file#fn` ──
    fn_users: dict[str, Counter] = {}
    for e in levels.get("fn_edges") or []:
        if e.get("rel") in _USER_RELS and e.get("t") and e.get("ss"):
            fn_users.setdefault(e["t"], Counter())[e["ss"]] += 1
    # ── backend functions ──
    for key, rec in fi.items():
        if "::" not in key:
            continue
        fk = key.replace("::", "#", 1)
        home = rec.get("entity") or f2s.get(key.split("::", 1)[0])
        users = fn_users.get(fk) or Counter()
        data = _data_of_ops((rec.get("access") or {}).get("ops"), m2s)
        if not users and not data:
            continue
        v, to, share, others = verdict(home, users, data)
        if v == "unweighed":
            continue
        pieces[fk] = _mk("function", home, "file", users, data, v, to, share, others)
    # ── endpoints (incl. TASK roots): users = the screens that fetch them (+ dispatchers), data = the access rollup ──
    ep_users: dict[str, Counter] = {}
    for ce in graph.get("cross_edges") or []:
        if ce.get("kind") == "bridge" and ce.get("to") and ce.get("from_slug"):
            ep_users.setdefault(ce["to"], Counter())[ce["from_slug"]] += 1
    task_fk: dict[str, str] = {}
    for r in amap.get("task_roots") or []:
        if r.get("path") and r.get("file") and r.get("fn"):
            task_fk["endpoint:TASK %s" % r["path"]] = "%s#%s" % (r["file"], r["fn"])
    for slug, l2 in (graph.get("l2") or {}).items():
        for n in (l2 or {}).get("nodes") or []:
            if n.get("kind") != "endpoint" or not n.get("id"):
                continue
            nid = n["id"]
            users = Counter(ep_users.get(nid) or {})
            if nid in task_fk:
                users.update(fn_users.get(task_fk[nid]) or {})
            acc = n.get("access")
            data = _data_of_ops(acc.get("ops") if isinstance(acc, dict) else acc, m2s)
            if not users and not data:
                continue
            v, to, share, others = verdict(slug, users, data)
            if v == "unweighed":
                continue
            pieces[nid] = _mk("task" if nid in task_fk else "endpoint", slug, "file", users, data, v, to, share, others)
    # ── frontend pieces: users = the pieces that render / use / import them, data = the endpoints they fetch ──
    fe = graph.get("fe") or {}
    fps = fe.get("pieces") or []
    if fps:
        def _home_of(p: dict[str, Any]) -> str | None:
            h = p.get("home") or ""
            return h[3:] if h.startswith("fe·") else (h or None)
        fe_users: dict[int, Counter] = {}
        for e in fe.get("edges") or []:
            if isinstance(e, (list, tuple)) and len(e) >= 3 and e[2] in _FE_USER_RELS:
                s_i, d_i = e[0], e[1]
                if isinstance(s_i, int) and isinstance(d_i, int) and 0 <= s_i < len(fps):
                    hs = _home_of(fps[s_i])
                    if hs:
                        fe_users.setdefault(d_i, Counter())[hs] += 1
        fe_data: dict[str, Counter] = {}
        stem_data: dict[str, Counter] = {}
        for ce in graph.get("cross_edges") or []:
            if ce.get("kind") == "bridge" and ce.get("to_slug"):
                if ce.get("export"):
                    fe_data.setdefault(ce["export"], Counter())[ce["to_slug"]] += 1
                if ce.get("from"):
                    stem_data.setdefault(str(ce["from"]).split("web:", 1)[-1], Counter())[ce["to_slug"]] += 1
        for i, p in enumerate(fps):
            if not isinstance(p, dict) or not p.get("id"):
                continue
            home = _home_of(p)
            users = fe_users.get(i) or Counter()
            stem = str(p.get("file") or "").rsplit(".", 1)[0]
            data = fe_data.get(p["id"]) or stem_data.get(stem) or Counter()
            extra: dict[str, Any] = {}
            if data and home and home not in ents:
                # the data witness names BACKEND entities; a frontend-only area (app-shell · design-system …) is not one of them — the
                # two namespaces cannot be compared, so data abstains and says why (review 2026-09-06)
                extra["data_note"] = "home %r is a frontend area, not a declared entity — the data witness cannot be compared" % home
                data = Counter()
            if not users and not data:
                continue
            v, to, share, others = verdict(home, users, data)
            if v == "unweighed":
                continue
            by = p.get("homed_by") or ("idiom" if fe_homing == "config" else "layout")   # a piece no config claim matched on a config-homed estate sits by the directory idiom
            pieces[p["id"]] = _mk("fe:%s" % (p.get("kind") or "piece"), home, by, users, data, v, to, share, others, **extra)
    stats: dict[str, Any] = {"present": True, "pieces": len(pieces), "agree": 0, "stay": 0, "move": 0, "shared": 0,
                             "by_kind": {}, "thresholds": {"move_share": MOVE_SHARE, "move_min_users": MOVE_MIN_USERS, "shared_min": SHARED_MIN}}
    for rec in pieces.values():
        stats[rec["verdict"]] = stats.get(rec["verdict"], 0) + 1
        bk = stats["by_kind"].setdefault(rec["kind"].split(":", 1)[0], {"pieces": 0, "move": 0, "shared": 0})
        bk["pieces"] += 1
        if rec["verdict"] in ("move", "shared"):
            bk[rec["verdict"]] += 1
    moves = sorted((k for k, r in pieces.items() if r["verdict"] == "move"), key=lambda k: (-(pieces[k]["share"] or 0), k))
    stats["move_named"] = [{"piece": k, "home": pieces[k]["home"], "to": pieces[k]["to"], "share": pieces[k]["share"]} for k in moves[:CAP_NAMED]]
    stats["move_named_note"] = ("first %d of %d named" % (CAP_NAMED, len(moves))) if len(moves) > CAP_NAMED else None
    stats["shared_named"] = sorted(k for k, r in pieces.items() if r["verdict"] == "shared")[:CAP_NAMED]
    pieces = {k: v for k, v in pieces.items() if v["verdict"] != "agree"}     # the agree count rides stats; no consumer reads an agree record
    return {"present": True, "pieces": pieces, "stats": stats, "rule": rule}


def attach(graph: dict[str, Any], ev: dict[str, Any]) -> None:
    """Put the counts on `stats.homing` and a `home_ev` field on every endpoint node / fe piece whose verdict ≠ agree."""
    graph.setdefault("stats", {})["homing"] = ev.get("stats") or {"present": False}
    pieces = ev.get("pieces") or {}
    for slug, l2 in (graph.get("l2") or {}).items():
        for n in (l2 or {}).get("nodes") or []:
            rec = pieces.get(n.get("id") or "")
            if rec and rec["verdict"] != "agree":
                n["home_ev"] = _ev_field(rec)
    for p in (graph.get("fe") or {}).get("pieces") or []:
        rec = pieces.get(p.get("id") or "") if isinstance(p, dict) else None
        if rec and rec["verdict"] != "agree":
            p["home_ev"] = _ev_field(rec)


def _ev_field(rec: dict[str, Any]) -> dict[str, Any]:
    out = {k: rec.get(k) for k in ("verdict", "to", "to_kind", "share", "users", "data", "by", "others")}
    if rec.get("data_note"):
        out["data_note"] = rec["data_note"]
    return out
