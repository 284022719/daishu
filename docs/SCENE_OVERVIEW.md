## 场景总览

本项目主要场景包括：
- `title_screen.tscn`：标题菜单（新游戏 / 继续游戏 / 退出）
- `prologue.tscn`：剧情说明 / 目标介绍
- `main.tscn`：主界面（显示金钱、天数、当日 NPC 列表与每日操作）
- `letter.tscn`：代写信纸场景（拖拽式竖排填写）
- `success.tscn`：成功结局界面
- `gameover.tscn`：失败结局界面

以下对每个场景的功能、节点树和重要信号连接做简单说明。

---

## title_screen.tscn

**主要功能**：  
游戏的入口菜单，提供“开始游戏”“继续游戏”“退出游戏”。  
通过 `title_screen.gd` 调用 `PlayerManager` 实现新档/续档逻辑，并切换到后续场景。

### 节点树（缩进形式）

- `TitleScreen: Control`（脚本：`title_screen.gd`）
  - `TextureRect: TextureRect`  
    - 全屏背景图，使用 `assets/images/backgrounds/main.png`。
  - `VBoxContainer: VBoxContainer`（居中布局，垂直排列按钮）
    - `StartButton: Button`（文本："开始游戏"）
    - `ContinueButton: Button`（文本："继续游戏"）
    - `QuitButton: Button`（文本："退出游戏"）

### 重要信号连接（在 `title_screen.gd._ready()` 中）

- `StartButton.pressed` → `_on_start_pressed()`  
  - 调用 `PlayerManager.reset()` 重置状态。  
  - 调用 `PlayerManager.save()` 存初始档。  
  - `get_tree().change_scene_to_file("res://scenes/prologue.tscn")` 进入剧情说明。

- `ContinueButton.pressed` → `_on_continue_pressed()`  
  - 若 `PlayerManager.has_save()`：  
    - 调用 `PlayerManager.load()` 加载存档。  
    - 切到 `main.tscn`。  
  - 否则：打印 "无存档，开始新游戏"，并复用 `_on_start_pressed()` 逻辑。

- `QuitButton.pressed` → `_on_quit_pressed()`  
  - `get_tree().quit()` 退出游戏。

---

## prologue.tscn

**主要功能**：  
展示背景故事与赶考目标（10 天内凑齐 500 文），玩家点击“启程”进入主界面。

### 节点树

- `Prologue: Control`（脚本：`prologue.gd`）
  - `Panel: Panel`  
    - 全屏面板，可用于未来添加背景或装饰。
  - `VBoxContainer: VBoxContainer`（居中面板）
    - `StoryLabel: Label`  
      - 多行文本：介绍明代贫寒书生、进京赶考、10 天 / 500 文的设定。
    - `ConfirmButton: Button`（文本："启程"）

### 重要信号连接（`prologue.gd`）

- `ConfirmButton.pressed` → `_on_confirm_pressed()`  
  - `get_tree().change_scene_to_file("res://scenes/main.tscn")` 进入主界面。

---

## main.tscn

**主要功能**：  
游戏的主工作界面，负责显示：
- 当前金钱与天数（含 10 天限时目标提示）  
- 当日可接的 NPC 委托列表  
- 每日流程操作（开始今日 / 结束今日 / 保存并退出）

### 节点树

- `Main: Control`（脚本：`main.gd`）
  - `Background: TextureRect`  
    - 全屏背景图 `main_bg.png.png`。
  - `MainPanel: Panel`（带圆角与米黄色背景的主内容面板）
    - `VBoxContainer: VBoxContainer`（垂直布局主内容）
      - `StatusBar: HBoxContainer`  
        - `MoneyLabel: Label`（显示当前铜钱）  
        - `DayLabel: Label`（显示当前日数 / 总天数）  
        - `Spacer: Control`（右侧弹性空白，用于对齐）
      - `GoalLabel: Label`（文本："目标：十日内攒够 500 文"）
      - `Label: Label`（文本："今日可接委托："）
      - `ScrollContainer: ScrollContainer`
        - `NPCList: VBoxContainer`（动态生成每个 NPC 的按钮）
      - `ButtonBar: HBoxContainer`
        - `StartDayBtn: Button`（"开始今日"）
        - `EndDayBtn: Button`（"结束今日"）
        - `SaveQuitBtn: Button`（"保存并退出"）
  - `EndDayPopup: AcceptDialog`（结束今日结算弹窗）
    - `EndDayLabel: Label`（显示当日收入/支出/净收益等）

### 重要信号连接（`main.gd._ready()`）

- `StartDayBtn.pressed` → `_on_start_day_pressed()`  
  - 通过 `/root/NPCManager` 调用 `get_today_npcs(PlayerManager.day)` 获得当日 3 个随机 NPC。  
  - 清空 `NPCList`，为每个未完成 NPC 动态创建一个按钮，按钮的 `pressed` 连接到 `_on_npc_button_pressed(btn)`。

- `EndDayBtn.pressed` → `_on_end_day_pressed()`  
  - 调用 `PlayerManager.get_day_summary()` 构造结算文本，填入 `EndDayLabel` 并弹出 `EndDayPopup`。

- `SaveQuitBtn.pressed` → `_on_save_quit_pressed()`  
  - 调用 `PlayerManager.save()` 存档当前进度。  
  - 切回 `title_screen.tscn`。

- `EndDayPopup.confirmed` → `_on_end_day_popup_confirmed()`  
  - 执行每日结算逻辑：  
    - `PlayerManager.apply_end_of_day_costs()` 扣固定支出。  
    - `PlayerManager.next_day()` 推进天数并在必要时触发结局。  
    - `PlayerManager.reset_day_ledger()`、`reset_completed_npcs()` 清空当日数据。  
    - 清空 `NPCList` 并刷新 UI。

- 监听全局信号：  
  - `PlayerManager.money_changed` → `_on_money_changed()` → `update_ui()`  
  - `PlayerManager.day_changed` → `_on_day_changed()` → `update_ui()`

---

## letter.tscn

**主要功能**：  
代写信纸场景，左侧为可拖拽的词库，右侧为竖排毛笔字体的信纸槽位。玩家通过拖拽词语完成称谓、正文三空、落款，然后提交由 `JudgeSystem` 判定，并将结果同步到 `PlayerManager`。

### 节点树

- `Letter: Control`（脚本：`letter.gd`）
  - `Background: TextureRect`  
    - 右侧信纸背景图 `letter.png`。
  - `HSplit: HSplitContainer`（左右分栏，左窄右宽）
    - `WordPanel: Panel`（左侧词库面板，透明样式）
      - `WordVBox: VBoxContainer`
        - `SalutationLabel: Label`（"称谓词库"）
        - `SalutationContainer: VBoxContainer`（动态生成称谓词按钮）
        - `BodyLabel: Label`（"正文词库"）
        - `BodyContainer: VBoxContainer`（按正文槽位分组生成词按钮）
        - `SignatureLabel: Label`（"落款词库"）
        - `SignatureContainer: VBoxContainer`（动态生成落款词按钮）
    - `LetterPanel: Panel`（右侧信纸区域，透明）
      - `LetterVBox: VBoxContainer`（竖排布局）
        - `RequestLabel: Label`（竖排显示 NPC 口述文本）
        - `SalutationSlot: Panel`（脚本：`letter_slot.gd`，称谓槽）
          - `TextLabel: Label`（占位/竖排文字）
        - `BodySlot1: Panel`（脚本：`letter_slot.gd`，正文槽 1："家中 ______"）
          - `TextLabel: Label`
        - `BodySlot2: Panel`（正文槽 2："在外 ______"）
          - `TextLabel: Label`
        - `BodySlot3: Panel`（正文槽 3："盼 ______"）
          - `TextLabel: Label`
        - `SignatureSlot: Panel`（落款槽）
          - `TextLabel: Label`
  - `ButtonBar: HBoxContainer`（底部操作栏）
    - `SubmitBtn: Button`（"提交"）
    - `ResetBtn: Button`（"重新填写"）
    - `BackBtn: Button`（"返回主界面"）
  - `ResultPopup: AcceptDialog`（结算弹窗）
    - `ResultLabel: Label`（显示报酬、反馈与高亮正确答案，支持 BBCode）

### 重要信号连接（`letter.gd._ready()`）

- 底部按钮：
  - `SubmitBtn.pressed` → `_on_submit_pressed()`  
    - 调用 `JudgeSystem.judge(current_npc, player_answers)` 获取 `fee` 与反馈。  
    - 构建包含“获得/扣钱 + 反馈 + 正确答案对照”的 BBCode 文本，并弹出 `ResultPopup`。
  - `ResetBtn.pressed` → `_on_reset_pressed()` → `reset_answers()` 清空槽位与 `player_answers`。
  - `BackBtn.pressed` → `_on_back_pressed()` → `return_to_main()` 返回主界面。

- 结算弹窗：
  - `ResultPopup.confirmed` → `_on_result_popup_confirmed()`  
    - 从 `_pending_result` 取 `fee` 和 NPC 名字。  
    - `PlayerManager.record_entry("commission", fee, desc, meta)` 记录收入/扣款。  
    - `PlayerManager.add_money(fee)` 更新金钱。  
    - `return_to_main()` 通知 `Main.on_npc_completed(npc_id)` 并刷新主界面。

- 槽位与拖拽：
  - 在 `_ready()` 中：  
    - 对 `salutation_slot`、`body_slot1/2/3`、`signature_slot` 统一连接 `word_dropped(slot_key, word)` → `_on_slot_word_dropped(slot_key, word)`。  
    - `_on_slot_word_dropped` 根据 `slot_key` 更新 `player_answers` 中对应字段。

---

## success.tscn

**主要功能**：  
成功结局界面，展示成功文案，并提供“重玩”“退出游戏”按钮。与 `gameover.tscn` 共用 `EndGameScreen.gd`，通过导出的 `is_success = true` 区分。

### 节点树

- `SuccessScreen: Control`（脚本：`EndGameScreen.gd`，导出属性 `is_success = true`）
  - `VBoxContainer: VBoxContainer`（居中、留边距）
    - `MessageLabel: Label`（成功结局文案）
    - `Buttons: HBoxContainer`（中间对齐）
      - `RestartButton: Button`（"重玩"）
      - `QuitButton: Button`（"退出游戏"）

### 重要信号连接（`EndGameScreen.gd._ready()`）

- `_ready()` 根据 `is_success` 设置 `MessageLabel.text`：
  - 成功时文案：“恭喜！你凑齐了进京的路费，得以赶赴科考。金榜题名，从此改变命运……”。

- `RestartButton.pressed` → `_on_restart_pressed()`  
  - 调用 `PlayerManager.reset()` 重置游戏状态。  
  - 切回 `title_screen.tscn`，允许玩家重新选择“开始/继续”。

- `QuitButton.pressed` → `_on_quit_pressed()`  
  - `get_tree().quit()` 退出游戏。

---

## gameover.tscn

**主要功能**：  
失败结局界面，展示失败文案与“重玩”“退出游戏”按钮，同样使用 `EndGameScreen.gd`，但 `is_success = false`。

### 节点树

- `GameOverScreen: Control`（脚本：`EndGameScreen.gd`，导出属性 `is_success = false`）
  - `VBoxContainer: VBoxContainer`（布局同成功界面）
    - `MessageLabel: Label`（失败结局文案）
    - `Buttons: HBoxContainer`
      - `RestartButton: Button`（"重玩"）
      - `QuitButton: Button`（"退出游戏"）

### 重要信号连接（与 success.tscn 共用）

- `_ready()` 中，根据 `is_success = false` 设置失败文案：
  - “路费不足，你错过了今年的科考。壮志难酬，只得回乡另谋生计……”。

- `RestartButton.pressed`、`QuitButton.pressed` 的行为与成功结局完全一致：  
  - 重玩：`PlayerManager.reset()` + 回标题。  
  - 退出：`get_tree().quit()`。

---

> 说明：需求中提到的 `settlement.tscn` 在当前项目中并不存在；结算流程由 `main.tscn` 内的 `EndDayPopup` 弹窗与 `main.gd` 中的逻辑共同完成。若未来添加独立结算场景，可在本文件中追加相应条目。  

