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

## The measured verdict

| page | example draws | onyx draws | purity (ex · onyx) | what it proves |
|---|---:|---:|---|---|
| lab-00 wrapper as shipped | 11,530 | — | 0.60 · — | today's cost: one Group per node, one Line per link, wires + hulls rebuilt every third tick — never settles in 400 s here |
| lab-00 hollow wrapper | 130 | 100 | 0.60 · 0.65 | the middle path: sim + camera stay the wrapper's, rendering is ours and instanced |
| **lab-01 raw three** | **130** | **102** | 0.60 · 0.65 | every must-survive row built at one draw per layer; 240 ticks in 4.3 s / 11.5 s (Blob worker); 19–31 MB |
| lab-02 sigma | 4 | 4 | 0.53 · 0.59 | labels de-collide free; glyph roster, badges, dashes, particles need custom GLSL — a reading lane at most |
| lab-03 cytoscape | canvas | canvas | 0.53 · 0.59 | containment FREE (nested compounds), badges + dashes declarative; Canvas2D at 1 fps and 217 MB on onyx |
| lab-04 cosmos → three | 130 | 102 | **0.93 · 0.97** | a real cluster force; needs ring anchors (a 2D force collapses onto the adapter's x-line); the GPU is CPU-emulated here |
| lab-05 Babylon | 62 | 52 | 0.60 · 0.65 | one call per thin layer; 8.3 MB; a total rewrite. The sweep's "1→1,343 draw-call jump" was its cumulative counter read raw |
| fdp bake | — | — | **0.994 · 0.999** | deterministic, 0 settle, sub-cluster purity 0.97–0.99 — the picture that keeps a reader's spatial memory |
| lab-01 raw · ×4 (5,404 nodes) | 466 | — | 0.50 · — | 240 ticks in 13 s, 34 MB; the per-cluster HULL meshes are the growth (4× the entities → ~260 hull meshes) — one merged hull geometry per level would flatten it under 30 |
| lab-00 hollow · ×4 | 466 | — | 0.50 · — | the same draw count as raw three at 89 MB (the wrapper's node objects still exist, empty) |

Draw calls decide (the station reaches ~39k/frame at T3 today, the wrapper's structural cost). Purity decides where the layout comes
from. Picking correctness ran 14–20 of 20 on every instanced page; the wrapper's raycast 10 of 20.

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

## Traps met (each cost a probe run)

`new THREE.Color(<float>)` is the hex-int constructor (black — the sweep's pick was never proven) · sigma's reducers return the FULL
attribute object (null crashes `addNode`) · cytoscape `[attr]` selectors match a null value · Babylon's `_drawCalls` accumulates across
frames · a 2D cluster force collapses onto the adapter's x-line anchors · fdp segfaults intermittently on this feed (three retries) ·
the WSL one-heavy-job rule (an fdp run beside a Chrome probe died) · `/tmp` does not survive a power outage (the sweeps' archived sources
are gone; the vendored bundles live in the tree).

## Owed

`?ships=1` (D2) · the review fold (lab review workflow) · merged hull geometry per level (the ×4 growth) · the `3d-bundle.js` recipe
commit + byte-compare · the D7 decision · the station's `cooldownTime` fix · the capsule machinery deletion pass.
