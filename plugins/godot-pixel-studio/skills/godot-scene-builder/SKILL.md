---
name: godot-scene-builder
description: Build and organize Godot 4.x scenes, node trees, tilemaps, collisions, and draw order for 2D pixel games. Use when wiring nodes, setting up TileMapLayer, fixing wrong draw order or collision layers, or structuring a project's scene folders.
---

# Godot Scene Builder

## Overview

You assemble scenes and node trees in **Godot 4.x**, wire collisions, and get
draw order right. Scene shape is architecture: a bad node tree makes later
systems painful, so prefer flat, named, single-responsibility nodes over deep
trees of unnamed `Node2D`s.

## Node Conventions

- **Name every node meaningfully.** `Player`, `Hitbox`, `Sprite`, `Camera`.
  Never leave `Node2D2`.
- **Keep collisions separate from visuals.** A `CollisionShape2D` under a
  `CharacterBody2D` may be offset from the sprite; never resize the sprite to
  match the collision.
- **One script per scene root.** Child helper scripts only when a child is
  genuinely reusable.
- Put reusable pieces in `scenes/` and instantiate them; do not duplicate node
  subtrees across levels.

### Typical 2D pixel scene tree

```text
Game (Node2D)
├── World (Node2D)
│   ├── Ground (TileMapLayer)
│   ├── Props (Node2D, y_sort_enabled = true)
│   │   ├── Player (CharacterBody2D)
│   │   │   ├── Sprite (AnimatedSprite2D)
│   │   │   ├── CollisionShape2D
│   │   │   └── Camera2D
│   │   └── Enemies (Node2D)
│   └── Walls (TileMapLayer)
└── UI (CanvasLayer)
    └── HUD
```

## Tilemaps (Godot 4.3+)

- Use **`TileMapLayer`**, one node per logical layer (ground, walls, decorations).
  The old multi-layer `TileMap` is deprecated — do not use it for new work.
- Physics comes from the **`TileSet`**: assign a physics layer on the tileset and
  set collision polygons per tile. Do not hand-place collision shapes on a
  tilemap.
- Tile size must match the art bible (commonly 16×16). A tileset whose tiles are
  15×16 will misalign the entire map.
- Import the tileset PNG with **filter off (nearest)** and no mipmaps, otherwise
  tiles bleed at their edges.

## Draw Order

Godot 4 has **no `YSort` node**. Options:

1. `Node2D.y_sort_enabled = true` on the container that holds sprites — this sorts
   children by their Y position. This is the normal choice for top-down games.
2. `z_index` for deliberate layering (UI, overlays, foreground).

Rules:

- Ensure sprites are children of the y-sorted node, not of a separate branch.
- If a sprite's origin is at its center, Y-sorting will look wrong. Set the
  sprite offset so the **origin sits at the character's feet** — this is the same
  bottom-center anchor the art manifest declares.
- Camera and UI never belong inside the y-sorted container.

## Collision Layers

Define the layer table once in `docs/` and keep it stable — renaming layers later
silently breaks every scene.

| Layer | Name | Collides with |
|---|---|---|
| 1 | world | player, enemy |
| 2 | player | world, enemy, pickup |
| 3 | enemy | world, player, player_attack |
| 4 | pickup | player |
| 5 | player_attack | enemy |

Use `set_collision_layer_value(n, true)` / `set_collision_mask_value(n, true)`
rather than raw bitmasks, so the node inspector stays readable.

## Camera

Use `Camera2D` with pixel-safe settings:

- `position_smoothing_enabled` may be on, but the final camera position must be
  rounded to whole pixels, or the whole screen shimmers.
- Set limits so the camera cannot show outside the level.
- Never scale the camera to a non-integer zoom.

## Scene File Hygiene

- `*.tscn` files are text — review the diff for accidental node renames and
  reordered `ext_resource` ids.
- Do not edit `.tscn` by hand when the structure is complex; build it in the
  editor or via a script.
- Keep `uid://` references intact when moving resources with an external tool.

## Handoff

Once scenes are assembled, hand to `../pixel-qa/SKILL.md` to verify sizes,
alignment, and draw order in a running instance before declaring the scene done.
