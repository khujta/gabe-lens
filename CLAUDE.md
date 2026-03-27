# Gabe Lens -- Project Context

Cognitive toolkit for Claude Code. A growing collection of skills that transform how you understand, review, and decide.

## Project Structure

```
gabe_lens/
  skills/
    gabe-lens/
      SKILL.md              -- Cognitive translation (Gabe Blocks)
      SUITS.md              -- 4 cognitive suit definitions for calibration
    gabe-roast/
      SKILL.md              -- Adversarial gap review
    gabe-align/
      SKILL.md              -- Pre-flight alignment check
      VALUES.md             -- Curated alignment values (tiered, versioned)
  commands/
    gabe-lens.md            -- /gabe-lens command
    gabe-lens-calibrate.md  -- /gabe-lens-calibrate command
    gabe-roast.md           -- /gabe-roast command
    gabe-align.md           -- /gabe-align command
  assets/                   -- Images for README
  README.md                 -- Public-facing documentation
  CLAUDE.md                 -- This file
```

## User Profile

`~/.claude/gabe-lens-profile.md` -- stores the user's chosen cognitive suit. Created by `/gabe-lens-calibrate`. If absent, default suit (Spatial-Analogical) is used.

## Conventions

- Each skill has its own directory under `skills/` with a `SKILL.md`
- Each skill has a matching command file under `commands/`
- Command files are lean -- they reference the SKILL.md for rules, not duplicate them
- Skills are independent but may reference each other (gabe-roast uses gabe-lens one-liner format, gabe-roast auto-triggers gabe-align shadow)

## Current Skills

| Skill | Version | Purpose |
|---|---|---|
| **gabe-lens** | 2.1.0 | Transforms concepts into analogies, maps, constraint boxes, handles. Adapts to cognitive suit. |
| **gabe-roast** | 1.0.0 | Adversarial gap review from a required perspective, classified by maturity + importance |
| **gabe-align** | 1.0.0 | Pre-flight alignment check against curated values. Three modes: shadow, standard, deep. |

## Commands

| Command | Skill | Purpose |
|---|---|---|
| `/gabe-lens` | gabe-lens | Explain a concept (full, brief, oneliner, annotate) |
| `/gabe-lens-calibrate` | gabe-lens | Discover your cognitive suit (interactive, one-time) |
| `/gabe-roast` | gabe-roast | Adversarial gap review (full, brief). Auto-runs shadow alignment gate. |
| `/gabe-align` | gabe-align | Pre-flight alignment check (shadow, standard, deep) |

## Skill Interactions

- **gabe-roast** auto-triggers **gabe-align shadow** before every roast (Pre-Roast Alignment Gate)
- **gabe-roast** uses **gabe-lens** one-liner format for gap handles
- **gabe-align** loads cognitive profile from **gabe-lens** calibration if available

## Adding a New Skill

1. Create `skills/<skill-name>/SKILL.md` with frontmatter (name, description, version)
2. Create `commands/<skill-name>.md` with frontmatter (name, description)
3. Add to the Skills table in README.md
4. Update this CLAUDE.md
