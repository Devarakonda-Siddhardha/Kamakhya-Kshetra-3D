# Kamakhya Kshetra 3D — Blender & Godot 4 Exploration

An interactive 3D architectural and cultural exploration of **Kamakhya Kshetra** on **Nilachal Hill, Guwahati, Assam**, built with a procedural **Blender Python** asset pipeline and a **Godot 4** exploration project.

## Architectural & Sacred-Site References
- **Nilachala Style (1565, Koch King Nara Narayana)**: Cruciform carved stone plinth (`bada`) crowned by a bulbous ribbed polygonal brick dome (`shikhara`), ringed by 12 subsidiary `angashikharas`, golden `kalasha`, and `trishul` finial.
- **Four-Chamber East-to-West Axis**: `Garbhagriha` → `Calanta` (12-pillared hall) → `Pancharatna` (5-domed hall) → `Natamandira` (curved-roof ritual hall).
- **Sacred Complex**: `Saubhagya Kunda` stepped water tank with earthen `diyas`, Western Stone `Torana` with brass bells, `Bhuvaneshwari` summit shrine, `Tara` & `Kameshwara` shrines, Nilachal Hill banyan groves, and the northern **Brahmaputra River** vista.

## Project Structure
```text
kamakhya-kshetra-3d/
├── blender/
│   ├── build_kamakhya_kshetra.py     # Full Blender 3.6/4.x bpy builder + .blend & .glb export
│   └── generate_glb_standalone.py    # Pure-Python glTF 2.0 (.glb) generator (no Blender required)
└── godot/
    ├── project.godot                 # Godot 4.3+ project config & input bindings
    ├── assets/models/                # Pre-generated modular .glb 3D assets
    ├── scenes/
    │   ├── main.tscn                 # Assembled 3D Kamakhya Kshetra world
    │   └── hud.tscn                  # Exploration HUD & sacred-site lore cards
    └── scripts/
        ├── player_controller.gd      # First-person walk/sprint/jump & mouse look
        ├── kshetra_manager.gd        # Dawn / Midday / Golden Dusk / Aarti Night lighting + diyas
        ├── landmark_hotspot.gd       # Interactive sacred-site triggers
        └── hud.gd                    # HUD controller
```

## Quick Start

### 1. Open Directly in Godot 4
The binary `.glb` 3D models are already pre-generated in `godot/assets/models/`.
1. Open **Godot 4.3+** → **Import** → select `godot/project.godot`.
2. Press **F5** to launch the interactive 3D exploration.
3. Controls: `WASD` walk, `Shift` sprint, `Space` jump, `Mouse` look, `E` inspect shrine lore, `T` cycle time of day (Golden Dusk / Dawn / Midday / Aarti Night), `Esc` release mouse.

### 2. Edit or Rebuild 3D Models in Blender
```bash
blender --background --python blender/build_kamakhya_kshetra.py
```
This saves `blender/kamakhya_kshetra.blend` (open in Blender to sculpt, add custom textures, or render in Cycles) and re-exports all modular `.glb` assets into `godot/assets/models/`.
