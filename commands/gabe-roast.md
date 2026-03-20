---
name: gabe-roast
description: "Adversarial gap review from a required perspective. Classifies gaps by maturity (MVP/Enterprise/Scale) and importance (Critical/High/Medium/Low) with one-liners."
---

# Gabe Roast

Adversarial gap review. Stress-tests a target from a specific perspective to surface gaps, risks, and missing pieces.

## Before Anything Else

Read the full skill definition from the gabe-roast skill (`SKILL.md`). This contains:
- The two required inputs (target + perspective)
- Classification dimensions (maturity levels + importance levels)
- Per-gap field definitions and rules
- Output format (full and brief)
- Behavior rules for before/during/after the roast
- Sequential roasting guidance
- Example output

## Inputs — Both Required

**If either input is missing, ask before proceeding. Never assume a default perspective.**

### Parsing Rule

The user provides both perspective and target as free text after the command. To parse:
- If the last argument looks like a file path, folder path, or "this conversation" / "what we discussed" — treat it as the **target** and everything before it as the **perspective**
- If ambiguous, ask the user to clarify which is which

## Modes

### Mode 1: Full (default)

**Usage:** `/gabe-roast [perspective] [target]`

Full adversarial review with all fields per gap. Steps:
1. Read the gabe-roast SKILL.md for format and behavior rules
2. Confirm both inputs are present — if missing, ask
3. Read the target fully (files, imports, referenced configs)
4. Adopt the perspective completely
5. Produce the roast in full format
6. Include the summary line

### Mode 2: Brief (`brief` | `bf`)

**Usage:** `/gabe-roast bf [perspective] [target]`

Table format. One row per gap. Sorted by maturity then importance. Steps:
1. Read the gabe-roast SKILL.md for format rules
2. Confirm both inputs — if missing, ask
3. Read the target fully
4. Adopt the perspective
5. Produce the brief table
6. Include the summary line
