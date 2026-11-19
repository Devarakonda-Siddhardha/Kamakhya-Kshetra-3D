extends CharacterBody3D
## First-person exploration controller for Kamakhya Kshetra on Nilachal Hill.

@export var walk_speed: float = 6.5
@export var sprint_speed: float = 12.0
@export var jump_velocity: float = 5.5
@export var mouse_sensitivity: float = 0.0022
@export var gravity: float = 16.0

@onready var head: Node3D = $Head
@onready var camera: Camera3D = $Head/Camera3D

var _mouse_captured: bool = true
var _active_hotspot: Node = null


func _ready() -> void:
	Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("toggle_mouse"):
		_mouse_captured = not _mouse_captured
		Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED if _mouse_captured else Input.MOUSE_MODE_VISIBLE)

	if event is InputEventMouseButton and event.pressed and not _mouse_captured:
		_mouse_captured = true
		Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)

	if event is InputEventMouseMotion and _mouse_captured:
		rotate_y(-event.relative.x * mouse_sensitivity)
		head.rotate_x(-event.relative.y * mouse_sensitivity)
		head.rotation.x = clampf(head.rotation.x, deg_to_rad(-80.0), deg_to_rad(80.0))

	if event is InputEventScreenDrag:
		rotate_y(-event.relative.x * mouse_sensitivity * 1.4)
		head.rotate_x(-event.relative.y * mouse_sensitivity * 1.4)
		head.rotation.x = clampf(head.rotation.x, deg_to_rad(-80.0), deg_to_rad(80.0))

	if event.is_action_pressed("interact") and _active_hotspot != null:
		_active_hotspot.trigger_lore()


func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity.y -= gravity * delta

	if Input.is_action_just_pressed("jump") and is_on_floor():
		velocity.y = jump_velocity

	var input_dir := Input.get_vector("move_left", "move_right", "move_forward", "move_backward")
	var direction := (transform.basis * Vector3(input_dir.x, 0.0, input_dir.y)).normalized()
	var speed := sprint_speed if Input.is_action_pressed("sprint") else walk_speed

	if direction != Vector3.ZERO:
		velocity.x = direction.x * speed
		velocity.z = direction.z * speed
	else:
		velocity.x = move_toward(velocity.x, 0.0, speed * 8.0 * delta)
		velocity.z = move_toward(velocity.z, 0.0, speed * 8.0 * delta)

	move_and_slide()


func set_active_hotspot(hotspot: Node) -> void:
	_active_hotspot = hotspot
