/* ─────────────────────────────────────────────────────────────────────────
   sim-panel.js — the change-simulation DETAIL PANEL, renderer-agnostic.

   The right-hand panel of the change-simulation instrument (typed identifier
   chips · the per-piece lifecycle timeline · tests + evidence · the stage-wide
   summary). It is pure HTML-string construction over window.GABE_SIM + the
   current lifecycle stage — it never touches the SVG/graph, so the SAME code
   serves every renderer (the command-center station AND the arch-graph lab).

   Host contract — call GABE_SIM_PANEL(ctx) once, where ctx is:
     SIM          window.GABE_SIM (touched/blast/pieces/stages/evidence/…)
     entities     DATA.l1.nodes  (each {slug,label,counts})
     STAGE_COLOR  { red, execute, review, commit } hex
     KIND_COLOR   { endpoint, model, schema, external } hex
     detailId     id of the panel container div
     stageSegId   id of the Red|Execute|Review|Commit segmented control
     getStage()   → the current stage string          (read shared state)
     applyStage(s)  host sets curStage, toggles the stageSeg buttons, and
                    RE-RENDERS the graph                (renderer touchpoint #1)
     selectPiece(key|null)  host highlights that piece in the graph
                    (renderer touchpoint #2)

   Returns { openDetail, openEntityDetail, stageSummary, resetPanel } — the four
   surfaces the host wires to its click model.
   ───────────────────────────────────────────────────────────────────────── */
(function () {
  "use strict";

  window.GABE_SIM_PANEL = function (ctx) {
    var SIM = ctx.SIM;
    var ENT = ctx.entities || [];
    var STAGE_COLOR = ctx.STAGE_COLOR;
    var KIND_COLOR = ctx.KIND_COLOR ||
      { endpoint: "#4c6ef5", model: "#12b886", schema: "#f59f00", external: "#868e96" };

    function cur() { return ctx.getStage(); }
    function dp() { return document.getElementById(ctx.detailId); }
    function trunc(s, n) { s = String(s); return s.length > n ? s.slice(0, n - 1) + "…" : s; }
    function entOf(slug) { return ENT.filter(function (x) { return x.slug === slug; })[0] || {}; }
    function labelOf(slug) { var n = entOf(slug); return n.label || slug; }

    // ── small stage blocks ────────────────────────────────────────────────
    var STAGE_HEAD = { red: "what we made fail", execute: "what we changed",
                       review: "what we found", commit: "what shipped" };
    function pill(t, c) { return "<span class='pill' style='background:" + (c || STAGE_COLOR[cur()]) + "'>" + t + "</span>"; }
    function dblock(l, t) { return "<div class='b'><div class='l'>" + l + "</div><div class='t'>" + t + "</div></div>"; }
    function headline(label, text, color) {
      return "<div class='b'><div class='l' style='color:" + color + "'>" + label + "</div>"
        + "<div class='headline' style='background:" + color + "18;border-left:3px solid " + color + "'>" + text + "</div></div>";
    }
    function bar(add, del) {
      var tot = (add || 0) + (del || 0) || 1, g = Math.round(100 * (add || 0) / tot);
      return "<div class='bar'><i style='width:" + g + "%;background:#2f9e63'></i><i style='width:" + (100 - g) + "%;background:#e5484d'></i></div>"
        + "<div class='delta'>+" + (add || 0) + " · −" + (del || 0) + " lines</div>";
    }

    // ── typed identifier chips — EQUAL the command center's code-section language ──
    //  glyphs lifted verbatim from _a3_code._INS_ICONS + _a3_render zap; kind
    //  colours from KIND_COLOR; ty-* families mirror _a3_code._TYPE_CLS (the
    //  colours themselves live in a3.css, theme-aware).
    var KIND_ICON = {
      fn: '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 17c2 0 3-1 3-3v-4c0-2 1-3 3-3"/><path d="M9 11h6"/>',
      endpoint: '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
      model: '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/>',
      schema: '<path d="M8 3H7a2 2 0 0 0-2 2v5a2 2 0 0 1-2 2 2 2 0 0 1 2 2v5c0 1.1.9 2 2 2h1"/><path d="M16 21h1a2 2 0 0 0 2-2v-5c0-1.1.9-2 2-2a2 2 0 0 1-2-2V5a2 2 0 0 0-2-2h-1"/>',
      datatype: '<polyline points="4 7 4 4 20 4 20 7"/><line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="4" x2="12" y2="20"/>'
    };
    var KIND_CHIP = { fn: "#0f766e", endpoint: KIND_COLOR.endpoint, model: KIND_COLOR.model, schema: KIND_COLOR.schema };
    var METHOD_COLOR = { GET: "#16794c", POST: "#4338ca", PUT: "#b45309", PATCH: "#b45309", DELETE: "#d1443c", BOOT: "#8a8f98", TASK: "#a78bfa" };   /* BOOT + TASK roots (legend pass 2026-09-06); an unknown verb still falls to #868e96 */
    var TYPE_CLS = { int: "num1", float: "num2", Decimal: "num2", Numeric: "num2", date: "tim1", time: "tim1",
      datetime: "tim2", str: "str1", Text: "str2", bytes: "str2", bool: "bool", dict: "json", list: "json",
      Any: "json", JSON: "json", Literal: "json", UUID: "id", uuid: "id" };
    function icoSvg(pathd) {
      return '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" '
        + 'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + pathd + '</svg>';
    }
    function tyFamily(t) { var toks = String(t).split(/[^A-Za-z_]+/);
      for (var i = 0; i < toks.length; i++) { if (TYPE_CLS[toks[i]]) return TYPE_CLS[toks[i]]; } return null; }
    function kindChip(kind, label) { var c = KIND_CHIP[kind] || "#868e96";
      return "<span class='idchip' style='color:" + c + ";background:" + c + "1f'>" + icoSvg(KIND_ICON[kind])
        + "<b>" + trunc(label, 30) + "</b></span>"; }
    function epChip(ep) { var mc = METHOD_COLOR[ep.m] || "#868e96", c = KIND_CHIP.endpoint;
      return "<span class='idchip' style='color:" + c + ";background:" + c + "1f' title='" + ep.m + " " + ep.p + " → " + ep.fn + "()'>"
        + icoSvg(KIND_ICON.endpoint) + "<span class='mth' style='color:" + mc + "'>" + ep.m + "</span><b>" + ep.p + "</b></span>"; }
    function dtChip(d) { var fam = tyFamily(d.t);
      return "<span class='idchip dt'>" + icoSvg(KIND_ICON.datatype) + "<b>" + d.n + "</b>"
        + "<span class='ty" + (fam ? " ty-" + fam : "") + "'>" + d.t + "</span></span>"; }
    // TESTS + EVIDENCE — the center's test-kind glyphs, coloured by pass/red state.
    var TEST_ICON = {
      unit: '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/>',
      integration: '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
      journey: '<circle cx="6" cy="19" r="3"/><circle cx="18" cy="5" r="3"/><path d="M12 19h4.5a3.5 3.5 0 0 0 0-7h-8a3.5 3.5 0 0 1 0-7H12"/>',
      web: '<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>'
    };
    var VERIFIED_ICON = '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>';
    var STATE_COLOR = { pass: "#16794c", red: "#e5484d", fail: "#e5484d", skip: "#b45309" };
    function testChip(t) { var c = STATE_COLOR[t.state] || "#868e96", ic = TEST_ICON[t.kind] || TEST_ICON.unit;
      var mk = t.state === "pass" ? "✓" : (t.state === "red" ? "✕" : "·"), lab = t.cid === "web" ? "e2e" : t.cid;
      return "<span class='idchip' style='color:" + c + ";background:" + c + "1f' title='" + (t.name || t.tfile) + " · " + (t.tfile || "") + " · " + t.state + "'>"
        + icoSvg(ic) + "<b>" + lab + "</b><span class='mth' style='color:" + c + "'>" + t.state + " " + mk + "</span></span>"; }
    function evChip(label, ev) { if (!ev) return "";
      var ok = (ev.exit === 0 && !ev.failed), c = ok ? "#16794c" : "#e5484d";
      return "<span class='idchip' style='color:" + c + ";background:" + c + "1f' title='" + label + "-junit @ " + (ev.head || "?") + "'>"
        + icoSvg(VERIFIED_ICON) + "<b>" + label + "</b><span class='mth' style='color:" + c + "'>" + ev.passed + " ✓"
        + (ev.failed ? " · " + ev.failed + " ✕" : "") + (ev.skipped ? " · " + ev.skipped + " skip" : "") + "</span></span>"; }
    function evidenceRow() { var ev = SIM.evidence; if (!ev) return "";
      var chips = Object.keys(ev).map(function (k) { return evChip(k, ev[k]); }).join("");
      return chips ? idrow("Evidence", chips) : ""; }
    function idrow(label, chips) { return chips ? "<div class='idrow'><div class='idlbl'>" + label
      + "</div><div class='idchips'>" + chips + "</div></div>" : ""; }
    function idSection(ids) {
      if (!ids) return "";
      var h = "";
      if (ids.fn)        h += idrow("Functions", ids.fn.map(function (f) { return kindChip("fn", f + "()"); }).join(""));
      if (ids.endpoint)  h += idrow("Endpoints", ids.endpoint.map(epChip).join(""));
      if (ids.model)     h += idrow("Models",    ids.model.map(function (m) { return kindChip("model", m); }).join(""));
      if (ids.schema)    h += idrow("Schemas",   ids.schema.map(function (s) { return kindChip("schema", s); }).join(""));
      if (ids.datatype)  h += idrow("Data types", ids.datatype.map(dtChip).join(""));
      if (ids.test)      h += idrow("Tests",     ids.test.map(testChip).join(""));
      if (ids.structure) h += idrow("Structures", ids.structure.map(function (s) { return "<span class='idchip st'>" + s + "</span>"; }).join(""));
      return h ? "<div class='idsec'>" + h + "</div>" : "";
    }
    // union the current stage's identifiers across an entity's pieces (entity panel)
    function aggregateIds(slug) {
      var sd = (SIM.stages && SIM.stages[cur()]) || {}, pieces = (SIM.pieces && SIM.pieces[slug]) || [];
      var out = {}, seen = { fn: {}, endpoint: {}, model: {}, schema: {}, datatype: {}, test: {}, structure: {} };
      pieces.forEach(function (p) { var ids = ((sd.pieces && sd.pieces[p.id]) || {}).ids; if (!ids) return;
        ["fn", "endpoint", "model", "schema", "datatype", "test", "structure"].forEach(function (k) {
          (ids[k] || []).forEach(function (v) { var key = (k === "endpoint") ? v.fn : (k === "datatype" ? v.n : (k === "test" ? v.cid + v.tfile : v));
            if (seen[k][key]) return; seen[k][key] = 1; (out[k] = out[k] || []).push(v); }); });
      });
      return Object.keys(out).length ? out : null;
    }

    // ── the DIFFERENTIAL: one piece across ALL FOUR stages at once (M1+M5) ──
    function pieceStageLine(p, s) {
      var d = (((SIM.stages || {})[s] || {}).pieces || {})[p.id] || {};
      if (s === "red")     return d.tested ? "red ✕ · " + (d.cases || []).join(" ") : "no red test";
      if (s === "execute") return d.changed ? "+" + (d.add || 0) + " " + (d.what || "changed") : "not edited";
      if (s === "review")  return d.touched_again ? "⚠ " + (d.risk || "") + " · " + trunc(d.why || "", 42) : "clean";
      if (s === "commit")  return p.role === "changed" ? "in commit ✓" : "not in commit";
      return "";
    }
    function lifecycleStrip(p) {
      var order = ["red", "execute", "review", "commit"], nm = { red: "Red", execute: "Execute", review: "Review", commit: "Commit" };
      return "<div class='lifecycle'>" + order.map(function (s) {
        var c = STAGE_COLOR[s], on = (s === cur());
        return "<div class='lc-row" + (on ? " active" : "") + "' data-stage='" + s + "'"
          + (on ? " style='background:" + c + "14;border-left:3px solid " + c + "'" : "") + ">"
          + "<span class='lc-dot' style='background:" + c + (on ? "" : ";opacity:.4") + "'></span>"
          + "<span class='lc-name'" + (on ? " style='color:" + c + "'" : "") + ">" + nm[s] + "</span>"
          + "<span class='lc-sum'>" + pieceStageLine(p, s) + "</span></div>";
      }).join("") + "</div>";
    }

    // ── a single PIECE — its lifecycle timeline + the active stage ────────────
    function openDetail(slug, p) {
      var sd = (SIM.stages && SIM.stages[cur()]) || {}, d = (sd.pieces && sd.pieces[p.id]) || {};
      var el = dp(), sc = STAGE_COLOR[cur()];
      var body = "";
      if (cur() === "execute") {
        body = d.changed
          ? "<div class='pillrow'>" + pill(d.action || "changed") + "<span class='file'>" + ((d.file || "").split("/").pop()) + "</span></div>"
            + bar(d.add, d.del) + headline("what we changed", d.effect || d.what || "—", sc)
            + idSection(d.ids) + (d.ids ? "" : dblock("added", d.what || "internal edits"))
          : "<div class='pillrow'>" + pill("not changed", "var(--muted)") + "</div>"
            + dblock("relation", "downstream via FK") + dblock("why it's here", d.summary || "referenced by the change");
      } else if (cur() === "red") {
        body = d.tested
          ? "<div class='pillrow'>" + pill("red proved", "#e5484d") + (d.cases || []).map(function (c) { return "<span class='case'>" + c + "</span>"; }).join("") + "</div>"
            + headline("what we made fail", d.red || "—", "#e5484d")
            + (d.use_case ? dblock("use case", d.use_case) : "") + idSection(d.ids)
            + dblock("covers", d.covers || "—") + dblock("guards against", d.guards || "—")
            + (d.source ? dblock("from", d.source) : "")
          : "<div class='pillrow'>" + pill("no test", "var(--muted)") + "</div>"
            + idSection(d.ids) + dblock("risk if it breaks", d.guards || "no red declared for this piece");
      } else if (cur() === "review") {
        var rc = { low: "#2f9e63", medium: "#d9821f", high: "#e5484d", watch: "#4c9aff" }[d.risk] || sc;
        body = "<div class='pillrow'>" + pill(d.touched_again ? "finding" : "clean") + pill("risk " + (d.risk || "—"), rc) + "</div>"
          + headline("what we found", d.why || "—", sc) + idSection(d.ids)
          + (d.impact ? dblock("impact", d.impact) : "") + (d.source ? dblock("from", d.source) : "");
      } else if (cur() === "commit") {
        var m = (SIM.stages.commit && SIM.stages.commit.meta) || {};
        var eids = (((SIM.stages.execute || {}).pieces || {})[p.id] || {}).ids;   // ship = what Execute changed
        body = "<div class='pillrow'>" + pill(p.role === "changed" ? "in commit" : "not in commit", p.role === "changed" ? sc : "var(--muted)") + "<span class='file'>" + (m.commit || "") + "</span></div>"
          + headline("what shipped", m.subject || "—", sc) + "<div class='delta'>" + (m.files || 0) + " files · +" + (m.add || 0) + " · −" + (m.del || 0) + "</div>"
          + idSection(eids) + "<div class='idsec'>" + evidenceRow() + "</div>" + dblock("cases", (m.cases || []).join(", ") || "—");
      }
      var ex = (sd.real === false) ? " <span class='ex'>· example</span>" : "";
      el.innerHTML = "<div class='phdr'>" + cur() + ex + " · lifecycle</div><h4>" + p.label + "</h4>"
        + "<div class='kind'>in " + labelOf(slug) + "</div>"
        + lifecycleStrip(p) + body;
      ctx.selectPiece(slug + "|" + p.id);
      // timeline rows switch the stage but keep THIS piece open (the differential nav)
      el.querySelectorAll(".lc-row").forEach(function (row) {
        row.addEventListener("click", function () {
          var s = row.getAttribute("data-stage"); if (s === cur()) return;
          ctx.applyStage(s);        // set curStage, sync stageSeg buttons, re-render graph
          openDetail(slug, p);
        });
      });
    }

    // ── the WHOLE entity — its stage headline aggregates every highlighted piece ──
    function openEntityDetail(slug) {
      var el = dp();
      var n = entOf(slug), c = n.counts || {};
      var TOUCH = {}, BLAST = {};
      (SIM.touched || []).forEach(function (s) { TOUCH[s] = 1; });
      (SIM.blast || []).forEach(function (s) { BLAST[s] = 1; });
      var roleCol = TOUCH[slug] ? "var(--touch)" : (BLAST[slug] ? "var(--blast)" : "var(--muted)");
      var role = TOUCH[slug] ? "touched by this change" : (BLAST[slug] ? "downstream · blast radius" : "not involved");
      var pieces = (SIM.pieces && SIM.pieces[slug]) || [], sd = (SIM.stages && SIM.stages[cur()]) || {}, sc = STAGE_COLOR[cur()];
      function row(k, v) { return "<div class='row'><span class='k'>" + k + "</span><span class='v'>" + v + "</span></div>"; }
      var lines = [];
      pieces.forEach(function (p) {
        var d = (sd.pieces && sd.pieces[p.id]) || {};
        if (cur() === "red" && d.tested) lines.push("<b>" + p.label + "</b> — " + (d.red || d.covers || ""));
        else if (cur() === "execute" && d.changed) lines.push("<b>" + p.label + "</b> +" + d.add + " · " + (d.what || ""));
        else if (cur() === "review" && d.touched_again) lines.push("<b>" + p.label + "</b> — " + (d.why || "") + " (" + (d.risk || "") + ")");
        else if (cur() === "commit" && p.role === "changed") lines.push("<b>" + p.label + "</b>");
      });
      var headText;
      if (cur() === "commit") { var m = (SIM.stages.commit && SIM.stages.commit.meta) || {};
        headText = (m.subject || "") + "<div class='delta'>" + (m.files || 0) + " files · +" + (m.add || 0) + " · −" + (m.del || 0) + "</div>"; }
      else headText = lines.length ? lines.join("<br>") : "<span class='muted'>nothing in this entity for the " + cur() + " stage</span>";
      var ex = (sd.real === false) ? " <span class='ex'>· example</span>" : "";
      el.innerHTML = "<div class='phdr'>entity · " + cur() + ex + "</div>"
        + "<h4 style='color:" + roleCol + "'>" + (n.label || slug) + "</h4><div class='kind'>" + role + "</div>"
        + row("endpoints", c.endpoints || 0) + row("models", c.models || 0) + row("schemas", c.schemas || 0) + row("files", c.files || 0) + row("lines", (c.lines || 0).toLocaleString())
        + headline(STAGE_HEAD[cur()], headText, sc)
        + (function () { var ag = aggregateIds(slug); return ag ? idSection(ag) : ""; })()
        + (cur() === "commit" ? "<div class='idsec'>" + evidenceRow() + "</div>" : "")
        + "<div class='sum'>double-click to open its pieces</div>";
      ctx.selectPiece(null);
    }

    // ── default panel: a stage-wide summary of the crucial pieces, all entities ──
    function stageSummary() {
      var el = dp(), sd = (SIM.stages && SIM.stages[cur()]) || {}, sc = STAGE_COLOR[cur()];
      var lines = [], n = 0;
      (SIM.touched || []).concat(SIM.blast || []).forEach(function (slug) {
        var ent = labelOf(slug);
        ((SIM.pieces && SIM.pieces[slug]) || []).forEach(function (p) {
          var d = (sd.pieces && sd.pieces[p.id]) || {};
          if (cur() === "red" && d.tested) { n++; lines.push("<b>" + p.label + "</b> — " + (d.red || d.covers || "") + " <span class='muted'>· " + ent + "</span>"); }
          else if (cur() === "execute" && d.changed) { n++; lines.push("<b>" + p.label + "</b> +" + d.add + " · " + (d.what || "") + " <span class='muted'>· " + ent + "</span>"); }
          else if (cur() === "review" && d.touched_again) { n++; lines.push("<b>" + p.label + "</b> — " + (d.why || "") + " (" + (d.risk || "") + ") <span class='muted'>· " + ent + "</span>"); }
          else if (cur() === "commit" && p.role === "changed") { n++; lines.push("<b>" + p.label + "</b> <span class='muted'>· " + ent + "</span>"); }
        });
      });
      var noun = { red: "red test", execute: "changed piece", review: "finding", commit: "piece in commit" }[cur()];
      var head, sub = n + " " + noun + (n === 1 ? "" : "s");
      if (cur() === "commit") { var m = (SIM.stages.commit && SIM.stages.commit.meta) || {};
        head = "<b>" + (m.commit || "") + "</b> " + (m.subject || "") + "<div class='delta'>" + (m.files || 0) + " files · +" + (m.add || 0) + " · −" + (m.del || 0) + " · " + (m.cases || []).join(", ") + "</div>"; }
      else head = lines.length ? lines.join("<br>") : "<span class='muted'>nothing flagged for the " + cur() + " stage</span>";
      var ex = (sd.real === false) ? " <span class='ex'>· example</span>" : "";
      el.innerHTML = "<div class='phdr'>" + cur() + ex + " · all entities</div>"
        + "<h4>Change summary</h4>"
        + "<div class='kind'><span style='color:var(--touch)'>" + (SIM.touched || []).join(", ") + "</span> &rarr; <span style='color:var(--blast)'>" + (SIM.blast || []).join(", ") + "</span> · " + sub + "</div>"
        + headline(STAGE_HEAD[cur()], head, sc)
        + "<div class='sum'>click an entity or a piece for its detail</div>";
      ctx.selectPiece(null);
    }
    function resetPanel() { stageSummary(); }

    return { openDetail: openDetail, openEntityDetail: openEntityDetail,
             stageSummary: stageSummary, resetPanel: resetPanel };
  };
})();
