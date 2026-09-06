// _a3_fe_extract.mjs — the FRONTEND arm's compiler pass (READ-ONLY). Runs the twin's OWN
// `typescript` (the one dependency every TS frontend ships) over its tsconfig and emits, per
// source file: resolved imports, exported symbols (kind · JSX · hook), per-export body REFS
// (jsx tags · calls · type refs · identifiers) and the import BINDINGS that resolve each local
// name to the file+symbol that declares it (barrels followed by the checker, not by us).
// _a3_fe.py classifies + wires on top of this. Nothing here writes to the tree.
//
//   node _a3_fe_extract.mjs <web_root> [out.json] [repo_root]   (one summary line on stderr)
//   repo_root = the root every path is emitted RELATIVE to (the caller's REPO_ROOT, so ids join
//   _a3_web's `web:<rel>` screens + graft's node paths); default = the nearest .git ancestor.
//
// Determinism: files sorted, refs deduped + sorted, no wallclock. Honest-empty is the
// CALLER's job — a missing typescript exits 3 with a reason on stderr; a missing tsconfig 4.
import { createRequire } from 'node:module';
import path from 'node:path';
import fs from 'node:fs';

const WEB = path.resolve(process.argv[2] || '.');
const OUT = process.argv[3] || null;
const TS_DIR = process.env.GABE_TS_DIR || null;          // override: where `typescript` lives (batteries)
let ts;
try {
  const req = createRequire(path.join(WEB, 'package.json'));
  ts = TS_DIR ? createRequire(path.join(TS_DIR, 'package.json'))('typescript') : req('typescript');
} catch (e) {
  process.stderr.write('fe-extract: typescript not resolvable from ' + (TS_DIR || WEB) + ' (' + e.message.split('\n')[0] + ')\n');
  process.exit(3);
}
const cfgPath = ts.findConfigFile(WEB, ts.sys.fileExists, 'tsconfig.json');
if (!cfgPath) { process.stderr.write('fe-extract: no tsconfig.json at or above ' + WEB + '\n'); process.exit(4); }
const cfg = ts.readConfigFile(cfgPath, ts.sys.readFile);
const parsed = ts.parseJsonConfigFileContent(cfg.config || {}, ts.sys, path.dirname(cfgPath));
// PROJECT REFERENCES: the default Vite React+TS root tsconfig is a stub — files:[] + references to
// tsconfig.app.json/tsconfig.node.json, no include. Its own fileNames is empty, so expand the
// referenced configs and union their fileNames, else the WHOLE frontend silently drops (147 files → 0).
let fileNames = parsed.fileNames || [];
let options = parsed.options;
if (fileNames.length === 0 && parsed.projectReferences && parsed.projectReferences.length) {
  const seen = new Set(); const merged = [];
  for (const ref of parsed.projectReferences) {
    let rp = ref && ref.path; if (!rp) continue;
    if (ts.sys.directoryExists && ts.sys.directoryExists(rp)) rp = ts.findConfigFile(rp, ts.sys.fileExists, 'tsconfig.json');
    if (!rp || !ts.sys.fileExists(rp)) continue;
    const rcfg = ts.readConfigFile(rp, ts.sys.readFile);
    const rparsed = ts.parseJsonConfigFileContent(rcfg.config || {}, ts.sys, path.dirname(rp));
    for (const fn of (rparsed.fileNames || [])) { if (!seen.has(fn)) { seen.add(fn); merged.push(fn); } }
    options = Object.assign({}, rparsed.options, options);   // root options keep precedence
  }
  if (merged.length) fileNames = merged;
}
const program = ts.createProgram({ rootNames: fileNames, options });
const checker = program.getTypeChecker();

// the repo root = nearest ancestor of WEB holding .git (else WEB's grandparent); paths are
// emitted RELATIVE to it so they join _a3_web's screen ids and graft's node paths.
let ROOT = process.argv[4] ? path.resolve(process.argv[4]) : WEB;
if (!process.argv[4]) {
  while (ROOT !== path.dirname(ROOT) && !fs.existsSync(path.join(ROOT, '.git'))) ROOT = path.dirname(ROOT);
  if (ROOT === path.dirname(ROOT)) ROOT = path.resolve(WEB, '..', '..');
}
const rel = f => path.relative(ROOT, f).split(path.sep).join('/');
const SRC = fs.existsSync(path.join(WEB, 'src')) ? path.join(WEB, 'src') + path.sep : WEB + path.sep;
const NOISE = /\/(node_modules|dist|build|storybook-static|coverage|\.next|\.turbo)\//;
const isTest = f => /\.(test|spec)\.(ts|tsx|js|jsx)$|\/__tests__\/|\/__mocks__\/|\/test\/|\/__regression__\/|\/e2e\/|\.e2e\./.test(f);

const leftmost = n => { while (n && (ts.isPropertyAccessExpression(n) || ts.isQualifiedName(n))) n = ts.isPropertyAccessExpression(n) ? n.expression : n.left; return n && ts.isIdentifier(n) ? n.text : null; };
const declKind = d => {
  if (!d) return 'other';
  if (ts.isFunctionDeclaration(d) || ts.isFunctionExpression(d) || ts.isArrowFunction(d) || ts.isMethodDeclaration(d)) return 'function';
  if (ts.isClassDeclaration(d)) return 'class';
  if (ts.isInterfaceDeclaration(d)) return 'interface';
  if (ts.isTypeAliasDeclaration(d)) return 'type';
  if (ts.isEnumDeclaration(d)) return 'enum';
  if (ts.isVariableDeclaration(d)) {
    const init = d.initializer;
    if (!init) return 'const';
    if (ts.isArrowFunction(init) || ts.isFunctionExpression(init)) return 'function';
    if (ts.isCallExpression(init)) {
      // unwrap `create<S>()(...)` (zustand curried) + `memo(...)`/`forwardRef(...)`
      let c = init; while (ts.isCallExpression(c.expression)) c = c.expression;
      return 'call:' + (leftmost(c.expression) || c.expression.getText(d.getSourceFile()).slice(0, 30));
    }
    return 'const';
  }
  return 'other';
};
const refsOf = node => {
  const jsx = new Set(), calls = new Set(), types = new Set(), idents = new Set(), ctxArgs = new Set();
  let hasJsx = false;
  const walk = n => {
    if (ts.isJsxOpeningElement(n) || ts.isJsxSelfClosingElement(n)) { hasJsx = true; const t = leftmost(n.tagName); if (t && /^[A-Z]/.test(t)) jsx.add(t); }
    else if (ts.isJsxFragment(n)) hasJsx = true;
    else if (ts.isCallExpression(n)) {
      const c = leftmost(n.expression); if (c) calls.add(c);
      if (c && /^use(Context|Store|Atom|Selector|AtomValue|SetAtom|Reducer)$/.test(c) && n.arguments[0] && ts.isIdentifier(n.arguments[0])) ctxArgs.add(n.arguments[0].text);
    }
    else if (ts.isTypeReferenceNode(n)) { const t = leftmost(n.typeName); if (t) types.add(t); }
    else if (ts.isIdentifier(n)) idents.add(n.text);
    ts.forEachChild(n, walk);
  };
  walk(node);
  return { hasJsx, jsx: [...jsx].sort(), calls: [...calls].sort(), types: [...types].sort(), idents: [...idents].sort(), ctxArgs: [...ctxArgs].sort() };
};

// ── D5 (operator 2026-09-05): a TYPE's MEMBERS — the frontend's schema fields — and a STORE's SHAPE — the value
//    type on createContext<T>() / create<T>()(…), the frontend's table columns. A member = [name, type text];
//    a method signature = name(). The shape keeps the type text, the type-reference names inside it (the arm
//    resolves them to type pieces → fields + a typed wire) and, for an inline literal, its members directly.
const STORE_CALLEES = /^(create|createStore|createContext|createSlice|configureStore|atom|atomWithStorage|atomFamily|signal|observable|makeAutoObservable|proxy|createSignal|writable|readable)$/;
const typeText = (t, sf) => t ? t.getText(sf).replace(/\s+/g, ' ').slice(0, 80) : '';
const membersOfNodes = (ms, sf) => { const out = []; for (const m of ms) { if ((ts.isPropertySignature(m) || ts.isMethodSignature(m)) && m.name) { const nm = m.name.getText(sf); out.push([nm, ts.isMethodSignature(m) ? nm + '()' : typeText(m.type, sf)]); } } return out; };
const membersOf = d => {
  if (!d) return null; const sf = d.getSourceFile();
  if (ts.isInterfaceDeclaration(d)) return membersOfNodes(d.members, sf);
  if (ts.isTypeAliasDeclaration(d) && ts.isTypeLiteralNode(d.type)) return membersOfNodes(d.type.members, sf);
  return null;
};
const shapeOf = d => {
  if (!d || !ts.isVariableDeclaration(d) || !d.initializer || !ts.isCallExpression(d.initializer)) return null;
  let c = d.initializer; while (ts.isCallExpression(c.expression)) c = c.expression;   // create<S>()(…) — the inner call carries the type args
  const callee = leftmost(c.expression); if (!callee || !STORE_CALLEES.test(callee)) return null;
  const ta = c.typeArguments && c.typeArguments[0]; const sf = d.getSourceFile();
  if (!ta) return { text: '', refs: [], members: null };
  const refs = new Set(); const walk = n => { if (ts.isTypeReferenceNode(n)) { const t = leftmost(n.typeName); if (t) refs.add(t); } ts.forEachChild(n, walk); }; walk(ta);
  let members = ts.isTypeLiteralNode(ta) ? membersOfNodes(ta.members, sf) : null;
  if (!members) {                         // a named type — exported or NOT (useUiStore's local UiState): ask the checker for its properties
    try {
      let t = checker.getTypeAtLocation(ta); if (t.getNonNullableType) t = t.getNonNullableType();   // AuthContextValue | undefined → AuthContextValue
      if (t.flags & ts.TypeFlags.Object) {   // object types only — a primitive (string) would list its prototype methods
        const props = t.getProperties();
        if (props.length) members = props.map(p => [p.name, checker.typeToString(checker.getTypeOfSymbolAtLocation(p, ta)).replace(/\s+/g, ' ').slice(0, 80)]);
      }
    } catch {}
  }
  return { text: typeText(ta, sf), refs: [...refs].sort(), members };
};

const files = {};
for (const sf of program.getSourceFiles()) {
  const f = sf.fileName;
  if (!f.startsWith(SRC) || sf.isDeclarationFile || f.endsWith('.d.ts') || NOISE.test(f) || isTest(f)) continue;
  const story = /\.stories\.(ts|tsx)$/.test(f);
  const rec = { story, imports: [], bindings: {}, exports: [] };
  // ── imports (static · re-export · dynamic) resolved by the compiler ──────────────────
  const seen = new Set();
  const addImport = (spec, flags) => {
    const r = ts.resolveModuleName(spec, f, parsed.options, ts.sys);
    const rm = r.resolvedModule;
    const to = rm && !rm.isExternalLibraryImport ? rel(rm.resolvedFileName) : null;
    const key = spec + '|' + (to || '');
    if (seen.has(key)) return; seen.add(key);
    rec.imports.push({ spec, to, external: !!(rm && rm.isExternalLibraryImport), ...flags });
  };
  const walkTop = n => {
    if ((ts.isImportDeclaration(n) || ts.isExportDeclaration(n)) && n.moduleSpecifier && ts.isStringLiteral(n.moduleSpecifier)) {
      addImport(n.moduleSpecifier.text, { typeOnly: !!(n.importClause && n.importClause.isTypeOnly) || !!n.isTypeOnly, dynamic: false, reexport: ts.isExportDeclaration(n) });
    }
    if (ts.isCallExpression(n) && n.expression.kind === ts.SyntaxKind.ImportKeyword && n.arguments[0] && ts.isStringLiteral(n.arguments[0])) addImport(n.arguments[0].text, { typeOnly: false, dynamic: true, reexport: false });
    ts.forEachChild(n, walkTop);
  };
  walkTop(sf);
  // ── bindings: local name → the file+symbol that DECLARES it (checker follows barrels) ──
  for (const st of sf.statements) {
    if (!ts.isImportDeclaration(st) || !st.importClause) continue;
    const ic = st.importClause;
    const bind = (localId, imported) => {
      let s = checker.getSymbolAtLocation(localId); if (!s) return;
      try { if (s.flags & ts.SymbolFlags.Alias) s = checker.getAliasedSymbol(s); } catch { return; }
      const d = (s.declarations || [])[0]; if (!d) return;
      const df = d.getSourceFile().fileName;
      if (NOISE.test(df) || df.includes('/node_modules/')) { rec.bindings[localId.text] = { ext: true }; return; }
      const nm = (d.name && ts.isIdentifier(d.name)) ? d.name.text : (s.name === 'default' ? imported : s.name);
      rec.bindings[localId.text] = { file: rel(df), name: nm, kind: declKind(d) };
    };
    if (ic.name) bind(ic.name, 'default');
    if (ic.namedBindings) {
      if (ts.isNamespaceImport(ic.namedBindings)) { const r = rec.imports.find(i => i.spec === st.moduleSpecifier.text); rec.bindings[ic.namedBindings.name.text] = r && r.to ? { file: r.to, name: '*', kind: 'namespace' } : { ext: true }; }
      else for (const el of ic.namedBindings.elements) bind(el.name, (el.propertyName || el.name).text);
    }
  }
  // ── LAZY bindings (2026-09-03): `const X = lazy(() => import("spec").then(m => ({ default: m.NAME })))` — React
  //    code-splitting. A lazy() const is NOT an import declaration, so the checker binds nothing and every `<X/>`
  //    in the file resolves to no piece — a whole route file's renders edges vanish (gustify routes/screens.tsx:
  //    13 routes, 0 renders wires). Bind it like a named import: the dynamic import's resolved file (already in
  //    rec.imports) + the mapped export, else `default`. An idiom (the callee is named lazy), never a name-list. ──
  for (const st of sf.statements) {
    if (!ts.isVariableStatement(st)) continue;
    for (const dcl of st.declarationList.declarations) {
      if (!dcl.initializer || !ts.isIdentifier(dcl.name) || !ts.isCallExpression(dcl.initializer)) continue;
      const callee = dcl.initializer.expression;
      const cname = ts.isIdentifier(callee) ? callee.text : (ts.isPropertyAccessExpression(callee) ? callee.name.text : '');
      if (cname !== 'lazy') continue;
      let spec = null, mapped = null;
      const walkLazy = n => {
        if (ts.isCallExpression(n) && n.expression.kind === ts.SyntaxKind.ImportKeyword && n.arguments[0] && ts.isStringLiteral(n.arguments[0])) spec = n.arguments[0].text;
        if (ts.isPropertyAssignment(n) && ts.isIdentifier(n.name) && n.name.text === 'default' && ts.isPropertyAccessExpression(n.initializer)) mapped = n.initializer.name.text;
        ts.forEachChild(n, walkLazy);
      };
      walkLazy(dcl.initializer);
      if (!spec) continue;
      const r = rec.imports.find(i => i.spec === spec);
      rec.bindings[dcl.name.text] = (r && r.to) ? { file: r.to, name: mapped || 'default', kind: 'lazy' } : { ext: true };
    }
  }
  // ── exports: the symbols this file OFFERS (+ their body refs) ─────────────────────────
  const msym = checker.getSymbolAtLocation(sf);
  const exps = msym ? checker.getExportsOfModule(msym) : [];
  for (const e of exps) {
    let s = e; try { if (s.flags & ts.SymbolFlags.Alias) s = checker.getAliasedSymbol(s); } catch {}
    const d = (s.declarations || [])[0];
    const df = d ? rel(d.getSourceFile().fileName) : null;
    const name = (d && d.name && ts.isIdentifier(d.name)) ? d.name.text : e.name;
    const local = df === rel(f);
    const ex = { name, isDefault: e.name === 'default', kind: declKind(d), reexport: local ? null : df };
    if (d && ts.isTypeAliasDeclaration(d) && /^components\s*\[/.test(d.type.getText(d.getSourceFile())))
      ex.apiAlias = true;                        // `type X = components["schemas"]["X"]` — a REFERENCE to the generated contract, not a shape
    if (local && d) {
      // the body = the whole declaration (a `const X = memo(() => <jsx/>)` keeps its JSX)
      const body = ts.isVariableDeclaration(d) ? d : d;
      Object.assign(ex, refsOf(body));
      const mem = membersOf(d); if (mem && mem.length) ex.members = mem;   // D5
      const sh = shapeOf(d); if (sh) ex.shape = sh;                       // D5
      ex.span = [sf.getLineAndCharacterOfPosition(d.getStart(sf)).line + 1, sf.getLineAndCharacterOfPosition(d.getEnd()).line + 1];
    }
    rec.exports.push(ex);
  }
  rec.exports.sort((a, b) => a.name < b.name ? -1 : a.name > b.name ? 1 : 0);
  // module-scope refs (calls outside any export — a side-effect module's wiring)
  const top = refsOf(sf);
  rec.file_refs = { calls: top.calls, jsx: top.jsx, hasJsx: top.hasJsx };
  files[rel(f)] = rec;
}
const keys = Object.keys(files).sort();
const out = { version: 1, web: rel(WEB) || '.', ts: ts.version, files: keys.length, byFile: Object.fromEntries(keys.map(k => [k, files[k]])) };
const text = JSON.stringify(out);
if (OUT) fs.writeFileSync(OUT, text); else process.stdout.write(text);
const all = keys.map(k => files[k]);
const imp = all.flatMap(r => r.imports);
process.stderr.write(`fe-extract: ${keys.length} files · ${imp.filter(i => i.to).length} internal import sites · ${imp.filter(i => i.external).length} external · ${all.flatMap(r => r.exports).length} exports · ts ${ts.version}\n`);
