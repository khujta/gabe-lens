# Graph-renderer labs — one feed · one adapter · one probe

**Swiftshader caveat, first:** every number here was measured under headless system Chrome with `--use-angle=swiftshader` (CPU rasterisation,
NO GPU) on this WSL2 host. fps and frame ms are comparable BETWEEN pages and UNDER-state the draw-call gap a real GPU would show; read them as a
rank. Draw calls, entity purity, picking correctness and the tier-press law are the deciding columns.

Design record: [../plan.md](../plan.md) · the sweeps this lab was cut from: [../sweeps/](../sweeps/) · chooser: [index.html](index.html).

## The count law (adapter.js, `selfTest()`)

`nodes = L2 pieces deduplicated by id + fe pieces − absorbed web files + function nodes (?fn=1) (+1 when ?inject=1)`

| fixture | L2 raw → unique | fe | absorbed | fn (?fn=1) | nodes | links | ents |
|---|---|---|---|---|---|---|---|
| example (gustify @ `afb646c9`) | 313 → 307 (6 shared externals) | 1,077 | 33 | 281 | **1,351** (1,632 with fn) | 4,053 (4,767 with fn) | 17 (9 entities · 2 buckets · 6 fe twins · 3 candidates) |
| onyx (tier3 @ `85de1bba2a`, no fe arm) | 794 → 794 | 0 | 0 | 2,380 | **794** (3,174 with fn) | 5,320 with fn | 10 |

The four sweeps reported 1,384 / 1,393 / 1,399 / 1,404 because none deduplicated the shared pieces AND absorbed the fetching files the way the
station does; this adapter is a port of the station's own fold, so its count is the station's count.

## Rails

| file | role |
|---|---|
| `feed-loader.js` | picks the fixture from `?feed=` and writes the `<script>` tags (file:// has no fetch) |
| `adapter.js` | THE adapter: `window.GABE_FEED` — nodes · links · ents · anchors · tiers · `seedPositions()` · `force()` (the station's zForce) · `applyBaked()` · `selfTest()` |
| `scorecard.js` | `window.__LAB` + `LAB.*` + the `LABG` probe surface every page registers (`setTier` · `positions` · `screenOf` · `pick` · `pickLink` · `stats` · `settled`) |
| `probe.mjs` | the ONE measurement rail (offline proof · ink · picking · tier-press law · heap · bundle split · R10 grep · purity · README regen) |
| `run.sh` | disk guard → adapter self-check per fixture → every page × fixture, one Chrome at a time |
| `vendor.sh` | exact pins → `vendor/` + `MANIFEST.json`; refuses `@cosmograph/cosmos`; three r185 is read from the station's own bundle |
| `fixtures/fetch-onyx.sh` | copies the tier3 center feeds into `fixtures/onyx/` (gitignored, ruling D3) |
| `bake-fdp.py` · `layouts/` | graphviz `fdp` + cluster subgraphs → `window.GABE_BAKED[fixture]` (`?layout=baked`) |

Knobs on every page: `?feed=example|onyx` · `?scale=full|core|x2|x4|x8` · `?layout=live|baked` · `?tier=0..3` · `?fn=1` · `?fe=0` · `?inject=1`.

## The measured table

<!-- probe:start -->
_(no probe run yet)_
<!-- probe:end -->

## The must-survive matrix

Each page's `LAB.panel({checklist})` claims its rows as free · built · lost; the probe records them beside the numbers and CHECKS the rows it can
(picking, the tier-press law, drawn count, the injected unknown kind, R10, offline). The full 24-row list is in [../plan.md](../plan.md).
