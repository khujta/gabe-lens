#!/usr/bin/env python3
"""A3 command-center station generator (stdlib only).

Fills the SHIPPED A3-Tabbed shell skeletons
(templates/center/shell/ — vendored, adopt-spec 1.1.1 §shell contract) with
machine facts from _center_data.py. The shell's invariant chrome — colored+iconed
sidebar (map v3: Now · Board · Entities · Docs · Code · Testing · Ledger ·
Releases · Leaf), the five-tab feature bar (Overview · Code · Tests · Evidence ·
Risk) and its data-sec section identities — ships IN the skeletons and is never
regenerated here; this only fills the project-specific slots.

Anti-curation: every number below is read from a machine source at build time
(PLAN.md, PENDING.md, LEDGER.md, junit XML, adoption.json, git). Slots whose
generator does not exist yet are left as raw {{TOKEN}}s so assets/slots.js
renders them as an honest "awaiting generator" chip — never as fake coverage.

Usage:  python3 scripts/build_center_a3.py
Gate:   python3 scripts/check_center_links.py   (run after)
"""

from __future__ import annotations

import contextlib
import datetime as _dt
import glob
import json
import os
import re
import subprocess
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _center_data as D  # noqa: E402
import _a3_board
import _a3_code
import _a3_graft  # noqa: E402  (the graft-wiring arm — topology provider)
import _a3_graph  # noqa: E402  (the C4 codebase-graph derivation)
import _a3_levels  # noqa: E402  (the rich LEVELS graph — the lab-native station feed)
import _a3_homing  # noqa: E402  (the membership EVIDENCE — file · users · data witnesses per piece; nothing re-homes)
import _a3_sim  # noqa: E402  (the live change-simulation projection — window.GABE_SIM)
import _a3_commits  # noqa: E402  (recent git commits → the elements they touched — window.GABE_COMMITS)
import _a3_web  # noqa: E402  (the web→API bridge extractor — the fetch arm)
import _a3_fe  # noqa: E402  (the frontend STRUCTURE arm — compiler-proven pieces + edges)
import _a3_guard
import _a3_ledger  # noqa: E402  (the case ledger, rulings 2026-07-24)
import _a3_tests  # noqa: E402  (model_insight serialization into archmap)
from _a3_code import ENTITY_CODE, ENTITY_MODELS, collect_entity_map  # noqa: E402
from _a3_evidence import is_reference  # noqa: E402
from _a3_feature import (  # noqa: E402
    ENTITY_PROOFS,
    ENTITY_RX,
    build_feature_pages,
    case_rows,
    claim_verdicts,
    entity_corpus,
    kind_state,
)

REPO_ROOT = D.REPO_ROOT
CENTER = D.CENTER_DIR               # READ root (config, adoption, cards, archmap)
# GABE_CENTER_OUT redirects every WRITE (pages, assets, archmap, run-history) to
# a scratch dir so a lab run can read a real project and never mutate it.
CENTER_OUT = (Path(os.environ["GABE_CENTER_OUT"])
              if os.environ.get("GABE_CENTER_OUT") else CENTER)
# LAB = the run was pointed at ANOTHER project's tree (a twin / dry-run). In LAB mode the graft
# index build defaults OFF (opt-in via GABE_GRAFT_BUILD=1), so a run that forgets the flag can never
# mutate the foreign tree; a normal self-build (no GABE_REPO_ROOT) keeps graft build ON as before.
LAB = bool(os.environ.get("GABE_REPO_ROOT"))
CFG = D.CFG
# The corpora a project verifies with — key · runner · kind, declared in
# center.config.json so no test-suite name is hardcoded here. Defaults to the
# api(pytest)/web(vitest) pair the suite ships with.
CORPORA = CFG.get("corpora") or [
    {"key": "api", "runner": "pytest", "kind": "integration",
     "kind_detail": "HTTP surface", "tag_class": "l-api", "kpi_detail": "pytest"},
    {"key": "web", "runner": "vitest", "kind": "unit",
     "kind_detail": "components/hooks", "tag_class": "l-web", "kpi_detail": "vitest"},
]
E2E = CFG.get("e2e", {})
_PROJECT = CFG.get("project", {})
PROJECT_NAME = _PROJECT.get("name", REPO_ROOT.name)
PROJECT_DISPLAY = _PROJECT.get("display_name", PROJECT_NAME)
# Project maturity is READ from .kdbp/BEHAVIOR.md, not assumed. "" when absent —
# the feature pages render an honest "not declared" rather than a fabricated tier.
MATURITY = D.load_maturity()
# This generator emits the app-wide Architecture station every run (rendered
# from archmap.json — the read-once rule), so its Code-group nav item is always
# lit. A binding a project has not wired yet would flip this False and get the
# honest "not built yet" line instead.
BUILD_ARCHITECTURE = CFG.get("build_architecture", True)
_IC_LIST = ('<line x1="8" y1="6" x2="21" y2="6"/>'
            '<line x1="8" y1="12" x2="21" y2="12"/>'
            '<line x1="8" y1="18" x2="21" y2="18"/>'
            '<line x1="3" y1="6" x2="3.01" y2="6"/>'
            '<line x1="3" y1="12" x2="3.01" y2="12"/>'
            '<line x1="3" y1="18" x2="3.01" y2="18"/>')
_IC_CODE = ('<polyline points="16 18 22 12 16 6"/>'
            '<polyline points="8 6 2 12 8 18"/>')
_IC_DB = ('<ellipse cx="12" cy="5" rx="9" ry="3"/>'
          '<path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>'
          '<path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>')
_IC_FILES = ('<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 '
             '3h9a2 2 0 0 1 2 2z"/>')
# Testing-station section icons (the old skeleton's hand-carried svgs — the
# station pane is generator-owned now, so the paths live here).
_IC_GRID4 = ('<rect x="3" y="3" width="18" height="18" rx="2"/>'
             '<line x1="3" y1="9" x2="21" y2="9"/>'
             '<line x1="3" y1="15" x2="21" y2="15"/>'
             '<line x1="12" y1="3" x2="12" y2="21"/>')
_IC_KCHECK = ('<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>'
              '<polyline points="22 4 12 14.01 9 11.01"/>')
_IC_CLOCK = '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>'
_IC_WALK = ('<path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>'
            '<circle cx="8.5" cy="7" r="4"/><polyline points="17 11 19 13 23 9"/>')
_IC_SHELF = ('<rect x="3" y="3" width="18" height="18" rx="2"/>'
             '<circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>')
_IC_SHIELD = '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>'
# The entity Tests tab's section icons (subnav parity: the estate page a
# sidebar subitem opens leads with the SAME glyph the entity tab uses).
_IC_DOCP = ('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 '
            '2-2V8z"/><polyline points="14 2 14 8 20 8"/>'
            '<line x1="16" y1="13" x2="8" y2="13"/>'
            '<line x1="16" y1="17" x2="8" y2="17"/>')
_IC_ALERTP = ('<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 '
              '1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>'
              '<line x1="12" y1="9" x2="12" y2="13"/>'
              '<line x1="12" y1="17" x2="12.01" y2="17"/>')
_VERB_CLS = {"GET": "m-get", "POST": "m-post", "DELETE": "m-del",
             "PUT": "m-mut", "PATCH": "m-mut"}
# The shell is a build INPUT, so it is vendored IN THE REPO. It used to be read
# straight from ~/.claude/templates/…, which meant the same commit rendered a
# different center depending on which template version the machine happened to
# have installed — and CI could not regenerate the center at all. For a system
# whose whole claim is "regenerate it and check", the regeneration input has to
# be under version control. The installed copy is now a FALLBACK, and a drift
# between the two is reported rather than silently preferred.
VENDORED_SHELL = REPO_ROOT / "templates" / "center" / "shell"
INSTALLED_SHELL = Path.home() / ".claude" / "templates" / "gabe" / "center" / "shell"


def resolve_shell() -> tuple[Path, str]:
    """(shell dir, one-line provenance) — vendored first, installed as fallback."""
    env = os.environ.get("GABE_SHELL_SRC")
    if env:
        return Path(env), f"shell: {env} (env override)"
    if VENDORED_SHELL.is_dir():
        note = f"shell: {VENDORED_SHELL.relative_to(REPO_ROOT)} (vendored)"
        if INSTALLED_SHELL.is_dir():
            drift = [p.name for p in sorted(VENDORED_SHELL.rglob("*"))
                     if p.is_file()
                     and (INSTALLED_SHELL / p.relative_to(VENDORED_SHELL)).exists()
                     and (INSTALLED_SHELL / p.relative_to(VENDORED_SHELL)
                          ).read_bytes() != p.read_bytes()]
            if drift:
                note += (f" · ⚠ {len(drift)} file(s) differ from the installed "
                         f"copy ({', '.join(drift[:4])}) — vendored wins")
        return VENDORED_SHELL, note
    return INSTALLED_SHELL, (f"shell: {INSTALLED_SHELL} (INSTALLED — not in this "
                             f"repo; regen is not reproducible from a clone)")


SHELL_SRC, SHELL_NOTE = resolve_shell()

import _a3_render as R_MARKS  # noqa: E402  (rowmarks lifecycle — init + snapshot)
from _a3_render import (  # noqa: E402  (helpers live beside this module)
    E,
    ENT_COL,
    entity_badge,
    entity_icon,
    legend,
    meter,
    sechead,
    gap,
    kpi,
    md,
    strip_slot_doc_comments,
    table,
    th_label,
    trunc,
    xtable,
    kind_ic,
)


def sh(*args: str) -> str:
    try:
        return subprocess.run(args, capture_output=True, text=True,
                              cwd=REPO_ROOT).stdout.strip()
    except OSError:
        return ""


# NEW-row badging baseline — the rows-seen snapshot of the LAST COMMITTED
# build. Read from HEAD (not the working tree) so every regen inside one
# iteration diffs against the same anchor: badges are stable until the
# snapshot lands in a commit, then wipe-and-restamp happens by construction.
# Missing/unparseable → None: bootstrap builds badge nothing, record only.
def _rowmarks_baseline() -> dict | None:
    # The snapshot path follows paths.center (a hardcoded default here would
    # silently disarm badging on any retargeted center — the crawl gate's M02
    # lesson applies to every HEAD-anchored read).
    try:
        _center_rel = CENTER.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        _center_rel = "docs/site/center"
    raw = sh("git", "show", f"HEAD:{_center_rel}/rows-seen.json")
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except ValueError:
        return None
    rows = data.get("rows") if isinstance(data, dict) else None
    return rows if isinstance(rows, dict) else None


R_MARKS.init_rowmarks(_rowmarks_baseline())


# --------------------------------------------------------------------------- #
# Machine sources
# --------------------------------------------------------------------------- #

plan = D.load_plan()
pending_all = D.load_pending_rows()   # open AND closed (board Done view)
pending = [r for r in pending_all if r['open']]
ledger = D.load_ledger(8)
# One junit read per declared corpus — keyed by the corpus key, so nothing
# downstream names a specific suite; it iterates CORPORA.
junit_by = {c["key"]: D.load_junit(c["key"]) for c in CORPORA}

adoption = {}
adopt_path = CENTER / "adoption.json"
if adopt_path.exists():
    adoption = json.loads(adopt_path.read_text())
sections = adoption.get("sections", [])
if not adopt_path.exists() or not sections:
    # review 2026-09-06 (repo-study): a repo adopted by config alone (bootstrap_center.sh) has no adoption record
    # yet, or an empty tracker — its center.config.json entities ARE the registry. Said out loud, never a SystemExit.
    sections = [{"entity": _s, "display_name": _s, "rank": "unranked", "status": "config-only",   # every field the board reads (tier1's first build crashed on `status`)
                 "checklist": {}, "signals": "center.config.json — no adoption record yet",
                 "approved_walk": None, "notes": "adopted by config (bootstrap_center.sh); /gabe-cc-init records the adoption"}
                for _s in sorted(ENTITY_CODE)]
    print(f"  ⚠ adoption.json {'absent' if not adopt_path.exists() else 'has no sections'} at {adopt_path} — entity registry "
          f"taken from center.config.json ({len(sections)} entities); /gabe-cc-init records the adoption sections")

walks = []
_walks_path = REPO_ROOT / ".kdbp" / "walks.jsonl"
if _walks_path.exists():
    for _ln in _walks_path.read_text().splitlines():
        if _ln.strip():
            with contextlib.suppress(json.JSONDecodeError):
                walks.append(json.loads(_ln))

phases = plan["phases"]
done_phases = [p for p in phases if all(v == "done" for v in p["cells"].values())]
owed = [p for p in phases if any(v != "done" for v in p["cells"].values())]
open_pending = [r for r in pending if r["open"]]
crit_pending = [r for r in open_pending if r["priority"] in ("critical", "high")]

t_total = sum((j or {}).get("total", 0) for j in junit_by.values())
t_failed = sum((j or {}).get("failed", 0) for j in junit_by.values())
t_skipped = sum((j or {}).get("skipped", 0) for j in junit_by.values())
pass_pct = f"{100.0 * (t_total - t_failed) / t_total:.1f}%" if t_total else "—"

HEAD_SHA = sh("git", "rev-parse", "--short", "HEAD") or "—"
_NOW = _dt.datetime.now(_dt.timezone.utc)
STAMP = _NOW.strftime("%Y-%m-%d %H:%MZ")
STAMP_ISO = _NOW.strftime("%Y-%m-%dT%H:%M:%SZ")
adopted = sum(1 for s in sections if s["status"] == "approved")

# --------------------------------------------------------------------------- #
# The center's own run accumulator — run-history.jsonl. The pre-adoption center
# kept one line per source per build; the A3 rebuild dropped the WRITER while
# keeping the reader (D.load_history) and the named-gap render. This is the
# writer, restored (adopt-spec §ephemeral/accumulator — the center's accumulator
# is this file). A build appends a source's line ONLY when its totals moved
# since that source's last line, so a regen that re-rendered identical junit adds
# nothing and the cap holds real run history rather than regen noise.
# --------------------------------------------------------------------------- #
HISTORY_CAP = 50


def append_history() -> list[dict]:
    hist = D.load_history()
    last: dict[str, dict] = {}
    for rec in hist:
        last[rec.get("source", "?")] = rec.get("totals", {})
    new = []
    for c in CORPORA:
        src, j = c["runner"], junit_by.get(c["key"])
        if not j:
            continue
        totals = {"passed": j["total"] - j["failed"] - j["skipped"],
                  "failed": j["failed"], "skipped": j["skipped"]}
        if last.get(src) != totals:
            new.append({"ts": STAMP_ISO, "source": src, "totals": totals})
    if not new:
        return hist
    lines = (hist + new)[-HISTORY_CAP:]
    (CENTER_OUT / "run-history.jsonl").write_text(
        "".join(json.dumps(rec) + "\n" for rec in lines))
    return lines


HISTORY = append_history()


def _verification_changelog() -> str:
    """The Tests-station accumulator, rendered — one row per source with its last
    recorded totals and how many builds moved it. Empty history stays an honest
    named gap rather than a zeroed table."""
    if not HISTORY:
        return gap("Verification changelog", "docs/site/center/run-history.jsonl")
    by_src: dict[str, list[dict]] = {}
    for rec in HISTORY:
        by_src.setdefault(rec.get("source", "?"), []).append(rec)
    rows = []
    for src, recs in sorted(by_src.items()):
        t = recs[-1].get("totals", {})
        rows.append([f"<b>{E(src)}</b>", str(t.get("passed", 0)),
                     str(t.get("failed", 0)), str(t.get("skipped", 0)),
                     str(len(recs)), E((recs[-1].get("ts") or "")[:10] or "—"),
                     E(D.rel_age(recs[-1].get("ts")))])
    return table(
        ["Source", "Passed", "Failed", "Skipped", "Runs recorded", "Date",
         "Last change"],
        rows, num={1, 2, 3, 4},
        note=f"{len(HISTORY)} line(s) in run-history.jsonl (committed, capped "
             f"{HISTORY_CAP}) — one per source per build whose totals moved. The "
             f"durable memory of what actually ran; a regen that changed nothing "
             f"adds nothing.")


verification_changelog = _verification_changelog()

# --------------------------------------------------------------------------- #
# Sidebar (entities come from the APPROVED adoption baseline — never an
# archived nav; adopt-spec 1.1.1 shell contract)
# --------------------------------------------------------------------------- #

BOX = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
       'stroke-linecap="round" stroke-linejoin="round">'
       '<rect x="3" y="3" width="18" height="18" rx="2"/></svg>')
# ONE vocabulary. adoption.json is the entity registry: every station names
# entities from it. This used to be a second hand-kept list, while tests.html
# grouped by a THIRD (center.config.json `areas`) and the config declared a
# fourth (`entities`, rendered nowhere) — so a reader crossing from the corpus
# matrix to a feature page silently changed taxonomy. See D123.
# D123: rows carry `display_name` — one word, one fact, rendered on nav, pages
# and the map. `label` is read as a fallback for tracker rows written before the
# rename, so an un-migrated adoption.json still names its entities.
LABELS = {s["entity"]: (s.get("display_name") or s.get("label") or s["entity"])
          for s in sections}
_REGISTRY = set(LABELS)


def _assert_registered(name: str, keys) -> None:
    """A per-entity mapping keyed on a slug the registry does not know is a
    typo that renders as silence — the exact drift class this center exists to
    kill. The config validates its own ids this way; the code dicts never did."""
    unknown = sorted(set(keys) - _REGISTRY)
    if unknown:
        raise SystemExit(
            f"center: {name} has key(s) {unknown} that are not entities in "
            f"adoption.json. Registry: {sorted(_REGISTRY)}")


for _n, _d in (("_a3_feature.ENTITY_RX", ENTITY_RX),
               ("_a3_feature.ENTITY_PROOFS", ENTITY_PROOFS),
               ("_a3_code.ENTITY_CODE", ENTITY_CODE),
               ("_a3_code.ENTITY_MODELS", ENTITY_MODELS)):
    _assert_registered(_n, _d)
def _has_card(slug: str) -> bool:
    """A feature page is written only once the entity has a card
    (build_feature_pages skips the cardless) — so a card on disk is the honest
    test for whether feature-<slug>.html will exist to link to."""
    return (CENTER / "cards" / f"{slug}.md").exists()


def _entity_href(slug: str) -> str:
    """A feature page exists only once the entity has a card — until then the
    nav points at the index rather than a 404."""
    return f"feature-{slug}.html" if _has_card(slug) else "entity-index.html"


# Map v3 (D123): adoption.json IS the registry that drives the sidebar. An
# entity with a card links its feature page; a pending entity (no card yet)
# renders MUTED and points at the index — never a dead feature link. Every row
# that is not yet approved wears its tracker state as a chip, so the sidebar
# tells the truth about what is adopted and what is still owed.
def _sidebar_entity(s: dict) -> str:
    slug = s["entity"]
    status = s["status"]
    approved = status in ("approved", "covered-by-feature")
    has_card = _has_card(slug)
    chip = "" if approved else f' <span class="count">{E(status)}</span>'
    style = "" if has_card else ' style="opacity:.55"'
    href = f"feature-{slug}.html" if has_card else "entity-index.html"
    # The entity's stable hash-picked icon (R: entity icons, 2026-07-23) —
    # the same glyph represents it across the center: nav, index, xref labels.
    return (f'<a class="navitem"{style} href="{href}" '
            f'title="{E(s["rank"])} · {E(status)}">'
            f'{entity_icon(slug, label=LABELS.get(slug, ""))} '
            f'{E(LABELS.get(slug, slug))}{chip}</a>')


sidebar_entities = "\n  ".join(_sidebar_entity(s) for s in sections) \
    or '<span class="navsub" style="opacity:.5">no shortlist yet</span>'

# {{SIDEBAR_CODE}} — the Architecture item lights up only when architecture.html
# is on disk (this generator writes it every run, so it is always lit here); a
# project that has not built the station yet gets an honest muted line, never a
# dead link. The per-feature Code TAB deliberately has no nav item of its own.
_ARCH_IC = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<polyline points="16 18 22 12 16 6"/>'
            '<polyline points="8 6 2 12 8 18"/></svg>')


_ARCH_PAGES = [
    ("arch-endpoints.html", "Endpoints", "sec-code-endpoints", "zap",
     "the HTTP surface, app-wide"),
    ("arch-code-map.html", "Code map", "sec-code-map", "doc",
     "every mapped file, app-wide"),
    ("arch-data-model.html", "Data model", "sec-code-model", "model",
     "every documented class, app-wide"),
    ("arch-dm-candidates.html", "Data-model candidates", "sec-code-model-cands",
     "merge", "merge · split, named by the machine"),
    ("arch-functions.html", "Functions", "sec-code-fns", "fn",
     "every mapped def, app-wide"),
    ("arch-fn-candidates.html", "Function candidates", "sec-code-fn-cands",
     "split", "merge · split, function-scoped"),
]


def _n_cands(recs: dict, floor: float, namer) -> int:
    """The dashboard badge for a candidates page = EXACTLY the rows that page
    renders: deduped MERGE pairs at or above the page's merge floor, plus one
    SPLIT row per god record.

    The `sim` field is recorded from the lower COMPUTE floor (_SIM_FLOOR /
    _FN_SIM_FLOOR) so the detail tables can show a nearest neighbour that is
    NOT a merge candidate; counting `c.get("sim")` therefore advertises a set
    far wider than the table lists, and pairs get counted twice besides. A
    badge the reader cannot reconcile with the page is the same failure R10
    removed — a number stated with more confidence than its basis carries.
    """
    pairs, god = set(), 0
    for key, c in recs.items():
        if c.get("god"):
            god += 1
        s = c.get("sim")
        if s and s.get("j", 0) >= floor:
            pairs.add(tuple(sorted((namer(key, c), s["cls"]))))
    return len(pairs) + god


def estate_menu(items: list[tuple[str, str, str]], current: str) -> str:
    """The STICKY estate menu (operator rulings 2026-07-24): every estate
    subpage carries the same cross-page subnav — back to its overview plus
    every sibling page, current marked. Inline top:0 because these pages
    have no sticky tabbar for the shared .subnav offset to sit under.
    `items` = (fname, label, icon-path)."""
    links = "".join(
        f'<a{" class=\"on\"" if fn == current else ""} href="{fn}">'
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        f"{ic}</svg>{E(lbl)}</a>" for fn, lbl, ic in items)
    return f'<nav class="subnav" style="top:0">{links}</nav>'


def sticky_stack(*parts: str) -> str:
    """Sticky chrome stacked as ONE unit (the estate menu above the entity
    filter bar) — two independent top:0 sticky bars overlap on scroll, the
    later one covering the earlier (.stickstack neutralizes the parts' own
    stickiness)."""
    return '<div class="stickstack">' + "".join(parts) + "</div>"


def _mini_ic(name: str) -> str:
    return ('<svg viewBox="0 0 24 24" width="14" height="14" fill="none" '
            'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            'stroke-linejoin="round">'
            + _a3_code._INS_ICONS[name] + "</svg>")


def _sidebar_code(current: str = "") -> str:
    """The CODE nav group: Architecture (dashboard) + one subitem per
    architecture page, each with its own icon (operator ruling 2026-07-23).
    `current` names the page to highlight."""
    if not ((CENTER / "architecture.html").exists() or BUILD_ARCHITECTURE):
        return '<span class="navsub" style="opacity:.5">not built yet</span>'
    on = " on" if current == "architecture.html" else ""
    out = [f'<a class="navitem{on}" href="architecture.html">'
           f"{_ARCH_IC} Architecture</a>"]
    for fname, title, _anchor, icon, _sub in _ARCH_PAGES:
        on = " on" if current == fname else ""
        out.append(f'<a class="navitem navsubitem{on}" href="{fname}">'
                   f"{_mini_ic(icon)} {title}</a>")
    return "\n  ".join(out)


# {{SIDEBAR_LEAF}} — each known OSS report gets a link WHEN its file is on disk
# under center/leaf/, else the honest empty line. Never a dead link.
_LEAF_REPORTS = [(r["path"], r["label"]) for r in CFG.get("leaf_reports", [])]
_LEAF_IC = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>'
            '<polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>')
sidebar_leaf = "\n  ".join(
    f'<a class="navitem" href="{rel}">{_LEAF_IC} {E(label)}</a>'
    for rel, label in _LEAF_REPORTS if (CENTER / rel).exists()
) or '<span class="navsub" style="opacity:.5">none wired yet</span>'

# --------------------------------------------------------------------------- #
# Hub content
# --------------------------------------------------------------------------- #

hub_stats = '<div class="kpis">' + "".join([
    kpi("tests", f"{t_total:,}", f"{t_failed} failed · {t_skipped} skipped",
        alert=bool(t_failed)),
    kpi("pass rate", pass_pct, "junit api + web"),
    kpi("phases", f"{len(done_phases)}/{len(phases)}", f"current {plan['current_phase']}"),
    kpi("open debt", str(len(open_pending)),
        f"{len(crit_pending)} critical/high", alert=bool(crit_pending)),
    kpi("adopted", f"{adopted}/{len(sections)}",
        f"{sum(1 for s in sections if s['status'] == 'awaiting-approval')} "
        f"awaiting approval", alert=bool(len(sections) - adopted)),
]) + "</div>"

recent_changes = table(
    ["Date", "Type", "Change", "Commit"],
    [[E(r[0]), E(r[1]), f"<b>{md(r[2])}</b>", f"<code>{E(r[3])}</code>"] for r in ledger],
    note="Source: .kdbp/LEDGER.md — newest first.")

needs_rows = [
    [f'<b>{E(p["id"])}</b> {E(trunc(p["name"], 44))}',
     E(", ".join(k for k, v in p["cells"].items() if v != "done")), "phase cell"]
    for p in owed[:8]
] + [
    [f'<b>P{E(r["num"])}</b> {md(trunc(r["finding"], 44))}',
     E(r["priority"]), E(r["source"])]
    for r in crit_pending[:6]
]
# Adoption owes too. The hub knew about phases and debt and nothing about the
# sections — so the re-walk the transaction page demands on its own risk
# register did not appear in the one place a reader looks for "what needs me".
_adopt_rows = []
for _s in sections:
    if _s["status"] == "approved":
        continue
    _unchecked = [k.replace("_", " ") for k, v in _s.get("checklist", {}).items()
                  if not v]
    _owes = (", ".join(_unchecked) if _unchecked
             else "operator approval — the checklist is complete")
    _adopt_rows.append([
        f'<a href="{_entity_href(_s["entity"])}"><b>'
        f'{E(LABELS[_s["entity"]])}</b></a>',
        E(_owes), f'adoption · {E(_s["status"])}'])
needs_rows += _adopt_rows

needs_you = (
    f'<div class="callout warn"><h3>{len(owed)} phase(s) owe cells · '
    f'{len(crit_pending)} critical/high debt · {len(_adopt_rows)} section(s) '
    f'not yet approved</h3></div>'
    + table(["Item", "Owes / priority", "Kind"], needs_rows,
            note=f"Showing {len(needs_rows)} of "
                 f"{len(owed) + len(crit_pending) + len(_adopt_rows)} open "
                 f"items — phase cells, priced debt, and sections awaiting "
                 f"adoption."))

# Drift: the authored current phase vs the earliest phase still owing a cell.
# When they disagree, a phase everyone considers shipped is missing a tick.
if plan.get("authored_phase") and plan["first_owed"] not in plan["authored_phase"]:
    stale = next((p for p in phases if p["id"] == plan["first_owed"]), None)
    unticked = ", ".join(k for k, v in stale["cells"].items() if v != "done") if stale else "?"
    needs_you += (
        f'<div class="callout warn"><h3>PLAN drift — authored phase '
        f'{E(plan["authored_phase"])}, but {E(plan["first_owed"])} still owes '
        f'{E(unticked)}</h3><div class="items">'
        f'<a href="board.html"><b>{E(plan["first_owed"])}</b> unticked '
        f'<span class="tag">{E(unticked)}</span></a></div></div>')

# --------------------------------------------------------------------------- #
# Board content — the card board (_a3_board). The rail-plus-three-lanes page it
# replaces could only ever show ONE phase as current, so every other live
# thread (owed walks, ripening fixes, priced debt, the scope arc) stayed in the
# operator's head. The lanes are gone; the phase SEQUENCE survives as a strip,
# because a card exists only while a phase still owes a cell and finished
# phases would otherwise leave no trace.
# --------------------------------------------------------------------------- #

def render_board(archmap: dict) -> dict:
    """board.html's slots. Called in the SECOND render pass (like the
    architecture station) because the board reads archmap coverage and per-file
    line counts, and archmap is assembled only after the feature pages run.
    Rendering it eagerly would price every card against the PREVIOUS build."""
    cards = _a3_board.build_cards(
        plan=plan, sections=sections, archmap=archmap, adoption=adoption,
        labels=LABELS, entity_href=_entity_href, pending=pending_all)
    n_open = sum(1 for c in cards if not c["done"])
    n_done = len(cards) - n_open
    strip, seq_json = _a3_board.phase_strip(plan)
    return {
        "{{BOARD_TITLE}}": "Board",
        "{{BOARD_LEDE}}": (
            f"Every open move in the project on one surface — so \u201cwhat\u2019s "
            f"next?\u201d is a choice instead of a question. {n_open} open cards "
            f"across six tracks, each carrying what it costs, how long it has sat, "
            f"and the command that starts it, plus {n_done} already closed under "
            f"Done. Derived from PLAN.md, PENDING.md, LEDGER.md, walks.jsonl and "
            f"adoption.json — a projection, never a second source of truth."),
        "{{BOARD_KPIS}}": _a3_board.kpis(cards),
        "{{PHASE_STRIP}}": strip,
        "{{PHASE_JSON}}": seq_json,
        "{{BOARD_MODES}}": _a3_board.modebar(),
        "{{BOARD_FILTERS}}": _a3_board.filter_bar(cards, LABELS),
        "{{BOARD_BOARDS}}": "".join(
            _a3_board.board_html(m, cards, LABELS)
            for m, _l, _s in _a3_board.MODES),
    }

# --------------------------------------------------------------------------- #
# Tests station
# --------------------------------------------------------------------------- #

def entities_of(path: str) -> list[str]:
    """Which registry entities claim this test file — the SAME regexes the
    feature pages count with, so the corpus matrix and a feature page can never
    disagree about what belongs to an entity.

    Returns a LIST because the regexes overlap by design: per-entity counts are
    views over the corpus, never a partition of it. A file claimed twice is
    counted on both rows and says so, rather than being silently assigned to
    whichever rule matched first (which is what the old glob map did)."""
    return [slug for slug, rx in ENTITY_RX.items() if re.search(rx, path, re.I)]


corpora = {c["key"]: junit_by.get(c["key"]) for c in CORPORA}
grid: dict[str, dict[str, list[int]]] = {
    s["entity"]: {c: [0, 0, 0] for c in corpora} for s in sections}
unmapped = {c: [0, 0, 0] for c in corpora}
shared_files = 0
for corpus, j in corpora.items():
    for fpath, rec in (j or {}).get("files", {}).items():
        owners = entities_of(fpath)
        if len(owners) > 1:
            shared_files += 1
        for slug in (owners or [None]):
            row = grid[slug] if slug in grid else unmapped
            row[corpus][0] += rec["tests"]
            row[corpus][1] += 1
            row[corpus][2] += rec["failed"]

n_files = sum(len((j or {}).get("files", {})) for j in junit_by.values())
_corpus_kpis = [
    kpi(c["key"], f"{(junit_by.get(c['key']) or {}).get('total', 0):,}",
        f"{len((junit_by.get(c['key']) or {}).get('files', {}))} files · {c['runner']}")
    for c in CORPORA]
# Coverage rides the KPI row when a reporter is wired (config `coverage`
# block, read by load_coverage); absent it stays the honest named gap.
_covd = D.load_coverage()
_cov_kpi = (
    kpi("coverage", " · ".join(f"{v['percent']}% {k}" for k, v in _covd.items()),
        "lines, from the wired reporter(s)")
    if _covd else kpi("coverage", "—", "no reporter wired"))
tests_kpis = '<div class="kpis">' + "".join([
    kpi("total", f"{t_total:,}", f"{n_files} files"),
    *_corpus_kpis,
    kpi("failed", str(t_failed), f"{t_skipped} skipped", alert=bool(t_failed)),
    _cov_kpi,
]) + "</div>"

# "N api + M web" — the per-corpus estate breakdown for the Testing lede.
_corpus_breakdown = " + ".join(
    f"{(junit_by.get(c['key']) or {}).get('total', 0):,} {c['key']}" for c in CORPORA)

# The dashboard MATRIX: entity × KIND health grid — every entity's testing
# state in one look (the old command set's shape, rebuilt on kind identity;
# operator ruling 2026-07-23). Junit-backed kinds show counts + pass state,
# the rest show their honest gap per entity (walks = manual).
_kind_by_corpus = {c["key"]: c.get("kind", c["key"]) for c in CORPORA}
# The static journey column is the DEBT display ("not wired") — it stands
# only while no corpus carries the journey kind; a wired e2e corpus takes
# the column over with real counts.
_kind_cols = ([(k, _kind_by_corpus[k]) for k in corpora]
              + [("", k2) for k2 in ("journey", "coverage", "manual",
                                     "deployed")
                 if k2 not in _kind_by_corpus.values()])
_hdr = "".join(f'<th title="{E(kind)}">{kind_ic(kind, 14)}</th>'
               for _k, kind in _kind_cols)


def _kind_cell(slug2, corpus, kind):
    if corpus:
        n, nf, failed = (grid[slug2] if slug2 else unmapped)[corpus]
        if not n:
            return '<td class="void">—</td>'
        state = (f'<small style="color:#b3403a">{failed} failing</small>'
                 if failed else "<small>all pass</small>")
        return (f'<td><span class="cell"><b>{n}</b> {state}<br>'
                f"<small>{nf} file(s)</small></span></td>")
    if kind == "manual" and slug2:
        wn = sum(1 for w in walks
                 if w.get("subject") in (slug2, f"adopt:{slug2}"))
        return (f'<td><span class="cell"><b>{wn}</b> '
                f"<small>walk(s)</small></span></td>" if wn
                else '<td class="void">never walked</td>')
    if kind == "journey":
        return '<td class="void">not wired</td>'
    if kind == "coverage":
        return '<td class="void">not sliced</td>'
    return '<td class="void">—</td>'


_rows = ""
for a in [{"id": s["entity"], "label": LABELS[s["entity"]]} for s in sections]:
    cells = "".join(_kind_cell(a["id"], k, kind) for k, kind in _kind_cols)
    _rows += (f'<tr><th class="area"><a href="{_entity_href(a["id"])}">'
              + entity_badge(a["id"], a["label"], 13) + f' {E(a["label"])}'
              f"</a></th>{cells}</tr>")
_rows += ('<tr><th class="area">unclaimed</th>'
          + "".join(_kind_cell(None, k, kind) if k
                    else '<td class="void">—</td>'
                    for k, kind in _kind_cols) + "</tr>")
# The grid alone — its claimed-by prose folds into the station sechead's ⊕
# (declutter ruling 2026-07-22: a table is flanked only by its data).
matrix = (f'<table class="riskgrid"><tr><th class="area">'
          f"{th_label(ENT_COL)}</th>{_hdr}</tr>{_rows}</table>")
_matrix_note = (
    f"Files are claimed by the ENTITY REGISTRY (adoption.json) through the "
    f"same regexes the feature pages count with — click an entity to open "
    f"its page. The regexes overlap by design, so {shared_files} file(s) "
    f"are claimed by more than one entity and counted on each row: these "
    f"are views over the corpus, not a partition of it, and the rows do "
    f'not sum to the total. "unclaimed" is honest surface area, not failure.')

# --- the corpus, file by file: the reverse index the archive had and the A3
# center dropped. A reader on a feature page can reach its files; nobody could
# go the other way, and the 608 unclaimed cases had no surface at all.
_file_rows, _file_exp = [], []
for _corpus, _j in corpora.items():
    for _f, _rec in sorted((_j or {}).get("files", {}).items(),
                           key=lambda x: -x[1]["tests"]):
        _owners = entities_of(_f)
        _claim = " ".join(
            f'<a class="dlink" href="{_entity_href(o)}">{E(LABELS[o])}</a>'
            for o in _owners) or '<span class="tag s-gap">unclaimed</span>'
        _cells = [
            " ".join(f'<a href="{_entity_href(o)}">'
                     + entity_badge(o, LABELS.get(o, o), 13) + "</a>"
                     for o in _owners),
            f'<span class="tag {"l-api" if _corpus == "api" else "l-web"}">'
            f"{E(_corpus)}</span>",
            f"<code>{E(_f)}</code>", str(_rec["tests"]),
            meter(_rec["tests"] - _rec["failed"], _rec["tests"]), _claim]
        # Rows OPEN to their cases (operator ruling 2026-07-24, superseding
        # Q3's flat rows): the app file altitude expands exactly like the
        # entity tab's, C-ids linking the Cases page — the row's identity
        # stays the file, the fold is the reading view.
        _file_rows.append((_cells, case_rows(_rec, _corpus, link_cids=True,
                                             cid_base="test-matrix.html")))
_unclaimed_files = sum(1 for r in _file_rows if "unclaimed" in r[0][5])
files_section = (
    sechead("Testing", "Files", "#0f766e", _IC_DOCP,
            sub="the file altitude — every test file, its ratios, and what "
                "claims it; the cases live on the Cases ledger",
            id_="sec-tests-files",
            info='<div class="leg">Claimed by = the registry entities whose '
                 "file pattern matches. A file may be claimed twice — the "
                 "counts are views, not a partition.</div>"
                 + legend("Claim state:", [
                     ("s-gap", "unclaimed",
                      "no adopted entity names this file yet — surface area, "
                      "not failure")]))
    + xtable([ENT_COL, "Corpus", "File", "Cases", "Passing", "Claimed by"],
             _file_rows,
             widths=["40px", "0.9fr", "2.6fr", "0.6fr", "1fr", "1.4fr"],
            note=f"{len(_file_rows)} file(s) · {_unclaimed_files} unclaimed. "
                 f"Read from the junit capture at build time; a file that stops "
                 f"running disappears from this table by itself."))

# The estate cards — the station's overview, mirroring the entity Tests tab's
# section set (cases · files · claims · untested) plus the machinery page.
# Every count is the same variable its landing section leads with.
_unt_counts = _a3_tests.untested_counts(REPO_ROOT)
testing_cards = ('<div class="archgrid">'
                 + "".join(
                     f'<a class="archcard" href="{fn}">{_mini_ic(ic)}'
                     f"<span><b>{ttl}</b>"
                     f'<span class="sub">{sub2}</span></span></a>'
                     for fn, ttl, ic, sub2 in [
                         ("test-matrix.html",
                          "Cases — the ledger", "fields",
                          f"{t_total:,} case(s) in {len(_file_rows)} file(s) "
                          f"· C-id anchors · filter by entity, kind, or the "
                          f"element a case exercises"),
                         ("test-files.html", "Files",
                          "archive",
                          f"{len(_file_rows)} file(s) · {_unclaimed_files} "
                          f"unclaimed · per-file flags, ratios and claim "
                          f"state at the file altitude"),
                         ("test-claims.html", "Claims", "doc",
                          f"{len(sections)} entity(ies)' authored coverage, "
                          "verified by class name"),
                         ("test-elements.html", "Untested surface", "fields",
                          f"{sum(_unt_counts.values())} element(s) no case "
                          f"or spec touches ({_unt_counts['endpoint']} "
                          f"endpoint · {_unt_counts['model']} model · "
                          f"{_unt_counts['function']} function)"),
                         ("test-corpora.html", "Corpora & gates", "zap",
                          f"{len(CORPORA)} corpus(es) · report sources · "
                          "pre-commit + CI gates · run history · walks · "
                          "demo shelf"),
                     ])
                 + "</div>")

# --- Kinds & coverage, app-wide — the entity Tests tab's fast snapshot at the
# application altitude: junit-backed kinds carry real counts, the rest their
# honest gap. The coverage row is the one place the app does BETTER than an
# entity: the wired reporters' repo-wide percentages are a machine fact here,
# while per-entity slicing stays a named gap.
_e2e_runner = E2E.get("runner", "playwright")
_e2e_gap_tag = E2E.get("junit_gap_tag", "local-only")
_spec_glob = CFG.get("paths", {}).get(
    "e2e_spec_glob", "tests/web-e2e/**/*.spec.ts")
# Anchored to the REPO, not the process cwd — a lab regen runs from the
# generators dir and a cwd-relative glob would count zero specs there.
_all_specs = sorted(glob.glob(str(REPO_ROOT / _spec_glob), recursive=True))
_ref_specs = [p for p in _all_specs if is_reference(Path(p).name)]
_app_specs = [p for p in _all_specs if p not in _ref_specs]
_app_kind_rows = []
for _c in CORPORA:
    _j = junit_by.get(_c["key"]) or {}
    _krec = {"cases": _j.get("total", 0), "failed": _j.get("failed", 0),
             "skipped": _j.get("skipped", 0), "ran_at": _j.get("ranAt")}
    _app_kind_rows.append(
        [f'<span class="tag {_c["tag_class"]}">{kind_ic(_c["kind"])} '
         f'{_c["kind"]}</span>',
         f'{_c["runner"]} ({_c["kind_detail"]})',
         f'{_krec["cases"]:,}',
         f'{len(_j.get("files", {}))} file(s)',
         meter(_krec["cases"] - _krec["failed"], _krec["cases"]),
         kind_state(_krec)])
# The static journey row is the DEBT display — it stands only while no
# corpus carries the journey kind (a wired e2e corpus reports through the
# loop above with real counts).
_app_kind_rows += ([] if any(c.get("kind") == "journey" for c in CORPORA)
                   else [
    [f'<span class="tag l-mobile">{kind_ic("journey")} journey</span>',
     f"{_e2e_runner} (e2e)", "—",
     f"{len(_app_specs)} spec(s) on disk"
     + (f'<br><small>+{len(_ref_specs)} reference-capture spec(s) held out '
        f"— they run the design lab, not the product</small>"
        if _ref_specs else ""),
     meter(0, 0),
     f'<span class="tag s-gap">no junit capture ({E(_e2e_gap_tag)})</span>']])
_app_kind_rows += [
    [f'<span class="tag l-models">{kind_ic("coverage")} coverage</span>',
     "lines, from the wired reporter(s)", "—",
     (" · ".join(f"{v['percent']}% {k}" for k, v in _covd.items())
      if _covd else "no reporter wired"),
     meter(0, 0),
     ('<span class="tag s-ok">captured</span>' if _covd
      else '<span class="tag s-gap">named gap</span>')],
    [f'<span class="tag l-services">{kind_ic("manual")} manual</span>',
     "operator walks", str(len(walks)),
     '<a class="dlink" href="test-corpora.html#sec-tests-walks">'
     "walks.jsonl</a>",
     meter(0, 0),
     ('<span class="tag s-ok">recorded</span>' if walks
      else '<span class="tag s-gap">none on record</span>')],
    [f'<span class="tag l-schemas">{kind_ic("deployed")} deployed</span>',
     "probes", "—", "nothing probes the deployed surface", meter(0, 0),
     '<span class="tag s-gap">absent</span>'],
]
app_kinds = table(["Kind", "Runner", "Cases", "Where", "Passing", "State"],
                  _app_kind_rows, num={2})

# The STATION BODY (rework ruling 2026-07-25): tests.html is a single-lens
# dashboard — the estate cards (the entity-tab mirror), kinds & coverage
# app-wide, and the entity × kind matrix. Full views live on the estate pages.
tests_body = (
    sechead("Testing", "The estate", "#3f6d4c", _IC_LIST,
            sub="the app-wide testing surfaces, one card each — the same "
                "sections every entity's Tests tab carries",
            id_="sec-tests-estate",
            note="Cases · Files · Claims · Untested surface mirror the "
                 "entity Tests tab at the application altitude; Corpora & "
                 "gates is the machinery — report sources, commit gates, "
                 "run history, recorded walks, and the demo shelf.")
    + testing_cards
    + sechead("Testing", "Kinds & coverage", "#15803d", _IC_KCHECK,
              sub=f"{t_total:,} automated case(s) · {t_failed} failed — "
                  "what verifies this application, how much of it runs, "
                  "and what each kind is for",
              id_="sec-tests-kinds",
              note="Cases, files and the passing proportion are read from "
                   "the junit capture at build time. A kind with no machine "
                   "record shows its gap instead of a zero.",
              info=legend("Kind colors:", [
                  ("l-api", "integration", "API through HTTP ·"),
                  ("l-web", "unit", "components in isolation ·"),
                  ("l-mobile", "journey", "real browser flows ·"),
                  ("l-models", "coverage", "lines executed ·"),
                  ("l-services", "manual", "a human walked it ·"),
                  ("l-schemas", "deployed", "probes against the live app")]))
    + app_kinds
    + sechead("Testing", "Entity × kind", "#3f6d4c", _IC_GRID4,
              sub="every entity's testing state in one look — counts and "
                  "pass state where a kind has a machine record, the honest "
                  "gap where it has none",
              id_="sec-tests-matrix",
              note=_matrix_note)
    + matrix)

_results_rel = CFG.get("paths", {}).get("results", "tests/results")
# What a corpus VERIFIES (operator ruling 2026-07-24) — config
# corpora[].description wins; else the kind's one-liner carries it.
_KIND_WHAT = {
    "integration": "drives the API through real HTTP — every endpoint "
                   "receipt in the center traces back to this corpus",
    "unit": "components and hooks in isolation — file-tier facts "
            "(imports + route literals), never dressed as case proof",
    "journey": "real browser flows through the product — the demo "
               "shelf's proof shots come from these runs",
}


def _corpus_what(c: dict) -> str:
    return E(c.get("description")
             or _KIND_WHAT.get(c.get("kind", ""), c.get("kind_detail", "")))


_bucket_rows = [
    [f'<b>{E(c["key"])}</b>', E(c["runner"]),
     str(len((junit_by.get(c["key"]) or {}).get("files", {}))),
     f'{(junit_by.get(c["key"]) or {}).get("total", 0):,}',
     f'{_results_rel}/{c["key"]}-junit.xml',
     _corpus_what(c)] for c in CORPORA]
if E2E and not E2E.get("junit_wired"):
    _bucket_rows.append(
        ["<b>e2e</b>", E(E2E.get("runner", "playwright")), "—", "—",
         f'<span class="tag">not wired</span> {E(E2E.get("not_wired_note", ""))}',
         E(E2E.get("description") or _KIND_WHAT["journey"])])
buckets = table(
    ["Corpus", "Runner", "Files", "Tests", "Report source",
     "What it verifies"],
    _bucket_rows, num={2, 3})

hooks = D.load_precommit_hooks()
ci_jobs = D.load_ci_jobs()
# What each gate DOES (operator ruling 2026-07-24): well-known hook ids get
# the curated one-liner; a local hook speaks through its own yaml `name:`;
# anything else stays the honest pointer. CI rows list their actual jobs.
_HOOK_DESC = {
    "ruff": "python linter — style + bug patterns before the commit lands",
    "ruff-format": "python formatter — one layout, no debates",
    "black": "python formatter",
    "isort": "python import sorter",
    "mypy": "python static type checker",
    "gitleaks": "secret scanner — blocks credentials from entering git "
                "history",
    "prettier": "js/ts/css formatter",
    "eslint": "js/ts linter",
    "trailing-whitespace": "strips trailing whitespace",
    "end-of-file-fixer": "ensures files end with a newline",
    "check-yaml": "yaml syntax check",
    "check-added-large-files": "blocks oversized files",
}


def _hook_what(hid: str, name: str) -> str:
    if hid in _HOOK_DESC:
        return E(_HOOK_DESC[hid])
    if name and name != hid:
        return f"{E(name)} <small>(its own name line)</small>"
    return ('<span class="sub">local hook — defined in '
            ".pre-commit-config.yaml</span>")


gates = table(
    ["Gate", "Kind", "Detail", "What it does"],
    [[f"<b>{E(h)}</b>", "pre-commit", ".pre-commit-config.yaml",
      _hook_what(h, nm)] for h, nm in hooks]
    + [[f"<b>{E(wf)}</b>", "ci", f"{len(js)} job(s)",
        E(" · ".join(str(j.get("name") or j.get("id") or "?")
                     for j in js))]
       for wf, js in ci_jobs.items()],
    note=f'{len(hooks)} pre-commit hook(s) · '
         f'{sum(len(j) for j in ci_jobs.values())} CI job(s).')

proof_root = D.PROOF_DIR
# Dot-dirs are tool residue (.ruff_cache landed on the shelf), not proof.
pdirs = sorted((d for d in proof_root.iterdir()
                if d.is_dir() and not d.name.startswith(".")),
               key=lambda d: d.name) if proof_root.exists() else []
# The shelf explains itself (operator ruling 2026-07-24: "I don't understand
# anything happening there"): every set shows WHO claims it (entity column)
# and WHERE it lands — the claiming entity's Evidence tab, where the legs
# and galleries render. Ownership = center.config.json entities[].proofs;
# an unclaimed set is named surface area, not noise. All sets render (the
# old top-14 cap was a silent truncation).
_set_owners: dict[str, list[str]] = {}
for _pslug, _pnames in ENTITY_PROOFS.items():
    for _pn in _pnames:
        _set_owners.setdefault(_pn, []).append(_pslug)


def _ev_anchor(name: str) -> str:
    return "ev-" + re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-")


def _manifest_of(d: Path) -> dict:
    p = d / "manifest.json"
    if p.exists():
        with contextlib.suppress(json.JSONDecodeError):
            return json.loads(p.read_text())
    return {}


def _guess_owner(name: str) -> str:
    """The LIKELY entity for an unclaimed set — its folder name run through
    the SAME registry regexes that claim test files. A machine guess for
    the integration pass, always labeled as one, never dressed as a claim."""
    for _gs, _grx in ENTITY_RX.items():
        with contextlib.suppress(re.error):
            if re.search(_grx, name, re.I):
                return _gs
    return ""


_shelf_rows = []
for _d in pdirs:
    _owners = _set_owners.get(_d.name, [])
    _mt = max((p.stat().st_mtime for p in _d.glob("*.png")), default=0)
    _when = (_dt.datetime.fromtimestamp(_mt, _dt.timezone.utc)
             .strftime("%Y-%m-%d") if _mt else "—")
    _ecell = " ".join(
        f'<a href="{_entity_href(o)}">'
        + entity_badge(o, LABELS.get(o, o), 13) + "</a>" for o in _owners)
    # WHAT the set shows — the manifest's own words (feature + story),
    # written by /gabe-cc-update curate after the green run. A set with NO
    # manifest predates the flow: it wears the LEGACY identifier, and the
    # closest thing it has to a story — its own numbered shot names — is
    # shown so the integration pass knows what it is looking at.
    _man = _manifest_of(_d)
    _legacy = not _man
    _name_cell = f"<b>{E(_d.name)}</b>" + (
        '<br><span class="tag s-med t-lg">legacy</span>' if _legacy else "")
    _feat = str(_man.get("feature") or "")
    _story = str((_man.get("narration") or {}).get("story") or "")
    if _feat or _story:
        _what = ((f"<b>{E(_feat)}</b>" if _feat else "")
                 + (f"<br><small>{E(_story)}</small>" if _story else ""))
    else:
        _shots = sorted(p.stem for p in _d.glob("*.png"))
        _peek = " · ".join(E(s) for s in _shots[:3])
        _rest = (f" (+{len(_shots) - 3} more in "
                 f"tests/web-e2e/proof/{E(_d.name)}/)"
                 if len(_shots) > 3 else "")
        _what = ('<span class="tag s-gap">no manifest</span>'
                 + (f'<br><small>shots: {_peek}{_rest}</small>'
                    if _shots else ""))
    _carded = next((o for o in _owners
                    if _entity_href(o).startswith("feature-")), "")
    if _carded:
        _land = (f'<a class="dlink" href="{_entity_href(_carded)}'
                 f'#{_ev_anchor(_d.name)}">'
                 f"{E(LABELS.get(_carded, _carded))}'s Evidence tab — "
                 "legs + galleries</a>")
    elif _owners:
        _land = '<span class="tag s-med">no feature page yet</span>'

    else:
        _land = '<span class="tag s-gap t-uncl">unclaimed</span>'

        _g = _guess_owner(_d.name)
        if _g:
            _land += (' <span class="sub">likely</span> '
                      f'<a href="{_entity_href(_g)}">'
                      + entity_badge(_g, LABELS.get(_g, _g), 13,
                                     show_name=True) + "</a>")
    _shelf_rows.append([_ecell, _name_cell, _what,
                        str(len(list(_d.glob("*.png")))), _when, _land])
# The shelf FILTER bar (operator ruling 2026-07-24): entity (owners AND
# likely guesses — both carry the ent- badge class) · set state
# (legacy/curated) · claim state. Same select dialect as the ledger bar;
# hidden rows ride the shared ehide class.
_shelf_bar = (
    '<div class="ledbar" id="shelfbar">'
    '<label><span class="ltit">entity</span><select id="sh-ent">'
    '<option value="all">all</option>'
    + "".join(f'<option value="{s["entity"]}">'
              f'{E(LABELS.get(s["entity"], s["entity"]))}</option>'
              for s in sections)
    + "</select></label>"
    '<label><span class="ltit">set</span><select id="sh-set">'
    '<option value="all">all</option>'
    '<option value="legacy">legacy</option>'
    '<option value="curated">curated</option></select></label>'
    '<label><span class="ltit">claim</span><select id="sh-claim">'
    '<option value="all">all</option>'
    '<option value="claimed">claimed</option>'
    '<option value="unclaimed">unclaimed</option></select></label>'
    f'<span class="sub" id="sh-count">{len(pdirs)} set(s)</span></div>')
_shelf_script = (
    "<script>(function(){var bar=document.getElementById('shelfbar');"
    "if(!bar)return;function apply(){"
    "var ent=document.getElementById('sh-ent').value,"
    "st=document.getElementById('sh-set').value,"
    "cl=document.getElementById('sh-claim').value,n=0;"
    "[].slice.call(document.querySelectorAll("
    "'#shelf table.tbl tbody tr')).forEach(function(r){"
    "var ok=(ent==='all'||!!r.querySelector('.ent-'+ent))"
    "&&(st==='all'||((st==='legacy')===!!r.querySelector('.t-lg')))"
    "&&(cl==='all'||((cl==='unclaimed')===!!r.querySelector('.t-uncl')));"
    "r.classList.toggle('ehide',!ok);if(ok)n++;});"
    "var c=document.getElementById('sh-count');"
    "if(c)c.textContent=n+' set(s)';}"
    "bar.addEventListener('change',apply);})();</script>")
demo_shelf = (_shelf_bar + '<div id="shelf">' + table(
    [ENT_COL, "Proof set", "What it shows", "Shots", "Newest",
     "Where it lands"],
    _shelf_rows, num={3},
    # What-it-shows carries the prose — give it the room; Shots and the
    # fixed-format date sit in narrow px columns (operator ruling
    # 2026-07-24: the description was cramped while fixed cells sprawled).
    widths=["44px", "1.1fr", "3.4fr", "58px", "100px", "1.5fr"],
    note=f"{len(pdirs)} proof set(s) under tests/web-e2e/proof/ — "
         "screenshots a human CURATED after a green run (/gabe-cc-update "
         "curate). A set is claimed by entities[].proofs in "
         "center.config.json and renders in full on its entity's Evidence "
         "tab; an unclaimed set is surface area for the next adoption.")
    + "</div>" + _shelf_script
) if pdirs else gap("Demo shelf", "tests/web-e2e/proof/")

# --------------------------------------------------------------------------- #
# Entity index station — the approved adoption baseline (adoption.json)
# --------------------------------------------------------------------------- #

_by_rank = {"critical": 0, "high": 1, "medium": 2}
entities_kpis = '<div class="kpis">' + "".join([
    kpi("entities", str(len(sections)), "approved baseline"),
    kpi("critical", str(sum(1 for s in sections if s["rank"] == "critical"))),
    kpi("high", str(sum(1 for s in sections if s["rank"] == "high"))),
    kpi("adopted", f"{adopted}/{len(sections)}", "walk-approved sections",
        alert=(adopted == 0 and bool(sections))),
]) + "</div>"

entity_grid = table(
    ["Entity", "Rank", "Status", "Machine signals", "Treatment"],
    [[f'<a href="{_entity_href(s["entity"])}"><b>'
      f'{E(LABELS.get(s["entity"], s["entity"]))}</b></a>', E(s["rank"]),
      E(s["status"]), E(trunc(s["signals"], 96)),
      # The column header already says Treatment — don't repeat it in the cell.
      E(trunc(s["notes"].removeprefix("Treatment:").split(".")[0], 58))]
     for s in sorted(sections, key=lambda s: _by_rank.get(s["rank"], 3))],
    note="Source: docs/site/center/adoption.json — built one per run via "
         "/gabe-cc-init section <entity>, then walk-approved.")

# --------------------------------------------------------------------------- #
# Hub lens tabs — the four-tab set re-lenses ONE subject (here: the project).
# Each lens is a rollup that points at the station holding the full view.
# --------------------------------------------------------------------------- #

_corpus_meta = [(c["key"], c["runner"], junit_by.get(c["key"])) for c in CORPORA]
tab_tests = (
    '<p class="sub">Corpus rollup — one row per corpus. The estate dashboard '
    '(kinds &amp; coverage, the entity × kind matrix, the estate cards) '
    'lives on <a href="tests.html">Tests</a>.</p>'
    + table(["Corpus", "Runner", "Files", "Tests", "Failed", "Skipped", "Last run"],
            [[f"<b>{E(n)}</b>", E(runner), str(len(j["files"])), f'{j["total"]:,}',
              str(j["failed"]), str(j["skipped"]), E(D.rel_age(j.get("ranAt")))]
             for n, runner, j in _corpus_meta if j]
            + ([["<b>e2e</b>", E(E2E.get("runner", "playwright")), "—", "—", "—",
                 "—", '<span class="tag">not wired</span>']]
               if E2E and not E2E.get("junit_wired") else []),
            num={2, 3, 4, 5}))

digests = []
for name in [c["key"] for c in CORPORA]:
    dp = REPO_ROOT / "tests" / "results" / f"{name}-junit.xml.digest.json"
    if dp.exists():
        # A corrupt digest is a missing digest — the row simply doesn't render.
        with contextlib.suppress(json.JSONDecodeError):
            digests.append((name, json.loads(dp.read_text())))

_proof_rows = []
if pdirs:
    _dated = [(d, max((p.stat().st_mtime for p in d.glob("*.png")), default=0),
               len(list(d.glob("*.png")))) for d in pdirs]
    for d, mt, n in sorted(_dated, key=lambda x: -x[1])[:8]:
        when = _dt.datetime.fromtimestamp(mt, _dt.timezone.utc).strftime("%Y-%m-%d") \
            if mt else "—"
        _proof_rows.append([f"<b>{E(d.name)}</b>", str(n), when])

tab_evidence = (
    '<p class="sub">Committed run digests — the memory of what actually ran '
    '(gate-spec <code>results_out</code>).</p>'
    + table(["Report", "Exit", "Passed", "Failed", "Skipped", "Duration", "HEAD", "Recorded"],
            # dict.get(k, default) does NOT apply the default when the key
            # EXISTS with a null value — and a digest legitimately carries
            # `"duration_s": null` when its runner reports no wall clock (the
            # web vitest digest does). Coalesce explicitly; a missing duration
            # renders as a named gap, not as "0s", which would read as a run
            # that took no time.
            [[f"<b>{E(n)}</b>", str(d.get("exit")),
              f'{(d.get("passed") or 0):,}',
              str(d.get("failed") or 0), str(d.get("skipped") or 0),
              (f'{d["duration_s"]:.0f}s' if d.get("duration_s") is not None
               else '<span class="sub">not recorded</span>'),
              f'<code>{E(str(d.get("head_sha")))}</code>',
              E(str(d.get("timestamp_utc", ""))[:16].replace("T", " "))] for n, d in digests],
            num={1, 2, 3, 4, 5},
            note="Absent digest = the run left no machine record.")
    + '<p class="sub">Latest proof sets — newest first. The full shelf '
      '(owners, descriptions, filters) lives on '
      '<a href="test-corpora.html#sec-tests-shelf">Corpora &amp; gates → '
      "Demo shelf</a>.</p>"
    + table(["Proof set", "Shots", "Newest"], _proof_rows, num={1},
            note=f"{len(pdirs)} proof set(s) on disk · showing {len(_proof_rows)}."))

# Risk = what is NOT verified: owed debt, drift, and unwired surfaces.
_risk_rows = [
    [f'<b>P{E(r["num"])}</b> {md(trunc(r["finding"], 52))}', E(r["priority"]),
     md(trunc(r["file"], 34)), E(r["source"])] for r in crit_pending[:8]]
if plan.get("authored_phase") and plan["first_owed"] not in plan["authored_phase"]:
    _risk_rows.append([f'PLAN drift — {E(plan["first_owed"])} still owes a cell '
                       f'while {E(plan["authored_phase"])} is authored current',
                       "high", ".kdbp/PLAN.md", "plan"])
for _n, _d in digests:
    if str(_d.get("head_sha")) != HEAD_SHA:
        _risk_rows.append([f'{E(_n)} evidence predates HEAD '
                           f'(recorded at <code>{E(str(_d.get("head_sha")))}</code>)',
                           "medium", "tests/results/", "digest"])
_gaps = [("e2e junit", "not wired — D121 local-only")]
if not _covd:
    _gaps.insert(0, ("Coverage", "no reporter wired"))
if not walks:
    _gaps.append(("Manual angles", ".kdbp/walks.jsonl absent"))
for _what, _src in _gaps:
    _risk_rows.append([f"{_what} unverified", "gap", E(_src), "named gap"])

tab_risk = (
    '<p class="sub">What is not verified — open critical/high debt, plan drift, '
    'stale evidence and unwired surfaces. Gate states below.</p>'
    + table(["Risk", "Severity", "Where", "Source"], _risk_rows,
            note=f"{len(crit_pending)} critical/high open of {len(open_pending)} total.")
    + '<p class="sub">Gate states.</p>' + gates)

# --------------------------------------------------------------------------- #
# Ledger station — one page per change, from git + PLAN cells + LEDGER row.
# (DEPLOYMENTS/ledger parsing lives here, not in _center_data.py, which is
# already over its size budget — see PENDING split seam.)
# --------------------------------------------------------------------------- #

_shortstat = sh("git", "show", "--shortstat", "--format=", "HEAD").strip()
_head_subject = sh("git", "log", "-1", "--format=%s")
_head_when = sh("git", "log", "-1", "--format=%ad", "--date=short")
_week = sh("git", "log", "--since=7.days", "--format=%h")
_nums = re.findall(r"(\d+) (files? changed|insertions?|deletions?)", _shortstat)
_stat = {k.split()[0]: v for v, k in _nums}

change_kpis = '<div class="kpis">' + "".join([
    kpi("commit", HEAD_SHA, _head_when),
    kpi("files", _stat.get("files", "0"), "changed in HEAD"),
    kpi("insertions", _stat.get("insertions", "0")),
    kpi("deletions", _stat.get("deletions", "0")),
    kpi("commits / 7d", str(len([c for c in _week.splitlines() if c]))),
]) + "</div>"

_log = sh("git", "log", "-10", "--format=%h\x1f%ad\x1f%s", "--date=short")
def entities_touched(sha: str) -> list[str]:
    """Which registry entities a commit touched, from the files it changed.

    ENTITY_CODE already maps entity -> source paths for the Code tab; the same
    map answers "which entity did this change belong to", which the ledger and
    release stations could not say at all. Globs are matched the way the code
    map expands them, so the answer here and on a feature page agree."""
    import fnmatch
    files = sh("git", "show", "--name-only", "--format=", sha).splitlines()
    hit = []
    for slug, layers in ENTITY_CODE.items():
        pats = [pat for pats in layers.values() for pat in pats]
        if any(fnmatch.fnmatch(f, pat) or f == pat
               for f in files for pat in pats):
            hit.append(slug)
    return sorted(hit)


def _entity_chips(slugs: list[str]) -> str:
    return " ".join(
        f'<a class="dlink" href="{_entity_href(x)}">{E(LABELS[x])}</a>'
        for x in slugs) or '<span class="sub">—</span>'


_commit_rows = [p for p in (ln.split("\x1f") for ln in _log.splitlines() if ln)
                if len(p) == 3]
change_commits = table(
    ["Commit", "Date", "Subject", "Entity"],
    [[f"<code>{E(p[0])}</code>", E(p[1]), md(trunc(p[2], 66)),
      _entity_chips(entities_touched(p[0]))] for p in _commit_rows],
    note="Source: git log — newest first. Entity is derived from the files the "
         "commit touched against the same code map the feature pages render, "
         "so a commit with no entity column changed something no adopted "
         "section claims yet.")

# PLAN cell flips: which phase rows changed, in the commits that touched PLAN.md.
_plan_log = sh("git", "log", "-6", "--format=%h\x1f%ad\x1f%s", "--date=short",
               "--", ".kdbp/PLAN.md")
_cell_rows = []
for _ln in _plan_log.splitlines():
    if not _ln:
        continue
    _p = _ln.split("\x1f")
    if len(_p) != 3:
        continue
    _diff = sh("git", "show", _p[0], "--format=", "--", ".kdbp/PLAN.md")
    _ids = []
    for _dl in _diff.splitlines():
        if _dl[:1] in "+-" and _dl[1:2] == "|":
            _c = [x.strip() for x in _dl[1:].strip().strip("|").split("|")]
            if len(_c) > 1 and _c[0] and _c[0] != "#":
                _pid = _c[1].partition("·")[0].strip() or _c[0]
                if _pid not in _ids:
                    _ids.append(_pid)
    _cell_rows.append([f"<code>{E(_p[0])}</code>", E(_p[1]), md(trunc(_p[2], 46)),
                       E(", ".join(_ids[:6]) or "—")])
change_cells = table(
    ["Commit", "Date", "Subject", "Phase rows touched"], _cell_rows,
    note="Commits that edited .kdbp/PLAN.md — the phase rows whose cells moved.")

_verify_rows = [[E(r[1]), md(trunc(r[2], 44)), f"<code>{E(r[3])}</code>",
                 md(trunc(r[4], 88))] for r in ledger[:6]]
change_verify = table(
    ["Type", "Change", "Commit", "Gates recorded"], _verify_rows,
    note="Source: .kdbp/LEDGER.md Gates column — what the gate actually recorded.")

# --------------------------------------------------------------------------- #
# Releases station — DEPLOYMENTS.md (stakeholder showcase)
# --------------------------------------------------------------------------- #


def load_deployments() -> list[dict]:
    """.kdbp/DEPLOYMENTS.md table -> rows, parsed never interpreted."""
    path = REPO_ROOT / ".kdbp" / "DEPLOYMENTS.md"
    out: list[dict] = []
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        if not line.startswith("|") or line.startswith("|--") or "| Date |" in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").replace("\\|", "|").split("|")]
        if len(cells) >= 6 and cells[0] and cells[0] != "#":
            out.append({"id": cells[0], "date": cells[1], "target": cells[2],
                        "pr": cells[3], "ci": cells[4], "notes": cells[5],
                        # gabe-push 7.5b writes a 7th Decisions column; older
                        # tables carry 6 — absent reads as the "—" it renders.
                        "decisions": cells[6] if len(cells) >= 7 else "—"})
    return out


deploys = load_deployments()
_recent = list(reversed(deploys))[:12]
_with_pr = [d for d in deploys if d["pr"] not in ("—", "-", "")]

releases_kpis = '<div class="kpis">' + "".join([
    kpi("deploys", str(len(deploys)), "DEPLOYMENTS.md rows"),
    kpi("latest", deploys[-1]["date"][:10] if deploys else "—",
        deploys[-1]["target"][:26] if deploys else ""),
    kpi("via PR", str(len(_with_pr)), f"of {len(deploys)}"),
    kpi("covered", f"{adopted}/{len(sections)}", "center sections"),
]) + "</div>"

latest_release = table(
    ["Field", "Value"],
    [["<b>id</b>", E(deploys[-1]["id"])], ["<b>date</b>", E(deploys[-1]["date"])],
     ["<b>branch → target</b>", md(deploys[-1]["target"])],
     ["<b>PR</b>", md(deploys[-1]["pr"])], ["<b>CI result</b>", md(deploys[-1]["ci"])],
     ["<b>notes</b>", md(trunc(deploys[-1]["notes"], 220))]]
    + ([["<b>decisions</b>", md(trunc(deploys[-1]["decisions"], 220))]]
       if deploys[-1]["decisions"] not in ("—", "-", "") else []),
    note="Newest row of .kdbp/DEPLOYMENTS.md."
) if deploys else gap("Latest release", ".kdbp/DEPLOYMENTS.md")

release_index = table(
    ["#", "Date", "Branch → Target", "PR", "CI result", "Decisions"],
    [[f'<b>{E(d["id"])}</b>', E(d["date"][:10]), md(trunc(d["target"], 40)),
      md(d["pr"]), md(trunc(d["ci"], 40)),
      md(trunc(d["decisions"], 40))] for d in _recent],
    note=f"{len(deploys)} deployment(s) recorded · showing {len(_recent)} newest. "
         f"Decisions come from /gabe-push 7.5b note actions.")

# --------------------------------------------------------------------------- #
# Docs station — feature-docs accumulator + foundations
# --------------------------------------------------------------------------- #

_FOUNDATIONS = CFG.get("foundations", [
    "SCOPE", "DECISIONS", "RULES", "BEHAVIOR", "STRUCTURE",
    "PLAN", "PENDING", "DOCS", "ENTITIES", "ROADMAP"])
_found_rows = []
for _name in _FOUNDATIONS:
    _p = REPO_ROOT / ".kdbp" / f"{_name}.md"
    if not _p.exists():
        continue
    _found_rows.append([
        f"<b>{E(_name)}.md</b>", str(len(_p.read_text().splitlines())),
        E(sh("git", "log", "-1", "--format=%ad", "--date=short", "--",
             f".kdbp/{_name}.md") or "—")])
foundations = table(["Document", "Lines", "Last change"], _found_rows, num={1},
                    note="Source: .kdbp/ — the durable project memory.")

_cards = sorted((CENTER / "cards").glob("*.md")) if (CENTER / "cards").exists() else []
feature_docs = table(
    ["Card", "Entity", "Lines"],
    [[f"<b>{E(c.stem)}</b>", "—", str(len(c.read_text().splitlines()))] for c in _cards],
    num={2},
    note="Feature cards accumulate here as sections are adopted "
         "(/gabe-cc-init section <entity>)."
) if _cards else gap("Feature docs", "docs/site/center/cards/*.md — 0 sections adopted")

_decisions = len(re.findall(r"^\| *D\d+",
                            (REPO_ROOT / ".kdbp" / "DECISIONS.md").read_text(), re.M)) \
    if (REPO_ROOT / ".kdbp" / "DECISIONS.md").exists() else 0
docs_kpis = '<div class="kpis">' + "".join([
    kpi("foundations", str(len(_found_rows)), ".kdbp documents"),
    kpi("decisions", str(_decisions), "DECISIONS.md rows"),
    kpi("feature cards", str(len(_cards)), f"{adopted}/{len(sections)} adopted",
        alert=not _cards),
    kpi("wells / runbooks",
        f'{len(list((REPO_ROOT / "docs" / "wells").glob("*.md")))} / '
        f'{len(list((REPO_ROOT / "docs" / "runbooks").glob("*.md")))}'),
]) + "</div>"

manual_angles = table(
    ["Subject", "Who", "When", "Result", "Evidence"],
    [[f'<b>{E(w.get("subject", "?"))}</b>', E(w.get("who", "?")),
      E(str(w.get("when", ""))[:10]), E(w.get("result", "?")),
      md(str(w.get("evidence") or "—"))] for w in reversed(walks)],
    note=f"{len(walks)} recorded walk(s) — the one verification input with no "
         f"machine source (.kdbp/walks.jsonl, append-only)."
) if walks else gap("Manual angles", ".kdbp/walks.jsonl")

# --------------------------------------------------------------------------- #
# Feature pages — one per entity that has a card, built FROM feature.html.
# The card is the authored translation; every count beside it is machine-read.
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# Slot maps
# --------------------------------------------------------------------------- #

SHARED = {
    "{{LANG}}": _PROJECT.get("lang", "en"),
    "{{PROJECT_NAME}}": PROJECT_DISPLAY,
    "{{HEAD_SHA}}": HEAD_SHA,
    "{{REGEN_STAMP}}": STAMP,
    "{{GENERATOR_NAME}}": "build_center_a3.py",
    "{{ENTITY_COUNT}}": str(len(sections)),
    "{{TESTS_COUNT}}": f"{t_total:,}",
    "{{SIDEBAR_ENTITIES}}": sidebar_entities,
    # {{SIDEBAR_TESTS_SUB}} is retired — the Testing navsub (cases · files ·
    # claims · untested, the estate pages) is STATIC in the skeletons (map v3),
    # so it cannot drift.
    "{{SIDEBAR_CODE}}": _sidebar_code(),
    "{{SIDEBAR_LEAF}}": sidebar_leaf,
    # Repo-wide totals. On an ENTITY page these are overridden with that
    # entity's own line — a green "1,448 · 0 failed" beside KPIs reading 87/141
    # was read as this entity's verdict, which is the loudest kind of false
    # pass a page can make.
    "{{STATUS_PILLS}}": (
        f'<span class="statuspill {"warn" if t_failed else "ok"}">'
        f'repo · {t_total:,} tests · {t_failed} failed</span> '
        f'<span class="statuspill {"warn" if owed else "ok"}">'
        f'phase {plan["current_phase"]}</span>'),
    # NOT a freshness fact about the DATA: this is the generator's own
    # clock (STAMP above), identical on all 9 pages, and the default
    # `refresh_center.sh regen` path does not re-run any suite. The
    # skeletons label it "regen" for that reason — "synced" implied the
    # numbers had just been re-read, which regen alone never does.
    "{{SYNC_AGE}}": STAMP,
}

PER_FILE = {
    "index.html": {
        "{{HUB_TITLE}}": f"{PROJECT_DISPLAY} Command Center",
        "{{HUB_LEDE}}": (f"Verification-first view of {PROJECT_DISPLAY} — every number below "
                         "is read from PLAN.md, PENDING.md, LEDGER.md and junit at build "
                         "time. Sidebar entities are the approved adoption baseline."),
        "{{HUB_HEADLINE_STATS}}": hub_stats,
        "{{RECENT_CHANGES}}": recent_changes,
        "{{NEEDS_YOU}}": needs_you,
        "{{TAB_TESTS}}": tab_tests,
        "{{TAB_EVIDENCE}}": tab_evidence,
        "{{TAB_RISK}}": tab_risk,
    },
    "entity-index.html": {
        "{{ENTITIES_TITLE}}": "Entity index",
        "{{ENTITIES_LEDE}}": (f"The approved adoption baseline — {len(sections)} entities, "
                              f"{adopted} adopted. Each section is built one per run via "
                              f"/gabe-cc-init section, then walk-approved."),
        "{{ENTITIES_KPIS}}": entities_kpis,
        "{{ENTITY_GRID}}": entity_grid,
    },
    "docs.html": {
        "{{DOCS_TITLE}}": "Docs",
        "{{DOCS_LEDE}}": (f"Foundations ({len(_found_rows)} .kdbp documents) plus the "
                          f"feature-docs accumulator — cards land here one per adopted "
                          f"section."),
        "{{DOCS_KPIS}}": docs_kpis,
        "{{FEATURE_DOCS}}": feature_docs,
        "{{FOUNDATIONS}}": foundations,
    },
    "tests.html": {
        "{{TESTS_TITLE}}": "Testing",
        "{{TESTS_LEDE}}": (f"The estate dashboard — {t_total:,} junit cases "
                           f"({_corpus_breakdown}), {t_failed} failed. Full "
                           "views live on the estate pages: cases · files · "
                           "claims · untested. Absent sources are named, "
                           "not zeroed."),
        "{{TESTS_KPIS}}": tests_kpis,
        "{{TESTS_BODY}}": tests_body,
    },
    "ledger.html": {
        "{{CHANGE_TITLE}}": f"Latest change · {HEAD_SHA}",
        "{{CHANGE_LEDE}}": (f"{md(trunc(_head_subject, 96))} — one page per change, from "
                            f"git, the PLAN cells it moved, and its LEDGER gates row."),
        "{{CHANGE_KPIS}}": change_kpis,
        "{{CHANGE_COMMITS}}": change_commits,
        "{{CHANGE_CELLS}}": change_cells,
        "{{CHANGE_VERIFY}}": change_verify,
    },
    "releases.html": {
        "{{RELEASES_TITLE}}": "Releases",
        "{{RELEASES_LEDE}}": (f"Stakeholder showcase — {len(deploys)} deployment(s) recorded "
                              f"in .kdbp/DEPLOYMENTS.md, newest first."),
        "{{RELEASES_KPIS}}": releases_kpis,
        "{{LATEST_RELEASE}}": latest_release,
        "{{RELEASE_INDEX}}": release_index,
    },
}


def render_architecture(amap: dict) -> dict[str, str]:
    """The Architecture ESTATE (operator ruling 2026-07-23): a DASHBOARD page
    plus SIX subpages — the same sections as every entity's Code tab, rendered
    app-wide by the same builder (merged maps, pseudo-slug 'app'), each table
    carrying the icon-only entity column and an entity FILTER bar where the
    six-pill subnav used to float. All pages fill the architecture skeleton;
    cross-section links route to the page that owns the anchor."""
    merged = _a3_code.merge_amaps(REPO_ROOT)
    xpage = {"ep": "arch-endpoints.html", "cm": "arch-code-map.html",
             "dm": "arch-data-model.html", "fn": "arch-functions.html"}
    full = _a3_code.build_code_tab("app", REPO_ROOT, "", amap=merged,
                                   entity_col=True, xpage=xpage)
    # Slice the six sections apart on their sechead roots.
    marks = []
    for fname, _t, anchor, _ic, _s in _ARCH_PAGES:
        k = full.find(f'id="{anchor}"')
        marks.append((full.rfind('<div class="sechead"', 0, k), fname))
    script_i = full.find(
        "<script>(function(){document.querySelectorAll('.dmchips')")
    chips_script = full[script_i:] if script_i != -1 else ""
    slices = {}
    for n, (start, fname) in enumerate(marks):
        end = marks[n + 1][0] if n + 1 < len(marks) else (
            script_i if script_i != -1 else len(full))
        slices[fname] = full[start:end]

    # The entity FILTER bar — replaces the floating subnav on these pages.
    ents = sorted(set(merged.get("_file_entity", {}).values()),
                  key=lambda s: LABELS.get(s, s))
    bar = ('<div class="entchips"><button class="chip on" data-ent="all">All'
           "</button>"
           + "".join(
               f'<button class="chip" data-ent="{s}">'
               + entity_badge(s, LABELS.get(s, s), 12, show_name=True)
               + "</button>" for s in ents)
           + "</div>"
           # Rows are collected AT CLICK TIME (this script precedes the tables
           # in the document — an eager query would bind an empty list), only
           # rows whose identity cell carries an entity badge are touched
           # (dictionary + row-detail tables have none), and hiding rides an
           # 'ehide' class so it composes with the kind filter's 'khide'.
           "<script>(function(){var c=document.querySelector('.entchips');"
           "if(!c)return;c.addEventListener('click',function(ev){"
           "var b=ev.target.closest('.chip');if(!b)return;"
           "c.querySelectorAll('.chip').forEach(function(x){x.classList.remove('on')});"
           "b.classList.add('on');var s=b.dataset.ent;"
           "[].slice.call(document.querySelectorAll('.xrow, table.tbl tbody tr'))"
           ".forEach(function(r){var cell=r.querySelector("
           "':scope > summary > span:first-child, "
           ":scope > .xsummary > span:first-child, :scope > td:first-child');"
           "if(!cell||!cell.querySelector('.entb'))return;"
           "r.classList.toggle('ehide',"
           "!(s==='all'||cell.querySelector('.ent-'+s)))});});})();</script>")

    base_skel = strip_slot_doc_comments(
        (SHELL_SRC / "architecture.html").read_text())

    def _page(fname: str, title: str, kpis: str, body: str) -> str:
        h = base_skel
        fills = {**SHARED, "{{SIDEBAR_CODE}}": _sidebar_code(current=fname),
                 "{{ARCH_KPIS}}": kpis, "{{ARCH_BODY}}": body}
        for tok, val in fills.items():
            h = h.replace(tok, val)
        if fname != "architecture.html":
            h = h.replace("<title>Architecture ·", f"<title>{title} ·")
            h = h.replace("<b>Architecture</b>",
                          '<a href="architecture.html">Architecture</a> › '
                          f"<b>{title}</b>")
            h = h.replace("<h1>Architecture</h1>", f"<h1>{title}</h1>")
        return h

    # The architecture estate's menu (operator ruling 2026-07-24: the same
    # sticky cross-page menu the testing estate carries) — overview first,
    # then every subpage with its own icon.
    _arch_items = ([("architecture.html", "Architecture overview", _IC_CODE)]
                   + [(fname, title, _a3_code._INS_ICONS[icon])
                      for fname, title, _a, icon, _s in _ARCH_PAGES])

    pages: dict[str, str] = {}
    for fname, title, _anchor, _ic, _sub in _ARCH_PAGES:
        body = sticky_stack(estate_menu(_arch_items, fname), bar) + slices[fname]
        if fname in ("arch-data-model.html", "arch-functions.html"):
            body += chips_script
        pages[fname] = _page(fname, title, "", body)

    # Dashboard: KPIs + one card per subpage.
    ins = _a3_code.model_insight(REPO_ROOT)
    fins = _a3_code.function_insight(REPO_ROOT)
    n_files = len(merged["files"])
    n_lines = sum(n for _l, _f, n in merged["files"])
    n_cls = len(merged["models"]) + len(merged["schemas"])
    # Candidate counts = exactly what the candidate pages list: MERGE (a
    # recorded nearest neighbour, i.e. similarity above the page's floor) plus
    # SPLIT (god). Never "nothing references it": the map covers only the
    # config-adopted files, so absence THERE is absence of evidence, not
    # evidence of deadness (R10 — the center reports, it does not assert).
    n_dmc = _n_cands(ins, _a3_code._MERGE_FLOOR, lambda k, c: k)
    n_fnc = _n_cands(fins, _a3_code._FN_MERGE_FLOOR, lambda _k, c: c["fn"])
    kpis = '<div class="kpis">' + "".join([
        kpi("entities", str(len(ents)), "mapped"),
        kpi("endpoints", str(len(merged["endpoints"])), "HTTP surface"),
        kpi("classes", str(n_cls), "models + schemas"),
        kpi("defs", str(len(fins)), "functions + methods"),
        kpi("files", f"{n_files}", f"{n_lines:,} lines"),
    ]) + "</div>"
    counts = {"arch-endpoints.html": f'{len(merged["endpoints"])} endpoint(s)',
              "arch-code-map.html": f"{n_files} file(s) · {n_lines:,} lines",
              "arch-data-model.html": f"{n_cls} class(es)",
              "arch-dm-candidates.html": f"{n_dmc} candidate(s)",
              "arch-functions.html": f"{len(fins)} def(s)",
              "arch-fn-candidates.html": f"{n_fnc} candidate(s)"}
    cards = "".join(
        f'<a class="archcard" href="{fname}">{_mini_ic(icon)}'
        f"<div><b>{E(title)}</b>"
        f'<span class="sub">{E(counts[fname])} — {E(sub)}</span></div></a>'
        for fname, title, _a, icon, sub in _ARCH_PAGES)
    dash = ('<p class="sub">The whole application read once per build into '
            "<code>archmap.json</code>; each page below runs the SAME "
            "sections as an entity's Code tab, app-wide, filterable by "
            "entity.</p>"
            f'<div class="archgrid">{cards}</div>')
    pages["architecture.html"] = _page("architecture.html", "Architecture",
                                       kpis, dash)
    return pages


def render_testing() -> dict[str, str]:
    """The TESTING ESTATE (operator ruling Q2, 2026-07-23): tests.html is the
    dashboard (KPIs · entity×corpus grid · estate cards); the corpus lives
    file-by-file on test-matrix.html (entity-filterable, per-case C-id
    anchors, Exercises receipts), claims and corpora/gates get their own
    pages. Same slicing idea as the architecture estate: one skeleton, one
    dialect, subpages own the anchors cross-links land on."""
    base_skel = strip_slot_doc_comments(
        (SHELL_SRC / "architecture.html").read_text())

    def _tpage(fname: str, title: str, sub: str, body: str,
               current: str = "") -> str:
        h = base_skel
        fills = {**SHARED, "{{SIDEBAR_CODE}}": _sidebar_code(),
                 "{{ARCH_KPIS}}": "", "{{ARCH_BODY}}": body}
        for tok, val in fills.items():
            h = h.replace(tok, val)
        h = h.replace("<title>Architecture ·", f"<title>{title} ·")
        h = h.replace("<b>Architecture</b>",
                      f'<a href="tests.html">Testing</a> › <b>{title}</b>')
        h = h.replace("<h1>Architecture</h1>",
                      f"<h1>{title}</h1>"
                      f'<p class="sub" style="margin-top:2px">{sub}</p>')
        # The sidebar marks the page you are ON — the arch estate already
        # does this through _sidebar_code(current=...); the Testing
        # subitems are static, so the mark lands here.
        if current:
            h = h.replace(
                f'class="navitem navsubitem" href="{current}"',
                f'class="navitem navsubitem on" href="{current}"')
        return h

    ents = [s["entity"] for s in sections]
    bar = ('<div class="entchips"><button class="chip on" data-ent="all">All'
           "</button>"
           + "".join(f'<button class="chip" data-ent="{s}">'
                     + entity_badge(s, LABELS.get(s, s), 12, show_name=True)
                     + "</button>" for s in ents)
           + "</div>"
           "<script>(function(){var c=document.querySelector('.entchips');"
           "if(!c)return;c.addEventListener('click',function(ev){"
           "var b=ev.target.closest('.chip');if(!b)return;"
           "c.querySelectorAll('.chip').forEach(function(x){x.classList.remove('on')});"
           "b.classList.add('on');var s=b.dataset.ent;"
           "[].slice.call(document.querySelectorAll('.xrow, table.tbl tbody tr'))"
           ".forEach(function(r){var cell=r.querySelector("
           "':scope > summary > span:first-child, "
           ":scope > .xsummary > span:first-child, :scope > td:first-child');"
           "if(!cell||!cell.querySelector('.entb'))return;"
           "r.classList.toggle('ehide',"
           "!(s==='all'||cell.querySelector('.ent-'+s)))});});})();</script>")

    # The app-wide CLAIMS table (operator ruling 2026-07-24: the estate page
    # carries the SAME expandable record the entity tab renders — a claim
    # row opens to its cases — not an index of links). Entity column first;
    # C-ids inside the folds link the Cases page.
    _cl_rows = []
    _cl_tally = {"running": 0, "ambiguous": 0, "drift": 0, "unknown": 0}
    _cardless = []
    for s in sections:
        slug = s["entity"]
        card_path = CENTER / "cards" / f"{slug}.md"
        if not card_path.exists():
            _cardless.append(LABELS.get(slug, slug))
            continue
        card = D.parse_card(card_path)
        rx = ENTITY_RX.get(slug, re.escape(slug))
        inv = entity_corpus(rx, junit_by, CORPORA)
        complete = all(inv[c["key"]]["present"] for c in CORPORA)
        cv = claim_verdicts(card.get("CLAIMS", []), inv, CORPORA, complete,
                            cid_base="test-matrix.html")
        ebadge = (f'<a href="{_entity_href(slug)}">'
                  + entity_badge(slug, LABELS.get(slug, slug), 13) + "</a>")
        for cells, detail in cv["rows"]:
            _cl_rows.append(([ebadge, *cells], detail))
        for k in _cl_tally:
            _cl_tally[k] += cv[k]
    _cl_note = (f'{_cl_tally["running"]} claim(s) running · '
                f'{_cl_tally["drift"]} drifted · {_cl_tally["ambiguous"]} '
                f'ambiguous · {_cl_tally["unknown"]} unknown. A drifted '
                "claim is a test that was promised and is gone; per-entity "
                "verdicts (incl. running-but-unclaimed classes) render on "
                "each entity's Tests tab."
                + (" No claims card yet: " + ", ".join(map(E, _cardless))
                   + "." if _cardless else ""))
    claims_body = (
        sechead("Testing", "Claims — the authored coverage", "#0d9488",
                _IC_KCHECK,
                sub="every entity's claimed test classes, joined to the run "
                    "by class name — open a claim to read its cases",
                id_="sec-tests-claims",
                note=_cl_note,
                info=legend("Claim state:", [
                    ("s-ok", "running", "the class is in junit ·"),
                    ("s-med", "ambiguous / unknown",
                     "short-name match, or junit absent ·"),
                    ("s-gap", "DRIFT", "claimed, not running")]))
        + (xtable([ENT_COL, "Kind", "Class", "Intent", "State"], _cl_rows,
                  widths=["40px", "0.9fr", "1.3fr", "3.4fr", "1fr"])
           if _cl_rows else
           '<p class="sub">No <code># CLAIMS</code> authored on any card '
           "yet — each entity's card can declare the test classes it "
           "promises, and the build verifies them here.</p>"))

    # The machinery page: sources · gates · history · walks · shelf — every
    # piece under its own sechead so the station's deep links (the manual
    # kind row lands on #sec-tests-walks) have an anchor to arrive at.
    corpora_body = (
        sechead("Testing", "Corpora — the report sources", "#3f6d4c",
                _IC_LIST,
                sub="one row per corpus: the runner, its junit capture, "
                    "and where the report lands",
                id_="sec-tests-corpora")
        + buckets
        + sechead("Testing", "Gates", "#3f6d4c", _IC_SHIELD,
                  sub="what stands in front of a commit — pre-commit hooks "
                      "and CI jobs",
                  id_="sec-tests-gates")
        + gates
        + sechead("Now", "Verification changelog", "#0d7a84", _IC_CLOCK,
                  sub="run history — one row per source whose recorded "
                      "totals moved",
                  id_="sec-tests-changelog")
        + verification_changelog
        + sechead("Testing", "Manual angles (walks)", "#3f6d4c", _IC_WALK,
                  sub="the one verification input with no machine source — "
                      "who walked what, when, with what verdict",
                  id_="sec-tests-walks")
        + manual_angles
        + sechead("Testing", "Demo shelf", "#3f6d4c", _IC_SHELF,
                  sub="human-curated proof of the journey kind — each set "
                      "is claimed by an entity and renders in full on that "
                      "entity's Evidence tab",
                  id_="sec-tests-shelf",
                  info=legend("Row vocabulary:", [
                      ("s-med", "legacy",
                       "no manifest — the set predates the curate flow ·"),
                      ("s-gap", "no manifest",
                       "no authored description; the shot names are the "
                       "only narration ·"),
                      ("s-gap", "unclaimed",
                       "no entity's proofs list names this set")])
                  + '<div class="leg">To INTEGRATE a legacy set: add it '
                    "to <code>entities[].proofs</code> in "
                    "center.config.json — it then renders on that "
                    "entity's Evidence tab with its legs and galleries — "
                    "and author its manifest.json (/gabe-cc-update curate "
                    "writes one on the next green run). A <b>likely</b> "
                    "badge is a name-pattern guess (the entity's test_rx "
                    "matched the folder name), never a claim. The entity "
                    "filter matches owners and likely guesses alike; a "
                    "set with no feature page yet lights up when its "
                    "entity is adopted.</div>")
        + demo_shelf)

    # The case LEDGER (rulings R1–R3, 2026-07-24): the C-id is the row and
    # the canonical anchor; its own dropdown bar replaces the chip bar here.
    app_inv = {c["key"]: (junit_by.get(c["key"]) or {}).get("files", {})
               for c in CORPORA}
    ledger_body = (
        sechead("Testing", "Cases — the ledger", "#0d6e78", _IC_GRID4,
                sub="every case identity in the estate — filter by entity, "
                    "kind, state, or the element it exercises; C-id pills "
                    "everywhere in the center land on these rows",
                id_="sec-tests-cases",
                note="Rows are case IDENTITIES: parametrize executions group "
                     "under their C-id, the test file is the metadata line "
                     "under the assertion. Solid chips are a case's own "
                     "facts (T1); dashed chips ride in from its file "
                     "(via file) — the filters match both.")
        + _a3_ledger.ledger_html(REPO_ROOT, app_inv, CORPORA,
                                 owners_of=entities_of, labels=LABELS,
                                 app=True))
    gaps_body = (
        sechead("Testing", "Untested surface — app-wide", "#b45309", _IC_ALERTP,
                sub="every element no case or spec touches — gaps only; the "
                    "tested roster lives on the architecture pages with its "
                    "receipts",
                id_="sec-tests-gaps",
                note="Rows come from the same AST map the architecture pages "
                     "render; a row disappears by itself the moment a case "
                     "or spec touches its element.")
        + _a3_tests.untested_surface(REPO_ROOT, "app", app=True))
    # The testing estate's menu items — rendered by the shared estate_menu().
    _est_items = [("tests.html", "Testing overview", _IC_KCHECK),
                  ("test-matrix.html", "Cases", _IC_GRID4),
                  ("test-files.html", "Files", _IC_DOCP),
                  ("test-claims.html", "Claims", _IC_KCHECK),
                  ("test-elements.html", "Untested", _IC_ALERTP),
                  ("test-corpora.html", "Corpora & gates", _IC_SHIELD)]

    def _esub(current: str) -> str:
        return estate_menu(_est_items, current)

    return {
        "test-elements.html": _tpage(
            "Untested", "Untested",
            "the untested surface: endpoints, models and functions no case "
            "or spec touches, entity-filterable",
            sticky_stack(_esub("test-elements.html"), bar) + gaps_body,
            current="test-elements.html"),
        "test-matrix.html": _tpage(
            "Cases", "Cases",
            "the case ledger — every identity with its C-id anchor and "
            "exercises chips, element-filterable; the file altitude lives "
            "on the Files page",
            _esub("test-matrix.html") + ledger_body,
            current="test-matrix.html"),
        # Files gets its OWN page (operator ruling 2026-07-24: one page per
        # estate section, the Code-group treatment) — the entity filter bar
        # rides on top, the anchor keeps its sec-tests-files identity.
        "test-files.html": _tpage(
            "Test files", "Files",
            "the file altitude — every test file with its ratios, flags "
            "and claim state, entity-filterable; open a row to read the "
            "cases inside it",
            sticky_stack(_esub("test-files.html"), bar) + files_section,
            current="test-files.html"),
        "test-claims.html": _tpage(
            "Test claims", "Claims",
            "the authored coverage, verified app-wide — open a claim to "
            "read its cases, filter by entity",
            sticky_stack(_esub("test-claims.html"), bar) + claims_body,
            current="test-claims.html"),
        "test-corpora.html": _tpage(
            "Corpora & gates", "Corpora & gates",
            "the machinery — report sources, the gates in front of a "
            "commit, the run history, the recorded walks, and the demo "
            "shelf", _esub("test-corpora.html") + corpora_body,
            current="test-corpora.html"),
    }


def main() -> int:
    if not SHELL_SRC.exists():
        print(f"⛔ shell templates missing: {SHELL_SRC}")
        return 2
    # GABE_CENTER_OUT is a lab override — if it is set, SAY SO loudly, so a leaked
    # env var can never silently write the whole center to a scratch dir while
    # printing "regen OK" (its sibling GABE_SHELL_SRC already announces itself).
    if CENTER_OUT != CENTER:
        print(f"  ⚠ WRITE redirected to {CENTER_OUT} (GABE_CENTER_OUT set) — "
              f"reads still come from {CENTER}. LAB run: the real center was "
              f"NOT touched.")
    elif LAB:
        # GABE_REPO_ROOT points at a foreign tree but GABE_CENTER_OUT is UNSET — the whole center is
        # about to be written INTO that project. Say so; the twin recipe always pairs the two.
        print(f"  ⚠ LAB run (GABE_REPO_ROOT set) with NO GABE_CENTER_OUT — the center is being written "
              f"INTO the foreign project at {CENTER}. Set GABE_CENTER_OUT to redirect writes to a scratch dir.")
    CENTER_OUT.mkdir(parents=True, exist_ok=True)
    (CENTER_OUT / "assets").mkdir(exist_ok=True)
    # Assets may nest (e.g. assets/evidence-states/*.png — the navigator's
    # captures). Copy files, RECURSE into directories: iterdir + read_bytes
    # crashes the whole build on the first sub-directory it meets.
    for asset in (SHELL_SRC / "assets").iterdir():
        dst = CENTER_OUT / "assets" / asset.name
        if asset.is_dir():
            shutil.copytree(asset, dst, dirs_exist_ok=True)
        else:
            dst.write_bytes(asset.read_bytes())

    wrote = []
    for src in sorted(SHELL_SRC.glob("*.html")):
        # architecture.html and board.html are owned by later passes —
        # render_architecture and render_board both need the archmap, which is
        # assembled after this loop. The generic pass would ship them slot-empty.
        if src.name in ("architecture.html", "board.html"):
            continue
        text = strip_slot_doc_comments(src.read_text())
        for tok, val in SHARED.items():
            text = text.replace(tok, val)
        for tok, val in PER_FILE.get(src.name, {}).items():
            text = text.replace(tok, val)
        (CENTER_OUT / src.name).write_text(text)
        wrote.append((src.name, text.count("{{")))

    ctx = SimpleNamespace(
        center=CENTER, center_out=CENTER_OUT, shell_src=SHELL_SRC,
        repo_root=REPO_ROOT, sections=sections, labels=LABELS,
        junit_by=junit_by, corpora=CORPORA, e2e=E2E, proof_root=proof_root,
        cfg=CFG, walks=walks, shared=SHARED, parse_card=D.parse_card,
        maturity=MATURITY, flow_coverage={},
    )
    for name in build_feature_pages(ctx):
        wrote.append((name, 0))

    # The committed architecture map — machine-derived (ast), regenerated every
    # build, diffable in PRs. Consumers read THIS instead of re-analyzing code.
    # `coverage` carries each carded entity's flow-coverage verdict so agents
    # read the machine numbers here instead of scraping the Evidence tab.
    # version 2 (2026-08-27): the archmap schema now carries the route/file census. The census
    # keys are non-empty-only (P5), so their ABSENCE cannot alone tell "full coverage" from "an
    # archmap a pre-census build wrote" — pulse S13 reads this version to make that call honestly.
    amap = {"version": 2, "head": HEAD_SHA, "generated": STAMP,
            "coverage": ctx.flow_coverage,
            "model_insight": _a3_code.insight_serial(REPO_ROOT),
            "test_insight": _a3_tests.test_insight(REPO_ROOT),
            "function_insight": _a3_code.fn_insight_serial(REPO_ROOT),
            # the table-class census BEYOND the config allowlists — what the map would have
            # silently dropped (the cc-init lens / pulse S11 read this; honest-empty {})
            "model_census": _a3_code.model_census(REPO_ROOT),
            "entities": {s: collect_entity_map(s, REPO_ROOT) for s in ENTITY_CODE}}
    # SCHEMA HOMING — a schema lives where its CONSUMER lives, not where its file was claimed.
    # Runs ONCE here, on the archmap's own facts, BEFORE every consumer of entities[*]["schemas"]
    # (C4 · levels · data-model page · cc-entity) reads it — one class, one home, on every page.
    # The stats block feeds pulse S12 + c4.stats; honest-empty {} when nothing moves.
    amap["schema_homing"] = _a3_code.home_schemas(amap["entities"], _a3_code.function_insight(REPO_ROOT))
    # ROUTE + FILE census — the coverage-loss the map would silently drop (same ruling as
    # model_census: config decides ownership, never existence). Emitted ONLY when non-empty
    # (P5): a project with full coverage carries NO census key, byte-identical. The file census's
    # unclaimed entries gain an optional `reach` (min call-hops from a mapped handler) from a
    # read-as-found graft pass — the "how close to the request path" rank the cc-init adopt rail
    # and pulse S13 read; honest-empty without a built index. A claim under a layer center.config
    # never declared is a silent no-op today → report it so the operator sees the drop.
    _fsm = _a3_code.fn_similarity_mode()            # exact | blocked — the twin pass above its budget is an approximation, said here
    if _fsm.get("mode") == "blocked":
        amap["fn_similarity"] = _fsm
    _mts = _a3_code.mount_stats(REPO_ROOT)          # the app → include_router chain the labels were resolved through (review 2026-09-06)
    if _mts:
        amap["route_mounts"] = _mts
    _unp = _a3_code.unparseable_files()
    if _unp:
        amap["unparseable"] = _unp                    # every mapped .py the scanners skipped — a NAMED gap
    _rcen = _a3_code.route_census(REPO_ROOT)
    if _rcen:
        amap["route_census"] = _rcen
    _fcen = _a3_code.file_census(REPO_ROOT)
    if _fcen:
        _reach = _a3_graft.reach_arm(REPO_ROOT, amap["entities"],
                                     [u["file"] for u in _fcen["unclaimed"]])
        # enrich into FRESH dicts — never mutate _fcen's rows, which are the module cache
        # (_a3_code._FILE_CENSUS); a second reader of file_census() must see the un-enriched census.
        amap["file_census"] = {**_fcen, "unclaimed": [
            ({**_u, "reach": _reach[_u["file"]]} if _u["file"] in _reach else _u)
            for _u in _fcen["unclaimed"]]}
    for _slug, _layer in _a3_code.undeclared_layers():
        print(f"    ⚠ center.config entity '{_slug}' claims layer '{_layer}' not in "
              f"code_layers — those files are dropped (add '{_layer}' to code_layers)")
    # FEATURE-FLAG census (class 12) — the config bools whose OFF walls a route/lane; the C4 flag
    # node reads this for its det. Non-empty-only (P5): no Settings bool / module Final[bool] → no key.
    _flg = _a3_code.parse_flags(REPO_ROOT)
    if _flg:
        amap["flags"] = _flg
    # class 8 (middleware): resolve each endpoint's GATE dep to its fn id — the K1 gate chain that
    # derive_depends (in the graft arm) draws — and census the app-level middleware stack. BEFORE
    # the archmap write so the endpoint nodes carry mw['fn'], BEFORE the graft arm reads the entries.
    _a3_code.resolve_middleware_targets(amap["entities"], REPO_ROOT)
    _amw = _a3_code.parse_app_middleware(REPO_ROOT)
    if _amw:
        amap["app_middleware"] = _amw
    # class 6 (dispatches): event-bus publisher→handler edges — folded into the graft adjacency +
    # drawn as a distinct `dispatches` wire. Emitted to the archmap non-empty-only (P5).
    _dm = _a3_code.dispatch_map(REPO_ROOT)
    if _dm:
        amap["dispatch"] = _dm
    # class 7 (boot): the lifespan/startup root — main.py is unclaimed, so its seeder write-path
    # never drew. Emit non-empty-only (P5); the graft arm homes main.py → __unclaimed__ for it.
    # class 13 (tasks): queue dispatch BY NAME (Celery/ARQ/Taskiq) — enqueue site → task fn, folded beside the
    # event-bus edges; the task fns are trace ROOTS. Emitted non-empty-only (P5).
    _tm = _a3_code.task_map(REPO_ROOT)
    if _tm:
        amap["tasks"] = {"tasks": _tm.get("tasks") or [], "stats": _tm.get("stats") or {}}
        amap["task_roots"] = _a3_code.parse_task_roots(REPO_ROOT)
    _boot = _a3_code.parse_boot_roots(REPO_ROOT)
    if _boot:
        amap["boot_roots"] = _boot
    # The GUARD lens — "if I change this, would anything tell me?" Joined from
    # the three maps above, so it costs one pass and re-reads no source.
    amap["guard_insight"] = _a3_guard.guard_insight(
        function_insight=amap["function_insight"],
        by_function=amap["test_insight"].get("by_function", {}),
        by_endpoint=amap["test_insight"].get("by_endpoint", {}),
        exercises=amap["test_insight"].get("exercises", {}),
        entities=amap["entities"],
        by_model=amap["test_insight"].get("by_model", {}),
        model_insight=amap["model_insight"],
        proofs=D.load_guard_proofs())
    (CENTER_OUT / "archmap.json").write_text(
        # sort_keys: without it the archmap re-orders on every regen and a review
        # diff carries ~1,750 lines of pure churn (gustify #150) — the one
        # artifact the center's correctness rests on became the least
        # reviewable. The sibling rows-seen.json dump below already sorts.
        json.dumps(amap, indent=1, ensure_ascii=False, sort_keys=True) + "\n")
    n_eps = sum(len(v["endpoints"]) for v in amap["entities"].values() if v)
    n_models = sum(len(v["models"]) for v in amap["entities"].values() if v)
    print(f"    wrote docs/site/center/archmap.json — {len(amap['entities'])} "
          f"entity(ies) · {n_eps} endpoints · {n_models} models")

    # The C4 codebase graph — a LIBRARY-NEUTRAL {nodes,edges} view derived from
    # the in-memory archmap (zero new source read), emitted as committed JSON +
    # a window-global sibling (the inflight.js file:// recipe). Renderers pick it
    # up; a deterministic build-time layout stamps x/y so the no-runtime-layout
    # render path needs no graph library under strict-CSP/file://. A derivation
    # bug must NOT blank the whole center, so it degrades LOUD (E3), never silent.
    try:
        _gcolors = {s: R_MARKS.entity_color(s)
                    for s, c in amap.get("entities", {}).items() if c}
        _gcolors["__unclaimed__"] = "#8a8f98"   # the coverage-loss bucket, muted
        # the graft-wiring arm: self-provision (the red beat's recipe) + derive the
        # cross-entity calls/imports slice. GABE_GRAFT_BUILD=0 reads as-found — a
        # dry-run against a twin must never write its tree. The arm never raises;
        # absence is a named stats entry, and the FK topology is unchanged.
        _garm = _a3_graft.graft_arm(
            REPO_ROOT, amap.get("entities") or {},
            # LAB (twin/dry-run) → build ONLY on explicit GABE_GRAFT_BUILD=1, so a forgotten flag can't
            # mutate the foreign tree (graft writes graft/ + .gitignore + .ignore into REPO_ROOT).
            # Self-build → default ON as before ("1" unless explicitly "0").
            allow_build=((os.environ.get("GABE_GRAFT_BUILD") == "1") if LAB
                         else (os.environ.get("GABE_GRAFT_BUILD", "1") != "0")),
            faccess={_k: {"ops": (_v.get("access") or {}).get("ops"),
                          "commits": (_v.get("access") or {}).get("commits"),
                          "sinks": _v.get("sinks"),
                          "externals": _v.get("externals")}   # class 9: providers this fn reaches
                     for _k, _v in _a3_code.function_insight(REPO_ROOT).items()
                     if _v.get("access") or _v.get("sinks") or _v.get("externals")},   # A2+C4+prov: joined onto the call-tree
            dispatches=(_dm.get("dispatches") or []) + (_tm.get("dispatches") or []),   # class 6 + 13: event-bus and task edges, one wire
            boot_roots=(amap.get("boot_roots") or []) + (amap.get("task_roots") or []))  # class 7 + 13: boot + task roots homed for behind/calls
        # the web→API bridge arm (Path A frontend): a SEPARATE module with its own
        # try/except so a fetch-parser bug degrades the bridge to honest-empty and
        # NEVER masquerades as graft absence (two arms, two presence flags). Read-only
        # source glob → no allow_build gate; honest-empty on a backend-only twin.
        try:
            _warm = _a3_web.web_arm(REPO_ROOT, amap.get("entities") or {})
        except Exception as _we:  # noqa: BLE001
            _warm = {"present": False, "reason": f"web arm error: {_we}"}
        # TRIPWIRE: c4-graph.json is machine-shaped by the (gitignored) graft index —
        # if this regen flips graft presence vs the committed file, say so LOUDLY, or
        # a graft-less host silently strips every calls/imports edge from the map.
        with contextlib.suppress(Exception):
            _prev = json.loads((CENTER_OUT / "c4-graph.json").read_text(encoding="utf-8"))
            _was = bool((_prev.get("stats", {}).get("graft") or {}).get("present"))
            if _was != bool(_garm.get("present")):
                print(f"    ⚠ GRAFT PRESENCE FLIP: committed c4-graph has graft "
                      f"present={_was}, this regen derives present={bool(_garm.get('present'))} "
                      f"({_garm.get('reason')}) — the calls/imports kinds will "
                      f"{'appear' if _garm.get('present') else 'DISAPPEAR'} in the diff")
            # the web arm's OWN presence flip — reuse the already-loaded _prev; a
            # web-less host silently strips every web piece + bridge edge otherwise.
            _wwas = bool((_prev.get("stats", {}).get("web") or {}).get("present"))
            if _wwas != bool(_warm.get("present")):
                print(f"    ⚠ WEB PRESENCE FLIP: committed c4-graph has web "
                      f"present={_wwas}, this regen derives present={bool(_warm.get('present'))} "
                      f"({_warm.get('reason')}) — the web pieces + bridge edges will "
                      f"{'appear' if _warm.get('present') else 'DISAPPEAR'} in the diff")
        # the frontend STRUCTURE arm (components · hooks · stores · routes · types · modules +
        # renders/uses/typed/fecall wires) — the twin's own `typescript` is the provider; its
        # OWN try/except + presence flag, honest-empty (no node/ts, GABE_FE_EXTRACT=0 for a
        # twin-read-only dry-run). It rides a SEPARATE `fe` key: FK+graft+web bytes untouched.
        try:
            _fearm = _a3_fe.fe_arm(REPO_ROOT, amap.get("entities") or {},
                                   screens=_warm.get("screens") or [])
        except Exception as _fe:  # noqa: BLE001
            _fearm = {"present": False, "reason": f"fe arm error: {_fe}"}
        with contextlib.suppress(Exception):
            _fwas = bool((_prev.get("stats", {}).get("fe") or {}).get("present"))
            if _fwas != bool(_fearm.get("present")):
                print(f"    ⚠ FRONTEND PRESENCE FLIP: committed c4-graph has fe "
                      f"present={_fwas}, this regen derives present={bool(_fearm.get('present'))} "
                      f"({_fearm.get('reason')}) — the frontend pieces + wires will "
                      f"{'appear' if _fearm.get('present') else 'DISAPPEAR'} in the diff")
        _graph = _a3_graph.build_c4_graph(
            amap, labels=LABELS,
            status={s["entity"]: s.get("status") for s in sections},
            colors=_gcolors, graft=_garm, web=_warm, fe=_fearm)
        # the LEVELS graph (window.GABE_LEVELS) — the lab-native station's rich feed:
        # functions · use-cases · communities · use-edges, ALL from the archmap insight
        # blocks (_a3_code already writes them) + the C4 topology; only cross-file call
        # edges need graft, honest-empty otherwise. A derivation error degrades the
        # station to topology-only (window.GABE_LEVELS absent), never blanks the center.
        _levels = None
        try:
            _levels = _a3_levels.build_levels(amap, _graph, graft=_garm)
        except Exception as _le:  # noqa: BLE001
            print(f"    ⚠ levels SKIPPED (derivation error, station degrades to topology): {_le}")
        # the membership EVIDENCE (Part C, 2026-09-06): three witnesses per piece — file · users · data —
        # weighed over the archmap + c4 + levels; the per-piece detail rides levels.json (the station
        # already loads it, gabe-map reads it lazily), the counts ride c4 stats.homing + `home_ev` on the
        # endpoint nodes / fe pieces whose witnesses disagree. NOTHING re-homes — evidence only.
        try:
            _hom = _a3_homing.evidence(amap, _graph, _levels)
        except Exception as _he:  # noqa: BLE001
            _hr = f"homing evidence error: {_he}"
            _hom = {"present": False, "reason": _hr, "pieces": {}, "stats": {"present": False, "pieces": 0, "reason": _hr}}
            print(f"    ⚠ homing evidence SKIPPED (derivation error): {_he}")
        _a3_homing.attach(_graph, _hom)
        if _levels is not None:
            _levels["homing"] = _hom
            _a3_levels.emit(_levels, CENTER_OUT)
            wrote.append(("levels.json", 0))
            print(f"    wrote docs/site/center/levels.json — {len(_levels['fn_nodes'])} fn(s) "
                  f"· {len(_levels['use_edges'])} use-edge(s)")
        _hs = _hom.get("stats") or {}
        print("    homing evidence: " + (f"{_hs.get('pieces')} piece(s) weighed · {_hs.get('agree', 0)} agree · {_hs.get('stay', 0)} stay · "
                                        f"{_hs.get('move', 0)} move candidate(s) · {_hs.get('shared', 0)} shared — evidence only, nothing re-homed"
                                        if _hs.get("present") else f"absent — {_hom.get('reason')}"))
        _a3_graph.emit(_graph, CENTER_OUT)      # emitted AFTER the evidence attach — the stats carry stats.homing
        wrote.append(("c4-graph.json", 0))
        _st = _graph["stats"]
        _gst = _st.get("graft") or {}
        _fst = _st.get("fe") or {}
        print(f"    frontend arm: " + (f"{_fst.get('pieces')} piece(s) · {_fst.get('edges')} wire(s) · "
              f"{(_fst.get('by_kind') or {}).get('component', 0)} components · "
              f"{_fst.get('screens_absorbed', 0)} screens absorbed ({_fst.get('reason')})"
              if _fst.get("present") else f"absent — {_fst.get('reason')}"))
        print(f"    wrote docs/site/center/c4-graph.json — {_st['entities']} node(s) "
              f"· {_st['l1_edges']} L1 edge(s)"
              + (f" · graft {_gst.get('cross_calls', 0)} calls/"
                 f"{_gst.get('cross_imports', 0)} imports ({_gst.get('reason')})"
                 if _gst.get("present") else f" · graft absent ({_gst.get('reason')})")
              + ("  ⚠ unclaimed bucket present" if _st["unclaimed"] else ""))
        _wst = _st.get("web") or {}
        if _wst.get("present"):
            print(f"    web bridge — {_wst.get('extractor')} · {_wst.get('screens', 0)} screen(s) "
                  f"· {_wst.get('matched', 0)} bridged / {len(_wst.get('unmatched') or [])} unmatched "
                  f"· {_wst.get('dynamic', 0)} dynamic")
        else:
            print(f"    web bridge absent ({_wst.get('reason')})")
    except Exception as _e:  # noqa: BLE001
        print(f"    ⚠ c4-graph SKIPPED (derivation error, center still built): {_e}")

    # The change-simulation projection the codebase-graph station overlays on the
    # graph — DERIVED LIVE (_a3_sim, C2): when a change is in flight (inflight.json
    # active) it derives touched/blast/pieces/stages from inflight + archmap + git +
    # junit + PENDING; otherwise window.GABE_SIM=null and the station degrades to the
    # plain map. sim.data.js is a beat-tail artifact, gitignored like inflight.{json,js}
    # (gabe-init seeds it), so the derivation from the churny tree never dirties a
    # commit. A derivation error degrades to honest-empty, never blanks the center.
    _simf = CENTER_OUT / "sim.data.js"
    _sim = None
    _inflight = None
    try:
        _ifsrc = CENTER / "inflight.json"          # write-inflight.py refreshes it at the beat tail
        if _ifsrc.is_file():
            _inflight = json.loads(_ifsrc.read_text())
        _ev = {}
        for _c in CORPORA:
            _dp = REPO_ROOT / "tests" / "results" / f"{_c['key']}-junit.xml.digest.json"
            if _dp.is_file():
                try:
                    _d = json.loads(_dp.read_text())
                    _ev[_c["key"]] = {k: _d.get(k) for k in
                                      ("passed", "failed", "skipped", "exit", "head", "duration_s")}
                except Exception:  # noqa: BLE001
                    pass
        _pp = REPO_ROOT / ".kdbp" / "PENDING.md"
        _pending = _pp.read_text(encoding="utf-8", errors="ignore") if _pp.is_file() else None
        _sim = _a3_sim.build_sim(_inflight, amap, REPO_ROOT, evidence=_ev, pending=_pending)
        _a3_sim.emit(_sim, CENTER_OUT)
        if _sim is not None:
            print(f"    wrote docs/site/center/sim.data.js — LIVE change in flight: "
                  f"{','.join(_sim['touched'])} → {','.join(_sim['blast']) or '(no blast)'}")
    except Exception as _e:  # noqa: BLE001
        # honest-empty on any error — never leave a STALE live overlay (the file is
        # gitignored/local, cheap to rewrite; a wrong "in flight" is worse than empty).
        _simf.write_text("// no change in flight — honest-empty at rest (derivation error)\n"
                         "window.GABE_SIM = null;\n")
        print(f"    ⚠ sim.data.js honest-empty (derivation skipped): {_e}")

    # Recent COMMITS as journeys (_a3_commits, C2 mirror): each commit → the graph
    # elements it touched, walkable in the picker's "commits" kind. Derived from git +
    # the built graph's file→node index; honest-empty without git. commits.js is a
    # beat-tail artifact, gitignored like sim.data.js (gabe-init seeds it) — churns per commit.
    try:
        _g = locals().get("_graph")
        _commits = _a3_commits.build_commits(REPO_ROOT, _g) if _g else None
        _a3_commits.emit(_commits, CENTER_OUT)
        if _commits:
            print(f"    wrote docs/site/center/commits.js — {len(_commits)} commit(s); "
                  f"latest touches {_commits[0]['nTouched']} element(s)")
    except Exception as _ce:  # noqa: BLE001 — honest-empty on any error
        (CENTER_OUT / "commits.js").write_text(
            "// commit journeys honest-empty (derivation error)\nwindow.GABE_COMMITS = [];\n")
        print(f"    ⚠ commits.js honest-empty (derivation skipped): {_ce}")

    # The curated USER-WORKFLOWS feed for the Universe station's journeys picker
    # (window.GABE_WORKFLOWS — the operator's user stories as ordered endpoints). CURATED
    # content, never built: the build only ENSURES the file exists so a clean center has
    # no dead script target — an honest-empty placeholder when absent, the center's own
    # curated file copied through when the build writes elsewhere, never overwritten.
    _wff = CENTER_OUT / "workflows.js"
    _wfsrc = CENTER / "workflows.js"
    if _wfsrc.is_file() and _wfsrc.resolve() != _wff.resolve():
        _wff.write_text(_wfsrc.read_text(encoding="utf-8"), encoding="utf-8")
    elif not _wff.is_file():
        _wff.write_text("// curated user workflows for the Gabe Universe journeys picker — none yet.\n"
                        "// window.GABE_WORKFLOWS = [{name, note, steps:[\"METHOD /path\", …]}]; see the\n"
                        "// suite's example/codebase-graph-station/workflows.js. Honest-empty until curated.\n"
                        "// Draft candidates: `/gabe-cc-update curate-workflows` → workflows.draft.js (review, then move in).\n"
                        "window.GABE_WORKFLOWS = [];\n", encoding="utf-8")
    # The DRAFT feed (window.GABE_WORKFLOWS_DRAFT — `/gabe-cc-update curate-workflows`, 2026-09-04): machine-proposed
    # candidates the human reviews in the station's workflows tab. Copied through like the curated file when the build
    # writes elsewhere; an honest-empty stub when absent — the same law as workflows.js: a clean center has NO dead
    # script target (the center link gate counts a referenced-but-missing file as dead). The drafter overwrites it.
    _wfd = CENTER_OUT / "workflows.draft.js"
    _wfdsrc = CENTER / "workflows.draft.js"
    if _wfdsrc.is_file() and _wfdsrc.resolve() != _wfd.resolve():
        _wfd.write_text(_wfdsrc.read_text(encoding="utf-8"), encoding="utf-8")
    elif not _wfd.is_file():
        _wfd.write_text("// DRAFT user workflows — none yet. `/gabe-cc-update curate-workflows` proposes candidates here\n"
                        "// (docs/site/center/workflows.draft.js) from the graph's uncovered endpoints; review in the station's\n"
                        "// workflows tab, then move an accepted entry into workflows.js. Honest-empty until drafted.\n"
                        "window.GABE_WORKFLOWS_DRAFT = [];\n", encoding="utf-8")

    # The per-phase ARCHIVE (Graph 2 replays past changes) — accumulate the CURRENT
    # phase's projection, keyed by phase id; completed phases stay frozen. COMMITTED +
    # diffable (unlike the ephemeral sim.data.js), so the memory of past changes
    # survives across sessions/clones (operator ruling 2026-08-12: committed accumulator,
    # per completed phase). Reads the prior archive from the source center, upserts, writes.
    try:
        _archf = CENTER / "sim-archive.json"
        _existing = json.loads(_archf.read_text()) if _archf.is_file() else None
        _archive = _a3_sim.archive_upsert(_existing, _sim, _inflight)
        _a3_sim.emit_archive(_archive, CENTER_OUT)
        wrote.append(("sim-archive.json", 0))
        if _sim is not None:
            print(f"    wrote docs/site/center/sim-archive.json — {len(_archive['phases'])} "
                  f"archived phase(s)")
    except Exception as _e:  # noqa: BLE001
        print(f"    ⚠ sim-archive skipped: {_e}")

    # The board — second pass, now that archmap can price every card.
    _btext = strip_slot_doc_comments((SHELL_SRC / "board.html").read_text())
    for _tok, _val in {**SHARED, **render_board(amap)}.items():
        _btext = _btext.replace(_tok, _val)
    (CENTER_OUT / "board.html").write_text(_btext)
    wrote.append(("board.html", _btext.count("{{")))

    # The Codebase-graph station — a principal top-nav section (operator ruling
    # 2026-08-11) rendering the C4 graph from the c4-graph.js emitted just above.
    # Pure shared-token fill: the page's interactivity is static JS over the
    # window globals, so it needs no page-specific data beyond SHARED chrome.
    if (SHELL_SRC / "codebase-graph.html").exists():
        _cbtext = strip_slot_doc_comments((SHELL_SRC / "codebase-graph.html").read_text())
        for _tok, _val in SHARED.items():
            _cbtext = _cbtext.replace(_tok, _val)
        (CENTER_OUT / "codebase-graph.html").write_text(_cbtext)
        wrote.append(("codebase-graph.html", _cbtext.count("{{")))

    # inflight.{json,js} are beat-tail artifacts (write-inflight.py, ruling
    # 2026-08-07) and are GITIGNORED (gabe-init seeds it). The builder writes an
    # inactive stub at BUILD time so the board's <script src="inflight.js"> link
    # resolves locally and the link gate passes — but because the files are
    # gitignored, the stub is never committed, so there is no dirty-forever loop
    # and pulse never sees them. In a project the beat tail overwrites the stub
    # with live data locally; a deployed/published center simply has no overlay.
    _ifj = CENTER_OUT / "inflight.json"
    if not _ifj.is_file():
        _stub = {"v": 1, "active": False, "reason": "no beat has written the projection yet",
                 "head": None, "branch": None}
        _ifj.write_text(json.dumps(_stub, indent=2, sort_keys=True) + "\n")
        (CENTER_OUT / "inflight.js").write_text(
            "window.GABE_INFLIGHT = " + json.dumps(_stub, sort_keys=True) + ";\n")

    # The app-wide Architecture station — a consumer of the read-once map, not a
    # second read of the code. Lights up {{SIDEBAR_CODE}} across the estate.
    if BUILD_ARCHITECTURE:
        _testing = render_testing()
        for _tname, _thtml in _testing.items():
            (CENTER_OUT / _tname).write_text(_thtml)
            wrote.append((_tname, _thtml.count("{{")))
        for _aname, _ahtml in render_architecture(amap).items():
            (CENTER_OUT / _aname).write_text(_ahtml)
            wrote.append((_aname, _ahtml.count("{{")))

    # NEW-row snapshot — every table row this build rendered, keyed + hashed.
    # Committed beside the pages: the next iteration's baseline. Written LAST
    # so the architecture station's tables are in it too.
    marks = R_MARKS.rowmarks_seen()
    (CENTER_OUT / "rows-seen.json").write_text(
        json.dumps({"version": 1, "rows": dict(sorted(marks.items()))},
                   indent=1, ensure_ascii=False) + "\n")
    armed = R_MARKS._ROWMARKS["baseline"] is not None
    state = ("badging armed" if armed
             else "bootstrap — badges off until this snapshot is committed")
    print(f"    wrote docs/site/center/rows-seen.json — {len(marks)} row(s) "
          f"tracked ({state})")

    print(f"  A3 regen @ {STAMP} · HEAD {HEAD_SHA}")
    print(f"  {SHELL_NOTE}")
    for name, left in wrote:
        state = "filled" if left == 0 else f"{left} slot(s) awaiting generator"
        print(f"    wrote docs/site/center/{name} — {state}")

    # Asset↔markup guard. The pages emit expandable-row tables (.xtbl/.xrow) for
    # the data model, the test matrix, Claimed coverage and the proof shelf. If
    # the a3.css that was COPIED lacks the .xtbl rule, every one of those renders
    # as unstyled stacked cells — the exact "regenerated with the new generators
    # over a stale a3.css" failure. Refuse to report success, don't ship it quiet.
    _css = CENTER_OUT / "assets" / "a3.css"
    _css_text = _css.read_text() if _css.exists() else ""
    if ".xtbl" not in _css_text:
        print("  ⛔ assets/a3.css has NO .xtbl rule — the expandable tables (data "
              "model · matrix · claims · proof shelf) will render UNSTYLED. Fold "
              "proposed-a3css-additions.css into a3.css (at the END, after the "
              "base rules) before regenerating. Refusing to report success.")
        return 3
    if not (CENTER_OUT / "assets" / "rowclick.js").exists():
        print("  ⚠ assets/rowclick.js is missing — row-click-to-expand and the "
              "targeted-row (#dm-…) opener degrade; wire it into the skeletons.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
