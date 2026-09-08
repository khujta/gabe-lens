# Graph renderers for the Gabe Universe — the design record (2026-09-07)

**The ask (operator, 2026-09-06):** explore other libraries to draw the universe graph, one html page per library, check what applies to
our case, and whether three.js is viable given a possible move toward games. **The answer, measured:** keep three.js and swap the
WRAPPER's render path — raw three draws the whole grammar in one call per layer; the games direction is open from three and closed
from every engine that fails `file://`; the strongest finding is not a renderer but a baked graphviz `fdp` layout that keeps every
entity intact. Plan + rulings: [plan.md](plan.md) · the lab and its measured table: [lab/README.md](lab/README.md) · the research
sweeps this was cut from: [sweeps/](sweeps/).

## One picture

```
   one feed ──► ONE adapter (the station's fold, ported) ──► {nodes, links, ents, anchors, tiers, force, seeds, bake}
                                                                 │
        ┌───────────────┬───────────────┬───────────────┬────────┴──────┬───────────────┬───────────────┐
     lab-00           lab-00 hollow    lab-01 raw       lab-02 sigma    lab-03 cyto     lab-04 cosmos   lab-05 babylon
   the wrapper       wrapper sim +    three, every     2D WebGL,       2D canvas,      GPU cluster     game host,
   as shipped        instanced draw   layer instanced  label grid      compounds       force → three   thin instances
                                                                 │
                                          ONE probe (offline · ink · picking · tier law · purity · README regen)
```

The only variable between two rows of the table is the renderer. Every page draws the same 1,351 nodes (example) or 3,174 (onyx with
the function layer), from the same seeds, under the same tick law (240 ticks), on the same host (swiftshader — fps is a rank).

## The measured verdict (build p2 — every row re-measured after the review fold)

| page | example draws | onyx draws | purity (ex · onyx) | picks (hit + nearer) | what it proves |
|---|---:|---:|---|---|---|
| lab-00 wrapper as shipped | 11,530 | 24,299 | 0.60 · 0.60 | 8 + 9 | today's cost: one Group per node, one Line per link, wires + hulls rebuilt every third tick; never reaches tick 240 in 400 s (27 / 17 ticks); 203 → 320 MB |
| lab-00 hollow wrapper | 130 | 102 | 0.60 · 0.60 | 12 + 7 | the middle path: sim + camera stay the wrapper's, rendering is ours and instanced; 22 → 34 MB |
| **lab-01 raw three** | **156** | **130** | 0.60 · 0.61 | 9 + 11 | every must-survive row built at one draw per layer (+26 sub-cluster label sprites, the station's way); 240 ticks in 4.6 s / 10.9 s (Blob worker); 19 → 25 MB |
| lab-02 sigma | 4 | 4 | 0.53 · 0.54 | 20 + 0 | labels de-collide free; glyph roster, badges, dashes, gradients, particles need custom GLSL — a reading lane at most |
| lab-03 cytoscape | canvas | canvas | 0.53 · 0.54 | 20 + 0 | containment FREE (nested compounds), badges + dashes + gradients declarative; Canvas2D at 1 fps, 131 → 123 MB |
| lab-04 cosmos → three | 156 | 130 | **0.93 · 0.97** | 8 + 12 | a real cluster force on RING anchors (a 2D force collapses onto the adapter's x-line); 74 / 39 ticks in 400 s — the GPU is CPU-emulated here |
| lab-05 Babylon | 62 | 52 | 0.60 · 0.61 | 11 + 7 | one call per thin layer (the sweep's "1→1,343" was its cumulative counter read raw); 8.3 MB; 72 → 115 MB; a total rewrite |
| fdp bake | — | — | **0.996 · 0.998** | — | deterministic, 0 settle, sub-cluster purity 0.98–0.99, with the handler wires in |
| lab-01 raw · ×4 (5,404 nodes) | 570 | — | 0.50 · — | 8 + 12 | 240 ticks in 16.9 s, 33 MB; the per-cluster hull + label meshes are the growth (4× the entities) — one merged geometry per level brings it under 40 |
| lab-00 hollow · ×4 | 466 | — | 0.50 · — | 7 + 10 | the wrapper's empty node objects still exist: 134 MB against 33 |

`picks`: 20 deterministic ids, a real pointer move each; "nearer" = another node's centre within 8 px of the probed pixel — a correct pick
of the nearer node, the cost of a dense field, not a miss. Every page's `drawn` is a RENDERER-side count and equalled the adapter's
expectation on every row; the injected unknown kind was drawn AND warned on lab-01 · 02 · 03 · 05.

Draw calls decide (the station reaches ~39k/frame at T3 today, the wrapper's structural cost). Purity decides where the layout comes
from. The tier press kept every position static on every page that had settled; on a still-ticking page (the wrapper, cosmos) it is
not measurable and the table says so.

**The kill rule (D5) was met:** lab-01 landed every row at one draw per layer on onyx, so lab-04/05 stayed calibration and lab-06 (pixi)
was not built.

## Rulings (2026-09-07) and what each changed

| # | Ruling | Outcome |
|---|---|---|
| D1 | 3D primary; one 2D lane only if alive after lab-02/03 | **Ruled 2026-09-07: every 2D option discarded** (operator). lab-02/03 stay as measured records; lab-06 stays unbuilt. |
| D2 | plain glyphs + `?ships=1` on lab-01 only | The ships row is still owed (one InstancedMesh per GLB); every number above is fleet-free. |
| D3 | onyx as a gitignored copy | `fixtures/fetch-onyx.sh`; onyx has no fe arm, so the example stays the fe witness. |
| D4 | Babylon render + walk, no Havok | Built; `?walk=1` on lab-01 and lab-05 (pointer lock + collisions). Badges/labels out of the spike. |
| D5 | Standard time box + kill rule | Met at lab-01 (above). |
| D6 | Fold the five sweeps | `sweeps/` holds their READMEs, reports and probe results (196 KB); the 74 MB of sources went. |
| D7 | Bake-when-present, decided after the labs | The purity table is the input: bake 0.994–0.999 · GPU cluster force 0.93–0.97 · every live sim 0.53–0.65. Decision owed to the operator (below). |

## The chosen lane and its migration shape

**Raw three, reached in two steps, both measured here.**

1. **Hollow wrapper first** (lab-00 `?hollow=1`): keep 3d-force-graph for the simulation, the camera rig, reheat and drag; return an empty
   `Object3D` from `nodeThreeObject`; draw every layer instanced into `Graph.scene()` from `three-kit.js`. Zero new bytes, 11,530 → 130 draws,
   234 → 37 MB, the station's tick/settle plumbing untouched. This is a render-path swap inside the station, not a rewrite.
2. **Raw three second** (lab-01): drop the wrapper once the hollow path has carried the station's full grammar (journeys, depth highlight,
   fleets, legend). What the suite then owns forever: the loop, the orbit rig, the label atlas, the colour-id picking pass (nodes first,
   wires second), the Blob-worker sim. `three-view.js` is the shape of that ownership (95 lines + the kit's 181).

Two station defects the labs surfaced on the way, both worth their own fix: the wrapper's default `cooldownTime` is 15 s of WALL CLOCK
(the station ships it — on a slow GPU the layout stops after ~17 ticks and looks settled); and the wrapper's per-tick cost is the
station's connector + hull rebuild every third tick.

## The station's own layout (`?layout=station`)

The operator's real question is the real page: *the example station gets slow when there is a lot on it.* So the lab draws the picture the
operator actually sees: `capture-station.mjs` reads the example station's settled positions (settled by ticks, the wall-clock cap lifted) into
`layouts/example.station.js`, and the 3D pages take `?layout=station` — no simulation, the same nodes the station draws at boot (tier 1,
fe-types and functions held), the same wires. The rows below are that picture rendered four ways; the station's own frame cost on this host
is the baseline row.

<!-- station:start -->
_Captured 2026-09-07 by `capture-station.mjs` from the example station at head `afb646c9`: 237 ticks to the engine stop (121 s, the wall-clock
cap lifted), 843 nodes positioned (the 508 fe-types held, the 281 functions off), tier 1 at boot. The station DRAWS 389 of those 843 at tier 1
(read from its own `nodeVisibility` accessor); the lab draws 430 at the same tier — the 41 extra are 20 routes + 21 schemas the station's global
helper fold (`n.__solo` in `visN`) hides, a station control the adapter does not carry (named here, not ported). Rows: `probe.mjs --feed=example
--layout=station --tier=1`, swiftshader, no GPU — fps* is a CPU-rasteriser floor and a rank; draw calls and heap are the deciding columns._

| renderer | nodes drawn | draw calls | triangles | frame ms | fps* | heap MB | pick hit + occluded | what it says |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| **the station itself** (the real page) | 389 | **6,232** | 688,786 | **400** | 2.6 | 175 | — | today's cost on this host: 2.6 frames a second at its boot tier |
| **the station instanced** (`?render=instanced`) | 389 | **189** | 1,550,600 | 565 | 1.8 | **45** | — | the SAME page, the same 843 nodes settled in the same 237 ticks: 33× fewer submissions and 3.9× less heap; the triangles rise because the layers allocate an instance per NODE (843) while the objects path only bodies the 389 the tier draws — 454 zero-scale spheres rasterise nothing but still run the vertex stage, which is what swiftshader charges for |
| lab-00 · the wrapper as shipped | 430 | 2,236 | 453,362 | 400 | 3 | 99 | 11 + 1 | the same library and per-node object model as the station (glyph · badges · bubble · label per node, connectors, hulls); the station's extra calls are its sub-labels, particles, tubes and chrome |
| lab-00 · hollow wrapper (`?hollow=1`) | 430 | **68** | 346,138 | 207 | 5 | 20 | 11 + 1 | the wrapper keeps the sim, camera, drag and reheat; every layer draws instanced from `three-kit.js` |
| lab-01 · raw three | 430 | 91 | 347,212 | 232 | 4 | 16 | 12 + 1 | one call per layer + one mesh per hull and hull label |
| lab-05 · Babylon | 430 | 39 | — | 258 | 4 | 52 | 8 + 1 (2 wrong) | one call per thin layer; a total rewrite of the station |

**What the table settles.** The slowness the operator sees is the RENDER PATH, not the layout and not the node count: the same picture, the same
430 nodes, costs 2,236 draw calls the wrapper's way and 68 instanced — 33× — and the real page pays 6,232 for 389 nodes because it draws more per
node than the lab's replica. Under swiftshader every row is fill-bound (350–690k triangles rasterised on the CPU), so the frame-time gap here
(400 → 207 ms) UNDERSTATES what a GPU gets from 33× fewer submissions; on an integrated GPU the per-call CPU cost is the bottleneck and the
draw-call column is the one that moves. Heap follows the same line: 175 MB on the station, 99 MB on the replica, 20 MB hollow — the wrapper's
per-node object tree (a Group holding a mesh, two bubbles, sprites and a label) is the memory.

Purity reads 0.985 on every row, but over the 430 DRAWN nodes only (the fe-types the station holds are the hardest to keep pure and are
not in this set), so it is not the lab's 0.60 measured over all 1,351 — a like-for-like read needs a capture at tier 3. What it does say: at
its boot tier the station's own zForce + EX band + `recomputeSubAnchors` keeps the drawn entities together, so on this estate the render path,
not the layout engine, is the beat that changes what the operator sees; D7 (the bake) moves down the list.

**The move this licensed — SHIPPED 2026-09-07, REMOVED 2026-09-08** (see the banner above; kept in the past tense because this paragraph is the RECORD of what was built, not a description of the station): the hollow render path INSIDE the real station — `nodeThreeObject` returns an
empty `Object3D`, `linkThreeObject` likewise, and the instanced layers of `three-kit.js` (forms · badge atlas · label atlas · wires per kind ·
particles) draw into `Graph.scene()` from the wrapper's own node positions each frame; hulls, journeys, depth highlight and the legend keep
their code because they never went through the wrapper's per-node objects. Behind a knob (`?render=instanced`, default off until the
gabe-universe battery carries it), measured on the real page with `capture-station.mjs`'s baseline (6,232 calls · 400 ms · 175 MB) as the
before row. The `cooldownTime` wall-clock fix rides the same beat (one line + one assert).

**What it measured, and what it did not.** `capture-station.mjs --query=render=instanced --no-write` at head `e40a2096`: **6,232 → 189 draw
calls** and **175 → 45 MB** of heap on the same 389 drawn nodes, 0 page errors, the same 237 ticks to settle. The picture is complete — a probe
at tier 1 counts 389 icons · 389 bubbles · 389 rims · 389 labels · 210 badges against 389 visible nodes, 0 labels past the atlas cap. What did
NOT improve is the swiftshader frame (400 → 565 ms) and the triangle count (689k → 1.55M), and both have one cause: the layers size themselves
to `nodes.length` (843) while the objects path only builds bodies for the nodes the tier draws (389). A hidden instance is zero-scaled — it
rasterises no pixels — but its vertices still run, and a CPU rasteriser bills for exactly that. On a GPU the submission count is the bottleneck
and the 33× is what the frame feels; this rig cannot show that, which is why the knob ships default-off.

**The named next lever** (not built): compact `mesh.count` to the visible high-water mark by keeping the visible slots contiguous across a
visibility change. That retires the whole triangle debt without touching the picture. Until then the two rows above are the honest pair — read
the draw-call and heap columns, not `frame ms`.

> ## REMOVED — 2026-09-08 (operator ruling). Read this before the sections below.
>
> The instanced render path was built into the station, measured on the real page, made the default, and then
> **taken out again**: *"drop the functionality of render, we didn't really gain much from it."* The station
> draws one three.js object per node once more, and the per-node fleets and route transports are back with it.
>
> **The measurement that settled it** (example estate, swiftshader, no GPU — objects vs instanced):
>
> | | tier 1 · 390 drawn | | tier 3 · 1,397 drawn | |
> |---|---:|---:|---:|---:|
> | | objects | instanced | objects | instanced |
> | draw calls | 9,199 | **204** | 39,384 | **243** |
> | heap MB | 152 | **43** | **456** | **47** |
> | triangles | 935k | 1,558k | 4,031k | **3,026k** |
> | frame ms | 500 | 555 | 1,483 | **1,026** |
>
> The numbers are real and the verdict still went against it, which is the part worth keeping. At the tier the
> operator actually works in, 9,199 calls is comfortable on a real GPU, so a 45× reduction bought nothing they
> could feel — while the toggle, the two render paths, the resume machinery that existed only to survive the
> switch, and the two probes that had to read whichever carrier was live were all cost they *could* feel. The
> win lives at tier 3 and at onyx scale; the price was paid at tier 1, every session. **A speedup nobody
> experiences is not a feature, and the confusion it carries is not free.**
>
> What SURVIVED, because none of it depended on the render path: the `cooldownTime` settle law (a slow GPU
> stopped the layout at ~17 ticks and it looked settled), the Fleet header layout, the trail's move to the
> top-right panel, and the badge-tick camera gate. `three-kit.js` is gone from the shell; the lab keeps its own
> copy, since the lab is the record.
>
> **What it would cost to bring back:** the whole arm is one commit range (`7f0b00f` … `096c771`) and the lab
> pages still draw it. The trigger that would justify it: a repo where tier 3 is the working tier, or an estate
> at onyx scale (≈3.9k nodes) where 39k draw calls per frame is the thing standing between the operator and
> the picture.

**PROMOTED TO THE DEFAULT — 2026-09-07, then REMOVED 2026-09-08 (banner above)**, on the operator's own GPU ("it really accelerates the renderization"), which is the read swiftshader
could not give. `?render=objects` — or the stored `objects` — is the way back, and a lightning-bolt toggle beside the FLEET title flips it.
Two things had to be settled first, and both are measurements, not opinions:

| under the instanced default | draw calls | note |
|---|---:|---|
| the objects path (now the opt-out) | 6,232 | one three.js object per node, one Line per wire |
| instanced, star field as SPRITES | 1,160 | the star field alone is ~958 calls: a Group of two Sprites per star, min(80, members×5) per entity |
| **instanced, star field as a LAYER** | **203** | 1,270 stars in ONE additive quad layer (`TK.starLayer`) — two instance slots per star, the halo carried as a dimmer additive tint |

**What the instanced default LOSES, and why it is structural, not lazy.** Two per-object GLB swarms cannot ride this path:
the per-node **fleets** (`fleetZones()` is built inside `buildNode`, which instancing replaces with an invisible proxy — turning `CFG.warOn`
back on changed the draw count by nothing, because the code never runs) and the per-route **transports** (790 shuttle Groups of 4 meshes each on
the example — enabling them took the instanced page from 202 to **6,524** calls, *worse* than the objects path it replaces). Both stay off under
INST and are named where they are switched off. The star field was in that list until this beat; it is not per-object, so it came back as a layer.

The battery now runs its WHOLE headless suite on the instanced default and measures the objects path explicitly via `?render=objects`. Two probes
had to stop pinning a renderer and start reading whichever carrier is live: the composed-node check (`fcb` — Sprite children vs `_instIconKey` +
`_instSlots`) and the two-slot badge check (`legend56` — `__slot` Sprites vs badge instances). Both assert the same LAW on both paths.

Two defects were found landing it, both worth naming because neither could fail in a static check: the render-mode global was published as
`window.__uniRender`, a name the naming FORMATTER already owned, so `__uniAddWireView` called a string, threw, and left `Graph` null — the page
was dead under the knob and the capture just timed out waiting. And the battery's new headless rows sat AFTER `await b.close()`, so they could
only ever throw. The battery now pins the collision negatively (`window.__uniRender=INST` must not appear) and asserts `drawnIcons === vis`,
because a bare `> 0` accepted a picture missing 90% of its glyphs.
<!-- station:end -->

## D7 — the layout question (owed)

The bake wins on every axis the labs measure: entity purity 0.994–0.999, sub-cluster 0.97–0.99, zero settle, byte-identical on an
unchanged feed. What it costs: graphviz at regen time (EPL-1.0 tool, nothing linked), no settle animation, and drag/expand/filter need a
local sub-sim. What it enables: a picture a reader can learn (the walkable universe's prerequisite). The recommendation stands:
**bake when graphviz is on PATH, live sim as the fallback, an honest Sources row saying which** — one emitter beat, one station beat.

## The bundle recipe (a suite gap, reconstructed)

`templates/center/shell/assets/3d-bundle.js` (1,637,037 B, byte-identical to the spike's) is an esbuild IIFE with no committed recipe.
From the spike README and the 5C trace record:

```bash
mkdir -p _build && cd _build && npm i three@0.185.1 3d-force-graph          # 3d-force-graph PIN UNVERIFIED (1.80 by API inspection)
cat > entry.js <<'JS'
import * as THREE from 'three'; import ForceGraph3D from '3d-force-graph';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { SVGLoader } from 'three/examples/jsm/loaders/SVGLoader.js';
import { ConvexGeometry } from 'three/examples/jsm/geometries/ConvexGeometry.js';
import { MarchingCubes } from 'three/examples/jsm/objects/MarchingCubes.js';
window.THREE = THREE; window.GLTFLoader = GLTFLoader; window.ForceGraph3D = ForceGraph3D.default || ForceGraph3D;
window.SVGLoader = SVGLoader; window.ConvexGeometry = ConvexGeometry; window.MarchingCubes = MarchingCubes;
JS
npx esbuild entry.js --bundle --minify --format=iife --outfile=../3d-bundle.js
```

The bundle carries `three.webgpu.js` + TSL (the wrapper's `useWebGPU` is a no-op, so 832 KB ride for nothing); a raw build with the
addons the station needs measures ~880 KB. **Owed:** commit this recipe beside the bundle and prove it by a byte-compare rebuild.

## The lab review (beat 11) — 39 claims, 38 confirmed, folded

Three seats (the station maintainer's roast · the adapter · the measurement) and one verifier over the union. Five blockers, all fixed:
the `drawn` column recounted the adapter's own tier predicate (now every page reports a RENDERER-side count — instance buffers, sigma's
display data, cytoscape's visibility, Babylon's thin-instance matrices — and the probe compares it with the adapter's expectation); the
endpoint→handler wires never resolved (the key is `det.file#fn`, the station's — +81 wires on the example, +545 on onyx, the fn bakes redone);
a relayouting tier press still scored PASS (the equality now rides `ok` and is re-read after a settle wait); a failing adapter self-test
could not fail the probe (`L.err` is read); and the ink assert's crop held the page chrome (hidden during the shot).

The rest, folded: the wire colour law (flat kind colour except fk · rollup gradients; 85% of wires were entity-tinted), dashes divided by
density (were multiplied — 3–7× too long), the station's `__BADGE_COL` verbatim (three families wore their host body colour), badges
pinned to the camera's right/up like `_mbTick`, the label atlas clipped per cell with an ellipsis, the FE write-spine heat DEFAULT OFF
(`?feheat=1`) and the backend band on calls wires by the target's `d2w` with 4 = green when unknown, generic kinds visible at every tier,
a bake refused for clone rungs, a bake-staleness warning, unknown rels warned, a link law that can fire (candidates = drawn + dropped)
and a handler-wire law, the two tautology self-checks replaced, the node-budget law (tier 0 above 1,600 without `?tier`), R10 and
vendorable rows on every page, the wires row split (dash · thickness · beam · gradient; thickness and the beam toggle LOST on the WebGL
pages), the settle column on one origin, tick counts on the 2D pages, the pick sample spanning the whole id space with `occluded`
split from `other`, stamped rows (`p2`), variant-aware result keys, the runner's exit codes and a guard that fails closed.

Two things the fold itself taught: a checklist label that SPELLS the forbidden words trips the R10 grep (rename the row, never the law);
and a self-test that cannot fail is the same as no self-test — both tautologies were mine.

## Traps met (each cost a probe run)

`new THREE.Color(<float>)` is the hex-int constructor (black — the sweep's pick was never proven) · sigma's reducers return the FULL
attribute object (null crashes `addNode`) · cytoscape `[attr]` selectors match a null value · Babylon's `_drawCalls` accumulates across
frames · a 2D cluster force collapses onto the adapter's x-line anchors · fdp segfaults intermittently on this feed (three retries) ·
the WSL one-heavy-job rule (an fdp run beside a Chrome probe died) · `/tmp` does not survive a power outage (the sweeps' archived sources
are gone; the vendored bundles live in the tree).

## Owed

`?ships=1` (D2) · wire thickness + the per-kind beam toggle on the WebGL pages · merged hull geometry per level (the ×4 growth) · the `3d-bundle.js` recipe
commit + byte-compare · the D7 decision · the station's `cooldownTime` fix · the capsule machinery deletion pass.
