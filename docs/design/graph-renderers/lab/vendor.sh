#!/usr/bin/env bash
# vendor.sh — the ONE vendoring recipe for the lab. Exact pins. UMD/IIFE only (the pages open from file:// with no network).
#   ./vendor.sh                 fetch every bundle (cache first, then jsDelivr) → vendor/ + vendor/MANIFEST.json
#   ./vendor.sh --cache <dir>   a directory of previously downloaded bundles to copy from before touching the network
#   ./vendor.sh --only babylon  one entry
# REFUSES @cosmograph/cosmos (CC-BY-NC-4.0 since 3.4.0 — same version string and API as the MIT @cosmos.gl/graph; the
# licence is the only difference and no test would catch it). The cosmos bundle is grepped after copy.
# three.js is NOT vendored: r185 ships no UMD; every 3D page reads window.THREE from the station's own esbuild IIFE
# at templates/center/shell/assets/3d-bundle.js (1,637,037 B) — the bundle the station already ships.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; V="$HERE/vendor"; mkdir -p "$V"
CACHE=""; ONLY=""
while [ $# -gt 0 ]; do case "$1" in --cache) CACHE="$2"; shift 2;; --only) ONLY="$2"; shift 2;; *) echo "unknown arg $1"; exit 2;; esac; done
# name | version | licence | lab file | jsDelivr path | cache filename(s) to try (space-separated)
PINS='
d3-dispatch|3.0.1|ISC|d3-dispatch.min.js|d3-dispatch@3.0.1/dist/d3-dispatch.min.js|d3-dispatch.min.js
d3-timer|3.0.1|ISC|d3-timer.min.js|d3-timer@3.0.1/dist/d3-timer.min.js|d3-timer.min.js
d3-binarytree|1.0.2|ISC|d3-binarytree.min.js|d3-binarytree@1.0.2/dist/d3-binarytree.min.js|d3-binarytree.min.js
d3-quadtree|3.0.1|ISC|d3-quadtree.min.js|d3-quadtree@3.0.1/dist/d3-quadtree.min.js|d3-quadtree.min.js
d3-octree|1.1.0|ISC|d3-octree.min.js|d3-octree@1.1.0/dist/d3-octree.min.js|d3-octree.min.js
d3-force-3d|3.0.6|MIT|d3-force-3d.min.js|d3-force-3d@3.0.6/dist/d3-force-3d.min.js|d3-force-3d.min.js
ngraph.graph|20.0.1|BSD-3-Clause|ngraph.graph.min.js|ngraph.graph@20.0.1/dist/ngraph.graph.min.js|ngraph.graph-20.0.1.min.js
ngraph.forcelayout|3.3.1|BSD-3-Clause|ngraph.forcelayout.min.js|ngraph.forcelayout@3.3.1/dist/ngraph.forcelayout.min.js|ngraph.forcelayout-3.3.1.min.js
sigma|3.0.3|MIT|sigma.min.js|sigma@3.0.3/dist/sigma.min.js|sigma-3.0.3.min.js
graphology|0.26.0|MIT|graphology.umd.min.js|graphology@0.26.0/dist/graphology.umd.min.js|graphology-0.26.0.umd.min.js
graphology-library|0.8.0|MIT|graphology-library.min.js|graphology-library@0.8.0/dist/graphology-library.min.js|graphology-library-0.8.0.min.js
cytoscape|3.34.2|MIT|cytoscape.min.js|cytoscape@3.34.2/dist/cytoscape.min.js|cytoscape-3.34.2.min.js
layout-base|2.0.1|MIT|layout-base.js|layout-base@2.0.1/layout-base.js|layout-base-2.0.1.js
cose-base|2.2.0|MIT|cose-base.js|cose-base@2.2.0/cose-base.js|cose-base-2.2.0.js
cytoscape-fcose|2.2.0|MIT|cytoscape-fcose.js|cytoscape-fcose@2.2.0/cytoscape-fcose.js|cytoscape-fcose-2.2.0.js
@cosmos.gl/graph|3.4.1|MIT|cosmos-graph.umd.min.js|@cosmos.gl/graph@3.4.1/dist/index.umd.js|cosmosgl-graph-3.4.1.umd.min.js
pixi.js|8.20.1|MIT|pixi.min.js|pixi.js@8.20.1/dist/pixi.min.js|pixi-8.20.1.min.js
babylonjs|9.25.0|Apache-2.0|babylon.min.js|babylonjs@9.25.0/babylon.js|babylon.min.js
'
sha(){ sha256sum "$1" | cut -c1-16; }
rows=()
while IFS='|' read -r name ver lic file jsd cachefiles; do
  [ -z "$name" ] && continue
  [ -n "$ONLY" ] && [ "$name" != "$ONLY" ] && [ "$file" != "$ONLY" ] && continue
  case "$name$jsd$cachefiles" in *cosmograph*) echo "REFUSED: $name names @cosmograph/cosmos (CC-BY-NC)"; exit 3;; esac
  dst="$V/$file"; src=""
  if [ -s "$dst" ]; then src="present"
  else
    if [ -n "$CACHE" ]; then for cf in $cachefiles; do hit="$(find "$CACHE" -type f -name "$cf" 2>/dev/null | head -1)"; if [ -n "$hit" ]; then cp "$hit" "$dst"; src="cache:${hit#$CACHE/}"; break; fi; done; fi
    if [ -z "$src" ]; then url="https://cdn.jsdelivr.net/npm/$jsd"; echo "fetch  $url"; curl -fsSL -o "$dst" "$url" || { echo "FAILED: $url (pin or path wrong — fix the PINS row, never guess a different package)"; rm -f "$dst"; exit 4; }; src="$url"; fi
  fi
  if [ "$name" = "@cosmos.gl/graph" ]; then
    if grep -q "cosmograph/cosmos\|CC-BY-NC" "$dst"; then echo "REFUSED: the cosmos bundle carries a non-commercial marker"; rm -f "$dst"; exit 3; fi
    grep -q "MIT" "$dst" || { echo "REFUSED: the cosmos bundle carries no MIT banner"; rm -f "$dst"; exit 3; }
  fi
  printf '%-22s %-8s %-13s %10s B  %s  %s\n' "$name" "$ver" "$lic" "$(stat -c %s "$dst")" "$(sha "$dst")" "$src"
  rows+=("{\"name\":\"$name\",\"version\":\"$ver\",\"license\":\"$lic\",\"file\":\"$file\",\"bytes\":$(stat -c %s "$dst"),\"sha256_16\":\"$(sha "$dst")\",\"jsdelivr\":\"https://cdn.jsdelivr.net/npm/$jsd\",\"source\":\"$src\"}")
done <<< "$PINS"
if [ -z "$ONLY" ]; then { echo "["; (IFS=$'\n'; printf '%s\n' "${rows[@]}" | paste -sd, -); echo "]"; } > "$V/MANIFEST.json"; else echo "(--only: MANIFEST.json left as is)"; fi
# the six d3-force-3d UMDs as ONE JS string: a Blob worker evaluates it instead of importScripts() — Windows Chrome over
# file://wsl.localhost/ refuses a worker's importScripts of a file:// sibling ('file:' URLs are unique origins), Linux Chrome allows it
if [ -s "$V/d3-force-3d.min.js" ]; then python3 - "$V" <<'PY2'
import json, sys, os
V = sys.argv[1]; parts = ['d3-dispatch', 'd3-timer', 'd3-binarytree', 'd3-quadtree', 'd3-octree', 'd3-force-3d']
src = ''.join(open(os.path.join(V, p + '.min.js'), encoding='utf-8').read() + '\n' for p in parts)
with open(os.path.join(V, 'd3-force-3d.worker.js'), 'w', encoding='utf-8') as f:
    f.write('/* GENERATED by vendor.sh — the six d3-force-3d UMDs as one string; a Blob worker evaluates it (no importScripts, works on file://wsl.localhost) */\n')
    f.write('window.__D3_WORKER_SRC=' + json.dumps(src) + ';\n')
print('d3-force-3d.worker.js:', os.path.getsize(os.path.join(V, 'd3-force-3d.worker.js')), 'bytes (generated)')
PY2
fi
[ -z "$ONLY" ] && python3 -c "import json;d=json.load(open('$V/MANIFEST.json'));print('MANIFEST.json:',len(d),'bundles,',sum(x['bytes'] for x in d),'bytes')"
echo "three r185: reused from ../../../../templates/center/shell/assets/3d-bundle.js ($(stat -c %s "$HERE/../../../../templates/center/shell/assets/3d-bundle.js") B, not vendored)"
