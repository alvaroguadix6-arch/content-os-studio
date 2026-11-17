"""Escena 3D «¿Qué pasaría si fueras inmortal?» (Blender / Cycles).

Uso:  python scene.py --out frames/ --frames 0 1709 [--samples 16] [--scale 100] [--every 1]

Todo es geometría y materiales 3D generados por código (sin recursos de terceros, salvo el
modelo de coche CC BY 4.0 que ya usa Content-OS para el tráfico del time-lapse).
"""
import argparse
import math
import os
import random
import sys
import time

import bpy
import bmesh
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from story import CITY, EARTH, EARTH_R, LIGHTNING_T, SCORCHED, SPACE, Story, StorySpec  # noqa: E402

CAR_GLB = os.environ.get("CAR_GLB", os.path.join(os.path.dirname(HERE), "assets", "CarConcept.glb"))


# ───────────────────────── utilidades ─────────────────────────

def link(ob):
    bpy.context.scene.collection.objects.link(ob)
    return ob


def principled(name, color=(0.5, 0.5, 0.5), rough=0.5, metal=0.0, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m


def node(nt, kind, **inputs):
    n = nt.nodes.new(kind)
    for k, v in inputs.items():
        if k in n.inputs:
            n.inputs[k].default_value = v
        else:
            setattr(n, k, v)
    return n


_UNIT = {}


def cube(name, loc, size, rot=(0, 0, 0), mat=None):
    key = mat.name if mat else "_"
    if key not in _UNIT:
        me = bpy.data.meshes.new("cubo_" + key)
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bm.to_mesh(me)
        bm.free()
        if mat:
            me.materials.append(mat)
        _UNIT[key] = me
    ob = link(bpy.data.objects.new(name, _UNIT[key]))
    ob.location, ob.scale, ob.rotation_euler = loc, size, rot
    return ob


def sphere(name, loc, r, mat, seg=64, ring=32):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=ring, radius=r)
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = link(bpy.data.objects.new(name, me))
    ob.location = loc
    return ob


def plane(name, loc, size, mat):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=size / 2)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = link(bpy.data.objects.new(name, me))
    ob.location = loc
    return ob


def key(obj, path, frame, value=None, interp="BEZIER"):
    if value is not None:
        attr = obj
        parts = path.split(".")
        for p in parts[:-1]:
            attr = getattr(attr, p)
        setattr(attr, parts[-1], value)
    obj.keyframe_insert(path, frame=frame)


def key_input(sock, frame, value):
    sock.default_value = value
    sock.keyframe_insert("default_value", frame=frame)


# ───────────────────────── personaje ─────────────────────────

def build_hero():
    """Figura humana con abrigo largo y capucha (siempre la misma en todo el vídeo)."""
    pts = {
        "pelvis": (0, 0, 0.95, 0.15), "vientre": (0, 0, 1.15, 0.14), "pecho": (0, 0, 1.38, 0.17),
        "cuello": (0, 0, 1.56, 0.06), "cabeza": (0, -0.01, 1.70, 0.11),
        "hombroL": (0.2, 0, 1.47, 0.07), "codoL": (0.25, 0.02, 1.17, 0.05), "manoL": (0.27, -0.02, 0.9, 0.045),
        "hombroR": (-0.2, 0, 1.47, 0.07), "codoR": (-0.25, 0.02, 1.17, 0.05), "manoR": (-0.27, -0.02, 0.9, 0.045),
        "caderaL": (0.1, 0, 0.9, 0.09), "rodillaL": (0.11, -0.01, 0.5, 0.065), "pieL": (0.12, 0.0, 0.08, 0.055), "puntaL": (0.12, -0.16, 0.04, 0.045),
        "caderaR": (-0.1, 0, 0.9, 0.09), "rodillaR": (-0.11, -0.01, 0.5, 0.065), "pieR": (-0.12, 0.0, 0.08, 0.055), "puntaR": (-0.12, -0.16, 0.04, 0.045),
    }
    edges = [("pelvis", "vientre"), ("vientre", "pecho"), ("pecho", "cuello"), ("cuello", "cabeza"),
             ("pecho", "hombroL"), ("hombroL", "codoL"), ("codoL", "manoL"),
             ("pecho", "hombroR"), ("hombroR", "codoR"), ("codoR", "manoR"),
             ("pelvis", "caderaL"), ("caderaL", "rodillaL"), ("rodillaL", "pieL"), ("pieL", "puntaL"),
             ("pelvis", "caderaR"), ("caderaR", "rodillaR"), ("rodillaR", "pieR"), ("pieR", "puntaR")]
    names = list(pts)
    me = bpy.data.meshes.new("Cuerpo")
    me.from_pydata([p[:3] for p in pts.values()], [(names.index(a), names.index(b)) for a, b in edges], [])
    body = link(bpy.data.objects.new("Cuerpo", me))
    body.modifiers.new("piel", "SKIN")
    for i, n in enumerate(names):
        r = pts[n][3]
        body.data.skin_vertices[0].data[i].radius = (r, r)
    body.data.skin_vertices[0].data[0].use_root = True
    sub = body.modifiers.new("suave", "SUBSURF")
    sub.levels = sub.render_levels = 2

    skin = principled("Pantalon", (0.02, 0.02, 0.022), 0.55)
    body.data.materials.append(skin)

    # Abrigo largo (cono abierto abajo) con pliegues
    coat_m = bpy.data.materials.new("Abrigo")
    coat_m.use_nodes = True
    nt = coat_m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.085, 0.065, 0.05, 1)
    b.inputs["Roughness"].default_value = 0.72
    b.inputs["Sheen Weight"].default_value = 0.6
    tex = node(nt, "ShaderNodeTexNoise", Scale=60.0, Detail=8.0)
    bump = node(nt, "ShaderNodeBump", Strength=0.15)
    nt.links.new(tex.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])

    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.29, radius2=0.205, depth=1.08, location=(0, 0.01, 1.0), end_fill_type="NOTHING")
    coat = bpy.context.active_object
    coat.name = "Abrigo"
    coat.data.materials.append(coat_m)
    for p in coat.data.polygons:
        p.use_smooth = True
    sol = coat.modifiers.new("grosor", "SOLIDIFY")
    sol.thickness = 0.02
    disp = coat.modifiers.new("pliegues", "DISPLACE")
    ntex = bpy.data.textures.new("viento", "CLOUDS")
    ntex.noise_scale = 0.35
    disp.texture = ntex
    disp.strength = 0.05
    disp.texture_coords = "OBJECT"
    wind = bpy.data.objects.new("Viento", None)
    link(wind)
    disp.texture_coords_object = wind
    coat.modifiers.new("suave", "SUBSURF").levels = 1

    bpy.ops.mesh.primitive_torus_add(major_radius=0.11, minor_radius=0.05, location=(0, 0.0, 1.55))
    scarf = bpy.context.active_object
    scarf.name = "Manga_bufanda"
    scarf.data.materials.append(principled("Bufanda", (0.25, 0.04, 0.03), 0.8))
    for p in scarf.data.polygons:
        p.use_smooth = True
    # Cinturón
    bpy.ops.mesh.primitive_torus_add(major_radius=0.215, minor_radius=0.018, location=(0, 0.01, 1.08))
    belt = bpy.context.active_object
    belt.name = "Manga_cinturon"
    belt.data.materials.append(principled("Cuero", (0.02, 0.012, 0.008), 0.4))
    # Hombros y mangas del abrigo
    for side in (1, -1):
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.075, depth=0.62, location=(0.235 * side, 0.01, 1.2), rotation=(0, math.radians(-8 * side), 0))
        sl = bpy.context.active_object
        sl.data.materials.append(coat_m)
        sl.modifiers.new("suave", "SUBSURF").levels = 1
        sl.parent = None
        sl.name = "Manga"

    # Capucha: casquete con el interior en sombra (nunca se ve la cara)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.155, location=(0, 0.02, 1.71))
    hood = bpy.context.active_object
    hood.name = "Capucha"
    hood.scale = (0.86, 0.95, 1.0)
    bm = bmesh.new()
    bm.from_mesh(hood.data)
    # abrir la parte delantera
    rem = [f for f in bm.faces if f.calc_center_median().y < -0.07 and f.calc_center_median().z < 0.06]
    bmesh.ops.delete(bm, geom=rem, context="FACES")
    bm.to_mesh(hood.data)
    bm.free()
    hood.data.materials.append(coat_m)
    hood.modifiers.new("grosor", "SOLIDIFY").thickness = 0.015
    for p in hood.data.polygons:
        p.use_smooth = True
    face = sphere("Sombra", (0, -0.005, 1.7), 0.105, principled("Sombra", (0.0, 0.0, 0.0), 1.0), 24, 12)

    hero = bpy.data.objects.new("Heroe", None)
    link(hero)
    for o in (body, coat, hood, face, wind) + tuple(o for o in bpy.data.objects if o.name.startswith("Manga")):
        o.parent = hero
    return hero, wind, body


def build_toon_hero(hero, story, fps):
    """Personaje 2D (estilo dibujos animados) en planos que siempre miran a la cámara.
    Un plano por combinación de expresión/brazos; se muestra el que toca en cada fotograma."""
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), "toon"))
    from character import H as CH, W as CW, draw

    tmp = os.path.join(os.environ.get("TMPDIR", "/tmp"), "contentos_personaje")
    os.makedirs(tmp, exist_ok=True)
    # ocultar la figura 3D
    for ch in hero.children:
        ch.hide_render = True
    combos = sorted({story.expression(f / fps) for f in range(story.frames)})
    planes = {}
    height = 1.85
    width = height * CW / CH
    for face, arms in combos:
        path = os.path.join(tmp, f"{face}_{arms}.png")
        draw(face, arms, look_up=face == "asombrado").save(path)
        img = bpy.data.images.load(path)
        m = bpy.data.materials.new(f"Toon_{face}_{arms}")
        m.use_nodes = True
        m.blend_method = "BLEND" if hasattr(m, "blend_method") else None
        nt = m.node_tree
        nt.nodes.remove(nt.nodes["Principled BSDF"])
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = img
        tex.interpolation = "Cubic"
        em = node(nt, "ShaderNodeEmission", Strength=1.0)
        nt.links.new(tex.outputs["Color"], em.inputs["Color"])
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(tex.outputs["Alpha"], mix.inputs[0])
        nt.links.new(tr.outputs[0], mix.inputs[1])
        nt.links.new(em.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
        me = bpy.data.meshes.new(f"Toon_{face}_{arms}")
        me.from_pydata([(-width / 2, 0, 0), (width / 2, 0, 0), (width / 2, 0, height), (-width / 2, 0, height)], [], [(0, 1, 2, 3)])
        uv = me.uv_layers.new(name="UVMap")
        for li, co in zip(range(4), [(0, 0), (1, 0), (1, 1), (0, 1)]):
            uv.data[li].uv = co
        me.materials.append(m)
        pl = link(bpy.data.objects.new(f"Toon_{face}_{arms}", me))
        pl.parent = hero
        pl.visible_shadow = False
        planes[(face, arms)] = pl
    return planes


def face_camera(planes, cam):
    for pl in planes.values():
        c = pl.constraints.new("LOCKED_TRACK")
        c.target = cam
        c.track_axis = "TRACK_NEGATIVE_Y"
        c.lock_axis = "LOCK_Z"


# ───────────────────────── ciudad (rayo, siglo, ruinas) ─────────────────────────

def city_material():
    """Fachada que cambia con el tiempo según el color del objeto:
    R = futurista (cristal y neón), G = ruina (oscura y con vegetación)."""
    m = bpy.data.materials.new("Fachada")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    info = nt.nodes.new("ShaderNodeObjectInfo")
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(info.outputs["Color"], sep.inputs[0])
    brick = node(nt, "ShaderNodeTexBrick", Scale=0.3, offset=0.0)
    brick.inputs["Mortar Size"].default_value = 0.06
    brick.inputs["Brick Width"].default_value = 0.55
    brick.inputs["Row Height"].default_value = 0.6
    brick.inputs["Color1"].default_value = (0.08, 0.09, 0.11, 1)
    brick.inputs["Color2"].default_value = (0.12, 0.12, 0.14, 1)
    brick.inputs["Mortar"].default_value = (0.42, 0.38, 0.34, 1)
    nt.links.new(geo.outputs["Position"], brick.inputs["Vector"])
    # ventanas encendidas al azar
    vor = node(nt, "ShaderNodeTexVoronoi", Scale=0.55)
    vor.inputs["Randomness"].default_value = 0.0
    nt.links.new(geo.outputs["Position"], vor.inputs["Vector"])
    lit = node(nt, "ShaderNodeMath", operation="GREATER_THAN")
    lit.inputs[1].default_value = 0.7
    nt.links.new(vor.outputs["Distance"], lit.inputs[0])
    win = node(nt, "ShaderNodeMath", operation="SUBTRACT")
    win.inputs[0].default_value = 1.0
    nt.links.new(brick.outputs["Fac"], win.inputs[1])
    lw = node(nt, "ShaderNodeMath", operation="MULTIPLY")
    nt.links.new(lit.outputs[0], lw.inputs[0])
    nt.links.new(win.outputs[0], lw.inputs[1])
    # futurista: líneas de neón cian
    wave = node(nt, "ShaderNodeTexWave", wave_type="BANDS", bands_direction="Z")
    wave.inputs["Scale"].default_value = 0.08
    nt.links.new(geo.outputs["Position"], wave.inputs["Vector"])
    neon = node(nt, "ShaderNodeMath", operation="GREATER_THAN")
    neon.inputs[1].default_value = 0.93
    nt.links.new(wave.outputs["Fac"], neon.inputs[0])
    # ruina: musgo y oscuridad
    moss = node(nt, "ShaderNodeTexNoise", Scale=0.35, Detail=6.0)
    nt.links.new(geo.outputs["Position"], moss.inputs["Vector"])
    base = node(nt, "ShaderNodeMix", data_type="RGBA")
    nt.links.new(sep.outputs[0], base.inputs[0])
    nt.links.new(brick.outputs["Color"], base.inputs[6])
    base.inputs[7].default_value = (0.03, 0.07, 0.1, 1)
    ruin = node(nt, "ShaderNodeMix", data_type="RGBA")
    nt.links.new(sep.outputs[1], ruin.inputs[0])
    nt.links.new(base.outputs[2], ruin.inputs[6])
    mossc = node(nt, "ShaderNodeMix", data_type="RGBA")
    nt.links.new(moss.outputs["Fac"], mossc.inputs[0])
    mossc.inputs[6].default_value = (0.02, 0.02, 0.018, 1)
    mossc.inputs[7].default_value = (0.05, 0.14, 0.03, 1)
    nt.links.new(mossc.outputs[2], ruin.inputs[7])
    nt.links.new(ruin.outputs[2], b.inputs["Base Color"])
    # emisión: ventanas (se apagan en ruina) + neón (futuro)
    e_win = node(nt, "ShaderNodeMath", operation="MULTIPLY")
    nt.links.new(lw.outputs[0], e_win.inputs[0])
    inv_r = node(nt, "ShaderNodeMath", operation="SUBTRACT")
    inv_r.inputs[0].default_value = 1.0
    nt.links.new(sep.outputs[1], inv_r.inputs[1])
    nt.links.new(inv_r.outputs[0], e_win.inputs[1])
    e_neon = node(nt, "ShaderNodeMath", operation="MULTIPLY")
    nt.links.new(neon.outputs[0], e_neon.inputs[0])
    nt.links.new(sep.outputs[0], e_neon.inputs[1])
    e_neon2 = node(nt, "ShaderNodeMath", operation="MULTIPLY")
    nt.links.new(e_neon.outputs[0], e_neon2.inputs[0])
    nt.links.new(inv_r.outputs[0], e_neon2.inputs[1])
    col = node(nt, "ShaderNodeMix", data_type="RGBA")
    nt.links.new(e_neon2.outputs[0], col.inputs[0])
    col.inputs[6].default_value = (1.0, 0.7, 0.4, 1)
    col.inputs[7].default_value = (0.1, 0.9, 1.0, 1)
    nt.links.new(col.outputs[2], b.inputs["Emission Color"])
    tot = node(nt, "ShaderNodeMath", operation="ADD")
    nt.links.new(e_win.outputs[0], tot.inputs[0])
    nt.links.new(e_neon2.outputs[0], tot.inputs[1])
    strength = node(nt, "ShaderNodeMath", operation="MULTIPLY")
    strength.inputs[1].default_value = 3.0
    nt.links.new(tot.outputs[0], strength.inputs[0])
    nt.links.new(strength.outputs[0], b.inputs["Emission Strength"])
    rough = node(nt, "ShaderNodeMath", operation="MULTIPLY_ADD")
    rough.inputs[1].default_value = -0.5
    rough.inputs[2].default_value = 0.65
    nt.links.new(sep.outputs[0], rough.inputs[0])
    nt.links.new(rough.outputs[0], b.inputs["Roughness"])
    met = node(nt, "ShaderNodeMath", operation="MULTIPLY")
    met.inputs[1].default_value = 0.8
    nt.links.new(sep.outputs[0], met.inputs[0])
    nt.links.new(met.outputs[0], b.inputs["Metallic"])
    return m


def build_city(story, fps):
    rnd = random.Random(7)
    fac = city_material()
    asphalt = principled("Asfalto", (0.03, 0.03, 0.032), 0.35)
    walk = principled("Acera", (0.18, 0.17, 0.16), 0.7)
    plane("Calle", (0, 0, 0), 600, asphalt)
    for side in (-1, 1):
        cube("Acera", (side * 9, 0, 0.08), (4, 600, 0.16), mat=walk)
    lamp_m = principled("Farola", (0.05, 0.05, 0.05), 0.4, 0.8)
    bulb = principled("Bombilla", (1, 1, 1), 0.3, emit=(1.0, 0.75, 0.45), strength=25)
    for y in range(-120, 121, 24):
        for side in (-1, 1):
            cube("Farola", (side * 7.6, y, 3), (0.15, 0.15, 6), mat=lamp_m)
            cube("Luz", (side * 7.0, y, 6.0), (1.2, 0.3, 0.15), mat=bulb)
    buildings = []
    t1 = story.shots[1]["start"]
    t2 = story.shots[1]["end"]
    t3 = story.shots[2]["end"]
    for side in (-1, 1):
        y = -160
        while y < 160:
            w = rnd.uniform(9, 18)
            d = rnd.uniform(10, 18)
            h = rnd.uniform(10, 45)
            x = side * (11 + d / 2 + rnd.uniform(0, 2))
            ob = cube("Edificio", (x, y + w / 2, h / 2), (d, w, h), mat=fac)
            ob["h"] = h
            buildings.append(ob)
            y += w + rnd.uniform(0.5, 3)
    for k in range(120):  # segunda y tercera fila (skyline)
        x = rnd.choice((-1, 1)) * rnd.uniform(40, 220)
        y = rnd.uniform(-220, 260)
        h = rnd.uniform(25, 110)
        ob = cube("Torre", (x, y, h / 2), (rnd.uniform(14, 30), rnd.uniform(14, 30), h), mat=fac)
        ob["h"] = h
        buildings.append(ob)
    # Animación: presente → +100 años (más altos, futuristas) → +500 años (ruinas)
    F = lambda s: int(round(s * fps))  # noqa: E731
    for ob in buildings:
        h0 = ob["h"]
        grow = rnd.uniform(1.4, 2.6)
        delay = rnd.uniform(0, 0.5)
        ob.color = (0, 0, 0, 1)
        key(ob, "color", F(t1 + 0.3 + delay * 3))
        key(ob, "scale", F(t1 + 0.3 + delay * 3))
        key(ob, "location", F(t1 + 0.3 + delay * 3))
        ob.color = (1, 0, 0, 1)
        ob.scale.z = h0 * grow
        ob.location.z = h0 * grow / 2
        key(ob, "color", F(t1 + 4 + delay * 8))
        key(ob, "scale", F(t1 + 4 + delay * 8))
        key(ob, "location", F(t1 + 4 + delay * 8))
        key(ob, "color", F(t2 - 0.2))
        key(ob, "scale", F(t2 - 0.2))
        key(ob, "location", F(t2 - 0.2))
        # corte a ruinas: derrumbadas e inclinadas
        ob.color = (0, 1, 0, 1)
        broken = rnd.uniform(0.15, 0.55)
        ob.scale.z = h0 * grow * broken
        ob.location.z = h0 * grow * broken / 2 - rnd.uniform(0, 2)
        ob.rotation_euler = (rnd.uniform(-0.08, 0.08), rnd.uniform(-0.08, 0.08), ob.rotation_euler.z)
        for attr in ("color", "scale", "location", "rotation_euler"):
            key(ob, attr, F(t2))
            key(ob, attr, F(t3))
    # Tráfico del time-lapse: coches cruzando muy rápido (estelas con desenfoque de movimiento)
    cars = []
    if os.path.exists(CAR_GLB):
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=CAR_GLB)
        car_objs = [o for o in bpy.data.objects if o not in before]
        root = next(o for o in car_objs if o.parent is None)
        root.location = (0, 1000, -50)  # plantilla oculta
        for i in range(6):
            inst = bpy.data.objects.new(f"Trafico{i}", None)
            inst.instance_type = "COLLECTION"
            cars.append(inst)
        coll = bpy.data.collections.new("CochePlantilla")
        for o in car_objs:
            for c in o.users_collection:
                c.objects.unlink(o)
            coll.objects.link(o)
        root.location = (0, 0, 0)
        root.rotation_euler = (0, 0, 0)
        for i, inst in enumerate(cars):
            inst.instance_collection = coll
            link(inst)
            lane = -3.5 if i % 2 else 3.5
            direction = 1 if i % 2 else -1
            inst.rotation_euler = (0, 0, 0 if direction > 0 else math.pi)
            inst.location = (lane, -2000, 0)
            key(inst, "location", F(t1))
            for k in range(8):
                ts = t1 + 0.4 + k * 1.1 + i * 0.18
                if ts > t2 - 0.6:
                    break
                inst.location = (lane, -140 * direction, 0)
                key(inst, "location", F(ts))
                inst.location = (lane, 140 * direction, 0)
                key(inst, "location", F(ts + 0.45))
                inst.location = (lane, -2000, 0)
                key(inst, "location", F(ts + 0.47))
            inst.location = (lane, -2000, 0)
            key(inst, "location", F(t2))
    return buildings


def build_ghosts(story, fps, body_mesh_obj):
    """Generaciones que aparecen y se desvanecen alrededor del protagonista."""
    m = bpy.data.materials.new("Fantasma")
    m.use_nodes = True
    nt = m.node_tree
    out = nt.nodes["Material Output"]
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    em = node(nt, "ShaderNodeEmission", Strength=2.5)
    em.inputs["Color"].default_value = (0.55, 0.75, 1.0, 1)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    info = nt.nodes.new("ShaderNodeObjectInfo")
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(info.outputs["Color"], sep.inputs[0])
    fres = node(nt, "ShaderNodeLayerWeight", Blend=0.6)
    mul = node(nt, "ShaderNodeMath", operation="MULTIPLY")
    nt.links.new(fres.outputs["Facing"], mul.inputs[0])
    nt.links.new(sep.outputs[2], mul.inputs[1])
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mul.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    # malla del cuerpo ya "aplicada" (sin abrigo)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(body_mesh_obj.evaluated_get(dg))
    me.materials.clear()
    me.materials.append(m)
    rnd = random.Random(3)
    t0, t1 = story.shots[2]["start"], story.shots[2]["end"]
    F = lambda s: int(round(s * fps))  # noqa: E731
    waves = 5
    for w in range(waves):
        ws = t0 + 0.4 + w * (t1 - t0 - 1) / waves
        for k in range(9):
            ang = rnd.uniform(0, 2 * math.pi)
            r = rnd.uniform(2.0, 8.0)
            g = link(bpy.data.objects.new("Generacion", me))
            g.location = (math.cos(ang) * r, math.sin(ang) * r, 0)
            g.rotation_euler = (0, 0, rnd.uniform(0, 6.28))
            sc = rnd.uniform(0.85, 1.08)
            g.scale = (sc, sc, sc)
            g.color = (0, 0, 0, 1)
            g.hide_render = True
            g.keyframe_insert("hide_render", frame=0)
            g.keyframe_insert("hide_render", frame=F(ws) - 1)
            g.hide_render = False
            g.keyframe_insert("hide_render", frame=F(ws))
            g.keyframe_insert("hide_render", frame=F(ws + 1.9))
            g.hide_render = True
            g.keyframe_insert("hide_render", frame=F(ws + 1.9) + 1)
            key(g, "color", 0)
            key(g, "color", F(ws))
            g.color = (0, 0, 0.9, 1)
            key(g, "color", F(ws + 0.6))
            key(g, "color", F(ws + 1.2))
            g.color = (0, 0, 0, 1)
            key(g, "color", F(ws + 1.9))


def build_lightning():
    m = principled("Rayo", (1, 1, 1), 0.5, emit=(0.75, 0.85, 1.0), strength=0.0)
    pts = [(0, 0, 60)]
    rnd = random.Random(5)
    z = 60
    x = y = 0
    while z > 1.8:
        z -= rnd.uniform(2, 6)
        x += rnd.uniform(-1.5, 1.5)
        y += rnd.uniform(-1.5, 1.5)
        pts.append((x * min(1, z / 20), y * min(1, z / 20), max(z, 1.8)))
    cu = bpy.data.curves.new("Rayo", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.06
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for p, c in zip(sp.points, pts):
        p.co = (*c, 1)
    ob = link(bpy.data.objects.new("Rayo", cu))
    ob.data.materials.append(m)
    return ob, m


# ───────────────────────── Tierra, gigante roja y espacio ─────────────────────────

def build_earth(story, fps):
    m = bpy.data.materials.new("Tierra")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    noise = node(nt, "ShaderNodeTexNoise", noise_dimensions="4D", Scale=1.6, Detail=8.0, Roughness=0.6)
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
    land = node(nt, "ShaderNodeValToRGB")
    land.color_ramp.elements[0].position = 0.5
    land.color_ramp.elements[1].position = 0.53
    nt.links.new(noise.outputs["Fac"], land.inputs["Fac"])
    ocean = (0.01, 0.05, 0.2, 1)
    green = (0.05, 0.16, 0.04, 1)
    c1 = node(nt, "ShaderNodeMix", data_type="RGBA")
    nt.links.new(land.outputs["Color"], c1.inputs[0])
    c1.inputs[6].default_value = ocean
    c1.inputs[7].default_value = green
    # hielo (glaciación) y desierto (océanos evaporados)
    ice = node(nt, "ShaderNodeMix", data_type="RGBA")
    ice.inputs[7].default_value = (0.85, 0.9, 0.95, 1)
    nt.links.new(c1.outputs[2], ice.inputs[6])
    desert = node(nt, "ShaderNodeMix", data_type="RGBA")
    desert.inputs[7].default_value = (0.35, 0.16, 0.06, 1)
    nt.links.new(ice.outputs[2], desert.inputs[6])
    nt.links.new(desert.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.6
    earth = sphere("Tierra", EARTH, EARTH_R, m, 128, 64)
    # luces de ciudades en el lado nocturno (se apagan)
    lights = node(nt, "ShaderNodeTexVoronoi", Scale=40.0)
    nt.links.new(tc.outputs["Object"], lights.inputs["Vector"])
    city = node(nt, "ShaderNodeMath", operation="LESS_THAN")
    city.inputs[1].default_value = 0.08
    nt.links.new(lights.outputs["Distance"], city.inputs[0])
    on_land = node(nt, "ShaderNodeMath", operation="MULTIPLY")
    nt.links.new(city.outputs[0], on_land.inputs[0])
    nt.links.new(land.outputs["Color"], on_land.inputs[1])
    lmul = node(nt, "ShaderNodeMath", operation="MULTIPLY")
    nt.links.new(on_land.outputs[0], lmul.inputs[0])
    nt.links.new(lmul.outputs[0], b.inputs["Emission Strength"])
    b.inputs["Emission Color"].default_value = (1.0, 0.7, 0.35, 1)
    # atmósfera
    atm_m = bpy.data.materials.new("Atmosfera")
    atm_m.use_nodes = True
    ant = atm_m.node_tree
    ant.nodes.remove(ant.nodes["Principled BSDF"])
    lw = node(ant, "ShaderNodeLayerWeight", Blend=0.08)
    pw = node(ant, "ShaderNodeMath", operation="POWER")
    pw.inputs[1].default_value = 3.0
    ant.links.new(lw.outputs["Facing"], pw.inputs[0])
    em = node(ant, "ShaderNodeEmission", Strength=1.6)
    em.inputs["Color"].default_value = (0.3, 0.55, 1.0, 1)
    tr = ant.nodes.new("ShaderNodeBsdfTransparent")
    mx = ant.nodes.new("ShaderNodeMixShader")
    ant.links.new(pw.outputs[0], mx.inputs[0])
    ant.links.new(tr.outputs[0], mx.inputs[1])
    ant.links.new(em.outputs[0], mx.inputs[2])
    ant.links.new(mx.outputs[0], ant.nodes["Material Output"].inputs["Surface"])
    sphere("Atmosfera", EARTH, EARTH_R * 1.025, atm_m, 96, 48)
    # luz del Sol para la Tierra
    sun = bpy.data.lights.new("SolTierra", "SUN")
    sun.energy = 5
    so = link(bpy.data.objects.new("SolTierra", sun))
    so.rotation_euler = (math.radians(90), 0, math.radians(35))
    # animación (segundos de la escena)
    t0, t1 = story.shots[3]["start"], story.shots[3]["end"]
    F = lambda s: int(round(s * fps))  # noqa: E731
    w = noise.inputs["W"]
    key_input(w, F(t0), 0.0)
    key_input(w, F(t1), 2.2)  # deriva continental
    key_input(lmul.inputs[1], F(t0), 6.0)
    key_input(lmul.inputs[1], F(t0 + 3.5), 0.0)
    key_input(ice.inputs[0], F(t0 + 3.0), 0.0)
    key_input(ice.inputs[0], F(t0 + 4.2), 0.75)
    key_input(ice.inputs[0], F(t0 + 6.4), 0.0)
    key_input(desert.inputs[0], F(t0 + 7.3), 0.0)
    key_input(desert.inputs[0], F(t1 - 0.5), 1.0)
    key_input(em.inputs["Strength"], F(t0 + 7.3), 1.6)
    key_input(em.inputs["Strength"], F(t1 - 0.5), 0.2)
    return earth


def build_scorched(story, fps):
    """Llanura abrasada y el Sol convertido en gigante roja (luego enana blanca)."""
    sx, sy, sz = SCORCHED
    m = bpy.data.materials.new("Roca")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    vor = node(nt, "ShaderNodeTexVoronoi", Scale=1.6, feature="DISTANCE_TO_EDGE")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
    crack = node(nt, "ShaderNodeMath", operation="LESS_THAN")
    crack.inputs[1].default_value = 0.012
    nt.links.new(vor.outputs["Distance"], crack.inputs[0])
    b.inputs["Base Color"].default_value = (0.06, 0.035, 0.025, 1)
    b.inputs["Roughness"].default_value = 0.9
    b.inputs["Emission Color"].default_value = (1.0, 0.25, 0.02, 1)
    em_k = node(nt, "ShaderNodeMath", operation="MULTIPLY")
    em_k.inputs[1].default_value = 5.0
    nt.links.new(crack.outputs[0], em_k.inputs[0])
    nt.links.new(em_k.outputs[0], b.inputs["Emission Strength"])
    bump = node(nt, "ShaderNodeBump", Strength=0.6)
    rock = node(nt, "ShaderNodeTexNoise", Scale=3.0, Detail=10.0)
    nt.links.new(tc.outputs["Object"], rock.inputs["Vector"])
    nt.links.new(rock.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    ground = plane("Llanura", (sx, sy, 0), 800, m)
    sub = ground.modifiers.new("relieve", "SUBSURF")
    sub.subdivision_type = "SIMPLE"
    sub.levels = sub.render_levels = 6
    disp = ground.modifiers.new("dunas", "DISPLACE")
    tx = bpy.data.textures.new("rocas", "CLOUDS")
    tx.noise_scale = 25
    disp.texture = tx
    disp.strength = 4.0
    ground.location.z = -2.0
    # Sol: gigante roja con granulación
    sm = bpy.data.materials.new("GiganteRoja")
    sm.use_nodes = True
    snt = sm.node_tree
    snt.nodes.remove(snt.nodes["Principled BSDF"])
    stc = snt.nodes.new("ShaderNodeTexCoord")
    gran = node(snt, "ShaderNodeTexNoise", Scale=5.0, Detail=10.0)
    snt.links.new(stc.outputs["Object"], gran.inputs["Vector"])
    ramp = node(snt, "ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.35, 0.02, 0.005, 1)
    ramp.color_ramp.elements[1].color = (0.9, 0.18, 0.03, 1)
    snt.links.new(gran.outputs["Fac"], ramp.inputs["Fac"])
    sem = node(snt, "ShaderNodeEmission", Strength=1.8)
    snt.links.new(ramp.outputs["Color"], sem.inputs["Color"])
    snt.links.new(sem.outputs[0], snt.nodes["Material Output"].inputs["Surface"])
    sun = sphere("GiganteRoja", (sx, sy + 900, 120), 60, sm, 96, 48)
    t0, t1 = story.shots[4]["start"], story.shots[4]["end"]
    F = lambda s: int(round(s * fps))  # noqa: E731
    # crece, ocupa medio cielo, y al final colapsa en una enana blanca
    for t, s_ in ((t0, 1.0), (t0 + 5.5, 6.5), (t0 + 6.4, 6.6), (t0 + 7.0, 0.04), (t1, 0.04)):
        sun.scale = (s_, s_, s_)
        key(sun, "scale", F(t))
    key_input(sem.inputs["Strength"], F(t0 + 6.6), 1.8)
    key_input(sem.inputs["Strength"], F(t0 + 7.0), 400.0)
    light = bpy.data.lights.new("LuzRoja", "SUN")
    light.color = (1.0, 0.35, 0.12)
    lo = link(bpy.data.objects.new("LuzRoja", light))
    lo.rotation_euler = (math.radians(-80), 0, 0)
    for t, e in ((t0, 2.0), (t0 + 5.5, 8.0), (t0 + 6.6, 8.0), (t0 + 7.1, 0.3), (t1, 0.3)):
        light.energy = e
        light.keyframe_insert("energy", frame=F(t))
    return sun


def build_world(story, fps):
    """Mundo: cielo físico (ciudad) ↔ campo de estrellas (espacio), animado por escena."""
    sc = bpy.context.scene
    w = bpy.data.worlds.new("Mundo")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    sky = nt.nodes.new("ShaderNodeTexSky")
    for st in ("MULTIPLE_SCATTERING", "NISHITA"):
        try:
            sky.sky_type = st
            break
        except TypeError:
            pass
    sky.sun_elevation = math.radians(4)
    sky.sun_rotation = math.radians(200)
    # estrellas
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vor = node(nt, "ShaderNodeTexVoronoi", Scale=260.0)
    nt.links.new(tc.outputs["Generated"], vor.inputs["Vector"])
    star = node(nt, "ShaderNodeMath", operation="LESS_THAN")
    star.inputs[1].default_value = 0.05
    nt.links.new(vor.outputs["Distance"], star.inputs[0])
    neb = node(nt, "ShaderNodeTexNoise", Scale=2.0, Detail=6.0)
    nt.links.new(tc.outputs["Generated"], neb.inputs["Vector"])
    nebc = node(nt, "ShaderNodeValToRGB")
    nebc.color_ramp.elements[0].position = 0.5
    nebc.color_ramp.elements[0].color = (0, 0, 0, 1)
    nebc.color_ramp.elements[1].color = (0.08, 0.03, 0.14, 1)
    nt.links.new(neb.outputs["Fac"], nebc.inputs["Fac"])
    stars = node(nt, "ShaderNodeMix", data_type="RGBA", blend_type="ADD")
    stars.inputs[0].default_value = 1.0
    nt.links.new(nebc.outputs["Color"], stars.inputs[6])
    nt.links.new(star.outputs[0], stars.inputs[7])
    # tormenta: cielo oscuro y nublado para el gancho
    storm = node(nt, "ShaderNodeMix", data_type="RGBA")
    nt.links.new(sky.outputs["Color"], storm.inputs[6])
    storm.inputs[7].default_value = (0.02, 0.025, 0.035, 1)
    # cielo rojizo de la llanura abrasada
    red = node(nt, "ShaderNodeMix", data_type="RGBA")
    nt.links.new(storm.outputs[2], red.inputs[6])
    grad_tc = tc
    sepz = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(grad_tc.outputs["Generated"], sepz.inputs[0])
    redramp = node(nt, "ShaderNodeValToRGB")
    redramp.color_ramp.elements[0].position = 0.5
    redramp.color_ramp.elements[0].color = (0.35, 0.06, 0.015, 1)
    redramp.color_ramp.elements[1].position = 0.75
    redramp.color_ramp.elements[1].color = (0.01, 0.002, 0.004, 1)
    nt.links.new(sepz.outputs["Z"], redramp.inputs["Fac"])
    nt.links.new(redramp.outputs["Color"], red.inputs[7])
    space = node(nt, "ShaderNodeMix", data_type="RGBA")
    nt.links.new(red.outputs[2], space.inputs[6])
    nt.links.new(stars.outputs[2], space.inputs[7])
    nt.links.new(space.outputs[2], bg.inputs["Color"])
    F = lambda s: int(round(s * fps))  # noqa: E731
    sh = {s["type"]: (s["start"], s["end"]) for s in story.shots}

    def hold(sock, values):
        prev = None
        for t, v in values:
            if prev is not None:
                key_input(sock, max(0, F(t) - 1), prev)
            key_input(sock, F(t), v)
            prev = v

    hold(storm.inputs[0], [(0, 0.6), (sh["siglo"][0], 0.0)])
    hold(red.inputs[0], [(0, 0.0), (sh["sol"][0], 1.0), (sh["sol"][0] + 7.0, 0.0)])
    hold(space.inputs[0], [(0, 0.0), (sh["tierra"][0], 1.0), (sh["sol"][0], 0.0), (sh["sol"][0] + 7.0, 1.0)])
    hold(bg.inputs["Strength"], [(0, 0.5), (sh["tierra"][0], 1.0)])
    # flash del rayo
    key_input(bg.inputs["Strength"], F(LIGHTNING_T) - 1, 0.5)
    key_input(bg.inputs["Strength"], F(LIGHTNING_T), 25.0)
    key_input(bg.inputs["Strength"], F(LIGHTNING_T + 0.15), 0.5)
    # time-lapse: el sol sube y baja (días y noches) durante el siglo
    t0, t1 = sh["siglo"]
    n = 10
    for i in range(n + 1):
        sky.sun_elevation = math.radians(4 + 60 * abs(math.sin(i * math.pi / 2)))
        sky.keyframe_insert("sun_elevation", frame=F(t0 + (t1 - t0) * i / n))
    sky.sun_elevation = math.radians(12)
    sky.keyframe_insert("sun_elevation", frame=F(sh["ruinas"][0]))
    sky.keyframe_insert("sun_elevation", frame=F(sh["ruinas"][1]))
    # Sol de la ciudad
    sun = bpy.data.lights.new("SolCiudad", "SUN")
    sun.color = (1.0, 0.75, 0.55)
    so = link(bpy.data.objects.new("SolCiudad", sun))
    so.rotation_euler = (math.radians(70), 0, math.radians(30))
    for t, e in ((0, 0.3), (sh["siglo"][0], 3.0), (sh["ruinas"][0], 1.5), (sh["tierra"][0], 0.0)):
        sun.energy = e
        sun.keyframe_insert("energy", frame=F(t))
    return bg


# ───────────────────────── montaje ─────────────────────────

def setup_render(samples, scale, fps):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.05
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 4
    sc.cycles.diffuse_bounces = 2
    sc.cycles.glossy_bounces = 2
    sc.cycles.transparent_max_bounces = 8
    sc.cycles.sample_clamp_indirect = 4.0
    sc.render.use_persistent_data = True
    sc.render.resolution_x = 1080
    sc.render.resolution_y = 1920
    sc.render.resolution_percentage = scale
    sc.render.fps = fps
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.5
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 93
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Punchy"
    except TypeError:
        pass


def build(spec, samples, scale):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    story = Story(spec)
    fps = spec.fps
    setup_render(samples, scale, fps)
    build_world(story, fps)
    hero, wind, body = build_hero()
    build_city(story, fps)
    build_ghosts(story, fps, body)
    bolt, bolt_m = build_lightning()
    build_earth(story, fps)
    build_scorched(story, fps)
    # luz de recorte para el héroe en el espacio (siempre se le ve la silueta)
    rim = bpy.data.lights.new("Recorte", "AREA")
    rim.energy = 0
    rim.size = 3
    rim_o = link(bpy.data.objects.new("Recorte", rim))
    cam_d = bpy.data.cameras.new("Camara")
    cam_d.sensor_width = 36
    cam_d.clip_end = 100000
    cam_d.dof.use_dof = True
    cam_d.dof.aperture_fstop = 2.8
    cam = link(bpy.data.objects.new("Camara", cam_d))
    bpy.context.scene.camera = cam
    sc = bpy.context.scene
    sc.frame_start = 0
    sc.frame_end = story.frames - 1
    toon = {}
    if getattr(spec, "style", "toon") == "toon":
        toon = build_toon_hero(hero, story, fps)
        face_camera(toon, cam)
    return story, {"hero": hero, "wind": wind, "bolt": bolt, "bolt_m": bolt_m, "cam": cam, "rim": rim, "rim_o": rim_o, "toon": toon}


def animate(story, objs, f0, f1):
    fps = story.spec.fps
    hero, cam = objs["hero"], objs["cam"]
    for f in range(f0, f1 + 1):
        t = f / fps
        pos, yaw, tilt = story.hero(t)
        hero.location = pos
        hero.rotation_euler = (tilt, 0, yaw)
        hero.keyframe_insert("location", frame=f)
        hero.keyframe_insert("rotation_euler", frame=f)
        if objs.get("toon"):
            cur = story.expression(t)
            for k, pl in objs["toon"].items():
                pl.hide_render = k != cur
                pl.keyframe_insert("hide_render", frame=f)
            # pequeño "rebote" de dibujos animados al respirar
            hero.scale = (1.0, 1.0, 1.0 + 0.012 * math.sin(t * 2.4))
            hero.keyframe_insert("scale", frame=f)
        objs["wind"].location = (t * 0.6, t * 0.3, 0)
        objs["wind"].keyframe_insert("location", frame=f)
        cpos, look, lens = story.camera(t)
        cam.location = cpos
        d = Vector(look) - Vector(cpos)
        cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        cam.data.lens = lens
        cam.data.dof.focus_distance = max(0.5, (Vector(pos) - Vector(cpos)).length if story.scene(t) not in ("tierra",) else d.length)
        for path in ("location", "rotation_euler"):
            cam.keyframe_insert(path, frame=f)
        cam.data.keyframe_insert("lens", frame=f)
        cam.data.dof.keyframe_insert("focus_distance", frame=f)
        # rayo
        on = LIGHTNING_T <= t < LIGHTNING_T + 0.22 and (f % 2 == 0 or t < LIGHTNING_T + 0.07)
        objs["bolt"].location = (CITY[0], CITY[1], 0)
        objs["bolt"].hide_render = not on
        objs["bolt"].keyframe_insert("hide_render", frame=f)
        b = objs["bolt_m"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        b.default_value = 80.0 if on else 0.0
        b.keyframe_insert("default_value", frame=f)
        # luz de recorte en el espacio
        sp = story.scene(t) in ("espacio", "sol")
        objs["rim"].energy = (600.0 if story.scene(t) == "espacio" else 120.0) if sp else 0.0
        objs["rim"].keyframe_insert("energy", frame=f)
        objs["rim_o"].location = (pos[0] - 2, pos[1] + 3, pos[2] + 2)
        objs["rim_o"].rotation_euler = (Vector(pos) - objs["rim_o"].location).to_track_quat("-Z", "Y").to_euler()
        objs["rim_o"].keyframe_insert("location", frame=f)
        objs["rim_o"].keyframe_insert("rotation_euler", frame=f)
    # cortes secos entre escenas
    for ob in (hero, cam, objs["rim_o"]):
        ad = ob.animation_data
        if ad and ad.action:
            for fc in getattr(ad.action, "fcurves", []):
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out/frames")
    ap.add_argument("--frames", nargs=2, type=int)
    ap.add_argument("--every", type=int, default=1)
    ap.add_argument("--samples", type=int, default=16)
    ap.add_argument("--scale", type=int, default=100)
    ap.add_argument("--spec")
    ap.add_argument("--only", nargs="*", type=int, help="fotogramas concretos (pruebas)")
    a = ap.parse_args(argv)
    spec = StorySpec.from_json(a.spec) if a.spec else StorySpec()
    story, objs = build(spec, a.samples, a.scale)
    f0, f1 = a.frames if a.frames else (0, story.frames - 1)
    frames = a.only or list(range(f0, min(f1, story.frames - 1) + 1, a.every))
    animate(story, objs, max(0, min(frames) - 1), min(story.frames - 1, max(frames) + 1))
    os.makedirs(a.out, exist_ok=True)
    sc = bpy.context.scene
    for f in frames:
        t0 = time.time()
        sc.frame_set(f)
        sc.render.filepath = os.path.join(os.path.abspath(a.out), f"f{f:05d}.jpg")
        bpy.ops.render.render(write_still=True)
        print(f"[render] fotograma {f} ({story.scene(f / spec.fps)}) en {time.time() - t0:.1f} s", flush=True)


if __name__ == "__main__":
    main()
