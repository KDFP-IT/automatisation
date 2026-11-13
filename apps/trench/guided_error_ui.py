from pathlib import Path
f=Path('dist/issue-guidance.js');s=f.read_text(encoding='utf-8');s+="\nexport const diagnosticKey=v=>v.guidance?.key?'guided|'+v.guidance.key:v.code+'|'+(['geometry','calculation'].includes(v.code)?v.kind+'|'+v.objectId+'|':'')+v.message;\n";f.write_text(s,encoding='utf-8')
f=Path('dist/validation-ui.js');s=f.read_text(encoding='utf-8');s="import {diagnosticKey} from './issue-guidance.js';\n"+s
s=s.replace("export const issueKey=v=>v.code+'|'+(['geometry','calculation'].includes(v.code)?v.kind+'|'+v.objectId+'|':'')+v.message;", "export const issueKey=diagnosticKey;")
s=s.replace("export function issueText(p,issue){const req=", "export function issueText(p,issue){if(issue.guidance){const object=(issue.kind==='well'?p.wells:p.edges).find(v=>v.id===issue.objectId);return [issue.guidance.title,object?.name||'',issue.guidance.directions.join(' ')]}const req=")
a=s.index('export function issueButton(');b=s.index('export function diagnosticsHTML',a)
s=s[:a]+'''export function issueButton(p,issue){const prefix=(issue.kind==='well'?'wells.'+p.wells.findIndex(v=>v.id===issue.objectId):'edges.'+p.edges.findIndex(v=>v.id===issue.objectId))+'.',focusPath=issue.paths?.find(v=>v.startsWith(prefix))||issue.paths?.[0]||'',object=(issue.kind==='well'?p.wells:p.edges).find(v=>v.id===issue.objectId),[title,context,help]=issueText(p,issue),g=issue.guidance;
 const repairs=g?.repairs?.map(r=>`<button data-action="repair-issue" data-kind="${r.kind}" data-id="${esc(r.id)}" data-repair-path="${esc(r.path)}" data-repair-tab="${r.tab}" data-repair-section="${r.section??g.section??''}" data-repair-station="${r.station??g.station??''}" data-repair-end="${r.end||''}">${esc(r.label)} →</button>`).join('');
 return `<article class="validation-issue ${isCalculationLimit(issue)?'limitation':issue.severity}"><b>${esc(title)}</b>${context?`<span>${esc(context)}</span>`:''}${g?.facts?.length?`<div class="issue-facts">${g.facts.map(f=>`<span>${esc(f)}</span>`).join('')}</div>`:''}<span>${esc(help)}</span>${limitDimensionsHTML(p,issue)}<div class="issue-actions"><button data-action="show-problem" data-issue-key="${esc(issueKey(issue))}">Показать на плане</button>${repairs|| (object?`<button data-action="issue" data-kind="${issue.kind}" data-id="${esc(issue.objectId)}" data-issue-code="${esc(issue.code)}" data-issue-section="${issue.sectionsByEdge?.[issue.objectId]??''}" data-issue-tab="${issue.tab||'geometry'}" data-issue-path="${esc(focusPath)}">${isSoilCoverage(issue)?'Задать грунты':isCalculationLimit(issue)?'Посмотреть размеры':'Открыть параметры'}</button>`:'')}</div></article>`;
}
'''+s[b:]
s=s.replace(" for(const node of root.querySelectorAll('[data-validation-paths]'))", " for(const note of root.querySelectorAll('.field-issue'))note.remove();\n for(const node of root.querySelectorAll('[data-validation-paths]'))")
s=s.replace("const found=issues.filter(v=>", "const found=issues.filter(v=>") # actual minified sequence below
old="!relational.has(v.code)&&!v.message.startsWith('Исправьте параметры колодца')&&v.paths?.some(k=>path===k||path.startsWith(k+'.'))"
new="(!relational.has(v.code)||v.guidance?.badPaths?.length)&&!v.message.startsWith('Исправьте параметры колодца')&&(v.guidance?.badPaths||v.paths)?.some(k=>path===k||path.startsWith(k+'.'))"
assert old in s;s=s.replace(old,new)
s=s.replace("node.title=[...new Set(found.map(v=>v.message))].join('\\n')", "node.title=[...new Set(found.map(v=>v.guidance?.directions.join(' ')||v.message))].join('\\n');const note=document.createElement('small');note.className='field-issue';note.textContent=found[0].guidance?.directions[0]||found[0].message;node.closest('label')?.append(note)")
f.write_text(s,encoding='utf-8')
f=Path('dist/network-views.js');s=f.read_text(encoding='utf-8');s="import {diagnosticKey} from './issue-guidance.js';\n"+s
s=s.replace("selected?.issueFocus===v.code+'|'+v.message", "selected?.issueFocus===diagnosticKey(v)")
needle=" if(result.jointRegions?.length)html+="
new=""" const markerKeys=new Set();for(const issue of result.issues||[]){if(issue.severity!=='error'||!issue.location||!issue.location.slice(0,2).every(Number.isFinite))continue;const ids=[issue.objectId,...(issue.related||[])],key=diagnosticKey(issue);if(selected&&!ids.includes(selected.id)&&selected.issueFocus!==key||markerKeys.has(key))continue;markerKeys.add(key);const q=P(issue.location[0],issue.location[1]);html+=`<g class="error-location-marker" pointer-events="none"><circle cx="${q[0]}" cy="${q[1]}" r="16" fill="#fef2f255" stroke="#d34f3d" stroke-width="2"/><path d="M${q[0]-5} ${q[1]-5}L${q[0]+5} ${q[1]+5}M${q[0]-5} ${q[1]+5}L${q[0]+5} ${q[1]-5}" stroke="#d34f3d" stroke-width="2"/>${selected?.issueFocus===key?text([q[0],q[1]-24],'Место ошибки','class="conflict-label"'):''}</g>`}
"""
assert needle in s;s=s.replace(needle,new+needle)
f.write_text(s,encoding='utf-8')
f=Path('dist/network-app.js');s=f.read_text(encoding='utf-8')
s=s.replace("v.code==='rect-port-normal'?portIssueCard(v):issueButton(p,v)", "v.code==='rect-port-normal'?portIssueCard(v):issueButton(p,v)")
# Add dedicated navigation which targets exactly the offending section and parameter.
needle=" if(a==='show-problem'){"
addition=""" if(a==='repair-issue'){
 if(el.dataset.kind==='well')showWell(id);else showEdge(id);
 const section=Number(el.dataset.repairSection),station=Number(el.dataset.repairStation),route=edge(),resolved=route&&result.edges[route.id]?.res;
 if(el.dataset.repairSection!==''&&route?.sections[section]){state.section=section;state.ratio=(route.sections[section].a+route.sections[section].b)/2}
 if(el.dataset.repairStation!==''&&resolved?.length>0){state.ratio=clampRatio(station/resolved.length);syncStationSection()}
 state.inspectorTab=el.dataset.repairTab||'geometry';state.inspectorOpen=true;renderInspector();renderCanvas();let path=el.dataset.repairPath;
 if(el.dataset.repairEnd&&route){const ref=route[el.dataset.repairEnd],i=p.wells.findIndex(w=>w.id===ref.well),j=p.wells[i]?.ports.findIndex(port=>port.id===ref.port);path=`wells.${i}.ports.${j}.invert`}
 const node=[...$('inspector').querySelectorAll('[data-validation-paths]')].find(n=>n.dataset.validationPaths===path)||[...$('inspector').querySelectorAll('[data-path]')].find(n=>n.dataset.path===path);
 if(node){for(let parent=node.parentElement;parent&&parent!==$('inspector');parent=parent.parentElement)if(parent.tagName==='DETAILS')parent.open=true;node.focus({preventScroll:true});node.scrollIntoView({block:'nearest'});node.classList.add('repair-focus');setTimeout(()=>node.classList.remove('repair-focus'),2500)}else $('inspector').scrollTop=0;return;
 }
"""
assert needle in s;s=s.replace(needle,addition+needle)
s=s.replace("planFrame=issue.polygon?planRegionFrame(", "planFrame=issue.location&&!issue.polygon?planRegionFrame([issue.location.slice(0,2)]):issue.polygon?planRegionFrame(")
f.write_text(s,encoding='utf-8')
