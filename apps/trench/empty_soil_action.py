from pathlib import Path
p=Path('dist/network-app.js');s=p.read_text(encoding='utf-8').replace("function layersEditor(layers,path,isWell=false){\n", "function layersEditor(layers,path,isWell=false){\n if(!layers.length)return `<div class=\"empty-soil-actions\"><button class=\"button orange-button\" data-action=\"add-layer\" data-target=\"${path}\">+ Добавить первый слой</button><button class=\"inline-add\" data-action=\"catalog\">Справочник грунтов</button></div>`;\n")
p.write_text(s,encoding='utf-8')
p=Path('dist/validation.css');p.write_text(p.read_text(encoding='utf-8')+'\n.empty-soil-actions{display:grid;gap:8px;margin-top:12px}.limit-dimensions small{display:block;margin-top:4px;font-size:11px;color:#657786}\n',encoding='utf-8')
