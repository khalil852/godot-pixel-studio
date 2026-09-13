---
name: pixel-artist
description: Draw pixel-art sprites, tiles, and UI with the deterministic pixel drawing tool. Use when the user wants actual pixel art produced or edited, needs sprite sheets, palette swaps, outlines, or says draw/sprite/tile/pixel art in a Godot project.
---

# Pixel Artist

## Overview

You draw pixel art by authoring **character grids** and rendering them with
`../../scripts/pixel_draw.py`. This is deterministic: the same spec always
produces the same PNG, the output is diff-able, and every pixel is intentional.

Do **not** use an image-generation model for this work. Generated images come
back anti-aliased, off-grid, and off-palette — they cannot be cleaned up into
shipped pixel art reliably.

## The Tool

```bash
python ../../scripts/pixel_draw.py <command> [options]
```

| Command | Use it for |
|---|---|
| `palettes` | List built-in palettes |
| `palette <name>` | Show the char → color mapping |
| `grid --spec F --out F` | **Core.** Render a character grid to PNG |
| `preview --in F --out F --scale 8 --grid-lines` | Enlarge for human review |
| `outline --in F --out F --color "#000000"` | Add a 1px outline |
| `recolor --in F --out F --map OLD=NEW` | Palette-swap for variants |
| `snap --in F --out F --palette pico8` | Force colors onto one palette |
| `sheet --frames ... --out F --columns N` | Build a sprite sheet |
| `info F` | Verify size, color count, bounding box |
| `mirror --in F --out F` | Flip horizontally |

## Grid Spec Format

```text
name: slime-idle-01
legend:
  ".": transparent
  "k": "#1a1c2c"
  "b": "#41a6f6"
  "B": "#3b5dc9"
  "w": "#f4f4f4"
grid:
.....kkkkkk.....
....kbbbbbbk....
...kbwwbbwwbk...
...kbbBBBBbbk...
```

Or skip `legend:` and use a built-in palette — grid characters then map to
`0123456789abcdef` in palette order:

```text
name: coin
palette: pico8
grid:
..aaa..
.aa9aa.
.a9a9a.
```

Rules that the tool enforces (and that you must respect while authoring):

- Every grid row must have the **same character count** — that count is the
  image width. The tool names the offending rows if you get it wrong.
- Every character in the grid must be defined in `legend:` or the palette.
- `.` and space are transparent.

## Authoring Workflow

1. **Pick the canvas size from the art bible.** Do not improvise new sizes.
   Common: 16×16 small props, 16×24 or 24×32 characters, 32×32 large props,
   8×8 or 16×16 tiles.
2. **Block the silhouette first.** Render a single-color version, preview it, and
   check the shape reads at 1× before adding any detail.
3. **Add the shading ramp.** Use 3–4 tones per material: shadow, base, highlight.
   Keep the light direction the same as every other asset in the project.
4. **Cluster, do not speckle.** Adjacent same-color pixels read as shapes;
   isolated single pixels read as noise. Avoid stray single pixels unless
   deliberate (eye glints, sparks).
5. **Outline if the project style calls for it.** A 1px dark outline
   (`outline`) separates a sprite from busy background tiles.
6. **Render, then preview and actually look at it.**
   ```bash
   python ../../scripts/pixel_draw.py grid --spec art/src/slime.txt --out game/art/slime.png
   python ../../scripts/pixel_draw.py preview --in game/art/slime.png --out art/review/slime-x8.png --scale 8 --grid-lines
   ```
   Read the preview image back. If it does not read clearly, fix the grid — do
   not ship it and hope.
7. **Verify with `info`.** Confirm the size matches the art bible and the color
   count is what you intended (unexpected color counts mean a typo'd hex).
8. **Keep the `.txt` spec in the repo** under `art/src/`. The PNG is a build
   artifact; the spec is the source.

## Symmetric Sprites

Author the left half **including the center column**, then mirror:

```bash
python ../../scripts/pixel_draw.py grid --spec art/src/hero-half.txt --out game/art/hero.png --mirror-x
```

Note this yields width `2w-1`. If the art bible demands an even width, author the
full grid instead — do not silently change the declared asset size.

## Animation Sets

- Keep every frame on **one canvas size with one shared anchor** (usually
  bottom-center). A frame that is 1px taller is a defect, not a style choice.
- Author frame 1, then vary it — do not redraw each frame from scratch.
- Assemble and inspect before wiring into Godot:
  ```bash
  python ../../scripts/pixel_draw.py sheet --frames a.png b.png c.png d.png --out run.png --columns 4
  ```
- Animation frame layouts and Godot wiring: `../../references/animation-and-spritesheet.md`.

## Palette Discipline

- Reuse one palette for the whole project. If a new color is genuinely needed,
  add it to the art bible **and** to the spec legend — do not quietly introduce a
  one-off hex.
- `snap --palette` is for rescuing off-palette art, not for routine work.
- Shading: `../../references/palette-and-shading.md`.

## QA Gates Before Handing Off

- Rendered size equals the size declared in the art bible.
- `info` shows only intended colors (no anti-aliased in-between tones).
- Silhouette reads at 1× and at the game's real zoom.
- Animation frames share canvas size and anchor.
- The preview was actually looked at, not just generated.
- `.txt` specs committed alongside the PNGs.
