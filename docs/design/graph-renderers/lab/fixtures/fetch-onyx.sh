#!/usr/bin/env bash
# fetch-onyx.sh — copy the onyx (repo-study tier3) center feeds into fixtures/onyx/ (GITIGNORED — ruling D3).
# The onyx map is the real shape at scale: 794 L2 pieces · 1,626 cross edges · 2,380 function nodes, NO fe arm.
# Source: the local tier3 study clone (read-only for us — nothing is ever written there).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="${GABE_ONYX_CENTER:-$HOME/projects/repo-study/tier3/docs/site/center}"
[ -f "$SRC/c4-graph.js" ] || { echo "fetch-onyx: no c4-graph.js under $SRC (set GABE_ONYX_CENTER)"; exit 2; }
mkdir -p "$HERE/onyx"
cp "$SRC/c4-graph.js" "$HERE/onyx/c4-graph.js"
[ -f "$SRC/levels.js" ] && cp "$SRC/levels.js" "$HERE/onyx/levels.js"
HEAD="$(git -C "$SRC" rev-parse --short HEAD 2>/dev/null || echo unknown)"
C4HEAD="$(grep -o '"head": *"[0-9a-f]*"' "$HERE/onyx/c4-graph.js" | head -1 | grep -o '[0-9a-f]*"$' | tr -d '"')"
printf 'source=%s\nrepo_head=%s\nc4_head=%s\nbytes_c4=%s\nbytes_levels=%s\n' "$SRC" "$HEAD" "$C4HEAD" "$(stat -c %s "$HERE/onyx/c4-graph.js")" "$(stat -c %s "$HERE/onyx/levels.js" 2>/dev/null || echo 0)" > "$HERE/onyx/SOURCE.txt"
cat "$HERE/onyx/SOURCE.txt"
