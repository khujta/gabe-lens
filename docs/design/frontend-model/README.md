# Frontend Model — design record & build plan

> A richer frontend arm for the codebase-graph: from "screens" (fetching files) to a real
> structure graph — components, hooks, stores, routes, the frontend's own types — mirroring
> how the backend has models/schemas/endpoints/functions.
>
> Status: **BUILT (P0–P3, 2026-08-23)** — see §9 for what landed, the measured numbers and what the plan got wrong. Triggered 2026-08-16 by the operator's
> question "what about the frontend? those pieces do not exist on the frontend" during the
> levels-graph polish. The polish (color/force/dotted/finder/legend) shipped separately.

## 1. Where we are (Tier 0)

`templates/center/generators/_a3_web.py` is a **regex fetch-extractor**. A frontend file
becomes a node ("screen") ONLY if it makes an API call (`apiClient.GET("/path")` etc.). It
carries the `(method, path)` of each call, which `_a3_graph` matches to a backend endpoint
(the bridge). Nothing else is modeled.

Consequence: the frontend cluster is the **data-fetching layer** (in gustify, the `useX`
hooks), not the view layer. A `.tsx` component that renders UI but never fetches is
invisible. The asymmetry is real —

| | backend | frontend (today) |
|---|---|---|
| node types | model · schema · endpoint · function | **screen (fetching file) only** |
| derivation | Python AST (`function_insight`/`model_insight`) + graft call graph | **regex fetch-sites** |
| edges | FK · touches · returns · calls · imports | **bridge (screen→endpoint) only** |

## 2. Goal — the frontend structure graph

Model the frontend the way the backend is modeled: typed NODES + resolved EDGES, honest-empty.

**Nodes** — DECIDED 2026-08-16: the **FULL** taxonomy, 7 kinds:
`component` · `hook` (useX) · `store` (Zustand/Redux/Context/Jotai) · `route`
(page/route→component) · `fe-type` (the frontend's own TS interfaces — a schema-equivalent)
· `endpoint` (backend, the bridge target) · `screen` = a role/flag on whichever file fetches.
Glyphs LOCKED to the operator-approved set from the `Frontend Graph Tiers` artifact:
component = browser-window · hook = fn-braces rect · store = box/package · route = signpost
· fe-type = schema-braces · endpoint = bolt (all Lucide, matching the levels-graph kit).

**Edges**: `imports` (file→file) · `renders` (component→component via JSX) · `uses-hook`
(component→hook) · `uses-store` (consumer→store) · `fetches` (the existing bridge, screen→
endpoint). This mirrors graft's "one graph, two providers": TOPOLOGY (imports/refs) + DOMAIN
(the node classification).

## 2b. CORRECTION — graft ALREADY indexes the frontend (the gap is ours, not graft's)

Measured 2026-08-16: gustify's `graft/.graph/wiring.json` = **18,494 nodes** (files + symbols,
each with `kind·path·span·signature·exported·summary·crux`) + **47,139 edges**
(`source·target·relation·confidence`), and **28,211 `.ts` refs** sit alongside 25,218 `.py`
(gastify: 22,106 `.ts`). TS files (`App.tsx`, …) are indexed with `origin:ast`.

So **graft has NO frontend gap** — it maps TS topology (imports/calls, cross-file) today, the
same as Python. The gap is entirely in the SUITE's CONSUMPTION: `_a3_web.py` regex-extracts only
fetch-sites and ignores graft's rich TS node/edge data. We have been leaving the frontend
topology on the table.

**This reshapes the plan — REUSE-FIRST:**
- **Topology (edges)** — come from graft's EXISTING TS wiring, not a new tool. `dependency-cruiser`
  is demoted to an optional import-only fallback (graft already covers imports + calls).
- **Domain (node kinds)** — the real new work: classify each graft TS file/symbol into
  component/hook/store/route/fe-type (convention + `ast-grep`, or `ts-morph`).
- **Oracle (verification)** — the compiler still matters: graft's cross-file TS calls are inferred,
  a FLOOR (per the suite's own graft trust-split), so `ts-morph`/`scip` is the authoritative
  denominator that tells us what graft's floor missed.

Net: the frontend arm is mostly a CONSUMER of graft's TS index + a domain classifier + a compiler
oracle — far less new tooling than §3/§4 first assumed.

## 2c. The DUAL PURPOSE — the map as pre-computed context (token-saving), not just a picture

The operator's framing: a codebase map exists so the suite's spine reads pre-computed context
instead of rescanning the codebase every task (graft/graphify's token-saving premise). Honest
current state:
- The ASSET exists and is rich — graft's `wiring.json` carries per-node `summary`/`crux` fields
  built for exactly this, over the WHOLE codebase (backend + frontend).
- The suite surfaces a SLICE into `archmap.json` (backend-leaning) + reads it in TARGETED ways:
  `gabe-cc-entity` assembles an entity context-pack "from the committed `archmap.json`, never
  re-reading the source"; `gabe-execute` uses graft for reach/reuse; `gabe-review` reads `archmap`
  for drift checks. But there is NO universal "inject the precomputed map as context on every task."
- So the double purpose is REAL but under-exploited: the index is a whole-codebase map; the wiring
  to save tokens broadly across the spine is partial.

**Adding the frontend map (this project) makes `archmap` whole-codebase** → `gabe-cc-entity` and any
map-reader then serve FRONTEND context too, same as backend. **Wiring the map as universal spine
pre-context is a SEPARATE, larger arc** (its own design record) — worthwhile, but not folded into
the frontend build; flagged here so it is not lost.

## 3. Research — the tool landscape (2026-08-16)

**There is no single "graft for the frontend."** graft's power is a queryable cross-file
import+call graph; on the frontend that job splits into a **topology arm** (import/reference
edges) and a **domain arm** (classify nodes + prop/type schemas). No tool emits the semantic
node labels (this-is-a-store / this-is-a-hook) — you synthesize those on top.

Ranked candidates (all static, no app-run; JSON-emitting preferred):

| Tool | Yields | JSON? | Build-free? | License | Effort | Role |
|---|---|---|---|---|---|---|
| **dependency-cruiser** | file import edges + **reverse edges (dependents)**, type-only imports, cycles/detacheds | ✅ `-T json` | ✅ (tsconfig for resolution only) | MIT | **low** | **topology arm** — the graft-imports mirror |
| **ast-grep** | AST-precise match nodes: `useX()` calls, `<Component>`, `create()/atom()/useContext()`, fetch sites | ✅ `--json` | ✅ | MIT | **low** | **pattern arm** — the AST-accurate upgrade of the regex extractor |
| **ts-morph** | build-your-own graph over the TS AST + type checker; component/hook/store nodes, render/call edges | you emit it | ✅ (degrades w/o node_modules) | MIT | med | **domain arm** engine |
| **react-docgen** | per-component prop schema (name/type/required/default/JSDoc) | ✅ | ✅ | MIT | low–med | hang a prop schema on component nodes |
| **scip-typescript** | compiler-accurate cross-file **symbol reference graph** (the truest graft-calls parallel) | protobuf (decode step) | static but wants deps installed | Apache-2.0 | med–high | Tier-2 resolved call/ref edges |
| skott / madge | file import edges (subset of dependency-cruiser) | ✅ | ✅ | MIT | low | fallback only |
| stack-graphs | no-build whole-repo name resolution | SQLite, not JSON | ✅ | MIT/Apache | high | long-term watch |
| semgrep | matches + taint (overkill) | ✅ | ✅ | LGPL + **restrictive rules license** | med | avoid (ast-grep is lighter + more permissive) |
| Glean | server-backed index | Angle query | needs a server | BSD-3 | very high | not for a static generator |

**No off-the-shelf tool for state/store detection or routes** — both are bespoke pattern
passes: store = definition (`create`/`createSlice`/`atom`/`createContext`) + consumers
(`useTheStore`/`useSelector`/`useAtom`/`useContext`), joined through the import graph; routes
= Next.js filesystem glob, or ast-grep the router config (`createBrowserRouter`/`createFileRoute`).

Sources: dependency-cruiser github.com/sverweij/dependency-cruiser · ast-grep github.com/ast-grep/ast-grep
· ts-morph github.com/dsherret/ts-morph · scip-typescript github.com/sourcegraph/scip-typescript
· react-docgen github.com/reactjs/react-docgen · skott github.com/antoine-coulon/skott.

## 4. Recommended path

**Tier 1 (do first — ~80% of the value, low cost, honest-empty, build-free):**
`ast-grep` (replace the brittle regex fetch-extractor with AST-accurate call-site + pattern
extraction) **+ dependency-cruiser** (import edges). Yields: screen/hook/component/store nodes
by naming convention + pattern, import edges, the fetch bridge — deterministic JSON both.

**Tier 2 (only once Tier 1 proves the node/edge model):** compiler-accurate reference edges
via `scip-typescript` (protobuf decode) or a `ts-morph` `findReferences` walker; `react-docgen`
prop schemas on component nodes.

Rationale: prove the model with the cheap AST layer before adopting a heavier indexer that
wants `node_modules` present and a protobuf-decode step.

## 5. Architecture fit (two arms, mirroring the backend)

- **`_a3_web.py` grows a topology arm** — shell out to `dependency-cruiser -T json` (self-provisioned
  like graft's `.graph/wiring.json`; `GABE_*_BUILD=0` reads as-found for read-only twin dry-runs),
  parse the module graph → frontend `imports` edges. Honest-empty when the tool or web root is absent
  (byte-identical to today's fetch-only build).
- **`_a3_web.py` grows a domain arm** — an ast-grep pass (rules for `useX`/JSX/`create`/`atom`/
  `useContext`/route configs) classifies each file into a node kind + emits render/uses edges.
  A SEPARATE try/except from the topology arm (a parser bug degrades to honest-empty, never touches
  the FK/graft bytes) — the same defense-in-depth the current web arm already uses.
- `_a3_graph.build_c4_graph` folds the frontend nodes/edges into `GABE_C4` (new L2 kinds +
  cross_edges), the same way the web bridge already lands.
- The levels page (`codebase-archive-lab.html`) `drawFrontend` grows from "screens on a force
  ring" to a small multi-glyph cluster (component/hook/store glyphs) — the force layout + per-entity
  bubble we just shipped already accommodate this (that is WHY we kept the bubble over concentric).

## 5b. Verification & completeness — the ORACLE strategy (operator's core concern)

The backend earned trust because Python's AST is authoritative + graft's graph was
cross-checked by the badge-vs-panel audit (24 defects found). The frontend needs the same
rigor, and the same shape: an authoritative ORACLE + a layered check that names every gap
instead of skipping it silently.

**The oracle = the TypeScript COMPILER.** It resolves every import, symbol, and reference —
it is the engine behind VS Code's "Find All References," so it knows the truth about what
connects to what. Reach it via **ts-morph** (in-process TS Compiler API, emits JSON we
control, degrades gracefully without `node_modules`) — or **scip-typescript** for a portable
committed index. This is the frontend's Python-AST-equivalent, and it is an EXISTING tool
(the operator's "prefer a tool over building from scratch" — the oracle is not hand-rolled).

The extraction and the oracle are DIFFERENT tools on purpose, so they can disagree:
- ast-grep + dependency-cruiser do the cheap, fast extraction (node classification + import edges).
- the compiler (ts-morph/scip) is the authoritative denominator we check that extraction against.

**Three verification layers (mirroring the backend):**

1. **Hermetic BATTERY** (`tests/frontend/`) — a tiny known React app with EVERY node + edge
   hand-enumerated; the extractor must find exactly that set (prove it can FIRE and stay
   silent, mutation-checked). Deterministic, like the synthetic archmaps in `tests/levels`.

2. **Real DRY-RUN + coverage numbers** against gustify's `apps/web` READ-ONLY:
   - **Node coverage** — the compiler enumerates ALL `.ts/.tsx` files (the denominator). Every
     file is either classified (component/hook/store/route/type) or bucketed `unclassified: N`.
     A skipped file is a NAMED number, never a silent drop → "not skipping nodes" is provable.
   - **Edge coverage** — `captured / compiler-resolved` for imports + references. A reference the
     compiler resolves that our graph misses is a listed gap, with the file+symbol.
   - Numbers go in the commit message (the suite's dry-run-on-a-COPY rule).
   - **Hand-verified sample flow** — the recipe-browse flow already enumerated by hand (7 nodes,
     6 edges: route→container→{view,store,hook}, hook→endpoint, type→hook) is a golden assertion.

3. **Adversarial AUDIT** — once it renders, the SAME badge-vs-panel + structural-sweep discipline
   that caught the 24 backend defects: agents diff the drawn frontend graph against the source +
   the oracle, hunting misclassification and missing edges the coverage % can't see.

The completeness guarantee is layer 2's node/edge coverage: the compiler is the total, our
extraction is the numerator, and the difference is always a named list — honest-empty applied
to completeness. **`ast-grep`/`dependency-cruiser` shift from "the extractor" to "the FAST extractor
verified against the compiler oracle"; scip/ts-morph rise from Tier-2 to the verification backbone.**

## 6. Constraints (non-negotiable, from the suite's design record)

Deterministic (sorted globs, no wallclock) · honest-empty (missing tool/root ⇒ empty field,
FK+graft bytes byte-identical) · read-only (never writes the twin tree) · build-free preferred
(no app run; tsconfig for resolution only) · every new detector ships fixture cases in `tests/`
proving it can FIRE and stay silent · a deterministic script runs against real data only after a
dry-run on a COPY with the numbers in the commit message.

## 7. Phased build plan

- **P0 — spike + oracle baseline (1 slice):** against gustify's `apps/web` READ-ONLY, run BOTH
  the fast extractor (`ast-grep` + `dependency-cruiser`) AND the compiler oracle (`ts-morph`
  `getSourceFiles`/`findReferences`, or `scip-typescript`). Report the **coverage numbers**: total
  files (oracle denominator) · classified-by-kind histogram · `unclassified: N` · edges captured /
  compiler-resolved. This IS the verification harness proving nothing is silently skipped — built
  first, before any render. Taxonomy already DECIDED (Full, 7 kinds); P0 validates it against real data.
- **P1 — topology arm:** dependency-cruiser import edges into `_a3_web` (self-provisioned, honest-empty,
  own try/except) → `imports` edges in `GABE_C4`. Battery + twin dry-run numbers.
- **P2 — domain arm:** ast-grep classification (component/hook/store) + render/uses edges. New L2
  kinds + glyphs. Battery + both-twin numbers.
- **P3 — render:** `drawFrontend` multi-glyph cluster (kept bubble + force); the finder + legend
  (visual swatches) already generalize. Playwright field-match.
- **P4 (optional) — Tier 2:** scip/ts-morph resolved reference edges; react-docgen prop schemas.

## 8. Open questions for the operator

- Node-kind taxonomy: is `component · hook · store · route · fe-type` the right cut, or start
  narrower (hook + component + store)?
- Adopt `ast-grep`/`dependency-cruiser` as suite dependencies (npm/binary), or vendor a minimal
  equivalent? (They are external tools the twin must have installed — graft already sets this precedent.)
- Do routes matter for the graph, or is the component/hook/store/fetch core enough for v1?


## 9. BUILT — 2026-08-23 (suite `graft-adoption`, Gabe Universe batch 48)

### What the P0 spike measured (gustify `apps/web`, READ-ONLY, the numbers that changed the plan)

| measure | value |
|---|---|
| oracle denominator (TS compiler, non-test `.ts/.tsx`) | **488 files · 2,806 import sites (2,401 internal-resolved · 404 external · 1 unresolved) · 2,822 exports** |
| graft's TS coverage | every file indexed (2,627 fns · 880 types · 85 interfaces) but only **222 import pairs + 715 call pairs = 38.9 %** of the compiler's 2,290 file→file import pairs |
| graft-convention arm (`derive_frontend`, name/path only) | **637 "components"** vs the compiler's **458 JSX-proven** exported components (over-claims non-JSX Pascal fns + non-exported symbols); 793 fe-types incl. non-exported; 535 `calls` edges, no imports/renders/typed |
| fast regex classifier vs oracle (files) | 206 component · 44 hook · 5 store · 4 fe-type · 1 route · **113 stories** · **111 plain modules** · 4 other — 2 disagreements left (a container whose JSX the scan missed; a barrel) |

**Three plan corrections the numbers forced:**
1. **The TypeScript compiler is the extractor, not the oracle-only.** Import resolution (path aliases, barrels, index files) is compiler work; re-implementing it in Python or adding dependency-cruiser is strictly worse than running the `typescript` every TS frontend already ships. ast-grep/dependency-cruiser are not adopted.
2. **An 8th kind, `module`.** 111 files (23 %) are plain value-export modules (feature logic 52 in cooking, lib, api clients) — the target of 515 component imports. Burying them as "unclassified" would hide a quarter of the frontend; they are an honest named kind (ONE piece per file).
3. **Stories are excluded, named.** 113 `.stories.tsx` files are documentation, not app elements (they would have been "components").

### What landed

- **`templates/center/generators/_a3_fe_extract.mjs`** — the compiler pass (read-only, temp-file output, 4.2 s on gustify): per file → resolved imports · exported symbols {kind, JSX, hook} · per-export body refs {jsx tags · calls · type refs · idents · useContext args} · checker-resolved import BINDINGS (barrels followed). `GABE_TS_DIR` overrides where `typescript` lives (batteries). Exit 3 = no typescript, 4 = no tsconfig.
- **`templates/center/generators/_a3_fe.py`** — `fe_arm(root, entities, screens)`: classification per EXPORT (component = Pascal + JSX proof · hook = `useX` fn · store = create/createContext/atom const or `useXStore` · route = router config or `*Route` / under `routes/` · fe-type · module), homing via `_a3_graft._fe_home` (entity / `design-system` · `app-shell` buckets / candidate features), typed wires resolved through bindings (`renders` · `uses-hook` · `uses-store` · `typed` · `fecall` · `imports`, most-specific wins), **screen absorption** (the fetch arm's `web:` node lands on the file's principal piece), honest-empty (`GABE_FE_EXTRACT=0` · no web · no node · no typescript → `present=False` + reason). Wires are compact index triples.
- **`_a3_graph.fold_fe`** — the arm rides a SEPARATE top-level `fe` key in GABE_C4 (`fe=None` → byte-identical; `present=False` → only `stats.fe`), so the 2D station, the bridge drift detectors and every existing battery see unchanged bytes. `build_center_a3.py` runs it in its own try/except with a presence-flip tripwire.
- **The Gabe Universe fold** (`universe-build/parts/adapter.js` + `layout.js` + `card.js`): pieces → planets under their home (synthetic coloured clusters for buckets/candidates), `module` kind (slab form + grid glyph), `fe-type`→`type`, wires via `FE_REL`, **Types held back at boot** (`_FETYPES`, the Functions precedent — `T` toggle beside ƒ), the shared frontend card builder (Frontend section: home · absorbed screen · exports), the Everything-panel Sources row, the legend roster. **Layout at scale:** the fold tripled the field (260 → 888 planets at rest, 1,501 with types) and the clustering proof measured **48.5 % bleed**; fixed with frontend `KRADF` layers (types core → routes rim), containment 0.3 → 0.6, and a deterministic **hull-overlap relaxation** (`__uniRelaxHulls`: anchors ≥ 1.05·max(R_a+R_b, 2·max(R_a,R_b)) with R = 1.6×RENT, the measured settled radius) → **2.6 %**.

### Measured on gustify (twin-read-only, `GABE_GRAFT_BUILD=0`)

**1,273 pieces** — 437 components · 83 hooks · 5 stores · 22 routes · 613 fe-types (265 referenced by a running piece) · 113 modules — across 8 entities + 2 buckets (design-system 113 · app-shell 98) + 3 candidate features (profile 97 · shopping 55 · me 2). **3,566 wires** — 935 renders · 436 uses-hook · 28 uses-store · 1,124 typed · 815 fecall · 228 imports; 1,563 cross-home. **32 screens absorbed** (all), 48 bridge wires preserved. Excluded + counted: 113 stories · 2 barrels · 2 pascal-no-jsx. Unresolved: 927 refs into libraries, 112 onto files with nothing drawn. Feed: `c4-graph.js` 327 KB → 747 KB.

### Batteries

`tests/frontend/run.sh` (NEW, 45 cases, mutation-proven): the hand-enumerated fixture app (`tests/frontend/fixture/`, 12 files → 11 pieces · 11 wires, every kind + every rel, barrel + alias + story) as a FROZEN extractor JSON (hermetic) + the LIVE compiler case when a `typescript` resolves (`GABE_TS_DIR` or the twins' web `node_modules`) else SKIPPED by name; honest-empty states; `fold_fe` invariants; determinism; the JSX-removed mutation. `tests/gabe-universe` §10u + a frontend-aware render assertion; `tests/arch-graph` 172 unchanged.

### Deferred (named)

- `fecall`/`renders` as their OWN wire kinds on the Connections pane (today they ride `calls`/`imports` styling) — the pane pins 4 rows.
- Route → component tree from the router CONFIG object (path → element) — today only the JSX inside it wires.
- Prop schemas on components (react-docgen) · compiler-resolved reference edges beyond bindings (P4).
- The levels lab (`codebase-archive-lab.html`) still reads graft's convention arm; it has not been switched to `fe`.

## 10. BUILT — 2026-08-28/29 (the FE data-flow spine + write-spine heat)

§9's arm modeled STRUCTURE (pieces + reference edges). This arc added the DATA-FLOW spine on top — which pieces touch state, in which DIRECTION — and rendered it on the Gabe Universe station. Commits LOCAL on `graft-adoption` (`62c2e8a`→`7bd9f31`).

### The four detector decisions (durable rulings)

1. **Same-file render fix** (`62c2e8a`) — `target_of` dropped every co-located JSX render edge, so the batch-48 component taxonomy was wrong for ~half the files. A `_render_target` resolving a no-binding tag to its sibling export fixed it: **36/67 root-views reclassified** (private 183→194, shared 99→124). The taxonomy the tier controls key on is now honest.

2. **F1 cache detector** (`7f888a4`) — a piece calling a query-library hook (`useQuery`/`useMutation`/`useSWR`/…) with **no project binding** is a server-CACHE sink. RULING: a LIBRARY-IDIOM roster (`_CACHE_CALLEES`, same class as `_STORE_`/`_ROUTER_CALLEES`), **never a project name-list**, counting ONLY when the callee resolves to no project piece — a project's own `useQuery` would bind, so honest-empty holds (no query lib → no `cache` key → byte-identical). Known follow-on: RTK-Query's generated `useGetXQuery` hooks are pattern-named — reported, not guessed into the roster. Measured gustify: cache_pieces 56.

3. **The chrome·read·write wire CHANNEL** (`f16a3b3` + `b430a5c`) — every FE call wire is classified by BACKWARD reachability from the sinks (store kind + `screen` fetch + `cache`): a wire reaching a sink is data, else chrome plumbing (muted ×0.4 at the render). The `cx=fecall` false-connector bug is fixed by construction (cx reaches no sink → chrome).

4. **The method-based write DIRECTION** (`b430a5c`) — the KEY ruling. read vs write is the **HTTP METHOD** of the fetch a piece reaches (`_WRITE_METHODS` = POST/PUT/PATCH/DELETE), read from the web arm's per-site method. **Chosen deliberately OVER a react-query `useMutation`/`useQuery` split**, which is single-stack (breaks the moment a twin uses swr, zustand, or raw fetch — gastify has all three). The verb is deterministic and universal, so the FE write spine is the frontend END of the SAME write fabric the backend d2w computes — not a parallel FE-only invention. This is the suite's "no single-stack / gustify-shaped heuristic" principle applied. `fed2w` DEPTH (a level-order BFS, hops-to-a-write-fetch) rides every write-spine piece; a store-object write (`zustand set()`) is NOT method-visible → not claimed (deferred until a twin shows a material store-write population). Measured gustify: 500 state wires split 474 read / 26 write; write_pieces 28; fed2w_max 2.

`feClass` per component (view = route-rendered · detached = no drawn renderer · private/connector/container/leaf — D1 ruling 2026-09-05: "view" was 0 render-parents, App plus 21 lost parents on gustify) is the class the disclosure T0–T3 preset keys on; `connector` requires touches-state.

### The write-spine HEAT — operator rulings D1–D4 (the Write-Spine Heat artifact → `7bd9f31`)

A published decision surface (four live-sample forks) → the operator ruled:
- **D1 · GRADIENT** (not binary) — a FE write wire bands by its target's `fed2w`.
- **D2 · wire + pill** — the WIRE carries the gradient; the `wsites` count + write-depth surface in the node CARD; the node RING is a SEPARATE toggle, **default OFF** (state var `__uniWriteRing` wired; the 3D ring/pill SPRITE is a deferred pass — Universe nodes are WebGL spheres).
- **D3 · a DISTINCT palette** — `FEBAND` blue→magenta (`#2563eb` far → `#7c3aed` → `#c026d3` at-the-write), the **previously-decided option A** from the `universe-build` scratchpad `two-spines.html`. RATIONALE: the FE spine IS the same write fabric, but a distinct gradient means a frontend write never reads as a backend one — `FEBAND` sits BESIDE the backend `BANDPAL` (green→orange), never merged.
- **D4 · a SEPARATE toggle** (`__uniFED2W`, default OFF) — its own "FE write heat" legend row, so the frontend spine reads without the backend heat. The wire branch is `l.write && __feD2WBand`, parallel to the backend `rel==="calls" && __d2wBand`; neither leaks.

### Batteries
`tests/frontend` 45→77 (cache sink both ways · the write channel serialized on `e[3]` · fed2w depth · honest-empty). `tests/gabe-universe` render proof BEHAVIORALLY gates the FE-heat toggle (off-by-default, bands fed2w 0→magenta / 4→blue) + static pins for `FEBAND`/`__uniFED2W`/the legend row/the ring toggle. `tests/arch-graph` 237 (honest-empty pinned).

5. **CLIENT-STORE pieces — a literal KEY is client state** (2026-09-07). A string a piece names when it
   reaches Web Storage (`localStorage`/`sessionStorage`) or the query cache (`queryKey: [<root>, …]`) is the
   frontend's smallest table, and it gets a piece. RULING: the same LIBRARY/PLATFORM-idiom class as
   `_STORE_`/`_ROUTER_`/`_CACHE_CALLEES` — `_STORAGE_VIA` names the two storage objects, `_STORAGE_OPS` names
   the three methods that take a key, and **never a project key allow-list**. The split of labour is the
   extractor's own: `_a3_fe_extract.mjs` captures the tuple `[object, method, key]` VERBATIM (window included)
   and `_a3_fe.py`'s roster decides what it means. A key handed over as an identifier resolves against the
   file's **module-level** string consts and nothing else — a const inside a function is not a shared key. A
   key built by a factory yields no literal, so it is reported by ABSENCE and never guessed (the same honesty
   as RTK-Query's pattern-named hooks below).
   - **Identity is (via, key), not the file.** A token WRITTEN in `useAuth` and READ in the api client is ONE
     piece with `ops: "rw"`, not two — which is the whole reason the arm is worth having.
   - **The piece is minted AFTER `principal` is fixed and never enters `file_pieces`.** `_PRINCIPAL` ranks
     `store` (1) above `hook` (2) and `component` (3), so a key filed under a component's path would HIJACK
     that file's principal piece and steal its screen absorption and module-scope refs. An assert pins it.
   - **No new relation.** Consumers wire over the existing `uses-store`, so REL2KIND · CONN · DASHMAP · the
     legend row and both stations are untouched. The read/WRITE DIRECTION of a client store as a *wire* stays
     deferred with the `zustand set()` case below — it is its own designed pass.
   - `stats.client_stores` + `client_stores_by_via`; the station carries `via`/`ops`/`client` so the card says
     `client state · localStorage` with "the app reads AND writes this key" rather than drawing a column-less
     store. Honest-empty: no key in the tree ⇒ no piece, no wire, byte-identical.

### Deferred (this arc)
- The node RING / `wsites` 3D pill sprite (D2) — awaiting the operator's look at the wire gradient.
- RTK-Query generated-hook detection (pattern-named, not in the `_CACHE_CALLEES` roster).
- Store-object (`zustand set()`) write detection — not method-visible; revisit on a store-write-heavy twin.
- A client store's read/write direction as a WIRE (ruling 5 above) — the `ops` field records it per piece;
  drawing it costs a new rel and the full legend chain, so it waits on the operator asking for it.

## 11. BUILT — 2026-09-03 (classification honesty: O2 rendered-by promotion · O1 `fe-unknown` · module classes)

Trigger: the journey matrix opened "Look for recipes" on a `module` that lit 83 of 85 data columns. Root cause
(analysis artifact `9e481f6b`): `classify_export` returns None for a Pascal `.tsx` function/class export whose own
body holds no JSX, and every None folded into the file's `module` piece — a false claim for two REAL components on
gustify (`RecipeBrowseContainer`, delegated render via imported render-fns; `LocaleSync`, a headless effect
component returning null). The false label severed their parents' `renders` edges (a `<X/>` tag binds only to a
component piece), so the route→container chain was cut: 3 of the 13 routes in `routes/screens.tsx` render the
container and none reached it; 29/113 journeys anchored on a view. The backend has no equivalent — its unknowns are
named (`__unclaimed__` · `external` + `unresolved_tables` · `schema_homing.ambiguous`) and a role it cannot prove
stays empty. Of the 110 modules, 108 were legitimate helper files; the extractor already counted the two misses
(`stats.fe.excluded.pascal_no_jsx: 2`).

### Rulings (operator)
- **O2 first — promote on evidence.** `build_fe` pre-walks every file's export `jsx` tag sets through that file's
  `bindings` (a same-file tag → the sibling) into a `rendered` set of `(file, name)`. A Pascal `.tsx` function/class
  export with no JSX of its own but a rendered-by hit becomes a **component** (counted in `stats.fe.promoted`) and its
  `renders` edge binds. Evidence the extractor already collects; no name-list.
- **O1 second — name the residue.** The same export with NO rendered-by hit becomes kind **`fe-unknown`** (never the
  file's module); `stats.fe.excluded.pascal_no_jsx` now counts exactly that residue. The universe registers it as
  `unknown` (dashed-ring `?` glyph, own colour, its own legend row + definition, hidden at T0–T2 like `module`).
  Pulse **S15** reads `stats.fe.by_kind["fe-unknown"]` from the committed c4-graph — report-never-gate; the residue
  is nagged, not remembered.
- **Module classes (`mclass`)** — what a module DOES, the way `feClass` reads a component and `role` a function:
  `render-fn` (a `.tsx` whose leftover exports hold JSX) · `api` (fetch call sites absorbed from the web arm) ·
  `model` / `config` / `lib` (directory idioms — `_MODEL_SEGS` / `_CONFIG_SEGS` / `_LIB_SEGS`, the same footing as the
  callee rosters, never a project name-list) · `logic` (everything else). Badge on the 3D node, legend rows under
  `module` with a definition each, `stats.fe.by_mclass`.
- **Definitions column** in the legend reference — "what it is, in your words": every type · badge · connector ·
  fleet item carries a reader-voiced definition beside its name (`_LRDEF`, 60 entries).
- **Deferred with triggers:** O3 (`returnsNull` / `returnsCall` proofs in the extractor) until S15 reports a
  residue > 0; O4 (a `render-fn` KIND rather than a module class) until a render-function must be a journey step.

### Batteries
`tests/frontend` (O2 FIRE + edge binds · O1 FIRE · SILENT camelCase helper · mclass render-fn/logic · mclass
api/model/config/lib + `by_mclass`; the old "JSX removed → module" MUTATION now proves promotion, and a second
mutant with the render removed proves `fe-unknown`) · `tests/gabe-universe` (kind registration + badge + legend +
definition pins; render gates) · `tests/pulse-angles` (S15 FIRE · silent at residue 0 · silent without the fe arm).

### Regen finding (same day) — LAZY bindings, and the numbers after
The first twin regen left `RecipeBrowseContainer` as `fe-unknown` (O1 working as designed) because `routes/screens.tsx`
never imports it: every route there code-splits its screen with `const X = lazy(() => import("spec").then(m => ({default:
m.NAME})))`. A `lazy()` const is not an import declaration, so the extractor bound nothing and the file's 13 routes had
ZERO `renders` wires — the real reason only 29/113 journeys could anchor on a view. `_a3_fe_extract.mjs` now binds a
`lazy()` const like a named import (the dynamic import's resolved file + the mapped export, else `default`; an idiom, no
name-list) and `build_fe` matches a `default` binding to the file's default export. Fixture: `src/routes/LazyRoute.tsx`
(refrozen; the enumeration is 19 pieces · 15 wires · 3 routes · 7 cross).
Gustify @ `3ea8a8af` after the change: promoted 2 · residue 0 · renders 837→850 · **route anchors 29→102 of 113** ·
"Look for recipes" opens on `route:CookingRoute` → `component:RecipeBrowseContainer` (connector, 2 lit cells) ·
`by_mclass` model 51 · logic 26 · lib 24 · render-fn 4 · api 2 · config 1.
**Trap recorded:** `universe-build/regen-example.sh` re-assembles `gabe-universe.html` from `parts/` (last touched
`fa67dee`) and lands it over the template — the station has since been edited directly (10+ commits). Only the four
feed files were landed by hand; the parts pipeline needs a re-split-or-retire decision before it is run again.
**Ruled (same day, `8521ba2`): `parts/` RETIRED.** The template is the source of record (`build_center_a3.py` ships it
to every project); `fill-example.py` rehomes the template into the example; `regen-example.sh` no longer assembles or
lands onto the template. `--check` after the change: the 4 feeds OK · codebase-graph.html OK · example page OK.

### D3 — the bridge lands on the export that fetched (ruling 2026-09-05)

The web arm records, per call site, the top-level declaration enclosing it (`_enclosing_export`: the nearest column-0 declaration above an indented call — a floor, no brace matching). The graph build puts `export: fe:<file>#<name>` on the bridge cross-edge (the file stays as `from`, so the codebase-graph station's Screens column is untouched); the frontend arm absorbs a screen per export, so a 16-hook file (`usePantryMutations.ts`) no longer folds onto one piece; the universe's link adapter and the drafter prefer the export piece and fall back to the file's principal. Batteries: arch-graph (export + bridge, byte-identical without) · frontend (absorption per export, the floor) · workflow-drafts (a second hook splits the cluster; mutation = drop the export) · gabe-universe (the FE leg of `POST /pantry/items` starts at `useCreatePantryItem`).

### D2 — hook roles (ruling 2026-09-05)

A hook is the frontend's function; `_a3_fe` gives each one ONE role by precedence from wires it already draws: **streamer** (its attributed fetch is an SSE call, or the api module it calls streams) · **fetcher** (a fetch site attributed to it, a query-library cache sink, or an api-class module it calls that fetches) · **store** (a `uses-store` wire — reads or writes; the extractor does not see setters, so the writer/reader split is the named follow-up) · **orchestrator** (calls other project hooks, nothing above) · **effect** (calls a lib/config module — analytics, logging, idempotency — nothing above) · **deriver** (none of the above). `stats.fe.by_hrole`. Station: the hook ROLE badge (`__BADGE_COL.hrole`), legend-reference rows behind the hook row, the hook row's ⓘ, `_LRDEF` definitions. Battery: `tests/frontend` (six hooks, one per role; mutation = take the fetch away → deriver); `tests/gabe-universe` pins + a headless count (every drawn hook carries a role).

### D5 — store shape and type members (ruling 2026-09-05)

The operator asked why a store shows no data while a model shows its columns. The arm had a holder without a shape: interfaces and type aliases were pieces without members, and a context/store was never wired to its value type. Now `_a3_fe_extract.mjs` records a type's members (`[name, type text]`, methods as `name()`) and a store's shape (the type argument on `createContext<T>()` / `create<T>()(…)`: text · the type names inside it · inline-literal members); `_a3_fe` gives the store `fields` (the referenced type's members, else the literal's) and a `typed` wire to the type piece; the station puts fields/members on `det.cols`, so the card's STRUCTURE section and the journey matrix read a store like a table and a type like a schema. Batteries: `tests/frontend` (fixture: `create<{ dense: boolean }>()` → fields, `createContext<string>()` → shape only, two typed exports' members; synthetic: a store naming a type in another file → that type's members + the typed wire; mutation: no shape → no fields) and `tests/gabe-universe` (a drawn store carries columns).
