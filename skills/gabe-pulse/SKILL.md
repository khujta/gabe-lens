---
name: gabe-pulse
description: "Read-only completeness sweep — ten deterministic signals ranked into bands, plus the ANGLE family: which satellite would find something right now, surfaced as one line at the end of every spine beat so the manual-only skills stop depending on memory. Never writes, never dispatches, never judges code."
when_to_use: "After a long or sprawling stretch: did everything that should have run actually run, what am I missing, anything pending before I stop? Reports what is owed and the command that clears it."
context: fork
agent: Explore
metadata:
  version: 1.7.6
---

# Gabe Pulse — is anything important owed?

**Usage:** `/gabe-pulse [brief | --json | --since <ref>]`

## Gabe execution contract (E1–E7)

This skill runs under the suite execution contract — E1 EVIDENCE · E2 RUN-BEFORE-✅ · E3 NO SILENT DOWNGRADE · E4 REUSE FIRST · E5 STATE SYNC · E6 MISSING ANCHOR = STOP · E7 REPORT WHERE — floors, not ceilings; a skill's own gate may be stricter, never looser. Full text: `../gabe-docs/references/execution-contract.md` (if that file is missing, E6 applies — STOP).

## What this does

A **satellite**, not a beat. `/gabe-next` answers *"what is the one next step?"* from PLAN cells.
Pulse answers the broader question you ask after a long stretch of work: **"is anything important
owed anywhere?"** — including the things no beat is currently watching.

It reads ten deterministic signals, sorts them into four bands, and prints a ranked report.
It **writes nothing, dispatches nothing, and runs no tests.** Every row names the command
that clears it; you decide whether to run it.

Its reason for existing is the measured one: across 70 sessions on five repos, 20% ran no
lifecycle beat at all, and 113 files changed in sessions that produced no commit and no record.
Pulse is the manual check that makes that visible before it compounds.

## Procedure

1. Read `references/pulse-spec.md` IN FULL before executing — it is the binding spec: the ten
   signals, their exact sources, the band ranking, the cap rule, and the degradation table.
   If it is missing, E6 applies — STOP.
2. Parse `$ARGUMENTS`: `brief` (headline only), `--json` (machine output), `--since <ref>`
   (passed through to the ledger-gap detector), `--bookkeeping <prefix>` (repeatable).
3. Establish the gate (spec §1). A `.kdbp/` project reads all ten signals; a repo without one
   reads the subset that git and the tree can answer, and **enumerates the rest as unavailable
   with a reason** — never silently.
4. Collect the signals (spec §2). Each is deterministic; none costs an LLM call. A signal that
   errors is reported as `undetermined` with its reason, never as clean (E3).
5. Rank into bands and apply the cap (spec §3). Print the report (spec §4).

## The four bands

Ranked by what their absence costs, worst first.

| Band | Question it answers | Signals |
|---|---|---|
| **EVIDENCE** | Did work happen that nothing recorded? | unregistered commits · uncommitted changes |
| **LIFECYCLE** | Is a beat owed on work already done? | router's next step · prior-phase debt · Red ⬜ · Center ⬜ |
| **SHIP** | Is finished work sitting unshipped? | unpushed commits |
| **AGING** | Is something quietly getting worse? | PENDING escalations · never-walked stations · size budget |

EVIDENCE leads because it is the only band where the *record itself* is missing — every other
band describes work the project can still see.

## Signal sources

All deterministic. No signal is inferred from prose or from a session transcript.

| # | Signal | Source | Clears with |
|---|--------|--------|-------------|
| P1 | Unregistered commits | `scripts/ledger-gap.sh` | `/gabe-commit`, or a ledger row |
| P2 | Uncommitted changes | `git status --porcelain` | `/gabe-commit` |
| P3 | Unpushed commits | `git log @{u}..HEAD` | `/gabe-push` |
| P4 | Router's next step | `mcp__gabe-kdbp__next_beat` → `../gabe-next/scripts/next.mjs --json` | whatever it names |
| P5 | Prior-phase debt | same, its prior-row sweep | the beat each row names |
| P6 | Center coverage ⬜ | `mcp__gabe-kdbp__kdbp_snapshot` `plan.phases[]` (cells as `todo`/`done`, capped at 40), else the PLAN `Center` column | `/gabe-cc-update <phase>` |
| P7 | Red debt ⬜ | `mcp__gabe-kdbp__kdbp_snapshot` `plan.phases[]` (cells as `todo`/`done`, capped at 40), else the PLAN `Red` column | `/gabe-red <phase>` |
| P8 | PENDING escalations | `mcp__gabe-kdbp__kdbp_snapshot` `pending` + `.kdbp/PENDING.md` | `/gabe-review deferred` |
| P9 | Never-walked stations | `.kdbp/walks.jsonl` | append walk record (walks.jsonl) |
| P10 | Size-budget breaches | `../gabe-commit/scripts/size-budget.sh` | report-never-gate (R9) |

**P4/P5 defer to `next.mjs` rather than re-deriving the routing decision** — directly, or through `mcp__gabe-kdbp__next_beat`, which relays that same script. Two readers of PLAN
cells that disagree is a second source of truth; pulse reports what the router says, verbatim.

## Output contract (summary)

Opens with **one line** naming the single most important owed thing, or `nothing owed`. Then the
banded table, worst band first, each row carrying its evidence and its clearing command. Closes
with the signal roster: how many signals ran, how many were unavailable, and **why each one was**
— an unavailable signal is a stated fact, never an omission (E3).

Caps at 5 rows per band. A truncated band prints `… N more` — never a silent cap. `brief` prints
only the headline and the roster count. Full contract in the spec; it is binding.

## Non-goals

- Does **not** write any file — no LEDGER row, no PENDING row, no PLAN tick. Pulse is read-only.
- Does **not** dispatch commands. It names them; you run them. (`/gabe-next` is the dispatcher.)
- Does **not** run tests, builds, or linters — no side effects, no wall-clock surprises.
- Does **not** judge code quality, coupling, or churn — that is `/gabe-review` and `/gabe-health`.
- Does **not** re-derive the routing decision — `next.mjs` owns it.
- Does **not** classify your work into categories. The record showed the useful split is
  *recorded* vs *unrecorded*, and P1/P2 already separate those without asking you to label anything.

## Example

```
$ /gabe-pulse
PULSE — gustify · 2026-07-26

▶ Most important: 73 commits carry no LEDGER row (evidence gap since 17a4056)

EVIDENCE
  P1  73 unregistered commits · 74 bookkeeping excluded    → /gabe-commit
  P2  30 uncommitted paths                                 → /gabe-commit
LIFECYCLE
  P4  router says: /gabe-review (Phase 41 — Exec ✅, Review ⬜)
  P6  3 phases shipped, not covered in the center          → /gabe-cc-update 38,39,41
SHIP
  P3  clean — nothing unpushed
AGING
  P8  2 PENDING rows at Times Deferred ≥ 3                 → /gabe-review deferred

signals: 8 ran · 2 unavailable (P9 no walks.jsonl · P10 no size-budget script on PATH)
```

The fence shows the STRUCTURE. In the real response the rows that name a file are emitted as
**markdown, not fenced**, so the paths click through (findings contract — a fenced link is inert):

- **P1** 73 unregistered commits since `17a4056` → [.kdbp/LEDGER.md](.kdbp/LEDGER.md) · `/gabe-commit`
- **P8** 2 PENDING rows at ≥3 deferrals → [.kdbp/PENDING.md](.kdbp/PENDING.md) · `/gabe-review deferred`
- **P10** breaches → each over-budget file linked (from `size-budget.sh`) · advisory

Count-only rows (P2 uncommitted, P4/P6 phase ids) stay plain — no single file to link.

$ARGUMENTS

## The ANGLE family (1.1.0)

`scripts/angles.py` computes thirteen evidence-backed triggers — adversarial pass owed (S1),
structural scan overdue (S2), journey proof missing (S3), published docs stale (S4), scope drift
(S5), entity context worth loading (S6), an explanation worth drawing (S7), workflow-census
capture debt (S8), entity-shape drift (S9), a diff-added fetch that named no declared endpoint
(S10), model-census drift (S11 — a table class no entity's config claims), schema-homing
residue (S12 — a schema unwired in a live file: dead, or in code the config never claimed; multi-consumer
shapes and dormant contract lanes are counted, never nagged) and route/file-census drift
(S13 — a route or backend `.py` in a scanned code dir that no entity claims, closest-to-the-request-path
first via the reach hop; absence is full coverage, never a false nag) — each naming the satellite that would find it now, or reporting **unavailable** with what
would unlock it. Spine beats print its `--one-line` output verbatim; it emits at most one row and
nothing when nothing fires.

```
python3 skills/gabe-pulse/scripts/angles.py . --why      # every signal, including why one is quiet
python3 skills/gabe-pulse/scripts/angles.py . --one-line # what a beat prints
python3 skills/gabe-pulse/scripts/angles.py . --json     # machine output
```

Full contract in `references/pulse-spec.md` §5, including the decay rule and this mechanism's own
kill condition. Battery: `tests/pulse-angles/run.sh` — 46 cases, every live signal proven to FIRE
and stay SILENT, plus the cap, the silence, and the decay.
