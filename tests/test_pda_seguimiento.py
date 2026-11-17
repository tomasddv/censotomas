"""Pruebas de padrón, medición de avances y persistencia."""
import sys
import tempfile
import types
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.modules.setdefault('streamlit', types.ModuleType('streamlit'))

from pda_candidates import load_candidates
from pda_storage import LocalStorage, clean_updates, merge_with_base
from pda_tab import summary


class SeguimientoPdaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = load_candidates(ROOT)
        cls.pairs = set(zip(cls.base['Plan ID'], cls.base['PDV'].astype(str)))

    def test_poblacion_y_condiciones(self):
        df = self.base
        self.assertEqual(len(df), 404)
        self.assertEqual(df['PDV'].nunique(), 339)
        self.assertEqual(df.groupby('Plan ID').size().to_dict(),
                         {'P1_CORE_PLUS':62,'P2_PREMIUM':295,'P3_KIOSCOS':47})
        p1 = df[df['Plan ID']=='P1_CORE_PLUS']
        p2 = df[df['Plan ID']=='P2_PREMIUM']
        p3 = df[df['Plan ID']=='P3_KIOSCOS']
        self.assertTrue((p1['HL segmento CMQ']<=0).all())
        self.assertTrue((p1['HL segmento CCU']>0).all())
        self.assertTrue((p2['HL segmento CMQ']>0).all())
        self.assertTrue((p2['HL segmento CCU']>0).all())
        self.assertTrue((p2['SOM segmento']<60).all())
        self.assertTrue((p3['SOM CMQ']<60).all())
        self.assertTrue((p3['Subcanal']=='KIOSCO/MAXIKIOSCO').all())
        self.assertEqual(int((p2.Ola=='Ola 1').sum()),100)

    def test_medicion_con_evidencia_y_sin_doble_conteo(self):
        data = merge_with_base(self.base,pd.DataFrame())
        self.assertEqual([r['Logrado'] for r in summary(data,{})],[0,0,0])
        p1=data.index[data['Plan ID']=='P1_CORE_PLUS'][0]
        p2=data.index[(data['Plan ID']=='P2_PREMIUM')&(data.Ola=='Ola 1')][0]
        p3=data.index[data['Plan ID']=='P3_KIOSCOS'][0]
        data.at[p1,'Presencia validada']='Sí'
        data.at[p1,'Fecha verificación']='2026-11-01'
        data.at[p2,'Fecha visita']='2026-11-02'
        data.at[p3,'SOM posterior']=65.0
        data.at[p3,'Fecha medición']='2026-11-03'
        self.assertEqual([r['Logrado'] for r in summary(data,{})],[1,1,1])
        data.at[p3,'Fecha medición']=''
        self.assertEqual(summary(data,{})[2]['Logrado'],0)
        data.at[p2,'Fecha visita']='2027-12-02'
        self.assertEqual(summary(data,{})[1]['Logrado'],0)

    def test_almacenamiento_reapertura_y_respaldo(self):
        sample = self.base.iloc[0]
        raw = pd.DataFrame([{
            'Plan ID':sample['Plan ID'],'PDV':sample['PDV'],
            'Estado':'Verificado','Responsable':sample.Promotor,
            'Fecha visita':'2026-12-03','Próxima gestión':'2026-12-16',
            'Presencia validada':'Sí','Fecha verificación':'2026-12-03',
            'SOM posterior':62.0,'Fecha medición':'2026-12-03',
            'Evidencia':'https://ejemplo.invalid/foto','Observaciones':'Visitado',
        }])
        cleaned = clean_updates(raw,self.pairs)
        with tempfile.TemporaryDirectory() as path:
            s1 = LocalStorage(Path(path))
            self.assertEqual(s1.save(cleaned),1)
            s1.save_goals({'P1_CORE_PLUS':35})
            s2 = LocalStorage(Path(path))
            self.assertEqual(len(s2.load()),1)
            self.assertEqual(s2.goals()['P1_CORE_PLUS'],35)
            restored = merge_with_base(self.base,s2.load())
            row = restored[(restored['Plan ID']==sample['Plan ID']) &
                           (restored.PDV==sample.PDV)].iloc[0]
            self.assertEqual(row['Estado'],'Verificado')
            self.assertEqual(row['Presencia validada'],'Sí')
            self.assertEqual(row['Fecha verificación'],'2026-12-03')

    def test_rechaza_cliente_ajeno_y_fechas_invalidas(self):
        d = pd.DataFrame([{'Plan ID':'P1_CORE_PLUS','PDV':'99999999'}])
        with self.assertRaises(ValueError):clean_updates(d,self.pairs)
        sample = self.base.iloc[0]
        d = pd.DataFrame([{'Plan ID':sample['Plan ID'],'PDV':sample['PDV'],
                           'Fecha visita':'31/99/2026'}])
        with self.assertRaises(ValueError):clean_updates(d,self.pairs)
        d = pd.DataFrame([{'Plan ID':sample['Plan ID'],'PDV':sample['PDV'],
                           'SOM posterior':'sin dato'}])
        with self.assertRaises(ValueError):clean_updates(d,self.pairs)


if __name__=='__main__':unittest.main()
