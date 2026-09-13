---
name: godot-pixel-studio
description: Route Godot 4.x 2D pixel-art game work to the right studio role. Use when the user wants to start, plan, or continue a pixel-art game in Godot and it is not yet clear which discipline should lead, or when a request spans design, art, code, scenes, and QA at once.
---

# Godot Pixel Studio

## Overview

This is the umbrella entrypoint for **Godot 4.x 2D pixel-art** game work.
It works like a small studio: this skill acts as the director, decides which
discipline leads, then hands off to a specialist role skill.

Order of operations matters. Do not start writing GDScript before the art
direction and gameplay loop are pinned down — that is how pixel projects drift
into inconsistent art and un-shippable scope.

## Studio Roles

| Role skill | Leads when |
|---|---|
| `../game-designer/SKILL.md` | Core loop, mechanics, scope, tuning are undefined |
| `../pixel-art-director/SKILL.md` | No art bible yet: palette, base resolution, asset spec |
| `../pixel-artist/SKILL.md` | Actual sprites/tiles need to be drawn |
| `../godot-programmer/SKILL.md` | GDScript gameplay systems and logic |
| `../godot-scene-builder/SKILL.md` | Scenes, node trees, tilemaps, collisions, Y-sorting |
| `../pixel-qa/SKILL.md` | Verify in-engine: sizes, alignment, animation, screenshots |

## Default Studio Workflow

1. **Design brief** — `game-designer` writes the one-page loop and a hard scope cap.
2. **Art bible** — `pixel-art-director` fixes base resolution, palette, and the
   exact asset list with pixel dimensions. Nobody draws before this exists.
3. **Art production** — `pixel-artist` draws every asset with
   `../../scripts/pixel_draw.py`. All art is authored as deterministic character
   grids, not generated images.
4. **Implementation** — `godot-programmer` writes GDScript against the agreed
   asset names and dimensions.
5. **Scene assembly** — `godot-scene-builder` wires nodes, tilemaps, collisions.
6. **QA gate** — `pixel-qa` runs the project and reports concrete defects.

Steps 3–6 iterate in small loops. After each loop, re-run the QA gate.

## Non-negotiable Rules

- **Target Godot 4.x.** Do not emit Godot 3 API (`KinematicBody2D`, `yield`,
  `TileMap` for new work, `PoolStringArray`). See
  `../../references/godot4-pixel-perfect.md`.
- **All pixel art goes through `pixel_draw.py`.** Never hand-write PNG bytes and
  never substitute an image-generation model for authored pixel art — the result
  will not be grid-aligned or palette-consistent.
- **One palette per project.** Take it from `pixel_draw.py palettes` or define a
  custom legend once, then reuse it for every asset.
- **Integer scale only.** Base resolution is small (often 320×180 or 384×216);
  display scaling is integer. Never non-integer scaling, never texture filtering.
- **Every asset has a declared pixel size and anchor.** Sprite frames that change
  size between frames are a defect.
- **Files on disk are the source of truth.** Keep art specs under `docs/` so a
  later session can resume without guessing.

## Do Not Stay Here When

- The user already named the discipline ("draw me a tileset" → `pixel-artist`;
  "why does my player jitter" → `godot-programmer`).
- The request is purely a Godot import-settings question → answer from
  `../../references/godot4-pixel-perfect.md` directly.
