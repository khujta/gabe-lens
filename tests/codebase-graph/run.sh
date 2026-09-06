#!/usr/bin/env bash
# Codebase-graph station battery — a STATIC/STRUCTURAL executable contract for the
# twin center's "Codebase graph" station (templates/center/shell/codebase-graph.html
# + assets/sim-panel.js), the change-simulation lifecycle instrument.
#
# WHY THIS EXISTS: the render gates never EXECUTE the station's inline sim JS —
# verify_center_chrome.mjs runs only rowclick.js against a stub DOM, and
# check_center_links only resolves srcs. So a whole class of station bug ships green.
# This battery is node-stdlib/grep only (no browser, no twin), zero-arg, and the
# doctor auto-runs it. It locks in the failure modes the render gates cannot see:
#   * a `hidden` element defeated by an author `display:` rule — the exact class of
#     the modal-shows-on-load bug and the stray-stageSeg bug (MUTATION-PROVEN here).
#   * a JS mount id (getElementById) or <script src> with no matching markup/file.
#   * the shared window.GABE_SIM_PANEL contract drifting from either host (station
#     + the arch-graph lab both load assets/sim-panel.js).
# Exit 0 = all pass. Add a FIRE+SILENT pair with every new station invariant.
set -u
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
SHELL_SRC="$REPO/templates/center/shell"

python3 - "$SHELL_SRC" <<'PY'
import sys, re, json, pathlib
shell = pathlib.Path(sys.argv[1])
station = (shell / "codebase-graph.html").read_text(encoding="utf-8")
panel   = (shell / "assets" / "sim-panel.js").read_text(encoding="utf-8")
grammar = (shell / "assets" / "graph-grammar.js").read_text(encoding="utf-8")
lab     = (shell / "example" / "arch-graph-lab" / "arch-graph-sim-svg.html").read_text(encoding="utf-8")
archive = (shell / "codebase-archive.html").read_text(encoding="utf-8")

pass_ = 0; fail = 0
def check(cond, msg):
    global pass_, fail
    if cond: pass_ += 1
    else: fail += 1; print("  FAIL:", msg)

# ── helpers ────────────────────────────────────────────────────────────────
def hidden_subjects(html):
    """class/id selectors on elements that carry the `hidden` attribute."""
    subs = set()
    for tag in re.findall(r'<[^>]*\bhidden\b[^>]*>', html):
        m = re.search(r'\bid="([^"]+)"', tag)
        if m: subs.add('#' + m.group(1))
        m = re.search(r'\bclass="([^"]+)"', tag)
        if m:
            for c in m.group(1).split(): subs.add('.' + c)
    return subs

def display_forced(css, subject):
    """A BARE-subject author rule (selector == subject exactly, no descendant scope)
    setting display to a VISIBLE value defeats the UA [hidden]{display:none} for
    EVERY element carrying it. A scoped rule (`.X .subject{…}`) only forces the
    scoped elements, so we don't chase it here — the known bug class is bare."""
    for m in re.finditer(r'([^{}]+)\{([^}]*)\}', css):
        if not re.search(r'display\s*:\s*(flex|inline-flex|grid|block|inline-block)\b', m.group(2)):
            continue
        for sel in m.group(1).split(','):
            if sel.strip() == subject:
                return True
    return False

def has_hidden_guard(css, subject):
    return re.search(re.escape(subject) + r'\[hidden\]\s*\{[^}]*display\s*:\s*none', css) is not None

# ── A · [hidden]-guard contract — the render gates cannot see this (MUTATION-PROVEN)
# CSS comments can carry literal braces (e.g. a comment mentioning [hidden]{display:none}),
# which would confuse the brace-based rule parser — strip them before cascade analysis.
CSS = re.sub(r'/\*.*?\*/', ' ', station, flags=re.S)
subs = hidden_subjects(station)
forced = sorted(s for s in subs if display_forced(CSS, s))
check('.cbg-seg' in forced,   "fixture: .cbg-seg is a display-forced hidden subject")
check('.cbg-modal' in forced, "fixture: .cbg-modal is a display-forced hidden subject")
for s in forced:
    check(has_hidden_guard(CSS, s),
          f"hidden element {s} is display-forced but has no {s}[hidden] display:none guard "
          f"(it will show on load, like the modal/stageSeg bug)")
# FIRE: strip the .cbg-seg guard → the check above must be able to catch it
_mut = re.sub(r'\.cbg-seg\[hidden\]\s*\{[^}]*\}', '', CSS, count=1)
check(not has_hidden_guard(_mut, '.cbg-seg'), "MUTATION: a removed [hidden] guard is detectable")

# ── B · every JS mount id resolves to an id in the file
# (both static id="…" markup AND ids created dynamically as id='…' in JS strings)
ids_present = set(re.findall(r'\bid=["\']([^"\']+)["\']', station))
mount_ids = set(re.findall(r'getElementById\("([^"]+)"\)', station))
check(len(mount_ids) > 10, "fixture: found the station's mount ids")
for mid in sorted(mount_ids):
    check(mid in ids_present, f'getElementById("{mid}") has no matching id in the markup/JS')
# FIRE: rename a mount id everywhere it is declared → it no longer resolves
_mut2 = set(re.findall(r'\bid=["\']([^"\']+)["\']',
                       re.sub(r'id=(["\'])cbg-detail\1', r'id=\1cbg-detailX\1', station)))
check('cbg-detail' not in _mut2, "MUTATION: a renamed mount id is detectable")

# ── C · <script src>: assets resolve on disk; the two emitted data globals are referenced
srcs = re.findall(r'<script src="([^"]+)"', station)
for src in srcs:
    if src.startswith("assets/"):
        check((shell / src).is_file(), f'<script src="{src}"> does not resolve in the shell')
check("./c4-graph.js" in srcs, "station references the emitted ./c4-graph.js (window.GABE_C4)")
check("./sim.data.js" in srcs, "station references the emitted ./sim.data.js (window.GABE_SIM)")
check("assets/sim-panel.js" in srcs, "station loads the shared assets/sim-panel.js")

# ── D · shared GABE_SIM_PANEL contract, symmetric across both hosts
check("window.GABE_SIM_PANEL" in panel, "sim-panel.js defines window.GABE_SIM_PANEL")
_ret = re.search(r'return\s*\{([^}]*)\}', panel, re.S)
_ret = _ret.group(1) if _ret else ""
for key in ["openDetail", "openEntityDetail", "stageSummary", "resetPanel"]:
    check(key in _ret, f"sim-panel.js returns the {key} surface")
check("window.GABE_SIM_PANEL" in station and 'src="assets/sim-panel.js"' in station,
      "station wires the shared sim-panel.js")
check("window.GABE_SIM_PANEL" in lab and "../../assets/sim-panel.js" in lab,
      "the arch-graph lab wires the same shared sim-panel.js")
for key in ["openDetail", "openEntityDetail", "resetPanel"]:
    check(("PANEL." + key) in station, f"station calls PANEL.{key}")
    check(("PANEL." + key) in lab, f"lab calls PANEL.{key}")

# ── E2 · revert-green fixes pinned (slice-1 fresh review): esc() on the subject,
# the drag gate, and the contract constants all reverted green before these.
check("esc(trunc(SIM.subject" in station, "the change strip escapes SIM.subject (XSS pin)")
check("esc(SIM.subject)" in station, "the commit modal escapes SIM.subject (XSS pin)")
_m3 = station.replace("esc(trunc(SIM.subject,64))", "trunc(SIM.subject,64)")
check("esc(trunc(SIM.subject" not in _m3, "MUTATION: a stripped strip-esc is detectable")
check("REDUCED || !!dragging || skipAnimOnce" in station,
      "drawExpansions gates the fly-in on drag + the release render")
check("GG.flowDots(host,pathEl,fill,!!dragging)" in station,
      "flowDots renders static dots while dragging (via the shared asset)")
check("skipAnimOnce=true; rerenderKeepPanel()" in station,
      "drag release re-renders (dots re-animate, selection restored)")
check("pointer-events:none" in re.search(r'\.cbg-root \.xcontlabel\{[^}]*\}', CSS).group(0),
      "the container label is pointer-transparent (dead-zone pin)")
check('["drift-ring",22]' in station, "drift ring keeps the contract radius 22 (≠ ok-ring 19)")
_et = re.search(r'\.cbg-root \.e-touch\{[^}]*\}', CSS).group(0)
check("stroke-width:1;" in _et and "opacity:.55" in _et,
      "e-touch keeps the lab constants 1/.55")
check("r=Math.min(r, d*0.5)" in station, "rimPull is clamped (never past the far anchor)")
check("panelTarget = { edge:" in station, "selectEdge records its panel target")
check("panelTarget = { l2:" in station, "map-mode L2 cards record their panel target")
check("function syncOpenAll" in station and station.count("syncOpenAll()") >= 2,
      "the Open/Close-all face derives from `expanded` in the render path")
check("cancelContTap()" in station and "pendingCont" in station,
      "piece/wire clicks cancel a pending container single-click")
check('regNode(contWrap, "ent:"+slug' in station,
      "an exploded entity re-registers on its container (visible selection ring)")

# ── E3 · the DOSSIER (port slice 2): PURPOSE/STRUCTURE/SIGNATURE/TESTED-BY over
# the emitter's per-node det block — honest-empty at every level.
# the dossier + icon grammar now lives in assets/graph-grammar.js (shared by BOTH
# stations — extracted at the recorded trigger when the archive adopted the grammar)
check("window.GABE_GRAPH_GRAMMAR" in grammar, "graph-grammar.js defines the shared factory")
check('src="assets/graph-grammar.js"' in station, "the change graph loads the shared grammar")
check("window.GABE_GRAPH_GRAMMAR" in station, "the change graph consumes the factory (guarded)")
check("function dossierHTML(det" in grammar, "the shared asset defines the dossier renderer")
check("if (!det) return \"\";" in grammar, "dossier is honest-empty (no det → no dossier)")
for fn in ["docSect", "structSect", "sigSect", "casesSect", "fkSect", "journeysSect", "payloadSect"]:
    check(("function " + fn + "(") in grammar, f"dossier section {fn} in the shared asset")
check("dossierHTML(n.det" in station, "the L2 card renders the dossier")
check("dossierHTML(l2n.det" in station, "the sim piece card JOINS the dossier (slice 2)")
check("table.ptab" in CSS and ".uqchip" in CSS and ".cid" in CSS,
      "the dossier table vocabulary is styled")
check('"structure (" + (det.cols.length + (det.cols_more || 0))' in grammar,
      "STRUCTURE headlines the FULL column count (shown + capped)")
check('"tested by (" + n + ")"' in grammar and "cases_more" in grammar,
      "TESTED-BY headlines the full ledger count, cap named")
# cross-entity test JOURNEYS (criterion A) — the persist-join's det.test_journeys, rendered in the dossier
check('"journeys (" + n + ")"' in grammar and "test_journeys_more" in grammar,
      "JOURNEYS headlines the full count, cap named")
check("casesSect(det) + journeysSect(det)" in grammar,
      "the dossier appends the test-journeys section after cases")
check("test_journeys" in grammar and "starts here and travels out" in grammar and "reached by a cross-entity test" in grammar,
      "journeys render the traveled entities with kind-specific ENTRY/STOP framing")
# response PAYLOAD floor — an endpoint's resp-schema field count, rendered after the signature
check("sigSect(det) + payloadSect(det)" in grammar and "field" in grammar and "ferried" in grammar,
      "the dossier renders the response payload field-count after the signature")
# (an earlier `X not in s.replace(X,'')` mutation line was tautological — always
# true whether or not X existed; for substring pins the presence check IS the gate)
check("function stateCls" in grammar and "st-skip" in grammar,
      "case states are three-valued (skip is never styled as a failure)")
check("route-file coverage" in grammar,
      "route-literal FILE credits render as a neutral fact, not a case row")
check("ICONSETS" in grammar and "lucide" in grammar and "classic" in grammar and "solid" in grammar,
      "the three icon sets live once, in the shared asset")
check("table-layout:fixed" in CSS and "overflow-wrap:anywhere" in CSS,
      "ptab tables cannot overflow the panel (fixed layout + wrap)")
check('var lineStyle = "direct"' in station,
      "the change graph defaults to DIRECT lines (Bowed is the archive's — operator 2026-08-13)")

# ── E4 · slice 3: journeys · nav history · corner boxes ──
check("function buildJourneys" in station, "journeys derive from the L2 wires (+ the SIM change walk)")
check(".slice(0,20)" in station and station.count(".slice(0,20)") >= 2,
      "journey steps are capped at 20 (both walk kinds)")
check("jrnResolved" in station and "SELREG.nodes[k]" in station,
      "journey steps resolve against SELREG at PLAY time (layout switches never break a walk)")
check("function navVisit" in station and "function navTouch" in station and "function goBack" in station,
      "the nav trail: link travel pushes, plain clicks touch, ← pops")
check("navStack.length>6) navStack.shift()" in station, "the trail is 6-deep")
check("navVisit(key); landOn(key);" in station,
      "jumpToNode = navVisit + landOn (travel always records the chain)")
check('id="cbg-keys"' in station and 'class="cbg-keys min"' in station,
      "the Controls corner box exists and STARTS minimized")
check("'<div class=\'cbg-legend\' id=\'cbg-legend\'>'" in station.replace('"', "'") or
      '"<div class=\'cbg-legend\' id=\'cbg-legend\'></div>"' in station,
      "the legend TAIL is created INSIDE the Legend corner box")
check('<div class="cbg-legend" id="cbg-legend"></div>' not in station,
      "the full-width bottom legend bar is gone (corner-box ruling, lab round 36)")
# ── E4b · TOOLBAR REDESIGN (operator 2026-08-13, Option B): one dense row — the
# journeys select folds behind a ▷ popover with a count badge; Open-all is icon-only.
check('id="cbg-jrnBtn"' in station and 'id="cbg-jrnCount"' in station,
      "the journeys picker is a ▷ button + count badge (the ~210px select left the toolbar)")
check('id="cbg-jrnPop"' in station and 'id="cbg-jrnSel"' in station.split("cbg-jrnPop",1)[1][:220],
      "the journeys select lives inside the #cbg-jrnPop popover")
check(".cbg-jrnbtn[hidden]" in CSS,
      "the icon journeys button honors [hidden] (author display beats the UA rule — the stepper replaces it in a walk)")
check('btn.setAttribute("data-face"' in station and "b.getAttribute(\"data-face\")" in station,
      "Open-all is icon-only; its semantic face survives on data-face (panel logic + probe)")
check("_CLOSE_ICON" in station and "_OPEN_ICON" in station,
      "syncOpenAll swaps an expand/collapse ICON (round-36 grammar), not text")

# ── E · honest-empty contract: the station degrades when GABE_SIM is null
check("degradePanel" in station, "station has a degrade path (no change in flight)")
check(re.search(r'window\.GABE_SIM\s*\|\|\s*null', station) is not None,
      "station reads window.GABE_SIM defensively (|| null)")

# ── F · the codebase-ARCHIVE station (ecosystem + past-phase replay) ──
aCSS = re.sub(r'/\*.*?\*/', ' ', archive, flags=re.S)
a_subs = hidden_subjects(archive)
for s in sorted(x for x in a_subs if display_forced(aCSS, x)):
    check(has_hidden_guard(aCSS, s), f"archive: hidden {s} is display-forced but has no {s}[hidden] guard")
a_ids = set(re.findall(r'\bid=["\']([^"\']+)["\']', archive))
a_mount = set(re.findall(r'getElementById\("([^"]+)"\)', archive))
check(len(a_mount) > 6, "archive: found the mount ids")
for mid in sorted(a_mount):
    check(mid in a_ids, f'archive: getElementById("{mid}") has no matching id')
a_srcs = re.findall(r'<script src="([^"]+)"', archive)
for src in a_srcs:
    if src.startswith("assets/"):
        check((shell / src).is_file(), f'archive: <script src="{src}"> does not resolve')
check("./c4-graph.js" in a_srcs, "archive loads the emitted ./c4-graph.js")
check("./sim-archive.js" in a_srcs, "archive loads the committed ./sim-archive.js (window.GABE_SIM_ARCHIVE)")
check("window.GABE_SIM_ARCHIVE" in archive, "archive reads window.GABE_SIM_ARCHIVE")
check("window.__ecotest" in archive, "archive exposes the __ecotest probe hook")
check("eco-feature" in archive, "archive builds the feature/phase dropdown (#eco-feature)")
# the Close/Open-all + Connections controls (change-graph parity) and the intra-edge machinery
check('id="eco-openAll"' in archive, "archive has the Close/Open-all toggle")
check('id="eco-conns"' in archive, "archive has the Connections toggle")
check(".xedge.intra" in aCSS, "archive styles the intra (piece↔piece) edge class")
check("intraEdgesFor" in archive, "archive derives intra edges (phase intra_edges | C4 L2 fk)")
# an exploded entity's big body vanishes; the container + pieces replace it (change-graph parity)
check(".node.exploded" in aCSS and "opacity:0" in aCSS.split(".node.exploded",1)[1][:40],
      "archive: an exploded entity's body is hidden (.node.exploded opacity:0)")
check('classList.toggle("exploded"' in archive, "archive: the exploded class is toggled per entity at draw")
# cross-entity PIECE coupling in the ecosystem view (the emitter's cross_edges)
check(".xedge.xcross" in aCSS, "archive styles the ecosystem cross-entity piece edge (.xedge.xcross)")
check("DATA.cross_edges" in archive, "archive reads the emitter's piece-level cross_edges")
check("declutter" in archive, "archive declutters entity spacing so exploded containers do not overlap")
# defaults MIRROR the change graph (entities ring · inside force)
check('insideLayout = "force"' in archive, "archive default inside layout = force (change-graph parity)")
check("if(!slugs.length) return;" in archive,
      "archive: the Close/Open-all toggle governs pieces in BOTH ecosystem + phase modes")
# FIRE: if the exploded-hide rule were dropped, the body would overlap the pieces again
_amut = re.sub(r'\.node\.exploded\s*\{[^}]*\}', '', aCSS, count=1)
check(".node.exploded" not in _amut, "MUTATION: a removed exploded-hide rule is detectable")
# an `unclaimed` L1 bucket (counts:null, no l2) must be excluded — else radius()/labels
# deref null and the map crashes on load (adversarial-verify HIGH). Filter at ingest.
check('filter(function(n){ return n.kind==="entity"; })' in archive,
      "archive filters L1 to entity nodes (unclaimed bucket excluded — crash guard)")
# centre-edge suppression must be PER-PAIR (only pairs whose piece-level coupling was
# actually drawn), not a blanket both-exploded gate — else an unreplaced pair (empty/
# stale cross_edges, cls-less model) hides the blast coupling with nothing in its place.
check("_drawnPairs[r.s" in archive and "suppressReplacedEdges" in archive,
      "archive suppresses a centre edge ONLY for pairs whose piece-level replacement was drawn")
check("explodeAll && showConns && hasXcross && bothExp" not in archive,
      "archive no longer uses the blanket both-exploded xhide gate (edgeless-blast regression guard)")
# the Connections toggle governs phase cross edges too (uniform contract, verify NIT)
check("if(selPhase && showConns){ (selPhase.cross_edges" in archive,
      "archive: the Connections toggle gates phase cross edges as well as intra")
# change-graph parity (r3-followup): force feeds on the intra edges (else force≈ring);
# intra edges inherit the entity colour; cross edges flow; collapse/resize panel present.
check("forceLayout(nds,ied," in archive,
      "archive: inside-force layout is fed the intra edges (reshapes; was []=repulsion≈ring)")
check("pth.style.stroke = isHot ? STAGE_COLOR[curStage] : col" in archive,
      "archive: intra edges inherit the entity colour, stage colour when hot")
check('class:"xedge xcross"' in archive and "flowDots(wireL, pth" in archive,
      "archive: ecosystem cross edges wear entity GRADIENTS + flow dots (the shared grammar — the amber marching dash died with the port)")
check('src="assets/graph-grammar.js"' in archive and "window.GABE_GRAPH_GRAMMAR" in archive,
      "archive consumes the shared graph-grammar.js (guarded)")
check('var lineStyle = "bowed"' in archive,
      "the archive defaults to BOWED lines (its signature — the change graph reads direct)")
check("dossierHTML(mn?mn.det:null" in archive.replace(" ",""),
      "the archive piece card joins the det dossier")
check('id="eco-resizer"' in archive and 'id="eco-sideToggle"' in archive,
      "archive has the resize divider + collapse toggle (change-graph panel parity)")
check(".eco-side.collapsed" in aCSS and "setSideCollapsed" in archive,
      "archive wires the collapse-to-a-bar panel")
# Tier 1: the structural id-card (data structures · API · principal fn) from the
# model's c4-graph L2 `ids` block, rendered honest-empty with the change-graph chips.
check("idCardHTML" in archive and "function modelNode(" in archive,
      "archive renders the model's structural id-card from its L2 ids block")
check("ids.principal" in archive and "'principal'" in archive,
      "archive surfaces the principal function as the panel lead")
check("GG.chips.dtChip" in archive and "GG.chips.epChip" in archive and ".idchip" in aCSS,
      "archive consumes the typed chip renderers from the shared grammar (+ its styles)")
check('idCardHTML(sids)' in archive, "archive's piece panel injects the id-card")
# FIRE: idCardHTML must be honest-empty (no card when the model carries no ids)
check("function idCardHTML(ids){ if(!ids) return" in archive,
      "archive id-card is honest-empty (no ids → nothing rendered) — regression guard")
# FIRE: if the openAll toggle were hidden in phase mode again, the old assignment returns
check("style.display = selPhase" not in archive,
      "archive: the Close/Open-all toggle is NOT hidden in phase mode (regression guard)")

# ── G · the committed example's det obeys the emitter contract (drift guard) ──
_exjs = (shell / "example" / "codebase-graph-station" / "c4-graph.js").read_text(encoding="utf-8")
_body = _exjs.split("window.GABE_C4 = ", 1)[1].split(";\nwindow.GABE_C4_COLORS", 1)[0]
_ex = json.loads(_body)
_dets = [n["det"] for g2 in _ex["l2"].values() for n in g2["nodes"] if "det" in n]
check(len(_dets) > 100, "example: det present at scale")
check(all(c.get("state") != "file" for d in _dets for c in d.get("cases", [])),
      "example: no file-aggregate pseudo-row impersonates a case")
check(all(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", u) for d in _dets for u in d.get("uqs", [])),
      "example: uqs are bare column names (normalized, never constraint exprs)")
check(all(len(d.get("cols", [])) <= 10 and len(d.get("cases", [])) <= 60 for d in _dets),
      "example: the emitter caps hold in the committed payload")
check(not any(n.get("resp") == "—" for g2 in _ex["l2"].values() for n in g2["nodes"]),
      "example: the em-dash resp default never ships")
_seen_cases = [ (c.get("corpus"), c.get("cid"), c.get("name"))
                for d in _dets for c in d.get("cases", []) ]
check(all(len({k for k in ((c.get("corpus"), c.get("cid"), c.get("name")) for c in d.get("cases", []))})
          == len(d.get("cases", [])) for d in _dets),
      "example: no duplicated case rows inside one dossier")

# ── H · KIND COVERAGE (operator 2026-08-13): both stations draw the FULL L2 surface
#        — models + schemas in the core, API endpoints on the border — not models only.
# change graph: the sim BEAT pieces stay .xpiece (port1's count pin); the full surface
# draws as a SEPARATE .xsurf[data-kind] layer the sim overlays (beat stays model-only).
check("function surfaceLayout(" in station,
      "change graph derives the full L2 surface (surfaceLayout: models+schemas core, endpoints border)")
check('class:"xsurf","data-kind":kind' in station,
      "change graph draws surface pieces as .xsurf[data-kind] (kept off the .xpiece beat count)")
check(".cbg-root .xsurf{" in CSS, "change graph styles the surface piece class")
check("pos[ep.id]={ x:cx+contR*Math.cos" in station,
      "change graph places endpoints on the container BORDER (radius = contR)")
check('class:"e-touch"' in station and 'regEdge(p, "touch"' in station,
      "change graph wires endpoints to the pieces they touch (border → core)")
check("function declutterExpanded(" in station,
      "change graph declutters exploded entities so the bigger containers never overlap")
# archive: the full surface as .xpiece[data-kind]; endpoints ride the border via insidePos.
check('n.kind==="model"||n.kind==="schema"||n.kind==="endpoint"' in archive,
      "archive ecoPieces admits models + schemas + endpoints (was model-only)")
check('class:"xpiece","data-kind":kind' in archive,
      "archive tags every piece with its data-kind (probe/selection discriminator)")
check('p.kind!=="endpoint"' in archive,
      "archive insidePos partitions the core (models+schemas) from the border (endpoints)")
check("ICONSETS[ICONSET].ep(g, 6.5," in archive and "ICONSETS[ICONSET].schema(g, 7," in archive,
      "archive dispatches the endpoint + schema glyphs by kind (was hard-coded model)")
check('if(selPhase && kind==="model")' in archive,
      "archive keeps the phase BEAT encoding model-only (endpoints/schemas render inert)")
check('class:"xedge touch"' in archive and ".xedge.touch" in aCSS,
      "archive draws the border → core touch wires")
check("pieceKind:function(k)" in archive, "archive exposes the per-kind probe counter")
# reverting ecoPieces to model-only is caught by the widened-filter presence check
# ABOVE — for a substring pin the presence check IS the mutation gate (the lesson this
# file records at the tautological-`X not in s.replace(X,'')` note; a fake .replace()
# mutation here would be theatre, always-true whenever the string exists). The behavioral
# proof that the widened filter actually RENDERS the kinds lives in port6/port7 (real
# browser: pieceKind("endpoint"/"schema")===fixture, touchEdges()>0).

# ── I · WEB→API BRIDGE (Path A frontend arm): the station draws the web pieces
#        (Screens) + the inferred fetch→endpoint bridge edges. STATIC presence pins
#        (each IS its own mutation gate — a fake .replace() would be theatre); the
#        REAL render proof is a headless-chrome check against the P3-regen example
#        (drill recipe → 7 bridges/8 screens · allergen → 1 bridge/1 cross-entity
#        stub · explode → 11 web surface + 48 bridges), run when the render changes.
check(".cbg-root .e-bridge{" in CSS,
      "bridge edges carry a .e-bridge class (dashed --c-fn-web wire)")
check('web:"#e8590c"' in station and 'web:"Screens"' in station,
      "the web piece kind is registered (KIND_COLOR/KIND_LABEL Screens)")
check('else if(n.kind==="web"){' in station,
      "the L2 drill draws a web 'screen' glyph")
# ── PRE-C: the column station survives a wave-C kind (middleware/provider/flag/prompt) — no NaN column ──
check('middleware:"#7048e8"' in station and 'middleware:"Middleware"' in station,
      "pre-C: the 4 wave-C kinds are registered in KIND_COLOR/KIND_LABEL")
check('if(ord2.indexOf(k)<0) ord2.push(k)' in station and 'if(ord3.indexOf(k)<0) ord3.push(k)' in station,
      "pre-C: ord2/ord3 append an unknown kind from layout.l2.order (aligned columns + headers)")
check('kc[n.kind]!=null?kc[n.kind]:ord2.length' in station,
      "pre-C: the column x guards kc[n.kind] — an unknown kind gets a real column, never undefined*COLW=NaN")
check('(KIND_LABEL[kind]||kind)' in station,
      "pre-C: the column header falls back to the raw kind name for a newer emitter's kind")
# ── legend pass (2026-09-06): BOOT + TASK in every METHOD roster; a TASK/unknown verb is never coerced to GET; stream is a card row;
#    provider ≠ web colour; the c4-only station never draws `dispatches` (function-level, levels only) ──
import re as _re
_gg = (shell / "assets" / "graph-grammar.js").read_text(encoding="utf-8")
check('TASK: "var(--m-task)"' in _gg and 'function taskMark(g, r, col)' in _gg and _gg.count('if (method === "TASK") { taskMark(g, r, col); return; }') == 3,
      "legend pass: the shared grammar knows BOOT/TASK and every icon set draws the TASK queue mark")
check('TASK:"var(--m-task)"' in station and '--m-task:#a78bfa' in station and '||"GET"' not in station and 'methodOf(label)||null' in station and 'methodOf(p.label)||null' in station,
      "legend pass: the station's METHOD roster has BOOT/TASK and an unknown verb falls to the muted mark, never to GET")
check('if(n.stream) h+=rowKV("delivery"' in station, "legend pass: a streaming endpoint's card carries a Delivery row")
_kc = {m.group(1): m.group(2) for m in _re.finditer(r'(\w+):"(#[0-9a-f]{6})"', station[station.find("var KIND_COLOR"):station.find("var KIND_COLOR") + 400])}
check(_kc.get("provider") and _kc.get("web") and _kc["provider"] != _kc["web"], f"legend pass: provider and web wear different colours ({_kc.get('provider')} vs {_kc.get('web')})")
check("e-dispatches" not in station and 'kind==="dispatches"' not in station and "dispatches:{" not in station,
      "legend pass: the c4-only station draws no `dispatches` wire (function-level edges live in levels.js; prose may name the mechanism)")
check('TASK: "#a78bfa"' in panel and '"#868e96"' in panel, "legend pass: sim-panel's METHOD_COLOR knows BOOT/TASK; an unknown verb still falls to #868e96")
_mc_p = dict(_re.findall(r'(\w+): "(#[0-9a-f]{6})"', panel[panel.find("var METHOD_COLOR"):panel.find("var METHOD_COLOR") + 200]))
_mc_g = dict(_re.findall(r'(\w+): "(#[0-9a-f]{6})"', _gg[_gg.find("var METHOD_COLOR"):_gg.find("var METHOD_COLOR") + 200]))
check(_mc_p and _mc_p == _mc_g, f"legend pass: graph-grammar's chip roster equals sim-panel's METHOD_COLOR ({_mc_g} vs {_mc_p})")
check('e.kind==="bridge" && e.from_slug===slug' in station,
      "the L2 drill draws a bridge pass over DATA.cross_edges (from_slug === drill)")
check('bridgeStub[e.to]' in station and 'reached by a fetch bridge' in station,
      "a cross-entity bridge endpoint gets a synthetic stub (mirror the external target)")
check('regEdge(p, "bridge"' in station and 'bridge:"bridge"' in station,
      "bridge edges register with the 'bridge' kind + edgeWord")
check("var WEB_UNMATCHED" in station and "fetch unmatched (no endpoint named)" in station,
      "an unmatched fetch marks its screen hollow-dashed with the raw method+path")
# the SIM-gated explode: web bucket + web surface glyph + a DATA-bridge pass
check('else if(n.kind==="web"){ web.push(n)' in station and "web:web, contR:webR" in station,
      "surfaceLayout collects web pieces on an outer ring (web-less → radius unchanged)")
check('else if(kind==="web"){ var unm=WEB_UNMATCHED' in station,
      "the explode drawSurf draws a web 'screen' glyph")
check('if(e.kind!=="bridge") return;' in station,
      "the explode draws a DATA-bridge pass (screen → endpoint over the surface)")
check("bridgeEdges: function()" in station,
      "the __cbgtest probe exposes the bridge-edge count")
# the committed EXAMPLE payload actually carries web data (a web-stripping regen fails here)
_wst = _ex.get("stats", {}).get("web") or {}
check(_wst.get("present") is True and _wst.get("matched", 0) > 0,
      "example c4-graph.js carries a present web arm with matched bridges")
_brk = [e for e in _ex.get("cross_edges", []) if e.get("kind") == "bridge"]
check(len(_brk) == _wst.get("matched"),
      "example: bridge cross_edges count == stats.web.matched (every match is a wire)")
check(any(n.get("kind") == "web" for g2 in _ex["l2"].values() for n in g2["nodes"]),
      "example: web pieces present as L2 nodes (the Screens the drill draws)")
check(all("m" in u and "p" in u and "from" in u for u in _wst.get("unmatched", [])),
      "example: every unmatched fetch names its method + path + source screen")

# ── J · ENDPOINT `behind` FLOOR (graft call-tree mass, a view-only complexity badge)
check("function behindBadge(" in station and ".cbg-root .behind-badge rect{" in CSS,
      "the behind badge has a draw helper + its muted pill style")
check(station.count("behindBadge(g, n.behind)") >= 1 and "behindBadge(g, node.behind)" in station,
      "both endpoint render paths (drill + explode) draw the behind badge")
check('h+=rowKV("behind"' in station and "behindBadges:function()" in station,
      "the detail card shows a behind row + the __cbgtest probe counts the badges")
_bst = _ex.get("stats", {}).get("behind") or {}
check(_bst.get("present") is True and _bst.get("scored", 0) > 0,
      "example c4-graph.js carries a present behind arm with scored handlers")
_beps = [n for g2 in _ex["l2"].values() for n in g2["nodes"]
         if n.get("kind") == "endpoint" and "behind" in n]
check(_beps and all(isinstance(n["behind"].get("fns"), int)
                    and isinstance(n["behind"].get("depth"), int) for n in _beps),
      "example: endpoints carry a {fns, depth} behind floor (ints, no guessed shape)")

# ── B12 (entity models, 2026-09-06): the codebase-graph station stays CLAIM-ONLY — it reads l1/l2 by slug and never the `models` block
#    (re-clustering it would drag sim-panel.js, two consumers, into the pass; trigger to revisit: a change simulated against a derived feature).
check('DATA.models' not in station and 'GABE_C4.models' not in station and '.models[' not in station and 'GABE_C4.models' not in panel and '.models[' not in panel,
      "B12: codebase-graph.html / sim-panel.js read the entity-models block — the station is claim-only by design")
print(f"codebase-graph battery: {pass_} passed, {fail} failed")
sys.exit(1 if fail else 0)
PY
PYRC=$?

# ── EXECUTED render FIRE+SILENT (gap #6): the python checks string-match the grammar source;
#    this actually RUNS journeysSect/payloadSect via a node shim (no browser) to prove real output ──
node -e '
global.window={}; global.document={createElement:function(){return {style:{},setAttribute:function(){},appendChild:function(){},append:function(){},getContext:function(){return {};}};}};
var fs=require("fs"); eval(fs.readFileSync(process.argv[1],"utf8"));
var GG=window.GABE_GRAPH_GRAMMAR(), ok=0, bad=0;
function a(c,m){ if(c){ok++;}else{bad++;console.error("  render FAIL:",m);} }
var j=GG.journeysSect({sig:{},test_journeys:[{cid:"C1",corpus:"api",entities:["a","b"],comp:2}],test_journeys_more:3});
a(/journeys \(4\)/.test(j)&&/starts here/.test(j)&&/C1/.test(j),"journeysSect FIRE (endpoint=ENTRY, count+more)");
a(GG.journeysSect({})===""&&GG.journeysSect({payload:{n:1}})==="","journeysSect SILENT (no test_journeys)");
a(/reached by a cross-entity test/.test(GG.journeysSect({test_journeys:[{cid:"C2",corpus:"web",entities:["x","y"],comp:2}]})),"journeysSect STOP framing (model/fn, no sig)");
var p=GG.payloadSect({payload:{n:3,schema:"WOut"}});
a(/3 fields ferried/.test(p)&&/WOut/.test(p)&&/\(response\)/.test(p),"payloadSect FIRE (N fields + schema + response)");
a(GG.payloadSect({})==="","payloadSect SILENT (no payload)");
a(/1 field ferried/.test(GG.payloadSect({payload:{n:1,schema:"X"}})),"payloadSect singular (1 field)");
console.log("  render FIRE+SILENT: "+ok+"/"+(ok+bad)+" executed");
process.exit(bad?1:0);
' "$SHELL_SRC/assets/graph-grammar.js"
NODERC=$?
if [ "$PYRC" -eq 0 ] && [ "$NODERC" -eq 0 ]; then exit 0; else exit 1; fi
