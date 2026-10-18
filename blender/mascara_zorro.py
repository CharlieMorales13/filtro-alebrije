"""Máscara de zorro de fiesta: ajuste a la cara, esqueleto y animación en Blender.

Uso (Blender 4.2+ / 5.x):
    blender --background --python blender/mascara_zorro.py -- <zorro_meshy.glb>

La base es un modelo generado con Meshy a partir de un prompt propio (zorro
de fiesta con pintura de alebrije, plumas y flecos de listón). Este script:
    1. reduce la malla (200 k → ~40 k caras) y las texturas (2048 → 1024),
    2. la escala y la coloca en el espacio del modelo canónico de MediaPipe
       (cm; X derecha, Y arriba, Z hacia la cámara) con los huecos de los
       ojos sobre los ojos del usuario,
    3. le crea un esqueleto (plumas, orejas y flecos) con pesos suaves,
    4. anima un ciclo de 2 s (flecos que se mecen, plumas y orejas) y
    5. guarda blender/mascara_zorro.blend y assets/mascara_zorro.glb.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
FUENTE = sys.argv[sys.argv.index("--") + 1]
FPS = 24
FRAMES = 48  # ciclo de 2 s

# Medidas de la máscara original (unidades de Meshy, vista de frente X/Z),
# tomadas de su silueta: centro de los huecos de los ojos.
OJO_X, OJO_Z = 0.164, 0.158
# Modelo canónico de MediaPipe: centro de los ojos (landmarks 33/133/159/145).
CANON_OJO_X, CANON_OJO_Y = 3.16, 2.63
ESCALA = CANON_OJO_X / OJO_X          # ≈ 19.3 cm por unidad de Meshy
DZ = CANON_OJO_Y - OJO_Z * ESCALA
BORDE_OJOS_Z = 4.8                     # el reverso de la máscara queda 1 cm frente a los ojos

bpy.ops.wm.read_factory_settings(use_empty=True)
escena = bpy.context.scene
escena.render.fps = FPS
escena.frame_start = 1
escena.frame_end = FRAMES + 1

bpy.ops.import_scene.gltf(filepath=FUENTE)
malla = next(o for o in bpy.data.objects if o.type == "MESH")
malla.name = "Mascara"
bpy.context.view_layer.objects.active = malla
malla.select_set(True)

# ---------------------------------------------------------------- optimizar
dec = malla.modifiers.new("reducir", "DECIMATE")
dec.ratio = 0.2
bpy.ops.object.modifier_apply(modifier="reducir")
for img in bpy.data.images:
    if img.size[0] > 1024:
        img.scale(1024, 1024)
        img.pack()
mat = malla.data.materials[0]
mat.name = "piel"  # main.js lo busca por nombre para teñirlo y hacerlo brillar

# ---------------------------------------------------------------- ajustar a la cara
# Meshy mira hacia -Y de Blender, igual que +Z del canónico: solo escala y traslación.
cerca_ojos = [v.co.y for v in malla.data.vertices
              if 0.1 < abs(v.co.x) < 0.26 and 0.06 < v.co.z < 0.26]
dy = -BORDE_OJOS_Z - max(cerca_ojos) * ESCALA
for v in malla.data.vertices:
    v.co = Vector((v.co.x * ESCALA, v.co.y * ESCALA + dy, v.co.z * ESCALA + DZ))
malla.data.update()


def M(x, z):
    """Punto de la vista frontal de Meshy → coordenadas de Blender ya escaladas."""
    return x * ESCALA, z * ESCALA + DZ


def suave(a, b, t):
    t = min(1.0, max(0.0, (t - a) / (b - a)))
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- esqueleto
# (nombre, cabeza, cola, peso(x, z) en unidades de Meshy)
_, Z_PLUMAS = M(0, 0.6)
HUESOS = [
    ("plumas", (M(0.06, 0.6)[0], 1.0, Z_PLUMAS), (M(0.06, 0.9)[0], 1.0, M(0, 0.9)[1]),
     lambda x, z: max(suave(0.62, 0.72, z) * (1 - suave(0.2, 0.28, abs(x - 0.06))), suave(0.79, 0.84, z))),
]
for lado, s in (("izq", -1), ("der", 1)):
    HUESOS += [
        (f"oreja_{lado}", (M(s * 0.33, 0.48)[0], 0, M(0, 0.48)[1]), (M(s * 0.42, 0.75)[0], 0, M(0, 0.75)[1]),
         lambda x, z, s=s: suave(0.5, 0.62, z) * suave(0.18, 0.26, s * x) * (1 - suave(0.79, 0.84, z))),
        (f"fleco_{lado}", (M(s * 0.5, 0.3)[0], 1.0, M(0, 0.3)[1]), (M(s * 0.55, -0.5)[0], 1.0, M(0, -0.5)[1]),
         lambda x, z, s=s: suave(0.5, 0.62, s * x) * suave(0.3, -0.3, z)),
        (f"barba_{lado}", (M(s * 0.12, -0.32)[0], 1.0, M(0, -0.32)[1]), (M(s * 0.15, -0.9)[0], 1.0, M(0, -0.9)[1]),
         lambda x, z, s=s: suave(-0.32, -0.85, z) * suave(-0.05, 0.08, s * x) * (1 - suave(0.45, 0.55, abs(x)))),
    ]

# pesos: cada vértice reparte 1.0 entre su hueso y la raíz
pesos_por_vertice = []
profundidad = {n: [] for n, *_ in HUESOS}
for v in malla.data.vertices:
    x, z = v.co.x / ESCALA, (v.co.z - DZ) / ESCALA
    pesos = {n: f(x, z) for n, _, _, f in HUESOS}
    total = sum(pesos.values())
    if total > 1:
        pesos = {n: p / total for n, p in pesos.items()}
    pesos_por_vertice.append((pesos, total))
    for n, p in pesos.items():
        if p > 0.3:
            profundidad[n].append(v.co.y)

datos = bpy.data.armatures.new("Esqueleto")
esqueleto = bpy.data.objects.new("Esqueleto", datos)
escena.collection.objects.link(esqueleto)
bpy.ops.object.select_all(action="DESELECT")
bpy.context.view_layer.objects.active = esqueleto
bpy.ops.object.mode_set(mode="EDIT")
raiz = datos.edit_bones.new("raiz")
raiz.head, raiz.tail = (0, 0, 0), (0, 0, 4)
for nombre, cabeza, cola, _ in HUESOS:
    y = sum(profundidad[nombre]) / max(1, len(profundidad[nombre]))  # pivote a la profundidad de su zona
    h = datos.edit_bones.new(nombre)
    h.head, h.tail, h.parent = (cabeza[0], y, cabeza[2]), (cola[0], y, cola[2]), raiz
bpy.ops.object.mode_set(mode="OBJECT")

grupos = {n: malla.vertex_groups.new(name=n) for n in ["raiz"] + [h[0] for h in HUESOS]}
for v, (pesos, total) in zip(malla.data.vertices, pesos_por_vertice):
    for n, p in pesos.items():
        if p > 0.01:
            grupos[n].add([v.index], p, "REPLACE")
    grupos["raiz"].add([v.index], max(0.0, 1 - min(1.0, total)), "REPLACE")
malla.parent = esqueleto
malla.modifiers.new("esqueleto", "ARMATURE").object = esqueleto

# ---------------------------------------------------------------- animación
# Ciclo de 2 s: los flecos se mecen como péndulos desfasados, las plumas
# ondean y las orejas dan un tirón a mitad del ciclo.
AMPLITUD = {"plumas": (14, 8), "fleco": (12, 14), "barba": (14, 8), "oreja": (10, 8)}
FASE = {"plumas": 0, "fleco_izq": 0.6, "fleco_der": 2.2, "barba_izq": 1.4, "barba_der": 3.0,
        "oreja_izq": 0, "oreja_der": 0.5}
for hueso in esqueleto.pose.bones:
    hueso.rotation_mode = "XYZ"
for f in range(1, FRAMES + 2, 2):
    t = (f - 1) / FRAMES * 2 * math.pi
    for hueso in esqueleto.pose.bones:
        if hueso.name == "raiz":
            continue
        ax, az = AMPLITUD[hueso.name.split("_")[0]]
        fase = FASE[hueso.name]
        if hueso.name.startswith("oreja"):  # tirón rápido de las orejas
            tiron = math.exp(-((f - 30) / 3) ** 2)
            hueso.rotation_euler = (math.radians(ax * tiron), 0, math.radians(az * tiron) * (1 if "der" in hueso.name else -1))
        else:
            hueso.rotation_euler = (math.radians(ax) * math.sin(t + fase), 0, math.radians(az) * math.sin(2 * t + fase))
        hueso.keyframe_insert("rotation_euler", frame=f)

# ---------------------------------------------------------------- exportar
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(AQUI, "mascara_zorro.blend"), compress=True)
os.makedirs(os.path.join(RAIZ, "assets"), exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=os.path.join(RAIZ, "assets", "mascara_zorro.glb"),
    export_format="GLB",
    export_animations=True,
    export_animation_mode="SCENE",
    export_force_sampling=True,
    export_image_format="JPEG",
    export_jpeg_quality=85,
    export_yup=True,
)
print("OK mascara_zorro exportada", os.path.getsize(os.path.join(RAIZ, "assets", "mascara_zorro.glb")) // 1024, "KB")
