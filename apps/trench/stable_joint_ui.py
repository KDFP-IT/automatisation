from pathlib import Path
p=Path('dist/network-app.js');s=p.read_text(encoding='utf-8');a=s.index("${(result.joints||[]).length?`<div class=\"joint-summary\"");b=s.index(";\n const issuesOpen=",a);s=s[:a]+"`;"+s[b+1:]
# Add a compact fixed-row control rather than changing canvas height as intersections appear/disappear.
s=s.replace(" const issuesOpen=", " const joinButton=$('joint-info');joinButton.hidden=!(result.joints||[]).length;joinButton.textContent='Стыки: '+(result.joints||[]).length;joinButton.title='Общая выемка '+fmt(jointVolume,3)+' м³ учтена один раз в ведомости.'+(shared?' Для выбранного участка общая часть показана отдельно.':'');const issuesOpen=",1)
s=s.replace("function initializeConstructor(){", "function initializeConstructor(){const jointButton=document.createElement('button');jointButton.id='joint-info';jointButton.className='joint-info';jointButton.hidden=true;$('data-status').before(jointButton);jointButton.onclick=()=>{flushEdit();state.page='report';render()};")
s=s.replace('Объёмы траншей получены численно. При сложном пересечении контуров нужна проверка совместной выемки.','Объёмы получены численно. Общая часть траншей учтена один раз в строках стыков ведомости.')
p.write_text(s,encoding='utf-8')
p=Path('dist/validation.css');p.write_text(p.read_text(encoding='utf-8')+'\n.joint-info{border:1px solid #bddcca;background:#edf7f2;color:#35654d;border-radius:5px;padding:5px 9px;font-size:12px;white-space:nowrap;cursor:pointer}.joint-info[hidden]{display:none}\n',encoding='utf-8')
for f in ['package.json','compose.yaml','package_network.py']:
 p=Path(f);p.write_text(p.read_text(encoding='utf-8').replace('5.5.0','6.0.0'),encoding='utf-8')
