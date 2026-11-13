from pathlib import Path
p=Path('dist/node-geometry.js');s=p.read_text(encoding='utf-8');a=s.index(' const from=e.from.well');b=s.index('\n}',a)
s=s[:a]+''' return normalizeAngle(pipeExitBearing(p,e,w.id)+offset);'''+s[b:]
s+='''
export function connectedRotationEdge(p,w){const edges=p.edges.filter(e=>e.from.well===w.id||e.to.well===w.id);return edges.find(e=>e.id===w.rotationEdge)||edges[0]}
export function pipeExitBearing(p,e,nodeId){
 const w=p.wells.find(v=>v.id===nodeId),from=e.from.well===nodeId;if(!w||!from&&e.to.well!==nodeId)throw Error('Труба не связана с узлом.');
 const other=p.wells.find(v=>v.id===(from?e.to.well:e.from.well)),point=(from?e.waypoints[0]:e.waypoints.at(-1))||other;
 if(!point||Math.hypot(point.x-w.x,point.y-w.y)<1e-9)throw Error('Сначала задайте ненулевое направление трубы.');
 return normalizeAngle(Math.atan2(point.y-w.y,point.x-w.x)*180/Math.PI);
}
export const isSquareWell=w=>isPhysicalWell(w)&&w.shape==='rect'&&Math.abs(w.width-w.length)<1e-6;
export function rotateWellTo(p,w,angle,{snap=true}={}){if(!Number.isFinite(angle))throw Error('Задайте угол поворота.');const e=connectedRotationEdge(p,w);if(snap&&isSquareWell(w)&&e){w.rotationMode='pipe';w.rotationEdge=e.id;w.rotation=normalizeAngle(Math.round(normalizeAngle(angle-pipeExitBearing(p,e,w.id))/90)*90)}else{w.rotationMode='manual';w.rotation=normalizeAngle(angle-(w.zeroAngle||0))}p.version=4}
export function quarterTurnWell(p,w,direction=1){const e=connectedRotationEdge(p,w);if(e&&w.shape==='rect'){const current=normalizeAngle(nodeAngle(p,w)-pipeExitBearing(p,e,w.id));w.rotationMode='pipe';w.rotationEdge=e.id;w.rotation=normalizeAngle(Math.round(current/90)*90+Math.sign(direction)*90)}else rotateWellTo(p,w,nodeAngle(p,w)+Math.sign(direction)*90,{snap:false});p.version=4}
'''
# Invalid drafts must not crash all views when auto pipe degenerates.
s=s.replace('return normalizeAngle(pipeExitBearing(p,e,w.id)+offset);',"try{return normalizeAngle(pipeExitBearing(p,e,w.id)+offset)}catch{return normalizeAngle(zero+offset)}")
p.write_text(s,encoding='utf-8')
p=Path('dist/constructor-core.js');s=p.read_text(encoding='utf-8').replace("import {isPhysicalWell}","import {isPhysicalWell,pipeExitBearing,normalizeAngle}")
s+='''
export function setPipeExitAngle(project,edgeId,nodeId,angle){
 if(!Number.isFinite(angle)||Math.abs(angle)>1e8)throw Error('Задайте конечный угол выхода трубы.');
 const e=project.edges.find(v=>v.id===edgeId),origin=project.wells.find(w=>w.id===nodeId);if(!e||!origin)throw Error('Не найдены труба или узел.');
 const before=pipeExitBearing(project,e,nodeId),a=normalizeAngle(angle+(origin.zeroAngle||0)-before)*Math.PI/180;
 const opposite=project.wells.find(w=>w.id===(e.from.well===nodeId?e.to.well:e.from.well));if(!opposite)throw Error('Не найден конец трубы.');
 for(const v of [...e.waypoints,opposite]){const x=v.x-origin.x,y=v.y-origin.y;v.x=origin.x+x*Math.cos(a)-y*Math.sin(a);v.y=origin.y+x*Math.sin(a)+y*Math.cos(a)}
 project.version=4;return project.edges.filter(v=>v.id!==edgeId&&(v.from.well===opposite.id||v.to.well===opposite.id)).map(v=>v.name);
}
''';p.write_text(s,encoding='utf-8')
p=Path('dist/network-app.js');s=p.read_text(encoding='utf-8').replace('isPhysicalWell,nodeAngle,normalizeAngle','isPhysicalWell,nodeAngle,normalizeAngle,pipeExitBearing,rotateWellTo,quarterTurnWell').replace('addEndpointAt,setPipeLength,','addEndpointAt,setPipeLength,setPipeExitAngle,')
s=s.replace("function rotationEditor(w,base){return ","function rotationEditor(w,base){return (w.shape==='rect'?'<div class=\"two\"><button class=\"inline-add\" data-action=\"quarter-turn\" data-direction=\"-1\">↶ −90°</button><button class=\"inline-add\" data-action=\"quarter-turn\" data-direction=\"1\">↷ +90°</button></div>':'')+")
s=s.replace('Ось Z — через центр. Синяя ручка — поворот, оранжевая — направление нуля.','Ось Z — через центр. Квадратный колодец: шаг 90° относительно трубы. Оранжевая ручка — направление нуля.')
s=s.replace("${e?`<button data-action=\"edge\"", "${e?exitAngleField(e,w)+`<button data-action=\"edge\"")
# Common input serves pipe inspector and each connected port.
pos=s.index('function renderEndpointInspector()')
s=s[:pos]+'''function exitAngleField(e,w,label='Угол выхода от 0°'){let angle;try{angle=normalizeAngle(pipeExitBearing(p,e,w.id)-(w.zeroAngle||0))}catch{angle=0}return field(label,'',angle,{unit:'°',command:'pipe-exit',index:w.id,part:e.id,hint:'В плане, от нуля узла. Узел фиксирован, другой конец и вершины поворачиваются.'})}
'''+s[pos:]
s=s.replace("const body=field('Длина трубы'", "const body=exitAngleField(e,res.from,'Угол выхода в начале')+exitAngleField(e,res.to,'Угол выхода в конце')+field('Длина трубы'")
s=s.replace("if(command==='pipe-length'){node.dataset.invalidDraft='true';return}","if(['pipe-length','pipe-exit'].includes(command)){node.dataset.invalidDraft='true';return}")
s=s.replace("if(node.dataset.command!=='pipe-length'||!node.dataset.invalidDraft)return;", "if(!['pipe-length','pipe-exit'].includes(node.dataset.command)||!node.dataset.invalidDraft)return;")
s=s.replace("setPipeLength(p,edge().id,node.value===''?NaN:Number(node.value));", "const value=node.value===''?NaN:Number(node.value),affected=node.dataset.command==='pipe-exit'?setPipeExitAngle(p,node.dataset.part,node.dataset.index,value):setPipeLength(p,edge().id,value);")
s=s.replace("recordChange(before,'Длина трубы');persist();render()", "recordChange(before,node.dataset.command==='pipe-exit'?'Угол выхода трубы':'Длина трубы');persist();render();if(affected?.length)notify('Также изменились: '+affected.join(', '))")
s=s.replace("ev.target.dataset.command==='pipe-length'", "['pipe-length','pipe-exit'].includes(ev.target.dataset.command)")
s=s.replace("if(command==='bearing')node.value=number(bearing(res,'from'));", "if(command==='bearing')node.value=number(bearing(res,'from'));if(command==='pipe-exit'&&!node.dataset.invalidDraft){const route=p.edges.find(v=>v.id===node.dataset.part),origin=p.wells.find(v=>v.id===node.dataset.index);if(route&&origin)try{node.value=number(normalizeAngle(pipeExitBearing(p,route,origin.id)-(origin.zeroAngle||0)))}catch{}}")
s=s.replace("if(a==='layer-mode')", "if(a==='quarter-turn'&&w){quarterTurnWell(p,w,Number(el.dataset.direction));recordChange(actionBefore,'Поворот колодца на 90°');persist();render();return}if(a==='layer-mode')")
s=s.replace("w.rotationMode='manual';w.rotation=normalizeAngle(angle-(w.zeroAngle||0))}calculate()", "rotateWellTo(p,w,angle)}calculate()")
p.write_text(s,encoding='utf-8')
