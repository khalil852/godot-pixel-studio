---
name: pixel-art-director
description: Set art direction for a Godot pixel-art game before any asset is drawn. Use when the project has no art bible, when palette or base resolution is undecided, when assets look inconsistent, or when the user asks for a style, palette, or asset list.
---

# Pixel Art Director

## Overview

You exist to prevent the most common pixel-art project failure: assets drawn one
at a time with no shared rules, producing a game that looks like a collage. You
produce a written **art bible** and an **asset manifest** that every later asset
must conform to. Nothing gets drawn before this exists.

## Deliverables

Write these into the project (create `docs/` if missing):

1. `docs/art-bible.md` — the rules.
2. `docs/asset-manifest.md` — the explicit asset list with pixel sizes.

## Art Bible Contents

### Base resolution

Pick a small internal resolution and state it once. Common choices for 2D pixel
games: **320×180** (16:9, pairs with 16×16 tiles) or **384×216**. Display scaling
must be integer.

State the **tile size** (usually 16×16) and the **world scale** (how many pixels
one tile of gameplay space is).

### Palette

Choose one palette and commit:

```bash
python ../../scripts/pixel_draw.py palettes
python ../../scripts/pixel_draw.py palette pico8
```

Built-ins: `pico8` (16), `sweetie16` (16), `gameboy` (4), `1bit` (2).

If the project needs a custom palette, define it explicitly as a `legend:` block
and paste it into the art bible as the single source of truth. Record:

- the exact hex list,
- **which 3–4 entries are the shading ramp for each material**,
- how many colors a single sprite may use.

A hard cap matters more than the specific palette. 16 colors total and ≤6 per
sprite is a workable default.

### Style rules

Write these as checkable statements, not vibes:

- Light direction (e.g. "top-left") and whether shadows are hard-edged.
- Outlined or unoutlined sprites; outline color.
- Black usage: pure `#000000` for outlines only, never for large fills.
- Detail floor: nothing below 1px; feature clusters of ≥2px unless deliberate.
- Anti-aliasing: **banned**. The palette is the only source of intermediate tones.
- Text: fixed bitmap font only, never a system TTF.
- Perspective: top-down / side-on / 3-4 view — pick one and hold it.

### Asset manifest

One table row per asset. This is a contract; `pixel-artist` and `godot-scene-builder`
both read it.

| Asset | Type | Frame size | Frames | Anchor | File |
|---|---|---|---|---|---|
| player idle | sprite | 16×24 | 4 | bottom-center | `art/player/idle.png` |
| player run | sprite | 16×24 | 6 | bottom-center | `art/player/run.png` |
| grass tile | tile | 16×16 | — | — | `art/tiles/ground.png` |
| coin | sprite | 8×8 | 4 | center | `art/props/coin.png` |

## Reviewing Existing Art

When asked whether assets are consistent, check concretely and report defects:

1. Render sizes against the manifest (`pixel_draw.py info <file>`).
2. Color counts — a sprite using 40 colors in a 16-color project is a defect.
3. Shading ramp — is the same ramp used across assets, or invented per asset?
4. Light direction consistency.
5. Outline presence/consistency.
6. Anchor/baseline drift within an animation set.

Report as a defect list with file, measurement, and expected value. Do not
rewrite art here — hand defects to `../pixel-artist/SKILL.md`.
