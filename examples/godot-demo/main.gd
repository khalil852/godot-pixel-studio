extends Node2D
## Minimal demo scene for the README GIF. Assets come straight out of
## pixel_draw.py — no editing in between, which is the point being shown.

const GROUND_Y := 132
const SCALE := 2.0

var hero: Sprite2D
var slime: Sprite2D
var t := 0.0


func _ready() -> void:
	var bg := ColorRect.new()
	bg.color = Color(0.13, 0.14, 0.20)
	bg.size = Vector2(320, 180)
	add_child(bg)

	# Ground strip — the same 16x16 tile repeated. If the tile size were off by
	# even one pixel you would see seams here, which is the point.
	var grass := load("res://grass-tile.png") as Texture2D
	for i in range(24):
		var s := Sprite2D.new()
		s.texture = grass
		s.centered = false
		s.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		s.scale = Vector2(SCALE, SCALE)
		s.position = Vector2(i * 16 * SCALE - 8, GROUND_Y)
		add_child(s)

	hero = _sprite("res://hero-idle.png", Vector2(96, GROUND_Y))
	slime = _sprite("res://slime-idle.png", Vector2(172, GROUND_Y))


func _sprite(path: String, foot: Vector2) -> Sprite2D:
	var s := Sprite2D.new()
	s.texture = load(path) as Texture2D
	s.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	s.scale = Vector2(SCALE, SCALE)
	s.centered = false
	s.position = Vector2(foot.x, foot.y - s.texture.get_height() * SCALE)
	add_child(s)
	return s


func _process(delta: float) -> void:
	t += delta
	# Quantise the bob to whole pixels: sub-pixel motion is exactly what makes
	# pixel art shimmer, so the demo must not do it.
	var bob := int(round(sin(t * 3.0)))
	hero.position.y = GROUND_Y - hero.texture.get_height() * SCALE + bob
	slime.position.y = GROUND_Y - slime.texture.get_height() * SCALE + int(round(sin(t * 3.0 + 1.3)))
	# Slow drift so the "game is running" reads as motion, not a still frame.
	hero.position.x = 36.0 + fmod(t * 26.0, 236.0)
