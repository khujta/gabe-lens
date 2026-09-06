#!/usr/bin/env python3
"""gabe-map — the Gabe Suite's MCP server (stdio, stdlib only): the committed codebase map as tools.

Register once, user scope (ask-first — `./install.sh --register-mcp`):
  claude mcp add -s user gabe-map -- python3 "$HOME/.claude/skills/gabe-map/scripts/server.py"

The wire framework lives in `mcpwire.py` (shared with gabe-kdbp); the tool bodies in `tools.py`
(v1: map_status · entity_context · touches · who_calls · entity_shape · cases_for · owner_of) and
`tools_wave2.py` (the graft equivalents + map lifecycle: find · outline · center_overview ·
blast_radius · map_census · map_diff · center_status · review_drift) and `tools_wave3.py` (the repo-study pair
2026-09-06: trace — the ordered path over levels.json · gates — the inverse of middleware). Binding contract:
references/map-spec.md; design record docs/design/gabe-map/README.md.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mcpwire  # noqa: E402
import tools  # noqa: E402

VERSION = "1.1.0"

if __name__ == "__main__":
    sys.exit(mcpwire.main("gabe-map", VERSION, tools))
