import {enrichIssues} from './issue-guidance.js';
import {assignBackfill,validateBackfill} from './backfill.js';
import {integrateJointTrenches} from './joint-excavation.js';
import {isPhysicalWell,wellDimensions,nodeAngle,localPoint,rectangleVertices,rectanglesOverlap} from './node-geometry.js';
import {clipPolygon,inspectNetwork,issuePaths} from './network-checks.js';
export const VERSION=4;
export const uid=()=>{if(globalThis.crypto.randomUUID)return globalThis.crypto.randomUUID();const b=globalThis.crypto.getRandomValues(new Uint8Array(16));b[6]=(b[6]&15)|64;b[8]=(b[8]&63)|128;const h=Array.from(b,v=>v.toString(16).padStart(2,'0')).join('');return h.slice(0,8)+'-'+h.slice(8,12)+'-'+h.slice(12,16)+'-'+h.slice(16,20)+'-'+h.slice(20)};
export const cot=a=>1/Math.tan(a*Math.PI/180);
export const degrees=m=>Math.atan2(1,m)*180/Math.PI;
export const lerp=(a,b,t)=>a+(b-a)*t;
export const sum=a=>a.reduce((x,y)=>x+y,0);
export function makeWell(name='Новый колодец',x=0,y=0,project=null){return {id:uid(),name,kind:'well',x,y,ground:121,shape:'round',diameter:1,width:1.4,length:1.4,wall:.12,workingHeight:1.8,neckHeight:.5,neckDiameter:.7,neckWall:.08,neckX:0,neckY:0,slab:.2,base:.2,baseProjection:.05,pitMargin:.4,pitSlope:.5,pad:.2,padMargin:.1,ports:[],layers:project?[]:[{soil:'ige1',bottom:1},{soil:'ige3',bottom:3},{soil:'ige5',bottom:20}]}}
export function makeSection(a=0,b=1){return {id:uid(),a,b,method:'trench',width:.9,slopeMode:'angles',left:45,right:45,topWidth:3,bedding:.15,beddingMaterial:'ЩПС',around:true,protection:.3,casing:0,casingWall:.04}}
export function makeEdge(project,fromId,toId){
 const a=project.wells.find(w=>w.id===fromId),b=project.wells.find(w=>w.id===toId);if(!a||!b||a===b)throw Error('Выберите два разных узла.');
 const p1={id:uid(),name:'Выход → '+b.name,invert:isPhysicalWell(a)?wellGeometry(a,project).floor+.15:(a.ports[0]?.invert??a.ground-2.5),bearing:null},p2={id:uid(),name:'Вход ← '+a.name,invert:isPhysicalWell(b)?wellGeometry(b,project).floor+.15:(b.ports[0]?.invert??b.ground-2.5),bearing:null};a.ports.push(p1);b.ports.push(p2);
 return {id:uid(),name:a.name+' → '+b.name,from:{well:a.id,port:p1.id},to:{well:b.id,port:p2.id},diameter:.4,pipeWall:.024,waypoints:[],sections:[makeSection()],layers:a.layers.length&&a.layers.length===b.layers.length&&a.layers.every((l,i)=>l.soil===b.layers[i].soil&&project.soils.some(s=>s.id===l.soil))?a.layers.map((l,i)=>({soil:l.soil,start:l.bottom,end:b.layers[i].bottom})):[]};
}
export function seedProject(){
 const p={version:VERSION,id:uid(),name:'Пилот · Д12 / Д12′ — КК2-12',notes:'Связность, длины 21,02 / 8,75 м и отметки труб взяты из профиля листа 2. Координаты условные; положение футляров, наружный низ труб, конструкция колодцев и границы грунтов требуют проверки по проекту. Это исходная модель для настройки, а не готовая ведомость проекта.',soils:[{id:'ige1',name:'ИГЭ-1 · техногенный суглинок',group:'III',color:'#b9a88e'},{id:'ige3',name:'ИГЭ-3б · суглинок',group:'II',color:'#c5b99c'},{id:'ige5',name:'ИГЭ-5б · песок',group:'I',color:'#e4d5ac'}],wells:[],edges:[]};
 const endX=14.18+6.84*Math.cos(Math.PI/18),endY=6.84*Math.sin(Math.PI/18);
 const a=makeWell('Д12',0,0),b=makeWell('Д12′',endX,endY+8.75),c=makeWell('КК2-12',endX,endY);a.ground=121.038;b.ground=121.039;c.ground=121.25;c.diameter=2;c.workingHeight=3;c.neckHeight=1.8;c.slab=.25;c.base=.25;
 p.wells=[a,b,c];const e=makeEdge(p,a.id,c.id),f=makeEdge(p,b.id,c.id);
 a.ports[0].invert=118.538;c.ports[0].invert=118.117;b.ports[0].invert=118.539;c.ports[1].invert=118.364;
 e.waypoints=[{id:uid(),x:14.18,y:0,ground:null,invert:118.254}];
 e.sections=[makeSection(0,5.21/21.02),makeSection(5.21/21.02,7.79/21.02),makeSection(7.79/21.02,1)];
 for(const s of [e.sections[0],e.sections[2]]){s.casing=.71;s.width=1.21}
 f.sections=[makeSection(0,.885/8.75),makeSection(.885/8.75,7.865/8.75),makeSection(7.865/8.75,1)];f.sections[1].casing=.71;f.sections[1].width=1.21;
 p.edges=[e,f];return p;
}
export function wellGeometry(w,p=null){
 if(!isPhysicalWell(w)){const z=w.ports[0]?.invert??w.ground-2.5;return {bodyW:0,bodyL:0,baseW:0,baseL:0,bodyTop:w.ground,floor:z,bottom:z,pitBottom:z,neckD:0,occupied:0,width:0,length:0,depth:0,m:0,excavation:0,pad:0,fill:0,pipe:0,backfill:0,topW:0,topL:0,rotation:0,workingHeight:0,neckHeight:0,height:0}}
 const {workingHeight,neckHeight,height}=wellDimensions(w),rotation=nodeAngle(p,w);
 const bodyW=w.shape==='round'?w.diameter+2*w.wall:w.width+2*w.wall,bodyL=w.shape==='round'?bodyW:w.length+2*w.wall;
 const baseW=bodyW+2*w.baseProjection,baseL=bodyL+2*w.baseProjection;
 const bodyTop=w.ground-neckHeight,floor=bodyTop-w.slab-workingHeight,bottom=floor-w.base,pitBottom=bottom-w.pad;
 const bodyArea=w.shape==='round'?Math.PI*bodyW**2/4:bodyW*bodyL,baseArea=w.shape==='round'?Math.PI*baseW**2/4:baseW*baseL;
 const neckD=w.neckDiameter+2*w.neckWall,occupied=bodyArea*(workingHeight+w.slab)+baseArea*w.base+Math.PI*neckD**2/4*neckHeight;
 const width=baseW+2*w.pitMargin,length=baseL+2*w.pitMargin,depth=w.ground-pitBottom,m=w.pitSlope;
 const excavation=width*length*depth+(width+length)*m*depth**2+4/3*m*m*depth**3;
 const pad=(baseW+2*w.padMargin)*(baseL+2*w.padMargin)*w.pad,backfill=excavation-occupied-pad;
 return {workingHeight,neckHeight,height,rotation,bodyW,bodyL,baseW,baseL,bodyTop,floor,bottom,pitBottom,neckD,occupied,width,length,depth,m,excavation,pad,fill:pad,pipe:occupied,backfill,topW:width+2*m*depth,topL:length+2*m*depth};
}
export function resolveEdge(p,e){
 const from=p.wells.find(w=>w.id===e.from.well),to=p.wells.find(w=>w.id===e.to.well);
 if(!from||!to)throw Error('Не найдены конечные узлы.');
 const portA=from.ports.find(x=>x.id===e.from.port),portB=to.ports.find(x=>x.id===e.to.port);if(!portA||!portB)throw Error('Не найдены подключения трубы.');
 const raw=[from,...e.waypoints,to],stations=[0];for(let i=1;i<raw.length;i++)stations.push(stations.at(-1)+Math.hypot(raw[i].x-raw[i-1].x,raw[i].y-raw[i-1].y));
 const length=stations.at(-1);
 const points=raw.map((r,i)=>({x:r.x,y:r.y,s:stations[i],ground:r.ground===null?lerp(from.ground,to.ground,stations[i]/length):r.ground,invert:i===0?portA.invert:i===raw.length-1?portB.invert:r.invert===null?lerp(portA.invert,portB.invert,stations[i]/length):r.invert}));
 const actualLength=sum(points.slice(1).map((r,i)=>Math.hypot(r.s-points[i].s,r.invert-points[i].invert)));
 return {from,to,portA,portB,points,length,actualLength};
}
export function atStation(res,s){
 const points=res.points;s=Math.max(0,Math.min(res.length,s));let i=points.findIndex((r,i)=>i>0&&r.s>=s);if(i<1)i=points.length-1;
 const a=points[i-1],b=points[i],ds=b.s-a.s,t=ds?(s-a.s)/ds:0,dx=(b.x-a.x)/ds,dy=(b.y-a.y)/ds;
 return {x:lerp(a.x,b.x,t),y:lerp(a.y,b.y,t),ground:lerp(a.ground,b.ground,t),invert:lerp(a.invert,b.invert,t),grade:(b.invert-a.invert)/ds,dx,dy,s};
}
export function sectionAt(e,res,s){const t=s/res.length;return e.sections.find((v,i)=>t>=v.a-1e-9&&(t<v.b||i===e.sections.length-1))||e.sections[0]}
export function crossSection(e,res,section,s){
 const point=atStation(res,s),radius=(section.casing||e.diameter)/2,carrierR=e.diameter/2,axis=point.invert+carrierR*Math.sqrt(1+point.grade**2),verticalR=radius*Math.sqrt(1+point.grade**2);
 const bottom=axis-verticalR-section.bedding,depth=point.ground-bottom;
 let left=cot(section.left),right=cot(section.right);
 if(section.slopeMode==='top'){
  const start=atStation(res,section.a*res.length),startAxis=start.invert+carrierR*Math.sqrt(1+start.grade**2),startDepth=start.ground-(startAxis-radius*Math.sqrt(1+start.grade**2)-section.bedding);
  left=right=(section.topWidth-section.width)/(2*startDepth);
 }
 const top=section.width+(left+right)*depth,fillTop=section.around?Math.min(point.ground,axis+verticalR+section.protection):bottom+section.bedding;
 return {...point,axis,radius,verticalR,bottom,depth,left,right,top,width:section.width,fillTop};
}
function overlap(a,b,c,d){return Math.max(0,Math.min(b,d)-Math.max(a,c))}
function union(intervals){const a=intervals.filter(([l,h])=>h>l).sort((a,b)=>a[0]-b[0]),result=[];for(const item of a){const last=result.at(-1);if(last&&last[1]>=item[0])last[1]=Math.max(last[1],item[1]);else result.push([...item])}return result}
function subtract(interval,cuts){let result=[interval];for(const [lo,hi]of union(cuts)){const next=[];for(const[a,b]of result){if(hi<=a||lo>=b)next.push([a,b]);else{if(a<lo)next.push([a,lo]);if(b>hi)next.push([hi,b])}}result=next}return result}
export function pitInterval(w,g,x,y){
 if(!isPhysicalWell(w))return null;const [lx,ly]=localPoint(w,x,y,g.rotation);const dx=Math.max(0,Math.abs(lx)-g.width/2),dy=Math.max(0,Math.abs(ly)-g.length/2);
 if(!g.m&&(dx>0||dy>0))return null;const lo=g.pitBottom+(g.m?Math.max(dx,dy)/g.m:0);return lo<w.ground?[lo,w.ground]:null;
}
function wellSoils(p,w,g){
 const volumes=Object.fromEntries(p.soils.map(s=>[s.id,0]));let previous=0;
 const primitive=h=>g.width*g.length*h+(g.width+g.length)*g.m*h*h+4/3*g.m*g.m*h**3;
 for(const layer of w.layers){const lower=Math.max(0,g.depth-layer.bottom),upper=Math.max(0,g.depth-previous);volumes[layer.soil]=(volumes[layer.soil]||0)+primitive(upper)-primitive(lower);previous=layer.bottom}
 return volumes;
}
function validateWell(p,w){
 const errors=[];if(!isPhysicalWell(w)){for(const k of ['x','y','ground'])if(!Number.isFinite(w[k]))errors.push('Заполните координаты и поверхность свободного конца.');for(const port of w.ports)if(!Number.isFinite(port.invert))errors.push('Заполните отметку трубы в свободном конце.');return errors}for(const k of ['x','y','ground','diameter','width','length','wall','workingHeight','neckHeight','neckDiameter','neckWall','neckX','neckY','slab','base','baseProjection','pitMargin','pitSlope','pad','padMargin'])if(!Number.isFinite(w[k]))errors.push('Заполните поле '+k+'.');
 for(const k of ['wall','neckHeight','neckWall','slab','base','baseProjection','pitMargin','pitSlope','pad','padMargin'])if(w[k]<0)errors.push('Размеры и заложение откосов не могут быть отрицательными.');
 for(const k of ['workingHeight','neckDiameter',...(w.shape==='round'?['diameter']:['width','length'])])if(w[k]<=0)errors.push('Основные размеры должны быть больше нуля.');
 if(!['round','rect'].includes(w.shape))errors.push('Неизвестная форма колодца.');
 const g=wellGeometry(w,p);
 if(w.heightMode==='total'&&(!Number.isFinite(w.height)||g.neckHeight<0))errors.push('Высота колодца меньше суммы рабочей части, перекрытия и днища. Увеличьте общую высоту или уменьшите рабочую часть.');
 if(!Number.isFinite(g.rotation))errors.push('Проверьте угол поворота и направление нуля.');
 if(w.shape==='round'&&Math.hypot(w.neckX,w.neckY)+g.neckD/2>g.bodyW/2+1e-9)errors.push('Горловина выходит за габарит рабочей части.');
 if(w.shape==='rect'&&(Math.abs(w.neckX)+g.neckD/2>g.bodyW/2||Math.abs(w.neckY)+g.neckD/2>g.bodyL/2))errors.push('Горловина выходит за габарит рабочей части.');
 if(w.padMargin>w.pitMargin)errors.push('Подготовка выходит за дно котлована: увеличьте рабочий зазор.');
 let prev=0;for(const layer of w.layers){if(!p.soils.some(x=>x.id===layer.soil)||!Number.isFinite(layer.bottom)||layer.bottom<=prev)errors.push('Проверьте грунты: глубины границ должны возрастать.');prev=layer.bottom}
 if(prev<g.depth-1e-8)errors.push('Грунтовые слои не покрывают дно котлована.');
 for(const port of w.ports){if(!Number.isFinite(port.invert)||(port.bearing!==null&&!Number.isFinite(port.bearing)))errors.push('Проверьте отметки и направления подключений.');if(port.invert<g.floor-1e-6)errors.push('Подключение «'+port.name+'» ниже внутреннего дна.');if(port.invert>w.ground)errors.push('Подключение находится выше поверхности.');}
 return [...new Set(errors)];
}
function validateEdge(p,e,res){
 const errors=[];if(e.from.well===e.to.well)errors.push('Начало и конец участка совпадают.');
 if(!Number.isFinite(res.length)||res.length<.01)errors.push('Участок должен иметь ненулевую длину.');
 if(!Number.isFinite(e.diameter)||e.diameter<=0||!Number.isFinite(e.pipeWall)||e.pipeWall<0||2*e.pipeWall>=e.diameter)errors.push('Проверьте наружный диаметр и толщину стенки трубы.');
 for(const point of res.points)if(!['x','y','ground','invert'].every(k=>Number.isFinite(point[k])))errors.push('Проверьте координаты и отметки точек профиля.');
 if(res.points.some((v,i)=>i&&v.s-res.points[i-1].s<.001))errors.push('Соседние точки трассы совпадают.');
 let end=0;for(const section of e.sections){
  if(!['trench','supports'].includes(section.method))errors.push('Неизвестный способ прокладки.');
  if(!Number.isFinite(section.a)||!Number.isFinite(section.b)||Math.abs(section.a-end)>1e-6||section.b<=section.a||section.b>1+1e-9)errors.push('Отрезки должны покрывать участок без разрывов и пересечений.');end=section.b;
  for(const k of ['width','left','right','topWidth','bedding','protection','casing','casingWall'])if(!Number.isFinite(section[k]))errors.push('Заполните параметры отрезков.');
  if(section.casing<0||section.casingWall<0||(section.casing&&section.casing-2*section.casingWall<e.diameter))errors.push('Труба не помещается во внутреннем диаметре футляра.');
  if(section.method!=='trench')continue;
  if(section.width<=0||section.bedding<0||section.protection<0)errors.push('Проверьте ширину траншеи и толщины засыпки.');
  if(!['angles','top'].includes(section.slopeMode))errors.push('Неизвестный способ задания откосов.');
  if(section.slopeMode==='angles'&&[section.left,section.right].some(a=>a<=0||a>90))errors.push('Углы откосов: больше 0° и не больше 90° от горизонтали.');
  if(section.slopeMode==='top'&&section.topWidth<section.width)errors.push('Верхнее основание меньше нижнего.');
  const samples=[section.a*res.length,section.b*res.length,...res.points.filter(v=>v.s>section.a*res.length&&v.s<section.b*res.length).map(v=>v.s)];
  for(const s of samples){const c=crossSection(e,res,section,s);if(c.depth<=0||c.axis+c.verticalR>c.ground+1e-8)errors.push('Труба или футляр выходит выше поверхности.');if(section.around&&c.axis+c.verticalR+section.protection>c.ground+1e-8)errors.push('Защитный слой выходит выше поверхности.');for(const m of [c.left,c.right])if(section.width/2+m*(c.axis-c.bottom)<Math.hypot(c.radius,m*c.verticalR)-1e-8)errors.push('Труба или футляр не помещается между откосами.');}
 }
 if(Math.abs(end-1)>1e-6)errors.push('Отрезки не покрывают всю длину участка.');
 let a=0,b=0;for(const layer of e.layers){if(!p.soils.some(x=>x.id===layer.soil)||![layer.start,layer.end].every(Number.isFinite)||layer.start<=a||layer.end<=b)errors.push('Границы грунтов должны возрастать в начале и конце участка.');a=layer.start;b=layer.end}
 for(const point of res.points){const c=crossSection(e,res,sectionAt(e,res,point.s),point.s);if(sectionAt(e,res,point.s).method==='trench'&&lerp(a,b,point.s/res.length)<c.depth-1e-8)errors.push('Грунтовые слои не покрывают дно траншеи.');}
 for(const [w,port]of [[res.from,res.portA],[res.to,res.portB]]){if(!isPhysicalWell(w))continue;const g=wellGeometry(w,p);if(port.invert+e.diameter>g.bodyTop-w.slab+1e-8)errors.push('Труба у узла «'+w.name+'» не помещается по высоте рабочей части.');}
 return [...new Set(errors)];
}
export function integrateEdge(p,e,res,{step=.22,crossSamples=56}={}){
 step=Math.max(step,res.length/1200);
 const result={excavation:0,pipe:0,fill:0,bedding:0,around:0,protection:0,backfill:0,excluded:0,soils:Object.fromEntries(p.soils.map(s=>[s.id,0]))};
 const pits=p.wells.filter(isPhysicalWell).map(w=>({w,g:wellGeometry(w,p)}));
 const boundaries=[...new Set([0,res.length,...res.points.map(p=>p.s),...e.sections.flatMap(s=>[s.a*res.length,s.b*res.length])])].sort((a,b)=>a-b);
 for(let k=1;k<boundaries.length;k++){
  const start=boundaries[k-1],end=boundaries[k],n=Math.max(1,Math.ceil((end-start)/step)),ds=(end-start)/n;
  for(let i=0;i<n;i++){
   const s=start+(i+.5)*ds,section=sectionAt(e,res,s);if(section.method!=='trench')continue;const c=crossSection(e,res,section,s),xMin=-section.width/2-c.left*c.depth,xMax=section.width/2+c.right*c.depth,dx=(xMax-xMin)/crossSamples;
   for(let j=0;j<crossSamples;j++){
    const x=xMin+(j+.5)*dx,lowerY=x < -section.width/2?(-x-section.width/2)/c.left:x>section.width/2?(x-section.width/2)/c.right:0;
    const lower=c.bottom+lowerY,upper=c.ground;if(!Number.isFinite(lower)||upper<=lower)continue;
    const wx=c.x-c.dy*x,wy=c.y+c.dx*x,cuts=pits.map(({w,g})=>pitInterval(w,g,wx,wy)).filter(Boolean);
    const intervals=subtract([lower,upper],cuts),weight=ds*dx,pipeHalf=Math.abs(x)<c.radius?Math.sqrt(c.radius*c.radius-x*x)*Math.sqrt(1+c.grade*c.grade):0;
    const pl=c.axis-pipeHalf,ph=c.axis+pipeHalf,bedTop=c.bottom+section.bedding,aroundTop=c.axis+c.verticalR;
    result.excluded+=((upper-lower)-sum(intervals.map(([lo,hi])=>hi-lo)))*weight;
    for(const[lo,hi]of intervals){
     result.excavation+=(hi-lo)*weight;result.pipe+=overlap(lo,hi,pl,ph)*weight;
     const material=(a,b)=>Math.max(0,overlap(lo,hi,a,b)-overlap(Math.max(lo,a),Math.min(hi,b),pl,ph))*weight;
     result.bedding+=material(c.bottom,bedTop);
     if(section.around){result.around+=material(bedTop,aroundTop);result.protection+=material(aroundTop,c.fillTop)}
     let previous=0;for(const layer of e.layers){const bottom=lerp(layer.start,layer.end,s/res.length);result.soils[layer.soil]+=overlap(lo,hi,c.ground-bottom,c.ground-previous)*weight;previous=bottom}
    }
   }
  }
 }
 result.fill=result.bedding+result.around+result.protection;result.backfill=result.excavation-result.pipe-result.fill;return result;
}
function pitsOverlap(a,b){const z=Math.min(a.w.ground,b.w.ground),low=Math.max(a.g.pitBottom,b.g.pitBottom);if(z<=low)return false;const outline=item=>rectangleVertices(item.w,item.g.width+2*item.g.m*(z-item.g.pitBottom),item.g.length+2*item.g.m*(z-item.g.pitBottom),item.g.rotation);return rectanglesOverlap(outline(a),outline(b))}
function lineIntersection(a,b,c,d){const den=(b.x-a.x)*(d.y-c.y)-(b.y-a.y)*(d.x-c.x);if(Math.abs(den)<1e-9)return null;const t=((c.x-a.x)*(d.y-c.y)-(c.y-a.y)*(d.x-c.x))/den,u=((c.x-a.x)*(b.y-a.y)-(c.y-a.y)*(b.x-a.x))/den;return t>1e-7&&t<1-1e-7&&u>1e-7&&u<1-1e-7?{x:lerp(a.x,b.x,t),y:lerp(a.y,b.y,t)}:null}
export function setSlopeMode(e,res,section,mode){
 if(mode===section.slopeMode)return;
 if(!['angles','top'].includes(mode))throw Error('Неизвестный способ задания откосов.');
 const c=crossSection(e,res,section,section.a*res.length);
 if(![c.left,c.right,c.depth,c.top].every(Number.isFinite)||c.depth<=0)throw Error('Сначала исправьте глубину и откосы траншеи.');
 if(mode==='top'){
  if(Math.abs(c.left-c.right)>1e-7)throw Error('Ширина поверху задаёт симметричные откосы. Сначала задайте одинаковые углы слева и справа.');
  section.topWidth=c.top;
 }else{section.left=degrees(c.left);section.right=degrees(c.right)}
 section.slopeMode=mode;
}
export function calculateNetwork(p,options={}){
 const wells={},edges={},errors=[],warnings=[],issues=inspectNetwork(p,{resolveEdge,wellGeometry,atStation,crossSection,pitInterval}).map(v=>v.code==='trench-overlap'?{...v,severity:'info',jointStatus:'pending'}:v);const soilTotals=Object.fromEntries(p.soils.map(s=>[s.id,0]));
 for(const w of p.wells){const g=wellGeometry(w,p),ownErrors=[...new Set([...validateWell(p,w),...issues.filter(v=>v.kind==='well'&&v.objectId===w.id&&v.severity==='error').map(v=>v.message)])];wells[w.id]={...assignBackfill(g,w),errors:ownErrors,soils:wellSoils(p,w,g)};for(const x of ownErrors)errors.push(w.name+': '+x)}
 const pits=p.wells.filter(isPhysicalWell).map(w=>({w,g:wellGeometry(w,p)}));
 for(let i=0;i<pits.length;i++)for(let j=i+1;j<pits.length;j++)if(pitsOverlap(pits[i],pits[j])){
  const message='Пересекаются котлованы «'+pits[i].w.name+'» и «'+pits[j].w.name+'». Уточните границы выемки; свод заблокирован.';errors.push(message);
  const pair=[pits[i],pits[j]],z=Math.min(...pair.map(v=>v.w.ground)),polygon=clipPolygon(...pair.map(v=>rectangleVertices(v.w,v.g.width+2*v.g.m*(z-v.g.pitBottom),v.g.length+2*v.g.m*(z-v.g.pitBottom),v.g.rotation))),location=polygon.length?[0,1].map(k=>polygon.reduce((n,v)=>n+v[k],0)/polygon.length):[(pair[0].w.x+pair[1].w.x)/2,(pair[0].w.y+pair[1].w.y)/2];
  for(const w of pair.map(v=>v.w)){wells[w.id].errors.push(message);issues.push({code:'pit-overlap',severity:'error',kind:'well',objectId:w.id,message,related:pair.map(v=>v.w.id).filter(id=>id!==w.id),polygon,location,paths:['x','y','pitMargin','pitSlope'].map(k=>'wells.'+p.wells.indexOf(w)+'.'+k),tab:'excavation'})}
 }
 for(const e of p.edges){try{const res=resolveEdge(p,e),ownErrors=[...new Set([...validateEdge(p,e,res),...issues.filter(v=>v.kind==='edge'&&v.objectId===e.id&&v.severity==='error').map(v=>v.message),...[res.from,res.to].flatMap(w=>(wells[w.id]?.errors||[]).filter(message=>!issues.some(v=>v.kind==='edge'&&v.objectId===e.id&&v.message===message)&&!issues.some(v=>v.code==='rect-port-normal'&&v.kind==='well'&&v.objectId===w.id&&v.message===message)).slice(0,1).map(message=>'Исправьте параметры колодца «'+w.name+'»: '+message))])];const r=ownErrors.length?null:integrateEdge(p,e,res,options);edges[e.id]={...assignBackfill(r,e),res,errors:ownErrors};for(const x of ownErrors)errors.push(e.name+': '+x)}catch(error){edges[e.id]={errors:[error.message]};errors.push(e.name+': '+error.message)}}

 const joints=[],jointRegions=[],numerical=[];
 // Solve whole connected overlap groups; a triple overlap must never be treated as three pair subtractions.
 const pending=issues.filter(v=>v.code==='trench-overlap'),groups=[];for(const issue of pending){const ids=new Set([issue.objectId,...(issue.related||[])]),matches=groups.filter(g=>[...ids].some(id=>g.has(id)));for(const g of matches){for(const id of g)ids.add(id);groups.splice(groups.indexOf(g),1)}groups.push(ids)}
 for(const ids of groups){const members=p.edges.filter(e=>ids.has(e.id)),ready=members.every(e=>edges[e.id]&&!edges[e.id].errors.length),regions=pending.filter(v=>ids.has(v.objectId));if(!ready){for(const v of regions){v.message='Заполните исходные данные участков для расчёта общей выемки.';v.jointStatus='pending'}continue}
  try{const union=integrateJointTrenches(p,members,{resolveEdge,crossSection,wellGeometry,pitInterval},options);numerical.push(union.numerical);
   for(const e of members){const old=edges[e.id];edges[e.id]={...old,...union.edges[e.id],excluded:old.excluded,grossExcavation:old.excavation,sharedExcavation:union.joints.filter(v=>v.edgeIds.includes(e.id)).reduce((n,v)=>n+v.excavation,0)}}
   joints.push(...union.joints);for(const v of regions){v.jointStatus='calculated';if(!jointRegions.some(r=>r.message===v.message))jointRegions.push({...v})}
   for(const conflict of union.conflicts){const names=conflict.edgeIds.map(id=>p.edges.find(e=>e.id===id).name),soilNames=conflict.soilIds.map(id=>p.soils.find(v=>v.id===id)?.name||'не указан'),message='В общей выемке участков «'+names.join('» и «')+'» в одном месте указаны разные грунты: '+soilNames.join(' / ')+'. Согласуйте слои грунта.';errors.push(message);for(const joint of union.joints)if(joint.edgeIds.some(id=>conflict.edgeIds.includes(id)))joint.errors.push(message);for(const id of conflict.edgeIds){edges[id].errors.push(message);issues.push({code:'joint-soil-conflict',severity:'error',kind:'edge',objectId:id,related:conflict.edgeIds.filter(v=>v!==id),message,paths:['edges.'+p.edges.findIndex(e=>e.id===id)+'.layers'],tab:'soils',location:conflict.location,soilIds:conflict.soilIds})}}
   for(const conflict of union.backfillConflicts||[]){const message='В общей части траншей заданы разные материалы засыпки. Выберите одинаковый материал у участков «'+conflict.edgeIds.map(id=>p.edges.find(e=>e.id===id).name).join('» и «')+'».';errors.push(message);for(const id of conflict.edgeIds){edges[id].errors.push(message);issues.push({code:'joint-backfill-conflict',location:conflict.location,severity:'error',kind:'edge',objectId:id,related:conflict.edgeIds.filter(v=>v!==id),message,paths:['edges.'+p.edges.findIndex(e=>e.id===id)+'.backfillSource'],tab:'bedding'})}for(const joint of union.joints)if(joint.edgeIds.some(id=>conflict.edgeIds.includes(id)))joint.errors.push(message)}
  }catch(error){const message='Не удалось рассчитать общую выемку: '+error.message;errors.push(message);for(const v of regions){v.jointStatus='failed';v.severity='error';v.message=message}}
 }
 // Successfully calculated overlaps are quantities, not diagnostics requiring user correction.
 for(let i=issues.length-1;i>=0;i--)if(issues[i].code==='trench-overlap'&&issues[i].jointStatus==='calculated')issues.splice(i,1);
 for(const [kind,items,values]of [['well',p.wells,wells],['edge',p.edges,edges]])for(const item of items){const r=values[item.id];if(!r)continue;if(!r.errors.length&&['excavation','backfill','pipe','fill'].some(k=>!Number.isFinite(r[k])||r[k]<-1e-6)){r.errors.push('Некорректный баланс объёмов: проверьте геометрию и размеры.');errors.push(item.name+': '+r.errors.at(-1))}for(const message of r.errors)if(!issues.some(v=>v.kind===kind&&v.objectId===item.id&&v.message===message))issues.push({code:'geometry',severity:'error',kind,objectId:item.id,message,paths:issuePaths(p,kind,item.id,message),tab:/грунт|сло[ий]/i.test(message)?'soils':'geometry'})}
 const total={excavation:0,backfill:0,nativeBackfill:0,importedBackfill:0,pipe:0,fill:0,soils:soilTotals};for(const r of [...Object.values(wells),...Object.values(edges),...joints])if(!r.errors.length){for(const k of ['excavation','backfill','nativeBackfill','importedBackfill','pipe','fill'])total[k]+=r[k]||0;for(const [id,v]of Object.entries(r.soils||{}))soilTotals[id]=(soilTotals[id]||0)+v}
 const soilSum=sum(Object.values(soilTotals));if(!errors.length&&Math.abs(soilSum-total.excavation)>.001)errors.push('Слои грунта не покрывают весь объём выемки.');
 warnings.push('Расчёт траншей — численное интегрирование. Котлованы исключаются из траншей по геометрии. Общая выемка пересекающихся траншей учтена один раз отдельными строками стыков.');
 for(const message of errors)if(!issues.some(v=>message===v.message||message.endsWith(': '+v.message)))issues.push({code:'network',severity:'error',kind:'network',objectId:p.id,message,paths:[],tab:'geometry'});
 for(const issue of issues.filter(v=>v.severity==='warning'))warnings.push(issue.message);
 enrichIssues(p,issues,{wellGeometry,resolveEdge,crossSection});
 return {wells,edges,joints,jointRegions,numerical,preview:!!options.preview,total,issues,errors:[...new Set(errors)],warnings,valid:!errors.length};
}
export function validateProject(input){
 if(!input||![3,VERSION].includes(input.version)||!Array.isArray(input.wells)||!Array.isArray(input.edges)||!Array.isArray(input.soils))throw Error('Ожидается JSON схемы версии 3 или 4.');
 if(input.wells.length>150||input.edges.length>200||input.soils.length>40)throw Error('Превышен размер проекта: 150 узлов, 200 участков, 40 грунтов.');
 const allIds=new Set();const id=x=>{if(typeof x!=='string'||!x||x.length>150||allIds.has(x))throw Error('Повторяющийся или некорректный ID.');allIds.add(x)};
 const finite=(x,label)=>{if(!Number.isFinite(x)||Math.abs(x)>1e8)throw Error('Некорректное число: '+label)};
 if(typeof input.name!=='string'||input.name.length>300)throw Error('Некорректное название проекта.');
 for(const soil of input.soils){id(soil.id);if(typeof soil.name!=='string'||!/^#[a-f\d]{6}$/i.test(soil.color)||!['I','II','III','IV','V','VI'].includes(soil.group))throw Error('Некорректный справочник грунтов.')}
 for(const w of input.wells){validateBackfill(w);if(w.workingHeightOverride!==undefined){finite(w.workingHeightOverride,'Рабочая часть');if(w.workingHeightOverride<=0)throw Error('Рабочая часть должна быть больше нуля.')}id(w.id);if(w.rotationEdge!==undefined&&(typeof w.rotationEdge!=='string'||w.rotationEdge.length>150))throw Error('Некорректная опорная труба.');if(!['well','endpoint',undefined].includes(w.kind))throw Error('Неизвестный тип узла.');for(const key of ['height','rotation','zeroAngle'])if(w[key]!==undefined)finite(w[key],key);if(w.heightMode!==undefined&&!['total','parts'].includes(w.heightMode))throw Error('Некорректный режим высоты.');if(w.rotationMode!==undefined&&!['manual','pipe'].includes(w.rotationMode))throw Error('Некорректный режим поворота.');if(typeof w.name!=='string'||!Array.isArray(w.ports)||w.ports.length>40||!Array.isArray(w.layers)||w.layers.length>40)throw Error('Некорректный узел.');for(const key of ['x','y','ground','diameter','width','length','wall','workingHeight','neckHeight','neckDiameter','neckWall','neckX','neckY','slab','base','baseProjection','pitMargin','pitSlope','pad','padMargin'])finite(w[key],key);for(const port of w.ports){if(port.wall!==undefined&&(!Number.isInteger(port.wall)||port.wall<0||port.wall>3))throw Error('Некорректная стена подключения.');id(port.id);finite(port.invert,'отметка подключения');if(port.bearing!==null)finite(port.bearing,'угол подключения')}for(const l of w.layers)finite(l.bottom,'граница грунта')}
 for(const e of input.edges){validateBackfill(e);id(e.id);if(typeof e.name!=='string'||!e.from||!e.to||!Array.isArray(e.sections)||!e.sections.length||e.sections.length>100||!Array.isArray(e.waypoints)||e.waypoints.length>100||!Array.isArray(e.layers)||e.layers.length>40)throw Error('Некорректный участок.');finite(e.diameter,'диаметр');finite(e.pipeWall,'стенка');for(const v of e.waypoints){if(v.autoPort!==undefined&&![e.from.well,e.to.well].includes(v.autoPort))throw Error('Некорректный подвод к стене.');id(v.id);for(const k of ['x','y'])finite(v[k],k);for(const k of ['ground','invert'])if(v[k]!==null)finite(v[k],k)}for(const v of e.sections){id(v.id);if(v.aroundMaterial!==undefined&&(typeof v.aroundMaterial!=='string'||!v.aroundMaterial.trim()||v.aroundMaterial.length>180))throw Error('Укажите материал обсыпки.');if(v.beddingMaterial!==undefined&&(typeof v.beddingMaterial!=='string'||v.beddingMaterial.length>100))throw Error('Некорректный материал основания.');for(const k of ['a','b','width','left','right','topWidth','bedding','protection','casing','casingWall'])finite(v[k],k)}for(const l of e.layers){finite(l.start,'граница грунта');finite(l.end,'граница грунта')}}
 const used=new Set();
 for(const e of input.edges){validateBackfill(e);
  if(e.from.well===e.to.well)throw Error('Участок должен соединять разные колодцы.');
  for(const end of [e.from,e.to]){const w=input.wells.find(w=>w.id===end.well);if(!w||!w.ports.some(v=>v.id===end.port))throw Error('Не найдено подключение участка «'+e.name+'».');const key=JSON.stringify([w.id,end.port]);if(used.has(key))throw Error('Одно подключение занято несколькими участками.');used.add(key)}
 }
 return input;
}
