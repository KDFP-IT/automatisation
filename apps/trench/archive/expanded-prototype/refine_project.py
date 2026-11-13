from pathlib import Path
p=Path('dist/project.js');s=p.read_text(encoding='utf8')
edits=[
 ("!Number.isFinite(x.excavation))throw", "!Number.isFinite(x.excavation)||(x.placement!==undefined&&!['trench','pit'].includes(x.placement)))throw"),
 ('Геометрическая конструкция по всей длине учитывается здесь с котлованом, равным её объёму, чтобы вычесть её один раз.', 'Для конструкции внутри траншеи выберите соответствующее размещение: отдельный котлован для неё не вычитается.'),
 ('<div class="structure-inputs">${field(\'Вытесняемый объём\'', '''<label>Размещение<select data-field="placement" data-list="structures" data-index="${i}"><option value="pit" ${x.placement!=='trench'?'selected':''}>В отдельном котловане</option><option value="trench" ${x.placement==='trench'?'selected':''}>Внутри траншеи</option></select></label><div class="structure-inputs">${field('Вытесняемый объём\''''),
 ("${field('Выемка котлована','excavation',x.excavation,{list:'structures',index:i,unit:'м³'})}", "${x.placement!=='trench'?field('Выемка котлована','excavation',x.excavation,{list:'structures',index:i,unit:'м³'}):'<p class=\"editor-hint\">Выемка уже учтена в траншее.</p>'}"),
 ("${f(x.excavation-x.volume)} м³", "${f(x.placement==='trench'?0:x.excavation-x.volume)} м³"),
 ("f(x.excavation-x.volume)+' м³'", "f(x.placement==='trench'?0:x.excavation-x.volume)+' м³'"),
 ("'count','method'].includes(field)", "'count','method','placement'].includes(field)"),
 ("if(field==='method')renderEditor()", "if(field==='method'||field==='placement')renderEditor()"),
 ("if(p.objectType==='box')section.structures.push({name:'Прямоугольная конструкция по всей длине',volume:r.structure,excavation:r.structure})", "if(p.objectType==='box')section.structures.push({name:'Прямоугольная конструкция по всей длине',volume:r.structure,excavation:0,placement:'trench'})"),
 ('Группы грунта нового участка заданы как 100% I — уточните по проекту.', 'Укажите доли групп грунта по проекту — до этого свод будет недоступен.'),
 ("rows.push([p.name,'Котлованы',x.name,'м³',x.excavation,x.excavationSource?.cell||''])", "rows.push([p.name,'Котлованы',x.name,'м³',x.placement==='trench'?0:x.excavation,x.placement==='trench'?'Внутри траншеи':x.excavationSource?.cell||''])"),
]
for a,b in edits:
 if a not in s:raise ValueError('Target missing: '+a)
 s=s.replace(a,b)
p.write_text(s,encoding='utf8')
