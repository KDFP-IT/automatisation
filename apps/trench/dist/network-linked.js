import {backfillName} from './backfill.js';
import {isPhysicalWell} from './node-geometry.js';
import {atStation,crossSection,sectionAt} from './network-model.js';
import {drawPlan,drawProfile,drawSection,esc,fmt} from './network-views.js';

export const clampRatio=r=>Math.max(0,Math.min(1,Number.isFinite(r)?r:0));
export const profileRatio=x=>clampRatio((x-85)/730);
export function nearestStationRatio(res,x,y){
 let best=Infinity,station=0;
 for(let i=1;i<res.points.length;i++){
  const a=res.points[i-1],b=res.points[i],dx=b.x-a.x,dy=b.y-a.y,den=dx*dx+dy*dy;
  if(den<=0)continue;
  const t=clampRatio(((x-a.x)*dx+(y-a.y)*dy)/den),distance=(x-a.x-t*dx)**2+(y-a.y-t*dy)**2;
  if(distance<best){best=distance;station=a.s+(b.s-a.s)*t}
 }
 return clampRatio(station/res.length);
}
export function stationInfo(e,res,ratio){
 const r=clampRatio(ratio),s=r*res.length,section=sectionAt(e,res,s),c=crossSection(e,res,section,s);
 const layers=e.layers.map((l,i)=>({soil:l.soil,top:i?e.layers[i-1].start+(e.layers[i-1].end-e.layers[i-1].start)*r:0,bottom:l.start+(l.end-l.start)*r}));
 return {ratio:r,s,section,index:e.sections.indexOf(section),c,layers};
}
export function linkedViews(p,result,e,res,ratio,showSoils){
 const info=stationInfo(e,res,ratio),{c,s}=info,plan=drawPlan(p,result,{kind:'edge',id:e.id}),q=plan.project(c.x,c.y),half=Math.max(1,c.top/2),normal=[-c.dy,c.dx];
 const a=plan.project(c.x+normal[0]*half,c.y+normal[1]*half),b=plan.project(c.x-normal[0]*half,c.y-normal[1]*half);
 plan.html+=`<g class="linked-station" pointer-events="none"><line x1="${a[0]}" y1="${a[1]}" x2="${b[0]}" y2="${b[1]}" stroke="#bd4b16" stroke-width="3" stroke-dasharray="5 3"/><circle cx="${q[0]}" cy="${q[1]}" r="8" fill="#fd6017" stroke="#fff" stroke-width="3"/><text x="${q[0]+13}" y="${q[1]-15}" class="station-marker-label">${fmt(s)} м</text></g>`;
 const metric=(label,value,unit='м',digits=3)=>`<div><dt>${label}</dt><dd>${fmt(value,digits)} <small>${unit}</small></dd></div>`;
 const metrics=`<p class="linked-chainage">${esc(res.from.name)} → ${esc(res.to.name)}<strong>${fmt(s)} / ${fmt(res.length)} м</strong></p><dl class="station-metrics">${metric('Отметка земли',c.ground)}${metric('Наружный низ трубы',c.invert)}${metric('Дно траншеи',c.bottom)}${metric('Глубина траншеи',c.depth)}${metric('Ширина дна',c.width)}${metric('Ширина поверху',c.top)}${metric('Местный уклон',-c.grade*1000,'‰')}${metric('Расчётный отрезок',info.index+1,'',0)}</dl><p class="station-method">${info.section.method==='supports'?'На опорах — выемки траншеи нет':'Открытая траншея'}${info.section.casing?' · футляр Ø '+fmt(info.section.casing*1000,0)+' мм':''}</p><h4>Границы грунтов в этой точке</h4><ul class="station-layers">${info.layers.map(l=>{const soil=p.soils.find(v=>v.id===l.soil);return `<li><i style="background:${soil?.color||'#ccc'}"></i><span>${esc(soil?.name||l.soil)}</span><b>${fmt(l.top)}–${fmt(l.bottom)} м</b></li>`}).join('')}</ul><p class="input-hint">Глубины границ от поверхности. План — в координатах проекта, вертикальный масштаб профиля отдельный.</p>`;
 return {plan:plan.html,profile:drawProfile(p,e,res,showSoils,info.ratio),section:drawSection(p,e,res,info.ratio,showSoils),metrics,unmap:plan.unmap};
}

// Subtotals deliberately separate trenches and well pits; each shared well is counted once.
export function networkReport(p,result){
 const rows=p.edges.map(e=>{const r=result.edges[e.id],valid=!!r&&!r.errors?.length&&Number.isFinite(r.excavation);return {id:e.id,name:e.name,from:p.wells.find(w=>w.id===e.from.well)?.name||'—',to:p.wells.find(w=>w.id===e.to.well)?.name||'—',length:r?.res?.length,diameter:e.diameter*1000,valid,errors:r?.errors||[],r}});
 const sum=items=>{const out={excavation:0,backfill:0,nativeBackfill:0,importedBackfill:0,fill:0,soils:Object.fromEntries(p.soils.map(s=>[s.id,0]))};for(const r of items){for(const key of ['excavation','backfill','nativeBackfill','importedBackfill','fill'])out[key]+=r?.[key]||0;for(const soil of p.soils)out.soils[soil.id]+=r?.soils?.[soil.id]||0}return out};
 return {rows,length:rows.reduce((n,r)=>n+(r.length||0),0),edges:sum(rows.filter(r=>r.valid).map(r=>r.r)),wells:sum(Object.values(result.wells).filter(r=>!r.errors?.length)),joints:sum((result.joints||[]).filter(r=>!r.errors?.length)),jointRows:result.joints||[],valid:result.valid,allEdgesValid:rows.every(r=>r.valid),total:result.total};
}
export function reportTable(p,result,selectedId){
 const report=networkReport(p,result),cells=(r,valid)=>`<td>${valid?fmt(r.excavation,3):'—'}</td><td>${valid?fmt(r.backfill,3):'—'}${valid?`<small class="backfill-breakdown">Вынутый: ${fmt(r.nativeBackfill||0,2)} · привозной: ${fmt(r.importedBackfill||0,2)}</small>`:''}</td>${p.soils.map(s=>`<td>${valid?fmt(r.soils?.[s.id]||0,3):'—'}</td>`).join('')}`;
 const summary=(label,r,valid,length='—')=>`<tr><th scope="row" colspan="3">${label}</th><td>${length}</td><td>—</td>${cells(r,valid)}</tr>`;
 return `<div class="report-heading"><div><h2>Таблица участков</h2><p>Объёмы в м³ · участки без общих стыков · длина в плане, м · диаметр, мм</p></div><span>${p.edges.length} участков · ${p.wells.filter(isPhysicalWell).length} колодцев</span></div><div class="report-scroll"><table><caption class="sr-only">Выемка, обратная засыпка и выемка по видам грунта</caption><thead><tr><th scope="col">Участок</th><th scope="col">От узла</th><th scope="col">До узла</th><th scope="col">Длина, м</th><th scope="col">Ø, мм</th><th scope="col">Выемка</th><th scope="col">Засыпка</th>${p.soils.map(s=>`<th scope="col"><i style="background:${s.color}"></i>${esc(s.name)}<small>Выемка, м³</small></th>`).join('')}</tr></thead><tbody>${report.rows.map(row=>`<tr class="${row.id===selectedId?'selected':''} ${row.valid?'':'invalid'}" data-report-edge="${esc(row.id)}"><th scope="row"><button data-action="edge" data-id="${esc(row.id)}">${esc(row.name)} ↗</button><small class="backfill-breakdown">Засыпка: ${esc(backfillName(p.edges.find(e=>e.id===row.id)))}</small>${row.valid?'':`<small class="report-error">${esc(row.errors.join('; ')||'Проверьте параметры')}</small>`}</th><td>${esc(row.from)}</td><td>${esc(row.to)}</td><td>${fmt(row.length)}</td><td>${fmt(row.diameter,0)}</td>${cells(row.r,row.valid)}</tr>`).join('')+report.jointRows.map(j=>`<tr class="joint-report-row"><th scope="row">Стык<small>${esc(j.names.join(' + '))}</small></th><td colspan="2">Общая выемка</td><td>—</td><td>—</td>${cells(j,!j.errors.length&&Number.isFinite(j.excavation))}</tr>`).join('')||`<tr><td colspan="${7+p.soils.length}">Добавьте участки, чтобы получить ведомость.</td></tr>`}</tbody><tfoot>${summary('Итого траншеи участков',report.edges,report.valid&&report.allEdgesValid,fmt(report.length))}${report.jointRows.length?summary('Итого стыки · '+report.jointRows.length,report.joints,report.valid):''}${summary('Котлованы колодцев · '+p.wells.filter(isPhysicalWell).length+' шт.',report.wells,report.valid)}${summary('Всего по проекту',report.total,report.valid,fmt(report.length))}</tfoot></table></div><div class="report-fill-summary"><span>Засыпка вынутым грунтом <b>${report.valid?fmt(report.total.nativeBackfill,3):'—'} м³</b></span><span>Всего привозных материалов <b>${report.valid?fmt((report.total.fill||0)+(report.total.importedBackfill||0),3):'—'} м³</b><small>включая подушку, обсыпку и подготовку</small></span></div><p class="report-note">Участки приведены без общих частей и без объёмов в котлованах. Общая выемка, материалы и засыпка стыков добавлены отдельными строками один раз. Котлованы добавлены отдельной строкой, каждый колодец учтён один раз. Грунты — состав выемки. Привозная засыпка в столбце не включает подушку, обсыпку и подготовку; их объём добавляется отдельно.${report.valid?'':' <strong>Общий итог не подтверждён: устраните замечания проекта. Числа в отдельных строках не являются итогом по сети.</strong>'}</p>`;
}
