"""Controles reproducibles para el archivo final de septiembre 2026 (DDV 70549)."""

from pathlib import Path
import sys
import unittest
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from censo_engine import indicadores, parse_censo, seleccionar_criterio_publicacion  # noqa: E402


class TestResultadosOficiales(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = ROOT / 'data' / 'septiembre_2026_oficial.xlsx'
        cls.pdv, cls.segments, cls.presences, cls.errors = parse_censo(
            source.read_bytes(), 'Septiembre'
        )

    def test_totales_cierre(self):
        total = indicadores(self.pdv)
        self.assertEqual(total['PDV'], 1442)
        self.assertEqual(self.pdv['Censable'].sum(), 1127)
        self.assertAlmostEqual(total['HL CMQ'], 6380.55663, places=4)
        self.assertAlmostEqual(total['HL CCU'], 1861.68, places=4)
        self.assertAlmostEqual(total['HL OTROS'], 440.61492, places=4)
        self.assertAlmostEqual(total['HL mercado'], 8682.85155, places=4)
        self.assertAlmostEqual(total['SOM'], 73.484576, places=4)

    def test_segmentos_reconcilian(self):
        for owner in ('CMQ', 'CCU', 'OTROS'):
            subtotal = self.segments.loc[self.segments.Empresa == owner, 'HL'].sum()
            self.assertAlmostEqual(subtotal, self.pdv[f'HL {owner}'].sum(), places=4)

    def test_exclusiones_y_fuente(self):
        self.assertTrue(self.errors.empty)
        self.assertEqual(self.pdv['Fuente'].nunique(), 1)
        marcas = self.presences.Marca.str.upper().tolist()
        self.assertFalse(any('GANCIA' in m or 'VINOS VALUE' in m for m in marcas))

    def test_criterio_oficial_vs_censo_anterior(self):
        abril, *_ = parse_censo((ROOT / 'data' / 'abril_2026.xlsx').read_bytes(), 'Abril')
        base = pd.concat([abril, self.pdv], ignore_index=True)
        ajustado = seleccionar_criterio_publicacion(base, 'Abril', 'Septiembre')
        ant = ajustado[ajustado.Periodo == 'Abril']
        act = ajustado[ajustado.Periodo == 'Septiembre']
        self.assertEqual(len(abril), 1253)
        self.assertEqual(len(ant), 1158)
        self.assertEqual(len(act), 1442)
        self.assertAlmostEqual(indicadores(abril)['SOM'], 71.6526705, places=5)
        self.assertAlmostEqual(indicadores(ant)['SOM'], 71.768908, places=5)
        self.assertAlmostEqual(indicadores(act)['SOM'], 73.484576, places=5)
        # Redondeo oficial: anterior 71,8 %, actual 73,5 %, diferencia +1,7 pp.
        self.assertEqual(round(indicadores(ant)['SOM'], 1), 71.8)
        self.assertEqual(round(indicadores(act)['SOM'], 1), 73.5)
        self.assertEqual(round(indicadores(act)['SOM']-indicadores(ant)['SOM'], 1), 1.7)


if __name__ == '__main__':
    unittest.main()
