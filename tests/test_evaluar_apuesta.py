import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import evaluar_apuesta as ev  # noqa: E402


class PruebasEvaluar(unittest.TestCase):
    def test_quitar_margen(self):
        justas, margen = ev.quitar_margen([1.90, 1.90])
        self.assertAlmostEqual(justas[0], 0.5)
        self.assertAlmostEqual(margen, 2 / 1.9 - 1)

    def test_valor_esperado(self):
        self.assertAlmostEqual(ev.valor_esperado(2.2, 0.5), 0.1)
        self.assertIn("A FAVOR", ev.veredicto(2.2, 0.5))
        self.assertIn("50-50", ev.veredicto(2.2, 0.5))
        self.assertIn("EN CONTRA", ev.veredicto(1.5, 0.5))
        self.assertIn("NEUTRAL", ev.veredicto(2.0, 0.5))

    def test_modelo_futbol_suma_uno(self):
        m = ev.modelo_futbol(1.5, 1.1)
        self.assertAlmostEqual(m["local"] + m["empate"] + m["visita"], 1)
        self.assertGreater(m["local"], m["visita"])
        self.assertAlmostEqual(m["mas_2.5"] + m["menos_2.5"], 1)

    def test_equipos_iguales_simetrico(self):
        m = ev.modelo_futbol(1.3, 1.3)
        self.assertAlmostEqual(m["local"], m["visita"])

    def test_goles_esperados(self):
        self.assertEqual(ev.goles_esperados(2, 1, 1, 2), (2.0, 1.0))


if __name__ == "__main__":
    unittest.main()
