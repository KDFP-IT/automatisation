from pathlib import Path
p=Path('dist/network-views.js');s=p.read_text(encoding='utf-8');pos=s.index('export function bearing');s=s[:pos]+'''export function planObjectFrame(p,selected){
 if(selected.kind==='well'){const w=p.wells.find(v=>v.id===selected.id);if(!w)throw Error('Выберите узел.');if(!isPhysicalWell(w))return fit([[w.x-1,-w.y-1],[w.x+1,-w.y+1]]);const g=wellGeometry(w,p);return fit(rectangleVertices(w,g.topW,g.topL,g.rotation).map(([x,y])=>[x,-y]))}
 const e=p.edges.find(v=>v.id===selected.id);if(!e)throw Error('Выберите участок.');const res=resolveEdge(p,e),margin=Math.max(.5,e.diameter);return fit(res.points.flatMap(v=>[[v.x-margin,-v.y-margin],[v.x+margin,-v.y+margin]]));
}
'''+s[pos:];p.write_text(s,encoding='utf-8')
p=Path('dist/network-app.js');s=p.read_text(encoding='utf-8').replace('drawWell,bearing}','drawWell,bearing,planObjectFrame}');s=s.replace("$('fit-plan').disabled=state.view!=='plan';", "$('fit-plan').disabled=state.view!=='plan';$('focus-object').disabled=state.view!=='plan'||state.scale==='network';")
s=s.replace("$('show-report').onclick=", "$('focus-object').onclick=()=>{try{planFrame=planObjectFrame(p,{kind:state.object==='well'?'well':'edge',id:state.object==='well'?state.wellId:state.edgeId});state.zoom=1;renderCanvas()}catch(error){notify(error.message)}};$('show-report').onclick=",1);p.write_text(s,encoding='utf-8')
p=Path('dist/index.html');s=p.read_text(encoding='utf-8').replace('<button id="fit-plan">Вписать</button>', '<button id="fit-plan" title="Показать всю трассу">Вписать</button><button id="focus-object" title="Приблизить выбранный участок или узел">К объекту</button>');p.write_text(s,encoding='utf-8')
