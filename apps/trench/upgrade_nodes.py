from pathlib import Path
p=Path('dist/network-app.js');s=p.read_text(encoding='utf-8')
s="import {isPhysicalWell,nodeAngle,normalizeAngle} from './node-geometry.js';\n"+s
s=s.replace('addWellAt,connectWells','addWellAt,addEndpointAt,setPipeLength,connectWells')
s=s.replace('function recordChange(before,label){history.record','function recordChange(before,label){p.version=4;history.record')
s=s.replace("['add-edge','connect']","['add-edge','pipe']")
s=s.replace("state.tool==='connect'?(state.connectFrom?'Выберите конечный колодец':'Выберите начальный колодец')", "['connect','pipe'].includes(state.tool)?(state.connectFrom?'Укажите конец трубы · колодец или точка на плане':'Укажите начало трубы · колодец или точка на плане')")
s=s.replace("$('add-edge').onclick=()=>setTool('connect')", "$('add-edge').onclick=()=>setTool('pipe')")
s=s.replace("state.tool==='connect'&&state.connectFrom", "['connect','pipe'].includes(state.tool)&&state.connectFrom")
s=s.replace("const node=ev.target.closest('[data-well]');if(state.tool==='connect'){", "let node=ev.target.closest('[data-well]');if(state.tool==='pipe'&&!node){const before=clone(p),xy=planTransform(svgPoint(ev)),w=addEndpointAt(p,...xy);recordChange(before,'Свободный конец трубы');persist();node={dataset:{well:w.id}}}if(['connect','pipe'].includes(state.tool)){")
s=s.replace("if(isWell&&w&&state.view==='3d')", "if(isWell&&w&&isPhysicalWell(w)&&state.view==='3d')")
s=s.replace("else if(isWell&&w&&state.view==='3d')", "else if(isWell&&w&&isPhysicalWell(w)&&state.view==='3d')")
s=s.replace("const isWell=state.scale==='object'&&state.object==='well',target=isWell?well():edge(),count=target?.layers.length||0;", "const isWell=state.scale==='object'&&state.object==='well',target=isWell?well():edge(),count=target?.layers.length||0;if(isWell&&target&&!isPhysicalWell(target)){renderEndpointInspector();return}")
s=s.replace("Колодцы <span>${p.wells.length}","Узлы <span>${p.wells.length}")
s=s.replace("<span class=\"tree-node-icon\">○</span>","<span class=\"tree-node-icon\">${isPhysicalWell(w)?'○':'•'}</span>")
s=s.replace("||parts.at(-1)==='beddingMaterial'", "||['beddingMaterial','heightMode','height','rotationMode','rotation','zeroAngle','rotationEdge'].includes(parts.at(-1))")
s=s.replace("const w=well();if(!w)return;const i=wi(),base='wells.'+i,g=wellGeometry(w);", "const w=well();if(!w)return;const i=wi(),base='wells.'+i,g=wellGeometry(w,p);")
s=s.replace("+field('Внутреннее дно','',g.floor", "+field('Высота колодца','',g.height,{unit:'м',command:'well-height',hint:'До наружного низа днища. Подготовка отдельно.'})+field('Внутреннее дно','',g.floor")
s=s.replace('${fmt(w.workingHeight)} / ${fmt(w.neckHeight)}','${fmt(g.workingHeight)} / ${fmt(g.neckHeight)}')
s=s.replace("field('Высота рабочей части',base+'.workingHeight',w.workingHeight,{unit:'м'})", "field('Высота рабочей части',base+'.workingHeight',g.workingHeight,{unit:'м',readonly:w.heightMode==='total'})")
s=s.replace("field('Высота горловины',base+'.neckHeight',w.neckHeight,{unit:'м'})", "field('Высота горловины',base+'.neckHeight',g.neckHeight,{unit:'м',readonly:w.heightMode==='total'})")
s=s.replace("+block('Котлован и координаты',pit,false)", "+block('Поворот на плане',rotationEditor(w,base),false)+block('Котлован и координаты',pit,false)")
s=s.replace("const body=field('Диаметр трубы'", "const body=field('Длина трубы','',res.actualLength,{unit:'м',command:'pipe-length',hint:'По оси с учётом уклона. Начало фиксировано, конец перемещается.'})+field('Диаметр трубы'")
s=s.replace("if(!path&&!command)return;beginEdit(node);", "if(!path&&!command)return;if(command==='pipe-length'){node.dataset.invalidDraft='true';return}beginEdit(node);")
s=s.replace("else if(path)pathSet(path,val);", "else if(path){if(path.endsWith('.zeroAngle')){const w=well(),angle=nodeAngle(p,w);pathSet(path,val);if(w.rotationMode!=='pipe')w.rotation=normalizeAngle(angle-val)}else pathSet(path,val);if(path.endsWith('.shape')&&val==='rect'){well().rotationMode='pipe';well().rotation=0}}")
s=s.replace("if(command==='floor'&&well()){const w=well();w.workingHeight=w.ground-w.neckHeight-w.slab-val}", "if(command==='well-height'&&well()){Object.assign(well(),{heightMode:'total',height:val})}if(command==='floor'&&well()){const w=well();if(w.heightMode==='total')w.height=w.ground-val+w.base;else w.workingHeight=w.ground-w.neckHeight-w.slab-val}")
s=s.replace("$('inspector').addEventListener('input',inputChanged);", """$('inspector').addEventListener('input',inputChanged);
$('inspector').addEventListener('change',ev=>{const node=ev.target;if(node.dataset.command!=='pipe-length')return;flushEdit();const before=clone(p);try{setPipeLength(p,edge().id,node.value===''?NaN:Number(node.value));delete node.dataset.invalidDraft;node.removeAttribute('aria-invalid');recordChange(before,'Длина трубы');persist();render()}catch(error){p=before;node.dataset.invalidDraft='true';node.setAttribute('aria-invalid','true');notify(error.message)}});
$('inspector').addEventListener('keydown',ev=>{if(ev.key==='Enter'&&ev.target.dataset.command==='pipe-length')ev.target.blur()});""")
pos=s.index('function renderWellInspector()')
s=s[:pos]+"""function renderEndpointInspector(){const w=well(),base='wells.'+wi();$('inspector-tabs').innerHTML='';$('inspector-title').textContent=w.name;$('inspector-kind').textContent='СВОБОДНЫЙ КОНЕЦ';$('inspector').innerHTML=block('Положение',field('Обозначение',base+'.name',w.name,{type:'text'})+field('Земля',base+'.ground',w.ground,{unit:'м'})+field('X',base+'.x',w.x,{unit:'м'})+field('Y',base+'.y',w.y,{unit:'м'}))+block('Трубы',w.ports.map((v,i)=>field('Наружный низ трубы',base+'.ports.'+i+'.invert',v.invert,{unit:'м'})+(linkedPort(w,v)?`<button data-action="edge" data-id="${esc(linkedPort(w,v).id)}" class="inline-add">Открыть трубу →</button>`:'')).join(''))+'<button class="button delete-button" data-action="delete-well">Удалить точку</button>'}
function rotationEditor(w,base){return select('Ориентация',base+'.rotationMode',w.rotationMode||'manual',[['manual','Вручную'],['pipe','По связанной трубе']])+(w.rotationMode==='pipe'?select('Опорная труба',base+'.rotationEdge',w.rotationEdge||p.edges.find(e=>e.from.well===w.id||e.to.well===w.id)?.id||'',[['','Автоматически'],...p.edges.filter(e=>e.from.well===w.id||e.to.well===w.id).map(e=>[e.id,e.name])]):'')+field(w.rotationMode==='pipe'?'Поправка к трубе':'Угол от нуля',base+'.rotation',w.rotation||0,{unit:'°'})+field('Направление 0° от оси X',base+'.zeroAngle',w.zeroAngle||0,{unit:'°'})+'<p class="compact-note">Ось Z — через центр. Синяя ручка — поворот, оранжевая — направление нуля.</p>'}
"""+s[pos:]
s=s.replace("const vertex=ev.target.closest('[data-waypoint]'),node=ev.target.closest('[data-well]');", "const rotation=ev.target.closest('[data-rotate-well],[data-zero-well]');if(rotation){drag={kind:rotation.dataset.zeroWell?'zero':'rotate',id:rotation.dataset.zeroWell||rotation.dataset.rotateWell,x:ev.clientX,y:ev.clientY,before:clone(p),frame:planFrame,moved:false};$('network-scene').setPointerCapture(ev.pointerId);return}const vertex=ev.target.closest('[data-waypoint]'),node=ev.target.closest('[data-well]');")
s=s.replace("if(!planTransform)return;const [x,y]=planTransform(svgPoint(ev)),target=", "if(!planTransform)return;const [x,y]=planTransform(svgPoint(ev));if(['rotate','zero'].includes(drag.kind)){const w=p.wells.find(w=>w.id===drag.id),angle=Math.atan2(y-w.y,x-w.x)*180/Math.PI;if(drag.kind==='zero'){const old=nodeAngle(p,w);w.zeroAngle=normalizeAngle(angle);if(w.rotationMode!=='pipe')w.rotation=normalizeAngle(old-angle)}else{w.rotationMode='manual';w.rotation=normalizeAngle(angle-(w.zeroAngle||0))}calculate();renderCanvas();return}const target=")
s=s.replace("if(d.kind==='node'||d.kind==='point'){", "if(['rotate','zero'].includes(d.kind)){if(d.moved){recordChange(d.before,'Поворот колодца');persist()}render();return}if(d.kind==='node'||d.kind==='point'){")
p.write_text(s,encoding='utf-8')
p=Path('api/app.py');s=p.read_text(encoding='utf-8').replace("model.get('version') != 3","model.get('version') not in (3, 4)").replace('модели схемы версии 3','модели схемы версии 3 или 4')
s=s.replace("identifier(well.get('id')); name(well.get('name'))", """identifier(well.get('id')); name(well.get('name'))
        for key in ['height', 'rotation', 'zeroAngle']:
            if key in well: number(well[key])
        for key, allowed in [('kind', ['well', 'endpoint']), ('heightMode', ['total', 'parts']), ('rotationMode', ['manual', 'pipe'])]:
            if key in well and well[key] not in allowed: raise ValueError('Некорректный режим узла.')
        if 'rotationEdge' in well and (not isinstance(well['rotationEdge'], str) or len(well['rotationEdge']) > 150): raise ValueError('Некорректная опорная труба.')""")
s=s.replace("well_count=len(model['wells']), edge_count=len(model['edges'])", "well_count=sum(w.get('kind') != 'endpoint' for w in model['wells']), endpoint_count=sum(w.get('kind') == 'endpoint' for w in model['wells']), edge_count=len(model['edges'])")
p.write_text(s,encoding='utf-8')
