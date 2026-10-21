# Censo DDV — versión sin archivos .bat ni ejecutables

Este paquete contiene código fuente de Streamlit (Python), los parámetros visuales y, en la versión completa, los Excel originales. No incluye `.bat`, `.cmd`, `.ps1`, `.exe`, `.dll`, instaladores ni ejecutables de Windows.

## Arranque en Windows (PowerShell / Terminal)

1. Extraer el contenido del ZIP en una carpeta local, por ejemplo `Documentos\censo_ddv_app`.
2. Si usás la edición **solo código**, colocá tus archivos originales en `censo_ddv_app/data/`, con estos nombres exactos:
   - `abril_2026.xlsx`
   - `septiembre_2026.xlsx`
   Alternativamente podés cargarlos desde **Archivos de origen** en la barra lateral, sin copiarlos a la carpeta.
3. Instalar Python 3.10 o superior desde su sitio oficial, si todavía no lo tenés.
4. Abrir una terminal **dentro de `censo_ddv_app`** (por ejemplo, escribí `powershell` en la barra de direcciones del Explorador).
5. Ejecutar los comandos uno por uno:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

6. Abrir la URL que muestra Streamlit (habitualmente `http://localhost:8501`).

**No es necesario desactivar Windows Defender ni desproteger el navegador.** Si Windows detecta de nuevo malware, no fuerces la descarga/ejecución: consultá la detección concreta en *Seguridad de Windows > Protección contra virus y amenazas > Historial de protección*.

## Contenido de la app

- Dashboard general y Share of Market.
- Share of Segment, distribución física y ponderada.
- Marcas, calibres, supervisores, promotores, canales y subcanales.
- Evolución de clientes, oportunidades comerciales y PDA.
- Auditoría de censabilidad y exportación de resultados.

## Notas de seguridad y confidencialidad

Los Excel tienen información comercial. No los subas a GitHub público ni compartas el paquete completo fuera del equipo autorizado. El proyecto usa bibliotecas de Python de PyPI para instalar Streamlit y visualizar la información. Este reempaquetado elimina los lanzadores de Windows, pero no sustituye un examen antivirus local.
