extends Area3D
## Interactive sacred landmark hotspot in Kamakhya Kshetra.

signal landmark_entered(hotspot: Node)
signal landmark_exited(hotspot: Node)
signal landmark_inspected(title: String, subtitle: String, description: String)

@export var site_id: String = "garbhagriha"
@export var title: String = "Garbhagriha — Main Shikhara"
@export var subtitle: String = "Nilachala Architectural Sanctum"
@export_multiline var description: String = ""

var discovered: bool = false


func _ready() -> void:
	body_entered.connect(_on_body_entered)
	body_exited.connect(_on_body_exited)


func _on_body_entered(body: Node3D) -> void:
	if body.has_method("set_active_hotspot"):
		body.set_active_hotspot(self)
		landmark_entered.emit(self)


func _on_body_exited(body: Node3D) -> void:
	if body.has_method("set_active_hotspot"):
		body.set_active_hotspot(null)
		landmark_exited.emit(self)


func trigger_lore() -> void:
	discovered = true
	landmark_inspected.emit(title, subtitle, description)
