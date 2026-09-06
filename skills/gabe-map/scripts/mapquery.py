#!/usr/bin/env python3
"""mapquery — the pure query library behind the gabe-map MCP server (and reach-emit.py).

READ-ONLY over a project's committed command-center map (docs/site/center/{center.config,
archmap,c4-graph,adoption}.json) plus git; the ONE write is the map-delta emit inside
`two_arm` (through gabe-commit's validated writer, `map-deltas.py append --once`), behind
five gates: (a) a map claim exists (graft resolved the symbol), (b) the grep hit is code, not
prose, (c) `--once` (no identical un-swept line), (d) the accumulator path is gitignored,
(e) the root is inside the session's roots. No stdout anywhere in this module — the server's
fd 1 is the JSON-RPC wire; diagnostics go to stderr via `log()`.

Honest-empty by construction: every lookup is `.get(...) or {}`; a missing block yields an
empty section with a `reason`; no center → `present: False` with the path that was looked for.
Design record: docs/design/gabe-map/README.md (D4 root · D5 honest-empty · D6 emit · D8 fresh).
"""
from __future__ import annotations
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tokenize
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS_DIR = Path(os.environ.get("GABE_SKILLS_DIR", HERE.parent.parent))   # ~/.claude/skills or repo skills/
MAP_DELTAS = SKILLS_DIR / "gabe-commit" / "scripts" / "map-deltas.py"
ENTITY_CONTEXT = SKILLS_DIR / "gabe-cc-entity" / "scripts" / "entity-context.py"
PULSE_SCRIPTS = SKILLS_DIR / "gabe-pulse" / "scripts"
CENTER_REL = "docs/site/center"
SUITE_CENTER_REL = "docs/center/suite-center.config.json"
LIVE_REL = ".kdbp/map-deltas.jsonl"
CAP = 40            # default list cap — every capped list NAMES its cap (D11)
REACH_CAP = 20      # per-symbol delta cap (reach-emit's, kept)
SRC_EXT = (".py", ".ts", ".tsx", ".js", ".jsx", ".mjs")
SYMBOL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,127}$")
_EXCL_DIR = re.compile(
    r'(^|/)(node_modules|dist|build|storybook-static|_archive|\.venv|venv|'
    r'__pycache__|coverage|\.next|site-packages)/|(^|/)docs/site/center/|(^|/)docs/center/')
_EXCL_BASE = re.compile(r'(\.min\.(js|css)|\.bundle\.js|-[A-Za-z0-9]{6,}\.js|\.data\.js|c4-graph.*\.js|levels\.js)$')


def log(msg: str) -> None:
    if os.environ.get("GABE_MAP_LOG"):
        sys.stderr.write("gabe-map: %s\n" % msg)


class MapStop(Exception):
    """A named, honest stop (no center · unknown slug · bad input) — never a crash."""


# ── shell (list args only, never a shell string) ──────────────────────────────
def sh(args: list[str], cwd: str | Path | None = None, timeout: int = 60,
       env: dict | None = None) -> tuple[int, str, str]:
    """env overlays os.environ (None = inherit unchanged)."""
    try:
        _env = {**os.environ, **env} if env else None
        r = subprocess.run(args, capture_output=True, text=True, cwd=str(cwd) if cwd else None,
                           timeout=timeout, stdin=subprocess.DEVNULL, env=_env)
        return r.returncode, r.stdout, r.stderr
    except FileNotFoundError as exc:
        return 127, "", str(exc)
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except OSError as exc:
        return 126, "", str(exc)


def git_toplevel(path: str | Path) -> str | None:
    rc, out, _ = sh(["git", "-C", str(path), "rev-parse", "--show-toplevel"])
    return out.strip() if rc == 0 and out.strip() else None


# ── root + center resolution (D4, amended: root := git toplevel) ─────────────
def resolve_root(explicit: str | None = None, roots: list[str] | None = None,
                 cwd: str | None = None) -> tuple[str, str]:
    """→ (root, source). Order: explicit arg → CLAUDE_PROJECT_DIR → roots[0] → cwd; then the git
    toplevel of that directory when it is inside a repo (a subdirectory cwd must not narrow grep)."""
    cand, source = None, ""
    if explicit:
        cand, source = explicit, "arg"
    elif os.environ.get("CLAUDE_PROJECT_DIR"):
        cand, source = os.environ["CLAUDE_PROJECT_DIR"], "CLAUDE_PROJECT_DIR"
    elif roots:
        cand, source = roots[0], "roots/list"
    else:
        cand, source = cwd or os.getcwd(), "cwd"
    cand = os.path.abspath(os.path.expanduser(cand))
    top = git_toplevel(cand) if os.path.isdir(cand) else None
    return (top or cand), source


def find_center(root: str) -> tuple[Path | None, str]:
    """Walk UP from root for docs/site/center/center.config.json. → (center_dir, reason)."""
    base = Path(root)
    for d in (base, *base.parents):
        c = d / CENTER_REL
        if (c / "center.config.json").is_file():
            return c, "found"
    if (base / SUITE_CENTER_REL).is_file():
        return None, "suite center (beat spine) — no codebase map by ruling R8"
    return None, "no command center under %s (looked for %s/center.config.json up from it)" % (root, CENTER_REL)


def project_root_of(center: Path) -> str:
    """The project root the center belongs to (center = <root>/docs/site/center)."""
    return str(center.parent.parent.parent)


# ── loaders with (path, mtime, size) cache + indexes built once per load (D13) ─
_CACHE: dict[str, tuple[tuple, dict]] = {}


def _load_json(path: Path) -> dict:
    try:
        st = path.stat()
    except FileNotFoundError:
        return {}
    key = (str(path), st.st_mtime_ns, st.st_size)
    hit = _CACHE.get(str(path))
    if hit and hit[0] == key:
        return hit[1]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        log("unreadable %s: %s" % (path, exc))
        data = {}
    if not isinstance(data, dict):
        data = {}
    _CACHE[str(path)] = (key, data)
    return data


class Center:
    """One project's committed map, loaded lazily, indexed once per load."""

    def __init__(self, center: Path):
        self.dir = center
        self.root = project_root_of(center)
        self._idx_key = None
        self._idx: dict = {}
        self._fnidx_key = None      # P0 (2026-09-06): the levels.json fn_edges index — built only when a tool asks
        self._fnidx: dict = {}

    @property
    def config(self) -> dict: return _load_json(self.dir / "center.config.json")
    @property
    def archmap(self) -> dict: return _load_json(self.dir / "archmap.json")
    @property
    def c4(self) -> dict: return _load_json(self.dir / "c4-graph.json")
    @property
    def adoption(self) -> dict: return _load_json(self.dir / "adoption.json")
    @property
    def levels(self) -> dict: return _load_json(self.dir / "levels.json")   # P0: lazy — trace · blast_radius · touches(task) read it; map_status never does

    def entities(self) -> dict:
        return (self.archmap.get("entities") or {})

    def idx(self) -> dict:
        """Inverse indexes; rebuilt when archmap/c4 change on disk."""
        key = tuple(_CACHE.get(str(self.dir / n), ((),))[0] for n in ("archmap.json", "c4-graph.json"))
        _ = self.archmap, self.c4
        key = tuple(_CACHE.get(str(self.dir / n), ((),))[0] for n in ("archmap.json", "c4-graph.json"))
        if self._idx_key == key and self._idx:
            return self._idx
        a, c = self.archmap, self.c4
        fi = a.get("function_insight") or {}
        mi = a.get("model_insight") or {}
        idx = {"fn_by_bare": {}, "fn_by_file": {}, "cls": {}, "table2model": {}, "model_fns": {},
               "file_owners": {}, "defines": {}, "c4_nodes": {}, "edges_in": {}, "edges_out": {},
               "web_by_stem": {}, "mapped_files": set(), "handler_of": {},
               "task_by_name": {}, "task_by_fn": {}}   # P1: TASK roots by REGISTERED name and by fn name → {root, nid, slug, fnkey}
        for k, rec in fi.items():
            if "::" not in k:
                continue
            f, qual = k.split("::", 1)
            bare = qual.split(".")[-1]
            idx["fn_by_bare"].setdefault(bare, []).append(k)
            idx["fn_by_file"].setdefault(f, []).append(k)
            for op in ((rec.get("access") or {}).get("ops") or []):
                if op.get("model"):
                    idx["model_fns"].setdefault(op["model"], []).append((k, op.get("rw", "?")))
        for cls, rec in mi.items():
            idx["cls"][cls] = (rec.get("entity"), rec.get("kind"), rec.get("file"))
        for slug, ent in (a.get("entities") or {}).items():
            for row in (ent.get("files") or []):
                if len(row) >= 2:
                    idx["file_owners"].setdefault(row[1], []).append((slug, row[0], row[2] if len(row) > 2 else None))
                    idx["mapped_files"].add(row[1])
            for path, names in (ent.get("defines") or {}).items():
                for n in names:
                    idx["defines"].setdefault(n.rstrip("()"), []).append((slug, path))
            for m in (ent.get("models") or []):
                if m.get("table"):
                    idx["table2model"][m["table"]] = (m.get("cls"), slug)
            for ep in (ent.get("endpoints") or []):
                if ep.get("file") and ep.get("fn"):
                    idx["handler_of"]["%s::%s" % (ep["file"], ep["fn"])] = (slug, ep.get("method"), ep.get("path"))
        for slug, l2 in (c.get("l2") or {}).items():
            for n in (l2.get("nodes") or []):
                if n.get("id"):
                    idx["c4_nodes"][(slug, n["id"])] = n
                    if n.get("kind") == "web":
                        idx["web_by_stem"][n["id"].split("web:", 1)[-1]] = (slug, n)
            for e in (l2.get("edges") or []):
                s, t = e.get("source"), e.get("target")
                if s and t:
                    idx["edges_in"].setdefault(t, []).append((s, e.get("kind") or "fk", slug))
                    idx["edges_out"].setdefault(s, []).append((t, e.get("kind") or "fk", slug))
        for e in (c.get("cross_edges") or []):
            s, t = e.get("from") or e.get("source"), e.get("to") or e.get("target")
            if s and t:
                kind = e.get("kind") or ("fk" if "via" in e else "edge")
                idx["edges_in"].setdefault(t, []).append((s, kind, e.get("from_slug") or "cross"))
                idx["edges_out"].setdefault(s, []).append((t, kind, e.get("to_slug") or "cross"))
        for p in (c.get("fe") or {}).get("pieces") or []:
            if isinstance(p, dict) and p.get("file"):
                idx["mapped_files"].add(p["file"])
        # P1 (2026-09-06): a worker task is addressable by the name it is REGISTERED under (task_roots[].path, e.g.
        # cleanup_idle_sandboxes) and by its function (task_roots[].fn, cleanup_idle_sandboxes_task); the c4 node is
        # endpoint:TASK <name>, the levels.json edge key is file#fn.
        nid_slug = {nid: slug for (slug, nid) in idx["c4_nodes"]}
        for root in (a.get("task_roots") or []):
            name, fn, f = root.get("path"), root.get("fn"), root.get("file")
            if not name:
                continue
            nid = "endpoint:TASK %s" % name
            rec = {"root": root, "nid": nid, "slug": nid_slug.get(nid), "fnkey": ("%s#%s" % (f, fn)) if (f and fn) else None}
            idx["task_by_name"][name] = rec
            if fn:
                idx["task_by_fn"].setdefault(fn, rec)
        self._idx, self._idx_key = idx, key
        return idx

    def fn_index(self) -> dict:
        """P0 — levels.json `fn_edges` as out/in adjacency keyed on `file#fn` (rel + conf carried per edge).
        Built once per Center on first use, rebuilt when the file changes; `present` False when there is no levels.json."""
        lv = self.levels
        key = _CACHE.get(str(self.dir / "levels.json"), ((),))[0]
        if self._fnidx_key == key and self._fnidx:
            return self._fnidx
        out = {"present": bool(lv), "edges": 0, "fn_out": {}, "fn_in": {}, "by_rel": {}}
        for e in (lv.get("fn_edges") or []) if isinstance(lv, dict) else []:
            s_, t_ = e.get("s"), e.get("t")
            if not (s_ and t_):
                continue
            rel, conf = e.get("rel") or "?", e.get("conf") or "?"
            out["fn_out"].setdefault(s_, []).append((t_, rel, conf))
            out["fn_in"].setdefault(t_, []).append((s_, rel, conf))
            out["by_rel"][rel] = out["by_rel"].get(rel, 0) + 1
            out["edges"] += 1
        self._fnidx, self._fnidx_key = out, key
        return out


HEALTH_STATES = ("present = the pass ran and found something · clean = the pass ran (the repo-study sentinel route_mounts is on the map) "
                 "and found nothing · not_emitted = an older map that never ran the pass — regen to know")


def health_key(a: dict, key: str) -> tuple:
    """P2 — absence semantics for the omitted-when-empty archmap keys (unparseable · fn_similarity · route_mounts · tasks …):
    (value, state) with state ∈ present | clean | not_emitted. The sentinel: `route_mounts` is written by every map the
    repo-study generators produced (2026-09-06), so its presence proves the pass ran; without it absence means an older map."""
    if key in a and a.get(key) not in (None, {}, []):
        return a[key], "present"
    return None, ("clean" if "route_mounts" in a else "not_emitted")


def map_health(a: dict, c: dict) -> dict:
    """Where the map is PARTIAL, in one object — read by map_status (one line), map_census (sections) and center_overview.
    Every fact already on the archmap/c4; nothing scanned. Each block carries its P2 state word."""
    rm, rm_s = health_key(a, "route_mounts")
    up, up_s = health_key(a, "unparseable")
    fs, fs_s = health_key(a, "fn_similarity")
    tk, tk_s = health_key(a, "tasks")
    st = c.get("stats") or {}
    web = st.get("web") or {}
    ents = a.get("entities") or {}
    n_ep = sum(len(e.get("endpoints") or []) for e in ents.values())
    n_sch = sum(len(e.get("schemas") or []) for e in ents.values())
    out = {"route_mounts": ({"state": rm_s, "mounted": rm.get("mounted"), "routers": rm.get("routers"), "unresolved": len(rm.get("unresolved") or [])}
                            if rm else {"state": rm_s}),
           "unparseable": {"state": up_s, "count": len(up) if up else 0},
           "fn_similarity": ({"state": fs_s, "mode": fs.get("mode"), "sizable": fs.get("sizable"), "budget": fs.get("budget"), "pairs": fs.get("pairs")}
                             if fs else {"state": fs_s, "mode": "exact" if fs_s == "clean" else None}),
           "tasks_unresolved": (list(((tk or {}).get("stats") or {}).get("unresolved") or []) if tk else []),
           "tasks_state": tk_s,
           "web": ({"extractor": web.get("extractor"), "other_roots": list(web.get("other_roots") or []), "unhomed": web.get("unhomed") or 0,
                    "unmatched": (len(web["unmatched"]) if isinstance(web.get("unmatched"), list) else (web.get("unmatched") or 0))}
                   if web.get("present") else {"present": False, "reason": web.get("reason") or "no web arm on this map"}),
           "schemas_zero": ("the schema arm extracted nothing across %d endpoint(s) — an EMPTY arm, not a clean one" % n_ep) if (n_ep and not n_sch) else False,
           "states": HEALTH_STATES}
    return out


def open_center(root: str) -> tuple[Center | None, str]:
    c, reason = find_center(root)
    return (Center(c) if c else None), reason


# ── freshness (D8, amended: regen-parent base · worktree-aware · tristate) ─────
def freshness(center: Center) -> dict:
    a = center.archmap
    head = a.get("head") or ""
    root = center.root
    out = {"head": head, "generated": a.get("generated"), "commits_since": None, "base": None,
           "mapped_files_changed": [], "mapped_files_changed_more": 0, "stale": None, "freshness": "unknown", "reason": ""}
    if not head:
        out["reason"] = "archmap carries no head"
        return out
    rc, _, _ = sh(["git", "-C", root, "cat-file", "-e", head + "^{commit}"])
    if rc != 0:
        out["reason"] = "head %s not in this repository's history" % head
        return out
    # base = the last commit that touched archmap.json when it descends from head (the regen
    # commit bundles source changes the map already reflects), else head itself
    base = head
    rc, out_log, _ = sh(["git", "-C", root, "log", "-1", "--format=%h", "--", CENTER_REL + "/archmap.json"])
    cand = out_log.strip()
    if rc == 0 and cand:
        rc2, _, _ = sh(["git", "-C", root, "merge-base", "--is-ancestor", head, cand])
        if rc2 == 0:
            base = cand
    out["base"] = base
    rc, cnt, _ = sh(["git", "-C", root, "rev-list", "--count", "%s..HEAD" % head])
    out["commits_since"] = int(cnt.strip()) if rc == 0 and cnt.strip().isdigit() else None
    changed: set[str] = set()
    rc, diff, _ = sh(["git", "-C", root, "diff", "--name-only", "--end-of-options", base])   # index+worktree vs base (base is server-derived; guarded defensively)
    if rc == 0:
        changed.update(l.strip() for l in diff.splitlines() if l.strip())
    rc, st, _ = sh(["git", "-C", root, "status", "--porcelain", "--untracked-files=all"])
    if rc == 0:
        for l in st.splitlines():
            if l.startswith("??"):
                changed.add(l[3:].strip())
    mapped = center.idx()["mapped_files"]
    hit = sorted(p for p in changed if p in mapped and p.endswith(SRC_EXT))
    out["mapped_files_changed"], out["mapped_files_changed_more"] = hit[:CAP], max(0, len(hit) - CAP)
    dirty_map = any(l.strip().endswith("archmap.json") for l in diff.splitlines()) if rc == 0 else False
    if dirty_map:
        out["stale"], out["freshness"], out["reason"] = None, "uncommitted regen", "archmap.json is modified in the worktree"
    elif hit:
        out["stale"], out["freshness"] = True, "stale"
        out["reason"] = "%d mapped source file(s) changed since the map's base %s" % (len(hit), base)
    else:
        out["stale"], out["freshness"] = False, "fresh"
        out["reason"] = "no mapped source file changed since %s" % base
    return out


def stamp(center: Center) -> dict:
    f = freshness(center)
    return {"map": "map@%s · %s" % (f.get("head") or "?", f.get("freshness")), "freshness": f}


# ── the two-arm reach core (shared by who_calls and reach-emit.py) ────────────
def noise(p: str) -> bool:
    return bool(_EXCL_DIR.search(p)) or bool(_EXCL_BASE.search(os.path.basename(p))) or not p.endswith(SRC_EXT)


def parse_callers(callers_json: str | None) -> tuple[set, set, list, str]:
    """→ (caller_files, def_files, hits[{path,symbol,span}], claim). claim ∈ present | absent:<why>."""
    callers, defs, hits = set(), set(), []
    if not callers_json:
        return callers, defs, hits, "absent: callers arm did not run"
    try:
        data = json.loads(callers_json)
    except Exception:
        return callers, defs, hits, "absent: callers arm returned unparseable output"
    matches = data.get("matches") or [] if isinstance(data, dict) else []
    if not matches:
        return callers, defs, hits, "absent: symbol not in the graft index"
    for m in matches:
        symp = (m.get("symbol") or {}).get("path")
        if symp:
            defs.add(symp)
        for h in (m.get("hits") or []):
            if h.get("path"):
                callers.add(h["path"])
                hits.append({"path": h["path"], "symbol": h.get("id") or h.get("name"), "span": h.get("span")})
    return callers, defs, hits, "present"


def graft_callers(sym: str, root: str, direction: str = "in", depth: str = "1") -> tuple[str | None, str]:
    """Arm A. → (json_text|None, status). Never a build/refresh (D10): --json --no-refresh only.
    direction=out gives callees; depth N|all walks transitively (graft's own blast radius)."""
    if not os.path.isdir(os.path.join(root, "graft")):
        return None, "no index (no graft/ dir)"
    args = ["graft", "callers", sym, ".", "--json", "--no-refresh"]
    if direction != "in":
        args += ["--direction", direction]
    if str(depth) != "1":
        args += ["--depth", str(depth)]
    rc, out, err = sh(args, cwd=root, timeout=120)
    if rc == 127:
        return None, "unavailable: graft binary not found"
    if rc != 0:
        return None, "unavailable: graft exit %d %s" % (rc, (err or out).strip().splitlines()[:1])
    return out, "ran"


def git_grep_hits(sym: str, root: str) -> tuple[list[dict], str]:
    """Arm B. `git grep -nwI --untracked` scoped to source globs, center dirs excluded. → (hits, status)."""
    if not SYMBOL_RE.match(sym):
        return [], "unavailable: symbol is not an identifier"
    args = ["git", "-C", root, "grep", "-nwI", "--untracked", "--full-name", "-e", sym, "--",
            *[":(glob)**/*" + e for e in SRC_EXT],
            ":(exclude)docs/site/center", ":(exclude)docs/center", ":(exclude)**/node_modules/**",
            ":(exclude)**/dist/**", ":(exclude)**/*.min.js"]
    rc, out, err = sh(args, timeout=60)
    if rc == 1:
        return [], "ran (no matches)"
    if rc != 0:
        return [], "unavailable: git grep exit %d %s" % (rc, err.strip().splitlines()[:1])
    hits = []
    for line in out.splitlines():
        parts = line.split(":", 2)
        if len(parts) == 3 and parts[1].isdigit():
            hits.append({"path": parts[0], "line": int(parts[1]), "text": parts[2]})
    return hits, "ran"


_PROSE_LINE = re.compile(r'^\s*(#|//|/\*|\*|"""|\'\'\')')


def classify_hit(root: str, path: str, line: int, text: str, sym: str = "") -> str:
    """'code' | 'prose' for THE SYMBOL'S OCCURRENCE on that line. Python files: exact via tokenize — the
    hit is prose only when every occurrence of the symbol on the line sits inside a COMMENT/STRING token
    (a call with a string argument on the same line stays code). Other files: a line-shape heuristic."""
    full = os.path.join(root, path)
    text = text or ""
    if path.endswith(".py") and os.path.isfile(full):
        try:
            with open(full, "rb") as fh:
                src = fh.read()
            spans = [(t.start, t.end) for t in tokenize.tokenize(io.BytesIO(src).readline)
                     if t.type in (tokenize.COMMENT, tokenize.STRING) and t.start[0] <= line <= t.end[0]]
            src_line = src.decode("utf-8", "replace").splitlines()[line - 1] if 0 < line <= len(src.splitlines()) else text
            cols = [m.start() for m in re.finditer(r"(?<![A-Za-z0-9_])%s(?![A-Za-z0-9_])" % re.escape(sym), src_line)] if sym else []
            if not cols:
                return "prose" if spans and not _has_code(src_line) else "code"
            for c in cols:
                inside = any((s_[0] < line or (s_[0] == line and s_[1] <= c)) and (e_[0] > line or (e_[0] == line and e_[1] > c))
                             for s_, e_ in spans)
                if not inside:
                    return "code"
            return "prose"
        except (tokenize.TokenError, SyntaxError, OSError, IndexError, UnicodeDecodeError):
            pass
    return "prose" if _PROSE_LINE.match(text) else "code"


def _has_code(src_line: str) -> bool:
    return not _PROSE_LINE.match(src_line or "")


def _live_ignored(root: str) -> bool:
    rc, _, _ = sh(["git", "-C", root, "check-ignore", "-q", LIVE_REL])
    return rc == 0


def emit_delta(root: str, sym: str, path: str, line: int, cmd: str) -> bool:
    """One delta through the validated writer with --once. → True when a line was actually written."""
    live = os.path.join(root, LIVE_REL)
    before = sum(1 for _ in open(live)) if os.path.exists(live) else 0
    found = "%s:%s" % (path, line)
    rc, _, err = sh([sys.executable, str(MAP_DELTAS), "append", "--once", "--type", "add", "--gen", "_a3_graft.calls",
                     "--cmd", cmd, "--subject", "callers(%s)" % sym, "--found", found, "--pointer", found], cwd=root)
    if rc != 0:
        log("append failed: %s" % err.strip())
        return False
    after = sum(1 for _ in open(live)) if os.path.exists(live) else 0
    return after > before


def two_arm(sym: str, root: str, callers_json: str | None, callers_status: str,
            grep_hits: list[dict], grep_status: str, *, emit: bool = True, cmd: str = "mcp",
            dry: bool = False, allowed_roots: list[str] | None = None, cap: int = REACH_CAP) -> dict:
    """The shared reach: union both arms, classify, gate the emit five ways, report every gate."""
    callers, defs, chits, claim = parse_callers(callers_json)
    if callers_status != "ran" and claim == "present":
        claim = "absent: " + callers_status
    elif callers_status != "ran":
        claim = "absent: " + callers_status
    by_file: dict[str, dict] = {}
    for h in grep_hits:
        p = h.get("path")
        if not p or noise(p):
            continue
        shape = classify_hit(root, p, int(h.get("line") or 0), h.get("text") or "", sym)
        cur = by_file.get(p)
        if cur is None:
            by_file[p] = {"path": p, "line": h.get("line", 0), "text": (h.get("text") or "").strip()[:160],
                          "shape": shape, "hits": 1, "code_hits": int(shape == "code")}
            continue
        cur["hits"] += 1
        cur["code_hits"] += int(shape == "code")
        if shape == "code" and cur["shape"] == "prose":      # a file is CODE if ANY hit on it is code
            cur.update({"line": h.get("line", 0), "text": (h.get("text") or "").strip()[:160], "shape": "code"})
    code_files = sorted(p for p, h in by_file.items() if h["shape"] == "code")
    prose_files = sorted(p for p, h in by_file.items() if h["shape"] == "prose")
    reach = sorted(f for f in (callers | defs | set(code_files)) if not noise(f))
    missed = [p for p in code_files if p not in callers and p not in defs]
    gates = {"claim": claim, "emit_requested": bool(emit), "dry_run": bool(dry),
             "kdbp": os.path.isdir(os.path.join(root, ".kdbp")),
             "live_ignored": None, "root_allowed": True if allowed_roots is None else root in allowed_roots}
    skipped, emitted = [], 0
    if emit and missed:
        if claim != "present":
            skipped.append("no map claim (%s) — a delta needs a context-A claim to diverge from" % claim)
        elif not gates["kdbp"]:
            skipped.append("no .kdbp/ under %s" % root)
        elif not gates["root_allowed"]:
            skipped.append("root outside the session roots (read-only)")
        else:
            gates["live_ignored"] = _live_ignored(root)
            if not gates["live_ignored"]:
                skipped.append("%s is not gitignored — run /gabe-init update to seed it" % LIVE_REL)
    for p in missed[:cap]:
        if emit and not skipped and not dry:
            if emit_delta(root, sym, p, by_file[p]["line"], cmd):
                emitted += 1
    notes = []
    if len(missed) > cap:
        notes.append("%d missed files, capped at %d (%d not emitted)" % (len(missed), cap, len(missed) - cap))
    return {"symbol": sym, "map_claim": claim, "callers_status": callers_status, "grep_status": grep_status,
            "callers": sorted(callers), "callers_detail": chits[:CAP], "defs": sorted(defs),
            "grep_code_files": code_files[:CAP], "grep_prose_files": prose_files[:CAP],
            "grep_hits": [by_file[p] for p in sorted(by_file)][:CAP],
            "missed_by_map": missed[:cap], "reach": reach, "emitted": emitted, "emit_skipped": skipped,
            "gates": gates, "notes": notes, "capped": len(missed) > cap or len(by_file) > CAP}


def reach_line(result: dict, root: str) -> str:
    """The record form red pastes into PLAN.md. `no index` when there is no map claim at all."""
    if result["map_claim"].startswith("absent: no index") or result["callers_status"].startswith("no index"):
        return "no index"
    rc, out, _ = sh(["git", "-C", root, "rev-parse", "--short", "HEAD"])
    sha = out.strip() if rc == 0 else "?"
    body = " · ".join(result["reach"]) if result["reach"] else "—"
    arm = "graft" if result["map_claim"] == "present" else "grep-only"
    return "- **Reach:** %s (%s@%s)" % (body, arm, sha)


# ── reuse of sibling skills' modules (hyphenated filenames → importlib) ───────
def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise MapStop("cannot import %s" % path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def entity_context_module():
    mod = load_module(ENTITY_CONTEXT, "gabe_entity_context")

    def _fail(msg, code=2):
        raise MapStop(msg)
    mod.fail = _fail
    return mod


def pulse_module(name: str):
    return load_module(PULSE_SCRIPTS / (name + ".py"), "gabe_pulse_" + name)


def cap_list(items, n: int = CAP) -> tuple[list, str | None]:
    items = list(items)
    if len(items) <= n:
        return items, None
    return items[:n], "+%d more (cap %d)" % (len(items) - n, n)


def server_sha(scripts_dir: Path | None = None) -> str:
    """md5 over every .py in the server's scripts dir — the install-vs-running identity."""
    h = hashlib.md5()
    for p in sorted((scripts_dir or HERE).glob("*.py")):
        h.update(p.name.encode()); h.update(p.read_bytes())
    return h.hexdigest()[:12]
