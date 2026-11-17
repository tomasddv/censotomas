/**
 * GALAXIA 2.4.16 | Gestión del canal mayorista · DDV
 * Proyecto independiente de Google Apps Script, publicado SOLO para usuarios de DDV.
 * Las ventas y los cupos son datos diferentes: corte de descuento != cupo autorizado.
 * Requiere servicio avanzado Drive API v3 (incluido en appsscript.json).
 */
const MAY = Object.freeze({
  TZ: 'America/Argentina/Buenos_Aires',
  SALES_HL: '1I-vewZKeotS02twpDgSnmAbYjKT4mlXG',
  SALES_BULTOS: '169T6XFTCJpPManqx3dUR_-0nR1rJ4TZT',
  ANUAL_BULTOS_NOMBRE: 'ventadiaria bultos anual.txt',
  ANUAL_BULTOS_PROP: 'DDV_MAYORISTA_BULTOS_ANUAL',
  ANUAL_BULTOS_CHUNK: 6 * 1024 * 1024,
  HIST_FOLDER: '1cukgXLUaPsEDK_yD7tSwgaBFZAbiDUot',
  ACTION_FOLDER: '1_yiShRYnTR_7K-104EpjfwLVrwysgnHf',
  CLIENTS: '1VrxE5Tu1T_ruYkKf4eW3uiGoKlJcpCA6',
  AUX: '1zXhbWtT7K1tY43MmYz7oTTYifMgmLyFT',
  NEGOTIATIONS: '1u610F8_EjDFoDYCG_jQX4QtwQTXYDjaq',
  DB_PROP: 'DDV_MAYORISTA_DB',
  H: {
    CLIENTES: ['Código','Razón social','Fantasía','Subcanal','Comportamiento ERP','Mayorista ERP','Anulado','Fecha anulación'],
    AUX: ['Marca ERP','Marca unificada','Segmento','Segmento comercial'],
    VENTA: ['Mes','Cliente','SKU','Producto','Marca','Calibre','Negocio','HL','Bultos','Importe neto','Filas','Fuente HL','Fuente bultos'],
    ACCIONES: ['Acción','Segmento','Familia','Alcance','Nombre ERP','Canal','Calibre / producto','Grupo clientes','Nombre grupo','Estado','Descuento máximo','Desde bultos','Corte 0% bultos','Escalas','Vigencia'],
    MEMBRESIA: ['Grupo clientes','Cliente'],
    PRODUCTOS: ['Acción','Grupo productos','Nombre grupo productos'],
    SKU_GRUPO: ['Grupo productos','Nombre grupo productos','SKU','Descripción SKU','Estado'],
    EXTENSIONES: ['Clave','Mes','Cliente','Acción','Grupo de extensión','Estado','Cupo original','Cupo adicional','Fecha solicitud','Fecha respuesta','Confirmación EDV','Evidencia URL','Observaciones','Usuario','Actualizado','Acción de excepción'],
    PLANES: ['Clave','Mes','Cliente','Hallazgo','Plan de acción','Objetivo HL','Responsable','Vencimiento','Estado','Resultado','Actualizado'],
    TOPES: ['Clave','Mes','Acción','Canal','Cupo comercial bultos','Fundamento','Validado por','Actualizado'],
    AUDITORIA: ['Mes','Requisito','Estado','Evidencia','Observaciones','Responsable','Actualizado'],
    CONTROL: ['Tipo','Mes','Fuente','Fecha proceso','Filas','Resultado'],
    NEGOCIACIONES: ['Cliente','Detalle','Inicio','Fin','Estado','Fuente'],
    MOVIMIENTOS_EXT: ['Clave','Mes','Cliente','Acción','Estado anterior','Estado nuevo','Confirmación','Evidencia','Usuario','Fecha'],
    CIERRES: ['Mes','Fecha cierre','Usuario','Observaciones'],
    ESTRATEGIA: ['Versión','Objetivo','Criterios de identificación','Seguimiento','Mix y crecimiento','Control de topes','Validación regional','Validado por','Fecha validación','Actualizado'],
    PARAMETROS: ['Clave','Valor','Descripción'],
  }
});

function doGet() {
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('DDV · Gestión mayorista · Galaxia 2.4.16')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

function db_() {
  const id = PropertiesService.getScriptProperties().getProperty(MAY.DB_PROP);
  if (!id) throw new Error('Primero ejecutá configurarProyecto() en Apps Script.');
  return SpreadsheetApp.openById(id);
}

function sheet_(ss, name, headers) {
  let sh = ss.getSheetByName(name);
  if (!sh) {
    sh = ss.insertSheet(name);
    if (headers) {
      sh.getRange(1, 1, 1, headers.length).setValues([headers]);
      sh.setFrozenRows(1);
      sh.getRange(1,1,1,headers.length).setBackground('#dce7fa').setFontWeight('bold').setFontColor('#111111');
      // Sheets contabiliza también columnas vacías. En NUEVOS cortes mensuales
      // conservamos sólo las columnas necesarias para que entre todo el histórico.
      if(/^[VMB]_20\d\d_\d\d$/.test(name)&&sh.getMaxColumns()>headers.length){
        sh.deleteColumns(headers.length+1,sh.getMaxColumns()-headers.length);
      }
    }
  }
  return sh;
}

function rows_(name) {
  const sh = db_().getSheetByName(name);
  if (!sh || sh.getLastRow() < 2) return [];
  return sh.getRange(2, 1, sh.getLastRow()-1, sh.getLastColumn()).getValues();
}

function writeSheet_(name, headers, rows, replace) {
  const ss = db_();
  const sh = sheet_(ss, name, headers);
  if (replace && sh.getLastRow()>1) sh.getRange(2,1,sh.getLastRow()-1,sh.getLastColumn()).clearContent();
  if (rows.length) {
    const first = replace ? 2 : sh.getLastRow()+1;
    if (sh.getMaxRows() < first + rows.length - 1) sh.insertRowsAfter(sh.getMaxRows(), first + rows.length - 1 - sh.getMaxRows());
    if (sh.getMaxColumns() < headers.length) sh.insertColumnsAfter(sh.getMaxColumns(), headers.length - sh.getMaxColumns());
    for (let i=0;i<rows.length;i+=1500) {
      const block = rows.slice(i,i+1500);
      sh.getRange(first+i,1,block.length,headers.length).setValues(block);
    }
  }
  return rows.length;
}

function configurarProyecto() {
  const props = PropertiesService.getScriptProperties();
  let id=props.getProperty(MAY.DB_PROP);
  if (!id) {
    const ss=SpreadsheetApp.create('DDV · GALAXIA 2.4.16 · BASE Y EVIDENCIAS');
    id=ss.getId();
    props.setProperty(MAY.DB_PROP,id);
  }
  const ss=SpreadsheetApp.openById(id);
  Object.keys(MAY.H).forEach(k=>sheet_(ss,k,MAY.H[k]));
  const aud=ss.getSheetByName('AUDITORIA');
  if (aud.getLastRow()===1) {
    const m=monthNow_();
    const items=[
      ['Estrategia mayorista documentada','Pendiente'],
      ['Estrategia validada por región CMQ','Pendiente'],
      ['Clientes mayoristas y comportamiento identificados','En proceso'],
      ['Reporte evolutivo por PDV, mensual','En proceso'],
      ['Seguimiento de desvíos y planes de acción','En proceso'],
      ['Topes por cliente y acción, control mensual','En proceso'],
      ['Autorización regional para excedentes','Pendiente'],
    ];
    writeSheet_('AUDITORIA',MAY.H.AUDITORIA,items.map(r=>[m,r[0],r[1],'','', '',new Date()]),false);
  }
  const strat=ss.getSheetByName('ESTRATEGIA');
  if(strat.getLastRow()===1){
    strat.appendRow([
      'Borrador 1.0',
      'Maximizar las ventas de DDV en hectolitros, sostener clientes de alto volumen y buscar oportunidades comerciales rentables.',
      'Monitorear mayoristas ERP, clientes con flag Comportamiento Mayorista y clientes de otros subcanales con volumen significativamente superior a sus pares.',
      'Revisión semanal sugerida y reporte mensual por cliente: HL, bultos, tendencia, SKU, mix, negociación, topes y planes de acción.',
      'El crecimiento en HL es prioritario: comprar uno o muchos SKU no se penaliza. El mix permite detectar oportunidades de desarrollo.',
      'Registrar tope comercial por cliente y acción, consumo mensual y solicitudes de extensión. Una extensión por cliente y acción al mes, aprobada exclusivamente por Quilmes.',
      'PENDIENTE', '', '',new Date()
    ]);
  }
  const conf=ss.getSheetByName('PARAMETROS');
  if(conf.getLastRow()===1){
    conf.getRange(2,1,2,3).setValues([
      ['PERCENTIL_ALERTA',95,'Percentil de HL por subcanal para una señal estadística exploratoria; no es criterio oficial.'],
      ['MIN_CLIENTES_SUBCANAL',10,'Cantidad mínima de compradores positivos para calcular la alerta del subcanal.']
    ]);
  }
  return {ok:true,dbUrl:ss.getUrl(),id};
}

function monthNow_(){return Utilities.formatDate(new Date(),MAY.TZ,'yyyy-MM');}
function norm_(v){return String(v==null?'':v).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toUpperCase().trim();}
function num_(v) {
  if (v===null||v===undefined||v==='') return null;
  if (typeof v==='number') return isFinite(v)?v:null;
  const s=String(v).trim().replace(/\s/g,'');
  if (!s) return null;
  let x=s;
  if (s.indexOf(',')>=0) x=s.replace(/\./g,'').replace(',','.');
  const n=Number(x);return isFinite(n)?n:null;
}
function code_(v){return String(v==null?'':v).replace(/\.0$/,'').replace(/\D/g,'').replace(/^0+(?=\d)/,'');}
function month_(v){
  const s=String(v||'').trim();
  if (/^\d{4}-\d{2}$/.test(s))return s;
  const m=s.match(/\b(\d{1,2})[-\/](\d{1,2})[-\/](\d{2,4})\b/);
  if(m){const y=m[3].length===2?'20'+m[3]:m[3];return y+'-'+('0'+Number(m[2])).slice(-2);}
  const a=norm_(s).match(/\b\d{1,2}[-\s](ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|SEPT|OCT|NOV|DIC)[-\s](\d{2,4})\b/);
  if(a){const meses=['ENE','FEB','MAR','ABR','MAY','JUN','JUL','AGO','SEP','OCT','NOV','DIC'];const n=a[1]==='SEPT'?9:meses.indexOf(a[1])+1;return (a[2].length===2?'20'+a[2]:a[2])+'-'+('0'+n).slice(-2);}
  return null;
}
function validMonth_(v){const s=String(v||'');if(!/^20\d\d-(0[1-9]|1[0-2])$/.test(s))throw Error('Mes inválido');return s;}
function saleSheet_(month){return 'V_'+validMonth_(month).replace('-','_');}
function catSheet_(prefix,month){return prefix+'_'+validMonth_(month).replace('-','_');}
function log_(tipo,mes,fuente,filas,res){
  writeSheet_('CONTROL',MAY.H.CONTROL,[[tipo,mes,fuente,new Date(),filas,res]],false);
}

/**
 * Excel en Drive -> Google Sheets temporal -> lectura de valores.
 * La fuente original jamás se modifica; se necesita habilitar Drive API v3.
 */
function withXlsx_(fileId,callback){
  if (typeof Drive==='undefined' || !Drive.Files) throw Error('Falta habilitar el servicio avanzado Drive API v3.');
  const file=DriveApp.getFileById(fileId);
  let tmp=null;
  try{
    tmp=Drive.Files.create({
      name:'DDV_TEMP_CONVERSION_'+new Date().getTime(),
      mimeType:'application/vnd.google-apps.spreadsheet'
    },file.getBlob(),{fields:'id'});
    if(!tmp||!tmp.id)throw Error('No se pudo convertir el Excel a Google Sheets.');
    const ss=SpreadsheetApp.openById(tmp.id);
    return callback(ss);
  }finally{
    if(tmp&&tmp.id) {
      try{Drive.Files.remove(tmp.id);}catch(e){console.warn('Temporal pendiente de eliminar: '+tmp.id);}
    }
  }
}
function afterHeader_(values,isHeader){
  const i=values.findIndex(isHeader);
  if(i<0)throw Error('No se encontró el encabezado esperado en una hoja del Excel.');
  return values.slice(i+1);
}

function latestFile_(folderId,check){
  const iter=DriveApp.getFolderById(folderId).getFiles();let best=null;
  while(iter.hasNext()){
    const f=iter.next();
    if(!check(f))continue;
    if(!best||f.getDateCreated()>best.getDateCreated())best=f;
  }
  if(!best)throw Error('No encontré archivo válido en la carpeta '+folderId);
  return best;
}
function latestNamed_(filename,fallbackId){
  const iter=DriveApp.getFilesByName(filename);
  let best=null;
  while(iter.hasNext()){
    const f=iter.next();
    if(!best||f.getDateCreated()>best.getDateCreated())best=f;
  }
  return best?best.getId():fallbackId;
}

function importarMaestros() {
  configurarProyecto();
  const clientesId=latestFile_(MAY.HIST_FOLDER,f=>/^reporte de clientes\.xlsx$/i.test(f.getName())).getId();
  const auxiliaresId=latestNamed_('AUXILIARES.xlsx',MAY.AUX);
  const clients=withXlsx_(clientesId,ss=>{
    const sh=ss.getSheets()[0],data=sh.getDataRange().getValues(),header=data.shift().map(String);
    if(!header.includes('Cliente')||!header.includes('Descripcion subcanal')||!header.includes('Programa COMPORTAMIENTO MAYORISTA'))
      throw Error('Cambió el encabezado del maestro de clientes.');
    const ix=k=>header.indexOf(k), read=(r,k)=>ix(k)>=0?r[ix(k)]:'';
    return data.filter(r=>code_(read(r,'Cliente'))).map(r=>[
      code_(read(r,'Cliente')),String(read(r,'Razon social')||''),String(read(r,'Nombre de fantasia')||''),
      String(read(r,'Descripcion subcanal')||''),norm_(read(r,'Programa COMPORTAMIENTO MAYORISTA'))==='SI'?'Sí':'No',
      norm_(read(r,'Descripcion subcanal')).includes('MAYORISTA')?'Sí':'No',
      String(read(r,'Anulado')||''),String(read(r,'Anulado fecha')||''),
    ]);
  });
  writeSheet_('CLIENTES',MAY.H.CLIENTES,clients,true);
  const aux=withXlsx_(auxiliaresId,ss=>{
    const vals=ss.getSheets()[0].getDataRange().getValues().slice(1);
    return vals.filter(r=>r[0]).map(r=>[String(r[0]),String(r[1]||''),String(r[2]||''),String(r[3]||'')]);
  });
  writeSheet_('AUX',MAY.H.AUX,aux,true);
  log_('MAESTROS','',clientesId+' + '+auxiliaresId,clients.length,'OK');
  return {ok:true,clientes:clients.length,marcas:aux.length};
}

function importarAcciones(mes) {
  configurarProyecto();mes=validMonth_(mes||monthNow_());
  if(cerrado_(mes))throw Error('Mes cerrado: no se puede reemplazar el snapshot de acciones.');
  const f=latestFile_(MAY.ACTION_FOLDER,x=>/acciones_grupos_clientes_topes_con_sku\.xlsx$/i.test(x.getName()));
  const out=withXlsx_(f.getId(),ss=>{
    const r={acciones:[],membresia:[],productos:[],skus:[],advertencias:[]};
    const tabs=ss.getSheets();
    for(const sh of tabs){
      const name=sh.getName();
      const v=sh.getDataRange().getValues();
      if(name==='Acciones y grupos'){
        for(const row of afterHeader_(v,row=>norm_(row[1])==='NRO. ACCION')){
          if(!code_(row[1]))continue;
          r.acciones.push([
            code_(row[1]),String(row[2]||''),String(row[3]||''),String(row[4]||''),String(row[5]||''),
            String(row[6]||''),String(row[7]||''),code_(row[8]),String(row[9]||''),
            String(row[10]||''),num_(row[11]),num_(row[12]),num_(row[13]),String(row[14]||''),String(row[16]||'')
          ]);
        }
      } else if(/^Grupo \d+$/.test(name)){
        const group=name.replace('Grupo ','');
        for(const row of afterHeader_(v,row=>norm_(row[0])==='CODIGO CLIENTE')){const c=code_(row[0]);if(c)r.membresia.push([group,c]);}
      } else if(name==='Productos por acción'){
        for(const row of afterHeader_(v,row=>norm_(row[1])==='NRO. ACCION')){const action=code_(row[1]),group=code_(row[7]);if(action&&group)r.productos.push([action,group,String(row[8]||'')]);}
      } else if(name==='SKU por grupo'){
        for(const row of afterHeader_(v,row=>norm_(row[0])==='ID GRUPO PRODUCTOS')){
          const g=code_(row[0]);if(!g)continue;
          r.skus.push([g,String(row[1]||''),code_(row[2]),String(row[3]||''),String(row[4]||'')]);
        }
      }
    }
    if(!r.acciones.length||!r.productos.length||!r.membresia.length)throw Error('Faltan hojas o encabezados en el archivo de acciones.');
    const seen=new Set();r.membresia=r.membresia.filter(x=>{const k=x.join('|');if(seen.has(k))return false;seen.add(k);return true;});
    return r;
  });
  const fechaFuente=out.acciones.map(r=>month_(r[14])).find(Boolean);
  if(fechaFuente&&fechaFuente!==mes)throw Error('El archivo de acciones corresponde a '+fechaFuente+'; no puede importarse como '+mes+'.');
  writeSheet_(catSheet_('A',mes),MAY.H.ACCIONES,out.acciones,true);
  writeSheet_(catSheet_('C',mes),MAY.H.MEMBRESIA,out.membresia,true);
  writeSheet_(catSheet_('P',mes),MAY.H.PRODUCTOS,out.productos,true);
  writeSheet_(catSheet_('S',mes),MAY.H.SKU_GRUPO,out.skus,true);
  log_('ACCIONES',mes,f.getId(),out.acciones.length,'OK: snapshot del archivo '+f.getName());
  return {ok:true,mes,acciones:out.acciones.length,membresias:out.membresia.length,
    relaciones:out.productos.length,gruposSKU:out.skus.length,fuente:f.getName()};
}

function checkHeaders_(h) {
  if(h.length<47||norm_(h[4])!=='COD. CLIENTE'||norm_(h[17])!=='CODIGO'||norm_(h[40])!=='CANTIDADES TOTALES')
    throw Error('Cambió la estructura de ventadiaria: revisar columnas 4,17 y 40.');
}
function readTxt_(id) {
  const f=DriveApp.getFileById(id), bytes=f.getSize();
  if(bytes>35000000)throw Error('Archivo mayor a 35 MB: dividir/importar por mes.');
  const txt=f.getBlob().getDataAsString('Windows-1252').replace(/\r/g,'');
  const rows=txt.split('\n');const h=rows.shift().split('\t');checkHeaders_(h);
  return {id,head:h,rows:rows.filter(Boolean)};
}
function saleKey_(r){return [r[2],r[4],r[17],r[35],r[38],r[42]].join('|');}
function summarizeSales_(hl,bultos,strictMonth){
  if(bultos&&(hl.rows.length!==bultos.rows.length))throw Error('HL y bultos tienen distinta cantidad de filas. Se canceló la importación.');
  const map=new Map();let negative=0,checked=0;
  for(let i=0;i<hl.rows.length;i++){
    const a=hl.rows[i].split('\t'),b=bultos?bultos.rows[i].split('\t'):null;
    if(a.length<47)continue;
    if(b&&(b.length<47||saleKey_(a)!==saleKey_(b)))throw Error('No coinciden las ventas HL/bultos en la fila '+(i+2)+'. No se importó.');
    const mes=month_(a[2]);if(!mes)continue;
    if(strictMonth&&mes!==strictMonth)throw Error('Archivo mezcla períodos: '+mes+' y '+strictMonth+'. Usá un corte mensual.');
    const client=code_(a[4]),sku=code_(a[17]),negocio=String(a[35]||'');
    if(!client||!sku)continue;
    const key=[mes,client,sku,negocio].join('|');
    if(!map.has(key))map.set(key,[mes,client,sku,String(a[18]||''),String(a[20]||''),String(a[23]||''),negocio,0,b?0:null,0,0,hl.id,b?b.id:'']);
    const x=map.get(key),h=num_(a[40]),u=b?num_(b[40]):null,n=num_(a[42]);
    x[7]+=(h||0);if(b)x[8]+=(u||0);x[9]+=(n||0);x[10]++;
    if(h<0||u<0)negative++;checked++;
  }
  const vals=[...map.values()].sort((a,b)=>a[1].localeCompare(b[1])||a[2].localeCompare(b[2]));
  const months=[...new Set(vals.map(x=>x[0]))];
  return {vals,months,checked,negative};
}

function importarVentasActuales(mesEsperado){
  configurarProyecto();
  const hlId=latestFile_(MAY.HIST_FOLDER,f=>/^ventadiaria\.txt$/i.test(f.getName())).getId();
  const bulId=latestFile_(MAY.HIST_FOLDER,f=>/^ventadiaria bultos\.txt$/i.test(f.getName())).getId();
  const hl=readTxt_(hlId),bul=readTxt_(bulId);
  const sum=summarizeSales_(hl,bul);
  if(sum.months.length!==1)throw Error('ventadiaria actual contiene varios meses: '+sum.months.join(', '));
  const mes=sum.months[0];
  if(mesEsperado&&validMonth_(mesEsperado)!==mes)throw Error('El archivo ventadiaria actual corresponde a '+mes+', no a '+mesEsperado+'.');
  if(cerrado_(mes))throw Error('El mes '+mes+' está cerrado: la sincronización no lo modifica.');
  writeSheet_(saleSheet_(mes),MAY.H.VENTA,sum.vals,true);
  guardarVolumenMensualCliente_(mes,sum.vals);
  log_('VENTAS',mes,hl.id+' + '+bul.id,sum.checked,'OK; '+sum.negative+' registros negativos');
  return {ok:true,mes,registros:sum.checked,clientes:new Set(sum.vals.map(r=>r[1])).size,skus:new Set(sum.vals.map(r=>r[2])).size,
    filasResumen:sum.vals.length,negativos:sum.negative,bultosReales:true};
}

function listarHistoricos(){
  const folder=DriveApp.getFolderById(MAY.HIST_FOLDER),iter=folder.getFiles(),out=[];
  while(iter.hasNext()){
    const f=iter.next(),n=f.getName();
    if(/vent?a|diaria/i.test(n)&&/\.txt$/i.test(n)&&f.getSize()<35000000&&f.getId()!==MAY.SALES_HL&&f.getId()!==MAY.SALES_BULTOS){
      out.push({id:f.getId(),name:n,fecha:Utilities.formatDate(f.getLastUpdated(),MAY.TZ,'yyyy-MM-dd'),mb:Math.round(f.getSize()/1048576*10)/10});
    }
  }
  return out.sort((a,b)=>b.fecha.localeCompare(a.fecha)).slice(0,80);
}

/** Ubica un corte mensual sin pedir el ID en el formulario. Ante ambigüedad NO elige al azar. */
function coincideNombreHistorico_(nombre,mes){
  const n=norm_(nombre).replace(/[_.,-]/g,' ').replace(/\s+/g,' ');
  if(!/\b(VENTA|VENTAS|VENTADIARIA|DIARIA)\b/.test(n)||!/\.TXT$/i.test(String(nombre)))return false;
  if(/BULTOS/.test(n))return false;
  const year=mes.slice(0,4),mm=Number(mes.slice(5));
  const mesTexto=['ENERO','FEBRERO','MARZO','ABRIL','MAYO','JUNIO','JULIO','AGOSTO','SEPTIEMBRE','OCTUBRE','NOVIEMBRE','DICIEMBRE'][mm-1];
  const esMes=new RegExp('\\b'+mesTexto+'\\b').test(n)||
    (mm===9&&/\bSETIEMBRE\b/.test(n))||
    n.includes(year+' '+('0'+mm).slice(-2))||n.includes(('0'+mm).slice(-2)+' '+year)||
    n.includes(year+('0'+mm).slice(-2));
  const anios=n.match(/\b20\d\d\b/g)||[];
  return esMes&&(!anios.length||anios.includes(year));
}
/** El archivo de bultos mensual tiene el mismo mes que el TXT de HL. */
function coincideNombreBultosHistorico_(nombre,mes){
  if(!/\bBULTOS\b/.test(norm_(nombre)))return false;
  return coincideNombreHistorico_(String(nombre).replace(/\bbultos\b/i,''),mes);
}
function buscarBultosHistoricosAuto_(mes){
  const it=DriveApp.getFolderById(MAY.HIST_FOLDER).getFiles(),hallados=[];
  while(it.hasNext()){
    const f=it.next();
    if(coincideNombreBultosHistorico_(f.getName(),mes)&&f.getSize()<=35000000){
      hallados.push({id:f.getId(),nombre:f.getName(),conAnio:norm_(f.getName()).includes(mes.slice(0,4))});
    }
  }
  const precisos=hallados.filter(x=>x.conAnio),posibles=precisos.length?precisos:hallados;
  if(posibles.length>1)throw Error('Hay varios archivos de bultos para '+mes+': '+posibles.map(x=>x.nombre).join(', ')+'. Indicá el año en el nombre.');
  return posibles[0]||null;
}
function fuenteVentasMes_(mes){
  const sh=db_().getSheetByName(saleSheet_(mes));
  if(!sh||sh.getLastRow()<2)return null;
  const r=sh.getRange(2,1,1,MAY.H.VENTA.length).getValues()[0];
  const ultimo=sh.getRange(sh.getLastRow(),1,1,MAY.H.VENTA.length).getValues()[0];
  // La presencia de la fuente además del valor evita considerar completo un lote interrumpido.
  return {hl:String(r[11]||''),bultos:String(r[12]||''),
    tieneBultos:r[8]!==''&&r[8]!==null&&!!r[12]&&
      ultimo[8]!==''&&ultimo[8]!==null&&!!ultimo[12]};
}
function buscarVentasHistoricasAuto_(mes){
  const conocidos={
    '2026-08':'12c7hy-bTbg7P_1QYUyKKcooNLo4iog1x',
    '2026-09':'1tYmVEPu3eehimo42hcBaI7k4f0zcG1PP',
    '2026-10':'190CTcpwpXnb3r8jBMnwDYJVWsED8hVI2'
  };
  if(conocidos[mes])return {id:conocidos[mes],nombre:'Corte histórico '+mes};
  const it=DriveApp.getFolderById(MAY.HIST_FOLDER).getFiles(),coincidencias=[];
  while(it.hasNext()){
    const f=it.next();
    if(coincideNombreHistorico_(f.getName(),mes)&&f.getSize()<=35000000){
      const n=norm_(f.getName());
      coincidencias.push({id:f.getId(),nombre:f.getName(),conAnio:n.includes(mes.slice(0,4))});
    }
  }
  const precisos=coincidencias.filter(f=>f.conAnio),posibles=precisos.length?precisos:coincidencias;
  if(posibles.length>1)throw Error('Hay varios TXT posibles para '+mes+': '+posibles.map(x=>x.nombre).join(', ')+'. Revisar archivo antes de importar.');
  return posibles[0]||null;
}

/** Carga meses ausentes o incorpora el par definitivo HL/bultos al cierre. */
function importarHistoricoAutomatico(mes){
  mes=validMonth_(mes);
  try{
    const anterior=fuenteVentasMes_(mes);
    if(cerrado_(mes))return anterior?{ok:true,mes,existente:true,cerrado:true}:
      {ok:false,mes,motivo:'El mes está cerrado y no tiene ventas importadas.'};
    if(mes===monthNow_()){
      if(anterior)return {ok:true,mes,existente:true};
      const actual=importarVentasActuales(mes);
      return {ok:true,mes,importado:true,filas:actual.filasResumen};
    }
    const archivo=buscarVentasHistoricasAuto_(mes);
    const bultos=buscarBultosHistoricosAuto_(mes);
    // Un mes ya importado sólo se reemplaza si llegó el PAR mensual definitivo.
    // Nunca se pisa un histórico existente con un archivo de sólo HL.
    if(anterior){
      if(archivo&&bultos&&(anterior.hl!==archivo.id||anterior.bultos!==bultos.id)){
        const x=importarHistorico({mes,archivoHL:archivo.id,archivoBultos:bultos.id,reemplazar:true});
        return {ok:true,mes,actualizado:true,filas:x.filasResumen,bultosReales:true,archivo:archivo.nombre};
      }
      if(!anterior.tieneBultos){
        const x=completarBultosMesDesdeAnual_(mes);
        if(x&&x.actualizado)return {ok:true,mes,actualizado:true,bultosReales:true,origen:'anual'};
        if(x&&x.motivo)return {ok:true,mes,existente:true,aviso:x.motivo};
      }
      return {ok:true,mes,existente:true};
    }
    if(!archivo)return {ok:false,mes,motivo:'No se encontró un TXT de HL mensual inequívoco en Drive.'};
    const x=importarHistorico({mes,archivoHL:archivo.id,archivoBultos:bultos?bultos.id:'',reemplazar:false});
    // El archivo anual puede completar bultos de meses que sólo tenían HL.
    const anual=bultos?null:completarBultosMesDesdeAnual_(mes);
    return {ok:true,mes,importado:true,filas:x.filasResumen,archivo:archivo.nombre,
      bultosReales:!!bultos||!!(anual&&anual.actualizado)};
  }catch(e){return {ok:false,mes,motivo:String(e&&e.message||e)};}
}

/** Importación histórica deliberada: nunca pisa un mes cerrado sin marcar reemplazar=true. */
function importarHistorico(form){
  const f=form||{},id=String(f.archivoHL||'').trim(),bulId=String(f.archivoBultos||'').trim();
  const mes=validMonth_(f.mes),sh=db_().getSheetByName(saleSheet_(mes));
  if(cerrado_(mes))throw Error('Mes cerrado: no se permite reescritura de ventas históricas.');
  if(sh&&sh.getLastRow()>1&&!f.reemplazar)throw Error('El mes '+mes+' ya existe. Para cambiar un cierre se necesita confirmar reemplazar.');
  const hl=readTxt_(id),bul=bulId?readTxt_(bulId):null;
  const sum=summarizeSales_(hl,bul,mes);
  if(!sum.vals.length)throw Error('Sin ventas de '+mes+' en el archivo.');
  writeSheet_(saleSheet_(mes),MAY.H.VENTA,sum.vals,true);
  guardarVolumenMensualCliente_(mes,sum.vals);
  log_('HISTORICO',mes,id+(bulId?' + '+bulId:''),sum.checked,bul?'OK bultos reales':'OK solo HL; bultos no disponibles');
  return {ok:true,mes,registros:sum.checked,filasResumen:sum.vals.length,bultosReales:!!bul};
}

/**
 * El TXT anual de bultos pesa aproximadamente 254 MB: no puede leerse con getBlob()
 * en una ejecución de Apps Script. Se descarga por rangos de 6 MiB, una por tarea,
 * y se guarda sólo el agregado verificable por mes, cliente, SKU y negocio.
 * El lote identifica la posición de bytes. Si un lote se escribe dos veces a causa
 * de una interrupción, el lector descarta la copia por su clave lote+venta.
 */
function estadoBultosAnual_(){
  const s=PropertiesService.getScriptProperties().getProperty(MAY.ANUAL_BULTOS_PROP);
  if(!s)return null;
  try{return JSON.parse(s);}catch(e){throw Error('Estado de histórico anual dañado. Contactá al administrador antes de reiniciar.');}
}
function guardarEstadoBultosAnual_(s){PropertiesService.getScriptProperties().setProperty(MAY.ANUAL_BULTOS_PROP,JSON.stringify(s));}
function hojaBultosAnual_(mes){return 'B_'+validMonth_(mes).replace('-','_');}
function mesesArchivoBultosAnual_(){
  const out=[];let mes='2025-05';
  while(mes<='2026-10'){out.push(mes);const y=Number(mes.slice(0,4)),m=Number(mes.slice(5));mes=m===12?(y+1)+'-01':y+'-'+('0'+(m+1)).slice(-2);}
  return out;
}
function activarTriggerBultosAnual_(){
  if(!ScriptApp.getProjectTriggers().some(t=>t.getHandlerFunction()==='procesarHistoricoBultosEnSegundoPlano')){
    ScriptApp.newTrigger('procesarHistoricoBultosEnSegundoPlano').timeBased().everyMinutes(1).create();
  }
}
function eliminarTriggerBultosAnual_(){
  ScriptApp.getProjectTriggers().forEach(t=>{
    if(t.getHandlerFunction()==='procesarHistoricoBultosEnSegundoPlano')ScriptApp.deleteTrigger(t);
  });
}
function getProgresoHistoricoBultos(){
  const s=estadoBultosAnual_();
  if(!s)return {estado:'pendiente',mensaje:'Histórico anual de bultos sin procesar. Iniciá la carga una sola vez.'};
  return {estado:s.estado,fuente:s.nombre,bytes:s.bytes,procesados:s.offset,
    porcentaje:Math.min(100,Math.round(100*(s.offset||0)/(s.bytes||1))),
    registros:s.registros||0,omitidos:s.omitidos||0,
    mesesAplicados:s.aplicados||{},error:s.error||'',mensaje:s.mensaje||'',
    iniciado:s.iniciado||'',actualizado:s.actualizado||''};
}
/** Inicio explícito desde la interfaz: crea un único trigger y retoma el punto anterior. */
function iniciarHistoricoBultosAnual(){
  db_();
  const fuente=latestFile_(MAY.HIST_FOLDER,f=>norm_(f.getName())===norm_(MAY.ANUAL_BULTOS_NOMBRE));
  let s=estadoBultosAnual_();
  if(s&&(s.id!==fuente.getId()||s.bytes!==fuente.getSize()||s.modificado!==fuente.getLastUpdated().getTime())){
    throw Error('El archivo anual cambió desde la carga anterior. No se mezclaron versiones: revisá el histórico con el administrador.');
  }
  if(!s){
    s={id:fuente.getId(),nombre:fuente.getName(),bytes:fuente.getSize(),
      modificado:fuente.getLastUpdated().getTime(),offset:0,restante:'',
      estado:'leyendo',registros:0,omitidos:0,aplicarPos:0,aplicados:{},
      iniciado:new Date().toISOString(),mensaje:'Leyendo el TXT anual en tramos.'};
    guardarEstadoBultosAnual_(s);
  }
  if(s.estado==='terminado')return getProgresoHistoricoBultos();
  if(s.estado==='error'){
    s.estado=s.offset===s.bytes?'aplicando':'leyendo';s.error='';
    guardarEstadoBultosAnual_(s);
  }
  activarTriggerBultosAnual_();
  procesarHistoricoBultosEnSegundoPlano();
  return getProgresoHistoricoBultos();
}
/** Agrega grupos compactos: cuatro columnas para no agotar las celdas de Sheets. */
function guardarLoteBultos_(mes,lote,acumulados){
  if(!acumulados.size)return;
  const ss=db_(),name=hojaBultosAnual_(mes);let sh=ss.getSheetByName(name);
  if(!sh){
    sh=ss.insertSheet(name);
    sh.getRange(1,1,1,4).setValues([['Lote byte','Clave mes|cliente|SKU|negocio','Bultos','Importe neto']]);
    sh.setFrozenRows(1);
    // En una hoja NUEVA eliminamos las columnas vacías que contarían para el límite de celdas.
    if(sh.getMaxColumns()>4)sh.deleteColumns(5,sh.getMaxColumns()-4);
  }
  const filas=[...acumulados].map(([clave,v])=>[lote,clave,v[0],v[1]]);
  const inicio=sh.getLastRow()+1,necesarias=inicio+filas.length-1;
  if(sh.getMaxRows()<necesarias)sh.insertRowsAfter(sh.getMaxRows(),necesarias-sh.getMaxRows());
  for(let i=0;i<filas.length;i+=1500){const bloque=filas.slice(i,i+1500);sh.getRange(inicio+i,1,bloque.length,4).setValues(bloque);}
}
/** Función invocada por el trigger temporal, una tarea pequeña por minuto. */
function procesarHistoricoBultosEnSegundoPlano(){
  const lock=LockService.getScriptLock();
  if(!lock.tryLock(500))return {ocupado:true};
  try{
    const s=estadoBultosAnual_();
    if(!s||s.estado==='terminado')return getProgresoHistoricoBultos();
    if(s.estado==='error')return getProgresoHistoricoBultos();
    const f=DriveApp.getFileById(s.id);
    if(f.getSize()!==s.bytes||f.getLastUpdated().getTime()!==s.modificado)throw Error('Cambió el archivo anual durante la lectura. Proceso detenido para no mezclar versiones.');
    if(s.estado==='leyendo')procesarLoteBultosAnual_(s);
    else if(s.estado==='aplicando')aplicarLoteBultosAnual_(s);
    s.actualizado=new Date().toISOString();
    guardarEstadoBultosAnual_(s);
    if(s.estado==='terminado')eliminarTriggerBultosAnual_();
    return getProgresoHistoricoBultos();
  }catch(e){
    const s=estadoBultosAnual_();
    if(s){s.estado='error';s.error=String(e&&e.message||e).slice(0,750);guardarEstadoBultosAnual_(s);}
    eliminarTriggerBultosAnual_();
    console.error('Bultos anual detenido: '+(e&&e.stack||e));
    return getProgresoHistoricoBultos();
  }finally{lock.releaseLock();}
}
function procesarLoteBultosAnual_(s){
  const desde=s.offset,hasta=Math.min(s.bytes-1,desde+MAY.ANUAL_BULTOS_CHUNK-1);
  if(desde>=s.bytes){s.estado='aplicando';return;}
  const url='https://www.googleapis.com/drive/v3/files/'+encodeURIComponent(s.id)+'?alt=media';
  const respuesta=UrlFetchApp.fetch(url,{headers:{Authorization:'Bearer '+ScriptApp.getOAuthToken(),
    Range:'bytes='+desde+'-'+hasta},muteHttpExceptions:true});
  if(respuesta.getResponseCode()!==206)throw Error('Drive no devolvió el tramo solicitado (HTTP '+respuesta.getResponseCode()+'). La lectura anual requiere descargas parciales.');
  const bytes=respuesta.getContent();
  if(bytes.length!==hasta-desde+1)throw Error('El tramo de Drive llegó incompleto: '+bytes.length+' bytes recibidos, '+(hasta-desde+1)+' esperados.');
  const contenido=Utilities.newBlob(bytes).getDataAsString('Windows-1252');
  const partes=(s.restante+contenido).split('\n');
  s.restante=partes.pop();
  if(hasta===s.bytes-1&&s.restante){partes.push(s.restante);s.restante='';}
  if(desde===0){checkHeaders_(String(partes.shift()||'').replace(/\r$/,'').split('\t'));}
  const resumen=resumirLineasBultosAnual_(partes),lote=desde;
  if(desde===0&&!resumen.registros)throw Error('El primer tramo del anual no tiene ventas válidas entre 2025-05 y 2026-10. Revisá fechas y columnas antes de procesar.');
  // Sólo adelantamos el cursor luego de escribir TODOS los agregados del lote.
  // Si Apps Script se interrumpe antes, la repetición queda deduplicada por lote+clave.
  for(const [mes,valores] of resumen.buckets)guardarLoteBultos_(mes,lote,valores);
  s.offset=hasta+1;s.registros+=resumen.registros;s.omitidos+=resumen.omitidos;
  if(s.offset>=s.bytes){s.estado='aplicando';s.restante='';s.mensaje='Archivo leído. Conciliando los bultos con los meses de HL ya importados.';}
}
/** Agregación testeable de líneas, sin tocar Drive. */
function resumirLineasBultosAnual_(lineas){
  const buckets=new Map();let registros=0,omitidos=0;
  for(const linea of lineas){
    if(!linea.trim())continue;
    const r=linea.replace(/\r$/,'').split('\t');
    if(r.length<47){omitidos++;continue;}
    const mes=month_(r[2]),cliente=code_(r[4]),sku=code_(r[17]),negocio=String(r[35]||'');
    if(!mes||mes<'2025-05'||mes>'2026-10'||!cliente||!sku){omitidos++;continue;}
    const b=num_(r[40]),fact=num_(r[42]);
    if(b===null||fact===null){omitidos++;continue;}
    if(!buckets.has(mes))buckets.set(mes,new Map());
    const map=buckets.get(mes),clave=[mes,cliente,sku,negocio].join('|');
    if(!map.has(clave))map.set(clave,[0,0]);
    const v=map.get(clave);v[0]+=b;v[1]+=fact;registros++;
  }
  return {buckets,registros,omitidos};
}
function completarBultosMesDesdeAnual_(mes){
  const s=estadoBultosAnual_();
  if(!s||!['aplicando','terminado'].includes(s.estado))return null;
  const sh=db_().getSheetByName(saleSheet_(mes));
  if(!sh||sh.getLastRow()<2)return {motivo:'No hay HL importados todavía en '+mes+'.'};
  if(cerrado_(mes))return {motivo:'El período '+mes+' está cerrado. No se modificaron sus ventas.'};
  const prev=fuenteVentasMes_(mes);
  if(prev&&prev.tieneBultos)return {existente:true};
  const bs=db_().getSheetByName(hojaBultosAnual_(mes));
  if(!bs||bs.getLastRow()<2)return {motivo:'El anual no contiene bultos de '+mes+'.'};
  const vistos=new Set(),agregados=new Map();
  for(const r of rows_(hojaBultosAnual_(mes))){
    const lote=String(r[0]),clave=String(r[1]),marcador=lote+'|'+clave;
    if(vistos.has(marcador))continue;
    vistos.add(marcador);
    if(!agregados.has(clave))agregados.set(clave,[0,0]);
    const v=agregados.get(clave);v[0]+=num_(r[2])||0;v[1]+=num_(r[3])||0;
  }
  const ventas=rows_(saleSheet_(mes));
  const valores=[];let faltantes=0,diferencias=0;
  for(const r of ventas){
    const k=[mes,code_(r[1]),code_(r[2]),String(r[6]||'')].join('|');
    const val=agregados.get(k);
    if(!val){faltantes++;continue;}
    const netoHL=num_(r[9])||0,tolerancia=Math.max(1,Math.abs(netoHL)*0.0000001);
    if(Math.abs(val[1]-netoHL)>tolerancia)diferencias++;
    valores.push([val[0]]);
  }
  if(faltantes||diferencias||agregados.size!==ventas.length){
    return {motivo:'Bultos anuales de '+mes+' sin conciliación exacta: '+faltantes+
      ' claves HL sin bultos, '+Math.max(0,agregados.size-ventas.length+faltantes)+
      ' claves adicionales y '+diferencias+' importes distintos. Se preservan los datos anteriores.'};
  }
  if(!ventas.length)return {motivo:'No hay ventas de '+mes+'.'};
  for(let i=0;i<valores.length;i+=1500){
    const v=valores.slice(i,i+1500);
    sh.getRange(i+2,9,v.length,1).setValues(v);
    sh.getRange(i+2,13,v.length,1).setValues(v.map(()=>[s.id]));
  }
  log_('BULTOS ANUAL',mes,s.id,valores.length,'Conciliación completa HL/bultos (claves e importe neto)');
  return {actualizado:true,filas:valores.length};
}
function aplicarLoteBultosAnual_(s){
  const meses=mesesArchivoBultosAnual_();
  if(s.aplicarPos>=meses.length){s.estado='terminado';s.mensaje='Histórico anual conciliado. Los meses sin HL quedan disponibles para completar al incorporarlos.';return;}
  const mes=meses[s.aplicarPos],r=completarBultosMesDesdeAnual_(mes);
  s.aplicados[mes]=r&&r.actualizado?'Conciliado ('+r.filas+' filas)':
    r&&r.existente?'Ya tenía bultos':(r&&r.motivo||'Sin cambios');
  s.aplicarPos++;
  if(s.aplicarPos>=meses.length){s.estado='terminado';s.mensaje='Procesamiento anual terminado. Revisá las conciliaciones por mes.';}
}

function importarNegociaciones(){
  configurarProyecto();
  const negoId=latestNamed_('NEGOCIACIONES.xlsx',MAY.NEGOTIATIONS);
  const data=withXlsx_(negoId,ss=>{
    const all=ss.getSheets()[0].getDataRange().getValues();
    if(norm_(all[0][0])!=='FECHA INICIO'||norm_(all[0][2])!=='CLIENTE')
      throw Error('Cambió la estructura de NEGOCIACIONES.xlsx.');
    const v=all.slice(2);
    return v.filter(r=>code_(r[2])).map(r=>[
      code_(r[2]),[String(r[12]||''),String(r[13]||''),String(r[14]||''),'Bonif. '+String(r[15]||0)+'%'].join(' · '),
      r[0] instanceof Date?Utilities.formatDate(r[0],MAY.TZ,'yyyy-MM-dd'):String(r[0]||''),
      r[1] instanceof Date?Utilities.formatDate(r[1],MAY.TZ,'yyyy-MM-dd'):String(r[1]||''),
      'Vigencia declarada',negoId
    ]);
  });
  writeSheet_('NEGOCIACIONES',MAY.H.NEGOCIACIONES,data,true);
  log_('NEGOCIACIONES','',negoId,data.length,'OK');
  return {ok:true,filas:data.length};
}

function getEstadoProyecto(){
  const ss=db_(),names=ss.getSheets().map(x=>x.getName());
  const meses=names.filter(x=>/^V_20\d\d_\d\d$/.test(x)).map(x=>x.slice(2,6)+'-'+x.slice(7)).sort().reverse();
  const catalogos=names.filter(x=>/^A_20\d\d_\d\d$/.test(x)).map(x=>x.slice(2,6)+'-'+x.slice(7)).sort().reverse();
  const fuente=rows_('CONTROL').slice(-12).map(r=>({tipo:r[0],mes:r[1],archivo:r[2],fecha:r[3] instanceof Date?Utilities.formatDate(r[3],MAY.TZ,'dd/MM/yyyy HH:mm'):String(r[3]),filas:r[4],resultado:r[5]})).reverse();
  return {meses,catalogos,mesDefault:meses[0]||monthNow_(),fuente,dbUrl:ss.getUrl(),mesActual:monthNow_()};
}

/** Bitácora opcional: no impide que se abra el tablero si falla la lectura. */
function getRegistroControl(){
  return rows_('CONTROL').slice(-12).map(r=>({
    tipo:String(r[0]||''),mes:String(r[1]||''),archivo:String(r[2]||''),
    fecha:r[3] instanceof Date?Utilities.formatDate(r[3],MAY.TZ,'dd/MM/yyyy HH:mm'):String(r[3]||''),
    filas:Number(r[4]||0),resultado:String(r[5]||'')
  })).reverse();
}

/** Diagnóstico sin escrituras: permite diferenciar configuración, permisos y cargas faltantes. */
function diagnosticarProyecto(){
  const id=PropertiesService.getScriptProperties().getProperty(MAY.DB_PROP);
  if(!id)return {ok:false,mensaje:'No existe una base configurada. Ejecutá configurarProyecto().',baseConfigurada:false};
  try{
    const ss=SpreadsheetApp.openById(id);
    const hojas=ss.getSheets().map(sh=>sh.getName());
    const meses=hojas.filter(n=>/^V_20\d\d_\d\d$/.test(n));
    const acciones=hojas.filter(n=>/^A_20\d\d_\d\d$/.test(n));
    return {ok:true,mensaje:meses.length?'La base responde y hay períodos de ventas disponibles.':'La base responde, pero todavía no se importaron ventas.',
      baseConfigurada:true,baseUrl:ss.getUrl(),cantidadHojas:hojas.length,
      mesesVentas:meses.map(n=>n.slice(2,6)+'-'+n.slice(7)).sort().reverse(),
      mesesAcciones:acciones.map(n=>n.slice(2,6)+'-'+n.slice(7)).sort().reverse(),mesActual:monthNow_(),
      maestrosClientes:hojas.includes('CLIENTES')?(ss.getSheetByName('CLIENTES').getLastRow()-1):0,
      maestrosAux:hojas.includes('AUX')?(ss.getSheetByName('AUX').getLastRow()-1):0};
  }catch(e){return {ok:false,baseConfigurada:true,mensaje:'No se puede abrir la base. Revisá el permiso de la cuenta que ejecuta el script.',detalle:String(e&&e.message||e)};}
}

function ventasMes_(mes){return rows_(saleSheet_(mes)).map(r=>({
  mes:String(r[0]),cliente:code_(r[1]),sku:code_(r[2]),producto:String(r[3]||''),
  marca:String(r[4]||''),calibre:String(r[5]||''),negocio:String(r[6]||''),
  hl:num_(r[7])||0,bultos:num_(r[8]),fact:num_(r[9])||0,filas:num_(r[10])||0
}));}

/** Resumen liviano por cliente y mes para evitar releer 3 archivos completos en cada filtro. */
function volumenClienteSheet_(mes){return 'M_'+validMonth_(mes).replace('-','_');}
function calcularVolumenMensualCliente_(ventas){
  const acumulado=new Map();
  ventas.forEach(r=>{
    if(norm_(r[6])!=='CERVEZAS CMQ')return;
    const cliente=code_(r[1]);if(!cliente)return;
    acumulado.set(cliente,(acumulado.get(cliente)||0)+(num_(r[7])||0));
  });
  return acumulado;
}
function guardarVolumenMensualCliente_(mes,ventas){
  const mapa=calcularVolumenMensualCliente_(ventas);
  const resumen=[...mapa].map(([cliente,hl])=>[mes,cliente,hl]);
  writeSheet_(volumenClienteSheet_(mes),['Mes','Cliente','HL cervezas CMQ'],resumen,true);
  return resumen.length;
}
function volumenClienteHistorico_(mes){
  const ss=db_(),resumen=ss.getSheetByName(volumenClienteSheet_(mes));
  if(resumen&&resumen.getLastRow()>1)return new Map(rows_(volumenClienteSheet_(mes)).map(r=>[code_(r[1]),num_(r[2])||0]));
  const ventas=ss.getSheetByName(saleSheet_(mes));
  if(!ventas||ventas.getLastRow()<2)return null;
  // Compatibilidad con meses importados antes de incorporar el resumen liviano.
  return calcularVolumenMensualCliente_(rows_(saleSheet_(mes)));
}
function clientesMap_(){
  const m=new Map();
  rows_('CLIENTES').forEach(r=>m.set(code_(r[0]),{
    codigo:code_(r[0]),razon:String(r[1]||''),fantasia:String(r[2]||''),
    subcanal:String(r[3]||'Sin subcanal'),comportamiento:String(r[4])==='Sí',
    mayoristaERP:String(r[5])==='Sí',anulado:String(r[6]||''),anuladoFecha:String(r[7]||'')
  }));
  return m;
}
function auxMap_(){
  const m=new Map();rows_('AUX').forEach(r=>m.set(norm_(r[0]),{
    marca:String(r[1]||r[0]),segmento:String(r[3]||r[2]||'')
  }));return m;
}
function familiaComercial_(r){
  const s=norm_(r.marca)+' '+norm_(r.producto);
  if(/\bBRAHMA\b/.test(s))return 'M2 · Brahma';
  if(/\bQUILMES\b/.test(s))return 'M1 · Quilmes';
  if(/STELLA|CORONA|ANDES ORIGEN/.test(s))return 'Above Core';
  return 'Otras marcas';
}
function agruparCliente_(ventas,clients,aux) {
  const totals=new Map();
  for(const r of ventas) {
    if(norm_(r.negocio)!=='CERVEZAS CMQ')continue;
    const c=clients.get(r.cliente)||{codigo:r.cliente,razon:'Cliente '+r.cliente,fantasia:'',subcanal:'Sin subcanal',comportamiento:false,mayoristaERP:false,anulado:'',anuladoFecha:''};
    if(!totals.has(r.cliente))totals.set(r.cliente,Object.assign({},c,{
      hl:0,bultos:0,fact:0,skus:new Set(),marcas:new Set(),bySKU:[],segmentos:{},
      top3HL:0,participacionTop3:0
    }));
    const t=totals.get(r.cliente);t.hl+=r.hl;t.fact+=r.fact;
    if(t.bultos!==null&&r.bultos!==null)t.bultos+=r.bultos;else t.bultos=null;
    if(r.hl>0)t.skus.add(r.sku);
    const brand=aux.get(norm_(r.marca));
    if(r.hl>0)t.marcas.add(brand?brand.marca:r.marca);
    const seg=brand?brand.segmento:'Sin clasificar';
    t.segmentos[seg]=(t.segmentos[seg]||0)+r.hl;
    t.bySKU.push({sku:r.sku,producto:r.producto,marca:r.marca,calibre:r.calibre,hl:r.hl,bultos:r.bultos,segmento:seg});
  }
  const arr=[...totals.values()].map(t=>{
    t.bySKU.sort((a,b)=>b.hl-a.hl);t.top3HL=t.bySKU.slice(0,3).reduce((s,x)=>s+x.hl,0);
    t.participacionTop3=t.hl>0?t.top3HL/t.hl:null;
    t.cantidadSKU=t.skus.size;t.cantidadMarcas=t.marcas.size;
    delete t.skus;delete t.marcas;
    return t;
  });
  return arr;
}

/** El P95 define la inclusión en alertas CM. ERP es una coincidencia informativa, nunca un atajo. */
function clasificarAlertaCM_(alertaP95,sostenida,tieneERP,mensual){
  if(!alertaP95)return tieneERP?'ERP sin alerta CM':'Comportamiento habitual';
  const base=mensual?'Alerta mensual CM':sostenida?'Alerta sostenida CM':'Alerta puntual CM';
  return base+(tieneERP?'/ERP':'');
}
function identificarComportamiento_(arr){
  const p=rows_('PARAMETROS'),get=(k,d)=>{const a=p.find(r=>String(r[0])===k);return a&&num_(a[1])!==null?num_(a[1]):d;};
  const percentile=Math.min(99.9,Math.max(50,get('PERCENTIL_ALERTA',95)))/100;
  const minN=Math.max(3,Math.round(get('MIN_CLIENTES_SUBCANAL',10)));
  const grupos=new Map();
  arr.forEach(c=>{
    if(c.hl<=0)return;
    const k=norm_(c.subcanal);
    if(!grupos.has(k))grupos.set(k,[]);
    grupos.get(k).push(c.hl);
  });
  const umbrales=new Map();
  grupos.forEach((a,k)=>{
    a.sort((x,y)=>x-y);
    const i=Math.max(0,Math.ceil(a.length*percentile)-1);
    umbrales.set(k,a.length>=minN?a[i]:null);
  });
  arr.forEach(c=>{
    const p95=umbrales.get(norm_(c.subcanal));
    c.umbralP95=p95;
    c.alertaEstadistica=p95!==null&&p95!==undefined&&c.hl>=p95&&c.hl>0;
    c.tipo=clasificarAlertaCM_(c.alertaEstadistica,false,c.mayoristaERP||c.comportamiento,true);
    c.identificado=c.alertaEstadistica;
  });
  return arr;
}

function mesesVentanaMovil_(mes,cantidad){
  const resultado=[];let actual=validMonth_(mes);
  for(let i=0;i<cantidad;i++){resultado.unshift(actual);actual=prevMonth_(actual);}
  return resultado;
}
function medianaPositiva_(valores){
  const ordenados=valores.filter(x=>Number.isFinite(x)&&x>0).sort((a,b)=>a-b);
  if(!ordenados.length)return null;
  const medio=Math.floor(ordenados.length/2);
  return ordenados.length%2?ordenados[medio]:(ordenados[medio-1]+ordenados[medio])/2;
}
function percentilRango_(valores,p){
  const ordenados=valores.filter(x=>Number.isFinite(x)&&x>0).sort((a,b)=>a-b);
  if(!ordenados.length)return null;
  return ordenados[Math.max(0,Math.ceil(ordenados.length*p)-1)];
}

/** Tres indicadores: posición P95, multiplicador sobre mediana y constancia mensual. */
function calcularComportamientoTrimestral_(mes,clientes,obtenerMes){
  const periodos=mesesVentanaMovil_(mes,3);
  const mensuales=periodos.map(p=>obtenerMes(p));
  const faltantes=periodos.filter((_,i)=>mensuales[i]===null);
  const info={periodos,faltantes,completo:!faltantes.length,porCliente:new Map(),criterio:
    'P95 del promedio mensual del mes seleccionado y los dos anteriores; multiplicador contra la mediana del subcanal; constancia si supera la mediana de su subcanal en al menos 2 de 3 meses.'};
  if(faltantes.length)return info;
  const keys=new Set();mensuales.forEach(map=>map.forEach((_,id)=>keys.add(id)));
  const clientesPeriodo=new Map();
  keys.forEach(codigo=>{
    const cli=clientes.get(codigo),subcanal=norm_(cli?cli.subcanal:'Sin subcanal');
    const valores=mensuales.map(map=>map.get(codigo)||0);
    const promedio=valores.reduce((a,b)=>a+b,0)/3;
    clientesPeriodo.set(codigo,{codigo,subcanal,valores,promedio});
  });
  const grupos=new Map();
  clientesPeriodo.forEach(c=>{
    if(c.promedio<=0)return;
    if(!grupos.has(c.subcanal))grupos.set(c.subcanal,[]);
    grupos.get(c.subcanal).push(c);
  });
  const config=rows_('PARAMETROS'),buscar=(k,def)=>{const r=config.find(x=>String(x[0])===k);return r&&num_(r[1])!==null?num_(r[1]):def;};
  const percentil=Math.min(99.9,Math.max(50,buscar('PERCENTIL_ALERTA',95)))/100;
  const minClientes=Math.max(3,Math.round(buscar('MIN_CLIENTES_SUBCANAL',10)));
  const perfiles=new Map();
  grupos.forEach((arr,subcanal)=>{
    const promedio=arr.map(c=>c.promedio),mediana=medianaPositiva_(promedio);
    const p95=arr.length>=minClientes?percentilRango_(promedio,percentil):null;
    const medianasMes=periodos.map((_,i)=>medianaPositiva_(arr.map(c=>c.valores[i])));
    perfiles.set(subcanal,{mediana,p95,medianasMes,compradores:arr.length});
  });
  clientesPeriodo.forEach(c=>{
    const p=perfiles.get(c.subcanal),mediana=p?p.mediana:null,p95=p?p.p95:null;
    const altos=p?c.valores.filter((v,i)=>v>0&&p.medianasMes[i]!==null&&v>=p.medianasMes[i]).length:0;
    info.porCliente.set(c.codigo,{
      promedioHL:c.promedio,medianaHL:mediana,p95HL:p95,
      multiplicador:mediana>0?c.promedio/mediana:null,
      mesesConCompra:c.valores.filter(v=>v>0).length,mesesAltos:altos,
      volumenes:c.valores,alertaP95:p95!==null&&c.promedio>=p95&&c.promedio>0,
      sostenido:p95!==null&&c.promedio>=p95&&c.promedio>0&&altos>=2,
      compradoresSubcanal:p?p.compradores:0
    });
  });
  return info;
}

function resumenMensual_(mes){
  if(!db_().getSheetByName(saleSheet_(mes)))return null;
  const v=ventasMes_(mes);let hl=0;
  const clientes=new Set();
  v.forEach(r=>{if(norm_(r.negocio)==='CERVEZAS CMQ'){hl+=r.hl;if(r.hl>0)clientes.add(r.cliente);}});
  return {mes,hl,clientes:clientes.size};
}

function getTablero(mes){
  mes=validMonth_(mes||getEstadoProyecto().mesDefault);
  const vals=ventasMes_(mes),clients=clientesMap_(),aux=auxMap_();
  const all=identificarComportamiento_(agruparCliente_(vals,clients,aux));
  const trimestre=calcularComportamientoTrimestral_(mes,clients,volumenClienteHistorico_);
  all.forEach(c=>{
    c.historial=trimestre.completo?(trimestre.porCliente.get(c.codigo)||{
      promedioHL:0,medianaHL:null,p95HL:null,multiplicador:null,mesesConCompra:0,mesesAltos:0,
      volumenes:[0,0,0],alertaP95:false,sostenido:false,compradoresSubcanal:0}):null;
    if(!trimestre.completo)return;
    c.tipo=clasificarAlertaCM_(c.historial.alertaP95,c.historial.sostenido,c.mayoristaERP||c.comportamiento,false);
    c.identificado=c.historial.alertaP95;
  });
  all.sort((a,b)=>b.hl-a.hl);
  const total=all.reduce((s,c)=>s+c.hl,0);
  const identified=all.filter(c=>c.identificado);
  const prev=prevMonth_(mes),last=String(Number(mes.slice(0,4))-1)+mes.slice(4);
  const ant=resumenMensual_(prev),aa=resumenMensual_(last);
  // No habilitar auditoría de topes si una escritura por tramos quedó incompleta.
  const mesesConBultos=vals.length>0&&vals.every(v=>v.bultos!==null);
  const mix={};
  vals.filter(v=>norm_(v.negocio)==='CERVEZAS CMQ').forEach(v=>{
    const k=familiaComercial_(v);mix[k]=(mix[k]||0)+v.hl;
  });
  const data={
    mes,ultimoCierre:mes!==monthNow_(),fuenteBultos:mesesConBultos,
    kpis:{
      volumenHL:total,compradores:all.filter(c=>c.hl>0).length,
      comportamiento:identified.length,
      mayoristasERP:all.filter(c=>c.mayoristaERP).length,
      alertasSostenidas:all.filter(c=>c.tipo.startsWith('Alerta sostenida CM')).length,
      alertasPuntuales:all.filter(c=>c.tipo.startsWith('Alerta puntual CM')).length,
      alertasERP:identified.filter(c=>c.comportamiento||c.mayoristaERP).length,
      volumenComportamiento:identified.reduce((s,c)=>s+c.hl,0),
      prevHL:ant?ant.hl:null,aaHL:aa?aa.hl:null,
    },
    mix,clientes:all.map(c=>({
      codigo:c.codigo,razon:c.razon,fantasia:c.fantasia,subcanal:c.subcanal,
      tipo:c.tipo,comportamiento:c.comportamiento,mayoristaERP:c.mayoristaERP,
      hl:c.hl,bultos:c.bultos,fact:c.fact,sku:c.cantidadSKU,marcas:c.cantidadMarcas,
      participacionTop3:c.participacionTop3,umbralP95:c.umbralP95,
      segmentos:c.segmentos,topSKU:c.bySKU.slice(0,5),historial:c.historial
    })),
    comportamientoTrimestral:{periodos:trimestre.periodos,faltantes:trimestre.faltantes,
      completo:trimestre.completo,criterio:trimestre.criterio},
    periodos:periodosDisponibles_(),
    acciones:accionesMes_(mes).map(a=>({
      accion:a.accion,canal:a.canal,familia:a.familia,alcance:a.alcance,grupo:a.grupo,
      nombreGrupo:a.nombreGrupo,estado:a.estado,corte:a.corte,desde:a.desde,
      descuento:a.descuento,calibre:a.calibre
    })),
    avisos:[
      mes===monthNow_()?'Mes abierto: ventas parciales y modificables.':'',
      !mesesConBultos?'No hay bultos reales para este período: control de topes no calculable.':'',
      !db_().getSheetByName(catSheet_('A',mes))?'Sin snapshot de acciones de este mes: no se extrapolan grupos de otros períodos.':'',
      trimestre.faltantes.length?'Comportamiento mayorista trimestral pendiente: importá ventas de '+trimestre.faltantes.join(', ')+'. Se mantiene la alerta mensual exploratoria hasta completar el histórico.':'',
      'Alerta por percentil de subcanal: criterio configurable y exploratorio, no definición oficial de CMQ.',
      'El corte a 0% de descuento no constituye automáticamente un límite comercial autorizado.'
    ].filter(Boolean)
  };
  return data;
}
function prevMonth_(mes){const d=new Date(Number(mes.slice(0,4)),Number(mes.slice(5,7))-2,1);return d.getFullYear()+'-'+('0'+(d.getMonth()+1)).slice(-2);}
function periodosDisponibles_(){return db_().getSheets().map(s=>s.getName()).filter(n=>/^V_20\d\d_\d\d$/.test(n)).map(n=>n.substring(2,6)+'-'+n.substring(7)).sort().reverse();}
function getClienteDetalle(mes,codigo){
  mes=validMonth_(mes);codigo=code_(codigo);
  const client=clientesMap_().get(codigo);
  const aux=auxMap_();let total=0;
  const venta=ventasMes_(mes).filter(r=>r.cliente===codigo&&norm_(r.negocio)==='CERVEZAS CMQ').map(r=>{
    total+=r.hl;
    const a=aux.get(norm_(r.marca));
    return {sku:r.sku,producto:r.producto,marca:a?a.marca:r.marca,calibre:r.calibre,segmento:a?a.segmento:'Sin clasificar',familia:familiaComercial_(r),hl:r.hl,bultos:r.bultos,fact:r.fact};
  }).sort((a,b)=>b.hl-a.hl);
  const neg=rows_('NEGOCIACIONES').filter(r=>code_(r[0])===codigo).map(r=>({detalle:String(r[1]),inicio:String(r[2]),fin:String(r[3])})).slice(0,35);
  return {cliente:client||{codigo,razon:'Sin maestro'},mes,total,venta,negociaciones:neg};
}

function accionesMes_(mes){
  const a=rows_(catSheet_('A',mes)),seen=new Set();
  return a.filter(r=>{const id=code_(r[0]);if(!id||seen.has(id)||!/CONFIRMADO/i.test(String(r[9])))return false;seen.add(id);return true;}).map(r=>({
    accion:code_(r[0]),segmento:String(r[1]),familia:String(r[2]),alcance:String(r[3]),
    nombre:String(r[4]),canal:String(r[5]),calibre:String(r[6]),grupo:code_(r[7]),
    nombreGrupo:String(r[8]),estado:String(r[9]),descuento:num_(r[10]),desde:num_(r[11]),
    corte:num_(r[12]),escalas:String(r[13]),vigencia:String(r[14])
  }));
}

function normalGroupMatch_(name,sale,aux){
  const n=norm_(name),b=norm_(sale.marca),c=norm_(sale.calibre),d=norm_(sale.producto);
  const both=c+' '+d,can=/LAT(A|AS|ON|ONES)|CAN\b/.test(both),lit=/1000|1200|LITRO|1L\b|1,2/.test(both);
  const stella=/STELLA/.test(b+' '+d),corona=/CORONA/.test(b+' '+d),andes=/ANDES ORIGEN|AO\b/.test(b+' '+d);
  const ics=aux.get(b),seg=ics?norm_(ics.segmento):'';
  if(n.includes('CORONA PORRON'))return corona&&/330|355|PORRON/.test(both);
  if(n.includes('CORONA 710'))return corona&&/710/.test(both);
  if(n.includes('CORONA LATA'))return corona&&can;
  if(n.includes('SA 710')||n.includes('STELLA 710'))return stella&&/710/.test(both);
  if(n.includes('SA LATA Y PORRON'))return stella&&(can||/330|355|PORRON/.test(both));
  if(n.includes('SA LITRO'))return stella&&lit;
  if(n.includes('STELLA PURE GOLD')||n.includes('SA PURE GOLD'))return stella&&/PURE GOLD|PG\b/.test(d);
  if(n.includes('STELLA 0.0'))return stella&&/0\.0|SIN ALCOHOL/.test(d);
  if(n.includes('AO LITRO Y LATA'))return andes&&(lit||can);
  if(n.includes('AO VARIEDADES'))return andes||/PATAGONIA/.test(b);
  if(n.includes('PATAGONIA LATA Y 730'))return /PATAGONIA/.test(b)&&(can||/730/.test(both));
  if(n.includes('STOUT LITRO'))return /STOUT/.test(d)&&lit;
  if(n.includes('BRAHMA Y QUILMES 269'))return /BRAHMA|QUILMES/.test(b)&&/269/.test(both);
  if(n.includes('VALUE LATA'))return /VALUE/.test(seg)&&can;
  if(n.includes('VALUE LITRO'))return /VALUE/.test(seg)&&lit;
  if(n.includes('LATON VALUE'))return /VALUE/.test(seg)&&/710|710CC|LATON/.test(both);
  if(n.includes('CORE LATA'))return /CORE/.test(seg)&&can;
  if(n.includes('CORE CLASICO LITRO Y LATA'))return /CORE/.test(seg)&&(lit||can);
  if(n.includes('LATA 1890'))return /1890/.test(d)&&can;
  if(n.includes('1890 LITRO'))return /1890/.test(d)&&lit;
  if(n.includes('1890 LATON'))return /1890/.test(d)&&/710|LATON/.test(both);
  // Grupos genéricos GP-..., combinaciones comerciales y criterios dinámicos requieren relevamiento.
  return null;
}

function getControlAccion(mes,accion){
  mes=validMonth_(mes);accion=code_(accion);
  const a=accionesMes_(mes).find(x=>x.accion===accion);
  if(!a)throw Error('No existe snapshot de la acción '+accion+' en '+mes);
  const clienteGroup=new Map();
  rows_(catSheet_('A',mes)).filter(r=>code_(r[0])===accion).forEach(r=>clienteGroup.set(code_(r[7]),true));
  const members=new Set(rows_(catSheet_('C',mes)).filter(r=>clienteGroup.has(code_(r[0]))).map(r=>code_(r[1])));
  const rel=rows_(catSheet_('P',mes)).filter(r=>code_(r[0])===accion).map(r=>({group:code_(r[1]),nombre:String(r[2]||'')}));
  const skus=new Map();
  rows_(catSheet_('S',mes)).forEach(r=>{
    const id=code_(r[0]);if(!skus.has(id))skus.set(id,new Set());if(code_(r[2]))skus.get(id).add(code_(r[2]));
  });
  const aux=auxMap_(),clientes=clientesMap_();
  // Alcance CORE Escala 3 confirmado verbalmente por DDV. Dos SKU no figuran
  // explícitos en el detalle del grupo del ERP: queda advertido al auditor.
  const core12=new Set(['2218','7026','7030','7038','7634','13503','19019',
    '19026','24709','28263','28846','32378']);
  const coreOverride=accion==='3493'||accion==='3494';
  const joined=new Map(),problemas=new Set();
  const all=ventasMes_(mes).filter(x=>members.has(x.cliente));
  for(const r of all) {
    let ok=coreOverride&&core12.has(r.sku);
    for(const g of rel) {
      const explicit=skus.get(g.group);
      const direct=!!(explicit&&explicit.has(r.sku));
      const inferred=direct?false:normalGroupMatch_(g.nombre,r,aux);
      if(direct||inferred===true){ok=true;break;}
      if(inferred===null&&(!explicit||!explicit.size))problemas.add(g.nombre);
    }
    if(!ok)continue;
    if(!joined.has(r.cliente))joined.set(r.cliente,{cliente:r.cliente,hl:0,bultos:0,sku:new Set()});
    const t=joined.get(r.cliente);t.hl+=r.hl;
    if(t.bultos!==null&&r.bultos!==null)t.bultos+=r.bultos;else t.bultos=null;
    t.sku.add(r.sku);
  }
  const caps=rows_('TOPES').find(r=>String(r[1])===mes&&code_(r[2])===accion);
  const cap=caps?num_(caps[4]):null;
  const exts=rows_('EXTENSIONES').filter(r=>String(r[1])===mes&&code_(r[3])===accion);
  const extMap=new Map(exts.map(r=>[code_(r[2]),r]));
  const aprobacionesHistoricas=new Set(rows_('MOVIMIENTOS_EXT')
    .filter(r=>String(r[1])===mes&&code_(r[3])===accion&&String(r[5])==='Aprobada').map(r=>code_(r[2])));
  const result=[...members].map(c=>{
    const t=joined.get(c)||{hl:0,bultos:all.length&&all.every(v=>v.bultos!==null)?0:null,sku:new Set()};
    const ext=extMap.get(c),aprobada=!!ext&&(String(ext[5])==='Aprobada'||
      (String(ext[5])==='Finalizada'&&aprobacionesHistoricas.has(c)));
    const concuerda=cap===null||!aprobada||Math.abs((num_(ext[6])||0)-cap)<.001;
    const extra=aprobada&&concuerda?(num_(ext[7])||0):0;
    const usable=cap===null?null:cap+extra;
    let estado='Sin cupo comercial validado';
    if(t.bultos===null)estado='Sin bultos históricos';
    else if(usable!==null)estado=t.bultos>usable?'Excede cupo':t.bultos>=usable*.9?'Próximo al límite':'Dentro del cupo';
    if(!concuerda)estado+=' · extensión no concuerda con cupo';
    if(problemas.size)estado=estado+' · cobertura parcial de SKU';
    const cli=clientes.get(c);
    return {cliente:c,razon:cli?cli.razon:'Cliente '+c,subcanal:cli?cli.subcanal:'',
      hl:t.hl,bultos:t.bultos,sku:t.sku.size,cupo:cap,extra,efectivo:usable,estado,
      extension:ext?String(ext[5]):'Sin solicitud'};
  });
  result.sort((x,y)=>(y.bultos||0)-(x.bultos||0));
  if(coreOverride)problemas.add('Core Escala 3: SKU 24709 y 32378 incluidos por definición DDV; validar en ERP');
  return {mes,accion:a,clientes:result,gruposProducto:rel,problemasSKU:[...problemas],
    muestra:result.length,parcial:problemas.size>0,
    advertencia:'Cupo comercial separado del corte de descuento; extensiones aprobadas solo con registro. Los grupos sin SKU o criterio claro dejan cobertura parcial.'};
}

function usuario_(){return Session.getActiveUser().getEmail()||'Usuario sin correo visible';}
function texto_(v,max){return String(v==null?'':v).trim().slice(0,max||1000);}
function dia_(v){const s=String(v||'');return /^20\d\d-\d\d-\d\d$/.test(s)?s:'';}
function guardarPlan(f){
  f=f||{};const mes=validMonth_(f.mes),cliente=code_(f.cliente);
  if(!cliente)throw Error('Indicá código de cliente.');
  if(!texto_(f.plan,2500))throw Error('El plan de acción no puede quedar vacío.');
  const key=mes+'|'+cliente+'|'+texto_(f.hallazgo,100).slice(0,50);
  const status=['Pendiente','En gestión','Finalizado','Cancelado'].includes(f.estado)?f.estado:'Pendiente';
  const objetivo=num_(f.objetivo),row=[
    key,mes,cliente,texto_(f.hallazgo,400),texto_(f.plan,2500),
    objetivo,texto_(f.responsable,140),dia_(f.vencimiento),status,texto_(f.resultado,1500),new Date()
  ];
  saveUnique_('PLANES',MAY.H.PLANES,key,row);
  return {ok:true,clave:key};
}
function listarPlanes(mes){mes=validMonth_(mes);return rows_('PLANES').filter(r=>String(r[1])===mes).map(r=>({
  clave:r[0],mes:r[1],cliente:code_(r[2]),hallazgo:String(r[3]),plan:String(r[4]),
  objetivo:num_(r[5]),responsable:String(r[6]),vencimiento:String(r[7]),estado:String(r[8]),resultado:String(r[9])
}));}
function saveUnique_(name,headers,key,row){
  const lock=LockService.getScriptLock();lock.waitLock(25000);
  try{
    const sh=sheet_(db_(),name,headers),last=sh.getLastRow();
    const keys=last>1?sh.getRange(2,1,last-1,1).getValues().map(r=>String(r[0])):[];
    const ix=keys.indexOf(String(key));
    if(ix<0)sh.getRange(last+1,1,1,row.length).setValues([row]);
    else sh.getRange(ix+2,1,1,row.length).setValues([row]);
  }finally{lock.releaseLock();}
}
function guardarTopeComercial(f) {
  f=f||{};const accion=code_(f.accion),valor=num_(f.tope),mes=validMonth_(f.mes);
  if(!accion||valor===null||valor<=0)throw Error('Indicá acción y cupo comercial en bultos.');
  if(!texto_(f.fundamento,1000))throw Error('Registrá el fundamento o fuente del cupo.');
  const action=accionesMes_(mes).find(a=>a.accion===accion);
  if(!action)throw Error('Acción no encontrada en el snapshot del mes.');
  const key=mes+'|'+accion;
  saveUnique_('TOPES',MAY.H.TOPES,key,[
    key,mes,accion,action.canal,valor,texto_(f.fundamento,1000),texto_(f.validadoPor,160),new Date()
  ]);
  return {ok:true,mes,accion,cupo:valor};
}
function listarTopes(mes){return rows_('TOPES').filter(r=>String(r[1])===mes).map(r=>({accion:code_(r[2]),canal:String(r[3]),cupo:num_(r[4]),fundamento:String(r[5]),validado:String(r[6])}));}

function guardarExtension(f){
  f=f||{};
  const mes=validMonth_(f.mes),cliente=code_(f.cliente),accion=code_(f.accionManual||f.accion),grupo=texto_(f.grupo,90);
  const allowed=['Solicitada','Aprobada','Rechazada','Finalizada'];
  const estado=allowed.includes(f.estado)?f.estado:'Solicitada';
  const original=num_(f.original),extra=num_(f.extra);
  if(!cliente||!accion)throw Error('Completá cliente y acción.');
  // Deben poder registrarse excepciones históricas aunque el ERP haya
  // sobrescrito la acción o no tengamos su snapshot original.
  if(original===null||original<=0||extra===null||extra<=0)throw Error('Indicá el cupo original y adicional en bultos.');
  if(estado==='Aprobada'&&!texto_(f.edv,400))throw Error('Para aprobar, registrá quién y cómo confirmó el EDV.');
  if(extra!==original)throw Error('La extensión agrega el mismo cupo que el original. Revisá los bultos.');
  const key=[mes,cliente,accion].join('|');
  const old=rows_('EXTENSIONES').find(r=>String(r[0])===key),antes=old?String(old[5]):'Sin registro';
  const row=[key,mes,cliente,accion,grupo,estado,original,extra,dia_(f.solicitud),dia_(f.respuesta),
    texto_(f.edv,400),texto_(f.evidencia,800),texto_(f.observaciones,1200),usuario_(),new Date(),code_(f.accionExcepcion)];
  const lock=LockService.getScriptLock();lock.waitLock(25000);
  try{
    const sh=sheet_(db_(),'EXTENSIONES',MAY.H.EXTENSIONES),end=sh.getLastRow();
    const keys=end>1?sh.getRange(2,1,end-1,1).getValues().map(r=>String(r[0])):[];
    const ix=keys.indexOf(key);
    if(ix<0)sh.getRange(end+1,1,1,row.length).setValues([row]);
    else sh.getRange(ix+2,1,1,row.length).setValues([row]);
    const hist=sheet_(db_(),'MOVIMIENTOS_EXT',MAY.H.MOVIMIENTOS_EXT);
    hist.appendRow([key,mes,cliente,accion,antes,estado,texto_(f.edv,400),texto_(f.evidencia,800),usuario_(),new Date()]);
  }finally{lock.releaseLock();}
  return {ok:true,clave:key,estado};
}
function listarExtensiones(mes){
  mes=validMonth_(mes);return rows_('EXTENSIONES').filter(r=>String(r[1])===mes).map(r=>({
    clave:r[0],mes:r[1],cliente:code_(r[2]),accion:code_(r[3]),grupo:String(r[4]||''),
    estado:String(r[5]||''),original:num_(r[6]),extra:num_(r[7]),solicitud:String(r[8]||''),
    respuesta:String(r[9]||''),edv:String(r[10]||''),evidencia:String(r[11]||''),
    observaciones:String(r[12]||''),accionExcepcion:code_(r[15]),evidenciaPendiente:!String(r[11]||'').trim()
  }));
}

function guardarAuditoria(f){
  f=f||{};const mes=validMonth_(f.mes),requisito=texto_(f.requisito,180);
  if(!requisito)throw Error('Elegí un requisito.');
  const estados=['Pendiente','En proceso','Cumplido','No cumple'];
  const estado=estados.includes(f.estado)?f.estado:'Pendiente';
  if(estado==='Cumplido'&&!texto_(f.evidencia,1000))throw Error('Para marcar «Cumplido», adjuntá una evidencia comprobable.');
  const all=rows_('AUDITORIA'),key=mes+'|'+requisito;
  const row=[mes,requisito,estado,texto_(f.evidencia,1000),texto_(f.observaciones,1800),texto_(f.responsable,120),new Date()];
  const lock=LockService.getScriptLock();lock.waitLock(25000);
  try{
    const sh=sheet_(db_(),'AUDITORIA',MAY.H.AUDITORIA);
    const ix=all.findIndex(r=>String(r[0])+'|'+String(r[1])===key);
    if(ix<0)sh.appendRow(row);
    else sh.getRange(ix+2,1,1,row.length).setValues([row]);
  }finally{lock.releaseLock();}
  return {ok:true};
}
function listarAuditoria(mes){
  mes=validMonth_(mes);
  const rows=rows_('AUDITORIA').filter(r=>String(r[0])===mes);
  if(rows.length)return rows.map(r=>({
    requisito:String(r[1]),estado:String(r[2]),evidencia:String(r[3]||''),observaciones:String(r[4]||''),responsable:String(r[5]||'')
  }));
  return ['Estrategia mayorista documentada','Estrategia validada por región CMQ',
    'Clientes mayoristas y comportamiento identificados','Reporte evolutivo por PDV, mensual',
    'Seguimiento de desvíos y planes de acción','Topes por cliente y acción, control mensual',
    'Autorización regional para excedentes'].map(requisito=>({requisito,estado:'Pendiente',evidencia:'',observaciones:'',responsable:''}));
}
function cerrado_(mes){return rows_('CIERRES').some(r=>String(r[0])===mes);}
function cerrarMes(f){
  f=f||{};const mes=validMonth_(f.mes);
  if(mes===monthNow_()&&!f.confirmarMesAbierto)throw Error('Mes todavía abierto. Confirmá el cierre anticipado explícitamente.');
  if(!db_().getSheetByName(saleSheet_(mes)))throw Error('Primero importá las ventas.');
  const sinAcciones=!db_().getSheetByName(catSheet_('A',mes));
  if(cerrado_(mes))throw Error('Ese mes ya fue cerrado.');
  writeSheet_('CIERRES',MAY.H.CIERRES,[[mes,new Date(),usuario_(),texto_(f.observaciones,1000)+(sinAcciones?' | Sin snapshot de acciones en este mes':'')]],false);
  log_('CIERRE',mes,'MANUAL',0,sinAcciones?'Cierre de ventas sin acciones históricas':'Cierre preservado, ventas y acciones bloqueadas');
  return {ok:true,mes};
}
function getComplementos(mes){
  return {planes:listarPlanes(mes),extensiones:listarExtensiones(mes),
    auditoria:listarAuditoria(mes),topes:listarTopes(mes),cerrado:cerrado_(mes),estrategia:getEstrategia(),nivel:nivelAuditoria_(mes)};
}
function getEstrategia(){
  const r=rows_('ESTRATEGIA').slice(-1)[0];
  return r?{version:String(r[0]),objetivo:String(r[1]),identificacion:String(r[2]),
    seguimiento:String(r[3]),mix:String(r[4]),topes:String(r[5]),
    validacion:String(r[6]),validadoPor:String(r[7]),fecha:String(r[8]||'')}:{};
}
function nivelAuditoria_(mes){
  const vals=listarAuditoria(mes);
  const has=(name)=>vals.some(x=>x.requisito===name&&x.estado==='Cumplido'&&String(x.evidencia||'').trim());
  const estrategia=getEstrategia();
  const region=/VALIDAD/i.test(norm_(estrategia.validacion))&&Boolean(String(estrategia.validadoPor||'').trim())&&Boolean(String(estrategia.fecha||'').trim());
  const n1=[
    'Estrategia mayorista documentada','Estrategia validada por región CMQ',
    'Clientes mayoristas y comportamiento identificados','Reporte evolutivo por PDV, mensual',
    'Seguimiento de desvíos y planes de acción'
  ];
  const n2=['Topes por cliente y acción, control mensual','Autorización regional para excedentes'];
  const ok1=n1.every(has)&&region,ok2=ok1&&n2.every(has);
  return {nivel:ok2?2:ok1?1:0,porcentaje:ok2?100:ok1?33:0,puntos:ok2?70:ok1?23.1:0,
    pendientes:[...n1,...n2].filter(x=>!has(x)),validacionRegional:region,
    leyenda:'Estimación interna según evidencia declarada. La calificación la decide el auditor CMQ.'};
}
