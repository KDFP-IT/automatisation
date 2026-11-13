from pathlib import Path
f=Path('dist/network-app.js');s=f.read_text(encoding='utf-8')
a=s.index('function backfillControls(');b=s.index('function fillTotals(',a)
s=s[:a]+'''function backfillControls(target,base){return select('Чем засыпать',base+'.backfillSource',target.backfillSource||'excavated',[['excavated','Вынутый грунт'],['imported','Привозной материал']])+(target.backfillSource==='imported'?field('Материал засыпки',base+'.backfillMaterial',target.backfillMaterial||'Песок',{type:'text',hint:'Например: песок или песчано-гравийная смесь.'}):'')}
'''+s[b:]
s=s.replace("${n(r?.backfill)} м³</dd>", "${n((r?.backfill||0)+(r?.fill||0))} м³</dd>")
s=s.replace('Всего обратная засыпка','Всего с подушкой и обсыпкой')
s=s.replace("(s.around?field('Слой над верхом '", "(s.around?field('Материал обсыпки',base+'.aroundMaterial',s.aroundMaterial||'Песок',{type:'text'})+field('Слой над верхом '")
s=s.replace("'backfillMaterial'].includes(parts.at(-1))", "'backfillMaterial','aroundMaterial'].includes(parts.at(-1))")
s=s.replace("if(node.readOnly&&well()?.heightMode==='total')", "if(value===undefined){const key=node.dataset.path.split('.').at(-1);if(key==='backfillSource')value='excavated';if(['backfillMaterial','aroundMaterial'].includes(key))value='Песок'}if(node.readOnly&&well()?.heightMode==='total')")
# single-object task list stays local; project task list is available below the plan
s=s.replace("soilTasksHTML(p,all)+errors", "soilTasksHTML(p,issues.filter(v=>v.kind===kind&&v.objectId===id))+errors")
f.write_text(s,encoding='utf-8')
f=Path('dist/network-model.js');s=f.read_text(encoding='utf-8').replace('Общая высота меньше суммы рабочей части','Высота колодца меньше суммы рабочей части')
s=s.replace("id(v.id);if(v.beddingMaterial", "id(v.id);if(v.aroundMaterial!==undefined&&(typeof v.aroundMaterial!=='string'||!v.aroundMaterial.trim()||v.aroundMaterial.length>180))throw Error('Укажите материал обсыпки.');if(v.beddingMaterial")
f.write_text(s,encoding='utf-8')
f=Path('api/app.py');s=f.read_text(encoding='utf-8').replace("            identifier(section.get('id'))", "            if 'aroundMaterial' in section and (not isinstance(section['aroundMaterial'], str) or not section['aroundMaterial'].strip() or len(section['aroundMaterial']) > 180):\n                raise ValueError('Укажите материал обсыпки.')\n            identifier(section.get('id'))");f.write_text(s,encoding='utf-8')
f=Path('dist/network-linked.js');s=f.read_text(encoding='utf-8');s="import {backfillName} from './backfill.js';\n"+s
s=s.replace("backfill:0,soils:","backfill:0,nativeBackfill:0,importedBackfill:0,fill:0,soils:")
s=s.replace("for(const key of ['excavation','backfill'])", "for(const key of ['excavation','backfill','nativeBackfill','importedBackfill','fill'])")
s=s.replace("${valid?fmt(r.backfill,3):'—'}</td>","${valid?fmt(r.backfill,3):'—'}${valid?`<small class=\"backfill-breakdown\">Вынутый: ${fmt(r.nativeBackfill||0,2)} · привозной: ${fmt(r.importedBackfill||0,2)}</small>`:''}</td>")
s=s.replace("<button data-action=\"edge\" data-id=\"${esc(row.id)}\">${esc(row.name)} ↗</button>","<button data-action=\"edge\" data-id=\"${esc(row.id)}\">${esc(row.name)} ↗</button><small class=\"backfill-breakdown\">Засыпка: ${esc(backfillName(p.edges.find(e=>e.id===row.id)))}</small>")
s=s.replace("Грунты — состав выемки, а не дополнительный объём.","Грунты — состав выемки. Привозная засыпка в столбце не включает подушку, обсыпку и подготовку; их объём добавляется отдельно.")
s=s.replace("</tfoot></table></div><p class=\"report-note\">", "</tfoot></table></div><div class=\"report-fill-summary\"><span>Засыпка вынутым грунтом <b>${report.valid?fmt(report.total.nativeBackfill,3):'—'} м³</b></span><span>Всего привозных материалов <b>${report.valid?fmt((report.total.fill||0)+(report.total.importedBackfill||0),3):'—'} м³</b><small>включая подушку, обсыпку и подготовку</small></span></div><p class=\"report-note\">")
f.write_text(s,encoding='utf-8')
f=Path('dist/validation-ui.js');s=f.read_text(encoding='utf-8').replace("cmd==='floor'?`wells.${well}.workingHeight`", "['floor','well-working-height'].includes(cmd)?`wells.${well}.workingHeight`:cmd==='well-height'?`wells.${well}.height`");f.write_text(s,encoding='utf-8')
