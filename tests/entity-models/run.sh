#!/usr/bin/env bash
# entity-models battery — the four entity models (claim · seeded · derived · proposed) and their prerequisite,
# the UNGATED element census (docs/design/entity-models/plan.md). Hermetic: a throwaway project tree + synthetic
# maps, python-stdlib only, zero-arg. Every FIRE has a SILENT sibling; every rule has a named mutation lever
# (a checker that cannot fail is non-evidence). Doctor auto-runs it (tests/*/run.sh).
#
# Phase 0 (2026-09-06) — element_census: the CLAIM ROOTS walked recursively; an unclaimed .py becomes an element
# row with its callables, tables, routes; bare files never listed; unparseable files listed with their reason;
# P5 honest-empty; byte-identical on a re-run. Mutation lever proven by hand: rglob → glob reddens the FIRE.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
GEN="$DIR/../../templates/center/generators"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
( cd "$GEN" && python3 - "$T" <<'PY'
import sys, json, pathlib
T = pathlib.Path(sys.argv[1])
sys.path.insert(0, ".")
import _a3_code as C
p = f = 0
def ck(c, m):
    global p, f
    if c: p += 1
    else: f += 1; print("  FAIL:", m)
def w(rel, text):
    q = T / rel; q.parent.mkdir(parents=True, exist_ok=True); q.write_text(text)

# ── the tree: pkg/api/a.py claimed · pkg/api/sub/b.py UNCLAIMED (recursive) · pkg/svc/c.py claimed by glob ·
#    pkg/svc/deep/d.py unclaimed with a table + a route · pkg/api/__init__.py bare · pkg/api/test_x.py a test ·
#    pkg/api/sub/bad.py unparseable · other/z.py OUTSIDE every claim root (never scanned) ──
w("pkg/api/a.py", "from fastapi import APIRouter\nrouter = APIRouter()\n@router.get('/a')\ndef get_a():\n    return 1\n")
w("pkg/api/sub/b.py", "def helper():\n    return 1\n\n\nclass Svc:\n    def run(self):\n        return 2\n\n    def __repr__(self):\n        return 'x'\n")
w("pkg/svc/c.py", "def c_one():\n    return 1\n")
w("pkg/svc/deep/d.py", "from fastapi import APIRouter\nrouter = APIRouter(prefix='/deep')\n\n\nclass Thing:\n    __tablename__ = 'things'\n\n\n@router.post('/things')\ndef make_thing():\n    return 1\n")
w("pkg/api/__init__.py", "")
w("pkg/api/test_x.py", "def test_x():\n    assert 1\n")
w("pkg/api/sub/bad.py", "def broken(:\n    pass\n")
w("other/z.py", "def zed():\n    return 1\n")
EC = {"alpha": {"api": ["pkg/api/a.py"], "services": ["pkg/svc/*.py"]}}

ck(C._claim_roots(EC) == ["pkg/api", "pkg/svc"], f"claim roots = the literal prefixes, shallowest ancestors ({C._claim_roots(EC)})")
ck(C._claim_roots({"e": {"api": ["pkg/api/a.py", "pkg/api/sub/*.py"], "web": ["web/src/**/*.ts"]}}) == ["pkg/api"],
   "a nested claim collapses into its ancestor; a frontend claim without .py never bounds the census")

out = C.element_census(T, entity_code=EC)
files = [r["file"] for r in out.get("elements", [])]
ck(files == ["pkg/api/sub/b.py", "pkg/api/sub/bad.py", "pkg/svc/deep/d.py"], f"FIRE: unclaimed files under the claim roots, recursively, sorted ({files})")
b = next(r for r in out["elements"] if r["file"] == "pkg/api/sub/b.py")
ck(b["fns"] == ["helper", "Svc.run"] and b["fns_n"] == 2 and b["tables"] == [] and b["routes"] == 0 and b["lines"] == 10, f"FIRE: callables named (no dunder), counts + lines carried ({b})")
d = next(r for r in out["elements"] if r["file"] == "pkg/svc/deep/d.py")
ck(d["tables"] == ["Thing"] and d["routes"] == 1 and d["fns"] == ["make_thing"], f"FIRE: a table class and a route in an unclaimed file are counted ({d})")
bad = next(r for r in out["elements"] if r["file"] == "pkg/api/sub/bad.py")
ck(bad["reason"].startswith("unparseable: syntax error") and bad["fns"] == [] and out["stats"]["unparseable"] == 1, f"an unparseable unclaimed file is listed with its reason and counted ({bad})")
ck(out["scanned_roots"] == ["pkg/api", "pkg/svc"] and out["claimed"] == {"py": 2} and out["stats"] == {"files": 3, "fns": 3, "tables": 1, "routes": 1, "unparseable": 1},
   f"the block carries roots · claimed count · stats ({out.get('scanned_roots')} {out.get('claimed')} {out.get('stats')})")
ck("pkg/api/__init__.py" not in files and "pkg/api/test_x.py" not in files and "other/z.py" not in files and "pkg/api/a.py" not in files,
   "SILENT: a bare __init__, a test file, a file outside every claim root and a claimed file are never listed")
ck(C.unparseable_files() == [] or all("bad.py" not in r[0] for r in C.unparseable_files()), "the census never records into unparseable_files (that list is for MAPPED files)")
ck(json.dumps(C.element_census(T, entity_code=EC), sort_keys=True) == json.dumps(out, sort_keys=True), "byte-identical on a re-run")
ck(C.element_census(T, entity_code={"alpha": {"api": ["pkg/api/a.py", "pkg/api/sub/*.py", "pkg/api/sub/bad.py"], "services": ["pkg/svc/**/*.py"]}}) == {},
   "P5 SILENT: everything claimed → no key at all (never {elements: []})")
ck(C.element_census(T, entity_code={"alpha": {"web": ["web/**/*.ts"]}}) == {}, "P5 SILENT: no python-bearing claim → {}")
ck(C.element_census(T, entity_code={}) == {}, "P5 SILENT: no config → {}")
# the mutation lever's shape: a non-recursive walk cannot see pkg/api/sub/b.py — assert the recursion is real
w("pkg/api/sub/sub2/e.py", "def e_one():\n    return 1\n")
ck("pkg/api/sub/sub2/e.py" in [r["file"] for r in C.element_census(T, entity_code=EC)["elements"]], "the walk is recursive at every depth (rglob → glob reddens this)")
ck(all("orphan" not in json.dumps(x) for x in (out, C.element_census.__doc__ or "")), "R10: no 'orphan' in the census or its doc")
print(f"entity-models battery: {p} passed, {f} failed")
sys.exit(1 if f else 0)
PY
)
