#!/usr/bin/env python3
"""Análisis, estadísticas y promedios de datos de apuestas.

Lee un CSV con una apuesta por fila y genera un reporte con:
  - totales (apostado, retorno, ganancia neta)
  - ROI / yield, porcentaje de aciertos
  - promedios (cuota, monto, ganancia por apuesta)
  - aciertos esperados según la cuota vs. aciertos reales
  - rachas, máxima caída (drawdown) y desglose por categoría y por mes

Columnas obligatorias: fecha, cuota, monto, resultado
Columnas opcionales:   deporte, mercado, casa, evento
Resultados válidos:    ganada, perdida, nula  (nula = se devuelve el monto)

Uso:
  python3 analizar_apuestas.py datos/apuestas_ejemplo.csv
  python3 analizar_apuestas.py apuestas.csv --json
"""

import argparse
import csv
import json
import statistics
import sys
from dataclasses import dataclass
from datetime import date, datetime

RESULTADOS = {
    "ganada": "ganada", "g": "ganada", "win": "ganada", "w": "ganada",
    "perdida": "perdida", "p": "perdida", "loss": "perdida", "l": "perdida",
    "nula": "nula", "n": "nula", "void": "nula", "push": "nula",
}
CATEGORIAS = ("deporte", "mercado", "casa")


@dataclass
class Apuesta:
    fecha: date
    cuota: float
    monto: float
    resultado: str
    deporte: str = ""
    mercado: str = ""
    casa: str = ""
    evento: str = ""

    @property
    def ganancia(self) -> float:
        if self.resultado == "ganada":
            return self.monto * (self.cuota - 1)
        if self.resultado == "perdida":
            return -self.monto
        return 0.0


def _numero(texto: str) -> float:
    texto = texto.strip().replace(" ", "")
    if "," in texto and "." in texto:      # 1.234,56 -> 1234.56
        texto = texto.replace(".", "").replace(",", ".")
    else:
        texto = texto.replace(",", ".")
    return float(texto)


def _fecha(texto: str) -> date:
    texto = texto.strip()
    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            pass
    raise ValueError(f"fecha no reconocida: {texto!r}")


def leer_csv(ruta: str) -> list[Apuesta]:
    with open(ruta, newline="", encoding="utf-8-sig") as f:
        muestra = f.read(2048)
        f.seek(0)
        try:
            dialecto = csv.Sniffer().sniff(muestra, delimiters=",;\t")
        except csv.Error:
            dialecto = csv.excel
        lector = csv.DictReader(f, dialect=dialecto)
        lector.fieldnames = [c.strip().lower() for c in lector.fieldnames or []]
        faltan = {"fecha", "cuota", "monto", "resultado"} - set(lector.fieldnames)
        if faltan:
            raise ValueError(f"faltan columnas: {', '.join(sorted(faltan))}")

        apuestas = []
        for num, fila in enumerate(lector, start=2):
            if not any((v or "").strip() for v in fila.values()):
                continue
            try:
                resultado = RESULTADOS[fila["resultado"].strip().lower()]
                apuesta = Apuesta(
                    fecha=_fecha(fila["fecha"]),
                    cuota=_numero(fila["cuota"]),
                    monto=_numero(fila["monto"]),
                    resultado=resultado,
                    **{c: (fila.get(c) or "").strip()
                       for c in (*CATEGORIAS, "evento")},
                )
            except KeyError:
                raise ValueError(
                    f"línea {num}: resultado inválido {fila['resultado']!r}"
                ) from None
            except ValueError as e:
                raise ValueError(f"línea {num}: {e}") from None
            if apuesta.cuota <= 1 or apuesta.monto <= 0:
                raise ValueError(f"línea {num}: cuota debe ser > 1 y monto > 0")
            apuestas.append(apuesta)
    apuestas.sort(key=lambda a: a.fecha)
    return apuestas


def resumen(apuestas: list[Apuesta]) -> dict:
    """Métricas generales de un grupo de apuestas."""
    n = len(apuestas)
    if n == 0:
        return {"apuestas": 0}
    ganadas = sum(a.resultado == "ganada" for a in apuestas)
    perdidas = sum(a.resultado == "perdida" for a in apuestas)
    nulas = n - ganadas - perdidas
    decididas = ganadas + perdidas
    apostado = sum(a.monto for a in apuestas)
    ganancia = sum(a.ganancia for a in apuestas)
    cuotas = [a.cuota for a in apuestas]
    montos = [a.monto for a in apuestas]
    ganancias = [a.ganancia for a in apuestas]
    # Probabilidad implícita (1/cuota) => aciertos que "esperaba" el mercado.
    esperadas = sum(1 / a.cuota for a in apuestas if a.resultado != "nula")
    return {
        "apuestas": n,
        "ganadas": ganadas,
        "perdidas": perdidas,
        "nulas": nulas,
        "pct_aciertos": 100 * ganadas / decididas if decididas else 0.0,
        "pct_aciertos_esperado": 100 * esperadas / decididas if decididas else 0.0,
        "total_apostado": apostado,
        "retorno_total": apostado + ganancia,
        "ganancia_neta": ganancia,
        "roi_pct": 100 * ganancia / apostado,
        "cuota_promedio": statistics.mean(cuotas),
        "cuota_mediana": statistics.median(cuotas),
        "cuota_promedio_ganadas": (
            statistics.mean(a.cuota for a in apuestas if a.resultado == "ganada")
            if ganadas else 0.0
        ),
        "monto_promedio": statistics.mean(montos),
        "monto_mediano": statistics.median(montos),
        "ganancia_promedio": statistics.mean(ganancias),
        "desviacion_ganancia": statistics.stdev(ganancias) if n > 1 else 0.0,
        "mayor_ganancia": max(ganancias),
        "mayor_perdida": min(ganancias),
    }


def rachas(apuestas: list[Apuesta]) -> dict:
    mejor = peor = actual = 0
    tipo_actual = None
    for a in apuestas:
        if a.resultado == "nula":
            continue
        if a.resultado == tipo_actual:
            actual += 1
        else:
            tipo_actual, actual = a.resultado, 1
        if tipo_actual == "ganada":
            mejor = max(mejor, actual)
        else:
            peor = max(peor, actual)
    return {
        "racha_ganadora_max": mejor,
        "racha_perdedora_max": peor,
        "racha_actual": (
            f"{actual} {'ganada' if tipo_actual == 'ganada' else 'perdida'}"
            f"{'s' if actual > 1 else ''}" if tipo_actual else "-"
        ),
    }


def evolucion_banca(apuestas: list[Apuesta]) -> dict:
    acumulado = pico = caida_max = 0.0
    for a in apuestas:
        acumulado += a.ganancia
        pico = max(pico, acumulado)
        caida_max = max(caida_max, pico - acumulado)
    return {"pico_ganancia": pico, "max_caida": caida_max}


def agrupar(apuestas: list[Apuesta], clave) -> dict:
    grupos: dict[str, list[Apuesta]] = {}
    for a in apuestas:
        grupos.setdefault(clave(a) or "(sin dato)", []).append(a)
    return {k: resumen(v) for k, v in sorted(grupos.items())}


def analizar(apuestas: list[Apuesta]) -> dict:
    if not apuestas:
        return {"general": {"apuestas": 0}}
    reporte = {
        "periodo": [apuestas[0].fecha.isoformat(), apuestas[-1].fecha.isoformat()],
        "general": resumen(apuestas),
        "rachas": rachas(apuestas),
        "banca": evolucion_banca(apuestas),
        "por_mes": agrupar(apuestas, lambda a: a.fecha.strftime("%Y-%m")),
        "por_rango_cuota": agrupar(apuestas, _rango_cuota),
    }
    for c in CATEGORIAS:
        if any(getattr(a, c) for a in apuestas):
            reporte[f"por_{c}"] = agrupar(apuestas, lambda a, c=c: getattr(a, c))
    return reporte


def _rango_cuota(a: Apuesta) -> str:
    for limite, etiqueta in ((1.5, "1.01-1.49"), (2.0, "1.50-1.99"),
                             (3.0, "2.00-2.99"), (5.0, "3.00-4.99")):
        if a.cuota < limite:
            return etiqueta
    return "5.00+"


# ---------------------------------------------------------------- reporte --

def _tabla(titulo: str, grupos: dict) -> list[str]:
    ancho = max(len(titulo), *(len(k) for k in grupos))
    lineas = [
        "",
        f"{titulo:<{ancho}}  {'N':>4}  {'%Acier':>6}  {'Cuota':>5}  "
        f"{'Apostado':>10}  {'Ganancia':>10}  {'ROI%':>7}",
        "-" * (ancho + 58),
    ]
    for k, r in grupos.items():
        lineas.append(
            f"{k:<{ancho}}  {r['apuestas']:>4}  {r['pct_aciertos']:>6.1f}  "
            f"{r['cuota_promedio']:>5.2f}  {r['total_apostado']:>10.2f}  "
            f"{r['ganancia_neta']:>+10.2f}  {r['roi_pct']:>+7.1f}"
        )
    return lineas


def formatear(reporte: dict) -> str:
    g = reporte["general"]
    if g["apuestas"] == 0:
        return "No hay apuestas para analizar."
    r, b = reporte["rachas"], reporte["banca"]
    lineas = [
        "=" * 62,
        "  ANÁLISIS, ESTADÍSTICAS Y PROMEDIOS DE DATOS DE APUESTAS",
        f"  Periodo: {reporte['periodo'][0]} a {reporte['periodo'][1]}",
        "=" * 62,
        "",
        "RESUMEN",
        f"  Apuestas:               {g['apuestas']}  "
        f"(G {g['ganadas']} / P {g['perdidas']} / N {g['nulas']})",
        f"  % de aciertos:          {g['pct_aciertos']:.1f}%",
        f"  % esperado por cuotas:  {g['pct_aciertos_esperado']:.1f}%",
        f"  Total apostado:         {g['total_apostado']:.2f}",
        f"  Retorno total:          {g['retorno_total']:.2f}",
        f"  Ganancia neta:          {g['ganancia_neta']:+.2f}",
        f"  ROI (yield):            {g['roi_pct']:+.2f}%",
        "",
        "PROMEDIOS",
        f"  Cuota promedio:         {g['cuota_promedio']:.2f}"
        f"  (mediana {g['cuota_mediana']:.2f})",
        f"  Cuota prom. ganadas:    {g['cuota_promedio_ganadas']:.2f}",
        f"  Monto promedio:         {g['monto_promedio']:.2f}"
        f"  (mediana {g['monto_mediano']:.2f})",
        f"  Ganancia por apuesta:   {g['ganancia_promedio']:+.2f}"
        f"  (desv. {g['desviacion_ganancia']:.2f})",
        f"  Mayor ganancia:         {g['mayor_ganancia']:+.2f}",
        f"  Mayor pérdida:          {g['mayor_perdida']:+.2f}",
        "",
        "RACHAS Y BANCA",
        f"  Racha ganadora máx.:    {r['racha_ganadora_max']}",
        f"  Racha perdedora máx.:   {r['racha_perdedora_max']}",
        f"  Racha actual:           {r['racha_actual']}",
        f"  Pico de ganancia:       {b['pico_ganancia']:+.2f}",
        f"  Máxima caída:           {b['max_caida']:.2f}",
    ]
    for clave, titulo in (("por_deporte", "Deporte"), ("por_mercado", "Mercado"),
                          ("por_casa", "Casa"), ("por_rango_cuota", "Rango cuota"),
                          ("por_mes", "Mes")):
        if clave in reporte:
            lineas += _tabla(titulo, reporte[clave])
    return "\n".join(lineas)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Estadísticas y promedios de apuestas.")
    p.add_argument("csv", help="archivo CSV con las apuestas")
    p.add_argument("--json", action="store_true", help="salida en formato JSON")
    p.add_argument("--desde", type=_fecha, help="filtrar desde fecha (incluida)")
    p.add_argument("--hasta", type=_fecha, help="filtrar hasta fecha (incluida)")
    p.add_argument("--deporte", help="filtrar por deporte")
    args = p.parse_args(argv)

    try:
        apuestas = leer_csv(args.csv)
    except (OSError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    if args.desde:
        apuestas = [a for a in apuestas if a.fecha >= args.desde]
    if args.hasta:
        apuestas = [a for a in apuestas if a.fecha <= args.hasta]
    if args.deporte:
        apuestas = [a for a in apuestas if a.deporte.lower() == args.deporte.lower()]

    reporte = analizar(apuestas)
    if args.json:
        print(json.dumps(reporte, indent=2, ensure_ascii=False))
    else:
        print(formatear(reporte))
    return 0


if __name__ == "__main__":
    sys.exit(main())
