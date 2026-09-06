# Center shell templates — A3 · Tabbed (the ruled layout, post-trial contract)

The command-center SHELL every adoption builds from. Field-tested end-to-end by the gastify
transaction trial (2026-07-20/21, absorbed at suite `55918c4`); nav contract merged per the
landed map v3. Distribution: this dir installs to `~/.claude/templates/gabe/center/shell/`;
projects VENDOR a copy (their `templates/center/shell/`) as the build input — reproducible per
commit — and improvements loop back HERE via export handoffs. The suite is the source of truth
and the distributor; a vendored copy is never edited ahead of a handoff.

**The shape:** a persistent left sidebar of stations + entity nouns picks a SUBJECT; feature
pages carry the invariant FIVE-tab bar (Overview · Code · Tests · Evidence · Risk); stations are
single-lens pages. Pure-CSS `:target` tabs (`:has(:target)` variant so in-page anchors and
subnav links do not collapse the pane).

## The exemplar — follow it, don't re-derive it

`example/feature-transaction.html` is a SNAPSHOT of the gastify trial's real generated page —
the field-tested output every ruling in this README was shaped on. Open it beside any section
you build: the five tabs, the hide/show behaviours (secinfo ⊕ legends, pmore truncation,
proofset/legset folds, expander rows + cascade), the color encodings (verbs, layers,
severities, type families — each with its legend), the meters, the cid chips, the subnavs, the
diagram picker, the viewer. It renders from the SHIPPED `../assets/` (proof the css here is the
css that built it); proof shots are labeled placeholders (real artifacts live in gastify);
sidebar links open the raw skeletons. **The rules live in the specs; the example of the rules
lives here.** When a rule and the exemplar disagree, that is a handoff finding, not a choice.

## The ownership rule (binding)

**The skeleton owns the TAB SET and the NAV GROUPS; the generator owns the sections inside a
pane.** Overview, Tests and Evidence panes ship BARE (`{{TAB_*}}` only) because their internal
sectioning (order, subnavs, expanders) is generator logic. Every generator-emitted section MUST
carry its identity: `sechead(…, sec_id=)` emits `data-sec="<id>"` on the wrapper — the same
section is identifiable on its station page and, entity-scoped, on feature pages. A section
page built from scratch instead of its template is a defect (adopt-spec).

## Files — the station set

| Template | Role | Tabs |
|---|---|---|
| `index.html` | hub SUBJECT — Overview tab contains `now.recent-changes` + `now.needs-you` | 4 (no Code) |
| `feature.html` | entity SUBJECT — one per adopted entity, generated from registration data | **5** |
| `tests.html` | Testing STATION — estate dashboard: cards (cases · files · claims · untested · corpora & gates) · kinds & coverage app-wide · entity × kind matrix; one `test-*` estate page per section (matrix=cases · files · claims · elements=untested · corpora=machinery) | 1 |
| `board.html` | Board STATION — every open move as a card (tracks: verify · prove · build · debt · arc) re-columned six ways (state · track · entity · effort · age · done) + the clickable phase-sequence strip. Slots: `{{BOARD_KPIS}}` `{{PHASE_STRIP}}` `{{PHASE_JSON}}` `{{BOARD_MODES}}` `{{BOARD_FILTERS}}` `{{BOARD_BOARDS}}`. Rendered in a SECOND pass (after archmap) so cards are priced against this build, not the last one; behaviour in `assets/board.js`. **In-flight overlay (ruling 2026-08-07):** the skeleton loads `inflight.js` (a script sibling — file:// kills fetch), the projection `write-inflight.py` refreshes at every E8 beat tail; build cards + the strip carry the phase's DECLARED entities (plan-time, operator-confirmed; null = never declared renders as absence, [] = explicit none), and the strip detail shows the live declared-vs-touched line when the projection names the open phase | 1 |
| `entity-index.html` `docs.html` `ledger.html` `releases.html` | single-lens STATIONS | 1 |
| `codebase-graph.html` | Codebase-graph STATION (principal top-nav) — the C4 codebase graph (entities + FK edges, from `c4-graph.json`) rendered as the change-simulation lifecycle instrument **in the level-lab grammar** (Lucide icons default, Classic/Solid in the gear · halo-trimmed bowed wires · entity-gradient strokes + flow dots + lane bows · regNode/regEdge selection with hop-depth slider + hover peek · layering law backgrounds→wires→nodes): overlays the change in flight (`window.GABE_SIM`) — touched entities + FK blast radius, four stage lenses wearing the change-graph-lab BEAT overlays (red rings+pills → heat+blast → green flips+amber drift → commit purple), per-piece lifecycle panel; every L2 card + sim piece carries the live DOSSIER (PURPOSE · STRUCTURE · SIGNATURE · TESTED-BY from the emitter's per-node `det` block, capped + honest-empty). Slice 3: JOURNEYS (derived request walks + the SIM change walk, resolve-at-play, toolbar picker + step bar), the 6-deep NAV TRAIL (← in the panel header — travel pushes, plain clicks reset), and the two CORNER BOXES (Legend = beat key + level tail bottom-left · Controls = the gesture grammar bottom-right, starts min; the full-width bottom bar died). Honest-empty (`GABE_SIM=null`) → the plain map + "no change in flight". Loads `./c4-graph.js` (`_a3_graph.emit`) + `./sim.data.js` (honest-empty stub) + `assets/sim-panel.js`. Battery: `tests/codebase-graph`; author-time probes: `example/codebase-graph-station/probes/`. VOCABULARY (legend pass 2026-09-06): methods GET/POST/PUT/PATCH/DELETE + BOOT + TASK roots from the ONE shared `METHOD` roster in `assets/graph-grammar.js` (`--m-boot`/`--m-task` vars; a TASK root wears the `taskMark` queue glyph); a `delivery` card row on `stream` endpoints; providers own `#f08c00` (≠ web). NOT drawn here: the provider class, the `dispatches` wire, the badge families — universe-only | 1 |
| `arch-code-map.html` (Tests column) | carries the GUARD chip per file — `guarded N/N` or `unguarded N/M`. reach and coverage say whether a file's code was RUN; the guard chip says whether any test NAMES what it declares, which is the question a refactor actually asks. Python rows are exact (ast defs → C-ids); ts/tsx rows are name-matched against the symbols web tests import, so they read as a floor and the tooltip says so | — |
| *(spec'd, next loop)* `architecture.html` | app-wide Architecture STATION rendered from `archmap.json` | 1 |
| `assets/a3.css` | the skin + identity layer + trial vocabulary (evolve via the loop, never per-project) | — |
| `assets/slots.js` | raw-skeleton affordance: unfilled `{{TOKEN}}`s render as labeled chips + a notice bar; inert on generated pages | — |
| `assets/a3-settings.js` | viewer settings (cog in `.brand`): 10 content fonts, size S–XL, compact, rail, Light/Dark — localStorage | — |
| `assets/a3-lightbox.js` | proof viewer + expander cascade; delegated on `a[data-lb]`, progressive (anchors resolve with JS off) | — |
| `assets/evidence-nav.js` + `.css` | the entity Evidence NAVIGATOR — one workflow at a time as a small-node bracket tree (left) ⇄ the selected step's production capture + provenance (right). Data-driven: `EvidenceNav.mount(root, {states, workflows, start})`; the contract and the LAYOUT LAW (siblings are parallel paths · a dependency sits one level below its parent · a complex section becomes its OWN linked workflow, never a denser subtree) are in the file's header. Battery: `tests/evidence-nav` | — |
| `assets/board.js` | board station only: framing switch (remembered per browser), cross-framing dropdown filters, column folds, phase-detail panel. SHOWS and HIDES what the generator rendered — it never writes card state, because a card the viewer can move becomes a second source of truth | — |
| `codebase-archive.html` | Codebase-archive STATION — the whole ecosystem + the durable per-phase archive, rendered **in the level-lab grammar via the shared `assets/graph-grammar.js`** (Lucide icons · halo-trimmed **Bowed**-default wires, its signature vs the change graph's direct · entity-gradient cross wires + flow dots · the selection engine with depth/peek/travel/← trail · beat rings on a replayed phase · corner boxes · det dossier + Tier-1 id-card on piece cards). Reads `./c4-graph.js` + `./sim-archive.js`. VOCABULARY: methods incl. BOOT/TASK roots via the grammar's `ep` builder (`--m-boot`/`--m-task` vars); no stream · provider class · `dispatches` drawing (providers still render as model cylinders — recorded, plan §5). Battery: `tests/codebase-graph` §F; probe `probes/port6` | 1 |
| `codebase-archive-lab.html` | Levels LAB — the level-lab grammar over the levels view (root → callee layers, `./levels.js`): the same method roster incl. BOOT/TASK roots (`taskMark` queue glyph), and the `dispatches` wire (long dash — an enqueuer hands work to a TASK root) — the ONLY non-universe surface that draws it. Loads `./c4-graph.js` + `./levels.js`. Battery: `tests/levels-page` | 1 |
| `gabe-universe.html` | Gabe Universe STATION — the same C4 graph as a **3D force-graph** (the spike 5C engine), principal top-nav, dark: entities as tinted clusters with capsule folding for big estates, the fe frontend arm (`fe·<entity>` paired estates + screens + bridge wires), WIRE-VIEW R-toggles, journey walks (backend + frontend legs), header search, and the full Everything→Entity→Cluster→Element panel. Reads `./c4-graph.js` + `./levels.js` + `./sim.data.js` + `assets/{3d-bundle,chip-assets}.js`. SOURCE: assembled from `docs/design/codebase-graph-consolidation/universe-build/` (see its README — `bash regen-example.sh`); NOT hand-edited. VOCABULARY (legend pass 2026-09-06): methods GET/POST/PUT/PATCH/DELETE + BOOT + TASK (method disc, TASK `#f0abfc` on the dark ground); the `dispatches` WIRE kind (long-dash amber `#f76707`, enqueuer → TASK root, an R-toggle + a beam like `access`); BADGE families `method` · `delivery:stream` (cyan `#06b6d4`, the endpoint's SECOND slot) · `pclass` (eight provider classes — llm · embed · vector · agent · infra · http · observability · payments; ROOT-SCOPE rule: a class names what the SDK root is FOR, one class per root, `null` → no badge) · the FE `feclass`/`hrole`; three Sources rows (files skipped · route mounts · twin pass) + the web row's fetch idiom; every legend row carries a drawn example chip or the honest `—`. Battery: `tests/gabe-universe` (static + render — `legend56` probes the second slot FIRE/SILENT + the reference chips + contrast); author-time proofs: `universe-build/verify-*.mjs` | 1 |
| `assets/graph-grammar.js` | the SHARED level-lab grammar (both codebase-graph stations): the three icon sets, halo-trimmed bowed `curve()`, entity gradients, flow dots, lane bows, two-row labels, the panel DOSSIER sections and the typed id-card chips — pure builders, host state passed per call. The stateful selection engine stays per-host (recorded DRY debt). Extracted at the recorded trigger (archive adoption). Contract pins: `tests/codebase-graph` | — |
| `assets/sim-panel.js` | the codebase-graph station's shared detail panel — a `window.GABE_SIM_PANEL(ctx)` factory (typed identifier chips · the per-piece red→execute→review→commit lifecycle timeline · tests+evidence · `openDetail`/`openEntityDetail`/`stageSummary`/`resetPanel`), parameterized on the renderer's two touchpoints. Loaded by the station AND the arch-graph lab, so it is edited ONCE. Contract guarded by `tests/codebase-graph` | — |

## The ruled nav (landed map v3 — merged 2026-07-21)

Static in the skeletons: the station items (Overview · Board · Entity index · Docs · Tests ·
Latest change · Releases), the colored group labels (`g-now/g-board/g-ent/g-docs/g-code/g-test/
g-ledger/g-rel/g-leaf`), and the Testing subitems (`Cases · Files · Claims · Untested` — icon'd
`navsubitem` rows in the Code-group layout, one per estate page (`test-matrix` / `test-files` /
`test-claims` / `test-elements`), carrying the entity Tests tab's section icons; never authored,
so it cannot drift). Generator-filled:

- `{{SIDEBAR_ENTITIES}}` — **adoption.json is THE registry and drives this list** (D123):
  adopted rows link their feature pages; pending rows render MUTED with their tracker state
  chip (pending/building/awaiting-approval), linking the entity index. Labels come from the
  registry row's `display_name` — one fact, one word, on every surface.
- `{{SIDEBAR_CODE}}` — the Architecture item: render it ONLY when `architecture.html` exists;
  else a muted "not built yet" line. The per-feature Code TAB deliberately has no nav item.
- `{{SIDEBAR_LEAF}}` — each known OSS report (htmlcov, playwright) WHEN its file exists on
  disk; else a muted "none wired yet" line. Never a dead link.
- `{{ENTITY_COUNT}}` `{{TESTS_COUNT}}` — live counts; every chrome number must be traceable to
  a section that leads with it (pills are links).

**Containment rule:** a nav item opens a PAGE; the page may hold several map sections
(Overview → recent-changes + needs-you; Board → rail + three lanes). One item per station —
sections are not nav entries.

## Placeholder contract

`{{PROJECT_NAME}}` `{{LANG}}` · sidebar: `{{SIDEBAR_ENTITIES}}` `{{SIDEBAR_CODE}}`
`{{SIDEBAR_LEAF}}` `{{ENTITY_COUNT}}` `{{TESTS_COUNT}}` · foot: `{{REGEN_STAMP}}`
`{{HEAD_SHA}}` `{{GENERATOR_NAME}}` · chrome: `{{STATUS_PILLS}}` `{{SYNC_AGE}}` (the pills
cluster rides IN the tabbar — `.tpills`; the topbar crumb scrolls away, the tabbar is sticky) ·
hub: `{{HUB_TITLE}}` `{{HUB_LEDE}}` `{{HUB_HEADLINE_STATS}}` `{{RECENT_CHANGES}}`
`{{NEEDS_YOU}}` `{{TAB_TESTS}}` `{{TAB_EVIDENCE}}` `{{TAB_RISK}}` · feature:
`{{SUBJECT_TITLE}}` `{{SUBJECT_LEDE}}` `{{SUBJECT_HEADLINE_STATS}}` `{{TAB_OVERVIEW}}`
`{{TAB_CODE}}` `{{TAB_TESTS}}` `{{TAB_EVIDENCE}}` `{{TAB_RISK}}` · station pages keep their
named slots (see each file's comments). A generator may add slots but must fill every listed
one or render an honest named gap — **a false gap is as dishonest as a false pass.**

## Section inventory per tab (feature pages — the five-tab contract)

| Tab | Sections (generator-owned) | Audience |
|---|---|---|
| Overview | card (lens block leads) · diagrams (picker) · growth · decisions changelog | everyone |
| Code | endpoints · code map · data model — ALL from `archmap.json`, the read-once code map | developers |
| Tests | actions · kinds & coverage · cases (the C-id LEDGER: entity/kind icons, dropdown filters incl. tag/endpoint/model/function, URL-param pre-apply + `led-strict` receipts mode, per-kind folds) · files (icon kinds; rows open to cases, C-ids link the ledger) · claims (no cases column — the fold lists them) · untested surface (gaps only) | "is it tested?" |
| Evidence | proof sets (rows → legs → galleries; reference files HELD OUT, stated) · not proven here | business |
| Risk | register (4-field grammar, GAP rows link growth) · not carried forward | whoever prices it |

Every tab pairs an accumulator with an ephemeral half (adopt-spec §ephemeral/accumulator):
card / card `# CODE` / **testing claim card (spec'd)** / `manifest.json` per set / card `# RISKS`.

## CSS vocabulary (the trial's additions — legend where used, always)

`.tpills` tabbar cluster · `.subnav` sticky per-tab nav · `details.secinfo` (⊕ legend beside a
section title; tables never hide) · `details.pmore` (word-boundary truncation carrying its own
⊕ — every truncation must) · `details.proofset` + `details.legset` (proof rows → legs; NOT
`.leg`, which is the legend row) · `.tbl tr.exp` expander rows + open-highlight · `.dgm`
diagram picker · `.lens*` + `details.more` (card folds) · `.tag.m-*` HTTP verbs · `.l-*`
layers · `.s-*` severities · `.fm-*` font-only verb links · `.ty-*` type families (deeper =
wider type; uncolored = domain alias, say so) · `.meter` (bar + count in one cell) · `.cid`
case-id chip (`.cid.none` = `—`, never "un-run"; a ledger row's `id="C<n>"` is the canonical
anchor every C-id pill lands on — cross-page pills prefix it `test-matrix.html#C<n>`) · every
icon-only entity COLUMN heads with the Entity-index layers glyph (generator `ENT_COL`), never
an empty header · `.subnav a.on` marks the current page in the sticky estate menu (testing AND
architecture subpages — overview first, then every sibling) · `.stickstack` stacks the menu
above the sticky entity bar as one unit · `.t-tbd` marks a to-be-designed reference — on the
arch pages an undocumented type, in a case fold an `unmapped imports` row naming the real repo
file no entity's code map registers yet (entity-index.html is the placeholder home) · `.ledbar`/`.lchip`/`.ledmeta`/`.tinfo`/`.ltag` (the case
ledger: filter bar with per-control clear ×, tiered chips solid=own/dashed=via-file, labeled
fold grid, ⓘ tier popovers, provenance-token pills) · `.tag.e-*`/`.st-*` effort/stage pricing ·
dark theme via `[data-theme="dark"]` (mermaid SVGs get an honest light plate) · viewer vars
`--root-size`/`--font-content`/`--side-w`, `data-compact` (vertical density) ≠ `data-rail`
(icon collapse). Chrome uses damped `calc()`, not pure rem — it must hold one line at every
viewer setting; under width pressure scroll, never wrap, never truncate.

## Behaviour contract (the JS layer — guard required)

Viewer: click opens the artifact IN the page; ←/→ run the WHOLE set leg by leg; ↑/↓ change
SET (fold current, unfold next); no wrap at the ends (wrapping silently changes subject); top
line = leg + position, bottom = set. Expanders CASCADE to sub-sections — one toggle, one
decision (`toggle` doesn't bubble: capture phase, and tests must wait a tick). Tab navigation
itself stays script-free. **This layer ships only with its committed harness** (the 360-combo
chrome proof was rebuilt as tests after the trial deleted it — do not regress this).

Evidence navigator: a node click swaps the right panel; a link pill jumps workflows and the picker follows; a shared sub-workflow's ⇱ back returns to whichever parent it was ENTERED from. A state with no capture renders the named-gap panel and never an image — the one property the battery mutation-proves by planting a fake shot.

## Evidence navigator — the wiring contract (proven on the transaction exemplar)

`example/feature-transaction.html` carries the navigator as the Evidence tab's
FIRST section. Four things the exemplar settled, all of them cheap here and
expensive in a twin:

1. **`evidence-nav.js` must NOT be `defer`red.** It only defines a global, and
   the generator's data block is an inline script that calls `mount()` during
   parse — a deferred asset runs after parsing, so the first wiring attempt
   mounted nothing. `defer` on this one file is a silent blank section.
2. **The data is INLINED, never fetched.** Center pages are opened over
   `file://` at least as often as over http, where `fetch()` is blocked. The
   generator emits one `<script>` per entity holding `{states, workflows}` and
   the mount call.
3. **One subnav per pane.** The section contributes its LINK to the pane's
   existing `.subnav`; it must not emit a second nav bar (the first cut did,
   and the pane grew two).
4. **Capture paths are center-relative** (`assets/evidence-states/…` from a
   station page, `../assets/…` from `example/`). The generator owns the
   rewrite from the project's proof root; a path that resolves in the prism
   does not automatically resolve in a feature page.

Section markup: `.subnav` link + `.sechead` (`--gc:#6b46c1`) with a `secinfo`
legend naming the three proof states and ✎, then `<div id="ev-nav-root">`.

## Rules

- The archived project's legacy shell/css is never a source of chrome.
- Content is generated from machine sources; authored prose only translates; a card must not
  restate a number the build can read.
- Raw skeletons render styled in place; `slots.js` labels unfilled slots — a template awaiting
  its generator, never a broken page.
- Generators copy `assets/` wholesale; the vendored copy is the build input (never `$HOME`).
