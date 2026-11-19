extends CanvasLayer
## Exploration HUD for Kamakhya Kshetra 3D.

@onready var time_label: Label = $TopBar/Margin/HBox/TimeLabel
@onready var discovery_label: Label = $TopBar/Margin/HBox/DiscoveryLabel
@onready var prompt_panel: PanelContainer = $PromptPanel
@onready var prompt_label: Label = $PromptPanel/Margin/PromptLabel
@onready var lore_panel: PanelContainer = $LorePanel
@onready var lore_title: Label = $LorePanel/Margin/VBox/Title
@onready var lore_subtitle: Label = $LorePanel/Margin/VBox/Subtitle
@onready var lore_body: Label = $LorePanel/Margin/VBox/Body


func _ready() -> void:
	prompt_panel.visible = false
	lore_panel.visible = false


func set_time_label(text: String) -> void:
	time_label.text = "Time [T]: %s" % text


func update_discovery_count(found: int, total: int) -> void:
	discovery_label.text = "Sacred Sites Discovered: %d / %d" % [found, total]


func show_prompt(text: String) -> void:
	prompt_label.text = text
	prompt_panel.visible = true


func hide_prompt() -> void:
	prompt_panel.visible = false


func show_lore(title: String, subtitle: String, description: String) -> void:
	lore_title.text = title
	lore_subtitle.text = subtitle
	lore_body.text = description
	lore_panel.visible = true


func hide_lore() -> void:
	lore_panel.visible = false
