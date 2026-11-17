"""Construye y renderiza la carrera en 3D con Blender (módulo bpy).

Uso (con el Python que tenga `bpy` instalado, o con `blender -b -P`):
    python scene_race.py --out salida/ --frames 0 1391 [--samples 24] [--scale 100] [--spec spec.json]

Todo es geometría 3D real renderizada con Cycles (trazado de rayos):
circuito, pianos, muros, gradas con público, edificios de la ciudad, pórtico de salida,
cielo físico al atardecer y dos superdeportivos (modelo CC-BY 4.0) animados fotograma a fotograma.
"""
import argparse
import math
import os
import random
import sys

import bpy
from mathutils import Euler, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import ROAD_WIDTH, Race, RaceSpec  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CAR_GLB = os.environ.get("CAR_GLB", os.path.join(HERE, "assets", "CarConcept.glb"))


# ─────────────────────────── materiales ───────────────────────────

def mat(name, color=(0.5, 0.5, 0.5), rough=0.5, metal=0.0, emit=None, emit_strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = emit_strength
    return m


def car_paint(name, color):
    m = mat(name, color, rough=0.28, metal=0.55)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Coat Weight"].default_value = 1.0
    b.inputs["Coat Roughness"].default_value = 0.03
    return m


def asphalt_mat():
    m = bpy.data.materials.new("Asfalto")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = nt.nodes.new("ShaderNodeTexNoise")
    n1.inputs["Scale"].default_value = 0.35
    n1.inputs["Detail"].default_value = 6
    n2 = nt.nodes.new("ShaderNodeTexNoise")
    n2.inputs["Scale"].default_value = 90
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.035, 0.035, 0.038, 1)
    ramp.color_ramp.elements[1].color = (0.11, 0.105, 0.1, 1)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "FLOAT"
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    nt.links.new(tc.outputs["Object"], n2.inputs["Vector"])
    nt.links.new(n1.outputs["Fac"], mix.inputs[2])
    nt.links.new(n2.outputs["Fac"], mix.inputs[3])
    mix.inputs[0].default_value = 0.35
    nt.links.new(mix.outputs[0], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs[3].default_value = 0.45
    rr.inputs[4].default_value = 0.85
    nt.links.new(n2.outputs["Fac"], rr.inputs[0])
    nt.links.new(rr.outputs[0], b.inputs["Roughness"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.25
    nt.links.new(n2.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def striped_mat(name, c1, c2, stripe_m=2.0, emissive=False):
    """Rayas a lo largo del circuito (pianos rojo/blanco). Usa la coordenada U = metros."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    uv = nt.nodes.new("ShaderNodeUVMap")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    math1 = nt.nodes.new("ShaderNodeMath")
    math1.operation = "DIVIDE"
    math1.inputs[1].default_value = stripe_m
    fl = nt.nodes.new("ShaderNodeMath")
    fl.operation = "PINGPONG"
    fl.inputs[1].default_value = 1.0
    gt = nt.nodes.new("ShaderNodeMath")
    gt.operation = "GREATER_THAN"
    gt.inputs[1].default_value = 0.5
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[6].default_value = (*c1, 1)
    mix.inputs[7].default_value = (*c2, 1)
    nt.links.new(uv.outputs["UV"], sep.inputs[0])
    nt.links.new(sep.outputs[0], math1.inputs[0])
    nt.links.new(math1.outputs[0], fl.inputs[0])
    nt.links.new(fl.outputs[0], gt.inputs[0])
    nt.links.new(gt.outputs[0], mix.inputs[0])
    nt.links.new(mix.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.55
    return m


def checker_mat():
    m = bpy.data.materials.new("Meta")
    m.use_nodes = True
    nt = m.node_tree
    ch = nt.nodes.new("ShaderNodeTexChecker")
    ch.inputs["Scale"].default_value = 1.0
    ch.inputs["Color1"].default_value = (0.9, 0.9, 0.9, 1)
    ch.inputs["Color2"].default_value = (0.02, 0.02, 0.02, 1)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["UV"], ch.inputs["Vector"])
    nt.links.new(ch.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    return m


def windows_mat(name, base, seed):
    """Fachadas con ventanas (algunas encendidas) mediante textura de ladrillo procedural."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    tc = type("TC", (), {"outputs": {"Object": geo.outputs["Position"]}})()
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.offset = 0.0
    br.squash = 1.0
    br.inputs["Scale"].default_value = 0.25
    br.inputs["Mortar Size"].default_value = 0.08
    br.inputs["Brick Width"].default_value = 0.5
    br.inputs["Row Height"].default_value = 0.6
    br.inputs["Color1"].default_value = (0.02, 0.04, 0.06, 1)
    br.inputs["Color2"].default_value = (0.05, 0.07, 0.09, 1)
    br.inputs["Mortar"].default_value = (*base, 1)
    nt.links.new(tc.outputs["Object"], br.inputs["Vector"])
    nt.links.new(br.outputs["Color"], b.inputs["Base Color"])
    noise = nt.nodes.new("ShaderNodeTexWhiteNoise")
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
    # ventanas encendidas al azar (cálido)
    cell = nt.nodes.new("ShaderNodeTexVoronoi")
    cell.inputs["Scale"].default_value = 0.6
    cell.inputs["Randomness"].default_value = 0.0
    nt.links.new(tc.outputs["Object"], cell.inputs["Vector"])
    gt = nt.nodes.new("ShaderNodeMath")
    gt.operation = "GREATER_THAN"
    gt.inputs[1].default_value = 0.72 + (seed % 5) * 0.03
    nt.links.new(cell.outputs["Distance"], gt.inputs[0])
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    nt.links.new(br.outputs["Fac"], inv.inputs[1])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    nt.links.new(gt.outputs[0], mul.inputs[0])
    nt.links.new(inv.outputs[0], mul.inputs[1])
    b.inputs["Emission Color"].default_value = (1.0, 0.72, 0.4, 1)
    nt.links.new(mul.outputs[0], b.inputs["Emission Strength"])
    b.inputs["Roughness"].default_value = 0.2
    b.inputs["Metallic"].default_value = 0.4
    return m


# ─────────────────────────── geometría ───────────────────────────

def ribbon(name, track, inner, outer, z=0.0, step=2.0, material=None, z_outer=None, uv_scale=1.0):
    """Banda a lo largo del circuito entre dos desplazamientos laterales."""
    verts, faces, uvs = [], [], []
    n = int(track.length / step)
    for i in range(n):
        s = i * track.length / n
        x1, y1, _ = track.frame(s, inner)
        x2, y2, _ = track.frame(s, outer)
        verts += [(x1, y1, z), (x2, y2, z if z_outer is None else z_outer)]
    for i in range(n):
        a, b = 2 * i, 2 * ((i + 1) % n)
        faces.append((a, b, b + 1, a + 1))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    uv = me.uv_layers.new(name="UVMap")
    for i, poly in enumerate(me.polygons):
        s0 = i * track.length / n
        s1 = (i + 1) * track.length / n
        for li, vi in zip(poly.loop_indices, poly.vertices):
            k = vi // 2
            s = s0 if k == i else s1
            uv.data[li].uv = (s * uv_scale, (vi % 2))
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if material:
        ob.data.materials.append(material)
    return ob


def wall(name, track, lateral, height, thick, material, step=3.0):
    verts, faces = [], []
    n = int(track.length / step)
    for i in range(n):
        s = i * track.length / n
        xa, ya, _ = track.frame(s, lateral)
        xb, yb, _ = track.frame(s, lateral + thick)
        verts += [(xa, ya, 0), (xa, ya, height), (xb, yb, height), (xb, yb, 0)]
    for i in range(n):
        a, b = 4 * i, 4 * ((i + 1) % n)
        for k in range(3):
            faces.append((a + k, b + k, b + k + 1, a + k + 1))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(material)
    return ob


_CUBES = {}


def box(name, loc, size, rot_z=0.0, material=None):
    """Caja a partir de un cubo compartido por material (instancias: rápido y ligero)."""
    key = material.name if material else "_"
    if key not in _CUBES:
        import bmesh
        me = bpy.data.meshes.new(f"cubo_{key}")
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        uv = bm.loops.layers.uv.new("UVMap")
        for face in bm.faces:
            for i, loop in enumerate(face.loops):
                loop[uv].uv = ((0, 0), (1, 0), (1, 1), (0, 1))[i % 4]
        bm.to_mesh(me)
        bm.free()
        if material:
            me.materials.append(material)
        _CUBES[key] = me
    ob = bpy.data.objects.new(name, _CUBES[key])
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (0, 0, rot_z)
    ob.scale = size
    return ob


def build_world(sun_elev_deg=5.0, sun_rot_deg=-60.0):
    sc = bpy.context.scene
    w = bpy.data.worlds.new("Cielo")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    sky = nt.nodes.new("ShaderNodeTexSky")
    for st in ("MULTIPLE_SCATTERING", "NISHITA"):
        try:
            sky.sky_type = st
            break
        except TypeError:
            continue
    for attr, val in (("sun_elevation", math.radians(sun_elev_deg)), ("sun_rotation", math.radians(sun_rot_deg)), ("sun_disc", True), ("air_density", 1.6), ("dust_density", 3.0), ("aerosol_density", 3.0), ("sun_intensity", 0.6)):
        if hasattr(sky, attr):
            setattr(sky, attr, val)
    bg = nt.nodes["Background"]
    bg.inputs["Strength"].default_value = 0.6
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    sun = bpy.data.lights.new("Sol", "SUN")
    sun.energy = 5.0
    sun.color = (1.0, 0.62, 0.36)
    sun.angle = math.radians(1.2)
    so = bpy.data.objects.new("Sol", sun)
    sc.collection.objects.link(so)
    el, az = math.radians(sun_elev_deg), math.radians(sun_rot_deg)
    to_sun = Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)))
    so.rotation_euler = (-to_sun).to_track_quat("-Z", "Y").to_euler()


def build_track(track):
    sc = bpy.context.scene
    W = ROAD_WIDTH / 2
    ribbon("Asfalto", track, -W, W, 0.0, material=asphalt_mat())
    white = mat("LineaBlanca", (0.85, 0.85, 0.82), 0.5)
    ribbon("LineaIzq", track, W - 0.45, W - 0.25, 0.005, material=white)
    ribbon("LineaDer", track, -W + 0.25, -W + 0.45, 0.005, material=white)
    curb = striped_mat("Piano", (0.75, 0.03, 0.02), (0.9, 0.9, 0.88), 3.0)
    ribbon("PianoIzq", track, W, W + 1.6, 0.03, material=curb, z_outer=0.0)
    ribbon("PianoDer", track, -W - 1.6, -W, 0.0, material=curb, z_outer=0.03)
    grass = mat("Cesped", (0.07, 0.16, 0.035), 0.85)
    ribbon("CespedIzq", track, W + 1.6, W + 26, -0.01, material=grass, step=4)
    ribbon("CespedDer", track, -W - 26, -W - 1.6, -0.01, material=grass, step=4)
    barrier = striped_mat("Barrera", (0.85, 0.85, 0.85), (0.8, 0.05, 0.03), 4.0)
    wall("MuroIzq", track, W + 26, 1.1, 0.5, barrier)
    wall("MuroDer", track, -W - 26.5, 1.1, 0.5, barrier)
    # Suelo general y línea de meta
    ground = mat("Suelo", (0.09, 0.09, 0.085), 0.9)
    bpy.ops.mesh.primitive_plane_add(size=3000, location=(0, 0, -0.05))
    bpy.context.active_object.data.materials.append(ground)
    x, y, h = track.frame(0.0, 0)
    fin = box("LineaMeta", (x, y, 0.012), (1.6, ROAD_WIDTH, 0.01), h, checker_mat())
    # Ajuste de UV de la meta para cuadros de 0.8 m
    for poly in fin.data.polygons:
        for li in poly.loop_indices:
            u, v = fin.data.uv_layers.active.data[li].uv
            fin.data.uv_layers.active.data[li].uv = (u * 2, v * 20)
    # Pórtico de salida con semáforo
    gantry = mat("Portico", (0.05, 0.05, 0.055), 0.4, 0.6)
    xg, yg, hg = track.frame(14.0, 0)
    for side in (-1, 1):
        px, py, _ = track.frame(14.0, side * (W + 2))
        box("PilarPortico", (px, py, 4), (0.6, 0.6, 8), hg, gantry)
    box("VigaPortico", (xg, yg, 7.6), (1.0, ROAD_WIDTH + 5, 1.2), hg, gantry)
    lights = []
    for i in range(5):
        lx, ly, _ = track.frame(13.4, (i - 2) * 1.6)
        m = mat(f"LuzSalida{i}", (0.1, 0, 0), 0.3, emit=(1, 0.02, 0.01), emit_strength=0.0)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.38, location=(lx, ly, 7.6), segments=16, ring_count=8)
        o = bpy.context.active_object
        o.data.materials.append(m)
        lights.append(m)
    return lights


def build_grandstands(track):
    """Gradas con público a lo largo de la recta principal."""
    rnd = random.Random(4)
    stand_mat = mat("Grada", (0.25, 0.26, 0.28), 0.7)
    crowd_mats = [mat(f"Publico{i}", c, 0.8) for i, c in enumerate([(0.7, 0.05, 0.03), (0.9, 0.7, 0.05), (0.05, 0.2, 0.6), (0.9, 0.9, 0.9), (0.08, 0.08, 0.08)])]
    roof = mat("Techo", (0.8, 0.8, 0.82), 0.35, 0.5)
    for s0 in range(-160, 220, 38):
        s = s0 % track.length
        for side, base in ((1, ROAD_WIDTH / 2 + 30), (-1, -(ROAD_WIDTH / 2 + 31))):
            if side == -1 and s0 > 120:
                continue
            for row in range(6):
                lat = side * (abs(base) + row * 1.6)
                x, y, h = track.frame(s, lat)
                hz = 0.5 + row * 0.9
                box("Escalon", (x, y, hz / 2), (34, 1.6, hz), h, stand_mat)
                # espectadores: cubos pequeños de colores
                for k in range(16):
                    if rnd.random() < 0.25:
                        continue
                    sx, sy, _ = track.frame(s - 16 + k * 2.1 + rnd.uniform(-0.4, 0.4), lat)
                    box("Fan", (sx, sy, 0.5 + row * 0.9 + 0.37), (0.5, 0.45, 0.75), h, rnd.choice(crowd_mats))
            xr, yr, _ = track.frame(s, side * (abs(base) + 5))
            box("TechoGrada", (xr, yr, 7.8), (36, 12, 0.3), h, roof).rotation_euler.x = math.radians(-6 * side)


def build_city(track):
    """Rascacielos alrededor del circuito (estética de ciudad de mundo abierto)."""
    rnd = random.Random(11)
    mats = [windows_mat(f"Edificio{i}", c, i) for i, c in enumerate([(0.32, 0.33, 0.36), (0.45, 0.4, 0.35), (0.2, 0.22, 0.27), (0.5, 0.5, 0.52)])]
    glass = mat("CristalTorre", (0.1, 0.16, 0.22), 0.05, 0.9)
    placed = 0
    for i in range(260):
        ang = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(560, 1100)
        x, y = math.cos(ang) * r * 0.95 + 20, math.sin(ang) * r * 0.75
        tall = rnd.random() < 0.25
        h = rnd.uniform(60, 190) if tall else rnd.uniform(18, 70)
        w = rnd.uniform(18, 40)
        d = rnd.uniform(18, 40)
        box("Edificio", (x, y, h / 2), (w, d, h), rnd.uniform(0, 3.14), glass if (tall and rnd.random() < 0.4) else rnd.choice(mats))
        placed += 1
    # Farolas/torres de iluminación junto al circuito
    pole = mat("Torre", (0.2, 0.2, 0.22), 0.4, 0.7)
    lamp = mat("Foco", (1, 1, 1), 0.3, emit=(1, 0.9, 0.75), emit_strength=8)
    for s in range(0, int(track.length), 120):
        x, y, h = track.frame(s, ROAD_WIDTH / 2 + 22)
        box("Poste", (x, y, 9), (0.4, 0.4, 18), 0, pole)
        box("Lampara", (x, y, 18.2), (2.4, 0.6, 0.5), h, lamp)
    return placed


def import_car(color, name, wing=False):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=CAR_GLB)
    objs = [o for o in bpy.data.objects if o not in before]
    root = next(o for o in objs if o.parent is None)
    paint = car_paint(f"Pintura{name}", color)
    for o in objs:
        if o.type != "MESH":
            continue
        for i, slot in enumerate(o.material_slots):
            if slot.material and slot.material.name.startswith("Paint"):
                o.material_slots[i].material = paint
        if "License" in o.name:
            o.hide_render = True
    # Contenedor: la carrocería mira a -Y en el modelo; lo giramos para que mire a +X
    holder = bpy.data.objects.new(f"Coche{name}", None)
    bpy.context.scene.collection.objects.link(holder)
    root.parent = holder
    root.rotation_euler = (0, 0, math.radians(90))
    root.location = (0, 0, 0.0)
    if wing:
        wm = mat(f"Aleron{name}", (0.02, 0.02, 0.02), 0.35, 0.3)
        for dx in (-0.45, 0.45):
            bpy.ops.mesh.primitive_cube_add(size=1, location=(-1.95, dx, 1.12))
            st = bpy.context.active_object
            st.scale = (0.08, 0.05, 0.28)
            st.data.materials.append(wm)
            st.parent = holder
        bpy.ops.mesh.primitive_cube_add(size=1, location=(-2.05, 0, 1.3))
        w = bpy.context.active_object
        w.scale = (0.36, 1.95, 0.05)
        w.rotation_euler = (0, math.radians(-8), 0)
        w.data.materials.append(wm)
        w.parent = holder
        holder.scale = (1.03, 1.06, 0.95)
    wheels = {k: next(o for o in objs if o.name.startswith(k)) for k in ("WheelFrontL", "WheelFrontR", "WheelRearL", "WheelRearR")}
    for wo in wheels.values():
        wo.rotation_mode = "XYZ"
    return holder, wheels, objs


def setup_render(samples, scale, fps):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.06
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except TypeError:
        pass
    sc.cycles.max_bounces = 4
    sc.cycles.diffuse_bounces = 2
    sc.cycles.glossy_bounces = 2
    sc.cycles.transmission_bounces = 4
    sc.cycles.transparent_max_bounces = 4
    sc.cycles.sample_clamp_indirect = 4.0
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.render.use_persistent_data = True
    sc.render.resolution_x = 1080
    sc.render.resolution_y = 1920
    sc.render.resolution_percentage = scale
    sc.render.fps = fps
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.45
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 93
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Punchy"
    except TypeError:
        pass
    sc.view_settings.exposure = 0.3


def animate(race, cars, cams, lights, f0, f1):
    sc = bpy.context.scene
    fps = race.spec.fps
    cam_ob = cams
    R_WHEEL = 0.385
    for f in range(f0, f1 + 1):
        vt = f / fps
        t = race.sim_time(vt)
        sc.frame_set(f)
        for key, (holder, wheels, _) in cars.items():
            st = race.car(key, t)
            holder.location = (st.x, st.y, 0.0)
            roll = -st.drift * 0.25 - st.steer * 0.04 * min(1, st.speed / 40)
            pitch = 0.0
            holder.rotation_euler = (roll, pitch, st.yaw)
            holder.keyframe_insert("location", frame=f)
            holder.keyframe_insert("rotation_euler", frame=f)
            spin = -st.s / R_WHEEL
            for name, wo in wheels.items():
                steer = st.steer if "Front" in name else 0.0
                wo.rotation_euler = (spin, 0, steer)
                wo.keyframe_insert("rotation_euler", frame=f)
        pos, look, lens, roll = race.camera(vt)
        cam_ob.location = pos
        d = Vector(look) - Vector(pos)
        rot = d.to_track_quat("-Z", "Y").to_euler()
        rot.rotate_axis("Z", roll)
        cam_ob.rotation_euler = rot
        cam_ob.data.lens = lens
        cam_ob.data.dof.focus_distance = max(1.0, d.length)
        cam_ob.keyframe_insert("location", frame=f)
        cam_ob.keyframe_insert("rotation_euler", frame=f)
        cam_ob.data.keyframe_insert("lens", frame=f)
        cam_ob.data.dof.keyframe_insert("focus_distance", frame=f)
        # Semáforo: se encienden 5 luces y se apagan a la salida
        T0 = race.t_go
        for i, m in enumerate(lights):
            on = (T0 - 3.0 + i * 0.5) <= t < T0
            b = m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
            b.default_value = 40.0 if on else 0.0
            b.keyframe_insert("default_value", frame=f)
    # Interpolación lineal para que el desenfoque de movimiento sea correcto
    for ob in [cam_ob] + [h for h, _, _ in cars.values()] + [w for _, ws, _ in cars.values() for w in ws.values()]:
        ad = ob.animation_data
        if ad and ad.action:
            for fc in getattr(ad.action, "fcurves", []):
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"


def build(spec, samples=20, scale=100):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    race = Race(spec)
    setup_render(samples, scale, spec.fps)
    build_world()
    lights = build_track(race.track)
    build_grandstands(race.track)
    build_city(race.track)
    car_a = import_car(spec.car_a_color, "A")
    car_b = import_car(spec.car_b_color, "B", wing=True)
    cam_data = bpy.data.cameras.new("Camara")
    cam_data.sensor_width = 36
    cam_data.dof.use_dof = True
    cam_data.dof.aperture_fstop = 4.0
    cam_data.clip_end = 5000
    cam = bpy.data.objects.new("Camara", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    sc = bpy.context.scene
    sc.frame_start = 0
    sc.frame_end = race.frames - 1
    return race, {"a": car_a, "b": car_b}, cam, lights


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out/frames")
    ap.add_argument("--frames", nargs=2, type=int, default=None)
    ap.add_argument("--every", type=int, default=1, help="renderizar 1 de cada N fotogramas (pruebas)")
    ap.add_argument("--samples", type=int, default=20)
    ap.add_argument("--scale", type=int, default=100, help="porcentaje de 1080x1920")
    ap.add_argument("--spec", default=None)
    ap.add_argument("--save-blend", default=None)
    a = ap.parse_args(argv)
    spec = RaceSpec.from_json(a.spec) if a.spec else RaceSpec()
    race, cars, cam, lights = build(spec, a.samples, a.scale)
    f0, f1 = a.frames if a.frames else (0, race.frames - 1)
    f1 = min(f1, race.frames - 1)
    # animamos un margen extra para el desenfoque de movimiento
    animate(race, cars, cam, lights, max(0, f0 - 1), min(race.frames - 1, f1 + 1))
    if a.save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.save_blend))
    os.makedirs(a.out, exist_ok=True)
    sc = bpy.context.scene
    import time
    for f in range(f0, f1 + 1, a.every):
        t0 = time.time()
        sc.frame_set(f)
        sc.render.filepath = os.path.join(os.path.abspath(a.out), f"f{f:05d}.jpg")
        bpy.ops.render.render(write_still=True)
        print(f"[render] fotograma {f} ({race.shot_at(f / spec.fps)['type']}) en {time.time() - t0:.1f} s", flush=True)


if __name__ == "__main__":
    main()
