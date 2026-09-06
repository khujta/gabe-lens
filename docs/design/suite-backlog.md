# Suite backlog — considered, not acted on

> Things this suite has DECIDED are worth thinking about and has deliberately NOT built.
> Opened 2026-07-26 at the end of the board + guard arc, so the reasoning survives the
> session that produced it.
>
> **Nothing here is a commitment.** An entry earns its place by carrying the evidence that
> made it interesting — a measured number, a named finding, a real failure — because the
> cost of re-deriving that later is what makes a backlog rot. An entry with no evidence
> should be deleted, not kept.
>
> Companion records: [`trim-ledger.md`](trim-ledger.md) (what was removed and why),
> [`verification-first/README.md`](verification-first/README.md) (the landed model),
> [`../investigations/2026-07-25-board-spike/`](../investigations/2026-07-25-board-spike/)
> (the board's design record).

## Open

| # | Item | Why it is here | Evidence | State |
|---|------|----------------|----------|-------|
| B1 | **`/gabe-red` — scope is too narrow** | Operator-flagged 2026-07-26: flaws and over-narrow scopes in the red beat, testing-related. A dedicated session is planned to state them. | Operator, from live use on gustify. Specifics not yet written down — **this row is a placeholder for that session, not a finding.** | **NEXT SESSION** — do not pre-empt; the point is to hear the operator's cases first |
| B2 | **Propagate board + guard to both twins** | Everything built 2026-07-25/26 is suite-only by instruction. | 9 commits: board station, guard lens, 4 generator modules, `board.js`, `a3.css`, 3 vendored fixes. | **DEFERRED** by operator — see *Propagation shape* below |
| B3 | **`proof_type: property`** | Plans declare `proof_type` (`test\|visual\|journey`) and `/gabe-red` reads it. For a hard-exclusion SAFETY rule (allergen wall, auth boundary, money) example-based tests are the structurally wrong tool: the rule is a claim about an input SPACE, not about twenty points in it. | gustify testing review 2026-07-25, gap #5: "SC-03/REQ-07's acceptance is unimplemented… you want generated adversarial inputs". Named as one of the two they would add if they could add only two. | **NOT STARTED** — small (vocabulary + one branch in red-spec), high leverage |
| B4 | **A review family for "a green that cannot go red"** | gustify gaps #2 and #7 are one family: framework config that hides reds, and a scheduled guard red so long it is ignored. | #2: no `afterEach(cleanup)` (every component stayed mounted); `__regression__` excluded when `CI=true` → "CI green" ≠ "suite green". #7: nightly watchdog red **5 consecutive nights**. | **NOT STARTED** — split it: the deterministic half (a CI-conditional exclusion is greppable) is a checker; the judgment half ("deliberate or accident?") is one paragraph of review-spec. gustify's own exclusion was DELIBERATE, so automating the verdict would be wrong |
| B5 | **Per-gate red streaks in the center** | A permanently-red signal is indistinguishable from a real regression, so it stops being read. | `run-history.jsonl` records `{source, totals, ts}` — totals only. The center can say "7 runs recorded" and cannot say "this gate has been red 5 nights". | **NOT STARTED** — cheap; the history file exists, it needs a per-gate field rather than a rollup |
| B6 | **Option D — widen gastify's entity registry** | Guard/board attribution is capped by the registry, not by the matcher. | Unattributed app-code rows repeatedly name `settings` (7), `groups` (6), `reports` (4), `retention` (3), `items` (3), `insights` (2) — real product domains with no entity. gustify's residual gap is prose in PENDING's `File` column instead, which no adoption fixes. | **EVALUATE AT PROPAGATION** (operator) — recommended for gastify, recommended AGAINST for gustify |
| B7 | **Uncommitted work is invisible to every git-based detector** | `ledger-gap.sh` subtracts against `git log`, so work that was never committed leaves no trace for it to find — and that is the purest form of the problem it was built for. | Measured 2026-07-26 across 70 sessions: **9 sessions changed 113 files and produced no commit at all**. Archetypes: gustify 2026-07-10 (32 files, 0 commits, *"focus on the match batch. I don't understand…"*), gabe-lens 2026-07-14 (21 files, 0 commits). Only the session transcript sees these. | **NOT STARTED** — the transcript is the only source, and it is the noisier signal (a repo using a different command vocabulary reads as 100% dark; that error was made and corrected the same day) |
| B8 | **No beat reviews work retrospectively** | `/gabe-review` Step 4.75 aligns a diff against the CURRENT phase. Work from three sessions ago, against a phase that never existed, is not a supported input — so `/gabe-pulse` can surface unregistered work but nothing can assess it after the fact. | Gap G4 of the 2026-07-26 absorb analysis. Compounds with G5 below: even if a phase is retro-fitted, its `Red` cell can never honestly be `✅`. | **NOT STARTED** — deliberately: `/gabe-pulse` v1.0.0 reports and points, and whether it should ever sequence the beats is the question its own use is meant to answer |

| B9 | **Docsite → center SHELL MERGE (ruled, next session)** | Operator ruled 2026-07-31 (AskUserQuestion): docsite pages render inside the CENTER's shell — one site, one look. Chosen over nav-bridge and full pipeline-merge. Design pins: (1) the Cifra shell retires, center shell (`docs/center/shell/`) becomes the one chrome; (2) build_docsite.py keeps owning markdown→HTML + diagram-compliance, emits INTO the center shell wrapper; (3) nav: docsite pages join the center nav as a "Docs" section; (4) twin propagation follows the same sync shape as B2; (5) the 5,511-line surface audit executes DURING this merge (what folds into center generators, what stays). | Ruled in the ◌-closure session; push-gates + direction-guard landed the same arc | **NEXT SESSION** — the one remaining ◌ |
| B10 | **`/gabe-commit` CHECK 6, 7, 8 have no script** | The gate-spec calls them deterministic (deferred scan · doc drift · structure), the install ships none — gustify P8 (2026-09-04) hand-rolled the deferred scan twice and the first pass miscounted open rows (64 vs the snapshot's 87) on an unanchored closure regex. | The two hand-rolled runs in one session. | **Deferred until the next gate that hand-rolls the scan** — then: `gabe-commit/scripts/deferred-scan.py <staged paths>` printing the mandated `DEFERRED SCAN:` line with linked rows, or a `pending_matches` tool on gabe-kdbp. |
| B11 | **`review_drift` `tasks` subject — a diff-added `@shared_task` / `@app.task` no dispatch site names** | The sibling of `entity_shape` for worker tasks (the repo-study tool pass 2026-09-06 cut it at the gate). | No study mission runs a review; the detector needs source parsing of the diff (`@shared_task` decorators, `send_task` names) that the map server does not do — it belongs beside `entity_shape.py --diff` in gabe-pulse. | open — trigger: a twin phase adds a Celery/ARQ task |
| B12 | **`fetch_bridge.diff_new_fetches` — comment/docstring/template literals count as fetches** | Both study repos' center-install commits produced phantom `GET /x` rows from the shell's own prose; gabe-map's `review_drift` now drops hunks under `docs/site/center/` and `generators/` (F12), but pulse S10 and `/gabe-review`'s WEB-BRIDGE DRIFT read the same function unfiltered. | tier0/tier3 `review_drift base=HEAD~1` before F12: `new_fetches [['GET','/x']]` from `templates/center/shell` prose. | open — trigger: the next twin commit that touches the center and trips S10 |

## Live consequences worth remembering

Not tasks — properties of what shipped, which a future session will otherwise rediscover.

- **`named` is not `guarded`, and most of the estate is `named`.** The guard lens joins NAMES;
  whether a naming case can FAIL is a separate fact that exists only after
  `skills/gabe-red/scripts/prove-guard.py` has been run. With zero proofs on record:
  gustify **0 guarded · 37 named · 139 unguarded**, gastify **0 · 18 · 82**. This is
  deliberate — a twin measured its own void rate at **1 in 6** — but anyone reading the
  center for the first time should know the zero is honest, not broken.
- **`prove-guard --run` must be narrowed to one case.** A suite-wide run makes an unrelated
  failure look like proof, and the script cannot tell the difference. This is its one way
  to lie.
- **The first post-propagation diff will be mostly noise.** `sort_keys` reorders the whole
  archmap once (#150) and every `guarded N/N` becomes `named N/N`. Land it on its own.
- **Retro-absorption can never honestly claim RED (gap G5).** `plan-proof-guard` blocks a phase
  whose `red` cell is done without a reachable `red@<sha>` and a non-empty cases record.
  Absorbed work was written *before* its tests by definition, so a retro-fitted phase must record
  an enumerated skip or a GUARD — never a `✅`. This is the guard working correctly, and it caps
  what any "absorb into the plan" design can produce. Do not discover this at the first block.
- **`/gabe-pulse` P1 is unavailable in this repo, by ruling (2026-07-26).** Nothing here would
  ever write a ledger — `/gabe-commit` writes into `.kdbp/LEDGER.md` and is KDBP-gated, and R8
  keeps `.kdbp/` out. A declared-but-unwritten `paths.ledger` would flip P1 from `no ledger
  surface` to `no baseline`: configured-looking, measuring nothing. Accepted as unavailable;
  pulse resolves P2/P3/P10 here and enumerates the rest.
- **Half the raw ledger-gap signal is bookkeeping.** A commit that writes a ledger row cannot
  appear in the ledger it wrote. Measured on real twins: **gustify 73 of 146 flagged, gastify
  116 of 285**. The detector filters commits touching only lifecycle paths (`--bookkeeping`,
  default `.kdbp/`) and always prints what it excluded. Twin-specific prefixes differ — gustify
  also writes `tests/results/*.digest.json` (7 more), gastify does not.
- **A skill missing from the center's beat roster was silently relabelled, not flagged.**
  `_suite_data.py` resolves groups with `beats.get(name, "cross-cutting")`, so adding
  `gabe-pulse` filed it as a contract skill with no error. Now gated by `check_suite_center.py
  --roster-only` (both directions plus duplicates), proven by 8 fixtures in `tests/suite-center/`.

## Propagation shape (B2)

Each twin vendors BOTH the generators and the shell, so a sync is four moves, not a copy:

1. **Generators** → twin `scripts/`: new `_a3_board.py`, `_a3_guard.py`; changed
   `_center_data.py`, `_a3_code.py`, `_a3_feature.py`, `build_center_a3.py`, `next_feature.py`
2. **Shell** → twin `docs/site/center/shell/`: `board.html` skeleton, `assets/board.js`, `a3.css`
3. **Regen**, then read the diff against the notes above
4. **Twin-side follow-ups**: gustify #148/#150/#151 can be closed by the sync itself (the
   fixes are upstream as of `033d82e`); B6 decided per twin

## Working note

`git add -A` in a worktree a parallel session is also writing to swept 58 of that session's
files into two commits (2026-07-26). Split back out with `git commit-tree` against a scratch
index — a rebase would have checked out the working tree and destroyed their uncommitted
edits. **Stage explicit paths when another session is live.**
