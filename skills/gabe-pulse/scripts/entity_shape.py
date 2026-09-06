#!/usr/bin/env python3
"""Entity-shape drift — the URL-domain ↔ entity-model cross-tab.

A PURE function (plus a thin CLI) that names two model defects the tracing tool
cares about:

  * DETACHED domain — a URL surface (`/settings`) that no *domain* entity owns; it
    falls to a cross-cutting aspect, so a workflow traces to the wrong place.
    (The JSON key is `orphans` — a contract three callers read; the reader-facing
    word is DETACHED, ruling R10.)
  * ASPECT entity — a cross-cutting concern (`allergen`) modeled as a peer
    domain: it co-claims many URL domains yet solely-owns almost none.

Report-only. There is NO stored artifact — every caller (pulse, review, cc-init)
computes fresh from its own already-fresh source, so nothing can go stale and
nothing needs remembering. See docs/design/ for the operability rationale.

HAZARD (entity models Phase 3, 2026-09-06): the ASPECT half of this module STAYS even though pulse S9 now
reports the EMITTER's measured aspects (gate fan-in) instead of the URL co-claim rule. Reason: `owned`
below is defined AGAINST `aspect_set`, and `owned` feeds `classify_new_routes` → /gabe-review's ENTITY-SHAPE
DRIFT subject and `mcp__gabe-map__entity_shape diff` on every project. Removing or changing the aspect rule
here silently changes review verdicts everywhere. It is reporting-only in pulse; it is a CLASSIFIER in review.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

# An entity is an ASPECT when it co-claims ≥ this many URL domains AND solely-owns
# ≤ this many — cross-cutting, not a domain (operator-ruled 2026-08-14). Tunable.
ASPECT_COCLAIM_MIN = 3
ASPECT_SOLE_MAX = 1


def url_domain(path: str) -> str:
    """The first non-parameter URL segment — the domain a route belongs to."""
    for seg in str(path).split("/"):
        if seg and seg[0] not in ("{", ":"):
            return seg
    return "root"


def entity_shape(endpoints: Iterable[dict[str, Any]],
                 url_domain_map: dict[str, str] | None = None) -> dict[str, Any]:
    """Classify the URL↔entity cross-tab. PURE + deterministic (sorted output).

    ``endpoints``: iterable of ``{"path": str, "entity": str|None}`` — one per
    route, ``entity`` None/"" for an unclaimed route.
    ``url_domain_map``: optional ``{domain_segment: candidate_name}`` — groups a
    naked segment into a nicer candidate (``settings`` → ``account``); a domain
    absent from the map falls back to its own segment (verbatim floor).

    Returns ``{orphans, aspects, coverage}``.
    """
    umap = url_domain_map or {}
    xtab: dict[str, dict[str, int]] = {}      # domain -> {entity: count}
    unclaimed = 0
    for ep in endpoints:
        ent = ep.get("entity")
        dom = url_domain(ep.get("path", ""))
        if not ent:
            unclaimed += 1
            continue
        xtab.setdefault(dom, {})
        xtab[dom][ent] = xtab[dom].get(ent, 0) + 1

    claimants = {d: set(m) for d, m in xtab.items()}
    all_entities = sorted(set().union(*claimants.values())) if claimants else []

    # per entity: which domains it SOLELY owns vs CO-claims with others
    sole = {e: sorted(d for d, c in claimants.items() if c == {e}) for e in all_entities}
    co = {e: sorted(d for d, c in claimants.items() if e in c and len(c) > 1) for e in all_entities}

    aspects = [
        {"entity": e, "co_claims": co[e], "sole_owns": sole[e]}
        for e in all_entities
        if len(co[e]) >= ASPECT_COCLAIM_MIN and len(sole[e]) <= ASPECT_SOLE_MAX
    ]
    aspect_set = {a["entity"] for a in aspects}

    # a domain is DETACHED (JSON key `orphans`, kept) when no NON-aspect (domain) entity claims
    # it — it lives only inside cross-cutting aspects, so it has no home a person would look in.
    # OWNED = the complement: a domain a real domain entity holds. `owned` is what
    # the diff-mode checks a NEW route against — which is why the aspect rule above must stay
    # even though pulse S9 reports the emitter's measured aspects (see the module HAZARD note).
    orphans, owned = [], []
    for dom in sorted(claimants):
        if claimants[dom] - aspect_set:
            owned.append(dom)
        else:
            orphans.append({
                "domain": dom,
                "claimed_by": sorted(claimants[dom]),
                "candidate": umap.get(dom, dom),
            })

    return {
        "orphans": orphans,
        "aspects": aspects,
        "owned": owned,
        "coverage": {"domains": len(claimants), "unclaimed_endpoints": unclaimed},
    }


# ── diff mode — a NEW route the diff ADDS, landing in a domain no entity owns ──
_ROUTE_RE = re.compile(r'@\w+\.(get|post|put|patch|delete)\(\s*["\']([^"\']+)', re.I)


def diff_new_routes(diff_text: str) -> list[tuple[str, str]]:
    """Route decorators on ADDED (+) lines of a unified diff → [(METHOD, path)].
    Fresh: catches the route BEFORE the archmap regenerates to include it."""
    out: list[tuple[str, str]] = []
    for line in diff_text.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        m = _ROUTE_RE.search(line)
        if m:
            out.append((m.group(1).upper(), m.group(2)))
    return out


def classify_new_routes(new_routes, owned, orphans, url_domain_map=None):
    """Which NEW routes land in a domain no DOMAIN entity owns (drift). Returns
    [{method, path, domain, candidate}] — a route whose domain is already OWNED
    is silent (it has a home)."""
    umap = url_domain_map or {}
    owned_set = set(owned)
    orphan_cand = {o["domain"]: o["candidate"] for o in orphans}
    drift = []
    for method, path in new_routes:
        dom = url_domain(path)
        if dom in owned_set:
            continue                        # the domain has a home — no drift
        drift.append({"method": method, "path": path, "domain": dom,
                      "candidate": orphan_cand.get(dom, umap.get(dom, dom))})
    return drift


def one_line(shape: dict[str, Any]) -> str:
    """A single pulse-style line, or "" when nothing fires (the silence contract)."""
    bits = []
    for o in shape["orphans"]:
        cand = o["candidate"]
        tail = f" (candidate: {cand})" if cand != o["domain"] else ""
        bits.append(f"/{o['domain']} orphaned{tail}")
    for a in shape["aspects"]:
        bits.append(f"{a['entity']} is an aspect ({len(a['co_claims'])} domains)")
    if not bits:
        return ""
    return "entity-shape drift: " + " · ".join(bits)


# ── CLI: load a project's committed archmap + optional url_domain_map ──────────
def load_project(root: Path) -> tuple[list[dict[str, Any]], dict[str, str]]:
    amap_path = root / "docs" / "site" / "center" / "archmap.json"
    if not amap_path.exists():
        raise FileNotFoundError(f"no archmap at {amap_path}")
    amap = json.loads(amap_path.read_text(encoding="utf-8"))
    endpoints = [
        {"path": e.get("path", ""), "entity": slug}
        for slug, ent in (amap.get("entities") or {}).items()
        for e in (ent.get("endpoints") or [])
    ]
    umap: dict[str, str] = {}
    cfg_path = root / "docs" / "site" / "center" / "center.config.json"
    if cfg_path.exists():
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        umap = cfg.get("url_domain_map") or {}
    return endpoints, umap


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", nargs="?", default=".", help="project root")
    ap.add_argument("--json", action="store_true", help="emit the full shape as JSON")
    ap.add_argument("--one-line", action="store_true", help="emit the pulse line (silent when no signal)")
    ap.add_argument("--diff", nargs="?", const="HEAD", default=None,
                    help="review mode: flag NEW routes in the git diff (default HEAD) that land in an unowned domain")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    try:
        endpoints, umap = load_project(root)
    except FileNotFoundError as exc:
        if args.diff is not None:
            # review convention: a check that could NOT run says so, never a false clean
            print("ENTITY-SHAPE DRIFT NOT RUN: no committed archmap.json — no model to check against")
            return 0
        if args.one_line:
            return 0            # pulse convention: honest silence — no center, no signal
        print(f"entity_shape: {exc}", file=sys.stderr)
        return 0                # report-never-gate: never a non-zero exit
    shape = entity_shape(endpoints, umap)

    if args.diff is not None:
        try:
            diff_text = subprocess.run(["git", "-C", str(root), "diff", args.diff],
                                       capture_output=True, text=True, timeout=30).stdout
        except Exception:
            return 0            # report-never-gate — a git hiccup is silence, not a crash
        drift = classify_new_routes(diff_new_routes(diff_text), shape["owned"], shape["orphans"], umap)
        if not drift:
            return 0            # silent when the diff adds nothing that drifts
        for d in drift:
            print(f"ENTITY-SHAPE DRIFT: new route {d['method']} {d['path']} lands in "
                  f"unowned domain /{d['domain']} — no domain entity owns it "
                  f"(candidate: {d['candidate']})")
        return 0
    if args.json:
        print(json.dumps(shape, indent=1, sort_keys=True))
    elif args.one_line:
        line = one_line(shape)
        if line:
            print(line)
    else:
        print(f"domains: {shape['coverage']['domains']} · unclaimed: {shape['coverage']['unclaimed_endpoints']}")
        for o in shape["orphans"]:
            print(f"  DETACHED /{o['domain']:18} claimed by {o['claimed_by']} -> candidate: {o['candidate']}")
        for a in shape["aspects"]:
            print(f"  ASPECT {a['entity']:16} co-claims {len(a['co_claims'])} {a['co_claims']} · sole-owns {a['sole_owns']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
