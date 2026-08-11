extends Node

signal money_changed(new_money: int)
signal day_changed(new_day: int)

const STALL_FEE_PER_DAY: int = 10 # 每日固定支出（摊位+房租+米钱等）
const SAVE_PATH := "user://save.dat"
const TOTAL_DAYS: int = 10
const TARGET_MONEY: int = 500

signal day_ledger_changed

var completed_npcs: Array[int] = []

var money: int = 100:
	set(value):
		money = value
		money_changed.emit(money)

var day: int = 1:
	set(value):
		day = value
		day_changed.emit(day)

var day_ledger: Array[Dictionary] = []

func _ready() -> void:
	# 存档加载由标题界面控制，这里不自动加载
	pass

func add_money(amount: int) -> void:
	money += amount
	if money < 0:
		show_failure_scene()

func next_day() -> void:
	day += 1
	if day > TOTAL_DAYS:
		check_endgame()

func is_npc_completed(npc_id: int) -> bool:
	return completed_npcs.has(npc_id)

func mark_npc_completed(npc_id: int) -> void:
	if not completed_npcs.has(npc_id):
		completed_npcs.append(npc_id)

func reset_completed_npcs() -> void:
	completed_npcs.clear()

func record_entry(kind: String, amount: int, desc: String, meta: Dictionary = {}) -> void:
	day_ledger.append({
		"kind": kind,
		"amount": amount,
		"desc": desc,
		"meta": meta
	})
	day_ledger_changed.emit()

func get_day_summary() -> Dictionary:
	var income := 0
	var expense := 0
	for e in day_ledger:
		var a := int(e.get("amount", 0))
		if a >= 0:
			income += a
		else:
			expense += -a
	
	var stall_fee := STALL_FEE_PER_DAY
	var net := income - expense - stall_fee
	return {
		"income": income,
		"expense": expense,
		"stall_fee": stall_fee,
		"net": net,
		"entries": day_ledger.duplicate(true)
	}

func apply_end_of_day_costs() -> void:
	add_money(-STALL_FEE_PER_DAY)

func reset_day_ledger() -> void:
	day_ledger.clear()
	day_ledger_changed.emit()

func reset() -> void:
	money = 100
	day = 1
	reset_completed_npcs()
	reset_day_ledger()

func check_endgame() -> void:
	if money >= TARGET_MONEY and money >= 0:
		show_success_scene()
	else:
		show_failure_scene()

func show_success_scene() -> void:
	get_tree().change_scene_to_file("res://scenes/success.tscn")

func show_failure_scene() -> void:
	get_tree().change_scene_to_file("res://scenes/gameover.tscn")

func get_save_data() -> Dictionary:
	return {
		"money": money,
		"day": day,
		"completed_npcs": completed_npcs.duplicate(),
		"day_ledger": day_ledger.duplicate(true)
	}

func apply_save_data(data: Dictionary) -> void:
	if data.has("money"):
		money = int(data.get("money", money))
	if data.has("day"):
		day = int(data.get("day", day))
	completed_npcs.clear()
	for id in data.get("completed_npcs", []):
		completed_npcs.append(int(id))
	day_ledger.clear()
	for e in data.get("day_ledger", []):
		if typeof(e) == TYPE_DICTIONARY:
			day_ledger.append(e)
	day_ledger_changed.emit()

func save_game() -> void:
	var file := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if file == null:
		push_error("保存失败：无法打开存档文件 %s" % SAVE_PATH)
		return
	var data := get_save_data()
	file.store_string(JSON.stringify(data))

func load_game() -> void:
	if not FileAccess.file_exists(SAVE_PATH):
		return
	var file := FileAccess.open(SAVE_PATH, FileAccess.READ)
	if file == null:
		push_error("读取失败：无法打开存档文件 %s" % SAVE_PATH)
		return
	var content := file.get_as_text()
	var json := JSON.new()
	var err := json.parse(content)
	if err != OK:
		push_error("存档 JSON 解析失败：%s" % json.get_error_message())
		return
	var data = json.data
	if typeof(data) == TYPE_DICTIONARY:
		apply_save_data(data)

func has_save() -> bool:
	return FileAccess.file_exists(SAVE_PATH)

func save() -> void:
	save_game()

func load() -> void:
	load_game()

