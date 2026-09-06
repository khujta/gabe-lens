/* ─────────────────────────────────────────────────────────────────────────
   graph-grammar.js — the LEVEL-LAB GRAMMAR's pure pieces, shared by the two
   codebase-graph stations (codebase-graph.html · codebase-archive.html).

   Extracted at the recorded trigger ("a shared renderer when the archive
   station adopts the same grammar"): everything here is a PURE builder —
   icon geometry, halo-trimmed bowed wires, entity-gradient strokes, flow
   dots, lane bows, two-row labels, the panel DOSSIER sections
   (PURPOSE · STRUCTURE · SIGNATURE · TESTED-BY) and the typed id-card chips.
   No host state: line-style multipliers, drag flags and icon-set choices are
   passed IN per call. The STATEFUL selection engine (SELREG · BFS · peek ·
   nav trail) deliberately stays per-host — it is entangled with each
   station's click model; extracting it is the remaining DRY debt.

   Host contract: var GG = window.GABE_GRAPH_GRAMMAR();  (no arguments)
     GG.ICONSETS[set].{model,schema,fn,ep}(g, r, …)   Lucide default lives in
                                                       the HOST's ICONSET var
     GG.halo(g)                                        14px wire-departure ring
     GG.curve(x1,y1,x2,y2,bow)                         bow is PRE-multiplied by
                                                       the host's LINE_MULT
     GG.kindPath(layer,a,b,kind,off)                   off pre-multiplied too
     GG.edgeGradient(defs,a,c,sCol,tCol) → url id      source→target blend
     GG.flowDots(host,pathEl,fill,staticNow) → [dots]  direction = motion;
                                                       staticNow freezes (drag)
     GG.lanes() → {bow(kFrom,kTo,bow)}                 fresh per render
     GG.rows2 / GG.twoRowLabel(g,txt,x,y)              ≤10-char label rows
     GG.esc / GG.trunc / GG.rnd
     GG.dossierHTML(det, docLabel, noun) + the individual sections — HTML
       strings over the emitter's per-node `det` block, honest-empty each
     GG.chips.{kindChip,epChip,dtChip,idrow,moreChip,icoSvg,tyFamily,…} — the
       typed id-card language (mirrors sim-panel.js's internal copy)

   Battery: tests/codebase-graph (contract pins read THIS file).
   ───────────────────────────────────────────────────────────────────────── */
(function () {
  "use strict";
  var NS = "http://www.w3.org/2000/svg";

  window.GABE_GRAPH_GRAMMAR = function () {
    function E(tag, attrs) { var e = document.createElementNS(NS, tag);
      if (attrs) for (var k in attrs) e.setAttribute(k, attrs[k]); return e; }
    function esc(s) { return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
    function trunc(s, n) { s = String(s); return s.length > n ? s.slice(0, n - 1) + "…" : s; }
    function rnd(v) { return Math.round(v * 100) / 100; }   // kill 1e-14 float dust

    var METHOD = { GET: "var(--m-get)", POST: "var(--m-post)", PUT: "var(--m-put)",
                   PATCH: "var(--m-put)", DELETE: "var(--m-delete)",
                   BOOT: "var(--m-boot)", TASK: "var(--m-task)" };   /* BOOT (lifespan root) + TASK (a worker entrypoint dispatched by name) — the ONE method roster every station shares (legend pass 2026-09-06) */
    /* a TASK endpoint's mark: a QUEUE — three stacked jobs, the last one leaving to a worker (the universe's badge idea, in SVG) */
    function taskMark(g, r, col) {
      g.appendChild(E("circle", { r: r, fill: col, stroke: "var(--panel)", "stroke-width": "1.6" }));
      g.appendChild(E("path", { d: "M-3 -3 L2.4 -3 M-3 0 L2.4 0 M-3 3 L2.4 3 M1.2 1.6 L3 3 L1.2 4.4",
        fill: "none", stroke: "#fff", "stroke-width": "1.1", "stroke-linecap": "round", transform: "scale(" + (r / 6) + ")" })); }
    var ICO_SCHEMA = 'M8 3H7a2 2 0 0 0-2 2v5a2 2 0 0 1-2 2 2 2 0 0 1 2 2v5c0 1.1.9 2 2 2h1 M16 21h1a2 2 0 0 0 2-2v-5c0-1.1.9-2 2-2a2 2 0 0 1-2-2V5a2 2 0 0 0-2-2h-1';
    var ICO_FN = 'M9 17c2 0 3-1 3-3v-4c0-2 1-3 3-3 M9 11h6';
    /* the three icon sets — byte-identical to the level lab (round 46 parity) */
    var ICONSETS = {
      classic: {
        model: function (g, r, col) { var h = r * 1.5, w = r * 1.7;
          g.appendChild(E("path", { d: "M" + (-w / 2) + " " + (-h / 2 + 3) + " v" + (h - 6) + " a" + (w / 2) + " 4 0 0 0 " + w + " 0 v-" + (h - 6),
            fill: col, "fill-opacity": "0.9", stroke: "var(--panel)", "stroke-width": "1.4" }));
          g.appendChild(E("ellipse", { cx: 0, cy: -h / 2 + 3, rx: w / 2, ry: 4, fill: col, stroke: "var(--panel)", "stroke-width": "1.4" })); },
        schema: function (g, r, col) { g.appendChild(E("circle", { r: r + 4, fill: "transparent" }));
          g.appendChild(E("path", { d: ICO_SCHEMA, fill: "none", stroke: col, "stroke-width": "2.4",
            "stroke-linecap": "round", "stroke-linejoin": "round",
            transform: "translate(" + (-r) + "," + (-r) + ") scale(" + (2 * r / 24) + ")" })); },
        fn: function (g, r, col, handler) { g.appendChild(E("circle", { r: r + 4, fill: "transparent" }));
          g.appendChild(E("path", { d: ICO_FN, fill: "none", stroke: col,
            "stroke-width": handler ? "3.1" : "2.2",
            "stroke-linecap": "round", "stroke-linejoin": "round",
            transform: "translate(" + (-r * 1.2) + "," + (-r * 1.2) + ") scale(" + (2.4 * r / 24) + ")" })); },
        ep: function (g, r, method) { var col = METHOD[method] || "var(--muted)"; if (method === "TASK") { taskMark(g, r, col); return; }
          g.appendChild(E("circle", { r: r, fill: col, stroke: "var(--panel)", "stroke-width": "1.6" }));
          g.appendChild(E("path", { d: "M1.4 " + (-r * 0.62) + " L" + (-r * 0.5) + " 0.6 L0.2 0.6 L-1 " + (r * 0.66) + " L" + (r * 0.56) + " -0.4 L0 -0.4 Z",
            fill: "#fff", transform: "scale(" + (r / 6) + ")" })); }
      },
      lucide: {
        model: function (g, r, col) { var k = 2.2 * r / 24, tf = "translate(" + (-r * 1.1) + "," + (-r * 1.1) + ") scale(" + k + ")";
          g.appendChild(E("circle", { r: r + 4, fill: "transparent" }));
          g.appendChild(E("ellipse", { cx: 12, cy: 5, rx: 9, ry: 3, fill: "none", stroke: col, "stroke-width": "2", transform: tf }));
          g.appendChild(E("path", { d: "M3 5v14a9 3 0 0 0 18 0V5 M3 12a9 3 0 0 0 18 0",
            fill: "none", stroke: col, "stroke-width": "2", "stroke-linecap": "round", transform: tf })); },
        schema: function (g, r, col) { g.appendChild(E("circle", { r: r + 4, fill: "transparent" }));
          g.appendChild(E("path", { d: ICO_SCHEMA, fill: "none", stroke: col, "stroke-width": "2",
            "stroke-linecap": "round", "stroke-linejoin": "round",
            transform: "translate(" + (-r) + "," + (-r) + ") scale(" + (2 * r / 24) + ")" })); },
        fn: function (g, r, col, handler) { var k = 2.4 * r / 24, tf = "translate(" + (-r * 1.2) + "," + (-r * 1.2) + ") scale(" + k + ")";
          g.appendChild(E("circle", { r: r + 4, fill: "transparent" }));
          g.appendChild(E("rect", { x: 3, y: 3, width: 18, height: 18, rx: 4, fill: "none", stroke: col,
            "stroke-width": handler ? "2.6" : "1.8", transform: tf }));
          g.appendChild(E("path", { d: ICO_FN, fill: "none", stroke: col, "stroke-width": "2",
            "stroke-linecap": "round", "stroke-linejoin": "round", transform: tf })); },
        ep: function (g, r, method) { var col = METHOD[method] || "var(--muted)"; if (method === "TASK") { taskMark(g, r, col); return; }
          g.appendChild(E("circle", { r: r + 1, fill: "none", stroke: col, "stroke-width": "2" }));
          g.appendChild(E("path", { d: "M13 2 3 14h9l-1 8 10-12h-9l1-8z", fill: col,
            transform: "translate(" + (-r * 0.75) + "," + (-r * 0.75) + ") scale(" + (1.5 * r / 24) + ")" })); }
      },
      solid: {
        model: function (g, r, col) { var h = r * 1.5, w = r * 1.7;
          g.appendChild(E("path", { d: "M" + (-w / 2) + " " + (-h / 2 + 3) + " v" + (h - 6) + " a" + (w / 2) + " 4 0 0 0 " + w + " 0 v-" + (h - 6), fill: col }));
          g.appendChild(E("ellipse", { cx: 0, cy: -h / 2 + 3, rx: w / 2, ry: 4, fill: col }));
          g.appendChild(E("ellipse", { cx: 0, cy: -h / 2 + 3, rx: w / 3.2, ry: 2.2, fill: "var(--panel)", "fill-opacity": "0.5" })); },
        schema: function (g, r, col) { g.appendChild(E("rect", { x: -r, y: -r, width: 2 * r, height: 2 * r, rx: 5, fill: col }));
          g.appendChild(E("path", { d: ICO_SCHEMA, fill: "none", stroke: "#fff", "stroke-width": "2.2",
            "stroke-linecap": "round", "stroke-linejoin": "round",
            transform: "translate(" + (-r * 0.75) + "," + (-r * 0.75) + ") scale(" + (1.5 * r / 24) + ")" })); },
        fn: function (g, r, col, handler) { g.appendChild(E("circle", { r: r + 1.5, fill: col }));
          if (handler) g.appendChild(E("circle", { r: r + 3.5, fill: "none", stroke: col, "stroke-width": "1.6" }));
          g.appendChild(E("path", { d: ICO_FN, fill: "none", stroke: "#fff", "stroke-width": "2.4",
            "stroke-linecap": "round", "stroke-linejoin": "round",
            transform: "translate(" + (-r * 0.85) + "," + (-r * 0.85) + ") scale(" + (1.7 * r / 24) + ")" })); },
        ep: function (g, r, method) { var col = METHOD[method] || "var(--muted)"; if (method === "TASK") { taskMark(g, r, col); return; }
          g.appendChild(E("rect", { x: -r - 1, y: -r - 1, width: 2 * r + 2, height: 2 * r + 2, rx: 6, fill: col }));
          g.appendChild(E("path", { d: "M1.4 " + (-r * 0.62) + " L" + (-r * 0.5) + " 0.6 L0.2 0.6 L-1 " + (r * 0.66) + " L" + (r * 0.56) + " -0.4 L0 -0.4 Z",
            fill: "#fff", transform: "scale(" + (r / 6) + ")" })); }
      }
    };

    var HALO_R = 14;   // the element circle: wires START at its edge, never the icon
    function halo(g) { g.insertBefore(E("circle", { class: "halo", r: HALO_R }), g.firstChild); }
    /* chord-trimmed quadratic bow — bow arrives PRE-multiplied by the host's
       LINE_MULT (Direct ×0.25 · Bowed ×2), so one function serves both defaults */
    function curve(x1, y1, x2, y2, bow) {
      var dx = x2 - x1, dy = y2 - y1, d = Math.hypot(dx, dy) || 1;
      if (d > 3 * HALO_R) { var ux = dx / d, uy = dy / d;
        x1 = x1 + ux * HALO_R; y1 = y1 + uy * HALO_R; x2 = x2 - ux * HALO_R; y2 = y2 - uy * HALO_R;
        dx = x2 - x1; dy = y2 - y1; d = Math.hypot(dx, dy) || 1; }
      var mx = (x1 + x2) / 2 - dy / d * bow, my = (y1 + y2) / 2 + dx / d * bow;
      return "M" + rnd(x1) + " " + rnd(y1) + " Q " + rnd(mx) + " " + rnd(my) + " " + rnd(x2) + " " + rnd(y2); }
    function kindPath(layer, a, b, kind, off) {
      var dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy) || 1, ux = dx / d, uy = dy / d;
      var mx = (a.x + b.x) / 2 - uy * off, my = (a.y + b.y) / 2 + ux * off;
      var p = E("path", { class: "e-" + kind, d: "M" + rnd(a.x) + " " + rnd(a.y) + " Q " + rnd(mx) + " " + rnd(my) + " " + rnd(b.x) + " " + rnd(b.y) });
      layer.appendChild(p); return p; }
    var _uid = 0;
    function edgeGradient(defs, a, c, sCol, tCol) {
      var id = "gg" + (++_uid);
      var g = E("linearGradient", { id: id, gradientUnits: "userSpaceOnUse",
        x1: rnd(a.x), y1: rnd(a.y), x2: rnd(c.x), y2: rnd(c.y) });
      g.appendChild(E("stop", { offset: "0%", "stop-color": sCol }));
      g.appendChild(E("stop", { offset: "100%", "stop-color": tCol }));
      defs.appendChild(g); return id; }
    var REDUCED = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
    /* direction = MOTION, never arrowheads (round 30); staticNow = the host is
       mid-drag (re-render per pointermove — no SMIL restart churn) */
    function flowDots(host, pathEl, fill, staticNow) {
      var out = [], len = 0; try { len = pathEl.getTotalLength(); } catch (_) { return out; }
      if (!len) return out;
      if (!pathEl.id) pathEl.id = "ggf" + (++_uid);
      var dur = Math.max(1.6, len / 55), n = len > 260 ? 2 : 1;
      for (var i = 0; i < n; i++) {
        var dot = E("circle", { class: "flowdot", r: "2.1", fill: fill });
        if (REDUCED || staticNow) { var q = pathEl.getPointAtLength(len * 0.62);
          dot.setAttribute("cx", rnd(q.x)); dot.setAttribute("cy", rnd(q.y));
        } else {
          var am = E("animateMotion", { dur: dur.toFixed(2) + "s", repeatCount: "indefinite",
            begin: (-dur * i / n).toFixed(2) + "s", rotate: "none" });
          var mp = E("mpath"); mp.setAttribute("href", "#" + pathEl.id);
          am.appendChild(mp); dot.appendChild(am);
        }
        host.appendChild(dot); out.push(dot);
      }
      return out; }
    /* a bidirectional pair rides two LANES — fresh registry per render */
    function lanes() { var _l = {};
      return { bow: function (kFrom, kTo, bow) {
        var k = kFrom < kTo ? kFrom + "›" + kTo : kTo + "›" + kFrom, rec = _l[k];
        if (rec === undefined) { _l[k] = { dir: kFrom, sign: bow < 0 ? -1 : 1 }; return bow; }
        return (rec.dir === kFrom ? rec.sign : -rec.sign) * Math.abs(bow); } }; }
    function rows2(s, max) { s = String(s); if (s.length <= max) return [s];
      var r1 = s.slice(0, max), rest = s.slice(max);
      return [r1, rest.length <= max ? rest : rest.slice(0, max - 1) + "…"]; }
    function twoRowLabel(g, txt, x, y) {
      rows2(txt, 10).forEach(function (r, i) {
        var e = E("text", { class: "plabel", x: x, y: y + i * 10 });
        e.textContent = r; g.appendChild(e); }); }

    /* ── the panel DOSSIER — HTML strings over the emitter's `det` block,
       every section honest-empty (no field, no section; no det, no dossier) ── */
    function _psvg(inner, w) { return "<svg viewBox='0 0 24 24' width='" + (w || 15) + "' height='" + (w || 15) + "'>" + inner + "</svg>"; }
    function _sect(icon, label) { return "<div class='k2'>" + icon + "<span>" + label + "</span></div>"; }
    function docSect(det, label) {
      if (!det || !det.doc) return "";
      return _sect(_psvg("<path d='M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z' fill='none' stroke='var(--muted)' stroke-width='1.7'/><path d='M14 2v5h5 M16 13H8 M16 17H8' fill='none' stroke='var(--muted)' stroke-width='1.7'/>"), label)
        + "<div class='note'>" + esc(det.doc) + "</div>"; }
    function fileRowHTML(det) {
      if (!det || !det.file) return "";
      var over = det.flines && det.flines > 800;   // the 800 CODE budget, report-never-gate
      return "<div class='row'><span class='k'>file</span><span class='v' style='font-weight:500'>"
        + "<code style='font-family:ui-monospace,Menlo,Consolas,monospace;font-size:0.786rem'>" + esc(det.file) + "</code>"
        + (det.flines ? " <span style='color:" + (over ? "#e5484d" : "var(--muted)") + "'>" + det.flines + " ln" + (over ? " · over the 800 budget" : "") + "</span>" : "")
        + "</span></div>"; }
    function usageRowHTML(det) {
      var u = det && det.usage; if (!u) return "";
      var bar = function (n, col) { return "<span class='pbar' style='width:" + Math.min(6 * (n || 0), 84) + "px;background:" + col + "'></span>" + (n || 0); };
      var parts = [];
      if (u.api != null)      parts.push(bar(u.api, "var(--c-fn-services)") + " api");
      if (u.fk_in != null)    parts.push(bar(u.fk_in, "var(--c-fn-services)") + " fk-in");
      if (u.internal != null) parts.push(bar(u.internal, "var(--accent)") + " internal");
      return parts.length ? "<div class='row'><span class='k'>usage</span><span class='v'>" + parts.join(" &nbsp; ") + "</span></div>" : ""; }
    function structSect(det, noun) {
      if (!det || !det.cols || !det.cols.length) return "";
      noun = noun || "column";
      var uq = {}; (det.uqs || []).forEach(function (u) { uq[u] = 1; });
      var h = _sect(_psvg("<path d='M3 5h18v14H3z M3 10h18 M9 5v14' fill='none' stroke='var(--muted)' stroke-width='1.7'/>"),
        "structure (" + (det.cols.length + (det.cols_more || 0)) + " " + noun + "s)");
      h += "<table class='ptab'><tr><th>" + noun + "</th><th class='nw'>type</th><th class='nw'>default</th></tr>";
      det.cols.forEach(function (c) {
        h += "<tr><td>" + esc(c[0]) + (uq[c[0]] ? "<span class='uqchip'>unique</span>" : "") + "</td>"
          + "<td class='ty'>" + esc(c[1] || "") + "</td><td style='color:var(--muted)'>" + esc(c[2] || "") + "</td></tr>"; });
      h += "</table>";
      if (det.cols_more) h += "<div class='pmore'>+" + det.cols_more + " more " + noun + "(s)</div>";
      return h; }
    function fkSect(det) {
      if (!det || !det.fks || !det.fks.length) return "";
      var h = _sect(_psvg("<path d='M9 12h6 M5 12a4 4 0 0 1 4-4h1 M19 12a4 4 0 0 1-4 4h-1' fill='none' stroke='var(--muted)' stroke-width='1.7'/>"),
        "stored as (foreign keys)");
      h += "<table class='ptab'><tr><th>fk column</th><th>points at</th></tr>";
      det.fks.forEach(function (f) { h += "<tr><td>" + esc(f[0]) + "</td><td class='ty'>" + esc(f[1]) + "</td></tr>"; });
      return h + "</table>"; }
    function sigSect(det) {
      var s = det && det.sig; if (!s) return "";
      var h = _sect(_psvg("<path d='M9 17c2 0 3-1 3-3v-4c0-2 1-3 3-3 M9 11h6' fill='none' stroke='var(--muted)' stroke-width='2'/>"),
        "signature");
      if (s.returns)
        h += "<table class='ptab'><tr><th>part</th><th class='nw'>type</th><th class='nw'>role</th></tr>"
          + "<tr><td>return</td><td class='ty'>" + esc(s.returns) + "</td><td>out</td></tr></table>";
      h += "<div class='pmore'>" + (s.async ? "async · " : "") + (s.lines ? s.lines + " lines · " : "")
        + "params live in the center's render pass</div>";
      return h; }
    function stateCls(s) { return s === "pass" ? "st-pass"
      : (s === "fail" || s === "red" || s === "error") ? "st-fail" : "st-skip"; }   // skip is not a failure
    function casesSect(det) {
      if (!det || !((det.cases || []).length || (det.case_files || []).length)) return "";
      var n = (det.cases || []).length + (det.cases_more || 0);
      var h = "";
      if (n) {
        h += _sect(_psvg("<rect x='3' y='7' width='18' height='11' rx='5.5' fill='none' stroke='var(--muted)' stroke-width='1.7'/><path d='M8.5 12.5 l2.4 2.4 L15.5 10' fill='none' stroke='var(--muted)' stroke-width='1.7'/>"),
          "tested by (" + n + ")");
        h += "<table class='ptab'><tr><th class='nw'>kind</th><th>case</th><th class='nw'>state</th></tr>";
        det.cases.forEach(function (c) {
          h += "<tr><td>" + esc(c.corpus || "") + "</td>"
            + "<td>" + (c.cid ? "<span class='cid'>" + esc(c.cid) + "</span> " : "") + esc(c.name || "") + "</td>"
            + "<td class='" + stateCls(c.state) + "'>" + esc(c.state || "") + "</td></tr>"; });
        h += "</table>";
        if (det.cases_more) h += "<div class='pmore'>+" + det.cases_more + " more case(s) — the matrix carries the full ledger</div>";
      }
      (det.case_files || []).forEach(function (f) {
        h += "<div class='pmore'>route-file coverage · " + esc(f.corpus || "") + " · " + esc(f.name || "") + "</div>"; });
      return h; }
    function journeysSect(det) {
      // cross-entity test JOURNEYS (criterion A) — the traveling test-chip, per element. det carries no
      // kind, but only endpoints get sig/status, so that is the honest entry-vs-stop tell.
      var js = det && det.test_journeys; if (!js || !js.length) return "";
      var n = js.length + (det.test_journeys_more || 0);
      var entry = !!(det.sig || det.status);
      var h = _sect(_psvg("<circle cx='6' cy='19' r='3' fill='none' stroke='var(--muted)' stroke-width='1.7'/><path d='M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15' fill='none' stroke='var(--muted)' stroke-width='1.7'/><circle cx='18' cy='5' r='3' fill='none' stroke='var(--muted)' stroke-width='1.7'/>"),
        "journeys (" + n + ")");
      h += "<div class='pmore'>" + (entry ? "entry · a cross-entity test starts here and travels out"
                                          : "a stop · reached by a cross-entity test that spans other entities") + "</div>";
      h += "<table class='ptab'><tr><th class='nw'>test</th><th class='nw'>corpus</th><th>travels</th><th class='nw'>comp</th></tr>";
      js.forEach(function (j) {
        h += "<tr><td>" + (j.cid ? "<span class='cid'>" + esc(j.cid) + "</span>" : "") + "</td>"
          + "<td>" + esc(j.corpus || "") + "</td>"
          + "<td>" + (j.entities || []).map(function (e) { return esc(e); }).join(" · ") + "</td>"
          + "<td class='nw'>" + (j.comp || 0) + "</td></tr>"; });
      h += "</table>";
      if (det.test_journeys_more) h += "<div class='pmore'>+" + det.test_journeys_more + " more journey(s) — the full set lives in the graph</div>";
      return h; }
    function payloadSect(det) {
      // response PAYLOAD — the field-count of the resp contract (archmap has no request body).
      var p = det && det.payload; if (!p) return "";
      return _sect(_psvg("<path d='M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z' fill='none' stroke='var(--muted)' stroke-width='1.7'/><path d='m3.3 7 8.7 5 8.7-5 M12 22V12' fill='none' stroke='var(--muted)' stroke-width='1.7'/>"), "payload")
        + "<div class='pmore'>" + p.n + " field" + (p.n === 1 ? "" : "s") + " ferried · &rarr; <span class='cid'>" + esc(p.schema) + "</span> (response)</div>"; }
    function dossierHTML(det, docLabel, noun) {
      if (!det) return "";
      return docSect(det, docLabel) + sigSect(det) + payloadSect(det) + structSect(det, noun) + fkSect(det)
        + usageRowHTML(det) + fileRowHTML(det) + casesSect(det) + journeysSect(det); }

    /* ── the typed id-card chips (Tier 1) — one copy for both stations ── */
    var KIND_ICON = {
      fn: '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 17c2 0 3-1 3-3v-4c0-2 1-3 3-3"/><path d="M9 11h6"/>',
      endpoint: '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
      datatype: '<polyline points="4 7 4 4 20 4 20 7"/><line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="4" x2="12" y2="20"/>' };
    var KIND_CHIP = { fn: "#0f766e", endpoint: "#4c6ef5" };
    var METHOD_COLOR = { GET: "#16794c", POST: "#4338ca", PUT: "#b45309", PATCH: "#b45309", DELETE: "#d1443c", BOOT: "#8a8f98", TASK: "#a78bfa" };   /* the chip roster mirrors sim-panel.js METHOD_COLOR — pinned equal (review 2026-09-06) */
    var TYPE_CLS = { int: "num1", float: "num2", Decimal: "num2", Numeric: "num2", date: "tim1", time: "tim1",
      datetime: "tim2", str: "str1", Text: "str2", bytes: "str2", bool: "bool", dict: "json", list: "json",
      Any: "json", JSON: "json", Literal: "json", UUID: "id", uuid: "id" };
    function icoSvg(p) { return '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + p + '</svg>'; }
    function tyFamily(t) { var toks = String(t).split(/[^A-Za-z_]+/);
      for (var i = 0; i < toks.length; i++) { if (TYPE_CLS[toks[i]]) return TYPE_CLS[toks[i]]; } return null; }
    function kindChip(kind, label) { var c = KIND_CHIP[kind] || "#868e96";
      return "<span class='idchip' style='color:" + c + ";background:" + c + "1f'>" + icoSvg(KIND_ICON[kind]) + "<b>" + esc(trunc(label, 30)) + "</b></span>"; }
    function epChip(ep) { var mc = METHOD_COLOR[ep.m] || "#868e96", c = KIND_CHIP.endpoint;
      return "<span class='idchip' style='color:" + c + ";background:" + c + "1f' title='" + esc(ep.m + " " + ep.p + " → " + ep.fn + "()") + "'>"
        + icoSvg(KIND_ICON.endpoint) + "<span class='mth' style='color:" + mc + "'>" + esc(ep.m) + "</span><b>" + esc(ep.p) + "</b></span>"; }
    function dtChip(d) { var fam = tyFamily(d.t);
      return "<span class='idchip dt'>" + icoSvg(KIND_ICON.datatype) + "<b>" + esc(d.n) + "</b><span class='ty" + (fam ? " ty-" + fam : "") + "'>" + esc(d.t) + "</span></span>"; }
    function idrow(label, chips) { return chips ? "<div class='idrow'><div class='idlbl'>" + label + "</div><div class='idchips'>" + chips + "</div></div>" : ""; }
    function moreChip(arr, n) { return arr.length > n ? "<span class='idchip st'>+" + (arr.length - n) + " more</span>" : ""; }

    return {
      E: E, esc: esc, trunc: trunc, rnd: rnd, METHOD: METHOD,
      ICONSETS: ICONSETS, HALO_R: HALO_R, halo: halo,
      curve: curve, kindPath: kindPath, edgeGradient: edgeGradient,
      flowDots: flowDots, lanes: lanes, rows2: rows2, twoRowLabel: twoRowLabel,
      _psvg: _psvg, _sect: _sect,
      docSect: docSect, fileRowHTML: fileRowHTML, usageRowHTML: usageRowHTML,
      structSect: structSect, fkSect: fkSect, sigSect: sigSect,
      stateCls: stateCls, casesSect: casesSect, journeysSect: journeysSect,
      payloadSect: payloadSect, dossierHTML: dossierHTML,
      chips: { KIND_ICON: KIND_ICON, KIND_CHIP: KIND_CHIP, METHOD_COLOR: METHOD_COLOR,
               TYPE_CLS: TYPE_CLS, icoSvg: icoSvg, tyFamily: tyFamily,
               kindChip: kindChip, epChip: epChip, dtChip: dtChip,
               idrow: idrow, moreChip: moreChip }
    };
  };
})();
