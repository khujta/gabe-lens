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
| D1 | 3D primary; one 2D lane only if alive after lab-02/03 | Neither 2D page keeps the composed-node grammar without custom programs (sigma) or at speed (cytoscape). Recommendation: no 2D lane; if a READING station is wanted, cytoscape preset from the bake (~1 beat). |
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
