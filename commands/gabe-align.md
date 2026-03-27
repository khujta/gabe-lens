---
name: gabe-align
description: "Pre-flight alignment check against curated values. Modes: shadow (core only), standard (all values), deep (alignment brief)."
---

# Gabe Align

Pre-flight alignment check. Tests proposed work against curated values before building.

## Before Anything Else

Read the full skill definition from the gabe-align skill (SKILL.md) and the values from VALUES.md. Both are required.

## Modes

### Mode 1: Standard (default)

**Usage:** /gabe-align [target]

Full alignment check against all Standard-tier values. Steps:

1. Read gabe-align SKILL.md for procedure and behavior rules
2. Read VALUES.md for current values and their tests
3. Identify the target (file path, intent, task reference, or "this conversation")
4. If file/folder: read it fully
5. If task reference (dev-story N, code-review N): look for sprint-status.yaml, TASKS.md, or STORIES.md. If not found, ask.
6. If available, load cognitive profile from ~/.claude/gabe-lens-profile.md
7. Run each Standard-tier value test against the target
8. Produce the standard output format
9. If gaps found, propose new value

### Mode 2: Shadow (shadow | sf | bf)

**Usage:** /gabe-align shadow [target]

Core values only. 3-5 line output. Steps:

1. Read VALUES.md Core values only (A1-A3)
2. Identify the target
3. Run each Core value test
4. Produce shadow output

### Mode 3: Deep (deep | dp)

**Usage:** /gabe-align deep [target]

Full check plus alignment brief. Steps:

1. Read gabe-align SKILL.md and VALUES.md
2. Identify the target
3. Load cognitive profile if available
4. Run all value tests (Core + Standard + applicable Extended)
5. Produce standard alignment output
6. Produce alignment brief: Intent, Cognitive Profile Constraints, Structural Risks, Recommended Approach, Open Questions, Values to Watch
