# 构建项目全局 Theme 并落盘为 .tres
# 为什么用代码生成而不是手写 .tres：Theme 里 stylebox 的序列化键名（`Type/styles/name`）
# 在本地文档语料里没有示例，手写有静默失效的风险；由引擎自己序列化则格式必然正确。
# 用法：godot --path <项目> --script res://tools/build_theme.gd
extends SceneTree

const OUT_PATH := "res://theme/daishu_theme.tres"
const FONT_PATH := "res://assets/fonts/hanchanlongcang.otf"
const BTN_TEX := "res://assets/images/ui/button_frame.png"

# 色板取自 docs/ART_PLAN.md §二（木构/家具 + 宣纸 + 墨），并复用已定稿的词库按钮配色
const PAPER := Color(0.976, 0.949, 0.878)
const PAPER_HOVER := Color(1.0, 0.976, 0.914)
const PAPER_PRESSED := Color(0.902, 0.851, 0.733)
const PAPER_DISABLED := Color(0.86, 0.84, 0.80, 0.7)
const INK := Color(0.235, 0.176, 0.098)
const INK_HOVER := Color(0.549, 0.322, 0.141)
const FONT_SIZE := 18

func _initialize() -> void:
	var theme := Theme.new()

	# ---- 默认字体：全局中文字体 ----
	# 判据来自 tools/probe_font.gd：项目实际用字 594 个，该字体 0 缺字。
	# 另挂一个系统字体做兜底 —— 日后新增文案若超出字库，也不会变豆腐块。
	if not ResourceLoader.exists(FONT_PATH):
		push_error("字体缺失: " + FONT_PATH)
		quit(1)
		return
	var font := load(FONT_PATH) as FontFile
	if font == null:
		push_error("字体加载失败（类型不是 FontFile）: " + FONT_PATH)
		quit(1)
		return
	# 用 FontVariation 包一层来挂兜底链。
	# 为什么不直接给 FontFile 设 fallbacks：实测（2026-10-11）`Font.fallbacks` 是对象属性，
	# 赋在 FontFile 上**不会写进 .tres**，重新 load 后 fallbacks 数量为 0，兜底静默失效。
	# 包成 FontVariation 后它作为独立子资源被序列化，兜底链得以保存。
	var sys := SystemFont.new()
	sys.font_names = PackedStringArray(["Microsoft YaHei", "SimSun", "Noto Sans CJK SC", "sans-serif"])
	sys.allow_system_fallback = true
	var vfont := FontVariation.new()
	vfont.base_font = font
	vfont.fallbacks = [sys]
	theme.default_font = vfont
	theme.default_font_size = FONT_SIZE
	print("默认字体: ", font.font_name, "  兜底: ", sys.font_names, "  字号: ", FONT_SIZE)

	# ---- 按钮九宫格 ----
	# 注意区分"文件不在"和"文件在但没导入"：`ResourceLoader.exists()` 对**未导入**的资源也返回 false，
	# 实测刚复制进来、`--import` 还没跑完时报的就是这个 —— 别把它当成文件丢失。
	# 见 AI_PLAYBOOK 第 15 条。
	if not ResourceLoader.exists(BTN_TEX):
		var abs_hint := ProjectSettings.globalize_path(BTN_TEX)
		if FileAccess.file_exists(BTN_TEX):
			push_error("按钮贴图存在但**尚未导入**（.import/.ctex 未生成）：%s\n先跑：godot --headless --path . --import" % BTN_TEX)
		else:
			push_error("按钮贴图文件不存在：%s（解析为 %s）" % [BTN_TEX, abs_hint])
		quit(1)
		return
	var tex := load(BTN_TEX) as Texture2D
	print("按钮贴图: ", tex.get_size())

	var margin := 12.0  # 与生图脚本里的九宫格边距一致
	for spec in [
		{"name": "normal",   "modulate": Color(1, 1, 1, 1)},
		{"name": "hover",    "modulate": Color(1.06, 1.04, 0.98, 1)},
		{"name": "pressed",  "modulate": Color(0.90, 0.86, 0.78, 1)},
		{"name": "disabled", "modulate": Color(0.80, 0.80, 0.80, 0.7)},
	]:
		var sb := StyleBoxTexture.new()
		sb.texture = tex
		sb.set_texture_margin_all(margin)
		# 内容边距比贴图边距小：按钮高度按"字号 + 上下各 4px"走，
		# 否则词库 3 组共 15 个按钮会撑出左侧面板（实测 8px 时底部被裁）
		sb.content_margin_left = 10.0
		sb.content_margin_right = 10.0
		sb.content_margin_top = 4.0
		sb.content_margin_bottom = 4.0
		sb.modulate_color = spec["modulate"]
		theme.set_stylebox(StringName(spec["name"]), "Button", sb)
	# focus 用 hover 的样子，避免额外的虚线框
	theme.set_stylebox("focus", "Button", theme.get_stylebox("hover", "Button"))

	# ---- 按钮文字色 ----
	theme.set_color("font_color", "Button", INK)
	theme.set_color("font_hover_color", "Button", INK_HOVER)
	theme.set_color("font_pressed_color", "Button", INK)
	theme.set_color("font_focus_color", "Button", INK)
	theme.set_color("font_disabled_color", "Button", Color(0.5, 0.48, 0.45, 0.7))

	# ---- Label 文字色（默认墨褐，取代原先的默认白字）----
	theme.set_color("font_color", "Label", INK)

	# ---- Panel 默认底色（具体场景仍可用 theme_override 覆盖）----
	var panel := StyleBoxFlat.new()
	panel.bg_color = Color(0.965, 0.933, 0.867, 0.92)
	panel.border_color = Color(0.549, 0.322, 0.141, 0.5)
	panel.set_border_width_all(2)
	panel.set_corner_radius_all(8)
	panel.set_content_margin_all(10)
	theme.set_stylebox("panel", "Panel", panel)

	# ---- 落盘 ----
	var dir := DirAccess.open("res://")
	if dir != null and not dir.dir_exists("theme"):
		dir.make_dir("theme")
	var err := ResourceSaver.save(theme, OUT_PATH)
	if err != OK:
		push_error("保存失败 err=%d" % err)
		quit(1)
		return
	print("已保存: ", OUT_PATH)

	# ---- 回读校验 ----
	# ⚠️ 不能用 load(OUT_PATH) 回读：同一进程内资源管理器会命中**写入前的缓存**，
	# 实测刚存完立刻 load 拿到的仍是旧值（default_font_size 读成上一版）。
	# 所以这里读**文件文本**为准；语义层面的校验交给独立进程的 tools/verify_theme.gd。
	var text := FileAccess.get_file_as_string(OUT_PATH)
	if text.is_empty():
		push_error("回读失败：文件为空")
		quit(1)
		return
	var ok := true
	var checks := {
		"default_font_size = %d" % FONT_SIZE: "字体字号",
		"Button/styles/normal = ": "按钮九宫格 normal",
		"Button/styles/hover = ": "按钮九宫格 hover",
		"Button/styles/pressed = ": "按钮九宫格 pressed",
		"Button/colors/font_color = ": "按钮字色",
		"Label/colors/font_color = ": "Label 字色",
		"Panel/styles/panel = ": "Panel 底纹",
		"default_font = ": "默认字体",
	}
	for needle in checks.keys():
		var hit := text.contains(needle)
		print("  %-22s %s" % [checks[needle], "✓" if hit else "✗ 缺失(" + needle + ")"] )
		if not hit:
			ok = false
	print("文件回读校验: ", "通过" if ok else "失败")
	print("（注意：fallbacks 不会进 .tres —— 由 scripts/FontFallback.gd 在运行时挂，见该文件注释）")
	quit(0 if ok else 1)
