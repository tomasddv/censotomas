"""Prueba reproducible del motor de datos sobre el censo adjunto de DDV."""
from pathlib import Path
import pandas as pd
from censo_engine import parse_censo, indicadores, segment_summary, priorities
ROOT=Path(__file__).parent
apr,seg_a,pres_a,errors_a=parse_censo((ROOT/'data/abril_2026.xlsx').read_bytes(),'Abril')
sep,seg_s,pres_s,errors_s=parse_censo((ROOT/'data/septiembre_2026.xlsx').read_bytes(),'Septiembre')
a=indicadores(apr); s=indicadores(sep)
assert a['PDV']==1253,(a['PDV'],'PDV Abril')
assert s['PDV']==1302,(s['PDV'],'PDV Septiembre')
assert len(set(apr.PDV)&set(sep.PDV))==1158
assert abs(a['SOM']-71.65267052557178)<1e-5
assert abs(s['SOM']-69.86426984968837)<1e-5
assert s['No censables']==175 and s['No censables con HL']==162
assert abs(a['HL mercado'] - 9803.7383116) < 1e-5
assert abs(s['HL mercado'] - 9110.979964) < 1e-5
seg=segment_summary(apr,sep,pd.concat([seg_a,seg_s]))
core_plus=seg[seg.Segmento=='CORE PLUS'].iloc[0]
assert abs(core_plus['Δ pp'] - (-12.850092))<0.001
assert len(priorities(sep,apr,1,60))>0
print('VALIDACIÓN CORRECTA')
print(f"Abril: {a['PDV']} PDV, {a['HL mercado']:.2f} HL, SOM {a['SOM']:.2f}%")
print(f"Septiembre: {s['PDV']} PDV, {s['HL mercado']:.2f} HL, SOM {s['SOM']:.2f}%")
print('Clientes coincidentes: 1.158 | No censables con HL en septiembre: 162')
print('Advertencia: este validador comprueba el motor, no renderiza Streamlit.')
