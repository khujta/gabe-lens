#!/usr/bin/env bash
# Gabe Universe station battery — a STATIC/STRUCTURAL executable contract for the
# twin center's "Gabe Universe" station (templates/center/shell/gabe-universe.html):
# the 5C 3D graph (lifted from the graft-adoption spike) fed LIVE by window.GABE_C4,
# with the element-components card ported to read the real per-node dossier (det).
#
# WHY THIS EXISTS: the render gates never EXECUTE the station's inline engine, and a
# whole class of bug ships green — the data feed dropped, the live card reverting to
# a toy field, the chip-class collision, the journeys field-mismatch (j.entities vs the
# card's old j.to). This battery is node-stdlib/grep only (no browser required), zero-arg,
# and the doctor auto-runs it. Every invariant ships as a FIRE+SILENT pair where the
# structural form allows (a positive present-assert + a guard on the known-bad pattern).
# An OPTIONAL headless-chrome render proof runs against the committed example feed when
# playwright-core + google-chrome-stable are present; it SKIPs loudly otherwise
# (nothing-to-verify is not the same as verified).
# Exit 0 = all pass.
set -u
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
SHELL_SRC="$REPO/templates/center/shell"

python3 - "$SHELL_SRC" <<'PY'
import sys, re, pathlib
shell = pathlib.Path(sys.argv[1])
page  = (shell / "gabe-universe.html").read_text(encoding="utf-8")

pass_ = 0; fail = 0
def t_order(pg):
    i=lambda s: pg.find(s)
    ks=[i('k:"show"'),i('k:"subs"'),i('k:"planets"'),i('k:"wires"'),i('k:"routes"'),i('k:"zDef"')]
    return -1 not in ks and ks==sorted(ks)
def check(cond, msg):
    global pass_, fail
    if cond: pass_ += 1
    else: fail += 1; print("  FAIL:", msg)

# ── 1. data feed + 3D assets are loaded (the station is inert without them) ──
check('src="./c4-graph.js"' in page, "c4-graph.js data feed not loaded (adapter has no input)")
check('src="./assets/3d-bundle.js"' in page, "3d-bundle.js (three.js + ForceGraph3D) not loaded")
check('src="./assets/chip-assets.js"' in page, "chip-assets.js (GLB fleet models) not loaded")
check('window.GABE_C4' in page, "adapter does not read window.GABE_C4")

# ── 2. the live adapter flattens the C4 hierarchy (l1/l2/cross_edges), not the toy NODEDEF ──
check('var NODEDEF=' not in page, "toy NODEDEF survived — the live adapter did not replace the spike's fixed data")
check('_C4.l2' in page and 'cross_edges' in page, "adapter does not flatten l2 + cross_edges")

# ── 3. nav: Gabe Universe is the ACTIVE row, exactly once, and the crumb names it ──
check(page.count('class="navitem on" href="gabe-universe.html"') == 1, "Gabe Universe nav row is not the single active item")
check('<b>Gabe Universe</b>' in page, "topbar crumb does not name the station")

# ── 4. one-row topbar; the spike's title-bar/explorer/hint are hidden, but the CONFIG + LEGEND are REVEALED ──
check(re.search(r'\.bar,\s*#expl,\s*\.hint\{[^}]*display:\s*none', page) is not None,
      "the spike title-bar/explorer/hint are not hidden")
check('#cfg, #expl' not in page and '#cfg, #elegend' not in page,
      "regression: #cfg/#elegend still in the hidden-overlay list (config + legend must be revealed)")
check('<div class="topbar">' in page, "one-row topbar missing")
# config + legend revealed and repositioned clear of the nav/topbar
check('#cfg.cfg{ top:calc(var(--topbarh)' in page, "config panel not repositioned below the topbar")
check('#elegend{ left:calc(var(--navw)' in page, "legend not moved clear of the nav")
# nav minimize + config gear affordances
check('id="navgear"' in page and 'window.__uniCfgToggle' in page, "config gear affordance missing")
check('id="navmin"' in page and 'window.__uniNavToggle' in page, "nav minimize affordance missing")
check('id="navshow"' in page and 'body.nav-min' in page, "nav restore tab / collapse class missing")
# web nodes get a billboard ICON (in `order`), not the fallback primitive cube
check('"screen","web","endpoint"' in page, "web kind not in `order` — web nodes would render as the primitive cube, not the screen icon")

# ── 5. #g is inset by the nav + topbar (not the spike's full-viewport fixed) ──
check(re.search(r'#g\{[^}]*left:\s*var\(--navw\)', page) is not None, "#g not inset by the nav width")

# ── 6. LIVE CARD helpers present (the toy per-kind renderer was replaced) ──
for fn in ("testsSec(det)", "journeysSection(", "payloadSec(det)", "liveConns(n)", "structureSec(n)"):
    check(fn in page, "live card helper missing: "+fn)
check('var cids=function' not in page, "toy cids() single-state test renderer survived")

# ── 7. FIRE+SILENT: journeys read the LIVE field j.entities, NOT the card's stale j.to ──
check('journeyFaces(home, j.entities' in page, "journeys do not read the live det field j.entities")
check('journeyFaces(home, j.to' not in page, "REGRESSION: journeys still read the stale j.to (dead on live det)")

# ── 8. FIRE+SILENT: tri-state test credits attach to .pchip, NOT .chip (explorer-chip collision) ──
check('"pchip st-"+st' in page, "test credits do not use the .pchip class")
check('"chip st-"+st' not in page, "REGRESSION: test credits use .chip — collides with the explorer encoding chips")

# ── 9. ported CSS present (else st-fail / ttag / journeys render uncolored) ──
for css in (".pchip.st-pass", ".pchip.filecov", ".ttag.inferred", ".connbox .cinf .pchip", ".jfaces", ".face.fhome"):
    check(css in page, "ported CSS rule missing: "+css)

# ── 10. the tokens the ported CSS references are DEFINED (missing var → uncolored border) ──
for tok in ("--red:", "--edge:", "--god:", "--font-ui:", "--font-mono:"):
    check(tok in page, "token not defined (ported CSS would render uncolored): "+tok)

# ── 10b. curved connectors: geometry branch present; the control lives in the config LINES pill (NOT the topbar) ──
check('QuadraticBezierCurve3' in page, "curved geometry (QuadraticBezierCurve3 arc) missing")
check('window.__uniCurved?__uniCurve' in page, "connectorWire does not branch straight/curved on the flag")
check('id="curveToggle"' not in page, "the topbar Curved button should be REMOVED (moved into the config LINES pill)")
check('pillHTML("lineStyle"' in page and '__uniSetCurve' in page, "the config LINES (Straight/Curved) control is missing")

# ── 10c. all C4 piece kinds are drawable + a silent-drop is IMPOSSIBLE (pre-C: generic fallback) ──
check('if(!KINDS.web)' in page, "web kind not injected — c4 web pieces would be silently dropped")
check('_genericKind(kind)' in page and 'drawn GENERICALLY' in page,
      "pre-C: an unknown kind must draw GENERICALLY (never a silent drop) + warn")
check('_dropped++;return' not in page.replace(" ", ""),
      "pre-C: the old silent-drop (_dropped++; return) is gone — the guard registers + draws")
# the 4 wave-C L2 kinds are registered so wave C draws them (no NaN, no drop)
for _k in ("middleware", "provider", "flag", "prompt"):
    check(('KINDS.'+_k+'=') in page.replace(" ", ""), "pre-C: KINDS.%s not registered" % _k)
# the 7 wave-C rels carry colour + weight + REL2KIND bucket (pv:0 — inferred floor, never "proven")
for _r in ("depends", "gated_by", "dispatches", "serializes", "reaches", "walls", "fnprompts"):
    check(('RELCOL.'+_r+'=') in page.replace(" ", "") and ('LINKMETA.'+_r+'=') in page.replace(" ", "")
          and (_r+":'") in page.replace(" ", ""), "pre-C: rel %s missing from RELCOL/LINKMETA/REL2KIND" % _r)

# ── 10d. batch-2 layout engine: entity-layout (chain/force/spread) + cluster-core (layer/kind/tests) + 2nd tab ──
check('entLayout:"force"' in page and 'coreBy:"layer"' in page, "CFG missing entLayout/coreBy fields")
check('function recomputeEX' in page and 'function assignSub' in page, "layout recompute/assignSub functions missing")
check('__chainMode' in page, "mode-aware zForce (chain vs force/spread) missing")
check('grp==="entLayout"' in page and 'grp==="coreByBE"||grp==="coreByFE"' in page, "applyCfg missing the entLayout/coreByBE|coreByFE branches")
check('d3ReheatSimulation' in page, "entity-layout change never reheats the sim (nodes would not move)")
check('window.__uniAddLayoutTab' in page and 'cfgtabbar' in page, "the Display|Layout config tab is missing")
check('recomputeEX(CFG.entLayout); (window.__uniAssignSplit?__uniAssignSplit():assignSub(CFG.coreByBE||"kind")); recomputeSubAnchors(); }catch(e){} build' in page, "boot does not assign the per-side cores before the sub-anchors")
# FIRE+SILENT: force/spread compute 3D anchors (EY/EZ), not just a flat X band
check('EY[e]=0; EZ[e]=0;' in page and ('EY[s]=Math.round' in page or 'EZ[s]=Math.round' in page),
      "EY/EZ 3D entity anchors not computed — force/spread would stay flat")

# ── 10e. batch-3: the levels feed drives Use-case / Community / FK-join cores (Guards dropped — no data) ──
check('src="./levels.js"' in page, "levels feed not loaded — usecase/community/fk cores have no source")
check('function _levelsGroupMap' in page and 'window.GABE_LEVELS' in page, "levels group-map join missing")
check('mode==="usecase"' in page and 'mode==="community"' in page and 'mode==="fk"' in page,
      "assignSub missing the usecase/community/fk levels-backed branches")
check('fk_communities' in page and 'usecases' in page and 'communities' in page, "levels map fields not read")

# ── 10f. batch-4: functions layer toggle · Guards core (data-backed) · LINES in config ──
check('function _buildFnData' in page and 'function toggleFns' in page, "functions layer (fn_nodes toggle) missing")
check('fn_nodes' in page and 'fn_edges' in page, "functions do not read the levels fn_nodes/fn_edges")
check('grp==="showFns"' in page and 'grp==="lineStyle"' in page, "applyCfg missing the showFns/lineStyle branches")
check('__uniAssignSplit=function' in page and 'CFG.coreByBE' in page and 'CFG.coreByFE' in page,
      "the PER-SIDE core split (__uniAssignSplit / coreByBE / coreByFE) is gone")
check('{v:"guards"' not in page, "the guards core must be dropped (operator: no value backend or frontend)")
check('isFinite(n.x)) _npos' in page, "the _npos NaN guard is missing (a transient add would spew computeBoundingSphere NaN)")

# ── 10g. batch-5: config re-tabbed Planets|Universe · master planet-assets toggle · orbit-around-click ──
check('class="cfgtab' not in page and 'cfgnote' in page,
      "the config panel must be TABLESS (batch 31 — everything lives in the fleet; the note explains)")
check('__uniFlPanes.wires=' in page and '__uniFlPanes.routes=' in page and '"Transports"' in page,
      "the Connections/Transports drawer panes are gone")
check('(fr.right+10)' in page, "the drawer lost its docking gap beside the fleet")
# batch 32: compaction — one ×, icon pills, opacity dots, speed steppers, no repeated labels
check('class="flsx"' in page and 'flsmin' not in page,
      "the drawer must have ONE plain × (the boxed button pair is back)")
check('_opGlyph' in page and 'fill-opacity' in page,
      "transparency pills lost their opacity DOTS (faint/ghost/film words must ride the hover)")
check('id="trMinus"' in page.replace("'",'"') or '"trMinus"' in page,
      "the transport speed lost its −/+ steppers")
check('overflow-x:hidden' in page,
      "drawer panes may scroll horizontally again (compaction regression)")
check('rt.querySelector("#curveAmtRng")' in page,
      "REGRESSION: the curve slider bound via document.getElementById — rt is DETACHED, the listener never attaches")
# batch 33: the transport speed LADDER — 7 positions, ×√2 per stop, numbered-dot thumb
check('_ts.min="-2"; _ts.max="4"; _ts.step="1"; _ts.value="0";' in page and '0.1*Math.pow(Math.SQRT2,pos)' in page,
      "the speed ladder is gone (−2..+4 positions, default 0.1 = two stops under the old 0.3)")
check('id="trSpdBadge"' in page.replace("'",'"') or '"trSpdBadge"' in page,
      "the numbered-dot thumb (speed badge) is gone")
# batch 34: one-row wire kinds + per-kind on/off + honest glow label
check('data-wtog=' in page and '__uniBeamPrev' in page and 'class="cfgrow wkrow"' in page,
      "wire kinds lost their one-row layout or the per-kind on/off toggle")
check('NOT speed; speed lives in Transports' in page and 'per kind: sample' not in page,
      "the glow label must say it is NOT speed (and the old footer note stays gone)")
check('applies WHILE a focus highlight is active' in page,
      "the FOCUS group no longer explains WHEN it applies")
# batch 35: the entity gradient (the 2D lab device, ported) — per-kind toggle, vertex colors
check('vertexColors:(_gr&&band==null)' in page and 'data-wgrad=' in page and 'ENT[_cs.ent]' in page,
      "the entity-gradient option is gone (vertex-color wires + per-row toggle + entity colors threaded)")
check('CONN[k].grad=!!CONN0[k].grad' in page,
      "wire reset must RESTORE the stock gradient flag (fk/calls default ON)")
check("style:'sparse',density:2.7,trust:0.9,grad:true" in page and "style:'solid',density:2,trust:0.6,grad:false,thick:1,gmode:'type'" in page,
      "the operator's stock CONN config drifted (fk grad on; calls flat #817536, grad off, gmode type)")
check('{ fk:0.9, bridge:0.8, calls:0.5, imports:1, rollup:0, access:0.7, dispatches:0.7 }' in page and '__uniCurveAmt=0.6' in page and 'lineStyle:"curved"' in page,
      "the operator's stock glow/curve defaults drifted (rollup hidden = beam 0, access glow 0.7)")
check('function _raySegDist' in page and 'w=ray.origin.clone().sub(A)' in page and 'showLinkPanel(wbest.l)' in page,
      "wire clicking is gone (ray-segment pick → connection panel)")
check('__uniHLMode();       // a FOCUS option while glowing' in page,
      "focus options no longer BITE (auto-switch to focus mode on click)")
check('id="flscopy"' in page.replace("'",'"') or '"flscopy"' in page,
      "the Connections copy-settings button is gone")
check('window.__uniLastCopy=txt' in page and '(key==="wires")?"":"none"' in page,
      "copy-settings lost its payload stash or its Connections-only gate")
check('pillHTML("warOn"' not in page and 'zonehint' in page, "the Zones On/Off master pill must be GONE (fleet zone columns own it) with a zonehint in its place")

# ── 10h. batch-6: assets OFF default · Zones inline master toggle · core 2-col grid · connector throttle ──
check('zDef:0, zAtk:0' in page, "the four war zones must default OFF per entity (the fleet zone columns are the only control)")
check('zonesoff' in page, "zone icons do not dim when the master toggle is off")
check('data-grp="coreByBE"], #cfg .pill[data-grp="coreByFE"],' in page and '{ display:grid' in page, "the per-side core pills are not a 2-column grid (they would overflow)")
check('if(force || _wtick%3===0) updateConnectors' in page, "per-tick connector rebuild is not throttled (settle stays laggy)")

# ── 10i. batch-7: static fleets · motion master · freeze-on-drag · orbit re-pivot on pointerdown ──
check('var ANIM={ fleets:false' in page, "fleets are not static by default (ANIM.fleets should be false)")
check('if(!ANIM.all) return' in page and 'if(ANIM.fleets && FLEETTICK.length)' in page, "pulseLoop not gated by ANIM (master pause / fleet freeze)")
check('function __uniSetupOrbit' in page and '__uniSetupOrbit(); }catch' in page, "orbit-pivot setup not wired at boot")
check('intersectPlane' in page and 'function _rotRig' in page and 'ctrls.enabled=false' in page, "orbit rigid-rotation around the clicked point (no reposition, no zoom) missing")
check('cam.quaternion.premultiply(q)' in page, "orbit is not a true rigid rotation (P would drift on polar tilt)")
check('id="trSpeedRng"' in page and 'INTC.speed' in page, "transport-speed slider missing")
check('id="motionBtn"' in page, "config-header motion play/pause button missing")
check('id="freezeDragBtn"' in page and '__uniToggleFreezeDrag' in page, "topbar freeze-on-drag toggle missing")
check('zoneshd{ display:flex; align-items:center; justify-content:flex-start' in page, "Zones toggle not placed next to the title (flex-start)")

# ── 10j. batch-9 CLUSTERING: the core drives POSITION (sub-anchor ring + reheat), endpoints ring the
#         entity EDGE (per-kind radial), entities separate (typed link rests + capped charge + containment) ──
check('function recomputeSubAnchors' in page, "sub-anchor ring recompute missing (core cannot re-arrange nodes)")
check('(SUBANCHOR[n.ent]||{})[n.sub]' in page, "zForce does not read the sub anchor — n.sub still decoration-only")
check('else if(grp==="coreByBE"||grp==="coreByFE"){ __uniFreezeForSettle(); (window.__uniAssignSplit?__uniAssignSplit():assignSub(CFG.coreByBE||"kind")); recomputeSubAnchors(); if(window.__uniApplyCapsules) __uniApplyCapsules(); if(Graph){ try{ Graph.d3ReheatSimulation(); }catch(e){} }' in page,
      "the per-side core branch does not re-anchor + re-fold + REHEAT (core change would not move nodes)")
check('grp==="coreBy"){ assignSub(CFG.coreBy); buildClusters()' not in page,
      "REGRESSION: coreBy is decoration-only again (assignSub straight to buildClusters, no reheat)")
check('var KRADF={ endpoint:' in page, "per-kind radial factors missing (endpoints would not ring the edge)")
check('var rmax=R0*1.6; if(r>rmax){ var kc=0.6*alpha*(rmax-r)/r;' in page,
      "soft containment missing (nodes bleed across entity hulls) — boundary 1.6, above the outermost kind ring")
check('function tuneLinkForce' in page and '.ent!==t.ent)?280:40' in page,
      "typed link rest-lengths missing (default rest≈30 springs collapse entities into one mesh)")
check('strength(-60).distanceMax(150)' in page, "charge not range-capped (unbounded -150 balloons each cluster)")
check('.strength(-150)' not in page, "REGRESSION: the unbounded -150 charge is back")
check('DEF={x:150,y:80,z:780}' in page, "home camera not pulled back for the widened (SEP 1.55) scene")

# ── 10k. batch-10: freeze-through-settle · ROUTES tab · icon LINES + curve amount · per-kind BEAM ──
check('function __uniFreezeForSettle' in page and 'window.__uniSettleDone' in page, "freeze/resume machinery missing")
check('updateClusters(true); if(window.__uniSettleDone) window.__uniSettleDone();' in page,
      "the engine settle does not resume what the layout freeze paused")
check('grp==="coreByBE"||grp==="coreByFE"){ __uniFreezeForSettle();' in page and 'grp==="entLayout"){ __uniFreezeForSettle();' in page,
      "layout/core changes do not freeze animations before the reheat")
check('grp==="coreBy"){ assignSub' not in page and 'grp==="entLayout"){ recomputeEX' not in page,
      "REGRESSION: a layout/core branch reheats without freezing")
check('"Connections"' in page and '"Transports"' in page, "the Connections/Transports fleet panes are missing (ex-Routes tab)")
check('M4 19 20 5' in page and 'M4 19 C 8 5 16 5 20 12' in page, "the LINES pill icons (straight/curved SVG) are missing")
check('{v:"straight",t:"Straight"}' not in page, "REGRESSION: the LINES pill is back to text labels")
check('id="curveAmtRng"' in page and '*(window.__uniCurveAmt||1)' in page,
      "curve-amount slider missing or __uniCurve ignores it")
check('window.__uniBeam={ fk:0.9' in page and 'if(!_bm && !sel) return;' in page and 'cfg.trust*_bm' in page,
      "per-kind beam missing (declare + skip-at-0 + opacity multiply)")
check('wireRow("fk")+wireRow("bridge")+wireRow("calls")+wireRow("imports")' in page,
      "the four per-kind wire rows (sample · color · shape · beam) are not built")
# batch 11-A: wire styling — ONE shared style map, CONN-derived samples + legend (a sample must never lie)
check('var DASHMAP={ solid:' in page, "the shared style→dasharray map is missing")
check('data-wcol=' in page and 'data-wshape=' in page and 'data-wreset=' in page,
      "per-kind color / shape / reset controls missing")
check('{t:"ln",k:"fk"' in page and '{t:"ln",k:"bridge"' in page,
      "legend Connectors rows do not reference CONN kinds (frozen literals would lie after an edit)")
check('{t:"ln",c:0x5893ad' not in page, "REGRESSION: legend Connectors back to hardcoded literals")
check('case "ln": var lw=it.k?(CONN[it.k]||CONN[' in page, "legend ln sample not derived from CONN at render time (a REL row falls to its connector KIND's style)")
check("'[data-itog=\"transports\"]'" in page, "the transports toggle is not DOM-moved into the Routes pane")
# review r2 (mutation-proven interleaves, all headless-verified):
check('mo.onclick=function(){ window.__uniSettleCancel();' in page,
      "motionBtn does not cancel the pending settle auto-resume (a pause DURING the settle gets stomped)")
check('if(window.__uniDragging) return;' in page and '__uniDragging=true;' in page,
      "the settle resume does not defer while a camera drag is held")
check('if(window.__uniSettleDone) window.__uniSettleDone(); }' in page and 'function _endDrag' in page,
      "the shared _endDrag release must fire the settle resume deferred mid-drag")
check(page.count('if(window.__uniAddLayoutTab) __uniAddLayoutTab()') == 3,
      "not all 3 buildCfg call sites re-tab (boot + URL-preset + ?drive) — a preset URL would drop the Routes tab")

# ── 10l. batch 11-B: FLEET panel — UNIVIS contract + six engine seams, all read through visEnt/visN ──
check('window.UNIVIS={ ent:{}, sub:{}, node:{}, meta:{} }' in page, "UNIVIS 4-namespace contract missing (sub = cluster overrides; node/meta = the in-flight seam)")
# batch 11-B3: CLUSTER rows — expand on the entity name, counter, per-cluster switches (distinct color)
check('(ev.show&&sv.show)?1:0' in page, "visN does not AND-combine entity and cluster flags")
check('data-fsub=' in page and 'flstog' in page and 'flcnt' in page and 'data-flx=' in page,
      "cluster rows / counter / expandable entity name missing")
check('window.__uniFleetRegroup=function' in page and 'updateClusters(true); if(window.__uniFleetRegroup) __uniFleetRegroup(); }' in page,
      "a core change does not regroup the panel (stale cluster overrides would linger)")
check('cluster hidden by the fleet panel' in page, "sub-hull seam misses the cluster-level skip")
check('sub-aware' in page, "transports do not resolve visibility at NODE level (cluster routes-off would leak)")
check('.fltog.flstog.on{ background:#0b7a63' in page,
      "cluster switches wear the entity color — the two levels must read differently")
# fleet backend/frontend split (operator ask): two group masters, each iterating its own subset;
# the split predicate reads the REGISTRY (FE_HOME) then the KEY prefix — never a rendered label (naming pass 2026-09-06: a label
# convention other than "fe · " must not re-group the frontend); the old label regex is the mutant
_fp=page[page.find('window.__uniIsFeEnt=function(e){'):page.find('window.__uniIsFeEnt=function(e){')+260]
check('FE_HOME[e]) || /^fe·/.test(String(e||""))' in _fp and '__uniEntLabel' not in _fp and '/^fe · /' not in _fp,
      "the frontend predicate (__uniIsFeEnt) must read FE_HOME ∪ the fe· KEY prefix, never the display label")
check('(r&&r.name)?(l+" · "+_hslug(e)):l' in page and '!/^fe·/.test(e))?(r.name' not in page,
      "modelRow's nm() must read a twin's name through the label funnel (fe·d: ids are indexed) instead of refusing fe· ids")
check('_masterRow("backend", "*backend"' in page and '_masterRow("frontend", "*frontend"' in page,
      "the fleet lost its two group masters (backend + frontend)")
check('var beEnts=_ents.filter(function(e){ return !__uniIsFeEnt(e); });' in page
      and 'var feEnts=_ents.filter(function(e){ return __uniIsFeEnt(e); });' in page,
      "the fleet render does not split entities into backend + frontend groups")
check('group master = its own subset' in page,
      "a group master must propagate ONLY into its own group's entities (backend/frontend subset)")
check('#fleet .flmaster.flgroup2{' in page, "the frontend section break (flgroup2) styling is gone")
# backend-function community pass (operator fix): functions cluster over the call graph (ƒ·<hub>),
# functions JOIN the data cluster they serve (operator ruling — seed from the handler endpoint, propagate over the call graph)
check('function _fnAssignSub(mode){' in page and 'l.rel==="handler" && s.kind==="endpoint" && t.kind==="function"' in page and 'cur[t.id]=s.sub;' in page,
      "the backend-function pass no longer seeds from the handler endpoint's data cluster")
check('try{ _fnAssignSub(mode); }catch(e){}   // functions JOIN their served data cluster' in page,
      "the fn pass is not wired into the data cores (community/use-case/fk)")
# the ENTITY column is a MASTER over its clusters for EVERY column except subs (operator): off→all off · on→all on
check('the entity column is a MASTER over its clusters for EVERY column except' in page and 'function _entSubKeys(ent)' in page,
      "the entity column master (entity toggle propagates to clusters for all cols but subs) is gone")
check('a cluster turned ON re-enables its entity' in page,
      "a cluster turned on no longer re-enables its entity")
# aesthetic (operator): selected-option name after a section title · no left border · legend tabs IN the header
check('__uniSyncGrpSel=function' in page and 'className="grpsel"' in page,
      "the selected-option name after a section title (grpsel) is gone")
check('.grplbl .grpsel{' in page and '#cfg .grp.cgside, #flside .grp.cgside{ padding-left:0;' in page,
      "the backend/frontend left border was not removed (title-only sections)")
check('<div class="lghd"><b>\'+(typeof ico==="function"?ico("shape",13):"")+\'Legend</b><button class="lgref"' in page and '</button><div class="lgtabs">' in page,
      "the legend tabs are not in the header, or the ⓘ is not inline between the title and the tabs")
check('var LGTABICO={' in page and '(LGTABICO[t]||t)' in page,
      "the legend tabs lost their icons (Types/Connectors/Planet should be icon-only)")
check('#elegend .lgtab{ display:inline-flex' in page and 'border:1px solid var(--line)' in page
      and '#elegend .lgtab.on{ color:#fff; background:var(--accent)' in page,
      "the legend tab buttons do not match the fleet header button style (bordered, accent-on)")
# the assemble line-map guard (fragility catch — a spike-base line shift must fail loud, not ship broken JS)
_asm = open('docs/design/codebase-graph-consolidation/universe-build/assemble.py').read()
check('_ANCHORS = {' in _asm and 'line-map STALE at' in _asm,
      "the assemble.py line-map anchor guard is gone (a spike-base line shift would silently ship broken JS)")
check('rz.className="flresize"' in page and 'MINW=230, MAXW=520' in page and 'p.style.width=w+"px"' in page,
      "the fleet width-resize handle (drag + double-click restore) is gone")
check('#fleet .flent{ flex:1 1 88px' in page,
      "the fleet label column does not absorb width (cluster titles stay cramped)")
check('reads inherited-off (dim)' in page, "a cluster switch does not dim when its parent entity is off")
check('layer:"Layer — the kind' in page and 'ti:"Chain — a flat layered ribbon' in page,
      "cluster-core / entity-layout options carry no hover explainers (word — meaning, since the icon-only pills)")
check('fnsTog' not in page and 'the Functions boolean is GONE' in page,
      "the Functions boolean must be removed (operator: the legend Function row governs load)")
check('k==="function" && window.toggleFns' in page and 'window.__uniSetKindState=function' in page,
      "the legend Function row no longer loads/unloads functions (via __uniSetKindState)")
check('window.__uniKindState={}' in page and 'window.__uniGroupToggle=function' in page and 'n.__solo=(ks.length===1 && cs[ks[0]]===n.kind && n.d2w==null' in page,
      "the 3-state legend (all/critical/off) + solo detection + group master are gone")
check('!(n.access&&n.access.ops&&n.access.ops.length)' in page,
      "the WRITE-FABRIC solo exemption (d2w/access fns never fold at critical) is gone")
check('var _HUB_FANIN=15' in page and 'n.role==="gate" && ks.length>=_HUB_FANIN' in page,
      "B2 HUB FOLD (a high-fan-in gate like require_household folds under critical, no 50-spoke star) is gone")
# ── journeys batch (operator 2026-08-27): backend chains · curated workflows · step note · chip rows · middle-click solo
check('function _bkCollect(){' in page and 'function _wfCollect(bk){' in page and '[["wf","workflows"],["commit","commits"],["bk","backend"]' in page,
      "the derived BACKEND journeys + curated WORKFLOWS journey kinds are gone from the picker (+ the commits kind)")
# wave D (P7): the backend-journey walk WALKS depends (Hop-0.5 gate) + dispatches (event-bus leg), not just draws them
check('(dep[l.source]=dep[l.source]||[]).push' in page and '(disp[l.source]=disp[l.source]||[]).push' in page
      and 'gsteps.push({id:g, hop:0.5, why:"gate", from:h})' in page and 'q.push([t,hop+1,"dispatch",fid])' in page,
      "wave D: the backend walk no longer traverses depends (Hop-0.5 gate) + dispatches (event-bus leg)")
check('meta.why==="gate"' in page and 'meta.why==="dispatch"' in page and '#stepnote .sng' in page and '#stepnote .snd' in page,
      "wave D: the step note no longer renders the gate + dispatch why (with their CSS)")
# DISCLOSURE TIERS (control-driven, no click-to-expand): T0–T3 header selector + presets + feClass gate
check('id="tiersel"' in page and 'data-tier="0"' in page and 'data-tier="3"' in page and 'window.__uniSetTier=function' in page,
      "the disclosure-tier selector (T0–T3, Alt+1–4) + __uniSetTier are gone")
# tiers moved to Alt+1–4 (plain 1–8 own the fleet columns on their own keydown; plain 1–4 fired BOTH → same tier rendered differently each press). The tier keydown REQUIRES altKey and reads e.code Digit1–4 (macOS Option-compose safe); the fleet keydown still guards !e.altKey so Alt+digit can't reach it.
check('/^Digit[1-4]$/.test(e.code' in page and 'e.altKey && !e.metaKey && !e.ctrlKey && /^Digit[1-4]$/' in page and '__uniSetTier(+e.code.slice(5)-1)' in page,
      "the tier keydown no longer requires Alt / no longer reads e.code (plain 1–4 would collide with the fleet-column keys again)")
check('k>="1"&&k<="8"&&!e.altKey' in page,
      "the fleet-column keydown dropped its !e.altKey guard (Alt+digit would toggle a fleet column AND set a tier)")
check('window.__uniFeClassState' in page and 'window.__uniFeClassState[n.feClass]===false' in page and '_TIER_PRESETS=[' in page,
      "the feClass visibility gate + the tier presets are gone")
check('window.__uniJrnSolo=function(e)' in page and 'c.onauxclick=function(ev){ if(ev.button!==1) return;' in page,
      "middle-click SOLO on the journey entity chips is gone")
check('id="stepnote"' in page and 'function _stepNote(){' in page and '#stepnote .snhop' in page,
      "the STEP NOTE (derived per-step guidance) is gone")
check('#stepnote{ position:fixed; left:50%; transform:translateX(-50%); bottom:46px;' in page,
      "the step note sits BOTTOM-centre (operator: moved off the top, same horizontal centre)")
check('window.__uniDrawJourneyNums=function' in page and 'if(window.__uniDrawJourneyNums) __uniDrawJourneyNums();' in page and 'function _numBadgeSprite' in page,
      "journey STEP-NUMBER badges (operator): the pass exists + is hooked (updateConnectors + walk render) — a sequence number overlaid on each step node during a walk")
check('window.__uniJn = window.__uniJn || { size:5, line:4.5, disc:0.6, font:0, off:-9 };' in page and 'id="jnSize"' not in page and 'id="jncopy"' not in page,
      "the step-number badge uses the operator-tuned DEFAULT config; the live tuner was removed once settled")
check('width:min(720px, calc(100vw - 16px))' in page and 'font:14px/1.5 var(--font-ui)' in page and 'class="snmin"' in page and '#stepnote.min .snwhat, #stepnote.min .snhop, #stepnote.min .sndoc{ display:none; }' in page and 'window.__uniStepMin' in page,
      "the step note is ENLARGED (720px/14px) + a minimize button collapses it to the title row (operator)")
check('#walkbar .wnav{ display:flex; align-items:center; gap:5px; flex-wrap:wrap; }' in page and '#walkbar .wchip{ flex:0 0 20px;' in page,
      "walkbar chips no longer keep a fixed size and wrap into rows")
check('s.src="./workflows.js"; s.onerror=function(){};' in page and 'if(!window.__uniJrnKind) window.__uniJrnKind=(((window.GABE_WORKFLOWS||[]).length||(window.GABE_WORKFLOWS_DRAFT||[]).length)?"wf":"bk")' in page,
      "the optional curated workflows feed (runtime-loaded, onerror-ignored) or the lazy default tab is gone")
check('if(n.kind!=="function") cnt[n.ent]=(cnt[n.ent]||0)+1;' in page,
      "functions must NOT trip the capsule fold (review: loading them must not collapse their entity)")
check('chain = layered plane · force = coupling bubbles' not in page and 'joined from the levels feed by name' not in page,
      "REGRESSION: the note lines below the pills are back (explainers must live on hover)")
check('function visEnt' in page and 'function visN' in page, "vis accessors missing (seams must read through ONE pair)")
check('nodeVisibility(function(n){ return _nodeVisibleFn(n); })' in page, "node visibility seam not wired (fleet ∧ focus fn)")
check('if(!visEnt(e).show) return; var mem=' in page, "ent-hull seam missing (hidden entity keeps its hull)")
check('if(!visEnt(n.ent).show||!visEnt(n.ent).subs) return;' in page,
      "sub-hull seam wrong — must skip on !show OR !subs (ghost sub-hulls around a hidden entity)")
check('wires-off entity/cluster' in page, "connector seam missing (wires keep drawing to hidden / wires-off entities)")
check('routes-off entity' in page, "transport seam missing (ghost shuttles fly to hidden entities)")
check('function linkVisFn(l){ return !CFG.conns; }' not in page, "REGRESSION: linkVisFn back to conns-only (dormant seam dropped)")
check('if(all||s.nodes||s.zones){ try{ rebuildNodes' in page,
      "show/zone routing skips rebuildNodes — re-show duplicates FLEETTICK/PULSE/ORBIT/WAVE closures")
check('if(all||s.nodes||s.routes){ try{ buildTransports' in page,
      "show routing skips buildTransports — MOVERS rebuild nowhere else")
check('window.__uniBuildFleet) __uniBuildFleet()' in page and 'window.__uniApplyVisPreset=function' in page,
      "fleet panel not built at boot / preset entry point missing")
check('body.nav-min #fleet{ left:48px' in page, "fleet panel does not clear the nav-restore tab under nav-min")
check('.fleethid{' in page and 'fltog.mdim' in page, "card hidden-note CSS / masters-dim CSS missing")
# batch 11-B2: per-entity fleet-zone gates (global AND entity) + zones/routes columns
check('(CFG.zDef&&visN(n).zDef)? placeFleet(' in page and '(CFG.zAtk&&visN(n).zAtk)? placeFleet(' in page,
      "def/atk fleet gates are not per-entity")
check('(CFG.zCfl&&visN(n).zCfl)? cflSpec(' in page and 'CFG.zSat&&visN(n).zSat) for(var si=0;' in page,
      "cfl/sat gates are not per-entity")
check('var def=CFG.zDef? placeFleet(' not in page, "REGRESSION: a fleet-zone gate ignores the fleet panel")
check('k:"zDef"' in page and 'k:"routes"' in page and 'icon:"truck"' in page,
      "zones/routes matrix columns missing")
check('__uniAddLayoutTab(); if(window.__uniAddWireView) __uniAddWireView(); if(window.__uniAddFocusCfg) __uniAddFocusCfg(); if(window.__uniFleetSync) __uniFleetSync(); } })();' in page,
      "the URL-preset path rebuilds the config without re-syncing the fleet masters-dim")
# batch 11-C: the sim feed + presets row (the in-flight seam must exist before that batch, or it debugs a phantom)
check('<script src="./sim.data.js"></script>' in page,
      "sim.data.js not loaded — GABE_SIM undefined on EVERY deployment, the in-flight seam is dead")
check('data-fpre="all"' in page and 'data-fpre="none"' in page and 'data-fpre="inflight"' in page,
      "presets row (All/None/In-flight) missing")
check('no sim feed on this page' in page and 'no change in flight' in page,
      "the In-flight stub does not distinguish its two honest-empty states (undefined vs null)")

# ── 10n. batch 12: layer ruling (c) · depth highlight · journeys picker · topbar icons · chord pan ──
check('else n.sub=n.layer||"data"' in page, "layer core still collapses (ruling c: group by the kind's OWN layer)")
check('SUBOF[n.layer]' not in page and 'SUBOF[KINDS' not in page, "REGRESSION: the SUBOF collapse is back")
check('var SUBSHIFT={ endpoints:0.04' in page, "hull hue-shift map lacks the un-collapsed layer keys")
check('function _hlCompute' in page and 'window._hlLinkF' in page and 'function _nodeVisibleFn' in page,
      "depth-highlight machinery missing (BFS + wire factor + shared visibility fn)")
check('kind, R, hf, ea, eb, hov, sel, band)' in page and "var _whf=(window._hlLinkF?_hlLinkF(l):1);" in page and "8, _whf," in page,
      "connector wires ignore the highlight factor (or lost the gradient entity args / selected-wire boost)")
check('.nodeVisibility(function(n){ return _nodeVisibleFn(n); })' in page,
      "node visibility does not go through the shared fn (focus mode dead)")
check('var hlGroup=' in page and '__uniHLTick' in page and 'if(window.__uniHLTick) __uniHLTick();' in page,
      "halos are not an independent scene group with a per-tick follow (node rebuilds would kill them)")
check('requestAnimationFrame(__uniHLReapply)' not in page, "REGRESSION: halos back to riding node objects via a rAF reapply")
check('id="depthBtn"' in page and 'id="hlModeBtn"' in page and 'id="jrnBtn"' in page, "topbar depth/mode/journeys buttons missing")
check(page.find('id="reset"') < page.find('<div class="statuspills">'), "repo pills are not at the FAR right of the topbar")
check('❄ Freeze on drag' not in page, "REGRESSION: freeze button back to text (icons only, explanation on hover)")
check('e.altKey&&(k==="q"||k==="e"||kc==="KeyQ"||kc==="KeyE")' in page and 'key==="Escape"' in page,
      "Alt+Q/E depth / Esc clear not wired (Alt+scroll retired batch 38)")
check('WheelEvent' not in page or 'if(!e.altKey) return; e.preventDefault();' not in page,
      "the retired Alt+scroll depth wheel is back")
check('function _jrnCollect' in page and '__uniJrnToggle' in page, "journeys collector/picker missing")
check('window.__uniJrnExcl=window.__uniJrnExcl' in page and 'window.__uniJrnCollapse=window.__uniJrnCollapse' in page and 'function _jrnPaint' in page and 'function _jrnChipsHTML' in page and 'function _jrnTouch' in page and 'function _jrnGroupsHTML' in page and 'class="jrnkindtabs"' in page and 'data-jk="' in page and 'class="jrnent' in page and 'class="jrngrp jgcl' in page and 'j.ents.some(function(e){ return !window.__uniJrnExcl[e]' in page,
      "the journeys picker = ONE view: ALL-entity chips (span-based filter) + KIND TABS (e2e/by-entity/agg) + COLLAPSIBLE by-start-entity groups — operator")
check('width:min(520px, calc(100vw - 16px))' in page and '#jrn{ position:fixed' in page,
      "the #jrn picker must be theme-aware (var(--panel) bg, not a dark literal) + viewport-clamped width (no narrow-screen overflow) — review fixes")
check("drag.btn===1" in page and "*0.0011" in page, "MIDDLE pan (translate the rig, no rotation) missing")

# ── 10o. batch 13: journeys LEFT+grouped+NAMED · banner · the WALK (steps + trail) · panel footer ·
#         clusters-only + wires toggles · graph decoupled from the panel · chip-hover halo · gear sync ──
check('#jrn{ position:fixed; left:50%' in page, "journeys dropdown is not centered under the topbar middle")
check('function _caseNames' in page and '(aggregated)' in page and 'jrngrp' in page,
      "journeys are not named (det.cases join) / aggregates not labeled / groups missing")
check("j.e2e=!!j.corpora.e2e" in page, "end-to-end journeys are not detected across corpora (aggregate rows span e2e+web)")
check('id="jrnpill"' in page and 'function _walkRender' in page and 'var WALK={' in page,
      "journey step PILL / walk machinery missing")
check('id="jrnhud"' not in page, "REGRESSION: the topbar HUD is back (the step pill floats over the diagram)")
check(page.count('<div class="spacer"></div>') == 2 and page.find('id="jrnBtn"') < page.find('id="hlModeBtn"') < page.find('id="depthBtn"'),
      "topbar order wrong (journeys · style middle; depth/freeze/reset right)")
check('<span id="jrnpill"' in page and page.find('id="hlModeBtn"') < page.find('id="jrnpill"') < page.find('id="depthBtn"'),
      "the journey step controls are not centered in the header bar")
check('#jrnpill .wname{' in page and 'm15 18-6-6 6-6' in page and 'm9 18 6-6-6-6' in page,
      "step buttons are not proper Lucide chevrons (the text glyphs sat skewed)")
check('window.__uniFlyStep=function _flyTick(){' in page and 'setInterval(window.__uniFlyStep, 16)' in page
      and 'FK.up' in page and 'k==="control"' in page and 'window.__uniFlyStep(); }catch(_fe){}' in page,
      "WASD/Space/Ctrl flight missing (interval tick + IMMEDIATE first step + elapsed-time scaling — batch 48)")
check('id="depthRng"' in page and 'ArrowUp' in page and 'ArrowDown' in page,
      "depth is not a draggable 1–5 bar with arrow-key fallback")
check('?0:1' in page and 'return 2.6;' in page, "glow must brighten the set and leave the rest ALONE (dim belongs to focus only)")
check('?0:0.05' not in page and '?0:0.18' not in page, "REGRESSION: glow dims the rest of the graph again")
check('shuttles fly the lit path only' in page, "transports roam off the lit path during a highlight")
check('function _frameSet' in page, "journey select does not frame the whole carrier set (the camera dived into the wire jungle)")
check('body.panel-open .panel .pbody{ overflow-y:auto' in page, "the card body does not scroll — the footer chevron leaves the screen on tall cards")
check('.panel .minbar .pmin{ order:2; margin-top:auto; }' in page,
      "the collapsed rail's expand chevron is not at the BOTTOM (parity with the expanded footer)")
check('function _rigStart' in page and 'ev.button===2' in page and 'ev.button===1' in page,
      "the three-button map (LEFT scheme · RIGHT tumble · MIDDLE pan) is not wired in pointerdown")
check('ev.buttons!==0' in page and '(ev.buttons&_bit)===0' in page and 'function _endDrag' in page,
      "chord-safe release missing: the LAST pointerup must end the drag and the move stream must release on owner-bit loss (stranded-drag fix)")
check('data-wgo=' in page and 'wchip' in page and 'function _aimAt' in page,
      "walk stepping (journey ‹›/trail chips + camera aim) missing")
check('class="pfoot"><button class="pmin"' in page and "<button class='pmin' title='minimize'" not in page,
      "the panel collapse chevron is not footer-only (it collides with the walk bar at the top)")
check('planets:1, wires:1' in page and 'k:"planets"' in page and 'k:"wires"' in page,
      "planets/wires are not fleet MATRIX columns (per entity AND cluster, master row included)")
check('(!_nodeVisibleFn(_cs)||!visN(_cs).wires)' in page, "the connector seam ignores the per-entity/cluster wires flag")
check('#g{ right:0 !important; }' in page, "the graph still resizes with the right panel")
check('__uniHoverHL(x.id)' in page and 'userData.__hov' in page, "connection-chip hover halo missing")
check('if(hidden) c.classList.remove("min");' in page, "the nav gear does not un-minimize the config on show (state drift)")

# ── 10q. batch 17: community default · ring layout · wider spacing ──
# ── operator polish (2026-08-25): method badge · spinning focus ring · zone header toggle · trail focus ──
check('function methodBadge(' in page and 'grp.add(methodBadge(' in page and 'c.arc(64,64,58' in page and "key==='DELETE'" in page
      and 'window.__badgeGlyph=function' in page and "window.__badgeGlyph(c,'method',m)" in page,
      "the endpoint METHOD badge (coloured circle + method GLYPH, from the shared __badgeGlyph source) is gone")
# C1 · FUNCTION ROLE badge — accessor/caller/gate/pure, same slot/machinery as the method badge, one glyph source
check('function roleBadge(' in page and 'grp.add(roleBadge(n.role))' in page and "window.__badgeGlyph(c,'role',role)" in page
      and "key==='accessor'" in page and 'role:f.role' in page,
      "the FUNCTION role badge (roleBadge → shared glyph, wired on n.kind==='function' && n.role, role carried onto the fn node) is gone")
# badge-KEY popup — the legend info dot renders each badge with the SAME __badgeGlyph + its meaning (legend-visual law)
check('data-badgeinfo=' in page and 'window.__badgePop=function' in page and 'class="bpcv"' in page
      and 'window.__badgeGlyph(c, kind, cv.dataset.k)' in page and 'window.__BADGE_DESC=' in page,
      "the legend badge-key popup (endpoint methods · function roles, drawn with the real badge glyph) is gone")
# SCHEMA FOLD + COUNT badge (operator, 2026-08-27): nested-only schemas fold under critical; the parent wears the count
check('SCHEMA fold (operator, 2026-08-27)' in page and 'n.__foldN=0' in page and 'if(sn.kind==="function"||tn.kind==="function") return;' in page
      and 'window.__uniSyncCountBadges=function' in page,
      "the schema FOLD clause in __uniComputeSolo (nested-only → __solo, __foldN on the parent, fn wires never a contract) is gone")
check('function countBadge(' in page and "window.__badgeGlyph(c,'count',nn)" in page and 'grp.add(_cb); grp.__cnt=_cb;' in page
      and 'if(kind==="count")' in page and 'c.fillText(t, 64, 68)' in page,
      "the schema COUNT badge (countBadge → shared glyph with the digits, attached on n.kind==='schema' && n.__foldN>0) is gone")
check('(it.k==="schema")?"count"' in page and '(kind==="count")?["N"]' in page and 'count:{ "*":' in page,
      "the legend badge-key row for the fold count (same glyph fn, one sample row) is gone")
# BOOT method badge (implemented): a designed power glyph + a description + the key list entry (not the generic dot)
check("key==='BOOT'" in page and 'c.arc(64,72,28' in page,
      "the BOOT method badge draws its power glyph (regressed to the generic dot)")
check('DELETE","BOOT","TASK"]' in page and "key==='TASK'" in page and 'c.lineTo(78,92)' in page and 'BOOT:"boot — runs ONCE' in page and 'key==="BOOT"?"boot event' in page,
      "BOOT is missing from the method key list / description / popup header")
check('D.schema_edges' in page and 'rel:e.rel||"uses", schema:true' in page and 'LINKMETA.returns=' in page,
      "the fn→schema wires (levels schema_edges: returns/takes/uses) are not linked into the field")
check('det.homed?kv("link","home"' in page and '" folded"' in page,
      "the card's schema-homing provenance row / the '(N folded)' nests group label is gone")
# C4 follow-up · endpoint GUARDS — the middleware floor (Depends/decorators before the body) → the card, carried by the adapter
check('function guardsSec(' in page and 'guardsSec(n)' in page and 'middleware:p.middleware' in page
      and 'The gates/deps that run BEFORE the handler body' in page,
      "the endpoint GUARDS section (C4 middleware floor → card, adapter-carried) is gone")
# panel HEADER badge — dimmed to the graph's badge opacity (mbOp) + its meaning on an INSTANT styled
# popup (click/hover), not the native-title delay (operator)
check("class='pheadbadge'" in page and 'window.__badgeGlyph(_c,_bk.kind,_bk.key)' in page
      and '_cv.style.opacity=(typeof CFG' in page and '__badgePop(_hb,_bk.kind,_bk.key)' in page
      and 'window.__BADGE_DESC' in page,
      "the panel-header badge (dimmed to graph opacity + instant click/hover popup) is gone")
# connection TYPE on the link card + the two new kinds in the connectors legend (operator)
check('sechd("link","Connection")' in page and 'REL2KIND[l.rel]' in page and 'window.__CONNDESC' in page
      and 'rollup <i>endpoint' in page and 'access <i>function' in page,
      "the link-card Connection type (kind + wire sample + meaning) + rollup/access legend rows are gone")
# function ACCESSES — an accessor's evidence (which model it reads/writes, from n.access) in the fn card
check('function accessSec(' in page and 'accessSec(n)' in page and 'The DB tables this function reads/writes' in page,
      "the function ACCESSES section (accessor badge → which model it reads/writes) is gone")
# Option A · the DATA-ACCESS connectors — rollup (endpoint→model) + access (fn→model) as distinct kinds,
# and _buildFnData draws the fn→model access wire from n.access.ops (the TRUE accessor connection)
check("'rollup'" in page and "'access'" in page and "reads_from:'rollup'" in page and "fnreads:'access'" in page
      and "rel:(o.rw===\"w\"?\"fnwrites\":\"fnreads\"), access:true" in page,
      "the rollup/access connector kinds + the fn→model access wire (Option A) are gone")
# Option A · the connector CONFIG (color·pattern·density·transparency·thickness) for rollup+access,
# calibratable + copyable; thickness renders a TUBE (a flat line is 1px), the copy carries the new fields
# BAKED calibration (operator JSON): rollup HIDDEN (beam 0), access RED (#e5484d = THE WRITE) glow 0.7,
# calls flat #817536 grad OFF; the access fine-tuning controls (den/α/thickness) stay
check("access:{color:0xe5484d" in page and 'rollup:0, access:0.7' in page
      and 'calls:{color:0x817536' in page and "grad:false,thick:1,gmode:'type'" in page
      and 'var wireRow2=function' in page and 'wireRow2("access")' in page,
      "the baked calls/access defaults or the access fine controls drifted")
# gmode GRADIENT LOGIC (baked; the selector was REMOVED per operator): per-end type-badge colour
# (endpoint METHOD / function ROLE) driven by CONN.gmode; calls gmode='type', access 'type-ent'
check("gmode:'type'" in page and "gmode:'type-ent'" in page and '__BADGE_COL.role[n.role]' in page
      and 'METHOD[n.m.method]' in page and '_gm==="type"' in page and 'data-wgmode' not in page,
      "the gmode gradient LOGIC drifted, or the removed mode-selector came back")
# connectors legend rows CLICK-TO-TOGGLE their wire (show/hide), like the node-kind toggles
check('data-lgconn="' in page and 'it.t==="ln"&&it.k' in page and 'k:"rollup"' in page and 'k:"access"' in page,
      "the connectors-legend show/hide toggle (+ rollup/access rows) is gone")
check('if(cfg.thick&&cfg.thick>1.05){' in page and 'new T.TubeGeometry(_tc' in page
      and 'density:(c.density!=null?c.density:null), trust:(c.trust!=null?c.trust:null), thick:(c.thick!=null?c.thick:null)' in page,
      "the thickness TUBE render + the copy carrying density/trust/thick are gone")
# badge LEAK fix — _mbTick prunes badges whose node group force-graph detached (grp.parent nulled on
# rebuild). `!b.parent` alone missed them (they kept b.parent=grp), so __uniBadges grew ~263/toggle;
# `!b.parent.parent` drops the detached ones while KEEPING live cached-node badges (no flicker).
check('if(!b||!b.parent||!b.parent.parent) continue; arr[live++]=b;' in page,
      "the _mbTick badge prune must drop grp-detached badges (!b.parent.parent) — the leak fix is gone")
check('window.__uniBadges.length=0; if(Graph) Graph.nodeThreeObject' not in page,
      "rebuildNodes must NOT wholesale-clear __uniBadges (that detacheded live cached-node badges)")
check('if(!was && sv[col] && UNIVIS.ent[ent] && !UNIVIS.ent[ent][col]) UNIVIS.ent[ent][col]=1;' in page,
      "a cluster toggle no longer re-enables its entity for THAT column (must match the entity-column behaviour)")
check('id="mbOpRng"' in page and 'BADGE OPACITY (operator)' in page and 'if(CFG.mbOp==null) CFG.mbOp=0.95;' in page and 'id="badgecfg"' not in page,
      "the GLOBAL badge-opacity slider must live in the Planets pane (not #cfg); the #cfg badge panel must be gone")
check("Temporary Config</span>" in page, "the top-right config panel must be renamed 'Temporary Config'")
check('window.__uniAddFocusCfg=function(){ window.__uniHLSeed()' in page and 'window.__uniHLDefaults={' in page and 'id="focuscfg"' not in page and 'focrng' not in page and 'srow("speed","focSpeed"' not in page,
      "the focus/highlight CONFIG PANEL must be retired to a seeder (no #focuscfg, no sliders/pills)")
check('grpWith("Highlight")' in page and '_hlBtn("focRing"' in page and '_hlBtn("focGlow"' in page and '_hlBtn("othGlow"' in page and '_hlBtn("othRing"' in page and 'entPane.push(hlGrp)' in page,
      "the four highlight toggles (focus ring/glow · others glow/ring) must live in the entity pane")
check('focGlowFall:0.4' in page and 'focGlowFall!=null?CFG.focGlowFall:0' in page,
      "focus-glow falloff must survive as a fixed default (0.4) + engine read")
check('dashN=(pat==="dashed")?Math.max(10, Math.round(sz*0.8))' in page and 'Math.round(sz/16)*128' in page and '_ringTex(typeof CFG!=="undefined"?CFG.focPat:null, thick, sz)' in page,
      "the dashed ring must scale its resolution + dash COUNT with the sphere size (big spheres pixelated)")
check('if(CFG.othRing && n.ent!=null && _selEnts[n.ent] && !(WALK.mode==="journey" && HL.exact)) _add(n, _ringSprite(n, (CFG.othRingInt!=null?CFG.othRingInt:0.35)), false);' in page and 'var _selEnts={};' in page,
      "the non-selected dim ring must be STATIC and confined to the selected element's entity (outer entities glow-only)")
check('if(!d0 && !_nodeVisibleFn(n)) return;' in page,
      "the highlight neighborhood glow must NOT draw on HIDDEN nodes (colored-halo noise vs the clickable ghost stars, operator)")
# fleet ASSETS = live 3D thumbnails inline on the sections (operator: the ACTUAL graph asset, not a text summary)
check('window.__uniAssetThumb=function' in page and 'window.__uniCardPrune=function' in page and 'window.__uniCardCells.push(entry)' in page and 'window.__uniAssets={' in page,
      "the card asset-thumbnail machinery (shared palR renderer, pruned card cells) must be present")
check('_hdAsset(jhd, function(){ return window.__uniAssets.testchip(); }' in page and 'window.__uniAssets.cargo()' in page and 'window.__uniAssets.ship(_corp)' in page and 'window.__uniAssets.sat()' in page,
      "the live asset thumbnails must attach to Usage(sat)/Tests(ship)/Journeys(test-chip)/Payload(cargo)")
check(page.count('if(window.__uniCardPrune) __uniCardPrune();') >= 6 and 'var _as=assetsSec(n)' not in page,
      "the card-thumbnail prune must run on EVERY panel rebuild (showPanel/showLinkPanel/panelAll/panelEnt/panelClu/closePanel) — no WebGL leak on nav-up or close (review)")
check('if(typeof SHIPSREADY!=="undefined" && !SHIPSREADY) return cv;' in page,
      "an asset thumbnail must skip until SHIPSREADY (else a stale loadingBox that never refreshes, review)")
check('function flagsSec(n)' in page and 'window.__uniAssets.god()' in page and 'window.__uniAssets.ung()' in page and 'unguarded · no test covers this' in page,
      "the risk flags (god-object / unguarded / conflict) must render with their raider asset (operator screenshot 2)")
check('if(real && window.__uniJrnStart){ row.style.cursor="pointer"; row.onclick=function(){ try{ __uniJrnStart(j.cid)' in page and 'an AGGREGATE of web/e2e cases folded' in page,
      "a named journey row must click → __uniJrnStart (top stepper); aggregate 'N case(s)' rows non-clickable + explained")
# panel/fleet/legend polish batch (operator)
check('getBoundingSphere(new T.Sphere()).radius' in page,
      "asset thumbnails must FRAME-FIT — fill the square regardless of native asset size (the sat was tiny)")
check('.sechd .cnt{ margin-left:0 !important; }' in page and 'height:384px !important' in page and 'width:344px' in page,
      "section counter LEFT-aligned next to its title · legend sized to the Types tab (384, no scroll) · fleet wider (344)")
check('<b class="flcnt flexp" style="--flc:' in page and '#fleet .flrow:not(.flsub):not(.flmaster) .fldot{ display:none; }' in page,
      "the fleet entity counter merges the dot + count into ONE entity-colored counter (no separate dot)")
check('sechd("truck","Cargo")' in page and 'window.__uniAssets.cargo()' in page and 'sechd("test","Test chip")' in page and 'window.__uniAssets.testchip()' in page,
      "the wire card must have SEPARATE Cargo + Test-chip sections, each with its 3D asset thumbnail (operator)")
check('class:"flagrow ok"' in page and 'no cargo ' in page and 'no test chip ' in page and 'same-entity wire (no transit)' in page,
      "each wire section must carry a present/absent FLAG (cross-entity → present; same-entity → no transit)")
check('window.__uniHovLink===l||window.__uniSelLink===l' in page and 'CFG.selThick!=null)?CFG.selThick:0.2' in page and 'CFG.selPattern)?CFG.selPattern:"solid"' in page,
      "a SELECTED (or hovered) wire must render as a WHITE tube whose opacity/thickness/pattern read from CFG (operator)")
check('CFG.selOpacity=0.5' in page and 'CFG.selThick=0.2' in page and 'CFG.selAnim="pulse"' in page and 'CFG.selAnimSpeed=0.3' in page and 'CFG.selGlow=true' in page and 'CFG.selGlowInt=0.05' in page,
      "the SELECTED-LINE look is SETTLED as the connection default (opacity .5 · thick .2 · pulse · speed .3 · glow-on @.05) — baked as a seeder, panel retired")
check('sg.id="selline"' not in page and 'class="slcopy"' not in page and 'class="pill selpill"' not in page and '_pill("motion","selAnim"' not in page,
      "the SELECTED LINE config PANEL must be retired from the Temporary Config (no #selline, no sliders/pills/copy) — operator")
check('window.__uniSelMeshes=[]' in page and 'CFG.selGlow){ var _gm=' in page and '_sr*2.6' in page and 'window.__uniSelCurve=_crv' in page and 'function _selAnim()' in page and '_selPhase=(_selPhase + 0.05*spd)' in page,
      "the selected wire must track its meshes+curve, build a wider GLOW tube on selGlow, and animate via a bounded-phase _selAnim rAF (pulse opacity · flow marching dots) — operator")
check('if(col!=="subs"){ var eon=UNIVIS.ent[ent][col];' in page and '_entSubKeys(ent).forEach(function(k){ (UNIVIS.sub[k]||(UNIVIS.sub[k]=Object.assign({},UNIVIS.ent[ent]||_VISDEF)))[col]=eon?1:0; })' in page,
      "the fleet ENTITY column button must cascade to ALL its clusters for EVERY column except subs — no partial dimmed state (operator)")
# panel polish: journeys legend → tooltip; hidden-node hover halo; panel-chip click reveals
check('var body=E("div",{class:"jsec"});' in page and 'A stop · reached by a test that spans other entities.' in page and 'class="jsub"' not in page,
      "the journeys entry/stop legend must live in the info TOOLTIP, not an inline .jsub line")
check('_hovSprite.position.set(_hp.x,_hp.y,_hp.z); try{ Graph.scene().add(_hovSprite)' in page,
      "hovering a HIDDEN node must place the white halo in the scene at its ghost position (invisible __threeObj would swallow it)")
check('if(_n0 && window.__uniReveal && typeof _nodeVisibleFn==="function" && !_nodeVisibleFn(_n0)){ try{ __uniReveal(id)' in page,
      "a panel chip whose target is FLEET-hidden must REVEAL it first (ghost-click parity)")
check('var rest=cs.slice(DCAP)' in page and '"see less"' in page and 'evidence matrix (beyond the loaded set)' in page,
      "the Tests section must EXPAND: first 6 shown, the rest fold behind +N more ⇄ see less (operator)")
check('pulseMode:"const"' in page and 'pulseAmp:0.08' in page and 'CFG.pulseMode==="const"' in page and 'bs+amp*18*s2' in page and 'srow("p.amp"' not in page,
      "the pulse must be a fixed const default (amp 0.08) + engine, slider retired")
check('function _ringTex(' in page and 'function _ringSprite(' in page and 'function _glowFor(' in page and 'CFG.focAnim' in page,
      "the configurable focus-ring engine (pattern texture · size mode · animation · non-selected marker) is gone")
# connection GHOSTS (operator: hidden connected nodes shown as faint stars AT their own position, no lines)
check('window.__uniDrawStubs=function' in page and 'if(window.__uniDrawStubs) __uniDrawStubs(connGroup)' in page and 'var _fleetShown=function' in page and 'var _kindShown=function' in page and '!_fleetShown(t) && _kindShown(t)' in page and 'glowSprite(col, 22, 0.45)' in page and '!ch.isSprite' in page,
      "connection GHOSTS: one faint star per hidden connected node, gated fleet-hide-not-kind, shared-sprite-geometry never disposed")
check('window.__uniReveal=function' in page and 'if(gbest && window.__uniReveal){ var _gid=gbest.st.hid; __uniReveal(_gid)' in page and 'cols.forEach(function(c){ UNIVIS.ent[ent][c]=1; })' in page,
      "clicking a ghost star (PRIORITY over the hull pick) must REVEAL the hidden target in place (force-on entity+cluster)")
check(page.count('rc.ray.distanceToPoint(P); if(d<22') == 2,
      "the ghost pick/hover threshold must be forgiving (22, matches the glow's world footprint) so an edge-click on the star still reveals — operator: same-entity ghost clicks missed at 13")
_gi = page.find('if(window.__uniStubs && window.__uniStubs.length){ var gbest=null;')
_ci = page.find('(typeof CLUSTERS!=="undefined"?CLUSTERS:[]).forEach')
check(_gi != -1 and _ci != -1 and _gi < _ci,
      "the ghost-pick must run BEFORE the cluster/hull pick — the small star wins, the big entity hull never preempts it (operator)")
check('window.__uniStubHoverInit=function' in page and 'unistubtip' in page and 'click to reveal' in page and 'svgInline(hn.kind' in page and 'rc.ray.distanceToPoint' in page,
      "hovering a ghost star must show its ICON + name (unistubtip, point-picked)")
# ghost click = SELECT (panel + trail); fleet master cascades to clusters; Alt+A/D trail nav
check('SEL={kind:"node",data:_gn}' in page and 'if(window.__uniHLSelect) __uniHLSelect(_gn)' in page and 'if(_gn.kind==="capsule"){ if(window.__uniCapExpand)' in page,
      "clicking a ghost must SELECT the node (panel + trail); a capsule ghost EXPANDS instead (onNodeClick parity)")
check('_entSubKeys(e).forEach(function(k){ (UNIVIS.sub[k]||(UNIVIS.sub[k]=Object.assign({},UNIVIS.ent[e]||_VISDEF)))[col]=on?1:0; })' in page,
      "the fleet group master must cascade to EVERY cluster, seeding a fresh sub FROM the entity (keeps zones), not zone-off _VISDEF")
check('else if(e.altKey&&(k==="a"||k==="d"||kc==="KeyA"||kc==="KeyD")){' in page and '_walkGo((k==="d"||kc==="KeyD")?1:-1)' in page and 'trail prev / next' in page,
      "Alt+A/D must step the trail (prev/next, e.code fallback for macOS) + appear in the controls cheat-sheet")
check('WALK.mode==="trail" && HL.on){ HL.origin=[n.id]' in page,
      "the focus ring does not transport to the selected TRAIL step")
check('the Zones config section is GONE' in page and 'grplbl zoneshd' not in page,
      "the Zones config section must be removed from the Planets pane (zones are fleet-only now)")
check('window.__uniBadges=[]' in page and 'function _mbTick()' in page and 'e[0]*_sx+e[4]*_sy+e[8]*3' in page and '(b.__slot||0)*(sz*0.72)' in page and 'window.__uniBadges.push(s)' in page,
      "the method badge is not ICON-relative (must ride the camera right/up basis, pinned to the component icon, never the sphere)")
check('new T.Vector3(0,1,0).applyQuaternion(cam.quaternion)' in page and 'if(FK.up) off.add(_upv); if(FK.dn) off.sub(_upv);' in page,
      "Space/Ctrl up-down is not camera-relative (must move along the camera up axis like WASD, not world-Y)")
check('function _ringSprite(' in page and 'HL.rings.push(' in page and 'material.rotation=_hlPhase' in page and '_hlPhase + 0.05*spd' in page and 'br*rad*fall' in page,
      "the configurable focus ring is gone (replaces the glow on the selected element)")
check('flztog' in page and '__uniFleetToggle(hs.ent||"*"' in page,
      "the ZONE column headers are not click-to-toggle (bulk zone show from the fleet)")
check('n.ent&&EX[n.ent]!=null?{x:EX[n.ent]' in page,
      "trail focus lost its entity-anchor fallback (an unpositioned step must still fly the camera)")
check('CFG.coreByBE=lv?"usecase":"kind"' in page and 'CFG.coreByFE="screen"' in page,
      "the per-side defaults (backend=community, frontend=screen) are gone")
check('{v:"ring",t:""' in page and 'Ring —' in page and 'mode==="ring"' in page,
      "the RING entity layout is missing (icon-only pill, word on hover)")
check('{v:"spread"' not in page and 'mode==="spread"' not in page, "REGRESSION: the useless spread layout is back")
check('SEP=(mode==="ring")?1.0:1.85' in page, "force-layout anchors are not widened (operator: entities too close)")
check('RENT[e]*0.78' in page, "sub-cluster rings are not widened (operator: clusters too close inside entities)")

# ── 10r. batch 18: focus rest behaviors · controls panel · Q/E yaw · invert mouse · middle=selection ──
check('rest:"hide"' in page and 'pillHTML("focusRest"' in page and page.count('{v:"dim",t:""')==1 and page.count('{v:"hide",t:""')==1
      and '{v:"fade"' not in page and '{v:"wires"' not in page,
      "FOCUS rest must offer DIM + HIDE only, as icon pills (hide default)")
check('HL.rest==="hide"' in page, "only the HIDE behavior may remove planets (dim/fade/wires keep them)")
check('id="ctrlp"' in page and '__uniBuildCtrl' in page and 'class="kbd"' in page,
      "the bottom-right CONTROLS panel is missing")
check('id="ctlInv"' not in page and 'id="ctlPvt"' not in page and 'UNICTL={ invert:false, selPivot:true' in page,
      "the invert / orbit-selection toggles are RETIRED (batch 50) — their behaviors ride the defaults")
check('__uniApplyMouseMap' not in page, "REGRESSION: invert swaps the mouse buttons again (it must flip ONLY the vertical axis)")
check('UNICTL.invert?1:-1' in page, "flight-style vertical inversion missing from the drag's polar term")
check('function _zoomDist' in page and 'addScaledVector(vdir, zd)' in page,
      "the drag pivot ignores the current zoom (the giant-sphere depth)")
check('_flyFreeze' in page and '_flyThaw' in page and '{passive:true});' in page,
      "camera controls (keys + wheel) do not freeze the decorations")
check('k==="q"' in page and 'ya*0.022' in page and '_rotRig(cam, ctrls.target, pv,' in page,
      "Q/E must orbit INWARD around the view centre at the zoom depth")
check('var ya=(FK.e?1:0)-(FK.q?1:0);' in page,
      "Q/E spin directions must stay SWAPPED (operator ruling: E spins Q's old way)")
check('drag.btn=1' in page and 'UNICTL.selPivot' in page and 'drag.btn=2' in page,
      "button remap incomplete: middle must own pan (btn=1) and right must own tumble (btn=2, orbit-selection lives there)")

# ── 10s. batch 20: the CAMERA-MODE dropdown — tumble (stock) · joystick (WoW anchor-velocity) · arcball · look ──
check('camMode:"look"' in page and 'id="ctlCam"' not in page and 'look — turn in place' in page,
      "LMB is FIXED to LOOK (batch 50) — the dropdown is retired, the engine default stays look")
for v in ('(drag.btn===2)?"tumble":(UNICTL.camMode||"look")','!=="joystick"','"arcball"'):
    check(v in page, "the camera-scheme ENGINE lost a mode (UI retired, engine kept): "+v)
check('ax:cx, ay:cy' in page and 'drag.cx-drag.ax' in page,
      "joystick anchor (ax/ay) or its offset velocity is gone")
check('JOYSTICK tick' in page and '(UNICTL.camMode||"look")!=="joystick"' in page,
      "the joystick per-frame velocity tick is gone (offset must KEEP turning while held)")
check('if(Math.abs(ox)<8) ox=0' in page, "the joystick deadzone (8px around the anchor) is gone")
check('crossVectors(v1, v0)' in page and 'z=d2<1?Math.sqrt(1-d2):0' in page,
      "the arcball virtual-trackball mapping is gone")
check('mode==="look"' in page and 'var eye=cam.position.clone()' in page,
      "look mode must rotate about the CAMERA (turn in place)")
check('(drag.btn===2)?"tumble"' in page, "the RIGHT button must always tumble regardless of the chosen LEFT scheme")
check('vs*dy*0.66' in page and '-vs*dy*0.66' not in page,
      "LOOK must start vertically INVERTED (aviation convention) — the old sign is back")

# ── 10t. batch 22: the PANEL HIERARCHY — Everything → Entity → Cluster → Element, two-way nav ──
for lit in ('window.__uniPanelAll=panelAll','window.__uniPanelEnt=panelEnt','window.__uniPanelClu=panelClu'):
    check(lit in page, "panel-hierarchy builder missing: "+lit)
check('class="pnav"' in page or "class:\"pnav\"" in page or '{class:"pnav"}' in page,
      "clickable panel nav rows (.pnav) are gone")
check('if(e.key==="Escape"){ __uniHLClear();' in page and 'if(window.__uniPanelAll) __uniPanelAll(); }' in page,
      "Esc must clear the selection AND land on the Everything panel")
check('setTimeout(function(){ if(window.__uniPanelAll) __uniPanelAll(); }, 0);' in page,
      "boot must open the Everything panel (deferred one tick past the card IIFE)")
check('Graph.onBackgroundClick(window.__uniBgClick)' in page,
      "background clicks are not wired to the hull picker")
check('{ekey:e, dash:_dash}' in page and '{ekey:e, skey:sub}' in page,
      "cluster hulls lost their routing keys (ekey/skey) — the picker cannot name a panel")
check('"— no hidden functions here"' in page, "the Stars section lost its honest-empty line")
# batch 23 (Everything tuning): navigable first · kind rows w/ meaning · paged stars · Sources
check('var KINDTIP=' in page and 'function kindRow' in page,
      "Elements rows lost their kind glyphs + meaning tooltips (KINDTIP/kindRow)")
check('function fnChips' in page and '"show less"' in page and 'shown+PAGE' in page,
      "the Stars paging wall (preview → +30 → show less) is gone")
check('Array.isArray(st.web.unmatched)' in page,
      "REGRESSION: the web-bridge row stringifies the unmatched ARRAY ([object Object])")
check('"Sources"' in page and 'sechd("entity","Entities"' in page,
      "Sources section or the leading Entities section is gone")
check('{class:"tipico "+(t.cls||"info")}' in page and '"info"),title:t.text' not in page,
      "REGRESSION: tipIcon carries a native title again — info icons must show ONLY the styled dark tip")
check('function _tipPlace' in page and 'r.right>iw-8' in page and 'tip.style.bottom="19px"' in page,
      "edge-aware tip placement is gone — tips clip at the viewport edges again")
# batch 24: direction markers + per-strategy core icons (pills + inherited by cluster surfaces)
check('window.__uniCoreIco=' in page and "(o.ic||'')+o.t" in page,
      "core-strategy icons are gone from the config pills (__uniCoreIco / pillHTML ic slot)")
check("ic:__uniCoreIco(k,12)" in page and '_coreOpts(["community","usecase","kind","fk","layer","tests"])' in page
      and '_coreOpts(["screen","community","kind","usecase"])' in page,
      "the per-side core lists (backend 6 · frontend 4) must each map through __uniCoreIco")
check('P.drill=' in page and 'P.up=' in page and 'function dirIco' in page,
      "drill-down / go-up direction markers are gone from the nav rows")
check('"__core"' in page and 'function coreLead' in page,
      "cluster rows no longer inherit the ACTIVE core strategy's icon")
# batch 25: hull selection light — containers brighten per panel level, rebuild-proof, Esc clears
check('window.__uniApplyHullSel=' in page and 'm.__baseOp=m.opacity' in page,
      "the hull selection light is gone (apply engine + lazy stock capture)")
check('window.__uniFleetSpot=' in page and 'data-fle=' in page and '_flOpen[ent]=1; __uniFleetRender(); return;' in page,
      "the fleet spot is gone (selection no longer mirrors into the fleet panel / cluster no longer opens its entity)")
check('__uniFleetSpot(hs.ent, hs.sub)' in page and '.flrow.spot' in page,
      "the hull engine no longer drives the fleet spot (or its CSS is gone)")
# batch 27: number-key fleet toggles (1–8 → columns 2–9, selection-scoped) + row-background spot
check('window.__uniFleetToggle=' in page and page.count('__uniFleetToggle(')>=2,
      "the shared fleet toggle is gone (clicks + number keys must use ONE path)")
check("k>=\"1\"&&k<=\"8\"" in page and 'hs.ent||"*"' in page,
      "the 1–8 number keys no longer toggle fleet columns for the selection")
check('class="flkey"' in page and 'rgba(76,110,245,.26)' in page,
      "fleet header key labels or the row-background spot styling are gone")
# batch 29/30: config-into-fleet — the SIDE DRAWER with per-column panes; zone buttons deprecated
check('data-pane="planets"' not in page and 'data-pane="universe"' not in page and 'window.__uniFlPanes=' in page,
      "the Planets AND Universe tabs must be GONE — their config lives in the fleet side drawer")
check('CFG.zDef=CFG.zAtk=CFG.zCfl=CFG.zSat=true;' in page,
      "the deprecated per-zone gates must be forced ON (fleet columns are the only zone control)")
check('window.__uniFlOpen=' in page and 'id="flstash"' in page and 'document.body.appendChild(side)' in page
      and 'window.__uniFlDock=' in page,
      "the fleet side drawer must be a FREE-STANDING body-level add-on docked to the fleet (__uniFlDock)")
check('flcfgbtn' in page and page.count('flcfgbtn')>=2,
      "the fleet header icons no longer open the drawer")
check('k:"show"' in page and t_order(page),
      "fleet column order must be Entity(show) · Sub-cluster(subs) · Planets · Connections(wires)")
check('Math.max(m.__baseOp*2, floor)' in page and 'm.__baseEm' in page,
      "the entity light lost its absolute floor / emissive glow (a bare ×factor is invisible on big shells)")
check('window.__uniHLSelectLink=' in page and '_whf=Math.max(_whf,1)*2.6' in page,
      "wire selection lost its glow boost or its BFS highlight (batch 38)")
check('var _lchip=function' in page and page.count('__uniHoverHL(id)')>=1,
      "the link card endpoint chips lost their hover halo (element-card parity, batch 39)")
# batch 40: F mode toggle · focus keeps the selected glow · hover lights the wire
check('(e.key==="f"||e.key==="F")' in page and 'HL.mode!=="glow" && !d0' in page,
      "F mode toggle or the focus-keeps-selected-glow rule is gone")
check('window.__uniHovLink===l' in page and page.count('__uniHovLink')>=4,
      "chip hover no longer lights the wire to the hovered element")
# batch 41: theme toggle + theme-aware highlight wires
check('id="themeBtn"' in page.replace("'",'"') and 'window.__uniApplyTheme=' in page and ':root[data-theme="light"]' in page,
      "the dark/light theme toggle is gone (button + apply + light var block)")
# batch 42: entity pane rebuild — combo row · options icon-toggles · the SPREAD slider
check('getElementById("fnsTog")' not in page and '"typesTog"' in page, "the Functions boolean must be gone while the Types boolean stays (operator: functions via the legend, types deferred)")
# batch 45: consumes + nests rels flow through the universe (the floating-schema fix)
# batch 46: endpoint→handler wires (Functions ON) + the honest empty-connections message
# batch 47: fleet clicks SELECT — name = panel+camera · count badge = expand · cluster name = cluster
check('class="flcnt flexp"' in page and 'ev.stopPropagation();' in page and '_frameSet(ids)' in page,
      "fleet selection clicks are gone (name must select+fly; the count badge must own expansion)")
check('data-fse=' in page and 'data-fss=' in page,
      "cluster fleet rows lost their select keys")
check('rel:"handler"' in page and 'fn:p.fn' in page,
      "endpoint→handler wires are gone (the fn field or the _buildFnData join)")
check('behavior lives in the call tree' in page and 'DYNAMIC (unmatchable templates' in page,
      "the empty-Connections message no longer explains WHERE the behavior lives")
check("consumes:'calls'" in page and "nests:'fk'" in page,
      "REL2KIND lost the consumes/nests mappings — the new wires would fall to the calls default silently")
check('consumes:"consumed by"' in page.replace("'",'"') or 'consumes:"consumes"' in page,
      "the card labels for consumes/nests rels are gone")
check('"spreadRng"' in page, "the SPREAD slider is gone (element separation inside entities)")
check('(window.__uniSpread||1.4)' in page and 'min="0.55" max="2.8"' in page and 'value="1.4"' in page and 'className="cfgrow rsrow"' in page,
      "spread scales RENT, default bumped to 1.4 (operator: dense entities overlapped) — the slider matches")
check('className="cfgrow entcombo"' in page,
      "the entity combo/options rows are gone")
check("'Legend</b>" in page.replace('"',"'") and '#elegend .lghd b svg' in page,
      "the legend lost its panel-chrome refit (iconed caps title + station styling)")
check('height:384px !important' in page,
      "the legend must hold ONE fixed size across every tab (sized to the Types tab, no scroll)")
check("lgbody lg-" in page and 'lg-types' in page and 'grid-template-columns:1fr 1fr' in page,
      "the legend Types two-column compaction is gone (per-tab body class + grid)")
check('_hlc=hov?' in page and '0x4f46e5:0xffffff' in page and '_hlc||(band!=null?band:(_gr?0xffffff:cfg.color))' in page,
      "highlighted wires lost their theme highlight color (white dark · indigo light)")
# D2W — the calls-wire heat spectrum (Proposal A, discrete bands). Emitter attaches d2w to fn_nodes;
# render colours a calls wire by its TARGET function's distance-to-write via BANDPAL.
check('window.BANDPAL=[' in page and 'window.__uniD2W=true' in page and 'window.__d2wBand=function' in page,
      "the D2W band palette / toggle / helper is missing (calls-wire heat spectrum)")
check('var _band=(l.rel==="calls"&&window.__d2wBand)?__d2wBand(_ct):(l.write&&window.__feD2WBand)?__feD2WBand(_ct):null;' in page and '===l), _band); });' in page,
      "the BACKEND heat still keys on the true `calls` REL (F2), and the FE write heat rides the SEPARATE `l.write`+fed2w branch (blue→magenta)")
# ── FE WRITE-SPINE heat (operator D1/D3/D4): a distinct blue→magenta gradient, its OWN toggle, default off ──
check('window.FEBAND=[0xc026d3,' in page,
      "the FE write gradient is the previously-decided option-A palette (0xc026d3 magenta AT the write → blue far), NOT the BE BANDPAL")
check('window.__uniFED2W=false;' in page,
      "the FE write heat has a SEPARATE toggle (operator D4), DEFAULT OFF")
check('data-fed2wtog="1"' in page and 'FE write heat <i>' in page,
      "the legend carries the SEPARATE FE-write-heat toggle row")
check('window.__uniWriteRing=false;' in page,
      "the write-spine node ring is a SEPARATE toggle (operator D2), DEFAULT OFF")
check('#jrnpill{ display:flex; align-items:center; justify-content:center; gap:6px; width:248px; flex:none' in page,
      "the journey-walker slot is a FIXED-WIDTH reserve (operator: the header must not shift when a journey enters/leaves)")
# ── the write-spine node RING pass (D2) + journey-tab ICONS (operator) ──
check('window.__uniDrawWriteRings=function' in page and 'if(window.__uniDrawWriteRings) __uniDrawWriteRings();' in page,
      "the write-ring pass is defined AND hooked into updateConnectors (rides the stub hook)")
check('data-writeringtog="1"' in page and 'write rings <i>' in page,
      "the legend carries the write-ring toggle row")
check('var _JRNKINDICO={' in page and '''title="'+kd[1]+'"''' in page and '(_JRNKINDICO[kd[0]]||kd[1])' in page,
      "the journey-kind tabs render ICONS with the type-word on hover (title=), not the title text")
# ── icon-less kinds now iconed (operator: the cubes — flag/provider/module/web/middleware/prompt) ──
_order = page.split("var order=[", 1)[1].split("]", 1)[0] if "var order=[" in page else ""
for _k in ("flag", "provider", "module", "web", "middleware", "prompt"):
    check(f"{_k}:'<" in page and f'"{_k}"' in _order,
          f"the '{_k}' kind has a Lucide GLYPH and is registered in the billboard `order` (was a cube)")
check('d2w:f.d2w' in page,
      "the levels fn_node d2w no longer rides onto the render node (call-wire heat lost its source)")
check('t:"d2wtog"' in page and 'function _bandSpectrumHTML' in page and 'it.k==="calls"?_bandSpectrumHTML()' in page,
      "the D2W band spectrum no longer folds into the calls info-popup (+ the on/off toggle row)")
check('data-d2wtog' in page and 'window.__uniD2W=!window.__uniD2W' in page,
      "the legend d2w on/off toggle no longer flips __uniD2W")
check('CALLS · DISTANCE HEAT' in page and 'data-band=' in page and 'data-bandcopy=' in page and 'BANDPAL0' in page,
      "the D2W band calibrate/copy config (5 colour inputs + copy + reset) is missing")
# DOUBLE-CLICK a node → reveal + light its one-hop neighbourhood (operator)
check('window.__uniRevealNeighbors=function' in page and 'hop.forEach(_force)' in page,
      "the double-click one-hop reveal (__uniRevealNeighbors) is missing")
check('window.__uniLastClick' in page and '_ct-_lc.t)<350' in page and 'window.__uniRevealNeighbors(n)' in page,
      "the onNodeClick double-click detection (same node <350ms → reveal) is missing")
# connector legend declutter: the row <i>description</i> moves behind an info ⓘ hover popup (operator)
check('function _lglbl' in page and page.count('_lglbl(it.l')>=2 and 'lglbl .tipico .tip' in page,
      "the connector-legend info-popup declutter (_lglbl on the ln + band rows) is missing")
# search-select routes through the SAME path as click+focus (__uniGoto: reveal-if-hidden + select + frame)
check(page.count('__uniGoto(n.id)')>=3,
      "the search-result select no longer routes through __uniGoto (reveal+select+frame, like a click)")
check('--chip-bg:#0e1524' in page and page.count('var(--chip-bg)')>=15,
      "the station's dark surfaces are hardcoded again (light theme cannot flip them)")
check('if(window.__uniSelHulls) __uniSelHulls(n);' in page,
      "element displays no longer light their cluster+entity hulls (showPanel hook)")
check('buildClusters=function(){ _bcOrig();' in page,
      "hull rebuilds drop the selection light (buildClusters wrap missing)")
check('out.push(aboveSec(n)); return out;' in page,
      "element cards lost their Above section (the way back up)")

# ── 10u. batch 48: the FRONTEND fold — c4.fe pieces (component · hook · store · route · type · module) + typed
#        wires on a SEPARATE key; screens absorbed into their principal piece; Types held back (toggle, OFF) ──
check('KINDS.module={' in page and 'form:"slab"' in page and 'if(f==="slab")' in page,
      "the `module` kind (slab form) is gone — plain TS modules have no glyph")
check("GLYPH.module='<rect x=\"3\" y=\"3\"" in page, "the module legend glyph (grid) is gone")
check('var FE_KIND={ "fe-type":"type", "fe-unknown":"unknown" };' in page and 'var FE_REL={ "uses-hook":"uses", "uses-store":"reads" };' in page,
      "the feed→spike kind/rel vocabulary maps are gone")
check('var _FE=(_C4.fe&&_C4.fe.pieces&&_C4.fe.pieces.length)?_C4.fe:null' in page,
      "the fe fold must gate on a NON-EMPTY pieces list (honest-empty feed = no fold)")
check('ENT[h.id]=(h.pair&&ENT[h.pair])?' in page and 'var FE_HOME_COL={ bucket:' in page,
      "non-entity homes (buckets · candidate features) must become their own coloured clusters")
check('var _P=_FE.pieces; (_FE.edges||[]).forEach(function(e){ var a=_P[e[0]], b=_P[e[1]];' in page,
      "fe wires must be read as COMPACT index triples over fe.pieces")
check('NIDS[n.screen].kind==="web") ABS[n.screen]=n.id;' in page and 'window.__uniFeAbsorbed=' in page,
      "screen absorption is gone (a fetching file would draw TWO nodes: web + piece)")
check('var _FETYPES=[], _FETYPELINKS=[];' in page and 'function toggleTypes(on){' in page and '"typesTog"' in page,
      "the Types toggle (fe-type pieces held back at boot, seeded on demand) is gone")
check('showTypes:"off"' in page and 'else if(grp==="showTypes"){ toggleTypes(CFG.showTypes==="on"); }' in page,
      "CFG.showTypes must default OFF and route through applyCfg")
check("fecall:'calls'" in page and 'LINKMETA.fecall={w:3,pv:1}; LINKMETA.imports={w:2,pv:1};' in page,
      "the fecall/imports rels lost their wire-kind / meta mapping")
check('["component","hook","store","route","type","module"].forEach(function(k){ if(!C[k]) C[k]=feBuilder; });' in page
      and 'function feSec(n){' in page, "the shared frontend card builder is gone")
check('"frontend arm",' in page and 'screens absorbed' in page, "the Everything panel's frontend-arm Sources row is gone")
check('var order=["route","component","hook","type","store","module","screen","web",' in page,
      "the legend roster lost `module`")

# ── 10v. batch 49: journeys walk a FRONTEND leg (bridge+uses/renders, client-side) · the header SEARCH ──
check('function _jrnFeLeg(carriers)' in page and 'l.rel==="bridge"' in page
      and '(l.rel==="uses"||l.rel==="renders"||l.rel==="fecall"||l.rel==="reads")' in page,
      "the journey frontend-leg derivation is gone (bridge -> screens -> users incl. fecall/reads callers)")
check('j.fe=_jrnFeLeg(j.carriers); j.feN=' in page, "journeys no longer precompute their fe leg (row/pill chips would lie)")
check('WRAPPER CLIMB' in page and 'sn.kind==="module"' in page and 'c.ent!==sn.ent' in page,
      "the FE-leg WRAPPER CLIMB: a bridged shared-lib MODULE with a cross-entity caller (an SSE client like lib/api/sse) is swapped for its feature callers, so the leg reaches the feature screen not the lib — proven on gustify: Create-a-recipe 0→2 → useRecipeStream → GustifyGenerateSheet")
check('(kind==="mclass")?"module class":' not in page and '(kind==="mclass")?["api","render-fn","model","config","lib","logic"]' in page,
      "__badgePop's key ternary carries no string branch for mclass (2026-09-05: keys.forEach threw on the Module ⓘ)")
check('if(!_bm && !sel) return;' in page and 'window.__uniSelectLink=function(l)' in page and 'if(window.__uniSelectLink) __uniSelectLink(l);' in page and 'function wireVisSec(l)' in page and 'function fkKey(s, t)' in page and 'class="lrex lrexl"' in page and '.lrex:not(.lrexl)' in page,
      "WIRE SELECTION (2026-09-05): a selected wire draws even when its kind beam is 0 (the vanishing rollup); one select path; the card says why a wire is hidden; the FK key line; example WIRE chips on the reference's connector rows")
check('window.__uniBudget=1600;' in page and 'window.__uniScaleGuard=function' in page and 'window.__uniApplyDeepLinks=function' in page and 'q.get("journey")' in page and 'window.__uniPanelEnt=function' in page and 'if(window.__uniScaleGuard){ try{ __uniScaleGuard(); }catch(e){} }' in page,
      "PASS 4 (2026-09-06): the node budget + scale guard (booted at tier 0 above it), the ?journey= / ?ent= deep links, the entity-panel handle")
# ── legend pass (2026-09-06) · Step 0: the endpoint ⓘ popover lists TASK — the two method arrays must be the SAME list (paired assert) ──
import re as _re0
_pop = _re0.search(r'\["GET","POST","PUT","PATCH","DELETE","BOOT","TASK"\]:\(kind==="count"\)', page); _sec = _re0.search(r'\["GET","POST","PUT","PATCH","DELETE","BOOT","TASK"\]\.forEach', page)
check(_pop is not None and _sec is not None and 'key==="TASK"?"worker task — dispatched by name from a queue"' in page,
      "Step 0: the __badgePop method list equals the compact-legend method list (TASK in both) and the popover head names the worker task")
# ── Step 3: the dispatches wire — CONN entry, kind list, beam, legend row, definitions, reference stock == CONN, the matrix hop ──
check("dispatches:'dispatches'" in page and "dispatches:{color:0xf76707,style:'longdash'" in page and "'access','dispatches']" in page and 'dispatches:0.7 }' in page
      and 'wireRow("dispatches")' in page and '{t:"ln",k:"dispatches"' in page and '"x:dispatches":' in page and 'dispatches:{col:"#f76707",style:"longdash"}' in page
      and 'longdash:[2.6,1.2]' in page and 'style==="longdash"?"10 4"' in page and 'uses:1, dispatches:1}' in page and 'dispatches:["dispatches"]' in page
      and 'dispatches:"inferred · by-name floor' in page and 'if(rel==="dispatches"){ return note(' in page
      and 'sparse:"5 10", longdash:"10 4" };' in page and '"sparse","longdash"].map(' in page   # the compact legend + the config sample paint from DASHMAP (review 2026-09-06)
      and 'handed off here by name: a queue or the event bus routes to this function after ' in page and 'the event bus routes here after ' not in page,
      "Step 3: the dispatches wire is registered on every surface (CONN · kinds · beam · legend row · definitions · reference stock · matrix hop · trust · carries)")
_cs = _re0.search(r'dispatches:\{col:"(#[0-9a-f]{6})",style:"(\w+)"\}', page); _cn = _re0.search(r"dispatches:\{color:0x([0-9a-f]{6}),style:'(\w+)'", page)
check(_cs and _cn and _cs.group(1) == "#" + _cn.group(1) and _cs.group(2) == _cn.group(2), "Step 3: the reference stock swatch equals the drawn CONN (colour + style cannot drift)")
# ── legend pass · Steps 5–7 (2026-09-06): the provider CLASS badge family · the DELIVERY (stream) badge on a second slot · FE homing said ──
check('pclass:p.pclass||null' in page and 'pclass:{llm:"#d946ef"' in page and "key==='llm'" in page and "key==='observability'" in page and 'n.kind==="provider" && n.pclass' in page
      and 'function _exPc(pc)' in page and '_badgeRow("pclass", pc, pc,' in page and all(('"pclass:%s":' % _k) in page for _k in ("llm","embed","vector","agent","infra","http","observability","payments")) and 'provider:function(n){' in page
      and '(kind==="pclass")?["llm","embed","vector","agent","infra","http","observability","payments"]' in page and '(kind==="pclass")?"provider class' in page
      and '(n.kind==="provider" && n.pclass) ? {kind:"pclass", key:n.pclass}' in page and '(_bik==="pclass")?"the provider classes' in page,
      "Step 5: the pclass badge family on every surface (adapter · colours · glyphs · painter · example · reference rows · definitions · popover · ⓘ · header · card)")
check('srcRow("alert","files skipped"' in page and 'srcRow("link","route mounts"' in page and 'srcRow("layers","twin pass"' in page and 'st.web.extractor?("via "' in page and 'SDK method(s) read from the generated client' in page
      and 'sizable function(s) over the' in page and '" pairs over a "' not in page and 'candidate pair(s) compared on shared rare identifiers' in page,
      "Step 5: the three Sources rows (alert · link · layers) + the bridge idiom on the web row; the twin-pass row says what the budget caps (sizable functions), never 'pairs over a budget' (review 2026-09-06)")
check('delivery:{stream:"#06b6d4"}' in page and 'kind==="delivery"' in page and 'n.kind==="endpoint" && n.stream' in page and '_sb.__slot=1' in page and '(b.__slot||0)*(sz*0.72)' in page
      and '_badgeRow("delivery", "stream"' in page and '"delivery:stream":' in page and 'function _exStream()' in page and '(kind==="delivery")?["stream"]' in page and 'It streams: the reply keeps arriving' in page and 'Worker task — runs on a worker' in page,
      "Step 6: the delivery badge family (colour · glyph · second slot · positioner · reference row · definition · popover · step copy)")
check('TASK:"#f0abfc"' in page and 'TASK:"#a78bfa"' not in page, "Step 6 (D4): the TASK disc left the endpoint body's hue — fuchsia-light, no violet-on-violet")
check('stream:"stream — the handler returns a streaming response (SSE / chunked)' in page and 'the response is an async generator' not in page and 'the ⓘ on a badged row (endpoint · function · schema · component · module · hook · provider) opens its key' in page,
      "Phase 2 review (2026-09-06): the delivery definition claims a streaming response (what _streams proves), not an async generator; the compact-legend note names every badged row's ⓘ")
check('homedBy:p.homed_by||null' in page and 'function homeRow(n){ return n.homedBy==="config"?kv("link","home"' in page and page.count('homeRow(n),')==3 and 'homed by the entity config' in page and 'homed by the feature layout' in page and 'the same home, a different witness' in page,
      "Step 7: FE homing — the adapter carries homedBy, the hook/component card says it, the Sources row names the witness (layout or config)")
check('(kind==="pclass")?"provider class":' not in page, "Step 5: no stray string-branch in the popover key ternary (the 269d17c class of bug)")
check(page.count('homeEv:p.home_ev||null') == 2 and 'function homeEvRow(n)' in page and page.count('homeEvRow(n),') == 4 and 'srcRow("role","homing evidence"' in page
      and 'evidence only, nothing re-homed' in page and 'location is an indicator, never the definition' in page and '"MOVE CANDIDATE → "' in page and '"SHARED — a cross-cutting aspect across "' in page and 'function _hslug(s)' in page and 'users abstain' in page and 'not a declared entity' in page,
      "Part C (2026-09-06): the membership-evidence field on endpoint nodes + fe pieces, the evidence row on every fe builder + the endpoint card, the Sources row — evidence only, nothing re-homed")
check('C.store=feDataBuilder; C.type=feDataBuilder; C.hook=feHookBuilder; C.component=feHookBuilder;' in page and 'function carriesSec(l)' in page and page.count('carriesSec(l)')>=1 and 'function carriesSec(l)' in page and '{t:"ln",k:"renders"' in page and '"x:typed":' in page and 'if(/tog$/.test(it.t||"")) return;' in page and page.count('structureSec(n),\n') >= 1,
      "CARD ORDER + CARRIES + CONNECTORS (2026-09-05): data kinds put Structure before Connections; hooks/components list the shapes they handle; every wire card says what it carries; the frontend wires join the connector roster; the reference lists wires only")
check('cols:(p.fields||p.members||[]).map(function(c){ return [c[0], c[1]||"", ""]; }), shape:p.shape||null' in page and 'n.kind==="store"){ op="client state"; opk="store"; fields=(n.det&&n.det.cols)||null;' in page and 'the frontend\'s table: its fields are its value type' in page,
      "STORE SHAPE (D5 2026-09-05): a store's fields / a type's members ride det.cols; the matrix reads a store like a table; the definition says so")
check('hrole:{fetcher:"#3b82f6",streamer:"#8b5cf6",store:"#ec4899",orchestrator:"#f59e0b",effect:"#ef4444",deriver:"#8794ab"}' in page and 'n.kind==="hook" && n.hrole' in page and '_badgeRow("hrole", hr, hr,' in page and '(it.k==="hook")?"hrole":(it.k==="provider")?"pclass":null' in page and 'hrole:p.hrole||null' in page and '"hrole:fetcher":' in page,
      "HOOK ROLES (D2 2026-09-05): the hook badge palette · buildNode badge · legend-reference rows · the hook row's ⓘ · the adapter field · definitions")
check('xp:e.export||null' in page and 'if(l.xp && NIDS[l.xp]) l.source=l.xp;' in page,
      "D3 (2026-09-05): a bridge's export piece wins over the file's absorbed piece — the journey's FE leg starts at the hook that fetched")
check('type:"Middleware (app-wide)"' in page and '"role:gate":"the check that can say no' in page and 'not a journey\'s gate' in page,
      "D4 (2026-09-05): gate is ONE concept — the role badge (endpoint guard or chain function); the Middleware row is the app-wide wrapper, never a journey's gate")
check('backend:["endpoint","function","schema","model","external","entity","middleware","flag","provider","prompt","element"]' in page and page.count('"external","entity","middleware","flag","provider","prompt","element"]')>=3 and 'middleware:"a wrapper the app runs on EVERY request' in page and 'provider:"an outside service' in page,
      "LEGEND ROSTER (2026-09-05): middleware · flag · provider · prompt appear in the group roster, the legend reference and the compact legend, each with a definition — the elements panel counted them while the legend did not")
check('l.rel!=="mounts"&&l.rel!=="fecall"' in page and 'return best||view||comp;' in page and '"render-fn":"#d946ef"' in page and 'logic:"#22d3ee"' in page and '(it.k==="module")?"mclass":(it.k==="hook")?"hrole":(it.k==="provider")?"pclass":null' in page,
      "JOURNEY STARTS AT A VIEW (2026-09-05): the anchor walk follows fecall and falls to a view/any component; render-fn + logic badges off the module amber; the Module legend row carries the class-key ⓘ")
check('var _JRNLEVELS={' in page and 'Orientation' in page and 'Core' in page and 'Specialized' in page and 'level:(w.level>=1&&w.level<=3)?w.level:0,   // dev-onboarding level (1/2/3) — a DRAFT carries the level the drafter suggested' in page and 'var L=j.level||99;' in page and 'drafts — review' not in page,
      "journey EXPERTISE LEVELS (operator): workflows carry a curated `level` CLAMPED to 1/2/3 (out-of-range → 0 = one 'other' bucket) + the 3-tier onboarding roster")
check('if(sel==="wf"){' in page and 'byLvl' in page and 'jglvl' in page and 'function _lvlBars' in page and 'jrnlede' in page,
      "the workflows tab GROUPS by onboarding level (①→②→③ top-down) with a filled-bar ramp + a visible lede — a new dev reads it as a ladder, not a flat 'user workflows' list")
check('window.__uniJrnLvlSolo=function' in page and 'jglvlhint' in page,
      "a LEVEL is discoverable + focusable: a visible per-tier hint + a middle-click tier-solo (mirrors the entity solo) — the onboarding persona can isolate ① in one gesture")
check('function _commitCollect()' in page and '["commit","commits"]' in page and 'j.commit?"commit"' in page and 'if(sel==="commit"){' in page and 'commits.js' in page,
      "COMMIT journeys (operator): each recent commit is a journey KIND — window.GABE_COMMITS → _commitCollect → the 'commits' tab, grouped by date bucket, walked like any journey")
check('return !!_fnById(id);' in page and 'commit:true, corpora:{commit:1}' in page,
      "a commit-journey's carriers are only nodes STILL on the map (a touched id that no longer resolves is dropped — honest coverage view)")
check('window.__uniRenderTierIcons=function' in page and 'var _TICO={' in page and 'window.__uniTierIcoSet="grid";' in page and 'function _tierIcoPill()' not in page and 'data-grp="tierIco"' not in page,
      "TIER ICONS SETTLED (operator): the header T0–T3 buttons wear the DETAIL GRID set everywhere; the switcher UI is retired (no config control, no other sets)")
check('id="jrnEntTog"' in page and 'window.__uniJrnEntOpen=!window.__uniJrnEntOpen' in page and 'COLLAPSED by default' in page,
      "the ENTITY picker is COLLAPSED behind a one-line toggle (operator: all-at-once was too much)")
check('class="jglvlinfo"' in page and 'vars:"Classified here:' in page and 'var _JINFO=' in page,
      "each LEVEL header carries a classification INFO icon (operator): hover shows what variables put a journey in that tier (like the connector legend)")
check('feclass:{connector:"#f97316",container:"#a855f7",leaf:"#84cc16",private:"#8794ab",detached:"#fb7185"}' in page and 'function feclassBadge(fc, kind)' in page and 'n.feClass==="connector"||n.feClass==="container"||n.feClass==="leaf"||n.feClass==="private"||n.feClass==="detached"' in page and 'var _FCALL=["view","private","connector","container","leaf","detached"]' in page and 'component:"#2f7de1"' in page and 'n.feClass==="view"&&billTex["screen"]' in page
      and '(it.fc==="view")?svgInline("screen",VIEWCOL,15)' in page,
      "COMPONENT CLASS palette (operator): view=SCREEN glyph; connector=blue arrow · container=VIOLET layers · leaf=LIME leaf · private=gray star — container off gray (2-gray clash), leaf off green (GET/hook collision); all four badged")
check('function _dispK(n)' in page and 'return _isView(n)?VIEWCOL:n.col;' in page and 'var K=_dispK(n);' in page and 'svgInline("screen",VIEWCOL,18)' in page,
      "VIEW display kind: one helper (_dispK/_isView/VIEWCOL) feeds node colour, panel head, hover, kind chips, walk card + legend — a view is never printed as an orange COMPONENT")
check('window.__uniJrnStart=function(cid)' in page and '__uniJrnStart(r.getAttribute("data-jr"))' in page,
      "the factored journey starter is gone (picker rows + search must share ONE start path)")
check('!_nodeVisibleFn(n)){ try{ __uniReveal(n.id)' in page and 'a step SELECTS its element' in page,
      "a journey/trail STEP must reveal its element's cluster+entity when the fleet has it hidden (operator: stepping = selecting)")
check('_wActive=(WALK.mode==="trail"||WALK.mode==="journey") && WALK.steps.length' in page and 'class="wclear tbico"' in page and 'HL.jrObj.name||HL.jrObj.cid):"trail"' in page,
      "a selected JOURNEY becomes the current trail (trail bar shows for journey mode, titled with the journey name) + a CLEAR button next to the title — operator")
check('fe.concat(j.carriers)' in page and 'WALK.mode="journey"; WALK.steps=fe.concat(j.carriers)' in page,
      "the walk no longer steps the frontend leg FIRST (users -> screens -> carriers)")
check('if(HL.exact){' in page and 'HL.exact=true; HL.mode="glow"; HL.origin=fe.concat(j.carriers)' in page,
      "journeys keep the EXACT-set highlight in GLOW/context mode (a depth-BFS from the dense fe cluster lit 2,824 wires — screen noise; and a journey must not inherit the click→focus-hide default)")
check('if(HL.jr){ _hlSyncUI(); return; }' in page and 'HL.depth=Math.max(1,Math.min(5,d));' in page,
      "the depth slider does NOT flood a walking journey (operator): during a journey it keeps the exact clean path, no BFS from the ~67-node path")
check('class="wfe"' in page and 'class="jrnfe"' in page and "svgInline(\"component\", KINDCOL.component" in page,
      "the fe chips (pill + picker rows) lost their ACTUAL component glyph (legend-visual rule)")
check('id="tsin"' in page and 'id="tsdd"' in page and 'id="tsrch"' in page and '.topsearch' in page,
      "the header search markup/styles are gone")
check('window.__uniSrchInit' in page and 'e.key==="/"' in page and 'inp.focus(); inp.select();' in page,
      "the / shortcut no longer focuses the search")
check('CFG.showTypes="on"; try{ toggleTypes(true); }catch(e){}' in page and 'turns Types ON' in page,
      "a held fe-type found via search must turn Types ON before selecting")
check('window.__uniSelNode=_selNode' in page, "the search lost the ONE node-select path (card export)")
check('_jrnCollect().forEach' in page and 'Object.keys(SUBANCHOR).forEach' in page,
      "the search index dropped journeys or clusters")
# 10v-b: the adversarial-review fixes (15 confirmed findings, 2026-08-23)
check('var _esc=function(x)' in page and '_esc(r.label)' in page and '_esc(inp.value.trim())' in page,
      "search innerHTML lost its escaper (labels are code identifiers; the echo is raw keyboard text)")
check('_jp.style.display="none";   // exclusive surfaces' in page,
      "opening the search dropdown must CLOSE the journeys picker (#jrn z-55 paints over the trapped dropdown)")
check('"functions (off)"' in page and 'turns ƒ ON' in page,
      "held functions (ƒ off) lost their search group — a function search would flat-line at no match")
check('return !!(NIDS[id] || (_CAPST&&_CAPST.byPiece[id]&&_fieldN(id)));' in page,
      "the journey FE leg is included regardless of tier-visibility (a workflow STARTS at the frontend, the wake surfaces its kind — operator); a genuinely fleet-hidden entity still shows the 'node not drawn' note")
check('addEventListener("focusout"' in page, "keyboard blur no longer closes the search dropdown")
check('_seen.reduce(function(a,gk)' in page, "search group headers can fragment again (regroup after the cap)")
check('#jrn .jrnrow.on .jrnfe{ color:#fff; }' in page, "the selected journey row's fe chip lost its contrast override")

# ── 10w. batch 50: fe· home identifier · FE community/usecase clusters · scaffold cut · controls trim ──
check('window.__uniEntLabel=function(e){ if(!e) return e; var nb=__uniNamingBlock(), conv=__uniConvention()' in page and '(fe?"fe · {name}":"{name}")' in page,
      "the fe-home display identifier is gone")
check('__uniEntLabel(e):e' in page and '__uniEntLabel(ent):ent' in page and '__uniEntLabel(label):label' in page,
      "an entity-name surface (fleet / panels / hull sprite) lost the fe· prefix")
check('function _feAssignSub(mode)' in page and 'if(l.rel!=="bridge") return;' in page and '"c·"+' in page,
      "FE community/usecase clustering is gone (every core except Kind would collapse fe pieces to one blob)")
check('try{ _feAssignSub(mode); }catch(e){}' in page, "assignSub no longer routes fe pieces through _feAssignSub")
check('#ctrlp .ctlrow{ flex-wrap:wrap; }' in page, "controls rows can overflow the border again")
check('measureText(txt).width' in page and 'cv.width=Math.max(256, tw);' in page,
      "labelSprite lost its text-fitted canvas (a long label clips both ends — 'fe · design-system' rendered '· design-syst')")
check('c.lbl.scale.set(_lh*_la, _lh, 1);' in page,
      "cluster label rescale lost the canvas-aspect rule (a text-fitted canvas squeezes at fixed 50x12.5)")

# ── 10x. batch 51: card-chip navigation (the 7-step trail) · legend hide-by-kind · fe/backend groups ──
check('window.__uniGoto=function(id)' in page and 'if(window.__uniGoto) __uniGoto(x.id);' in page
      and 'if(window.__uniGoto) __uniGoto(id);' in page,
      "card/link chips lost their click navigation (select + frame + the 7-step trail)")
check('window.__uniKindOff={};' in page and 'if(window.__uniFoldHelpers!==false && n.__solo && !window.__uniPin[n.id]) return _KOFF;' in page,
      "the BINARY visN gate (off / on + the GLOBAL helper-fold) is gone")
# binary legend + component-class rows + the fold-helpers toggle (control-system phase 2)
check("__uniKindToggle=function(k){ if(!k) return;   // BINARY" in page and 'cur==="off"?"all":"off"' in page and 'window.__uniFoldHelpers=true;' in page,
      "the legend is no longer BINARY (on/off) with a global fold-helpers toggle")
check('t:"feclass"' in page and 'data-lgfc=' in page and '__uniFeClassToggle(rw.dataset.lgfc)' in page and 'data-lgfold=' in page,
      "the component-class legend rows + the fold-helpers row are gone")
# FEATURE A (operator): view MERGED into a Frontend TYPE row (the phantom screen kind dropped, 0 nodes) + the OTHER
# classes (connector/container/leaf/private) moved behind a component ⓘ that reuses the __badgePop key machinery.
check('["route","component","hook","type","store","module","web"]' in page and '{t:"feclass",fc:"view"}' in page and '{t:"hd",l:"component classes"}' not in page,
      "the FE legend group dropped the phantom screen row / kept the component-classes group / lost the View type row")
check('(it.k==="component")?"feclass"' in page and 'the component classes (how each is drawn)' in page,
      "the Component (FE) legend row has no ⓘ badge-key dot (feclass)")
check('kind==="feclass")?["connector","container","leaf","private"]' in page and '(kind==="feclass")?"component class"' in page,
      "__badgePop does not list all FOUR feclass badges (connector/container/leaf/private) in the component ⓘ popup")
check('view — its own type row' in page and '.badgepop .bpnote{' in page,
      "the feclass popup footer note (view = own type · private = plain) + its CSS are gone")
# FEATURE B (operator): the legend header ⓘ opens a full graph-area REFERENCE (__uniLegRef) — every FE/BE type +
# badge with its actual glyph + a live search example; the example chip fills the bar + focuses (__uniSearchGo) + closes.
check('window.__uniLegRef=function' in page and 'window.__uniSearchGo=function' in page and 'class="lgref"' in page and 'if(window.__uniLegRef) __uniLegRef();' in page,
      "the legend-reference overlay (__uniLegRef) + its search-go bridge + the header ⓘ button + wiring are gone")
check('id="uni-legref"' in page and '#uni-legref{' in page and 'left:var(--navw); right:0; top:var(--topbarh)' in page,
      "the #uni-legref overlay markup/CSS (full graph-area, theme-var positioned) is gone")
check('function _exNode(pred)' in page and 'function _exMethod(m)' in page and 'function _exFc(fc)' in page and 'class="lrex"' in page,
      "the reference derives examples from real loaded nodes (per kind/feClass/method) into clickable chips — gone")
check('if(id && window.__uniGoto){ _close(); if(inp) inp.blur(); try{ __uniGoto(id); }catch(e){} return true; }' in page,
      "__uniSearchGo no longer prefers __uniGoto(id) (would reintroduce best-match ambiguity for example chips)")
# reference refinements (operator): representative descriptions (_LRDESC) · PARENTs get no header example (noEx) ·
# private is one of the FOUR badged classes in the loop · Type/Entity derive off-field examples · honest dash fallback.
check('var _LRDESC={' in page and 'a URL page — one of the app' in page and 'backend logic — the code behind the endpoints' in page and "noEx?''" in page,
      "the reference lost its representative _LRDESC descriptions or the parent no-example (noEx) suppression")
check('["connector","container","leaf","private"].forEach(function(fc){ h+=_badgeRow("feclass"' in page and 'if(k==="type"){ var t=(window._FETYPES' in page and 'if(k==="entity"){ var e=' in page and 'a marker/badge concept, not a searchable node' in page,
      "private not in the reference badged loop / Type+Entity examples not derived / the honest-dash fallback is gone")
# TIER column (operator): each row shows the min tier it appears at (from _TIER_PRESETS), the header shows/sets the
# current tier, rows above it dim; connectors/ships read "any", type reads "manual"; fold count now derives an example.
check('function _minTierKind(k){' in page and 'function _minTierFc(fc){' in page and 'function _tierCell(t, mode){' in page and 'class="lrtdots' in page and 'lrtiersel' not in page and 'n.kind==="schema" && n.__foldN>0' in page and 'uni-legref") && window.__uniLegRef' in page,
      "the reference TIER-DOT column (min-tier from _TIER_PRESETS · the 4-dot cell · NO in-overlay selector · the header-sync refresh in __uniSetTier · the fold-count example) is gone")
# T3 "Everything" truly shows everything incl. the 508 fe-types (operator): its preset koff is EMPTY, and
# __uniSetTier wakes the type layer (toggleTypes) the way it wakes functions (toggleFns).
check('name:"Everything", koff:[],' in page and 'if(k==="type" && window.toggleTypes && !_walk){' in page,
      "T3 no longer shows everything — the Everything preset re-hid type, or __uniSetTier stopped waking the type layer")
# Component (FE) glyph: the REAL color source is KINDCOL (line `KINDS[k].col=KINDCOL[k]` overwrites the KINDS
# literal), and KINDCOL.component was #d946ef — IDENTICAL to view's hardcoded #d946ef. Now #ff8c00 orange.
check('component:"#2f7de1"' in page and 'KINDS[k].col=KINDCOL[k]' in page and 'component:"#d946ef"' not in page,
      "KINDCOL.component is not #2f7de1 — cobalt since 2026-09-05 (it drives the real glyph color; orange read as the module amber, #d946ef is the view)")
# connector wires resolve from a CANONICAL stock palette (not live CONN, which the d2w heat recolors) — the
# built LEGEND.Connectors rows carry it.k not it.c, so the old it.c read rendered every wire gray/solid.
check('var _CONNSTOCK={ fk:{col:"#5893ad"' in page and 'calls:{col:"#f59e0b"' in page and 'access:{col:"#ef4444"' in page and 'function _connCS(it){' in page,
      "the reference connector wires no longer resolve from the _CONNSTOCK canonical palette (would render gray again)")
# REAL 3D asset thumbnails in the reference fleet/ship rows (operator) — replicate thumbBuild + a PAL_CELLS spin
# cell marked __ref so it PRUNES on close (legThumb's LEG_CELLS is shared with the small legend).
check('function _thumbBuild(it){' in page and 'function _refThumb(cv, buildObj, fixedScale){' in page and 'class="lrcv"' in page and 'PAL_CELLS.filter(function(c){ return !c.__ref; })' in page,
      "the reference lost its real 3D ship thumbnails (_thumbBuild/_refThumb/.lrcv) or the __ref prune-on-close")
# the ⓘ opens the reference AND sits right after the "Legend" title (post the upstream shape-icon prefix), an
# inline info dot like the .lgbi row dots — NOT boxed at the far right.
check('Legend</b><button class="lgref"' in page and 'if(window.__uniLegRef) __uniLegRef();' in page,
      "the legend-reference ⓘ is not inline right after the Legend title (moved off the far-right button slot)")
# the ⓘ hugs the title: the title's own margin-right:auto (which shoved it right) is overridden, the tabs own the auto
check('#elegend .lghd b{ flex:0 0 auto !important; margin-right:0 !important; }' in page and '#elegend .lghd .lgtabs{ margin-left:auto !important; }' in page,
      "the ⓘ no longer hugs the Legend title (the title's margin-right:auto is not overridden / the tabs lost the auto)")
# Field/fleet: NON-ship items (Blast/Flak/Star = shock/flak/dot) render the 2D marker shapes, ships/sats the 3D
# thumbnail, via one _refIco dispatcher; the satellite is scaled up; descriptions revised to the FE/BE angle.
check('function _vis2d(it){' in page and 'function _refIco(it){' in page and 'var _REFDESC={ fk:"a foreign-key link' in page and 'pivot.scale.setScalar(fit)' in page and 'fit=(fixedScale!=null)?fixedScale:Math.max(0.2, Math.min(60, 6.4/maxd))' in page and 'it.t==="sat"?2.8:null' in page,
      "the fleet lost its 2D markers / _refIco / _REFDESC / the AUTO-FIT / the satellite's fixed-scale exemption (auto-fit shrinks it)")
# JOURNEY DETAIL overlay (operator): clicking the walk-bar journey NAME opens a full graph-area list of EVERY
# step (kind icon + entity groups); a step row walks the graph to it + closes. Same chrome as the legend ref.
check('window.__uniJrnDetail=function' in page and 'id="uni-jrnref"' in page and '#uni-jrnref{' in page and 'if(window.__uniJrnDetail) __uniJrnDetail();' in page,
      "the journey-detail overlay (__uniJrnDetail) / its #uni-jrnref markup+CSS / the walk-bar name trigger are gone")
check('class="jdstep' in page and 'data-si="' in page and 'WALK.i=i; try{ _walkGo(0); }catch(e){}' in page and 'left:var(--navw); right:0; top:var(--topbarh)' in page,
      "the journey-detail step rows / their walk-to-step click / the full graph-area coverage are gone")
# journey-detail COLUMNS + deterministic DATA semantics (operator): the entity-dot + cluster columns, and a DATA
# block — op badge (from endpoint method / function role) · read/write model TARGETS (reads_from/writes_to/
# fnreads/fnwrites edges) · structure FIELDS (det.cols) · gate CONDITION (evaluates …).
check('function _stepData(n){' in page and 'function _dataHTML(sd){' in page and 'function _groupsHTML(gs){' in page and 'function _grp(id, dir, spec){' in page and 'function _fieldsHTML(sd){' in page and 'class="jdentdot"' in page and 'class="jdenc"' in page and 'class="jdencE"' in page and 'class="jdencC"' in page and 'class="jdopc"' in page and 'class="jdfrom"' in page and 'class="jdto"' in page and 'class="jdrel"' in page and 'op="guards"; opk="gate"; note="evaluates "' in page,
      "the journey-detail merged entity·cluster cell, the OPERATION column, or the RELATION-labelled FROM/TO groups (_grp/_groupsHTML/.jdrel) are gone")
# journey-detail COLUMN HEADER + entity-tinted rows (operator 2026-09-03): the entity is a column, so the per-entity
# group rows are gone; ONE sticky header names every column; each row carries its entity color as --ec.
check('class="jdcols"' in page and '#uni-jrnref .jdcols, #uni-jrnref .jdstep{ display:grid;' in page and 'grid-template-columns:26px 22px 190px 130px 130px 196px 196px;' in page and 'jd-grid' in page and 'class="jdmh"' in page and 'class="jdmx' in page and 'background:var(--panel);' in page and 'padding:0 0 22px' in page and 'class="jdgrp"' not in page and 'class="jdclu"' not in page and 'style="--ec:' in page and 'var(--ec, transparent) 9%' in page and 'function _srcsOf(id, rels){' in page and 'function _feEndpoints(id){' in page,
      "the 7-column GRID (element · entity·cluster · operation · from · to), the FLUSH opaque sticky header, entity-tinted rows, or the incoming-edge resolver are gone; or a retired group-row/standalone-cluster came back")
# journey matrix: operation frozen + transitive call-chain reach (indirect cells) (operator 2026-09-03)
check('TRANSITIVE data reach' in page and '.cell.ind{' in page and 'jdopc{ position:sticky; left:368px' in page and '_HOP={calls:1' in page,
      "the transitive call-chain reach (indirect cells / .cell.ind style) or the operation-column freeze regressed")
# journey matrix KIND FLAGS + diagonal headers + kind icon + no legend (operator 2026-09-03)
check('class="jdflags"' in page and 'class="jdflag' in page and 'data-kd="' in page and 'gabe:universe:jdKinds4' in page and 'data-kd="function"' not in page and 'var _DK={model:1, schema:1, store:1};' in page and 'class="jdmhn"' in page and 'color:var(--mc' in page and 'class="jdmhk"' in page and 'pop.className="jdcolpop"' in page and '.jdcolpop{' in page and 'function _jdColPop(' in page and 'function _jdCellPop(' in page and 'var _COMPOSE={route:1, module:1};' in page and 'var _FANOUT=8;' in page and 'function _jrnRouteAnchor(' in page and 'fe.unshift(_anc)' in page and '.jdstep .jdico::after' in page and 'var _LRDEF={' in page and 'class="lrdef"' in page and 'function _defOf(' in page and 'FE_KIND={ "fe-type":"type", "fe-unknown":"unknown" }' in page and 'KINDS.unknown={' in page and 'GLYPH.unknown=' in page and 'mclass:{api:' in page and '_badgeRow("mclass"' in page and 'mclass:p.mclass||null' in page and 'kind==="mclass"' in page and 'window.GABE_WORKFLOWS_DRAFT' in page and 'function _wfOne(' in page and 'class="jrndraft"' in page and 's.src="./workflows.draft.js"' in page and 'class="jdhl"' in page and '.jdmh.jdcol-hot{' in page and '.jdcols .jdhl{' in page and 'var _OPC={read:' in page and '.jdcolpop .cpsep{' in page and '_snCache' in page and '_HOP={calls:1' in page and 'class="jdmxleg"' not in page,
      "the matrix kind-flags (jdflag/jdKinds persist), diagonal headers (rotate -45), the per-column kind icon (jdmhk), or the legend-removal regressed")
# journey overlay RESIZER (operator 2026-09-03): a left-edge handle drags the panel width, double-click resets.
check('_rz.className="jdrz"' in page and '#uni-jrnref .jdrz{' in page and 'cursor:ew-resize' in page and 'removeItem("gabe:universe:jrnLeft")' in page and 'setItem("gabe:universe:jrnLeft"' in page,
      "the journey-overlay resizer handle (_rz.jdrz / ew-resize / persisted left / double-click reset) is gone")
# fleet-side tier config pills (control-system phase 3)
check('pillHTML("tier"' in page and 'fcPill.className="pill fcpill"' in page and 'entPane.unshift(tierGrp)' in page,
      "the fleet Entity pane's tier + fold + component-class pills are gone")
check('window.__uniKindToggle=function(k)' in page and '__uniKindToggle(rw.dataset.lgk)' in page,
      "the legend rows are no longer hide-by-kind controls")
check('lghd2 lggrp gs-' in page and '{t:"hd",l:"frontend"}' in page and '{t:"hd",l:"backend"}' in page
      and '__uniGroupToggle(hd.dataset.lggrp)' in page,
      "the legend frontend/backend headers are no longer clickable 3-state masters")
check('.lgrow.lgoff{ opacity:.32; }' in page and 'data-lgk=' in page,
      "a hidden kind's legend row no longer dims")

# ── 10y. batch 52: the C SPLIT (paired fe· entities) + the WIRE VIEW R-lab in the config ──
check('FE_PAIR={}' in page and 'if(h.pair) FE_PAIR[h.id]=h.pair;' in page,
      "the fe·X pairing map is gone (nothing would seat a split home beside its backend twin)")
check('lerp(new T.Color("#ffffff"),0.38)' in page,
      "a paired fe entity lost its TINT of the backend twin's colour (the pairing must be visible as family)")
check('E2.push([fh, FE_PAIR[fh], 8]);' in page and 'ord.splice(bi+1,0,fh);' in page,
      "pair seating is gone (force spring + ring adjacency)")
check('(fe?"fe · {name}":"{name}")' in page and 'forms[conv][fe?"fe":"be"]' in page, "the label formatter must fall back to today's opened-dot prefix without a naming block, and read the emitted form with one")
# the R2–R4 lab was RETIRED by the entity-models pass (Phase 2, 2026-09-06): the machinery goes, not just the buttons — an unreachable
# toggle that still gated the connector build was the failure mode. The CAPSULES option followed on 2026-09-07 (dropped); the ENTITY MODEL pill leads the group.
check('window.UNIWIRE' not in page and '__uniRelHide' not in page and '__uniDrawBundles' not in page and '_UTILSET' not in page and '_SOLEP' not in page and '_wireSets' not in page,
      "R2–R4 machinery survived (UNIWIRE / __uniRelHide / __uniDrawBundles / _UTILSET / _SOLEP) — a retired toggle still gates the connector build")
check('data-v="r2"' not in page and '["r2","R2"' not in page and '["r3","R3"' not in page and '["r4","R4"' not in page and 'UNIWIRE[d[0]]' not in page,
      "an R2/R3/R4 button is still built")
check('window.__uniAddWireView=function()' in page and 'id="wireview"' not in page.replace("'",'"') and '>CAPSULES</div>' not in page and '"wv-"+d[0]' not in page and 'id="entmodel"' in page.replace("'",'"')
      and '__uniAddWireView();' in page,
      "the CAPSULES option must be GONE (dropped 2026-09-07) while the ENTITY MODEL pill is built at boot / preset re-tabs")

# ── 10z. batch 52 review fixes (7 confirmed → 6 distinct) ──
check('UNICAP.on=true' not in page and 'UNICAP.on=!UNICAP.on' not in page and 'UNICAP.on = ' not in page,
      "a control still turns capsules on — UNICAP.on has NO writer since the option was dropped (2026-09-07)")
_sg=page[page.find('window.__uniScaleGuard=function()'):page.find('window.__uniApplyDeepLinks=function()')]
check(bool(_sg) and '__uniSetTier(0)' in _sg and '__uniApplyCapsules' not in _sg and 'booted at tier 0' in _sg and 'opens FOLDED' not in page and 'open a planet' not in page,
      "the scale guard must boot an over-budget field at TIER 0 without the capsule fold (and say so — the Sources row's hover text included)")
check('window.__uniCamFit=function(ms)' in page and '__uniCamFit(600); else Graph.cameraPosition(DEF' in page
      and '__uniCamFit(0); }, 400);' in page,
      "the camera no longer fits the live field (19 clusters outgrew the fixed 780) on boot + reset")
check('" (frontend of "+' in page.replace("'",'"'), "a paired piece's card no longer names its backend twin")

# ── 10aa. batch 53: capsules (S1+S3) · areas (S2) · the screen core (S4) · alias/fixture de-noisers ──
check('window.UNICAP={ on:false, threshold:80, open:{} };' in page and 'window.__uniApplyCapsules=function()' in page,
      "capsules DEFAULT OFF (operator: control-driven simplification) — the fold machinery survives dormant, with no control (the option was dropped 2026-09-07)")
check('if(window.__uniSetTier){ try{ __uniSetTier(1); }catch(e){} }' in page,
      "the station BOOTS simplified via the T1 tier (the tier replaces the capsule fold as boot-time simplification)")
check('rel:"bundle"' in page and 'count:g2.n' in page, "capsule wires lost their aggregated bundles")

# ── 10aa. ENTITY MODELS — Phase 2 of docs/design/entity-models/plan.md (2026-09-06): the claim is the join key, the other three are views ──
check(page.count('entClaim:')==3 and 'ent:ent, entClaim:ent,' in page and 'ent:p.home, entClaim:p.home,' in page and 'ent:f.slug, entClaim:f.slug,' in page,
      "B1: the immutable claim is not stamped on exactly the three node literals (backend · frontend · function)")
check('window.__uniClaimEnts=_ents.slice();' in page and page.find('window.__uniClaimEnts=_ents.slice();') < page.find('/* LINKS: intra-entity'),
      "B1: the claim registry is not captured after the FE fold (the claim round trip would drift)")
check('KINDS.element={' in page and 'KINDCOL.element=' in page and 'order.push("element")' in page and '"prompt","element"].forEach' in page
      and '"prompt","element"].filter' in page and 'element:"a backend file' in page and '"prompt","element"];' in page,
      "B1: the element kind lacks its registry / legend row / compact-legend row / tier list / tip")
check('"claimed by "+String(n.entClaim||n.ent||"")' in page and '"home "+_hslug(n.entClaim||n.ent)+" by "+by' in page and '_hslug(n.ent)+" by "' not in page and 'String(n.ent||"").replace(/^fe·/,"")+"\'s config' not in page,
      "R2: the homing-evidence and config-home card rows must join on the CLAIM (n.entClaim), never the view's home")
_sm1=page[page.find('window.__uniSetModel=function(v, opts)'):page.find('window.__uniAddWireView=function()')]
check('pools.push(_FETYPES)' in _sm1 and 'live={}; pools.forEach(function(pool){ pool.forEach(function(n){ if(n&&!n.__cap&&n.ent) live[n.ent]=1; }); });' in _sm1 and 'live={}; nodes.forEach' not in _sm1,
      "R2: the held fe-type pool re-homes and the cluster registry is built over EVERY pool (a function-only cluster must be minted with functions OFF)")
_sm2=page[page.find('window.__uniSetModel=function(v, opts)'):page.find('window.__uniAddWireView=function()')]
check(_sm2.find('window.__uniModel=v;') < _sm2.find('var pools=[nodes]') and _sm2.count('window.__uniModel=v;')==1,
      "R2: the model flag is set BEFORE the re-cluster (buildClusters reads it for the aspect dash)")
check('if(!mem.length) return;' in page[page.find('function buildClusters()'):page.find('function hull(ms, pad)')], "R2: a registered cluster with zero drawn members allocates no hull (no label at the origin)")
check('" unclaimed file(s) in the map"' in page and 'hidden at this tier (drawn from Trace)' in page and 'unclaimed file(s) drawn' not in page, "R2: the elements Sources row says the state (drawn from which tier), not the intent")
check('fnsN:(kind==="element"?_num(p.fns):null)' in page and 'more (the census lists 12)' in page, "R2: the element card names the functions beyond the 12 its det lists")
check('var pc=D.pieces[n.entClaim||n.ent];' in page and 'D.pieces[n.ent];' not in page,
      "B2: the levels group map must join on the CLAIM — a moved piece would lose its use-case / community / fk group and land in 'other'")
_em=page[page.find('if(!document.getElementById("entmodel"))'):page.find('if(!document.getElementById("entnaming"))')]
check(bool(_em) and re.findall(r'\["(\w+)","\w+",', _em)==["claim","seeded","derived","proposed"] and '__uniSetModel(btn.getAttribute("data-v"))' in _em
      and "' disabled'" in _em and 'vw.reason' in _em,
      "B3: the ENTITY MODEL pill is not the four-position claim · seeded · derived · proposed with disabled-with-reason positions")
check(page.find('em.id="entmodel"') < page.find('en.id="entnaming"'), "B3: #entmodel must be built ABOVE #entnaming")
check('ico(MICO[d[0]],13)' in _em and "\">'+d[1]+'</button>'" not in _em and '(d[1]+" — "+d[2])' in _em,
      "B3-icons: the ENTITY MODEL buttons must carry an ICON with the word on hover (operator 2026-09-07), not the word")
check('window.localStorage.setItem("gabe:universe:model", v)' in page and 'window.localStorage.getItem("gabe:universe:model")' in page,
      "B3: the model preference is not persisted / read back (gabe:universe:model)")
_sm=page[page.find('window.__uniSetModel=function(v, opts)'):page.find('/* a naming or mark switch RELABELS')]
check(all(k in _sm for k in ('recomputeEX(CFG.entLayout)','__uniAssignSplit()','recomputeSubAnchors()','__uniApplyCapsules()','Graph.d3ReheatSimulation()','JRN=null','UNICAP.open={}','_FNNODES','_CAPST.nodes','n.ent=H[n.id]||c','n.modelMark=','__uniFleetRender()','applyVis("all")','__uniFreezeForSettle()')),
      "B5: __uniSetModel misses a step of the live re-cluster chain (pools · homes · registry · anchors · capsules · reheat · spans · fleet · panel · vis)")
check('Graph.graphData(' not in _sm and 'n.id=' not in _sm and 'n.col=' not in _sm and 'nodes=[' not in _sm and 'links=' not in _sm and 'NIDS[' not in _sm,
      "B5: __uniSetModel must never touch the node/link arrays, an id, NIDS or a colour (the identity law — a walk's steps are ids)")
check('return false; }' in _sm and 'views[v].present' in _sm and '_ents.length=0;' in _sm and 'claimEnts.slice()' in _sm,
      "B5: an absent/unknown view must return false and stay put; the claim view must restore the registry exactly")
check('window.__model=q.get("model")' in page and 'mv=window.__model' in page, "B6: ?model= is not parsed / applied")
_dl=page[page.find('window.__uniApplyDeepLinks=function()'):page.find('window.UNICAP={')]
check(0 < _dl.find('__uniSetModel(_want,{noStore:true})') < _dl.find('__jrnDone') < _dl.find('__entDone') and 'localStorage.setItem' not in _dl,
      "B6: the model must apply BEFORE ?journey= / ?ent= and never write localStorage from the URL path")
check('function makeCluster(members, color, shape, op, level, label, dash)' in page and page.count('wireframe:!!dash')==2 and '_dash=!!(_mr&&_mr.kind==="aspect")' in page and '{ekey:e, dash:_dash}' in page,
      "B7: an aspect hull has no dashed/stippled rim (sphere + polygon)")
check(page.count('homeEvRow(n), modelRow(n),')==4 and 'function modelRow(n)' in page and 'modelRow(n),\n      accessSec(n),' in page,
      "B8: the model row is not beside every homing-evidence row (endpoint · fe · fe-data · fe-hook) and on the function card")
check('function modelSec(ent)' in page and 'var _ms=modelSec(ent); if(_ms) pb.append(_ms);' in page and 'pchip verdict v-' in page,
      "B8: panelEnt carries no model section / verdict badge")
check('C.element=function(n)' in page and 'sechd("info","Unclaimed file")' in page, "B8: no element card")
check('srcRow("role","entity model"' in page and 'cluster(s) folded at this model' in page and '" atoms anchored"' in page and 'srcRow("info","elements"' in page and 'window.__uniFoldedN=Object.keys(fold).length' in page,
      "B9: the Sources rows (entity model per view · elements · the folded count) are missing")
_ls=page[page.find('function _modelSection()'):page.find('function _planetSection()')]
check(bool(_ls) and '_connSection()+_planetSection()+_modelSection()' in page and len(re.findall(r'\["(claim|seeded|derived|proposed|aspect|layer|element)","', _ls))==7 and 'lrdef' in _ls and 'stroke-dasharray' in _ls,
      "B9: the legend ENTITY MODELS section lacks its seven rows (each with a definition, the aspect swatch dashed)")
# ── 10ab. NAMING (naming-plan Phase 3, 2026-09-06): words from the strategy, the mark from the emitted form; a switch relabels, never re-clusters ──
check(all(k in page for k in ('window.__uniNameOf=function(id)','window.__uniRender=function(form, name)','window.__uniCaseRun=function(run, how)','window.__uniStrategy=function()','window.__uniConvention=function()')),
      "B3-naming: the formatter chain (__uniNameOf · __uniRender · __uniCaseRun · __uniStrategy · __uniConvention) is missing a link")
check('{name|camel}' in page and '{name|pascal}' in page and '/^(.*?)( · | — )(.*)$/' in page, "B3-naming: the case tokens are not substituted on the leading word-run only")
_en=page[page.find('if(!document.getElementById("entnaming"))'):page.find('if(!document.getElementById("entfeconv"))')]
_ec=page[page.find('if(!document.getElementById("entfeconv"))'):page.find('/* ── SELECTED-LINE look SETTLED')]
check(bool(_en) and bool(_ec) and page.find('em.id="entmodel"') < page.find('en.id="entnaming"') < page.find('ec.id="entfeconv"'),
      "B3-naming: #entnaming and #entfeconv must be built under #entmodel, in that order")
check('ico(NICO[k]||"domain",13)' in _en and "+k+'</button>'" not in _en and '_ea2(k+" — "+ti)' in _en
      and 'ico(CICO[k]||"none",13)' in _ec and 'ico("tint",13)' in _ec and '_ea3(k+" — "+ti)' in _ec,
      "B3-icons: the NAMES and FRONTEND MARK buttons must carry ICONS with the word + rule (or the rendered mark) on hover (operator 2026-09-07)")
_ico=page[page.find('var ICO={'):page.find('function ico(g,w)')]
check(bool(_ico) and all((k+":'") in _ico or (k+':GLYPH') in _ico for k in ('claim','seeded','derived','proposed','domain','table','path','action','config','both','prefix','suffix','bracket','tint','none')) and '"class":GLYPH.schema' in _ico and 'glyph:GLYPH.screen' in _ico and '"case":\'' in _ico,
      "B3-icons: the ICO roster is missing a pill icon (claim · seeded · derived · proposed · domain · table · class · path · action · config · both · case · prefix · suffix · bracket · glyph · tint · none)")
check('__uniSetNaming(btn.getAttribute("data-v"))' in _en and "' disabled'" in _en and 'dis[k]' in _en and '__uniSetFeConv(btn.getAttribute("data-v"))' in _ec and '["case","prefix","suffix","bracket","glyph","tint","none"]' in _ec and '__uniRender(f.fe,"my feature")' in _ec,
      "B3-naming: the pills bind their setters, render disabled positions with reasons, and the mark buttons carry their ACTUAL mark (on hover since 2026-09-07)")
_rl=page[page.find('window.__uniRelabel=function()'):page.find('window.__uniSetNaming=function(k, opts)')]
check(bool(_rl) and 'buildClusters()' in _rl and '__uniFleetRender()' in _rl and all(x not in _rl for x in ('recomputeEX','__uniAssignSplit','recomputeSubAnchors','__uniApplyCapsules','d3ReheatSimulation','Graph.graphData(','nodes=','n.ent=','JRN=null')),
      "B3-naming: __uniRelabel must relabel (clusters · fleet · panel) and NEVER re-cluster (the absence list)")
_sn=page[page.find('window.__uniSetNaming=function(k, opts)'):page.find('window.__uniAddWireView=function()')]
check('return false; }' in _sn and 'localStorage.setItem("gabe:universe:naming", k)' in _sn and 'localStorage.setItem("gabe:universe:feconv", k)' in _sn and 'opts.noStore' in _sn,
      "B3-naming: the setters refuse an unknown key (false + one console line) and persist unless noStore")
_dl2=page[page.find('window.__uniApplyDeepLinks=function()'):page.find('window.UNICAP={')]
check(0 < _dl2.find('__uniSetNaming(_wn,{noStore:true,noRender:true})') < _dl2.find('__uniSetModel(_want,{noStore:true})') < _dl2.find('__jrnDone') and 'localStorage.setItem' not in _dl2 and 'window.__naming=q.get("naming"); window.__feconv=q.get("feconv");' in page,
      "B6-naming: ?naming=/?feconv= are assigned BEFORE the model switch, before ?journey=/?ent=, and never stored from the URL")
check('srcRow("info","names"' in page and 'your choice · project default' in page and 'frontend mark: ' in page and '_nb.config_error?("⚠ "' in page, "B9-naming: the Sources names clause (strategy · source · coverage · mark · a config error first) is missing")
check('rows.push(["naming","names: "+k' in page and 'rows.push(["mark","frontend mark: "+c' in page, "B9-naming: the legend NAMES + FRONTEND MARK rows are missing")
check('_lt.slice(0,_nmax-1)+"…"' in page, "the hull sprite must truncate at name_max with an ellipsis (an action phrase runs 100+ chars)")
check('orphan' not in page[page.find('/* ── NAMING (naming-plan.md Phase 3'):page.find('/* LINKS: intra-entity')].lower() and 'orphan' not in _en.lower() and 'orphan' not in _ec.lower(), "R10: a naming string says 'orphan'")
# ── the surfaces review (R2, 2026-09-06): the relabel keeps the reader's panel · one label funnel on the card · escaped sinks · synced pills ──
check('if(pv&&document.body.classList.contains("panel-open")){' in _rl and 'pv.lvl==="clu"&&window.__uniPanelClu' in _rl and 'pv.lvl==="node"&&pv.id&&NIDS[pv.id]' in _rl and 'else if(pv.lvl==="all"&&window.__uniPanelAll) __uniPanelAll(); } }catch(e){}' in _rl,
      "R2-naming: __uniRelabel re-renders only an OPEN panel at its own level (ent · clu · node · all) — never pops the census over a cluster panel or an element card")
check('window.__uniPView={lvl:"node", id:n&&n.id};' in page, "R2-naming: an element card records its level")
_nm=page[page.find('function modelRow(n)'):page.find('function modelSec(ent)')]
check('"fe · "' not in _nm and 'r.name+" · "' not in _nm and '(r&&r.name)?(l+" · "+_hslug(e)):l' in _nm, "R2-naming: modelRow's nm() goes through __uniEntLabel (strategy + mark) with the raw id beside a cluster's name — no hard-coded prefix, no bare r.name")
check('window.__uniSyncNamingPills=function()' in page and page.count('try{ __uniSyncNamingPills(); }catch(e){}')==3 and 'b.classList.toggle("on", !b.disabled&&' in page and 'if(window.__relabelOwed){ window.__relabelOwed=false; if(!_switched){' in page,
      "R2-naming: the setters sync the pills themselves (a deep-linked or stored naming beside a model switch never leaves the pill on the wrong position); a disabled button is never lit")
check("(k===cur&&!off?' class=\"on\"':'')" in page and "(k===cur2&&!off?' class=\"on\"':'')" in page, "R2-naming: a disabled position is never lit at build")
check('window.__uniEsc=function(x)' in page and 'window.__uniEntLabelHTML=function(e)' in page and '__uniEntLabelHTML(e):(window.__uniEntLabel?__uniEntLabel(e):e))+\'</span>' in page and '"<div class=\'ptitle\'><div class=\'pname\'>"+_hx(title)+"</div>"' in page,
      "R2-naming: the fleet row and the panel head escape the label (project prose reaches innerHTML) — the fleet through __uniEntLabelHTML (the glyph mark rides it)")
check('__uniEsc((window.__uniEntLabel?__uniEntLabel(e):e)+" · "+e)' in page, "R2-naming: the fleet tooltip carries the FULL label beside the id (the sprite truncates, the fleet carries)")
check('ico("tint",13)' in page and 'glyph:GLYPH.screen' in page and "none:'<circle" in page and 'ico(CICO[k]||"none",13)' in page and '(k==="tint"&&!off)?(\'<span style="color:\'' in page, "R2-naming: glyph · tint · none buttons read differently (icons: the screen glyph · a tinted palette · the ban circle)")
check('x.kind==="feature"&&x.name&&(k==="domain"||(x.names&&x.names[k]&&x.names[k]!==x.name))' in page and 'ex=_r.name+" → "+(window.__uniEntLabel?__uniEntLabel(_r.id):_r.names[k])' in page, "R2-naming: the legend example shows a row whose name CHANGES, drawn as the hull draws it")
check('+" "+((window.__uniNameOf&&__uniNameOf(e))||"")' in page, "R2-naming: the search scorer keeps the emitter's words as a witness under every convention")
check('"entity · "+(window.__uniEntLabel?__uniEntLabel(ent):_hslug(ent))' in page and '"entity · "+ent,' not in page, "R2-naming/R10: panelClu's Above row goes through the label funnel")
check('orphan' not in page[page.find('/* ── ENTITY MODELS (Phase 2'):page.find('/* ── ONE badge-glyph source')].lower()
      and 'orphan' not in page[page.find('function modelRow(n)'):page.find('function feBuilder(n)')].lower() and 'orphan' not in _ls.lower(),
      "R10: an entity-model string says 'orphan'")
check('try{ rebuildNodes(); }catch(e){}' in page.split('__uniApplyCapsules=function')[1][:5000],
      "the capsule surgery lost its decoration reset (stale FLEETTICK closures threw)")
check('if(n&&n.kind==="capsule"){ if(window.__uniCapExpand) __uniCapExpand(n.ent); return; }' in page,
      "one click on a capsule must EXPAND its entity")
check('if(_CAPST&&_CAPST.byPiece[id])' in page, "goto/search into a folded piece no longer auto-expands")
check('g:"collapsed"' in page and 'opens the capsule' in page,
      "stashed pieces vanished from search (the index must list them and expand on open)")
check('if(window.__uniApplyCapsules) __uniApplyCapsules(); if(window.__uniSetTier){ try{ __uniSetTier(1); }catch(e){} } if(window.__uniScaleGuard){ try{ __uniScaleGuard(); }catch(e){} } if(window.__uniApplyDeepLinks){ try{ __uniApplyDeepLinks(); }catch(e){} } if(window.__uniCamFit) __uniCamFit(0); }, 400);' in page,
      "the boot 400ms settle applies the T1 tier (capsules default off → the tier is the boot-time simplification)")
check('KINDS.capsule={' in page and 'f==="pod"' in page and 'C.capsule=function(n)' in page,
      "the capsule kind lost its form/card")
check('if(mode==="screen"){' in page and 'screen:"Screen — pieces group by the SCREEN' in page,
      "the SCREEN core strategy (S4) is gone")
check('"area": _area_of(path, home)' in open('templates/center/generators/_a3_fe.py').read()
      and 'apiAlias' in open('templates/center/generators/_a3_fe_extract.mjs').read(),
      "the emitter lost areas (S2) or the API-alias flag")
# ── the review-53 fix wave (13 confirmed findings → 10 subjects) ──
check('in alias_cut or (path, ex.get("name") or "") in scaffold_cut' in open('templates/center/generators/_a3_fe.py').read(),
      "review 53[5]: cut exports must never act as edge SOURCES")
check('elif home == "app-shell":' in open('templates/center/generators/_a3_fe.py').read(),
      "review 53[6]: the app-shell area keeps its discriminating first segment")
check('function assignSub(mode){ _assignSubImpl(mode);' in page and 'if(n.__cap) n.sub=n.area||n.sub;' in page,
      "review 53[2]/[10]: the assignSub wrapper must restamp capsule areas")
check(page.count('try{ __uniAssignSplit(); }catch(e){}') >= 1 and 'grpOf' not in page,
      "review 53[11]: capsules fold from FRESH per-side subs (restore → __uniAssignSplit → fold); grpOf deleted")
check('function _fieldNodes()' in page and '_fieldLinks()' in page and '_fieldN(' in page,
      "review 53[0]: the journey machinery reads the WHOLE field (stash included)")
check('function _stashPurge(flag)' in page and page.count('_stashPurge(') == 3,
      "review 53[9]: BOTH toggles purge their pieces from the capsule stash")
check(page.count('__uniApplyCapsules&&_CAPST!==undefined) try{ __uniApplyCapsules(); }catch(e){}') == 2,
      "review 53[1]: toggleFns AND toggleTypes re-fold a collapsed entity")
check("nodes.some(function(n){ return n.__cap&&n.ent===e; })" in page,
      "review 53[3]: the fleet NAME click expands a folded entity")
check('_CAPST) _CAPST.nodes.forEach(function(n){ live[n.ent+"|"+n.sub]=1; });' in page,
      "review 53[4]: fleet overrides survive the fold round-trip")
check('capsule:"a FOLDED area' in page and '" folded"' in page and '__uniPanelAll) try{ __uniPanelAll(); }catch(e){}' in page,
      "review 53[12]: KINDTIP.capsule + the folded annotation + the census refresh")

# ── 11. every remaining {{TOKEN}} is a token the GLOB loop fills on EVERY page (HUB_TITLE/SYNC_AGE are
#        PER_FILE / unused here → deliberately EXCLUDED so an accidental detached is caught, not waved through) ──
SHARED = {"LANG","PROJECT_NAME","HEAD_SHA","REGEN_STAMP","GENERATOR_NAME","ENTITY_COUNT","TESTS_COUNT",
          "SIDEBAR_ENTITIES","SIDEBAR_CODE","SIDEBAR_LEAF","STATUS_PILLS"}
toks = set(re.findall(r'\{\{([A-Z_]+)\}\}', page))
detached = toks - SHARED
check(not detached, "page carries tokens the glob build cannot fill on every page: "+", ".join(sorted(detached)))

# ── 11b. reverse nav symmetry: the station's OWN nav links back to the core sibling stations ──
for href in ('href="index.html"', 'href="codebase-graph.html"', 'href="codebase-archive-lab.html"', 'href="tests.html"'):
    check(href in page, "station nav missing a sibling backlink: "+href)

print(f"  static: {pass_} passed, {fail} failed")
sys.exit(1 if fail else 0)
PY
STATIC=$?

# ── 12. nav consistency: every sibling full-nav page carries the Gabe Universe item ──
MISS=0
for f in index board architecture entity-index docs codebase-archive tests releases codebase-graph ledger codebase-archive-lab feature; do
  grep -q 'href="gabe-universe.html"' "$SHELL_SRC/$f.html" || { echo "  FAIL: $f.html nav missing the Gabe Universe item"; MISS=1; }
done
[ "$MISS" = 0 ] && echo "  nav-consistency: 12/12 sibling pages carry the item"

# ── 13. OPTIONAL headless render proof against the committed example feed ──
EXPAGE="$SHELL_SRC/example/codebase-graph-station/gabe-universe.html"
CHROME=/usr/bin/google-chrome-stable
PWDIR="$REPO/docs/design/graft-adoption/spike/_build/node_modules/playwright-core"
if [ -x "$CHROME" ] && [ -d "$PWDIR" ] && [ -f "$EXPAGE" ]; then
  node - "$EXPAGE" "$PWDIR" <<'JS'
const path=require('path');
const { chromium } = require(process.argv[3]);
(async()=>{
  const b=await chromium.launch({executablePath:'/usr/bin/google-chrome-stable',args:['--use-angle=swiftshader','--no-sandbox','--disable-gpu-sandbox','--disable-dev-shm-usage']});
  const p=await b.newPage({viewport:{width:1100,height:760}});
  const errs=[]; p.on('pageerror',e=>errs.push(e.message)); p.on('console',m=>{if(m.type()==='error')errs.push(m.text());});
  await p.goto('file://'+path.resolve(process.argv[2]));
  await p.waitForFunction('window.__spikeKindsReady===true',{timeout:30000}).catch(()=>{});
  await p.waitForTimeout(1800);
  const r=await p.evaluate(()=>{
    // deterministic pick: an endpoint whose card WILL carry a passing chip + journey faces — robust to
    // the node-array order (which shifted when capsules default off unfolded ~190 pieces).
    const _eps=(typeof nodes!=='undefined'&&nodes)?nodes.filter(n=>n.kind==='endpoint'&&n.det&&n.det.cases&&n.det.cases.length):[];
    const pick=_eps.find(n=>n.det.cases.some(c=>c.state==='pass')&&n.det.test_journeys&&n.det.test_journeys.length)||_eps.find(n=>n.det.cases.some(c=>c.state==='pass'))||_eps[0]||null;
    if(pick) showPanel(pick); const pb=document.getElementById('pbody');
    // CAPTURE the card state NOW — the few ring block below toggles the tier (T3→T1) which re-renders
    // the panel; reading these after that would see a clobbered card (the boot-T1 regression).
    const stPassV=!!(pb&&pb.querySelector('.pchip.st-pass')), faceV=!!(pb&&pb.querySelector('.jfaces .face'));
    const fePresent=!!(window.GABE_C4&&GABE_C4.fe&&GABE_C4.fe.pieces&&GABE_C4.fe.pieces.length);
    const fe={ present:fePresent, feNodes:nodes.filter(n=>n.fe).length, webLeft:nodes.filter(n=>n.kind==='web').length,
      absorbed:window.__uniFeAbsorbed||0, typesHeld:(typeof _FETYPES!=='undefined')?_FETYPES.length:-1, typesDrawn:nodes.filter(n=>n.kind==='type').length,
      feRels:links.filter(l=>l.fe).length, bridge:links.filter(l=>l.rel==='bridge').length, tog:!!document.getElementById('typesTog') };
    // FE write-spine heat (operator D1/D3/D4): a distinct blue→magenta gradient, its OWN toggle default OFF,
    // banding a write wire by its target's fed2w. Prove the toggle BEHAVES, not just that the string exists.
    const wn = nodes.find(n=>n.fe && n.fed2w!=null);
    const few = { band0: !!window.FEBAND && window.FEBAND[0]===0xc026d3, offDefault: window.__uniFED2W===false,
      writeNode: !!wn, flatWhenOff: window.__feD2WBand ? window.__feD2WBand(wn)===null : false };
    if(window.__feD2WBand && wn){ window.__uniFED2W=true;
      few.hotAtWrite = window.__feD2WBand(Object.assign({},wn,{fed2w:0}))===0xc026d3;
      few.coolFar = window.__feD2WBand(Object.assign({},wn,{fed2w:4}))===0x2563eb;
      window.__uniFED2W=false; }
    // the write-spine node RING (D2): a pass exists, default OFF, and toggling it ON draws ring sprites
    // for rendered write-spine nodes then clears them OFF — behaviour, not just a string.
    few.ringDraw = typeof window.__uniDrawWriteRings==='function';
    few.ringOffDefault = window.__uniWriteRing===false;
    if(few.ringDraw){ var _pt=window.__uniTier; if(window.__uniSetTier) window.__uniSetTier(3);   // rings draw only for VISIBLE write-spine nodes — force T3 so the count is boot-tier-independent (boot is now T1)
      window.__uniWriteRing=true; try{ window.__uniDrawWriteRings(); }catch(e){}
      few.ringsDrawn = (window.__uniWriteRingGroup && window.__uniWriteRingGroup.children.length) || 0;
      window.__uniWriteRing=false; try{ window.__uniDrawWriteRings(); }catch(e){}
      few.ringsCleared = (window.__uniWriteRingGroup && window.__uniWriteRingGroup.children.length) || 0;
      if(window.__uniSetTier && _pt!=null) window.__uniSetTier(_pt); }
    // curated workflows (workflows.js): the 8 journeys-review additions loaded, and each new step
    // resolves EXACTLY to an endpoint node (the pre-existing rows use the station's param normalisation
    // and are not asserted here — only the new exact-key rows, so a typo'd new endpoint fails).
    var NEWWF=["Create a recipe","Request a recipe on demand","Generate a weekly plan","Advance a cooking stage","Remove a pantry item","Tune recipe discovery","Update kitchen equipment","Manage / delete my account"];
    var wfAll=window.GABE_WORKFLOWS||[], epSet=new Set(nodes.filter(n=>n.kind==='endpoint').map(n=>n.id));
    var newWf=wfAll.filter(function(x){return NEWWF.indexOf(x.name)>=0;}), newBad=0;
    newWf.forEach(function(x){(x.steps||[]).forEach(function(s){ if(!epSet.has('endpoint:'+s)) newBad++; });});
    var wfInfo={ count:wfAll.length, newFound:newWf.length, newBad:newBad };
    // the previously-cube kinds now build a billboard ICON texture (billTex[k]) — proof, not a string check
    var _iconKinds=["flag","provider","module","web","middleware","prompt"];
    var iconsBuilt=(typeof billTex!=='undefined')?_iconKinds.filter(function(k){ return billTex[k]; }).length:-1;
    // the journey-walker slot is a FIXED-WIDTH reserve (operator): filling the pill must NOT move the tiers.
    var _tsr=document.getElementById('tiersel'), _jp=document.getElementById('jrnpill');
    var _leftEmpty=_tsr?Math.round(_tsr.getBoundingClientRect().left):-1, _wEmpty=_jp?Math.round(_jp.getBoundingClientRect().width):-1;
    if(_jp) _jp.innerHTML='<span class="wname"><b class="wpos">1/48</b><span class="wjname">A very long journey name that should truncate inside the reserved slot</span></span>';
    var _leftFull=_tsr?Math.round(_tsr.getBoundingClientRect().left):-1, _wFull=_jp?Math.round(_jp.getBoundingClientRect().width):-1;
    if(_jp) _jp.innerHTML='';
    var hdr={ moved:Math.abs(_leftEmpty-_leftFull), slotEmpty:_wEmpty, slotFull:_wFull };
    // a user reaches an endpoint THROUGH the frontend — a workflow walk must START at a frontend piece,
    // not the API endpoint, even when the boot tier hides that piece's kind (operator). Run this LAST.
    var jrn=null; try{ var _wi=(window.GABE_WORKFLOWS||[]).findIndex(function(w){ return w.name==='Cook a recipe — the cooking session'; });
      if(_wi>=0 && window.__uniJrnStart){ window.__uniJrnStart('wf:'+_wi);
        var _f0=(typeof WALK!=='undefined'&&WALK.steps.length)?_fnById(WALK.steps[0]):null;
        // the depth slider must NOT flood a walking journey (operator): exact stays, the set doesn't grow.
        var _setBefore=(typeof HL!=='undefined'&&HL.set)?Object.keys(HL.set).length:0, _exBefore=(typeof HL!=='undefined')?HL.exact:null;
        if(window.__uniHLDepth) window.__uniHLDepth(5);
        var _setAfter=(typeof HL!=='undefined'&&HL.set)?Object.keys(HL.set).length:0, _exAfter=(typeof HL!=='undefined')?HL.exact:null;
        // step-number badges: a walking journey overlays each RENDERED step with its sequence number.
        if(window.__uniDrawJourneyNums) __uniDrawJourneyNums();
        var _bn=window.__uniJrnNumGroup?window.__uniJrnNumGroup.children.map(function(s){return s.userData.nid;}):[];
        var _badges=_bn.length, _badgesUnique=((new Set(_bn)).size===_bn.length);   // ONE badge per node — a revisited node must NOT stack (operator)
        if(window.__uniHLClear) __uniHLClear();
        var _badgesCleared=(window.__uniJrnNumGroup&&window.__uniJrnNumGroup.children.length)||0;   // clearing the journey removes them
        jrn={ feLen:(typeof WALK!=='undefined'?WALK.feLen:0), firstKind:_f0?_f0.kind:null,
          depthNoFlood:(_exBefore===true && _exAfter===true && _setAfter<=_setBefore),
          badges:_badges, badgesUnique:_badgesUnique, badgesCleared:_badgesCleared }; } }catch(e){}
    // EXPERTISE LEVELS (operator): the workflows tab is a dev-onboarding ladder. Assert the INVARIANT,
    // not the census (no hardcoded 16): a LEVELED wf is in 1..3, the sum matches the leveled count,
    // one tier pip per leveled row, the lede is visible, and the named tiers group.
    var lvl=null; try{ window.__uniJrnKind='wf'; window.__uniJrnCollapse={}; var _wfj=_jrnCollect().filter(function(j){ return j.wf; });
      var _gh=_jrnGroupsHTML();
      var _byN=function(n){ return _wfj.filter(function(j){ return j.level===n; }).length; };
      var _rowsFull=(_gh.match(/data-jr="wf:/g)||[]).length;
      window.__uniJrnCollapse={"lvl2":1}; var _ghC=_jrnGroupsHTML(); var _rowsColl=(_ghC.match(/data-jr="wf:/g)||[]).length; window.__uniJrnCollapse={};
      lvl={ outOfRange:_wfj.filter(function(j){ return j.level>3 || j.level<0; }).length,     // clamp must keep this 0
            leveled:_wfj.filter(function(j){ return j.level>=1 && j.level<=3; }).length,
            headers:(_gh.match(/data-ge="lvl/g)||[]).length,                                   // distinct tier headers (not the double-counting /jglvl/)
            sumMatches:( _byN(1)+_byN(2)+_byN(3) === _wfj.filter(function(j){ return j.level>=1&&j.level<=3; }).length ),
            pips:(_gh.match(/class="jrnlvl /g)||[]).length,                                     // one per-row tier pip per leveled wf (critic gap)
            hasLede:(_gh.indexOf('jrnlede')>=0),
            collapseIsolates:( (_rowsFull-_rowsColl) === _byN(2) && _rowsColl>0 ),             // collapsing lvl2 drops ONLY lvl2's rows (isolation)
            grouped:(_gh.indexOf('Orientation')>=0 && _gh.indexOf('Core')>=0 && _gh.indexOf('Specialized')>=0) }; }catch(e){}
    // COMMIT journeys: window.GABE_COMMITS → the 'commits' kind; each carries only nodes still on
    // the map, and walking one runs the shared journey walk. (Example seeds a gustify commits.js.)
    var cm=null; try{ window.__uniJrnKind='commit'; window.__uniJrnCollapse={};
      var _cmj=_jrnCollect().filter(function(j){ return j.commit; });
      var _cok = _cmj.every(function(j){ return j.carriers.length>0 && j.carriers.every(function(id){ return !!_fnById(id); }); });
      var _cgh=_jrnGroupsHTML(); var walked=null;
      if(_cmj.length){ window.__uniJrnStart(_cmj[0].cid);
        walked={ mode:(typeof WALK!=='undefined'?WALK.mode:null), steps:(typeof WALK!=='undefined'?WALK.steps.length:0) };
        if(window.__uniHLClear) __uniHLClear(); }
      cm={ n:_cmj.length, carriersOnMap:_cok, tab:_cgh.indexOf('coverage journey')>=0, walked:walked }; }catch(e){ cm={err:String(e)}; }
    // three MIDDLE-SECTION refinements (operator): tier-icon set switch · collapsed entity picker · level info icons
    var ui3=null; try{
      var _t3=function(){ return document.querySelector('#tiersel button[data-tier="3"]'); };
      if(window.__uniRenderTierIcons) window.__uniRenderTierIcons();        // SETTLED: grid everywhere, no switcher
      var _grid=(window.__uniTierIcoSet==="grid"), _gsvg=!!(_t3()&&_t3().querySelector('svg')),   // T3 wears the grid icon (an svg, not a T-label)
          _t0svg=(document.querySelector('#tiersel button[data-tier="0"]')||{}).querySelector&&document.querySelector('#tiersel button[data-tier="0"]').querySelector('svg'),
          _noSwitcher=!document.getElementById('tiericogrp');
      window.__uniJrnKind='wf'; window.__uniJrnEntOpen=false; _jrnPaint(document.getElementById('jrn'));
      var _collapsed=document.querySelectorAll('#jrn .jrnent').length;     // COLLAPSED default → 0 chips
      window.__uniJrnEntOpen=true; _jrnPaint(document.getElementById('jrn'));
      var _expanded=document.querySelectorAll('#jrn .jrnent').length;      // expanded → chips
      window.__uniJrnEntOpen=false; _jrnPaint(document.getElementById('jrn'));
      var _infos=[].map.call(document.querySelectorAll('#jrn .jglvlinfo'), function(i){ return (i.getAttribute('title')||'').indexOf('Classified here:')===0; });
      ui3={ tierGridSettled:(_grid && _gsvg && !!_t0svg && _noSwitcher), entCollapse:(_collapsed===0 && _expanded>0),
            infoIcons:_infos.length, infoHaveVars:_infos.every(Boolean) }; }catch(e){ ui3={err:String(e)}; }
    return { nodes:(typeof nodes!=='undefined'&&nodes)?nodes.length:-1, err:!!document.getElementById('err'),
      cardOpen:document.body.classList.contains('panel-open'),
      stPass:stPassV, face:faceV, fe, few, wfInfo, iconsBuilt, hdr, jrn, lvl, cm, ui3 }; });
  // COMPONENT CLASS representation (operator) — a SEPARATE pass at T3 with a settle wait, since setTier
  // triggers an async node rebuild: view=SCREEN glyph (no badge) · connector/container/leaf/private=cube+badge (all four classes badged).
  await p.evaluate(() => { if (window.__uniSetTier) window.__uniSetTier(3); });
  await p.waitForTimeout(1600);
  const fcb = await p.evaluate(() => {
    const inB = new Set(window.__uniBadges || []);
    const s = (fc) => { const n = nodes.find(x => x.kind==='component' && x.feClass===fc && x.__threeObj); if(!n) return null;
      let tex=null, bdg=false; n.__threeObj.children.forEach(ch => { if(ch.type==='Sprite'){ if(ch.material&&ch.material.map&&tex===null) tex=ch.material.map; if(inB.has(ch)) bdg=true; } });
      return { screen:tex===billTex.screen, comp:tex===billTex.component, badge:bdg }; };
    const v=s('view'), cn=s('connector'), ct=s('container'), pv=s('private'), lf=s('leaf');
    return { view:!!(v&&v.screen&&!v.badge), connector:!!(cn&&cn.comp&&cn.badge), container:!!(ct&&ct.comp&&ct.badge),
             leaf:!!(lf&&lf.comp&&lf.badge), priv:!!(pv&&pv.comp&&pv.badge) };
  }).catch(e => ({ err: String(e) }));
  // FOCUS/TIER regression (operator bug): a CLICK focuses TIGHT (focus-hide at the depth-1 default → a
  // small visible set), and a TIER press CLEARS the click focus (deterministic, no glow-flood carryover).
  await p.evaluate(() => { window.__uniSetTier(3); if(window.__uniHLClear) window.__uniHLClear(); if(window.__uniHLDepth) window.__uniHLDepth(1);   // fresh state: a prior test raised HL.depth — reset to the depth-1 default a real click sees
    var cn=nodes.find(x=>x.kind==='component'&&x.feClass==='container'&&x.__threeObj); if(cn) window.__uniHLSelect(cn); window.__ffOk=!!cn; });
  await p.waitForTimeout(1000);
  const clickFocus = await p.evaluate(() => ({ ok:window.__ffOk, mode:HL.mode, on:HL.on, depth:HL.depth, walk:WALK.mode, vis:nodes.filter(n=>_nodeVisibleFn(n)).length, setN:Object.keys(HL.set).length })).catch(e=>({err:String(e)}));
  await p.evaluate(() => window.__uniSetTier(2));
  await p.waitForTimeout(1000);
  const afterTier = await p.evaluate(() => ({ on:HL.on, walk:WALK.mode, vis:nodes.filter(n=>_nodeVisibleFn(n)).length })).catch(e=>({err:String(e)}));
  // WIRE SELECTION (2026-09-05): a selected wire DRAWS even when its kind beam is 0 (the vanishing rollup) — probed after the layout cached positions
  const wireSel = await p.evaluate(() => { try{ var rl=links.find(function(l){ return (l.rel==='reads_from'||l.rel==='writes_to') && NIDS[lid(l.source)] && NIDS[lid(l.target)] && _npos[lid(l.source)] && _npos[lid(l.target)]; }); if(!rl) return {err:'no positioned rollup wire', npos:Object.keys(_npos).length};
      window.__uniSelCurve=null; __uniSelectLink(rl); var drawn=!!window.__uniSelCurve; var heads=[].map.call(document.querySelectorAll('#pbody .sec .sechd'), function(h){ return h.textContent.trim().slice(0,10); });
      var chips=0; try{ __uniLegRef(); chips=document.querySelectorAll('#uni-legref .lrexl').length; __uniLegRef(); }catch(e){}
      var fkl=links.find(function(l){ return l.rel==='fk' && NIDS[lid(l.source)] && NIDS[lid(l.target)]; }); var key=null; if(fkl){ __uniSelectLink(fkl); key=/key /.test(document.getElementById('pbody').textContent); }
      window.__uniSelLink=null; SEL=null; try{ updateConnectors(); }catch(e){}
      return {drawn:drawn, vis:heads.indexOf('Visibility')>=0, chips:chips, key:key, beam:window.__uniBeam&&window.__uniBeam.rollup}; }catch(e){ return {err:String(e)}; } }).catch(e=>({err:String(e)}));
  console.log('  wireSel '+JSON.stringify(wireSel));
  // PASS 4 (2026-09-06): the scale guard folds an over-budget field; the deep links open one journey / one entity
  const scaleDL = await p.evaluate(() => { try{ var was={on:UNICAP.on, tier:window.__uniTier}; window.__uniBudget=10; var hit=__uniScaleGuard();
      var r={hit:hit, capOn:UNICAP.on, tier:window.__uniTier, row:!!window.__uniBudgetHit};
      window.__uniBudget=1600; UNICAP.on=was.on; try{ __uniApplyCapsules(); }catch(e){} if(window.__uniSetTier) __uniSetTier(was.tier||1); window.__uniBudgetHit=null;
      var j0=(_jrnCollect().filter(function(x){ return x.wf && !x.draft; })[0]||{}); window.__jrn=j0.name||null; window.__jrnDone=false; __uniApplyDeepLinks(); r.jrn=j0.name||null; r.steps=(WALK&&WALK.steps||[]).length; try{ __uniJrnStart(null); }catch(e){}
      window.__ent=(Object.keys(ENT)[0]||null); window.__entDone=false; __uniApplyDeepLinks(); r.ent=(window.__uniPView&&window.__uniPView.lvl)||null; return r; }catch(e){ return {err:String(e)}; } }).catch(e=>({err:String(e)}));
  console.log('  scaleDL '+JSON.stringify(scaleDL));
  // legend pass (2026-09-06) · Step 3: a dispatches wire on the EXAMPLE page (the event bus, 2 wires) draws, its card says DISPATCHES, the reference row carries a real chip
  const dispSel = await p.evaluate(() => { try{ var dl=links.find(function(l){ return l.rel==='dispatches' && NIDS[lid(l.source)] && NIDS[lid(l.target)] && _npos[lid(l.source)] && _npos[lid(l.target)]; }); if(!dl) return {err:'no positioned dispatches wire'};
      window.__uniSelCurve=null; __uniSelectLink(dl); var drawn=!!window.__uniSelCurve; var card=document.getElementById('pbody').textContent; var chip=/dispatches/i.test(card);   // the chip is upper-cased by CSS; the DOM text is the kind name
      var ref=null; try{ __uniLegRef(); var row=[].slice.call(document.querySelectorAll('#uni-legref .lrrow')).find(function(r){ return /^dispatches/.test((r.querySelector('.lrtx')||{}).textContent||''); }); ref=row?(row.querySelector('.lrexl')?'real':(row.querySelector('.lrnone')?'dash':'none')):'norow'; __uniLegRef(); }catch(e){}
      window.__uniSelLink=null; SEL=null; try{ updateConnectors(); }catch(e){} return {drawn:drawn, chip:chip, ref:ref}; }catch(e){ return {err:String(e)}; } }).catch(e=>({err:String(e)}));
  console.log('  dispSel '+JSON.stringify(dispSel));
  // legend pass · Steps 5–6: the stream endpoint wears a SECOND badge slot; a plain endpoint does not; the provider card has a Class section; the reference chips are real / honest dashes; every badge disc clears 30° of its host body
  const legend56 = await p.evaluate(() => { try{
      var st=nodes.find(function(x){ return x.kind==='endpoint' && x.stream && x.__threeObj; }); var pl=nodes.find(function(x){ return x.kind==='endpoint' && !x.stream && x.__threeObj; });
      var slot1=function(n){ return n.__threeObj.children.filter(function(ch){ return ch.type==='Sprite' && ch.__slot===1; }); };
      var s1=st?slot1(st):[]; var others=st?st.__threeObj.children.filter(function(ch){ return ch.type==='Sprite' && ch.__slot!==1; }):[];
      var xs=others.map(function(ch){ return Math.round(ch.position.x*100)/100; }); var apart=s1.length===1 && xs.indexOf(Math.round(s1[0].position.x*100)/100)<0;
      var gm=NIDS['provider:gemini']; var cls=null; if(gm){ SEL={kind:'node',data:gm}; showPanel(gm); var t=document.getElementById('pbody').textContent; cls=/Class/.test(t)&&/llm/.test(t); }
      var ref={}, refBlank=[]; try{ __uniLegRef(); [].slice.call(document.querySelectorAll('#uni-legref .lrrow')).forEach(function(r){ var k=((r.querySelector('.lrtx b')||{}).textContent||'').trim(); if(['llm','embed','vector','agent','infra','http','observability','payments','stream'].indexOf(k)>=0){ ref[k]=(r.querySelector('.lrnone')||r.querySelector('.lrno'))?'dash':(r.querySelector('.lrex')?'real':'none'); if(!((r.querySelector('.lrdef')||{}).textContent||'').trim()) refBlank.push(k); } }); __uniLegRef(); }catch(e){}
      var hue=function(h){ var r=parseInt(h.slice(1,3),16)/255,g=parseInt(h.slice(3,5),16)/255,b=parseInt(h.slice(5,7),16)/255,mx=Math.max(r,g,b),mn=Math.min(r,g,b),d=mx-mn,H=0; if(d){ if(mx===r) H=((g-b)/d)%6; else if(mx===g) H=(b-r)/d+2; else H=(r-g)/d+4; H*=60; if(H<0) H+=360; } return H; };
      var host={method:'endpoint',delivery:'endpoint',role:'function',feclass:'component',mclass:'module',hrole:'hook',pclass:'provider'}; var bad=[], legacy=[]; var sat=function(h){ var r=parseInt(h.slice(1,3),16)/255,g=parseInt(h.slice(3,5),16)/255,b=parseInt(h.slice(5,7),16)/255,mx=Math.max(r,g,b),mn=Math.min(r,g,b); return mx?(mx-mn)/mx:0; };
      Object.keys(host).forEach(function(fam){ var fam_=window.__BADGE_COL[fam]||{}; var body=(KINDS[host[fam]]||{}).col; if(!body) return; Object.keys(fam_).forEach(function(k){ if(sat(fam_[k])<0.25||sat(body)<0.25) return; var d=Math.abs(hue(fam_[k])-hue(body)); d=Math.min(d,360-d); if(d<30){ var own=(fam==='delivery'||fam==='pclass'||(fam==='method'&&k==='TASK')); (own?bad:legacy).push(fam+':'+k+'@'+Math.round(d)); } }); });   // the rule binds the families this pass owns; older pairs are REPORTED (contrastLegacy), a recolour of their own
      return {streamId:st&&st.id, slot1:s1.length, apart:apart, plainSlot1:pl?slot1(pl).length:null, providerClass:cls, ref:ref, refN:Object.keys(ref).length, refBlank:refBlank, contrastBad:bad, contrastLegacy:legacy}; }catch(e){ return {err:String(e)}; } }).catch(e=>({err:String(e)}));
  console.log('  legend56 '+JSON.stringify(legend56));
  // Part C (2026-09-06): the membership evidence renders — stats.homing on the Sources row, home_ev on at least one node, the card's evidence row
  const homingEv = await p.evaluate(() => { try{
      var st=(window.GABE_C4&&window.GABE_C4.stats&&window.GABE_C4.stats.homing)||null; var n=nodes.find(function(x){ return x.homeEv && x.homeEv.verdict!=='agree' && x.__threeObj; });
      var src=null; try{ window.__uniPanelAll(); src=/homing evidence/.test(document.getElementById('pbody').textContent); }catch(e){ src='err:'+e; }
      var evrow=function(t){ var m=t.match(/home .{0,400}?nothing re-homed/); return m?m[0]:''; };   // the evidence row alone — the card's Identity/nav rows carry the raw bucket token by an older choice
      var row=null, clean=null; if(n){ SEL={kind:'node',data:n}; showPanel(n); var t=document.getElementById('pbody').textContent; var r0=evrow(t); row=/evidence only, nothing re-homed/.test(r0) && /MOVE CANDIDATE|SHARED|STAY/.test(r0); clean=!!r0 && !/__unclaimed__|say abstains/.test(r0); }
      var un=nodes.find(function(x){ return x.homeEv && x.ent==='__unclaimed__' && x.__threeObj; }); var unClean=null; if(un){ SEL={kind:'node',data:un}; showPanel(un); var r1=evrow(document.getElementById('pbody').textContent); unClean=/^home unclaimed by/.test(r1) && !/__unclaimed__/.test(r1); }
      return {stats:st?{pieces:st.pieces,move:st.move,shared:st.shared,present:st.present}:null, nodeWithEv:!!n, cardRow:row, clean:clean, unclaimedCard:unClean, sourcesRow:src}; }catch(e){ return {err:String(e)}; } }).catch(e=>({err:String(e)}));
  console.log('  homingEv '+JSON.stringify(homingEv));
  // TIER KEY regression (operator bug): plain 1–4 fired the tier handler AND the fleet-column handler
  // (two listeners, preventDefault can't stop the second) → the same tier rendered differently each
  // press. Tiers now require Alt+Digit1–4; plain digits must NO LONGER move the tier, and Alt+Digit is
  // deterministic (same key → same tier every time).
  const keyReg = await p.evaluate(() => {
    const K=(code,alt)=>document.dispatchEvent(new KeyboardEvent('keydown',{key:code.slice(5),code,altKey:!!alt,bubbles:true}));
    window.__uniSetTier(3); const t0=window.__uniTier;
    K('Digit2',false); const afterPlain=window.__uniTier;          // plain 2 → must NOT change the tier
    K('Digit2',true);  const afterAlt=window.__uniTier;            // Alt+2 → T1
    K('Digit2',true); K('Digit2',true); const afterAltx3=window.__uniTier;  // same key again → still T1 (deterministic)
    K('Digit4',true); const map4=window.__uniTier;                 // Alt+4 → T3
    K('Digit1',true); const map1=window.__uniTier;                 // Alt+1 → T0
    return { t0, afterPlain, afterAlt, afterAltx3, map4, map1 };
  }).catch(e=>({err:String(e)}));
  // LEGEND REFERENCE (Feature B): the ⓘ opens the full graph-area overlay (FE+BE types · badges · example chips ·
  // connectors · planets); an example chip fills the search bar + focuses the node + closes; a flag hides its kind.
  const legRef = await p.evaluate(() => {
    const btn=document.querySelector('#elegend .lgref'); if(!btn) return {err:'no lgref button'};
    window.__uniSetTier(3); const t3ShowTypes=(typeof CFG!=='undefined'&&CFG.showTypes==='on');   // T3 = Everything incl. the 508 fe-types (operator): the type layer wakes
    window.__uniSetTier(1);   // a known tier so the tier-column assertions are deterministic
    btn.click(); const ov=document.getElementById('uni-legref'); if(!ov) return {err:'overlay did not open'};
    const open={ secs:[].filter.call(ov.querySelectorAll('.lrsh'), h=>/FRONTEND|BACKEND/.test(h.textContent)).length,
      chips:ov.querySelectorAll('.lrex').length, badges:ov.querySelectorAll('.lrbc').length, flags:ov.querySelectorAll('.lrflag').length,
      conn:!![].find.call(ov.querySelectorAll('.lrsh'), h=>/CONNECTORS/.test(h.textContent)),
      planet:!![].find.call(ov.querySelectorAll('.lrsh'), h=>/FLEET/.test(h.textContent)),
      viewRow:!![].find.call(ov.querySelectorAll('.lrtx b'), x=>x.textContent==='View') };
    // refinements (operator): PARENT rows (component/endpoint/function) carry NO header example; Type/Entity
    // derive one (held-off → search wakes them); private is a BADGED class now; the "enable ƒ" text is gone.
    const rowOf=(nm)=>[].find.call(ov.querySelectorAll('.lrrow'), r=>((r.querySelector('.lrtx b')||{}).textContent||'')===nm);
    const hasEx=(nm)=>{ const r=rowOf(nm); return !!(r&&r.querySelector('.lrex')); };
    const ref={ compNoEx:!hasEx('Component (FE)'), endpNoEx:!hasEx('API endpoint'), fnNoEx:!hasEx('Function ƒ'),
      typeEx:hasEx('Type'), entityEx:hasEx('Entity (container)'),
      privBadge:!!(rowOf('private')&&rowOf('private').querySelector('.lrbc')),
      noEnableF:!/enable ƒ/.test(ov.innerHTML) };
    // TIER column as DOTS (operator): a row of 4 dots filled where the element is drawn — route(T0)=4 filled,
    // hook(T2)=2 + dim at T1, leaf(T3)=1, type=manual (0 filled). NO duplicate selector in the overlay (header
    // only). connectors/ships read "any". fold count now derives an example.
    const dotsOf=(nm)=>{ const r=rowOf(nm); const cell=r&&r.querySelector('.lrtdots'); if(!cell) return null;
      const filled=[].slice.call(cell.querySelectorAll('circle')).filter(c=>c.getAttribute('fill')==='currentColor').length;
      return { filled, any:cell.classList.contains('lrtany'), man:cell.classList.contains('lrtman'), dim:r.classList.contains('lrdim') }; };
    const foldR=[].find.call(ov.querySelectorAll('.lrrow'), r=>((r.querySelector('.lrtx b')||{}).textContent||'')==='fold count');
    const D=(nm)=>dotsOf(nm)||{};
    const tier={ noOverlaySel:!ov.querySelector('.lrtiersel'), cells:ov.querySelectorAll('.lrtdots').length,
      routeDots:D('Route (screen)').filled, routeDim:D('Route (screen)').dim,
      hookDots:D('Hook (FE)').filled, hookDim:D('Hook (FE)').dim, leafDots:D('leaf').filled,
      typeDots:D('Type').filled, typeHasFlag:!!(rowOf('Type')&&rowOf('Type').querySelector('.lrflag')), t3ShowTypes, anyCells:ov.querySelectorAll('.lrtany').length,
      foldEx:!!(foldR&&foldR.querySelector('.lrex')) };
    // LAYOUT (operator): two 2-col grids (FE|BE · CONN|FLEET) · tier dots are the LAST cell (one right axis) ·
    // connector wires carry DISTINCT semantic colors (not all gray) · component glyph is orange, not view-fuchsia.
    const rowKids=(nm)=>{ const r=rowOf(nm); return r?[].map.call(r.children, c=>c.className.split(' ')[0]):[]; };
    const rk=rowKids('Route (screen)'); const exI=rk.indexOf('lrex'), tI=rk.indexOf('lrtdots');
    const connSec=(()=>{ const h=[].find.call(ov.querySelectorAll('.lrsh'), x=>/CONNECTORS/.test(x.textContent)); return h&&h.closest('.lrsec'); })();
    const fleetSec=(()=>{ const h=[].find.call(ov.querySelectorAll('.lrsh'), x=>/FLEET/.test(x.textContent)); return h&&h.closest('.lrsec'); })();
    const wireCols=connSec?[...new Set([].map.call(connSec.querySelectorAll('.lrico svg path'), p=>p.getAttribute('stroke')))]:[];
    const compRow=rowOf('Component (FE)'); const compStroke=compRow&&compRow.querySelector('.lrico svg')&&compRow.querySelector('.lrico svg').getAttribute('stroke');
    // 3D thumbnails: .lrcv canvases in the fleet/ship rows, each registered as a __ref spin-cell in PAL_CELLS.
    const thumbs=ov.querySelectorAll('.lrcv').length;
    const refCells=(typeof PAL_CELLS!=='undefined')?PAL_CELLS.filter(c=>c.__ref).length:0;
    // the ⓘ sits right after the <b>Legend</b> title, before the tabs (an inline dot, not the far-right slot),
    // and HUGS the title (small gap — the title's margin-right:auto override + the tabs' auto)
    const hd=document.querySelector('#elegend .lghd');
    const kids=hd?[].slice.call(hd.children):[];
    const bi=kids.findIndex(c=>c.tagName==='B'), ri=kids.findIndex(c=>c.classList&&c.classList.contains('lgref')), tabi=kids.findIndex(c=>c.classList&&c.classList.contains('lgtabs'));
    const _b=hd&&hd.querySelector('b'), _ref=hd&&hd.querySelector('.lgref');
    const iconHug=(_b&&_ref)?(_ref.getBoundingClientRect().left-(_b.getBoundingClientRect().left+_b.getBoundingClientRect().width)):999;
    // FLEET: a NON-ship Field item (Star = a dot) renders a 2D marker (a div), not a canvas; a ship/sat renders a
    // canvas. Descriptions revised to the FE/BE angle (fk → "a foreign-key link…").
    const fRow=(nm)=>fleetSec?[].find.call(fleetSec.querySelectorAll('.lrrow'), r=>((r.querySelector('.lrtx b')||{}).textContent||'')===nm):null;
    const starRow=fRow('Star'), satRow=fRow('Satellites');
    const fkRow=connSec?[].find.call(connSec.querySelectorAll('.lrrow'), r=>((r.querySelector('.lrtx b')||{}).textContent||'')==='fk'):null;
    const layout={ grids:ov.querySelectorAll('.lrcols').length, tierLast:(tI>exI && exI>=0),
      connFleetSameGrid:!!(connSec&&fleetSec&&connSec.parentElement===fleetSec.parentElement&&connSec.parentElement.classList.contains('lrcols')),
      wireUniq:wireCols.length, wireNotAllGray:wireCols.some(c=>c&&c.toLowerCase()!=='#8590a8'), compCobalt:compStroke==='#2f7de1',
      thumbs, refCells, hdrRefAfterTitle:(ri===bi+1 && ri>=0 && ri<tabi), iconHug:Math.round(iconHug),
      starIs2d:!!(starRow&&starRow.querySelector('.lrico > div')&&!starRow.querySelector('.lrcv')),
      satIsThumb:!!(satRow&&satRow.querySelector('.lrcv')),
      fkDescRevised:!!(fkRow&&/foreign-key link/.test((fkRow.querySelector('.lrtx i')||{}).textContent||'')) };
    const chip=ov.querySelector('.lrex'); const s=chip&&chip.getAttribute('data-s'); if(chip) chip.click();
    const jump={ closed:!document.getElementById('uni-legref'), barVal:(document.getElementById('tsin')||{}).value,
      hlOn:(typeof HL!=='undefined'&&HL.on), hlMode:(typeof HL!=='undefined'&&HL.mode), s:s };
    document.querySelector('#elegend .lgref').click();   // re-open
    const ov2=document.getElementById('uni-legref'); const f=ov2&&ov2.querySelector('.lrflag[data-flagk="endpoint"]');
    const before=(window.__uniKindState||{}).endpoint; if(f) f.click(); const after=(window.__uniKindState||{}).endpoint;
    const ov3=document.getElementById('uni-legref'); if(ov3) window.__uniLegRef();   // close so it never bleeds into later checks
    return { open, ref, tier, layout, jump, flag:{ before, after, rebuilt:!!ov3 } };
  }).catch(e=>({err:String(e)}));
  // JOURNEY DETAIL (operator): start a journey, click the walk-bar name pill → a full graph-area overlay lists
  // every step with its kind icon + entity grouping; a step row walks the graph to it + closes.
  const jrnDetail = await p.evaluate(() => {
    const js=(typeof _jrnCollect==='function')?_jrnCollect():[]; if(!js.length) return {err:'no journeys'};
    window.__uniJrnStart(js[0].cid); const nsteps=WALK.steps.length;
    const wn=document.querySelector('#jrnpill .wname'); const clickable=!!(wn&&wn.onclick); if(wn) wn.onclick();
    const ov=document.getElementById('uni-jrnref'); if(!ov) return {err:'overlay did not open', clickable};
    const steps=ov.querySelectorAll('.jdstep').length, groups=ov.querySelectorAll('.jdgrp').length, icons=ov.querySelectorAll('.jdico svg').length;
    const cols=ov.querySelectorAll('.jdcols').length, colsSticky=(cols&&getComputedStyle(ov.querySelector('.jdcols')).position==='sticky');
    const tinted=[].slice.call(ov.querySelectorAll('.jdstep')).filter(x=>/--ec:/.test(x.getAttribute('style')||'')).length;
    // columns (operator): every step has the entity dot + cluster column; the DATA block derives op badges,
    // read/write model targets, structure fields, and gate conditions — all deterministic.
    const all=[].slice.call(ov.querySelectorAll('.jdstep'));
    const entDots=all.filter(x=>x.querySelector('.jdenc .jdentdot')).length, clus=all.filter(x=>x.querySelector('.jdencC')).length;
    const rels=all.reduce((a,x)=>a+x.querySelectorAll('.jdfrom .jdrel, .jdto .jdrel').length,0);
    const ops=all.filter(x=>x.querySelector('.jdop')).length, tgts=all.filter(x=>x.querySelector('.jdtgt')).length;
    const fields=all.filter(x=>x.querySelector('.jdfields')).length, gates=all.filter(x=>x.querySelector('.jdop-gate')).length;
    const opcs=all.filter(x=>x.querySelector('.jdopc .jdop')).length, flows=all.filter(x=>x.querySelector('.jdfrom')&&x.querySelector('.jdto')).length,
          fromTo=all.filter(x=>x.querySelectorAll('.jdfrom .jdtgt, .jdto .jdtgt').length>0).length;
    const bd=ov.querySelector('.jdbody'); const noHOverflow=!(bd.scrollWidth>bd.clientWidth+1);
    // FLUSH header (operator): body has no top padding, so the sticky header's top edge meets the body's top —
    // scrolled rows cannot show through above it. Assert the pixel gap is ~0.
    const hcell=ov.querySelector('.jdcols'), flush=(bd.getBoundingClientRect().top - hcell.getBoundingClientRect().top) < 1.5;
    // GRID ALIGNMENT (operator): a header column and its row column must share the SAME left edge (flex drifted).
    const hc=[].slice.call(ov.querySelectorAll('.jdcols>*')).slice(0,7).map(e=>Math.round(e.getBoundingClientRect().left));
    const r0=all[0], rc=[r0.querySelector('.jdnum'),r0.querySelector('.jdico'),r0.querySelector('.jdmain'),r0.querySelector('.jdenc'),r0.querySelector('.jdopc'),r0.querySelector('.jdfrom'),r0.querySelector('.jdto')].map(e=>e?Math.round(e.getBoundingClientRect().left):-1);
    const aligned=hc.length===rc.length && hc.every((x,k)=>Math.abs(x-rc[k])<=1);
    const rz=ov.querySelector('.jdrz'), defL=Math.round(ov.getBoundingClientRect().left);
    let dragL=defL, resetL=defL;
    if(rz){ rz.dispatchEvent(new MouseEvent('mousedown',{bubbles:true,clientX:rz.getBoundingClientRect().left+2,clientY:400}));
      document.dispatchEvent(new MouseEvent('mousemove',{bubbles:true,clientX:rz.getBoundingClientRect().left+320,clientY:400}));
      document.dispatchEvent(new MouseEvent('mouseup',{bubbles:true})); dragL=Math.round(ov.getBoundingClientRect().left);
      rz.dispatchEvent(new MouseEvent('dblclick',{bubbles:true})); resetL=Math.round(ov.getBoundingClientRect().left); }
    const resizeOk=!!rz && dragL>defL+200 && Math.abs(resetL-defL)<=2;
    // DATA-LINEAGE MATRIX: data-structure columns, filled role cells, horizontally scrollable (operator 2026-09-03)
    const mh=ov.querySelectorAll('.jdmh').length, mxCells=ov.querySelectorAll('.jdstep .jdmx').length, filled=ov.querySelectorAll('.jdmx .cell').length;
    // KIND FLAGS: chips present, model ON by default only, each column carries a kind icon, toggling widens the matrix
    const flagKinds=[].slice.call(ov.querySelectorAll('.jdflag')).map(x=>x.getAttribute('data-kd'));
    const flagN=flagKinds.length, flagsOn=[].slice.call(ov.querySelectorAll('.jdflag.on')).length;
    const mhk=ov.querySelectorAll('.jdmhk svg').length, noLegend=ov.querySelectorAll('.jdmxleg').length===0;
    const colored=[].slice.call(ov.querySelectorAll('.jdmh')).filter(x=>/--mc:/.test(x.getAttribute('style')||'')).length;
    const step0cells=(all[0]?all[0].querySelectorAll('.jdmx .cell').length:0);   // a FE component step now shows its from/to on the right
    // FROZEN through operation (operator): scroll right, the operation column stays put
    const _bd=ov.querySelector('.jdbody');
    const _op0=Math.round(all[0].querySelector('.jdopc').getBoundingClientRect().left); _bd.scrollLeft=500;
    const _op1=Math.round(all[0].querySelector('.jdopc').getBoundingClientRect().left); _bd.scrollLeft=0;
    const opcFrozen=Math.abs(_op0-_op1)<60;
    const indirect=ov.querySelectorAll('.jdmx .cell.ind').length;   // call-chain (transitive) data reach fills orchestration steps
    const _mhBefore=mh; const _fon=ov.querySelector('.jdflag.on'); if(_fon) _fon.onclick();   // toggle one OFF → columns shrink
    const mhAfter=ov.querySelectorAll('.jdmh').length;
    const anyRowCells = all.some(r=>r.querySelector('.jdmx .cell'));
    const flagsOk = flagN>0 && flagsOn===flagN && flagKinds.indexOf('function')<0 && mhk===_mhBefore && colored===_mhBefore && noLegend && mhAfter<_mhBefore && anyRowCells;
    if(_fon) _fon.onclick();   // restore
    const bd2=ov.querySelector('.jdbody'); const scrollableX=bd2.scrollWidth>bd2.clientWidth+2;
    const matrixOk = mh>0 && mxCells===mh*all.length && filled>0 && scrollableX;
    // frozen identity: the element column stays put when scrolled right
    const _fz0=Math.round(all[0].querySelector('.jdmain').getBoundingClientRect().left); bd2.scrollLeft=300;
    const _fz1=Math.round(all[0].querySelector('.jdmain').getBoundingClientRect().left); bd2.scrollLeft=0;
    const frozenOk = Math.abs(_fz0-_fz1) < 40;   // sticky-left: moves only a few px while content scrolls 300 (non-frozen would move ~300)
    // WALK SYNC: row-click keeps the overlay OPEN + moves the walk; jump to a data-touching step lights its columns
    const dataRow=all.find(r=>r.querySelector('.jdmx .cell')); const dsi=dataRow?+dataRow.getAttribute('data-si'):-1;
    if(dataRow) dataRow.onclick();
    const stillOpen=!!document.getElementById('uni-jrnref'), walkI=WALK.i;
    const hotHdr=document.querySelectorAll('#uni-jrnref .jdmh.jdcol-hot').length, hotCells=document.querySelectorAll('#uni-jrnref .jdmx.jdcol-hot').length;
    const walkSyncOk = stillOpen && walkI===dsi && hotHdr>0 && hotCells>0;
    if(document.getElementById('uni-jrnref')) window.__uniJrnDetail();
    return { clickable, nsteps, steps, groups, icons, stepsMatch:(steps===nsteps),
      entDots, clus, ops, tgts, fields, gates, cols, colsSticky, tinted, opcs, flows, fromTo, flush, aligned, rels, resizeOk,
      mh, filled, matrixOk, frozenOk, walkSyncOk, flagsOk, opcFrozen, indirect };
  }).catch(e=>({err:String(e)}));
  // STORE VISIBILITY (operator 2026-09-03): a FRESH viewer (empty localStorage — a private window) opening a
  // store-touching journey MUST see the store flag ON, store columns, and lit store cells. Also: header info
  // icons INLINE with their label · a selected step highlights column TITLES, never tints the column cells.
  const storeCheck = await p.evaluate(() => {
    // simulate a FRESH viewer (private window): clear the accumulated flag cache + tier state the prior evals left
    try{ if(window.__uniSetTier) window.__uniSetTier(3); if(window.__uniHLClear) window.__uniHLClear(); }catch(e){}
    try{ delete window.__uniJdKinds; localStorage.removeItem('gabe:universe:jdKinds4'); }catch(e){}
    const js=(typeof _jrnCollect==='function')?_jrnCollect():[];
    const j=js.find(x=>/Look for recipes/i.test(x.name||''))||js[0]; if(!j) return {err:'no journey'};
    window.__uniJrnStart(j.cid); const wn=document.querySelector('#jrnpill .wname'); if(wn&&wn.onclick) wn.onclick();
    const ov=document.getElementById('uni-jrnref'); if(!ov) return {err:'no overlay'};
    const kindOf={}; (typeof nodes!=='undefined'?nodes:[]).forEach(n=>{ if(!(n.label in kindOf)) kindOf[n.label]=n.kind; });
    const cols=[].slice.call(ov.querySelectorAll('.jdmh')).map(x=>x.getAttribute('data-col'));
    const storeCols=cols.filter(c=>kindOf[c]==='store').length;
    const flags=[].slice.call(ov.querySelectorAll('.jdflag')).map(x=>({kd:x.getAttribute('data-kd'),on:x.classList.contains('on')}));
    const sf=flags.find(f=>f.kd==='store'); const storeFlagOn=!!(sf&&sf.on);
    let litStore=0; [].forEach.call(ov.querySelectorAll('.jdstep .jdmx:not(.empty)'),m=>{ if(kindOf[m.getAttribute('data-col')]==='store') litStore++; });
    const hl=ov.querySelector('.jdcols .jdmain .jdhl'), info=hl&&hl.querySelector('.jdinfo');
    const iconInline=!!(hl&&info)&&Math.abs(hl.getBoundingClientRect().top-info.getBoundingClientRect().top)<10;
    const drow=[].slice.call(ov.querySelectorAll('.jdstep')).find(r=>r.querySelector('.jdmx .cell')); if(drow) drow.onclick();
    const hh=document.querySelector('#uni-jrnref .jdmh.jdcol-hot'), hc=document.querySelector('#uni-jrnref .jdmx.jdcol-hot');
    const titleHot=!!hh && getComputedStyle(hh).backgroundColor!=='rgba(0, 0, 0, 0)';
    const cellClean=!hc || getComputedStyle(hc).backgroundColor==='rgba(0, 0, 0, 0)';
    const r0=ov.querySelector('.jdstep[data-si="0"]'); const row0Lit=r0?r0.querySelectorAll('.jdmx .cell').length:-1;   // DE-FLOOD: a composition root lights only what IT touches (was 83 of 85)
    if(document.getElementById('uni-jrnref')) window.__uniJrnDetail();
    const j2=js.find(x=>/Initial setup/i.test(x.name||'')); let anchorKind=null; if(j2){ window.__uniJrnStart(j2.cid); const n0=NIDS[WALK.steps[0]]; anchorKind=n0?n0.kind:null; }
    // a leg whose screen is reached only through a render-fn MODULE (fecall) still opens on the ROUTE above it (operator 2026-09-05: the photos journey opened on renderCookingFlowView)
    // every legend ⓘ opens its key without throwing (operator 2026-09-05: the Module ⓘ threw keys.forEach — a stray string branch in __badgePop's key ternary); mclass lists its SIX classes
    const lgbiOk=(function(){ try{ var bs=[].slice.call(document.querySelectorAll('.lgbi[data-badgeinfo]')); var kinds=bs.map(function(b){ return b.dataset.badgeinfo; }); var ok=kinds.indexOf('mclass')>=0 && kinds.indexOf('feclass')>=0;
      bs.forEach(function(b){ window.__badgePop(b, b.dataset.badgeinfo); var n=document.querySelectorAll('#badgepop .bprow').length; if(b.dataset.badgeinfo==='mclass' && n!==6) ok=false; if(b.dataset.badgeinfo==='pclass' && n!==8) ok=false; if(n<1) ok=false; window.__badgePopHide(); }); return ok; }catch(e){ return 'ERR:'+e; } })();
    // D3: the FE leg of POST /pantry/items starts at useCreatePantryItem (the hook that fetched), not at whichever hook its 16-hook file mapped to
    const hookRoles=(function(){ try{ var ns=Object.values(NIDS).filter(function(n){ return n.kind==='hook'; }); var withRole=ns.filter(function(n){ return n.hrole; }).length; var kinds={}; ns.forEach(function(n){ if(n.hrole) kinds[n.hrole]=(kinds[n.hrole]||0)+1; }); return {hooks:ns.length, withRole:withRole, kinds:Object.keys(kinds).length}; }catch(e){ return {err:String(e)}; } })();
    const storeShape=(function(){ try{ var ss=Object.values(NIDS).filter(function(n){ return n.kind==='store'; }); return {stores:ss.length, shaped:ss.filter(function(n){ return n.det&&n.det.cols&&n.det.cols.length; }).length}; }catch(e){ return {err:String(e)}; } })();
    const cardOrder=(function(){ try{ var st=Object.values(NIDS).find(function(n){ return n.kind==='store' && n.det && n.det.cols && n.det.cols.length; }); if(!st) return {err:'no shaped store'}; showPanel(st);
      var heads=[].map.call(document.querySelectorAll('#pbody .sec .sechd'), function(h){ return h.textContent.replace(/\s+/g,' ').trim().slice(0,12); });
      var md=Object.values(NIDS).find(function(n){ return n.kind==='model' && n.det && n.det.cols && n.det.cols.length; }); var mheads=[]; if(md){ showPanel(md); mheads=[].map.call(document.querySelectorAll('#pbody .sec .sechd'), function(h){ return h.textContent.replace(/\s+/g,' ').trim().slice(0,12); }); }
      var br=links.find(function(l){ return l.rel==='bridge' && NIDS[lid(l.target)] && NIDS[lid(l.target)].kind==='endpoint'; }); var carries=null; if(br){ showLinkPanel(br); carries=[].map.call(document.querySelectorAll('#pbody .sec .sechd'), function(h){ return h.textContent; }).some(function(t){ return /Carries/.test(t); }); }
      var ref=null; try{ __uniLegRef(); var secs=[].slice.call(document.querySelectorAll('#uni-legref .lrsec')); var cs=secs.find(function(x){ return /CONNECTORS/.test((x.querySelector('.lrsh')||{}).textContent||''); }); var rows=[].slice.call(cs.querySelectorAll('.lrrow')); ref={rows:rows.length, blank:rows.filter(function(r){ return !((r.querySelector('.lrtx')||{}).textContent||'').trim(); }).length, fe:rows.some(function(r){ return /^renders/.test(((r.querySelector('.lrtx')||{}).textContent||'').trim()); })}; __uniLegRef(); }catch(e){ ref={err:String(e)}; }
      return {store:heads.slice(0,3), model:mheads.slice(0,3), carries:carries, ref:ref}; }catch(e){ return {err:String(e)}; } })();
    let feStart=null; try{ var _lg=_jrnFeLeg(['endpoint:POST /pantry/items']); feStart=(_lg.screens||[]).map(function(id){ return String(id).split('#').pop(); }).join('|'); }catch(e){ feStart='ERR:'+e; }
    const j3=js.find(x=>/cooking sessions — photos/.test(x.name||'')); let anchorKind3=null; if(j3){ window.__uniJrnStart(j3.cid); const n3=NIDS[WALK.steps[0]]; anchorKind3=n3?n3.kind:null; }   // JOURNEY STARTS AT A VIEW: the route leads when one is in reach
    // DRAFT workflows (curate-workflows, 2026-09-04 · placement 2026-09-05): the example lands workflows.draft.js → each draft sits IN ITS TIER section (level 1–3, named), draft:true, WALKABLE
    const drafts=js.filter(x=>x.draft); let draftWalk=0; if(drafts.length){ window.__uniJrnStart(drafts[0].cid); draftWalk=WALK.steps.length; }
    const draftGrp=(function(){ try{ window.__uniJrnKind='wf'; var h=_jrnGroupsHTML(); return !/drafts — review/.test(h) && /jrndraft/.test(h); }catch(e){ return false; } })();   // drafts render (chip present) inside the tier ladder, never in a bucket of their own
    // VIEW display kind (operator 2026-09-04): a component with feClass "view" prints "View (FE)" in the view colour on the panel head — the legend's View example landed on an orange COMPONENT card before
    const vn=Object.values(NIDS).find(x=>x&&x.kind==='component'&&x.feClass==='view'); let viewType=null, viewCol=null, viewIcon=null;
    if(vn){ try{ showPanel(vn); viewType=((document.querySelector('#phead .ptype span')||{}).textContent)||null; viewCol=_dispK(vn).col; viewIcon=(ENC.color==='heat')?'heat':iconCol(vn); }catch(e){ viewType='ERR:'+e; } }
    return { journey:j.name, storeCols, storeFlagOn, litStore, iconInline, titleHot, cellClean, row0Lit, anchorKind, anchorKind3, lgbiOk, feStart, hookRoles, storeShape, cardOrder, drafts:drafts.length, draftWalk, draftGrp, draftLeveled:drafts.every(x=>x.level>=1&&x.level<=3), draftNamed:drafts.every(x=>/^(Look at|Add|Edit|Remove|Manage) /.test(x.name||'')), viewType, viewCol, viewIcon };
  }).catch(e=>({err:String(e)}));
  // ── ENTITY MODELS (Phase 2): the live switch on the example feed — identity (arrays + ids untouched), the feed's moved count, the
  //    registry gains each named cluster, an abstained piece keeps its claim, 'other' does not rise (B2), a walk survives, the aspect hull
  //    is dashed, the entity card shows a verdict on proposed, the claim round trip is element-wise equal (THE mutation proof), and a feed
  //    without the block returns false and stays on claim. Runs LAST so the walk it starts disturbs no earlier probe.
  const modelSw = await p.evaluate(() => { try{
      var M=window.GABE_C4&&GABE_C4.models; if(!M||!M.views) return {err:'no models block on the example feed — regen the example (regen-example.sh)'};
      var before={}; nodes.forEach(function(n){ before[n.id]=n.ent; }); var ids=nodes.map(function(n){ return n.id; }), n0=nodes.length, l0=links.length;   // keyed by id — a walk may load the function layer into `nodes` between the switches
      var other=function(){ return nodes.filter(function(n){ return !n.__cap && n.sub==='other'; }).length; }, o0=other();
      var r={n0:n0, views:Object.keys(M.views).filter(function(k){ return M.views[k].present; })};
      r.seeded=__uniSetModel('seeded'); r.sameN=(nodes.length===n0 && links.length===l0); r.idsOk=ids.every(function(id,i){ return nodes[i]&&nodes[i].id===id&&NIDS[id]===nodes[i]; });
      var st=window.__uniModelStats; r.moved=st.moved; r.feedMoved=M.views.seeded.moved; r.movedOk=(st.moved===M.views.seeded.moved);
      var LVM=(window.GABE_LEVELS&&GABE_LEVELS.models)||{}; var feedN=function(map,v){ var a=((M[map]||{})[v]||[]), b=(((LVM[map]||{})[v])||[]); return a.length+b.length; };
      r.heldOk=(st.held===feedN('held','seeded')); r.abstainN=(st.abstained===feedN('abstain','seeded')); r.feedHeld=feedN('held','seeded'); r.stHeld=st.held;   // the live tally vs the FEED, both halves (review: a count asserted against itself proves nothing)
      var newC=_ents.filter(function(e){ return __uniClaimEnts.indexOf(e)<0; }); r.newClusters=newC.length; r.regOk=newC.every(function(e){ return !!ENT[e] && !!UNIVIS.ent[e]; });
      var ab=nodes.find(function(n){ return n.modelMark==='abstain'; }); r.abstainOk=(!ab || ab.ent===ab.entClaim); r.o0=o0; r.o1=other(); r.otherOk=(other()<=o0);
      r.pill=[].map.call(document.querySelectorAll('.pill[data-grp="entmodel"] button'), function(b){ return b.getAttribute('data-v')+(b.classList.contains('on')?'*':'')+(b.disabled?'-':''); }).join(' ');
      try{ __uniPanelAll(); var pt0=document.getElementById('pbody').textContent; r.srcRow=/entity model/.test(pt0) && (new RegExp('seeded · '+st.moved+' moved · '+st.abstained+' abstained · '+st.held+' held')).test(pt0); }catch(e){ r.srcRow='err:'+e; }
      var mv=nodes.find(function(n){ return n.modelMark==='moved'; })||(_FNNODES||[]).find(function(n){ return n.modelMark==='moved'; }); if(mv){ SEL={kind:'node',data:mv}; showPanel(mv); var _pt=document.getElementById('pbody').textContent; r.cardRow=/seeded: claim .+ → .+ nothing re-homed on disk/.test(_pt);
        var _hs=function(x){ return x==='__unclaimed__'?'unclaimed':String(x||'').replace(/^fe·/,''); }; var _ev=(_pt.match(/home (\S+) by /)||[])[1]; r.evClaim=_ev?(_ev===_hs(mv.entClaim)):null; }   // the evidence row names the CLAIM slug, not the view's destination (review)
      // a function-only cluster registers with functions OFF (the default resting state): derived from claim with the fn layer hidden
      r.claim0=__uniSetModel('claim'); var _fnWasOn=(typeof _fnsOn!=='undefined'&&_fnsOn); if(_fnWasOn){ try{ toggleFns(false); }catch(e){} }
      r.derivedOff=__uniSetModel('derived'); r.aspectReg=(_ents.indexOf('a:get_auth_context')>=0 && !!ENT['a:get_auth_context'] && !!UNIVIS.ent['a:get_auth_context']); r.noEmptyHull=!CLUSTERS.some(function(c){ return c.level==='ent' && !c.members.length; });
      try{ toggleFns(true); }catch(e){} r.aspectHullAfterLoad=!!CLUSTERS.find(function(c){ return c.level==='ent' && c.ekey==='a:get_auth_context' && c.dash; });
      r.newClustersFeed=(_ents.filter(function(e){ return __uniClaimEnts.indexOf(e)<0; }).length===M.views.derived.new_clusters); r.newClustersN=[_ents.filter(function(e){ return __uniClaimEnts.indexOf(e)<0; }).length, M.views.derived.new_clusters];
      __uniSetModel('seeded');
      var j=_jrnCollect()[0]; if(j){ __uniJrnStart(j.cid); } var steps=(WALK.steps||[]).slice(), wi=WALK.i;
      r.derived=__uniSetModel('derived'); r.walkOk=((WALK.steps||[]).join('|')===steps.join('|') && WALK.i===wi && _jrnCollect().length>0);
      var asp=CLUSTERS.find(function(c){ return c.level==='ent' && /^a:/.test(c.ekey||''); }); r.aspect=asp?{ekey:asp.ekey, dash:!!asp.dash}:null;
      var d=_ents.find(function(e){ return /^d:/.test(e); }); if(d){ __uniPanelEnt(d); r.entCard=/Entity model · derived/.test(document.getElementById('pbody').textContent); }
      r.proposed=__uniSetModel('proposed'); var slug=(M.rosters.proposed||[]).filter(function(x){ return x.verdict && _ents.indexOf(x.slug)>=0; })[0]; if(slug){ __uniPanelEnt(slug.slug); r.badge=((document.querySelector('#pbody .pchip.verdict')||{}).textContent)||null; }   // the chip itself — textContent concatenates words, so a \b regex never matches
      try{ var NB=window.__uniNamingBlock&&__uniNamingBlock(); if(NB){ var L=function(){ return _ents.map(function(e){ return __uniEntLabel(e); }); }, E=function(){ return nodes.map(function(n){ return n.ent; }).join('|')+'#'+CLUSTERS.map(function(c){ return c.ekey+'/'+c.skey; }).join('|'); };
        var l0=L(), e0=E(), st0=(WALK.steps||[]).join('|'); r.nmDefault=[__uniStrategy(), __uniConvention()];
        var alt=(NB.positions||[]).filter(function(k){ return k!=='domain' && !(NB.disabled||{})[k] && (NB.coverage||{})[k]>0; })[0]||null; r.nmAlt=alt;
        r.nmSwitch=alt?__uniSetNaming(alt,{noStore:true}):null; var l1=L(); r.nmRelabelOnly=(E()===e0) && (WALK.steps||[]).join('|')===st0; r.nmChanged=l1.some(function(x,i){ return x!==l0[i]; });
        var sp=function(){ return _ents.filter(function(e){ return __uniIsFeEnt(e); }).length; }, s0=sp(), same=true, labelsByConv={};
        Object.keys((NB.fe&&NB.fe.forms)||{}).forEach(function(c){ if(__uniSetFeConv(c,{noStore:true})){ same=same&&(sp()===s0)&&(E()===e0); labelsByConv[c]=__uniEntLabel(_ents.filter(function(e){ return __uniIsFeEnt(e); })[0]||''); } });
        r.convSplitInvariant=same; r.convLabels=labelsByConv; r.convDistinct=Object.keys(labelsByConv).length>=5 && new Set(Object.values(labelsByConv)).size>=4;
        r.nmBack=__uniSetNaming('domain',{noStore:true}) && __uniSetFeConv(NB.fe.convention||'case',{noStore:true}); window.__uniNaming=null; window.__uniFeConv=null; __uniRelabel(); r.nmRoundTrip=L().join('|')===l0.join('|');
        r.nmBogus=(__uniSetNaming('verb')===false) && (__uniSetFeConv('emoji')===false) && __uniStrategy()===r.nmDefault[0];
        try{ window.__naming='table'; window.__namingDone=false; window.localStorage.setItem('gabe:universe:model','derived'); window.__modelDone=false; window.__model=null; __uniApplyDeepLinks();
          var _lit=[].map.call(document.querySelectorAll('.pill[data-grp="entnaming"] button.on'), function(b){ return b.getAttribute('data-v'); });
          r.dlPrecedence=(__uniStrategy()==='table' && window.__uniModel==='derived' && _lit.join(',')==='table' && window.localStorage.getItem('gabe:universe:naming')===null);
          window.localStorage.removeItem('gabe:universe:model'); window.__naming=null; window.__uniNaming=null;
          window.localStorage.setItem('gabe:universe:naming','verb'); window.__namingDone=false; __uniApplyDeepLinks(); r.dlStoredBogus=(__uniStrategy()===NB.default); window.localStorage.removeItem('gabe:universe:naming');
          var _dk=(NB.positions||[]).filter(function(k){ return k!=='domain'&&!(NB.disabled||{})[k]&&(NB.coverage||{})[k]>0; })[1]||alt; NB.disabled=NB.disabled||{}; var _keepD=NB.disabled[_dk]; NB.disabled[_dk]='x (probe)'; var _em3=document.getElementById('entnaming'); if(_em3) _em3.remove(); __uniAddWireView();
          var _btn=document.querySelector('.pill[data-grp="entnaming"] button[data-v="'+_dk+'"]'); r.dlDisabled=(__uniSetNaming(_dk)===false && !!_btn && _btn.disabled && !_btn.classList.contains('on')); if(_keepD===undefined) delete NB.disabled[_dk]; else NB.disabled[_dk]=_keepD; var _em4=document.getElementById('entnaming'); if(_em4) _em4.remove(); __uniAddWireView();
          var _slug=__uniClaimEnts.filter(function(e){ return !__uniIsFeEnt(e) && e!=='__unclaimed__'; })[0]; NB.entities=NB.entities||{}; var _keepE=NB.entities[_slug]; NB.entities[_slug]={display:'X <y> & z'}; __uniSetNaming('config',{noStore:true}); __uniPanelEnt(_slug);
          var _pn=document.querySelector('#phead .pname'); r.escHead=(_pn.textContent===__uniEntLabel(_slug) && _pn.innerHTML.indexOf('&lt;y&gt;')>=0 && !_pn.querySelector('y') && /X/.test(_pn.textContent));   // the head shows exactly the rendered label (the case mark applies) and the angle brackets are text, never an element if(_keepE===undefined) delete NB.entities[_slug]; else NB.entities[_slug]=_keepE; __uniSetNaming('domain',{noStore:true}); window.__uniNaming=null;
          var _cl=nodes.find(function(n){ return n.sub && n.sub!=='other' && !n.__cap; }); if(_cl){ __uniPanelClu(_cl.ent,_cl.sub); __uniSetNaming(alt,{noStore:true}); r.relabelKeepsPanel=(window.__uniPView&&window.__uniPView.lvl==='clu'&&window.__uniPView.sub===_cl.sub); __uniSetNaming('domain',{noStore:true}); window.__uniNaming=null; }
        }catch(e){ r.dlErr=String(e); }
        var keepN=GABE_C4.models.naming; delete GABE_C4.models.naming; r.nmAbsent=(__uniSetNaming('table')===false) && __uniEntLabel(_ents.filter(function(e){ return __uniIsFeEnt(e); })[0]||'fe·x').indexOf('fe · ')===0; GABE_C4.models.naming=keepN;
        try{ __uniPanelAll(); var _pt3=document.getElementById('pbody').textContent; r.nmSrcRow=/\(project default/.test(_pt3) && /frontend mark: case \(camel\/pascal\)/.test(_pt3); }catch(e){ r.nmSrcRow='err:'+e; } } else r.nmSkip='no naming block on the example feed — regen'; }catch(e){ r.nmErr=String(e); }
      try{ var _sp=function(){ return [_ents.filter(function(e){ return !__uniIsFeEnt(e); }).length, _ents.filter(function(e){ return __uniIsFeEnt(e); }).length]; }; var _s0=_sp(); var _lb=window.__uniEntLabel; window.__uniEntLabel=function(e){ return "X "+e; }; var _s1=_sp(); window.__uniEntLabel=_lb; r.splitInvariant=(_s0.join('/')===_s1.join('/')) && _s0[1]>0; r.split=_s0; }catch(e){ r.splitInvariant='err:'+e; }
      r.claim=__uniSetModel('claim'); r.roundTrip=(nodes.every(function(n){ return !(n.id in before) || n.ent===before[n.id]; }) && Object.keys(before).every(function(id){ return !NIDS[id] || NIDS[id].ent===before[id]; }) && _ents.length===__uniClaimEnts.length && _ents.every(function(e,i){ return e===__uniClaimEnts[i]; }) && nodes.every(function(n){ return !n.modelMark; }));
      r.noDash=!CLUSTERS.some(function(c){ return c.dash; });
      var keep=GABE_C4.models; delete GABE_C4.models; r.absent=(__uniSetModel('derived')===false) && window.__uniModel==='claim';
      try{ __uniPanelAll(); r.absentRow=/claim — the registry .*the only model this feed carries \(no entity-models block/.test(document.getElementById('pbody').textContent); }catch(e){}
      try{ var _em=document.getElementById('entmodel'); if(_em) _em.remove(); __uniAddWireView(); r.pillAbsent=[].map.call(document.querySelectorAll('.pill[data-grp="entmodel"] button'), function(b){ return b.getAttribute('data-v')+(b.classList.contains('on')?'*':'')+(b.disabled?'-':''); }).join(' '); }catch(e){ r.pillAbsent='err:'+e; }
      try{ window.localStorage.setItem('gabe:universe:model','derived'); window.__modelDone=false; window.__model=null; __uniApplyDeepLinks(); r.storedFallback=(window.__uniModel==='claim'); window.localStorage.removeItem('gabe:universe:model'); }catch(e){ r.storedFallback='err:'+e; }
      GABE_C4.models=keep;
      try{ var _em2=document.getElementById('entmodel'); if(_em2) _em2.remove(); __uniAddWireView(); }catch(e){}
      try{ var _d0=(M.rosters.derived||[]).filter(function(x){ return x.kind==='feature'; })[0]; window.__model='derived'; window.__ent=_d0&&_d0.id; window.__modelDone=false; window.__entDone=false; __uniApplyDeepLinks();
        r.deepLink=(window.__uniModel==='derived' && window.__uniPView && window.__uniPView.lvl==='ent' && window.__uniPView.ent===(_d0&&_d0.id)); window.__model=null; window.__ent=null; }catch(e){ r.deepLink='err:'+e; }
      try{ var _el=nodes.find(function(n){ return n.kind==='element'; })||(_CAPST&&_CAPST.nodes.find(function(n){ return n.kind==='element'; })); if(_el){ SEL={kind:'node',data:_el}; showPanel(_el); var _et=document.getElementById('pbody').textContent; r.elementCard=/Unclaimed file/.test(_et) && _et.indexOf(_el.det.file)>=0 && /functions/.test(_et); } else r.elementCard='no element node on the feed'; }catch(e){ r.elementCard='err:'+e; }
      __uniSetModel('claim');
      try{ __uniPanelAll(); r.claimRow=/claim — the registry/.test(document.getElementById('pbody').textContent); }catch(e){}
      return r; }catch(e){ return {err:String(e)}; } }).catch(e=>({err:String(e)}));
  console.log('  modelSw '+JSON.stringify(modelSw));
  const modelOk = !!(modelSw && !modelSw.err && modelSw.seeded===true && modelSw.sameN && modelSw.idsOk && modelSw.movedOk && modelSw.heldOk && modelSw.abstainN && modelSw.regOk && modelSw.abstainOk && modelSw.otherOk
    && modelSw.evClaim!==false && modelSw.claim0===true && modelSw.derivedOff===true && modelSw.aspectReg===true && modelSw.noEmptyHull===true && modelSw.aspectHullAfterLoad===true && modelSw.newClustersFeed===true
    && modelSw.splitInvariant===true && !modelSw.nmErr && !modelSw.nmSkip && modelSw.nmSwitch===true && modelSw.nmRelabelOnly===true && modelSw.nmChanged===true && modelSw.convSplitInvariant===true && modelSw.convDistinct===true && modelSw.nmBack===true && modelSw.nmRoundTrip===true && modelSw.nmBogus===true && modelSw.nmAbsent===true && modelSw.nmSrcRow===true && !modelSw.dlErr && modelSw.dlPrecedence===true && modelSw.dlStoredBogus===true && modelSw.dlDisabled===true && modelSw.escHead===true && modelSw.relabelKeepsPanel===true && modelSw.absentRow===true && /claim\* seeded- derived- proposed-/.test(modelSw.pillAbsent||'') && modelSw.storedFallback===true && modelSw.deepLink===true && (modelSw.elementCard===true || modelSw.elementCard==='no element node on the feed')
    && /claim seeded\*/.test(modelSw.pill||'') && modelSw.srcRow===true && modelSw.cardRow===true && modelSw.derived===true && modelSw.walkOk && modelSw.aspect && modelSw.aspect.dash===true
    && modelSw.entCard===true && modelSw.proposed===true && ['FEATURE','SPLIT','MERGE','ASPECT','LAYER'].indexOf(modelSw.badge)>=0 && modelSw.claim===true && modelSw.roundTrip===true && modelSw.noDash && modelSw.absent===true && modelSw.claimRow===true);
  await b.close();
  // the frontend fold, when the feed carries it: pieces drawn · every web node absorbed · bridge wires survive ·
  // types held back (toggle present) — a feed WITHOUT fe must leave all of that at zero (honest-empty)
  const f=r.fe, feOk = f.present ? (f.feNodes>0 && f.webLeft===0 && f.absorbed>0 && f.typesHeld>0 && f.typesDrawn===0 && f.feRels>0 && f.bridge>0 && f.tog)
                                 : (f.feNodes===0 && f.absorbed===0 && f.typesHeld===0 && !f.tog);
  const w=r.few, fewOk = !f.present ? true : (w.band0 && w.offDefault && w.writeNode && w.flatWhenOff && w.hotAtWrite && w.coolFar
    && w.ringDraw && w.ringOffDefault && w.ringsDrawn>0 && w.ringsCleared===0);
  // the 8 journeys-review workflows LOADED (16 total). newBad counts steps not in the DERIVED backend
  // set — legitimately the read-companions (GET) + the ORM-idiom writes (systemic #5) the access pass
  // can't see; the station HONESTLY marks those unmapped per row, so it is reported, not gated.
  const wi=r.wfInfo, wfOk = wi.newFound===8 && wi.count===16;
  const iconsOk = r.iconsBuilt===6;   // flag/provider/module/web/middleware/prompt each build a billboard icon (no cube)
  const hdrOk = r.hdr && r.hdr.moved<=1 && r.hdr.slotEmpty>=240 && r.hdr.slotFull>=240 && Math.abs(r.hdr.slotEmpty-r.hdr.slotFull)<=1;   // the reserved walker slot keeps a constant width → tiers don't shift when a journey enters/leaves
  const _FE_KINDS=['hook','component','module','store','route','web','screen','type'];
  const jrnOk = r.jrn && r.jrn.feLen>=1 && _FE_KINDS.indexOf(r.jrn.firstKind)>=0 && r.jrn.depthNoFlood===true
    && r.jrn.badges>0 && r.jrn.badgesUnique===true && r.jrn.badgesCleared===0;   // + the walk overlays step-NUMBER badges (ONE per node, no stacking), cleared when the journey ends
  // the workflows tab is a DEV-ONBOARDING LADDER — assert INVARIANTS (not the 16-workflow census):
  // no out-of-range level, leveled>0, sum matches, one pip per leveled row, lede shown, ①→②→③
  // grouped, and collapsing one level isolates only its rows.
  const lv=r.lvl, levelsOk = lv && lv.outOfRange===0 && lv.leveled>0 && lv.sumMatches===true
    && lv.headers>=1 && lv.pips===lv.leveled && lv.hasLede===true && lv.grouped===true && lv.collapseIsolates===true;
  // COMMIT journeys: the example seeds a gustify commits.js → >=1 commit journey, all carriers on
  // the map, the commit tab renders, and walking one runs the shared walk.
  const cm=r.cm, commitsOk = cm && !cm.err && cm.n>0 && cm.carriersOnMap===true && cm.tab===true
    && cm.walked && cm.walked.mode==='journey' && cm.walked.steps>0;
  // the 3 middle-section refinements behave: tier-icon set switch (text↔svg↔back), entity picker
  // collapsed-by-default (0 chips → expands), and one classification info icon per level.
  const u3=r.ui3, ui3Ok = u3 && !u3.err && u3.tierGridSettled===true && u3.entCollapse===true && u3.infoIcons>=3 && u3.infoHaveVars===true;
  // component classes are visually distinct: view=screen glyph (no badge), connector/container/leaf/private=cube+badge (all four badged)
  const fc=fcb, fcbOk = fc && !fc.err && fc.view===true && fc.connector===true && fc.container===true && fc.leaf===true && fc.priv===true;
  // a click focuses tight (focus mode, depth 1, small set) and a tier press CLEARS it → full graph, deterministic
  const focusOk = clickFocus && !clickFocus.err && clickFocus.ok && clickFocus.mode==='focus' && clickFocus.on===true
    && clickFocus.depth===1 && clickFocus.vis<150
    && afterTier && !afterTier.err && afterTier.on===false && afterTier.walk===null && afterTier.vis>clickFocus.vis;
  // tiers on Alt+Digit only: plain 2 leaves the tier untouched; Alt+2 → T1 and stays T1 on repeat (deterministic); Alt+4→T3, Alt+1→T0
  const kr=keyReg, keyOk = kr && !kr.err && kr.t0===3 && kr.afterPlain===3 && kr.afterAlt===1 && kr.afterAltx3===1 && kr.map4===3 && kr.map1===0;
  // the reference opens with both sides + example chips + badges + flags + connectors + planets + the View row;
  // a chip fills the bar and focuses (HL focus mode) and closes the overlay; a flag hides its kind (all→off)
  const lr=legRef, legRefOk = lr && !lr.err && lr.open && lr.open.secs===2 && lr.open.chips>0 && lr.open.badges>0
    && lr.open.flags>0 && lr.open.conn && lr.open.planet && lr.open.viewRow
    && lr.ref && lr.ref.compNoEx && lr.ref.endpNoEx && lr.ref.fnNoEx && lr.ref.typeEx && lr.ref.entityEx && lr.ref.privBadge && lr.ref.noEnableF
    && lr.tier && lr.tier.noOverlaySel && lr.tier.cells>0 && lr.tier.routeDots===4 && !lr.tier.routeDim && lr.tier.hookDots===2 && lr.tier.hookDim && lr.tier.leafDots===1 && lr.tier.typeDots===1 && lr.tier.typeHasFlag && lr.tier.t3ShowTypes && lr.tier.anyCells>0 && lr.tier.foldEx
    && lr.layout && lr.layout.grids===2 && lr.layout.tierLast && lr.layout.connFleetSameGrid && lr.layout.wireUniq>=5 && lr.layout.wireNotAllGray && lr.layout.compCobalt
    && lr.layout.thumbs>0 && lr.layout.refCells>0 && lr.layout.hdrRefAfterTitle && lr.layout.iconHug<20 && lr.layout.starIs2d && lr.layout.satIsThumb && lr.layout.fkDescRevised
    && lr.jump && lr.jump.closed===true && lr.jump.barVal===lr.jump.s && lr.jump.hlOn===true && lr.jump.hlMode==='focus'
    && lr.flag && lr.flag.before==='all' && lr.flag.after==='off' && lr.flag.rebuilt===true;
  // the journey-detail overlay opens from the walk-bar name, lists every step (icon + entity groups), and a
  // step row walks the graph to it + closes.
  const jd=jrnDetail, jrnDetailOk = jd && !jd.err && jd.clickable && jd.steps>0 && jd.stepsMatch && jd.groups===0 && jd.cols===1 && jd.colsSticky && jd.tinted===jd.steps && jd.opcs===jd.ops && jd.flows===jd.steps && jd.fromTo>0 && jd.icons===jd.steps
    && jd.entDots===jd.steps && jd.clus===jd.steps && jd.ops>0 && jd.tgts>0 && jd.fields>0 && jd.rels>0 && jd.flush && jd.aligned && jd.resizeOk
    && jd.matrixOk && jd.frozenOk && jd.walkSyncOk && jd.flagsOk && jd.opcFrozen && jd.indirect>0;
  const sc=storeCheck, storeOk = sc && !sc.err && sc.storeCols>=1 && sc.storeFlagOn && sc.litStore>=1 && sc.iconInline && sc.titleHot && sc.cellClean && sc.row0Lit>=0 && sc.row0Lit<=5 && sc.anchorKind==='route' && sc.anchorKind3==='route' && sc.lgbiOk===true && /useCreatePantryItem/.test(sc.feStart||'') && sc.hookRoles && sc.hookRoles.hooks>0 && sc.hookRoles.withRole===sc.hookRoles.hooks && sc.hookRoles.kinds>=3 && sc.storeShape && sc.storeShape.stores>0 && sc.storeShape.shaped>=1 && sc.cardOrder && !sc.cardOrder.err && /Usage/.test(sc.cardOrder.store[0]||'') && /Structure/.test(sc.cardOrder.store[1]||'') && /Structure/.test(sc.cardOrder.model[1]||'') && sc.cardOrder.carries===true && sc.cardOrder.ref && sc.cardOrder.ref.blank===0 && sc.cardOrder.ref.fe===true && sc.drafts>=1 && sc.draftWalk>0 && sc.draftGrp && sc.draftLeveled && sc.draftNamed && sc.viewType==='View (FE)' && sc.viewCol==='#d946ef' && (sc.viewIcon==='heat'||sc.viewIcon==='#d946ef');
  const wireSelOk = !!(wireSel && !wireSel.err && wireSel.drawn===true && wireSel.vis===true && wireSel.chips>=8 && wireSel.key===true && wireSel.beam===0);
  const homingOk = !!(homingEv && !homingEv.err && homingEv.stats && homingEv.stats.present && homingEv.stats.pieces > 0 && homingEv.nodeWithEv && homingEv.cardRow === true && homingEv.clean === true && homingEv.unclaimedCard !== false && homingEv.sourcesRow === true);
  const legend56Ok = !!(legend56 && !legend56.err && legend56.slot1===1 && legend56.apart===true && legend56.plainSlot1===0 && legend56.providerClass===true && legend56.ref && legend56.ref.llm==='real' && legend56.ref.payments==='dash' && legend56.ref.stream==='real' && legend56.refN===9 && legend56.refBlank && legend56.refBlank.length===0 && legend56.contrastBad && legend56.contrastBad.length===0);
  const dispOk = !!(dispSel && !dispSel.err && dispSel.drawn===true && dispSel.chip===true && dispSel.ref==='real');
  const scaleOk = !!(scaleDL && !scaleDL.err && scaleDL.hit===true && scaleDL.capOn===false && scaleDL.tier===0 && scaleDL.row===true && scaleDL.jrn && scaleDL.steps>0 && scaleDL.ent==='ent');
  const ok = r.nodes>0 && !r.err && errs.length===0 && r.cardOpen && r.stPass && feOk && wireSelOk && scaleOk && dispOk && legend56Ok && homingOk && fewOk && wfOk && iconsOk && hdrOk && jrnOk && levelsOk && commitsOk && ui3Ok && fcbOk && focusOk && keyOk && legRefOk && jrnDetailOk && storeOk && modelOk;
  if(ok) console.log(`  render: PASS — ${r.nodes} live nodes, 0 errors, card renders (st-pass=${r.stPass}, faces=${r.face}); frontend ${f.present?`${f.feNodes} pieces · ${f.absorbed} screens absorbed · ${f.typesHeld} types held · FE-write heat off-by-default, bands blue→magenta`:'absent (honest-empty)'}`);
  else { console.error('  render FAIL:', JSON.stringify(r), 'fewOk='+fewOk, 'wfOk='+wfOk, 'iconsOk='+iconsOk, 'hdrOk='+hdrOk, 'jrnOk='+jrnOk, 'levelsOk='+levelsOk, 'commitsOk='+commitsOk, 'ui3Ok='+ui3Ok, 'fcbOk='+fcbOk+' '+JSON.stringify(fcb), 'focusOk='+focusOk+' click='+JSON.stringify(clickFocus)+' tier='+JSON.stringify(afterTier), 'keyOk='+keyOk+' '+JSON.stringify(keyReg), 'legRefOk='+legRefOk+' '+JSON.stringify(legRef).slice(0,600), 'jrnDetailOk='+jrnDetailOk+' '+JSON.stringify(jrnDetail), 'storeOk='+storeOk+' '+JSON.stringify(storeCheck), 'modelOk='+modelOk+' '+JSON.stringify(modelSw), 'errs='+errs.slice(0,4).join(' | ')); process.exit(1); }
})();
JS
  RENDER=$?
else
  echo "  render: SKIP ⚠ — RENDER COVERAGE DID NOT RUN (no chrome/playwright-core/example on this host)."
  echo "         provision: mkdir -p docs/design/graft-adoption/spike/_build && (cd \$_ && npm i playwright-core) ; system chrome, or set GABE_CHROME_BIN/GABE_PW_DIR (see docs/design/graft-adoption/spike/README.md §Rebuild)."
  echo "           the static contract above still holds, but the inline-engine execution path is UNVERIFIED here."
  RENDER=0
fi

# ── 13b. OPTIONAL tier-engine behavioral proof (the arc's headline feature) ──
#    The static checks above only assert the tier STRINGS exist; a logic regression (a non-nested
#    preset breaking monotonic reveal, __uniSetTier no-op'ing, a broken feClass gate / key / sync,
#    a tier×walk collision) keeps every string check green. verify-tiers.mjs TOGGLES __uniSetTier
#    against the committed example and asserts the actual behavior — wire it here so suite-doctor runs it.
VTIERS="$REPO/docs/design/codebase-graph-consolidation/universe-build/verify-tiers.mjs"
if [ -x "$CHROME" ] && [ -d "$PWDIR" ] && [ -f "$EXPAGE" ] && [ -f "$VTIERS" ]; then
  if GABE_CHROME_BIN="$CHROME" GABE_PW_DIR="$PWDIR" node "$VTIERS"; then
    TIERS=0
  else
    TIERS=1; echo "  tiers: FAIL — verify-tiers.mjs reported a tier-engine regression (see PASS/FAIL lines above)"
  fi
else
  echo "  tiers: SKIP ⚠ — TIER-ENGINE COVERAGE DID NOT RUN (no chrome/playwright-core/example on this host)."
  echo "         the static tier-string contract above still holds, but the toggle logic is UNVERIFIED here."
  TIERS=0
fi

[ "$STATIC" = 0 ] && [ "$MISS" = 0 ] && [ "$RENDER" = 0 ] && [ "$TIERS" = 0 ] && { echo "gabe-universe battery: ALL PASS"; exit 0; }
echo "gabe-universe battery: FAILURES ABOVE"; exit 1
