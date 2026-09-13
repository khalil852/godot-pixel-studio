# Palette and shading

## Why a fixed palette matters

Pixel art reads as coherent because the *entire game* draws from one colour set.
When each sprite invents its own colours, the result looks like a collage even
though every individual sprite is competent. Fix the palette once, in the art
bible, and treat it as a constraint rather than a suggestion.

## Choosing a palette

Built-ins available in the tool:

```bash
python ../../scripts/pixel_draw.py palettes
python ../../scripts/pixel_draw.py palette sweetie16
```

| Name | Colors | Character |
|---|---|---|
| `pico8` | 16 | Saturated, high contrast, classic fantasy look |
| `sweetie16` | 16 | Softer, lower contrast, good for cozy styles |
| `gameboy` | 4 | 4-shade green; extremely restrictive, very cohesive |
| `1bit` | 2 | Black and white only; maximum style pressure |

A 4-colour palette is a legitimate choice and often produces a better-looking
first game than 16 colours used carelessly.

## The shading ramp

Pick **3–4 palette entries per material** and use the same ramp everywhere:

```text
shadow  →  base  →  highlight      (3 tones)
shadow  →  mid  →  base  →  highlight   (4 tones)
```

Rules:

- **One light direction** for the whole project. Top-left is the common default.
  Light direction is a project-wide decision, not a per-sprite one.
- **Skip a step, not a shake.** Use the ramp in order. Do not put the highlight
  next to the shadow with no mid tone.
- **Highlight where the light hits**, not as an outline. Highlights along the
  light-facing top/left edges; shadows on the bottom/right and under overhangs.
- **Larger masses get more ramp steps than small details.** A 8×8 coin needs 3
  tones; a 32×32 boss can carry 4.

## Anti-aliasing is banned

Do not soften edges with intermediate colours. In pixel art, a hard edge *is* the
style. If a shape needs to read as round, do it with the **silhouette and ramp**,
not by blending edge colours.

Detecting leaked anti-aliasing: run `pixel_draw.py info` on the asset. If the
colour count is far above the ramp size (for example 40 colours on a 16×16
sprite), it was anti-aliased or resized with interpolation.

## Outlines

Choose one convention and hold it:

- **Full 1px outline** — reads cleanly on busy backgrounds; classic for
  platformers and top-down. Implement with `pixel_draw.py outline`.
- **Selective outline** — only on edges facing away from the light.
- **No outline** — relies on strong value contrast between sprite and background.
  Only safe if the tiles behind are deliberately low-contrast.

Rules for any choice:

- Outline colour is one palette entry, not pure black unless the palette says so.
- Never outline with a colour outside the palette.
- The outline lives **inside** the declared frame size. It may not push a 16×16
  sprite to 18×18; author with the outline accounted for.

## Readability over realism

- **Value contrast first.** A sprite that is invisible in greyscale will be
  invisible on a busy background regardless of hue.
- **Cluster, don't speckle.** Isolated single pixels read as noise. A "texture" of
  scattered single pixels reads as dirt.
- **Reserve the brightest entry** for the player and key interactables. If the
  background uses the brightest colour, the player loses.
- **Keep tiles lower contrast than characters.** Backgrounds are supporting cast.

## Dithering

Dithering (checkerboard blending of two palette entries) is valid for gradients,
skies, and large flat areas. Rules:

- Use it for **texture or gradient**, never to fake a colour that the palette
  lacks on a small sprite — at 16×16 it just looks like noise.
- Keep the pattern regular. Random dithering reads as a mistake.
- The project should decide once whether it dithers at all, so the look is
  consistent.

## Palette swaps for variants

Enemy tiers, damage flashes, and team colours are palette swaps, not redraws:

```bash
python ../../scripts/pixel_draw.py recolor \
  --in art/enemy/base.png --out art/enemy/elite.png \
  --map "#41a6f6=#b13e53" "#3b5dc9=#5d275d"
```

Always swap **within the project palette**. A swap that introduces off-palette
colours breaks the rule above and will look wrong next to everything else.

To rescue imported or off-palette art:

```bash
python ../../scripts/pixel_draw.py snap --in raw.png --out fixed.png --palette pico8
```

`snap` is a recovery tool, not part of the normal workflow — author on-palette in
the first place.
