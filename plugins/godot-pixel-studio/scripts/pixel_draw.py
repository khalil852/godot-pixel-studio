#!/usr/bin/env python3
"""pixel_draw —— 确定性像素绘画工具（Godot 2D 像素游戏用）。

设计理念：像素画要靠精确控制每个像素，而不是靠概率生成的图片。
所以主入口是「字符网格 -> PNG」：用调色板字符画一张图，结果是完全确定的、可复查的、可 diff 的。

子命令：
  palettes                     列出内置调色板
  palette <name>               打印某个调色板的字符->颜色对照
  grid --spec F --out F        由字符网格渲染出 PNG（核心）
  outline --in F --out F       给不透明像素加 1px 描边
  recolor --in F --out F       替换颜色（做换色变体）
  mirror --in F --out F        水平镜像
  info F                       检查 PNG：尺寸/颜色数/透明度/是否像素对齐
  sheet --frames ... --out F   把多帧拼成精灵表（spritesheet）
  preview --in F --out F       放大预览（带网格与调色板图例，仅用于审阅）

所有命令在 Windows/Linux/macOS 下均可运行，仅依赖 Pillow。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:  # pragma: no cover
    raise SystemExit("需要 Pillow：python -m pip install pillow")

TRANSPARENT_CHARS = {".", " "}

# 内置调色板（值为标准公开配色，字符 0-9a-f 依次对应）
PALETTES: dict[str, list[str]] = {
    "pico8": [
        "#000000", "#1D2B53", "#7E2553", "#008751",
        "#AB5236", "#5F574F", "#C2C3C7", "#FFF1E8",
        "#FF004D", "#FFA300", "#FFEC27", "#00E436",
        "#29ADFF", "#83769C", "#FF77A8", "#FFCCAA",
    ],
    "sweetie16": [
        "#1a1c2c", "#5d275d", "#b13e53", "#ef7d57",
        "#ffcd75", "#a7f070", "#38b764", "#257179",
        "#29366f", "#3b5dc9", "#41a6f6", "#73eff7",
        "#f4f4f4", "#94b0c2", "#566c86", "#333c57",
    ],
    "gameboy": ["#0F380F", "#306230", "#8BAC0F", "#9BBC0F"],
    "1bit": ["#000000", "#FFFFFF"],
}

PALETTE_CHARS = "0123456789abcdefghijklmnopqrstuvwxyz"


# ---------------------------------------------------------------- 颜色工具

def parse_color(text: str) -> tuple[int, int, int, int]:
    """支持 #rgb / #rrggbb / #rrggbbaa / transparent。"""
    t = text.strip().strip('"').strip("'").lower()
    if t in ("transparent", "none", "clear"):
        return (0, 0, 0, 0)
    if t.startswith("#"):
        t = t[1:]
    if len(t) == 3:
        t = "".join(c * 2 for c in t)
    if len(t) == 6:
        t += "ff"
    if len(t) != 8:
        raise ValueError(f"无法解析颜色: {text}")
    return (int(t[0:2], 16), int(t[2:4], 16), int(t[4:6], 16), int(t[6:8], 16))


def to_hex(rgba: tuple[int, int, int, int]) -> str:
    r, g, b, a = rgba
    return "transparent" if a == 0 else f"#{r:02x}{g:02x}{b:02x}"


def load_image(path) -> Image.Image:
    """读图并转 RGBA。文件不存在时给出干净的错误信息，而不是 traceback。"""
    f = Path(path)
    if not f.is_file():
        raise SystemExit(f"找不到文件: {path}")
    try:
        return Image.open(f).convert("RGBA")
    except Exception as exc:
        raise SystemExit(f"无法读取图片 {path}: {exc}")


def nearest_palette_color(rgba, palette):
    """把颜色吸附到调色板里最接近的一个（欧氏距离，忽略 alpha）。"""
    r, g, b, _ = rgba
    best, best_d = None, None
    for c in palette:
        cr, cg, cb, _ = c
        d = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
        if best_d is None or d < best_d:
            best, best_d = c, d
    return best


def all_pixels(img) -> list:
    """取出全部像素。不用 img.getdata() —— 它在 Pillow 12+ 已弃用并会打印警告，
    污染 Codex 读取的命令输出。"""
    px = img.load()
    w, h = img.size
    return [px[x, y] for y in range(h) for x in range(w)]


# ---------------------------------------------------------------- 网格规格解析

# 行尾注释：只在 '#' 前面有空白时才当注释切掉。
# 这样 `"k": "#1a1c2c"   # 描边` 能正确取到颜色，
# 而颜色值自身的 '#'（前面没有空白）不会被误切。
_COMMENT_RE = re.compile(r"\s+#")


def strip_comment(line: str) -> str:
    return _COMMENT_RE.split(line, maxsplit=1)[0].rstrip()


def parse_spec(path: Path) -> dict:
    """解析字符网格规格。

    支持两种写法：
      palette: pico8          # 用调色板索引字符（0-9a-f）
      legend:                 # 或者显式指定字符->颜色
        ".": transparent
        "k": "#1a1c2c"        # 行尾注释可以随便写
      grid:
        ..kk..
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    block = None
    legend_lines, grid_lines = [], []
    for raw in lines:
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        stripped = line.strip()
        if stripped in ("grid:", "legend:"):
            block = stripped[:-1]
            continue
        if stripped.startswith(("name:", "palette:", "scale:", "author:")):
            block = None
            continue
        if block == "legend":
            legend_lines.append(strip_comment(line).strip())
        elif block == "grid":
            grid_lines.append(strip_comment(line).strip())

    if not grid_lines:
        raise SystemExit(f"{path}: 没找到 grid: 块")

    # 目标是显式 legend 优先
    legend: dict[str, tuple[int, int, int, int]] = {}
    for item in legend_lines:
        if ":" not in item:
            continue
        ch, col = item.split(":", 1)
        ch = ch.strip().strip('"').strip("'")
        col = col.strip().strip('"').strip("'")
        try:
            legend[ch] = parse_color(col)
        except ValueError:
            raise SystemExit(f"{path}: 无法解析 legend 里的颜色 -> {ch!r}: {col!r}")

    palette_name = None
    for raw in lines:
        if raw.strip().startswith("palette:"):
            palette_name = strip_comment(raw).split(":", 1)[1].strip()

    index_map: dict[str, tuple[int, int, int, int]] = {}
    if not legend:
        if not palette_name or palette_name not in PALETTES:
            raise SystemExit(
                f"{path}: 需要 legend: 块，或 palette: 指向内置调色板（{'/'.join(PALETTES)}）")
        for i, hexv in enumerate(PALETTES[palette_name]):
            index_map[PALETTE_CHARS[i]] = parse_color(hexv)

    # 校验宽度一致：必须报出"实际不符的行"，否则作者会照着错的行号去改
    counts = Counter(len(r) for r in grid_lines)
    width = counts.most_common(1)[0][0]
    bad = [(i + 1, len(r)) for i, r in enumerate(grid_lines) if len(r) != width]
    if bad:
        shown = ", ".join(f"第{i}行({w}字符)" for i, w in bad[:12])
        raise SystemExit(
            f"{path}: 网格每行必须是 {width} 字符，但以下行不符 -> {shown}"
            + ("  …" if len(bad) > 12 else ""))
    return {"grid": grid_lines, "width": width, "height": len(grid_lines),
            "legend": legend, "index_map": index_map}


def render_grid(spec: dict, mirror_x: bool = False) -> Image.Image:
    grid = spec["grid"]
    h, w = spec["height"], spec["width"]
    out_w = w * 2 - 1 if mirror_x else w
    img = Image.new("RGBA", (out_w, h), (0, 0, 0, 0))
    px = img.load()
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch in TRANSPARENT_CHARS:
                continue
            color = spec["legend"].get(ch, spec["index_map"].get(ch))
            if color is None:
                raise SystemExit(f"网格里有未定义的字符 {ch!r}（第{y+1}行第{x+1}列）")
            px[x, y] = color
            if mirror_x and 0 <= out_w - 1 - x < out_w:
                px[out_w - 1 - x, y] = color
    return img


# ---------------------------------------------------------------- 子命令

def cmd_palettes(_args):
    for name, colors in PALETTES.items():
        print(f"{name:<12} {len(colors)} 色")
    return 0


def cmd_palette(args):
    colors = PALETTES.get(args.name)
    if not colors:
        raise SystemExit(f"没有这个调色板: {args.name}（可选: {'/'.join(PALETTES)}）")
    print(f"{args.name}: {len(colors)} 色")
    for i, hexv in enumerate(colors):
        rgba = parse_color(hexv)
        print(f"  {PALETTE_CHARS[i]}  {hexv}  rgb{rgba[:3]}")
    return 0


def cmd_grid(args):
    spec = parse_spec(Path(args.spec))
    img = render_grid(spec, mirror_x=args.mirror_x)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    colors = {c for c in all_pixels(img) if c[3] > 0}
    print(f"已生成 {out}  {img.width}x{img.height}  不透明颜色 {len(colors)} 种")
    return 0


def cmd_outline(args):
    src = load_image(args.infile)
    color = parse_color(args.color)
    w, h = src.size
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(src, (0, 0))
    op = src.load()
    np_ = out.load()
    for y in range(h):
        for x in range(w):
            if op[x, y][3] != 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and op[nx, ny][3] != 0:
                    np_[x, y] = color
                    break
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.save(args.out)
    print(f"已加描边 {to_hex(color)} -> {args.out}")
    return 0


def cmd_recolor(args):
    src = load_image(args.infile)
    mapping = {}
    for pair in args.map:
        old, new = pair.split("=", 1)
        mapping[parse_color(old)] = parse_color(new)
    px = src.load()
    changed = 0
    for y in range(src.height):
        for x in range(src.width):
            c = px[x, y]
            if c in mapping:
                px[x, y] = mapping[c]
                changed += 1
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    src.save(args.out)
    print(f"已替换 {changed} 个像素 -> {args.out}")
    return 0


def cmd_mirror(args):
    src = load_image(args.infile)
    out = src.transpose(Image.FLIP_LEFT_RIGHT)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.save(args.out)
    print(f"已水平镜像 -> {args.out}")
    return 0


def cmd_info(args):
    img = load_image(args.infile)
    data = all_pixels(img)
    opaque = [c for c in data if c[3] > 0]
    counts = Counter(opaque)
    print(f"文件      : {args.infile}")
    print(f"尺寸      : {img.width} x {img.height}")
    print(f"不透明像素: {len(opaque)} / {len(data)}")
    print(f"颜色数    : {len(counts)}")
    if opaque:
        ys = [i // img.width for i, c in enumerate(data) if c[3] > 0]
        xs = [i % img.width for i, c in enumerate(data) if c[3] > 0]
        print(f"内容包围盒: x {min(xs)}-{max(xs)}, y {min(ys)}-{max(ys)}")
    print("颜色占比  :")
    for c, n in counts.most_common(12):
        print(f"  {to_hex(c):<12} {n:>5} px")
    if args.json:
        print(json.dumps({"width": img.width, "height": img.height,
                          "colors": {to_hex(c): n for c, n in counts.items()}},
                         ensure_ascii=False))
    return 0


def cmd_sheet(args):
    frames = [Path(p) for p in args.frames]
    if not frames:
        raise SystemExit("需要至少一帧 --frames")
    imgs = [load_image(f) for f in frames]
    tw = args.tile_w or max(i.width for i in imgs)
    th = args.tile_h or max(i.height for i in imgs)
    cols = args.columns or len(imgs)
    rows = (len(imgs) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * tw, rows * th), (0, 0, 0, 0))
    for i, im in enumerate(imgs):
        if im.size != (tw, th):
            print(f"警告: {frames[i].name} 尺寸 {im.size} != {tw}x{th}，按左上角贴合", file=sys.stderr)
        sheet.paste(im, ((i % cols) * tw, (i // cols) * th))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.out)
    print(f"已生成精灵表 {args.out}  {sheet.width}x{sheet.height}  {cols}列 x {rows}行  单元 {tw}x{th}")
    return 0


def cmd_preview(args):
    src = load_image(args.infile)
    scale = args.scale
    big = src.resize((src.width * scale, src.height * scale), Image.NEAREST)
    pad = 12
    grid_w = 26
    canvas = Image.new("RGBA", (big.width + pad * 2 + grid_w, big.height + pad * 2), (24, 24, 32, 255))
    canvas.paste(big, (pad, pad))
    d = ImageDraw.Draw(canvas)
    if args.grid_lines and src.width <= 64 and src.height <= 64:
        for x in range(src.width + 1):
            d.line([(pad + x * scale, pad), (pad + x * scale, pad + big.height)],
                   fill=(70, 70, 84, 255))
        for y in range(src.height + 1):
            d.line([(pad, pad + y * scale), (pad + big.width, pad + y * scale)],
                   fill=(70, 70, 84, 255))
    # 图例：列出实际使用的颜色
    counts = Counter(c for c in all_pixels(src) if c[3] > 0)
    lx = big.width + pad + 4
    ly = pad
    for c, _ in counts.most_common(20):
        d.rectangle([lx, ly, lx + 12, ly + 12], fill=c, outline=(90, 90, 104, 255))
        ly += 16
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    canvas.save(args.out)
    print(f"已生成预览 {args.out}  放大 {scale}x（仅供审阅，不要用于游戏资源）")
    return 0


def cmd_snap(args):
    """把图片颜色吸附到指定调色板 —— 用于统一风格或压缩颜色数。"""
    src = load_image(args.infile)
    palette = [parse_color(h) for h in PALETTES[args.palette]]
    px = src.load()
    for y in range(src.height):
        for x in range(src.width):
            c = px[x, y]
            if c[3] == 0:
                continue
            px[x, y] = nearest_palette_color(c, palette)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    src.save(args.out)
    print(f"已吸附到 {args.palette} 调色板 -> {args.out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="确定性像素绘画工具")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("palettes", help="列出内置调色板").set_defaults(func=cmd_palettes)

    sp = sub.add_parser("palette", help="查看某个调色板的字符对照")
    sp.add_argument("name")
    sp.set_defaults(func=cmd_palette)

    sp = sub.add_parser("grid", help="字符网格 -> PNG（核心）")
    sp.add_argument("--spec", required=True, help="网格规格文件")
    sp.add_argument("--out", required=True, help="输出 PNG")
    sp.add_argument("--mirror-x", action="store_true", help="右半镜像左半（画对称角色省一半）")
    sp.set_defaults(func=cmd_grid)

    sp = sub.add_parser("outline", help="加 1px 描边")
    sp.add_argument("--in", dest="infile", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--color", default="#000000")
    sp.set_defaults(func=cmd_outline)

    sp = sub.add_parser("recolor", help="替换颜色（做换色变体）")
    sp.add_argument("--in", dest="infile", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--map", nargs="+", required=True, metavar="OLD=NEW",
                    help="例如 --map '#ff0000=#00ff00' '#000000=#ffffff'")
    sp.set_defaults(func=cmd_recolor)

    sp = sub.add_parser("mirror", help="水平镜像")
    sp.add_argument("--in", dest="infile", required=True)
    sp.add_argument("--out", required=True)
    sp.set_defaults(func=cmd_mirror)

    sp = sub.add_parser("info", help="检查 PNG（尺寸/颜色/透明度）")
    sp.add_argument("infile")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_info)

    sp = sub.add_parser("sheet", help="多帧 -> 精灵表")
    sp.add_argument("--frames", nargs="+", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--columns", type=int)
    sp.add_argument("--tile-w", type=int)
    sp.add_argument("--tile-h", type=int)
    sp.set_defaults(func=cmd_sheet)

    sp = sub.add_parser("preview", help="放大预览（审阅用）")
    sp.add_argument("--in", dest="infile", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--scale", type=int, default=8)
    sp.add_argument("--grid-lines", action="store_true", help="叠加像素网格")
    sp.set_defaults(func=cmd_preview)

    sp = sub.add_parser("snap", help="把颜色吸附到调色板（统一风格）")
    sp.add_argument("--in", dest="infile", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--palette", default="pico8")
    sp.set_defaults(func=cmd_snap)

    return p


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
