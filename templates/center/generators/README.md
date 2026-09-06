# A3 command-center generators

The machine-derived station generator for a project's **Testing Command Center** —
the same pipeline that renders gastify's center, generalized so any project drives
it entirely from one config file. It fills the vendored A3-Tabbed shell skeletons
(`templates/center/shell/`) with facts read from PLAN.md, PENDING.md, LEDGER.md,
junit XML, adoption.json and git at build time. Nothing on the pages is authored
except each entity's lens card; every number is machine-read (the anti-curation
guardrail).

## The one binding file: `center.config.json`

These scripts read **only** from `docs/site/center/center.config.json` and
`docs/site/center/adoption.json`. No project path, suite name, or entity mapping
is hardcoded in the Python. Copy `center.config.template.json` into the center dir
at adoption and fill it; `center.config.example.json` is the gastify binding as a
worked example.

| Key | What it binds |
|---|---|
| `project` | name · display_name · lang — the hub title and page chrome |
| `paths` | center · kdbp · results · proof · e2e_spec_glob · mermaid_renderer |
| `corpora[]` | one per test suite: `key` · `runner` · `kind` · `kind_detail` · `tag_class`. Drives junit loading, the estate totals, the corpus matrix, the per-entity Tests tab, and run-history sources — no suite name is written in code |
| `e2e` | runner + the local-only / coverage-gate notes the prose interpolates |
| `leaf_reports[]` | the OSS HTML reports the sidebar links when on disk |
| `commands` | capture commands run by `refresh_center.sh <mode>` (one shell line each) |
| `foundations`, `code_layers`, `build_architecture` | the KDBP docs to list, the code-map layer order, whether to emit the Architecture station |
| `entities.<slug>` | `test_rx` (claims test files — required), and once the section is adopted: `proofs`, `code` (files by layer), `models` (classes to document) |

**adoption.json is the entity registry** (D123): every `entities` key MUST be a
slug registered there. An unknown slug aborts the build — the drift class this
tool exists to kill, applied to its own config.

## Module map

| File | Role |
|---|---|
| `build_center_a3.py` | orchestrator — loads sources, fills every station, writes the pages + `archmap.json` |
| `_center_data.py` | durable layer — KDBP docs, gate configs, the lens-card parser, and **config + path resolution** every module reads |
| `_results_ingest.py` | run-result loaders — junit / coverage / run-history (the P165 split seam: the sources a run REPLACES, apart from the durable layer) |
| `_a3_render.py` | pure HTML helpers (tables, meters, section banners, markdown) — no data, no state |
| `_a3_feature.py` | per-entity feature pages (Overview · Tests · Evidence · Risk · Growth) |
| `_a3_code.py` | the Code tab — endpoints / models / schemas parsed from source with `ast` |
| `_a3_evidence.py` | the Evidence tab — proof sets walked off disk, narrated from each `manifest.json` |
| `_a3_graph.py` | the C4 codebase graph — a LIBRARY-NEUTRAL `{nodes,edges}` view derived from the in-memory archmap (zero new source read; FK-only L1 edges, honesty laws), emitted as committed `c4-graph.json` + the `window.GABE_C4`/`GABE_C4_COLORS` sibling `c4-graph.js` with a baked ring x/y + deps-gradient fx/fy layout. Feeds the `codebase-graph.html` station. Battery: `tests/arch-graph` (emitter) + `tests/codebase-graph` (station) |
| `_a3_levels.py` | the rich LEVELS graph — `window.GABE_LEVELS` for the lab-native station: functions · use-cases · communities · use-edges · per-piece hub/god/tests/guards, ALL derived from the archmap insight blocks (`function_insight` · `model_insight.internal_refs` · `guard_insight` · `test_insight`) + the C4 topology (cross-file call edges ride graft, honest-empty otherwise). Emitted as `levels.json` + the `window.GABE_LEVELS` sibling `levels.js`. Feeds `codebase-archive-lab.html` (the lab renderer wrapped in the shell chrome). Battery: `tests/levels` |
| `_center_mermaid.py` | build-time mermaid pre-render, cached by content hash |
| `check_center_links.py` | the crawl gate — every internal href resolves, or the build fails |
| `refresh_center.sh` | ONE entry point — `regen` (default, cheap) or a capture mode from `commands` |

## Running it

```bash
scripts/refresh_center.sh            # regen only — re-render from inputs on disk
scripts/refresh_center.sh junit      # run the declared junit capture, then regen
scripts/refresh_center.sh all        # junit + coverage + e2e, then regen
```

`build_center_a3.py` renders from the **vendored** shell
(`<repo>/templates/center/shell/`) so a clone regenerates reproducibly; the
installed suite copy (`~/.claude/templates/gabe/center/shell/`) is a fallback and
any drift between the two is reported, never silently preferred.

## Stack assumptions

The code decode (`_a3_code.py`) parses **FastAPI** decorators, **SQLAlchemy**
`Mapped[...]` columns and **Pydantic** classes with `ast`; the corpus loaders read
**junit** XML (pytest xunit2 / vitest junit reporter). Projects on that stack —
the suite's twin apps — bind cleanly. A different backend swaps the code-decode
parsers; the rest (KDBP, junit, proof, render) is stack-agnostic.

## Provenance

Ported from gastify's field-tested `scripts/` (the reference implementation named
by adopt-spec). Every gastify-specific binding was moved into `center.config.json`;
the port was proved behavior-preserving by a differential byte-diff — fed gastify's
own bindings, the generalized generators reproduce gastify's committed center
exactly (all 10 pages + `archmap.json` byte-identical modulo the wall-clock stamp).
`_center_data.py` was split at the P165 seam (931 → 302 data + 144 results-ingest).

## Environment contract (the GABE_* variables)

`build_center_a3.py` and the arms read these; a fresh regen sets them explicitly:

| Var | Meaning |
|---|---|
| `GABE_REPO_ROOT` | the project whose center is built (its tree is READ; writes only if `GABE_GRAFT_BUILD=1`) |
| `GABE_CONFIG` | that project's `docs/site/center/center.config.json` (bindings + capture commands) |
| `GABE_SHELL_SRC` | the vendored shell skeletons to fill (`templates/center/shell`) |
| `GABE_CENTER_OUT` | redirect ALL writes here (a temp dir → twin-read-only build); unset = the project's own `docs/site/center` |
| `GABE_GRAFT_BUILD` | `1` (default) self-provisions graft (`graft build` + scoped `.ignore` edit — **writes into the twin tree**); `0` reads the index as-found, twin tree untouched — use for a read-only regen |
| `GABE_TS_DIR` | (fe arm) a dir whose `node_modules` has `typescript`; absent → the fe arm is honest-empty |
| `GABE_FE_EXTRACT` | `0` disables the fe compiler pass (honest-empty) |

**Twin-read-only recipe** (never writes the twin): `GABE_GRAFT_BUILD=0 GABE_REPO_ROOT=<twin>
GABE_CONFIG=<twin>/docs/site/center/center.config.json GABE_SHELL_SRC=$PWD/templates/center/shell
GABE_CENTER_OUT=$(mktemp -d) python3 templates/center/generators/build_center_a3.py`.

**Propagate to an adopted twin**: `bash templates/center/generators/propagate.sh <twin-root>`
- `bootstrap_center.sh <repo> [--name <slug>] [--display "<name>"]` — the CONFIG-ONLY adoption of the center into a repo that has none (review 2026-09-06): lands the generators into `scripts/`, the shell (minus `example/`) into `templates/center/shell/`, a `center.config.json` skeleton (`entities: {}` — fill it), the `.gitignore` seeds; never a tracker (the build takes the config's entities as the registry, out loud), never overwrites, re-runnable. Then `bash scripts/refresh_center.sh regen`. A suite-side driver like `propagate.sh` — never vendored.
(`--check` reports drift, writes nothing) — updates the twin's vendored generators + shell,
then runs the twin's `scripts/refresh_center.sh regen`.
