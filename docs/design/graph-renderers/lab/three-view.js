/* three-view.js — the SHARED raw-three view the 3D pages draw with (lab-01 raw · lab-04 cosmos→three). One renderer, every layer instanced
   (three-kit.js), hulls per entity + sub, colour-id picking of nodes AND link segments, the cards, an optional walk mode and the LABG probe
   surface. A page supplies POSITIONS (a worker sim, a GPU sim, a bake) and calls V.sync() when they change; the view never lays out.
     var V = TV.create(F, { labels:true, particles:true, walk:false });
     V.sync(t)            rewrite every instance matrix + wire + badge + label from n.x/n.y/n.z (call on a position change)
     V.hulls.build() / V.hulls.update()
     V.setSettled(ms)     flips LABG.settled + records settle_ms (once)
     V.run(onFrame)       the rAF loop (onFrame(now, dt) before the render — return true when positions changed this frame)
     V.surface({...})     merges extra fields into LABG (ticks, stats extras)                                                   */
(function () {
  'use strict';
  var T = window.THREE, TK = window.TK;
  window.TV = { create: function (F, opts) {
    opts = opts || {};
    var LABELS = opts.labels !== false, PARTICLES = opts.particles !== false, WALK = !!opts.walk;
    var nodes = F.nodes, links = F.links, byId = F.byId, N = nodes.length, TIER = F.tier;
    var visible = function (n) { return n.tier <= TIER; };
    var IS = 10, BR = IS * 0.62, BUB = '#aab4c6';
    var W = innerWidth, H = innerHeight, renderer = new T.WebGLRenderer({ antialias: N < 6000, powerPreference: 'high-performance', preserveDrawingBuffer: true });
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2)); renderer.setSize(W, H); renderer.setClearColor(0x0b0e13, 1); (opts.container || document.getElementById('g')).appendChild(renderer.domElement);
    var scene = new T.Scene(), cam = new T.PerspectiveCamera(55, W / H, 1, 20000); scene.add(new T.AmbientLight(0xffffff, 1.5)); var dl = new T.DirectionalLight(0xffffff, 1.2); dl.position.set(300, 400, 600); scene.add(dl);
    var rig = TK.orbit(cam, renderer.domElement, { r: 820, theta: 0.19, phi: 0.1 });
    function slotsOf(n) { var a = null, b = null;
      if (n.kind === 'endpoint' && n.m) a = { family: 'method', value: n.m }; else if (n.kind === 'function' && n.det && n.det.role) a = { family: 'role', value: n.det.role };
      else if (n.kind === 'component' && n.feClass && n.feClass !== 'view') a = { family: 'feclass', value: n.feClass }; else if (n.kind === 'module' && n.mclass) a = { family: 'mclass', value: n.mclass };
      else if (n.kind === 'hook' && n.hrole) a = { family: 'hrole', value: n.hrole }; else if (n.kind === 'provider' && n.pclass) a = { family: 'pclass', value: n.pclass };
      if (n.kind === 'endpoint' && n.stream) b = { family: 'delivery', value: 'stream' }; return [a, b]; }
    function wireColor(l, e) { var n = byId[e ? l.target : l.source], cfg = F.conn[l.kind] || F.conn.calls, band = F.bandOf(l); if (band) return band.color; if (cfg.gmode === 'type' || cfg.gmode === 'type-ent') { if (n && n.kind === 'endpoint' && n.m) return F.method[n.m]; } return (n && F.entColor[n.ent]) || cfg.color; }
    var glyph = TK.glyphLayers(nodes, F.colorOf, function (n) { return (F.kinds[n.kind] || {}).form || 'sphere'; }), bub = TK.sphereLayer(N, BUB, 0.10, BR, 12), badges = TK.badgeLayer(nodes, slotsOf);
    var labels = LABELS ? TK.labelLayer(nodes, function (n) { return n.label; }, 4000) : { mesh: null, set: function () {}, hide: function () {}, flush: function () {}, slotOf: {}, pick: [] };
    var wires = TK.wireLayers(links, F, wireColor), cross = []; links.forEach(function (l, i) { if (l.cross) cross.push(i); });
    var parts = PARTICLES ? TK.particleLayer(cross, 1, '#e6edf3', 2.2) : null;
    [].concat(glyph.meshes, [bub.mesh], badges.mesh ? [badges.mesh] : [], labels.mesh ? [labels.mesh] : [], wires.meshes, parts ? [parts.mesh] : []).forEach(function (m) { scene.add(m); });
    if (LABELS && labels.pick.length < N) LAB.note('labels_capped', labels.pick.length + ' of ' + N);
    var hullGroup = new T.Group(), HULLS = []; scene.add(hullGroup);
    var hulls = { build: function () { while (hullGroup.children.length) { var h = hullGroup.children.pop(); if (h.geometry) h.geometry.dispose(); } HULLS = [];
        var byEnt = {}, bySub = {}; nodes.forEach(function (n) { if (!visible(n)) return; (byEnt[n.ent] = byEnt[n.ent] || []).push(n); var k = n.ent + '|' + n.sub; (bySub[k] = bySub[k] || []).push(n); });
        Object.keys(byEnt).forEach(function (e) { var m = TK.hullMesh(F.entColor[e], 0.08), lbl = TK.labelSprite(F.entKind[e] === 'entity' ? e : ('fe · ' + e.replace(/^fe·/, '')), 34, F.entColor[e]); hullGroup.add(m); hullGroup.add(lbl); HULLS.push({ mesh: m, lbl: lbl, members: byEnt[e], pad: 26 }); });
        Object.keys(bySub).forEach(function (k) { if (bySub[k].length < 2) return; var e = k.split('|')[0], m = TK.hullMesh(F.entColor[e], 0.12); hullGroup.add(m); HULLS.push({ mesh: m, members: bySub[k], pad: 10 }); }); },
      update: function () { HULLS.forEach(function (h) { var pts = h.members.map(function (n) { return [n.x, n.y, n.z]; }); var g = TK.hullGeometry(pts, h.pad); if (g) { h.mesh.geometry.dispose(); h.mesh.geometry = g; h.mesh.visible = true; } else h.mesh.visible = false;
        if (h.lbl) { var cx = 0, cz = 0, top = -1e9; pts.forEach(function (p) { cx += p[0]; cz += p[2]; if (p[1] > top) top = p[1]; }); h.lbl.position.set(cx / pts.length, top + 26, cz / pts.length); } }); } };
    var posOf = function (id) { var n = byId[id]; return (n && visible(n)) ? [n.x, n.y, n.z] : null; };
    function sync(t) {
      for (var i = 0; i < N; i++) { var n = nodes[i], on = visible(n); glyph.setVisible(i, on); if (on) { glyph.setPos(i, n.x, n.y, n.z); bub.set(i, n.x, n.y, n.z); var ls = labels.slotOf[i]; if (ls != null) labels.set(ls, n.x, n.y - (BR + 4.5), n.z); } else { bub.hide(i); var ls2 = labels.slotOf[i]; if (ls2 != null) labels.hide(ls2); } }
      badges.items.forEach(function (it, q) { var n = nodes[it.i]; if (visible(n)) badges.set(q, n.x + BR * 0.9, n.y + (it.slot ? BR * 0.9 : -BR * 0.9), n.z + 3); else badges.hide(q); });
      glyph.flush(); bub.flush(); badges.flush(); labels.flush(); wires.update(posOf); if (parts) parts.update(t || 0, posOf, links); }
    function syncVisibility() { links.forEach(function (l, li) { var a = byId[l.source], b = byId[l.target]; wires.setVisible(li, !!(a && b && visible(a) && visible(b))); }); }
    /* picking: nodes with the wires hidden, then the wires alone */
    var picker = TK.picker(renderer, cam), base = 0; glyph.meshes.forEach(function (m) { picker.add(m, base); base += m.count; }); wires.meshes.forEach(function (m) { picker.add(m, base); base += m.geometry.attributes.position.count / 2; });
    function pickNode(x, y) { var r = picker.pick(x, y, 'nodes'); if (!r || !r.mesh.isInstancedMesh) return null; var ni = glyph.nodeOf(r.mesh, r.index); return ni == null ? null : nodes[ni].id; }
    function pickLink(x, y) { var r = picker.pick(x, y, 'links'); if (!r || !r.mesh.isLineSegments) return null; return wires.linkOf(r.mesh, r.index); }
    var tip = document.getElementById('tip'), card = document.getElementById('card'), lastPick = 0;
    function esc(s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;'); }
    function showCard(n) { if (!card) return; card.style.display = 'block'; card.innerHTML = '<b>' + esc(n.label) + '</b><div class="row"><span>kind</span><span>' + n.kind + (n.m ? ' · ' + n.m : '') + (n.stream ? ' · stream' : '') + '</span></div><div class="row"><span>entity</span><span>' + esc(n.ent) + (n.ent !== n.entClaim ? ' (claim ' + esc(n.entClaim) + ')' : '') + '</span></div><div class="row"><span>tier</span><span>T' + n.tier + ' · degree ' + n.deg + (n.hub ? ' · hub' : '') + '</span></div>' + (n.det && n.det.file ? '<div class="row"><span>file</span><span>' + esc(n.det.file) + '</span></div>' : '') + (n.behind && n.behind.fns ? '<div class="row"><span>behind</span><span>' + n.behind.fns + ' fns · depth ' + n.behind.depth + '</span></div>' : ''); }
    function showLink(l) { if (!card) return; card.style.display = 'block'; card.innerHTML = '<b>' + esc(byId[l.source].label) + ' → ' + esc(byId[l.target].label) + '</b><div class="row"><span>wire</span><span>' + l.rel + ' (' + l.kind + ')' + (l.cross ? ' · cross-entity' : '') + (l.proven ? ' · structural' : ' · inferred') + '</span></div>'; }
    if (tip) { addEventListener('pointermove', function (e) { if (WALK) return; tip.style.left = (e.clientX + 14) + 'px'; tip.style.top = (e.clientY + 14) + 'px'; var t = performance.now(); if (t - lastPick < 60) return; lastPick = t; var id = pickNode(e.clientX, e.clientY); if (!id) { tip.style.display = 'none'; return; } var n = byId[id]; tip.style.display = 'block'; tip.innerHTML = '<b>' + esc(n.label) + '</b><i>' + n.kind + ' · ' + esc(n.ent) + (n.m ? ' · ' + n.m : '') + '</i>'; }); }
    addEventListener('click', function (e) { if (WALK) return; var id = pickNode(e.clientX, e.clientY); if (id) showCard(byId[id]); else { var li = pickLink(e.clientX, e.clientY); if (li != null) showLink(links[li]); } });
    /* walk mode: pointer lock + WASD/QE, a capsule against the buildings (uniform grid) */
    var walk = null;
    if (WALK) { var keys = {}, yaw = 0, pitch = 0, pos = new T.Vector3(F.anchors.EX[F.ents[0]] || 0, 0, 120), grid = null, CELL = 40;
      var rebuildGrid = function () { grid = Object.create(null); for (var i = 0; i < N; i++) { var n = nodes[i]; if (!visible(n)) continue; var k = ((n.x / CELL) | 0) + ',' + ((n.y / CELL) | 0) + ',' + ((n.z / CELL) | 0); (grid[k] = grid[k] || []).push(i); } };
      var collide = function (p) { var cx = (p.x / CELL) | 0, cy = (p.y / CELL) | 0, cz = (p.z / CELL) | 0, RR = BR + 3; for (var a = -1; a <= 1; a++) for (var b = -1; b <= 1; b++) for (var c = -1; c <= 1; c++) { var cell = grid[(cx + a) + ',' + (cy + b) + ',' + (cz + c)]; if (!cell) continue; for (var q = 0; q < cell.length; q++) { var n = nodes[cell[q]], dx = p.x - n.x, dy = p.y - n.y, dz = p.z - n.z, d = Math.sqrt(dx * dx + dy * dy + dz * dz); if (d < RR && d > 1e-6) { var push = (RR - d) / d; p.x += dx * push; p.y += dy * push; p.z += dz * push; } } } };
      renderer.domElement.addEventListener('click', function () { renderer.domElement.requestPointerLock(); });
      addEventListener('mousemove', function (e) { if (document.pointerLockElement !== renderer.domElement) return; yaw -= e.movementX * 0.0025; pitch = Math.max(-1.5, Math.min(1.5, pitch - e.movementY * 0.0025)); });
      addEventListener('keydown', function (e) { keys[e.code] = true; }); addEventListener('keyup', function (e) { keys[e.code] = false; });
      walk = { step: function (dt) { if (!grid) rebuildGrid(); var sp = (keys.ShiftLeft ? 90 : 45) * dt, fwd = new T.Vector3(-Math.sin(yaw), 0, -Math.cos(yaw)), right = new T.Vector3(Math.cos(yaw), 0, -Math.sin(yaw));
        if (keys.KeyW) pos.addScaledVector(fwd, sp); if (keys.KeyS) pos.addScaledVector(fwd, -sp); if (keys.KeyD) pos.addScaledVector(right, sp); if (keys.KeyA) pos.addScaledVector(right, -sp); if (keys.KeyE) pos.y += sp; if (keys.KeyQ) pos.y -= sp;
        collide(pos); cam.position.copy(pos); cam.rotation.set(0, 0, 0); cam.rotateY(yaw); cam.rotateX(pitch); }, rebuild: rebuildGrid, pos: pos };
      LAB.note('walk', 'pointer lock + WASD/QE, capsule r=' + (BR + 3).toFixed(1) + ' vs buildings (uniform grid ' + CELL + ')'); }
    addEventListener('resize', function () { W = innerWidth; H = innerHeight; cam.aspect = W / H; cam.updateProjectionMatrix(); renderer.setSize(W, H); });
    /* the probe surface */
    var settled = false;
    var G = LAB.graph({ nodes: nodes, links: links, byId: byId, settled: false,
      setTier: function (t) { TIER = Math.max(0, Math.min(3, t | 0)); syncVisibility(); sync(0); hulls.build(); hulls.update(); if (walk) walk.rebuild(); return G.visible(); },
      visible: function () { var c = 0; for (var i = 0; i < N; i++) if (visible(nodes[i])) c++; return c; },
      visibleIds: function () { return nodes.filter(visible).map(function (n) { return n.id; }); },
      positions: function () { var o = {}; for (var i = 0; i < N; i++) { var n = nodes[i]; if (visible(n)) o[n.id] = [n.x, n.y, n.z]; } return o; },
      screenOf: function (id) { var n = byId[id]; return n ? TK.screenOf(cam, renderer, n.x, n.y, n.z) : null; },
      pick: pickNode, pickLink: pickLink,
      stats: function () { var i = renderer.info; return { calls: i.render.calls, triangles: i.render.triangles, geometries: i.memory.geometries, textures: i.memory.textures, glyphLayers: glyph.meshes.length, wireLayers: wires.meshes.length }; } });
    var frames = 0, fpsm = LAB.fps, lastFrame = performance.now();
    var V = { renderer: renderer, cam: cam, scene: scene, rig: rig, G: G, sync: sync, syncVisibility: syncVisibility, hulls: hulls, walk: walk, tier: function () { return TIER; }, visible: visible, BR: BR,
      setSettled: function () { if (settled) return; settled = true; G.settled = true; LAB.mark('settle_ms'); LAB.set('layout_ms', window.__LAB.settle_ms); hulls.update(); sync(0); },
      isSettled: function () { return settled; },
      surface: function (extra) { Object.assign(G, extra || {}); },
      run: function (onFrame) { (function loop() { requestAnimationFrame(loop); var now = performance.now(), dt = Math.min(0.05, (now - lastFrame) / 1000); lastFrame = now;
        var moved = onFrame ? onFrame(now, dt, frames) : false;
        if (moved || !settled) sync(now * 0.001); else if (parts) parts.update(now * 0.001, posOf, links);
        if ((moved || !settled) && frames % 3 === 0) hulls.update(); if (walk) { if (frames % 30 === 0) walk.rebuild(); walk.step(dt); }
        renderer.render(scene, cam); frames++; fpsm(); if (frames === 2) LAB.mark('first_frame_ms');
        if (frames % 30 === 0) { var i2 = renderer.info; LAB.set('draws', i2.render.calls); LAB.set('tris', i2.render.triangles); LAB.set('geos', i2.memory.geometries); LAB.set('texs', i2.memory.textures); if (V.hud) V.hud(i2); } })(); } };
    syncVisibility(); hulls.build();
    return V;
  } };
})();
