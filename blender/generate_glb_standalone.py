"""
Standalone Pure-Python glTF 2.0 (.glb) Generator for Kamakhya Kshetra
=====================================================================
Generates ready-to-import binary .glb 3D assets directly into
`godot/assets/models/` using only the Python standard library (zero Blender
dependency required), matching the exact geometry, scale, and PBR materials
of `build_kamakhya_kshetra.py` (converted to glTF Y-up convention for Godot 4).
"""

import json
import math
import os
import struct

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "godot", "assets", "models"))
os.makedirs(EXPORT_DIR, exist_ok=True)


class GLBBuilder:
    def __init__(self):
        self.materials = []
        self.mat_map = {}
        self.primitives = []  # list of (mat_idx, positions, normals, indices)

    def add_material(self, name, color, roughness=0.78, metallic=0.0, emissive=None):
        if name in self.mat_map:
            return self.mat_map[name]
        mat = {
            "name": name,
            "pbrMetallicRoughness": {
                "baseColorFactor": [color[0], color[1], color[2], 1.0],
                "metallicFactor": metallic,
                "roughnessFactor": roughness,
            },
            "doubleSided": True,
        }
        if emissive is not None:
            mat["emissiveFactor"] = list(emissive)
        idx = len(self.materials)
        self.materials.append(mat)
        self.mat_map[name] = idx
        return idx

    def _add_mesh(self, mat_idx, verts, tris):
        """verts: list of (x,y,z), tris: list of (i0,i1,i2). Computes flat/smooth normals."""
        positions = []
        normals = []
        indices = []
        for (i0, i1, i2) in tris:
            v0, v1, v2 = verts[i0], verts[i1], verts[i2]
            e1 = (v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2])
            e2 = (v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2])
            nx = e1[1] * e2[2] - e1[2] * e2[1]
            ny = e1[2] * e2[0] - e1[0] * e2[2]
            nz = e1[0] * e2[1] - e1[1] * e2[0]
            l = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            n = (nx / l, ny / l, nz / l)
            base = len(positions)
            positions.extend([v0, v1, v2])
            normals.extend([n, n, n])
            indices.extend([base, base + 1, base + 2])
        self.primitives.append((mat_idx, positions, normals, indices))

    def add_box(self, size, center, mat_idx):
        sx, sy, sz = size[0] * 0.5, size[1] * 0.5, size[2] * 0.5
        cx, cy, cz = center
        v = [
            (cx - sx, cy - sy, cz - sz), (cx + sx, cy - sy, cz - sz),
            (cx + sx, cy + sy, cz - sz), (cx - sx, cy + sy, cz - sz),
            (cx - sx, cy - sy, cz + sz), (cx + sx, cy - sy, cz + sz),
            (cx + sx, cy + sy, cz + sz), (cx - sx, cy + sy, cz + sz),
        ]
        tris = [
            (0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
            (0, 1, 5), (0, 5, 4), (2, 3, 7), (2, 7, 6),
            (0, 4, 7), (0, 7, 3), (1, 2, 6), (1, 6, 5),
        ]
        self._add_mesh(mat_idx, v, tris)

    def add_cylinder(self, radius_bottom, radius_top, height, center, mat_idx, segs=14):
        cx, cy, cz = center
        y0, y1 = cy - height * 0.5, cy + height * 0.5
        verts = []
        for s in range(segs):
            a = 2.0 * math.pi * s / segs
            verts.append((cx + radius_bottom * math.cos(a), y0, cz + radius_bottom * math.sin(a)))
        for s in range(segs):
            a = 2.0 * math.pi * s / segs
            verts.append((cx + radius_top * math.cos(a), y1, cz + radius_top * math.sin(a)))
        bot_c = len(verts); verts.append((cx, y0, cz))
        top_c = len(verts); verts.append((cx, y1, cz))
        tris = []
        for s in range(segs):
            sn = (s + 1) % segs
            tris.append((s, sn, segs + sn))
            tris.append((s, segs + sn, segs + s))
            tris.append((bot_c, sn, s))
            tris.append((top_c, segs + s, segs + sn))
        self._add_mesh(mat_idx, verts, tris)

    def add_nilachala_dome(self, radius, height, base_center, mat_idx, segs=16, rings=12, ribbed=True):
        cx, cy, cz = base_center
        verts = []
        for r in range(rings + 1):
            t = r / rings
            taper = (1.0 - t) ** 0.58
            rad = radius * (0.28 + 0.72 * taper) * (1.0 + 0.12 * math.sin(t * math.pi))
            if ribbed and 0 < r < rings:
                rad *= 1.0 + 0.03 * math.sin(r * math.pi)
            if r == rings:
                rad = radius * 0.12
            y = cy + t * height
            for s in range(segs):
                a = 2.0 * math.pi * s / segs
                verts.append((cx + rad * math.cos(a), y, cz + rad * math.sin(a)))
        apex = len(verts)
        verts.append((cx, cy + height * 1.03, cz))
        tris = []
        for r in range(rings):
            for s in range(segs):
                sn = (s + 1) % segs
                a0 = r * segs + s
                a1 = r * segs + sn
                b0 = (r + 1) * segs + s
                b1 = (r + 1) * segs + sn
                tris.append((a0, b1, a1))
                tris.append((a0, b0, b1))
        for s in range(segs):
            sn = (s + 1) % segs
            tris.append((rings * segs + s, apex, rings * segs + sn))
        self._add_mesh(mat_idx, verts, tris)

    def add_kalasha(self, base_center, scale, gold_idx, trishul=False):
        cx, cy, cz = base_center
        self.add_cylinder(0.55 * scale, 0.55 * scale, 0.28 * scale, (cx, cy + 0.14 * scale, cz), gold_idx, 12)
        self.add_cylinder(0.32 * scale, 0.28 * scale, 0.5 * scale, (cx, cy + 0.52 * scale, cz), gold_idx, 12)
        self.add_cylinder(0.24 * scale, 0.03 * scale, 0.9 * scale, (cx, cy + 1.2 * scale, cz), gold_idx, 10)
        if trishul:
            self.add_cylinder(0.05 * scale, 0.04 * scale, 1.4 * scale, (cx, cy + 2.1 * scale, cz), gold_idx, 8)
            self.add_box((0.55 * scale, 0.08 * scale, 0.08 * scale), (cx, cy + 2.55 * scale, cz), gold_idx)
            for side in (-1, 1):
                self.add_box((0.07 * scale, 0.5 * scale, 0.07 * scale),
                             (cx + side * 0.25 * scale, cy + 2.8 * scale, cz), gold_idx)

    def save(self, filepath):
        # Merge primitives by material for compact glTF
        grouped = {}
        for mat_idx, pos, norm, idx in self.primitives:
            if mat_idx not in grouped:
                grouped[mat_idx] = ([], [], [])
            gp, gn, gi = grouped[mat_idx]
            offset = len(gp)
            gp.extend(pos)
            gn.extend(norm)
            gi.extend([i + offset for i in idx])

        bin_chunks = bytearray()
        buffer_views = []
        accessors = []
        gltf_prims = []

        def add_view(raw_bytes, target):
            while len(bin_chunks) % 4 != 0:
                bin_chunks.append(0)
            offset = len(bin_chunks)
            bin_chunks.extend(raw_bytes)
            bv_idx = len(buffer_views)
            buffer_views.append({
                "buffer": 0,
                "byteOffset": offset,
                "byteLength": len(raw_bytes),
                "target": target,
            })
            return bv_idx

        for mat_idx, (gp, gn, gi) in grouped.items():
            pos_bytes = b"".join(struct.pack("<fff", *p) for p in gp)
            norm_bytes = b"".join(struct.pack("<fff", *n) for n in gn)
            idx_bytes = b"".join(struct.pack("<I", i) for i in gi)

            p_min = [min(p[k] for p in gp) for k in range(3)]
            p_max = [max(p[k] for p in gp) for k in range(3)]

            bv_pos = add_view(pos_bytes, 34962)
            bv_norm = add_view(norm_bytes, 34962)
            bv_idx = add_view(idx_bytes, 34963)

            acc_pos = len(accessors)
            accessors.append({
                "bufferView": bv_pos, "componentType": 5126, "count": len(gp),
                "type": "VEC3", "min": p_min, "max": p_max,
            })
            acc_norm = len(accessors)
            accessors.append({
                "bufferView": bv_norm, "componentType": 5126, "count": len(gn), "type": "VEC3",
            })
            acc_idx = len(accessors)
            accessors.append({
                "bufferView": bv_idx, "componentType": 5125, "count": len(gi), "type": "SCALAR",
            })
            gltf_prims.append({
                "attributes": {"POSITION": acc_pos, "NORMAL": acc_norm},
                "indices": acc_idx,
                "material": mat_idx,
            })

        gltf = {
            "asset": {"version": "2.0", "generator": "KamakhyaKshetraBuilder"},
            "scene": 0,
            "scenes": [{"nodes": [0]}],
            "nodes": [{"mesh": 0, "name": os.path.splitext(os.path.basename(filepath))[0]}],
            "meshes": [{"primitives": gltf_prims}],
            "materials": self.materials,
            "buffers": [{"byteLength": len(bin_chunks)}],
            "bufferViews": buffer_views,
            "accessors": accessors,
        }
        json_bytes = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
        while len(json_bytes) % 4 != 0:
            json_bytes += b" "
        while len(bin_chunks) % 4 != 0:
            bin_chunks.append(0)

        total_len = 12 + 8 + len(json_bytes) + 8 + len(bin_chunks)
        with open(filepath, "wb") as f:
            f.write(struct.pack("<III", 0x46546C67, 2, total_len))
            f.write(struct.pack("<II", len(json_bytes), 0x4E4F534A))
            f.write(json_bytes)
            f.write(struct.pack("<II", len(bin_chunks), 0x004E4942))
            f.write(bin_chunks)
        print(f"Generated {filepath} ({total_len / 1024:.1f} KB)")


def add_palette(b):
    return {
        "granite": b.add_material("Stone_Granite", (0.42, 0.39, 0.36), 0.88),
        "carved": b.add_material("Stone_Carved", (0.52, 0.47, 0.41), 0.82),
        "cream": b.add_material("Plaster_Cream", (0.86, 0.80, 0.70), 0.78),
        "terracotta": b.add_material("Terracotta_Red", (0.64, 0.24, 0.14), 0.72),
        "vermilion": b.add_material("Vermilion_Ochre", (0.76, 0.28, 0.15), 0.68),
        "gold": b.add_material("Gold_Kalasha", (0.95, 0.76, 0.24), 0.22, 0.95),
        "brass": b.add_material("Brass_Bell", (0.78, 0.58, 0.22), 0.32, 0.88),
        "kunda": b.add_material("Water_Saubhagya", (0.06, 0.19, 0.20), 0.08, 0.15),
        "river": b.add_material("Water_Brahmaputra", (0.14, 0.27, 0.34), 0.15, 0.10),
        "grass": b.add_material("Nilachal_Grass", (0.16, 0.31, 0.13), 0.92),
        "foliage": b.add_material("Tropical_Foliage", (0.11, 0.27, 0.09), 0.85),
        "bark": b.add_material("Tree_Bark", (0.24, 0.17, 0.12), 0.92),
        "clay": b.add_material("Diya_Clay", (0.52, 0.25, 0.14), 0.85),
        "flame": b.add_material("Diya_Flame", (1.0, 0.75, 0.25), 0.2, 0.0, emissive=(1.0, 0.65, 0.15)),
    }


def generate_all():
    # 1. Main Kamakhya Temple (Y-up: X=East/West, Y=Height, Z=North/South)
    b = GLBBuilder()
    m = add_palette(b)
    gx = 9.0
    b.add_box((9.4, 1.4, 9.4), (gx, 0.7, 0.0), m["granite"])
    b.add_box((7.6, 5.2, 7.6), (gx, 4.0, 0.0), m["carved"])
    b.add_box((8.6, 5.0, 4.4), (gx, 3.9, 0.0), m["carved"])
    b.add_box((4.4, 5.0, 8.6), (gx, 3.9, 0.0), m["carved"])
    b.add_nilachala_dome(4.1, 8.8, (gx, 6.5, 0.0), m["terracotta"], 16, 14, True)
    b.add_kalasha((gx, 15.3, 0.0), 1.25, m["gold"], trishul=True)
    for i in range(12):
        a = 2.0 * math.pi * i / 12.0
        ax, az = gx + 3.95 * math.cos(a), 3.95 * math.sin(a)
        b.add_cylinder(0.55, 0.55, 1.5, (ax, 7.25, az), m["carved"], 10)
        b.add_nilachala_dome(0.62, 2.3, (ax, 8.0, az), m["vermilion"], 10, 8, False)
        b.add_kalasha((ax, 10.3, az), 0.32, m["gold"])

    # Calanta
    cx = 1.5
    b.add_box((6.2, 1.2, 7.4), (cx, 0.6, 0.0), m["granite"])
    b.add_box((6.0, 0.6, 7.0), (cx, 4.8, 0.0), m["terracotta"])
    for px in (-2.2, -0.75, 0.75, 2.2):
        for pz in (-2.8, 0.0, 2.8):
            if abs(px) < 1.5 and abs(pz) < 1.0:
                continue
            b.add_cylinder(0.24, 0.24, 3.6, (cx + px, 3.0, pz), m["carved"], 10)
    b.add_nilachala_dome(2.3, 4.2, (cx, 5.1, 0.0), m["vermilion"], 14, 10, False)
    b.add_kalasha((cx, 9.3, 0.0), 0.72, m["gold"])

    # Pancharatna
    px0 = -5.2
    b.add_box((7.4, 1.2, 7.8), (px0, 0.6, 0.0), m["granite"])
    b.add_box((7.0, 4.4, 7.2), (px0, 3.4, 0.0), m["cream"])
    b.add_box((7.5, 0.5, 7.7), (px0, 5.7, 0.0), m["terracotta"])
    b.add_nilachala_dome(2.4, 4.8, (px0, 5.95, 0.0), m["terracotta"], 14, 10, True)
    b.add_kalasha((px0, 10.75, 0.0), 0.75, m["gold"])
    for dx in (-2.4, 2.4):
        for dz in (-2.5, 2.5):
            b.add_nilachala_dome(1.15, 2.7, (px0 + dx, 5.95, dz), m["vermilion"], 12, 8, False)
            b.add_kalasha((px0 + dx, 8.65, dz), 0.4, m["gold"])

    # Natamandira
    nx = -13.2
    b.add_box((9.0, 1.1, 7.6), (nx, 0.55, 0.0), m["granite"])
    b.add_box((8.6, 3.6, 7.0), (nx, 2.9, 0.0), m["cream"])
    # Stepped curved apsidal roof approximation
    for k in range(5):
        frac = k / 4.0
        rw = 8.9 - frac * 1.4
        rd = 7.4 * math.cos(frac * 1.15)
        b.add_box((rw, 0.42, rd), (nx, 4.85 + k * 0.36, 0.0), m["terracotta"])
    b.add_box((2.4, 0.4, 4.2), (nx - 5.2, 3.4, 0.0), m["terracotta"])
    for pz in (-1.6, 1.6):
        b.add_cylinder(0.22, 0.22, 2.8, (nx - 6.0, 2.0, pz), m["carved"], 10)
    b.save(os.path.join(EXPORT_DIR, "kamakhya_temple.glb"))

    # 2. Saubhagya Kunda
    b = GLBBuilder()
    m = add_palette(b)
    for i in range(5):
        w, d, y = 18.0 - i * 1.4, 14.0 - i * 1.4, -0.35 * i
        t = 0.75
        b.add_box((w, 0.45, t), (0.0, y, d / 2 - t / 2), m["granite"])
        b.add_box((w, 0.45, t), (0.0, y, -d / 2 + t / 2), m["granite"])
        b.add_box((t, 0.45, d), (w / 2 - t / 2, y, 0.0), m["granite"])
        b.add_box((t, 0.45, d), (-w / 2 + t / 2, y, 0.0), m["granite"])
    b.add_box((12.6, 0.15, 8.6), (0.0, -1.35, 0.0), m["kunda"])
    for i in range(-7, 8, 2):
        for sz in (-6.6, 6.6):
            b.add_cylinder(0.16, 0.14, 0.09, (float(i), 0.28, sz), m["clay"], 8)
            b.add_cylinder(0.08, 0.01, 0.16, (float(i), 0.40, sz), m["flame"], 8)
    b.save(os.path.join(EXPORT_DIR, "saubhagya_kunda.glb"))

    # 3. Torana Gate
    b = GLBBuilder()
    m = add_palette(b)
    for sx in (-2.4, 2.4):
        b.add_box((1.1, 0.8, 1.1), (sx, 0.4, 0.0), m["granite"])
        b.add_box((0.75, 4.4, 0.75), (sx, 2.8, 0.0), m["carved"])
    b.add_box((6.2, 0.55, 0.9), (0.0, 5.1, 0.0), m["carved"])
    b.add_box((6.8, 0.45, 1.1), (0.0, 5.7, 0.0), m["terracotta"])
    b.add_kalasha((0.0, 5.95, 0.0), 0.5, m["gold"])
    for bx in (-1.1, 0.0, 1.1):
        b.add_cylinder(0.03, 0.03, 0.7, (bx, 4.5, 0.0), m["brass"], 6)
        b.add_cylinder(0.28, 0.08, 0.45, (bx, 4.0, 0.0), m["brass"], 10)
    b.save(os.path.join(EXPORT_DIR, "torana_gate.glb"))

    # 4. Sub Shrine (Bhuvaneshwari / Tara / Kameshwara / Bagalamukhi)
    b = GLBBuilder()
    m = add_palette(b)
    b.add_box((5.4, 0.9, 5.4), (0.0, 0.45, 0.0), m["granite"])
    b.add_box((4.2, 3.2, 4.2), (0.0, 2.5, 0.0), m["cream"])
    b.add_box((4.7, 0.35, 4.7), (0.0, 4.25, 0.0), m["terracotta"])
    b.add_nilachala_dome(2.0, 4.0, (0.0, 4.4, 0.0), m["vermilion"], 14, 10, True)
    b.add_kalasha((0.0, 8.4, 0.0), 0.65, m["gold"], trishul=True)
    b.save(os.path.join(EXPORT_DIR, "sub_shrine.glb"))

    # 5. Nilachal Hill Terrain & Brahmaputra River
    b = GLBBuilder()
    m = add_palette(b)
    b.add_box((46.0, 1.0, 38.0), (-1.0, -0.5, -6.0), m["granite"])
    b.add_box((18.0, 8.0, 18.0), (26.0, 3.5, 24.0), m["grass"])
    b.add_box((14.0, 0.5, 14.0), (26.0, 7.6, 24.0), m["granite"])
    for s in range(16):
        t = s / 15.0
        b.add_box((4.2, 0.5, 1.2), (14.0 + t * 9.0, t * 7.4, 10.0 + t * 8.0), m["carved"])
    b.add_cylinder(76.0, 66.0, 14.0, (0.0, -7.6, 0.0), m["grass"], 24)
    b.add_box((220.0, 0.4, 55.0), (0.0, -14.2, -82.0), m["river"])
    for (tx, ty, tz) in [(-26, 0, 12), (-25, 0, -22), (24, 0, -20), (32, 7.5, 16), (18, 7.5, 32), (-18, 0, 22)]:
        b.add_cylinder(0.55, 0.4, 4.2, (tx, ty + 2.1, tz), m["bark"], 8)
        b.add_cylinder(3.6, 2.2, 3.0, (tx, ty + 5.2, tz), m["foliage"], 10)
    b.save(os.path.join(EXPORT_DIR, "nilachal_terrain.glb"))

    # 6. Sanctum Interior: Garbhagriha Yoni Peetha (authentic non-iconic rock fissure + spring)
    #    & Calanta Simhasana with Utsava Murti of Devi Kameshwari (Kamakhya)
    b = GLBBuilder()
    m = add_palette(b)
    silk_red = b.add_material("Rakta_Vastra_Silk", (0.78, 0.08, 0.10), 0.55)
    sindoor = b.add_material("Sindoor_Vermilion", (0.92, 0.16, 0.08), 0.65)
    basalt = b.add_material("Sacred_Basalt", (0.20, 0.19, 0.21), 0.72)
    spring = b.add_material("Natural_Spring", (0.12, 0.36, 0.42), 0.06, 0.25)

    # A) Garbhagriha Cave Sanctum (centered at X = +9.0)
    gx = 9.0
    # Descending stone steps into cave floor
    for s in range(4):
        b.add_box((2.4, 0.25, 0.55), (gx - 2.6 + s * 0.4, 1.15 - s * 0.22, 0.0), m["granite"])
    # Sacred Yoni Peetha natural basalt rock base & recessed spring basin
    b.add_cylinder(1.55, 1.35, 0.55, (gx + 0.3, 0.45, 0.0), basalt, 16)
    b.add_cylinder(1.05, 0.92, 0.18, (gx + 0.3, 0.78, 0.0), spring, 16)
    # Red silk drape (Rakta Vastra) & vermilion/hibiscus offerings around the Peetha
    b.add_box((1.35, 0.12, 0.95), (gx + 0.65, 0.86, 0.0), silk_red)
    for i in range(8):
        a = 2.0 * math.pi * i / 8.0
        b.add_cylinder(0.14, 0.08, 0.10, (gx + 0.3 + 1.15 * math.cos(a), 0.80, 1.15 * math.sin(a)), sindoor, 8)
        b.add_cylinder(0.11, 0.09, 0.07, (gx + 0.3 + 1.48 * math.cos(a), 0.76, 1.48 * math.sin(a)), m["clay"], 8)
        b.add_cylinder(0.06, 0.01, 0.14, (gx + 0.3 + 1.48 * math.cos(a), 0.88, 1.48 * math.sin(a)), m["flame"], 6)

    # B) Calanta Hall Simhasana & Utsava Murti of Devi Kameshwari (centered at X = +1.5)
    cx = 1.5
    # Stepped lotus pedestal (Simhasana)
    b.add_box((2.1, 0.45, 1.6), (cx, 1.42, 0.0), m["carved"])
    b.add_cylinder(0.68, 0.58, 0.28, (cx, 1.78, 0.0), m["gold"], 14)
    # Ornate golden Prabhavali (halo arch behind the murti)
    b.add_box((0.12, 1.85, 1.35), (cx + 0.42, 2.72, 0.0), m["gold"])
    b.add_cylinder(0.72, 0.68, 0.14, (cx + 0.36, 3.35, 0.0), m["gold"], 14)
    # Stylized seated gilded Devi Kameshwari Utsava Murti (base, torso, red sari drape, crown/mukuta)
    b.add_cylinder(0.42, 0.32, 0.36, (cx, 2.10, 0.0), silk_red, 12)     # seated lotus posture in rakta vastra
    b.add_cylinder(0.24, 0.20, 0.58, (cx, 2.55, 0.0), m["gold"], 12)    # torso
    b.add_cylinder(0.16, 0.16, 0.28, (cx, 3.00, 0.0), m["gold"], 12)    # head
    b.add_cylinder(0.18, 0.03, 0.42, (cx, 3.34, 0.0), m["gold"], 10)    # conical mukuta crown
    # Flanking brass oil lamps (deepastambha)
    for dz in (-0.95, 0.95):
        b.add_cylinder(0.18, 0.07, 1.05, (cx - 0.35, 1.95, dz), m["brass"], 10)
        b.add_cylinder(0.08, 0.01, 0.18, (cx - 0.35, 2.56, dz), m["flame"], 6)

    b.save(os.path.join(EXPORT_DIR, "sanctum_interior.glb"))


if __name__ == "__main__":
    generate_all()
