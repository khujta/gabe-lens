---
name: gabe-lens-calibrate
description: Discover which cognitive suit fits you best. Presents the same concept in 4 styles — you pick the one that clicks.
---

# Gabe Lens Calibrate

Interactive calibration to find which cognitive suit matches how you think. The result is saved globally so all future `/gabe-lens` output adapts to your style.

## Before Anything Else

Read the suit definitions from `skills/gabe-lens/SUITS.md`. This contains:
- The 4 cognitive archetypes (Spatial-Analogical, Sequential-Procedural, Abstract-Structural, Narrative-Contextual)
- How each suit adapts every section of a Gabe Block
- A quick comparison table of the same concept in all 4 suits

## How Calibration Works

### Step 1: Pick a concept

Present 3 concept options at different complexity levels. The user picks one:

- **Simple:** "Caching"
- **Medium:** "Event-driven architecture"
- **Complex:** "Consensus algorithms"

If the user says "surprise me" or doesn't choose, use the medium option.

If the user wants to calibrate with their OWN concept, accept it — the calibration works with any concept.

### Step 2: Generate 4 Gabe Blocks

For the chosen concept, produce a FULL Gabe Block in each of the 4 suits. Label each clearly:

```
═══ SUIT A: Spatial-Analogical ═════════════════════════
[Full Gabe Block in Spatial-Analogical style]

═══ SUIT B: Sequential-Procedural ═════════════════════
[Full Gabe Block in Sequential-Procedural style]

═══ SUIT C: Abstract-Structural ═══════════════════════
[Full Gabe Block in Abstract-Structural style]

═══ SUIT D: Narrative-Contextual ═══════════════════════
[Full Gabe Block in Narrative-Contextual style]
```

### Step 3: User picks

Ask the user:

> Which one clicked fastest? You can pick one, or rank your top 2.
> If none felt right, tell me what was missing and we can adjust.

### Step 4: Save profile

Write the selected suit to `~/.claude/gabe-lens-profile.md`:

```markdown
---
suit: spatial-analogical
calibrated: 2026-03-20
concept-used: event-driven architecture
---

# Gabe Lens Profile

Active suit: **Spatial-Analogical**

To recalibrate: `/gabe-lens-calibrate`
To reset to default: `/gabe-lens-calibrate reset`
```

Valid suit values: `spatial-analogical`, `sequential-procedural`, `abstract-structural`, `narrative-contextual`

### Reset to Default

**Usage:** `/gabe-lens-calibrate reset`

If the user says "reset" or "default":
1. Delete `~/.claude/gabe-lens-profile.md` if it exists
2. Confirm: "Profile reset. Gabe Lens will use the default suit (Spatial-Analogical)."

Do NOT run the full calibration flow for a reset.

## Rules

- Each suit block must be a COMPLETE Gabe Block — all sections present. Don't abbreviate.
- The goal is for the user to FEEL the difference, not analyze it. Let the blocks speak for themselves.
- If the user picks two suits, save the primary one. Note the secondary in the profile as a comment.
- If the user says "they're all good" or can't decide, suggest they try the medium concept in a different domain (e.g., cooking, law, music) to tease out the difference.
- Calibration is a one-time thing. The profile persists across sessions.
