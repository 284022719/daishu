## 存档 JSON 格式（PlayerManager.save/load）

`PlayerManager.save()` / `load()` 通过内部的 `get_save_data()` 和 `apply_save_data()` 与磁盘上的 `user://save.dat` 交互。  
存档文件内容是一个顶层 **JSON 对象**，字段如下：

```json
{
  "money": 120,
  "day": 3,
  "completed_npcs": [-123456, -123789],
  "day_ledger": [
    {
      "kind": "commission",
      "amount": 20,
      "desc": "张大牛 委托结算",
      "meta": {
        "npc_id": -123456,
        "npc_name": "张大牛"
      }
    },
    {
      "kind": "commission",
      "amount": -5,
      "desc": "格式错误扣款",
      "meta": {}
    }
  ]
}
```

### 字段说明

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `money` | `int` | 当前玩家金钱。游戏中通过 `PlayerManager.money` 访问，结算与扣费后会更新该值。 |
| `day` | `int` | 当前天数（第几日），从 1 开始计数。用于驱动主界面显示以及 10 天限期的结局判定。 |
| `completed_npcs` | `Array<int>` | 当前天已经完成委托的 NPC id 列表。用于在主界面生成当日 NPC 列表时过滤，避免重复接同一委托。随机 NPC 的 id 一般为负数。 |
| `day_ledger` | `Array<Dictionary>` | 当日的收支流水明细列表，每个元素是一条账目记录。仅代表当前这一天的流水；每天结束时会被清空。 |

#### `day_ledger` 单条记录结构

每条记录（`Dictionary`）形如：

```json
{
  "kind": "commission",
  "amount": 20,
  "desc": "张大牛 委托结算",
  "meta": {
    "npc_id": -123456,
    "npc_name": "张大牛"
  }
}
```

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `kind` | `String` | 收支类型标记，例如 `"commission"` 表示委托结算。未来可扩展其他类型（如房租、事件等）。 |
| `amount` | `int` | 本条记录的金额。正数表示收入，负数表示支出或惩罚。 |
| `desc` | `String` | 文本描述，用于结算界面展示。例如 `"张大牛 委托结算"`。 |
| `meta` | `Dictionary` | 额外的元数据，结构不固定。当前用于存 NPC 相关信息，如 `{"npc_id": -123456, "npc_name": "张大牛"}`，也可以为空字典 `{}`。 |

> 备注：`PlayerManager.apply_save_data()` 会对 `money`、`day`、`completed_npcs` 和 `day_ledger` 做类型安全处理，并在应用后发出 `day_ledger_changed` 信号刷新界面。

---

## 随机 NPC 数据格式（NPCManager.generate_random_npc）

`NPCManager.generate_random_npc()` 返回表示一个 NPC 委托的 **字典**，其中包含展示用信息、正确答案、词库和计费配置。`get_today_npcs()` 会生成一个由此类字典组成的数组。

```json
{
  "npc_id": -123456789,
  "name": "张大牛",
  "first_day": 1,
  "required_calligraphy": 0,
  "avatar": "",
  "description": "一位普通的路人",
  "letter_type": "家书",
  "request_text": "我是张大牛，想给父母写封信。家中安好，在外保重，盼团聚。",
  "correct": {
    "salutation": "父母大人膝下",
    "body_slots": {
      "slot1": "安好",
      "slot2": "保重",
      "slot3": "团聚"
    },
    "signature": "男叩上"
  },
  "word_pool": {
    "salutation": ["父母大人膝下", "爹娘亲启"],
    "body_slots": {
      "slot1": ["安好", "安康", "平安", "无事"],
      "slot2": ["勿念", "保重", "加衣", "早归"],
      "slot3": ["回信", "团聚", "归家", "平安"]
    },
    "signature": ["男叩上", "儿拜上"]
  },
  "base_fee": 12,
  "perfect_bonus": 8,
  "feedback": {
    "perfect": "先生写得真好！",
    "normal": "还行吧",
    "wrong": "不对不对"
  }
}
```

### 顶层字段说明

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `npc_id` | `int` | NPC 的唯一标识。当前实现中为负数，基于时间戳和随机数生成，用于当天查找与存档。 |
| `name` | `String` | NPC 昵称，由 `FIRST_NAMES` + `LAST_NAMES` 随机组合，如 `"张大牛"`。 |
| `first_day` | `int` | NPC 首次出现的天数，目前恒为 `1`，为未来剧情扩展预留。 |
| `required_calligraphy` | `int` | 要求的书法等级，目前恒为 `0`，未来可用于书法系统。 |
| `avatar` | `String` | 头像资源路径，目前为空字符串。 |
| `description` | `String` | NPC 文本描述，例如 `"一位普通的路人"`。 |
| `letter_type` | `String` | 信件类型，目前为 `"家书"`。 |
| `request_text` | `String` | NPC 的口述需求文本，已经将正文正确词 `slot1/2/3` 格式化进句子内，供代写界面展示。 |
| `correct` | `Dictionary` | 当前 NPC 对应的“标准答案”，供 `JudgeSystem` 判定使用。 |
| `word_pool` | `Dictionary` | 提供给前端 UI 和 `JudgeSystem` 的合法词库，用于生成词按钮与校验格式。 |
| `base_fee` | `int` | 完成委托的基础报酬（内容正确但非全对时的报酬）。当前为 12 文。 |
| `perfect_bonus` | `int` | 五项全对时在 `base_fee` 基础上额外奖励的金额。当前为 8 文。 |
| `feedback` | `Dictionary` | 按不同判定结果（完美/一般/错误）给出的 NPC 文本反馈。 |

### `correct` 字段

```json
"correct": {
  "salutation": "父母大人膝下",
  "body_slots": {
    "slot1": "安好",
    "slot2": "保重",
    "slot3": "团聚"
  },
  "signature": "男叩上"
}
```

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `salutation` | `String` | 正确的称谓文本，对应信纸顶部称谓槽位。 |
| `body_slots` | `Dictionary` | 正文三个槽位的正确词。键为 `"slot1"`、`"slot2"`、`"slot3"`。 |
| `body_slots.slot1` | `String` | “家中 …” 句中的正确词。 |
| `body_slots.slot2` | `String` | “在外 …” 句中的正确词。 |
| `body_slots.slot3` | `String` | “盼 …” 句中的正确词。 |
| `signature` | `String` | 正确落款文本，对应信纸底部落款槽位。 |

### `word_pool` 字段

```json
"word_pool": {
  "salutation": ["父母大人膝下", "爹娘亲启"],
  "body_slots": {
    "slot1": ["安好", "安康", "平安", "无事"],
    "slot2": ["勿念", "保重", "加衣", "早归"],
    "slot3": ["回信", "团聚", "归家", "平安"]
  },
  "signature": ["男叩上", "儿拜上"]
}
```

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `salutation` | `Array<String>` | 可供选择的称谓列表。代写界面左侧“称谓词库”即来源于此。 |
| `body_slots` | `Dictionary` | 正文三个槽位的合法候选词列表。 |
| `body_slots.slot1` | `Array<String>` | “家中 …” 槽位可用的候选词。 |
| `body_slots.slot2` | `Array<String>` | “在外 …” 槽位可用的候选词。 |
| `body_slots.slot3` | `Array<String>` | “盼 …” 槽位可用的候选词。 |
| `signature` | `Array<String>` | 落款槽位可用的候选词。 |

> 说明：`JudgeSystem` 在判定时，既使用 `correct` 字段判断是否“答对”，也使用 `word_pool` 验证玩家答案是否来自合法词库（否则算格式错误并扣款）。

### `feedback` 字段

```json
"feedback": {
  "perfect": "先生写得真好！",
  "normal": "还行吧",
  "wrong": "不对不对"
}
```

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `perfect` | `String` | 五项全对时使用的 NPC 反馈文本。 |
| `normal` | `String` | 格式正确但有内容不匹配时使用的反馈文本，搭配 `base_fee`。 |
| `wrong` | `String` | 存在格式错误（空白或非法词）时使用的反馈文本，搭配按项数扣款。 |

