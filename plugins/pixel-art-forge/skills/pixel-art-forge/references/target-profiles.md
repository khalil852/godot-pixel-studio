# Target profiles: what a good asset measures like

Measured numbers from real builds with this tool. These exist because they are the
one kind of guidance that changed an agent's behaviour in testing: at 96×96 an
agent that ran `audit` and saw `dominant run 4px at 21%, 18 distinct run lengths`
read the 64×64 profile below, narrowed its body, and pulled the sprite to the same
profile. Design advice did not have that effect; numbers did.

Use these as a calibration target — "does my asset look like the others" — not as a
pass/fail gate. A deliberately stylised asset may not match, and that is fine.

## Sprites

| Size | Colours | Dominant run | Run-length spread | Light margin |
|---|---|---|---|---|
| 16×16 (grid path) | 7 | 2px | few | small (+3/+1/+1px) |
| 64×64 | 14–16 | 2px, 37–40% of runs | ~11 distinct | +12/+9/+4px across materials |
| 96×96 | 16 | 2px, 35% of runs | ~11 distinct | +12/+11/+4px |

What the numbers say:

- **`dominant run 2px` at every size above 32px.** A 2px feature unit is what reads
  as deliberate higher-resolution pixel art. A 4px dominant run at 64px+ is the
  "upscaled small sprite" tell.
- **Run-length spread collapses after `blocksnap`.** 17–18 distinct run lengths
  means the feature scale is mixed; ~11 means it is not.
- **Light margins grow with canvas size.** On a 16×16 sprite a correct highlight is
  only 1–3px nearer the light than average, which is close enough to noise that the
  check is weak there. At 64px+ it is 4–12px and the signal is real.
- **14–16 colours for a 64×64 character.** Not because 16 is a rule, but because
  that is what three 4–5 step ramps plus an outline comes to.

## UI

| Element | Colours | Border thickness | Interior |
|---|---|---|---|
| panel 192×64 | 3 | 2px, spread 0 | 95% one tone, 3 tones |
| button 96×28 | 3 | 2px, spread 0 | 89% one tone, 3 tones |
| bar 160×16 | 3 | 2px, spread 0 | 65% one tone, 2 tones |
| composite screen | many | 3px, spread 0 | flatness does not apply |

- **3 colours per element, not 16.** A UI element needs ink, fill and one lit
  bevel. Spending more means the element is competing with the content it holds.
- **Border thickness spread must be 0.** A UI frame with one side thicker than
  another is the clearest visual defect a panel can have, and it is invisible in the
  code that produced it.
- **A bar's interior is two flat blocks, not one.** 65% dominant with 2 tones is
  correct for a 65%-filled bar; a single-tone-dominance test would wrongly fail it.
- **Composite screens have no meaningful interior flatness.** A HUD contains bars,
  buttons and dialogs, so its interior is legitimately busy.

## Animation

| Property | Target |
|---|---|
| frame size | identical across the set |
| baseline spread | 0px with `--anchor bottom` |
| largest step vs median | under 2.5× |
| loop seam vs median | under 2.5× (skip with `--open-ended`) |

## Reading these numbers honestly

They come from a small number of builds, mostly one subject (a character, a potion
bottle, a HUD). They describe what worked, not what is optimal. If a project's
assets consistently land outside these ranges and look right, the project is the
authority and this table is the thing that is wrong.
