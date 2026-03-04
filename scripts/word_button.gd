extends Button

var category: String = ""   # "salutation" / "body" / "signature"
var body_slot: String = ""  # "slot1" / "slot2" / "slot3" for body

func _get_drag_data(_at_position: Vector2):
	if text == "":
		return null
	var data := {
		"type": "word",
		"word": text,
		"category": category,
		"body_slot": body_slot,
	}
	var preview := Label.new()
	preview.text = text
	preview.add_theme_color_override("font_color", Color.WHITE)
	preview.add_theme_color_override("font_outline_color", Color.BLACK)
	preview.add_theme_constant_override("outline_size", 2)
	set_drag_preview(preview)
	return data

