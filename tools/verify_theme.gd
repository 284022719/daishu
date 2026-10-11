# 全局 Theme 生效验证：三查 —— ① 设置项指向 ② 资源加载 ③ 控件实际取到的样式
# 判据：控件"实际取到"的样式才是真的；只看 project.godot 写了什么不算数。
# 用法：godot --path <项目> --script res://tools/verify_theme.gd
extends SceneTree

const THEME_PATH := "res://theme/daishu_theme.tres"

# 主题字体可能是 FontFile 或（挂了兜底后）FontVariation —— 后者没有 font_name，
# 要取 base_font.font_name（实测：直接读 .font_name 会报 Invalid access）
func _font_label(f: Font) -> String:
	if f == null:
		return "null"
	if f is FontVariation:
		var v := f as FontVariation
		return "%s(+fallbacks=%d)" % [_font_label(v.base_font), v.fallbacks.size()]
	if f is FontFile:
		return (f as FontFile).font_name
	return f.get_class()

func _initialize() -> void:
	var ok := true

	# ① 项目设置
	var setting := str(ProjectSettings.get_setting("gui/theme/custom", ""))
	print("① gui/theme/custom = '", setting, "'")
	if setting != THEME_PATH:
		print("   [!] 设置项与预期不符")
		ok = false

	# ② 资源能加载
	if not ResourceLoader.exists(THEME_PATH):
		push_error("主题资源不存在")
		quit(1)
		return
	var th := load(THEME_PATH) as Theme
	print("② 加载成功：", th.get_class(), "  default_font=", _font_label(th.default_font),
		"  size=", th.default_font_size)

	# ③ 造一个真实控件，看它实际取到什么（这是最终判据）
	get_root().size = Vector2i(1152, 648)
	var btn := Button.new()
	btn.text = "开始今日"
	var panel := Panel.new()
	var label := Label.new()
	label.text = "铜钱: 100文"
	var holder := Control.new()
	holder.set_anchors_preset(Control.PRESET_FULL_RECT)
	holder.add_child(btn)
	holder.add_child(panel)
	holder.add_child(label)
	get_root().add_child(holder)
	await process_frame
	await process_frame

	print("③ 控件实际取到的主题值：")
	var font := btn.get_theme_font("font")
	print("   Button.font      = ", _font_label(font))
	if not _font_label(font).begins_with("ChillLongCangKaiShu Bold"):
		print("   [!] 按钮没拿到书法字体")
		ok = false

	for state in ["normal", "hover", "pressed", "disabled", "focus"]:
		var sb := btn.get_theme_stylebox(state)
		var t := sb.get_class() if sb else "null"
		var is_tex := sb is StyleBoxTexture
		print("   Button/styl_%-8s = %s%s" % [state, t, "" if is_tex else "   ← 不是九宫格!"])
		if not is_tex:
			ok = false

	var fc := btn.get_theme_color("font_color")
	print("   Button.font_color = ", fc)
	if fc != Color(0.235, 0.176, 0.098):
		print("   [!] 按钮字色不符")
		ok = false

	var panel_sb := panel.get_theme_stylebox("panel")
	print("   Panel.panel       = ", (panel_sb.get_class() if panel_sb else "null"))

	var lf := label.get_theme_font("font")
	print("   Label.font        = ", _font_label(lf))
	if not _font_label(lf).begins_with("ChillLongCangKaiShu Bold"):
		print("   [!] Label 没拿到全局字体")
		ok = false

	print("=== 结论: ", "PASS" if ok else "FAIL", " ===")
	quit(0 if ok else 1)
