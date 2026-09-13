# Godot Pixel Studio

A pixel-art game studio for **Codex** — role-based skills plus a deterministic
pixel drawing tool, aimed at **Godot 4.x 2D pixel-art** projects.

> This repository is a Codex plugin marketplace named `codexskill`. It currently
> ships one plugin, `godot-pixel-studio`; the marketplace layout supports adding
> more under `plugins/`.

![16x16 slime sprite](docs/slime-enlarged.png)

*The slime above is rendered from a plain-text character grid — every pixel is
authored, not sampled from a generative model.*

---

## The problem

Asking an LLM for pixel art usually produces something that *looks* like pixel
art but is unusable in an engine:

- it is **anti-aliased** (soft edges, hundreds of colours) instead of crisp pixels,
- it is **off-palette**, so it clashes with every other asset,
- sprites come back at **inconsistent sizes**, so frames pop and collisions drift,
- it cannot be **edited precisely** — you cannot ask for "move the eye one pixel left"
  and get a deterministic result.

And game projects fail for a second reason: the model starts writing code before
art direction and scope exist, so the game grows sideways and never ships.

This plugin addresses both.

## What's inside

### A studio of seven roles

| Skill | Role |
|---|---|
| `godot-pixel-studio` | **Director** — decides which discipline leads, and in what order |
| `game-designer` | Core loop, player verbs, and a hard **scope cap** |
| `pixel-art-director` | Art bible: base resolution, palette, and an explicit asset manifest |
| `pixel-artist` | Draws the sprites and tiles |
| `godot-programmer` | Godot 4 GDScript: movement, state machines, Resources, signals |
| `godot-scene-builder` | Node trees, `TileMapLayer`, collision layers, Y-sorting |
| `pixel-qa` | Runs the project and reports concrete defects with measurements |

The workflow is: **design brief → art bible → art → code → scenes → QA**, in small
loops with a QA gate between them.

### A deterministic pixel drawing tool

`scripts/pixel_draw.py` (Python + Pillow, no other dependencies).

The core idea: **pixel art needs per-pixel control, not probabilistic
generation.** So the main entry point turns a **character grid into a PNG**. The
result is exact, diff-able, and reviewable in a pull request.

```bash
python plugins/godot-pixel-studio/scripts/pixel_draw.py palette pico8
python plugins/godot-pixel-studio/scripts/pixel_draw.py grid --spec examples/slime-idle.txt --out slime.png
python plugins/godot-pixel-studio/scripts/pixel_draw.py preview --in slime.png --out slime-x8.png --scale 8 --grid-lines
```

| Command | Purpose |
|---|---|
| `grid` | Render a character grid to PNG (**core**) |
| `preview` | Integer-scaled preview with grid overlay and palette legend |
| `outline` | Add a 1px outline |
| `recolor` | Palette-swap to make enemy tiers / damage variants |
| `snap` | Force colours onto one palette |
| `sheet` | Assemble frames into a sprite sheet |
| `info` | Inspect size, colour count, bounding box |
| `mirror` | Flip horizontally |
| `palettes` / `palette` | Built-in palettes: `pico8`, `sweetie16`, `gameboy`, `1bit` |

Authoring a sprite looks like this:

```text
name: slime-idle-01
legend:
  ".": transparent
  "k": "#1a1c2c"   # outline
  "b": "#41a6f6"   # body base
  "B": "#3b5dc9"   # body shadow
  "w": "#f4f4f4"   # eye highlight
grid:
.....kkkkkk.....
....kbbbbbbk....
...kbwwbbwwbk...
...kbbBBBBbbk...
```

Symmetric characters can be authored as half a grid and mirrored
(`--mirror-x`):

![15x16 mirrored character](docs/hero-enlarged.png)

### Reference documents

- `godot4-pixel-perfect.md` — project settings, texture filtering, camera
  rounding, the sub-pixel jitter problem, and a symptom → cause table
- `animation-and-spritesheet.md` — frame layout, anchor discipline, timing
- `palette-and-shading.md` — building shading ramps, outlines, dithering

## Install

This repository is a Codex plugin marketplace, so you can install straight from
it:

```bash
codex plugin marketplace add khalil852/codexskill
codex plugin add godot-pixel-studio@codexskill
```

Then **restart Codex and open a new thread** — skills are loaded per thread, so an
existing session will not see the new roles.

Verify it worked by asking: *"what skills do you have available?"* — you should
see `godot-pixel-studio` and its six role skills.

## Requirements

- **Codex** with plugin support
- **Python 3.9+** with **Pillow** (`python -m pip install pillow`)
- **Godot 4.x** for the engine-side skills (developed against Godot 4.7)

## Quick start

Once installed, restart Codex and start a new thread:

> Start a Godot 4 pixel-art game. Write the design brief and art bible first.

The director skill will route to `game-designer` and `pixel-art-director` before
any code or art is produced. To draw something immediately:

> Draw a 16x16 pixel-art coin using the pico8 palette and show me the enlarged preview.

## Repository layout

```text
.
├── .agents/plugins/marketplace.json      # marketplace manifest
├── examples/                             # runnable grid specs + rendered output
├── docs/                                 # images for this README
└── plugins/godot-pixel-studio/
    ├── .codex-plugin/plugin.json
    ├── skills/                           # seven role skills
    ├── scripts/pixel_draw.py             # the drawing tool
    └── references/                       # Godot 4 and pixel-art reference docs
```

## Design notes

- **Why text grids instead of image generation?** Determinism and editability.
  A grid is a source file: it diffs, it reviews, and one pixel can be changed
  precisely. Generated images give none of that.
- **Why 7 separate skills instead of one big prompt?** Each discipline has hard
  rules that conflict (design wants scope, art wants consistency, QA wants
  evidence). Keeping them separate keeps those rules enforceable, and mirrors how
  roles are actually separated on a team.
- **Why insist on an asset manifest?** Sprite size and anchor are contracts
  between art and code. Undeclared sizes are the root cause of popping animation
  and collision drift.

## License

MIT — see [LICENSE](LICENSE).

---

## 中文说明

这是一个给 **Codex** 用的「Godot 4 像素风游戏工作室」插件：7 个角色 skill
（导演 / 策划 / 美术总监 / 像素画师 / 程序 / 场景 / QA）加一个**确定性像素绘画工具**。

核心设计：**像素画靠精确控制每个像素，不靠概率生成**。所以作画主入口是
「字符网格 → PNG」——用调色板字符写网格，输出完全确定、可 diff、可复查，
而不是让模型生成一张带抗锯齿、调色板混乱、尺寸不一的图。

安装后需要**重启 Codex 并开新会话**（skill 按会话加载，旧会话看不到新角色）。

示例即仓库里的 `examples/`：`slime-idle.txt` 是显式 `legend` 写法，
`hero-idle-half.txt` 演示对称角色只画左半再用 `--mirror-x` 镜像，
`grass-tile.txt` 演示直接用内置调色板索引。

依赖：Python 3.9+ 与 Pillow；引擎侧针对 Godot 4.x（开发时用的是 4.7）。
