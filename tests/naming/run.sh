#!/usr/bin/env bash
# _a3_naming battery — every NAME a cluster could wear, computed once (naming-plan.md, 2026-09-06). Hermetic: a synthetic models block
# + atoms, python-stdlib only, zero-arg; the installed naming law is reached through GABE_DRAFT_WORKFLOWS pointing at the REPO copy.
#   * STRATEGIES  — table · class (acronym lever LLMModelFlow; OAuthConfig honestly 'o auth config') · path (common segment ·
#                   leaf fallback · collision suffix + count · the 1/3 self-disable) · action (the law, uncapped labels; absent +
#                   the reason when the script is unreachable) · config (domains · tables · the legacy url_domain_map fallback ·
#                   entities · adoption display_name; unused_words · unknown_entities) · both (prefix from the descent, the
#                   majority prefix, the table alone).
#   * CONVENTIONS — the seven forms with the project's words substituted; render() camel/pascal on the leading word-run.
#   * CONTRACT    — default/source, validation report-never-gate (bad strategy · bad convention · bad case), fe absent → said.
#   * JOIN KEY    — the block with names + naming popped is byte-equal to the block built without a config; row.name unchanged.
#   * DETERMINISM · R10.  Exit 0 = all pass.
set -u
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
export GABE_DRAFT_WORKFLOWS="$REPO/skills/gabe-cc-update/scripts/draft-workflows.py"
python3 - "$REPO" <<'PY'
import sys, json, copy, os
repo = sys.argv[1]; sys.path.insert(0, repo + "/templates/center/generators")
import _a3_naming as N
p = 0; f = 0
def ck(c, m):
    global p, f
    if c: p += 1
    else: f += 1; print("  FAIL:", m)

# ── words ──
ck(N.class_words("LLMModelFlow") == "llm model flow" and N.class_words("ChatMessageFeedback") == "chat message feedback" and N.class_words("Assistant__UserSpecificConfig") == "assistant user specific config",
   "class: acronym-aware split, lowercased, `__` → space")
ck(N.class_words("OAuthConfig") == "o auth config", "class: OAuthConfig reads 'o auth config' — honest, never guessed (a project renames it in naming.words.tables)")
ck(N.path_name(["/cooking/sessions/{id}/photos", "/cooking/sessions"]) == "sessions" and N.path_name(["/a/x", "/b/x", "/c/y"]) == "x" and N.path_name([]) is None,
   "path: the deepest common segment, else the most frequent leaf (ties alphabetical), None without paths")
ck(N.path_name(["/recipe/a", "/recipe/b", "/other/c"]) == "recipe" and N.path_name(["/a/x", "/b/y"]) is None,
   "path: every leaf unique → the level-1 majority prefix names it, else NO name (honest-empty beats an alphabetical pick)")
ck(N._majority_prefix(["/y/a", "/y/b", "/z/c"]) == "y" and N._majority_prefix(["/y/a", "/z/b"]) is None, "both: the level-1 prefix only under a strict majority")

# ── a synthetic block: three features (one domain-named, two table-named, two of them colliding on `path`), one candidate ──
def row(cid, table, cls, named_by, domain=None, twin=None):
    return {"id": cid, "kind": "feature", "name": (domain if named_by == "domain" else N._words(table)), "named_by": named_by, "domain": domain,
            "anchor_table": table, "anchor_cls": cls, "twin": twin, "members": ["apps/api/x.py#fn", "endpoint:GET /%s" % table]}
def block():
    return {"rosters": {"derived": [row("d:t1", "t1", "LLMModelFlow", "domain", "x", "fe·d:t1"), row("d:t2", "t2", "T2", "table"), row("d:t3", "t3", "OAuthConfig", "table"),
                                    {"id": "a:auth", "kind": "aspect", "name": "auth"}],
                        "proposed": [], "candidates": [{"id": "d:t3", "name": "t3", "kind": "feature", "named_by": "table", "anchor_table": "t3"}]}}
ATOMS = [{"ep": "endpoint:GET /x/a", "method": "GET", "path": "/x/a", "via": "http", "anchor": "t1"}, {"ep": "endpoint:POST /x/b", "method": "POST", "path": "/x/b", "via": "http", "anchor": "t1"},
         {"ep": "endpoint:TASK t", "method": "TASK", "path": "", "via": "task", "anchor": "t1"},
         {"ep": "endpoint:GET /y/c", "method": "GET", "path": "/y/c", "via": "http", "anchor": "t2"}, {"ep": "endpoint:GET /z/c", "method": "GET", "path": "/z/c", "via": "http", "anchor": "t2"},
         {"ep": "endpoint:GET /w/c", "method": "GET", "path": "/w/c", "via": "http", "anchor": "t3"}, {"ep": "endpoint:DELETE /w/c/{id}", "method": "DELETE", "path": "/w/c/{id}", "via": "http", "anchor": "t3"}]
LABELS = {"alpha": "Alpha Feature", "beta": "beta"}
FE = {"present": True, "by_home": {"fe·alpha": 4, "fe·beta": 2, "design-system": 9}}
b0 = block(); nm0 = N.apply(b0, ATOMS, LABELS, None, None, FE)
F = {r["id"]: r for r in b0["rosters"]["derived"] if r.get("kind") == "feature"}
ck(F["d:t1"]["names"]["table"] == "t1" and F["d:t1"]["names"]["class"] == "llm model flow" and F["d:t3"]["names"]["class"] == "o auth config" and F["d:t2"]["names"]["class"] == "t2",
   f"table + class per row (class falls back to the table words when the class is the table) ({F['d:t1'].get('names')})")
ck(F["d:t1"]["names"]["path"] == "x" and F["d:t2"]["names"]["path"] == "c (t2)" and F["d:t3"]["names"]["path"] == "c (t3)" and nm0["collisions"]["path"] == 2,
   f"path: the common segment; the two rows colliding on 'c' are suffixed with their table words and COUNTED ({[F[k]['names'].get('path') for k in ('d:t1','d:t2','d:t3')]} · {nm0['collisions']})")
ck(F["d:t1"]["names"]["action"] == "Add x — a · b" and F["d:t3"]["names"]["action"] == "Manage w — c", f"action: the naming law over the UNCAPPED labels; a TASK atom never votes ({F['d:t1']['names'].get('action')} · {F['d:t3']['names'].get('action')})")
ck(F["d:t1"]["names"]["both"] == "t1 · /x" and F["d:t2"]["names"]["both"] == "t2" and F["d:t3"]["names"]["both"] == "t3 · /w",
   f"both: the descent's domain · the majority prefix · the table alone when no majority holds ({[F[k]['names'].get('both') for k in ('d:t1','d:t2','d:t3')]})")
ck("config" not in F["d:t1"]["names"] and "config" not in nm0["disabled"] and nm0["coverage"] == {"domain": 3, "table": 3, "class": 3, "path": 3, "action": 3, "config": 0, "both": 3, "rows": 3} and "2 of 3 rows collide" in nm0["disabled"].get("path", ""),
   f"config: no words → no key on any cluster row, coverage 0, but the position stays ON while a claim entity carries a display name; path self-disables at 2 of 3 colliding ({nm0['coverage']} · {nm0['disabled']})")
nmE = N.apply(block(), ATOMS, {}, None, None, FE)
ck(nmE["disabled"].get("config", "").startswith("no naming.words") and nmE["entities"] == {}, f"config: no words AND no display names → the position is disabled with the reason ({nmE['disabled']})")
ck(all(r["name"] in ("x", "t2", "t3") for r in F.values()) and b0["rosters"]["candidates"][0]["names"] == F["d:t3"]["names"] and "names" not in [r for r in b0["rosters"]["derived"] if r["kind"] == "aspect"][0],
   "row.name is untouched (the domain strategy IS row.name); a candidate copies its feature's names{}; an aspect carries none")
ck(nm0["present"] is True and nm0["default"] == "domain" and nm0["source"] == "built-in" and nm0["fe"]["convention"] == "case" and nm0["fe"]["present"] and nm0["fe"]["homes"] == 3 and nm0["fe"]["twins"] == 1 and nm0["config_error"] is None and nm0["unused_words"] == [] and nm0["unknown_entities"] == [],
   f"contract: built-in defaults domain · case, fe present, twins counted, no error ({ {k: nm0.get(k) for k in ('default','source','config_error')} })")
ck(nm0["entities"] == {"alpha": {"display": "Alpha Feature", "source": "adoption display_name"}}, f"config for a claim entity: adoption display_name when it differs from the slug ({nm0['entities']})")
fm = nm0["fe"]["forms"]
ck(fm["case"] == {"fe": "{name|camel}", "be": "{name|pascal}"} and fm["prefix"]["fe"] == "fe · {name}" and fm["suffix"]["fe"] == "{name} (ui)" and fm["bracket"] == {"fe": "[ui] {name}", "be": "[api] {name}"} and fm["glyph"]["mark"] == "screen" and fm["none"] == {"fe": "{name}", "be": "{name}"},
   f"forms: the seven templates with the suite's default words substituted ({fm})")
ck(N.render(fm["case"]["fe"], "cooking sessions · /cooking") == "cookingSessions · /cooking" and N.render(fm["case"]["be"], "legal-consent") == "LegalConsent" and N.render(fm["case"]["be"], "Manage cooking — readiness · stage") == "ManageCooking — readiness · stage" and N.render(fm["bracket"]["be"], "cooking") == "[api] cooking",
   "render: camel/pascal on the leading word-run only; separators and the trailing detail keep their words; a word form substitutes {name}")
ck(N.render(fm["case"]["fe"], "iPhone sync") == "iPhoneSync" and N.render(fm["case"]["be"], "Legal/Consent") == "LegalConsent" and N.render(fm["case"]["be"], "R&D lane") == "RDLane",
   "render: word interiors survive (the project's own casing); `/` and `&` split words")
ck(N.render("{name|shout}", "cooking") == "cooking" and N.forms(N.DEFAULT_WORDS, {"frontend": "none", "backend": "pascal"})["case"] == {"fe": "{name}", "be": "{name|pascal}"},
   "render: an unknown transform degrades to the bare name; an identity case emits the bare token — no renderer ever sees {name|none}")
bN = block(); nmN = N.apply(bN, ATOMS, LABELS, {"fe": {"case": {"frontend": "none", "backend": "none"}}}, None, FE)
ck(nmN["config_error"] is None and nmN["fe"]["forms"]["case"] == {"fe": "{name}", "be": "{name}"} and "|none" not in json.dumps(nmN["fe"]["forms"]), f"case none is legal and renders bare ({nmN['fe']['forms']['case']})")

# ── config: words · entities · legacy url_domain_map · the project's marks and case pair ──
CFG = {"strategy": "class", "fe": {"convention": "bracket", "frontend": "screens", "backend": "services", "case": {"frontend": "pascal", "backend": "camel"}},
       "words": {"domains": {"x": "the x lane"}, "tables": {"t3": "third things", "ghost": "nothing"}}, "entities": {"alpha": "The Alpha", "nope": "n"}}
b1 = block(); nm1 = N.apply(b1, ATOMS, LABELS, CFG, {"w": "legacy w"}, FE)
F1 = {r["id"]: r for r in b1["rosters"]["derived"] if r.get("kind") == "feature"}
ck(F1["d:t1"]["names"]["config"] == "the x lane" and F1["d:t3"]["names"]["config"] == "third things" and "config" not in F1["d:t2"]["names"],
   f"config: words.domains for a domain-named row, words.tables for a table-named row, nothing for the rest ({[F1[k]['names'].get('config') for k in ('d:t1','d:t2','d:t3')]})")
ck(nm1["default"] == "class" and nm1["source"] == "center.config.json#naming" and nm1["fe"]["convention"] == "bracket" and nm1["fe"]["forms"]["bracket"] == {"fe": "[screens] {name}", "be": "[services] {name}"} and nm1["fe"]["forms"]["case"] == {"fe": "{name|pascal}", "be": "{name|camel}"},
   f"config: the strategy, the convention, the project's marks and the swapped case pair ride the forms ({nm1['fe']['forms']['bracket']} · {nm1['fe']['forms']['case']})")
ck(nm1["entities"]["alpha"] == {"display": "The Alpha", "source": "naming.entities"} and nm1["unknown_entities"] == ["nope"] and nm1["unused_words"] == ["ghost"] and nm1["config_error"] is None and "config" not in nm1["disabled"],
   f"config: naming.entities wins over display_name; an unknown slug and an unused word are NAMED, never a crash ({nm1['unknown_entities']} · {nm1['unused_words']})")
b2 = block(); nm2 = N.apply(b2, ATOMS, LABELS, {"words": {"domains": {}}}, {"x": "legacy x"}, FE)
ck({r["id"]: r for r in b2["rosters"]["derived"] if r.get("kind") == "feature"}["d:t1"]["names"]["config"] == "legacy x", "config: the legacy top-level url_domain_map is the fallback for words.domains — never moved, still read")
b3 = block(); nm3 = N.apply(b3, ATOMS, LABELS, {"strategy": "verb", "fe": {"convention": "emoji", "case": {"frontend": "shout", "backend": 7}}}, None, FE)
ck(nm3["default"] == "domain" and nm3["fe"]["convention"] == "case" and nm3["fe"]["case"] == {"frontend": "camel", "backend": "pascal"} and "naming.strategy 'verb'" in nm3["config_error"] and "naming.fe.convention 'emoji'" in nm3["config_error"]
   and "naming.fe.case.frontend is not one of camel · pascal · none" in nm3["config_error"] and "naming.fe.case.backend is not" in nm3["config_error"] and "shout" not in json.dumps(nm3["fe"]["forms"]),
   f"validation is report-never-gate: a bad strategy, convention and BOTH case keys keep the built-ins and are NAMED under their real keys ({nm3['config_error']})")
nmM = N.apply(block(), ATOMS, LABELS, "domain", None, FE)
ck("naming is a str, not an object — the whole block was ignored" in nmM["config_error"] and nmM["source"] == "center.config.json#naming (ignored — see config_error)" and nmM["default"] == "domain",
   f"a naming block that is not an object is NAMED and the source says ignored ({nmM['config_error']} · {nmM['source']})")
nmM2 = N.apply(block(), ATOMS, LABELS, {"strategy": ["class"], "fe": 7, "words": {"domains": ["x"], "tables": {"t3": None}}, "entities": {"alpha": 3}}, "not-a-map", FE)
ck(all(x in nmM2["config_error"] for x in ("naming.strategy ['class']", "naming.fe is a int", "naming.words.domains is a list", "naming.words.tables.t3 is not a word", "naming.entities.alpha is not a word", "url_domain_map is a str")) and nmM2["default"] == "domain" and nmM2["fe"]["convention"] == "case",
   f"every wrong-typed level is NAMED (strategy · fe · words.domains · a table word · an entity word · url_domain_map) and the built-ins stand ({nmM2['config_error']})")
nmW = N.apply(block(), ATOMS, LABELS, {"fe": {"words": {"frontend": "", "backend": "server"}}}, None, FE)
ck("naming.fe.words.frontend is not a word" in nmW["config_error"] and nmW["fe"]["words"] == {"frontend": "ui", "backend": "server"}, f"the nested words shape names its real key; the good half still lands ({nmW['config_error']})")
nmW2 = N.apply(block(), ATOMS, LABELS, {"fe": {"frontend": "client", "backend": 3}}, None, FE)
ck("naming.fe.backend is not a word" in nmW2["config_error"] and nmW2["fe"]["words"] == {"frontend": "client", "backend": "api"}, f"the flat words shape (the template's) names its real key ({nmW2['config_error']})")
b4 = block(); nm4 = N.apply(b4, ATOMS, LABELS, None, None, {"present": False, "reason": "no frontend root"})
ck(nm4["fe"]["present"] is False and nm4["fe"]["reason"] == "no frontend root" and nm4["fe"]["convention"] == "case", "fe absent → present False with the emitter's reason (the station disables the mark pill from this)")

# ── the path self-disable (≥ 1/3 rows collide) ──
b5 = block(); b5["rosters"]["derived"] = [r for r in b5["rosters"]["derived"] if r["id"] != "d:t1"]; nm5 = N.apply(b5, ATOMS, LABELS, None, None, FE)
bZ = block(); bZ["rosters"]["derived"] = []; bZ["rosters"]["candidates"] = []; nmZ = N.apply(bZ, ATOMS, LABELS, None, None, FE)
ck(all(nmZ["disabled"].get(k, "").startswith("no derived cluster rows") for k in ("table", "class", "path", "action", "both")) and "config" not in nmZ["disabled"] and nmZ["coverage"]["rows"] == 0,
   f"rows 0: every cluster position disables with ONE shared reason; config stays ON while a claim entity has a display name ({nmZ['disabled']})")
nmZ2 = N.apply(bZ, ATOMS, {}, None, None, FE)
nmR = N.apply(block(), ATOMS, {}, {"strategy": "config"}, None, FE)
ck(nmR["default"] == "domain" and nmR["requested"] == "config" and "naming.strategy 'config' cannot be served on this feed" in (nmR["config_error"] or ""),
   f"a default the feed cannot serve (config with no words) is NAMED, `requested` kept, the built-in stands ({nmR['config_error']})")
ck("config" in nmZ2["disabled"] and "no derived cluster rows and no naming.words" in nmZ2["disabled"]["config"], "rows 0 and no display names: config disables too, with its reason")
ck("path" in nm5["disabled"] and "2 of 2 rows collide" in nm5["disabled"]["path"], f"path: every row colliding → the position disables itself with the count ({nm5['disabled']})")

# ── action: the law unreachable → absent, the reason names the path; coverage 0 ──
os.environ["GABE_DRAFT_WORKFLOWS"] = "/nonexistent/draft-workflows.py"
b6 = block(); nm6 = N.apply(b6, ATOMS, LABELS, None, None, FE)
os.environ["GABE_DRAFT_WORKFLOWS"] = repo + "/skills/gabe-cc-update/scripts/draft-workflows.py"
ck(all("action" not in r.get("names", {}) for r in b6["rosters"]["derived"] if r.get("kind") == "feature") and nm6["coverage"]["action"] == 0 and "/nonexistent/draft-workflows.py" in nm6["disabled"]["action"] and nm6["action_source"]["reason"],
   f"action: the installed law unreachable → no action key on any row, coverage 0, the path in the reason — never a crash ({nm6['disabled'].get('action')})")

# ── JOIN KEY: names + naming are ADDITIVE — pop them and the block is byte-equal under every strategy × convention ──
def strip(b):
    b = copy.deepcopy(b)
    for r in b["rosters"]["derived"] + b["rosters"]["candidates"]:
        r.pop("names", None)
    return json.dumps(b, sort_keys=True)
base = strip(block())
same = True
for st in N.STRATEGIES:
    for cv in N.CONVENTIONS:
        bb = block(); N.apply(bb, ATOMS, LABELS, {"strategy": st, "fe": {"convention": cv}}, None, FE)
        same = same and strip(bb) == base and all(r["name"] in ("x", "t2", "t3") for r in bb["rosters"]["derived"] if r.get("kind") == "feature")
ck(same, "JOIN KEY: under every strategy × convention the block minus names{} is byte-equal to the config-less block and row.name never changes")
ck(json.dumps(N.apply(block(), ATOMS, LABELS, CFG, {"w": "legacy w"}, FE), sort_keys=True) == json.dumps(nm1, sort_keys=True), "deterministic: a second run is byte-identical")
ck(nm1["action_source"]["path"].startswith("~/") and "/home/" not in json.dumps(nm1), f"PORTABLE: the naming-law path is home-relative on the map — never an operator-machine path (the doctor's lint) ({nm1['action_source']})")
ck("orphan" not in (json.dumps(nm1) + json.dumps(b1) + (N.__doc__ or "")).lower(), "R10: no 'orphan' in the block, the rows or the doc")
# ── REGISTRIES (naming-plan Phase 2): the id-resolution bodies never learn a naming word — a negative grep guard over the functions
#    that join on fe·/d: ids in the generators and the gabe-map tools; a fixture inserting the word proves the guard fires ──
import inspect, importlib
sys.path.insert(0, repo + "/skills/gabe-map/scripts")
import _a3_homing, _a3_graft, tools as T, tools_wave2 as W2, tools_wave4 as W4
GUARD = ("naming", "convention", "names[", "camel", "pascal")
def clean(src):
    return not any(w in src for w in GUARD)
import _a3_models as MM
ck(hasattr(W2, "t_center_overview") and hasattr(W4, "t_entity_models") and hasattr(MM, "attach") and hasattr(MM, "levels_slice"), "REGISTRIES guard targets exist (a rename must redden, never pass silently)")
bodies = {"_a3_graft._fe_pair": inspect.getsource(_a3_graft._fe_pair), "_a3_graft._fe_home": inspect.getsource(_a3_graft._fe_home),
          "tools.t_entity_context": inspect.getsource(T.t_entity_context), "tools.detect_kind": inspect.getsource(T.detect_kind),
          "tools_wave2.t_center_overview": inspect.getsource(W2.t_center_overview),
          "tools_wave4._resolve_piece": inspect.getsource(W4._resolve_piece), "tools_wave4._claim_of": inspect.getsource(W4._claim_of),
          "tools_wave4.t_entity_models (id resolution)": inspect.getsource(W4.t_entity_models).split("# ── model → the roster")[0],
          "_a3_models.attach": inspect.getsource(MM.attach), "_a3_models.levels_slice": inspect.getsource(MM.levels_slice)}
hom_src = open(repo + "/templates/center/generators/_a3_homing.py", encoding="utf-8").read()
bodies["_a3_homing (whole module)"] = hom_src
bad = [k for k, v in bodies.items() if not clean(v)]
ck(not bad, f"REGISTRIES: an id-resolution body carries a naming word ({bad}) — a convention must never reach a join")
ck(not clean(inspect.getsource(W4._claim_of) + "  # convention"), "REGISTRIES guard fires on a fixture that inserts the word (the guard is live)")
print(f"naming battery: {p} passed, {f} failed")
sys.exit(1 if f else 0)
PY
