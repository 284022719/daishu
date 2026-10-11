# 量出真实几何：贴图在屏幕上被画到哪、Background 控件的 rect 多大、槽位实际矩形
# 目的：搞清楚场景锚点(0..1)到底相对**哪个矩形**解析，别再靠推断
extends SceneTree

func _initialize() -> void:
	get_root().size = Vector2i(1152, 648)
	get_root().content_scale_size = Vector2i(1152, 648)
	var packed: PackedScene = load("res://scenes/letter.tscn")
	var letter: Node = packed.instantiate()
	get_root().add_child(letter)
	for i in range(6):
		await process_frame

	var bg: TextureRect = letter.get_node("Background")
	var paper: Control = letter.get_node("PaperArea")
	print("=== 视口 ===")
	print("  root.size = ", get_root().size, "  visible_rect = ", get_root().get_visible_rect())

	print("=== Background (TextureRect) ===")
	print("  position = ", bg.position)
	print("  size     = ", bg.size)
	print("  global_position = ", bg.global_position)
	if bg.texture != null:
		print("  texture size = ", bg.texture.get_size())
	print("  expand_mode = ", bg.expand_mode, "  stretch_mode = ", bg.stretch_mode)
	print("  → 贴图按 keep-aspect-centered 实际绘制区（推算）:")
	var tw := float(bg.texture.get_size().x)
	var th := float(bg.texture.get_size().y)
	var cw := bg.size.x
	var chh := bg.size.y
	var scale := minf(cw / tw, chh / th)
	var dw := tw * scale
	var dh := th * scale
	var dx := bg.position.x + (cw - dw) * 0.5
	var dy := bg.position.y + (chh - dh) * 0.5
	print("     绘制区 x %.1f..%.1f  (宽 %.1f)" % [dx, dx + dw, dw])
	print("     绘制区 y %.1f..%.1f  (高 %.1f)  缩放 %.4f" % [dy, dy + dh, dh, scale])

	print("=== PaperArea (Control，槽位的父节点) ===")
	print("  position = ", paper.position, "  size = ", paper.size)
	print("  global_position = ", paper.global_position)

	print("=== 各槽位实际矩形 ===")
	for n in ["SalutationSlot", "BodySlot1", "BodySlot2", "BodySlot3", "SignatureSlot"]:
		var s: Control = paper.get_node(n)
		print("  %-15s global_pos=(%.1f, %.1f)  size=(%.1f, %.1f)  [x %.1f..%.1f, y %.1f..%.1f]"
			% [n, s.global_position.x, s.global_position.y, s.size.x, s.size.y,
			   s.global_position.x, s.global_position.x + s.size.x,
			   s.global_position.y, s.global_position.y + s.size.y])
	quit(0)
