extends Control

# 节点引用
@onready var money_label = $VBoxContainer/StatusBar/MoneyLabel
@onready var day_label = $VBoxContainer/StatusBar/DayLabel
@onready var npc_list_container = $VBoxContainer/ScrollContainer/NPCList
@onready var start_day_btn = $VBoxContainer/ButtonBar/StartDayBtn
@onready var end_day_btn = $VBoxContainer/ButtonBar/EndDayBtn
@onready var save_quit_btn = $VBoxContainer/ButtonBar/SaveQuitBtn
@onready var day_settlement_dialog: ConfirmationDialog = $DaySettlementDialog
@onready var settlement_summary_label: Label = $DaySettlementDialog/DialogContent/SummaryLabel
@onready var settlement_details_label: RichTextLabel = $DaySettlementDialog/DialogContent/DetailsScroll/DetailsLabel

func _ready():
	# 连接按钮信号
	start_day_btn.pressed.connect(_on_start_day_pressed)
	end_day_btn.pressed.connect(_on_end_day_pressed)
	save_quit_btn.pressed.connect(_on_save_quit_pressed)
	
	# 监听玩家状态变化并刷新 UI
	PlayerManager.money_changed.connect(_on_money_changed)
	PlayerManager.day_changed.connect(_on_day_changed)
	
	# 初始化显示
	update_ui()
	
	# 默认不显示NPC列表（等点击“开始今日”后显示）
	clear_npc_list()
	
	day_settlement_dialog.confirmed.connect(_on_settlement_confirmed)
	day_settlement_dialog.canceled.connect(_on_settlement_canceled)
	day_settlement_dialog.get_ok_button().text = "确认结算并进入下一天"
	day_settlement_dialog.get_cancel_button().text = "返回继续接单"

func add_money(delta: int) -> void:
	PlayerManager.add_money(delta)

func update_ui():
	money_label.text = "铜钱: " + str(PlayerManager.money) + "文"
	day_label.text = "第 " + str(PlayerManager.day) + " 日"

func _on_money_changed(_new_money: int) -> void:
	update_ui()

func _on_day_changed(_new_day: int) -> void:
	update_ui()

func clear_npc_list():
	# 清空NPC列表容器中的所有子节点
	for child in npc_list_container.get_children():
		child.queue_free()

func _on_start_day_pressed():
	print("开始新的一天")
	# 调用NPCManager获取今日NPC
	var npc_manager = get_node("/root/NPCManager")  # 如果是自动加载的
	if not npc_manager:
		print("错误：找不到NPCManager")
		return
	
	var today_npcs = npc_manager.get_today_npcs(PlayerManager.day, PlayerManager.completed_npcs)
	print("今日NPC数量：", today_npcs.size())
	
	# 清空之前的列表
	clear_npc_list()
	
	# 为每个NPC创建一个按钮
	for npc in today_npcs:
		var npc_id = npc.get("npc_id", null)
		if npc_id != null and PlayerManager.is_npc_completed(int(npc_id)):
			continue
		var btn = Button.new()
		btn.text = npc["name"]
		# 将NPC的id存储在按钮的meta中，便于点击时获取
		btn.set_meta("npc_id", npc["npc_id"])
		btn.pressed.connect(_on_npc_button_pressed.bind(btn))
		npc_list_container.add_child(btn)

func on_npc_completed(npc_id: int) -> void:
	PlayerManager.mark_npc_completed(npc_id)
	for child in npc_list_container.get_children():
		if child is Button and child.has_meta("npc_id") and int(child.get_meta("npc_id")) == npc_id:
			child.queue_free()
			break

func _on_npc_button_pressed(btn):
	var npc_id = btn.get_meta("npc_id")
	print("点击了NPC：", btn.text, " ID: ", npc_id)
	
	# 切换到代写界面，并传入NPC ID
	var letter_scene = preload("res://scenes/letter.tscn")
	var letter_instance = letter_scene.instantiate()
	get_tree().root.add_child(letter_instance)
	
	# 调用初始化函数
	letter_instance.init_with_npc(npc_id)
	
	# 隐藏主界面（可选）
	self.hide()

func _on_end_day_pressed():
	print("结束今日")
	_show_day_settlement()

func _show_day_settlement() -> void:
	var summary: Dictionary = PlayerManager.get_day_summary()
	var income := int(summary.get("income", 0))
	var expense := int(summary.get("expense", 0))
	var stall_fee := int(summary.get("stall_fee", 0))
	var net := int(summary.get("net", 0))
	var entries: Array = summary.get("entries", [])
	
	settlement_summary_label.text = "第 %d 日结算：收入 %d 文，扣除 %d 文，摊位费 %d 文，净收益 %d 文" % [PlayerManager.day, income, expense, stall_fee, net]
	
	var lines: Array[String] = []
	if entries.is_empty():
		lines.append("（今日暂无委托结算记录）")
	else:
		for e in entries:
			var desc := str(e.get("desc", ""))
			var amount := int(e.get("amount", 0))
			if amount < 0:
				lines.append("- %s：扣钱 %d 文" % [desc, abs(amount)])
			else:
				lines.append("- %s：获得 %d 文" % [desc, amount])
	lines.append("")
	lines.append("- 摊位费：扣钱 %d 文" % stall_fee)
	
	settlement_details_label.text = "[b]当日收入明细[/b]\n" + "\n".join(lines)
	day_settlement_dialog.popup_centered()

func _on_settlement_confirmed() -> void:
	# 扣除摊位费、进入下一天、清空当日状态
	PlayerManager.apply_end_of_day_costs()
	PlayerManager.next_day()
	PlayerManager.reset_day_ledger()
	PlayerManager.reset_completed_npcs()
	clear_npc_list()

func _on_settlement_canceled() -> void:
	# 继续留在当天，不做任何结算动作
	pass

func _on_save_quit_pressed():
	print("保存并退出")
	PlayerManager.save_game()
	get_tree().quit()