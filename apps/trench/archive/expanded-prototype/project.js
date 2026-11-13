import {seedProjects,sourceInfo} from './seed.js';
import {calculateProject,summarizeProjects,pipeVolume,newProject} from './project-model.js';
const $=id=>document.getElementById(id),esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const f=(n,d=3)=>Number.isFinite(n)?n.toLocaleString('ru-RU',{minimumFractionDigits:d,maximumFractionDigits:d}):'—';
const clone=x=>structuredClone(x),key='earthworks-project-v2';
let projects=clone(seedProjects),selectedId=projects[0]?.id,storageIssue='';
function normalize(input){
 if(!Array.isArray(input)||input.length>500)throw Error('Ожидается список не более 500 участков.');
 const ids=new Set();
 for(const p of input){
  if(!p||typeof p.id!=='string'||ids.has(p.id)||typeof p.name!=='string'||p.name.length>1000)throw Error('Некорректные названия или идентификаторы участков.');ids.add(p.id);
  if(!Number.isFinite(p.totalExcavation)||!Array.isArray(p.groups)||p.groups.length!==4||!p.groups.every(Number.isFinite))throw Error('Некорректная выемка или группы грунта.');
  for(const list of ['materials','pipes','structures'])if(!Array.isArray(p[list])||p[list].length>500)throw Error('Некорректный список '+list+'.');
  for(const x of p.materials)if(typeof x.name!=='string'||!Number.isFinite(x.volume))throw Error('Некорректный материал.');
  for(const x of p.structures)if(typeof x.name!=='string'||!Number.isFinite(x.volume)||!Number.isFinite(x.excavation)||(x.placement!==undefined&&!['trench','pit'].includes(x.placement)))throw Error('Некорректное сооружение.');
  for(const x of p.pipes)if(typeof x.name!=='string'||!['area','diameter'].includes(x.method)||!['length','area','diameter','count'].every(k=>Number.isFinite(x[k])))throw Error('Некорректная труба.');
  p.sourceWarnings=Array.isArray(p.sourceWarnings)?p.sourceWarnings.filter(x=>typeof x==='string'):[];
 }
 return input;
}
try{const text=localStorage.getItem(key);if(text){const data=JSON.parse(text);if(data.version!==2)throw Error('Неизвестная версия проекта.');projects=normalize(data.projects);selectedId=projects[0]?.id}}catch(e){storageIssue='Сохранённый проект не прочитан: '+e.message+' Показана копия исходного Excel.'}
function status(text){$('project-status').textContent=text}
function persist(){try{normalize(projects);localStorage.setItem(key,JSON.stringify({version:2,projects}));storageIssue=''}catch(e){storageIssue='Изменения не сохранены в браузере: '+e.message;status(storageIssue)}}
function current(){return projects.find(p=>p.id===selectedId)}
function setTab(name){const geometry=name==='geometry';$('geometry-section').hidden=!geometry;$('project-section').hidden=geometry;for(const n of ['geometry','project']){$('tab-'+n).classList.toggle('active',n===name);$('tab-'+n).setAttribute('aria-selected',String(n===name))}}
$('tab-geometry').onclick=()=>setTab('geometry');$('tab-project').onclick=()=>setTab('project');
function metric(label,n,note=''){return `<article class="panel project-metric"><span>${label}</span><strong>${f(n)} <small>м³</small></strong><p>${note}</p></article>`}
function renderSummary(){
 const sum=summarizeProjects(projects);$('project-count').textContent=String(projects.length);
 const complete=!sum.errors.length;
 $('project-totals').innerHTML=metric('Общая выемка',complete?sum.totalExcavation:NaN,projects.length+' участков')+metric('Засыпка грунтом',complete?sum.groundBackfill:NaN,'Траншеи и котлованы')+metric('ЩПС',complete?sum.materials:NaN,'Все слои')+metric('Вывоз грунта',complete?sum.exported:NaN,'В плотном теле');
 const warnings=projects.filter(p=>p.sourceWarnings?.length).length;
 $('project-notices').innerHTML=(sum.errors.length?`<div class="error">Свод недоступен: исправьте данные участков ${sum.errors.map(esc).join(', ')}. Итог не исключает ошибки молча.</div>`:'')+`<p class="project-footnote">${warnings?'Замечания к исходнику: '+warnings+' участка. ':''}Группы I–IV: ${complete&&!sum.soilErrors.length?sum.groups.map((x,i)=>['I','II','III','IV'][i]+' — '+f(x)+' м³').join(' · '):'распределение недоступно — проверьте доли в участках '+sum.soilErrors.map(esc).join(', ')}. Колодцы на стыках суммируются как отдельные записи исходника.</p>`;
 $('project-rows').innerHTML=projects.map(p=>{const r=calculateProject(p),ok=!r.errors.length;return `<tr class="${p.id===selectedId?'selected':''}"><th scope="row"><button class="route-button" data-select="${esc(p.id)}">${esc(p.name)}</button></th>${['totalExcavation','trench','materials','pipe','backfill','pitBackfill','exported'].map(k=>`<td>${f(ok?r[k]:NaN)}</td>`).join('')}<td><span class="state ${ok?'':'bad'}">${ok?(p.sourceWarnings?.length?'Исходник ⚑':r.soilErrors.length?'Грунт ?':r.warnings.length?'Округление':'Баланс ✓'):'Ошибка'}</span></td></tr>`}).join('');
}
function field(label,field,value,options={}){
 const attrs=`data-field="${field}" ${options.list?`data-list="${options.list}" data-index="${options.index}"`:''}`;
 return `<label>${label}<div class="input-wrap"><input ${attrs} aria-label="${esc(label)}" type="${options.text?'text':'number'}" ${options.text?'maxlength="300"':'step="any" min="0"'} value="${Number.isNaN(value)?'':esc(value)}">${options.unit?`<span>${options.unit}</span>`:''}</div></label>`;
}
function origin(x){return x?.cell?`<span class="origin" title="${esc(x.formula?'='+x.formula:'Исходное значение')}">${esc(x.cell)}${x.original!==undefined?' · '+f(x.original,5):''}</span>`:''}
function removeButton(list,i){return `<button type="button" class="remove-button" data-remove="${list}" data-index="${i}" aria-label="Удалить строку ${i+1}">×</button>`}
function renderEditor(){
 const p=current();if(!p){$('project-editor').innerHTML='<p class="project-footnote">Добавьте участок или копию исходного Excel.</p>';return}
 $('project-editor').innerHTML=`<div class="editor-title"><div><div class="eyebrow">ВЫБРАННЫЙ УЧАСТОК</div><h2 id="selected-title">${esc(p.name)}</h2></div><div class="toolbar-actions"><button class="button" id="duplicate-section">Создать копию</button><button class="button danger" id="delete-section">Удалить участок</button></div></div>
 <div id="selected-diagnostics"></div><div class="editor-grid">
 <section class="panel editor-panel"><h3>Выемка и группы грунта</h3>${field('Название участка','name',p.name,{text:true})}${field('Общая выемка, включая котлованы','totalExcavation',p.totalExcavation,{unit:'м³'})}${origin(p.totalSource)}<div class="group-inputs">${p.groups.map((x,i)=>field(['I','II','III','IV'][i]+' группа','percent',x,{list:'groups',index:i,unit:'%'})).join('')}</div><p class="editor-hint">Группы относятся ко всей выемке. Сумма долей — 100%. При добавлении котлована учитывайте его дополнительную выемку в общем объёме.</p><label>Примечание с ИГЭ<textarea data-field="soilNote" rows="3">${esc(p.soilNote||'')}</textarea></label>${p.source?`<p class="source-caption">${esc(p.source.file)}<br>Лист ${esc(p.source.sheet)}, ${esc(p.source.range)}</p>`:'<p class="source-caption">Участок создан в приложении.</p>'}${p.geometry?`<details><summary>Сохранённые параметры геометрии</summary><pre>${esc(JSON.stringify(p.geometry,null,2))}</pre></details>`:''}</section>
 <section class="panel editor-panel"><div class="panel-head"><h3>Материалы засыпки</h3><button class="text-button" data-add="materials">+ Материал</button></div><p class="editor-hint">Непересекающиеся объёмы слоёв. Подушка входит в общий объём ЩПС один раз.</p>${p.materials.map((x,i)=>`<div class="material-row">${field('Материал','name',x.name,{text:true,list:'materials',index:i})}${field('Объём','volume',x.volume,{list:'materials',index:i,unit:'м³'})}${removeButton('materials',i)}${origin(x)}</div>`).join('')}</section>
 <section class="panel editor-panel wide"><div class="panel-head"><h3>Трубы и футляры</h3><button class="text-button" data-add="pipes">+ Труба / футляр</button></div><p class="editor-hint">Excel использует расчётную площадь из формулы. Для новых труб можно выбрать наружный диаметр. Вложенную трубу внутри футляра отдельно не добавляйте: грунт вытесняет наружная оболочка.</p>${p.pipes.map((x,i)=>`<div class="item-card">${removeButton('pipes',i)}${field('Наименование трубы / футляра','name',x.name,{text:true,list:'pipes',index:i})}<div class="pipe-inputs"><label>Способ расчёта<select data-field="method" data-list="pipes" data-index="${i}"><option value="area" ${x.method==='area'?'selected':''}>Площадь из Excel, м²</option><option value="diameter" ${x.method==='diameter'?'selected':''}>Наружный диаметр, мм</option></select></label>${field('Длина','length',x.length,{list:'pipes',index:i,unit:'м'})}${x.method==='area'?field('Площадь','area',x.area,{list:'pipes',index:i,unit:'м²'}):field('Наружный диаметр','diameter',x.diameter,{list:'pipes',index:i,unit:'мм'})}${field('Количество','count',x.count,{list:'pipes',index:i,unit:'шт.'})}</div><div class="item-total">${origin(x)}<span>Вытеснение: <strong data-pipe-total="${i}">${f(pipeVolume(x))}</strong> м³</span></div></div>`).join('')||'<p class="editor-hint">Трубы не добавлены.</p>'}</section>
 <section class="panel editor-panel wide"><div class="panel-head"><h3>Колодцы, камеры и другие сооружения</h3><button class="text-button" data-add="structures">+ Сооружение</button></div><p class="editor-hint">Наружный вытесняемый объём сооружения и отдельный объём его котлована. Для конструкции внутри траншеи выберите соответствующее размещение: отдельный котлован для неё не вычитается.</p>${p.structures.map((x,i)=>`<div class="item-card">${removeButton('structures',i)}${field('Наименование сооружения','name',x.name,{text:true,list:'structures',index:i})}<label>Размещение<select data-field="placement" data-list="structures" data-index="${i}"><option value="pit" ${x.placement!=='trench'?'selected':''}>В отдельном котловане</option><option value="trench" ${x.placement==='trench'?'selected':''}>Внутри траншеи</option></select></label><div class="structure-inputs">${field('Вытесняемый объём','volume',x.volume,{list:'structures',index:i,unit:'м³'})}${x.placement!=='trench'?field('Выемка котлована','excavation',x.excavation,{list:'structures',index:i,unit:'м³'}):'<p class="editor-hint">Выемка уже учтена в траншее.</p>'}<div class="structure-result">Засыпка котлована<strong data-pit-total="${i}">${f(x.placement==='trench'?0:x.excavation-x.volume)} м³</strong></div></div><div class="item-total">${origin(x)}${origin(x.excavationSource)}</div>${x.soilNote?`<p class="editor-hint">${esc(x.soilNote)}</p>`:''}</div>`).join('')||'<p class="editor-hint">Сооружения не добавлены.</p>'}</section>
 <section class="panel editor-panel wide"><h3>Расчёт выбранного участка</h3><div id="selected-results"></div></section></div>`;
 $('duplicate-section').onclick=()=>{const duplicate=clone(p);duplicate.id=crypto.randomUUID();duplicate.name+=' (копия)';projects.push(duplicate);selectedId=duplicate.id;persist();render();status('Создана отдельная копия участка.')};
 $('delete-section').onclick=()=>{const i=projects.findIndex(x=>x.id===selectedId);projects.splice(i,1);selectedId=projects[Math.min(i,projects.length-1)]?.id;persist();render();status('Участок удалён. Сохраняйте JSON проекта для резервной копии.')};
 renderSelectedResults();
}
function renderSelectedResults(){
 const p=current();if(!p)return;const r=calculateProject(p);
 $('selected-title').textContent=p.name;
 $('selected-diagnostics').innerHTML=r.errors.map(x=>`<div class="error">${esc(x)}</div>`).join('')+[...(p.sourceWarnings||[]),...r.soilErrors,...r.warnings].map(x=>`<div class="source-warning">${esc(x)}</div>`).join('');
 const rows=[['Общая выемка',r.totalExcavation],['Выемка котлованов',r.pits],['Выемка траншеи',r.trench],['ЩПС / привозные материалы',r.materials],['Вытеснение трубами',r.pipe],['Вытеснение сооружениями',r.structures],['Обратная засыпка траншеи',r.backfill],['Обратная засыпка котлованов',r.pitBackfill],['Всего грунта на засыпку',r.groundBackfill],['Вывоз в плотном теле',r.exported]];
 $('selected-results').innerHTML=`<dl class="calculation-rows">${rows.map(([label,n])=>`<div><dt>${label}</dt><dd>${f(r.errors.length?NaN:n)} м³</dd></div>`).join('')}</dl><div class="source-comparison">${p.originalBackfill!==undefined?`<p>Исходный Excel ${esc(p.backfillSource?.cell)}: ${f(p.originalBackfill,5)} м³. Текущая засыпка до округления: ${f(r.rawBackfill,5)} м³. Разница: ${f(r.rawBackfill-p.originalBackfill,5)} м³.</p>`:''}<p>Баланс: общая выемка = грунт на засыпку + вывоз. ${r.errors.length?'Есть ошибки исходных данных.':'Невязка: '+f(p.totalExcavation-r.groundBackfill-r.exported,6)+' м³.'}</p></div>`;
 p.pipes.forEach((x,i)=>{const node=$('project-editor').querySelector(`[data-pipe-total="${i}"]`);if(node)node.textContent=f(pipeVolume(x))});
 p.structures.forEach((x,i)=>{const node=$('project-editor').querySelector(`[data-pit-total="${i}"]`);if(node)node.textContent=f(x.placement==='trench'?0:x.excavation-x.volume)+' м³'});
}
function render(){renderSummary();renderEditor()}
$('project-rows').onclick=e=>{const button=e.target.closest('[data-select]');if(button){selectedId=button.dataset.select;render()}};
$('project-editor').addEventListener('input',e=>{
 const node=e.target,field=node.dataset.field,p=current();if(!field||!p)return;
 const list=node.dataset.list,i=Number(node.dataset.index),value=node.type==='number'?(node.value.trim()===''?NaN:Number(node.value)):node.value;
 if(!list&&['name','totalExcavation','soilNote'].includes(field))p[field]=value;
 else if(list==='groups'&&Number.isInteger(i)&&i>=0&&i<4)p.groups[i]=value;
 else if(['materials','pipes','structures'].includes(list)&&p[list][i]&&['name','volume','excavation','length','area','diameter','count','method','placement'].includes(field))p[list][i][field]=value;
 persist();renderSummary();renderSelectedResults();if(field==='method'||field==='placement')renderEditor();
});
$('project-editor').addEventListener('click',e=>{
 const p=current(),add=e.target.closest('[data-add]'),remove=e.target.closest('[data-remove]');if(!p)return;
 if(add){const list=add.dataset.add;if(list==='materials')p.materials.push({name:'Новый материал',volume:0});if(list==='pipes')p.pipes.push({name:'Новая труба',length:1,diameter:315,area:0,method:'diameter',count:1});if(list==='structures')p.structures.push({name:'Новое сооружение',volume:0,excavation:0})}
 else if(remove){const list=remove.dataset.remove;if(['materials','pipes','structures'].includes(list))p[list].splice(Number(remove.dataset.index),1)}else return;
 persist();render();
});
$('new-project').onclick=()=>{const p=newProject('Новый участок '+(projects.length+1));projects.push(p);selectedId=p.id;persist();render();status('Новый участок добавлен. Введите общую выемку и состав работ.')};
$('load-source').onclick=()=>{
 const copies=clone(seedProjects);for(const p of copies){p.id=crypto.randomUUID();p.name+=' (Excel)'}projects.push(...copies);selectedId=copies[0].id;persist();render();status('Добавлена отдельная копия 16 участков исходного Excel. Ваши текущие участки сохранены; копии участвуют в общем итоге.')
};
window.addEventListener('add-geometry',e=>{
 const {p,r,name}=e.detail,section=newProject(name);section.totalExcavation=r.excavation;section.geometry=clone(p);section.materials[0].name='Подсыпка из геометрического расчёта';section.materials[0].volume=r.bed;
 if(p.objectType==='pipe')section.pipes.push({name:'Труба Ø '+p.diameter+' мм',length:p.length,diameter:p.diameter,area:0,method:'diameter',count:p.count});
 // An inline rectangular object is counted once as a non-backfilled subvolume.
 if(p.objectType==='box')section.structures.push({name:'Прямоугольная конструкция по всей длине',volume:r.structure,excavation:0,placement:'trench'});
 projects.push(section);selectedId=section.id;persist();render();setTab('project');status('Геометрический расчёт добавлен отдельным участком. Исходные 16 участков не изменены. Укажите доли групп грунта по проекту — до этого распределение по группам недоступно.');
 $('geometry-save-message').textContent='Участок добавлен в ведомость.';
});
function download(filename,content,type){const url=URL.createObjectURL(new Blob([content],{type})),a=document.createElement('a');a.href=url;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
function ensureExport(){try{normalize(projects);return true}catch(e){status('Экспорт не выполнен: '+e.message);return false}}
$('save-project').onclick=()=>{if(!ensureExport())return;download('earthworks-project.json',JSON.stringify({version:2,source:sourceInfo,projects},null,2),'application/json');status('JSON проекта сохранён. Его можно открыть на другом компьютере.')};
$('export-csv').onclick=()=>{
 if(!ensureExport())return;const rows=[['Участок','Раздел','Позиция','Ед. изм.','Значение','Источник / замечание']];
 for(const p of projects){const r=calculateProject(p);for(const[k,label]of Object.entries({totalExcavation:'Общая выемка',trench:'Выемка траншеи',pits:'Выемка котлованов',materials:'ЩПС',pipe:'Трубы',structures:'Сооружения',rawBackfill:'Засыпка траншеи (до округления)',pitBackfill:'Засыпка котлованов',groundBackfill:'Засыпка грунтом всего',exported:'Вывоз в плотном теле'}))rows.push([p.name,'Итог',label,'м³',r[k],[...r.errors,...r.soilErrors].join(' ')]);
 p.groups.forEach((x,i)=>{rows.push([p.name,'Грунт',['I','II','III','IV'][i]+' группа','%',x,'']);rows.push([p.name,'Грунт',['I','II','III','IV'][i]+' группа','м³',r.groups[i],''])});
 for(const x of p.materials)rows.push([p.name,'Материалы',x.name,'м³',x.volume,x.cell||'']);
 for(const x of p.pipes)rows.push([p.name,'Трубы',x.name,'м³',pipeVolume(x),(x.cell||'')+'; L='+x.length+'; '+(x.method==='area'?'S='+x.area:'D='+x.diameter)+'; n='+x.count]);
 for(const x of p.structures){rows.push([p.name,'Сооружения',x.name,'м³',x.volume,x.cell||'']);rows.push([p.name,'Котлованы',x.name,'м³',x.placement==='trench'?0:x.excavation,x.placement==='trench'?'Внутри траншеи':x.excavationSource?.cell||''])}
 for(const x of p.sourceWarnings||[])rows.push([p.name,'Замечание',x,'','','']);
 }
 const sum=summarizeProjects(projects);if(!sum.errors.length)for(const k of ['totalExcavation','trench','pits','materials','pipe','structures','rawBackfill','pitBackfill','groundBackfill','exported'])rows.push(['ВСЕГО','Свод',k,'м³',sum[k],'']);
 const cell=value=>{let s=typeof value==='number'?(Number.isFinite(value)?String(value).replace('.',','):'н/д'):String(value??'');if(typeof value!=='number'&&/^[\s]*[=+@-]/.test(s))s="'"+s;return '"'+s.replace(/"/g,'""')+'"'};
 download('earthworks-volumes.csv','\uFEFF'+rows.map(row=>row.map(cell).join(';')).join('\r\n'),'text/csv;charset=utf-8');status('CSV выгружен с детализацией и точными остатками. Откройте его в Excel.');
};
$('open-project').onchange=async e=>{
 const file=e.target.files[0];if(!file)return;
 try{if(file.size>10*1024*1024)throw Error('Файл больше 10 МБ.');const data=JSON.parse(await file.text());if(data.version!==2)throw Error('Ожидается проект версии 2.');const incoming=normalize(data.projects);for(const p of incoming){p.id=crypto.randomUUID();p.name+=' (импорт)'}projects.push(...incoming);selectedId=incoming[0]?.id||selectedId;persist();render();status('Добавлено '+incoming.length+' участков из JSON. Существующие данные сохранены.')}catch(error){status('Файл не открыт: '+error.message)}finally{e.target.value=''}
};
render();if(storageIssue)status(storageIssue);
