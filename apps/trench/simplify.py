from pathlib import Path
p=Path('dist/index.html');s=p.read_text(encoding='utf8')
start=s.index('<nav class="app-tabs"');end=s.index('<div id="geometry-section"',start);s=s[:start]+s[end:]
start=s.index('<section id="project-section"');end=s.index('<footer>',start);s=s[:start]+s[end:]
s=s.replace('<script type="module" src="project.js"></script>','').replace('<link rel="stylesheet" href="project.css">','<link rel="stylesheet" href="calculator.css">')
s=s.replace('Расчёт траншей с перепадом высот и ведомость грунтов: трубы, котлованы, сооружения и ЩПС.','Расчёт выемки и обратной засыпки траншеи с интерактивной схемой.').replace('Грунт — расчёт и ведомость','Грунт — выемка и засыпка')
start=s.index('<label>Название участка');end=s.index('<button id="photo-example"',start);s=s[:start]+s[end:]
start=s.index('<button id="add-geometry"');end=s.index('</form>',start);s=s[:start]+s[end:]
s=s.replace('Грунт за вычетом трубы и подсыпки','Грунт за вычетом конструкции и материалов')
s=s.replace('Ведомость отдельно учитывает котлованы, сооружения и слои ЩПС. ','')
s=s.replace('<p><b>Засыпка:</b> Vз = V − Vтр − Vп.</p>','<p><b>Засыпка грунтом:</b> Vз = V − Vк − Vп − Vдоп, где Vк — наружный объём труб или конструкции, Vдоп — другие слои ЩПС / песка, заданные отдельно. Это принцип вычитания вытесненных объёмов из Excel.</p>')
s=s.replace('<span>03</span> Основание','<span>03</span> Подсыпка и другие материалы')
target='<small>Отдельный материал по всей ширине траншеи. Введите 0, если подсыпки нет.</small></label></fieldset>'
s=s.replace(target,target.replace('</fieldset>','<label>Другие слои ЩПС / песка<div class="input-wrap"><input id="extraFill" type="number" step="0.1" min="0" value="0"><span>м³</span></div><small>Суммарный объём сверх подсыпки. Введите 0, если нет.</small></label></fieldset>'))
start=s.index('<div id="end-values"');end=s.index('<div id="errors"',start);endpoint=s[start:end];s=s[:start]+s[end:]
s=s.replace('<div class="panel balance">','<details class="panel method breakdown"><summary>Расшифровка объёмов <span>+</span></summary>'+endpoint+'<div class="balance">')
s=s.replace('</div></div>\n<details class="panel method">','</div></div></details>\n<details class="panel method">')
s=s.replace('<i class="bed"></i>Подсыпка</span><strong id="bed-result">','<i class="bed"></i>Подсыпка и другие материалы</span><strong id="bed-result">')
s=s.replace('конструкция + привозная подсыпка','конструкция + привозные материалы')
p.write_text(s,encoding='utf8')
p=Path('dist/app.js');s=p.read_text(encoding='utf8')
s=s.replace("'bed-result':'bed'","'bed-result':'fill'").replace("['backfill','occupied','bed']","['backfill','occupied','fill']")
s=s.replace(" $('add-geometry').disabled=!valid;\n",'')
s=s.replace(";$('geometry-name').value='Д11.1/К2 — Д11.2/К2 (пример с фото)'",'')
start=s.index("$('add-geometry').onclick=");end=s.index("$('reset').onclick=",start);s=s[:start]+s[end:]
s=s.replace(";$('geometry-name').value='Новый участок';$('geometry-save-message').textContent=''",'')
s=s.replace("if(e.target.id==='depthMode'&&$('depthMode').value==='variable')$('depthEnd').value=$('depth').value;update()", "if(e.target.id==='depthMode'){if($('depthMode').value==='variable')$('depthEnd').value=$('depth').value;else if(view==='end'){setView('2d');return}}update()")
p.write_text(s,encoding='utf8')
