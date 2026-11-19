extends Node3D
## Manages Kamakhya Kshetra lighting presets, flickering diya lamps, and sacred-site discovery.

@onready var sun: DirectionalLight3D = $DirectionalLight3D
@onready var world_env: WorldEnvironment = $WorldEnvironment
@onready var hud: CanvasLayer = $HUD
@onready var diya_lights: Node3D = $DiyaLights
@onready var hotspots_root: Node3D = $Landmarks

var _time_presets: Array[Dictionary] = [
	{
		"name": "Golden Dusk (Sandhya)",
		"sun_rot": Vector3(-22.0, 38.0, 0.0),
		"sun_color": Color(1.0, 0.68, 0.36),
		"sun_energy": 1.6,
		"ambient_energy": 0.45,
		"sky_top": Color(0.16, 0.20, 0.38),
		"sky_horizon": Color(0.88, 0.48, 0.26),
		"diya_energy": 2.4,
	},
	{
		"name": "Dawn (Usha)",
		"sun_rot": Vector3(-16.0, -45.0, 0.0),
		"sun_color": Color(1.0, 0.80, 0.56),
		"sun_energy": 1.3,
		"ambient_energy": 0.5,
		"sky_top": Color(0.24, 0.34, 0.58),
		"sky_horizon": Color(0.95, 0.66, 0.45),
		"diya_energy": 1.4,
	},
	{
		"name": "Midday (Madhyahna)",
		"sun_rot": Vector3(-68.0, 15.0, 0.0),
		"sun_color": Color(1.0, 0.96, 0.88),
		"sun_energy": 2.1,
		"ambient_energy": 0.75,
		"sky_top": Color(0.22, 0.52, 0.86),
		"sky_horizon": Color(0.70, 0.84, 0.96),
		"diya_energy": 0.4,
	},
	{
		"name": "Aarti Night (Ratri)",
		"sun_rot": Vector3(-35.0, 140.0, 0.0),
		"sun_color": Color(0.45, 0.55, 0.85),
		"sun_energy": 0.25,
		"ambient_energy": 0.18,
		"sky_top": Color(0.03, 0.05, 0.12),
		"sky_horizon": Color(0.10, 0.12, 0.22),
		"diya_energy": 3.6,
	},
]

var _preset_idx: int = 0
var _discovered_ids: Dictionary = {}
var _elapsed: float = 0.0


func _ready() -> void:
	for child in hotspots_root.get_children():
		if child.has_signal("landmark_entered"):
			child.landmark_entered.connect(_on_landmark_entered)
			child.landmark_exited.connect(_on_landmark_exited)
			child.landmark_inspected.connect(_on_landmark_inspected)
	_apply_time_preset(0)
	hud.update_discovery_count(0, hotspots_root.get_child_count())


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("cycle_time"):
		_preset_idx = (_preset_idx + 1) % _time_presets.size()
		_apply_time_preset(_preset_idx)


func _process(delta: float) -> void:
	_elapsed += delta
	var base_energy: float = _time_presets[_preset_idx]["diya_energy"]
	var idx := 0
	for light in diya_lights.get_children():
		if light is OmniLight3D:
			var flicker := 0.88 + 0.12 * sin(_elapsed * 7.5 + float(idx) * 1.9)
			light.light_energy = base_energy * flicker
			idx += 1


func _apply_time_preset(index: int) -> void:
	var p := _time_presets[index]
	sun.rotation_degrees = p["sun_rot"]
	sun.light_color = p["sun_color"]
	sun.light_energy = p["sun_energy"]
	if world_env.environment:
		world_env.environment.ambient_light_energy = p["ambient_energy"]
		var sky := world_env.environment.sky
		if sky and sky.sky_material is ProceduralSkyMaterial:
			var mat := sky.sky_material as ProceduralSkyMaterial
			mat.sky_top_color = p["sky_top"]
			mat.sky_horizon_color = p["sky_horizon"]
	hud.set_time_label(p["name"])


func _on_landmark_entered(hotspot: Node) -> void:
	hud.show_prompt("Press [E] to inspect: %s" % hotspot.title)


func _on_landmark_exited(_hotspot: Node) -> void:
	hud.hide_prompt()
	hud.hide_lore()


func _on_landmark_inspected(title: String, subtitle: String, description: String) -> void:
	_discovered_ids[title] = true
	hud.update_discovery_count(_discovered_ids.size(), hotspots_root.get_child_count())
	hud.show_lore(title, subtitle, description)
