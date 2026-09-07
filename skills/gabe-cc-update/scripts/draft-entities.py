#!/usr/bin/env python3
"""draft-entities.py — the ENTITY-MODEL DRAFTER (Phase 4 of docs/design/entity-models/plan.md, 2026-09-06).

A PROJECTION of the committed c4-graph's `models` block into a reviewable draft: one verdict per declared entity
(FEATURE · SPLIT · MERGE · ASPECT · LAYER, with the emitter's why and its suggested edit) and every CANDIDATE feature no
entity declares — each arriving NAMED in the user's words and CLASSIFIED (the naming law, ruling 2026-09-05). It re-reads
nothing and re-derives nothing: one source, one truth — `homes.proposed` on the same block is the station's rendering of
the same verdicts, so this file is loaded by NO page (plain JSON, never a `window.*` .js). Acceptance is ONE edit —
`entities.<slug>` in `docs/site/center/center.config.json` — then `/gabe-cc-init rank` (the third lens reads this draft).

Laws: DETERMINISTIC (everything sorted; the c4 `head` sha is the only stamp; an unchanged input rewrites nothing) ·
HONEST-EMPTY ×4 (no center config · no c4-graph · unreadable c4 · no `models` block → the reason is printed, NOTHING is
written, exit 0) · REPORT-NEVER-GATE (exit 1 only on a write failure) · an all-FEATURE / no-candidate run writes a VALID
EMPTY draft so a stale one never lingers · `coverage.witnessed` + `abstained` are NON-OPTIONAL (31/29/46/29% witness
coverage must never read as "69% wrong") · never touches center.config.json · no "orphan" (R10).

usage: python3 draft-entities.py <project-root> [--out <path>] [--json] [--model proposed|derived] [--min N] [--naming <strategy>]
  --out     where the draft goes (default docs/site/center/entities.draft.json under the root)
  --json    print the full report instead of the one line
  --model   proposed (default: verdicts + candidates) · derived (every derived cluster as a row — what the code says)
  --min     minimum endpoints per candidate (default 1)
  --naming  the NAMING STRATEGY for a human run — domain · table · class · path · action · config · both (default: the project's
            `naming.default` from the map; a committed draft speaks the project default). `name_from` says which applied; every
            row keeps `names{}` (every candidate name the emitter computed); `suggested_slug` NEVER follows a strategy — it derives
            from the domain name (`slug_from`) and `slug_options{table, class}` offers the alternatives for the human to pick.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

VERDICTS = ("FEATURE", "SPLIT", "MERGE", "ASPECT", "LAYER")


def _words(seg: str) -> str:
    return re.sub(r"[-_]+", " ", str(seg or "")).strip()


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(s or "").lower()).strip("-")


def _u(s):
    return "unclaimed" if s == "__unclaimed__" else s                       # R10


def _sibling():
    """draft-workflows.py beside this file — `draft_name()` is the ONE naming rule (verb-set phrase + path noun + actions)."""
    p = Path(__file__).resolve().parent / "draft-workflows.py"
    if not p.is_file():
        return None
    spec = importlib.util.spec_from_file_location("gabe_draft_workflows", p)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _action(members: list[str], sib) -> str | None:
    """The verb-set phrase over the candidate's ENDPOINT members — `Manage dish history events — …` — via the sibling's draft_name."""
    labels = sorted(m.split(":", 1)[1] for m in members if isinstance(m, str) and m.startswith("endpoint:") and not m.startswith("endpoint:BOOT ") and not m.startswith("endpoint:TASK "))
    if not labels or sib is None:
        return None
    try:
        return sib.draft_name(labels)[0]
    except Exception:  # noqa: BLE001
        return None


def _center(root: Path) -> Path:
    return root / "docs" / "site" / "center"


def project(models: dict, head: str, model: str, min_endpoints: int, sib, naming: str | None = None) -> dict:
    """The draft — a pure projection of the block (nothing derived here; the battery pins equality with the rosters)."""
    views = models.get("views") or {}
    rosters = models.get("rosters") or {}
    nb = models.get("naming") if isinstance(models.get("naming"), dict) and (models.get("naming") or {}).get("positions") else {}
    strategy = naming if naming in (nb.get("positions") or ()) else (nb.get("default") if nb else None) or "domain"
    naming_note = (("naming: %s (%s)" % (strategy, "your --naming" if naming == strategy and naming else ("project default — " + str(nb.get("source")) if nb else "no naming block on this map — regen with the current generators; names fall back to the emitted row.name"))))
    derived_v, proposed_v, seeded_v = (views.get("derived") or {}), (views.get("proposed") or {}), (views.get("seeded") or {})
    declared, candidates = [], []
    if model == "proposed":
        for r in sorted((rosters.get("proposed") or []), key=lambda x: str(x.get("slug"))):
            declared.append({"slug": r.get("slug"), "verdict": r.get("verdict"), "why": r.get("why"), "evidence": r.get("evidence") or {},
                             **({"suggested_edit": r["suggested_edit"]} if r.get("suggested_edit") else {})})
        rows = rosters.get("candidates") or []
    else:
        rows = [r for r in (rosters.get("derived") or []) if r.get("kind") == "feature"] + [r for r in (rosters.get("derived") or []) if r.get("kind") != "feature"]
    names: dict[str, int] = {}
    for r in rows:
        if r.get("kind", "feature") == "feature" and int(r.get("endpoints") or 0) < min_endpoints:
            continue
        nms = r.get("names") if isinstance(r.get("names"), dict) else {}
        base = r.get("name") or _words(r.get("anchor_table") or r.get("id"))
        name = nms.get(strategy) if (strategy != "domain" and nms.get(strategy)) else base
        row = {"id": r.get("id"), "name": name, "name_from": (strategy if (strategy == "domain" or nms.get(strategy)) else "domain"), "names": nms, "kind": ("candidate feature" if model == "proposed" else (r.get("kind") or "feature")),
               "named_by": r.get("named_by"), "anchor_table": r.get("anchor_table"), "anchor_by": r.get("anchor_by"), "domain": r.get("domain"),
               "endpoints": r.get("endpoints"), "screens": r.get("screens"), "purity": r.get("purity"),
               "spans_entities": [_u(s) for s in (r.get("spans_entities") or sorted((r.get("claim_mix") or {}).keys()))],
               "suggested_slug": r.get("suggested_slug") or _slug(base if r.get("named_by") == "domain" else (r.get("anchor_table") or base)), "slug_from": "domain",
               "slug_options": {k: _slug(v) for k, v in (("table", nms.get("table") or (_words(r.get("anchor_table")) if r.get("anchor_table") else None)), ("class", nms.get("class"))) if v},
               "action": nms.get("action") or _action(r.get("members") or [], sib), "why": r.get("why"), "members": (r.get("members") or [])[:40], "members_more": r.get("members_more", 0)}
        row = {k: v for k, v in row.items() if v is not None}
        names[row["name"]] = names.get(row["name"], 0) + 1
        candidates.append(row)
    for row in candidates:                                                   # a collision is suffixed with the anchor table — the tier list never shows twins
        if names.get(row["name"], 0) > 1 and row.get("anchor_table"):
            row["name"] = "%s (%s)" % (row["name"], _words(row["anchor_table"]))
    candidates.sort(key=lambda x: (-(x.get("endpoints") or 0), x["name"]))
    atoms, anchored = int(derived_v.get("atoms") or 0), int(derived_v.get("anchored") or 0)
    abstained = sorted((models.get("abstain") or {}).get("derived") or [])
    return {
        "head": head, "model": model, "source": "docs/site/center/c4-graph.json#models (a projection — nothing re-derived)",
        "naming": {"strategy": strategy, "source": ("your --naming" if naming == strategy and naming else (nb.get("source") if nb else "none")), "note": naming_note,
                   **({"config_error": nb.get("config_error")} if nb and nb.get("config_error") else {}), **({"unused_words": nb.get("unused_words")} if nb and nb.get("unused_words") else {})},
        "rule": models.get("rule"),
        "declared": declared,
        "candidates": candidates,
        "abstained": {"count": len(abstained), "pieces": abstained[:40], "more": max(0, len(abstained) - 40),
                      "note": "atoms no witness reaches — they KEEP their claim; never a candidate"},
        "coverage": {"atoms": atoms, "anchored": anchored, "witnessed": (round(anchored / atoms, 3) if atoms else None), "abstained": int(derived_v.get("abstained") or 0),
                     "purity": derived_v.get("purity"), "features": derived_v.get("features"), "aspects": derived_v.get("aspects"), "layers": derived_v.get("layers"),
                     "seeded_moved": seeded_v.get("moved"), "seeded_held": seeded_v.get("held"), "verdicts": proposed_v.get("verdicts"),
                     "note": "witnessed = the share of request atoms a table anchors; the rest ABSTAIN — an unwitnessed atom is not a wrong one"},
        "accept": "add entities.<slug> (code.* claims for its files, models for its tables) to docs/site/center/center.config.json, then /gabe-cc-init rank — the next regen and draft drop it",
        "law": "claim is the registry and the join key; this draft is a projection of the proposed view — nothing here re-homes anything",
    }


def render(draft: dict) -> str:
    return json.dumps(draft, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="draft entity proposals from the committed c4-graph's models block")
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--out", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--model", choices=("proposed", "derived"), default="proposed")
    ap.add_argument("--min", type=int, default=1)
    ap.add_argument("--naming", choices=("domain", "table", "class", "path", "action", "config", "both"), default=None)
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    center = _center(root)
    if not (center / "center.config.json").is_file():
        print("draft-entities: no center (docs/site/center/center.config.json absent) — nothing drafted")
        return 0
    c4p = center / "c4-graph.json"
    if not c4p.is_file():
        print("draft-entities: no c4-graph.json yet — the center regen builds the graph; nothing drafted")
        return 0
    try:
        c4 = json.loads(c4p.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"draft-entities: c4-graph.json unreadable ({e.__class__.__name__}) — nothing drafted")
        return 0
    models = c4.get("models")
    if not isinstance(models, dict) or not models.get("present"):
        st = (c4.get("stats") or {}).get("models") or {}
        why = ("the emitter ran and said: %s" % st.get("reason")) if st.get("present") is False else "no models block on this map — regen with the current generators (entity models, 2026-09-06)"
        print(f"draft-entities: {why}; nothing drafted")
        return 0
    if a.model == "proposed" and not ((models.get("views") or {}).get("proposed") or {}).get("present"):
        print(f"draft-entities: the proposed view is absent — {((models.get('views') or {}).get('proposed') or {}).get('reason') or 'no reason recorded'}; nothing drafted")
        return 0
    draft = project(models, str(c4.get("head") or ""), a.model, max(1, a.min), _sibling(), naming=a.naming)
    out = Path(a.out).resolve() if a.out else center / "entities.draft.json"
    text = render(draft)
    try:
        changed = not (out.is_file() and out.read_text(encoding="utf-8") == text)
        if changed:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text, encoding="utf-8")
    except OSError as e:
        print(f"draft-entities: write failed at {out} ({e})")
        return 1
    rep = {**draft, "out": str(out), "written": changed}
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=1, sort_keys=True))
    else:
        cov = draft["coverage"]
        tally = " · ".join(f"{k} {v}" for k, v in (cov.get("verdicts") or {}).items() if v) or "no verdicts"
        print(f"draft-entities ({a.model}): {len(draft['declared'])} declared verdict(s) [{tally}] · {len(draft['candidates'])} candidate(s) · "
              f"witnessed {cov['anchored']}/{cov['atoms']} atoms · {draft['abstained']['count']} abstained · {draft['naming']['note']} · head {draft['head'] or '?'} → {out}{'' if changed else ' (unchanged)'}")
        for d in draft["declared"]:
            if d.get("verdict") and d["verdict"] != "FEATURE":
                print(f"  {d['verdict']:8} {d['slug']}  — {d.get('why') or ''}")
        for c in draft["candidates"]:
            print(f"  CANDIDATE {c['name']}  (named by {c.get('name_from') or c.get('named_by') or 'table'}; slug {c.get('suggested_slug')}" + (f", or {' / '.join(c['slug_options'].values())}" if c.get('slug_options') else "") + f"; {c.get('endpoints') or 0} endpoint(s))"
                  + (f"  — {c['action']}" if c.get("action") else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
