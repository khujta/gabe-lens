/* feed-loader.js — picks the FIXTURE from the URL and writes its <script> tags at parse time (file:// has no fetch).
     ?feed=example (default)  → the committed example estate under templates/center/shell/example/codebase-graph-station/
     ?feed=onyx               → fixtures/onyx/ (a gitignored COPY made by fixtures/fetch-onyx.sh — ruling D3)
     ?feed=<name>             → fixtures/<name>/c4-graph.js (+ levels.js)
     ?fn=1                    → also load levels.js so the adapter can add the function layer (2,380 nodes on onyx)
   Loaded FIRST in every lab page. Exposes window.GABE_FIXTURE for the adapter and the probe. */
(function () {
  function qs(k, d) { var m = new RegExp('[?&]' + k + '=([^&]*)').exec(location.search); return m ? decodeURIComponent(m[1]) : d; }
  var feed = qs('feed', 'example'), fn = qs('fn', '0') === '1';
  var EX = '../../../../templates/center/shell/example/codebase-graph-station/';
  var base = feed === 'example' ? EX : ('./fixtures/' + feed.replace(/[^a-z0-9_-]/gi, '') + '/');
  window.GABE_FIXTURE = { name: feed, c4: base + 'c4-graph.js', levels: fn ? base + 'levels.js' : null, fn: fn };
  document.write('<script src="' + window.GABE_FIXTURE.c4 + '"><\/script>');
  if (fn) document.write('<script src="' + window.GABE_FIXTURE.levels + '"><\/script>');
})();
