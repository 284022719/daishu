# 校验 NPC 头像：5 种关系 → 字与色互不相同；缺字段时不崩
extends SceneTree

const NPCAvatar := preload("res://scripts/npc_avatar.gd")

func _initialize() -> void:
	DisplayServer.window_set_size(Vector2i(1152, 648))
	get_root().size = Vector2i(1152, 648)
	var ok := true

	print("=== 关系 → 头像映射 ===")
	var seen_glyph := {}
	var seen_color := {}
	for rel in ["父母", "子女", "夫妻", "兄弟", "朋友"]:
		var av: Control = NPCAvatar.new()
		get_root().add_child(av)
		av.setup({"relation": rel})
		await process_frame
		var g: String = av.get_glyph()
		var c: Color = av.get_color()
		print("  %-4s → 字 '%s'  色 %s" % [rel, g, c.to_html(false)])
		if seen_glyph.has(g):
			print("     [!] 字与 ", seen_glyph[g], " 重复")
			ok = false
		if seen_color.has(c):
			print("     [!] 颜色与 ", seen_color[c], " 重复")
			ok = false
		seen_glyph[g] = rel
		seen_color[c] = rel
		av.queue_free()

	print("=== 缺字段/异常输入不应崩 ===")
	for probe in [{}, {"relation": ""}, {"relation": "不存在的身份"}, {"name": "张三"}]:
		var av: Control = NPCAvatar.new()
		get_root().add_child(av)
		av.setup(probe)
		await process_frame
		var g: String = av.get_glyph()
		var sz := av.get_combined_minimum_size()
		print("  %-28s → 字 '%s'  最小尺寸 (%.0f,%.0f)" % [str(probe), g, sz.x, sz.y])
		if g.is_empty():
			print("     [!] 字为空")
			ok = false
		if sz.x <= 0.0 or sz.y <= 0.0:
			print("     [!] 最小尺寸为 0，布局会塌")
			ok = false
		av.queue_free()

	print("=== 顺带核对设计论据（这条曾被我写错，留在这里防止再错）===")
	# 正确说法：头像取「关系」的理由是「关系是玩法信息 + 字色集合小且受控」，
	# 而**不是**「关系比姓氏更不容易重复」—— 下面这组数字就是反例。
	var surname_collide := 0.0
	var total := 0.0
	for a in range(7):
		for b in range(7):
			for c in range(7):
				total += 1.0
				if a == b or a == c or b == c:
					surname_collide += 1.0
	print("  7 个姓氏取 3 个（可重复）撞姓概率 = %.1f%%" % (100.0 * surname_collide / total))
	print("  5 个关系取 3 个（可重复）撞关系概率 = %.1f%%" % (100.0 * (1.0 - (5.0 * 4.0 * 3.0) / 125.0)))
	print("  49 种姓名取 3 个（可重复）撞名概率 = %.1f%%" % (100.0 * (1.0 - (49.0 * 48.0 * 47.0) / (49.0 * 49.0 * 49.0))))
	print("  → 结论：头像负责「关系类别」，唯一标识交给姓名（姓名本来就印在按钮上）")

	print("=== 结论: ", "PASS" if ok else "FAIL", " ===")
	quit(0 if ok else 1)
