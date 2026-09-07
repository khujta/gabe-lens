/* scorecard.js — the ONE instrument every lab page wears (a superset of the sweeps' lab-common.js contract, so the
   folded records' pages would still probe). Three things:
     1. window.__LAB — the machine-readable result the probe reads (ready · counts · timings · draws · notes · errors)
     2. LAB.* — mark/set/note/hud/fps/panel/score/ready — the page-side API
     3. window.LABG — the PROBE SURFACE a page registers via LAB.graph({...}) — the plan's row 24:
          nodes, links      the adapter's arrays as drawn (ids as link ends)
          byId              id → node
          setTier(t)        re-evaluate visibility WITHOUT relayout (0..3); returns the visible node count
          visible()         number of nodes currently drawn
          positions()       {id:[x,y,z]} for every drawn node (2D pages give z=0)
          screenOf(id)      {x,y} CSS pixels of a node's centre, or null
          pick(x,y)         the node id under a CSS pixel (the page's own pick pass), or null
          pickLink(x,y)     the link index under a pixel, or null (null-only pages record the row as lost)
          stats()           {calls, triangles, geometries, textures} for the last frame (engine-specific; null when unknown)
          settled           true once the layout engine's OWN stop signal fired (baked layouts: true at boot)
   No library dependency. The probe fails a page that never calls LAB.ready(). */
(function () {
  var HUD = null, SCORE = null, t0 = performance.now();
  var L = window.__LAB = {
    lib: '', ver: '', page: location.pathname.replace(/.*\//, ''), feed: null, scale: null, layout: null, tier: null,
    boot_ms: null, first_frame_ms: null, settle_ms: null, layout_ms: null,
    nodes: 0, links: 0, drawn: 0, fps: null, frame_ms: null, draws: null, tris: null, geos: null, texs: null,
    err: [], ready: false, notes: {}, matrix: []
  };
  window.addEventListener('error', function (e) { L.err.push(String(e.message)); });
  function el(t, c, x) { var d = document.createElement(t); if (c) d.className = c; if (x != null) d.textContent = x; return d; }
  var ORDER = ['lib', 'ver', 'feed', 'scale', 'layout', 'tier', 'nodes', 'links', 'drawn', 'boot_ms', 'first_frame_ms', 'settle_ms',
    'fps', 'frame_ms', 'draws', 'tris', 'geos', 'texs', 'heap_mb', 'purity', 'pick_ms', 'pick_ok', 'tier_ms', 'tier_static', 'err'];
  function fmt(v) { if (v == null) return '—'; if (Array.isArray(v)) return v.length ? v.length + ' ✗' : '0'; if (typeof v === 'number') return (Math.round(v * 100) / 100).toString(); return String(v); }
  window.LAB = {
    qs: function (k, d) { var m = new RegExp('[?&]' + k + '=([^&]*)').exec(location.search); return m ? decodeURIComponent(m[1]) : d; },
    mark: function (k) { L[k] = +(performance.now() - t0).toFixed(1); },
    set: function (k, v) { L[k] = v; if (SCORE) LAB.score(); },
    note: function (k, v) { L.notes[k] = v; },
    /* the must-survive MATRIX rows this page claims: [label, 'free'|'built'|'lost'|'na', how]. The probe records them
       beside the measured columns; a 'free'/'built' row that the probe can check (picking, tier static, hulls) is CHECKED. */
    matrix: function (rows) { L.matrix = rows.map(function (r) { return { row: r[0], state: r[1], how: r[2] || '' }; }); },
    panel: function (opts) {
      var wrap = el('div', 'lab-panel');
      wrap.innerHTML = '<div class="lp-h"><b>' + opts.lib + '</b> <span class="lp-v">' + (opts.ver || '') + '</span></div>';
      var meta = el('div', 'lp-meta');
      meta.innerHTML = '<div>bundle <b>' + (opts.bundle || '?') + '</b></div><div>licence <b>' + (opts.license || '?') + '</b></div>' +
        (opts.role ? '<div>role <b>' + opts.role + '</b></div>' : '');
      wrap.appendChild(meta);
      HUD = el('div', 'lp-hud'); wrap.appendChild(HUD);
      var ul = el('div', 'lp-list');
      (opts.checklist || []).forEach(function (r) {
        var li = el('div', 'lp-row ' + r[1]);
        li.appendChild(el('span', 'lp-dot')); li.appendChild(el('span', 'lp-k', r[0])); li.appendChild(el('span', 'lp-d', r[2] || ''));
        ul.appendChild(li);
      });
      wrap.appendChild(ul);
      if (opts.verdict) { var v = el('div', 'lp-verdict'); v.innerHTML = opts.verdict; wrap.appendChild(v); }
      document.body.appendChild(wrap);
      L.lib = opts.lib; L.ver = opts.ver || '';
      if (opts.checklist) LAB.matrix(opts.checklist);
      if (!SCORE) { SCORE = el('pre', ''); SCORE.id = 'score'; document.body.appendChild(SCORE); }
      LAB.score();
      return wrap;
    },
    hud: function (o) {
      if (!HUD) return;
      HUD.innerHTML = Object.keys(o).map(function (k) { return '<div><span>' + k + '</span><b>' + o[k] + '</b></div>'; }).join('');
    },
    /* the fixed-order scorecard: a screenshot of the page carries its numbers */
    score: function (extra) {
      if (extra) Object.assign(L, extra);
      if (!SCORE) { SCORE = el('pre', ''); SCORE.id = 'score'; document.body.appendChild(SCORE); }
      SCORE.innerHTML = ORDER.map(function (k) { return '<span class="k">' + (k + '            ').slice(0, 14) + '</span>' + fmt(L[k]); }).join('\n');
    },
    fps: (function () {
      var last = performance.now(), acc = 0, n = 0, cur = 0, ms = 0;
      return function () {
        var t = performance.now(), d = t - last; last = t; acc += d; n++;
        if (acc > 500) { cur = Math.round(1000 / (acc / n)); ms = +(acc / n).toFixed(2); acc = 0; n = 0; L.fps = cur; L.frame_ms = ms; if (SCORE) LAB.score(); }
        return { fps: cur, ms: ms };
      };
    })(),
    graph: function (g) { window.LABG = g; return g; },
    ready: function (extra) {
      Object.assign(L, extra || {});
      var F = window.GABE_FEED; if (F) { L.feed = F.fixture; L.scale = F.scale; L.layout = F.layout; if (L.nodes === 0) L.nodes = F.nodes.length; if (L.links === 0) L.links = F.links.length; }
      L.ready = true; window.__LAB_READY = true; document.title = '[ready] ' + document.title; LAB.score();
    }
  };
})();
