"""_a3_models — the four ENTITY MODELS: claim · seeded · derived · proposed (docs/design/entity-models/plan.md, 2026-09-06).

The one law: `claim` is the REGISTRY and the JOIN KEY — every tool, hook, generator and station registry joins on the claim
slug. `seeded` / `derived` / `proposed` are VIEWS: per-piece home DELTAS over the claim, resolved by a reader as
`home = models.homes[view][id] or claim`. Nothing ever joins on a view's cluster names. NOTHING here re-homes the map.

  seeded   · Part C's `move` verdicts applied (≥ MOVE_SHARE of ≥ MOVE_MIN_USERS users in ONE other entity, data agrees or
             abstains — `_a3_homing.rule`, copied verbatim into `bands`), the SHARED/HUB element class HELD OUT, targets
             TIER-CONSISTENT (a backend piece → a declared entity; a frontend piece → an fe·<slug> home; buckets and
             __unclaimed__ may consume, never receive).
  derived  · request ATOMS (an endpoint + its schemas + the hook that fetches it) merged on the WRITE-MAJORITY TABLE they
             touch — the operator's bound: a write is ownership, decided PER ATOM (an atom with writes anchors on its
             write-majority table; one with reads only anchors on its read-majority table and the row SAYS `anchor_by:
             read`); NAMED by the URL domain at adaptive depth (descend only while the domain's atoms name > 1 anchor
             table, DEPTH_CAP; a prefix must be named by the majority of the cluster's atoms and, past level 1, by at
             least two of them), the anchor table in the user's words as the fallback. Residue: aspects (a gate with
             fan-in across ≥ ASPECT_DOMAINS URL domains MOVES to `a:<gate>`; a table written by ≥ WRITE_FANIN entities
             and frontend pieces consumed from ≥ FE_HOMES homes are REPORTED, never moved) and layers (a declared entity
             with no endpoint — files or tables held for others — reported). An atom with no anchor ABSTAINS: it keeps
             its claim and is listed.
  proposed · one verdict per DECLARED entity — FEATURE · SPLIT · MERGE · ASPECT · LAYER (precedence ASPECT > LAYER >
             SPLIT > MERGE > FEATURE) — plus undeclared CANDIDATES (computed FIRST: a feature proposed as its own entity
             is never evidence that one entity belongs to another), rendered as the map AS IF every proposal were
             accepted (SPLIT / MERGE / candidates move pieces, first verdict wins; ASPECT / LAYER move nothing).

Pure derivation over the in-memory archmap + c4 graph + levels graph + the Part C evidence: no source read, no new arm,
no wallclock, no randomness (sorted inputs, sorted ties, no label propagation). Every cap is printed in `stats.caps`
and every clipped list carries a `_more` sibling or a `stats.truncated` entry. Honest-empty: no levels graph → the
block is absent with the reason — the claim view is byte-identical when the block is stripped (tests/arch-graph pins it).

KILL CONDITION for `HUB_FLOOR["platform"]` (the pulse-angle discipline): if a regen on any estate selects 0 or > 10% of
frontend pieces as platform hubs, the floor is wrong — `views.seeded.note` says so; nothing is tuned silently.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Any

import _a3_naming   # every name a cluster could wear, computed once (naming-plan.md 2026-09-06)
import _a3_render

_UNCLAIMED = "__unclaimed__"
DEPTH_CAP = 3              # adaptive-depth naming stops here (the measured rule; `truncated` says when it clipped)
HUB_HOMES = 3              # a hub is consumed from at least this many homes …
HUB_FLOOR = {"gate": 1, "api-client": 1, "platform": 8, "default": 20}   # … and has at least this in-degree, per class
ASPECT_DOMAINS = 3         # a gate on endpoints of ≥ this many URL domains is an aspect
ASPECT_COCLAIM_MIN = 3     # entity_shape.py's rule restated: ≥ this many co-claimed domains (claimed by ≥ 2 entities) …
ASPECT_SOLE_MAX = 1        # … and at most this many sole-owned domains → an aspect
WRITE_FANIN = 3            # a table written by ≥ this many declared entities is a spine (reported)
FE_HOMES = 3               # a frontend piece consumed from ≥ this many homes is shared frontend (reported)
SPLIT_MIN = 3              # an entity splits only into parts of ≥ this many atoms each
CANDIDATE_SHARE = 2 / 3    # a feature spanning ≥ 3 declared entities is a candidate when no entity holds two thirds of it
ROSTER_CAP = 200
MEMBER_CAP = 400
SHARED_CAP = 400
EVIDENCE_CAP = 12
_PARAM = re.compile(r"^(\{.*\}|:\w+|<.*>|\$\{.*\})$")
_C4_PREFIX = ("endpoint:", "model:", "schema:", "web:", "provider:", "middleware:", "flag:", "prompt:", "external:", "element:", "fe:", "fe·")


# ── small helpers ──────────────────────────────────────────────────────────────
def _segs(path: str) -> list[str]:
    return [s for s in str(path or "").strip("/").split("/") if s and not _PARAM.match(s)]


def _majority(c: Counter) -> tuple[str | None, float]:
    if not c:
        return None, 0.0
    top, n = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[0]
    return top, n / max(1, sum(c.values()))


def _words(table: str | None) -> str:
    """A table name in the user's words: `dish_history_events` → `dish history events` (the naming law, 2026-09-05)."""
    return re.sub(r"[_\-]+", " ", str(table or "")).strip() or str(table or "")


def _slug_of(table: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(table or "").lower()).strip("-")


def _capped(items: list, cap: int) -> tuple[list, int]:
    return items[:cap], max(0, len(items) - cap)


# ── 1 · the union dataflow graph ──────────────────────────────────────────────
def _dataflow(amap: dict, graph: dict, levels: dict | None) -> dict:
    """Directed consumer → produced edges with their rel. Returns {out, inn, home, kind, fe_ids} — `home` is the CLAIM home
    of every node (slug · fe·slug · bucket · __unclaimed__). The write-is-ownership bound lives per ATOM (see `_atoms`),
    not per edge: every edge counts once here."""
    out: dict[str, list] = {}
    inn: dict[str, list] = {}
    home: dict[str, str] = {}
    kind: dict[str, str] = {}

    def edge(u: str, v: str, rel: str) -> None:
        if not u or not v or u == v:
            return
        out.setdefault(u, []).append((v, rel))
        inn.setdefault(v, []).append((u, rel))
    for slug, l2 in (graph.get("l2") or {}).items():
        for n in (l2 or {}).get("nodes") or []:
            if n.get("id"):
                home[n["id"]] = slug
                kind[n["id"]] = n.get("kind") or "?"
        for e in (l2 or {}).get("edges") or []:
            edge(e.get("source"), e.get("target"), e.get("kind") or "fk")
    for ce in graph.get("cross_edges") or []:
        k = ce.get("kind") or "fk"
        src = ce.get("from") or ce.get("source")
        if k == "bridge" and ce.get("export"):
            src = ce["export"]
        edge(src, ce.get("to") or ce.get("target"), k)
    fe = graph.get("fe") or {}
    fps = fe.get("pieces") or []
    fe_ids: list[str] = []
    for p in fps:
        if isinstance(p, dict) and p.get("id"):
            home[p["id"]] = str(p.get("home") or _UNCLAIMED)
            kind[p["id"]] = "fe:%s" % (p.get("kind") or "piece")
            fe_ids.append(p["id"])
    for e in fe.get("edges") or []:
        if isinstance(e, (list, tuple)) and len(e) >= 3 and isinstance(e[0], int) and isinstance(e[1], int) \
                and 0 <= e[0] < len(fps) and 0 <= e[1] < len(fps):
            edge(fps[e[0]].get("id"), fps[e[1]].get("id"), e[2])
    fi = amap.get("function_insight") or {}
    for key, rec in fi.items():
        if "::" in key:
            fk = key.replace("::", "#", 1)
            home[fk] = rec.get("entity") or _UNCLAIMED
            kind[fk] = "function"
            for op in (rec.get("access") or {}).get("ops") or []:
                if isinstance(op, dict) and op.get("model") and op.get("rw") == "w":
                    edge(fk, "model:%s" % op["model"], "writes_to")
    for e in (levels or {}).get("fn_edges") or [] if isinstance(levels, dict) else []:
        if e.get("s") and e.get("t"):
            edge(e["s"], e["t"], e.get("rel") or "calls")
            home.setdefault(e["s"], e.get("ss") or _UNCLAIMED)
            home.setdefault(e["t"], e.get("ds") or _UNCLAIMED)
            kind.setdefault(e["s"], "function")
            kind.setdefault(e["t"], "provider" if str(e["t"]).startswith("provider:") else "function")
    return {"out": out, "inn": inn, "home": home, "kind": kind, "fe_ids": fe_ids}


# ── 2 · the SHARED / HUB element class ────────────────────────────────────────
def hub_class(amap: dict, graph: dict, df: dict) -> tuple[dict[str, dict], list[dict]]:
    """{id: {class, homes, indeg, domains?}} for every hub — a piece consumed from ≥ HUB_HOMES distinct homes with an
    in-degree at or above its class's floor. Classes are idioms already on the map, never a project name-list:
    gate (a gate Depends on endpoints of ≥ 2 entities) · api-client (fe mclass api, or an fe module fecall-reached
    from ≥ 3 homes) · platform (its home is a bucket or __unclaimed__) · default (everything else, floor 20)."""
    gates: dict[str, set] = {}
    gate_domains: dict[str, set] = {}
    for slug, ent in (amap.get("entities") or {}).items():
        for ep in ent.get("endpoints") or []:
            dom = (_segs(ep.get("path") or "") or ["/"])[0]
            for m in ep.get("middleware") or []:
                if isinstance(m, dict) and m.get("gate") and m.get("fn"):
                    fk = str(m["fn"]).replace("::", "#", 1)
                    gates.setdefault(fk, set()).add(slug)
                    gate_domains.setdefault(fk, set()).add(dom)
    buckets = {h.get("id") for h in ((graph.get("fe") or {}).get("homes") or []) if isinstance(h, dict) and h.get("kind") == "bucket"}
    mclass = {p["id"]: p.get("mclass") for p in ((graph.get("fe") or {}).get("pieces") or []) if isinstance(p, dict) and p.get("id")}
    hubs: dict[str, dict] = {}
    for nid, srcs in df["inn"].items():
        consumers = {df["home"].get(u, _UNCLAIMED) for u, _r in srcs}
        indeg = len(srcs)
        cls = None
        if nid in gates and len(gates[nid]) >= 2:
            cls = "gate"
        elif mclass.get(nid) == "api" or (df["kind"].get(nid, "").startswith("fe:") and
                                          len({df["home"].get(u) for u, r in srcs if r == "fecall"}) >= 3):
            cls = "api-client"
        elif df["home"].get(nid) in buckets or df["home"].get(nid) == _UNCLAIMED:
            cls = "platform"
        floor = HUB_FLOOR.get(cls or "default", HUB_FLOOR["default"])
        if len(consumers) >= HUB_HOMES and indeg >= floor:
            row = {"id": nid, "class": cls or "default", "homes": len(consumers), "indeg": indeg}
            if nid in gate_domains:
                row["domains"] = len(gate_domains[nid])
            hubs[nid] = row
    rows = sorted(hubs.values(), key=lambda r: (r["class"], r["id"]))
    return hubs, rows


# ── 3 · SEEDED — Part C's move band, hubs held, tier-consistent targets ───────
def seed(hom: dict | None, hubs: dict, amap: dict, graph: dict) -> dict:
    ents = set((amap.get("entities") or {}).keys())
    fe_homes = {h.get("id") for h in ((graph.get("fe") or {}).get("homes") or []) if isinstance(h, dict) and h.get("kind") == "fe"}
    if hom is None:
        return {"view": {"present": False, "reason": "no Part C homing block on this feed (levels.json predates it) — regen the center to weigh the move band"},
                "homes": {}, "held": [], "abstain": []}
    if not hom.get("present"):
        return {"view": {"present": False, "reason": hom.get("reason") or "no homing evidence"}, "homes": {}, "held": [], "abstain": []}
    homes: dict[str, str] = {}
    held: list[str] = []
    abstain: list[str] = []
    weighed = int(((hom.get("stats") or {}).get("pieces")) or 0)
    for pid, rec in sorted((hom.get("pieces") or {}).items()):
        if rec.get("verdict") != "move" or not rec.get("to"):
            continue
        if pid in hubs:
            held.append(pid)
            continue
        to = rec["to"]
        if pid.startswith("fe:"):
            target = "fe·%s" % to
            if target in fe_homes:
                homes[pid] = target
            else:
                abstain.append(pid)                     # a bucket / candidate / unclaimed area never receives
        else:
            if to in ents:
                homes[pid] = to
            else:
                abstain.append(pid)
    rate = (len(homes) / weighed * 100.0) if weighed else 0.0
    view = {"present": True, "moved": len(homes), "held": len(held), "abstained": len(abstain), "weighed": weighed,
            "note": "Part C move verdicts only — %.1f%% of weighed pieces move, NOT free propagation (which would move a third to a half); hubs held, targets tier-consistent" % rate}
    return {"view": view, "homes": homes, "held": held, "abstain": abstain}


# ── 4 · DERIVED — request atoms → write-majority table → adaptive-depth domain name ───
def _atoms(amap: dict, graph: dict) -> list[dict]:
    """One atom per HTTP/TASK endpoint node: its schemas, its fetchers (bridge exports or screens), its anchor table —
    the write-majority table when the atom writes, else the read-majority (`anchor_by` says which)."""
    bridge_by_ep: dict[str, list[str]] = {}
    for ce in graph.get("cross_edges") or []:
        if ce.get("kind") == "bridge" and ce.get("to"):
            bridge_by_ep.setdefault(ce["to"], []).append(ce.get("export") or ce.get("from") or "")
    table2cls: dict[str, str] = {}
    for ent in (amap.get("entities") or {}).values():
        for m in ent.get("models") or []:
            if m.get("table") and m.get("cls"):
                table2cls.setdefault(m["table"], m["cls"])
    atoms: list[dict] = []
    for slug, l2 in sorted((graph.get("l2") or {}).items()):
        ep_schemas: dict[str, list[str]] = {}
        for e in (l2 or {}).get("edges") or []:
            if str(e.get("target") or "").startswith("schema:"):
                ep_schemas.setdefault(e.get("source"), []).append(e["target"])
        for n in (l2 or {}).get("nodes") or []:
            if n.get("kind") != "endpoint" or not n.get("id") or str(n["id"]).startswith("endpoint:BOOT "):
                continue
            label = str(n.get("label") or n["id"].split(":", 1)[-1])
            method, _, path = label.partition(" ")
            acc = n.get("access")
            ops = (acc.get("ops") if isinstance(acc, dict) else acc) or []
            w: Counter = Counter()
            r: Counter = Counter()
            for op in ops:
                if isinstance(op, dict) and (op.get("table") or op.get("model")):
                    key = op.get("table") or op.get("model")
                    (w if op.get("rw") == "w" else r)[key] += 1
            anchor, _share = _majority(w) if w else _majority(r)
            atoms.append({"ep": n["id"], "method": method, "path": path if method != "TASK" else "", "slug": slug,
                          "via": "task" if method == "TASK" else "http", "schemas": sorted(set(ep_schemas.get(n["id"], []))),
                          "fetchers": sorted({f for f in bridge_by_ep.get(n["id"], []) if f}),
                          "anchor": anchor, "anchor_cls": table2cls.get(anchor or "", anchor), "anchor_by": "write" if w else ("read" if r else None),
                          "fn": ("%s#%s" % ((n.get("det") or {}).get("file"), n.get("fn"))) if n.get("fn") and (n.get("det") or {}).get("file") else None})
    return atoms


def _name_cluster(members: list[dict], all_atoms: list[dict]) -> tuple[str, str, int, bool]:
    """(name, named_by ∈ domain|table, depth, truncated) — descend from depth 1 while the domain's atoms (ACROSS clusters)
    name > 1 anchor table, stop at a singleton or DEPTH_CAP. A prefix must be named by the MAJORITY of this cluster's
    atoms and, past level 1, by at least TWO of them (a single endpoint's own path is an endpoint name, not a feature).
    Otherwise the anchor table names it, in the user's words. TASK atoms carry no path and never vote."""
    http = [a for a in members if a["path"]]
    anchor = members[0].get("anchor")
    if not http:
        return (_words(anchor), "table", 0, False)
    level, prefix, truncated = 1, (), False
    while True:
        counts = Counter(tuple(_segs(a["path"])[:level]) for a in http if len(_segs(a["path"])) >= level)
        if not counts:
            prefix = ()
            break
        top, n = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0]
        if n * 2 <= len(http) or (level > 1 and n < 2):
            prefix = ()
            break
        prefix = top
        anchors_under = {a["anchor"] for a in all_atoms if a["path"] and tuple(_segs(a["path"])[:level]) == top and a["anchor"]}
        if len(anchors_under) > 1 and level < DEPTH_CAP:
            level += 1
            continue
        if len(anchors_under) > 1:                    # still shared at the cap: the domain cannot name it — the table does
            truncated, prefix = True, ()
        break
    if prefix:
        return ("/".join(prefix), "domain", level, truncated)
    return (_words(anchor), "table", level if truncated else 0, truncated)


def derive(amap: dict, graph: dict, levels: dict | None, df: dict, hubs: dict) -> dict:
    ents = set((amap.get("entities") or {}).keys())
    atoms = _atoms(amap, graph)
    anchored = [a for a in atoms if a["anchor"]]
    abstain = sorted(a["ep"] for a in atoms if not a["anchor"])
    if not anchored:
        return {"view": {"present": False, "reason": "no request atom carries a table (no access ops on any endpoint) — nothing to anchor"},
                "rosters": [], "homes": {}, "held": [], "abstain": abstain, "atoms": atoms, "fe_pieces": {}}
    by_anchor: dict[str, list[dict]] = {}
    for a in anchored:
        by_anchor.setdefault(a["anchor"], []).append(a)
    fe_pieces = {p["id"]: p for p in ((graph.get("fe") or {}).get("pieces") or []) if isinstance(p, dict) and p.get("id")}
    buckets = {h.get("id") for h in ((graph.get("fe") or {}).get("homes") or []) if isinstance(h, dict) and h.get("kind") == "bucket"}
    rosters: list[dict] = []
    homes: dict[str, str] = {}
    held: list[str] = []
    claimed_fn: dict[str, str] = {}
    claimed_fe: dict[str, str] = {}
    for anchor in sorted(by_anchor):
        members = by_anchor[anchor]
        name, named_by, depth, truncated = _name_cluster(members, atoms)
        cid = "d:%s" % anchor
        mix = Counter(a["slug"] for a in members)
        maj, purity = _majority(mix)
        by_mix = Counter(a["anchor_by"] for a in members)
        anchor_by, _s = _majority(by_mix)
        for a in members:
            homes[a["ep"]] = cid
            for s in a["schemas"]:
                homes[s] = cid
        # the endpoint's handler + its direct callees (one hop over the levels calls — a floor), hubs held, first anchor wins
        for a in members:
            fk = a.get("fn")
            if fk and fk in df["home"]:
                for cand in [fk] + [v for v, r in df["out"].get(fk, []) if r == "calls" and df["kind"].get(v) == "function"]:
                    if cand in hubs:
                        if cand not in held:
                            held.append(cand)
                        continue
                    if claimed_fn.setdefault(cand, cid) == cid:
                        homes[cand] = cid
        # the frontend twin: fetchers + the pieces that render / use them (one hop — a floor), first anchor wins
        twin = "fe·%s" % cid
        any_fe = False
        for a in members:
            for f in a["fetchers"]:
                if f in fe_pieces and f not in hubs:
                    for cand in [f] + [u for u, r in df["inn"].get(f, []) if r in ("renders", "uses-hook") and u in fe_pieces and u not in hubs and df["home"].get(u) not in buckets]:
                        if claimed_fe.setdefault(cand, twin) == twin:
                            homes[cand] = twin
                            any_fe = True
        screens = len({f.split("#")[0] for a in members for f in a["fetchers"]})
        fetchers = len({f for a in members for f in a["fetchers"]})
        why = ("%d endpoint(s) %s %s under /%s" % (len(members), "write" if anchor_by == "write" else "read", anchor, name) if named_by == "domain"
               else "%d endpoint(s) %s %s — the domain tree cannot name it, the table does" % (len(members), "write" if anchor_by == "write" else "read", anchor))
        if anchor_by == "read":
            why += "; no endpoint writes this table — anchored on reads"
        rosters.append({"id": cid, "twin": twin if any_fe else None, "name": name, "kind": "feature", "anchor_table": anchor, "anchor_cls": members[0].get("anchor_cls"),
                        "anchor_by": anchor_by, **({"anchor_by_mix": dict(sorted(by_mix.items()))} if len(by_mix) > 1 else {}),
                        "domain": name if named_by == "domain" else None, "named_by": named_by, "depth": depth, "truncated": truncated,
                        "color": _a3_render.entity_color(cid), "endpoints": len(members), "screens": screens, "fetchers": fetchers, "purity": round(purity, 2),
                        "claim_mix": dict(sorted(mix.items())), "majority": maj, "why": why})
    # ── residue · aspects ──
    aspects: list[dict] = []
    gate_dom: dict[str, set] = {}
    gate_eps: dict[str, int] = {}
    for slug, ent in (amap.get("entities") or {}).items():
        for ep in ent.get("endpoints") or []:
            dom = (_segs(ep.get("path") or "") or ["/"])[0]
            for m in ep.get("middleware") or []:
                if isinstance(m, dict) and m.get("gate") and m.get("fn"):
                    fk = str(m["fn"]).replace("::", "#", 1)
                    gate_dom.setdefault(fk, set()).add(dom)
                    gate_eps[fk] = gate_eps.get(fk, 0) + 1
    for fk in sorted(gate_dom):
        if len(gate_dom[fk]) >= ASPECT_DOMAINS:
            aid = "a:%s" % fk.split("#")[-1]
            homes[fk] = aid
            aspects.append({"id": aid, "name": _words(fk.split("#")[-1]), "kind": "aspect", "detector": "gate-fan-in", "domains": len(gate_dom[fk]),
                            "endpoints": gate_eps[fk], "members": [fk], "drawn": True, "color": _a3_render.entity_color(aid),
                            "why": "a gate on endpoints of %d URL domains — no feature owns it" % len(gate_dom[fk])})
    writers: dict[str, set] = {}
    for slug, l2 in (graph.get("l2") or {}).items():
        for n in (l2 or {}).get("nodes") or []:
            if n.get("kind") == "endpoint":
                acc = n.get("access")
                for op in ((acc.get("ops") if isinstance(acc, dict) else acc) or []):
                    if isinstance(op, dict) and op.get("rw") == "w" and (op.get("model") or op.get("table")):
                        writers.setdefault(op.get("model") or op.get("table"), set()).add(slug)
    spines = sorted(m for m, s in writers.items() if len(s & ents) >= WRITE_FANIN)
    if spines:
        mem, more = _capped(["model:%s" % m for m in spines], MEMBER_CAP)
        aspects.append({"id": "a:spine", "name": "shared data", "kind": "aspect", "detector": "write-fan-in", "members": mem, "members_more": more,
                        "tables": spines[:40], "tables_more": max(0, len(spines) - 40), "drawn": False,
                        "why": "tables written by ≥%d declared entities — a feature's anchor for none" % WRITE_FANIN})
    fe_shared = sorted(nid for nid, srcs in df["inn"].items() if nid in fe_pieces and len({df["home"].get(u) for u, _r in srcs}) >= FE_HOMES)
    if fe_shared:
        for f in fe_shared:
            homes.pop(f, None)                          # reported, never moved
            if f not in held:
                held.append(f)
        mem, more = _capped(fe_shared, MEMBER_CAP)
        aspects.append({"id": "a:fe-shared", "name": "shared frontend", "kind": "aspect", "detector": "fe-homes", "members": mem, "members_more": more, "drawn": False,
                        "why": "frontend pieces consumed from ≥%d homes — moving them into one hull would erase the geography" % FE_HOMES})
    # members are rebuilt from the FINAL homes — a card never advertises a piece the map homes elsewhere
    by_home: dict[str, list[str]] = {}
    for pid, h in homes.items():
        by_home.setdefault(h, []).append(pid)
    for r in rosters:
        mem = sorted(by_home.get(r["id"], []), key=lambda x: (0 if str(x).startswith("endpoint:") else 1, x)) + sorted(by_home.get(r["twin"], []) if r["twin"] else [])   # endpoint ids FIRST — a capped list never clips the labels a name is computed from
        r["members"], r["members_more"] = _capped(mem, MEMBER_CAP)
        if r["twin"] and not by_home.get(r["twin"]):
            r["twin"] = None
    layers: list[dict] = []
    for slug, ent in sorted((amap.get("entities") or {}).items()):
        if not (ent.get("endpoints") or []) and ((ent.get("files") or []) or (ent.get("models") or [])):
            n_models = len(ent.get("models") or [])
            layers.append({"id": "l:%s" % slug, "name": slug, "kind": "layer", "slug": slug, "files": len(ent.get("files") or []), "tables": n_models, "drawn": False,
                           "why": ("no endpoint — %d table(s) held for other entities' endpoints (a data holder, not a feature; consumption not weighed)" % n_models) if n_models
                                  else "no endpoint and no table — files consumed by other entities (a layer, not a feature; consumption not weighed)"})
    purity_all = round(sum(r["purity"] * r["endpoints"] for r in rosters) / max(1, sum(r["endpoints"] for r in rosters)), 3)
    roster_rows, roster_more = _capped(rosters, ROSTER_CAP)
    view = {"present": True, "features": len(rosters), "aspects": len(aspects), "layers": len(layers), "atoms": len(atoms), "anchored": len(anchored),
            "abstained": len(abstain), "purity": purity_all, "new_clusters": len(rosters) + sum(1 for r in rosters if r["twin"]) + sum(1 for a in aspects if a.get("drawn")),
            "note": "an unanchored atom KEEPS its claim — no witness, no move; features named by the URL domain at adaptive depth, the anchor table as the fallback"}
    return {"view": view, "rosters": roster_rows + aspects + layers, "rosters_more": roster_more,
            "homes": homes, "held": sorted(set(held)), "abstain": abstain, "atoms": atoms, "fe_pieces": fe_pieces}


# ── 5 · PROPOSED — candidates first, then one verdict per declared entity; the map as if accepted ───
def _entity_shape_rule(amap: dict) -> tuple[dict[str, set], dict[str, set], dict[str, set]]:
    """entity_shape.py's aspect rule restated (the pulse script is not shipped to a twin's scripts/): per entity the URL
    domains it claims, the ones it SOLE-owns, and the ones it CO-claims (claimed by ≥ 2 entities) — depth 1."""
    dom_ents: dict[str, set] = {}
    for slug, ent in (amap.get("entities") or {}).items():
        for ep in ent.get("endpoints") or []:
            if str(ep.get("method") or "").upper() in ("BOOT", "TASK"):
                continue
            dom = (_segs(ep.get("path") or "") or ["/"])[0]
            dom_ents.setdefault(dom, set()).add(slug)
    claims: dict[str, set] = {}
    sole: dict[str, set] = {}
    co: dict[str, set] = {}
    for dom, ss in dom_ents.items():
        for s in ss:
            claims.setdefault(s, set()).add(dom)
            if len(ss) == 1:
                sole.setdefault(s, set()).add(dom)
            else:
                co.setdefault(s, set()).add(dom)
    return claims, sole, co


def propose(amap: dict, graph: dict, derived: dict, df: dict) -> dict:
    ents = sorted((amap.get("entities") or {}).keys())
    if not derived.get("view", {}).get("present"):
        return {"view": {"present": False, "reason": "no derived view — nothing to judge against"}, "rosters": [], "candidates": [], "homes": {}, "abstain": []}
    feats = [r for r in derived["rosters"] if r["kind"] == "feature"]
    by_id = {r["id"]: r for r in feats}
    fe_pieces = derived.get("fe_pieces") or {}
    claims, sole, co = _entity_shape_rule(amap)
    gate_home: dict[str, str] = {}
    for r in derived["rosters"]:
        if r["kind"] == "aspect" and r.get("detector") == "gate-fan-in":
            for m in r["members"]:
                gate_home[m] = df["home"].get(m)
    atoms_by_slug: dict[str, list[dict]] = {}
    for a in derived["atoms"]:
        atoms_by_slug.setdefault(a["slug"], []).append(a)
    homes: dict[str, str] = {}
    # ── candidates FIRST: an all-unclaimed feature, or one spanning ≥3 entities with no two-thirds majority ──
    candidates: list[dict] = []
    cand_ids: set = set()
    for r in feats:
        mix = r["claim_mix"]
        maj, share = _majority(Counter(mix))
        if maj == _UNCLAIMED or (len(mix) >= 3 and share < CANDIDATE_SHARE):
            cand_ids.add(r["id"])
            mem, more = _capped(r["members"], 40)
            candidates.append({"id": r["id"], "name": r["name"], "kind": "feature", "named_by": r["named_by"], "anchor_table": r["anchor_table"], "domain": r.get("domain"),
                               "endpoints": r["endpoints"], "screens": r["screens"], "spans_entities": sorted(k for k in mix if k != _UNCLAIMED),
                               "suggested_slug": _slug_of(r["name"] if r["named_by"] == "domain" else r["anchor_table"]), "color": r["color"], "members": mem, "members_more": more})
            for m in r["members"]:
                homes.setdefault(m, r["twin"] if (m.startswith("fe:") and r["twin"]) else r["id"])
    rows: list[dict] = []
    merged_into: dict[str, str] = {}
    merges_seen: set = set()
    for slug in ents:
        ent = (amap.get("entities") or {}).get(slug) or {}
        my_atoms = atoms_by_slug.get(slug, [])
        parts: Counter = Counter("d:%s" % a["anchor"] for a in my_atoms if a["anchor"] and ("d:%s" % a["anchor"]) not in cand_ids)
        verdict, why, evidence, edit = None, "", {}, None
        gates_here = sorted(fk.split("#")[-1] for fk, h in gate_home.items() if h == slug)
        n_co, n_so = len(co.get(slug, set())), len(sole.get(slug, set()))
        if gates_here or (n_co >= ASPECT_COCLAIM_MIN and n_so <= ASPECT_SOLE_MAX and my_atoms):
            verdict = "ASPECT"
            why = ("homes the gate %s, on endpoints of many domains" % gates_here[0]) if gates_here else ("co-claims %d URL domains and sole-owns %d — spread across others' surfaces" % (n_co, n_so))
            evidence = {"co_claims": sorted(co.get(slug, set()))[:EVIDENCE_CAP], "sole_owns": sorted(sole.get(slug, set()))[:EVIDENCE_CAP], "gates": gates_here[:6],
                        **({"co_claims_more": len(co.get(slug, set())) - EVIDENCE_CAP} if len(co.get(slug, set())) > EVIDENCE_CAP else {})}
        elif not my_atoms:
            n_models = len(ent.get("models") or [])
            if not (ent.get("files") or []) and not n_models:
                verdict, why = None, "no file, no endpoint, no table — nothing to weigh"
            else:
                verdict = "LAYER"
                why = ("no endpoint — %d table(s) held for other entities' endpoints (a data holder, not a feature; consumption not weighed)" % n_models) if n_models \
                    else ("no endpoint and no table — %d file(s) consumed by other entities (consumption not weighed)" % len(ent.get("files") or []))
                evidence = {"files": len(ent.get("files") or []), "tables": n_models}
        elif not parts:
            in_cand = sorted({"d:%s" % a["anchor"] for a in my_atoms if a["anchor"] and ("d:%s" % a["anchor"]) in cand_ids})
            verdict, why = None, ("%d endpoint(s) but no atom carries a table — nothing to anchor" % len(my_atoms) if not in_cand
                                  else "its atoms sit only in %s, proposed as new entit%s — nothing left to weigh" % (" · ".join(by_id[c]["name"] for c in in_cand if c in by_id), "y" if len(in_cand) == 1 else "ies"))
            evidence = {"atoms": len(my_atoms), "candidates": in_cand}
        else:
            big = [(cid, n) for cid, n in parts.items() if n >= SPLIT_MIN]
            leaf_domains = {by_id[cid]["name"] for cid, _n in big if cid in by_id}
            if len(big) >= 2 and len(leaf_domains) >= 2 and len({by_id[c]["anchor_table"] for c, _n in big if c in by_id}) >= 2:
                verdict = "SPLIT"
                into = sorted(cid for cid, _n in big)
                why = "%d clean feature(s) inside — %s" % (len(into), " · ".join(by_id[c]["name"] for c in into if c in by_id))
                evidence = {"atoms": len(my_atoms), "features": into, "domains": sorted(leaf_domains)}
                for a in my_atoms:
                    cid = "d:%s" % a["anchor"] if a["anchor"] else None
                    if cid in into:
                        homes.setdefault(a["ep"], cid)
                        for s in a["schemas"]:
                            homes.setdefault(s, cid)
                        for f in a["fetchers"]:
                            if f in fe_pieces and derived["homes"].get(f) == "fe·%s" % cid:
                                homes.setdefault(f, "fe·%s" % cid)
                edit = {"split": [{"slug": _slug_of(by_id[c]["name"]) if c in by_id and by_id[c]["named_by"] == "domain" else _slug_of(by_id[c]["anchor_table"] if c in by_id else c),
                                   "anchor": by_id[c]["anchor_table"] if c in by_id else None} for c in into]}
            else:
                top_cid, _share = _majority(parts)
                maj_slug = by_id[top_cid]["majority"] if top_cid in by_id else None
                if maj_slug and maj_slug != slug and maj_slug in ents:
                    pair = tuple(sorted((slug, maj_slug)))
                    n_me = sum(1 for a in atoms_by_slug.get(slug, []) if a["anchor"] and "d:%s" % a["anchor"] == top_cid)
                    n_other = sum(1 for a in atoms_by_slug.get(maj_slug, []) if a["anchor"] and "d:%s" % a["anchor"] == top_cid)
                    if n_other != n_me:
                        survivor, how = (maj_slug if n_other > n_me else slug), "more atoms in the feature"
                    elif len(sole.get(maj_slug, set())) != len(sole.get(slug, set())):
                        survivor, how = (maj_slug if len(sole.get(maj_slug, set())) > len(sole.get(slug, set())) else slug), "sole-owns a domain"
                    else:
                        survivor, how = pair[0], "sorted-first"
                    verdict = "MERGE"
                    why = "its atoms sit in %s, whose majority is %s — survivor %s (%s)" % (by_id[top_cid]["name"], maj_slug, survivor, how)
                    evidence = {"feature": top_cid, "atoms": {slug: n_me, maj_slug: n_other}, "survivor": survivor, "alternative": maj_slug if survivor == slug else slug}
                    if pair not in merges_seen:
                        merges_seen.add(pair)
                        loser = slug if survivor != slug else maj_slug
                        merged_into[loser] = survivor
                        for a in atoms_by_slug.get(loser, []):
                            homes.setdefault(a["ep"], survivor)
                            for s in a["schemas"]:
                                homes.setdefault(s, survivor)
                            for f in a["fetchers"]:
                                if f in fe_pieces:
                                    homes.setdefault(f, "fe·%s" % survivor)
                    edit = {"merge_into": survivor}
                else:
                    verdict = "FEATURE"
                    why = "majority of %s and sole-owns %d URL domain(s)" % (by_id[top_cid]["name"] if top_cid in by_id else "its feature", n_so)
                    evidence = {"feature": top_cid, "sole_owns": sorted(sole.get(slug, set()))[:EVIDENCE_CAP]}
        rows.append({"slug": slug, "verdict": verdict, "why": why, "evidence": evidence, **({"suggested_edit": edit} if edit else {})})
    for row in rows:                                    # a slug that LOST atoms in a merge must say so, whatever its own row read
        if row["slug"] in merged_into and row["verdict"] != "MERGE":
            row.update({"verdict": "MERGE", "why": "its atoms were merged into %s (a partner's verdict) — was: %s" % (merged_into[row["slug"]], row["why"]),
                        "evidence": {**row["evidence"], "survivor": merged_into[row["slug"]]}, "suggested_edit": {"merge_into": merged_into[row["slug"]]}})
    cands, cand_more = _capped(candidates, ROSTER_CAP)
    tally = Counter(x["verdict"] or "none" for x in rows)
    view = {"present": True, "verdicts": {k: tally.get(k, 0) for k in ("FEATURE", "SPLIT", "MERGE", "ASPECT", "LAYER")}, "unweighed": tally.get("none", 0),
            "candidates": len(candidates), "moved": len(homes), "note": "the map as if every proposal were accepted — candidates first, then SPLIT / MERGE move pieces (first verdict wins); ASPECT / LAYER move nothing"}
    return {"view": view, "rosters": rows, "candidates": cands, "candidates_more": cand_more, "homes": homes, "abstain": []}


# ── 6 · the block, the attach, the levels slice ───────────────────────────────
RULE = ("claim = the config's code.* file claims (the map today) · seeded = Part C move verdicts applied, hubs held, targets tier-consistent · "
        "derived = request atoms merged on the write-majority table, named by the URL domain at adaptive depth (the table in the user's words as "
        "the fallback) · proposed = candidates first, then one verdict per declared entity (FEATURE · SPLIT · MERGE · ASPECT · LAYER), rendered as if "
        "accepted. Deterministic: sorted inputs, sorted ties, no label propagation, no seed. claim is the join key; the other three are views.")


def _bands_seeded(hom: dict | None) -> dict:
    if hom and hom.get("present") and hom.get("rule"):
        return dict(hom["rule"])
    try:
        import _a3_homing
        return {"move_share": _a3_homing.MOVE_SHARE, "move_min_users": _a3_homing.MOVE_MIN_USERS, "shared_min": _a3_homing.SHARED_MIN,
                "text": "the module's constants — no Part C block on this feed"}
    except Exception:  # noqa: BLE001
        return {}


def build(amap: dict, graph: dict, levels: dict | None, hom: dict | None = None, naming_cfg: dict | None = None, labels: dict | None = None, url_domain_map: dict | None = None) -> dict:
    """The `models` block. `present: False` + reason when the levels graph is absent (no users witness). `naming_cfg` = the
    config's optional `naming` block, `labels` = the registry's display names per slug, `url_domain_map` = the legacy top-level
    key — all three feed `_a3_naming.apply`, which attaches `names{}` to every derived/candidate row and the `naming` contract."""
    if not isinstance(levels, dict) or not levels:
        return {"present": False, "reason": "no levels graph (graft arm absent) — the users witness cannot be read; the claim view is the only model"}
    df = _dataflow(amap, graph, levels)
    hubs, shared = hub_class(amap, graph, df)
    s = seed(hom, hubs, amap, graph)
    d = derive(amap, graph, levels, df, hubs)
    p = propose(amap, graph, d, df)
    fe_n = len(df["fe_ids"])
    plat = sum(1 for r in shared if r["class"] == "platform")
    if fe_n and (plat == 0 or plat > 0.10 * fe_n):
        s["view"]["note"] = (s["view"].get("note") or "") + " · KILL CONDITION: platform hubs = %d of %d fe pieces — HUB_FLOOR['platform'] (%d) is wrong for this estate" % (plat, fe_n, HUB_FLOOR["platform"])
    views = {"claim": {"present": True, "pieces": len(df["home"]), "note": "the config's code.* claims — the map today"},
             "seeded": s["view"], "derived": d["view"], "proposed": p["view"]}
    present = [v for v in ("seeded", "derived", "proposed") if views[v].get("present")]
    shared_rows, shared_more = _capped(shared, SHARED_CAP)
    truncated = []
    if d.get("rosters_more"):
        truncated.append(["rosters.derived", d["rosters_more"]])
    if shared_more:
        truncated.append(["shared", shared_more])
    if p.get("candidates_more"):
        truncated.append(["rosters.candidates", p["candidates_more"]])
    block = {
        "head": graph.get("head"),
        "rule": RULE,
        "default": "claim",
        "views": views,
        "bands": {"seeded": _bands_seeded(hom)},
        "shared": shared_rows,
        "shared_more": shared_more,
        "rosters": {"derived": d["rosters"], "proposed": p["rosters"], "candidates": p["candidates"]},
        "homes": {v: {"seeded": s, "derived": d, "proposed": p}[v]["homes"] for v in present},
        "held": {v: {"seeded": s, "derived": d}[v]["held"] for v in present if v in ("seeded", "derived")},
        "abstain": {v: {"seeded": s, "derived": d, "proposed": p}[v]["abstain"] for v in present},
        "stats": {"caps": {"depth_cap": DEPTH_CAP, "hub_homes": HUB_HOMES, "hub_floor": dict(HUB_FLOOR), "aspect_domains": ASPECT_DOMAINS,
                           "aspect_coclaim_min": ASPECT_COCLAIM_MIN, "aspect_sole_max": ASPECT_SOLE_MAX, "write_fanin": WRITE_FANIN, "fe_homes": FE_HOMES,
                           "split_min": SPLIT_MIN, "candidate_share": round(CANDIDATE_SHARE, 3), "roster_cap": ROSTER_CAP, "member_cap": MEMBER_CAP,
                           "shared_cap": SHARED_CAP, "evidence_cap": EVIDENCE_CAP},
                  "truncated": truncated},
        "present": True,
    }
    try:
        block["naming"] = _a3_naming.apply(block, d.get("atoms") or [], labels or {}, naming_cfg, url_domain_map, (graph.get("stats") or {}).get("fe"))
    except Exception as _ne:  # noqa: BLE001 — a vocabulary problem never costs the models block
        block["naming"] = {"present": False, "reason": "naming error: %s" % _ne, "default": _a3_naming.DEFAULT_STRATEGY, "rule": _a3_naming.RULE}
    return block


def _is_c4_id(pid: str) -> bool:
    return str(pid).startswith(_C4_PREFIX)


def attach(graph: dict, mod: dict) -> None:
    """`graph.models` (the c4-side block: homes restricted to c4 ids) + `stats.models`; no per-node fields (the strip test)."""
    st = graph.setdefault("stats", {})
    if not mod or not mod.get("present"):
        st["models"] = {"present": False, "reason": (mod or {}).get("reason") or "no models block"}
        graph.pop("models", None)
        return
    c4_ids = {n["id"] for l2 in (graph.get("l2") or {}).values() for n in (l2 or {}).get("nodes") or [] if n.get("id")}
    c4_ids |= {p["id"] for p in ((graph.get("fe") or {}).get("pieces") or []) if isinstance(p, dict) and p.get("id")}
    block = {k: v for k, v in mod.items() if k not in ("homes", "held", "abstain")}
    block["homes"] = {v: {k: t for k, t in m.items() if k in c4_ids} for v, m in (mod.get("homes") or {}).items()}
    block["held"] = {v: [k for k in lst if k in c4_ids] for v, lst in (mod.get("held") or {}).items()}
    block["abstain"] = {v: [k for k in lst if k in c4_ids] for v, lst in (mod.get("abstain") or {}).items()}
    graph["models"] = block
    views = mod.get("views") or {}
    st["models"] = {"present": True, "views": [v for v in ("claim", "seeded", "derived", "proposed") if (views.get(v) or {}).get("present")],
                    "features": (views.get("derived") or {}).get("features", 0), "shared": len(mod.get("shared") or []),
                    "seeded_moved": (views.get("seeded") or {}).get("moved", 0), "derived_abstained": (views.get("derived") or {}).get("abstained", 0),
                    "candidates": (views.get("proposed") or {}).get("candidates", 0)}


def levels_slice(mod: dict, graph: dict) -> dict:
    """The levels.json mirror: the per-view homes for backend FUNCTION ids (`file#fn` — levels-side nodes the c4 map lacks).
    Any other id that is not on the c4 map is DROPPED and named (never silently reclassified as a function)."""
    if not mod or not mod.get("present"):
        return {"present": False, "reason": (mod or {}).get("reason") or "no models block"}
    c4_ids = {n["id"] for l2 in (graph.get("l2") or {}).values() for n in (l2 or {}).get("nodes") or [] if n.get("id")}
    c4_ids |= {p["id"] for p in ((graph.get("fe") or {}).get("pieces") or []) if isinstance(p, dict) and p.get("id")}
    dropped: list[str] = []

    def fn_only(keys):
        out = []
        for k in keys:
            if k in c4_ids:
                continue
            if _is_c4_id(k):
                dropped.append(k)
                continue
            out.append(k)
        return out
    homes = {v: {k: t for k, t in m.items() if k in fn_only(list(m.keys()))} for v, m in (mod.get("homes") or {}).items()}
    held = {v: fn_only(lst) for v, lst in (mod.get("held") or {}).items()}
    abstain = {v: fn_only(lst) for v, lst in (mod.get("abstain") or {}).items()}
    return {"present": True, "head": mod.get("head"), "views": mod.get("views"), "bands": mod.get("bands"),
            "homes": homes, "held": held, "abstain": abstain, "dropped": sorted(set(dropped))}
