---
name: pixel-qa
description: Verify a Godot pixel-art game actually runs and looks right, then report concrete defects. Use when the user asks whether the game works, wants a playtest or smoke test, reports blurry/jittery/misaligned visuals, or before declaring any milestone done.
---

# Pixel QA

## Overview

You verify with evidence, not assertions. "It should work" is not a result. Your
output is either a **clean run report with commands and observed output**, or a
**defect list** naming file, measurement, expected value, and observed value.

Never report a milestone as complete without having run the project.

## 1. Script and resource health

```bash
godot --headless --path <project> --quit
```

Read the output. Any parse error, missing resource, or invalid `uid://` reference
is a **blocking defect** — collect the exact message and file. A clean run exits
with no error lines.

## 2. Asset conformance against the manifest

For every asset in `docs/asset-manifest.md`:

```bash
python ../../scripts/pixel_draw.py info <path/to/asset.png>
```

Check and report:

- **Declared vs actual size.** A 16×24 declared frame that renders 16×23 is a defect.
- **Color count.** Against the art bible cap (e.g. ≤6 per sprite). A high count
  usually means anti-aliasing leaked in or a hex was mistyped.
- **Transparency.** Sprites must have a real alpha channel; a white box behind a
  sprite means the background was flattened.
- **Bounding box / anchor.** Within one animation set, the content's bottom edge
  must be consistent. Drift of even 1px causes visible popping.

Report as a table of asset → expected → actual → verdict.

## 3. Animation set integrity

```bash
python ../../scripts/pixel_draw.py sheet --frames <frames...> --out /tmp/review.png --columns <n>
```

Then **read the sheet image back** and inspect:

- All frames same canvas size (the tool warns when they are not).
- Silhouette and proportions stable across frames — no shrinking or swelling.
- Consistent facing direction.
- Frame 1 matches the shipped idle pose when the set continues from idle.

## 4. In-engine visual checks

Launch the game and capture the actual frame, then inspect the image:

- **Blur** — if edges are soft, texture filtering is on. Expected: hard pixel edges.
  Cause and fix: `../godot-programmer/SKILL.md` (film/defect table).
- **Sub-pixel shimmer** — move the camera and watch a static tile edge. Wobbling
  means the camera or a node sits on a fractional position.
- **Misalignment** — tiles should meet with no seams and no 1px double lines.
  Seams mean the tileset tile size disagrees with the art bible.
- **Draw order** — walk behind and in front of a prop. Wrong order means the
  sprite is not under the y-sorted container, or its origin is not at its feet.
- **Collision mismatch** — the collision box should match where the player
  visually stands, not the sprite's full art bounds.

## 5. Playtest the loop

Play the first playable slice from the design brief and report on:

- Does the core loop complete without a crash or soft-lock?
- Is any input unresponsive, or a verb missing an animation?
- Frame rate stability; note stalls, not just averages.
- Anything requiring an undocumented step to progress.

## Defect Report Format

```text
[D1] Blocking — sprite size mismatch
File:   art/player/run.png
Expect: 16x24 per frame, 6 frames
Actual: frames 3 and 5 are 16x23
Cause:  authored on a 23-row grid
Fix:    ../pixel-artist/SKILL.md — re-render from the corrected spec
```

Severity levels: **Blocking** (cannot ship / cannot run), **Major** (visible
defect), **Minor** (polish). Do not bury blocking issues under minor ones.

## What You Do Not Do

- Do not fix art or code here. Report, then hand off to the owning role skill.
- Do not accept "looks fine" as a verdict. State the command run and what was
  observed.
- Do not declare success from the absence of complaints — absence of testing is
  not evidence of correctness.
