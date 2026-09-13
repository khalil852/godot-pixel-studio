# Animation and sprite sheets

## Frame layout conventions

Godot's `AnimatedSprite2D` reads a `SpriteFrames` resource, which can be built
either from **individual frame images** or from a **sheet atlas**. Both work;
pick one per project and stay consistent.

### Individual frames (simplest)

```text
art/player/idle/01.png
art/player/idle/02.png
art/player/idle/03.png
art/player/idle/04.png
```

Then in `SpriteFrames`, one animation named `idle` with 4 frames. Frame **1** is
the first frame.

### Horizontal strip (best for pixel art)

Build one row per animation with `pixel_draw.py sheet`:

```bash
python ../../scripts/pixel_draw.py sheet \
  --frames art/src/idle/01.png art/src/idle/02.png art/src/idle/03.png art/src/idle/04.png \
  --out art/player/idle.png --columns 4
```

In a `SpriteFrames` atlas you then set the region per frame. Strip order must be
left-to-right with no padding unless you configure the atlas grid to match.

**Do not add margins between frames.** If the sheet has padding, every region
rect has to account for it and off-by-one errors are invisible until runtime.

## Frame-set rules

These are the invariants to verify, not preferences:

1. **Constant canvas size.** Every frame of an animation is the same pixel size.
   A frame that is 1px taller shifts the sprite and produces a visible pop.
2. **Constant anchor.** The content's bottom edge (feet) sits at the same row in
   every frame. Verify with `pixel_draw.py info` and compare bounding boxes.
3. **Constant palette and light.** A frame that uses a colour no other frame uses
   means the ramp drifted.
4. **Constant facing.** Flipping mid-set breaks readability.
5. **Specified frame count.** If the art manifest says 4 frames, ship 4. Do not
   silently ship 3 and claim a shorter animation.

## Building an animation

1. Author frame 1 as the reference pose. Render and preview it.
2. Derive the remaining frames by editing that grid — vary limb positions and
   body bob, keep the silhouette family.
3. Assemble a sheet and **look at it**:
   ```bash
   python ../../scripts/pixel_draw.py sheet --frames ... --out /tmp/check.png --columns 6
   ```
   Read the image back and check for size drift and pose popping.
4. Wire into Godot, then verify in-engine (`../skills/pixel-qa/SKILL.md`).

## Timing

- Set the animation speed on the `SpriteFrames` animation (fps), not with
  `speed_scale` hacks scattered in scripts.
- Typical pixel-game ranges: idle 4–6 fps, run 8–12 fps, attack 10–15 fps.
  Short loops read better than long ones at low frame counts.
- For events tied to a specific frame, use `AnimatedSprite2D.frame_changed` or
  `animation_finished` rather than counting time.

```gdscript
@onready var anim: AnimatedSprite2D = $Sprite

func _ready() -> void:
    anim.animation_finished.connect(_on_anim_finished)
    anim.play("attack")

func _on_anim_finished() -> void:
    _set_state(State.IDLE)
```

## Common animation defects

| Defect | Symptom in game | Cause |
|---|---|---|
| Size drift | sprite pops in size | a frame authored on a different canvas |
| Anchor drift | sprite bobs into the floor | feet row differs between frames |
| Pose popping | jerky loop | frames redrawn independently instead of derived |
| Colours flickering | palette shimmer | a frame uses an off-ramp colour |
| Wrong loop point | visible hitch when repeating | last frame duplicates frame 1 |
| Animation too fast | unreadable | fps too high for 4 frames |
