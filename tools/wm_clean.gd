# 去掉底图右下角水印：裁掉含水印的底带后等比缩放回原尺寸
#
# 为什么这样做（而不是修补或直接裁掉）：
#   - 直接裁掉会**改变图片尺寸** → TextureRect 等比缩放比变了 → 槽位锚点全部失效。
#   - 局部修补会在水印处留糊斑：实测水印压在装饰纹理/人物鞋子上，周边各行横向离散度 σ≈40，
#     不是均匀纹理，没有可复制的水印下内容。
#   - 裁剪 + 缩放回原尺寸：**水印 100% 移除、零修补**，输出尺寸与缩放比都不变，
#     槽位矩形高度不变，只需把纵向锚点按 新 = (旧 - s)/(1 - s) 重算（s = 裁剪比例）。
#
# 代价（必须知道）：画面上移、顶部内容略微放大（本例约 10%）。
#
# 用法：
#   godot --path <项目> --script res://tools/wm_clean.gd -- \
#       --image res://assets/images/backgrounds/main.png --crop-through 1380 --out <输出.png> \
#       [--anchor 0.117,0.882] [--keep-size]
extends SceneTree

func _initialize() -> void:
	var image_path := ""
	var out_path := ""
	var crop_through := 0
	var keep_size := false
	var anchors: Array = []
	var args := OS.get_cmdline_user_args()
	for i in range(args.size()):
		match args[i]:
			"--image":
				if i + 1 < args.size(): image_path = args[i + 1]
			"--out":
				if i + 1 < args.size(): out_path = args[i + 1]
			"--crop-through":
				if i + 1 < args.size(): crop_through = int(args[i + 1])
			"--keep-size":
				keep_size = true
			"--anchor":
				if i + 1 < args.size():
					for part in args[i + 1].split(","):
						anchors.append(float(part))

	if image_path.is_empty() or out_path.is_empty() or crop_through <= 0:
		push_error("用法: --image <res://…png> --crop-through <Y> --out <绝对路径.png> [--anchor a,b] [--keep-size]")
		quit(2)
		return

	var img := Image.load_from_file(ProjectSettings.globalize_path(image_path))
	if img == null:
		push_error("加载失败: " + image_path)
		quit(1)
		return
	var W := img.get_width()
	var H := img.get_height()
	print("输入 %s  %d×%d  格式=%d" % [image_path.get_file(), W, H, img.get_format()])

	var y0 := clampi(crop_through, 1, H - 1)
	# 只保留 [0, y0)
	img = img.get_region(Rect2i(0, 0, W, y0))
	print("裁掉 y≥%d → %d×%d  （去掉 %.2f%% 高度）" % [y0, img.get_width(), img.get_height(), (1.0 - float(y0) / H) * 100.0])

	if not keep_size:
		# 缩放回原尺寸：宽高比与窗口尺寸都不变 ⇒ 槽位矩形高度不变
		# 注意 class_image.rst:1695 —— resize() 返回 void（不是 Error），别去判返回值
		img.resize(W, H, Image.INTERPOLATE_LANCZOS)
		print("缩放回 %d×%d（LANCZOS）" % [W, H])

	var abs_out := out_path
	if abs_out.begins_with("res://") or abs_out.begins_with("user://"):
		abs_out = ProjectSettings.globalize_path(abs_out)
	var serr := img.save_png(abs_out)
	if serr != OK:
		push_error("保存失败 err=%d → %s" % [serr, abs_out])
		quit(1)
		return
	print("写出 %s  %d×%d" % [abs_out, img.get_width(), img.get_height()])

	if not keep_size:
		var s := float(y0) / H
		print("")
		print("【纵向锚点重算】裁剪比例 s = %d/%d = %.6f" % [y0, H, s])
		print("  公式: 新anchor = (旧anchor - s) / (1 - s) = (旧anchor - %.6f) / %.6f" % [s, 1.0 - s])
		for a in anchors:
			print("  旧 %.6f  →  新 %.6f" % [a, (a - s) / (1.0 - s)])
		print("  横向锚点不变；槽位像素高度不变。")
	quit(0)
