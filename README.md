# CENSO DDV — tablero comparativo 2025–2026

Aplicación Streamlit para analizar censos de mercado de **Distribuidora del Valle (código 70549)**.

## ✅ Seguimiento de los tres planes de acción (nuevo)

En el panel lateral elegí **✅ Seguimiento de planes**. Esta sección conserva su
propia cartera fija de **septiembre 2026** y no depende de los filtros ni del par
de censos seleccionado en el resto del dashboard. Hay tres universos:

La planificación semanal, las acciones y los criterios para validar resultados
están en [`PLAN_COMERCIAL_SEP26.md`](PLAN_COMERCIAL_SEP26.md).

| Plan | Candidatos | Ola 1 | Meta operativa propuesta | Fecha propuesta |
| --- | ---: | ---: | --- | --- |
| P1. Core Plus en K+T | 62 PDV | 30 | Verificar presencia en 30 PDV | 15/01/2027 |
| P2. Intensidad Premium | 295 PDV | 100 | Registrar 100 visitas en ola 1 | 31/01/2027 |
| P3. Recuperar kioscos | 47 PDV | 17 | Medir 17 PDV que pasen a SOM ≥ 60% | 28/02/2027 |

**Son 404 asignaciones plan–PDV pero 339 PDV únicos.** Un mismo cliente puede
integrar más de un plan: no sumes los HL de los tres planes como si fueran
mercados independientes. Las fechas y metas son propuestas, editables en el
tablero. El corte oficial sigue siendo el SOM general DDV de 73,5%.

El tablero ofrece:

- Avance real contra meta, carga por supervisor/promotor y próximas gestiones vencidas.
- Ranking de primera ola por HL, filtros por plan, responsable, estado, cliente y ola.
- Ficha editable con estado, responsable, visita, fecha siguiente, validación,
  SOM posterior medido, evidencia y observaciones.
- Exportación e importación del respaldo CSV sin alterar los datos originales.
- Metas editables, guardadas junto al seguimiento.

**Reglas de avance:**

- **P1** solo contabiliza un PDV cuando se marca presencia validada **Sí** y se
  registra una fecha de verificación ya ocurrida.
- **P2** contabiliza una visita con fecha, solamente en los primeros 100 PDV
  priorizados, cuando la fecha ya ocurrió. La meta de SOM Premium plaza de **63% a 66%** no se da por
  lograda por visitar: debe validarse con una nueva medición de volúmenes.
- **P3** solo contabiliza un PDV recuperado si se carga SOM posterior **≥60%**
  y su fecha de medición ya ocurrida. Sin actualización no se considera recuperado.

### Guardado y continuidad

En PC/servidor con disco persistente, las gestiones se guardan automáticamente
en **SQLite local** (`.local/pda_seguimiento.sqlite3`, excluido de Git). No se
pierden al cerrar el navegador. **Streamlit Community Cloud no garantiza que
ese archivo sobreviva a un reinicio del servidor.** Allí conviene conectar una
Google Sheet privada para persistencia entre sesiones y usuarios:

1. Creá una Google Sheet privada, copiá su ID desde la URL.
2. Creá una cuenta de servicio en Google Cloud con Sheets API habilitada y
   compartí la Sheet con el correo de esa cuenta de servicio (Editor).
3. En Streamlit, **App → Settings → Secrets**, cargá el contenido siguiendo
   `.streamlit/secrets.example.toml`, con `pda_sheet_id` y
   `[gcp_service_account]`.
4. Reiniciá la aplicación. El módulo crea/usa las hojas `Seguimiento` y `Metas`
   sin tocar otras pestañas. El tablero confirma el modo *Google Sheets (persistente)*.

No pongas credenciales en GitHub. Como medida adicional, descargá un respaldo
CSV regularmente. Para volver a cargarlo, usá **Supervisión y respaldos →
Restaurar gestiones desde un respaldo CSV**; solo se aceptan claves plan–PDV
de la base oficial.

### Regeneración del padrón

El archivo `data/pda_objetivos_septiembre_2026.csv` es una foto del censo
oficial, sin datos de seguimiento. Reproducilo con:

```bash
python scripts/generar_carteras.py
```

Exige `data/septiembre_2026_oficial.xlsx` y verifica exactamente 62, 295 y 47
asignaciones de cada plan. Al regenerar el padrón no se borran las gestiones,
ya que se identifican por **Plan ID + Código PDV**.

**Actualización 17/11/2026:** septiembre se calcula a partir de `PATAGONIA_Resultados_Finales_Sept2026 VF (12.11).xlsx`, con resultados finales del 12/11/2026. Se conservan las fuentes de octubre de 2025 y abril de 2026.

## Selector de períodos

En el panel lateral, **Comparación de censos** permite elegir:
- **OCT-25 vs. ABR-26** (Octubre 2025 contra Abril 2026).
- **ABR-26 vs. SEP-26** (Abril 2026 contra Septiembre 2026).

Todas las secciones, filtros y descargas utilizan únicamente el par seleccionado: resumen, SOM, segmentos, distribución física y ponderada, marcas/calibres, equipo, oportunidades, clientes, plan de acción, auditoría y exportación a Excel.

### Criterio de publicación (vista inicial)

Para reproducir el tablero oficial de septiembre, la selección inicial es **Criterio de publicación (actual completo, anterior coincidente)**:

- **Censo actual:** todos los PDV del censo actual de DDV (70549).
- **Censo anterior:** solo los PDV del anterior cuyos códigos continúan presentes en el censo actual.
- **Septiembre 2026 frente a abril 2026, sin otros filtros:** septiembre conserva **1.442 PDV y SOM 73,48 % → 73,5 %**; abril conserva **1.158 de sus 1.253 PDV y SOM 71,77 % → 71,8 %**. La diferencia es **+1,72 pp → +1,7 pp**, como en el tablero oficial.
- Los **95 PDV de abril que no aparecen en septiembre** explican el cambio respecto del SOM completo de abril (71,65 %). En «Auditoría de datos» se pueden consultar y descargar en CSV.

**Atención:** esta comparación utiliza universos diferentes entre períodos. El dato de abril completo no se modifica. Podés elegir **Universo completo**, **Mismos PDV en ambos censos** o **Solo censables (auditoría)** para contrastar otras metodologías. La regla de publicación se aplica al par de censos que selecciones; para octubre–abril es un criterio de análisis y aún no está conciliado con una captura oficial externa.

## Ejecutar desde Windows

Abrir la carpeta que contiene `app.py` y `censo_engine.py`, escribir `cmd` en la barra de direcciones del Explorador y ejecutar:

```bat
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

La instalación de dependencias solo es necesaria la primera vez. La URL local suele ser http://localhost:8501.

## Para actualizar tu aplicación existente

1. Detené Streamlit en la consola con `Ctrl+C`.
2. Reemplazá **app.py** y copiá **pda_candidates.py**, **pda_storage.py** y **pda_tab.py** dentro de `censo_ddv_app`.
3. Copiá **data/pda_objetivos_septiembre_2026.csv** y mantené los Excel y JSON del censo que ya funcionan.
4. Actualizá **requirements.txt** e instalá dependencias con `python -m pip install -r requirements.txt`.
5. Ejecutá de nuevo `python -m streamlit run app.py` y elegí **✅ Seguimiento de planes**.

Para usar una instalación desde cero, copiá la carpeta del paquete completo, que ya incluye los tres censos.

## Fuente y precauciones

- Octubre de 2025: archivo `Template Consolidado Resultados Octubre 2025 MIO.xlsx`, pestaña `10-2025`.
- Abril de 2026: archivo `Template Consolidado Resultados Abril 2026(2).xlsx`, pestaña `Base HL`.
- Septiembre de 2026: archivo **`PATAGONIA_Resultados_Finales_Sept2026 VF (12.11).xlsx`**, pestaña `Hoja1`. En esta carpeta se guarda sin cambios de contenido con el nombre `septiembre_2026_oficial.xlsx`.
- La aplicación toma **primero** `septiembre_2026_oficial.xlsx`. Conserva `septiembre_2026.xlsx` como plantilla anterior de respaldo, con una advertencia visible cuando se use.
- Para abril se mantiene la plantilla **Abril 2026(2)**. La variante anterior **Abril 2026(1).xls** presenta volúmenes distintos y no reproduce el cierre del tablero oficial.
- En todos los meses se filtra estrictamente **DDV (código de distribuidor 70549)**. El archivo regional de septiembre contiene múltiples distribuidores.
- Octubre y abril: el **Share of Market total** usa las columnas `VOL CMQ.`, `VOL CCU.` y `VOL OTROS`; el detalle por segmento conserva los resúmenes declarados.
- Septiembre final: la planilla trae **90 preguntas de producto ya en HL**, sin columnas VOL ni resúmenes de segmentos. El motor agrupa cada pregunta por fabricante y segmento según `data/septiembre_productos.json` (mapeo de la plantilla original verificado contra los 90 encabezados del archivo final).
- **Gancia 0.0 y Vinos Value se excluyen** del denominador del SOM, de los segmentos y de los recuentos de presencia. Ambos vienen como `null` en el archivo final; la exclusión también queda explícita en el motor.
- Las distribuciones y segmentaciones se recalculan desde cada fuente y los filtros activos: no se cargan resultados porcentuales precalculados.
- Por **marca y calibre** se muestra presencia/distribución, no volumen exhaustivo, ya que los campos del cuestionario pueden solaparse.
- En octubre de 2025 el estado de relevamiento aparece como `Relevado`; abril de 2026 no presenta la misma variable de censabilidad y septiembre de 2026 sí tiene una bandera específica.
- **Control de cierre del septiembre oficial, DDV, universo completo:** 1.442 PDV; 6.380,56 HL de CMQ, 1.861,68 HL de CCU y 440,61 HL de Otros; mercado 8.682,85 HL; **SOM CMQ 73,48 %**. El universo contiene 1.127 PDV marcados `Si`, 164 `No` y 151 `0`. El SOM cambia si filtrás solo censables.
- La variación de HL entre censos no representa la evolución de la facturación ni necesariamente una variación del mercado anual comparable, dadas las diferencias de momento y universo relevado.
- El plan de acción editable se mantiene en memoria de sesión por comparación y puede exportarse como CSV.
- **Los datos incluyen información comercial interna**: evitá publicar la carpeta `data/` en repositorios públicos.

Si la aplicación se aloja en Streamlit Community Cloud, cargá estos archivos en un **repositorio privado** con acceso permitido en la plataforma; si no es posible, usá la carga manual desde el panel lateral y no publiques la base en un repositorio público.

**Importante para Git:** `.gitignore` excluye los Excel de `data/` para proteger información comercial. Si el repositorio es privado y decidís incluir los censos, agregalos de forma explícita desde `censo_ddv_app`:

```bash
git add -f data/octubre_2025.xlsx data/abril_2026.xlsx data/septiembre_2026_oficial.xlsx
git add -f data/pda_objetivos_septiembre_2026.csv
git add app.py censo_engine.py pda_candidates.py pda_storage.py pda_tab.py requirements.txt data/septiembre_productos.json PLAN_COMERCIAL_SEP26.md README.md tests/ scripts/ .streamlit/secrets.example.toml
```

No subas los Excel a un repositorio público.

No incluye archivos `.bat`, `.exe` ni otros lanzadores de Windows. Si una descarga sigue siendo bloqueada por el antivirus, no fuerces la descarga; usá los archivos por separado y revisá el motivo de la detección.
