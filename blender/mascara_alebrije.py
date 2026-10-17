"""Máscara de alebrije: modelado, textura y animación en Blender.

Uso (Blender 4.2+ / 5.x):
    blender --background --python blender/mascara_alebrije.py

Genera:
    blender/mascara_alebrije.blend   archivo fuente editable
    assets/mascara_alebrije.glb      modelo con animación para la web

Las medidas están en centímetros y en el espacio del modelo canónico de
MediaPipe (X derecha, Y arriba, Z hacia la cámara), así la máscara queda
alineada con la matriz de transformación facial sin ajustes extra.
"""
import math
import os

import bmesh
import bpy
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
FPS = 24
FRAMES = 48  # ciclo de 2 s

PALETA = np.array([
    (0.95, 0.10, 0.45),  # rosa mexicano
    (0.00, 0.70, 0.65),  # turquesa
    (1.00, 0.78, 0.00),  # amarillo
    (1.00, 0.35, 0.00),  # naranja
    (0.35, 0.80, 0.15),  # verde limón
    (0.45, 0.15, 0.75),  # morado
])


def C(x, y, z):
    """Coordenada canónica de MediaPipe (Y arriba) → Blender (Z arriba)."""
    return (x, -z, y)


# ---------------------------------------------------------------- escena
bpy.ops.wm.read_factory_settings(use_empty=True)
escena = bpy.context.scene
escena.render.fps = FPS
escena.frame_start = 1
escena.frame_end = FRAMES + 1


# ---------------------------------------------------------------- textura
def textura_alebrije(tam=1024):
    """Bandas en zigzag con contorno negro y puntos, al estilo de los alebrijes de Tilcajete."""
    v, u = np.mgrid[0:tam, 0:tam] / tam
    zig = np.abs(((u * 48) % 2) - 1) * 0.35       # diente de sierra → zigzag
    fila = v * 16 + zig
    banda = np.floor(fila).astype(int)
    color = PALETA[banda % len(PALETA)]
    # contorno negro entre bandas
    borde = np.abs(fila - np.round(fila)) < 0.06
    color[borde] = (0.05, 0.03, 0.05)
    # puntos de color contrastante en el centro de cada banda
    cu = (u * 48) % 1 - 0.5
    cv = (fila % 1) - 0.5
    punto = (cu ** 2 + cv ** 2) < 0.045
    color[punto] = PALETA[(banda[punto] + 3) % len(PALETA)]
    centro = (cu ** 2 + cv ** 2) < 0.012
    color[centro] = (1, 1, 1)
    rgba = np.concatenate([color, np.ones((tam, tam, 1))], axis=2)
    img = bpy.data.images.new("alebrije", tam, tam)
    img.pixels.foreach_set(rgba.astype(np.float32).ravel())
    img.pack()
    return img


IMG = textura_alebrije()


def material(nombre, color=None, textura=False, emision=0.0):
    m = bpy.data.materials.new(nombre)
    if hasattr(m, "use_nodes"):
        try:
            m.use_nodes = True
        except Exception:  # Blender 5 ya usa nodos siempre
            pass
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.45
    if textura:
        tex = m.node_tree.nodes.new("ShaderNodeTexImage")
        tex.image = IMG
        m.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    if color:
        bsdf.inputs["Base Color"].default_value = (*color, 1)
    if emision:
        bsdf.inputs["Emission Color"].default_value = (*color, 1)
        bsdf.inputs["Emission Strength"].default_value = emision
    return m


M_PIEL = material("piel_alebrije", textura=True)
M_BLANCO = material("blanco", (1, 1, 1))
M_NEGRO = material("negro", (0.02, 0.02, 0.02))
M_IRIS = material("iris", (1.0, 0.75, 0.0), emision=2.0)
M_CUERNO = material("cuerno", textura=True)
M_ROSA = material("rosa", tuple(PALETA[0]))
M_TURQUESA = material("turquesa", tuple(PALETA[1]))


def activar(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def asignar(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    bpy.ops.object.shade_smooth()


def pivote(nombre, loc, padre):
    e = bpy.data.objects.new(nombre, None)
    e.location = C(*loc)
    e.parent = padre
    bpy.context.collection.objects.link(e)
    return e


# ---------------------------------------------------------------- raíz
raiz = bpy.data.objects.new("Mascara", None)
bpy.context.collection.objects.link(raiz)

# ---------------------------------------------------------------- casco
# Elipsoide que cubre todo el rostro canónico (15.5 x 17.7 cm) con margen.
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=40, radius=1, location=C(0, -0.5, 1.5))
casco = bpy.context.active_object
casco.name = "Casco"
casco.scale = (9.2, 7.2, 11.2)  # (ancho, profundidad, alto) en ejes de Blender
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bm = bmesh.new()
bm.from_mesh(casco.data)
atras = [v for v in bm.verts if (casco.matrix_world @ v.co).y > -0.4]  # recorta la mitad trasera
bmesh.ops.delete(bm, geom=atras, context="VERTS")
bm.to_mesh(casco.data)
bm.free()
grosor = casco.modifiers.new("grosor", "SOLIDIFY")
grosor.thickness = 0.35
bpy.ops.object.modifier_apply(modifier="grosor")
asignar(casco, M_PIEL)
casco.parent = raiz

# ---------------------------------------------------------------- hocico
bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1, location=C(0, -2.2, 8.4))
hocico = bpy.context.active_object
hocico.name = "Hocico"
hocico.scale = (3.6, 2.4, 2.6)
asignar(hocico, M_TURQUESA)
hocico.parent = raiz
for x in (-1.2, 1.2):  # fosas nasales
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.45, location=C(x, -1.6, 10.6))
    fosa = bpy.context.active_object
    asignar(fosa, M_NEGRO)
    fosa.parent = raiz

# colmillos
for x in (-1.6, 1.6):
    bpy.ops.mesh.primitive_cone_add(radius1=0.45, depth=1.6, location=C(x, -4.9, 8.6), rotation=(math.pi, 0, 0))
    colmillo = bpy.context.active_object
    asignar(colmillo, M_BLANCO)
    colmillo.parent = raiz

# ---------------------------------------------------------------- ojos
ojos = []
for lado, x in (("Izq", -3.4), ("Der", 3.4)):
    piv = pivote(f"Ojo{lado}", (x, 2.9, 7.6), raiz)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1.7, location=(0, 0, 0))
    globo = bpy.context.active_object
    globo.name = f"Globo{lado}"
    globo.scale = (1, 0.6, 1)
    asignar(globo, M_BLANCO)
    globo.parent = piv
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=0.95, location=(0, -0.75, 0))
    iris = bpy.context.active_object
    iris.name = f"Iris{lado}"
    iris.scale = (1, 0.5, 1)
    asignar(iris, M_IRIS)
    iris.parent = piv
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.45, location=(0, -1.15, 0))
    pupila = bpy.context.active_object
    pupila.name = f"Pupila{lado}"
    pupila.scale = (0.6, 0.4, 1.2)  # pupila de reptil
    asignar(pupila, M_NEGRO)
    pupila.parent = piv
    ojos.append(piv)

# ---------------------------------------------------------------- orejas
orejas = []
for lado, s in (("Izq", -1), ("Der", 1)):
    piv = pivote(f"Oreja{lado}", (s * 7.0, 5.0, 3.0), raiz)
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=2.2, depth=6.5, location=(s * 2.6, 0, 1.8))
    oreja = bpy.context.active_object
    oreja.name = f"OrejaMalla{lado}"
    oreja.rotation_euler = (0, math.radians(s * 55), 0)
    oreja.scale = (1, 0.35, 1)
    asignar(oreja, M_ROSA)
    oreja.parent = piv
    orejas.append((piv, s))

# ---------------------------------------------------------------- cuernos (espiral de conos)
cuernos = []
for lado, s in (("Izq", -1), ("Der", 1)):
    piv = pivote(f"Cuerno{lado}", (s * 3.6, 9.4, 3.2), raiz)
    pos = [0.0, 0.0, 0.0]
    for i in range(6):
        r = 1.1 * (1 - i / 6.5)
        r2 = 1.1 * (1 - (i + 1) / 6.5)
        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=r, radius2=r2, depth=1.9, location=tuple(pos))
        seg = bpy.context.active_object
        seg.name = f"Cuerno{lado}{i}"
        ang = i * 0.35
        seg.rotation_euler = (math.radians(-8 * i), math.radians(s * (15 + 9 * i)), 0)
        asignar(seg, M_CUERNO)
        seg.parent = piv
        pos[0] += s * 0.45 * math.cos(ang)
        pos[2] += 0.95
        pos[1] += 0.18 * i
    cuernos.append((piv, s))

# ---------------------------------------------------------------- cresta
cresta = []
for i in range(5):
    z = 5.5 - i * 1.5
    y = -0.5 + 11.2 * math.sqrt(max(0.0, 1 - ((z - 1.5) / 7.2) ** 2))  # sobre la superficie del casco
    piv = pivote(f"Cresta{i}", (0, y, z), raiz)
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1.1 - i * 0.12, depth=3.2 - i * 0.3, location=(0, 0, 1.4))
    pua = bpy.context.active_object
    pua.name = f"Pua{i}"
    pua.scale = (0.35, 1, 1)
    asignar(pua, M_TURQUESA if i % 2 else M_ROSA)
    pua.parent = piv
    cresta.append(piv)


# ---------------------------------------------------------------- animación
def clave(obj, frame, rot=None, esc=None):
    if rot is not None:
        obj.rotation_euler = rot
        obj.keyframe_insert("rotation_euler", frame=frame)
    if esc is not None:
        obj.scale = esc
        obj.keyframe_insert("scale", frame=frame)


for f in range(1, FRAMES + 2, 4):
    t = (f - 1) / FRAMES * 2 * math.pi
    for piv, s in orejas:   # aleteo de orejas
        clave(piv, f, rot=(0, s * math.radians(14) * math.sin(t), s * math.radians(8) * math.sin(t + 1)))
    for piv, s in cuernos:  # vaivén de cuernos
        clave(piv, f, rot=(math.radians(5) * math.sin(t), 0, s * math.radians(6) * math.sin(t)))
    for i, piv in enumerate(cresta):  # ola en la cresta
        clave(piv, f, rot=(math.radians(18) * math.sin(t - i * 0.9), 0, 0))
    for piv in ojos:  # ojos que miran de lado a lado
        clave(piv, f, rot=(0, 0, math.radians(12) * math.sin(t)))

# parpadeo rápido a mitad del ciclo
for piv in ojos:
    for f, sy in ((1, 1), (28, 1), (31, 0.1), (34, 1), (FRAMES + 1, 1)):
        clave(piv, f, esc=(1, 1, sy))

# respiración del hocico
for f in range(1, FRAMES + 2, 6):
    t = (f - 1) / FRAMES * 2 * math.pi
    clave(hocico, f, esc=(3.6 * (1 + 0.04 * math.sin(t * 2)), 2.4, 2.6 * (1 + 0.04 * math.sin(t * 2))))

# ---------------------------------------------------------------- exportar
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(AQUI, "mascara_alebrije.blend"), compress=True)
os.makedirs(os.path.join(RAIZ, "assets"), exist_ok=True)
bpy.ops.export_scene.gltf(
    filepath=os.path.join(RAIZ, "assets", "mascara_alebrije.glb"),
    export_format="GLB",
    export_animations=True,
    export_animation_mode="SCENE",
    export_force_sampling=True,
    export_yup=True,
)
print("OK mascara_alebrije exportada")
