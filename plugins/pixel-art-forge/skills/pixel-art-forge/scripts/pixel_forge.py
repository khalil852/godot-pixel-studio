#!/usr/bin/env python3
"""pixel_forge — constructive pixel-art tool for higher-resolution game assets.

Why this is not a grid editor
-----------------------------
At 16x16 every pixel can be hand-authored. At 64x64 that is 4096 decisions, and
hand-authoring it produces exactly the failure this tool exists to prevent: noisy,
inconsistent, obviously-machine-made pixel art. So beyond small sprites the work
is *constructive* — crisp shapes, banded shading driven by a declared light
direction, deliberate dithering, and explicit feature-scale quantisation.

The rule this tool enforces
---------------------------
"AI feel" is not a vibe. It is a set of physically measurable defects:

  1. anti-aliasing      — colours that are blends of palette entries
  2. palette drift      — more colours than the project palette declares
  3. isolated pixels    — single pixels with no neighbour (noise, not detail)
  4. feature-scale mush — 1px detail sitting next to 4px detail in one asset
  5. gradient shading   — continuous tone instead of banded ramps
  6. inconsistent light — highlights not on the declared light side
  7. irregular dither   — speckle instead of a repeatable pattern

Commands 1-6 are prevented by construction. `audit` measures all seven so the
verdict is a number, not an opinion.

Animation is first-class: `frames` derives a cycle parametrically from one base
sprite with integer-only transforms, `loopcheck` verifies anchor and loop
continuity, and `sheet` exports a sheet plus an atlas.

Run `pixel_forge.py <command> --help` for any command.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter, deque
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:  # pragma: no cover
    raise SystemExit("Pillow required: python -m pip install pillow")

CLEAR = (0, 0, 0, 0)

PALETTES: dict[str, list[str]] = {
    "pico8": ["#000000", "#1D2B53", "#7E2553", "#008751", "#AB5236", "#5F574F",
              "#C2C3C7", "#FFF1E8", "#FF004D", "#FFA300", "#FFEC27", "#00E436",
              "#29ADFF", "#83769C", "#FF77A8", "#FFCCAA"],
    "sweetie16": ["#1a1c2c", "#5d275d", "#b13e53", "#ef7d57", "#ffcd75", "#a7f070",
                  "#38b764", "#257179", "#29366f", "#3b5dc9", "#41a6f6", "#73eff7",
                  "#f4f4f4", "#94b0c2", "#566c86", "#333c57"],
    "gameboy": ["#0F380F", "#306230", "#8BAC0F", "#9BBC0F"],
    "1bit": ["#000000", "#FFFFFF"],
    # A 32-colour ramp palette for higher-resolution work: four complete 8-step
    # ramps (skin, cloth-blue, neutral, foliage). Ramps rather than scattered
    # colours, because banded shading needs somewhere to step.
    "forge32": [
        # skin, dark -> light
        "#2b1610", "#4a2a1c", "#6b3f28", "#8f5734",
        "#b47443", "#d49a63", "#ecc38f", "#ffe1bd",
        # cloth blue, dark -> light
        "#0d1626", "#16263f", "#203a5c", "#2d5180",
        "#3f6ea6", "#5a91c8", "#8bb8e4", "#c3e0f7",
        # neutral, dark -> light
        "#101216", "#1e2228", "#31363f", "#4a515c",
        "#6a7280", "#8f97a5", "#b8c0cc", "#e2e7ee",
        # foliage, dark -> light
        "#0e1a0c", "#17290f", "#244016", "#345a1f",
        "#4a7a2c", "#64a03c", "#8ac457", "#b8e58a",
    ],
    # Five 8-step ramps: skin, red, blue, neutral, foliage. Red earns its own
    # ramp because it is a primary in game art (health, damage, hearts, danger)
    # and forge32 has no red at all.
    "forge40": [
        # skin
        "#2b1610", "#4a2a1c", "#6b3f28", "#8f5734",
        "#b47443", "#d49a63", "#ecc38f", "#ffe1bd",
        # red
        "#2b0a0d", "#4a1216", "#6e1c20", "#96282a",
        "#bf3a35", "#de5b45", "#f28767", "#ffb894",
        # cloth blue
        "#0d1626", "#16263f", "#203a5c", "#2d5180",
        "#3f6ea6", "#5a91c8", "#8bb8e4", "#c3e0f7",
        # neutral
        "#101216", "#1e2228", "#31363f", "#4a515c",
        "#6a7280", "#8f97a5", "#b8c0cc", "#e2e7ee",
        # foliage
        "#0e1a0c", "#17290f", "#244016", "#345a1f",
        "#4a7a2c", "#64a03c", "#8ac457", "#b8e58a",
    ],
}

PALETTE_CHARS = "0123456789abcdefghijklmnopqrstuvwxyz"

# A 5x7 bitmap font. Pixel-art assets need labels, HUD numbers and card ranks,
# and a system TTF cannot be used: it arrives anti-aliased and off-palette.
FONT_5X7: dict[str, list[str]] = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    ":": ["00000", "00100", "00100", "00000", "00100", "00100", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
}


TRANSPARENT_CHARS = {".", " "}
_COMMENT_RE = re.compile(r"\s+#")


# ------------------------------------------------------------------ colours

def parse_color(text: str) -> tuple[int, int, int, int]:
    t = str(text).strip().strip('"').strip("'").lower()
    if t in ("transparent", "none", "clear"):
        return CLEAR
    if t.startswith("#"):
        t = t[1:]
    if len(t) == 3:
        t = "".join(c * 2 for c in t)
    if len(t) == 6:
        t += "ff"
    if len(t) != 8:
        raise ValueError(f"cannot parse colour: {text}")
    return (int(t[0:2], 16), int(t[2:4], 16), int(t[4:6], 16), int(t[6:8], 16))


def hexof(c: tuple[int, int, int, int]) -> str:
    r, g, b, a = c
    return "transparent" if a == 0 else f"#{r:02x}{g:02x}{b:02x}"


def dist2(a, b) -> int:
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2


def luminance(c) -> float:
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def hsv(c):
    """Hue in degrees and saturation 0..1. Used to decide whether two tones
    belong to the same colour family."""
    r, g, b = c[0] / 255, c[1] / 255, c[2] / 255
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    s = 0.0 if mx == 0 else d / mx
    if d == 0:
        h = 0.0
    elif mx == r:
        h = (60 * ((g - b) / d)) % 360
    elif mx == g:
        h = 60 * ((b - r) / d) + 120
    else:
        h = 60 * ((r - g) / d) + 240
    return h, s


def same_ramp(a, b, band, hue_tol=25.0, sat_floor=0.25, dark=45.0) -> bool:
    """Are two tones neighbours within ONE material's ramp?

    Luminance closeness alone is not enough: on a playing card the cream face
    (luminance 230) and the heart highlight (155) are 75 apart and have nothing
    to do with each other. Near-black is treated as neutral because saturation is
    numerically unstable down there -- a black border computes as "saturated".
    """
    if abs(luminance(a) - luminance(b)) >= band:
        return False
    gray_a = hsv(a)[1] < sat_floor or luminance(a) < dark
    gray_b = hsv(b)[1] < sat_floor or luminance(b) < dark
    if gray_a != gray_b:
        return False
    if gray_a and gray_b:
        return True
    dh = abs(hsv(a)[0] - hsv(b)[0])
    return min(dh, 360 - dh) <= hue_tol


def palette_colors(name: str) -> list[tuple[int, int, int, int]]:
    if name not in PALETTES:
        raise SystemExit(f"unknown palette: {name} (have {'/'.join(PALETTES)})")
    return [parse_color(h) for h in PALETTES[name]]


def all_pixels(img) -> list:
    px = img.load()
    return [px[x, y] for y in range(img.height) for x in range(img.width)]


def load_image(path) -> Image.Image:
    p = Path(path)
    if not p.is_file():
        raise SystemExit(f"file not found: {path}")
    try:
        return Image.open(p).convert("RGBA")
    except Exception as exc:
        raise SystemExit(f"cannot read image {path}: {exc}")


def save(img: Image.Image, path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    img.save(p)


def neighbours(x, y, w, h):
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                yield nx, ny


# ------------------------------------------------------------------ ramps

def cmd_ramp(args):
    """A shading ramp between two colours.

    When both ends are members of the named palette, the ramp is taken by walking
    the palette's own index range. Interpolating in RGB and then snapping picks
    the *nearest* colour, which silently jumps into a neighbouring ramp: a blue
    ramp interpolated toward white snaps its mid steps onto the neutral greys,
    because mid-grey happens to be nearer than the blue ramp's own mid entry.
    """
    a, b = parse_color(args.frm), parse_color(args.to)
    pal = palette_colors(args.palette) if args.palette else None
    steps = max(2, args.steps)

    ramp = None
    if pal:
        try:
            ia, ib = pal.index(a), pal.index(b)
        except ValueError:
            ia = ib = None
        if ia is not None and ia != ib:
            lo, hi = min(ia, ib), max(ia, ib)
            span = hi - lo
            idx = [lo + round(k * span / (steps - 1)) for k in range(steps)]
            ramp = [pal[i] for i in idx]

    if ramp is None:
        out = []
        for i in range(steps):
            t = i / (steps - 1) if steps > 1 else 0.0
            raw = tuple(int(round(a[k] + (b[k] - a[k]) * t)) for k in range(3)) + (255,)
            out.append(min(pal, key=lambda c: dist2(c, raw)) if pal else raw)
        ramp = out

    seen, unique = set(), []
    for s in ramp:
        if s not in seen:
            seen.add(s)
            unique.append(s)

    lums = [luminance(c) for c in unique]
    monotone = all(lums[i] <= lums[i + 1] for i in range(len(lums) - 1)) or \
               all(lums[i] >= lums[i + 1] for i in range(len(lums) - 1))

    print(",".join(hexof(s) for s in unique))
    if len(unique) < steps:
        print(f"# note: {steps} steps collapsed to {len(unique)}", file=sys.stderr)
    if not monotone:
        print("# warning: ramp luminance is not monotone — the two ends probably "
              "belong to different ramps in this palette", file=sys.stderr)
    return 0


# ------------------------------------------------------------------ shapes

def cmd_canvas(args):
    w, h = (int(v) for v in args.size.lower().split("x"))
    bg = parse_color(args.bg)
    save(Image.new("RGBA", (w, h), bg), args.out)
    print(f"canvas {w}x{h} bg={hexof(bg)} -> {args.out}")
    return 0


def cmd_shape(args):
    """Draw a crisp primitive. No anti-aliasing: every pixel is on or off.

    The shape is drawn onto its own layer and hardened there, then composited
    pixel-exactly. Hardening the whole canvas would repaint every existing pixel
    in the new colour — which silently destroys the rest of the sprite.
    """
    img = load_image(args.infile) if args.infile else Image.new(
        "RGBA", tuple(int(v) for v in args.size.lower().split("x")), CLEAR)
    color = parse_color(args.color)
    layer = Image.new("RGBA", img.size, CLEAR)
    d = ImageDraw.Draw(layer)

    if args.kind == "poly":
        if not args.points:
            raise SystemExit('--points is required for --kind poly, e.g. '
                             '--points "32,4 60,60 4,60"')
        pts = []
        for pair in args.points.replace(";", " ").split():
            ax, ay = pair.split(",")
            pts.append((int(ax), int(ay)))
        if len(pts) < 3:
            raise SystemExit("a polygon needs at least 3 points")
        d.polygon(pts, fill=color)
    else:
        if not args.box:
            raise SystemExit("--box is required (x,y,w,h — or x0,y0,x1,y1 for line)")
        parts = [int(v) for v in args.box.split(",")]
        if len(parts) != 4:
            raise SystemExit("--box wants four integers")
        if args.kind == "line":
            d.line(parts, fill=color, width=args.width)
        else:
            x, y, w, h = parts
            box = [x, y, x + w - 1, y + h - 1]
            if args.kind == "ellipse":
                d.ellipse(box, fill=color)
            elif args.kind == "rect":
                d.rectangle(box, fill=color)
            elif args.kind == "rrect":
                d.rounded_rectangle(box, radius=args.radius, fill=color)
            else:
                raise SystemExit(f"unknown shape: {args.kind}")

    # Harden the layer only: any pixel the shape touched becomes exactly `color`
    # or fully clear. Pillow can blend at curved edges; pixel art cannot.
    lp = layer.load()
    for y in range(layer.height):
        for x in range(layer.width):
            c = lp[x, y]
            if c[3] == 0:
                continue
            lp[x, y] = color if c[3] >= 128 else CLEAR

    # Composite manually rather than with alpha_composite, so a fully opaque
    # layer pixel replaces the base pixel outright with no blending.
    ip = img.load()
    for y in range(img.height):
        for x in range(img.width):
            if lp[x, y][3] == 255:
                ip[x, y] = lp[x, y]

    save(img, args.out)
    print(f"{args.kind} {hexof(color)} -> {args.out}")
    return 0


# ------------------------------------------------------------------ shading

def depth_from_light(img, dx, dy, only=None, cap=255):
    """Steps from each pixel toward the light, stopping at any boundary.

    Small depth = close to the lit edge. Banding this produces shading that
    follows the silhouette, which is how hand-made pixel art is shaded.

    `only` restricts both the starting pixels and the "inside" test to one
    colour, so each material gets its own depth field. Without it, a head and a
    torso share one field and the shading of each is distorted by the other's
    bulk.
    """
    px = img.load()
    w, h = img.size

    def inside(x, y):
        c = px[x, y]
        return c[3] > 0 and (only is None or c == only)

    out = [[0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if not inside(x, y):
                continue
            k, cx, cy = 0, x + dx, y + dy
            while 0 <= cx < w and 0 <= cy < h and inside(cx, cy) and k < cap:
                k += 1
                cx += dx
                cy += dy
            out[y][x] = k
    return out


LIGHT_VECTORS = {
    "tl": (-1, -1), "t": (0, -1), "tr": (1, -1),
    "l": (-1, 0), "r": (1, 0),
    "bl": (-1, 1), "b": (0, 1), "br": (1, 1),
}


def cmd_shade(args):
    """Banded directional shading. The ramp stays discrete by construction.

    The ramp is auto-oriented by luminance so that the pixels nearest the light
    always receive the brighter end, whichever order the caller passed. Getting
    this backwards is invisible in the command output and obvious only in the
    picture, so the tool decides it rather than trusting the argument order.
    """
    img = load_image(args.infile)
    ramp = [parse_color(c) for c in args.ramp.split(",")]
    target = parse_color(args.color) if args.color else None

    if luminance(ramp[0]) < luminance(ramp[-1]):
        ramp = list(reversed(ramp))
        note = " (auto-reversed: nearest-light takes the brighter end)"
    else:
        note = ""

    lums = [luminance(c) for c in ramp]
    if not (all(a <= b for a, b in zip(lums, lums[1:])) or
            all(a >= b for a, b in zip(lums, lums[1:]))):
        print("warning: ramp luminance is not monotone; shading will look muddy",
              file=sys.stderr)

    dx, dy = LIGHT_VECTORS[args.light]
    depth = depth_from_light(img, dx, dy, only=target)
    px = img.load()
    maxd = max((max(row) for row in depth), default=0)
    if maxd == 0:
        raise SystemExit("nothing to shade — no pixels matched "
                         + (hexof(target) if target else "the selection"))

    bands = len(ramp)
    for y in range(img.height):
        for x in range(img.width):
            if px[x, y][3] == 0:
                continue
            if target is not None and px[x, y] != target:
                continue
            band = min(bands - 1, depth[y][x] * bands // (maxd + 1))
            px[x, y] = ramp[band]
    save(img, args.out)
    print(f"shaded light={args.light} maxdepth={maxd} bands={bands}{note} -> {args.out}")
    return 0


BAYER = {
    "bayer2": [[0, 2], [3, 1]],
    "bayer4": [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]],
}


def cmd_dither(args):
    """Deliberate dithering: a fixed repeating matrix, not random speckle."""
    img = load_image(args.infile)
    a, b = parse_color(args.a), parse_color(args.b)
    if args.pattern == "checker":
        mat, modulo = [[0, 1], [1, 0]], 2
    else:
        mat = BAYER[args.pattern]
        modulo = len(mat)
    px = img.load()
    x0, y0, w, h = (int(v) for v in args.region.split(",")) if args.region \
        else (0, 0, img.width, img.height)
    level = max(0.0, min(1.0, args.level))
    for y in range(y0, min(y0 + h, img.height)):
        for x in range(x0, min(x0 + w, img.width)):
            if px[x, y] != a:
                continue
            t = (mat[y % modulo][x % modulo] + 0.5) / (modulo * modulo)
            if t < level:
                px[x, y] = b
    save(img, args.out)
    print(f"dither {args.pattern} level={level} -> {args.out}")
    return 0


def cmd_outline(args):
    """Outline every opaque pixel, or only the edges facing away from the light."""
    img = load_image(args.infile)
    color = parse_color(args.color)
    w, h = img.size
    src = img.copy()
    px = src.load()
    out = img.load()
    dx, dy = LIGHT_VECTORS[args.light]
    for y in range(h):
        for x in range(w):
            if px[x, y][3] != 0:
                continue
            edge = False
            for nx, ny in neighbours(x, y, w, h):
                if px[nx, ny][3] == 0:
                    continue
                if args.mode == "full":
                    edge = True
                    break
                # light-aware: only annotate neighbours that face away from light
                if (nx - x, ny - y) == (dx, dy):
                    continue
                edge = True
                break
            if edge:
                out[x, y] = color
    save(img, args.out)
    print(f"outline {args.mode} {hexof(color)} -> {args.out}")
    return 0


# ------------------------------------------------- anti-AI-feel construction

def cmd_blocksnap(args):
    """Quantise detail to NxN blocks.

    This is the single strongest defence against "AI feel" at higher resolution:
    a machine-drawn sprite mixes 1px and 4px features, and that mixed feature
    scale is what the eye reads as wrong. Forcing one block size makes the whole
    asset read as deliberately placed.
    """
    img = load_image(args.infile)
    n = max(1, args.block)
    w, h = img.size
    px = img.load()
    out = Image.new("RGBA", (w, h), CLEAR)
    q = out.load()
    for by in range(0, h, n):
        for bx in range(0, w, n):
            counts = Counter()
            for y in range(by, min(by + n, h)):
                for x in range(bx, min(bx + n, w)):
                    counts[px[x, y]] += 1
            total = sum(counts.values())
            dominant, cnt = counts.most_common(1)[0]
            # treat transparency as a colour for the vote: a mostly-empty block
            # must not be filled by a stray opaque pixel
            if dominant != CLEAR and counts[CLEAR] * 2 >= total:
                dominant = CLEAR
            for y in range(by, min(by + n, h)):
                for x in range(bx, min(bx + n, w)):
                    q[x, y] = dominant
    save(out, args.out)
    print(f"blocksnap {n}x{n} -> {args.out}")
    return 0


def cmd_clean(args):
    """Delete pixels that have too few opaque neighbours (noise, not detail)."""
    img = load_image(args.infile)
    for _ in range(max(1, args.passes)):
        src = img.copy()
        px = src.load()
        out = src.copy()
        q = out.load()
        for y in range(img.height):
            for x in range(img.width):
                if px[x, y][3] == 0:
                    continue
                n = sum(1 for nx, ny in neighbours(x, y, img.width, img.height)
                        if px[nx, ny][3] > 0)
                if n < args.min_neighbors:
                    q[x, y] = CLEAR
        img = out
    save(img, args.out)
    print(f"clean min_neighbors={args.min_neighbors} -> {args.out}")
    return 0


def cmd_snap(args):
    img = load_image(args.infile)
    pal = palette_colors(args.palette)
    px = img.load()
    changed = 0
    for y in range(img.height):
        for x in range(img.width):
            c = px[x, y]
            if c[3] == 0:
                continue
            best = min(pal, key=lambda p: dist2(p, c))
            if best != c:
                px[x, y] = best
                changed += 1
    save(img, args.out)
    print(f"snap {args.palette}: {changed} px changed -> {args.out}")
    return 0


def cmd_recolor(args):
    img = load_image(args.infile)
    mapping = {}
    for pair in args.map:
        old, new = pair.split("=", 1)
        mapping[parse_color(old)] = parse_color(new)
    px = img.load()
    n = 0
    for y in range(img.height):
        for x in range(img.width):
            if px[x, y] in mapping:
                px[x, y] = mapping[px[x, y]]
                n += 1
    save(img, args.out)
    print(f"recolor: {n} px -> {args.out}")
    return 0


def cmd_grid(args):
    """Text-grid rendering — still the right tool at small sizes."""
    spec = _parse_grid_spec(Path(args.spec))
    img = _render_grid(spec, mirror_x=args.mirror_x)
    save(img, args.out)
    print(f"{img.width}x{img.height} -> {args.out}")
    return 0


def _parse_grid_spec(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()
    block, legend_lines, grid_lines = None, [], []
    for raw in lines:
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        s = line.strip()
        if s in ("grid:", "legend:"):
            block = s[:-1]
            continue
        if s.startswith(("name:", "palette:", "scale:", "author:")):
            block = None
            continue
        if block == "legend":
            legend_lines.append(_COMMENT_RE.split(line, 1)[0].strip())
        elif block == "grid":
            grid_lines.append(_COMMENT_RE.split(line, 1)[0].strip())
    if not grid_lines:
        raise SystemExit(f"{path}: no grid: block")

    legend = {}
    for item in legend_lines:
        if ":" not in item:
            continue
        ch, col = item.split(":", 1)
        ch = ch.strip().strip('"').strip("'")
        col = col.strip().strip('"').strip("'")
        try:
            legend[ch] = parse_color(col)
        except ValueError:
            raise SystemExit(f"{path}: bad legend colour for {ch!r}: {col!r}")

    index_map = {}
    if not legend:
        pname = None
        for raw in lines:
            if raw.strip().startswith("palette:"):
                pname = _COMMENT_RE.split(raw, 1)[0].split(":", 1)[1].strip()
        if not pname or pname not in PALETTES:
            raise SystemExit(f"{path}: need a legend: block or a known palette:")
        for i, h in enumerate(PALETTES[pname]):
            index_map[PALETTE_CHARS[i]] = parse_color(h)

    counts = Counter(len(r) for r in grid_lines)
    width = counts.most_common(1)[0][0]
    bad = [(i + 1, len(r)) for i, r in enumerate(grid_lines) if len(r) != width]
    if bad:
        raise SystemExit(f"{path}: every row must be {width} chars; offenders: "
                         + ", ".join(f"row {i} ({n})" for i, n in bad[:10]))
    return {"grid": grid_lines, "width": width, "height": len(grid_lines),
            "legend": legend, "index_map": index_map}


def _render_grid(spec: dict, mirror_x=False) -> Image.Image:
    h, w = spec["height"], spec["width"]
    out_w = w * 2 - 1 if mirror_x else w
    img = Image.new("RGBA", (out_w, h), CLEAR)
    px = img.load()
    for y, row in enumerate(spec["grid"]):
        for x, ch in enumerate(row):
            if ch in TRANSPARENT_CHARS:
                continue
            color = spec["legend"].get(ch, spec["index_map"].get(ch))
            if color is None:
                raise SystemExit(f"undefined char {ch!r} at row {y+1} col {x+1}")
            px[x, y] = color
            if mirror_x and 0 <= out_w - 1 - x < out_w:
                px[out_w - 1 - x, y] = color
    return img


# ------------------------------------------------------------------ animation

def _shift(img, dx, dy, canvas=None):
    w, h = canvas or img.size
    out = Image.new("RGBA", (w, h), CLEAR)
    out.alpha_composite(img, (max(0, dx), max(0, dy)))
    return out


def _squash(img, rows):
    """Change height by `rows` by duplicating/removing whole pixel rows.

    Duplicating rows instead of resampling is what keeps the result pixel-exact;
    a resample here would reintroduce the anti-aliasing this tool exists to avoid.
    """
    if rows == 0:
        return img
    px = img.load()
    keep = []
    if rows > 0:                                    # stretch: duplicate rows
        step = max(1, img.height // (rows + 1))
        for y in range(img.height):
            keep.append(y)
            if y % step == step - 1 and len(keep) < img.height + rows:
                keep.append(y)
    else:                                           # squash: drop rows
        step = max(1, img.height // (abs(rows) + 1))
        for y in range(img.height):
            if y % step != step - 1 or y >= img.height - 1:
                keep.append(y)
    out = Image.new("RGBA", (img.width, len(keep)), CLEAR)
    q = out.load()
    for i, y in enumerate(keep):
        for x in range(img.width):
            q[x, i] = px[x, y]
    return out


def _motion_offset(i, count, amp, phase=0.0):
    return int(round(math.sin(2 * math.pi * (i / count) + phase) * amp))


def _content_box(img):
    """Opaque bounding box, or None when the image is empty."""
    px = img.load()
    xs, ys = [], []
    for y in range(img.height):
        for x in range(img.width):
            if px[x, y][3] > 0:
                xs.append(x)
                ys.append(y)
    if not xs:
        return None
    return (min(xs), min(ys), max(xs) + 1, max(ys) + 1)


def cmd_frames(args):
    """Derive a cycle from one base sprite using integer-only transforms.

    Anchor semantics matter more than they look. `bottom` (default) keeps the
    sprite's base row fixed so the feet stay planted, and a vertical bob is then
    realised as a stretch/compress from that base rather than a translation --
    which is how a hand-made breathing idle actually works. Translating the whole
    sprite instead lifts the feet off the ground, and `loopcheck` reports exactly
    that as baseline drift. `free` translates everything, feet included; use it
    for floating characters or a hop where leaving the ground is the point.

    The base is cropped to its opaque bounds before any deformation. Squashing
    the padded canvas directly drops rows out of the transparent margin, which
    shifts the content's base row and shows up as anchor drift even though the
    sprite itself was never moved.
    """
    raw = load_image(args.infile)
    box = _content_box(raw)
    if box is None:
        raise SystemExit(f"{args.infile} is fully transparent -- nothing to animate")
    base = raw.crop(box)
    count = max(2, args.count)
    planted = args.anchor == "bottom"

    frames = []
    max_extra = abs(args.bob) + abs(args.squash) + 2
    canvas_h = base.height + 2 * max_extra
    canvas_w = base.width + 2 * abs(args.sway)

    for i in range(count):
        bob = _motion_offset(i, count, args.bob)
        squash = _motion_offset(i, count, args.squash, math.pi / 2)

        if planted:
            f = _squash(base, squash + bob)
            dy = 0
        else:
            f = _squash(base, squash)
            dy = bob

        dx = _motion_offset(i, count, args.sway)
        out = Image.new("RGBA", (canvas_w, canvas_h), CLEAR)
        out.alpha_composite(
            f, (abs(args.sway) + dx, canvas_h - max_extra - f.height + dy))
        frames.append(out)

    outdir = Path(args.out_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    stem = Path(args.infile).stem
    written = []
    for i, f in enumerate(frames):
        p = outdir / f"{stem}-{i + 1:02d}.png"
        f.save(p)
        written.append(p)
    print(f"{count} frames {canvas_w}x{canvas_h} anchor={args.anchor} "
          f"(content cropped to {base.width}x{base.height}) -> {outdir}")
    for p in written[:3]:
        print(f"  {p.name}")
    if len(written) > 3:
        print(f"  ... {written[-1].name}")
    return 0


def cmd_text(args):
    """Render text from the built-in 5x7 bitmap font, hardened and integer-scaled.

    A system TTF cannot be used here: it arrives anti-aliased and off-palette,
    which is the exact defect this tool exists to prevent. So the font is a
    bitmap and the only permitted scaling is a whole-number pixel multiply.
    """
    if args.infile:
        img = load_image(args.infile)
    elif args.size:
        img = Image.new("RGBA", tuple(int(v) for v in args.size.lower().split("x")), CLEAR)
    else:
        raise SystemExit("give --in or --size")
    color = parse_color(args.color)
    text = args.string.upper()
    scale = max(1, args.scale)
    x, y = (int(v) for v in args.at.split(","))
    adv = 6 * scale                      # 5px glyph + 1px gap

    missing = []
    for i, ch in enumerate(text):
        glyph = FONT_5X7.get(ch)
        if glyph is None:
            missing.append(ch)
            continue
        ox = x + i * adv
        for ry, row in enumerate(glyph):
            for rx, bit in enumerate(row):
                if bit != "1":
                    continue
                for sy in range(scale):
                    for sx in range(scale):
                        ax, ay = ox + rx * scale + sx, y + ry * scale + sy
                        if 0 <= ax < img.width and 0 <= ay < img.height:
                            img.putpixel((ax, ay), color)
    if missing:
        print(f"warning: no glyph for {''.join(sorted(set(missing)))!r}", file=sys.stderr)
    save(img, args.out)
    print(f'text "{text}" at {x},{y} scale={scale} -> {args.out}')
    return 0


_ROT = {90: Image.ROTATE_90, 180: Image.ROTATE_180, 270: Image.ROTATE_270}


def _orient(img, flip=None, rotate=None):
    if flip == "h":
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    elif flip == "v":
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
    elif flip == "both":
        img = img.transpose(Image.ROTATE_180)
    if rotate:
        img = img.transpose(_ROT[rotate])
    return img


def cmd_flip(args):
    """Mirror. Flipping for facing direction is the common game-asset use."""
    out = _orient(load_image(args.infile), flip=args.axis)
    save(out, args.out)
    print(f"flip {args.axis} -> {args.out}")
    return 0


def cmd_rotate(args):
    out = _orient(load_image(args.infile), rotate=args.degrees)
    save(out, args.out)
    print(f"rotate {args.degrees} deg -> {args.out}")
    return 0


def cmd_paste(args):
    """Composite one image onto another pixel-exactly.

    Pixels are replaced, never blended. An alpha-composite would mix the stamp's
    edge pixels with the base and quietly reintroduce off-palette tones.
    """
    base = load_image(args.infile)
    src = _orient(load_image(args.src), flip=args.flip, rotate=args.rotate)
    x, y = (int(v) for v in args.at.split(","))
    bp, sp = base.load(), src.load()
    for sy in range(src.height):
        for sx in range(src.width):
            c = sp[sx, sy]
            if c[3] == 0:
                continue
            ax, ay = x + sx, y + sy
            if 0 <= ax < base.width and 0 <= ay < base.height:
                bp[ax, ay] = c
    save(base, args.out)
    print(f"paste {args.src} at {x},{y}"
          + (f" flip={args.flip}" if args.flip else "")
          + (f" rotate={args.rotate}" if args.rotate else "")
          + f" -> {args.out}")
    return 0


def cmd_sheet(args):
    frame_paths = [Path(p) for p in args.frames]
    imgs = [load_image(p) for p in frame_paths]
    tw = args.tile_w or max(i.width for i in imgs)
    th = args.tile_h or max(i.height for i in imgs)
    cols = args.columns or len(imgs)
    rows = (len(imgs) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * tw, rows * th), CLEAR)
    entries = []
    for i, im in enumerate(imgs):
        x, y = (i % cols) * tw, (i // cols) * th
        if im.size != (tw, th):
            print(f"warning: {frame_paths[i].name} is {im.size}, cell is {tw}x{th}",
                  file=sys.stderr)
        sheet.paste(im, (x, y))
        entries.append({"name": frame_paths[i].stem, "x": x, "y": y,
                        "w": im.width, "h": im.height})
    save(sheet, args.out)
    print(f"sheet {sheet.width}x{sheet.height} {cols}x{rows} cell {tw}x{th} -> {args.out}")
    if args.atlas:
        Path(args.atlas).write_text(json.dumps(
            {"image": Path(args.out).name, "cell": [tw, th], "frames": entries},
            indent=2), encoding="utf-8")
        print(f"atlas -> {args.atlas}")
    return 0


def cmd_loopcheck(args):
    """Verify a frame set: constant size, stable anchor, clean loop."""
    imgs = [load_image(p) for p in args.frames]
    if len(imgs) < 2:
        raise SystemExit("need at least 2 frames")
    problems, notes = [], []
    sizes = {i.size for i in imgs}
    if len(sizes) != 1:
        problems.append(f"frame sizes differ: {sorted(sizes)}")
    size = imgs[0].size

    bottoms = []
    for n, im in enumerate(imgs):
        px = im.load()
        rows = [y for y in range(im.height) if any(px[x, y][3] > 0 for x in range(im.width))]
        bottoms.append(max(rows) if rows else None)
    known = [b for b in bottoms if b is not None]
    if known and (max(known) - min(known)) > args.anchor_tolerance:
        problems.append(f"baseline drifts by {max(known)-min(known)}px "
                        f"(tolerance {args.anchor_tolerance})")
    else:
        notes.append(f"baseline stable (spread {max(known)-min(known) if known else 0}px)")

    def diff(a, b):
        pa, pb = a.load(), b.load()
        return sum(1 for y in range(size[1]) for x in range(size[0])
                   if pa[x, y] != pb[x, y])

    steps = [diff(imgs[i], imgs[i + 1]) for i in range(len(imgs) - 1)]
    loop = diff(imgs[-1], imgs[0])
    total = size[0] * size[1]
    ordered = sorted(steps)
    median = ordered[len(ordered) // 2] or 1

    # Judge jumps and the loop seam against the cycle's own median step, not
    # against the frame area. On a small sprite any real motion changes a large
    # fraction of pixels, so an area-relative threshold calls normal motion a pop
    # and says nothing about whether the motion is *even*.
    notes.append(f"largest inter-frame change {max(steps)}/{total} px "
                 f"({max(steps)/total*100:.1f}%), median step {median} px")
    notes.append(f"last->first change {loop}/{total} px ({loop/total*100:.1f}%)")
    if max(steps) > median * args.jump_ratio:
        problems.append(f"uneven cycle: largest step {max(steps)} px is "
                        f"{max(steps)/median:.1f}x the median {median} px "
                        f"(limit {args.jump_ratio}x) — that step will read as a pop")
    if not args.open_ended and loop > median * args.seam_ratio:
        problems.append(f"loop seam is {loop/median:.1f}x the median step "
                        f"(limit {args.seam_ratio}x) — the last frame does not lead "
                        f"back into the first")

    for n in notes:
        print(f"  ok    {n}")
    for p in problems:
        print(f"  FAIL  {p}")
    print(f"loopcheck: {len(imgs)} frames, {'PASS' if not problems else 'FAIL'}")
    return 0 if not problems else 1


# ------------------------------------------------------------------ audit

def _palette_set(name: str) -> set:
    return set(palette_colors(name))


def _auto_families(colors, band):
    """Group tones into rough material families by luminance and hue.

    Advisory only. Saturation shifts at ramp ends, so this merges unrelated dark
    ends and splits bright ones; it is a hint, not a measurement.
    """
    cols = list(colors)
    parent = {c: c for c in cols}

    def find(c):
        while parent[c] != c:
            parent[c] = parent[parent[c]]
            c = parent[c]
        return c

    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            if same_ramp(a, b, band):
                ra, rb = find(a), find(b)
                if ra != rb:
                    parent[ra] = rb
    groups: dict = {}
    for c in cols:
        groups.setdefault(find(c), []).append(c)
    return [m for m in groups.values() if len(m) >= 2]


def cmd_audit(args):
    """Measure the seven defects that make pixel art read as machine-made."""
    img = load_image(args.infile)
    px = img.load()
    w, h = img.size
    opaque = [(x, y) for y in range(h) for x in range(w) if px[x, y][3] > 0]
    if not opaque:
        raise SystemExit("image is fully transparent")
    colors = Counter(px[x, y] for x, y in opaque)
    total = len(opaque)

    results = []

    def check(name, value, ok, detail=""):
        results.append({"check": name, "value": value, "pass": bool(ok),
                        "detail": detail})

    # 1. palette discipline
    pal = _palette_set(args.palette) if args.palette else None
    check("colour count", len(colors),
          len(colors) <= args.max_colors,
          f"limit {args.max_colors}"
          + (f", palette {args.palette} has {len(pal)}" if pal else ""))
    if pal is not None:
        off = {c: n for c, n in colors.items() if c not in pal}
        check("palette drift", len(off), not off,
              "off-palette: " + ", ".join(f"{hexof(c)}x{n}" for c, n in
                                          list(off.items())[:6]) if off else "all on palette")

    # 2. anti-aliasing: colours that are blends of two other present colours
    if len(colors) > 2:
        base_colors = sorted(colors, key=lambda c: -colors[c])[:max(4, len(colors)//2)]
        aa = []
        for c, n in colors.items():
            if n > total * 0.02:
                continue
            for i, a in enumerate(base_colors):
                for b in base_colors[i + 1:]:
                    mid = tuple((a[k] + b[k]) // 2 for k in range(3)) + (255,)
                    if dist2(mid, c) <= args.aa_tolerance ** 2:
                        aa.append(c)
                        break
        check("anti-alias suspects", len(aa), not aa,
              ", ".join(hexof(c) for c in aa[:6]) if aa else "none")

    # 3. isolated pixels
    iso = 0
    for x, y in opaque:
        if not any(px[nx, ny][3] > 0 for nx, ny in neighbours(x, y, w, h)):
            iso += 1
    ratio = iso / total
    check("isolated pixels", f"{iso} ({ratio*100:.1f}%)",
          ratio <= args.max_isolated,
          f"limit {args.max_isolated*100:.0f}% — these read as noise, not detail")

    # 4. feature scale: run lengths of constant colour along rows and columns
    runs = []
    for y in range(h):
        run = 1
        for x in range(1, w):
            if px[x, y] == px[x - 1, y] and px[x, y][3] > 0:
                run += 1
            else:
                if run > 1:
                    runs.append(run)
                run = 1
    if runs:
        rc = Counter(runs)
        dominant = rc.most_common(1)[0][0]
        share = rc[dominant] / len(runs)
        check("dominant run length", f"{dominant}px ({share*100:.0f}% of runs)",
              share >= args.min_run_share,
              f"want one clear feature scale; {len(rc)} distinct run lengths seen")
    else:
        check("dominant run length", "n/a", True, "no runs > 1px")

    # 5. gradient shading: adjacent tones that touch each other with a tiny
    #    luminance gap. The test must be spatial — sorting every colour by
    #    luminance and looking at gaps flags unrelated materials that happen to
    #    sit at similar brightness (a mid-blue and a mid-grey are 1.4 apart in
    #    luminance and have nothing to do with each other).
    if len(colors) >= 4:
        close_pairs = {}
        for y in range(h):
            for x in range(w):
                c = px[x, y]
                if c[3] == 0:
                    continue
                for nx, ny in ((x + 1, y), (x, y + 1)):
                    if nx >= w or ny >= h:
                        continue
                    d = px[nx, ny]
                    if d[3] == 0 or d == c:
                        continue
                    g = abs(luminance(c) - luminance(d))
                    if 0 < g < args.min_tonal_gap:
                        key = tuple(sorted([hexof(c), hexof(d)]))
                        close_pairs[key] = close_pairs.get(key, 0) + 1
        worst = sorted(close_pairs.items(), key=lambda kv: -kv[1])[:4]
        check("banded shading", f"{len(close_pairs)} touching near-tone pairs",
              len(close_pairs) <= args.max_smooth_gaps,
              ("closest seams: " + "; ".join(f"{a}/{b} x{n}" for (a, b), n in worst))
              if worst else
              f"every touching tone pair differs by >= {args.min_tonal_gap} luminance")
    else:
        check("banded shading", f"{len(colors)} colours", True, "too few tones to band")

    # 6. light consistency.
    #
    # Two formulations were tried and rejected. (a) The single globally lightest
    # colour: wrong under per-material shading, where every material has its own
    # highlight. (b) Auto-grouping colours into materials by luminance and hue:
    # wrong because saturation shifts at ramp ends, so a dark rule merges the
    # OUTLINE with the darkest step of two unrelated ramps, and bright ends of
    # different ramps collide. Auto-grouping is therefore reported as a hint and
    # never fails the audit.
    #
    # The reliable form needs the caller to say which tones form a material. The
    # workflow already computes those ramps, so passing them costs nothing.
    if not args.light:
        check("light consistency", "not checked", True, "pass --light to enable")
    else:
        dx, dy = LIGHT_VECTORS[args.light]
        proj = lambda x, y: x * dx + y * dy      # larger = nearer the light
        where = {c: [] for c in colors}
        for x, y in opaque:
            where[px[x, y]].append((x, y))

        def judge(members):
            members = [c for c in members if where.get(c)]
            if len(members) < 2:
                return None
            allpts = [p for c in members for p in where[c]]
            mean_all = sum(proj(*p) for p in allpts) / len(allpts)
            brightest = max(members, key=luminance)
            mean_b = sum(proj(*p) for p in where[brightest]) / len(where[brightest])
            return brightest, mean_b - mean_all

        if args.material:
            rows = [r for r in (judge([parse_color(c) for c in spec.split(",")])
                                for spec in args.material) if r]
            failed = [r for r in rows if r[1] <= 0]
            check("light consistency",
                  f"{len(rows) - len(failed)}/{len(rows)} declared materials lit "
                  f"from the {args.light}",
                  not failed,
                  "; ".join(f"brightest {hexof(b)} {d:+.0f}px" for b, d in rows)
                  + "  (positive = highlight sits on the light side)")
        else:
            rows = [r for r in (judge(m) for m in _auto_families(colors, args.light_band))
                    if r]
            if not rows:
                check("light consistency", "not checked", True,
                      "no multi-tone group found")
            else:
                passing = sum(1 for _, d in rows if d > 0)
                check("light consistency",
                      f"{passing}/{len(rows)} auto-groups lit correctly (advisory)",
                      True,
                      "auto-grouping is a hint only — it mis-groups ramp ends, so it "
                      "never fails the audit. Declare the ramps to judge exactly: "
                      "--material \"c1,c2,c3\"")
        # 7. silhouette cleanliness: 1px notches and spikes in the outline.
    #    These are the signature of machine-made edges — a hand-drawn silhouette
    #    steps in readable increments, not single-pixel jitter.
    notches = spikes = 0
    for y in range(h):
        for x in range(w):
            orth = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
            orth = [(a, b) for a, b in orth if 0 <= a < w and 0 <= b < h]
            on = sum(1 for a, b in orth if px[a, b][3] > 0)
            if px[x, y][3] == 0 and on >= 3:
                notches += 1
            elif px[x, y][3] > 0 and on <= 1:
                spikes += 1
    jaggy = notches + spikes
    check("silhouette cleanliness", f"{notches} notches, {spikes} spikes",
          jaggy <= args.max_jaggy,
          f"limit {args.max_jaggy} — 1px edge jitter is the machine-made tell")

    if args.ui:
        # UI-specific qualities. A panel is the inverse of a sprite: the interior
        # is *supposed* to be empty, and the information sits in a border of
        # constant thickness. Neither property is checked by the sprite defaults.
        w_, h_ = img.size
        mid = range(int(w_ * 0.2), int(w_ * 0.8)) or range(w_)

        def band(seq):
            """Thickness of the outermost opaque colour band, walking inward.

            Transparent lead-in is skipped: measuring from the very first pixel
            reports 0 for anything with padding or rounded corners, which is how
            an earlier version of this check managed to report every side as 0.
            """
            k = 0
            while k < len(seq) and seq[k][3] == 0:
                k += 1
            if k >= len(seq):
                return None
            colour, start = seq[k], k
            while k < len(seq) and seq[k] == colour:
                k += 1
            return k - start

        def median(vals):
            vals = sorted(v for v in vals if v is not None)
            return vals[len(vals) // 2] if vals else None

        sides = {
            "top": median(band([px[x, y] for y in range(h_)]) for x in mid),
            "bottom": median(band([px[x, y] for y in range(h_ - 1, -1, -1)]) for x in mid),
            "left": median(band([px[x, y] for x in range(w_)]) for y in range(h_)),
            "right": median(band([px[x, y] for x in range(w_ - 1, -1, -1)]) for y in range(h_)),
        }
        known = [v for v in sides.values() if v]
        if len(known) < 4:
            check("UI border thickness", "n/a", True,
                  "some sides have no opaque border to measure")
        else:
            spread = max(known) - min(known)
            check("UI border thickness", f"{sides} (spread {spread}px)", spread <= 1,
                  "a UI border must keep constant thickness on all four sides")

        # Interior flatness, measured over OPAQUE interior pixels only. Counting
        # transparent ones made a sprite "77% transparent" and told you nothing.
        t_, b_, l_, r_ = (sides["top"] or 0), (sides["bottom"] or 0), \
            (sides["left"] or 0), (sides["right"] or 0)
        inner = [px[x, y]
                 for y in range(min(t_ + 1, h_), max(h_ - b_ - 1, 0))
                 for x in range(min(l_ + 1, w_), max(w_ - r_ - 1, 0))]
        inner = [c for c in inner if c[3] > 0]
        if len(inner) < 16:
            check("UI interior flatness", "n/a", True, "interior too small to judge")
        else:
            counts = Counter(inner)
            dominant, dn = counts.most_common(1)[0]
            share, tones = dn / len(inner), len(counts)
            # Two conditions, not one. "One dominant tone" alone fails a progress
            # bar, whose interior is legitimately two large flat blocks (filled and
            # empty). A UI interior is flat when it has a dominant tone AND few
            # tones overall; a sprite interior has many tones whatever its
            # dominant share is.
            check("UI interior flatness",
                  f"{share*100:.0f}% one tone ({hexof(dominant)}), {tones} tones",
                  share >= args.ui_flat_min and tones <= args.ui_tones,
                  f"want >= {args.ui_flat_min*100:.0f}% in one tone and <= {args.ui_tones} "
                  f"tones; a bar's fill/empty split passes, a sprite's detail does not")

    width = max(len(r["check"]) for r in results)
    for r in results:
        mark = "PASS" if r["pass"] else "FAIL"
        print(f"  {mark}  {r['check']:<{width}}  {r['value']}")
        if r["detail"]:
            print(f"        {' ' * width}  {r['detail']}")
    failed = [r for r in results if not r["pass"]]
    print(f"audit: {len(results)-len(failed)}/{len(results)} checks passed"
          + ("  — asset reads as hand-made" if not failed else ""))
    if args.json:
        print(json.dumps({"file": args.infile, "size": [w, h], "opaque_px": total,
                          "results": results}, indent=2))
    return 0 if not failed else 1


# ------------------------------------------------------------------ misc

# ------------------------------------------------------------------ UI

def cmd_ui(args):
    """Generate a UI element: panel, button, or bar.

    UI is large-area and low-detail by nature: all of the information lives in
    the border and corners, and the interior is deliberately empty. That is the
    opposite of a sprite, where every region needs feature-scale detail -- which
    is why `audit --ui` treats a flat interior as correct rather than a defect.
    """
    w, h = (int(v) for v in args.size.lower().split("x"))
    img = Image.new("RGBA", (w, h), CLEAR)
    ramp = [parse_color(c) for c in args.ramp.split(",")]
    if len(ramp) < 3:
        raise SystemExit("ui --ramp needs at least 3 tones (dark, mid, light)")
    lo, mid, hi = ramp[0], ramp[len(ramp) // 2], ramp[-1]
    ink = parse_color(args.ink) if args.ink else ramp[0]
    t = max(1, args.border)
    d = ImageDraw.Draw(img)

    if args.radius:
        d.rounded_rectangle([0, 0, w - 1, h - 1], args.radius, fill=ink)
        d.rounded_rectangle([t, t, w - 1 - t, h - 1 - t], args.radius, fill=mid)
    else:
        d.rectangle([0, 0, w - 1, h - 1], fill=ink)
        d.rectangle([t, t, w - 1 - t, h - 1 - t], fill=mid)

    if args.kind in ("panel", "button"):
        i = t + args.bevel
        d.line([(i, i), (w - 1 - i, i)], fill=hi)
        d.line([(i, i), (i, h - 1 - i)], fill=hi)
        d.line([(w - 1 - i, i), (w - 1 - i, h - 1 - i)], fill=lo)
        d.line([(i, h - 1 - i), (w - 1 - i, h - 1 - i)], fill=lo)
        if args.state == "pressed":
            img = img.transpose(Image.FLIP_TOP_BOTTOM)
        elif args.state == "disabled":
            px = img.load()
            for yy in range(h):
                for xx in range(w):
                    if px[xx, yy][3] > 0:
                        r, g, b, a = px[xx, yy]
                        px[xx, yy] = (int(0.55 * r + 0.45 * 110),
                                      int(0.55 * g + 0.45 * 110),
                                      int(0.55 * b + 0.45 * 110), a)
    elif args.kind == "bar":
        ix, iy = t + 1, t + 1
        iw, ih = w - 2 * (t + 1), h - 2 * (t + 1)
        if iw <= 0 or ih <= 0:
            raise SystemExit(f"border {t} leaves no room inside a {w}x{h} bar")
        d.rectangle([ix, iy, ix + iw - 1, iy + ih - 1], fill=ink)
        filled = int(iw * max(0.0, min(1.0, args.pct)))
        if filled > 0:
            d.rectangle([ix, iy, ix + filled - 1, iy + ih - 1], fill=hi)
            d.line([(ix, iy), (ix + filled - 1, iy)], fill=ramp[-1])
    else:
        raise SystemExit(f"unknown ui kind: {args.kind}")

    allowed = ramp + [ink]
    px = img.load()
    for yy in range(img.height):
        for xx in range(img.width):
            c = px[xx, yy]
            if c[3] > 0 and c not in allowed:
                px[xx, yy] = min(allowed, key=lambda q: dist2(q, c))
    save(img, args.out)
    print(f"ui {args.kind} {w}x{h} state={args.state} -> {args.out}")
    return 0


def cmd_nineslice(args):
    """Scale a small skin to any size by tiling, keeping the corners 1:1.

    This is what makes UI cheap: author one tiny skin (say 24x24 with 8px corners)
    and get a 320x180 panel out of it. Nothing is resampled -- edge strips and the
    centre are tiled, so the result stays pixel-exact and the interior stays flat,
    which is exactly what UI wants.
    """
    src = load_image(args.infile)
    tw, th = (int(v) for v in args.size.lower().split("x"))
    c = args.corner
    if 2 * c >= min(src.width, src.height):
        raise SystemExit(f"corner {c} too large for a {src.width}x{src.height} skin")
    if tw < 2 * c or th < 2 * c:
        raise SystemExit(f"target {tw}x{th} must be at least {2 * c}x{2 * c}")
    out = Image.new("RGBA", (tw, th), CLEAR)
    sp, op = src.load(), out.load()
    mx, my = max(1, src.width - 2 * c), max(1, src.height - 2 * c)
    for y in range(th):
        for x in range(tw):
            if x < c:
                sx = x
            elif x >= tw - c:
                sx = src.width - (tw - x)
            else:
                sx = c + (x - c) % mx
            if y < c:
                sy = y
            elif y >= th - c:
                sy = src.height - (th - y)
            else:
                sy = c + (y - c) % my
            op[x, y] = sp[min(sx, src.width - 1), min(sy, src.height - 1)]
    save(out, args.out)
    if args.meta:
        meta = {"source": Path(args.infile).name, "target": [tw, th],
                "insets": {"left": c, "top": c, "right": c, "bottom": c},
                "note": "corners 1:1, edges and centre tiled"}
        Path(args.meta).write_text(json.dumps(meta, indent=2), encoding="utf-8")
        print(f"slice metadata -> {args.meta}")
    print(f"nineslice {src.width}x{src.height} corner={c} -> {tw}x{th} {args.out}")
    return 0


def cmd_batch(args):
    """Run many commands in ONE process, quietly.

    Two costs disappear at once. Per-command Python startup is ~145ms on this
    machine, so a 20-step build pays ~3s of pure interpreter overhead; and every
    command the agent issues is another model turn, which is where the real money
    goes. A batch is one call and prints one line unless a step fails.
    """
    import contextlib
    import io
    import shlex
    parser = build_parser()
    lines = Path(args.file).read_text(encoding="utf-8").splitlines()
    done, failed = 0, []
    for n, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            argv = shlex.split(line)
        except ValueError as exc:
            failed.append(f"line {n}: unparsable ({exc})")
            continue
        if argv and argv[0].endswith("pixel_forge.py"):
            argv = argv[1:]
        out_buf, err_buf = io.StringIO(), io.StringIO()
        try:
            with contextlib.redirect_stdout(out_buf), \
                    contextlib.redirect_stderr(err_buf):
                ns = parser.parse_args(argv)
                ns.func(ns)
            done += 1
        except BaseException as exc:
            # argparse reports usage errors on stderr and exits with code 2, so
            # reporting only the exception would give "FAIL: 2" and tell the
            # caller nothing. Surface the actual text instead.
            why = (err_buf.getvalue().strip() or out_buf.getvalue().strip()
                   or f"{type(exc).__name__}: {exc}")
            why = " ".join(why.split())[:220]
            failed.append(f"line {n} ({argv[0] if argv else '?'}): {why}")
    print(f"batch: {done} ok, {len(failed)} failed  [{Path(args.file).name}]")
    for f in failed[:8]:
        print(f"  FAIL {f}")
    return 0 if not failed else 1


def cmd_info(args):
    img = load_image(args.infile)
    data = all_pixels(img)
    opaque = [c for c in data if c[3] > 0]
    counts = Counter(opaque)
    print(f"file      : {args.infile}")
    print(f"size      : {img.width} x {img.height}")
    print(f"opaque px : {len(opaque)} / {len(data)}")
    print(f"colours   : {len(counts)}")
    if opaque:
        xs = [i % img.width for i, c in enumerate(data) if c[3] > 0]
        ys = [i // img.width for i, c in enumerate(data) if c[3] > 0]
        print(f"bounds    : x {min(xs)}-{max(xs)}, y {min(ys)}-{max(ys)}")
    for c, n in counts.most_common(8):
        print(f"  {hexof(c):<10} {n:>6} px")
    return 0


def cmd_preview(args):
    src = load_image(args.infile)
    s = args.scale
    big = src.resize((src.width * s, src.height * s), Image.NEAREST)
    pad, legend_w = 14, 30
    canvas = Image.new("RGBA", (big.width + pad * 2 + legend_w, big.height + pad * 2),
                       (26, 26, 34, 255))
    canvas.alpha_composite(big, (pad, pad))
    d = ImageDraw.Draw(canvas)
    if args.grid_lines and max(src.size) <= 96:
        for x in range(src.width + 1):
            d.line([(pad + x * s, pad), (pad + x * s, pad + big.height)], fill=(64, 64, 78, 255))
        for y in range(src.height + 1):
            d.line([(pad, pad + y * s), (pad + big.width, pad + y * s)], fill=(64, 64, 78, 255))
    counts = Counter(c for c in all_pixels(src) if c[3] > 0)
    lx, ly = big.width + pad + 4, pad
    for c, _ in counts.most_common(24):
        d.rectangle([lx, ly, lx + 14, ly + 14], fill=c, outline=(90, 90, 104, 255))
        ly += 18
    save(canvas, args.out)
    print(f"preview {s}x -> {args.out}")
    return 0


def cmd_palettes(_args):
    for n, cs in PALETTES.items():
        print(f"{n:<12} {len(cs)} colours")
    return 0


# ------------------------------------------------------------------ cli

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="constructive pixel-art tool")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("palettes").set_defaults(func=cmd_palettes)

    sp = sub.add_parser("canvas", help="create an empty canvas")
    sp.add_argument("--size", required=True, help="WxH")
    sp.add_argument("--bg", default="transparent")
    sp.add_argument("--out", required=True)
    sp.set_defaults(func=cmd_canvas)

    sp = sub.add_parser("shape", help="draw a crisp primitive (no anti-aliasing)")
    sp.add_argument("--in", dest="infile")
    sp.add_argument("--size", help="WxH, when starting a new canvas")
    sp.add_argument("--out", required=True)
    sp.add_argument("--kind", default="ellipse",
                    choices=["ellipse", "rect", "rrect", "line", "poly"])
    sp.add_argument("--box", help="x,y,w,h")
    sp.add_argument("--color", required=True)
    sp.add_argument("--radius", type=int, default=4)
    sp.add_argument("--width", type=int, default=1)
    sp.add_argument("--points", help='poly vertices "x,y x,y x,y"')
    sp.add_argument("--harden", action="store_true", default=True,
                    help="force exact colours (on by default)")
    sp.set_defaults(func=cmd_shape)

    sp = sub.add_parser("ramp", help="palette-snapped shading ramp")
    sp.add_argument("--from", dest="frm", required=True)
    sp.add_argument("--to", required=True)
    sp.add_argument("--steps", type=int, default=4)
    sp.add_argument("--palette")
    sp.set_defaults(func=cmd_ramp)

    sp = sub.add_parser("shade", help="banded directional shading")
    sp.add_argument("--in", dest="infile", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--ramp", required=True, help="c1,c2,c3[,c4]")
    sp.add_argument("--light", default="tl", choices=sorted(LIGHT_VECTORS))
    sp.add_argument("--color", help="only shade pixels of this colour")
    sp.set_defaults(func=cmd_shade)

    sp = sub.add_parser("dither", help="patterned dithering between two colours")
    sp.add_argument("--in", dest="infile", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--a", required=True)
    sp.add_argument("--b", required=True)
    sp.add_argument("--pattern", default="bayer2",
                    choices=["bayer2", "bayer4", "checker"])
    sp.add_argument("--level", type=float, default=0.5)
    sp.add_argument("--region", help="x,y,w,h")
    sp.set_defaults(func=cmd_dither)

    sp = sub.add_parser("outline", help="full or light-aware outline")
    sp.add_argument("--in", dest="infile", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--color", default="#000000")
    sp.add_argument("--mode", default="full", choices=["full", "light"])
    sp.add_argument("--light", default="tl", choices=sorted(LIGHT_VECTORS))
    sp.set_defaults(func=cmd_outline)

    sp = sub.add_parser("blocksnap", help="quantise detail to NxN blocks")
    sp.add_argument("--in", dest="infile", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--block", type=int, required=True)
    sp.set_defaults(func=cmd_blocksnap)

    sp = sub.add_parser("clean", help="remove pixel noise")
    sp.add_argument("--in", dest="infile", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--min-neighbors", type=int, default=1)
    sp.add_argument("--passes", type=int, default=1)
    sp.set_defaults(func=cmd_clean)

    sp = sub.add_parser("snap", help="force colours onto one palette")
    sp.add_argument("--in", dest="infile", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--palette", required=True)
    sp.set_defaults(func=cmd_snap)

    sp = sub.add_parser("recolor", help="palette swap (variants)")
    sp.add_argument("--in", dest="infile", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--map", nargs="+", required=True, metavar="OLD=NEW")
    sp.set_defaults(func=cmd_recolor)

    sp = sub.add_parser("grid", help="render a character grid (small sprites)")
    sp.add_argument("--spec", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--mirror-x", action="store_true")
    sp.set_defaults(func=cmd_grid)

    sp = sub.add_parser("frames", help="derive an animation cycle from one sprite")
    sp.add_argument("--in", dest="infile", required=True)
    sp.add_argument("--out-dir", required=True)
    sp.add_argument("--count", type=int, default=6)
    sp.add_argument("--bob", type=int, default=1, help="vertical amplitude in px")
    sp.add_argument("--sway", type=int, default=0, help="horizontal amplitude in px")
    sp.add_argument("--squash", type=int, default=0, help="rows of squash/stretch")
    sp.add_argument("--anchor", default="bottom", choices=["bottom", "free"],
                    help="bottom: keep the feet planted (default); free: translate it all")
    sp.set_defaults(func=cmd_frames)

    sp = sub.add_parser("flip", help="mirror horizontally or vertically")
    sp.add_argument("--in", dest="infile", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--axis", default="h", choices=["h", "v", "both"])
    sp.set_defaults(func=cmd_flip)

    sp = sub.add_parser("rotate", help="rotate by a right angle")
    sp.add_argument("--in", dest="infile", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--degrees", type=int, default=180, choices=[90, 180, 270])
    sp.set_defaults(func=cmd_rotate)

    sp = sub.add_parser("paste", help="composite pixel-exactly (no blending)")
    sp.add_argument("--in", dest="infile", required=True)
    sp.add_argument("--src", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--at", required=True, help="x,y")
    sp.add_argument("--flip", choices=["h", "v", "both"])
    sp.add_argument("--rotate", type=int, choices=[90, 180, 270])
    sp.set_defaults(func=cmd_paste)

    sp = sub.add_parser("text", help="render text from the built-in 5x7 font")
    sp.add_argument("--in", dest="infile")
    sp.add_argument("--size", help="WxH when starting a new canvas")
    sp.add_argument("--out", required=True)
    sp.add_argument("--at", default="0,0", help="x,y top-left of the first glyph")
    sp.add_argument("--string", required=True)
    sp.add_argument("--color", required=True)
    sp.add_argument("--scale", type=int, default=1)
    sp.set_defaults(func=cmd_text)

    sp = sub.add_parser("sheet", help="frames -> sprite sheet (+ atlas)")
    sp.add_argument("--frames", nargs="+", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--columns", type=int)
    sp.add_argument("--tile-w", type=int)
    sp.add_argument("--tile-h", type=int)
    sp.add_argument("--atlas", help="write a JSON atlas too")
    sp.set_defaults(func=cmd_sheet)

    sp = sub.add_parser("loopcheck", help="verify an animation set")
    sp.add_argument("--frames", nargs="+", required=True)
    sp.add_argument("--anchor-tolerance", type=int, default=0)
    sp.add_argument("--jump-ratio", type=float, default=2.5,
                    help="fail if one step exceeds median x this")
    sp.add_argument("--seam-ratio", type=float, default=2.5,
                    help="fail if the loop seam exceeds median x this")
    sp.add_argument("--open-ended", action="store_true",
                    help="not a loop: skip the first/last seam check")
    sp.set_defaults(func=cmd_loopcheck)

    sp = sub.add_parser("audit", help="measure the seven machine-made tells")
    sp.add_argument("infile")
    sp.add_argument("--palette")
    sp.add_argument("--max-colors", type=int, default=32)
    sp.add_argument("--max-isolated", type=float, default=0.02)
    sp.add_argument("--min-run-share", type=float, default=0.25)
    sp.add_argument("--aa-tolerance", type=int, default=10)
    sp.add_argument("--min-tonal-gap", type=float, default=6.0)
    sp.add_argument("--max-smooth-gaps", type=int, default=2)
    sp.add_argument("--light")
    sp.add_argument("--material", action="append", default=[],
                    help='comma-separated ramp for one material, repeatable')
    sp.add_argument("--light-band", type=float, default=90.0,
                    help="max luminance gap for two tones to count as one ramp")
    sp.add_argument("--ui", action="store_true",
                    help="also run UI-specific checks (border thickness, interior flatness)")
    sp.add_argument("--ui-flat-min", type=float, default=0.45)
    sp.add_argument("--ui-tones", type=int, default=6,
                    help="max distinct tones allowed in a UI interior")
    sp.add_argument("--max-jaggy", type=int, default=8,
                    help="allowed 1px notches+spikes on the silhouette")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_audit)

    sp = sub.add_parser("ui", help="generate a UI element (large area, low detail)")
    sp.add_argument("--kind", default="panel", choices=["panel", "button", "bar"])
    sp.add_argument("--size", required=True, help="WxH")
    sp.add_argument("--out", required=True)
    sp.add_argument("--ramp", required=True, help="c1,c2,...,cN (dark..light)")
    sp.add_argument("--border", type=int, default=2)
    sp.add_argument("--bevel", type=int, default=1)
    sp.add_argument("--radius", type=int, default=0)
    sp.add_argument("--state", default="normal",
                    choices=["normal", "hover", "pressed", "disabled"])
    sp.add_argument("--pct", type=float, default=0.5)
    sp.add_argument("--ink", help="override the outline colour")
    sp.set_defaults(func=cmd_ui)

    sp = sub.add_parser("nineslice", help="scale a small UI skin to any size (tiled)")
    sp.add_argument("--in", dest="infile", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--size", required=True, help="target WxH")
    sp.add_argument("--corner", type=int, required=True)
    sp.add_argument("--meta", help="write engine slice metadata JSON")
    sp.set_defaults(func=cmd_nineslice)

    sp = sub.add_parser("batch", help="run a build script in one process (quiet)")
    sp.add_argument("file")
    sp.set_defaults(func=cmd_batch)

    sp = sub.add_parser("info")
    sp.add_argument("infile")
    sp.set_defaults(func=cmd_info)

    sp = sub.add_parser("preview")
    sp.add_argument("--in", dest="infile", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--scale", type=int, default=6)
    sp.add_argument("--grid-lines", action="store_true")
    sp.set_defaults(func=cmd_preview)

    return p


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
