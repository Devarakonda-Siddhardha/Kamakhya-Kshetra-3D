"""
Kamakhya Kshetra — Procedural 3D World Builder for Blender (3.6 / 4.x)
======================================================================
Generates the Nilachal Hill sacred complex of Kamakhya Kshetra (Guwahati, Assam)
based on Nilachala temple architecture:
  1. Main Kamakhya Temple (East -> West):
       - Garbhagriha: cruciform stone bada + ribbed bulbous polygonal shikhara,
         ring of 12 angashikharas, golden kalasha & trishul finial.
       - Calanta: 12-pillared hall with secondary Nilachala dome.
       - Pancharatna: five-domed hall (1 central + 4 corner domes).
       - Natamandira: curved apsidal-roof ritual hall with arched portals.
  2. Saubhagya Kunda: stepped stone sacred tank with water surface & earthen diyas.
  3. Entrance Torana Gate with hanging brass temple bells.
  4. Surrounding Nilachal Hill shrines (Bhuvaneshwari Summit, Tara, Kameshwara, Bagalamukhi).
  5. Nilachal Hill terrain, stone stairways, courtyard, banyan foliage & Brahmaputra River vista.

Usage (CLI):
    blender --background --python blender/build_kamakhya_kshetra.py

Exports:
    - kamakhya_kshetra.blend (next to this script)
    - Modular .glb files into ../godot/assets/models/
"""

import math
import os
import bpy
import bmesh
from mathutils import Vector, Euler

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "godot", "assets", "models"))
os.makedirs(EXPORT_DIR, exist_ok=True)


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def make_material(name, base_color, roughness=0.75, metallic=0.0, emission=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission is not None and emission_strength > 0.0:
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
            bsdf.inputs["Emission Strength"].default_value = emission_strength
        elif "Emission" in bsdf.inputs:
            bsdf.inputs["Emission"].default_value = (*emission, 1.0)
    return mat


def create_materials():
    return {
        "stone_granite": make_material("Stone_Granite", (0.42, 0.39, 0.36), roughness=0.88),
        "stone_carved": make_material("Stone_Carved", (0.52, 0.47, 0.41), roughness=0.82),
        "plaster_cream": make_material("Plaster_Cream", (0.86, 0.80, 0.70), roughness=0.78),
        "terracotta": make_material("Terracotta_Red", (0.64, 0.24, 0.14), roughness=0.72),
        "vermilion": make_material("Vermilion_Ochre", (0.76, 0.28, 0.15), roughness=0.68),
        "gold": make_material("Gold_Kalasha", (0.95, 0.76, 0.24), roughness=0.22, metallic=0.95),
        "brass": make_material("Brass_Bell", (0.78, 0.58, 0.22), roughness=0.32, metallic=0.88),
        "water_kunda": make_material("Water_Saubhagya", (0.06, 0.19, 0.20), roughness=0.08, metallic=0.15),
        "water_river": make_material("Water_Brahmaputra", (0.14, 0.27, 0.34), roughness=0.15, metallic=0.10),
        "hill_grass": make_material("Nilachal_Grass", (0.16, 0.31, 0.13), roughness=0.92),
        "foliage": make_material("Tropical_Foliage", (0.11, 0.27, 0.09), roughness=0.85),
        "bark": make_material("Tree_Bark", (0.24, 0.17, 0.12), roughness=0.92),
        "diya_clay": make_material("Diya_Clay", (0.52, 0.25, 0.14), roughness=0.85),
        "diya_flame": make_material("Diya_Flame", (1.0, 0.72, 0.22), roughness=0.2,
                                    emission=(1.0, 0.62, 0.15), emission_strength=8.0),
    }


def get_or_create_collection(name):
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def link_obj(obj, col):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)


def add_box(name, size, location, mat, col, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    obj.data.materials.append(mat)
    link_obj(obj, col)
    return obj


def add_cylinder(name, radius, depth, location, mat, col, vertices=16, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                        location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(mat)
    link_obj(obj, col)
    return obj


def add_nilachala_dome(name, radius, height, location, mat, col, segments=16, rings=14, ribbed=True):
    """Creates a bulbous, ribbed polygonal beehive shikhara characteristic of Nilachala architecture."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    ring_verts = []
    for r in range(rings + 1):
        t = r / rings
        # Bulbous beehive profile: swells slightly at t~0.18 then curves inward smoothly
        profile = math.sin(t * math.pi * 0.52 + 0.12) ** 0.75
        taper = (1.0 - t) ** 0.58
        rad = radius * (0.28 + 0.72 * taper) * (1.0 + 0.12 * math.sin(t * math.pi))
        if ribbed and 0 < r < rings:
            rad *= 1.0 + 0.03 * math.sin(r * math.pi)
        if r == rings:
            rad = radius * 0.12
        z = t * height
        verts = []
        for s in range(segments):
            ang = (2.0 * math.pi * s) / segments
            verts.append(bm.verts.new((rad * math.cos(ang), rad * math.sin(ang), z)))
        ring_verts.append(verts)

    for r in range(rings):
        for s in range(segments):
            s_next = (s + 1) % segments
            bm.faces.new((
                ring_verts[r][s],
                ring_verts[r][s_next],
                ring_verts[r + 1][s_next],
                ring_verts[r + 1][s],
            ))
    # Cap top
    top_center = bm.verts.new((0.0, 0.0, height * 1.03))
    for s in range(segments):
        s_next = (s + 1) % segments
        bm.faces.new((ring_verts[rings][s], ring_verts[rings][s_next], top_center))

    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    obj.data.materials.append(mat)
    link_obj(obj, col)
    return obj


def add_kalasha_finial(name_prefix, base_pos, scale, mats, col, with_trishul=False):
    x, y, z = base_pos
    add_cylinder(f"{name_prefix}_Amalaka", 0.55 * scale, 0.28 * scale, (x, y, z + 0.14 * scale), mats["gold"], col, 16)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.35 * scale,
                                         location=(x, y, z + 0.55 * scale))
    pot = bpy.context.active_object
    pot.name = f"{name_prefix}_KalashaPot"
    pot.data.materials.append(mats["gold"])
    link_obj(pot, col)
    bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.22 * scale, radius2=0.02 * scale,
                                    depth=0.9 * scale, location=(x, y, z + 1.25 * scale))
    spire = bpy.context.active_object
    spire.name = f"{name_prefix}_Spire"
    spire.data.materials.append(mats["gold"])
    link_obj(spire, col)
    if with_trishul:
        add_cylinder(f"{name_prefix}_TrishulStaff", 0.05 * scale, 1.4 * scale,
                     (x, y, z + 2.2 * scale), mats["gold"], col, 8)
        for side in (-1, 1):
            add_box(f"{name_prefix}_TrishulProng_{side}", (0.06 * scale, 0.06 * scale, 0.55 * scale),
                    (x + side * 0.22 * scale, y, z + 2.75 * scale), mats["gold"], col,
                    rotation=(0, side * 0.35, 0))


def build_kamakhya_main_temple(mats):
    """Builds the 4-chamber main Kamakhya Temple along the X axis (East=+X to West=-X)."""
    col = get_or_create_collection("Kamakhya_Temple")

    # 1. GARBHAGRIHA (East, X = +9.0)
    gx = 9.0
    add_box("Garbhagriha_Plinth", (9.4, 9.4, 1.4), (gx, 0.0, 0.7), mats["stone_granite"], col)
    # Cruciform ratha-style bada projections
    add_box("Garbhagriha_BadaCore", (7.6, 7.6, 5.2), (gx, 0.0, 4.0), mats["stone_carved"], col)
    add_box("Garbhagriha_RathaX", (8.6, 4.4, 5.0), (gx, 0.0, 3.9), mats["stone_carved"], col)
    add_box("Garbhagriha_RathaY", (4.4, 8.6, 5.0), (gx, 0.0, 3.9), mats["stone_carved"], col)
    # Main ribbed beehive Nilachala Shikhara
    add_nilachala_dome("Garbhagriha_Shikhara", 4.1, 8.8, (gx, 0.0, 6.5), mats["terracotta"], col, 16, 16, True)
    add_kalasha_finial("Garbhagriha_Finial", (gx, 0.0, 15.3), 1.25, mats, col, with_trishul=True)

    # Ring of 12 Angashikharas (minaret-inspired subsidiary domes)
    for i in range(12):
        ang = (2.0 * math.pi * i) / 12.0
        ax = gx + 3.95 * math.cos(ang)
        ay = 3.95 * math.sin(ang)
        add_cylinder(f"Angashikhara_Base_{i}", 0.55, 1.5, (ax, ay, 7.25), mats["stone_carved"], col, 10)
        add_nilachala_dome(f"Angashikhara_Dome_{i}", 0.62, 2.3, (ax, ay, 8.0), mats["vermilion"], col, 10, 8, False)
        add_kalasha_finial(f"Angashikhara_Finial_{i}", (ax, ay, 10.3), 0.32, mats, col)

    # 2. CALANTA (12-pillared hall, X = +1.5)
    cx = 1.5
    add_box("Calanta_Plinth", (6.2, 7.4, 1.2), (cx, 0.0, 0.6), mats["stone_granite"], col)
    add_box("Calanta_RoofSlab", (6.0, 7.0, 0.6), (cx, 0.0, 4.8), mats["terracotta"], col)
    for px in (-2.2, -0.75, 0.75, 2.2):
        for py in (-2.8, 0.0, 2.8):
            if abs(px) < 1.5 and abs(py) < 1.0:
                continue
            add_cylinder(f"Calanta_Pillar_{px}_{py}", 0.24, 3.6, (cx + px, py, 3.0), mats["stone_carved"], col, 12)
    add_nilachala_dome("Calanta_Dome", 2.3, 4.2, (cx, 0.0, 5.1), mats["vermilion"], col, 14, 10, False)
    add_kalasha_finial("Calanta_Finial", (cx, 0.0, 9.3), 0.72, mats, col)

    # 3. PANCHARATNA (Five-domed hall, X = -5.2)
    px0 = -5.2
    add_box("Pancharatna_Plinth", (7.4, 7.8, 1.2), (px0, 0.0, 0.6), mats["stone_granite"], col)
    add_box("Pancharatna_Walls", (7.0, 7.2, 4.4), (px0, 0.0, 3.4), mats["plaster_cream"], col)
    add_box("Pancharatna_Cornice", (7.5, 7.7, 0.5), (px0, 0.0, 5.7), mats["terracotta"], col)
    # Central dome + 4 corner domes
    add_nilachala_dome("Pancharatna_CenterDome", 2.4, 4.8, (px0, 0.0, 5.95), mats["terracotta"], col, 14, 12, True)
    add_kalasha_finial("Pancharatna_CenterFinial", (px0, 0.0, 10.75), 0.75, mats, col)
    for dx in (-2.4, 2.4):
        for dy in (-2.5, 2.5):
            add_nilachala_dome(f"Pancharatna_CornerDome_{dx}_{dy}", 1.15, 2.7,
                               (px0 + dx, dy, 5.95), mats["vermilion"], col, 12, 8, False)
            add_kalasha_finial(f"Pancharatna_CornerFinial_{dx}_{dy}", (px0 + dx, dy, 8.65), 0.4, mats, col)

    # 4. NATAMANDIRA (West apsidal curved-roof ritual hall, X = -13.2)
    nx = -13.2
    add_box("Natamandira_Plinth", (9.0, 7.6, 1.1), (nx, 0.0, 0.55), mats["stone_granite"], col)
    add_box("Natamandira_Walls", (8.6, 7.0, 3.6), (nx, 0.0, 2.9), mats["plaster_cream"], col)
    # Curved barrel/apsidal roof
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=3.7, depth=8.8,
                                        location=(nx, 0.0, 4.7), rotation=(0.0, math.pi / 2.0, 0.0))
    roof = bpy.context.active_object
    roof.name = "Natamandira_CurvedRoof"
    roof.scale = (0.55, 1.0, 1.0)
    roof.data.materials.append(mats["terracotta"])
    link_obj(roof, col)
    # West entry porch
    add_box("Natamandira_PorchRoof", (2.4, 4.2, 0.4), (nx - 5.2, 0.0, 3.4), mats["terracotta"], col)
    for py in (-1.6, 1.6):
        add_cylinder(f"Natamandira_PorchPillar_{py}", 0.22, 2.8, (nx - 6.0, py, 2.0), mats["stone_carved"], col, 10)

    return col


def build_saubhagya_kunda(mats):
    """Builds the sacred stepped rectangular tank Saubhagya Kunda with earthen diyas."""
    col = get_or_create_collection("Saubhagya_Kunda")
    # 5 stepped tiers descending into water
    for i in range(5):
        w = 18.0 - i * 1.4
        d = 14.0 - i * 1.4
        z = -0.35 * i
        # Four rim beams around opening
        t = 0.75
        add_box(f"Kunda_StepN_{i}", (w, t, 0.45), (0.0, d / 2 - t / 2, z), mats["stone_granite"], col)
        add_box(f"Kunda_StepS_{i}", (w, t, 0.45), (0.0, -d / 2 + t / 2, z), mats["stone_granite"], col)
        add_box(f"Kunda_StepE_{i}", (t, d, 0.45), (w / 2 - t / 2, 0.0, z), mats["stone_granite"], col)
        add_box(f"Kunda_StepW_{i}", (t, d, 0.45), (-w / 2 + t / 2, 0.0, z), mats["stone_granite"], col)

    # Water surface
    add_box("Kunda_Water", (12.6, 8.6, 0.15), (0.0, 0.0, -1.35), mats["water_kunda"], col)

    # Glowing earthen diyas along rim
    for i in range(-7, 8, 2):
        for sy in (-6.6, 6.6):
            add_cylinder(f"Diya_Rim_{i}_{sy}", 0.16, 0.09, (float(i), sy, 0.28), mats["diya_clay"], col, 10)
            bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=6, radius=0.09,
                                                 location=(float(i), sy, 0.38))
            fl = bpy.context.active_object
            fl.name = f"Diya_Flame_{i}_{sy}"
            fl.data.materials.append(mats["diya_flame"])
            link_obj(fl, col)
    return col


def build_torana_gate(mats):
    """Builds a carved stone entrance torana archway with hanging brass temple bells."""
    col = get_or_create_collection("Torana_Gate")
    for sx in (-2.4, 2.4):
        add_box(f"Torana_Base_{sx}", (1.1, 1.1, 0.8), (sx, 0.0, 0.4), mats["stone_granite"], col)
        add_box(f"Torana_Pillar_{sx}", (0.75, 0.75, 4.4), (sx, 0.0, 2.8), mats["stone_carved"], col)
    add_box("Torana_LintelLower", (6.2, 0.9, 0.55), (0.0, 0.0, 5.1), mats["stone_carved"], col)
    add_box("Torana_LintelUpper", (6.8, 1.1, 0.45), (0.0, 0.0, 5.7), mats["terracotta"], col)
    add_kalasha_finial("Torana_CenterFinial", (0.0, 0.0, 5.95), 0.5, mats, col)
    for bx in (-1.1, 0.0, 1.1):
        add_cylinder(f"Torana_BellChain_{bx}", 0.03, 0.7, (bx, 0.0, 4.5), mats["brass"], col, 6)
        bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.28, radius2=0.08, depth=0.45,
                                        location=(bx, 0.0, 4.0))
        bell = bpy.context.active_object
        bell.name = f"Torana_Bell_{bx}"
        bell.data.materials.append(mats["brass"])
        link_obj(bell, col)
    return col


def build_sub_shrine(mats):
    """Builds a reusable Nilachala-style Dasamahavidya / Shiva shrine."""
    col = get_or_create_collection("Sub_Shrine")
    add_box("Shrine_Plinth", (5.4, 5.4, 0.9), (0.0, 0.0, 0.45), mats["stone_granite"], col)
    add_box("Shrine_Sanctum", (4.2, 4.2, 3.2), (0.0, 0.0, 2.5), mats["plaster_cream"], col)
    add_box("Shrine_Cornice", (4.7, 4.7, 0.35), (0.0, 0.0, 4.25), mats["terracotta"], col)
    add_nilachala_dome("Shrine_Dome", 2.0, 4.0, (0.0, 0.0, 4.4), mats["vermilion"], col, 14, 10, True)
    add_kalasha_finial("Shrine_Finial", (0.0, 0.0, 8.4), 0.65, mats, col, with_trishul=True)
    return col


def build_nilachal_terrain(mats):
    """Builds the terraced Nilachal Hill landscape, stone courtyard, stairways & Brahmaputra River."""
    col = get_or_create_collection("Nilachal_Terrain")
    # Main stone courtyard platform around Kamakhya Temple & Saubhagya Kunda
    add_box("Courtyard_Main", (46.0, 38.0, 1.0), (-1.0, 6.0, -0.5), mats["stone_granite"], col)
    # Upper summit terrace for Bhuvaneshwari Temple (South-East high hill)
    add_box("Bhuvaneshwari_Summit", (18.0, 18.0, 8.0), (26.0, -24.0, 3.5), mats["hill_grass"], col)
    add_box("Bhuvaneshwari_Plaza", (14.0, 14.0, 0.5), (26.0, -24.0, 7.6), mats["stone_granite"], col)
    # Stone stairway up to Bhuvaneshwari Summit
    for s in range(16):
        t = s / 15.0
        add_box(f"Summit_Step_{s}", (4.2, 1.2, 0.5),
                (14.0 + t * 9.0, -10.0 - t * 8.0, t * 7.4), mats["stone_carved"], col)
    # Surrounding lush Nilachal hillside skirt
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=72.0, depth=14.0, location=(0.0, 0.0, -7.6))
    hill = bpy.context.active_object
    hill.name = "Nilachal_HillBase"
    hill.data.materials.append(mats["hill_grass"])
    link_obj(hill, col)
    # Brahmaputra River vista along northern slope (+Y)
    add_box("Brahmaputra_River", (220.0, 55.0, 0.4), (0.0, 82.0, -14.2), mats["water_river"], col)

    # Stylized Assamese banyan trees around perimeter
    tree_spots = [(-26, -12, 0), (-25, 22, 0), (24, 20, 0), (32, -16, 7.5), (18, -32, 7.5), (-18, -22, 0)]
    for idx, (tx, ty, tz) in enumerate(tree_spots):
        add_cylinder(f"Banyan_Trunk_{idx}", 0.55, 4.2, (tx, ty, tz + 2.1), mats["bark"], col, 10)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=3.4, location=(tx, ty, tz + 5.2))
        canopy = bpy.context.active_object
        canopy.name = f"Banyan_Canopy_{idx}"
        canopy.scale = (1.25, 1.25, 0.72)
        canopy.data.materials.append(mats["foliage"])
        link_obj(canopy, col)
    return col


def export_collection_glb(col_name, filename):
    bpy.ops.object.select_all(action="DESELECT")
    col = bpy.data.collections[col_name]
    for obj in col.objects:
        obj.select_set(True)
    out_path = os.path.join(EXPORT_DIR, filename)
    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format="GLB",
        use_selection=True,
        export_apply=True,
    )
    print(f"[Kamakhya Builder] Exported {out_path}")


def main():
    clear_scene()
    mats = create_materials()

    build_kamakhya_main_temple(mats)
    build_saubhagya_kunda(mats)
    build_torana_gate(mats)
    build_sub_shrine(mats)
    build_nilachal_terrain(mats)

    # Export each modular collection at local origin for clean Godot instancing
    export_collection_glb("Kamakhya_Temple", "kamakhya_temple.glb")
    export_collection_glb("Saubhagya_Kunda", "saubhagya_kunda.glb")
    export_collection_glb("Torana_Gate", "torana_gate.glb")
    export_collection_glb("Sub_Shrine", "sub_shrine.glb")
    export_collection_glb("Nilachal_Terrain", "nilachal_terrain.glb")

    # Arrange full assembled scene in the .blend file for Blender preview/rendering
    for obj in bpy.data.collections["Saubhagya_Kunda"].objects:
        obj.location.y += 15.5
    for obj in bpy.data.collections["Torana_Gate"].objects:
        obj.location.x -= 23.0
    for obj in bpy.data.collections["Sub_Shrine"].objects:
        obj.location += Vector((26.0, -24.0, 7.8))

    # Golden-hour sun & camera
    bpy.ops.object.light_add(type="SUN", location=(30, -30, 40), rotation=(0.8, 0.3, 0.6))
    bpy.context.active_object.data.energy = 3.5
    bpy.ops.object.camera_add(location=(-34, 34, 22), rotation=(1.1, 0.0, -2.35))
    bpy.context.scene.camera = bpy.context.active_object

    blend_path = os.path.join(SCRIPT_DIR, "kamakhya_kshetra.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"[Kamakhya Builder] Saved master scene to {blend_path}")


if __name__ == "__main__":
    main()
