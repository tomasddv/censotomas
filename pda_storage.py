"""Persistencia del seguimiento PDA: SQLite local o Google Sheets privado.

Los datos base del censo no se modifican. Solo se guardan acciones por
(Plan ID, PDV). Para Streamlit Community Cloud usar Google Sheets; la base
SQLite local es apropiada para PC/servidor con disco persistente.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sqlite3

import pandas as pd


EDITABLE = [
    'Estado', 'Responsable', 'Fecha visita', 'Próxima gestión',
    'Presencia validada', 'Fecha verificación',
    'SOM posterior', 'Fecha medición',
    'Evidencia', 'Observaciones',
]
KEYS = ['Plan ID', 'PDV']
STORED = KEYS + EDITABLE + ['Actualizado']
ESTADOS = ['Pendiente', 'Contactado', 'En gestión', 'Ejecutado', 'Verificado', 'Descartado']


def empty_progress() -> pd.DataFrame:
    return pd.DataFrame(columns=STORED)


def merge_with_base(base: pd.DataFrame, progress: pd.DataFrame) -> pd.DataFrame:
    """Combina base inmutable y ediciones persistidas sin multiplicar filas."""
    b = base.copy()
    b['PDV'] = b['PDV'].astype(str)
    if progress.empty:
        p = empty_progress()
    else:
        p = progress.copy()
        p['PDV'] = p['PDV'].astype(str)
        p = p.drop_duplicates(KEYS, keep='last')
    data = b.merge(p, on=KEYS, how='left', validate='one_to_one')
    for col in EDITABLE + ['Actualizado']:
        if col not in data:
            data[col] = ''
        data[col] = data[col].where(data[col].notna(), '')
    data['Responsable'] = data['Responsable'].where(
        data['Responsable'].astype(str).str.strip() != '', data['Promotor'])
    data['Estado'] = data['Estado'].where(
        data['Estado'].astype(str).str.strip() != '', 'Pendiente')
    data['Presencia validada'] = data['Presencia validada'].where(
        data['Presencia validada'].isin(['Sí', 'No']), 'No')
    data['SOM posterior'] = pd.to_numeric(data['SOM posterior'], errors='coerce')
    return data


def clean_updates(df: pd.DataFrame, valid_pairs: set[tuple[str, str]]) -> pd.DataFrame:
    """Importa solo campos autorizados, sin permitir PDV inventados."""
    if not set(KEYS).issubset(df.columns):
        raise ValueError('La carga necesita las columnas Plan ID y PDV.')
    d = df.copy()
    d['PDV'] = d['PDV'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
    d['Plan ID'] = d['Plan ID'].astype(str).str.strip()
    if d.duplicated(KEYS).any():
        raise ValueError('Hay registros repetidos para un mismo plan y PDV.')
    invalid = [key for key in zip(d['Plan ID'], d['PDV']) if key not in valid_pairs]
    if invalid:
        raise ValueError(f'La carga contiene {len(invalid)} combinaciones plan-PDV no incluidas en la base oficial.')
    for col in EDITABLE:
        if col not in d:
            d[col] = ''
    d['Estado'] = d['Estado'].replace('', 'Pendiente').fillna('Pendiente')
    if not d['Estado'].isin(ESTADOS).all():
        raise ValueError('Se encontraron estados de acción no reconocidos.')
    d['Presencia validada'] = d['Presencia validada'].replace('', 'No').fillna('No')
    if not d['Presencia validada'].isin(['Sí', 'No']).all():
        raise ValueError('Presencia validada solo admite Sí o No.')
    som_input = d['SOM posterior'].fillna('').astype(str).str.strip()
    # Un porcentaje escrito incorrectamente no debe convertirse silenciosamente
    # en un valor vacío: eso falsearía la lectura de recuperaciones medidas.
    som_numeric = pd.to_numeric(som_input.str.replace(',', '.', regex=False), errors='coerce')
    if (som_input.ne('') & som_numeric.isna()).any():
        raise ValueError('El SOM posterior debe ser numérico; ejemplo: 62,5.')
    d['SOM posterior'] = som_numeric
    if d['SOM posterior'].notna().any() and not d['SOM posterior'].dropna().between(0, 100).all():
        raise ValueError('El SOM posterior debe estar entre 0 y 100%.')
    for col in ['Fecha visita', 'Próxima gestión', 'Fecha verificación', 'Fecha medición']:
        val = d[col].fillna('').astype(str).str.strip()
        invalid_dates = val[(val != '') & pd.to_datetime(val, errors='coerce', format='%Y-%m-%d').isna()]
        if len(invalid_dates):
            raise ValueError(f'Fecha inválida en {col}; usar AAAA-MM-DD.')
        d[col] = val
    for col in ['Responsable', 'Evidencia', 'Observaciones']:
        d[col] = d[col].fillna('').astype(str)
    d['Actualizado'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
    return d[STORED].copy()


class LocalStorage:
    mode = 'SQLite local'

    def __init__(self, project_root: Path):
        folder = project_root / '.local'
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / 'pda_seguimiento.sqlite3'
        with sqlite3.connect(self.path) as cx:
            cx.execute('''CREATE TABLE IF NOT EXISTS seguimiento (
                plan_id TEXT NOT NULL, pdv TEXT NOT NULL, estado TEXT,
                responsable TEXT, fecha_visita TEXT, proxima_gestion TEXT,
                presencia_validada TEXT, fecha_verificacion TEXT,
                som_posterior REAL, fecha_medicion TEXT, evidencia TEXT,
                observaciones TEXT, actualizado TEXT,
                PRIMARY KEY (plan_id, pdv))''')
            cx.execute('''CREATE TABLE IF NOT EXISTS metas (
                plan_id TEXT PRIMARY KEY, meta INTEGER NOT NULL)''')

    def load(self) -> pd.DataFrame:
        with sqlite3.connect(self.path) as cx:
            frame = pd.read_sql_query('SELECT * FROM seguimiento', cx)
        if frame.empty:
            return empty_progress()
        frame.columns = STORED
        return frame

    def save(self, rows: pd.DataFrame) -> int:
        if rows.empty:
            return 0
        q = ('INSERT INTO seguimiento VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?) '
             'ON CONFLICT(plan_id,pdv) DO UPDATE SET '
             'estado=excluded.estado,responsable=excluded.responsable,'
             'fecha_visita=excluded.fecha_visita,proxima_gestion=excluded.proxima_gestion,'
             'presencia_validada=excluded.presencia_validada,'
             'fecha_verificacion=excluded.fecha_verificacion,'
             'som_posterior=excluded.som_posterior,fecha_medicion=excluded.fecha_medicion,'
             'evidencia=excluded.evidencia,observaciones=excluded.observaciones,'
             'actualizado=excluded.actualizado')
        values = []
        for _, r in rows.iterrows():
            v = [r['Plan ID'], r['PDV'], r['Estado'], r['Responsable'],
                 r['Fecha visita'], r['Próxima gestión'], r['Presencia validada'],
                 r['Fecha verificación'], r['SOM posterior'], r['Fecha medición'],
                 r['Evidencia'], r['Observaciones'], r['Actualizado']]
            values.append(tuple(None if pd.isna(x) else x for x in v))
        with sqlite3.connect(self.path) as cx:
            cx.executemany(q, values)
        return len(values)

    def goals(self) -> dict[str, int]:
        with sqlite3.connect(self.path) as cx:
            return dict(cx.execute('SELECT plan_id,meta FROM metas').fetchall())

    def save_goals(self, goals: dict[str, int]):
        with sqlite3.connect(self.path) as cx:
            cx.executemany('INSERT INTO metas VALUES (?,?) ON CONFLICT(plan_id) '
                           'DO UPDATE SET meta=excluded.meta', list(goals.items()))


class GoogleSheetsStorage:
    mode = 'Google Sheets (persistente)'

    def __init__(self, sheet_id: str, service_account: dict):
        import gspread
        client = gspread.service_account_from_dict(service_account)
        book = client.open_by_key(sheet_id)
        try:
            self.ws = book.worksheet('Seguimiento')
        except gspread.WorksheetNotFound:
            self.ws = book.add_worksheet('Seguimiento', rows=1000, cols=13)
        if self.ws.row_values(1) != STORED:
            if self.ws.row_values(1):
                raise ValueError('La hoja Seguimiento tiene encabezados distintos. No se modificó para proteger tus datos.')
            self.ws.update('A1:M1', [STORED])
        try:
            self.metas = book.worksheet('Metas')
        except gspread.WorksheetNotFound:
            self.metas = book.add_worksheet('Metas', rows=20, cols=2)
        if not self.metas.row_values(1):
            self.metas.update('A1:B1', [['Plan ID', 'Meta']])

    def load(self) -> pd.DataFrame:
        # get_all_records puede convertir códigos de clientes en números y
        # perder ceros iniciales. En el seguimiento la clave PDV es texto.
        values = self.ws.get_all_values()
        if len(values) <= 1:
            return empty_progress()
        return pd.DataFrame([row[:len(STORED)] + [''] * max(0, len(STORED) - len(row))
                             for row in values[1:]], columns=STORED)

    def save(self, rows: pd.DataFrame) -> int:
        if rows.empty:
            return 0
        existing = self.ws.get_all_values()
        location = {(str(r[0]),str(r[1])):idx+1 for idx,r in enumerate(existing[1:], start=1)
                    if len(r)>=2}
        updates,append = [],[]
        for _,r in rows.iterrows():
            pair = (str(r['Plan ID']),str(r['PDV']))
            values = ['' if pd.isna(r[col]) else r[col] for col in STORED]
            if pair in location:
                n = location[pair]
                updates.append({'range':f'A{n}:M{n}','values':[values]})
            else:
                append.append(values)
        if updates:
            self.ws.batch_update(updates)
        if append:
            self.ws.append_rows(append, value_input_option='RAW')
        return len(rows)

    def goals(self) -> dict[str, int]:
        return {r['Plan ID']:int(r['Meta']) for r in self.metas.get_all_records() if r.get('Meta')}

    def save_goals(self, goals: dict[str, int]):
        data = [['Plan ID','Meta']] + [[k,int(v)] for k,v in goals.items()]
        self.metas.update(f'A1:B{len(data)}',data)


def make_storage(project_root: Path, secrets=None):
    """No consulta conexiones externas si la configuración no fue provista."""
    if secrets is not None:
        try:
            sheet_id = secrets.get('pda_sheet_id')
            account = secrets.get('gcp_service_account')
        except Exception:
            sheet_id,account = None,None
        if sheet_id and account:
            return GoogleSheetsStorage(str(sheet_id), dict(account))
    return LocalStorage(project_root)
