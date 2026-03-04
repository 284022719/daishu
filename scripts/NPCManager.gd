extends Node

# 当日生成的 NPC 列表，供 get_npc_by_id 查找
var current_day_npcs: Array = []

# 常量定义（仅家书）
const FIRST_NAMES = ["张", "王", "李", "刘", "陈", "赵", "周"]
const LAST_NAMES = ["大牛", "二狗", "翠花", "铁柱", "秀英", "有才", "三娘"]
const RELATIONS = ["父母", "子女", "夫妻", "兄弟", "朋友"]

const SALUTATION_POOL = {
	"父母": ["父母大人膝下", "爹娘亲启"],
	"子女": ["吾儿如晤", "吾女见字"],
	"夫妻": ["夫君如晤", "贤妻妆次"],
	"兄弟": ["吾兄亲启", "贤弟如晤"],
	"朋友": ["仁兄足下", "好友如面"]
}

const SIGNATURE_POOL = {
	"父母": ["男叩上", "儿拜上"],
	"子女": ["父字", "母字"],
	"夫妻": ["妾拜上", "夫字"],
	"兄弟": ["弟谨启", "兄字"],
	"朋友": ["友拜上", "弟谨启"]
}

const BODY_SLOT1_WORDS = ["安好", "安康", "平安", "无事"]
const BODY_SLOT2_WORDS = ["勿念", "保重", "加衣", "早归"]
const BODY_SLOT3_WORDS = ["回信", "团聚", "归家", "平安"]

const FEEDBACK_PERFECT = ["先生写得真好！", "正是我想说的！", "太感谢了！"]
const FEEDBACK_NORMAL = ["还行吧", "就这样", "可以了"]
const FEEDBACK_WRONG = ["不对不对", "这写的啥？", "重写！"]

func generate_random_npc() -> Dictionary:
	var npc_id: int = -int(Time.get_unix_time_from_system() + randi() % 10000)

	var first: String = FIRST_NAMES[randi() % FIRST_NAMES.size()]
	var last: String = LAST_NAMES[randi() % LAST_NAMES.size()]
	var npc_name: String = first + last

	var relation: String = RELATIONS[randi() % RELATIONS.size()]
	var salutation_pool: Array = SALUTATION_POOL[relation]
	var signature_pool: Array = SIGNATURE_POOL[relation]

	var correct_salutation: String = salutation_pool[randi() % salutation_pool.size()]
	var correct_signature: String = signature_pool[randi() % signature_pool.size()]

	var correct_body: Dictionary = {
		"slot1": BODY_SLOT1_WORDS[randi() % BODY_SLOT1_WORDS.size()],
		"slot2": BODY_SLOT2_WORDS[randi() % BODY_SLOT2_WORDS.size()],
		"slot3": BODY_SLOT3_WORDS[randi() % BODY_SLOT3_WORDS.size()]
	}

	var word_pool: Dictionary = {
		"salutation": salutation_pool,
		"body_slots": {
			"slot1": BODY_SLOT1_WORDS,
			"slot2": BODY_SLOT2_WORDS,
			"slot3": BODY_SLOT3_WORDS
		},
		"signature": signature_pool
	}

	var story_templates: Array = [
		"我是{name}，想给{relation}写封信。家中{slot1}，在外{slot2}，盼{slot3}。",
		"给我{relation}带个话：家里{slot1}，你在外要{slot2}，记得{slot3}。",
		"写封信给{relation}：{slot1}，{slot2}，{slot3}。"
	]
	var story: String = story_templates[randi() % story_templates.size()].format({
		"name": npc_name,
		"relation": relation,
		"slot1": correct_body["slot1"],
		"slot2": correct_body["slot2"],
		"slot3": correct_body["slot3"]
	})

	var feedback: Dictionary = {
		"perfect": FEEDBACK_PERFECT[randi() % FEEDBACK_PERFECT.size()],
		"normal": FEEDBACK_NORMAL[randi() % FEEDBACK_NORMAL.size()],
		"wrong": FEEDBACK_WRONG[randi() % FEEDBACK_WRONG.size()]
	}

	return {
		"npc_id": npc_id,
		"name": npc_name,
		"first_day": 1,
		"required_calligraphy": 0,
		"avatar": "",
		"description": "一位普通的路人",
		"letter_type": "家书",
		"request_text": story,
		"correct": {
			"salutation": correct_salutation,
			"body_slots": correct_body,
			"signature": correct_signature
		},
		"word_pool": word_pool,
		"base_fee": 12,
		"perfect_bonus": 8,
		"feedback": feedback
	}

func get_today_npcs(_day: int) -> Array:
	var result: Array = []
	for i in range(3):
		result.append(generate_random_npc())
	current_day_npcs = result
	return result

func get_npc_by_id(npc_id: int) -> Dictionary:
	var id_int := int(npc_id)
	for npc in current_day_npcs:
		if int(npc.get("npc_id", 0)) == id_int:
			return npc
	return {}
