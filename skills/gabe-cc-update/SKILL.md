---
name: gabe-cc-update
description: "Command-center feature coverage — translate shipped work into its entity's lens card, diagrams, and evidence narration; keep the center regenerating green. Also owns scripts/write-inflight.py, the deterministic in-flight projection the E8 beat tail refreshes (inflight.json + .js, read by the board at view time)."
when_to_use: "Cover a shipped feature, center status, backfill entity-by-entity, curate proof after a green run — ONLY where docs/site/center/center.config.json exists; elsewhere STOP → /gabe-cc-init."
metadata:
  version: 1.8.0
---

# Gabe Feature — the command center's per-feature ritual

**Usage:** `/gabe-cc-update [<phase>|--range A..B] | status | backfill | curate <artifact-subdir> <shot-nums…> | curate-workflows | release [--since <row>]`

## Gabe execution contract (E1–E7)

This skill runs under the suite execution contract — E1 EVIDENCE · E2 RUN-BEFORE-✅ · E3 NO SILENT DOWNGRADE · E4 REUSE FIRST · E5 STATE SYNC · E6 MISSING ANCHOR = STOP · E7 REPORT WHERE — floors, not ceilings; a skill's own gate may be stricter, never looser. Full text: `../gabe-docs/references/execution-contract.md` (if that file is missing, E6 applies — STOP).

## The intention (why this skill exists)

*A shipped feature becomes explainable to anyone — its story, its diagrams, its tests, its proof, one click apart — and the center regenerates green afterward. The machine already knows the facts (PLAN, junit, run-history, coverage, adoption.json, archmap, git) — where the servers are registered the map and the lifecycle state are READ as tools (`mcp__gabe-map__*` · `mcp__gabe-kdbp__*`) rather than re-derived by hand; junit, run-history and the raw coverage report stay file reads; this skill writes ONLY the translation. Every claim it cannot derive, it must refuse to invent.*

The scripts do everything deterministic. The judgment that remains, and is ALL this skill adds: prose worth reading, which diagram nodes light up, which shots become proof, whether a claimed regex or glob is honest, and whether a gap gets a reason or a task. The center's axis is the ENTITY (adoption.json is the registry — D123): a shipped phase lands as growth on the entity pages it touched, never as a page of its own.

## Scope gate (run FIRST, every invocation)

`docs/site/center/center.config.json` must exist in the project — `mcp__gabe-map__map_status` answers this gate in one call: it walks up for that same anchor and returns the center's entities, its freshness vs git, the graft index state and the regen command. A `present: false` answer carries its own `reason` (no center under this root · a root it resolved elsewhere · the suite's own beat-spine center, ruling R8) — read the reason and confirm against the file before stopping: the FILE is the gate, the tool is the fast path. If it does not exist: **STOP** — this project has no command center. Point the human at `/gabe-cc-init` (brownfield center adoption — its `init` mode archives existing docs and bootstraps the center; `rank`/`section` ingest the back-catalog) and end.

## Bindings (the project provides; verify before each mode)

All machinery ships in the suite (`templates/center/` — generators, gate, helpers, harness) and reaches a project bootstrap-by-copy at `/gabe-cc-init` init; the project's copies live under `scripts/`.

| Binding | Path |
|---|---|
| Generator | `scripts/build_center_a3.py` — invoked via `scripts/refresh_center.sh [junit\|coverage\|e2e\|all\|regen]` (`regen` = re-render only; the other modes first run the shell lines declared in config `commands`) |
| Gate | `scripts/check_center_links.py` — chained by `refresh_center.sh` after EVERY mode; dead links / an empty crawl fail (exit 1), registry drift WARNs |
| Proof curation | `scripts/curate_proof.py <artifact-subdir> <shot-nums…>` |
| Backfill queue | `scripts/next_feature.py` |
| Status actionables | `scripts/center_status.py` — the `status` mode's linked findings + `→ next` steps (reads registry/cards/config; prints, gates nothing); `mcp__gabe-map__center_status` runs the SUITE's own copy of this generator against the project — never this installed file (WS-2; byte-identical at install, so a locally edited `scripts/center_status.py` is NOT what the tool relays) — capped at 6,000 chars (`truncated` named), and never triggers a regen of its own |
| Workflow drafts | `scripts/draft-workflows.py <root> [--json] [--min N]` — the `curate-workflows` mode's drafter (reads the committed c4-graph + workflows.js; writes `docs/site/center/workflows.draft.js`; honest-empty without a center) |
| Entity drafts | `scripts/draft-entities.py <root> [--json] [--model proposed\|derived] [--min N]` — the ENTITY-MODEL drafter (entity models Phase 4, 2026-09-06): a projection of the committed c4-graph `models` block into `docs/site/center/entities.draft.json` — a verdict per declared entity + every candidate entity NAMED (`named_by` domain\|table, `draft_name()`'s action phrase, suggested slug) + `coverage.witnessed` and `abstained` (non-optional); loaded by NO page; honest-empty ×4 (no center · no c4 · unreadable · no `models` block → "regen with the current generators"); COMMITTED so pulse S18 and the cc-init third lens read it across sessions; acceptance is owned by `/gabe-cc-init rank` (one `entities.<slug>` edit) |
| Census scaffold | `scripts/scaffold_census.py <root> <slug>` — seeds a valid skeleton workflow census from a card's `# FLOWS` (the census ASK's *author now*; a convenience, not E6-mandatory — absent, the census is hand-authored) |
| Risk sweep | `scripts/risk_sweep.py <root> <slug>` — the P0–P3 ladder collector (step 6); ranked + capped flags routed through `scripts/disposition.py <root> --defer\|--tackle --flag '<json>'` (the disposition contract) |
| Shell-JS harness | `scripts/verify_center_chrome.mjs <page.html…\|center-dir>` |
| The one editorial overlay | `docs/site/center/center.config.json` (`paths` · `corpora` · `commands` · `entities.<slug>` blocks) |
| Entity registry | `docs/site/center/adoption.json` (owned by `/gabe-cc-init` — slugs, statuses, display names) |
| Cards | `docs/site/center/cards/<slug>.md` |

Any binding in this table missing → E6 STOP, name it, done. Project-local extras (a scaffold script, extra reporters) are optional conveniences — never E6-mandatory. Format authority: the generators themselves (`scripts/_center_data.py` fails loud on card structure; `build_center_a3.py` aborts on an `entities` key adoption.json does not register) — `references/feature-spec.md` states intention and POINTS there; never duplicate the schema.

## Modes

### `/gabe-cc-update <phase>` or `--range A..B` (default — cover one shipped feature)

1. Name the entity(ies) the phase's work touched — pass the phase's changed files (its LEDGER commits' diff) to `mcp__gabe-map__blast_radius` and it reads them into their owning entities (a FLOOR reading; with NO `files` argument it reads the WORKTREE vs HEAD, not the phase); `mcp__gabe-map__owner_of` answers one path and `mcp__gabe-map__entity_context` with no slug lists the registered ones; the slugs are still `adoption.json`'s (an unknown slug aborts the build; a genuinely NEW entity is `/gabe-cc-init` registry business, never a config edit). Display names come from the registry rows, colors from the generator maps — the config names nothing.
2. Write or extend `entities.<slug>` in `center.config.json`: `test_rx` (required — claims the test files that VERIFY the entity, which may predate the phase; broad on purpose: an over-match shows as a visible row, an under-match silently hides coverage — ask `mcp__gabe-map__cases_for` on the entity's endpoints and models first: each answer names the C-ids and the test FILES already covering them, so the pattern is drawn around files that exist; it reads the LAST regen, so a brand-new `entities.<slug>` block answers empty until step 3's regen, and the corpus grep stays the floor for what the map has not mapped) and, once the section is adopted, `proofs[]` · `code{layer: [globs]}` · `models[]` — ask `mcp__gabe-map__map_census` before drafting them: the unclaimed files, models and routes it names are exactly what this block should claim (or leave unclaimed with a reason, never in silence), and `mcp__gabe-map__owner_of <path>` says whether another entity already claims a file. Draft patterns carry `TODO(verify-glob)`. Author or extend the card — the contract (required sections + EXACT headings, the FLOWS grammar, optional LENS/CODE/RISKS/ANGLES sections, diagram rules) lives ONCE in `references/feature-spec.md`: read it before writing; the gate flags deviations. Ground every line in commits/code you actually read.
3. Regenerate (`refresh_center.sh regen`). Read the built feature page's **resolved match lists** — trim any over-claiming `test_rx`/glob, then delete the `TODO(verify-glob)` marker. Gate must be green (WARNs for THIS entity cleared).
4. **Workflow census** — the Evidence tab's spine (P1: structural, always high). Run `check_workflow_drift.py docs/site/center/workflows/<slug>.json`; if the census is **absent or drifted, ASK** the operator — never author silently: *author now* (`scaffold_census.py <root> <slug>` seeds a valid skeleton from the card's `# FLOWS`; the operator reshapes the states) · *extend* (add missing steps) · *defer* (S8 nags; the tab renders a named absence) · *decline* (record the reason). Fires **regardless of an open Center cell** — the forward-phase FIXER is one trigger, not the only one. Tick `workflow_census` in `adoption.json` once authored or declined-with-reason. Contract: `references/feature-spec.md` §The workflow census.
5. Evidence, when it exists or one run away: green e2e run → `curate` mode below. When it doesn't: the card's ANGLES intent plus the machine Action Ledger carry the absence honestly — never a fake proof.
6. **Risk sweep** — the post-generation P0–P3 ladder (ruling 2026-08-10). Run `risk_sweep.py <root> <slug>`: it surfaces the **capped, ranked** flags — security priced HIGH on the card (P0) · census capture/claim debt (P1) · an e2e gap where the card's `# RISKS` prices a GAP of money/correctness/security with no proof set (P2) · size-budget breaches collapsed to one (P3). For each flag ASK the operator **tackle-now** (`disposition.py <root> --tackle --flag '<flag-json>'` → apply the printed spec via `/gabe-plan update`) or **defer** (`disposition.py <root> --defer --flag '<flag-json>'` → a PENDING row); both render on the board, defers get nagged by pulse P8/S8. High-risk only, never a flood; an `unavailable` detector is named, never a false all-clear. A model-layer pass MAY add `/gabe-roast Security` + `/gabe-health` god-files/coupling beyond the scriptable detectors. Contract: `../gabe-docs/references/disposition-contract.md`.
7. Present the built pages (feature + docs) to the human for THE review. On approval, stamp the card `# REVIEWED` (date + who) **and close the lifecycle loop (E5):** if the phase has a PLAN row whose Phases table carries a `Center` column — `mcp__gabe-kdbp__phase_context` with `phase: <phase>` (unset, it answers PLAN.json's `current_phase`: the covered phase on the routed path, where /gabe-next settled the pointer onto this Center-⬜ row before dispatching, but NOT for a prior-phase debt row or a `--range` member — pass the id every time, one call per covered phase) returns that row's cells and its PLAN.md line, and a table with no Center column simply carries no `center` key in `cells` (`mcp__gabe-kdbp__kdbp_snapshot` shows the whole table the same way) — set that phase's `Center` cell to ✅ in `.kdbp/PLAN.md` **and** mirror `cells.center = "done"` into `.kdbp/PLAN.json` (same turn), both through Write/Edit so the D7 plan-proof hooks see the write — this is the cell `/gabe-next` reads to stop routing coverage. If the PLAN has no `Center` column, print one line: `ℹ PLAN has no Center column — run /gabe-plan update to adopt routed command-center coverage` and continue (never mutate the schema here; that is /gabe-plan's job). One feature per invocation; report what remains.

### `/gabe-cc-update status`

Run `refresh_center.sh regen`, then take the actionable list from `mcp__gabe-map__center_status` — it runs the SUITE's own copy of `center_status.py` against this project (never the repo's — WS-2) and relays it, never triggering a regen of its own; when the answer says `truncated`, or the server is not registered, run `scripts/center_status.py` directly for the full text — it **owns the actionable list**: every finding is a workspace-relative markdown link (clickable in the IDE/terminal) plus a concrete `→ next` step, read from the same registry/cards/config the gate reads. **Relay its output verbatim** and add only ordering prose — never compose a link by hand. It covers the card + registry actionables: a card `# REVIEWED` not stamped (a card on disk is finalized regardless of registry status — a PENDING entity with a card is the live mid-ritual thread, surfaced not skipped), `TODO(author|verify-glob|narration)`, sub-canon diagrams (pre-review only), malformed FLOWS, proof sets missing narration, and cardless entities (adopted → backfill · pending → shortlisted). Then read the **gate's own** build + dead-link summary verbatim (dead links fail the build; the crawl is the gate's, not center_status's). No judgment beyond ordering.

### `/gabe-cc-update backfill`

Run `next_feature.py` — the queue reads committed center data only: fully-served PLAN phases whose `Center` cell is still open, then adopted entities with no card on disk. For the next queued item, ask the human for the TIER — **full** (evidence + narration; recent work) · **card-only** (registry block + card; history whose evidence nobody can rerun) · **skip** (record the disposition where the queue reads it: a parked/obsolete phase marks its PLAN `Center` cell ⏸/⚰️, a dropped entity carries the reason on its registry row — dropped work never gets a fake page, and never silence). Then run the default mode at that tier. One item per invocation.

### `/gabe-cc-update release [--since <deployments-row>]`

The stakeholder showcase — a MODE, not a lifecycle beat (it owns no time window, observes nothing perishable, gates nothing). Triggered by `/gabe-push`'s terminal-env pointer; renders `releases/<id>.html` from the phases whose `Center` cell went ✅ since the last terminal-env DEPLOYMENTS row. Contents + the video-slots-as-named-gaps rule: `references/feature-spec.md` §Release (binding).

### `/gabe-cc-update curate <artifact-subdir> <shot-nums…>`

After a green e2e run: pick the shots that PROVE the claims (selection is the judgment — one leg per claim), run `curate_proof.py`, author the manifest's narration block (`story` · one sentence per leg — describes, never asserts) AND its classification (`role:` + `flows:` — feature-spec §Flow coverage), then register the set: append the artifact-subdir name to `entities.<slug>.proofs[]` in `center.config.json`. Regen. Video custody: recordings are machine-local, never committed; the pages say so.

## Output contract

Per feature, on completion: a validated `entities.<slug>` block with human-confirmed `test_rx`/globs · a card with zero TODO markers and a `# REVIEWED` stamp · 3 diagrams (or the card states why fewer) · narration + `role:`/`flows:` wherever a proof set exists · gate green with this entity contributing zero WARNs · the phase's PLAN `Center` cell flipped ✅ (PLAN.md + PLAN.json) where that column exists, else the one-line adopt-the-column pointer. The verification changelog needs nothing from you — the builder appends `run-history.jsonl` itself on every regen whose totals moved. Card-only tier: the same minus evidence (ANGLES carry the reasons). Skip: one registry-row reason. E7: report page paths + the gate's closing line.

### `/gabe-cc-update curate-workflows`

**A draft is finished work, not a cluster waiting for a name (operator 2026-09-05).** The drafter names each entry in the
user's words — the legend reference's definitions logic: what the person DOES (`Manage cooking sessions — cancel ·
readiness · photos`, `Look at notifications`, `Edit settings — household · preferences`; `draft_name()` in the script,
deterministic from the endpoint labels) — and levels it into its tier, so the station places it in Orientation · Core ·
Specialized beside the curated rows, wearing a DRAFT chip. Review = walk it, then ACCEPT by moving the entry into
`workflows.js` (rename freely); there is no "review & name" bucket. This is the default from here on.

Journey CREATION for the one journey kind that needs a human (ruling 2026-09-04). Backend, test and
commit journeys derive themselves; the curated user workflows (`docs/site/center/workflows.js`) did
not — a new project's tab stayed empty until someone remembered the file. This mode PROPOSES, never
curates: run `scripts/draft-workflows.py .` — every endpoint no curated workflow names, clustered by
entity · the screen that drives it, steps read→write, level SUGGESTED (no writes → 1 · single-entity
writes → 2 · cross-entity → 3), written as `draft:true` entries to `workflows.draft.js`. The station
lists them in the workflows tab under **drafts — review & name**, walkable like any workflow.
Print the script's line verbatim (drafts · uncovered · covered · infra skipped · unreached), then
hand the operator the review: walk a draft, rename it in their words, reorder, set the level, move
it into `workflows.js`; the next run drops it. **Unreached** endpoints (no screen calls them) are
reported, never drafted — a bridge gap or a dead endpoint is the human's call. Pulse S16 nags the
standing coverage; `/gabe-cc-update status` shows the draft count. Deterministic (no wallclock; the
c4 head sha stamps the file); honest-empty without a center or a c4-graph; report-never-gate.

