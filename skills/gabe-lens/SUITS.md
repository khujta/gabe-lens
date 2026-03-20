---
name: gabe-lens-suits
description: Cognitive suit definitions for Gabe Lens calibration. Each suit adapts how Gabe Blocks are written to match a cognitive archetype.
---

# Gabe Lens — Cognitive Suits

Four cognitive archetypes that determine HOW Gabe Blocks are written. The block structure stays the same (PROBLEM, ANALOGY, MAP, CONSTRAINT BOX, HANDLE, LIMITS, SIGNAL) — what changes is the style, language, and emphasis within each section.

---

## Suit 1: Spatial-Analogical (default)

**Profile:** Thinks in 3D space. Reasons through physical metaphors. Grasps concepts by mapping them to tangible systems.

**How each section adapts:**

| Section | Style |
|---|---|
| THE PROBLEM | Concrete scenario — what breaks, what fails |
| THE ANALOGY | Physical system (mechanical, fluid, optical, etc.) visualizable in 3D space. Captures the key trade-off. |
| THE MAP | ASCII spatial diagram — boxes, arrows, layers. Top = high-level, bottom = implementation. |
| CONSTRAINT BOX | IS / IS NOT / DECIDES — everyday language, prevents overthinking |
| ONE-LINE HANDLE | Physical metaphor, 5-10 words, survives fatigue. "Hooks are gravity — docs are speed limit signs" |
| ANALOGY LIMITS | When the physical analogy stops mapping to reality |

**Best for:** People who say "show me a diagram," who gesture while explaining, who think "it's like a..." before they think "it's defined as..."

**Example handle:** "The refrigerator door opens every 27 minutes"

---

## Suit 2: Sequential-Procedural

**Profile:** Thinks in steps and processes. Grasps concepts by understanding the sequence of events and decision points. Wants to know what happens first, then next, then after.

**How each section adapts:**

| Section | Style |
|---|---|
| THE PROBLEM | What goes wrong when steps are skipped or out of order |
| THE ANALOGY | Process/workflow analogy — assembly line, recipe, protocol. Emphasizes order and dependencies. |
| THE MAP | Flowchart or sequence diagram — numbered steps, decision diamonds, branches. Time flows top to bottom. |
| CONSTRAINT BOX | DOES / DOES NOT DO / DECIDES WHEN — framed as actions and boundaries |
| ONE-LINE HANDLE | Process description, 5-10 words. "Validate before you persist, never after" |
| ANALOGY LIMITS | When the process analogy breaks because real execution isn't linear |

**Best for:** People who say "walk me through it," who outline before writing, who debug by tracing execution step by step.

**Example handle:** "Check the lock before you open the door, not after you walk through"

---

## Suit 3: Abstract-Structural

**Profile:** Thinks in patterns, types, and relationships. Grasps concepts by understanding what category something belongs to, how it relates to other concepts, and what rules govern it. Comfortable with formal constraints.

**How each section adapts:**

| Section | Style |
|---|---|
| THE PROBLEM | What category of problem this addresses — the general class, not just one scenario |
| THE ANALOGY | Pattern/type relationship — "X is a special case of Y," "X and Y are both instances of Z." Uses mathematical intuition without notation. |
| THE MAP | Hierarchy or classification diagram — parent/child, implements/extends, contains/references. Shows type relationships. |
| CONSTRAINT BOX | IS A / IS NOT A / DISTINGUISHES — framed as classification and boundaries |
| ONE-LINE HANDLE | Formal relationship, 5-10 words. "Every cache is a trade: space for time" |
| ANALOGY LIMITS | When the structural analogy oversimplifies — real systems don't fit clean hierarchies |

**Best for:** People who say "what's the general principle?", who think in taxonomies, who reach for abstractions before examples.

**Example handle:** "Authentication proves who; authorization proves what"

---

## Suit 4: Narrative-Contextual

**Profile:** Thinks in stories and scenarios. Grasps concepts by imagining a person in a situation, facing a choice, dealing with consequences. Learns through cause-and-effect chains with characters.

**How each section adapts:**

| Section | Style |
|---|---|
| THE PROBLEM | A story: a specific person hits a specific wall. "A developer pushes to prod and..." |
| THE ANALOGY | Scenario with characters — "Imagine you're the librarian and someone asks for a book that..." Uses everyday situations, not technical metaphors. |
| THE MAP | Cause-effect chain or timeline — "User does X → system does Y → Z happens → user sees W." Shows the journey, not the architecture. |
| CONSTRAINT BOX | WHO / WHAT THEY CAN'T / WHAT THEY CHOOSE — framed as character constraints and decisions |
| ONE-LINE HANDLE | Scenario summary, 5-10 words. "The librarian can't read every book she shelves" |
| ANALOGY LIMITS | When the story oversimplifies — real systems don't have single characters making single decisions |

**Best for:** People who say "give me an example," who learn from case studies, who remember stories better than diagrams.

**Example handle:** "The new hire follows the map; the veteran smells the smoke"

---

## Calibration: Same Concept, Four Suits

Here is "caching" explained as a one-liner in each suit, to show how the same concept feels different:

| Suit | One-liner |
|---|---|
| Spatial-Analogical | "A fridge next to the stove — cold storage one arm's reach away" |
| Sequential-Procedural | "Check the shelf before you walk to the warehouse" |
| Abstract-Structural | "Every cache is a trade: space for time" |
| Narrative-Contextual | "The barista remembers your order — no menu needed" |

Same concept, four different brains.
