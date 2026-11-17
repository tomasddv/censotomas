/**
 * Pruebas locales de reglas puras: node test_local.js
 * No ejecuta operaciones sobre el Google Drive del usuario.
 */
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const code=fs.readFileSync(__dirname+'/Code.gs','utf8');
const html=fs.readFileSync(__dirname+'/Index.html','utf8');
const js=html.match(/<script>([\s\S]*?)<\/script>/);
assert(js,'El HTML debe incluir código de cliente');
new vm.Script(js[1],{filename:'Index.html'});
const browser=vm.createContext({window:{addEventListener(){}},console,Date,Set,Map,Math,String,Number,isFinite,Error,RegExp});
vm.runInContext(js[1],browser,{filename:'Index.html'});
assert.throws(()=>vm.runInContext('validarEstado(null)',browser),/diagnóstico inicial/);
assert.throws(()=>vm.runInContext('validarEstado({})',browser),/diagnóstico inicial/);
assert.strictEqual(vm.runInContext('validarEstado({ok:true,mesesVentas:["2026-11"],mesActual:"2026-11"}).mesDefault',browser),'2026-11');
assert.strictEqual(vm.runInContext('validarEstado({ok:true,mesesVentas:["2026-11"],mesActual:"2026-11"}).meses[0]',browser),'2026-11');
assert.deepStrictEqual(JSON.parse(vm.runInContext("JSON.stringify(mesesEnVentana('2026-10'))",browser)),['2026-08','2026-09','2026-10']);
assert.deepStrictEqual(JSON.parse(vm.runInContext("JSON.stringify(mesesEnVentana('2026-01'))",browser)),['2025-11','2025-12','2026-01']);
assert.strictEqual(vm.runInContext("mesesParaFiltro({meses:['2026-11'],mesActual:'2026-11',mesDefault:'2026-11'}).includes('2026-10')",browser),true);
const ctx=vm.createContext({console,Date,Set,Map,Math,String,Number,isFinite,Error,RegExp});
vm.runInContext(code,ctx,{filename:'Code.gs'});
const run=expr=>vm.runInContext(expr,ctx);
assert.strictEqual(run("month_('2-nov-26')"),'2026-11');
assert.strictEqual(run("month_('14-nov-26')"),'2026-11');
assert.strictEqual(run("month_('31/10/2026')"),'2026-10');
assert.strictEqual(run("code_('(0002941)')"),'2941');
assert.strictEqual(run("num_('1.234,56')"),1234.56);
assert.strictEqual(run("num_('0,0568')"),.0568);
assert.strictEqual(run("prevMonth_('2026-01')"),'2025-12');
assert.deepStrictEqual(JSON.parse(run("JSON.stringify(mesesVentanaMovil_('2026-11',3))")),['2026-09','2026-10','2026-11']);
assert.deepStrictEqual(JSON.parse(run("JSON.stringify(mesesVentanaMovil_('2026-10',3))")),['2026-08','2026-09','2026-10']);
assert.deepStrictEqual(JSON.parse(run("JSON.stringify(mesesVentanaMovil_('2026-01',3))")),['2025-11','2025-12','2026-01']);
assert.strictEqual(run("coincideNombreHistorico_('venta agosto.txt','2026-08')"),true);
assert.strictEqual(run("coincideNombreHistorico_('venta septiembre.txt','2026-09')"),true);
assert.strictEqual(run("coincideNombreHistorico_('ventadiaria octubre.txt','2026-10')"),true);
assert.strictEqual(run("coincideNombreHistorico_('venta septiembre 2025.txt','2026-09')"),false);
assert.strictEqual(run("coincideNombreHistorico_('venta agosto bultos.txt','2026-08')"),false);
assert.strictEqual(run("coincideNombreBultosHistorico_('ventadiaria bultos noviembre.txt','2026-11')"),true);
assert.strictEqual(run("coincideNombreBultosHistorico_('ventadiaria bultos diciembre 2026.txt','2026-12')"),true);
assert.strictEqual(run("coincideNombreBultosHistorico_('ventadiaria bultos noviembre 2025.txt','2026-11')"),false);
assert.strictEqual(run("coincideNombreBultosHistorico_('ventadiaria bultos anual.txt','2026-10')"),false);
const monthsAnnual=JSON.parse(run('JSON.stringify(mesesArchivoBultosAnual_())'));
assert.strictEqual(monthsAnnual.length,18);
assert.strictEqual(monthsAnnual[0],'2025-05');
assert.strictEqual(monthsAnnual.at(-1),'2026-10');
assert.strictEqual(run("normalGroupMatch_('CORONA 710',{marca:'CORONA',calibre:'BOTELLA 710 CC',producto:'CORONA OW X12 710'},new Map())"),true);
assert.strictEqual(run("normalGroupMatch_('CORONA PORRON',{marca:'CORONA',calibre:'BOTELLA 330 CC',producto:'CORONA PORRON'},new Map())"),true);
assert.strictEqual(run("normalGroupMatch_('GP-100328365',{marca:'CORONA',calibre:'BOTELLA 710 CC',producto:'CORONA'},new Map())"),null);

// Las tres señales usan únicamente meses completos anteriores al filtro.
// Se comprueban también la ausencia de meses y la exclusión de otras unidades de negocio.
ctx.rows_=()=>[];
ctx.testHab=[{hl:1,subcanal:'Autoservicio',mayoristaERP:false,comportamiento:false}];
assert.strictEqual(run("identificarComportamiento_(testHab)[0].tipo"),'Comportamiento habitual');
assert.strictEqual(run("identificarComportamiento_(testHab)[0].identificado"),false);
ctx.testERP=[{hl:1,subcanal:'Autoservicio',mayoristaERP:false,comportamiento:true}];
assert.strictEqual(run("identificarComportamiento_(testERP)[0].tipo"),'ERP sin alerta CM');
assert.strictEqual(run("identificarComportamiento_(testERP)[0].identificado"),false);
assert.strictEqual(run("clasificarAlertaCM_(true,true,false,false)"),'Alerta sostenida CM');
assert.strictEqual(run("clasificarAlertaCM_(true,true,true,false)"),'Alerta sostenida CM/ERP');
assert.strictEqual(run("clasificarAlertaCM_(true,false,true,false)"),'Alerta puntual CM/ERP');
assert.strictEqual(run("clasificarAlertaCM_(true,false,false,false)"),'Alerta puntual CM');
assert.strictEqual(run("clasificarAlertaCM_(true,false,true,true)"),'Alerta mensual CM/ERP');
assert.strictEqual(run("clasificarAlertaCM_(false,false,true,false)"),'ERP sin alerta CM');
ctx.testClients=new Map(Array.from({length:20},(_,i)=>[String(i+1),{subcanal:'Autoservicio'}]));
ctx.testSeries=Object.fromEntries(['2026-08','2026-09','2026-10'].map(m=>[
  m,new Map(Array.from({length:20},(_,i)=>[String(i+1),i+1]))
]));
assert.strictEqual(run("calcularComportamientoTrimestral_('2026-10',testClients,m=>testSeries[m]||null).completo"),true);
assert.deepStrictEqual(JSON.parse(run("JSON.stringify(calcularComportamientoTrimestral_('2026-10',testClients,m=>testSeries[m]||null).periodos)")),['2026-08','2026-09','2026-10']);
assert.strictEqual(run("calcularComportamientoTrimestral_('2026-10',testClients,m=>testSeries[m]||null).porCliente.get('20').p95HL"),19);
assert.strictEqual(run("calcularComportamientoTrimestral_('2026-10',testClients,m=>testSeries[m]||null).porCliente.get('20').medianaHL"),10.5);
assert.strictEqual(run("calcularComportamientoTrimestral_('2026-10',testClients,m=>testSeries[m]||null).porCliente.get('20').mesesAltos"),3);
assert.strictEqual(run("calcularComportamientoTrimestral_('2026-10',testClients,m=>testSeries[m]||null).porCliente.get('20').sostenido"),true);
assert.strictEqual(run("calcularComportamientoTrimestral_('2026-10',testClients,m=>testSeries[m]||null).porCliente.get('2').alertaP95"),false);
assert.strictEqual(run("calcularComportamientoTrimestral_('2026-10',testClients,m=>m==='2026-09'?null:testSeries[m]).completo"),false);
assert.strictEqual(run("calcularComportamientoTrimestral_('2026-10',testClients,m=>m==='2026-09'?null:testSeries[m]).porCliente.size"),0);
ctx.testSales=[['2026-08','0001','SKU','Prod','Marca','Cal','Cervezas CMQ',12],['2026-08','1','SKU2','Prod','Marca','Cal','CERVEZAS CMQ',3],['2026-08','2','SKU3','Prod','Marca','Cal','AGUAS',500]];
assert.strictEqual(run("calcularVolumenMensualCliente_(testSales).get('1')"),15);
assert.strictEqual(run("calcularVolumenMensualCliente_(testSales).has('2')"),false);

// Integración: el ERP aislado NO ingresa al listado ni a los KPI de alertas CM.
ctx.testClientBase=new Map(Array.from({length:20},(_,i)=>[
  String(i+1),{codigo:String(i+1),razon:'Cliente '+(i+1),fantasia:'',subcanal:'Autoservicio',
    mayoristaERP:i===0||i===19,comportamiento:false}
]));
ctx.testVentaTablero=Array.from({length:20},(_,i)=>({mes:'2026-10',cliente:String(i+1),sku:'SKU'+i,
  negocio:'CERVEZAS CMQ',producto:'Producto',marca:'MARCA',calibre:'710',hl:i+1,bultos:null,fact:100}));
ctx.testPerfiles=new Map([
  ['19',{promedioHL:19,medianaHL:10.5,p95HL:19,multiplicador:19/10.5,mesesConCompra:3,
    mesesAltos:1,volumenes:[19,19,19],alertaP95:true,sostenido:false,compradoresSubcanal:20}],
  ['20',{promedioHL:20,medianaHL:10.5,p95HL:19,multiplicador:20/10.5,mesesConCompra:3,
    mesesAltos:3,volumenes:[20,20,20],alertaP95:true,sostenido:true,compradoresSubcanal:20}]
]);
ctx.clientesMap_=()=>ctx.testClientBase;
ctx.ventasMes_=()=>ctx.testVentaTablero;
ctx.auxMap_=()=>new Map();
ctx.calcularComportamientoTrimestral_=()=>({completo:true,periodos:['2026-08','2026-09','2026-10'],
  faltantes:[],criterio:'prueba',porCliente:ctx.testPerfiles});
ctx.resumenMensual_=()=>null;
ctx.periodosDisponibles_=()=>['2026-10'];
ctx.accionesMes_=()=>[];
ctx.monthNow_=()=> '2026-11';
ctx.db_=()=>({getSheetByName:()=>null});
const tableroIntegrado=run("getTablero('2026-10')");
assert.strictEqual(tableroIntegrado.kpis.comportamiento,2);
assert.strictEqual(tableroIntegrado.kpis.alertasERP,1);
assert.strictEqual(tableroIntegrado.kpis.alertasSostenidas,1);
assert.strictEqual(tableroIntegrado.kpis.alertasPuntuales,1);
assert.strictEqual(tableroIntegrado.clientes.find(c=>c.codigo==='1').tipo,'ERP sin alerta CM');
assert.strictEqual(tableroIntegrado.clientes.find(c=>c.codigo==='20').tipo,'Alerta sostenida CM/ERP');
assert.strictEqual(tableroIntegrado.clientes.find(c=>c.codigo==='19').tipo,'Alerta puntual CM');

// El cargador automático conserva HL ya importados hasta que llega el par definitivo.
ctx.testExiste=true;
ctx.db_=()=>({getSheetByName:()=>ctx.testExiste?{getLastRow:()=>50}:null});
ctx.cerrado_=()=>false;
ctx.monthNow_=()=> '2026-11';
ctx.fuenteVentasMes_=()=>ctx.testExiste?{hl:'archivo-prueba',bultos:'',tieneBultos:false}:null;
ctx.buscarVentasHistoricasAuto_=()=>({id:'archivo-prueba',nombre:'venta agosto.txt'});
ctx.buscarBultosHistoricosAuto_=()=>null;
const conciliarReal=ctx.completarBultosMesDesdeAnual_;
ctx.completarBultosMesDesdeAnual_=()=>null;
ctx.importarHistorico=(f)=>({mes:f.mes,filasResumen:18});
assert.strictEqual(run("importarHistoricoAutomatico('2026-08').existente"),true);
ctx.buscarBultosHistoricosAuto_=()=>({id:'bultos-agosto',nombre:'ventadiaria bultos agosto.txt'});
const reemplazoPar=run("importarHistoricoAutomatico('2026-08')");
assert.strictEqual(reemplazoPar.actualizado,true);
assert.strictEqual(reemplazoPar.bultosReales,true);
ctx.buscarBultosHistoricosAuto_=()=>null;
ctx.testExiste=false;
assert.strictEqual(run("importarHistoricoAutomatico('2026-08').importado"),true);
ctx.buscarVentasHistoricasAuto_=()=>null;
assert.strictEqual(run("importarHistoricoAutomatico('2026-08').ok"),false);

// Agregación del TXT anual: bultos reales en el mismo grano, sin convertir HL.
const ventaB=(fecha,cliente,bultos,neto,negocio='CERVEZAS CMQ')=>{
  const cols=Array(47).fill('');
  cols[2]=fecha;cols[4]=cliente;cols[17]='2218';cols[35]=negocio;
  cols[40]=bultos;cols[42]=neto;
  return cols.join('\t');
};
ctx.anualLineas=[ventaB('01/10/2026','00042','8,5','100,00'),
  ventaB('02/10/2026','42','2','50'),ventaB('01/04/2025','42','9','100')];
const l=run('resumirLineasBultosAnual_(anualLineas)');
assert.strictEqual(l.registros,2);
assert.strictEqual(l.omitidos,1);
assert.deepStrictEqual(Array.from(l.buckets.get('2026-10').get('2026-10|42|2218|CERVEZAS CMQ')),[10.5,150]);

// Conciliación exacta con deduplicación por lote ante interrupciones del trigger.
ctx.completarBultosMesDesdeAnual_=conciliarReal;
const ventaConHL=['2026-10','42','2218','Producto','Marca','Calibre','CERVEZAS CMQ',1,null,150,2,'hl',''];
ctx.anualRows=[['0','2026-10|42|2218|CERVEZAS CMQ',8.5,100],
  ['0','2026-10|42|2218|CERVEZAS CMQ',8.5,100],
  ['100','2026-10|42|2218|CERVEZAS CMQ',2,50]];
ctx.estadoBultosAnual_=()=>({estado:'terminado',id:'bultos-anual'});
ctx.rows_=(name)=>name==='B_2026_10'?ctx.anualRows: name==='V_2026_10'?[ventaConHL]:[];
ctx.fuenteVentasMes_=()=>({hl:'hl',bultos:'',tieneBultos:false});
ctx.cerrado_=()=>false;
ctx.escrituras=[];
const fakeSaleSheet={getLastRow:()=>2,getRange:(fila,col)=>({setValues:arr=>ctx.escrituras.push({fila,col,arr})})};
ctx.db_=()=>({getSheetByName:name=>name==='B_2026_10'?{getLastRow:()=>4}:
  name==='V_2026_10'?fakeSaleSheet:null});
ctx.log_=()=>{};
const conciliado=run("completarBultosMesDesdeAnual_('2026-10')");
assert.strictEqual(conciliado.actualizado,true);
assert.strictEqual(ctx.escrituras.length,2);
assert.strictEqual(ctx.escrituras[0].arr[0][0],10.5);
assert.strictEqual(ctx.escrituras[1].arr[0][0],'bultos-anual');
ctx.escrituras=[];
ctx.anualRows[2][3]=70;
assert.match(run("completarBultosMesDesdeAnual_('2026-10')").motivo,/importe/);
assert.strictEqual(ctx.escrituras.length,0,'No modificar ventas si el anual no concilia');
ctx.cerrado_=()=>true;
assert.match(run("completarBultosMesDesdeAnual_('2026-10')").motivo,/cerrado/);

// Descarga por byte-range: valida cabecera, tamaño exacto, cursor y estado del proceso.
const cabecera=Array(47).fill('col');
cabecera[4]='COD. CLIENTE';cabecera[17]='CODIGO';cabecera[40]='CANTIDADES TOTALES';
ctx.rangeTxt=cabecera.join('\t')+'\r\n'+ventaB('01/10/2026','42','3','90')+'\r\n';
ctx.testRange={offset:0,bytes:Buffer.byteLength(ctx.rangeTxt,'latin1'),restante:'',estado:'leyendo',registros:0,omitidos:0};
ctx.rangeWrites=[];
ctx.ScriptApp={getOAuthToken:()=> 'token-de-prueba'};
ctx.Utilities={newBlob:bytes=>({getDataAsString:charset=>{
  assert.strictEqual(charset,'Windows-1252');return Buffer.from(bytes).toString('latin1');
}})};
ctx.UrlFetchApp={fetch:(url,opciones)=>{
  assert.match(url,/alt=media/);
  assert.strictEqual(opciones.headers.Range,'bytes=0-'+(ctx.testRange.bytes-1));
  return {getResponseCode:()=>206,getContent:()=>Array.from(Buffer.from(ctx.rangeTxt,'latin1'))};
}};
ctx.guardarLoteBultos_=(mes,lote,map)=>ctx.rangeWrites.push({mes,lote,map});
run('procesarLoteBultosAnual_(testRange)');
assert.strictEqual(ctx.testRange.offset,ctx.testRange.bytes);
assert.strictEqual(ctx.testRange.estado,'aplicando');
assert.strictEqual(ctx.testRange.registros,1);
assert.strictEqual(ctx.rangeWrites.length,1);
assert.strictEqual(ctx.rangeWrites[0].map.get('2026-10|42|2218|CERVEZAS CMQ')[0],3);

const hlPath=__dirname+'/../ventadiaria_hl_check.txt';
const bPath=__dirname+'/../ventadiaria_bultos_check.txt';
if(fs.existsSync(hlPath)&&fs.existsSync(bPath)){
  const parse=(path,id)=>{
    const lines=fs.readFileSync(path,'latin1').replace(/\r/g,'').split('\n');
    const head=lines.shift().split('\t');
    return {id,head,rows:lines.filter(Boolean)};
  };
  ctx.testHL=parse(hlPath,'hl'),ctx.testB=parse(bPath,'bultos');
  const summary=run("summarizeSales_(testHL,testB)");
  assert.strictEqual(summary.checked,18035);
  assert.strictEqual(summary.months[0],'2026-11');
  assert.strictEqual(summary.months.length,1);
  assert.strictEqual(summary.negative,102);
  assert(summary.vals.some(x=>x[7]>0&&x[8]>0),'Debe agregar HL y bultos por cliente-SKU');
  console.log('Prueba ventas reales: '+summary.checked+' registros · '+summary.vals.length+' agregados · '+summary.negative+' negativos');
}else console.log('Sin archivos de prueba originales: se comprobaron las reglas básicas.');
console.log('OK · Código servidor, HTML y reglas básicas');
