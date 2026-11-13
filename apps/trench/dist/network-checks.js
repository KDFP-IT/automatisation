import {isPhysicalWell,localPoint,worldPoint,rectangularPort} from './node-geometry.js';
// Geometric coordination only. No assumed hydraulic or regulatory thresholds.
const EPS=1e-7;
const dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0),sub=(a,b)=>a.map((v,i)=>v-b[i]);
const mix=(a,b,t)=>a.map((v,i)=>v+(b[i]-v)*t);
export function closestSegments(a,b,c,d){
 const u=sub(b,a),v=sub(d,c),w=sub(a,c),A=dot(u,u),B=dot(u,v),C=dot(v,v),D=dot(u,w),E=dot(v,w),den=A*C-B*B;
 let s=C<=EPS*EPS&&A>EPS*EPS?Math.max(0,Math.min(1,-D/A)):den>EPS*EPS?Math.max(0,Math.min(1,(B*E-C*D)/den)):0;
 let t=C>EPS*EPS?(B*s+E)/C:0;
 if(t<0){t=0;s=A>EPS*EPS?Math.max(0,Math.min(1,-D/A)):0}else if(t>1){t=1;s=A>EPS*EPS?Math.max(0,Math.min(1,(B-D)/A)):0}
 const p=mix(a,b,s),q=mix(c,d,t);return {s,t,p,q,distance:Math.hypot(...sub(p,q))};
}
const cross=(a,b,c)=>(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);
const area=poly=>poly.reduce((sum,a,i)=>{const b=poly[(i+1)%poly.length];return sum+a[0]*b[1]-a[1]*b[0]},0)/2;
export function clipPolygon(subject,clip){
 let out=subject;if(area(clip)<0)clip=[...clip].reverse();
 for(let i=0;i<clip.length&&out.length;i++){const a=clip[i],b=clip[(i+1)%clip.length],input=out;out=[];let previous=input.at(-1),prevInside=cross(a,b,previous)>=-EPS;
  for(const point of input){const inside=cross(a,b,point)>=-EPS;if(inside!==prevInside){const u=cross(a,b,previous),v=cross(a,b,point),t=u/(u-v);out.push([previous[0]+(point[0]-previous[0])*t,previous[1]+(point[1]-previous[1])*t])}if(inside)out.push(point);previous=point;prevInside=inside}
 }return out;
}
export function inspectNetwork(p,{resolveEdge,wellGeometry,atStation,crossSection,pitInterval}){
 const issues=[],resolved=new Map(),occupants=new Map();
 const add=(code,severity,kind,objectId,message,paths=[],tab='geometry',related=[])=>issues.push({id:code+'-'+issues.length,code,severity,kind,objectId,message,paths,tab,related});
 const edgePath=e=>'edges.'+p.edges.indexOf(e),wellPath=w=>'wells.'+p.wells.indexOf(w);
 const insideBody=(w,point)=>{const g=wellGeometry(w,p),local=localPoint(w,point[0],point[1],g.rotation);return point[2]>=g.bottom-EPS&&point[2]<=g.bodyTop+EPS&&(w.shape==='round'?Math.hypot(point[0]-w.x,point[1]-w.y)<=g.bodyW/2+EPS:Math.abs(local[0])<=g.bodyW/2+EPS&&Math.abs(local[1])<=g.bodyL/2+EPS)};
 for(const e of p.edges){
  let res;try{res=resolveEdge(p,e)}catch{continue}resolved.set(e.id,res);if(!Number.isFinite(res.length)||res.length<EPS)continue;
  for(const [side,w,port]of [['from',res.from,res.portA],['to',res.to,res.portB]]){
   const key=JSON.stringify([w.id,port.id]),previous=occupants.get(key);if(previous){for(const item of [previous,e])add('port-reused','error','edge',item.id,'Одно подключение колодца «'+w.name+'» занято несколькими трубами. Создайте отдельный вход/выход.',[edgePath(item)+'.'+(item.from.well===w.id?'from':'to')], 'geometry',[w.id])}else occupants.set(key,e);
   if(!isPhysicalWell(w))continue;
   if(w.shape==='rect'){const port=rectangularPort(p,w,e);if(!port.valid){const message='Труба «'+e.name+'» должна выходить из центра стены колодца «'+w.name+'» под 90° к стене. Выберите стену подключения или исправьте направление трубы.';const paths=[edgePath(e)+'.waypoints',wellPath(w)+'.rotation',wellPath(w)+'.rotationMode'];add('rect-port-normal','error','edge',e.id,message,paths,'geometry',[w.id]);add('rect-port-normal','error','well',w.id,message,paths,'geometry',[e.id])}}

   const idx=side==='from'?1:res.points.length-1,a=res.points[idx-1],b=res.points[idx],ds=b.s-a.s,grade=(b.invert-a.invert)/ds,g=wellGeometry(w,p),diameter=e.diameter*Math.sqrt(1+grade*grade);
   const paths=[edgePath(e)+'.diameter',wellPath(w)+'.ports.'+w.ports.indexOf(port)+'.invert',wellPath(w)+'.workingHeight',wellPath(w)+'.neckHeight',wellPath(w)+'.slab'];
   if(Number.isFinite(diameter)&&(port.invert<g.floor-EPS||port.invert+diameter>g.bodyTop-w.slab+EPS)){
    const message='Труба «'+e.name+'» не помещается между внутренним дном и перекрытием колодца «'+w.name+'». Проверьте отметку входа и высоту рабочей части.';
    add('port-height','error','edge',e.id,message,paths,'geometry',[w.id]);add('port-height','error','well',w.id,message,paths,'geometry',[e.id]);
   }
   const [ldx,ldy]=localPoint({x:0,y:0},b.x-a.x,b.y-a.y,g.rotation),ux=Math.abs(ldx)/ds,uy=Math.abs(ldy)/ds,tx=ux>EPS?w.width/2/ux:Infinity,ty=uy>EPS?w.length/2/uy:Infinity;
   const span=w.shape==='round'?w.diameter:tx<ty?2*Math.max(0,w.length/2-uy*tx)*ux:2*Math.max(0,w.width/2-ux*ty)*uy;
   if(e.diameter>span+EPS){const message='Диаметр трубы «'+e.name+'» больше внутреннего габарита колодца «'+w.name+'».';const dims=[edgePath(e)+'.diameter',wellPath(w)+'.diameter',wellPath(w)+'.width',wellPath(w)+'.length'];add('port-width','error','edge',e.id,message,dims,'geometry',[w.id]);add('port-width','error','well',w.id,message,dims,'geometry',[e.id])}
   // Absolute levels are shared, geology is independent: discrepancies need confirmation, never silent copying.
   const end=side==='from'?'start':'end';if(e.layers.length&&w.layers.length&&(e.layers.length!==w.layers.length||e.layers.some((l,i)=>l.soil!==w.layers[i]?.soil||Math.abs(l[end]-w.layers[i].bottom)>.001)))add('geology-junction','warning','edge',e.id,'Грунты у колодца «'+w.name+'» отличаются от грунтов участка. Проверьте привязку слоёв.',[edgePath(e)+'.layers',wellPath(w)+'.layers'],'soils',[w.id]);
  }
  for(let i=1;i<res.points.length-1;i++){
   const a=res.points[i-1],b=res.points[i],c=res.points[i+1],u=[b.x-a.x,b.y-a.y],v=[c.x-b.x,c.y-b.y];
   if(Math.abs(u[0]*v[1]-u[1]*v[0])<EPS&&dot(u,v)<-EPS)add('route-reversal','error','edge',e.id,'Трасса разворачивается назад по тому же звену. Исправьте вершину '+i+'.',[edgePath(e)+'.waypoints']);
  }
  for(let i=1;i<res.points.length;i++){
   const a=res.points[i-1],b=res.points[i],ds=b.s-a.s;if(ds<EPS)continue;
   if(b.invert>a.invert+EPS)add('rising-pipe','warning','edge',e.id,'Подъём трубы по направлению «'+res.from.name+' → '+res.to.name+'» на '+a.s.toFixed(2)+'–'+b.s.toFixed(2)+' м. Проверьте направление и профиль.',[edgePath(e)+'.waypoints'],'geometry');
   if(Math.abs(b.invert-a.invert)<EPS)add('flat-pipe','warning','edge',e.id,'Горизонтальная труба на '+a.s.toFixed(2)+'–'+b.s.toFixed(2)+' м. Убедитесь, что это предусмотрено проектом.',[edgePath(e)+'.waypoints']);
  }
  // Validate coverage at every zone/profile breakpoint, not just at route vertices.
  for(let si=0;si<e.sections.length;si++){
   const section=e.sections[si];if(section.method!=='trench'||!(section.a>=0&&section.b>section.a&&section.b<=1))continue;
   const stations=[section.a*res.length,section.b*res.length,...res.points.filter(v=>v.s>section.a*res.length&&v.s<section.b*res.length).map(v=>v.s)];
   const last=e.layers.at(-1);if(last&&stations.some(s=>{const c=crossSection(e,res,section,s),depth=last.start+(last.end-last.start)*s/res.length;return Number.isFinite(c.depth)&&depth<c.depth-EPS}))add('soil-zone-coverage','error','edge',e.id,'Грунты не покрывают дно траншеи в зоне '+(si+1)+'. Увеличьте глубину последнего слоя или уточните профиль.',[edgePath(e)+'.layers'],'soils');
  }
 }
 // 3D swept-axis envelopes, split at each pipe bend and casing boundary.
 const segments=[];
 for(const e of p.edges){const res=resolved.get(e.id);if(!res||!Number.isFinite(res.length)||res.length<=EPS||!(e.diameter>0))continue;
  for(let pi=1;pi<res.points.length;pi++)for(const section of e.sections){
   const lo=Math.max(res.points[pi-1].s,section.a*res.length),hi=Math.min(res.points[pi].s,section.b*res.length);if(!(hi-lo>EPS))continue;
   const a=atStation(res,lo),b=atStation(res,hi),grade=(b.invert-a.invert)/(hi-lo),offset=e.diameter/2*Math.sqrt(1+grade*grade),radius=(section.casing||e.diameter)/2;
   const start=[a.x,a.y,a.invert+offset],end=[b.x,b.y,b.invert+offset];if(![...start,...end,radius].every(Number.isFinite))continue;
   segments.push({e,pi,lo,hi,a:start,b:end,radius,section,res});
  }
 }
 const seen=new Set();
 for(let i=0;i<segments.length;i++)for(let j=i+1;j<segments.length;j++){
  const a=segments[i],b=segments[j],self=a.e===b.e;if(self&&Math.abs(a.pi-b.pi)<=1)continue;
  if([0,1,2].some(k=>Math.max(a.a[k],a.b[k])+a.radius<Math.min(b.a[k],b.b[k])-b.radius||Math.max(b.a[k],b.b[k])+b.radius<Math.min(a.a[k],a.b[k])-a.radius))continue;
  const pair=JSON.stringify([a.e.id,b.e.id].sort()),hit=closestSegments(a.a,a.b,b.a,b.b);if(hit.distance>=a.radius+b.radius-EPS)continue;
  const midpoint=mix(hit.p,hit.q,.5),common=p.wells.filter(w=>[a.e.from.well,a.e.to.well].includes(w.id)&&[b.e.from.well,b.e.to.well].includes(w.id));
  if(!self&&common.some(w=>isPhysicalWell(w)?insideBody(w,midpoint):Math.hypot(midpoint[0]-w.x,midpoint[1]-w.y,midpoint[2]-(w.ports[0]?.invert+a.e.diameter/2))<=Math.max(a.radius,b.radius)+EPS))continue;
  if(seen.has(pair))continue;seen.add(pair);
  const message=self?'Самопересечение трубы или футляра на участке «'+a.e.name+'».':'Пересекаются наружные габариты труб/футляров «'+a.e.name+'» и «'+b.e.name+'». Проверьте план и высотные отметки.';
  for(const e of self?[a.e]:[a.e,b.e]){add(self?'pipe-self-clash':'pipe-clash','error','edge',e.id,message,[edgePath(e)+'.waypoints',edgePath(e)+'.diameter',edgePath(e)+'.sections'],'geometry',self?[]:[e===a.e?b.e.id:a.e.id]);Object.assign(issues.at(-1),{location:midpoint,clash:{distance:hit.distance,required:a.radius+b.radius,overlap:a.radius+b.radius-hit.distance,edges:[{id:a.e.id,station:a.lo+(a.hi-a.lo)*hit.s},{id:b.e.id,station:b.lo+(b.hi-b.lo)*hit.t}],points:[hit.p,hit.q]}})}
 }
 // Confirm a positive 3D soil overlap in clipped trench footprints, excluding well pits.
 const trenchPairs=new Set(),pits=p.wells.filter(isPhysicalWell).map(w=>({w,g:wellGeometry(w,p)}));
 const footprint=segment=>{
  const c=atStation(segment.res,(segment.lo+segment.hi)/2),a=crossSection(segment.e,segment.res,segment.section,segment.lo),b=crossSection(segment.e,segment.res,segment.section,segment.hi),n=[-c.dy,c.dx];
  const offset=(point,t)=>[point.x+n[0]*t,point.y+n[1]*t];return [offset(a,-a.width/2-a.left*a.depth),offset(a,a.width/2+a.right*a.depth),offset(b,b.width/2+b.right*b.depth),offset(b,-b.width/2-b.left*b.depth)];
 };
 const interval=(segment,point)=>{const a=segment.a,b=segment.b,dx=b[0]-a[0],dy=b[1]-a[1],t=Math.max(0,Math.min(1,((point[0]-a[0])*dx+(point[1]-a[1])*dy)/(dx*dx+dy*dy))),c=crossSection(segment.e,segment.res,segment.section,segment.lo+t*(segment.hi-segment.lo)),lat=-(point[0]-c.x)*c.dy+(point[1]-c.y)*c.dx;return [c.bottom+(lat<-c.width/2?(-lat-c.width/2)/c.left:lat>c.width/2?(lat-c.width/2)/c.right:0),c.ground]};
 const remaining=(lo,hi,point)=>{
  let intervals=[[lo,hi]];for(const {w,g}of pits){const cut=pitInterval?pitInterval(w,g,point[0],point[1]):null;if(!cut)continue;const bottom=cut[0];if(!(bottom<w.ground))continue;
   intervals=intervals.flatMap(([a,b])=>{if(w.ground<=a||bottom>=b)return [[a,b]];return [...(a<bottom?[[a,bottom]]:[]),...(w.ground<b?[[w.ground,b]]:[])]});
  }return intervals.some(([a,b])=>b-a>1e-5);
 };
 const footprints=new Map(segments.filter(s=>s.section.method==='trench').map(s=>[s,footprint(s)]));
 const trenches=[...footprints.keys()];
 for(let i=0;i<trenches.length;i++)for(let j=i+1;j<trenches.length;j++){
  const a=trenches[i],b=trenches[j],self=a.e===b.e;if(self&&Math.abs(a.pi-b.pi)<=1)continue;
  const key=JSON.stringify([a.e.id,b.e.id].sort());if(trenchPairs.has(key))continue;
  const pa=footprints.get(a),pb=footprints.get(b);if(!pa.flat().concat(pb.flat()).every(Number.isFinite))continue;
  if([0,1].some(k=>Math.max(...pa.map(p=>p[k]))<=Math.min(...pb.map(p=>p[k]))+EPS||Math.max(...pb.map(p=>p[k]))<=Math.min(...pa.map(p=>p[k]))+EPS))continue;
  const polygon=clipPolygon(pa,pb);if(polygon.length<3||Math.abs(area(polygon))<1e-6)continue;
  const centre=[0,1].map(k=>polygon.reduce((n,p)=>n+p[k],0)/polygon.length),samples=[centre,...polygon.map(p=>[p[0]*.99+centre[0]*.01,p[1]*.99+centre[1]*.01])];
  if(!samples.some(point=>{const x=interval(a,point),y=interval(b,point),lo=Math.max(x[0],y[0]),hi=Math.min(x[1],y[1]);return hi>lo+EPS&&remaining(lo,hi,point)}))continue;trenchPairs.add(key);
  const message=self?'Перекрываются части траншеи «'+a.e.name+'» за пределами котлованов.':'Перекрываются объёмы траншей «'+a.e.name+'» и «'+b.e.name+'» за пределами котлованов. Уточните совместную выемку: автоматическое объединение объёмов пока не выполняется.';
  for(const e of self?[a.e]:[a.e,b.e]){add('trench-overlap','error','edge',e.id,message,[edgePath(e)+'.sections',edgePath(e)+'.waypoints'],'geometry',self?[]:[e===a.e?b.e.id:a.e.id]);Object.assign(issues.at(-1),{polygon,location:centre,sectionsByEdge:{[a.e.id]:a.e.sections.indexOf(a.section),[b.e.id]:b.e.sections.indexOf(b.section)}})}
 }
 // Distinct ports must also have distinct physical openings at the internal wall.
 for(const w of p.wells.filter(isPhysicalWell)){const openings=[];
  for(const e of p.edges){const res=resolved.get(e.id);if(!res)continue;const from=e.from.well===w.id,to=e.to.well===w.id;if(!from&&!to)continue;
   const point=from?res.points[1]:res.points.at(-2),port=from?res.portA:res.portB,dx=point.x-w.x,dy=point.y-w.y,len=Math.hypot(dx,dy);if(len<EPS)continue;
   const [ldx,ldy]=localPoint({x:0,y:0},dx,dy,wellGeometry(w,p).rotation),ux=ldx/len,uy=ldy/len,distance=w.shape==='round'?w.diameter/2:Math.min(Math.abs(ux)>EPS?w.width/2/Math.abs(ux):Infinity,Math.abs(uy)>EPS?w.length/2/Math.abs(uy):Infinity),grade=(point.invert-port.invert)/len;
   openings.push({e,point:[w.x+dx/len*distance,w.y+dy/len*distance,port.invert+grade*distance+e.diameter/2*Math.sqrt(1+grade*grade)],radius:e.diameter/2});
  }
  for(let i=0;i<openings.length;i++)for(let j=i+1;j<openings.length;j++){const a=openings[i],b=openings[j];if(Math.hypot(...sub(a.point,b.point))>=a.radius+b.radius-EPS)continue;
   const message='Перекрываются входы труб «'+a.e.name+'» и «'+b.e.name+'» в колодце «'+w.name+'». Разведите направления или отметки подключений.';
   const details={well:w.id,distance:Math.hypot(...sub(a.point,b.point)),required:a.radius+b.radius,edges:[a.e.id,b.e.id]};add('port-openings','error','well',w.id,message,[wellPath(w)+'.ports',wellPath(w)+'.diameter',wellPath(w)+'.width',wellPath(w)+'.length']);Object.assign(issues.at(-1),{location:mix(a.point,b.point,.5),opening:details});for(const e of [a.e,b.e]){add('port-openings','error','edge',e.id,message,[edgePath(e)+'.diameter',edgePath(e)+'.waypoints',wellPath(w)+'.ports'],'geometry',[w.id]);Object.assign(issues.at(-1),{location:mix(a.point,b.point,.5),opening:details})}
  }
 }
 // Distance from an axis segment to the actual solid body of an unrelated well.
 const hitWells=new Set();
 for(const segment of segments)for(const w of p.wells.filter(isPhysicalWell)){if([segment.e.from.well,segment.e.to.well].includes(w.id))continue;const g=wellGeometry(w,p),r=segment.radius,key=JSON.stringify([segment.e.id,w.id]);if(hitWells.has(key))continue;
  if(Math.min(...[segment.a[2],segment.b[2]])-r>g.bodyTop||Math.max(segment.a[2],segment.b[2])+r<g.bottom||Math.min(segment.a[0],segment.b[0])-r>w.x+Math.hypot(g.bodyW,g.bodyL)/2||Math.max(segment.a[0],segment.b[0])+r<w.x-Math.hypot(g.bodyW,g.bodyL)/2||Math.min(segment.a[1],segment.b[1])-r>w.y+Math.hypot(g.bodyW,g.bodyL)/2||Math.max(segment.a[1],segment.b[1])+r<w.y-Math.hypot(g.bodyW,g.bodyL)/2)continue;
  const distance=t=>{const q=mix(segment.a,segment.b,t),local=localPoint(w,q[0],q[1],g.rotation),z=Math.max(g.bottom-q[2],q[2]-g.bodyTop,0),x=Math.max(Math.abs(local[0])-g.bodyW/2,0),y=Math.max(Math.abs(local[1])-g.bodyL/2,0),h=w.shape==='round'?Math.max(Math.hypot(q[0]-w.x,q[1]-w.y)-g.bodyW/2,0):Math.hypot(x,y);return Math.hypot(h,z)};
  let lo=0,hi=1;for(let k=0;k<40;k++){const a=lo+(hi-lo)/3,b=hi-(hi-lo)/3;if(distance(a)<distance(b))hi=b;else lo=a}if(Math.min(distance(0),distance(1),distance((lo+hi)/2))>=r-EPS)continue;hitWells.add(key);
  const message='Труба/футляр «'+segment.e.name+'» пересекает рабочую часть колодца «'+w.name+'», к которому не подключена.';
  const nearest=[0,1,(lo+hi)/2].map(t=>({t,d:distance(t)})).sort((a,b)=>a.d-b.d)[0],location=mix(segment.a,segment.b,nearest.t),pipeWell={well:w.id,edge:segment.e.id,station:segment.lo+(segment.hi-segment.lo)*nearest.t,distance:nearest.d,radius:segment.radius};add('pipe-well-clash','error','edge',segment.e.id,message,[edgePath(segment.e)+'.waypoints'],'geometry',[w.id]);Object.assign(issues.at(-1),{location,pipeWell});add('pipe-well-clash','error','well',w.id,message,[wellPath(w)+'.x',wellPath(w)+'.y'],'geometry',[segment.e.id]);Object.assign(issues.at(-1),{location,pipeWell});
 }
 // Names and isolated nodes are informational; they do not determine flow or numerical validity.
 for(const kind of ['well','edge']){const items=kind==='well'?p.wells:p.edges;for(const item of items){if(!item.name.trim())add('empty-name','warning',kind,item.id,'Задайте обозначение объекта.');else if(items.some(v=>v!==item&&v.name.trim()===item.name.trim()))add('duplicate-name','warning',kind,item.id,'Обозначение «'+item.name+'» повторяется. Различайте объекты на схеме.');if(kind==='well'&&isPhysicalWell(item)&&!p.edges.some(e=>e.from.well===item.id||e.to.well===item.id))add('isolated-well','warning',kind,item.id,'Колодец не соединён с участками. Его котлован учитывается отдельно.') }}
 return issues;
}

export function issuePaths(p,kind,id,message){
 const list=kind==='well'?p.wells:p.edges,index=list.findIndex(v=>v.id===id),base=(kind==='well'?'wells.':'edges.')+index,item=list[index];if(!item)return [];
 if(/грунт|сло[ий]/i.test(message))return [base+'.layers'];
 if(kind==='well'){if(/Горловина/.test(message))return ['neckDiameter','neckX','neckY','diameter','width','length'].map(k=>base+'.'+k);if(/подготовка/i.test(message))return ['padMargin','pitMargin'].map(k=>base+'.'+k);return []}
 if(/стенки трубы/.test(message))return [base+'.diameter',base+'.pipeWall'];
 if(/внутреннем диаметре футляра/.test(message))return [base+'.diameter',...item.sections.flatMap((_,i)=>['casing','casingWall'].map(k=>base+'.sections.'+i+'.'+k))];
 const fields=/Углы откосов/.test(message)?['left','right']:/футляр/.test(message)?['casing','casingWall','width']:/Защитный/.test(message)?['protection']:/основание/.test(message)?['topWidth','width']:/отрез|Отрез/.test(message)?['a','b']:/откосами/.test(message)?['width','left','right']:/ширину траншеи/.test(message)?['width','bedding','protection']:[];
 return item.sections.flatMap((_,i)=>fields.map(k=>base+'.sections.'+i+'.'+k));
}
