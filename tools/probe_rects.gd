extends SceneTree
## 探针：打印指定场景里关键节点的**实际矩形**，用于判断布局是否真的生效。
## 用法：godot --path . --script res://tools/probe_rects.gd -- --scene prologue

func _initialize() -> void:
	var scene_key := "prologue"
	var args := OS.get_cmdline_user_args()
	for i in range(args.size()):
		if args[i] == "--scene" and i + 1 < args.size():
			scene_key = args[i + 1]

	var paths := {
		"prologue": "res://scenes/prologue.tscn",
		"success": "res://scenes/success.tscn",
		"gameover": "res://scenes/gameover.tscn",
	}
	if not paths.has(scene_key):
		print("[probe] 未知场景: ", scene_key)
		quit(1)
		return

	var packed: PackedScene = load(paths[scene_key])
	if packed == null:
		print("[probe] 加载失败: ", paths[scene_key])
		quit(1)
		return

	var root_node: Node = packed.instantiate()
	# ⚠️ SceneTree 默认视口是 100x100，Control 的锚点/容器布局会算成 0 —— 必须先设成项目视口，
	# 否则探针打印的全是 size=(0,0)，看着像"布局没生效"，其实是观察方式的问题。
	get_root().size = Vector2i(1152, 648)
	get_root().add_child(root_node)

	print("[probe] 场景=", scene_key, "  视口=", get_root().size)

	# 递归打印每个 Control 的全局矩形
	_dump(root_node, 0)

	quit(0)

func _dump(node: Node, depth: int) -> void:
	if node is Control:
		var c := node as Control
		var gr := c.get_global_rect()
		print("%s%s  pos=(%.0f,%.0f)  size=(%.0f,%.0f)  sfv=%d  anchor=%.2f..%.2f/%.2f..%.2f" % [
			"  ".repeat(depth), c.name,
			gr.position.x, gr.position.y, gr.size.x, gr.size.y,
			c.size_flags_vertical,
			c.anchor_left, c.anchor_right, c.anchor_top, c.anchor_bottom,
		])
	for child in node.get_children():
		_dump(child, depth + 1)
