extends Node

signal money_changed(new_money: int)
signal day_changed(new_day: int)

const STALL_FEE_PER_DAY: int = 2
const SAVE_PATH := "user://save_game.json"

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
	load_game()

func add_money(amount: int) -> void:
	money += amount

func next_day() -> void:
	day += 1
	# 这里可以触发每日结算后的自动扣除等逻辑

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
	# 只扣一次摊位费，不写入 ledger（避免第二天仍显示“昨天摊位费”）
	add_money(-STALL_FEE_PER_DAY)

func reset_day_ledger() -> void:
	day_ledger.clear()
	day_ledger_changed.emit()

func get_save_data() -> Dictionary:
	return {
		"money": money,
		"day": day,
		"completed_npcs": completed_npcs.duplicate()
	}

func apply_save_data(data: Dictionary) -> void:
	if data.has("money"):
		money = int(data.get("money", money))
	if data.has("day"):
		day = int(data.get("day", day))
	completed_npcs.clear()
	for id in data.get("completed_npcs", []):
		completed_npcs.append(int(id))

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

