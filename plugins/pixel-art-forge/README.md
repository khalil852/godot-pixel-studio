# pixel-art-forge

Constructive pixel-art tooling for higher-resolution sprites and game UI, with a
measurable audit for the defects that make pixel art read as machine-made.

The skill is the documentation — see
[`skills/pixel-art-forge/SKILL.md`](skills/pixel-art-forge/SKILL.md). Everything
here is deliberately thin around it.

## What is in the box

```text
skills/pixel-art-forge/
├── SKILL.md                     # the process: palettes, ramps, constructive path, gates
├── scripts/pixel_forge.py       # 25 commands, ~1750 lines, Pillow only
├── references/
│   ├── anti-ai-tells.md         # each defect: how it is measured, how it is cured
│   ├── hirez-workflow.md        # building a larger asset, in order
│   ├── animation.md             # cycles, anchors, what loopcheck judges
│   ├── ui-and-large-areas.md    # panels, buttons, bars, nine-slice
│   └── target-profiles.md       # measured numbers to calibrate against
└── assets/asset-brief.txt       # the brief template — fill it before starting
```

## The three ideas it is built on

**Deterministic over generative.** Pixel art needs per-pixel control. The grid entry
point turns a character grid into a PNG, so the result is exact, diff-able, and
reviewable. No resampling happens anywhere: stretches duplicate whole rows, scaling
is nearest-neighbour and integer.

**Craft is measurable.** `audit` reports eight checks with the numbers behind them —
palette drift, anti-alias suspects, isolated pixels, dominant run length, banded
shading, per-material light consistency, silhouette cleanliness, and (with `--ui`)
border thickness and interior flatness. It exits non-zero on failure, so it works as
a gate rather than an opinion.

**Specification beats explanation.** See the root README for the two experiments.
Short version: telling the agent what to *do and report* changed its behaviour;
explaining art to it did not.

## Quick start

```bash
PIX=skills/pixel-art-forge/scripts/pixel_forge.py

$PIX palettes
$PIX ramp --from "#2b1610" --to "#ffe1bd" --steps 5 --palette forge40

# sprites: constructive above ~32px, grid below it
$PIX ui --kind panel --size 24x24 --ramp "$GLASS" --border 2 --bevel 2 --out skin.png
$PIX nineslice --in skin.png --size 320x180 --corner 8 --out panel.png --meta panel.json

# build many steps in one process, quietly (measured 4.1x, and one tool call)
$PIX batch build.txt
```

Requirements: Python 3.9+ and Pillow. Nothing else.

## License

MIT.
