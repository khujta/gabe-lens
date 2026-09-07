"""_a3_naming — every NAME a cluster could wear, computed ONCE (docs/design/entity-models/naming-plan.md, 2026-09-06).

A name is a RENDERING of a row that already exists. The claim slug and every cluster id (`fe·<slug>` · `d:<table>` · `a:<gate>` ·
`fe·d:<table>`) are JOIN KEYS and never move; a STRATEGY changes the words a cluster wears, a CONVENTION changes how a frontend
piece is told apart from a backend one. Both are emitted here so the station, gabe-map and the drafter substitute one `{name}`
and cannot drift on the rule.

  STRATEGIES (names{} per roster row; `row.name` itself is the `domain` strategy and stays byte-identical):
    domain  · today's `_a3_models._name_cluster` — the URL domain at adaptive depth, else the table in the user's words
    table   · `_words(anchor_table)` — unique by construction (the id is `d:<table>`)
    class   · the ORM class split acronym-aware, lowercased (`LLMModelFlow` → `llm model flow`; `OAuthConfig` → `o auth config` —
              no rule can know OAuth is one word; a project renames it in naming.words.tables)
    path    · the deepest segment common to every HTTP path of the cluster, else the most frequent leaf; collisions across rows
              suffixed ` (<table words>)`, counted, and the position self-disables when ≥ 1/3 of the rows collide
    action  · the 2026-09-05 naming law verbatim — `draft_name()` from the INSTALLED gabe-cc-update drafter over the cluster's
              UNCAPPED endpoint labels (GABE_DRAFT_WORKFLOWS overrides the path; unreachable → absent, said)
    config  · the project's own words — naming.entities / adoption display_name for a claim entity; naming.words.domains /
              naming.words.tables / the legacy top-level url_domain_map for a cluster; absent → no key, the position disables
    both    · `<table words> · /<url prefix>` — the two machine witnesses side by side, unique by construction
  CONVENTIONS (form templates with the project's words already substituted; `{name}` · `{name|camel}` · `{name|pascal}`):
    case (default, operator-ruled 2026-09-06: frontend camelCase · backend PascalCase) · prefix · suffix · bracket · glyph · tint · none

Deterministic (sorted inputs, sorted ties, no wallclock), honest-empty (an absent input is an absent key or a disabled position
with its reason), report-never-gate (a malformed naming block records `config_error` and defaults — a regen never fails on a
vocabulary file), R10 (the unclaimed bucket is spelled `unclaimed`, never the older word). NOTHING here touches an id.
"""
from __future__ import annotations

import importlib.util
import os
import re
from collections import Counter
from pathlib import Path

STRATEGIES = ("domain", "table", "class", "path", "action", "config", "both")
CONVENTIONS = ("case", "prefix", "suffix", "bracket", "glyph", "tint", "none")
DEFAULT_STRATEGY = "domain"
DEFAULT_CONVENTION = "case"
DEFAULT_WORDS = {"frontend": "ui", "backend": "api"}
DEFAULT_CASE = {"frontend": "camel", "backend": "pascal"}
NAME_MAX = 40                 # the hull sprite truncates past this; every other surface carries the whole name (kill: a two-line label)
PATH_DISABLE_SHARE = 1 / 3    # the `path` position disables itself when this share of rows collide
_PARAM = re.compile(r"^(\{.*\}|:\w+|<.*>|\$\{.*\})$")
RULE = "names are DISPLAY — the claim slug and every cluster id are unchanged; nothing joins on a name"


# ── words ─────────────────────────────────────────────────────────────────────
def _words(s: str | None) -> str:
    return re.sub(r"[_\-]+", " ", str(s or "")).strip()


def class_words(cls: str | None) -> str:
    """`LLMModelFlow` → `llm model flow` · `ChatMessageFeedback` → `chat message feedback` · `Assistant__UserSpecificConfig` →
    `assistant user specific config`. Acronym-aware (a run of capitals before a capitalised word stays one word); `OAuthConfig`
    reads `o auth config` — said on the card, never guessed."""
    s = str(cls or "")
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", s)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", s)
    s = re.sub(r"[_\-]+", " ", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def _segs(path: str) -> list[str]:
    return [x for x in str(path or "").strip("/").split("/") if x and not _PARAM.match(x)]


def path_name(paths: list[str]) -> str | None:
    """The deepest segment common to EVERY path, else the most frequent leaf segment (ties alphabetical); None without paths."""
    segl = [_segs(p) for p in paths if _segs(p)]
    if not segl:
        return None
    common: list[str] = []
    for i in range(min(len(s) for s in segl)):
        col = {s[i] for s in segl}
        if len(col) == 1:
            common.append(segl[0][i])
        else:
            break
    if common:
        return _words(common[-1])
    leaves = Counter(s[-1] for s in segl)
    top = sorted(leaves.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    return _words(top)


def _majority_prefix(paths: list[str]) -> str | None:
    """The level-1 URL segment held by a strict majority of the paths, else None."""
    firsts = [s[0] for s in (_segs(p) for p in paths) if s]
    if not firsts:
        return None
    top, n = sorted(Counter(firsts).items(), key=lambda kv: (-kv[1], kv[0]))[0]
    return top if n * 2 > len(firsts) else None


# ── the installed naming law ─────────────────────────────────────────────────
def load_draft_name() -> tuple:
    """(draft_name callable | None, path, reason) — the ONE copy of the 2026-09-05 law lives in the installed gabe-cc-update skill
    (three consumers import it there); GABE_DRAFT_WORKFLOWS overrides the path (the GABE_GRAFT_INDEX precedent)."""
    p = Path(os.environ.get("GABE_DRAFT_WORKFLOWS") or (Path.home() / ".claude" / "skills" / "gabe-cc-update" / "scripts" / "draft-workflows.py"))
    if not p.is_file():
        return None, str(p), "draft-workflows.py not found at %s — install the suite or set GABE_DRAFT_WORKFLOWS" % p
    try:
        spec = importlib.util.spec_from_file_location("gabe_draft_workflows_naming", p)
        if spec is None or spec.loader is None:
            return None, str(p), "draft-workflows.py could not be loaded from %s" % p
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        fn = getattr(mod, "draft_name", None)
        if not callable(fn):
            return None, str(p), "draft-workflows.py at %s carries no draft_name()" % p
        return fn, str(p), None
    except Exception as e:  # noqa: BLE001
        return None, str(p), "draft-workflows.py at %s failed to import (%s)" % (p, e.__class__.__name__)


# ── conventions ───────────────────────────────────────────────────────────────
def _pair(cfg: dict | None, key: str, default: dict, allowed: tuple | None = None) -> tuple[dict, str | None]:
    out = dict(default)
    err = None
    raw = (cfg or {}).get(key)
    if isinstance(raw, dict):
        for k in ("frontend", "backend"):
            v = raw.get(k)
            if isinstance(v, str) and v.strip() and (allowed is None or v.strip() in allowed):
                out[k] = v.strip()
            elif v is not None:
                err = "naming.fe.%s.%s is not %s" % (key if key != "words" else "", k, ("one of " + " · ".join(allowed)) if allowed else "a word")
    return out, err


def forms(words: dict, case: dict) -> dict:
    """The seven form templates with the project's words substituted; `{name}` · `{name|camel}` · `{name|pascal}` are the tokens
    every surface substitutes (the case mark applies to the name's leading word-run — up to the first ` · ` or ` — `)."""
    fw, bw = words["frontend"], words["backend"]
    return {
        "case": {"fe": "{name|%s}" % case["frontend"], "be": "{name|%s}" % case["backend"]},
        "prefix": {"fe": "fe · {name}", "be": "{name}"},
        "suffix": {"fe": "{name} (%s)" % fw, "be": "{name}"},
        "bracket": {"fe": "[%s] {name}" % fw, "be": "[%s] {name}" % bw},
        "glyph": {"fe": "{name}", "be": "{name}", "mark": "screen", "sprite": "tint"},
        "tint": {"fe": "{name}", "be": "{name}"},
        "none": {"fe": "{name}", "be": "{name}"},
    }


def _case(run: str, how: str) -> str:
    ws = [w for w in re.split(r"[\s_\-]+", run) if w]
    if not ws:
        return run
    if how == "camel":
        return ws[0].lower() + "".join(w[:1].upper() + w[1:].lower() for w in ws[1:])
    if how == "pascal":
        return "".join(w[:1].upper() + w[1:].lower() for w in ws)
    return run


def render(form: str, name: str) -> str:
    """Substitute a form template over a name — the reference implementation the station and the tools mirror."""
    m = re.match(r"^(.*?)( · | — )(.*)$", name)
    head, sep, tail = (m.group(1), m.group(2), m.group(3)) if m else (name, "", "")
    out = form.replace("{name|camel}", _case(head, "camel") + sep + tail).replace("{name|pascal}", _case(head, "pascal") + sep + tail)
    return out.replace("{name}", name)


# ── the names per row + the naming block ─────────────────────────────────────
def _cfg_words(cfg: dict | None) -> tuple[dict, dict]:
    w = (cfg or {}).get("words") if isinstance((cfg or {}).get("words"), dict) else {}
    dom = w.get("domains") if isinstance(w.get("domains"), dict) else {}
    tab = w.get("tables") if isinstance(w.get("tables"), dict) else {}
    return {str(k): str(v) for k, v in dom.items() if isinstance(v, str) and v.strip()}, {str(k): str(v) for k, v in tab.items() if isinstance(v, str) and v.strip()}


def names_for(row: dict, labels: list[str], draft_name, dom_words: dict, tab_words: dict, url_domain_map: dict) -> dict:
    """The names{} a derived/candidate row could wear — only the keys a strategy can produce, never null."""
    table = row.get("anchor_table")
    cls = row.get("anchor_cls")
    out: dict = {}
    if table:
        out["table"] = _words(table)
        out["class"] = class_words(cls) if (cls and cls != table) else _words(table)
    paths = [lab.split(" ", 1)[1] for lab in labels if " " in lab]
    pn = path_name(paths)
    if pn:
        out["path"] = pn
    if draft_name is not None and labels:
        try:
            out["action"] = draft_name(sorted(labels))[0]
        except Exception:  # noqa: BLE001
            pass
    if table:
        prefix = row.get("domain") if row.get("named_by") == "domain" else _majority_prefix(paths)
        out["both"] = ("%s · /%s" % (_words(table), prefix)) if prefix else _words(table)
    first = (row.get("domain") or "").split("/")[0] if row.get("named_by") == "domain" else None
    cfgn = (dom_words.get(first) if first else None) or (tab_words.get(table) if table else None) or ((url_domain_map or {}).get(first) if first else None)
    if isinstance(cfgn, str) and cfgn.strip():
        out["config"] = cfgn.strip()
    return out


def apply(mod: dict, atoms: list[dict], labels_by_slug: dict, cfg: dict | None, url_domain_map: dict | None, fe_stats: dict | None) -> dict:
    """Attach `names{}` to every derived feature row and candidate row of the models block IN PLACE and return the `naming`
    block. `atoms` are the emitter's uncapped request atoms (the labels come from here, never from the capped members list)."""
    cfg = cfg if isinstance(cfg, dict) else {}
    errors: list[str] = []
    strategy = cfg.get("strategy") if isinstance(cfg.get("strategy"), str) else None
    if strategy is not None and strategy not in STRATEGIES:
        errors.append("naming.strategy %r is not one of %s" % (strategy, " · ".join(STRATEGIES)))
        strategy = None
    fe_cfg = cfg.get("fe") if isinstance(cfg.get("fe"), dict) else {}
    convention = fe_cfg.get("convention") if isinstance(fe_cfg.get("convention"), str) else None
    if convention is not None and convention not in CONVENTIONS:
        errors.append("naming.fe.convention %r is not one of %s" % (convention, " · ".join(CONVENTIONS)))
        convention = None
    words, werr = _pair(fe_cfg, "words", DEFAULT_WORDS) if isinstance(fe_cfg.get("words"), dict) else _pair({"words": {k: fe_cfg.get(k) for k in ("frontend", "backend")}}, "words", DEFAULT_WORDS)
    if werr:
        errors.append(werr)
    case, cerr = _pair(fe_cfg, "case", DEFAULT_CASE, ("camel", "pascal", "none"))
    if cerr:
        errors.append(cerr)
    dom_words, tab_words = _cfg_words(cfg)
    draft_name, dn_path, dn_reason = load_draft_name()
    # the cluster's UNCAPPED endpoint labels, by anchor table
    labels_by_anchor: dict[str, list[str]] = {}
    for a in atoms or []:
        if a.get("anchor") and a.get("via") == "http" and a.get("path"):
            labels_by_anchor.setdefault(a["anchor"], []).append("%s %s" % (a.get("method"), a.get("path")))
    rosters = mod.get("rosters") or {}
    feats = [r for r in (rosters.get("derived") or []) if r.get("kind") == "feature"]
    cands = rosters.get("candidates") or []
    used_dom: set = set()
    used_tab: set = set()
    cov: Counter = Counter()
    for r in feats:
        labs = sorted(set(labels_by_anchor.get(r.get("anchor_table") or "", [])))
        r["names"] = names_for(r, labs, draft_name, dom_words, tab_words, url_domain_map or {})
        if "config" in r["names"]:
            first = (r.get("domain") or "").split("/")[0] if r.get("named_by") == "domain" else None
            if first and first in dom_words:
                used_dom.add(first)
            elif r.get("anchor_table") in tab_words:
                used_tab.add(r["anchor_table"])
    # path collisions: suffix every colliding row with its table words (deterministic), count them
    by_path: dict[str, list[dict]] = {}
    for r in feats:
        if r.get("names", {}).get("path"):
            by_path.setdefault(r["names"]["path"], []).append(r)
    collided = 0
    for pn, rows in sorted(by_path.items()):
        if len(rows) > 1:
            for r in rows:
                r["names"]["path"] = "%s (%s)" % (pn, _words(r.get("anchor_table")))
                collided += 1
    for r in feats:
        for k in STRATEGIES:
            if k == "domain" or k in (r.get("names") or {}):
                cov[k] += 1
    by_id = {r["id"]: r for r in feats if r.get("id")}
    for c in cands:
        src = by_id.get(c.get("id"))
        if src is not None:
            c["names"] = dict(src.get("names") or {})
    # claim entities: the project's display words
    ent_cfg = cfg.get("entities") if isinstance(cfg.get("entities"), dict) else {}
    entities: dict = {}
    unknown = sorted(k for k in ent_cfg if k not in labels_by_slug)
    for slug in sorted(labels_by_slug):
        disp = ent_cfg.get(slug) if isinstance(ent_cfg.get(slug), str) and ent_cfg.get(slug).strip() else None
        lab = labels_by_slug.get(slug)
        if disp:
            entities[slug] = {"display": disp.strip(), "source": "naming.entities"}
        elif isinstance(lab, str) and lab and lab != slug:
            entities[slug] = {"display": lab, "source": "adoption display_name"}
    n_rows = len(feats)
    long_action = sum(1 for r in feats if len((r.get("names") or {}).get("action") or "") > NAME_MAX)
    long_both = sum(1 for r in feats if len((r.get("names") or {}).get("both") or "") > NAME_MAX)
    disabled: dict = {}
    if n_rows and cov.get("config", 0) == 0 and not entities:
        disabled["config"] = "no naming.words / naming.entities in center.config.json and no adoption display_name — nothing to name from"
    if n_rows and cov.get("action", 0) == 0:
        disabled["action"] = dn_reason or "no cluster carries an HTTP endpoint label"
    if n_rows and collided >= PATH_DISABLE_SHARE * n_rows:
        disabled["path"] = "%d of %d rows collide on their path name — the position is off on this feed" % (collided, n_rows)
    fe_present = bool((fe_stats or {}).get("present"))
    fe_block = {"present": fe_present, "reason": None if fe_present else ((fe_stats or {}).get("reason") or "no frontend arm on this map"),
                "convention": convention or DEFAULT_CONVENTION, "words": words, "case": case, "forms": forms(words, case),
                "homes": (fe_stats or {}).get("homes"), "twins": sum(1 for r in feats if r.get("twin"))}
    unused = sorted([k for k in dom_words if k not in used_dom] + [k for k in tab_words if k not in used_tab])
    return {"default": strategy or DEFAULT_STRATEGY, "source": ("center.config.json#naming" if cfg else "built-in"),
            "positions": list(STRATEGIES), "coverage": {**{k: (n_rows if k == "domain" else cov.get(k, 0)) for k in STRATEGIES}, "rows": n_rows},
            "collisions": {"path": collided}, "long": {"action": long_action, "both": long_both}, "disabled": disabled,
            "entities": entities, "fe": fe_block, "action_source": {"path": dn_path, "reason": dn_reason},
            "config_error": ("; ".join(errors) if errors else None), "unused_words": unused, "unknown_entities": unknown,
            "caps": {"name_max": NAME_MAX, "path_disable_share": round(PATH_DISABLE_SHARE, 3)}, "rule": RULE}
