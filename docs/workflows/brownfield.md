# Brownfield Workflow

**Purpose:** adopt Gabe Suite into an existing codebase without pretending it is a fresh project.

## Shape

Brownfield work starts with evidence, not intention. The repository already contains decisions, shortcuts, tests, and drift. Gabe Suite should first discover those facts and only then create KDBP structure around them.

```mermaid
flowchart TD
    Repo[Existing repo] --> Inventory[Read-only inventory]
    Inventory --> Init{"KDBP exists?"}
    Init -->|Yes| Update["/gabe-init update"]
    Init -->|No| Adopt["/gabe-init <name>"]
    Update --> Baseline["/gabe-health + /gabe-health debt"]
    Adopt --> Baseline
    Baseline --> Scope["/gabe-scope or scope from existing docs"]
    Scope --> PlanCheck["/gabe-plan check when PLAN exists"]
    Scope --> Plan["/gabe-plan"]
```

This guide covers KDBP adoption (init/scope/plan). For adopting the **Testing Command Center** into an existing codebase — archiving legacy docs, bootstrapping the center, and ingesting the back-catalog one approved section at a time — the dedicated command is `/gabe-cc-init`.

## Step 1 - Inventory Without Writing

Before any Gabe command mutates the repo, inspect:

- `git status --short --branch`
- existing docs and README
- package manifests and test scripts
- source tree layout
- current CI and deployment files
- existing architecture decisions, ADRs, issue docs, or planning files
- whether `.kdbp/` already exists

The goal is to avoid AP2 surprise and AP12 undocumented-decision damage. Brownfield adoption should not overwrite or reinterpret existing project truth without evidence.

## Step 2 - Choose the Adoption Path

| Existing state | Path |
|----------------|------|
| `.kdbp/` exists | use `/gabe-init update` for non-destructive template top-up |
| no `.kdbp/`, but repo has code | use `/gabe-init <name>` cautiously after inventory |
| active older `PLAN.md` exists | use `/gabe-plan check` before executing |
| existing docs already define scope | feed them into `/gabe-scope` reference frame |

`/gabe-init update` must not overwrite user-authored files. It should add missing KDBP files, run schema migrations when accepted, and preserve existing content.

## Step 3 - Establish a Baseline

Run:

```sh
/gabe-health
/gabe-health debt
```

Use the baseline to find:

- god files and churn hotspots
- coupling clusters
- missing or implicit decisions
- rule violations from existing lessons
- AP citations that explain architectural pressure

Do not use the baseline as an excuse to refactor everything. Route findings into `PENDING.md`, `DECISIONS.md`, or a staged plan.

## Step 4 - Capture Existing Scope

If the project has no `.kdbp/SCOPE.md`, run:

```sh
/gabe-scope
```

Use the Reference Frame step to add existing docs as authoritative or suggestive references. Brownfield scope should summarize what the repo already is before it describes what it should become.

If scope already exists and needs a change, use:

```sh
/gabe-scope-change "what changed"
```

## Step 5 - Retrofit or Create a Plan

If an active plan exists:

```sh
/gabe-plan check
```

Use the report to identify missing columns, missing phase details, missing tier decisions, or missing decision records. Apply retrofits only after reviewing the preview.

If no active plan exists:

```sh
/gabe-plan "next stabilization or feature milestone"
```

For brownfield projects, the first plan should usually stabilize observability, tests, structure, or documentation before large feature work.

## Step 6 - Execute in Narrow Slices

Use `/gabe-next` once KDBP state is coherent. Keep slices small because brownfield risk is usually hidden in coupling and implicit state.

Expected loop:

```sh
/gabe-next
/gabe-review
/gabe-commit
/gabe-push
```

Run `/gabe-review` tightly on changed areas and include untracked files that are clearly part of the same change set.

**Understanding what already shipped:** if the project has no Testing Command Center yet,
`/gabe-cc-init` bootstraps one (archive-never-delete init, machine-ranked shortlist, one approved
section per run). Once a center exists, `/gabe-cc-update backfill` is a first-class brownfield tool — it walks
served phases newest-first and turns each into an explainable page (card + diagrams +
test angles + evidence), with honest tiers for history: `full` for recent work,
`card-only` when evidence can't be re-run, `skip(reason)` for dropped work. New
features then join the per-phase rhythm (`… /gabe-review → /gabe-cc-update <phase> →
/gabe-commit …`) so the center never falls behind again.

## Adopt a repo you don't own (a study install)

A codebase you are reading, not shipping — a study curriculum, a due-diligence pass, a first look at an
inherited service — gets the center too, without the back-catalog flow. The install is the config-only
half of `/gabe-cc-init init`, as a script (2026-09-06, from the repo-study program):

```
git -C <repo> checkout -b gabe-center          # a LOCAL branch: app source untouched, never pushed
bash ~/.claude/templates/gabe/center/generators/bootstrap_center.sh <repo> --name <slug> --display "<name>"
```

It lands the generators in `scripts/`, the station skeletons in `templates/center/shell/`, a
`docs/site/center/center.config.json` skeleton with `entities: {}`, and the `.gitignore` seeds. Never a tracker,
never over an existing config, re-runnable. Then:

1. **Fill `entities`** — one block per entity: `code.api` / `code.models` / `code.schemas` / `code.services` /
   `code.web` (literal paths **or globs, `**` recursive**) + `test_rx`. Derive them from the route census
   (`backend/**/routes.py`, `api/v1/*.py`) and the packages; a repo that keeps every table in one file gets a
   `data` entity that owns it, so every foreign key reads as a cross-entity wire.
2. **A frontend needs `typescript`.** Run the project's own install (`bun install`, `npm ci`) so the extractor
   resolves it from the tree — or `export GABE_TS_DIR=<a dir whose node_modules/typescript exists>`; the arm SAYS
   when it borrowed one.
3. `bash scripts/refresh_center.sh regen` — the archmap, the C4 graph, every station page, the chrome harness.
   With no `adoption.json` the build takes the config's entities as the registry, out loud.
4. **Journeys = your missions.** Write `docs/site/center/workflows.js` (`{ name, level, note, steps: ["METHOD /path", …] }`,
   labels exactly as the station prints them) and open `docs/site/center/gabe-universe.html?journey=<name>` — one
   trace per session. `?ent=<slug>` opens one entity.

What the graph says instead of guessing: `route_mounts.unresolved` (a non-literal include prefix), `unparseable`
(a file the suite's Python could not parse — newer syntax gets a shim), `stats.web.other_roots` (a second frontend
not scanned), `stats.web.unhomed` (fetching files no entity claims), `fn_similarity` (the twin pass ran blocked
above its budget), and above 1,600 nodes the station boots FOLDED (capsules on, tier 0 — a Sources row says so).

What never happens here: no test suite runs (`regen` never runs one), no source file is edited, nothing is pushed.
`/gabe-cc-init init · rank · section <entity>` records the adoption later, on the same files.

## Brownfield AP Watchlist

| AP | Watch for |
|----|-----------|
| AP2 minimize surprise | behavior that existing users or maintainers already rely on |
| AP4 everyone will not just | manual runbooks posing as safety |
| AP6 coupling | refactors that force unrelated areas to move together |
| AP8 explicit state | hidden caches, implicit flags, stale async listeners |
| AP9 single source of truth | duplicated config, schema, constants, or generated files |
| AP11 testability | logic that requires full-system boot for small checks |
| AP12 documented decisions | architecture implied only by old code |

## Acceptance Signals

Brownfield adoption is ready for normal phase execution when:

- `.kdbp/` exists and important existing docs are reflected in scope or references.
- current risk has been baselined with `/gabe-health` and `/gabe-health debt`.
- an active plan passes `/gabe-plan check`, or a new plan exists.
- major implicit decisions are either recorded in `DECISIONS.md` or tracked in `PENDING.md`.
- the first execution slice has a bounded blast radius and a clear test path.

## Avoid

| Avoid | Use instead |
|-------|-------------|
| treating brownfield as greenfield | inventory first |
| rewriting docs before reading code | reference existing docs, then reconcile |
| broad refactor as first plan | stabilization or narrow feature slice |
| direct SCOPE edits | `/gabe-scope-change` |
| hiding adoption gaps in chat | `PENDING.md`, `DECISIONS.md`, or `RULES.md` |
