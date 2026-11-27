"""Pruebas de quiz y Conquista: lote, guion, textos, zonas seguras y portada (sin voz; tiempos sintéticos).

    python3 render3d/tests/test_formatos.py
"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIM = os.path.join(ROOT, "simula")
CONQ = os.path.join(ROOT, "conquista")
sys.path.insert(0, SIM)
import formatos  # noqa: E402
import zona_segura as ZS  # noqa: E402

PRIVADO = ("@", "http", "token", "usuario")


def test_lote_valida_y_limita():
    j = formatos.lote("islas, castillos,islas", "2")
    assert [x["id"] for x in j] == ["quiz-islas", "quiz-castillos", "conquista-ep02"], j
    for mal in ("../etc/passwd", "noexiste", "islas;rm -rf /"):
        try:
            formatos.lote(mal)
            raise AssertionError(f"debería rechazar {mal!r}")
        except ValueError:
            pass
    try:
        formatos.lote("islas,castillos,gentilicios,comida,fiestas,monumentos,facil_1,facil_2,dificil_1")
        raise AssertionError("debería limitar a 8")
    except ValueError:
        pass
    try:
        formatos.lote("", "")
        raise AssertionError("lote vacío")
    except ValueError:
        pass


def test_lote_con_paquetes_y_plataformas():
    paq = sorted(os.listdir(os.path.join(ROOT, "..", "paquetes", "2026-W48")))[0]
    j = formatos.lote("islas", "", f"paquetes/2026-W48/{paq}")
    assert [x["formato"] for x in j] == ["quiz", "paquete"], j
    for mal in ("paquetes/../x.json", "paquetes/2026-W48/no-existe.json", "/etc/passwd"):
        try:
            formatos.lote("", "", mal)
            raise AssertionError(mal)
        except ValueError:
            pass
    txt = formatos.plataformas("Primera línea.\n\nCuerpo.", ["#a", "#b", "#c", "#d", "#e"], "Título del vídeo")
    assert "INSTAGRAM" in txt and "TIKTOK" in txt and "Título del vídeo #Shorts" in txt


def test_quiz_json_completos():
    for t, _, _ in formatos.temas():
        q = formatos.cargar_quiz(t)
        assert len(q["preguntas"]) == 5, t
        for p in q["preguntas"]:
            assert p["q"] and p["respuesta"] and len(p["punto"]) == 2, (t, p)
        g = formatos.guion_quiz(q)
        assert [k for k, _ in g["guion"]][:3] == ["intro", "q1", "a1"] and g["guion"][-1][0] == "outro"


def test_textos_sin_datos_privados():
    for t in ("islas", "castillos", "gentilicios", "sabias_1"):
        txt, tags = formatos.texto_quiz(formatos.cargar_quiz(t))
        assert 3 <= len(tags) <= 5 and all(x.startswith("#") for x in tags)
        assert not any(p in txt.lower() for p in PRIVADO), txt
    txt, tags = formatos.texto_conquista(os.path.join(CONQ, "temporada1"), 2)
    assert "episodio 3" in txt.lower() and not any(p in txt.lower() for p in PRIVADO), txt


def _zonas_quiz(tema):
    os.environ["QUIZ"] = tema
    import importlib
    import quiz
    importlib.reload(quiz)
    nar = formatos.narracion_sintetica(formatos.guion_quiz(formatos.cargar_quiz(tema)))
    v = quiz.Video(nar, tema)
    return v, ZS.fuera_de_zona(v, paso=0.5)


def test_zonas_seguras_quiz():
    for tema in ("islas", "fiestas_peru"):  # España con Canarias y un mapa de otro país
        _, malos = _zonas_quiz(tema)
        assert not malos, (tema, malos)


def test_canarias_dentro_de_la_zona():
    os.environ["QUIZ"] = "islas"
    import importlib
    import quiz
    importlib.reload(quiz)
    c = quiz.CAN
    assert not ZS.inseguro((c["x"], c["y"], c["x"] + c["w"], c["y"] + c["h"]))
    for lon, lat in ((-18.0, 27.75), (-13.5, 29.25), (-15.6, 28.1)):  # El Hierro, La Graciosa, Gran Canaria
        x, y = quiz.proj(lon, lat, can=True)
        assert c["x"] < x < c["x"] + c["w"] and c["y"] < y < c["y"] + c["h"], (lon, lat, x, y)


def test_zonas_seguras_conquista():
    sys.path.insert(0, CONQ)
    import conquista
    import episodio
    for ep in (1, 2):
        st = conquista.estado(os.path.join(CONQ, "temporada1"), ep)
        g = {"guion": [[k, t] for k, t, _ in episodio.guion(st)], "pausas": {}}
        v = episodio.Video(formatos.narracion_sintetica(g), os.path.join(CONQ, "temporada1"), ep)
        malos = ZS.fuera_de_zona(v, paso=0.5)
        assert not malos, (ep, malos)


def test_contar_votos_reconoce_y_no_duplica():
    sys.path.insert(0, CONQ)
    import contar
    import datos
    m, p = datos.load()
    for txt, esperado in (("Jumillaaaa murcia", "Jumilla"), ("SEVILLAAA", "Sevilla"), ("Cádiz capital", "Cádiz"),
                          ("Alcoy( primeroooo)", "Alcoi/Alcoy"), ("Guadix, Granada", "Guadix")):
        i, _ = contar.parse(txt)
        assert i is not None and m[i]["nombre"] == esperado, (txt, i)
    for txt in ("Villanueva", "jaja qué bueno"):  # ambiguo o sin pueblo: no suma
        assert contar.parse(txt)[0] is None, txt
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "c.csv")
        open(src, "w").write("usuario,comentario,red\na1,Guadix Granada,instagram\na1,Baza Granada,instagram\nb2,Guadix,instagram\n")
        subprocess.run([sys.executable, os.path.join(CONQ, "contar.py"), src, d, "9"], check=True, capture_output=True)
        out = open(os.path.join(d, "votos", "ep09.csv")).read()
        assert "Guadix,Granada,2" in out and "Baza" not in out, out   # 1 voto por cuenta: el primero


def test_provincias_y_pueblos_bilingues():
    sys.path.insert(0, CONQ)
    import datos
    for t in ("Alacant/Alicante", "València/Valencia", "Araba/Álava", "Castelló/Castellón"):
        assert datos.prov_code(t), t
    i, why = datos.find("Alcoi/Alcoy", "Alacant/Alicante")
    assert i is not None, why


def test_zonas_seguras_todas_las_escenas_de_paquete():
    """Cada tipo de escena de nivel_oculto (mapa, simulación, animación, archivo, gráfico, texto, y los motivos de
    meteorito) se dibuja dentro de la zona segura. Así un fallo de maquetación se detecta en las pruebas, antes de
    gastar una máquina de render (en Faisanes se coló el panel de «archivo» hasta x=890)."""
    import nivel_oculto as no
    kinds = sorted(no.ALLOWED_KINDS)
    pkg = {"id": "prueba-escenas", "title": "Prueba de escenas", "pillar": "curiosidades", "format": "reel",
           "script": [f"Frase de prueba número {i + 1} para la escena {k}, con 1.250 datos." for i, k in enumerate(kinds)],
           "visual_brief": [{"scene": i + 1, "seconds": 4, "kind": k, "visual": "prueba"} for i, k in enumerate(kinds)],
           "on_screen_text": [{"at": 4.0 * i, "text": f"RÓTULO DE PRUEBA BASTANTE LARGO {i}"} for i in range(len(kinds))],
           "caption": {"text": "x", "hashtags": ["#a"]}}
    v = no.make_video(pkg)(no.synthetic_narration(pkg))
    assert no.beat_motifs(pkg) == [None] * len(kinds)  # escenas genéricas (los motivos de meteorito van aparte)
    malos = ZS.fuera_de_zona(v, paso=0.4, fps=30)
    assert not malos, malos
    pkg_m = dict(pkg, script=[t.replace("1.250 datos", "un meteorito de 3,8 kilos") for t in pkg["script"]])
    assert any(no.beat_motifs(pkg_m))                  # y también con los motivos de meteorito
    malos = ZS.fuera_de_zona(no.make_video(pkg_m)(no.synthetic_narration(pkg_m)), paso=0.4, fps=30)
    assert not malos, malos


def test_escenas_con_datos_en_zona_segura():
    """Cada escena con datos (escenas.py: mapas reales, cifras, comparaciones, fechas, figuras) se dibuja dentro de
    la zona segura y sustituye a la escena genérica de su frase."""
    import nivel_oculto as no
    import escenas
    E = [{"tipo": "mapa_espana", "punto": [-3.38, 37.73], "etiqueta": "Bélmez de la Moraleda", "resaltar": ["Jaén"]},
         {"tipo": "mapa_espana", "punto": [-17.23, 28.10], "etiqueta": "La Gomera"},
         {"tipo": "mapa_mundo", "punto": [121.56, 15.76], "etiqueta": "Baler · Filipinas"},
         {"tipo": "contador", "valor": 337, "unidad": "días de asedio"},
         {"tipo": "comparacion", "items": [{"etiqueta": "Una ciudad muy larga", "valor": 297000, "destacar": True},
                                           {"etiqueta": "Otra", "valor": 84000}, {"etiqueta": "Tercera", "valor": 150000}]},
         {"tipo": "linea_tiempo", "hitos": [{"fecha": "1 de julio de 1898", "texto": "Empieza el asedio de la iglesia"},
                                            {"fecha": "10 de diciembre de 1898", "texto": "Tratado de París"},
                                            {"fecha": "2 de junio de 1899", "texto": "Se rinden"}]},
         {"tipo": "personas", "resaltar": 18, "etiqueta": "nacidos en el extranjero"},
         {"tipo": "reloj", "horas": [["Sol", "12:00"], ["Reloj", "14:00"]]},
         {"tipo": "documento", "titular": "Aparece una cara en el suelo de una cocina de un pueblo de Jaén", "fecha": "1971"},
         ] + [{"tipo": "figura", "figura": f, "texto": "85 metros", "lados": ["Marruecos", "España"]} for f in sorted(escenas.FIGURAS)]
    script = [f"Frase de prueba número {i + 1} con la escena {e['tipo']} y algo más de texto." for i, e in enumerate(E)]
    starts, total = no.estimated_starts(script)
    secs = [b - a for a, b in zip(starts, starts[1:] + [total])]
    pkg = {"id": "prueba-escenas-datos", "title": "x", "pillar": "historia", "format": "reel", "script": script,
           "visual_brief": [{"scene": i + 1, "seconds": s, "kind": "texto", "visual": "x", "escena": e} for i, (e, s) in enumerate(zip(E, secs))],
           "on_screen_text": [{"at": a, "text": f"RÓTULO {i}"} for i, a in enumerate(starts)], "caption": {"text": "x", "hashtags": ["#a"]}}
    assert no.beat_specs(pkg) == E                                     # una escena por frase, ninguna se pierde
    assert not escenas.valida({"tipo": "figura", "figura": "dragon"}) and not escenas.valida({"tipo": "contador"})
    malos = ZS.fuera_de_zona(no.make_video(pkg)(no.synthetic_narration(pkg)), paso=0.4, fps=30)
    assert not malos, malos


def test_pico_real_ultimo_recurso():
    """Fallo del 26-11 (quiz de esquí a +0,4 dBTP marcado «listo»): si el limitador no basta, se baja el volumen del
    audio ya codificado hasta quedar por debajo de −1 dBTP."""
    import shutil
    if not shutil.which("ffmpeg"):
        print("  (sin ffmpeg: se omite)")
        return
    sys.path.insert(0, SIM)
    import montaje
    with tempfile.TemporaryDirectory() as d:
        wav, mp4 = os.path.join(d, "a.wav"), os.path.join(d, "v.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=f=1000:d=2", "-af", "volume=40dB",
                        "-c:a", "pcm_f32le", "-ar", "48000", wav], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=64x64:d=2", "-i", wav,
                        "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k", "-shortest", mp4], check=True)
        assert montaje.pico_real(mp4) > montaje.TP_MAX
        assert montaje.bajar_volumen(mp4) <= montaje.TP_MAX


def test_primer_fotograma_con_contenido():
    """Retención (fase 2): el primer fotograma de una historia con mapa ya enseña el mapa, no una pantalla vacía."""
    import numpy as np
    import nivel_oculto as no
    pkg = {"id": "prueba-primer-segundo", "title": "x", "pillar": "historia", "format": "reel",
           "script": ["Bélmez de la Moraleda, un pueblo de Jaén, con una frase algo larga.", "Y una segunda frase de prueba."],
           "visual_brief": [{"scene": 1, "seconds": 4, "kind": "mapa", "visual": "x",
                             "escena": {"tipo": "mapa_espana", "punto": [-3.38, 37.73], "etiqueta": "Bélmez", "resaltar": ["Jaén"]}},
                            {"scene": 2, "seconds": 2, "kind": "texto", "visual": "x"}],
           "on_screen_text": [], "caption": {"text": "x", "hashtags": ["#a"]}}
    v = no.make_video(pkg)(no.synthetic_narration(pkg))
    a = np.asarray(v.frame(0).convert("RGB"), np.float32)
    zona = a[700:1200, 150:850]
    assert (zona.max(axis=2) > 90).mean() > 0.15, "el mapa no se ve en el primer fotograma"


def test_conquista_diaria_sin_votos_nuevos():
    """La serie es diaria: un episodio sin votos nuevos también se genera y su guion tiene sentido."""
    import shutil
    sys.path.insert(0, CONQ)
    import conquista
    import episodio
    with tempfile.TemporaryDirectory() as d:
        t = os.path.join(d, "t")
        shutil.copytree(os.path.join(CONQ, "temporada1"), t)
        ult = max(int(f[2:4]) for f in os.listdir(os.path.join(t, "votos")) if f.startswith("ep"))
        open(os.path.join(t, "votos", f"ep{ult + 1:02d}.csv"), "w").write("pueblo,provincia,votos\n")
        st = conquista.estado(t, ult + 1)
        g = episodio.guion(st)
        assert st["votos_nuevos"] == 0 and "no se ha movido" in g[0][1] and "Cero" not in g[0][1], g[0]
        assert f"episodio {episodio.letras(ult + 2)}" in g[-1][1]


def test_conquista_votos_pendientes_no_inventa():
    """Respaldo: si los comentarios no se pudieron leer, el episodio sale igual, dice la verdad y no suma nada."""
    import shutil
    sys.path.insert(0, CONQ)
    import conquista
    import episodio
    with tempfile.TemporaryDirectory() as d:
        t = os.path.join(d, "t")
        shutil.copytree(os.path.join(CONQ, "temporada1"), t)
        ult = max(int(f[2:4]) for f in os.listdir(os.path.join(t, "votos")) if f.endswith(".csv"))
        open(os.path.join(t, "votos", f"ep{ult + 1:02d}.pendiente"), "w").write("comentarios no leídos a tiempo\n")
        st, antes = conquista.estado(t, ult + 1), conquista.estado(t, ult)
        assert st["votos_pendientes"] and st["votos_nuevos"] == 0 and st["votos_total"] == antes["votos_total"]
        g = episodio.guion(st)
        assert "próximo episodio" in g[0][1] and "no se ha movido" not in g[0][1], g[0]
        open(os.path.join(t, "votos", f"ep{ult + 1:02d}.csv"), "w").write("pueblo,provincia,votos\n")
        assert not conquista.estado(t, ult + 1)["votos_pendientes"]   # en cuanto llega el CSV, deja de estar pendiente


def test_portada():
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "voz"))
        nar = formatos.narracion_sintetica(formatos.guion_quiz(formatos.cargar_quiz("castillos")))
        json.dump(nar, open(os.path.join(d, "voz", "narracion.json"), "w"))
        out = os.path.join(d, "p.jpg")
        r = subprocess.run([sys.executable, os.path.join(SIM, "formatos.py"), "portada-auto", "quiz", "castillos",
                            os.path.join(d, "voz"), out], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        from PIL import Image
        assert Image.open(out).size == (1080, 1920)


def test_pedido_lote_semanal_valida():
    """El pedido del repo privado solo acepta quiz existentes, paquetes de su semana y ≤ 8 vídeos por lote."""
    sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "tools"))
    import pedido_lote as PL
    raiz = os.path.dirname(ROOT)
    paq = sorted(f for f in os.listdir(os.path.join(raiz, "paquetes", "2026-W50")) if f.endswith(".json"))[0]
    ok = PL.validar({"semana": "2026-W50", "lotes": [{"temas": "capitales,rios", "paquetes": f"paquetes/2026-W50/{paq}"}]}, raiz)
    assert ok == [{"temas": "capitales,rios", "paquetes": f"paquetes/2026-W50/{paq}"}]
    malos = [{"semana": "x", "lotes": [{"temas": "rios"}]},
             {"semana": "2026-W50", "lotes": [{"temas": "../x"}]},
             {"semana": "2026-W50", "lotes": [{"temas": "no_existe"}]},
             {"semana": "2026-W50", "lotes": [{"temas": "rios"}, {"temas": "rios"}]},
             {"semana": "2026-W50", "lotes": [{"temas": ",".join(["rios", "capitales", "islas", "castillos", "dulces",
                                                                       "quesos", "parques", "unesco", "lenguas"])}]},
             {"semana": "2026-W50", "lotes": [{"paquetes": f"paquetes/2026-W49/{paq}"}]},
             {"semana": "2026-W50", "lotes": []}]
    for m in malos:
        try:
            PL.validar(m, raiz)
        except ValueError:
            continue
        raise AssertionError(f"debería rechazar {m}")


if __name__ == "__main__":
    solo = set(sys.argv[1:])  # p. ej. `test_formatos.py rapidas` o nombres de pruebas concretas
    RAPIDAS = {"test_lote_valida_y_limita", "test_lote_con_paquetes_y_plataformas", "test_quiz_json_completos", "test_textos_sin_datos_privados",
               "test_canarias_dentro_de_la_zona", "test_contar_votos_reconoce_y_no_duplica",
               "test_provincias_y_pueblos_bilingues", "test_conquista_diaria_sin_votos_nuevos",
               "test_conquista_votos_pendientes_no_inventa", "test_pedido_lote_semanal_valida"}
    if "rapidas" in solo:
        solo = RAPIDAS
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn) and (not solo or name in solo):
            fn()
            print("ok", name)
