from pathlib import Path
f=Path('dist/parameter-sketches.js');s=f.read_text(encoding='utf-8')
s=s.replace("const a=res.points[0],b=", "if(!Number.isFinite(res.length)||res.length<=0||!res.points?.length)return '<svg viewBox=\"0 0 340 180\"><text x=\"20\" y=\"80\">Задайте ненулевую длину трубы.</text></svg>';\n const a=res.points[0],b=")
s=s.replace('stroke-width="8" stroke-linejoin="round"','stroke-width="${Math.min(18,Math.max(4,e.diameter*20))}" stroke-linejoin="round"')
s=s.replace('cx="55" cy="150" r="17"','cx="55" cy="150" r="${Math.min(23,Math.max(8,e.diameter*40))}"')
s=s.replace('<path d="M${xl} ${bottom}H${xr}V${bed}H${xl}Z"', '<path d="M${xl} ${bottom}H${xr}L${X(c.width/2+c.right*s.bedding)} ${bed}H${X(-c.width/2-c.left*s.bedding)}Z"')
s=s.replace('<circle cx="${X(0)}" cy="${axis}" r="${Math.max(3,r)}"', '${s.casing?`<circle cx="${X(0)}" cy="${axis}" r="${Math.max(3,c.radius*Math.min(scale,sz))}" fill="#c8d3dc" stroke="#527791"/>`:""}<circle cx="${X(0)}" cy="${axis}" r="${Math.max(3,r)}"')
f.write_text(s,encoding='utf-8')
f=Path('dist/network-app.js');s=f.read_text(encoding='utf-8');a=s.index("$('inspector').addEventListener('focusin',ev=>{const cmd=",s.index('projectLibrary.start();'))
s=s[:a]+'''function highlightParameterSketches(){const node=document.activeElement,cmd=node?.dataset?.command,path=node?.dataset?.path;let part=cmd==='well-height'?'height':cmd==='well-neck-height'?'neck':cmd==='well-working-height'?'work':cmd==='pipe-length'?'pipe-length':cmd==='diameter-mm'?'pipe-diameter':path?.endsWith('.base')?'base':path?.endsWith('.slab')?'slab':null;
 if(path?.includes('.sections.')){const key=path.split('.').at(-1);part={width:'trench-width',topWidth:'trench-top',left:'trench-left',right:'trench-right',slopeMode:'trench-top'}[key]||part}
 const route=edge();if(route&&path?.endsWith('.invert'))for(const [side,label]of [['from','pipe-from'],['to','pipe-to']]){const i=p.wells.findIndex(w=>w.id===route[side].well),j=p.wells[i]?.ports.findIndex(v=>v.id===route[side].port);if(path===`wells.${i}.ports.${j}.invert`)part=label}
 for(const item of $('inspector').querySelectorAll('[data-dimension]'))item.classList.toggle('part-active',item.dataset.dimension===part)
}
$('inspector').addEventListener('focusin',highlightParameterSketches);
'''
s=s.replace("syncInputs();syncLayerDepths();renderBeddingMetrics();renderValidation();persist()", "syncInputs();syncLayerDepths();renderBeddingMetrics();highlightParameterSketches();renderValidation();persist()")
f.write_text(s,encoding='utf-8')
for name in ['compose.yaml','package.json','package_network.py','README.md','DEPLOY.md']:
 f=Path(name);f.write_text(f.read_text(encoding='utf-8-sig').replace('7.1.0','7.2.0'),encoding='utf-8')
f=Path('NETWORK.md');s=f.read_text(encoding='utf-8');s+='''\n\n## 7.2.0 — размеры на схемах трубы, траншеи и колодца\n\nРазрез колодца подписывает общую высоту и высоты горловины, верхней плиты, рабочей части и днища в метрах. Нажатие на общую высоту и любую часть переводит к соответствующему полю.\n\nТруба показана продольной схемой с фактической длиной по оси, диаметром, отметками наружного низа обоих концов и уклоном. Схема траншеи показывает выбранное сечение: ширины по дну и поверху, глубину и углы от горизонтали. Для нескольких зон показано сечение выбранной зоны; его расстояние от начала подписано. Размеры обновляются после ввода, активный параметр выделяется.\n\nНажатие на глубину открывает отметку трубы; глубина остаётся расчётной величиной из отметок поверхности, наружного низа трубы, футляра и подушки. В режиме углов верхняя ширина рассчитывается; нажатие на неё открывает способ задания откосов. В режиме верхней ширины углы рассчитываются, их нажатие открывает способ задания откосов. Схемы иллюстративны, размеры берутся из существующей геометрии. Формулы, формат модели и API не меняются: web 7.2.0 + API 2.2.0.\n''';f.write_text(s,encoding='utf-8')
