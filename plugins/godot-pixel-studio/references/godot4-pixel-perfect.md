# Godot 4 pixel-perfect setup

Reference for pixel-art 2D projects in **Godot 4.x**. Setting paths below are the
Godot 4 project-setting keys; if a key is not found in a newer minor, search the
same wording in **Project → Project Settings** — the paths are stable across 4.x
but a few have been renamed between minors.

## Project settings

| Setting | Value | Why |
|---|---|---|
| `rendering/textures/canvas_textures/default_texture_filter` | **Nearest** | Linear filtering blurs every sprite. This is the single most common cause of "my pixel art looks blurry". |
| `display/window/size/viewport_width` | e.g. `320` | Internal resolution. Small base = crisp integer scaling. |
| `display/window/size/viewport_height` | e.g. `180` | 320×180 is 16:9 and pairs cleanly with 16×16 tiles. |
| `display/window/stretch/mode` | `canvas_items` | See tradeoff below. |
| `display/window/stretch/aspect` | `keep` | Prevents the aspect ratio from distorting pixels. |
| `display/window/stretch/scale_mode` | `integer` (4.2+) | Forces whole-number scaling so pixels stay square. |
| `rendering/2d/snap/snap_2d_transforms_to_pixel` | `true` | Rounds node transforms to whole pixels. |
| `rendering/2d/snap/snap_2d_vertices_to_pixel` | `true` | Rounds polygon vertices. |
| `rendering/anti_aliasing/quality/msaa_2d` | `Disabled` | MSAA softens edges — the opposite of what pixel art wants. |

### `canvas_items` vs `viewport` stretch mode

- **`canvas_items`** — the canvas renders at window resolution but positions are
  scaled. Camera motion can be smooth (non-integer), UI can render at native
  resolution, and text stays sharp. Recommended default for most pixel games.
  Risk: sub-pixel camera motion can shimmer, so round the camera position.
- **`viewport`** — renders the whole frame at the low base resolution and scales
  it up. Truly pixel-perfect by construction, but *everything* including UI is
  blocky and you cannot have sub-pixel positions at all. Choose this only when
  you want hard pixel-locked motion.

Pick one deliberately. Mixing expectations (smooth camera in `viewport` mode) is a
frequent source of confusion.

## Texture import settings

For every pixel-art PNG, in the **Import** dock:

- **Filter** → off (nearest). Project default covers new imports; re-import
  existing files if the default was changed later.
- **Mipmaps** → off. Mipmaps cause size-dependent blurring.
- **Fix Alpha Border** → on for sprites with hard edges, to avoid dark fringing
  from transparent pixels bleeding in.

Per-node override when you cannot change the import:

```gdscript
# GDScript
sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
```

## Camera

Pixel-safe camera behaviour:

```gdscript
extends Camera2D

func _process(_delta: float) -> void:
    # Smooth follow is fine, but the final position must be integral.
    position = get_parent().position.round()
```

- Enable `position_smoothing_enabled` only if you round afterwards.
- Set `limit_left/right/top/bottom` so the camera never shows outside the level,
  which exposes the background colour as a strip.
- Do **not** use a non-integer `zoom`. If you need to zoom, use integer values
  (2, 3, 4) or adjust the base resolution instead.

## Movement and the sub-pixel problem

Physics bodies move in floats. Convert to whole pixels before drawing:

```gdscript
func _physics_process(delta: float) -> void:
    velocity = velocity.move_toward(target_velocity, accel * delta)
    move_and_slide()
    position = position.round()   # keeps the sprite on whole pixels
```

Without the final `round()`, a body at x = 10.4 draws a blurred or wobbling
sprite even with nearest filtering, because the vertex positions are fractional.

## Sprite origins and anchors

- Set the sprite/animation origin at the character's **feet (bottom-center)** for
  top-down and platformer games. Y-sorting and collision both assume this.
- Enable `centered = false` and set `offset` explicitly when you need the origin
  at a corner.
- Never let an animation change the origin between frames.

## Common symptoms → causes

| Symptom | Cause |
|---|---|
| Blurry sprites everywhere | default texture filter is Linear |
| Blurry after adding a new asset | that PNG was imported with the old filter setting |
| Everything shimmers while moving | camera at fractional position |
| One sprite jitters at low speed | `position` not rounded after `move_and_slide()` |
| Tiles show 1px seams | tileset tile size ≠ art-bible tile size, or mipmaps on |
| Dark fringe around sprites | alpha bleeding — enable Fix Alpha Border, or author with a clean alpha edge |
| UI text is blurry | TTF font in a pixel project — use a bitmap font |
| Non-square pixels when the window is resized | stretch aspect not `keep`, or scale mode not `integer` |
