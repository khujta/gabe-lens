# Gabe Pulse — binding spec

> The deep spec for `/gabe-pulse`. `SKILL.md` is the lean core and carries the summary;
> this file is binding wherever the two could be read differently.
>
> Pulse is a **satellite**: read-only, human-invoked, dispatches nothing. Every rule below
> exists to keep it from becoming a nag surface — a report that fires on everything is
> muted within a week, and a muted report is worse than none because it looks like coverage.

## §0 Contract

Runs under E1–E7 (`../../gabe-docs/references/execution-contract.md`). Two floors bind hardest:

- **E1 EVIDENCE** — every row cites the artifact it read. No row is emitted from inference,
  from prose, or from a session transcript. If a signal cannot be measured, it is
  `undetermined`, never clean.
- **E3 NO SILENT DOWNGRADE** — a signal that did not run prints an enumerated reason. The
  roster line at the end of the report is not optional; it is how the reader distinguishes
  "nothing owed" from "nothing looked".

## §1 Gate and modes

### 1.1 Gate

Pulse runs anywhere. It does **not** require `.kdbp/`. What varies is which signals resolve.

| Repo shape | Detection | Signal set |
|---|---|---|
| KDBP project | `.kdbp/BEHAVIOR.md` exists | all ten |
| Command-center project, no KDBP | a center config exists and declares `paths.ledger` (`mcp__gabe-map__map_status` settles the center half — honest-empty, with its reason, where there is none) | P1–P3, P10, plus any the config names |
| Plain git repo | `git rev-parse` succeeds | P2, P3, P10 |
| Not a git repo | — | STOP: `pulse: not a git repository — nothing to measure` |

**Ledger location.** P1 needs a ledger. Resolution order, first hit wins:

1. `--ledger <path>` on the command line
2. `.kdbp/LEDGER.md`
3. the center config's `paths.ledger`, if declared

A repo with none of these reports P1 as `undetermined — no ledger surface` and continues.
This is the R8 case: the suite repo carries no `.kdbp/`, so its ledger is config-named.

### 1.2 Modes

| Invocation | Behavior |
|---|---|
| `/gabe-pulse` | full banded report |
| `/gabe-pulse brief` | headline + roster line only; no table |
| `/gabe-pulse --json` | machine output, schema in §4.3; suppresses all prose |
| `--since <ref>` | passed to P1 verbatim; narrows the commit range |
| `--bookkeeping <prefix>` | repeatable; passed to P1 verbatim |

Unknown arguments are an error, not a silent ignore: `pulse: unknown argument: <x>` and STOP.

## §2 The ten signals

Every signal is deterministic and costs zero LLM calls. Run them in this order; none depends
on another's result, so a failure never cascades.

### P1 · Unregistered commits — EVIDENCE

```
bash <skill>/scripts/ledger-gap.sh --json [--since <ref>] [--ledger <path>] [--bookkeeping <p>]...
```

Exit `0` clean · `2` gap · `1` undetermined. **Exit 1 is not clean** — surface the `reason`
field verbatim. Row text: `N unregistered commits · M bookkeeping excluded`. The bookkeeping
count is always shown when non-zero; the filter is never allowed to shrink the number silently.

Evidence: the JSON's `baseline` and `registered_hashes`. Clearing command: `/gabe-commit`
for future work; for the existing gap, a ledger row or an accepted decision to leave it.

### P2 · Uncommitted changes — EVIDENCE

```
git status --porcelain
```

Count tracked modifications and staged entries. **Untracked-only does not fire** — matching
`stop-session-reminder.sh`, so the two surfaces never disagree about what "dirty" means.
Row: `N uncommitted paths`. Clearing command: `/gabe-commit`.

### P3 · Unpushed commits — SHIP

```
git log --oneline @{u}..HEAD
```

No upstream configured → `undetermined — no upstream for <branch>`, not clean. Row:
`N commits ahead of <upstream>`. Clearing command: `/gabe-push`.

### P4 · Router's next step — LIFECYCLE

```
node ../gabe-next/scripts/next.mjs --json
```

`mcp__gabe-kdbp__next_beat` relays this same script with its exit codes mapped to fields — ask it first; the node invocation above stays for a repo where the server is not registered. Report its decision **verbatim**. Exit `1` → its terminal message (no plan / plan complete)
becomes the row. Exit `2` → `undetermined — PLAN.json unusable`.

Pulse never re-derives this. Two readers of PLAN cells that disagree is a second source of
truth, and the router is the one the lifecycle already trusts.

### P5 · Prior-phase debt — LIFECYCLE

From the same `next.mjs --json` payload: its prior-row sweep. Row lists phase ids and which
cells are outstanding. Clearing command: the beat each cell names.

### P6 · Center coverage — LIFECYCLE

Phases whose `Center` cell is `⬜` **and** whose `Push` cell is `✅` — shipped but uncovered.
Read the cells from `mcp__gabe-kdbp__kdbp_snapshot` `plan.phases[]` (header-resolved, so an optional
column is never read off a shifted position; each cell arrives as `todo` / `active` / `done` / `skipped`,
not the raw glyph — `⬜` is `todo`, `✅` is `done`, `n/a` or `⏸` is `skipped`). Its list caps at 40 rows and
names the cap — count a longer plan from `.kdbp/PLAN.md` itself, since a capped list is not an absence
proof.
Column absent → `unavailable — no Center column` (normal, not a defect). Clearing command:
`/gabe-cc-update <phase>`.

### P7 · Red debt — LIFECYCLE

Phases whose `Red` cell is `⬜` **and** whose `Exec` cell is not `⬜` — executed without a
committed red checkpoint, read from `mcp__gabe-kdbp__kdbp_snapshot` `plan.phases[]` (header-resolved;
cells arrive as `todo` / `active` / `done` / `skipped`, not the raw glyph — `⬜` is `todo`; capped at 40
rows with the cap named — a longer plan is counted from `.kdbp/PLAN.md`).
Column absent → `unavailable — no Red column`. Clearing command:
`/gabe-red <phase>`.

> A phase with `Red ⬜` and `Exec ⬜` is not debt — it is simply not started. Reporting it
> would make every unstarted phase look owed, which is how a report earns its mute.

### P8 · PENDING escalations — AGING

`.kdbp/PENDING.md` rows with `status=open` — `mcp__gabe-kdbp__kdbp_snapshot` `pending.open` is the exact
total and resolves closure the way the file declares it (a Status verdict token or a `<!-- P<n> resolved -->`
comment); its `top` list caps at 10, so the `Times Deferred ≥ 3` tally is still counted from the file.
Report two numbers: total open, and how many sit
at `Times Deferred ≥ 3` (gate-spec's forced-decision threshold). Only the second is a row;
the total is context. Clearing command: `/gabe-review deferred`.

### P9 · Never-walked stations — AGING

Stations declared in the center config that have **zero** entries in `.kdbp/walks.jsonl`.
Never-walked is the reportable state; a stale walk is not pulse's business (the center already
renders staleness). Clearing action: append a walk record to `.kdbp/walks.jsonl` (the `/gabe-walk` skill was archived 2026-07-30; the record format survives).

### P10 · Size-budget breaches — AGING

```
bash ../gabe-commit/scripts/size-budget.sh $(git diff --name-only HEAD)
```

**Pass the file list explicitly.** A bare invocation defaults to `git diff --cached --name-only`
and, with nothing staged, exits 0 having inspected **zero files** — a vacuous pass reported as
clean. The first live run of this skill hit exactly that (2026-07-26). Always state the count:
`clean — N files inspected`. `N = 0` because nothing changed is clean; `N = 0` from a wrong
invocation is not, and only the printed count tells them apart.

Exit `2` = breaches exist. **Advisory only** — R9 makes the 800-line budget report-never-gate,
so this row never reads as blocking and never proposes a fix.

## §3 Ranking and caps

### 3.1 Band order

`EVIDENCE` → `LIFECYCLE` → `SHIP` → `AGING`. Fixed; not re-sorted by count or severity.

EVIDENCE leads because it is the only band where the **record** is missing rather than the
work. Everything in the other three bands describes something the project can still see and
act on; an EVIDENCE gap is the class that disappears.

### 3.2 The headline

One line, above the table: the highest-band row with the largest count, phrased as a fact.
If every signal is clean or unavailable → `▶ nothing owed`. If every signal is *unavailable*
→ `▶ nothing measured — N signals unavailable` (never `nothing owed`; that would be the
absence-of-evidence error the whole skill exists to prevent).

### 3.3 Caps

Five rows per band. A truncated band ends with `… N more`. Within a band, rows sort by count
descending, ties by signal id. **No silent caps** — a cap that does not announce itself reads
as coverage.

## §4 Output contract

### 4.1 Full report

```
PULSE — <project> · <date>

▶ Most important: <headline>

EVIDENCE
  P1  <row text>                                → <clearing command>
  ...
LIFECYCLE
  ...
SHIP
  ...
AGING
  ...

signals: N ran · M unavailable (<id> <reason> · <id> <reason>)
```

Bands with no rows print `clean` on one line rather than being omitted — an omitted band is
indistinguishable from a band that was never checked.

**Findings contract** (`../../gabe-docs/references/execution-contract.md` §"The findings
contract"): the `→ clearing command` is each row's STEP (already mandated). For the LINK half,
a row that names a specific file or the artifact it read renders it as a clickable
workspace-relative link — **P8** links `.kdbp/PENDING.md`, **P10** links each over-budget file
(`size-budget.sh` prints them), **P1** links `.kdbp/LEDGER.md`, **P9** links `.kdbp/walks.jsonl`,
and any signal naming a path links it. A bare count-plus-command row (P2 `N uncommitted paths`,
P4/P6 phase ids) carries no link — a count has no single location and the command is the move.
Pulse is deliberately command-first; linkify only where a real file is named, never a count.

### 4.2 Brief

Headline plus the roster line. Nothing else.

### 4.3 JSON

```json
{
  "project": "<name>", "generated": "<ISO date>",
  "headline": "<text>",
  "bands": { "EVIDENCE": [ {"id":"P1","text":"…","command":"…","count":73,"evidence":"…"} ], … },
  "roster": { "ran": 8, "unavailable": [ {"id":"P9","reason":"no walks.jsonl"} ] }
}
```

`generated` is the date the run happened, read from the environment — never fabricated.

## §5 Degradation table

| Signal | KDBP project | Center-only repo | Plain git repo |
|---|---|---|---|
| P1 unregistered | yes | yes, if `paths.ledger` | no — `no ledger surface` |
| P2 uncommitted | yes | yes | yes |
| P3 unpushed | yes | yes | yes |
| P4 router | yes | no — `no PLAN.json` | no |
| P5 prior debt | yes | no | no |
| P6 center | if `Center` column | no | no |
| P7 red | if `Red` column | no | no |
| P8 pending | yes | no — `no PENDING.md` | no |
| P9 walks | if walks.jsonl | if walks.jsonl | no |
| P10 size budget | yes | yes | yes |

In this repo (suite, R8 — no `.kdbp/` by ruling) pulse resolves **P2, P3 and P10**, and
enumerates the other seven as unavailable with reasons. That is the intended behavior, not a
degraded one: the suite's open moves live in the board's sources, and pulse says so rather
than pretending to measure a lifecycle that was deliberately not adopted.

**P1 is unavailable here, by decision.** `suite-center.config.json` declares no `paths.ledger`
and will not: `/gabe-commit` writes rows into `.kdbp/LEDGER.md` and is KDBP-gated, so nothing
in this repo would ever write a ledger. A declared-but-unwritten ledger would flip P1 from
`no ledger surface` to `no baseline` — configured-looking and measuring nothing, which §7
forbids. Operator ruling 2026-07-26: accept P1 as unavailable here. Revisit only if something
starts writing ledger rows in this repo, which would mean revisiting R8 itself.

> An earlier draft of this section claimed P1 resolved here. The first live run of the skill
> disproved it. Kept as a note because the failure mode — a spec asserting a capability its
> own environment cannot provide — is the one E1 exists to catch.

## §6 Seams

Checked against the adjacent specs at authoring time (CLAUDE.md's handshake-walk rule).

| Neighbor | Seam | Resolution |
|---|---|---|
| `/gabe-next` | both read PLAN cells | pulse **calls** `next.mjs --json` — directly, or through `mcp__gabe-kdbp__next_beat`, which relays that same script — and quotes it; it never parses cells itself for P4/P5 |
| `/gabe-health` | both survey the project | health = code condition (god files, churn, coupling); pulse = lifecycle completeness. No overlapping signal |
| `/gabe-review` | both surface owed work | review prices and triages a diff; pulse counts and points. Pulse never opens a finding |
| `/gabe-commit` | both read the LEDGER | commit **writes** rows; pulse only subtracts against them. Pulse writes nothing |
 | walks.jsonl records | both read walks.jsonl | walk records land by hand or via /gabe-cc-init approvals; pulse counts never-walked. Pulse never appends |
| `stop-session-reminder` hook | both define "dirty" | identical rule — tracked modifications only, untracked-only does not fire |

## §7 What pulse must never become

Recorded because the suite has already made this mistake once: the LEDGER per-tool-call writer
was retired in A2 KDBP-lite after it filled a real project's ledger with five garbage rows from
`[pre-flight]` and `[classifier]` output lines.

- Never fires automatically. Human-invoked only.
- Never writes. The moment pulse records something, it becomes a source of truth that can
  disagree with the ledger it reads.
- Never lists more than the cap. A 40-row report is a muted report.
- Never reports a clean signal as a row. Bands print `clean`; individual clean signals do not
  earn a line.
- Never converts an `undetermined` into a `clean`. That is the absence-of-evidence error, and
  §12 PROXY EVIDENCE names it as the suite's dominant recurring failure class.


## §5 ANGLE signals — which satellite would find something

Added 2026-07-31. The measured problem: **fifteen of the suite's twenty-eight skills have
nothing that fires them**, and an operator working the router-dispatched spine never meets them.
The rejected fix was a "consider /gabe-roast" line in each beat — a line that prints every run
carries no information about THIS run, and the eye learns to skip the tail of a report.

So a satellite earns its line only when repo state says it would find something. Computed by
`scripts/angles.py`, which is deterministic, read-only, and reports an uncomputable signal as
**unavailable with its reason** rather than staying quiet.

### 5.1 The signals

| id | Fires when | Surfaces | Source |
|---|---|---|---|
| S1 | ≥3 phases done and no roast RECORD in recent commits (`gabe-roast`/"roast" — review prose saying "adversarial" is NOT a reset; measured false-silence 2026-08-07) | `/gabe-roast Sweeper "<goal>"` — pasteable verbatim: perspective included, goal clipped at a word boundary, quote closed | PLAN.json + `git log` |
| S2 | ≥25 commits since the last scan RECORD (`gabe-health`/"structural scan"/"health scan" — loose words like "churn" collided with ordinary prose and silenced a full cycle; measured 2026-08-07) | `/gabe-health` | `git log` |
| S3 | a reviewed phase declares `proof_type: journey\|visual` and carries no `proof` | `/gabe-myopic` | PLAN.json |
| S4 | a doc page is older than the markdown it was rendered from | `/gabe-docsite` | `scripts/checkers/docsite-staleness.sh` |
| S5 | files changed outside the current phase's declared `scope` (see 5.4) — unavailable, honestly, when the phase declares no scope | `/gabe-scope-change` | PLAN.json `phases[].scope` + shared work-scope resolver |
| S6 | ≥3 changed files belong to one entity's code map (clean tree ⇒ the diff source walks back past pure-`.kdbp` bookkeeping commits to the newest WORK commit — beat ends land right after the tick commit, which blinded the old `HEAD~1..HEAD` fallback; measured 15/15 silent, 2026-08-07) | `/gabe-cc-entity <slug>` | center config + `git diff` |
| S7 | the diff spans ≥2 layers across ≥3 files | `/gabe-imagine` | center config + `git diff` |
| S9 | the entity model diverges from its code — TWO ARMS (entity models Phase 3, 2026-09-06): **A** a DETACHED domain no *domain* entity owns, recomputed fresh from the archmap; **B** the ASPECTS the emitter MEASURED (gate fan-in rows + proposed ASPECT verdicts) read from the committed c4 `models` block, `aspects: not_emitted — regen to know` inside the line when the block is missing. The STANDING reminder; `/gabe-review` catches the NEW route on the diff. See 5.6 | `/gabe-cc-init rank` | arm A: committed `archmap.json`, recomputed fresh (`entity_shape.py`); arm B: the committed `c4-graph.json` `models` block — as fresh as that regen, and says so |
| S13 | a route or backend `.py` sits in a scanned code dir that no entity's config claims (the model-census ruling widened to routes + backend files). The STANDING reminder → `/gabe-cc-init`; closest-to-the-request-path file leads via the reach hop. `route_census`/`file_census` are emitted non-empty-only, so their absence is full coverage — silent, never a false nag | `/gabe-cc-init` | committed `archmap.json` `route_census` + `file_census` (built by `_a3_code.route_census`/`file_census`, reach by `_a3_graft.reach_arm` — nothing stored, nothing globbed here) |
| S14 | a codebase-map generator arm's ACTIVE missed edges (grep found what the map did NOT, tallied per edge, `count` = persistence) crossed the breadth threshold — the map keeps diverging from grep during real dev. The **one accumulator-backed angle** (a delta cannot be re-derived without re-running grep), but the active/cold split is computed FRESH (commits since `last_n` vs the horizon) so a fixed/dormant arm self-silences — nothing that can go stale is stored. Emitted at red/execute/review, tallied by `/gabe-commit`'s sweep (map-delta loop 11a) | inspect `.kdbp/map-deltas-rollup.jsonl` → improve the arm | the `.kdbp/map-deltas-rollup.jsonl` tally ledger (edge-keyed on `(gen, subject, file)`, dedup + `count`; the deliberate stored-tally exception, tier computed) |
| S15 | frontend classification residue — a Pascal .tsx function/class export with no JSX of its own and no file rendering it carries the honest kind `fe-unknown` (never a `module` claim; a rendered-by hit promotes it to component), read from the committed c4-graph `stats.fe.by_kind` (O1, 2026-09-03) | universe legend → Unknown (FE): render it somewhere, or add the O3 proof; residue 0 after O2 on the example | — |
| S16 | workflow coverage — screen-reachable endpoints no curated workflow (`workflows.js`) names, counted by the curate-workflows drafter's analysis over the committed `c4-graph.json` (read-only, nothing stored; infra + BOOT never counted); fires at ≥3 uncovered, or when `workflows.draft.js` still carries a proposal nobody moved into `workflows.js` — the REVIEW is owed, not the run; honest-empty without endpoints or without the drafter script | `/gabe-cc-update curate-workflows` · universe → workflows tab → drafts |  |

Thresholds are deliberately coarse. A threshold tuned to fire often is a threshold that will be
ignored, and an ignored signal is worse than none because it also teaches the reader to skip the
line beside it.

### 5.2 The one-line mode — what the beats print

Every spine beat (`plan · red · execute · review · commit · push`) ends by running
`angles.py --one-line` and printing its output verbatim. It emits **at most one row**:

```
PULSE: 6 phases done, no adversarial pass on this plan → /gabe-roast Sweeper "the docs merge"
```

and **nothing** when no trigger fires. There is deliberately no all-clear line: a beat that ends
with a reassurance every run has re-invented the noise this replaces.

### 5.3 Decay — how a true signal avoids becoming wallpaper

Each offer is appended to `.kdbp/PULSE.jsonl` as `{ts, id, hash, text}`, where `hash` covers the
signal id AND its evidence text. Offered **twice** on the same evidence without the condition
clearing ⇒ suppressed until the evidence changes. Repos with no `.kdbp/` degrade to stateless
mode: the signals still fire, decay simply does not apply, and that is stated rather than hidden.

**Kill condition for this whole mechanism.** If the line is offered ten consecutive times and
taken zero times — measurable directly from `PULSE.jsonl`, since a taken suggestion clears its
own condition — it is noise, and it gets deleted rather than tuned. The same discipline the Gabe
register holds over itself.

### 5.4 S5 — scope drift, computable since the scope mirror (ruling 2026-08-07)

The trigger is *files changed outside the current phase's declared scope*. It was unavailable
until `/gabe-plan` began mirroring the phase's Scope bullet to `PLAN.json` `phases[].scope`; S5
now compares the changed files (from the shared work-scope resolver — the same diff source S6/S7
use) against that phase's scope globs (`*` does not cross `/`) and fires on the ones outside it.
A phase that declares **no** `scope:` field still reports unavailable — honestly, naming the
missing field — rather than falling back to a `types` proxy that would compare a category against
a path and be wrong in both directions. The rule held: no proxy nobody could trust; the signal
waited for real data, then lit up when the data arrived.

### 5.5 Which satellites deliberately have NO trigger

`/gabe-lens` · `/gabe-meme` · `/gabe-artifact` answer "help me think / help me see" — no repo
state predicts them, and a guess would spend the reader's attention on nothing.
`/gabe-help` addresses repo visitors, not the loop. `/gabe-scope` fires on new projects, which is
not a state a beat can observe. `/gabe-next` is the thing you call. `/gabe-handoff` is already
Stop-hooked. `/gabe-pulse` is this engine. **Wiring all fifteen would cheapen the six that mean
something** — the roster stays honest by leaving these out loud.

### 5.6 S9 — entity-shape drift (the standing model reminder)

The entity model is a set of DOMAIN aggregates (recipe · cooking · …). Two ways it drifts from
the app's real URL structure, both of which misdirect a workflow trace:

- **Detached domain (arm A)** — a URL surface (`/settings`) that no domain entity owns; it falls to a
  cross-cutting aspect, so tracing "the settings workflow" lands in the wrong entity. (The JSON key
  stays `orphans` — a contract three callers read; the reader-facing word is *detached*, ruling R10.)
- **Aspect (arm B, entity models Phase 3 — 2026-09-06)** — a cross-cutting concern the EMITTER measured:
  a gate on ≥3 URL domains' endpoints (`_a3_models` gate fan-in — the detector that measured 23/24 and
  34/41 on the twins) or a declared entity the proposed view judged ASPECT. The old single-arm phrase
  "co-claims ≥3 URL domains, solely-owns ≤1" is RETIRED from the line (URL co-claim and screen co-fetch
  are not the detector); `entity_shape.py`'s aspect rule STAYS because review's diff classification
  (`owned` vs `aspect_set`) depends on it — its module HAZARD note says so.

**Division of labour with `/gabe-review`.** Review DETECTS a new route in an orphan domain on the
diff that introduced it (fresh, real-time — the Step 3.4 subject ENTITY-SHAPE DRIFT). S9 is the STANDING
reminder for a drift that already exists and survives the reviewing session — the same
review-detects / pulse-nags split S8 uses for census capture debt.

**Arm A stores nothing; arm B is exactly as fresh as the committed c4 and says so.** Arm A recomputes
the URL↔entity cross-tab from the committed `archmap.json` on every beat via `entity_shape.entity_shape()` —
no `entity-drift.json` to write at regen and read stale (operability ruling 2026-08-14). Arm B reads the
aspects the emitter already measured from the committed `c4-graph.json` `models` block: when the block is
missing the line carries `aspects: not_emitted — regen to know` beside whatever arm A found, so a
half-signal never reads clean; when the emitter ran and found no derived view it carries the reason.
The evidence-text hash changes with the two-arm wording, so S9 re-offers twice on suppressed repos (§5.3) — expected. Unavailable, honestly,
when there is no center config or no archmap yet. Candidate names for an orphan come from an
optional `url_domain_map` in `center.config.json` (`{segment: name}`, e.g. `settings → account`);
absent an entry, the candidate is the verbatim segment.
