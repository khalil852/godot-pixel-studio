---
name: godot-programmer
description: Write Godot 4.x GDScript for 2D pixel-art games. Use when the user needs gameplay logic, movement, state machines, signals, save systems, or fixes for jitter, blurry pixels, or wrong-direction input in a Godot 4 project.
---

# Godot Programmer

## Overview

You write **Godot 4.x** GDScript for 2D pixel games. Correctness targets:
pixel-perfect motion, no Godot 3 API, and data in `Resource` files rather than
hardcoded constants.

Full reference: `../../references/godot4-pixel-perfect.md`.

## Godot 4 API Rules

Never emit Godot 3 names. If you catch yourself writing any of these, stop:

| Godot 3 (wrong) | Godot 4 (correct) |
|---|---|
| `KinematicBody2D` | `CharacterBody2D` |
| `move_and_slide(velocity)` | `move_and_slide()` with `velocity` as a property |
| `yield(obj, "sig")` | `await obj.sig` |
| `export var` | `@export var` |
| `onready var` | `@onready var` |
| `instance()` | `instantiate()` |
| `PoolStringArray` | `PackedStringArray` |
| `OS.get_ticks_msec()` | `Time.get_ticks_msec()` |
| `TileMap` (new work) | `TileMapLayer` (Godot 4.3+) |
| `YSort` node | `y_sort_enabled` on the parent `Node2D` |
| `delta` in `_physics_process` as float | still a float — but use `_physics_process` for motion |

## Movement Pattern

```gdscript
extends CharacterBody2D

@export var speed: float = 70.0
@export var accel: float = 900.0
@export var friction: float = 1200.0

func _physics_process(delta: float) -> void:
    var dir := Input.get_vector("move_left", "move_right", "move_up", "move_down")
    var target := dir * speed
    var rate := accel if dir != Vector2.ZERO else friction
    velocity = velocity.move_toward(target, rate * delta)
    move_and_slide()
```

- Keep motion in `_physics_process`, never `_process`.
- Do not multiply by `delta` inside `move_and_slide()`.
- Snap the visual: when the project uses pixel snapping, keep the body's position
  integral (`position = position.round()`) after moving, so the sprite never
  lands on a half pixel.

## State Machines

Prefer an explicit enum + `match` over nested booleans, and keep transitions in
one function:

```gdscript
enum State { IDLE, RUN, JUMP, HURT }
var state: State = State.IDLE

func _set_state(next: State) -> void:
    if next == state:
        return
    state = next
    match state:
        State.IDLE: anim.play("idle")
        State.RUN:  anim.play("run")
        State.JUMP: anim.play("jump")
        State.HURT: anim.play("hurt")
```

Animation names must match the art manifest exactly. If a name is missing from
the manifest, that is a spec defect — report it rather than inventing one.

## Data as Resources

Tuning values belong in `Resource` classes, not constants scattered in scripts:

```gdscript
class_name EnemyStats
extends Resource

@export var max_health: int = 3
@export var move_speed: float = 40.0
@export var contact_damage: int = 1
```

Then `@export var stats: EnemyStats` on the enemy script. This lets the game
designer retune without touching code.

## Signals

- Declare with types: `signal died(who: Node2D)`.
- Connect in code (`sig.connect(_on_died)`) or via the editor; prefer code so the
  wiring is reviewable in a diff.
- Avoid reaching up the tree with `get_parent()` chains. Emit a signal instead.

## Common 2D Pixel Defects and Their Causes

| Symptom | Cause | Fix |
|---|---|---|
| Everything looks blurry | texture filter is Linear | set default texture filter to Nearest (project settings) |
| Pixels shimmer while camera moves | non-integer camera position | round the camera position, enable 2D pixel snapping |
| Player jitters at low speed | fractional `position` accumulating | `position = position.round()` after `move_and_slide()` |
| Wrong-direction diagonal input | using `Input.is_action_pressed` per axis | use `Input.get_vector(...)` |
| Sprite sinks into floor | collision shape larger than the visible sprite's feet | match the shape to the anchor, not the art bounds |
| Animation runs too fast/slow | `AnimatedSprite2D.speed_scale` not set | set `sprite_frames` fps on the `SpriteFrames` resource |

## Verification

Run the project headlessly to catch script errors before claiming success:

```bash
godot --headless --path <project> --quit
```

Godot prints parse errors and missing-resource errors on startup. A clean exit
with no error lines is the minimum bar. Deeper runtime checks belong to
`../pixel-qa/SKILL.md`.
