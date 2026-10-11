# 量主界面布局：面板/行/头像/按钮的实际矩形，定位"内容撑破面板"的具体数字
extends SceneTree

func _initialize() -> void:
	DisplayServer.window_set_size(Vector2i(1152, 648))
	get_root().size = Vector2i(1152, 648)
	var packed: PackedScene = load("res://scenes/main.tscn")
	var scene: Node = packed.instantiate()
	get_root().add_child(scene)
	for i in range(4):
		await process_frame

	var btn: Button = scene.get_node("MainPanel/VBoxContainer/ButtonBar/StartDayBtn")
	btn.emit_signal("pressed")
	for i in range(6):
		await process_frame

	var panel: Control = scene.get_node("MainPanel")
	var vbox: Control = scene.get_node("MainPanel/VBoxContainer")
	var list: Control = scene.get_node("MainPanel/VBoxContainer/NPCList")
	print("=== 视口 1152x648 ===")
	print("  MainPanel  pos=(%.1f,%.1f) size=(%.1f,%.1f)  min=(%.1f,%.1f)"
		% [panel.position.x, panel.position.y, panel.size.x, panel.size.y,
		   panel.get_combined_minimum_size().x, panel.get_combined_minimum_size().y])
	print("  VBox       pos=(%.1f,%.1f) size=(%.1f,%.1f)  min=(%.1f,%.1f)"
		% [vbox.position.x, vbox.position.y, vbox.size.x, vbox.size.y,
		   vbox.get_combined_minimum_size().x, vbox.get_combined_minimum_size().y])
	print("  NPCList    子节点=%d  size=(%.1f,%.1f)  min=(%.1f,%.1f)"
		% [list.get_child_count(), list.size.x, list.size.y,
		   list.get_combined_minimum_size().x, list.get_combined_minimum_size().y])

	print("=== 逐行 ===")
	for i in range(list.get_child_count()):
		var row: Control = list.get_child(i)
		print("  行%d  pos=(%.1f,%.1f) size=(%.1f,%.1f)  min=(%.1f,%.1f)"
			% [i, row.global_position.x, row.global_position.y, row.size.x, row.size.y,
			   row.get_combined_minimum_size().x, row.get_combined_minimum_size().y])
		for c in row.get_children():
			var cc := c as Control
			print("     └ %-16s pos=(%.1f,%.1f) size=(%.1f,%.1f) min=(%.1f,%.1f)"
				% [cc.get_class(), cc.global_position.x, cc.global_position.y, cc.size.x, cc.size.y,
				   cc.get_combined_minimum_size().x, cc.get_combined_minimum_size().y])
			for g in cc.get_children():
				var gg := g as Control
				print("         └ %-14s pos=(%.1f,%.1f) size=(%.1f,%.1f)"
					% [gg.get_class(), gg.global_position.x, gg.global_position.y, gg.size.x, gg.size.y])
	quit(0)
