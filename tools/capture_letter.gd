# 截图工具：headless 加载 letter.tscn，注入一个 NPC，输出 PNG
# 用法：
#   godot --headless --path <项目> --script res://tools/capture_letter.gd -- --out <绝对路径.png>
extends SceneTree

func _initialize() -> void:
	var out_path := ""
	var args := OS.get_cmdline_user_args()
	for i in range(args.size()):
		if args[i] == "--out" and i + 1 < args.size():
			out_path = args[i + 1]
	if out_path.is_empty():
		push_error("缺少 --out 参数")
		quit(1)
		return

	# 根窗口尺寸（信纸场景按 1152x648 设计）
	get_root().size = Vector2i(1152, 648)

	var packed: PackedScene = load("res://scenes/letter.tscn")
	if packed == null:
		push_error("无法加载 res://scenes/letter.tscn")
		quit(1)
		return
	var letter: Node = packed.instantiate()
	get_root().add_child(letter)

	# 等布局稳定
	await process_frame
	await process_frame

	# 用 NPCManager 生成第 1 天的委托人并注入
	var npc_manager: Node = get_root().get_node_or_null("NPCManager")
	var npc_id: int = 0
	if npc_manager != null:
		var npcs: Array = npc_manager.get_today_npcs(1)
		if npcs.size() > 0:
			npc_id = int(npcs[0].get("npc_id", 0))
			print("[capture] 注入 NPC id=", npc_id, " name=", npcs[0].get("name", "?"))
		else:
			print("[capture] 警告：get_today_npcs(1) 返回空")
	else:
		print("[capture] 警告：找不到 /root/NPCManager")

	if npc_id != 0 and letter.has_method("init_with_npc"):
		letter.init_with_npc(npc_id)
	else:
		print("[capture] 未注入 NPC，将截取未初始化状态")

	# 让异步填充分配完成
	for i in range(6):
		await process_frame

	var img: Image = get_root().get_texture().get_image()
	if img == null:
		push_error("取不到视口图像")
		quit(1)
		return
	var err := img.save_png(out_path)
	if err != OK:
		push_error("保存失败 err=%d path=%s" % [err, out_path])
		quit(1)
		return
	print("[capture] 已保存 ", out_path, "  尺寸=", img.get_width(), "x", img.get_height())
	quit(0)
