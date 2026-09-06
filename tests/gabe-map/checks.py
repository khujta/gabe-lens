#!/usr/bin/env python3
"""gabe-map battery — the server's executable contract (run by tests/gabe-map/run.sh).

Hermetic: a synthetic center (archmap · c4-graph · center.config · adoption) inside a temp git repo
with real commits (so freshness has a history), a FAKE `graft` on PATH returning canned JSON, real
`git grep`, and the battery client (read deadlines on every message). Proves FIRE and SILENT for the
wire laws, honest-empty, freshness, every `touches` kind, raw parity, and all five emit gates.

Env: SERVER_OVERRIDE (path to server.py — mutation proof; siblings resolve from that dir, shared
skills from GABE_SKILLS_DIR) · GABE_MAP_E2E=1 adds the API-billed harness run (opt-in).
"""
from __future__ import annotations
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SERVER = os.environ.get("SERVER_OVERRIDE") or os.path.join(REPO, "skills", "gabe-map", "scripts", "server.py")
os.environ.setdefault("GABE_SKILLS_DIR", os.path.join(REPO, "skills"))
sys.path.insert(0, HERE)
from client import Client, parse_text  # noqa: E402

PASS = FAIL = 0


def ok(cond: bool, msg: str, extra: str = ""):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print("FAIL: %s%s" % (msg, (" — " + str(extra)[:300]) if extra else ""))


def sh(args, cwd=None, env=None):
    return subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True)


def git(root, *args):
    r = sh(["git", "-C", root, *args])
    return r.stdout.strip()


# ── fixture ────────────────────────────────────────────────────────────────────
def write(root, rel, text):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)


def make_repo(T: str, seed_ignore: bool = True) -> str:
    root = os.path.join(T, "proj")
    os.makedirs(root)
    sh(["git", "init", "-q", root])
    git(root, "config", "user.email", "t@t"); git(root, "config", "user.name", "t")
    if seed_ignore:
        write(root, ".gitignore", ".kdbp/map-deltas.jsonl\n.kdbp/map-deltas-rollup.jsonl\n")
    os.makedirs(os.path.join(root, ".kdbp"), exist_ok=True)
    write(root, "apps/api/services/thing.py", '"""Service for things — see other.py which calls thing()."""\n\n\ndef thing():\n    return 1\n')
    write(root, "apps/api/other.py", 'from apps.api.services.thing import thing\n\n\nclass Caller:\n    def run(self):\n        return thing()\n\n\nclass Helper:\n    def run(self):\n        return 2\n')
    write(root, "apps/api/services/downstream.py", 'from apps.api.services.thing import thing\n\n\ndef down():\n    return thing()  # a caller the index missed\n')
    write(root, "apps/api/tests/test_thing.py", '"""Docstring mentions thing but never calls it."""\n\n\ndef test_other():\n    assert 1 == 1\n')
    write(root, "apps/api/api/things.py", 'def get_thing(item_id: int):\n    return {"id": item_id}\n')
    write(root, "apps/api/models/thing.py", 'class Thing:\n    pass\n')
    write(root, "apps/api/models/widget.py", 'class Widget:\n    pass\n')
    write(root, "apps/api/services/shared.py", 'X = 1\n')
    write(root, "apps/api/integrations/x.py", 'def a():\n    pass\n\n\ndef b():\n    pass\n')
    write(root, "apps/web/src/things.ts", 'export const Things = () => fetch("/api/v1/things/1");\n')
    write(root, "README.md", "fixture\n")
    git(root, "add", "-A"); git(root, "commit", "-q", "-m", "base")
    head = git(root, "rev-parse", "--short=8", "HEAD")
    center(root, head)
    git(root, "add", "-A"); git(root, "commit", "-q", "-m", "regen")          # the regen commit = freshness base
    write(root, "README.md", "fixture v2\n")
    git(root, "add", "-A"); git(root, "commit", "-q", "-m", "docs only")     # commits_since 2, nothing mapped → fresh
    return root


def center(root: str, head: str):
    ents = {
        "thing": {
            "defines": {"apps/api/services/thing.py": ["thing()"], "apps/api/other.py": ["Caller", "Helper"],
                        "apps/web/client/types.gen.ts": ["loginLoginAccessTokenData"], "apps/web/src/login.ts": ["loginBanner"]},
            "endpoints": [{"method": "GET", "path": "/things/{item_id}", "fn": "get_thing", "file": "apps/api/api/things.py",
                           "status": "200", "resp": "ThingOut", "doc": "One thing", "touches": ["Thing"], "touches_x": ["Annotated"], "stream": True,
                           "middleware": [{"name": "auth(Scope.READ)", "callee": "auth", "fn": "apps/api/deps.py::auth", "gate": True, "via": "param-dep"},
                                          {"name": "require_auth_scope(Scope.WRITE)", "callee": "require_auth_scope", "fn": "apps/api/deps.py::require_auth_scope", "gate": True, "via": "param-dep"},
                                          {"name": "get_db", "callee": "get_db", "gate": False, "via": "param-dep"}]},
                          {"method": "DELETE", "path": "/things/{item_id}", "fn": "delete_thing", "file": "apps/api/api/things.py",
                           "status": "204", "resp": "None", "doc": "Drop one thing", "touches": ["Thing"], "touches_x": [],
                           "middleware": [{"name": "auth(Scope.READ, allow_anonymous=True)", "callee": "auth", "fn": "apps/api/deps.py::auth", "gate": True, "via": "param-dep"}]},
                          {"method": "POST", "path": "/login/access-token", "fn": "login", "file": "apps/api/api/login.py",
                           "status": "200", "resp": "Token", "doc": "Log in", "touches": [], "touches_x": []}],
            "files": [["services", "apps/api/services/thing.py", 5], ["api", "apps/api/api/things.py", 2],
                      ["services", "apps/api/services/shared.py", 1], ["services", "apps/api/other.py", 11],
                      ["models", "apps/api/models/thing.py", 2], ["services", "apps/api/services/downstream.py", 5]],
            "models": [{"cls": "Thing", "table": "things", "file": "apps/api/models/thing.py",
                        "cols": [["id", "int", ""], ["name", "str", ""]], "fks": {}, "doc": "A thing", "uqs": [], "rels": []}],
            "schemas": [{"cls": "ThingOut", "file": "apps/api/schemas/thing.py", "fields": [["id", "int", ""]], "doc": ""},
                        {"cls": "ThingOut", "file": "apps/api/schemas/thing.py", "fields": [["id", "int", ""]], "doc": ""}],   # the within-entity duplicate row (tier0 shape)
        },
        "other": {
            "defines": {"apps/api/models/widget.py": ["Widget"]},
            "endpoints": [],
            "files": [["services", "apps/api/services/shared.py", 1], ["models", "apps/api/models/widget.py", 2]],
            "models": [{"cls": "Widget", "table": "widgets", "file": "apps/api/models/widget.py",
                        "cols": [["id", "int", ""], ["thing_id", "int", ""]], "fks": {"thing_id": "things.id"}, "doc": "", "uqs": [], "rels": []}],
            "schemas": [{"cls": "ThingOut", "file": "apps/api/schemas/thing.py", "fields": [["id", "int", ""]], "doc": ""}],   # the same schema consumed by a second entity
        },
    }
    fi = {
        "apps/api/services/thing.py::thing": {"name": "thing", "fn": "thing", "file": "apps/api/services/thing.py", "entity": "thing",
                                              "layer": "services", "handler": False, "async": False, "lines": 2, "returns": "int",
                                              "doc": "—", "usage": 2, "access": {"commits": False, "ops": [{"model": "Thing", "table": "things", "rw": "r"}]}},
        "apps/api/api/things.py::get_thing": {"name": "get_thing", "fn": "get_thing", "file": "apps/api/api/things.py", "entity": "thing",
                                              "layer": "api", "handler": True, "async": False, "lines": 2, "returns": "dict", "doc": "—",
                                              "usage": 0, "access": {"commits": False, "ops": [{"model": "Thing", "table": "things", "rw": "r"}]}},
        "apps/api/other.py::Caller.run": {"name": "run", "fn": "Caller.run", "file": "apps/api/other.py", "entity": "thing", "layer": "services",
                                          "handler": False, "async": False, "lines": 2, "returns": "int", "doc": "—", "usage": 0, "access": {"commits": False, "ops": []}},
        "apps/api/other.py::Helper.run": {"name": "run", "fn": "Helper.run", "file": "apps/api/other.py", "entity": "thing", "layer": "services",
                                          "handler": False, "async": False, "lines": 2, "returns": "int", "doc": "—", "usage": 0, "access": {"commits": False, "ops": []}},
        # F2: two METHODS sharing the bare name `search` — the qualified join must keep them apart
        "apps/api/services/thing.py::Svc.search": {"name": "search", "fn": "Svc.search", "file": "apps/api/services/thing.py", "entity": "thing", "layer": "services",
                                                   "handler": False, "async": False, "lines": 2, "returns": "list", "doc": "—", "usage": 1, "access": {"commits": False, "ops": []}},
        "apps/api/services/other_svc.py::Other.search": {"name": "search", "fn": "Other.search", "file": "apps/api/services/other_svc.py", "entity": "thing", "layer": "services",
                                            "handler": False, "async": False, "lines": 2, "returns": "list", "doc": "—", "usage": 0, "access": {"commits": False, "ops": []}},
        # review 2026-09-06: the task FN is usually ALSO in function_insight (36 of 46 on onyx) — the function record must win the bare name and cross-link the task root
        "apps/api/tasks.py::sweep_things_task": {"name": "sweep_things_task", "fn": "sweep_things_task", "file": "apps/api/tasks.py", "entity": "thing", "layer": "services",
                                                 "handler": False, "async": False, "lines": 3, "returns": "None", "doc": "Sweep", "usage": 0, "access": {"commits": True, "ops": [{"model": "Thing", "table": "things", "rw": "w"}]}},
    }
    mi = {"Thing": {"kind": "model", "entity": "thing", "file": "apps/api/models/thing.py", "fk_in": 1, "internal": 1, "touches": 1, "usage": 1,
                    "internal_refs": [{"file": "apps/api/services/thing.py", "defs": ["thing"]}]},
          "Widget": {"kind": "model", "entity": "other", "file": "apps/api/models/widget.py", "fk_in": 0, "internal": 0, "touches": 0, "usage": 0, "internal_refs": []},
          "ThingOut": {"kind": "schema", "entity": "thing", "file": "apps/api/schemas/thing.py", "fk_in": 0, "internal": 1, "touches": 0, "usage": 0,
                       "internal_refs": [{"file": "apps/api/api/things.py", "defs": ["get_thing"]}]}}
    ti = {"by_function": {"apps/api/services/thing.py::thing": {"direct": [{"cid": "C7", "name": "test_thing_C7", "state": "pass", "corpus": "api", "tfile": "apps/api/tests/test_thing.py"}]}},
          "by_model": {"Thing": {"via_route": [{"cid": "C8", "name": "test_get_thing_C8", "state": "pass", "corpus": "api", "tfile": "apps/api/tests/test_things_api.py"}]}},
          "by_endpoint": {"apps/api/api/things.py::get_thing": {"api": [{"cid": "C8", "name": "test_get_thing_C8", "state": "pass", "corpus": "api", "tfile": "apps/api/tests/test_things_api.py"}],
                                                                "e2e": [{"cid": "", "name": "3 case(s)", "state": "file", "corpus": "e2e", "tfile": "apps/web/e2e/things.spec.ts", "n": 3}]}},
          "by_file": {"apps/api/services/thing.py": {"coverage": None, "reach": ["apps/api/tests/test_thing.py"]}},
          "case_home": {"C7": "apps/api/tests/test_thing.py", "C8": "apps/api/tests/test_things_api.py"},
          "case_own": {}, "exercises": {}}
    archmap = {"version": 2, "head": head, "generated": "2026-09-02 00:00Z", "entities": ents, "function_insight": fi, "model_insight": mi,
               "test_insight": ti, "guard_insight": {"files": {}, "functions": {}, "totals": {}},
               "file_census": {"claimed": 8, "scanned_dirs": ["apps/api"],
                               "unclaimed": [{"file": "apps/api/integrations/x.py", "fns": 2, "reason": "file not in any entity's code map", "routes": 0, "tables": 0}]},
               "coverage": {"thing": {"total": 2, "covered": 1, "unproven": ["x"], "golden_total": 1, "golden_covered": 0, "inferred": [], "malformed": 0, "unclassified": []}},
               "model_census": {"claimed": 2, "scanned_dirs": 1, "unclaimed": []}, "schema_homing": {},
               # Part B (2026-09-06): the repo-study keys — task roots · route mounts · the blocked twin pass · an unparseable file · ASGI middleware
               "task_roots": [{"method": "TASK", "path": "sweep_things", "fn": "sweep_things_task", "file": "apps/api/tasks.py", "doc": "Sweep", "resp": "—", "status": "—", "touches": [], "touches_x": []}],
               "tasks": {"tasks": [{"name": "sweep_things", "fn": "sweep_things_task", "file": "apps/api/tasks.py", "line": 3, "doc": "Sweep"}],
                         "stats": {"tasks": 1, "sites": 1, "edges": 1, "unresolved": []}},
               "route_mounts": {"mounted": 1, "routers": 1, "scanned": 1, "unresolved": [{"file": "apps/api/app.py", "line": 3, "why": "non-literal prefix: settings.PREFIX"}]},
               "fn_similarity": {"mode": "blocked", "pairs": 10, "budget": 5, "sizable": 9, "rare_df": 40},
               "unparseable": [["apps/api/integrations/x.py", "unparseable: bad"]],
               "app_middleware": [{"cls": "RateLimiterMiddleware", "file": "apps/api/app.py", "line": 12, "order": 0, "scope": "all"}]}
    ep_id = "endpoint:GET /things/{item_id}"
    c4 = {"version": 1, "head": head, "colors": {},
          "l1": {"nodes": [{"id": "thing", "kind": "entity", "slug": "thing"}, {"id": "other", "kind": "entity", "slug": "other"}],
                 "edges": [{"source": "other", "target": "thing", "weight": 1, "kinds": {"fk": 1}}]},
          "l2": {"thing": {"nodes": [{"id": ep_id, "kind": "endpoint", "fn": "get_thing", "label": "GET /things/{item_id}", "stream": True,
                                      "behind": {"fns": 2, "depth": 1, "names": ["thing", "AuthContext.require", "Svc.search"]},
                                      "access": {"commits": False, "ops": [{"model": "Thing", "rw": "r", "table": "things"}]}, "det": {"cases": []}},
                                     {"id": "endpoint:POST /login/access-token", "kind": "endpoint", "fn": "login", "label": "POST /login/access-token"},
                                     {"id": "endpoint:TASK sweep_things", "kind": "endpoint", "fn": "sweep_things_task", "label": "TASK sweep_things",
                                      "behind": {"fns": 1, "depth": 1, "names": ["sweep_helper"]}},
                                     {"id": "provider:litellm", "kind": "provider", "label": "litellm", "pclass": "llm"},
                                     {"id": "model:Thing", "kind": "model"}, {"id": "schema:ThingOut", "kind": "schema"},
                                     {"id": "web:apps/web/src/things", "kind": "web"}],
                           "edges": [{"kind": "reads_from", "source": ep_id, "target": "model:Thing"},
                                     {"kind": "touches", "source": ep_id, "target": "schema:ThingOut"}]},
                 "other": {"nodes": [{"id": "model:Widget", "kind": "model"}], "edges": []}},
          "cross_edges": [{"from": "model:Widget", "to": "model:Thing", "via": "thing_id", "from_slug": "other", "to_slug": "thing"},
                          {"kind": "bridge", "from": "web:apps/web/src/things", "to": ep_id, "from_slug": "thing", "to_slug": "thing"}],
          "fe": {"pieces": [{"id": "fe:apps/web/src/things.ts#Things", "file": "apps/web/src/things.ts", "name": "Things", "kind": "hook",
                             "hrole": "fetcher", "homed_by": "config", "fed2w": 1, "channel": "read", "cache": False, "span": [1, 3]},
                            {"id": "fe:apps/web/client/types.gen.ts#loginLoginAccessTokenData", "file": "apps/web/client/types.gen.ts",
                             "name": "loginLoginAccessTokenData", "kind": "fe-type"}], "edges": [],
                 "homes": [{"id": "fe·thing", "kind": "fe", "pair": "thing", "pieces": 1, "areas": 1}]},
          "stats": {"graft": {"present": True, "index_hash": "abc123abc123"},
                    "web": {"present": True, "extractor": "fetch", "screens": 1, "fetch_sites": 3, "matched": 1, "dynamic": 0, "unhomed": 1,
                            "other_roots": ["mobile/src"], "unmatched": [{"m": "GET", "p": "/x", "from": "web:apps/web/src/other"},
                                                                          {"m": "GET", "p": "/api/v1/things/{id}", "from": "web:apps/web/src/other"}]},
                    "providers": {"count": 1, "by_provider": {"litellm": 1}, "by_pclass": {"llm": 1}}, "gate_endpoints": 2,
                    "fe": {"present": True, "homing": "config"}}, "layout": {}}
    # P0: the levels.json edges the trace/blast tools read — direction matters (reverse s/t = the mutation that must fail the FIRE)
    levels = {"fn_edges": [{"s": "apps/api/api/things.py#get_thing", "t": "apps/api/services/thing.py#thing", "rel": "calls", "conf": "extracted"},
                           {"s": "apps/api/services/thing.py#thing", "t": "provider:redis", "rel": "reaches", "conf": "inferred"},
                           {"s": "apps/api/api/things.py#get_thing", "t": "apps/api/tasks.py#sweep_things_task", "rel": "dispatches", "conf": "extracted"}],
              # Part C: the membership evidence the emitter writes onto levels.json (read lazily by touches + map_census)
              "homing": {"present": True, "rule": {"move_share": 0.6, "move_min_users": 2, "shared_min": 3, "text": "agree · move candidate · shared · stay — evidence only, nothing re-homed"},
                         "stats": {"present": True, "pieces": 3, "agree": 1, "stay": 0, "move": 1, "shared": 1, "by_kind": {"function": {"pieces": 2, "move": 1, "shared": 1}, "endpoint": {"pieces": 1, "move": 0, "shared": 0}},
                                   "thresholds": {"move_share": 0.6, "move_min_users": 2, "shared_min": 3},
                                   "move_named": [{"piece": "apps/api/services/thing.py#thing", "home": "thing", "to": "other", "share": 0.75}], "move_named_note": None, "shared_named": ["apps/api/other.py#Helper.run"]},
                         "pieces": {"apps/api/services/thing.py#thing": {"kind": "function", "home": "thing", "by": "file", "users": {"other": 3, "thing": 1}, "data": {"other": 1}, "verdict": "move", "to": "other", "share": 0.75},
                                    "apps/api/other.py#Helper.run": {"kind": "function", "home": "thing", "by": "file", "users": {"other": 1, "thing": 1, "third": 1}, "data": {}, "verdict": "shared", "to": None, "share": 0.33},
                                    "endpoint:GET /things/{item_id}": {"kind": "endpoint", "home": "thing", "by": "file", "users": {"thing": 1}, "data": {"thing": 1}, "verdict": "agree", "to": None, "share": None}}}}
    cfg = {"entities": {"thing": {"test_rx": "test_", "proofs": [], "models": ["Thing"],
                                  "code": {"services": ["apps/api/services/*.py", "apps/api/other.py"], "api": ["apps/api/api/*.py"], "models": ["apps/api/models/thing.py"]}},
                        "other": {"test_rx": "test_", "proofs": [], "models": ["Widget"], "code": {"models": ["apps/api/models/widget.py"]}}},
           "url_domain_map": {}}
    adoption = {"sections": [{"entity": "thing", "display_name": "Thing", "rank": "critical", "status": "approved",
                              "checklist": {"a": True, "b": False}, "signals": {}, "notes": ""}]}
    for name, data in (("archmap.json", archmap), ("c4-graph.json", c4), ("center.config.json", cfg), ("adoption.json", adoption), ("levels.json", levels)):
        write(root, "docs/site/center/" + name, json.dumps(data, indent=1, sort_keys=True))


def variant(root, mutate):
    """Rewrite the center on disk through `mutate(archmap, c4) -> (archmap, c4, drop_adoption)`; restore with `restore(root)`."""
    cdir = os.path.join(root, "docs/site/center")
    a = json.load(open(os.path.join(cdir, "archmap.json"))); c = json.load(open(os.path.join(cdir, "c4-graph.json")))
    a, c, drop = mutate(a, c)
    write(root, "docs/site/center/archmap.json", json.dumps(a, indent=1, sort_keys=True))
    write(root, "docs/site/center/c4-graph.json", json.dumps(c, indent=1, sort_keys=True))
    if drop and os.path.exists(os.path.join(cdir, "adoption.json")):
        os.remove(os.path.join(cdir, "adoption.json"))


def restore(root):
    git(root, "checkout", "--", "docs/site/center")


def older_map(a, c):
    """V_OLD — a map from before the repo-study pass: no tasks/mounts-siblings, no provider/TASK nodes; route_mounts (the sentinel) kept."""
    for k in ("app_middleware", "task_roots", "tasks", "fn_similarity", "unparseable"):
        a.pop(k, None)
    c["l2"]["thing"]["nodes"] = [n for n in c["l2"]["thing"]["nodes"] if n.get("kind") != "provider" and not n["id"].startswith("endpoint:TASK ")]
    c["stats"].pop("providers", None)
    return a, c, False


def config_only(a, c):
    """V_CFGONLY — bootstrap_center.sh's map: no adoption.json, l1 says config-only, no file_census, no schemas, no web arm, mounts clean."""
    a.pop("file_census", None)
    for ent in a["entities"].values():
        ent["schemas"] = []
    a["route_mounts"] = {"mounted": 1, "routers": 1, "scanned": 1, "unresolved": []}
    for n in c["l1"]["nodes"]:
        n["status"] = "config-only"
    c["stats"]["web"] = {"present": False, "reason": "no frontend"}
    return a, c, True


def fake_graft(T: str) -> str:
    d = os.path.join(T, "bin")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "graft")
    with open(p, "w") as f:
        f.write('''#!/usr/bin/env bash
# fake graft: `graft callers <sym> . --json --no-refresh`
sym="$2"
case "$sym" in
  thing) cat <<'JSON'
{"query":"thing","matches":[{"symbol":{"id":"apps/api/services/thing.py#thing","name":"thing","kind":"function","path":"apps/api/services/thing.py","span":"L4-L5"},
 "hits":[{"id":"apps/api/other.py#Caller.run","relation":"calls","depth":1,"name":"run","kind":"function","path":"apps/api/other.py","span":"L5-L6"}]}],"saved":{"files":1,"baselineChars":10}}
JSON
  ;;
  *) echo '{"query":"'"$sym"'","matches":[]}' ;;
esac
''')
    os.chmod(p, 0o755)
    return d


def spawn(root, T, env_extra=None, cwd=None, graft_dir=None):
    env = {"PATH": ((graft_dir + ":") if graft_dir else "") + os.environ.get("PATH", ""), "GABE_SKILLS_DIR": os.environ["GABE_SKILLS_DIR"]}
    if env_extra:
        env.update(env_extra)
    return Client(SERVER, root, env=env, cwd=cwd or T)


def call_json(c, name, args):
    text, is_err, raw = c.call(name, args)
    return parse_text(text), is_err, text, raw


def live_lines(root):
    p = os.path.join(root, ".kdbp", "map-deltas.jsonl")
    return open(p).read().splitlines() if os.path.exists(p) else []


def main() -> int:
    T = tempfile.mkdtemp(prefix="gabe-map-")
    try:
        run(T)
        part_b_tail(os.path.join(T, "proj"), T, os.path.join(T, "bin"))
    finally:
        shutil.rmtree(T, ignore_errors=True)
    print("gabe-map battery: %d passed, %d failed" % (PASS, FAIL))
    return 0 if FAIL == 0 else 1


def run(T):
    root = make_repo(T)
    gdir = fake_graft(T)
    os.makedirs(os.path.join(root, "graft", ".graph"), exist_ok=True)
    write(root, "graft/.graph/wiring.json", '{"meta":{},"nodes":[],"edges":[]}')

    # ── wire laws ──────────────────────────────────────────────────────────────
    c = spawn(root, T, graft_dir=gdir)
    r = c.request("server/discover", {"_meta": {}}, id_="server-discover-probe-1")           # auto-negotiation probe FIRST
    ok(r is not None and r.get("error", {}).get("code") == -32601 and r.get("id") == "server-discover-probe-1",
       "pre-initialize unknown method → -32601 with the STRING id echoed", r)
    r = c.request("tools/list")
    ok(r is not None and r.get("error", {}).get("code") == -32602, "tools/list before initialize → -32602", r)
    r = c.request("ping")
    ok(r is not None and r.get("result") == {}, "ping before initialize → {}", r)
    init = c.initialize("2025-11-25")
    res = (init or {}).get("result") or {}
    ok(res.get("protocolVersion") == "2025-11-25", "initialize echoes a supported version", init)
    ok((res.get("serverInfo") or {}).get("name") == "gabe-map", "serverInfo.name is gabe-map", res.get("serverInfo"))
    ok("mcp__gabe-map__who_calls" in (res.get("instructions") or ""), "instructions route to the full tool ids", (res.get("instructions") or "")[:80])
    ok(res.get("capabilities") == {"tools": {}}, "declares only tools", res.get("capabilities"))
    ok(any(m.get("method") == "roots/list" for m in c.server_requests), "server asked for roots after initialized", c.server_requests)
    tools = c.tools()
    names = sorted(t["name"] for t in tools)
    V1 = {"map_status", "entity_context", "touches", "who_calls", "entity_shape", "cases_for", "owner_of"}
    W2 = {"find", "outline", "center_overview", "blast_radius", "map_census", "map_diff", "center_status", "review_drift"}
    W3 = {"trace", "gates"}
    ok(set(names) == V1 | W2 | W3 and len(names) == 17, "v1 seven + wave-2 eight + wave-3 two tools listed (17)", names)
    ins = res.get("instructions") or ""
    ok(all(x in ins for x in ("mcp__gabe-map__gates", "mcp__gabe-map__trace", '"TASK <name>", stream=true, kind=provider', "where the map is PARTIAL", "A trace hop marked `inferred` is graft's guess")) and "orphan" not in ins,
       "F17: the instructions route gates · trace · TASK/stream/provider · map PARTIAL, the floor law names the inferred hop, and no line says orphan (R10)", ins[-600:])
    ok(all(t["inputSchema"].get("type") == "object" for t in tools), "every inputSchema is an object schema")
    ok(all("annotations" in t and "readOnlyHint" in t["annotations"] for t in tools), "every tool carries annotations")
    ok(next(t for t in tools if t["name"] == "who_calls")["annotations"]["readOnlyHint"] is False, "who_calls is not readOnly (the emit)")
    ok(all(len(t.get("description", "")) <= 200 for t in tools), "descriptions ≤ 200 chars", [(t["name"], len(t["description"])) for t in tools if len(t["description"]) > 200])
    r = c.request("nonsense/method")
    ok(r is not None and r.get("error", {}).get("code") == -32601, "unknown method → -32601", r)
    text, is_err, raw = c.call("no_such_tool", {})
    ok(is_err and (raw or {}).get("error", {}).get("code") == -32602, "unknown tool → -32602", raw)
    c.send_raw("this is not json")                                                  # garbage line → skipped
    c.send({"jsonrpc": "2.0", "method": "notifications/whatever"})                  # unknown notification → silence
    r = c.request("ping")
    ok(r is not None and r.get("result") == {}, "server survives a garbage line and an unknown notification", r)
    d, is_err, text, raw = call_json(c, "touches", {})
    ok(is_err and d and "stop" in d, "missing required argument → isError result with a stop message (not a JSON-RPC error)", text[:120])
    ok("structuredContent" not in ((raw or {}).get("result") or {}), "results carry NO structuredContent (one channel)")
    ok(text.startswith("gabe-map · touches"), "result text starts with the header line", text[:40])
    c.close()

    c = spawn(root, T, graft_dir=gdir)
    init = c.initialize("1999-01-01")
    ok(((init or {}).get("result") or {}).get("protocolVersion") == "2025-11-25", "unsupported version → the server's latest", init)
    c.close()

    # ── root law: CLAUDE_PROJECT_DIR wins over a foreign cwd; toplevel from a subdir ──
    sub = os.path.join(root, "apps", "api")
    c = spawn(sub, T, graft_dir=gdir, cwd=T)
    c.initialize()
    d, is_err, text, _ = call_json(c, "map_status", {})
    ok(d and d.get("present") is True and d.get("root") == root and d.get("root_source") == "CLAUDE_PROJECT_DIR",
       "CLAUDE_PROJECT_DIR (a subdir) resolves to the git toplevel, cwd ignored", {k: d.get(k) for k in ("present", "root", "root_source")} if d else text)
    ok(d and d["counts"]["endpoints"] == 3 and d["counts"]["models"] == 2 and d["counts"]["fe_pieces"] == 2 and d["counts"]["tasks"] == 1 and d["counts"]["streams"] == 1
       and d["counts"]["providers"] == 1 and d["counts"]["app_middleware"] == 1 and d["counts"]["schemas"] == 1 and d["counts"]["schemas_rows"] == 3,
       "map_status counts (F5 FIRE: tasks · streams · providers · app_middleware · DISTINCT schemas 1 beside 3 rows)", d and d.get("counts"))
    h = d and d.get("map_health")
    ok(h and h["route_mounts"] == {"state": "present", "mounted": 1, "routers": 1, "unresolved": 1} and h["fn_similarity"]["mode"] == "blocked" and h["fn_similarity"]["sizable"] == 9
       and h["web"]["other_roots"] == ["mobile/src"] and h["web"]["unmatched"] == 2 and h["unparseable"] == {"state": "present", "count": 1} and h["schemas_zero"] is False,
       "F5 FIRE: map_health names the unresolved mount, the blocked twin pass (sizable over budget), the unscanned root, the unparseable file", h)
    ok(d and d["freshness"]["freshness"] == "fresh" and d["freshness"]["commits_since"] == 2, "docs-only commits after the regen read FRESH (base = regen commit)", d and d.get("freshness"))
    ok(d and d["graft"]["index_present"] and d["graft"]["match"] is False and "note" in d["graft"], "graft index hash mismatch is explained, never called stale", d and d.get("graft"))
    ok(d and d["file_census"] == {"claimed": 8, "unclaimed": 1}, "file_census summarized", d and d.get("file_census"))
    ok(d and isinstance(d.get("server_sha"), str) and len(d["server_sha"]) == 12, "server_sha present")
    # stale: edit a MAPPED file in the worktree (uncommitted) → stale
    write(root, "apps/api/other.py", open(os.path.join(root, "apps/api/other.py")).read() + "\n# touched\n")
    d, _, _, _ = call_json(c, "map_status", {})
    ok(d and d["freshness"]["freshness"] == "stale" and "apps/api/other.py" in d["freshness"]["mapped_files_changed"], "an uncommitted edit to a mapped file reads STALE (worktree-aware)", d and d.get("freshness"))
    git(root, "checkout", "--", "apps/api/other.py")
    # unknown head → tristate unknown
    a = json.load(open(os.path.join(root, "docs/site/center/archmap.json")))
    a["head"] = "deadbeef"
    write(root, "docs/site/center/archmap.json", json.dumps(a))
    d, _, _, _ = call_json(c, "map_status", {})
    ok(d and d["freshness"]["stale"] is None and d["freshness"]["freshness"] == "unknown", "head not in history → stale null / unknown", d and d.get("freshness"))
    git(root, "checkout", "--", "docs/site/center/archmap.json")
    c.close()

    # ── honest-empty ──────────────────────────────────────────────────────────
    nocenter = os.path.join(T, "plain"); os.makedirs(nocenter); sh(["git", "init", "-q", nocenter])
    c = spawn(nocenter, T)
    c.initialize()
    d, is_err, text, _ = call_json(c, "map_status", {})
    ok(d and d.get("present") is False and not is_err and "/gabe-cc-init" in d.get("hint", "") and "Grep" in d.get("hint", ""),
       "no center → present:false, isError:false, hint to Grep + cc-init", text[:200])
    d, is_err, _, _ = call_json(c, "touches", {"target": "Thing"})
    ok(d and d.get("present") is False and not is_err, "every tool answers honest-empty without a center", d)
    c.close()
    suite = os.path.join(T, "suite"); os.makedirs(os.path.join(suite, "docs", "center")); sh(["git", "init", "-q", suite])
    write(suite, "docs/center/suite-center.config.json", "{}")
    c = spawn(suite, T); c.initialize()
    d, _, _, _ = call_json(c, "map_status", {})
    ok(d and d.get("present") is False and "R8" in d.get("reason", "") and "hint" not in d, "suite-center repo → ruling R8, no cc-init hint", d)
    c.close()

    # ── tools on the fixture ──────────────────────────────────────────────────
    c = spawn(root, T, graft_dir=gdir)
    c.initialize()
    # entity_context
    d, _, _, _ = call_json(c, "entity_context", {})
    ok(d and len(d.get("entities", [])) == 2 and any(e["slug"] == "other" and e.get("note") for e in d["entities"]), "entity list = adoption ∪ archmap, unregistered flagged", d and d.get("entities"))
    d, _, _, _ = call_json(c, "entity_context", {"slug": "thing"})
    ok(d and d["entity"]["code"]["counts"]["endpoints"] == 3 and d["entity"]["code"]["endpoints"] == ["GET /things/{item_id} ⚡", "DELETE /things/{item_id}", "POST /login/access-token"]
       and d["entity"]["code"]["counts"]["streams"] == 1 and d["entity"]["code"]["counts"]["tasks"] == 1, "brief carries counts + endpoint names (⚡ marks the stream; F8 streams/tasks counts)", d and d.get("entity", {}).get("code"))
    ok(d and d["c4"]["l2_node_kinds"] == {"endpoint": 2, "task": 1, "provider": 1, "model": 1, "schema": 1, "web": 1} and d["c4"]["providers"] == ["litellm"] and d["c4"]["fe_home"]["homing"] == "config",
       "F3/F8: the l2 histogram splits task from endpoint, providers are NAMED, the fe home says which witness homed it", d and d.get("c4"))
    df, _, _, _ = call_json(c, "entity_context", {"slug": "thing", "detail": "full"})
    ok(df and df["entity"]["code"]["endpoints"][0]["stream"] is True and df["entity"]["code"]["endpoints"][0]["gates"] == ["auth(Scope.READ)", "require_auth_scope(Scope.WRITE)"] and df["entity"]["code"]["endpoints"][2]["gates"] == [],
       "F8 FIRE/SILENT: full detail carries stream + the gate names per endpoint (get_db is not a gate)", df and df["entity"]["code"].get("endpoints"))
    ok(d and d["c4"]["l1_edges"] and d["c4"]["fe_home"]["id"] == "fe·thing" and d["coverage"]["total"] == 2, "brief adds c4 l1 edges, fe home, coverage", d and d.get("c4"))
    ok(d and d["entity"]["relations"] == {"related_entities": [], "unresolved_tables": [], "fk_out": 0}, "brief collapses relations to counts", d and d["entity"].get("relations"))
    d, _, _, _ = call_json(c, "entity_context", {"slug": "thing", "detail": "raw"})
    ref = sh([sys.executable, os.path.join(os.environ["GABE_SKILLS_DIR"], "gabe-cc-entity", "scripts", "entity-context.py"), "thing",
              "--center", os.path.join(root, "docs/site/center"), "--json"])
    ok(d and d.get("entity") == json.loads(ref.stdout), "raw detail is byte-parity with entity-context.py --json")
    d, is_err, _, _ = call_json(c, "entity_context", {"slug": "nope"})
    ok(is_err and d and "not found" in d.get("stop", "") and "thing" in d.get("stop", ""), "unknown slug → the reader's STOP text with the registered list", d)
    d, is_err, _, _ = call_json(c, "entity_context", {"slug": "thing", "detail": "huge"})
    ok(is_err and d and "detail must be" in d.get("stop", ""), "bad detail → stop", d)
    # touches: model with fk_in + r/w fns + cross-entity edge + cases split
    d, _, _, _ = call_json(c, "touches", {"target": "Thing"})
    ok(d and d["kind"] == "model" and d["fk_in_models"] == [{"model": "Widget", "col": "thing_id", "entity": "other"}], "model: fk_in computed from every model's fks", d and d.get("fk_in_models"))
    ok(d and {(f["fn"], f["rw"]) for f in d["functions_rw"]} == {("apps/api/services/thing.py::thing", "r"), ("apps/api/api/things.py::get_thing", "r"), ("apps/api/tasks.py::sweep_things_task", "w")}, "model: functions r/w from access.ops (the task fn writes)", d and d.get("functions_rw"))
    ok(d and "reads_from" in d["endpoint_edges"] and "fk" in d["endpoint_edges"], "model: l2 edges ∪ cross_edges (kind-less FK row → fk)", d and d.get("endpoint_edges"))
    ok(d and d["tests"]["cases"][0]["cid"] == "C8", "model: cases from by_model", d and d.get("tests"))
    # touches: endpoint normalization + file-state rows split
    d, _, _, _ = call_json(c, "touches", {"target": "get /api/v1/things/${id}"})
    ok(d and d["matched"] and d["entity"] == "thing" and d["endpoint"]["handler"] == "apps/api/api/things.py::get_thing", "endpoint matched through normalization (/api/vN, ${x})", d)
    ok(d and d["behind"]["fns"] == 2 and d["screens_in"] and d["tests"]["cases"] == [{"cid": "C8", "name": "test_get_thing_C8", "state": "pass", "corpus": "api", "tfile": "apps/api/tests/test_things_api.py"}]
       and d["tests"]["covered_by_test_files"][0]["tfile"] == "apps/web/e2e/things.spec.ts", "endpoint: behind, bridge in-edge, state=file rows split off", d and d.get("tests"))
    ok(d and d["endpoint"]["stream"] is True and d["app_middleware"][0]["cls"] == "RateLimiterMiddleware" and "EVERY request" in d["app_middleware_note"],
       "F1 FIRE: the endpoint answer carries stream + the ASGI middleware that also applies", d and {k: d.get(k) for k in ("app_middleware", "app_middleware_note")})
    ok(d and d["web_unmatched_fetches"] == [{"m": "GET", "p": "/api/v1/things/{id}", "from": "web:apps/web/src/other"}],
       "the unmatched-fetch join reads the m/p keys the emitter writes (was path/method — never matched on a real map)", d and d.get("web_unmatched_fetches"))
    d, _, _, _ = call_json(c, "touches", {"target": "POST /login/access-token"})
    ok(d and d["matched"] and d["endpoint"]["stream"] is False, "F1 SILENT: an endpoint without the key reads stream False", d and d.get("endpoint"))
    ok(d and "touches_x" not in json.dumps(d), "touches_x is never surfaced")
    d, _, _, _ = call_json(c, "touches", {"target": "POST /things/1"})
    ok(d and d.get("matched") is False and "normalization" in d.get("reason", ""), "unmatched endpoint is named, not empty", d)
    # touches: file with two owners + census; unclaimed file
    d, _, _, _ = call_json(c, "touches", {"target": "apps/api/services/shared.py"})
    ok(d and {o["entity"] for o in d["owners"]} == {"thing", "other"}, "file: BOTH owners returned", d and d.get("owners"))
    d, _, _, _ = call_json(c, "touches", {"target": "apps/api/integrations/x.py"})
    ok(d and d["owned"] is False and d["census"]["claimed"] is False and d["census"]["reason"].startswith("unparseable:"), "file: unclaimed census row surfaces — F10: the unparseable reason wins", d and d.get("census"))
    # touches: bare function ambiguous / unique / qualified / define / case / entity
    d, _, _, _ = call_json(c, "touches", {"target": "run"})
    ok(d and len(d.get("ambiguous", [])) == 2, "bare name with 2 keys → ambiguous, never a silent pick", d)
    d, _, _, _ = call_json(c, "touches", {"target": "thing"})
    ok(d and d.get("kind") == "entity" and d.get("entity", {}).get("slug") == "thing", "bare 'thing' resolves to the ENTITY (slug wins over the function by rule order)", d and d.get("kind"))
    d, _, _, _ = call_json(c, "touches", {"target": "apps/api/services/thing.py#thing"})
    ok(d and d["function"]["access_ops"][0]["model"] == "Thing" and d["function"]["endpoints_reaching"]["found"] == ["endpoint:GET /things/{item_id}"]
       and "floor" in d["function"]["endpoints_reaching"], "qualified fn via #: access ops + endpoints reaching with the FLOOR label", d and d.get("function"))
    d, _, _, _ = call_json(c, "touches", {"target": "Caller"})
    ok(d and d["kind"] == "define" and d["methods"] == ["apps/api/other.py::Caller.run"], "define branch: a non-model class → methods", d)
    # F2: the qualified join — Svc.search reaches the endpoint (behind.names carries "Svc.search"); Other.search must NOT through the bare `search`
    d, _, _, _ = call_json(c, "touches", {"target": "apps/api/services/thing.py::Svc.search"})
    ok(d and d["function"]["endpoints_reaching"]["found"] == ["endpoint:GET /things/{item_id}"] and "qualified" in d["function"]["endpoints_reaching"]["floor"],
       "F2 FIRE: a method joins behind.names on Class.method", d and d.get("function", {}).get("endpoints_reaching"))
    d, _, _, _ = call_json(c, "touches", {"target": "apps/api/services/other_svc.py::Other.search"})
    ok(d and d["function"]["endpoints_reaching"]["found"] == [], "F2 SILENT: the bare `search` no longer bridges Other.search to Svc.search's endpoint", d and d.get("function", {}).get("endpoints_reaching"))
    d, _, _, _ = call_json(c, "touches", {"target": "apps/api/deps.py::auth"})
    ok(d and d["function"].get("reason") == "not in function_insight", "a gate fn outside function_insight still answers honestly", d and d.get("function"))
    # F3: TASK roots addressable — by 'TASK <name>', by the registered name, by the fn name; honest-empty by name
    d, _, _, _ = call_json(c, "touches", {"target": "TASK sweep_things"})
    ok(d and d["kind"] == "task" and d["matched"] and d["entity"] == "thing" and d["task"]["fn"] == "sweep_things_task" and d["dispatched_by"] == [{"from": "apps/api/api/things.py#get_thing", "conf": "extracted"}]
       and d["behind"]["fns"] == 1 and d["stream"] is False and "worker task" in d["app_middleware_note"],
       "F3 FIRE: touches('TASK <name>') → the task, its dispatchers (levels.json), behind, the no-HTTP-gates note", d and {k: d.get(k) for k in ("task", "dispatched_by", "behind")})
    d, _, _, _ = call_json(c, "touches", {"target": "sweep_things"})
    ok(d and d["kind"] == "task" and d["matched"], "F3: the REGISTERED name resolves to the task (P1 detect_kind)", d and d.get("kind"))
    d, _, _, _ = call_json(c, "touches", {"target": "sweep_things_task"})
    ok(d and d["kind"] == "function_bare" and d["function"]["access_ops"][0]["rw"] == "w" and d["function"]["task_root"]["name"] == "sweep_things" and "TASK sweep_things" in d["function"]["task_root"]["see"],
       "review F1: a bare task-fn name that function_insight KNOWS answers as the function (access ops kept) and cross-links its task root", d and {k: (d.get("function") or {}).get(k) for k in ("key", "task_root")})
    d, _, _, _ = call_json(c, "touches", {"target": "apps/api/tasks.py::sweep_things_task"})
    ok(d and d["kind"] == "function" and d["function"]["task_root"]["name"] == "sweep_things", "review F1: the qualified task fn carries the same cross-link", d and (d.get("function") or {}).get("task_root"))
    d, _, _, _ = call_json(c, "touches", {"target": "TASK nope"})
    ok(d and d["kind"] == "task" and d["matched"] is False and "task_roots" in d["reason"], "F3 SILENT: an unknown task names task_roots, never a crash", d)
    d, _, _, _ = call_json(c, "cases_for", {"target": "TASK sweep_things"})
    ok(d and d["kind"] == "task" and d["cases"] == [] and "task roots are not entity endpoints" in d.get("reason", ""), "F3: cases_for('TASK x') is honest-empty by name", d and d.get("reason"))
    # F9: a screen/hook file → its pieces (hrole · homing) and the endpoints it fetches
    d, _, _, _ = call_json(c, "touches", {"target": "apps/web/src/things.ts"})
    ok(d and d["fe"]["calls"] == [{"endpoint": "endpoint:GET /things/{item_id}", "kind": "bridge"}] and d["fe"]["pieces"][0]["hrole"] == "fetcher" and d["fe"]["pieces"][0]["homed_by"] == "config",
       "F9 FIRE: the file branch carries the screen→endpoint leg + the piece's role and homing", d and d.get("fe"))
    d, _, _, _ = call_json(c, "touches", {"target": "apps/api/services/thing.py"})
    ok(d and "fe" not in d, "F9 SILENT: a backend file carries no fe block", d and sorted(d.keys()))
    d, _, _, _ = call_json(c, "touches", {"target": "C7"})
    ok(d and d["kind"] == "case" and d["home"] == "apps/api/tests/test_thing.py", "case id → home test file", d)
    d, _, _, _ = call_json(c, "touches", {"target": "nothing_here"})
    ok(d and d.get("found") is False and "grep" in d.get("reason", ""), "unknown name → found:false naming the grep floor", d)
    # cases_for
    d, _, _, _ = call_json(c, "cases_for", {"target": "thing"})
    ok(d and d.get("via") in ("by_function", "case_home") or d.get("kind") == "entity", "cases_for resolves the target", d and {k: d.get(k) for k in ("kind", "via")})
    d, _, _, _ = call_json(c, "cases_for", {"target": "apps/api/api/things.py::get_thing"})
    ok(d and [x["cid"] for x in d["cases"]] == ["C8"] and d["covered_by_test_files"][0]["n"] == 3, "cases_for endpoint handler: cases vs file rows split", d)
    ok(d and d["max_cid_in_map"] == 8 and d["corpus"]["next_cid_floor"] is None or d["corpus"].get("max_cid_seen") is None, "corpus grep runs (fixture has no C-ids in test names → floor None)", d and d.get("corpus"))
    # owner_of
    d, _, _, _ = call_json(c, "owner_of", {"paths": ["apps/api/services/shared.py", "apps/api/integrations/x.py", "apps/api/"]})
    r0, r1, r2 = d["results"]
    ok({o["entity"] for o in r0["owners"]} == {"thing", "other"} and set(r0["config_glob_owners"]) == {"thing"}, "owner_of: map owners (2) + config-glob owners", r0)
    ok(r1["owned"] is False and r1["census"]["claimed"] is False and r1["census"]["reason"].startswith("unparseable:") and r1["note"], "owner_of: unowned file names the blind spot — F10 FIRE: and WHY (unparseable)", r1)
    ok(r0["census"] == {"claimed": True}, "F10 SILENT: a mapped, parseable file's census is unchanged", r0["census"])
    ok(r2["kind"] == "dir" and r2["owners"].get("thing") and r2["unclaimed_in_census"] == ["apps/api/integrations/x.py"], "owner_of: directory aggregate", r2)
    # entity_shape
    d, _, _, _ = call_json(c, "entity_shape", {"domain": "things"})
    ok(d and d.get("one_line") and d["domain"]["owners"] == {"thing": 2}, "entity_shape: domain owner lookup", d and d.get("domain"))
    ok(d and d["mounts_unresolved"] == 1 and "route mount(s) unresolved" in d["one_line"], "F13 FIRE: the mounts caveat rides one_line", d and d.get("one_line"))

    # ── wave 2: the graft equivalents + map lifecycle ─────────────────────────
    d, _, _, _ = call_json(c, "find", {"query": "thing"})
    ok(d and d["hits"] and d["hits"][0]["kind"] == "entity" and d["hits"][0]["name"] == "thing" and d["total"] >= 4, "find: exact entity ranks first, total counts every kind", d and {k: d.get(k) for k in ("total",)} | {"top": (d or {}).get("hits", [])[:3]})
    d, _, _, _ = call_json(c, "find", {"query": "thing", "kind": "model", "limit": 1})
    ok(d and [h["kind"] for h in d["hits"]] == ["model"] and d["hits"][0]["name"] == "Thing", "find: kind filter + limit", d and d.get("hits"))
    # F4: ranking · dedupe · generated-client noise · providers · tasks · stream filter
    d, _, _, _ = call_json(c, "find", {"query": "login"})
    ok(d and [h["name"] for h in d["hits"]][:3] == ["POST /login/access-token", "loginBanner", "loginLoginAccessTokenData"] and [h for h in d["hits"] if h["name"] == "loginLoginAccessTokenData"] == [{"kind": "fe", "name": "loginLoginAccessTokenData", "entity": None, "file": "apps/web/client/types.gen.ts", "piece_kind": "fe-type"}],
       "F4 FIRE: the +25 kind bonus alone puts the endpoint (substring) over a plain prefix define; the −30 alone puts the generated twin below it; the define twin folds into ONE fe hit", d and d.get("hits"))
    d, _, _, _ = call_json(c, "find", {"query": "ThingOut", "kind": "schema"})
    ok(d and d["total"] == 1 and d["hits"][0]["entities"] == ["other", "thing"], "F4 FIRE: a schema two entities consume (and one lists twice) is ONE hit naming both, deduped + sorted", d and d.get("hits"))
    d, _, _, _ = call_json(c, "find", {"query": "litellm"})
    ok(d and d["hits"][0]["kind"] == "provider" and d["hits"][0]["pclass"] == "llm" and d["hits"][0]["entity"] == "thing", "F4 FIRE: a provider is findable (c4 provider node, once per name)", d and d.get("hits"))
    d, _, _, _ = call_json(c, "find", {"query": "sweep"})
    ok(d and d["hits"][0]["kind"] == "task" and d["hits"][0]["name"] == "sweep_things" and d["hits"][0]["id"] == "endpoint:TASK sweep_things", "F3 FIRE: a task is findable by its registered name", d and d.get("hits"))
    d, _, _, _ = call_json(c, "find", {"query": "t /", "kind": "endpoint", "stream": True})
    ok(d and d["total"] == 1 and d["hits"][0]["stream"] is True and "stream=true" in d["filter"], "F4 FIRE: stream=true keeps only the streaming endpoints (and every endpoint hit carries stream)", d and d.get("hits"))
    d, _, _, _ = call_json(c, "find", {"query": "t /", "kind": "endpoint"})
    ok(d and d["total"] == 2, "F4 SILENT: without the filter both endpoints hit", d and d.get("total"))
    d, is_err, _, _ = call_json(c, "find", {"query": "x"})
    ok(is_err and "2 characters" in (d or {}).get("stop", ""), "find: a 1-char query is a stop", d)
    d, _, _, _ = call_json(c, "outline", {"file": "apps/api/other.py"})
    ok(d and d["signatures"].startswith("unavailable") and {x["name"] for x in d["definitions"]} == {"Caller.run", "Helper.run"} and d["owners"], "outline without a graft index: definitions from function_insight, signatures named unavailable", d and {k: d.get(k) for k in ("signatures", "definitions")})
    write(root, "graft/.graph/wiring.json", json.dumps({"meta": {}, "nodes": [{"id": "apps/api/other.py#Caller.run", "name": "Caller.run", "kind": "method", "path": "apps/api/other.py", "span": "L5-L6", "signature": "def run(self) -> int", "exported": True}], "edges": []}))
    d, _, _, _ = call_json(c, "outline", {"file": "apps/api/other.py"})
    ok(d and d["signatures"].startswith("graft index") and d["definitions"][0]["signature"] == "def run(self) -> int" and d["definitions"][0]["span"] == "L5-L6", "outline with a graft index: span + signature from wiring.json", d and d.get("definitions"))
    d, _, _, _ = call_json(c, "center_overview", {})
    ok(d and len(d["entities"]) == 2 and d["entities"][1]["entity"] == "thing" and d["entities"][1]["coverage"] == "1/2" and d["census_gaps"]["files_unclaimed"] == 1 and d["unregistered"] == ["other"], "center_overview: entities with coverage, census gaps, unregistered", d and {k: d.get(k) for k in ("census_gaps", "unregistered")})
    ok(d and d["web"]["extractor"] == "fetch" and d["web"]["unmatched"] == 2 and d["web"]["other_roots"] == ["mobile/src"] and d["arms"]["providers"] == ["litellm"] and d["arms"]["fe"] == {"present": True, "homing": "config"}
       and d["arms"]["app_middleware"] == 1 and d["arms"]["gate_endpoints"] == 2 and d["arms"]["tasks"] == 1 and d["map_health"]["route_mounts"]["unresolved"] == 1 and d["census_gaps"]["routes_unclaimed"] is None and "route_census" in d["census_absent"],
       "F7 FIRE: the web arm (a LIST unmatched counts), named providers, fe homing, middleware/gates/tasks, map_health; an absent census block is None + named", d and {k: d.get(k) for k in ("web", "arms", "census_absent")})
    d, _, _, _ = call_json(c, "blast_radius", {"files": ["apps/api/services/thing.py"]})
    ok(d and d["touched_entities"] == {"thing": 1} and "endpoint:GET /things/{item_id}" in d["endpoints_reached"] and d["reading"] == "contained" and "floor" in d, "blast_radius: owners + endpoints via behind.names (floor) + reading", d and {k: d.get(k) for k in ("touched_entities", "endpoints_reached", "reading")})
    ok(d and d["tasks_dispatched"] == [] and d["tasks_defined"] == [], "F15 SILENT: a change that dispatches nothing lists no task", d and {k: d.get(k) for k in ("tasks_dispatched", "tasks_defined")})
    d, _, _, _ = call_json(c, "blast_radius", {"files": ["apps/api/api/things.py"]})
    ok(d and d["tasks_dispatched"] == [{"task": "endpoint:TASK sweep_things", "from": "apps/api/api/things.py#get_thing", "conf": "extracted"}] and d["reading"] == "cross-process",
       "F15 FIRE: the dispatch arm — a changed handler that enqueues a task lists it (levels.json, conf) and the reading says cross-process", d and {k: d.get(k) for k in ("tasks_dispatched", "reading")})
    d, _, _, _ = call_json(c, "blast_radius", {"files": ["apps/api/tasks.py"]})
    ok(d and d["tasks_defined"] == ["endpoint:TASK sweep_things"] and d["reading"] == "cross-process", "F15 FIRE: a changed file that DEFINES a task root lists it as an entry point", d and d.get("tasks_defined"))
    d, _, _, _ = call_json(c, "blast_radius", {"files": ["apps/api/integrations/x.py"]})
    ok(d and d["reading"] == "unmapped" and d["unowned_files"] == ["apps/api/integrations/x.py"], "blast_radius: unmapped files are named, reading = unmapped", d)
    d, _, _, _ = call_json(c, "map_census", {})
    ok(d and d["census"]["file"]["unclaimed"][0]["file"] == "apps/api/integrations/x.py" and "reason" in d["census"]["route"], "map_census: unclaimed file listed, absent route census named", d and d.get("census"))
    cs = d and d["census"]
    ok(cs and cs["mounts"]["unresolved"][0]["why"].startswith("non-literal prefix") and cs["mounts"]["state"] == "present" and cs["twins"]["mode"] == "blocked" and "9 sizable function(s) over the 5 budget" in cs["twins"]["text"]
       and cs["web"]["other_roots"] == ["mobile/src"] and cs["web"]["unmatched"] == 2 and cs["web"]["unmatched_named"] == ["GET /x", "GET /api/v1/things/{id}"] and cs["unparseable"]["count"] == 1 and cs["unparseable"]["rows"][0]["why"] == "unparseable: bad"
       and cs["schema"]["empty_arm"] is False,
       "F6 FIRE: the four new sections — mounts · twins (sizable over budget, never 'pairs over a budget') · web roots + unmatched named · unparseable rows", cs and {k: cs.get(k) for k in ("mounts", "twins", "web", "unparseable")})
    d, _, _, _ = call_json(c, "map_census", {"kind": "twins"})
    ok(d and list(d["census"].keys()) == ["twins"] and d["census"]["twins"]["state"] == "present", "F6: one section only", d and d.get("census"))
    # Part C: the membership evidence as fields + a census section (levels.json homing, read lazily)
    d, _, _, _ = call_json(c, "map_census", {"kind": "homing"})
    hm = d and d["census"]["homing"]
    ok(hm and hm["state"] == "present" and hm["move"] == 1 and hm["shared"] == 1 and hm["move_named"][0]["to"] == "other" and hm["shared_named"] == ["apps/api/other.py#Helper.run"] and "nothing re-homed" in hm["text"],
       "Part C FIRE: map_census(homing) — counts, the move candidates + shared aspects named, evidence only", hm)
    d, _, _, _ = call_json(c, "touches", {"target": "apps/api/services/thing.py#thing"})
    ok(d and d["function"]["home_evidence"]["verdict"] == "move" and d["function"]["home_evidence"]["to"] == "other" and d["function"]["home_evidence"]["users"] == {"other": 3, "thing": 1} and "nothing re-homed" in d["function"]["home_evidence"]["note"],
       "Part C FIRE: touches(function) carries the evidence record when the witnesses disagree", d and d["function"].get("home_evidence"))
    d, _, _, _ = call_json(c, "touches", {"target": "GET /things/{item_id}"})
    ok(d and "home_evidence" not in d, "Part C SILENT: an agreeing endpoint carries no evidence field (the answer's shape is unchanged)", d and sorted(d.keys()))
    d, _, _, _ = call_json(c, "touches", {"target": "apps/api/other.py::Helper.run"})
    ok(d and d["function"]["home_evidence"]["verdict"] == "shared", "Part C: a shared aspect says so on the function", d and d["function"].get("home_evidence"))
    d, is_err, _, _ = call_json(c, "map_census", {"kind": "bogus"})
    ok(is_err, "map_census: bad kind is a stop")
    # ── wave 3: trace + gates (N1/N2) ──
    d, _, _, _ = call_json(c, "trace", {"start": "GET /things/{item_id}"})
    tos = d and [h["to"] for h in d["hops"]]
    ok(d and d["from"]["kind"] == "endpoint" and d["from"]["gates"] == ["auth(Scope.READ)", "require_auth_scope(Scope.WRITE)"] and d["from"]["stream"] is True and "provider:redis" in tos and "apps/api/tasks.py#sweep_things_task" in tos
       and [h for h in d["hops"] if h["rel"] == "dispatches"][0]["conf"] == "extracted" and [h for h in d["hops"] if h["rel"] == "dispatches"][0]["task"] == "endpoint:TASK sweep_things"
       and [h for h in d["hops"] if h["rel"] == "calls"][0]["models"] == ["Thing r"] and d["summary"].startswith("hops 3 of 3 reachable") and d["app_middleware"] == ["RateLimiterMiddleware"] and d["behind_contrast"]["fns"] == 2
       and any(l.startswith("  calls (extracted)  apps/api/services/thing.py#thing") for l in d["tree"]) and any(l.startswith("    reaches (inferred)  provider:redis") for l in d["tree"]),
       "N1 FIRE: trace from an endpoint — gates + stream in the header, the call hop with its models, the provider hop, the dispatch hop → TASK, the FLOOR summary, the indented tree", d and {k: d.get(k) for k in ("from", "summary", "tree")})
    d, _, _, _ = call_json(c, "trace", {"start": "TASK sweep_things"})
    ok(d and d["from"]["kind"] == "task" and d["from"]["label"] == "TASK sweep_things" and d["tree"][0].startswith("apps/api/tasks.py#sweep_things_task") and d.get("reason", "").startswith("no calls/depends/dispatches/reaches edge(s) leave")
       and d["app_middleware"] == [] and "worker task runs outside it" in d["app_middleware_note"],
       "N1: a trace can start at a TASK root; zero out-edges is named, never empty; no ASGI list on a worker (review)", d and {k: d.get(k) for k in ("from", "reason", "app_middleware")})
    d, _, _, _ = call_json(c, "trace", {"start": "GET /things/{item_id}", "depth": 1})
    ok(d and "provider:redis" not in [h["to"] for h in d["hops"]] and d["summary"].startswith("hops 2 of 3 reachable"), "N1: depth=1 stops before the reaches hop and the summary names what it did not walk", d and d.get("summary"))
    d, _, _, _ = call_json(c, "trace", {"start": "apps/api/services/thing.py#thing", "rels": ["calls"]})
    ok(d and d["hops"] == [] and d["reason"].startswith("no calls edge(s) leave apps/api/services/thing.py#thing"), "N1 SILENT: rels=[calls] on a function with only a reaches edge names the absence", d and d.get("reason"))
    d, _, _, _ = call_json(c, "trace", {"start": "search"})
    ok(d and "ambiguous" in d and "pass file::name" in d["reason"], "N1: an ambiguous bare start lists the keys", d and d.get("reason"))
    d, _, _, _ = call_json(c, "gates", {"gate": "auth"})
    ok(d and [e["endpoint"] for e in d["endpoints"]] == ["GET /things/{item_id}", "DELETE /things/{item_id}"] and d["by_argument"] == {"Scope.READ": 2} and [e["arg"] for e in d["endpoints"]] == ["Scope.READ", "Scope.READ, allow_anonymous=True"]
       and d["fn"] == ["apps/api/deps.py::auth"] and d["app_middleware"][0]["cls"] == "RateLimiterMiddleware" and d["endpoints_total"] == 3 and d["endpoints_matched"] == 2 and d["gated_total"] == 2
       and d["ungated"] == {"count": 1, "sample": ["POST /login/access-token"]} and d["cross_check"] == "stats say 2 gated endpoint(s), this walk counts 2" and d["non_gate_deps"] == []
       and all(e["how"] == "callee" for e in d["endpoints"]) and d["also_named_in"] == {"require_auth_scope": 1} and "ambiguous_gate" not in d,
       "N2 FIRE: gates(auth) — an EXACT callee hit is the gate (2 endpoints, by_argument keyed on the head: Scope.READ ×2 with the full arg per row), total vs matched apart, the substring twin require_auth_scope only NAMED", d and {k: d.get(k) for k in ("endpoints", "by_argument", "also_named_in", "endpoints_total", "endpoints_matched")})
    d, _, _, _ = call_json(c, "gates", {"gate": "Scope.READ"})
    ok(d and [e["endpoint"] for e in d["endpoints"]] == ["GET /things/{item_id}", "DELETE /things/{item_id}"] and all(e["how"] == "argument" for e in d["endpoints"]) and "ambiguous_gate" not in d,
       "N2: a gate is found by its ARGUMENT string (one callee → not ambiguous)", d and d.get("endpoints"))
    d, _, _, _ = call_json(c, "gates", {"gate": "Scope"})
    ok(d and d["callees"] == ["auth", "require_auth_scope"] and d["ambiguous_gate"].startswith("'Scope' matched 2 distinct dependencies (auth · require_auth_scope)") and d["endpoints_matched"] == 3,
       "N2 FIRE (review): a substring that lands on two callees says ambiguous_gate and names them", d and {k: d.get(k) for k in ("callees", "ambiguous_gate")})
    d, _, _, _ = call_json(c, "gates", {"gate": "get_db"})
    ok(d and d["endpoints"] == [] and d["non_gate_deps"][0]["endpoint"] == "GET /things/{item_id}" and "non-gate dependency" in d["reason"], "N2 SILENT: a dep that is not a gate is listed apart, never reported as one", d and {k: d.get(k) for k in ("non_gate_deps", "reason")})
    d, _, _, _ = call_json(c, "gates", {"gate": "nope"})
    ok(d and d["endpoints"] == [] and "no endpoint names 'nope'" in d["reason"] and d["app_middleware"][0]["cls"] == "RateLimiterMiddleware", "N2 SILENT: an unknown gate names the reason and still prints the app-scope list", d and d.get("reason"))
    d, _, _, _ = call_json(c, "gates", {})
    ok(d and d["gates"] == [{"callee": "auth", "fn": "apps/api/deps.py::auth", "endpoints": 2, "via": ["param-dep"], "args": 2},
                            {"callee": "require_auth_scope", "fn": "apps/api/deps.py::require_auth_scope", "endpoints": 1, "via": ["param-dep"], "args": 1}]
       and d["gated_total"] == 2 and d["endpoints_total"] == 3 and "1 task root(s) run outside" in d["tasks"],
       "N2: the census — every gate callee with its endpoint count (endpoints_total keeps the map's count); tasks named as outside the gates", d and {k: d.get(k) for k in ("gates", "tasks", "endpoints_total")})
    # ── the OLDER-MAP variant: absence semantics (P2), honest-empty for the new kinds ──
    variant(root, older_map)
    d, _, _, _ = call_json(c, "map_status", {})
    h = d and d.get("map_health")
    ok(h and h["fn_similarity"] == {"state": "clean", "mode": "exact"} and h["unparseable"] == {"state": "clean", "count": 0} and h["tasks_state"] == "clean" and d["counts"]["tasks"] == 0 and d["counts"]["providers"] == 0,
       "P2 SILENT: with the sentinel present, absent keys read CLEAN (the pass ran and found nothing)", h)
    d, _, _, _ = call_json(c, "touches", {"target": "GET /things/{item_id}"})
    ok(d and d["app_middleware"] == [] and "the app declares no ASGI middleware (the pass ran" in d["app_middleware_note"], "F1 SILENT: no app_middleware block with the sentinel → [] and the CLEAN wording (P2 decides, never a hedge)", d and d.get("app_middleware_note"))
    d, _, _, _ = call_json(c, "touches", {"target": "TASK sweep_things"})
    ok(d and d["matched"] is False and "0 registered task(s)" in d["reason"], "F3 SILENT: an older map has no task roster — said by name", d and d.get("reason"))
    d, _, _, _ = call_json(c, "find", {"query": "sweep", "kind": "task"})
    ok(d and d["total"] == 0 and "no task_roots block" in d["note"], "F3/F4 SILENT: find(kind=task) on an older map → 0 + the note", d and d.get("note"))
    d, _, _, _ = call_json(c, "find", {"query": "litellm", "kind": "provider"})
    ok(d and d["total"] == 0 and "no provider nodes" in d["note"], "F4 SILENT: find(kind=provider) with no provider nodes → 0 + the note", d and d.get("note"))
    d, _, _, _ = call_json(c, "entity_context", {"slug": "thing"})
    ok(d and d["c4"]["providers"] == [] and "task" not in d["c4"]["l2_node_kinds"], "F8 SILENT: no provider nodes → [], no TASK nodes → no task key", d and d.get("c4"))
    d, _, _, _ = call_json(c, "map_census", {"kind": "twins"})
    ok(d and d["census"]["twins"] == {"state": "clean", "text": "the structural-twin pass ran exactly"}, "F6 SILENT: the twin section reads clean through the sentinel", d and d.get("census"))
    a2 = json.load(open(os.path.join(root, "docs/site/center/archmap.json"))); a2.pop("route_mounts", None)
    write(root, "docs/site/center/archmap.json", json.dumps(a2, indent=1, sort_keys=True))
    d, _, _, _ = call_json(c, "map_status", {})
    h = d and d.get("map_health")
    ok(h and h["route_mounts"] == {"state": "not_emitted"} and h["fn_similarity"]["state"] == "not_emitted" and "regen to know" in h["states"], "P2: without the sentinel an absent key reads NOT_EMITTED — regen to know", h)
    d, _, _, _ = call_json(c, "touches", {"target": "GET /things/{item_id}"})
    ok(d and "regen to know" in d["app_middleware_note"], "F1: without the sentinel the app_middleware note says regen to know", d and d.get("app_middleware_note"))
    d, _, _, _ = call_json(c, "map_census", {"kind": "twins"})
    ok(d and d["census"]["twins"]["state"] == "not_emitted" and "regen to know" in d["census"]["twins"]["text"], "F6: the twin section says regen to know on an older map", d and d.get("census"))
    restore(root)
    # ── the CONFIG-ONLY variant (bootstrap_center.sh): the registry is the config, census absence ≠ 0, the empty schema arm, mounts clean, no web arm ──
    variant(root, config_only)
    d, _, _, _ = call_json(c, "center_overview", {})
    ok(d and d["registry"].startswith("config-only") and "unregistered" not in d and d["entities"][0]["status"] == "config-only" and d["census_gaps"]["files_unclaimed"] is None and "file_census" in d["census_absent"]
       and d["web"] == {"present": False, "reason": "no frontend"} and d["map_health"]["schemas_zero"].startswith("the schema arm extracted nothing"),
       "F7 FIRE: config-only registry (no 'unregistered'), absent census → None, the web arm's absence verbatim, the empty schema arm", d and {k: d.get(k) for k in ("registry", "census_gaps", "web")})
    d, _, _, _ = call_json(c, "entity_context", {})
    ok(d and d["registry"].startswith("config-only") and all(e["status"] == "config-only" and e["note"] == "config-only registry" for e in d["entities"]), "F8 FIRE: the entity list says config-only once and per row", d and d.get("entities"))
    d, _, _, _ = call_json(c, "map_census", {"kind": "schema"})
    ok(d and d["census"]["schema"]["empty_arm"].startswith("the schema arm extracted nothing across 3 endpoint(s)"), "F6 FIRE: 0 schemas across N endpoints = an EMPTY arm, said", d and d.get("census"))
    d, _, _, _ = call_json(c, "map_status", {})
    ok(d and d["counts"]["schemas"] == 0 and "schemas_rows" not in d["counts"], "F5 SILENT: no duplicate rows → schemas_rows is absent", d and d.get("counts"))
    d, _, _, _ = call_json(c, "map_census", {"kind": "mounts"})
    ok(d and d["census"]["mounts"]["unresolved"] == [] and d["census"]["mounts"]["state"] == "present" and "reason" not in d["census"]["mounts"], "F6 SILENT: mounts with nothing unresolved → [] and no reason", d and d.get("census"))
    d, _, _, _ = call_json(c, "entity_shape", {})
    ok(d and d["mounts_unresolved"] == 0 and "unresolved" not in d["one_line"], "F13 SILENT: no unresolved mount → one_line unchanged", d and d.get("one_line"))
    restore(root)
    d, _, _, _ = call_json(c, "center_overview", {})
    ok(d and d["unregistered"] == ["other"] and "registry" not in d, "F7 SILENT: with adoption.json the unregistered contract holds", d and d.get("unregistered"))
    # F15/N1 SILENT: no levels.json → the reason, never a crash
    os.rename(os.path.join(root, "docs/site/center/levels.json"), os.path.join(root, "docs/site/center/levels.json.off"))
    d, _, _, _ = call_json(c, "blast_radius", {"files": ["apps/api/api/things.py"]})
    ok(d and d["tasks_dispatched"] == {"reason": "no levels.json — dispatch edges unread"}, "F15 SILENT: no levels.json → the dispatch arm names its absence", d and d.get("tasks_dispatched"))
    d, _, _, _ = call_json(c, "trace", {"start": "GET /things/{item_id}"})
    ok(d and "hops" not in d and d["reason"].startswith("no levels.json in this center"), "N1 SILENT: no levels.json → the named reason, no stack", d and d.get("reason"))
    d, _, _, _ = call_json(c, "map_census", {"kind": "homing"})
    ok(d and d["census"]["homing"]["state"] == "not_emitted" and "regen" in d["census"]["homing"]["text"], "Part C SILENT: no levels.json → the homing section says not_emitted (regen), never a crash", d and d.get("census"))
    d, _, _, _ = call_json(c, "touches", {"target": "apps/api/services/thing.py#thing"})
    ok(d and "home_evidence" not in d["function"], "Part C SILENT: without levels.json the function answer carries no evidence field", d and sorted(d["function"].keys()))
    d, _, _, _ = call_json(c, "touches", {"target": "TASK sweep_things"})
    ok(d and d["dispatched_by"] == {"reason": "no levels.json — dispatch edges unread"}, "F3 SILENT: touches(task) names the missing dispatch source", d and d.get("dispatched_by"))
    os.rename(os.path.join(root, "docs/site/center/levels.json.off"), os.path.join(root, "docs/site/center/levels.json"))
    # F11: the corpus grep skips the suite's own installs; says so without .kdbp/
    write(root, "apps/api/tests/x_test.py", "def test_seven_C7():\n    pass\n"); git(root, "add", "apps/api/tests/x_test.py")
    d, _, _, _ = call_json(c, "cases_for", {"target": "apps/api/api/things.py::get_thing"})
    ok(d and d["corpus"]["max_cid_seen"] == 7 and d["corpus"]["next_cid_floor"] == 8, "F11 FIRE: a real test's C7 sets the corpus floor", d and d.get("corpus"))
    write(root, "scripts/_a3_tests.py", "# the C4 L2 elements — C99 is prose here\n"); write(root, "docs/site/center/generators/x_test.py", "C88\n")
    git(root, "add", "scripts/_a3_tests.py", "docs/site/center/generators/x_test.py")
    d, _, _, _ = call_json(c, "cases_for", {"target": "apps/api/api/things.py::get_thing"})
    ok(d and d["corpus"]["max_cid_seen"] == 7, "F11 SILENT: C99 in scripts/_a3_tests.py and C88 under docs/site/center/ never move the floor", d and d.get("corpus"))
    git(root, "rm", "-q", "--cached", "apps/api/tests/x_test.py", "scripts/_a3_tests.py", "docs/site/center/generators/x_test.py")
    for f in ("apps/api/tests/x_test.py", "scripts/_a3_tests.py", "docs/site/center/generators/x_test.py"):
        os.remove(os.path.join(root, f))
    shutil.rmtree(os.path.join(root, "docs/site/center/generators"), ignore_errors=True)
    kd = os.path.join(root, ".kdbp"); os.rename(kd, kd + ".off")
    d, _, _, _ = call_json(c, "cases_for", {"target": "apps/api/api/things.py::get_thing"})
    ok(d and d["corpus"]["note"].startswith("no .kdbp/"), "F11: without .kdbp/ the corpus floor is named a corpus artefact", d and d.get("corpus"))
    os.rename(kd + ".off", kd)
    d, _, _, _ = call_json(c, "map_diff", {"base": "HEAD"})
    ok(d and d["regenerated"] is False and "not regenerated" in d["note"], "map_diff: same head → regenerated:false, named", d)
    d, _, _, _ = call_json(c, "map_diff", {"base": "HEAD~2"})
    ok(d and d.get("regenerated") is None and "git show failed" in (d.get("reason") or ""), "map_diff: a ref without a committed map → reason, never a crash", d)
    # ── WS-2: the generators run from the SUITE, never from the target repo ───────
    d, _, _, _ = call_json(c, "center_status", {})
    ok(d and d["status"].get("ran") is True and (d["status"].get("text") or "").startswith("CENTER STATUS"),
       "center_status: runs the SUITE's own generator against the target root (WS-2)", d and d.get("status"))
    # the invariant the fix exists for: neither call site may execute a script out of the target tree
    _w2 = open(os.path.join(os.path.dirname(SERVER), "tools_wave2.py"), encoding="utf-8").read()
    ok('Path(root) / "scripts"' not in _w2,
       "WS-2: tools_wave2 never builds a script path under the target root", _w2.count('Path(root) / "scripts"'))
    ok(_w2.count('"-I"') == 2 and _w2.count('"GABE_REPO_ROOT"') == 2,
       "WS-2: both generator call sites run isolated (-I) AND pass GABE_REPO_ROOT", (_w2.count('"-I"'), _w2.count('"GABE_REPO_ROOT"')))
    # GABE_REPO_ROOT is REQUIRED, not cosmetic: _center_data.REPO_ROOT defaults to the
    # generator's OWN tree, so without it the suite copy reads the SUITE's center. Prove it.
    _gen = next((p for p in (os.path.join(REPO, r, "center_status.py")
                             for r in ("templates/center/generators", "templates/gabe/center/generators"))
                 if os.path.isfile(p)), None)
    ok(_gen is not None, "WS-2: the suite ships its own center_status.py for the resolver to find", REPO)
    if _gen:
        _r = sh([sys.executable, "-I", _gen, root], cwd=root)
        _o = _r.stdout
        ok("not a center project" in _o, "WS-2: the suite generator WITHOUT GABE_REPO_ROOT reads the wrong tree — the env var is load-bearing", _o[:120])
    d, _, _, _ = call_json(c, "review_drift", {"base": "HEAD~1"})
    ok(d and d["subjects"]["entity_shape"]["ran"] and d["subjects"]["web_bridge"]["ran"] and not d["subjects"]["reach"]["ran"] and not d["subjects"]["entity"]["ran"] and set(d["not_run"]) == {"reach", "entity", "workflow_census"},
       "review_drift: script-backed subjects run, record-backed ones NOT RUN with reasons", d and {k: v.get("ran") for k, v in (d or {}).get("subjects", {}).items()})
    # ── S2 (review batch 2): a `no index` Reach record is a real record — the reason must say so, not "no Reach: record".
    write(root, ".kdbp/PLAN.md", "# Plan\n\n## Phases\n\n| Phase | Exec | Review |\n|---|---|---|\n| P1 | ✅ | ⬜ |\n\n### Phase P1 — Noindex\n\n- **Reach:** no index\n")
    d, _, _, _ = call_json(c, "review_drift", {"base": "HEAD~1", "subjects": ["reach"]})
    _rr = (d or {}).get("subjects", {}).get("reach", {})
    ok(d and not _rr.get("ran") and "no index" in (_rr.get("reason") or "") and "no Reach: record" not in (_rr.get("reason") or ""),
       "S2: `- **Reach:** no index` → REACH NOT RUN names the no-index record, never 'no Reach: record'", _rr)
    os.remove(os.path.join(root, ".kdbp", "PLAN.md"))   # leave .kdbp/ itself — the who_calls emit gate below needs it
    # ── S3 (review batch 2): workflow_census must pass --archmap so census-lag can fire, and must NAME the junit half it
    # cannot run. Before: --center only → census-lag silently off, ran:true, nothing in not_run (a clean bill that was not one).
    _am_path = os.path.join(root, "docs", "site", "center", "archmap.json")
    _am_orig = open(_am_path, encoding="utf-8").read()
    _am = json.loads(_am_orig)
    _am["model_insight"] = {"Thing": {"columns": [{"name": "id"}, {"name": "name"}, {"name": "color"}]}}
    write(root, "docs/site/center/archmap.json", json.dumps(_am))
    write(root, "docs/site/center/workflows/thing.json",
          json.dumps({"entity": "thing", "states": {"s1": {"l": "Create thing", "shot": [], "writes": [["Thing.name", "", ""]]}}}))
    d, _, _, _ = call_json(c, "review_drift", {"base": "HEAD~1", "subjects": ["workflow_census"]})
    _wc = (d or {}).get("subjects", {}).get("workflow_census", {})
    _kinds = [f.get("kind") for r in (_wc.get("results") or []) for f in (r.get("result") or [])]
    ok(_wc.get("ran") is True and "census-lag" in _kinds and any(f.get("label") == "Thing.color" for r in (_wc.get("results") or []) for f in (r.get("result") or [])),
       "S3: workflow_census passes --archmap → census-lag fires on the uncovered column (Thing.color)", {"kinds": _kinds, "ran": _wc.get("ran")})
    ok(any("claim-drift (junit half)" in x for x in (_wc.get("not_run") or [])),
       "S3: the junit half it cannot run is NAMED in the subject's not_run, never silent", _wc.get("not_run"))
    write(root, "docs/site/center/archmap.json", _am_orig)
    os.remove(os.path.join(root, "docs", "site", "center", "workflows", "thing.json")); os.rmdir(os.path.join(root, "docs", "site", "center", "workflows"))
    d, _, _, _ = call_json(c, "who_calls", {"symbol": "thing", "direction": "out", "depth": "2"})
    ok(d and d["direction"] == "out" and "callees" in d and "callers" not in d and d["emitted"] == 0 and any("transitive" in s for s in d["emit_skipped"]), "who_calls direction=out: callees named, never emits", d and {k: d.get(k) for k in ("direction", "emitted", "emit_skipped")})
    ok(d and d["map_confidence"]["active_missed_edges"] is None and "no map-delta ledger" in d["map_confidence"]["note"], "who_calls: map_confidence field present (no ledger → honest)", d and d.get("map_confidence"))

    # ── who_calls: the five emit gates ────────────────────────────────────────
    d, _, _, _ = call_json(c, "who_calls", {"symbol": "thing"})
    ok(d and d["map_claim"] == "present" and d["callers"] == ["apps/api/other.py"] and d["defs"] == ["apps/api/services/thing.py"], "who_calls: graft arm parsed", d and {k: d.get(k) for k in ("map_claim", "callers", "defs", "callers_status")})
    ok(d and "apps/api/services/downstream.py" in d["grep_code_files"] and "apps/api/tests/test_thing.py" in d["grep_prose_files"],
       "who_calls: code hit vs docstring-only file classified (tokenize)", d and {k: d.get(k) for k in ("grep_code_files", "grep_prose_files", "grep_status")})
    ok(d and d["missed_by_map"] == ["apps/api/services/downstream.py"] and d["emitted"] == 1, "who_calls: the missed code caller is emitted (once)", d and {k: d.get(k) for k in ("missed_by_map", "emitted", "emit_skipped", "gates")})
    lines = live_lines(root)
    ok(len(lines) == 1 and '"cmd":"mcp"' in lines[0] and '"subject":"callers(thing)"' in lines[0] and "downstream.py" in lines[0], "delta line written with cmd:mcp", lines)
    ok(d and d["reach_line"].startswith("- **Reach:** ") and "graft@" in d["reach_line"] and "downstream.py" in d["reach_line"], "reach line includes the grep-found code file", d and d.get("reach_line"))
    d, _, _, _ = call_json(c, "who_calls", {"symbol": "thing"})
    ok(len(live_lines(root)) == 1 and d["emitted"] == 0, "repeat call → 0 new lines (--once in the writer)", live_lines(root))
    d, _, _, _ = call_json(c, "who_calls", {"symbol": "nothing_indexed"})
    ok(d and d["map_claim"].startswith("absent") and d["emitted"] == 0 and len(live_lines(root)) == 1, "empty graft arm → no claim → no emit", d and {k: d.get(k) for k in ("map_claim", "emitted", "emit_skipped")})
    d, _, _, _ = call_json(c, "who_calls", {"symbol": "thing", "emit": False})
    ok(d and d["emitted"] == 0 and d["gates"]["emit_requested"] is False, "emit:false → no write", d and d.get("gates"))
    # F1: a rollup ledger present must not crash who_calls (json was unimported) — map_confidence answers
    with open(os.path.join(root, ".kdbp", "map-deltas-rollup.jsonl"), "w") as fh:
        fh.write(json.dumps({"v": 2, "gen": "_a3_graft.calls", "subject": "callers(x)", "file": "a.py", "count": 3, "last_n": 999999}) + "\n")
    d, is_err, _, _ = call_json(c, "who_calls", {"symbol": "thing", "emit": False})
    ok(not is_err and d and (d.get("map_confidence") or {}).get("active_missed_edges") == 1, "who_calls with a rollup ledger → map_confidence (F1: json import)", d and d.get("map_confidence"))
    os.remove(os.path.join(root, ".kdbp", "map-deltas-rollup.jsonl"))
    d, is_err, _, _ = call_json(c, "who_calls", {"symbol": "bad symbol; rm -rf"})
    ok(is_err and d and "identifier" in d.get("stop", ""), "non-identifier symbol → stop", d)
    c.close()
    # GABE_MAP_NO_EMIT
    os.remove(os.path.join(root, ".kdbp", "map-deltas.jsonl"))
    c = spawn(root, T, graft_dir=gdir, env_extra={"GABE_MAP_NO_EMIT": "1"}); c.initialize()
    d, _, _, _ = call_json(c, "who_calls", {"symbol": "thing"})
    ok(d and d["emitted"] == 0 and not live_lines(root), "GABE_MAP_NO_EMIT=1 → nothing written (the twin dry-run switch)", d and d.get("emitted"))
    c.close()
    # not gitignored → skipped and named
    noign = make_repo(os.path.join(T, "b"), seed_ignore=False)
    os.makedirs(os.path.join(noign, "graft"), exist_ok=True)
    c = spawn(noign, T, graft_dir=gdir); c.initialize()
    d, _, _, _ = call_json(c, "who_calls", {"symbol": "thing"})
    ok(d and d["emitted"] == 0 and any("not gitignored" in s for s in d["emit_skipped"]) and not live_lines(noign), "un-ignored accumulator → emit skipped + named", d and d.get("emit_skipped"))
    c.close()
    # no graft dir → grep arm still answers, no emit, reach line honest
    nograft = make_repo(os.path.join(T, "c"))
    c = spawn(nograft, T, graft_dir=gdir); c.initialize()
    d, _, _, _ = call_json(c, "who_calls", {"symbol": "thing"})
    ok(d and d["callers_status"].startswith("no index") and d["grep_code_files"] and d["emitted"] == 0 and d["reach_line"] == "no index",
       "no graft/ → grep arm answers, no emit, reach_line 'no index'", d and {k: d.get(k) for k in ("callers_status", "grep_code_files", "emitted", "reach_line")})
    c.close()

    # ── opt-in harness e2e (API-billed) ───────────────────────────────────────
    if os.environ.get("GABE_MAP_E2E"):
        cfg = os.path.join(T, "mcp.json")
        write(T, "mcp.json", json.dumps({"mcpServers": {"gabe-map": {"type": "stdio", "command": sys.executable, "args": [SERVER]}}}))
        env = {k: v for k, v in os.environ.items() if k not in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT")}
        env["PATH"] = gdir + ":" + env.get("PATH", "")
        r = subprocess.run(["claude", "-p", "Call the gabe-map map_status tool once and print only the word DONE.", "--mcp-config", cfg,
                            "--strict-mcp-config", "--allowedTools", "mcp__gabe-map", "--max-turns", "3", "--output-format", "stream-json", "--verbose"],
                           cwd=root, env=env, capture_output=True, text=True, timeout=240)
        # the stream carries the assistant's tool_use blocks — the ONLY place the call is visible from outside the server
        called = '"name":"mcp__gabe-map__map_status"' in r.stdout.replace(" ", "")
        ok(r.returncode == 0 and called, "harness e2e: the model called mcp__gabe-map__map_status through the real client", r.stdout[-400:] + r.stderr[-300:])




def part_b_tail(root, T, gdir):
    """F12 (review_drift ignores the suite's own install hunks) + F14 (map_diff: task roots + the health delta) — they add commits, so they run last."""
    c = spawn(root, T, graft_dir=gdir)
    c.initialize()
    write(root, "docs/site/center/x.html", "<script>apiFetch('/x')</script>\n")            # the suite's own template prose (the study-repo phantom)
    write(root, "apps/web/hooks/useY.ts", "export const useY = () => apiFetch('/y');\n")     # a real project fetch (the detector's idiom)
    git(root, "add", "-A"); git(root, "commit", "-q", "-m", "center install + a real hook")
    d, _, _, _ = call_json(c, "review_drift", {"base": "HEAD~1", "subjects": ["web_bridge"]})
    wb = d and d["subjects"]["web_bridge"]
    ok(wb and wb.get("ran") and [list(x)[:2] for x in wb["new_fetches"]] == [["GET", "/y"]], "F12 FIRE/SILENT: the center's own fetch('/x') is not a project fetch; the real hook's fetch('/y') still is", wb)
    a = json.load(open(os.path.join(root, "docs/site/center/archmap.json")))
    a0 = dict(a); a0.pop("task_roots"); a0.pop("unparseable"); a0["head"] = "0000beef"
    a0["route_mounts"] = dict(a["route_mounts"], unresolved=[])
    write(root, "docs/site/center/archmap.json", json.dumps(a0, indent=1, sort_keys=True)); git(root, "add", "-A"); git(root, "commit", "-q", "-m", "regen without the task")
    write(root, "docs/site/center/archmap.json", json.dumps(a, indent=1, sort_keys=True)); git(root, "add", "-A"); git(root, "commit", "-q", "-m", "regen with the task")
    d, _, _, _ = call_json(c, "map_diff", {"base": "HEAD~1"})
    ok(d and d["regenerated"] and d["tasks"] == {"added": ["sweep_things"], "removed": [], "base": 0, "head": 1} and d["health_delta"]["mounts_unresolved"] == [0, 1] and d["health_delta"]["unparseable"] == [0, 1],
       "F14 FIRE: map_diff names the task root that appeared and the health delta (mounts · unparseable)", d and {k: d.get(k) for k in ("tasks", "health_delta")})
    c.close()

if __name__ == "__main__":
    sys.exit(main())
