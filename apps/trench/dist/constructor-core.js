import {isPhysicalWell,pipeExitBearing,normalizeAngle,nodeAngle,connectedRotationEdge,rectangularPort,referencePipeBearing} from './node-geometry.js';
import {uid,makeWell,makeEdge,resolveEdge,wellGeometry} from './network-model.js';
export const clone=value=>structuredClone(value);
export function emptyProject(){return {version:4,id:uid(),name:'Новая трасса',notes:'Предварительная модель. Конструкции новых объектов — шаблон; отметки, геология и основание требуют проверки по проекту.',soils:[],wells:[],edges:[]}}
export class ProjectHistory{
 constructor(limit=60){this.limit=limit;this.past=[];this.future=[]}
 record(before,after,label='Изменение'){if(JSON.stringify(before)===JSON.stringify(after))return false;this.past.push({before:clone(before),after:clone(after),label});if(this.past.length>this.limit)this.past.shift();this.future=[];return true}
 undo(){const entry=this.past.pop();if(!entry)return null;this.future.push(entry);return clone(entry.before)}
 redo(){const entry=this.future.pop();if(!entry)return null;this.past.push(entry);return clone(entry.after)}
 get undoLabel(){return this.past.at(-1)?.label||''}
 get redoLabel(){return this.future.at(-1)?.label||''}
}
export function addWellAt(project,x,y){
 if(![x,y].every(Number.isFinite))throw Error('Некорректные координаты.');
 if(project.wells.length>=150)throw Error('В проекте допускается не более 150 колодцев.');let n=1;while(project.wells.some(w=>w.name==='К'+n))n++;
 project.version=4;const w=makeWell('К'+n,Math.round(x*100)/100,Math.round(y*100)/100,project);Object.assign(w,{heightMode:'total',height:2.7,rotationMode:'manual',rotation:0,zeroAngle:0});w.dataStatus='preliminary';project.wells.push(w);return w;
}
export function connectWells(project,from,to,{fromPort,toPort}={}){
 if(project.edges.length>=200)throw Error('В проекте допускается не более 200 участков.');
 const a=project.wells.find(w=>w.id===from),b=project.wells.find(w=>w.id===to);if(!a||!b||a===b)throw Error('Выберите два разных колодца.');
 const used=(w,id)=>project.edges.some(e=>(e.from.well===w.id&&e.from.port===id)||(e.to.well===w.id&&e.to.port===id));
 for(const [w,id]of [[a,fromPort],[b,toPort]])if(id&&(!w.ports.some(p=>p.id===id)||used(w,id)))throw Error('Подключение недоступно.');
 const e=makeEdge(project,from,to);
 for(const [side,w,id]of [['from',a,fromPort],['to',b,toPort]])if(id){w.ports=w.ports.filter(p=>p.id!==e[side].port);e[side].port=id}
 e.dataStatus='preliminary';project.edges.push(e);return e;
}
export function transformEdge(project,id,{length,bearing,grade,replaceFixed=false,zoneMode='proportional'}){
 const e=project.edges.find(e=>e.id===id);if(!e)throw Error('Выберите участок.');const res=resolveEdge(project,e),origin=res.from;
 if(length!==undefined){if(!Number.isFinite(length)||length<=0)throw Error('Длина должна быть больше нуля.');if(zoneMode==='fixed'&&e.sections.some(s=>s.a*res.length>=length||s.b<1&&s.b*res.length>=length))throw Error('Новая длина обрежет зону. Измените её границы или выберите масштабирование.');const f=length/res.length;for(const point of [...e.waypoints,res.to]){point.x=origin.x+(point.x-origin.x)*f;point.y=origin.y+(point.y-origin.y)*f}if(zoneMode==='fixed')for(const s of e.sections){s.a=s.a*res.length/length;s.b=s.b===1?1:s.b*res.length/length}}
 if(bearing!==undefined){if(!Number.isFinite(bearing))throw Error('Задайте направление.');const first=resolveEdge(project,e).points[1],old=Math.atan2(first.y-origin.y,first.x-origin.x),a=bearing*Math.PI/180-old;for(const point of [...e.waypoints,res.to]){const x=point.x-origin.x,y=point.y-origin.y;point.x=origin.x+x*Math.cos(a)-y*Math.sin(a);point.y=origin.y+x*Math.sin(a)+y*Math.cos(a)}}
 if(grade!==undefined){if(!Number.isFinite(grade))throw Error('Задайте уклон.');if(e.waypoints.some(v=>v.invert!==null)&&!replaceFixed)throw Error('Есть фиксированные отметки. Разрешите их замену либо задайте отметки вручную.');const updated=resolveEdge(project,e);updated.portB.invert=updated.portA.invert-grade/1000*updated.length;if(replaceFixed)for(const v of e.waypoints)v.invert=null;}
 return project.edges.filter(v=>v.id!==id&&(v.from.well===res.to.id||v.to.well===res.to.id)).map(v=>v.name);
}
export function copyEdgeSoilsToWells(project,id){
 const e=project.edges.find(e=>e.id===id);if(!e?.layers.length)throw Error('Сначала задайте слои участка.');
 for(const [end,key]of [[e.from,'start'],[e.to,'end']]){const w=project.wells.find(w=>w.id===end.well);if(!isPhysicalWell(w))continue;const layers=e.layers.map(l=>({soil:l.soil,bottom:l[key]}));if(layers.at(-1).bottom<wellGeometry(w).depth)throw Error('Грунты не покрывают котлован «'+w.name+'».');}
 for(const [end,key]of [[e.from,'start'],[e.to,'end']]){const w=project.wells.find(w=>w.id===end.well);if(isPhysicalWell(w))w.layers=e.layers.map(l=>({soil:l.soil,bottom:l[key]}))}
}

export function addEndpointAt(project,x,y,{ground=121,invert=ground-2.5}={}){
 if(![x,y,ground,invert].every(Number.isFinite))throw Error('Проверьте координаты и отметки свободного конца.');if(project.wells.length>=150)throw Error('Допускается не более 150 узлов.');let n=1;while(project.wells.some(w=>w.name==='Точка '+n))n++;
 const point=makeWell('Точка '+n,x,y,project);point.kind='endpoint';point.ground=ground;point.ports=[{id:uid(),name:'Конец трубы',invert,bearing:null}];point.layers=[];project.version=4;project.wells.push(point);return point;
}
export function setPipeLength(project,id,length){
 if(!Number.isFinite(length)||length<=0||length>1e8)throw Error('Задайте положительную длину трубы.');const e=project.edges.find(e=>e.id===id);if(!e)throw Error('Участок не найден.');const res=resolveEdge(project,e);if(!(res.length>.001))throw Error('Сначала задайте положение концов трубы.');
 const pieces=res.points.slice(1).map((b,i)=>({ds:b.s-res.points[i].s,dz:b.invert-res.points[i].invert})),actual=f=>pieces.reduce((n,v)=>n+Math.hypot(v.ds*f,v.dz),0),minimum=.01/res.length;
 if(length<actual(minimum)-1e-8)throw Error('Такая длина невозможна при заданных отметках. Увеличьте длину или уменьшите перепад высот.');let lo=minimum,hi=Math.max(1,length/res.length);while(actual(hi)<length)hi*=2;for(let i=0;i<70;i++){const mid=(lo+hi)/2;if(actual(mid)<length)lo=mid;else hi=mid}
 project.version=4;return transformEdge(project,id,{length:res.length*(lo+hi)/2});
}

export function setPipeExitAngle(project,edgeId,nodeId,angle){
 if(!Number.isFinite(angle)||Math.abs(angle)>1e8)throw Error('Задайте конечный угол выхода трубы.');
 const e=project.edges.find(v=>v.id===edgeId),origin=project.wells.find(w=>w.id===nodeId);if(!e||!origin)throw Error('Не найдены труба или узел.');
 const before=pipeExitBearing(project,e,nodeId),a=normalizeAngle(angle-before)*Math.PI/180;
 const opposite=project.wells.find(w=>w.id===(e.from.well===nodeId?e.to.well:e.from.well));if(!opposite)throw Error('Не найден конец трубы.');
 for(const v of [...e.waypoints,opposite]){const x=v.x-origin.x,y=v.y-origin.y;v.x=origin.x+x*Math.cos(a)-y*Math.sin(a);v.y=origin.y+x*Math.sin(a)+y*Math.cos(a)}
 project.version=4;return project.edges.filter(v=>v.id!==edgeId&&(v.from.well===opposite.id||v.to.well===opposite.id)).map(v=>v.name);
}


// Remove only obsolete generated elbows; user vertices are preserved unless straightening is requested.
export function removeGeneratedLeads(project){let count=0;for(const e of project.edges){const before=e.waypoints.length;e.waypoints=e.waypoints.filter(v=>!v.autoPort);count+=before-e.waypoints.length}return count}
export function reconcileRectangularPorts(project){removeGeneratedLeads(project);return []}
export function setRectangularPortWall(project,edgeId,nodeId,wall){
 const w=project.wells.find(v=>v.id===nodeId),e=project.edges.find(v=>v.id===edgeId);if(!w||w.shape!=='rect'||!e||!Number.isInteger(wall)||wall<0||wall>3)throw Error('Выберите стену колодца.');const side=e.from.well===nodeId?'from':e.to.well===nodeId?'to':null;if(!side)throw Error('Труба не связана с колодцем.');
 const direction=nodeAngle(project,w);e.waypoints=[];const affected=setPipeExitAngle(project,edgeId,nodeId,direction+wall*90);w.ports.find(v=>v.id===e[side].port).wall=wall;
 if(w.rotationMode==='pipe'){const ref=connectedRotationEdge(project,w);w.rotation=normalizeAngle(direction-referencePipeBearing(project,ref,w.id))}else w.rotation=normalizeAngle(direction-(w.zeroAngle||0));return affected;
}
export function alignWellToPipe(project,edgeId,nodeId,wall){const w=project.wells.find(v=>v.id===nodeId),e=project.edges.find(v=>v.id===edgeId);if(!w||w.shape!=='rect'||!e||![e.from.well,e.to.well].includes(nodeId)||!Number.isInteger(wall)||wall<0||wall>3)throw Error('Выберите трубу и стену колодца.');removeGeneratedLeads(project);Object.assign(w,{rotationMode:'pipe',rotationEdge:edgeId,rotation:normalizeAngle(-wall*90)});project.version=4;return w}
export function straightenPipe(project,edgeId){const e=project.edges.find(v=>v.id===edgeId);if(!e)throw Error('Выберите трубу.');e.waypoints=[];project.version=4}

export function setWellHeight(w,value){if(!Number.isFinite(value)||value<=0)throw Error('Задайте положительную высоту колодца.');const g=wellGeometry(w);Object.assign(w,{heightMode:'total',height:value,workingHeight:g.workingHeight,workingHeightOverride:g.workingHeight})}
export function setWellWorkingHeight(w,value){if(!Number.isFinite(value)||value<=0)throw Error('Рабочая часть должна быть больше нуля.');const g=wellGeometry(w);Object.assign(w,{heightMode:'total',height:g.height,workingHeight:value,workingHeightOverride:value})}

export function setWellNeckHeight(w,value){if(!Number.isFinite(value)||value<0)throw Error('Высота горловины должна быть нулём или больше.');const g=wellGeometry(w);Object.assign(w,{heightMode:'total',height:g.workingHeight+value+w.slab+w.base,workingHeight:g.workingHeight,workingHeightOverride:g.workingHeight,neckHeight:value})}
export function setWellFloor(w,value){if(!Number.isFinite(value))throw Error('Укажите отметку пола внутри колодца.');setWellHeight(w,w.ground-value+w.base)}
