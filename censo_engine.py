"""Motor de lectura y cálculos del Censo DDV. No modifica los archivos de origen."""
from __future__ import annotations
from collections import defaultdict
from functools import lru_cache
import io
import re
import unicodedata
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd

NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
RELS = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
PKG = '{http://schemas.openxmlformats.org/package/2006/relationships}'
SEGS = ['VALUE', 'CORE', 'CORE PLUS', 'PREMIUM', 'SUPER PREMIUM', 'SIN CLASIFICAR']
OWNERS = ['CMQ', 'CCU', 'OTROS']


def norm(value):
    if value is None: return ''
    value = unicodedata.normalize('NFKD', str(value)).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'\s+', ' ', value.upper().strip())


def numeric(v):
    try: return float(v or 0)
    except (TypeError, ValueError): return 0.0


def clean_id(v):
    if v is None: return ''
    try:
        return str(int(float(v))) if float(v).is_integer() else str(v).strip()
    except (ValueError, TypeError, OverflowError):
        return str(v).strip()


def staff(v, kind):
    s = norm(re.sub(r'^\s*\d+\s*-\s*', '', str(v or '')))
    tokens = ' '.join(sorted(s.split()))
    labels = {
        'BRUNO ISMAEL': 'BRUNO ISMAEL', 'CASCO HERNAN': 'HERNAN CASCO',
        'ANIBAL VITI': 'ANIBAL VITI', 'SIRI MARTIN': 'MARTIN SIRI',
        'NICASTRO LUCAS': 'LUCAS NICASTRO', 'POCHETINO NICOLAS': 'NICOLAS POCHETINO',
        'BISS FEDERICO': 'FEDERICO BISS', 'FABRE GASTON': 'GASTON FABRE',
        'ALVAREZ PABLO': 'PABLO ALVAREZ', 'GARCIA MATIAS': 'MATIAS GARCIA',
        'ROJAS ALEXANDER': 'ALEXANDER ROJAS', 'MENDEZ CARLOS': 'CARLOS MENDEZ',
        'VITI ANIBAL': 'ANIBAL VITI',
    }
    return labels.get(tokens, s or 'SIN ASIGNAR')


def canal(v):
    s = norm(v)
    return {'MAY': 'MAYO'}.get(s, s or 'SIN DATO')


def subcanal(v):
    s = norm(v)
    aliases = {
        'ALMACEN AUTOSERV': 'ALMACEN AUTOSERVICE',
        'KIOSCO/MAXIKIOSC': 'KIOSCO/MAXIKIOSCO',
        'CARNICERIA/POLLE': 'CARNICERIA/POLLERIA',
        'AUTOSERVICIO IND': 'AUTOSERVICIO INDEPENDIENTE',
        'FIAMBRERIA/QUESE': 'FIAMBRERIA/QUESERIA',
        'ROTISERIA/COM P': 'ROTISERIA/COM P LLEVAR',
    }
    return aliases.get(s, s or 'SIN DATO')


def calibre(v):
    s = norm(v)
    if not s or s in {'TOTAL CALIBRES', 'TC', '0.0'}: return ''
    if '710' in s: return '710 cc'
    if '410/473' in s or '473' in s: return '410/473 cc'
    if '330' in s or '275' in s: return '330/275 cc'
    if '1,2' in s or '1.2' in s or '1,5' in s or '1.5' in s: return '1,2 / 1,5 L'
    if '500' in s: return '500 cc'
    if '940' in s: return '940 cc / otros'
    if 'OW' in s or 'ONE WAY' in s: return 'One way'
    if 'PET' in s: return 'PET'
    if 'LITRO' in s or s in {'1 L', '1L'}: return 'Litro'
    return s


def marca(v):
    s = norm(v)
    if not s: return ''
    # Consolidaciones de presentaciones, sin agregar dos productos al mismo registro.
    if s.endswith('.0') and s[:-2].isdigit(): s = s[:-2]
    if s.startswith('0.0%'):
        if 'QUILMES' in s: return 'QUILMES 0.0'
        if 'BRAHMA' in s: return 'BRAHMA 0.0'
        if 'STELLA' in s: return 'STELLA ARTOIS 0.0'
        if 'CORONA' in s: return 'CORONA 0.0'
        if 'HEINEKEN' in s: return 'HEINEKEN 0.0'
        return ''
    if 'VALUE LATA ' in s: return ''
    if 'TOTAL MARCAS' in s or 'TOTAL CALIBRES' in s or s == 'TC' or ' + ' in s: return ''
    names = ['QUILMES', 'BRAHMA', 'STELLA ARTOIS', 'CORONA', 'PATAGONIA',
             'BUDWEISER', 'ANDES ORIGEN', 'ANDES REGIONAL', 'IMPERIAL',
             'HEINEKEN', 'SCHNEIDER', 'AMSTEL', 'MILLER', 'MICHELOB',
             '1890', 'BAJO CERO', 'PALERMO', 'SALTA', 'NORTE', 'SANTA FE',
             'BEAGLE', 'ZEUS', 'CAPE HORN', 'DORADA', 'GROLSH', 'GROLSCH',
             'IGUANA', 'ISENBECK', '361', 'LA FELIZ', 'PACIFICO', 'NORTADA',
             'ANDOQUE', 'BUCKLER', 'COSTENA', 'AGUILA', 'WELLS GOLD']
    for b in names:
        if s == b or s.startswith(b + ' ') or s.startswith(b + '('):
            return 'GROLSCH' if b == 'GROLSH' else b
    if 'OTRAS ' in s or 'CONTRABANDO' in s or 'SIN SEGMENTO' in s: return ''
    return s


def _colnum(s):
    n = 0
    for c in s: n = n * 26 + (ord(c) - 64)
    return n - 1


def _sheet_xml(z, target_name='Base HL'):
    wb = ET.fromstring(z.read('xl/workbook.xml'))
    rel = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    targets = {r.get('Id'): r.get('Target') for r in rel.findall(PKG+'Relationship')}
    for sh in wb.find(NS+'sheets'):
        if norm(sh.get('name')) == norm(target_name):
            path = targets.get(sh.get(RELS+'id'), '')
            if path.startswith('/'): return path.lstrip('/')
            if path.startswith('xl/'): return path
            return 'xl/' + path
    raise ValueError(f'Falta la hoja {target_name} en el Excel.')


def _strings(z):
    try:
        with z.open('xl/sharedStrings.xml') as f: root = ET.parse(f).getroot()
    except KeyError: return []
    return [''.join(t.text or '' for t in si.iter(NS+'t')) for si in root.findall(NS+'si')]


def _read_rows(z, xml_name, strings):
    with z.open(xml_name) as file:
        for _, el in ET.iterparse(file, events=('end',)):
            if el.tag != NS+'row': continue
            values = {}
            for c in el.findall(NS+'c'):
                ref = c.get('r',''); match = re.match('[A-Z]+',ref)
                if match is None: continue
                typ = c.get('t','n'); v = c.find(NS+'v'); inline = c.find(NS+'is')
                if typ == 'inlineStr' and inline is not None:
                    value = ''.join(t.text or '' for t in inline.iter(NS+'t'))
                elif v is None: continue
                elif typ == 's':
                    try: value = strings[int(v.text)]
                    except (IndexError, ValueError, TypeError): value = ''
                elif typ in ('str','e','b'): value = v.text
                else:
                    try: value = float(v.text)
                    except (TypeError, ValueError): value = v.text
                values[_colnum(match.group())] = value
            yield int(el.get('r', '0')), values
            el.clear()


def parse_censo(file_bytes, periodo):
    """Devuelve (PDV, segmentos, presencias, auditoría).
    Los totales CMQ/CCU/OTROS provienen de las columnas VOL oficiales.
    Los segmentos provienen de los totales de segmento del template.
    Marca/calibre: SOLO indicador binario de presencia; los detalles pueden solaparse.
    """
    with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
        strs = _strings(z)
        it = _read_rows(z, _sheet_xml(z), strs)
        hdr = {}
        registros = []
        segmentos = []
        presencias = []
        errores = []
        cols_ready = False
        for row_number, vec in it:
            if row_number <= 9:
                hdr[row_number] = vec
                continue
            if not cols_ready:
                h = hdr.get(9,{})
                vol_cols = {norm(v): i for i,v in h.items() if norm(v).startswith('VOL ') or norm(v)=='SOM'}
                needs = ['VOL CMQ.', 'VOL CCU.', 'VOL OTROS']
                if not all(k in vol_cols for k in needs):
                    raise ValueError(f'No se identificaron las columnas de volumen oficiales para {periodo}.')
                first_seg = min((i for i,v in h.items() if re.match(r'^(CMQ|CCU|OTROS) (VALUE|CORE|PREMIUM|SUPER PREMIUM)',norm(v))), default=vol_cols['VOL CMQ.'])
                seg_cols = {}
                for i,v in h.items():
                    m = re.match(r'^(CMQ|CCU|OTROS)\s+(VALUE|CORE PLUS|CORE|PREMIUM|SUPER PREMIUM)$', norm(v))
                    if m and i < vol_cols['VOL CMQ.']: seg_cols[(m.group(1),m.group(2))]=i
                question_cols = []
                last_cal = ''
                for i,owner in sorted(hdr.get(4,{}).items()):
                    own = norm(owner)
                    if own not in OWNERS or i < 16 or i >= first_seg: continue
                    brand = marca(hdr.get(5,{}).get(i))
                    if not brand: continue
                    raw_cal = hdr.get(7,{}).get(i)
                    if raw_cal not in (None, '', 0):
                        last_cal = raw_cal
                    cal = calibre(raw_cal or last_cal)
                    # La pestaña Septiembre usa celdas de calibre combinadas: propagar
                    # el encabezado válido hacia todas las preguntas del mismo bloque.
                    if not cal:
                        descr = norm(hdr.get(9,{}).get(i))
                        cal = calibre(descr.split('-', 1)[-1]) if '-' in descr else ''
                    seg = norm(hdr.get(6,{}).get(i))
                    if seg not in SEGS: seg = 'SIN CLASIFICAR'
                    question_cols.append((i,own,brand,cal,seg))
                cols_ready = True
            raw_id = vec.get(6)
            if raw_id is None: continue
            pid = clean_id(raw_id)
            if not pid or not pid.isdigit(): continue
            vol = {owner: numeric(vec.get(vol_cols['VOL '+owner+'.' if owner != 'OTROS' else 'VOL OTROS'])) for owner in OWNERS}
            mercado = sum(vol.values())
            is_censable = norm(vec.get(13)) in {'SI','SÍ'} if periodo == 'Septiembre' else True
            rec = {'Periodo': periodo, 'PDV': pid, 'Supervisor': staff(vec.get(9),'supervisor'),
                   'Promotor': staff(vec.get(10),'promotor'), 'Canal': canal(vec.get(11)),
                   'Subcanal': subcanal(vec.get(12)), 'Censable': is_censable,
                   'Estado censo': norm(vec.get(13)) if periodo=='Septiembre' else 'SI',
                   'Motivo no censo': norm(vec.get(14)) if periodo=='Septiembre' else norm(vec.get(13)),
                   'HL CMQ': vol['CMQ'], 'HL CCU': vol['CCU'], 'HL OTROS': vol['OTROS'],
                   'HL Mercado': mercado, 'SOM CMQ': 100*vol['CMQ']/mercado if mercado > 0 else None,
                   'Fila origen': row_number}
            registros.append(rec)
            for (owner,segment), ix in seg_cols.items():
                value = numeric(vec.get(ix))
                if value > 0:
                    segmentos.append({'Periodo':periodo,'PDV':pid,'Empresa':owner,'Segmento':segment,'HL':value})
            # La presencia se basa solo en >0 en la pregunta, no en su suma (hay preguntas agregadas).
            found = set()
            for ix, owner, brand, cal, seg in question_cols:
                if numeric(vec.get(ix)) > 0:
                    found.add((owner,brand,cal,seg))
            for owner,brand,cal,seg in found:
                presencias.append({'Periodo':periodo,'PDV':pid,'Empresa':owner,'Marca':brand,
                                   'Calibre':cal or 'SIN DATO','Segmento':seg})
            if any(x < 0 for x in vol.values()): errores.append((pid,'HL negativos'))
        if not registros: raise ValueError(f'No se encontraron PDV en el archivo de {periodo}.')
        df = pd.DataFrame(registros)
        seg_df = pd.DataFrame(segmentos,columns=['Periodo','PDV','Empresa','Segmento','HL'])
        pres_df = pd.DataFrame(presencias,columns=['Periodo','PDV','Empresa','Marca','Calibre','Segmento']).drop_duplicates()
        # El detalle por segmento no siempre reconcilia completamente con el total (en abril hay residual).
        for owner in OWNERS:
            ref = f'HL {owner}'
            subtotal = seg_df[seg_df.Empresa==owner].groupby('PDV')['HL'].sum() if not seg_df.empty else pd.Series(dtype=float)
            residual = df.set_index('PDV')[ref].sub(subtotal,fill_value=0)
            for pid,delta in residual.items():
                if abs(delta)>0.001:
                    errores.append((pid,f'Diferencia por segmentos {owner}: {delta:.3f} HL'))
                    # Solo residuales positivos pueden tener categoría sin clasificar;
                    # negativos se dejan como discrepancias de auditoría, no duplicar.
                    if delta > 0:
                        segmentos.append({'Periodo': periodo,'PDV':pid,'Empresa':owner,'Segmento':'SIN CLASIFICAR','HL':delta})
        seg_df = pd.DataFrame(segmentos,columns=['Periodo','PDV','Empresa','Segmento','HL'])
        return df, seg_df, pres_df, pd.DataFrame(errores,columns=['PDV','Alerta']).assign(Periodo=periodo)


def indicadores(df):
    total = float(df['HL Mercado'].sum()) if len(df) else 0
    cmq = float(df['HL CMQ'].sum()) if len(df) else 0
    beer = df[df['HL Mercado']>0]
    con_cmq = df[df['HL CMQ']>0]
    return {'PDV': int(df.PDV.nunique()), 'PDV cerveza':int(beer.PDV.nunique()),
            'PDV CMQ':int(con_cmq.PDV.nunique()), 'HL mercado':total,'HL CMQ':cmq,
            'HL CCU':float(df['HL CCU'].sum()), 'HL OTROS':float(df['HL OTROS'].sum()),
            'SOM':100*cmq/total if total>0 else 0,
            'DF':100*con_cmq.PDV.nunique()/beer.PDV.nunique() if len(beer)>0 else 0,
            'DP':100*con_cmq['HL Mercado'].sum()/total if total>0 else 0,
            'DF universo':100*con_cmq.PDV.nunique()/df.PDV.nunique() if len(df)>0 else 0,
            'No censables':int((~df.Censable).sum()),
            'No censables con HL':int((~df.Censable & (df['HL Mercado']>0)).sum())}


def tabla_grupos(dfa,dfb,field):
    values = sorted(set(dfa[field])|set(dfb[field]))
    rows = []
    for key in values:
        a = indicadores(dfa[dfa[field]==key]); b = indicadores(dfb[dfb[field]==key])
        rows.append({'Grupo':key,'PDV Abr':a['PDV'],'PDV Sep':b['PDV'],
                     'HL Abr':a['HL mercado'],'HL Sep':b['HL mercado'],
                     'SOM Abr':a['SOM'] if a['HL mercado']>0 else None,
                     'SOM Sep':b['SOM'] if b['HL mercado']>0 else None,
                     'Δ pp':b['SOM']-a['SOM'] if a['HL mercado']>0 and b['HL mercado']>0 else None,
                     'DF Abr':a['DF'] if a['PDV cerveza'] else None,
                     'DF Sep':b['DF'] if b['PDV cerveza'] else None,
                     'DP Abr':a['DP'] if a['HL mercado']>0 else None,
                     'DP Sep':b['DP'] if b['HL mercado']>0 else None})
    return pd.DataFrame(rows)


def segment_summary(dfa,dfb,segments):
    rows = []
    for seg in SEGS:
        sa = segments[(segments.Periodo=='Abril') & (segments.PDV.isin(dfa.PDV)) & (segments.Segmento==seg)]
        sb = segments[(segments.Periodo=='Septiembre') & (segments.PDV.isin(dfb.PDV)) & (segments.Segmento==seg)]
        av = sa.groupby('Empresa').HL.sum().to_dict(); bv = sb.groupby('Empresa').HL.sum().to_dict()
        ta = sum(av.values()); tb = sum(bv.values())
        xa=100*av.get('CMQ',0)/ta if ta>0 else None
        xb=100*bv.get('CMQ',0)/tb if tb>0 else None
        rows.append({'Segmento':seg,'Abr CMQ HL':av.get('CMQ',0),'Abr CCU HL':av.get('CCU',0),
                     'Abr Otros HL':av.get('OTROS',0),'Abr Mercado HL':ta,'SOM Abr':xa,
                     'Sep CMQ HL':bv.get('CMQ',0),'Sep CCU HL':bv.get('CCU',0),
                     'Sep Otros HL':bv.get('OTROS',0),'Sep Mercado HL':tb,'SOM Sep':xb,
                     'Δ pp':xb-xa if xa is not None and xb is not None else None,
                     'Peso Abr':100*ta/dfa['HL Mercado'].sum() if dfa['HL Mercado'].sum()>0 else 0,
                     'Peso Sep':100*tb/dfb['HL Mercado'].sum() if dfb['HL Mercado'].sum()>0 else 0})
    return pd.DataFrame(rows)


def segment_distribution(df, segments, period):
    s=segments[(segments.Periodo==period) & (segments.PDV.isin(df.PDV))]
    rows=[]
    for seg in SEGS:
        g=s[s.Segmento==seg]
        market=g.groupby('PDV').HL.sum()
        cmq=g[g.Empresa=='CMQ'].groupby('PDV').HL.sum()
        active=market[market>0]
        in_cmq=cmq[cmq>0].index
        n=active.index.intersection(in_cmq).size
        denom=active.index.size
        p_market=float(active.sum())
        w=float(active.reindex(in_cmq).fillna(0).sum())
        rows.append({'Segmento':seg,'PDV segmento':denom,'PDV CMQ':n,
                     'DF':100*n/denom if denom else None,'DP':100*w/p_market if p_market else None,
                     'HL segmento':p_market})
    return pd.DataFrame(rows)


def presence_distribution(df,presence, period, dimension='Marca',company='CMQ'):
    p=presence[(presence.Periodo==period)&(presence.PDV.isin(df.PDV))]
    if company!='TODAS': p=p[p.Empresa==company]
    if dimension=='Calibre': p=p[p.Calibre!='SIN DATO']
    if p.empty: return pd.DataFrame(columns=[dimension,'PDV con presencia','DF universo','DP mercado'])
    by_pdv=df.set_index('PDV')['HL Mercado']
    pdv_n=df.PDV.nunique(); market=float(df['HL Mercado'].sum())
    rows=[]
    for group,values in p.groupby(dimension):
        ids=set(values.PDV)
        rows.append({dimension:group,'PDV con presencia':len(ids),
                     'DF universo':100*len(ids)/pdv_n if pdv_n else None,
                     'DP mercado':100*by_pdv.reindex(list(ids)).fillna(0).sum()/market if market else None})
    return pd.DataFrame(rows).sort_values('PDV con presencia',ascending=False)


def priorities(df, previous, min_hl=1.0, som_below=60.0):
    out=df[(df['HL Mercado']>=min_hl)&(df['SOM CMQ'].fillna(100)<som_below)].copy()
    out['HL competencia']=out['HL CCU']+out['HL OTROS']
    bef=previous[['PDV','SOM CMQ']].rename(columns={'SOM CMQ':'SOM abril'})
    out=out.merge(bef,on='PDV',how='left')
    out['Δ pp cliente']=out['SOM CMQ']-out['SOM abril']
    return out.sort_values('HL competencia',ascending=False).reset_index(drop=True)


def pdv_changes(dfa,dfb):
    af=dfa[['PDV','Supervisor','Promotor','Canal','Subcanal','SOM CMQ','HL Mercado','HL CMQ']].rename(
        columns={'SOM CMQ':'SOM Abr','HL Mercado':'HL Abr','HL CMQ':'CMQ Abr',
                 'Supervisor':'Supervisor Abr','Promotor':'Promotor Abr',
                 'Canal':'Canal Abr','Subcanal':'Subcanal Abr'})
    bf=dfb[['PDV','Supervisor','Promotor','Canal','Subcanal','SOM CMQ','HL Mercado','HL CMQ','HL CCU','HL OTROS']].rename(
        columns={'SOM CMQ':'SOM Sep','HL Mercado':'HL Sep','HL CMQ':'CMQ Sep'})
    combined=bf.merge(af,on='PDV',how='outer',indicator=True)
    combined['Estado']=combined['_merge'].map({'both':'Ambos','left_only':'Solo septiembre','right_only':'Solo abril'}).astype(str)
    combined['Δ pp']=combined['SOM Sep']-combined['SOM Abr']
    combined.drop(columns='_merge',inplace=True)
    return combined
