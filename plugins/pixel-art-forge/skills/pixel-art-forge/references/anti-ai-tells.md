# The seven tells of machine-made pixel art

Every one of these is measurable. That matters: if you cannot measure it, you
cannot tell whether a fix worked, and you end up arguing about taste instead of
reading a number.

`pixel_forge.py audit <file>` prints all seven with the values behind the verdict.

---

## 1. Anti-aliasing

**Looks like:** soft, slightly fuzzy edges. The single most reliable tell, and the
one that survives every other cleanup step.

**Measured as:** colours that are close to the midpoint of two other colours
present in the image, and that occupy only a small share of pixels. These are
blend pixels that no palette contains.

```
FAIL  anti-alias suspects     93149
      #936593, ...
```

**Cause:** any resampling — bilinear or bicubic upscale, a "smooth" brush, rotating
with interpolation, an image model's output, or exporting at one size and scaling
to another.

**Cure:** rebuild with nearest-neighbour operations only. `shape` hardens every
pixel it draws onto its own layer, so curved primitives arrive with hard edges.
For existing art, `snap` maps blends onto the nearest palette entries — but note
that this is lossy: a blurred edge carries several blended tones and snapping
collapses them into a jagged staircase that then needs `blocksnap` and `clean`.

---

## 2. Palette drift

**Looks like:** colours that are *almost* the project's colours. Cheap-looking,
and it makes every asset subtly clash with every other.

**Measured as:** pixels whose colour is not a member of the declared palette.

```
FAIL  palette drift           1343
      off-palette: #96f967x1, #f16584x1, ...
```

**Cure:** `snap --palette <name>` maps every opaque pixel to its nearest palette
entry. Run it after any operation that might introduce new colours, and keep
colour count under the project cap.

---

## 3. Isolated pixels

**Looks like:** grain. A scattering of single pixels that catch the eye
individually instead of reading as texture.

**Measured as:** the share of opaque pixels with no opaque orthogonal or diagonal
neighbour. Detail in pixel art is made of clusters; a lone pixel is noise.

```
FAIL  isolated pixels         35 (2.6%)
      limit 2%
```

**Cure:** `clean --min-neighbors 2`. The threshold is the number of opaque
neighbours a pixel must have to survive. `1` removes only fully isolated pixels;
`2` also removes thin spurs and one-pixel tails, which is usually what you want.
Use `--passes 2` when noise is dense, since removing pixels can isolate others.

---

## 4. Feature-scale mush

**Looks like:** a sprite where some detail is one pixel wide and other detail is
four pixels wide. This mixed scale is what reads as "an upscaled small image" or
"a machine drew it" — the eye cannot find a consistent unit of construction.

**Measured as:** the distribution of constant-colour run lengths along rows and
columns. Healthy pixel art has one dominant run length; mushy art has many
distinct lengths.

```
PASS  dominant run length     2px (72% of runs)
      want one clear feature scale; 7 distinct run lengths seen
```

**Cure:** `blocksnap --block N`. Each NxN block votes and takes its dominant
colour, so every feature becomes a multiple of N. Transparent pixels vote too, so
a mostly-empty block is not filled by a stray opaque pixel. At 64px, `--block 2`
is the common choice: it gives the piece a deliberate chunky unit while still
allowing curved silhouettes.

**The discipline this imposes:** after `blocksnap`, do not add 1px detail by hand.
That reintroduces exactly the mush you just removed.

---

## 5. Gradient shading

**Looks like:** smooth tonal transitions, as if airbrushed. Pixel art is shaded in
bands.

**Measured as:** pairs of colours that **touch each other in the image** and whose
luminance differs by less than a few steps.

The spatial part is essential. Sorting every colour by luminance and looking at
gaps flags unrelated materials that happen to sit at similar brightness — a
mid-blue and a mid-grey can be 1.4 luminance apart and have nothing to do with
each other. Only tones that are *adjacent on screen* reveal a gradient.

```
FAIL  banded shading          7 touching near-tone pairs
      closest seams: #0d1626/#101216 x24; ...
```

**Cure:** `shade --ramp` with a discrete ramp from `ramp --steps 3..5`. The ramp
is taken by walking the palette's own index range, so the steps are palette
entries rather than interpolated colours that happen to land near one.

---

## 6. Inconsistent light

**Looks like:** highlights scattered across the sprite, or a highlight side that
does not match the rest of the project. It reads as flat and cheap even when the
shading is banded correctly.

**Measured as:** *per material* — the brightest step of a material must sit nearer
the light than that material's average position. You declare the materials:

```bash
pixel_forge.py audit hero.png --palette forge40 --light tl \
    --material "$SKIN" --material "$CLOTH"
```

```
PASS  light consistency       2/2 declared materials lit from the tl
      brightest #ffe1bd +8px; brightest #c3e0f7 +9px
      (positive = highlight sits on the light side)
```

Declaring the ramps costs nothing because the workflow already computes them with
`ramp`. **Run `audit` without `--material` and this check degrades to a hint that
never fails** — see below for why.

### Why this check is declarative

Two simpler formulations were implemented and both were wrong, which is worth
recording because the failures are not obvious:

1. **The single globally lightest colour.** Fails on per-material shading: every
   material has its own highlight, so the globally lightest tone is just whichever
   ramp ends brightest, and its position says nothing about the light.
2. **Auto-grouping colours into materials** by luminance and hue. Fails because
   saturation shifts at ramp ends. A "very dark counts as neutral" rule merges the
   **outline** with the darkest step of two unrelated ramps, and the bright ends of
   different ramps collide with each other. On a test sprite this produced four
   groups where there were three materials, two of which failed.

So auto-grouping is reported as `(advisory)` and never fails the audit. Passing
`--material` removes the guesswork and the check becomes a real gate. Verified:
the same sprite scores `+15px` (pass) with the highlight on the light side and
`-61px` (fail) when the highlight is moved to the shadow side.

### The one thing that still trips it

**Do not let an outline share a palette entry with a fill ramp.** If your line
colour is also, say, the darkest step of the neutral ramp, the outline is counted
as part of that material — and an outline surrounds everything, so it drags the
material's average position to the middle of the sprite and the highlight looks
misplaced. Give outlines their own entry (pure black is the usual choice).

Measured on a test sprite: with the outline sharing the neutral ramp's darkest
step the neutral material scored `-8px` (fail); after giving the outline its own
colour the same material scored `+2px` (pass), with nothing else changed.

### Cure

Pass the same `--light` to every `shade` and `outline` call, and shade **per
material** (`--color`) so each part gets its own depth field. Shading a head and
torso as one mass is a common cause of the melted look.

`shade` auto-orients the ramp so that pixels nearest the light receive the
brighter end, whichever order you passed. Getting this backwards is invisible in
the command output and obvious in the picture, so the tool decides rather than
trusting argument order.

---

## 7. Jittery silhouette

**Looks like:** a slightly ragged outline. Single-pixel notches and spikes.

**Measured as:** transparent pixels with three or four opaque orthogonal
neighbours (notches), plus opaque pixels with one or zero (spikes).

```
PASS  silhouette cleanliness  0 notches, 0 spikes
PASS  limit 8 — 1px edge jitter is the machine-made tell
```

A hand-drawn silhouette steps in readable increments. Jitter is what is left
after a model, or a blur, has been near an edge.

**Cure:** `blocksnap` first (it removes the sub-unit detail that causes jitter),
then `clean` (it removes the spikes that remain). Re-run `audit` to confirm.

---

## Using audit well

- **It is a gate, not a score.** Passing means none of the seven defects is
  present. It says nothing about whether the character is well designed, the pose
  reads, or the palette suits the project. Look at the picture too.
- **Set `--palette` and `--light`.** Without them, checks 1, 2 and 6 are skipped
  and you get a much weaker signal.
- **Tune thresholds per project.** A 1-bit game legitimately fails "banded
  shading" with 2 colours; a deliberately dithered piece may have many touching
  tone pairs. Change the threshold when the project's style justifies it, but
  change it knowingly.
- **Repair has a ceiling.** `clean` + `snap` + `blocksnap` took a blurred,
  jittered sprite from 1/8 checks to 6/8 in testing. The two stubborn failures
  were residual blend tones the blur had created. Blur destroys information; no
  palette operation restores it. Prevention is cheaper than repair.
