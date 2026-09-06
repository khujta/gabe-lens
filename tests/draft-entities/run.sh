#!/usr/bin/env bash
# draft-entities.py fixture battery — the ENTITY-MODEL DRAFTER's executable contract (entity models Phase 4,
# docs/design/entity-models/plan.md C12, 2026-09-06). Proves, hermetically on a synthetic center (a c4-graph.json
# carrying the emitter's `models` block, in a temp dir):
#   * FIRE          — every declared verdict is projected with its why + suggested edit; every CANDIDATE arrives NAMED
#                     (the emitter's name, `named_by` domain|table, a suggested slug, `draft_name()`'s action phrase).
#   * SILENT        — an all-FEATURE, no-candidate block → a VALID EMPTY draft (candidates []), so a stale one never lingers.
#   * HONEST-EMPTY  — no center config · no c4 · unreadable c4 · no `models` block → the reason printed, NOTHING written, exit 0.
#   * DETERMINISM   — a second run on an unchanged input writes nothing ("unchanged") and is byte-identical; the c4 head is the only stamp.
#   * ABSTAIN       — a witnessless atom lands in `abstained`, never in `candidates`; `coverage.witnessed` is present and right.
#   * PROJECTION    — the draft's declared verdicts EQUAL the block's proposed roster (nothing derived locally) — the mutation
#                     "derive a verdict here" reddens it; flipping the fixture's anchor table changes the fallback name.
#   * --min · --model derived · R10 (no "orphan").
# Exit 0 = all pass.
set -u
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
D="$REPO/skills/gabe-cc-update/scripts/draft-entities.py"
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
pass=0; fail=0
ok(){ pass=$((pass+1)); }
bad(){ fail=$((fail+1)); echo "  FAIL: $1"; }

mkcenter() { local r="$T/$1"; mkdir -p "$r/docs/site/center"; printf '{}' > "$r/docs/site/center/center.config.json"; echo "$r"; }
# the emitter's block: two declared verdicts (cooking SPLIT · pantry MERGE) + one FEATURE; two candidates — one named by its URL
# domain (orph, 2 endpoints), one by its table (dish history events, 3 endpoints); two abstained atoms; coverage 78/80.
c4() { cat <<'JSON'
{"head":"abc1234","l2":{},"stats":{"models":{"present":true,"views":["claim","seeded","derived","proposed"]}},
 "models":{"present":true,"head":"abc1234","default":"claim","rule":"claim = the registry · the other three are views",
  "views":{"claim":{"present":true},"seeded":{"present":true,"moved":9,"held":4,"abstained":7},
           "derived":{"present":true,"features":25,"aspects":3,"layers":1,"atoms":80,"anchored":78,"abstained":2,"purity":0.897},
           "proposed":{"present":true,"verdicts":{"FEATURE":1,"SPLIT":1,"MERGE":1,"ASPECT":0,"LAYER":0},"candidates":2}},
  "rosters":{
   "derived":[{"id":"d:cooking_sessions","name":"cooking/sessions","kind":"feature","named_by":"domain","anchor_table":"cooking_sessions","anchor_by":"write","endpoints":5,"screens":2,"purity":1.0,"claim_mix":{"cooking":5},"members":["endpoint:GET /cooking/sessions"]},
              {"id":"a:auth","name":"auth","kind":"aspect","detector":"gate-fan-in","domains":9,"members":["a/deps.py#auth"],"drawn":true}],
   "proposed":[{"slug":"cooking","verdict":"SPLIT","why":"2 clean feature(s) inside — cooking/sessions · cooking/photos","evidence":{"atoms":9},"suggested_edit":{"split":[{"slug":"cooking-sessions","anchor":"cooking_sessions"},{"slug":"cooking-photos","anchor":"cooking_photos"}]}},
               {"slug":"pantry","verdict":"MERGE","why":"its atoms sit in pantry items, whose majority is recipe — survivor recipe (more atoms in the feature)","evidence":{"survivor":"recipe"},"suggested_edit":{"merge_into":"recipe"}},
               {"slug":"recipe","verdict":"FEATURE","why":"majority of recipe filter modes and sole-owns 3 URL domain(s)","evidence":{}}],
   "candidates":[{"id":"d:t7","name":"orph","kind":"feature","named_by":"domain","anchor_table":"t7","endpoints":2,"screens":0,"spans_entities":[],"suggested_slug":"orph","members":["endpoint:GET /orph","endpoint:POST /orph"]},
                 {"id":"d:dish_history_events","name":"dish history events","kind":"feature","named_by":"table","anchor_table":"dish_history_events","endpoints":3,"screens":1,"spans_entities":["cooking","progression","recipe"],"suggested_slug":"dish-history-events","members":["endpoint:GET /dishes/history","endpoint:GET /dishes/history/{id}","endpoint:DELETE /dishes/history/{id}","fe:src/features/history/useHistory.ts#useHistory"]}]},
  "homes":{"seeded":{},"derived":{},"proposed":{}},"held":{"seeded":[],"derived":[]},
  "abstain":{"seeded":[],"derived":["endpoint:GET /z","endpoint:GET /health"],"proposed":[]},
  "stats":{"caps":{"depth_cap":3},"truncated":[]}}}
JSON
}

# ── FIRE ──
r=$(mkcenter fire); c4 > "$r/docs/site/center/c4-graph.json"
out=$(python3 "$D" "$r" --json); rc=$?; echo "$out" > "$T/fire.json"
[ "$rc" = 0 ] && ok || bad "FIRE: exit 0 ($rc)"
python3 - "$T/fire.json" "$r/docs/site/center/entities.draft.json" <<'PY' && ok || bad "FIRE: verdicts projected with why + edit; candidates NAMED (named_by · slug · action); head stamped; coverage + abstained present"
import json,sys; r=json.load(open(sys.argv[1])); f=json.load(open(sys.argv[2]))
assert r["head"]=="abc1234" and r["model"]=="proposed" and r["written"] is True, (r["head"], r["written"])
d={x["slug"]:x for x in r["declared"]}
assert d["cooking"]["verdict"]=="SPLIT" and d["cooking"]["suggested_edit"]["split"][0]["slug"]=="cooking-sessions" and "cooking/sessions" in d["cooking"]["why"], d["cooking"]
assert d["pantry"]["verdict"]=="MERGE" and d["pantry"]["suggested_edit"]=={"merge_into":"recipe"}, d["pantry"]
assert d["recipe"]["verdict"]=="FEATURE" and "suggested_edit" not in d["recipe"], d["recipe"]
c={x["name"]:x for x in r["candidates"]}
assert list(c)==["dish history events","orph"], list(c)                                   # most endpoints first, then name
assert c["orph"]["named_by"]=="domain" and c["orph"]["suggested_slug"]=="orph" and c["orph"]["action"]=="Add orph", c["orph"]
assert c["dish history events"]["named_by"]=="table" and c["dish history events"]["suggested_slug"]=="dish-history-events" and c["dish history events"]["action"]=="Manage dishes — history", c["dish history events"]
assert c["dish history events"]["spans_entities"]==["cooking","progression","recipe"] and c["dish history events"]["kind"]=="candidate feature"
assert r["coverage"]["witnessed"]==0.975 and r["coverage"]["atoms"]==80 and r["coverage"]["anchored"]==78 and r["coverage"]["purity"]==0.897 and r["coverage"]["seeded_moved"]==9, r["coverage"]
assert r["abstained"]["count"]==2 and r["abstained"]["pieces"]==["endpoint:GET /health","endpoint:GET /z"], r["abstained"]
assert "orphan" not in json.dumps(r).lower()
assert f["head"]=="abc1234" and f["declared"]==r["declared"] and f["candidates"]==r["candidates"], "the file is the report minus out/written"
assert "window." not in open(sys.argv[2]).read(), "plain JSON — loaded by no page"
PY
o=$(python3 "$D" "$r"); echo "$o" | grep -q "3 declared verdict(s) \[FEATURE 1 · SPLIT 1 · MERGE 1\] · 2 candidate(s) · witnessed 78/80 atoms · 2 abstained · head abc1234" \
  && echo "$o" | grep -q "SPLIT    cooking" && echo "$o" | grep -q "CANDIDATE dish history events  (named by its table; slug dish-history-events; 3 endpoint(s))  — Manage dishes — history" \
  && ok || bad "FIRE: the one-line report + the verdict and candidate lines ($o)"
echo "$o" | grep -qi "orphan" && bad "R10: the report says orphan" || ok
# ── PROJECTION equality: the draft's declared verdicts are the block's proposed roster, field for field (nothing derived here) ──
python3 - "$T/fire.json" "$r/docs/site/center/c4-graph.json" <<'PY' && ok || bad "PROJECTION: declared verdicts ≠ the block's proposed roster (something was derived locally)"
import json,sys; r=json.load(open(sys.argv[1])); m=json.load(open(sys.argv[2]))["models"]
src={x["slug"]:x for x in m["rosters"]["proposed"]}
for d in r["declared"]:
    s=src[d["slug"]]; assert d["verdict"]==s["verdict"] and d["why"]==s["why"] and d.get("suggested_edit")==s.get("suggested_edit"), (d, s)
assert sorted(x["id"] for x in r["candidates"])==sorted(x["id"] for x in m["rosters"]["candidates"])
PY

# ── SILENT: all-FEATURE, no candidates → a VALID EMPTY draft ──
r=$(mkcenter silent); c4 | python3 -c "
import json,sys; j=json.load(sys.stdin); m=j['models']
for x in m['rosters']['proposed']: x['verdict']='FEATURE'; x.pop('suggested_edit',None)
m['rosters']['candidates']=[]; m['views']['proposed']['verdicts']={'FEATURE':3,'SPLIT':0,'MERGE':0,'ASPECT':0,'LAYER':0}; m['views']['proposed']['candidates']=0
print(json.dumps(j))" > "$r/docs/site/center/c4-graph.json"
python3 "$D" "$r" --json > "$T/silent.json"
python3 - "$T/silent.json" <<'PY' && ok || bad "SILENT: all-FEATURE → candidates [] with the verdicts still listed (a valid empty draft)"
import json,sys; r=json.load(open(sys.argv[1])); assert r["candidates"]==[] and all(x["verdict"]=="FEATURE" for x in r["declared"]) and r["written"] is True, r
PY
[ -f "$r/docs/site/center/entities.draft.json" ] && ok || bad "SILENT: the empty draft is WRITTEN (a stale draft never lingers)"

# ── HONEST-EMPTY ×4 ──
r="$T/nocenter"; mkdir -p "$r"; o=$(python3 "$D" "$r"); rc=$?
[ "$rc" = 0 ] && echo "$o" | grep -q "no center" && [ ! -e "$r/docs/site/center/entities.draft.json" ] && ok || bad "HONEST-EMPTY: no center → reason + nothing written + exit 0 ($o)"
r=$(mkcenter noc4); o=$(python3 "$D" "$r"); rc=$?
[ "$rc" = 0 ] && echo "$o" | grep -q "no c4-graph" && [ ! -e "$r/docs/site/center/entities.draft.json" ] && ok || bad "HONEST-EMPTY: no c4 → reason + nothing written ($o)"
r=$(mkcenter badc4); printf '{not json' > "$r/docs/site/center/c4-graph.json"; o=$(python3 "$D" "$r"); rc=$?
[ "$rc" = 0 ] && echo "$o" | grep -q "unreadable" && [ ! -e "$r/docs/site/center/entities.draft.json" ] && ok || bad "HONEST-EMPTY: unreadable c4 → reason + nothing written ($o)"
r=$(mkcenter nomodels); printf '{"head":"abc1234","l2":{},"stats":{}}' > "$r/docs/site/center/c4-graph.json"; o=$(python3 "$D" "$r"); rc=$?
[ "$rc" = 0 ] && echo "$o" | grep -q "regen with the current generators" && [ ! -e "$r/docs/site/center/entities.draft.json" ] && ok || bad "HONEST-EMPTY: no models block → 'regen with the current generators', nothing written ($o)"
r=$(mkcenter absent); printf '{"head":"abc1234","l2":{},"stats":{"models":{"present":false,"reason":"no levels graph (graft arm absent)"}}}' > "$r/docs/site/center/c4-graph.json"; o=$(python3 "$D" "$r"); rc=$?
[ "$rc" = 0 ] && echo "$o" | grep -q "the emitter ran and said: no levels graph" && [ ! -e "$r/docs/site/center/entities.draft.json" ] && ok || bad "HONEST-EMPTY: the emitter's absence carries its reason ($o)"

# ── DETERMINISM: unchanged input → byte-identical + "(unchanged)"; no wallclock ──
r=$(mkcenter det); c4 > "$r/docs/site/center/c4-graph.json"
python3 "$D" "$r" >/dev/null; h1=$(md5sum "$r/docs/site/center/entities.draft.json" | cut -d' ' -f1)
o=$(python3 "$D" "$r"); h2=$(md5sum "$r/docs/site/center/entities.draft.json" | cut -d' ' -f1)
[ "$h1" = "$h2" ] && echo "$o" | grep -q "(unchanged)" && ! grep -q '20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]T' "$r/docs/site/center/entities.draft.json" && ok || bad "DETERMINISM: unchanged input → byte-identical + '(unchanged)', no wallclock ($o)"

# ── ABSTAIN: a witnessless atom is listed in abstained, never a candidate (asserted in FIRE); the count rides coverage ──
python3 - "$T/fire.json" <<'PY' && ok || bad "ABSTAIN: the abstained atoms never appear among the candidates' members"
import json,sys; r=json.load(open(sys.argv[1])); mem=[m for c in r["candidates"] for m in c["members"]]; assert not (set(mem) & set(r["abstained"]["pieces"])) and r["coverage"]["abstained"]==2
PY

# ── MUTATION 1: a drafter that derives a verdict locally reddens the PROJECTION assert ──
sed 's/"why": r.get("why"), "evidence": r.get("evidence") or {},/"why": r.get("why"), "evidence": r.get("evidence") or {}, "verdict": ("MERGE" if r.get("slug") == "recipe" else r.get("verdict")),/' "$D" > "$T/mut1.py"
grep -q 'if r.get("slug") == "recipe"' "$T/mut1.py" || bad "MUTATION 1 precondition: the mutant did not apply"
cp "$D" "$T/_real.py"; cp "$REPO/skills/gabe-cc-update/scripts/draft-workflows.py" "$T/draft-workflows.py"
r=$(mkcenter mut1); c4 > "$r/docs/site/center/c4-graph.json"; python3 "$T/mut1.py" "$r" --json > "$T/mut1.json" 2>/dev/null
python3 - "$T/mut1.json" "$r/docs/site/center/c4-graph.json" <<'PY' && bad "MUTATION 1: a locally derived verdict passed the projection check" || ok
import json,sys; r=json.load(open(sys.argv[1])); m=json.load(open(sys.argv[2]))["models"]; src={x["slug"]:x for x in m["rosters"]["proposed"]}
assert all(d["verdict"]==src[d["slug"]]["verdict"] for d in r["declared"])
PY
# ── MUTATION 2: flip the fixture's anchor table on the table-named candidate → its fallback slug changes (the name is READ, not invented) ──
r=$(mkcenter mut2); c4 | python3 -c "
import json,sys; j=json.load(sys.stdin); c=j['models']['rosters']['candidates'][1]; c['anchor_table']='meal_log_events'; c.pop('suggested_slug'); c['name']='meal log events'; print(json.dumps(j))" > "$r/docs/site/center/c4-graph.json"
python3 "$D" "$r" --json > "$T/mut2.json"
python3 - "$T/mut2.json" <<'PY' && ok || bad "MUTATION 2: the table-named candidate follows the fixture's anchor table (slug meal-log-events)"
import json,sys; r=json.load(open(sys.argv[1])); c={x["name"]:x for x in r["candidates"]}; assert c["meal log events"]["suggested_slug"]=="meal-log-events" and "dish history events" not in c, c
PY

# ── --min 3: the 2-endpoint candidate is dropped, the 3-endpoint one stays ──
r=$(mkcenter mn); c4 > "$r/docs/site/center/c4-graph.json"; python3 "$D" "$r" --json --min 3 > "$T/mn.json"
python3 - "$T/mn.json" <<'PY' && ok || bad "--min 3: only the 3-endpoint candidate remains"
import json,sys; r=json.load(open(sys.argv[1])); assert [c["name"] for c in r["candidates"]]==["dish history events"], r["candidates"]
PY
# ── --model derived: every derived cluster as a row (features first, then aspects), no declared verdicts ──
r=$(mkcenter dv); c4 > "$r/docs/site/center/c4-graph.json"; python3 "$D" "$r" --json --model derived --out "$r/derived.json" > "$T/dv.json"
python3 - "$T/dv.json" <<'PY' && ok || bad "--model derived: the derived clusters (feature + aspect) as rows, declared []"
import json,sys; r=json.load(open(sys.argv[1])); assert r["model"]=="derived" and r["declared"]==[] and [(c["id"],c["kind"]) for c in r["candidates"]]==[("d:cooking_sessions","feature"),("a:auth","aspect")], r["candidates"]
PY

echo "draft-entities battery: $pass passed, $fail failed"
[ "$fail" -eq 0 ] || exit 1
