extends Control

# 节点引用
@onready var money_label = $MainPanel/VBoxContainer/StatusBar/MoneyLabel
@onready var day_label = $MainPanel/VBoxContainer/StatusBar/DayLabel
@onready var npc_list_container = $MainPanel/VBoxContainer/ScrollContainer/NPCList
@onready var start_day_btn = $MainPanel/VBoxContainer/ButtonBar/StartDayBtn
@onready var end_day_btn = $MainPanel/VBoxContainer/ButtonBar/EndDayBtn
@onready var save_quit_btn = $MainPanel/VBoxContainer/ButtonBar/SaveQuitBtn
@onready var end_day_popup: AcceptDialog = $EndDayPopup
@onready var end_day_label: Label = $EndDayPopup/EndDayLabel

func _ready():
	# 连接按钮信号
	start_day_btn.pressed.connect(_on_start_day_pressed)
	end_day_btn.pressed.connect(_on_end_day_pressed)
	save_quit_btn.pressed.connect(_on_save_quit_pressed)
	end_day_popup.confirmed.connect(_on_end_day_popup_confirmed)
	end_day_popup.get_ok_button().text = "确认"
	
	# 监听玩家状态变化并刷新 UI
	PlayerManager.money_changed.connect(_on_money_changed)
	PlayerManager.day_changed.connect(_on_day_changed)
	
	# 初始化显示
	update_ui()
	
	# 默认不显示NPC列表（等点击“开始今日”后显示）
	clear_npc_list()

func add_money(delta: int) -> void:
	PlayerManager.add_money(delta)

func update_ui():
	money_label.text = "铜钱: " + str(PlayerManager.money) + "文"
	day_label.text = "第 %d 日 / 共 %d 日" % [PlayerManager.day, PlayerManager.TOTAL_DAYS]

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
	
	var today_npcs = npc_manager.get_today_npcs(PlayerManager.day)
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
	
	# 调用初始化函数（确保传入 int，与 NPCManager 查找一致）
	letter_instance.init_with_npc(int(npc_id))
	
	# 隐藏主界面（可选）
	self.hide()

func _on_end_day_pressed():
	var summary: Dictionary = PlayerManager.get_day_summary()
	var income := int(summary.get("income", 0))
	var expense := int(summary.get("expense", 0))
	var stall_fee := int(summary.get("stall_fee", 23))
	var net := int(summary.get("net", 0))
	var lines := "第 %d 日结算\n\n" % PlayerManager.day
	lines += "今日收入：%d 文\n" % income
	lines += "今日扣除：%d 文\n" % expense
	lines += "固定支出（摊位+房租+米钱）：%d 文\n\n" % stall_fee
	lines += "净收益：%d 文\n" % net
	lines += "确认后进入下一天。"
	end_day_label.text = lines
	end_day_popup.popup_centered()

func _on_end_day_popup_confirmed() -> void:
	PlayerManager.apply_end_of_day_costs()
	PlayerManager.next_day()
	PlayerManager.reset_day_ledger()
	PlayerManager.reset_completed_npcs()
	clear_npc_list()
	update_ui()

func _on_save_quit_pressed():
	print("保存并退出")
	PlayerManager.save()
	get_tree().change_scene_to_file("res://scenes/title_screen.tscn")
