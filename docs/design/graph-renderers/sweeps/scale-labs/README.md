# Sweep D — scale and layout labs

Eight `file://` labs over the committed example estate, comparing **layout engines** (not
renderers) on the real feed: 1,384 nodes · 4,053 edges · 20 groups, with a `?k=3` switch to
4,152 / 12,279 — onyx's drawn size.

Open [`index.html`](index.html) for the measured comparison and the verdicts.

## The rule this sweep is built on

The variable is the **layout**. Every lab that is not explicitly testing a renderer draws through
the same canvas-2D view in `lab-kit.js`, and the HUD reports `layout ms` and `draw ms` as two
numbers, so no engine can win on the wrong half. Labs whose library owns its own renderer
(cosmos.gl, cytoscape) carry a **harvest → canvas** button that reads positions back and redraws
them on the shared view — which is also the composition test: can this engine drive a renderer we
already own, three.js included?

## Files

| file | what it is |
|---|---|
| `index.html` | the report: measured tables at both scales, verdicts, licence trap |
| `lab-precomputed.html` | D1 · server-baked graphviz sfdp / sfdp-clustered / neato / networkx |
| `lab-d3-worker.html` | D2 · d3-force 3.0.0 in a Blob-URL Web Worker |
| `lab-fa2-worker.html` | D3 · graphology-layout-forceatlas2 0.10.1, Barnes-Hut, in a worker |
| `lab-cosmos-layout.html` | D4 · cosmos.gl 3.4.1 GPU force layout, positions harvested |
| `lab-ngraph-3d.html` | D5 · ngraph.forcelayout 3.3.1 in 3D, projection written by hand |
| `lab-webgpu-force.html` | D6 · hand-written WGSL compute-shader force layout, no library |
| `lab-lod-aggregate.html` | D7 · LOD / aggregation / bundling strategy, no library |
| `lab-fcose-compound.html` | D8 · cytoscape + fCoSE with entities as compound parents |
| `lab-kit.js` | shared: feed, `?k=` scaling, canvas view, convex hulls, HUD, probe hook |
| `lab-feed.js` | the feed (copied from the sibling sweep's deterministic `build-feed.py`) |
| `bake-layouts.py` | generates `lab-layouts.js` — the server-side layouts, deterministic |
| `probe.mjs` | headless gate: boots each lab, asserts no network, screenshots, records |
| `vendor/` | offline bundles; nothing here reaches the network at runtime |

## Reproduce

```bash
python3 bake-layouts.py          # re-bake lab-layouts.js (byte-identical on an unchanged feed)
node probe.mjs                   # all labs at 1x  -> probe-results.json + shots/
node probe.mjs --k=3             # onyx scale      -> probe-results-x3.json + shots-x3/
node probe.mjs lab-cosmos-layout.html
```

`vendor/` is rebuilt only on a machine with network; the pinned versions and their licences are
listed in `index.html`. Three artefacts are copies of the sibling sweep's bundles
(`cosmos-gl.js`, `cytoscape.min.js`, `cytoscape-ext.js`, `d3-force.js`); `graphology-fa2.js`,
`ngraph.js`, `worker-d3.js` and `worker-fa2.js` were built here with esbuild.

## The finding

**graphviz `fdp` honours `subgraph cluster_*`; `sfdp` silently ignores them.** Measured on this
feed with k=10 neighbour purity (of a node's 10 nearest neighbours, what fraction share its
entity):

| engine | bake | entity purity |
|---|---:|---:|
| **fdp + cluster subgraphs** | 1,782 ms | **0.996** |
| *control: group-seeded ring, no layout* | 0 ms | 0.888 |
| sfdp | 547 ms | 0.481 |
| sfdp **with** cluster subgraphs | 534 ms | 0.475 |
| networkx spring_layout | 16,542 ms | 0.472 |
| neato | 3,181 ms | 0.405 |
| fdp **without** clusters | 761 ms | 0.282 |

Every plain force layout scores *worse than doing nothing*, because a force sim optimises edge
length and edge length is not entity membership. Only three engines in the whole sweep can be
told about the 20 groups: graphviz `fdp` (cluster subgraphs), cosmos.gl (`setPointClusters`, a
real GPU force) and fCoSE (compound parents) — and fCoSE takes 2m22s at onyx scale.
`fdp + clusters` is linear on this shape: 1,638 → 3,296 → 4,904 ms at 1× → 2× → 3×.

## Two constraints this sweep discovered

**`file://` blocks classic Workers.** A page at origin `null` cannot do `new Worker('w.js')`, and
`importScripts` of a `file://` URL fails. The worker labs construct their worker from a **Blob
URL** over source text the page already holds — which is why `vendor/worker-d3.js` and
`vendor/worker-fa2.js` are the engine bundled *into a JS string constant* rather than as scripts.
Any production use of a layout worker in a `file://` page has to take this shape.

**WebGPU cannot be gated here.** On this machine (WSL2, Chrome 144) `requestAdapter()` returns
null in every configuration tried — headless, headed with `DISPLAY=:0`, with and without
`--enable-unsafe-webgpu`, `--enable-features=Vulkan`, `--use-webgpu-adapter=swiftshader`. D6's
shader is complete and correct; it simply cannot be *proven* by our own headless render gate,
which is the fact that matters for shipping.
