---
name: gabe-align-values
description: Curated alignment values for pre-flight checks. Tiered into Core (always), Standard (default), Extended (deep only).
version: 1.0.0
last_updated: 2026-03-27
---

# Alignment Values

## Tiers

| Tier | Scope | Checked in |
|------|-------|-----------|
| **Core** | Foundational — would have caught the memory system structural miss | Shadow, Standard, Deep |
| **Standard** | Comprehensive — covers common design and implementation pitfalls | Standard, Deep |
| **Extended** | Domain-specific — added as projects reveal new gaps | Deep (when relevant) |

---

## Core Values

### A1 — "Structure for the mind, not for the machine"

- **Guards against:** Designing around storage/software conventions instead of the user’s cognitive model
- **Test:** "Is this structure shaped by how the user thinks, or by how the technology organizes data?"
- **Violation:** Using domain-based folders (law/, tax/, software/) because that’s how wikis and documentation systems work
- **Alignment:** Using semantic/episodic/procedural because that’s how human memory retrieves information
- **Origin:** Khujta Memory v0.1.0-v0.3.0 used domain folders; Obsidian review revealed cognitive mismatch

### A2 — "Show me two roads before paving one"

- **Guards against:** Committing to the first plausible approach without presenting alternatives for foundational decisions
- **Test:** "Were at least 2 fundamentally different approaches considered for the top-level structure?"
- **Violation:** Proposing domain-folders as THE structure without mentioning memory-type or chronological or project-based alternatives
- **Alignment:** Presenting 3 structural options with trade-offs, letting the user choose based on how they think
- **Origin:** v0.1.0 architecture presented one structure as default; alternatives only emerged after the third roast

### A3 — "Touch it before you fill it"

- **Guards against:** Building at scale on an untested foundation. Skipping manual validation.
- **Test:** "Will the user physically interact with a small sample before we scale?"
- **Violation:** Auto-generating 128 nodes before the user opens the vault in Obsidian
- **Alignment:** Creating 5 manual test nodes, reviewing in the target tool, validating the format THEN automating
- **Origin:** Phase 0.5 was planned but partially skipped; structural mismatch discovered at 128 nodes instead of 5

---

## Standard Values

### A4 — "The user’s verbs, not the system’s nouns"

- **Guards against:** Organizing by WHAT things are (categories) instead of what the user DOES with them (retrieval actions)
- **Test:** "If the user asks 'how do I find X?' — does the answer follow their natural retrieval pattern?"
- **Violation:** Organizing by domain (law/, tax/) when the user thinks "what is X?" / "what happened?" / "how do I?"
- **Alignment:** Organizing by cognitive function (semantic, episodic, procedural) matching natural question types

### A5 — "Taste the architecture, not just the food"

- **Guards against:** Reviewing implementation details while accepting the foundational model unchallenged
- **Test:** "Have we challenged the foundational assumption, not just the implementation details?"
- **Violation:** Three roasts finding 31 implementation gaps but none questioning domain-based folders as the organizing principle
- **Alignment:** First review challenges the organizing principle; subsequent reviews address implementation within the validated structure

### A6 — "Who is this for at 11pm?"

- **Guards against:** Building for the fresh, focused user instead of the fatigued, scanning one
- **Test:** "Would this still work when the user is tired, distracted, or on their phone?"
- **Violation:** Nodes with dense YAML frontmatter requiring parsing to understand; diagrams that only render on desktop
- **Alignment:** Distilled views showing priorities in 3 scannable lines; mobile-friendly formats

### A7 — "The profile is the blueprint"

- **Guards against:** Having a cognitive profile (gabe-lens suit) but not applying it to structural decisions
- **Test:** "Was the user’s cognitive profile consulted for structural decisions, not just content formatting?"
- **Violation:** Using gabe-lens Gabe Blocks for content explanation but not consulting the cognitive profile when designing folder structure
- **Alignment:** Top-level structure mirrors how the cognitive profile retrieves information (top-down, function-first)

---

## Extended Values

Extended values are added as specific domains or projects reveal gaps not covered by Core and Standard.

### Adding a new Extended value

When an alignment check reveals a gap:
1. Propose using this template:
2. User approves and assigns tier
3. Add here with `added:` date and `trigger:` context
4. Bump VALUES.md version (minor for Standard/Extended, major for Core)

Template:
```
## AX — "[handle]"
- Guards against: [what]
- Test: "[question]"
- Violation: [concrete example]
- Alignment: [concrete example]
- Tier: Extended
- Added: YYYY-MM-DD
- Trigger: [what case revealed this]
```

(No extended values yet — this section grows organically)
