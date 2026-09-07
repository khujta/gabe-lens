# 2D graph-library labs

Ten renderers, one feed, one measurement rail. Open `index.html`.

## What this is

The universe station (`templates/center/shell/gabe-universe.html`) draws the codebase map in 3D on
three.js + 3d-force-graph. This directory asks the 2D question: **which library would draw the same
map, and what would we give up or gain?**

Every lab loads the *same committed example estate* —
`templates/center/shell/example/codebase-graph-station/c4-graph.js` — through the *same adapter*
(`feed.js`), so the only variable between pages is the renderer.

| feed | value |
|---|---|
| nodes | **1,384** (307 backend L2 pieces + 1,077 frontend pieces) |
| edges | **4,104** (482 intra-entity + 343 cross + 3,228 fe + 51 fe→web bridge) |
| entity groups | **14** (9 entities + 5 frontend buckets) |
| node kinds | 15 — endpoint · model · schema · web · external · middleware · provider · flag · element · component · hook · store · route · module · fe-type |
| edge kinds | 15 |
| c4 head | `afb646c9` |

That is deliberately the hard case for a 2D renderer: **entity hulls + typed glyph nodes + readable
labels**, not a monochrome hairball.

## Constraints every lab honours

* opens from `file://`, **no network** — every library is vendored under `vendor/` as UMD/IIFE
* no build step, no bundler, no ES modules (Chrome blocks module scripts on `file://`)
* no blob: workers (Chrome blocks those on `file://` too — the sigma lab uses the *synchronous*
  ForceAtlas2 for exactly this reason)

## Files

```
index.html            the chooser + the comparison table (measured on this host)
feed.js               GABE_C4 -> {nodes, edges, groups}. Shared by every lab.
lab-kit.js            shared chrome: HUD, fps meter, timings, hull overlay, group separation
lab.css               shared dark theme
lab-<lib>.html        one lab per library
vendor/               vendored UMD bundles (~6.2 MB total, gitignore candidates)
_probe/probe.mjs      headless boot check: <lab.html> [shot.png]  -> JSON of measured rows
_probe/shot.mjs       screenshot-only helper (for index.html, which has no #stage)
```

## Running a headless check

```sh
node _probe/probe.mjs "$PWD/lab-sigma.html" "$PWD/_probe/sigma.png"
SETTLE=22000 node _probe/probe.mjs "$PWD/lab-force-graph.html" "$PWD/_probe/fg.png"   # slow settlers
```

Uses system Chrome + the playwright-core already vendored at
`docs/design/graft-adoption/spike/_build/node_modules/playwright-core`, with
`--use-angle=swiftshader` (no GPU on this host). **Every fps number in these labs is therefore a
software-rasteriser number** and is a floor, not a ceiling.

## The three findings the labs exist to make concrete

1. **Only two libraries here have native grouping.** cytoscape.js (compound nodes) and AntV G6
   (combos) express "this node lives inside that entity" as data the *layout* respects. Everywhere
   else — sigma, vis-network, ECharts, vivagraph, cosmos.gl — the entity hulls in these labs are our
   own overlay canvas (`LAB.hullOverlay`), plus a projection call that differs per library.

2. **Layout, not rendering, is the cost at this size.** 1,384 nodes is small for every renderer here;
   nothing struggled to *paint*. What separates them is the settle: 0.70 s (vivagraph) · 0.73 s
   (sigma FA2) · 1.2 s (G6) · 1.6 s (d3-force) · 3.6 s (vis-network) · 4.0 s (ECharts) · 7.6 s
   (cytoscape fcose) · 15.4 s (force-graph, because it repaints on every tick) · never blocks
   (cosmos.gl, which runs the simulation on the GPU).

3. **Per-node draw callbacks forbid batching, and it shows.** force-graph calls `nodeCanvasObject`
   1,384 times and strokes 4,104 links individually per frame. The hand-rolled d3+Canvas lab draws
   the identical scene by bucketing strokes per colour — ~15 `stroke()` calls instead of 4,104 — and
   redraws in **2.6 ms**.

See `index.html` for the full table, the fps caveat, and why react-flow, Konva, Graphistry and the
commercial SDKs (KeyLines/ReGraph, Ogma, yFiles) got no lab.
