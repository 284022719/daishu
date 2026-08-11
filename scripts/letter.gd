extends Control

# 左侧词库
@onready var request_label: Label = $HSplit/LetterPanel/LetterVBox/RequestLabel
@onready var salutation_container: VBoxContainer = $HSplit/WordPanel/WordVBox/SalutationContainer
@onready var body_container: VBoxContainer = $HSplit/WordPanel/WordVBox/BodyContainer
@onready var signature_container: VBoxContainer = $HSplit/WordPanel/WordVBox/SignatureContainer

# 右侧信纸槽位
@onready var salutation_slot = $HSplit/LetterPanel/LetterVBox/Slots/SalutationSlot
@onready var body_slot1 = $HSplit/LetterPanel/LetterVBox/Slots/BodySlot1
@onready var body_slot2 = $HSplit/LetterPanel/LetterVBox/Slots/BodySlot2
@onready var body_slot3 = $HSplit/LetterPanel/LetterVBox/Slots/BodySlot3
@onready var signature_slot = $HSplit/LetterPanel/LetterVBox/Slots/SignatureSlot

# 底部按钮与结算弹窗
@onready var submit_btn: Button = $ButtonBar/SubmitBtn
@onready var reset_btn: Button = $ButtonBar/ResetBtn
@onready var back_btn: Button = $ButtonBar/BackBtn
@onready var result_popup: AcceptDialog = $ResultPopup
@onready var result_label: RichTextLabel = $ResultPopup/ResultLabel

const WORD_BUTTON_SCRIPT := preload("res://scripts/word_button.gd")
# 信纸毛笔字体（从 assets/fonts/hanchanlongcang.otf 加载）
const LETTER_FONT_PATH := "res://assets/fonts/hanchanlongcang.otf"
const LETTER_FONT_SIZE := 22
const LETTER_FONT_COLOR := Color.BLACK

# 当前NPC数据
var current_npc: Dictionary = {}
var current_npc_id: int = 0
var _npc_initialized := false
var _pending_result: Dictionary = {}

# 当前填写的答案（与判定系统兼容）
var player_answers := {
	"salutation": "",
	"body_slot1": "",
	"body_slot2": "",
	"body_slot3": "",
	"signature": ""
}

func _ready() -> void:
	submit_btn.pressed.connect(_on_submit_pressed)
	reset_btn.pressed.connect(_on_reset_pressed)
	back_btn.pressed.connect(_on_back_pressed)
	result_popup.confirmed.connect(_on_result_popup_confirmed)
	result_popup.get_ok_button().text = "确认"

	# 槽位接收拖拽后，更新 player_answers
	for slot in [salutation_slot, body_slot1, body_slot2, body_slot3, signature_slot]:
		slot.word_dropped.connect(_on_slot_word_dropped)

	# 信纸区域使用毛笔字体（若存在 maobi.ttf）
	_apply_letter_font()
	# 口述文本用系统小字，便于横向阅读
	request_label.remove_theme_font_override("font")
	request_label.remove_theme_font_size_override("font_size")
	request_label.remove_theme_color_override("font_color")
	request_label.remove_theme_constant_override("outline_size")
	request_label.remove_theme_color_override("font_outline_color")
	request_label.add_theme_font_size_override("font_size", 14)

# 为右侧信纸区域所有 Label 应用毛笔字体与墨色
func _apply_letter_font() -> void:
	if not ResourceLoader.exists(LETTER_FONT_PATH):
		return
	var font: Font = load(LETTER_FONT_PATH) as Font
	if font == null:
		return
	var letter_vbox: VBoxContainer = $HSplit/LetterPanel/LetterVBox
	_apply_font_to_labels(letter_vbox, font)

func _apply_font_to_labels(control: Control, font: Font) -> void:
	if control is Label:
		control.add_theme_font_override("font", font)
		control.add_theme_font_size_override("font_size", LETTER_FONT_SIZE)
		control.add_theme_color_override("font_color", LETTER_FONT_COLOR)
		# 轻微描边模拟墨迹
		control.add_theme_constant_override("outline_size", 1)
		control.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.4))
	for child in control.get_children():
		if child is Control:
			_apply_font_to_labels(child, font)

# 竖排：每字一行，自上而下（中国古代书写习惯）
func _to_vertical(s: String) -> String:
	if s.is_empty():
		return ""
	var lines: PackedStringArray = []
	for i in range(s.length()):
		lines.append(s[i])
	return "\n".join(lines)

# 初始化界面，由主界面调用
func init_with_npc(npc_id: int) -> void:
	_npc_initialized = false
	current_npc_id = int(npc_id)
	var npc_manager = get_node("/root/NPCManager")
	current_npc = npc_manager.get_npc_by_id(current_npc_id)

	if current_npc.is_empty():
		print("错误：找不到NPC ID ", npc_id, "，current_day_npcs 数量: ", npc_manager.current_day_npcs.size())
		return

	request_label.text = str(current_npc.get("request_text", ""))

	_build_word_pools()
	reset_answers()
	_npc_initialized = true

func _build_word_pools() -> void:
	# 清空旧的词库按钮
	for c in [salutation_container, body_container, signature_container]:
		for child in c.get_children():
			child.queue_free()

	var word_pool: Dictionary = current_npc.get("word_pool", {})

	# 称谓词库
	for text in word_pool.get("salutation", []):
		_add_word_button(salutation_container, str(text), "salutation", "")

	# 正文词库（body_slots.slot1/2/3），每行加标签对应右侧槽位
	var body_slots: Dictionary = word_pool.get("body_slots", {})
	var slot_labels := {"slot1": "家中", "slot2": "在外", "slot3": "盼"}
	for slot_name in ["slot1", "slot2", "slot3"]:
		var label := Label.new()
		label.text = "· " + slot_labels.get(slot_name, slot_name)
		label.add_theme_font_size_override("font_size", 12)
		label.add_theme_color_override("font_color", Color(0.4, 0.4, 0.4))
		body_container.add_child(label)
		var row := HBoxContainer.new()
		body_container.add_child(row)
		for text in body_slots.get(slot_name, []):
			_add_word_button(row, str(text), "body", slot_name)

	# 落款词库
	for text in word_pool.get("signature", []):
		_add_word_button(signature_container, str(text), "signature", "")

func _add_word_button(parent: Node, text: String, category: String, body_slot: String) -> void:
	var btn := Button.new()
	btn.set_script(WORD_BUTTON_SCRIPT)
	btn.text = text
	btn.category = category
	btn.body_slot = body_slot
	parent.add_child(btn)

func _on_slot_word_dropped(slot_key: String, word: String) -> void:
	match slot_key:
		"salutation":
			player_answers["salutation"] = word
		"body_slot1":
			player_answers["body_slot1"] = word
		"body_slot2":
			player_answers["body_slot2"] = word
		"body_slot3":
			player_answers["body_slot3"] = word
		"signature":
			player_answers["signature"] = word

# 提交按钮：弹出结算结果，确认后再结算并返回
func _on_submit_pressed() -> void:
	if not _npc_initialized or current_npc.is_empty():
		return
	var result: Dictionary = JudgeSystem.judge(current_npc, player_answers)
	_pending_result = result
	var fee := int(result.get("fee", 0))
	var feedback_text := str(result.get("feedback_text", ""))
	var line1 := ""
	if fee < 0:
		line1 = "扣钱：%d 文" % abs(fee)
	else:
		line1 = "获得：%d 文" % fee
	var correct_answers: Dictionary = result.get("correct_answers", {})
	var item_correct: Dictionary = result.get("item_correct", {})
	var answer_block := _build_answer_highlight(correct_answers, item_correct)
	result_label.text = line1 + "\n\n" + feedback_text + answer_block
	result_popup.popup_centered()

# 生成带高亮的“正确答案”区块（BBCode：绿色=正确，错项旁显示玩家所填）
func _build_answer_highlight(correct_answers: Dictionary, item_correct: Dictionary) -> String:
	if correct_answers.is_empty():
		return ""
	var c := correct_answers
	var ok := item_correct
	var slot1 := str(c.get("body_slot1", ""))
	var slot2 := str(c.get("body_slot2", ""))
	var slot3 := str(c.get("body_slot3", ""))
	var sal := str(c.get("salutation", ""))
	var sig := str(c.get("signature", ""))
	var lines: Array[String] = []
	lines.append("\n\n——— [color=#27ae60]正确答案[/color] ———")
	var sal_extra := " （你填：%s）" % player_answers.get("salutation", "") if not ok.get("salutation", true) else ""
	lines.append("称谓：[color=#27ae60]%s[/color]%s" % [sal, sal_extra])
	lines.append("正文：家中[color=#27ae60]%s[/color]%s，在外[color=#27ae60]%s[/color]%s，盼[color=#27ae60]%s[/color]%s。" % [
		slot1, " （你填：%s）" % player_answers.get("body_slot1", "") if not ok.get("body_slot1", true) else "",
		slot2, " （你填：%s）" % player_answers.get("body_slot2", "") if not ok.get("body_slot2", true) else "",
		slot3, " （你填：%s）" % player_answers.get("body_slot3", "") if not ok.get("body_slot3", true) else ""
	])
	var sig_extra := " （你填：%s）" % player_answers.get("signature", "") if not ok.get("signature", true) else ""
	lines.append("落款：[color=#27ae60]%s[/color]%s" % [sig, sig_extra])
	return "\n".join(lines)

func _on_result_popup_confirmed() -> void:
	var fee := int(_pending_result.get("fee", 0))
	var npc_name := str(current_npc.get("name", "未知NPC"))
	PlayerManager.record_entry("commission", fee, "%s 委托结算" % npc_name, {"npc_id": current_npc_id, "npc_name": npc_name})
	PlayerManager.add_money(fee)
	return_to_main()

# 重新填写按钮
func _on_reset_pressed() -> void:
	reset_answers()

func reset_answers() -> void:
	# 清空槽位显示
	salutation_slot.clear_slot()
	body_slot1.clear_slot()
	body_slot2.clear_slot()
	body_slot3.clear_slot()
	signature_slot.clear_slot()

	# 清空答案记录
	player_answers = {
		"salutation": "",
		"body_slot1": "",
		"body_slot2": "",
		"body_slot3": "",
		"signature": ""
	}

# 返回主界面（显示主界面并移除代写界面，保留主界面状态）
func _on_back_pressed() -> void:
	return_to_main()

func return_to_main() -> void:
	var main = get_tree().root.get_node_or_null("Main")
	if main:
		if main.has_method("on_npc_completed"):
			main.on_npc_completed(current_npc_id)
		main.show()
		if main.has_method("update_ui"):
			main.update_ui()
	queue_free()
