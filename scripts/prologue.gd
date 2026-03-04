extends Control

@onready var confirm_btn: Button = $VBoxContainer/ConfirmButton

func _ready() -> void:
	confirm_btn.pressed.connect(_on_confirm_pressed)

func _on_confirm_pressed() -> void:
	get_tree().change_scene_to_file("res://scenes/main.tscn")

