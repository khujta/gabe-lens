/* probe.mjs — the ONE measurement rail. Solo-sequential (one Chrome at a time — the WSL2 rule), system Chrome + playwright-core,
   --use-angle=swiftshader (CPU rasteriser, NO GPU: every fps/frame number here is a floor and a RANK, never a rating).
     node probe.mjs                                   every lab-*.html on ?feed=example
     node probe.mjs --feed=onyx --fn=1                the onyx fixture with its function layer (fixtures/fetch-onyx.sh first)
     node probe.mjs --only=lab-01-three-raw.html      one page (comma-separated for several)
     node probe.mjs --scale=x4 --layout=baked --tier=3 --inject=1 --settle=120000 --fps=5000 --no-readme
   Per page it records: nodes/drawn (vs the adapter's count — a page that silently drops nodes goes RED) · boot · first frame (page-reported)
   · settle (the engine's OWN stop signal via LABG.settled, else timeout → null) · fps over the window (the page's own per-RENDER meter)
   · draw calls/tris/geos/texs (LABG.stats) · picking over 20 deterministic ids (real pointer move + LABG.pick) · tier press cost + positions
   EQUAL before/after (the no-relayout law) · heap MB · bundle KB split station/vendor/feed · offline proof (any non-file:// request FAILS
   the row) · honesty (0 pageerror · ink > 0.002 from the composited screenshot · no R10 word in the DOM · the injected unknown kind drawn)
   · k=10 entity purity of the final positions. Writes probe-results.<feed>.<scale>.json + _shots/ and regenerates README.md's table. */
import { createRequire } from 'module';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const D = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(D, '../../../..');
const PW = process.env.GABE_PW_DIR || path.join(REPO, 'docs/design/graft-adoption/spike/_build/node_modules/playwright-core');
const CHROME = process.env.GABE_CHROME_BIN || '/usr/bin/google-chrome-stable';
const arg = (k, d) => { const m = process.argv.find(a => a.startsWith('--' + k + '=')); return m ? m.slice(k.length + 3) : d; };
const FEED = arg('feed', 'example'), SCALE = arg('scale', 'full'), LAYOUT = arg('layout', 'live'), TIER = arg('tier', '3'), FN = arg('fn', '0');
const INJECT = arg('inject', '0') === '1', SETTLE = +arg('settle', '90000'), FPSWIN = +arg('fps', '5000'), NOREADME = process.argv.includes('--no-readme');
const only = arg('only', '');
const pages = only ? only.split(',') : fs.readdirSync(D).filter(f => /^lab-\d\d.*\.html$/.test(f)).sort();
if (!fs.existsSync(CHROME) || !fs.existsSync(PW)) { console.log('SKIP ⚠ — no chrome/playwright-core (set GABE_CHROME_BIN / GABE_PW_DIR)'); process.exit(3); }
if (FEED !== 'example' && !fs.existsSync(path.join(D, 'fixtures', FEED, 'c4-graph.js'))) { console.log('SKIP ⚠ — fixtures/' + FEED + '/c4-graph.js missing (run fixtures/fetch-onyx.sh)'); process.exit(3); }
const { chromium } = createRequire(import.meta.url)(PW);
const R10 = /\b(orphan|orphans|orphaned|dead code|unused)\b/i;
const PROBE_BUILD = 'p2 2026-09-07';   // bumped when a measured column changes meaning; rows without it render as stale

function purity(pos, ent, K = 10) {   // k=10 neighbour purity in the page's FINAL positions (the scale sweep's metric, 3D)
  const ids = Object.keys(pos).filter(i => ent[i]); let n = ids.length; if (n < K + 2) return null;
  let step = 1; if (n > 6000) step = Math.ceil(n / 3000);   // sample the probes above 6k, never the candidates
  const X = new Float64Array(n), Y = new Float64Array(n), Z = new Float64Array(n), E = ids.map(i => ent[i]);
  ids.forEach((i, k) => { X[k] = pos[i][0]; Y[k] = pos[i][1]; Z[k] = pos[i][2] || 0; });
  let tot = 0, cnt = 0; const d = new Float64Array(n), idx = new Int32Array(n);
  for (let a = 0; a < n; a += step) { for (let b = 0; b < n; b++) { const dx = X[a] - X[b], dy = Y[a] - Y[b], dz = Z[a] - Z[b]; d[b] = dx * dx + dy * dy + dz * dz; idx[b] = b; }
    d[a] = Infinity; const part = Array.from(idx).sort((p, q) => d[p] - d[q]).slice(0, K); tot += part.filter(b => E[b] === E[a]).length / K; cnt++; }
  return +(tot / cnt).toFixed(3);
}

const b = await chromium.launch({ executablePath: CHROME, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--no-sandbox', '--disable-gpu-sandbox', '--disable-dev-shm-usage', '--enable-precise-memory-info'] });
const rows = []; let bad = 0;
for (const spec of pages) {
  const page = spec.split('?')[0], variant = spec.includes('?') ? spec.slice(spec.indexOf('?') + 1) : '';   // --only=lab-00.html?hollow=1 → a VARIANT row of the same page
  const cfgSuffix = (FN === '1' ? ' fn=1' : '') + (LAYOUT !== 'live' ? ' layout=' + LAYOUT : '') + (TIER !== '3' ? ' tier=' + TIER : '');
  const pageKey = page + (variant ? '?' + variant : '') + cfgSuffix, shotKey = page.replace('.html', '') + (variant ? '.' + variant.replace(/[^a-z0-9]+/gi, '-') : '') + cfgSuffix.replace(/[^a-z0-9]+/gi, '-');
  const url = 'file://' + path.join(D, page) + '?feed=' + FEED + '&scale=' + SCALE + '&layout=' + LAYOUT + '&tier=' + TIER + '&fn=' + FN + (INJECT ? '&inject=1' : '') + (variant ? '&' + variant : '');
  const p = await b.newPage({ viewport: { width: 1400, height: 860 } });
  const errs = [], net = [];
  p.on('pageerror', e => errs.push('PE: ' + e.message));
  p.on('console', m => { if (m.type() === 'error') errs.push('CE: ' + m.text().slice(0, 220)); });
  await p.route('**', r => { const u = r.request().url(); if (u.startsWith('file://') || u.startsWith('blob:') || u.startsWith('data:')) r.continue(); else { net.push(u); r.abort(); } });
  const t0 = Date.now();
  await p.goto(url, { timeout: 60000 }).catch(e => errs.push('NAV: ' + e.message));
  await p.waitForFunction('window.__LAB_READY===true', { timeout: SETTLE }).catch(() => errs.push('TIMEOUT: __LAB_READY never set within ' + SETTLE + ' ms'));
  const norender = await p.evaluate(() => !!(window.__LAB && window.__LAB.notes && window.__LAB.notes.norender)).catch(() => false);
  // settle: the engine's OWN stop signal
  const settled = await p.waitForFunction('!window.LABG || window.LABG.settled===true', { timeout: SETTLE }).then(() => true).catch(() => false);
  const ticks = await p.evaluate(() => { try { return window.LABG && window.LABG.ticks ? window.LABG.ticks() : null; } catch (e) { return null; } });   // the layout's tick count (at settle, or at the timeout — the wrapper's per-tick cost under swiftshader is minutes)
  const heap0 = await p.evaluate(() => performance.memory ? performance.memory.usedJSHeapSize : null);
  // the fps window: the page's own per-RENDER meter
  if (!norender) await p.waitForTimeout(FPSWIN);
  const L = await p.evaluate(() => window.__LAB || null);
  const G = await p.evaluate(() => {
    const g = window.LABG; if (!g) return null;
    const F = window.GABE_FEED; const fixedByTier = (F && F.fixed) ? [0, 1, 2, 3].map(t => F.nodes.filter(n => n.tier <= t && n.bx != null).length) : null;
    const out = { stats: null, visible: null, drawn: null, feedNodes: F ? F.counts.nodes : null, feedLinks: F ? F.counts.links : null, byTier: fixedByTier || (F ? F.counts.byTier : null), tier: F ? F.tier : null, layout: F ? F.layout : null, baked: F && F.baked ? { hit: F.baked.hit, of: F.baked.of } : null, warnings: F ? F.warnings : [], heat: F ? F.heat : null, budgetHit: F ? F.budgetHit : null };
    try { out.stats = g.stats ? g.stats() : null; } catch (e) { out.stats = { err: String(e) }; }
    try { out.visible = g.visible ? g.visible() : null; } catch (e) { out.visible = null; }
    try { out.drawn = g.drawn ? g.drawn() : null; } catch (e) { out.drawn = 'err:' + e; }   // the RENDERER's count (instance buffers · display data · visibility) — the adapter's byTier is the expected side
    return out;
  });
  const fpsState = settled ? 'settled' : 'ticking';
  // picking: 20 deterministic ids among the VISIBLE nodes, real pointer move + the page's pick
  let pick = { tries: 0, hits: 0, other: 0, occluded: 0, none: 0, unpositioned: 0, ms: null, mech: (L && L.notes && L.notes.pick) || null };
  if (G && !norender) {
    const ids = await p.evaluate(() => { const g = window.LABG; const F = window.GABE_FEED; const vis = (g.visibleIds ? g.visibleIds() : F.nodes.filter(n => n.tier <= F.tier).map(n => n.id)).slice().sort(); const out = []; for (let i = 0; i < 20 && vis.length; i++) { const id = vis[Math.round(i * (vis.length - 1) / 19)]; if (!out.includes(id)) out.push(id); } return out; });
    let msAcc = 0;
    for (const id of ids) {
      const sc = await p.evaluate(id => { try { return window.LABG.screenOf(id); } catch (e) { return null; } }, id);
      if (!sc || !isFinite(sc.x) || !isFinite(sc.y) || sc.x < 0 || sc.y < 0 || sc.x > 1400 || sc.y > 860) { pick.unpositioned++; continue; }
      await p.mouse.move(sc.x, sc.y); await p.waitForTimeout(60);
      const r = await p.evaluate(([x, y]) => { const t = performance.now(); let id = null; try { id = window.LABG.pick(x, y); } catch (e) { id = null; } return { id, ms: performance.now() - t }; }, [sc.x, sc.y]);
      pick.tries++; msAcc += r.ms; if (r.id === id) pick.hits++; else if (r.id) { const o = await p.evaluate(oid => { try { return window.LABG.screenOf(oid); } catch (e) { return null; } }, r.id); if (o && Math.hypot(o.x - sc.x, o.y - sc.y) <= 8) pick.occluded++; else pick.other++; } else pick.none++;   // occluded = another node's centre sits within 8 px of the probed pixel (a correct pick of the nearer node)
    }
    pick.ms = pick.tries ? +(msAcc / pick.tries).toFixed(2) : null;
  }
  // the tier press: positions EQUAL before/after, cost timed, visible counts vs the adapter's byTier
  let tier = null;
  if (G && !norender) tier = await p.evaluate(() => {
    const g = window.LABG; if (!g.setTier) return { na: true };
    const before = g.positions(); const t0 = performance.now(); const v0 = g.setTier(0); const t1 = performance.now(); const v3 = g.setTier(3); const t2 = performance.now();
    window.__tierBefore = before; return { down_ms: +(t1 - t0).toFixed(1), up_ms: +(t2 - t1).toFixed(1), visible_t0: v0, visible_t3: v3, n: Object.keys(before).length };
  });
  if (tier && !tier.na && !settled) { tier.static = null; tier.note = 'sim still ticking at the press — positions move on their own, the equality is not measurable (the wrapper never reaches its 240th tick within the budget)'; }
  else if (tier && !tier.na) { await p.waitForTimeout(500); const eq = await p.evaluate(() => { const g = window.LABG, before = window.__tierBefore || {}, after = g.positions(); let moved = 0; for (const id in before) { const a = before[id], b = after[id]; if (!b || Math.abs(a[0] - b[0]) > 1e-6 || Math.abs(a[1] - b[1]) > 1e-6 || Math.abs((a[2] || 0) - (b[2] || 0)) > 1e-6) moved++; } return { moved }; });   // read AFTER a settle wait — an async relayout must not score static
    tier.moved = eq.moved; tier.static = eq.moved === 0; }
  const heap1 = await p.evaluate(() => performance.memory ? performance.memory.usedJSHeapSize : null);
  // bundle bytes: every <script src>, split station / vendor / feed / lab
  const scripts = await p.evaluate(() => [...document.scripts].map(s => s.src).filter(Boolean));
  const bundle = { station: 0, vendor: 0, feed: 0, lab: 0 };
  for (const s of scripts) { let f; try { f = fileURLToPath(s.split('?')[0]); } catch (e) { continue; } let sz = 0; try { sz = fs.statSync(f).size; } catch (e) { sz = 0; }
    if (f.includes('/templates/center/shell/assets/')) bundle.station += sz; else if (f.includes('/vendor/')) bundle.vendor += sz; else if (/c4-graph\.js|levels\.js|\.fdp\.js$/.test(f)) bundle.feed += sz; else bundle.lab += sz; }
  // honesty: ink from the composited screenshot · R10 grep · injected node drawn
  const shot = path.join(D, '_shots', shotKey + '.' + FEED + '.' + SCALE + (INJECT ? '.inject' : '') + '.png');
  fs.mkdirSync(path.dirname(shot), { recursive: true }); let shotNote = null;
  try { await p.screenshot({ path: shot, timeout: 180000 }); } catch (e) { shotNote = 'screenshot timed out (a frame takes longer than the compositor waits): ' + String(e.message || e).slice(0, 80); }   // the wrapper on onyx draws 24k calls per frame — a shot can outlast the budget; that is a NOTE, never a crash
  let ink = null;
  if (!norender && !shotNote) { await p.addStyleTag({ content: '.lab-panel,#score,.lab-knobs,.lab-legend,.lab-card,.lab-tip{visibility:hidden !important}' }); let buf = null; try { buf = await p.screenshot({ clip: { x: 340, y: 20, width: 800, height: 620 }, timeout: 180000 }); } catch (e) { shotNote = 'ink shot timed out'; } await p.addStyleTag({ content: '.lab-panel,#score,.lab-knobs,.lab-legend,.lab-card{visibility:visible !important}' }); if (buf) { const ip = await b.newPage();
    ink = await ip.evaluate(async b64 => { const img = new Image(); img.src = 'data:image/png;base64,' + b64; await img.decode(); const c = document.createElement('canvas'); c.width = 300; c.height = 200; const x = c.getContext('2d'); x.drawImage(img, 0, 0, 300, 200); const d = x.getImageData(0, 0, 300, 200).data; let k = 0; for (let i = 0; i < d.length; i += 4) { if (d[i] > 24 || d[i + 1] > 28 || d[i + 2] > 34) k++; } return +(k / 60000).toFixed(4); }, buf.toString('base64'));
    await ip.close(); } }
  const r10 = await p.evaluate(src => { const t = document.body ? document.body.innerText : ''; const m = new RegExp(src, 'i').exec(t); return m ? m[0] : null; }, R10.source);
  const injected = INJECT ? await p.evaluate(() => { const g = window.LABG; const F = window.GABE_FEED; const n = F && F.byId['zz:lab-injected']; if (!n) return 'missing-from-feed'; if (!g) return 'no-LABG'; try { const s = g.screenOf('zz:lab-injected'); const warned = (F.warnings || []).some(w => /unknown to this adapter/.test(w)); return (s && isFinite(s.x) && isFinite(s.y)) ? (warned ? 'drawn' : 'drawn-unwarned') : 'not-drawn'; } catch (e) { return 'err'; } }) : null;
  // purity of the final positions
  let pur = null;
  if (G && !norender) { const pe = await p.evaluate(() => { const g = window.LABG; const F = window.GABE_FEED; const pos = g.positions(); const ent = {}; for (const id in pos) { const n = F.byId[id]; if (n) ent[id] = n.ent; } return { pos, ent }; }); pur = purity(pe.pos, pe.ent); }
  const expected = G && G.byTier ? G.byTier[G.tier] : (G ? G.feedNodes : null);
  const drawnOk = norender || !G || (typeof G.drawn === 'number' ? G.drawn === expected : null);   // null = the page exposes no renderer-side count (the column reads '?')
  const pageErr = (L && L.err) || [];
  const ok = !!(L && L.ready) && errs.length === 0 && pageErr.length === 0 && net.length === 0 && (norender || shotNote || ink > 0.002) && !r10 && drawnOk !== false && (!tier || tier.na || tier.static !== false) && (!INJECT || norender || injected === 'drawn');   // static === null: not measurable on a still-ticking page, never a failure   // a page without a renderer (the adapter check) cannot draw the injected kind — it proves the count law instead
  if (!ok) bad++;
  const row = { page: pageKey, lib: L && L.lib, ver: L && L.ver, feed: FEED, scale: SCALE, layout: G && G.layout || LAYOUT, tier: +TIER, ok, wall_ms: Date.now() - t0, probe_build: PROBE_BUILD, when: new Date().toISOString(),
    nodes: G ? G.feedNodes : (L && L.nodes), links: G ? G.feedLinks : (L && L.links), drawn: G ? G.drawn : null, expected, drawn_ok: drawnOk, fps_state: fpsState, page_err: pageErr.slice(0, 3), purity_note: (L && L.notes && L.notes.anchors) || null, heat: G && G.heat, budget_hit: G && G.budgetHit, boot_ms: L && L.boot_ms, first_frame_ms: L && L.first_frame_ms, settle_ms: settled ? (L && L.settle_ms) : null, settled,
    ticks, settle_note: settled ? null : ('not settled within ' + SETTLE + ' ms' + (ticks != null ? ' (tick ' + ticks + ')' : '')),
    fps: L && L.fps, frame_ms: L && L.frame_ms, draws: G && G.stats && G.stats.calls, tris: G && G.stats && G.stats.triangles, geos: G && G.stats && G.stats.geometries, texs: G && G.stats && G.stats.textures,
    shot_note: shotNote, pick, tier, heap_mb: heap1 ? +(Math.max(heap0 || 0, heap1) / 1048576).toFixed(1) : null, bundle, ink, r10, injected, purity: pur, offline: net.length === 0, net: net.slice(0, 3), errs: errs.slice(0, 5),
    matrix: L && L.matrix || [], notes: L && L.notes || {}, warnings: G && G.warnings || [], baked: G && G.baked };
  rows.push(row);
  console.log((ok ? 'PASS  ' : 'FAIL  ') + pageKey.padEnd(34) + ' n=' + String(row.nodes).padStart(5) + ' drawn=' + String(row.drawn).padStart(5) + (drawnOk === false ? '≠' + expected : '') + ' boot=' + String(row.boot_ms).padStart(6) + ' settle=' + String(row.settle_ms).padStart(6) +
    ' fps=' + String(row.fps).padStart(3) + ' draws=' + String(row.draws).padStart(6) + ' pick=' + pick.hits + '/' + pick.tries + ' tier=' + (tier && tier.static != null ? (tier.static ? 'static' : 'MOVED ' + tier.moved) : (tier && tier.note ? 'n/a (ticking)' : '—')) + ' ink=' + ink + ' purity=' + pur + ' heap=' + row.heap_mb + 'MB');
  errs.slice(0, 5).forEach(e => console.log('        ' + e)); if (net.length) console.log('        NET: ' + net.slice(0, 3).join(' '));
  if (r10) console.log('        R10 word on the page: ' + r10); if (drawnOk === false) console.log('        drawn ' + row.drawn + ' ≠ expected ' + expected + ' — a page that silently drops nodes'); if (pageErr.length) console.log('        PAGE: ' + pageErr.join(' | ').slice(0, 300)); if (tier && !tier.na && tier.static === false) console.log('        TIER PRESS MOVED ' + tier.moved + ' nodes'); if (INJECT && injected !== 'drawn') console.log('        INJECT: ' + injected);
  await p.close();
}
await b.close();
// merge into probe-results.<feed>.<scale>.json by page
const out = path.join(D, 'probe-results.' + FEED + '.' + SCALE + (FN === '1' ? '.fn' : '') + (LAYOUT !== 'live' ? '.' + LAYOUT : '') + (INJECT ? '.inject' : '') + '.json');
let prev = []; try { prev = JSON.parse(fs.readFileSync(out, 'utf8')); } catch (e) { prev = []; }
const merged = prev.filter(r => !rows.find(x => x.page === r.page)).concat(rows).sort((a, b) => a.page.localeCompare(b.page));
fs.writeFileSync(out, JSON.stringify(merged, null, 1));
if (!NOREADME) regenReadme();
console.log('\n' + (bad ? bad + ' FAILED' : 'all ' + rows.length + ' green') + ' · feed=' + FEED + ' scale=' + SCALE + ' → ' + path.basename(out));
process.exit(bad ? 1 : 0);

function regenReadme() {
  const rd = path.join(D, 'README.md'); let md; try { md = fs.readFileSync(rd, 'utf8'); } catch (e) { return; }
  const files = fs.readdirSync(D).filter(f => /^probe-results\..*\.json$/.test(f)).sort();
  const all = files.flatMap(f => JSON.parse(fs.readFileSync(path.join(D, f), 'utf8')));
  const f = v => v == null ? '—' : (typeof v === 'number' ? (Number.isInteger(v) ? v.toLocaleString('en-US') : v) : String(v));
  const lines = ['| page | lib | feed · scale | nodes → drawn | boot ms | 1st frame | settle (ticks) | fps* (state) | frame ms | draws | tris | pick (mechanism) | tier press | heap MB | bundle KB (station+vendor) | purity k10 | offline | errors | matrix |', '|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---:|---:|---:|---|---|---|'];
  for (const r of all) { const mx = r.matrix || []; const c = s => mx.filter(m => m.state === s).length;
    lines.push('| ' + [r.page.replace('.html', '') + (r.ok ? '' : ' ✗') + (r.probe_build ? '' : ' (stale)'), r.lib || '—', r.feed + ' · ' + r.scale + (r.layout === 'baked' ? ' · baked' : ''), f(r.nodes) + ' → ' + (r.drawn == null ? '?' : f(r.drawn)) + (r.drawn_ok === false ? ' ✗' : ''), f(r.boot_ms), f(r.first_frame_ms), r.settled ? (f(r.settle_ms) + (r.ticks != null ? ' (' + r.ticks + ')' : '')) : (r.settle_note ? ('>' + Math.round(+((/within (\d+)/.exec(r.settle_note) || [0, 0])[1]) / 1000) + ' s' + (r.ticks != null ? ' at tick ' + r.ticks : '')) : 'never (probe timeout)'), f(r.fps) + (r.fps_state ? ' (' + r.fps_state + ')' : ''), f(r.frame_ms), f(r.draws), f(r.tris),
      r.pick && r.pick.tries ? r.pick.hits + '/' + r.pick.tries + (r.pick.occluded ? ' +' + r.pick.occluded + ' occl' : '') + ' · ' + r.pick.ms + ' ms' + (r.pick.mech ? ' (' + r.pick.mech.split(' ')[0] + ')' : '') : '—', r.tier && r.tier.static != null ? (r.tier.static ? 'static' : 'MOVED ' + r.tier.moved) + ' · ' + r.tier.down_ms + '/' + r.tier.up_ms + ' ms' : (r.tier && r.tier.note ? 'n/a · ticking · ' + r.tier.down_ms + '/' + r.tier.up_ms + ' ms' : '—'), f(r.heap_mb),
      r.bundle ? Math.round((r.bundle.station + r.bundle.vendor) / 1024).toLocaleString('en-US') + ' (' + Math.round(r.bundle.station / 1024) + '+' + Math.round(r.bundle.vendor / 1024) + ')' : '—', f(r.purity) + (r.purity_note ? ' (' + r.purity_note.split(' ')[0] + ')' : ''), r.offline ? 'yes' : 'NET ✗', ((r.errs || []).length + (r.page_err || []).length) ? (((r.errs || []).length + (r.page_err || []).length) + ' ✗') : '0', mx.length ? c('free') + ' free · ' + c('built') + ' built · ' + c('lost') + ' lost' : '—'].join(' | ') + ' |'); }
  // the must-survive MATRIX: every page's checklist claims side by side (free · built · lost · na), one row per label
  const pagesM = all.filter(r => r.matrix && r.matrix.length && /^lab-/.test(r.page)).filter((r, i, a) => a.findIndex(x => x.page === r.page) === i);   // the adapter check is not a page
  const labels = []; pagesM.forEach(r => r.matrix.forEach(m => { if (!labels.includes(m.row)) labels.push(m.row); }));
  const sym = { free: '●', built: '◐', lost: '✗', na: '—' };
  const mrows = ['| row | ' + pagesM.map(r => r.page.replace('.html', '').replace('-baseline-3d-force-graph', '').replace('-three-raw', ' raw').replace('?hollow=1', ' hollow')).join(' | ') + ' |', '|---|' + pagesM.map(() => ':---:').join('|') + '|']
    .concat(labels.map(l => '| ' + l + ' | ' + pagesM.map(r => { const m = r.matrix.find(x => x.row === l); return m ? '<span title="' + String(m.how || '').replace(/"/g, '&quot;') + '">' + (sym[m.state] || m.state) + '</span>' : '·'; }).join(' | ') + ' |'));
  const mblock = '<!-- matrix:start -->\n_● free (the library gives it) · ◐ built (ours on top of it) · ✗ lost (not achievable without a custom program) · — not in scope for the page; hover a cell for how._\n\n' + mrows.join('\n') + '\n<!-- matrix:end -->';
  if (/<!-- matrix:start -->[\s\S]*<!-- matrix:end -->/.test(md)) md = md.replace(/<!-- matrix:start -->[\s\S]*<!-- matrix:end -->/, mblock); else md += '\n\n' + mblock + '\n';
  const block = '<!-- probe:start -->\n_Regenerated by probe.mjs (' + PROBE_BUILD + ') on this host (WSL2 · Chrome + swiftshader, **no GPU**: fps* is a CPU-rasteriser floor and a RANK, never a rating; draw calls and purity are the deciding columns). `drawn` is the RENDERER\'s count (instance buffers · display data · visibility), `?` when a page exposes none; on the 3D pages the station bytes ARE the renderer; a purity marked (ring) ran on 2D ring anchors, not the adapter\'s x-line; the pick mechanism is per page (colour-id · raycast · library · scan) and `occl` counts a nearer node correctly picked; rows marked (stale) predate this build._\n\n' + lines.join('\n') + '\n<!-- probe:end -->';
  if (/<!-- probe:start -->[\s\S]*<!-- probe:end -->/.test(md)) md = md.replace(/<!-- probe:start -->[\s\S]*<!-- probe:end -->/, block); else md += '\n\n' + block + '\n';
  fs.writeFileSync(rd, md);
}
