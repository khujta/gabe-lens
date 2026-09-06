#!/usr/bin/env bash
# propagate.sh <twin-root> [--check] — sync this suite's vendored center stack INTO an
# already-adopted twin, then regenerate the twin's center. The copy mapping lived only in
# session memory before this script (finding: no committed twin-propagation recipe).
#
# MAPPING (the non-obvious part — different dirs, same basenames):
#   suite templates/center/generators/{*.py,*.mjs,*.sh}  →  <twin>/scripts/     (UPDATE existing only;
#     propagate.sh itself is the suite's driver, never a twin asset — skipped)
#   suite templates/center/shell/  (minus example/) →  <twin>/templates/center/shell/
# then: <twin>/scripts/refresh_center.sh regen   (re-renders from the twin's own data)
#
# UPDATE-ONLY by design: a generator the twin does NOT already vendor is a NEW capability —
# adopting it is a deliberate call (its shell page, nav wiring, config may be missing), so
# this script REPORTS those and does not copy them. --check reports the drift, writes nothing.
set -euo pipefail
TWIN="${1:?usage: propagate.sh <twin-root> [--check]}"; shift || true
CHECK=0; [ "${1:-}" = "--check" ] && CHECK=1
SUITE="$(cd "$(dirname "$0")/../../.." && pwd)"
GEN="$SUITE/templates/center/generators"; SHELL_SRC="$SUITE/templates/center/shell"
TGEN="$TWIN/scripts"; TSHELL="$TWIN/templates/center/shell"
[ -d "$TWIN" ] && [ -d "$TGEN" ] || { echo "FAIL: $TWIN is not an adopted twin (no scripts/)"; exit 1; }

drift=0; new_gen=()
echo "── generators → $TGEN (update-only)"
for f in "$GEN"/*.py "$GEN"/*.mjs "$GEN"/*.sh; do
  b=$(basename "$f"); case "$b" in propagate.sh|bootstrap_center.sh) continue;; esac   # the suite's drivers, never twin assets (review 2026-09-05: refresh_center.sh — the regen this script RUNS — drifted silently while --check said "in sync")
  if [ -e "$TGEN/$b" ]; then
    if diff -q "$f" "$TGEN/$b" >/dev/null 2>&1; then :; else
      if [ "$CHECK" = 1 ]; then echo "  DRIFT $b"; drift=1; else cp "$f" "$TGEN/$b"; echo "  updated $b"; fi
    fi
  else new_gen+=("$b"); fi
done
# A NEW generator that an UPDATED generator imports is not a new capability — it is a hard dependency the regen
# below would crash on (2026-09-06: _a3_homing.py imported by build_center_a3.py left both twins with a broken
# regen). Land it, say so; every other new generator stays a deliberate adoption.
req_gen=(); opt_gen=()
for b in "${new_gen[@]}"; do
  mod="${b%.py}"
  if [[ "$b" == *.py ]] && grep -lqE "^(import|from) ${mod}\b" "$TGEN"/*.py 2>/dev/null; then
    if [ "$CHECK" = 1 ]; then echo "  DRIFT $b (NEW, required by $(grep -lE "^(import|from) ${mod}\b" "$TGEN"/*.py | xargs -n1 basename | tr '\n' ' '))"; drift=1
    else cp "$GEN/$b" "$TGEN/$b"; echo "  landed $b — NEW, required by $(grep -lE "^(import|from) ${mod}\b" "$TGEN"/*.py | xargs -n1 basename | tr '\n' ' ')"; fi
    req_gen+=("$b")
  else opt_gen+=("$b"); fi
done
[ ${#opt_gen[@]} -gt 0 ] && echo "  NEW (not vendored by this twin — adopt deliberately): ${opt_gen[*]}"
# graft's AGENT SKILL ("get your context from graft before grepping") contradicts the suite's tool floor
# (the map tools first — execution-contract.md); graft serves map CREATION only (ruling 2026-09-02). The dir is
# graft-authored + untracked, so a twin re-decides it every time it is noticed → name it here, once, as
# DELETE-ON-ADOPTION. Reported, never deleted by this script (a user-side dir is the operator's to remove).
[ -d "$TWIN/.claude/skills/graft" ] && echo "  ⚠ $TWIN/.claude/skills/graft/ exists — graft's agent skill; DELETE-ON-ADOPTION (tool floor): rm -rf '$TWIN/.claude/skills/graft'"

echo "── shell (minus example/) → $TSHELL"
if [ -d "$TSHELL" ]; then
  while IFS= read -r -d '' f; do
    rel="${f#"$SHELL_SRC"/}"; case "$rel" in example/*) continue;; esac
    dst="$TSHELL/$rel"
    if diff -q "$f" "$dst" >/dev/null 2>&1; then :; else
      if [ "$CHECK" = 1 ]; then echo "  DRIFT $rel"; drift=1; else mkdir -p "$(dirname "$dst")"; cp "$f" "$dst"; echo "  updated $rel"; fi
    fi
  done < <(find "$SHELL_SRC" -type f -print0)
else echo "  (twin has no templates/center/shell — vendored differently; skipping)"; fi

if [ "$CHECK" = 1 ]; then
  [ $drift = 0 ] && echo "PROPAGATE CHECK: twin is in sync with the suite" || { echo "PROPAGATE CHECK: DRIFT above — run without --check to sync"; exit 1; }
else
  echo "── regenerate the twin's center (its own data)"
  ( cd "$TWIN" && bash scripts/refresh_center.sh regen ) | tail -2
  echo "Propagated. Review the twin's git diff; commit on the twin's working branch."
fi
