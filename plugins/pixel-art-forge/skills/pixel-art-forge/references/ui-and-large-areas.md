# UI and large areas

## Why UI needs different rules from sprites

A sprite is dense: every region carries feature-scale detail, and a flat 20-pixel
expanse inside a sprite is a defect. A UI element is the opposite. A panel is a
flat interior with all of its information in a border and four corners. The two
have incompatible quality criteria, which is why the audit has a `--ui` mode
rather than one set of thresholds pretending to cover both.

The practical consequence: **`audit` without `--ui` will pass a good UI panel but
for the wrong reasons**, and `audit --ui` will fail a perfectly good sprite. Use
the mode that matches the asset.

## The technique that makes UI cheap

Author one small **skin**, then scale it to any size by tiling. A 24×24 skin with
8-pixel corners becomes a 320×180 panel, and the interior stays flat and
pixel-exact because nothing is resampled.

```bash
PIX=scripts/pixel_forge.py

# one 24x24 skin
$PIX ui --kind panel --size 24x24 --ramp "$GLASS" --border 2 --bevel 2 --radius 4 --out skin.png

# any target size, corners kept 1:1, edges and centre tiled
$PIX nineslice --in skin.png --size 320x180 --corner 8 --out big_panel.png --meta big_panel.json
```

The `--meta` file carries the insets engines expect:

```json
{ "insets": { "left": 8, "top": 8, "right": 8, "bottom": 8 },
  "note": "corners 1:1, edges and centre tiled" }
```

Godot's `NinePatchRect` takes those four insets directly. Anything that reads a
nine-patch (Unity `Image` with a sprite border, CSS `border-image`, most UI
toolkits) uses the same numbers.

**Tiling, not stretching.** Stretching a 1px edge line is harmless, but stretching
a textured edge smears it into off-palette tones. Tiling repeats whole pixels, so
the result stays exact.

## Element recipes

```bash
# panel — the workhorse: flat interior, bevelled border
$PIX ui --kind panel --size 192x64 --ramp "$GLASS" --border 2 --bevel 2 --radius 6 --out panel.png

# button — same shape, four states
$PIX ui --kind button --size 96x28 --ramp "$GLASS" --border 2 --bevel 1 --state normal   --out btn_n.png
$PIX ui --kind button --size 96x28 --ramp "$GLASS" --border 2 --bevel 1 --state hover    --out btn_h.png
$PIX ui --kind button --size 96x28 --ramp "$GLASS" --border 2 --bevel 1 --state pressed  --out btn_p.png
$PIX ui --kind button --size 96x28 --ramp "$GLASS" --border 2 --bevel 1 --state disabled --out btn_d.png

# bar — frame plus fill, pct 0..1
$PIX ui --kind bar --size 160x16 --ramp "$HP_RAMP" --border 2 --pct 0.65 --out hp.png
```

- `pressed` inverts the bevel (the light edge moves to the bottom-right), which is
  the whole visual language of a pressed button. Recolour it too if your style
  calls for it.
- `disabled` desaturates toward grey while keeping the shape, so the silhouette
  still reads.
- The `--ramp` is dark→light and must have **at least 3 tones**: the darkest is the
  ink, the middle is the fill, the lightest is the lit bevel. Two tones cannot
  express a bevel.
- Everything is hardened onto the declared ramp, so UI never carries a blended
  edge. Draw-mode blending at borders is the most common way a UI ends up with
  off-palette pixels.

## Building a whole screen

A composite screen is many elements plus placement:

```bash
$PIX batch hud.txt
```

`batch` runs a script file in **one process** and prints one line. Two reasons:
this machine pays ~145 ms of Python startup per invocation, so a 20-step build
wastes ~3 s on the interpreter alone; and every separate command is another model
turn. Measured on a 20-command HUD build: **3.95 s → 0.95 s (4.1×)**, and one tool
call instead of twenty.

Batch reports only failures, formatted as `line N (command): <the real argparse
message>`. Output is suppressed for steps that succeed, so a clean run costs a
single line of context.

Place elements with `paste`; it replaces pixels rather than blending, so a button
dropped onto a panel keeps hard edges.

## Auditing UI

```bash
$PIX audit panel.png --palette forge40 --light tl --ui
```

`--ui` adds two checks that the sprite defaults cannot express:

| Check | Measures | Passes when |
|---|---|---|
| UI border thickness | the outermost opaque band on all four sides (median over the middle 60%, so rounded corners do not skew it) | the four sides agree within 1px |
| UI interior flatness | the share of the interior in one tone, and how many tones the interior uses | one tone ≥ 45% **and** ≤ 6 tones |

Both conditions are needed for flatness. A dominance test alone fails a progress
bar, whose interior is legitimately two large flat blocks (filled and empty); a
tone-count test alone fails a panel with a bevel. Together they pass panels,
buttons and bars, and fail sprites — a sprite interior typically scores ~25% in one
tone across a dozen tones.

**Scope limit, stated plainly: the flatness check applies to a single UI element,
not to a composite screen.** A full HUD contains bars, buttons and dialogs, so its
interior is legitimately busy and the check will fail. On a composite, judge border
thickness and look at the render; do not read the flatness verdict as a defect.

## Checking UI by eye when the model cannot see

A text-only model cannot look at the render, and UI failures are usually *layout*
failures — a bar that overlaps a button, a panel whose border is cut off. Neither
the audit nor an ASCII colour map catches that.

What catches it: render the screen at an integer scale and actually look at it.

```bash
$PIX preview --in hud.png --out hud_review.png --scale 3
```

If no vision is available, the honest move is to say so and hand the render to the
user for the layout judgement, rather than reporting a passing audit as if it
covered composition.
