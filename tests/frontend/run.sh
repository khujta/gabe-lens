#!/usr/bin/env bash
# _a3_fe battery — the FRONTEND arm's executable contract (compiler-proven pieces + typed wires).
#
# _a3_fe.build_fe turns the compiler extractor's JSON (_a3_fe_extract.mjs) into {pieces,
# edges, homes, stats}; _a3_graph.fold_fe rides it on GABE_C4 as a SEPARATE `fe` key.
# This battery proves, HERMETICALLY on the hand-enumerated fixture app (tests/frontend/fixture:
# route + a LAZY route · 2 components · fetching hook · 2 stores · 2 types · 2 modules · story · barrel):
#   * CLASSIFICATION: every kind lands exactly once per the enumeration; the story + barrel
#     are EXCLUDED and COUNTED; helpers fold into ONE module piece per file.
#   * WIRES: renders · uses-hook · uses-store (both useContext + useXStore) · typed · fecall,
#     each resolved through the compiler's bindings (barrel + path alias followed); cross flag.
#   * SCREEN ABSORPTION: the fetch arm's `web:` node lands on the hook that fetches (sites).
#   * HONEST-EMPTY: GABE_FE_EXTRACT=0 · no web source · no typescript → present=False + reason;
#     fold_fe(fe=None) leaves GABE_C4 byte-identical; present=False → only stats.fe.
#   * DETERMINISM: byte-identical on a re-run (sorted inputs, index-triple wires).
#   * MUTATION (O2/O1): a JSX-less Pascal export is a component only on RENDERED-BY evidence (promoted +
#     counted); rendered nowhere it is fe-unknown (counted) — never folded into the file's module.
#   * LIVE (when a `typescript` resolves — GABE_TS_DIR, else the twins' web node_modules):
#     the extractor re-derives the FROZEN fixture JSON byte-for-byte; else SKIPPED by name.
# FIRE and SILENT both exercised. Exit 0 = all pass.
set -u
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
GEN="$REPO/templates/center/generators"
FIX="$REPO/tests/frontend/fixture"

# where a `typescript` can be found for the LIVE case (first hit wins; none → skip, named)
TS_DIR="${GABE_TS_DIR:-}"
if [ -z "$TS_DIR" ]; then
  for c in /home/khujta/projects/apps/gustify/apps/web /home/khujta/projects/apps/gastify/web "$REPO/docs/design/graft-adoption/spike/_build"; do
    [ -d "$c/node_modules/typescript" ] && { TS_DIR="$c"; break; }
  done
fi

python3 - "$GEN" "$FIX" "$TS_DIR" <<'PY'
import sys, json, os, copy, subprocess, shutil
from pathlib import Path
gen, fix, ts_dir = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
sys.path.insert(0, gen)
import _a3_fe, _a3_web, _a3_graph

pass_ = 0; fail = 0; skipped = []
def check(cond, msg):
    global pass_, fail
    if cond: pass_ += 1
    else: fail += 1; print("  FAIL:", msg)

X = json.load(open(fix / "extract.frozen.json"))
screens = _a3_web.web_arm(fix, {}).get("screens") or []
check(len(screens) == 1 and screens[0]["id"] == "web:src/features/recipe/useRecipe",
      "fixture: the fetch arm sees exactly the one fetching hook as a screen")
fe = _a3_fe.build_fe(X, {"recipe": {}}, screens)
P = {p["id"]: p for p in fe["pieces"]}
kind = {p["name"]: p["kind"] for p in fe["pieces"]}
home = {p["name"]: p["home"] for p in fe["pieces"]}

# ── classification: the enumeration, exactly ──────────────────────────────────────────
check(fe["stats"]["pieces"] == 22, f"22 pieces from 24 files (got {fe['stats']['pieces']})")   # +2 (review 2026-09-05): the intersection-typed store + its type · +1 (2026-09-07): the TanStack file route
check(fe["stats"]["by_kind"] == {"component": 4, "fe-type": 5, "hook": 1, "module": 5, "route": 4, "store": 3},
      f"by_kind matches the enumeration ({fe['stats']['by_kind']})")
check(kind.get("RecipeCard") == "component" and kind.get("Badge") == "component"
      and kind.get("Chip") == "component" and kind.get("RecipeDetailBody") == "component", "JSX-proven exports are components")
check(kind.get("format") == "module" and kind.get("nav") == "module", "deep app-shell helpers fold into module pieces")
check(kind.get("useRecipe") == "hook", "a useX function is a hook")
check(kind.get("ThemeContext") == "store" and kind.get("useUiStore") == "store",
      "createContext() const AND a create()-built useXStore are stores (not hooks)")
check(kind.get("router") == "route" and kind.get("HomeRoute") == "route",
      "the router config (createBrowserRouter) + a JSX export under /routes/ are routes")
check(P["fe:src/routes/settings.cards.tsx#Route"]["label"] == "/settings/cards" and P["fe:src/routes/settings.cards.tsx#Route"]["route"] == "/settings/cards"
      and P["fe:src/routes/settings.cards.tsx#Route"]["name"] == "Route" and "label" not in P["fe:src/routes/HomeRoute.tsx#HomeRoute"],
      "corpus: the TanStack file route's label is its URL (the extractor's arg0 → route_label); the JSX route keeps its export name with no label key")
check(kind.get("Recipe") == "fe-type" and kind.get("RecipeProps") == "fe-type", "type + interface are fe-types")
check(kind.get("scoring") == "module" and sorted(P["fe:src/features/recipe/scoring.ts"]["exports"]) == ["WEIGHTS", "score"],
      "plain value exports fold into ONE module piece per file, exports listed")
check(kind.get("api") == "module", "the apiFetch definition file is a module (the fetch arm skips it; this arm draws it)")
check(fe["stats"]["excluded"]["stories"] == 1 and fe["stats"]["excluded"]["barrels"] == 1,
      "the story and the barrel are EXCLUDED and COUNTED")
check(fe["stats"]["excluded"].get("scaffold_files") == 1 and fe["stats"]["excluded"].get("scaffold_exports") == 3,
      "the /spikes/ file + the stray *Spike export are design SCAFFOLD — excluded and COUNTED (batch 50)")
check(not any("Spike" in p["name"] or "/spikes/" in p["file"] for p in fe["pieces"]),
      "no spike piece may reach the graph")
check(fe["stats"]["unresolved"].get("scaffold") == 1,
      "RecipeCard's ref to the cut ScorePreviewSpike export must COUNT under unresolved.scaffold — never rewire to the principal")
check("Primary" not in kind and "index" not in kind, "no piece for a story export or a barrel")
# ── 53a: areas · API-alias collapse · fixture tagging ────────────────────────────────
check(fe["stats"]["excluded"].get("api_aliases") == 3 and "Recipe2" not in kind and "PantryItemDTO" not in kind
      and "MealDTO" not in kind,
      "a `type X = components[…]` alias is a REFERENCE to the generated contract — counted, never a piece")
check(not any(fe["pieces"][a]["name"] == "Meal" for a, b, r, *_ in fe["edges"]),
      "review 53[5]: a CUT alias's own body refs fabricate NO edge from the file's principal")
check(P["fe:src/features/recipe/recipeFixtures.ts"].get("fixture") is True,
      "a fixtures module is TAGGED showcase data (kept — real screens import fixtures)")
check(all(p.get("area") for p in fe["pieces"]) and P["fe:src/features/recipe/scoring.ts"]["area"] == "root"
      and P["fe:src/design-system/Badge.tsx#Badge"]["area"] == "root",
      "every piece carries its AREA (the S2 capsule level)")
check(P["fe:src/features/recipe/components/detail/RecipeDetailBody.tsx#RecipeDetailBody"]["area"] == "components/detail"
      and P["fe:src/design-system/atoms/Chip.tsx#Chip"]["area"] == "atoms",
      "nested feature + deep bucket areas derive from the real sub-path (review 53[8])")
check(P["fe:src/lib/utils/format.ts"]["area"] == "lib/utils" and P["fe:src/routes/utils/nav.ts"]["area"] == "routes/utils"
      and P["fe:src/routes/HomeRoute.tsx#HomeRoute"]["area"] == "routes" and P["fe:src/lib/api.ts"]["area"] == "lib",
      "review 53[6]: the synthetic app-shell home keeps its discriminating first segment — lib/utils never merges with routes/utils")
check(all("areas" in h for h in fe["homes"]), "homes count their areas")
# ── homing ─────────────────────────────────────────────────────────────────────────────
check(home.get("RecipeCard") == "fe·recipe" and home.get("useRecipe") == "fe·recipe", "features/recipe → the PAIRED fe·recipe entity (the C split — never folded into the backend twin)")
check(home.get("Badge") == "design-system", "design-system → its own shared bucket")
check(home.get("ThemeContext") == "app-shell" and home.get("router") == "app-shell", "store/ + app/ → app-shell")
check({h["id"]: h["kind"] for h in fe["homes"]} == {"app-shell": "bucket", "design-system": "bucket", "fe·recipe": "fe"},
      f"homes carry their kind (fe / bucket / candidate) ({fe['homes']})")
check(next(h for h in fe["homes"] if h["id"] == "fe·recipe").get("pair") == "recipe",
      "a paired fe home must NAME its backend twin (the join key every reader uses)")
# ── wires: every rel, resolved through bindings (barrel + alias followed) ──────────────
E = {(fe["pieces"][a]["name"], fe["pieces"][b]["name"]): r for a, b, r, *_ in fe["edges"]}
check(E.get(("RecipeCard", "Badge")) == "renders", "JSX tag → renders (through the @design-system alias)")
check(E.get(("HomeRoute", "RecipeCard")) == "renders", "renders resolved THROUGH the barrel (features/recipe/index.ts)")
check(E.get(("router", "HomeRoute")) == "renders", "a route config's JSX element → renders")
check(E.get(("RecipeCard", "useRecipe")) == "uses-hook", "hook call → uses-hook")
check(E.get(("RecipeCard", "ThemeContext")) == "uses-store", "useContext(X) → uses-store")
check(E.get(("RecipeCard", "useUiStore")) == "uses-store", "a useXStore call → uses-store (not uses-hook)")
check(E.get(("RecipeCard", "RecipeProps")) == "typed" and E.get(("useRecipe", "Recipe")) == "typed", "type refs → typed")
check(E.get(("RecipeCard", "scoring")) == "fecall", "a call into a module's helper → fecall onto the MODULE piece")
check(E.get(("useRecipe", "api")) == "fecall", "apiFetch() → fecall onto the api module")
check(E.get(("RecipeDetailBody", "Chip")) == "renders" and E.get(("nav", "format")) == "fecall",
      "the nested component renders the deep-bucket atom; a deep helper call wires module→module")
check(E.get(("scoring", "Recipe")) == "typed", "a module's type import → typed")
check(fe["stats"]["edges"] == 16 and fe["stats"]["by_rel"] == {"fecall": 3, "renders": 5, "typed": 5, "uses-hook": 1, "uses-store": 2},
      f"exactly the enumerated 16 wires — recipeFixtures typed→Recipe joined, LazyRoute→RecipeCard lazy-bound, useStatementStore typed→StatementStore ({fe['stats']['by_rel']})")
check(E.get(("LazyRoute", "RecipeCard")) == "renders" and kind.get("LazyRoute") == "route",
      "LAZY binding (2026-09-03): `const Card = lazy(() => import(\"@features/recipe/RecipeCard\").then(m => ({default: m.RecipeCard})))` binds the tag → renders")
check(fe["stats"].get("samefile_renders", 0) == 0,
      "SAME-FILE render (blocker 2) SILENT: a corpus with no co-located render adds no edge (byte-identical)")

# ── SAME-FILE render (blocker 2) FIRE: a JSX tag with NO binding is a same-file symbol; resolve it
#    to the sibling EXPORT (target_of used to drop it, mis-classifying co-located views/leaves). ──
_X2 = {"byFile": {"src/features/panel/Panel.tsx": {
    "exports": [{"name": "Panel", "kind": "function", "hasJsx": True, "jsx": ["Header", "div"]},
                {"name": "Header", "kind": "function", "hasJsx": True, "jsx": []}],
    "bindings": {}}}}
_fe2 = _a3_fe.build_fe(_X2, {"panel": {}}, [])
_E2 = {(_fe2["pieces"][a]["name"], _fe2["pieces"][b]["name"]): r for a, b, r, *_ in _fe2["edges"]}
check(_E2.get(("Panel", "Header")) == "renders" and _fe2["stats"].get("samefile_renders") == 1,
      "SAME-FILE render FIRE: a same-file JSX tag resolves to its sibling export (Panel → Header)")
check(("Panel", "div") not in _E2,
      "SAME-FILE render: an HTML tag (div) is not an export → resolves to nothing, no spurious edge")

# ── feClass — the F4 fold-control class per component (view = route-rendered · detached = no renderer · private/leaf/connector/container; D1 2026-09-05) ──
_X3 = {"byFile": {"src/features/dash/Dash.tsx": {
    "exports": [{"name": "Dash", "kind": "function", "hasJsx": True, "jsx": ["Row", "Icon"]},
                {"name": "Row", "kind": "function", "hasJsx": True, "jsx": ["Icon"]},
                {"name": "Icon", "kind": "function", "hasJsx": True, "jsx": []},
                {"name": "Lost", "kind": "function", "hasJsx": True, "jsx": []}],
    "bindings": {}},
  "src/routes/DashRoute.tsx": {
    "exports": [{"name": "DashRoute", "kind": "function", "hasJsx": True, "jsx": ["Dash"]}],
    "bindings": {"Dash": {"file": "src/features/dash/Dash.tsx", "name": "Dash"}}}}}
_fe3 = _a3_fe.build_fe(_X3, {"dash": {}}, [])
_cls = {p["name"]: p.get("feClass") for p in _fe3["pieces"] if p["kind"] == "component"}
check(_cls.get("Dash") == "view" and _cls.get("Row") == "private" and _cls.get("Icon") == "leaf" and _cls.get("Lost") == "detached",
      "feClass (D1 2026-09-05): rendered by a ROUTE = view · 0 render-parents = detached (never a view) · 1 = private · 2+ shared no-data = leaf")
check(_fe3["stats"]["by_feclass"] == {"leaf": 1, "detached": 1, "private": 1, "view": 1},
      "feClass: the by_feclass stat tallies the component classes incl. detached")

# ── STORE DETECTOR (F2): a call reaching a store/fetch is STATE; cx/util plumbing is CHROME (cx=fecall fix) ──
_X4 = {"byFile": {
    "src/store/dash.ts": {"exports": [{"name": "useDashStore", "kind": "call:create", "hasJsx": False}], "bindings": {}},
    "src/util/cx.ts": {"exports": [{"name": "cx", "kind": "function", "hasJsx": False}], "bindings": {}},
    "src/features/dash/Panel.tsx": {"exports": [
        {"name": "Panel", "kind": "function", "hasJsx": True, "jsx": ["Child"], "calls": ["useDashStore", "cx"]},
        {"name": "Child", "kind": "function", "hasJsx": True, "jsx": []}],
        "bindings": {"useDashStore": {"file": "src/store/dash.ts", "name": "useDashStore"},
                     "cx": {"file": "src/util/cx.ts", "name": "cx"}}}}}
_fe4 = _a3_fe.build_fe(_X4, {"dash": {}}, [])
_pan4 = next((p for p in _fe4["pieces"] if p["name"] == "Panel"), None)
check(_pan4 and _pan4.get("state") is True,
      "STORE DETECTOR: a component whose call reaches a store TOUCHES STATE")
check(_fe4["stats"]["by_channel"] == {"chrome": 1, "read": 1, "write": 0},
      "STORE DETECTOR: the store call is READ (touches state, no write reached), cx is CHROME (cx=fecall fixed)")
# the by_channel STAT above is computed off the edge DICTS; the RENDERER instead reads the channel
# off the serialized wire's 4th slot (e[3]) — assert THAT, or a serialization drop ships green.
_ch4 = {(_fe4["pieces"][e[0]]["name"], _fe4["pieces"][e[1]]["name"]): (e[3] if len(e) > 3 else None)
        for e in _fe4["edges"]}
check(_ch4.get(("Panel", "useDashStore")) == "read" and _ch4.get(("Panel", "cx")) == "chrome"
      and _ch4.get(("Panel", "Child")) is None,
      "STORE DETECTOR: the channel SERIALIZES onto the wire at e[3] (store→read, cx→chrome) and a "
      "renders wire carries NO 4th slot — the exact shape chrome:(e[3]===\"chrome\") consumes")
# ── CACHE DETECTOR (F1): a hook calling a query-library idiom (useQuery/useSWR) with no project
#    binding is a CACHE sink → it touches server state, so its caller's wire is STATE not chrome. ──
_X5 = {"byFile": {
    "src/features/me/useMe.ts": {"exports": [{"name": "useMe", "kind": "function", "hasJsx": False,
        "calls": ["useQuery"]}], "bindings": {"useQuery": {"ext": True}}},   # react-query import → ext, no project piece
    "src/features/me/MeCard.tsx": {"exports": [{"name": "MeCard", "kind": "function", "hasJsx": True,
        "jsx": [], "calls": ["useMe"]}], "bindings": {"useMe": {"file": "src/features/me/useMe.ts", "name": "useMe"}}}}}
_fe5 = _a3_fe.build_fe(_X5, {"me": {}}, [])
_useMe = next((p for p in _fe5["pieces"] if p["name"] == "useMe"), None)
_meCard = next((p for p in _fe5["pieces"] if p["name"] == "MeCard"), None)
check(_useMe and _useMe.get("cache") is True and _fe5["stats"]["cache_pieces"] == 1,
      "CACHE DETECTOR: a hook calling useQuery (no project binding) is a cache sink (react-query idiom)")
check(_meCard and _meCard.get("state") is True,
      "CACHE DETECTOR: the component calling that cache hook TOUCHES state (reachability through the sink)")
_ch5 = {(_fe5["pieces"][e[0]]["name"], _fe5["pieces"][e[1]]["name"]): (e[3] if len(e) > 3 else None) for e in _fe5["edges"]}
check(_ch5.get(("MeCard", "useMe")) == "read",
      "CACHE DETECTOR: the MeCard→useMe wire serializes channel=read (a query hook touches state, not chrome)")
# honest-empty: a project with NO query lib gets NO `cache` key on any piece (byte-identical)
_X6 = {"byFile": {"src/features/x/useX.ts": {"exports": [{"name": "useX", "kind": "function",
    "hasJsx": False, "calls": ["useState", "cx"]}], "bindings": {"cx": {"ext": True}}}}}
_fe6 = _a3_fe.build_fe(_X6, {"x": {}}, [])
check(all("cache" not in p for p in _fe6["pieces"]) and _fe6["stats"]["cache_pieces"] == 0,
      "CACHE DETECTOR honest-empty: no query-lib call → no `cache` key on any piece (byte-identical)")

# ── FE d2w WRITE DETECTOR: the read/write direction is the HTTP METHOD of the fetch a piece reaches
#    (via the web bridge's per-site method) — deterministic + library-agnostic, NEVER a hook name. ──
_X7 = {"byFile": {
    "src/features/save/useSave.ts": {"exports": [{"name": "useSave", "kind": "function", "hasJsx": False,
        "calls": ["apiFetch"]}], "bindings": {"apiFetch": {"ext": True}}},
    "src/features/save/SaveBtn.tsx": {"exports": [{"name": "SaveBtn", "kind": "function", "hasJsx": True,
        "jsx": [], "calls": ["useSave"]}], "bindings": {"useSave": {"file": "src/features/save/useSave.ts", "name": "useSave"}}}}}
_screens7 = [{"id": "web:src/features/save/useSave", "file": "src/features/save/useSave.ts",
              "calls": [{"method": "POST", "path": "/save"}], "dynamic": 0}]
_fe7 = _a3_fe.build_fe(_X7, {"save": {}}, _screens7)
_useSave = next((p for p in _fe7["pieces"] if p["name"] == "useSave"), None)
_saveBtn = next((p for p in _fe7["pieces"] if p["name"] == "SaveBtn"), None)
check(_useSave and _useSave.get("wsites") == 1 and _fe7["stats"]["write_pieces"] == 2,
      "FE d2w WRITE: a POST fetch makes its piece a write sink (wsites), and the write spine reaches 2 pieces (sink + caller)")
check(_saveBtn and _saveBtn.get("write") is True and _saveBtn.get("state") is True,
      "FE d2w WRITE: the component reaching the write-fetch is on the WRITE spine (reachability)")
check(_useSave.get("fed2w") == 0 and _saveBtn.get("fed2w") == 1 and _fe7["stats"]["fed2w_max"] == 1,
      "FE d2w DEPTH: the write sink is fed2w 0 (at the write), its caller fed2w 1 (one hop) — the gradient's number")
_ch7 = {(_fe7["pieces"][e[0]]["name"], _fe7["pieces"][e[1]]["name"]): (e[3] if len(e) > 3 else None) for e in _fe7["edges"]}
check(_ch7.get(("SaveBtn", "useSave")) == "write",
      "FE d2w WRITE: the SaveBtn→useSave wire serializes channel=write (the HTTP verb, not a hook name)")
# a GET-only fetch is a READ (no write flag) — the method, not the presence of a fetch, decides
_X8 = {"byFile": {"src/features/list/List.tsx": {"exports": [{"name": "List", "kind": "function",
    "hasJsx": True, "jsx": [], "calls": ["apiFetch"]}], "bindings": {"apiFetch": {"ext": True}}}}}
_screens8 = [{"id": "web:src/features/list/List", "file": "src/features/list/List.tsx",
              "calls": [{"method": "GET", "path": "/list"}], "dynamic": 0}]
_fe8 = _a3_fe.build_fe(_X8, {"list": {}}, _screens8)
_ls = next((p for p in _fe8["pieces"] if p["name"] == "List"), None)
check(_ls and _ls.get("screen") and "wsites" not in _ls and "write" not in _ls and "fed2w" not in _ls
      and _fe8["stats"]["write_pieces"] == 0 and _fe8["stats"]["fed2w_max"] == 0,
      "FE d2w READ: a GET-only fetch carries NO write/fed2w — the method decides, honest-empty of writes")

check(fe["stats"]["cross"] == 7, f"7 wires cross homes (got {fe['stats']['cross']})")
check(all(isinstance(e, list) and 3 <= len(e) <= 4 and isinstance(e[0], int) for e in fe["edges"]),
      "wires are COMPACT index triples (a call wire may carry a 4th channel element: state/chrome)")
check(fe["stats"]["unresolved"] == {"ext": 0, "no_piece": 0, "scaffold": 1, "alias": 1},
      "the scaffold ref AND RecipeDetailBody's ref into the cut Recipe2 alias each COUNT, named — never dropped silently")
# ── screen absorption ──────────────────────────────────────────────────────────────────
hook = P["fe:src/features/recipe/useRecipe.ts#useRecipe"]
check(hook.get("screen") == "web:src/features/recipe/useRecipe" and hook.get("sites") == 1,
      "the fetching hook carries the absorbed web node id + its fetch-site count")
check(fe["stats"]["screens_absorbed"] == 1, "screens_absorbed counts it")
check("screen" not in P["fe:src/features/recipe/RecipeCard.tsx#RecipeCard"], "a non-fetching piece carries no screen")
# ── determinism ────────────────────────────────────────────────────────────────────────
fe2 = _a3_fe.build_fe(json.loads(json.dumps(X)), {"recipe": {}}, screens)
check(json.dumps(fe, sort_keys=True) == json.dumps(fe2, sort_keys=True), "byte-identical on a re-run")
# ── MUTATION: a Pascal export WITHOUT JSX — rendered-by evidence decides (O2/O1, 2026-09-03) ────────────
Xm = copy.deepcopy(X)
for ex in Xm["byFile"]["src/design-system/Badge.tsx"]["exports"]:
    if ex["name"] == "Badge": ex["hasJsx"] = False; ex["jsx"] = []
fm = _a3_fe.build_fe(Xm, {"recipe": {}}, screens)
km = {p["name"]: p["kind"] for p in fm["pieces"]}
check(km.get("Badge") == "component" and fm["stats"]["promoted"] == 1 and fm["stats"]["excluded"]["pascal_no_jsx"] == 0,
      "MUTATION (O2): JSX removed from Badge → STILL a component, promoted on rendered-by evidence (RecipeCard renders <Badge/>); nothing falls through")
Em = {(fm["pieces"][a]["name"], fm["pieces"][b]["name"]): r for a, b, r, *_ in fm["edges"]}
check(Em.get(("RecipeCard", "Badge")) == "renders", "MUTATION (O2): the renders edge binds onto the promoted component")
# …and with the render ALSO gone nothing proves it → fe-unknown, counted (O1) — never the file's module
Xu = copy.deepcopy(Xm)
for ex in Xu["byFile"]["src/features/recipe/RecipeCard.tsx"]["exports"]:
    if ex["name"] == "RecipeCard": ex["jsx"] = [t for t in ex.get("jsx", []) if t != "Badge"]
fu = _a3_fe.build_fe(Xu, {"recipe": {}}, screens)
ku = {p["name"]: p["kind"] for p in fu["pieces"]}
check(ku.get("Badge") == "fe-unknown" and fu["stats"]["excluded"]["pascal_no_jsx"] == 1 and fu["stats"]["promoted"] == 0,
      "MUTATION (O1): JSX removed AND no file renders it → fe-unknown, counted in pascal_no_jsx — an honest kind, not a module")
# ── the C4 fold ────────────────────────────────────────────────────────────────────────
base = {"version": 1, "stats": {"entities": 1}, "l2": {}}
check(json.dumps(_a3_graph.fold_fe(copy.deepcopy(base), None), sort_keys=True) == json.dumps(base, sort_keys=True),
      "fold_fe(None) leaves GABE_C4 byte-identical")
off = _a3_graph.fold_fe(copy.deepcopy(base), {"present": False, "reason": "no web source"})
check("fe" not in off and off["stats"]["fe"] == {"present": False, "reason": "no web source"},
      "present=False → only stats.fe names the absence")
on = _a3_graph.fold_fe(copy.deepcopy(base), {**fe, "present": True, "reason": "typescript x"})
check(sorted(on["fe"]) == ["edges", "homes", "pieces"] and on["stats"]["fe"]["present"] and on["stats"]["fe"]["pieces"] == 22,
      "present → the `fe` key (pieces · edges · homes) + stats.fe")
check("l2" in on and on["l2"] == {}, "the fold never touches l2")
# ── honest-empty arm states ────────────────────────────────────────────────────────────
os.environ["GABE_FE_EXTRACT"] = "0"
d = _a3_fe.fe_arm(fix, {"recipe": {}}, screens)
check(d == {"present": False, "reason": "extract disabled (GABE_FE_EXTRACT=0)"}, f"GABE_FE_EXTRACT=0 → disabled, named ({d})")
del os.environ["GABE_FE_EXTRACT"]
nw = _a3_fe.fe_arm(Path("/nonexistent-root"), {})
check(nw == {"present": False, "reason": "no web source"}, f"no web source → present=False, named ({nw})")
os.environ["GABE_TS_DIR"] = "/nonexistent-ts"
nts = _a3_fe.fe_arm(fix, {"recipe": {}}, screens)
check(nts.get("present") is False and "typescript not resolvable" in nts.get("reason", ""),
      f"no typescript → present=False with the extractor's reason ({nts})")
del os.environ["GABE_TS_DIR"]
# ── LIVE: the extractor re-derives the frozen JSON (when a typescript resolves) ─────────
if ts_dir and shutil.which("node"):
    os.environ["GABE_TS_DIR"] = ts_dir
    live = _a3_fe.fe_arm(fix, {"recipe": {}}, screens)
    del os.environ["GABE_TS_DIR"]
    check(live.get("present") is True, f"LIVE: the arm runs on the fixture ({live.get('reason')})")
    check("borrowed via GABE_TS_DIR" in (live.get("reason") or ""), f"LIVE (2026-09-06): a GABE_TS_DIR run SAYS the typescript was borrowed ({live.get('reason')})")
    same = json.dumps({k: live.get(k) for k in ("pieces", "edges", "homes")}, sort_keys=True) == \
           json.dumps({k: fe[k] for k in ("pieces", "edges", "homes")}, sort_keys=True)
    check(same, "LIVE: the compiler pass re-derives the FROZEN fixture graph exactly (pieces · edges · homes)")
    # ── review finding 2: a files:[]+references tsconfig (the default Vite React+TS stub) must be FOLLOWED ──
    import tempfile
    _td = Path(tempfile.mkdtemp())
    try:
        (_td / "src").mkdir()
        (_td / "src" / "Thing.tsx").write_text("export function Thing(){ return null as any }\n")
        (_td / "package.json").write_text('{"name":"refstub","version":"0.0.0","dependencies":{"react":"*"}}\n')
        (_td / "tsconfig.json").write_text('{"files":[],"references":[{"path":"./tsconfig.app.json"}]}\n')
        (_td / "tsconfig.app.json").write_text('{"compilerOptions":{"jsx":"react-jsx","module":"esnext","moduleResolution":"bundler","skipLibCheck":true},"include":["src"]}\n')
        os.environ["GABE_TS_DIR"] = ts_dir
        _ref = _a3_fe.fe_arm(_td, {}, [])
        del os.environ["GABE_TS_DIR"]
        check(_ref.get("present") is True and any("Thing" in p.get("name", "") for p in _ref.get("pieces", [])),
              f"LIVE: a files:[]+references tsconfig is FOLLOWED — frontend recovered, not silently dropped ({_ref.get('reason')})")
        # and a tsconfig that genuinely matches 0 files degrades HONESTLY (present=False), never present=True/0
        (_td / "tsconfig.json").write_text('{"include":["does-not-exist"]}\n')
        (_td / "tsconfig.app.json").unlink()
        os.environ["GABE_TS_DIR"] = ts_dir
        _emp = _a3_fe.fe_arm(_td, {}, [])
        del os.environ["GABE_TS_DIR"]
        check(_emp.get("present") is False and "0 source files" in _emp.get("reason", ""),
              f"LIVE: a tsconfig matching 0 files → present=False (honest-empty, not a false success) ({_emp.get('reason')})")
    finally:
        shutil.rmtree(_td, ignore_errors=True)
else:
    skipped.append("LIVE extractor case — no `typescript` resolvable (set GABE_TS_DIR)")


# ── O2 · RENDERED-BY promotion + O1 · fe-unknown (2026-09-03) — a Pascal .tsx function/class export with NO JSX of its own:
#    rendered as a tag anywhere → COMPONENT (delegated render · headless effect) and the renders edge BINDS;
#    rendered nowhere → fe-unknown, an honest kind — never the file's module. Both counted. ──
_X8 = {"byFile": {
    "src/routes/screens.tsx": {"exports": [{"name": "RecipesRoute", "kind": "function", "hasJsx": True, "jsx": ["BrowseContainer"]}],
        "bindings": {"BrowseContainer": {"file": "src/features/cook/BrowseContainer.tsx", "name": "BrowseContainer"}}},
    "src/features/cook/BrowseContainer.tsx": {"exports": [{"name": "BrowseContainer", "kind": "function", "hasJsx": False, "calls": ["renderBrowseView"]}],
        "bindings": {"renderBrowseView": {"file": "src/features/cook/renderBrowseView.tsx", "name": "renderBrowseView"}}},
    "src/features/cook/renderBrowseView.tsx": {"exports": [{"name": "renderBrowseView", "kind": "function", "hasJsx": True, "jsx": []}], "bindings": {}},
    "src/i18n/Orphan.tsx": {"exports": [{"name": "Orphan", "kind": "function", "hasJsx": False}], "bindings": {}},
    "src/features/cook/helpers.ts": {"exports": [{"name": "score", "kind": "function", "hasJsx": False}], "bindings": {}}}}
_fe8 = _a3_fe.build_fe(_X8, {"cook": {}}, [])
_k8 = {p["name"]: p["kind"] for p in _fe8["pieces"]}
_E8 = {(_fe8["pieces"][a]["name"], _fe8["pieces"][b]["name"]): r for a, b, r, *_ in _fe8["edges"]}
check(_k8.get("BrowseContainer") == "component" and _fe8["stats"].get("promoted") == 1,
      f"O2 FIRE: a JSX-less Pascal .tsx export RENDERED by a route is promoted to component (+ counted) ({_k8})")
check(_E8.get(("RecipesRoute", "BrowseContainer")) == "renders",
      "O2: the promotion binds the route's renders edge — the severed view chain is restored")
check(_k8.get("Orphan") == "fe-unknown" and _fe8["stats"]["excluded"]["pascal_no_jsx"] == 1
      and _fe8["stats"]["by_kind"].get("fe-unknown") == 1,
      "O1 FIRE: a JSX-less Pascal .tsx export rendered NOWHERE is fe-unknown — an honest kind, never a module claim (+ counted)")
check(_k8.get("helpers") == "module" and "score" not in _k8,
      "O2/O1 SILENT: a camelCase helper still folds into its file's module piece")
_mc8 = {p["name"]: p.get("mclass") for p in _fe8["pieces"] if p["kind"] == "module"}
check(_mc8.get("renderBrowseView") == "render-fn" and _mc8.get("helpers") == "logic",
      f"mclass: a JSX-bearing camelCase .tsx module is render-fn · a feature helper is logic ({_mc8})")
check(all("jsx" not in p for p in _fe8["pieces"]), "mclass: the transient jsx marker never ships on a piece")
# ── module CLASSES — api (fetch sites absorbed from the web arm) · model · config · lib, by directory IDIOM ──
_X9 = {"byFile": {
    "src/lib/api/client.ts": {"exports": [{"name": "getRecipes", "kind": "function", "hasJsx": False}], "bindings": {}},
    "src/features/cook/model/mappers.ts": {"exports": [{"name": "mapRecipe", "kind": "function", "hasJsx": False}], "bindings": {}},
    "src/app/queryClient.ts": {"exports": [{"name": "queryClient", "kind": "const", "hasJsx": False}], "bindings": {}},
    "src/design-system/cx.ts": {"exports": [{"name": "cx", "kind": "function", "hasJsx": False}], "bindings": {}}}}
_fe9 = _a3_fe.build_fe(_X9, {"cook": {}}, [{"id": "web:src/lib/api/client", "calls": [{"method": "GET", "path": "/recipes"}]}])
_mc9 = {p["name"]: p.get("mclass") for p in _fe9["pieces"] if p["kind"] == "module"}
check(_mc9 == {"client": "api", "mappers": "model", "queryClient": "config", "cx": "lib"},
      f"mclass: api (fetch sites) · model (/model/) · config (/app/) · lib (/design-system/) ({_mc9})")
check(_fe9["stats"]["by_mclass"] == {"api": 1, "config": 1, "lib": 1, "model": 1},
      "mclass: the by_mclass stat tallies module classes")
for s in skipped: print("  SKIP ⚠:", s)   # the doctor-recognized coverage-skip marker (else a skipped LIVE-extractor case reads as false CLEAN)
# ── PASS 2 (review 2026-09-06): a Next.js App Router page file's default export IS the route, whatever its name ──
_X13 = {"byFile": {
    "web/src/app/chat/page.tsx": {"exports": [{"name": "ChatHome", "kind": "function", "hasJsx": True, "isDefault": True}], "bindings": {}},
    "web/src/app/chat/layout.tsx": {"exports": [{"name": "ChatLayout", "kind": "function", "hasJsx": True, "isDefault": True}], "bindings": {}},
    "web/src/components/chat/ChatHome.tsx": {"exports": [{"name": "ChatHome", "kind": "function", "hasJsx": True, "isDefault": True}], "bindings": {}},
    "web/src/app/chat/helper.tsx": {"exports": [{"name": "ChatHelper", "kind": "function", "hasJsx": True}], "bindings": {}}}}
_fe13 = _a3_fe.build_fe(_X13, {}, [])
_k13 = {p["file"] + "#" + p["name"]: p["kind"] for p in _fe13["pieces"]}
check(_k13.get("web/src/app/chat/page.tsx#ChatHome") == "route" and _k13.get("web/src/app/chat/layout.tsx#ChatLayout") == "route",
      f"pass 2 FIRE: app/**/page.tsx + layout.tsx default exports are routes ({_k13})")
check(_k13.get("web/src/components/chat/ChatHome.tsx#ChatHome") == "component" and _k13.get("web/src/app/chat/helper.tsx#ChatHelper") == "component",
      f"pass 2 SILENT: the same component outside a page file, and a non-role file under app/, stay components ({_k13})")

# ── a route's LABEL is its URL path (tier0 review 2026-09-07): the file-router literal first, the file by convention second, the export name last ──
_X14 = {"byFile": {
    "frontend/src/routes/_layout/admin.tsx": {"exports": [{"name": "Route", "kind": "call:createFileRoute", "arg0": "/_layout/admin", "hasJsx": False}], "bindings": {}},
    "frontend/src/routes/_layout/index.tsx": {"exports": [{"name": "Route", "kind": "call:createFileRoute", "arg0": "/_layout/", "hasJsx": False}], "bindings": {}},
    "frontend/src/routes/_layout.tsx": {"exports": [{"name": "Route", "kind": "call:createFileRoute", "arg0": "/_layout", "hasJsx": False}], "bindings": {}},
    "frontend/src/routes/category.$key.tsx": {"exports": [{"name": "Route", "kind": "call:createFileRoute", "arg0": "/category/$key", "hasJsx": False}], "bindings": {}},
    "frontend/src/routes/__root.tsx": {"exports": [{"name": "Route", "kind": "call:createRootRoute", "hasJsx": False}], "bindings": {}},
    "frontend/src/routes/settings.cards.tsx": {"exports": [{"name": "Route", "kind": "call:createFileRoute", "hasJsx": False}], "bindings": {}},
    "web/src/app/(marketing)/chat/[id]/page.tsx": {"exports": [{"name": "ChatPage", "kind": "function", "hasJsx": True, "isDefault": True}], "bindings": {}},
    "apps/web/src/routes/screens.tsx": {"exports": [{"name": "HomeRoute", "kind": "function", "hasJsx": True}], "bindings": {}},
    "apps/web/src/routes/router.tsx": {"exports": [{"name": "router", "kind": "call:createBrowserRouter", "hasJsx": True}], "bindings": {}}}}
_fe14 = _a3_fe.build_fe(_X14, {}, [])
_l14 = {p["file"]: (p.get("label"), p.get("route"), p["name"]) for p in _fe14["pieces"] if p["kind"] == "route"}
check(_l14.get("frontend/src/routes/_layout/admin.tsx") == ("/admin", "/_layout/admin", "Route")
      and _l14.get("frontend/src/routes/_layout/index.tsx") == ("/", "/_layout/", "Route")
      and _l14.get("frontend/src/routes/category.$key.tsx") == ("/category/:key", "/category/$key", "Route"),
      f"route label FIRE: the file-router literal becomes the label — pathless `_layout` dropped, `$key` → `:key`, `/_layout/` → `/`; the raw literal rides as `route`, `name` stays the export ({_l14})")
check(_l14.get("frontend/src/routes/_layout.tsx") == ("/_layout", "/_layout", "Route")
      and _l14.get("frontend/src/routes/__root.tsx") == ("root shell", None, "Route")
      and _l14.get("frontend/src/routes/settings.cards.tsx") == ("/settings/cards", None, "Route")
      and _l14.get("web/src/app/(marketing)/chat/[id]/page.tsx") == ("/chat/:id", None, "ChatPage"),
      f"route label FIRE: a pathless-only literal keeps its raw form, the root route reads `root shell`, a file route without a literal and a Next page take the FILE by the router's convention ({_l14})")
check(_l14.get("apps/web/src/routes/screens.tsx") == (None, None, "HomeRoute") and _l14.get("apps/web/src/routes/router.tsx") == (None, None, "router"),
      f"route label SILENT: a react-router JSX route and a createBrowserRouter config carry NO label key — the export name stays the label, the example estate is byte-identical ({_l14})")

# ── D6 (review 2026-09-05): NO feature layout → the config's web claims home the pieces; a feature layout wins outright ──
_X10 = {"byFile": {
    "web/src/hooks/useGroups.ts": {"exports": [{"name": "useGroups", "kind": "function", "hasJsx": False}], "bindings": {}},
    "web/src/lib/http.ts": {"exports": [{"name": "http", "kind": "function", "hasJsx": False}], "bindings": {}}}}
_ENT10 = {"group-share": {"files": [["web", "web/src/hooks/useGroups.ts", 10], ["api", "backend/app/api/groups.py", 900]]}}
_fe10 = _a3_fe.build_fe(_X10, _ENT10, [])
_h10 = {p["name"]: p["home"] for p in _fe10["pieces"]}
check(_h10 == {"useGroups": "fe·group-share", "http": "app-shell"} and _fe10["stats"].get("homing") == "config",
      f"D6 FIRE: a flat src/ tree homes by the config's web claims — useGroups → fe·group-share, the unclaimed lib stays app-shell ({_h10}, {_fe10['stats'].get('homing')})")
check(any(h["id"] == "fe·group-share" and h.get("pair") == "group-share" and h["kind"] == "fe" for h in _fe10["homes"])
      and all(p.get("homed_by") == "config" for p in _fe10["pieces"] if p["home"] == "fe·group-share"),
      "D6: a config-homed piece PAIRS to its backend twin like a layout home, and says homed_by=config")
_X11 = dict(_X10); _X11 = {"byFile": dict(_X10["byFile"], **{"src/features/cook/useCook.ts": {"exports": [{"name": "useCook", "kind": "function", "hasJsx": False}], "bindings": {}}})}
_fe11 = _a3_fe.build_fe(_X11, dict(_ENT10, cook={}), [])
_h11 = {p["name"]: p["home"] for p in _fe11["pieces"]}
check(_h11["useCook"] == "fe·cook" and _h11["useGroups"] == "app-shell" and _fe11["stats"].get("homing") == "layout",
      f"D6 SILENT: a feature layout wins — the config claim is NOT consulted, useGroups stays app-shell ({_h11})")
_fe12 = _a3_fe.build_fe(_X10, frozenset({"group-share"}), [])
check(all(p["home"] == "app-shell" for p in _fe12["pieces"]) and _fe12["stats"].get("homing") == "layout",
      "D6: entities as a bare slug set carry no claims — layout only, honest app-shell")
check(fe["stats"].get("homing") == "layout", "D6: the fixture (features/ layout) reads homing=layout — byte-identical homes")
check(all("homed_by" not in p for p in fe["pieces"]) and all(p.get("homed_by") == "config" for p in _fe10["pieces"] if p["home"].startswith("fe·")),
      "Step 7: homed_by rides only config-homed pieces — absent on the layout estate, present on the config one")
# ── D3 (2026-09-05): a screen file with several hooks — the call's `export` decides which piece carries the screen ──
_X7 = {"byFile": {"src/features/pantry/usePantryMutations.ts": {
    "exports": [{"name": "useApplyReset", "kind": "function", "hasJsx": False, "jsx": []},
                {"name": "useCreatePantryItem", "kind": "function", "hasJsx": False, "jsx": []}],
    "bindings": {}}}}
_S7 = [{"id": "web:src/features/pantry/usePantryMutations", "file": "src/features/pantry/usePantryMutations.ts",
        "calls": [{"method": "POST", "path": "/pantry/items", "export": "useCreatePantryItem"}], "dynamic": 0}]
_fe7 = _a3_fe.build_fe(_X7, {"pantry": {}}, _S7)
_P7 = {p["name"]: p for p in _fe7["pieces"]}
check(_P7["useCreatePantryItem"].get("screen") == "web:src/features/pantry/usePantryMutations" and _P7["useCreatePantryItem"].get("wsites") == 1
      and not _P7["useApplyReset"].get("screen"),
      "D3 FIRE: the export that fetched carries the screen (+ its write site); the file's first hook does not")
check(_fe7["stats"].get("screens_by_export") == 1, "D3: stats.screens_by_export counts the per-export absorption")
_S7b = [{"id": "web:src/features/pantry/usePantryMutations", "file": "src/features/pantry/usePantryMutations.ts",
         "calls": [{"method": "POST", "path": "/pantry/items"}], "dynamic": 0}]
_fe7b = _a3_fe.build_fe(_X7, {"pantry": {}}, _S7b)
_P7b = {p["name"]: p for p in _fe7b["pieces"]}
check(_P7b["useApplyReset"].get("screen") and not _P7b["useCreatePantryItem"].get("screen") and _fe7b["stats"].get("screens_by_export") == 0,
      "D3 SILENT (the floor): a call with no export still lands on the file's principal piece")
_S7c = [{"id": "web:src/features/pantry/usePantryMutations", "file": "src/features/pantry/usePantryMutations.ts", "calls": [], "dynamic": 1}]
_fe7c = _a3_fe.build_fe(_X7, {"pantry": {}}, _S7c)
_P7c = {p["name"]: p for p in _fe7c["pieces"]}
check(_P7c["useApplyReset"].get("screen") == "web:src/features/pantry/usePantryMutations" and _P7c["useApplyReset"].get("sites") == 0 and _fe7c["stats"].get("screens_absorbed") == 1,
      "D3 regression pin: a DYNAMIC-only screen (no literal call) is still absorbed by the file's principal — the web node never strands (webLeft stayed 0 on the example)")

# ── D2 (2026-09-05): HOOK ROLES — one per hook by precedence, from wires the arm already draws ──
_X8 = {"byFile": {
    "src/features/r/useFetchR.ts": {"exports": [{"name": "useFetchR", "kind": "function", "hasJsx": False, "calls": []}], "bindings": {}},
    "src/features/r/useStreamR.ts": {"exports": [{"name": "useStreamR", "kind": "function", "hasJsx": False, "calls": []}], "bindings": {}},
    "src/features/r/useLocaleStore.ts": {"exports": [{"name": "useLocaleStore", "kind": "function", "hasJsx": False, "calls": ["create"]}], "bindings": {"create": {"ext": True}}},
    "src/features/r/useLocale.ts": {"exports": [{"name": "useLocale", "kind": "function", "hasJsx": False, "calls": ["useLocaleStore"]}], "bindings": {"useLocaleStore": {"file": "src/features/r/useLocaleStore.ts", "name": "useLocaleStore"}}},
    "src/features/r/useDeriveR.ts": {"exports": [{"name": "useDeriveR", "kind": "function", "hasJsx": False, "calls": ["useMemo"]}], "bindings": {"useMemo": {"ext": True}}},
    "src/features/r/useComboR.ts": {"exports": [{"name": "useComboR", "kind": "function", "hasJsx": False, "calls": ["useDeriveR"]}], "bindings": {"useDeriveR": {"file": "src/features/r/useDeriveR.ts", "name": "useDeriveR"}}},
    "src/lib/analytics.ts": {"exports": [{"name": "track", "kind": "function", "hasJsx": False, "calls": []}], "bindings": {}},
    "src/features/r/useTrackR.ts": {"exports": [{"name": "useTrackR", "kind": "function", "hasJsx": False, "calls": ["track"]}], "bindings": {"track": {"file": "src/lib/analytics.ts", "name": "track"}}}}}
_S8 = [{"id": "web:src/features/r/useFetchR", "file": "src/features/r/useFetchR.ts", "calls": [{"method": "GET", "path": "/r", "export": "useFetchR"}], "dynamic": 0},
       {"id": "web:src/features/r/useStreamR", "file": "src/features/r/useStreamR.ts", "calls": [{"method": "GET", "path": "/r/stream", "export": "useStreamR", "sse": True}], "dynamic": 0}]
_fe8 = _a3_fe.build_fe(_X8, {"r": {}}, _S8)
_H8 = {p["name"]: p.get("hrole") for p in _fe8["pieces"] if p["kind"] == "hook"}
check(_H8 == {"useFetchR": "fetcher", "useStreamR": "streamer", "useLocale": "store", "useDeriveR": "deriver", "useComboR": "orchestrator", "useTrackR": "effect"},
      "HOOK ROLES (D2): fetcher · streamer · store · orchestrator · effect · deriver from wires — got " + str(_H8))
check(_fe8["stats"].get("by_hrole") == {"deriver": 1, "effect": 1, "fetcher": 1, "orchestrator": 1, "store": 1, "streamer": 1},
      "HOOK ROLES: stats.by_hrole tallies the six")
check(not any("hrole" in p for p in _fe8["pieces"] if p["kind"] != "hook"), "HOOK ROLES: only hooks carry a role")
_fe8m = _a3_fe.build_fe(_X8, {"r": {}}, [_S8[1]])
check({p["name"]: p.get("hrole") for p in _fe8m["pieces"] if p["name"] == "useFetchR"} == {"useFetchR": "deriver"},
      "HOOK ROLES MUTATION: without its fetch site useFetchR falls to deriver (the role is READ from wires, never assumed)")

# ── D5 (2026-09-05): a STORE's SHAPE (its value type → fields + a typed wire) · a TYPE's MEMBERS ──
_PF = {p["name"]: p for p in fe["pieces"]}
check(_PF["useUiStore"].get("shape") == "{ dense: boolean }" and _PF["useUiStore"].get("fields") == [["dense", "boolean"]],
      "D5 FIRE (fixture): create<{ dense: boolean }>() — the zustand store carries its inline shape as fields")
check(_PF["ThemeContext"].get("shape") == "string" and not _PF["ThemeContext"].get("fields"),
      "D5 (fixture): createContext<string>() — a primitive shape has text and no fields (honest-empty)")
_ISM = [["rows", "string[]"], ["busy", "boolean"], ["load", "() => void"]]
check(_PF["useStatementStore"].get("fields") == _ISM and _PF["StatementStore"].get("members") == _ISM,
      f"D5 FIRE (review 2026-09-05): an INTERSECTION store type (State & Actions) yields its merged members — fields on the store, members on the type ({_PF['useStatementStore'].get('fields')})")
check(_PF["Recipe"].get("members") == [["id", "string"], ["title", "string"], ["score", "number"]] and _PF["RecipeProps"].get("members") == [["id", "string"]],
      "D5 (fixture): type/interface exports carry their members — the frontend's schema fields")
check(fe["stats"].get("stores_with_fields") == 2 and fe["stats"].get("types_with_members") == len([p for p in fe["pieces"] if p["kind"] == "fe-type" and p.get("members")]) and fe["stats"].get("types_with_members") >= 2,
      "D5: stats.stores_with_fields / types_with_members tally the fixture (every typed export with members, Recipe + RecipeProps among them)")
_X9 = {"byFile": {
    "src/features/cart/types.ts": {"exports": [{"name": "CartState", "kind": "type", "hasJsx": False, "members": [["items", "Item[]"], ["total", "number"]]}], "bindings": {}},
    "src/features/cart/useCartStore.ts": {"exports": [{"name": "useCartStore", "kind": "call:create", "hasJsx": False, "calls": ["create"], "types": ["CartState"],
                                                        "shape": {"text": "CartState", "refs": ["CartState"], "members": None}}],
                                          "bindings": {"create": {"ext": True}, "CartState": {"file": "src/features/cart/types.ts", "name": "CartState"}}}}}
_fe9 = _a3_fe.build_fe(_X9, {"cart": {}}, [])
_P9 = {p["name"]: p for p in _fe9["pieces"]}
_E9 = {(_fe9["pieces"][e[0]]["name"], _fe9["pieces"][e[1]]["name"]): e[2] for e in _fe9["edges"]}
check(_P9["useCartStore"]["kind"] == "store" and _P9["useCartStore"].get("fields") == [["items", "Item[]"], ["total", "number"]] and _E9.get(("useCartStore", "CartState")) == "typed",
      "D5 FIRE (synthetic): a store whose shape names a type in another file takes that type's members as fields + a typed wire to it")
_X9m = {"byFile": {k: dict(v, exports=[{kk: vv for kk, vv in ex.items() if kk != "shape"} for ex in v["exports"]]) for k, v in _X9["byFile"].items()}}
_fe9m = _a3_fe.build_fe(_X9m, {"cart": {}}, [])
check(not next(p for p in _fe9m["pieces"] if p["name"] == "useCartStore").get("fields") and _fe9m["stats"].get("stores_with_fields") == 0,
      "D5 MUTATION: no shape on the store export → no fields (the store's columns are READ from its value type, never assumed)")

print(f"frontend battery: {pass_} passed, {fail} failed" + (f", {len(skipped)} skipped" if skipped else ""))
sys.exit(1 if fail else 0)
PY
