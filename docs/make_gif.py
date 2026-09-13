#!/usr/bin/env python3
"""Generate docs/grid-to-sprite.gif — the README demo.

Shows the real chain: the character grid appears row by row on the left while the
sprite materialises row by row on the right, the finished asset is shown at game
scale, and (optionally) the same PNGs are shown running in Godot.

It calls the real drawing code (pixel_draw.parse_spec / render_grid) instead of
re-implementing rendering, so the GIF cannot drift from the tool's behaviour.

Regenerating the Godot segment
------------------------------
The game frames are not checked in; capture them from the demo project:

    export GD="/path/to/godot"
    "$GD" --headless --path examples/godot-demo --import
    "$GD" --path examples/godot-demo --write-movie /tmp/out/f.png \\
          --fixed-fps 12 --quit-after 36

Then:  python docs/make_gif.py --game-frames /tmp/out

Run from the repository root.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageSequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "plugins/godot-pixel-studio/scripts"))
import pixel_draw  # noqa: E402  (path set up above)

BG = (20, 20, 27, 255)
PANEL = (30, 30, 40, 255)
BORDER = (58, 58, 74, 255)
INK = (230, 230, 238, 255)
MUTED = (146, 146, 166, 255)
ACCENT = (96, 206, 140, 255)
KEY = (120, 180, 255, 255)
GHOST = (48, 48, 62, 255)

FONT_MONO = r"C:\Windows\Fonts\consola.ttf"
FONT_REG = r"C:\Windows\Fonts\segoeui.ttf"
SPEC = ROOT / "examples/hero-idle-half.txt"

PAD = 20
GAP = 26
ZOOM = 7
LINE_H = 18
MONO_SZ = 13
CAP_H = 34
LABEL_H = 26


def font(path: str, size: int):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def display_lines() -> list[str]:
    """The spec as shown: declarations + grid only.

    Comment lines are dropped on purpose. They are documentation for a human
    reader, not part of the art, and leaving them in pushes the actual grid off
    the panel (and buries the point of the demo under a wall of prose).
    """
    out = []
    for line in SPEC.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        out.append(line.rstrip())
    return out


def partial_sprite(spec: dict, rows: int) -> Image.Image:
    """Render only the first `rows` grid rows — the reveal animation."""
    if rows <= 0:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    sub = dict(spec)
    sub["grid"] = spec["grid"][:rows]
    sub["height"] = rows
    return pixel_draw.render_grid(sub, mirror_x=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--game-frames", default=None,
                    help="directory of PNG frames captured from Godot (optional)")
    args = ap.parse_args()

    lines = display_lines()
    grid_idx = next(i for i, l in enumerate(lines) if l.strip() == "grid:")
    grid_rows = len(lines) - grid_idx - 1

    spec = pixel_draw.parse_spec(SPEC)
    assert spec["height"] == grid_rows, f"spec rows {spec['height']} != displayed {grid_rows}"

    f_mono = font(FONT_MONO, MONO_SZ)
    f_mono_lg = font(FONT_MONO, 15)
    f_label = font(FONT_REG, 13)
    f_cap = font(FONT_REG, 13)

    panel_h = max(len(lines) * LINE_H + 26, 300)
    sprite_w = (spec["width"] * 2 - 1) * ZOOM
    left_w = int(f_mono.getlength(max(lines, key=len))) + 34
    right_w = max(sprite_w + 40, 300)

    cmd = "python pixel_draw.py grid --spec hero-idle-half.txt --out hero-idle.png --mirror-x"
    note = "one character changed = one pixel changed"
    # The canvas must fit the caption too, or the command gets silently truncated.
    cap_w = int(f_mono_lg.getlength(cmd)) + 16 + int(f_cap.getlength(note)) + 24

    W = max(PAD + left_w + GAP + right_w + PAD, PAD + cap_w + PAD)
    H = PAD + LABEL_H + panel_h + CAP_H + PAD

    lx0, ly0 = PAD, PAD + LABEL_H
    lx1, ly1 = lx0 + left_w, ly0 + panel_h
    rx0 = lx1 + GAP
    rx1, ry1 = rx0 + right_w, ly0 + panel_h

    def frame(shown_header: int, rows: int, caret: bool, header_text: str,
              sub: str, note: str, zoom: int) -> Image.Image:
        img = Image.new("RGBA", (W, H), BG)
        d = ImageDraw.Draw(img)

        # --- left: the spec text
        d.rounded_rectangle([lx0, ly0, lx1, ly1], 8, fill=PANEL, outline=BORDER, width=1)
        d.text((lx0 + 2, ly0 - LABEL_H - 2), "examples/hero-idle-half.txt",
               font=f_label, fill=MUTED)
        y = ly0 + 13
        for i, line in enumerate(lines):
            if i >= shown_header:
                break
            colour = INK
            if line.strip().startswith(("name:", "legend:", "grid:")):
                colour = KEY
            d.text((lx0 + 14, y), line, font=f_mono, fill=colour)
            y += LINE_H
        if caret:
            d.rectangle([lx0 + 14, y + 2, lx0 + 14 + 7, y + 5], fill=ACCENT)

        # --- right: the sprite
        d.rounded_rectangle([rx0, ly0, rx1, ry1], 8, fill=PANEL, outline=BORDER, width=1)
        d.text((rx0 + 2, ly0 - LABEL_H - 2), header_text, font=f_label, fill=MUTED)

        full_w = (spec["width"] * 2 - 1) * zoom
        full_h = spec["height"] * zoom
        ox = rx0 + (right_w - full_w) // 2
        oy = ly0 + (panel_h - full_h) // 2
        d.rectangle([ox - 1, oy - 1, ox + full_w, oy + full_h], outline=GHOST)

        sp = partial_sprite(spec, rows)
        if sp.width > 1:
            big = sp.resize((sp.width * zoom, sp.height * zoom), Image.NEAREST)
            img.alpha_composite(big, (ox, oy))

        # --- caption
        cy = ly1 + 12
        d.text((PAD + 2, cy), cmd, font=f_mono_lg, fill=ACCENT)
        nx = PAD + 2 + int(f_mono_lg.getlength(cmd)) + 16
        if nx + int(f_cap.getlength(note)) < W - PAD:
            d.text((nx, cy + 1), note, font=f_cap, fill=MUTED)
        return img

    frames: list[tuple[Image.Image, int]] = []

    # Phase A — declarations appear, then the grid rows, sprite growing in step.
    blink = 0
    for i in range(1, grid_idx + 1):
        blink = 1 - blink
        frames.append((frame(i, 0, bool(blink), "hero-idle.png  (mirror-x)",
                             "", "text grid in", ZOOM), 130))
    for row in range(grid_rows + 1):
        blink = 1 - blink
        frames.append((frame(len(lines), row, bool(blink), "hero-idle.png  (mirror-x)",
                             "", "exact pixels out", ZOOM), 190 if row < grid_rows else 1300))

    # Phase B — hold on the finished pair, with the command that produced it.
    for i in range(3):
        blink = 1 - blink
        frames.append((frame(len(lines), grid_rows, bool(blink), "hero-idle.png  (mirror-x)",
                             "", "one character changed = one pixel changed", ZOOM), 800))

    # Phase C — the finished asset at game scale.
    for z, hold in ((ZOOM, 800), (10, 800), (14, 1600)):
        frames.append((frame(len(lines), grid_rows, True, "hero-idle.png",
                             "", "engine-ready: exact size, on palette", z), hold))

    # Phase D — the same PNGs running in Godot.
    if args.game_frames:
        gdir = Path(args.game_frames)
        gpaths = sorted(gdir.glob("*.png"))
        if not gpaths:
            print(f"warning: no PNG frames in {gdir}, skipping the Godot segment",
                  file=sys.stderr)
        else:
            note = "running in Godot 4.7 — the same PNG, no editing in between"
            sample = Image.open(gpaths[0]).convert("RGBA")
            # Crop the empty sky away so the gameplay strip fills the frame, then
            # scale by a whole number with nearest-neighbour. A fractional scale
            # here would undo the exactness the GIF is demonstrating.
            crop_top = 44
            strip = sample.crop((0, crop_top, sample.width, sample.height))
            # Use nearly the full canvas width: at scale 2 the strip reads as a
            # thumbnail and the pixel detail — the whole point — is lost.
            gscale = max(1, min((W - 8) // strip.width, (H - 92) // strip.height))
            gw, gh = strip.width * gscale, strip.height * gscale
            for gp in gpaths:
                img = Image.new("RGBA", (W, H), BG)
                d = ImageDraw.Draw(img)
                game = Image.open(gp).convert("RGBA").crop(
                    (0, crop_top, sample.width, sample.height))
                game = game.resize((gw, gh), Image.NEAREST)
                gx, gy = (W - gw) // 2, (H - gh) // 2 - 12
                d.rectangle([gx - 2, gy - 2, gx + gw + 1, gy + gh + 1],
                            outline=BORDER, width=2)
                img.alpha_composite(game, (gx, gy))
                d.text((PAD, H - 34), note, font=f_cap, fill=ACCENT)
                frames.append((img, 120))

    out = ROOT / "docs/grid-to-sprite.gif"
    imgs = [f.convert("P", palette=Image.ADAPTIVE, colors=48) for f, _ in frames]
    imgs[0].save(out, save_all=True, append_images=imgs[1:],
                 duration=[d for _, d in frames], loop=0, optimize=False, disposal=2)

    # Read the file back: Pillow can coalesce frames, so verify the real timing
    # instead of trusting the list we passed in.
    saved = Image.open(out)
    real_frames = sum(1 for _ in ImageSequence.Iterator(saved))
    real_ms = 0
    for f in ImageSequence.Iterator(saved):
        real_ms += f.info.get("duration", 0)
    print(f"wrote {out}")
    print(f"  intended: {len(frames)} frames, {sum(d for _, d in frames)/1000:.1f}s")
    print(f"  on disk : {real_frames} frames, {real_ms/1000:.1f}s, {out.stat().st_size/1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
