from pathlib import Path
f=Path('dist/node-geometry.js');s=f.read_text(encoding='utf-8').replace("w.heightMode==='total'?1.8:w.workingHeight","w.heightMode==='total'?(w.workingHeightOverride??1.8):w.workingHeight");f.write_text(s,encoding='utf-8')
f=Path('dist/constructor-core.js');s=f.read_text(encoding='utf-8');s+='''\nexport function setWellHeight(w,value){if(!Number.isFinite(value)||value<=0)throw Error('Задайте положительную высоту колодца.');const g=wellGeometry(w);Object.assign(w,{heightMode:'total',height:value,workingHeight:g.workingHeight,workingHeightOverride:g.workingHeight})}\nexport function setWellWorkingHeight(w,value){if(!Number.isFinite(value)||value<=0)throw Error('Рабочая часть должна быть больше нуля.');const g=wellGeometry(w);Object.assign(w,{heightMode:'total',height:g.height,workingHeight:value,workingHeightOverride:value})}\n''';f.write_text(s,encoding='utf-8')
f=Path('dist/network-model.js');s=f.read_text(encoding='utf-8');s="import {assignBackfill,validateBackfill} from './backfill.js';\n"+s
s=s.replace("Высота колодца меньше 1,8 м + перекрытие + днище. Горловина не может быть отрицательной.","Общая высота меньше суммы рабочей части, перекрытия и днища. Увеличьте общую высоту или уменьшите рабочую часть.")
s=s.replace("wells[w.id]={...g,errors:ownErrors,soils:wellSoils(p,w,g)}", "wells[w.id]={...assignBackfill(g,w),errors:ownErrors,soils:wellSoils(p,w,g)}")
s=s.replace("edges[e.id]={...r,res,errors:ownErrors}","edges[e.id]={...assignBackfill(r,e),res,errors:ownErrors}")
s=s.replace("const total={excavation:0,backfill:0,pipe:0,fill:0,soils:soilTotals}","const total={excavation:0,backfill:0,nativeBackfill:0,importedBackfill:0,pipe:0,fill:0,soils:soilTotals}")
s=s.replace("for(const k of ['excavation','backfill','pipe','fill'])total", "for(const k of ['excavation','backfill','nativeBackfill','importedBackfill','pipe','fill'])total")
s=s.replace("for(const w of input.wells){id(w.id);", "for(const w of input.wells){validateBackfill(w);if(w.workingHeightOverride!==undefined){finite(w.workingHeightOverride,'Рабочая часть');if(w.workingHeightOverride<=0)throw Error('Рабочая часть должна быть больше нуля.')}id(w.id);")
# edge validation loop locate generically
s=s.replace("for(const e of input.edges){", "for(const e of input.edges){validateBackfill(e);")
# conflict handling after union conflicts; insertion before catch (inside group)
needle="  }catch(error){const message='Не удалось рассчитать общую выемку: '"
addition="""   for(const conflict of union.backfillConflicts||[]){const message='В общей части траншей заданы разные материалы засыпки. Выберите одинаковый материал у участков «'+conflict.edgeIds.map(id=>p.edges.find(e=>e.id===id).name).join('» и «')+'».';errors.push(message);for(const id of conflict.edgeIds){edges[id].errors.push(message);issues.push({code:'joint-backfill-conflict',severity:'error',kind:'edge',objectId:id,related:conflict.edgeIds.filter(v=>v!==id),message,paths:['edges.'+p.edges.findIndex(e=>e.id===id)+'.backfillSource'],tab:'bedding'})}for(const joint of union.joints)if(joint.edgeIds.some(id=>conflict.edgeIds.includes(id)))joint.errors.push(message)}
"""
assert needle in s;s=s.replace(needle,addition+needle)
f.write_text(s,encoding='utf-8')
f=Path('dist/joint-excavation.js');s=f.read_text(encoding='utf-8');s="import {backfillSource,backfillName} from './backfill.js';\n"+s
s=s.replace("'protection','backfill'","'protection','backfill','nativeBackfill','importedBackfill'")
s=s.replace("joints=new Map(),conflicts=new Map()", "joints=new Map(),conflicts=new Map(),backfillConflicts=new Map()")
s=s.replace("target[category]+=volume;", """target[category]+=volume;
     if(category==='backfill'){const specs=[...new Set(active.map(v=>backfillSource(v.part.e)+':'+backfillName(v.part.e)))];target[backfillSource(active[0].part.e)==='imported'?'importedBackfill':'nativeBackfill']+=volume;if(specs.length>1&&!backfillConflicts.has(key))backfillConflicts.set(key,{edgeIds:ids})}
""")
s=s.replace("return {edges:rows,joints:","return {backfillConflicts:[...backfillConflicts.values()],edges:rows,joints:")
f.write_text(s,encoding='utf-8')
f=Path('api/app.py');s=f.read_text(encoding='utf-8');needle='    wells = {}';helper="""    def backfill_settings(obj):
        if obj.get('backfillSource', 'excavated') not in ['excavated', 'imported']:
            raise ValueError('Выберите материал засыпки.')
        if 'backfillMaterial' in obj and (not isinstance(obj['backfillMaterial'], str) or not obj['backfillMaterial'].strip() or len(obj['backfillMaterial']) > 180):
            raise ValueError('Укажите материал засыпки.')

""";assert needle in s;s=s.replace(needle,helper+needle,1)
s=s.replace("identifier(well.get('id')); name(well.get('name'))", "backfill_settings(well)\n        if 'workingHeightOverride' in well:\n            number(well['workingHeightOverride'])\n            if well['workingHeightOverride'] <= 0: raise ValueError('Рабочая часть должна быть больше нуля.')\n        identifier(well.get('id')); name(well.get('name'))")
s=s.replace("for edge in model['edges']:","for edge in model['edges']:\n        backfill_settings(edge)")
f.write_text(s,encoding='utf-8')
