extends Node
## 启动时给主题的默认字体挂上系统字体兜底链。
##
## 为什么需要这一步（2026-10-11 实测）：
## `Font.fallbacks` **不会**被序列化进 .tres —— 无论赋在 FontFile 上还是包一层 FontVariation，
## 存盘再 load 回来 fallbacks 数量都是 0（build_theme.gd 的回读校验会报"兜底链没保存下来"）。
## 所以兜底只能在运行时挂。
##
## 必要性：项目当前用字 594 个，`hanchanlongcang.otf` 实测 0 缺字（tools/probe_font.gd）。
## 但它的 CJK 覆盖率只有 32.4%，**日后新增文案一旦超出字库就会渲染成方块**
## （实测：项目外用字在该字体下显示为密集方块，Godot 不会自动回退系统字体）。
## 这个自启动就是那道保险。

const FALLBACK_FONTS := ["Microsoft YaHei", "SimSun", "Noto Sans CJK SC", "sans-serif"]

func _ready() -> void:
	var theme := ThemeDB.get_project_theme()
	if theme == null:
		push_warning("ProjectSettings 未设置 gui/theme/custom，跳过字体兜底")
		return
	var base := theme.default_font
	if base == null:
		push_warning("全局主题没有 default_font，跳过字体兜底")
		return

	var sys := SystemFont.new()
	sys.font_names = PackedStringArray(FALLBACK_FONTS)
	sys.allow_system_fallback = true

	if base is FontVariation:
		(base as FontVariation).fallbacks = [sys]
	else:
		# FontFile 不能承载 fallbacks（会被序列化丢弃），包一层 FontVariation
		var v := FontVariation.new()
		v.base_font = base
		v.fallbacks = [sys]
		theme.default_font = v

	print("[FontFallback] 已挂兜底: ", FALLBACK_FONTS, "  实际 fallbacks=", theme.default_font.fallbacks.size())
