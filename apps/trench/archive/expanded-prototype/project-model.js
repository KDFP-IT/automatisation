export const materialNames=['Подушка из ЩПС','Засыпка из ЩПС','Защитный слой из ЩПС','Засыпка траншеи ЩПС'];
export function newProject(name='Новый участок'){
 return {id:crypto.randomUUID(),name,totalExcavation:0,materials:materialNames.map(name=>({name,volume:0})),pipes:[],structures:[],groups:[0,0,0,0],sourceWarnings:[],soilNote:''};
}
export function pipeVolume(p){return p.length*(p.method==='diameter'?Math.PI*(p.diameter/1000)**2/4:p.area)*(p.count??1)}
export function calculateProject(p){
 const errors=[],soilErrors=[],warnings=[];const nonnegative=(v,label)=>{if(!Number.isFinite(v)||v<0)errors.push(label+': введите число не меньше нуля.')};
 nonnegative(p.totalExcavation,'Общая выемка');
 for(const x of p.materials)nonnegative(x.volume,x.name);
 for(const x of p.pipes){nonnegative(x.length,'Длина трубы');nonnegative(x.method==='diameter'?x.diameter:x.area,'Диаметр / площадь трубы');if(!Number.isInteger(x.count)||x.count<1)errors.push('Количество труб должно быть целым положительным числом.');if(!['area','diameter'].includes(x.method))errors.push('Неизвестный способ расчёта трубы.')}
 for(const x of p.structures){nonnegative(x.volume,'Объём сооружения');nonnegative(x.excavation,'Выемка котлована');if(x.placement!=='trench'&&x.excavation+1e-9<x.volume)errors.push('Выемка котлована меньше объёма сооружения «'+x.name+'».')}
 for(const x of p.groups)if(!Number.isFinite(x)||x<0)soilErrors.push('Доля группы грунта должна быть числом не меньше нуля.');
 const groupPercent=p.groups.reduce((a,b)=>a+b,0);
 if(Math.abs(groupPercent-100)>.0001)soilErrors.push('Сумма долей групп грунта должна быть 100%, сейчас '+groupPercent.toFixed(3)+'%.');
 const materials=p.materials.reduce((a,x)=>a+x.volume,0),pipe=p.pipes.reduce((a,x)=>a+pipeVolume(x),0);
 const structures=p.structures.reduce((a,x)=>a+x.volume,0),pits=p.structures.reduce((a,x)=>a+(x.placement==='trench'?0:x.excavation),0);
 const inlineStructures=p.structures.reduce((a,x)=>a+(x.placement==='trench'?x.volume:0),0);
 const trench=p.totalExcavation-pits,pitBackfill=pits-(structures-inlineStructures),rawBackfill=trench-materials-pipe-inlineStructures;
 if(trench < -.001)errors.push('Котлованы превышают общую выемку.');
 if(rawBackfill < -.001)errors.push('Материалы и трубы превышают объём траншеи на '+(-rawBackfill).toFixed(3)+' м³. Проверьте исходные данные.');
 const backfill=Math.abs(rawBackfill)<.001?0:rawBackfill;
 if(Math.abs(rawBackfill)>1e-9&&Math.abs(rawBackfill)<.001)warnings.push('Остаток округления засыпки '+rawBackfill.toFixed(5)+' м³ показан как 0,000 м³. Исходный остаток сохранён в экспорте.');
 const exported=materials+pipe+structures;
 return {totalExcavation:p.totalExcavation,trench,pits,materials,pipe,structures,inlineStructures,pitBackfill,rawBackfill,backfill,groundBackfill:rawBackfill+pitBackfill,displaced:exported,exported,groups:p.groups.map(x=>soilErrors.length?NaN:p.totalExcavation*x/100),errors:[...new Set(errors)],soilErrors:[...new Set(soilErrors)],warnings};
}
export function summarizeProjects(projects){
 const keys=['totalExcavation','trench','pits','materials','pipe','structures','pitBackfill','rawBackfill','groundBackfill','exported'];
 const total=Object.fromEntries(keys.map(k=>[k,0]));total.groups=[0,0,0,0];total.errors=[];total.soilErrors=[];
 for(const p of projects){const r=calculateProject(p);if(r.soilErrors.length)total.soilErrors.push(p.name);if(r.errors.length){total.errors.push(p.name);continue}for(const k of keys)total[k]+=r[k];r.groups.forEach((x,i)=>total.groups[i]+=x)}
 total.count=projects.length;return total;
}
