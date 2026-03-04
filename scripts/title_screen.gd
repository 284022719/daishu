extends Control

@onready var start_btn: Button = $VBoxContainer/StartButton
@onready var continue_btn: Button = $VBoxContainer/ContinueButton
@onready var quit_btn: Button = $VBoxContainer/QuitButton

func _ready() -> void:
	start_btn.pressed.connect(_on_start_pressed)
	continue_btn.pressed.connect(_on_continue_pressed)
	quit_btn.pressed.connect(_on_quit_pressed)
	
	# 没有存档时可以考虑禁用“继续游戏”按钮
	continue_btn.disabled = not PlayerManager.has_save()

func _on_start_pressed() -> void:
	PlayerManager.reset()
	PlayerManager.save()
	get_tree().change_scene_to_file("res://scenes/prologue.tscn")

func _on_continue_pressed() -> void:
	if PlayerManager.has_save():
		PlayerManager.load()
		get_tree().change_scene_to_file("res://scenes/main.tscn")
	else:
		print("无存档，开始新游戏")
		_on_start_pressed()

func _on_quit_pressed() -> void:
	get_tree().quit()

