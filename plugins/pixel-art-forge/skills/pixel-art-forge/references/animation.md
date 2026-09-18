# Animation: cycles, anchors, and what loopcheck is judging

## Generate, then verify

```bash
pixel_forge.py frames --in hero.png --out-dir anim --count 6 --bob 2 --squash 1
pixel_forge.py loopcheck --frames anim/hero-0*.png --anchor-tolerance 0
pixel_forge.py sheet --frames anim/hero-0*.png --out anim/sheet.png \
    --columns 6 --atlas anim/sheet.json
```

Cycles are derived from **one approved base frame** using integer-only
transforms. Nothing is resampled: a stretch duplicates whole rows, a squash drops
whole rows. Frame-by-frame redrawing is deliberately not offered — it is the
fastest route to a cycle whose frames disagree about the character.

## Anchor semantics

`--anchor bottom` (the default) keeps the base row fixed so the feet stay planted.
A vertical `--bob` is then realised as **stretch from the base** rather than
translation:

- translating the whole sprite lifts the feet off the ground, which reads as
  floating or as a bad collision alignment;
- stretching from a planted base raises the body while the feet stay put, which
  is how a hand-made breathing idle actually works.

`--anchor free` translates everything, feet included. Use it for hovering
enemies, projectiles, and hops where leaving the ground is the point.

The base is cropped to its opaque bounds before any deformation. Squashing the
padded canvas directly drops rows out of the transparent margin, which shifts the
content's base row and surfaces as anchor drift even though the sprite was never
moved. This is why the output canvas is not simply the input size plus padding.

## What loopcheck actually measures

It reports three things, and judges two of them **against the cycle's own median
step**, not against the frame area.

| Check | Meaning |
|---|---|
| baseline spread | max−min of each frame's lowest opaque row; must be within `--anchor-tolerance` |
| largest inter-frame change | the biggest pixel delta between consecutive frames, reported in px and % |
| loop seam | the pixel delta from last frame back to first |

The two judgements:

- **A jump is a step much larger than the median.** If one step is more than
  `--jump-ratio` (default 2.5×) the median, that step will read as a pop.
- **A loop seam is bad when it is far larger than a normal step.** If the
  last→first delta exceeds `--seam-ratio` (default 2.5×) the median, the last
  frame does not lead back into the first.

Judging against the median rather than the frame area matters. On a 26×64 sprite
any real motion changes a large fraction of pixels, so an area-relative threshold
calls ordinary motion a pop — and, more importantly, it says nothing about
whether the motion is *even*, which is what actually reads as popping.

For a non-looping set (attack, hurt, death) pass `--open-ended` to skip the seam
check.

## Verified behaviour

In testing, a 6-frame `--bob 2 --squash 1` cycle built with `--anchor bottom`:

```
ok    baseline stable (spread 0px)
ok    largest inter-frame change 463/1664 px (27.8%), median step 386 px
ok    last->first change 379/1664 px (22.8%)
loopcheck: 6 frames, PASS
```

Displacing one frame 9px horizontally inside the same canvas — so the baseline is
untouched and only the motion evenness is broken — produced:

```
FAIL  uneven cycle: largest step 1194 px is 2.6x the median 463 px (limit 2.5x)
      that step will read as a pop
```

which is the intended discrimination: the check finds *unevenness*, not *bigness*.

## Export

`sheet --atlas` writes the frame rectangles alongside the image:

```json
{ "image": "sheet.png", "cell": [64, 70],
  "frames": [ {"name": "hero-01", "x": 0, "y": 0, "w": 64, "h": 70}, ... ] }
```

Cells are laid out left-to-right, top-to-bottom, `--columns` per row. Frames of
differing sizes produce a warning, because an atlas assumes one cell size — if
you see that warning, the cycle has a size defect that `loopcheck` should have
caught first.

For Godot, import the sheet with filter off and no mipmaps, then build a
`SpriteFrames` from the atlas rectangles. For engines that take a JSON hash or
array, the atlas is already in a shape you can transform in a few lines.

## Frame counts and timing

- 4–6 frames for idle, 6–8 for a walk, 3–5 for an attack.
- Set the speed on the animation resource, not by generating more frames.
- A shorter loop with a clean seam reads better than a longer loop with a hitch,
  which is exactly what `--seam-ratio` is protecting.
