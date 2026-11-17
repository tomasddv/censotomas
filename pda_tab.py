"""Tablero liviano de ejecución de los tres PDA de septiembre de 2026."""
from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from pda_candidates import PLANES, PLAN_IDS, load_candidates
from pda_storage import EDITABLE, ESTADOS, KEYS, clean_updates, make_storage, merge_with_base


def fmt(value, decimals=1):
    if value is None or pd.isna(value):
        return '—'
    return f'{value:,.{decimals}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def present(v):
    return v is not None and not pd.isna(v) and str(v).strip() != ''


def occurred(dates: pd.Series) -> pd.Series:
    """Una visita/validación futura no es ejecución ya lograda."""
    parsed = pd.to_datetime(dates, errors='coerce', format='%Y-%m-%d')
    today = datetime.now(ZoneInfo('America/Argentina/Buenos_Aires')).date()
    return parsed.notna() & parsed.le(pd.Timestamp(today))


def achieved(frame: pd.DataFrame) -> pd.Series:
    """Éxito del PDA, según la evidencia pedida en cada plan."""
    good = pd.Series(False, index=frame.index)
    core = frame['Plan ID'] == 'P1_CORE_PLUS'
    premium = frame['Plan ID'] == 'P2_PREMIUM'
    kiosks = frame['Plan ID'] == 'P3_KIOSCOS'
    good.loc[core] = (frame.loc[core, 'Presencia validada'].eq('Sí') &
                      occurred(frame.loc[core, 'Fecha verificación']))
    good.loc[premium] = (frame.loc[premium, 'Ola'].eq('Ola 1') &
                         occurred(frame.loc[premium, 'Fecha visita']))
    good.loc[kiosks] = (occurred(frame.loc[kiosks, 'Fecha medición']) &
                        frame.loc[kiosks, 'SOM posterior'].ge(60))
    return good


def summary(data: pd.DataFrame, goals: dict) -> list[dict]:
    result = []
    for plan_id in PLAN_IDS:
        rows = data[data['Plan ID'] == plan_id]
        done = int(achieved(rows).sum())
        meta = int(goals.get(plan_id, PLANES[plan_id]['Meta']))
        result.append({'Plan ID':plan_id,'Plan':PLANES[plan_id]['Nombre'],
                       'Meta':meta,'Logrado':done,'Avance':min(done/max(meta,1),1),
                       'PDV objetivo':len(rows),'Visitas':int(occurred(rows['Fecha visita']).sum()),
                       'Verificados':int((rows.Estado == 'Verificado').sum()),
                       'Pendientes':int((rows.Estado == 'Pendiente').sum()),
                       'HL mercado candidatos':float(rows['HL Mercado'].sum())})
    return result


def _as_export(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode('utf-8-sig')


def _goals_ui(storage, goals):
    with st.expander('Ajustar metas operativas (propuestas)', expanded=False):
        with st.form('goals_form'):
            g1,g2,g3 = st.columns(3)
            values = {
                'P1_CORE_PLUS':g1.number_input('PDV Core Plus a activar',1,62,int(goals['P1_CORE_PLUS'])),
                'P2_PREMIUM':g2.number_input('PDV Premium a visitar',1,100,int(goals['P2_PREMIUM'])),
                'P3_KIOSCOS':g3.number_input('Kioscos a recuperar',1,47,int(goals['P3_KIOSCOS'])),
            }
            if st.form_submit_button('Guardar metas'):
                storage.save_goals(values)
                st.success('Metas guardadas.')
                st.rerun()


def _filters(data):
    a,b,c,d=st.columns([1.3,1,1,1])
    with a:
        sel_plan=st.selectbox('Plan', ['Todos']+[f'{PLANES[k]["Nombre"]} ({k})' for k in PLAN_IDS])
    with b:
        sel_ola=st.selectbox('Ola', ['Todas','Ola 1','Ola 2'])
    with c:
        sel_sup=st.selectbox('Supervisor',['Todos']+sorted(data.Supervisor.unique().tolist()))
    with d:
        sel_state=st.selectbox('Estado',['Todos']+ESTADOS)
    a,b=st.columns([1,2])
    with a:
        sel_prom=st.selectbox('Promotor',['Todos']+sorted(data.Promotor.unique().tolist()))
    with b:
        query=st.text_input('Buscar PDV, responsable o subcanal',placeholder='Código PDV o nombre')
    out=data
    if sel_plan!='Todos':
        out=out[out['Plan ID']==sel_plan.rsplit('(',1)[-1].rstrip(')')]
    if sel_ola!='Todas':out=out[out.Ola==sel_ola]
    if sel_sup!='Todos':out=out[out.Supervisor==sel_sup]
    if sel_prom!='Todos':out=out[out.Promotor==sel_prom]
    if sel_state!='Todos':out=out[out.Estado==sel_state]
    if query:
        q=query.casefold()
        out=out[out[['PDV','Responsable','Subcanal']].fillna('').astype(str)
                .apply(lambda col:col.str.casefold().str.contains(q,regex=False)).any(axis=1)]
    return out


def _client_form(storage, filtered, allowed):
    st.markdown('#### Registrar una gestión')
    if filtered.empty:
        st.info('No hay clientes para los filtros seleccionados.')
        return
    options=list(range(len(filtered)))
    index=st.selectbox('Cliente y plan',options,format_func=lambda n:
        f'{filtered.iloc[n]["PDV"]}  ·  {filtered.iloc[n]["Plan"]}  ·  '
        f'{filtered.iloc[n]["Promotor"]}  ·  {filtered.iloc[n]["HL Mercado"]:.1f} HL')
    record=filtered.iloc[index]
    key=(record['Plan ID'],str(record.PDV))
    with st.form(f'edit_{key[0]}_{key[1]}'):
        c1,c2,c3=st.columns(3)
        with c1:
            state=st.selectbox('Estado de gestión',ESTADOS,index=ESTADOS.index(record.Estado))
            who=st.text_input('Responsable',value=str(record.Responsable))
            last=st.text_input('Fecha de visita',value=str(record['Fecha visita']),placeholder='AAAA-MM-DD')
        with c2:
            next_=st.text_input('Próxima gestión',value=str(record['Próxima gestión']),placeholder='AAAA-MM-DD')
            verified=st.selectbox('Presencia Core Plus validada', ['No','Sí'],
                                  index=0 if record['Presencia validada']!='Sí' else 1,
                                  help='Para el plan 1 requiere fecha de verificación para impactar en el KPI.')
            verified_date=st.text_input('Fecha de verificación',value=str(record['Fecha verificación']),placeholder='AAAA-MM-DD')
        with c3:
            posterior = '' if pd.isna(record['SOM posterior']) else fmt(record['SOM posterior'],2).replace(',','.')
            observed=st.text_input('SOM posterior medido (%)',value=posterior,
                help='Para kioscos, el KPI se actualiza con SOM ≥ 60% y fecha de medición.')
            measured=st.text_input('Fecha de medición',value=str(record['Fecha medición']),placeholder='AAAA-MM-DD')
            evidence=st.text_input('Link de evidencia',value=str(record.Evidencia),placeholder='Foto, pedido o acta')
        notes=st.text_area('Observaciones / próxima acción',value=str(record.Observaciones),height=90)
        submitted=st.form_submit_button('💾 Guardar gestión',type='primary')
    if submitted:
        try:
            som_value=None if not observed.strip() else float(observed.strip().replace(',','.'))
            update=pd.DataFrame([{
                'Plan ID':key[0],'PDV':key[1],'Estado':state,'Responsable':who,
                'Fecha visita':last,'Próxima gestión':next_,
                'Presencia validada':verified,'Fecha verificación':verified_date,
                'SOM posterior':som_value,'Fecha medición':measured,
                'Evidencia':evidence,'Observaciones':notes,
            }])
            clean=clean_updates(update,allowed)
            storage.save(clean)
            st.success(f'Gestión guardada para PDV {key[1]} ({record.Plan}).')
            st.rerun()
        except (ValueError,TypeError) as e:
            st.error(f'No se guardó la gestión: {e}')


def _overdue(data):
    due=pd.to_datetime(data['Próxima gestión'], errors='coerce')
    today=datetime.now(ZoneInfo('America/Argentina/Buenos_Aires')).date()
    return ((due.notna()) & (due < pd.Timestamp(today)) &
            ~data.Estado.isin(['Verificado','Descartado']))


def render(project_root: Path):
    st.subheader('Seguimiento de los tres planes · Septiembre 2026')
    st.caption('Base fija: resultados oficiales de DDV (70549). No se suman HL entre planes: '
               'un mismo PDV puede participar en más de una acción.')
    base=load_candidates(project_root)
    allowed=set(zip(base['Plan ID'].astype(str),base.PDV.astype(str)))
    try:
        storage=make_storage(project_root,st.secrets)
        effective=merge_with_base(base,storage.load())
        goals={k:int(storage.goals().get(k,PLANES[k]['Meta'])) for k in PLAN_IDS}
    except Exception as exc:
        st.error('No fue posible abrir el almacenamiento de seguimiento; las oportunidades base no se modificaron.')
        st.exception(exc)
        return

    if storage.mode=='SQLite local':
        st.info('Guardado automático en esta instalación. Si usás Streamlit Community Cloud, '
                'conectá Google Sheets en Secrets para persistencia entre reinicios; '
                'también podés descargar un respaldo CSV.')
    else:
        st.success('Seguimiento conectado a Google Sheets privado: los cambios se guardan entre sesiones.')

    stats=summary(effective,goals)
    k1,k2,k3=st.columns(3)
    for col,row in zip([k1,k2,k3],stats):
        with col:
            st.metric(row['Plan'],f"{row['Logrado']}/{row['Meta']}",
                      help=PLANES[row['Plan ID']]['Objetivo'])
            st.progress(row['Avance'])
            st.caption(f"{row['PDV objetivo']} PDV · {fmt(row['HL mercado candidatos'])} HL de mercado · "
                       f"fecha propuesta {PLANES[row['Plan ID']]['Fecha propuesta']}")
    c1,c2,c3,c4=st.columns(4)
    c1.metric('PDV únicos involucrados',effective.PDV.nunique())
    c2.metric('Asignaciones plan–PDV',len(effective))
    c3.metric('Gestiones vencidas',int(_overdue(effective).sum()))
    c4.metric('Visitas ejecutadas',int(occurred(effective['Fecha visita']).sum()))
    _goals_ui(storage,goals)

    summary_tab,actions_tab,report_tab=st.tabs(['Resumen y prioridades','Gestión por cliente','Supervisión y respaldos'])
    with summary_tab:
        st.markdown('#### Qué se busca lograr')
        table=pd.DataFrame([
            {'Plan':PLANES[k]['Nombre'],'Universo':f"{stats[i]['PDV objetivo']} PDV",
             'Objetivo':PLANES[k]['Objetivo'],
             'Fecha propuesta':PLANES[k]['Fecha propuesta']}
            for i,k in enumerate(PLAN_IDS)])
        st.dataframe(table,use_container_width=True,hide_index=True)
        st.markdown('#### Primera ola priorizada por hectolitros')
        for plan_id in PLAN_IDS:
            initial=effective[(effective['Plan ID']==plan_id)&(effective.Ola=='Ola 1')]
            st.caption(f'{PLANES[plan_id]["Nombre"]}: {len(initial)} PDV prioritarios, '
                       f'{fmt(initial["HL Mercado"].sum())} HL de mercado.')
        priority=effective[(effective.Ola=='Ola 1')&
                           ~effective.Estado.isin(['Verificado','Descartado'])]
        priority=priority.sort_values(['Plan ID','Orden']).head(30)
        st.dataframe(priority[['Plan','PDV','Supervisor','Promotor','HL Mercado',
                               'SOM CMQ','Prioridad','Estado','Próxima gestión']],
                     use_container_width=True,hide_index=True,height=430)
        st.caption('El orden prioriza puertas de alto peso. Es un listado de oportunidades, no una promesa de ventas.')

    with actions_tab:
        visible=_filters(effective)
        st.caption(f'{len(visible)} combinaciones plan–PDV visibles. '
                   'Seleccioná un registro, cargá avances y guardalos.')
        inspect_cols=['Plan','PDV','Supervisor','Promotor','HL Mercado','HL Rival',
                      'SOM CMQ','SOM segmento','Ola','Estado','Fecha visita','Próxima gestión']
        st.dataframe(visible[inspect_cols].sort_values('HL Mercado',ascending=False),
                     use_container_width=True,hide_index=True,height=330)
        _client_form(storage,visible,allowed)
        st.download_button('⬇️ Descargar selección (CSV)',_as_export(visible),
                           file_name='PDA_DDV_clientes_filtrados.csv',mime='text/csv')

    with report_tab:
        st.markdown('#### Cumplimiento por plan, supervisor y promotor')
        details=effective.copy()
        details['PDA logrado']=achieved(details).astype(int)
        group=details.groupby(['Plan','Supervisor','Promotor'],as_index=False).agg(
            Asignaciones=('PDV','size'),PDV_unicos=('PDV','nunique'),
            Pendientes=('Estado',lambda s:int((s=='Pendiente').sum())),
            Visitas=('Fecha visita',lambda s:int(occurred(s).sum())),
            Verificados=('Estado',lambda s:int((s=='Verificado').sum())),
            Logrados=('PDA logrado','sum'),
        )
        st.dataframe(group.sort_values(['Plan','Logrados','Asignaciones'],ascending=[True,False,False]),
                     use_container_width=True,hide_index=True)
        st.markdown('#### Respaldo y recuperación del seguimiento')
        st.download_button('⬇️ Descargar respaldo completo (CSV)',_as_export(effective),
            file_name='PDA_DDV_seguimiento_respaldo.csv',mime='text/csv',type='primary')
        upload=st.file_uploader('Restaurar gestiones desde un respaldo CSV',type=['csv'],key='restore_pda')
        if upload:
            try:
                data=pd.read_csv(BytesIO(upload.getvalue()),dtype={'PDV':str},keep_default_na=False)
                clean=clean_updates(data,allowed)
                st.warning(f'Se actualizarán las gestiones de {len(clean)} combinaciones plan–PDV '
                           'incluidas en el archivo. Los datos base del censo no cambiarán.')
                if st.button('Confirmar importación de gestiones',type='primary'):
                    storage.save(clean)
                    st.success('Respaldo incorporado.')
                    st.rerun()
            except Exception as exc:
                st.error(f'El respaldo no se pudo validar: {exc}')
        st.caption('Metodología: P1 cuenta presencia validada con fecha; P2 cuenta visita en '
                   'los primeros 100 PDV; P3 cuenta SOM posterior ≥ 60% con fecha de medición. '
                   'La meta Premium 63% → 66% requiere nuevo relevamiento de volumen para verificarse.')
