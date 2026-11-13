from pathlib import Path
p=Path('dist/network-views.js');s=p.read_text(encoding='utf-8').replace('zero=ray(w.zeroAngle??0)','zero=(()=>{const q=ray(w.zeroAngle??0);return [centre[0]+(q[0]-centre[0])*.72,centre[1]+(q[1]-centre[1])*.72]})()');p.write_text(s,encoding='utf-8')
p=Path('dist/network-app.js');s=p.read_text(encoding='utf-8').replace("p.edges=p.edges.filter(x=>x.id!==id);", "p.edges=p.edges.filter(x=>x.id!==id);for(const w of p.wells)if(w.rotationEdge===id)delete w.rotationEdge;")
s=s.replace("isWell&&state.view==='3d'?w?.name", "isWell&&isPhysicalWell(w)&&state.view==='3d'?w?.name")
s=s.replace("...((e||isWell)?[['3d','3D']]:[])","...((e||isWell&&isPhysicalWell(w))?[['3d','3D']]:[])")
s=s.replace("function showWell(id){flushEdit();", "function showWell(id){flushEdit();if(p.wells.find(w=>w.id===id)?.kind==='endpoint')state.view='plan';")
s=s.replace("state.scale==='object'&&state.object==='well'?{r:result.wells", "state.scale==='object'&&state.object==='well'&&isPhysicalWell(well())?{r:result.wells")
p.write_text(s,encoding='utf-8')
p=Path('dist/project-library.js');s=p.read_text(encoding='utf-8').replace('Колодцев: ${v.well_count} · Участков: ${v.edge_count}', 'Колодцев: ${v.well_count}${v.endpoint_count?` · Точек: ${v.endpoint_count}`:\'\'} · Участков: ${v.edge_count}');p.write_text(s,encoding='utf-8')
for f in ['package.json','compose.yaml','package_network.py']:
 p=Path(f);s=p.read_text(encoding='utf-8').replace('4.5.0','5.0.0').replace('trench-projects-api:1.2.0','trench-projects-api:2.0.0');p.write_text(s,encoding='utf-8')
p=Path('dist/constructor.css');p.write_text(p.read_text(encoding='utf-8')+'\n.rotation-handle{cursor:grab;pointer-events:all}.rotation-handle:active{cursor:grabbing}.well-orientation .axis-note{font-size:12px}\n',encoding='utf-8')
