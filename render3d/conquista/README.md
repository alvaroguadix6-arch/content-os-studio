# TU PUEBLO CONQUISTA ESPAÑA · Serie de NIVEL OCULTO

Serie participativa: los espectadores comentan su pueblo y su provincia, cada comentario válido es un voto y los
pueblos conquistan el mapa de España municipio a municipio. Cada episodio (20–35 s, 1080×1920) enseña el mapa nuevo,
el líder, el gran salto de la semana, invasiones, rivalidades y el TOP 5, y termina pidiendo comentar.

## Mecánica de la competición

| Regla | Detalle |
|---|---|
| Cómo se vota | Comentar `Pueblo, Provincia` en el último episodio (TikTok, Reels o Shorts). |
| Valor | **1 voto por cuenta y episodio** (vale su primer comentario reconocido). Los votos se acumulan toda la temporada. |
| Validez | Tiene que ser uno de los **8.131 municipios** oficiales (INE/IGN). Provincia obligatoria si el nombre se repite. |
| Conquista | Cada voto = **150 km²** (`km2_por_voto` en `config.json`). Con V votos el pueblo alcanza un radio √(V·150/π) km. |
| Fronteras | Cada municipio es del pueblo que lo alcanza con más holgura (distancia / radio). Si dos pueblos chocan, la frontera se desplaza hacia el que tiene menos votos. Un pueblo puede **invadir** municipios de otro. |
| Provincias | Quien controla **más del 50 %** de una provincia la **domina** (corona en el mapa). |
| Ranking | Por votos acumulados; empate → llegó antes. Flechas de subida/bajada y «NEW». |
| Rivalidades | Pares de pueblos con frontera común (o misma provincia) y votos más igualados. |
| Fin de temporada | Libre (p. ej. cuando alguien domine 10 provincias o al llegar a X episodios). |

Nada se inventa: el episodio 1 arranca con el mapa vacío (0 votos) y la demostración va marcada como **EJEMPLO**.

## Episodio a episodio

```bash
# 1) contar los comentarios reales del episodio anterior (exportación o copia: usuario,comentario[,red])
python contar.py comentarios_ep01.csv temporada1 2        # → temporada1/votos/ep02.csv + temporada1/revisar/ep02.txt
#    (o rellena tú temporada1/votos/ep02.csv: pueblo,provincia,votos)
# 2) producir el episodio
PY_VOZ=<python con kokoro> python producir.py temporada1 2  # → temporada1/salida/ep02.mp4 + ep02_resumen.txt
```

El guion del episodio se escribe solo a partir de los datos (`episodio.py → guion()`):
intro con votos nuevos → líder (zoom a su territorio) → gran salto / pueblo nuevo → invasión → rivalidad «VS»
→ TOP 5 → «Comenta tu pueblo y tu provincia… ¿quién conquistará más en el episodio N+1?».

## Archivos

| Archivo | Qué hace |
|---|---|
| `datos.py` | Municipios del IGN (es-atlas, MIT): áreas, centroides y reconocimiento de nombres. |
| `conquista.py` | Motor: votos → territorios, ranking, invasiones, rivalidades, provincias dominadas. `python conquista.py temporada1 3` imprime el estado. |
| `mapa.py` | Mapa rasterizado (8.212 recintos) con cámara libre y zoom cinematográfico. |
| `episodio.py` | Guion automático + animación del episodio (plantilla de lanzamiento y plantilla normal). |
| `contar.py` | Comentarios → votos (1 por cuenta, revisión de lo no reconocido). |
| `producir.py` | Todo en un comando: estado → guion → voz → fotogramas → montaje (música + efectos). |
