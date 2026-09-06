#!/usr/bin/env node
// Chrome harness for the command-center shell JS (alignment review M22).
//
// The previous harness (gastify scripts/verify_center_chrome.mjs) drove
// Playwright against `tr.rowtog` rows — a DOM the generators stopped emitting,
// so it could neither pass nor catch drift. This rewrite verifies the CURRENT
// shell contract against a BUILT page with node stdlib only, two ways:
//
//   1. STRUCTURAL — scan the page's markup and assert the shapes the shell JS
//      keys on: every .xtbl holds details.xrow rows with summary-first
//      children, flat rows carry .xsummary, a[data-lb] artifacts sit inside
//      .xrow within .xtbl with href + data-shot, details[data-sub] legs live
//      inside their .xrow, every internal #href resolves to an id (openTarget
//      is a silent no-op on a dead anchor), the settings mount points
//      (.topbar/.side/.brand) exist, the referenced assets resolve on disk,
//      and no {{TOKEN}} slot is left unfilled.
//
//   2. BEHAVIORAL — EXECUTE the rowclick.js the page references inside a
//      minimal stub DOM built from shapes SCRAPED off the page (row tag,
//      summary tag, a real cross-referenced row id, a real tab id) and assert:
//      row click toggles open/closed, links and [data-lb] artifacts do not
//      toggle, flat rows cascade their ⊕ details, .tbl rows toggle with their
//      .exp sibling, a cross-reference hash OPENS + center-scrolls the row,
//      and a #tab-* hash scrolls to top without center-scrolling.
//
// Either side drifting — generator markup or shell JS selectors — makes a
// check fail, which is exactly what the dead rowtog harness could not do.
//
// Usage:  node verify_center_chrome.mjs <page.html … | center-dir …>
// Dir mode checks every *.html that references rowclick.js (others are
// skipped with a note); zero qualifying pages is a refused vacuous pass.
// Exit 0 = green, 1 = drift, 2 = usage / unreadable input / vacuous run.

import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';

// ───────────────────────── result collection ────────────────────────────────
let pass = 0;
const fails = [];
function check(page, cond, msg) {
  const line = `${path.basename(page)} · ${msg}`;
  if (cond) { pass += 1; console.log('PASS · ' + line); }
  else { fails.push(line); console.log('FAIL · ' + line); }
  return cond;
}
function info(page, msg) {
  console.log('INFO · ' + path.basename(page) + ' · ' + msg);
}

// ───────────────────────── page selection ────────────────────────────────────
const args = process.argv.slice(2);
if (!args.length) {
  console.error('usage: node verify_center_chrome.mjs <page.html … | center-dir …>');
  process.exit(2);
}
const pages = [];
for (const a of args) {
  const p = path.resolve(a);
  let st;
  try { st = fs.statSync(p); } catch {
    console.error('⛔ not found: ' + p);
    process.exit(2);
  }
  if (st.isDirectory()) {
    for (const f of fs.readdirSync(p).filter((f) => f.endsWith('.html')).sort())
      pages.push({ file: path.join(p, f), explicit: false });
  } else {
    pages.push({ file: p, explicit: true });
  }
}

// ───────────────────────── streaming tag scanner ─────────────────────────────
const VOID = new Set(['area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
  'link', 'meta', 'param', 'source', 'track', 'wbr']);
const ATTR_RX = /([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*(?:=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>]+)))?/g;

function parseAttrs(raw) {
  const out = {};
  for (const m of raw.matchAll(ATTR_RX)) out[m[1]] = m[2] ?? m[3] ?? m[4] ?? '';
  return out;
}

// One pass over the markup, maintaining an open-element stack, collecting the
// facts the contract checks need. Raw text of <script>/<style> is skipped.
function scanPage(html) {
  const lower = html.toLowerCase();
  const facts = {
    scripts: [], ids: new Map(), hashHrefs: [], xtblCount: 0, xrows: [],
    dataLb: [], dataSub: [], tabIds: [], hasTopbar: false, hasSide: false,
    brandInSide: false,
  };
  const stack = [];
  let i = 0;
  while (i < html.length) {
    const lt = html.indexOf('<', i);
    if (lt < 0) break;
    if (html.startsWith('<!--', lt)) {
      const e = html.indexOf('-->', lt);
      i = e < 0 ? html.length : e + 3;
      continue;
    }
    if (html[lt + 1] === '!') { i = html.indexOf('>', lt) + 1 || html.length; continue; }
    const isClose = html[lt + 1] === '/';
    let j = lt + (isClose ? 2 : 1);
    let name = '';
    while (j < html.length && /[a-zA-Z0-9-]/.test(html[j])) name += html[j++];
    if (!name) { i = lt + 1; continue; }
    let q = null, k = j;
    while (k < html.length) {
      const c = html[k];
      if (q) { if (c === q) q = null; }
      else if (c === '"' || c === "'") q = c;
      else if (c === '>') break;
      k += 1;
    }
    const tag = name.toLowerCase();
    if (isClose) {
      const at = stack.map((e) => e.tag).lastIndexOf(tag);
      if (at >= 0) stack.length = at;               // tolerant unwind
    } else {
      const raw = html.slice(j, k);
      const selfClose = /\/\s*$/.test(raw);
      const rec = recordOpen(facts, stack, tag, parseAttrs(raw));
      if (!selfClose && !VOID.has(tag)) stack.push(rec);
      if (tag === 'script' || tag === 'style') {
        const close = lower.indexOf('</' + tag, k);
        if (close > 0) { i = close; continue; }
      }
    }
    i = k + 1;
  }
  return facts;
}

function recordOpen(facts, stack, tag, attrs) {
  const classes = new Set((attrs.class || '').split(/\s+/).filter(Boolean));
  const parent = stack[stack.length - 1];
  const inXtbl = stack.some((e) => e.classes.has('xtbl'));
  const xrowAnc = [...stack].reverse().find((e) => e.classes.has('xrow'));
  if (attrs.id) {
    facts.ids.set(attrs.id, { tag, classes });
    if (attrs.id.startsWith('tab-')) facts.tabIds.push(attrs.id);
  }
  if (tag === 'script' && attrs.src) facts.scripts.push(attrs.src);
  if (attrs.href && attrs.href.startsWith('#') && attrs.href.length > 1)
    facts.hashHrefs.push(attrs.href.slice(1));
  if (classes.has('xtbl')) facts.xtblCount += 1;
  if (classes.has('topbar')) facts.hasTopbar = true;
  if (classes.has('side')) facts.hasSide = true;
  if (classes.has('brand') && stack.some((e) => e.classes.has('side')))
    facts.brandInSide = true;
  if (parent && parent.rec) {
    if (parent.rec.firstChild === null) parent.rec.firstChild = tag;
    if (classes.has('xsummary')) parent.rec.hasXsummary = true;
  }
  let rec = null;
  if (classes.has('xrow')) {
    rec = { tag, id: attrs.id || '', flat: classes.has('xflat'), inXtbl,
      firstChild: null, hasXsummary: false };
    facts.xrows.push(rec);
  }
  if ('data-lb' in attrs)
    facts.dataLb.push({ tag, inXrow: !!xrowAnc, inXtbl,
      href: attrs.href || '', shot: attrs['data-shot'] || '' });
  if (tag === 'details' && 'data-sub' in attrs)
    facts.dataSub.push({ inXrow: !!xrowAnc });
  return { tag, classes, rec };
}

// ───────────────────────── minimal stub DOM ──────────────────────────────────
// Just enough DOM for rowclick.js: closest / querySelector(All) with the
// selector grammar it uses (tag, .class, [attr], compounds, descendant and
// child combinators, :scope >), classList, details.open, event delegation.
const SIV_CALLS = [];

function parseCompound(tok) {
  if (tok === ':scope') return { scope: true };
  const m = tok.match(/^([a-zA-Z0-9-]*)((?:\.[-\w]+)*)((?:\[[^\]]+\])*)$/);
  if (!m) throw new Error('unsupported selector token: ' + tok);
  return {
    tag: m[1] ? m[1].toLowerCase() : null,
    classes: m[2].split('.').filter(Boolean),
    attrs: [...m[3].matchAll(/\[([^\]=~|^$*]+)(?:[~|^$*]?=[^\]]*)?\]/g)].map((x) => x[1]),
  };
}

function parseSelector(sel) {
  const steps = [];
  let comb = null;
  for (const tok of sel.trim().split(/\s+/)) {
    if (tok === '>') { comb = '>'; continue; }
    steps.push({ comb: steps.length ? (comb || ' ') : null, ...parseCompound(tok) });
    comb = null;
  }
  return steps;
}

class El {
  constructor(tag, attrs = {}) {
    this.tagName = tag.toUpperCase();
    this.attrs = { ...attrs };
    this.classes = new Set((attrs.class || '').split(/\s+/).filter(Boolean));
    this.children = [];
    this.parentElement = null;
    this.open = 'open' in attrs;
    const self = this;
    this.classList = {
      contains: (c) => self.classes.has(c),
      add: (c) => self.classes.add(c),
      remove: (c) => self.classes.delete(c),
      toggle: (c, force) => {
        const on = force === undefined ? !self.classes.has(c) : !!force;
        if (on) self.classes.add(c); else self.classes.delete(c);
        return on;
      },
    };
  }
  get id() { return this.attrs.id || ''; }
  append(...kids) {
    for (const k of kids) { k.parentElement = this; this.children.push(k); }
    return this;
  }
  get nextElementSibling() {
    if (!this.parentElement) return null;
    const sib = this.parentElement.children;
    return sib[sib.indexOf(this) + 1] || null;
  }
  getAttribute(n) { return n in this.attrs ? this.attrs[n] : null; }
  contains(node) {
    for (let n = node; n; n = n.parentElement) if (n === this) return true;
    return false;
  }
  matchesCompound(st) {
    if (st.tag && this.tagName.toLowerCase() !== st.tag) return false;
    for (const c of st.classes) if (!this.classes.has(c)) return false;
    for (const a of st.attrs) if (!(a in this.attrs)) return false;
    return true;
  }
  matchesComplex(steps, scope, i = steps.length - 1) {
    const st = steps[i];
    if (st.scope) return this === scope;
    if (!this.matchesCompound(st)) return false;
    if (i === 0) return true;
    if (st.comb === '>')
      return this.parentElement
        ? this.parentElement.matchesComplex(steps, scope, i - 1) : false;
    for (let p = this.parentElement; p; p = p.parentElement)
      if (p.matchesComplex(steps, scope, i - 1)) return true;
    return false;
  }
  closest(sel) {
    const steps = parseSelector(sel);
    for (let n = this; n; n = n.parentElement)
      if (n.matchesComplex(steps, null)) return n;
    return null;
  }
  querySelectorAll(sel) {
    const steps = parseSelector(sel);
    const out = [];
    const walk = (node) => {
      for (const k of node.children) {
        if (k.matchesComplex(steps, this)) out.push(k);
        walk(k);
      }
    };
    walk(this);
    return out;
  }
  querySelector(sel) { return this.querySelectorAll(sel)[0] || null; }
  scrollIntoView(opts) { SIV_CALLS.push({ el: this, opts: opts || {} }); }
}

const el = (tag, attrs, ...kids) => new El(tag, attrs).append(...kids);

function makeRuntime(body) {
  const listeners = { doc: {}, win: {} };
  const on = (bag) => (type, fn) => (bag[type] = bag[type] || []).push(fn);
  const location = { hash: '' };
  const doc = {
    readyState: 'complete',
    body,
    addEventListener: on(listeners.doc),
    getElementById(id) {
      const find = (n) => {
        for (const k of n.children) {
          if (k.id === id) return k;
          const hit = find(k);
          if (hit) return hit;
        }
        return null;
      };
      return find(body);
    },
  };
  const win = {
    scrollToCalls: [],
    addEventListener: on(listeners.win),
    scrollTo(...a) { this.scrollToCalls.push(a); },
    getSelection: () => '',
    location,
  };
  return {
    doc, win, location,
    click(target) {
      const ev = { target, preventDefault() { this.defaultPrevented = true; } };
      for (const fn of listeners.doc.click || []) fn(ev);
      return ev;
    },
    hashchange(hash) {
      location.hash = hash;
      for (const fn of listeners.win.hashchange || []) fn({});
    },
  };
}

// ───────────────────── behavioral battery (executes rowclick.js) ─────────────
function behavioral(page, facts, rowclickPath) {
  const expandRows = facts.xrows.filter((r) => !r.flat);
  const rowTag = mode(expandRows.map((r) => r.tag)) || 'details';
  const sumTag = mode(expandRows.map((r) => r.firstChild)) || 'summary';
  const crossRow = expandRows.find((r) => r.id && facts.hashHrefs.includes(r.id));
  const tabId = facts.tabIds[0] || null;

  // The stub is built FROM the page's shapes: its row/summary tags and the
  // real cross-ref + tab ids. If the generator drifts, the stub drifts with
  // the page and rowclick.js stops matching it — the assertions below fire.
  const bold = el('b', {});
  const link = el('a', { href: '#elsewhere' });
  const shotImg = el('img', {});
  const shot = el('a', { href: 'shot.png', 'data-lb': '1' }, shotImg);
  const summary = el(sumTag, {}, el('span', {}, bold), link, shot);
  const row = el(rowTag, { class: 'xrow', id: crossRow ? crossRow.id : 'stub-row' },
    summary, el('div', { class: 'xbody' }, el('p', {})));
  const pmore = el('details', { class: 'pmore' }, el('summary', {}));
  const flatSpan = el('span', {});
  const flat = el('div', { class: 'xrow xflat' },
    el('div', { class: 'xsummary' }, flatSpan, pmore));
  const xtbl = el('div', { class: 'xtbl' }, el('div', { class: 'xhead' }), row, flat);
  const det1 = el('details', {}, el('summary', {}));
  const det2 = el('details', {}, el('summary', {}));
  const tr1 = el('tr', {}, el('td', {}, det1));
  const trExp = el('tr', { class: 'exp' }, el('td', {}, det2));
  const tbl = el('table', { class: 'tbl' }, el('tbody', {}, tr1, trExp));
  const pane = el('section', { class: 'tabpane', id: tabId || 'tab-stub' });
  const body = el('body', {}, xtbl, tbl, pane);

  SIV_CALLS.length = 0;
  const rt = makeRuntime(body);
  const src = fs.readFileSync(rowclickPath, 'utf8');
  const run = vm.runInThisContext(
    '(function (document, window, location) {\n' + src + '\n})',
    { filename: rowclickPath });
  run(rt.doc, rt.win, rt.location);

  rt.click(bold);
  check(page, row.open === true, 'rowclick: clicking the row summary opens the row');
  rt.click(bold);
  check(page, row.open === false, 'rowclick: clicking the open row again closes it');
  rt.click(link);
  check(page, row.open === false, 'rowclick: a link inside the row does not toggle it');
  rt.click(shotImg);
  check(page, row.open === false, 'rowclick: a [data-lb] artifact does not toggle the row');
  rt.click(flatSpan);
  check(page, pmore.open === true && flat.classes.has('rowopen'),
    'rowclick: a flat .xrow click cascades its ⊕ details + rowopen');
  rt.click(det1.querySelector('summary'));
  check(page, det1.open && det2.open
    && tr1.classes.has('rowopen') && trExp.classes.has('rowopen'),
    'rowclick: a .tbl row click opens its details + .exp sibling together');

  if (crossRow) {
    rt.hashchange('#' + crossRow.id);
    const centered = SIV_CALLS.some((c) => c.el === row && c.opts.block === 'center');
    check(page, row.open === true && centered,
      `rowclick: cross-ref #${crossRow.id} opens the target row and centers it`);
  } else {
    info(page, 'no cross-referenced .xrow id on this page — deep-link case skipped');
  }
  if (tabId) {
    SIV_CALLS.length = 0;
    rt.win.scrollToCalls.length = 0;
    rt.hashchange('#' + tabId);
    check(page,
      rt.win.scrollToCalls.some((a) => a[0] === 0 && a[1] === 0) && !SIV_CALLS.length,
      `rowclick: tab hash #${tabId} lands at page top without center-scrolling`);
  } else {
    info(page, 'no tab-* id on this page — tab-scroll case skipped');
  }
}

function mode(list) {
  const counts = new Map();
  for (const v of list) if (v) counts.set(v, (counts.get(v) || 0) + 1);
  return [...counts.entries()].sort((a, b) => b[1] - a[1]).map((e) => e[0])[0] || null;
}

// ───────────────────────── per-page verification ─────────────────────────────
const LIGHTBOX_LITERALS = ["a[data-lb]", "'.xtbl'", "'.xrow'", 'details[data-sub]'];

function verifyPage(page, explicit) {
  const html = fs.readFileSync(page, 'utf8');
  const facts = scanPage(html);
  const dir = path.dirname(page);
  const asset = (suffix) => {
    const src = facts.scripts.find((s) => s.endsWith(suffix));
    return src ? path.resolve(dir, src) : null;
  };

  const rowclickPath = asset('rowclick.js');
  if (!rowclickPath) {
    if (explicit) { check(page, false, 'page references rowclick.js'); return true; }
    info(page, 'does not reference rowclick.js — skipped (pre-ledger page?)');
    return false;
  }

  // wiring: every referenced asset resolves on disk
  for (const src of facts.scripts)
    check(page, fs.existsSync(path.resolve(dir, src)), `asset resolves: ${src}`);

  // expandable-table estate. PRESENCE is a feature-page contract — dashboard
  // stations (index, ledger, releases…) reference rowclick.js for their flat
  // rows without carrying an expandable estate; only CONSISTENCY is universal.
  const base = path.basename(page);
  const isFeaturePage = /^feature-.+\.html$/.test(base);
  if (isFeaturePage) {
    check(page, facts.xtblCount > 0 && facts.xrows.some((r) => !r.flat),
      `page has an .xtbl estate (${facts.xtblCount} tables, ${facts.xrows.length} rows)`);
  } else if (facts.xtblCount === 0) {
    info(page, 'no .xtbl estate — a dashboard station, consistency checks only');
  }
  check(page, facts.xrows.every((r) => r.inXtbl),
    'every .xrow sits inside an .xtbl');
  const badRows = facts.xrows.filter(
    (r) => !r.flat && !(r.tag === 'details' && r.firstChild === 'summary'));
  check(page, badRows.length === 0,
    'every expandable .xrow is <details> with a summary-first child'
    + (badRows.length ? ` (${badRows.length} off-contract)` : ''));
  check(page, facts.xrows.filter((r) => r.flat).every((r) => r.hasXsummary),
    'every flat .xrow.xflat carries its .xsummary');

  // anchors: openTarget is a silent no-op on a dead id
  const missing = [...new Set(facts.hashHrefs)].filter((h) => !facts.ids.has(h));
  check(page, missing.length === 0,
    `every internal #href resolves to an id (${facts.hashHrefs.length} refs`
    + (missing.length ? `, DEAD: ${missing.slice(0, 5).join(' ')}` : '') + ')');
  // Tab wiring is checked where a tab bar EXISTS; a single-pane station has
  // no tab links and that is its design, not drift.
  const tabRefs = [...new Set(facts.hashHrefs.filter((h) => h.startsWith('tab-')))];
  if (tabRefs.length || isFeaturePage) {
    check(page, tabRefs.length > 0 && tabRefs.every((t) => facts.ids.has(t)),
      `tab links target real panes (${tabRefs.length} tabs)`);
  } else {
    info(page, 'no tab bar on this page — tab-pane case skipped');
  }

  // proof-viewer wiring
  if (facts.dataLb.length) {
    const lbPath = asset('a3-lightbox.js');
    check(page, !!lbPath && fs.existsSync(lbPath),
      `page has ${facts.dataLb.length} [data-lb] artifacts and references a3-lightbox.js`);
    check(page, facts.dataLb.every((a) => a.href && a.shot),
      'every [data-lb] artifact carries href + data-shot');
    check(page, facts.dataLb.every((a) => a.inXrow && a.inXtbl),
      'every [data-lb] artifact sits inside an .xrow within an .xtbl (set navigation)');
    if (lbPath && fs.existsSync(lbPath)) {
      const lbSrc = fs.readFileSync(lbPath, 'utf8');
      const gone = LIGHTBOX_LITERALS.filter((l) => !lbSrc.includes(l));
      check(page, gone.length === 0,
        'a3-lightbox.js still keys on the page\'s shapes'
        + (gone.length ? ` (missing: ${gone.join(' ')})` : ''));
    }
  } else {
    info(page, 'no [data-lb] artifacts on this page — viewer wiring skipped');
  }
  check(page, facts.dataSub.every((d) => d.inXrow),
    'every details[data-sub] leg lives inside an .xrow (cascade contract)');

  // settings mount points
  if (asset('a3-settings.js'))
    check(page, facts.hasTopbar && facts.hasSide && facts.brandInSide,
      'settings mount points exist (.topbar, .side, .side .brand)');

  // slots: a generated page carries no unfilled tokens — measured against the page's SKELETON. Review 2026-09-06
  // (repo-study, onyx): rendered docstrings carry prompt placeholders (`{{CURRENT_DATETIME}}`) that are CONTENT,
  // not slots; a token is unfilled only when the skeleton this page was filled from carries the same token. The
  // skeleton is looked up at <repo>/templates/center/shell/<page> (a center under docs/site/center/) or beside the
  // example estate; with no skeleton found the plain rule (any {{TOKEN}}) applies, as before. feature.html is the
  // one KNOWN placeholder (the station template ships with its slots labeled until a generator claims it) — noted.
  const tokRx = /\{\{[A-Z0-9_]+\}\}/g;
  const pageToks = [...new Set(html.match(tokRx) || [])];
  let skelToks = null;
  // a DERIVED page is filled from its family's skeleton: arch-*.html ← architecture.html · feature-*.html ← feature.html · test-*.html ← tests.html
  const family = /^arch-/.test(base) ? 'architecture.html' : /^feature-/.test(base) ? 'feature.html' : /^test-/.test(base) ? 'tests.html' : null;
  const skelNames = family ? [base, family] : [base];
  const skelCands = [];
  for (const nm of skelNames) skelCands.push(path.join(dir, '..', '..', '..', 'templates', 'center', 'shell', nm), path.join(dir, '..', nm));
  for (const cand of skelCands) {
    try { if (fs.existsSync(cand) && path.resolve(cand) !== path.resolve(page)) { skelToks = new Set(fs.readFileSync(cand, 'utf8').match(tokRx) || []); break; } } catch {}
  }
  const unfilled = skelToks ? pageToks.filter(t => skelToks.has(t)) : pageToks;
  if (base === 'feature.html' && pageToks.length) {
    info(page, 'known placeholder station — unfilled slots are its documented state');
  } else {
    if (skelToks && pageToks.length && !unfilled.length) info(page, `content tokens, not slots (absent from the skeleton): ${pageToks.slice(0, 3).join(' ')}`);
    check(page, unfilled.length === 0,
      'no unfilled {{TOKEN}} slots on a generated page' + (unfilled.length ? ` (${unfilled.slice(0, 3).join(' ')})` : ''));
  }

  behavioral(page, facts, rowclickPath);
  return true;
}

// ───────────────────────── main ──────────────────────────────────────────────
let verified = 0;
for (const { file, explicit } of pages) {
  if (verifyPage(file, explicit)) verified += 1;
  console.log('');
}
if (!verified) {
  console.error('⛔ no page referencing rowclick.js found — refusing the vacuous pass');
  process.exit(2);
}
console.log(`chrome harness: ${verified} page(s) · ${pass} passed, ${fails.length} failed`);
if (fails.length) process.exit(1);
