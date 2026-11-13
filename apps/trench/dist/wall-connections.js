import {isPhysicalWell,nodeAngle,rectangularPort,normalizeAngle} from './node-geometry.js';
// Selected nodes follow the cursor; other wells stay put. Free endpoints may slide.
// Rectangular wells turn to a reference pipe instead of dragging a round neighbour.
export function preserveWallConnections(p,before,movedIds){
 const moved=new Set(movedIds),original=new Map(before.wells.map(w=>[w.id,w])),angles=new Map(before.wells.map(w=>[w.id,nodeAngle(before,w)])),connections=[];
 for(const e of before.edges){if(e.waypoints.length)continue;for(const side of ['from','to']){const w=original.get(e[side].well);if(!isPhysicalWell(w)||w.shape!=='rect')continue;const port=w.ports.find(v=>v.id===e[side].port),c=rectangularPort(before,w,e),wall=Number.isInteger(port?.wall)?port.wall:c.valid?c.wall:null;if(wall===null)continue;connections.push({a:w.id,b:e[side==='from'?'to':'from'].well,edge:e.id,wall,name:e.name})}}
 const reached=new Set(moved);let expanded=true;while(expanded){expanded=false;for(const c of connections)if(reached.has(c.a)||reached.has(c.b))for(const id of [c.a,c.b])if(!reached.has(id)){reached.add(id);expanded=true}}
 const points=new Map(p.wells.map(w=>{const source=moved.has(w.id)||!reached.has(w.id)?w:original.get(w.id);return [w.id,{x:source.x,y:source.y}]})),references=new Map();
 for(const w of before.wells.filter(w=>reached.has(w.id)&&isPhysicalWell(w)&&w.shape==='rect')){
  const linked=connections.filter(c=>c.a===w.id),group=linked.filter(c=>moved.has(c.b)),fixedWells=linked.filter(c=>!moved.has(c.b)&&isPhysicalWell(original.get(c.b))),candidates=group.length?group:moved.has(w.id)?fixedWells:[];
  if(!candidates.length)continue;
  const ref=candidates.find(c=>c.edge===w.rotationEdge)||candidates.find(c=>original.get(c.b).shape==='round')||candidates[0],a=points.get(w.id),b=points.get(ref.b),dx=b.x-a.x,dy=b.y-a.y;
  if(Math.hypot(dx,dy)<.01)throw Error('Колодец слишком близко к соседнему узлу. Отодвиньте его.');
  angles.set(w.id,normalizeAngle(Math.atan2(dy,dx)*180/Math.PI-ref.wall*90));references.set(w.id,ref);
 }
 const active=connections.filter(c=>reached.has(c.a)).map(c=>{const a=(angles.get(c.a)+c.wall*90)*Math.PI/180;return {...c,t:[-Math.sin(a),Math.cos(a)],d:[Math.cos(a),Math.sin(a)]}});
 if(!active.length)return [];
 // Fixed means fixed in XY, not fixed pipe bearing: round wells have no angular constraint.
 const fixed=new Set([...moved,...before.wells.filter(w=>isPhysicalWell(w)&&!moved.has(w.id)).map(w=>w.id)]);
 const residual=c=>{const a=points.get(c.a),b=points.get(c.b);return (b.x-a.x)*c.t[0]+(b.y-a.y)*c.t[1]};
 for(let pass=0;pass<512;pass++){let max=0;for(const c of active){const r=residual(c);max=Math.max(max,Math.abs(r));if(Math.abs(r)<1e-9)continue;const a=points.get(c.a),b=points.get(c.b),ma=fixed.has(c.a)?0:1,mb=fixed.has(c.b)?0:1,total=ma+mb;if(!total)continue;for(const k of ['x','y']){const t=c.t[k==='x'?0:1];a[k]+=r*t*ma/total;b[k]-=r*t*mb/total}}if(max<1e-8)break}
 const bad=active.find(c=>Math.abs(residual(c))>1e-6);if(bad){const anchor=original.get(bad.b);throw Error('Не получается сохранить 90°: «'+anchor.name+'» остаётся на месте. Добавьте его в группу для переноса или выберите другую стену.')}
 for(const c of active){const a=points.get(c.a),b=points.get(c.b);if((b.x-a.x)*c.d[0]+(b.y-a.y)*c.d[1]<.01)throw Error('Труба окажется с другой стороны стены. Выберите другую стену или уменьшите перемещение.')}
 const adjusted=[];for(const w of p.wells){const v=points.get(w.id);if(Math.hypot(w.x-v.x,w.y-v.y)>1e-8&&!moved.has(w.id))adjusted.push(w.name);w.x=v.x;w.y=v.y}
 for(const w of p.wells.filter(w=>reached.has(w.id)&&isPhysicalWell(w)&&w.shape==='rect')){const ref=references.get(w.id);if(ref){w.rotationMode='pipe';w.rotationEdge=ref.edge;w.rotation=normalizeAngle(-ref.wall*90)}else{w.rotationMode='manual';w.rotation=normalizeAngle(angles.get(w.id)-(w.zeroAngle||0))}}
 return adjusted;
}

