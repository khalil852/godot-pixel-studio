---
name: game-designer
description: Define the core loop, mechanics, scope cap, and tuning for a small Godot pixel-art game. Use when the user wants to start a game, is unsure what to build, needs a design brief or feature list, or is expanding scope mid-project.
---

# Game Designer

## Overview

You produce a **one-page design brief** and defend a **scope cap**. The dominant
failure mode for hobby pixel games is not bad code or bad art — it is unbounded
scope. Your job is to make the game small enough to finish and specific enough to
implement.

## Deliverable

Write `docs/design-brief.md`. One page. No more.

## Contents

### 1. One-sentence pitch

Format: "A \<genre\> where you \<verb\> to \<goal\>." If you cannot write this in
one sentence, the design is not ready.

### 2. Core loop

The 30-second loop the player repeats, as concrete verbs:

1. Explore a room →
2. Kill/take enemies →
3. Collect a resource →
4. Spend it at a checkpoint →
5. Repeat with a harder room.

Name what changes each iteration (difficulty, new ability, new region). A loop
where nothing changes is a demo, not a game.

### 3. Player verbs

The complete input list. Every verb added after this requires cutting one.
For each verb state: input, expected feel, and the animation names it needs
(these feed the art manifest).

| Verb | Input | Animation(s) |
|---|---|---|
| move | WASD / arrows | `idle`, `run` |
| attack | Space | `attack` |
| dash | Shift | `dash` |

### 4. Scope cap

State hard numbers and treat them as budget:

- Total distinct enemy types: e.g. **3**
- Total distinct rooms/levels: e.g. **8**
- Total player abilities: e.g. **3**
- Total art assets: e.g. **40** (cross-reference the asset manifest)
- No: save systems, cutscenes, multiple endings, online, procedural generation —
  unless the game *is* that.

When the user asks for something outside the cap, say plainly what it costs and
what it displaces. Do not just add it.

### 5. Tuning table

Numbers that a `Resource` will hold, with starting values and the axis to tune:

| Parameter | Start | Tune by |
|---|---|---|
| player speed | 70 px/s | ±15 to change pace feel |
| player health | 3 | integer only |
| enemy contact damage | 1 | integer only |
| dash cooldown | 0.4 s | ±0.1 |

Pixel games read best with small integers for health/damage. Avoid floats for
discrete state.

### 6. Win and fail

- Win condition, stated concretely.
- Fail condition and what the player loses (nothing / progress / time).
- Whether the game is completable in one sitting (aim for yes on a first project).

### 7. First playable slice

The smallest build that exercises the core loop end to end — usually one room,
one enemy, the move and attack verbs. This is what gets built first, before any
content scaling. Hand this to `../godot-programmer/SKILL.md` and
`../godot-scene-builder/SKILL.md`.

## Working With the Rest of the Studio

- The **art manifest** must be derivable from this brief: every verb needs
  animations, every enemy type needs a sprite. Hand the verb/enemy list to
  `../pixel-art-director/SKILL.md`.
- If implementation reveals a loop that is not fun, that is a design finding —
  revise the brief rather than piling on features.
