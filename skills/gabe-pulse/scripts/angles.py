#!/usr/bin/env python3
"""ANGLE signals — which satellite would find something, right now.

    python3 angles.py [<repo-root>] [--one-line] [--json] [--why]

The problem this exists for, in the operator's words: *"they will get buried by
my lack of awareness while I use only the router-dispatched commands."* Fifteen
of the suite's twenty-eight skills have nothing that fires them. Adding
"consider /gabe-roast" to every beat would fix nothing — a line that prints
every time carries no information about THIS run and the eye learns to skip it.

So a signal only earns its line when the repo state says the satellite would
find something. Not "consider a roast" but "6 phases done, no adversarial pass
since this plan started". Every signal below is computed from committed state,
never inferred, and a signal whose source is missing reports **unavailable with
the reason** rather than staying quiet — a silent signal is indistinguishable
from a clean one.

`--one-line` prints AT MOST ONE row, formatted for a beat's terminal report:

    PULSE: 6 phases done, no adversarial pass on this plan → /gabe-roast Sweeper "<subject>"

and prints NOTHING when there is nothing. There is no "all clear" line: a beat
that ends with a reassurance every run has re-invented the noise this avoids.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# How much has to accumulate before a signal is worth a line. Deliberately
# coarse: a threshold tuned to fire often is a threshold that will be ignored.
THRESHOLDS = {
    # S8 — owed captures worth interrupting for. Below this the census is
    # merely young; above it, evidence debt is accumulating unattended.
    "evidence_owed": 3,
    "phases_before_roast": 3,
    "commits_before_health": 25,
    "entity_files_touched": 3,
    "prism_layers": 2,
    "prism_actors": 3,
    "scope_outside": 1,
    # S16 — screen-reachable endpoints in no curated workflow; below this a curate run
    # proposes noise, at it the workflows tab is lying by omission. cluster_min mirrors the
    # drafter's --min default so the "proposable" count equals what a run writes.
    "workflow_uncovered": 3,
    "workflow_cluster_min": 1,
    # S18 — candidate entities in entities.draft.json worth a ruling; one candidate is a curiosity,
    # two are a pattern the registry is missing. A non-FEATURE verdict fires on its own.
    "entity_candidates": 2,
    # S14 — a codebase-map generator arm whose ACTIVE missed edges have this many
    # distinct entries is diverging enough to be worth a generator look; horizon =
    # commits since an edge last recurred beyond which it reads COLD (self-silencing).
    "map_delta_active": 3,
    "map_delta_horizon": 40,
}

# Offered twice for the same evidence and not taken ⇒ silent until the evidence
# changes. Without this a true signal becomes wallpaper, which is the same
# failure as a false one.
DECAY_AFTER = 2


def sh(args: list[str], cwd: Path) -> str:
    try:
        p = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, timeout=30)
        return p.stdout if p.returncode == 0 else ""
    except Exception:                                        # noqa: BLE001
        return ""


def load_plan(root: Path) -> dict | None:
    p = root / ".kdbp" / "PLAN.json"
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None




def done_phases(plan: dict) -> list[dict]:
    return [ph for ph in plan.get("phases", [])
            if (ph.get("cells") or {}).get("exec") == "done"]


def commits_since_grep(root: Path, pattern: str, limit: int = 400) -> int | None:
    """How many commits since the last one mentioning `pattern`.

    None when the repo has no commits at all — different from "none mentioned",
    which is a real answer and returns the full count.
    """
    log = sh(["git", "log", f"-{limit}", "--pretty=%H%x1f%s%x1f%b%x1e"], root)
    if not log.strip():
        return None
    entries = [e for e in log.split("\x1e") if e.strip()]
    for i, e in enumerate(entries):
        if re.search(pattern, e, re.I):
            return i
    return len(entries)


# --------------------------------------------------------------------------- #
# The signals. Each returns (fires: bool, evidence: str, command: str) or an
# Unavailable with the reason and what would make it computable.
# --------------------------------------------------------------------------- #

class Unavailable(str):
    """A signal that could not be computed, carrying WHY."""


def s1_roast(root: Path, plan: dict | None, cfg: dict | None):
    if plan is None:
        return Unavailable("no .kdbp/PLAN.json — the phase record is the trigger's source")
    done = done_phases(plan)
    if len(done) < THRESHOLDS["phases_before_roast"]:
        return None
    # Reset only on a roast RECORD, never on incidental prose: "adversarial" in
    # the old pattern matched a review commit's "4-lens adversarial pass" line
    # (measured on a copy of the real repo, 2026-08-07) and silenced the signal
    # for a whole cycle. A review is not a roast.
    since = commits_since_grep(root, r"gabe-roast|\broast(ed|s)?\b")
    if since is None:
        return Unavailable("no commit history to measure against")
    if since < len(done):
        return None
    # The command must be pasteable VERBATIM: the old form clipped the goal
    # mid-word inside the quotes AND omitted the perspective /gabe-roast
    # requires — pasted as-is it BLOCKED (observed, 7-minute round trip).
    # Sweeper is the archetype for accumulated-estate gaps — the perspective
    # the operator picked unprompted for exactly this roast shape.
    goal = (plan.get("goal") or "this plan").strip()
    if len(goal) > 60:
        goal = (goal[:60].rsplit(" ", 1)[0] or goal[:60]) + "…"
    return (f"{len(done)} phases done, no adversarial pass on this plan",
            f'/gabe-roast Sweeper "{goal}"')


def s2_health(root: Path, plan: dict | None, cfg: dict | None):
    # Reset only on a scan RECORD. The old pattern's loose words ("churn",
    # "god file") collided with ordinary commit prose — measured on a copy of
    # the real repo (2026-08-07): "archmap.json stops churning on every regen"
    # re-zeroed the counter and kept S2 silent for an entire 100+-commit cycle
    # while no scan had run.
    since = commits_since_grep(root, r"gabe-health|structural scan|health scan")
    if since is None:
        return Unavailable("no commit history to measure against")
    if since < THRESHOLDS["commits_before_health"]:
        return None
    return (f"{since} commits since the last structural scan",
            "/gabe-health")


def s3_myopic(root: Path, plan: dict | None, cfg: dict | None):
    if plan is None:
        return Unavailable("no .kdbp/PLAN.json — proof_type lives in the phase record")
    owed = [ph for ph in plan.get("phases", [])
            if (ph.get("proof_type") in ("journey", "visual"))
            and (ph.get("cells") or {}).get("review") == "done"
            and not ph.get("proof")]
    if not owed:
        return None
    names = ", ".join(str(ph.get("id", "?")) for ph in owed[:3])
    return (f"{len(owed)} reviewed phase(s) owe journey/visual proof and carry none ({names})",
            "/gabe-myopic")


def s4_docsite(root: Path, plan: dict | None, cfg: dict | None):
    checker = root / "scripts" / "checkers" / "docsite-staleness.sh"
    if not checker.is_file():
        return Unavailable("no scripts/checkers/docsite-staleness.sh in this repo")
    try:
        p = subprocess.run(["bash", str(checker), str(root)],
                           capture_output=True, text=True, timeout=60)
    except Exception as exc:                                  # noqa: BLE001
        return Unavailable(f"staleness checker could not run ({exc})")
    if p.returncode == 0:
        return None
    n = len([l for l in p.stdout.splitlines() if l.startswith("docsite: ")])
    return (f"{n} doc page(s) older than the markdown they were rendered from",
            "/gabe-docsite")


# The diff source and the entity resolver are SHARED with write-inflight.py so the
# board and the pulse line can never name different entities for the same tree
# (ruling 2026-08-07). work_scope.changed_files also excludes the beat tail's own
# inflight.{json,js} — without that, part-2 of the tail rewrites them one line
# before part-3 runs this file, and S6/S7 go permanently silent (the very bug the
# walk-back was added to fix, reintroduced by the tail's own ordering).
import os as _os  # noqa: E402
import sys as _sys  # noqa: E402
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))  # so `import work_scope` works even when angles.py is loaded via importlib (the batteries do this), not just run as a script
import work_scope  # noqa: E402  (same dir; installed alongside under ~/.claude/skills/gabe-pulse/scripts)
import entity_shape  # noqa: E402  (same dir; the URL-domain ↔ entity-model cross-tab, computed fresh)
import fetch_bridge  # noqa: E402  (same dir; the web→API bridge drift, read from the committed c4-graph)


def _current_phase(plan: dict) -> dict | None:
    cur = str(plan.get("current_phase", ""))
    return next((p for p in plan.get("phases", []) or [] if str(p.get("id")) == cur), None)


def s5_scope(root: Path, plan: dict | None, cfg: dict | None):
    """Scope drift — files changed outside the current phase's declared scope.

    Computable since 2026-08-07: `/gabe-plan` mirrors the phase's Scope bullet to
    PLAN.json `phases[].scope`. A phase with no scope key still reports unavailable
    (honestly — nothing to drift from), never a `types` proxy guess.
    """
    if plan is None:
        return Unavailable("no .kdbp/PLAN.json — the phase record is the scope source")
    ph = _current_phase(plan)
    if ph is None:
        return Unavailable("current phase not found in PLAN.json phases")
    scope = ph.get("scope")
    if not scope:
        return Unavailable("current phase declares no `scope:` field — add one at plan time to unlock scope-drift")
    changed, _src = work_scope.changed_files(root)
    if not changed:
        return None
    outside = [f for f in changed if not any(work_scope.matches(f, p) for p in scope)]
    if len(outside) < THRESHOLDS["scope_outside"]:
        return None
    return (f"{len(outside)} changed file(s) outside phase {ph.get('id')}'s declared scope",
            "/gabe-scope-change")


def s6_entity(root: Path, plan: dict | None, cfg: dict | None):
    if cfg is None:
        return Unavailable("no center config — entity code maps are the trigger's source")
    globs = work_scope.entity_code_globs(cfg)
    if not globs:
        return Unavailable("center config declares no entity code maps yet")
    changed, _src = work_scope.changed_files(root)
    if not changed:
        return None
    touched = work_scope.touched_entities(cfg, changed)
    if not touched:
        return None
    best = max(touched, key=lambda t: t["files"])
    if best["files"] < THRESHOLDS["entity_files_touched"]:
        return None
    return (f"{best['files']} changed file(s) belong to the {best['slug']} code map",
            f"/gabe-cc-entity {best['slug']}")


def s7_prism(root: Path, plan: dict | None, cfg: dict | None):
    if cfg is None:
        return Unavailable("no center config — the layer map is the trigger's source")
    if not work_scope.layer_globs(cfg):
        return Unavailable("center config declares no layered code map yet")
    changed, _src = work_scope.changed_files(root)
    if not changed:
        return None
    touched = work_scope.touched_layers(cfg, changed)
    if len(touched) < THRESHOLDS["prism_layers"] or len(changed) < THRESHOLDS["prism_actors"]:
        return None
    return (f"the diff spans {len(touched)} layers ({', '.join(touched[:4])}) "
            f"across {len(changed)} files",
            "/gabe-imagine")


def s8_evidence(root: Path, plan: dict | None, cfg: dict | None):
    """Workflow-census capture debt — the standing reminder.

    /gabe-review DETECTS drift on the diff that caused it; this angle exists for
    what review can only DEFER: an owed capture needs a green e2e run plus
    curation, so it survives the reviewing session and then needs something to
    keep surfacing it. Reads the committed census only — no run, no parse."""
    wf_dir = root / "docs" / "site" / "center" / "workflows"
    if not wf_dir.is_dir():
        return Unavailable("no workflow census yet — /gabe-cc-update authors it")
    owed, drift, ents = 0, 0, 0
    for f in sorted(wf_dir.glob("*.json")):
        try:
            census = json.loads(f.read_text())
        except Exception:
            continue
        ents += 1
        for st in (census.get("states") or {}).values():
            if st.get("grp"):
                continue
            if not st.get("shot"):
                owed += 1
            cap = str(st.get("cap") or "")
            if "owed" in cap:
                drift += 1
    if not ents:
        return Unavailable("workflow census directory is empty")
    if owed < THRESHOLDS["evidence_owed"]:
        return None
    named = f"{drift} named capture-owed" if drift else "none named"
    return (f"{owed} workflow step(s) across {ents} entity census(es) have no "
            f"capture ({named})",
            "/gabe-cc-update curate")


def _emitted_aspects(root: Path) -> tuple[list[str], str | None]:
    """ARM B of S9 (entity models Phase 3, 2026-09-06): the aspects the EMITTER measured, read from the committed c4-graph's
    `models` block — the derived view's gate-fan-in rows (a gate on ≥3 URL domains' endpoints, the detector that measured
    23/24 · 34/41 on the twins) and the proposed view's ASPECT verdicts (each with its why). Returns (phrases, state) —
    state None when present, else the word to print INSIDE the line: not_emitted (no block — regen to know) or the emitter's reason."""
    c4 = fetch_bridge._center(root) / "c4-graph.json"
    if not c4.exists():
        return [], "not_emitted — no c4-graph.json yet (regen to know)"
    try:
        g = json.loads(c4.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return [], f"c4-graph.json unreadable ({e.__class__.__name__})"
    m = g.get("models")
    if not isinstance(m, dict):
        st = (g.get("stats") or {}).get("models")
        if isinstance(st, dict) and st.get("present") is False:
            return [], f"absent — {st.get('reason') or 'the emitter recorded no reason'}"
        return [], "not_emitted — no models block on this map (regen with the current generators to know)"
    views = m.get("views") or {}
    if not (views.get("derived") or {}).get("present"):
        return [], f"absent — {(views.get('derived') or {}).get('reason') or 'no derived view'}"
    out = []
    for r in (m.get("rosters") or {}).get("derived") or []:
        if r.get("kind") == "aspect" and r.get("detector") == "gate-fan-in":
            out.append(f"{r.get('name') or r.get('id')} (gate fan-in: {str((r.get('members') or [''])[0]).split('#')[-1]} spans {r.get('domains')} domains)")
    for r in (m.get("rosters") or {}).get("proposed") or []:
        if r.get("verdict") == "ASPECT":
            out.append(f"{r.get('slug')} is an aspect ({r.get('why') or 'proposed ASPECT'})")
    return out, None


def s9_entity_shape(root: Path, plan: dict | None, cfg: dict | None):
    """Entity-shape drift — TWO ARMS (entity models Phase 3, 2026-09-06).

    ARM A (fresh, unchanged computation): a DETACHED domain — a URL surface no domain entity
    owns, recomputed from the committed archmap by `entity_shape.py` every beat; nothing stored.
    ARM B (emitted): the ASPECTS the emitter MEASURED — gate fan-in rows + proposed ASPECT verdicts
    read from the committed c4-graph's `models` block, exactly as fresh as that regen and SAID
    when the block is missing (`aspects: not_emitted — regen to know`) — a half-signal never reads
    clean. The URL co-claim aspect phrase of the old single arm is RETIRED from the line (measured:
    gate fan-in is the detector; screen co-fetch and URL co-claim are not) — `entity_shape.py`'s
    aspect half still feeds review's diff classification (its hazard comment says why).

    The STANDING reminder: /gabe-review catches a NEW route on the diff that caused the drift;
    this angle keeps an already-standing detached domain / aspect visible every beat."""
    if cfg is None:
        return Unavailable("no center config — the entity model is the trigger's source")
    try:
        endpoints, umap = entity_shape.load_project(root)
    except FileNotFoundError:
        return Unavailable("no archmap yet — the center regen builds it")
    shape = entity_shape.entity_shape(endpoints, umap)
    detached = shape["orphans"]                                   # the JSON key stays (three callers read it); the WORD is detached (R10)
    aspects, aspect_state = _emitted_aspects(root)
    if not detached and not aspects:
        return None
    parts = []
    if detached:
        names = ", ".join("/" + o["domain"] for o in detached[:3])
        more = f" +{len(detached) - 3}" if len(detached) > 3 else ""
        parts.append(f"{len(detached)} detached domain(s) ({names}{more})")
    if aspects:
        parts.append(f"{len(aspects)} aspect(s): " + " · ".join(aspects[:3]) + (f" +{len(aspects) - 3}" if len(aspects) > 3 else ""))
    elif aspect_state:
        parts.append(f"aspects: {aspect_state}")
    return (f"entity-shape drift — {' · '.join(parts)}", "/gabe-cc-init rank")


def s10_web_bridge(root: Path, plan: dict | None, cfg: dict | None):
    """Web→API bridge drift — a frontend apiFetch that resolves to NO declared
    endpoint (the model doesn't cover an API surface the web actually calls).

    The STANDING reminder: /gabe-review catches a NEW unmatched fetch on the diff;
    this angle keeps a persisted gap visible every beat. READS the committed
    c4-graph.json's stats.web.unmatched — the bridge extractor already NAMED every
    unresolved fetch at emit time. Nothing is recomputed (graft cannot recover a
    fetch's path and a pulse angle must not glob source), so it reads the persisted
    bridge — the same freshness contract as S9 reading the archmap."""
    if cfg is None:
        return Unavailable("no center config — the bridge lives in c4-graph.json")
    try:
        present, unmatched, _reason = fetch_bridge.load_unmatched(root)
    except FileNotFoundError:
        return Unavailable("no c4-graph.json yet — the center regen builds the bridge")
    if not present:
        return Unavailable("web arm absent (no web source / no REST idiom)")
    if len(unmatched) < fetch_bridge.WEB_UNMATCHED_MIN:
        return None
    names = ", ".join(f"{u.get('m')} {u.get('p')}" for u in unmatched[:2])
    more = f" +{len(unmatched) - 2}" if len(unmatched) > 2 else ""
    unhomed = fetch_bridge.load_unhomed(root)   # fetching files the bridge could home nowhere — counted, drawn nowhere (review 2026-09-05)
    return (f"web-bridge drift — {len(unmatched)} fetch(es) hit no declared endpoint "
            f"({names}{more})"
            + (f" · {unhomed} fetching file(s) unhomed — no screen drawn" if unhomed else ""), "/gabe-cc-init")


def s11_model_census(root: Path, plan: dict | None, cfg: dict | None):
    """Model-census drift — a TABLE class (string `__tablename__`) that lives in the
    project's model directories but no entity's config allowlist claims (operator
    ruling 2026-08-27: the config decides OWNERSHIP, never EXISTENCE — gustify lost
    ShoppingItem, SubscriptionEntitlement, SetupCompletionState, IdempotencyKey and
    AiSpendLog this way, real writes with no red wire).

    The STANDING reminder: the build already MINTS these into the `__unclaimed__`
    bucket so their access wires land; this angle keeps the unclaimed list visible
    every beat until each class is homed (or its exclusion recorded). READS the
    committed archmap's `model_census` — the census is computed at build time, so
    nothing here globs source and nothing goes stale between regens."""
    if cfg is None:
        return Unavailable("no center config — the census lives in archmap.json")
    amap_path = root / "docs" / "site" / "center" / "archmap.json"
    if not amap_path.exists():
        return Unavailable("no archmap yet — the center regen builds the census")
    try:
        amap = json.loads(amap_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return Unavailable("archmap.json unreadable")
    census = amap.get("model_census")
    if not isinstance(census, dict):
        return Unavailable("archmap predates the model census — regen the center")
    unclaimed = census.get("unclaimed") or []
    if not unclaimed:
        return None
    names = ", ".join(u.get("cls", "?") for u in unclaimed[:3])
    more = f" +{len(unclaimed) - 3}" if len(unclaimed) > 3 else ""
    return (f"model-census drift — {len(unclaimed)} table class(es) no entity claims "
            f"({names}{more})", "/gabe-cc-init")


def s12_schema_homing(root: Path, plan: dict | None, cfg: dict | None):
    """Schema-homing residue — the homing pass (a schema lives where its CONSUMER lives, not
    where its file was claimed; operator ruling 2026-08-27) leaves ONE state a human must act
    on: UNWIRED in a LIVE file (no route and no claimed function names it — a dead shape, or
    code the config does not claim: /gabe-cc-init; gustify's DishHistoryListResponse pointed at
    the unclaimed api/history.py). MULTI-CONSUMER shapes stay by ruling (the shared Blocks —
    they fold under critical) and DORMANT shapes — unwired in a file no known route reaches, a
    contract lane not yet wired (the gastify exchange) — wake themselves the build a route or
    claimed function names them; neither is an action, so neither nags; both ride the line as
    context so the lane is not forgotten. READS the committed archmap's `schema_homing`
    (computed at build time; nothing stored to go stale)."""
    if cfg is None:
        return Unavailable("no center config — homing lives in archmap.json")
    amap_path = root / "docs" / "site" / "center" / "archmap.json"
    if not amap_path.exists():
        return Unavailable("no archmap yet — the center regen runs the homing pass")
    try:
        amap = json.loads(amap_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return Unavailable("archmap.json unreadable")
    sh = amap.get("schema_homing")
    if not isinstance(sh, dict):
        return Unavailable("archmap predates schema homing — regen the center")
    amb = sh.get("ambiguous") or []
    live = [u for u in (sh.get("unwired") or []) if not u.get("dormant")]
    dormant = [u for u in (sh.get("unwired") or []) if u.get("dormant")]
    if not live:            # multi-consumer shapes STAY by ruling (shared Blocks, they fold); dormant lanes wake
        return None         # themselves — neither is an action, so neither nags; both ride the line as context
    names = ", ".join(u.get("cls", "?") for u in live[:3]) + (f" +{len(live) - 3}" if len(live) > 3 else "")
    tail = (f" · {len(amb)} multi-consumer" if amb else "") + (f" · {len(dormant)} dormant" if dormant else "")
    return (f"schema homing — {len(live)} unwired in live files ({names})" + tail, "/gabe-cc-init")


def s13_route_file_census(root: Path, plan: dict | None, cfg: dict | None):
    """Route/file-census drift — a ``.py`` sitting in a scanned code dir that no entity's
    config claims (operator ruling 2026-08-27, the model-census ruling widened to routes and
    backend files: the config decides OWNERSHIP, never EXISTENCE). A route file the api list
    omits loses its endpoints; a backend file no code list names loses its functions AND every
    call touching them (graft homes by file → entity), so ``function_insight`` never walks it
    and the ``behind`` pill counts fns the walk cannot reach.

    The STANDING reminder → ``/gabe-cc-init``: keep the unclaimed set visible every beat until
    each file is claimed (or recorded as excluded). READS the committed archmap's
    ``route_census`` / ``file_census`` (emitted non-empty-only, so their ABSENCE is full
    coverage — silent, never a false nag; the file entries carry an optional ``reach`` = min
    call-hops from a mapped handler, so the closest-to-the-request-path file leads the list).
    Nothing here globs source; nothing goes stale between regens."""
    if cfg is None:
        return Unavailable("no center config — the census lives in archmap.json")
    amap_path = root / "docs" / "site" / "center" / "archmap.json"
    if not amap_path.exists():
        return Unavailable("no archmap yet — the center regen builds the census")
    try:
        amap = json.loads(amap_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return Unavailable("archmap.json unreadable")
    # The census keys are non-empty-only (P5), so their ABSENCE alone cannot tell "full coverage"
    # from "a pre-census build wrote this archmap" — the archmap VERSION does (route/file census
    # landed at version 2). Without it, a stale archmap would read as a false all-clear — the exact
    # silent-signal failure this family exists to prevent (see the module docstring). S11/S12 lean
    # on their keys being written unconditionally; S13's keys are not, so it leans on the version.
    if amap.get("version", 1) < 2:
        return Unavailable("archmap predates the route/file census — regen the center")
    rc = amap.get("route_census") if isinstance(amap.get("route_census"), dict) else {}
    fc = amap.get("file_census") if isinstance(amap.get("file_census"), dict) else {}
    routes = rc.get("unclaimed") or []
    files = fc.get("unclaimed") or []
    if not routes and not files:            # version ≥ 2 + non-empty-only keys absent → full coverage
        return None
    # closest-to-the-request-path first: a file with a reach hop leads, nearest hop wins, then name
    files = sorted(files, key=lambda u: (u.get("reach", 10 ** 6), u.get("file", "")))
    lead = files or routes
    names = ", ".join(u.get("file", "?") for u in lead[:3]) + (f" +{len(lead) - 3}" if len(lead) > 3 else "")
    parts = []
    if routes:
        parts.append(f"{len(routes)} route file(s)")
    if files:
        parts.append(f"{len(files)} backend file(s)")
    return (f"route/file census drift — {' + '.join(parts)} no entity claims ({names})",
            "/gabe-cc-init")


def s14_map_deltas(root: Path, plan: dict | None, cfg: dict | None):
    """Map↔grep delta debt — a codebase-map generator arm whose ACTIVE missed edges
    have accumulated past the threshold, so the map keeps diverging from what grep
    finds during real dev (red/execute/review emit the divergences; /gabe-commit's
    sweep tallies them).

    The ONE accumulator-backed angle: a delta cannot be re-derived without re-running
    grep, so — unlike S8-S13 — this reads a stored tally. But the tally is a TALLY
    (dedup by edge, count = persistence), and the active/cold split is computed FRESH
    from the current commit count vs each edge's last_n, so nothing that can go stale
    is stored. A fixed or dormant arm's edges fall COLD on their own and this goes
    silent. The rollup ledger is written by /gabe-commit's sweep (11a)."""
    ledger = root / ".kdbp" / "map-deltas-rollup.jsonl"
    if not ledger.is_file():
        return Unavailable("no map-delta ledger yet — /gabe-commit's sweep builds it from red/execute/review emits")
    try:
        n_now = int((sh(["git", "rev-list", "--count", "HEAD"], root).strip() or "0"))
    except ValueError:
        n_now = 0
    # Same horizon source as /gabe-commit's sweep (MAP_DELTAS_H), so the tier the sweep
    # digests and the tier S14 nags can never disagree; default = the coarse threshold.
    horizon = int(os.environ.get("MAP_DELTAS_H", THRESHOLDS["map_delta_horizon"]))
    by_gen: dict[str, list[int]] = {}
    for line in ledger.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        # Read ONLY the v2 tally the sweep authors. A pre-11a v1 rollup is raw append lines (no
        # dedup, no last_n) — the next /gabe-commit sweep migrates it, so skip it here rather than
        # mis-count each raw line as its own active edge (the false-fire the build review caught).
        if not isinstance(o, dict) or o.get("v") != 2 or not o.get("gen"):
            continue
        if n_now - o.get("last_n", 0) < horizon:            # ACTIVE, computed fresh
            by_gen.setdefault(o["gen"], []).append(o.get("count", 1))
    hot = {g: cs for g, cs in by_gen.items() if len(cs) >= THRESHOLDS["map_delta_active"]}
    if not hot:
        return None                                         # all cold / below threshold — silent
    ranked = sorted(hot.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    top_gen, top_cs = ranked[0]
    extra = f" +{len(ranked) - 1} more arm(s)" if len(ranked) > 1 else ""
    ev = (f"map-delta debt — {top_gen}: {len(top_cs)} active missed edges "
          f"(top recurs {max(top_cs)}x){extra}")
    return (ev, "inspect .kdbp/map-deltas-rollup.jsonl → improve the arm")


def s15_fe_unknown(root: Path, plan: dict | None, cfg: dict | None):
    """Frontend classification residue — a Pascal .tsx function/class export the classifier could
    NOT prove (no JSX of its own, rendered nowhere) carries the honest kind ``fe-unknown`` instead
    of a ``module`` claim (O1, 2026-09-03; a rendered-by hit promotes it to component — O2).
    READS the committed c4-graph.json ``stats.fe.by_kind["fe-unknown"]``. Zero on the example after
    O2; any residue is a component the extractor cannot see (a delegated render nobody tags · a
    headless effect nobody mounts) → the O3 proofs, or a genuinely dead export. Report-never-gate;
    silent when the fe arm is absent."""
    if cfg is None:
        return Unavailable("no center config — the fe stats live in c4-graph.json")
    c4 = fetch_bridge._center(root) / "c4-graph.json"
    if not c4.exists():
        return Unavailable("no c4-graph.json yet — the center regen builds the fe arm")
    try:
        fe = (json.loads(c4.read_text(encoding="utf-8")).get("stats") or {}).get("fe") or {}
    except Exception as e:  # noqa: BLE001
        return Unavailable(f"c4-graph.json unreadable ({e.__class__.__name__})")
    if not fe.get("by_kind"):
        return Unavailable("fe arm absent (no web source / no typescript)")
    n = int((fe.get("by_kind") or {}).get("fe-unknown", 0) or 0)
    if n < 1:
        return None
    return (f"fe-unknown residue — {n} Pascal .tsx export(s) the classifier could not prove "
            f"(no JSX of their own, rendered nowhere)",
            "universe legend → Unknown (FE): render it somewhere, or add the O3 proof (return-null / render-call)")


def _drafter():
    """The curate-workflows drafter (gabe-cc-update/scripts/draft-workflows.py), imported by FILE —
    a hyphenated name beside another skill, resolved relative to THIS file so the repo layout
    (skills/gabe-pulse/scripts → skills/gabe-cc-update/scripts) and the install layout (~/.claude/skills)
    both work. None when the script is absent (a partial install) — S16 goes honest-empty, never guesses."""
    p = Path(__file__).resolve().parents[2] / "gabe-cc-update" / "scripts" / "draft-workflows.py"
    if not p.is_file():
        return None
    import importlib.util
    spec = importlib.util.spec_from_file_location("gabe_draft_workflows", p)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _pending_drafts(p: Path) -> int:
    """Proposals still sitting in workflows.draft.js — every `draft: true` entry the human has not yet
    moved into workflows.js. Tolerant of the honest-empty stub and of a hand-edited file (0 on any parse
    failure: a broken draft file is the drafter's next run to fix, not a pulse crash)."""
    if not p.is_file():
        return 0
    try:
        s = p.read_text(encoding="utf-8")
        i = s.index("=", s.index("window.GABE_WORKFLOWS_DRAFT")) + 1
        while i < len(s) and s[i].isspace():
            i += 1
        arr = json.JSONDecoder().raw_decode(s, i)[0]
        return sum(1 for d in arr if isinstance(d, dict) and d.get("draft"))
    except Exception:  # noqa: BLE001
        return 0


def s17_homing_evidence(root: Path, plan: dict | None, cfg: dict | None):
    """Membership evidence — pieces whose USERS / DATA witnesses disagree with their FILE (Part C, 2026-09-06:
    location is an indicator, never the definition). READS the committed c4-graph.json ``stats.homing`` — the
    emitter (_a3_homing) weighs three witnesses per piece and records a verdict; NOTHING re-homes. Fires at ≥ 3
    move candidates (≥60% of ≥2 users in ONE other entity, data agrees or abstains); the shared count (≥3
    consuming entities, none ≥60%) is REPORTED beside it, never a trigger — a shared utility is a structural constant
    (5 of 6 estates carry ≥ 1), not a debt anyone clears. The move is the entity walk; re-homing stays opt-in. Report-never-gate;
    silent on an older map (no block) and when the levels graph was absent (no users witness)."""
    if cfg is None:
        return Unavailable("no center config — the homing evidence lives in c4-graph.json")
    c4 = fetch_bridge._center(root) / "c4-graph.json"
    if not c4.exists():
        return Unavailable("no c4-graph.json yet — the center regen weighs the witnesses")
    try:
        hom = (json.loads(c4.read_text(encoding="utf-8")).get("stats") or {}).get("homing")
    except Exception as e:  # noqa: BLE001
        return Unavailable(f"c4-graph.json unreadable ({e.__class__.__name__})")
    if not isinstance(hom, dict):
        return Unavailable("no homing block on this map — regen with the current generators (Part C 2026-09-06)")
    if not hom.get("present"):
        return Unavailable(f"homing evidence absent — {hom.get('reason') or 'no levels graph'}")
    move, shared = int(hom.get("move") or 0), int(hom.get("shared") or 0)
    if move < 3:                       # shared is a structural constant of any real codebase (5 of 6 estates ≥ 1) — reported, never a trigger (review 2026-09-06)
        return None
    named = " · ".join(f"{str(m.get('piece', '?')).split('#')[-1]} → {m.get('to')}" for m in (hom.get("move_named") or [])[:3])
    return (f"homing evidence — {move} move candidate(s) (≥60% of ≥2 users in one other entity, data agrees) · {shared} shared aspect(s)"
            f"{(' · e.g. ' + named) if named else ''}; a piece's home is its file claim and its users say otherwise "
            f"(re-home is opt-in — nothing moved)",
            "/gabe-cc-init section  (the entity walk; mcp__gabe-map__entity_models model=seeded shows the moves applied, with destinations — the shared count is S9's fe-homes input)")


def s16_workflow_coverage(root: Path, plan: dict | None, cfg: dict | None):
    """Workflow coverage — the curated user workflows (window.GABE_WORKFLOWS, docs/site/center/workflows.js)
    are hand-authored and go stale as endpoints land. The DRAFTER (`/gabe-cc-update curate-workflows`)
    proposes candidates from the graph's screen-reachable endpoints no curated workflow names; this angle
    runs the drafter's ANALYSIS read-only over the committed c4-graph.json + workflows.js (nothing stored)
    and fires when (a) uncovered endpoints reach the threshold — a curate run is worth it — or (b)
    workflows.draft.js still carries proposals nobody moved into workflows.js — the REVIEW is owed, not
    the run (2026-09-04, the journeys dive). Report-never-gate; honest-empty without a c4, without
    endpoints (no API arm), or when the drafter script is not installed."""
    if cfg is None:
        return Unavailable("no center config — workflows live in docs/site/center/")
    center = fetch_bridge._center(root)
    c4p = center / "c4-graph.json"
    if not c4p.exists():
        return Unavailable("no c4-graph.json yet — the center regen builds it")
    drafter = _drafter()
    if drafter is None:
        return Unavailable("draft-workflows.py not found beside gabe-cc-update — reinstall the suite")
    try:
        c4 = json.loads(c4p.read_text(encoding="utf-8"))
        covered, _n = drafter.curated_labels(center)
        res = drafter.analyse(c4, covered, THRESHOLDS["workflow_cluster_min"])
    except Exception as e:  # noqa: BLE001
        return Unavailable(f"coverage analysis failed ({e.__class__.__name__})")
    if int(res.get("endpoints") or 0) < 1:
        return Unavailable("no endpoints in c4-graph.json (no API arm)")
    unc = int(res.get("uncovered") or 0)
    total = int(res.get("covered") or 0) + unc   # the denominator = the REAL endpoints; infra (_-prefixed) + BOOT + TASK sit outside it
    pending = _pending_drafts(center / "workflows.draft.js")
    if unc < THRESHOLDS["workflow_uncovered"] and pending < 1:
        return None
    clusters = len(res.get("drafts") or [])
    head = (f"workflow coverage — {unc}/{total} endpoint(s) in no curated workflow "
            f"({clusters} draft cluster(s) proposable)")
    if pending:
        return (head + f"; {pending} draft(s) already proposed, awaiting review",
                "universe → workflows tab → 'drafts — review & name': walk it, rename, set the level, move it into workflows.js")
    return (head, "/gabe-cc-update curate-workflows")


def s18_entity_proposals(root: Path, plan: dict | None, cfg: dict | None):
    """Entity proposals — the entity-model DRAFTER (`gabe-cc-update/scripts/draft-entities.py`, Phase 4 2026-09-06)
    projects the committed c4 `models` block into `docs/site/center/entities.draft.json`: a verdict per declared
    entity (FEATURE · SPLIT · MERGE · ASPECT · LAYER) + the candidate features no entity declares, each named. This
    angle reads that COMMITTED draft (the S16 precedent — the REVIEW is owed, not the run) and fires on ≥1 non-FEATURE
    verdict or ≥ THRESHOLDS['entity_candidates'] candidates. Two states: the draft's `head` equals the committed c4
    `head` → the review is owed (move: /gabe-cc-init rank, the third lens); heads differ → the draft is STALE and
    the RUN is owed (move: re-run the drafter). No draft file → silent; unparseable → 0, never a crash; no center →
    Unavailable. Report-never-gate; nothing here re-homes anything."""
    if cfg is None:
        return Unavailable("no center config — the entity draft lives in docs/site/center/")
    center = fetch_bridge._center(root)
    dp = center / "entities.draft.json"
    if not dp.is_file():
        return None
    try:
        d = json.loads(dp.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None                                                  # a broken draft is the drafter's next run to fix, not a pulse crash
    if not isinstance(d, dict):
        return None
    ruled = [x for x in (d.get("declared") or []) if isinstance(x, dict) and x.get("verdict") and x["verdict"] != "FEATURE"]
    cands = [x for x in (d.get("candidates") or []) if isinstance(x, dict)]
    if not ruled and len(cands) < THRESHOLDS["entity_candidates"]:
        return None
    head = None
    c4p = center / "c4-graph.json"
    if c4p.exists():
        try:
            head = json.loads(c4p.read_text(encoding="utf-8")).get("head")
        except Exception:  # noqa: BLE001
            head = None
    nmg = d.get("naming") if isinstance(d.get("naming"), dict) else {}
    nm_clause = ""
    if nmg:
        nm_clause = f" · names by {nmg.get('strategy') or 'domain'}"
        if nmg.get("config_error"):
            nm_clause += f" · ⚠ naming config: {nmg['config_error']}"
        if nmg.get("unused_words"):
            nm_clause += f" · {len(nmg['unused_words'])} naming word(s) name nothing"
    named_r = " · ".join(f"{x.get('slug')} {x['verdict']}" for x in ruled[:3]) + (f" +{len(ruled) - 3}" if len(ruled) > 3 else "")
    named_c = " · ".join(str(x.get("name")) for x in cands[:3]) + (f" +{len(cands) - 3}" if len(cands) > 3 else "")
    body = (f"{len(ruled)} verdict(s) to rule" + (f" ({named_r})" if ruled else "") + f" · {len(cands)} candidate entit{'y' if len(cands) == 1 else 'ies'}" + (f" ({named_c})" if cands else ""))
    if head and d.get("head") and str(d.get("head")) != str(head):
        return (f"entity proposals STALE — the draft was projected from map {d.get('head')} but the committed map is {head}; {body} — re-run before trusting",
                "python3 ~/.claude/skills/gabe-cc-update/scripts/draft-entities.py .  (then /gabe-cc-init rank)")
    return (f"entity proposals — {body}{nm_clause}; the REVIEW is owed (accept = one entities.<slug> edit in center.config.json), nothing re-homed",
            "/gabe-cc-init rank  (the entity-model third lens reads entities.draft.json)")


SIGNALS = [
    ("S1", "adversarial", s1_roast),
    ("S8", "evidence debt", s8_evidence),
    ("S3", "journey proof", s3_myopic),
    ("S4", "published docs", s4_docsite),
    ("S6", "entity context", s6_entity),
    ("S7", "explanation", s7_prism),
    ("S2", "structural", s2_health),
    ("S5", "scope", s5_scope),
    ("S9", "entity shape", s9_entity_shape),
    ("S10", "web bridge", s10_web_bridge),
    ("S11", "model census", s11_model_census),
    ("S12", "schema homing", s12_schema_homing),
    ("S13", "route/file census", s13_route_file_census),
    ("S14", "map deltas", s14_map_deltas),
    ("S15", "fe classification", s15_fe_unknown),
    ("S16", "workflow coverage", s16_workflow_coverage),
    ("S17", "homing evidence", s17_homing_evidence),
    ("S18", "entity proposals", s18_entity_proposals),
]


# --------------------------------------------------------------------------- #
# Decay — the record that stops a true signal from becoming wallpaper
# --------------------------------------------------------------------------- #

def decay_path(root: Path) -> Path | None:
    kdbp = root / ".kdbp"
    return (kdbp / "PULSE.jsonl") if kdbp.is_dir() else None


def read_offers(path: Path | None) -> list[dict]:
    if not path or not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def suppressed(offers: list[dict], sid: str, digest: str) -> bool:
    """Offered DECAY_AFTER times with this exact evidence and never cleared."""
    return sum(1 for o in offers if o.get("id") == sid and o.get("hash") == digest) >= DECAY_AFTER


def record(path: Path | None, sid: str, digest: str, text: str) -> None:
    if not path:
        return
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"ts": int(time.time()), "id": sid,
                             "hash": digest, "text": text}) + "\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--one-line", action="store_true",
                    help="print at most one row (a beat's terminal report), or nothing")
    ap.add_argument("--json", action="store_true", help="machine output")
    ap.add_argument("--why", action="store_true",
                    help="also list signals that did NOT fire and why")
    ap.add_argument("--no-record", action="store_true",
                    help="do not write the decay record (used by the battery)")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    plan = load_plan(root)
    cfg, _cfgdir = work_scope.load_center_config(root)   # the shared, both-layout probe
    dpath = decay_path(root)
    offers = read_offers(dpath)

    fired, quiet, unavailable = [], [], []
    for sid, label, fn in SIGNALS:
        try:
            res = fn(root, plan, cfg)
        except Exception as exc:                              # noqa: BLE001
            unavailable.append({"id": sid, "label": label, "reason": f"signal errored: {exc}"})
            continue
        if isinstance(res, Unavailable):
            unavailable.append({"id": sid, "label": label, "reason": str(res)})
        elif res is None:
            quiet.append({"id": sid, "label": label})
        else:
            evidence, command = res
            digest = hashlib.sha1(f"{sid}|{evidence}".encode("utf-8")).hexdigest()[:12]
            fired.append({"id": sid, "label": label, "evidence": evidence,
                          "command": command, "hash": digest,
                          "suppressed": suppressed(offers, sid, digest)})

    live = [f for f in fired if not f["suppressed"]]

    if args.json:
        print(json.dumps({"fired": fired, "quiet": quiet, "unavailable": unavailable,
                          "decay_record": str(dpath) if dpath else None}, indent=1))
        return 0

    if args.one_line:
        if not live:
            return 0                      # silence is the correct output
        top = live[0]
        if not args.no_record:
            record(dpath, top["id"], top["hash"], top["evidence"])
        print(f'PULSE: {top["evidence"]} → {top["command"]}')
        return 0

    if not live and not unavailable:
        print("angles: nothing to surface — every satellite trigger is quiet")
    for f in live:
        print(f'  {f["id"]}  {f["evidence"]}  → {f["command"]}')
    for f in fired:
        if f["suppressed"]:
            print(f'  {f["id"]}  (silenced — offered {DECAY_AFTER}× on the same evidence, '
                  f'not taken; returns when the evidence changes)')
    if args.why:
        for q in quiet:
            print(f'  {q["id"]}  quiet — its condition is not met')
        for u in unavailable:
            print(f'  {u["id"]}  UNAVAILABLE — {u["reason"]}')
    elif unavailable:
        print(f'  ({len(unavailable)} signal(s) unavailable — run with --why to see why)')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
