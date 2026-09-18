---
name: pixel-art-forge
description: Construct and repair higher-resolution pixel-art game assets with defensible craft. Use when producing or fixing pixel art above tiny-sprite scale (roughly 32px and up), when AI-generated sprite art looks cheap or wrong, when building animated sprite cycles for a game, or when asked to make pixel art that does not read as machine-made.
---

# Pixel Art Forge

## The premise

"AI feel" in pixel art is not a vibe, it is a list of measurable defects. Every
one of them has a construction-time cure:

| Tell | Measurement | Cure |
|---|---|---|
| anti-aliasing | colours that are blends of palette entries | all drawing is nearest-neighbour and hardened per layer |
| palette drift | colour count vs the project palette | `snap`; `audit --palette` fails on off-palette pixels |
| isolated pixels | opaque pixels with no neighbour | `clean --min-neighbors 2` |
| feature-scale mush | many distinct run lengths | `blocksnap --block N` |
| gradient shading | touching tone pairs closer than a few luminance steps | `shade` with a discrete `ramp` |
| inconsistent light | lightest tone not biased to the declared side | `--light` on every `shade`/`outline` |
| jittery silhouette | 1px notches and spikes | `blocksnap` + `clean` |

`audit` prints all seven with the numbers behind them, and exits non-zero when
any fails. Treat it as the gate, not the opinion.

## Why this is not a grid editor above small sizes

At 16×16 every pixel can be hand-decided. At 64×64 that is 4096 decisions, and
hand-authoring it reproduces exactly the defect this skill exists to prevent.
Above roughly 32px the work is **constructive**:

- `shape` places crisp primitives (rect, rounded rect, ellipse, line)
- `shade` bands light across a material by depth from the light side
- `blocksnap` forces one feature scale over the whole asset
- `clean` deletes pixels that are noise rather than detail

`grid` is still here, and still right, for small sprites where a character grid
is genuinely readable.

## Start from a brief, not a sentence

A measured result from this skill's own testing. Given only "make a 64x64 sprite
that passes audit", the agent produced a passing asset. Given the same task as a
filled-in `assets/asset-brief.txt`, it additionally:

- ran a **parameter sweep to rule out a hypothesis** — proving that a glass ring
  around liquid forces the ring's whole inner edge into the lightest band, with the
  margin stuck at -1.0px across a 4-to-8 band sweep, so no ramp tuning could fix it
  and the geometry had to change;
- quantified a trade-off — one `outline` pass yields a 1px ring, not a multiple of
  the 2px block, measurably degrading the run profile (4px dominant at 38%, 15 run
  lengths);
- reported four more things it could **not** verify, including that engine import
  must use nearest-neighbour or the whole exercise is void.

The difference was not knowledge; the model already had that. It was **specification**:
naming `must read as`, fixing the block size, and requiring the report to state what
the agent could not verify and who must check it. A measured contrast inside this
skill: genre and craft *explanations* changed nothing, while *process and reporting
requirements* did.

Fill `assets/asset-brief.txt` before starting. A blank line in it is a decision not
yet made.

## Production workflow (a new higher-res asset)

```bash
PIX=pixel_forge.py      # scripts/pixel_forge.py

# 1. Declare the palette and pull real ramps out of it.
$PIX palettes
SKIN=$($PIX ramp --from "#2b1610" --to "#ffe1bd" --steps 5 --palette forge32)
CLOTH=$($PIX ramp --from "#0d1626" --to "#c3e0f7" --steps 5 --palette forge32)

# 2. Block the silhouette with primitives, back to front (legs, torso, head).
$PIX canvas --size 64x64 --out hero.png
$PIX shape --in hero.png  --out hero.png --kind rrect   --box 24,42,6,18 --radius 2 --color "#31363f"
$PIX shape --in hero.png  --out hero.png --kind rrect   --box 20,26,24,22 --radius 6 --color "${CLOTH%%,*}"
$PIX shape --in hero.png  --out hero.png --kind ellipse --box 22,8,20,20  --color "${SKIN%%,*}"

# 3. Shade one material at a time, always with the same declared light.
$PIX shade --in hero.png --out hero.png --ramp "$SKIN"  --light tl --color "${SKIN%%,*}"
$PIX shade --in hero.png --out hero.png --ramp "$CLOTH" --light tl --color "${CLOTH%%,*}"

# 4. Outline, then force one feature scale, then clear the noise.
$PIX outline --in hero.png --out hero.png --color "#101216" --mode full
$PIX blocksnap --in hero.png --out hero.png --block 2
$PIX clean   --in hero.png --out hero.png --min-neighbors 2

# 5. Gate it. Declare the ramps so the light check is a real gate.
$PIX audit hero.png --palette forge40 --light tl     --material "$SKIN" --material "$CLOTH"
$PIX preview --in hero.png --out review.png --scale 5 --grid-lines
```

Look at `preview.png`. The audit passing is necessary, not sufficient — it cannot
tell you the pose reads badly.

## The rules that actually produce the look

- **One light direction for the whole project.** Pass the same `--light` to every
  `shade` and `outline` call. `audit --light --material <ramp>` checks it per
  material; without `--material` the check is advisory only, because colour
  alone cannot reliably identify a material.
- **Give the outline its own palette entry.** If a line colour doubles as a fill
  ramp's darkest step, the outline is counted as part of that material and drags
  its average position to the middle of the sprite, which makes the light check
  report a false failure.
- **Shade per material, not per silhouette.** Always pass `--color` so each
  material gets its own depth field; shading a head and torso as one mass is what
  produces the "melted" look.
- **Ramps are discrete.** Take 3–5 steps from the palette via `ramp`. The tool
  auto-orients the ramp so pixels nearest the light get the brighter end; if you
  pass a ramp whose luminance is not monotone it warns, because that means the
  two ends belong to different palette ramps.
- **Pick a block size and hold it.** At 64px, `--block 2` is usually right: it
  makes every feature a multiple of two, which is what separates deliberate
  higher-res pixel art from upscaled small art. Then do not introduce 1px detail
  by hand.
- **Outline is optional; consistency is not.** `--mode full` for busy
  backgrounds, `--mode light` to outline only the shadow side. Whichever you
  pick, pick it once.
- **Dither deliberately or not at all.** `dither` uses a fixed matrix between two
  ramp-adjacent colours. Random speckle is the thing being avoided; if you cannot
  say why a region is dithered, remove it.

## UI: large area, low detail

A UI element is the inverse of a sprite. A panel is a flat interior with all of
its information in a border and four corners, and a flat 20-pixel expanse is
*correct* there and a defect in a sprite. Generate UI with `ui`, scale it with
`nineslice`, and judge it with `audit --ui`.

```bash
PIX=scripts/pixel_forge.py

# one 24x24 skin, then any size you like — corners 1:1, edges and centre tiled
$PIX ui --kind panel --size 24x24 --ramp "$GLASS" --border 2 --bevel 2 --radius 4 --out skin.png
$PIX nineslice --in skin.png --size 320x180 --corner 8 --out panel.png --meta panel.json

# elements
$PIX ui --kind button --size 96x28 --ramp "$GLASS" --border 2 --state pressed --out btn_p.png
$PIX ui --kind bar --size 160x16 --ramp "$HP" --border 2 --pct 0.65 --out hp.png

# gate it as UI, not as a sprite
$PIX audit panel.png --palette forge40 --light tl --ui
```

- **`--ramp` needs at least 3 tones** (ink, fill, lit bevel). Two cannot express a
  bevel. `ui` hardens every pixel onto the ramp, so UI never carries a blended edge.
- **`pressed` inverts the bevel**, `disabled` desaturates. Recolour them too if the
  style calls for it.
- **`--ui` adds border-thickness and interior-flatness checks.** Do not run the
  sprite defaults on UI and call the result a verdict, and do not run `--ui` on a
  sprite — it will fail, correctly, because a sprite interior is supposed to be busy.
- **The flatness check is for a single element, not a composite screen.** A full HUD
  is legitimately busy inside; judge border thickness and look at the render instead.
- **Never stretch to scale; tile.** Tiling repeats whole pixels and stays exact,
  where stretching a textured edge smears off-palette tones. `nineslice` tiles.

Full detail, including the Godot/engine side: `references/ui-and-large-areas.md`.

## Build in one call: `batch`

Every command is a separate process (~145 ms of Python startup on this machine) and
a separate model turn, which is where the cost actually is. A batch is one call and
one line of output:

```bash
$PIX batch hud.txt      # 20-command HUD: 3.95s -> 0.95s (4.1x), one tool call
```

The file holds one command per line, `#` comments allowed. Successful steps are
silent; failures print `line N (command): <the real message>`. Prefer a batch over a
long chain of individual calls for anything with more than a few steps, and keep the
script on disk so the asset is reproducible.

## Animation

Cycles are derived from one approved base frame with integer-only transforms, so
nothing is ever resampled.

```bash
$PIX frames --in hero.png --out-dir anim --count 6 --bob 2 --squash 1
$PIX loopcheck --frames anim/hero-0*.png --anchor-tolerance 0
$PIX sheet --frames anim/hero-0*.png --out anim/sheet.png --columns 6 --atlas anim/sheet.json
```

- **`--anchor bottom` (default) keeps the feet planted.** A vertical `--bob` is
  then realised as stretch from the base rather than translation, because
  translating the whole sprite lifts the feet off the ground. `--anchor free`
  translates everything — right for floating characters and hops.
- The base is cropped to its opaque bounds before transforming. Without that,
  squashing drops rows out of the transparent margin and the base row shifts,
  which `loopcheck` reports as anchor drift.
- **`loopcheck` judges evenness, not magnitude.** A jump is a step much larger
  than the cycle's own median step, and the loop seam is the last→first change
  compared against that median. On a small sprite any real motion changes a large
  fraction of pixels, so area-relative thresholds would call normal motion a pop.
- For a non-looping set (attack, death) pass `--open-ended` to skip the seam check.

Details and the reasoning: `references/animation.md`.

## Repairing art that already looks machine-made

```bash
$PIX clean     --in bad.png --out fixed.png --min-neighbors 2 --passes 2
$PIX snap      --in fixed.png --out fixed.png --palette forge32
$PIX blocksnap --in fixed.png --out fixed.png --block 2
$PIX audit fixed.png --palette forge32 --light tl
```

This reliably clears palette drift, speckle noise and edge jitter. Be honest
about the ceiling: `clean`/`snap`/`blocksnap` took a heavily blurred, jittered
sprite from 1/8 audit checks to 6/8 in testing, and the two stubborn failures
were the residual blend tones the blur created. **Blur destroys information;
no palette operation restores it.** Repair is a rescue, not a substitute for
constructing properly.

## Command map

| Command | Purpose |
|---|---|
| `palettes` / `ramp` | palette list; discrete ramp between two palette entries |
| `canvas` / `shape` | start a canvas; draw crisp primitives |
| `shade` | banded directional shading, per material |
| `dither` | fixed-matrix dithering between two tones |
| `outline` | full or light-aware outline |
| `blocksnap` | quantise detail to NxN — enforce one feature scale |
| `clean` | delete pixels with too few neighbours |
| `snap` / `recolor` | palette lock; palette swap for variants |
| `grid` | character grid, for small sprites |
| `ui` | generate a UI element: panel / button / bar (large area, low detail) |
| `nineslice` | scale one small skin to any size, tiled, + engine insets |
| `batch` | run a build script in ONE process, quiet — one tool call |
| `frames` / `sheet` / `loopcheck` | animation generation, export, verification |
| `audit` / `info` / `preview` | measurement and review |

## Before handing anything back

- `audit` passes with the project palette and the declared light.
- `preview` was actually looked at, not just generated.
- Every frame of a cycle passes `loopcheck`.
- UI is gated with `audit --ui`, and a composite screen's layout was
  actually looked at by someone who can see it.
- The `.txt` grid specs and the commands that produced each asset are recorded,
  so the asset is reproducible rather than a one-off binary.

## References

- `references/anti-ai-tells.md` — each tell, how it is measured, how it is cured
- `references/hirez-workflow.md` — constructing a larger asset, in order
- `references/target-profiles.md` — measured colour counts, dominant run lengths, light margins and UI border/interior figures to calibrate against
- `references/animation.md` — cycles, anchors, and what `loopcheck` is judging
- `references/ui-and-large-areas.md` — UI panels/buttons/bars, nine-slice, and why UI is audited differently from sprites
