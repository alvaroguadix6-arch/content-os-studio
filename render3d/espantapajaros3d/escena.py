"""«El espantapájaros» en 3D (Blender / Cycles). Misma historia, tiempos, textos y música que simula/espantapajaros.py.

Todo es geometría y materiales procedurales generados por código (sin recursos de terceros).

    python escena.py --out fotogramas/ --frames 0 2129 [--res 540] [--samples 16] [--every 1]
    python escena.py --out prueba/ --times 1.5 8 40      (fotogramas sueltos por segundo)

Luego `montar.py` amplía a 1080×1920, pone textos y destellos y añade la música.
"""
import argparse
import math
import os
import random
import sys
import time

import bpy
from mathutils import Euler, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "simula"))
import espantapajaros as E2D  # noqa: E402  (estado de la historia y tiempos)

FPS = 30
NEST = Vector((0.60, 0.0, 1.72))     # sombrero-nido (boca arriba) sobre el brazo derecho
NECK = Vector((0.0, 0.0, 1.50))
BAR_Z = 1.45
CAM_Z0, CAM_D, CAM_F = 1.257, 11.9, 85.0

k, lerp, cl = E2D.k, E2D.lerp, E2D.cl


def srgb(c):
    """color 0-255 sRGB → lineal"""
    out = []
    for v in c[:3]:
        v = v / 255.0
        out.append(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4)
    return tuple(out)


def link(ob, parent=None):
    bpy.context.scene.collection.objects.link(ob)
    if parent:
        ob.parent = parent
    return ob


def empty(name, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None)
    e.location = loc
    return link(e, parent)


def mesh_obj(name, op, mat=None, parent=None, smooth=True, **kw):
    op(**kw)
    ob = bpy.context.active_object
    ob.name = name
    if smooth:
        bpy.ops.object.shade_smooth()
    if mat:
        ob.data.materials.append(mat)
    if parent:
        mw = ob.matrix_world.copy()
        ob.parent = parent
        ob.matrix_world = mw
    return ob


# ───────────── materiales ─────────────
def material(name, col, rough=0.8, bump=0.0, bump_scale=60.0, sheen=0.0, emit=None, emit_s=0.0, stripes=None):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*srgb(col), 1)
    b.inputs["Roughness"].default_value = rough
    if sheen:
        b.inputs["Sheen Weight"].default_value = sheen
    if emit:
        b.inputs["Emission Color"].default_value = (*srgb(emit), 1)
        b.inputs["Emission Strength"].default_value = emit_s
    if bump:
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = bump_scale
        nz.inputs["Detail"].default_value = 8
        bp = nt.nodes.new("ShaderNodeBump")
        bp.inputs["Strength"].default_value = bump
        nt.links.new(nz.outputs["Fac"], bp.inputs["Height"])
        nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
        # ligera variación de color
        ramp = nt.nodes.new("ShaderNodeMix")
        ramp.data_type = "RGBA"
        ramp.inputs["Factor"].default_value = 0.25
        ramp.inputs[6].default_value = (*srgb(col), 1)
        ramp.inputs[7].default_value = (*[c * 0.7 for c in srgb(col)], 1)
        nz2 = nt.nodes.new("ShaderNodeTexNoise")
        nz2.inputs["Scale"].default_value = bump_scale / 8
        nt.links.new(nz2.outputs["Fac"], ramp.inputs["Factor"])
        nt.links.new(ramp.outputs[2], b.inputs["Base Color"])
    if stripes:
        wv = nt.nodes.new("ShaderNodeTexWave")
        wv.inputs["Scale"].default_value = stripes[1]
        wv.bands_direction = "Z"
        cr = nt.nodes.new("ShaderNodeValToRGB")
        cr.color_ramp.interpolation = "CONSTANT"
        cr.color_ramp.elements[0].color = (*srgb(col), 1)
        cr.color_ramp.elements[1].position = 0.5
        cr.color_ramp.elements[1].color = (*srgb(stripes[0]), 1)
        nt.links.new(wv.outputs["Fac"], cr.inputs["Fac"])
        nt.links.new(cr.outputs["Color"], b.inputs["Base Color"])
    return m


def set_col(m, col):
    nt = m.node_tree
    for n in nt.nodes:
        if n.type == "MIX" and getattr(n, "data_type", "") == "RGBA":
            n.inputs[6].default_value = (*srgb(col), 1)
            n.inputs[7].default_value = (*[c * 0.7 for c in srgb(col)], 1)
            return
    nt.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*srgb(col), 1)


# ───────────── nubes de puntos (nieve, hojas, pétalos, estrellas) ─────────────
def points_object(name, n, mat, radius):
    me = bpy.data.meshes.new(name)
    me.vertices.add(n)
    ob = bpy.data.objects.new(name, me)
    link(ob)
    ng = bpy.data.node_groups.new(name + "_gn", "GeometryNodeTree")
    ng.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi, go = ng.nodes.new("NodeGroupInput"), ng.nodes.new("NodeGroupOutput")
    mp = ng.nodes.new("GeometryNodeMeshToPoints")
    mp.inputs["Radius"].default_value = radius
    sm = ng.nodes.new("GeometryNodeSetMaterial")
    sm.inputs["Material"].default_value = mat
    ng.links.new(gi.outputs[0], mp.inputs["Mesh"])
    ng.links.new(mp.outputs[0], sm.inputs["Geometry"])
    ng.links.new(sm.outputs[0], go.inputs[0])
    mod = ob.modifiers.new("pts", "NODES")
    mod.node_group = ng
    return ob


def set_points(ob, pts):
    me = ob.data
    n = len(me.vertices)
    flat = [0.0] * (n * 3)
    for i in range(n):
        if i < len(pts):
            flat[3 * i:3 * i + 3] = pts[i]
        else:
            flat[3 * i:3 * i + 3] = (0, 0, -50)
    me.vertices.foreach_set("co", flat)
    me.update()


# ───────────── construcción ─────────────
class Escena:
    def __init__(self, res=540, samples=16):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        sc = self.sc = bpy.context.scene
        sc.render.engine = "CYCLES"
        sc.cycles.device = "CPU"
        sc.cycles.samples = samples
        sc.cycles.use_denoising = True
        sc.cycles.max_bounces = 4
        sc.cycles.diffuse_bounces = 2
        sc.cycles.glossy_bounces = 1
        sc.cycles.transparent_max_bounces = 4
        sc.render.resolution_x, sc.render.resolution_y = res, int(res * 16 / 9)
        sc.render.image_settings.file_format = "PNG"
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.look = "AgX - Punchy"
        self.rnd = random.Random(5)
        self.M = {
            "sack": material("saco", (200, 160, 100), 0.9, 0.35, 140),
            "wood": material("madera", (120, 84, 52), 0.8, 0.4, 25),
            "straw": material("paja", E2D.STRAW, 0.6, 0.2, 90),
            "hat": material("sombrero", E2D.HATC, 0.7, 0.5, 70),
            "band": material("cinta", (190, 50, 45), 0.6),
            "shirt": material("camisa", E2D.SHIRT, 0.9, 0.3, 120, sheen=0.4),
            "coat": material("abrigo", E2D.COAT, 0.9, 0.35, 150, sheen=0.6),
            "scarf": material("bufanda", (205, 45, 55), 0.9, sheen=0.6, stripes=((245, 240, 230), 9)),
            "patch": material("remiendo", (150, 120, 70), 0.9, 0.3, 120),
            "ink": material("hilo", (35, 28, 28), 0.5),
            "button": material("boton", (25, 22, 26), 0.25),
            "cheek": material("mejilla", (240, 140, 130), 0.8),
            "hole": material("agujero", (50, 38, 28), 0.9),
            "snow": material("nieve", (250, 252, 255), 0.6, 0.2, 30),
            "ground": material("suelo", (214, 162, 74), 1.0, 0.3, 4),
            "grass": material("hierba", (210, 160, 70), 0.8),
            "hill": material("colina", (186, 112, 66), 1.0),
            "hill2": material("colina2", (214, 140, 74), 1.0),
            "leaf": material("copas", (220, 120, 50), 0.9, 0.5, 6),
            "fleaf": material("hojas", (220, 110, 40), 0.7),
            "fsnow": material("copos", (255, 255, 255), 0.5, emit=(255, 255, 255), emit_s=0.6),
            "petal": material("petalos", (250, 150, 190), 0.6),
            "star": material("estrellas", (255, 255, 255), 1.0, emit=(230, 236, 255), emit_s=0.0),
            "moon": material("luna", (246, 244, 226), 1.0, emit=(246, 244, 226), emit_s=0.0),
            "crow": material("cuervo", (28, 28, 34), 0.5),
            "beak": material("pico", (70, 55, 40), 0.5),
            "bandage": material("venda", (250, 250, 250), 0.9),
        }
        self.world()
        self.landscape()
        self.scarecrow()
        self.birds = [self.make_bird(f"hero", E2D.FLOCK_COLS[0], 1.15)] + [self.make_bird(f"b{i}", E2D.FLOCK_COLS[i], 1.0) for i in range(8)]
        self.crows = [self.make_bird(f"crow{i}", None, 1.5, crow=True) for i in range(3)]
        self.straws = [mesh_obj(f"pajavuela{i}", bpy.ops.mesh.primitive_cylinder_add, self.M["straw"], radius=0.007, depth=0.16,
                                rotation=(0, math.pi / 2, 0)) for i in range(5)]
        self.snow = points_object("nieve", 1600, self.M["fsnow"], 0.012)
        self.leaves = points_object("hojas", 60, self.M["fleaf"], 0.018)
        self.petals = points_object("petalos", 90, self.M["petal"], 0.022)
        stars = self.stars = points_object("estrellas", 300, self.M["star"], 0.25)
        r = random.Random(2)
        set_points(stars, [(r.uniform(-60, 60), 160, r.uniform(8, 70)) for _ in range(300)])
        self.camera()

    def world(self):
        w = bpy.data.worlds.new("mundo")
        self.sc.world = w
        nt = w.node_tree
        bg = nt.nodes["Background"]
        sky = nt.nodes.new("ShaderNodeTexSky")
        sky.sky_type = "MULTIPLE_SCATTERING"
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        nt.links.new(sky.outputs[0], mix.inputs[6])
        nt.links.new(mix.outputs[2], bg.inputs["Color"])
        self.sky, self.skymix, self.bg = sky, mix, bg
        sun = bpy.data.lights.new("sol", "SUN")
        self.sun = link(bpy.data.objects.new("sol", sun))
        fill = bpy.data.lights.new("relleno", "AREA")
        fill.size = 6
        self.fill = link(bpy.data.objects.new("relleno", fill))
        self.fill.location = (-2.5, -6, 3.5)
        self.fill.rotation_euler = Euler((math.radians(60), 0, math.radians(-20)))
        self.moon = mesh_obj("luna", bpy.ops.mesh.primitive_uv_sphere_add, self.M["moon"], radius=4, location=(38, 150, 46))

    def landscape(self):
        M = self.M
        g = mesh_obj("suelo", bpy.ops.mesh.primitive_plane_add, M["ground"], size=400, location=(0, 150, 0), smooth=False)
        for i, (x, y, sx, sz, m) in enumerate([(-40, 140, 90, 22, "hill"), (55, 170, 110, 30, "hill"), (0, 95, 70, 10, "hill2"), (-70, 90, 40, 9, "hill2")]):
            h = mesh_obj(f"colina{i}", bpy.ops.mesh.primitive_uv_sphere_add, M[m], radius=1, location=(x, y, -sz * 0.35), segments=48, ring_count=24)
            h.scale = (sx, sx * 0.4, sz)
        self.tree_tops = []
        r = random.Random(3)
        for i, (x, y) in enumerate([(-9, 30), (-14, 42), (11, 34), (17, 48), (-24, 60), (26, 64)]):
            s = r.uniform(0.9, 1.4)
            mesh_obj(f"tronco{i}", bpy.ops.mesh.primitive_cylinder_add, M["wood"], radius=0.25 * s, depth=4 * s, location=(x, y, 2 * s))
            for j in range(3):
                tp = mesh_obj(f"copa{i}{j}", bpy.ops.mesh.primitive_ico_sphere_add, M["leaf"], radius=1.6 * s, subdivisions=3,
                              location=(x + r.uniform(-0.9, 0.9), y + r.uniform(-0.5, 0.5), 4.2 * s + j * 0.7 * s))
                tp.scale = (1, 1, 0.85)
                self.tree_tops.append((tp, tp.scale.copy()))
        # hierba (instancias en el campo cercano)
        bpy.ops.mesh.primitive_plane_add(size=18, location=(0, 2, 0.001))
        patch = bpy.context.active_object
        patch.name = "campo"
        patch.data.materials.append(M["ground"])
        bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.012, radius2=0, depth=0.22, location=(0, 0, -100))
        blade = bpy.context.active_object
        blade.name = "brizna"
        blade.data.materials.append(M["grass"])
        ng = bpy.data.node_groups.new("hierba", "GeometryNodeTree")
        ng.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
        ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
        N = ng.nodes
        gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
        dist = N.new("GeometryNodeDistributePointsOnFaces")
        dist.inputs["Density"].default_value = 550
        oi = N.new("GeometryNodeObjectInfo")
        oi.inputs["Object"].default_value = blade
        inst = N.new("GeometryNodeInstanceOnPoints")
        rr = N.new("FunctionNodeRandomValue")
        rr.data_type = "FLOAT_VECTOR"
        [x for x in rr.inputs if x.name == "Min" and x.type == "VECTOR"][0].default_value = (-0.35, -0.35, 0)
        [x for x in rr.inputs if x.name == "Max" and x.type == "VECTOR"][0].default_value = (0.35, 0.35, 6.28)
        rs = N.new("FunctionNodeRandomValue")
        [x for x in rs.inputs if x.name == "Min" and x.type == "VALUE"][0].default_value = 0.5
        [x for x in rs.inputs if x.name == "Max" and x.type == "VALUE"][0].default_value = 1.3
        join = N.new("GeometryNodeJoinGeometry")
        L = ng.links
        L.new(gi.outputs[0], dist.inputs["Mesh"])
        L.new(dist.outputs["Points"], inst.inputs["Points"])
        L.new(oi.outputs["Geometry"], inst.inputs["Instance"])
        L.new([x for x in rr.outputs if x.type == "VECTOR"][0], inst.inputs["Rotation"])
        L.new([x for x in rs.outputs if x.type == "VALUE"][0], inst.inputs["Scale"])
        L.new(gi.outputs[0], join.inputs[0])
        L.new(inst.outputs[0], join.inputs[0])
        L.new(join.outputs[0], go.inputs[0])
        patch.modifiers.new("hierba", "NODES").node_group = ng

    def straw_tuft(self, name, loc, direction, n=9, ln=0.13, spread=0.5, parent=None, seed=0):
        r = random.Random(seed)
        objs = []
        d = Vector(direction).normalized()
        for i in range(n):
            v = (d + Vector((r.uniform(-spread, spread), r.uniform(-spread, spread), r.uniform(-spread, spread)))).normalized()
            l = ln * r.uniform(0.6, 1.1)
            c = Vector(loc) + v * l / 2
            ob = mesh_obj(f"{name}{i}", bpy.ops.mesh.primitive_cylinder_add, self.M["straw"], parent=parent, radius=0.006, depth=l, location=c,
                          vertices=6)
            ob.rotation_mode = "QUATERNION"
            ob.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(v)
            objs.append(ob)
        return objs

    def scarecrow(self):
        M = self.M
        mesh_obj("poste", bpy.ops.mesh.primitive_cylinder_add, M["wood"], radius=0.05, depth=1.9, location=(0, 0.02, 0.85))
        mesh_obj("travesaño", bpy.ops.mesh.primitive_cylinder_add, M["wood"], radius=0.035, depth=1.5, location=(0, 0.02, BAR_Z),
                 rotation=(0, math.pi / 2, 0))
        # camisa (cuerpo + mangas)
        self.shirt = mesh_obj("camisa", bpy.ops.mesh.primitive_cone_add, M["shirt"], radius1=0.22, radius2=0.27, depth=0.62, location=(0, 0, 1.17),
                              vertices=48)
        for s in (-1, 1):
            mesh_obj(f"manga{s}", bpy.ops.mesh.primitive_cylinder_add, M["shirt"], radius=0.085, depth=0.5, location=(s * 0.4, 0, BAR_Z),
                     rotation=(0, math.pi / 2, 0), vertices=32)
            self.straw_tuft(f"pajamano{s}", (s * 0.64, 0, BAR_Z), (s, 0, -0.2), 12, 0.16, 0.45, seed=4 + s)
        self.straw_tuft("pajapie", (0, 0, 0.88), (0, 0, -1), 16, 0.16, 0.6, seed=9)
        self.patch = mesh_obj("remiendo", bpy.ops.mesh.primitive_cube_add, M["patch"], size=1, location=(0.07, -0.245, 1.0), smooth=False)
        self.patch.scale = (0.09, 0.012, 0.08)
        self.belt = mesh_obj("cuerda", bpy.ops.mesh.primitive_torus_add, M["straw"], major_radius=0.235, minor_radius=0.014, location=(0, 0, 0.93))
        self.hole = mesh_obj("agujero", bpy.ops.mesh.primitive_cylinder_add, M["hole"], radius=0.07, depth=0.02, location=(-0.07, -0.25, 1.26),
                             rotation=(math.pi / 2, 0, 0))
        self.hole_straw = self.straw_tuft("pajaagujero", (-0.07, -0.26, 1.26), (0, -1, 0.3), 8, 0.1, 0.7, seed=12)
        # abrigo (cuerpo + mangas) agrupado
        self.coat = empty("abrigo_grupo", (0, 0, 0))
        cb = mesh_obj("abrigo", bpy.ops.mesh.primitive_cone_add, M["coat"], parent=self.coat, radius1=0.27, radius2=0.31, depth=0.66,
                      location=(0, 0, 1.17), vertices=48)
        for s in (-1, 1):
            mesh_obj(f"mangaabrigo{s}", bpy.ops.mesh.primitive_cylinder_add, M["coat"], parent=self.coat, radius=0.105, depth=0.42,
                     location=(s * 0.38, 0, BAR_Z), rotation=(0, math.pi / 2, 0), vertices=32)
        for i in range(3):
            mesh_obj(f"botonabrigo{i}", bpy.ops.mesh.primitive_cylinder_add, M["hat"], parent=self.coat, radius=0.022, depth=0.02,
                     location=(0.05, -0.30 + i * 0.01, 1.32 - i * 0.14), rotation=(math.pi / 2 - 0.15, 0, 0))
        self.coat_parts = [cb]
        self.blanket = mesh_obj("manta", bpy.ops.mesh.primitive_uv_sphere_add, M["coat"], radius=1, location=NEST + Vector((0, 0, 0.02)))
        self.blanket.scale = (0.2, 0.17, 0.08)
        # cabeza (todo cuelga del cuello para inclinarla)
        self.neck = empty("cuello", NECK)
        head_c = Vector((0, 0, 1.78))
        self.head = mesh_obj("cabeza", bpy.ops.mesh.primitive_uv_sphere_add, M["sack"], parent=self.neck, radius=0.2, location=head_c,
                             segments=48, ring_count=24)
        self.head.scale = (1, 0.95, 1.05)
        mesh_obj("atadura", bpy.ops.mesh.primitive_torus_add, M["straw"], parent=self.neck, major_radius=0.085, minor_radius=0.016,
                 location=(0, 0, 1.6))
        self.straw_tuft("pelo", (0, 0, 1.9), (0, 0, 1), 26, 0.2, 1.3, parent=self.neck, seed=21)

        def on_face(x, z, off=0.004):
            y = -math.sqrt(max(0.0, 0.2 ** 2 - x * x - z * z)) * 0.95 - off
            return head_c + Vector((x, y, z))

        self.eyes, self.eyes_closed = [], []
        for s in (-1, 1):
            e = mesh_obj(f"ojo{s}", bpy.ops.mesh.primitive_cylinder_add, M["button"], parent=self.neck, radius=0.033, depth=0.02,
                         location=on_face(s * 0.07, 0.035), rotation=(math.pi / 2, 0, 0))
            self.eyes.append((e, e.location.copy()))
            c = mesh_obj(f"ojocerrado{s}", bpy.ops.mesh.primitive_torus_add, M["ink"], parent=self.neck, major_radius=0.03, minor_radius=0.005,
                         location=on_face(s * 0.07, 0.035), rotation=(math.pi / 2, 0, 0))
            c.scale = (1, 1, 0.55)
            self.eyes_closed.append(c)
            ck = mesh_obj(f"mejilla{s}", bpy.ops.mesh.primitive_uv_sphere_add, M["cheek"], parent=self.neck, radius=0.03,
                          location=on_face(s * 0.12, -0.03, 0.0))
            ck.scale = (1, 0.3, 0.7)
            self.cheeks = getattr(self, "cheeks", []) + [ck]
        # boca: curva cosida
        cu = bpy.data.curves.new("boca", "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = 0.011
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(2)
        for bp in sp.bezier_points:
            bp.handle_left_type = bp.handle_right_type = "AUTO"
        self.mouth = link(bpy.data.objects.new("boca", cu), self.neck)
        self.mouth.data.materials.append(M["ink"])
        self.on_face = on_face
        self.stitches = [mesh_obj(f"punto{i}", bpy.ops.mesh.primitive_cylinder_add, M["ink"], parent=self.neck, radius=0.004, depth=0.03,
                                  location=(0, 0, 0)) for i in range(5)]
        # sombrero
        self.hat = empty("sombrero", (0, 0, 0))
        mesh_obj("ala", bpy.ops.mesh.primitive_cylinder_add, M["hat"], parent=self.hat, radius=0.34, depth=0.025, location=(0, 0, 1.93), vertices=64)
        mesh_obj("copa", bpy.ops.mesh.primitive_cone_add, M["hat"], parent=self.hat, radius1=0.19, radius2=0.165, depth=0.18, location=(0, 0, 2.03),
                 vertices=48)
        mesh_obj("cinta", bpy.ops.mesh.primitive_cylinder_add, M["band"], parent=self.hat, radius=0.187, depth=0.045, location=(0, 0, 1.975),
                 vertices=48)
        self.hat_flowers = []
        for i in range(5):
            a = -math.pi / 2 + (i - 2) * 0.32
            f = self.flower(f"florsombrero{i}", Vector((math.cos(a) * 0.19, math.sin(a) * 0.19, 1.975)), E2D.FLOWER_COLS[i % 5], 0.028, self.hat)
            self.hat_flowers.append(f)
        # bufanda
        self.scarf = empty("bufanda", (0, 0, 0))
        mesh_obj("bufandaanillo", bpy.ops.mesh.primitive_torus_add, M["scarf"], parent=self.scarf, major_radius=0.16, minor_radius=0.055,
                 location=(0, 0, 1.56))
        self.scarf_tail = mesh_obj("bufandacola", bpy.ops.mesh.primitive_cube_add, M["scarf"], parent=self.scarf, size=1,
                                   location=(0.09, -0.2, 1.4))
        self.scarf_tail.scale = (0.07, 0.025, 0.26)
        self.scarf_tail.rotation_euler = (0.15, 0, 0.1)
        # nieve acumulada
        self.snowcaps = []
        for name, loc, sc in (("nievecabeza", (0, 0, 1.97), (0.15, 0.13, 0.05)), ("nievehombro", (-0.4, 0, BAR_Z + 0.1), (0.2, 0.09, 0.04)),
                              ("nievenido", NEST + Vector((0, 0, 0.1)), (0.18, 0.15, 0.045))):
            o = mesh_obj(name, bpy.ops.mesh.primitive_uv_sphere_add, M["snow"], radius=1, location=loc,
                         parent=self.neck if name == "nievecabeza" else None)
            self.snowcaps.append((o, Vector(sc)))
        # flores del cuerpo
        self.body_flowers = []
        r = random.Random(8)
        for i in range(16):
            z = r.uniform(0.95, 1.42)
            ang = r.uniform(-1.2, 1.2) - math.pi / 2
            rad = lerp(0.22, 0.27, (z - 0.86) / 0.62) + 0.01
            if i in (6, 7, 8, 9, 10):  # en las mangas
                x = [-0.5, 0.42, -0.32, 0.3, -0.2][i - 6]
                loc = Vector((x, -0.08, BAR_Z + 0.05))
            else:
                loc = Vector((math.cos(ang) * rad, math.sin(ang) * rad, z))
            self.body_flowers.append(self.flower(f"flor{i}", loc, E2D.FLOWER_COLS[i % 5], 0.035))

    def flower(self, name, loc, col, size, parent=None):
        g = empty(name, loc, parent)
        mat = bpy.data.materials.get(f"petalo{col}") or material(f"petalo{col}", col, 0.6, sheen=0.3)
        for i in range(5):
            a = i * 2 * math.pi / 5
            p = mesh_obj(f"{name}p{i}", bpy.ops.mesh.primitive_uv_sphere_add, mat, parent=g, radius=size * 0.55,
                         location=loc + Vector((math.cos(a) * size * 0.6, -0.01, math.sin(a) * size * 0.6)), segments=12, ring_count=8)
            p.scale = (1, 0.4, 1)
        mesh_obj(f"{name}c", bpy.ops.mesh.primitive_uv_sphere_add, self.M["straw"], parent=g, radius=size * 0.4, location=loc + Vector((0, -0.02, 0)),
                 segments=12, ring_count=8)
        g.scale = (0, 0, 0)
        return g

    def make_bird(self, name, cols, size, crow=False):
        M = self.M
        if crow:
            mb = mbr = M["crow"]
        else:
            breast, back = cols
            mb = bpy.data.materials.get(f"plumaje{back}") or material(f"plumaje{back}", back, 0.8, 0.2, 200, sheen=0.8)
            mbr = bpy.data.materials.get(f"pecho{breast}") or material(f"pecho{breast}", breast, 0.8, 0.2, 200, sheen=0.8)
        root = empty(name, (0, 0, -50))
        body = empty(name + "_cuerpo", (0, 0, 0), root)
        s = 1.0

        def part(nm, op, mat, loc, scale=(1, 1, 1), **kw):
            o = mesh_obj(name + nm, op, mat, location=loc, **kw)
            o.scale = scale
            o.parent = body
            return o

        part("tronco", bpy.ops.mesh.primitive_uv_sphere_add, mb, (0, 0, 0), (1.25, 0.95, 1.0), radius=0.055, segments=24, ring_count=12)
        part("pecho", bpy.ops.mesh.primitive_uv_sphere_add, mbr, (0.028, 0, -0.008), (0.9, 0.85, 0.85), radius=0.05, segments=24, ring_count=12)
        part("cabeza", bpy.ops.mesh.primitive_uv_sphere_add, mb, (0.06, 0, 0.05), (1, 1, 1), radius=0.038, segments=24, ring_count=12)
        part("cara", bpy.ops.mesh.primitive_uv_sphere_add, mbr, (0.075, 0, 0.04), (0.8, 0.9, 0.8), radius=0.03, segments=16, ring_count=8)
        part("pico", bpy.ops.mesh.primitive_cone_add, M["beak"], (0.108, 0, 0.05), (1, 1, 1), radius1=0.011, radius2=0, depth=0.035,
             rotation=(0, math.pi / 2, 0), vertices=12)
        for sy in (-1, 1):
            part(f"ojo{sy}", bpy.ops.mesh.primitive_uv_sphere_add, M["button"], (0.075, sy * 0.03, 0.062), (1, 1, 1), radius=0.008, segments=12,
                 ring_count=6)
        part("cola", bpy.ops.mesh.primitive_cone_add, mb, (-0.085, 0, 0.012), (1, 0.6, 1), radius1=0.03, radius2=0.004, depth=0.07,
             rotation=(0, -math.pi / 2 - 0.3, 0), vertices=12)
        wings = []
        for sy in (-1, 1):
            hinge = empty(f"{name}hombro{sy}", (0, sy * 0.035, 0.02), body)
            wgt = mesh_obj(f"{name}ala{sy}", bpy.ops.mesh.primitive_uv_sphere_add, mb, location=(0, 0, 0), radius=1, segments=16, ring_count=8)
            wgt.scale = (0.055, 0.012, 0.03) if not crow else (0.06, 0.01, 0.035)
            wgt.parent = hinge
            wgt.location = (-0.012, sy * 0.045, 0)
            wings.append((hinge, sy))
        band = part("venda", bpy.ops.mesh.primitive_cube_add, M["bandage"], (-0.01, -0.048, 0.022), (0.03, 0.006, 0.02), size=1)
        root.scale = (size * 1.8,) * 3
        return dict(root=root, body=body, wings=wings, band=band, flower=None, crow=crow)

    def camera(self):
        cd = bpy.data.cameras.new("cam")
        cd.lens = CAM_F
        cd.sensor_fit = "VERTICAL"
        cd.sensor_height = 36
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = 2.8
        self.cam = link(bpy.data.objects.new("cam", cd))
        self.sc.camera = self.cam

    # ───────────── por fotograma ─────────────
    def season_params(self, name):
        return {
            "otono": dict(elev=7, rot=200, sky=0.5, flat=0.55, flatc=(250, 168, 96), sunc=(255, 180, 110), suns=3.2, sang=2, fill=50,
                          ground=(205, 150, 70), grass=(214, 165, 72), hill=(170, 100, 60), hill2=(200, 130, 70), leaf=(220, 120, 50), leafk=1, night=0, exp=-0.2),
            "invierno": dict(elev=20, rot=160, sky=0.5, flat=0.85, flatc=(176, 188, 210), sunc=(220, 228, 255), suns=1.4, sang=25, fill=90,
                             ground=(236, 241, 248), grass=(225, 232, 242), hill=(200, 208, 226), hill2=(222, 228, 240), leaf=(230, 235, 245), leafk=0.45,
                             night=0, exp=-1.7),
            "noche": dict(elev=-5, rot=160, sky=0.1, flat=1.0, flatc=(22, 30, 64), sunc=(150, 175, 255), suns=1.6, sang=4, fill=55,
                          ground=(150, 162, 196), grass=(150, 160, 194), hill=(50, 58, 90), hill2=(64, 72, 108), leaf=(120, 130, 160), leafk=0.45,
                          night=1, exp=0.6),
            "primavera": dict(elev=40, rot=150, sky=0.55, flat=0.0, flatc=(120, 190, 250), sunc=(255, 246, 228), suns=4.2, sang=3, fill=70,
                              ground=(110, 176, 82), grass=(116, 190, 84), hill=(86, 150, 76), hill2=(112, 178, 88), leaf=(90, 170, 70), leafk=1,
                              night=0, exp=-1.3),
        }[name]

    def apply_season(self, t):
        a, b, m = E2D.season_mix(t)
        pa, pb = self.season_params(a), self.season_params(b)

        def L(key):
            va, vb = pa[key], pb[key]
            if isinstance(va, tuple):
                return tuple(lerp(x, y, m) for x, y in zip(va, vb))
            return lerp(va, vb, m)

        self.sky.sun_elevation = math.radians(max(L("elev"), 1))
        self.sky.sun_rotation = math.radians(L("rot"))
        self.skymix.inputs["Factor"].default_value = L("flat")
        self.skymix.inputs[7].default_value = (*srgb(L("flatc")), 1)
        self.bg.inputs["Strength"].default_value = L("sky") if L("flat") < 0.5 else lerp(0.6, 1.0, L("flat")) * (1 - 0.8 * L("night"))
        sun = self.sun.data
        sun.color = srgb(L("sunc"))
        sun.energy = L("suns")
        sun.angle = math.radians(L("sang"))
        el = math.radians(max(L("elev"), 12 if L("night") > 0.5 else 4))
        rotz = math.radians(L("rot") - 180)
        self.sun.rotation_euler = Euler((math.pi / 2 - el, 0, rotz))
        self.fill.data.energy = L("fill")
        self.sc.view_settings.exposure = L("exp")
        self.fill.data.color = srgb(mixc_t(L("sunc"), (200, 210, 255), 0.6))
        for key, mat in (("ground", "ground"), ("grass", "grass"), ("hill", "hill"), ("hill2", "hill2"), ("leaf", "leaf")):
            set_col(self.M[mat], L(key))
        lk = L("leafk")
        for tp, base in self.tree_tops:
            tp.scale = base * lk
        nt = L("night")
        self.M["star"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 3 * nt
        self.M["moon"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 4 * nt
        self.moon.hide_render = nt < 0.05
        self.stars.hide_render = nt < 0.05

    def pose_bird(self, b, pos, t, fly, face, scale=1.0, hurt=False, shiver=0.0, carry=None, seed=0, visible=True):
        root = b["root"]
        if not visible or pos is None:
            root.location = (0, 0, -50)
            return
        x, y, z = pos
        if shiver:
            x += math.sin(t * 60 + seed) * 0.006 * shiver
        root.location = (x, y, z)
        root.rotation_euler = (0, 0, 0 if face > 0 else math.pi)
        base = 1.0 * (1.6 if b["crow"] else 1.0)
        root.scale = (base * scale,) * 3
        for hinge, sy in b["wings"]:
            if fly:
                a = math.sin(t * 28 + seed) * 1.1
                hinge.rotation_euler = (sy * a, 0, 0)
            else:
                hinge.rotation_euler = (sy * -0.15, 0, 0)
        b["body"].rotation_euler = (0, -0.25 if fly else 0.0, 0)
        b["band"].hide_render = not hurt

    def pose(self, t):
        s = E2D.state(t)
        te = 40.8 if t < 3.5 else t
        self.apply_season(t)
        # cuerpo
        f = s["fill"]
        sh = math.sin(t * 55) * 0.006 * s["shiver"]
        self.shirt.scale = (0.6 + 0.4 * f, 0.6 + 0.4 * f, 1)
        self.shirt.location.x = sh
        self.patch.location = (0.07 * (0.6 + 0.4 * f) + sh, -0.245 * (0.6 + 0.4 * f), 1.0)
        hole_k = cl((0.85 - f) / 0.3)
        self.hole.scale = (hole_k + 1e-4,) * 3
        self.hole.location = (-0.07 + sh, -0.252 * (0.6 + 0.4 * f) - 0.005, 1.26)
        for o in self.hole_straw:
            o.hide_render = hole_k < 0.05
        # abrigo
        c = s["coat"]
        if c < 0.02:
            self.coat.location = (0, 0, 0)
            self.coat.scale = (1, 1, 1)
            self.coat.hide_render = False
            for o in self.coat.children:
                o.hide_render = False
            self.blanket.hide_render = True
        elif c < 0.98:
            p = Vector((0, 0, 1.17)).lerp(NEST + Vector((0, 0, 0.02)), c) + Vector((0, 0, 0.5 * math.sin(math.pi * c)))
            sc_ = lerp(1.0, 0.45, c)
            self.coat.scale = (sc_, sc_, lerp(1, 0.3, c))
            self.coat.location = p - Vector((0, 0, 1.17)) * self.coat.scale.z
            for o in self.coat.children:
                o.hide_render = False
            self.blanket.hide_render = True
        else:
            for o in self.coat.children:
                o.hide_render = True
            self.blanket.hide_render = False
        # cabeza
        self.neck.rotation_euler = (0, s["tilt"], 0)
        self.neck.location = NECK - Vector((0, 0, s["droop"] / 430.0)) + Vector((sh, 0, 0))
        closed = s["closed"]
        lx, ly = s["look"]
        for (e, base), ec in zip(self.eyes, self.eyes_closed):
            e.hide_render = closed
            ec.hide_render = not closed
            e.location = base + Vector((lx * 0.0012, 0, -ly * 0.0012))
        sm = s["smile"]
        pts = [self.on_face(-0.085, -0.075), self.on_face(0, -0.075 - 0.045 * sm, 0.006), self.on_face(0.085, -0.075)]
        for bp, p in zip(self.mouth.data.splines[0].bezier_points, pts):
            bp.co = p - NECK
            bp.handle_left_type = bp.handle_right_type = "AUTO"
        for i, st in enumerate(self.stitches):
            u = -0.8 + i * 0.4
            st.location = self.on_face(u * 0.085, -0.075 - 0.045 * sm * (1 - u * u), 0.008) - NECK
        for ck in self.cheeks:
            ck.hide_render = sm < 0.6
        # sombrero: cabeza → nido (boca arriba) → cabeza
        hn = s["hat_nest"]
        tilt = s["tilt"]
        on_head = self.neck.location + Vector((math.sin(tilt) * 0.43, 0, math.cos(tilt) * 0.43))
        hp = on_head.lerp(NEST, hn) + Vector((0, 0, 0.45 * math.sin(math.pi * hn)))
        self.hat.location = hp - Vector((0, 0, 1.93))
        # el grupo se diseñó en z=1.93: se gira alrededor de su propio centro
        self.hat.rotation_euler = (math.pi * hn, lerp(tilt, 0, hn), 0)
        self.hat.location = hp - self.hat.matrix_basis.to_3x3() @ Vector((0, 0, 1.93)) if hn > 0 else hp - Vector((0, 0, 1.93))
        sc_h = lerp(1, 0.85, hn)
        self.hat.scale = (sc_h,) * 3
        self.hat.location = hp - (Euler(self.hat.rotation_euler).to_matrix() @ Vector((0, 0, 1.93 * sc_h)))
        for i, fl in enumerate(self.hat_flowers):
            v = k(te, 59.0 + i * 0.12, 59.4 + i * 0.12)
            fl.scale = (v,) * 3
        # bufanda
        sn = s["scarf_nest"]
        neckpos = Vector((sh, 0, 1.56))
        target = NEST + Vector((0, 0, 0.1))
        sp = neckpos.lerp(target, sn) + Vector((0, 0, 0.35 * math.sin(math.pi * sn)))
        scs = lerp(1, 1.6, sn)
        self.scarf.scale = (scs, scs, lerp(1, 0.7, sn))
        self.scarf.location = sp - Vector((0, 0, 1.56 * self.scarf.scale.z))
        self.scarf_tail.hide_render = sn > 0.05
        if c > 0.98:  # bajo la manta
            self.scarf.location.z -= 0.04
        # nieve acumulada
        sv = s["snow"]
        for o, base in self.snowcaps:
            o.scale = base * (sv + 1e-4)
            o.hide_render = sv < 0.02
        # flores
        for i, fl in enumerate(self.body_flowers):
            v = cl((te - (55.6 + i * 0.27)) / 0.25) if i < s["flowers"] + 1 else 0.0
            fl.scale = (v * (1 + 0.25 * math.sin(math.pi * cl(v))),) * 3
        # paja que vuela al nido
        for j, o in enumerate(self.straws):
            if 29.2 < te < 32.8:
                u = ((te - 29.2) / 1.2 + j * 0.2) % 1
                p = Vector((-0.07, -0.28, 1.26)).lerp(NEST + Vector((0, 0, 0.05)), u) + Vector((0, 0, 0.35 * math.sin(math.pi * u)))
                o.location = p
                o.rotation_euler = (0, math.pi / 2, u * 6)
                o.hide_render = False
            else:
                o.hide_render = True
        self.pose_birds(t, te, s)
        self.particles(t)
        self.camera_at(t)

    def hero_pos(self, t):
        if 3.5 > t:
            return (NEST.x, -0.01, NEST.z + 0.08), False, 1, 0.95, 0.6
        if t < 6.0:
            return None
        if t < 7.2:
            u = (t - 6.0) / 1.2
            return (lerp(1.5, 0.42, u) + 0.12 * math.sin(u * 9), -0.35, lerp(2.7, 0.07, u * u)), True, -1, 1.0, 0.0
        if t < 11.0:
            return (0.42, -0.35, 0.07), False, -1, 1.0, 1.0
        if t < 12.5:
            u = k(t, 11.0, 12.5)
            return (lerp(0.42, NEST.x, u), lerp(-0.35, -0.02, u), lerp(0.07, NEST.z + 0.04, u) + 0.55 * math.sin(math.pi * u)), True, 1, 1.0, 0.0
        if t < 45.4:
            z = NEST.z + (0.04 if t < 25 else 0.14)
            shiv = 1.0 if 15.6 < t < 17.8 else 0.3 if t > 25 else 0.0
            return (NEST.x, -0.01, z), False, -1, 0.95, shiv
        if t < 46.5:
            u = k(t, 45.4, 46.0)
            return (NEST.x, -0.02, NEST.z + 0.09 + 0.25 * u), u > 0.1, -1, 1.0, 0.0
        if t < 49.0:
            a = (t - 46.5) / 2.5 * 2 * math.pi
            return (0.95 * math.sin(a), -0.6 * math.cos(a), 1.85 + 0.25 * math.sin(2 * a)), True, 1 if math.cos(a) > 0 else -1, 1.0, 0.0
        if t < 50.6:
            u = k(t, 49.0, 50.6)
            return (lerp(0, 3.2, u), lerp(-0.6, 2.5, u), lerp(1.85, 3.8, u)), True, 1, 1.0, 0.0
        return None

    def pose_birds(self, t, te, s):
        hb = self.hero_pos(t)
        hero = self.birds[0]
        hurt = s["hurt"] and t >= 3.5 or t < 3.5
        if t >= 60.6:
            u = k(t, 60.6, 61.6)
            hp = self.hat.location + Euler(self.hat.rotation_euler).to_matrix() @ Vector((0, 0, 2.12 * self.hat.scale.z))
            start = hp + Vector((0.02, 0, 0.45))
            self.pose_bird(hero, start.lerp(hp + Vector((0, 0, 0.06)), u), t, u < 0.95, -1, 1.0)
        elif hb is None:
            self.pose_bird(hero, None, t, False, 1)
        else:
            pos, fl, face, sc_, shiv = hb
            self.pose_bird(hero, pos, t, fl, face, sc_, hurt=hurt, shiver=shiv)
        # bandada
        perches = [(-0.6, -0.01, BAR_Z + 0.12), (-0.45, -0.02, BAR_Z + 0.12), (-0.3, -0.03, BAR_Z + 0.12), (0.28, -0.03, BAR_Z + 0.12),
                   (NEST.x - 0.12, -0.05, NEST.z + 0.14), (NEST.x + 0.16, -0.04, NEST.z + 0.12), (0.42, -0.03, BAR_Z + 0.12), (-0.17, -0.03, BAR_Z + 0.12)]
        for i, b in enumerate(self.birds[1:]):
            if t < 53.4:
                self.pose_bird(b, None, t, False, 1)
                continue
            a0 = i * 0.8
            if t < 55.6:
                u = k(t, 53.4 + i * 0.08, 55.6)
                start = Vector((3.4 + (i % 3) * 0.3, 2.0 + i * 0.1, 2.6 + abs(i - 3.5) * 0.12))
                orbit = Vector((1.0 * math.sin(a0), -0.65 * math.cos(a0), 1.6 + 0.35 * math.sin(i * 1.7)))
                self.pose_bird(b, start.lerp(orbit, u), t, True, -1, seed=i)
            elif t < 60.6:
                a = a0 + (t - 55.6) * 1.5
                pos = Vector((1.0 * math.sin(a), -0.65 * math.cos(a), 1.6 + 0.35 * math.sin(i * 1.7) + 0.08 * math.sin(t * 3 + i)))
                if i == 6 and t > 58.6:  # trae el sombrero de vuelta
                    pos = self.hat.location + Euler(self.hat.rotation_euler).to_matrix() @ Vector((0, 0, 2.12 * self.hat.scale.z)) + Vector((0.05, 0, 0.3))
                self.pose_bird(b, pos, t, True, 1 if math.cos(a) > 0 else -1, seed=i)
            else:
                a = a0 + 5.0 * 1.5
                orbit = Vector((1.0 * math.sin(a), -0.65 * math.cos(a), 1.6 + 0.35 * math.sin(i * 1.7)))
                u = k(t, 60.6 + i * 0.1, 61.8 + i * 0.1)
                self.pose_bird(b, orbit.lerp(Vector(perches[i]), u), t, u < 0.95, 1 if perches[i][0] < 0 else -1, seed=i)
        for i, cr in enumerate(self.crows):
            if 3.5 <= t < 6.2:
                u = (t - 3.5) / 2.7
                self.pose_bird(cr, (0.3 + i * 0.25 + u * 3.5, -0.5 + i * 0.3, 1.9 + i * 0.15 + u * 2.2), t, True, 1, seed=i * 2)
            else:
                self.pose_bird(cr, None, t, False, 1)

    def particles(self, t):
        R = E2D.PARTS
        snow, leaves, petals = [], [], []
        wint = (t < 3.5) or (14.6 < t < 43)
        if wint:
            n = 500 if t < 22 and t >= 3.5 else 900 if t < 35 and t >= 3.5 else 1600
            wind = 0.0 if (3.5 <= t < 35) else 1.1
            dens = k(t, 14.6, 16) if t >= 3.5 else 1
            r = random.Random(1)
            for i in range(int(n * dens)):
                x0, y0, z0, sp = r.uniform(-2.6, 2.6), r.uniform(-4.5, 3), r.uniform(0, 3.4), r.uniform(0.6, 1.3)
                z = (z0 - t * 0.55 * sp) % 3.4
                x = (x0 + 0.08 * math.sin(t * sp + i) + t * wind * sp + 2.6) % 5.2 - 2.6
                snow.append((x, y0, z))
        if 3.5 <= t < 14:
            r = random.Random(3)
            for i in range(60):
                x0, y0, z0, sp = r.uniform(-2.4, 2.4), r.uniform(-3, 2), r.uniform(0, 3.2), r.uniform(0.5, 1.2)
                z = (z0 - t * 0.35 * sp) % 3.2
                leaves.append(((x0 + 0.25 * math.sin(t * sp + i) + t * 0.12 + 2.4) % 4.8 - 2.4, y0, z))
        if t > 44:
            r = random.Random(4)
            for i in range(40 if t < 53 else 90):
                x0, y0, z0, sp = r.uniform(-2.4, 2.4), r.uniform(-3, 2), r.uniform(0, 3.2), r.uniform(0.4, 1.0)
                z = (z0 - t * 0.22 * sp) % 3.2
                petals.append(((x0 + 0.3 * math.sin(t * sp * 0.7 + i) + 2.4) % 4.8 - 2.4, y0, z))
        set_points(self.snow, snow)
        set_points(self.leaves, leaves)
        set_points(self.petals, petals)

    def camera_at(self, t):
        """encuadre por tramos: (punto de mira, alto del encuadre en metros)"""
        te = t
        if t < 3.5:
            tgt, hgt = Vector((0.3, 0, 1.62)), 1.55
        elif 7.0 <= te < 8.8:
            tgt, hgt = Vector((0.35, -0.35, 0.32)), 1.25
        elif 15.6 <= te < 17.6:
            tgt, hgt = Vector((0.45, 0, 1.55)), 1.0
        elif 37.4 <= te < 41.8:
            tgt, hgt = Vector((0.3, 0, 1.62)), lerp(1.7, 1.35, k(te, 37.4, 41.8))
        elif 50.6 <= te < 53.4:
            tgt, hgt = Vector((0.1, 0, 1.6)), lerp(2.4, 1.6, k(te, 50.6, 53.4))
        elif 60.6 <= te < 63.4:
            tgt, hgt = Vector((0.15, 0, 1.68)), 1.75
        else:
            tgt, hgt = Vector((0.05, 0, CAM_Z0)), 5.03 * lerp(1.0, 0.93, (math.sin(te * 0.15) + 1) / 2)
            if te >= 63.4:
                tgt, hgt = Vector((0.05, 0, CAM_Z0 + 0.25 * k(te, 63.4, 65))), 5.03 * lerp(1.0, 1.12, k(te, 63.4, 65))
        d = hgt / (36 / CAM_F)
        # en los planos cortos, la mira queda algo por debajo del centro para dejar cielo arriba para los textos
        shift = 0.12 * hgt if hgt < 3 else 0
        pos = Vector((tgt.x + 0.25 * math.sin(te * 0.2), -d, tgt.z + shift + 0.1))
        self.cam.location = pos
        look = Vector((tgt.x, 0, tgt.z + shift))
        self.cam.rotation_euler = (look - pos).to_track_quat("-Z", "Y").to_euler()
        self.cam.data.dof.focus_distance = (Vector((tgt.x, 0, tgt.z)) - pos).length

    def render(self, t, path):
        self.pose(t)
        self.sc.render.filepath = path
        bpy.ops.render.render(write_still=True)


def mixc_t(a, b, x):
    return tuple(lerp(p, q, x) for p, q in zip(a, b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--frames", nargs=2, type=int)
    ap.add_argument("--times", nargs="+", type=float)
    ap.add_argument("--res", type=int, default=540)
    ap.add_argument("--samples", type=int, default=16)
    ap.add_argument("--every", type=int, default=1)
    ap.add_argument("--offset", type=int, default=0)
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    os.makedirs(a.out, exist_ok=True)
    esc = Escena(a.res, a.samples)
    if a.times:
        for t in a.times:
            t0 = time.time()
            esc.render(t, os.path.join(a.out, f"t_{t:05.1f}.png"))
            print(f"t={t} {time.time() - t0:.1f}s", flush=True)
        return
    for fi in range(a.frames[0] + a.offset, a.frames[1] + 1, a.every):
        p = os.path.join(a.out, f"f{fi:05d}.png")
        if os.path.exists(p):
            continue
        t0 = time.time()
        esc.render(fi / FPS, p)
        print(f"f{fi} {time.time() - t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
