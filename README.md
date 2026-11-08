# Análisis, estadísticas y promedios de datos de apuestas

Herramienta en Python (sin dependencias externas) que lee un CSV con tus apuestas
y calcula estadísticas y promedios.

## Uso

```bash
python3 analizar_apuestas.py datos/apuestas_ejemplo.csv
python3 analizar_apuestas.py mis_apuestas.csv --desde 2026-08-01 --hasta 2026-08-31
python3 analizar_apuestas.py mis_apuestas.csv --deporte fútbol
python3 analizar_apuestas.py mis_apuestas.csv --json > reporte.json
```

## Formato del CSV

| Columna     | Obligatoria | Ejemplo                       |
|-------------|-------------|-------------------------------|
| `fecha`     | sí          | `2026-07-15` o `15/07/2026`   |
| `cuota`     | sí          | `1.85` o `1,85` (decimal)     |
| `monto`     | sí          | `20`                          |
| `resultado` | sí          | `ganada`, `perdida` o `nula`  |
| `deporte`   | no          | `Fútbol`                      |
| `mercado`   | no          | `1X2`                         |
| `casa`      | no          | `Bet365`                      |
| `evento`    | no          | `Real Madrid vs Barcelona`    |

Separador `,`, `;` o tabulador (se detecta solo). También acepta `G/P/N` y `win/loss/void`.

## Qué calcula

- **Resumen:** nº de apuestas, ganadas/perdidas/nulas, % de aciertos, total apostado,
  retorno, ganancia neta y ROI (yield).
- **% esperado por cuotas:** promedio de la probabilidad implícita (1/cuota).
  Si tu % de aciertos real está por encima, estás superando al mercado.
- **Promedios:** cuota (media y mediana), cuota de las ganadas, monto, ganancia por
  apuesta y su desviación, mayor ganancia y mayor pérdida.
- **Rachas y banca:** racha ganadora/perdedora máxima, racha actual, pico de ganancia
  y máxima caída (drawdown).
- **Desgloses:** por deporte, mercado, casa, rango de cuota y mes.

## Evaluar una apuesta antes de hacerla

`evaluar_apuesta.py` te dice si una apuesta va **a favor**, **en contra** o es **neutral**
según los datos, comparando la probabilidad estimada con lo que paga la cuota.

**Modo cuotas:** cuánto cobra la casa y qué probabilidad real indica cada cuota.

```bash
python3 evaluar_apuesta.py cuotas 2.10 3.40 3.60 --nombres Local Empate Visita
python3 evaluar_apuesta.py cuotas 2.10 3.40 3.60 --mi-prob 52 --elegida 1
```

**Modo fútbol:** modelo de goles (Poisson) con los promedios de los últimos partidos
(goles a favor y en contra por partido de cada equipo). Calcula 1X2, doble oportunidad,
más/menos 2.5, ambos marcan y marcadores más probables, y compara con las cuotas.

```bash
python3 evaluar_apuesta.py futbol --local-gf 1.8 --local-gc 0.9 --visita-gf 1.1 --visita-gc 1.4 \
    --cuota-1 1.95 --cuota-x 3.50 --cuota-2 4.00 --cuota-mas25 1.85 --cuota-menos25 1.95
```

**Cómo leerlo:**
- *Cuota justa* = 1 / probabilidad. Si la casa paga **más** que la cuota justa, hay valor.
- *Valor esperado* = cuánto ganarías en promedio por cada 1 apostado si la apuesta se
  repitiera muchas veces. Positivo = a favor; negativo = en contra.
- Ningún modelo garantiza el resultado: una apuesta "a favor" puede perderse.

## Pruebas

```bash
python3 -m unittest discover -s tests
```
