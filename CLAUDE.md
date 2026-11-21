# Mi Economía — instrucciones para Claude

Este repo es el registro de la economía personal del usuario (pesos colombianos, COP).
El usuario habla en español colombiano informal y te cuenta sus ingresos, gastos, fiados, préstamos, etc.
Tu trabajo: anotarlo en los CSV, correr el reporte, contestarle con el resumen y hacer commit + push.

## Archivos
- `datos/movimientos.csv` — todo movimiento de plata. Columnas:
  `fecha,tipo,monto,medio,categoria,persona,descripcion,fecha_limite`
- `datos/pendientes.csv` — pagos que el usuario tiene que hacer (arriendo, servicios, apartados de la nómina).
  Columnas: `fecha_limite,concepto,monto,estado,nota`. Estados: `programado` (pago futuro que saldrá de la próxima
  plata que entre; NO se descuenta de la plata libre), `pendiente` (ya hay que sacarlo de la plata actual; SÍ se
  descuenta) y `pagado`. Cuando entre la nómina, pasar a `pendiente` los programados que salen de ella.
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
- `medio`: `Efectivo`, `Nequi`, `Bancolombia`, `Nu Flujo`, `Nu Emergencia`, `Acciones`. Si no lo dice, `Efectivo` (o preguntar si importa).
  Cuando dice "en efectivo" o "saqué X en efectivo" es plata de la billetera (`Efectivo`), NO un retiro de cajero.
- `fecha_limite`: cuándo le van a pagar / cuándo tiene que pagar.
- Categorías sugeridas: Nómina, Comida, Mercado, Hogar, Transporte, Arriendo, Servicios, Celular, Salud, Ropa,
  Diversión, Familia, Tienda, Deudas, Suscripciones, Otros. Mantenerlas consistentes.
- Categoría `Novia` con secciones, se escribe `Novia/<sección>`: `Novia/Comida`, `Novia/Salidas a comer`,
  `Novia/Regalos`, `Novia/Transferencias`, `Novia/Moteliadas`. Todo gasto para la novia va ahí (aunque sea fiado
  en la tienda). El reporte las agrupa bajo "Novia". Otras categorías pueden usar el mismo formato `Principal/Sección`.
- Cuando llega la nómina y dice "tengo que sacar X para esto", anotar el ingreso y agregar cada apartado a
  `pendientes.csv`; cuando lo pague, registrar el gasto y marcar el pendiente como `pagado`.
- Si algo es ambiguo (monto, si fue fiado o de contado, quién), preguntar antes de anotar.
- Nunca borrar movimientos viejos; para corregir, editar la fila equivocada y avisar.
- Después de cada actualización: `python3 economia.py`, mostrar un resumen corto (total, plata libre,
  deudas que cambiaron) y hacer commit + push.

## Gastos fijos conocidos
Cuando se pague uno, marcarlo `pagado` y agregar el de la siguiente quincena/mes como `programado`.
- Plata para mamá (casa): $150.000 cada quincena (días 15 y 30). La del 15-nov se pagó el 17-nov.
- Colaboración mamá (queso, granola, comida que él come): ~$50.000 cada quincena. Categoría `Mercado`.
- Plata para la novia (salidas, comida, motel): $50.000 cada quincena. Categoría `Novia/<sección>`, persona `Novia`.
- Netflix: $18.900 mensual, débito automático de Bancolombia (~día 21). Categoría `Suscripciones/Netflix`.
- Claude Code: $63.490 mensual desde Bancolombia (fecha de cobro por confirmar). Categoría `Suscripciones/Claude`.
- Tienda del barrio: cuenta corriente que va sumando (fiados) y se baja con abonos parciales ($50.000, $100.000...)
  cada mes. NO programar el pago total; registrar cada abono como `abono` a `Tienda del barrio`.
- Celular a cuotas (persona `Celular a cuotas`): $1.050.000 en 6 cuotas de $175.000 sin intereses, la primera
  mensuales, se pagan el día 23 (dic-2026 a may-2027) con la plata de la nómina del 15. Ya están programadas en
  `pendientes.csv`. Cada cuota pagada = `abono` de 175000 a `Celular a cuotas` + marcar la cuota `pagado`.

## Ingresos y ahorro
- Nómina: quincena del 30 ≈ $1.050.000 (trae el auxilio de transporte); quincena del 15 ≈ $800.000–850.000.
- El contrato termina el 15-dic-2026 y firma el nuevo esa misma semana. Liquidación: cesantías del año, intereses,
  prima del semestre y vacaciones pagadas en plata (no las toma). Estimado ~$4.000.000 si gana el mínimo; no confirmado.
- Nu tiene dos cajitas: `Nu Flujo` (mete y saca; cuenta como plata para gastar) y `Nu Emergencia` (fondo de
  emergencia, NO se toca). `Nu Emergencia` y `Acciones` son AHORRO (`AHORRO` en economia.py): cuentan en el total
  pero no en la plata libre. Meter plata ahí = `traslado` (ej. `Bancolombia>Nu Emergencia`), no `gasto`.
- Meta: $60.000/mes a Nu Emergencia (≈9 % E.A.) = $30.000 por quincena, y $30.000–50.000 por quincena en acciones
  (le interesan tecnológicas grandes tipo Apple/Google, Coca-Cola y algo de S&P 500). Programar ambos cada quincena.
