# The four entity models — claim · seeded · derived · proposed

> Design record for the entity-models pass (2026-09-06). The plan that was executed is [plan.md](plan.md); the analysis it
> came from is the artifact *Entities from Evidence* (six-agent workflow over gustify · gastify · tier0 · onyx). This file
> holds what the plan cannot: the operator's decision, the measured table, the abstention law, every cap with the
> condition that kills it, the deferred items with their triggers, and the kill condition for the whole derived view.

## The decision

The operator asked for a deeper analysis than "which file is this in": *detect a piece of code as an element (endpoint ·
function · hook · component · model · store · schema), cluster by functionality and place in the workflow/dataflow, and deduce
entities — a group of elements that corresponds to a feature or aspect of the bigger system.* The analysis produced three
approaches; the artifact recommended P3 (a drafter + human acceptance) with P1's two prerequisites and advised against P2.
The operator ruled: **build all three, switch between them with a pill in the top-right config section, drop the R1–R4
wire-view controls.** Four follow-up decisions (AskUserQuestion, 2026-09-06): table anchors + adaptive-depth URL-domain names
· proposed as its own fourth view (the map AS IF accepted) · URL-domain-noun naming with the table in the user's words as the
fallback · R2–R4 dropped. One decision taken in the plan by DECISION block: naming descends only while a domain's atoms name
more than one anchor table, `DEPTH_CAP` 3; the `>N endpoints` clause was dropped.

## The one law

**`claim` is the REGISTRY and the JOIN KEY.** An entity today is a name + file claims (`code.*` globs) + a models allowlist +
`test_rx`; every tool, hook, generator and station registry joins on the claim slug. `seeded` · `derived` · `proposed` are
VIEWS — per-piece home DELTAS resolved per node as `home = C4.models.homes[view][id] || GABE_LEVELS.models.homes[view][id] ||
entClaim` — and **nothing joins on their names** (`d:<table>` · `a:<gate>` · `fe·d:<table>` are cluster ids, never slugs).
Nothing is re-homed on disk. The definition of an entity did not change; what changed is that the disagreement between the
file claim and the other witnesses is now VISIBLE, on four surfaces (the station pill · `entity_models` · pulse S9-B/S18 ·
the drafter), and acceptance is one edit in `center.config.json`.

## Where each model is emitted, and who reads it

| Model | Emitted by | Carried on | Read by |
|---|---|---|---|
| claim | the config's `code.*` claims (`_a3_graph` l1/l2) | every map (unchanged bytes — the strip test) | everything |
| seeded | `_a3_models.seed` — Part C's move verdicts (`_a3_homing`), hubs held, targets tier-consistent | `c4.models.homes.seeded` (c4 ids) · `levels.models.homes.seeded` (function ids) | the pill · `entity_models` · S17's pointer |
| derived | `_a3_models.derive` — request atoms on the write-majority table, URL-domain names at adaptive depth; aspects · layers | `c4.models.rosters.derived` + homes · the levels half | the pill · `entity_models` · S9 arm B · the drafter (`--model derived`) |
| proposed | `_a3_models.propose` — candidates first, then one verdict per declared entity, as if accepted | `c4.models.rosters.proposed` + `candidates` + homes | the pill · `entity_models` · `entity_context.proposed` · the drafter → `entities.draft.json` → S18 · cc-init's third lens |

The element census (`_a3_code.element_census`) is the bound of "what could be an element at all": every backend `.py` under a
claim root that no entity claims is minted into the unclaimed area as an `element:` node (cap 2000, said when clipped) so the
map's blind spot has a shape.

## The measured table (the analysis, verbatim)

Four estates: gustify · gastify · tier0 · onyx (tier3).

| Measure | gustify | gastify | tier0 | onyx |
|---|---|---|---|---|
| Unsupervised LPA purity vs the declared entities | 0.646 | 0.654 | 0.660 | 0.576 |
| … after removing the hubs (ablation) | 0.857 | 0.908 | 0.727 | 0.704 |
| hubs removed | 41 | 16 | 5 | 109 |
| Witness coverage, backend files (users ∪ data reach them) | 31% | 29% | 46% | 29% |
| Witness coverage with the frontend | 92% | 67% | 87% | 57% |
| Free propagation would move | 34–42% of pieces on every estate | | | |
| Gate fan-in (the aspect detector): gate on N of M URL domains | 23/24 | 34/41 | — | — |
| Screen co-fetch as an aspect detector | NOT a detector (measured) | | | |
| Triads (endpoint · schema · hook) recovered | 6/8 | 4/5 | 2/4 | 0/9 |
| gastify unclaimed by any entity | 33 routes · 254 fns · 12 tables | | | |
| graft cross-file edges | all `inferred` (a floor, never a census) | | | |

**Derived purity (the shipped emitter, deterministic — no LPA, no seed):** the analysis measured 0.910 · 0.898 · 0.893
(gustify · gastify · onyx); the emitter as shipped after its review (write primacy decided PER ATOM, a read-only atom anchors
on reads and says so; a prefix needs the cluster's majority and, past level 1, two atoms) measures **0.897 · 0.897 · 0.893**
with 78/80 · 49/49 · 327/545 atoms anchored. The two-hundredths on gustify is the per-atom rule doing what it says.

## The abstention law

A piece no witness reaches KEEPS its claim and is LISTED — never guessed. Concretely: an atom with no table (`abstain.derived`),
a seed whose target is tier-inconsistent (a backend piece bound for an `fe·` area, a frontend piece bound for a bucket —
`abstain.seeded`), a hub (`held`) and an entity with no atom (`unweighed`) all print on the Sources row, in the census, and in
the draft's `coverage` + `abstained`. 31/29/46/29% witness coverage must never read as "69% wrong": the draft's
`coverage.witnessed` and `abstained` are non-optional fields.

## Every cap, with the condition that kills it

| Cap | Value | Kill / review condition (observable) |
|---|---|---|
| `DEPTH_CAP` | 3 | a regen where > 20% of derived names are `truncated` — the domain tree is deeper than the rule; onyx shipped 7 of 65 |
| `HUB_HOMES` | 3 | a piece consumed from 3 homes that a reader calls a feature, not plumbing (the bar, not the floor, makes a hub) |
| `HUB_FLOOR` gate · api-client · platform · default | 1 · 1 · 8 · 20 | **platform: 0 or > 10% of frontend pieces read as platform hubs** — printed in `views.seeded.note` as `KILL CONDITION` by the emitter itself |
| `ASPECT_DOMAINS` | 3 | a gate on 2 domains a reader calls cross-cutting; or a 3-domain gate that is one feature's own guard |
| `ASPECT_COCLAIM_MIN` / `ASPECT_SOLE_MAX` | 3 / 1 | entity_shape.py's own numbers (operator-ruled 2026-08-14); changing them changes review's diff verdicts — see the hazard note there |
| `WRITE_FANIN` | 3 | a table written by 3 entities that is one feature's table (the spine row is reported, never drawn) |
| `FE_HOMES` | 3 | a frontend piece consumed from 3 homes whose hull a reader wants to SEE (deferred item below) |
| `SPLIT_MIN` | 3 | a 2-atom feature the operator would split out by hand |
| `CANDIDATE_SHARE` | 2/3 | a feature spanning 3 entities with a 70% majority that is still a missing entity |
| `ROSTER_CAP` · `MEMBER_CAP` · `SHARED_CAP` · `EVIDENCE_CAP` | 200 · 400 · 400 · 12 | any `stats.truncated` entry or `_more` sibling > 0 on a twin — a cap that clips real data is raised, never silently |
| `_ELEMENT_CAP` · `_ELEMENT_FN_CAP` | 2000 · 40 | `stats.elements.truncated` true on any estate |

## Deferred, with triggers

- Depends-modularity aspect detector — trigger: an aspect the three detectors (gate fan-in · write fan-in · fe-homes) miss.
- Layer hulls + moving `a:fe-shared` pieces into a drawn aspect hull — trigger: a reader asks to SEE the shared plumbing as a field.
- Minting TypeScript unpieced files as elements — trigger: a config/test file the drafter needs to name.
- Re-clustering `codebase-graph.html` / `sim-panel.js` — trigger: a change simulated against a derived feature (B12 pins claim-only).
- The `homing: usage-first` config switch — Part C's own trigger: ≥ 5 hand-accepted moves on a twin.
- A `model=` argument on the existing tools — never: the join-key hazard.
- A drawn "muted mark" for abstained/held pieces — the plan named a candidate/fixture draw channel that does not exist; the mark rides the card row.

## The kill condition for the derived view

Zero candidates accepted across three drafts on both twins ⇒ the pill is a picture, not a proposal. Say so here (with the
three draft heads), keep the pill, do not delete the emitter — a picture of the disagreement is still the operator's ask.

## Naming — strategies and the frontend mark (naming-plan, 2026-09-06)

The operator's second ask: options for how a cluster is NAMED and how a frontend home is told apart from a backend one, per
model. The plan is [naming-plan.md](naming-plan.md); the law is one sentence — a name is a RENDERING over an unchanged id. The
emitter (`_a3_naming.py`) computes every candidate name once (`names{}` per row) and the convention FORMS with the project's
words; the station, gabe-map and the drafter substitute one `{name}`. Rulings (AskUserQuestion): default strategy `domain`
(zero churn) · default convention `case` — frontend camelCase, backend PascalCase (every label's casing changes on regen: the
operator's chosen churn; `naming.fe.case` swaps the pair) · the emitter imports the INSTALLED `draft_name` · the phrase==noun
dedupe landed first (`69daa37`). Recommendations taken: `both` = table · /url prefix; `path` ships with collision suffixes and
a 1/3 self-disable; the config binds text surfaces and seeds the station (the reader may override the station only);
`url_domain_map` absorbed as a fallback, never moved; `suggested_slug` never follows a strategy (`slug_from` + `slug_options`);
the claim model renders display names under `config`; S18 gains one clause, no S19. Measured on the six committed maps: rows
25 · 12 · 2 · 0 · 1 · 65; differs from today — table 5 · 1 · 1 · – · 1 · 15, class 21 · 12 · 1 · – · 1 · 24, both 21 · 11 · 2 · – ·
1 · 61; path collisions 4 · 5 · 0 · – · 0 · 19 (gastify's `path` self-disables at 5/12); action over `name_max` 40: 10 · 3 · 0 · – · 0 ·
39 (the hull sprite truncates with an ellipsis; a two-line label is the cap's kill condition); config coverage 0 everywhere until
a project writes words (display names keep the position on for 8 · 7 · 4 entities); `OAuthConfig` reads `o auth config` by
rule — honestly; cost +6.7 · +4.3 · +1.8 · +1.3 · +1.5 · +15.4 KB. Deferred with triggers: a `both_owner` composition (the
audit string) when wanted; S19 for naming debt the first time a `naming.words` key survives a regen that dropped its cluster.

### The naming pass as shipped (2026-09-06, suite `c4e2156`)

Two read-only reviews (emitter 15 real · surfaces 19 real, all fixed): no operator path on the map (the doctor's lint fired
once) · an identity case emits the bare token · every malformed config level named · the relabel keeps the reader's panel · one
label funnel on the card · escaped innerHTML sinks · pills synced by the setters · a disabled position never lit · a default the
feed cannot serve named, the built-in standing. Per estate (default domain · built-in; fe mark case where a frontend exists):

| Estate | rows | table · class · action · both | path named · collisions | fe mark | naming words configured |
|---|---|---|---|---|---|
| gustify (`6af08c96`, pushed) | 25 | 25 each | 22/25 · 6 | case | none yet (8 display names keep `config` on) |
| gastify (`6c285583`, pushed) | 12 | 12 each | 12/12 · 5 → the position self-disables (≥ 1/3) | case | none (7 display names) |
| tier0 (local) | 2 | 2 each | 2/2 · 0 | case | none (4 display names) |
| tier1 (local) | 0 | — (every cluster position disabled with one reason) | — | no frontend — pill disabled | none |
| tier2 (local) | 1 | 1 each | 1/1 · 0 | no frontend | none |
| tier3 / onyx (local) | 65 | 65 each | 63/65 · 24 | no frontend | none (no adoption record → `config` disabled) |

Reading worth a look: the operator-ruled `case` default relabels every claim entity on the twins (`Cooking` · `pantry` becomes
`Pantry`, frontend homes `cookingSessions`); the first project to write `naming.words` or `naming.entities` lights the `config`
position for its clusters. The surfaces review's one deferred item: `both_owner` (the audit string) as a config value when wanted.

## The estates as shipped (2026-09-06, suite `a6cf665`)

| Estate | seeded moved · held | derived features · anchored/atoms · abstained · purity | proposed | candidates | hubs |
|---|---|---|---|---|---|
| gustify (`afb646c9`, pushed) | 9 · 4 | 25 · 78/80 · 2 · 0.897 | FEATURE 2 · SPLIT 3 · ASPECT 1 · LAYER 1 | dish history events | 55 |
| gastify (pushed) | 7 · 0 | 12 · 49/49 · 0 · 0.897 | FEATURE 2 · SPLIT 3 | — | 20 |
| tier0 (local) | 4 · 1 | 2 · 9/23 · 14 · 0.778 | FEATURE 2 · MERGE 1 | — | 13 |
| tier1 (local) | 2 · 0 | absent — no atom carries a table (said) | absent (said) | — | 1 |
| tier2 (local) | 1 · 0 | 1 · 2/11 · 9 · 1.0 | FEATURE 1 | — | 0 |
| tier3 / onyx (local) | 96 · 2 | 65 · 327/545 · 218 · 0.893 | FEATURE 1 · SPLIT 4 · ASPECT 2 · LAYER 2 | search settings · user user group | 28 |

Every estate carries `entities.draft.json` (head-stamped); tier1's drafter wrote nothing and said why. On onyx
`?model=derived&ent=d:persona` resolves against the derived clusters and the Sources row reads `327/545 atoms anchored · 218
abstained` (the station boots unfolded there — the T1 field is 794 nodes, under the scale guard's 1,600 budget). One reading
worth a ruling: the sibling naming law yields `Manage manage — users · permissions …` for onyx's `/manage/*` candidate — the
noun IS the domain word; the human renames on acceptance.

## Batteries

`tests/entity-models` (the emitter, 69, every rule with a named mutation lever) · `tests/arch-graph` (byte-identity when
stripped; element nodes) · `tests/levels` (the function half) · `tests/center` (the wiring; a raising build leaves both
files with the honest absence; the twin driver lands a new required generator) · `tests/gabe-universe` (584 static + the
headless switch proof: identity · feed counts · registry · abstain · the claim join · a walk survives · dashed aspect · verdict
badge · the claim round trip · honest-empty; mutation-proven) · `tests/codebase-graph` (claim-only pin) · `tests/gabe-map`
(187, the 18th tool) · `tests/pulse-angles` (89, S9 two arms + S18) · `tests/entity-drift` (green unchanged — the rewire is
reporting-only) · `tests/draft-entities` (18, projection equality with two mutants).
