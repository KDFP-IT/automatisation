from pathlib import Path
p=Path('dist/plan-selection.js')
p.write_text('''import {nodeAngle,referencePipeBearing,connectedRotationEdge,normalizeAngle} from './node-geometry.js';
export const selectionKey=(kind,id)=>kind+':'+id;
export function selectionNodes(p,keys){
 const nodes=new Set();for(const key of keys){const cut=key.indexOf(':'),kind=key.slice(0,cut),id=key.slice(cut+1);if(kind==='well'&&p.wells.some(w=>w.id===id))nodes.add(id);if(kind==='edge'){const e=p.edges.find(e=>e.id===id);if(e){nodes.add(e.from.well);nodes.add(e.to.well)}}}return nodes;
}
// Apply absolute displacement from a drag snapshot, never accumulate rounding or change levels.
export function translateSelection(p,before,keys,dx,dy){
 if(!Number.isFinite(dx)||!Number.isFinite(dy))throw Error('Задайте смещение группы.');
 const nodes=selectionNodes(before,keys),edges=new Set(keys.filter(v=>v.startsWith('edge:')).map(v=>v.slice(5)));
 for(const w of p.wells){const source=before.wells.find(v=>v.id===w.id);if(source&&nodes.has(w.id)){w.x=source.x+dx;w.y=source.y+dy}}
 for(const e of p.edges){const source=before.edges.find(v=>v.id===e.id);if(!source)continue;if(edges.has(e.id)||nodes.has(e.from.well)&&nodes.has(e.to.well))for(const v of e.waypoints){const old=source.waypoints.find(q=>q.id===v.id);if(old){v.x=old.x+dx;v.y=old.y+dy}}}
 for(const w of p.wells.filter(w=>nodes.has(w.id)&&w.rotationMode==='pipe')){const old=before.wells.find(v=>v.id===w.id),ref=connectedRotationEdge(p,w);if(ref)w.rotation=normalizeAngle(nodeAngle(before,old)-(w.zeroAngle||0)-referencePipeBearing(p,ref,w.id))}
 return p.edges.filter(e=>nodes.has(e.from.well)!==nodes.has(e.to.well)).map(e=>e.name);
}
export function selectionInBox(p,a,b){
 const x0=Math.min(a[0],b[0]),x1=Math.max(a[0],b[0]),y0=Math.min(a[1],b[1]),y1=Math.max(a[1],b[1]),inside=v=>v.x>=x0&&v.x<=x1&&v.y>=y0&&v.y<=y1;
 const nodes=new Set(p.wells.filter(inside).map(v=>v.id));return [...nodes].map(id=>selectionKey('well',id)).concat(p.edges.filter(e=>nodes.has(e.from.well)&&nodes.has(e.to.well)&&e.waypoints.every(inside)).map(e=>selectionKey('edge',e.id)));
}
''',encoding='utf-8')
f=Path('dist/network-app.js');s=f.read_text(encoding='utf-8')
s="import {selectionKey,selectionNodes,translateSelection,selectionInBox} from './plan-selection.js';\n"+s
s=s.replace("issueFocus:null,resultsScope:","selection:[],groupMode:false,issueFocus:null,resultsScope:")
s=s.replace("function normalizeSelection(){","function normalizeSelection(){state.selection=state.selection.filter(k=>k.startsWith('well:')?p.wells.some(w=>'well:'+w.id===k):p.edges.some(e=>'edge:'+e.id===k));")
s=s.replace("function renderBuilderState(){","function renderBuilderState(){\n if($('group-select')){$('group-select').classList.toggle('active',state.groupMode);$('group-select').setAttribute('aria-pressed',String(state.groupMode));$('selection-count').textContent=state.selection.length?'Выбрано: '+state.selection.length:'';$('clear-selection').hidden=!state.selection.length}")
s=s.replace("'Выберите элемент · фон — перемещение плана'","(state.selection.length?'Тяните выбранный объект — перенос группы · Ctrl/Shift + щелчок — выбор':'Ctrl/Shift + щелчок — несколько объектов · Shift + фон — рамка')")
s=s.replace("function initializeConstructor(){",'''function initializeConstructor(){
 const group=document.createElement('div');group.className='group-selection-tools';group.innerHTML='<button id="group-select" aria-pressed="false" title="Выбор нескольких объектов щелчками и рамкой">▧ Группа</button><span id="selection-count" aria-live="polite"></span><button id="clear-selection" hidden title="Снять выделение">×</button>';$('tool-select').parentElement.after(group);
 $('group-select').onclick=()=>{state.groupMode=!state.groupMode;state.tool='select';state.view='plan';render()};$('clear-selection').onclick=()=>{state.selection=[];renderCanvas();renderBuilderState()};
''')
s=s.replace("function showEdge(id){flushEdit();","function showEdge(id){state.selection=[];flushEdit();")
s=s.replace("function showWell(id){flushEdit();","function showWell(id){state.selection=[];flushEdit();")
s=s.replace("const plan=drawPlan(p,result,","const plan=drawPlan(p,result,") # group overlay below avoids model renderer changes
s=s.replace("html=plan.html;lastPlanHTML=html;",'''html=plan.html;const groupNodes=selectionNodes(p,state.selection);for(const e of p.edges.filter(e=>state.selection.includes(selectionKey('edge',e.id)))){const pts=[p.wells.find(w=>w.id===e.from.well),...e.waypoints,p.wells.find(w=>w.id===e.to.well)].map(v=>plan.project(v.x,v.y).join(',')).join(' ');html+=`<polyline points="${pts}" fill="none" stroke="#1689b9" stroke-width="3" stroke-dasharray="7 4" pointer-events="none"/>`}for(const w of p.wells.filter(w=>groupNodes.has(w.id))){const q=plan.project(w.x,w.y);html+=`<circle cx="${q[0]}" cy="${q[1]}" r="22" fill="none" stroke="#1689b9" stroke-width="2.5" stroke-dasharray="5 3" pointer-events="none"/>`}lastPlanHTML=html;''')
s=s.replace("block('Углы выхода',directions,false)","block('Подключение трубы · 90° к стене',directions,true)")
s=s.replace('Выберите стену для прямой трубы','Нажмите стену — труба встанет под 90°')
s=s.replace('</svg><p class="port-selection-note">Выбор стены выпрямит', '''</svg><div class="wall-buttons">${[0,1,2,3].map(i=>`<button data-action="choose-wall" data-well-id="${esc(w.id)}" data-edge-id="${esc(e.id)}" data-wall="${i}" aria-pressed="${port.wall===i&&port.valid}" class="${port.wall===i&&port.valid?'active':''}">Стена ${i+1}<small>90°</small></button>`).join('')}</div><p class="port-selection-note">Выбор стены выпрямит''')
s=s.replace("const rotation=ev.target.closest('[data-rotate-well],[data-zero-well]');",'''const hitNode=ev.target.closest('[data-well]'),hitEdge=ev.target.closest('[data-edge]'),key=hitNode?selectionKey('well',hitNode.dataset.well):hitEdge?selectionKey('edge',hitEdge.dataset.edge):null;
 if(!ev.target.closest('[data-waypoint]')&&(ev.ctrlKey||ev.metaKey||ev.shiftKey||state.groupMode||state.selection.length)){
  if(key){flushEdit();const toggle=ev.ctrlKey||ev.metaKey||ev.shiftKey||state.groupMode;if(toggle){state.selection=state.selection.includes(key)?state.selection.filter(v=>v!==key):[...state.selection,key]}else if(!state.selection.includes(key)&&!(hitNode&&selectionNodes(p,state.selection).has(hitNode.dataset.well)))state.selection=[key];
   drag={kind:'group',x:ev.clientX,y:ev.clientY,start:planTransform(svgPoint(ev)),keys:[...state.selection],before:clone(p),frame:planFrame,moved:false};renderCanvas();renderBuilderState();$('network-scene').setPointerCapture(ev.pointerId);return;
  }else if(ev.shiftKey||state.groupMode){flushEdit();drag={kind:'box',x:ev.clientX,y:ev.clientY,start:planTransform(svgPoint(ev)),base:(ev.ctrlKey||ev.metaKey||ev.shiftKey)?[...state.selection]:[],moved:false};$('network-scene').setPointerCapture(ev.pointerId);return}
 }
 if(hitEdge&&!hitNode&&!ev.target.closest('[data-waypoint]')){flushEdit();drag={kind:'group',x:ev.clientX,y:ev.clientY,start:planTransform(svgPoint(ev)),keys:[selectionKey('edge',hitEdge.dataset.edge)],singleEdge:hitEdge.dataset.edge,before:clone(p),frame:planFrame,moved:false};$('network-scene').setPointerCapture(ev.pointerId);return}
 const rotation=ev.target.closest('[data-rotate-well],[data-zero-well]');''')
s=s.replace("if(drag.kind==='camera'){",'''if(drag.kind==='box'){const end=planTransform(svgPoint(ev));state.selection=[...new Set([...drag.base,...selectionInBox(p,drag.start,end)])];renderCanvas();renderBuilderState();const a=planProject(...drag.start),b=svgPoint(ev);$('network-scene').insertAdjacentHTML('beforeend',`<rect x="${Math.min(a[0],b[0])}" y="${Math.min(a[1],b[1])}" width="${Math.abs(a[0]-b[0])}" height="${Math.abs(a[1]-b[1])}" fill="#1689b920" stroke="#1689b9" stroke-dasharray="5 3" pointer-events="none"/>`);return}
 if(drag.kind==='group'){const q=planTransform(svgPoint(ev));state.selection=drag.keys;translateSelection(p,drag.before,drag.keys,Math.round((q[0]-drag.start[0])*100)/100,Math.round((q[1]-drag.start[1])*100)/100);calculate({step:.4,crossSamples:32,preview:true});renderCanvas();renderResults();return}
 if(drag.kind==='camera'){''')
s=s.replace("drag=null;if(['rotate','zero']",'''drag=null;if(d.kind==='box'){renderCanvas();renderBuilderState();return}if(d.kind==='group'){if(d.moved){recordChange(d.before,'Перемещение группы');persist();render();const affected=p.edges.filter(e=>selectionNodes(p,d.keys).has(e.from.well)!==selectionNodes(p,d.keys).has(e.to.well));if(affected.length)notify('Группа перемещена. Проверьте соседние трубы: '+affected.map(e=>e.name).join(', '))}else if(d.singleEdge)showEdge(d.singleEdge);else{renderCanvas();renderBuilderState()}return}if(['rotate','zero']''')
s=s.replace("if(drag?.before){p=drag.before;drag=null;render();return}setTool('select');", "if(drag?.before){p=drag.before;drag=null;render();return}state.selection=[];state.groupMode=false;setTool('select');")
s=s.replace("state.issueFocus=null;state.edgeId=p.edges[0]?.id;", "state.selection=[];state.groupMode=false;state.issueFocus=null;state.edgeId=p.edges[0]?.id;")
f.write_text(s,encoding='utf-8')
f=Path('dist/validation.css');f.write_text(f.read_text(encoding='utf-8')+'''\n.group-selection-tools{display:flex;align-items:center;gap:8px}.group-selection-tools button{padding:10px 14px;border:1px solid #ccdce5;border-radius:7px;background:white;color:#31536c;cursor:pointer}.group-selection-tools button.active,.wall-buttons button.active{background:#fff0e6;border-color:#fd6017;color:#b64308}.group-selection-tools span{font-size:13px;color:#31536c;white-space:nowrap}.wall-picker svg{max-height:190px}.wall-buttons{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin:8px 0}.wall-buttons button{border:1px solid #b9ccda;border-radius:7px;background:white;padding:10px 3px;cursor:pointer;color:#31536c}.wall-buttons small{display:block;font-size:13px;margin-top:5px}.wall-pick{cursor:pointer}.wall-pick:hover line:last-of-type{stroke:#fd6017}\n''',encoding='utf-8')
