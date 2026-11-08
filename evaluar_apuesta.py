#!/usr/bin/env python3
"""Evaluar una apuesta ANTES de hacerla.

Dos modos:

1) cuotas  – Convierte las cuotas de la casa en probabilidades, calcula el
   margen (comisión) de la casa y, si das tu propia estimación, te dice si la
   apuesta tiene valor.

   python3 evaluar_apuesta.py cuotas 2.10 3.40 3.60 --nombres Local Empate Visita
   python3 evaluar_apuesta.py cuotas 2.10 3.40 3.60 --mi-prob 52 --elegida 1

2) futbol  – Estima probabilidades con un modelo de Poisson usando los goles
   promedio de los últimos partidos de cada equipo, y compara con las cuotas.

   python3 evaluar_apuesta.py futbol --local-gf 1.8 --local-gc 0.9 \
       --visita-gf 1.1 --visita-gc 1.4 --cuota-1 1.95 --cuota-x 3.50 \
       --cuota-2 4.00 --cuota-mas25 1.85 --cuota-menos25 1.95

IMPORTANTE: ningún modelo da certezas. Esto mide si el precio (la cuota) es
justo según los datos, no garantiza el resultado.
"""

import argparse
import math
import sys

UMBRAL_VALOR = 0.03  # ±3 % de valor esperado para considerar "a favor/en contra"


# ------------------------------------------------------------ cuotas ------

def prob_implicita(cuota: float) -> float:
    return 1 / cuota


def quitar_margen(cuotas: list[float]) -> tuple[list[float], float]:
    """Devuelve (probabilidades justas, margen de la casa)."""
    implicitas = [prob_implicita(c) for c in cuotas]
    total = sum(implicitas)
    return [p / total for p in implicitas], total - 1


def valor_esperado(cuota: float, prob: float) -> float:
    """Ganancia esperada por cada 1 apostado (0.05 = +5 %)."""
    return prob * cuota - 1


def veredicto(cuota: float, prob: float) -> str:
    ve = valor_esperado(cuota, prob)
    if ve > UMBRAL_VALOR:
        texto = "A FAVOR: la cuota paga más de lo que indican los datos"
    elif ve < -UMBRAL_VALOR:
        texto = "EN CONTRA: la cuota paga menos de lo que indican los datos"
    else:
        texto = "NEUTRAL: precio justo, sin ventaja clara"
    if 0.45 <= prob <= 0.55:
        texto += " (resultado casi 50-50)"
    return texto


# ------------------------------------------------------------ Poisson -----

def poisson(k: int, lam: float) -> float:
    return math.exp(-lam) * lam ** k / math.factorial(k)


def goles_esperados(local_gf, local_gc, visita_gf, visita_gc,
                    ventaja_local=1.0) -> tuple[float, float]:
    """Goles esperados: mezcla el ataque de uno con la defensa del otro."""
    lam_local = (local_gf + visita_gc) / 2 * ventaja_local
    lam_visita = (visita_gf + local_gc) / 2
    return lam_local, lam_visita


def modelo_futbol(lam_local: float, lam_visita: float, max_goles: int = 10) -> dict:
    p1 = px = p2 = mas25 = ambos = 0.0
    marcadores = []
    for i in range(max_goles + 1):
        for j in range(max_goles + 1):
            p = poisson(i, lam_local) * poisson(j, lam_visita)
            marcadores.append(((i, j), p))
            if i > j:
                p1 += p
            elif i == j:
                px += p
            else:
                p2 += p
            if i + j > 2:
                mas25 += p
            if i > 0 and j > 0:
                ambos += p
    total = p1 + px + p2  # ~1, corrige el recorte en max_goles
    marcadores.sort(key=lambda m: m[1], reverse=True)
    return {
        "local": p1 / total, "empate": px / total, "visita": p2 / total,
        "mas_2.5": mas25 / total, "menos_2.5": 1 - mas25 / total,
        "ambos_marcan_si": ambos / total, "ambos_marcan_no": 1 - ambos / total,
        "doble_1x": (p1 + px) / total, "doble_x2": (px + p2) / total,
        "marcadores": [(f"{i}-{j}", p / total) for (i, j), p in marcadores[:5]],
    }


# ------------------------------------------------------------ salida ------

def _pct(p: float) -> str:
    return f"{100 * p:5.1f}%"


def linea_mercado(nombre: str, prob: float, cuota: float | None) -> str:
    base = f"  {nombre:<18} {_pct(prob)}   cuota justa {1 / prob:6.2f}"
    if cuota is None:
        return base
    ve = valor_esperado(cuota, prob)
    return f"{base}   casa {cuota:5.2f}   valor {100 * ve:+6.1f}%   {veredicto(cuota, prob)}"


def cmd_cuotas(a) -> int:
    nombres = a.nombres or [f"Opción {i + 1}" for i in range(len(a.cuotas))]
    if len(nombres) != len(a.cuotas):
        print("Error: --nombres debe tener tantos nombres como cuotas", file=sys.stderr)
        return 1
    justas, margen = quitar_margen(a.cuotas)
    print("PROBABILIDADES SEGÚN LA CASA")
    print(f"  Margen (comisión) de la casa: {100 * margen:.1f}%\n")
    for n, c, pj in zip(nombres, a.cuotas, justas):
        print(f"  {n:<12} cuota {c:5.2f}   implícita {_pct(prob_implicita(c))}"
              f"   real sin margen {_pct(pj)}")
    if a.mi_prob is not None:
        idx = a.elegida - 1
        if not 0 <= idx < len(a.cuotas):
            print("Error: --elegida fuera de rango", file=sys.stderr)
            return 1
        p = a.mi_prob / 100
        print(f"\nTU APUESTA: {nombres[idx]} a {a.cuotas[idx]:.2f}")
        print(f"  Tu probabilidad estimada: {_pct(p)}  (la casa dice {_pct(justas[idx])})")
        print(f"  Valor esperado: {100 * valor_esperado(a.cuotas[idx], p):+.1f}% por apuesta")
        print(f"  {veredicto(a.cuotas[idx], p)}")
    return 0


def cmd_futbol(a) -> int:
    lam_l, lam_v = goles_esperados(a.local_gf, a.local_gc, a.visita_gf,
                                   a.visita_gc, a.ventaja_local)
    m = modelo_futbol(lam_l, lam_v)
    print("MODELO DE GOLES (Poisson)")
    print(f"  Goles esperados: local {lam_l:.2f}  -  visita {lam_v:.2f}\n")
    mercados = [
        ("Gana local", "local", a.cuota_1), ("Empate", "empate", a.cuota_x),
        ("Gana visita", "visita", a.cuota_2),
        ("Local o empate", "doble_1x", None), ("Empate o visita", "doble_x2", None),
        ("Más de 2.5", "mas_2.5", a.cuota_mas25),
        ("Menos de 2.5", "menos_2.5", a.cuota_menos25),
        ("Ambos marcan: sí", "ambos_marcan_si", a.cuota_ambos_si),
        ("Ambos marcan: no", "ambos_marcan_no", a.cuota_ambos_no),
    ]
    for nombre, clave, cuota in mercados:
        print(linea_mercado(nombre, m[clave], cuota))
    print("\n  Marcadores más probables: " +
          ", ".join(f"{s} ({_pct(p).strip()})" for s, p in m["marcadores"]))
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Evaluar una apuesta antes de hacerla.")
    sub = p.add_subparsers(dest="modo", required=True)

    c = sub.add_parser("cuotas", help="analizar cuotas de un mercado")
    c.add_argument("cuotas", type=float, nargs="+", help="cuotas decimales de cada opción")
    c.add_argument("--nombres", nargs="+")
    c.add_argument("--mi-prob", type=float, help="tu probabilidad estimada en %%")
    c.add_argument("--elegida", type=int, default=1, help="opción que quieres apostar (1, 2...)")
    c.set_defaults(func=cmd_cuotas)

    f = sub.add_parser("futbol", help="modelo de goles con promedios recientes")
    for arg, ayuda in (("--local-gf", "goles a favor por partido del local"),
                       ("--local-gc", "goles en contra por partido del local"),
                       ("--visita-gf", "goles a favor por partido del visitante"),
                       ("--visita-gc", "goles en contra por partido del visitante")):
        f.add_argument(arg, type=float, required=True, help=ayuda)
    f.add_argument("--ventaja-local", type=float, default=1.0,
                   help="multiplicador de goles del local (ej. 1.1)")
    for arg in ("--cuota-1", "--cuota-x", "--cuota-2", "--cuota-mas25",
                "--cuota-menos25", "--cuota-ambos-si", "--cuota-ambos-no"):
        f.add_argument(arg, type=float)
    f.set_defaults(func=cmd_futbol)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
