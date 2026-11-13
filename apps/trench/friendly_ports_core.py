from pathlib import Path
p=Path('dist/node-geometry.js');s=p.read_text(encoding='utf-8').replace('pipeExitBearing(p,e,w.id)+offset','referencePipeBearing(p,e,w.id)+offset');s+='''
export function referencePipeBearing(p,e,nodeId){const clean={...e,waypoints:e.waypoints.filter(v=>!v.autoPort)};return pipeExitBearing(p,clean,nodeId)}
''';p.write_text(s,encoding='utf-8')
p=Path('dist/constructor-core.js');s=p.read_text(encoding='utf-8').replace('connectedRotationEdge}','connectedRotationEdge,rectangularPort,referencePipeBearing}');a=s.index('export function setRectangularPortWall(');s=s[:a]+'''
export function reconcileRectangularPorts(project,before=null,{onlyNode=null,onlyEdge=null,force=false}={}){
 const changed=[];
 // Orientations depend on route vertices entered by the engineer, never on generated leads.
 const geometries=new Map(project.wells.filter(w=>w.kind!=='endpoint'&&w.shape==='rect').map(w=>[w.id,wellGeometry(w,project)]));
 for(const w of project.wells){if(!geometries.has(w.id)||onlyNode&&w.id!==onlyNode)continue;const g=geometries.get(w.id);
  for(const e of project.edges){if(onlyEdge&&e.id!==onlyEdge)continue;const side=e.from.well===w.id?'from':e.to.well===w.id?'to':null;if(!side)continue;const port=w.ports.find(v=>v.id===e[side].port);if(!port)continue;
   const oldW=before?.wells.find(v=>v.id===w.id),oldE=before?.edges.find(v=>v.id===e.id),oldPort=oldW?.ports.find(v=>v.id===port.id);
   let wall=port.wall??oldPort?.wall;if(!Number.isInteger(wall)){try{wall=oldW&&oldE?rectangularPort(before,oldW,oldE).wall:rectangularPort(project,w,e).wall}catch{wall=0}}
   let lead=e.waypoints.find(v=>v.autoPort===w.id),current;try{current=rectangularPort(project,w,e)}catch{current={valid:false}};
   if(!force&&!lead&&(!before||!oldW||!oldE)&&!current.valid)continue;
   port.wall=wall;
   if(!force&&!lead&&current.valid&&current.wall===wall)continue;
   const radius=wall%2?g.bodyL/2:g.bodyW/2,outer=Math.max(e.diameter,e.sections[side==='from'?0:e.sections.length-1]?.casing||0),distance=radius+Math.max(.5,outer),angle=(g.rotation+wall*90)*Math.PI/180;
   if(!lead){lead={id:uid(),x:0,y:0,ground:null,invert:null,autoPort:w.id};if(side==='from')e.waypoints.unshift(lead);else e.waypoints.push(lead)}
   lead.x=w.x+Math.cos(angle)*distance;lead.y=w.y+Math.sin(angle)*distance;changed.push(e.name);
  }
 }
 if(changed.length)project.version=4;return [...new Set(changed)];
}
export function setRectangularPortWall(project,edgeId,nodeId,wall){
 const w=project.wells.find(v=>v.id===nodeId),e=project.edges.find(v=>v.id===edgeId);if(!w||w.shape!=='rect'||!e||!Number.isInteger(wall)||wall<0||wall>3)throw Error('Выберите стену на схеме колодца.');const side=e.from.well===nodeId?'from':e.to.well===nodeId?'to':null;if(!side)throw Error('Труба не связана с колодцем.');
 w.ports.find(v=>v.id===e[side].port).wall=wall;return reconcileRectangularPorts(project,null,{onlyNode:nodeId,onlyEdge:edgeId,force:true});
}
''';p.write_text(s,encoding='utf-8')
# Scope selection suppression to the drawing surfaces, keep forms and report text selectable.
p=Path('dist/constructor.css');p.write_text(p.read_text(encoding='utf-8')+'\n#network-scene,#network-scene *,#linked-views svg,#linked-views svg *{-webkit-user-select:none;user-select:none;-webkit-touch-callout:none}#network-scene,#linked-views svg{touch-action:none}\n.wall-picker{margin:10px 0;padding:12px;border:1px solid #dbe5ec;border-radius:9px;background:#f8fafc}.wall-picker h4{margin:0 0 6px}.wall-picker svg{display:block;width:100%;height:150px;user-select:none}.wall-pick{cursor:pointer}.wall-pick:focus{outline:none;stroke:#f97316;stroke-width:6}.port-repair{padding:12px;background:#fff5e9;border:1px solid #f3dbba;border-radius:8px;margin:8px 0}.port-repair p{margin:5px 0 9px;font-size:12px;line-height:1.5}.port-repair-actions{display:flex;gap:7px;flex-wrap:wrap}.port-repair button{border:1px solid #edbe93;background:white;border-radius:5px;padding:7px;color:#93450f}.port-selection-note{font-size:12px;color:#587082;margin:4px 0}.auto-port-point{fill:#fff;stroke:#587082;stroke-width:2}\n',encoding='utf-8')
