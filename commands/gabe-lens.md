---
name: gabe-lens
description: Transform technical concepts into your cognitive format — physical analogies, spatial maps, constraint boxes.
---

# Gabe Lens

Cognitive translation tool. Transforms complex technical content into a visual-spatial, analogical reasoning format.

## Before Anything Else

Read the full skill definition from the gabe-lens skill (`SKILL.md`). This contains:
- The cognitive profile (visual-spatial, conceptual-analogical, top-down constraint-driven)
- The Gabe Block template and rules for each component (including ANALOGY LIMITS)
- Compression modes (Full / Brief / Oneliner)
- When to apply / when not to apply
- Examples of well-formed Gabe Blocks

## Modes

### Mode 1: Explain — Full Block (default)

**Usage:** `/gabe-lens [concept or question]`

Transform a single concept into a full Gabe Block. Steps:

1. Read the gabe-lens SKILL.md for format rules
2. Identify the core concept from the user's input
3. Produce a single, well-formed Gabe Block with all components:
   - THE PROBLEM (purpose-first — or WHAT IT ENABLES for tool/building-block concepts)
   - THE ANALOGY (physical system)
   - THE MAP (ASCII spatial diagram)
   - CONSTRAINT BOX (IS / IS NOT / DECIDES)
   - ONE-LINE HANDLE (5-10 words, survives fatigue)
   - ANALOGY LIMITS (where the analogy breaks)
   - SIGNAL (Quick check or Deeper question)

### Mode 2: Brief (`brief` | `bf`)

**Usage:** `/gabe-lens brief [concept]` or `/gabe-lens bf [concept]`

Produce a brief Gabe Block (~40-80 tokens) — one-line handle + constraint box only. Use when space is tight or the concept has been introduced before.

1. Read the gabe-lens SKILL.md for format rules
2. Identify the core concept from the user's input
3. Produce a brief block:
   - Concept name as header
   - CONSTRAINT BOX (IS / IS NOT / DECIDES)
   - ONE-LINE HANDLE

### Mode 3: Oneliner (`oneliner` | `ol`)

**Usage:** `/gabe-lens oneliner [concept]` or `/gabe-lens ol [concept]`

Produce only the one-line handle (~5-15 tokens) — the most compressed form. Use for compaction handoffs, session re-anchoring, or when every token counts.

1. Read the gabe-lens SKILL.md for one-line handle rules
2. Identify the core concept from the user's input
3. Produce a single memorable phrase (5-10 words) that captures the essence

### Mode 4: Annotate (`annotate` | `an`)

**Usage:** `/gabe-lens annotate [file-path]` or `/gabe-lens an [file-path]`

Read a document and produce a companion file with Gabe Blocks for its key concepts. Steps:

1. Read the gabe-lens SKILL.md for format rules
2. Read the target document fully
3. Identify the 3-5 most complex or critical concepts (not trivial facts)
4. For each concept, produce a complete Gabe Block (full mode)
5. Write the companion file to the same directory as the original, named `{original-name}-gabe-lens.md`
   - Example: `docs/04-gate-audit.md` → `docs/04-gate-audit-gabe-lens.md`
6. The companion file should:
   - Reference the source document at the top
   - Present Gabe Blocks in the order they appear in the source
   - Include a brief intro explaining what this file is
