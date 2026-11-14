#!/usr/bin/env python3
"""Mi Economía: lee los CSV de datos/ y genera REPORTE.md con saldos, deudas y resúmenes.

Uso:  python3 economia.py            -> genera REPORTE.md e imprime el resumen
      python3 economia.py 2026-11    -> resumen enfocado en ese mes
"""
import csv
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

BASE = Path(__file__).parent
MOV = BASE / "datos" / "movimientos.csv"
PEND = BASE / "datos" / "pendientes.csv"
REPORTE = BASE / "REPORTE.md"

# Efecto de cada tipo: (signo en mi plata, signo en "me debe" de la persona, signo en "le debo")
TIPOS = {
    "saldo_inicial":     (+1, 0, 0),   # plata con la que arranco en un medio
    "ingreso":           (+1, 0, 0),   # nómina, ventas, regalos...
    "gasto":             (-1, 0, 0),   # pago de contado
    "fiado":             (0, 0, +1),   # saco cosas fiadas (ej. tienda del barrio)
    "abono":             (-1, 0, -1),  # le pago/abono a alguien que le debo
    "prestamo_recibido": (+1, 0, +1),  # alguien me presta plata
    "preste":            (-1, +1, 0),  # yo le presto plata a alguien
    "me_debe":           (0, +1, 0),   # alguien me queda debiendo sin que yo saque plata (ej. un trabajo)
    "cobro":             (+1, -1, 0),  # alguien me paga lo que me debía
    "traslado":          (0, 0, 0),    # mover plata entre medios: medio = "Origen>Destino"
}


def pesos(n):
    s = f"{abs(round(n)):,}".replace(",", ".")
    return f"-${s}" if n < 0 else f"${s}"


def leer(path):
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if any((v or "").strip() for v in r.values())]


def main():
    mes = sys.argv[1] if len(sys.argv) > 1 else date.today().strftime("%Y-%m")
    movs = sorted(leer(MOV), key=lambda r: r["fecha"])
    pend = leer(PEND)

    saldo_medio = defaultdict(float)
    me_deben = defaultdict(float)
    le_debo = defaultdict(float)
    vence = {}  # persona -> fecha límite más reciente
    ing_mes, gas_mes = defaultdict(float), defaultdict(float)
    errores = []

    for i, r in enumerate(movs, 2):
        tipo = r["tipo"].strip()
        if tipo not in TIPOS:
            errores.append(f"Fila {i}: tipo desconocido '{tipo}'")
            continue
        monto = float(r["monto"])
        medio = (r.get("medio") or "Efectivo").strip() or "Efectivo"
        persona = (r.get("persona") or "").strip()
        cat = (r.get("categoria") or "Otros").strip() or "Otros"
        s_plata, s_me, s_le = TIPOS[tipo]

        if tipo == "traslado":
            origen, _, destino = medio.partition(">")
            saldo_medio[origen.strip()] -= monto
            saldo_medio[destino.strip()] += monto
        else:
            saldo_medio[medio] += s_plata * monto
        if s_me:
            me_deben[persona] += s_me * monto
        if s_le:
            le_debo[persona] += s_le * monto
        if (s_me > 0 or s_le > 0) and r.get("fecha_limite"):
            vence[persona] = r["fecha_limite"]

        if r["fecha"].startswith(mes):
            if tipo == "ingreso":
                ing_mes[cat] += monto
            elif tipo in ("gasto", "fiado"):  # lo fiado también es consumo
                gas_mes[cat] += monto

    total = sum(saldo_medio.values())
    pendientes = [p for p in pend if p["estado"].strip().lower() != "pagado"]
    total_pend = sum(float(p["monto"]) for p in pendientes)
    total_me_deben = sum(v for v in me_deben.values() if v > 0.5)
    total_le_debo = sum(v for v in le_debo.values() if v > 0.5)

    L = [f"# Mi Economía — reporte al {date.today().isoformat()}", ""]
    L += ["## Plata disponible", "", "| Medio | Saldo |", "|---|---:|"]
    L += [f"| {m} | {pesos(v)} |" for m, v in sorted(saldo_medio.items()) if abs(v) > 0.5]
    L += [f"| **Total** | **{pesos(total)}** |", ""]
    L += [f"- Pagos pendientes por hacer: **{pesos(total_pend)}**",
          f"- Plata libre (total − pendientes): **{pesos(total - total_pend)}**",
          f"- Me deben: **{pesos(total_me_deben)}** · Yo debo: **{pesos(total_le_debo)}**",
          f"- Patrimonio neto (plata + me deben − debo): **{pesos(total + total_me_deben - total_le_debo)}**", ""]

    L += ["## Personas que me deben", ""]
    filas = [(p, v) for p, v in me_deben.items() if v > 0.5]
    if filas:
        L += ["| Persona | Debe | Fecha de pago |", "|---|---:|---|"]
        L += [f"| {p} | {pesos(v)} | {vence.get(p, '')} |" for p, v in sorted(filas, key=lambda x: -x[1])]
    else:
        L += ["Nadie me debe por ahora."]
    L += [""]

    L += ["## Lo que yo debo (tienda, préstamos…)", ""]
    filas = [(p, v) for p, v in le_debo.items() if v > 0.5]
    if filas:
        L += ["| A quién | Debo | Fecha límite |", "|---|---:|---|"]
        L += [f"| {p} | {pesos(v)} | {vence.get(p, '')} |" for p, v in sorted(filas, key=lambda x: -x[1])]
    else:
        L += ["No debo nada. 🙌"]
    L += [""]

    L += ["## Pagos pendientes por hacer", ""]
    if pendientes:
        L += ["| Fecha límite | Concepto | Monto | Nota |", "|---|---|---:|---|"]
        L += [f"| {p['fecha_limite']} | {p['concepto']} | {pesos(float(p['monto']))} | {p.get('nota', '')} |"
              for p in sorted(pendientes, key=lambda p: p["fecha_limite"])]
    else:
        L += ["Nada pendiente."]
    L += [""]

    L += [f"## Mes {mes}", "",
          f"- Ingresos: **{pesos(sum(ing_mes.values()))}**",
          f"- Gastos (incluye fiado): **{pesos(sum(gas_mes.values()))}**",
          f"- Diferencia: **{pesos(sum(ing_mes.values()) - sum(gas_mes.values()))}**", ""]
    if gas_mes:
        L += ["| Categoría de gasto | Monto |", "|---|---:|"]
        L += [f"| {c} | {pesos(v)} |" for c, v in sorted(gas_mes.items(), key=lambda x: -x[1])]
        L += [""]

    L += ["## Últimos 20 movimientos", ""]
    if movs:
        L += ["| Fecha | Tipo | Monto | Medio | Categoría | Persona | Descripción |", "|---|---|---:|---|---|---|---|"]
        for r in movs[-20:][::-1]:
            L.append(f"| {r['fecha']} | {r['tipo']} | {pesos(float(r['monto']))} | {r.get('medio','')} | "
                     f"{r.get('categoria','')} | {r.get('persona','')} | {r.get('descripcion','')} |")
    else:
        L += ["Todavía no hay movimientos."]

    if errores:
        L += ["", "## ⚠️ Errores en los datos", ""] + [f"- {e}" for e in errores]

    texto = "\n".join(L) + "\n"
    REPORTE.write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
