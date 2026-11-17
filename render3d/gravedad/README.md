# «¿Qué pasaría si la gravedad desapareciera durante 10 segundos?»

Vídeo de ilustraciones realistas animadas por capas, sincronizado con una narración continua.

## Pasos
1. `arte.py`  – genera fondos y recortables con IA libre (LCM Dreamshaper v7) y los recorta con rembg (U²-Net/ISNet).
2. `voz.py`   – narración continua del guion completo (Kokoro-82M, Apache 2.0, o Piper, MIT) + tiempos de frases y palabras.
3. `animar.py`– anima los fotogramas 1080×1920 siguiendo los tiempos de la narración.
4. `montaje.py` – música de suspense y efectos generados por código, subtítulos sincronizados (ASS), MP4.

```bash
python voz.py trabajo/ --motor kokoro --voz em_alex      # Python con torch + kokoro
python animar.py --narracion trabajo --arte arte --out trabajo/frames
python montaje.py --narracion trabajo --arte arte --frames trabajo/frames --out trabajo/video.mp4
```

Voces disponibles: `em_alex`, `em_santa`, `ef_dora` (Kokoro) o `--motor piper`.
Las ilustraciones son contenido generado con IA: márcalo así al publicar.
