from pathlib import Path
for f in ['package.json','compose.yaml','package_network.py']:
 p=Path(f);p.write_text(p.read_text(encoding='utf-8').replace('5.1.0','5.2.0'),encoding='utf-8')
p=Path('dist/node-geometry.js');s=p.read_text(encoding='utf-8').replace("export function rectangularPort(p,w,e){const delta=", "export function rectangularPort(p,w,e){let bearing;try{bearing=pipeExitBearing(p,e,w.id)}catch{return {wall:0,error:Infinity,valid:false}}const delta=").replace("const delta=normalizeAngle(pipeExitBearing(p,e,w.id)-nodeAngle(p,w))", "const delta=normalizeAngle(bearing-nodeAngle(p,w))");p.write_text(s,encoding='utf-8')
