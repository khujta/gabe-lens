#!/usr/bin/env python3
"""draft-workflows.py — the curate-workflows DRAFTER (`/gabe-cc-update curate-workflows`).

Journey CREATION for the one journey kind that needs a human. Backend, test and commit journeys
derive themselves from the map; the curated user workflows (docs/site/center/workflows.js) did not —
a new project's workflows tab stayed empty until someone remembered to write the file, and the
example drifted from the project it describes. Measured 2026-09-04 on gustify: 39 of 81 endpoints in
no workflow, falling into 14 natural entity·screen clusters.

This script PROPOSES, never curates. From the committed c4-graph.json it takes every endpoint no
curated workflow names, clusters them by (entity · the SCREEN that drives them — the route above the
fetching piece), orders each cluster's steps read→write, SUGGESTS a level, and writes them as drafts
to docs/site/center/workflows.draft.js (window.GABE_WORKFLOWS_DRAFT). The Universe station lists the
drafts in the workflows tab under "drafts — review & name", walkable like any workflow. The human
renames, reorders, sets the level and moves an accepted entry into workflows.js; the next run drops
it, because it is now covered. Regenerated wholesale — never hand-edit the draft file.

Laws: DETERMINISTIC (everything sorted; no wallclock — the c4 `head` sha is the only provenance
stamp; an unchanged input re-writes nothing) · HONEST-EMPTY (no center config / no c4-graph → the
reason is printed, NOTHING is written, exit 0) · REPORT-NEVER-GATE (exit 1 only on a write failure) ·
NO PROJECT NAME-LISTS (infra endpoints are skipped by idiom: BOOT events, TASK roots (a worker entrypoint dispatched by name is not a user workflow), and paths whose first
segment starts with "_"; an endpoint with no screen is REPORTED as unreached, never drafted).

usage: python3 draft-workflows.py <project-root> [--out <path>] [--json] [--min N]
  --out   where the draft file goes (default docs/site/center/workflows.draft.js under the root)
  --json  print the full report (drafts · uncovered · unreached · skipped) instead of the one line
  --min   minimum endpoints per cluster to draft (default 1 — a one-step workflow is legitimate)
NAMING (operator 2026-09-05): a draft is not a cluster key waiting for a name — it arrives NAMED in the
user's words (`Manage cooking sessions — cancel · readiness · photos`, see draft_name) and LEVELED into
its tier, exactly as a curated entry would; the station places it in that section with a DRAFT chip.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

LABEL_RX = re.compile(r'"((?:GET|POST|PUT|PATCH|DELETE|BOOT|TASK) [^"]+)"')
NAME_RX = re.compile(r'name\s*:\s*"([^"]*)"')
SCREENISH_RX = re.compile(r"(Page|Screen|View)$")
CFG_RX = re.compile(r"(^|/)(router|routes)\.[jt]sx?$")
SCREEN_DIR_RX = re.compile(r"/(pages|features)/")
VERB_ORDER = {"GET": 0, "POST": 1, "PUT": 2, "PATCH": 3, "DELETE": 4}
LEVEL_NAME = {1: "Orientation", 2: "Core", 3: "Specialized"}
PARAM_RX = re.compile(r"^\{.*\}$|^\$\{.*\}$|^:")


def _words(seg: str) -> str:
    """`resolve-batch` → `resolve batch`, `frequent_ingredients` → `frequent ingredients`."""
    return re.sub(r"[-_]+", " ", seg).strip()


def draft_name(steps: list[str]) -> tuple[str, str, list[str]]:
    """The draft's NAME in the user's words — the same logic as the legend reference's definitions
    column (operator 2026-09-05: "a screen you navigate to", "a piece of UI that draws something"):
    what the person DOES, not the machine's cluster key. Deterministic from the endpoint labels alone:
      phrase  ← the verb set: GET only → "Look at" · DELETE only → "Remove" · GET/POST → "Add" ·
                GET/PUT/PATCH → "Edit" · anything mixed → "Manage"
      noun    ← the first path segment, plus the second when EVERY path shares it and it reads as a
                collection (plural: `sessions`, `items`; never `status`/`active`) — `cooking sessions`
      actions ← every other non-parameter segment, in path order, deduped, capped at 4 — `cancel ·
                readiness · photos`; appended after an em dash so the name stays a sentence
    Returns (name, noun, actions). `Manage cooking sessions — cancel · readiness · photos` reads in
    the tier list beside the curated `Cook a recipe — the cooking session`; the human may still rename."""
    verbs: set[str] = set()
    firsts: list[str] = []
    seconds: list[str] = []
    actions: list[str] = []
    for lab in steps:
        verb, _, path = lab.partition(" ")
        verbs.add(verb)
        segs = [s for s in path.strip("/").split("/") if s]
        if not segs:
            continue
        firsts.append(segs[0])
        rest = [s for s in segs[1:] if not PARAM_RX.match(s)]
        seconds.append(rest[0] if rest else "")
        for s in rest:
            if s not in actions:
                actions.append(s)
    first = max(sorted(set(firsts)), key=firsts.count) if firsts else "app"
    noun = _words(first)
    sec = seconds[0] if seconds else ""
    if sec and all(s == sec for s in seconds) and sec.endswith("s") and len(sec) > 3 and sec != "status":
        noun = f"{noun} {_words(sec)}"
        actions = [a for a in actions if a != sec]
    if verbs <= {"GET"}:
        phrase = "Look at"
    elif verbs == {"DELETE"}:
        phrase = "Remove"
    elif verbs <= {"GET", "POST"}:
        phrase = "Add"
    elif verbs <= {"GET", "PUT", "PATCH"}:
        phrase = "Edit"
    else:
        phrase = "Manage"
    if noun.split()[0].lower() == phrase.lower():
        # the domain word IS the verb (onyx's /manage/* — "Manage manage — …", 9 of 65 rows, ruling 2026-09-06): the noun becomes
        # the most frequent second segment (ties alphabetical) and leaves the actions; with no second segment the phrase stands alone
        sec2 = [s for s in seconds if s]
        if sec2:
            best = max(sorted(set(sec2)), key=sec2.count)
            noun = _words(best)
            actions = [a for a in actions if a != best]
        else:
            noun = ""
    acts = [_words(a) for a in actions[:4]] + (["…"] if len(actions) > 4 else [])
    name = f"{phrase} {noun}".rstrip() + (f" — {' · '.join(acts)}" if acts else "")
    return name, noun, acts


def _dedupe_names(drafts: list[dict]) -> None:
    """Two clusters may read the same — `Look at cooking — active` from two screens. Suffix BOTH
    with their screen so the tier list never shows twins (deterministic; only on collision)."""
    seen: dict[str, int] = {}
    for d in drafts:
        seen[d["name"]] = seen.get(d["name"], 0) + 1
    for d in drafts:
        if seen[d["name"]] > 1:
            d["name"] = f"{d['name']} (from {d['cluster']['screen']})"


def _center(root: Path) -> Path:
    return root / "docs" / "site" / "center"


def curated_labels(center: Path) -> tuple[set[str], int]:
    """The step labels every curated workflow names + the workflow count. Tolerant of the JS
    literal (unquoted keys, comments, `{param}` inside labels): whole-file label extraction,
    never a block parse — a `{recipe_id}` inside a string must not split an entry."""
    p = center / "workflows.js"
    if not p.is_file():
        return set(), 0
    s = p.read_text(encoding="utf-8")
    s = re.sub(r"/\*[\s\S]*?\*/", "", s)
    s = re.sub(r"(?m)^\s*//[^\n]*", "", s)
    return set(LABEL_RX.findall(s)), len(NAME_RX.findall(s))


def analyse(c4: dict, covered: set[str], min_size: int) -> dict:
    l2 = c4.get("l2") or {}
    model_slug: dict[str, str] = {}
    endpoints: list[dict] = []
    for slug, blk in l2.items():
        for n in blk.get("nodes") or []:
            if n.get("kind") == "model" and n.get("label"):
                model_slug[n["label"]] = slug
            elif n.get("kind") == "endpoint":
                endpoints.append(n)

    fe = c4.get("fe") or {}
    pieces: list[dict] = fe.get("pieces") or []
    idx = {p["id"]: i for i, p in enumerate(pieces)}
    by_screen: dict[str, str] = {}
    for p in pieces:                              # a file may now hold several fetching pieces (D3): the FIRST
        if p.get("screen"):                       # (principal-ranked) is the fallback for a bridge with no export
            by_screen.setdefault(p["screen"], p["id"])
    parents: dict[str, list[str]] = {}          # piece → the pieces that render / use / import it
    for e in fe.get("edges") or []:
        if len(e) < 3 or e[2] not in ("renders", "uses-hook", "imports"):
            continue
        a, b = e[0], e[1]
        if 0 <= a < len(pieces) and 0 <= b < len(pieces):
            parents.setdefault(pieces[b]["id"], []).append(pieces[a]["id"])

    def route_of(start: list[str]) -> str | None:
        """The nearest ROUTE above these pieces (≤3 hops up renders/uses/imports). Screen-like
        routes win (*Page/Screen/View, under /pages/ or /features/); router config files are
        skipped — idiom rules only, never a project name-list. None when no route is in reach."""
        seen = set(start)
        frontier = sorted(start)
        best = None
        for _ in range(4):
            nxt: list[str] = []
            for pid in frontier:
                p = pieces[idx[pid]] if pid in idx else None
                if p and p.get("kind") == "route" and not CFG_RX.search(p.get("file") or ""):
                    if SCREENISH_RX.search(p.get("name") or "") or SCREEN_DIR_RX.search(p.get("file") or ""):
                        return p["name"]
                    if best is None:
                        best = p["name"]
                for q in sorted(parents.get(pid, [])):
                    if q not in seen:
                        seen.add(q)
                        nxt.append(q)
            frontier = sorted(nxt)
            if not frontier:
                break
        return best

    bridges: dict[str, set[tuple[str, str | None]]] = {}
    for e in c4.get("cross_edges") or []:
        if e.get("kind") == "bridge" and e.get("to") and e.get("from"):
            bridges.setdefault(e["to"], set()).add((e["from"], e.get("export")))   # (file node, the export piece — D3)

    reached: list[dict] = []
    unreached: list[dict] = []
    skipped: list[str] = []
    covered_n = 0
    for n in sorted(endpoints, key=lambda n: n.get("label") or ""):
        label = n.get("label") or ""
        verb, _, path = label.partition(" ")
        first = path.strip("/").split("/")[0] if path else ""
        if verb in ("BOOT", "TASK") or first.startswith("_"):   # a worker task (dispatched by name) is not a user workflow — skipped like BOOT (legend pass 2026-09-06)
            skipped.append(label)
            continue
        if label in covered:
            covered_n += 1
            continue
        ops = (n.get("access") or {}).get("ops") or []
        writes = sorted({o["model"] for o in ops if o.get("rw") == "w" and o.get("model")})
        reads = sorted({o["model"] for o in ops if o.get("rw") == "r" and o.get("model")})
        screens = sorted({(x if (x and x in idx) else by_screen.get(w)) for w, x in bridges.get(n.get("id", ""), ())} - {None})   # the export's piece first, the file's principal as the floor
        row = {"label": label, "verb": verb, "path": path, "entity": n.get("slug") or "?",
               "writes": writes, "reads": reads,
               "screens": [pieces[idx[s]]["name"] for s in screens],
               "route": route_of(screens) if screens else None}
        (reached if screens else unreached).append(row)

    clusters: dict[tuple[str, str], list[dict]] = {}
    for r in reached:
        key = (r["entity"], r["route"] or r["screens"][0])
        clusters.setdefault(key, []).append(r)

    drafts: list[dict] = []
    for (ent, scr), rs in sorted(clusters.items()):
        if len(rs) < min_size:
            continue
        rs = sorted(rs, key=lambda r: (VERB_ORDER.get(r["verb"], 9), r["path"]))
        w_models = sorted({m for r in rs for m in r["writes"]})
        r_models = sorted({m for r in rs for m in r["reads"]})
        span = {ent} | {model_slug[m] for r in rs for m in r["writes"] + r["reads"] if m in model_slug}
        level = 1 if not w_models else (3 if len(span) > 1 else 2)
        verbs = {r["verb"] for r in rs}
        why = ("no writes" if not w_models else "single-entity writes" if level == 2 else "cross-entity writes")
        steps = [r["label"] for r in rs]
        name, noun, acts = draft_name(steps)
        # the NOTE is the definition column, in the user's words: what happens, from where, touching what
        touch = ((f"reads {', '.join(r_models[:4])}{'…' if len(r_models) > 4 else ''}" if r_models else "")
                 + (" and " if r_models and w_models else "")
                 + (f"writes {', '.join(w_models[:4])}{'…' if len(w_models) > 4 else ''}" if w_models else ""))
        drafts.append({
            "name": name,
            "level": level,
            "draft": True,
            "note": (f"{name.split(' — ')[0].lower()} from the {scr} screen — the app {touch or 'touches no model'}; "
                     f"{len(rs)} endpoint{'s' if len(rs) != 1 else ''}, {why} → {LEVEL_NAME.get(level, 'other')} (level {level}). "
                     f"A DRAFT: accept it by moving this entry into workflows.js (rename freely)."),
            "steps": steps,
            "cluster": {"entity": ent, "screen": scr},
            "why": {"writes": len(w_models), "reads": len(r_models), "span": sorted(span)},
        })
    _dedupe_names(drafts)

    return {"drafts": drafts, "endpoints": len(endpoints), "covered": covered_n,
            "uncovered": len(reached) + len(unreached),
            "unreached": [{"label": r["label"], "entity": r["entity"], "writes": len(r["writes"])} for r in unreached],
            "skipped_infra": skipped}


def render(drafts: list[dict], head: str) -> str:
    body = json.dumps(drafts, ensure_ascii=False, indent=2)
    return ("// DRAFT user workflows — machine-proposed by `/gabe-cc-update curate-workflows` (draft-workflows.py)\n"
            f"// from the committed c4-graph (head {head or '?'}): every endpoint no curated workflow names, clustered by\n"
            "// entity · the screen that drives it, steps ordered read→write, NAMED in the user's words (what the person\n"
            "// does — the legend reference's definitions logic) and LEVELED into its tier (Orientation · Core ·\n"
            "// Specialized), so each draft already sits in its section of the workflows tab wearing the DRAFT chip.\n"
            "// Accept one by moving its entry into workflows.js (rename freely) — the next run drops it.\n"
            "// Regenerated wholesale; never hand-edit. Absent or empty → the station shows no drafts.\n"
            f"window.GABE_WORKFLOWS_DRAFT = {body};\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="draft user-workflow candidates from the committed c4-graph")
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--out", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--min", type=int, default=1)
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    center = _center(root)
    if not (center / "center.config.json").is_file():
        print("curate-workflows: no center (docs/site/center/center.config.json absent) — nothing drafted")
        return 0
    c4p = center / "c4-graph.json"
    if not c4p.is_file():
        print("curate-workflows: no c4-graph.json yet — the center regen builds the graph; nothing drafted")
        return 0
    try:
        c4 = json.loads(c4p.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"curate-workflows: c4-graph.json unreadable ({e.__class__.__name__}) — nothing drafted")
        return 0
    covered, n_wf = curated_labels(center)
    rep = analyse(c4, covered, max(1, a.min))
    rep["workflows"] = n_wf
    out = Path(a.out).resolve() if a.out else center / "workflows.draft.js"
    text = render(rep["drafts"], str(c4.get("head") or ""))
    try:
        changed = not (out.is_file() and out.read_text(encoding="utf-8") == text)
        if changed:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text, encoding="utf-8")
    except OSError as e:
        print(f"curate-workflows: write failed at {out} ({e})")
        return 1
    rep["out"] = str(out)
    rep["written"] = changed
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        d = rep["drafts"]
        print(f"curate-workflows: {len(d)} draft(s) from {rep['uncovered']} uncovered endpoint(s) of {rep['endpoints']} "
              f"({rep['covered']} covered by {n_wf} workflow(s) · {len(rep['skipped_infra'])} infra skipped · "
              f"{len(rep['unreached'])} unreached — no screen) → {out}{'' if changed else ' (unchanged)'}")
        for x in d:
            print(f"  L{x['level']}  {x['name']}  ← {' · '.join(x['steps'][:4])}{' …' if len(x['steps']) > 4 else ''}")
        if rep["unreached"]:
            print(f"  unreached (no screen calls them — a bridge gap or a dead endpoint): "
                  + ", ".join(u["label"] for u in rep["unreached"][:8]) + (" …" if len(rep["unreached"]) > 8 else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
