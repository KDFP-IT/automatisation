from pathlib import Path
p=Path('dist/network-app.js');s=p.read_text(encoding='utf-8');a=s.index("$('inspector').addEventListener('change'");b=s.index("$('inspector').addEventListener('focusout'",a)
s=s[:a]+"""function commitPipeLength(node){if(node.dataset.command!=='pipe-length'||!node.dataset.invalidDraft)return;flushEdit();const before=clone(p);try{setPipeLength(p,edge().id,node.value===''?NaN:Number(node.value));delete node.dataset.invalidDraft;node.removeAttribute('aria-invalid');recordChange(before,'Длина трубы');persist();render()}catch(error){p=before;node.dataset.invalidDraft='true';node.setAttribute('aria-invalid','true');notify(error.message)}}
$('inspector').addEventListener('change',ev=>commitPipeLength(ev.target));
$('inspector').addEventListener('focusout',ev=>commitPipeLength(ev.target));
$('inspector').addEventListener('keydown',ev=>{if(ev.key==='Enter'&&ev.target.dataset.command==='pipe-length'){ev.preventDefault();commitPipeLength(ev.target)}});
"""+s[b:]
s=s.replace('Поставьте колодцы и соедините их.','Нарисуйте трубу или поставьте колодцы.').replace("'Поставьте колодцы'","'Добавьте трубу или колодец'")
p.write_text(s,encoding='utf-8')
p=Path('dist/index.html');s=p.read_text(encoding='utf-8').replace('⌁ Соединить','⌁ Труба');p.write_text(s,encoding='utf-8')
p=Path('dist/network-views.js');s=p.read_text(encoding='utf-8').replace('Поставьте первый колодец','Добавьте трубу или колодец').replace('Инструмент «Колодец» — щелчок по плану','«Труба» — начало и конец на плане');p.write_text(s,encoding='utf-8')
