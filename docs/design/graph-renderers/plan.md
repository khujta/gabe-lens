# Plan — graph renderer labs for the Gabe Universe (2026-09-07)

**Status:** IN EXECUTION 2026-09-07 — rulings D1 3D primary · D4 render + walk · D5 Standard · D6 fold (all = the recommendations; D2/D3/D7 as recommended). Beats 0–3 landed (`8d44ab5` fold · `de6a4ba` rails · lab-00 · bake · lab-01 · lab-02 · lab-03 · lab-04 · lab-05 in the lab commit); the measured table lives in [lab/README.md](lab/README.md). Original status: DRAFT — nothing built. Operator ask (2026-09-06): *"explore options of other libraries to display this graph — separate
html files to try different libraries, see on the internet what could apply in our case, also check if three.js is viable; I know
it is for games, but we might move in that direction at some point."* Research workflow (four web sweeps · one local inventory ·
one Fable judge, `wf_ac03853c-5a3`) → this synthesis. Build starts on "land it".

**The one law this plan hangs on:** one feed, one adapter, one probe. Every lab page draws the SAME committed example estate
(`templates/center/shell/example/codebase-graph-station/c4-graph.js`) through the SAME `adapter.js`, and one `probe.mjs` measures
every page the same way, so the only variable between two rows of the table is the library. Five sweeps already on disk broke
this law (four adapters, four node counts: 1,384 / 1,393 / 1,399 / 1,404) — their numbers are evidence, never the table.

---

## The verdict the research already reached (measured, swiftshader, no GPU)

1. **Keep three.js. Drop the wrapper's render path for the 3D lane.** `window.THREE` r185 is already the bundle the station ships
   (`assets/3d-bundle.js`, 1,637,037 B) with InstancedMesh · BatchedMesh · LOD · ConvexGeometry · MarchingCubes inside it. Raw three on
   the identical feed: **3 draw calls vs the wrapper's 5,366** at 1,393 nodes (21,941 at ×4; the station reaches ~39,470/frame at T3).
   The wrapper's `useWebGPU` is a source-verified silent no-op (3d-force-graph 1.80 forwards only `controlType`/`rendererConfig`/
   `extraRenderers`), so the current stack can never reach the GPU path. Cost: the suite owns the layout loop (d3-force-3d in a
   Blob-URL worker), the camera rig, a label atlas, colour-id picking for nodes AND links, and the composed-node grammar as instanced
   layers — the B2 sweep page proves the core in ~340 lines. A zero-byte middle path exists and is measured FIRST: keep 3d-force-graph
   as sim + camera, return an empty `Object3D` from `nodeThreeObject`, draw everything instanced through `.scene()` (the "hollow wrapper").
2. **Games direction: OPEN from three, CLOSED from everything else that survives `file://`.** Godot / Unity / Bevy fetch `.wasm`/`.pck`
   — measured to fail from origin `null`. Babylon.js 9 is the only game host that opens offline, at 8,316,622 B UMD (5× our whole
   bundle), Apache-2.0, a total rewrite of ~6.3k three-shaped lines, with an unisolated 1→1,343 draw-call jump at 4,170 solids.
   three's own FPS kit (PointerLockControls + Octree + Capsule) is 27,608 B of source in the esbuild we already run — the sweep's
   `game-lab-three-raw.html` walked 1,390 solids at 34 fps / 6 draw calls. Rapier physics is additive and offline-safe only via
   `@dimforge/rapier3d-compat` (wasm inlined as base64; +816 KB gz). WebXR is ~50 lines through `renderer.xr`. So the game direction
   argues FOR staying on three; lab-01 is its door-keeper, not a separate spike.
3. **The strongest single finding is not a renderer.** graphviz `fdp` WITH cluster subgraphs bakes a deterministic layout in 1.6 s at
   **0.996 entity purity** (k=10 neighbour purity: of a node's ten nearest drawn neighbours, the share inside its entity). Every live
   force sim scored WORSE than doing nothing (group-seeded ring 0.888 · sfdp 0.481 · networkx 0.472 · neato 0.405 · fdp without
   clusters 0.282). `sfdp` silently IGNORES clusters (0.475 with them) and looks like it worked — the trap is named so nobody
   "optimises" fdp into sfdp. A baked layout is also the prerequisite for any walkable universe: a city that rearranges itself on
   every regen cannot be learned. It becomes an ADAPTER MODE (`?layout=baked`) every page can take.
4. **2D lane, if it lives:** cytoscape.js 3.34 is the SEMANTIC winner (native compound nodes = entity containment the layout and the
   stylesheet both respect; MIT; healthiest maintenance) but only with a PRESET layout — fcose is 7.6–9.3 s at 1,384 nodes and
   141,679 ms at 4,152. sigma.js 3.0.3 is the PERFORMANCE-AND-LABELS winner (60 fps under swiftshader; the only free label
   de-collider) but hulls and the glyph roster are ours. cosmos.gl is worth a page ONLY as a GPU layout feeding our renderer, never
   as a renderer — and ONLY `@cosmos.gl/graph` (MIT); `@cosmograph/cosmos` is CC-BY-NC-4.0 since 3.4.0 at the same version string.
5. **Layout, not rendering, is the cost at this size.** Nothing in 49 candidates struggled to PAINT 1,384 nodes; what separates them is
   when the layout is paid for and whether the nine entities are a first-class object.

## The scorecard (49 candidates judged; ★ = gets a lab page)

| Score | Candidate | Family | Why it stands / why it falls |
|---:|---|---|---|
| 8.5 ★ | **three.js r185, raw** | 3D | Already shipped; 3 draw calls; WebGPU reachable; bundle −46% without the wrapper. Cost: we own loop · rig · labels · picking · grammar. |
| 8 ★ | **graphviz `fdp` + cluster subgraphs** | layout (bake) | 0.996 purity · 1.6 s · byte-stable; EPL-1.0 tool at regen time only, nothing linked. 2D; z from the entity band. |
| 8 ★ | **LOD / aggregation tiers** | strategy | The onyx answer the station half-believes (`__uniBudget` 1,600, T0–T3); aggregated wires must carry the bundled count honestly. |
| 7 ★ | **cytoscape.js 3.34** | 2D | Native compound entities · shape-by-selector · query algebra. fcose is the wrong complexity class → preset from the bake. |
| 6 ★ | **3d-force-graph 1.80** (today) | 3D | The CONTROL: gives the 3D tick with `d3Force` hooks, camera, raycast free; structurally unbatchable (one Mesh per node/link). |
| 6 ★ | **Babylon.js 9.25** | game | Thin instances with per-instance colour (2 draw calls), GPUPicker, checkCollisions; 8.3 MB UMD; total rewrite; the 1→1,343 jump. |
| 6 ★ | **sigma.js 3.0.3 + graphology** | 2D | Instanced WebGL, 59–60 fps, built-in label collision; no grouping (hulls = our cached overlay). v4 beta rewrites labels → v3 label work is throwaway. |
| 5.5 ★ | **cosmos.gl 3.4.1** (`@cosmos.gl/graph`) | GPU layout | Real cluster force (`setPointClusters`), never blocks the main thread; as a renderer: points only, no labels, no hulls. |
| 5.5 ★ | **PixiJS 8.20 + d3-force** | 2D | The only 2D option that carries composed nodes with batching; no graph semantics at all (ours). CONDITIONAL page. |
| 8 | three.js + PointerLockControls/Octree/Capsule | game | The walk mode: 27,608 B added to the bundle; no lab of its own — rides lab-01. |
| 6.5 | three.js + Rapier 3D (`rapier3d-compat`) | game | Real collision; +816 KB gz; lazy on walk-mode entry; Apache-2.0 beside MIT. |
| 6.5 | d3-force / d3-force-3d in a Blob worker | layout | What the station runs today, off the main thread; ~0.4–0.5 purity as a global layout. |
| 6 | d3-force + hand-rolled Canvas2D | 2D floor | 2.6 ms full redraw by bucketing strokes per colour; its batching lesson is inherited by lab-01, no new page. |
| 6 | ngraph.forcelayout 3.3.1 | layout | True nD, 31 KB, BSD-3; 300 steps ≈ 1.1 s; the `?tick=ngraph` alternative inside lab-01. |
| 5.5 | AntV G6 5.1 | 2D | Native combos; 1,351 KB Canvas2D-only UMD (WebGL is a separate package); the named fallback for cytoscape's badge slot. |
| 5 | force-graph 1.51 (2D incumbent) | 2D | Zero new bytes; repaints every tick (15.4 s settle vs 1.6 s batched); stays the 2D station's renderer where it has a battery. |
| ≤4.5 | PlayCanvas · deck.gl · forceatlas2 · vis-network · fcose · ECharts · A-Frame · WebGPU compute (PARKED: `requestAdapter()` null on this WSL2 host) · Phaser · Excalibur · networkx · Konva · VivaGraph · regl · cannon-es · WebCola · Godot · GraphWaGu · react-flow · Unity · Bevy | — | See *Rejected*. |
| 0 | `@cosmograph/cosmos` (CC-BY-NC) · Graphistry (server) · KeyLines/ReGraph · Ogma · yFiles (commercial, domain-keyed) | — | Disqualified before any feature comparison. |

## The lab pages (shortlist, in build order)

| Page | Role | What it must prove |
|---|---|---|
| `lab-00-baseline-3d-force-graph.html` | THE CONTROL | Today's wrapper on the shared adapter with NO station chrome: typed glyph meshes · two badge sprites · bubble · ConvexGeometry hulls · 7 CONN wire styles with dash + particles · `zForce` via `d3Force('layer')` · `setTier` via `nodeVisibility`/`linkVisibility` · click node/link → card · budget fold. Pins the adapter's node count and every baseline number. **`?hollow=1`**: empty `nodeThreeObject` + instanced layers drawn into `Graph.scene()` — the zero-byte middle path measured beside the raw page. |
| `lab-01-three-raw.html` | THE DECISIVE PAGE | `window.THREE` from the station's own bundle, no wrapper: glyph forms as ONE BatchedMesh keyed by `KINDS[kind].form` · badge slots A/B as two InstancedMesh atlas quads · bubbles one InstancedMesh sphere · labels as an instanced billboard atlas (1 draw call) · wires as LineSegments with per-vertex colour + dash attribute · particles one instanced Points layer · hulls ConvexGeometry per entity + sub-cluster · tick = d3-force-3d + 5 peers in a Blob-URL worker with `zForce` ported verbatim (`?tick=ngraph`) · colour-id picking for nodes AND link segments · `?ships=1` stretch row (D2) · `?walk=1` PointerLock walk (the games door). |
| `lab-02-sigma.html` | 2D WebGL | Cached hull overlay via `graphToViewport` · glyph roster via a custom NodeProgram · badge slots as a second node layer · EdgeProgram for dash · `nodeReducer`/`edgeReducer` as the visibility predicate (no relayout) · **built-in label collision** (the one thing to showcase) · sync FA2 at core, `?layout=baked` at full · pick buffer → cards. |
| `lab-03-cytoscape.html` | 2D with NATIVE containment | Entities + sub-clusters as nested compound parents (zero hull code) · shape-by-selector roster · two badge slots as multiple `background-image`s (G6 combos named fallback) · dash on the canvas renderer + `?webgl=1` recording which wire styles are lost · `display:none` visibility · `layout:'preset'` from the bake (fcose only at `?scale=core`, its seconds on the HUD) · one query-algebra demo. |
| `lab-04-cosmos-layout-three.html` | GPU layout option | `@cosmos.gl/graph` sim with `setPointClusters` = entity homes and a stated iteration budget; `getPointPositions()` (0.5–0.6 ms) feeds lab-01's instanced renderer each frame; prints k=10 purity beside the bake's 0.996; records that under swiftshader the GPU sim is pathological (19 fps) and 60 fps only paused. |
| `lab-05-babylon-spike.html` | game-engine host | Thin instances with per-instance colour · GreasedLine dashed typed wires · GPUPicker · ArcRotateCamera · ported convex hulls (records ConvexGeometry/MarchingCubes lost) · setTier via buffer rewrites · `?walk=1` UniversalCamera with `checkCollisions` at entity/cluster level (D4) · MUST reproduce or isolate the 1→1,343 draw-call jump on onyx. |
| `lab-06-pixi.html` | CONDITIONAL 7th | Only if D1 keeps the 2D lane alive after 02/03: one texture per (kind, colour) → batched sprites with badge/ring children · hulls as Graphics · d3-quadtree picking · BitmapText · render-on-demand. Answers "can 2D keep the badge system with batching". |

## The must-survive checklist (24 rows — every page carries this matrix: free · built · lost)

1. Entity hulls, drawn and labelled, plus sub-cluster hulls on their own on/off + opacity control (rows 1–2).
3. Anchored deterministic layout: a custom per-tick force OR precomputed positions, so EX/EY/EZ anchors · SUBANCHOR rings · KRADF radial bias · 1.6×RENT containment survive.
4. Per-node COMPOSED objects: glyph + up to two badge discs + bubble + label, data-driven (colour+size points cannot carry method/feclass/hrole/mclass/pclass/delivery).
5. Six badge families in two slots under the 30° hue-clearance rule: method (GET/POST/PUT/PATCH/DELETE/BOOT/TASK) · role · feclass · mclass · hrole · pclass · delivery:stream · schema fold count.
6. Typed wires, 7 connector kinds (fk · bridge · calls · imports · rollup · access · dispatches): colour + solid/sparse/dotted/longdash + thickness + gradient + per-kind beam toggle.
7. Directional particles (flow direction is READ, not decoration).
8. Two independent heat gradients — BANDPAL green→orange on backend `d2w`, FEBAND blue→magenta on frontend `fed2w` — separately toggled, never merged.
9. Per-node picking → the four-level panel + the `det` dossier card. 10. Per-LINK picking with hover tolerance → the wire card; a selected wire draws even at beam 0.
11. `nodeVisibility`/`linkVisibility` re-evaluated on demand WITHOUT relayout — a tier press keeps positions static (operator ruling).
12. Tiers T0–T3 as re-appliable presets over kind + feClass, Alt+1–4, preserving a running journey walk.
13. Depth highlight (GLOW / FOCUS, four outside-treatments, default 1, Esc clears). 14. Journey walks with numbered step badges, FE→BE legs, view-first start, fly-to with the entity-anchor fallback.
15. Search that wakes held-off layers or expands a capsule. 16. The node budget fold above 1,600 with a Sources row saying so.
17. The legend overlay painting from the LIVE colour/wire literals with drawn example chips — legends render the actual glyph, words only on hover.
18. Honest-empty throughout: fe absent → backend-only byte-identical; `GABE_SIM` null → plain map; unknown node kind → generic glyph + console warning, NEVER a silent drop.
19. The Sources rows, one per input, with hover explanations. 20. R10: no "orphan"/"dead"/"unused" string anywhere; project identifiers keep their own words.
21. `file://` with zero network: UMD/IIFE only, no ESM, no bare specifiers, no worker that fetches, assets as `data:` URIs.
22. Vendorable as a committed pinned blob under `templates/center/shell/assets/` (it lands in every adopting repo; today's weight is 4.2 MB).
23. Provable under headless system Chrome + playwright-core + `--use-angle=swiftshader` with NO GPU (a WebGPU-first renderer can only be asserted).
24. A probe surface: readiness flag · nodes/links arrays · id→node map · link-end normaliser (source may be object or string) · the per-node scene object.

## The lab design

```
docs/design/graph-renderers/
  plan.md                      this file
  README.md                    the decision record (written at the end: the one-picture model, the measured table, the matrix, D1–D7 with dates)
  sweeps/<name>/               RECORDS folded from the five untracked sweeps (README + index.html + probe-results*.json ONLY — D6)
  lab/
    README.md                  the scorecard table between <!-- probe:start --> / <!-- probe:end --> (regenerated by the probe);
                               the must-survive matrix per page; the swiftshader caveat in the first paragraph
    adapter.js                 THE adapter (contract below) + selfTest(); adapter.py twin for the baker
    scorecard.js               window.__LAB / __LAB_READY / LAB.panel|mark|set|note|fps|ready — a superset of the sweep's
                               lab-common.js so the folded records stay probeable; PRINTS the numbers into <pre id="score">
                               in a fixed key order so a screenshot carries them
    lab.css · index.html       chooser + the table; links every page with ?feed/?scale/?layout knobs
    lab-00 … lab-06 .html      the pages above
    bake-fdp.py                ported from graph-scale-labs/bake-layouts.py: emits layouts/<feed>.fdp.js =
                               window.GABE_BAKED[feed] = {id:[x,y,z]} (fdp + cluster subgraphs, z = entity band), byte-identical
    layouts/                   committed, small (example.fdp.js · onyx.fdp.js)
    fixtures/fetch-onyx.sh     gitignored copy of the tier3 feed (D3)
    package.json               exact pins (sigma@3.0.3 graphology@0.26.0 graphology-layout-forceatlas2@0.10.1 cytoscape@3.34.2
                               cytoscape-bubblesets @cosmos.gl/graph@3.4.1 pixi.js@8.20.1 @babylonjs/core@9.25 …); the vendor
                               script REFUSES @cosmograph/cosmos and writes vendor/MANIFEST.json (bytes per bundle)
    vendor/ · node_modules/ · fixtures/onyx/ · _shots/     gitignored (~16 MB; the WSL disk guard runs first)
    probe.mjs                  section-13 pattern: solo-sequential; system Chrome + playwright-core at
                               docs/design/graft-adoption/spike/_build/node_modules/playwright-core; --use-angle=swiftshader
                               --enable-unsafe-swiftshader --no-sandbox --disable-gpu-sandbox --disable-dev-shm-usage; 1400×860;
                               page.route('**') FAILS the row on any non-file:// request; waitForFunction __LAB_READY; pixel-ink
                               proof; synthetic-pointer picking; tier-press position-equality; R10 DOM grep; writes
                               probe-results.<feed>.<scale>.json + _shots/ and regenerates the README table
    run.sh                     df -h /mnt/c + du -sh /var/log guard → one page × one fixture at a time; loud SKIP without chrome
```

The folder sits outside `install.sh`'s glob and the doctor's parity checks — cheap to iterate; the 800-line CODE budget still applies
report-never-gate (sizes in the commit). NO CDN anywhere (a lab that reaches the network fails its row). The feed is READ from the
station's example copy, never duplicated (`graph-scale-labs/lab-feed.js` is a 1.15 MB copy — the thing this rule forbids).

## The adapter contract (`window.GABE_FEED = buildFeed(GABE_C4, GABE_LEVELS|null, {fn, fe, scale, layout})`)

- **NODE** `{id, kind (fe-type→type; levels fn→function), ent (mutable home), entClaim (immutable), sub (layer band from KINDS[kind].layer),
  label, m (method off the LABEL via GABE_GRAMMAR.methodOf; unknown → null, NEVER 'GET'), det, behind, stream, pclass, homeEv, table, sites,
  fe, feClass, hrole, mclass, fed2w, write, cache, sse, screen, d2w, god, hub, sx sy sz (seeded), bx by bz (baked, else null), tier (0..3 from
  kind + feClass per the station's _TIER_PRESETS)}`.
- **LINK** `{source, target (ids — every page keeps ids and uses lid()), rel (30 values), kind (CONN key via REL2KIND), band (d2w/fed2w),
  dash, count (bundled, when aggregated)}`.
- **Also** `ents` (with anchors EX/EY/EZ and sub-anchors) · `byId` · `kinds` · `conn` · `rel2kind` · `counts` · `fixture` · `head` · `budget:1600`
  · `seedPositions(spread)` · `tierOf(n)` · `bandOf(l)` · `selfTest()` (node/link counts equal the feed's declared counts; an unknown kind
  is kept + warned; `?fe=0` yields a dump byte-identical to a backend-only build).
- Deterministic: same feed → same object, no `Math.random`, no wall clock. The station's `__uniBudget` fold is the adapter's `tier` field, not a page's opinion.

## The measurements (every row, every page, both fixtures)

nodes drawn / visible at boot and at T3 (vs the feed's count — a page that silently drops nodes goes red) · time to first frame (first rAF after
composited ink > 0.002) · time to settle (the engine's OWN stop signal) · fps over 5 s + mean frame ms (**swiftshader caveat on every table**:
CPU rasterisation under-states the draw-call gap on a real GPU) · draw calls / triangles / geometries / textures (`renderer.info`, Babylon
`engine.drawCalls`, Pixi stats) · picking latency + correctness over 20 deterministic ids (real pointer event + `LABG.pick`) · tier press cost
+ positions EQUAL before/after · memory (`usedJSHeapSize` at four marks, `--enable-precise-memory-info`) · bundle bytes split shared-with-station
/ new · offline proof (any non-`file://` request fails the row) · honesty proofs (0 pageerror · ink > 0.002 · `?fe=0` byte-identical · injected
unknown kind drawn + warned · no R10 word in the DOM) · **entity purity k=10** in the page's final positions · fixtures: example (1,384 nodes)
+ onyx (794 L2 + 2,380 fn · 1,626 cross + 2,982 fn edges — NO fe arm) + `?scale=x4` on the top two pages.

## Build order (each beat ends probed green; [H] = heavy, serial, alone)

| # | Beat | Lands | Cost |
|---|---|---|---|
| 0 | Preflight | `df -h /mnt/c` + `du -sh /var/log`; the D6 ruling executed (fold or delete the five sweeps); the folder + `.gitignore` | ~2 min |
| 1 | Rails | `package.json` + vendor script (refuses the NC package, MANIFEST) [H] · `fetch-onyx.sh` · `lab.css` · `adapter.js` + `selfTest()` + `adapter.py` · `scorecard.js` · `probe.mjs` · `run.sh` · README skeleton | 1 beat |
| 2 | lab-00 baseline (+ `?hollow=1`) | the control's numbers on example + onyx; the adapter's node count pinned in the table [H probe] | 1 beat |
| 3 | bake-fdp.py + layouts/ | `?layout=baked` exists before the 2D pages need it; purity printed; byte-identical on an unchanged feed [H fdp ~2 s ×2] | ½ beat |
| 4 | **lab-01 three-raw** | every must-survive row free/built with a probed assert (link picking and the two badge slots are the rows that go missing); example · onyx · x4; `?ships=1` last; `?walk=1` | 2 beats — THE decision |
| 5–6 | lab-02 sigma → lab-03 cytoscape | one page per beat; each records which wire styles/badges the library could not draw | 1 beat each |
| 7–8 | lab-04 cosmos-layout → lab-05 babylon | cluster force vs bake on the same purity metric; the Babylon 1→1,343 jump reproduced or isolated; walk depth per D4 [H: 8 MB vendor] | 1 beat each |
| 9 | lab-06 pixi | ONLY if D1 keeps the 2D lane alive after 5–6 | 1 beat |
| 10 | Full probe run | `run.sh` over every page × {example, onyx} + top two × {x4}; README table + matrix regenerated; `probe-results*.json` committed with the numbers in the message | ~20 min wall |
| 11 | Review | `/gabe-roast` from the station maintainer's seat (what the raw page dropped that the matrix did not catch) + a bounded review of adapter (determinism · honest-empty · the four traps) and probe (fire+silent pairs); findings folded | 1 beat |
| 12 | Decision record | `README.md`: the chosen lane and its migration shape (hollow-wrapper vs raw vs stay), the bundle recipe for `3d-bundle.js` COMMITTED (the gap the inventory found: no package.json, no esbuild script exists today), the walk-mode prerequisites | ½ beat |

**Kill rule (D5):** if lab-01 lands every must-survive row at ≤ ~6 draw calls per layer on onyx, beats 7–9 become calibration and may be cut
to their `?layout=baked` purity row only. lab-00 hollow and lab-01 decide; everything after is pricing the alternatives honestly.

## Decisions (the operator rules; the recommendation is first)

| # | Question | Recommendation | Why |
|---|---|---|---|
| D1 | 2D vs 3D primacy | **3D primary; ONE 2D lane decided after lab-02/03 measure the label field and compound containment; lab-06 only if that lane is alive** | The station's thesis (drawn containment, the hull bleed, the game direction) is 3D and every game host that survives `file://` is 3D; 2D wins on labels and layout semantics — a reading station, not the instrument. |
| D2 | GLB ship fleets in the labs | **Plain glyphs everywhere + a `?ships=1` stretch row on lab-01 only** | The fleets are the largest share of the 39,470 draws and would make every cross-library number a fleet number; whether 22 GLBs instance at one draw call each is the one question that decides if the "space war" reading survives raw three. |
| D3 | onyx as a second fixture | **Gitignored copy under `fixtures/onyx/` via `fetch-onyx.sh` from the repo-study tier3 clone; `?scale=x4` kept as the synthetic ladder** | Onyx is the real shape (3× gustify's cross density, 2,380 fn nodes, no fe arm); the clone rung stretches hulls artificially; both are needed and neither is the other. |
| D4 | Babylon spike depth | **(b) render-only + `?walk=1` UniversalCamera with `checkCollisions`; stop before Havok; the 1→1,343 draw-call row is mandatory** | (a) never tests walkability, the only reason to spend a page on an 8 MB rewrite candidate; (c) is blocked on the `file://` wasm fetch. |
| D5 | Time box | **Standard: six pages + onyx + README + roast + decision record (~6–8 beats) with the kill rule above** | The evidence already points at raw three; the other pages price the alternatives, and their value drops sharply once the 3D page is proven. |
| D6 | The five untracked sweeps (74 MB, `??` in git) | **Fold: keep each sweep's README + index.html report + probe-results*.json under `sweeps/<name>/`; delete `vendor/`, shots, `_dl/`, duplicated feeds, the page sources** | They are the evidence the shortlist was cut from (the fdp purity table, fcose's 2m22s, the `file://` worker findings) and must stay citable; four adapters beside a fifth would make the new table unarguable-with. Deleting all five loses the records. |
| D7 | Layout primacy in the PRODUCT | **Bake when graphviz is on PATH at regen, live sim as the fallback with an honest Sources row — decided AFTER the labs print purity per engine on the same metric** | Changes the product (no settle animation; a picture that keeps a reader's spatial memory across commits; the walkable prerequisite) but adds a build-time EPL-1.0 tool to every adopting repo. Not a lab decision — a station decision the labs inform. |

Two contradictions the labs must settle on the way: (1) graph-2d-labs' README says Chrome blocks `blob:` workers on `file://`; graph-scale-labs
BUILT Blob-URL workers over inlined source and probed them green — the probe re-tests it once and the README states the answer. (2) the sweeps
disagree on the node count (1,384 / 1,393 / 1,399 / 1,404) because each adapter folded the fe arm and the bridge stubs differently — the ONE
adapter's `selfTest()` states the rule and the count once.

## Rejected (with the reason)

- **`@cosmograph/cosmos`** — CC-BY-NC-4.0 from 3.4.0 (verified on the npm registry), identical version/API to the MIT `@cosmos.gl/graph`; a
  non-commercial licence in a suite that installs into other people's repos, and no test would catch it. The vendor script refuses the name.
- **Graphistry · KeyLines/ReGraph · Ogma · yFiles** — server-side or commercial, licence-gated, no public artefact; yFiles' domain-bound key is
  structurally hostile to `file://`. Named so nobody re-researches them.
- **react-flow / xyflow** — a node EDITOR: DOM per node under React, ESM-first, no `file://` story. **Konva** — Canvas2D retained scene graph
  with a hit region per node and a second render pass. **VivaGraphJS** — renderer frozen since 2019-10, no text primitive. **ECharts** — zero
  grouping, single-symbol nodes, 4.0 s blocking layout. **vis-network** — Canvas2D only, whole-scene redraw per tick, two settings hang the
  tab. **AntV G6 v5** — 1,351 KB Canvas2D-only UMD; kept only as the named fallback for cytoscape's badge slot.
- **deck.gl** — a MAP renderer: no scene graph, no 3D hull, 2D-only graph layer. **regl** — dormant; kept as the recorded measurement floor.
  **A-Frame** — pins a `super-three` fork, no instancing component. **PlayCanvas** — per-instance colour and instance-granular picking are
  both custom work. **Godot 4 · Unity 6 · Bevy** — `.wasm`/`.pck` arrive by fetch, measured to FAIL from origin `null`. **cannon-es** — no
  release since 2022-08. **Phaser · Excalibur** — 2D game floors that give up the premise (you do not stand inside a 2D map).
- **cytoscape-fcose as the layout** — 8.1–9.3 s at 1,384, 141,679 ms at 4,152, main thread; its compound-gravity vocabulary is kept as the
  SPECIFICATION of what we want. **WebCola** — no release since 2019-05. **networkx as the baker** — 16.5 s for purity 0.472; **python-igraph**
  — GPL-2.0, must not enter even at build time. **graphviz `sfdp`** — silently ignores clusters.
- **WebGPU compute layout (hand-written WGSL) + GraphWaGu/GraphGPU/d3-force-webgpu** — PARKED, not rejected: Chrome 144 on this WSL2 host
  returns null from `requestAdapter()` in every configuration, so the harness cannot prove it. **forceatlas2 as a lane** — 5× d3-force's
  bytes, ~1.7× its settle, the same purity class; used only inside the sigma page.

## Risks (in place)

- **Adapter drift is already real** (four counts in five sweeps). If the new adapter is not the ONE every page and the probe read, the table
  lies. Verdict: act now — beat 1 lands `selfTest()` before any page.
- **Swiftshader numbers are CPU rasterisation**: fps is comparable across pages on this host but under-states the draw-call gap on a GPU.
  Verdict: every table carries the caveat; draw calls and purity are the deciding columns, fps is a rank.
- **A raw-three page can "win" on draw calls while quietly dropping features** (link picking, the second badge slot, dash styles, the
  selected-wire-at-beam-0 rule, positions-static-on-tier-press). Verdict: the 24-row matrix is probed per page, never self-reported.
- **Choosing raw three means the suite owns the loop, the rig, the picking pass and the label atlas forever** (~340 lines core, more for the
  full grammar). Verdict: priced by lab-01 against the hollow-wrapper row; the decision record names the migration shape.
- **The `3d-bundle.js` build recipe is NOT committed** (no package.json, no esbuild script anywhere). Any change to the shipped three bundle
  (Line2, PointerLockControls, dropping three-render-objects) first reconstructs the recipe. Verdict: beat 12 commits it — a suite gap
  regardless of the lab's outcome.
- **Vendoring weight vs the WSL2 disk rule**: ~16 MB gitignored (Babylon alone 8.3 MB) on a machine with thin headroom. Verdict: `run.sh`
  guards `df`/`du` first; vendoring is one serial [H] step.
- **The onyx fixture has no fe arm** — it never exercises the fe fold, screen absorption or FEBAND. Verdict: example stays the fe witness; both
  fixtures are mandatory, neither substitutes.
- **Baking the layout changes the product** (drag/expand/filter then need a live local sub-sim; graphviz becomes a regen dependency or a
  fallback with an honest Sources row). Verdict: D7 — a station decision after the labs, never inside them.
- **Time sink**: seven pages × 24 rows × two fixtures is a renderer zoo. Verdict: the kill rule (D5); lab-00 hollow and lab-01 decide.
- **R10 and honest-empty are rendering LAWS**: the probe greps the DOM for the forbidden words and injects an unknown kind; a page that fails
  either has a red row whatever its fps.
