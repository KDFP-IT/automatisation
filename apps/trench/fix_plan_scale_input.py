from pathlib import Path
p=Path('dist/network-app.js');s=p.read_text(encoding='utf-8').replace("$('zoom').onchange=e=>", "$('zoom').oninput=e=>{const value=Number(e.target.value);if(Number.isFinite(value)&&value>0)setPlanZoom(value/100)};$('zoom').onchange=e=>");p.write_text(s,encoding='utf-8')
