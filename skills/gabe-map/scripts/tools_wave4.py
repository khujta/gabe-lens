#!/usr/bin/env python3
"""tools_wave4 — the ENTITY MODELS tool (Phase 3 of docs/design/entity-models/plan.md, 2026-09-06).

entity_models · ONE tool, four modes — the emitter's four models (claim · seeded · derived · proposed) as they sit on the
committed map. `claim` is the REGISTRY and the JOIN KEY (every other tool joins on the claim slug); the other three are
VIEWS — per-piece home deltas the station applies live, never re-homed on disk.
  no args            → the CENSUS: the four views with their counts and state, `today: claim`, the rule, the caps.
  model=<view>       → that view's ROSTER (derived features with kind · named_by · anchor · purity; proposed verdicts +
                       candidates; seeded moves by destination; claim = the entity list) + abstained + coverage.
  entity=<slug|d:…>  → the members homed there under `model` (default claim), capped at mq.CAP with the cap named, each
                       with its mark (moved · abstain · held).
  piece=<file#fn | endpoint:… | 'METHOD /path' | fe:… | path>  → the CROSS-MODEL row {claim, seeded, derived, proposed}
                       with why + mark per view.
Why ONE tool and not a `model=` flag on five: three of the four views produce names that are NOT slugs, gabe-map joins on
slug everywhere, and MCP schemas are deferred — a flag is invisible until a schema loads, a NAME in the instructions is
the discovery surface. Reads `c4.models` (already loaded — delta-sized) for census/roster, `levels.models` LAZILY for
function pieces only; `map_status` never touches either. Honest-empty tri-state (mq.MODELS_STATES): present ·
not_emitted (an older map — regen) · absent (the emitter ran and says why). Read-only, no subprocess, every cap named.
Registered into tools.TOOLS at import (after wave 3).
"""
from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import re  # noqa: E402
import mapquery as mq  # noqa: E402
import tools as T  # noqa: E402

VIEWS = ("claim", "seeded", "derived", "proposed")
_C4_PREFIX = ("endpoint:", "model:", "schema:", "web:", "provider:", "middleware:", "flag:", "prompt:", "external:", "element:", "fe:")
_CASE_RX = re.compile(r"^(.*?)( · | — )(.*)$")


def _case(run: str, how: str) -> str:
    ws = [w for w in re.split(r"[\s_\-/&]+", run) if w]                     # mirrors _a3_naming._case: interiors kept
    if not ws:
        return run
    if how == "camel":
        return ws[0][:1].lower() + ws[0][1:] + "".join(w[:1].upper() + w[1:] for w in ws[1:])
    if how == "pascal":
        return "".join(w[:1].upper() + w[1:] for w in ws)
    return run


def _render(form: str, name: str) -> str:
    """The three-line substitution every surface owns (mirrors _a3_naming.render): {name} · {name|camel} · {name|pascal} on the leading word-run."""
    m = _CASE_RX.match(name or "")
    head, sep, tail = (m.group(1), m.group(2), m.group(3)) if m else (name or "", "", "")
    out = (form or "{name}").replace("{name|camel}", _case(head, "camel") + sep + tail).replace("{name|pascal}", _case(head, "pascal") + sep + tail).replace("{name}", name or "")
    return re.sub(r"\{name\|[a-z]+\}", name or "", out)


def _naming(block: dict) -> dict:
    nb = (block or {}).get("naming") or {}
    return nb if isinstance(nb, dict) and nb.get("positions") else {}


def _named(block: dict, row: dict) -> dict:
    """`name` under the CONFIG default strategy (a text surface has no reader to hold a preference) + `name_from` + the alternates; the id stays beside it."""
    nb = _naming(block)
    k = nb.get("default") or "domain"
    names = row.get("names") or {}
    if k != "domain" and names.get(k):
        return {"name": names[k], "name_from": k, "names": names}
    return {"name": row.get("name"), "name_from": "domain" if row.get("name") else None, "names": names}


def _label(block: dict, ident: str, name: str) -> str:
    """The name through the config's frontend/backend convention — `[api] cooking` · `cookingSessions` — never used as a key."""
    nb = _naming(block)
    fe = nb.get("fe") or {}
    forms = fe.get("forms") if fe.get("present") is not False else None
    conv = fe.get("convention") or "case"
    form = (forms or {}).get(conv) or {"fe": "fe · {name}", "be": "{name}"}
    return _render(form["fe" if str(ident).startswith("fe·") else "be"], name)


_MARK_TEXT = {"moved": "moved by this view", "abstain": "no witness reaches this piece — it keeps its claim", "held": "shared plumbing — held out of every re-home",
              None: "keeps its claim"}


def _u(s):
    return "unclaimed" if s == "__unclaimed__" else s                                                    # R10


def _homes(center: mq.Center, block: dict, view: str, want_levels: bool) -> tuple[dict, set, set]:
    """The view's home delta (+ abstain/held sets): the c4 half from the loaded block, the levels half only when asked."""
    H = dict((block.get("homes") or {}).get(view) or {})
    AB = set((block.get("abstain") or {}).get(view) or [])
    HD = set((block.get("held") or {}).get(view) or [])
    if want_levels:
        lv = center.entity_models_levels()
        H.update((lv.get("homes") or {}).get(view) or {})
        AB |= set((lv.get("abstain") or {}).get(view) or [])
        HD |= set((lv.get("held") or {}).get(view) or [])
    return H, AB, HD


def _mark(pid: str, H: dict, AB: set, HD: set) -> str | None:
    return "moved" if pid in H else ("abstain" if pid in AB else ("held" if pid in HD else None))


def _roster_index(block: dict) -> dict:
    r = {}
    for row in ((block.get("rosters") or {}).get("derived") or []):
        if row.get("id"):
            r[row["id"]] = row
            if row.get("twin"):
                r[row["twin"]] = {**row, "id": row["twin"], "twin_of": row["id"]}
    for row in ((block.get("rosters") or {}).get("candidates") or []):
        if row.get("id"):
            r[row["id"]] = {**r.get(row["id"], {}), **row, "candidate": True}
    return r


_BLOCK: dict = {}      # the current block for the row helpers (set per call — one process serves one request at a time)


def _cluster_row(cid: str, ridx: dict, verdicts: dict) -> dict | None:
    """What a cluster IS in one line — a feature/aspect/layer/candidate row, or a declared slug's proposed verdict."""
    r = ridx.get(cid)
    if r:
        nm = _named(_BLOCK.get("b") or {}, r)
        return {"id": cid, **nm, "label": _label(_BLOCK.get("b") or {}, cid, nm.get("name") or cid), "kind": ("candidate feature" if r.get("candidate") else r.get("kind")),
                **({"named_by": r["named_by"]} if r.get("named_by") else {}), **({"anchor_table": r["anchor_table"], "anchor_by": r.get("anchor_by")} if r.get("anchor_table") else {}),
                **({"purity": r["purity"]} if r.get("purity") is not None else {}), **({"twin_of": r["twin_of"]} if r.get("twin_of") else {}),
                **({"suggested_slug": r["suggested_slug"]} if r.get("suggested_slug") else {}), "why": r.get("why")}
    v = verdicts.get(cid.replace("fe·", "", 1))
    if v:
        return {"id": cid, "kind": "declared entity", "verdict": v.get("verdict"), "why": v.get("why")}
    return None


def _claim_of(center: mq.Center, pid: str) -> str | None:
    """The claim home of a c4 id (its l2 slug · an fe piece's home) or a function key (function_insight.entity)."""
    idx = center.idx()
    for (slug, nid) in idx["c4_nodes"]:
        if nid == pid:
            return slug
    for p in (((center.c4.get("fe") or {}).get("pieces")) or []):
        if isinstance(p, dict) and p.get("id") == pid:
            return p.get("home")
    rec = (center.archmap.get("function_insight") or {}).get(pid.replace("#", "::", 1))
    if rec:
        return rec.get("entity") or "__unclaimed__"
    if pid.startswith("endpoint:"):                                        # an endpoint the c4 did not draw but the archmap declares
        label = pid.split(":", 1)[1]
        for slug, ent in center.entities().items():
            for ep in ent.get("endpoints") or []:
                if "%s %s" % (str(ep.get("method") or "").upper(), ep.get("path")) == label:
                    return slug
    return None


def _resolve_piece(center: mq.Center, piece: str) -> tuple[str | None, str]:
    """A piece argument → the id the models maps carry (c4 id or `file#fn`), plus the kind word."""
    t = piece.strip()
    if t.startswith(_C4_PREFIX):
        return t, ("fe piece" if t.startswith("fe:") else t.split(":", 1)[0])
    kind, key = T.detect_kind(t, center)
    if kind == "endpoint":
        return "endpoint:%s %s" % (key[0], key[1]), "endpoint"
    if kind == "task":
        return "endpoint:TASK %s" % key, "task"
    if kind == "function":
        return str(key).replace("::", "#", 1), "function"
    if kind in ("model", "schema"):
        return "%s:%s" % (kind, key), kind
    if kind == "file":
        return t, "file (no model maps a bare file — pass file#fn, an endpoint or an fe: id)"
    return None, kind


def t_entity_models(args: dict, roots) -> dict:
    center, root, source, reason = T._ctx(args, roots)
    if not center:
        return T._absent(root, source, reason)
    model = (args.get("model") or "").strip().lower()
    entity = (args.get("entity") or "").strip()
    piece = (args.get("piece") or "").strip()
    if model and model not in VIEWS:
        raise mq.MapStop("model must be one of claim · seeded · derived · proposed (claim is the registry; the other three are views over it)")
    out = T._base(center, root, source)
    block, state, why = center.entity_models()
    out["state"] = state
    out["states"] = mq.MODELS_STATES
    out["law"] = "claim is the registry and the join key — every other tool joins on the claim slug; seeded · derived · proposed are VIEWS (per-piece home deltas), nothing is re-homed on disk"
    if state != "present":
        out["reason"] = why
        return out
    views = block.get("views") or {}
    _BLOCK["b"] = block
    verdicts = {r.get("slug"): r for r in ((block.get("rosters") or {}).get("proposed") or []) if r.get("slug")}
    ridx = _roster_index(block)
    # ── piece → the cross-model row ──
    if piece:
        pid, kind = _resolve_piece(center, piece)
        out["piece"] = piece
        if not pid:
            out.update({"found": False, "reason": "%s is not a piece the models map (%s) — pass file#fn, 'METHOD /path', 'TASK <name>', an fe:/endpoint:/schema:/model: id; grep -rn remains the floor" % (piece, kind)})
            return out
        claim = _claim_of(center, pid)
        if claim is None:
            out.update({"found": False, "id": pid, "kind": kind, "reason": "no piece with this id on the map (c4 nodes · fe pieces · function_insight) — grep -rn remains the floor"})
            return out
        is_fn = kind == "function"
        row = {"claim": _u(claim)}
        marks, whys = {}, {}
        for v in ("seeded", "derived", "proposed"):
            if not (views.get(v) or {}).get("present"):
                row[v] = None
                whys[v] = (views.get(v) or {}).get("reason") or "view absent"
                continue
            H, AB, HD = _homes(center, block, v, want_levels=is_fn)
            home = H.get(pid, claim)
            row[v] = _u(home)
            marks[v] = _mark(pid, H, AB, HD)
            cr = _cluster_row(home, ridx, verdicts) if home != claim else None
            whys[v] = (cr.get("why") if cr else None) or _MARK_TEXT[marks[v]]
        out.update({"found": True, "id": pid, "kind": kind, "homes": row, "mark": marks, "why": whys,
                    "hub": next((s for s in (block.get("shared") or []) if s.get("id") == pid), None),
                    "note": "one row, four homes — the claim is the join key; a view's name (d:… · a:… · fe·d:…) is never a slug"})
        return out
    # ── entity → members under a model ──
    if entity:
        v = model or "claim"
        out.update({"entity": entity, "model": v})
        if v != "claim" and not (views.get(v) or {}).get("present"):
            out.update({"found": False, "reason": "the %s view is absent — %s" % (v, (views.get(v) or {}).get("reason") or "no reason recorded")})
            return out
        H, AB, HD = _homes(center, block, v, want_levels=(v != "claim"))
        ids = {nid for (_s, nid) in center.idx()["c4_nodes"]}
        ids |= {p["id"] for p in (((center.c4.get("fe") or {}).get("pieces")) or []) if isinstance(p, dict) and p.get("id")}
        ids |= set(H) | AB | HD
        members = []
        for pid in sorted(ids):
            home = H.get(pid) or _claim_of(center, pid)
            if home == entity:
                members.append({"id": pid, "mark": _mark(pid, H, AB, HD), "claim": _u(_claim_of(center, pid))})
        cr = _cluster_row(entity, ridx, verdicts)
        if not members and not cr and entity not in center.entities() and not entity.startswith("fe·"):
            out.update({"found": False, "reason": "no entity or cluster named %s under the %s model — entity_context lists the slugs, model=%s the clusters; grep -rn remains the floor" % (entity, v, v)})
            return out
        out.update({"found": True, "what": cr, "members": members[:mq.CAP], "members_total": len(members), "cap": mq.CAP,
                    "moved_in": sum(1 for m in members if m["mark"] == "moved"), "held": sum(1 for m in members if m["mark"] == "held"),
                    "note": ("function pieces ride levels.json and are listed under a non-claim model only" if v == "claim" else "members = c4 pieces + function keys whose home under this view resolves here")})
        return out
    # ── model → the roster ──
    if model:
        vw = views.get(model) or {}
        out.update({"model": model, "view": vw})
        if model != "claim" and not vw.get("present"):
            out["reason"] = vw.get("reason") or "view absent"
            return out
        if model == "claim":
            out["entities"] = sorted(center.entities().keys())
            out["note"] = "the registry — entity_context <slug> for a slice; the other three views are deltas over these slugs"
            return out
        H, AB, HD = _homes(center, block, model, want_levels=True)
        out["coverage"] = {"moved": len(H), "abstained": len(AB), "held": len(HD)}
        if model == "seeded":
            by_to: dict[str, list] = {}
            for pid, to in sorted(H.items()):
                by_to.setdefault(_u(to), []).append(pid)
            out["moves"] = {to: {"count": len(ps), "pieces": ps[:mq.CAP]} for to, ps in by_to.items()}
            out["held"] = sorted(HD)[:mq.CAP]
            out["bands"] = (block.get("bands") or {}).get("seeded")
            out["note"] = "Part C's move verdicts applied — hubs held, targets tier-consistent; %s" % (vw.get("note") or "")
        elif model == "derived":
            rows = ((block.get("rosters") or {}).get("derived") or [])
            out["clusters"] = [{**{k: r.get(k) for k in ("id", "kind", "named_by", "anchor_table", "anchor_by", "domain", "endpoints", "screens", "purity", "twin", "detector", "drawn", "why") if r.get(k) is not None},
                                **_named(block, r), "label": _label(block, r.get("id") or "", _named(block, r).get("name") or r.get("id") or "")}
                               for r in rows[:mq.CAP]]
            out["clusters_total"] = len(rows)
            out["abstained"] = sorted(AB)[:mq.CAP]
            out["note"] = vw.get("note")
        else:
            out["verdicts"] = [{k: r.get(k) for k in ("slug", "verdict", "why", "suggested_edit") if r.get(k) is not None} for r in ((block.get("rosters") or {}).get("proposed") or [])[:mq.CAP]]
            out["candidates"] = [{**{k: r.get(k) for k in ("id", "named_by", "anchor_table", "suggested_slug", "endpoints", "spans_entities") if r.get(k) is not None}, **_named(block, r)}
                                 for r in ((block.get("rosters") or {}).get("candidates") or [])[:mq.CAP]]
            out["note"] = vw.get("note")
        out["cap"] = mq.CAP
        out["truncated"] = (block.get("stats") or {}).get("truncated") or []
        return out
    # ── the census ──
    out.update({"today": block.get("default") or "claim", "rule": block.get("rule"),
                "views": {v: ({k: views[v].get(k) for k in ("present", "moved", "held", "abstained", "features", "aspects", "layers", "atoms", "anchored", "purity", "verdicts", "candidates", "reason") if views.get(v, {}).get(k) is not None}
                              if isinstance(views.get(v), dict) else {"present": False}) for v in VIEWS},
                "shared_hubs": len(block.get("shared") or []),
                "naming": ({"default": _naming(block).get("default"), "source": _naming(block).get("source"), "convention": ((_naming(block).get("fe") or {}).get("convention") if (_naming(block).get("fe") or {}).get("present") is not False else "none — " + str((_naming(block).get("fe") or {}).get("reason"))),
                            "coverage": _naming(block).get("coverage"), "collisions": _naming(block).get("collisions"), "disabled": _naming(block).get("disabled"), "config_error": _naming(block).get("config_error"),
                            "unused_words": _naming(block).get("unused_words"), "unknown_entities": _naming(block).get("unknown_entities"),
                            "note": "names are DISPLAY — text surfaces speak the project default (center.config.json#naming); the station honours a reader's pill; every answer keeps the raw id beside the name"}
                           if _naming(block) else {"state": "not_emitted", "reason": "no naming block on this map — regen with the current generators; names fall back to the emitted row.name"}),
                "candidates": [r.get("name") for r in ((block.get("rosters") or {}).get("candidates") or [])][:mq.CAP],
                "caps": (block.get("stats") or {}).get("caps"), "truncated": (block.get("stats") or {}).get("truncated") or [],
                "next": "model=<view> for a roster · entity=<slug|d:…> for members · piece=<file#fn|'METHOD /path'|fe:…> for the cross-model row"})
    return out


TOOLS = [
    {"name": "entity_models", "fn": t_entity_models, "annotations": T.RO,
     "description": "The four entity models on the map — claim (the registry) · seeded · derived · proposed (views) — named by the project's strategy. No args → census; model= roster; entity= members; piece= its homes.",
     "inputSchema": T._schema({"model": {"type": "string", "enum": list(VIEWS), "description": "A view's roster (claim = the entity list)."},
                               "entity": {"type": "string", "description": "A slug or a view's cluster id (d:<table> · a:<gate> · fe·<x>) — its members under `model` (default claim)."},
                               "piece": {"type": "string", "description": "file#fn · 'METHOD /path' · 'TASK <name>' · fe:<file>#<name> · endpoint:/schema:/model: id — its home under each model."},
                               **T.ROOT_PROP})},
]
