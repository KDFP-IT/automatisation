from pathlib import Path
p=Path('dist/scene3d.js');s=p.read_text(encoding='utf-8').replace("import {isPhysicalWell,worldPoint}","import {isPhysicalWell,worldPoint,nodeAngle,normalizeAngle}")
s=s.replace('stroke="#c86b32" stroke-width="2" ${a.dashed?', 'stroke="${a.color||\'#c86b32\'}" stroke-width="2" ${a.axis?`data-axis="${esc(a.axis)}"`:""} ${a.dashed?')
s=s.replace('${Number.isFinite(l.beta)?', '${l.axis?`data-axis-label="${esc(l.axis)}"`:""} ${Number.isFinite(l.beta)?')
s=s.replace("r=g.bodyW/2,A=", "r=w.shape==='rect'?Math.min(g.bodyW/2/Math.max(1e-12,Math.abs(Math.cos(az))),g.bodyL/2/Math.max(1e-12,Math.abs(Math.sin(az)))):g.bodyW/2,A=")
s=s.replace("return render(p,mesh,bounds,plan?{yaw:0,pitch:90,showSoils:false}:camera,[{at:[0,0,g.pitBottom],text:w.name,dy:26}]);", """const axes=wellAxisAnnotations(w,g);if(!plan)bounds.push(...axes.annotations.flatMap(a=>a.points));
 return render(p,mesh,bounds,plan?{yaw:0,pitch:90,showSoils:false}:camera,[{at:[0,0,g.pitBottom],text:w.name,dy:26},...(!plan?axes.labels:[])],!plan?axes.annotations:[]);""")
s+='''
export function wellAxisAnnotations(w,g){
 const origin=[0,0,w.ground+.3],arm=Math.max(1,Math.max(g.bodyW,g.bodyL)*.8),ray=(angle,length=arm)=>{const q=worldPoint({x:0,y:0},length,0,angle);return [...q,origin[2]]},zero=ray(w.zeroAngle||0),body=ray(g.rotation,arm*.75),top=[0,0,w.ground+.9];
 return {annotations:[{axis:'Z',points:[[0,0,g.bottom],top],color:'#368c80',dashed:true},{axis:'zero',points:[origin,zero],color:'#ce793c',dashed:true},{axis:'body',points:[origin,body],color:'#315c7c'}],labels:[{axis:'Z',at:top,text:'Z · ось поворота',dy:-12,class:'axis-note'},{axis:'zero',at:zero,text:'0°',dy:18,class:'axis-note'},{axis:'body',at:body,text:normalizeAngle(g.rotation-(w.zeroAngle||0)).toFixed(1)+'°',dy:-12,class:'axis-note'}]};
}
'''
p.write_text(s,encoding='utf-8')
p=Path('dist/network-app.js');s=p.read_text(encoding='utf-8');s=s.replace("const body=exitAngleField(e,res.from,'Угол выхода в начале')+exitAngleField(e,res.to,'Угол выхода в конце')+field('Длина трубы'", "const directions=exitAngleField(e,res.from,'Угол выхода в начале')+exitAngleField(e,res.to,'Угол выхода в конце');const body=field('Длина трубы'")
s=s.replace("block('Труба',body)+block('Траншея", "block('Труба',body)+block('Углы выхода',directions,false)+block('Траншея")
p.write_text(s,encoding='utf-8')
for f in ['package.json','compose.yaml','package_network.py']:
 p=Path(f);p.write_text(p.read_text(encoding='utf-8').replace('5.0.0','5.1.0'),encoding='utf-8')
