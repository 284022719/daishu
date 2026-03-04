## JudgeSystem.judge() 判定逻辑说明

本文档基于 `scripts/JudgeSystem.gd` 中的 `judge()` 方法，对代写判定规则进行自然语言总结，方便后续调试和平衡数值。

---

## 一、整体判定流程

`judge(npc: Dictionary, answers: Dictionary) -> Dictionary` 的主要步骤：

1. **读取 NPC 配置与玩家答案**
   - 从 `npc` 中读取：
     - `word_pool`: NPC 的合法词库（称谓、正文词库、落款），用于格式校验。
     - `correct`: 正确答案字典（包含 `salutation`、`body_slots`、`signature`）。
     - `correct_body`: `correct.body_slots`，包含 `"slot1" / "slot2" / "slot3"`。
     - 报酬配置：`base_fee`（基础报酬）、`perfect_bonus`（完美加成）。
     - 三种反馈文本：`feedback.perfect` / `feedback.normal` / `feedback.wrong`。
   - 将传入的 `answers` 存为 `safe_answers`，避免空引用。

2. **初始化统计状态 `state`**
   - `format_errors`: 0（格式错误次数）
   - `content_mismatch`: 0（内容不匹配次数）
   - `correct_count`: 0（完全正确的项数，总共 5 项）

3. **逐项检查 5 个答案**
   调用内部辅助函数 `_check_item()`，按顺序检查：
   - 称谓：  
     `_check_item(safe_answers, word_pool, "salutation", "salutation", correct.salutation, state)`
   - 正文三空：  
     - 第 1 空（家中 …）：`"body_slot1"` 对 `"body_slots.slot1"`  
     - 第 2 空（在外 …）：`"body_slot2"` 对 `"body_slots.slot2"`  
     - 第 3 空（盼 …）：`"body_slot3"` 对 `"body_slots.slot3"`
   - 落款：  
     `_check_item(safe_answers, word_pool, "signature", "signature", correct.signature, state)`

   每次 `_check_item` 会根据玩家答案更新 `state` 中的三个统计量（见后文“格式错误与内容错误定义”）。

4. **根据统计结果决定判定等级与报酬**
   - 统计量：
     - `format_errors`：格式错误次数。
     - `content_mismatch`：内容不匹配次数。
     - `correct_count`：5 项中答对的数量。
   - 逻辑分支：
     1. **若存在格式错误（`format_errors > 0`）**  
        - 判定结果：`result_code = RESULT_WRONG`（即 `"WRONG"`）。  
        - 报酬：`fee = -2 * format_errors`（按格式错误的项数扣钱，每项 -2 文）。  
        - 反馈文本：`feedback_text = feedback.wrong`。
     2. **否则，如存在内容不匹配（`content_mismatch > 0`）**  
        - 判定结果：`result_code = RESULT_NORMAL`（即 `"NORMAL"`）。  
        - 报酬：`fee = base_fee`（拿到基础报酬，视为“写得还行”）。  
        - 反馈文本：`feedback_text = feedback.normal`。
     3. **否则，如果五项全对（`correct_count == 5`）**  
        - 判定结果：`result_code = RESULT_PERFECT`（即 `"PERFECT"`）。  
        - 报酬：`fee = base_fee + perfect_bonus`（基础报酬 + 完美加成）。  
        - 反馈文本：`feedback_text = feedback.perfect`。
     4. 如果三类统计量均为 0（极端情况下 answers 全缺省且未记入错误），则保持默认：  
        - 结果：`RESULT_NORMAL`、`fee = base_fee`、`feedback_text = feedback.normal`。

5. **构造附加信息（用于界面高亮与分析）**
   - `correct_answers` 字典：  
     将 `correct` 和 `correct_body` 中的五个“标准答案”拉平成：
     - `"salutation"`：正确称谓
     - `"body_slot1"` / `"body_slot2"` / `"body_slot3"`：三个正文槽位的正确词
     - `"signature"`：正确落款
   - `item_correct` 字典：  
     对每个 key 比较 `answers[key]` 与 `correct_answers[key]` 是否一致，结果为布尔值，用于 UI 标出每项是否做对。

6. **返回判定结果字典**
   返回的 `Dictionary` 包含：

   - `fee`: `int`，本次委托收支（>0 收入，<0 扣款）。  
   - `feedback_text`: `String`，用于显示在结算弹窗中的 NPC 反馈。  
   - `result_code`: `String`，取值为 `"PERFECT"` / `"NORMAL"` / `"WRONG"`。  
   - `perfect_count`: `int`，即 `correct_count`，表示完全正确的项数。  
   - `format_error_count`: `int`，格式错误总数。  
   - `content_mismatch_count`: `int`，内容不匹配总数。  
   - `correct_answers`: `Dictionary`，五项标准答案。  
   - `item_correct`: `Dictionary`，逐项是否答对的布尔标记。

---

## 二、格式错误与内容错误的定义

### 1. `_check_item()` 的输入

`_check_item(safe_answers, word_pool, answer_key, pool_key, correct_value, state)` 主要关心：

- `answer_key`：玩家答案在 `answers` 中的键（如 `"salutation"`、`"body_slot1"` 等）。
- `pool_key`：对应的词库键：
  - 称谓、落款：直接在 `word_pool` 顶层取 `word_pool["salutation"]`、`word_pool["signature"]`。
  - 正文三空：`body_slot1/2/3` 特殊处理，从 `word_pool["body_slots"]["slot1/2/3"]` 取词库。
- `correct_value`：该项的正确答案文本。

### 2. 格式错误（`format_errors`）

一项会被判为“格式错误”的情况：

1. **玩家未填写（空值）**  
   - 从 `safe_answers` 取出答案，调用 `str(...).strip_edges()` 去掉首尾空白后，如果结果是空字符串 `""`：  
     - 直接 `state["format_errors"] += 1`，并 **返回**，不再检查内容。

2. **答案不在合法词库中**  
   - 从 `word_pool` 或 `word_pool["body_slots"]` 中取出该项对应的合法候选词数组 `pool`。  
   - 如果 `pool.has(v)` 为 `false`，说明玩家填写的词 **不在该项合法候选中**：
     - 记为 `format_errors`，`state["format_errors"] += 1`，并返回。

> 总结：**空白** 或 **乱写词（不在词库）** 都记为格式错误。  
> 只要一项被视为格式错误，就不会进入“内容匹配”的比较。

### 3. 内容错误（`content_mismatch`）

当 `_check_item()` 确认：

- 答案非空；且  
- 答案属于对应词库 `pool` 中的一个合法项；

这时进一步比较：

- 若 `v == correct_value`：  
  - 该项视为**完全正确**，`state["correct_count"] += 1`。
- 若 `v != correct_value`：  
  - 该项视为**内容不匹配**，`state["content_mismatch"] += 1`。

> 注意：内容错误不影响格式统计；它只在后续“计费规则”中决定是拿基础报酬还是完美加成。

---

## 三、计费规则

计费逻辑基于三种统计结果（格式错误、内容错误、全对），优先级依次为：**格式错误 > 内容错误 > 完美**。

1. **格式错误存在（`format_errors > 0`）**
   - 视为严重问题：玩家写的内容不合规范或乱写。
   - 结果：
     - `result_code = "WRONG"`  
     - `fee = -2 * format_errors`（按项扣钱）  
     - `feedback_text = feedback.wrong`

2. **无格式错误但有内容错误（`format_errors == 0 && content_mismatch > 0`）**
   - 视为“格式合格但内容不完全符合期望”。
   - 结果：
     - `result_code = "NORMAL"`  
     - `fee = base_fee`（基础报酬，常量由 NPC 配置给出）  
     - `feedback_text = feedback.normal`

3. **五项全部正确（`correct_count == 5`）**
   - 在前两种情况都不成立时，若 `correct_count == 5`：
   - 结果：
     - `result_code = "PERFECT"`  
     - `fee = base_fee + perfect_bonus`（基础报酬 + 完美加成）  
     - `feedback_text = feedback.perfect`

4. **其他极端情况**
   - 若以上都不满足（例如 `answers` 为空但未记入错误——理论上不应发生），则保持初始化：  
     - `result_code = "NORMAL"`  
     - `fee = base_fee`  
     - `feedback_text = feedback.normal`

---

## 四、result_code 的含义

返回字典中的 `result_code` 取值为下列三种常量之一：

- `RESULT_PERFECT` / `"PERFECT"`：
  - 条件：五项答案全部正确。
  - 意义：格式与内容都完全符合 NPC 期待，获得最高报酬（`base_fee + perfect_bonus`）。
  - UI 用途：可用于展示特殊动画或“完美”标记。

- `RESULT_NORMAL` / `"NORMAL"`：
  - 条件：无格式错误，但至少一项内容不匹配，或作为安全兜底。
  - 意义：写得“还行”，格式过关，内容大体能看，但不完全合心意；只给基础报酬。

- `RESULT_WRONG` / `"WRONG"`：
  - 条件：至少存在一项格式错误。
  - 意义：玩家在形式上就不合要求（没填或乱写），属于“写错信”；通过扣钱惩罚。

---

## 五、其他细节与空值处理

1. **空值处理**
   - 在 `_check_item()` 中，将从 `answers` 取到的值统一：
     ```gdscript
     var v := str(safe_answers.get(answer_key, "")).strip_edges()
     ```
   - 这意味着：
     - `null`、缺少键、或仅有空格的答案，都会被视为 `""`，直接记入 `format_errors`。

2. **正文三槽的词库特殊处理**
   - `_check_item()` 中，对于 `"body_slot1/2/3"` 并不是直接用 `word_pool["body_slot1"]`，而是：
     - 访问 `word_pool["body_slots"]`，再根据 `"slot1/2/3"` 取对应数组。
   - 这是因为 NPC 配置中将正文词库统一存放在嵌套字典 `body_slots` 下，避免字段分散。

3. **安全访问 NPC 与答案**
   - `npc` 和 `answers` 均通过“安全字典”处理：
     ```gdscript
     var safe_npc := npc if npc != null else {}
     var safe_answers := answers if answers != null else {}
     ```
   - 避免因传入 `null` 导致运行时错误。

4. **界面高亮依赖的返回字段**
   - `correct_answers` 为 UI 提供了标准答案文本，用于在结算弹窗中展示“正确答案”。
   - `item_correct` 则让 UI 能在逐项上标注“你填的 vs 正确的”的区别，支持错误项特别高亮。

综合来看，`JudgeSystem.judge()` 将判定逻辑分成**格式 → 内容 → 计费 → 反馈 → 高亮信息**五个层次，实现了对玩家填写质量的较细粒度区分，同时为 UI 与数值平衡提供了必要的统计信息。  

