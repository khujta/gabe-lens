#!/usr/bin/env python3
"""_a3_web.py — the web→API bridge extractor (Path A: the frontend arm of the C4 graph).

Reads the app's web source ONCE (read-only glob) and returns, per fetching FILE,
the raw ``(method, path)`` each API-call site names — the FLOOR the bridge matcher
in ``_a3_graph`` joins to the endpoint key-space. graft cannot recover a fetch's
``(method, path)`` (its edges carry no call-site text), so this is a source-reading
arm, SEPARATE from the graft arm with its OWN try/except at the call site: a parser
bug degrades the web arm to honest-empty, never touching graft topology or FK bytes.

PLUGGABLE by design — the API-call idiom differs per app, so one hard-coded pattern
would score ~0% on the next app scanned. Three built-in matchers, auto-selected by
hit-count:
  * ``apiFetch``  — a centralized typed wrapper ``apiFetch<T>(path, {method})`` (gustify)
  * ``axios``     — ``axios.get/post/put/patch/delete(url, …)`` (method from the call name)
  * ``fetch``     — raw ``fetch(url, {method})``
An app with NO REST idiom (tRPC / GraphQL) yields ``present=True, screens=[]`` — an
honest zero, never a crash. A backend-only repo (no ``apps/web/src``) yields
``present=False`` with a named reason.

SSE is handled SEPARATELY from the roster: a streaming endpoint uses a different
primitive (``new EventSource`` / ``fetchEventSource``) that coexists with the primary
idiom, and ``_detect_idiom`` is winner-take-all, so SSE could never win a roster slot.
It runs as an ALWAYS-ON additive pass on every file, merged into that file's calls and
counted in ``stats.sse_sites`` — so a stream enters the coverage denominator instead of
staying invisible. An SSE-only app reports ``extractor="sse"``.

Homing: a web file already listed in an archmap entity's file rows homes by file
(``_file2slug``); a file the archmap does not carry is left ``slug=None`` for
``_a3_graph`` to home by the endpoint its fetch matched (the bridge fallback). The
match itself lives in ``_a3_graph`` (it owns the endpoint ids + the normalization),
so this module stays a pure extractor and returns RAW paths.

Determinism: files are globbed ``sorted(rglob)``; screens + calls sorted; no wallclock.
Battery: tests/arch-graph/run.sh (the web-arm extraction self-test, temp-dir source).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from _a3_graft import _file2slug   # reuse the archmap file→entity homing table

# the conventional web source roots (relative to the repo), tried IN ORDER — the first
# that exists AND holds ts/tsx sources wins. Covers apps/web/src (monorepo), web/src,
# frontend/src, and a bare src/, so the frontend arm is not gustify-layout-specific.
# Absent everywhere → honest-empty.
_WEB_ROOTS = (("apps", "web", "src"), ("web", "src"), ("frontend", "src"),
              ("apps", "frontend", "src"), ("client", "src"), ("src",))
_SKIP_SUFFIXES = (".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx",
                  ".stories.tsx", ".stories.ts", ".d.ts")
_NOISE_PARTS = frozenset({"node_modules", "dist", "build", "storybook-static",
                          "__mocks__", "__tests__"})


def _detect_web_root(root: Path):
    """The first candidate web root that exists AND holds ≥1 non-noise .ts/.tsx — the
    web layer's location is project-specific, so we detect it rather than assume one."""
    for parts in _WEB_ROOTS:
        cand = root.joinpath(*parts)
        if not cand.is_dir():
            continue
        for f in cand.rglob("*.ts*"):
            if f.suffix in (".ts", ".tsx") and not any(p in _NOISE_PARTS for p in f.parts):
                return cand
    return None

# ── the pluggable call-site matchers; group 'path' = the first-arg literal ────
# apiFetch / axios / fetch. axios also captures the method in group 'm'.
_CALL_RES: dict[str, re.Pattern] = {
    "apiFetch": re.compile(
        r"""apiFetch\w*\s*(?:<[^>]*>)?\s*\(\s*[`'"](?P<path>[^`'"]+)[`'"]"""),
    "axios": re.compile(
        r"""axios\s*\.\s*(?P<m>get|post|put|patch|delete)\s*\(\s*[`'"](?P<path>[^`'"]+)[`'"]""",
        re.I),
    "fetch": re.compile(
        r"""(?<![\w.])fetch\s*\(\s*[`'"](?P<path>[^`'"]+)[`'"]"""),
    # AUDIT #5: openapi-fetch — `apiClient.GET("/path")` / `client.POST(...)`. The method is
    # the (UPPERCASE, case-sensitive → distinctive, won't catch Map.get()) property; the path
    # is the first-arg literal. gastify's dominant idiom (70 sites) that the roster missed.
    "openapiFetch": re.compile(
        r"""(?<![\w.])[A-Za-z_$][\w$]*\s*\.\s*(?P<m>GET|POST|PUT|PATCH|DELETE)\s*\(\s*[`'"](?P<path>[^`'"]+)[`'"]"""),
}
# a bare-identifier first arg (apiFetch(path, …)) — a dynamic call site, NAMED not matched.
_CALL_DYN: dict[str, re.Pattern] = {
    "apiFetch": re.compile(r"""apiFetch\w*\s*(?:<[^>]*>)?\s*\(\s*[A-Za-z_$][\w$]*\s*[,)]"""),
    "axios": re.compile(r"""axios\s*\.\s*(?:get|post|put|patch|delete)\s*\(\s*[A-Za-z_$][\w$]*\s*[,)]""", re.I),
    "fetch": re.compile(r"""(?<![\w.])fetch\s*\(\s*[A-Za-z_$][\w$]*\s*[,)]"""),
    "openapiFetch": re.compile(r"""(?<![\w.])[A-Za-z_$][\w$]*\s*\.\s*(?:GET|POST|PUT|PATCH|DELETE)\s*\(\s*[A-Za-z_$][\w$]*\s*[,)]"""),
}
# ── SSE (Server-Sent Events) — an ALWAYS-ON ADDITIVE pass, NOT a roster idiom ──
# A streaming endpoint is opened by a DIFFERENT primitive than a one-shot REST call,
# and it COEXISTS with the app's primary idiom (a chat app still fetches its settings
# over apiFetch). `_detect_idiom` is winner-take-all, so an SSE matcher placed in the
# roster could never win against the dominant REST idiom and its sites would drop. So
# SSE is extracted on EVERY file, in parallel with the winning idiom, and merged in.
# Library-agnostic — keyed on the two STANDARD browser/TS primitives, never a project
# wrapper name:
#   * `new EventSource(<url>)`         — the native API; the spec fixes the method to GET.
#   * `fetchEventSource(<url>, {…})`   — @microsoft/@fortaine fetch-event-source; POST-able,
#                                        so the method rides its options object (default GET).
# A raw `fetch(url,{headers:{Accept:'text/event-stream'}})` is already caught WHEN `fetch`
# is the winning idiom; catching it when it is NOT would need the event-stream marker in
# the call window and risks false positives, so it is a documented non-goal here.
#
# TWO TIERS, because a stream URL is almost never an inline literal — it carries a token /
# query, so real code builds it in a variable (measured across BOTH twins: gustify homes
# the path in `const STREAM_PATH="/api/v1/…"` then `new EventSource(href)`; gastify inlines
# it in a template `const url=\`${API_BASE}/api/v1/…\`` then `new EventSource(url)`):
#   * TIER 1 (precise): the SSE call's first arg IS a literal → exact (method, path).
#   * TIER 2 (floor):   the arg is a VARIABLE (a dynamic SSE site) → the path is indirected,
#     so HARVEST the api-path literals from the file (comments + query strings stripped) and
#     emit each as a GET floor, tagged floor:True. The bridge's endpoint match is the safety
#     net — a harvested non-endpoint path becomes a NAMED-unmatched fetch, never a false edge.
# the name is ANCHORED, not an open `EventSource[A-Za-z]*` — that suffix matched an
# event-sourcing/CQRS class (`new EventSourceStore(…)`, `new EventSourcedAggregate(…)`)
# in a repo with NO Server-Sent Events, minting phantom sites. Accepted forms: the native
# `EventSource`, the common `EventSourcePolyfill`, an optional namespace (`window.EventSource`),
# and fetchEventSource's generic arg (`fetchEventSource<Ev>(…)`).
_SSE_HEAD = r"""new\s+(?:[\w$]+\.)?EventSource(?:Polyfill)?\s*\("""
_FES_HEAD = r"""(?<![\w.])fetchEventSource\s*(?:<[^>]*>)?\s*\("""
_SSE_RES: dict[str, re.Pattern] = {
    "EventSource": re.compile(_SSE_HEAD + r"""\s*[`'"](?P<path>[^`'"]+)[`'"]"""),
    "fetchEventSource": re.compile(_FES_HEAD + r"""\s*[`'"](?P<path>[^`'"]+)[`'"]"""),
}
# a NON-LITERAL first arg (a variable, member access, or call — anything not a quote) is a
# dynamic SSE site → the path is indirected, Tier 2 harvests it. The negative lookahead
# excludes the literal case (Tier 1 owns it) and the empty `()` call.
_SSE_DYN: dict[str, re.Pattern] = {
    "EventSource": re.compile(_SSE_HEAD + r"""\s*(?![`'")])\S"""),
    "fetchEventSource": re.compile(_FES_HEAD + r"""\s*(?![`'")])\S"""),
}
# TIER-2 harvest machinery: strip comments (`:`-guard keeps https://), take every string /
# template literal, and keep the ones shaped like an API path (contains /api/ or /vN/, or a
# rooted multi-segment path). Query + fragment are dropped so ?token=… never defeats the match.
_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)
_LINE_COMMENT_RE = re.compile(r"(?<!:)//[^\n]*")
_STR_LIT_RE = re.compile(r"""[`'"]([^`'"]*)[`'"]""")
_API_PATH_FALLBACK = re.compile(r"^/[A-Za-z][\w-]*(?:/[\w{}$.:-]+)+/?$")


def _strip_comments(text: str) -> str:
    return _LINE_COMMENT_RE.sub("", _BLOCK_COMMENT_RE.sub("", text))


def _looks_api_path(s: str) -> bool:
    """A string literal shaped like an API route — the Tier-2 harvest filter."""
    if "/api/" in s or re.search(r"/v\d+/", s):
        return True
    return bool(_API_PATH_FALLBACK.match(re.sub(r"\$\{[^}]*\}", "", s)))

# the wrapper's OWN definition file (apiFetch is defined here, not called) — its
# internal `path` param calls are not real call sites; skip the file entirely.
_DEF_RE = re.compile(r"""(?:export\s+)?(?:async\s+)?function\s+apiFetch|const\s+apiFetch\s*=""")
# method rides the options object: apiFetch(path, { method: "PATCH", body }) — a
# token scan (not object parse) so a nested body:{…} never defeats it. Default GET.
_METHOD_RE = re.compile(r"""method\s*:\s*[`'"](?P<m>GET|POST|PUT|PATCH|DELETE)""", re.I)


def _iter_sources(web_root: Path) -> list[Path]:
    """Every non-noise .ts/.tsx under the web root, deterministically ordered."""
    out: list[Path] = []
    for f in sorted(web_root.rglob("*.ts")) + sorted(web_root.rglob("*.tsx")):
        name = f.name
        if any(name.endswith(sfx) for sfx in _SKIP_SUFFIXES):
            continue
        if any(part in _NOISE_PARTS for part in f.parts):
            continue
        out.append(f)
    return sorted(out)


def _method_after(text: str, call_start: int) -> str:
    """Two-stage method read: scan the call's balanced-paren window for a
    `method:` token (survives a nested body:{…}); default GET."""
    depth = 0
    i = call_start
    n = len(text)
    # advance to the opening '(' of this call
    while i < n and text[i] != "(":
        i += 1
    start = i
    while i < n:
        c = text[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                break
        i += 1
    window = text[start:i + 1]
    m = _METHOD_RE.search(window)
    return m.group("m").upper() if m else "GET"


def _detect_idiom(texts: list[str]) -> tuple[str | None, dict[str, int]]:
    """Pick the dominant API-call idiom by literal-call hit-count across the tree."""
    counts = {name: sum(len(rx.findall(t)) for t in texts)
              for name, rx in _CALL_RES.items()}
    best = max(sorted(counts), key=lambda k: counts[k])   # sorted → deterministic tie-break
    return (best if counts[best] > 0 else None), counts


_DECL_RE = re.compile(r"""^(?:export\s+(?:default\s+)?)?(?:async\s+)?(?:function\s*\*?\s*(?P<f>[A-Za-z_$][\w$]*)|(?:const|let|var)\s+(?P<v>[A-Za-z_$][\w$]*)\s*[=:]|class\s+(?P<c>[A-Za-z_$][\w$]*))""", re.M)


def _decl_starts(text: str) -> list[tuple[int, str]]:
    """``[(offset, name)]`` of every COLUMN-0 declaration — the file's top-level exports, consts and
    classes in source order (formatted TypeScript keeps top-level declarations at column 0)."""
    return [(m.start(), m.group("f") or m.group("v") or m.group("c")) for m in _DECL_RE.finditer(text)]


def _enclosing_export(decls: list[tuple[int, str]], text: str, pos: int) -> str | None:
    """The top-level declaration a call site sits INSIDE — D3 (operator 2026-09-05): the bridge lands on
    the hook that fetched, not on its file. Rule: the nearest column-0 declaration ABOVE the call, provided
    the call's own line is indented (a call on a column-0 line is module-level → None). A FLOOR by design —
    no brace matching, so a call inside a nested block is still attributed to the enclosing top-level
    declaration; the right file and the right export, never a guess across files."""
    ls = text.rfind("\n", 0, pos) + 1
    if ls >= len(text) or text[ls] not in " \t":
        # a column-0 line: module-level — UNLESS the line itself opens a declaration (a one-line
        # `export function useA(){ return apiFetch(…) }` keeps the call on its own declaration line)
        for off, nm in decls:
            if off == ls:
                return nm
        return None
    name = None
    for off, nm in decls:
        if off <= pos:
            name = nm
        else:
            break
    return name


def _extract_file(text: str, idiom: str) -> tuple[list[dict[str, str]], int]:
    """Return this file's (method, path) call sites (+ the enclosing ``export``, D3) + the dynamic-path
    site count."""
    calls: list[dict[str, str]] = []
    rx = _CALL_RES[idiom]
    decls = _decl_starts(text)
    for m in rx.finditer(text):
        path = m.group("path")
        if idiom in ("axios", "openapiFetch"):   # method rides the call itself (group m)
            method = m.group("m").upper()
        else:
            method = _method_after(text, m.start())
        c: dict[str, str] = {"method": method, "path": path}
        exp = _enclosing_export(decls, text, m.start())
        if exp:
            c["export"] = exp
        calls.append(c)
    dyn = len(_CALL_DYN[idiom].findall(text))
    # de-dup + sort for determinism
    seen: set[tuple[str, str]] = set()
    uniq: list[dict[str, str]] = []
    for c in sorted(calls, key=lambda c: (c["method"], c["path"], c.get("export") or "")):   # same (method, path) from two exports → the sorted-first export wins, deterministically
        key = (c["method"], c["path"])
        if key not in seen:
            seen.add(key)
            uniq.append(c)
    return uniq, dyn


def _extract_sse(text: str) -> tuple[list[dict[str, str]], int, list[dict[str, str]]]:
    """Return ``(literal_calls, dynamic_count, floor_calls)`` for this file.

    Tier 1 ``literal_calls``: `new EventSource("/x")` / `fetchEventSource("/x", …)` — a
    precise (method, path). EventSource is GET by spec; fetchEventSource may POST, so its
    method is read from the options object (default GET). Each is tagged ``sse: True``.

    Tier 2 ``floor_calls`` (only when a DYNAMIC SSE call exists): the stream URL is built
    in a variable, so harvest the file's api-path literals as GET floors, tagged
    ``sse: True, floor: True``. The bridge match filters non-endpoints to named-unmatched.

    The bridge reads only method+path, so the extra tags ride harmlessly."""
    text = _strip_comments(text)               # a commented-out `new EventSource("…")` is not a site
    calls: list[dict[str, str]] = []
    decls = _decl_starts(text)
    for name, rx in _SSE_RES.items():
        for m in rx.finditer(text):
            method = "GET" if name == "EventSource" else _method_after(text, m.start())
            c: dict[str, str] = {"method": method, "path": m.group("path"), "sse": True}
            exp = _enclosing_export(decls, text, m.start())
            if exp:
                c["export"] = exp                  # D3: the stream's hook, not its file
            calls.append(c)
    dyn = sum(len(rx.findall(text)) for rx in _SSE_DYN.values())
    floors: list[dict[str, str]] = []
    if dyn:                                    # a variable arg → recover the indirected path
        seen: set[str] = set()
        for m in _STR_LIT_RE.finditer(text):
            path = m.group(1).split("?", 1)[0].split("#", 1)[0]   # drop query + fragment
            if path not in seen and _looks_api_path(path):
                seen.add(path)
                floors.append({"method": "GET", "path": path, "sse": True, "floor": True})
    return calls, dyn, floors


def _rel(f: Path, root: Path) -> str:
    """Repo-relative posix path — the key _file2slug and the archmap file rows use."""
    try:
        return f.relative_to(root).as_posix()
    except ValueError:
        return f.as_posix()


def web_arm(root: Path, entities: dict[str, Any]) -> dict[str, Any]:
    """The whole web arm, one call: glob → detect idiom → extract call sites →
    home by file. NEVER raises inside (the caller still wraps it — defence in
    depth); any failure returns ``{present: False, reason}``.

    Returns ``{present, reason, extractor, screens, stats}`` where each screen is
    one fetching FILE collapsed to a single node (id ``web:<relpath-no-suffix>``),
    carrying its raw ``calls`` for _a3_graph to match. ``present=False`` carries only
    the reason and the caller's FK+graft graph stays byte-identical.
    """
    try:
        root = Path(root)
        web_root = _detect_web_root(root)
        if web_root is None:
            return {"present": False,
                    "reason": "no web source (tried " + ", ".join("/".join(p) for p in _WEB_ROOTS) + ")"}
        files = _iter_sources(web_root)
        # read every candidate once; drop the wrapper's own definition file
        texts: list[tuple[Path, str]] = []
        for f in files:
            try:
                src = f.read_text(errors="ignore")
            except OSError:
                continue
            if _DEF_RE.search(src):
                continue                       # the apiFetch definition, not a caller
            texts.append((f, src))
        idiom, counts = _detect_idiom([t for _, t in texts])
        f2s = _file2slug(entities)
        screens: list[dict[str, Any]] = []
        total_sites = total_dyn = total_sse = total_floor = 0
        total_export = 0                                # D3: call sites attributed to their enclosing export
        for f, src in texts:
            # the winning REST idiom (byte-identical when no SSE joins) + the always-on
            # SSE pass, MERGED and re-deduped by (method, path). A no-SSE file's `calls`
            # stay exactly the idiom output — only an SSE-bearing file changes.
            calls, dyn = _extract_file(src, idiom) if idiom else ([], 0)
            scalls, sdyn, sfloors = _extract_sse(src)
            dyn += sdyn                          # ALWAYS count SSE dynamics — a dynamic-only stream
                                                 # file with no harvestable literal must not vanish
            if scalls or sfloors:
                merged: dict[tuple[str, str], dict[str, str]] = {
                    (c["method"], c["path"]): c for c in calls}
                for c in scalls:
                    merged.setdefault((c["method"], c["path"]), c)   # Tier-1 precise SSE
                precise_paths = {c["path"] for c in merged.values()}  # any-method claim on a path
                for c in sfloors:                                     # Tier-2 floor — only unclaimed paths
                    if c["path"] not in precise_paths:
                        merged.setdefault((c["method"], c["path"]), c)
                calls = sorted(merged.values(), key=lambda c: (c["method"], c["path"]))
            if not calls and not dyn:
                continue
            rel = _rel(f, root)
            screens.append({
                "id": "web:" + re.sub(r"\.(ts|tsx)$", "", rel),
                "file": rel,
                "slug": f2s.get(rel),          # file-homed; None → _a3_graph endpoint-homes
                "label": re.sub(r"\.(ts|tsx)$", "", f.name),
                "calls": calls,
                "dynamic": dyn,
            })
            total_sites += len(calls)
            total_dyn += dyn
            total_sse += sum(1 for c in calls if c.get("sse"))
            total_export += sum(1 for c in calls if c.get("export"))
            total_floor += sum(1 for c in calls if c.get("floor"))
        # no REST idiom AND no SSE anywhere → the honest 'nothing to extract' record
        # (byte-identical to the pre-SSE build; `idiom_hits` kept for the debug trail).
        if idiom is None and total_sse == 0:
            return {"present": True, "reason": "no REST api-call idiom detected",
                    "extractor": None, "screens": [],
                    "stats": {"screens": 0, "fetch_sites": 0, "dynamic": 0,
                              "sse_sites": 0, "sse_floor": 0, "extractor": None, "idiom_hits": counts}}
        screens.sort(key=lambda s: s["id"])
        extractor = idiom or "sse"    # SSE-only app → the extractor IS sse
        reason = (f"{idiom} · {len(screens)} fetching files" if idiom
                  else f"sse · {len(screens)} fetching files")
        return {
            "present": True, "reason": reason,
            "extractor": extractor, "screens": screens,
            "stats": {"screens": len(screens), "fetch_sites": total_sites,
                      "dynamic": total_dyn, "sse_sites": total_sse, "sites_with_export": total_export, "sse_floor": total_floor,
                      "extractor": extractor},
        }
    except Exception as exc:   # noqa: BLE001 — the arm enhances, never breaks, the build
        return {"present": False, "reason": f"web arm error: {exc}"}
