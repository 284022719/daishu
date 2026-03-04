extends Panel

signal word_dropped(slot_key: String, word: String)

@export var slot_key: String = ""           # "salutation", "body_slot1" 等
@export var expected_category: String = ""  # "salutation" / "body" / "signature"
@export var body_slot: String = ""          # "slot1" / "slot2" / "slot3" for body
@export var placeholder: String = "______"

@onready var text_label: Label = $TextLabel

var _base_modulate: Color

var _border_color: Color = Color(0, 0, 0, 0.5)
var _border_width: float = 1.5
var _dash_length: float = 8.0
var _gap_length: float = 4.0

func _ready() -> void:
	_base_modulate = modulate
	if text_label:
		text_label.text = _to_vertical(placeholder)
	mouse_entered.connect(_on_mouse_entered)
	mouse_exited.connect(_on_mouse_exited)
	resized.connect(_on_resized)
	queue_redraw()

func clear_slot() -> void:
	if text_label:
		text_label.text = _to_vertical(placeholder)

# 竖排：每字一行，自上而下
func _to_vertical(s: String) -> String:
	if s.is_empty():
		return ""
	var lines: PackedStringArray = []
	for i in range(s.length()):
		lines.append(s[i])
	return "\n".join(lines)

func _on_resized() -> void:
	queue_redraw()

func _draw() -> void:
	var r := Rect2(Vector2.ZERO, size)
	var top_left := r.position
	var top_right := r.position + Vector2(r.size.x, 0)
	var bottom_left := r.position + Vector2(0, r.size.y)
	var bottom_right := r.position + Vector2(r.size.x, r.size.y)

	_draw_dashed_line(top_left, top_right)
	_draw_dashed_line(top_right, bottom_right)
	_draw_dashed_line(bottom_right, bottom_left)
	_draw_dashed_line(bottom_left, top_left)

func _draw_dashed_line(from: Vector2, to: Vector2) -> void:
	var dir: Vector2 = to - from
	var length: float = dir.length()
	if length <= 0.0:
		return
	var normal: Vector2 = dir / length
	var pos: float = 0.0
	while pos < length:
		var start_point: Vector2 = from + normal * pos
		var end_pos: float = min(pos + _dash_length, length)
		var end_point: Vector2 = from + normal * end_pos
		draw_line(start_point, end_point, _border_color, _border_width)
		pos += _dash_length + _gap_length

func _can_drop_data(_at_position: Vector2, data) -> bool:
	if typeof(data) != TYPE_DICTIONARY:
		return false
	if data.get("type", "") != "word":
		return false
	var cat := str(data.get("category", ""))
	if cat != expected_category:
		return false
	if expected_category == "body":
		# 正文需要匹配具体哪个 slot
		return str(data.get("body_slot", "")) == body_slot
	return true

func _drop_data(_at_position: Vector2, data) -> void:
	if not _can_drop_data(_at_position, data):
		return
	var word := str(data.get("word", ""))
	if text_label:
		text_label.text = _to_vertical(word)
	# 放下后给予轻微“选中”反馈
	modulate = Color(0.95, 1.0, 0.95)
	word_dropped.emit(slot_key, word)

func _on_mouse_entered() -> void:
	# 鼠标悬停时略微提亮，模拟纸张被触碰
	if modulate == _base_modulate:
		modulate = Color(1.02, 1.02, 1.0)

func _on_mouse_exited() -> void:
	# 离开时，如果不是“选中高亮”（绿色调），恢复基础颜色
	if modulate.r > 1.0 or modulate.g > 1.0:
		modulate = _base_modulate
