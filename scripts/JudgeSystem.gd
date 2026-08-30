extends Node

const RESULT_PERFECT := "PERFECT"
const RESULT_GOOD := "GOOD"
const RESULT_NORMAL := "NORMAL"
const RESULT_WRONG := "WRONG"

func _check_item(safe_answers: Dictionary, word_pool: Dictionary, answer_key: String, pool_key: String, correct_value: String, state: Dictionary) -> void:
	var v := str(safe_answers.get(answer_key, "")).strip_edges()
	if v == "":
		state["format_errors"] = int(state.get("format_errors", 0)) + 1
		return
	
	# 正文三项的词库在 word_pool.body_slots.slot1/2/3，不是 word_pool.body_slot1
	var pool: Array
	if pool_key.begins_with("body_slot"):
		var body_slots: Dictionary = word_pool.get("body_slots", {})
		var slot_name := pool_key  # body_slot1 -> 对应 body_slots.slot1（key 为 "slot1"）
		pool = body_slots.get(slot_name.replace("body_", ""), [])
	else:
		pool = word_pool.get(pool_key, [])
	if not pool.has(v):
		state["format_errors"] = int(state.get("format_errors", 0)) + 1
		return
	
	if v == correct_value:
		state["correct_count"] = int(state.get("correct_count", 0)) + 1
	else:
		state["content_mismatch"] = int(state.get("content_mismatch", 0)) + 1

func judge(npc: Dictionary, answers: Dictionary) -> Dictionary:
	var safe_npc := npc if npc != null else {}
	var safe_answers := answers if answers != null else {}
	
	var word_pool: Dictionary = safe_npc.get("word_pool", {})
	var correct: Dictionary = safe_npc.get("correct", {})
	var correct_body: Dictionary = correct.get("body_slots", {})
	
	var base_fee: int = int(safe_npc.get("base_fee", 0))
	var perfect_bonus: int = int(safe_npc.get("perfect_bonus", 0))
	var feedback: Dictionary = safe_npc.get("feedback", {})
	
	var state := {
		"format_errors": 0,
		"content_mismatch": 0,
		"correct_count": 0
	}
	
	_check_item(safe_answers, word_pool, "salutation", "salutation", str(correct.get("salutation", "")).strip_edges(), state)
	_check_item(safe_answers, word_pool, "body_slot1", "body_slot1", str(correct_body.get("slot1", "")).strip_edges(), state)
	_check_item(safe_answers, word_pool, "body_slot2", "body_slot2", str(correct_body.get("slot2", "")).strip_edges(), state)
	_check_item(safe_answers, word_pool, "body_slot3", "body_slot3", str(correct_body.get("slot3", "")).strip_edges(), state)
	_check_item(safe_answers, word_pool, "signature", "signature", str(correct.get("signature", "")).strip_edges(), state)
	
	var format_errors: int = int(state.get("format_errors", 0))
	var content_mismatch: int = int(state.get("content_mismatch", 0))
	var correct_count: int = int(state.get("correct_count", 0))
	
	var result_code := RESULT_NORMAL
	var fee := base_fee
	var feedback_text := str(feedback.get("normal", ""))
	
	if format_errors > 0:
		result_code = RESULT_WRONG
		fee = -2 * format_errors
		feedback_text = str(feedback.get("wrong", ""))
	elif correct_count == 5:
		result_code = RESULT_PERFECT
		fee = base_fee + perfect_bonus
		feedback_text = str(feedback.get("perfect", ""))
	elif correct_count == 4:
		# 阶梯：4/5 正确给 70% bonus，平滑"全有或全无"的技能悬崖
		result_code = RESULT_GOOD
		fee = base_fee + int(perfect_bonus * 0.7)
		feedback_text = str(feedback.get("good", feedback.get("normal", "")))
	else:
		# 内容错误（错词）：按 60% 底薪计费，让乱填有真实代价
		result_code = RESULT_NORMAL
		fee = int(base_fee * 0.6)
		feedback_text = str(feedback.get("normal", ""))
	
	# 每项是否正确，以及正确答案（供界面高亮用）
	var correct_answers: Dictionary = {
		"salutation": str(correct.get("salutation", "")).strip_edges(),
		"body_slot1": str(correct_body.get("slot1", "")).strip_edges(),
		"body_slot2": str(correct_body.get("slot2", "")).strip_edges(),
		"body_slot3": str(correct_body.get("slot3", "")).strip_edges(),
		"signature": str(correct.get("signature", "")).strip_edges()
	}
	var item_ok: Dictionary = {}
	for key in correct_answers.keys():
		var v := str(safe_answers.get(key, "")).strip_edges()
		item_ok[key] = (v == correct_answers[key])
	
	return {
		"fee": fee,
		"feedback_text": feedback_text,
		"result_code": result_code,
		"perfect_count": correct_count,
		"format_error_count": format_errors,
		"content_mismatch_count": content_mismatch,
		"correct_answers": correct_answers,
		"item_correct": item_ok
	}
