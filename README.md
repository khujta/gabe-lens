<div align="center">

<img src="assets/gabe-lens-hero.png" alt="gabe-suite" width="600">

# Gabe Suite

**Development suite for Claude Code**

Skills and hooks for understanding, reviewing, deciding, and shipping — with a knowledge system (KDBP) that tracks values, decisions, and deferred work across sessions.

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)
[![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-Plugin-blueviolet.svg?style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiPjxwYXRoIGQ9Ik0xMiAyTDIgN2wxMCA1IDEwLTUtMTAtNXoiLz48cGF0aCBkPSJNMiAxN2wxMCA1IDEwLTUiLz48cGF0aCBkPSJNMiAxMmwxMCA1IDEwLTUiLz48L3N2Zz4=)](https://github.com/khujta/gabe-suite)
[![Version](https://img.shields.io/badge/version-2.3.0-green.svg?style=flat-square)](https://github.com/khujta/gabe-suite)
[![GitHub Stars](https://img.shields.io/github/stars/khujta/gabe-suite?style=flat-square&color=yellow)](https://github.com/khujta/gabe-suite/stargazers)

*Not a prompt template. Built from empirical self-observation.*

</div>

> **Name note.** The project/suite is **Gabe Suite**. One of the skills inside it is called **Gabe Lens** (invoked via `/gabe-lens`) — the cognitive-translation layer. They're different things: the suite contains the skill. Previous name for the suite was "Gabe Lens" — this repo was renamed to avoid collision.

## The Suite

### Skill Highlights

| Skill | Command | What it does |
|---|---|---|
| **Gabe Lens** | `/gabe-lens` | Cognitive translation — analogies, spatial maps, constraint boxes, one-line handles |
| **Gabe Review** | `/gabe-review` | Code review — risk pricing, confidence scoring, interactive triage, deferred items, tier drift |
| **Gabe Roast** | `/gabe-roast` | Adversarial gap review — stress-tests from a required perspective |
| **Gabe Myopic** | `/gabe-myopic` | Short-sighted-user walkthrough — simulates a shallow planning horizon (1/1.5/2 steps) to flag foresight traps, overwhelm, recall demands, no-undo dead-ends |
| **Gabe Assess** | `/gabe-assess` | The direction guard — change impact (blast radius, maturity scope, prerequisites) + values/AP boundary check |
| **Gabe Health** | `/gabe-health` | The scanner, three lenses — codebase health · decision-debt (`debt`) · skill-estate sweep (`estate`, ask-first) |
| **Gabe Help** | `/gabe-help` | Context-aware guide — scans environment, suggests the right tool |
| **Gabe Mockup** | `/gabe-mockup` | UX/mockup execution — legacy HTML recipes plus React-first Storybook modes |
| **Gabe Docs** | _(consulted)_ | Documentation house style — CommonMark, Mermaid library, per-well diagram recommendations (used by `/gabe-init`, `/gabe-commit`) |

### Command Surface (30 skills)

Every capability is one skill under `skills/<name>/` — the skill name gives the slash
invocation (`skills/gabe-plan/` ⇒ `/gabe-plan`). Each SKILL.md is a lean core that loads
its binding spec from the skill's `references/` directory on demand. The command surface
covers the full KDBP lifecycle from project init through ship:

| Command | What it does |
|---|---|
| `/gabe-artifact` | House chrome for published Artifacts — left-anchored content, one cog panel top-right, the fixed font roster; design pass → kit → render gate → publish → report |
| `/gabe-cc-init` | Brownfield command-center adoption — archive existing docs (never delete), bootstrap the center, machine-rank the critical entities, ingest one section per run at human speed with checklist + walk-recorded approval |
| `/gabe-assess` | The direction guard — change impact assessment + values/AP boundary check; auto-triggers on direction steers in KDBP projects (direction-guard.sh) |
| `/gabe-commit` | Commit quality gate — deterministic checks, interactive triage, defer/accept/fix |
| `gabe-docs` *(background)* | Documentation standards + the suite execution contract — consulted by other skills, not invoked directly |
| `/gabe-docsite` | Publish docs onto the generated HTML docs site — place, wire the nav, render with working diagrams |
| `/gabe-cc-entity` | Entity-context reader — assemble one entity's slice (code map + registry + bindings) into a context pack from the command center's data; brief or JSON |
| `/gabe-execute` | Phase execution — tier-cap task breakdown, mid-phase escalation gate |
| `/gabe-cc-update` | Testing-command-center feature coverage — lens card + diagrams + evidence narration over machine facts; status/backfill/curate (projects with `docs/site/center/`) |
| `/gabe-handoff` | Session handoff — paste-able next-session resume prompt + evidence-gated KDBP state sync (PLAN/LEDGER/PENDING) into `.kdbp/HANDOFF.md` |
| `/gabe-health` | The suite scanner — structural health (god files, churn, coupling, bugs) · `debt` decision-debt lens with AP citations · `estate` ask-first promote/archive sweep |
| `/gabe-help` | Context-aware guide — scans environment and suggests the right workflow |
| `/gabe-imagine` | Give it a context — a concept, an app, a use case, a phenomenon, a code map — and it dissects the material (seats, spheres, gravity worlds), proposes representations ranked critical/recommended/nice-to-have, asks, then builds command-center pages: component-led, register-voiced captions under a hard surface budget, assets lifted from the pattern libraries before anything is invented. Five floor grammars by material shape; console or article pages, or a published artifact |
| `/gabe-kdbp` | The .kdbp lifecycle state as 7 read-only MCP tools (kdbp_snapshot · phase_context · review_target · next_beat · verify_commands · pending_row_preview · ledger_row_preview); status / register / probe |
| `/gabe-init` | Project setup — creates `.kdbp/`, installs hooks, selects project type + maturity |
| `/gabe-lens` | Cognitive translation — analogies, constraint boxes, Gabe Blocks |
| `/gabe-map` | The codebase map as 17 MCP tools (who_calls · touches · owner_of · cases_for · entity_context · entity_shape · map_status · find · outline · center_overview · blast_radius · map_census · map_diff · center_status · review_drift · trace · gates); status / register / probe |
| `/gabe-meme` | Oblique-meme generation — persona-matched visual metaphors via memegen.link, verified PNGs, punch-up only; + surface-wit mode for rendered HTML surfaces (absorbed gabe-quip) |
| `/gabe-mockup` | Mockup/UX workflow — legacy static mockups plus React-first Storybook and `design-ref` |
| `/gabe-myopic` | Short-sighted-user walkthrough — panel of 3 planning horizons flags foresight traps, overwhelm, recall demands, no-undo dead-ends |
| `/gabe-next` | Zero-logic router — reads PLAN.md and dispatches to the next gabe command |
| `/gabe-plan` | KDBP-aware planning + per-phase tier decision with optional HTML review artifact for complex decisions |
| `/gabe-pulse` | Read-only completeness sweep — after a stretch of work, is anything important owed? Ten deterministic signals, four bands, every row naming the command that clears it. Writes nothing, dispatches nothing |
| `/gabe-push` | Push, create PR, watch CI, promote branches — post-commit shipping; terminal-env pushes are gated by a blocking proceed/hold ask backed by the fail-closed push-gate hook |
| `/gabe-red` | TDD's first half as a beat — declare the failing cases before code (C-ids born in test names), commit the red checkpoint; guards for refactors, enumerated skips |
| `/gabe-review` | Code review — risk pricing, confidence scoring, interactive triage, deferred items |
| `/gabe-roast` | Adversarial gap review — stress-tests from a required perspective |
| `/gabe-scope` | Authors SCOPE.md — stable premise plus the phase arc in its `## Phases` section — and `scope-references.yaml`. Multi-step, checkpoint-gated, Opus-heavy |
| `/gabe-scope-change` | Scope evolution, one entry point — classifies pivot vs addition; additions execute inline, pivots route to `-pivot` |
| `/gabe-scope-pivot` | Scope pivot — direction change, archives v{N} and creates v{N+1} |

### KDBP System

The Knowledge, Decisions, Behavior, and Pending system tracks project state across sessions:

```
.kdbp/
├── BEHAVIOR.md      # Project name, domain, maturity, tech stack
├── VALUES.md        # 3-7 project-specific values (checked at commit)
├── DECISIONS.md     # Append-only architecture decision table
├── PENDING.md       # Deferred items with priority and escalation
├── LEDGER.md        # Thin session index — one row per command checkpoint
├── PLAN.md          # Active plan (written by /gabe-plan)
├── PLAN.json        # Machine mirror of PLAN.md (phases, tier, per-phase proof) — read by session hooks
└── archive/         # Archived plans (completed_, defer_, cancelled_) + retired legacy files
```

User-level values at `~/.kdbp/VALUES.md` apply across all projects.

For complex plans, `/gabe-plan` may also create a self-contained HTML review artifact under `docs/gabe/plans/...`. That HTML is the human-facing entrypoint for dense decisions, diagrams, phase maps, and bottleneck summaries; `.kdbp/PLAN.md`, `.kdbp/DECISIONS.md`, and `.kdbp/LEDGER.md` remain canonical for automation and lifecycle state. Every complex HTML artifact should include a visible detail-link section that points readers to the Markdown/README files where deeper implementation details live.

### Hooks (5, installed to `~/.claude/settings.json`)

| Hook | Event | What it does |
|---|---|---|
| KDBP Active | SessionStart | Loads project name, maturity, and stack from `.kdbp/BEHAVIOR.md` |
| ACTIVE PLAN | SessionStart | Surfaces current phase + state cells — reads `.kdbp/PLAN.json` first, falls back to `PLAN.md` |
| KDBP CHECKPOINT | PreToolUse (Bash) | Warns on raw `git commit`, points to `/gabe-commit` |
| PUSH-GATE-GUARD | PreToolUse (Bash) | Fails a raw terminal-env `git push` closed in multi-env projects unless `/gabe-push` minted a fresh gate marker after the ONE proceed/hold ask |
| RED-ENTRY-GUARD | PreToolUse (Write/Edit) | Warns on source writes while the current phase's Red cell is still owed |
| STRUCTURE: warning | PostToolUse (Write) | Warns when a new file doesn't match a pattern in `.kdbp/STRUCTURE.md` |
| PLAN-PROOF-GUARD | PostToolUse (Write/Edit) | D7 — blocks a PLAN ✅ cell whose cited evidence doesn't exist (debts warn, lies block) |
| DIRECTION GUARD | UserPromptSubmit | Injects the steer rule in KDBP projects — direction changes route through `/gabe-assess brief` before building |
| SESSION-END REMINDER | Stop | NEXT-pointer (0.3b): fires only when the tree is dirty AND no commit landed this session — prints `next: /gabe-commit` once |

### Workflows

| I need to... | Use |
|---|---|
| Start a new project | `/gabe-init [name]` |
| Start from a fresh idea | `/gabe-assess "idea"` then `/gabe-init`, `/gabe-scope`, `/gabe-plan` |
| Adopt an existing codebase | read [docs/workflows/brownfield.md](docs/workflows/brownfield.md), then use `/gabe-init` or `/gabe-init update` |
| Point the graph at a repo you don't own | a study, a due-diligence read, a first look: `bootstrap_center.sh <repo>` on a local branch, fill the entities, `refresh_center.sh regen` — see [docs/workflows/brownfield.md](docs/workflows/brownfield.md#adopt-a-repo-you-dont-own-a-study-install) and the [repo-study design record](docs/design/repo-study/README.md) |
| Scope a new project (SCOPE.md, incl. its `## Phases` section) | `/gabe-scope` |
| Change project scope | `/gabe-scope-change "description of change"` |
| Check values alignment (boundary check) | `/gabe-assess` |
| Understand a concept | `/gabe-lens [concept]` |
| Find gaps in a design | `/gabe-roast [perspective] [target]` |
| Find where short-sighted users get lost or trapped | `/gabe-myopic [target]` |
| Assess a change | `/gabe-assess [change]` |
| Create or manage a plan (with tier picker) | `/gabe-plan [goal]` |
| Execute the current phase | `/gabe-execute` |
| Execute mockup or React Storybook UI work | `/gabe-mockup` |
| Advance automatically to next step | `/gabe-next` |
| Review code | `/gabe-review` |
| Scan architecture decision debt | `/gabe-health debt [brief|dry-run]` |
| Check codebase health | `/gabe-health` |
| Commit with quality checks | `/gabe-commit [message]` |
| Push, create PR, watch CI | `/gabe-push` |
| Consolidate architect-level understanding | `/gabe-teach [topics/status/free]` |
| What tool do I need? | `/gabe-help` |

### Documentation

| Doc | Purpose |
|-----|---------|
| [docs/WORKFLOW.md](docs/WORKFLOW.md) | State machine + command flow — start here |
| [docs/workflows/README.md](docs/workflows/README.md) | Greenfield vs brownfield workflow chooser |
| [docs/workflows/greenfield.md](docs/workflows/greenfield.md) | Idea-to-first-phase workflow for new apps |
| [docs/workflows/brownfield.md](docs/workflows/brownfield.md) | Adoption guide for existing codebases |
| [docs/suite-state-audit.md](docs/suite-state-audit.md) | Current suite inventory and gap audit |
| [docs/GAPS.md](docs/GAPS.md) | Remaining workflow gaps + options |
| [docs/architecture/requirements.md](docs/architecture/requirements.md) | Design invariants + non-goals |
| [docs/architecture/diagram-standards.md](docs/architecture/diagram-standards.md) | Mermaid conventions for suite docs |
| [docs/architecture/scope-data-contracts.md](docs/architecture/scope-data-contracts.md) | `/gabe-scope` output contract |
| [docs/architecture/stack.md](docs/architecture/stack.md) | Recommended application stack (Python + FastAPI + PydanticAI + React + Bun) for downstream projects |

---

## Install

```bash
git clone https://github.com/khujta/gabe-suite.git
cd gabe-suite
./install.sh              # Install skills, commands, templates, and docs
./install.sh --dry-run    # Show what would be done
./install.sh --uninstall  # Remove everything
```

After install, initialize a project:

```
/gabe-init [project-name]
```

This creates `.kdbp/`, installs hooks, and asks about project type and maturity.

---

## Gabe Lens (skill)

> Everything from here through "Cognitive Suits" describes the `/gabe-lens` cognitive-translation skill — the single component that shares its name with the old suite. Other skills (`/gabe-review`, `/gabe-roast`, `/gabe-assess`, etc.) are documented further below or in their respective SKILL.md files.

### See it in action

Ask `/gabe-lens enforcement tiers` and get this:

```
┌─── GABE BLOCK: Enforcement Tiers ──────────────────────┐
│                                                        │
│  THE PROBLEM                                           │
│  Rules written in docs get ignored under fatigue and   │
│  context loss. 19 files exceeded the 800-line limit    │
│  despite the limit being documented everywhere.        │
│                                                        │
│  THE ANALOGY                                           │
│  Think of it as gravity vs. posted speed limits.       │
│  Gravity (Tier 1 hooks) works whether you're paying    │
│  attention or not — drop a ball, it falls. Speed       │
│  limits (Tier 3 docs) only work if the driver reads    │
│  the sign AND chooses to comply. Tier 2 (workflows)    │
│  is like a speed bump — it slows you down IF you       │
│  drive over it, but you can take a different road.     │
│                                                        │
│  THE MAP                                               │
│                                                        │
│    Tier 1: GRAVITY ══════════════════► Always works    │
│    (hooks)    PreToolUse ─→ fires every edit           │
│               pre-commit ─→ fires every commit         │
│                                                        │
│    Tier 2: SPEED BUMPS ─ ─ ─ ─ ─ ─ ─► Works if used    │
│    (workflows) /review ─→ only if invoked              │
│                                                        │
│    Tier 3: POSTED SIGNS · · · · · · ·► Often ignored   │
│    (docs)     CLAUDE.md rules ─→ lost after compaction │
│                                                        │
│  CONSTRAINT BOX                                        │
│    IS:      A reliability classification for rules     │
│    IS NOT:  A quality judgment (Tier 3 rules aren't    │
│             bad rules — they're just badly placed)     │
│    DECIDES: Where to invest enforcement effort —       │
│             convert Tier 3 lessons into Tier 1 hooks   │
│                                                        │
│  ONE-LINE HANDLE                                       │
│  "Hooks are gravity — docs are speed limit signs"      │
│                                                        │
│  SIGNAL: Quick check ✓                                 │
│  (The concept is intuitive once you see the tiers.     │
│   Don't overthink — the tier system IS the insight.)   │
└────────────────────────────────────────────────────────┘
```

That one-line handle — *"Hooks are gravity — docs are speed limit signs"* — stuck for weeks. The original 3-paragraph explanation didn't last a day.

### Usage

#### Full block (default)

```
/gabe-lens [concept or question]
```

All components: problem, analogy, map, constraint box, one-line handle. ~200-350 tokens.

#### Brief

```
/gabe-lens bf [concept]
```

Constraint box + one-line handle only. ~40-80 tokens. For previously introduced concepts.

#### Oneliner

```
/gabe-lens ol [concept]
```

Just the memorable phrase. ~5-15 tokens. For compaction handoffs or re-anchoring.

#### Annotate a document

```
/gabe-lens an [file-path]
```

Reads a file and produces a companion with Gabe Blocks for the 3-5 most critical concepts.

### Compression modes

| Context | Mode | Command | Tokens |
|---|---|---|---|
| First encounter with a concept | Full | `/gabe-lens` | ~200-350 |
| Referencing a known concept | Brief | `/gabe-lens bf` | ~40-80 |
| Compaction handoff or re-anchoring | Oneliner | `/gabe-lens ol` | ~5-15 |

### Analogy domains

Physical systems you can visualize in 3D, in preference order:

1. **Mechanical** — gears, valves, pulleys
2. **Fluid dynamics** — pressure, flow, reservoirs
3. **Optics** — lenses, mirrors, refraction
4. **Chemistry** — reactions, catalysts, equilibrium
5. **Electromagnetism** — fields, circuits, charges
6. **Thermodynamics** — heat, entropy, engines
7. **Biology** — cells, ecosystems, evolution

If no good physical analogy exists, the skill says so explicitly rather than forcing a weak metaphor.

### Cognitive Suits

Not everyone thinks the same way. The Gabe Lens skill adapts its output to match how your brain works.

| Suit | Style | Example handle for "caching" |
|---|---|---|
| **Spatial-Analogical** (default) | Physical metaphors, 3D diagrams | "A fridge next to the stove" |
| **Sequential-Procedural** | Step-by-step, process flows | "Check the shelf before the warehouse" |
| **Abstract-Structural** | Patterns, types, relationships | "Every cache is a trade: space for time" |
| **Narrative-Contextual** | Stories, characters, scenarios | "The barista remembers your order" |

#### Calibrate

```
/gabe-lens-calibrate
```

Presents the same concept in all 4 suits. Pick the one that clicks. Your choice is saved globally and used for all future `/gabe-lens` output.

To reset to default: `/gabe-lens-calibrate reset`

---

## Gabe Roast (skill)

Adversarial gap review. Adopts a perspective (architect, UX designer, security auditor, etc.) and attacks a target to find what's missing, broken, or risky.

### See it in action

Ask `/gabe-roast "UX Designer" MOCKUP-PLAN.md` and get:

```
GABE ROAST: MOCKUP-PLAN.md
Perspective: UX Designer

═══ MVP ════════════════════════════════════════════════

CRITICAL

  M1
  **Gap:** The plan starts with 12 isolated screen mockups
  but defines no user flow diagrams. Each screen is designed
  in a vacuum.
  **One-liner:** "Building rooms before drawing the hallways"
  **Effort:** M (confident)
  **Lose:** Every screen gets reworked once flows reveal they
  don't connect.

HIGH

  M2
  **Gap:** Component library is extracted BEFORE screens exist.
  **One-liner:** "Packing a suitcase before knowing the destination"
  **Effort:** S (confident)
  **Lose:** Component library gets rebuilt from scratch once
  real screens reveal actual patterns.

────────────────────────────────────────────────────────
TOTAL: 2 gaps — 1 critical, 1 high
```

### Usage

Both inputs are **required** — if either is missing, the skill asks before proceeding.

```
/gabe-roast [perspective] [target]
```

**Brief mode** (table format):

```
/gabe-roast bf [perspective] [target]
```

### Classification

Gaps are grouped by **maturity level** (MVP / Enterprise / Scale), then by **importance** (Critical / High / Medium / Low). Each gap includes a Gabe Lens one-liner, effort estimate with confidence, and the cost of inaction.

---

## Gabe Assess (skill)

Rapid change impact assessment. Pauses before an "obvious yes" to surface what a proposed change actually means before you commit.

### See it in action

Someone proposes fixing CORS on a shared staging bucket. Before saying yes:

```
/gabe-assess Fix Storage CORS for staging scan testing
```

```
GABE ASSESS: Fix Storage CORS for staging scan testing
Context: blocker

D1 BLAST RADIUS: External
   Bucket is shared with Gustify. CORS changes affect all apps.

D2 MATURITY SCOPE: MVP
   Current: MVP. Proposed: MVP-appropriate config change.
   Match — but shared infra elevates risk.

D3 PREREQUISITES:
   - Verify Gustify doesn't have its own CORS config
   - Check who deploys staging rules (INC-001)

D4 ALTERNATIVES:
   [A] Do nothing — defer E2E, unit tests already prove it
   [B] Minimal    — gsutil cors set + allowedEmails entry (S)
   [C] Proper     — combined rules deploy from Gustify repo (M)
   [D] Workaround — test via admin script, bypass client (S)

RECOMMENDATION: [B] — neither change touches shared rules file
ONE-LINER: "Bucket knob and guest list — don't redecorate the shared house"
```

### Usage

```
/gabe-assess [change description]           # Full assessment
/gabe-assess bf [change]                    # Brief (4 lines)
/gabe-assess il [change]                    # Inline (1 sentence)
/gabe-assess batch [change 1] + [change 2]  # Multiple changes
```

### Assessment dimensions

| Dimension | Question |
|---|---|
| **D1 Blast Radius** | What does this touch? (Contained / Local / Cross-cutting / External) |
| **D2 Maturity Scope** | Is this the right level of fix for where we are? (MVP / Enterprise / Scale) |
| **D3 Prerequisites** | What must be true before this change is safe? |
| **D4 Alternatives** | Is there a simpler, cheaper, or more appropriate path? |

---

## Gabe Myopic (skill)

Role-plays a **short-sighted user** — someone whose planning horizon is 1 to 2 steps, never 3+ —
and walks a flow to find where the design demands foresight a normal person doesn't have. It's the
inverse of an expert design panel: not *"what would a master notice?"* but *"what would a beginner
fail to see coming?"* The signature catch is the **mattress trap** — a choice whose real
consequence lands two or more steps later, invisible at the moment you make it.

### See it in action

Ask `/gabe-myopic checkout-flow` and get:

```
# Myopic Walk: checkout-flow
> Simulated short-sighted users — findings are hypotheses to validate, not proof.

## Panel result
| User  | Fatal step | What breaks them                                  |
|-------|-----------|----------------------------------------------------|
| @1    | 2         | two decisions before any progress shows            |
| @1.5  | 4         | shipping methods pruned by a country picked step 2 |
| @2    | 5         | discount field is on payment, total is on review   |

## Findings (most severe first)
### [CRITICAL] 🛏️ Step 2 → bites at Step 4 — country silently prunes shipping
- What the myopic user does: picks a country reactively; at step 4 half the
  shipping options are gone with no message tying it back.
- Fix: show "ships to {country}: 2 of 4 methods" on the address step itself.

## The handle
"Braces for the total — the discount door was two rooms back, already locked."
```

### Usage

```
/gabe-myopic [target]            # WALK — full panel of 3 horizons (default)
/gabe-myopic trap [target]       # only foresight traps (the mattress)
/gabe-myopic step [target]       # interactive, first-person, one step per turn
/gabe-myopic fix [target]        # propose horizon-collapsing design changes
/gabe-myopic horizon [feature]   # 30-second triage: how many steps of foresight?
```

The **target** is anything that represents the flow: a described workflow, a spec/PRD, UI code,
screenshots, or a live app.

### The four flags

| Flag | Fires when… |
|---|---|
| 🛏️ **Foresight trap** | a choice's consequence lands ≥2 steps later, unseen now |
| 🌊 **Overwhelm point** | one step demands more simultaneous decisions than working memory holds |
| 🧠 **Recall demand** | the user must carry info from an earlier step in their head |
| 🚪 **No-undo dead-end** | the myopic path went wrong and there's no cheap way back |

Grounded in the **Cognitive Walkthrough** method, tuned by bounded planning horizon and present-bias
myopia — see `skills/gabe-myopic/reference.md`.

---

## Embedding in workflows

```yaml
project_knowledge:
  optional:
    - "skills/gabe-lens/SKILL.md"
    - "skills/gabe-roast/SKILL.md"
```

One-line handles from both skills enhance compaction handoff notes by surviving context compression.

## The origin story

<details>
<summary>How the Gabe Lens skill — and later the whole suite — was built from a cognitive self-observation experiment</summary>

The suite started as a single skill called `gabe-lens`. That skill started as a personal experiment: **what happens when you use AI to reverse-engineer how your own brain learns?** Over time, workflow commands (`/gabe-init`, `/gabe-commit`, `/gabe-plan`, `/gabe-execute`, `/gabe-push`, `/gabe-teach`, `/gabe-scope`) and companion skills (`/gabe-roast`, `/gabe-assess`, `/gabe-assess`, `/gabe-review`, `/gabe-health`, `/gabe-help`, plus the consulted-only `gabe-docs` and `gabe-arch`) accreted around it. The umbrella became the Gabe Suite. The origin skill kept its name.

I sat down with Claude and deliberately tried to learn a complex topic — attention mechanisms in neural networks. But the real goal wasn't understanding attention. It was watching *how my mind processed* the explanation, in real time, and having Claude observe and document the patterns.

What we discovered:

- **I don't reach for equations — I reach for metaphors.** When learning how Query/Key/Value works in transformers, I spontaneously generated analogies: spheres reflecting light onto each other, chemical reactions with temperature and state. These weren't decorations — they were my primary reasoning substrate.

- **I reason top-down, not bottom-up.** My mind asks "why does this exist?" before "how does it work?" Purpose first, constraints second, mechanism last.

- **I learn in spirals.** Constrained prototype → generalize → formalize → refine. I don't need complete understanding to start.

- **I have an overthinking trap.** When a correct answer comes fast, I spiral searching for hidden complexity that isn't there. The IS NOT field in constraint boxes was designed specifically to short-circuit this.

These were patterns observed during actual learning exercises, documented in real time. Once we had the cognitive profile, the next question was obvious: can we turn this into a reusable format?

The learning profile became the SKILL.md. The explanation sequence (Problem → Analogy → Code) became the Gabe Block. The overthinking trap mitigation became the constraint box. The one-liners I remembered days later became the one-line handles.

</details>

## License

MIT
