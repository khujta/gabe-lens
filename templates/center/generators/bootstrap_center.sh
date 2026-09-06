#!/usr/bin/env bash
# bootstrap_center.sh <repo-root> [--name <slug>] [--display "<name>"] — the CONFIG-ONLY adoption of the suite's
# command center into a repo that has none. Review 2026-09-06 (repo-study): no skill path did this without the
# human-speed back-catalog flow of /gabe-cc-init (archive · rank · one section per run); a study repo, or any
# first look at a codebase, needs the deterministic half of `init` step 4 on its own — this script IS that step.
#
# WRITES (never overwrites an existing config; re-runnable):
#   <repo>/scripts/                       ← the generators (templates/center/generators/*.py|*.mjs|refresh_center.sh)
#   <repo>/templates/center/shell/        ← the station skeletons (minus example/)
#   <repo>/docs/site/center/center.config.json   ← the skeleton, `entities: {}` — YOU fill them
#   <repo>/.gitignore                     ← the local-only runtime artifacts (gabe-init step 1.8)
# It writes NO adoption.json: with none present the build takes the config's entities as the registry, out loud;
# /gabe-cc-init init·rank·section records the adoption later without redoing any of this.
#
# THEN (printed at the end):
#   1 · fill `entities` in docs/site/center/center.config.json — one block per entity: code.api / code.models /
#       code.schemas / code.services / code.web (literal paths OR globs, `**` recursive) + test_rx (+ models: [classes])
#   2 · a frontend needs `typescript`: run the project's own install (npm ci / bun install / pnpm i) — or export
#       GABE_TS_DIR=<a dir whose node_modules/typescript exists> (the arm SAYS when it borrowed one)
#   3 · bash scripts/refresh_center.sh regen  → docs/site/center/gabe-universe.html (+ every station page)
#   4 · (study) docs/site/center/workflows.js = your missions as journeys → open ?journey=<name>
set -euo pipefail
REPO="${1:?usage: bootstrap_center.sh <repo-root> [--name <slug>] [--display \"<name>\"]}"; shift || true
NAME=""; DISPLAY=""
while [ $# -gt 0 ]; do case "$1" in --name) NAME="$2"; shift 2;; --display) DISPLAY="$2"; shift 2;; *) echo "unknown arg: $1" >&2; exit 2;; esac; done
# the generators dir is where THIS script lives and the shell sits beside it — true in the repo (templates/center/{generators,shell})
# AND in the install (~/.claude/templates/gabe/center/{generators,shell}); the old "../../.. /templates/center" walk resolved to
# ~/.claude/templates/templates/… from the installed copy and landed nothing (found on the tier0 re-bootstrap, 2026-09-06)
GEN="$(cd "$(dirname "$0")" && pwd)"; SHELL_SRC="$(cd "$GEN/../shell" && pwd)"
[ -d "$REPO" ] || { echo "FAIL: $REPO is not a directory"; exit 1; }
REPO="$(cd "$REPO" && pwd)"
[ -n "$NAME" ] || NAME="$(basename "$REPO")"
[ -n "$DISPLAY" ] || DISPLAY="$NAME"
echo "── bootstrap $DISPLAY ($NAME) at $REPO"

echo "── generators → scripts/ (the suite's drivers propagate.sh / bootstrap_center.sh stay in the suite)"
mkdir -p "$REPO/scripts"; n=0
for f in "$GEN"/*.py "$GEN"/*.mjs "$GEN"/*.sh; do
  b=$(basename "$f"); case "$b" in propagate.sh|bootstrap_center.sh) continue;; esac
  if [ -e "$REPO/scripts/$b" ] && diff -q "$f" "$REPO/scripts/$b" >/dev/null 2>&1; then continue; fi
  cp "$f" "$REPO/scripts/$b"; n=$((n+1))
done; echo "  $n file(s) landed"

echo "── shell (minus example/) → templates/center/shell/"
mkdir -p "$REPO/templates/center/shell"; m=0
while IFS= read -r -d '' f; do
  rel="${f#"$SHELL_SRC"/}"; case "$rel" in example/*) continue;; esac
  dst="$REPO/templates/center/shell/$rel"
  if [ -e "$dst" ] && diff -q "$f" "$dst" >/dev/null 2>&1; then continue; fi
  mkdir -p "$(dirname "$dst")"; cp "$f" "$dst"; m=$((m+1))
done < <(find "$SHELL_SRC" -type f -print0); echo "  $m file(s) landed"

echo "── docs/site/center/center.config.json"
mkdir -p "$REPO/docs/site/center"
CFG="$REPO/docs/site/center/center.config.json"
if [ -e "$CFG" ]; then echo "  exists — kept (fill/adjust it by hand)"; else
  python3 - "$GEN/center.config.template.json" "$CFG" "$NAME" "$DISPLAY" <<'PY'
import json, sys
tpl, dst, name, disp = sys.argv[1:]
cfg = json.load(open(tpl))
cfg["project"] = {"name": name, "display_name": disp, "lang": "en"}
cfg["_bootstrap"] = "written by bootstrap_center.sh — fill `entities` (one block per entity: code.api/models/schemas/services/web + test_rx), then `bash scripts/refresh_center.sh regen`"
json.dump(cfg, open(dst, "w"), indent=2, ensure_ascii=False); open(dst, "a").write("\n")
PY
  echo "  written (skeleton — entities: {})"; fi

echo "── .gitignore seeds (local-only runtime artifacts)"
GI="$REPO/.gitignore"; touch "$GI"; added=0
for s in ".kdbp/reviews-archive/" ".kdbp/.push-gate-ok" ".kdbp/PULSE.jsonl" "docs/site/center/inflight.json" "docs/site/center/inflight.js" "docs/site/center/sim.data.js" "scripts/__pycache__/"; do
  grep -qxF "$s" "$GI" || { [ $added = 0 ] && printf '\n# gabe suite — local-only runtime artifacts (gabe-init step 1.8)\n' >> "$GI"; echo "$s" >> "$GI"; added=$((added+1)); }
done; echo "  $added line(s) added"

cat <<NEXT
Bootstrapped. NEXT (in order):
  1 · fill \`entities\` in docs/site/center/center.config.json (see $GEN/center.config.example.json)
  2 · frontend? run the project's own install (npm ci / bun install) so \`typescript\` resolves — or export GABE_TS_DIR
  3 · cd "$REPO" && bash scripts/refresh_center.sh regen
  4 · open docs/site/center/gabe-universe.html — ?journey=<name> opens one trace (docs/site/center/workflows.js)
  adoption record: /gabe-cc-init init · rank · section <entity> (records adoption.json; nothing above is redone)
NEXT
