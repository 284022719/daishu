extends Node

const RESULT_PERFECT := "PERFECT"
const RESULT_NORMAL := "NORMAL"
const RESULT_WRONG := "WRONG"

func _check_item(safe_answers: Dictionary, word_pool: Dictionary, answer_key: String, pool_key: String, correct_value: String, state: Dictionary) -> void:
	var v := str(safe_answers.get(answer_key, "")).strip_edges()
	if v == "":
		state["format_errors"] = int(state.get("format_errors", 0)) + 1
		return
	
	var pool: Array = word_pool.get(pool_key, [])
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
	elif content_mismatch > 0:
		result_code = RESULT_NORMAL
		fee = base_fee
		feedback_text = str(feedback.get("normal", ""))
	elif correct_count == 5:
		result_code = RESULT_PERFECT
		fee = base_fee + perfect_bonus
		feedback_text = str(feedback.get("perfect", ""))
	
	return {
		"fee": fee,
		"feedback_text": feedback_text,
		"result_code": result_code,
		"perfect_count": correct_count,
		"format_error_count": format_errors,
		"content_mismatch_count": content_mismatch
	}
