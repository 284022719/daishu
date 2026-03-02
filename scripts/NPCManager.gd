extends Node

# NPC数据数组，从JSON加载后填充
var npc_data = []

# 信号：数据加载完成
signal data_loaded

func _ready():
	load_npc_data()

# 从JSON文件加载NPC数据
func load_npc_data():
	var file = FileAccess.open("res://data/npc_data.json", FileAccess.READ)
	if file == null:
		push_error("无法打开NPC数据文件：res://data/npc_data.json")
		return
	
	var content = file.get_as_text()
	var json = JSON.new()
	var parse_result = json.parse(content)
	
	if parse_result != OK:
		push_error("JSON解析错误：", json.get_error_message(), " at line ", json.get_error_line())
		return
	
	# 假设JSON顶层是一个数组
	npc_data = json.data
	emit_signal("data_loaded")
	print("NPC数据加载成功，共 ", npc_data.size(), " 个NPC")

# 根据ID获取NPC数据
func get_npc_by_id(npc_id: int) -> Dictionary:
	for npc in npc_data:
		if npc["npc_id"] == npc_id:
			return npc
	return {}

# 获取今日NPC列表（原型阶段先返回全部，后续可按天数逻辑生成）
func get_today_npcs(day: int, exclude_ids: Array[int] = []) -> Array:
	# 动态生成逻辑：
	# - 仅选择 first_day <= day 的 NPC（解锁）
	# - 使用 day 作为随机种子，保证同一天结果稳定（可复现）
	# - 按天数逐步增加当日可接委托数量
	var unlocked: Array = []
	for npc in npc_data:
		var first_day := int(npc.get("first_day", 1))
		if first_day <= day:
			unlocked.append(npc)
	
	if unlocked.is_empty():
		return []
	
	# 稳定洗牌（Fisher–Yates）
	var rng := RandomNumberGenerator.new()
	rng.seed = int(day) * 1337 + 42
	for i in range(unlocked.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var tmp = unlocked[i]
		unlocked[i] = unlocked[j]
		unlocked[j] = tmp
	
	# 当日委托数量：第1天约3个，后续逐步增加，最多6个
	var desired_count: int = int(clamp(2 + int((day + 1) / 2), 3, 6))
	var result: Array = []
	for npc in unlocked:
		var npc_id := int(npc.get("npc_id", 0))
		if exclude_ids.has(npc_id):
			continue
		result.append(npc)
		if result.size() >= desired_count:
			break
	
	return result
