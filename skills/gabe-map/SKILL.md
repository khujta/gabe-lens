---
name: gabe-map
description: "The suite's MCP server — the project's committed codebase map as 17 tools the agent reaches for mid-reasoning (who_calls · touches · owner_of · cases_for · entity_context · entity_shape · map_status + the graft equivalents find · outline · center_overview · blast_radius · map_census · map_diff · center_status · review_drift + trace · gates), read-only, honest-empty without a center. Usage: /gabe-map status | register | probe [root]"
when_to_use: "Manage the gabe-map MCP server: is it registered at user scope, is it disabled in this project, does the running server match the install, does this project have a map. Human-initiated only; the TOOLS themselves are reached for by every skill through mcp__gabe-map__*."
disable-model-invocation: true
metadata:
  version: 1.2.1
---

# Gabe Map — the codebase map as tools

**Usage:** `/gabe-map status` · `/gabe-map register` · `/gabe-map probe [root]`

## Gabe execution contract (E1–E7)

This skill runs under the suite execution contract — E1 EVIDENCE · E2 RUN-BEFORE-✅ · E3 NO SILENT DOWNGRADE · E4 REUSE FIRST · E5 STATE SYNC · E6 MISSING ANCHOR = STOP · E7 REPORT WHERE — floors, not ceilings; a skill's own gate may be stricter, never looser. Full text: `../gabe-docs/references/execution-contract.md` (if that file is missing, E6 applies — STOP).

## What this does

`scripts/server.py` is a stdio MCP server (Python stdlib only; the wire framework `mcpwire.py` is shared with gabe-kdbp) that serves a project's committed command-center map — `docs/site/center/{archmap,c4-graph,center.config,adoption}.json` (+ `levels.json`, read lazily and ONLY by `trace` · `blast_radius` · `touches` on a task — `map_status` never loads it) — as seventeen tools: the v1 seven, the graft equivalents, and the repo-study pair `trace` · `gates` (ruling 2026-09-02: graft serves map creation only; the skills use these). Registered once at **user scope**, it answers in every project from that project's OWN map, and says plainly when a project has none. It is the suite's **reliability surface**: the questions a skill used to answer by remembering to run a script (who calls this, what touches that, which entity owns this path, which cases cover it) become tools advertised to the harness every session. It is NOT a rail — lifecycle moments stay on hooks and gates — and it writes nothing except the gitignored map-delta lines `who_calls` appends when grep finds a code reference the map missed (five gates; see the spec).

Design record: `../../docs/design/gabe-map/README.md`. Binding contract: `references/map-spec.md`.

## The seventeen tools (`mcp__gabe-map__<name>`)

| Tool | Answers | Reads |
|---|---|---|
| `map_status` | is there a map here, how fresh, graft index state, regen command, **and where it is partial** (`map_health`: mounts · unparseable · twin pass · web roots — each with its state word present · clean · not_emitted) | archmap · c4 · inflight · git |
| `entity_context` | one entity's slice (brief · full incl. gates + stream · raw); providers named, tasks counted apart; omit slug → the registered list, **or the config-only list when no adoption.json** | archmap · adoption · config · c4 |
| `touches` | what touches a file / model / schema / function / entity / endpoint (stream flag, per-route gates + the ASGI middleware that also applies) / task root (`TASK <name>` — registered name or fn, its dispatchers) / case; a screen/hook file → its pieces (hrole · fed2w · homing) and the endpoints it fetches; method targets join on `Class.method`; a piece whose membership witnesses disagree carries `home_evidence` (Part C) | archmap · c4 · levels (task · homing) |
| `who_calls` | who calls or uses a symbol — graft callers ∪ word-boundary git grep, code vs prose; `direction=out` walks callees, `depth` the transitive reach, every answer stamped with `map_confidence` | graft index · git grep (+ the emit) |
| `entity_shape` | who owns URL domain /x; detached domains; a diff's new routes (caveated when route mounts are unresolved) | archmap (fresh) |
| `cases_for` | which C-ids cover X (incl. `TASK <name>`, honest-empty by name); the corpus's max C-id and next-id floor (suite installs excluded; meaningless without `.kdbp/`, and says so) | archmap · git grep |
| `owner_of` | which entity owns these paths or this directory; where the map is blind (and why: unparseable files named) | archmap · center.config |
| `find` | X by name/doc across entities, endpoints (`stream=true` filter), tasks (`TASK <name>`), models, schemas (deduped per file), functions, providers, screens, FE pieces; generated clients de-ranked (graft_find_code's equivalent) | archmap · c4 |
| `outline` | a file's definitions with spans + signatures, owner, models, tests (graft_file_api's equivalent) | graft index · archmap |
| `center_overview` | orientation by entity: rank, status, counts, coverage, arms (graft · web extractor · fe homing · providers · app middleware), census gaps (absent ≠ 0), registry mode (config-only when no adoption.json), map_health (graft_repo_map's equivalent) | archmap · adoption · c4 |
| `blast_radius` | what a change touches — entities, functions, models, endpoints reached, tasks defined + tasks dispatched (levels.json, conf per edge → reading `cross-process`), tests, FE pieces, a reading (floor) | archmap · c4 · levels · git |
| `map_census` | where the map is blind: unclaimed files/models/routes, unwired/ambiguous schemas, **unparseable files, unresolved route mounts, the blocked twin pass, unscanned frontend roots + unhomed fetches**; the empty schema arm said; the `homing` section — pieces whose users/data witnesses disagree with their file (move candidates · shared aspects; evidence only) | archmap · c4 · levels (homing) |
| `map_diff` | how the committed map changed between two refs, per entity, plus task roots and the health delta | git show · archmap |
| `center_status` | the center's actionable list, relayed verbatim | the suite's own `center_status.py` (WS-2) |
| `review_drift` | a review's deterministic drift subjects vs a base ref; NOT RUN is first-class; the suite's own center hunks never count as project fetches | archmap · c4 · PLAN · git |
| `trace` | the ORDERED path from an endpoint, `TASK <name>` or function to the models and providers it reaches — one hop per line with its confidence (extracted · inferred), depth/fanout named, the endpoint's `behind` mass for contrast; a FLOOR | levels.json (lazy) · archmap · c4 |
| `gates` | which endpoints a gate guards — by callee, `file::fn` key, or argument string (`Permission.MANAGE_LLMS`) — split by argument, non-gate deps apart, ungated count, the ASGI middleware on every request; omit gate → the census | archmap · c4 |

**The repo-study pass (2026-09-06, plan `docs/design/repo-study/legend-and-tools-plan.md` Part B):** eleven map facts the generators had learned reached no tool — six projection drops, five join-key mismatches, two missing readers. So: a `TASK <name>` is addressable everywhere the map names it (`endpoint:TASK <name>`; the answer's kind says `task`, never `endpoint`); method targets join on the qualified `Class.method`; absence of an omitted-when-empty key (`unparseable` · `fn_similarity` · `tasks`) reads **clean** only when the study-pass sentinel `route_mounts` is on the map, else **not_emitted — regen to know** (D5); `trace` reads `levels.json`, never graft (`who_calls direction=out` returned nothing on tier0); `gates` is a tool, not a `touches` fold, because an argument string is not a function (D2). Both write nothing and open no subprocess — the tool floor holds unchanged.

## Procedure

1. Treat the text after the invocation as the mode: `status` (default) · `register` · `probe [root]`.
2. Read `references/map-spec.md` before acting — the binding tool contract, wire laws and emit gates. If missing, E6 applies — STOP.
3. **status** — run `python3 scripts/mcp-status.py` (installed: `${ECC_ROOT:-$HOME/.claude}/skills/gabe-map/scripts/mcp-status.py`). It reads `~/.claude.json` (never `claude mcp get`, which launches the server to health-check it): registered at user scope? · disabled for this project (`projects[…].disabledMcpServers`)? · the registered command's path vs the installed `server.py` · `server_sha` of the install. Then run the probe (step 5) against the current directory and relay `map_status`. Present the two verbatim.
4. **register** — ask-first, always: show the exact command and run it only after the operator confirms:
   `claude mcp add -s user gabe-map -- python3 "$HOME/.claude/skills/gabe-map/scripts/server.py"` (the shell expands `$HOME`; the harness stores the absolute path). Idempotent: if `~/.claude.json` already carries `mcpServers.gabe-map`, say so and stop. A **restart of the Claude Code session is required** for a stdio server to appear — say so. Equivalent non-interactive form: `./install.sh --register-mcp` in the suite repo.
5. **probe [root]** — one handshake + `tools/list` + `map_status` through the battery's client:
   `python3 "${ECC_ROOT:-$HOME/.claude}/skills/gabe-map/scripts/probe.py" [root]` — prints the tool names and the `map_status` text. Honest-empty on a project with no center (`present: false` + the reason); a suite-center repo answers with ruling R8, never `/gabe-cc-init`.
6. Report (E7): registered/disabled/path-parity · map present + freshness · server_sha. Never register without the confirmation in step 4.

## Output contract (summary)

- **status:** `gabe-map · registered: yes|no (user scope) · disabled here: yes|no · install parity: ok|MISMATCH <path> · server_sha <12hex>` + the `map_status` text for the cwd project.
- **register:** the command, the confirmation, the result line, the restart reminder.
- **probe:** `tools: 17 (…names…)` + the `map_status` text.
- Every tool answer the server returns is ONE text block: a header `gabe-map · <tool> · map@<head> · <fresh|stale|unknown>` and the JSON result; lists are capped and the cap is named; absence is a named `reason`, never silence.
