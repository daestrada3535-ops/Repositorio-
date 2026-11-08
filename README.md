# Análisis de apuestas

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

## Pruebas

```bash
python3 -m unittest discover -s tests
```
