from pathlib import Path
p=Path('dist/network-views.js');s=p.read_text(encoding='utf8');s="import {drawEdgeMesh,drawWellMesh} from './scene3d.js';\n"+s
start=s.index('export function drawEdge3d(')
s=s[:start]+'''export function drawEdge3d(p,e,res,camera={}){return drawEdgeMesh(p,e,res,camera)}
export function drawWell(p,w,camera={},plan=false){return drawWellMesh(p,w,camera,plan)}
'''
# Make soil boundaries legible in planar views as well.
s=s.replace("(soil?.color||'#ccc')+'aa'", "(soil?.color||'#ccc')+'dd'").replace("(soil?.color||'#ccc')+'77'", "(soil?.color||'#ccc')+'bb'")
p.write_text(s,encoding='utf8')
p=Path('dist/index.html');s=p.read_text(encoding='utf8')
s=s.replace('<button id="soil-catalog" class="button">Грунты</button>', '<button id="edit-layers" class="button layer-button">Слои грунта</button><button id="soil-catalog" class="button">Справочник грунтов</button>')
s=s.replace('<div id="context-actions" class="context-actions"></div>','<div id="context-actions" class="context-actions"></div><div class="display-options"><label><input id="show-soils" type="checkbox" checked> Показывать слои грунта</label><button id="focus-layers">Настроить слои ↗</button></div>')
s=s.replace('<label id="angle-control" hidden>Ракурс <input id="angle" type="range" min="-1" max="1" step="0.02" value="0.4"></label>', '<div id="orbit-controls" class="orbit-controls" hidden><label>Поворот <input id="angle" type="range" min="-180" max="180" step="1" value="-35"><output id="yaw-value">−35°</output></label><label>Наклон <input id="pitch" type="range" min="10" max="80" step="1" value="30"><output id="pitch-value">30°</output></label><button id="reset-camera" title="Вернуть исходный ракурс">↺ Сбросить</button></div>')
s=s.replace('<div id="volume-cards"','<section id="soil-summary" class="panel soil-summary"></section><div id="volume-cards"',1)
s=s.replace('<div id="inspector"></div>','<nav id="inspector-tabs" class="inspector-tabs" aria-label="Настройка объекта"></nav><div id="inspector"></div>')
p.write_text(s,encoding='utf8')
p=Path('dist/network-app.js');s=p.read_text(encoding='utf8')
s=s.replace("ratio:.5,angle:.4,zoom:1", "ratio:.5,yaw:-35,pitch:30,showSoils:true,inspectorTab:'geometry',zoom:1")
s=s.replace("$('angle-control')", "$('orbit-controls')")
s=s.replace("drawWell(p,w,state.angle,state.view==='plan')", "drawWell(p,w,{yaw:state.yaw,pitch:state.pitch,showSoils:state.showSoils},state.view==='plan')")
s=s.replace("drawEdge3d(p,e,res,state.angle)", "drawEdge3d(p,e,res,{yaw:state.yaw,pitch:state.pitch,showSoils:state.showSoils})")
needle=" $('canvas-legend').innerHTML="
addition=""" $('angle').value=String(state.yaw);$('pitch').value=String(state.pitch);$('yaw-value').textContent=Math.round(state.yaw)+'°';$('pitch-value').textContent=Math.round(state.pitch)+'°';$('show-soils').checked=state.showSoils;
 $('network-scene').classList.toggle('orbit-scene',state.view==='3d');
"""
s=s.replace(needle,addition+needle,1)
s=s.replace("state.view==='section'||state.view==='profile'?p.soils.map", "state.scale!=='network'&&state.showSoils?p.soils.map")
s=s.replace("Наружная геометрия рабочей части, основания и горловины. Оранжевым показаны подключения труб.","Вращайте мышью или ползунками. Цветные полосы — грунты котлована; оранжевым показаны подключения.")
s=s.replace("Продольное направление выпрямлено и сокращено для наглядности. Реальные повороты видны на общем плане.","Вращение мышью: влево/вправо — поворот, вверх/вниз — наклон. Цветные откосы показывают слои грунта. Продольная длина условная.")
s=s.replace("$('canvas-caption').textContent=caption;", "$('canvas-caption').textContent=caption;renderSoilSummary();")
# Soil editing gets its own visible tab rather than being buried below geometry.
needle="function renderInspector(){\n"
replacement="""function renderInspector(){
 const isWell=state.scale==='object'&&state.object==='well',target=isWell?well():edge(),count=target?.layers.length||0;
 $('inspector-tabs').innerHTML=`<button data-action="inspector-tab" data-id="geometry" class="${state.inspectorTab==='geometry'?'active':''}">Геометрия</button><button data-action="inspector-tab" data-id="soils" class="${state.inspectorTab==='soils'?'active':''}">Слои грунта <span>${count}</span></button>`;
 if(state.scale!=='network'&&state.inspectorTab==='soils'&&target){
  $('inspector-title').textContent=target.name;$('inspector-kind').textContent='СЛОИ ГРУНТА';
  const path=isWell?'wells.'+wi()+'.layers':'edges.'+ei()+'.layers';
  $('inspector').innerHTML='<p class="inspector-intro">Слои идут сверху вниз. Меняйте глубины границ — модель и объёмы обновляются автоматически.</p>'+layersEditor(target.layers,path,isWell)+(isWell?'':'<div class="soil-view-actions"><button data-action="view" data-id="section">Показать сечение</button><button data-action="view" data-id="profile">Показать профиль</button></div>');return;
 }
"""
assert needle in s;s=s.replace(needle,replacement,1)
# Also keep a direct access button at the bottom of geometry for existing users.
s=s.replace("+block('Грунты котлована',layersEditor(w.layers,base+'.layers',true),false)","+'<button class=\"inline-add layer-button\" data-action=\"edit-layers\">Настроить слои грунта ↗</button>'")
s=s.replace("+block('Грунты по длине участка',layersEditor(e.layers,base+'.layers'),false)","+'<button class=\"inline-add layer-button\" data-action=\"edit-layers\">Настроить слои грунта ↗</button>'")
s=s.replace("function action(ev){", """function openLayers(){
 if(state.scale==='network'){if(edge()){state.scale='edge';state.object='pipe';state.view='section';const s=edge().sections[state.section]||edge().sections[0];state.ratio=(s.a+s.b)/2}else if(well()){state.scale='object';state.object='well';state.view='3d'}else{notify('Добавьте участок или колодец, чтобы задать слои грунта.');return}}
 state.inspectorTab='soils';state.showSoils=true;render();$('inspector').scrollTop=0;
}
function renderSoilSummary(){
 const selected=selectedResult(),r=selected.r,valid=r&&!selected.errors.length;
 const soils=p.soils.filter(s=>(r?.soils?.[s.id]||0)>1e-8);
 $('soil-summary').innerHTML=`<div class="soil-summary-heading"><h2>Слои грунта · ${esc(selected.label||'проект')}</h2><button data-action="edit-layers">Настроить слои ↗</button></div><div class="soil-cards">${(soils.length?soils:p.soils).map(s=>`<button data-action="edit-layers" class="soil-card"><i style="background:${s.color}"></i><span>${esc(s.name)}<small>${esc(s.group)} группа разработки</small></span><strong>${valid?fmt(r.soils?.[s.id]||0,3):'—'} м³</strong></button>`).join('')}</div><p>${state.scale==='network'?'На общем плане показана сеть. Для границ слоёв откройте участок — «Сечение» или «Объём».':'Цвета и штриховка на схеме соответствуют грунтам. Глубины границ доступны во вкладке «Слои грунта» справа.'}</p>`;
}
function action(ev){""")
s=s.replace(" if(a==='network')return", " if(a==='edit-layers')return openLayers();if(a==='inspector-tab'){if(id==='soils')return openLayers();state.inspectorTab='geometry';renderInspector();$('inspector').scrollTop=0;return}\n if(a==='network')return",1)
s=s.replace("['tree','inspector','view-buttons','context-actions','breadcrumbs']", "['tree','inspector','inspector-tabs','soil-summary','view-buttons','context-actions','breadcrumbs']")
s=s.replace("$('angle').oninput=e=>{state.angle=Number(e.target.value);renderCanvas()}", "$('angle').oninput=e=>{state.yaw=Number(e.target.value);renderCanvas()}")
needle="$('project-name').oninput="
s=s.replace(needle,"""$('pitch').oninput=e=>{state.pitch=Number(e.target.value);renderCanvas()};
$('show-soils').onchange=e=>{state.showSoils=e.target.checked;renderCanvas()};
$('edit-layers').onclick=openLayers;$('focus-layers').onclick=openLayers;
$('reset-camera').onclick=()=>{state.yaw=-35;state.pitch=30;renderCanvas()};
"""+needle,1)
# Preserve the node-drag behaviour on the plan, use genuine orbit drag in 3D.
start=s.index("$('network-scene').onpointerdown=");end=s.index("render();if(loadMessage)",start)
s=s[:start]+"""$('network-scene').onpointerdown=ev=>{
 const node=ev.target.closest('[data-well]');
 if(state.scale==='network'&&node){const w=p.wells.find(w=>w.id===node.dataset.well);drag={kind:'node',id:w.id,x:ev.clientX,y:ev.clientY,moved:false,frame:planFrame}}
 else if(state.view==='3d')drag={kind:'camera',x:ev.clientX,y:ev.clientY,yaw:state.yaw,pitch:state.pitch,moved:false};
 if(drag)$('network-scene').setPointerCapture(ev.pointerId);
};
$('network-scene').onpointermove=ev=>{
 if(!drag)return;if(Math.hypot(ev.clientX-drag.x,ev.clientY-drag.y)<3&&!drag.moved)return;drag.moved=true;
 if(drag.kind==='camera'){state.yaw=((drag.yaw+(ev.clientX-drag.x)*.45+540)%360)-180;state.pitch=Math.max(10,Math.min(80,drag.pitch-(ev.clientY-drag.y)*.35));renderCanvas();return}
 if(!planTransform)return;const [x,y]=planTransform(svgPoint(ev)),w=p.wells.find(w=>w.id===drag.id);w.x=Math.round(x*100)/100;w.y=Math.round(y*100)/100;calculate();renderCanvas();renderResults();
};
$('network-scene').onpointerup=ev=>{
 if(drag){const d=drag;drag=null;if(d.kind==='node'){persist();if(d.moved)render();else showWell(d.id);return}if(d.moved)return}
 const node=ev.target.closest('[data-edge],[data-pipe]');if(node){if(node.dataset.pipe){state.edgeId=node.dataset.pipe;showPipe()}else showEdge(node.dataset.edge)}
};
$('network-scene').onpointercancel=()=>{drag=null;persist();render()};
"""+s[end:]
p.write_text(s,encoding='utf8')
