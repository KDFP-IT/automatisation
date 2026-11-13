from pathlib import Path
p=Path('dist/network-model.js');s=p.read_text(encoding='utf-8');s="import {integrateJointTrenches} from './joint-excavation.js';\n"+s
s=s.replace("issues=inspectNetwork(p,{resolveEdge,wellGeometry,atStation,crossSection,pitInterval});", "issues=inspectNetwork(p,{resolveEdge,wellGeometry,atStation,crossSection,pitInterval}).map(v=>v.code==='trench-overlap'?{...v,severity:'info',jointStatus:'pending'}:v);")
a=s.index(' for(let i=0;i<p.edges.length;i++)for(let j=i+1;j<p.edges.length;j++){',s.index('export function calculateNetwork'))
b=s.index(" for(const [kind,items,values]",a)
s=s[:a]+''' const joints=[],jointRegions=[],numerical=[];
 // Solve whole connected overlap groups; a triple overlap must never be treated as three pair subtractions.
 const pending=issues.filter(v=>v.code==='trench-overlap'),groups=[];for(const issue of pending){const ids=new Set([issue.objectId,...(issue.related||[])]),matches=groups.filter(g=>[...ids].some(id=>g.has(id)));for(const g of matches){for(const id of g)ids.add(id);groups.splice(groups.indexOf(g),1)}groups.push(ids)}
 for(const ids of groups){const members=p.edges.filter(e=>ids.has(e.id)),ready=members.every(e=>edges[e.id]&&!edges[e.id].errors.length),regions=pending.filter(v=>ids.has(v.objectId));if(!ready){for(const v of regions){v.message='Заполните исходные данные участков для расчёта общей выемки.';v.jointStatus='pending'}continue}
  try{const union=integrateJointTrenches(p,members,{resolveEdge,crossSection,wellGeometry,pitInterval},options);numerical.push(union.numerical);
   for(const e of members){const old=edges[e.id];edges[e.id]={...old,...union.edges[e.id],excluded:old.excluded,grossExcavation:old.excavation,sharedExcavation:union.joints.filter(v=>v.edgeIds.includes(e.id)).reduce((n,v)=>n+v.excavation,0)}}
   joints.push(...union.joints);for(const v of regions){v.jointStatus='calculated';if(!jointRegions.some(r=>r.message===v.message))jointRegions.push({...v})}
   for(const conflict of union.conflicts){const names=conflict.edgeIds.map(id=>p.edges.find(e=>e.id===id).name),soilNames=conflict.soilIds.map(id=>p.soils.find(v=>v.id===id)?.name||'не указан'),message='В общей выемке участков «'+names.join('» и «')+'» в одном месте указаны разные грунты: '+soilNames.join(' / ')+'. Согласуйте слои грунта.';errors.push(message);for(const id of conflict.edgeIds){edges[id].errors.push(message);issues.push({code:'joint-soil-conflict',severity:'error',kind:'edge',objectId:id,related:conflict.edgeIds.filter(v=>v!==id),message,paths:['edges.'+p.edges.findIndex(e=>e.id===id)+'.layers'],tab:'soils',location:conflict.location})}}
  }catch(error){const message='Не удалось рассчитать общую выемку: '+error.message;errors.push(message);for(const v of regions){v.jointStatus='failed';v.severity='error';v.message=message}}
 }
 // Successfully calculated overlaps are quantities, not diagnostics requiring user correction.
 for(let i=issues.length-1;i>=0;i--)if(issues[i].code==='trench-overlap'&&issues[i].jointStatus==='calculated')issues.splice(i,1);
'''+s[b:]
s=s.replace("[...Object.values(wells),...Object.values(edges)])if(!r.errors.length)", "[...Object.values(wells),...Object.values(edges),...joints])if(!r.errors.length)")
s=s.replace("warnings.push('Расчёт траншей — численное интегрирование. Котлованы исключаются из траншей по геометрии. Сложные перекрытия контуров траншей вне котлованов требуют инженерной проверки.');", "warnings.push('Расчёт траншей — численное интегрирование. Котлованы исключаются из траншей по геометрии. Общая выемка пересекающихся траншей учтена один раз отдельными строками стыков.');")
s=s.replace("return {wells,edges,total,issues,errors:", "return {wells,edges,joints,jointRegions,numerical,total,issues,errors:")
p.write_text(s,encoding='utf-8')
