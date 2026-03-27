---
name: gabe-align
description: "Pre-flight alignment check against curated values. Tests proposed work before building, designing, or deciding. Three modes: shadow (core values, 3-5 lines), standard (full check), deep (check + alignment brief)."
metadata:
  version: 1.0.0
---

# Gabe Align — Pre-Flight Alignment Check Skill

## Purpose

Test proposed work against a curated set of alignment values BEFORE building, coding, designing, or deciding. Surfaces foundational mismatches early, when they’re cheap to fix.

This is NOT a replacement for gabe-roast (which finds implementation gaps). It’s a gate that runs BEFORE detail work, checking whether the foundation is sound.

---

## Required Inputs

### 1. Mode

| Mode | Alias | Values Checked | Output | Use Case |
|------|-------|---------------|--------|----------|
| **shadow** | `sf`, `bf` | Core only (A1-A3) | 3-5 lines inline | Quick sanity check, auto-trigger in gabe-roast |
| **standard** | (default) | All Standard (A1-A7+) | Full alignment document | Before design, implementation, or non-trivial tasks |
| **deep** | `dp` | All + brief | Alignment document + alignment brief | Greenfield projects, new architectures, major decisions |

If no mode specified, default to **standard**.

### 2. Target — What to check

| Input Type | Example |
|---|---|
| **Intent** | "build a memory system for my agents" |
| **File** | `/docs/architecture.md` |
| **Folder** | `/src/services/` |
| **Task reference** | `dev-story 42`, `code-review PR-17` |
| **Context** | "this conversation" |

### Artifact Discovery

When the target references a task/story/ticket:
1. Look for `sprint-status.yaml`, `TASKS.md`, `STORIES.md`, or similar in the current project root
2. If found, parse and locate the referenced task
3. If not found, ask: "I can’t find a task tracking file. Where should I look? Or paste the task description."
4. If the task references other files (PRD, architecture doc, test plan), read those too

---

## Procedure

### Before Checking

1. Read `skills/gabe-align/VALUES.md` fully
2. Identify mode from invocation (shadow / standard / deep)
3. Identify target and context type (greenfield intent / existing artifact)
4. If existing artifact: locate and read ALL referenced files
5. If task reference: find tracking file or ask
6. If available, load the user’s cognitive profile (gabe-lens suit from `~/.claude/gabe-lens-profile.md`)

### During Checking

7. For each applicable value (based on mode tier):
   a. State the value handle
   b. Apply the test question to the target
   c. Produce verdict: PASS, CONCERN, or FAIL
   d. If CONCERN or FAIL: explain WHAT specifically is misaligned and WHY
8. Check each value independently — don’t let other results influence assessment
9. Be specific. "Violates A4" is not enough. State what’s misaligned concretely.
10. Don’t pad. If all values pass, say so. A forced CONCERN is worse than an honest PASS.
11. For code reviews: translate value violations into concrete dev concerns (missing tests, unvalidated assumptions, architectural drift)

### After Checking

12. Produce the output format for the selected mode (see Output Formats below)
13. If any value FAILs in standard or deep mode: list specific action items to resolve
14. If the check reveals a gap no existing value covers: propose a new value (see New Value Proposal)
15. If deep mode: produce the alignment brief as a standalone section
16. The alignment result IS the deliverable. Do not proceed to the task itself — the user decides next steps.

---

## Output Formats

### Shadow Mode

```
ALIGN (shadow): [target name]
A1 ✓ | A2 ⚠ [one-line concern] | A3 ✓
Status: PASS | PROCEED WITH CONCERNS | DO NOT PROCEED
```

### Standard Mode

```
GABE ALIGN: [target name]
Date: YYYY-MM-DD
Values version: X.Y.Z

VALUES CHECKED: N
PASS: X | CONCERN: Y | FAIL: Z

A1 ✓ PASS — [one-line explanation]
A2 ⚠ CONCERN — [explanation + what to do about it]
A3 ✗ FAIL — [explanation + what the alternative looks like]
...

[If new value suggested:]
SUGGESTED VALUE:
AX: "[handle]" — [guards against what]. Approve? [y/n]

ACTION ITEMS:
1. [specific action for each concern/failure]

ALIGNMENT: PROCEED | PROCEED WITH CONCERNS | DO NOT PROCEED
```

### Deep Mode

Same as Standard, plus:

```
═══ ALIGNMENT BRIEF ═══

## Intent
[Restated for clarity — what we’re trying to achieve]

## Cognitive Profile Constraints
[From gabe-lens suit. What this means for structural decisions.]

## Structural Risks
[Risks identified by value checks — what’s likely to go wrong]

## Recommended Approach
[Based on value alignment, what direction to take]

## Open Questions
[Must be resolved before designing]

## Values to Watch
[Which values are most at risk during implementation]
```

---

## New Value Proposal

When the check reveals a gap no existing value covers:

1. Surface it: "No existing value addresses [specific concern]"
2. Propose in brief format:
   ```
   AX — "[handle]"
   Guards against: [what]
   Test: "[question]"
   Violation example: [concrete]
   Alignment example: [concrete]
   Tier: [Core / Standard / Extended]
   Trigger: [what case revealed this]
   ```
3. User approves, rejects, or modifies
4. If approved: added to VALUES.md with `added:` date
5. VALUES.md version bumped (minor for Standard/Extended, major for Core)

---

## Integration with gabe-roast

Before executing any roast, gabe-roast runs a shadow alignment:

1. Read target
2. Run gabe-align shadow (core values A1-A3)
3. If all PASS: proceed to roast
4. If CONCERN: print warning, proceed
5. If FAIL: print warning + "Foundational alignment issue on [value]. Consider /gabe-align standard before roasting implementation details. Proceed? [y/n]"

---

## When to Use

**Always use for:**
- New projects or architectures (deep mode)
- Before first roast on any artifact (shadow, auto)
- Before implementing a design that hasn’t been alignment-checked
- Starting work on a new epic or major feature

**Consider using for:**
- Code reviews that touch architecture
- Sprint planning (check stories against values)
- Any decision that feels "obvious" (A2: present alternatives)

**Don’t use for:**
- Trivial bug fixes or typo corrections
- Tasks where alignment was already checked and nothing changed
- Follow-up work on an already-aligned design (unless scope changed)

---

## Example: Memory System Catch

If `/gabe-align deep "build a unified memory system"` had been run before v0.1.0:

A1 FAIL — Domain folders follow software conventions, not cognitive model
A2 FAIL — Only one structural approach presented
A3 CONCERN — Manual test planned but batch extraction scheduled before it
A4 CONCERN — Retrieval pattern doesn’t match user’s natural questions
A5 CONCERN — No roast planned for the organizing principle itself

This would have redirected to semantic/episodic/procedural BEFORE any nodes were created.
