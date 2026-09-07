/* debug.mjs — open one lab page headless and print every page error WITH its stack + the console (a quick look, not a measurement).
     node debug.mjs lab-02-sigma.html "feed=example&scale=core" */
import { createRequire } from 'module'; import path from 'path'; import { fileURLToPath } from 'url';
const D = path.dirname(fileURLToPath(import.meta.url)), REPO = path.resolve(D, '../../../..');
const { chromium } = createRequire(import.meta.url)(process.env.GABE_PW_DIR || path.join(REPO, 'docs/design/graft-adoption/spike/_build/node_modules/playwright-core'));
const page = process.argv[2], q = process.argv[3] || 'feed=example';
const b = await chromium.launch({ executablePath: process.env.GABE_CHROME_BIN || '/usr/bin/google-chrome-stable', args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--no-sandbox', '--disable-gpu-sandbox', '--disable-dev-shm-usage'] });
const p = await b.newPage({ viewport: { width: 1400, height: 860 } });
p.on('pageerror', e => console.log('PAGEERROR', e.message, '\n', (e.stack || '').split('\n').slice(0, 6).join('\n')));
p.on('console', m => { if (m.type() !== 'log') console.log('CONSOLE', m.type(), m.text().slice(0, 300)); });
await p.goto('file://' + path.join(D, page) + '?' + q, { timeout: 60000 });
await p.waitForFunction('window.__LAB_READY===true', { timeout: +(process.env.DBG_WAIT || 25000) }).then(() => console.log('READY')).catch(() => console.log('NOT READY in time'));
console.log('LAB', JSON.stringify(await p.evaluate(() => { const L = window.__LAB || {}; return { lib: L.lib, nodes: L.nodes, drawn: L.drawn, err: L.err, notes: L.notes, feed: !!window.GABE_FEED, labg: !!window.LABG }; })));
await b.close();
