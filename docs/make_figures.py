#!/usr/bin/env python3
"""Generate docs/why-deterministic.png — the README hero comparison.

Left panel shows the failure modes that make generative image output unusable
in a game engine: anti-aliased edges, off-palette colours, drifting sprite sizes
and unstable baselines. Right panel shows the same sprite set produced by
`pixel_draw.py grid`: hard edges, one palette, exact declared sizes.

Honesty note: the left panel is NOT a sample from a specific image model. It is
produced by applying the actual failure transforms (bilinear resampling, per-pixel
colour jitter, size jitter, baseline jitter) to the clean sprite, so the defects
shown are real and measurable rather than illustrative hand-waving. If you have a
genuine model output to show, swap it in as assets/naive-sample.png and pass
--naive.

Run from the repository root:
    python docs/make_figures.py
"""
from __future__ import annotations

import argparse
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BG = (22, 22, 30, 255)
PANEL_BG = (30, 30, 40, 255)
PANEL_BORDER = (58, 58, 74, 255)
INK = (232, 232, 240, 255)
MUTED = (150, 150, 168, 255)
BAD = (226, 96, 96, 255)
GOOD = (96, 206, 140, 255)

FONT_REG = r"C:\Windows\Fonts\segoeui.ttf"
FONT_MONO = r"C:\Windows\Fonts\consola.ttf"
ZOOM = 5          # sprite zoom inside a cell (5x makes anti-aliasing visible)
CELL = 60         # px per sprite cell
PAD = 18
GAP = 26
TITLE_H = 74
FOOT_H = 52


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def degrade(img: Image.Image, rng: random.Random) -> Image.Image:
    """Apply the real failure modes: size jitter, bilinear resampling, colour jitter."""
    w, h = img.size
    # size jitter — a generative model returns whatever size it feels like
    if rng.random() < 0.6:
        h2 = max(4, h + rng.choice((-1, 1)))
        img = img.resize((w, h2), Image.NEAREST)
    # bilinear upscale — this is what produces anti-aliasing
    img = img.resize((img.width * ZOOM, img.height * ZOOM), Image.BILINEAR)
    # per-pixel colour jitter — off-palette drift
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            j = lambda v: max(0, min(255, v + rng.randint(-14, 14)))
            px[x, y] = (j(r), j(g), j(b), a)
    return img


def clean(img: Image.Image) -> Image.Image:
    return img.resize((img.width * ZOOM, img.height * ZOOM), Image.NEAREST)


def bob(img: Image.Image, i: int) -> Image.Image:
    """A tiny, anchored vertical bob so the clean panel reads as an animation set."""
    dy = (0, 1, 2, 1)[i % 4]
    out = Image.new("RGBA", (img.width, img.height + 2), (0, 0, 0, 0))
    out.paste(img, (0, 2 - dy), img)     # feet stay put, body moves
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=7, help="deterministic defect jitter")
    ap.add_argument("--naive", default=None,
                    help="optional real model sample to use for the left panel")
    ap.add_argument("--out", default="docs/why-deterministic.png")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    root = Path(__file__).resolve().parent.parent
    base = Image.open(root / "examples/slime-idle.png").convert("RGBA")
    frames = 4

    # --- build the sprites first so the layout can be measured, not guessed
    clean_sprites = [clean(bob(base, i)) for i in range(frames)]
    bad_sprites = []
    for _ in range(frames):
        if args.naive:
            s = Image.open(args.naive).convert("RGBA")
            bad_sprites.append(s.resize((s.width * ZOOM, s.height * ZOOM), Image.NEAREST))
        else:
            bad_sprites.append(degrade(base, rng))

    cell_w = max([s.width for s in clean_sprites] + [s.width for s in bad_sprites]) + 16
    cell_h = max([s.height for s in clean_sprites] + [s.height for s in bad_sprites]) + 16
    row_w, row_h = cell_w * frames, cell_h

    f_title = font(FONT_REG, 20)
    f_cap = font(FONT_REG, 15)
    f_small = font(FONT_MONO, 13)

    def tw(s: str, f) -> int:
        return int(f.getlength(s))

    L = {
        "title": "What generative output gets you",
        "cap": "soft edges · off-palette drift · size + baseline jitter",
        "sub": "cannot ship — every frame needs redrawing",
    }
    R = {
        "title": "What pixel_draw.py grid gets you",
        "cap": "hard edges · one palette · exact declared sizes",
        "sub": "ships as-is — differences are one line of diff",
    }

    # panel width must fit the sprite row, the title, and both caption lines
    def panel_width(meta: dict) -> int:
        return max(row_w,
                   tw(meta["title"], f_title),
                   tw(meta["cap"], f_cap),
                   tw(meta["sub"], f_small)) + PAD * 2

    pw_l, pw_r = panel_width(L), panel_width(R)
    title_h = 34
    panel_h = row_h + PAD * 2
    cap_h = 48

    width = PAD + pw_l + GAP + pw_r + PAD
    height = PAD + title_h + panel_h + cap_h + PAD
    canvas = Image.new("RGBA", (width, height), BG)
    d = ImageDraw.Draw(canvas)

    top_title = PAD
    top_panel = top_title + title_h

    # --- panels
    for x0, pw in ((PAD, pw_l), (PAD + pw_l + GAP, pw_r)):
        d.rounded_rectangle([x0, top_panel, x0 + pw, top_panel + panel_h], 8,
                            fill=PANEL_BG, outline=PANEL_BORDER, width=1)

    # --- left: degraded, with baseline jitter kept inside the panel
    for i in range(frames):
        sp = bad_sprites[i]
        cx = PAD + PAD + i * cell_w + (cell_w - sp.width) // 2
        room = panel_h - 2 * PAD
        jitter = rng.randint(-3, 3)
        cy = top_panel + PAD + max(0, min(room - sp.height, (room - sp.height) // 2 + jitter))
        canvas.alpha_composite(sp, (cx, cy))

    # --- right: clean, anchored bob
    for i in range(frames):
        sp = clean_sprites[i]
        cx = PAD + pw_l + GAP + PAD + i * cell_w + (cell_w - sp.width) // 2
        cy = top_panel + PAD + (panel_h - 2 * PAD - sp.height) // 2
        canvas.alpha_composite(sp, (cx, cy))

    # --- text
    d.text((PAD, top_title), L["title"], font=f_title, fill=INK)
    d.text((PAD + pw_l + GAP, top_title), R["title"], font=f_title, fill=INK)

    y = top_panel + panel_h + 14
    d.text((PAD, y), L["cap"], font=f_cap, fill=BAD)
    d.text((PAD, y + 22), L["sub"], font=f_small, fill=MUTED)
    d.text((PAD + pw_l + GAP, y), R["cap"], font=f_cap, fill=GOOD)
    d.text((PAD + pw_l + GAP, y + 22), R["sub"], font=f_small, fill=MUTED)

    out = root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out)
    print(f"wrote {out}  {canvas.width}x{canvas.height}")
    print("left panel source:", args.naive or f"simulated defects (seed={args.seed})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
