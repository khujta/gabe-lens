#!/usr/bin/env python3
"""A3 Code tab — the machine-derived technical decode of one entity.

Everything here is parsed from source with `ast`, never hand-listed (the
anti-curation guardrail applied to code documentation): endpoints from the
FastAPI decorators + their real docstrings, the data model from the SQLAlchemy
`Mapped[...]` columns + table args, and the code map from the files on disk
with their measured line counts. The card contributes only the section intro
prose; if a file moves or an endpoint is added, the next regen shows it
without anyone editing a doc.
"""

from __future__ import annotations

import ast
import glob as _glob
import json as _json
import re as _re_mod
from urllib.parse import quote as _uq
from pathlib import Path

import _center_data as _cd
import _a3_guard
import _a3_tests
from _a3_render import (E, ENT_COL, entity_badge, kind_ic, kind_tag, entity_icon, legend,
                        lines_grade, md, sechead, subnav, table, th_label, trunc, xtable)

_ADOPT_NAMES: dict | None = None


def _adopt_name(slug_: str) -> str:
    """The entity's display name from the registry (label fallback), cached."""
    global _ADOPT_NAMES
    if _ADOPT_NAMES is None:
        _ADOPT_NAMES = {}
        p = _cd.CENTER_DIR / "adoption.json"
        if p.exists():
            try:
                for s in _json.loads(p.read_text()).get("sections", []):
                    if s.get("entity"):
                        _ADOPT_NAMES[s["entity"]] = (s.get("display_name")
                                                     or s.get("label")
                                                     or s["entity"])
            except (ValueError, OSError):
                pass
    return _ADOPT_NAMES.get(slug_, slug_)


def _field_desc(item: ast.AnnAssign, src_lines: list[str]) -> str:
    """One-line field description, MACHINE-DERIVED only: a description=/comment=
    string kwarg on the field's value call (pydantic Field / mapped_column),
    else the field line's own trailing `# comment`. Absent stays absent —
    the page renders an em dash, never an invented sentence."""
    if isinstance(item.value, ast.Call):
        for kw in item.value.keywords:
            if (kw.arg in ("description", "comment")
                    and isinstance(kw.value, ast.Constant)
                    and isinstance(kw.value.value, str)):
                return " ".join(kw.value.value.split())
    line = src_lines[item.lineno - 1] if 0 < item.lineno <= len(src_lines) else ""
    m = _re_mod.search(r"#\s*(.+?)\s*$", line)
    return " ".join(m.group(1).split()) if m else ""

# The layers a code map is organized by, in render order. Semantic names, not
# paths: api=endpoints (FastAPI), models=SQLAlchemy, schemas=Pydantic, the rest
# are file globs. Declared in center.config.json `code_layers`.
_CODE_LAYERS = _cd.CFG.get("code_layers",
                           ["api", "services", "models", "schemas", "web", "mobile"])

# Icons (feather-style) + colors for the tab's generated section banners.
_IC_ZAP = '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>'
_IC_FOLDER = ('<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 '
              '2-2h5l2 3h9a2 2 0 0 1 2 2z"/>')
_IC_DB = ('<ellipse cx="12" cy="5" rx="9" ry="3"/>'
          '<path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>'
          '<path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>')

_METHOD_CLS = {"GET": "m-get", "POST": "m-post", "PATCH": "m-mut",
               "PUT": "m-mut", "DELETE": "m-del"}
# Type families for the data-model Type column: one hue per family, and within
# a family the WIDER type renders deeper (int plain → float/Decimal deep). A
# token absent here is a domain type or alias and stays uncolored on purpose.
_TYPE_CLS = {
    "int": "ty-num1", "float": "ty-num2", "Decimal": "ty-num2",
    "Numeric": "ty-num2", "date": "ty-tim1", "time": "ty-tim1",
    "datetime": "ty-tim2", "str": "ty-str1", "Text": "ty-str2",
    "bytes": "ty-str2", "bool": "ty-bool", "dict": "ty-json",
    "list": "ty-json", "Any": "ty-json", "JSON": "ty-json",
    "Literal": "ty-json", "UUID": "ty-id", "uuid": "ty-id",
    "None": "ty-null",
}
_LAYER_CLS = {"api": "l-api", "services": "l-services", "models": "l-models",
              "schemas": "l-schemas", "web": "l-web", "mobile": "l-mobile"}

# Which source files make up an entity, by layer, and which model classes to
# document — read from center.config.json `entities.<slug>.code` /
# `.models`. Paths are repo-relative; web/mobile/test entries are globs. This is
# the ONE editorial mapping and it lives in config, not in this file, so the
# generator source stays project-agnostic (everything rendered from it is
# measured, not asserted).
_ENTITIES = _cd.CFG.get("entities", {})
def _expand_globs(repo: Path, pats) -> list[str]:
    """center.config.json ``code.api`` / ``code.models`` / ``code.schemas`` entries — literal paths OR
    globs. Review 2026-09-06 (repo-study): a glob silently yielded NOTHING — the parsers test
    ``path.exists()`` on the pattern itself. A literal path passes through untouched (every existing
    config byte-identical); a pattern expands to its sorted repo-relative matches, ``**`` recursive,
    deduplicated in order. Foreign repos (tier1's ``modules/*/routes.py``, onyx's ``server/**``) become
    expressible without listing a hundred files by hand."""
    out: list[str] = []
    for pat in pats or []:
        if any(ch in pat for ch in "*?["):
            for h in sorted(_glob.glob(str(repo / pat), recursive=True)):
                hp = Path(h)
                if not hp.is_file():
                    continue
                try:
                    rel = str(hp.relative_to(repo))
                except ValueError:
                    rel = h
                if rel not in out:
                    out.append(rel)
        elif pat not in out:
            out.append(pat)
    return out


ENTITY_CODE = {slug: e["code"] for slug, e in _ENTITIES.items() if e.get("code")}
ENTITY_CODE = {slug: {**code, **{k: _expand_globs(_cd.REPO_ROOT, code.get(k))
                                 for k in ("api", "models", "schemas") if code.get(k)}}
               for slug, code in ENTITY_CODE.items()}
# Entity classes to document from the model files (absent = all classes found).
ENTITY_MODELS = {slug: e["models"] for slug, e in _ENTITIES.items() if e.get("models")}


def _first_sentence(doc: str | None) -> str:
    """The docstring's SUMMARY PARAGRAPH (up to the first blank line), joined —
    wrapped source lines are one sentence, not one line each.

    Returns it WHOLE. It used to cut at 170 chars here, and then `purpose_cell`
    built a ⊕ expander whose "full" span was that already-truncated string — a
    reader who clicked to finish the sentence still could not finish it. One
    truncator per value; this is not it."""
    if not doc:
        return "—"
    return " ".join(doc.strip().split("\n\n")[0].split())


def _safe_read(path) -> str | None:
    """A file's text, never raising on a bad encoding (errors='replace') or a vanished
    file (OSError → None). One non-UTF-8 file must not abort the whole regen (E3)."""
    try:
        return path.read_text(errors="replace")
    except OSError:
        return None


_UNPARSEABLE: dict[str, str] = {}     # rel file → why (review 2026-09-06: a skipped file removed a whole module with no signal anywhere)


def _relkey(path) -> str:
    try:
        return str(Path(path).relative_to(_cd.REPO_ROOT))
    except ValueError:
        return str(path)


def unparseable_files() -> list[list[str]]:
    """[[rel, why]] — every mapped Python file the scanners could NOT parse this build (bad encoding,
    a syntax error, newer syntax than the running interpreter). Surfaced on the archmap
    (``unparseable``) so an absent module reads as a NAMED gap, never as silence. [] honest-empty."""
    return [[k, v] for k, v in sorted(_UNPARSEABLE.items())]


# NEWER-SYNTAX SHIMS (review 2026-09-06): the scanners parse with the SUITE's interpreter (3.12 here); a
# project on a newer Python (tier0 requires 3.14 and writes PEP 758 `except A, B:`) turned its auth
# module unparseable — the whole dependency chain vanished. A shim is a SOURCE-LEVEL rewrite of one
# known construct into its older-spelling equivalent, applied ONLY after the plain parse fails and only
# if the rewritten text then parses. Semantics-preserving by construction (`except A, B:` ≡ `except (A, B):`).
_SYNTAX_SHIMS = (
    (_re_mod.compile(r"^(\s*except\s+)([A-Za-z_][\w.]*(?:\s*,\s*[A-Za-z_][\w.]*)+)(\s*:)", _re_mod.M), r"\1(\2)\3"),   # PEP 758
)


def _shim_parse(src: str):
    """ast.parse after the known newer-syntax rewrites, or None."""
    text = src
    for rx, rep in _SYNTAX_SHIMS:
        text = rx.sub(rep, text)
    if text == src:
        return None
    try:
        return ast.parse(text)
    except (SyntaxError, ValueError):
        return None


def _safe_parse(path):
    """(tree, src) for a Python file, or (None, src|None) — NEVER raises. A file that
    is not valid Python for the running interpreter (a WIP syntax error, newer syntax on
    an older interpreter, or non-Python mapped into a Python layer) is skipped, not fatal —
    and RECORDED (``unparseable_files``) so the skip is said out loud.
    Mirrors the try/except the newer detectors (function_insight/_def_spans) already use."""
    src = _safe_read(path)
    if src is None:
        _UNPARSEABLE[_relkey(path)] = "unreadable"
        return None, None
    try:
        return ast.parse(src), src
    except SyntaxError as exc:
        shimmed = _shim_parse(src)                # a newer-Python spelling the running interpreter lacks
        if shimmed is not None:
            return shimmed, src
        _UNPARSEABLE[_relkey(path)] = f"syntax error at line {exc.lineno}"
        return None, src
    except ValueError as exc:
        _UNPARSEABLE[_relkey(path)] = f"unparseable: {str(exc)[:60]}"
        return None, src


def _table_of(node: ast.ClassDef) -> str | None:
    """The TABLE a class maps, or None. A string ``__tablename__`` (SQLAlchemy declarative) — or the
    SQLModel idiom ``class User(SQLModel, table=True)`` whose table defaults to the class name
    lowercased (review 2026-09-06: tier0 and tier2 drew ZERO tables, so the schema-vs-model mission had
    no model to point at). A computed/f-string name stays undocumented, never a guess."""
    for item in node.body:
        if (isinstance(item, ast.Assign) and item.targets
                and getattr(item.targets[0], "id", "") == "__tablename__"
                and isinstance(item.value, ast.Constant)
                and isinstance(item.value.value, str)):
            return item.value.value
    for kw in node.keywords:
        if kw.arg == "table" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
            return node.name.lower()
    return None



# ── ROUTER MOUNTS (review 2026-09-06, repo-study). The URL a handler really serves is the CHAIN
#    app → include_router(…, prefix) → … → APIRouter(prefix) → decorator path. The scanner read only the
#    leaf's APIRouter(prefix=): tier1 (Fastro) mounts prefix-less module routers at include time
#    (`router.include_router(users_router, prefix="/users")` under `/v1` under `/api`) so 88% of its
#    endpoints carried a wrong URL and the URL-domain lens read garbage; tier0/tier2 lost 100%/84%.
#    Resolved ONCE per repo: every .py under the api files' top-level dirs that mentions include_router
#    is parsed; routers are keyed (file, variable); imports resolve a name / `mod.router` attribute to
#    the declaring file; mount(leaf) = mount(parent) + parent's own prefix + the include prefix, rooted
#    at the FastAPI app (or any receiver the scan cannot name — a factory's `application` param).
#    A NON-LITERAL include prefix (`settings.API_V1_STR`) contributes "" and is NAMED in the stats,
#    never guessed. The leading API mount (`/api`, `/api/v1`) is then STRIPPED from every label — the
#    normalization the web arm applies to fetch paths — so the twins' labels (mounted under /api/v1)
#    stay byte-identical while a foreign repo's domains come out right.
_MOUNTS: dict[str, dict] = {}
_MOUNT_SKIP = ("/.venv/", "/venv/", "/node_modules/", "/site-packages/", "/__pycache__/",
               "/tests/", "/test/", "/alembic/", "/migrations/")
_API_MOUNT_RE = _re_mod.compile(r"^/api(?:/v\d+)?(?=/|$)")


def _strip_api(path: str) -> str:
    """`/api/v1/users/{id}` → `/users/{id}`; `/api/manage/x` → `/manage/x`; a bare mount → `/`."""
    return _API_MOUNT_RE.sub("", path) or "/"


def _resolve_module(repo: Path, from_rel: str, module: str | None, level: int) -> str | None:
    """`from .x import y` / `from app.api import z` → the repo-relative FILE that declares the module
    (``x.py`` or ``x/__init__.py``), searched from the importing file's package outward. None = unknown."""
    parts = [p for p in (module or "").split(".") if p]
    start = Path(from_rel).parent
    if level:
        for _ in range(max(level - 1, 0)):
            start = start.parent
        bases = [start]
    else:
        bases = [start, *start.parents]
    for base in bases:
        cands = []
        if parts:
            cands.append((base / Path(*parts)).with_suffix(".py"))
            cands.append(base / Path(*parts) / "__init__.py")
        else:
            cands.append(base / "__init__.py")
        for cand in cands:
            p = repo / cand
            if p.is_file():
                try:
                    return str(p.relative_to(repo))
                except ValueError:
                    return str(cand)
    return None


def _mounts_for(repo: Path, files) -> dict:
    """{'mount': {(file, router_var): prefix}, 'unresolved': [...], 'scanned', 'routers', 'mounted'} —
    cached per repo; the scan covers the top-level dirs of ``files`` ∪ every configured api file."""
    key = str(repo)
    if key in _MOUNTS:
        return _MOUNTS[key]
    tops = {Path(f).parts[0] for f in (files or []) if Path(f).parts}
    for _slug in ENTITY_CODE:
        for f in (ENTITY_CODE[_slug].get("api") or []):
            if Path(f).parts:
                tops.add(Path(f).parts[0])
    decl: dict[tuple, str] = {}          # (file, var) → the router's OWN APIRouter(prefix)
    edges: list[tuple] = []              # (parent_key, child_key, include_prefix)
    unresolved: list[dict] = []
    scanned = 0
    for top in sorted(tops):
        root = repo / top
        if not root.is_dir():
            continue
        for py in sorted(root.rglob("*.py")):
            s = str(py)
            if any(k in s for k in _MOUNT_SKIP):
                continue
            src = _safe_read(py)
            if not src or "include_router" not in src:
                continue
            tree, _ = _safe_parse(py)
            if tree is None:
                continue
            rel = str(py.relative_to(repo))
            scanned += 1
            imports: dict[str, tuple] = {}     # local name → (module file, symbol|None, submodule file|None)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    mf = _resolve_module(repo, rel, node.module, node.level)
                    for a in node.names:
                        sub = _resolve_module(repo, rel, (node.module + "." + a.name) if node.module else a.name, node.level)
                        imports[a.asname or a.name] = (mf, a.name, sub)
                elif isinstance(node, ast.Import):
                    for a in node.names:
                        mf = _resolve_module(repo, rel, a.name, 0)
                        imports[a.asname or a.name.split(".")[0]] = (mf, None, mf)
                elif isinstance(node, (ast.Assign, ast.AnnAssign)) and isinstance(node.value, ast.Call):
                    fn = getattr(node.value.func, "id", "") or getattr(node.value.func, "attr", "")
                    tg = node.targets if isinstance(node, ast.Assign) else [node.target]
                    names = [t.id for t in tg if isinstance(t, ast.Name)]
                    if fn == "APIRouter":
                        pf = ""
                        for kw in node.value.keywords:
                            if (kw.arg == "prefix" and isinstance(kw.value, ast.Constant)
                                    and isinstance(kw.value.value, str)):
                                pf = kw.value.value
                        for n in names:
                            decl[(rel, n)] = pf

            def _key(expr):
                if isinstance(expr, ast.Name):
                    if (rel, expr.id) in decl:
                        return (rel, expr.id)
                    imp = imports.get(expr.id)
                    if imp and imp[0] and imp[1]:
                        return (imp[0], imp[1])
                    return None
                if isinstance(expr, ast.Attribute) and isinstance(expr.value, ast.Name):
                    imp = imports.get(expr.value.id)
                    if imp:
                        if imp[2]:                      # `from . import users` → users.router
                            return (imp[2], expr.attr)
                        if imp[0] and imp[1] is None:   # `import pkg.mod as m` → m.router
                            return (imp[0], expr.attr)
                    return None
                return None

            for node in ast.walk(tree):
                if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and node.func.attr == "include_router" and node.args):
                    continue
                child = _key(node.args[0])
                if child is None:
                    unresolved.append({"file": rel, "line": node.lineno,
                                       "why": "child router not resolvable: " + ast.unparse(node.args[0])[:60]})
                    continue
                parent = _key(node.func.value)
                if parent is None:                       # the app / a factory param / an unknown receiver → a ROOT
                    parent = ("app", rel + "#" + (getattr(node.func.value, "id", None) or "app"))
                inc = ""
                for kw in node.keywords:
                    if kw.arg == "prefix":
                        if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                            inc = kw.value.value
                        else:
                            unresolved.append({"file": rel, "line": node.lineno,
                                               "why": "non-literal prefix: " + ast.unparse(kw.value)[:60]})
                edges.append((parent, child, inc))
    parent_of: dict[tuple, list] = {}
    for p, c, inc in edges:
        parent_of.setdefault(c, []).append((p, inc))
    memo: dict[tuple, str] = {}

    def _mount(k, seen=()):
        if k in memo:
            return memo[k]
        if k in seen or k not in parent_of:
            memo[k] = ""
            return ""
        p, inc = parent_of[k][0]                 # a router mounted twice keeps its FIRST mount (deterministic: file order)
        m = _mount(p, seen + (k,)) + (decl.get(p, "") if p[0] != "app" else "") + inc
        memo[k] = m
        return m

    mounts = {k: _mount(k) for k in parent_of}
    out = {"mount": mounts, "unresolved": unresolved, "scanned": scanned,
           "routers": len(decl), "mounted": sum(1 for v in mounts.values() if v)}
    _MOUNTS[key] = out
    return out


def mount_stats(repo: Path) -> dict:
    """The archmap's ``route_mounts`` block — {scanned, routers, mounted, unresolved:[…]} for THIS repo's
    resolved chain, or {} when no include_router chain was found (honest-empty, byte-identical)."""
    m = _MOUNTS.get(str(repo))
    if not m or not (m["mount"] or m["unresolved"]):
        return {}
    return {"scanned": m["scanned"], "routers": m["routers"], "mounted": m["mounted"],
            "unresolved": m["unresolved"]}


def parse_endpoints(repo: Path, files: list[str]) -> list[dict]:
    """FastAPI surface via ast: decorator method+path, router prefix, the
    handler's REAL docstring, response_model and status_code when literal."""
    out: list[dict] = []
    _mts = _mounts_for(repo, files)["mount"]
    for rel in files:
        path = repo / rel
        if not path.exists():
            continue
        tree, _src = _safe_parse(path)
        if tree is None:                       # unparseable file → skip, don't abort the build (it is NAMED in unparseable_files)
            continue
        _aliases = _dep_aliases(repo, rel, tree)   # `user: CurrentUserDep` — module-level Annotated[…, Depends()] aliases, this file + one import hop
        prefix = ""                       # the file's LAST APIRouter(prefix=…) — the fallback for a decorator on a router this scan cannot name
        prefixes: dict[str, str] = {}     # router VARIABLE → its own prefix (review 2026-09-05: gastify's groups.py mounts `router` at /groups
        for node in ast.walk(tree):       #   AND `invites_router` at /invites — ONE prefix per file had labeled all 17 handlers /invites)
            _call, _names = None, []
            if (isinstance(node, (ast.Assign, ast.AnnAssign)) and isinstance(node.value, ast.Call)
                    and getattr(node.value.func, "id", "") == "APIRouter"):
                _call = node.value
                _tg = node.targets if isinstance(node, ast.Assign) else [node.target]
                _names = [t.id for t in _tg if isinstance(t, ast.Name)]
            elif isinstance(node, ast.Call) and getattr(node.func, "id", "") == "APIRouter":
                _call = node
            else:
                continue
            _own = ""
            for kw in _call.keywords:
                if (kw.arg == "prefix" and isinstance(kw.value, ast.Constant)
                        and isinstance(kw.value.value, str)):   # a non-str prefix would break (prefix + sub)
                    _own = kw.value.value
                    if _call is node:
                        prefix = _own                            # the file-level fallback keeps the pre-review rule (last wins)
            for _n in _names:
                prefixes[_n] = _own
        for node in ast.walk(tree):
            if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                continue
            for dec in node.decorator_list:
                if not (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)):
                    continue
                method = dec.func.attr
                if method not in ("get", "post", "put", "patch", "delete"):
                    continue
                _rv = dec.func.value                                   # `router` in @router.get(…) → THAT router's prefix
                _pre = prefixes.get(_rv.id, prefix) if isinstance(_rv, ast.Name) else prefix
                _mp = _mts.get((rel, _rv.id), "") if isinstance(_rv, ast.Name) else ""   # + the app → include_router chain above it
                has_path = (dec.args and isinstance(dec.args[0], ast.Constant)
                            and isinstance(dec.args[0].value, str))   # str-only → (prefix + sub) can't TypeError
                sub = dec.args[0].value if has_path else ""
                resp = status = None
                for kw in dec.keywords:
                    if kw.arg == "response_model":
                        resp = ast.unparse(kw.value)
                    if kw.arg == "status_code":
                        status = ast.unparse(kw.value).rsplit(".", 1)[-1]
                # Every bare name the handler's body touches — intersected later
                # with model/schema class names to derive endpoint↔type links.
                refs = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
                ep = {
                    "method": method.upper(), "path": _strip_api(_mp + _pre + sub),
                    "fn": node.name, "file": rel, "refs": refs,
                    "doc": _first_sentence(ast.get_docstring(node)),
                    "resp": (resp or "—").removeprefix("PaginatedResponse[").removesuffix("]"),
                    "status": status or "200",
                }
                if _streams(node, dec):                                # class 13b: the handler streams (SSE / chunked) — an async generator, not one payload
                    ep["stream"] = True
                mw = _endpoint_middleware(node, dec, _aliases)   # C4: the level-2 gates (auth/consent/idempotency) run before the body
                if mw:
                    ep["middleware"] = mw
                _fl = _flag_gates(node, parse_flags(repo))   # class 12: the feature-flag walls in the handler body
                if _fl:
                    ep["flags"] = _fl
                out.append(ep)
    return out


_STREAM_CLASSES = frozenset({"StreamingResponse", "EventSourceResponse"})


def _streams(node, route_dec) -> bool:
    """True when the handler returns a streaming response — `StreamingResponse(...)` / sse-starlette's
    `EventSourceResponse(...)` in its body, or `response_class=StreamingResponse` on the route (review
    2026-09-06: tier2's chat stream read as a plain POST; the token's path had no marker)."""
    for kw in getattr(route_dec, "keywords", []):
        if kw.arg == "response_class" and (getattr(kw.value, "id", None) or getattr(kw.value, "attr", None)) in _STREAM_CLASSES:
            return True
    for n in ast.walk(node):
        if isinstance(n, ast.Call) and (getattr(n.func, "id", None) or getattr(n.func, "attr", None)) in _STREAM_CLASSES:
            return True
    return False


def _schema_orm(node: ast.ClassDef) -> bool:
    """True when a pydantic schema reads from ORM ATTRIBUTES — ``model_config =
    ConfigDict(from_attributes=True)`` (v2) or a nested ``class Config:`` with ``orm_mode = True`` /
    ``from_attributes = True`` (v1). The signal the serializes NAMING arm requires: a schema that
    MAPS a model (so ``PantryItemResponse`` → ``PantryItem`` is a real serialization, not a coincidence)."""
    for item in node.body:
        if (isinstance(item, ast.Assign) and item.targets
                and getattr(item.targets[0], "id", "") == "model_config"
                and isinstance(item.value, ast.Call)):
            for kw in item.value.keywords:
                if kw.arg == "from_attributes" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    return True
        if isinstance(item, ast.ClassDef) and item.name == "Config":
            for sub in item.body:
                if (isinstance(sub, ast.Assign) and sub.targets
                        and getattr(sub.targets[0], "id", "") in ("orm_mode", "from_attributes")
                        and isinstance(sub.value, ast.Constant) and sub.value.value is True):
                    return True
    return False


def parse_schemas(repo: Path, files: list[str]) -> list[dict]:
    """Pydantic request/response shapes — the classes the Returns column names.
    Same honesty rule: parsed from source, never listed by hand."""
    out: list[dict] = []
    for rel in files:
        path = repo / rel
        if not path.exists():
            continue
        tree, src = _safe_parse(path)
        if tree is None:                       # unparseable schema file → skip, don't abort
            continue
        src_lines = src.splitlines()
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            fields = [(i.target.id, ast.unparse(i.annotation),
                       _field_desc(i, src_lines))
                      for i in node.body
                      if isinstance(i, ast.AnnAssign) and isinstance(i.target, ast.Name)]
            if fields:
                _sd = {"cls": node.name, "file": rel, "fields": fields,
                       "doc": _first_sentence(ast.get_docstring(node))}
                if _schema_orm(node):                # class 5b: this schema maps a model (serializes NAMING arm)
                    _sd["orm"] = True
                out.append(_sd)
    return out


def _anchor(kind: str, slug: str, name: str) -> str:
    import re as _re
    return f"{kind}-{slug}-{_re.sub(r'[^A-Za-z0-9]+', '-', name).strip('-')}"


def parse_defines(repo: Path, rel: str) -> list[str]:
    """What a file DEFINES, parsed per language: python -> top-level classes +
    public functions (ast); ts/tsx -> exported symbols (export grammar)."""
    import re as _re
    path = repo / rel
    if not path.exists():
        return []
    if rel.endswith(".py"):
        names = []
        _tree, _ = _safe_parse(path)
        for node in (_tree.body if _tree is not None else []):   # unparseable → no defines, not fatal
            if isinstance(node, ast.ClassDef):
                names.append(node.name)
            elif (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                  and not node.name.startswith("_")):
                names.append(f"{node.name}()")
        return names
    src = _safe_read(path) or ""   # non-UTF-8 TS/JS never aborts the regen
    names = _re.findall(
        r"export\s+(?:default\s+)?(?:async\s+)?"
        r"(?:function|const|class|interface|type)\s+([A-Za-z_]\w*)", src)
    return list(dict.fromkeys(names))


# Example values are SYNTHETIC — derived from Literal values when the type
# carries them, else from field-name/type heuristics. Labeled as such.
_NAME_EXAMPLES = [
    ("currency", '"CLP"'), ("country", '"CL"'), ("city", '"Concepción"'),
    ("merchant", '"Jumbo Bio Bío"'), ("alias", '"Jumbo"'),
    ("term_total", "12"), ("term_current", "3"), ("share_count", "2"),
    ("confidence", "0.93"), ("fx_rate", "0.00106"), ("qty", "2"),
    ("_minor", "12990"), ("_ms", "840"), ("tokens", "1250"),
    ("label", '"cuota 3 de 12"'), ("name", '"Pan integral"'),
    ("image_url", '"/transactions/{id}/images/{id}"'),
    ("thumbnail_url", '"data:image/webp;…"'), ("payload", '{"merchant": "…"}'),
    ("signals", '[{"kind": "total_mismatch"}]'), ("sort_order", "1"),
]


def _example(name: str, typ: str) -> str:
    import re as _re
    lit = _re.search(r'Literal\[\s*[\'"]([^\'"]+)[\'"]', typ)
    if lit:
        return f'"{lit.group(1)}"'
    low = name.lower()
    t = typ.lower()
    # Type-shaped checks FIRST where the type is unambiguous — a *_user_edited_at
    # datetime must never inherit the merchant string example by name-match.
    if "datetime" in t or low.endswith("_at"):
        return '"2026-07-20T14:32:00Z"'
    if "uuid" in t:
        return '"b7e2a1c4-5d68-4f2e-9a3b-1c2d3e4f5a6b"'
    for frag, ex in _NAME_EXAMPLES:
        if frag in low:
            return ex
    if t.startswith("date"):
        return '"2026-07-20"'
    if t.startswith("time"):
        return '"14:32"'
    if "bool" in t:
        return "true"
    if "decimal" in t or "float" in t:
        return "0.93"
    if "int" in t:
        return "3"
    if t.startswith("list"):
        return "[…]"
    if "dict" in t:
        return "{…}"
    return '"…"'


# Stable per-file font colors for the endpoints table's file links.
_FILE_PALETTE = ["#4f46e5", "#0f766e", "#b45309", "#7c3aed",
                 "#0d7a84", "#c2410c", "#8a6d1a", "#d1443c"]
_VERB_FONT = {"GET": "fm-get", "POST": "fm-post", "PATCH": "fm-mut",
              "PUT": "fm-mut", "DELETE": "fm-del"}


def parse_models(repo: Path, files: list[str], only: list[str] | None) -> list[dict]:
    """SQLAlchemy entities via ast: table name, Mapped[...] columns with their
    annotations, unique constraints, and the class docstring."""
    out: list[dict] = []
    for rel in files:
        path = repo / rel
        if not path.exists():
            continue
        tree, _src = _safe_parse(path)
        if tree is None:                       # unparseable model file → skip, don't abort
            continue
        _src_lines = _src.splitlines()
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            if only and node.name not in only:
                continue
            tab = _table_of(node)                 # __tablename__ string, or the SQLModel table=True default (review 2026-09-06)
            cols: list[tuple[str, str]] = []
            fks: dict[str, str] = {}
            rels: list[dict] = []
            uqs: list[str] = []
            for item in node.body:
                if (isinstance(item, ast.Assign) and
                        getattr(item.targets[0], "id", "") == "__table_args__"):
                    uqs = [ast.unparse(e)[:90] for e in getattr(item.value, "elts", [])
                           if "UniqueConstraint" in ast.unparse(e)]
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    ann = ast.unparse(item.annotation)
                    if not ann.startswith("Mapped["):
                        continue
                    inner = ann[7:-1]
                    call = item.value if isinstance(item.value, ast.Call) else None
                    fn = ""
                    if call is not None:
                        fn = getattr(call.func, "id", getattr(call.func, "attr", ""))
                    if fn == "relationship":
                        # An ORM NAVIGATION property — not a stored column. The
                        # only stored direction is the ForeignKey column.
                        many = inner.startswith("list[")
                        target = (inner[5:-1] if many else inner)
                        target = target.split("|")[0].strip().strip("\"'")
                        kw = {k.arg: ast.unparse(k.value).strip("'\"")
                              for k in call.keywords if k.arg}
                        rels.append({"name": item.target.id, "target": target,
                                     "many": many,
                                     "back": kw.get("back_populates", ""),
                                     "cascade": kw.get("cascade", "")})
                        continue
                    cols.append((item.target.id, inner,
                                 _field_desc(item, _src_lines)))
                    if call is not None:
                        for sub in ast.walk(call):
                            if (isinstance(sub, ast.Call)
                                    and getattr(sub.func, "id", "") == "ForeignKey"
                                    and sub.args
                                    and isinstance(sub.args[0], ast.Constant)):
                                fks[item.target.id] = sub.args[0].value
            if tab:
                out.append({"cls": node.name, "table": tab, "file": rel,
                            "doc": _first_sentence(ast.get_docstring(node)),
                            "cols": cols, "fks": fks, "rels": rels, "uqs": uqs})
    return out


def code_map(repo: Path, layers: dict) -> list[tuple[str, str, int]]:
    """(layer, file, measured line count) for every file the mapping names —
    globs expanded against disk, so a moved file drops out visibly."""
    rows: list[tuple[str, str, int]] = []
    for layer in _CODE_LAYERS:
        for pat in layers.get(layer, []):
            for f in sorted(_glob.glob(str(repo / pat), recursive=True)):
                p = Path(f)
                if p.is_file() and ".test." not in p.name:
                    rows.append((layer, str(p.relative_to(repo)),
                                 len((_safe_read(p) or "").splitlines())))
    return rows


# One parse per entity per build: the Code tab, the archmap serialization and
# the model-insight pass all read THIS cache (before it, the tree was parsed
# twice per entity; the insight pass would have made it three).
_EMAP_CACHE: dict[str, dict | None] = {}


def collect_entity_map(slug: str, repo: Path) -> dict | None:
    if slug in _EMAP_CACHE:
        return _EMAP_CACHE[slug]
    _EMAP_CACHE[slug] = _collect_entity_map(slug, repo)
    return _EMAP_CACHE[slug]


def _collect_entity_map(slug: str, repo: Path) -> dict | None:
    """The entity's architecture map, gathered ONCE per build: endpoints (with
    the documented types each handler touches), models (columns/FKs/relationship
    edges), schemas, files-with-lines, and per-file defines.

    This object is BOTH the Code tab's input and the serialized archmap.json —
    the committed, machine-derived reference map the operator asked for: later
    sessions (or any tool) read the map instead of re-analyzing the codebase,
    and a PR diff of the map IS the architecture change, reviewable."""
    layers = ENTITY_CODE.get(slug)
    if not layers:
        return None
    eps = parse_endpoints(repo, layers.get("api", []))
    models = parse_models(repo, layers.get("models", []), ENTITY_MODELS.get(slug))
    schemas = parse_schemas(repo, layers.get("schemas", []))
    files = code_map(repo, layers)
    documented = {m["cls"] for m in models} | {s["cls"] for s in schemas}
    for e in eps:
        _refs = e.pop("refs")
        e["touches"] = sorted(_refs & documented)
        # the RESIDUE — bare names the handler touches that WE do not document. Raw on
        # purpose (this scan cannot see other entities); the C4 assembler intersects it
        # with the GLOBAL class index, which is what turns an aspect's coupling (allergen
        # models touched by cooking/pantry handlers) into visible cross-entity wires.
        e["touches_x"] = sorted(_refs - documented)
    return {
        "endpoints": eps, "models": models, "schemas": schemas,
        "files": [[layer, f, n] for layer, f, n in files],
        "defines": {f: parse_defines(repo, f)
                    for layer, f, _ in files if layer != "api"},
    }


# --------------------------------------------------------------------------- #
# Model insight — the DATA-MODEL lens (operator ruling 2026-07-23, spike at
# docs/investigations/2026-07-23-model-insight-spike/): every documented class
# app-wide gets machine-derived signals — usage on TWO axes (api = endpoint
# touches + FK in-degree · internal = mapped backend files referencing it),
# a BASE flag (derives from nothing), a god-class flag, and its closest
# structural twin. The same shape is built to run over other member kinds later
# (functions · methods) — scoped tables, never mixed. The generator NAMES
# candidates; verdicts stay with judgment (review / a health pass), never
# authored here. R10: usage is REPORTED, never turned into a deadness verdict —
# absence of references in the mapped set is falsified by one unmapped file.
# --------------------------------------------------------------------------- #

_GOD_FIELDS = 15
_SIM_FLOOR = 0.5
_MERGE_FLOOR = 0.8

_INS_ICONS = {
    "model": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/>',
    "schema": '<path d="M8 3H7a2 2 0 0 0-2 2v5a2 2 0 0 1-2 2 2 2 0 0 1 2 2v5c0 1.1.9 2 2 2h1"/><path d="M16 21h1a2 2 0 0 0 2-2v-5c0-1.1.9-2 2-2a2 2 0 0 1-2-2V5a2 2 0 0 0-2-2h-1"/>',
    "base": '<circle cx="12" cy="5" r="3"/><line x1="12" y1="22" x2="12" y2="8"/><path d="M5 12H2a10 10 0 0 0 20 0h-3"/>',
    "fields": '<rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/>',
    "sim": '<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
    "merge": '<circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M6 21V9a9 9 0 0 0 9 9"/>',
    "split": '<line x1="6" y1="3" x2="6" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/>',
    "doc": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>',
    "archive": '<rect x="2" y="3" width="20" height="5" rx="1"/><path d="M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8"/><line x1="10" y1="12" x2="14" y2="12"/>',
    "zap": '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    "fn": '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 17c2 0 3-1 3-3v-4c0-2 1-3 3-3"/><path d="M9 11h6"/>',
    "method": '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="12" cy="12" r="2"/>',
}


def _ins_ic(name: str) -> str:
    return ('<svg viewBox="0 0 24 24" width="13" height="13" fill="none" '
            'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            f'stroke-linejoin="round">{_INS_ICONS[name]}</svg>')


def itag(color_cls: str, icon: str, title: str, text: str = "") -> str:
    """An icon chip: the tag COLOR pair stays, the word lives in the tooltip
    and the section's ⊕ dictionary; data (a count, a twin + %) rides beside
    the icon. CONTRACT: `title` is escaped here; `text` must arrive
    PRE-ESCAPED html (call sites pass E()'d names) — do not double-escape."""
    body = _ins_ic(icon) + (f" {text}" if text else "")
    return f'<span class="tag ic {color_cls}" title="{E(title)}">{body}</span>'


_INSIGHT: dict | None = None
_DEF_SPANS: dict[str, list] = {}


def _def_spans(f: str, text: str) -> list:
    """Per-file (def name, start, end) spans, parsed once per build."""
    if f not in _DEF_SPANS:
        try:
            _DEF_SPANS[f] = [
                (n.name, n.lineno, n.end_lineno or n.lineno)
                for n in ast.walk(ast.parse(text))
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        except SyntaxError:
            _DEF_SPANS[f] = []
    return _DEF_SPANS[f]


_CENSUS: dict | None = None
_ROUTE_CENSUS: dict | None = None
_FILE_CENSUS: dict | None = None
_FLAGS: dict | None = None
_DISPATCH: dict | None = None


def _table_classes(tree) -> list[tuple[str, str]]:
    """[(cls, table)] — every top-level class with a string `__tablename__` (a REAL
    table; mixins/abstract bases without one never count)."""
    out = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        tab = _table_of(node)
        if tab is not None:
            out.append((node.name, tab))
    return out


def model_census(repo: Path, entity_code: dict | None = None,
                 entity_models: dict | None = None) -> dict:
    """The TABLE-CLASS census BEYOND the config allowlists (operator ruling 2026-08-27:
    the config decides OWNERSHIP, never EXISTENCE). center.config.json is a double
    allowlist — an entity lists its model FILES (code.models) and its model CLASSES
    (models); a table class in an unlisted file, or filtered by the class list, used
    to vanish from the map with no trace (gustify: ShoppingItem, SubscriptionEntitlement,
    SetupCompletionState, IdempotencyKey, AiSpendLog — real writes, no red wire).

    Scans every .py in the MODEL DIRS (the directories holding any configured model
    file) for classes with a string `__tablename__`, compares against the claimed
    census, and returns {scanned_dirs, claimed, unclaimed:[{cls, table, file, reason}]}
    — the block the C4 builder, the cc-init lens and pulse S11 read. Their model→table
    entries also feed the ORM-access map (fn_insight), so the C3 arm MINTS them into the
    `__unclaimed__` bucket and their access wires LAND. Honest-empty: no configured
    model file → {} (byte-identical). Deterministic: sorted dirs, files, classes."""
    global _CENSUS
    if _CENSUS is not None and entity_code is None and entity_models is None:
        return _CENSUS
    ec = ENTITY_CODE if entity_code is None else entity_code
    em = ENTITY_MODELS if entity_models is None else entity_models
    claimed_files: dict[str, str] = {}          # rel file → owning slug (first wins)
    for slug in sorted(ec):
        for f in _expand_globs(repo, ec[slug].get("models")):
            claimed_files.setdefault(f, slug)
    if not claimed_files:
        out: dict = {}
    else:
        claimed_cls: set[str] = set()
        for slug in sorted(ec):
            for m in parse_models(repo, _expand_globs(repo, ec[slug].get("models")), em.get(slug)):
                claimed_cls.add(m["cls"])
        dirs = sorted({str(Path(f).parent) for f in claimed_files})
        unclaimed: list[dict] = []
        for d in dirs:
            dp = repo / d
            if not dp.is_dir():
                continue
            for py in sorted(dp.glob("*.py")):
                rel = str(py.relative_to(repo))
                tree, _ = _safe_parse(py)
                if tree is None:
                    continue
                for cls, table in _table_classes(tree):
                    if cls in claimed_cls:
                        continue
                    owner = claimed_files.get(rel)
                    reason = (f"class not in {owner}'s models allowlist" if owner
                              else "file not in any entity's models list")
                    unclaimed.append({"cls": cls, "table": table, "file": rel, "reason": reason})
        unclaimed.sort(key=lambda u: (u["file"], u["cls"]))
        out = {"scanned_dirs": dirs, "claimed": len(claimed_cls), "unclaimed": unclaimed}
    if entity_code is None and entity_models is None:
        _CENSUS = out
    return out


def _count_callables(tree) -> int:
    """Every ``def``/``async def`` ANYWHERE in the file — top-level functions, class methods
    AND nested/local helpers (``ast.walk`` descends into bodies). A rough callable-mass signal
    for the file census's ranking, never a gate; an over-count of nested closures is acceptable."""
    return sum(1 for n in ast.walk(tree)
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))


# Files a census must never nag about even when they sit unclaimed in a scanned dir.
_CENSUS_SKIP = ("__init__.py", "conftest.py")


def route_census(repo: Path, entity_code: dict | None = None) -> dict:
    """The ROUTE-FILE census BEYOND the config api allowlists — same ruling as
    :func:`model_census` (config decides ownership, never existence). center.config.json
    lists an entity's route FILES (``code.api``); a route-bearing ``.py`` sitting in one of
    those api dirs but claimed by no entity used to vanish — every downstream arm keys off
    ``entities[*].endpoints`` (gustify: equipment/meal_plan/e2e_seed/locale/health routes).

    Scans every ``.py`` in the API DIRS (the directories holding any configured api file) for
    route decorators (:func:`parse_endpoints`), skips the claimed set, and returns
    ``{scanned_dirs, claimed, unclaimed:[{file, routes, methods, reason}]}``. Emitted-only-when-
    non-empty is the P5 rule: ``{}`` when there is no api config OR nothing unclaimed to report,
    so a project with full route coverage carries NO ``route_census`` key (byte-identical).
    Deterministic: sorted dirs, files, methods. Cached like the sibling censuses."""
    global _ROUTE_CENSUS
    if _ROUTE_CENSUS is not None and entity_code is None:
        return _ROUTE_CENSUS
    ec = ENTITY_CODE if entity_code is None else entity_code
    claimed: set[str] = set()
    for slug in sorted(ec):
        for f in (ec[slug].get("api") or []):
            claimed.add(f)
    out: dict = {}
    if claimed:
        dirs = sorted({str(Path(f).parent) for f in claimed})
        unclaimed: list[dict] = []
        for d in dirs:
            dp = repo / d
            if not dp.is_dir():
                continue
            for py in sorted(dp.glob("*.py")):
                rel = str(py.relative_to(repo))
                if (rel in claimed or py.name in _CENSUS_SKIP
                        or py.name.startswith("test_") or ".test." in py.name):   # test routers are not prod routes (parity with file_census)
                    continue
                routes = parse_endpoints(repo, [rel])
                if not routes:
                    continue
                unclaimed.append({"file": rel, "routes": len(routes),
                                  "methods": sorted({r["method"] for r in routes}),
                                  "reason": "route file not in any entity's api list"})
        unclaimed.sort(key=lambda u: u["file"])
        if unclaimed:                              # P5: no key at all when nothing to nag about
            out = {"scanned_dirs": dirs, "claimed": len(claimed), "unclaimed": unclaimed}
    if entity_code is None:
        _ROUTE_CENSUS = out
    return out


def file_census(repo: Path, entity_code: dict | None = None) -> dict:
    """The BACKEND-FILE census BEYOND the config code allowlists — the broad sibling of
    :func:`route_census`. An entity's ``code.<layer>`` lists name its files; a ``.py`` in one
    of those dirs that no entity claims drops the file AND every call touching it (graft homes
    by file → entity), so ``function_insight`` never walks it and the ``behind`` pill counts
    fns the walk cannot reach (gustify: 52 files · 233 callables in unclaimed files).

    Scans every ``.py`` in the CODE DIRS (the directories holding any configured PYTHON file,
    across every declared layer), skips the claimed set, and returns
    ``{scanned_dirs, claimed, unclaimed:[{file, routes, fns, tables, reason}]}`` — the block
    pulse S13 and the cc-init adopt rail read; a build-time :func:`~_a3_graft.reach_arm` pass
    adds an optional ``reach`` (min call-hops from a mapped handler) per entry. A file with no
    route, fn or table (a bare ``__init__``/constants module) is not nagged. P5 honest-empty:
    ``{}`` when there is no python code config OR nothing unclaimed (byte-identical). Only the
    dirs the config already reaches are scanned — a fully-orphan dir (no claimed sibling) is
    surfaced by the layer report + the operator's claims, never guessed here.
    Deterministic: sorted dirs, files. Cached."""
    global _FILE_CENSUS
    if _FILE_CENSUS is not None and entity_code is None:
        return _FILE_CENSUS
    ec = ENTITY_CODE if entity_code is None else entity_code
    claimed: set[str] = set()
    dirs_set: set[str] = set()
    for slug in sorted(ec):
        for layer in _CODE_LAYERS:
            for pat in (ec[slug].get(layer) or []):
                for f in sorted(_glob.glob(str(repo / pat), recursive=True)):
                    p = Path(f)
                    if p.is_file() and p.suffix == ".py":
                        rel = str(p.relative_to(repo))
                        claimed.add(rel)
                        dirs_set.add(str(Path(rel).parent))
    out: dict = {}
    if dirs_set:
        dirs = sorted(dirs_set)
        unclaimed: list[dict] = []
        for d in dirs:
            dp = repo / d
            if not dp.is_dir():
                continue
            for py in sorted(dp.glob("*.py")):
                rel = str(py.relative_to(repo))
                if (rel in claimed or py.name in _CENSUS_SKIP
                        or py.name.startswith("test_") or ".test." in py.name):
                    continue
                tree, _ = _safe_parse(py)
                if tree is None:
                    continue
                routes = len(parse_endpoints(repo, [rel]))
                fns = _count_callables(tree)
                tables = len(_table_classes(tree))
                if routes == 0 and fns == 0 and tables == 0:   # bare __init__/constants — nothing to home
                    continue
                unclaimed.append({"file": rel, "routes": routes, "fns": fns,
                                  "tables": tables,
                                  "reason": "file not in any entity's code map"})
        unclaimed.sort(key=lambda u: u["file"])
        if unclaimed:                              # P5: no key at all when nothing to nag about
            out = {"scanned_dirs": dirs, "claimed": len(claimed), "unclaimed": unclaimed}
    if entity_code is None:
        _FILE_CENSUS = out
    return out


def undeclared_layers(entity_code: dict | None = None) -> list[tuple[str, str]]:
    """(slug, layer) pairs where an entity's ``code`` block names a layer that ``_CODE_LAYERS``
    does NOT declare — a SILENT no-op today (``code_map`` iterates ``_CODE_LAYERS`` only, so a
    ``code.reference`` list a project adds is dropped with no trace). The build prints a report
    line from this so a claim under an unlisted layer is visible, never lost. Sorted; ``[]``
    when every claimed layer is declared (the common case)."""
    ec = ENTITY_CODE if entity_code is None else entity_code
    declared = set(_CODE_LAYERS)
    out: list[tuple[str, str]] = []
    for slug in sorted(ec):
        for layer in (ec[slug] or {}):
            if layer not in declared:
                out.append((slug, layer))
    return sorted(out)


def parse_boot_roots(repo: Path, entity_code: dict | None = None) -> list[dict]:
    """BOOT roots (class 7): the lifespan / startup fn that runs ONCE at app boot — ``FastAPI(
    lifespan=F)`` or ``@app.on_event('startup')``. main.py is UNCLAIMED (it sits above the route
    dirs), so its boot writers (the catalog/reference seeders) never drew. Scans main.py/app.py in
    the api dirs and returns endpoint-shaped records ``{method:'BOOT', path, fn, file, touches,
    touches_x, doc, resp, status}`` — the C4 mints a ``BOOT lifespan`` node from them, homed to
    __unclaimed__. ``[]`` honest-empty (no lifespan/startup → byte-identical, P5). Deterministic."""
    ec = ENTITY_CODE if entity_code is None else entity_code
    _dset: set = set()
    for slug in sorted(ec):
        for f in _expand_globs(repo, ec[slug].get("api")):
            _dset.add(str(Path(f).parent))
            _dset.add(str(Path(f).parent.parent))       # main.py/app.py sit one dir up from the routes
    out: list[dict] = []
    seen: set = set()
    for d in sorted(_dset):
        dp = repo / d
        for name in ("main.py", "app.py"):
            py = dp / name
            if not py.is_file():
                continue
            rel = str(py.relative_to(repo))
            tree, _ = _safe_parse(py)
            if tree is None:
                continue
            roots: list[str] = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "FastAPI":
                    for kw in node.keywords:
                        if kw.arg == "lifespan":
                            fn = (kw.value.id if isinstance(kw.value, ast.Name)
                                  else kw.value.attr if isinstance(kw.value, ast.Attribute) else None)
                            if fn:
                                roots.append(fn)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for dec in node.decorator_list:
                        if (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)
                                and dec.func.attr == "on_event" and dec.args
                                and isinstance(dec.args[0], ast.Constant) and dec.args[0].value == "startup"):
                            roots.append(node.name)
            for fn in roots:
                if (rel, fn) in seen:
                    continue
                seen.add((rel, fn))
                out.append({"method": "BOOT", "path": fn, "fn": fn, "file": rel,
                            "touches": [], "touches_x": [], "doc": "—", "resp": "—", "status": "boot"})
    # disambiguate the node id (BOOT method + path) ONLY on a real collision (review fix [10]: two
    # `lifespan` roots in different services share `endpoint:BOOT lifespan` → add_node drops the
    # second). Single-boot repos are untouched → byte-identical (P5).
    _fn_ct: dict = {}
    for r in out:
        _fn_ct[r["fn"]] = _fn_ct.get(r["fn"], 0) + 1
    for r in out:
        if _fn_ct[r["fn"]] > 1:
            r["path"] = f"{r['fn']} @{Path(r['file']).parent.name or Path(r['file']).stem}"
    out.sort(key=lambda r: (r["file"], r["fn"]))
    return out


def parse_flags(repo: Path, entity_code: dict | None = None) -> dict:
    """FEATURE-FLAG census (coverage class 12): the config bools whose OFF state walls a route or a
    lane. Two idioms, from the SAME dirs the code map reaches PLUS their immediate parents (a
    ``config.py`` / ``constants.py`` sits ABOVE the api/services dirs): a pydantic ``BaseSettings``/
    ``Settings`` class's ``bool`` fields, and a module-level ``Final[bool]`` constant. Returns
    ``{name: {src, line, default}}`` — the block the walls detector keys against and the C4 flag node
    reads. ``{}`` honest-empty (no Settings bool, no module ``Final[bool]`` → byte-identical, P5).
    Deterministic: sorted dirs, files, fields. Cached."""
    global _FLAGS
    if _FLAGS is not None and entity_code is None:
        return _FLAGS
    ec = ENTITY_CODE if entity_code is None else entity_code
    dirs: set = set()
    for slug in sorted(ec):
        for layer in _CODE_LAYERS:
            for pat in (ec[slug].get(layer) or []):
                for f in sorted(_glob.glob(str(repo / pat), recursive=True)):
                    p = Path(f)
                    if p.is_file() and p.suffix == ".py":
                        dirs.add(p.parent)
                        dirs.add(p.parent.parent)   # config.py/constants.py live one dir up
    flags: dict = {}

    def _bool_const(val):
        return val.value if isinstance(val, ast.Constant) and isinstance(val.value, bool) else None

    for d in sorted(dirs, key=str):
        if not d.is_dir():
            continue
        for py in sorted(d.glob("*.py")):
            if repo not in py.parents:                  # grandparent-of-a-root-file can sit ABOVE repo
                continue                                 # (review fix [4]: relative_to would abort the whole build)
            tree, _ = _safe_parse(py)
            if tree is None:
                continue
            rel = str(py.relative_to(repo))
            for node in tree.body:
                if isinstance(node, ast.ClassDef) and any(
                        (getattr(b, "id", "") or getattr(b, "attr", "")) in ("BaseSettings", "Settings")
                        for b in node.bases):
                    for item in node.body:
                        if (isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
                                and ast.unparse(item.annotation).strip() in ("bool", "Final[bool]")):
                            flags.setdefault(item.target.id, {"src": rel, "line": item.lineno,
                                                              "default": _bool_const(item.value)})
                elif (isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
                      and ast.unparse(node.annotation).strip() == "Final[bool]"):
                    flags.setdefault(node.target.id, {"src": rel, "line": node.lineno,
                                                      "default": _bool_const(node.value)})
    out = dict(sorted(flags.items()))
    if entity_code is None:
        _FLAGS = out
    return out


def _flag_leaves(test, flags: dict) -> list[tuple[str, str]]:
    """Every flag-name leaf in an ``ast.If`` test + its polarity. ``if not FLAG:`` → (FLAG, 'off',
    OFF walls); ``if FLAG:`` → (FLAG, 'on'). A leaf is a bare ``Name`` (a constant) OR an
    ``Attribute`` whose ``.attr`` names the field, regardless of receiver (``settings.x`` AND
    ``get_settings().x`` both → ``x``). A COMPOUND test — ``not (RECIPE_CREATION_ENABLED or
    settings.recipe_creation_enabled)``, the effective-flag idiom — walls on BOTH flags (the
    ``BoolOp`` is walked). Only names IN ``flags`` count; ``[]`` when the test names no flag."""
    on = "on"
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        test, on = test.operand, "off"
    leaves: list[str] = []

    def _collect(node):
        if isinstance(node, ast.BoolOp):
            for v in node.values:
                _collect(v)
        elif isinstance(node, ast.Name) and node.id in flags:
            leaves.append(node.id)
        elif isinstance(node, ast.Attribute) and node.attr in flags:
            leaves.append(node.attr)

    _collect(test)
    return [(n, on) for n in leaves]


def _raise_status(rz) -> str:
    """The 403/404 (or the exception class name) a ``raise`` carries — the wall's ``on_fail``."""
    exc = rz.exc
    if isinstance(exc, ast.Call):
        for kw in exc.keywords:
            if kw.arg == "status_code" and isinstance(kw.value, ast.Constant):
                return str(kw.value.value)
        for a in exc.args:
            if isinstance(a, ast.Constant) and isinstance(a.value, int):
                return str(a.value)
        return _call_bare(exc.func) or (exc.func.attr if isinstance(exc.func, ast.Attribute) else "raise")
    return exc.id if isinstance(exc, ast.Name) else "raise"


def _flag_gates(fnnode, flags: dict) -> list[dict]:
    """The feature-flag WALLS in one function: an ``if <flag>: raise`` clock. A wall fires ONLY
    when the guarded body RAISES — ``if not flag: return`` is an ARM, not a wall (honest floor, a
    later ``arms`` wire). ``[{name, on, on_fail, line}]`` sorted, ``[]`` when none (P5)."""
    if not flags:
        return []
    out: list[dict] = []
    for n in ast.walk(fnnode):
        if not isinstance(n, ast.If):
            continue
        leaves = _flag_leaves(n.test, flags)
        if not leaves:
            continue
        rz = next((s for stmt in n.body for s in ast.walk(stmt) if isinstance(s, ast.Raise)), None)
        if rz is None:                              # if not flag: return → an ARM, never a wall
            continue
        _of = _raise_status(rz)
        for name, on in leaves:
            out.append({"name": name, "on": on, "on_fail": _of, "line": n.lineno})
    out.sort(key=lambda w: (w["name"], w["line"]))
    _seen: set = set()                                  # one wall per (flag, on) — review fix [1]: a
    _dedup = []                                          # doubly-guarded handler otherwise double-counts
    for w in out:                                        # toward _FLAG_SAT and draws two identical wires
        if (w["name"], w["on"]) in _seen:
            continue
        _seen.add((w["name"], w["on"]))
        _dedup.append(w)
    return _dedup


def home_schemas(entities: dict, function_insight: dict | None = None) -> dict:
    """SCHEMA HOMING (operator ruling 2026-08-27): a schema lives where its CONSUMER lives,
    not where its FILE was claimed. center.config.json claims schema FILES per entity, and a
    file is one entity's — so gustify drew allergen's ``schemas/preferences.py`` shapes under
    allergen though every one of them is a field of auth's ``SetupCompleteRequest`` or the body
    of a settings route, and progression's ``responses.py`` carried ``MeResponse`` (auth) and
    ``SettingsResponse`` (settings). A file claim cannot split a file; this pass can.

    Inputs are the archmap's OWN facts — no new source read:
      * endpoint consumers — an endpoint of entity S names the class in
        ``touches ∪ touches_x ∪ resp`` (the same bare-name floor the touches wire rides);
      * function consumers — a claimed (entity-stamped, non-handler) function ``returns`` it,
        ``takes`` it (param annotation) or ``uses`` it (a body identifier) — the service-consumed
        schemas no handler ever names (gustify's gastify exchange contract);
      * parents — a schema whose field TYPE names the class (the ``nests`` source).
    Rule, per schema, endpoint consumers OUTRANKING function consumers (a route is the stronger
    ownership signal): exactly ONE consumer entity → move there; no consumer but parents that all
    resolve to ONE entity → follow the parent (transitive, cycle-safe); otherwise stay
    (``own`` | ``ambiguous`` | ``unwired``) — never guessed, always reported.

    MUTATES ``entities`` in place: the schema dict moves between ``entities[*]["schemas"]``
    (appended, sorted by class — untouched entities keep their byte order) and is stamped
    ``homed_from`` + ``homed_why`` (the C4 node and its card carry the provenance). Returns the
    stats block for ``amap["schema_homing"]`` → pulse S12 / ``c4.stats.schema_homing`` /
    the levels ``schema_edges`` feed:
      {"moved": [{cls, from, to, why}], "ambiguous": [{cls, home, consumers}],
       "unwired": [{cls, home, file, dormant}], "fn_wires": [{fn, cls, rel, slug}]}
    ``dormant`` = unwired AND no class of its FILE is endpoint-consumed — a contract lane no
    route reaches yet; the tag self-clears the build a route names any class of that file.
    Honest-empty: no schema, or nothing to move → empty lists and ``entities`` untouched
    (every downstream feed byte-identical). Deterministic: sorted slugs, classes, functions."""
    import re as _re
    idx: dict[str, tuple[str, dict]] = {}          # cls → (file-home slug, schema dict); first wins
    for slug in sorted(entities):
        for sc in ((entities.get(slug) or {}).get("schemas") or []):
            if sc.get("cls"):
                idx.setdefault(sc["cls"], (slug, sc))
    empty = {"moved": [], "ambiguous": [], "unwired": [], "fn_wires": []}
    if not idx:
        return empty
    _cls_rx = _re.compile(r"[A-Z][A-Za-z0-9_]+")
    ep_cons: dict[str, dict[str, str]] = {c: {} for c in idx}   # cls → {slug: first endpoint label}
    file_hit: set[str] = set()                                    # files with ≥1 endpoint-consumed class
    for slug in sorted(entities):
        for ep in ((entities.get(slug) or {}).get("endpoints") or []):
            label = f"{ep.get('method', '')} {ep.get('path', '')}".strip()
            names = set(ep.get("touches") or []) | set(ep.get("touches_x") or [])
            names |= {m for m in _cls_rx.findall(str(ep.get("resp") or "")) if m != "None"}
            for c in sorted(names):
                if c in idx:
                    ep_cons[c].setdefault(slug, label)
                    file_hit.add(idx[c][1].get("file") or "")
    fn_cons: dict[str, dict[str, str]] = {c: {} for c in idx}
    fn_wires: list[dict] = []
    for key in sorted(function_insight or {}):
        rec = function_insight[key] or {}
        ent = rec.get("entity")
        if not ent or rec.get("handler"):          # a handler's consumption IS its endpoint's
            continue
        fid = f"{rec.get('file', '')}#{rec.get('fn', '')}"
        _own = str(rec.get("fn") or "").split(".", 1)[0] if rec.get("method") else None   # a schema's OWN
        rets = {m for m in _cls_rx.findall(str(rec.get("returns") or "")) if m in idx}
        takes: set[str] = set()
        for _p in (rec.get("params") or []):
            ann = _p[1] if isinstance(_p, (list, tuple)) and len(_p) > 1 else ""
            takes |= {m for m in _cls_rx.findall(str(ann or "")) if m in idx}
        uses = {m for m in (rec.get("ids") or ()) if m in idx} - rets - takes
        for rel, group in (("returns", rets), ("takes", takes - rets), ("uses", uses)):
            for c in sorted(group):
                if c == _own:                      # validator/helper method on the class itself — not a consumer
                    continue
                fn_cons[c].setdefault(ent, fid)
                fn_wires.append({"fn": fid, "cls": c, "rel": rel, "slug": ent})
    parents: dict[str, set[str]] = {c: set() for c in idx}
    for c, (_slug, sc) in idx.items():
        for fld in (sc.get("fields") or []):
            ftype = fld[1] if isinstance(fld, (list, tuple)) and len(fld) > 1 else ""
            for m in _cls_rx.findall(str(ftype or "")):
                if m in idx and m != c:
                    parents[m].add(c)
    home = {c: slug for c, (slug, _sc) in idx.items()}
    resolved: dict[str, str] = {}
    why: dict[str, str] = {}

    def _resolve(c: str, stack: tuple = ()) -> str:
        if c in resolved:
            return resolved[c]
        if c in stack:                              # composition cycle → the file home, no recursion
            return home[c]
        cons = ep_cons[c] or fn_cons[c]
        if len(cons) == 1:
            slug = next(iter(cons))
            r = slug
            why[c] = ("consumed-by:" if ep_cons[c] else "fn-consumed-by:") + cons[slug]
        elif len(cons) > 1:
            r = home[c]
            why[c] = "ambiguous:" + ",".join(sorted(cons))
        elif parents[c]:
            ph = {_resolve(p, stack + (c,)) for p in sorted(parents[c])}
            if len(ph) == 1:
                r = ph.pop()
                why[c] = "nested-in:" + ",".join(sorted(parents[c]))
            else:
                r = home[c]
                why[c] = "ambiguous-parents:" + ",".join(sorted(ph))
        else:
            r = home[c]
            why[c] = "unwired"
        resolved[c] = r
        return r

    for c in sorted(idx):
        _resolve(c)
    moved: list[dict] = []
    for c in sorted(idx):
        src, to = home[c], resolved[c]
        if to == src or to not in entities or entities.get(to) is None:
            continue
        sc = idx[c][1]
        lst = (entities.get(src) or {}).get("schemas") or []
        if sc in lst:
            lst.remove(sc)
        sc["homed_from"] = src
        sc["homed_why"] = why[c]
        entities[to].setdefault("schemas", []).append(sc)
        moved.append({"cls": c, "from": src, "to": to, "why": why[c]})
    ambiguous = [{"cls": c, "home": home[c],
                  "consumers": sorted((ep_cons[c] or fn_cons[c]) if why[c].startswith("ambiguous:")
                                      else set(why[c].split(":", 1)[1].split(",")))}
                 for c in sorted(idx) if why[c].startswith("ambiguous")]
    unwired = [{"cls": c, "home": home[c], "file": idx[c][1].get("file") or "",
                "dormant": (idx[c][1].get("file") or "") not in file_hit}
               for c in sorted(idx) if why[c] == "unwired"]
    return {"moved": moved, "ambiguous": ambiguous, "unwired": unwired,
            "fn_wires": sorted(fn_wires, key=lambda w: (w["fn"], w["cls"], w["rel"]))}


def model_insight(repo: Path) -> dict:
    """{cls: signals} across EVERY documented class app-wide — computed once
    per build off the cached entity maps + one word-boundary scan of the
    mapped backend files. Serialized into archmap.json as `model_insight`."""
    global _INSIGHT
    if _INSIGHT is not None:
        return _INSIGHT
    classes: dict[str, dict] = {}
    table_owner: dict[str, str] = {}
    all_eps: list[dict] = []
    py_files: set[str] = set()
    for slug in ENTITY_CODE:
        v = collect_entity_map(slug, repo)
        if not v:
            continue
        all_eps.extend(v["endpoints"])
        for _layer, f, _n in v["files"]:
            if f.endswith(".py"):
                py_files.add(f)
        # FIRST registration wins, matching merge_amaps' setdefault rule — a
        # last-wins here once let the Entity column name the WRONG owner for
        # a class's own row (review H2). A same-named class in a DIFFERENT
        # file is a collision: recorded, warned once per build, first owner
        # kept deterministically (config entity order).
        for m in v["models"]:
            prev = classes.get(m["cls"])
            if prev and prev["file"] != m["file"]:
                prev.setdefault("collides", []).append(m["file"])
            classes.setdefault(m["cls"], {
                "cls": m["cls"], "kind": "model", "entity": slug,
                "file": m["file"], "fields": m["cols"],
                "fks_out": m.get("fks", {})})
            table_owner.setdefault(m.get("table", ""), m["cls"])
        for s in v["schemas"]:
            prev = classes.get(s["cls"])
            if prev and prev["file"] != s["file"]:
                prev.setdefault("collides", []).append(s["file"])
            classes.setdefault(s["cls"], {
                "cls": s["cls"], "kind": "schema", "entity": slug,
                "file": s["file"], "fields": s["fields"], "fks_out": {}})
    texts = {}
    for f in sorted(py_files):
        p = repo / f
        if p.exists():
            texts[f] = _safe_read(p) or ""
    names = set(classes)
    for c in classes.values():
        c["touches"] = sum(1 for e in all_eps if c["cls"] in e.get("touches", []))
        tgt = {t for t, owner in table_owner.items() if owner == c["cls"]}
        c["fk_in"] = sum(1 for o in classes.values() if o is not c
                         for ref in o["fks_out"].values()
                         if str(ref).split(".")[0] in tgt)
        refs_out = {n for n in names if n != c["cls"]
                    and any(n in str(t) for _f in [c["fields"]] for _n, t, *_ in _f)}
        c["base"] = not c["fks_out"] and not refs_out
        c["god"] = len(c["fields"]) >= _GOD_FIELDS
        c["usage"] = c["touches"] + c["fk_in"]
        rx = _re_mod.compile(rf"\b{_re_mod.escape(c['cls'])}\b")
        c["internal_files"] = sorted(f for f, t in texts.items()
                                     if f != c["file"] and rx.search(t))
        c["internal"] = len(c["internal_files"])
        # WHICH defs in each referencing file mention the class — for the
        # detail's "Usage by internal" table (file · functions).
        c["internal_refs"] = []
        for f in c["internal_files"]:
            lines = texts[f].splitlines()
            defs = [name for name, s, e in _def_spans(f, texts[f])
                    if rx.search("\n".join(lines[s - 1:e]))]
            c["internal_refs"].append(
                {"file": f, "defs": list(dict.fromkeys(defs))[:6]})
    for c in classes.values():
        mine = {n for n, *_ in c["fields"]}
        best, best_j, shared = "", 0.0, 0
        for o in classes.values():
            if o is c:
                continue
            theirs = {n for n, *_ in o["fields"]}
            union = mine | theirs
            j = len(mine & theirs) / len(union) if union else 0.0
            if j > best_j:
                best, best_j, shared = o["cls"], j, len(mine & theirs)
        c["sim"] = ({"cls": best, "j": round(best_j, 2), "shared": shared,
                     "of": len(mine)} if best_j >= _SIM_FLOOR else None)
    _collided = sorted(c["cls"] for c in classes.values() if c.get("collides"))
    if _collided:
        print(f"    ⚠ class name collision(s) across entities — first owner "
              f"wins, cross-references may under-resolve: "
              + " · ".join(_collided[:8])
              + (" …" if len(_collided) > 8 else ""))
    _INSIGHT = classes
    return classes


# --------------------------------------------------------------------------- #
# Function insight — the FUNCTIONS lens, sibling of the data-model lens (same
# dialect: icon tags · chips · two-bar usage · candidates), with the
# function-shaped equivalents: kind = function | method | endpoint handler;
# BASE = calls no other documented function; god = length ≥ _FN_GOD_LINES;
# twin = body-identifier Jaccard. Same-file references OUTSIDE the def's own
# span COUNT as internal usage — a helper called within its module is used
# (a class merely living in its file is not). Usage is EVIDENCE, never a
# deadness verdict (R10): the refs scan sees only config-mapped Python, so
# "no mapped caller" says as much about the config as about the code.
# --------------------------------------------------------------------------- #

_FN_GOD_LINES = 50
_FN_SIM_FLOOR = 0.6
_FN_MERGE_FLOOR = 0.85
# SCALE (review 2026-09-06, onyx: 9,234 mapped defs → 42 M pairwise Jaccards + a regex per (fn, file) — the build sat
# 10 minutes in this pass on a study repo). Two moves, both NAMED on the archmap (`fn_similarity`):
#   · the reference scan pre-tokenizes every file ONCE and runs the regex only where the fn's name is a token —
#     exact (a `\bname\b` match implies the token), so every twin stays byte-identical;
#   · the twin pass stays the exact pairwise loop up to `_FN_TWIN_BUDGET` sizable functions (gustify 522); above it
#     candidates are BLOCKED on shared RARE identifiers (document frequency ≤ `_FN_RARE_DF`) — an approximation that
#     can miss a twin sharing only common names, said out loud as mode "blocked".
_FN_TWIN_BUDGET = 2500
_FN_RARE_DF = 40
_FN_SIM_MODE: dict = {}
_IDENT_RX = _re_mod.compile(r"[A-Za-z_]\w*")


def fn_similarity_mode() -> dict:
    """{mode: exact | blocked, sizable, budget[, rare_df]} for THIS build — {} until function_insight ran."""
    return dict(_FN_SIM_MODE)
_FN_INSIGHT: dict | None = None
_PY_TEXTS: dict[str, str] = {}
_FILE_IMPORTS: dict[str, dict] = {}


def _file_imports(f: str) -> dict:
    """{imported local name: app-internal?} for one mapped file — the machine
    rule behind the 'to be designed' label: a CamelCase name imported from
    THIS app's own packages (or relatively) is ours to document someday; a
    third-party import never is."""
    if f in _FILE_IMPORTS:
        return _FILE_IMPORTS[f]
    if f not in _PY_TEXTS:
        return {}   # unknown text: DON'T cache emptiness (fill order, M5)
    text = _PY_TEXTS[f]
    # App-internal = the module's root is any DIRECTORY segment of the mapped
    # paths (the disk root and the import root often differ — apps/api/… on
    # disk imports as api.…, so the first-segment-only rule missed everything).
    tops = {seg for p in _PY_TEXTS for seg in p.split("/")[:-1]}
    out: dict = {}
    try:
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.ImportFrom):
                app = (node.level or 0) > 0 or \
                      (node.module or "").split(".")[0] in tops
                for a in node.names:
                    out[a.asname or a.name] = app
            elif isinstance(node, ast.Import):
                for a in node.names:
                    out[(a.asname or a.name).split(".")[0]] = \
                        a.name.split(".")[0] in tops
    except SyntaxError:
        pass
    _FILE_IMPORTS[f] = out
    return out
_PY_KEYWORDS = frozenset(
    "self None True False return yield await async lambda pass break continue "
    "import from raise assert global nonlocal print range list dict set tuple "
    "type isinstance issubclass super property staticmethod classmethod".split())


# ── ORM data-access detection (C2) — the write graft cannot see ─────────────
# graft resolves 0 edges for session.add/select/execute (untyped receiver → an
# un-indexed library method). So we read the access off the AST we already walk:
# READS are a near-census (the model is a LITERAL arg — select(Model)); WRITES use
# a per-function var→class symtab built from `x = Model(...)` constructor assigns —
# the dominant idiom. The honest floor: an object bound OUTSIDE the function is an
# under-count, never a wrong table. Model→table via __tablename__ (already parsed).
_ORM_WRITE_M = frozenset({"add", "add_all", "delete", "merge",
                          "bulk_save_objects", "bulk_insert_mappings"})   # session.<m>(obj)
_ORM_WRITE_CORE = frozenset({"insert", "update", "delete"})              # <core>(Model)
_ORM_READ_CORE = frozenset({"select"})                                  # select(Model)
_ORM_COMMIT = frozenset({"commit", "flush"})


def _model_table_map(trees: dict) -> dict[str, str]:
    """{ModelClassName: table} across all parsed files — a write can target a model
    declared in another file, so the map is global before the per-fn walk."""
    m2t: dict[str, str] = {}
    for tree in trees.values():
        for node in getattr(tree, "body", []):
            if not isinstance(node, ast.ClassDef):
                continue
            tab = _table_of(node)
            if tab is not None:
                m2t[node.name] = tab
    return m2t


def _call_attr(func) -> str | None:      # x.method(...) → "method"
    return func.attr if isinstance(func, ast.Attribute) else None


def _call_bare(func) -> str | None:      # foo(...) / Model(...) → "foo" / "Model"
    return func.id if isinstance(func, ast.Name) else None


def _orm_access(fnnode, m2t: dict[str, str]) -> dict:
    """{'ops': [{'model','table','rw'}], 'commits': bool} for one function, or {}.

    B1 (the ORM substrate, 2026-08-27) widened the near-census: the symtab now binds a var
    from four more idioms besides the constructor (a Model-annotated PARAM · ``x = session.get
    (Model, id)`` · ``for row in <bound>``), an ATTRIBUTE-WRITE (``user.col = v`` / ``+=`` on a
    bound Model — the write that has no flush yet, decision 3: NOT flush-gated), and the ROOT of a
    ``select(Model.col)`` / ``.join(Model)`` / ``.select_from(Model)`` chain (a column select the
    old bare-Name rule ignored). Residual floors stay honest: a cross-file helper return, a
    dict-comprehension binding and a multi-model select still under-count, never mis-table."""
    if not m2t:
        return {}

    def _name_model(arg) -> str | None:           # select(Model) — a bare class literal
        return arg.id if isinstance(arg, ast.Name) and arg.id in m2t else None

    def _root_model(arg) -> str | None:           # the Model at the ROOT of an attr/select chain:
        while isinstance(arg, ast.Attribute):     # Model.col → Model ; a.b.c → a
            arg = arg.value
        return arg.id if isinstance(arg, ast.Name) and arg.id in m2t else None

    symtab: dict[str, str] = {}   # local var / param → model class
    # (B1) Model-annotated PARAMS: def f(x: Model) / f(x: Model | None) → x is that Model
    _params = (list(getattr(fnnode.args, "posonlyargs", []))
               + list(getattr(fnnode.args, "args", []))
               + list(getattr(fnnode.args, "kwonlyargs", [])))
    for _a in _params:
        if _a.annotation is not None:
            for _tok in _re_mod.findall(r"[A-Za-z_][A-Za-z0-9_]*", ast.unparse(_a.annotation)):
                if _tok in m2t:
                    symtab[_a.arg] = _tok
                    break
    for n in ast.walk(fnnode):
        if (isinstance(n, ast.Assign) and len(n.targets) == 1
                and isinstance(n.targets[0], ast.Name) and isinstance(n.value, ast.Call)):
            b = _call_bare(n.value.func)
            if b in m2t:                                               # x = Model(...)
                symtab[n.targets[0].id] = b
            elif _call_attr(n.value.func) == "get" and n.value.args and _name_model(n.value.args[0]):
                symtab[n.targets[0].id] = _name_model(n.value.args[0])  # (B1) x = session.get(Model, id)
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.annotation is not None:
            a = ast.unparse(n.annotation)
            if a in m2t:
                symtab[n.target.id] = a
        elif (isinstance(n, ast.For) and isinstance(n.target, ast.Name)
              and isinstance(n.iter, ast.Name) and n.iter.id in symtab):
            symtab[n.target.id] = symtab[n.iter.id]                     # (B1) for row in <bound> → row is that model

    def _arg_model(arg) -> str | None:            # session.add(x) — x local or inline Model(...)
        if isinstance(arg, ast.Name):
            return symtab.get(arg.id)
        if isinstance(arg, ast.Call) and _call_bare(arg.func) in m2t:
            return _call_bare(arg.func)
        return None

    ops: dict[tuple, dict] = {}
    commits = False
    serial: list[dict] = []                    # class 5b: X.model_validate(v) sites → schema serializes model

    def _put(model, rw):
        if model:
            ops[(model, rw)] = {"model": model, "table": m2t[model], "rw": rw}

    for n in ast.walk(fnnode):
        # (B1) ATTRIBUTE WRITE: <bound>.col = v / <bound>.col += v — a pending write on a bound
        # Model (not flush-gated, decision 3). A non-Model receiver binds nothing → no-op.
        if isinstance(n, (ast.Assign, ast.AugAssign)):
            for _t in (n.targets if isinstance(n, ast.Assign) else [n.target]):
                if isinstance(_t, ast.Attribute) and isinstance(_t.value, ast.Name):
                    _put(symtab.get(_t.value.id), "w")
        if not isinstance(n, ast.Call):
            continue
        attr, bare = _call_attr(n.func), _call_bare(n.func)
        # (class 5b) SITE arm: `Schema.model_validate(v)` / `.model_validate_json(v)` — the schema
        # SERIALIZES the model bound to v (resolved through the B1 symtab). The schema name is raw
        # here (not in m2t); build_c4_graph resolves it to a schema node. model:None = a residual
        # floor (a callee-return/tuple arg the symtab can't bind) — recorded, never guessed.
        if (attr in ("model_validate", "model_validate_json")
                and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.args):
            serial.append({"cls": n.func.value.id, "model": _arg_model(n.args[0]), "line": n.lineno})
        if attr in _ORM_WRITE_M and n.args:
            _put(_arg_model(n.args[0]), "w")
        if attr == "get" and n.args:                                  # session.get(Model, id)
            _put(_name_model(n.args[0]), "r")
        if bare in _ORM_READ_CORE:                                    # select(Model) OR select(Model.col) (B1)
            for a in n.args:
                _put(_name_model(a) or _root_model(a), "r")
        if attr in ("join", "select_from") and n.args:                # (B1) .join(Model) / .select_from(Model)
            _put(_name_model(n.args[0]) or _root_model(n.args[0]), "r")
        if bare in _ORM_WRITE_CORE:                                   # Core insert/update/delete(Model[.col])
            for a in n.args:
                _put(_name_model(a) or _root_model(a), "w")
        if attr in _ORM_COMMIT:
            commits = True
    out = sorted(ops.values(), key=lambda x: (x["rw"], x["model"]))
    res: dict = {"ops": out, "commits": commits}
    if serial:                                 # class 5b: emit only when a model_validate site exists (P5)
        res["serializes"] = sorted(serial, key=lambda s: (s["cls"], s["line"]))
    return res if (out or commits or serial) else {}


# ── C4 · NON-ORM SINK floor (file · cache · queue/event · http) ─────────────
# A coarse CATEGORY floor (view-only, honest), NOT an edge — a file/cache/queue has no
# model node to point at. Conservative idioms keep false-positives low: a bare `.set(`/
# `.send(` never fires — the receiver must name the sink (redis/cache/bus/…), or the call
# must be an unambiguous write (open(…, "w"), .write_text). Borrowed shape: codesight's
# sink-category tag. Middleware (the decorator/route-dep gate scan) lands below in _endpoint_middleware.
_FILE_WRITE_MODES = ("w", "a", "x")


# Import names that make a `session.<verb>` call HTTP, not SQLAlchemy (B1 sink guard).
_HTTP_IMPORT_NAMES = frozenset({"httpx", "aiohttp", "requests", "ClientSession", "AsyncClient"})

# class 9 · the PROVIDER allowlist — a ROOT PACKAGE → provider name map (curated, never "tag every
# third-party import" — the gustify-only-heuristics guard). A fn that reaches one of these bound
# names draws a `reaches provider:<name>` wire to the edge of the system.
_PROVIDER_ROOTS = {
    "genai": "gemini", "firebase_admin": "firebase",
    "sentry_sdk": "sentry", "openai": "openai", "anthropic": "anthropic",
    "stripe": "stripe", "boto3": "aws", "redis": "redis",
    "httpx": "http", "requests": "http", "aiohttp": "http",
    # the AI stack (review 2026-09-06, tier2/tier3): an LLM, agent, embedding or vector provider is an
    # edge of the system like any other SDK — one wire per bound name, never a tag on every import
    "langchain": "langchain", "langchain_core": "langchain", "langchain_community": "langchain",
    "langchain_openai": "openai", "langchain_anthropic": "anthropic", "langgraph": "langgraph",
    "litellm": "litellm", "mem0": "mem0", "pgvector": "pgvector", "qdrant_client": "qdrant",
    "pinecone": "pinecone", "cohere": "cohere", "voyageai": "voyage", "ollama": "ollama",
    "vertexai": "vertex", "mistralai": "mistral", "groq": "groq", "together": "together",
    "sentence_transformers": "sentence-transformers", "transformers": "huggingface",
}
# `google` is NOT a provider root (review fix [11]): google.oauth2/google.cloud/google.auth are NOT
# the Gemini LLM — only the genai SDK is. Matched by the specific submodule below, never by root.
_GEMINI_GOOGLE = ("google.genai", "google.generativeai")
_FILE_PROVIDERS: dict[str, dict] = {}


def _file_providers(f: str) -> dict:
    """{local imported name → provider} for one file's SDK imports (class 9). An ``import
    firebase_admin`` / ``from google import genai`` whose root ∈ ``_PROVIDER_ROOTS``, PLUS an
    ``x = importlib.import_module('firebase_admin.auth')`` string binding (the verifier idiom).
    ``{}`` when the file imports no known provider (byte-identical, P5). Cached like _file_imports."""
    if f in _FILE_PROVIDERS:
        return _FILE_PROVIDERS[f]
    if f not in _PY_TEXTS:
        return {}
    out: dict = {}
    try:
        for node in ast.walk(ast.parse(_PY_TEXTS[f])):
            if isinstance(node, ast.ImportFrom):
                _mod = node.module or ""
                if _mod == "google" or _mod.startswith(_GEMINI_GOOGLE):
                    # `from google import genai` / `from google.genai import ...` — the ONLY google→gemini
                    # bind (review fix [11]): oauth2/cloud/auth share the root but are not the LLM.
                    for a in node.names:
                        if _mod.startswith(_GEMINI_GOOGLE) or a.name == "genai":
                            out[a.asname or a.name] = "gemini"
                    continue
                p = _PROVIDER_ROOTS.get(_mod.split(".")[0])
                if p:
                    for a in node.names:
                        out[a.asname or a.name] = p
            elif isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.startswith(_GEMINI_GOOGLE):     # import google.generativeai as genai
                        out[(a.asname or a.name).split(".")[0]] = "gemini"
                        continue
                    p = _PROVIDER_ROOTS.get(a.name.split(".")[0])
                    if p:
                        out[(a.asname or a.name).split(".")[0]] = p
            elif (isinstance(node, ast.Assign) and len(node.targets) == 1
                  and isinstance(node.targets[0], ast.Name) and isinstance(node.value, ast.Call)
                  and isinstance(node.value.func, ast.Attribute) and node.value.func.attr == "import_module"
                  and node.value.args and isinstance(node.value.args[0], ast.Constant)):
                _arg = str(node.value.args[0].value)
                p = "gemini" if _arg.startswith(_GEMINI_GOOGLE) else _PROVIDER_ROOTS.get(_arg.split(".")[0])
                if p:
                    out[node.targets[0].id] = p
    except SyntaxError:
        pass
    _FILE_PROVIDERS[f] = out
    return out


def _detect_externals(fnnode, binds: dict) -> list[str]:
    """The external PROVIDERS a fn reaches (class 9), from ``binds`` (``_file_providers``). RULE A:
    a Call whose attribute-chain ROOT Name ∈ binds (``firebase_admin.auth.verify_id_token(...)`` ·
    ``genai.Client(...)``). RULE B: a bound attr/name passed AS a Call arg
    (``asyncio.to_thread(firebase_auth.delete_user, uid)`` — the bound-attribute-as-argument idiom).
    Sorted providers, ``[]`` honest-empty. A cross-scope binding (``self._client = genai.Client()``)
    is an under-count residual, never a wrong provider."""
    if not binds:
        return []

    def _root(node):
        while isinstance(node, ast.Attribute):
            node = node.value
        return node.id if isinstance(node, ast.Name) else None

    provs: set = set()
    for n in ast.walk(fnnode):
        if not isinstance(n, ast.Call):
            continue
        r = _root(n.func)                               # RULE A: the call's receiver root
        if r in binds:
            provs.add(binds[r])
        for a in n.args:                                # RULE B: a bound attr/name passed as an arg
            ar = _root(a) if isinstance(a, (ast.Attribute, ast.Name)) else None
            if ar in binds:
                provs.add(binds[ar])
    return sorted(provs)


def _detect_sinks(fnnode, http_lib: bool = False) -> list[str]:
    """The non-ORM sink CATEGORIES this function reaches, sorted. [] when none (honest).

    ``http_lib`` (B1): whether the MODULE imports an http client. ``session.<verb>`` is HTTP only
    then — otherwise ``session`` is SQLAlchemy's and the old blanket rule invented http sinks on
    ORM code (the 5 false ``session.delete`` http entries on gustify). A ``requests``/``httpx``/
    ``aiohttp`` receiver stays http by name regardless (aiohttp's ``ClientSession`` keeps its sink)."""
    cats: set[str] = set()
    for n in ast.walk(fnnode):
        if not isinstance(n, ast.Call):
            continue
        func = n.func
        attr = func.attr if isinstance(func, ast.Attribute) else None
        bare = func.id if isinstance(func, ast.Name) else None
        recv = (func.value.id.lower()
                if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) else "")
        if bare == "open" and len(n.args) >= 2 and isinstance(n.args[1], ast.Constant) \
                and isinstance(n.args[1].value, str) \
                and any(m in n.args[1].value for m in _FILE_WRITE_MODES):
            cats.add("file")
        if attr in ("write_text", "write_bytes"):
            cats.add("file")
        if ("redis" in recv or "cache" in recv) and attr in ("set", "setex", "delete", "hset", "expire", "incr"):
            cats.add("cache")
        if attr in ("publish", "emit", "dispatch", "enqueue") \
                and (attr == "enqueue" or "bus" in recv or "event" in recv or "queue" in recv):
            cats.add("queue")
        if ("requests" in recv or "httpx" in recv or "aiohttp" in recv or "client" in recv
                or ("session" in recv and http_lib)) \
                and attr in ("post", "put", "patch", "delete", "get"):   # B1: `session` is http only with an http import
            cats.add("http")
    return sorted(cats)


# ── C4 follow-up · ENDPOINT MIDDLEWARE floor (the level-2 gates: auth / consent / idempotency) ──
# The operator's backend model: (1) receive → (2) MIDDLEWARE / business / legal gates → (3) access
# methods. C1's role BFS walks direct calls in the handler BODY; the framework injects Depends()/
# Security() BEFORE the body runs, so a call-tree walk never sees them. This reads the ROUTE surface:
# the handler's Depends()/Security() (signature + `dependencies=[...]`) + any non-route decorator.
# A FLOOR by design — a dependency nested INSIDE another Depends is not walked (honest under-count);
# `gate` is a name heuristic (a hint, never a claim). Borrowed shape: codesight's per-route dep chain.
_DEPENDS = frozenset({"Depends", "Security"})
# TOKEN set, not substrings — `scope` must NOT fire on `scoped_query`, `require` not on `required_filters`.
# NB: no "session"/"settings" — get_session/get_settings are resource deps, not guards.
_MW_GATE_TOKENS = frozenset({
    "auth", "authenticate", "authenticated", "authorize", "authorization", "authz",
    "require", "permission", "permissions", "consent", "idempotent", "idempotency",
    "verify", "guard", "ensure", "csrf", "ratelimit", "throttle", "scope", "scopes",
    "role", "roles", "login", "tenant", "household", "check", "assert", "enforce",
    "block", "owner", "ownership", "allowed", "forbid", "deny", "protect", "secure", "restrict",
})
# compound auth idioms a token split can't catch as one token
_MW_GATE_SUBSTR = ("current_user", "currentuser", "get_current")
_MW_CAMEL = _re_mod.compile(r"([a-z0-9])([A-Z])")


def _mw_tokens(name: str) -> list[str]:
    """snake + camelCase → lowercased word tokens (RoleChecker → [role, checker])."""
    snake = _MW_CAMEL.sub(r"\1_\2", name)
    return [t for t in _re_mod.split(r"[^a-z0-9]+", snake.lower()) if t]


def _is_mw_gate(name: str | None) -> bool:
    n = (name or "").lower()
    if any(s in n for s in _MW_GATE_SUBSTR):
        return True
    return any(t in _MW_GATE_TOKENS for t in _mw_tokens(name or ""))


def _depends_target(call) -> str | None:
    """`Depends(fn)` / `fastapi.Depends(fn)` / `Security(fn, ...)` / `Depends(Checker("x"))`
    → the dependency EXPRESSION, unparsed. `.attr` on the callee catches the qualified form
    (`fastapi.Depends`); unparsing the ARG (not just its leaf) keeps distinct deps distinct —
    `auth.verify` ≠ `billing.verify`, `RoleChecker('a')` ≠ `RoleChecker('b')`.
    HONEST FLOOR: an ALIASED import (`from fastapi import Depends as Dep`) is not resolved —
    that needs per-file import tracking; such a file under-counts, never mis-names."""
    if not isinstance(call, ast.Call) or not call.args:
        return None
    callee = getattr(call.func, "id", None) or getattr(call.func, "attr", None)
    if callee not in _DEPENDS:
        return None
    return ast.unparse(call.args[0])


def _depends_callee(call) -> str | None:
    """`Depends(require_permission(Permission.X))` → ``require_permission`` — the FACTORY's leaf name, so the
    gate resolves to a function even though its display name keeps the full expression (review
    2026-09-06: 405 of onyx's permission gates drew nothing — the resolver looked the whole expression up
    by bare function name). None when the dep is not a call."""
    if not isinstance(call, ast.Call) or not call.args or not isinstance(call.args[0], ast.Call):
        return None
    f = call.args[0].func
    return getattr(f, "id", None) or getattr(f, "attr", None)


_ALIASES: dict[tuple, dict] = {}


def _dep_aliases(repo: Path, rel: str, tree, depth: int = 0) -> dict[str, list[str]]:
    """{AliasName: [dep exprs]} — module-level ``X = Annotated[T, Depends(f)]`` in this file, plus the
    aliases it imports by name (one hop). tier1 declares ``CurrentUserDep`` in
    infrastructure/dependencies.py and handlers annotate ``user: CurrentUserDep`` — a bare Name the
    signature scan could not see (review 2026-09-06: 2 of 35 endpoints showed any dependency)."""
    ck = (rel, depth)
    if ck in _ALIASES:
        return _ALIASES[ck]
    out: dict[str, list[str]] = {}
    for node in getattr(tree, "body", []):
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            deps = _annotated_depends(node.value)
            if deps:
                tg = node.targets if isinstance(node, ast.Assign) else [node.target]
                for t in tg:
                    if isinstance(t, ast.Name):
                        out[t.id] = deps
        elif isinstance(node, ast.ImportFrom) and depth < 1:
            mf = _resolve_module(repo, rel, node.module, node.level)
            if not mf:
                continue
            sub_tree, _ = _safe_parse(repo / mf)
            if sub_tree is None:
                continue
            theirs = _dep_aliases(repo, mf, sub_tree, depth + 1)
            for a in node.names:
                if a.name in theirs:
                    out[a.asname or a.name] = theirs[a.name]
    _ALIASES[ck] = out
    return out


def _dec_name(dec) -> str | None:
    if isinstance(dec, ast.Call):
        dec = dec.func
    if isinstance(dec, ast.Name):
        return dec.id
    if isinstance(dec, ast.Attribute):
        return dec.attr
    return None


def _annotated_depends(ann) -> list[str]:
    """`x: Annotated[T, Depends(fn), ...]` — the modern FastAPI idiom carries the Depends INSIDE
    the annotation, not the default. Return each dep name it names (or []). Both the bare
    `Annotated[...]` and the qualified `typing.Annotated[...]` (Attribute value) forms match."""
    out: list[str] = []
    if isinstance(ann, ast.Subscript):
        v = ann.value
        if getattr(v, "id", None) == "Annotated" or getattr(v, "attr", None) == "Annotated":
            sl = ann.slice
            elts = sl.elts if isinstance(sl, ast.Tuple) else [sl]
            for el in elts:
                t = _depends_target(el)
                if t:
                    out.append(t)
    return out


def _endpoint_middleware(node, route_dec, aliases: dict | None = None) -> list[dict]:
    """[{'name','via','gate'[,'callee']}] — the gates/deps that run before the handler body, or []
    (honest). via ∈ {route-dep, param-dep, decorator}; gate-first, then name-sorted. ``aliases`` =
    the file's ``Name = Annotated[…, Depends()]`` table (``_dep_aliases``) so a bare-Name annotation
    resolves; ``callee`` = a factory dep's leaf function (``_depends_callee``)."""
    found: dict[str, dict] = {}

    def _add(name, via, callee=None):
        if name and name not in found:
            found[name] = {"name": name, "via": via, "gate": _is_mw_gate(name)}
            if callee and callee != name:
                found[name]["callee"] = callee

    for kw in getattr(route_dec, "keywords", []):                 # 1 · @router.x(..., dependencies=[Depends(..)])
        if kw.arg == "dependencies" and isinstance(kw.value, (ast.List, ast.Tuple)):
            for el in kw.value.elts:
                _add(_depends_target(el), "route-dep", _depends_callee(el))
    args = node.args                                              # 2 · def h(..., x = Depends(fn))
    params = list(getattr(args, "posonlyargs", [])) + list(args.args)
    defs = list(args.defaults)
    for p, d in zip(params[len(params) - len(defs):], defs):
        _add(_depends_target(d), "param-dep", _depends_callee(d))
    for d in args.kw_defaults:
        if d is not None:
            _add(_depends_target(d), "param-dep", _depends_callee(d))
    for p in params + list(args.kwonlyargs):                      # 2b · x: Annotated[T, Depends(fn)] (the modern idiom)
        if p.annotation is not None:
            for nm in _annotated_depends(p.annotation):
                _add(nm, "param-dep")
            if isinstance(p.annotation, ast.Name) and aliases and p.annotation.id in aliases:   # 2c · x: CurrentUserDep (a module-level alias)
                for nm in aliases[p.annotation.id]:
                    _add(nm, "param-dep")
    for dec in node.decorator_list:                               # 3 · non-route decorator (@require_household)
        if dec is route_dec:
            continue
        nm = _dec_name(dec)
        if nm and nm not in ("get", "post", "put", "patch", "delete"):
            _add(nm, "decorator")
    return sorted(found.values(), key=lambda m: (not m["gate"], m["name"]))


def function_insight(repo: Path) -> dict:
    """{'<file>::<qual>': signals} for every def in the mapped backend files,
    computed once per build. Serialized into archmap.json as
    `function_insight`."""
    global _FN_INSIGHT
    if _FN_INSIGHT is not None:
        return _FN_INSIGHT
    file_layer: dict[str, str] = {}
    file_entity: dict[str, str] = {}
    handlers: set = set()
    for slug in ENTITY_CODE:
        v = collect_entity_map(slug, repo)
        if not v:
            continue
        for layer, f, _n in v["files"]:
            if f.endswith(".py"):
                file_layer.setdefault(f, layer)
                file_entity.setdefault(f, slug)
        for e in v["endpoints"]:
            handlers.add((e["fn"], e["file"]))
    texts = {f: (_safe_read(repo / f) or "") for f in sorted(file_layer)
             if (repo / f).exists()}   # encoding-safe: a legacy-encoded file must not abort function_insight
    _PY_TEXTS.update(texts)
    # pre-parse once (each tree reused for the model-map AND the fn walk), then
    # build the GLOBAL model→table map before any fn is inspected — a write can
    # target a model class declared in another file (C2).
    trees: dict[str, ast.AST] = {}
    for f, text in texts.items():
        try:
            trees[f] = ast.parse(text)
        except SyntaxError:
            continue
    # the model→table map ALSO sees the UNCLAIMED table classes (model_census) — so a
    # write to a table the config never claimed is still attributed (C2) and minted (C3);
    # the fn walk below stays on the MAPPED trees only (no fns from unclaimed files).
    _m2t_trees = dict(trees)
    for _u in (model_census(repo).get("unclaimed") or []):
        if _u["file"] not in _m2t_trees:
            _t, _ = _safe_parse(repo / _u["file"])
            if _t is not None:
                _m2t_trees[_u["file"]] = _t
    model2table = _model_table_map(_m2t_trees)
    fns: dict[str, dict] = {}
    for f, tree in trees.items():
        text = texts[f]
        lines = text.splitlines()
        _hl = bool(set(_file_imports(f)) & _HTTP_IMPORT_NAMES)   # B1: does THIS module import an http client?
        _pv = _file_providers(f)                                 # class 9: this module's SDK imports → provider binds

        def _add(node, cls: str | None):
            if node.name.startswith("__") or len(node.name) < 3:
                return
            qual = f"{cls}.{node.name}" if cls else node.name
            span = (node.lineno, node.end_lineno or node.lineno)
            body = "\n".join(lines[span[0] - 1:span[1]])
            fns[f"{f}::{qual}"] = {
                "fn": qual, "name": node.name, "method": bool(cls),
                "file": f, "entity": file_entity.get(f, ""),
                "layer": file_layer.get(f, ""),
                "handler": (node.name, f) in handlers,
                "async": isinstance(node, ast.AsyncFunctionDef),
                "lines": span[1] - span[0] + 1, "span": span,
                "params": [(a.arg,
                            ast.unparse(a.annotation) if a.annotation else "")
                           for a in node.args.args if a.arg != "self"],
                "returns": ast.unparse(node.returns) if node.returns else "",
                "doc": _first_sentence(ast.get_docstring(node)),
                "access": _orm_access(node, model2table),   # C2: ORM read/write ops → model/table
                "ids": {i for i in _re_mod.findall(
                    r"[A-Za-z_][A-Za-z0-9_]{3,}", body)} - _PY_KEYWORDS,
            }
            _snk = _detect_sinks(node, http_lib=_hl)         # C4: non-ORM sink categories (honest-empty)
            if _snk:
                fns[f"{f}::{qual}"]["sinks"] = _snk
            _flg = _flag_gates(node, parse_flags(repo))      # class 12: fn-level feature-flag walls (spend-cap etc.)
            if _flg:
                fns[f"{f}::{qual}"]["flags"] = _flg
            _ext = _detect_externals(node, _pv)              # class 9: external providers this fn reaches
            if _ext:
                fns[f"{f}::{qual}"]["externals"] = _ext

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                _add(node, None)
            elif isinstance(node, ast.ClassDef):
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        _add(sub, node.name)
    plain_names = {c["name"] for c in fns.values()
                   if not c["method"] and len(c["name"]) >= 4}
    _ftok = {f: set(_IDENT_RX.findall(text)) for f, text in texts.items()}   # every file's identifier set, once (scale)
    for c in fns.values():
        rx = (_re_mod.compile(rf"\.{_re_mod.escape(c['name'])}\b")
              if c["method"] else
              _re_mod.compile(rf"\b{_re_mod.escape(c['name'])}\b"))
        refs = []
        for f, text in texts.items():
            if c["name"] not in _ftok[f]:      # exact pre-filter: a regex hit needs the name as a token of the file
                continue
            if f == c["file"]:
                # blank the def's own span — self-reference is not usage
                ls = text.splitlines()
                s, e = c["span"]
                probe = "\n".join(ls[:s - 1] + [""] * (e - s + 1) + ls[e:])
            else:
                probe = text
            if rx.search(probe):
                refs.append(f)
        c["api"] = (sum(1 for h, hf in handlers
                        if h == c["name"] and hf == c["file"])
                    + sum(1 for f in refs
                          if file_layer.get(f) == "api" and f != c["file"]))
        c["internal"] = sum(1 for f in refs if file_layer.get(f) != "api"
                            or f == c["file"])
        c["ref_files"] = refs
        c["base"] = not any(n != c["name"] and n in c["ids"]
                            for n in plain_names)
        c["god"] = c["lines"] >= _FN_GOD_LINES
        c["usage"] = c["api"]
    sizable = [c for c in fns.values() if len(c["ids"]) >= 8]
    for c in fns.values():
        c["sim"] = None
    global _FN_SIM_MODE
    if len(sizable) <= _FN_TWIN_BUDGET:
        _FN_SIM_MODE = {"mode": "exact", "sizable": len(sizable), "budget": _FN_TWIN_BUDGET}
        _cands = None
    else:                                        # blocked: only pairs sharing a RARE identifier are compared
        _df: dict[str, int] = {}
        for c in sizable:
            for t in c["ids"]:
                _df[t] = _df.get(t, 0) + 1
        _post: dict[str, list] = {}
        for i, c in enumerate(sizable):
            for t in c["ids"]:
                if _df[t] <= _FN_RARE_DF:
                    _post.setdefault(t, []).append(i)
        _cands = []
        for i, c in enumerate(sizable):
            s: set[int] = set()
            for t in c["ids"]:
                if _df[t] <= _FN_RARE_DF:
                    s.update(_post[t])
            s.discard(i)
            _cands.append(sorted(s))
        _FN_SIM_MODE = {"mode": "blocked", "sizable": len(sizable), "budget": _FN_TWIN_BUDGET, "rare_df": _FN_RARE_DF,
                        "pairs": sum(len(x) for x in _cands)}
    for i, c in enumerate(sizable):
        best, best_j, shared = "", 0.0, 0
        for o in (sizable if _cands is None else (sizable[k] for k in _cands[i])):
            if o is c:
                continue
            union = c["ids"] | o["ids"]
            j = len(c["ids"] & o["ids"]) / len(union) if union else 0.0
            if j > best_j:
                best, best_j, shared = o["fn"], j, len(c["ids"] & o["ids"])
        if best_j >= _FN_SIM_FLOOR:
            c["sim"] = {"cls": best, "j": round(best_j, 2), "shared": shared,
                        "of": len(c["ids"])}
    _FN_INSIGHT = fns
    return fns


def resolve_middleware_targets(entities: dict, repo: Path) -> int:
    """Resolve each endpoint's GATE middleware dep (``get_auth_context``, ``require_household``, …)
    to its function_insight id ``<file>::<fn>`` and stamp ``mw['fn']`` — the target ``derive_depends``
    draws the K1 gate chain onto. By NAME (a gate dep name is unique on gustify; a method also keys
    on its bare name so ``require_household`` matches ``AuthContext.require_household``); an ambiguous
    or unresolvable name gets NO ``fn`` key (honest floor). Non-gate deps (get_session/get_settings —
    ``_is_mw_gate`` False) are skipped (Decision #6: only gate=True deps draw). MUTATES ``entities``
    in place; returns the count resolved. Runs AFTER function_insight (its keys are the source).

    KNOWN over-claim (review finding [3], DEFERRED - no risk-free fix): ``by_name`` spans MAPPED files
    only, so uniqueness is measured there. A bare gate dep whose REAL target is an UNMAPPED file can
    match a same-named mapped method via the leaf alias below and bind wrongly. The confident fix
    (drop the leaf alias) would regress the intended require_household -> AuthContext.require_household,
    indistinguishable from the wrong case using ``fi`` alone. Dormant on gustify (0 measured). TRIGGER
    to revisit: the first project whose endpoint detail panel shows a gate chain landing on a
    semantically-wrong fn - then gate resolution needs an unmapped-file scan, not a leaf alias."""
    fi = function_insight(repo)
    by_name: dict[str, list[str]] = {}
    for key, v in fi.items():
        _fn = v.get("fn") or key.rsplit("::", 1)[-1]
        by_name.setdefault(_fn, []).append(key)
        if "." in _fn:                                  # a method: also resolvable by its bare name
            by_name.setdefault(_fn.rsplit(".", 1)[-1], []).append(key)
    resolved = 0
    for slug in sorted(entities):
        e = entities.get(slug)
        if not e:
            continue
        for ep in e.get("endpoints") or []:
            for mw in ep.get("middleware") or []:
                if not mw.get("gate") or mw.get("fn"):
                    continue
                cands = by_name.get(mw["name"]) or by_name.get(mw.get("callee") or "")   # a factory dep resolves by its callee (review 2026-09-06)
                if cands and len(cands) == 1:           # unique → resolve; ambiguous → honest floor
                    mw["fn"] = cands[0]
                    resolved += 1
    return resolved


def parse_app_middleware(repo: Path, entity_code: dict | None = None) -> list[dict]:
    """The app-level middleware STACK (class 8): every ``app.add_middleware(Cls, …)`` — the CORS /
    rate-limit / idempotency gates that wrap EVERY request. Scans the api dirs' PARENTS (``main.py``
    sits ABOVE the route dirs the census reaches), matches ``add_middleware(`` calls, and carries a
    ``scope`` floor of ``'all'`` (a computed per-route scope is never guessed — the endpoints already
    name their own gate deps). Returns ``[{cls, file, line, order, scope}]`` sorted by add order,
    ``[]`` honest-empty (no ``add_middleware`` → byte-identical, P5). Deterministic."""
    ec = ENTITY_CODE if entity_code is None else entity_code
    dirs: set = set()
    for slug in sorted(ec):
        for pat in (ec[slug].get("api") or []):
            for f in sorted(_glob.glob(str(repo / pat), recursive=True)):
                p = Path(f)
                if p.is_file():
                    dirs.add(p.parent)
                    dirs.add(p.parent.parent)          # main.py lives one dir up from the routes
    out: list[dict] = []
    for d in sorted(dirs, key=str):
        if not d.is_dir():
            continue
        for py in sorted(d.glob("*.py")):
            if repo not in py.parents:                  # grandparent-of-a-root-file can sit ABOVE repo
                continue                                 # (review fix [4]: relative_to would abort the whole build)
            tree, _ = _safe_parse(py)
            if tree is None:
                continue
            rel = str(py.relative_to(repo))
            for node in ast.walk(tree):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and node.func.attr == "add_middleware" and node.args):
                    _a0 = node.args[0]
                    cls = (_a0.id if isinstance(_a0, ast.Name)
                           else _a0.attr if isinstance(_a0, ast.Attribute) else None)
                    if cls:
                        out.append({"cls": cls, "file": rel, "line": node.lineno, "scope": "all"})
    out.sort(key=lambda m: (m["file"], m["line"]))
    for _i, _m in enumerate(out):
        _m["order"] = _i
    return out


_DISPATCH_REG = frozenset({"register", "register_once", "subscribe", "add_handler", "on"})


def dispatch_map(repo: Path) -> dict:
    """Event-bus DISPATCH edges (class 6): a publisher fn → each handler registered for the event it
    publishes. A type-keyed registry (``register_once(EventCls, handler)``) is NO call graft can see,
    and handlers are imported FUNCTION-LOCALLY under aliases (``from services.skills import
    on_cooked_meal_created as _han``) — so the edge from ``bus.publish(EventCls(...))`` to the handler
    is invisible. This resolves the handler alias (fn-local + module-level ImportFrom → module → file
    by path-suffix) and joins publisher→handler. Returns ``{dispatches: [{s, t, event, conf}], stats}``
    or ``{}`` honest-empty (no register + no publish → byte-identical, P5). conf 'extracted' (a census)."""
    global _DISPATCH
    if _DISPATCH is not None:
        return _DISPATCH
    trees: dict[str, ast.AST] = {}
    for slug in ENTITY_CODE:
        v = collect_entity_map(slug, repo)
        if not v:
            continue
        for _layer, f, _n in v.get("files", []):
            if f.endswith(".py") and f not in trees:
                t, _ = _safe_parse(repo / f)
                if t is not None:
                    trees[f] = t
    name2file: dict[str, list[str]] = {}
    module_imp: dict[str, dict[str, tuple]] = {}         # file → {alias: (module, orig)}
    for f, t in trees.items():
        module_imp[f] = {}
        for node in t.body:
            if isinstance(node, ast.ImportFrom):
                for a in node.names:
                    module_imp[f][a.asname or a.name] = (node.module, a.name)
        for node in ast.walk(t):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name2file.setdefault(node.name, []).append(f)

    def _mod2file(module):
        if not module:
            return None
        parts = module.split(".")
        for f in trees:
            fp = f[:-3].split("/")
            if len(fp) >= len(parts) and fp[-len(parts):] == parts:
                return f
        return None

    def _resolve(name, f, local):
        src = local.get(name) or module_imp.get(f, {}).get(name)
        if src:
            hf = _mod2file(src[0])
            if hf:
                return f"{hf}#{src[1]}"
        cands = name2file.get(name)
        return f"{cands[0]}#{name}" if cands and len(cands) == 1 else None

    def _own_nodes(fn):
        # descendants of fn's OWN body, NOT descending into a nested def/lambda (review fix [6]:
        # ast.walk(fn) crosses into closures, so a nested-fn publish got credited to every encloser).
        stack = list(ast.iter_child_nodes(fn))
        while stack:
            n = stack.pop()
            yield n
            if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                stack.extend(ast.iter_child_nodes(n))

    registry: dict[str, list[str]] = {}                 # EventClsName → [handler_id]
    for f, t in trees.items():
        for fnnode in ast.walk(t):
            if not isinstance(fnnode, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            local = {}
            for n in _own_nodes(fnnode):
                if isinstance(n, ast.ImportFrom):
                    for a in n.names:
                        local[a.asname or a.name] = (n.module, a.name)
            for n in _own_nodes(fnnode):
                if (isinstance(n, ast.Call) and _call_attr(n.func) in _DISPATCH_REG and len(n.args) >= 2):
                    ev = _call_bare(n.args[0]) or (n.args[0].attr if isinstance(n.args[0], ast.Attribute) else None)
                    hn = _call_bare(n.args[1])
                    if not ev or not hn:
                        continue
                    hid = _resolve(hn, f, local)
                    if hid:
                        registry.setdefault(ev, []).append(hid)
    dispatches: list[tuple] = []
    for f, t in trees.items():
        for fnnode in ast.walk(t):
            if not isinstance(fnnode, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            pid = f"{f}#{fnnode.name}"
            for n in _own_nodes(fnnode):                # innermost fn only (review fix [6])
                if isinstance(n, ast.Call) and _call_attr(n.func) == "publish":
                    for a in n.args:                    # publish(event) OR publish(session, event) — scan every arg
                        if not isinstance(a, ast.Call):  # only a CONSTRUCTED event counts (review fix [7]: a
                            continue                     # bare Name arg fabricates edges on a class-name collision)
                        ev = _call_bare(a.func) or (a.func.attr if isinstance(a.func, ast.Attribute) else None)  # [8]
                        for hid in registry.get(ev, []):
                            if hid != pid:
                                dispatches.append((pid, hid, ev))
    edges = [{"s": s, "t": t, "event": e, "conf": "extracted"}
             for (s, t, e) in sorted(set(dispatches))]
    out = ({"dispatches": edges,
            "stats": {"events": len(registry),
                      "handlers": len({h for hs in registry.values() for h in hs}),
                      "edges": len(edges)}}
           if edges else {})
    _DISPATCH = out
    return out




# ── TASK DISPATCH BY NAME (review 2026-09-06, repo-study — class 13). A queue hands work to a worker by a
#    NAME, never a call: Celery `app.send_task("x")` / `fn.delay()` / `fn.apply_async()` reaches
#    `@shared_task(name="x")`; ARQ `enqueue_job("fn")` reaches a function listed in `WorkerSettings.functions`;
#    Taskiq `fn.kiq()` reaches `@broker.task`. graft sees none of it (onyx: 46 @shared_task · 33 send_task,
#    every indexing mission dark past the enqueue). Two AST passes over the entity-mapped files — the
#    TASK REGISTRY (name → `<file>#<fn>`, names resolved through string constants / class attributes such as
#    `OnyxCeleryTask.CHECK_FOR_INDEXING`) and the DISPATCH SITES (enclosing fn → task) — joined into the same
#    `dispatches` shape the event-bus map emits (rel 'dispatches', conf 'extracted'), so the station draws
#    them with the wire it already has. Task functions are also TRACE ROOTS (`parse_task_roots`) — a
#    worker's chain was unreachable even with the edge, because only handlers rooted the levels walk.
_TASK_DECOS = frozenset({"shared_task", "task"})              # @shared_task(…) · @celery_app.task(…) · @broker.task(…)
_TASK_SEND = frozenset({"send_task", "enqueue_job", "enqueue"})  # <app>.send_task(NAME) · <pool>.enqueue_job("fn")
_TASK_CALL = frozenset({"delay", "apply_async", "kiq"})          # <fn>.delay(…) · <fn>.apply_async(…) · <fn>.kiq(…)
_TASKS: dict | None = None
_TASK_ROOTS: list | None = None


def _mapped_trees(repo: Path) -> dict[str, ast.AST]:
    trees: dict[str, ast.AST] = {}
    for slug in ENTITY_CODE:
        v = collect_entity_map(slug, repo)
        if not v:
            continue
        for _layer, f, _n in v.get("files", []):
            if f.endswith(".py") and f not in trees:
                t, _ = _safe_parse(repo / f)
                if t is not None:
                    trees[f] = t
    return trees


def _str_constants(trees: dict) -> dict[str, str]:
    """{`NAME` | `Class.NAME`: literal} — module-level and class-body string assignments (the task-name
    registries: `class OnyxCeleryTask: CHECK_FOR_INDEXING = "check_for_indexing"`). An f-string stays
    unresolved (named, never guessed)."""
    out: dict[str, str] = {}
    for t in trees.values():
        for node in t.body:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                for tg in node.targets:
                    if isinstance(tg, ast.Name):
                        out.setdefault(tg.id, node.value.value)
            elif isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.Assign) and isinstance(item.value, ast.Constant) and isinstance(item.value.value, str):
                        for tg in item.targets:
                            if isinstance(tg, ast.Name):
                                out.setdefault(f"{node.name}.{tg.id}", item.value.value)
    return out


def _name_arg(expr, consts: dict) -> str | None:
    """A task name from a literal, a bare constant, or a `Class.ATTR` — else None."""
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        return expr.value
    if isinstance(expr, ast.Name):
        return consts.get(expr.id)
    if isinstance(expr, ast.Attribute) and isinstance(expr.value, ast.Name):
        return consts.get(f"{expr.value.id}.{expr.attr}")
    return None


def _task_registry(trees: dict, consts: dict) -> tuple[dict[str, str], list[dict]]:
    """({task name: `<file>#<fn>`}, [task records]) — every decorated task fn + every fn an ARQ
    `WorkerSettings.functions` list names. A task answers to its declared `name=`, its bare fn name and
    its dotted `module.fn` (Celery's default name)."""
    reg: dict[str, str] = {}
    recs: list[dict] = []
    for f, t in trees.items():
        mod = f[:-3].replace("/", ".")
        arq: set[str] = set()
        for node in ast.walk(t):
            if isinstance(node, ast.ClassDef) and node.name == "WorkerSettings":
                for item in node.body:
                    if isinstance(item, ast.Assign) and isinstance(item.value, (ast.List, ast.Tuple)):
                        arq.update(e.id for e in item.value.elts if isinstance(e, ast.Name))
        for node in ast.walk(t):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            declared = None
            is_task = node.name in arq
            for dec in node.decorator_list:
                leaf = _dec_name(dec)
                if leaf in _TASK_DECOS:
                    is_task = True
                    if isinstance(dec, ast.Call):
                        for kw in dec.keywords:
                            if kw.arg == "name":
                                declared = _name_arg(kw.value, consts) or declared
            if not is_task:
                continue
            tid = f"{f}#{node.name}"
            names = [n for n in (declared, node.name, f"{mod}.{node.name}") if n]
            for n in names:
                reg.setdefault(n, tid)
            recs.append({"name": declared or node.name, "fn": node.name, "file": f,
                         "doc": _first_sentence(ast.get_docstring(node)), "line": node.lineno})
    return reg, sorted(recs, key=lambda r: (r["file"], r["fn"]))


def task_map(repo: Path) -> dict:
    """{dispatches: [{s, t, event, conf}], stats} — enqueue site → task fn, joined by NAME. `{}`
    honest-empty (no task, no dispatch → byte-identical). Deterministic (sorted)."""
    global _TASKS
    if _TASKS is not None:
        return _TASKS
    trees = _mapped_trees(repo)
    consts = _str_constants(trees)
    reg, recs = _task_registry(trees, consts)
    name2file: dict[str, list[str]] = {}
    for f, t in trees.items():
        for node in ast.walk(t):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name2file.setdefault(node.name, []).append(f)
    dispatches: set[tuple] = set()
    unresolved: list[str] = []
    sites = 0
    for f, t in trees.items():
        for fnnode in ast.walk(t):
            if not isinstance(fnnode, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            pid = f"{f}#{fnnode.name}"
            stack = list(ast.iter_child_nodes(fnnode))
            while stack:                                   # this fn's OWN body — never a nested def's
                n = stack.pop()
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                    continue
                stack.extend(ast.iter_child_nodes(n))
                if not isinstance(n, ast.Call):
                    continue
                attr = _call_attr(n.func)
                tid = None
                label = None
                if attr in _TASK_SEND and n.args:           # send_task(NAME) · enqueue_job("fn")
                    sites += 1
                    label = _name_arg(n.args[0], consts)
                    if label:
                        tid = reg.get(label)
                        if tid is None and attr != "send_task":
                            cands = name2file.get(label) or []
                            tid = f"{cands[0]}#{label}" if len(cands) == 1 else None
                    if tid is None:
                        unresolved.append(label or ast.unparse(n.args[0])[:60])
                elif attr in _TASK_CALL and isinstance(n.func, ast.Attribute):   # fn.delay(…) · fn.apply_async(…)
                    recv = n.func.value
                    fname = getattr(recv, "id", None) or getattr(recv, "attr", None)
                    if not fname:
                        continue
                    sites += 1
                    label = fname
                    tid = reg.get(fname)
                    if tid is None:
                        cands = name2file.get(fname) or []
                        tid = f"{cands[0]}#{fname}" if len(cands) == 1 else None
                    if tid is None:
                        unresolved.append(fname)
                if tid and tid != pid:
                    dispatches.add((pid, tid, label or tid.rsplit("#", 1)[-1]))
    edges = [{"s": s, "t": t, "event": e, "conf": "extracted"} for (s, t, e) in sorted(dispatches)]
    out = ({"dispatches": edges, "tasks": recs,
            "stats": {"tasks": len(recs), "sites": sites, "edges": len(edges),
                      "unresolved": sorted(set(unresolved))[:20]}}
           if (edges or recs) else {})
    _TASKS = out
    return out


def parse_task_roots(repo: Path) -> list[dict]:
    """TASK roots (class 13): every task fn as an endpoint-shaped record `{method:'TASK', path:<name>, fn,
    file, touches, touches_x, doc, resp, status}` — the C4 mints an `endpoint:TASK <name>` node homed to
    the task file's entity (else __unclaimed__) and the levels walk ROOTS on it, so a worker's chain
    (fetch → chunk → embed → index) draws downstream of the queue. `[]` honest-empty."""
    global _TASK_ROOTS
    if _TASK_ROOTS is not None:
        return _TASK_ROOTS
    tm = task_map(repo)
    out: list[dict] = []
    for r in tm.get("tasks") or []:
        out.append({"method": "TASK", "path": r["name"], "fn": r["fn"], "file": r["file"],
                    "touches": [], "touches_x": [], "doc": r.get("doc") or "",
                    "resp": "—", "status": "—"})
    _TASK_ROOTS = out
    return out


def fn_insight_serial(repo: Path) -> dict:
    return {k: {kk: vv for kk, vv in v.items()
                if kk not in ("ids", "span", "params", "ref_files")}
            for k, v in function_insight(repo).items()}


def insight_serial(repo: Path) -> dict:
    """The archmap-ready view: signals only, never the field lists (those
    already ride models/schemas)."""
    return {k: {kk: vv for kk, vv in v.items()
                if kk not in ("fields", "fks_out", "internal_files")}
            for k, v in model_insight(repo).items()}


def _ins_tags(cls: str, ins: dict) -> str:
    """The icon chips for one class cell — dialect + colors per the ruling:
    kind (violet model / teal schema) · base green · fields-count red ·
    twin+% amber. No deadness chip — usage rides the two bars as evidence."""
    c = ins.get(cls)
    if not c:
        return ""
    out = itag("l-models" if c["kind"] == "model" else "l-schemas", c["kind"],
               "model — a persisted DB entity" if c["kind"] == "model"
               else "schema — an API / pipeline shape")
    if c["base"]:
        out += " " + itag("t-base", "base",
                          "base class — derives from nothing: no FK out, no "
                          "field typed by another documented class")
    if c["god"]:
        out += " " + itag("t-god", "fields",
                          f"god-class flag — {len(c['fields'])} fields",
                          str(len(c["fields"])))
    if c["sim"]:
        s = c["sim"]
        out += " " + itag("t-sim", "sim",
                          f"closest structural twin — {s['shared']}/{s['of']} "
                          f"fields shared",
                          f'{E(s["cls"])} {int(s["j"] * 100)}%')
    return out


def _ins_usage(cls: str, ins: dict) -> str:
    c = ins.get(cls)
    if not c:
        return "—"
    w_api = max(2, min(60, c["usage"] * 11))
    w_int = max(2, min(60, c["internal"] * 11))
    return (f'<span class="ubar" style="width:{w_api}px"></span>'
            f'<b>{c["usage"]}</b> <small>api</small><br>'
            f'<span class="ubar u-int" style="width:{w_int}px"></span>'
            f'<b>{c["internal"]}</b> <small>internal</small>')


def merge_amaps(repo: Path) -> dict:
    """The APP-WIDE map: every entity's cached map merged (endpoints deduped
    by method+path+handler, classes by name, files by layer+path). Feeding it
    to build_code_tab under the pseudo-slug 'app' renders the architecture
    station with the SAME six sections as every entity's Code tab — one
    dialect, two altitudes (operator ruling 2026-07-23)."""
    eps, models, schemas, files, defines = [], {}, {}, {}, {}
    file_entity: dict = {}
    seen_ep = set()
    for s in ENTITY_CODE:
        v = collect_entity_map(s, repo)
        if not v:
            continue
        for e in v["endpoints"]:
            k = (e["method"], e["path"], e["fn"], e["file"])
            if k not in seen_ep:
                seen_ep.add(k)
                eps.append(e)
        for m in v["models"]:
            models.setdefault(m["cls"], m)
        for sc in v["schemas"]:
            schemas.setdefault(sc["cls"], sc)
        for layer, f, n in v["files"]:
            files.setdefault((layer, f), n)
            file_entity.setdefault(f, s)
        defines.update(v["defines"])
    return {"endpoints": eps, "models": list(models.values()),
            "_file_entity": file_entity,
            "schemas": list(schemas.values()),
            "files": [[layer, f, n] for (layer, f), n in files.items()],
            "defines": defines}


_IC_LINK_SM = ('<svg viewBox="0 0 24 24" width="12" height="12" '
               'fill="none" stroke="currentColor" stroke-width="2" '
               'stroke-linecap="round" stroke-linejoin="round">'
               '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 '
               '0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/>'
               '<line x1="10" y1="14" x2="21" y2="3"/></svg>')


_GUARD_LENS: dict | None = None


def guard_lens(repo: Path) -> dict:
    """The guard lens for this repo, computed once per build.

    Lives here rather than being threaded through every caller because the
    code map renders from a per-ENTITY amap while the lens is app-wide: an
    entity slice must still be able to say "this file has 12 unguarded defs",
    and that number cannot come from the slice it is rendering."""
    global _GUARD_LENS
    if _GUARD_LENS is None:
        ti = _a3_tests.test_insight(repo)
        _GUARD_LENS = _a3_guard.guard_insight(
            function_insight=fn_insight_serial(repo),
            by_function=ti.get("by_function", {}),
            by_endpoint=ti.get("by_endpoint", {}),
            exercises=ti.get("exercises", {}),
            entities={s_: collect_entity_map(s_, repo) for s_ in ENTITY_CODE},
            by_model=ti.get("by_model", {}),
            model_insight=insight_serial(repo),
            proofs=_cd.load_guard_proofs())
    return _GUARD_LENS


def build_code_tab(slug: str, repo: Path, intro_html: str,
                   amap: dict | None = None, entity_col: bool = False,
                   xpage: dict | None = None) -> str:
    """The Code tab: endpoints · code map · data model (+ candidates) ·
    functions (+ candidates). Returns "" for entities with no ENTITY_CODE
    mapping yet — rendered as a named gap by the caller. With an explicit
    `amap` (merge_amaps) it renders the APP-WIDE view for the architecture
    station under the caller's pseudo-slug."""
    amap = amap or collect_entity_map(slug, repo)
    if not amap:
        return ""
    eps, models, schemas = amap["endpoints"], amap["models"], amap["schemas"]
    files = [tuple(row) for row in amap["files"]]

    _page_files = {f for _layer, f, _n in files}
    # xpage maps an anchor kind to the PAGE that carries it, so section-crossing
    # links stay alive when the sections live on separate pages; entity_col
    # prepends the icon-only entity identity column (operator 2026-07-23).
    xpage = xpage or {}

    def _href(kind: str, anchor: str) -> str:
        return f"{xpage.get(kind, '')}#{anchor}"

    _file_ent = dict(amap.get("_file_entity", {})) if entity_col else {}

    def _ent_cell(ent: str) -> str:
        return entity_badge(ent, _adopt_name(ent), 13)

    # --- the test↔code thread (spike ruling 2026-07-23): every element row
    # answers "is this tested, and by what KIND?" — kind chips + tier-labeled
    # receipts, gaps named, nothing gated (D1).
    _ti = _a3_tests.test_insight(repo)
    _GUARD = guard_lens(repo)
    _corpora_cfg = _cd.CFG.get("corpora", [])
    _ckind = {c2["key"]: c2.get("kind", c2["key"]) for c2 in _corpora_cfg}
    _kcls = {c2.get("kind", c2["key"]): c2.get("tag_class", "")
             for c2 in _corpora_cfg}
    _has_journey = "journey" in _ckind.values()

    def _tchip(kind: str, n, title: str) -> str:
        return (f'<span class="tag tk {_kcls.get(kind, "")}" '
                f'title="{E(kind)}: {E(title)}">{kind_ic(kind)} {n}'
                f"</span>")

    def _tgap(label: str, title: str) -> str:
        return (f'<span class="tag tk t-tgap" title="{E(title)}">'
                f"{E(label)}</span>")

    _STATE_CHIP = {"pass": "s-ok", "fail": "s-high", "skip": "s-gap"}

    def _dmh(color: str, icon: str, label: str, extra: str = "") -> str:
        """A titled subsection head inside the row detail — icon + colored
        label, so each block (usage · structure) is identifiable at a
        glance (operator polish 2026-07-23)."""
        return (f'<p class="dmh" style="--dc:{color}">{_ins_ic(icon)}'
                f"<b>{E(label)}</b>{extra}</p>")

    def _ref_count(refs: list) -> str:
        """Receipts arithmetic for a tier label: case counts always visible,
        file-level rows counted in BOTH units (operator, round 13)."""
        if refs and refs[0]["state"] == "file":
            n = sum(r.get("n") or 0 for r in refs)
            return (f"{len(refs)} file(s)"
                    + (f" · {n} case(s)" if n else ""))
        return f"{len(refs)} case(s)"

    def _tb_summary(tb: dict) -> str:
        """Tested-by as the ENDPOINT-style aggregation table — Kind · Tier ·
        Volume · State rows, never a per-case listing (operator, round 16).
        The fold title's count-link opens the actual cases in the filtered
        ledger."""
        rows2 = ""
        for tier, refs in (("direct", tb.get("direct") or []),
                           ("via route", tb.get("via_route") or [])):
            by_c: dict[str, list] = {}
            for r in refs:
                by_c.setdefault(r["corpus"], []).append(r)
            for c2, rs in sorted(by_c.items()):
                kind = _ckind.get(c2, c2)
                for is_file, rs2 in (
                        (False, [r for r in rs if r["state"] != "file"]),
                        (True, [r for r in rs if r["state"] == "file"])):
                    if not rs2:
                        continue
                    if is_file:
                        n2 = sum(r.get("n") or 0 for r in rs2)
                        vol = f"{len(rs2)} file(s) · {n2} case(s)"
                        st = "file-level receipts"
                    else:
                        vol = f"{len(rs2)} case(s)"
                        npass = sum(1 for r in rs2 if r["state"] == "pass")
                        nbad = len(rs2) - npass
                        st = (f"{npass} pass"
                              + (f" · {nbad} not passing" if nbad else ""))
                    rows2 += (f'<tr><td><span class="tag '
                              f'{_kcls.get(kind, "")}" title="{E(kind)}">'
                              f"{kind_ic(kind, 14)}</span></td>"
                              f"<td>{tier}</td><td>{vol}</td>"
                              f"<td>{st}</td></tr>")
        if not rows2:
            return ""
        return ('<table class="tbl"><thead><tr><th>Kind</th><th>Tier</th>'
                "<th>Volume</th><th>State</th></tr></thead>"
                f"<tbody>{rows2}</tbody></table>")

    def _rcnt(refs: list) -> int:
        """Receipt CASE count — file-level refs contribute their case
        counts, so every number is in one unit and the chips ADD UP."""
        return sum((x.get("n") or 1) if x["state"] == "file" else 1
                   for x in refs)

    def _ep_tcell(e: dict) -> str:
        key = f'{e["file"]}::{e["fn"]}'
        refs = _ti["by_endpoint"].get(key) or {}
        # The guard verdict unions BOTH bindings, exactly as the lens does. A
        # route can be reached by a case that names its HANDLER rather than the
        # path; reading by_endpoint alone would call that endpoint untested.
        # The two agree on today's twins — which is why it has to be written
        # down rather than relied on.
        via_handler = _ti.get("by_function", {}).get(key) or []
        chips = []
        for c2, r in sorted(refs.items()):
            n = _rcnt(r)
            chips.append(_tchip(_ckind.get(c2, c2), n,
                                f"{n} {c2} receipt case(s) — api: cases "
                                "driving this route; web: cases in files "
                                "encoding it (T1)"))
        if not chips and via_handler:
            return (f'<span class="tag tk t-via" title="no case matches this '
                    f'route\'s path, but {len(via_handler)} case(s) name its '
                    f'handler by name — the contract is unwatched, the code is '
                    f'not">via handler {len(via_handler)}</span>')
        if not chips:
            # 21% of endpoints on one twin, 7% on the other — rare enough that
            # the chip is news. That is the whole reason it lives HERE and not
            # on the function page, where 60-82% carry it and it reads as
            # wallpaper.
            return _tgap("unguarded",
                         "no case or spec matches this route's path AND no "
                         "case names its handler — change the contract and "
                         "no NAMED case goes red")
        if _has_journey and not any(
                _ckind.get(c2) == "journey" for c2 in refs):
            chips.append(_tgap("journey —",
                               "no browser spec drives this route"))
        return " ".join(chips)

    def _duo_tcell(rec: dict | None, what: str) -> str:
        rec = rec or {}
        d, v = rec.get("direct") or [], rec.get("via_route") or []
        nd, nv = _rcnt(d), _rcnt(v)
        chips = []
        if d:
            chips.append(_tchip(_ckind.get(d[0]["corpus"], "unit"), nd,
                                f"cases that import and use this {what} "
                                "by name (T1)"))
        if v:
            chips.append(f'<span class="tag tk t-via" title="composed '
                         f"through the endpoint join — cases driving a "
                         f'route that serves this {what} (T2)">'
                         f"via route {nv}</span>")
        if chips:
            return " ".join(chips)
        # `t-unguarded` is the FILTER hook only — it rides the chip that was
        # already here. At 60-82% unguarded a second visible chip on every row
        # would be the default state rendered 300 times; the informative move
        # is to let the reader filter TO them, not to label each one.
        return (f'<span class="tag tk t-tgap t-unguarded" title="no case '
                f'reaches this {E(what)} by name or via a route — change it '
                f'and no NAMED case goes red">no case</span>')

    def _cm_tcell(f: str) -> str:
        rec = _ti["by_file"].get(f) or {}
        reach, cov = rec.get("reach") or [], rec.get("coverage")
        bits = [(f'<span class="tag tk" title="test file(s) whose imports '
                 f'reach this file (T3)">reach · {len(reach)}</span>')
                if reach else
                _tgap("no reach", "no test file's imports reach this file")]
        bits.append(
            f'<span class="tag tk l-models" title="line coverage, captured '
            f'{E(str(cov["age"])[:16])}">cov {cov["pct"]}%</span>' if cov
            else _tgap("cov —", "line coverage not captured — wire the "
                       "coverage block and run capture --with-coverage"))
        # THE GUARD CHIP. reach and coverage both answer "was this file's code
        # RUN"; neither answers "does any test NAME what it declares". A file
        # can sit at 90% coverage because something upstream imports it and
        # still have nothing that fails when its exports change. That is the
        # gap a refactor falls into, so it gets its own chip.
        g = (_GUARD.get("files") or {}).get(f)
        if g and g["declared"]:
            n_un, n_all = g["unguarded"], g["declared"]
            if not n_un:
                # NAMED is not GUARDED. Everything here is named by some case;
                # whether any of those cases can FAIL is a separate fact, and
                # it only exists once prove-guard has mutated the code and
                # watched the case go red. Saying "guarded" before that
                # overstates safety by exactly the void rate (1 in 6 on a real
                # corpus), so `guarded` is reserved for proven.
                n_pv = g.get("proven") or 0
                if n_pv:
                    bits.append(
                        f'<span class="tag tk s-ok" title="all {n_all} declared '
                        f'defs are named by a case, and {n_pv} mutation '
                        f'proof(s) on this file were observed to turn a case '
                        f'red">guarded {n_all}/{n_all}</span>')
                else:
                    bits.append(
                        f'<span class="tag tk t-via" title="all {n_all} declared '
                        f'defs are NAMED by a case — but no case here has been '
                        f'shown able to fail. Run '
                        f'skills/gabe-red/scripts/prove-guard.py to turn this '
                        f'into `guarded`.">named {n_all}/{n_all}</span>')
            else:
                floor = ("" if g["exact"] else
                         " Name-matched against the symbols web tests import, "
                         "so this is a floor, not a coverage figure.")
                sev = "s-high" if g["share"] >= 0.8 else "s-med"
                bits.append(
                    f'<span class="tag tk {sev}" title="{n_un} of {n_all} '
                    f'declared defs are named by NO test — change them and '
                    f'no NAMED case goes red.{E(floor)}">unguarded '
                    f'{n_un}/{n_all}</span>')
        return " ".join(bits)
    _rid_seen: set = set()

    def _rid(base: str) -> str:
        """Per-page-unique row id: the FIRST occurrence keeps the bare anchor
        (every link targets it — consistent with first-wins ownership); a
        sanitizer collision (get_statement vs _get_statement, a model+schema
        name pair on the app page) gets a numeric suffix instead of silently
        hijacking deep links (review H1, proven on gastify data)."""
        rid, n = base, 1
        while rid in _rid_seen:
            n += 1
            rid = f"{base}-{n}"
        _rid_seen.add(rid)
        return rid

    model_names = {m["cls"] for m in models}
    schema_names = {s["cls"] for s in schemas}
    documented = model_names | schema_names
    # Both insights are needed EARLY: endpoints/code-map/data-model details
    # all link into them (cached — later sections reuse).
    fins = function_insight(repo)
    ins = model_insight(repo)
    _fn_by_filename: dict = {}
    for _c in fins.values():
        _fn_by_filename.setdefault((_c["file"], _c["name"]), _c)

    def _entity_chip(owner: str, pending: bool) -> str:
        """The cross-entity label: the owner's stable icon + display name;
        pending owners say so (their page is not built yet)."""
        name = _adopt_name(owner)
        title = f"entity: {name}" + (" — pending, page not built yet"
                                     if pending else "")
        return (f' <span class="tag ic t-ent" title="{E(title)}">'
                f"{entity_icon(owner, 11, label=name)} {E(name)}</span>")

    def _xref(kind: str, ident: str, owner: str) -> tuple[str, str]:
        """(href, entity-chip) for a function ('fn') or class ('dm')
        reference. Same page → plain anchor. Another CARDED entity → its
        feature page's anchor + the entity chip. A PENDING entity (no page
        yet) → the entity index, the placeholder home for everything whose
        page is not built, + the chip marked pending."""
        if not owner or owner == slug:
            return f'#{_anchor(kind, slug, ident)}', ""
        if (_cd.CENTER_DIR / "cards" / f"{owner}.md").exists():
            return (f'feature-{owner}.html#{_anchor(kind, owner, ident)}',
                    _entity_chip(owner, False))
        return "entity-index.html", _entity_chip(owner, True)

    def _io_label(fentry: dict, cls: str) -> str:
        """in / out / in·out — where the class sits in the function's
        signature (param annotation vs return annotation); empty when it is
        only used in the body."""
        pin = any(cls in (t or "") for _p, t in fentry.get("params", []))
        pout = cls in (fentry.get("returns") or "")
        if pin and pout:
            return ' <span class="tag t-io" title="parameter AND return type">in·out</span>'
        if pin:
            return ' <span class="tag t-in" title="parameter type">in</span>'
        if pout:
            return ' <span class="tag t-out" title="return type">out</span>'
        return ""

    def _fn_link(fentry: dict, io_cls: str = "") -> str:
        """A linked function chip (+ optional in/out label vs io_cls)."""
        href, chip = _xref("fn", fentry["file"] + "-" + fentry["fn"],
                           fentry.get("entity", ""))
        io = _io_label(fentry, io_cls) if io_cls else ""
        return (f'<a class="dlink" href="{href}"><code>{E(fentry["fn"])}'
                f"</code></a>{io}{chip}")

    def _fchip(f: str) -> str:
        """A file mention LINKS to its code-map row when the file is on this
        page; a file mapped by another entity stays plain."""
        name = E(f.rsplit("/", 1)[-1])
        if f in _page_files:
            return f'<a class="dlink" href="{_href("cm", _anchor("cm", slug, f))}"><code>{name}</code></a>'
        return f"<code>{name}</code>"


    # The link graph: file colors, endpoint↔file, endpoint↔type — every id is
    # derived so the three tables cross-reference without hand-kept indexes.
    file_color = {f: _FILE_PALETTE[i % len(_FILE_PALETTE)]
                  for i, f in enumerate(dict.fromkeys(e["file"] for e in eps))}
    model_names = {m["cls"] for m in models}
    schema_names = {s["cls"] for s in schemas}
    eps_by_file: dict[str, list[dict]] = {}
    for e in eps:
        eps_by_file.setdefault(e["file"], []).append(e)

    # The longest path segment every endpoint shares — the router's own prefix,
    # derived rather than the literal "/transactions" this used to carry.
    _paths = [e["path"] for e in eps]
    _common = ""
    if _paths:
        head = _paths[0].split("/")
        for i in range(1, len(head) + 1):
            cand = "/".join(head[:i])
            if cand and all(p == cand or p.startswith(cand + "/") for p in _paths):
                _common = cand

    def ep_chip(e: dict) -> str:
        """Font-colored, background-free endpoint link back to its row."""
        short = (e["path"].removeprefix(_common) if _common else e["path"]) or "/"
        return (f'<a class="{_VERB_FONT.get(e["method"], "")}" '
                f'href="{_href("ep", _anchor("ep", slug, e["file"] + "-" + e["fn"]))}">{E(e["method"])} '
                f"{E(short)}</a>")

    def purpose_cell(doc: str) -> str:
        if doc == "—" or len(doc) <= 76:
            return E(doc)
        cut = doc[:76].rsplit(" ", 1)[0].rstrip(" ,;·")
        return (f'<details class="pmore"><summary><span class="cut">{E(cut)}…</span>'
                f'<span class="full">{E(doc)}</span><i></i></summary></details>')

    def returns_cell(e: dict) -> str:
        import re as _re
        parts = []
        for tok in dict.fromkeys(_re.findall(r"[A-Za-z_]\w+", e["resp"])):
            if tok in schema_names:
                parts.append(f'<a class="dlink" href="{_href("dm", _anchor("dm", slug, tok))}">'
                             f"{E(tok)}</a>")
        body = " ".join(parts) or f'<code>{E(e["resp"])}</code>'
        return f'{body}<br><small>{E(e["status"])}</small>'

    # --- Guard: this entity's action items ---------------------------------
    # First on the tab on purpose. The rest of the Code tab is REFERENCE (what
    # exists); this is the only part that asks for a decision, and burying a
    # call-to-action under four reference tables is how it stops being one.
    # Same lens, same cut as the board's guard track, so the two agree by
    # construction rather than by anyone remembering to keep them in step.
    # ENTITY tabs only. The app-wide roll-up already exists as the board's
    # Guard track, and a third surface saying the same thing is the redundancy
    # this lens was designed to avoid. (It is skipped explicitly rather than
    # left to be dropped by render_architecture's slicer, which would discard
    # it silently and cost a build's worth of wasted HTML.)
    _guard_moves = ([] if entity_col else
                    [m for m in _a3_guard.guard_moves(_GUARD)
                     if m["entity"] == slug])
    html = ""
    if _guard_moves:
        _gm_rows = [[
            (f'<span class="tag ic t-hot">{_ins_ic("zap")}</span> '
             if m["kind"] == "function" else
             f'<span class="tag ic t-god">{_ins_ic("fields")}</span> '),
            f'<b>{E(m["title"])}</b><br><small>{E(m["detail"])}</small>',
            f'<code>{E(m["file"].rsplit("/", 1)[-1])}</code>',
            (f'<span class="tag e-{m["effort"].lower()}">{E(m["effort"])}</span>'
             f'<br><small>{E(m["effort_basis"])}</small>'),
            ('<span class="tag s-ok">exact</span>' if m["exact"]
             else '<span class="tag t-tbd">floor</span>'),
        ] for m in _guard_moves[:12]]
        if entity_col:
            for row, m in zip(_gm_rows, _guard_moves[:12]):
                row.insert(0, _ent_cell(m["entity"]))
        html += sechead(
            "Code", "Guard \u2014 unwatched code", "#c2461e", _IC_ZAP,
            sub="what to write a test for before touching this entity again",
            id_="sec-code-guard",
            note=f"{len(_guard_moves)} move(s)"
                 + (f" \u00b7 showing {len(_gm_rows)}"
                    if len(_guard_moves) > len(_gm_rows) else "")
                 + ". A move is code that is USED and that no case NAMES \u2014 "
                   "change it and no NAMED case goes red. Files are one move each "
                   "(writing guards is a file-sized sitting); a function is "
                   "named on its own only when it is load-bearing enough that "
                   "the guard is a single test.",
            info=legend("Confidence:", [
                ("s-ok", "exact", "python \u2014 ast defs joined to recorded "
                                  "case ids \u00b7"),
                ("t-tbd", "floor", "ts/tsx \u2014 exported symbols matched by "
                                   "NAME against what web tests import, so the "
                                   "count is a floor, never a coverage figure")])
        )
        html += table(([ENT_COL, "", "Move", "File", "Cost", "Confidence"]
                       if entity_col else ["", "Move", "File", "Cost",
                                           "Confidence"]), _gm_rows,
                      note="Same cut as the board's Guard track.")

    # --- Endpoints ---------------------------------------------------------
    html += "" if entity_col else subnav(
                  ([("sec-code-guard", "Guard", _IC_ZAP)] if _guard_moves else [])
                  + [
                   ("sec-code-endpoints", "Endpoints", _IC_ZAP),
                   ("sec-code-map", "Code map", _IC_FOLDER),
                   ("sec-code-model", "Data model", _IC_DB),
                   ("sec-code-model-cands", "Data-model candidates",
                    _INS_ICONS["merge"]),
                   ("sec-code-fns", "Functions", _INS_ICONS["fn"]),
                   ("sec-code-fn-cands", "Function candidates",
                    _INS_ICONS["merge"])])
    html += sechead(
        "Code", "Endpoints", "#4f46e5", _IC_ZAP,
        sub="the HTTP surface, parsed from the FastAPI decorators",
        id_="sec-code-endpoints",
        note=f"{len(eps)} endpoint(s) — method, path, docstring, response model "
             f"and handler are read from source at build time, never hand-listed.",
        info=legend("Verb colors:", [
            ("m-get", "GET", "reads — no state change ·"),
            ("m-post", "POST", "creates ·"),
            ("m-mut", "PATCH/PUT", "modifies ·"),
            ("m-del", "DELETE", "removes")])
        + '<div class="leg">Links: the file name jumps to its code-map row; '
          'a violet return type jumps to its definition in the data model. '
          'Click a row for the purpose, the handler function and the models '
          'it uses.</div>')
    _ep_rows = []
    for e in eps:
        fe = _fn_by_filename.get((e["file"], e["fn"]))
        handler = _fn_link(fe) if fe else f'<code>{E(e["fn"])}</code>'
        models_used = []
        resp_toks = [t for t in dict.fromkeys(
            _re_mod.findall(r"[A-Za-z_]\w+", e["resp"]))
            if t in documented or t in ins]
        for t in resp_toks:
            if t in documented:
                href, chip = _href("dm", _anchor("dm", slug, t)), ""
            else:
                href, chip = _xref("dm", t, ins[t].get("entity", ""))
            models_used.append(
                f'<tr><td><a class="dlink" href="{href}">{E(t)}</a>{chip}'
                f'</td><td><span class="tag t-out" title="response model">'
                f"out</span></td></tr>")
        for t in e["touches"]:
            if t not in resp_toks:
                models_used.append(
                    f'<tr><td><a class="dlink" '
                    f'href="{_href("dm", _anchor("dm", slug, t))}">'
                    f'{E(t)}</a></td><td><span class="tag t-in" '
                    f'title="read or written by the handler">touched'
                    f"</span></td></tr>")
        models_tbl = (
            '<table class="tbl"><thead><tr><th>Model</th><th>Role</th>'
            "</tr></thead><tbody>" + "".join(models_used)
            + "</tbody></table>") if models_used else "—"
        meta_rows = [
            (f'{_ins_ic("doc")} PURPOSE', "#64748b",
             md(e["doc"]) if e["doc"] != "—" else "—"),
            (f'{_ins_ic("fn")} HANDLER', "#b45309", handler),
        ]
        detail = ('<table class="tbl dm-meta"><tbody>' + "".join(
            f'<tr><td class="metak" style="color:{col}">{k}</td>'
            f"<td>{v}</td></tr>" for k, col, v in meta_rows)
            + "</tbody></table>")
        # List-valued facts are full-width titled sections (operator ruling
        # 2026-07-23): title line first, table spanning the whole row.
        if models_used:
            detail += (_dmh("#7c3aed", "model", "Models used",
                            f' <span class="sub">({len(models_used)})</span>')
                       + models_tbl)
        _refs_by = _ti["by_endpoint"].get(f'{e["file"]}::{e["fn"]}') or {}
        if _refs_by:
            _srows, _tot = "", 0
            for c2, refs in sorted(_refs_by.items()):
                kind = _ckind.get(c2, c2)
                if refs and refs[0]["state"] == "file":
                    # File-level receipts carry their CASE counts too — the
                    # arithmetic the filtered ledger lands on stays visible.
                    _fn_cases = sum(r.get("n") or 0 for r in refs)
                    _tot += _fn_cases
                    vol = (f"{len(refs)} file(s)"
                           + (f" · {_fn_cases} case(s)" if _fn_cases else ""))
                    st = "file-level receipts"
                else:
                    npass = sum(1 for r in refs if r["state"] == "pass")
                    _tot += len(refs)
                    vol = f"{len(refs)} case(s)"
                    st = (f"{npass} pass"
                          + (f" · {len(refs) - npass} not passing"
                             if len(refs) - npass else ""))
                _srows += (f'<tr><td><span class="tag '
                           f'{_kcls.get(kind, "")}" title="{E(kind)}">'
                           f"{kind_ic(kind, 14)}</span>"
                           f"</td><td>{vol}</td><td>{st}</td></tr>")
            _tm = ("test-matrix.html?led-ep="
                   + _uq(f'{e["method"]} {e["path"]}', safe="")
                   + "&led-strict=1#sec-tests-cases")
            detail += (_dmh("#15803d", "fn", "Tests",
                            f' <a class="sub dlink" href="{_tm}" '
                            f'title="open the case ledger filtered to this '
                            f'route — lands on exactly these receipt '
                            f'case(s)">({_tot} case(s)) {_IC_LINK_SM}</a>')
                       + '<table class="tbl"><thead><tr><th>Kind</th>'
                         "<th>Volume</th><th>State</th></tr></thead><tbody>"
                       + _srows + "</tbody></table>")
        cells = [
            f'<span class="tag {_METHOD_CLS.get(e["method"], "")}">'
            f'{E(e["method"])}</span> <code>{E(e["path"])}</code><br>'
            f'<small>{E(e["fn"])} · '
            f'<a class="flink" style="color:{file_color[e["file"]]}" '
            f'href="{_href("cm", _anchor("cm", slug, e["file"]))}">'
            f'{E(e["file"].rsplit("/", 1)[-1])}</a></small>',
            returns_cell(e), _ep_tcell(e)]
        if entity_col:
            cells.insert(0, _ent_cell(_file_ent.get(e["file"], slug)))
        _ep_rows.append((cells, detail,
                         _rid(_anchor("ep", slug, e["file"] + "-" + e["fn"]))))
    html += xtable(([ENT_COL, "Endpoint", "Returns", "Tests"] if entity_col
                    else ["Endpoint", "Returns", "Tests"]), _ep_rows,
                   widths=(["34px", "2.4fr", "1.1fr", "1.2fr"] if entity_col
                           else ["2.4fr", "1.1fr", "1.2fr"]))

    # --- Code map: one table PER LAYER, each with an honest Defines column --
    _map_info = ('<div class="leg">Click a row: layer · line budget · what '
                 "the file DEFINES — endpoints (verb-colored) · functions "
                 "(linked to the Functions section) · classes (linked to the "
                 "data model) · other exported symbols.</div>")
    layer_desc = {"api": "HTTP routes", "services": "business logic",
                   "models": "DB tables", "schemas": "request/response shapes",
                   "web": "browser UI", "mobile": "native app"}
    documented = model_names | schema_names

    def defines_cell(layer: str, f: str) -> str:
        if layer == "api":
            return " · ".join(ep_chip(e) for e in eps_by_file.get(f, [])) or "—"
        names = amap["defines"].get(f, [])
        if not names:
            return "—"
        chips = []
        for n in names:
            if n in documented:
                chips.append(f'<a class="dlink" href="{_href("dm", _anchor("dm", slug, n))}">'
                             f"{E(n)}</a>")
            else:
                chips.append(f"<code>{E(n)}</code>")
        return " · ".join(chips)

    over = sum(1 for _, _, n in files if n > 800)
    html += sechead(
        "Code", "Code map", "#0f766e", _IC_FOLDER,
        sub="every file this entity lives in, measured on disk",
        id_="sec-code-map",
        note=f"{len(files)} file(s) · {sum(n for _, _, n in files):,} lines "
             f"measured on disk this build · {over} file(s) over the 800-line "
             f"budget. A moved file drops out of this table visibly.",
        info=_map_info + legend("Lines encode the 800-line budget:", [
            ("s-ok", "≤ 800", "within budget ·"),
            ("s-med", "801+", "refactor candidate — red deepens toward 2,000 ·"),
            ("s-high", "≥ 2000", "most intense red")]))
    _cm_rows = []
    for layer, f, n in files:
        if layer == "api":
            fns_c = [ep_chip(e) for e in eps_by_file.get(f, [])]
            cls_c: list[str] = []
            other: list[str] = []
        else:
            fns_c, cls_c, other = [], [], []
            for nm in amap["defines"].get(f, []):
                # parse_defines marks functions with a () suffix; the insight
                # keys are bare names.
                fe = _fn_by_filename.get((f, nm.removesuffix("()")))
                if fe:
                    fns_c.append(_fn_link(fe))
                elif nm in documented:
                    cls_c.append(f'<a class="dlink" '
                                 f'href="{_href("dm", _anchor("dm", slug, nm))}">{E(nm)}</a>')
                elif nm in ins:
                    href, chip = _xref("dm", nm, ins[nm].get("entity", ""))
                    cls_c.append(f'<a class="dlink" href="{href}">{E(nm)}</a>'
                                 + chip)
                else:
                    other.append(f"<code>{E(nm)}</code>")
        budget = ("within the 800-line budget" if n <= 800 else
                  f"{round(n * 100 / 800)}% of the budget — split candidate")
        meta_rows = [
            (f'{_ins_ic("doc")} LAYER', "#0f766e",
             f'{E(layer)} — {E(layer_desc.get(layer, ""))}'),
            (f'{_ins_ic("fields")} BUDGET', "#b3403a",
             f"{n:,} lines · {E(budget)}"),
        ]
        if fns_c:
            meta_rows.append((f'{_ins_ic("fn")} '
                              + ("ENDPOINTS" if layer == "api"
                                 else "FUNCTIONS DEFINED"), "#b45309",
                              " · ".join(fns_c)))
        if cls_c:
            meta_rows.append((f'{_ins_ic("model")} CLASSES DEFINED', "#7c3aed",
                              " · ".join(cls_c)))
        if other:
            meta_rows.append((f'{_ins_ic("doc")} OTHER SYMBOLS', "#64748b",
                              " · ".join(other)))
        detail = ('<table class="tbl dm-meta"><tbody>' + "".join(
            f'<tr><td class="metak" style="color:{col}">{k}</td>'
            f"<td>{v}</td></tr>" for k, col, v in meta_rows)
            + "</tbody></table>")
        cells = [f'<span class="tag {_LAYER_CLS.get(layer, "")}" '
                 f'title="{E(layer_desc.get(layer, ""))}">{E(layer)}</span>',
                 f"<code>{E(f)}</code>", lines_grade(n), _cm_tcell(f)]
        if entity_col:
            cells.insert(0, _ent_cell(_file_ent.get(f, slug)))
        _cm_rows.append((cells, detail, _rid(_anchor("cm", slug, f))))
    html += xtable(([ENT_COL, "Layer", "File", "Lines", "Tests"] if entity_col
                    else ["Layer", "File", "Lines", "Tests"]), _cm_rows,
                   widths=(["34px", "0.8fr", "2.1fr", "0.8fr", "1.2fr"]
                           if entity_col
                           else ["0.8fr", "2.2fr", "0.8fr", "1.2fr"]))

    # --- Data model: header-table cards; compositions LINK, never repeat ----
    def link_types(typ: str, src_file: str = "") -> str:
        """A field typed with another documented class links to that class's
        card — on THIS page, or cross-entity via _xref (with the entity
        label). A CamelCase name that is app-internal by import but documented
        NOWHERE renders the 'to be designed' pending link (entity-index is the
        placeholder home; the crawl gate counts these per page). Every OTHER
        identifier is colored by its type family."""
        import re as _re

        def one(m: _re.Match) -> str:
            tok = m.group(0)
            if tok in documented:
                return (f'<a class="dlink" href="{_href("dm", _anchor("dm", slug, tok))}">'
                        f"{tok}</a>")
            o = ins.get(tok)
            if o:
                href, chip = _xref("dm", tok, o.get("entity", ""))
                return f'<a class="dlink" href="{href}">{tok}</a>{chip}'
            if (src_file and tok[:1].isupper()
                    and _file_imports(src_file).get(tok)):
                return ('<a class="dlink" href="entity-index.html" '
                        'title="to be designed — an app type not documented '
                        'in any entity map yet; the entity index is its '
                        f'placeholder home">{tok}'
                        '<span class="tag ic t-tbd">tbd</span></a>')
            cls = _TYPE_CLS.get(tok)
            return f'<span class="ty {cls}">{tok}</span>' if cls else tok

        # Quoted segments are Literal VALUES, not type names — split them out
        # first so an enum value like 'date' is never colored as a type.
        return "".join(
            E(part) if i % 2 else _re.sub(r"[A-Za-z_]\w*", one, E(part))
            for i, part in enumerate(_re.split(r"('[^']*')", typ[:60])))

    by_cls = {m["cls"]: m for m in models}

    def _incoming_fk_tbl(cls: str) -> str:
        """Referenced by — the STORED side of the in-degree: every ForeignKey
        column in another model that points at this table (was the unlabeled
        '+N FK in-degree' line; operator ruling 2026-07-23: structure facts
        live in the structure, labeled)."""
        me = by_cls.get(cls)
        if not me:
            return ""
        rows = ""
        for other, rec in by_cls.items():
            if other == cls:
                continue
            for col, tgt2 in rec.get("fks", {}).items():
                if tgt2.split(".")[0] == me["table"]:
                    _oent = ins.get(other, {}).get("entity", "")
                    rows += (f'<tr><td><a class="dlink" href="'
                             f'{_href("dm", _anchor("dm", slug, other))}">'
                             f"{E(other)}</a>"
                             + (" " + entity_badge(_oent, _adopt_name(_oent),
                                                   12) if _oent else "")
                             + f"</td><td><code>{E(other)}.{E(col)}</code>"
                             f"</td><td><code>{E(tgt2)}</code></td></tr>")
        if not rows:
            return ""
        return (_dmh("#0d6e78", "fields", "Referenced by",
                     ' <span class="sub">ForeignKey columns in other models '
                     "pointing at this table</span>")
                + '<table class="tbl"><thead><tr><th>Model</th>'
                  "<th>FK column</th><th>Points at</th></tr></thead>"
                  f"<tbody>{rows}</tbody></table>")

    def rel_rows(cls: str, rels: list[dict]) -> str:
        """ORM navigation properties, rendered APART from columns — with the
        one stored direction (the ForeignKey) named for each. A back_populates
        pair is two views of one FK, never circular storage."""
        if not rels:
            return ""
        rows = ""
        for r in rels:
            tgt = by_cls.get(r["target"])
            _tent = ins.get(r["target"], {}).get("entity", "")
            # The target link is minted THREE ways, never blindly (gastify 2026-09-04: `User` is an FK
            # target with no card on any page and no home entity — the unconditional same-page anchor
            # was a dead link the center gate rightly failed): a CARD on this page → its anchor; a class
            # some other entity documents → that page's anchor (+ chip); neither → the to-be-designed
            # reference every other undocumented app type already gets (counted, never a dead anchor).
            if tgt is not None:
                link = (f'<a class="dlink" href="{_href("dm", _anchor("dm", slug, r["target"]))}">'
                        f'{E(r["target"])}</a>'
                        + (" " + entity_badge(_tent, _adopt_name(_tent), 12)
                           if _tent else ""))
            elif _tent and _tent != slug:
                _xh, _xc = _xref("dm", r["target"], _tent)
                link = f'<a class="dlink" href="{_xh}">{E(r["target"])}</a>{_xc}'
            else:
                link = ('<a class="dlink" href="entity-index.html" title="to be designed — an app '
                        'type not documented in any entity map yet; the entity index is its '
                        f'placeholder home">{E(r["target"])}<span class="tag ic t-tbd">tbd</span></a>')
            if r["many"]:
                kind = "one → many"
                via = next((f'{r["target"]}.{c} → {t2}'
                            for c, t2 in (tgt["fks"].items() if tgt else [])
                            if by_cls.get(cls) and t2.split(".")[0] == by_cls[cls]["table"]),
                           "—")
            else:
                kind = "many → one"
                me = by_cls.get(cls)
                via = next((f'{cls}.{c} → {t2}'
                            for c, t2 in (me["fks"].items() if me else [])
                            if tgt and t2.split(".")[0] == tgt["table"]), "—")
            back = (f'back_populates=<code>{E(r["back"])}</code>' if r["back"] else "—")
            casc = f' · cascade <code>{E(r["cascade"])}</code>' if r["cascade"] else ""
            rows += (f"<tr><td><code>{E(r['name'])}</code></td><td>{link} "
                     f"<small>{kind}</small></td>"
                     f"<td><code>{E(via)}</code></td><td>{back}{casc}</td></tr>")
        return (_dmh("#b45309", "fields", "Relationships",
                     ' <span class="sub">ORM navigation, not stored columns '
                     "— each is a view over ONE ForeignKey</span>")
                + f'<table class="tbl"><thead><tr><th>Attribute</th><th>Target</th>'
                f"<th>Stored as (the FK)</th><th>Paired via</th></tr></thead>"
                f"<tbody>{rows}</tbody></table>")

    def _dm_meta(cls: str, kind_html: str, doc: str = "") -> str:
        """Kind + docstring only — the usage facts are titled TABLES now."""
        rows = [(f'{_ins_ic("model" if "model" in kind_html else "schema")} KIND',
                 "#7c3aed", kind_html)]
        if doc:
            rows.append((f'{_ins_ic("doc")} DOCSTRING', "#64748b", E(doc)))
        body = "".join(
            f'<tr><td class="metak" style="color:{col}">{k}</td>'
            f"<td>{v}</td></tr>" for k, col, v in rows)
        return f'<table class="tbl dm-meta"><tbody>{body}</tbody></table>'

    def _dm_api_tbl(cls: str, is_schema: bool) -> str:
        """Usage by API — the teal bar's receipts: one row per endpoint that
        touches the class, linked to its endpoint row."""
        c = ins.get(cls, {})
        n = c.get("usage", 0)
        bar = (f'<span class="ubar" style="width:{max(2, min(60, n * 11))}px">'
               f"</span><b>{n}</b>")
        head = _dmh("#0d6e78", "zap", "Usage by API", f" {bar}")
        hits = [e for e in eps
                if cls in e["touches"] or (is_schema and cls in e["resp"])]
        if not hits:
            return head + ('<p class="sub">no API usage on record — '
                           "the teal bar is empty.</p>")
        body = "".join(
            f"<tr><td>{ep_chip(e)}</td><td><code>{E(e['fn'])}</code></td>"
            f"<td>{_fchip(e['file'])}</td></tr>" for e in hits)
        return (head + '<table class="tbl"><thead><tr><th>Endpoint</th>'
                "<th>Handler</th><th>Defined in</th></tr></thead>"
                f"<tbody>{body}</tbody></table>")

    def _dm_int_tbl(cls: str) -> str:
        """Usage by internal — the violet bar's receipts: one row per mapped
        backend file referencing the class, with the functions that do."""
        c = ins.get(cls, {})
        n = c.get("internal", 0)
        bar = (f'<span class="ubar u-int" style="width:'
               f'{max(2, min(60, n * 11))}px"></span><b>{n}</b>')
        head = _dmh("#7c3aed", "schema", "Usage by internal", f" {bar}")
        refs = c.get("internal_refs") or []
        if not refs:
            return head + ('<p class="sub">no internal references across the '
                           "mapped backend files — the violet bar is empty.</p>")
        # Functions are documented now — each referencing def LINKS to its
        # Functions row (here or on its owner's page) and carries the in/out
        # label: where this class sits in that function's signature. A ref
        # with no def is module level (imports, constants) — which is why the
        # axis stays "internal", not "functions".
        body = ""
        for r in refs:
            fdefs = []
            for d in r["defs"]:
                fe = _fn_by_filename.get((r["file"], d))
                fdefs.append(_fn_link(fe, io_cls=cls) if fe
                             else f"<code>{E(d)}</code>")
            body += (f"<tr><td>{_fchip(r['file'])}</td><td>"
                     + (" · ".join(fdefs)
                        or "<span class='sub'>module level</span>")
                     + "</td></tr>")
        return (head + '<table class="tbl"><thead><tr><th>File</th>'
                "<th>Referencing function(s)</th></tr></thead>"
                f"<tbody>{body}</tbody></table>")

    def _dm_detail(cls: str, fields: list, meta_html: str = "",
                   rels: list[dict] | None = None, is_schema: bool = True,
                   uqs: list | None = None, src_file: str = "") -> str:
        """The in-place expansion, in titled blocks (operator polish
        2026-07-23): metadata (kind · docstring) → Usage by API → Usage by
        internal → relationships → Structure (columns, with unique-constraint
        chips packed onto their rows). Descriptions read from source; absent
        renders an em dash. Older 2-tuple archmaps stay renderable."""
        uq_cols: set = set()
        leftover_uqs = []
        fnames = {str(f[0]) for f in fields}
        for u in (uqs or []):
            named = set(_re_mod.findall(r"'([A-Za-z_][A-Za-z0-9_]*)'", u)) & fnames
            if named:
                uq_cols |= named
            else:
                leftover_uqs.append(u)
        body = ""
        for f in fields:
            n, t = f[0], f[1]
            d = f[2] if len(f) > 2 and f[2] else "—"
            uq_chip = (' <span class="tag t-uq" title="part of a UNIQUE '
                       'constraint">unique</span>' if n in uq_cols else "")
            body += (f"<tr><td><code>{E(n)}</code>{uq_chip}</td>"
                     f"<td>{link_types(t, src_file)}</td>"
                     f"<td><code>{E(_example(n, t))}</code></td>"
                     f"<td>{E(trunc(d, 96))}</td></tr>")
        struct_head = _dmh("#b3403a", "fields", "Structure",
                           f' <span class="sub">{len(fields)} column(s)</span>')
        leftover = "".join(
            f'<p class="sub">Constraint: <code>{E(u)}</code></p>'
            for u in leftover_uqs)
        # Tested by — the ENDPOINT-style aggregation; the count-link title
        # opens the actual cases in the filtered ledger.
        _tb = _ti["by_model"].get(cls) or {}
        tb_html = _tb_summary(_tb)
        if tb_html:
            _tbtot = _rcnt((_tb.get("direct") or [])
                           + (_tb.get("via_route") or []))
            _tbsee = ("test-matrix.html?led-mdl=" + _uq(cls, safe="")
                      + "&led-strict=1#sec-tests-cases")
            tb_html = _dmh("#15803d", "fn", "Tested by",
                           f' <a class="sub dlink" href="{_tbsee}" '
                           f'title="open the case ledger filtered to this '
                           f'class — lands on exactly these receipt '
                           f'case(s)">({_tbtot} case(s)) {_IC_LINK_SM}</a>'
                           ) + tb_html
        return (f"{meta_html}{_dm_api_tbl(cls, is_schema)}{_dm_int_tbl(cls)}"
                f"{rel_rows(cls, rels or [])}"
                f"{_incoming_fk_tbl(cls) if not is_schema else ''}"
                f"{tb_html}"
                f"{struct_head}{leftover}"
                f'<table class="tbl"><thead><tr><th>Column</th><th>Type</th>'
                f"<th>Example (synthetic)</th><th>Description</th></tr></thead>"
                f"<tbody>{body}</tbody></table>")

    _DM_W = ["2.2fr", "0.9fr", "1.7fr", "1.2fr"]

    html += sechead(
        "Code", "Data model", "#7c3aed", _IC_DB,
        sub="DB entities and API shapes — each names its file and "
            "the endpoints that touch it", id_="sec-code-model",
        info='<div class="leg">A field typed with another documented class LINKS '
             "to it (violet) instead of repeating its structure. Examples are "
             "synthetic — derived from Literal values and field-name heuristics, "
             "never real user data.</div>"
             + '<div class="leg">Type colors — one hue per family, deeper = the '
               'wider type: <span class="ty ty-num1">int</span> '
               '<span class="ty ty-num2">float · Decimal</span> numeric · '
               '<span class="ty ty-tim1">date · time</span> '
               '<span class="ty ty-tim2">datetime</span> temporal · '
               '<span class="ty ty-str1">str</span> '
               '<span class="ty ty-str2">bytes · Text</span> textual · '
               '<span class="ty ty-bool">bool</span> · '
               '<span class="ty ty-json">list · dict · Literal</span> '
               'structured · <span class="ty ty-id">UUID</span> identity · '
               '<span class="ty ty-null">None</span> nullable. An uncolored '
               "token is a domain alias (an enum defined in this codebase).</div>"
             + '<div class="leg"><b>Insight icons</b> — the DATA-MODEL lens; '
               "the same shape runs over other member kinds later (functions "
               "· methods), scoped, never mixed:"
               '<ul class="iclist">'
               f"<li>{itag('l-models', 'model', 'model')} <b>model</b> — a "
               "persisted DB entity: lives in a table, owns FKs.</li>"
               f"<li>{itag('l-schemas', 'schema', 'schema')} <b>schema</b> — "
               "an API / pipeline shape: crosses a boundary, owns no "
               "storage.</li>"
               f"<li>{itag('t-base', 'base', 'base class')} <b>base</b> — "
               "derives from NOTHING: no FK out, no field typed by another "
               "documented class; a foundation others build on.</li>"
               f"<li>{itag('t-god', 'fields', 'god-class flag', 'N')} "
               f"<b>god-class flag</b> — field count ≥ {_GOD_FIELDS}; the "
               f"number that makes it a {itag('t-god', 'split', 'split candidate')} "
               "split candidate below.</li>"
               f"<li>{itag('t-sim', 'sim', 'structural twin', 'Class N%')} "
               "<b>closest structural twin</b> — % = shared fields over the "
               f"union (Jaccard); a ≥{int(_MERGE_FLOOR * 100)}% pair becomes "
               f"a {itag('t-sim', 'merge', 'merge candidate')} merge candidate "
               "below.</li>"
               "<li>Usage bars: teal = api (endpoint touches + FK in) · "
               "violet = internal (mapped backend files referencing the "
               "class). Both bars are EVIDENCE, never a verdict: they count "
               "references inside the config-mapped files only, so a zero "
               "means <i>no indexed usage — go check</i>, never <i>dead</i>. "
               "One unmapped file falsifies a zero; nothing falsifies a "
               "count.</li>"
               "</ul></div>"
             + (f'<p class="sub"><b>About this section</b></p>{intro_html}'
                if intro_html else ""))
    ins = model_insight(repo)
    html += ('<div class="dmchips" id="dm-chips">'
             + "".join(f'<button class="chip" data-f="{k}">{lbl}</button>'
                       for k, lbl in (("all", "All"), ("t-base", "base"),
                                      ("t-sim", "≈ similar"),
                                      ("t-god", "god"))) + "</div>")
    html += (f'<p class="sub"><span class="tag l-models">models</span> '
             f"{len(models)} DB entity class(es) — click a row to open its "
             f"columns:</p>")
    _mrows = []
    for m in models:
        meta = _dm_meta(m["cls"],
                        f'model — table <code>{E(m["table"])}</code>',
                        doc=m.get("doc") or "")
        _own = ins.get(m["cls"], {}).get("entity", slug)
        cells = ([_ent_cell(_own)] if entity_col else []) + [
                 f'<b>{E(m["cls"])}</b><br>{_ins_tags(m["cls"], ins)}'] + \
                ([] if entity_col else [E(_own)]) + [
                 f'<code>{E(m["file"])}</code>',
                 _ins_usage(m["cls"], ins),
                 _duo_tcell(_ti["by_model"].get(m["cls"]), "class")]
        _mrows.append((cells,
                       _dm_detail(m["cls"], m["cols"], meta, m["rels"],
                                  is_schema=False, uqs=m["uqs"],
                                  src_file=m["file"]),
                       _rid(_anchor("dm", slug, m["cls"]))))
    _dm_head = ([ENT_COL, "Class", "File", "Usage", "Tests"] if entity_col
                else ["Class", "Entity", "File", "Usage", "Tests"])
    _dm_w = (["34px", "2fr", "1.5fr", "1.1fr", "1.2fr"] if entity_col
             else [*_DM_W, "1.2fr"])
    html += xtable(_dm_head, _mrows, widths=_dm_w)
    html += (f'<p class="sub" style="margin-top:14px">'
             f'<span class="tag l-schemas">schemas</span> {len(schemas)} API '
             f"schema(s) — the shapes the Returns column links to:</p>")
    _srows = []
    for s_ in schemas:
        meta = _dm_meta(s_["cls"], "API schema", doc=s_.get("doc") or "")
        _own = ins.get(s_["cls"], {}).get("entity", slug)
        cells = ([_ent_cell(_own)] if entity_col else []) + [
                 f'<b>{E(s_["cls"])}</b><br>{_ins_tags(s_["cls"], ins)}'] + \
                ([] if entity_col else [E(_own)]) + [
                 f'<code>{E(s_["file"])}</code>',
                 _ins_usage(s_["cls"], ins),
                 _duo_tcell(_ti["by_model"].get(s_["cls"]), "schema")]
        _srows.append((cells,
                       _dm_detail(s_["cls"], s_["fields"], meta,
                                  src_file=s_["file"]),
                       _rid(_anchor("dm", slug, s_["cls"]))))
    html += xtable(_dm_head, _srows, widths=_dm_w)

    # -- Data-model candidates: named by the machine, ruled by judgment ------
    own = {m["cls"] for m in models} | {s_["cls"] for s_ in schemas}
    cands = ""
    seen_pairs: set = set()
    for cls in sorted(own):
        c = ins.get(cls)
        if not c or not c["sim"] or c["sim"]["j"] < _MERGE_FLOOR:
            continue
        key = tuple(sorted((cls, c["sim"]["cls"])))
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        s = c["sim"]
        _ec = (f"<td>{_ent_cell(ins.get(key[0], {}).get('entity', slug))}</td>"
               if entity_col else "")
        cands += (f'<tr>{_ec}<td>{itag("t-sim", "merge", "merge candidate")}</td>'
                  f'<td><code>{E(key[0])}</code> ≈ <code>{E(key[1])}</code></td>'
                  f'<td>{int(s["j"] * 100)}% structural twin ({s["shared"]}/'
                  f'{s["of"]} fields) — justified echo, or duplication waiting '
                  f"to drift? Rule it.</td></tr>")
    for cls in sorted(own, key=lambda k: (-len(ins[k]["fields"])
                                          if k in ins else 0, k)):
        c = ins.get(cls)
        if c and c["god"]:
            _ec = (f"<td>{_ent_cell(ins.get(cls, {}).get('entity', slug))}</td>"
                   if entity_col else "")
            cands += (f'<tr>{_ec}<td>{itag("t-god", "split", "split candidate")}</td>'
                      f'<td><code>{E(cls)}</code></td>'
                      f'<td>{len(c["fields"])} fields — past the {_GOD_FIELDS}-'
                      f"field line; the number names it, judgment rules it."
                      f"</td></tr>")
    _n_cands = cands.count("<tr>")
    html += sechead(
        "Code", "Data-model candidates", "#7c3aed", _INS_ICONS["merge"],
        sub="MERGE and SPLIT — named by the machine, ruled by judgment; the "
            "verdict lands in DECISIONS/PENDING via review or a health pass, "
            "never here",
        id_="sec-code-model-cands",
        note=f"{_n_cands} candidate(s) this build · each wears the color and "
             f"icon dialect of the flag that triggered it on the Data model "
             f"page.",
        info='<div class="leg"><b>What the candidate icons mean</b>'
             '<ul class="iclist">'
             f"<li>{itag('t-sim', 'merge', 'merge candidate')} <b>merge</b> — "
             f"structural twins ≥ {int(_MERGE_FLOOR * 100)}% (from the "
             f"{itag('t-sim', 'sim', 'similarity flag')} similarity flag).</li>"
             f"<li>{itag('t-god', 'split', 'split candidate')} <b>split</b> — "
             f"a god class ≥ {_GOD_FIELDS} fields (from the "
             f"{itag('t-god', 'fields', 'fields flag', 'N')} fields flag)."
             "</li></ul></div>"
             '<div class="leg"><b>Why these two, and not "nothing uses '
             'this"</b> — similarity and size are CORPUS-COMPLETE signals: '
             "two mapped classes sharing 87% of their field names is TRUE no "
             "matter what lives outside the map, and a 22-field class is 22 "
             "fields however little the config covers. Absence of references "
             "is neither — a single file outside the entity config falsifies "
             "it. This section names only what the instrument can actually "
             "support. The usage evidence lives on the Data model page — two "
             "bars per class, api and internal — and a reader checks it there."
             "</div>"
             '<div class="leg"><b>The floor, stated honestly</b> — the '
             "similarity flag records the TOP-1 nearest neighbour per class "
             f"only, only above the {int(_SIM_FLOOR * 100)}% line, Python "
             "only, mapped files only, and only field NAMES (types and "
             "semantics are not compared). Every one of those is a way to "
             f"MISS a pair, never a way to invent one. This TABLE cuts higher "
             f"still — it lists pairs at \u2265 {int(_MERGE_FLOOR * 100)}%, so "
             f"the {int(_SIM_FLOOR * 100)}% recording floor is what the flag "
             "sees, not what you are reading. This page is a FLOOR, not a "
             "census: it under-reports duplication and always will. That "
             "direction is the safe one — under-reporting a positive signal "
             "costs you a missed merge; under-reporting absence gets live "
             "code deleted.</div>"
             '<div class="leg"><b>Known blind spot</b> \u2014 classes outside '
             "the entity config are invisible here, and the misses cluster "
             "there rather than in the maths: two modules can carry near-"
             "identical schemas and drift apart for months without either "
             "appearing on this page, if one of them is not in the config. "
             "An empty candidates table means the mapped set is clean, not "
             "the repository.</div>")
    if cands:
        html += (
            "<table class=\"tbl\"><thead><tr>"
            + (f"<th>{th_label(ENT_COL)}</th>" if entity_col else "")
            + "<th>Candidate</th><th>Classes</th>"
            "<th>Why the machine flags it</th></tr></thead>"
            f"<tbody>{cands}</tbody></table>")
    else:
        html += ('<p class="sub">No data-model candidates <b>in the mapped set</b> this build — no twins past the merge line, no god classes. Files outside the entity config were never examined.</p>')
    # ---- Functions — the FUNCTIONS lens (sibling of the data model) --------
    fins = function_insight(repo)
    page_py = {f for _layer, f, _n in files if f.endswith(".py")}
    frows_src = sorted((c for c in fins.values() if c["file"] in page_py),
                       key=lambda c: (-(c["api"] + c["internal"]), c["fn"]))
    plain_names = {c["name"] for c in fins.values()
                   if not c["method"] and len(c["name"]) >= 4}
    qual_by_name = {}
    for c in fins.values():
        qual_by_name.setdefault(c["name"], c)
    if frows_src:
        html += sechead(
            "Code", "Functions", "#b45309", _INS_ICONS["fn"],
            sub="every def in this entity's mapped backend files — the "
                "FUNCTIONS lens, sibling of the data model above",
            id_="sec-code-fns",
            note=f"{len(frows_src)} def(s) · click a row for its usage "
                 f"receipts, calls and signature · same dialect as the data "
                 f"model: tags · filters · two-bar usage · candidates.",
            info='<div class="leg"><b>Insight icons</b> — the FUNCTIONS lens:'
                 '<ul class="iclist">'
                 f"<li>{itag('l-services', 'fn', 'function')} <b>function</b> "
                 "— a module-level def.</li>"
                 f"<li>{itag('l-models', 'method', 'method')} <b>method</b> — "
                 "a def bound to a class.</li>"
                 f"<li>{itag('l-api', 'zap', 'endpoint handler')} <b>endpoint "
                 "handler</b> — a route decorator serves it.</li>"
                 f"<li>{itag('t-base', 'base', 'base function')} <b>base</b> — "
                 "calls no other documented function; a foundation others "
                 "build on.</li>"
                 f"<li>{itag('t-god', 'fields', 'god-function flag', 'N')} "
                 f"<b>god-function flag</b> — length ≥ {_FN_GOD_LINES} lines; "
                 f"makes it a {itag('t-god', 'split', 'split candidate')} "
                 "split candidate below.</li>"
                 f"<li>{itag('t-sim', 'sim', 'structural twin', 'fn N%')} "
                 "<b>closest structural twin</b> — body-identifier overlap "
                 f"(Jaccard); a ≥{int(_FN_MERGE_FLOOR * 100)}% pair becomes a "
                 f"{itag('t-sim', 'merge', 'merge candidate')} merge candidate "
                 "below.</li>"
                 "<li>Usage bars: teal = api (endpoints served + api-layer "
                 "files referencing) · violet = internal (mapped files "
                 "referencing — same-file calls outside the def count: a "
                 "helper used within its module is used). Both bars are "
                 "EVIDENCE, never a verdict: the scan reads config-mapped "
                 "Python only, so a zero reads <i>no indexed caller — go "
                 "check</i>, never <i>dead</i>.</li></ul></div>")
        html += ('<div class="dmchips" id="fn-chips">'
                 + "".join(f'<button class="chip" data-f="{k}">{lbl}</button>'
                           # `unguarded` is a FILTER, not a per-row label: it
                           # is the majority state, so the useful act is
                           # narrowing to it, and `hot` narrows further to the
                           # ones with real callers behind them.
                           for k, lbl in (("all", "All"), ("t-unguarded",
                                                           "unguarded"),
                                          ("t-hot", "hot &amp; unguarded"),
                                          ("t-base", "base"),
                                          ("t-sim", "≈ similar"),
                                          ("t-god", "god"))) + "</div>")

        def _fn_tags(c: dict) -> str:
            out = (itag("l-models", "method", "method — bound to a class")
                   if c["method"] else
                   itag("l-services", "fn", "function — module-level def"))
            if c["handler"]:
                out += " " + itag("l-api", "zap",
                                  "endpoint handler — a route serves it")
            if c["base"]:
                out += " " + itag("t-base", "base",
                                  "base — calls no other documented function")
            if c["god"]:
                out += " " + itag("t-god", "fields",
                                  f"god-function flag — {c['lines']} lines",
                                  str(c["lines"]))
            # HOT AND UNGUARDED — the only unguarded subset worth a visible
            # mark: real callers behind it, so a change lands somewhere and
            # nothing catches it. Everything else is reachable via the filter.
            _k = f'{c["file"]}::{c["fn"]}'
            if (not (_ti.get("by_function", {}).get(_k)
                     or _ti.get("by_endpoint", {}).get(_k))
                    and (c.get("usage") or 0) >= _a3_guard.HOT_USAGE):
                out += " " + itag("t-hot", "zap",
                                  f"hot and unguarded — called from "
                                  f"{c['usage']} places, named by no case",
                                  str(c["usage"]))
            if c["sim"]:
                s = c["sim"]
                out += " " + itag("t-sim", "sim",
                                  f"closest structural twin — {s['shared']}/"
                                  f"{s['of']} shared identifiers",
                                  f'{E(s["cls"])} {int(s["j"] * 100)}%')
            return out

        def _fn_usage_cell(c: dict) -> str:
            w_api = max(2, min(60, c["api"] * 11))
            w_int = max(2, min(60, c["internal"] * 11))
            return (f'<span class="ubar" style="width:{w_api}px"></span>'
                    f'<b>{c["api"]}</b> <small>api</small><br>'
                    f'<span class="ubar u-int" style="width:{w_int}px"></span>'
                    f'<b>{c["internal"]}</b> <small>internal</small>')

        def _fn_refs_rx(c: dict):
            return (_re_mod.compile(rf"\.{_re_mod.escape(c['name'])}\b")
                    if c["method"] else
                    _re_mod.compile(rf"\b{_re_mod.escape(c['name'])}\b"))

        def _fn_detail(c: dict) -> str:
            kind = ("endpoint handler" if c["handler"]
                    else "method" if c["method"] else "function")
            kind += " · async" if c["async"] else ""
            kind += f' · {c["lines"]} lines · layer {E(c["layer"] or "—")}'
            meta_rows = [(f'{_ins_ic("fn")} KIND', "#b45309", E(kind))]
            if c["doc"] and c["doc"] != "—":
                meta_rows.append((f'{_ins_ic("doc")} DOCSTRING', "#64748b",
                                  E(c["doc"])))
            meta = ('<table class="tbl dm-meta"><tbody>' + "".join(
                f'<tr><td class="metak" style="color:{col}">{k}</td>'
                f"<td>{v}</td></tr>" for k, col, v in meta_rows)
                + "</tbody></table>")
            # Usage by API
            bar = (f'<span class="ubar" style="width:'
                   f'{max(2, min(60, c["api"] * 11))}px"></span><b>{c["api"]}</b>')
            api_head = _dmh("#0d6e78", "zap", "Usage by API", f" {bar}")
            served = [e for e in eps
                      if e["fn"] == c["name"] and e["file"] == c["file"]]
            api_files = [f for f in c["ref_files"] if f != c["file"]]
            api_html = api_head
            if served:
                api_html += ('<table class="tbl"><thead><tr><th>Endpoint</th>'
                             "<th>Status</th></tr></thead><tbody>"
                             + "".join(f"<tr><td>{ep_chip(e)}</td>"
                                       f'<td><code>{E(e["status"])}</code></td>'
                                       f"</tr>" for e in served)
                             + "</tbody></table>")
            elif c["api"]:
                api_html += ('<p class="sub">referenced from api-layer '
                             "file(s): " + " · ".join(
                                 _fchip(f) for f in api_files) + "</p>")
            else:
                api_html += ('<p class="sub">no endpoint serves it, no '
                             "api-layer file references it — the teal bar is "
                             "empty.</p>")
            # Usage by internal
            ibar = (f'<span class="ubar u-int" style="width:'
                    f'{max(2, min(60, c["internal"] * 11))}px"></span>'
                    f'<b>{c["internal"]}</b>')
            int_head = _dmh("#7c3aed", "schema", "Usage by internal", f" {ibar}")
            rx = _fn_refs_rx(c)
            int_rows = ""
            for f in c["ref_files"]:
                txt = _PY_TEXTS.get(f, "")
                if not txt:
                    continue
                if f == c["file"]:
                    ls = txt.splitlines()
                    s, e_ = c["span"]
                    txt_probe = "\n".join(ls[:s - 1] + [""] * (e_ - s + 1)
                                          + ls[e_:])
                else:
                    txt_probe = txt
                lines_f = txt_probe.splitlines()
                defs = [name for name, s2, e2 in _def_spans(f, txt)
                        if rx.search("\n".join(lines_f[s2 - 1:e2]))]
                defs = list(dict.fromkeys(defs))[:6]
                linked = []
                for d in defs:
                    fe = _fn_by_filename.get((f, d))
                    linked.append(_fn_link(fe) if fe else f"<code>{E(d)}</code>")
                int_rows += (f"<tr><td>{_fchip(f)}"
                             + (" <small>(own file)</small>"
                                if f == c["file"] else "")
                             + "</td><td>"
                             + (" · ".join(linked)
                                or "<span class='sub'>module level</span>")
                             + "</td></tr>")
            int_html = int_head + (
                ('<table class="tbl"><thead><tr><th>File</th>'
                 "<th>Referencing function(s)</th></tr></thead>"
                 f"<tbody>{int_rows}</tbody></table>") if int_rows else
                '<p class="sub">no references across the mapped files — the '
                "violet bar is empty.</p>")
            # Calls — documented functions this body references
            calls = sorted(n for n in plain_names
                           if n != c["name"] and n in c["ids"])
            call_chips = []
            for n in calls:
                tgt = qual_by_name.get(n)
                call_chips.append(_fn_link(tgt) if tgt
                                  else f"<code>{E(n)}</code>")
            calls_html = (_dmh("#0f766e", "merge", "Calls",
                               f' <span class="sub">{len(calls)} documented '
                               f"function(s)</span>")
                          + ('<p class="sub">' + " · ".join(call_chips)
                             + "</p>"
                             if calls else
                             '<p class="sub">calls no other documented '
                             "function — a base.</p>"))
            # Tested by — the ENDPOINT-style aggregation; the count-link
            # title opens the actual cases in the filtered ledger.
            _tb = _ti["by_function"].get(f'{c["file"]}::{c["fn"]}') or {}
            _seeall = ("test-matrix.html?led-fn="
                       + _uq(c["name"] + "()", safe="")
                       + "&led-strict=1#sec-tests-cases")
            tb_html = _tb_summary(_tb)
            if tb_html:
                _tbtot = _rcnt((_tb.get("direct") or [])
                               + (_tb.get("via_route") or []))
                tb_html = _dmh("#15803d", "fn", "Tested by",
                               f' <a class="sub dlink" href="{_seeall}" '
                               f'title="open the case ledger filtered to '
                               f'this function — lands on exactly these '
                               f'receipt case(s)">({_tbtot} case(s)) '
                               f"{_IC_LINK_SM}</a>") + tb_html
            # Signature
            sig_head = _dmh("#b3403a", "fields", "Signature",
                            f' <span class="sub">{len(c["params"])} param(s) '
                            f"in · "
                            + ("1 return out" if c.get("returns") else
                               "return unannotated") + "</span>")
            # Every documented class in a type LINKS (link_types), and each
            # row says which side of the function it sits on: params are IN,
            # the return is OUT — the same in/out dialect the class pages use.
            srows = "".join(
                f"<tr><td><code>{E(p)}</code></td>"
                f"<td>{link_types(t, c['file']) if t else '—'}</td>"
                f'<td><span class="tag t-in">in</span></td></tr>'
                for p, t in c["params"])
            srows += ("<tr><td><i>returns</i></td>"
                      f"<td>{link_types(c['returns'], c['file']) if c.get('returns') else '—'}</td>"
                      f'<td><span class="tag t-out">out</span></td></tr>')
            sig = ('<table class="tbl"><thead><tr><th>Param</th>'
                   "<th>Type</th><th>Role</th></tr></thead><tbody>"
                   + srows + "</tbody></table>")
            return (meta + api_html + int_html + calls_html + tb_html
                    + sig_head + sig)

        _frows = []
        for c in frows_src:
            cells = ([_ent_cell(c["entity"])] if entity_col else []) + [
                     f'<b><code>{E(c["fn"])}</code></b><br>{_fn_tags(c)}'] + \
                    ([] if entity_col else [E(c["entity"])]) + [
                     f'<code>{E(c["file"])}</code>',
                     _fn_usage_cell(c),
                     _duo_tcell(_ti["by_function"].get(
                         f'{c["file"]}::{c["fn"]}'), "function")]
            _frows.append((cells, _fn_detail(c),
                           _rid(_anchor("fn", slug,
                                        c["file"] + "-" + c["fn"]))))
        html += xtable(([ENT_COL, "Function", "File", "Usage", "Tests"]
                        if entity_col
                        else ["Function", "Entity", "File", "Usage",
                              "Tests"]), _frows,
                       widths=(["34px", "2fr", "1.5fr", "1.1fr", "1.2fr"]
                               if entity_col
                               else ["2fr", "0.9fr", "1.5fr", "1.1fr",
                                     "1.2fr"]))

        # Functions candidates — same dialect, function-scoped.
        fcands = ""
        seen_fp: set = set()
        for c in frows_src:
            s = c["sim"]
            if not s or s["j"] < _FN_MERGE_FLOOR:
                continue
            key = tuple(sorted((c["fn"], s["cls"])))
            if key in seen_fp:
                continue
            seen_fp.add(key)
            _ec = f"<td>{_ent_cell(c['entity'])}</td>" if entity_col else ""
            fcands += (f'<tr>{_ec}<td>{itag("t-sim", "merge", "merge candidate")}'
                       f"</td><td><code>{E(key[0])}</code> ≈ "
                       f'<code>{E(key[1])}</code></td>'
                       f'<td>{int(s["j"] * 100)}% identifier twin '
                       f'({s["shared"]}/{s["of"]}) — same job twice, or a '
                       f"justified pattern? Rule it.</td></tr>")
        for c in sorted(frows_src, key=lambda x: -x["lines"]):
            if c["god"]:
                _ec = f"<td>{_ent_cell(c['entity'])}</td>" if entity_col else ""
                fcands += (f'<tr>{_ec}<td>{itag("t-god", "split", "split candidate")}'
                           f'</td><td><code>{E(c["fn"])}</code></td>'
                           f'<td>{c["lines"]} lines — past the '
                           f"{_FN_GOD_LINES}-line function budget; the number "
                           f"names it, judgment rules it.</td></tr>")
        _n_fcands = fcands.count("<tr>")
        html += sechead(
            "Code", "Function candidates", "#b45309", _INS_ICONS["merge"],
            sub="MERGE and SPLIT — named by the machine, ruled by judgment; "
                "same contract as the data-model candidates, function-scoped",
            id_="sec-code-fn-cands",
            note=f"{_n_fcands} candidate(s) this build · each wears the color "
                 f"and icon dialect of the flag that triggered it on the "
                 f"Functions page.",
            info='<div class="leg"><b>What the candidate icons mean</b>'
                 '<ul class="iclist">'
                 f"<li>{itag('t-sim', 'merge', 'merge candidate')} <b>merge</b>"
                 f" — identifier twins ≥ {int(_FN_MERGE_FLOOR * 100)}% (from "
                 f"the {itag('t-sim', 'sim', 'similarity flag')} similarity "
                 "flag).</li>"
                 f"<li>{itag('t-god', 'split', 'split candidate')} <b>split</b>"
                 f" — a god function ≥ {_FN_GOD_LINES} lines (from the "
                 f"{itag('t-god', 'fields', 'length flag', 'N')} length flag)."
                 "</li></ul></div>"
                 '<div class="leg"><b>Why these two, and not "nothing calls '
                 'this"</b> — similarity and length are CORPUS-COMPLETE '
                 "signals: two mapped defs sharing 87% of their body "
                 "identifiers is TRUE regardless of what lies outside the "
                 "map, and a 120-line function is 120 lines however little "
                 "the config covers. \"Nothing references this\" is falsified "
                 "by one file outside the corpus — so this section names "
                 "duplication and size, and never asserts deadness. The usage "
                 "evidence lives on the Functions page — two bars per def, "
                 "api and internal — and a reader checks it there.</div>"
                 '<div class="leg"><b>The floor, stated honestly</b> — the '
                 "similarity flag records the TOP-1 nearest neighbour per "
                 "def, only among defs with ≥ 8 body identifiers, only above "
                 f"the {int(_FN_SIM_FLOOR * 100)}% line, Python only, mapped "
                 f"files only \u2014 while this TABLE cuts higher still, listing "
                 f"pairs at \u2265 {int(_FN_MERGE_FLOOR * 100)}%. Every one of "
                 "those is a way to MISS a pair, "
                 "never a way to invent one. The page is a FLOOR, not a "
                 "census — and that direction is the safe one: under-reporting "
                 "a positive signal costs a missed merge, while under-reporting "
                 "absence gets live code deleted.</div>"
                 '<div class="leg"><b>Known blind spot</b> — files outside '
                 "the entity config are invisible here, and the misses "
                 "cluster there rather than in the maths: two modules can "
                 "share dozens of byte-identical functions and drift apart "
                 "for months without either appearing on this page, if one of "
                 "them is not in the config. An empty candidates table means "
                 "the mapped set is clean, not the repository.</div>")
        if fcands:
            html += (
                "<table class=\"tbl\"><thead><tr>"
                + (f"<th>{th_label(ENT_COL)}</th>" if entity_col else "")
                + "<th>Candidate</th>"
                "<th>Functions</th><th>Why the machine flags it</th></tr>"
                f"</thead><tbody>{fcands}</tbody></table>")
        else:
            html += ('<p class="sub">No function candidates this build — no '
                     "identifier twins past the merge line, no god functions "
                     "in the mapped set.</p>")
    else:
        # The subnav always lists both sections — a pill pointing at a
        # missing anchor is a dead link the crawl gate rightly fails, so an
        # entity with no mapped defs renders both as honest-empty.
        html += sechead(
            "Code", "Functions", "#b45309", _INS_ICONS["fn"],
            sub="every def in this entity's mapped backend files",
            id_="sec-code-fns",
            note="no defs in this entity's mapped backend files this build.")
        html += sechead(
            "Code", "Function candidates", "#b45309", _INS_ICONS["merge"],
            sub="named by the machine, ruled by judgment",
            id_="sec-code-fn-cands",
            note="no defs — no candidates.")

    # ONE generic chips script for every insight table on the pane: each
    # .dmchips filters the .xrow rows between itself and the next section
    # head or chips strip (never a candidates table — those use plain rows).
    html += (
        "<script>(function(){document.querySelectorAll('.dmchips').forEach("
        "function(c){var rows=[];var n=c.nextElementSibling;"
        "while(n&&!(n.classList&&(n.classList.contains('sechead')||"
        "n.classList.contains('dmchips')))){"
        "rows.push.apply(rows,n.querySelectorAll('.xrow'));"
        "n=n.nextElementSibling;}c.addEventListener('click',function(ev){"
        "var b=ev.target.closest('.chip');if(!b)return;"
        "c.querySelectorAll('.chip').forEach(function(x){x.classList.remove('on')});"
        "b.classList.add('on');var f=b.dataset.f;rows.forEach(function(r){"
        "r.classList.toggle('khide',!(f==='all'||r.querySelector('summary .'+f)))});"
        "});c.querySelector('.chip').classList.add('on');});})();</script>")
    # The "About this section" methodology prose used to trail the tables; the
    # declutter ruling folds it into the section's ⊕ (info above) instead.
    return html
