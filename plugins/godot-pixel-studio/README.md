# godot-pixel-studio

A small pixel-art game studio for **Godot 4.x 2D** projects: seven role skills and a
deterministic character-grid drawing tool.

## The seven roles

| Skill | Role |
|---|---|
| `godot-pixel-studio` | Director — decides which discipline leads, and in what order |
| `game-designer` | Core loop, player verbs, and a hard scope cap |
| `pixel-art-director` | Art bible: base resolution, palette, asset manifest |
| `pixel-artist` | Draws the sprites and tiles |
| `godot-programmer` | Godot 4 GDScript: movement, state machines, Resources, signals |
| `godot-scene-builder` | Node trees, `TileMapLayer`, collision layers, Y-sorting |
| `pixel-qa` | Runs the project and reports measured defects |

The workflow is **design brief → art bible → art → code → scenes → QA**, in small
loops with a QA gate between them.

## The drawing tool

`scripts/pixel_draw.py` renders a character grid to PNG:

```bash
python scripts/pixel_draw.py grid --spec examples/slime-idle.txt --out slime.png
python scripts/pixel_draw.py preview --in slime.png --out slime-x8.png --scale 8 --grid-lines
```

Also: `outline`, `recolor`, `snap`, `sheet`, `info`, `mirror`, `palettes`. Built-in
palettes: `pico8`, `sweetie16`, `gameboy`, `1bit`.

For assets above roughly 32px, use the **pixel-art-forge** plugin instead — a
character grid stops being readable there, and its constructive path is the right
tool.

## Scope note

This plugin is Godot-specific. Since it was written, most of the general pixel-art
work moved into `pixel-art-forge` and the process discipline into `game-studio-sim`.
This one remains the Godot-specific layer: its references are about Godot project
settings, GDScript, tilemaps and Y-sorting.

## License

MIT.
