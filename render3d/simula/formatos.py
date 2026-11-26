"""NIVEL OCULTO · Utilidades comunes para producir quiz y episodios de «Tu pueblo conquista España» en lote.

    python formatos.py temas                                   → lista de quiz disponibles (quizzes/*.json)
    python formatos.py lote "islas,castillos" [conquista_ep]   → matriz JSON para GitHub Actions (valida y limita)
    python formatos.py guion-quiz <tema> <salida.json>         → guion de voz (pausa de 5 s para la cuenta atrás)
    python formatos.py texto quiz <tema> <dir>                 → descripcion.txt + hashtags.txt
    python formatos.py texto conquista <temporada> <ep> <dir>  → descripcion.txt + hashtags.txt
    python formatos.py fondo quiz <tema> <narracion/> <fondo.jpg>              → fondo limpio para la portada
    python formatos.py fondo conquista <temporada> <ep> <narracion/> <fondo.jpg>
    python formatos.py portada-auto quiz <tema> <narracion/> <portada.jpg>     → fondo + título automático
    python formatos.py zonas quiz <tema> <narracion/>                          → sale con 1 si algo queda tapado
    python formatos.py zonas conquista <temporada> <ep> <narracion/>
    python formatos.py zonas paquete <paquete.json> <narracion/>
    python formatos.py portada <fondo.jpg> <salida.jpg> "TÍTULO" ["SUBTÍTULO"]

Todo es local y gratuito. La descripción sigue las reglas de ig-caption (primera línea que engancha, una sola
petición, 3-5 hashtags) y nunca incluye datos privados: solo el contenido del propio quiz o los votos
agregados que ya son públicos (pueblo, provincia, votos).
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
QDIR = os.path.join(HERE, "quizzes")
CONQ = os.path.join(os.path.dirname(HERE), "conquista")
MAX_LOTE = 8  # vídeos por ejecución (4 máquinas a la vez): un día y medio de publicaciones a 3 al día
ROOT = os.path.dirname(os.path.dirname(HERE))
PAQ_RE = re.compile(r"^paquetes/[0-9]{4}-W[0-9]{2}/[a-z0-9-]+\.json$")
NOMBRE_RE = re.compile(r"^[a-z0-9_]{1,40}$")


# ───── temas y lote ─────
def temas():
    out = []
    for f in sorted(os.listdir(QDIR)):
        if f.endswith(".json") and f != "provincias.geojson":
            q = json.load(open(os.path.join(QDIR, f), encoding="utf-8"))
            out.append((f[:-5], q.get("tema", ""), q.get("pais", "ESPAÑA")))
    return out


def lote(spec, conquista_ep="", paquetes=""):
    """Convierte la selección del formulario en una lista de trabajos. Lanza ValueError si algo no es válido."""
    disp = {t for t, _, _ in temas()}
    jobs = []
    for raw in [x.strip().lower() for x in (spec or "").split(",") if x.strip()]:
        if not NOMBRE_RE.match(raw) or raw not in disp:
            raise ValueError(f"tema desconocido: {raw!r} (usa `python formatos.py temas`)")
        if any(j["id"] == f"quiz-{raw}" for j in jobs):
            continue  # sin duplicados
        jobs.append({"formato": "quiz", "tema": raw, "id": f"quiz-{raw}"})
    ep = str(conquista_ep or "").strip()
    if ep:
        if not ep.isdigit() or not 1 <= int(ep) <= 99:
            raise ValueError("episodio de Conquista inválido (1-99)")
        vd = os.path.join(CONQ, "temporada1", "votos")
        if int(ep) > 1 and not any(os.path.exists(os.path.join(vd, f"ep{int(ep):02d}.{x}")) for x in ("csv", "pendiente")):
            raise ValueError(f"faltan los votos del episodio {ep} (temporada1/votos/ep{int(ep):02d}.csv o .pendiente)")
        jobs.append({"formato": "conquista", "tema": f"ep{int(ep):02d}", "id": f"conquista-ep{int(ep):02d}"})
    for raw in [x.strip() for x in (paquetes or "").split(",") if x.strip()]:
        if not PAQ_RE.match(raw) or not os.path.exists(os.path.join(ROOT, raw)):
            raise ValueError(f"paquete inválido o inexistente: {raw!r} (formato paquetes/AAAA-Www/id.json)")
        pid = "paq-" + os.path.basename(raw)[:-5]
        if any(j["id"] == pid for j in jobs):
            continue
        jobs.append({"formato": "paquete", "tema": raw, "id": pid})
    if not jobs:
        raise ValueError("no hay nada que renderizar: indica temas de quiz, un episodio de Conquista o paquetes")
    if len(jobs) > MAX_LOTE:
        raise ValueError(f"como mucho {MAX_LOTE} vídeos por ejecución (para no gastar de más)")
    return jobs


# ───── quiz ─────
def cargar_quiz(tema):
    if not NOMBRE_RE.match(tema):
        raise ValueError("tema inválido")
    return json.load(open(os.path.join(QDIR, tema + ".json"), encoding="utf-8"))


def guion_quiz(q):
    sabias = q.get("modo") == "sabias"
    g, p = [["intro", q["intro"]]], {"intro": 0.45}
    for i, x in enumerate(q["preguntas"], 1):
        g += [[f"q{i}", x.get("voz_q", x["q"])], [f"a{i}", x.get("voz_a", x["respuesta"])]]
        p[f"q{i}"] = 1.4 if sabias else 5.0  # 5 s de cuenta atrás
        p[f"a{i}"] = 0.9
    g.append(["outro", q["outro"]])
    p["outro"] = 0.0
    return {"guion": g, "pausas": p}


def narracion_sintetica(guion):
    """Tiempos aproximados sin voz (para pruebas y comprobaciones): 2,6 palabras por segundo."""
    t, lines = 0.25, []
    for k, txt in guion["guion"]:
        ws = txt.split()
        d = max(0.8, len(ws) / 2.6)
        lines.append({"key": k, "text": txt, "start": t, "end": t + d,
                      "words": [[w, t + i * d / len(ws), t + (i + 1) * d / len(ws)] for i, w in enumerate(ws)]})
        t += d + guion["pausas"].get(k, 0.2)
    return {"lines": lines, "duration": t}


def texto_quiz(q):
    tema = q.get("tema", "").capitalize()
    pais = q.get("pais", "España").capitalize()
    sabias = q.get("modo") == "sabias"
    if sabias:
        cab = f"{q.get('titulo', tema)}. ¿Cuál no sabías?"
        cuerpo = q["intro"]
        pide = "Guárdalo para ganar la próxima discusión de geografía."
    else:
        cab = f"¿Cuántas aciertas de 5? Quiz de {tema.lower()} de {pais}."
        cuerpo = q["intro"]
        pide = "Mándaselo a alguien de tu provincia y comparad resultados."
    tags = q.get("hashtags") or ["#quiz", f"#{_tag(pais)}", "#geografia", "#curiosidades"]
    return f"{cab}\n\n{cuerpo}\n\n{pide}", tags[:5]


# ───── conquista ─────
def texto_conquista(temporada, ep):
    sys.path.insert(0, CONQ)
    import conquista  # noqa: E402
    st = conquista.estado(temporada, ep)
    P = st["pueblos"]
    if not P:
        cab = f"Episodio {ep} de Tu pueblo conquista España: el mapa sigue vacío."
        cuerpo = "El primer pueblo que comente empieza ganando."
    else:
        lid = P[0]
        cab = f"Episodio {ep} de Tu pueblo conquista España: {lid['nombre']} va primero con {lid['votos']} voto{'s' if lid['votos'] != 1 else ''}."
        pct = f"{st['conquistado']:.1f}".replace(".", ",")
        cuerpo = (f"Los votos del episodio anterior se suman en el episodio {ep + 1}. {len(P)} pueblos en juego y el {pct} % de España ya tiene dueño."
                  if st.get("votos_pendientes") else
                  f"{st['votos_nuevos']} votos nuevos, {len(P)} pueblos en juego y el {pct} % de España ya tiene dueño.")
    pide = (f"Comenta tu pueblo y tu provincia: cada cuenta suma un voto y conquista territorio en el episodio {ep + 1}.")
    return f"{cab}\n\n{cuerpo}\n\n{pide}", ["#tupuebloconquistaespaña", "#españa", "#pueblos", "#mapa"]


def _tag(s):
    s = s.lower()
    for a, b in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u")):
        s = s.replace(a, b)
    return re.sub(r"[^a-zñ0-9]", "", s)


def texto_paquete(path):
    p = json.load(open(os.path.join(ROOT, path), encoding="utf-8"))
    c = p.get("caption") or {}
    texto = (c.get("text") if isinstance(c, dict) else str(c)).replace("Fuentes en el primer comentario.", "").strip()
    return texto, (c.get("hashtags") if isinstance(c, dict) else None) or ["#curiosidades", "#nivelOculto"]


def plataformas(texto, tags, titulo=None):
    """Mismo vídeo, texto adaptado a cada app (todas aceptan 1080×1920; la zona segura ya es común)."""
    primera = texto.split("\n")[0].strip()
    titulo = (titulo or primera).strip()
    yt = titulo if len(titulo) <= 90 else titulo[:87].rsplit(" ", 1)[0] + "…"
    return ("INSTAGRAM (Reels)\n" + texto + "\n\n" + " ".join(tags) + "\n\n"
            "TIKTOK\n" + titulo + "\n" + primera + "\n" + " ".join(tags[:4]) + "\n\n"
            "YOUTUBE SHORTS\nTítulo: " + yt + " #Shorts\nDescripción:\n" + texto + "\n" + " ".join(tags[:3]) + "\n")


def guardar_texto(texto, tags, d, titulo=None):
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "descripcion.txt"), "w", encoding="utf-8").write(texto + "\n\n" + " ".join(tags) + "\n")
    open(os.path.join(d, "hashtags.txt"), "w", encoding="utf-8").write(" ".join(tags) + "\n")
    open(os.path.join(d, "plataformas.txt"), "w", encoding="utf-8").write(plataformas(texto, tags, titulo))


# ───── portada ─────
def portada(frame_path, out, titulo, sub=None):
    """Portada 1080×1920 a partir de un fotograma del vídeo: oscurece, título grande y subtítulo, todo dentro
    de la zona segura (y 330-900, x 118-962) para que ninguna app lo tape en la cuadrícula ni en el feed."""
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    fonts = "/usr/share/fonts/opentype/inter/"

    def f(style, size):
        return ImageFont.truetype(fonts + f"Inter-{style}.otf", int(size))
    im = Image.open(frame_path).convert("RGB").resize((1080, 1920))
    im = im.filter(ImageFilter.GaussianBlur(2)).convert("RGBA")
    shade = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(shade)
    for y in range(0, 1100):
        ds.line([(0, y), (1080, y)], fill=(8, 4, 24, int(215 * max(0.0, 1 - max(0, y - 700) / 400))))
    im.alpha_composite(shade)
    d = ImageDraw.Draw(im)
    d.text((540, 272), "N I V E L   O C U L T O", font=f("ExtraBold", 26), fill=(230, 220, 255), anchor="mm")
    words, lines, size = titulo.upper().split(), [], 112
    while True:
        lines, cur = [], ""
        for w in words:
            test = (cur + " " + w).strip()
            if d.textlength(test, font=f("Black", size)) <= 844:
                cur = test
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
        if (len(lines) <= 3 and len(lines) * size * 1.08 <= 430) or size <= 56:
            break
        size -= 6
    y = 390
    for i, ln in enumerate(lines):
        col = (255, 206, 60) if i == len(lines) - 1 and len(lines) > 1 else (255, 255, 255)
        d.text((540, y + size / 2), ln, font=f("Black", size), fill=col, anchor="mm", stroke_width=8, stroke_fill=(20, 10, 50))
        y += size * 1.08
    if sub:
        fs = 44
        while d.textlength(sub.upper(), font=f("Black", fs)) + 80 > 844 and fs > 26:
            fs -= 2
        w = d.textlength(sub.upper(), font=f("Black", fs)) + 80
        y += 30
        d.rounded_rectangle([540 - w / 2, y, 540 + w / 2, y + fs + 40], 26, fill=(230, 40, 60))
        d.text((540, y + (fs + 40) / 2), sub.upper(), font=f("Black", fs), fill=(255, 255, 255), anchor="mm")
    im.convert("RGB").save(out, quality=92)
    return out


def video(formato, args, nar_dir):
    """Objeto vídeo (quiz o episodio) con la narración real, para comprobar zonas o sacar el fondo de portada."""
    nar = json.load(open(os.path.join(nar_dir, "narracion.json"), encoding="utf-8"))
    if formato == "quiz":
        cargar_quiz(args[0])  # valida el nombre
        os.environ["QUIZ"] = args[0]
        import quiz
        return quiz.Video(nar, args[0])
    if formato == "conquista":
        sys.path.insert(0, CONQ)
        import episodio
        return episodio.Video(nar, args[0], int(args[1]))
    if formato == "paquete":  # paquetes de instagram-agent (nivel_oculto.py); .frame recibe nº de fotograma
        import nivel_oculto
        return nivel_oculto.make_video(nivel_oculto.load_package(args[0]))(nar)
    raise ValueError("formato desconocido")


def titulo_portada(formato, args):
    if formato == "quiz":
        q = cargar_quiz(args[0])
        if q.get("modo") == "sabias":
            return q.get("titulo", q["tema"]), "¿Cuál no sabías?"
        pais = q.get("pais", "ESPAÑA").capitalize()
        return f"{q['tema'].capitalize()} de {pais}", "¿Cuántas aciertas?"
    return "Tu pueblo conquista España", f"Episodio {int(args[1])}"


def main(a):
    cmd = a[0] if a else ""
    if cmd == "temas":
        for t, tema, pais in temas():
            print(f"{t:24s} {tema} ({pais})")
    elif cmd == "lote":
        print(json.dumps({"include": lote(a[1], a[2] if len(a) > 2 else "", a[3] if len(a) > 3 else "")}, ensure_ascii=False))
    elif cmd == "guion-quiz":
        json.dump(guion_quiz(cargar_quiz(a[1])), open(a[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    elif cmd == "texto" and a[1] == "quiz":
        t, sub = titulo_portada("quiz", [a[2]])
        guardar_texto(*texto_quiz(cargar_quiz(a[2])), a[3], f"{t}: {sub.lower()}")
    elif cmd == "texto" and a[1] == "paquete":
        guardar_texto(*texto_paquete(a[2]), a[3], json.load(open(os.path.join(ROOT, a[2]), encoding="utf-8")).get("title"))
    elif cmd == "titulo-portada":  # titulo-portada paquete <ruta>
        p = json.load(open(os.path.join(ROOT, a[2]), encoding="utf-8"))
        t = (p.get("title") or "").split(":")[0].strip()
        print(t if len(t) <= 42 else (p.get("hook") or {}).get("on_screen", t[:42]))
    elif cmd == "texto" and a[1] == "conquista":
        guardar_texto(*texto_conquista(a[2], int(a[3])), a[4], f"Tu pueblo conquista España · Episodio {int(a[3])}")
    elif cmd == "fondo":
        video(a[1], a[2:-2], a[-2]).fondo_portada().save(a[-1], quality=92)
    elif cmd == "portada-auto":  # portada-auto quiz <tema> <voz/> <out.jpg> | conquista <temporada> <ep> <voz/> <out.jpg>
        v = video(a[1], a[2:-2], a[-2])
        bg = a[-1] + ".fondo.jpg"
        v.fondo_portada().save(bg, quality=92)
        titulo, sub = titulo_portada(a[1], a[2:-2])
        print("portada:", portada(bg, a[-1], titulo, sub))
        os.remove(bg)
    elif cmd == "zonas":  # zonas quiz <tema> <voz/> | conquista <temporada> <ep> <voz/>
        import zona_segura as ZS
        malos = ZS.fuera_de_zona(video(a[1], a[2:-1], a[-1]), paso=0.25, fps=30 if a[1] == "paquete" else None)
        for m in malos:
            print("⚠️ fuera de la zona segura:", m)
        print("zonas seguras:", "OK" if not malos else f"{len(malos)} elementos tapados")
        return 1 if malos else 0
    elif cmd == "portada":
        print("portada:", portada(a[1], a[2], a[3], a[4] if len(a) > 4 else None))
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
