from pathlib import Path
p=Path('dist/scene3d.js');s=p.read_text(encoding='utf-8').replace('nodeAngle,normalizeAngle','nodeAngle,normalizeAngle,junctionAngles');a=s.index('export function wellAxisAnnotations');s=s[:a]+'''export function wellPipeAngleAnnotations(p,w,g){
 const pairs=w.shape==='round'?junctionAngles(p,w):[];if(pairs.length!==1)return {annotations:[],labels:[]};
 const pair=pairs[0],delta=normalizeAngle(pair.b.bearing-pair.a.bearing),r=Math.max(g.bodyW,g.bodyL)*.9,z=w.ground+.3,point=angle=>[r*Math.cos(angle*Math.PI/180),r*Math.sin(angle*Math.PI/180),z],points=Array.from({length:25},(_,i)=>point(pair.a.bearing+delta*i/24));
 return {annotations:[{points:[[0,0,z],points[0]],dashed:true},{points},{points:[[0,0,z],points.at(-1)],dashed:true}],labels:[{at:point(pair.a.bearing+delta/2),text:pair.angle.toFixed(1)+'°',dy:-12,class:'junction-angle-label'}]};
}
'''
s=s.replace(" return render(p,mesh,bounds,plan?{yaw:0,pitch:90,showSoils:false}:camera,[{at:[0,0,g.pitBottom],text:w.name,dy:26}]);", " const angles=plan?{annotations:[],labels:[]}:wellPipeAngleAnnotations(p,w,g);bounds.push(...angles.annotations.flatMap(a=>a.points));return render(p,mesh,bounds,plan?{yaw:0,pitch:90,showSoils:false}:camera,[{at:[0,0,g.pitBottom],text:w.name,dy:26},...angles.labels],angles.annotations);")
p.write_text(s,encoding='utf-8')
p=Path('dist/network-views.js');s=p.read_text(encoding='utf-8');s=s.replace("unmap:v=>{const q=f.unmap(v);return[q[0],-q[1]]},frame:f,project:(x,y)=>f.map([x,-y])", "unmap:v=>{const q=f.unmap([450+(v[0]-450)/zoom,260+(v[1]-260)/zoom]);return[q[0],-q[1]]},frame:f,project:(x,y)=>{const q=f.map([x,-y]);return [450+(q[0]-450)*zoom,260+(q[1]-260)*zoom]}");p.write_text(s,encoding='utf-8')
p=Path('tests/exit-angles.test.js');s=p.read_text(encoding='utf-8').replace('drawWellMesh,wellAxisAnnotations','drawWellMesh').replace('normalizeAngle(pipeExitBearing(p,e,w.id)-w.zeroAngle),40','pipeExitBearing(p,e,w.id),40');a=s.index("test('3D well axes");s=s[:a]+'''test('well 3D omits construction axes and rendering leaves the model unchanged',()=>{const p=seedProject(),w=p.wells[0];w.shape='rect';w.zeroAngle=30;w.rotation=90;const before=JSON.stringify(p),html=drawWellMesh(p,w);assert.ok(!html.includes('data-axis='));assert.ok(!html.includes('NaN'));assert.equal(JSON.stringify(p),before)});
''';p.write_text(s,encoding='utf-8')
