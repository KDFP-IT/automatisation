from pathlib import Path
Path('dist/plan-viewport.js').write_text('''// Zoom is bounded only by finite floating-point arithmetic, never by a fixed UI range.
export function zoomPlanView(frame,zoom,factor,anchor=[450,260]){
 const next=zoom*factor;if(!frame||!Number.isFinite(next)||next<=0||!Number.isFinite(1/next)||!Number.isFinite(frame.scale*next))return {frame,zoom};
 const dx=(anchor[0]-450)*(1/next-1/zoom),dy=(anchor[1]-260)*(1/next-1/zoom);
 // Flatten transforms, avoiding an ever-growing chain on each wheel tick.
 const root=frame.root||frame,ox=(frame.offsetX||0)+dx,oy=(frame.offsetY||0)+dy;
 return {zoom:next,frame:{scale:root.scale,root,offsetX:ox,offsetY:oy,map:v=>{const q=root.map(v);return [q[0]+ox,q[1]+oy]},unmap:v=>root.unmap([v[0]-ox,v[1]-oy])}};
}
''',encoding='utf-8')
p=Path('dist/node-geometry.js');s=p.read_text(encoding='utf-8');s+='''
export function junctionPipes(p,w){return p.edges.filter(e=>e.from.well===w.id||e.to.well===w.id).flatMap(e=>{try{return [{edge:e,bearing:pipeExitBearing(p,e,w.id)}]}catch{return []}})}
export const angleBetweenPipes=(a,b)=>Math.abs(normalizeAngle(b-a));
export function junctionAngles(p,w){const pipes=junctionPipes(p,w),pairs=[];for(let i=0;i<pipes.length;i++)for(let j=i+1;j<pipes.length;j++)pairs.push({a:pipes[i],b:pipes[j],angle:angleBetweenPipes(pipes[i].bearing,pipes[j].bearing)});return pairs}
export function rectangularPort(p,w,e){const delta=normalizeAngle(pipeExitBearing(p,e,w.id)-nodeAngle(p,w)),wall=((Math.round(delta/90)%4)+4)%4,error=Math.abs(normalizeAngle(delta-wall*90));return {wall,error,valid:error<.001}}
''';p.write_text(s,encoding='utf-8')
p=Path('dist/constructor-core.js');s=p.read_text(encoding='utf-8').replace('pipeExitBearing,normalizeAngle','pipeExitBearing,normalizeAngle,nodeAngle,connectedRotationEdge');s=s.replace('angle+(origin.zeroAngle||0)-before','angle-before');s+='''
export function setRectangularPortWall(project,edgeId,nodeId,wall){
 const w=project.wells.find(v=>v.id===nodeId);if(!w||w.shape!=='rect'||!Number.isInteger(wall)||wall<0||wall>3)throw Error('Выберите одну из четырёх стен.');const direction=nodeAngle(project,w),affected=setPipeExitAngle(project,edgeId,nodeId,direction+90*wall);
 if(w.rotationMode==='pipe'){const ref=connectedRotationEdge(project,w);w.rotation=normalizeAngle(direction-pipeExitBearing(project,ref,w.id))}else w.rotation=normalizeAngle(direction-(w.zeroAngle||0));return affected;
}
''';p.write_text(s,encoding='utf-8')
p=Path('dist/network-checks.js');s=p.read_text(encoding='utf-8').replace('isPhysicalWell,localPoint,worldPoint','isPhysicalWell,localPoint,worldPoint,rectangularPort');needle="   if(!isPhysicalWell(w))continue;";s=s.replace(needle,needle+'''
   if(w.shape==='rect'){const port=rectangularPort(p,w,e);if(!port.valid){const message='Труба «'+e.name+'» должна выходить из центра стены колодца «'+w.name+'» под 90° к стене. Выберите стену подключения или исправьте направление трубы.';const paths=[edgePath(e)+'.waypoints',wellPath(w)+'.rotation',wellPath(w)+'.rotationMode'];add('rect-port-normal','error','edge',e.id,message,paths,'geometry',[w.id]);add('rect-port-normal','error','well',w.id,message,paths,'geometry',[e.id])}}
''',1);p.write_text(s,encoding='utf-8')
p=Path('dist/network-views.js');s=p.read_text(encoding='utf-8').replace('worldPoint,nodeAngle','worldPoint,nodeAngle,junctionAngles,normalizeAngle');a=s.index(" if(selected?.kind==='well')");b=s.index(" html+=text([88,490]",a)
s=s[:a]+''' if(selected?.kind==='well'){const w=p.wells.find(w=>w.id===selected.id);if(w&&isPhysicalWell(w)&&w.shape==='round'){const pairs=junctionAngles(p,w);if(pairs.length===1){const pair=pairs[0],centre=P(w.x,w.y),g=wellGeometry(w,p),r=Math.max(44,g.bodyW*f.scale*zoom/2+25),delta=normalizeAngle(pair.b.bearing-pair.a.bearing),start=pair.a.bearing,xy=angle=>[centre[0]+r*Math.cos(angle*Math.PI/180),centre[1]-r*Math.sin(angle*Math.PI/180)],a=xy(start),b=xy(start+delta),m=xy(start+delta/2);html+=`<g class="junction-angle" pointer-events="none"><path d="M${a[0]} ${a[1]} A${r} ${r} 0 0 ${delta>0?0:1} ${b[0]} ${b[1]}" fill="none" stroke="#cc671f" stroke-width="2"/>${text([m[0],m[1]-10],fmt(pair.angle,1)+'°','class="junction-angle-label"')}</g>`}}}
'''+s[b:];p.write_text(s,encoding='utf-8')
p=Path('dist/scene3d.js');s=p.read_text(encoding='utf-8');a=s.index(' const axes=wellAxisAnnotations');b=s.index('\n}',a);s=s[:a]+''' return render(p,mesh,bounds,plan?{yaw:0,pitch:90,showSoils:false}:camera,[{at:[0,0,g.pitBottom],text:w.name,dy:26}]);'''+s[b:];p.write_text(s,encoding='utf-8')
p=Path('dist/index.html');s=p.read_text(encoding='utf-8').replace('<label id="zoom-control">Масштаб <input id="zoom" type="range" min="0.6" max="2" step="0.05" value="1"></label>', '<div id="zoom-control" class="plan-zoom"><button id="plan-zoom-out" aria-label="Отдалить план">−</button><label><input id="zoom" aria-label="Масштаб плана, %" type="number" min="0" step="any" value="100">%</label><button id="plan-zoom-in" aria-label="Приблизить план">+</button></div>');p.write_text(s,encoding='utf-8')
