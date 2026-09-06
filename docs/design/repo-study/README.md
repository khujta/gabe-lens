# The repo-study program — pointing the Universe at repos you don't own

**Date:** 2026-09-06 · **Status:** passes 1–4 shipped · bootstrap shipped · tiers 0–3 installed on local branches
**Operator brief:** "fix these issues to make the suite more resilient and capable of processing different kinds of
repos, then take each tier repo in the repo study and treat it like a separate project, install the suite on each and
generate the center with the graph one by one — see that the suite is install-friendly, and update our docs."

## The goal it serves

`/home/khujta/projects/repo-study/learning-path/gabe-universe-rampup.md` — four foreign FastAPI repos, one per tier,
studied **read-only** by tracing ONE workflow per session in the Gabe Universe and drawing it from memory:

| tier | repo | why | missions |
|---|---|---|---|
| 0 · the mirror | fastapi/full-stack-fastapi-template | the typed FastAPI↔React contract (SQLModel · hey-api client) | auth spine · schema/model split · generated-client contract |
| 1 · the production spine | benavlabs/FastAPI-boilerplate (Fastro) | what survives load (jobs · cache · limits) | background job · cache-aside · rate limiter + tiers |
| 2 · AI plumbing | wassim249/fastapi-langgraph template | streaming · agent graph · vector memory · fallback | 4 traces |
| 3 · boss level | onyx | navigate what you cannot read | chat SSE · connector indexing · RBAC |

"Read-only" in this program means: **no source edits, nothing pushed upstream.** The center is installed INTO each
clone on a local `gabe-center` branch — that install IS the object under test (ruling 2026-09-06; the out-of-tree
build via `GABE_REPO_ROOT`/`GABE_CENTER_OUT`/`GABE_GRAFT_INDEX` stays available for a byte-clean tree).

## The gap review (6 agents, read-only, verified)

Out-of-tree builds already worked (tier0 and tier2 built into `/tmp`, repo untouched by an mtime sweep; `graft --dir`
keeps its index out too). The blocker was that **13 of 13 trace missions went dark** in the graph. 56 gaps deduped, the
first 20 reproduced by an adversarial verifier; grouped:

| group | what was wrong | where |
|---|---|---|
| backend arm | SQLModel `table=True` tables invisible (tier0/tier2: 0 models) · include_router-time prefixes ignored (100% / 88% / 84% wrong URLs on tiers 0/1/2) · `Annotated` alias + factory `Depends(f(args))` gates invisible · `code.api/models/schemas` took literal paths only, `**` not recursive · an unparseable file vanished silently (tier0 requires Python 3.14) | `_a3_code.py` |
| web bridge | a bare `/api` proxy mount never matched (onyx 30 → 251 of 352 with one regex) · the hey-api generated SDK was no idiom (tier0: no bridge at all) · Next.js App Router pages were not routes · one web root per repo (onyx `mobile/`, `widget/` invisible) · `typescript` absent from uninstalled clones | `_a3_web.py` · `_a3_fe.py` · `_a3_graph.py` |
| dispatch by name | Celery/ARQ/Taskiq `send_task(NAME)` carried no edge · workers never rooted a trace · a streaming endpoint read as a plain POST · the AI stack was no provider | `_a3_code.py` · `_a3_levels.py` · `_a3_graph.py` |
| the station at scale | onyx ≈ 3.9k nodes / 10k links with no budget · no way to open on ONE journey/entity | `gabe-universe.html` |
| adoption | no skill path adopts a repo without the human-speed back-catalog flow · `adoption.json` was a hard prerequisite · an absent graft index dir was hardcoded | `build_center_a3.py` · `/gabe-cc-init` |
| worksheet | tier1's T1 (ARQ job) and T2 (cache-aside) have NO application code at HEAD `2b6373d` | the learning path |

## What shipped in the suite (branch `graft-adoption`)

| pass | commit | rules | proof |
|---|---|---|---|
| 1 · backend arm | `8dea20d` | mount chain resolved through imports, `/api[/vN]` stripped (twin labels byte-identical: gustify 80/80 · gastify 49/49) · SQLModel tables · Annotated aliases (one import hop) · factory `callee` · config globs · `unparseable` named + PEP 758 shim · adoption stub · `GABE_GRAFT_INDEX` | center 140 · arch-graph 267 · pulse 65 |
| 2 · web + frontend | `4eccdef` | bare `/api` · `sdkTable` idiom (two-pass table) · Next.js `app/**/page.tsx` routes · `other_roots` named · actionable typescript reasons | arch-graph 273 · frontend 109 |
| 3 · dispatch by name | `4d85130` | `task_map` (Celery/ARQ/Taskiq → `dispatches`) · TASK roots (`endpoint:TASK <name>`, homed, seeded into the walk) · `stream` marker · AI providers | center 141 · arch-graph 277 |
| 4 · the station | `6743cfe` · `8b068b1` | node budget 1600 → boots folded above it (Sources row says so) · `?journey=` / `?ent=` deep links (boot + settle) · typescript provenance (`tsFrom`) | universe 556 + behavioral probe |
| adoption | `5e709c1` · `69becb8` | `bootstrap_center.sh` — the config-only adoption, deterministic, re-runnable; config-only registry rows carry every board field | center 150 |
| scale | `585c3d3` | `function_insight`: indexed reference scan (exact) · blocked twin pass above 2500 sizable fns, `fn_similarity` named | center 151 |

Measured on the study repos before/after (read-only dry runs): tier1 URL domains `/` ×6 · `/{username}` ×6 → `/users` 11 ·
`/api-keys` 8 · `/auth` 6 · `/rate-limits` 4 · `/tiers` 2; tier1 gated endpoints 2 → 20 of 35; tier0 gates 6 → 16 of 20;
tier0 bridge 0 → 17 sites (23 SDK methods); onyx groups.py-style labels, 63 tasks · 44 of 46 dispatch sites resolved.

## The install recipe (what a study project needs)

```
git -C <repo> checkout -b gabe-center                       # a local branch — never pushed
bash ~/.claude/templates/gabe/center/generators/bootstrap_center.sh <repo> --name <slug> --display "<name>"
#   → scripts/ (generators) · templates/center/shell/ · docs/site/center/center.config.json (entities: {}) · .gitignore seeds
# fill `entities` (code.api / models / schemas / services / web — literal paths or globs, ** recursive · test_rx)
# frontend? run the project's own install (bun install / npm ci) — or export GABE_TS_DIR=<dir with node_modules/typescript>
bash scripts/refresh_center.sh regen                          # archmap · c4-graph · every station page · chrome harness
# docs/site/center/workflows.js = the worksheet's missions as journeys → open gabe-universe.html?journey=<name>
```
The build takes the config's entities as the registry when `adoption.json` is absent (said out loud);
`/gabe-cc-init init · rank · section` records the adoption later without redoing any of this.

## The four installs

| tier | branch commit | endpoints · tables · graft calls | frontend · bridge | notes |
|---|---|---|---|---|
| 0 | `2ac980a` | 23 · 2 · 28 | 346 pieces (homed by config, 5 planets) · sdkTable 17/17 | bun installs at the repo root; universe 223 nodes; 3 journeys |
| 1 | `555929a` | 31 · 6 · 31 | — | 6 entities by module; gated 20; T1/T2 recorded as no-code-at-HEAD |
| 2 | `daedb62` | 11 · 3 · 17 | — | stream marked on `POST /chatbot/chat/stream`; providers langchain · langgraph · mem0 · openai · redis; 4 journeys |
| 3 | (local) | 512 · 155 · 5852 | 2602 pieces (8 planets) · fetch 188/351, 19 unhomed, `mobile/src` + `widget/src` named as not scanned | 9 entities by package; `data` owns the models file; 46 TASK roots + 32 dispatch edges; twin pass blocked (7,258 sizable → 1 M pairs); **universe 2,050 nodes → booted folded** (203 capsules, tier 0, ready in 17 s); regen 2.5 min; workflow B walks TASK roots |

## Friction log (what the install taught the suite)

- a first build on a config-only repo crashed on the synthesized registry row (`status`) → rows carry every board field.
- bun installs `node_modules` at the REPO root; the "deps absent" note looked at the package dir → the note now follows the
  extractor's own typescript provenance (`tsFrom`).
- the deep links waited for the force layout to settle (16 s headless on tier0) → applied at boot too.
- tier0 requires Python 3.14 (`except A, B:`); the suite runs 3.12 → the auth module had vanished → the PEP 758 shim.
- onyx: the archmap phase sat 10 minutes in two quadratic passes → indexed scan + blocked twin pass.
- `git add` with one missing pathspec stages nothing (a script lesson, not a suite defect).
- onyx docstrings carry prompt placeholders (`{{CURRENT_DATETIME}}`) that the chrome harness read as unfilled shell slots →
  the slot check is measured against the page's SKELETON (derived pages map to their family: `arch-*` ← `architecture.html`).

## Owed

- twins re-propagation (one pass at the end of the program — the generators moved through six commits).
- CLOSED 2026-09-06 — the station half of pass 3 (the legend pass, [legend-and-tools-plan.md](legend-and-tools-plan.md) Part A): the `dispatches` wire, the TASK method, the `delivery:stream` + `pclass` badge families, the three Sources rows, the FE homing witness — every element with its legend row + drawn example. Recorded: the suite's EXAMPLE estate (gustify) cannot show TASK or `dispatches` at any sha (no task runtime) — its rows carry the honest `—`; the twins' committed `c4-graph.json` changes when propagated (provider nodes gain `pclass`, `stats.providers.by_pclass` + `stats.route_mounts` appear; `levels.json` byte-identical); one LEGACY contrast pair outside the pass (`role:caller`, dark-on-dark at ~22) is reported by the contrast probe, not failed — owed to a role-palette pass.
- the LangGraph state-machine lens (tier2 T2/T3 — `add_node`/`add_edge` by string; trigger: the tier2 T2 session) ·
  a second web root (onyx mobile; trigger: a mobile mission) · the 2D fallback drops the frontend.
- the R10 carve-out as a stated ruling: suite-authored strings only; project identifiers keep their words.
- `/gabe-cc-init init` calls `bootstrap_center.sh` for its step 4 (spec pointer landed; the skill text still describes the copy by hand).
