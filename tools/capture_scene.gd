# 通用场景截图：加载任意场景，可选点击某个按钮后截图
# 用法：
#   godot --path <项目> --script res://tools/capture_scene.gd -- --scene main --out <路径.png> [--click StartDayBtn]
extends SceneTree

const SCENES := {
	"main": "res://scenes/main.tscn",
	"title": "res://scenes/title_screen.tscn",
	"prologue": "res://scenes/prologue.tscn",
	"letter": "res://scenes/letter.tscn",
	"success": "res://scenes/success.tscn",
	"gameover": "res://scenes/gameover.tscn",
}

func _initialize() -> void:
	var scene_key := "main"
	var out_path := ""
	var click_name := ""
	var args := OS.get_cmdline_user_args()
	for i in range(args.size()):
		match args[i]:
			"--scene":
				if i + 1 < args.size():
					scene_key = args[i + 1]
			"--out":
				if i + 1 < args.size():
					out_path = args[i + 1]
			"--click":
				if i + 1 < args.size():
					click_name = args[i + 1]

	if out_path.is_empty():
		push_error("缺少 --out 参数")
		quit(1)
		return
	if not SCENES.has(scene_key):
		push_error("未知场景: " + scene_key)
		quit(1)
		return

	get_root().size = Vector2i(1152, 648)

	var packed: PackedScene = load(SCENES[scene_key])
	if packed == null:
		push_error("加载失败: " + SCENES[scene_key])
		quit(1)
		return
	var scene: Node = packed.instantiate()
	get_root().add_child(scene)
	for i in range(4):
		await process_frame

	# 可选：点一次按钮（用于触发列表填充等交互后再截图）
	if not click_name.is_empty():
		var btn := _find_node_by_name(scene, click_name)
		if btn == null:
			print("[capture] 找不到按钮: ", click_name)
		elif btn is Button:
			print("[capture] 点击按钮: ", click_name)
			btn.emit_signal("pressed")
			for i in range(6):
				await process_frame
		else:
			print("[capture] ", click_name, " 不是 Button")

	for i in range(3):
		await process_frame

	var img: Image = get_root().get_texture().get_image()
	if img == null:
		push_error("取不到视口图像")
		quit(1)
		return
	img.save_png(out_path)
	print("[capture] 已保存 ", out_path, "  ", img.get_width(), "x", img.get_height())
	quit(0)

func _find_node_by_name(root: Node, target: String) -> Node:
	if root.name == target:
		return root
	for child in root.get_children():
		var found := _find_node_by_name(child, target)
		if found != null:
			return found
	return null
