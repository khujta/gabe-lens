#!/usr/bin/env bash
# run.sh — the lab's battery: disk guard → adapter self-check on every fixture → every page × {example, onyx} one at a time.
#   ./run.sh                    everything (~minutes: one headless Chrome per page per fixture, serial by the WSL2 rule)
#   ./run.sh example            one fixture
#   ./run.sh onyx lab-01-three-raw.html
# Exit 3 = SKIP (no chrome / playwright-core / fixture) — loud, never silent.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE"
echo "── disk guard (WSL2 rule) ──"; df -h /mnt/c 2>/dev/null | tail -1; du -sh /var/log 2>/dev/null
FREE=$(df -BG /mnt/c 2>/dev/null | awk 'NR==2{gsub("G","",$4); print $4}'); LOG=$(du -sm /var/log 2>/dev/null | cut -f1)
[ -n "$FREE" ] && [ "$FREE" -lt 40 ] && { echo "ALARM: C: under 40 GB free ($FREE G) — stop"; exit 2; }
[ -n "$LOG" ] && [ "$LOG" -gt 2048 ] && { echo "ALARM: /var/log over 2 GB (${LOG} MB) — stop"; exit 2; }
FEEDS="${1:-example onyx}"; ONLY="${2:-}"
[ ! -s vendor/MANIFEST.json ] && echo "vendor/ empty — run ./vendor.sh first (pages that need a bundle will fail their row)"
rc=0
for f in $FEEDS; do
  if [ "$f" != "example" ] && [ ! -f "fixtures/$f/c4-graph.js" ]; then echo "SKIP ⚠ fixtures/$f — run fixtures/fetch-onyx.sh"; rc=3; continue; fi
  echo; echo "── adapter self-check · $f ──"
  node probe.mjs --feed="$f" --only=adapter-check.html --no-readme --fps=0 || rc=1
  if [ "$f" = "onyx" ]; then node probe.mjs --feed="$f" --fn=1 --only=adapter-check.html --no-readme --fps=0 || rc=1; fi
  echo; echo "── pages · $f ──"
  if [ -n "$ONLY" ]; then node probe.mjs --feed="$f" --only="$ONLY" || rc=1; else node probe.mjs --feed="$f" || rc=1; fi
done
exit $rc
