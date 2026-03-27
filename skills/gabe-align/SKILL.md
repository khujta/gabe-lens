---
name: gabe-align
description: "Pre-flight alignment check against curated values. Tests proposed work before building, designing, or deciding."
metadata:
  version: 1.0.0
---

# Gabe Align -- Pre-Flight Alignment Check Skill

## Purpose

Test proposed work against a curated set of alignment values BEFORE building, coding, designing, or deciding. Surfaces foundational mismatches early, when they are cheap to fix.

This is NOT a replacement for gabe-roast (which finds implementation gaps). It is a gate that runs BEFORE detail work, checking whether the foundation is sound.

---

## Required Inputs

### 1. Mode

| Mode | Alias | Values Checked | Output | Use Case |
|------|-------|---------------|--------|----------|
| shadow | sf, bf | Core only A1-A3 | 3-5 lines inline | Quick sanity, auto-trigger in gabe-roast |
| standard | default | All Standard A1-A7+ | Full alignment document | Before design, implementation, non-trivial tasks |
| deep | dp | All + brief | Alignment doc + alignment brief | Greenfield projects, new architectures |

If no mode specified, default to standard.

### 2. Target -- What to check

| Input Type | Example |
|---|---|
| Intent | "build a memory system for my agents" |
| File | /docs/architecture.md |
| Folder | /src/services/ |
| Task reference | dev-story 42, code-review PR-17 |
| Context | "this conversation" |

### Artifact Discovery

When the target references a task/story/ticket:
1. Look for sprint-status.yaml, TASKS.md, STORIES.md, or similar in the current project root
2. If found, parse and locate the referenced task
3. If not found, ask: "I cannot find a task tracking file. Where should I look? Or paste the task description."
4. If the task references other files (PRD, architecture doc, test plan), read those too

---

## Procedure

### Before Checking

1. Read skills/gabe-align/VALUES.md fully
2. Identify mode from invocation (shadow / standard / deep)
3. Identify target and context type (greenfield intent / existing artifact)
4. If existing artifact: locate and read ALL referenced files
5. If task reference: find tracking file or ask
6. If available, load cognitive profile from ~/.claude/gabe-lens-profile.md

### During Checking

7. For each applicable value (based on mode tier):
   a. State the value handle
   b. Apply the test question to the target
   c. Produce verdict: PASS, CONCERN, or FAIL
   d. If CONCERN or FAIL: explain WHAT specifically is misaligned and WHY
8. Check each value independently
9. Be specific. "Violates A4" is not enough. State what is misaligned concretely.
10. Do not pad. If all values pass, say so. A forced CONCERN is worse than an honest PASS.
11. For code reviews: translate violations into concrete dev concerns (missing tests, unvalidated assumptions, drift)

### After Checking

12. Produce the output format for the selected mode
13. If any value FAILs: list specific action items
14. If gap found no existing value covers: propose a new value
15. If deep mode: produce alignment brief
16. The alignment result IS the deliverable. Do not proceed to the task -- user decides next steps.

---

## Output Formats

### Shadow Mode

ALIGN (shadow): [target name]
A1 check | A2 check | A3 check
Status: PASS | PROCEED WITH CONCERNS | DO NOT PROCEED

### Standard Mode

GABE ALIGN: [target name]
Date: YYYY-MM-DD
Values version: X.Y.Z

VALUES CHECKED: N
PASS: X | CONCERN: Y | FAIL: Z

Per-value results with one-line explanations.
Action items for concerns and failures.
New value suggestions if gaps found.
Final alignment verdict.

### Deep Mode

Same as Standard, plus an Alignment Brief with:
- Intent (restated for clarity)
- Cognitive Profile Constraints (from gabe-lens suit)
- Structural Risks (identified by value checks)
- Recommended Approach (based on value alignment)
- Open Questions (must resolve before designing)
- Values to Watch (most at risk during implementation)

---

## New Value Proposal

When the check reveals a gap no existing value covers:
1. Surface it: "No existing value addresses [specific concern]"
2. Propose: AX -- "[handle]", Guards against, Test, Violation example, Alignment example, Tier
3. User approves, rejects, or modifies
4. If approved: added to VALUES.md, version bumped

---

## Integration with gabe-roast

Before executing any roast, gabe-roast runs a shadow alignment:
1. Read target
2. Run gabe-align shadow (core values A1-A3)
3. All PASS: proceed to roast
4. CONCERN: print warning, proceed
5. FAIL: warn + recommend /gabe-align standard before roasting. Ask to proceed.

---

## When to Use

Always use for: new projects/architectures (deep), before first roast (shadow auto), before implementing unchecked designs, starting new epics.

Consider for: code reviews touching architecture, sprint planning, decisions that feel "obvious" (A2).

Do not use for: trivial bug fixes, already-aligned work with no scope change.
