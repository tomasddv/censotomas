"""Dashboard Censo DDV | Abril / Septiembre 2026
Ejecutar: streamlit run app.py
Fuente: archivos oficiales Template Consolidado Resultados, pestaña Base HL.
"""
from pathlib import Path
from io import BytesIO
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from censo_engine import (
    parse_censo, indicadores, tabla_grupos, segment_summary, segment_distribution,
    presence_distribution, priorities, pdv_changes, SEGS, OWNERS,
)

st.set_page_config(page_title='Censo DDV · Inteligencia Comercial', page_icon='🍺', layout='wide', initial_sidebar_state='expanded')

st.markdown('''
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
html, body, [class*="css"], [data-testid="stAppViewContainer"] { font-family:'DM Sans',sans-serif; }
.stApp {
    color: #000000 !important;
}
[data-testid="stAppViewContainer"] {background:#f5f8f6;}
[data-testid="stSidebar"] {background:#eaf3ee; border-right:1px solid #d5e4da;}
.block-container {padding-top:1.7rem;max-width:1500px;}
h1,h2,h3 {font-family:'Space Grotesk',sans-serif!important;letter-spacing:-.025em;}
h1 {font-weight:700!important;}
[data-testid="stMetric"] {background:white;border:1px solid #dfeae3;padding:17px 19px;border-radius:16px;box-shadow:0 4px 19px rgba(15,75,44,.035);}
[data-testid="stMetricLabel"] {font-weight:650!important;color:#557467!important;}
[data-testid="stMetricValue"] {font-family:'Space Grotesk',sans-serif;font-size:1.75rem!important;color:#11482f;}
[data-testid="stMetricDelta"] {font-size:.85rem;}
[data-testid="stDataFrame"], [data-testid="stPlotlyChart"] {background:#fff;border:1px solid #e1eae4;border-radius:14px;padding:6px;}
.hero {background:linear-gradient(120deg,#063e2a,#08734a 75%,#15aa6b);color:white;padding:29px 33px;border-radius:18px;margin-bottom:22px;box-shadow:0 10px 28px rgba(2,72,40,.15);}
.hero .eyebrow {font-size:11px;font-weight:800;letter-spacing:.16em;opacity:.8;}
.hero h1 {font-size:29px;line-height:1.15;color:#fff!important;margin:8px 0 5px;}
.hero p {color:#d7f7e5!important;margin:0;font-size:13px;}
.info {background:#e8f5ec;border-left:4px solid #168c58;padding:12px 18px;border-radius:7px;font-size:13px;color:#1b5939;margin:14px 0;}
.mini {color:#597566;font-size:12px;line-height:1.5;}
section[data-testid="stSidebar"] h2 {color:#094f34!important;}
[data-testid="stHorizontalBlock"] {gap:0.7rem;}
</style>
''', unsafe_allow_html=True)

GREEN='#0b8451'; MINT='#53c79a'; NAVY='#173a35'; ORANGE='#e09b46'; RED='#cd5360'
CMP = {'CMQ':GREEN,'CCU':ORANGE,'OTROS':'#7186a1'}
PERIOD = {'Abril':'ABR-26','Septiembre':'SEP-26'}
ROOT=Path(__file__).resolve().parent


def number(x,d=1):
    if x is None or pd.isna(x): return '—'
    return f'{x:,.{d}f}'.replace(',','X').replace('.',',').replace('X','.')

def perc(x,d=1):return f'{number(x,d)}%' if x is not None and not pd.isna(x) else '—'

def pp(x): return f'{x:+.2f} pp'.replace('.',',') if x is not None and not pd.isna(x) else '—'

def figure(fig,height=380):
    fig.update_layout(height=height,paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='DM Sans',color=NAVY,size=12),margin=dict(l=18,r=16,t=36,b=27),
        legend=dict(orientation='h',y=1.14,x=0),xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor='#e8efeb',zeroline=False))
    return fig


def draw(df,kind='group',height=400):
    if df is None or df.empty:st.info('No hay datos con los filtros seleccionados.');return
    if kind=='market':
        fig=px.bar(df,x='Empresa',y='SOM',color='Periodo',barmode='group',text='SOM',
            color_discrete_map={'Abril':GREEN,'Septiembre':MINT},labels={'SOM':'Share de mercado (%)'})
        fig.update_traces(texttemplate='%{text:.1f}%',textposition='outside')
        fig.update_yaxes(range=[0,max(10,float(df.SOM.max())*1.22)])
    elif kind=='segment':
        fig=px.bar(df,x='Segmento',y='SOM',color='Periodo',barmode='group',text='SOM',
             color_discrete_map={'Abril':GREEN,'Septiembre':MINT},labels={'SOM':'SOM del segmento (%)'})
        fig.update_traces(texttemplate='%{text:.1f}%',textposition='outside')
    elif kind=='mix':
        fig=px.bar(df,x='Segmento',y='Peso',color='Periodo',barmode='group',text='Peso',
             color_discrete_map={'Abril':GREEN,'Septiembre':MINT},labels={'Peso':'Peso en mercado (%)'})
        fig.update_traces(texttemplate='%{text:.1f}%',textposition='outside')
    elif kind=='changes':
        d=df.sort_values('Δ pp',ascending=True).dropna(subset=['Δ pp'])
        fig=px.bar(d,x='Δ pp',y='Grupo',orientation='h',color='Δ pp',
              color_continuous_scale=['#d36062','#e5e8d7','#0e925a'],color_continuous_midpoint=0,
              labels={'Δ pp':'Variación de SOM (pp)'})
        fig.update_layout(showlegend=False,coloraxis_showscale=False)
    else:
        fig=px.bar(df,x=df.columns[0],y=df.columns[1],color_discrete_sequence=[GREEN])
    st.plotly_chart(figure(fig,height),use_container_width=True)


@st.cache_data(show_spinner=False,max_entries=4)
def load_both(ab,sp):
    april=parse_censo(ab,'Abril'); september=parse_censo(sp,'Septiembre')
    return (pd.concat([april[0],september[0]],ignore_index=True),
            pd.concat([april[1],september[1]],ignore_index=True),
            pd.concat([april[2],september[2]],ignore_index=True),
            pd.concat([april[3],september[3]],ignore_index=True))


def get_files():
    candidates = {
        'Abril':[ROOT/'data'/'abril_2026.xlsx',ROOT/'Template Consolidado Resultados Abril 2026(2).xlsx',ROOT/'Template Consolidado Resultados Abril 2026.xlsx'],
        'Septiembre':[ROOT/'data'/'septiembre_2026.xlsx',ROOT/'Template Consolidado Resultados Septiembre 2026.xlsx']
    }
    return {k:next((f for f in files if f.exists()),None) for k,files in candidates.items()}


st.sidebar.markdown('## 🍺 CENSO DDV')
st.sidebar.caption('INTELIGENCIA COMERCIAL · 2026')
files=get_files()
with st.sidebar.expander('📁 Archivos de origen',expanded=False):
    up_apr=st.file_uploader('Abril 2026',type='xlsx',key='apr')
    up_sep=st.file_uploader('Septiembre 2026',type='xlsx',key='sep')
    for label,source,up in [('Abril',files['Abril'],up_apr),('Septiembre',files['Septiembre'],up_sep)]:
        st.caption(f'{label}: '+ ('Archivo cargado' if up else (source.name if source else 'PENDIENTE')))
try:
    a_bytes=up_apr.getvalue() if up_apr else (files['Abril'].read_bytes() if files['Abril'] else None)
    s_bytes=up_sep.getvalue() if up_sep else (files['Septiembre'].read_bytes() if files['Septiembre'] else None)
    if a_bytes is None or s_bytes is None:
        st.error('Se necesitan los dos censos. Adjuntalos en el panel lateral o copialos a la carpeta data/.');st.stop()
    with st.spinner('Procesando censos oficiales y controlando volúmenes…'):
        raw,all_seg,all_pres,all_errors=load_both(a_bytes,s_bytes)
except Exception as exc:
    st.error('No se pudieron cargar los templates. Revisá que ambos tengan la pestaña «Base HL».')
    st.exception(exc);st.stop()

original_a=raw[raw.Periodo=='Abril']; original_b=raw[raw.Periodo=='Septiembre']
original_common=set(original_a.PDV)&set(original_b.PDV)

st.sidebar.markdown('### Filtros generales')
universe=st.sidebar.selectbox('Universo a comparar',['Universo completo','Mismos PDV en ambos censos','Solo censables (auditoría)'],
    help='Mismos PDV: intersección por Código PDV; recomendable para comparar resultados. Solo censables: ambos períodos aplican su bandera respectiva.')
base=raw.copy()
if universe=='Mismos PDV en ambos censos':base=base[base.PDV.isin(original_common)]
elif universe=='Solo censables (auditoría)':base=base[base.Censable]
filters={}
for field in ['Supervisor','Promotor','Canal','Subcanal']:
    opts=sorted(base[field].dropna().unique().tolist())
    selected=st.sidebar.multiselect(field,opts,placeholder='Todos',key=f'flt_{field}')
    filters[field]=selected
    if selected:base=base[base[field].isin(selected)]
# En modo homogéneo, mantener solamente los PDV que sobreviven a los filtros
# en ambos períodos; así no reaparecen cambios artificiales del universo.
if universe=='Mismos PDV en ambos censos':
    fa=set(base.loc[base.Periodo=='Abril','PDV'])
    fb=set(base.loc[base.Periodo=='Septiembre','PDV'])
    base=base[base.PDV.isin(fa & fb)]

a=base[base.Periodo=='Abril'];b=base[base.Periodo=='Septiembre']
if a.empty and b.empty:st.warning('Los filtros dejaron ambos períodos sin registros.');st.stop()
ma=indicadores(a);mb=indicadores(b)

st.sidebar.divider()
sections=[
'📊 Resumen ejecutivo','🍺 Share of Market','🏷️ Share of Segment',
'📍 Distribución física','⚖️ Distribución ponderada','🔎 Marcas y calibres',
'👥 Equipo, canales y subcanales','🎯 Oportunidades y 80/20',
'🏪 Clientes y evolución','🚀 Objetivos y PDA','🛡️ Auditoría de datos','⬇️ Descargar reportes'
]
page=st.sidebar.radio('Análisis',sections,label_visibility='collapsed')
st.sidebar.caption('Fuente: volumen censado (HL), no venta facturada. Los filtros siempre recalculan los denominadores.')

st.markdown('''<div class="hero"><div class="eyebrow">DISTRIBUIDORA DEL VALLE · PROCESOS DE VENTA</div>
<h1>Censo de mercado | Tablero de resultados</h1>
<p>ABRIL vs. SEPTIEMBRE 2026 · Share of Market · Distribución · Oportunidades · Planes de acción</p></div>''',unsafe_allow_html=True)

if universe!='Mismos PDV en ambos censos':
    st.caption('Universo activo: '+universe+' · Abril '+str(ma['PDV'])+' PDV · Septiembre '+str(mb['PDV'])+' PDV · '+str(len(original_common))+' clientes coinciden en la base original.')
else:st.caption('Comparación homogénea por Código PDV · Abril '+str(ma['PDV'])+' · Septiembre '+str(mb['PDV']))


def metrics_block(xa,xb):
    c1,c2,c3,c4,c5=st.columns(5)
    c1.metric('SOM CMQ · Abril',perc(xa['SOM'],2))
    c2.metric('SOM CMQ · Septiembre',perc(xb['SOM'],2),pp(xb['SOM']-xa['SOM']),delta_color='normal')
    c3.metric('HL mercado · Sep',number(xb['HL mercado'],1), f"{number(xb['HL mercado']-xa['HL mercado'],1)} HL",delta_color='off')
    c4.metric('PDV con cerveza · Sep',number(xb['PDV cerveza'],0))
    c5.metric('DF CMQ · Sep',perc(xb['DF'],2),pp(xb['DF']-xa['DF']))


def market_table():
    # Plotly necesita un valor de período por fila; d['Periodo'] es una Serie.
    rows = []
    for periodo, df_periodo in [('Abril', a), ('Septiembre', b)]:
        total_mercado = float(df_periodo['HL Mercado'].sum())
        for fabricante in OWNERS:
            hl = float(df_periodo[f'HL {fabricante}'].sum())
            rows.append({
                'Periodo': periodo,
                'Empresa': fabricante,
                'SOM': 100 * hl / total_mercado if total_mercado > 0 else 0.0,
                'HL': hl,
            })
    return pd.DataFrame(rows, columns=['Periodo', 'Empresa', 'SOM', 'HL'])


def comparison_summary():
    return pd.DataFrame([{'Métrica':k,'Abril':ma[k],'Septiembre':mb[k],
             'Δ':mb[k]-ma[k]} for k in ['PDV','PDV cerveza','PDV CMQ','HL mercado','HL CMQ','HL CCU','HL OTROS','SOM','DF','DP','DF universo']])


def filtered_segments():
    return all_seg[(all_seg.PDV.isin(base.PDV))].copy()


def filtered_pres():
    return all_pres[(all_pres.PDV.isin(base.PDV))].copy()


def grouped_presence(dim,owner):
    pres=filtered_pres()
    ap=presence_distribution(a,pres,'Abril',dim,owner)
    bp=presence_distribution(b,pres,'Septiembre',dim,owner)
    left=ap.rename(columns={'PDV con presencia':'PDV Abr','DF universo':'DF Abr','DP mercado':'DP Abr'})
    right=bp.rename(columns={'PDV con presencia':'PDV Sep','DF universo':'DF Sep','DP mercado':'DP Sep'})
    co=left.merge(right,on=dim,how='outer')
    if co.empty:return co
    co['Δ DF pp']=co['DF Sep']-co['DF Abr'];co['Δ DP pp']=co['DP Sep']-co['DP Abr']
    return co.sort_values('PDV Sep',ascending=False,na_position='last')


def two_segment_distributions():
    s=filtered_segments()
    sa=segment_distribution(a,s,'Abril').rename(columns={'PDV segmento':'PDV seg Abr','PDV CMQ':'PDV CMQ Abr', 'DF':'DF Abr','DP':'DP Abr','HL segmento':'HL Abr'})
    sb=segment_distribution(b,s,'Septiembre').rename(columns={'PDV segmento':'PDV seg Sep','PDV CMQ':'PDV CMQ Sep','DF':'DF Sep','DP':'DP Sep','HL segmento':'HL Sep'})
    result=sa.merge(sb,on='Segmento',how='outer')
    result['Δ DF pp']=result['DF Sep']-result['DF Abr'];result['Δ DP pp']=result['DP Sep']-result['DP Abr']
    return result


def show_table(df,key='',formats=None):
    if df.empty:st.info('No hay registros para esta apertura.');return
    disp=df.copy()
    fmt=formats or {}
    try:
        style=disp.style.format({col:spec for col,spec in fmt.items() if col in disp.columns},na_rep='—')
        st.dataframe(style,use_container_width=True,hide_index=True,height=min(600,95+len(disp)*35))
    except Exception:
        st.dataframe(disp,use_container_width=True,hide_index=True)


PCT='{:.2f}%'; NUM='{:,.2f}'; PP='{:+.2f} pp'; INT='{:,.0f}'

if page=='📊 Resumen ejecutivo':
    st.subheader('Visión general de la plaza')
    metrics_block(ma,mb)
    left,right=st.columns([1.1,1])
    with left:
        st.markdown('#### Participación por fabricante')
        draw(market_table(),'market')
    with right:
        st.markdown('#### Principales indicadores')
        res=comparison_summary()
        show_table(res,formats={'Abril':NUM,'Septiembre':NUM,'Δ':NUM})
    st.markdown('#### Evolución por segmento')
    segs=segment_summary(a,b,filtered_segments())
    sm=segs[segs.Segmento!='SIN CLASIFICAR']
    plot=pd.concat([sm[['Segmento','SOM Abr']].rename(columns={'SOM Abr':'SOM'}).assign(Periodo='Abril'),
                    sm[['Segmento','SOM Sep']].rename(columns={'SOM Sep':'SOM'}).assign(Periodo='Septiembre')])
    draw(plot,'segment')
    show_table(sm[['Segmento','SOM Abr','SOM Sep','Δ pp','Peso Abr','Peso Sep']],formats={'SOM Abr':PCT,'SOM Sep':PCT,'Δ pp':PP,'Peso Abr':PCT,'Peso Sep':PCT})
    st.info(f"Lectura comercial: SOM CMQ varía {pp(mb['SOM']-ma['SOM'])}. La comparación es de dos relevamientos del mismo año, no contra año anterior.")
    if universe!='Mismos PDV en ambos censos':
        ca=indicadores(original_a[original_a.PDV.isin(original_common)])
        cb=indicadores(original_b[original_b.PDV.isin(original_common)])
        st.markdown(f'<div class="info"><b>Control del universo:</b> entre los {len(original_common):,} clientes presentes en ambos censos, el SOM CMQ cambia {pp(cb["SOM"]-ca["SOM"])}. Usá «Mismos PDV en ambos censos» para trabajar sin altas ni bajas de muestra.</div>',unsafe_allow_html=True)

elif page=='🍺 Share of Market':
    st.subheader('Share of Market · total cerveza')
    st.caption('CMQ HL ÷ HL total de cerveza declarada. La comparación se pondera por volumen, no por cantidad de clientes.')
    metrics_block(ma,mb)
    mt=market_table();draw(mt,'market')
    res=mt.pivot(index='Empresa',columns='Periodo',values=['HL','SOM'])
    res.columns=[' '.join(c) for c in res.columns]
    res=res.reset_index()
    if 'SOM Septiembre' in res and 'SOM Abril' in res:res['Δ pp']=res['SOM Septiembre']-res['SOM Abril']
    show_table(res,formats={'HL Abril':NUM,'HL Septiembre':NUM,'SOM Abril':PCT,'SOM Septiembre':PCT,'Δ pp':PP})
    st.markdown('#### Share por apertura de negocio')
    field=st.selectbox('Desglosar por',['Canal','Subcanal','Supervisor','Promotor'])
    g=tabla_grupos(a,b,field)
    l,r=st.columns([1.1,1])
    with l:show_table(g,formats={'HL Abr':NUM,'HL Sep':NUM,'SOM Abr':PCT,'SOM Sep':PCT,'Δ pp':PP,'DF Abr':PCT,'DF Sep':PCT,'DP Abr':PCT,'DP Sep':PCT})
    with r:draw(g.dropna(subset=['Δ pp']).head(22),'changes',height=max(350,min(820,len(g)*34)))

elif page=='🏷️ Share of Segment':
    st.subheader('Share of Segment · peso y participación de cerveza')
    st.caption('Segmentos declarados por las columnas resumen del template: Value, Core, Core Plus, Premium y Super Premium.')
    segs=segment_summary(a,b,filtered_segments())
    st.markdown('#### SOM de CMQ dentro de cada segmento')
    core=segs[segs.Segmento!='SIN CLASIFICAR']
    bars=pd.concat([core[['Segmento','SOM Abr']].rename(columns={'SOM Abr':'SOM'}).assign(Periodo='Abril'),
                    core[['Segmento','SOM Sep']].rename(columns={'SOM Sep':'SOM'}).assign(Periodo='Septiembre')])
    draw(bars,'segment')
    show_table(segs,formats={k:(PCT if k in ['SOM Abr','SOM Sep','Peso Abr','Peso Sep'] else PP if k=='Δ pp' else NUM) for k in segs.columns if k!='Segmento'})
    st.markdown('#### Peso de cada segmento en el mercado total')
    weights=pd.concat([core[['Segmento','Peso Abr']].rename(columns={'Peso Abr':'Peso'}).assign(Periodo='Abril'),
                       core[['Segmento','Peso Sep']].rename(columns={'Peso Sep':'Peso'}).assign(Periodo='Septiembre')])
    draw(weights,'mix',height=340)
    st.warning('Cuando los totales por segmento no reconcilian con el total oficial, se muestra un residual «SIN CLASIFICAR». No se redistribuye artificialmente entre marcas o segmentos.')
    st.markdown('#### Abrir por supervisor, promotor o canal')
    group_by=st.selectbox('Dimensión',['Supervisor','Promotor','Canal','Subcanal'],key='groupseg')
    period=st.radio('Período',['Septiembre','Abril'],horizontal=True,key='segtime')
    ds=b if period=='Septiembre' else a
    seg=filtered_segments()
    seg=seg[(seg.Periodo==period)&seg.PDV.isin(ds.PDV)&(seg.Segmento!='SIN CLASIFICAR')]
    if not seg.empty:
        tg=seg.merge(ds[['PDV',group_by]],on='PDV',how='left')
        ag=tg.groupby([group_by,'Segmento','Empresa'],as_index=False).HL.sum()
        p=ag.pivot_table(index=[group_by,'Segmento'],columns='Empresa',values='HL',fill_value=0).reset_index()
        for comp in OWNERS:
            if comp not in p:p[comp]=0.
        p['Mercado HL']=p[OWNERS].sum(axis=1)
        p['SOM CMQ']=100*p['CMQ']/p['Mercado HL'].replace(0,np.nan)
        show_table(p.sort_values('Mercado HL',ascending=False),formats={'CMQ':NUM,'CCU':NUM,'OTROS':NUM,'Mercado HL':NUM,'SOM CMQ':PCT})

elif page=='📍 Distribución física':
    st.subheader('Distribución física · Presencia de CMQ')
    st.caption('DF total = PDV con HL CMQ > 0 / PDV con HL de cerveza > 0. Un punto de venta se cuenta una sola vez.')
    c1,c2,c3,c4=st.columns(4)
    c1.metric('DF total Abril',perc(ma['DF'],2))
    c2.metric('DF total Septiembre',perc(mb['DF'],2),pp(mb['DF']-ma['DF']))
    c3.metric('PDV CMQ Sep',number(mb['PDV CMQ'],0))
    c4.metric('DF sobre universo Sep',perc(mb['DF universo'],2))
    st.markdown('#### DF por segmento · entre PDV que venden cada segmento')
    segdist=two_segment_distributions()
    show_table(segdist[['Segmento','PDV seg Abr','PDV CMQ Abr','DF Abr','PDV seg Sep','PDV CMQ Sep','DF Sep','Δ DF pp']],
        formats={'DF Abr':PCT,'DF Sep':PCT,'Δ DF pp':PP})
    st.markdown('#### Distribución física por marca y calibre')
    dimension=st.radio('Agrupar por',['Marca','Calibre'],horizontal=True,key='df_dim')
    owner=st.selectbox('Fabricante',['CMQ','CCU','OTROS','TODAS'],key='df_own')
    table=grouped_presence(dimension,owner)
    show_table(table[[dimension,'PDV Abr','PDV Sep','DF Abr','DF Sep','Δ DF pp']] if not table.empty else table,
        formats={'DF Abr':PCT,'DF Sep':PCT,'Δ DF pp':PP})
    st.info('Para marcas y calibres, la distribución se calcula sobre todos los PDV relevados del universo seleccionado. Es un criterio distinto de la DF por segmento.')

elif page=='⚖️ Distribución ponderada':
    st.subheader('Distribución ponderada · Peso comercial de los PDV')
    st.caption('DP total = HL de mercado de los PDV con CMQ / HL total de mercado. No es lo mismo que Share of Market.')
    c1,c2,c3=st.columns(3)
    c1.metric('DP Abril',perc(ma['DP'],2))
    c2.metric('DP Septiembre',perc(mb['DP'],2),pp(mb['DP']-ma['DP']))
    c3.metric('HL mercado Sep',number(mb['HL mercado']))
    st.markdown('#### Distribución ponderada por segmento')
    sd=two_segment_distributions()
    show_table(sd[['Segmento','HL Abr','HL Sep','DP Abr','DP Sep','Δ DP pp']],
        formats={'HL Abr':NUM,'HL Sep':NUM,'DP Abr':PCT,'DP Sep':PCT,'Δ DP pp':PP})
    st.markdown('#### Peso de los PDV donde aparece la marca / calibre')
    dim=st.radio('Agrupar por',['Marca','Calibre'],horizontal=True,key='dp_dim')
    own=st.selectbox('Fabricante',['CMQ','CCU','OTROS','TODAS'],key='dp_own')
    table=grouped_presence(dim,own)
    show_table(table[[dim,'PDV Abr','PDV Sep','DP Abr','DP Sep','Δ DP pp']] if not table.empty else table,
        formats={'DP Abr':PCT,'DP Sep':PCT,'Δ DP pp':PP})
    st.info('La DP por marca/calibre usa como ponderador el volumen total del PDV. Por segmento, utiliza el volumen total del segmento en el PDV.')

elif page=='🔎 Marcas y calibres':
    st.subheader('Aperturas por marcas, segmentos y calibres')
    st.caption('Cobertura/penetración en clientes, no ventas de SKU. En los cuestionarios hay preguntas combinadas y totales superpuestos.')
    left,right,third=st.columns(3)
    with left: dim=st.selectbox('Vista',['Marca','Calibre','Segmento'])
    with right: owner=st.selectbox('Fabricante',['CMQ','CCU','OTROS','TODAS'],key='brand_owner')
    with third:metric=st.selectbox('Indicador',['PDV con presencia','Distribución física (%)','Distribución ponderada (%)'])
    if dim=='Segmento':
        sd=two_segment_distributions();st.dataframe(sd,use_container_width=True,hide_index=True)
    else:
        table=grouped_presence(dim,owner)
        if not table.empty:
            show_table(table,formats={'DF Abr':PCT,'DF Sep':PCT,'Δ DF pp':PP,'DP Abr':PCT,'DP Sep':PCT,'Δ DP pp':PP})
            pairs={'PDV con presencia':('PDV Abr','PDV Sep'),
                  'Distribución física (%)':('DF Abr','DF Sep'),
                  'Distribución ponderada (%)':('DP Abr','DP Sep')}
            ca,cb=pairs[metric]
            best=table.sort_values(cb,ascending=False).head(15)
            plotted=pd.concat([best[[dim,ca]].rename(columns={ca:'Resultado'}).assign(Periodo='Abril'),
                               best[[dim,cb]].rename(columns={cb:'Resultado'}).assign(Periodo='Septiembre')])
            fig=px.bar(plotted,x=dim,y='Resultado',color='Periodo',barmode='group',
                color_discrete_map={'Abril':GREEN,'Septiembre':MINT})
            fig.update_xaxes(tickangle=-35)
            st.plotly_chart(figure(fig,420),use_container_width=True)
    st.warning('No se calcula un SOM exacto por marca o calibre a partir de estas preguntas: algunos campos acumulan productos y se duplican entre presentaciones. Para ese indicador se necesita el detalle de volumen sin solapamientos.')

elif page=='👥 Equipo, canales y subcanales':
    st.subheader('Desempeño de supervisión y ejecución en la plaza')
    field=st.selectbox('Apertura',['Supervisor','Promotor','Canal','Subcanal'])
    rows=tabla_grupos(a,b,field)
    show_table(rows,formats={'HL Abr':NUM,'HL Sep':NUM,'SOM Abr':PCT,'SOM Sep':PCT,'Δ pp':PP,'DF Abr':PCT,'DF Sep':PCT,'DP Abr':PCT,'DP Sep':PCT})
    draw(rows.dropna(subset=['Δ pp']).head(24),'changes',height=max(350,min(950,len(rows)*33)))
    st.markdown('#### Ranking septiembre · HL competencia por grupo')
    if len(b):
        competition=b.groupby(field,as_index=False)[['HL CMQ','HL CCU','HL OTROS','HL Mercado']].sum()
        competition['HL competencia']=competition['HL CCU']+competition['HL OTROS']
        competition['SOM CMQ']=100*competition['HL CMQ']/competition['HL Mercado'].replace(0,np.nan)
        show_table(competition.sort_values('HL competencia',ascending=False),formats={'HL CMQ':NUM,'HL CCU':NUM,'HL OTROS':NUM,'HL Mercado':NUM,'HL competencia':NUM,'SOM CMQ':PCT})
    st.caption('Los supervisores pueden haber cambiado entre censos. El nombre se homologa, pero la cartera de clientes puede no ser la misma.')

elif page=='🎯 Oportunidades y 80/20':
    st.subheader('Clientes con oportunidad de recuperar volumen a la competencia')
    st.caption('Prioridad = HL de CCU + OTROS en el PDV, con SOM CMQ inferior al umbral. Es potencial de sustitución, no una venta garantizada.')
    c1,c2,c3=st.columns([1,1,2])
    with c1:limit=st.slider('SOM máximo de cliente (%)',10,95,60,5)
    with c2:min_hl=st.number_input('Mercado mínimo (HL)',min_value=0.,value=1.,step=0.5)
    pr=priorities(b,a,min_hl,limit)
    competitor=pr['HL competencia'].sum() if len(pr) else 0
    c1,c2,c3=st.columns(3)
    c1.metric('PDV candidatos',number(len(pr),0))
    c2.metric('HL competencia en candidatos',number(competitor,1))
    c3.metric('Promotores con candidatos',number(pr.Promotor.nunique() if len(pr) else 0,0))
    if not pr.empty:
        pr['HL acum.']=pr['HL competencia'].cumsum()
        pr['% oportunidad acumulada']=100*pr['HL acum.']/competitor if competitor>0 else 0
        n_80=int((pr['% oportunidad acumulada']<80).sum())+1 if competitor else 0
        st.markdown(f'<div class="info">El <b>80% del volumen competidor priorizado</b> se concentra en los primeros <b>{n_80} PDV</b> de {len(pr)} candidatos ({n_80/len(pr)*100:.0f}% de la cartera candidata).</div>',unsafe_allow_html=True)
        st.markdown('#### Ranking de clientes prioritarios · Septiembre')
        cols=['PDV','Supervisor','Promotor','Canal','Subcanal','HL Mercado','HL CMQ','HL CCU','HL OTROS','HL competencia','SOM abril','SOM CMQ','Δ pp cliente','% oportunidad acumulada']
        show_table(pr[cols],formats={'HL Mercado':NUM,'HL CMQ':NUM,'HL CCU':NUM,'HL OTROS':NUM,'HL competencia':NUM,'SOM abril':PCT,'SOM CMQ':PCT,'Δ pp cliente':PP,'% oportunidad acumulada':PCT})
        st.markdown('#### Concentración por promotor')
        team=pr.groupby('Promotor',as_index=False).agg(PDV=('PDV','nunique'),HL_competencia=('HL competencia','sum'))
        team=team.sort_values('HL_competencia',ascending=False)
        fig=px.bar(team,x='HL_competencia',y='Promotor',orientation='h',color_discrete_sequence=[GREEN],
            labels={'HL_competencia':'HL competencia potencial'})
        st.plotly_chart(figure(fig,max(350,len(team)*34)),use_container_width=True)
        st.download_button('⬇️ Descargar clientes candidatos (CSV)',pr.to_csv(index=False).encode('utf-8-sig'),
            file_name='oportunidades_censo_septiembre.csv',mime='text/csv')
    st.markdown('#### PDV con competidor pero sin CMQ en un segmento')
    s=filtered_segments();sp=s[(s.Periodo=='Septiembre')&(s.PDV.isin(b.PDV))]
    if not sp.empty:
        pivot=sp.pivot_table(index=['PDV','Segmento'],columns='Empresa',values='HL',aggfunc='sum',fill_value=0).reset_index()
        for company in OWNERS:
            if company not in pivot:pivot[company]=0.
        pivot['HL rival']=pivot['CCU']+pivot['OTROS']
        empty=pivot[(pivot.CMQ<=0)&(pivot['HL rival']>0)&(pivot.Segmento!='SIN CLASIFICAR')]
        if not empty.empty:
            empty=empty.merge(b[['PDV','Supervisor','Promotor','Canal','Subcanal']],on='PDV',how='left')
            st.metric('Oportunidades segmento sin CMQ',len(empty))
            show_table(empty.sort_values('HL rival',ascending=False),formats={'CMQ':NUM,'CCU':NUM,'OTROS':NUM,'HL rival':NUM})
        else:st.info('Sin PDV con esta condición en el universo seleccionado.')

elif page=='🏪 Clientes y evolución':
    st.subheader('Comparativo individual · todos los PDV')
    combined=pdv_changes(a,b)
    query=st.text_input('Buscar Código PDV o promotor',placeholder='Ejemplo: 2590 o GARCIA')
    if query:
        mask=combined['PDV'].astype(str).str.contains(query,case=False,regex=False)
        mask |= combined['Promotor'].fillna('').astype(str).str.contains(query,case=False,regex=False)
        combined=combined[mask]
    c1,c2,c3=st.columns(3)
    c1.metric('PDV coincidentes',int((combined.Estado=='Ambos').sum()))
    c2.metric('Solo abril',int((combined.Estado=='Solo abril').sum()))
    c3.metric('Solo septiembre',int((combined.Estado=='Solo septiembre').sum()))
    options=['Todos','Caída de SOM','Crecimiento de SOM','Solo abril','Solo septiembre']
    order=st.selectbox('Mostrar',options)
    if order=='Caída de SOM':combined=combined[combined['Δ pp']<0].sort_values('Δ pp')
    elif order=='Crecimiento de SOM':combined=combined[combined['Δ pp']>0].sort_values('Δ pp',ascending=False)
    elif order in ['Solo abril','Solo septiembre']:combined=combined[combined.Estado==order]
    show_table(combined,formats={'SOM Abr':PCT,'SOM Sep':PCT,'Δ pp':PP,'HL Abr':NUM,'HL Sep':NUM,'CMQ Abr':NUM,'CMQ Sep':NUM,'HL CCU':NUM,'HL OTROS':NUM})
    st.download_button('⬇️ Descargar detalle filtrado CSV',combined.to_csv(index=False).encode('utf-8-sig'),
        file_name='detalle_clientes_censo.csv',mime='text/csv')

elif page=='🚀 Objetivos y PDA':
    st.subheader('Simulador comercial · objetivo SOM y Plan de Acción')
    if mb['HL mercado']<=0:st.warning('El período actual no tiene mercado de cerveza declarado.');st.stop()
    default_target=min(100,max(0,round(mb['SOM']+2.0,1)))
    target=st.slider('Objetivo de SOM CMQ',0.0,100.0,default_target,0.5,
        help='Supone mercado fijo y conquista de hectolitros a competidores, sin aumentar el total del mercado.')
    additional=max(0,mb['HL mercado']*target/100-mb['HL CMQ'])
    competition=mb['HL CCU']+mb['HL OTROS']
    c1,c2,c3,c4=st.columns(4)
    c1.metric('SOM CMQ actual',perc(mb['SOM'],2))
    c2.metric('SOM objetivo',perc(target,1),pp(target-mb['SOM']))
    c3.metric('HL por conquistar',number(additional,2))
    c4.metric('% de HL rival a captar',perc(100*additional/competition if competition else 0,1))
    st.info('Modelo estático: los HL captados se restan a competencia y se suman a CMQ, manteniendo constante el mercado relevado. No representa un pronóstico de venta.')
    st.markdown('#### Plan de acción operativo · Editable')
    if 'pda_data' not in st.session_state:
        st.session_state.pda_data=pd.DataFrame([
            {'Foco':'Recuperación Core Plus','Supervisor':'','Promotor':'','PDV':'','Acción':'Revisar mix y negociar apertura','Meta HL':0.0,'Responsable':'','Fecha':'','Estado':'Pendiente'},
            {'Foco':'Recuperación Premium','Supervisor':'','Promotor':'','PDV':'','Acción':'Trabajar presencia por marca/calibre','Meta HL':0.0,'Responsable':'','Fecha':'','Estado':'Pendiente'},
            {'Foco':'PDV alto peso competencia','Supervisor':'','Promotor':'','PDV':'','Acción':'Visita y propuesta comercial','Meta HL':0.0,'Responsable':'','Fecha':'','Estado':'Pendiente'},
            {'Foco':'Calidad del censo','Supervisor':'','Promotor':'','PDV':'','Acción':'Validar PDV no censables con volumen','Meta HL':0.0,'Responsable':'','Fecha':'','Estado':'Pendiente'},
        ])
    st.session_state.pda_data=st.data_editor(st.session_state.pda_data,num_rows='dynamic',hide_index=True,use_container_width=True,
        column_config={'Meta HL':st.column_config.NumberColumn('Meta HL',min_value=0.0,format='%.2f'),
                       'Estado':st.column_config.SelectboxColumn('Estado',options=['Pendiente','En ejecución','Finalizado','Bloqueado'])})
    total_hl=st.session_state.pda_data['Meta HL'].fillna(0).sum()
    st.metric('HL planificados en acciones',number(total_hl,2))
    st.download_button('⬇️ Descargar PDA (CSV)',st.session_state.pda_data.to_csv(index=False).encode('utf-8-sig'),
        file_name='pda_censo_ddv.csv',mime='text/csv')
    st.caption('Las ediciones se conservan durante la sesión. Descargá el CSV antes de cerrar la página; para seguimiento compartido se requiere conectar almacenamiento.')

elif page=='🛡️ Auditoría de datos':
    st.subheader('Consistencia y calidad del censo')
    st.caption('Control de alcance, censabilidad, coincidencia entre plantillas y diferencias de segmentación.')
    c1,c2,c3,c4=st.columns(4)
    c1.metric('PDV Abril · base completa',int(len(original_a)))
    c2.metric('PDV Septiembre · base completa',int(len(original_b)))
    c3.metric('PDV coincidentes',len(original_common))
    c4.metric('No censables con HL · Septiembre',indicadores(original_b)['No censables con HL'])
    st.warning('Septiembre registra PDV no censables que igualmente declaran HL de cerveza. En filtros «Solo censables» se excluyen, pero eso cambia el universo y no debe compararse sin advertencia con abril.')
    st.markdown('#### Estado de censabilidad · septiembre')
    statuses=original_b.groupby(['Estado censo','Motivo no censo'],dropna=False,as_index=False).agg(
        PDV=('PDV','nunique'),HL_mercado=('HL Mercado','sum'))
    show_table(statuses.sort_values('PDV',ascending=False),formats={'HL_mercado':NUM})
    st.markdown('#### PDV marcados no censables con volumen')
    conflicted=original_b[(~original_b.Censable)&(original_b['HL Mercado']>0)]
    show_table(conflicted[['PDV','Supervisor','Promotor','Canal','Subcanal','Estado censo','Motivo no censo','HL Mercado','HL CMQ','HL CCU','HL OTROS']],
        formats={'HL Mercado':NUM,'HL CMQ':NUM,'HL CCU':NUM,'HL OTROS':NUM})
    st.markdown('#### Diferencias de conciliación en segmentos')
    if not all_errors.empty:
        seg_alerts=all_errors[all_errors.Alerta.str.contains('Diferencia por segmentos',na=False)]
        summary=seg_alerts.groupby(['Periodo','Alerta'],as_index=False).size()
        st.caption(f'{len(seg_alerts)} advertencias por PDV/empresa; algunas son redondeos, otras diferencias reales entre resumen y desglose.')
        st.dataframe(seg_alerts,use_container_width=True,hide_index=True,height=320)
    else:st.success('No se detectaron diferencias en la conciliación por segmento.')
    st.info('La app usa siempre las columnas oficiales VOL CMQ., VOL CCU. y VOL OTROS para el SOM total. Para segmentos usa los totales resumidos del Excel, y expone aparte las diferencias sin imputaciones encubiertas.')

elif page=='⬇️ Descargar reportes':
    st.subheader('Descargas consolidadas')
    st.caption('Los reportes se construyen con los filtros activos del panel lateral. La base original no se modifica.')
    segment=segment_summary(a,b,filtered_segments())
    teams=tabla_grupos(a,b,'Promotor')
    supervisors=tabla_grupos(a,b,'Supervisor')
    channels=tabla_grupos(a,b,'Canal')
    subchannels=tabla_grupos(a,b,'Subcanal')
    customers=pdv_changes(a,b)
    opps=priorities(b,a,1,60)
    pres=grouped_presence('Marca','CMQ')
    calibres=grouped_presence('Calibre','CMQ')
    dist=two_segment_distributions()
    selected_errors=all_errors[all_errors.PDV.isin(base.PDV)]
    tables={
        'Resumen':comparison_summary(),'SOM Fabricantes':market_table(),
        'Share Segmento':segment,'DF DP Segmento':dist,
        'Marcas CMQ':pres,'Calibres CMQ':calibres,
        'Supervisores':supervisors,'Promotores':teams,'Canales':channels,
        'Subcanales':subchannels,'Oportunidades':opps,
        'Clientes':customers,'Auditoria':selected_errors,
    }
    st.markdown(f'El archivo Excel reúne **{len(tables)} hojas** y los indicadores de los dos censos.')
    @st.cache_data(show_spinner=False)
    def generate_xlsx(sets):
        buffer=BytesIO()
        with pd.ExcelWriter(buffer,engine='xlsxwriter') as writer:
            for sheet,d in sets.items():
                name=sheet[:31]
                d.to_excel(writer,sheet_name=name,index=False)
                ws=writer.sheets[name]
                ws.freeze_panes(1,0)
                ws.autofilter(0,0,max(1,len(d)),max(0,len(d.columns)-1))
                ws.set_row(0,28)
                ws.set_column(0,min(24,max(0,len(d.columns)-1)),19)
                for col,hd in enumerate(d.columns):
                    if hd in ('Supervisor','Promotor','Subcanal','Grupo','Motivo no censo'):ws.set_column(col,col,27)
        return buffer.getvalue()
    if st.button('Preparar Excel del análisis',type='primary'):
        st.session_state['xls_ready']=True
    if st.session_state.get('xls_ready',False):
        try:
            xls=generate_xlsx(tables)
            st.download_button('⬇️ Descargar Excel completo',xls,file_name='Censo_DDV_Dashboard_Comparativo_2026.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',type='primary')
        except Exception as exc:st.error(f'Error generando Excel: {exc}')
    st.download_button('⬇️ Descargar PDV filtrados en CSV',base.to_csv(index=False).encode('utf-8-sig'),
         file_name='censo_ddv_pdv_filtrados.csv',mime='text/csv')
    st.caption('Fuente: Template Consolidado Resultados Abril 2026 + Septiembre 2026 (Base HL). No incluye AA porque no hay archivos 2025.')

st.divider()
st.caption('DDV · Censo de Mercado 2026 · HL de mercado declarados en relevamiento | Sin datos históricos inventados | Indicadores recalculados por filtros')
