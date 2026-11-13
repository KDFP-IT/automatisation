export const isPhysicalWell=w=>w?.kind!=='endpoint';
export const normalizeAngle=v=>((v+180)%360+360)%360-180;
export function wellDimensions(w){const workingHeight=w.heightMode==='total'?(w.workingHeightOverride??1.8):w.workingHeight,neckHeight=w.heightMode==='total'?w.height-workingHeight-w.slab-w.base:w.neckHeight;return {workingHeight,neckHeight,height:workingHeight+neckHeight+w.slab+w.base}}
export function nodeAngle(p,w){
 const offset=w.rotation??0,zero=w.zeroAngle??0;
 if(w.rotationMode!=='pipe'||!p)return normalizeAngle(zero+offset);
 const edges=p.edges.filter(e=>e.from.well===w.id||e.to.well===w.id),e=edges.find(e=>e.id===w.rotationEdge)||edges[0];if(!e)return normalizeAngle(zero+offset);
 try{return normalizeAngle(referencePipeBearing(p,e,w.id)+offset)}catch{return normalizeAngle(zero+offset)}
}
export function localPoint(w,x,y,angle=0){const a=angle*Math.PI/180,dx=x-w.x,dy=y-w.y;return [dx*Math.cos(a)+dy*Math.sin(a),-dx*Math.sin(a)+dy*Math.cos(a)]}
export function worldPoint(w,x,y,angle=0){const a=angle*Math.PI/180;return [w.x+x*Math.cos(a)-y*Math.sin(a),w.y+x*Math.sin(a)+y*Math.cos(a)]}
export function rectangleVertices(w,width,length,angle=0){return [[-width/2,-length/2],[width/2,-length/2],[width/2,length/2],[-width/2,length/2]].map(([x,y])=>worldPoint(w,x,y,angle))}
export function rectanglesOverlap(a,b){for(const poly of [a,b])for(let i=0;i<4;i++){const u=poly[i],v=poly[(i+1)%4],axis=[-(v[1]-u[1]),v[0]-u[0]],pa=a.map(p=>p[0]*axis[0]+p[1]*axis[1]),pb=b.map(p=>p[0]*axis[0]+p[1]*axis[1]);if(Math.max(...pa)<=Math.min(...pb)+1e-8||Math.max(...pb)<=Math.min(...pa)+1e-8)return false}return true}

export function connectedRotationEdge(p,w){const edges=p.edges.filter(e=>e.from.well===w.id||e.to.well===w.id);return edges.find(e=>e.id===w.rotationEdge)||edges[0]}
export function pipeExitBearing(p,e,nodeId){
 const w=p.wells.find(v=>v.id===nodeId),from=e.from.well===nodeId;if(!w||!from&&e.to.well!==nodeId)throw Error('Труба не связана с узлом.');
 const other=p.wells.find(v=>v.id===(from?e.to.well:e.from.well)),point=(from?e.waypoints[0]:e.waypoints.at(-1))||other;
 if(!point||Math.hypot(point.x-w.x,point.y-w.y)<1e-9)throw Error('Сначала задайте ненулевое направление трубы.');
 return normalizeAngle(Math.atan2(point.y-w.y,point.x-w.x)*180/Math.PI);
}
export const isSquareWell=w=>isPhysicalWell(w)&&w.shape==='rect'&&Math.abs(w.width-w.length)<1e-6;
export function rotateWellTo(p,w,angle,{snap=true}={}){if(!Number.isFinite(angle))throw Error('Задайте угол поворота.');const e=connectedRotationEdge(p,w);if(snap&&isSquareWell(w)&&e){w.rotationMode='pipe';w.rotationEdge=e.id;w.rotation=normalizeAngle(Math.round(normalizeAngle(angle-referencePipeBearing(p,e,w.id))/90)*90)}else{w.rotationMode='manual';w.rotation=normalizeAngle(angle-(w.zeroAngle||0))}p.version=4}
export function quarterTurnWell(p,w,direction=1){const e=connectedRotationEdge(p,w);if(e&&w.shape==='rect'){const current=normalizeAngle(nodeAngle(p,w)-referencePipeBearing(p,e,w.id));w.rotationMode='pipe';w.rotationEdge=e.id;w.rotation=normalizeAngle(Math.round(current/90)*90+Math.sign(direction)*90)}else rotateWellTo(p,w,nodeAngle(p,w)+Math.sign(direction)*90,{snap:false});p.version=4}

export function junctionPipes(p,w){return p.edges.filter(e=>e.from.well===w.id||e.to.well===w.id).flatMap(e=>{try{return [{edge:e,bearing:pipeExitBearing(p,e,w.id)}]}catch{return []}})}
export const angleBetweenPipes=(a,b)=>Math.abs(normalizeAngle(b-a));
export function junctionAngles(p,w){const pipes=junctionPipes(p,w),pairs=[];for(let i=0;i<pipes.length;i++)for(let j=i+1;j<pipes.length;j++)pairs.push({a:pipes[i],b:pipes[j],angle:angleBetweenPipes(pipes[i].bearing,pipes[j].bearing)});return pairs}
export function rectangularPort(p,w,e){let bearing;try{bearing=pipeExitBearing(p,e,w.id)}catch{return {wall:0,error:Infinity,valid:false}}const delta=normalizeAngle(bearing-nodeAngle(p,w)),wall=((Math.round(delta/90)%4)+4)%4,error=Math.abs(normalizeAngle(delta-wall*90));return {wall,error,valid:error<.001}}

export function referencePipeBearing(p,e,nodeId){const clean={...e,waypoints:e.waypoints.filter(v=>!v.autoPort)};return pipeExitBearing(p,clean,nodeId)}
