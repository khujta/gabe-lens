"""The FRONTEND arm — the frontend modeled the way the backend is: typed PIECES + resolved
EDGES, honest-empty.

Provider = the TypeScript COMPILER (``_a3_fe_extract.mjs`` run against the twin's own
``typescript``): exported symbols with their kind + JSX/hook proof, the body REFS of each
(jsx tags · calls · type refs · identifiers), and import BINDINGS the checker resolved
(barrels followed). This module classifies every exported symbol into ONE kind and wires
pieces by resolving each ref through its binding:

    kind        proof                                   edge (from the referrer)
    component   Pascal export whose body holds JSX      renders        (jsx tag)
    hook        `useX` function export                  uses-hook      (call)
    store       create()/createContext()/atom() const   uses-store     (call · useContext(X))
                or a `useXStore` hook
    route       router config / *Route component        renders
    fe-type     type · interface · enum                 typed          (type ref)
    module      ONE piece per file of plain value        fecall         (call)  · imports (ident)
                exports (feature logic, lib, api)
                · mclass = what it DOES: render-fn · api · model · config · lib · logic
    fe-unknown  Pascal .tsx function/class export with   —
                no JSX of its own and NO rendered-by
                evidence (O1). A rendered-by hit promotes
                it to component instead (O2) — 2026-09-03

Measured on gustify 2026-08-23 (P0, docs/design/frontend-model/README.md §9): the
compiler proves 458 JSX components where graft's name convention claimed 637, and resolves
2,290 import pairs where graft carries 891 (38.9%) — hence the compiler is the provider and
graft stays the cross-file CALL contributor elsewhere. Stories/tests are EXCLUDED and
counted; barrels yield no piece (bindings see through them); a Pascal `.tsx` export without
JSX is counted (``pascal_no_jsx``), never silently dropped.

Honest-empty: no web root · ``GABE_FE_EXTRACT=0`` · no ``node`` · no ``typescript`` · an
extractor/parse failure → ``{present: False, reason}`` and the caller's GABE_C4 stays
byte-identical (the arm rides a SEPARATE top-level ``fe`` key; see _a3_graph.fold_fe).
READ-ONLY: the extractor never writes into the twin; its JSON goes to a temp file.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from _a3_web import _detect_web_root          # the same web-root roster as the fetch arm
from _a3_graft import _fe_home, _fe_pair      # feature-dir → fe·entity (paired) / bucket / candidate

EXTRACTOR = Path(__file__).with_name("_a3_fe_extract.mjs")

_STORE_CALLEES = frozenset({
    "create", "createStore", "createContext", "createSlice", "configureStore", "atom",
    "atomWithStorage", "atomFamily", "signal", "observable", "makeAutoObservable", "proxy",
    "createSignal", "writable", "readable",
})
_ROUTER_CALLEES = frozenset({
    "createBrowserRouter", "createHashRouter", "createMemoryRouter", "createRouter",
    "createFileRoute", "createRootRoute", "createRoutesFromElements",
})
# server-CACHE / query-library hooks (react-query · swr · apollo): a piece that CALLS one READS or
# WRITES the server cache = state (F1). A LIBRARY idiom, not a project name-list (same class as
# _STORE_CALLEES) — and it counts ONLY when the callee has no project binding, since a project's own
# useQuery would resolve to a piece; so honest-empty holds (no query lib → no cache piece → byte-
# identical). RTK-Query's generated useGetXQuery/useXMutation hooks are pattern-named, not in this
# fixed roster — a known follow-on gap, reported never guessed.
_CACHE_CALLEES = frozenset({
    "useQuery", "useQueries", "useInfiniteQuery", "useSuspenseQuery", "useSuspenseQueries",
    "useSuspenseInfiniteQuery", "useMutation", "useMutationState", "useLazyQuery",
    "useSWR", "useSWRInfinite", "useSWRMutation", "useSWRSubscription",
})
# FE d2w — the read/WRITE direction is the HTTP METHOD of the fetch a piece reaches (via the web
# bridge's per-site (method, path)), NOT a hook name: deterministic + LIBRARY-AGNOSTIC (works whether
# the write rides react-query useMutation, axios.post, or raw fetch, on ANY twin). A write-method fetch
# = this piece WRITES; GET = reads. Store-object writes (zustand set()) aren't method-visible → not
# claimed here (deferred: revisit when a twin shows a material store-write population the bridge misses).
_WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
# CLIENT STATE named by a literal KEY: Web Storage, and the query cache's own key-space. A PLATFORM /
# LIBRARY idiom roster (same class as _STORE_/_ROUTER_/_CACHE_CALLEES), never a project key allow-list —
# an object the roster does not know is not storage, and a key built by a factory yields no literal for
# the extractor to hand over, so it is reported by ABSENCE and never guessed. Honest-empty: a tree with
# no Web Storage and no queryKey mints no piece and no wire, and the arm is byte-identical.
_STORAGE_VIA = {"localStorage": "localStorage", "sessionStorage": "sessionStorage"}
_STORAGE_OPS = {"setItem": "w", "getItem": "r", "removeItem": "w"}
_QUERY_VIA = "query-cache"
_TYPE_KINDS = frozenset({"type", "interface", "enum"})
# design SCAFFOLD, not the app (batch 50, measured on gustify): /spikes/ (122 pieces) and
# /showcase/ (4) had ZERO app in-edges — excluded and counted. Fixture modules
# (recipeFixtures, activeShowcaseFixtures) and lib/mockupAssets are APP-WIRED (real screens
# import them — 8 + 90 edges measured) and STAY. Stories/tests were already excluded.
_SCAFFOLD_PATH = ("/spikes/", "/showcase/")
_HOOK_RX = re.compile(r"^use[A-Z0-9]")
_FIXTURE_RX = re.compile(r"(?:^|/)(?:[A-Za-z]*[Ff]ixtures?|mockupAssets)\.tsx?$")


def _area_of(path: str, home: str = "") -> str:
    """The piece's AREA — the sub-directory group inside its home (S2, batch 53): up to two
    path segments between the segments the HOME consumed and the file. `cooking/components/
    recipes/X` → ``components/recipes``; a root-level file → ``root``. The synthetic app-shell
    home consumed NOTHING, so rest[0] is the discriminator there — dropping it merged
    lib/utils with routes/utils (review 53[6]). The capsule level renders these."""
    parts = path.split("/")
    rest = parts[parts.index("src") + 1:] if "src" in parts else parts
    if rest and rest[0] == "features" and len(rest) > 2:
        mid = rest[2:-1]
    elif home == "app-shell":
        mid = rest[:-1]
    elif rest:
        mid = rest[1:-1]
    else:
        mid = []
    return "/".join(mid[:2]) if mid else "root"
_PASCAL_RX = re.compile(r"^[A-Z]")
# module CLASSES — directory IDIOMS (the same footing as the callee rosters above), never a project name-list
_MODEL_SEGS = frozenset({"model", "models", "types", "schema", "schemas", "dto"})
_CONFIG_SEGS = frozenset({"app", "config", "setup", "bootstrap", "env"})
_LIB_SEGS = frozenset({"lib", "utils", "helpers", "shared", "common", "design-system", "i18n", "assets", "styles"})
# precedence when two refs hit the same (from, to): the MOST specific relation wins
_REL_RANK = {"renders": 0, "uses-store": 1, "uses-hook": 2, "fecall": 3, "typed": 4, "imports": 5}
# the file's PRINCIPAL piece — where a screen flag / a module-scope ref / a ref to a
# non-piece export lands. Lower = more principal.
_PRINCIPAL = {"route": 0, "store": 1, "hook": 2, "component": 3, "fe-unknown": 4, "module": 5, "fe-type": 6}


# ── classification ──────────────────────────────────────────────────────────────────────
_NEXT_APP_RX = re.compile(r"(^|/)app/(?:.*/)?(page|layout|template|error|loading|not-found)\.(tsx|jsx)$")   # Next.js App Router file roles (review 2026-09-06: onyx web/src/app/**/page.tsx)


# ── a route's LABEL is its URL path (tier0 review 2026-09-07: six TanStack routes all named `Route`) ────────
# Resolution order, first hit wins: 1 · the literal the file-router factory was given (`createFileRoute("/_layout/admin")`)
# 2 · the file, by the router's own convention (TanStack `routes/settings.cards.tsx` · Next `app/chat/page.tsx`)
# 3 · the export name, as before (a react-router JSX route keeps its name — no `label` key at all).
# `name` stays the export; the raw literal rides as `route` so the card can say `export Route · route "/_layout/admin"`.
_FILE_ROUTER_CALLEES = frozenset({"createFileRoute", "createLazyFileRoute", "createRootRoute", "createRootRouteWithContext"})
_ROUTE_PATHLESS_RX = re.compile(r"/_[^/]+(?=/|$)")          # a TanStack pathless segment (`/_layout`) — layout only, never in the URL
_ROUTE_PARAM_RX = re.compile(r"\$([A-Za-z0-9_]+)")         # `$id` → `:id`
_NEXT_GROUP_RX = re.compile(r"/(\([^/]*\)|@[^/]+)(?=/|$)")   # Next `(group)` and `@slot` segments — not in the URL


def _route_path_label(lit: str) -> str:
    """The display form of a file-route literal: pathless segments dropped, `$x` → `:x`; a literal that is ONLY
    pathless segments (the layout route itself) keeps its raw form so it stays unique."""
    p = _ROUTE_PATHLESS_RX.sub("", lit)
    if not p:                       # `/_layout` — the layout route itself: nothing is left, the raw literal is the honest label
        return lit
    if not p.startswith("/"):
        p = "/" + p
    return _ROUTE_PARAM_RX.sub(r":\1", p)


def _route_from_file(path: str) -> str | None:
    """A TanStack file route without a literal: `…/routes/_layout/settings.cards.tsx` → `/settings/cards`."""
    m = re.search(r"(^|/)routes/(.+)\.(tsx|jsx|ts|js)$", path)
    if not m:
        return None
    stem = m.group(2)
    if stem == "__root":
        return "root shell"
    stem = re.sub(r"\.(lazy|route)$", "", stem)
    segs = [s for s in re.split(r"[/.]", stem) if s and s != "index" and not s.startswith("_")]
    return _ROUTE_PARAM_RX.sub(r":\1", "/" + "/".join(segs))


def _next_route_from_file(path: str) -> str | None:
    """A Next.js App Router file: `web/src/app/(marketing)/chat/[id]/page.tsx` → `/chat/:id`."""
    m = re.search(r"(^|/)app/(.*/)?(page|layout|template|error|loading|not-found)\.(tsx|jsx)$", path)
    if not m:
        return None
    d = "/" + (m.group(2) or "").rstrip("/")
    d = _NEXT_GROUP_RX.sub("", d) or "/"
    d = re.sub(r"\[\.\.\.([A-Za-z0-9_]+)\]", r":\1*", d)
    d = re.sub(r"\[([A-Za-z0-9_]+)\]", r":\1", d)
    role = m.group(3)
    return d if role == "page" else f"{d} · {role}"


def route_label(ex: dict[str, Any], path: str) -> tuple[str | None, str | None]:
    """(label, raw literal) for a route piece — (None, None) when the export name is the honest label (rule 3)."""
    kind = ex.get("kind") or ""
    callee = kind[5:] if kind.startswith("call:") else None
    lit = ex.get("arg0")
    if callee in _FILE_ROUTER_CALLEES:
        if isinstance(lit, str) and lit.startswith("/"):
            return _route_path_label(lit), lit
        if callee.startswith("createRootRoute"):
            return "root shell", None
        return _route_from_file(path), None
    if _NEXT_APP_RX.search(path):
        return _next_route_from_file(path), None
    return None, None


def classify_export(ex: dict[str, Any], path: str) -> str | None:
    """ONE kind per exported symbol, or None = folds into the file's `module` piece.
    Order matters: a `useXStore` const from create() is a store, not a hook; a `*Route`
    component is a route, not a component."""
    kind = ex.get("kind") or "other"
    name = ex.get("name") or ""
    callee = kind[5:] if kind.startswith("call:") else None
    if kind in _TYPE_KINDS:
        return "fe-type"
    if callee in _ROUTER_CALLEES:
        return "route"
    if callee in _STORE_CALLEES or (_HOOK_RX.match(name) and name.endswith("Store")):
        return "store"
    if kind == "function" and _HOOK_RX.match(name):
        return "hook"
    jsx = bool(ex.get("hasJsx"))
    if _PASCAL_RX.match(name) and jsx and kind in ("function", "class") or (
            _PASCAL_RX.match(name) and jsx and callee in ("memo", "forwardRef", "styled", "observer", "lazy")):
        if (name.endswith(("Route", "Router", "Page")) or "/routes/" in path or "/pages/" in path
                or (ex.get("isDefault") and _NEXT_APP_RX.search(path))):   # a default export of an app/**/page.tsx IS the route, whatever its name
            return "route"
        return "component"
    return None


def _piece_id(path: str, name: str | None) -> str:
    return f"fe:{path}#{name}" if name else f"fe:{path}"


# ── the arm ─────────────────────────────────────────────────────────────────────────────
def build_fe(extract: dict[str, Any], entities: dict[str, Any] | frozenset[str] | None,
             screens: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Pure: extractor JSON → {pieces, edges, homes, stats}. Deterministic (sorted inputs,
    sorted outputs). ``screens`` = _a3_web's screen list (id ``web:<rel-no-suffix>``) so a
    fetching file's principal piece carries ``screen`` + ``sites`` (the universe absorbs the
    file-level web node into it)."""
    slugs = frozenset(entities) if entities else frozenset()
    client_stores: list[str] = []          # the (via, key) pieces minted below — counted, never re-filed
    by_file: dict[str, Any] = extract.get("byFile") or {}
    pieces: dict[str, dict[str, Any]] = {}
    file_pieces: dict[str, list[str]] = {}          # file → piece ids (in principal order)
    export_piece: dict[tuple[str, str], str] = {}   # (file, export name) → piece id
    stats_x = {"stories": 0, "barrels": 0, "pascal_no_jsx": 0, "module_exports": 0}
    alias_cut: set[tuple[str, str]] = set()
    scaffold_files: set[str] = set()
    scaffold_cut: set[tuple[str, str]] = set()          # (file, export) name-level cuts — a ref to one must COUNT, never rewire
    # O2 · RENDERED-BY evidence (2026-09-03): every (file, name) some export renders as a JSX tag, resolved through
    # that file's bindings (a same-file tag resolves to the sibling). A Pascal .tsx function/class export with NO JSX
    # of its own but a rendered-by hit IS a component (delegated render · headless effect) — promoted below, never
    # folded into the file's module. Evidence the extractor already collects; no name-list.
    rendered: set[tuple[str, str]] = set()
    promoted = 0
    for _p, _rec in by_file.items():
        if _rec.get("story") or any(seg in _p for seg in _SCAFFOLD_PATH):
            continue
        _binds = _rec.get("bindings") or {}
        _names = {e.get("name") for e in _rec.get("exports") or []}
        for _ex in _rec.get("exports") or []:
            for _tag in _ex.get("jsx") or []:
                _b = _binds.get(_tag)
                if _b and _b.get("file") and not _b.get("ext"):
                    rendered.add((_b["file"], _b.get("name") or _tag))
                elif not _b and _tag in _names:
                    rendered.add((_p, _tag))
    for path in sorted(by_file):
        rec = by_file[path]
        if rec.get("story"):
            stats_x["stories"] += 1
            continue
        if any(seg in path for seg in _SCAFFOLD_PATH):
            scaffold_files.add(path)
            stats_x["scaffold_files"] = stats_x.get("scaffold_files", 0) + 1
            stats_x["scaffold_exports"] = stats_x.get("scaffold_exports", 0) + len(rec.get("exports") or [])
            continue
        local = [e for e in rec.get("exports") or [] if not e.get("reexport")]
        if not local:
            if rec.get("exports"):
                stats_x["barrels"] += 1
            continue
        home, cand = _fe_home(path, slugs)
        ids: list[str] = []
        leftovers: list[str] = []
        left_jsx = False                                    # a leftover export holds JSX → mclass render-fn
        for ex in sorted(local, key=lambda e: e.get("name") or ""):
            if (ex.get("name") or "").endswith("Spike"):       # a stray spike export in an app path
                stats_x["scaffold_exports"] = stats_x.get("scaffold_exports", 0) + 1
                scaffold_cut.add((path, ex.get("name") or ""))
                continue
            if ex.get("apiAlias"):                              # a one-line REFERENCE to the generated API
                stats_x["api_aliases"] = stats_x.get("api_aliases", 0) + 1   # contract — counted, never a piece
                alias_cut.add((path, ex.get("name") or ""))     # (the map-side de-noiser, source review 2026-08-23)
                continue
            k = classify_export(ex, path)
            if k is None:
                _nm = ex.get("name") or ""
                if _PASCAL_RX.match(_nm) and path.endswith(".tsx") and ex.get("kind") in ("function", "class"):
                    if (path, _nm) in rendered or (ex.get("isDefault") and (path, "default") in rendered):   # O2: rendered as a tag somewhere (a lazy `default` binding counts) → the component the JSX proof missed
                        k = "component"
                        promoted += 1
                    else:                                       # O1: an honest unknown — never claimed as a module
                        k = "fe-unknown"
                        stats_x["pascal_no_jsx"] += 1          # the residue the pulse line reads
                else:
                    if ex.get("hasJsx"):
                        left_jsx = True
                    leftovers.append(_nm)
                    continue
            pid = _piece_id(path, ex["name"])
            pieces[pid] = {"id": pid, "name": ex["name"], "kind": k, "file": path, "home": home,
                           "candidate": bool(cand), "span": ex.get("span"), "area": _area_of(path, home)}
            if k == "route":                              # the label is the URL path when the router says one; the export name otherwise
                _rl, _rlit = route_label(ex, path)
                if _rl:
                    pieces[pid]["label"] = _rl
                if _rlit:
                    pieces[pid]["route"] = _rlit
            if _FIXTURE_RX.search(path):
                pieces[pid]["fixture"] = True                   # showcase data, not domain mass — tagged, kept
            if ex.get("members"):                        # D5: a type's fields (the frontend's schema)
                pieces[pid]["members"] = ex["members"]
            if ex.get("shape") and k == "store":          # D5: a store's value type (its text now; fields + the typed wire once bindings resolve)
                pieces[pid]["shape"] = ex["shape"].get("text") or ""
            ids.append(pid)
            export_piece[(path, ex["name"])] = pid
            if ex.get("isDefault"):
                export_piece[(path, "default")] = pid   # a lazy() binding without a .then mapping names the default export
        if leftovers:
            stats_x["module_exports"] += len(leftovers)
            value_ids = [i for i in ids if pieces[i]["kind"] != "fe-type"]
            if not value_ids:                          # types + helpers, or a plain module: ONE
                pid = _piece_id(path, None)            # `module` piece for the file's value exports
                stem = path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
                pieces[pid] = {"id": pid, "name": stem, "kind": "module", "file": path, "home": home,
                               "candidate": bool(cand), "exports": sorted(leftovers), "area": _area_of(path, home)}
                if left_jsx:
                    pieces[pid]["jsx"] = True
                if _FIXTURE_RX.search(path):
                    pieces[pid]["fixture"] = True
                ids.append(pid)
        ids.sort(key=lambda i: (_PRINCIPAL.get(pieces[i]["kind"], 9), i))
        file_pieces[path] = ids
        for nm in leftovers:                           # a helper's refs/targets ride the principal
            export_piece[(path, nm)] = ids[0]          # VALUE piece (never a type — ids are ranked)
    principal = {f: ids[0] for f, ids in file_pieces.items() if ids}

    # screens: the fetch arm's file-level nodes → the principal piece absorbs them
    absorbed = 0
    by_export = 0                                  # D3: pieces that took a screen through their own export
    for sc in screens or []:
        sid = sc.get("id") or ""
        rel = sid[4:] if sid.startswith("web:") else sid
        for ext in (".tsx", ".ts"):
            pid = principal.get(rel + ext)
            if pid:
                calls = sc.get("calls") or []
                # D3 (operator 2026-09-05): a call site names the EXPORT enclosing it, so the screen lands on
                # the hook/component that fetched — usePantryMutations.ts (16 hooks) no longer folds onto one
                # piece. A call with no export (module-level, or an export the arm did not mint) still lands
                # on the file's principal piece — the floor, never a drop.
                _by: dict[str, list] = {}
                for c in calls:
                    _exp = c.get("export")
                    _tp = _piece_id(rel + ext, _exp) if _exp else None
                    _by.setdefault(_tp if (_tp and _tp in pieces) else pid, []).append(c)
                if not _by:                                # a dynamic-only screen (no literal call) still belongs to the file's principal — the web node must not strand
                    _by[pid] = []
                for _tp, _cs in _by.items():
                    pieces[_tp]["screen"] = sid
                    pieces[_tp]["sites"] = len(_cs)
                    w = sum(1 for c in _cs if (c.get("method") or "GET").upper() in _WRITE_METHODS)
                    if w:                              # FE d2w: a POST/PUT/PATCH/DELETE fetch WRITES (HTTP verb, library-agnostic)
                        pieces[_tp]["wsites"] = w      # write-method fetch count (a subset of `sites`)
                    if any(c.get("sse") for c in _cs):
                        pieces[_tp]["sse"] = True       # an event stream — the hook role reads it (streamer)
                    if _tp != pid:
                        by_export += 1
                absorbed += 1
                break

    # module CLASSES (operator 2026-09-03) — what a module DOES, the way feClass reads a component and role a function:
    #   render-fn · a .tsx whose leftover exports hold JSX (a view drawn by a plain function)
    #   api       · it fetches the API (the web arm absorbed call sites onto it)
    #   model     · the feature's data layer (a model/models/types/schema path segment — shapes + mappers)
    #   config    · app wiring (an app/config/setup/bootstrap segment)
    #   lib       · shared plumbing (lib/utils/helpers/shared/common/design-system/i18n/assets/styles)
    #   logic     · everything else — feature rules and calculations
    by_mclass: dict[str, int] = {}
    for p in pieces.values():
        if p["kind"] != "module":
            continue
        segs = set(p["file"].split("/")[:-1])
        mc = ("render-fn" if p.pop("jsx", False) else
              "api" if p.get("sites") else
              "model" if segs & _MODEL_SEGS else
              "config" if segs & _CONFIG_SEGS else
              "lib" if segs & _LIB_SEGS else "logic")
        p["mclass"] = mc
        by_mclass[mc] = by_mclass.get(mc, 0) + 1

    # edges: each piece's refs → binding → target piece, typed by the channel
    edges: dict[tuple[str, str], str] = {}
    unresolved = {"ext": 0, "no_piece": 0, "scaffold": 0, "alias": 0}   # ext = a library symbol · no_piece = a bound
    local = {"refs": 0}                               #   file with nothing drawn · local = same-file

    def target_of(bind: dict[str, Any] | None) -> str | None:
        if not bind:
            local["refs"] += 1                        # a same-file symbol — not a gap
            return None
        if bind.get("ext"):
            unresolved["ext"] += 1
            return None
        f, nm = bind.get("file"), bind.get("name")
        if f in scaffold_files or (f, nm) in scaffold_cut:
            unresolved["scaffold"] += 1                # an app ref INTO cut scaffold (file- OR export-level) — named, never silent, never rewired to the principal
            return None
        if (f, nm) in alias_cut:
            unresolved["alias"] += 1                   # a typed ref to a generated-contract REFERENCE — the contract is the backend schema, already mapped there
            return None
        if nm == "*":
            t = principal.get(f)
        else:
            t = export_piece.get((f, nm)) or principal.get(f)
        if not t:
            unresolved["no_piece"] += 1
        return t

    def add(src: str, tgt: str | None, rel: str) -> None:
        if not tgt or tgt == src:
            return
        if pieces[src]["kind"] == "fe-type":          # a type's `typeof useFoo` IS a type relation
            rel = "typed"
        cur = edges.get((src, tgt))
        if cur is None or _REL_RANK[rel] < _REL_RANK[cur]:
            edges[(src, tgt)] = rel

    for path, ids in file_pieces.items():
        rec = by_file[path]
        binds = rec.get("bindings") or {}

        def _render_target(tag: str, _p: str = path, _b: dict = binds) -> str | None:
            """A JSX tag → the piece it renders. A tag with NO binding is a SAME-FILE symbol —
            resolve it to a same-file EXPORT (blocker 2: `target_of` dropped every same-file
            render edge, so 36/67 root-views were mis-classified — they were sub-components
            rendered in their own file; per commit 62c2e8a: private 183→194, shared 99→124).
            HTML tags / non-exported locals still resolve to None (a real ref, not a gap)."""
            b = _b.get(tag)
            if b is not None:
                return target_of(b)
            t = export_piece.get((_p, tag))
            if t is None:
                local["refs"] += 1
            else:
                local["samefile"] = local.get("samefile", 0) + 1
            return t

        for ex in rec.get("exports") or []:
            if ex.get("reexport"):
                continue
            if (path, ex.get("name") or "") in alias_cut or (path, ex.get("name") or "") in scaffold_cut:
                continue          # a CUT export's body refs are cut noise — never rewired to the principal (review 53[5])
            src = export_piece.get((path, ex.get("name") or "")) or principal.get(path)
            if not src:
                continue
            seen: set[str] = set()
            for tag in ex.get("jsx") or []:
                seen.add(tag); add(src, _render_target(tag), "renders")
            for c in ex.get("ctxArgs") or []:
                seen.add(c); add(src, target_of(binds.get(c)), "uses-store")
            for c in ex.get("calls") or []:
                seen.add(c)
                t = target_of(binds.get(c))
                if not t:
                    if c in _CACHE_CALLEES:              # a library query/cache hook (react-query/swr):
                        pieces[src]["cache"] = True      # this piece TOUCHES the server cache = state (F1)
                    continue
                tk = pieces[t]["kind"]
                add(src, t, "uses-store" if tk == "store" else "uses-hook" if tk == "hook" else "fecall")
            for ty in ex.get("types") or []:
                seen.add(ty); add(src, target_of(binds.get(ty)), "typed")
            _sh = ex.get("shape")
            if _sh and pieces[src]["kind"] == "store":     # D5: the store's SHAPE → its fields + a typed wire to the type piece
                _flds = None
                for _ref in _sh.get("refs") or []:
                    _tgt = target_of(binds.get(_ref)) or (_piece_id(path, _ref) if _piece_id(path, _ref) in pieces else None)
                    if _tgt and _tgt != src:
                        add(src, _tgt, "typed")
                        if _flds is None and pieces[_tgt].get("members"):
                            _flds = pieces[_tgt]["members"]
                if _flds is None and _sh.get("members"):
                    _flds = _sh["members"]                # an inline literal: create<{ dense: boolean }>()
                if _flds:
                    pieces[src]["fields"] = _flds
            for idn in ex.get("idents") or []:
                if idn in seen or idn not in binds:
                    continue
                add(src, target_of(binds.get(idn)), "imports")
        # module-scope refs ride the principal piece. The extractor's file_refs walks the WHOLE
        # file (a superset), so anything an export already claimed is skipped here — else the same
        # ref double-counts (unresolved.scaffold read 2 for one fixture ref) and double-processes.
        fr = rec.get("file_refs") or {}
        src = principal.get(path)
        if src:
            claimed: set[str] = set()
            for ex in rec.get("exports") or []:
                for ch in ("jsx", "calls"):
                    claimed.update(ex.get(ch) or [])
            for tag in fr.get("jsx") or []:
                if tag in claimed:
                    continue
                add(src, _render_target(tag), "renders")
            for c in fr.get("calls") or []:
                if c in claimed:
                    continue
                t = target_of(binds.get(c))
                if t:
                    tk = pieces[t]["kind"]
                    add(src, t, "uses-store" if tk == "store" else "uses-hook" if tk == "hook" else "fecall")
                elif c in _CACHE_CALLEES:                 # a module-scope query/cache call → cache sink (F1)
                    pieces[src]["cache"] = True

        # ── CLIENT-STORE PIECES (2026-09-07). A literal KEY a piece names when it reaches Web Storage or
        #    the query cache IS client state — the frontend's smallest table. ONE piece per (via, key),
        #    shared by every file that names it, so a token WRITTEN in useAuth and READ in the api client
        #    is one node, not two. The piece is minted here, AFTER `principal` is fixed above, and is
        #    NEVER entered into file_pieces/ids — _PRINCIPAL ranks store (1) above hook (2) and component
        #    (3), so a key piece filed under a component would HIJACK that file's principal piece and
        #    steal its screen absorption and its module-scope refs. `ops` records r / w / rw honestly.
        # The extractor's `file_refs` is the WHOLE-FILE walk, so every key inside an export body appears
        # there TOO. Without this claim set the module-scope pass re-attributes each key to the file's
        # PRINCIPAL piece — and when the principal is not the export that names it (a route beside a
        # component, say) the principal gains a `uses-store` wire to state it never touches, and with it a
        # place on the state spine. The neighbouring calls/jsx loops already guard this way; this one did not.
        _claimed: set[tuple[str, str, str]] = set()
        for _ex in ([e for e in (rec.get("exports") or []) if not e.get("reexport")]
                    + [dict(rec.get("file_refs") or {}, name=None)]):
            _src = (export_piece.get((path, _ex.get("name") or "")) if _ex.get("name") else None) or principal.get(path)
            if not _src:
                continue
            _modscope = not _ex.get("name")
            _keys: list[tuple[str, str, str]] = []       # (via, key, op)
            for _t in _ex.get("storage") or []:
                if not (isinstance(_t, (list, tuple)) and len(_t) == 3):
                    continue
                _obj, _m, _k = _t
                _via, _op = _STORAGE_VIA.get(_obj), _STORAGE_OPS.get(_m)
                if _via and _op and _k:
                    _keys.append((_via, _k, _op))
            for _k in _ex.get("queryKeys") or []:
                if _k:
                    _keys.append((_QUERY_VIA, _k, "r"))   # a queryKey names the cache entry the piece READS or invalidates
            for _via, _k, _op in _keys:
                if _modscope and (_via, _k, _op) in _claimed:
                    continue                             # an export already owns this key — never re-file it on the principal
                _claimed.add((_via, _k, _op))
                _pid = f"fe:store:{_via}#{_k}"
                _p = pieces.get(_pid)
                if _p is None:
                    _p = pieces[_pid] = {"id": _pid, "name": _k, "kind": "store", "via": _via, "client": True,
                                         "file": path, "home": pieces[_src]["home"], "candidate": False,
                                         "area": pieces[_src].get("area"), "ops": ""}
                    client_stores.append(_pid)
                if _op not in _p["ops"]:
                    _p["ops"] = "rw" if _p["ops"] else _op
                add(_src, _pid, "uses-store")

    # ── D6 (review 2026-09-05): NO FEATURE LAYOUT → the config's own web claims home the pieces. _fe_home routes
    #    by directory idiom (features/<x>, <entity>/); a flat src/{routes,hooks,components} tree (gastify) landed
    #    EVERY piece in app-shell — one bucket, no per-entity fleet rows, every journey's frontend leg in one planet.
    #    Precedence: layout FIRST (a feature layout wins outright — gustify byte-identical); only when the layout
    #    homed NOTHING to an entity or candidate do center.config.json's `code.web` claims — carried expanded on
    #    the archmap as entities[slug].files [['web', path, lines]] — home a piece to fe·<slug> (paired to its
    #    backend twin exactly like a layout home). Said in stats.homing = 'layout' | 'config' so the station names it.
    homing = "layout"
    if isinstance(entities, dict) and pieces and not any(
            p["home"].startswith("fe·") or p.get("candidate") for p in pieces.values()):
        _claim: dict[str, str] = {}
        for _slug in sorted(entities):
            for _f in (entities[_slug] or {}).get("files") or []:
                if isinstance(_f, (list, tuple)) and len(_f) >= 2 and _f[0] == "web" and isinstance(_f[1], str):
                    _claim.setdefault(_f[1], _slug)            # sorted slugs → the first claimant wins, deterministically
        for p in pieces.values():
            _slug = _claim.get(p.get("file") or "")
            if _slug:
                p["home"] = "fe·" + _slug
                p["homed_by"] = "config"
                homing = "config"
    # the client stores never entered the per-file ranking, so no file's principal piece moved (see the mint)
    assert not any(pid in ids for ids in file_pieces.values() for pid in client_stores), \
        "a client-store piece reached file_pieces — it would outrank the file's hook/component principal"
    edge_list = [{"from": s, "to": t, "rel": r, "cross": pieces[s]["home"] != pieces[t]["home"]}
                 for (s, t), r in sorted(edges.items())]
    # ── STORE DETECTOR (F2) + feClass. A call wire is STATE if it (transitively) reaches a STORE, a
    #    FETCH, or a query/CACHE hook, else CHROME (cx/useT/layout plumbing). PRINCIPLED reachability
    #    over the call edges — the sinks are the store kind + fetching pieces (`screen`) + cache-hook
    #    pieces (`cache`, F1: react-query/swr library idioms), never a gustify name-list.
    #    feClass per COMPONENT then reads it (ruling 2026-09-05, D1): view = rendered by a ROUTE (the
    #    screen a URL mounts — what the operator calls the view) · detached = 0 render-parents (no drawn renderer:
    #    the app shell, or a piece whose renderer the extractor cannot see — said out loud, never a view) ·
    #    private = exactly 1 · connector = shared AND reaches state · container = shared, renders children
    #    only · leaf = shared, neither. Before D1, 0 parents was called "view" — App plus 21 lost parents. ──
    _STATE_CALL = ("fecall", "uses-hook", "uses-store")
    _rin: dict[str, set] = {}          # component id → its render-parents
    _rchild: dict[str, bool] = {}      # component id → renders at least one child component
    _callers: dict[str, list] = {}     # target → callers, over CALL edges only (state propagates backward)
    for e in edge_list:
        s, t, r = e["from"], e["to"], e["rel"]
        if r == "renders" and pieces[t]["kind"] == "component":
            _rin.setdefault(t, set()).add(s)
            if pieces[s]["kind"] == "component":
                _rchild[s] = True
        if r in _STATE_CALL:
            _callers.setdefault(t, []).append(s)
    _sink = set(pid for pid, p in pieces.items() if p["kind"] == "store" or p.get("screen") or p.get("cache"))
    touches_state = set(_sink); _stk = list(_sink)
    while _stk:                        # a caller of anything that touches state itself touches state
        _t = _stk.pop()
        for _s in _callers.get(_t, ()):
            if _s not in touches_state:
                touches_state.add(_s); _stk.append(_s)
    _wsink = set(pid for pid, p in pieces.items() if p.get("wsites"))   # FE d2w write sinks: a write-method fetch
    touches_write = set(_wsink)        # a caller reaching a write-method fetch is on the WRITE spine (⊆ touches_state)
    _fed2w = {pid: 0 for pid in _wsink}   # hops to the nearest write sink (0 = the sink itself) — the FE d2w DEPTH
    _frontier, _depth = set(_wsink), 0    # level-order BFS: first reach = the minimum distance (deterministic on sets)
    while _frontier:
        _depth += 1
        _next: set[str] = set()
        for _t in _frontier:
            for _s in _callers.get(_t, ()):
                if _s not in touches_write:
                    touches_write.add(_s); _fed2w[_s] = _depth; _next.add(_s)
        _frontier = _next
    for _pid, _d in _fed2w.items():
        pieces[_pid]["fed2w"] = _d      # the gradient's number: 0 at the write, rising outward (station bands it)
    by_channel = {"chrome": 0, "read": 0, "write": 0}
    for e in edge_list:                # tag each call wire chrome | READ | WRITE — read/write is the HTTP method
        if e["rel"] in _STATE_CALL:    # the wire reaches (deterministic, library-agnostic), never a hook name
            to = e["to"]
            ch = ("write" if to in touches_write else
                  "read" if (e["rel"] == "uses-store" or to in touches_state) else "chrome")
            e["channel"] = ch
            by_channel[ch] += 1
    by_class: dict[str, int] = {}
    for pid, p in pieces.items():
        if p["kind"] != "component":
            continue
        fi = len(_rin.get(pid, ()))
        _by_route = any(pieces[_s]["kind"] == "route" for _s in _rin.get(pid, ()))
        fc = ("view" if _by_route else "detached" if fi == 0 else "private" if fi == 1
              else "connector" if pid in touches_state else "container" if _rchild.get(pid) else "leaf")
        p["feClass"] = fc
        if pid in touches_state:
            p["state"] = True
        if pid in touches_write:
            p["write"] = True                          # on the FE d2w WRITE spine (reaches a write-method fetch)
        by_class[fc] = by_class.get(fc, 0) + 1
    # ── HOOK ROLES (D2, operator 2026-09-05): a hook is the frontend's function — ONE role from what it
    #    touches, read the way a backend function's role is read, by precedence, from wires the arm
    #    already draws: streamer (its fetch is an event stream) · fetcher (a fetch site attributed to it,
    #    a query-library cache sink, or an api-class module it calls that fetches) · store (a uses-store
    #    wire — reads OR writes: the extractor does not see setters, so the writer/reader split is the
    #    named follow-up) · orchestrator (calls other project hooks and nothing above) · effect (calls a
    #    lib/config module — analytics, logging, idempotency — and nothing above) · deriver (none of the
    #    above: computes from its inputs). Library hooks (useState, useMemo) are ext bindings → no wire. ──
    _out: dict[str, list] = {}
    for e in edge_list:
        _out.setdefault(e["from"], []).append(e)
    by_hrole: dict[str, int] = {}
    for pid, p in pieces.items():
        if p["kind"] != "hook":
            continue
        outs = _out.get(pid, ())
        _api = [pieces[e["to"]] for e in outs if e["rel"] == "fecall"
                and pieces[e["to"]]["kind"] == "module" and pieces[e["to"]].get("mclass") == "api"]
        _sse = bool(p.get("sse")) or any(m.get("sse") for m in _api)
        _fetch = bool(p.get("screen")) or bool(p.get("cache")) or any(m.get("screen") for m in _api)
        _store = any(e["rel"] == "uses-store" for e in outs)
        _orch = any(e["rel"] == "uses-hook" and pieces[e["to"]]["kind"] == "hook" for e in outs)
        _eff = any(e["rel"] == "fecall" and pieces[e["to"]]["kind"] == "module"
                   and pieces[e["to"]].get("mclass") in ("lib", "config") for e in outs)
        hr = ("streamer" if _sse else "fetcher" if _fetch else "store" if _store
              else "orchestrator" if _orch else "effect" if _eff else "deriver")
        p["hrole"] = hr
        by_hrole[hr] = by_hrole.get(hr, 0) + 1
    by_kind: dict[str, int] = {}
    by_home: dict[str, int] = {}
    for p in pieces.values():
        by_kind[p["kind"]] = by_kind.get(p["kind"], 0) + 1
        by_home[p["home"]] = by_home.get(p["home"], 0) + 1
    by_rel: dict[str, int] = {}
    for e in edge_list:
        by_rel[e["rel"]] = by_rel.get(e["rel"], 0) + 1
    homes = []
    for h, n in sorted(by_home.items()):
        pair = _fe_pair(h)
        kind = ("fe" if pair else
                "candidate" if any(p["candidate"] for p in pieces.values() if p["home"] == h) else
                "entity" if h in slugs else "bucket")
        rec = {"id": h, "kind": kind, "pieces": n,
               "areas": len({p["area"] for p in pieces.values() if p["home"] == h and p.get("area")})}
        if pair:
            rec["pair"] = pair            # the backend twin — seats fe·X beside X, joins the two reads
        homes.append(rec)
    for p in pieces.values():                          # emit-lean: a false flag is no flag
        if not p.get("candidate"):
            p.pop("candidate", None)
    order = {k: i for i, k in enumerate(sorted(pieces))}
    return {
        "pieces": [pieces[k] for k in sorted(pieces)],
        # COMPACT wires: [from_idx, to_idx, rel] over `pieces` order (the two ~70-char ids
        # repeated per wire tripled the feed); `cross` = homes differ, derived by the reader
        "edges": [([order[e["from"]], order[e["to"]], e["rel"], e["channel"]] if e.get("channel")
                   else [order[e["from"]], order[e["to"]], e["rel"]]) for e in edge_list],
        "homes": homes,
        "stats": {"files": len(by_file), "pieces": len(pieces), "by_kind": dict(sorted(by_kind.items())),
                  "by_home": dict(sorted(by_home.items())), "homing": homing, "edges": len(edge_list),
                  "by_rel": dict(sorted(by_rel.items())), "cross": sum(1 for e in edge_list if e["cross"]),
                  "screens_absorbed": absorbed, "screens_by_export": by_export, "unresolved": unresolved, "local_refs": local["refs"],
                  "samefile_renders": local.get("samefile", 0), "by_feclass": dict(sorted(by_class.items())), "by_mclass": dict(sorted(by_mclass.items())), "by_hrole": dict(sorted(by_hrole.items())), "stores_with_fields": sum(1 for _p in pieces.values() if _p["kind"] == "store" and _p.get("fields")),
                  "client_stores": len(client_stores),
                  "client_stores_by_via": dict(sorted((lambda c: c)({_v: sum(1 for _q in client_stores if pieces[_q]["via"] == _v) for _v in sorted({pieces[_q]["via"] for _q in client_stores})}).items())), "types_with_members": sum(1 for _p in pieces.values() if _p["kind"] == "fe-type" and _p.get("members")), "promoted": promoted,
                  "by_channel": by_channel, "state_pieces": len(touches_state),
                  "cache_pieces": sum(1 for p in pieces.values() if p.get("cache")),
                  "write_pieces": len(touches_write),
                  "write_sites": sum(p.get("wsites", 0) for p in pieces.values()),
                  "fed2w_max": max(_fed2w.values(), default=0),
                  "fe_types_referenced": len({e["to"] for e in edge_list if pieces[e["to"]]["kind"] == "fe-type"
                                              and pieces[e["from"]]["kind"] != "fe-type"}),
                  "excluded": stats_x,
                  "ts": extract.get("ts")},
    }


def run_extractor(web_root: Path, repo_root: Path, timeout: int = 180) -> tuple[dict[str, Any] | None, str]:
    """Run the compiler pass into a temp file (never into the twin). (json, reason). Paths are
    emitted relative to ``repo_root`` so piece ids join the fetch arm's screens + graft's nodes."""
    node = shutil.which("node")
    if not node:
        return None, "node not on PATH"
    with tempfile.TemporaryDirectory(prefix="gabe-fe-") as td:
        out = Path(td) / "fe.json"
        try:
            r = subprocess.run([node, str(EXTRACTOR), str(web_root), str(out), str(repo_root)],
                               capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return None, f"extractor timed out after {timeout}s"
        if r.returncode == 3:              # typescript not resolvable — say what fixes it (review 2026-09-06: every study clone lacked node_modules)
            return None, (f"typescript not resolvable from {web_root} — run the project's frontend install (its node_modules) "
                          f"or set GABE_TS_DIR=<dir whose node_modules/typescript exists>")
        if r.returncode != 0:
            msg = (r.stderr or r.stdout or "").strip().splitlines()
            return None, (msg[-1] if msg else f"extractor exit {r.returncode}")
        try:
            return json.loads(out.read_text()), "ok"
        except (OSError, json.JSONDecodeError) as exc:
            return None, f"extractor output unreadable: {exc}"


def fe_arm(root: Path, entities: dict[str, Any] | frozenset[str] | None,
           screens: list[dict[str, Any]] | None = None, allow_run: bool = True) -> dict[str, Any]:
    """The whole arm, one call. NEVER raises; ``present=False`` carries only the reason."""
    try:
        root = Path(root)
        web_root = _detect_web_root(root)
        if web_root is None:
            return {"present": False, "reason": "no web source"}
        if not allow_run or os.environ.get("GABE_FE_EXTRACT", "1") == "0":
            return {"present": False, "reason": "extract disabled (GABE_FE_EXTRACT=0)"}
        # the extractor wants the PACKAGE root (tsconfig + node_modules), not src/
        pkg = web_root.parent if web_root.name == "src" else web_root
        data, reason = run_extractor(pkg, root)
        if data is None:
            return {"present": False, "reason": reason}
        if not data.get("files"):   # a tsconfig resolved but matched 0 source files → HONEST-EMPTY, never a false present=True/0-pieces (the Vite references-stub trap)
            return {"present": False,
                    "reason": f"typescript {data.get('ts')} · 0 source files (tsconfig matched none — references not followed or empty include)"}
        out = build_fe(data, entities, screens)
        out["present"] = True
        out["reason"] = f"typescript {data.get('ts')} · {data.get('files')} files"
        if data.get("tsFrom") == "override":       # a BORROWED typescript (GABE_TS_DIR) parsed the tree — the project's own deps may be absent → third-party imports unresolved
            out["reason"] += " · typescript borrowed via GABE_TS_DIR — the project's own deps may be absent (third-party imports unresolved)"
        return out
    except Exception as exc:  # noqa: BLE001 — the arm enhances, never breaks, the build
        return {"present": False, "reason": f"fe arm error: {exc}"}
