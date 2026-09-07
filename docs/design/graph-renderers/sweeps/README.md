# Research sweeps — RECORDS, not labs (folded 2026-09-07, ruling D6)

Five untracked sweeps were written by the graph-renderer research workflow on 2026-09-06/07 (74 MB: vendored bundles, screenshots,
duplicated feeds, page sources). They used FOUR different adapters over the same example estate and reported four node counts
(1,384 · 1,393 · 1,399 · 1,404) — which is why the operator ruled them RECORDS: each folder here keeps only its README, its
`index.html` report and its `probe-results*.json`, so the measured tables stay citable. The page sources, `vendor/`, `_shots/`
and the copied feeds were deleted from the tree; the one lab that supersedes them is `../lab/` (one feed · one adapter · one probe).

The `index.html` reports are NOT runnable here (their pages and vendor bundles are gone; a table filled by a sibling script shows
empty). Read them as documents. Every number in them is a swiftshader (CPU rasteriser, no GPU) number on this WSL2 host.

| Folder | Sweep | What it measured | The finding worth keeping |
|---|---|---|---|
| `2d-labs/` | ten 2D renderers | settle time · idle fps · bundle · grouping primitive · labels | only cytoscape (compound) and G6 (combos) express containment natively; force-graph repaints every tick (15.4 s vs 2.6 ms batched canvas) |
| `libs/` | Sweep A, seven 2D libraries + ×3 scale | layout ms · paint ms · fps at 1,384 and 4,152 | "a green boot is not a render" — sigma reported 60 fps drawing nothing; only the screenshot caught it |
| `scale-labs/` | Sweep D, eight layout engines | layout ms vs draw ms, k=10 entity purity, ×3 | graphviz `fdp` + cluster subgraphs 0.996 purity; every live force sim scores below the seeded ring (0.888); `sfdp` ignores clusters; `file://` blocks classic workers, Blob-URL workers work |
| `libraries/` | Sweep D variant, ten layout labs at four scales | layout wall clock · main-thread fps at 1,404 and 3,931 | sfdp bakes the estate in 550 ms server-side; every in-browser force layout costs 1.8–12 s per load for a worse picture |
| `libs-sweep/` | Sweeps B + C, seven 3D renderers + five game engines | draw calls · fps · boot at core/full/×2–×32 | raw three: 3 draw calls vs the wrapper's 5,366; Godot/Unity/Bevy fail from origin `null`; Babylon the only game host that opens offline |

Design record for the lab that replaced them: [../plan.md](../plan.md).
