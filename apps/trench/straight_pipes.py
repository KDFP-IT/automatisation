from pathlib import Path
p=Path('dist/constructor-core.js');s=p.read_text(encoding='utf-8');a=s.index('export function reconcileRectangularPorts(');s=s[:a]+'''// Remove only obsolete generated elbows; user vertices are preserved unless straightening is requested.
export function removeGeneratedLeads(project){let count=0;for(const e of project.edges){const before=e.waypoints.length;e.waypoints=e.waypoints.filter(v=>!v.autoPort);count+=before-e.waypoints.length}return count}
export function reconcileRectangularPorts(project){removeGeneratedLeads(project);return []}
export function setRectangularPortWall(project,edgeId,nodeId,wall){
 const w=project.wells.find(v=>v.id===nodeId),e=project.edges.find(v=>v.id===edgeId);if(!w||w.shape!=='rect'||!e||!Number.isInteger(wall)||wall<0||wall>3)throw Error('Выберите стену колодца.');const side=e.from.well===nodeId?'from':e.to.well===nodeId?'to':null;if(!side)throw Error('Труба не связана с колодцем.');
 const direction=nodeAngle(project,w);e.waypoints=[];const affected=setPipeExitAngle(project,edgeId,nodeId,direction+wall*90);w.ports.find(v=>v.id===e[side].port).wall=wall;
 if(w.rotationMode==='pipe'){const ref=connectedRotationEdge(project,w);w.rotation=normalizeAngle(direction-referencePipeBearing(project,ref,w.id))}else w.rotation=normalizeAngle(direction-(w.zeroAngle||0));return affected;
}
export function alignWellToPipe(project,edgeId,nodeId,wall){const w=project.wells.find(v=>v.id===nodeId),e=project.edges.find(v=>v.id===edgeId);if(!w||w.shape!=='rect'||!e||![e.from.well,e.to.well].includes(nodeId)||!Number.isInteger(wall)||wall<0||wall>3)throw Error('Выберите трубу и стену колодца.');removeGeneratedLeads(project);Object.assign(w,{rotationMode:'pipe',rotationEdge:edgeId,rotation:normalizeAngle(-wall*90)});project.version=4;return w}
export function straightenPipe(project,edgeId){const e=project.edges.find(v=>v.id===edgeId);if(!e)throw Error('Выберите трубу.');e.waypoints=[];project.version=4}
''';p.write_text(s,encoding='utf-8')
p=Path('dist/network-app.js');s=p.read_text(encoding='utf-8').replace('reconcileRectangularPorts,connectWells','reconcileRectangularPorts,removeGeneratedLeads,alignWellToPipe,straightenPipe,connectWells')
s=s.replace("resultsScope:'selection'", "issueFocus:null,resultsScope:'selection'")
s=s.replace('Короткий подвод к центру стены. Другие колодцы остаются на месте.','Выбор стены выпрямит и повернёт всю трубу. Её второй конец переместится.')
s=s.replace('Выберите стену — система добавит подвод под 90°.','Можно повернуть колодец или всю прямую трубу.')
s=s.replace('Нажмите стену, к которой подвести трубу','Выберите стену для прямой трубы')
s=s.replace('<button data-action="choose-wall" data-well-id="${esc(w.id)}" data-edge-id="${esc(e.id)}" data-wall="${port.wall}">Подвести к ближайшей стене</button>', '<button data-action="align-well" data-well-id="${esc(w.id)}" data-edge-id="${esc(e.id)}" data-wall="${port.wall}">Повернуть колодец к трубе</button>')
s=s.replace("notify('Подвод к стене обновлён. Длина трубы пересчитана.')", "notify('Труба прямая. Второй конец перемещён; соседние участки перепроверены.')")
s=s.replace("if(a==='apply-soils')", "if(a==='align-well'){alignWellToPipe(p,el.dataset.edgeId,el.dataset.wellId,Number(el.dataset.wall));recordChange(actionBefore,'Поворот колодца к трубе');persist();render();return}if(a==='straighten-pipe'){straightenPipe(p,e.id);recordChange(actionBefore,'Прямая труба');persist();render();return}if(a==='apply-soils')")
s=s.replace("const ways=e.waypoints.map", "const ways=(e.waypoints.length?'<button class=\"inline-add\" data-action=\"straighten-pipe\">Сделать трубу прямой</button>':'')+e.waypoints.map")
s=s.replace("p=validateProject(model);history.past=[];", "p=validateProject(model);const beforeCleanup=clone(p),removed=removeGeneratedLeads(p);history.past=[];")
s=s.replace("state.edgeId=p.edges[0]?.id;state.wellId", "if(removed){history.record(beforeCleanup,p,'Убрать автоматические изгибы');setTimeout(()=>{persist();notify('Автоматические изгибы убраны. Точки, заданные вручную, сохранены.')},0)}state.issueFocus=null;state.edgeId=p.edges[0]?.id;state.wellId")
p.write_text(s,encoding='utf-8')
