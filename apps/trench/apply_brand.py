from pathlib import Path
p=Path('dist/index.html');s=p.read_text(encoding='utf8')
s=s.replace('<button id="photo-example" type="button" class="button example-button">Загрузить пример с фото</button>\n','')
s=s.replace('До 0,001 м² (как на фото)','До 0,001 м²')
s=s.replace('<link rel="stylesheet" href="calculator.css">','<link rel="stylesheet" href="calculator.css"><link rel="stylesheet" href="kdfp.css">')
s=s.replace('<a class="brand" href="./"><span class="brand-icon">▱</span> грунт<span class="brand-dot">.</span></a>','<a class="brand" href="https://www.kdfp.ru/" target="_blank" rel="noopener" aria-label="КДФП Инжиниринг — сайт компании"><img src="assets/kdfp-logo.png" alt="КДФП Инжиниринг" width="168" height="39"></a>')
s=s.replace('ЗЕМЛЯНЫЕ РАБОТЫ / 01','ИНЖЕНЕРНЫЕ РАСЧЁТЫ / 01').replace('<h1>Траншея. Труба. Объём.</h1>','<h1>Расчёт земляных работ</h1>').replace('Задайте геометрию — получите баланс грунта.','Выемка и обратная засыпка траншеи')
s=s.replace('Грунт — выемка и засыпка','КДФП — расчёт земляных работ')
s=s.replace('грунт. <span class="muted">/ Расчёт земляных работ</span>','КДФП ИНЖИНИРИНГ <span class="muted">/ Расчёт земляных работ</span>')
p.write_text(s,encoding='utf8')
p=Path('dist/app.js');s=p.read_text(encoding='utf8')
start=s.index('try{const saved=');end=s.index('function read()',start)
s=s[:start]+'''try{
 const current=localStorage.getItem('trench-v3');
 let saved=JSON.parse(current||localStorage.getItem('trench-v2')||localStorage.getItem('trench-v1'));
 if(saved&&typeof saved==='object'){
  if(!current){
   const wasExample=saved.length===6.79&&saved.bottom===1.16&&saved.depth===2.45&&saved.depthEnd===2.66&&saved.objectType==='none';
   if(wasExample)saved={...defaults};
   else saved.objectType='pipe';
  }
  for(const k of Object.keys(defaults)){
   if(stringFields.includes(k)){if(typeof saved[k]==='string'&&Array.from($(k).options).some(o=>o.value===saved[k]))$(k).value=saved[k]}
   else if(typeof saved[k]==='number'&&Number.isFinite(saved[k]))$(k).value=saved[k];
  }
 }
}catch{}
'''+s[end:]
s=s.replace("localStorage.setItem('trench-v2'", "localStorage.setItem('trench-v3'")
start=s.index("$('photo-example').onclick=");end=s.index("$('reset').onclick=",start);s=s[:start]+s[end:]
palette={'#77917b':'#9aa5ad','#9aa896':'#9fa9b0','#687f6c':'#6f7b84','#c8d1c3':'#cbd0d4','#a8b69e':'#a1aab1','#d6dfd0':'#dce0e3','#c9b574':'#c7b797','#e2eadb88':'#e0e5e888','#b5c3ac':'#aab4bc','#c9d5ba90':'#bdc8d090','#b7c9a675':'#b4c0ca75','#d5dfc680':'#d3dbe080','#e7eddf90':'#e5eaee90','#e0d2a5':'#e8d9bc','#bdaa79':'#c6b18a','#e8d9ac':'#e9d9bc','#ca9464':'#fd7a3d','#a9754e':'#cf5318','#ce9363':'#fd6017','#8f603d':'#cb4d12','#5c6c5b':'#515b62','#9e6e47':'#b94b18','#3e5145':'#30383e','#d3a373':'#f5a274','#9d7952':'#cf6c38','#b88d60':'#e9844f','#d9b792':'#ffb58f','#678366':'#8999a5','#a7b897':'#9ba8b1','#78916e':'#8999a5','#b1845c':'#e77b43','#a06d43':'#ca581e'}
for a,b in palette.items():s=s.replace(a,b)
s=s.replace('const shade=Math.round(151+40*Math.sin(2*Math.PI*i/64))','const shade=Math.round(110+24*Math.sin(2*Math.PI*i/64))').replace('rgb(${shade+47},${shade},${shade-45})','rgb(${Math.min(255,shade+125)},${shade},${Math.max(20,shade-70)})')
p.write_text(s,encoding='utf8')
p=Path('README.md');s=p.read_text(encoding='utf8')
s=s.replace('Кнопка «Загрузить пример с фото» включает округление F₁/F₂ до 0,001 м² и воспроизводит 42,297 м³. При расчёте без промежуточного округления — 42,299 м³.','Округление F₁/F₂ до 0,001 м² можно включить отдельно.')
s=s.replace('# Калькулятор выемки и обратной засыпки','# КДФП — калькулятор выемки и обратной засыпки')
s += '\nОформление по референсу https://www.kdfp.ru/: логотип КДФП, цвета #fd6017 / #3e4449 / #f3f3f3, локальный шрифт Montserrat (лицензия OFL в assets). Все ресурсы включены в образ. Труба выбрана по умолчанию.\n'
p.write_text(s,encoding='utf8')
