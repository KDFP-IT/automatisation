from pathlib import Path
p=Path('dist/network-app.js');s=p.read_text(encoding='utf8')
needle="body+=`<div class=\"connection-label\">${esc(res.from.name)} → ${esc(res.to.name)}</div>`+field('Наружный диаметр трубы'"
replacement="body+=`<div class=\"connection-label\">${esc(res.from.name)} → ${esc(res.to.name)}</div>`+field('Длина участка в плане','',res.length,{unit:'м',command:'length',hint:'Масштабирует точки участка и перемещает конечный узел. Связанные участки тоже меняются.'})+field('Направление первого звена','',bearing(res,'from'),{unit:'°',command:'bearing',hint:'Угол от оси X против часовой стрелки. Поворачивает участок вместе с конечным узлом.'})+field('Наружный диаметр трубы'"
assert needle in s;s=s.replace(needle,replacement,1)
# Synchronize dependent inputs without destroying focus while the user types.
needle='persist()}\nfunction pathSet'
replacement='''syncInputs();persist()}
function syncInputs(){
 for(const node of $('inspector').querySelectorAll('[data-path]')){
  if(node===document.activeElement)continue;let value=p;
  for(const key of node.dataset.path.split('.'))value=value?.[key];
  if(node.type==='checkbox')node.checked=!!value;else node.value=value===null?'':number(value);
 }
 for(const node of $('inspector').querySelectorAll('[data-command]')){
  if(node===document.activeElement)continue;const command=node.dataset.command;
  if(command==='floor'&&well())node.value=number(wellGeometry(well()).floor);
  const e=edge(),res=e&&result.edges[e.id]?.res;if(!res)continue;
  if(command==='grade')node.value=number((res.portA.invert-res.portB.invert)/res.length*1000);
  if(command==='length')node.value=number(res.length);
  if(command==='bearing')node.value=number(bearing(res,'from'));
  if(command==='boundary'){const sec=e.sections[Number(node.dataset.index)];if(sec)node.value=number(sec[node.dataset.part]*res.length)}
 }
}
function pathSet'''
assert needle in s;s=s.replace(needle,replacement,1)
p.write_text(s,encoding='utf8')
