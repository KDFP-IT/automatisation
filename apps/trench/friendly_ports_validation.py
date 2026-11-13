from pathlib import Path
p=Path('dist/node-geometry.js');s=p.read_text(encoding='utf-8').replace('angle-pipeExitBearing(p,e,w.id)','angle-referencePipeBearing(p,e,w.id)').replace('nodeAngle(p,w)-pipeExitBearing(p,e,w.id)','nodeAngle(p,w)-referencePipeBearing(p,e,w.id)');p.write_text(s,encoding='utf-8')
p=Path('api/app.py');s=p.read_text(encoding='utf-8').replace("identifier(port.get('id')); number(port.get('invert')); ports.add(port['id'])", "identifier(port.get('id')); number(port.get('invert')); ports.add(port['id'])\n            if 'wall' in port and (isinstance(port['wall'], bool) or not isinstance(port['wall'], int) or not 0 <= port['wall'] <= 3): raise ValueError('Некорректная стена подключения.')")
s=s.replace("identifier(point.get('id')); number(point.get('x')); number(point.get('y'))", "identifier(point.get('id')); number(point.get('x')); number(point.get('y'))\n            if 'autoPort' in point and point['autoPort'] not in [edge['from']['well'], edge['to']['well']]: raise ValueError('Некорректный подвод к стене.')")
p.write_text(s,encoding='utf-8')
p=Path('dist/network-model.js');s=p.read_text(encoding='utf-8').replace("for(const port of w.ports){id(port.id);", "for(const port of w.ports){if(port.wall!==undefined&&(!Number.isInteger(port.wall)||port.wall<0||port.wall>3))throw Error('Некорректная стена подключения.');id(port.id);")
s=s.replace("for(const v of e.waypoints){id(v.id);", "for(const v of e.waypoints){if(v.autoPort!==undefined&&![e.from.well,e.to.well].includes(v.autoPort))throw Error('Некорректный подвод к стене.');id(v.id);");p.write_text(s,encoding='utf-8')
p=Path('tests/junctions-viewport.test.js');s=p.read_text(encoding='utf-8').replace('route length and elevations','opposite node and elevations').replace("const res=resolveEdge(p,e),L=res.actualLength,z=res.points.map(v=>v.invert);", "const res=resolveEdge(p,e),end=[res.to.x,res.to.y],z=res.points.map(v=>v.invert);")
s=s.replace("near(resolveEdge(p,e).actualLength,L);assert.deepEqual(resolveEdge(p,e).points.map(v=>v.invert),z);", "assert.deepEqual([res.to.x,res.to.y],end);assert.ok(e.waypoints.some(v=>v.autoPort===w.id));assert.equal(resolveEdge(p,e).portA.invert,z[0]);assert.equal(resolveEdge(p,e).portB.invert,z.at(-1));")
s=s.replace("e.waypoints[0].x+=1;assert.equal(rectangularPort(p,w,e).valid,true)","e.waypoints.find(v=>!v.autoPort).x+=1;reconcileRectangularPorts(p);assert.equal(rectangularPort(p,w,e).valid,true)")
s=s.replace('{setRectangularPortWall}', '{setRectangularPortWall,reconcileRectangularPorts}')
p.write_text(s,encoding='utf-8')
for f in ['package.json','compose.yaml','package_network.py']:
 p=Path(f);p.write_text(p.read_text(encoding='utf-8').replace('5.2.0','5.3.0').replace('trench-projects-api:2.0.0','trench-projects-api:2.1.0'),encoding='utf-8')
