# Adopt spec — the binding contract behind /gabe-cc-init

> The one deep home for the adoption tracker, archive rules, the generator-promotion path,
> ranking signals, the section checklist, and walk-recorded approval. SKILL.md carries intention
> + modes and points here; nothing below is restated there.
> Design record & ruling: `docs/design/verification-first/README.md` §5 addendum R7 (suite repo).

## Preconditions (all modes)

- Git repository + `.kdbp/` present — `mcp__gabe-kdbp__kdbp_snapshot` answers both in one call (branch · ahead/behind · dirty · the `.kdbp/` files it found) and says plainly when there is no `.kdbp/` — else exit: `⛔ No KDBP. Run /gabe-init first.`
- `section`/`status`/`rank` require the tracker (`docs/site/center/adoption.json`) — else exit
  with the init pointer. `init` with an existing tracker asks: resume (report status) or
  re-adopt (archives the current center again — rare, confirm twice).
- A project with a center but no tracker is mid-flight history (hand-bootstrapped, n=2 era):
  `init` treats the existing center as archivable inventory like any other doc tree.

## The adoption tracker — `docs/site/center/adoption.json`

Small, append-only in spirit: rows change status, never vanish.

```json
{
  "version": 1,
  "started": "YYYY-MM-DD",
  "archived_to": "docs/_archive/YYYY-MM-DD-pre-adoption/",
  "shortlist_approved": null,
  "sections": [
    {
      "entity": "cook-state",
      "display_name": "Cook State",
      "rank": "critical",
      "status": "pending",
      "checklist": {
        "testing_inventory": false, "legacy_reverified": false, "card": false,
        "diagrams": false, "proofs": false, "gate_green": false,
        "workflow_census": false, "walk_recorded": false
      },
      "signals": "junit 34 hits · churn 12 commits/90d · SCOPE REQ-03",
      "approved_walk": null,
      "notes": ""
    }
  ]
}
```

- `status`: `pending | building | awaiting-approval | approved | covered-by-feature | dropped`.
- `covered-by-feature`: the forward track (`/gabe-cc-update <phase>`) already built this entity's
  section — record the phase id in `notes`, reuse, never duplicate (E4).
- `dropped` requires a reason in `notes`. Rows are never deleted.
- The tracker NEVER lives in PLAN.md and `/gabe-next` never reads it — the main plan keeps
  shipping while adoption proceeds in spare time; both tracks meet in the same center.

## Mode `init`

1. **Inventory** — list what exists, with counts: `docs/**` trees (by subsystem), any
   `docs/site/center/` (hand-built), README-adjacent doc files, mockup/investigation dirs.
   Render as a table: path · files · looks-like (docs system / center / investigation / assets).
   The **path** column renders as a clickable workspace-relative link — **findings contract**
   (`../../gabe-docs/references/execution-contract.md`), which also governs the `rank` candidate
   table's signal-evidence paths below.
2. **Archive picker (checkpoint)** — the operator marks each inventory row KEEP or ARCHIVE.
   Machine sources are never offered for archive: tests, junit/results, `.kdbp/`, root README,
   source code. Default proposal: archive superseded human doc trees + any hand-built center;
   keep investigations referenced in git history.
3. **Archive (on approval)** — `git mv` each ARCHIVE row into
   `docs/_archive/<date>-pre-adoption/<original-path>/`, then write an `README.md` in the archive
   dir: why archived, what replaced it (the center), how to reference (links keep working in git
   history; nothing was deleted). One commit, path-scoped. Same policy as suite skills:
   **archived, never deleted**.
4. **Bootstrap the center shell** from the installed suite `templates/center/`. **The deterministic half of this step is a script (2026-09-06): `templates/center/generators/bootstrap_center.sh <repo> --name <slug>` lands the generators, the shell (minus `example/`), a `center.config.json` skeleton and the `.gitignore` seeds, never a tracker and never over an existing config — run it, then continue with the archive and the tracker below.**
   `center.config.json` skeleton (project name, corpora bindings, results globs from
   `.kdbp/BEHAVIOR.md` `results_out` when present), the generator scripts, assets/shell, empty
   section dirs.
   - **Generator promotion (first-ever adoption only):** if the GENERATOR SCRIPTS do not exist
     in the installed suite's `templates/center/` (the `shell/` skeletons alone do NOT satisfy
     this — shell and generators are independent, and the shell landed first, 2026-07-20),
     init's first job IS the promotion (design record §5: ripe at n=2,
     executed at n=3 with purpose): port the most mature existing center implementation
     — **gastify** (`scripts/build_center_a3.py`, `_a3_render/_a3_feature/_a3_code/
     _a3_evidence.py`, `_center_data.py`, `_center_mermaid.py`, `check_center_links.py`,
     `refresh_center.sh`; it superseded gustify as the reference at the transaction trial) —
     generalize hard-coded paths into `center.config.json` bindings, land them in the SUITE
     repo as `templates/center/`, run the suite's `./install.sh`, and only then bootstrap the
     project. **The promotion writes to the suite REPO, never the app repo:** resolve the suite
     checkout by asking the operator (or the project CLAUDE.md's suite pointer); if the suite
     repo is not present and writable on this machine, STOP —
     `⛔ generator promotion needs the suite repo checked out (templates/center/ does not exist
     yet). Clone the suite, or run init on the machine that has it.` E6: never compose
     generators from memory; if the reference implementation (gastify's scripts) is also
     unreachable, STOP and name both missing anchors.
   - Promoted-generator floor (what the templates must support): C-id extraction from junit
     test names via the anchored token pattern (red-spec §Backfill); **ever-red** per id
     (`git log -S "C<id>"` → first commit → `RED:` trailer present?); `walks.jsonl` → manual
     angles + staleness; honest-gap rendering (`⤫ skipped(no reporter)`, NEVER-walked red);
     **the link/orphan gate ignores `adoption.json`** — it is the adoption tracker, not a
     center-derived page (a gate that WARNs on it would teach sections to delete their own
     state to get green).
   - **Shell / layout contract (the ruled layout — A3 · Tabbed, layout-lab convergence
     2026-07-14):** the bootstrapped shell is the A3-Tabbed shape — a persistent LEFT SIDEBAR
     of section/entity nouns (`class="side"`) + a per-feature FIVE-tab bar (`nav.tabbar`: Overview · Code · Tests · Evidence · Risk — trial-ratified 2026-07-21), the
     hub with its own shell (tabs fit a feature, not the hub). **The shell SHIPS as suite
     templates: `templates/center/shell/` (installed at `~/.claude/templates/gabe/center/shell/`)
     — `assets/` (a3.css incl. the IDENTITY LAYER: landed-map group colors, `.sechead` section
     banners, exclusive icons; plus slots.js, the raw-skeleton slot affordance — inert on
     generated pages) + the FULL station set (`index`/`feature`/`tests`/`board`/`codebase-graph`/
     `entity-index`/`docs`/`ledger`/`releases`.html — `codebase-graph` is the C4
     codebase-graph / change-simulation station, auto-emitted with an honest-empty
     `sim.data.js` + `c4-graph.js` alongside the archmap) with the placeholder contract + the
     station↔sources mapping table in that dir's README. The INVARIANT chrome ships in the
     skeletons (colored+iconed station sidebar per the RULED NAV — map v3, merged 2026-07-21 —, tab icons, `data-sec` section identity);
     generators fill only the project-specific slots the README lists. Every crucial section is
     generated FROM its skeleton — a section page built from scratch instead of its template is a
     defect.** Init copies the shell (incl. `assets/`) and wires the project's generators to fill
     its slots; the shell is independent of the generator promotion (a project's own generators
     may emit into it before the python promotion happens). Decision record: the layout lab's
     README (`docs/investigations/2026-07-14-center-layout-lab/`). **Restoring the archived
     project's legacy shell/css violates the clean-slate ruling — the archive is testimony to
     re-verify, never a source of chrome.** The sidebar's nouns come from the approved entity
     baseline (rank), not from the archived nav.
5. **Write the tracker** (`sections: []`, `shortlist_approved: null`) and report (E7): archive
   manifest, bootstrapped paths, the `rank` pointer.

## Mode `rank`

1. **Gather signals — every candidate cites machine sources only:**
   - `.kdbp/SCOPE.md` REQs + §Phases entities; `.kdbp/PLAN.md` phases (`mcp__gabe-kdbp__kdbp_snapshot` returns the LIVE phase table — ids, names, per-beat cells, capped with a `+N more` note; the archived plans it does not read, so those stay a file read) **including archived
     plans** (`.kdbp/archive/`); routes/modules (framework route tables, top-level feature
     dirs); test density per entity (where a map already exists, `mcp__gabe-map__center_overview` gives per-entity counts, flow coverage and the entities the registry does not yet carry, and `mcp__gabe-map__cases_for` names the cases already covering a candidate's endpoints/models; corpus grep + junit name matches stay the floor — and the only signal available for a candidate the map has never seen); churn
     (`git log --since=90.days` commits per dir); existing `walks.jsonl` subjects;
     `.kdbp/BEHAVIOR.md` `critical_paths` (hotfix-sensitive globs rank critical by default).
2. **Render the candidate table:** entity · proposed rank (critical/high/medium) · the signal
   evidence per column · what a section would contain (tests found y/n, legacy docs found y/n,
   proofs found y/n). No signal, no row — an entity the machine cannot see is proposed only by
   the operator. Every file/dir path in the signal-evidence columns renders as a clickable
   workspace-relative link (findings contract).
2b. **The URL-domain SECOND LENS (advisory, alongside — never replaces the ranking).** When
   `docs/site/center/archmap.json` exists (a re-rank, or after the first bootstrap pass), also
   ask `mcp__gabe-map__entity_shape` (it loads that same `entity_shape.py` module against the committed map and returns the shape plus its one-line finding; `python3 ~/.claude/skills/gabe-pulse/scripts/entity_shape.py .` is the fallback when the server is not registered) and present its output beside
   the candidate table: **orphan domains** (a URL surface no proposed entity owns — a candidate
   entity the churn/test ranking may have missed, named via the optional `url_domain_map`) and
   **aspect entities** (a candidate that co-claims many URL domains and solely-owns almost none —
   likely a cross-cutting concern, not a peer domain; flag it so the operator rules it in
   knowingly, not by accident). This lens ADVISES; the operator still rules the shortlist
   (2026-07-21 baseline). Honest-skip with one line — `URL-domain lens: no archmap yet, re-run
   after the first section adoption` — when the archmap is absent (initial greenfield rank).
3. **Checkpoint:** the operator trims, re-ranks, adds, drops. On approval: write one
   `sections[]` row per shortlisted entity — `status: "pending"`, `rank`, `display_name` (one
   human-facing word, e.g. `"Transaction"` — D123: the registry's rendered name, never left to
   default to the raw slug), `signals` (the evidence string), `checklist` with ALL EIGHT keys
   `false`, `approved_walk: null`, `notes: ""` — and set `shortlist_approved` to today's ISO
   date (that date IS the truth test `section`/`status` check). Report. Re-running `rank`
   later APPENDS new candidates; approved rows are never re-ranked silently.

## Mode `section <entity>`

**One entity per run — refuse batching** (`⛔ one section per run — human-speed review is the
point`). Preconditions: shortlist approved — else exit
`⛔ Shortlist not approved. Run /gabe-cc-init rank and approve it before building a section.` —
and the entity row exists and is `pending`/`building`.

1. **Testing inventory** (machine): on entering the build, set the row's `status: "building"`
   (and persist every checklist tick to `adoption.json` AS IT FLIPS — an aborted run must leave
   honest partial state, not a `pending` row with invisible progress). Then: corpus tests
   matching the entity — `mcp__gabe-map__touches <slug>` for the entity's slice once that slug is on the map (an unregistered slug is NOT an entity to the map: detect_kind falls through to a bare-name search, so read the `kind` it answers with) and `mcp__gabe-map__cases_for` per endpoint/model for the C-ids and test files already covering it, THEN grep + junit for what the map does not carry (the map is a FLOOR: no case in an answer is not proof the corpus has none) — counts per corpus (api/web/e2e), angle classification
   (automated angles present; manual angles from `walks.jsonl`; **absent angles NAMED** — the
   gap list is content, not shame). Tick `testing_inventory`.
2. **Legacy mining:** read the archived docs for this entity (`archived_to` + git history).
   Every claim carried forward is RE-VERIFIED against current code/tests before it enters the
   center; claims that no longer verify go to a `Not carried forward` list on the section page
   with one-line reasons. Bulk import is forbidden — a legacy page is testimony, not truth.
   Tick `legacy_reverified`.
3. **Build:** start from the machine surface — `mcp__gabe-map__entity_context <slug> detail=full` returns the entity's endpoints, models, schemas and files-by-layer without re-reading the codebase (the *Machine-surface-first section builds* rail below; an entity the map does not yet carry answers `code: null`, and the corpus is then the only surface) — then the feature card (entity primacy, gabe-cc-update's card contract where applicable),
   diagrams per `gabe-docs` standards (or the card states why fewer), testing page (angles +
   verdicts from machine facts), proofs — curate real shots/artifacts where they exist; absent
   proofs render as named gaps, never staged. Tick `card` / `diagrams` / `proofs`.
   Then the **workflow census** — the card's `# FLOWS` now exist on disk, so run the census ASK
   (`gabe-cc-update` feature-spec §The workflow census): `check_workflow_drift.py` the entity's
   census, then *author* (`scaffold_census.py <root> <slug>` seeds a skeleton from the flows) /
   *extend* / *defer* / *decline*. Tick `workflow_census` once authored or declined-with-reason.
   This step is the WRITER for the 8th key: a back-catalog entity has no phase, so
   `/gabe-cc-update`'s phase-driven census step never reaches it — the adoption ritual must.
4. **Regenerate + gate:** run the center refresh; the link/gate check must be green with this
   section contributing zero WARNs. Tick `gate_green`.
5. **Checklist render + checkpoint:** BRIEF the operator before asking for a verdict —
   per the walk-briefing convention (preserved from _archive/gabe-walk §Procedure step 2) (why this walk · the card's HANDLE/WHAT & WHY · the
   `# FLOWS` itinerary with each flow's proof state, unproven flows called out as "your
   eyes are the only verification" · what pass/partial/fail mean here). An approval
   request without its briefing is a mystery, and a mystery produces a rubber stamp,
   not a witness. Then show the checklist, the built page paths, the dropped-claims
   list. Operator verdict:
   - **approve** → append the walk record to `.kdbp/walks.jsonl` — subject `adopt:<entity>`, result pass (who·when·evidence = section
     path); store the walk timestamp in `approved_walk`; status `approved`. Tick
     `walk_recorded`.
   - **changes** → status `awaiting-approval`, notes carry the asks; next run resumes here.
   - **park** → status stays `building`, notes say why.
6. **Report (E7):** paths, checklist, tracker row, and the walk line verbatim on approval.

## Mode `status`

Read tracker + `walks.jsonl` — the tracker stays the authority for per-section checklist glyphs and walk age; `mcp__gabe-map__entity_context` with no slug returns the registry rows (slug · display_name · rank · status · mapped) and `mcp__gabe-map__center_status` relays the forward track's own actionable list, which names cardless entities and cards whose `# REVIEWED` stamp is MISSING — the first look for the reconciliation below, never its proof: the list carries no positive roster of stamped cards, is relayed capped at 6,000 chars (`truncated: true` when cut) and answers a `reason` instead of a list when the suite's generator is not installed, so an entity absent from it is not thereby stamped. Before offering `covered-by-feature`, open that entity's card under `cards/` and confirm the `# REVIEWED` line. Render the board: per-section status/checklist glyphs, approved
n/of-shortlist convergence, stalest approved section (walk age), suggested next entity (highest
rank still pending). **Reconciliation with the forward track:** a `pending`/`building` section
whose entity already carries a `# REVIEWED`-stamped center card (built by `/gabe-cc-update`) is
listed with an offer to mark it `covered-by-feature` (phase id into `notes`) — reuse, never
rebuild (E4). That offer is the ONLY write `status` may make, and only on explicit accept.

## The post-trial contract (transaction trial, absorbed 2026-07-21)

The gastify trial carried one entity end-to-end; these rulings now BIND every section build.
Deep homes: the shell README (tab set, nav contract, css/behaviour vocabulary) and
feature-spec (card contract). This section states what adoption must OBEY.

- **Ownership rule:** the skeleton owns the tab set and nav groups; the generator owns the
  sections inside a pane — and every generator-emitted section carries `data-sec` (via
  `sechead(sec_id=)`). Feature pages are generated from REGISTRATION DATA (config + registry +
  card + machine sources); entity #2 is data, never new page code.
- **D123 — `adoption.json` is THE entity registry.** One vocabulary: rows carry `display_name`
  (rendered on nav, pages, and the map — one fact, one word); every per-entity mapping keys on
  a registry slug and the build ABORTS on unknown slugs; the sidebar is driven from the
  registry (adopted → feature-page link; pending → muted + tracker state chip).
- **archmap — the read-once rule.** The build reads the whole application ONCE per run (ast,
  no LLM; context reads are expensive) into committed `archmap.json`; every consumer — the
  Code tab, the app-wide **Architecture station** (`architecture.html`, built whenever
  `center.config.json` sets `build_architecture: true` — `render_architecture()` in
  `build_center_a3.py` renders it straight from archmap.json), any section needing
  architecture facts — reads the MAP, never the codebase. Committed so a PR diff of it IS
  the architecture change. The map also carries the two INSIGHT blocks — `model_insight`
  (per documented class: usage on both axes, base/god flags, closest structural
  twin) and `function_insight` (the same signals function-shaped, per mapped def) —
  computed by the same build pass off the same cached parses: no extra step, no authored
  input; agents read the signals here instead of re-deriving them — served as tools by `mcp__gabe-map__entity_context` · `touches` · `find` · `outline`, and the map stays a FLOOR: absence in an answer is never proof of absence, `grep -rn` is. `rows-seen.json` sits
  beside it as the second committed
  machine-state file: the per-row snapshot the NEW-badge layer diffs against (baseline =
  the snapshot at HEAD, so iteration boundary = commit boundary; regens inside one
  iteration badge identically, and the commit landing the snapshot wipes-and-restamps by
  construction). Both are generator-owned — never hand-edited.
- **Ephemeral/accumulator is a REQUIREMENT per tab:** Overview=card/growth · Code=card
  `# CODE`/archmap renders · Tests=**testing claim card (`# CLAIMS`, one
  `class — intent` line each; `claim_verdicts()` in `_a3_feature.py` joins each claim by the
  class NAME the card names and checks it still runs in junit — the cases' C-ids are read
  for DISPLAY, not the join key; a claimed class not running renders as drift, a name
  matching several classes as ambiguous, and if junit is incomplete the verdict is
  withheld)**/matrix ·
  Evidence=`manifest.json` per set/disk walk · Risk=card
  `# RISKS`/derived GAP rows. The CENTER's own accumulator is `run-history.jsonl` (one line
  per build: ts · source · totals — `append_history()` in `build_center_a3.py` appends it
  every regen a source's totals moved, capped at 50 rows; reader + named gap render
  alongside).
- **Machine-surface-first section builds:** a section starts from endpoints + models + junit
  inventory; legacy cards are supporting testimony (the six-card reorganize method produced a
  page narrower than its own evidence).
- **Anti-curation additions:** reference material is NOT evidence (path-matched `ref/`,
  `storybook`, `mockup`, `design` — held out per FILE and SAID: "N reference artifact(s) held
  out"); a false gap is as dishonest as a false pass (verify the CLAIM against disk, not the
  render); every angle carries BOTH prices (growth = cost to close; risk = cost to leave
  open; GAP rows link their growth row); a severity needs its stake (4-field RISKS grammar);
  a card must not restate a number the build can read; every truncation carries its expander;
  every chrome number links to a section that leads with it; one fact, one word.
- **Verification reach:** BEHAVIOR.md Verify Commands MUST include the center's own tests — `mcp__gabe-kdbp__verify_commands` returns the binding as it stands (the BEHAVIOR section first, manifest candidates otherwise; it never runs them and never guesses a flag), so the gap is read, not remembered
  (e.g. `uv run pytest ../tests/center --junitxml=../tests/results/center-junit.xml` +
  results_out entry) — the trial shipped 49 tests reachable by neither the local gate nor
  push-to-main CI. The shell JS layer ships only with its committed harness — the suite's
  `templates/center/verify_center_chrome.mjs` (FIRE/silent-proven by `tests/chrome/run.sh`),
  which propagates with the generator promotion and runs against the built pages.

## Non-goals

- No forward-track coverage (`/gabe-cc-update` owns shipped phases + the PLAN `Center` cell).
- No standalone doc placement (`/gabe-docsite`), no scope/plan edits, no deletion — ever.
- No auto-approval: a section without its walk record is not approved, whatever the prose says.
- No synthesized history: the section's changelog derives from git; adoption never backdates.

## Model census — the config decides ownership, never existence

`center.config.json` is a double allowlist: an entity lists its model FILES (`code.models`) and
its model CLASSES (`models`). Operator ruling (2026-08-27, gustify): a table class in an unlisted
file, or filtered by the class list, must NEVER vanish from the map. The build now scans every
`.py` in the model directories for classes with a string `__tablename__` and reports the ones no
entity claims as `archmap.json → model_census.unclaimed` (`{cls, table, file, reason}`); their
write/read access wires still land (the C3 arm mints them into the `__unclaimed__` bucket).

Rails, so no session has to remember it:
- **`rank`** — the candidate table MUST list `model_census.unclaimed` (count + names — read it with `mcp__gabe-map__map_census kind=model`, the same archmap block capped and named, with each entry's `reason` intact) as a claim
  column; an entity is not approvable while a table class its handlers write sits unclaimed.
- **`section <entity>`** — the checklist gains one line: *every table class this entity's
  endpoints write or read is in its `models` list, and its file in `code.models`* — verified
  against `model_census` (`mcp__gabe-map__map_census kind=model` for the unclaimed list, `mcp__gabe-map__entity_context <slug> detail=full` for the models this entity actually carries), not by eye. A deliberate exclusion (a table hidden from the map on
  purpose) is recorded in the tracker with a reason; silence is never an exclusion.
- **Standing reminder** — pulse angle **S11** prints the unclaimed count at the end of every
  spine beat until the list is empty; `/gabe-review` prices a diff-added table class the same way
  the web-bridge subject prices a stray fetch (follow-on).

## Route + file census — the same ruling, widened to routes and backend files

The model-census ruling extends to two more coverage classes the config used to drop silently.
An entity lists its route FILES (`code.api`) and its backend FILES (`code.services` and any
declared layer); a route-bearing `.py` in an api dir the api list omits loses its endpoints, and
a backend `.py` no code list names loses its functions AND every call touching them (graft homes
by file → entity, so `function_insight` never walks it and the `behind` pill counts fns the walk
cannot reach). The build now scans every `.py` in the API dirs and the backend code dirs and
reports the unclaimed ones as `archmap.json → route_census.unclaimed` (`{file, routes, methods,
reason}`) and `file_census.unclaimed` (`{file, routes, fns, tables, reason, reach?}`). Both keys
are emitted NON-EMPTY-ONLY, so their absence is full coverage, never a stale block. The optional
`reach` on a file entry is the minimum call-hops from a mapped handler — how close the file sits
to the request path, so the closest-to-live file is claimed first.

Rails, so no session has to remember it:
- **`rank`** — the candidate table SHOULD list `route_census.unclaimed` and `file_census.unclaimed` (`mcp__gabe-map__map_census` returns both blocks in one read — `kind=route` / `kind=file` for one at a time — each entry keeping its `reason` and its `reach`)
  (count + the reach-nearest names) beside the model-census claim column; a route file that
  belongs to a candidate entity is claimed into its `code.api`, a backend file into the right
  layer. A claim is the operator's — the census only makes the file visible.
- **`section <entity>`** — when a shortlisted entity owns any unclaimed route/backend file (`mcp__gabe-map__map_census` names them; `mcp__gabe-map__owner_of <path>` says whether the map, the config globs, or nobody claims a given file), claim
  it in the same pass (route → `code.api`, service → the layer list). A file deliberately left
  unclaimed (a runtime not yet on the map) is recorded in the tracker with a reason; silence is
  never an exclusion. **A claim under a layer `code_layers` does not declare is a silent no-op**
  — the build prints a report line naming it; add the layer to `code_layers` (config) so the
  files are read.
- **Standing reminder** — pulse angle **S13** prints the unclaimed route/file count at the end of
  every spine beat until the list is empty (reach-nearest first); `/gabe-review`'s entity-shape
  subject prices a diff-added route landing in an unowned URL domain the same way.

