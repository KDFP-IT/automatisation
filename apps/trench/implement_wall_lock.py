from pathlib import Path
f=Path('dist/network-app.js');s=f.read_text(encoding='utf-8');s="import {preserveWallConnections} from './wall-connections.js';\n"+s
old="translateSelection(p,drag.before,drag.keys,Math.round((q[0]-drag.start[0])*100)/100,Math.round((q[1]-drag.start[1])*100)/100);calculate"
new="const last=clone(p);try{translateSelection(p,drag.before,drag.keys,Math.round((q[0]-drag.start[0])*100)/100,Math.round((q[1]-drag.start[1])*100)/100);drag.wallMoved=preserveWallConnections(p,drag.before,selectionNodes(p,drag.keys))}catch(error){p=last;notify(error.message);return}calculate"
assert old in s;s=s.replace(old,new)
old="target.x=Math.round(x*100)/100;target.y=Math.round(y*100)/100;reconcileRectangularPorts(p,drag.before);"
new="const last=clone(p);target.x=Math.round(x*100)/100;target.y=Math.round(y*100)/100;if(drag.kind==='node'){try{drag.wallMoved=preserveWallConnections(p,drag.before,[drag.id])}catch(error){p=last;notify(error.message);return}}reconcileRectangularPorts(p,drag.before);"
assert old in s;s=s.replace(old,new)
s=s.replace("recordChange(d.before,'Перемещение '+(d.kind==='node'?'колодца':'вершины'));persist();render()", "recordChange(d.before,'Перемещение '+(d.kind==='node'?'колодца':'вершины'));persist();render();if(d.wallMoved?.length)notify('Выходы 90° сохранены. Перемещены связанные узлы: '+d.wallMoved.join(', '))")
s=s.replace("if(affected.length)notify('Группа перемещена. Проверьте соседние трубы: '+affected.map(e=>e.name).join(', '))", "if(d.wallMoved?.length)notify('Выходы 90° сохранены. Перемещены связанные узлы: '+d.wallMoved.join(', '));else if(affected.length)notify('Группа перемещена. Проверьте соседние трубы: '+affected.map(e=>e.name).join(', '))")
# Apply same constraint rules to numeric X/Y edits, using the uncommitted field's original snapshot.
s=s.replace("if(path&&/\\.(x|y|rotation|rotationMode|shape)$/.test(path)", "if(path&&/^wells\\.\\d+\\.(x|y)$/.test(path)&&editSession?.before){try{preserveWallConnections(p,editSession.before,[p.wells[Number(path.split('.')[1])].id])}catch(error){p=clone(editSession.before);notify(error.message);render();return}}if(path&&/\\.(x|y|rotation|rotationMode|shape)$/.test(path)")
f.write_text(s,encoding='utf-8')
f=Path('dist/network-views.js');s=f.read_text(encoding='utf-8')
s=s.replace("let html=defs;\n for(const w of p.wells.filter(isPhysicalWell)){", "let html=defs;const pitContours=p.wells.filter(isPhysicalWell).map(w=>{const g=wellGeometry(w,p);return {w,vertices:rectangleVertices(w,g.topW,g.topL,g.rotation).map(([x,y])=>P(x,y))}});html+='<defs><mask id=\"joint-outside-pits\" maskUnits=\"userSpaceOnUse\" x=\"0\" y=\"0\" width=\"900\" height=\"520\"><rect width=\"900\" height=\"520\" fill=\"white\"/>'+pitContours.map(v=>poly(v.vertices,'black','black')).join('')+'</mask></defs>';\n for(const w of p.wells.filter(isPhysicalWell)){")
s=s.replace("map(([x,y])=>P(x,y)),'#a8bac30b','#bdc9d1','stroke-dasharray=\"4 4\"')", "map(([x,y])=>P(x,y)),'#7bb5dd17','#92b0c5','stroke-dasharray=\"4 4\"')")
s=s.replace("'stroke-width=\"1.5\" pointer-events=\"none\"');const q=P(...region.location);html+=text([q[0],q[1]-12],'Общая выемка учтена'", "'stroke-width=\"1.5\" mask=\"url(#joint-outside-pits)\" pointer-events=\"none\"');const q=P(...region.location);html+=text([q[0],q[1]-12],'Общая часть траншей'")
s=s.replace("'Пунктир — границы котлованов'", "'Голубой пунктир — котлованы'")
# One fixed-position legend; never affects canvas sizing while editing.
s=s.replace("html+=text([88,490]", "if(result.jointRegions?.length)html+=text([450,490],'Зелёный — пересечение траншей вне котлованов','class=\"joint-plan-label\" pointer-events=\"none\"');\n html+=text([88,490]")
f.write_text(s,encoding='utf-8')
