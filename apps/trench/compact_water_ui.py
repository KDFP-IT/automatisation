from pathlib import Path
f=Path('dist/network-app.js');s=f.read_text(encoding='utf-8');a=s.index('function renderBeddingInspector(){');b=s.index('function renderWellPit()',a)
s=s[:a]+'''function renderBeddingInspector(){
 const e=edge(),res=e&&result.edges[e.id]?.res;if(!e||!res)return;const i=Math.min(state.section,e.sections.length-1),s=e.sections[i],base='edges.'+ei()+'.sections.'+i,r=result.edges[e.id];
 $('inspector-title').textContent=e.name;$('inspector-kind').textContent='ЗАСЫПКА ТРУБЫ';
 const bed=`<div class="two">${select('Материал',base+'.beddingMaterial',s.beddingMaterial||'ЩПС',[['ЩПС','ЩПС'],['Песок','Песок'],['Щебень','Щебень'],['Другой материал','Другой материал']])}${field('Толщина подушки',base+'.bedding',s.bedding,{unit:'м',min:0})}</div>`;
 const around=checkbox('Привозная обсыпка вокруг трубы',base+'.around',s.around)+(s.around?field('Материал обсыпки',base+'.aroundMaterial',s.aroundMaterial||'Песок',{type:'text'})+field('Слой над верхом '+(s.casing?'футляра':'трубы'),base+'.protection',s.protection,{unit:'м',min:0}):'');
 $('inspector').innerHTML=(e.sections.length>1?sectionChips(e,res):'')+(s.method!=='trench'?'<p class="model-warning">На этой зоне труба на опорах. Подушка и обсыпка не учитываются.</p>':taskCard('Засыпка до поверхности',backfillControls(e,'edges.'+ei()))+fillSketch()+block('1. Подушка · '+(s.bedding?esc(s.beddingMaterial||'ЩПС')+', '+fmt(s.bedding)+' м':'без подушки'),bed,false)+block('2. Обсыпка · '+(s.around?esc(s.aroundMaterial||'Песок')+', над трубой '+fmt(s.protection)+' м':'не задана'),around,false))+`<div id="fill-totals">${fillTotals(r,!r?.errors.length)}</div>`+block('Расчёт по материалам',`<section id="bedding-metrics" class="bedding-metrics">${beddingMetricsHTML()}</section>`,false);
}
function renderWellBackfill(){const w=well(),r=result.wells[w.id],base='wells.'+wi();$('inspector-title').textContent=w.name;$('inspector-kind').textContent='ЗАСЫПКА КОЛОДЦА';$('inspector').innerHTML=taskCard('Засыпка вокруг колодца',backfillControls(w,base))+fillSketch(true)+block('Подготовка под днищем · '+fmt(w.pad)+' м',`<div class="two">${field('Толщина подготовки',base+'.pad',w.pad,{unit:'м',min:0})}${field('Выпуск за днище',base+'.padMargin',w.padMargin,{unit:'м',min:0})}</div>`,false)+`<div id="fill-totals">${fillTotals(r,!r?.errors.length)}</div><button class="inline-add" data-action="inspector-tab" data-id="excavation">Размеры котлована →</button>`}
'''+s[b:]
# Full well height and chamber can be compared on one row.
s=s.replace("const heights=field('Общая высота колодца'", "const heights='<div class=\"two\">'+field('Общая высота колодца'")
s=s.replace("hint:'От земли до наружного низа днища.'", "hint:'До наружного низа днища.'")
s=s.replace("min:.01})+`<button class=\"standard-value\"", "min:.01})+'</div>'+`<button class=\"standard-value\"")
# Less height in primary sizes, preserve native labels.
s=s.replace("field('Обозначение',base+'.name',w.name,{type:'text'})+select('Форма колодца'", "field('Обозначение',base+'.name',w.name,{type:'text'})+'<div class=\"two\">'+select('Форма колодца'")
s=s.replace("field('Внутренний диаметр',base+'.diameter',w.diameter,{unit:'м'}):`<div class=\"two\">", "field('Внутренний диаметр',base+'.diameter',w.diameter,{unit:'м'})+'</div>':'</div>'+`<div class=\"two\">")
f.write_text(s,encoding='utf-8')
