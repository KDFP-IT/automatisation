import {nodeAngle,referencePipeBearing,connectedRotationEdge,normalizeAngle} from './node-geometry.js';
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
