# DDV · Gestión del canal mayorista · Galaxia 2.4.16

Tablero privado en **Google Apps Script**, alimentado por archivos existentes en Google Drive. Está diseñado para seguimiento operativo y preparación de auditorías; no implica validación regional ni calificación oficial de CMQ.

## Archivos incluidos

1. **Code.gs**: acceso a Drive, importaciones, cálculos, cierres y registro de evidencias.
2. **Index.html**: panel web responsive con ocho secciones.
3. **appsscript.json**: manifiesto que activa el servicio avanzado Drive API v3.
4. **test_local.js**: pruebas locales con Node.js, sin conectar ni modificar tu Drive.

## Instalación (una sola vez)

1. Ingresá a https://script.google.com/ y elegí **Nuevo proyecto**. Nombre sugerido: **DDV · Mayorista Galaxia**.
2. Abrí **Code.gs** del proyecto y reemplazá su contenido con el del archivo **Code.gs** de este paquete.
3. Junto a **Archivos**, pulsá **+ → HTML**. Poné el nombre **Index** (sin `.html`) y pegá el contenido de **Index.html**.
4. En **Configuración del proyecto**, activá **Mostrar archivo de manifiesto `appsscript.json` en el editor**. Reemplazá su contenido con el manifiesto adjunto.
5. En **Servicios**, pulsá **+**, elegí **Drive API**, versión **v3**, identificador **Drive**, y agregala. Si Google muestra que falta habilitar la API en el proyecto de Google Cloud, habilitá la **Google Drive API** allí. Esto es necesario para leer los Excel `.xlsx` sin modificarlos.
6. Guardá el proyecto. En el selector de funciones elegí **configurarProyecto** y pulsá **Ejecutar**. Autorizá el acceso. La función crea una Google Sheet nueva llamada *DDV · GALAXIA 2.4.16 · BASE Y EVIDENCIAS*.
7. Elegí **Implementar → Nueva implementación → Aplicación web**. Ejecutar como **yo**. En acceso elegí **Solo yo** para probar; para compartir, únicamente personal de DDV autorizado. **Nunca “Cualquier persona”** porque la base contiene información comercial y datos de clientes.
8. Abrí la URL de la aplicación web. En **Fuentes y cierres**, pulsá **Sincronizar datos principales**. El tablero ejecutará cuatro importaciones secuenciales: maestros, acciones, ventas y negociaciones.

Si abrís la vista antes de ejecutar `configurarProyecto`, aparecerá el botón **Crear base de datos**.

### Si la aplicación muestra un error o queda vacía

1. Usá **Comprobar conexión** dentro del tablero. El diagnóstico informa si la base existe, si tiene datos y si la cuenta del script puede abrirla.
2. Si indica que falta la base, ejecutá **configurarProyecto** en el editor de Apps Script; si existe pero no hay ventas, entrá a **Fuentes y cierres** y cargá las cuatro fuentes.
3. Después de cambiar `Code.gs` o `Index.html`, guardá y entrá a **Implementar → Administrar implementaciones → Editar (lápiz) → Versión nueva → Implementar**. La URL `/exec` sigue ejecutando la versión anterior hasta que publiques otra. Para pruebas rápidas también podés usar **Implementar → Probar implementaciones**, pero esa URL `/dev` requiere acceso al editor.
4. Un mensaje sobre `getEstadoProyecto` indica que la web recibió una respuesta vacía o inválida; no significa que los datos del Drive se hayan perdido. Volvé a comprobar que el código del servidor y la versión desplegada coincidan.

**Si ya tenés una aplicación funcionando:** reemplazá únicamente el contenido de **Code.gs** e **Index.html**, guardá y publicá **Versión nueva** desde **Implementar → Administrar implementaciones**. Se conserva la misma base, el enlace de la web y todo lo ya importado.

**Revisión posterior al diagnóstico del 14/11/2026:** Se confirmó que `diagnosticarProyecto` devolvía correctamente una base con ventas de noviembre, pero `getEstadoProyecto` llegaba vacío al navegador. El inicio del tablero ahora consulta directamente el método de diagnóstico, y la bitácora de cargas se obtiene en segundo plano al entrar a «Fuentes y cierres». Si alguna consulta de datos falla, el error identifica la función correspondiente (`getTablero` o `getComplementos`) para acotar el siguiente paso.

## Fuentes incorporadas

| Archivo de Drive | Qué aporta | Importación |
| --- | --- | --- |
| `ventadiaria.txt` | HL, facturación, cliente, fecha, SKU, marca y calibre | Ventas actuales |
| `ventadiaria bultos.txt` | Bultos reales en el mismo detalle | Ventas actuales |
| `ventadiaria bultos anual.txt` | Bultos reales desde mayo de 2025 hasta octubre de 2026 (aprox. 254 MB) | Preparación anual por tramos, **una sola vez** |
| `ventadiaria noviembre.txt` / `ventadiaria bultos noviembre.txt` | Par definitivo de HL y bultos para noviembre de 2026 | Cierre mensual automático al consultar el período |
| `reporte de clientes.xlsx` | Razón social, subcanal, bandera de comportamiento mayorista | Maestros |
| `AUXILIARES.xlsx` | Marca unificada y segmento | Maestros |
| `acciones_grupos_clientes_topes_con_sku.xlsx` | Acciones, grupo de clientes, grupos de producto, SKU explícitos, cortes de descuento | Acciones actuales |
| `NEGOCIACIONES.xlsx` | Negociaciones y descuentos relevados | Negociaciones |

Las carpetas y los IDs de los archivos actuales ya están configurados en `Code.gs`. Para las **acciones** se toma el Excel más reciente de la carpeta, pero se **verifica su mes de vigencia** antes de importarlo. No puede cargarse accidentalmente una foto de noviembre como si fuera octubre.

## Uso de cada mes

1. Durante el mes: reemplazá o actualizá los dos archivos `ventadiaria` en Drive y pulsá **Ventas actuales**. El sistema rechaza la importación si HL y bultos no coinciden en orden, cliente, SKU y demás claves de control.
2. Hacia el cierre: actualizá el Excel en la carpeta **ACIONES Y GRUPOS**, pulsá **Acciones actuales** y revisá los grupos y SKU.
3. Registrá cada solicitud de extensión en la aplicación. La aprobación exige indicar el medio/persona que confirmó el EDV; adjuntá una captura o enlace para respaldarla. El **estado de una extensión no se infiere automáticamente** por una oferta comercial o por superar un corte de descuento.
4. Registrá planes de acción y evidencias. Revisá la **estrategia borrador** en la hoja `ESTRATEGIA` y documentá la validación regional cuando exista.
5. Cuando corresponda, usá **Cerrar mes**. El cierre bloquea la sobrescritura de ventas y acciones de ese período, pero sigue permitiendo agregar planes, extensiones y evidencias.

### Nuevo flujo a partir de noviembre de 2026

1. Al cierre, subí **ambos TXT del mismo mes** a la misma carpeta histórica de Drive: `ventadiaria noviembre.txt` y `ventadiaria bultos noviembre.txt` (para diciembre, cambiá «noviembre» por «diciembre»). El tablero también reconoce nombres como `ventadiaria noviembre 2026.txt`.
2. Abrí el tablero, elegí ese mes en **Período** y pulsá **Actualizar vista**, o entrá a **Fuentes y cierres → Cargar automáticamente ese mes y los dos anteriores**. No se piden IDs: los dos archivos se buscan por nombre y se valida que sus filas coincidan.
3. Si se había cargado una foto parcial del mes durante su vigencia, **el par definitivo la reemplaza automáticamente** cuando ese mes pasa a ser histórico. Si sólo apareció uno de los dos archivos, **no se sobrescribe** un mes ya importado. Tampoco se reemplaza un mes marcado «Cerrado».
4. **Subí y verificá los dos TXT ANTES de pulsar «Cerrar mes»**, porque el cierre protege las ventas contra modificaciones. Para meses posteriores, repetí lo mismo. Al cambiar de año, agregá el año al nombre para evitar archivos homónimos (`ventadiaria enero 2027.txt` y `ventadiaria bultos enero 2027.txt`).
5. La aplicación revisa los tres períodos al abrir el tablero y al actualizar la vista. Desde un navegador que permanece abierto después de que subís los TXT, pulsá **Actualizar vista** para volver a comprobar el contenido de Drive.

### Preparación inicial de `ventadiaria bultos anual.txt`

El archivo anual confirmado en la carpeta de Drive pesa **253.581.986 bytes** y contiene, según tu descripción, mayo 2025–octubre 2026. Ese tamaño excede el importador normal de 35 MB y no se descarga entero en memoria ni se convierte a Excel.

1. Publicá esta versión del proyecto. Apps Script podría volver a pedirte autorización para consultar rangos de Drive y gestionar el procesamiento temporal.
2. En **Fuentes y cierres**, pulsá **Preparar histórico anual de bultos** una sola vez. Se crea una tarea temporal de Apps Script que lee tramos de 6 MiB, aproximadamente uno por minuto. Este trabajo **puede tardar alrededor de una hora**, según la velocidad de los servicios. Podés cerrar la pestaña: la preparación sigue en segundo plano. El botón **Consultar avance** muestra porcentaje, registros y conciliación de los 18 meses.
3. La preparación genera hojas compactas `B_AAAA_MM` en la base **privada** del tablero; el TXT original no se toca. Cuando termina de leerlo, intenta completar los bultos de cada `V_AAAA_MM` que ya tenga HL.
4. **No suma bultos por aproximación.** Sólo escribe bultos cuando coincide el juego completo de cliente, SKU, mes y negocio, y los importes netos del HL y del anual. Si hay diferencias, el mes se informa como «sin conciliación» y conserva sus datos. Si un mes no tiene HL, sus bultos quedan preparados y se incorporan cuando cargues su TXT de HL.
5. El proceso se puede reanudar desde el último tramo si falla por una causa transitoria; preserva los lotes y deduplica posibles repeticiones. Si Google no acepta la descarga parcial (por permisos, cuota o endpoint), se detiene con un error explícito: en ese caso habrá que obtener TXT de bultos **por mes** desde el ERP. No afirmamos que el anual ya está procesado hasta verificar el estado «Proceso anual terminado» en tu aplicación.

**Limitaciones:** tener sólo el TXT de bultos anual no incorpora HL que no estuvieran importados previamente. Para revisar evolución de mayo 2025 en adelante, la base necesita también los cortes mensuales correspondientes de HL. No se modifican meses ya cerrados; para rectificarlos se requiere un proceso explícito y auditado.

## Histórico desde mayo de 2025

**La importación de los meses necesarios para el comportamiento mayorista es automática al cambiar el filtro de período.** El tablero comprueba los tres meses contra Drive, carga los que faltan y revisa si los existentes ya tienen el **par definitivo** de HL y bultos o si pueden conciliarse con el anual preparado. Sólo reemplaza un mes histórico **no cerrado** cuando están los dos TXT mensuales coincidentes. No modifica las fuentes originales. Si los nombres son ambiguos o los archivos no se pueden conciliar, avisa sin inventar cantidades. Podés reintentar desde **Fuentes y cierres**.

También podés escribir directamente `2026-10` (o `2026 10`) en **Fuentes y cierres → Mes a analizar** y pulsar **Cargar automáticamente ese mes y los dos anteriores**. No necesitás pegar los ID de los tres TXT; el tablero selecciona octubre, septiembre y agosto y procesa sólo los que falten.

El formulario de **Fuentes y cierres → Importación manual excepcional** queda como respaldo si el archivo mensual no se puede identificar automáticamente. Recién en ese caso elegís el mes `AAAA-MM` y pegás el **ID** del TXT mensual de Drive.

El importador verifica que el archivo tenga **un único mes de ventas**. Si también tenés la versión del mes en bultos, podés indicar su ID. Si no existe, **el volumen histórico en HL sí se conserva, pero NO se calculan topes históricos como si tuviéramos bultos reales**. Los meses anteriores a los snapshots de acciones disponibles no heredan grupos de clientes actuales.

Los cortes mensuales mayores de 35 MB no se importan en una sola ejecución con el cargador ordinario; deben dividirse o procesarse por tramos. **La excepción específica es el archivo anual de bultos**, cuya preparación tiene un mecanismo propio en segundo plano.

### Comportamiento mayorista · comparación de tres meses móviles

El **mes elegido sí integra el cálculo**, junto con sus **dos meses calendario anteriores**. Por ejemplo:

| Mes seleccionado | Meses analizados automáticamente | Fuente requerida |
| --- | --- | --- |
| Octubre de 2026 | Octubre, septiembre y agosto de 2026 | `ventadiaria octubre.txt`, `venta septiembre.txt`, `venta agosto.txt` |
| Noviembre de 2026 | Noviembre, octubre y septiembre de 2026 | Noviembre del ERP + TXT de octubre y septiembre |
| Enero de 2027 | Enero de 2027, diciembre y noviembre de 2026 | Los tres cortes mensuales correspondientes |

Los archivos identificados para agosto, septiembre y octubre de 2026 ya tienen sus referencias configuradas; para otros meses el sistema intenta reconocer el período por el nombre del TXT. Si hay más de un archivo posible, no toma una decisión arbitraria. **Importar un mes puede llevar tiempo la primera vez**, pero las consultas posteriores usan los datos guardados. Cuando el período seleccionado todavía está abierto, se incluye su volumen **parcial**, y el tablero lo advierte expresamente.

Los indicadores se calculan en **HL de CERVEZAS CMQ** y por **subcanal**, usando la clasificación del maestro actual:

1. **Percentil 95 del promedio mensual:** para cada comprador se suman sus HL del mes seleccionado y de los dos anteriores y se dividen por 3. Dentro del subcanal, se ordenan los promedios positivos y se toma el valor en la posición `techo(N × 0,95)`. Se exige una muestra de al menos 10 compradores (ajustable en `PARAMETROS`). El P95 es una alerta exploratoria, no un reconocimiento automático de mayorista.
2. **Multiplicador contra la mediana:** `promedio mensual del cliente / mediana de promedios mensuales de compradores del mismo subcanal`. Se presenta como información para auditar; no se establece un umbral adicional inventado.
3. **Constancia:** se cuentan los meses (entre los 3 evaluados) en los que el cliente compró al menos la mediana mensual positiva de su subcanal. Una **alerta sostenida** requiere alcanzar P95 y ser alto en **2 o 3 meses**; una **alerta puntual** alcanza P95 pero no demuestra constancia suficiente.

**El P95 es condición necesaria para figurar en la lista de alertas CM.** Tener una bandera «Mayorista ERP» o «Comportamiento ERP», sin alcanzar el P95, **no alcanza** para incluir un cliente en los indicadores, totales o rankings de alertas. La coincidencia ERP sólo añade el sufijo `/ERP` a una alerta estadística que ya cumple el criterio.

| Situación | Clasificación visible | ¿Entra en las alertas CM? |
| --- | --- | --- |
| Alcanza P95 y muestra constancia en 2 de 3 meses; no está en ERP | `Alerta sostenida CM` | Sí |
| Alcanza P95 y muestra constancia; además está en ERP | `Alerta sostenida CM/ERP` | Sí |
| Alcanza P95 sin constancia suficiente | `Alerta puntual CM` o `Alerta puntual CM/ERP` | Sí |
| No alcanza P95, pero tiene bandera ERP | `ERP sin alerta CM` | **No** |
| No alcanza P95 ni tiene bandera ERP | `Comportamiento habitual` | No |

Si faltan meses para completar el cálculo, se indica el módulo como **pendiente** y las alertas del P95 de un solo mes se distinguen como `Alerta mensual CM` (con sufijo `/ERP` cuando corresponda). El listado **Clientes** muestra sólo alertas de forma predeterminada, ordenadas por **promedio mensual de HL de los tres meses** cuando ese histórico está completo; ofrece la opción **Todos los clientes** para consultar los demás sin sumarlos al ranking de alertas.

**Comportamiento habitual** es la categoría de clientes que no tienen una clasificación mayorista en ERP ni alcanzan el criterio de alerta estadística aplicable. No significa falta de compras, garantía de conducta comercial correcta ni validación oficial de Quilmes.

Cada importación genera una hoja compacta `M_AAAA_MM` con el volumen mensual de cada cliente. Los filtros consultan esas hojas para evitar cargar tres listados enteros de ventas cada vez. Los meses importados antes de esta versión siguen siendo compatibles, aunque pueden tardar más al hacer el primer cálculo. **Los TXT históricos sin archivo de bultos no sirven para auditar topes de bultos.**

## Reglas de negocio incorporadas

- **Core**: M1 Quilmes y M2 Brahma; productos de Core Escala 3 también incluyen el listado de 12 SKU definido por DDV. Los SKU **24709 y 32378** todavía requieren corroborar pertenencia formal al grupo del ERP.
- **Above Core**: Stella Artois, Andes Origen y Corona. Se distinguen **Stella+Andes**, **Stella 710×6**, **Corona 710**, **Corona 330**, por acción correspondiente.
- El nombre del grupo puede identificar producto/calibre: por ejemplo, **Corona 710** o **Corona porrón (330)**. Se usa SKU explícito cuando existe; grupos genéricos o sin identificación inequívoca quedan **parciales**, no se inventa su contenido.
- Un mismo SKU puede estar en varios grupos de producto de una acción; su consumo **se cuenta una sola vez**.
- **Corte promocional al 0%** (Book/ERP) y **cupo comercial autorizado** se guardan como **campos distintos**. El cupo se documenta desde la sección **Topes** con fundamento y responsable. Esto evita confundir diferencias como 84, 85, 168, 169, 150 y 400.
- La extensión agrega el **mismo volumen que el cupo original**; se admite una por **cliente + acción + mes**, con posibilidad de acciones diferentes en el mismo mes. Estados: solicitada, aprobada, rechazada y finalizada. Se registra el cambio de estado en una bitácora inalterada por nuevas ediciones.
- Se puede ingresar **manualmente** una acción histórica sobrescrita, junto con su código de excepción, por ejemplo octubre: **330535** y **329801**.
- El volumen principal se calcula en **HL de CERVEZAS CMQ**. No se penaliza vender pocos SKU. La concentración de los tres SKU principales ayuda a proponer oportunidades.
- Identificación de alertas CM: sólo clientes que alcanzan el percentil **95** de volumen de su **propio subcanal** (mínimo 10 compradores por defecto); ERP actúa como coincidencia y no como criterio de ingreso. El P95 es **exploratorio**, no una definición oficial de Quilmes. Se puede configurar en `PARAMETROS`.
- Un cliente actualmente anulado no se elimina de la historia si registró compras en el período.

## Auditoría: qué NO se considera acreditado automáticamente

- Una estrategia redactada en la planilla **no equivale a validación regional de CMQ**. La hoja `ESTRATEGIA` inicia como **PENDIENTE** y requiere responsable, fecha y respaldo.
- Tener un corte de descuento de 0% **no demuestra** que el sistema prohíba vender por fuera del cupo. Ese comportamiento operativo debe confirmarse.
- Los registros de devoluciones aparecen con cantidades negativas en el ERP. El tablero usa el neto exportado; si el control comercial de cupo funciona sobre bruto acumulado, será necesario adaptar esa regla tras confirmación.
- Los grupos con criterios dinámicos no explicitados pueden producir una **cobertura parcial**. La pantalla de topes lo indica.
- La puntuación de auditoría en pantalla es **una estimación interna condicionada por evidencias**; no sustituye la decisión del auditor.

## Verificación ejecutada antes de entregar

- Sintaxis de `Code.gs` y JavaScript de `Index.html`.
- Comparación real de las fuentes del mes abierto: **18.035 filas**, mismos encabezados y dimensiones, **102 registros con cantidad negativa**.
- Consolidación de esas filas a **14.745 combinaciones** de mes, cliente, SKU y unidad de negocio.
- Prueba de nombres de grupos Corona 710, Corona porrón y grupo ambiguo sin inventar SKU.
- Pruebas de ventana móvil (noviembre, octubre y cambio de año), percentil 95, mediana, constancia 2/3, meses faltantes y exclusión de otras unidades de negocio.
- Nuevas pruebas de nombres de cierre mensual HL y bultos, actualización de meses existentes sólo con un par definitivo, parser del bultos anual, deduplicación de lotes, conciliación de importes y rechazo seguro de diferencias.

**Pendiente:** ejecutar y autorizar el proyecto dentro de la cuenta Google que tiene acceso a los archivos, revisar que el servicio Drive v3 convierta correctamente el Excel y validar visualmente con datos reales tras desplegar. No se hizo ninguna implementación en la cuenta de Google del usuario desde aquí.
