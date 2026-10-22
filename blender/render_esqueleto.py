"""Renderiza la máscara del zorro con su esqueleto visible (huesos como varillas de color)."""
import sys, math
import bpy, bmesh
from mathutils import Vector

salida = sys.argv[sys.argv.index("--") + 1]
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
mallas = [o for o in bpy.data.objects if o.type == "MESH" and o.visible_get()]
print("ARMADURA", arm.name, [b.name for b in arm.data.bones])

colores = [(1, .1, .4, 1), (1, .8, 0, 1), (0, .8, .5, 1), (.1, .6, 1, 1), (1, .4, 0, 1), (.7, .2, 1, 1), (1, 1, 1, 1), (.2, 1, .2, 1)]
for i, b in enumerate(arm.pose.bones):
    cabeza, cola = arm.matrix_world @ b.head, arm.matrix_world @ b.tail
    largo = (cola - cabeza).length
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=largo * 0.12, radius2=largo * 0.02, depth=largo, location=(cabeza + cola) / 2)
    hueso = bpy.context.active_object
    hueso.rotation_euler = (cola - cabeza).to_track_quat("Z", "Y").to_euler()
    mat = bpy.data.materials.new(f"hueso{i}")
    mat.diffuse_color = colores[i % len(colores)]
    hueso.data.materials.append(mat)
    hueso.show_in_front = True
    for punto in (cabeza, cola):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=largo * 0.09, location=punto, segments=12, ring_count=8)
        bpy.context.active_object.data.materials.append(mat)

pts = [o.matrix_world @ Vector(c) for o in mallas for c in o.bound_box]
lo = Vector([min(p[i] for p in pts) for i in range(3)])
hi = Vector([max(p[i] for p in pts) for i in range(3)])
centro, tam = (lo + hi) / 2, max(hi - lo)
cam = bpy.data.objects.new("cam_captura", bpy.data.cameras.new("cam_captura"))
bpy.context.collection.objects.link(cam)
cam.location = centro + Vector((tam * 0.55, -tam * 1.5, tam * 0.25))
cam.rotation_euler = (centro - cam.location).to_track_quat("-Z", "Y").to_euler()
sc = bpy.context.scene
sc.camera = cam
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "STUDIO"
sc.display.shading.color_type = "TEXTURE"
sc.display.shading.show_xray = True
sc.display.shading.xray_alpha = 0.55
sc.render.film_transparent = False
sc.world = sc.world or bpy.data.worlds.new("mundo")
sc.render.resolution_x, sc.render.resolution_y = 1080, 1080
sc.render.filepath = salida
bpy.ops.render.render(write_still=True)
print("OK", salida)
