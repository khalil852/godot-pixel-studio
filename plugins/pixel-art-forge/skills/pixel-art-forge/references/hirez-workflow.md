# Constructing a higher-resolution asset

This is the order that works. It follows the same principle each time: **decide
the thing that constrains everything else first**, then build under that
constraint.

## 0. Decide the numbers before drawing

Write these down, because every later command references them:

| Decision | Typical | Why it must come first |
|---|---|---|
| Canvas size | 64×64, 96×96 | Determines how much detail is even possible |
| Palette | 16–32 colours | `ramp`, `snap` and `audit` all need it |
| Block size | 2 at 64px, 1 at 32px | Sets the smallest feature; cannot change later without redrawing |
| Light | `tl` | Every `shade`/`outline` call must agree |
| Outline | full, or light-side | Affects how assets sit on backgrounds |

A 64px sprite with a 2px block has an effective working grid of 32×32. That is
the real resolution limit you are designing against — worth knowing before you
try to draw something with 1px eyelashes.

## 1. Pull real ramps from the palette

```bash
SKIN=$(pixel_forge.py ramp --from "#2b1610" --to "#ffe1bd" --steps 5 --palette forge32)
```

Use 3 steps for small masses, 4–5 for large ones. If the tool warns that the ramp
is not monotone in luminance, you passed two ends from *different* ramps in the
palette — pick both ends from the same ramp block.

## 2. Block the silhouette, back to front

Draw the parts that are behind first. Each `shape` call hardens its own layer and
composites pixel-exactly, so later shapes sit on top cleanly rather than blending.

```bash
pixel_forge.py canvas --size 64x64 --out hero.png
pixel_forge.py shape --in hero.png --out hero.png --kind rrect --box 24,42,6,18 \
    --radius 2 --color "#31363f"          # far leg
pixel_forge.py shape --in hero.png --out hero.png --kind rrect --box 34,42,6,18 \
    --radius 2 --color "#31363f"          # near leg
pixel_forge.py shape --in hero.png --out hero.png --kind rrect --box 20,26,24,22 \
    --radius 6 --color "${CLOTH%%,*}"     # torso, starting at the ramp's dark end
pixel_forge.py shape --in hero.png --out hero.png --kind ellipse --box 22,8,20,20 \
    --color "${SKIN%%,*}"                 # head
```

Always start a mass at the **dark end** of its ramp. `shade` replaces pixels of
that exact colour, so the initial fill doubles as the selection mask.

**Check the silhouette before shading.** Fill everything with a flat mid-tone,
preview it, and confirm the shape reads. Shading a bad silhouette just makes a bad
silhouette with nicer colours.

## 3. Shade one material at a time

```bash
pixel_forge.py shade --in hero.png --out hero.png --ramp "$SKIN"  --light tl \
    --color "${SKIN%%,*}"
pixel_forge.py shade --in hero.png --out hero.png --ramp "$CLOTH" --light tl \
    --color "${CLOTH%%,*}"
```

`--color` is not optional in practice. It restricts the depth field to that
material, so the head is shaded by the head's own form. Without it, one field is
computed across the whole silhouette and each part's shading is distorted by the
others' bulk — the classic "melted" look.

Light comes from the declared side, so the side nearest the light gets the
brightest ramp step and the deepest interior gets the darkest. The tool
auto-orients the ramp for you.

## 4. Outline

```bash
pixel_forge.py outline --in hero.png --out hero.png --color "#101216" --mode full
```

Use `--mode light` for a selective outline that only annotates the shadow side —
it reads as more rendered, and it lets the lit edge blend into bright backgrounds.
Whichever you choose, use it for every asset in the project.

## 5. Force one feature scale

```bash
pixel_forge.py blocksnap --in hero.png --out hero.png --block 2
```

This is the step people skip and then wonder why the result still looks cheap.
Curved primitives produce 1px staircase corners; `blocksnap` folds them into the
project's unit. Expect the curve to get chunkier — that is the point. If the
silhouette loses too much, either accept a larger canvas or design shapes that
survive the block size.

## 6. Clear the noise, then lock the palette

```bash
pixel_forge.py clean --in hero.png --out hero.png --min-neighbors 2
pixel_forge.py snap  --in hero.png --out hero.png --palette forge32
```

Order matters: `clean` decides which pixels are noise from their neighbourhood, so
running it before `snap` avoids treating blend artefacts as real detail.

## 7. Gate and review

```bash
pixel_forge.py audit hero.png --palette forge40 --light tl     --material "$SKIN" --material "$CLOTH" --material "$NEUT"
pixel_forge.py preview --in hero.png --out review.png --scale 5 --grid-lines
```

Pass every ramp as a `--material` so the light check is judged against declared
materials rather than guessed from colour.

Review at integer scale with the pixel grid on — that is how the asset will be
seen in a pixel-perfect game, and it is the only way to spot a one-pixel error.

If a check fails, fix the cause rather than the measurement:

| Failing check | Almost always caused by |
|---|---|
| palette drift | a hex you typed by hand instead of taking from the palette |
| anti-alias suspects | a shape drawn outside the palette, or an external image |
| isolated pixels | speckle left by `blocksnap` at radius corners—run `clean` again |
| banded shading | ramp steps taken from two different palette ramps |
| light consistency | one `shade` call with the wrong `--light` |
| silhouette jitter | `blocksnap` too small for the shapes you drew |

## Worked example

A 64×64 character built exactly as above: **14 colours, all on palette, 0
anti-alias suspects, 0 isolated pixels, 0 silhouette jitter, light bias +17.3px
toward the declared side, 8/8 audit checks passed.**
