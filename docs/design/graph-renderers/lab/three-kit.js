/* three-kit.js — the shared three.js toolkit for the 3D pages (lab-00 ?hollow=1 · lab-01 raw · lab-04 cosmos→three). Reads window.THREE
   (r185 from the station's own 3d-bundle.js). Everything here is INSTANCED: one draw call per layer, never one per node.
     TK.formGeo(form)                 the station's primitiveMesh geometry per KINDS form (ring · cube · cylinder · octa · panel · knot · cone · wire · slab · pod · container)
     TK.glyphLayers(nodes, colorOf)   one InstancedMesh per form → {meshes[], setPos(i,x,y,z), setVisible(i,on), pickIndex(mesh,instanceId)}
     TK.sphereLayer(n, color, op)     one InstancedMesh sphere (bubbles · hull seeds)
     TK.badgeLayer(nodes, slotFn)     badge discs as an atlas quad InstancedMesh (slot A + B) — the six families drawn as canvas discs with the family colour + 1–2 letters
     TK.labelLayer(nodes, labelOf, max)  canvas atlas + instanced billboard quads (1 draw call)
     TK.wireLayers(links, feed)       one LineSegments per CONN kind (7) with per-vertex colour + the kind's dash (LineDashedMaterial needs lineDistances — rewritten on update)
     TK.particleLayer(links, n)       one Points layer of directional particles along the chosen links
     TK.hullGeometry(points, pad)     ConvexGeometry over the icosahedron-seeded point cloud (the station's hull())
     TK.orbit(camera, dom)            a hand-written orbit rig (OrbitControls is ESM-only in three) → {fit(r), target}
     TK.picker(renderer, camera)      colour-id picking over registered instanced meshes → pick(x,y) → {mesh, instanceId} | null */
(function () {
  'use strict';
  var T = window.THREE; if (!T) { window.TK_ERR = 'window.THREE missing'; return; }
  var TK = window.TK = {};
  var R = 7, GEO = {};
  TK.formGeo = function (form) {
    if (GEO[form]) return GEO[form];
    var g;
    if (form === 'ring') g = new T.TorusGeometry(R * 0.9, R * 0.34, 10, 22);
    else if (form === 'cube') g = new T.BoxGeometry(R * 1.5, R * 1.5, R * 1.5);
    else if (form === 'cylinder') g = new T.CylinderGeometry(R * 0.85, R * 0.85, R * 1.8, 18);
    else if (form === 'octa') g = new T.OctahedronGeometry(R * 1.15, 0);
    else if (form === 'panel') g = new T.BoxGeometry(R * 2.1, R * 1.5, R * 0.5);
    else if (form === 'knot') g = new T.TorusKnotGeometry(R * 0.62, R * 0.24, 48, 8);
    else if (form === 'cone') g = new T.ConeGeometry(R * 0.95, R * 1.9, 16);
    else if (form === 'wire') g = new T.BoxGeometry(R * 1.4, R * 1.4, R * 1.4);
    else if (form === 'slab') g = new T.BoxGeometry(R * 2.0, R * 0.55, R * 2.0);
    else if (form === 'pod') g = new T.SphereGeometry(R * 2.1, 12, 9);
    else if (form === 'container') g = new T.IcosahedronGeometry(R * 2.2, 0);
    else g = new T.SphereGeometry(R, 14, 10);
    GEO[form] = g; return g;
  };
  var dummy = new T.Object3D(), tmpC = new T.Color();
  function instanced(geo, mat, n) { var m = new T.InstancedMesh(geo, mat, n); m.instanceMatrix.setUsage(T.DynamicDrawUsage); m.frustumCulled = false; m.count = n; return m; }
  function setAt(mesh, i, x, y, z, s) { dummy.position.set(x, y, z); dummy.scale.setScalar(s); dummy.updateMatrix(); mesh.setMatrixAt(i, dummy.matrix); }
  TK.hide = function (mesh, i) { dummy.position.set(0, 0, 0); dummy.scale.setScalar(0); dummy.updateMatrix(); mesh.setMatrixAt(i, dummy.matrix); };   // a zero-scale instance draws nothing and costs no draw call

  /* ── glyphs: one InstancedMesh per form ─────────────────────────────────────────────────────────────────────── */
  TK.glyphLayers = function (nodes, colorOf, formOf, scale) {
    scale = scale || (10 / 13);
    var byForm = {}; nodes.forEach(function (n, i) { var f = formOf(n); (byForm[f] = byForm[f] || []).push(i); });
    var meshes = [], slot = new Array(nodes.length), vis = new Uint8Array(nodes.length).fill(1), pos = new Float32Array(nodes.length * 3);
    Object.keys(byForm).forEach(function (f) {
      var idx = byForm[f], wire = f === 'wire' || f === 'container';
      var mat = wire ? new T.MeshBasicMaterial({ wireframe: true, transparent: true, opacity: f === 'container' ? 0.4 : 0.96 }) : new T.MeshLambertMaterial({ emissive: 0xffffff, emissiveIntensity: 0.35, transparent: true, opacity: 0.96 });
      var m = instanced(TK.formGeo(f), mat, idx.length); m.name = 'glyph:' + f; m.userData.nodeIndex = idx;
      idx.forEach(function (ni, k) { slot[ni] = { mesh: m, k: k }; tmpC.set(colorOf(nodes[ni])); m.setColorAt(k, tmpC); });
      m.instanceColor.needsUpdate = true; meshes.push(m);
    });
    return { meshes: meshes, slot: slot,
      setPos: function (i, x, y, z) { pos[i * 3] = x; pos[i * 3 + 1] = y; pos[i * 3 + 2] = z; var s = slot[i]; if (vis[i]) setAt(s.mesh, s.k, x, y, z, scale); else TK.hide(s.mesh, s.k); },
      setVisible: function (i, on) { vis[i] = on ? 1 : 0; var s = slot[i]; if (on) setAt(s.mesh, s.k, pos[i * 3], pos[i * 3 + 1], pos[i * 3 + 2], scale); else TK.hide(s.mesh, s.k); },
      setColor: function (i, c) { var s = slot[i]; tmpC.set(c); s.mesh.setColorAt(s.k, tmpC); s.mesh.instanceColor.needsUpdate = true; },
      flush: function () { meshes.forEach(function (m) { m.instanceMatrix.needsUpdate = true; }); },
      nodeOf: function (mesh, instanceId) { var ix = mesh.userData.nodeIndex; return ix ? ix[instanceId] : null; } };
  };
  TK.sphereLayer = function (n, color, op, r, seg) {
    var m = instanced(new T.SphereGeometry(r || 6.2, seg || 12, seg ? Math.max(6, seg - 4) : 9), new T.MeshBasicMaterial({ color: color, transparent: true, opacity: op, depthWrite: false }), n); m.name = 'spheres';
    return { mesh: m, set: function (i, x, y, z, s) { setAt(m, i, x, y, z, s == null ? 1 : s); }, hide: function (i) { TK.hide(m, i); }, flush: function () { m.instanceMatrix.needsUpdate = true; } };
  };

  /* ── atlas quads (badges · labels): one canvas texture, one InstancedMesh of billboard quads, aUv per instance ──── */
  function atlasMaterial(tex, w, h) {
    var mat = new T.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false, alphaTest: 0.02 });
    mat.onBeforeCompile = function (sh) {
      sh.vertexShader = 'attribute vec4 aUv;\nattribute vec2 aSize;\nvarying vec4 vAUv;\n' + sh.vertexShader
        .replace('#include <begin_vertex>', '#include <begin_vertex>\n vAUv = aUv;')
        .replace('#include <project_vertex>', ['vec4 mv = modelViewMatrix * instanceMatrix * vec4(0.0,0.0,0.0,1.0);', 'mv.xy += position.xy * aSize;', 'gl_Position = projectionMatrix * mv;'].join('\n'));
      sh.fragmentShader = 'varying vec4 vAUv;\n' + sh.fragmentShader.replace('#include <map_fragment>', 'vec4 tc = texture2D(map, vAUv.xy + vMapUv * vAUv.zw); diffuseColor *= tc;');
    };
    return mat;
  }
  function quadLayer(tex, n, uvs, sizes) {
    var q = new T.PlaneGeometry(1, 1); q.setAttribute('aUv', new T.InstancedBufferAttribute(uvs, 4)); q.setAttribute('aSize', new T.InstancedBufferAttribute(sizes, 2));
    var m = instanced(q, atlasMaterial(tex), n); m.renderOrder = 5; m.name = 'atlas';
    return { mesh: m, set: function (i, x, y, z) { setAt(m, i, x, y, z, 1); }, hide: function (i) { TK.hide(m, i); }, flush: function () { m.instanceMatrix.needsUpdate = true; } };
  }
  /* badge discs: family colour + 1–2 letters, the 30° hue-clearance is the family's own colour choice (mirrors the station's canvas badges) */
  /* the station's __BADGE_COL literal (gabe-universe.html), verbatim — a badge never wears its host body's colour */
  var BADGECOL = { method: { GET: '#22c55e', POST: '#3b82f6', PUT: '#f97316', PATCH: '#eab308', DELETE: '#ef4444', BOOT: '#8a8f98', TASK: '#f0abfc' },
    role: { accessor: '#ef4444', caller: '#3b82f6', gate: '#eab308', pure: '#8794ab' },
    feclass: { connector: '#f97316', container: '#a855f7', leaf: '#84cc16', 'private': '#8794ab', detached: '#fb7185' },
    mclass: { api: '#3b82f6', 'render-fn': '#d946ef', model: '#14b8a6', config: '#8794ab', lib: '#84cc16', logic: '#22d3ee' },
    hrole: { fetcher: '#3b82f6', streamer: '#8b5cf6', store: '#ec4899', orchestrator: '#f59e0b', effect: '#ef4444', deriver: '#8794ab' },
    pclass: { llm: '#d946ef', embed: '#a3e635', vector: '#14b8a6', agent: '#8b5cf6', infra: '#8794ab', http: '#3b82f6', observability: '#ec4899', payments: '#22c55e' },
    delivery: { stream: '#06b6d4' }, count: { '*': '#06b6d4' } };
  TK.badgeColor = function (family, value) { var f = BADGECOL[family] || {}; return f[value] || f['*'] || '#8794ab'; };
  TK.badgeAtlas = function (entries) {   // entries: [{family, value}] → {tex, uv(i)}
    var S = 64, COLS = 8, ROWS = Math.max(1, Math.ceil(entries.length / COLS)), cv = document.createElement('canvas'); cv.width = S * COLS; cv.height = S * ROWS; var c = cv.getContext('2d');
    entries.forEach(function (e, k) { var x = (k % COLS) * S, y = ((k / COLS) | 0) * S; c.fillStyle = TK.badgeColor(e.family, e.value); c.beginPath(); c.arc(x + S / 2, y + S / 2, S * 0.44, 0, 6.2832); c.fill();
      c.fillStyle = '#0b0e13'; c.font = '700 22px ui-sans-serif,system-ui,sans-serif'; c.textAlign = 'center'; c.textBaseline = 'middle'; var t = String(e.value || '?'); c.fillText(t.length > 3 ? t.slice(0, 2).toUpperCase() : t.toUpperCase(), x + S / 2, y + S / 2 + 1); });
    var tex = new T.CanvasTexture(cv); tex.colorSpace = T.SRGBColorSpace;
    return { tex: tex, uv: function (k) { return [(k % COLS) / COLS, 1 - (((k / COLS) | 0) + 1) / ROWS, 1 / COLS, 1 / ROWS]; } };
  };
  TK.badgeLayer = function (nodes, slotFn, size) {   // slotFn(n) → [{family,value}|null, {family,value}|null]; one instance per (node, slot) that has a badge
    var keys = {}, entries = [], items = [];
    nodes.forEach(function (n, i) { var s = slotFn(n) || []; for (var j = 0; j < 2; j++) { var b = s[j]; if (!b) continue; var key = b.family + ':' + b.value; if (keys[key] == null) { keys[key] = entries.length; entries.push(b); } items.push({ i: i, slot: j, k: keys[key] }); } });
    if (!items.length) return { mesh: null, items: items, set: function () {}, hide: function () {}, flush: function () {} };
    var atlas = TK.badgeAtlas(entries), uvs = new Float32Array(items.length * 4), sizes = new Float32Array(items.length * 2), sz = size || 6.5;
    items.forEach(function (it, q) { var u = atlas.uv(it.k); uvs[q * 4] = u[0]; uvs[q * 4 + 1] = u[1]; uvs[q * 4 + 2] = u[2]; uvs[q * 4 + 3] = u[3]; sizes[q * 2] = sz; sizes[q * 2 + 1] = sz; });
    var L = quadLayer(atlas.tex, items.length, uvs, sizes); L.mesh.name = 'badges'; L.items = items; L.atlas = atlas;
    L.place = function (i, x, y, z, br) { /* the station: slot A lower-right of the icon, slot B upper-right */ };
    return L;
  };
  TK.labelLayer = function (nodes, labelOf, max, opts) {
    opts = opts || {}; var cap = Math.min(max || 400, 4000), pick = []; for (var i = 0; i < nodes.length && pick.length < cap; i++) if (!opts.filter || opts.filter(nodes[i])) pick.push(i);
    if (!pick.length) return { mesh: null, pick: pick, set: function () {}, hide: function () {}, flush: function () {} };
    var CW = 256, CH = 32, COLS = 16, ROWS = Math.ceil(pick.length / COLS), cv = document.createElement('canvas'); cv.width = CW * COLS; cv.height = CH * ROWS; var c = cv.getContext('2d');   /* 16 cols × 256 = 4096 px wide; 4,000 labels = 250 rows = 8,000 px tall — the swiftshader texture ceiling; above the cap the rest go unlabelled and the page says so */
    c.font = '600 20px Menlo,Consolas,ui-monospace,monospace'; c.textBaseline = 'middle'; c.fillStyle = opts.color || '#cdd6ea';
    pick.forEach(function (ni, k) { var x = (k % COLS) * CW, y = ((k / COLS) | 0) * CH, t = String(labelOf(nodes[ni]) || ''); if (t.length > 20) t = t.slice(0, 19) + '…'; c.save(); c.beginPath(); c.rect(x, y, CW, CH); c.clip(); c.fillText(t, x + 4, y + CH / 2); c.restore(); });   /* 20 chars at 12 px/char fit the 256 px cell; a longer label is cut and marked, never bled into its neighbour */
    var tex = new T.CanvasTexture(cv); tex.colorSpace = T.SRGBColorSpace;
    var uvs = new Float32Array(pick.length * 4), sizes = new Float32Array(pick.length * 2);
    pick.forEach(function (ni, k) { uvs[k * 4] = (k % COLS) / COLS; uvs[k * 4 + 1] = 1 - (((k / COLS) | 0) + 1) / ROWS; uvs[k * 4 + 2] = 1 / COLS; uvs[k * 4 + 3] = 1 / ROWS; sizes[k * 2] = opts.w || 46; sizes[k * 2 + 1] = opts.h || 6; });
    var L = quadLayer(tex, pick.length, uvs, sizes); L.mesh.name = 'labels'; L.pick = pick; L.slotOf = {}; pick.forEach(function (ni, k) { L.slotOf[ni] = k; });
    return L;
  };

  /* ── wires: one LineSegments per CONN kind, per-vertex colour, the kind's dash ──────────────────────────────── */
  var DASH = { dashed: [1.7, 1.0], dotted: [0.35, 0.95], sparse: [1.4, 2.8], longdash: [2.6, 1.2] };
  TK.wireLayers = function (links, feed, colorOf) {   // colorOf(link, endIndex) → hex; returns {layers{kind}, update(posOf), setVisible(li,on)}
    var byKind = {}; links.forEach(function (l, i) { (byKind[l.kind] = byKind[l.kind] || []).push(i); });
    var layers = {}, slot = new Array(links.length), vis = new Uint8Array(links.length).fill(1);
    Object.keys(byKind).forEach(function (kind) { var idx = byKind[kind], cfg = feed.conn[kind] || feed.conn.calls, n = idx.length;
      var pos = new Float32Array(n * 6), col = new Float32Array(n * 6), geo = new T.BufferGeometry();
      geo.setAttribute('position', new T.BufferAttribute(pos, 3).setUsage(T.DynamicDrawUsage)); geo.setAttribute('color', new T.BufferAttribute(col, 3));
      idx.forEach(function (li, k) { slot[li] = { kind: kind, k: k }; for (var e = 0; e < 2; e++) { tmpC.set(colorOf(links[li], e) || cfg.color); col[k * 6 + e * 3] = tmpC.r; col[k * 6 + e * 3 + 1] = tmpC.g; col[k * 6 + e * 3 + 2] = tmpC.b; } });
      var dn = cfg.density || 1, base = DASH[cfg.style] || [1.2, 1], vc = true;   /* per-vertex colour carries the heat band AND the kind colour (colorOf returns cfg.color where the station draws flat) — the station gradients only fk · rollup */
      var mat = cfg.style === 'solid' ? new T.LineBasicMaterial({ vertexColors: vc, transparent: true, opacity: Math.min(1, cfg.trust) })
        : new T.LineDashedMaterial({ vertexColors: vc, transparent: true, opacity: Math.min(1, cfg.trust), dashSize: base[0] / dn, gapSize: base[1] / dn });   /* the station: base / density */
      var ls = new T.LineSegments(geo, mat); ls.frustumCulled = false; ls.name = 'wires:' + kind; ls.userData.linkIndex = idx;
      if (cfg.style !== 'solid') geo.setAttribute('lineDistance', new T.BufferAttribute(new Float32Array(n * 2), 1).setUsage(T.DynamicDrawUsage));
      layers[kind] = { mesh: ls, pos: pos, idx: idx, dashed: cfg.style !== 'solid' }; });
    return { layers: layers, slot: slot, meshes: Object.keys(layers).map(function (k) { return layers[k].mesh; }),
      update: function (posOf) { Object.keys(layers).forEach(function (kind) { var L = layers[kind], p = L.pos, ld = L.dashed ? L.mesh.geometry.attributes.lineDistance.array : null;
        L.idx.forEach(function (li, k) { var a = vis[li] ? posOf(links[li].source) : null, b = vis[li] ? posOf(links[li].target) : null; if (!a || !b) { for (var q = 0; q < 6; q++) p[k * 6 + q] = 0; if (ld) { ld[k * 2] = 0; ld[k * 2 + 1] = 0; } return; }
          p[k * 6] = a[0]; p[k * 6 + 1] = a[1]; p[k * 6 + 2] = a[2]; p[k * 6 + 3] = b[0]; p[k * 6 + 4] = b[1]; p[k * 6 + 5] = b[2];
          if (ld) { ld[k * 2] = 0; ld[k * 2 + 1] = Math.sqrt((a[0] - b[0]) * (a[0] - b[0]) + (a[1] - b[1]) * (a[1] - b[1]) + (a[2] - b[2]) * (a[2] - b[2])); } });
        L.mesh.geometry.attributes.position.needsUpdate = true; if (ld) L.mesh.geometry.attributes.lineDistance.needsUpdate = true; }); },
      setVisible: function (li, on) { vis[li] = on ? 1 : 0; }, isVisible: function (li) { return !!vis[li]; },
      recolor: function (colorOf2) { Object.keys(layers).forEach(function (kind) { var L = layers[kind], col = L.mesh.geometry.attributes.color; L.idx.forEach(function (li, k) { for (var e = 0; e < 2; e++) { tmpC.set(colorOf2(links[li], e) || (feed.conn[kind] || feed.conn.calls).color); col.array[k * 6 + e * 3] = tmpC.r; col.array[k * 6 + e * 3 + 1] = tmpC.g; col.array[k * 6 + e * 3 + 2] = tmpC.b; } }); col.needsUpdate = true; }); },
      linkOf: function (mesh, segIndex) { var ix = mesh.userData.linkIndex; return ix ? ix[segIndex] : null; } };
  };
  TK.particleLayer = function (linkIdx, perLink, color, size) {   // directional particles: perLink dots per link travelling source→target
    var n = linkIdx.length * perLink, pos = new Float32Array(n * 3), geo = new T.BufferGeometry(); geo.setAttribute('position', new T.BufferAttribute(pos, 3).setUsage(T.DynamicDrawUsage));
    var pts = new T.Points(geo, new T.PointsMaterial({ color: color || '#e6edf3', size: size || 2.2, transparent: true, opacity: 0.9, sizeAttenuation: true, depthWrite: false })); pts.frustumCulled = false; pts.name = 'particles';
    return { mesh: pts, n: n, update: function (t, posOf, links) { var q = 0; for (var i = 0; i < linkIdx.length; i++) { var l = links[linkIdx[i]], a = posOf(l.source), b = posOf(l.target);
      for (var j = 0; j < perLink; j++, q++) { if (!a || !b) { pos[q * 3] = pos[q * 3 + 1] = pos[q * 3 + 2] = 0; continue; } var u = ((t * 0.08 + i * 0.37 + j / perLink) % 1); pos[q * 3] = a[0] + (b[0] - a[0]) * u; pos[q * 3 + 1] = a[1] + (b[1] - a[1]) * u; pos[q * 3 + 2] = a[2] + (b[2] - a[2]) * u; } }
      geo.attributes.position.needsUpdate = true; } };
  };

  /* ── hulls: the station's hull() — icosahedron directions seeded around every member, ConvexGeometry over the cloud ── */
  var DIRS = (function () { var g = new T.IcosahedronGeometry(1, 0), p = g.attributes.position, seen = {}, out = []; for (var i = 0; i < p.count; i++) { var x = +p.getX(i).toFixed(3), y = +p.getY(i).toFixed(3), z = +p.getZ(i).toFixed(3), k = x + ',' + y + ',' + z; if (seen[k]) continue; seen[k] = 1; out.push([x, y, z]); } return out; })();
  TK.hullGeometry = function (points, pad) { var Rr = 9 + (pad || 26), pts = []; points.forEach(function (p) { DIRS.forEach(function (d) { pts.push(new T.Vector3(p[0] + d[0] * Rr, p[1] + d[1] * Rr, p[2] + d[2] * Rr)); }); }); try { return new window.ConvexGeometry(pts); } catch (e) { return null; } };
  var SUBSHIFT = { endpoints: 0.04, api: -0.08, web: 0.10, frontend: 0.10, data: 0.0 };
  TK.subColor = function (entHex, sub) { return '#' + new T.Color(entHex).offsetHSL(SUBSHIFT[sub] || 0, 0.05, 0.06).getHexString(); };
  TK.hullMesh = function (color, op, wire) { return new T.Mesh(new T.BufferGeometry(), new T.MeshLambertMaterial({ color: color, emissive: color, emissiveIntensity: 0.10, transparent: true, opacity: op, side: T.DoubleSide, depthWrite: false, wireframe: !!wire })); };
  TK.labelSprite = function (txt, size, col) { var cv = document.createElement('canvas'), c0 = cv.getContext('2d'), fnt = '600 ' + (size || 26) + 'px Menlo,Consolas,ui-monospace,monospace'; c0.font = fnt; var tw = Math.ceil(c0.measureText(txt).width) + 16; cv.width = Math.max(256, tw); cv.height = 64; var c = cv.getContext('2d'); c.font = fnt; c.fillStyle = col || '#cdd6ea'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(txt, cv.width / 2, 32);
    var s = new T.Sprite(new T.SpriteMaterial({ map: new T.CanvasTexture(cv), transparent: true, depthWrite: false })); s.scale.set(34 * (cv.width / 256), 8.5, 1); return s; };

  /* ── camera rig ────────────────────────────────────────────────────────────────────────────────────────────── */
  TK.orbit = function (cam, dom, opts) { opts = opts || {}; var down = false, px = 0, py = 0, th = opts.theta || 0.4, ph = opts.phi || 0.28, r = opts.r || 900, tgt = new T.Vector3(opts.tx || 0, opts.ty || 0, opts.tz || 0);
    function apply() { cam.position.set(tgt.x + r * Math.cos(ph) * Math.sin(th), tgt.y + r * Math.sin(ph), tgt.z + r * Math.cos(ph) * Math.cos(th)); cam.lookAt(tgt); }
    apply();
    dom.addEventListener('pointerdown', function (e) { down = true; px = e.clientX; py = e.clientY; });
    addEventListener('pointerup', function () { down = false; });
    addEventListener('pointermove', function (e) { if (!down) return; th -= (e.clientX - px) * 0.005; ph = Math.max(-1.45, Math.min(1.45, ph + (e.clientY - py) * 0.005)); px = e.clientX; py = e.clientY; apply(); });
    dom.addEventListener('wheel', function (e) { e.preventDefault(); r = Math.max(40, Math.min(12000, r * (1 + Math.sign(e.deltaY) * 0.12))); apply(); }, { passive: false });
    return { fit: function (rad) { r = rad; apply(); }, target: tgt, apply: apply, get r() { return r; } };
  };
  /* ── colour-id picking over instanced meshes (nodes) and line segments (links): one 1×1 readback, O(1) in node count ── */
  var PICKGEO = {};
  TK.picker = function (renderer, cam) {
    var scene = new T.Scene(), target = new T.WebGLRenderTarget(1, 1, { colorSpace: T.LinearSRGBColorSpace }), pixel = new Uint8Array(4), regs = [], W = 0, H = 0;
    function idColor(i) { var v = (i + 1) & 0xffffff; return new T.Color().setRGB(((v >> 16) & 255) / 255, ((v >> 8) & 255) / 255, (v & 255) / 255, T.LinearSRGBColorSpace); }   /* exact bytes: linear working space in, linear target out, no colour-space conversion (new Color(<float>) is a HEX-INT constructor — it floors to black) */
    return { add: function (mesh, base, geoOverride) {   // an InstancedMesh (ids base..base+count) or LineSegments (ids per segment, drawn fat via a thin quad? no — lines pick with their own width only)
        var clone; if (mesh.isInstancedMesh) { var pg = geoOverride; if (!pg) { var g0 = mesh.geometry; if (!g0.boundingSphere) g0.computeBoundingSphere(); var rr = +(g0.boundingSphere.radius).toFixed(2); pg = PICKGEO[rr] || (PICKGEO[rr] = new T.IcosahedronGeometry(rr, 0)); }   /* a 20-tri icosahedron at the FORM's bounding radius stands in for every glyph in the pick pass — the same footprint, a fraction of the vertex work */
          clone = new T.InstancedMesh(pg, new T.MeshBasicMaterial({}), mesh.count); clone.frustumCulled = false; for (var i = 0; i < mesh.count; i++) clone.setColorAt(i, idColor(base + i)); clone.instanceColor.needsUpdate = true; clone.instanceMatrix = mesh.instanceMatrix; }
        else if (mesh.isLineSegments) { var n = mesh.geometry.attributes.position.count / 2, col = new Float32Array(n * 6); for (var k = 0; k < n; k++) { var c = idColor(base + k); for (var e = 0; e < 2; e++) { col[k * 6 + e * 3] = c.r; col[k * 6 + e * 3 + 1] = c.g; col[k * 6 + e * 3 + 2] = c.b; } } var g = new T.BufferGeometry(); g.setAttribute('position', mesh.geometry.attributes.position); g.setAttribute('color', new T.BufferAttribute(col, 3)); clone = new T.LineSegments(g, new T.LineBasicMaterial({ vertexColors: true })); clone.frustumCulled = false; }
        else return; scene.add(clone); regs.push({ src: mesh, clone: clone, base: base, count: mesh.isInstancedMesh ? mesh.count : mesh.geometry.attributes.position.count / 2 }); },
      pick: function (x, y, layer) {   /* layer: 'nodes' (instanced clones only) · 'links' (line clones only) · undefined = all; a wire crossing a node's centre must not steal the node pick */
        var sz = renderer.getSize(new T.Vector2()); W = sz.x; H = sz.y; regs.forEach(function (r) { if (r.src.isInstancedMesh) { r.clone.instanceMatrix.needsUpdate = true; } r.clone.visible = r.src.visible && (!layer || (layer === 'nodes' ? !!r.src.isInstancedMesh : !!r.src.isLineSegments)); });
        var pc = cam.clone(); pc.setViewOffset(W, H, x * renderer.getPixelRatio() | 0, y * renderer.getPixelRatio() | 0, 1, 1); pc.updateProjectionMatrix();
        var oldT = renderer.getRenderTarget(), oldC = renderer.getClearColor(new T.Color()), oldA = renderer.getClearAlpha(); renderer.setRenderTarget(target); renderer.setClearColor(0x000000, 1); renderer.clear(); renderer.render(scene, pc); renderer.readRenderTargetPixels(target, 0, 0, 1, 1, pixel); renderer.setRenderTarget(oldT); renderer.setClearColor(oldC, oldA);
        var id = ((pixel[0] << 16) | (pixel[1] << 8) | pixel[2]); if (!id) return null; id -= 1; for (var i = 0; i < regs.length; i++) { var r = regs[i]; if (id >= r.base && id < r.base + r.count) return { mesh: r.src, index: id - r.base }; } return null; },
      scene: scene };
  };
  TK.screenOf = function (cam, renderer, x, y, z) { var v = new T.Vector3(x, y, z).project(cam); if (v.z > 1) return null; var sz = renderer.getSize(new T.Vector2()); return { x: (v.x + 1) / 2 * sz.x, y: (1 - v.y) / 2 * sz.y }; };
})();
