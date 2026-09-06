# Plan — the legend catches up, and the tools learn the map (2026-09-06)

**Status:** PLAN — nothing built. Produced by two read-only planning workflows (Part A: 4 inventories + designer + critic +
synthesizer · Part B: 2 inventories that probed the tools on tier0/tier3 + a self-adversarial designer), after the
operator's correction: *"we might be planning too lightly — the legend for each new element with its example, the maps
and the generation scripts, and as a consequence the journeys."* The decisions for the operator are collected at the end.

Ground: suite `f00b1e2` (branch graft-adoption); the four study installs under `/home/khujta/projects/repo-study/tier{0..3}`
(local `gabe-center` branches); the twins gustify/gastify; the record [README.md](README.md).

---

# Part A — the legend catches up

Scope: the Gabe Universe station (both copies) + the sibling stations + the emitters that feed them + the consumers that count endpoints. HEAD `f00b1e2`, branch `graft-adoption`. Every anchor below was read at that sha; line numbers are for orientation — **the builder anchors on the literal with an assert-count-1 replacement, never on the line.** Every station edit lands in BOTH `templates/center/shell/gabe-universe.html` and `templates/center/shell/example/codebase-graph-station/gabe-universe.html` (they differ only at L1, L943-944, L957-958, L962, L964, L970, L972, L998, L1014-1015 — all placeholders above the first anchor).

---

## 1. What the pass changes, per element

| # | Element | Emitter change | Station registries touched | Legend compact | Legend reference (definition · example source) | Card | Tier | Consumers to guard |
|---|---|---|---|---|---|---|---|---|
| 0 | **TASK popover bug** (shipped today) | none | 2 — `__badgePop` key list L5915 + head L5918 | endpoint ⓘ now lists 7 methods | already there (L4522 `…"BOOT","TASK"].forEach`) · `_exMethod("TASK")` → `—` on the example, REAL on tier3 | none | endpoint's (T0) | run.sh L491 pin breaks → re-pin; add a paired assert (popover list == `_beSection` list) |
| 1 | **dispatches wire** (task enqueue + event bus, ONE kind) | none — `REL2KIND` is station-only; levels/c4 bytes untouched everywhere | 16 — `CONN` L1615 · dash map L1648 · `CONN_KINDS` L1616 · `REL2KIND` L1618 · `__uniBeam` L2080 · `wireRow` L3734 · `__CONNDESC` L3991 · `_EXREL` L4358 · `"x:dispatches"` in `_LRDEF` (beside L4451) · `_REFDESC` L4579 · `_CONNSTOCK` L4531 + `_dash` L4535 + stale comment L4530 · Trust map L5740 · `carriesSec` L5703 · `_HOP` L4719 · step copy L2954 · LEGEND row after L5875 | new `{t:"ln",k:"dispatches"}` row — swatch painted from live `CONN` by `vis()` L5958, click-to-hide free via `__uniBeam` | "a function hands work off by name — a queue or the event bus carries it; the sender does not wait" · `_EXREL.dispatches` → REAL on the example TODAY (`cooking.py#post_complete → progression.py#on_cooked_meal_created`, 2 wires); `—` on gastify/tier0-2; 24 on tier3 | link card: kind chip DISPATCHES + `__CONNDESC` line + Trust row + carriesSec note; node card already has `dispatches`/`dispatched by`/merge (L5278-5283, no edit) | inherits its END kinds (functions: T1+) | `_bkCollect` already walks it (L2673/L2697) — no edit; levels lab `codebase-archive-lab.html` L1442 collapses it to calls (Step 2); `codebase-graph.html`/`sim-panel.js`/`_a3_sim.py` never load `levels.js` → nothing owed, pin the boundary |
| 2 | **TASK roots are not HTTP endpoints** | `_a3_graph._counts` gains a `tasks` count (L107 precedent L1299) — OPTIONAL, see Decision 6 | 0 on the universe (covered) · sibling stations: `graph-grammar.js` L47 + 3 `ep` builders · `codebase-graph.html` L32/L612/L1257/L1676 (+L1470 verb) · `sim-panel.js` L69 · `codebase-archive-lab.html` L506 | already covered | already covered | universe step card L2936 gets a TASK sentence | — | **drafter** `draft-workflows.py` L40 + L196 + L21 · **S16** inherits (angles.py L614 comment) · S9/S13/S10/census measured SAFE (no edit; invariant recorded) · `endpoints` count in the drafter result L247 |
| 3 | **stream badge** (`delivery:stream`) | none — `stream:true` already emitted (`_a3_graph.py` L630-631); the EXAMPLE c4 is one regen stale (0 nodes today; gustify 1) | 12 — `__BADGE_COL` L3977 · `__BADGE_DESC` L3983 · glyph branch before L4023 + thin-stroke list L3997 · painter after the L1723-1726 chain · positioner `__slot` L4049 · `_exStream()` beside L4375 · reference row chained onto L4522 · `_LRDEF "delivery:stream"` · `__badgePop` L5915/L5918 · step card L2936 · header badge L5808 (leave on method) | NO second ⓘ on the endpoint row (one-slot design at L6012) — reaches the reader via the reference row + the card | "the answer arrives in pieces while you wait, not all at once at the end" · `_exStream()` → `—` until `regen-example.sh`, then REAL `endpoint:GET /recipe-creation/gustify/stream`; gastify 2 · tier2 1 · tier3 11 | `streamSec` L5345 already renders "Delivery" (mounted L5413) — no edit | endpoint's (T0) | `codebase-graph.html` has zero `stream` awareness — a Delivery row on `n.stream` (Step 2); `stats.web.sse` ≠ endpoint `stream` (the SSE trap — never one word for both) |
| 4 | **provider class** (`pclass`) | `_a3_code.py` `_PROVIDER_CLASS` beside L1688 (roster, never a project list) · `_a3_graph.py` L1340 `pclass` on the node + `det` · L1395 `by_pclass` beside `by_provider` | 13 — adapter L1223 · `__BADGE_COL`/`__BADGE_DESC` · glyph branch + L3997 list · painter chain L1726 append · `_exPc(pc)` · reference sub-rows under provider (L4519-4521, WITHOUT `noEx`) · `__badgePop` L5915/L5918 · compact ⓘ L6012 + title L6013 · header badge L5808 · NEW `C.provider` card near L5451 · `_LRDEF "pclass:*"` | provider kind row (cloud glyph as drawn) gains the ⓘ dot → popover paints the 8 class badges | one line per class in the user's words · `_exPc(pc)`: llm REAL (gemini) after regen; the other 7 `—` on the example; infra REAL gastify (firebase)/tier2/tier3; embed tier3 (voyage); vector tier2 (mem0); agent tier2; http tier3; observability tier3 (sentry); payments `—` EVERYWHERE | NEW `C.provider` — today a provider card body is EMPTY (no `C.provider`, L5411-5457) | provider's (T1: in Skeleton's `koff` L4128) | `codebase-graph.html` L608-609 `provider:"#e8590c"` == `web:"#e8590c"` (a colour collision, Step 2); `sim-panel.js` KIND_CHIP latent only; CLAUDE.md L65 roster sentence is a coverage claim, not exhaustive — no "correction" owed |
| 5 | **Sources rows** — `unparseable` · `route_mounts` · `fn_similarity` (+ the web idiom fold) | `_a3_graph.py` three `**({…} if … else {})` keys beside L1380 (`schema_homing` idiom); `extractor`/`sdk_methods` already emitted L1414/L1423 | 4 — three `srcRow` calls inserted after the cross-touches statement (ends at L5608) + the web row value L5610 | n/a | n/a (a panel section) | Sources block L5602-5621 | n/a | tests/arch-graph SILENT = `json.dumps`-identical stats without the blocks; every twin's stats gains `route_mounts` on its next regen (nodes/edges unchanged) |
| 6 | **FE homing by config** | none | 3 — Sources `st.fe.homing` L5617 (layout branch speaks) · adapter L1252 `homedBy` · FE card kv row (the `feBuilder` family, ~L5495) | none — nothing drawn, nothing listed | none | one `home` kv row on a config-homed piece (slug stripped of `fe·`) | n/a | tests/frontend: `homed_by` survives to `homedBy` |

---

## 2. Decisions for the operator

Only choices that change the outcome. Each: option → cost → what breaks → ONE recommendation.

**D1 · dispatches wire style + colour (the legend REFERENCE is where distinctness is judged).**
Verified: `_CONNSTOCK` L4531 paints fk/calls/rollup all as `dashed`; `_dash()` L4535 knows only dotted/dashed (unknown → solid). In 3D, `dashed` is unused (L1648: fk/bridge/rollup sparse · calls/access solid · imports dotted).
- (a) style `longdash` in BOTH palettes, colour `#f76707` kept (= `RELCOL.dispatches` L1180, so emitter/link/wire/legend agree). Cost: add `longdash:[2.6,1.2]` to the L1648 base map + `style==="longdash"?"10 4":` to `_dash`. Breaks: nothing pinned. Note the neighbourhood in the CONN comment: `RELCOL.reaches="#e8590c"` and `KINDCOL.provider="#e8590c"` are orange too.
- (b) style `dashed`, hue moved off amber (e.g. rose) and `RELCOL.dispatches` changed in the same commit. Cost: two hex edits; the reference still shows a `dashed` row under a `dashed` calls row, distinguished by hue only.
- **Recommend (a).** Pin `_CONNSTOCK.dispatches` == `CONN.dispatches` (col+style) in run.sh.

**D2 · one wire for event-bus AND task hand-offs, or two.**
- ONE (`dispatches`): station-only rename of the bucket; all levels.json/c4 bytes identical; the example draws a REAL chip. The mechanism is already visible at the TARGET (a task fn sits under `endpoint:TASK` with the violet queue badge L4029).
- TWO (`dispatches` + `enqueues`): an emitter marker (tier3's levels.json bytes change) or a second by-name join at adapter time; every rel-keyed registry (`RELCOL`/`LINKMETA` L1180-1181, `relLabel` L5278/5280, `CONNICO` L5283, `_bkCollect` L2673, `_HOP`, Trust L5740, run.sh L106-108) needs a sixth entry and `REL2KIND[...]||'calls'` L1659 masks any omission; a legend row `—` on 6 of 7 estates forever.
- **Recommend ONE.** Trigger for TWO: an operator asks to FILTER worker vs bus hand-offs — and even then it is a filter on the target's root kind, not a wire kind.

**D3 · `_SOLO_REL` and `_HOP` for dispatches (side effects the design missed).**
- `_SOLO_REL` L4193 + `dispatches:1`: `__uniComputeSolo` L4194-4196 COUNTS callers and FOLDS single-caller helpers (write-fabric exempt). A task fn with exactly one enqueuer (tier3's common case) gains its first parent and becomes fold-eligible under the enqueuer. **Recommend: drop from this pass**; trigger: a FIRE/SILENT solo pin proving a single-enqueuer task fn does not fold.
- `_HOP` L4719 + `dispatches:1`: the journey-detail matrix walks through an enqueue to the task's reads/writes — a real gap today, but on the example page it VISIBLY changes the matrix (progression/skills writes attach to the cooking step). **Recommend: keep**, say so in the commit, run the walk proofs (`verify-jrnstep`/`walk` in tests/gabe-universe) after.

**D4 · the delivery badge colour + slot.** Verified: the endpoint BODY is `#8b5cf6` (`KINDS.endpoint` L1062, `KINDCOL.endpoint` L1087); `hrole.streamer` is the same `#8b5cf6` (L3981); the file records two prior badge-on-body failures (L3979 blue-on-cobalt, L3981 amber-on-amber).
- (a) same GLYPH as the streamer (L4005 verbatim), colour cyan `#06b6d4`, second slot camera-right. Cost: a two-line positioner change (slot 0 = today's expression verbatim). Breaks: nothing pinned; POST `#3b82f6` is ~30° from cyan but sits one badge-width away with a different glyph — state it in the comment.
- (b) the streamer violet `#8b5cf6` → invisible on the endpoint ring (the L3979 class of bug). Rejected.
- (c) composite wave under the verb inside the method disc → no registry shape (`_badgeRow`/`__badgePop`/`_LRDEF` are family-keyed); the legend could never show it. Rejected.
- **Recommend (a).** Write the rule in the `__BADGE_COL` comment: *a disc never sits within ~30° hue of its host kind's body colour.* Before landing the second sprite, grep for single-badge assumptions (`grp.__cnt` L1725, `__uniSyncCountBadges`, hover scale) — `_mbTick` L4038-4052 itself is per-sprite and safe.
- **Sub-decision — the shipped TASK badge `#a78bfa` on the `#8b5cf6` body (same hue, lighter tint).** Recommend: add it to the contrast probe (Step 6) and leave the hex unless the probe flags it; if it does, `#f0abfc` (fuchsia-light) keeps the "violet family" read while clearing 30°.

**D5 · provider class vocabulary + roster rule + palette.** Verified roster L1688-1701; provider body `#e8590c` (L1161/L1170).
- Roster rule: **root-SDK scope** (what the SDK IS, never the one use seen) — the same law for every row. Consequence: `boto3→infra`, `firebase_admin→infra` (Auth+Firestore+FCM+Storage is a platform), `cohere→llm` (a full LLM SDK; tier3 uses it to rerank — flagged in the comment), `voyage→embed`, `sentence-transformers→embed`, `mem0→vector` (a memory layer over a vector store — flagged), `huggingface→llm` (transformers is a model runtime — flagged), `vertex→llm`.
- Vocabulary: with root-scope, NO root maps to `auth` → **EIGHT classes**: llm · embed · vector · agent · infra · http · observability · payments. `auth` returns the day an auth-only SDK root joins `_PROVIDER_ROOTS` (trigger). `payments` stays although no estate imports stripe — the roster is the vocabulary, the estate is the census.
- SIX coarse (`ai` folded): rejected — tier2's five providers collapse to three `ai` + infra, and the proposed sparkle is the role `pure` star (L4002) with a different meaning.
- Palette (contrast vs `#e8590c` ≈ 20°, intra-family distinct; glyphs carry the idea): `llm:"#d946ef"` (fuchsia, bubble) · `embed:"#a3e635"` (lime, vector arrow) · `vector:"#14b8a6"` (teal, the model cylinder L4013 verbatim) · `agent:"#8b5cf6"` (violet, the orchestrator fork L4007 verbatim) · `infra:"#8794ab"` (gray, the config cog L4014 verbatim) · `http:"#3b82f6"` (blue, the api wall L4011 verbatim) · `observability:"#ec4899"` (pink, an eye) · `payments:"#22c55e"` (green, a card). None within 30° of orange; nearest intra pair fuchsia/pink 38°.
- **Recommend EIGHT, root-scope rule, this palette.** Commit message must say: provider NODE bytes + `stats.providers` change on gustify/gastify/tier2/tier3; levels/edges unchanged.

**D6 · TASK roots in the drafter and the counts.**
- (a) skip TASK as infra (`verb in ("BOOT","TASK")`) AND `LABEL_RX` gains `|TASK`. Measured tier3: uncovered 540→494, unreached 365→319, skipped_infra 0→46, drafts unchanged 37; S16 prints 494/499. A curated TASK step never reaches the covered check (the skip runs first, L196 before L199) — exactly how BOOT behaves.
- (b) `LABEL_RX` alone: covered 8, 43 TASK still listed as "a bridge gap or a dead endpoint" (L311).
- (c) draft TASK roots as journeys: `draft_name()` would phrase a queue job as a screen action; `VERB_ORDER` L45 has no TASK rank.
- **Recommend (a).** The drafter's `"endpoints": len(endpoints)` (L247) keeps counting BOOT+TASK+infra — leave it (the battery pins `==5` at tests/workflow-drafts L64; a TASK fixture node makes it 6 → re-pin). Separately: `_a3_graph._counts.endpoints` (L107) never counts TASK; **do not fold TASK in** — if the operator wants the L1 card honest on tier3, add a separate `tasks` count following the L1299 precedent (optional; not required for the pass).

**D7 · the suite's example estate: gustify-only with `—` chips, or a second pinned snapshot.**
- gustify-only: after a plain regen the example shows REAL chips for dispatches · stream · BOOT · llm · infra? (no — gustify has gemini only) · route mounts (`24 router(s) mounted`) · `via apiFetch`; `—` for TASK (gustify has no worker queue — `grep -rlE 'celery|from arq|taskiq|shared_task'` hits only the vegetable in `shared/taxonomy.py`), 7 of 8 pclass rows, files skipped, twin pass, sdk_methods. FIRE proofs for those are synthetic (tests/arch-graph `_fixtk` L623-642 template) + static source pins.
- second snapshot (tier3): a second ~1 MB levels.json + c4 in the repo, a second regen recipe, a second render harness — for chips the reference already renders honestly as `—`.
- **Recommend gustify-only.** Trigger for a second snapshot: an operator needs to SEE a TASK chain on the suite's own page (a docs/demo need), not a proof need.

**D8 · badge precedence on the card header (endpoint wearing method + stream).** Keep the header badge on `method` (L5808); `streamSec` carries delivery in the body. **Recommend keep** — the 3D badge gets the second slot, the header does not (no two-slot header in this pass).

---

## 3. Build order

Legend: **[H]** = heavy, serial on this machine, wall-clock from today's runs. Each station step: identical `old_string` in BOTH gabe-universe.html copies, assert-count-1 in each.

### A · Step 0 — the shipped TASK bug (station, both copies) — light

1. `gabe-universe.html` L5915 · literal `["GET","POST","PUT","PATCH","DELETE","BOOT"]:(kind==="count")` → `["GET","POST","PUT","PATCH","DELETE","BOOT","TASK"]:(kind==="count")`.
2. L5918 · literal `(key==="BOOT"?"boot event — runs once at startup":"HTTP method")` → `(key==="BOOT"?"boot event — runs once at startup":key==="TASK"?"worker task — dispatched by name from a queue":"HTTP method")`.
3. `tests/gabe-universe/run.sh` L491 · re-pin `'DELETE","BOOT"]' in page` → `'DELETE","BOOT","TASK"]' in page`; add the missing glyph pin `"key==='TASK'" in page and 'c.lineTo(78,92)' in page`; add a paired assert that the `__badgePop` method array text equals the `_beSection` array text (extract both with a regex on `["GET","POST",…]` and compare).
4. Mutation-prove: revert 1 once → the paired assert fails.

### B · Step 1 — the drafter + S16 (the only step that changes a number an operator reads today) — light

5. `skills/gabe-cc-update/scripts/draft-workflows.py` L40 · `(?:GET|POST|PUT|PATCH|DELETE|BOOT) [^"]+` → `(?:GET|POST|PUT|PATCH|DELETE|BOOT|TASK) [^"]+`.
6. L196 · `if verb == "BOOT" or first.startswith("_"):` → `if verb in ("BOOT", "TASK") or first.startswith("_"):`.
7. L21-22 docstring · after `BOOT events,` add `TASK roots (a worker entrypoint dispatched by name is not a user workflow),`.
8. `skills/gabe-pulse/scripts/angles.py` L614 comment · `infra (_-prefixed) + BOOT sit outside it` → `infra (_-prefixed) + BOOT + TASK sit outside it`. No code change.
9. `tests/workflow-drafts/run.sh` · add a TASK node to the synthetic c4 (L28-39, copy the BOOT node at L39: `{"id":"endpoint:TASK reindex","kind":"endpoint","label":"TASK reindex",…}`) and a curated `"TASK reindex"` step in the fixture workflows.js; re-pin L64 `r["endpoints"]==5` → `==6` and `r["skipped_infra"]==["BOOT lifespan","POST /_e2e/seed"]` → include `"TASK reindex"` (sorted as the script sorts); assert the TASK label is in neither `drafts` nor `unreached` (the UNREACHED case L89-94). SILENT: the pre-existing cases stay green. Mutation: revert 6 → TASK lands in unreached → fails.
10. `tests/pulse-angles/run.sh` · add a TASK node to the C4WF fixture (L343-362); the L364 assert STAYS `3/3` (that is the regression: TASK must not enter the denominator). Run `tests/workflow-drafts/run.sh` then `tests/pulse-angles/run.sh` (both < 5 s, one after the other).

### C · Step 2 — the sibling stations' METHOD literals + the levels lab wire — light, batteries ≈ 3 s each

11. `templates/center/shell/assets/graph-grammar.js` L47 · `var METHOD = { GET: "var(--m-get)", POST: "var(--m-post)", PUT: "var(--m-put)",` → append `BOOT: "var(--m-boot)", TASK: "var(--m-task)"` inside the literal; in each of the three `ep` builders (L67/L88/L107, `var col = METHOD[method] || "var(--muted)";`) add a `method==="TASK"` queue-shape branch (three stacked bars + an exit arrow — the L4029 idea in SVG). This fixes `codebase-archive.html` L900 for free.
12. `templates/center/shell/codebase-graph.html` L32 · after `--m-delete:#d1443c;` add `--m-boot:#8a8f98; --m-task:#a78bfa;`; L612 · append `BOOT:"var(--m-boot)", TASK:"var(--m-task)"` to `var METHOD = {…}`; L1257 and L1676 · `var m=methodOf(label)||"GET";` (2 sites — `replace_all` or two edits) → `var m=methodOf(label)||null;` and let `epMark` fall to `var(--muted)` (keep `methodOf`'s null contract — L1470 depends on it); L1470 · after `if(m) h+=rowKV("method", m);` add `if(n.stream) h+=rowKV("delivery","streams — SSE / chunked; the response is an async generator, not one payload");` (verify `n` is in scope there; else read `p.stream` through the same path the label comes from); L608-609 · `provider:"#e8590c"` → `provider:"#f08c00"` (or any hex ≠ `web`) — the pin is inequality, not the value.
13. `templates/center/shell/assets/sim-panel.js` L69 · append `BOOT: "#8a8f98", TASK: "#a78bfa"` to `METHOD_COLOR`; unknown verbs still fall to `#868e96` (L82).
14. `templates/center/shell/codebase-archive-lab.html` L506 · append `BOOT`/`TASK` to its own `METHOD` literal; L1442 · `ed.rel==="imports"?"imports":"calls"` → `ed.rel==="imports"?"imports":ed.rel==="dispatches"?"dispatches":"calls"` with a `kindPath` style `dispatches` (colour `#f76707`, long dash) and `regEdge(p, … "dispatch" …)`; add the wire to the lab's `legend([...])` call (L1447-1449) drawn as the actual stroke.
15. Batteries, serially: `tests/codebase-graph/run.sh` (add beside L376-382: FIRE `'TASK:"var(--m-task)"' in station and 'methodOf(label)||"GET"' not in station`; `'n.stream' in station` + the Delivery literal; `KIND_COLOR.provider !== KIND_COLOR.web` parsed from the two literals; a NEGATIVE pin `'dispatch' not in station` for the c4-only station; sim-panel `TASK: "#a78bfa"` + the `#868e96` fallback) → `tests/levels-page/run.sh` (a `rel:'dispatches'` fn_edge gets its own class/word; a `calls` edge still `.e-calls`) → `tests/levels/run.sh` (copy the class-8 block L159-169 twice: a graft call carrying `rel:'dispatches'` survives into `fn_edges`; `task_roots` puts the task fn in `drawn_fn`; SILENT byte-identical without). Mutation-prove each new pin once.

### D · Step 3 — the dispatches wire on the universe (both copies) — light; universe battery **[H] ≈ 1.5 min**

16. L1648 · `({dashed:[1.7,1.0], dotted:[0.35,0.95], sparse:[1.4,2.8]})` → `({dashed:[1.7,1.0], dotted:[0.35,0.95], sparse:[1.4,2.8], longdash:[2.6,1.2]})`.
17. L1615 `CONN` · after `access:{…}` (the last entry) append `, dispatches:{color:0xf76707,style:'longdash',density:1.9,trust:0.55,grad:false,thick:1,gmode:'type'}` with a comment naming the `#e8590c` provider/reaches neighbourhood.
18. L1616 · `var CONN_KINDS=['fk','bridge','calls','imports','rollup','access'];` → `…,'access','dispatches'];`.
19. L1618 · `dispatches:'calls'` → `dispatches:'dispatches'` (occurs once).
20. L2080 · `rollup:0, access:0.7 };` → `rollup:0, access:0.7, dispatches:0.7 };`.
21. L3734 · `wireRow("calls")+wireRow("imports")` → `wireRow("calls")+wireRow("imports")+wireRow("dispatches")` (the run.sh L235 pin is a substring — stays green).
22. L3991 `__CONNDESC` · append `, dispatches:"a function hands work off by name — a queue or the event bus carries it, the sender does not wait"` inside the literal.
23. L4358 `_EXREL` · after `access:["fnwrites","fnreads"],` insert `dispatches:["dispatches"],`.
24. `_LRDEF` · after L4451 `"x:calls":"one backend function calls another, across areas",` insert `"x:dispatches":"a function hands work to a worker or an event bus by name — it names the job and moves on; the job runs later, somewhere else",`.
25. L4579 `_REFDESC` · after the `calls:` entry insert `dispatches:"one function enqueues or publishes to another by its registered name — the call does not wait, and the link is inferred from the name (a floor)",`.
26. L4531 `_CONNSTOCK` · append `, dispatches:{col:"#f76707",style:"longdash"}`; L4535 `_dash` · `style==="dotted"?"1.5 3.5":style==="dashed"?"6 3":""` → `…:style==="dashed"?"6 3":style==="longdash"?"10 4":""`; L4530 stale comment `rollup/access aren't in CONN at all` → `rollup/access ARE in CONN (L1615) but stock keeps the semantic hues`.
27. L5740 Trust map · after `imports:"inferred · import floor"` add `, dispatches:"inferred · by-name floor (the target is resolved from its registered name)"`.
28. L5703 `carriesSec` · before `return note("— a control wire: the props / arguments it carries…` insert `if(rel==="dispatches"){ return note("— the job's arguments: the sender names the task and passes a payload the extractor does not read"); }` (confirm the local is named `rel` in that function; else use the name the function binds).
29. L4719 · `_HOP={calls:1, fecall:1, bridge:1, fetches:1, handler:1, uses:1};` → `…, uses:1, dispatches:1};` (per D3; `_SOLO_REL` L4193 untouched).
30. L2954 · `— the event bus routes here after "+esc(frmL)+" publishes` → `— handed off here by name: a queue or the event bus routes to this function after "+esc(frmL)+" enqueues / publishes`.
31. Legend row · after L5875 `{t:"ln",k:"calls",l:"calls <i>a cross-entity function call</i>"},` insert `{t:"ln",k:"dispatches",l:"dispatches <i>a function hands work off by name — a queue or an event bus carries it</i>"},` (never a literal `c:` — run.sh L243 guards it).
32. `_a3_levels.py` L281 comment · `# class 6: a dispatch edge keeps rel:'dispatches'` → `# class 6 + 13: event-bus AND task-enqueue edges keep rel:'dispatches'` (comment only, bytes of output unchanged).
33. Battery `tests/gabe-universe/run.sh`: static pins `"dispatches:'dispatches'"`, `"dispatches:{color:0xf76707"`, `'dispatches:0.7'`, `'wireRow("dispatches")'`, `'{t:"ln",k:"dispatches"'`, `'"x:dispatches":'`, `'dispatches:{col:"#f76707",style:"longdash"}'`, `'longdash:[2.6,1.2]'`, `'dispatches:1}'` on the `_HOP` line, the L2954 literal (update the L331 pin), a CONN==STOCK equality parse; render probe `dispSel` modelled on `wireSel` (L1333): pick a positioned `l.rel==='dispatches'` link on the EXAMPLE page (2 exist today), assert drawn + card kind chip `DISPATCHES` + the reference row's chip is `.lrexl` not `.lrnone`; run the jrnstep/walk solo proofs. **[H] ≈ 1.5 min, nothing else running.**

### E · Step 4 — emitters (pclass + Sources stats) + the example regen — light, then **[H]**

34. `templates/center/generators/_a3_code.py` · after the `_PROVIDER_ROOTS` literal closes (L1701 `}`) add `_PROVIDER_CLASS` keyed by provider NAME (the value side of `_PROVIDER_ROOTS`), comment stating the root-scope rule and the flagged rows: `{"openai":"llm","anthropic":"llm","gemini":"llm","litellm":"llm","mistral":"llm","groq":"llm","together":"llm","ollama":"llm","vertex":"llm","huggingface":"llm","cohere":"llm", "voyage":"embed","sentence-transformers":"embed", "pgvector":"vector","qdrant":"vector","pinecone":"vector","mem0":"vector", "langchain":"agent","langgraph":"agent", "redis":"infra","aws":"infra","firebase":"infra", "http":"http", "sentry":"observability", "stripe":"payments"}`.
35. `_a3_graph.py` L1340 · `"label": _p, "det": {"provider": _p}}` → `"label": _p, "det": {"provider": _p, "pclass": _PC.get(_p)}, "pclass": _PC.get(_p)}` with `_PC = _a3_code._PROVIDER_CLASS` imported/aliased once; L1395 · `"by_provider": dict(sorted(_prov_by.items()))}` → add `, "by_pclass": dict(sorted(Counter(_PC.get(p) for p in _prov_by if _PC.get(p)).items()))` (unknown names excluded — honest-empty).
36. `_a3_graph.py` beside L1380 (`**({"schema_homing": …`) add three keys in the same idiom: `**({"unparseable": {"count": len(_up), "files": [f[0] for f in _up][:12]}} if (_up := amap.get("unparseable")) else {}),` · `**({"route_mounts": {"mounted": int(_rm.get("mounted") or 0), "routers": int(_rm.get("routers") or 0), "unresolved": list(_rm.get("unresolved") or [])}} if isinstance((_rm := amap.get("route_mounts")), dict) else {}),` · `**({"fn_similarity": {"mode": _fs.get("mode"), "pairs": _fs.get("pairs"), "budget": _fs.get("budget")}} if isinstance((_fs := amap.get("fn_similarity")), dict) and _fs.get("mode") else {}),`. (`fn_similarity` reaches the archmap ONLY when blocked — build_center_a3.py L1989-1990 — so the station never says "exact".)
37. `tests/arch-graph/run.sh` · FIRE: an archmap file importing `langchain` → provider node `pclass=="agent"` + `stats.providers.by_pclass=={"agent":1}`; unknown root → `pclass is None`, node otherwise identical; a synthetic archmap carrying `unparseable` (`[["a.py","SyntaxError"]]`), `route_mounts` (tier3's dict shape incl. an `unresolved` DICT `{"file","line","why"}`), `fn_similarity` `{"mode":"blocked","pairs":9,"budget":2}` → the three stats keys with those shapes. SILENT: the same archmap without the blocks → `json.dumps(stats)` identical to the pre-change build (bit-for-bit; use the `web=None`/`fe=None` byte-identity pattern the battery already has). Run it (< 30 s).
38. **[H] `bash docs/design/codebase-graph-consolidation/universe-build/regen-example.sh`** (plain — NEVER `--check` with uncommitted station edits: L107 `git checkout` reverts the example page). Lands: `stream:true` on `endpoint:GET /recipe-creation/gustify/stream`, `pclass:"llm"` on `provider:gemini`, `stats.route_mounts {mounted 24, routers 1, unresolved []}`, `stats.providers.by_pclass {llm:1}`. Its tail runs `tests/gabe-universe/run.sh` (L116) — that is the ≈1.5 min. Commit the estate refresh as its own commit with the byte classes stated.

### F · Step 5 — pclass badge family + Sources rows + `C.provider` (both copies) — light; battery **[H] ≈ 1.5 min**

39. L1223 · `middleware:p.middleware, stream:!!p.stream };` → `middleware:p.middleware, stream:!!p.stream, pclass:p.pclass||null };`.
40. L3977-3982 `__BADGE_COL` · after the `hrole:{…}` line add `pclass:{llm:"#d946ef",embed:"#a3e635",vector:"#14b8a6",agent:"#8b5cf6",infra:"#8794ab",http:"#3b82f6",observability:"#ec4899",payments:"#22c55e"},` + the comment rule (*never within ~30° of the host body — provider body is #e8590c*).
41. L3983 `__BADGE_DESC` · add `pclass:{ llm:"llm — a text/completion model the code calls", embed:"embed — turns text into vectors (embeddings / rerank)", vector:"vector — a similarity store the app searches by meaning", agent:"agent — an orchestration framework (langchain / langgraph) that drives model calls", infra:"infra — rented plumbing: cache, queue, object store, a platform SDK", http:"http — a plain outbound HTTP client, provider unnamed", observability:"observability — where errors and traces are shipped", payments:"payments — money moves through here" },`.
42. L3997 · `kind==="mclass"||kind==="hrole"?11:13` → `kind==="mclass"||kind==="hrole"||kind==="pclass"||kind==="delivery"?11:13` (one edit serves Step 6 too).
43. Before L4023 `} else {` (the METHOD fallthrough) insert `} else if(kind==="pclass"){ … }` with: `llm` bubble `c.moveTo(36,42); c.lineTo(92,42); c.lineTo(92,76); c.lineTo(60,76); c.lineTo(46,90); c.lineTo(48,76); c.lineTo(36,76); c.closePath(); c.moveTo(50,59); c.lineTo(78,59);` · `embed` arrow `c.moveTo(36,88); c.lineTo(88,40); c.moveTo(66,40); c.lineTo(88,40); c.lineTo(88,62);` · `vector` = the mclass `model` path (L4013) verbatim · `agent` = hrole `orchestrator` (L4007) verbatim · `infra` = mclass `config` (L4014) verbatim · `http` = mclass `api` (L4011) verbatim · `observability` eye `c.moveTo(32,64); c.bezierCurveTo(48,40,80,40,96,64); c.bezierCurveTo(80,88,48,88,32,64); c.moveTo(76,64); c.arc(64,64,12,0,6.2832);` · `payments` card `c.moveTo(34,44); c.lineTo(94,44); c.lineTo(94,84); c.lineTo(34,84); c.closePath(); c.moveTo(34,58); c.lineTo(94,58);` · else `c.arc(64,64,15,0,6.2832)`.
44. Painter L1726 · append to the chain `else if(n.kind==="provider" && n.pclass){ try{ grp.add(feclassBadge(n.pclass,"pclass")); }catch(_pb){} }` (`feclassBadge(key,family)` L1717 is the generic wrapper — no new factory).
45. Beside L4375 `_exMethod` add `function _exPc(pc){ return _exNode(function(n){ return n.kind==="provider" && n.pclass===pc; }); }`.
46. L4521-4524 `_beSection` · leave `_kids` as is (provider keeps its own gemini chip — `_typeRow(k,noEx)` L4498 suppresses it when true); add a branch after the schema branch: `else if(k==="provider"){ var _pt=_minTierKind("provider"); ["llm","embed","vector","agent","infra","http","observability","payments"].forEach(function(pc){ h+=_badgeRow("pclass", pc, pc, (BD.pclass&&BD.pclass[pc])||"", _exPc(pc), _pt); }); }`.
47. `_LRDEF` (near L4451) · `"pclass:llm":"a model that writes text for you", "pclass:embed":"turns your text into numbers so it can be compared", "pclass:vector":"where the app keeps meanings so it can search by similarity", "pclass:agent":"the conductor that decides which model call comes next", "pclass:infra":"plumbing the app rents — cache, queue, storage, a platform", "pclass:http":"a plain call out to someone else's URL", "pclass:observability":"where errors go to be seen", "pclass:payments":"where money moves",`.
48. L5915 · before the role fallback `:["accessor","caller","gate","pure"]` insert `:(kind==="pclass")?["llm","embed","vector","agent","infra","http","observability","payments"]:(kind==="delivery")?["stream"]`; L5918 · both arms gain `(kind==="pclass")?"provider class — what kind of outside service this is":(kind==="delivery")?"delivery — how the answer reaches the client":` BEFORE the role fallback (the 269d17c stray-branch class).
49. L6012 · `(it.k==="hook")?"hrole":null;` → `(it.k==="hook")?"hrole":(it.k==="provider")?"pclass":null;`; L6013 title · add `(_bik==="pclass")?"the provider classes (what kind of outside service)":` before the fallback.
50. L5808 · `: (n.kind==="function" && n.role) ? {kind:"role", key:n.role} : null;` → `… : (n.kind==="provider" && n.pclass) ? {kind:"pclass", key:n.pclass} : null;`.
51. New `C.provider` before L5451 `external:function(n){`: `provider:function(n){ var det=n.det||{}; return [ usage(usageN(n), usageBreak(n)), (n.pclass?E("div",{class:"sec"}, sechd("info","Class"), E("div",{class:"sublbl"}, icoEl("link"), n.pclass+" ", E("span",{style:"color:var(--muted);font-size:10px"}, (window.__BADGE_DESC&&__BADGE_DESC.pclass&&__BADGE_DESC.pclass[n.pclass])||""))):null), liveConns(n), docSec(det,"Note")||E("div",{class:"sec"}, sechd("doc","Note"), E("div",{class:"doc"},"An outside service a function reaches — the edge of the system, past the last owned line.")), fileRowSec(n) ]; },` — `docSec` (L5392) and `fileRowSec` (L5393) are honest-empty on `det={provider,pclass}` (verified: both return null without `doc`/`file`).
52. Sources (after the cross-touches statement, whose tooltip literal ends `…the dotted touches wires between entities"));` L5608): `if(st.unparseable&&st.unparseable.count) w.append(srcRow("alert","files skipped", st.unparseable.count+" .py file(s) the scanner could not parse", "Every mapped .py the AST scanners skipped — a NAMED gap, never silence. Whatever those files define is missing from this graph: "+(st.unparseable.files||[]).join(", ")));` · `if(st.route_mounts){ var _ru=st.route_mounts.unresolved||[]; w.append(srcRow("link","route mounts", st.route_mounts.mounted+" router(s) mounted"+(_ru.length?(" · "+_ru.length+" prefix(es) unresolved"):""), "include_router() calls the scanner resolved to a URL prefix. An unresolved prefix is a non-literal expression (settings.API_V1_STR, a router built by a call) — its endpoints' paths are a FLOOR, so a bridge match can miss them.")); if(_ru.length) w.append(chipList(_ru.map(function(u){ return u.file+":"+u.line+" — "+u.why; }), "link", "link", 3)); }` (the items are DICTS — map before `chipList` L5172; `route` is NOT in the `icoEl` map, `link` is) · `if(st.fn_similarity) w.append(srcRow("layers","twin pass", "blocked — "+st.fn_similarity.pairs+" pairs over a "+st.fn_similarity.budget+" budget, an approximation", "The structural-twin (duplicate-function) pass. Shown only when the pass was blocked — the repo was too large for the exact comparison, so the twin verdicts are an approximation, said out loud."));` · web row L5610: prepend `(st.web.extractor?("via "+st.web.extractor+" · "):"")+` to the value and append `+(st.web.sdk_methods?(" · "+st.web.sdk_methods+" SDK method(s) read from the generated client"):"")`; tooltip `every apiFetch call site` → `every fetch call site (the idiom named first)`. No "orphan" anywhere.
53. Battery: static pins `'pclass:p.pclass||null'`, `'pclass:{llm:"#d946ef"'`, `"key==='llm'"`, `'n.kind==="provider" && n.pclass'`, `'function _exPc(pc)'`, `'_badgeRow("pclass", pc, pc,'`, `'"pclass:llm":'`, `'provider:function(n){'`, the four `srcRow(` literals + `'st.web.extractor'`, `'(kind==="pclass")?"provider class":' not in page` (mirror of L889); re-pin L899 `'(it.k==="hook")?"hrole":null'` → `'(it.k==="hook")?"hrole":(it.k==="provider")?"pclass":null'` and L907 likewise; headless loop L1531-1532: `if(b.dataset.badgeinfo==='pclass' && n!==8) ok=false;`; render: open `provider:gemini` → card has a `Class` section (FIRE) and the reference `llm` row chip is `.lrexl`, `payments` row is `.lrno` (the honest dash). **[H] ≈ 1.5 min.**

### G · Step 6 — the delivery badge (both copies) — light; battery **[H] ≈ 1.5 min**

54. `__BADGE_COL` · add `delivery:{stream:"#06b6d4"},` (comment: host body `#8b5cf6`, 71° off; POST `#3b82f6` one badge-width away, 30°). `__BADGE_DESC` · `delivery:{ stream:"stream — the response is an async generator: pieces leave as they are made, so the client sees the first byte early and an error can land mid-body" },`.
55. Glyph · before the `} else if(kind==="pclass"){` branch insert `} else if(kind==="delivery"){` + the streamer path (L4005) VERBATIM: `c.moveTo(34,50); c.bezierCurveTo(44,38,54,62,64,50); c.bezierCurveTo(74,38,84,62,94,50); c.moveTo(34,78); c.bezierCurveTo(44,66,54,90,64,78); c.bezierCurveTo(74,66,84,90,94,78);`.
56. Painter · a SEPARATE statement after the L1723-1726 chain (an endpoint's slot is spent on method): `if(n.kind==="endpoint" && n.stream){ try{ var _sb=feclassBadge("stream","delivery"); _sb.__slot=1; grp.add(_sb); }catch(_sb0){} }`.
57. Positioner L4049 · `b.position.set(e[0]*ox+e[4]*oy+e[8]*3, e[1]*ox+e[5]*oy+e[9]*3, e[2]*ox+e[6]*oy+e[10]*3);` → `var _sx=ox+((b.__slot||0)*(sz*0.72)), _sy=oy; b.position.set(e[0]*_sx+e[4]*_sy+e[8]*3, e[1]*_sx+e[5]*_sy+e[9]*3, e[2]*_sx+e[6]*_sy+e[10]*3);` (`sz` is bound at L4042; slot 0 is today's expression verbatim).
58. Beside `_exMethod` · `function _exStream(){ return _exNode(function(n){ return n.kind==="endpoint" && n.stream; }); }`; L4522 · after the method `forEach(...)` chain `h+=_badgeRow("delivery", "stream", "stream", (BD.delivery&&BD.delivery.stream)||"", _exStream(), _et);`; `_LRDEF` · `"delivery:stream":"the answer arrives in pieces while you wait, not all at once at the end",`.
59. Step card L2936 · after the gates clause append `+(n.stream?" It streams: the reply keeps arriving after the first byte (SSE / chunked).":"")` and a TASK arm: when `n.m&&n.m.method==="TASK"` the `what` text is `"Worker task — runs on a worker, dispatched by name from a queue. "` instead of `"API endpoint — the entity's outward door. "` (reuse the L4444 wording).
60. Battery: static pins (`'delivery:{stream:"#06b6d4"}'`, `'kind==="delivery"'`, `'n.kind==="endpoint" && n.stream'`, `'_sb.__slot=1'`, `'(b.__slot||0)*(sz*0.72)'`, `'_badgeRow("delivery", "stream"'`, `'"delivery:stream":'`, `'function _exStream()'`); render probe `streamSlot`: FIRE — the group of `endpoint:GET /recipe-creation/gustify/stream` holds 2 Sprite children with different `position.x` after one tick; SILENT — a non-stream endpoint holds 1 Sprite and its `position.x` equals the value computed by the old expression; contrast probe — for every drawn badge, `__BADGE_COL[family][key]` hue is ≥30° from `KINDS[n.kind].col` hue (report the shipped TASK/#8b5cf6 pair; D4 decides). **[H] ≈ 1.5 min.**

### H · Step 7 — FE homing (both copies) — light

61. L5617 · `(st.fe.homing==="config"?"homed by the config's web claims (no feature layout) · ":"")` → `(st.fe.homing==="config"?"homed by the entity config's web claims (no feature layout) · ":st.fe.homing==="layout"?"homed by the feature layout · ":"")`; tooltip gains *HOW pieces were given a home: by the feature layout, or by the entity config's web claims when the repo has no feature layout — the same home, a different witness.*
62. L1252 · `hrole:p.hrole||null` → `hrole:p.hrole||null, homedBy:p.homed_by||null` (append-only; the L899 pin stays green).
63. FE card builders (~L5495 family) · one row `n.homedBy==="config"?kv("link","home","claimed by "+String(n.ent||"").replace(/^fe·/,"")+"'s config — no feature folder names it"):null`.
64. `tests/frontend/run.sh`: `homed_by` present on the config estate fixture, absent on the layout one; run.sh static pins for 61-63. Render is byte-identical (nothing drawn) — no probe.

### I · Step 8 — install, docs, doctor, estates

65. `./install.sh` (≈5 s).
66. Docs: `templates/center/shell/README.md` L36 table — add a `codebase-archive-lab.html` row (loads `./c4-graph.js` + `./levels.js`, battery `tests/levels-page`, the only non-universe `dispatches` surface); extend the L45/L54/L55 rows with the kind+wire vocabulary each page draws (methods incl. BOOT/TASK · stream · provider class · dispatches). `CLAUDE.md` L63 (codebase-graph station bullet) — one sentence: the method roster (GET/POST/PUT/PATCH/DELETE + BOOT + TASK, one shared literal in `assets/graph-grammar.js`), the Delivery row on `stream`, the provider CLASS as a node field. `CLAUDE.md` L65 — append the render half: the `dispatches` wire kind, the `delivery:stream` + `pclass` badge families, the three Sources rows; state the root-scope roster rule. `docs/design/repo-study/README.md` L89 Owed — one bullet closing "the station half of pass 3" and recording: the example estate cannot show TASK at any sha; twins' committed outputs change (byte classes below). `regen-example.sh` L116 — add `tests/codebase-graph/run.sh` after the universe battery (serial).
67. **[H] `scripts/suite-doctor.sh` once, at the end — ≈4 min, nothing else running.**
68. **[H] Tiers 0–3 regen** (`/home/khujta/projects/repo-study/tierN`, tier3 ≈ 2.5 min, the others less; one at a time) — verifies: tier3 draws 46 TASK roots with the popover fixed, 24 long-dash orange wires, 11 stream badges on the second slot, 9 provider badges across llm/embed/infra/http/observability, Sources shows `11 router(s) mounted · 3 prefix(es) unresolved` with three chips + `twin pass blocked — 997658 pairs over a 2500 budget`; tier2 `POST /chatbot/chat/stream` + mem0 vector + langchain/langgraph agent; tier0 `via sdkTable · 23 SDK method(s)`; S16 on tier3 prints `494/499`. Journeys: tier3's three curated workflows walk unchanged (83 steps); the TASK steps now count as covered labels.
69. **Twins (gustify/gastify) — READ-ONLY by ruling; ≈2 min each when the propagation pass runs.** What changes and why it is the point: `c4-graph.json` provider nodes gain `pclass` (`gemini→llm`, `firebase→infra`) + `stats.providers.by_pclass` + `stats.route_mounts` (`{24,1,[]}` / `{21,0,[]}`); levels.json byte-identical; the station file itself. gastify's two SSE endpoints wear the stream badge.

---

## 4. Invariants and proofs

- **Byte-identity where the element is absent, stated per estate.** Element 1: no data bytes change anywhere (station-only). Element 3: no data change (`stream` already emitted); the example is one regen stale. Element 4: provider NODE bytes + `stats.providers` change on gustify/gastify/tier2/tier3; tier0/tier1 identical. Element 5: `stats.route_mounts` appears on all six twins (a mounted count is information, not emptiness), `fn_similarity` on tier3 only, `unparseable` nowhere; nodes/edges untouched. `tests/arch-graph` pins SILENT = `json.dumps`-identical without the blocks. The commit messages carry these byte classes.
- **Legend = the actual glyph/wire as drawn.** Every new `ln` row carries `k` (run.sh L243 guards literal `c:`); `vis()` L5958 paints from live `CONN`; the reference paints from `_CONNSTOCK` — pinned equal to `CONN.dispatches` (col + style) so the two cannot drift; badge rows paint through the same `__badgeGlyph` repaint (L4615). The delivery glyph is the streamer path verbatim; five pclass glyphs are existing idea-pairs verbatim (api wall, cylinder, cog, fork).
- **Every reference row carries an example chip or `—`.** Resolvers `_exLink` (via `_EXREL.dispatches`), `_exStream()`, `_exPc(pc)`; `_exLinkChip` L4363 / `_exChip` L4379 emit the honest dash. On the suite's example after the plain regen: dispatches REAL · stream REAL · BOOT REAL · TASK `—` (at every sha) · pclass llm REAL, 7 rows `—` · route mounts REAL (`24 router(s) mounted`) · files skipped / twin pass ABSENT (no estate has them) · `via apiFetch` REAL. Rows are never hidden because the estate lacks them.
- **Honest-empty.** No badge without a field (`pclass` null → no badge, no Class section; `stream` false → one sprite at the pre-change x); no Sources row without its key; the twin-pass row exists only when blocked (never "exact"); `carriesSec` names the un-read payload; `__badgePop` gets explicit `delivery`/`pclass` branches BEFORE the role fallback and a `not in page` pin mirrors L889; the `layout` homing branch speaks.
- **R10.** New copy uses unresolved · skipped · unmatched · detached. The station has 0 "orphan" (verified). Standing violations outside this pass, logged not touched: `angles.py` L327 `orphan domain(s)` and `entity_shape.py`'s `orphans` key.
- **TASK/BOOT are not HTTP endpoints — the rules.** Drafter skips them (Step 1); S16 inherits; S9 reads `entities[].endpoints` only (measured zero TASK there — `task_roots` is a separate key; INVARIANT: never merge `task_roots` into `entities[].endpoints`, or `url_domain()` mints 46 pseudo-domains); census `check_workflow_drift.py` is verb-free (workflows.js ≠ the census); `_a3_graph._counts.endpoints` never counts TASK (L107 vs L1299); `methodOf()` keeps its null contract and the three `||"GET"` coercions go; fetch_bridge/S10 key-space stays HTTP-only; `_a3_sim.py` prices MODEL change only — a TASK root never enters the blast radius (pin SILENT in tests/sim by planting `task_roots`; do not "fix").
- **Headless probes, by estate.** Example page (after regen): `dispSel` (2 real wires) · `streamSlot` FIRE/SILENT · pclass popover count 8 · `C.provider` Class section on gemini · contrast probe. Synthetic only (tests/arch-graph `_fixtk` L623-642 + static source pins, the BOOT pattern at run.sh L489-492): TASK · unparseable · fn_similarity · sdk_methods · payments. **Never write a render probe that needs a TASK node — it fails forever on this twin.** `verify-tiers.mjs` L107 `fleet.fc === 6` — leave `_FCALL` L4125 alone; badges add no nodes so monotonic reveal stays green.
- **The STREAM/SSE trap.** `stats.web.sse` (frontend fetch SITES using an SSE idiom: gustify 1 · gastify 2 · tier3 0) and endpoint `stream` (backend delivery: tier3 11) measure opposite ends of one wire. The badge reads `n.stream` only; if the web row ever names `sse`, it says "N SSE fetch site(s)", never "streaming endpoints".
- **Two-file law.** The static battery reads one copy; `verify-tiers.mjs` L8 renders the other. A one-file edit passes one proof and fails the other. Each step: identical `old_string`, assert-count-1 in each file.
- **Mutation proof.** Every new pin is reverted once and watched fail before the commit (a checker that cannot fail is non-evidence).

---

## 5. What stays out (with triggers)

| Out | Why | Trigger to bring it in |
|---|---|---|
| `enqueues` as a second wire kind | the mechanism is drawn at the target root; permanent `—` on 6 of 7 estates | an operator asks to FILTER worker vs bus hand-offs → a filter on the target's root kind |
| `_SOLO_REL.dispatches` | may fold single-enqueuer task fns under the enqueuer | a FIRE/SILENT solo pin proving a single-enqueuer task fn does not fold |
| widening the d2w band (L1663) to dispatch legs | a separate heat decision | an operator asks for enqueue hops inside the distance-to-write heat |
| a second ⓘ on the endpoint compact-legend row | one-slot design (L6012) | a second badge family on any OTHER kind row makes the two-slot ⓘ generic |
| a two-slot card HEADER badge (method + stream) | `streamSec` already carries delivery in the body | the operator asks for the header to show both |
| `auth` provider class | no root in `_PROVIDER_ROOTS` is auth-only under the root-scope rule | the first auth-only SDK root joins the roster |
| a `tasks` count on the L1 entity card (`_a3_graph._counts`) + a TASK section in the classic endpoint tables (`_a3_code.py` L78 `_METHOD_CLS`, L3147 cells) + a stream pill there | HTML tables are HTTP-only by construction; a decision, not a defect | tier3's operator reads "endpoints: 12" against a drill drawing 12+N — then a SEPARATE `tasks` count/section from `amap["task_roots"]`, never a merge into `entities[].endpoints` |
| the journeys picker row badge colour/glyph for TASK chains (`_jrnRow` L2740) + a stream marker on journey rows | the flag is not on the journey record; `_bkCollect` would need to carry it | an operator wants worker chains separable in the picker → a filter, not a 7th tab (`_JRNKINDS` L2827) |
| `codebase-graph.html` drawing the newer `cross_edges` kinds (touches/nests/serializes/reads_from/writes_to/consumes/walls/gated_by — only `bridge` is drawn, L1216/L1648) | outside the six elements | the change-sim station is asked to show data coupling; then L1216 filter + L972 `edgeWord` + L1031 map + legend rows together |
| `codebase-archive.html` drawing provider/middleware/flag as a MODEL cylinder (L897-901) | a separate wave-C-class defect | any regen where an ecosystem view shows a provider — extend the kind branch like `codebase-graph.html` L1257-1261 |
| a per-piece config-homing badge | all-or-nothing per estate (`_a3_fe.py` L443-454) — zero bits within one canvas; a dashed ring collides with the fe-unknown tell (L1124) | `_a3_fe.py` homes pieces by config INDIVIDUALLY (mixed estates) |
| searching `stream` / `llm` from the header box (`_collect` L4265) | the reference chips are the discovery path | an operator types a badge key into search and expects hits → widen the `extra` arg |
| a second pinned example snapshot (tier3) | D7 | a docs/demo need to SEE a TASK chain on the suite's own page |
| the R10 violations in `angles.py` L327 / `entity_shape.py` | outside this pass | its own R10 sweep commit |
| twins regen | READ-ONLY by ruling | the standing propagation pass (memory: ~17 commits behind) |

---

# Part B — the tool layer

**Status: BUILT 2026-09-06** (P0–P2 · F1–F15 · F17 · N1 `trace` · N2 `gates`; F16 no change by design). The battery and the study-repo probe numbers are in the commit; the design record's Owed list carries what this part hands back to Part A (the `emitted` list, D5).

**Ground truth this section stands on.** Suite HEAD `f00b1e2`; `skills/gabe-map/scripts/tools.py` 695 lines · `tools_wave2.py` 552 · `mapquery.py` 505; SKILL.md 1.1.4; the battery pins `len(names) == 15` at `tests/gabe-map/checks.py:238`. Re-verified on disk this session: `tools.py:20` HTTP verb regex, `tools.py:294-296` endpoint projection, `tools.py:242/248` bare-name join, `tools_wave2.py:173-174` dead web ternary, `tools_wave2.py:220/229` blast join, `mapquery.py:147-153` the four loaders (no `levels`). On tier3: `levels.json` holds 2,982 `fn_edges` (calls 2,498 · depends 428 · reaches 32 · dispatches 24; conf extracted 927 / inferred 2,055); `archmap.app_middleware` = 4 ASGI classes; `route_mounts` `{mounted 11, routers 7, scanned 8, unresolved[3]}`; `fn_similarity {mode: blocked, pairs: 997658, budget: 2500, sizable: 7258}`; `c4.stats.gate_endpoints` 476; `stats.providers.count` 9; `stats.fe.homing` 'config'; `l1` nodes carry `status: 'config-only'`. tier0 `route_mounts.unresolved[0].why` = `non-literal prefix: settings.API_V1_STR`, `app_middleware` absent.

The one-line diagnosis both inventories converge on: **eleven new map facts, zero reach a tool** — six are projection drops (data loaded, one line from the answer), five are join-key mismatches, two are missing readers (`levels.json`, `app_middleware`). So Part B is a **projection-and-join pass over the existing 15 + one loader**, plus exactly two new tools. Fewer, sharper.

---

## B.0 Prerequisites (no tool changes, everything below depends on them)

| Id | What | Anchor | Change |
|---|---|---|---|
| **P0** | `levels.json` loader | `mapquery.py:145-150` `@property def config … def archmap … def c4 … def adoption` | Add `@property def levels` (lazy `_load_json(self.dir / "levels.json")`, honest `{}` when absent) and an `idx["fn_out"]` / `idx["fn_in"]` pair keyed on the edge's `s`/`t` (`file#fn` form), with `rel`+`conf` carried. Built once per `Center` on first use — 3.2 MB on tier3, ≈50 ms; **never loaded by a tool that does not ask for it** (map_status stays at 193 ms). |
| **P1** | TASK addressability | `tools.py:20` `HTTP = re.compile(r"^(GET\|POST\|PUT\|PATCH\|DELETE\|HEAD\|OPTIONS)\s+(/\S*)$", re.I)` | Second regex `TASK = re.compile(r"^TASK\s+(\S+)$", re.I)`; `detect_kind` gains a `task` branch BEFORE `function_bare`. `idx` gains `task_by_name` (from `archmap.task_roots[].path` — the REGISTERED name, e.g. `cleanup_idle_sandboxes`) and `task_by_fn` (`task_roots[].fn`, e.g. `cleanup_idle_sandboxes_task`), each → `(root record, c4 node "endpoint:TASK <name>")`. A bare-name lookup that misses `function_insight` falls through to `task_by_name` before saying "map miss". |
| **P2** | Absence semantics for omitted-when-empty keys | `build_center_a3.py:1989-1996` `if _unp: amap["unparseable"] = _unp` / `if _mts: amap["route_mounts"] = _mts` / `if _fsm.get("mode") == "blocked": …` | One helper `mq.health_key(archmap, key)` → `(value, state)` with state ∈ {`present`, `clean` (absent AND `route_mounts` present — the sentinel that the repo-study pass ran; all four tiers carry it), `not_emitted` (absent AND no sentinel — an older map; text: "regen to know")}. Every health line below prints the state word. See D5. |

---

## B.1 Fixes

Format per row: **tool · anchor · change · battery (FIRE / SILENT) · SKILL.md text**. Battery cases go in `tests/gabe-map/checks.py` — fixture literals at `:131` (archmap) / `:138` (c4) / `:90` (the endpoint), assertions `ok(cond, msg, extra)` at `:30` inside `run(T)` at `:212`; the mutation lever is `SERVER_OVERRIDE` (`run.sh:20`).

### F1 · `touches` endpoint branch — `stream` + app-scope gates
- **Anchor:** `tools.py:294-296` `"endpoint": {"method": method, "path": ep.get("path"), "handler": fkey, "status": ep.get("status"), "resp": ep.get("resp"), "doc": …, "middleware": ep.get("middleware"), "touches_own": ep.get("touches")}`
- **Change:** add `"stream": bool(ep.get("stream"))` to the dict; add a sibling top-level `"app_middleware": [{cls,file,line,order,scope}…]` read from `archmap.app_middleware` with note `"ASGI-scope — applies to EVERY request before the route's Depends; absent block → none recorded"`. Same two lines on the TASK branch (P1) so a task answer has the same shape.
- **FIRE:** set `"stream": True` on the fixture endpoint (`checks.py:90`) and add `"app_middleware": [{"cls": "RateLimiterMiddleware", "file": "apps/api/app.py", "line": 12, "order": 0, "scope": "all"}]` to the archmap literal → `res["endpoint"]["stream"] is True` and `res["app_middleware"][0]["cls"] == "RateLimiterMiddleware"`. **SILENT:** a second fixture endpoint without the key → `stream is False`; archmap without `app_middleware` → `app_middleware == []` with the absent-block note.
- **SKILL.md:** `touches` row "Answers" gains "… endpoint (stream flag, per-route gates + the ASGI middleware that also applies)".
- **Probe:** tier2 `POST /chatbot/chat/stream`, tier3 `POST /chat/send-chat-message` (stream true), tier1 `PATCH /rate-limits/{name}` (RateLimiterMiddleware at `app_factory.py:263`).

### F2 · `touches` function branch + `blast_radius` — the bare-vs-qualified join
- **Anchors:** `tools.py:242` `bare = key.split("::", 1)[1].split(".")[-1]` + `tools.py:248` `if bare in (b.get("names") or []):`; `tools_wave2.py:220` `bare = {k.split("::", 1)[1].split(".")[-1] for k in fns}` + `:229` `if hkey or (names & bare):`
- **Change:** compute `qual = key.split("::", 1)[1]` (`MemoryService.search`); match `qual in names`; fall back to `bare in names` ONLY when `"." not in qual` (a plain function). Same in blast_radius as a set of quals ∪ the plain-function bares. This is stricter than today in one direction (a method no longer matches through its bare name, which was a false positive class) and correct in the other.
- **FIRE:** fixture `function_insight` key `apps/api/services/thing.py::Svc.search` + fixture endpoint node `behind.names: ["Svc.search"]` → `touches("…::Svc.search").endpoints_reaching.found == ["endpoint:GET /things/{item_id}"]`; blast_radius on that file lists the endpoint `via: "behind.names (floor, cap 12)"`. **SILENT:** `behind.names: ["Other.search"]` → `found == []` (the bare `search` must NOT bridge two classes).
- **SKILL.md:** no text change (the row already claims the join); add a line to the `who_calls`/`touches` note: "method targets join on `Class.method`".
- **Probe:** tier2 `app/services/memory.py::MemoryService.search` (positive control: the stream endpoint's `behind.names` lists it).

### F3 · TASK roots addressable — `touches` · `find` · `entity_context` · `cases_for`
- **Anchors:** `tools.py:20` (P1); `tools_wave2.py:74-93` "the add() sources are entities · function_insight · fe.pieces · web_by_stem"; `tools_wave2.py:528` kind enum; `tools.py:192-194` `for n in ((c.get("l2") or {}).get(slug) or {}).get("nodes") or []: k = n.get("kind") or "?"`
- **Change:** (a) `touches("TASK <name>")` → the P1 branch returns `{matched, kind: "task", entity, task: {name, fn, file, doc, handler}, dispatched_by: [{from: "file#fn", conf}]}` (the `dispatched_by` list from P0's `fn_in` filtered `rel == "dispatches"`; honest `{reason: "no levels.json"}` without P0's file) + the same `behind`/`access` blocks the endpoint branch reads off the c4 node; (b) `find` gains an `add("task", root["path"], slug, root["file"], {"fn": root["fn"]}, doc)` loop over `archmap.task_roots` and `"task"` in the enum; a task is found by its REGISTERED name or its fn name; (c) `entity_context.c4.l2_node_kinds` counts ids starting `endpoint:TASK ` under `"task"`, and `code.counts` gains `tasks` + `streams`; (d) `cases_for("TASK x")` routes through P1 and reports honest-empty by name ("no by_endpoint row for TASK x — task roots are not entity endpoints in test_insight").
- **FIRE:** archmap literal gains `"task_roots": [{"method": "TASK", "path": "sweep_things", "fn": "sweep_things_task", "file": "apps/api/tasks.py", "doc": "Sweep", "resp": "—", "status": "—", "touches": []}]`, `"tasks": {"tasks": [...same...], "stats": {"tasks": 1, "sites": 1, "edges": 1, "unresolved": []}}`; c4 l2 `thing.nodes` gains `{"id": "endpoint:TASK sweep_things", "kind": "endpoint", "label": "TASK sweep_things"}` → `touches("TASK sweep_things").matched`, `touches("sweep_things").kind == "task"`, `find("sweep")` has a `kind == "task"` hit, `entity_context("thing").c4.l2_node_kinds == {"endpoint": 1, "task": 1, …}`. **SILENT:** `touches("TASK nope")` → `found False` with reason naming `task_roots`; a map without `task_roots` → no `"task"` key in the histogram, `find(kind="task")` → `total 0`, note "no task_roots block".
- **SKILL.md:** `find` row lists "tasks (TASK <name>)"; `touches` row adds "task root (TASK <name> — registered name or fn)"; instructions line (F17).
- **Probe:** tier3 `TASK check_for_indexing`, `cleanup_idle_sandboxes` (name ≠ fn), `dispatched_by` on `check_for_vespa_sync_task` (2 edges from `document_set/api.py`).

### F4 · `find` — ranking, dedupe, generated-client noise, providers, stream filter
- **Anchors:** `tools_wave2.py:51` `if n.startswith(q): return 70` vs `:53` `if q in n: return 50`; `tools_wave2.py:82` `add("model", m.get("cls") or "", slug, m.get("file"), {"table": m.get("table")}, m.get("doc") or "")`; `tools_wave2.py:95` `hits.sort(key=lambda h: (-h[0], h[1]["kind"], h[1]["name"]))`
- **Change:** (a) kind bonus: `entity/endpoint/task/model/provider` +25, `schema/function` +10, `define/fe/screen` +0 — so an endpoint substring hit (50+25) outranks a generated define prefix hit (70+0); (b) dedupe: a `define` and an `fe` piece with the same `(name, file)` collapse into the `fe` hit; a `schema`/`model` with the same `(cls, file)` across entities collapses into ONE hit with `entities: [...]` (tier0's 54→18); (c) `-30` for a file matching `\.gen\.|/client/|/generated/` (the score stays named in `ranking`); (d) a `"provider"` kind sourced from every c4 l2 node with `kind == "provider"` (id `provider:<name>`); (e) input `stream: true` restricts endpoint hits to `ep.get("stream")` and every endpoint hit carries `"stream": bool` so the SSE missions can ask "which endpoints stream".
- **FIRE:** fixture gains an endpoint `POST /login/access-token`, a define `loginLoginAccessTokenData` in `apps/web/client/types.gen.ts` + an fe piece of the same name/file, a provider node `provider:litellm` → `find("login").hits[0].kind == "endpoint"`, the gen row appears ONCE, `find("litellm").hits[0].kind == "provider"`, `find(kind="endpoint", stream=True).total == 1`. **SILENT:** existing `find("thing")` ordering assertion unchanged (pin it); `find(kind="provider")` on a map without provider nodes → `total 0`, note "no provider nodes in c4".
- **SKILL.md:** `find` row: "… entities, endpoints (⚡ stream filter), tasks, models, schemas (deduped per file), functions, providers, screens, FE pieces; generated clients de-ranked".
- **Probe:** tier0 `find("login")` (endpoint first), tier3 `find("stream", kind="endpoint", stream=True)` → 13, `find("litellm")`.

### F5 · `map_status` — distinct counts + `map_health`
- **Anchors:** `tools.py:62` `"endpoints": sum(len(e.get("endpoints") or []) for e in ents.values()),`; `tools.py:63` `"schemas": sum(len(e.get("schemas") or []) for e in ents.values()),`
- **Change:** `schemas` counts distinct `(cls, file)` and prints `schemas_rows` beside it when they differ; add `tasks` (len `task_roots`), `streams` (endpoints with `stream`), `providers` (`c4.stats.providers.count`), `app_middleware` (len); add `out["map_health"] = {route_mounts: {mounted, routers, unresolved: N}, unparseable: N, fn_similarity: {mode, pairs, budget} , tasks_unresolved: [...], web: {extractor, other_roots, unhomed, unmatched: N}, schemas_zero: bool}` — each through P2 with its state word. A `schemas: 0` on a map with >0 endpoints prints `schemas_zero: "the schema arm extracted nothing — an EMPTY arm, not a clean one"`.
- **FIRE:** archmap literal gains `"route_mounts": {"mounted": 1, "routers": 1, "scanned": 1, "unresolved": [{"file": "apps/api/app.py", "line": 3, "why": "non-literal prefix: settings.PREFIX"}]}` and `"fn_similarity": {"mode": "blocked", "pairs": 10, "budget": 5, "sizable": 9}`; c4 stats gains `"web": {"present": True, "extractor": "fetch", "unmatched": [{"m": "GET", "p": "/x"}], "other_roots": ["mobile/src"], "unhomed": 1, …}` → `map_health.route_mounts.unresolved == 1`, `fn_similarity.mode == "blocked"`, `web.other_roots == ["mobile/src"]`, `counts.tasks == 1`, `counts.streams == 1`. **SILENT:** delete `fn_similarity` and `unparseable` → state `clean` (sentinel present); delete `route_mounts` too → `not_emitted` with "regen to know".
- **SKILL.md:** `map_status` row: "is there a map here, how fresh, graft state, regen command, **and where it is partial (map_health: mounts · unparseable · twins · web roots)**".
- **Probe:** tier3 (3 mounts, twins blocked, schemas 0, 2 other_roots), tier0 (1 mount `settings.API_V1_STR`, clean elsewhere).

### F6 · `map_census` — the map-health home
- **Anchors:** `tools_wave2.py:267-269` `sections = {"file": block("file_census"), "model": block("model_census"), "route": block("route_census"), "schema": (…)}`; `:262` `return {"reason": "no %s block in this archmap (version %s)" % (name, a.get("version"))}`; `:541` enum `["file", "model", "route", "schema"]`
- **Change:** four new sections — `unparseable` (`[[file, why]]` via P2), `mounts` (`route_mounts.unresolved[]` each `{file, line, why}` + the `mounted/routers/scanned` counts), `twins` (`fn_similarity` when `mode == "blocked"`, text "a pass that did not run: N pairs over budget M"), `web` (`stats.web.extractor` · `other_roots[]` "second frontends never scanned" · `unhomed` · `unmatched: N` + first 12 named, cap named); the `schema` section gains the empty-arm guard ("0 schemas extracted across N endpoints — arm produced nothing, not clean"); `tasks` unresolved kinds (`tasks.stats.unresolved`) ride the `mounts` section as a sibling line. Enum grows to `file|model|route|schema|unparseable|mounts|twins|web`. The `note` at `:276` gains "absent block = not emitted (older map) unless the study-pass sentinel is present".
- **FIRE:** same fixture as F5 → `census.mounts.unresolved[0].why` startswith `non-literal prefix`, `census.twins.mode == "blocked"`, `census.web.other_roots == ["mobile/src"]`, `census.unparseable` (add `"unparseable": [["apps/api/integrations/x.py", "unparseable: bad"]]`) has 1 row; a map with `schemas` all empty and 1 endpoint → `census.schema.empty_arm` truthy. **SILENT:** remove the keys → each section `{state: "clean"}`; `kind="mounts"` on a map with `unresolved: []` → `unresolved == []`, no `reason`.
- **SKILL.md:** `map_census` row: "where the map is blind: unclaimed files/models/routes, unwired/ambiguous schemas, **unparseable files, unresolved route mounts, the blocked twin pass, unscanned frontend roots + unhomed fetches**".
- **Probe:** tier3 (every section fires), tier0 (mounts only).

### F7 · `center_overview` — dead web branch, absence≠0, config-only registry, names
- **Anchors:** `tools_wave2.py:173-174` `… for k in ("screens", "fetch_sites", "matched", "unmatched") …} if isinstance((st.get("web") or {}).get("unmatched"), int) else {"unmatched": len(…)}` (structurally dead — emitter `_a3_graph.py:915` `_unmatched: list[dict] = []` → `:1419` `"unmatched": _unmatched`); `:169-171` `"census_gaps": {"files_unclaimed": len((a.get("file_census") or {}).get("unclaimed") or []), …`; `:175` `"unregistered": sorted(set(center.entities()) - set(ad)),`
- **Change:** (a) delete the ternary; `web = {extractor, screens, fetch_sites, matched, unmatched: len(list), dynamic, unhomed, other_roots, sse, sdk_methods (when present)}`; (b) `census_gaps.*` → `None` when the block is absent (mirror `routes_unclaimed`'s guard), with a `census_absent: [...]` list; (c) when `adoption.json` is absent AND the c4 l1 nodes carry `status: "config-only"` → `registry: "config-only (bootstrap_center.sh — no adoption.json; /gabe-cc-init to adopt)"`, `unregistered` omitted, rows carry `status: "config-only"`; (d) `arms` gains `providers: [names]` (from `stats.providers.by_provider` keys), `fe: {present, homing}`, `app_middleware: N`, `gate_endpoints: N`; (e) one `map_health` line = F5's object (shared helper, not a second implementation).
- **FIRE:** c4 stats web literal with a LIST `unmatched` → `web.extractor == "fetch"` and `web.unmatched == 1`; delete `adoption.json` from the fixture write loop (`checks.py:160`) + set l1 `status: "config-only"` → `registry` startswith `config-only` and `"unregistered" not in res`; delete `file_census` → `census_gaps.files_unclaimed is None`. **SILENT:** with adoption.json present the existing `unregistered` assertion holds; `web.present False` → `web == {"present": False, "reason": …}` verbatim.
- **SKILL.md:** `center_overview` row: "… arms (graft · web extractor · fe homing · providers · app middleware), census gaps (absent ≠ 0), registry mode".
- **Probe:** tier3 (`extractor fetch · 80 screens · 188/352 · other_roots 2 · registry config-only · providers 9`), tier0 (`sdkTable · 23 sdk_methods · 17/17`), tier1 (`unregistered` gone).

### F8 · `entity_context` — split histogram, streams, gates at full, homing, config-only
- **Anchors:** `tools.py:110-111` `for slug in sorted(mapped - seen): rows.append({… "note": "in archmap, not in adoption.json"})`; `tools.py:141, 149-150` (the brief/full endpoint projection that drops `stream`/`middleware`); `tools.py:192-194`
- **Change:** list mode: when no adoption.json and l1 says `config-only`, the note becomes `"config-only registry"` once at the top, rows carry `status: "config-only"`; `code.counts` gains `streams`, `tasks`; `detail=full` endpoint lines carry `stream` and a `gates: [callee(args)…]` line built from `middleware[].name` where `gate` is true; `c4.l2_node_kinds` splits `task` (F3) and `c4.providers` names them (`["aws","redis","sentry"]`) instead of `provider: 3`; `c4.fe_home` gains `homing` from `stats.fe.homing`.
- **FIRE:** fixture endpoint with `stream: True` + middleware `{name: "auth", gate: True}` → `entity_context("thing", detail="full").code.endpoints[0].gates == ["auth"]` and `.stream is True`; provider node → `c4.providers == ["litellm"]`. **SILENT:** `detail="brief"` line unchanged except the `⚡` marker; no provider nodes → `c4.providers == []`.
- **SKILL.md:** row: "one entity's slice (brief · full incl. gates + stream · raw); omit slug → the registered list, **or the config-only list when no adoption.json**".
- **Probe:** tier3 `indexing` (`endpoint 75 · task 46 · providers [aws, redis, sentry]`), tier1 `rate-limit`.

### F9 · `touches` file branch — the screen→endpoint leg (candidate #5 as FIELDS)
- **Anchor:** `tools.py:341` `"web_node": {"entity": web[0], "id": web[1].get("id")} if web else None})`
- **Change:** beside `web_node`, emit `fe: {pieces: [{name, kind, hrole, feClass, fed2w, channel, cache, sites, wsites, homed_by, span}], calls: [{endpoint: "endpoint:POST /login/access-token", kind: "bridge"}…]}` — `calls` from `idx["edges_out"][web_id]` (already built), pieces from `c4.fe.pieces` filtered on file. Cap 12 named.
- **FIRE:** fixture fe piece with `hrole: "fetcher", homed_by: "config"` + a `cross_edges` bridge from `web:apps/web/hooks/useX` to the endpoint → `touches("apps/web/hooks/useX.ts").fe.calls[0].endpoint == "endpoint:GET /things/{item_id}"`, `.fe.pieces[0].hrole == "fetcher"`. **SILENT:** a backend file → `"fe" not in res`.
- **SKILL.md:** `touches` row adds "a screen/hook file → its pieces (hrole · fed2w · homing) and the endpoints it fetches".
- **Probe:** tier0 `frontend/src/hooks/useAuth.ts` (3 bridges), tier3 any of the 32 fetching files.

### F10 · `owner_of` · `outline` — `_census_entry` consults `unparseable`
- **Anchors:** `tools.py:367-371` (`_census_entry`); `tools.py:618-619` `"census": _census_entry(a, p), "note": None if owners else "unowned by the map — the map is BLIND here; …"`; `tools_wave2.py:126` `out["signatures"] = "graft index (%s)" % wiring["hash"]`
- **Change:** `_census_entry` checks `archmap.unparseable` first → `{claimed: False, reason: "unparseable: <why>"}`; `outline` on such a file says `definitions: []` **because** of it (`census.reason`), never "an empty file". Two lines; fixes both tools.
- **FIRE:** `unparseable: [["apps/api/integrations/x.py", "unparseable: bad"]]` in the fixture + the file present in the temp repo → `owner_of("apps/api/integrations/x.py").results[0].census.reason` startswith `unparseable:`; `outline` same path → `census.reason` same. **SILENT:** a mapped file → `census` unchanged (existing assertion).
- **SKILL.md:** `owner_of` row "… where the map is blind (**and why: unparseable files named**)".
- **Probe:** none of the four study maps carries the key today (the PEP 758 shims fixed tier0) — probe on the fixture only; state that in the commit.

### F11 · `cases_for` — the corpus grep excludes the suite's own installs
- **Anchor:** `tools.py:571-572` `mq.sh(["git", "-C", root, "grep", "-ohIE", "(^|[^A-Za-z0-9])C[0-9]{1,5}(v[0-9]+)?([^0-9]|$)", "--", …])`; `:576-578` `out["corpus"] = {"searched": …, "max_cid_seen": mx or None, "next_cid_floor": (mx + 1) if mx else None, …}`
- **Change:** append pathspec excludes `':!docs/site/center/**' ':!scripts/_a3_*.py' ':!**/generators/**'` (the study inventory traced tier0's phantom `C4` to `scripts/_a3_tests.py:473`); when `.kdbp/` is absent add `corpus.note: "no .kdbp/ — this repo mints no C-ids; the floor is a corpus artefact, not a registry"` (tier3's 12345).
- **FIRE:** temp repo gains `tests/x_test.py` with `C7` → `max_cid_seen == 7`. **SILENT:** temp repo gains `scripts/_a3_tests.py` containing `the C4 L2 elements` and `C99` → `max_cid_seen` stays 7.
- **SKILL.md:** `cases_for` row "… the corpus's max C-id and next-id floor (**suite installs excluded; meaningless without .kdbp/, and says so**)".
- **Probe:** tier0 (4→None), tier3 (12345→None with the note).

### F12 · `review_drift` — web_bridge false positives (the `tasks` subject is CUT, see B.3)
- **Anchor:** `tools_wave2.py:459-461` `new_f = fb.diff_new_fetches(diff) … cls = fb.classify_new_fetches(new_f, keys) if new_f else {}`
- **Change:** filter the diff handed to `fb.diff_new_fetches` to hunks whose file is not under `docs/site/center/` or a `generators/` dir (gabe-map side, no pulse edit) — the two phantom `GET /x` / `GET …` rows on BOTH study repos came from the center-install commit's own template prose. The proper guard against comment/docstring literals stays in `gabe-pulse/scripts/fetch_bridge.py` as a follow-up outside this part (it fires on every twin commit that touches the center).
- **FIRE:** temp repo third commit adds `docs/site/center/x.html` with `fetch('/x')` → `subjects.web_bridge.new_fetches == []`. **SILENT:** a real `apps/web/hooks/useY.ts` adding `fetch('/y')` → `new_fetches == [["GET","/y"]]` (pin the true positive so the filter cannot over-reach).
- **SKILL.md:** no text change.
- **Probe:** tier0 `base=HEAD~1` → `new_fetches []`.

### F13 · `entity_shape` — the mounts caveat
- **Anchor:** `tools.py:486-487` `endpoints, umap = es.load_project(Path(center.root)); shape = es.entity_shape(endpoints, umap)`
- **Change:** `out["mounts_unresolved"] = N` + one caveat line appended to `one_line` when N>0: "· N route mount(s) unresolved — the domain table is partial" (from `archmap.route_mounts.unresolved`).
- **FIRE:** F5 fixture → `mounts_unresolved == 1` and `one_line` contains "unresolved". **SILENT:** `unresolved: []` → `mounts_unresolved == 0`, `one_line` unchanged (pin the existing string).
- **SKILL.md:** `entity_shape` row "… a diff's new routes (**caveated when route mounts are unresolved**)".
- **Probe:** tier3 (3), tier0 (1).

### F14 · `map_diff` — task roots as a first-class delta
- **Anchor:** `tools_wave2.py:298-301` `"endpoints": {"%s %s" % (e.get("method"), e.get("path")) for e in ent.get("endpoints") or []}`
- **Change:** `_ent_sets` gains a top-level `tasks` set from `task_roots[].path`; output gains `tasks: {added, removed}` and `health_delta: {mounts_unresolved: (base, head), unparseable: (base, head)}` (two ints each, via P2).
- **FIRE:** the temp repo's regen commit adds a task root → `map_diff(base=HEAD~2).tasks.added == ["sweep_things"]`. **SILENT:** docs-only commit → `regenerated False`, `tasks` absent.
- **SKILL.md:** row "… per entity, **plus task roots and the health delta**".
- **Probe:** twins only — the study installs have one center commit (`git show` honest reason already verified).

### F15 · `blast_radius` — the dispatch arm + task roots as entry points (needs P0/P1)
- **Anchor:** `tools_wave2.py:229-230` `if hkey or (names & bare): endpoints[nid] = {"entity": slug, "via": "handler in changed file" if hkey else "behind.names (floor, cap 12)"}`
- **Change:** (a) a changed file that defines a task root lists it under `tasks_defined[]` (an entry point, same class as an endpoint); (b) `tasks_dispatched[]` = for every changed function key, the `fn_out` edges with `rel == "dispatches"` → `{task, from, conf}`; (c) `reading` may now say `cross-process` when (b) is non-empty.
- **FIRE:** fixture `levels.json` literal (P0 case) with one `dispatches` edge from `apps/api/api/things.py#get_thing` → `blast_radius(files=["apps/api/api/things.py"]).tasks_dispatched[0].task == "endpoint:TASK sweep_things"`. **SILENT:** no `levels.json` → `tasks_dispatched == {"reason": "no levels.json — dispatch edges unread"}`.
- **SKILL.md:** row "… endpoints reached, **tasks dispatched (levels.json, conf per edge)**, tests, FE pieces".
- **Probe:** tier3 `files=["backend/onyx/server/features/document_set/api.py"]` → `check_for_vespa_sync_task`.

### F16 · `who_calls` — no change
The one tool that reads no map; the arm-difference IS its health signal. Note for the ramp-up: `graft callers` on tier3 walks a 61 MB index (2.4 s measured) — fine per call, not in a loop. `direction=out` was EMPTY on tier0 (`callees: []`) — that is why N1 reads `levels.json` and does not shell to graft.

### F17 · `INSTRUCTIONS` — the discovery surface
- **Anchor:** `tools.py:665-678` (the fifteen routing lines + floor law; pinned by the battery and echoed in `initialize`).
- **Change:** four lines added, none removed:
  - `- which endpoints does a gate / Permission.X guard; what ASGI middleware applies to every request → mcp__gabe-map__gates`
  - `- the ordered path from an endpoint or TASK to the models and providers it reaches (conf per hop) → mcp__gabe-map__trace`
  - `- a celery/background TASK root, a streaming endpoint, a provider (litellm · redis · …) → find / touches take "TASK <name>", stream=true, kind=provider`
  - `- where the map is PARTIAL (unparseable files · unresolved mounts · blocked twin pass · unscanned frontend roots) → mcp__gabe-map__map_census (map_status carries the one-line map_health)`
  - The floor law paragraph gains one clause: "A trace hop marked `inferred` is graft's guess, not a proof."
- **Battery:** the existing instructions pin (grep of the initialize response) gains the four substrings.

**Out of Part B (emitter side, for Part A):** tier0 SQLModel models carry `"cols": []` (mission T0-2 has no field list) — a `_a3_code.py` fix, not a projection.

---

## B.2 New tools — two, not eight

### N1 · `trace` — the ordered path (candidate #1)
- **Instructions line:** "the ordered path from an endpoint, TASK or function to the models and providers it reaches, one hop per line with its confidence → mcp__gabe-map__trace"
- **Inputs:** `start` (`"METHOD /path"` · `"TASK <name>"` · `"file::fn"` · `"file#fn"`), `depth` (default 4, max 8), `rels` (default `["calls","dispatches","depends","reaches"]`), `fanout` (default 8, max 20), `root`.
- **Output (text, indented):**
  ```
  trace from POST /chat/send-chat-message · gates: require_permission(Permission.WRITE_CHAT) · app: CORS, CaptchaCookie, LoginCaptcha, ClientIP · map@f1a685fa80 fresh
  └ chat_backend.py#handle_new_chat_message                      [start · stream ⚡]
    ├ calls (inferred)  process_message.py#stream_chat_message   models: ChatMessage r/w · ChatSession r
    │ ├ reaches (inferred) provider:litellm
    │ └ calls (extracted) …
    └ dispatches (extracted) vespa/tasks.py#check_for_vespa_sync_task  → TASK check_for_vespa_sync
  hops 17 of 41 reachable (fanout 8 · depth 4 named) · inferred 12 / extracted 5 — a FLOOR: grep before claiming absence
  ```
- **Map keys:** `levels.json.fn_edges` (P0), `archmap.task_roots` (P1), `entities[].endpoints[].middleware` + `archmap.app_middleware` (the header), `function_insight[].access.{ops,externals,sinks}` (the per-hop models/providers), `c4.l2 behind.{fns,depth}` (printed once as the mass, for contrast).
- **Honest-empty:** no `levels.json` → `{present: True, reason: "no levels.json in this center — regen with the current generators"}`; a start with zero out-edges → "no fn_edges leave <start> — cross-file calls are graft-inferred; the behind block says N fns exist; grep is the floor"; start not found → routes through P1's detect_kind reason.
- **Read-only proof:** opens exactly `levels.json` + the already-loaded archmap/c4; no subprocess, no git, no emit path (does not touch `map-deltas.py`).
- **Cost:** tier3 index build 2,982 rows ≈ 50 ms once per Center; a depth-4 fanout-8 walk ≤ 4,681 visits worst case, ~5 ms; every cap named (D11).
- **Battery:** P0 fixture `levels.json` literal `{"fn_edges": [{"s": "apps/api/api/things.py#get_thing", "t": "apps/api/services/thing.py#thing", "rel": "calls", "conf": "extracted"}, {"s": "apps/api/services/thing.py#thing", "t": "provider:redis", "rel": "reaches", "conf": "inferred"}, {"s": "apps/api/api/things.py#get_thing", "t": "apps/api/tasks.py#sweep_things_task", "rel": "dispatches", "conf": "extracted"}]}` written by the `:160` loop → **FIRE:** `trace("GET /things/{item_id}").text` contains `provider:redis`, `dispatches (extracted)`, and the gate `auth`; `trace("TASK sweep_things")` starts at the task node; `depth=1` → the reaches hop absent and `hops 2 of 3` named. **SILENT:** delete `levels.json` → the named reason, no stack; `rels=["dispatches"]` on a function with only calls → "no dispatches edges leave …". Mutation: reverse `s`/`t` in the fixture → the FIRE assertion fails (proves the direction is read).
- **Probe:** tier3 `POST /chat/send-chat-message` (behind 269 → an ordered path), tier2 `POST /chatbot/chat/stream` (18 fns: `LangGraphAgent.get_stream_response → MemoryService.search → provider mem0`), tier3 `TASK check_for_indexing`, tier0 `POST /login/access-token` (where `who_calls direction=out` returned nothing — the control that the loader, not graft, answers).

### N2 · `gates` — the inverse of `middleware` (candidate #7)
- **Instructions line:** "which endpoints a gate guards — by callee, by fn key, or by its argument string (Permission.MANAGE_LLMS) — plus the ASGI middleware that applies to every request → mcp__gabe-map__gates"
- **Inputs:** `gate` (a callee name · `file::fn` key · argument substring; omit → the census of all gates), `root`.
- **Output:**
  ```
  gate require_permission (backend/onyx/auth/permissions.py::require_permission) · 476 endpoints · map@f1a685fa80
  by argument: Permission.BASIC_ACCESS 196 · FULL_ADMIN_PANEL_ACCESS 116 · MANAGE_LLMS 25 · MANAGE_ACTIONS 22 · MANAGE_CONNECTORS 22 · … (30 args, 12 shown)
  MANAGE_LLMS: GET /admin/llm/provider (manage) · PUT /admin/llm/provider (manage) · … (cap 40 named)
  ungated endpoints: 36 (GET /health, …)
  app-scope (every request, in order): CORSMiddleware · CaptchaCookieMiddleware · LoginCaptchaMiddleware · ClientIPMiddleware (backend/onyx/main.py:753-770)
  ```
- **Map keys:** `entities[].endpoints[].middleware[{name,fn,callee,gate,via}]`, `archmap.task_roots[].middleware` (tasks have none — printed as such), `archmap.app_middleware`, `c4.stats.gate_endpoints` (a cross-check line: "stats say 476, I count 476").
- **Honest-empty:** no middleware anywhere → "the map recorded no Depends on any endpoint"; unknown gate → "no endpoint names <gate> in a param-dep or decorator — a router-level `dependencies=[...]` or an ASGI middleware is not in this list; app-scope below" (the app list still prints); `app_middleware` absent → "none recorded (block absent — older map or none declared)".
- **Read-only proof:** pure archmap walk; zero new extraction (every byte already in the map); no subprocess.
- **Cost:** 512 endpoints × ≤5 middleware → <5 ms on tier3.
- **Battery:** fixture endpoint middleware `{name: "auth(Scope.READ)", callee: "auth", fn: "apps/api/deps.py::auth", gate: True, via: "param-dep"}` + a second endpoint with `{name: "get_db", gate: False}` → **FIRE:** `gates("auth").endpoints` = the one endpoint, `by_argument == {"Scope.READ": 1}`, `gates("Scope.READ")` finds it by argument, `app_middleware[0].cls == "RateLimiterMiddleware"`. **SILENT:** `gates("nope")` → `endpoints == []` with the named reason AND the app list still present; `gates("get_db")` → the endpoint listed under `non_gate_deps` (a dep that is not a gate must not be reported as one). Mutation: flip `gate: True` → False in the fixture → FIRE fails.
- **Probe:** tier3 `require_permission` (476), tier0 `get_current_user` (12), tier1 `get_current_superuser` (13) + `RateLimiterMiddleware` at `app_factory.py:263`.

### Cut at the gate (were candidates; folded or dropped)
| Candidate | Verdict | Where it lives now |
|---|---|---|
| #2 `map_blind` | **cut → merged** | F6 `map_census` sections + F5 `map_status.map_health` (one helper, two homes) |
| #3 task/worker census | **cut → folded** | P1 + F3 (addressable everywhere) + N1 `dispatched_by`/dispatch hops |
| #4 provider census | **cut → fields** | F4 `find kind=provider`, F7/F8 named providers, N1 terminates on `provider:*` |
| #5 frontend context | **cut → fields** | F9 on `touches` file branch (the index was already built) |
| #6 bootstrap preview | **cut / defer** | D4 below — a `--dry-run` on `bootstrap_center.sh`, not a tool |
| `stream` filter tool | **cut → argument** | F4 `find(stream=true)` + F1/F8 badges |
| `review_drift` `tasks` subject | **cut → backlog** | not on any study mission's path; the diff-added-`@shared_task` detector needs source parsing the server does not do |

---

## B.3 Attack — every item, the strongest objection, the verdict

| Item | Strongest objection | Verdict |
|---|---|---|
| **P0 levels loader** | A fifth reader widens the server's read set the spec pins ("archmap · c4 · config · adoption"); 3.2 MB on tier3 could creep into every call. | **keep** — lazy, touched only by `trace`/`blast_radius`/`touches(task)`; the read set is stated once in SKILL.md and grows by one named file. |
| **P1 TASK verb** | `TASK` is not HTTP; teaching the endpoint regex a non-HTTP verb muddles "endpoint". | **keep** — the MAP already prints `endpoint:TASK <name>` (c4 id) and `method: 'TASK'` (archmap); the tool must address what the map names. The answer's `kind` says `task`, not `endpoint`. |
| **P2 sentinel** | Inferring "clean" from a sibling key is a heuristic; a future emitter that stops writing `route_mounts` silently flips every absent key to `not_emitted`. | **keep, flagged D5** — the alternative (always "not emitted") makes every clean map look partial; the alternative-alternative (an explicit `emitted: [...]` list from the emitter) is the RIGHT fix and belongs in Part A. P2 is the bridge until then. |
| F1 stream/app_middleware | `app_middleware` on every endpoint answer is repetition — 4 lines × 512 calls. | **keep** — it is the tier1 mission's whole mechanism and it is 4 rows; print `cls` only, `file:line` once. |
| F2 join | Stricter matching may DROP today's plain-function matches if a name contains a dot for another reason. | **keep** — `function_insight` keys are `file::Qual.name`; a dot means a class. The SILENT case pins that `Other.search` no longer bridges — which was a silent false positive before. |
| F3 task addressability | Scope in disguise? A session might now treat the 46 tasks as THE background job list. | **keep** — the answer prints `tasks.stats.unresolved` (`['task_name']` on tier3: tasks registered under a computed name are NOT in this list). Floor stated in-answer. |
| F4 find ranking | Kind bonuses are opinion; "endpoint over define" may bury a legitimate TS lookup. | **keep** — `kind=` still filters exactly; only the unfiltered call reorders, and `ranking` prints the formula. The gen-file penalty is path-shaped, not name-shaped. |
| F5/F6 map_health in two tools | Duplicate of the station's job (the codebase-graph/universe show census)? Two homes = drift. | **keep, one helper** — the station is a page an agent cannot read; the memory says "a session cannot ask WHERE the floor is". Two homes because `map_status` is "call first" and `map_census` is "where blind" — same object, one function. |
| F7 config-only | Changing the `unregistered` contract could break a twin's skill that reads it. | **keep** — the key is omitted only when the l1 status says `config-only` (a mode that did not exist before today); with adoption.json nothing changes (SILENT pin). |
| F9 fe fields | This is candidate #5 sneaking back as fields; cost on a 2,602-piece map? | **keep** — filtered on ONE file; cap 12 named. Not a tool, an unblocked projection. |
| F11 corpus excludes | The exclusion list is suite-shaped; a project with a legit `scripts/_a3_x.py` test is skipped. | **keep** — those names are the suite's installs by construction; the `.kdbp`-absent note is the real fix. |
| F12 web_bridge filter | Fixing it server-side instead of in `fetch_bridge.py` leaves pulse S10 and `/gabe-review` with the same phantom. | **keep here, owe pulse** — Part B is the tool layer; the pulse fix is a one-line follow-up named in B.5. |
| F14 map_diff | Unprobable on the study repos (one center commit). | **keep small** — twins prove it; three lines. |
| F15 dispatch arm | Blast through a dispatch edge is speculative — a task may run hours later. | **keep** — `reading: cross-process` is the honest word; `conf` rides every edge. |
| **N1 `trace`** | (a) Tool-floor law "tools are not rails" — a walk output reads like a scope; (b) the station's `?journey=` already draws paths; (c) `who_calls direction=out` exists; (d) the name `walk` collides with the ARCHIVED `gabe-walk` skill and `journey` with the five journey kinds. | **keep, renamed `trace`** — (a) every hop prints `conf`, the footer prints the FLOOR sentence, `Reach:` records stay grep-backed; (b) the station's journeys are curated screen→endpoint workflows — the fn-level order exists only in `levels.json`, which no agent-readable surface exposes; (c) `direction=out` returned `callees: []` on tier0 — graft-out is a different, weaker source; (d) `trace` collides with the "5C trace arc" *vocabulary* but no skill or tool — D1 offers the alternatives. |
| **N2 `gates`** | Could be a `touches` fold: `touches("require_permission")` gaining `gated_endpoints`. Fewer tools. | **keep as a tool** — the argument-string query (`Permission.MANAGE_LLMS`) is not a function, file, model or endpoint; `detect_kind` would have to grow a sixth fallback that guesses. A 60-line tool with one clear question beats an overloaded branch. `touches` on a gate fn DOES gain a one-line cross-link (`gated_endpoints: 476 → gates`). D2 records the choice. |
| Candidate #6 bootstrap | The tool floor says preview-writes-nothing is fine; the memory says build it. | **cut/defer** — it must SCAN SOURCE (no map exists yet), which is the generators' job, not the map server's read set; all four study repos are already bootstrapped; F7 removes the pain it was proposed to cure. D4. |
| Candidate `tasks` review subject | It is the "sibling" of entity_shape. | **cut** — no study mission runs a review; the detector needs `@shared_task` parsing in the diff, i.e. source reading the server does not do. Backlog line. |
| Count 15 → 17 | Every "15/fifteen" string (SKILL.md, README:63, CLAUDE.md cell, checks.py:238, gabe-help catalog) must move in ONE commit or the doctor's parity check fails. | **accepted cost** — listed in B.5; the doctor is the proof. |

---

## B.4 Decisions for the operator

**D1 — the path tool: `trace` (new) vs pointing the session at the station's `?journey=`.**
- *Station pointer:* cost 0; breaks the study — an agent cannot read a rendered page, and the station's journeys are the curated screen→endpoint kind, not the fn-level order; missions T0-1/T2-1/T3-A/T3-B stay at "here is the mass (269 fns)".
- *`trace`:* cost ≈ 140 lines + P0 (≈40) + 6 battery cases; breaks nothing (additive, lazy loader). Name options: `trace` (recommended; collides only with prose vocabulary) · `walk` (collides with archived `gabe-walk`) · `journey_walk` (collides with the five journey kinds and the curate-workflows drafter).
- **Recommendation: build `trace`.** It is the one item that turns "mass" into "order", which is the ramp-up's thesis.

**D2 — the inverse gate: `gates` (new tool) vs a `gated_endpoints` fold into `touches`.**
- *Fold:* cost ≈ 30 lines; breaks the argument-string question (`Permission.X` is not a `touches` target) and leaves `app_middleware` homeless.
- *Tool:* cost ≈ 60 lines + 4 battery cases + one more name in every count.
- **Recommendation: the tool**, with the one-line cross-link on `touches`. Two whole missions (T0-1 last hop, T3-C) for 60 lines.

**D3 — map-health home: F5+F6 (fold into `map_status` + `map_census`) vs a new `map_blind`.**
- *New tool:* one sharper name, but a third place to say the same facts, and "where is the map blind" is ALREADY `map_census`'s instructions line — a duplicate by definition.
- *Fold:* zero new names; the helper is written once.
- **Recommendation: fold.** Cut `map_blind`.

**D4 — foreign-repo bootstrap: a preview tool vs `bootstrap_center.sh --dry-run`.**
- *Tool:* must scan source (URL domains, dirs, tasks) before any map exists — outside the server's read set, and a second implementation of the shell script's ranking (`bootstrap_center.sh`, 78 lines, currently `usage: bootstrap_center.sh <repo-root> [--name <slug>] [--display "<name>"]` — no dry-run flag).
- *Flag:* ≈ 15 lines on the script, prints the `center.config.json` skeleton, writes nothing; `/gabe-cc-init` stays the writer.
- **Recommendation: the flag, and not in this pass** — every study repo is already bootstrapped; F7's `registry: config-only` removes the "9 unregistered" symptom today.

**D5 — absence semantics for omitted-when-empty keys (`unparseable` · `fn_similarity` · `route_mounts`).**
- *"absent = clean":* matches the emitter's intent (`build_center_a3.py:1989-1996`) but on an older map reads a blind spot as clean.
- *"absent = not emitted":* never lies, but every clean map prints four "regen to know" lines forever.
- *P2 sentinel (`route_mounts` present ⇒ the pass ran):* honest on all four tiers + the twins after one regen; brittle if the emitter ever drops the sentinel.
- **Recommendation: P2 now; ask Part A for an explicit `archmap.emitted: [keys]` list in the next generator commit, at which point P2 collapses to one line.**

---

## B.5 Build order + proofs

**Order (each step lands green before the next; heavy checks serially, per the machine rule):**
1. **P0 · P1 · P2** in `mapquery.py` / `tools.py` — loaders and detect_kind only; battery fixture gains `levels.json`, `task_roots`, `tasks`, `route_mounts`, `fn_similarity`, `unparseable`, `app_middleware`, the stream endpoint, the gen define + fe twin, the provider node, the fe bridge edge (all in `checks.py:84-160`). Run `tests/gabe-map/run.sh` (≈ 3 s) — every EXISTING assertion still green with the richer fixture (the SILENT half of the whole pass).
2. **F1 · F2 · F3** (the three-line class: `stream`, the join, TASK) — FIRE cases; mutate the fixture (`s`/`t` reversed; `gate` flipped; `Svc.search` → `Other.search`) to prove each can fail.
3. **F4** find; **F5 · F6 · F7 · F8** the health/overview/context projections (one shared helper `mq.map_health(archmap, c4)`).
4. **F9 · F10 · F11 · F12 · F13 · F14**.
5. **N1 `trace`** (needs 1) → **N2 `gates`** → **F15** (needs 1 + N1's edge index).
6. **F17** INSTRUCTIONS + the instructions pin; `tools_wave2.py` registers the two tools; `checks.py:238` `len(names) == 15` → `== 17` with a `W3 = {"trace", "gates"}` set.
7. Docs: `skills/gabe-map/SKILL.md` — `description` "as 15 tools" → "as 17 tools (… + trace · gates)", line 20 "fifteen" → "seventeen", the tools table gains two rows and the read set names `levels.json`, `metadata.version: 1.1.4 → 1.2.0` (two new tools = minor; fixes alone would be 1.1.5). `CLAUDE.md` gabe-map cell: "FIFTEEN tools" → "SEVENTEEN", version 1.2.0, the read set line gains `levels.json`, and the sentence "graft serves map CREATION only" stays. `README.md:63` "15 MCP tools (…)" → 17 with the two names. `gabe-help` catalog regenerates at install (`scripts/gen-help-catalog.py`). `docs/design/repo-study/README.md` carries this Part B. **`skills/gabe-docs/references/execution-contract.md` §"The tool floor" — UNCHANGED**: read-only except `who_calls`' emit still holds (`trace`/`gates` write nothing, open no subprocess); the map-is-a-FLOOR law is what `trace`'s footer prints. `suite-backlog.md` gains two lines: the `tasks` review subject; the pulse-side `fetch_bridge.diff_new_fetches` literal guard.
8. `./install.sh` (≈ 5 s) — the servers install machine-wide to `~/.claude/skills/gabe-map/scripts/`; registration in `~/.claude.json` points at that path, so **no re-run of `./install.sh --register-mcp`** is needed; a running Claude Code session keeps the OLD tool list until restarted (SKILL.md:50 already says so — the release note repeats it). `tests/mcp-registration/run.sh` is untouched (it checks registration state, not the tool count) — run it anyway as the SILENT proof.
9. `scripts/suite-doctor.sh` (≈ 2–4 min, alone) — CLEAN is the parity proof (version/count strings, hook harness, docsite staleness).

**Proof rules honoured:**
- Every FIRE has a SILENT sibling (meta-review P2/P4), and every new assertion has a named fixture mutation that makes it fail.
- The "dry-run against a COPY" rule: the server is read-only, so the study repos ARE the copies — the commit message records the numbers: tier3 `trace POST /chat/send-chat-message` hop count vs `behind.fns 269`; `gates require_permission` = 476 = `stats.gate_endpoints`; tier0 `find("login").hits[0]` = the endpoint; tier1 `touches PATCH /rate-limits/{name}` shows `RateLimiterMiddleware`; tier3 `map_census` names 3 mounts / twins blocked / 2 other_roots / schemas empty-arm; tier0/tier3 `cases_for` corpus → None with the note; timings (`map_status` must stay ≤ 200 ms on tier3 — P0 must not load).
- Size budget: `tools.py` 695 + ≈ 90 and `tools_wave2.py` 552 + ≈ 230 stay under the 800 CODE budget; if `trace` pushes `tools_wave2.py` past it, `trace`+`gates` go to a `tools_wave3.py` sibling (the pattern already used) — state the numbers in the commit either way.
- No `.kdbp/` in this repo (R8): the advisory arm only — battery + doctor + this section as the roast record.
---

# Part C — location is an indicator, never the definition

**Status: BUILT 2026-09-06** — C1 `_a3_homing.py` · C2 build order (levels → evidence → c4 emit) · C3 the station rows · C4 pulse S17 · C5 gabe-map fields + census section · C6 batteries · C7 estates · C8 docs. Evidence only — nothing re-homed; the opt-in switch waits on its trigger.

## C.0 The ruling and today's definition

**Ruling (operator, 2026-09-06):** a code piece is identified by its CONTENT, its FUNCTIONALITY and its USAGE. Where the code sits in the tree is an INDICATOR — a prior and a tie-breaker — never the DEFINITION of what it belongs to.

**Today's entity definition** (`center.config.json` `entities.<slug>`): a name + FILE CLAIMS (`code.api/models/schemas/services/web` — literal paths or globs) + a `models` allowlist + `test_rx`; the registry is `adoption.json` (or config-only after `bootstrap_center.sh`). Membership is the file claim: a piece belongs to the entity whose claim matches its file (`_a3_code` per layer; `_a3_fe` by the feature layout, or by the config's `code.web` claims when the tree has no feature layout — D6). So a function whose callers and data all live in another entity is homed by its folder, and the graph draws it there.

**Measured 2026-09-06 (file witness vs the data witness, per backend function with model access):** gustify 29% disagree · onyx 17%; endpoints vs their data rollup in the same band; frontend pieces vs the entities that render/use them: gustify 40% · onyx 85% (onyx is config-homed — the file witness is weakest exactly where the layout is not feature-shaped). The map already holds every witness; it never says when they disagree.

## C.1 The three witnesses and the three-outcome rule (per piece)

| Witness | Backend function (`file#fn`) | Endpoint (`endpoint:METHOD /path` · `TASK <name>`) | Frontend piece (`fe:file#name`) |
|---|---|---|---|
| **file** (today's home) | the entity whose file claim owns the file | the entity the router file is claimed by | `home` (fe·<slug>; `homed_by` layout \| config) |
| **users** (who consumes it) | callers' entities — `levels.fn_edges` with rel `calls` · `depends` · `dispatches`, the edge's `ss` | the screens that fetch it — bridge `cross_edges` `from_slug` (+ dispatchers' entities for a TASK) | the pieces that `renders` · `uses-hook` · `uses-store` · `imports` · `fecall` it — the source piece's `home` |
| **data** (what it touches) | `function_insight.access.ops` models → the entity that declares the model | the c4 node's `access.ops` rollup → model entities | the endpoints it fetches (bridge `to_slug`) |

Verdict, computed from the witnesses that EXIST (an absent witness abstains; `__unclaimed__` counts as a consumer but never as a destination):

- **agree** — every present witness holds a strict MAJORITY (> half) for the file entity — never a plurality, never a tie (review 2026-09-06: a plurality with an insertion-order tie-break read `AppHeader` at 20% of its users as "every witness agrees").
- **move candidate** — ONE other entity holds ≥ 60% of ≥ 2 users AND the data witness agrees with it (a majority) or abstains. Named with the share. The bars are NOT disjoint: a ≥60% concentration wins over breadth, so the record carries `others` (the consuming entities besides home) and the card says "also used by N other entities" — the reader sees the breadth before acting.
- **shared / aspect** — ≥ 3 distinct consuming entities and no entity holds ≥ 60%. The piece is cross-cutting; a candidate for an aspect entity, not a move.
- **stay** — disagreement that meets neither bar (a minority user elsewhere, a single caller, or data contradicting the users). File wins as the tie-breaker.

A destination that is not a declared entity (a frontend-only area such as `app-shell`) is said so (`to_kind: fe-area`); a frontend piece homed in such an area has no comparable data witness (the data witness names BACKEND entities), so data abstains with `data_note`. Thresholds are constants in one place (`_a3_homing.MOVE_SHARE = 0.60`, `MOVE_MIN_USERS = 2`, `SHARED_MIN = 3`) and printed in the stats so a reader knows the bar.

## C.2 What gets built (evidence first — NOTHING re-homes)

| Id | Where | Change |
|---|---|---|
| **C1** emitter | NEW `templates/center/generators/_a3_homing.py` `evidence(amap, graph, levels) -> {pieces, stats, rule}` | pure derivation over the in-memory archmap + c4 + levels (no source read, no new arm). `pieces[key] = {kind, home, by, users{slug:n}, data{slug:n}, verdict, to, to_kind, share, others, data_note?}` only for pieces whose witnesses DISAGREE — the agree count rides `stats` (no consumer reads an agree record; 46% of the block on onyx before the cut); `stats = {pieces, agree, stay, move, shared, by_kind{…}, thresholds, move_named, shared_named}`. |
| **C2** build order | `build_center_a3.py` L2134–2150 | levels build first, then `_hom = _a3_homing.evidence(…)`; `_levels["homing"] = _hom` (the per-piece detail rides levels.json — the station already loads it, gabe-map reads it lazily); `_graph["stats"]["homing"] = _hom["stats"]` + `home_ev: {verdict, to, share}` on every endpoint node / fe piece whose verdict ≠ agree; c4 emitted AFTER (the emit is a dump — no order dependency). c4 ALWAYS carries `stats.homing`: `present:false` + the reason when levels are absent (graft arm) or the derivation raised — the reason rides the stats so pulse and the station name the real cause. |
| **C3** station (both copies) | `gabe-universe.html` Sources + cards | Sources row `homing evidence` — `N pieces weighed · A agree · S stay · M move candidate(s) · K shared` (+ the thresholds in the tooltip; `present:false` → the reason). Card row `homeEvRow(n)` on endpoint and fe cards when `home_ev` exists: `home <slug> by file · users say <to> (72%) · data says <to> → MOVE CANDIDATE — evidence only, nothing re-homed`. No new glyph or wire (a row, not a visual element → no legend entry; the reference gains a one-line definition under Sources). |
| **C4** pulse | `skills/gabe-pulse/scripts/angles.py` S17 | reads the committed `c4-graph.json` `stats.homing`: fires at ≥ 3 move candidates → `S17 homing evidence — M move candidate(s) (≥60% of ≥2 users in one other entity, data agrees) · K shared aspect(s) … → /gabe-cc-init section (re-home is opt-in — nothing moved)`. The shared count is REPORTED, never a trigger (5 of 6 estates carry ≥ 1 — a structural constant, not a debt; review 2026-09-06). Nothing stored. |
| **C5** gabe-map | `map_census` section `homing` (counts + the first 12 move candidates / shared aspects, from levels.json lazily) · `touches` function/endpoint/task/fe-piece answers carry `home_evidence` when the piece has one (the unclaimed bucket spelled `unclaimed`) | projections over C1's block; every line names the rule. DEFERRED: an `entity_context` per-entity disagree count — trigger: a study session asks "how much of THIS entity is disputed". |
| **C6** batteries | `tests/arch-graph` (the emitter: FIRE move · shared · stay · SILENT agree, absent levels; mutation: flip one caller's `ss`) · `tests/gabe-universe` (row pins + a render probe: the example's Sources row and one card row) · `tests/pulse-angles` (S17 FIRE/SILENT) · `tests/gabe-map` (3 cases) | every FIRE with a SILENT sibling. |
| **C7** estates | example regen → tiers 0–3 (serial) → twins | the numbers land in the design record: per estate `agree / stay / move / shared`. |
| **C8** docs | `CLAUDE.md` (the entity-definition sentence + the ruling: file claim = membership TODAY, evidence rows say where usage disagrees, re-home is opt-in) · design record · this plan | — |

**Opt-in re-home (NOT this pass):** `center.config.json` `homing: usage-first` would let the emitter home a `move` piece by its users. Trigger: an operator accepts ≥ 5 move candidates on a twin by hand (moves the file claims) — then the switch saves the hand-moves; before that it is a heuristic with no ground truth.

**Recorded as S items (not built):** gate-by-behaviour (a middleware that only reads is not a gate — behaviour, not name) · content-based module classes (`mclass` from what a module's body does, not its path). Both are the same ruling applied to two more classifiers; each needs its own measurement first.

## C.3 Invariants

- **Nothing re-homes.** Byte-identical entities/files/models on every estate; only `levels.json.homing`, `c4.stats.homing` and the `home_ev` fields appear.
- **Honest-empty.** No levels → `present:false` + reason; a piece with no witness beyond file is not weighed (never counted as agree).
- **R10.** Copy uses move candidate · shared · stay · agree; `__unclaimed__` is named "unclaimed", never "orphan".
- **Two-file law** for the station; **mutation proof** for every new pin.
