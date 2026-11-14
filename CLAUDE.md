# Mi Economía — instrucciones para Claude

Este repo es el registro de la economía personal del usuario (pesos colombianos, COP).
El usuario habla en español colombiano informal y te cuenta sus ingresos, gastos, fiados, préstamos, etc.
Tu trabajo: anotarlo en los CSV, correr el reporte, contestarle con el resumen y hacer commit + push.

## Archivos
- `datos/movimientos.csv` — todo movimiento de plata. Columnas:
  `fecha,tipo,monto,medio,categoria,persona,descripcion,fecha_limite`
- `datos/pendientes.csv` — pagos que el usuario tiene que hacer (arriendo, servicios, apartados de la nómina).
  Columnas: `fecha_limite,concepto,monto,estado,nota` (estado: `pendiente` o `pagado`).
- `economia.py` — genera `REPORTE.md`. Correr: `python3 economia.py` (o `python3 economia.py 2026-11` para un mes).

## Tipos de movimiento
| tipo | cuándo | efecto |
|---|---|---|
| saldo_inicial | plata con la que arranca en un medio | + plata |
| ingreso | nómina, ventas, regalos | + plata |
| gasto | pagó algo de contado | − plata |
| fiado | sacó algo fiado (tienda del barrio) | + lo que debe (cuenta como gasto del mes) |
| abono | le paga/abona a alguien que le debe (tienda, préstamo) | − plata, − lo que debe |
| prestamo_recibido | alguien le presta plata | + plata, + lo que debe |
| preste | él le presta plata a alguien | − plata, + le deben |
| me_debe | alguien le queda debiendo sin sacar plata (un trabajo, una venta) | + le deben |
| cobro | alguien le paga lo que le debía | + plata, − le deben |
| traslado | mover plata entre medios; `medio` = `Origen>Destino` | nada en el total |

## Reglas
- Montos sin puntos ni signo: `1500000`. Fechas `AAAA-MM-DD`; si no dice fecha, usar hoy.
- `persona` es obligatoria en fiado/abono/prestamo_recibido/preste/me_debe/cobro. Usar SIEMPRE el mismo nombre
  (la tienda es `Tienda del barrio`).
- `medio`: `Efectivo`, `Nequi`, `Bancolombia`, etc. Si no lo dice, `Efectivo` (o preguntar si importa).
- `fecha_limite`: cuándo le van a pagar / cuándo tiene que pagar.
- Categorías sugeridas: Nómina, Comida, Mercado, Transporte, Arriendo, Servicios, Celular, Salud, Ropa,
  Diversión, Familia, Tienda, Deudas, Otros. Mantenerlas consistentes.
- Cuando llega la nómina y dice "tengo que sacar X para esto", anotar el ingreso y agregar cada apartado a
  `pendientes.csv`; cuando lo pague, registrar el gasto y marcar el pendiente como `pagado`.
- Si algo es ambiguo (monto, si fue fiado o de contado, quién), preguntar antes de anotar.
- Nunca borrar movimientos viejos; para corregir, editar la fila equivocada y avisar.
- Después de cada actualización: `python3 economia.py`, mostrar un resumen corto (total, plata libre,
  deudas que cambiaron) y hacer commit + push.
