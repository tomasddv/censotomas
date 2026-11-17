"""Carteras auditables para los tres planes del Censo DDV de septiembre 2026.

No son ventas futuras ni clientes con acciones cumplidas: son oportunidades
medidas sobre el resultado oficial de DDV (distribuidor 70549).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from censo_engine import parse_censo


PLANES = {
    'P1_CORE_PLUS': {
        'Nombre': 'Apertura Core Plus',
        'Descripción': 'Activar Andes Origen/Core Plus en K+T con competencia y sin CMQ en el segmento.',
        'Objetivo': '30 PDV con presencia CMQ Core Plus verificada',
        'Meta': 30,
        'Unidad': 'PDV activados',
        'Fecha propuesta': '2027-01-15',
    },
    'P2_PREMIUM': {
        'Nombre': 'Intensidad Premium',
        'Descripción': 'Auditar precio, exhibición y ejecución de Premium en 100 K+T prioritarios.',
        'Objetivo': '100 visitas ejecutadas; SOM Premium plaza 63,0% → 66,0% (a medir en un nuevo censo)',
        'Meta': 100,
        'Unidad': 'Visitas registradas en ola 1',
        'Fecha propuesta': '2027-01-31',
    },
    'P3_KIOSCOS': {
        'Nombre': 'Recuperación de kioscos',
        'Descripción': 'Implementar plan individual de surtido y visibilidad en kioscos con SOM inferior al 60%.',
        'Objetivo': 'Recuperar 17 de 47 PDV hasta SOM ≥ 60% (47 → 30 bajo umbral)',
        'Meta': 17,
        'Unidad': 'PDV recuperados medidos',
        'Fecha propuesta': '2027-02-28',
    },
}

PLAN_IDS = list(PLANES)

BASE_COLUMNS = [
    'Plan ID', 'Plan', 'PDV', 'Supervisor', 'Promotor', 'Canal', 'Subcanal',
    'HL Mercado', 'HL CMQ', 'HL Rival', 'SOM CMQ',
    'HL segmento CMQ', 'HL segmento CCU', 'SOM segmento',
    'Prioridad', 'Ola', 'Orden',
]


def build_candidates(septiembre_file: bytes) -> pd.DataFrame:
    """Calcula la cartera sin arrastrar filtros del dashboard ni otros distris."""
    pdv, segmentos, _, errores = parse_censo(septiembre_file, 'Septiembre')
    if len(pdv) != 1442 or pdv.PDV.nunique() != len(pdv):
        raise ValueError('Universo DDV inesperado: se esperaban 1.442 PDV únicos.')
    if not errores.empty:
        raise ValueError('La fuente de septiembre presenta alertas de volumen.')

    base = pdv.set_index('PDV').copy()
    base['HL Rival'] = base['HL CCU'] + base['HL OTROS']
    grupo = segmentos.pivot_table(index='PDV', columns=['Segmento', 'Empresa'],
                                 values='HL', aggfunc='sum', fill_value=0)
    for segmento in ('CORE PLUS', 'PREMIUM'):
        for empresa in ('CMQ', 'CCU'):
            columna = (segmento, empresa)
            base[f'{segmento} {empresa}'] = (
                grupo[columna].reindex(base.index, fill_value=0)
                if columna in grupo else 0.0
            )

    def rows(mask, plan_id, metric_segment=None):
        d = base.loc[mask].copy()
        if metric_segment:
            cmq = d[f'{metric_segment} CMQ']
            ccu = d[f'{metric_segment} CCU']
            den = cmq + ccu
            d['HL segmento CMQ'] = cmq
            d['HL segmento CCU'] = ccu
            d['SOM segmento'] = (100 * cmq / den.where(den > 0)).fillna(0)
        else:
            d['HL segmento CMQ'] = 0.0
            d['HL segmento CCU'] = 0.0
            d['SOM segmento'] = d['SOM CMQ'].fillna(0)
        sort_by = 'HL Rival' if plan_id == 'P3_KIOSCOS' else 'HL Mercado'
        d = d.sort_values([sort_by, 'HL Mercado'], ascending=False, kind='stable')
        d['Plan ID'] = plan_id
        d['Plan'] = PLANES[plan_id]['Nombre']
        d['Orden'] = range(1, len(d) + 1)
        ola = 100 if plan_id == 'P2_PREMIUM' else 30 if plan_id == 'P1_CORE_PLUS' else 17
        d['Ola'] = d.Orden.apply(lambda n: 'Ola 1' if n <= ola else 'Ola 2')
        d['Prioridad'] = d.Ola.map({'Ola 1': 'Alta', 'Ola 2': 'Media'})
        d = d.reset_index().rename(columns={'index': 'PDV'})
        return d[BASE_COLUMNS].copy()

    kyt = (base.Canal == 'K+T') & (base['HL Mercado'] >= 2)
    core = rows(kyt & (base['CORE PLUS CMQ'] <= 0) &
                (base['CORE PLUS CCU'] > 0), 'P1_CORE_PLUS', 'CORE PLUS')
    premium_denom = base['PREMIUM CMQ'] + base['PREMIUM CCU']
    premium_share = 100 * base['PREMIUM CMQ'] / premium_denom.where(premium_denom > 0)
    premium = rows(kyt & (base['PREMIUM CMQ'] > 0) &
                   (base['PREMIUM CCU'] > 0) & (premium_share < 60),
                   'P2_PREMIUM', 'PREMIUM')
    kioscos = rows((base.Subcanal == 'KIOSCO/MAXIKIOSCO') &
                  (base['HL Mercado'] >= 1) & (base['SOM CMQ'] < 60), 'P3_KIOSCOS')
    result = pd.concat([core, premium, kioscos], ignore_index=True)
    counts = result.groupby('Plan ID').size().to_dict()
    expected = {'P1_CORE_PLUS': 62, 'P2_PREMIUM': 295, 'P3_KIOSCOS': 47}
    if counts != expected or result.duplicated(['Plan ID', 'PDV']).any():
        raise ValueError(f'No se reconcilian los universos de planes: {counts}.')
    for col in ['HL Mercado', 'HL CMQ', 'HL Rival', 'SOM CMQ',
                'HL segmento CMQ', 'HL segmento CCU', 'SOM segmento']:
        result[col] = result[col].round(5)
    result['PDV'] = result['PDV'].astype(str)
    return result


def load_candidates(project_root: Path) -> pd.DataFrame:
    path = project_root / 'data' / 'pda_objetivos_septiembre_2026.csv'
    if path.is_file():
        df = pd.read_csv(path, dtype={'PDV': 'string'}, keep_default_na=False)
    else:
        # Ayuda a instalaciones existentes donde el CSV no fue agregado al Git:
        # se recompone desde el archivo oficial sin inventar oportunidades.
        origin = project_root / 'data' / 'septiembre_2026_oficial.xlsx'
        if not origin.is_file():
            raise FileNotFoundError('Falta el padrón PDA y el Excel oficial de septiembre.')
        df = build_candidates(origin.read_bytes())
    if df.duplicated(['Plan ID', 'PDV']).any():
        raise ValueError('Hay duplicados por plan y PDV en el archivo de oportunidades.')
    return df
