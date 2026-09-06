#!/usr/bin/env python3
"""fetch_bridge.py — web→API bridge drift, two arms (mirrors entity_shape.py exactly).

A web ``apiFetch`` that resolves to no declared endpoint is a coverage-gap finding:
the frontend calls an API surface no entity owns — a missing/undeclared endpoint, a
typo'd path, or model drift. Two arms surface it on the rails that already fire:

  * STANDING (pulse S10): READ the committed ``c4-graph.json`` ``stats.web.unmatched``
    — the bridge extractor already NAMED every unresolved fetch at emit time. Nothing
    is recomputed here: graft cannot recover a fetch's ``(method, path)`` and a pulse
    angle must not glob source, so we read the PERSISTED bridge. Its staleness profile
    is S9's exactly — it goes stale only if the center is never regenerated. Nothing
    stored beyond the single committed emitter output; no sidecar.

  * ``--diff`` (gabe-review): regex a NEW ``apiFetch(path,{method})`` OR a literal SSE call
    (``new EventSource("/x")`` / ``fetchEventSource("/x", {method})``) on ADDED (+) diff
    lines and match it against the committed endpoint key-space, so review prices a new
    unmatched fetch on the diff that caused it, BEFORE the center regenerates. The SSE
    forms are kept in sync with ``_a3_web``'s SSE arm so review flags exactly what the
    standing S10 will nag after regen (a dynamic-arg stream has no single-line literal to
    price here — S10, reading the persisted ``unmatched``, owns that case).

Report-only, no stored artifact, exit 0 always (report-never-gate). The tiny
``norm_path`` mirrors ``_a3_graph._norm_path`` (the bridge's match contract) — a
5-line pure duplicate across two install packages, deliberately not a shared import.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# fire only on a PATTERN of unresolved fetches, not a single stray (anti-wallpaper;
# the pulse decay record suppresses even this after DECAY_AFTER unchanged offers).
WEB_UNMATCHED_MIN = 2

_API_PREFIX_RE = re.compile(r"^/api/v\d+")
_PATH_PARAM_RE = re.compile(r"\$?\{[^}]*\}")


def norm_path(path: str) -> str:
    """The bridge match key — drop /api/vN, collapse {x}/${x} to one placeholder,
    strip a trailing slash. Mirrors _a3_graph._norm_path (kept in sync by contract)."""
    p = (path or "").strip()
    p = _API_PREFIX_RE.sub("", p)
    p = _PATH_PARAM_RE.sub("{}", p)
    p = p.rstrip("/")
    if not p.startswith("/"):
        p = "/" + p
    return p


def _center(root: Path) -> Path:
    return root / "docs" / "site" / "center"


def load_unhomed(root: Path) -> int:
    """``stats.web.unhomed`` — fetching files the bridge could HOME to no entity and whose fetches matched
    nothing: counted at emit time, drawn nowhere (review 2026-09-05: gastify dropped 13 of 24 from the
    Screens column and no surface said so). 0 when absent or unreadable — a count that rides the S10
    line, never its own trigger."""
    try:
        web = json.loads((root / "docs" / "site" / "center" / "c4-graph.json").read_text()).get("stats", {}).get("web") or {}
        return int(web.get("unhomed") or 0)
    except Exception:  # noqa: BLE001 — honest 0
        return 0


def load_unmatched(root: Path) -> tuple[bool, list[dict], str]:
    """``(present, unmatched, reason)`` from the committed c4-graph.json stats.web."""
    c4 = _center(root) / "c4-graph.json"
    if not c4.exists():
        raise FileNotFoundError(f"no c4-graph at {c4}")
    web = (json.loads(c4.read_text(encoding="utf-8")).get("stats") or {}).get("web") or {}
    if not web.get("present"):
        return False, [], web.get("reason", "web arm absent")
    return True, list(web.get("unmatched") or []), web.get("reason", "")


def load_endpoint_keys(root: Path) -> set[tuple[str, str]]:
    """``{(METHOD, norm_path)}`` of the committed archmap endpoints — the diff match set."""
    amap = _center(root) / "archmap.json"
    if not amap.exists():
        raise FileNotFoundError(f"no archmap at {amap}")
    data = json.loads(amap.read_text(encoding="utf-8"))
    keys: set[tuple[str, str]] = set()
    for _slug, ent in (data.get("entities") or {}).items():
        for ep in (ent.get("endpoints") or []):
            keys.add((str(ep.get("method", "")).upper(), norm_path(str(ep.get("path", "")))))
    return keys


# ── diff mode — a NEW apiFetch the diff ADDS, resolving to no declared endpoint ──
_FETCH_RE = re.compile(r"""apiFetch\w*\s*(?:<[^>]*>)?\s*\(\s*[`'"]([^`'"]+)[`'"]""")
_METHOD_RE = re.compile(r"""method\s*:\s*[`'"](GET|POST|PUT|PATCH|DELETE)""", re.I)
# a NEW SSE call with a LITERAL path — kept in sync with _a3_web's SSE arm so the review
# diff-arm prices exactly what pulse S10 (reading stats.web.unmatched) will later nag.
# EventSource is GET by spec; fetchEventSource reads its options method (default GET). A
# dynamic-arg stream (the Tier-2 case) has no single-line literal to price here — S10 owns it.
_SSE_RE = re.compile(
    r"""(?P<es>new\s+(?:[\w$]+\.)?EventSource(?:Polyfill)?|fetchEventSource)\s*(?:<[^>]*>)?\s*\(\s*[`'"]([^`'"]+)[`'"]""")


def diff_new_fetches(diff_text: str) -> list[tuple[str, str]]:
    """``[(METHOD, path)]`` for apiFetch AND literal SSE calls on ADDED (+) diff lines."""
    out: list[tuple[str, str]] = []
    for line in diff_text.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        m = _FETCH_RE.search(line)
        if m:
            mm = _METHOD_RE.search(line)
            out.append(((mm.group(1).upper() if mm else "GET"), m.group(1)))
        s = _SSE_RE.search(line)
        if s:
            # EventSource → GET; fetchEventSource → its options method (default GET)
            if s.group("es").startswith("new"):
                out.append(("GET", s.group(2)))
            else:
                sm = _METHOD_RE.search(line)
                out.append(((sm.group(1).upper() if sm else "GET"), s.group(2)))
    return out


def classify_new_fetches(new_fetches: list[tuple[str, str]],
                         endpoint_keys: set[tuple[str, str]]) -> list[dict]:
    """Which NEW fetches resolve to no committed endpoint (drift). A matched fetch
    is silent (it has a home). Deterministic, sorted."""
    drift = []
    for method, path in new_fetches:
        if (method, norm_path(path)) in endpoint_keys:
            continue
        drift.append({"method": method, "path": path})
    drift.sort(key=lambda d: (d["method"], d["path"]))
    return drift


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".", help="project root")
    ap.add_argument("--json", action="store_true", help="emit the standing shape as JSON")
    ap.add_argument("--one-line", action="store_true", help="emit the pulse line (silent when no signal)")
    ap.add_argument("--diff", nargs="?", const="HEAD", default=None,
                    help="review mode: flag NEW apiFetch calls in the git diff (default HEAD) that hit no endpoint")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    if args.diff is not None:
        try:
            keys = load_endpoint_keys(root)
        except FileNotFoundError:
            print("WEB-BRIDGE DRIFT NOT RUN: no committed archmap.json — no endpoint set to check against")
            return 0
        try:
            diff_text = subprocess.run(["git", "-C", str(root), "diff", args.diff],
                                       capture_output=True, text=True, timeout=30).stdout
        except Exception:   # noqa: BLE001 — a git hiccup is silence, not a crash
            return 0
        drift = classify_new_fetches(diff_new_fetches(diff_text), keys)
        for d in drift:
            print(f"WEB-BRIDGE DRIFT: new fetch {d['method']} {d['path']} resolves to no "
                  f"declared endpoint — the web calls an API surface no entity owns")
        return 0

    try:
        present, unmatched, reason = load_unmatched(root)
        unhomed = load_unhomed(root) if present else 0
    except FileNotFoundError as exc:
        if args.one_line:
            return 0            # pulse convention: honest silence — no center, no signal
        print(f"fetch_bridge: {exc}", file=sys.stderr)
        return 0                # report-never-gate: never a non-zero exit
    if args.json:
        print(json.dumps({"present": present, "unmatched": unmatched, "unhomed": unhomed, "reason": reason},
                         indent=1, sort_keys=True))
        return 0
    if args.one_line:
        if present and len(unmatched) >= WEB_UNMATCHED_MIN:
            names = ", ".join(f"{u.get('m')} {u.get('p')}" for u in unmatched[:2])
            more = f" +{len(unmatched) - 2}" if len(unmatched) > 2 else ""
            print(f"web-bridge drift: {len(unmatched)} fetch(es) hit no declared endpoint "
                  f"({names}{more})"
                  + (f" · {unhomed} fetching file(s) unhomed — no screen drawn" if unhomed else ""))
        return 0
    if not present:
        print(f"web bridge absent ({reason})")
    else:
        print(f"web bridge — {len(unmatched)} unmatched fetch(es)"
              + (f" · {unhomed} fetching file(s) unhomed (no screen drawn)" if unhomed else "")
              + (f": {reason}" if reason else ""))
        for u in unmatched:
            print(f"  UNMATCHED {u.get('m')} {u.get('p')}  (from {u.get('from')})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
