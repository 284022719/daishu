extends Control

# 节点引用
@onready var npc_avatar = $VBoxContainer/HBoxContainer/NPCAvatar
@onready var request_label = $VBoxContainer/HBoxContainer/RequestLabel
@onready var salutation_option = $VBoxContainer/LetterPaper/LetterContent/HBoxContainer/SalutationOption
@onready var body_slot1 = $VBoxContainer/LetterPaper/LetterContent/HBoxContainer2/BodyContainer/HBoxContainer/BodySlot1
@onready var body_slot2 = $VBoxContainer/LetterPaper/LetterContent/HBoxContainer2/BodyContainer/HBoxContainer2/BodySlot2
@onready var body_slot3 = $VBoxContainer/LetterPaper/LetterContent/HBoxContainer2/BodyContainer/HBoxContainer3/BodySlot3
@onready var signature_option = $VBoxContainer/LetterPaper/LetterContent/HBoxContainer3/SignatureOption
@onready var submit_btn = $VBoxContainer/HBoxContainer2/SubmitBtn
@onready var reset_btn = $VBoxContainer/HBoxContainer2/ResetBtn
@onready var back_btn = $VBoxContainer/BackBtn
@onready var word_pool_container = $VBoxContainer/WordPoolContainer
@onready var result_dialog: ConfirmationDialog = $ResultDialog
@onready var result_title_label: Label = $ResultDialog/DialogContent/ResultTitleLabel
@onready var fee_label: Label = $ResultDialog/DialogContent/FeeLabel
@onready var feedback_label: Label = $ResultDialog/DialogContent/FeedbackLabel

# 当前NPC数据
var current_npc = {}
var current_npc_id = 0
var pending_result: Dictionary = {}

# 当前填写的答案
var player_answers = {
	"salutation": "",
	"body_slot1": "",
	"body_slot2": "",
	"body_slot3": "",
	"signature": ""
}

func _ready():
	# 连接按钮信号
	submit_btn.pressed.connect(_on_submit_pressed)
	reset_btn.pressed.connect(_on_reset_pressed)
	back_btn.pressed.connect(_on_back_pressed)
	
	result_dialog.confirmed.connect(_on_result_confirmed)
	result_dialog.canceled.connect(_on_result_canceled)
	result_dialog.get_ok_button().text = "确认结算"
	result_dialog.get_cancel_button().text = "继续修改"
	
	# 连接下拉框选择信号
	salutation_option.item_selected.connect(_on_salutation_selected)
	signature_option.item_selected.connect(_on_signature_selected)
	
	# 初始化（等数据传入后再填充）

# 初始化界面，由主界面调用
func init_with_npc(npc_id: int):
	current_npc_id = npc_id
	var npc_manager = get_node("/root/NPCManager")
	current_npc = npc_manager.get_npc_by_id(npc_id)
	
	if current_npc.is_empty():
		print("错误：找不到NPC ID ", npc_id)
		return
	
	# 显示NPC口述文本
	request_label.text = current_npc["request_text"]
	
	# TODO: 设置头像（如果有资源的话）
	
	# 填充称谓下拉框
	fill_salutation_options()
	
	# 填充落款下拉框
	fill_signature_options()
	
	# 创建词库按钮
	create_word_pool_buttons()
	
	# 重置玩家答案
	reset_answers()

# 填充称谓下拉框
func fill_salutation_options():
	salutation_option.clear()
	var salutation_pool = current_npc["word_pool"]["salutation"]
	for text in salutation_pool:
		salutation_option.add_item(text)

# 填充落款下拉框
func fill_signature_options():
	signature_option.clear()
	var signature_pool = current_npc["word_pool"]["signature"]
	for text in signature_pool:
		signature_option.add_item(text)

# 创建词库按钮（正文填空用）
func create_word_pool_buttons():
	# 清空之前的按钮
	for child in word_pool_container.get_children():
		child.queue_free()
	
	# 获取正文各空位的词库（支持 body_slots 或 body_slot1/2/3 两种格式）
	var body_pool = {}
	if current_npc["word_pool"].has("body_slots"):
		body_pool = current_npc["word_pool"]["body_slots"]
	else:
		body_pool = {
			"slot1": current_npc["word_pool"].get("body_slot1", []),
			"slot2": current_npc["word_pool"].get("body_slot2", []),
			"slot3": current_npc["word_pool"].get("body_slot3", [])
		}
	
	for slot_name in body_pool.keys():
		var slot_label = Label.new()
		slot_label.text = slot_name + ": "
		word_pool_container.add_child(slot_label)
		
		var button_row = HBoxContainer.new()
		for word in body_pool[slot_name]:
			var btn = Button.new()
			btn.text = word
			btn.set_meta("slot_name", slot_name)
			btn.set_meta("word", word)
			btn.pressed.connect(_on_word_button_pressed.bind(btn))
			button_row.add_child(btn)
		word_pool_container.add_child(button_row)

# 点击词库按钮：填充对应的填空
func _on_word_button_pressed(btn):
	var slot_name = btn.get_meta("slot_name")
	var word = btn.get_meta("word")
	
	# 根据slot_name更新对应的填空按钮文本
	match slot_name:
		"slot1":
			body_slot1.text = word
			player_answers["body_slot1"] = word
		"slot2":
			body_slot2.text = word
			player_answers["body_slot2"] = word
		"slot3":
			body_slot3.text = word
			player_answers["body_slot3"] = word

# 称谓选择
func _on_salutation_selected(index: int):
	var text = salutation_option.get_item_text(index)
	player_answers["salutation"] = text

# 落款选择
func _on_signature_selected(index: int):
	var text = signature_option.get_item_text(index)
	player_answers["signature"] = text

# 提交按钮
func _on_submit_pressed():
	# 按设计：未填写/未选择视为格式错误，因此不自动补默认值
	var result: Dictionary = JudgeSystem.judge(current_npc, player_answers)
	pending_result = result
	_update_result_dialog(pending_result)
	result_dialog.popup_centered()

func _update_result_dialog(result: Dictionary) -> void:
	var result_code := str(result.get("result_code", ""))
	var fee := int(result.get("fee", 0))
	var format_err := int(result.get("format_error_count", 0))
	var content_mis := int(result.get("content_mismatch_count", 0))
	var perfect_count := int(result.get("perfect_count", 0))
	
	var title := "结算结果"
	match result_code:
		"PERFECT":
			title = "结算结果：完美（5/5 正确）"
		"NORMAL":
			title = "结算结果：普通（正确 %d 项，内容不匹配 %d 项）" % [perfect_count, content_mis]
		"WRONG":
			title = "结算结果：错误（格式错误 %d 项）" % format_err
	result_title_label.text = title
	
	if fee < 0:
		fee_label.text = "扣钱：%d文（净收入：-%d文）" % [abs(fee), abs(fee)]
	else:
		fee_label.text = "获得：%d文" % fee
	
	feedback_label.text = str(result.get("feedback_text", ""))

func _on_result_confirmed() -> void:
	# 确认后再结算并返回主界面
	var fee := int(pending_result.get("fee", 0))
	var npc_name := str(current_npc.get("name", "未知NPC"))
	PlayerManager.record_entry("commission", fee, "%s 委托结算" % npc_name, {"npc_id": current_npc_id, "npc_name": npc_name})
	PlayerManager.add_money(fee)
	return_to_main()

func _on_result_canceled() -> void:
	# 继续修改：不结算、不退出
	pass

# 重新填写按钮
func _on_reset_pressed():
	reset_answers()

func reset_answers():
	# 清空填空按钮文本
	body_slot1.text = ""
	body_slot2.text = ""
	body_slot3.text = ""
	
	# 重置下拉框选择（不选任何项）
	salutation_option.select(-1)
	signature_option.select(-1)
	
	# 清空答案记录
	player_answers = {
		"salutation": "",
		"body_slot1": "",
		"body_slot2": "",
		"body_slot3": "",
		"signature": ""
	}

# 返回主界面（显示主界面并移除代写界面，保留主界面状态）
func _on_back_pressed():
	return_to_main()

func return_to_main() -> void:
	var main = get_tree().root.get_node_or_null("Main")  # 确保主场景节点名为 Main
	if main:
		if main.has_method("on_npc_completed"):
			main.on_npc_completed(current_npc_id)
		main.show()
	queue_free()