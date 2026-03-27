---
name: gabe-align-values
description: Curated alignment values for pre-flight checks. Tiered into Core, Standard, Extended.
version: 1.0.0
last_updated: 2026-03-27
---

# Alignment Values

## Tiers

| Tier | Scope | Checked in |
|------|-------|-----------|
| Core | Foundational -- catches structural mismatches | Shadow, Standard, Deep |
| Standard | Comprehensive -- covers common design and implementation pitfalls | Standard, Deep |
| Extended | Domain-specific -- added as projects reveal new gaps | Deep when relevant |

---

## Core Values

### A1 -- "Structure for the mind, not for the machine"

- **Guards against:** Designing around storage/software conventions instead of the user cognitive model
- **Test:** "Is this structure shaped by how the user thinks, or by how the technology organizes data?"
- **Violation:** Using domain-based folders because that is how wikis work
- **Alignment:** Using semantic/episodic/procedural because that is how human memory retrieves
- **Origin:** Khujta Memory v0.1-v0.3 used domain folders; Obsidian review revealed cognitive mismatch

### A2 -- "Show me two roads before paving one"

- **Guards against:** Committing to the first plausible approach without presenting alternatives for foundational decisions
- **Test:** "Were at least 2 fundamentally different approaches considered for the top-level structure?"
- **Violation:** Proposing domain-folders as THE structure without alternatives
- **Alignment:** Presenting 3 structural options with trade-offs, user chooses
- **Origin:** v0.1 presented one structure; alternatives only emerged after the third roast

### A3 -- "Touch it before you fill it"

- **Guards against:** Building at scale on an untested foundation. Skipping manual validation.
- **Test:** "Will the user physically interact with a small sample before we scale?"
- **Violation:** Auto-generating 128 nodes before user opens the vault
- **Alignment:** Creating 5 manual test nodes, reviewing, validating, THEN automating
- **Origin:** Phase 0.5 was planned but skipped; mismatch discovered at 128 nodes instead of 5

---

## Standard Values

### A4 -- "The user verbs, not the system nouns"

- **Guards against:** Organizing by WHAT things are instead of what the user DOES with them
- **Test:** "If the user asks how do I find X -- does the answer follow their natural retrieval pattern?"
- **Violation:** Organizing by domain when the user thinks in what/when/how questions
- **Alignment:** Organizing by cognitive function matching natural question types

### A5 -- "Taste the architecture, not just the food"

- **Guards against:** Reviewing implementation details while accepting the foundational model unchallenged
- **Test:** "Have we challenged the foundational assumption, not just the implementation details?"
- **Violation:** Three roasts finding 31 implementation gaps but none questioning the organizing principle
- **Alignment:** First review challenges the organizing principle; subsequent reviews address implementation

### A6 -- "Who is this for at 11pm?"

- **Guards against:** Building for the fresh focused user instead of the fatigued scanning one
- **Test:** "Would this still work when the user is tired, distracted, or on their phone?"
- **Violation:** Dense YAML frontmatter requiring parsing; desktop-only diagram rendering
- **Alignment:** Distilled views showing priorities in 3 scannable lines; mobile-friendly formats

### A7 -- "The profile is the blueprint"

- **Guards against:** Having a cognitive profile but not applying it to structural decisions
- **Test:** "Was the cognitive profile consulted for structural decisions, not just content formatting?"
- **Violation:** Using gabe-lens for content but not consulting cognitive profile for folder structure
- **Alignment:** Top-level structure mirrors how the cognitive profile retrieves information

---

## Extended Values

Extended values are added as projects reveal gaps not covered by Core and Standard.

### Adding a new Extended value

When an alignment check reveals a gap:
1. Propose: AX -- "[handle]", Guards against, Test, Violation, Alignment, Tier, Added date, Trigger
2. User approves and assigns tier
3. Add here, bump VALUES.md version

No extended values yet -- this section grows organically.
