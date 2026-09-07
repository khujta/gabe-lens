/* adapter.js — THE adapter. Every lab page and the probe read the SAME {nodes, links} from window.GABE_C4 through this file,
   so the only variable between two rows of the README table is the renderer. A faithful port of the station's own fold
   (templates/center/shell/gabe-universe.html, the "live adapter" block, suite head b2273c9):
     · L2 pieces DEDUP by id (a shared piece draws once); an UNKNOWN kind is KEPT + drawn generically + counted (never dropped)
     · fe pieces homed by `home` (bucket · candidate · fe·<twin> pair) → synthetic entities with their own colour
     · the bridge cross-edge lands on the EXPORT that fetched (D3), else the fetching file's piece (screen absorption)
     · fe-type → `type`; the feed's `uses-hook`/`uses-store` → `uses`/`reads` (FE_REL)
     · tiers T0–T3 from the station's _TIER_PRESETS (kind off-lists + feClass off-lists); a tier press changes VISIBILITY only
     · entity anchors EX/EY/EZ · sub-cluster rings (recomputeSubAnchors) · KRADF kind rings · 1.6×RENT containment — zForce
   plus what the labs need and the station does not expose: deterministic seed positions, baked positions (?layout=baked),
   the ×k clone ladder (?scale=x4), the function layer (?fn=1 with levels.js), an injected unknown kind (?inject=1) and
   selfTest(). Deterministic: same feed + same URL → the same object; no Math.random, no wall clock.
   URL knobs: ?feed (feed-loader.js) · ?fn=0|1 · ?fe=0|1 · ?scale=full|core|x2|x4|x8 · ?layout=live|baked · ?tier=0..3 · ?inject=1
   Output (window.GABE_FEED): { nodes, links, ents, byId, anchors, kinds, conn, connKinds, rel2kind, dashmap, method, bandpal,
     feband, counts, fixture, head, budget:1600, scale, layout, tier, tierOf(n), bandOf(l), colorOf(n), seedPositions(spread),
     force(alpha), applyBaked(), selfTest(), qs(k,d), methodOf(label) } */
(function () {
  'use strict';
  function qs(k, d) { var m = new RegExp('[?&]' + k + '=([^&]*)').exec(location.search); return m ? decodeURIComponent(m[1]) : d; }

  /* ── the station's literals, mirrored (kind → colour · form · layer) ───────────────────────────────────────────── */
  var KINDS = {
    route: { col: '#38bdf8', form: 'cone', layer: 'web' }, component: { col: '#2f7de1', form: 'panel', layer: 'web' },
    hook: { col: '#10b981', form: 'knot', layer: 'web' }, store: { col: '#ec4899', form: 'cylinder', layer: 'web' },
    type: { col: '#64748b', form: 'wire', layer: 'web' }, screen: { col: '#a855f7', form: 'panel', layer: 'web' },
    web: { col: '#a855f7', form: 'panel', layer: 'web' }, module: { col: '#f59e0b', form: 'slab', layer: 'web' },
    unknown: { col: '#9aa3b2', form: 'panel', layer: 'web' },
    endpoint: { col: '#8b5cf6', form: 'ring', layer: 'endpoints' },
    'function': { col: '#6366f1', form: 'cube', layer: 'api' }, middleware: { col: '#7048e8', form: 'slab', layer: 'api' },
    flag: { col: '#e03131', form: 'slab', layer: 'api' }, element: { col: '#8a8f98', form: 'panel', layer: 'api' },
    schema: { col: '#06b6d4', form: 'octa', layer: 'data' }, model: { col: '#14b8a6', form: 'cylinder', layer: 'data' },
    external: { col: '#94a3b8', form: 'octa', layer: 'data' }, provider: { col: '#e8590c', form: 'panel', layer: 'data' },
    prompt: { col: '#ae3ec9', form: 'panel', layer: 'data' }, entity: { col: '#84cc16', form: 'container', layer: 'data' }
  };
  var GENERIC = { col: '#8a8f98', form: 'panel', layer: 'data' };
  var FE_KIND = { 'fe-type': 'type', 'fe-unknown': 'unknown' };
  var FE_REL = { 'uses-hook': 'uses', 'uses-store': 'reads' };
  var FE_HOME_COL = { bucket: '#7c3aed', candidate: '#f97316' };
  var CONN = {
    fk: { color: '#5893ad', style: 'sparse', density: 2.7, trust: 0.9, grad: true, thick: 1, gmode: 'ent' },
    bridge: { color: '#e8f443', style: 'sparse', density: 1.7, trust: 0.62, thick: 1, gmode: 'ent' },
    calls: { color: '#817536', style: 'solid', density: 2, trust: 0.6, grad: false, thick: 1, gmode: 'type' },
    imports: { color: '#a855f7', style: 'dotted', density: 2.2, trust: 0.52, thick: 1, gmode: 'ent' },
    rollup: { color: '#8b5cf6', style: 'sparse', density: 0.9, trust: 0.4, thick: 1, grad: true, gmode: 'type-ent' },
    access: { color: '#e5484d', style: 'solid', density: 2.5, trust: 0.85, thick: 1.6, grad: false, gmode: 'type-ent' },
    dispatches: { color: '#f76707', style: 'longdash', density: 1.9, trust: 0.55, grad: false, thick: 1, gmode: 'type' }
  };
  var CONN_KINDS = ['fk', 'bridge', 'calls', 'imports', 'rollup', 'access', 'dispatches'];
  var REL2KIND = { fk: 'fk', pk: 'fk', nests: 'fk', handler: 'calls', touch: 'calls', touches: 'calls', resp: 'calls', uses: 'calls', calls: 'calls',
    consumes: 'calls', fetches: 'bridge', bridge: 'bridge', renders: 'imports', mounts: 'imports', reads: 'imports', imports: 'imports', typed: 'imports',
    fecall: 'calls', bundle: 'calls', reads_from: 'rollup', writes_to: 'rollup', fnreads: 'access', fnwrites: 'access', depends: 'calls', gated_by: 'calls',
    dispatches: 'dispatches', serializes: 'fk', reaches: 'calls', walls: 'access', fnprompts: 'calls' };
  var LINKMETA = { touches: { w: 4, pv: 1 }, fk: { w: 2, pv: 1 }, bridge: { w: 3, pv: 0 }, calls: { w: 5, pv: 0 }, imports: { w: 3, pv: 0 }, renders: { w: 3, pv: 1 },
    mounts: { w: 2, pv: 1 }, uses: { w: 4, pv: 0 }, reads: { w: 3, pv: 0 }, typed: { w: 2, pv: 1 }, fetches: { w: 5, pv: 0 }, handler: { w: 6, pv: 1 }, resp: { w: 3, pv: 1 },
    pk: { w: 1, pv: 1 }, depends: { w: 4, pv: 0 }, gated_by: { w: 5, pv: 0 }, dispatches: { w: 4, pv: 0 }, serializes: { w: 2, pv: 0 }, reaches: { w: 3, pv: 0 },
    walls: { w: 4, pv: 0 }, fnprompts: { w: 2, pv: 0 }, fnreads: { w: 3, pv: 0 }, fnwrites: { w: 3, pv: 0 } };
  var DASHMAP = { solid: '', dashed: '6 3', dotted: '1.5 3.5', sparse: '5 10', longdash: '10 4' };
  var METHOD = { GET: '#22c55e', POST: '#3b82f6', PUT: '#f97316', PATCH: '#eab308', DELETE: '#ef4444', BOOT: '#8a8f98', TASK: '#f0abfc' };
  var BANDPAL = ['#f2711c', '#f59f00', '#f5d90a', '#bcd12f', '#46a758'];   // backend d2w: 0 closest→orange … 4/none→green
  var FEBAND = ['#c026d3', '#9c33e0', '#7c3aed', '#4f52ea', '#2563eb'];    // frontend fed2w: 0 at-the-write→magenta … 4/far→blue
  var KRADF = { endpoint: 1.45, web: 1.45, screen: 1.45, external: 1.1, 'function': 0.35, model: 0.4, schema: 0.4, type: 0.3, module: 0.45, store: 0.5, hook: 0.7, component: 0.9, route: 1.2 };
  var TIERS = [
    { name: 'Skeleton', koff: ['function', 'schema', 'hook', 'module', 'unknown', 'type', 'middleware', 'flag', 'provider', 'prompt', 'external', 'store', 'element'], fcoff: ['private', 'connector', 'container', 'leaf'] },
    { name: 'Surface', koff: ['function', 'hook', 'module', 'unknown', 'type', 'prompt', 'element'], fcoff: ['private', 'leaf'] },
    { name: 'Trace', koff: ['module', 'unknown', 'type'], fcoff: ['leaf'] },
    { name: 'Everything', koff: [], fcoff: [] }];
  var SPREAD = 1.4, BUDGET = 1600;

  function methodOf(label) {
    var G = window.GABE_GRAMMAR; if (G && typeof G.methodOf === 'function') { try { var r = G.methodOf(label); return r == null ? null : r; } catch (e) { /* fall through */ } }
    var m = /^(GET|POST|PUT|PATCH|DELETE|BOOT|TASK)\b/.exec(label || ''); return m ? m[1] : null;
  }
  function num(x) { return (typeof x === 'number' && isFinite(x)) ? x : (+x || 0); }
  function hash(s) { var h = 2166136261; for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; } return h >>> 0; }
  function testFloor(det) { var n = (det.cases || []).length + num(det.cases_more); (det.case_files || []).forEach(function (f) { var mm = /(\d+)\s*case/.exec(f.name || ''); if (mm) n += +mm[1]; }); return n; }

  function build(C4, LV, o) {
    if (o.scale === 'core') o = Object.assign({}, o, { fe: false, fn: false });   /* core = L1+L2+cross with the web nodes in place (no fe fold, so the bridges land on the fetching files) */
    var warn = [], generic = 0, unknownRels = {};
    var K = {}; Object.keys(KINDS).forEach(function (k) { K[k] = KINDS[k]; });
    function kindOf(kind) { if (!K[kind]) { K[kind] = { col: GENERIC.col, form: GENERIC.form, layer: GENERIC.layer, generic: true }; generic++; warn.push('kind "' + kind + '" unknown to this adapter — drawn generically (never dropped)'); } return K[kind]; }
    var COL = C4.colors || {};
    var ents = ((C4.l1 && C4.l1.nodes) || []).map(function (e) { return e.slug || e.id; });
    if (!ents.length) ents = Object.keys(C4.l2 || {});
    var ENT = {}, entKind = {}, entPair = {};
    ents.forEach(function (e) { ENT[e] = COL[e] || '#0d9488'; entKind[e] = 'entity'; });

    var nodes = [], byId = Object.create(null);
    function add(n) { if (byId[n.id]) return null; byId[n.id] = n; nodes.push(n); return n; }
    Object.keys(C4.l2 || {}).forEach(function (ent) {
      ((C4.l2[ent] || {}).nodes || []).forEach(function (p) {
        var kd = kindOf(p.kind), det = p.det || {}, beh = p.behind || {};
        add({ id: p.id, kind: p.kind, ent: ent, entClaim: ent, sub: kd.layer, label: p.label || p.slug || p.id, m: p.kind === 'endpoint' ? methodOf(p.label) : null,
          det: det, behind: { fns: num(beh.fns), depth: num(beh.depth) }, stream: !!p.stream, pclass: p.pclass || null, homeEv: p.home_ev || null,
          table: p.table || null, sites: num(p.sites), fn: p.fn || null, fnsN: p.kind === 'element' ? num(p.fns) : null, unmapped: !!p.unmapped,
          tests: testFloor(det), cols: (det.cols || []).length, generic: !!kd.generic, fe: undefined, deg: 0 });
      });
    });
    var FE = (o.fe && C4.fe && C4.fe.pieces && C4.fe.pieces.length) ? C4.fe : null;
    if (FE) {
      (FE.homes || []).forEach(function (h) { if (h.kind === 'entity') return; entKind[h.id] = h.kind; if (h.pair) entPair[h.id] = h.pair;
        if (ents.indexOf(h.id) < 0) { ents.push(h.id); ENT[h.id] = (h.pair && ENT[h.pair]) ? tint(ENT[h.pair], 0.38) : (FE_HOME_COL[h.kind] || '#8b5cf6'); } });
      FE.pieces.forEach(function (p) { var kind = FE_KIND[p.kind] || p.kind, kd = kindOf(kind);
        if (ents.indexOf(p.home) < 0) { ents.push(p.home); ENT[p.home] = '#8b5cf6'; entKind[p.home] = 'bucket'; warn.push('fe home "' + p.home + '" not in fe.homes — added'); }
        add({ id: p.id, kind: kind, ent: p.home, entClaim: p.home, sub: kd.layer, label: p.name || p.id, m: null,
          det: { file: p.file, span: p.span || null, cols: (p.fields || p.members || []).length }, behind: { fns: 0, depth: 0 }, stream: false, pclass: null, homeEv: p.home_ev || null,
          table: null, sites: num(p.sites), fn: null, fnsN: null, unmapped: false, tests: 0, cols: (p.fields || p.members || []).length, generic: !!kd.generic,
          fe: true, screen: p.screen || null, feClass: p.feClass || null, hrole: p.hrole || null, mclass: p.mclass || null, fed2w: (p.fed2w == null ? null : p.fed2w),
          write: !!p.write, cache: !!p.cache, sse: !!p.sse, candidate: !!p.candidate, area: p.area || null, deg: 0 });
      });
    }
    var fnN = 0, handlers = 0;
    if (o.fn && LV && LV.fn_nodes && LV.fn_nodes.length) {
      LV.fn_nodes.forEach(function (f) { var kd = kindOf('function'); var ent = f.slug || '__unclaimed__'; if (ents.indexOf(ent) < 0) { ents.push(ent); ENT[ent] = COL[ent] || '#0d9488'; entKind[ent] = 'entity'; }
        if (add({ id: f.id, kind: 'function', ent: ent, entClaim: ent, sub: kd.layer, label: f.name || f.id.replace(/.*#/, ''), m: null, det: { file: f.id.split('#')[0], layer: f.layer || null, role: f.role || null },
          behind: { fns: num(f.behind && f.behind.fns), depth: num(f.behind && f.behind.depth) }, stream: false, pclass: null, homeEv: null, table: null, sites: 0, fn: null, fnsN: null, unmapped: false,
          tests: 0, cols: 0, generic: false, fe: undefined, d2w: (f.d2w == null ? null : f.d2w), god: !!(f.god || (f.hub && f.hub.god)), hub: !!(f.hub && num(f.hub.usage) >= 20), handler: !!f.handler, access: f.access || null, deg: 0 })) fnN++; });
    }
    if (o.inject) { kindOf('zz-unknown-kind'); add({ id: 'zz:lab-injected', kind: 'zz-unknown-kind', ent: ents[0], entClaim: ents[0], sub: 'data', label: 'lab injected unknown kind', m: null, det: {}, behind: { fns: 0, depth: 0 }, stream: false, pclass: null, homeEv: null, table: null, sites: 0, fn: null, fnsN: null, unmapped: false, tests: 0, cols: 0, generic: true, fe: undefined, deg: 0 }); }

    /* ── links ──────────────────────────────────────────────────────────────────────────────────────────────────── */
    var links = [];
    function link(s, t, rel, extra) { var l = { source: s, target: t, rel: rel, kind: REL2KIND[rel] }; if (!l.kind) { l.kind = 'calls'; if (!unknownRels[rel]) warn.push('rel "' + rel + '" unknown to this adapter — drawn as calls (never dropped)'); unknownRels[rel] = (unknownRels[rel] || 0) + 1; } if (extra) Object.keys(extra).forEach(function (k) { l[k] = extra[k]; }); links.push(l); return l; }
    Object.keys(C4.l2 || {}).forEach(function (ent) { ((C4.l2[ent] || {}).edges || []).forEach(function (e) { link(e.source, e.target, e.kind || 'calls'); }); });
    (C4.cross_edges || []).forEach(function (e) { link(e.from, e.to, e.kind || 'fk', { cross: true, xp: e['export'] || null }); });
    var absorbed = 0;
    if (FE) {
      var P = FE.pieces; (FE.edges || []).forEach(function (e) { var a = P[e[0]], b = P[e[1]]; if (!a || !b) return; link(a.id, b.id, FE_REL[e[2]] || e[2], { fe: true, chrome: e[3] === 'chrome', write: e[3] === 'write' }); });
      var ABS = {}; nodes.forEach(function (n) { if (n.fe && n.screen && byId[n.screen] && byId[n.screen].kind === 'web') ABS[n.screen] = n.id; });
      links.forEach(function (l) { if (l.xp && byId[l.xp]) l.source = l.xp; else if (ABS[l.source]) l.source = ABS[l.source]; if (ABS[l.target]) l.target = ABS[l.target]; });
      Object.keys(ABS).forEach(function (w) { delete byId[w]; }); nodes = nodes.filter(function (n) { return !ABS[n.id]; }); absorbed = Object.keys(ABS).length;
    }
    if (o.fn && LV && LV.fn_nodes && LV.fn_nodes.length) {
      (LV.fn_edges || []).forEach(function (e) { link(e.s, e.t, e.rel || 'calls', { conf: e.conf || null }); });
      (LV.schema_edges || []).forEach(function (e) { link(e.s, e.t, e.rel || 'uses'); });
      nodes.forEach(function (n) { if (n.kind === 'function' && n.access && n.access.ops) { (n.access.ops || []).forEach(function (op) { if (op.model && byId['model:' + op.model]) link(n.id, 'model:' + op.model, op.rw === 'w' ? 'fnwrites' : 'fnreads'); }); } });
      nodes.forEach(function (n) { if (n.kind !== 'endpoint' || !n.fn) return; var key = String((n.det || {}).file || '').split(':')[0] + '#' + n.fn; if (byId[key]) { link(n.id, key, 'handler'); handlers++; } });   /* the station composes det.file#fn — a bare fn name resolves nothing (review 2026-09-07) */
    }
    if (o.inject) { var ep = nodes.filter(function (n) { return n.kind === 'endpoint'; })[0]; if (ep) link(ep.id, 'zz:lab-injected', 'calls'); }
    var dropped = 0; links = links.filter(function (l) { var ok = byId[l.source] && byId[l.target] && l.source !== l.target; if (!ok) dropped++; return ok; });
    links.forEach(function (l) { var m = LINKMETA[l.rel] || { w: 2, pv: 1 }; l.w = m.w; l.proven = !!m.pv; byId[l.source].deg++; byId[l.target].deg++; });
    nodes.forEach(function (n) { if (n.hub == null) n.hub = n.deg >= 20; if (n.god == null) n.god = false; });

    /* ── ×k clone ladder ─────────────────────────────────────────────────────────────────────────────────────────── */
    var mk = /^x(\d+)$/.exec(o.scale || '');
    if (mk) { var k = Math.max(2, Math.min(32, +mk[1])), N0 = nodes, L0 = links, cross0 = L0.filter(function (l) { return l.cross; });
      nodes = []; links = []; byId = Object.create(null); var E0 = ents.slice(); ents = [];
      for (var c = 0; c < k; c++) { var sfx = c ? '#c' + c : '';
        E0.forEach(function (e) { ents.push(e + sfx); if (c) { ENT[e + sfx] = ENT[e]; entKind[e + sfx] = entKind[e]; if (entPair[e]) entPair[e + sfx] = entPair[e] + sfx; } });
        N0.forEach(function (n) { var m = Object.assign({}, n, { id: n.id + sfx, ent: n.ent + sfx, entClaim: n.entClaim + sfx }); nodes.push(m); byId[m.id] = m; });
        L0.forEach(function (l) { links.push(Object.assign({}, l, { source: l.source + sfx, target: l.target + sfx })); });
        if (c) cross0.forEach(function (l, i) { if (i % 20 === 0) links.push(Object.assign({}, l, { target: l.target + sfx, clone: true })); }); }
    }

    /* ── anchors (the station's EX band + recomputeSubAnchors) ───────────────────────────────────────────────────── */
    var EX = {}, EY = {}, EZ = {}, RENT = {}, SUB = {};
    ents.forEach(function (e, i) { EX[e] = ents.length <= 1 ? 0 : (-300 + i * (600 / (ents.length - 1))); EY[e] = 0; EZ[e] = 0; });
    (function () { var cnt = {}, subs = {}; nodes.forEach(function (n) { cnt[n.ent] = (cnt[n.ent] || 0) + 1; (subs[n.ent] = subs[n.ent] || {})[n.sub] = (subs[n.ent][n.sub] || 0) + 1; });
      ents.forEach(function (e, ei) { var cc = cnt[e] || 0; RENT[e] = (30 + 9 * Math.sqrt(cc)) * SPREAD; var g = subs[e] || {}, ks = Object.keys(g).sort(function (a, b) { return (g[b] - g[a]) || (a < b ? -1 : 1); }); var m = {}; SUB[e] = m;
        if (ks.length < 2) { ks.forEach(function (kk) { m[kk] = { x: 0, y: 0, z: 0 }; }); return; }
        var SR = Math.min(RENT[e] * 0.78, 44 + 13 * ks.length); ks.forEach(function (kk, i) { var a = ei * 0.7 + i * (Math.PI * 2 / ks.length); m[kk] = { x: Math.cos(a) * SR, y: ((i % 2) ? 1 : -1) * SR * 0.22, z: Math.sin(a) * SR }; }); }); })();

    /* ── tiers · bands · colours ─────────────────────────────────────────────────────────────────────────────────── */
    function tierOf(n) { var kind = n.kind;   /* a generic (unregistered) kind is never in a koff list → visible at every tier, the station's behaviour */ for (var t = 0; t < 4; t++) { if (TIERS[t].koff.indexOf(kind) >= 0) continue; if (n.fe && n.feClass && TIERS[t].fcoff.indexOf(n.feClass) >= 0) continue; return t; } return 3; }
    nodes.forEach(function (n) { n.tier = tierOf(n); });
    var heat = { be: o.heat, fe: o.feHeat };   /* the station: backend heat on, FE write-spine heat DEFAULT OFF (operator D4) */
    function bandOf(l) { var t = byId[l.target]; if (!t) return null;
      if (l.fe) { if (!heat.fe || !l.write) return null; var f = t.fed2w; if (f == null) return null; var fi = Math.max(0, Math.min(4, f | 0)); return { pal: 'fe', i: fi, color: FEBAND[fi] }; }
      if (!heat.be || l.rel !== 'calls') return null; var d = t.d2w; var i = (d == null) ? 4 : Math.min(d | 0, 3); return { pal: 'be', i: i, color: BANDPAL[i] }; }   /* the station's __d2wBand: calls wires, the target's d2w, 4 = green when unknown */
    function colorOf(n) { return (K[n.kind] || GENERIC).col; }
    var byKind = {}, byTier = [0, 0, 0, 0]; nodes.forEach(function (n) { byKind[n.kind] = (byKind[n.kind] || 0) + 1; for (var t = n.tier; t < 4; t++) byTier[t]++; });
    var counts = { nodes: nodes.length, links: links.length, ents: ents.length, byKind: byKind, byTier: byTier, fe: nodes.filter(function (n) { return n.fe; }).length, absorbed: absorbed, generic: generic, fn: fnN, handlers: handlers,
      cross: links.filter(function (l) { return l.cross; }).length, feLinks: links.filter(function (l) { return l.fe; }).length, droppedLinks: dropped, unknownRels: unknownRels };

    /* ── positions: deterministic seed · baked · the station's zForce ────────────────────────────────────────────── */
    function seedPositions(spread) { spread = spread || 1; nodes.forEach(function (n) { var h = hash(n.id), th = (h % 3600) / 3600 * Math.PI * 2, ph = ((h >>> 12) % 1000) / 1000 * Math.PI - Math.PI / 2;
      var R = (RENT[n.ent] || 60) * (KRADF[n.kind] || 1.0) * spread, sa = (SUB[n.ent] || {})[n.sub] || { x: 0, y: 0, z: 0 };
      n.sx = EX[n.ent] + sa.x + Math.cos(th) * Math.cos(ph) * R; n.sy = EY[n.ent] + sa.y + Math.sin(ph) * R * 0.6; n.sz = EZ[n.ent] + sa.z + Math.sin(th) * Math.cos(ph) * R; }); return nodes; }
    function applyBaked() { var BB = window.GABE_BAKED || {}, B = BB[o.fixture + (o.fn ? ':fn' : '')] || BB[o.fixture]; var hit = 0;   /* the fn bake has its own key; without it the plain bake places the pieces and the functions stay live */
      if (/^x\d+$/.test(o.scale || '')) { nodes.forEach(function (n) { n.bx = n.by = n.bz = null; }); return { hit: 0, of: nodes.length, meta: null, why: 'a bake has no positions for cloned nodes (?scale=' + o.scale + ') — live layout' }; }
      if (B && B.meta && B.meta.head && C4.head && B.meta.head !== C4.head) warn.push('baked layout is STALE: layouts head ' + B.meta.head + ' ≠ feed head ' + C4.head + ' — re-run bake-fdp.py'); nodes.forEach(function (n) { var p = B && B.pos && B.pos[n.id.replace(/#c\d+$/, '')]; if (p) { hit++; n.bx = p[0]; n.by = p[1]; n.bz = p.length > 2 ? p[2] : 0; } else { n.bx = n.by = n.bz = null; } }); return { hit: hit, of: nodes.length, meta: B && B.meta || null }; }
    function force(alpha) { var ns = force.__n || []; for (var i = 0; i < ns.length; i++) { var n = ns[i], x = n.x || 0, y = n.y || 0, z = n.z || 0, has3 = typeof n.vz === 'number';
      var sa = (SUB[n.ent] || {})[n.sub], ax = EX[n.ent] || 0, ay = EY[n.ent] || 0, az = EZ[n.ent] || 0;
      n.vx += (ax + (sa ? sa.x : 0) - x) * 0.08 * alpha; n.vy += (ay + (sa ? sa.y : 0) - y) * 0.08 * alpha; if (has3) n.vz += (az + (sa ? sa.z : 0) - z) * 0.08 * alpha;
      var dx = x - ax, dy = y - ay, dz = has3 ? z - az : 0, r = Math.sqrt(dx * dx + dy * dy + dz * dz); if (!(r > 1e-3) || !isFinite(r)) continue;
      var R0 = RENT[n.ent] || 60, f = KRADF[n.kind]; if (f) { var kr = 0.30 * alpha * (R0 * f - r) / r; n.vx += dx * kr; n.vy += dy * kr; if (has3) n.vz += dz * kr; }
      var rmax = R0 * 1.6; if (r > rmax) { var kc = 0.6 * alpha * (rmax - r) / r; n.vx += dx * kc; n.vy += dy * kc; if (has3) n.vz += dz * kc; } } }
    force.initialize = function (ns) { force.__n = ns; };

    var feed = { nodes: nodes, links: links, ents: ents, byId: byId, entColor: ENT, entKind: entKind, entPair: entPair, anchors: { EX: EX, EY: EY, EZ: EZ, RENT: RENT, SUB: SUB },
      kinds: K, conn: CONN, connKinds: CONN_KINDS, rel2kind: REL2KIND, dashmap: DASHMAP, method: METHOD, bandpal: BANDPAL, feband: FEBAND, kradf: KRADF, tiers: TIERS,
      counts: counts, fixture: o.fixture, head: C4.head || null, budget: BUDGET, scale: o.scale, layout: o.layout, tier: (o.tier == null ? (nodes.length > BUDGET ? 0 : 3) : o.tier), budgetHit: (o.tier == null && nodes.length > BUDGET) ? { nodes: nodes.length, budget: BUDGET } : null, heat: heat, warnings: warn,
      tierOf: tierOf, bandOf: bandOf, colorOf: colorOf, seedPositions: seedPositions, applyBaked: applyBaked, force: force, qs: qs, methodOf: methodOf,
      setHeat: function (be, fe) { heat.be = !!be; heat.fe = !!fe; }, handlers: handlers };
    return feed;
  }
  function tint(hex, t) { var c = parseInt(hex.slice(1), 16), r = c >> 16 & 255, g = c >> 8 & 255, b = c & 255; r += (255 - r) * t; g += (255 - g) * t; b += (255 - b) * t; return '#' + ((1 << 24) + ((r | 0) << 16) + ((g | 0) << 8) + (b | 0)).toString(16).slice(1); }

  /* ── selfTest: the count law, stated ONCE and checked against the raw feed ─────────────────────────────────────── */
  function selfTest(feed, C4, LV, o) {
    var checks = [];
    function chk(name, ok, detail) { checks.push({ name: name, ok: !!ok, detail: detail || '' }); }
    var ids = {}; feed.nodes.forEach(function (n) { ids[n.id] = (ids[n.id] || 0) + 1; }); var dup = Object.keys(ids).filter(function (i) { return ids[i] > 1; });
    chk('ids unique', dup.length === 0, dup.slice(0, 3).join(', '));
    var P0 = (o.fe && C4.fe && C4.fe.pieces) ? C4.fe.pieces : [], cand = 0;   /* the LINK LAW: every candidate wire either drew or was counted dropped */
    Object.keys(C4.l2 || {}).forEach(function (e) { cand += ((C4.l2[e] || {}).edges || []).length; }); cand += (C4.cross_edges || []).length;
    if (o.fe) (C4.fe && C4.fe.edges || []).forEach(function (e) { if (P0[e[0]] && P0[e[1]]) cand++; });
    if (o.fn && LV && LV.fn_nodes) { cand += (LV.fn_edges || []).length + (LV.schema_edges || []).length; feed.nodes.forEach(function (n) { if (n.kind === 'function' && n.access && n.access.ops) n.access.ops.forEach(function (op) { if (op.model && feed.byId['model:' + op.model]) cand++; }); if (n.kind === 'endpoint' && n.fn && feed.byId[String((n.det || {}).file || '').split(':')[0] + '#' + n.fn]) cand++; }); }
    if (o.inject) cand++;
    if (!/^x\d+$/.test(o.scale || '')) chk('link law: candidates = drawn + dropped', feed.links.length + feed.counts.droppedLinks === cand, feed.links.length + ' + ' + feed.counts.droppedLinks + ' vs ' + cand);
    if (o.fn && LV && LV.fn_nodes && LV.fn_nodes.length) chk('handler wires resolve (det.file#fn)', feed.counts.handlers > 0 && feed.links.filter(function (l) { return l.rel === 'handler'; }).length === feed.counts.handlers, feed.counts.handlers + ' handler wires');
    chk('no wire dropped on a clean feed', o.fn || o.inject || /^x\d+$/.test(o.scale || '') || feed.counts.droppedLinks === 0, feed.counts.droppedLinks + ' dropped');
    if (o.scale === 'core') o = Object.assign({}, o, { fe: false, fn: false });
    if (!/^x\d+$/.test(o.scale || '')) {
      var l2 = {}; Object.keys(C4.l2 || {}).forEach(function (e) { ((C4.l2[e] || {}).nodes || []).forEach(function (p) { l2[p.id] = 1; }); });
      var fe = (o.fe && C4.fe && C4.fe.pieces) ? C4.fe.pieces : [], feIds = {}; fe.forEach(function (p) { feIds[p.id] = 1; });
      var web = {}; fe.forEach(function (p) { if (p.screen && l2[p.screen]) web[p.screen] = 1; });
      var fn = (o.fn && LV && LV.fn_nodes) ? LV.fn_nodes.filter(function (f) { return !l2[f.id] && !feIds[f.id]; }).length : 0;
      var expected = Object.keys(l2).length + fe.length - Object.keys(web).length + fn + (o.inject ? 1 : 0);
      chk('count law: L2(dedup) + fe − absorbed web + fn (+inject) = nodes', feed.nodes.length === expected, feed.nodes.length + ' vs ' + expected + ' (L2 ' + Object.keys(l2).length + ' · fe ' + fe.length + ' · absorbed ' + Object.keys(web).length + ' · fn ' + fn + ')');
    }
    chk('unknown kind kept, never dropped', !o.inject || (feed.byId['zz:lab-injected'] && feed.byId['zz:lab-injected'].generic && feed.byId['zz:lab-injected'].kind === 'zz-unknown-kind'));
    chk('fe=0 yields no fe node/link', o.fe || (feed.nodes.every(function (n) { return !n.fe; }) && feed.links.every(function (l) { return !l.fe; })));
    chk('method never defaults to GET', feed.nodes.every(function (n) { return n.kind !== 'endpoint' || n.m === null || /^(GET|POST|PUT|PATCH|DELETE|BOOT|TASK)$/.test(n.m); }));
    chk('tier presets hold (no function below T2, no leaf component below T3, a generic kind at T0)', feed.nodes.every(function (n) { return (n.kind !== 'function' || n.tier >= 2) && !(n.fe && n.feClass === 'leaf' && n.tier < 3) && (!n.generic || n.tier === 0); }));
    var again = build(C4, LV, o); var sig = function (f) { return f.nodes.map(function (n) { return n.id + '|' + n.ent + '|' + n.tier; }).join(';') + '#' + f.links.map(function (l) { return l.source + '>' + l.target + '|' + l.rel; }).join(';'); };
    chk('deterministic (build twice, identical)', sig(again) === sig(feed));
    feed.seedPositions(1); var s1 = feed.nodes.map(function (n) { return n.sx + ',' + n.sy + ',' + n.sz; }).join(';'); feed.seedPositions(1); var s2 = feed.nodes.map(function (n) { return n.sx + ',' + n.sy + ',' + n.sz; }).join(';');
    chk('seed positions deterministic + finite', s1 === s2 && feed.nodes.every(function (n) { return isFinite(n.sx) && isFinite(n.sy) && isFinite(n.sz); }));
    return { ok: checks.every(function (c) { return c.ok; }), checks: checks, counts: feed.counts, warnings: feed.warnings };
  }

  var C4 = window.GABE_C4, LV = window.GABE_LEVELS || null;
  if (!C4) { window.GABE_FEED_ERR = 'window.GABE_C4 missing — feed-loader.js must run first'; return; }
  var FX = window.GABE_FIXTURE || { name: 'example', fn: false };
  var _tq = qs('tier', null);
  var o = { fixture: FX.name, fn: qs('fn', FX.fn ? '1' : '0') === '1', fe: qs('fe', '1') !== '0', scale: qs('scale', 'full'), layout: qs('layout', 'live'), tier: _tq == null ? null : Math.max(0, Math.min(3, +_tq | 0)), inject: qs('inject', '0') === '1', heat: qs('heat', '1') !== '0', feHeat: qs('feheat', '0') === '1' };
  var feed = build(C4, LV, o);
  if (o.layout === 'baked') { var bk = feed.applyBaked(); feed.baked = bk; if (!bk.hit) { feed.layout = 'live'; feed.warnings.push(bk.why || ('?layout=baked asked but no window.GABE_BAKED[' + o.fixture + '] positions — live layout used (say so on the page)')); } }
  feed.selfTest = function () { return selfTest(feed, C4, LV, o); };
  feed.opts = o;
  window.GABE_FEED = feed;
  if (feed.warnings.length) { try { console.warn('[adapter] ' + feed.warnings.join(' · ')); } catch (e) { /* no console */ } }
})();
