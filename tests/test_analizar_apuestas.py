import os
import sys
import tempfile
import unittest
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import analizar_apuestas as aa  # noqa: E402


def ap(cuota, monto, resultado, dia=1, deporte="Fútbol"):
    return aa.Apuesta(date(2026, 1, dia), cuota, monto, resultado, deporte)


class PruebasAnalisis(unittest.TestCase):
    def setUp(self):
        self.apuestas = [
            ap(2.0, 10, "ganada", 1),
            ap(3.0, 10, "perdida", 2),
            ap(1.5, 20, "ganada", 3),
            ap(2.5, 10, "nula", 4, "Tenis"),
            ap(2.0, 10, "perdida", 5, "Tenis"),
        ]

    def test_ganancia_por_apuesta(self):
        self.assertEqual([a.ganancia for a in self.apuestas], [10, -10, 10, 0, -10])

    def test_resumen(self):
        r = aa.resumen(self.apuestas)
        self.assertEqual(r["apuestas"], 5)
        self.assertEqual((r["ganadas"], r["perdidas"], r["nulas"]), (2, 2, 1))
        self.assertAlmostEqual(r["pct_aciertos"], 50.0)
        self.assertAlmostEqual(r["total_apostado"], 60)
        self.assertAlmostEqual(r["ganancia_neta"], 0)
        self.assertAlmostEqual(r["roi_pct"], 0)
        self.assertAlmostEqual(r["cuota_promedio"], 2.2)
        self.assertAlmostEqual(r["monto_promedio"], 12)
        # esperado = (1/2 + 1/3 + 1/1.5 + 1/2) / 4 decididas
        self.assertAlmostEqual(r["pct_aciertos_esperado"], 100 * 2.0 / 4)

    def test_rachas_y_banca(self):
        r = aa.rachas(self.apuestas)
        self.assertEqual(r["racha_ganadora_max"], 1)
        self.assertEqual(r["racha_perdedora_max"], 1)
        self.assertEqual(r["racha_actual"], "1 perdida")
        b = aa.evolucion_banca(self.apuestas)
        self.assertAlmostEqual(b["pico_ganancia"], 10)
        self.assertAlmostEqual(b["max_caida"], 10)

    def test_agrupado_por_deporte(self):
        rep = aa.analizar(self.apuestas)
        self.assertEqual(rep["por_deporte"]["Tenis"]["apuestas"], 2)
        self.assertAlmostEqual(rep["por_deporte"]["Fútbol"]["ganancia_neta"], 10)

    def test_lectura_csv_formato_europeo(self):
        contenido = "Fecha;Cuota;Monto;Resultado\n15/03/2026;1,85;1.000,50;G\n"
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False,
                                         encoding="utf-8") as f:
            f.write(contenido)
        try:
            [a] = aa.leer_csv(f.name)
        finally:
            os.unlink(f.name)
        self.assertEqual(a.fecha, date(2026, 3, 15))
        self.assertAlmostEqual(a.cuota, 1.85)
        self.assertAlmostEqual(a.monto, 1000.5)
        self.assertEqual(a.resultado, "ganada")

    def test_resultado_invalido(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            f.write("fecha,cuota,monto,resultado\n2026-01-01,2,10,quizas\n")
        try:
            with self.assertRaises(ValueError):
                aa.leer_csv(f.name)
        finally:
            os.unlink(f.name)

    def test_sin_apuestas(self):
        self.assertEqual(aa.formatear(aa.analizar([])), "No hay apuestas para analizar.")


if __name__ == "__main__":
    unittest.main()
