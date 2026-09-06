#!/usr/bin/env bash
# Chrome-harness fixture battery — the executable contract of the shell-JS
# verifier (2026-07-22 alignment review M22).
#
# M22 found the only shell-JS harness (gastify's verify_center_chrome.mjs)
# was DEAD CODE: its tr.rowtog locators match nothing the generators emit, so
# it could neither pass nor catch drift, and adopt-spec's "shell JS ships only
# with its committed harness" was false everywhere. The rewritten harness at
# templates/center/verify_center_chrome.mjs is proven here to both stay SILENT
# on the shipped example pages and FIRE when the page markup or the shell JS
# drifts off the contract. Hermetic: temp copies only, no network, cleans up
# after itself. Exit 0 = all pass.
set -u
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
HARNESS="$REPO/templates/center/verify_center_chrome.mjs"
SHELL_SRC="$REPO/templates/center/shell"
LEDGER="feature-transaction-action-ledger.html"

T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT

pass=0; fail=0
ok()  { pass=$((pass+1)); }
bad() { fail=$((fail+1)); echo "FAIL: $1"; }

run_h() { node "$HARNESS" "$@" >"$T/out" 2>&1; echo $?; }
mkshell() { rm -rf "$T/shell"; cp -a "$SHELL_SRC" "$T/shell"; }

# --- SILENT: the shipped example pages pass ---------------------------------
[ "$(run_h "$SHELL_SRC/example")" = 0 ] \
  && ok || { bad "silent: shipped example pages must pass"; cat "$T/out"; }
grep -q "$LEDGER" "$T/out" && ok || bad "silent: report names the pages it checked"
grep -q "does not reference rowclick.js" "$T/out" \
  && ok || bad "silent: the pre-ledger page is skipped with a note, not failed"

# --- FIRE: page-side drift — the row class the JS keys on is renamed --------
mkshell
sed -i 's/class="xrow"/class="rowx"/g' "$T/shell/example/$LEDGER"
[ "$(run_h "$T/shell/example/$LEDGER")" != 0 ] \
  && ok || bad "fire: renaming .xrow in the page must fail the harness"

# --- FIRE: JS-side drift — rowclick's .xrow selector is renamed -------------
mkshell
sed -i "s/'\\.xrow'/'.row2'/g" "$T/shell/assets/rowclick.js"
[ "$(run_h "$T/shell/example")" != 0 ] \
  && ok || bad "fire: rowclick selector drift must fail the harness"
grep -q "FAIL · .*clicking the row summary opens the row" "$T/out" \
  && ok || bad "fire: selector drift is caught by EXECUTING the JS, not by grep"

# --- FIRE: a cross-referenced row id goes dead (openTarget no-op drift) -----
mkshell
REF=$(grep -o 'href="#dm-[^"]*"' "$T/shell/example/$LEDGER" | head -1 \
      | sed 's/href="#//; s/"$//')
[ -n "$REF" ] || bad "fixture: no #dm- cross-ref found to mutate"
sed -i "s/id=\"$REF\"/id=\"$REF-gone\"/" "$T/shell/example/$LEDGER"
[ "$(run_h "$T/shell/example/$LEDGER")" != 0 ] \
  && ok || bad "fire: a dangling cross-ref anchor must fail the harness"

# --- FIRE: the page stops loading rowclick.js (explicit page mode) ----------
mkshell
sed -i 's#<script src="[^"]*rowclick\.js"[^>]*></script>##' "$T/shell/example/$LEDGER"
[ "$(run_h "$T/shell/example/$LEDGER")" != 0 ] \
  && ok || bad "fire: an explicit page without rowclick.js must fail"

# --- FIRE: a shipped asset the page references is missing -------------------
mkshell
rm "$T/shell/assets/a3-lightbox.js"
[ "$(run_h "$T/shell/example")" != 0 ] \
  && ok || bad "fire: a missing referenced asset must fail the harness"

# --- slots are measured against the SKELETON (review 2026-09-06, onyx prompt placeholders in docstrings) ---
mkshell
SKPAGE=$(cd "$T/shell/example" && for f in *.html; do [ -f "$T/shell/$f" ] && echo "$f" && break; done)
[ -n "$SKPAGE" ] || bad "fixture: no example page with a skeleton of the same name"
SKTOK=$(grep -o '{{[A-Z0-9_]*}}' "$T/shell/$SKPAGE" | head -1)
[ -n "$SKTOK" ] || bad "fixture: the skeleton $SKPAGE carries no {{TOKEN}} slot to test with"
sed -i 's#</body>#<table><tr><td>Replace `{{CURRENT_DATETIME}}` placeholders in the prompt</td></tr></table></body>#' "$T/shell/example/$SKPAGE"
[ "$(run_h "$T/shell/example/$SKPAGE")" = 0 ] && grep -q "content tokens, not slots" "$T/out" \
  && ok || { bad "silent: a {{TOKEN}} that is CONTENT (absent from the skeleton) must not read as an unfilled slot"; grep "TOKEN\|content" "$T/out"; }
sed -i "s#</body>#<div>$SKTOK</div></body>#" "$T/shell/example/$SKPAGE"
[ "$(run_h "$T/shell/example/$SKPAGE")" != 0 ] && grep -q "no unfilled {{TOKEN}} slots on a generated page ($SKTOK" "$T/out" \
  && ok || { bad "fire: a skeleton slot left in the page must fail and be NAMED"; grep "TOKEN" "$T/out"; }

# --- vacuous run refused ----------------------------------------------------
mkdir -p "$T/empty"
[ "$(run_h "$T/empty")" = 2 ] \
  && ok || bad "vacuous: a dir with no qualifying pages must exit 2, not pass"

# --- CHIP-CLASS COVERAGE ----------------------------------------------------
# R10 retired the `orphan` verdict, its `.t-orph` CSS rule went with it, and 219
# chips plus 8 filter buttons kept shipping in the gallery — rendering with bare
# `.tag .ic` and teaching a vocabulary the generator can no longer emit. Nothing
# here caught it: the harness checks markup contracts and asset presence, never
# whether a `t-*` class the pages USE still has a rule that STYLES it. A gallery
# is an exemplar; an exemplar demonstrating a dead class is drift with a
# audience.
# The predicate is STYLED-OR-EMITTED, not styled. A first cut asserting "every
# t-* needs a CSS rule" fired on t-lg and t-uncl, which turned out to be live
# semantic markers from build_center_a3.py whose visual weight comes from their
# sibling s-med/s-gap classes. Those are correct markup, so the assertion was
# wrong, not the gallery. Dead vocabulary is the class that is NEITHER styled
# NOR emitted — precisely what t-orph became the moment R10 landed.
chip_classes() {  # every t-* class the example pages actually use
  grep -oh 'class="[^"]*\bt-[a-z0-9-]*' "$1"/*.html 2>/dev/null \
    | grep -oh '\bt-[a-z0-9-]*' | sort -u
}
live_classes() {  # styled by the shell, OR emitted by a generator
  { grep -oh '\.t-[a-z0-9-]*' "$1/assets/a3.css" 2>/dev/null | sed 's/^\.//'
    grep -oh '\bt-[a-z0-9-]*' "$REPO"/templates/center/generators/*.py 2>/dev/null
  } | sort -u
}

# SILENT: the shipped gallery uses no dead class
mkshell
dead=$(comm -23 <(chip_classes "$T/shell/example") <(live_classes "$T/shell") | tr '\n' ' ')
[ -z "$(echo "$dead" | tr -d '[:space:]')" ] \
  && ok || bad "silent: gallery uses t-* class(es) neither styled nor emitted: $dead"

# FIRE: a class the shell no longer styles and no generator emits must be caught
mkshell
sed -i '0,/class="tag ic t-god"/s//class="tag ic t-retired"/' \
  "$T/shell/example/arch-functions.html"
dead=$(comm -23 <(chip_classes "$T/shell/example") <(live_classes "$T/shell") | tr '\n' ' ')
[ -n "$(echo "$dead" | tr -d '[:space:]')" ] \
  && ok || bad "fire: a t-* class neither styled nor emitted must be reported"

echo "=================================="
echo "chrome battery: $pass passed, $fail failed"
[ "$fail" = 0 ]
