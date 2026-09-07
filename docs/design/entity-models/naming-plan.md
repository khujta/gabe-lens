# Plan — naming strategies and frontend/backend conventions for the entity models (2026-09-06)

**Status:** RULED 2026-09-06 (operator, AskUserQuestion) — building. Rulings: default strategy `domain` · **default convention `case` — frontend camelCase, backend PascalCase (a NEW shape, see the conventions table; the word marks prefix/suffix/bracket/glyph/tint/none stay as pill positions)** · the emitter imports the INSTALLED `draft_name` (env override `GABE_DRAFT_WORKFLOWS`) · the phrase==noun dedupe lands as its OWN commit first. Decisions 5–11 taken on their recommendations (DECISION blocks in the session). Original header follows.

**Status (original):** DRAFT — nothing built. Operator ask (2026-09-06, after the four models shipped at `e60484a`): *"per model let's add options
for different naming strategies and conventions — different ways to name the entities, and different conventions to distinguish
frontend and backend instead of prefixing frontend with fe".* Judge panel (three read-only designs — display-only · emitter-emits-all
· config-first — one Fable judge; numbers below were recomputed on the six committed maps) → this synthesis. Build starts on "land it".

**The one law this plan hangs on:** a name is a RENDERING of a row that already exists. The claim slug and every cluster id
(`fe·<slug>` · `d:<table>` · `a:<gate>` · `fe·d:<table>`) are JOIN KEYS and never move; a strategy or a convention changes words,
never ids. The pill's default reproduces today's map byte for byte, so the whole pass lands as a pure addition.

---

## The shape

**Every candidate name is computed ONCE, by the emitter.** All three designs converged here, and the probe settled it twice: the
`action` phrase needs the Python `draft_name()`, and the candidate roster's 40-member cap (endpoint ids sort after `apps/…`
ids) already clips `d:dish_history_events` to 6 of its 8 endpoint labels — today's drafter names a candidate over PARTIAL input.
Computing from the emitter's uncapped atoms fixes a live bug, not a latent one.

1. **Per roster row** (`c4.models.rosters.derived[]` features · `candidates[]`; aspects/layers carry what applies): `name`
   UNCHANGED (= the `domain` strategy) plus a `names{}` sibling holding only the keys a strategy could produce, never null —
   `{"table": "cooking photos", "class": "cooking photo", "path": "cooking", "action": "Manage cooking — sessions · photos · active ·
   cancel", "both": "cooking photos · /cooking/sessions/photos"}` (+ `"config": "…"` only when the project names the row). The
   twin `fe·d:<table>` inherits its backend row through `__uniModelRoster` (already indexed). Cost ≈ 4,522 B gustify (+0.27%) ·
   2,148 gastify (+0.24%) · 236 tier0 · 0 tier1 · 131 tier2 · 12,523 onyx (+0.67%). `members` gains a deterministic fix in the same
   commit: endpoint ids sort FIRST, so the 40-cap never clips the action input again.
2. **`c4.models.naming`** — the contract, once: `default` · `source` (built-in | center.config.json#naming) · `positions` ·
   `coverage{}` per strategy · `collisions{path}` · `long{action, both}` (rows over `name_max` 40) · `disabled{}` with reasons ·
   `entities{slug: {display}}` · `fe{present, reason, convention, words{frontend, backend}, forms{…}, homes, twins}` ·
   `config_error` · `unused_words[]` · `unknown_entities[]` · `caps{name_max}` · `rule`. On a feed without a frontend
   (tier1 · tier2 · onyx) `fe.present:false` carries the emitter's reason and the conventions are absent. Validation is
   report-never-gate: an unknown strategy/convention keeps the built-in and records `config_error`; a `words` key naming nothing
   lands in `unused_words`; a `naming.entities` key that is not a declared slug lands in `unknown_entities`; a malformed block is
   one warn line and defaults — a regen never fails on a vocabulary file. `levels.json` gains nothing.
3. **`center.config.json`** → optional `"naming": {"strategy": "domain", "fe": {"convention": "prefix", "frontend": "ui",
   "backend": "api"}, "words": {"domains": {"manage": "administration"}, "tables": {"user__user_group": "group membership"}},
   "entities": {"legal-consent": "Legal & Consent"}}` with a `_naming_comment` saying every key is optional and nothing here is
   a join key. The top-level `url_domain_map` STAYS (entity_shape's CLI, review's ENTITY-SHAPE DRIFT and the MCP tool read it
   there) and is read as the fallback for `words.domains` — `naming.source` marks it deprecated. Seeded commented-out in
   `center.config.template.json`, filled in `center.config.example.json`.
4. **`entities.draft.json`**: `naming` echoed at the top (strategy · source), `names{}` per row, `name_from`, `slug_from: "domain"`
   and `slug_options{table, class}` per candidate — the human sees every word and picks the slug; `suggested_slug` unchanged.

Deliberately NOT in the shape: per-node name fields (3,396 nodes on onyx — the strip test), names on `homes{}`/`held`/`abstain`,
a top-level `c4.naming`, an emitted tier map, a `noun` key, a strategy key anywhere near an id.

**Conventions are FORM TEMPLATES emitted with the project's words already substituted** (`{fe: "[ui] {name}", be: "[api] {name}"}`)
so the station, gabe-map and the drafter each own a three-line `{name}` substitution and cannot drift on the shape.

## The strategies (pill `#entnaming`, in this order)

| Position | Rule | gustify | onyx | Measured |
|---|---|---|---|---|
| `domain` (default) | today's `_name_cluster`: the URL domain at adaptive depth, else the table in words — this IS `row.name` | d:cooking_photos → `cooking/sessions/photos` · d:cooking_sessions → `cooking sessions` | d:voice_provider → `admin/voice` · d:chunk_stats → `chunk stats` | differs 0 on all six estates |
| `table` | `_words(anchor_table)` always — unique by construction (the id is `d:<table>`) | `cooking photos` · `consent records` | `voice provider` · `connector credential pair` | differs 5/25 · 1/12 · 15/65, 0 collisions |
| `class` | the ORM class split acronym-aware, lowercased (`LLMModelFlow` → `llm model flow`; `OAuthConfig` → `o auth config`, said on the card — no rule can know OAuth is one word; the project renames it in `naming.words.tables`) | `dish history event` · `canonical ingredient` | `chat message feedback` (the class disagrees with the table) | differs 21/25 · 12/12 · 30/65, 0 collisions |
| `path` | the deepest segment common to all the cluster's HTTP paths, else the most frequent leaf; TASK atoms never vote; collisions suffixed ` (<table words>)` at emit; the count on the pill title and the Sources row; self-disables at ≥ 1/3 colliding rows | `cooking` · `sessions` · `cupo` (a real segment, a useless name — honest) | `providers` · `chat` · `manage (credential)` | collisions 4/25 · 5/12 · 19/65 (max 29%, none disables) |
| `action` | the 2026-09-05 law verbatim — `draft_name()` over the cluster's UNCAPPED endpoint labels | `Manage cooking sessions — readiness · stage · timer · complete` | `Manage chat — delete all chat sessions · …` (102 chars, the max) | over 40 chars on 10/25 · 3/12 · 41/65 → hull sprite truncates at `name_max` 40, every other surface carries the phrase; `Manage manage` on 9/65 onyx rows (the ruling below) |
| `config` | the project's words: claim entity → `naming.entities[slug]` else adoption `display_name` (already in the feed as `l1.nodes[].label`, ignored by the universe today); cluster → `naming.words.domains[first segment]` when domain-named, else `naming.words.tables[table]`, else the legacy `url_domain_map`; a row nothing names carries no key; the position disables at coverage 0 with the reason | `Legal/Consent` · `Cooking` (8/8 entities) · clusters abstain until words are written | 0/9 entities (no adoption.json) · 0/65 clusters → disabled, reason printed | adoption display_name ≠ slug on 8/8 · 5/5 · 4/4 · 0/9; `url_domain_map` declared on zero estates |
| `both` | `<table words> · /<url prefix>` (the prefix the descent reached, else the level-1 majority; the table alone when none) — unique by construction, the two machine witnesses side by side | `cooking sessions · /cooking` · `cooking photos · /cooking/sessions/photos` | `credential · /manage` · `chat message · /chat` | differs 21/25 · 61/65; max 41 · 63 chars (1 · 7 rows over 40) |

## The conventions (pill `#entfeconv`, each button renders its ACTUAL mark — legend-visual law)

| Convention | Form | Note |
|---|---|---|
| `case` (default, operator-ruled) | `{name\|camel}` / `{name\|pascal}` | the CASING is the mark — frontend `cookingSessions`, backend `CookingSessions`; applied to the name's leading word-run (up to the first ` · ` or ` — `), separators and trailing detail keep their words; `naming.fe.case {frontend: camel, backend: pascal}` swaps the pair; one-word names still differ (`cooking` / `Cooking`); every label's casing changes on regen — the operator's chosen churn |
| `prefix` | `fe · {name}` / `{name}` | today's mark, the key's dot opened; two batteries pin it today (re-pinned as a position) |
| `suffix` | `{name} (ui)` / `{name}` | the mark trails, so a sorted fleet/search seats `cooking (ui)` beside `cooking` — 11 of gustify's 20 fleet homes sort under "f" today |
| `bracket` | `[ui] {name}` / `[api] {name}` | the only SYMMETRIC mark — the backend is marked too, so "no mark means backend" is never learned; the text fallback for glyph/tint in a plain-text tool answer |
| `glyph` | `{name}` / `{name}` + the screen glyph on DOM labels | canvas hull sprites cannot carry an SVG → tint; the Sources row says so |
| `tint` | `{name}` / `{name}` | the twin tint (lerp 0.38) + the fleet's Backend/Frontend masters are the whole signal; a flat list shows two `cooking` → the search result's sub line prints the raw key |
| `none` | bare | structurally lossless (ring seating rides `FE_PAIR`, the fleet splits on the set, the panel says it in words); the FORCED, unstored rendering on a feed without a frontend |
| `words` | not a shape — the INPUT | `naming.fe.frontend` / `.backend` (`client`/`server`, `screens`/`services`, a Spanish pair) substituted into every form at emit; absent → `ui`/`api`, an explicit suite default, not a guess |

**The load-bearing line, landed first and alone:** `__uniIsFeEnt` (station `:3374`) today regexes `/^fe · /` on the RENDERED label,
and that boolean drives behaviour — the fleet's backend/frontend split, the two group masters, capsule area stamping, `coreLead`'s
coreByFE/coreByBE. Any convention but `prefix` would silently re-group every frontend entity. New body:
`!!FE_HOME[e] || /^fe·/.test(String(e||""))` — the registry (every non-entity fe home + every minted `fe·d:` twin), then the KEY
prefix; never a label. Headless pin: beEnts/feEnts counts identical across all six conventions (gustify 9 / 11). Python side:
`id.startswith("fe·") or id in fe_home_ids`. Also: `modelRow.nm()` drops its `!/^fe·/` refusal so `fe·d:` twins read their roster
name (today they render `fe · d:cooking_photos`).

## The control surface

Two single-select pills in the cog panel, built by the same `__uniAddWireView` pass directly under `#entmodel` and above `#wireview`,
in its disabled-position grammar (reason in `title`, `__uniSyncGrpSel` echoing the chosen word). **GLOBAL, not per model** — names
key on cluster ids that span the views; a per-model preference would 4× the reader state and make one click change words for two
reasons; the disabled-position grammar carries the per-model honesty (on the claim model only `config` differs from the slug — the
title says so).

**Precedence, stated once** (station header + shell README, one battery case per level): URL > localStorage > config
(`models.naming.default` / `.fe.convention`) > built-in (`domain` / `case`). localStorage keys `gabe:universe:naming` and
`gabe:universe:feconv`; a stored value the feed cannot serve falls through with ONE console line naming the valid set; no state
renders a blank label. Deep links `?naming=` and `?feconv=` beside `?model=`: inside `__uniApplyDeepLinks` ASSIGN naming/feconv
state first (no render), then apply `?model=` (its re-cluster labels with the convention in force), then `?journey=`/`?ent=`; if no
model switch happened one `__uniRelabel()` closes it; always `{noStore:true}` — a shared link never rewrites the reader's preference.

**The switch is a RELABEL, never a re-cluster:** `__uniSetNaming(k, opts)` / `__uniSetFeConv(k, opts)` mirror `__uniSetModel`'s
signature and guard, set the state, then ONE `__uniRelabel()` (re-add the cluster label sprites · `__uniFleetRender` · the open
panel · the search index · the Sources row · the legend · `__uniSyncGrpSel` · store unless noStore). The static pin is the ABSENCE
list: no `recomputeEX` · `__uniAssignSplit` · `recomputeSubAnchors` · `__uniApplyCapsules` · `d3ReheatSimulation` ·
`Graph.graphData(` · `nodes=` · `n.ent=` · `JRN=null` in the slice.

**Sources row:** one clause on the entity-model row — `names: class (your choice · project default: domain) · 25/25 named · 0
collide · 2 truncated at 40 · frontend mark: bracket (ui/api) · 11 homes · 19 twins · source: center.config.json#naming` — leading
with `config_error` when set. **Legend:** `_modelSection` gains a NAMES row (the strategy in force with its rule sentence, drawing the
same cluster's name before/after on the reader's own feed) and a FRONTEND MARK row drawing the actual mark from the same form literal.

**Beyond the station:** gabe-map `entity_models` rows carry `name` (the config default) · `names{}` · `name_from` · the raw id, and
the census a `naming` line; `entity_context`'s fe_home note renders through the config convention with the id beside it; NO
`naming=` argument on any tool (the record's ruling; schemas are deferred, the alternates ride the payload). The drafter writes the
config default, `names{}`, `--naming <key>` as an explicit override for a human run, `slug_from: "domain"`; pulse S18 gains one
clause (strategy in force · `config_error` · `unused_words`), no new trigger.

## Build order (each phase ends in a review; [H] = heavy, serial, alone)

0. **STATION, standalone commit (the live latent bug):** `__uniIsFeEnt` off the label; `modelRow.nm()` reads roster names for
   twins; retire + replace the two pins that grep the label; headless: beEnts/feEnts invariant when a label changes. Template only
   → `regen-example.sh` (commit first — the `--check` trap). Worth landing even if the rest is deferred.
1. **EMITTER:** NEW `templates/center/generators/_a3_naming.py` (~170: table · class · path + dedupe · action via the installed
   `draft_name` (honest-empty) · config resolution incl. the `url_domain_map` fallback · both · forms with words substituted ·
   coverage/collisions/long/disabled · validation) + `_a3_models.py` +~20 (attach `names{}`; `naming` into `build()`; endpoint ids
   first in `members`; 683 → ~703) + `build_center_a3.py` +~8 (pass `CFG.naming`, `CFG.url_domain_map`, `LABELS`; one report
   line) + the two config templates. Batteries: NEW `tests/naming/run.sh` (~160: FIRE/SILENT per strategy · acronym lever
   `LLMModelFlow` · path dedupe · the phrase==noun fixture if ruled · config FIRE/SILENT/INVALID/LEGACY · `unused_words` ·
   determinism · R10 · the JOIN-KEY assert: build under every strategy × convention, pop `names` + `naming`, byte-equal to the
   config-less build) · `tests/entity-models` +~15 (`name` byte-identical; `suggested_slug` derives from `name` only — a mutant that
   follows `names[k]` reddens) · `tests/arch-graph` +~12 (strip → committed bytes) · `tests/center` +~10 (a bad strategy regens
   GREEN with `config_error`; absent block → source built-in). Review R1: dry-run on COPIES of the six committed maps reproducing the
   measured table; numbers into the commit.
2. **REGISTRIES:** nothing new — the strip test covers the additive key; a negative grep guard names the id-resolution bodies
   (`_a3_homing:172` · `_a3_graft._fe_pair` · `tools.py:242` · `tools_wave2:203` · `tools_wave4:77/189`): no `naming`/`convention`
   symbol inside them; a fixture inserting the word proves the guard fires.
3. **STATION** (template only; example regenerated): `__uniNameOf(id)` (roster `names[strategy]` → `row.name` → the l1 label for
   claim slugs → the id) · `__uniEntLabel` composing `forms[conv][tier]` over it · `__uniRelabel` · the two setters · the two pills ·
   boot read + precedence · deep links in the stated order · Sources clause · legend rows. `tests/gabe-universe` +~60 static
   (`data-v` order for both pills · built between `#entmodel` and `#wireview` on all three call-site paths · the `__uniRelabel`
   absence list · noStore on the URL path · legend rows concatenated · no "orphan") + 3 headless asserts in the existing block
   (switch naming → `nodes.map(n=>n.ent)` and `CLUSTERS.map(c=>c.ekey)` element-wise unchanged, ≥1 label changed, a walk survives;
   cycle six conventions → split counts identical; round trip → labels element-wise equal; delete `models.naming` → the setter
   returns false, one console line). [H] alone.
4. **TOOLS:** `tools_wave4.py` +~30 · `tools.py` +~6 · map-spec §5.10 +~12 · gabe-map SKILL bump; `tests/gabe-map` +~25 incl.
   the probe `entity_context('Legal/Consent')` and the 102-char action phrase → `{found:false}` + the grep floor, never a match.
5. **DRAFTER + PULSE:** `draft-entities.py` +~30 (read `names{}`/`naming.default`, `--naming` override, `name_from`, `slug_from`,
   `slug_options{}`, `_action()` kept as the fallback for a feed without names) · `angles.py` +~8 (the S18 clause) · pulse-spec +4 ·
   two version bumps; `tests/draft-entities` +~15 · `tests/pulse-angles` +~8.
6. **DOCS + INSTALL + DOCTOR:** CLAUDE.md (one Conventions clause + three version rows) · README.md NAMING section (the measured
   table verbatim, `name_max` 40 with its kill condition, the OAuthConfig honesty, the dependency ruling, the operator's rulings) ·
   shell README (the pill contract + the precedence law). `./install.sh` → `scripts/suite-doctor.sh` [H] CLEAN.
7. **REGENS, serial:** `regen-example.sh` then `--check` → tier0 → tier1 → tier2 → tier3 → gustify and gastify via `propagate.sh`
   → regen → drafter per estate. Record per estate: strategy + source · coverage per position · positions disabled and why · path
   collisions suffixed · action rows truncated · fe present/absent. The diff on each estate is the `names`/`naming` bytes and
   nothing else — the reviewable proof that the default changed nothing.

**Estimate:** ≈ 20 files · ≈ 700 lines of code/config/docs + ≈ 300 battery lines; `gabe-universe.html` +~130/−30 in the TEMPLATE only
(6,226 → ~6,330, over the 800 CODE budget already — state the numbers in the commit); three skill bumps; 1.5–2 sessions, the last
half being six serial regens plus the doctor.

## Decisions (the operator rules; the recommendation is first)

1. **Built-in default STRATEGY** — `domain` (0 churn on all six estates; the purity table stays comparable; try `class`/`both` from
   the pill, set the config when one sticks) · `table` · `class` · `both`.
2. **Built-in default CONVENTION** — `prefix` as the built-in (0 churn), `bracket` as the config template's suggested value (the
   complaint behind the ask is the asymmetry, which bracket alone removes); `suffix` is the one to try first on gustify for the
   sorting win.
3. **How the emitter reaches `draft_name()` for `action`** — import the INSTALLED skill script (`~/.claude/skills/gabe-cc-update/
   scripts/draft-workflows.py`, env override `GABE_DRAFT_WORKFLOWS` — the `GABE_GRAFT_INDEX` precedent); unreachable → `names.action`
   absent for every row, `coverage.action` 0 with the path in the reason · move `draft_name` into `_a3_naming.py` and flip three
   skill consumers onto the project's generator copy · keep `action` drafter-only (no pill position).
4. **The phrase==noun dedupe in `draft_name`** (`Manage manage — …` on 9/65 onyx rows; 0 elsewhere) — its OWN commit before this
   pass (the workflow drafter and S16 improve with it; onyx's workflow drafts re-run under a stated reason) · inside this pass · no.
5. `both` composition — `<table> · /<url prefix>` (the two machine witnesses; unique by construction) · `<name> · <claim majority>`
   (the better AUDIT string; offer as the config value `both_owner` only when wanted) · ship both positions.
6. `path` ships as a pill position — yes, collisions suffixed + counted + the 1/3 self-disable · emit for the drafter only · no.
7. The config's `naming` block BINDS the text surfaces (gabe-map, the draft, S18) while the station keeps a reader override; both
   print which strategy they applied · seed everywhere · bind everywhere.
8. `url_domain_map` — absorbed: `naming.words.domains` wins, the top-level key is read as a fallback and marked deprecated, never
   moved · keep both independent · migrate away.
9. `suggested_slug` — always derived from `name` (today), `slug_from: "domain"`, `slug_options{table, class}` offered · follow the
   config default · follow the reader's pill.
10. The CLAIM model renders the `config` strategy (adoption `display_name`: gustify 8/8, gastify 5/5, tier0 4/4, onyx 0) — yes (the
    largest immediate readability win, already in the feed, the slug stays on the card) · no.
11. Pulse — one clause on S18, no new trigger · a new S19 · nothing.

## Rejected (with the reason)

- Computing strategies per surface — three implementations of six rules and a JS port of `draft_name`; the emitted `names{}` costs
  0.09–0.67% of the c4 bytes, cheaper than one drifted rule.
- A per-MODEL naming/convention state — 4× reader state; one click changing words for two reasons.
- A `naming=` argument on `entity_models` — the record rules a view argument "never"; schemas are deferred so it would be invisible.
- `suggested_slug` following a strategy — a display preference reaching a registry key; the domain variant collides 7/25 · 34/65.
- A top-level `c4.naming` block — a second strip surface; `models` is present on all six estates, the contract fits under it.
- An emitted tier map — `FE_HOME` ∪ the `fe·` key already IS the set.
- Emitting `noun` — data for a surface that does not exist; the standalone value collides on 14/25 · 53/65.
- A domain-without-fallback position — mostly falls back, or collides 12/25 · 55/65 at level 1 and is `both` once suffixed.
- An eighth `id` position — the card prints the raw id beside every name.
- Moving `url_domain_map` without a fallback — three readers.
- Title-Case class names — the law is lowercase words.
- `words` as a seventh shape — it is the input to every shape.
- A new S19 — a vocabulary typo is not a signal.
- Hand-editing the example station copy — the template is the source of record; `fill-example.py` writes the example.
- Pre-composing 7×7 labels per id — 60–120 KB of near-duplicate strings.
- Raising the sprite cap instead of `name_max` 40 — a 102-char label draws a sprite ~6× normal width; the kill condition for the
  cap is a two-line label.
- Fixing OAuthConfig by rule — no CamelCase rule knows OAuth is one word; the project renames it in `naming.words.tables`.
