#!/usr/bin/env bash
# Center-generator fixture battery — the executable contract of the center's
# guard layer (2026-07-22 alignment review M01/M02/M04/M05/M09/M12).
#
# Every deterministic guard the generators ship is proven able to both FIRE and
# stay SILENT here: the refresh driver's capture→gates chaining (M01), the
# crawl gate's dead-href / estate-probe / empty-crawl / paths.center cases
# (M02, M04), the D123 unknown-slug abort, the lens-card completeness abort,
# the shell-missing exit 2 and the a3.css .xtbl guard exit 3, and the flow
# grammar + classifier honesty rules (M05, M12). Hermetic: temp fixture
# projects, env-override lab pattern (GABE_REPO_ROOT / GABE_SHELL_SRC), no
# network, cleans up after itself. Exit 0 = all pass.
set -u
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
GEN="$REPO/templates/center/generators"
SHELL_SRC="$REPO/templates/center/shell"

T=$(mktemp -d)
trap '[ -n "${KEEPFIX:-}" ] || rm -rf "$T"' EXIT
[ -n "${KEEPFIX:-}" ] && echo "fixture kept: $T"

pass=0; fail=0
ok()  { pass=$((pass+1)); }
bad() { fail=$((fail+1)); echo "FAIL: $1"; }

# --- fixture project ------------------------------------------------------
mk_fixture() { # $1 = dir, $2 = center rel path (default docs/site/center)
  python3 - "$1" "${2:-docs/site/center}" <<'PY'
import base64, json, sys
from pathlib import Path
root, center_rel = Path(sys.argv[1]), sys.argv[2]
c = root / center_rel
(c / "cards").mkdir(parents=True)
(root / "src").mkdir(parents=True)
# A real FastAPI endpoint so the endpoints lens has rows: MODELS USED links
# must route through the xpage map on the architecture pages (parsed via ast,
# never imported, so no fastapi dependency needed).
(root / "src" / "api.py").write_text(
    "from src.schemas import GadgetOut\n\n"
    'router = APIRouter(prefix="/gadgets")\n\n\n'
    '@router.get("/one", response_model=GadgetOut)\n'
    "def get_gadget():\n"
    '    """Fetch one gadget."""\n'
    "    return GadgetOut()\n\n\n"
    # A SECOND endpoint that NO case touches — the guard chip's FIRE case at
    # the endpoint altitude (/one stays tested, so the SILENT case survives).
    '@router.get("/two", response_model=GadgetOut)\n'
    "def get_other_gadget():\n"
    '    """Fetch another gadget."""\n'
    "    return GadgetOut()\n\n\n"
    # A third endpoint whose HANDLER a case imports and calls, while no case
    # drives its ROUTE. by_endpoint alone calls this untested; the union does
    # not. Without this shape the two are indistinguishable in a fixture.
    '@router.get("/three", response_model=GadgetOut)\n'
    "def get_third_gadget():\n"
    '    """Fetch a third gadget."""\n'
    "    return GadgetOut()\n\n\n"
    "def handler():\n    return 1\n")
# An over-budget file so the Code area's action table has a structure row
# (the folded-price shape needs rows to render).
(root / "src" / "big.py").write_text("# filler\n" * 810)
# Functions for the FUNCTIONS lens: a base helper used same-file, a helper no
# case names, a near-duplicate pair, and a god-length def.
# The MERGE fixture (R10): two defs whose bodies share 16 of 17 identifiers
# (89%, past _FN_MERGE_FLOOR = 0.85) and each carry ≥ 8 (the sizable floor).
# Similarity is CORPUS-COMPLETE — two mapped defs being 89% alike stays true
# whatever lives outside the map, which is why it replaced the orphan flag as
# the candidate basis.
_FN_TWIN = (
    "def collate_gadget_{sfx}(records, lookup):\n"
    "    totals = {{}}\n"
    "    for entry in records:\n"
    "        bucket = entry.kind_label\n"
    "        weight = entry.amount_value\n"
    "        totals[bucket] = totals.get(bucket, 0) + weight\n"
    "    ranked = sorted(totals.items(), key=lambda pair: pair[1])\n"
    "    average = float(sum(totals.values())) / float(len(ranked) or 1)\n"
    "    report = {{'ranked': ranked, 'average': average, 'lookup': lookup}}\n"
    "    return report\n\n\n")
(root / "src" / "funcs.py").write_text(
    "from src.widgets import PendingThing\n\n\n"
    "def plan_widget(p: PendingThing) -> PendingThing:\n    return p\n\n\n"
    "def make_gid():\n    return 'g-1'\n\n\n"
    "def build_gadget(seed):\n    return make_gid() + seed\n\n\n"
    # No case names it and no mapped file calls it. That is an UNTESTED-surface
    # fixture and nothing more — after R10 the center may report the absence of
    # indexed callers, never assert the def is dead.
    "def lonely_helper():\n    return 0\n\n\n"
    "def emit_gadget(d: GadgetDraft) -> GadgetDraft:\n    return d\n\n\n"
    + _FN_TWIN.format(sfx="alpha") + _FN_TWIN.format(sfx="beta")
    # The SPLIT fixture: past _FN_GOD_LINES = 50.
    + "def sprawler():\n" + "    x = 1\n" * 52 + "    return x\n")
# A schema whose fields carry machine-readable descriptions (kwarg + trailing
# comment) for the data-model Description column.
(root / "src" / "schemas.py").write_text(
    "class GadgetOut:\n"
    "    gid: str  # the gadget's public identifier\n"
    "    size: int = Field(description=\"measured footprint in mm\")\n"
    "    raw: bytes\n"
    "\n\nclass GadgetIn:  # 100% structural twin of GadgetOut -> merge candidate\n"
    "    gid: str\n"
    "    size: int\n"
    "    raw: bytes\n"
    "\n\nclass GadgetDraft:  # used by emit_gadget as param AND return -> in-out\n"
    "    gid: str\n"
    "    note: str\n"
    # The model SPLIT fixture (R10): 16 fields, past _GOD_FIELDS = 15. Field
    # names share nothing with the other three, so it perturbs no twin pair.
    "\n\nclass GadgetBlob:  # 16 fields -> god class -> split candidate\n"
    + "".join(f"    {_f}: str\n" for _f in
              ("alpha", "bravo", "charlie", "delta", "echo", "foxtrot",
               "golf", "hotel", "india", "juliet", "kilo", "lima",
               "mike", "november", "oscar", "papa")))
(root / "tests" / "results").mkdir(parents=True, exist_ok=True)
(root / "tests" / "test_gadgets.py").write_text(
    "from src.schemas import GadgetOut\n"
    "from src.funcs import make_gid\n"
    "from src.api import get_third_gadget\n\n\n"
    "def test_handler_direct_C18():\n"
    "    get_third_gadget()\n\n\n"
    "def test_lists_gadgets_C11(client):\n"
    '    client.get("/gadgets/one")\n\n\n'
    "def test_gid_format_C12():\n"
    "    make_gid()\n"
    "    GadgetOut()\n\n\n"
    # No own facts and no C-id: FIRES the ledger's via-file inherited chips
    # (Q1) and the unminted honesty tag (Q2).
    "def test_unlabeled():\n"
    "    assert True\n\n\n"
    # Located def for the '>'-parametrize case (C15) — no facts of its own,
    # so it cannot inherit the file's endpoint hits and skew via-route.
    "def test_retry_backoff_C15():\n"
    "    assert True\n")
# A CI/tooling test NO entity claims and NO app import reaches (the gastify
# C1710 shape): its fold must render the named gaps (entities: unclaimed ·
# exercises: no app joins) instead of a silently thinner spine.
(root / "tests" / "test_ci_gate.py").write_text(
    "def test_pipeline_shape_C16():\n"
    "    assert True\n")
# The gastify C1599 shape: the test imports a REAL repo file that NO entity's
# code map registers — the fold must render the actionable TBD gap
# ("unmapped imports"), never the infra-flavored "no app joins".
(root / "tools").mkdir(exist_ok=True)
(root / "tools" / "ci_helper.py").write_text("VALUE = 1\n")
(root / "tests" / "test_tooling.py").write_text(
    "import tools.ci_helper\n\n\n"
    "def test_shape_check_C17():\n"
    "    assert True\n")
# A WEB corpus slice: a ts source in the entity's code map + a vitest-shaped
# junit whose describe carries provenance tokens — FIRES the tag facet
# (DF3/W1 -> data-tag + .ltag pills + the tag filter) and the uses·T3 chips
# (imported symbols are the closest file-tier gets to naming what is under
# test).
# WSeed lives in a file the TEST never imports — its link in planWidget's
# signature must resolve through the GLOBAL ts-export index.
(root / "src" / "kinds.ts").write_text(
    "export type WSeed = { gid: string };\n")
(root / "src" / "widget.ts").write_text(
    'import type { WSeed } from "./kinds";\n\n'
    "export function planWidget(seed: WSeed): GadgetOut {\n"
    "  return { gid: seed.gid } as GadgetOut;\n}\n"
    'export const WIDGET_KIND = "w";\n')
# On disk, exports fine — but NOT in the gadget entity's code registration:
# the web test's import of it must surface as the unmapped-imports TBD gap.
(root / "src" / "fmt.ts").write_text(
    "export const fmt = (n: string): string => n;\n")
(root / "tests" / "widget.test.ts").write_text(
    'import { planWidget, WIDGET_KIND } from "../src/widget";\n'
    # An import that resolves to a real ts file OUTSIDE the entity's code
    # registration: the web-corpus half of the unmapped-imports TBD gap.
    'import { fmt } from "../src/fmt";\n\n'
    # A route literal: the endpoint gains a FILE-level web receipt, so the
    # fold's arithmetic rows (N file(s) · M case(s)) have a FIRE case.
    'const url = "/gadgets/one";\n\n'
    'it("arms", () => planWidget(fmt(WIDGET_KIND)));\n')
(root / "tests" / "results" / "web-junit.xml").write_text(
    '<testsuites><testsuite name="vitest" timestamp="2026-07-23T00:00:00">'
    '<testcase classname="tests/widget.test.ts" '
    'name="DF3 widget guard (review W1) &gt; C14 · arms on edit" '
    'time="0.01"/>'
    "</testsuite></testsuites>")
(root / "tests" / "results" / "api-junit.xml").write_text(
    '<testsuites><testsuite name="pytest" timestamp="2026-07-23T00:00:00">'
    '<testcase classname="tests.test_gadgets" '
    'name="test_lists_gadgets_C11" time="0.1"/>'
    # C18 imports and CALLS an endpoint handler without driving its route —
    # the shape that separates the guard union (by_endpoint OR by_function)
    # from by_endpoint alone. The corpus IS the junit: a test def not listed
    # here is not a case and credits nothing.
    '<testcase classname="tests.test_gadgets" '
    'name="test_handler_direct_C18" time="0.1"/>'
    # C12 ran as two parametrize executions: ONE identity, one ledger row —
    # inside a pytest class so the card's # CLAIMS line can join it by NAME.
    '<testcase classname="tests.test_gadgets.TestGadgets" '
    'name="test_gid_format_C12[a]" time="0.1"/>'
    '<testcase classname="tests.test_gadgets.TestGadgets" '
    'name="test_gid_format_C12[b]" time="0.1"/>'
    '<testcase classname="tests.test_gadgets" '
    'name="test_unlabeled" time="0.1"/>'
    # A pytest parametrize whose id carries ">" (a lambda repr — the gustify
    # C494 shape): the ledger must NOT read it as a vitest "Describe > case"
    # split, or the C-id is dropped and the row loses its anchor.
    '<testcase classname="tests.test_gadgets" '
    'name="test_retry_backoff_C15[&lt;lambda&gt; at 0xbeef&gt;-0]" time="0.1"/>'
    '<testcase classname="tests.test_gadgets" '
    'name="test_retry_backoff_C15[&lt;lambda&gt; at 0xbeef&gt;-1]" time="0.1"/>'
    '<testcase classname="tests.test_ci_gate" '
    'name="test_pipeline_shape_C16" time="0.1"/>'
    '<testcase classname="tests.test_tooling" '
    'name="test_shape_check_C17" time="0.1"/>'
    "</testsuite></testsuites>")
cfg = {"project": {"name": "Fixture", "domain": "battery"},
       "paths": {"center": center_rel, "kdbp": ".kdbp",
                 "results": "tests/results", "proof": "tests/web-e2e/proof"},
       "corpora": [{"key": "api", "runner": "pytest",
                    "kind": "integration", "kind_detail": "HTTP surface",
                    "tag_class": "l-api", "kpi_detail": "pytest"},
                   {"key": "web", "runner": "vitest",
                    "kind": "unit", "kind_detail": "components",
                    "tag_class": "l-web", "kpi_detail": "vitest"}],
       "entities": {"gadget": {"test_rx": "gadget|widget",
                               "proofs": ["g1", "solo"],
                               "code": {"api": ["src/api.py"],
                                        "services": ["src/big.py",
                                                     "src/funcs.py"],
                                        "schemas": ["src/schemas.py"],
                                        "web": ["src/widget.ts",
                                                "src/kinds.ts"]},
                               "models": []}}}
# The config ALWAYS lives at the DEFAULT center path — it is where paths.center
# itself is read from (_center_data: "CENTER_DIR is where config lives, so it
# cannot itself come from config"); everything else follows the override.
cfg_home = root / "docs/site/center"
cfg_home.mkdir(parents=True, exist_ok=True)
(cfg_home / "center.config.json").write_text(json.dumps(cfg, indent=1))
(c / "adoption.json").write_text(json.dumps(
    {"sections": [{"entity": "gadget", "display_name": "Gadget",
                   "status": "adopted", "rank": "high",
                   "signals": "fixture", "notes": ""}]}, indent=1))
(c / "cards" / "gadget.md").write_text("""# HANDLE
The gadget ledger.
# REVIEWED
2026-07-25 — fixture operator, on the built pages: the ledger and the proof set.
Walk of the refreshed page still owed separately.
# WHAT & WHY
Tracks gadgets end to end.
# FOR WHOM
Fixture people.
# FLOWS
- scan ★ → receipt into the ledger
- manual → typed entry path
# IS
The gadget slice.
# IS NOT
Everything else.
# DECIDED
- D1 fixture ruling.
# CLAIMS
- TestGadgets — gid format keeps its shape
""")
png = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
    "YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")
g1 = root / "tests/web-e2e/proof/g1"
g1.mkdir(parents=True)
(g1 / "01-walk.png").write_bytes(png)
# The spec points at a CAPTURED test file — the evidence seam joins it to
# the corpus record (C14) and renders the Verified-by line.
(g1 / "manifest.json").write_text(json.dumps(
    {"feature": "Gadget scan walk", "spec": "tests/widget.test.ts",
     "proof_form": "recorded journey", "source_run": "local 2026-07-22",
     "role": "principal", "flows": ["scan"],
     "legs": {"walk": ["01"]},
     "narration": {"story": "One pass through the scan flow.",
                   "legs": {"walk": "start to finish"}}}, indent=1))
# A single-FILE proof set: loose at the proof root (M04's exact case).
(root / "tests/web-e2e/proof/solo.png").write_bytes(png)
# A proof set NO entity claims: the shelf must name it unclaimed, never
# render it as an anonymous row.
stray = root / "tests/web-e2e/proof/stray"
stray.mkdir()
(stray / "01-x.png").write_bytes(png)
# Tool residue inside the proof root (.ruff_cache landed on the gastify
# shelf): dot-dirs are never proof sets.
cache = root / "tests/web-e2e/proof/.some_cache"
cache.mkdir()
(cache / "junk.png").write_bytes(png)
# A LEGACY set whose folder name matches an entity's test_rx: the shelf
# must wear the legacy tag, narrate through its shot names (3 + the
# named-path rest), and suggest the LIKELY owner.
wlw = root / "tests/web-e2e/proof/widget-legacy-walk"
wlw.mkdir()
for _i, _nm in enumerate(["01-open", "02-fill", "03-save", "04-done"]):
    (wlw / f"{_nm}.png").write_bytes(png)
# Pre-commit gates: a well-known id (curated one-liner) + a local hook that
# describes itself through its own `name:` line.
(root / ".pre-commit-config.yaml").write_text(
    "repos:\n"
    "  - repo: https://github.com/astral-sh/ruff-pre-commit\n"
    "    rev: v0.4.0\n"
    "    hooks:\n"
    "      - id: ruff\n"
    "  - repo: local\n"
    "    hooks:\n"
    "      - id: size-budget\n"
    "        name: size budget report\n"
    "        entry: bash scripts/size.sh\n"
    "        language: system\n")
PY
}

build() { # $1 = fixture root, $2 = shell dir; echoes exit code
  (cd "$T" && GABE_REPO_ROOT="$1" GABE_SHELL_SRC="$2" \
     python3 "$GEN/build_center_a3.py" >"$T/build.out" 2>&1; echo $?)
}
gate() { # $1 = fixture root; echoes exit code
  (cd "$T" && GABE_REPO_ROOT="$1" \
     python3 "$GEN/check_center_links.py" >"$T/gate.out" 2>&1; echo $?)
}

# --- builder guards: SILENT (happy build) + every FIRE ---------------------
FIX="$T/fix"; mk_fixture "$FIX"
[ "$(build "$FIX" "$SHELL_SRC")" = 0 ] && ok || { bad "builder: happy fixture must build (see $T/build.out)"; cat "$T/build.out"; }
[ -f "$FIX/docs/site/center/feature-gadget.html" ] && ok || bad "builder: feature page written for carded entity"
# Data-model Description column: kwarg + trailing-comment sources render,
# a bare field stays an em dash (never invented).
grep -q '<th>Description</th>' "$FIX/docs/site/center/feature-gadget.html" \
  && ok || bad "dm: Description column header renders"
grep -q "the gadget&#x27;s public identifier\|the gadget's public identifier" "$FIX/docs/site/center/feature-gadget.html" \
  && ok || bad "dm: trailing-# comment becomes the field description"
grep -q 'measured footprint in mm' "$FIX/docs/site/center/feature-gadget.html" \
  && ok || bad "dm: Field(description=) becomes the field description"
# Folded prices: Code + Evidence area tables drop the three price columns and
# state the shared price once under ⊕; Tests/Other keep the full shape.
python3 - "$FIX/docs/site/center/feature-gadget.html" <<'PY' && ok || bad "fold: Code/Evidence lean tables + shared-price info (see above)"
import re, sys
html = open(sys.argv[1]).read()
def section(anchor):
    i = html.find(f'id="{anchor}"')
    assert i != -1, anchor
    j = html.find('class="sechead"', i + 1)
    return html[i:j if j != -1 else len(html)]
code, ev = section("sec-code-actions"), section("sec-ev-actions")
for name, sec in (("code", code), ("evidence", ev)):
    assert "Cost / run after" not in sec, f"{name}: price column survived"
    assert "Shared price for every move here" in sec, f"{name}: shared price missing from info"
assert "Cost / run after" in html, "full-shape tables (Tests/Other) lost their price columns"
PY
# Model-insight lens (operator ruling 2026-07-23): icon tags, filter chips,
# two-bar usage, candidates table, archmap serialization.
python3 - "$FIX" <<'PY' && ok || bad "model insight: page + archmap signals (see above)"
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
html = (root / "docs/site/center/feature-gadget.html").read_text()
assert 'id="dm-chips"' in html, "filter chips missing"
assert html.count('class="tag ic') >= 6, "icon chips missing"
assert 'title="base class' in html, "base tag missing (GadgetOut is base)"
# R10 (2026-08-04): the center REPORTS evidence and never ASSERTS deadness.
# The orphan chip was ~94% false positive on both twins because `refs` was a
# bare-name regex over the config-adopted files only — it measured how little
# the config maps, not how much code is dead. Chip and filter both gone.
# MUTATION (two lines, because the flag has no compute site left to read):
# restore `c["orphan"] = c["usage"] == 0 and c["internal"] == 0` at the tail
# of model_insight()'s first loop, and `if c["orphan"]: out += itag("t-orph",
# …)` in _ins_tags() — GadgetIn is zero on both axes, so it fires.
assert 'title="orphan' not in html, "R10: the orphan chip must be GONE"
# MUTATION: put ("t-orph", "orphan") back in the dm-chips tuple list.
assert 'data-f="t-orph"' not in html, "R10: the orphan filter chip must be GONE"
assert "u-int" in html and "ubar" in html, "two-bar usage missing"
assert "Data-model candidates" in html, "candidates table missing"
# The repurposed basis (R10 part 2): field-name Jaccard and field count are
# CORPUS-COMPLETE — GadgetOut ≈ GadgetIn at 100% and GadgetBlob at 16 fields
# stay true whatever lives outside the map, which a single unmapped caller
# would have falsified for "nothing references this". SCOPED to the section:
# the functions half of the same page also ships merge and split rows, and an
# unscoped `in html` would let sprawler vouch for GadgetBlob.
_mc = html[html.find('id="sec-code-model-cands"'):html.find('id="sec-code-fns"')]
assert _mc, "the dm candidates section must precede the functions section"
# MUTATION: raise _MERGE_FLOOR above 1.0 — the 100% pair stops qualifying.
assert 'title="merge candidate"' in _mc \
    and "GadgetIn</code> ≈ <code>GadgetOut" in _mc, \
    "the twin pair must be a MERGE candidate"
# MUTATION: raise _GOD_FIELDS to 20 — GadgetBlob's 16 fields stop qualifying.
assert 'title="split candidate"' in _mc and "past the 15-field" in _mc, \
    "a 16-field class must yield a SPLIT candidate"
# MUTATION: restore the `if c and c["orphan"]:` loop in the dm candidates
# builder — GadgetIn and GadgetBlob both re-enter as deprecation rows.
assert "deprecation candidate" not in _mc and "file for removal" not in _mc, \
    "R10: no surface may nominate a class for deletion on absent references"
assert "What the candidate icons mean" in html, "candidates icon dictionary missing"
assert "Insight icons" in html, "section icon dictionary missing"
assert '<ul class="iclist">' in html, "icon dictionary must render as a LIST"
assert "<span>Entity</span>" in html, "consolidated tables need the Entity column"
assert "<span>Touched by</span>" not in html and "<span>Used by</span>" not in html, \
    "touched-by/used-by columns must move into the row detail"
assert "dm-meta" in html, "row detail must lead with the metadata block"
assert "Usage by API" in html and "Usage by internal" in html, \
    "usage facts must render as TITLED tables in the detail"
assert 'class="dmh"' in html, "detail subsections need their iconed titles"
assert "Structure" in html and html.count('class="dmh"') >= 3, \
    "structure needs its own titled block"
assert "the teal bar is empty" in html or "<th>Endpoint</th>" in html, \
    "api usage table (or its honest-empty line) must render"
assert "the violet bar is empty" in html or "<th>Referencing function(s)</th>" in html, \
    "internal usage table (or its honest-empty line) must render"
# The FUNCTIONS lens (sibling section)
assert 'id="sec-code-fns"' in html, "functions section missing"
assert 'id="fn-chips"' in html, "functions filter chips missing"
fn_i = html.find('id="sec-code-fns"')
fns_html = html[fn_i:]
assert "make_gid" in fns_html and "sprawler" in fns_html, "fixture defs must list"
assert 'title="base — calls no other documented function"' in fns_html, \
    "make_gid must wear the base tag"
assert 'id="sec-code-model-cands"' in html and 'id="sec-code-fn-cands"' in html, \
    "both candidates sections need their own anchored secheads"
assert html.count("What the candidate icons mean") >= 2, \
    "both candidates sections need their icon dictionary in the section info"
assert "Function candidates" in fns_html, "function candidates section missing"
# The repurposed FUNCTION candidates (R10 part 2): MERGE = body-identifier
# Jaccard past _FN_MERGE_FLOOR, SPLIT = length past _FN_GOD_LINES. Both are
# corpus-complete: the collate pair being 89% alike is a fact about the two
# defs, not a claim about everything the map never read.
_fc = fns_html[fns_html.find('id="sec-code-fn-cands"'):]
# MUTATION: raise _FN_MERGE_FLOOR to 0.95 — the pair sits at 0.89 and the
# merge row disappears from the table.
assert "collate_gadget_alpha</code> ≈ <code>collate_gadget_beta" in _fc \
    and "identifier twin" in _fc, \
    "the 89% near-duplicate pair must be a MERGE candidate"
# MUTATION: raise _FN_GOD_LINES to 60 — sprawler's 54 lines stop qualifying.
assert "sprawler" in _fc and "past the 50-line" in _fc, \
    "the 54-line def must be a SPLIT candidate"
# MUTATION: restore the `if c["orphan"]:` loop in the fn candidates builder —
# lonely_helper (and six others) re-enter as deprecation rows.
assert "deprecation candidate" not in _fc and "file for removal" not in _fc, \
    "R10: no surface may nominate a function for deletion on absent callers"
assert "52" in fns_html or "53" in fns_html, "sprawler god-length must show"
assert "Signature" in fns_html and "Calls" in fns_html, \
    "detail needs Calls + Signature titled blocks"
fi = json.loads((root / "docs/site/center/archmap.json").read_text())["function_insight"]
mg = fi["src/funcs.py::make_gid"]
# The EVIDENCE survives the verdict's removal — usage/api/internal are facts
# other surfaces read (the guard lens prices `hot` off usage), so they are
# pinned here against a refactor that drops them alongside the flag.
# MUTATION: add "usage" (or "api") to the excluded keys in fn_insight_serial()
# — the pages still render and this KeyErrors, which is the whole point of
# pinning the SERIALIZED record and not just the rendered surface.
assert mg["base"] and mg["internal"] >= 1, mg
assert (mg["usage"], mg["api"]) == (0, 0), mg
lh = fi["src/funcs.py::lonely_helper"]
# MUTATION: restore `c["orphan"] = not c["handler"] and not refs` at the tail
# of function_insight() — lonely_helper is exactly the shape that set it True.
assert "orphan" not in lh, f"R10: function_insight must carry no orphan verdict: {lh}"
assert (lh["usage"], lh["api"], lh["internal"]) == (0, 0, 0), lh
assert not any("orphan" in c for c in fi.values()), \
    "R10: not one function record may carry the flag"
assert fi["src/funcs.py::sprawler"]["god"]
# The merge page's own input, pinned in the RECORD: a row can render from an
# in-memory value the archmap never carries, and the census consumers read
# the file. MUTATION: add "sim" to fn_insight_serial()'s excluded keys — the
# candidates table still renders and this KeyErrors.
_tw = fi["src/funcs.py::collate_gadget_alpha"]["sim"]
assert _tw["cls"] == "collate_gadget_beta" and _tw["j"] >= 0.85, _tw
# in/out dialect + linked references (entity-icons round)
assert fi["src/funcs.py::emit_gadget"]["returns"] == "GadgetDraft"
assert 'class="tag t-io"' in html, \
    "GadgetDraft's referencing fn must wear in·out (param AND return)"
assert "<i>returns</i>" in html and 'class="tag t-out"' in html, \
    "Signature must state the return with its out role"
assert 'class="tag t-in"' in html, "params must carry the in role"
# to-be-designed pending links (app-internal import, documented nowhere)
assert 'class="tag ic t-tbd"' in html, \
    "PendingThing must render the to-be-designed pending link"
assert "AsyncSession" not in html or 't-tbd">tbd</span></a>' in html  # sanity
# endpoints + code map row details (the dm dialect everywhere)
assert "MODELS USED" not in html or "PURPOSE" in html
assert "FUNCTIONS DEFINED" in html and "CLASSES DEFINED" in html, \
    "code-map details must split defines into linked functions/classes"
assert "<span>Defines</span>" not in html, \
    "the Defines column must move into the row detail"
assert "BUDGET" in html, "code-map detail needs the budget row"
a = json.loads((root / "docs/site/center/archmap.json").read_text())
mi = a["model_insight"]
assert mi["GadgetOut"]["base"], mi["GadgetOut"]
assert mi["GadgetOut"]["internal_refs"][0]["file"] == "src/api.py", \
    "endpoint handler must appear as a usage receipt"
# MUTATION: restore `c["orphan"] = c["usage"] == 0 and c["internal"] == 0` at
# the tail of the first model_insight() loop — GadgetIn sets it True.
assert "orphan" not in mi["GadgetIn"], f"R10: no orphan verdict: {mi['GadgetIn']}"
assert not any("orphan" in c for c in mi.values()), \
    "R10: not one model record may carry the flag"
# The evidence the verdict was built from SURVIVES it, unrenamed: usage is
# still endpoint touches + FK in-degree, internal still counts referencing
# mapped files. Pinned on both a used and an unused class — GadgetIn's (0, 0)
# is exactly what used to read `orphan`, and it must now read as two numbers
# and no verdict.
# MUTATION: add "usage" (or "internal") to insight_serial()'s excluded keys.
assert (mi["GadgetOut"]["usage"], mi["GadgetOut"]["internal"]) == (3, 1), \
    mi["GadgetOut"]
assert (mi["GadgetIn"]["usage"], mi["GadgetIn"]["internal"]) == (0, 0), \
    mi["GadgetIn"]
assert mi["GadgetOut"]["sim"]["cls"] == "GadgetIn" and mi["GadgetOut"]["sim"]["j"] == 1.0
assert mi["GadgetIn"]["kind"] == "schema"
# MUTATION: raise _GOD_FIELDS to 20 — the 16-field class stops being god.
assert mi["GadgetBlob"]["god"] and not mi["GadgetOut"]["god"], mi["GadgetBlob"]
PY

# R10, estate-wide (design record §5, 2026-08-04): "the command center REPORTS
# evidence and never ASSERTS deadness. A surface may say 'no indexed callers —
# go check'; it may never say 'orphan'." The fixture is built to be the WORST
# case for this: lonely_helper, GadgetIn, GadgetBlob and six other defs are all
# zero on every reference axis, so every deleted render site has a live input.
# Scoped to the pages + the archmap — a3.css may keep a dead .t-orph rule
# (colors are shell vocabulary, not a claim), and that is not a verdict.
python3 - "$FIX/docs/site/center" <<'PY' && ok || bad "R10: no page may assert deadness (see above)"
import sys
from pathlib import Path
c = Path(sys.argv[1])
pages = sorted(c.glob("*.html")) + [c / "archmap.json"]
assert len(pages) > 12, f"only {len(pages)} surfaces swept — did the build run?"
# MUTATION: restore EITHER `c["orphan"] = …` compute site on its own —
# archmap.json is swept too, so the key alone trips this before any page does;
# add a render site (_ins_tags · _fn_tags · either candidates loop) and a
# rendered page carries the word as well.
banned = ("orphan", "true orphan", "deprecation candidate", "t-orph",
          "file for removal", "zero on both usage axes")
for p in pages:
    text = p.read_text()
    for word in banned:
        assert word not in text, f"{p.name} still says {word!r}"
print(f"{len(pages)} surfaces swept clean")
# The honesty the repurposed pages OWE their reader, on both of them. These
# three sentences are the argument for the new basis; a page that keeps the
# tables and drops them is back to asserting more than it knows.
# MUTATION: delete the "The floor, stated honestly" paragraph from either
# candidates sechead's info block in _a3_code.py.
for _pg in ("arch-fn-candidates.html", "arch-dm-candidates.html"):
    t = (c / _pg).read_text()
    assert "CORPUS-COMPLETE" in t, f"{_pg}: the basis argument is missing"
    assert "FLOOR, not a census" in t, f"{_pg}: the under-report must be owned"
    assert "TOP-1" in t and "outside the entity config" in t, \
        f"{_pg}: the floor's scope + its blind spot must be stated"
print("both candidate pages state their floor")
PY
# The compute sites themselves, and every consumer that subscripts them. A
# previous run of this migration deleted both `c["orphan"] = …` assignments
# while three `if c["orphan"]:` reads stayed live: it parsed, and it would
# have KeyError'd at build time. ast.parse cannot see that; this can.
# MUTATION: re-add `c["orphan"] = not c["handler"] and not refs` to
# _a3_code.py and the first grep fires.
(cd "$GEN" && python3 - <<'PY'
import re, sys
from pathlib import Path
gen = Path(".")
hits = []
for p in sorted(gen.glob("*.py")):
    for n, line in enumerate(p.read_text().splitlines(), 1):
        if re.search(r'\["orphan"\]|\.get\("orphan"\)|"orphan_unguarded"'
                     r'|"cls_orphan"', line):
            hits.append(f"{p.name}:{n}: {line.strip()}")
assert not hits, "surviving orphan compute/read:\n" + "\n".join(hits)
sys.path.insert(0, ".")
import _a3_code as C
# MUTATION: put the "orphan" key back in _INS_ICONS — the icon is the chip's
# other half, and a live icon is how the chip comes back by accident.
assert "orphan" not in C._INS_ICONS, "the orphan icon entry must be gone"
# ... while the floors the repurposed pages now stand on are still named.
assert C._FN_SIM_FLOOR == 0.6 and C._FN_GOD_LINES == 50, "fn floors moved"
assert C._SIM_FLOOR == 0.5 and C._GOD_FIELDS == 15, "dm floors moved"
print("generators clean · floors intact")
PY
) >"$T/r10.out" 2>&1 && ok || { bad "R10: no generator may compute or read the flag"; cat "$T/r10.out"; }

# ── per-router prefix (review 2026-09-05): a file mounting TWO routers labels each handler by ITS router's prefix ──
( cd "$GEN" && python3 - "$T" <<'PY'
import sys, tempfile
from pathlib import Path
sys.path.insert(0, ".")
import _a3_code as C
root = Path(tempfile.mkdtemp(dir=sys.argv[1])); (root / "src").mkdir()
(root / "src" / "two.py").write_text(
    'router = APIRouter(prefix="/groups")\n'
    'invites_router = APIRouter(prefix="/invites")\n'
    'stray = APIRouter()\n'
    '@router.get("/{gid}")\ndef one(): return 1\n'
    '@invites_router.post("/{token}/accept")\ndef two(): return 2\n'
    '@stray.get("/loose")\ndef three(): return 3\n'
    '@app.get("/raw")\ndef four(): return 4\n')
eps = {e["fn"]: e["path"] for e in C.parse_endpoints(root, ["src/two.py"])}
assert eps["one"] == "/groups/{gid}", eps             # FIRE: the pre-review rule (last prefix wins) labeled this /invites/{gid}
assert eps["two"] == "/invites/{token}/accept", eps
assert eps["three"] == "/loose", eps                   # a router declared WITHOUT a prefix keeps none, whatever its siblings declare
assert eps["four"] == "/invites/raw", eps              # an object the scan cannot name falls back to the file's last prefix (the unchanged rule)
(root / "src" / "one.py").write_text('router = APIRouter(prefix="/gadgets")\n@router.get("/x")\ndef gx(): return 1\n')
assert {e["path"] for e in C.parse_endpoints(root, ["src/one.py"])} == {"/gadgets/x"}   # SILENT: a single router reads exactly as before
print("per-router prefix ok")
PY
) >"$T/prefix.out" 2>&1 && ok || { bad "per-router prefix: each handler wears ITS router's prefix"; cat "$T/prefix.out"; }

# ── PASS 1 · foreign-repo resilience (review 2026-09-06, repo-study): SQLModel tables · router mount chain ·
#    Annotated alias + factory Depends · config globs · unparseable-file signal. FIRE + SILENT each. ──
( cd "$GEN" && python3 - "$T" <<'PY'
import sys, tempfile
from pathlib import Path
sys.path.insert(0, ".")
import _a3_code as C
root = Path(tempfile.mkdtemp(dir=sys.argv[1]))
# 1 · SQLModel `table=True` is a table (name = class lowercased); a base without it is not; __tablename__ wins
(root / "m.py").write_text(
    "class UserBase(SQLModel):\n    email: str\n"
    "class User(UserBase, table=True):\n    id: int\n"
    "class Item(SQLModel, table=True):\n    __tablename__ = 'items_t'\n    id: int\n"
    "class Plain(Base):\n    id: int\n")
tabs = dict(C._table_classes(C._safe_parse(root / "m.py")[0]))
assert tabs == {"User": "user", "Item": "items_t"}, tabs                       # FIRE: the __tablename__-only rule saw ZERO tables here
ms = {m["cls"]: m["table"] for m in C.parse_models(root, ["m.py"], None)}
assert ms.get("User") == "user" and ms.get("Item") == "items_t" and "UserBase" not in ms and "Plain" not in ms, ms
# 2 · the app → include_router chain: mount prefixes resolve through imports; /api/vN is stripped; non-literal is NAMED
(root / "app").mkdir(); (root / "app" / "__init__.py").write_text("")
(root / "app" / "api").mkdir(); (root / "app" / "api" / "__init__.py").write_text("")
(root / "app" / "api" / "routes").mkdir(); (root / "app" / "api" / "routes" / "__init__.py").write_text("")
(root / "app" / "main.py").write_text(
    "from app.api.main import api_router\nfrom app.api.routes import health\n"
    "app = FastAPI()\napp.include_router(api_router, prefix='/api/v1')\napp.include_router(health.router)\n")
(root / "app" / "api" / "main.py").write_text(
    "from app.api.routes import login, users\nfrom app.api.routes.items import router as items_router\n"
    "api_router = APIRouter()\napi_router.include_router(login.router)\n"
    "api_router.include_router(users.router, prefix='/users')\napi_router.include_router(items_router, prefix=settings.ITEMS)\n")
(root / "app" / "api" / "routes" / "login.py").write_text("router = APIRouter(prefix='/login')\n@router.post('/access-token')\ndef login(): return 1\n")
(root / "app" / "api" / "routes" / "users.py").write_text("router = APIRouter()\n@router.get('/{user_id}')\ndef read(): return 1\n")
(root / "app" / "api" / "routes" / "items.py").write_text("router = APIRouter()\n@router.get('/')\ndef items(): return 1\n")
(root / "app" / "api" / "routes" / "health.py").write_text("router = APIRouter()\n@router.get('/healthz')\ndef hz(): return 1\n")
C._MOUNTS.clear()
files = ["app/api/routes/login.py", "app/api/routes/users.py", "app/api/routes/items.py", "app/api/routes/health.py"]
eps = {e["fn"]: e["path"] for e in C.parse_endpoints(root, files)}
assert eps["login"] == "/login/access-token", eps            # own prefix under a stripped /api/v1 mount
assert eps["read"] == "/users/{user_id}", eps                # FIRE: the leaf-only rule labeled this /{user_id}
assert eps["items"] == "/", eps                              # a non-literal include prefix contributes "" — never a guess
assert eps["hz"] == "/healthz", eps                          # mounted on the app directly — untouched
st = C.mount_stats(root)
assert st["mounted"] >= 2 and any("non-literal prefix: settings.ITEMS" in u["why"] for u in st["unresolved"]), st
# 3 · Annotated alias (imported) + factory Depends callee
(root / "app" / "deps.py").write_text("CurrentUser = Annotated[dict, Depends(get_current_user)]\n")
(root / "app" / "api" / "routes" / "me.py").write_text(
    "from app.deps import CurrentUser\nrouter = APIRouter()\n"
    "@router.get('/me', dependencies=[Depends(require_permission(Perm.ADMIN))])\ndef me(user: CurrentUser): return 1\n")
C._MOUNTS.clear(); C._ALIASES.clear()
mw = {m["name"]: m for m in C.parse_endpoints(root, ["app/api/routes/me.py"])[0]["middleware"]}
assert "get_current_user" in mw and mw["get_current_user"]["gate"], mw          # FIRE: a bare-Name alias annotation drew nothing
fac = mw.get("require_permission(Perm.ADMIN)")
assert fac and fac.get("callee") == "require_permission" and fac["gate"], mw   # the factory's leaf resolves; the display name stays exact
# 4 · config globs expand (recursive **), literals pass through
(root / "mods").mkdir(); (root / "mods" / "a").mkdir(); (root / "mods" / "b").mkdir(); (root / "mods" / "b" / "deep").mkdir()
for f in ("a/routes.py", "b/routes.py", "b/deep/routes.py"): (root / "mods" / f).write_text("router = APIRouter()\n")
assert C._expand_globs(root, ["mods/*/routes.py"]) == ["mods/a/routes.py", "mods/b/routes.py"]
assert C._expand_globs(root, ["mods/**/routes.py"]) == ["mods/a/routes.py", "mods/b/deep/routes.py", "mods/b/routes.py"]
assert C._expand_globs(root, ["mods/a/routes.py", "nope.py"]) == ["mods/a/routes.py", "nope.py"]   # SILENT: literals untouched
# 5 · an unparseable file is NAMED, not silently skipped
(root / "bad.py").write_text("def broken(:\n    pass\n")
C._UNPARSEABLE.clear(); C._safe_parse(root / "bad.py")
assert any("bad.py" in k and "syntax error" in v for k, v in C.unparseable_files()), C.unparseable_files()
# 5b · a NEWER-Python spelling (PEP 758 `except A, B:` — tier0 requires 3.14) parses through the shim; a real error still does not
(root / "new.py").write_text("def f():\n    try:\n        pass\n    except ValueError, KeyError:\n        raise\n")
C._UNPARSEABLE.clear(); t, _ = C._safe_parse(root / "new.py")
assert t is not None and not C.unparseable_files(), C.unparseable_files()   # FIRE: the plain 3.12 parse rejects this line
print("pass-1 resilience ok")
PY
) >"$T/pass1.out" 2>&1 && ok || { bad "pass 1: SQLModel tables · mount chain · alias/factory Depends · globs · unparseable"; cat "$T/pass1.out"; }

# M04: the single-file set's href carries NO set-name segment.
grep -q 'proof/solo.png"' "$FIX/docs/site/center/feature-gadget.html" \
  && ok || bad "single-file set: href must be proof-root relative"
grep -q 'proof/solo/solo.png' "$FIX/docs/site/center/feature-gadget.html" \
  && bad "single-file set: minted a dead <set>/<file> href (M04 regression)" || ok

# D123 unknown-slug abort.
D123="$T/d123"; mk_fixture "$D123"
python3 - "$D123" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1]) / "docs/site/center/center.config.json"
cfg = json.loads(p.read_text())
cfg["entities"]["bogus"] = {"test_rx": "bogus"}
p.write_text(json.dumps(cfg))
PY
[ "$(build "$D123" "$SHELL_SRC")" != 0 ] && ok || bad "D123: unknown config slug must abort"
grep -q "not entities in adoption.json" "$T/build.out" && ok || bad "D123: abort names the registry"

# Lens-card completeness abort.
CARD="$T/card"; mk_fixture "$CARD"
sed -i '/# DECIDED/,$d' "$CARD/docs/site/center/cards/gadget.md"
[ "$(build "$CARD" "$SHELL_SRC")" != 0 ] && ok || bad "card: missing required section must abort"
grep -q "missing section" "$T/build.out" && ok || bad "card: abort names the missing section"

# Shell missing → exit 2.
[ "$(build "$FIX" "$T/no-such-shell")" = 2 ] && ok || bad "shell missing must exit 2"

# a3.css without .xtbl → exit 3.
BROKEN="$T/shell-broken"; cp -a "$SHELL_SRC" "$BROKEN"
python3 - "$BROKEN/assets/a3.css" <<'PY'
import sys
from pathlib import Path
p = Path(sys.argv[1])
p.write_text(p.read_text().replace(".xtbl", ".gone"))
PY
XFIX="$T/xfix"; mk_fixture "$XFIX"
[ "$(build "$XFIX" "$BROKEN")" = 3 ] && ok || bad "a3.css without .xtbl must exit 3"

# M05: malformed FLOWS lines surface as a build warning, never vanish.
M5="$T/m5"; mk_fixture "$M5"
sed -i 's/- manual → typed entry path/- manual entry with no arrow/' \
  "$M5/docs/site/center/cards/gadget.md"
[ "$(build "$M5" "$SHELL_SRC")" = 0 ] && ok || bad "m5: malformed FLOWS still builds"
grep -q "FLOWS line(s) did not parse" "$T/build.out" && ok || bad "m5: build must WARN on malformed FLOWS"
grep -q "FLOWS line(s) did not parse" "$M5/docs/site/center/feature-gadget.html" \
  && ok || bad "m5: the page's coverage note must carry the malformed count"

# --- crawl gate: SILENT + every FIRE --------------------------------------
[ "$(gate "$FIX")" = 0 ] && ok || { bad "gate: clean center must pass"; cat "$T/gate.out"; }
grep -q " 0 dead" "$T/gate.out" && ok || bad "gate: clean center reports 0 dead"
grep -q "to-be-designed reference" "$T/gate.out" \
  && ok || bad "gate: the pending-links sweep must WARN on t-tbd references"

# --- FK-target links (gastify 2026-09-04): a relationship() whose target has NO card on any page and
#     no home entity (an app type outside the mapped tree — gastify's `User`) rendered a same-page
#     anchor that did not exist → 2 dead links, regen failed closed. Now: card → its anchor · another
#     entity's class → that page · neither → the to-be-designed reference. Separate mini-fixture so the
#     main fixture's pinned counts never shift. MUTATION: restore the unconditional `_anchor(slug, target)`
#     link in _a3_code.rel_rows → the gate reports 1 dead and the tbd grep fails.
RELFIX="$T/relfix"; mk_fixture "$RELFIX"
cat > "$RELFIX/src/models.py" <<'PYM'
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Widget(Base):
    __tablename__ = "widgets"
    id: Mapped[int] = mapped_column(primary_key=True)


class Gadget(Base):
    __tablename__ = "gadgets"
    id: Mapped[int] = mapped_column(primary_key=True)
    widget_id: Mapped[int] = mapped_column(ForeignKey("widgets.id"))
    widget: Mapped["Widget"] = relationship("Widget")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    owner: Mapped["User"] = relationship("User", back_populates="gadgets")
PYM
python3 - "$RELFIX/docs/site/center/center.config.json" <<'PY2'
import json, sys
p = sys.argv[1]; cfg = json.load(open(p)); cfg["entities"]["gadget"]["code"]["models"] = ["src/models.py"]
json.dump(cfg, open(p, "w"), indent=1)
PY2
[ "$(build "$RELFIX" "$SHELL_SRC")" = 0 ] && ok || { bad "relfix: a model file with an undocumented FK target must still build"; tail -5 "$T/build.out"; }
[ "$(gate "$RELFIX")" = 0 ] && ok || { bad "relfix gate: an undocumented FK target must not be a dead anchor"; grep "dead\|✗" "$T/gate.out" | head -3; }
grep -q " 0 dead" "$T/gate.out" && ok || bad "relfix gate: 0 dead"
RELDM="$RELFIX/docs/site/center/arch-data-model.html"
grep -q '>User<span class="tag ic t-tbd">tbd</span></a>' "$RELDM" \
  && ok || bad "relfix: the undocumented target (User) must render as the to-be-designed reference"
grep -q 'id="dm-app-Widget"' "$RELDM" && grep -q 'href="[^"]*#dm-app-Widget">Widget</a>' "$RELDM" \
  && ok || bad "relfix SILENT: a documented target (Widget) keeps its real anchor"

# Dead internal href → exit 1.
DEAD="$T/dead"; mk_fixture "$DEAD"
build "$DEAD" "$SHELL_SRC" >/dev/null
echo '<a href="nope-missing.html">x</a>' >> "$DEAD/docs/site/center/index.html"
[ "$(gate "$DEAD")" = 1 ] && ok || bad "gate: dead internal href must exit 1"

# Duplicate ids are DEAD (review H1): the set-based anchor check is blind to
# them, so the gate counts occurrences per page.
DUP="$T/dup"; mk_fixture "$DUP"
build "$DUP" "$SHELL_SRC" >/dev/null
printf '<i id="dm-chips"></i>' >> "$DUP/docs/site/center/feature-gadget.html"
[ "$(gate "$DUP")" = 1 ] && ok || bad "gate: a duplicated id must FAIL the crawl"
grep -q "duplicate id" "$T/gate.out" && ok || bad "gate: dup-id failure names itself"
# …and stays SILENT on script-literal / non-id-attribute look-alikes (the
# Levels page carries `var id="cls:"` + `rid="cls:"` in JS — not DOM ids).
JSD="$T/jsdup"; mk_fixture "$JSD"
build "$JSD" "$SHELL_SRC" >/dev/null
printf '<script>var id="dm-chips"; var rid="dm-chips"; var cid="dm-chips";</script><b data-id="dm-chips"></b>' \
  >> "$JSD/docs/site/center/feature-gadget.html"
[ "$(gate "$JSD")" = 0 ] && ok || { bad "gate: JS literals + data-id must NOT count as duplicate ids"; cat "$T/gate.out"; }
# File-qualified fn anchors (H1): same-named defs in different files can't collide.
grep -q 'id="fn-gadget-src-funcs-py-make-gid"' "$FIX/docs/site/center/feature-gadget.html" \
  && ok || bad "fn anchors must carry the defining file"

# Estate (../) ref probed on disk → missing target is DEAD, not exempt (M04).
EST="$T/est"; mk_fixture "$EST"
build "$EST" "$SHELL_SRC" >/dev/null
echo '<a href="../../../tests/web-e2e/proof/never.png">x</a>' >> "$EST/docs/site/center/index.html"
[ "$(gate "$EST")" = 1 ] && ok || bad "gate: missing estate target must exit 1"
grep -q "estate target missing" "$T/gate.out" && ok || bad "gate: estate probe names its finding"

# paths.center override honored end to end (M02: no hardcoded center path).
PANEL="$T/panel"; mk_fixture "$PANEL" "docs/site/panel"
[ "$(build "$PANEL" "$SHELL_SRC")" = 0 ] && ok || bad "panel: paths.center build"
[ -f "$PANEL/docs/site/panel/index.html" ] && ok || bad "panel: pages land under paths.center"
[ "$(gate "$PANEL")" = 0 ] && ok || bad "gate: must crawl the CONFIGURED center dir"
grep -q " 0 pages" "$T/gate.out" && bad "gate: crawled the hardcoded default instead of paths.center (M02 regression)" || ok

# Empty crawl → refuse the vacuous pass (M02).
EMPTY="$T/empty"; mkdir -p "$EMPTY"
[ "$(gate "$EMPTY")" = 1 ] && ok || bad "gate: 0 pages must exit 1, not pass green"
grep -q "refusing the vacuous pass" "$T/gate.out" && ok || bad "gate: empty crawl says why it failed"

# --- refresh driver wiring (M01) — stubbed builders isolate the shell logic -
RF="$T/rf"; mkdir -p "$RF/scripts" "$RF/docs/site/center"
cp "$GEN/refresh_center.sh" "$RF/scripts/"
cat > "$RF/scripts/build_center_a3.py" <<'PY'
open("gates-ran.marker", "w").write("build")
print("stub build")
PY
cat > "$RF/scripts/check_center_links.py" <<'PY'
print("stub gate")
PY
cat > "$RF/docs/site/center/center.config.json" <<'JSON'
{"commands": {"junit": ["echo capture-ran"], "coverage": ["echo cov-ran"],
              "e2e": ["echo e2e-ran"]}}
JSON
run_rf() { (cd "$RF" && bash scripts/refresh_center.sh "$@" >"$T/rf.out" 2>&1; echo $?); }

rm -f "$RF/gates-ran.marker"
[ "$(run_rf junit)" = 0 ] && ok || bad "refresh junit: must exit 0 (M01: was exit 1 before the gates)"
grep -q "capture-ran" "$T/rf.out" && ok || bad "refresh junit: capture ran"
[ -f "$RF/gates-ran.marker" ] && ok || bad "refresh junit: regenerate+gates block must be REACHED (M01)"

rm -f "$RF/gates-ran.marker"
[ "$(run_rf all)" = 0 ] && ok || bad "refresh all: must exit 0"
grep -q "cov-ran" "$T/rf.out" && grep -q "e2e-ran" "$T/rf.out" \
  && ok || bad "refresh all: must not die after the first group (M01)"
[ -f "$RF/gates-ran.marker" ] && ok || bad "refresh all: gates reached"

# No-commands group: says so, still reaches the gates.
cat > "$RF/docs/site/center/center.config.json" <<'JSON'
{"commands": {}}
JSON
rm -f "$RF/gates-ran.marker"
[ "$(run_rf junit)" = 0 ] && ok || bad "refresh junit(no cmds): exit 0"
grep -q "no commands declared" "$T/rf.out" && ok || bad "refresh junit(no cmds): says so"
[ -f "$RF/gates-ran.marker" ] && ok || bad "refresh junit(no cmds): gates reached"

[ "$(run_rf bogus-mode)" = 2 ] && ok || bad "refresh: unknown mode must exit 2"

# --- render/consume wiring (M19 Decisions · M40 coverage · M38 · M30) ------
DEP="$T/dep"; mk_fixture "$DEP"
mkdir -p "$DEP/.kdbp" "$DEP/tests/results"
cat > "$DEP/.kdbp/DEPLOYMENTS.md" <<'MD'
| # | Date | Branch → Target | PR | CI result | Notes | Decisions |
|---|------|-----------------|----|-----------|-------|-----------|
| d0 | 2026-07-21 | main → staging | — | green | first |
| d1 | 2026-07-22 | main → prod | PR#5 | green | notes here | D42 chose the estate probe |
MD
python3 - "$DEP" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1]) / "docs/site/center/center.config.json"
cfg = json.loads(p.read_text())
cfg["coverage"] = {"api": {"json": "tests/results/api-coverage.json"}}
p.write_text(json.dumps(cfg))
(Path(sys.argv[1]) / "tests/results/api-coverage.json").write_text(
    json.dumps({"totals": {"percent_covered": 78.31}}))
PY
[ "$(build "$DEP" "$SHELL_SRC")" = 0 ] && ok || bad "dep: wired fixture builds"
grep -q 'D42 chose the estate probe' "$DEP/docs/site/center/releases.html" \
  && ok || bad "M19: the Decisions column must render on the releases station"
grep -q '78.3% api' "$DEP/docs/site/center/tests.html" \
  && ok || bad "M40: a wired coverage reporter must ride the Testing KPI row"
# Silent halves on the plain fixture: no reporter -> named gap; no 7th column
# -> no decisions cell invented.
grep -q 'no reporter wired' "$FIX/docs/site/center/tests.html" \
  && ok || bad "M40: no reporter must stay the honest named gap"
# Entity icons: semantic keyword match first, hash pool only as fallback.
(cd "$GEN" && python3 -c "
import _a3_render as R
assert R.entity_glyph_name('transaction') == 'card'
assert R.entity_glyph_name('allergen') == 'alert'
assert R.entity_glyph_name('card-alias') == 'tag'   # alias beats card — order
assert R.entity_glyph_name('auth') == 'lock'
assert R.entity_glyph_name('zzz-mystery') == ''      # fallback path
assert '<svg' in R.entity_icon('zzz-mystery')
") && ok || bad "entity icons: semantic map must fit the twins' vocabulary"

# Architecture ESTATE (2026-07-23): a dashboard + six subpages, each running
# its entity-dialect section app-wide with the entity filter bar + icon-only
# entity column; nav lists every subpage.
python3 - "$FIX/docs/site/center" <<'PY2' && ok || bad "architecture estate: dashboard + six subpages (see above)"
import sys
from pathlib import Path
c = Path(sys.argv[1])
dash = (c / "architecture.html").read_text()
assert "archgrid" in dash and 'href="arch-endpoints.html"' in dash, "dashboard cards missing"
assert 'id="sec-code-endpoints"' not in dash, "dashboard must not inline the sections"
pages = {"arch-endpoints.html": "sec-code-endpoints",
         "arch-code-map.html": "sec-code-map",
         "arch-data-model.html": "sec-code-model",
         "arch-dm-candidates.html": "sec-code-model-cands",
         "arch-functions.html": "sec-code-fns",
         "arch-fn-candidates.html": "sec-code-fn-cands"}
for fname, anchor in pages.items():
    h = (c / fname).read_text()
    assert f'id="{anchor}"' in h, f"{fname}: missing {anchor}"
    assert 'class="entchips"' in h, f"{fname}: entity filter bar missing"
    assert "navsubitem" in h, f"{fname}: nav subpages missing"
    # Round 21: the architecture estate carries the same sticky menu the
    # testing estate does — overview + siblings, current marked, stacked
    # with the entity bar as ONE sticky unit.
    assert f'class="on" href="{fname}"' in h \
        and 'href="architecture.html"' in h, f"{fname}: estate menu missing"
    assert 'class="stickstack"' in h, f"{fname}: menu+bar must stack sticky"
# R10 dry-run catch (gustify COPY, 2026-08-05): the dashboard badge must
# count EXACTLY the rows its page renders. When the candidates pages were
# repurposed off the orphan flag, the badge kept a looser selector
# (`c.get("sim")`, i.e. the lower COMPUTE floor, pairs double-counted) and
# advertised 88 candidates over a 30-row page — a number the reader cannot
# reconcile, which is the same overclaim R10 removed.
# MUTATION: in build_center_a3.py restore
# `n_dmc = sum(1 for c in ins.values() if c.get("god") or c.get("sim"))`
# — the fixture's GadgetIn/GadgetOut pair is recorded on both sides, so the
# badge reads one higher than the table.
for fname, anchor in (("arch-dm-candidates.html", "sec-code-model-cands"),
                      ("arch-fn-candidates.html", "sec-code-fn-cands")):
    h = (c / fname).read_text()
    body = h[h.find(f'id="{anchor}"'):]
    rows = body[body.find("<tbody>"):body.find("</tbody>")].count("<tr>")
    assert rows > 0, f"{fname}: repurposed page renders NO rows"
    import re as _re
    badge = _re.search(rf'href="{fname}"[^>]*>.*?(\d+) candidate\(s\)',
                       dash, _re.S)
    assert badge, f"{fname}: dashboard badge missing"
    assert int(badge.group(1)) == rows, \
        f"{fname}: badge says {badge.group(1)}, page renders {rows}"
    # ...and the subtitle may not advertise a row class the page cannot emit.
    assert "deprecation" not in dash, "dashboard still advertises deprecation"
h = (c / "arch-data-model.html").read_text()
assert 'class="entb ent-gadget"' in h, "icon-only entity column missing"
assert "dm-app-" in h, "app-scoped anchors missing"
# Cross-section links must route to the OWNING page — a bare same-page
# #dm-app-… anchor on the endpoints page is a dead link (gastify dry-run
# caught exactly this on 2026-07-23).
h = (c / "arch-endpoints.html").read_text()
assert 'href="arch-data-model.html#dm-app-' in h, \
    "endpoint model links must route via the xpage map"
assert 'href="#dm-app-' not in h, "unrouted same-page dm anchor on endpoints page"
# The filter must actually FIRE (2026-07-23 operator catch: the script bound
# rows before the tables existed, so clicking filtered nothing) and compose
# with the kind filter via classes, never a display-style tug-of-war.
for fname in pages:
    h = (c / fname).read_text()
    assert "classList.toggle('ehide'" in h, f"{fname}: entity filter not class-based"
    assert "var rows=[].slice.call" not in h.split("</h1>")[-1].split("sechead")[0], \
        f"{fname}: bar script must collect rows at click time, not eagerly"
h = (c / "arch-data-model.html").read_text()
assert "classList.toggle('khide'" in h, "kind filter must compose via khide"
css = (c / "assets" / "a3.css").read_text()
assert "position:sticky" in css.split(".entchips{", 1)[1].split("}")[0], \
    "the entity bar must stick while the page scrolls"
assert ".xrow.khide,.xrow.ehide" in css, "filter compose rule missing from css"
PY2

# The test↔code thread (spike ruling 2026-07-23): kind chips + tier-labeled
# receipts on code rows, from the fixture's junit + AST joins. FIRE proof:
# the endpoint chip, the handler's via-route credit, the C-id receipts, the
# named gaps (untested fn, coverage not captured), file reach, 4+ Tests cols.
python3 - "$FIX/docs/site/center/feature-gadget.html" <<'PY3' && ok || bad "thread: code rows carry kind chips + receipts (see above)"
import sys
html = open(sys.argv[1]).read()
assert 'title="integration' in html and "</svg> 1<" in html, \
    "endpoint kind chip (icon + count, no separator) missing"
assert "<b>Tests</b>" in html and "What it asserts" in html, \
    "endpoint Tests titled section with receipts table missing"
assert "<b>Models used</b>" in html, "Models-used titled section missing"
assert '<th>Model</th><th>Role</th>' in html, "MODELS USED must be a table"
assert 'l-api">' in html and "</svg> integration" in html, \
    "kind chip must carry its center-wide icon + color"
assert "via route 2" in html, \
    "handler via-route credit missing (C11 + the web file receipt)"
assert ">C11</span>" in html and ">C12</span>" in html, "C-id receipts missing"
assert "no case" in html, "untested-function gap chip missing"
assert "cov —" in html, "coverage named-gap chip missing"
assert "reach · " in html, "file reach chip missing"
assert html.count(">Tests</span>") >= 4, "Tests column missing from a table"
PY3

# The case LEDGER (rulings R1–R3 + Q1–Q6, 2026-07-24): the C-id is the row
# and the canonical anchor; dropdown filters (R2) incl. per-element datalists;
# solid T1 chips vs dashed via-file inheritance (Q1); the unminted honesty
# tag (Q2); parametrize variants grouped under their id; test-elements.html
# is the GAPS page — untested rows FIRE, tested elements stay SILENT — and
# the Shape-A element roster is gone from the entity tab.
python3 - "$FIX/docs/site/center" <<'PY4' && ok || bad "testing estate: case ledger + gaps page (see above)"
import sys
from pathlib import Path
c = Path(sys.argv[1])
dash = (c / "tests.html").read_text()
assert 'href="test-matrix.html"' in dash and "archgrid" in dash, "dashboard cards missing"
assert "Untested surface" in dash and 'href="test-elements.html"' in dash, \
    "Untested-surface card missing"
# The STATION REWORK (2026-07-25): tests.html is a single-lens dashboard —
# estate cards mirror the entity Tests tab (cases · files · claims ·
# untested + the machinery page), kinds & coverage runs app-wide, the
# entity × kind matrix keeps the grid. The old matrix/evidence/gates tab
# set is GONE, and the sidebar navsub now names the estate pages.
assert 'id="tab-tests"' not in dash and 'class="tabbar"' not in dash, \
    "the old tab set must be gone from the testing station"
assert 'href="test-files.html"' in dash, \
    "the Files card must land on its own estate page"
assert 'href="test-claims.html"' in dash and 'href="test-corpora.html"' in dash, \
    "estate cards must cover claims + the machinery page"
assert 'id="sec-tests-kinds"' in dash and "Kinds &amp; coverage" in dash, \
    "app-wide Kinds & coverage section missing"
assert "</svg> integration" in dash and "</svg> journey" in dash \
    and "</svg> deployed" in dash, "app kind rows must carry their kind chips"
assert "no reporter wired" in dash or "% " in dash, \
    "the coverage kind row must state the reporter fact"
assert 'id="sec-tests-matrix"' in dash and 'class="riskgrid"' in dash, \
    "entity × kind matrix section missing"
idx = (c / "index.html").read_text()
# The Code-group treatment (operator ruling 2026-07-24): the Testing group
# lists one icon'd navsubitem per estate PAGE — same layout as the
# Architecture subitems, same icons as the entity Tests tab sections.
for pg, lbl in (("test-matrix.html", "Cases"), ("test-files.html", "Files"),
                ("test-claims.html", "Claims"),
                ("test-elements.html", "Untested"),
                ("test-corpora.html", "Corpora &amp; gates")):
    assert f'class="navitem navsubitem" href="{pg}"' in idx \
        and f"</svg> {lbl}</a>" in idx, f"Testing navsubitem {lbl} missing"
assert 'class="navsub"><a href="test-' not in idx, \
    "the plain-text navsub is retired for the Code-group layout"
assert "tests.html#tab-" not in idx, "the old tab navsub must be gone"
# Wrap-up sweep: the hub lens tabs must not point at retired homes — the
# shelf lives on the machinery page, the old matrix/gates/angles wording
# is gone from the Tests rollup.
assert 'href="test-corpora.html#sec-tests-shelf"' in idx, \
    "the hub Evidence lens must point the shelf at its machinery home"
assert "gates and angles" not in idx and "Tests → Evidence" not in idx, \
    "stale old-station prose must be gone from the hub lenses"
co = (c / "test-corpora.html").read_text()
assert 'id="sec-tests-walks"' in co, \
    "walks need their anchored home on the machinery page (the manual kind row lands here)"
assert 'id="sec-tests-gates"' in co and 'id="sec-tests-corpora"' in co \
    and 'id="sec-tests-changelog"' in co and 'id="sec-tests-shelf"' in co, \
    "machinery-page sections must each carry a sechead anchor"
# Round 23: the machinery explains itself — corpora say WHAT they verify,
# gates say WHAT they do (curated id / the hook's own name line), and the
# demo shelf shows WHO claims each set and WHERE it lands.
assert "What it verifies" in co and "drives the API through real HTTP" in co, \
    "corpora table must carry the what-it-verifies column"
assert "What it does" in co \
    and "python linter" in co and "size budget report" in co, \
    "gates must describe themselves (curated id + yaml name fallback)"
assert 'href="feature-gadget.html#ev-g1"' in co, \
    "a claimed proof set must link its entity's Evidence anchor"
assert ">stray</b>" in co and ">unclaimed<" in co[co.find(">stray</b>"):][:2400], \
    "an unclaimed proof set must be NAMED unclaimed on the shelf"
assert "<title>entity</title>" in co, "the shelf entity column needs its glyph"
# Round 24: the shelf explains each SET (What it shows = the manifest's own
# feature + story; no manifest = named gap), and repeated state prose moves
# behind the ledger-dialect ⓘ popover (tag + tinfo, script included).
assert "What it shows" in co and "Gadget scan walk" in co \
    and "One pass through the scan flow." in co, \
    "a curated set must show its manifest's feature + story"
assert ">no manifest<" in co[co.find(">stray</b>"):][:900], \
    "a manifest-less set must name that gap in What-it-shows"
# Round 28: row popovers RETIRED on the shelf (three open ⓘs covered each
# other) — the vocabulary + integration recipe live in the sechead ⊕, rows
# keep bare tags with filter marker classes, and the bar filters by
# entity · set state · claim state via the shared ehide class.
assert 'class="tinfo"' not in co, \
    "shelf rows must not carry popovers — the ⊕ holds the vocabulary"
assert "entities[].proofs" in co and "never a claim" in co, \
    "the ⊕ must carry the integration recipe + the likely-badge honesty"
assert 'id="shelfbar"' in co and 'id="sh-ent"' in co \
    and 'id="sh-set"' in co and 'id="sh-claim"' in co, \
    "shelf filter bar (entity · set · claim) missing"
assert 't-lg">legacy<' in co and 't-uncl">unclaimed<' in co, \
    "filter marker classes must ride the tags"
assert "classList.toggle('ehide'" in co and 'id="sh-count"' in co, \
    "the shelf filter must hide via ehide and keep the live count"
# Round 25: pinned widths must reach the browser — fr is grid vocabulary,
# a real <col> needs px/% (equal-column fallback was the cramped shelf);
# dot-dirs are tool residue, never proof sets.
import re as _re3
assert not _re3.search(r'col style="width:[0-9.]+fr"', co), \
    "table col widths must never ship fr units"
assert 'style="width:44px"' in co and _re3.search(
    r'col style="width:[0-9.]+%"', co), \
    "the shelf colgroup must mix px (icons/dates) with % (prose)"
assert ">.some_cache</b>" not in co, "a dot-dir must never render as a set"
# The tflip capability stays in the css for the ledger's right-edge ⓘs
# (the shelf itself no longer carries popovers — round 28).
assert ".tinfo.tflip .tx" in (c / "assets" / "a3.css").read_text(), \
    "a3.css must ship the tflip rule"
# Round 27: legacy sets are IDENTIFIED and made legible for integration —
# the legacy tag, the shot-name narration (3 + named-path rest), and the
# LIKELY owner guessed from the entity test_rx (a labeled guess, never a
# claim). A curated set (g1) must NOT wear the tag.
_wlw = co[co.find(">widget-legacy-walk</b>"):][:2400]
assert ">legacy<" in _wlw, "a manifest-less set must wear the legacy tag"
assert "shots: 01-open · 02-fill · 03-save" in _wlw \
    and "(+1 more in tests/web-e2e/proof/widget-legacy-walk/)" in _wlw, \
    "legacy narration must peek the shot names and NAME where the rest live"
assert ">likely</span>" in _wlw and "ent-gadget" in _wlw, \
    "the name-pattern owner guess must render as the labeled LIKELY badge"
assert ">legacy<" not in co[co.find(">g1</b>"):co.find(">stray</b>")], \
    "a curated set must never wear the legacy tag"
assert ">likely</span>" not in \
    co[co.find(">stray</b>"):co.find(">widget-legacy-walk</b>")], \
    "no guess when no entity pattern matches the name"
assert 'href="test-corpora.html#sec-tests-walks"' in dash, \
    "the manual kind row must link the walks record"
# Round 19 (operator verdicts 2026-07-24): the entity column HEADER carries
# the Entity-index layers glyph on every table that has the icon-only
# column; the estate pages carry a sticky section menu (overview + the
# five estate pages, current marked); Gaps is renamed Untested; app rows
# OPEN like their entity-tab counterparts (files -> cases, claims -> cases)
# with C-ids linking the Cases page across pages.
assert "<title>entity</title>" in dash, \
    "the entity x kind matrix must label its entity column with the glyph"
cl = (c / "test-claims.html").read_text()
assert 'class="entb ent-gadget"' in cl and ">running<" in cl, \
    "the app claims page must carry the real per-claim rows, entity first"
assert 'class="entchips"' in cl and 'class="stickstack"' in cl, \
    "claims must carry the entity filter bar, stacked with the menu"
assert 'href="test-matrix.html#C12"' in cl, \
    "an app claim fold's C-ids must link the Cases page"
assert "<title>entity</title>" in cl, "claims entity column needs its glyph"
for est, cur in (("test-matrix.html", "Cases"),
                 ("test-files.html", "Files"),
                 ("test-claims.html", "Claims"),
                 ("test-elements.html", "Untested"),
                 ("test-corpora.html", "Corpora")):
    eh = (c / est).read_text()
    assert 'class="subnav"' in eh and 'href="tests.html"' in eh, \
        f"{est}: estate menu with the overview link missing"
    assert f'class="on" href="{est}"' in eh, \
        f"{est}: the menu must mark the current page"
    assert f'class="navitem navsubitem on" href="{est}"' in eh, \
        f"{est}: the SIDEBAR subitem must mark the current page too"
m = (c / "test-matrix.html").read_text()
assert 'id="ledbar"' in m and "<select" in m and "<datalist" in m, \
    "dropdown filter bar missing (R2)"
assert 'id="C11"' in m, "C-id row anchor missing (the canonical anchor)"
assert 'data-ep="get /gadgets/one"' in m, "own T1 endpoint fact missing on C11"
assert "lc-via" in m, "inherited via-file chip missing (Q1: test_unlabeled)"
assert ">unminted<" in m, "unminted honesty tag missing (Q2)"
assert "×2</small>" in m, "parametrize executions must group under C12"
assert 'href="arch-endpoints.html#ep-app-' in m, "chips must LINK the code estate"
assert 'data-ent="gadget"' in m, "entity data attribute missing"
assert 'id="sec-tests-files"' not in m, \
    "the file altitude moved to its own page — no second home on the ledger"
assert "<title>entity</title>" in m, "the ledger entity column needs its glyph"
tf = (c / "test-files.html").read_text()
assert 'id="sec-tests-files"' in tf and 'class="entchips"' in tf, \
    "test-files.html must carry the file altitude with the entity filter bar"
assert 'href="test-matrix.html#C11"' in tf, \
    "an app file row must OPEN to its cases, C-ids linking the Cases page"
assert "<title>entity</title>" in tf, "files entity column needs its glyph"
# The gustify C494 regression pair: the files fold and the ledger must agree
# on a parametrized pytest id carrying ">" — the fold links C15, the ledger
# owns the anchor with both executions grouped under it.
assert 'href="test-matrix.html#C15"' in tf and 'id="C15"' in m, \
    "a pytest '>' parametrize id must keep its C-id and its ledger anchor"
assert "×2</small>" in m[m.find('id="C15"'):][:2000], \
    "C15's two executions must group under one ledger row"
# The fold SPINE is invariant (the C1710 confusion): a case with no entity
# and no app joins names both gaps instead of shipping a thinner fold —
# and exactly once (C16 is the only such case in the fixture).
_c16 = m[m.find('id="C16"'):][:4000]
assert ">unclaimed<" in _c16 and ">no app joins<" in _c16, \
    "an unclaimed joinless case must name both fold gaps"
assert m.count(">no app joins<") == 1, \
    "joined cases must NOT carry the no-app-joins gap"
assert 'class="k">entities<' in m[m.find('id="C11"'):][:4000], \
    "a claimed case keeps its real entities row"
# The C1599 confusion, resolved (round 21): an import landing on a REAL but
# UNREGISTERED repo file renders the actionable TBD gap — python (C17,
# tools/ci_helper.py) and web (C14's file imports src/fmt.ts) — and such a
# case never reads as infra ("no app joins" stays C16-only, above).
_c17 = m[m.find('id="C17"'):][:4000]
assert "unmapped imports" in _c17 and "tools/ci_helper.py" in _c17 \
    and 't-tbd">tbd<' in _c17, \
    "an unmapped python import must render the TBD gap row"
assert ">no app joins<" not in _c17, \
    "an unmapped-import case is awaiting adoption, not infra"
_c14 = m[m.find('id="C14"'):][:6000]
assert "src/fmt.ts" in _c14 and 't-tbd">tbd<' in _c14, \
    "an unmapped web import must render the TBD gap row"
assert 'class="ledmeta"' in m, "fold must be the labeled metadata grid"
assert 'class="k">entities<' in m, "fold must name the entities the case relates to"
assert 'in reach<details class="tinfo"' in m and "lonely_helper()" in m, \
    "in-reach chips (what reached files define) missing from the fold"
assert 'id="led-tag"' in m and 'data-tag="df3|w1"' in m, \
    "tag facet missing (tokens from the group name must be filterable)"
assert "tokenMatch" in m, \
    "exact-option inputs must token-match (GET /x must not catch GET /x/{id})"
assert 'data-for="led-ep"' in m and "closest('.lx')" in m, \
    "per-filter clear × missing (a filtered-to-zero ledger must never strand)"
assert 'class="ltit"' in m, "clear × must ride the title line, not the control"
assert 'class="ltag">DF3</span>' in m, "group tokens must render highlighted"
assert "<span>Exercises</span>" not in m, \
    "Exercises column retired — the fold carries what a case exercises"
assert 'class="tinfo"' in m and 'class="k">uses · T3<' not in m, \
    "tier codes must move off the labels into the ⓘ explainer"
assert 'uses<details class="tinfo"' in m and 'class="k kwide"' in m, \
    "the uses ⓘ must ride the label and the block must span the fold width"
assert "<b>functions</b>" in m and "<th>Signature</th>" in m \
    and ">planWidget<" in m and "seed: <a" in m, \
    "functions subsection must show typed signatures with linked types"
assert 'href="arch-code-map.html#cm-app-src-kinds-ts">WSeed</a>' in m, \
    "a signature type must link home via the GLOBAL ts-export index"
assert 'class="tclose"' in m and "d2._t=setTimeout" in m, \
    "the ⓘ popover needs its × and the auto-dismiss timer"
assert "<b>constants</b>" in m and ">WIDGET_KIND<" in m \
    and "<th>Declared as</th>" in m, \
    "constants subsection missing its declared-as column"
assert 'class="entb ent-gadget"' in m, "entity icon must lead the ledger row"
f = (c / "feature-gadget.html").read_text()
assert 'id="sec-tests-cases"' in f and 'id="C11"' in f, \
    "entity tab must carry the scoped ledger with C-id anchors"
assert 'title="integration · api corpus"' in f, \
    "Files kind cell must be icon-only (kind + corpus ride the title)"
assert '<a class="cid" href="#C11">' in f, \
    "Files rows must open onto their cases with C-ids linking the ledger"
assert ">running<" in f and "Cases · C-ids" not in f, \
    "claims must join the fixture class and drop the cases column"
assert '<a class="cid" href="#C12">' in f, \
    "claim fold C-ids must link their ledger rows"
# The EVIDENCE SEAM: g1's spec joins the corpus (C14 pill -> ledger row);
# the manifest-less solo set reads its named gap; sets carry anchors.
assert "<b>Verified by</b> <code>tests/widget.test.ts</code>" in f \
    and 'href="#C14"' in f, "evidence seam: spec must join its C-ids"
assert "no spec pointer joins the corpus record" in f, \
    "a set without a joinable spec must read its named gap"
assert 'id="ev-g1"' in f, "proof sets need anchors (the reverse link's target)"
# The triangle's last leg: dm card folds carry Tested-by receipts (the fn
# folds already did → count ≥ 2), and code-side C-id pills stay in-page on
# entity pages while the arch estate keeps the Cases-page link.
assert f.count("Tested by") >= 2, "dm fold must carry Tested-by receipts"
assert "<th>Tier</th>" in f, \
    "Tested-by folds must be the endpoint-style aggregation (Kind·Tier·…)"
af = (c / "arch-functions.html").read_text()
assert "led-fn=make_gid%28%29&led-strict=1" in af, \
    "arch-estate Tested-by titles must link the strict-filtered ledger"
# The whole-app parity contract (operator, round 29): every arch element
# page carries the SAME test sections + ledger links its entity twin does.
aep = (c / "arch-endpoints.html").read_text()
assert "test-matrix.html?led-ep=" in aep and "led-strict=1" in aep \
    and "<b>Tests</b>" in aep, \
    "arch endpoints must carry Tests sections linking the strict ledger"
adm = (c / "arch-data-model.html").read_text()
assert "test-matrix.html?led-mdl=" in adm and "Tested by" in adm, \
    "arch data model must carry Tested-by linking the strict ledger"
# The truncation BAN (operator ruling 2026-07-25): never "… N more" with no
# reference — every receipts block links its FILTERED ledger view, and the
# ledger pre-applies filters arriving as URL params.
import re as _re2
for _pg, _h in (("feature", f), ("matrix", m), ("arch-fn", af)):
    assert not _re2.search(r"… \d+ more", _h) and \
        not _re2.search(r"\+\d+ more<", _h), f"dangling truncation on {_pg}"
assert "test-matrix.html?led-mdl=GadgetOut&led-strict=1#sec-tests-cases" in f, \
    "dm Tested-by must link the receipts-strict model-filtered ledger"
assert "test-matrix.html?led-fn=make_gid%28%29&led-strict=1#sec-tests-cases" in f, \
    "fn Tested-by must link the receipts-strict function-filtered ledger"
assert "test-matrix.html?led-ep=GET%20%2Fgadgets%2Fone&led-strict=1#sec-tests-cases" in f, \
    "endpoint fold must link the receipts-strict route-filtered ledger"
# Strict mode's landing contract: rows carry RECEIPT attrs the engine
# recorded, and the JS honors led-strict while the URL value is untouched.
assert _re2.search(r'id="C11"[^>]*data-epr="get /gadgets/one"', m), \
    "C11 must carry its endpoint receipt attr"
assert _re2.search(r'id="C14"[^>]*data-epr="get /gadgets/one"', m), \
    "C14 (web file receipt) must carry the endpoint receipt attr"
assert "led-strict" in m and "strictVals" in m, \
    "the ledger JS must honor the strict receipts mode"
assert '">= 2</b>' not in f and 'class="ttot"' not in f, \
    "the = total chip is retired from the Tests cells"
# The receipts ARITHMETIC stays visible (operator, round 13): file-level
# rows carry their case counts, the Tests title totals them.
assert "1 file(s) · 1 case(s)" in f, \
    "file-level receipt rows must state their case count"
assert "(2 case(s)) <svg" in f, \
    "the endpoint Tests title count must be the link (with its icon)"
assert "URLSearchParams" in m, "the ledger must pre-apply URL-param filters"
assert _re2.search(r'id="C11"[^>]*data-mdl="[^"]*gadgetout', m), \
    "T2 route credits must join the filter surface (C11 -> GadgetOut)"
assert "test-matrix.html?led-q=" in f, \
    "the evidence Verified-by must link the spec-filtered ledger"
assert 'id="sec-tests-gaps"' in f and "lonely_helper" in f, \
    "entity Untested-surface section missing"
assert 'id="sec-tests-elements"' not in f, \
    "Shape A element roster must be GONE from the entity tab"
el = (c / "test-elements.html").read_text()
assert 'class="entchips"' in el and "Untested surface" in el, "Untested page missing"
assert "<h1>Untested</h1>" in el, "the page is named Untested now, not Gaps"
assert "<title>entity</title>" in el, "untested entity column needs its glyph"
assert "lonely_helper" in el, "untested function gap row must FIRE"
assert "/gadgets/one" not in el, "tested endpoint must stay SILENT on the Gaps page"
assert (c / "test-claims.html").exists() and (c / "test-corpora.html").exists()
PY4

# Gabe Center branding: the suite icon + subtitle ship in every skeleton.
grep -q "gabe-icon.png" "$FIX/docs/site/center/index.html" \
  && ok || bad "brand: the Gabe icon must ride the sidebar logo tile"
grep -q "Gabe Center" "$FIX/docs/site/center/index.html" \
  && ok || bad "brand: the subtitle must read Gabe Center"
[ -f "$FIX/docs/site/center/assets/gabe-icon.png" ] \
  && ok || bad "brand: gabe-icon.png must copy with the shell assets"
# The chrome harness ships with the generators and rides the refresh loop
# (operator ruling 2026-07-24) — regen · crawl gate · browser behavior are
# the three gates every center refresh runs.
[ -f "$GEN/verify_center_chrome.mjs" ] \
  && ok || bad "verify_center_chrome.mjs must ship with the generators"
grep -q "verify_center_chrome.mjs docs/site/center" "$GEN/refresh_center.sh" \
  && ok || bad "the chrome harness must ride refresh_center.sh"
# M38: the architecture station fills its OWN skeleton, completely.
[ -f "$SHELL_SRC/architecture.html" ] && ok || bad "M38: shell/architecture.html skeleton must ship"
grep -q '<h1>Architecture</h1>' "$FIX/docs/site/center/architecture.html" \
  && ok || bad "M38: architecture.html renders"
grep -q '{{' "$FIX/docs/site/center/architecture.html" \
  && bad "M38: architecture.html left unfilled slot tokens" || ok
# M30: archmap.json carries the machine-readable flow-coverage verdict.
python3 - "$FIX" <<'PY' && ok || bad "M30: archmap coverage block wrong (see above)"
import json, sys
from pathlib import Path
a = json.loads((Path(sys.argv[1]) / "docs/site/center/archmap.json").read_text())
c = a["coverage"]["gadget"]
assert (c["covered"], c["total"]) == (1, 2), c
assert (c["golden_covered"], c["golden_total"]) == (1, 1), c
assert c["unproven"] == ["manual"], c
assert "solo" in c["unclassified"], c
PY
# M30 gate warns: malformed FLOWS card (reuse the M5 fixture) + a typo'd role.
gate "$M5" >/dev/null 2>&1
grep -q 'FLOWS line(s) do not parse' "$T/gate.out" \
  && ok || bad "M30: gate must WARN on a card FLOWS line that does not parse"
ROLE="$T/role"; mk_fixture "$ROLE"
python3 - "$ROLE" <<'PY'
import json, sys
from pathlib import Path
m = Path(sys.argv[1]) / "tests/web-e2e/proof/g1/manifest.json"
man = json.loads(m.read_text())
man["role"] = "Principal"
man["flows"] = ["scam"]
m.write_text(json.dumps(man))
PY
build "$ROLE" "$SHELL_SRC" >/dev/null
gate "$ROLE" >/dev/null 2>&1
grep -q "role 'Principal' is not one of" "$T/gate.out" \
  && ok || bad "M30: gate must WARN on a role outside the role set"
grep -q 'names key(s) the card lacks: scam' "$T/gate.out" \
  && ok || bad "M30: gate must WARN on flows naming a card-unknown key"

# --- walk subjects: bare slug AND adopt:<slug> both credit the entity ------
# (the walk-briefing reshape: record-walk: transaction and /gabe-cc-init's
#  adopt:transaction are the same witness — an exact adopt:-only match left
#  honest walks invisible on the very page they walked)
WK="$T/walk"; mk_fixture "$WK"
mkdir -p "$WK/.kdbp"
printf '{"subject":"gadget","who":"t","when":"2026-07-23T00:00:00Z","result":"pass","evidence":null,"note":"looked at the ledger only"}\n' \
  > "$WK/.kdbp/walks.jsonl"
[ "$(build "$WK" "$SHELL_SRC")" = 0 ] && ok || bad "walk: fixture builds"
grep -q 'manual — walked 2026-07-23' "$WK/docs/site/center/feature-gadget.html" \
  && ok || bad "walk: BARE-slug subject must close the manual angle"
# #151: the walk's NOTE is where the walker qualifies what they checked, and
# WHO walked it is half the record. A bare date asserts more than it knows.
grep -q 'walked 2026-07-23 by t' "$WK/docs/site/center/feature-gadget.html" \
  && ok || bad "walk: the walker must be named beside the date"
grep -q 'looked at the ledger only' "$WK/docs/site/center/feature-gadget.html" \
  && ok || bad "walk: the NOTE must render — candour that cannot reach the reader is not disclosure"
printf '{"subject":"adopt:gadget","who":"t","when":"2026-07-23T00:00:00Z","result":"pass","evidence":null,"note":"approved"}\n' \
  > "$WK/.kdbp/walks.jsonl"
build "$WK" "$SHELL_SRC" >/dev/null
grep -q 'manual — walked 2026-07-23' "$WK/docs/site/center/feature-gadget.html" \
  && ok || bad "walk: adopt:-prefixed subject must still close the manual angle"
printf '{"subject":"other-thing","who":"t","when":"2026-07-23T00:00:00Z","result":"pass","evidence":null,"note":"x"}\n' \
  > "$WK/.kdbp/walks.jsonl"
build "$WK" "$SHELL_SRC" >/dev/null
grep -q 'no walk on record' "$WK/docs/site/center/feature-gadget.html" \
  && ok || bad "walk: an unrelated subject must NOT credit the entity"

# --- NEW-row badges: the rowmarks engine (gastify trial 824bf7e, absorbed) --
if (cd "$GEN" && python3 - <<'PY'
import _a3_render as R

def snapshot_of(render):
    R.init_rowmarks(None)
    render()
    return R.rowmarks_seen()

# bootstrap: no baseline at HEAD -> record only, badge nothing
R.init_rowmarks(None)
assert "t-new" not in R.table(["A"], [["brand-new row"]])
# armed empty baseline -> everything badges
R.init_rowmarks({})
assert 'class="tag t-new">NEW</span>' in R.table(["A"], [["fresh row"]])
# known unchanged row stays clean
base = snapshot_of(lambda: R.table(["A", "B"], [["row-1", "same"]]))
R.init_rowmarks(base)
assert "t-new" not in R.table(["A", "B"], [["row-1", "same"]])
# touched row re-badges
base = snapshot_of(lambda: R.table(["A", "B"], [["row-1", "before"]]))
R.init_rowmarks(base)
assert "t-new" in R.table(["A", "B"], [["row-1", "after"]])
# a relative-time tick is the clock moving, not the row
base = snapshot_of(lambda: R.table(["Corpus", "Last run"],
                                   [["api", "T−27h"], ["proof", "47d ago"]]))
R.init_rowmarks(base)
assert "t-new" not in R.table(["Corpus", "Last run"],
                              [["api", "T−28h"], ["proof", "48d ago"]])
# xtable rows badge too — exactly the new one
base = snapshot_of(lambda: R.xtable(["Set", "Role"], [(["old-set", "principal"], "")]))
R.init_rowmarks(base)
out = R.xtable(["Set", "Role"], [(["old-set", "principal"], ""),
                                 (["new-set", "edge"], "<p>detail</p>")])
assert out.count("t-new") == 1
# duplicate first cells (LEDGER dates) key apart via the occurrence counter
rows = [["2026-07-22", "first"], ["2026-07-22", "second"]]
base = snapshot_of(lambda: R.table(["Date", "What"], rows))
R.init_rowmarks(base)
assert "t-new" not in R.table(["Date", "What"], rows)
PY
) >"$T/rowmarks.out" 2>&1; then ok; else bad "rowmarks unit cases (see below)"; cat "$T/rowmarks.out"; fi

# End to end: iteration boundary = commit boundary. Bootstrap badges nothing;
# committing the snapshot arms it; one appended LEDGER row badges exactly once;
# a same-iteration regen is idempotent.
RM="$T/rowmark-e2e"; mk_fixture "$RM"
(cd "$RM" && git init -q && git config user.email t@t && git config user.name t)
mkdir -p "$RM/.kdbp"
printf '| Date | What | Phase | Review | Push |\n|---|---|---|---|---|\n| 2026-07-22 | first row | 1 | ok | — |\n' > "$RM/.kdbp/LEDGER.md"
[ "$(build "$RM" "$SHELL_SRC")" = 0 ] && ok || bad "rowmark-e2e: bootstrap build"
grep -q "bootstrap — badges off" "$T/build.out" && ok || bad "rowmark-e2e: bootstrap says badges off"
grep -rl "t-new\">NEW" "$RM/docs/site/center" --include="*.html" >/dev/null \
  && bad "rowmark-e2e: bootstrap must badge NOTHING" || ok
(cd "$RM" && git add -A >/dev/null && git commit -qm baseline)
printf '| 2026-07-23 | second row | 2 | ok | — |\n' >> "$RM/.kdbp/LEDGER.md"
build "$RM" "$SHELL_SRC" >/dev/null
# The appended row may legitimately render (and badge) in more than one table;
# the contract is: badges exist, and EVERY badge in the estate belongs to the
# one changed row — nothing untouched lights up.
python3 - "$RM/docs/site/center" <<'PY' && ok || bad "rowmark-e2e: badges must mark ONLY the appended row (see above)"
import sys
from pathlib import Path
total, stray = 0, 0
for p in Path(sys.argv[1]).glob("*.html"):
    html = p.read_text()
    i = 0
    while (i := html.find('t-new">NEW', i)) != -1:
        total += 1
        # the badge sits IN the first cell — row context spans both sides
        around = html[max(0, i - 400):i + 400]
        # legitimate NEW content this iteration: the appended LEDGER row, and
        # the baseline COMMIT itself (git-derived tables see new history too)
        if not any(m in around for m in ("second row", "2026-07-23", "baseline")):
            stray += 1
            print(f"STRAY badge in {p.name}: …{around[-120:]!r}")
        i += 1
assert total >= 1, "no badge rendered at all"
assert stray == 0, f"{stray} stray badge(s) of {total}"
print(f"{total} badge(s), all on the appended row")
PY
cp "$RM/docs/site/center/rows-seen.json" "$T/rows-seen.1"
build "$RM" "$SHELL_SRC" >/dev/null
diff -q "$T/rows-seen.1" "$RM/docs/site/center/rows-seen.json" >/dev/null \
  && ok || bad "rowmark-e2e: same-iteration regen must be idempotent"
grep -q 't-new">NEW' "$RM/docs/site/center/ledger.html" \
  && ok || bad "rowmark-e2e: badges stable across same-iteration regens"

# --- flow grammar + classifier honesty (M05/M12/M03) -----------------------
if (cd "$GEN" && python3 - <<'PY'
import sys
import _a3_evidence as ev

flows, bad = ev.parse_flows(
    ["- scan ★ → receipt to ledger", "- browse the list",
     "- two words → x", "- manual → typed entry"])
assert [f[0] for f in flows] == ["scan", "manual"]
assert flows[0][2] is True and flows[1][2] is False
assert len(bad) == 2, bad

F = [("scan", "receipt into the ledger pipeline", True),
     ("manual", "typed entry path", False)]
S = lambda man, name="x": {"man": man, "name": name, "legs": []}
c = ev._classify(S({"role": "Principal"}), F)
assert c["role"] == "" and "role" in c["reason"]           # typo'd role → unclear
c = ev._classify(S({"role": "principal", "flows": "scan"}), F)
assert c["role"] == "" and "LIST" in c["reason"]           # string flows → unclear
c = ev._classify(S({"flows": ["scam"]}), F)
assert c["role"] == "" and "scam" in c["reason"]           # unknown key → unclear
c = ev._classify(S({"role": "principal", "flows": ["scan"]}), F)
assert (c["role"], c["flows"], c["golden"], c["explicit_match"]) == \
       ("principal", ["scan"], True, True)                 # explicit wins
c = ev._classify(S({"feature": "the scan journey", "proof_form": "recorded"},
                   name="scan-walk"), F)
assert c["role"] == "principal" and c["inferred"] and not c["explicit_match"]
c = ev._classify(S({}), F)
assert c["role"] == "" and c["reason"] == "no manifest"
# explicit EMPTY flows: [] declares "covers nothing" — inference stays shut
# (gastify 6ed1292: ca0's story once inferred five phantom flows)
c = ev._classify(S({"role": "supporting", "flows": [],
                    "narration": {"story": "the scan and manual paths"}}), F)
assert c["role"] == "supporting" and c["flows"] == []
# inference reads IDENTITY ONLY — a story mentioning a flow must not match
# (suite ruling 2026-07-23, handoff §9)
c = ev._classify(S({"feature": "context shots", "proof_form": "stills",
                    "narration": {"story": "user runs the scan pipeline"}},
                   name="ctx-set"), F)
assert c["flows"] == [], c
sys.exit(0)
PY
) >"$T/py.out" 2>&1; then ok; else bad "flow grammar/classifier unit asserts (see below)"; cat "$T/py.out"; fi

# --- BOARD station (2026-07-25): card model + the closure verdict ----------
# The board is a projection of PLAN/PENDING/LEDGER/walks/SCOPE. Each rule below
# is proven able to BOTH fire and stay silent, because a checker that cannot
# fail is non-evidence.
if (cd "$GEN" && python3 - <<'BOARDPY'
import sys
sys.path.insert(0, ".")
import _center_data as D
import _a3_board as B

# ---- closure verdict: the LEADING token decides, the tail is provenance ----
# A reconciled row records its history inline; a substring test sees both
# verdicts and guesses. FIRE (closed) and SILENT (still open) both proven.
for text, want in [
    ("RESOLVED @ abc123 2026-07-23 - fixed . prior: STILL-REAL @ old", True),
    ("STILL-REAL @ e37dccc5 - undecidable statically", False),
    ("PART-RESOLVED - only half shipped", False),
    ("RESOLVED-OBSOLETE", True),
    ("ACCEPTED-TRADEOFF against D72-A", False),
    ("FOUNDER-GATED pre-launch", False),
    ("open - parked: later", False),
    ("CLOSED 2026-07-21 (reconcile)", True),
    ("", False),                       # empty Status is NOT closed
    ("rebuild-only note", False),      # unknown lowercase verdict stays open
]:
    got = D._verdict_closed(text)
    assert got == want, "verdict %r: got %s want %s" % (text, got, want)

# ---- md_tables: a header is a row FOLLOWED BY a |---| separator -----------
# Rows interleaved with HTML comments must NOT split the table, and the row
# after a comment must NOT be promoted to a header.
doc = "\n".join([
    "| # | Finding | Priority | Status |",
    "|---|---------|----------|--------|",
    "| 1 | first   | low      | OPEN   |",
    "<!-- an aside between rows -->",
    "| 2 | second  | high     | OPEN   |",
])
rows = D.pick_table(doc, "#", "Finding", "Priority")
assert len(rows) == 2, "comment split the table: %d rows" % len(rows)
assert rows[1]["Finding"] == "second", rows

# ---- col(): the arc table is spelled two ways in the wild -----------------
assert D.col({"ID": "3"}, "ID", "#") == "3"
assert D.col({"#": "3"}, "ID", "#") == "3"
assert D.col({"Depends on": "1"}, "Depends-on", "Depends on") == "1"

# ---- area_of: SEGMENTS, not prefixes -------------------------------------
# Rules written as apps/api|apps/web once labelled a whole codebase "tooling".
assert B.area_of("apps/api/api/recipes.py") == "api"
assert B.area_of("backend/app/main.py") == "api", "gastify layout must resolve"
assert B.area_of("web/src/routes/scan.tsx") == "web"
assert B.area_of("scripts/build.py") == "tooling"
assert B.area_of("tests/web-e2e/a.spec.ts") == "e2e"
assert B.area_of("") is None and B.area_of("-") is None

# ---- brace expansion + attribution: path-derived or ABSENT ----------------
assert sorted(B.cite_tokens("f/{a,b}/**")) == ["f/a", "f/b"]
# A five-entity registry, because the sweep guard is RELATIVE: a citation is
# only "not discriminating" once it covers more than half the registry, and a
# two-entity fixture could never exercise it.
amap = {"entities": {
    "recipe": {"files": [["api", "apps/api/recipes.py", 900]]},
    "pantry": {"files": [["api", "apps/api/pantry.py", 120]]},
    "auth": {"files": [["api", "apps/api/auth.py", 200]]},
    "cooking": {"files": [["api", "apps/api/cooking.py", 200]]},
    "billing": {"files": [["api", "apps/api/billing.py", 200]]}}}
ENT = {"recipe": "Recipe", "pantry": "Pantry", "auth": "Auth",
       "cooking": "Cooking", "billing": "Billing"}
att = B.Attributor(amap, ENT)
slugs, matched = att("apps/api/recipes.py")
assert slugs == ["recipe"] and matched, (slugs, matched)           # FIRE
slugs, _ = att("scripts/_center_data.py")
assert slugs == [], "a tooling path must read cross-cutting, never guess"
slugs, _ = att("apps/api/recipes.py + apps/api/pantry.py")
assert sorted(slugs) == ["pantry", "recipe"], slugs                # SET not one
slugs, _ = att("apps/api")
assert slugs == [], "a whole-tree citation must collapse to cross-cutting"
assert len(att("apps/api/recipes.py")[0]) == 1, "a precise path still resolves"

def prow(**kw):
    row = {"num": "1", "date": "2026-01-01", "source": "review",
           "finding": "f", "file": "", "scale": "mvp", "priority": "low",
           "impact": "", "deferred": "0", "status": "OPEN", "verified": "",
           "gate": "", "open": True, "closed": False, "closed_on": "",
           "parked": False, "origin_file": ".kdbp/PENDING.md"}
    row.update(kw)
    return row

def cards(pending, sections=(), plan=None):
    return B.build_cards(plan=plan or {"phases": []}, sections=list(sections),
                         archmap=amap, adoption={},
                         labels=ENT, entity_href=lambda s: "f-%s.html" % s,
                         pending=pending)

# ---- effort is priced from RECORDED line counts --------------------------
big = [c for c in cards([prow(file="apps/api/recipes.py")])
       if c["track"] == "debt"][0]
assert big["effort"] == "L" and "900 lines" in big["effort_basis"], big
assert big["inferred"] == [], "a recorded line count is not an inference"
assert big["ripe"] is False, "an L-sized row is never ripe"

# ---- the ripe predicate: prerequisites met AND cheap ---------------------
sm = [c for c in cards([prow(num="2", file="apps/api/pantry.py")])
      if c["track"] == "debt"][0]
assert sm["ripe"] is True and sm["effort"] == "S", sm

# ---- a gated row is BLOCKED, not ready, and never ripe ------------------
g = [c for c in cards([prow(num="3", file="apps/api/pantry.py",
                            gate="founder")]) if c["track"] == "debt"][0]
assert g["state"] == "blocked" and g["ripe"] is False, g

# ---- verify cards route to the RIGHT beat -------------------------------
# 6/7 with only the walk owed -> record-walk; 0/7 -> /gabe-cc-init. Naming the
# wrong command sends the operator to a beat whose preconditions are not met.
full = dict.fromkeys(("testing_inventory", "legacy_reverified", "card",
                      "diagrams", "proofs", "gate_green"), True)
secs = [{"entity": "recipe", "display_name": "Recipe",
         "status": "awaiting-approval",
         "checklist": dict(full, walk_recorded=False)},
        {"entity": "pantry", "display_name": "Pantry",
         "status": "awaiting-approval",
         "checklist": dict.fromkeys(list(full) + ["walk_recorded"], False)}]
by = {c["id"]: c for c in cards([], secs) if c["track"] == "verify"}
assert by["verify:recipe"]["cmd"] == "record walk: recipe → walks.jsonl", by["verify:recipe"]
assert by["verify:recipe"]["ripe"] is True
assert by["verify:pantry"]["cmd"] == "/gabe-cc-init section pantry", by["verify:pantry"]
assert by["verify:pantry"]["ripe"] is False
# both are OWED TO YOU - nobody but the operator can clear either
assert set(c["state"] for c in by.values()) == set(["owed_to_you"])

# ---- an APPROVED, fully-checked section emits NO verify card (silent) ----
done_sec = [{"entity": "recipe", "display_name": "Recipe",
             "status": "approved", "checklist": dict(full, walk_recorded=True)}]
assert not [c for c in cards([], done_sec) if c["track"] == "verify"], \
    "an approved section must not owe a walk"

# ---- phase_id: the `#` column wins when Phase carries no separator -------
assert B.phase_id({"num": "P4", "id": "God files", "name": "God files"}) == "P4"
assert B.phase_id({"num": "1", "id": "W1", "name": "Token foundation"}) == "W1"

# ---- every framing renders, and `done` switches population --------------
mixed = cards([prow(num="9", file="apps/api/pantry.py", open=False,
                    closed=True, status="CLOSED 2026-02-01",
                    closed_on="2026-02-01")], secs)
labels = ENT
for mode, _l, _s in B.MODES:
    html = B.board_html(mode, mixed, labels)
    assert 'class="bboard"' in html, mode
    assert 'data-mode="%s"' % mode in html, mode
open_n = sum(1 for c in mixed if not c["done"])
done_n = len(mixed) - open_n
assert done_n == 1 and open_n >= 2, (open_n, done_n)
assert B.board_html("done", mixed, labels).count('class="bcard"') == done_n
assert B.board_html("state", mixed, labels).count('class="bcard"') == open_n

# ---- KPI reconciliation: 0 is a real number, not "missing" --------------
# `closed_days or 999` once made every same-day close count as ancient, so the
# KPI contradicted the column beside it. The close date is TODAY, not a
# literal: a hardcoded 2026-07-25 passed for exactly seven days and then
# failed on 2026-08-01 — date-rot reporting a bug that did not exist.
import datetime as _dt
_today = _dt.date.today().isoformat()
k = B.kpis([B._card(id="x", track="debt", title="t", detail="", state="done",
                    done=True, created=_today, closed=_today,
                    source="s")])
assert "1 in the last 7" in k, k
sys.exit(0)
BOARDPY
) >"$T/py.out" 2>&1; then ok; else bad "board card model + closure verdict (see below)"; cat "$T/py.out"; fi

# --- GUARD lens (2026-07-25): used-but-unguarded, and the by_endpoint trap ---
if (cd "$GEN" && python3 - <<'GUARDPY'
import sys
sys.path.insert(0, ".")
import _a3_guard as G

FI = {
    # guarded by a direct function binding
    "api/a.py::alpha": {"fn": "alpha", "file": "api/a.py", "entity": "e1",
                        "usage": 5, "lines": 10, "api": False},
    # guarded ONLY by a route test -> by_endpoint, same file::fn key shape
    "api/a.py::route_h": {"fn": "route_h", "file": "api/a.py", "entity": "e1",
                          "usage": 1, "lines": 10, "api": True,
                          "handler": True},
    # genuinely unguarded and load-bearing
    "api/a.py::hot": {"fn": "hot", "file": "api/a.py", "entity": "e1",
                      "usage": 4, "lines": 12, "api": False},
    # unguarded, used once, internal -> NOT a card (noise)
    "api/a.py::cold": {"fn": "cold", "file": "api/a.py", "entity": "e1",
                       "usage": 1, "lines": 8, "api": False},
}
ENTS = {"e1": {"files": [["api", "api/a.py", 100],
                         ["web", "web/big.ts", 1200],
                         ["web", "web/small.ts", 40]],
               "defines": {"web/big.ts": ["Used"] + [f"Unused{i}"
                                                     for i in range(12)],
                           "web/small.ts": ["OnlyThing"]}}}
EXER = {"t1.test.ts": {"corpus": "web", "uses": [{"name": "Used"}],
                       "functions": []},
        "t2.test.ts": {"corpus": "web", "uses": [{"name": "OnlyThing"}],
                       "functions": []}}

# THE by_endpoint TRAP: a route test credits the handler under by_endpoint, not
# by_function. Reading only by_function reports every route-tested endpoint as
# unguarded — the exact false alarm this lens exists to avoid.
gi = G.guard_insight(function_insight=FI,
                     by_function={"api/a.py::alpha": [{"cid": "C1"}]},
                     by_endpoint={"api/a.py::route_h": {"api": [{"cid": "C2"}]}},
                     exercises=EXER, entities=ENTS)
assert "api/a.py::alpha" not in gi["functions"], "a bound fn must be guarded"
assert "api/a.py::route_h" not in gi["functions"], \
    "a ROUTE-tested handler must count as guarded"
assert "api/a.py::hot" in gi["functions"] and "api/a.py::cold" in gi["functions"]
assert gi["totals"]["fn_guarded"] == 2, gi["totals"]

# SILENT the other way: drop by_endpoint and the handler becomes unguarded, so
# the assertion above is testing something real.
gi_nb = G.guard_insight(function_insight=FI,
                        by_function={"api/a.py::alpha": [{"cid": "C1"}]},
                        by_endpoint={}, exercises=EXER, entities=ENTS)
assert "api/a.py::route_h" in gi_nb["functions"]

# ---- web: symbols matched by NAME against what tests import ---------------
big = gi["files"]["web/big.ts"]
assert big["declared"] == 13 and big["unguarded"] == 12, big
assert big["exact"] is False, "the web half is a name match — never exact"
assert "Used" not in big["names"], big["names"]
small = gi["files"]["web/small.ts"]
assert small["unguarded"] == 0, "a fully-named file must read guarded"

# ---- python file rollup is EXACT -----------------------------------------
apy = gi["files"]["api/a.py"]
assert apy["exact"] is True and apy["declared"] == 4 and apy["unguarded"] == 2, apy
assert apy["lines"] == 100, "file lines come from the entity map, not the fn"

# ---- moves: hot functions individually, files as one sitting --------------
mv = G.guard_moves(gi)
ids = [m["id"] for m in mv]
assert "guard:api/a.py::hot" in ids, ids           # FIRE: load-bearing
assert "guard:api/a.py::cold" not in ids, \
    "used once and internal is a fact, not a to-do"  # SILENT
assert "guard:web/big.ts" in ids, ids               # 1200 lines, 75% unguarded
assert "guard:web/small.ts" not in ids, "a fully-guarded file owes nothing"
byid = {m["id"]: m for m in mv}
assert byid["guard:web/big.ts"]["kind"] == "file"
assert byid["guard:web/big.ts"]["exact"] is False
assert byid["guard:api/a.py::hot"]["kind"] == "function"
assert byid["guard:api/a.py::hot"]["exact"] is True
# A hot function outranks even a file whose RAW score is higher: it is
# specific, small and cheap, so it belongs at the top of a pick-list.
# (big.ts scores 12*5 + 1200//100 = 72 on its own; the hot fn scores 40.)
assert ids.index("guard:api/a.py::hot") < ids.index("guard:web/big.ts"), ids

# ---- the cluster cut: a SMALL file with a big pile still earns a card -----
ENTS2 = {"e1": {"files": [["web", "web/tiny.ts", 60]],
                "defines": {"web/tiny.ts": [f"S{i}" for i in range(12)]}}}
gi2 = G.guard_insight(function_insight={}, by_function={}, by_endpoint={},
                      exercises={}, entities=ENTS2)
assert G.guard_moves(gi2), "12 unguarded exports is a sitting whatever the size"
# ... and a small file UNDER the cluster floor stays silent
ENTS3 = {"e1": {"files": [["web", "web/tiny.ts", 60]],
                "defines": {"web/tiny.ts": ["A", "B", "C"]}}}
gi3 = G.guard_insight(function_insight={}, by_function={}, by_endpoint={},
                      exercises={}, entities=ENTS3)
assert not G.guard_moves(gi3), "3 unguarded exports in a 60-line file is noise"

# ---- graceful on an empty project ----------------------------------------
empty = G.guard_insight(function_insight={}, by_function={}, by_endpoint={},
                        exercises={}, entities={})
assert empty["files"] == {} and G.guard_moves(empty) == []
sys.exit(0)
GUARDPY
) >"$T/py.out" 2>&1; then ok; else bad "guard lens (see below)"; cat "$T/py.out"; fi

# --- GUARD placement across altitudes (2026-07-25 gap analysis) ------------
# One fact, four altitudes. Each level gets the form its RATE justifies, and
# the rendered surfaces are pinned so a refactor cannot quietly swap them.
if (cd "$GEN" && python3 - <<'PLACEPY'
import sys
sys.path.insert(0, ".")
import _a3_guard as G

# ---- class-only files: the hole the data-model level exists to fill -------
# A models/ or schemas/ file declares classes and no defs, so it never entered
# the function rollup and rendered NO guard signal at all.
ENTS = {"e1": {"files": [["models", "api/models.py", 120],
                         ["api", "api/svc.py", 90]],
               "defines": {}}}
FI = {"api/svc.py::doer": {"fn": "doer", "file": "api/svc.py", "entity": "e1",
                           "usage": 1, "lines": 5, "api": False}}
# `Stale` carries the RETIRED flag in its input record on purpose: a twin
# regenerating against an archmap written before R10 must not resurrect the
# branch. The consumer reads evidence now, so the key is inert data.
MI = {"Kept":   {"cls": "Kept", "file": "api/models.py", "entity": "e1"},
      "Naked":  {"cls": "Naked", "file": "api/models.py", "entity": "e1"},
      "Stale":  {"cls": "Stale", "file": "api/models.py", "entity": "e1",
                 "orphan": True},
      # this one lives in a file that ALREADY has a function chip
      "InSvc":  {"cls": "InSvc", "file": "api/svc.py", "entity": "e1"}}
gi = G.guard_insight(function_insight=FI, by_function={}, by_endpoint={},
                     exercises={}, entities=ENTS,
                     by_model={"Kept": [{"cid": "C1"}]}, model_insight=MI)
mf = gi["files"]["api/models.py"]
assert mf["kind"] == "model" and mf["declared"] == 3, mf
# R10: an unnamed class is UNGUARDED, full stop — the lens no longer forks a
# class off as "delete it, don't guard it" on a verdict it cannot support.
# MUTATION: restore `if v.get("orphan"): slot["orphan_unguarded"] += 1 else:`
# around the counter in _a3_guard.guard_insight — Stale leaves the count and
# both of the next two asserts fail.
assert mf["unguarded"] == 2, mf
assert "orphan_unguarded" not in mf, f"R10: the split slot must be gone: {mf}"
assert mf["names"] == ["Naked", "Stale"], mf["names"]
assert mf["lines"] == 120, "class-file lines come from the entity map"
# the class in a file that already has a function chip is NOT re-counted
assert gi["files"]["api/svc.py"]["kind"] == "api", gi["files"]["api/svc.py"]
assert gi["files"]["api/svc.py"]["declared"] == 1, "no class/def double count"
# MUTATION: re-add `"cls_orphan": sum(v["orphan_unguarded"] …)` to totals.
assert gi["totals"]["cls_files"] == 1 and gi["totals"]["cls_unguarded"] == 2, \
    gi["totals"]
assert "cls_orphan" not in gi["totals"], \
    f"R10: the orphan total must be gone: {gi['totals']}"

# SILENT: with no model inputs at all the lens behaves exactly as before
plain = G.guard_insight(function_insight=FI, by_function={}, by_endpoint={},
                        exercises={}, entities=ENTS)
assert "api/models.py" not in plain["files"], "class files need model inputs"
assert plain["totals"]["cls_files"] == 0
sys.exit(0)
PLACEPY
) >"$T/py.out" 2>&1; then ok; else bad "guard placement: class-only files (see below)"; cat "$T/py.out"; fi

# The RENDERED placement contract, on the built fixture.
python3 - "$FIX/docs/site/center/feature-gadget.html" <<'PY' && ok || bad "guard placement: rendered surfaces (see above)"
import sys
html = open(sys.argv[1]).read()

# ENDPOINT altitude — the chip is `unguarded` (rare: ~21%/7% on the twins), and
# it unions BOTH bindings, so an endpoint reached only through its handler
# reads `via handler N` rather than being called untested.
# Precise: the earlier form matched the FUNCTIONS filter chip whose label is
# also "unguarded" — a false pass that survived because the fixture had no
# untested endpoint at all. Anchor on the chip's own tooltip instead.
assert "no case or spec matches this route" in html and \
       "no case names its handler" in html, \
       "the untested endpoint must carry the guard chip, and its tooltip must "\
       "name the UNION (path OR handler) it was decided by"
assert "/gadgets/two" in html, "the untested endpoint must render"
assert ">unguarded</span>" in html, "the endpoint chip's LABEL is part of the "\
                                    "contract, not just its tooltip"
# THE UNION, pinned: /three's route is driven by nothing, but a case calls its
# handler, so it must NOT read as unguarded.
assert "via handler" in html, "an endpoint reached only through its handler "\
                              "must say so instead of being called untested"

# FUNCTION altitude — no second per-row chip (60-82% would be wallpaper): the
# filter hook rides the gap chip that was already there.
assert "t-tgap t-unguarded" in html, "unguarded fns need the filter hook"
assert 'data-f="t-unguarded"' in html, "the functions strip needs the filter"
assert 'data-f="t-hot"' in html, "...and the hot narrowing"

# CODE MAP altitude — the file rollup stays.
assert "unguarded " in html and "/" in html, "code-map rollup chip missing"
PY

# --- vendored-fix regressions (gustify #148 · #150 · #151) -----------------
# Found in a twin's VENDORED copies of these generators. They are pinned here
# so a propagation carries the fixes upstream instead of a re-sync reverting
# whatever the twin patched locally.
if (cd "$GEN" && python3 - <<'VENDPY'
import sys, json
sys.path.insert(0, ".")
import _center_data as D

# ---- #148: the Center queue was structurally blind ------------------------
# load_plan keeps `red`/`center` at the phase TOP level while `cells` holds the
# original four. next_feature.py asked for cells["center"], matched nothing for
# every phase, and could never report an owed Center cell — it printed
# "queue clear" while a served phase's Center was todo.
phase = {"id": "P1", "name": "x", "cells": {"exec": "done", "review": "done",
                                            "commit": "done", "push": "done"},
         "red": "todo", "center": "todo"}
c = D.phase_cells(phase)
assert c["center"] == "todo", "center must be reachable through phase_cells"
assert c["red"] == "todo", "red too — same split, same trap"
assert list(c) == ["red", "exec", "review", "commit", "push", "center"], c
assert "center" not in phase["cells"], "the raw shape is unchanged on purpose"
# a project whose table carries NO Center column must stay distinguishable
# from one that owes it — that is the distinction the queue reports on
bare = {"id": "P2", "cells": {"exec": "done"}, "red": None, "center": None}
assert "center" not in D.phase_cells(bare), "absent column != owed cell"
assert D.phase_cells({}) == {}, "graceful on a phase with nothing"
sys.exit(0)
VENDPY
) >"$T/py.out" 2>&1; then ok; else bad "vendored-fix #148: center reachable (see below)"; cat "$T/py.out"; fi

# ---- #150: archmap key order must be STABLE across regens -----------------
python3 - "$FIX/docs/site/center/archmap.json" <<'PY' && ok || bad "vendored-fix #150: archmap must be sort_keys'd (see above)"
import json, sys
raw = open(sys.argv[1]).read()
d = json.loads(raw)
assert list(d) == sorted(d), "top-level archmap keys are not sorted"
for k in ("entities", "function_insight", "model_insight", "guard_insight"):
    v = d.get(k)
    if isinstance(v, dict) and len(v) > 1:
        assert list(v) == sorted(v), f"{k} keys are not sorted"
# the sibling dump already sorted; the archmap now matches it, so a regen
# diff carries real change instead of ~1,750 lines of reorder noise
PY

# ---- #151: the card's own qualification must REACH the page ---------------
python3 - "$FIX/docs/site/center" <<'PY' && ok || bad "vendored-fix #151: REVIEWED + walk note must render (see above)"
import pathlib, sys, json
d = pathlib.Path(sys.argv[1])
page = (d / "feature-gadget.html").read_text()
card = (d / "cards" / "gadget.md").read_text()
assert "# REVIEWED" in card, "the fixture card must carry the section, or this "\
                             "check proves nothing"
if True:
    assert "Reviewed &mdash; what this evidence" in page \
        or "Reviewed — what this evidence" in page, \
        "a card carrying # REVIEWED must render it — candour in the source "\
        "that cannot reach the reader is not disclosure"
    body = card.split("# REVIEWED", 1)[1].strip().splitlines()[0][:40]
    assert body[:24] in page, "the REVIEWED text itself must render, not just a heading"
PY

# --- NAMED IS NOT GUARDED: the third state + prove-guard ------------------
# The guard lens joins NAMES. Whether a naming case can FAIL is a separate
# fact that only exists once a mutation was observed to turn it red. A twin
# measured its own void rate at 1 in 6, so rendering "named" as "guarded"
# overstates safety by exactly that much.
PG="$T/pg"; mk_fixture "$PG"
mkdir -p "$PG/.kdbp"
[ "$(build "$PG" "$SHELL_SRC")" = 0 ] && ok || bad "named: fixture builds"
# SILENT: with no proofs on record, a fully-named file must read `named`,
# and the word `guarded` must appear NOWHERE except inside `unguarded`.
python3 - "$PG/docs/site/center/arch-code-map.html" <<'PY' && ok || bad "named: no proofs must never render 'guarded' (see above)"
import re, sys
h = open(sys.argv[1]).read()
assert re.search(r">named \d+/\d+", h), "a fully-named file must read `named`"
bare = re.findall(r">guarded \d+/\d+", h)
assert not bare, f"claimed guarded with zero proofs on record: {bare[:3]}"
PY
# FIRE: one recorded PROVEN verdict upgrades that file to `guarded`.
python3 - "$PG" <<'PY'
import json, pathlib, re, sys
root = pathlib.Path(sys.argv[1])
h = (root / "docs/site/center/arch-code-map.html").read_text()
amap = json.loads((root / "docs/site/center/archmap.json").read_text())
target = next(f for f, v in amap["guard_insight"]["files"].items()
              if v["declared"] and not v["unguarded"])
(root / ".kdbp/guard-proofs.jsonl").write_text(json.dumps({
    "case": "C11", "symbol": target, "file": target, "line": 1,
    "mutation": "cmp ==>!=", "result": "proven",
    "when": "2026-07-26T00:00:00Z", "head": "fixture"}) + "\n")
PY
build "$PG" "$SHELL_SRC" >/dev/null
grep -qE ">guarded [0-9]+/[0-9]+" "$PG/docs/site/center/arch-code-map.html" \
  && ok || bad "named: a PROVEN record must upgrade its file to 'guarded'"
# A recorded VOID is evidence the guard does NOT hold — it must never upgrade.
python3 - "$PG" <<'PY'
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
rec = json.loads((root / ".kdbp/guard-proofs.jsonl").read_text().strip())
rec["result"] = "void"
(root / ".kdbp/guard-proofs.jsonl").write_text(json.dumps(rec) + "\n")
PY
build "$PG" "$SHELL_SRC" >/dev/null
grep -qE ">guarded [0-9]+/[0-9]+" "$PG/docs/site/center/arch-code-map.html" \
  && bad "named: a VOID verdict must NOT upgrade anything" || ok
# a corrupt line must not kill the build (graceful-absent contract)
printf 'not json\n' >> "$PG/.kdbp/guard-proofs.jsonl"
[ "$(build "$PG" "$SHELL_SRC")" = 0 ] && ok || bad "named: a malformed proof line must not break the build"

# --- prove-guard itself: PROVEN vs VOID vs refusals ------------------------
PGS="$REPO/skills/gabe-red/scripts/prove-guard.py"
PGR="$T/pgrepo"; mkdir -p "$PGR/src" "$PGR/tests"
(cd "$PGR" && git init -q . && git config user.email t@t && git config user.name t)
printf 'def is_allowed(age):\n    return age >= 18\n' > "$PGR/src/wall.py"
printf 'from src.wall import is_allowed\ndef test_real():\n    assert is_allowed(18) is True\n    assert is_allowed(17) is False\n' > "$PGR/tests/test_real.py"
printf 'from src.wall import is_allowed\ndef test_void():\n    is_allowed(18)\n    assert True\n' > "$PGR/tests/test_void.py"
(cd "$PGR" && git add -A && git commit -qm init)
BEFORE=$(md5sum "$PGR/src/wall.py" | cut -d' ' -f1)
(cd "$PGR" && python3 "$PGS" src/wall.py:2 --run "python3 -m pytest -q tests/test_real.py" --no-record >/dev/null 2>&1)
[ $? = 0 ] && ok || bad "prove-guard: a real guard must be PROVEN (exit 0)"
(cd "$PGR" && python3 "$PGS" src/wall.py:2 --run "python3 -m pytest -q tests/test_void.py" --no-record >/dev/null 2>&1)
[ $? = 2 ] && ok || bad "prove-guard: a guard that names but cannot fail must be VOID (exit 2)"
# THE property that matters most: the source is byte-identical afterwards.
[ "$(md5sum "$PGR/src/wall.py" | cut -d' ' -f1)" = "$BEFORE" ] \
  && ok || bad "prove-guard: MUST restore the mutated file byte-for-byte"
# ... including when the runner dies without returning a verdict
(cd "$PGR" && python3 "$PGS" src/wall.py:2 --run "python3 -c 'import os;os._exit(9)'" --no-record >/dev/null 2>&1)
[ "$(md5sum "$PGR/src/wall.py" | cut -d' ' -f1)" = "$BEFORE" ] \
  && ok || bad "prove-guard: must restore even when the runner crashes"
# refusals, each exit 3: already-red baseline · no syntax-safe mutation · dirty file
printf 'def test_broken():\n    assert False\n' > "$PGR/tests/test_broken.py"
(cd "$PGR" && python3 "$PGS" src/wall.py:2 --run "python3 -m pytest -q tests/test_broken.py" --no-record >/dev/null 2>&1)
[ $? = 3 ] && ok || bad "prove-guard: an ALREADY-red guard proves nothing (exit 3)"
(cd "$PGR" && python3 "$PGS" src/wall.py:1 --run "true" --no-record >/dev/null 2>&1)
[ $? = 3 ] && ok || bad "prove-guard: a line with no syntax-safe mutation must REFUSE, never mangle"
printf '# scratch\n' >> "$PGR/src/wall.py"
(cd "$PGR" && python3 "$PGS" src/wall.py:2 --run "true" --no-record >/dev/null 2>&1)
[ $? = 3 ] && ok || bad "prove-guard: a dirty file must be refused (the revert would not be exact)"
(cd "$PGR" && git checkout -- src/wall.py)

# --- evidence navigator: the census-driven mount (shell README wiring traps) --
# The census (docs/site/center/workflows/<slug>.json) drives the Evidence tab's
# Workflows section. Reference census: tests/center/fixtures/
# workflow-census-gadget.json (2 workflows, 8 states, all three proof states).

# Census ABSENT (the main fixture has none): the honest one-line absence must
# render — the debt named, the clearing command stated — and no mount, no fake
# tree, no subnav link. MUTATION that fires these: in workflow_nav_section,
# return the mounted section (or "") when the census file is missing.
grep -q 'census not captured' "$FIX/docs/site/center/feature-gadget.html" \
  && ok || bad "wf-census absent: the named absence line must render"
grep -q 'gabe-cc-update' "$FIX/docs/site/center/feature-gadget.html" \
  && ok || bad "wf-census absent: the absence line must carry the command that clears the debt"
grep -q 'ev-nav-root' "$FIX/docs/site/center/feature-gadget.html" \
  && bad "wf-census absent: no census must mean NO mount root — never a fake empty tree" || ok
grep -q 'sec-ev-flows' "$FIX/docs/site/center/feature-gadget.html" \
  && bad "wf-census absent: the pane subnav must NOT grow a Workflows link" || ok

# Census PRESENT, with two captures on disk and one referenced file that is NOT
# (gadget-gid.png is deliberately never written).
WFC="$T/wfcensus"; mk_fixture "$WFC"
mkdir -p "$WFC/docs/site/center/workflows" \
         "$WFC/docs/site/center/assets/evidence-states"
cp "$REPO/tests/center/fixtures/workflow-census-gadget.json" \
   "$WFC/docs/site/center/workflows/gadget.json"
python3 - "$WFC" <<'PY'
import base64, sys
from pathlib import Path
png = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
    "YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")
d = Path(sys.argv[1]) / "docs/site/center/assets/evidence-states"
(d / "gadget-home.png").write_bytes(png)
(d / "gadget-plus.png").write_bytes(png)
# gadget-gid.png stays missing on purpose: the demotion case below.
PY
[ "$(build "$WFC" "$SHELL_SRC")" = 0 ] && ok || { bad "wf-census: fixture must build"; cat "$T/build.out"; }
WFP="$WFC/docs/site/center/feature-gadget.html"
# The mounted shape: legend + root div + inline mount + the data INLINED.
# MUTATION: drop any one emission (root div, mount call, legend, json.dumps of
# states) from workflow_nav_section — its grep here goes red.
grep -q 'id="ev-nav-root"' "$WFP" && ok || bad "wf-census: the mount root div must render"
grep -q 'EvidenceNav.mount' "$WFP" && ok || bad "wf-census: the inline mount call must render"
grep -q 'never a staged shot' "$WFP" && ok || bad "wf-census: the legend naming the three proof states must render"
grep -q '"l":"resize"' "$WFP" && ok || bad "wf-census: the census states must be INLINED — file:// pages cannot fetch"
grep -q 'gadget-home.png' "$WFP" && ok || bad "wf-census: a capture that IS on disk must survive into the page"
grep -q 'href="#sec-ev-flows"' "$WFP" && ok || bad "wf-census: the pane's ONE subnav must gain the Workflows link"
[ "$(grep -o '<nav class="subnav">' "$WFP" | wc -l)" -le 5 ] \
  && ok || bad "wf-census: the section must join the pane's subnav, never add a second one"
# Missing capture: held out of the inlined copy, step demoted, note printed —
# never a broken <img>. MUTATION: inline census states unchecked (skip the
# center-dir probe) in workflow_nav_section.
grep -q 'gadget-gid.png' "$WFP" \
  && bad "wf-census: a capture missing on disk must be HELD OUT of the page (broken img)" || ok
grep -q '"l":"gid","st":"unpowered"' "$WFP" \
  && ok || bad "wf-census: a running step with no surviving capture must render unpowered"
grep -q 'capture missing on disk' "$T/build.out" \
  && ok || bad "wf-census: holding a capture out must print a build note, never happen silently"
# ... and the census FILE keeps the stale claim (accumulator law — the drift
# checker prices it, the build must not "fix" it).
grep -q 'gadget-gid.png' "$WFC/docs/site/center/workflows/gadget.json" \
  && ok || bad "wf-census: the build must NEVER edit the census file (accumulator)"
# Wiring trap 1, pinned: evidence-nav.js must NOT be deferred — a deferred
# asset runs after the inline mount parses, a silent blank section. MUTATION:
# add `defer` to the include in shell/feature.html.
grep -q '<script src="assets/evidence-nav.js"></script>' "$SHELL_SRC/feature.html" \
  && ok || bad "wf-nav include: shell feature.html must carry the plain include — no defer, no rename"
grep 'evidence-nav.js' "$WFP" | grep -q 'defer' \
  && bad "wf-nav include: the generated page carries a DEFERRED evidence-nav.js (silent blank section)" || ok
grep -q 'evidence-nav.js' "$WFP" \
  && ok || bad "wf-nav include: the generated page must include evidence-nav.js"

# --- census-gap action rows: a gap the navigator RENDERS is also PRICED -----
# Every class the navigator shows lands as ONE aggregated row in the Evidence
# action table (angle_rows, src "census"), fed by the SAME census_scan the
# navigator mounts from — read once, probed once, per entity per build.

# The scan is read ONCE: gadget-gid.png missing prints exactly one hold-out
# note in the WFC build. MUTATION: drop the _CENSUS_MEMO lookup in census_scan
# — angle_rows and workflow_nav_section each probe, the note prints twice.
[ "$(grep -c 'capture missing on disk' "$T/build.out")" = 1 ] \
  && ok || bad "census-rows: the census must be read+probed ONCE per entity (memo)"

# WFC (fixture census: 1 ghost · 2 authored-unpowered · 1 demoted):
# ghost class, one row naming the step. MUTATION: skip the st=="ghost" branch
# in census_scan's classification.
grep -q 'census step(s) named with no proof: resize' "$WFP" \
  && ok || bad "census-rows: ghost steps must mint ONE aggregated evidence row"
# unpowered class: BOTH steps on ONE row, census order. MUTATION: mint one row
# per step (the row would name a single step, never 'save, size').
grep -q 'census step(s) asserted but never photographed: save, size' "$WFP" \
  && ok || bad "census-rows: authored-unpowered steps must aggregate onto ONE row"
# demoted class (claimed running, shot missing on disk). MUTATION: drop
# demoted.append in census_scan's running-with-no-capture branch.
grep -q 'census capture(s) claimed but missing on disk: gid' "$WFP" \
  && ok || bad "census-rows: a demoted capture claim must mint the drift-flavored row"
# ... whose stake states the DISAGREEMENT, not the generic evidence stake.
# MUTATION: drop the stake override on the demoted add() call.
grep -q 'census claims more capture than the disk holds' "$WFP" \
  && ok || bad "census-rows: the demoted row's stake must say census claims > disk holds"
# src "census" renders its own provenance tag, never "judgment". MUTATION:
# mint census rows with the default src, or map src "census" to the judgment tag.
grep -q 'the disk probe this build">census<' "$WFP" \
  && ok || bad "census-rows: census rows must wear the census provenance tag"

# ABSENT census (the main fixture): the navigator's absence LINE (asserted
# above) AND the priced action ROW both render — two halves of one honesty.
# MUTATION: delete the status=="absent" branch in angle_rows' census block.
grep -q 'workflow census not captured' "$FIX/docs/site/center/feature-gadget.html" \
  && ok || bad "census-rows absent: the priced action row must render beside the absence line"
grep -q 'author the workflow census' "$FIX/docs/site/center/feature-gadget.html" \
  && ok || bad "census-rows absent: the row's move must name the owner command"

# UNREADABLE census: line + row, both carrying the parse failure. MUTATION:
# delete the status=="unreadable" branch in angle_rows' census block (row
# grep) or return the mounted section on parse failure (line grep).
WFU="$T/wfunread"; mk_fixture "$WFU"
mkdir -p "$WFU/docs/site/center/workflows"
printf '{ not json' > "$WFU/docs/site/center/workflows/gadget.json"
[ "$(build "$WFU" "$SHELL_SRC")" = 0 ] && ok || { bad "census-rows unreadable: fixture must build"; cat "$T/build.out"; }
WUP="$WFU/docs/site/center/feature-gadget.html"
grep -q 'census unreadable' "$WUP" \
  && ok || bad "census-rows unreadable: the navigator's named-gap line must render"
grep -q 'workflow census present but unreadable' "$WUP" \
  && ok || bad "census-rows unreadable: the priced action row must render beside the line"
grep -q 'repair the census file' "$WUP" \
  && ok || bad "census-rows unreadable: the row's move must name the owner command"

# CLEAN census (every step running, every shot on disk): ZERO census rows —
# the honest-clear case — while the navigator still mounts. MUTATION: mint any
# census row unconditionally (e.g. drop the `if census.get(...)` guards).
WFG="$T/wfgreen"; mk_fixture "$WFG"
mkdir -p "$WFG/docs/site/center/workflows" \
         "$WFG/docs/site/center/assets/evidence-states"
python3 - "$WFG" "$REPO/tests/center/fixtures/workflow-census-gadget.json" <<'PY'
import base64, json, sys
from pathlib import Path
root, src = Path(sys.argv[1]), Path(sys.argv[2])
census = json.loads(src.read_text())
png = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
    "YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")
center = root / "docs/site/center"
(center / "assets/evidence-states/gadget-green.png").write_bytes(png)
for sid, st in census["states"].items():
    if not st.get("grp"):
        st["st"] = "running"
        st["shot"] = ["assets/evidence-states/gadget-green.png"]
(center / "workflows/gadget.json").write_text(json.dumps(census, indent=1))
PY
[ "$(build "$WFG" "$SHELL_SRC")" = 0 ] && ok || { bad "census-rows clean: fixture must build"; cat "$T/build.out"; }
WGP="$WFG/docs/site/center/feature-gadget.html"
grep -q 'EvidenceNav.mount' "$WGP" \
  && ok || bad "census-rows clean: the navigator must still mount"
grep -qE 'census step\(s\)|census capture\(s\)|workflow census not captured|workflow census present but unreadable' "$WGP" \
  && bad "census-rows clean: an all-running census with shots on disk must mint ZERO census rows" || ok

echo
echo "center battery: $pass passed, $fail failed"
[ "$fail" = 0 ] || exit 1
