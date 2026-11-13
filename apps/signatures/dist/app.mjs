import {decodeCms,extractExpected,matchPeople,parseName,checkDigest,correctExpected,includeHandwriting,restoreHandwriting} from './core.mjs';
import {pageLines,inkEvidence} from './layout.mjs';
import {digestHex} from './vendor/hash.mjs';
const $=id=>document.getElementById(id);
const state={files:[],expected:[],signers:[],rows:[],filter:'all',pdf:null,pdfBytes:null,pages:[],errors:[],mode:'actual',name:'',busy:false,run:0};
const labels={found:'Найдена',missing:'Не найдена',review:'Уточнить'};
function el(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;}
function showError(message){$('upload-error').textContent=message;$('upload-error').hidden=!message;}
function fileList(){
  $('file-list').replaceChildren();
  state.files.forEach((file,i)=>{const li=el('li');li.append(el('strong',/\.pdf$/i.test(file.name)?'PDF':'SIG'));const name=el('span',file.name,'file-name');name.append(el('small',`${(file.size/1024).toFixed(0)} КБ`));li.append(name);const remove=el('button','×');remove.type='button';remove.disabled=state.busy;remove.setAttribute('aria-label',`Убрать ${file.name}`);remove.onclick=()=>{state.files.splice(i,1);fileList();};li.append(remove);$('file-list').append(li);});
  $('analyze').disabled=state.busy||!state.files.some(f=>/\.pdf$/i.test(f.name));
  $('analyze').replaceChildren(document.createTextNode(state.files.some(f=>/\.(sig|sgn|p7s)$/i.test(f.name))?'Сверить подписи':'Собрать список'),el('span','↗'));
}
function acceptFiles(files){
  if(state.busy)return;
  const errors=[];
  for(const file of files){const pdf=/\.pdf$/i.test(file.name);if(!/\.(pdf|sig|sgn|p7s)$/i.test(file.name)){errors.push(`Не поддержан: ${file.name}`);continue;}if(file.size>(pdf?100:10)*1024*1024){errors.push(`Слишком большой файл: ${file.name}`);continue;}if(state.files.some(f=>f.name===file.name&&f.size===file.size))continue;if(pdf)state.files=state.files.filter(f=>!/\.pdf$/i.test(f.name));state.files.push(file);}
  showError(errors.join('\n'));fileList();
}
$('files').onchange=e=>{acceptFiles(e.target.files);e.target.value='';};
for(const name of ['dragover','dragenter'])$('dropzone').addEventListener(name,e=>{e.preventDefault();$('dropzone').classList.add('dragging');});
$('dropzone').ondragleave=()=>$('dropzone').classList.remove('dragging');
$('dropzone').ondrop=e=>{e.preventDefault();$('dropzone').classList.remove('dragging');acceptFiles(e.dataTransfer.files);};
$('scope').onchange=()=>{const first=$('scope').value==='first';for(const id of ['page-count','page-label','page-start','page-start-label'])$(id).hidden=!first;};
let pdfjs;
async function loadPdfjs(){if(!pdfjs){pdfjs=await import('./vendor/pdf.mjs');pdfjs.GlobalWorkerOptions.workerSrc=new URL('./vendor/pdf.worker.mjs',import.meta.url).href;}return pdfjs;}
async function inspectHandwriting(page,lines){
 const stamps=lines.filter(l=>l.drawing&&l.signatureScreenRect);if(!stamps.length)return;
 const scale=3,view=page.getViewport({scale:1}),left=Math.floor(Math.min(...stamps.map(l=>l.signatureScreenRect[0]))),top=Math.floor(Math.min(...stamps.map(l=>l.signatureScreenRect[1]))),right=Math.ceil(Math.max(...stamps.map(l=>l.signatureScreenRect[2]))),bottom=Math.ceil(Math.max(...stamps.map(l=>l.signatureScreenRect[3])));
 const canvas=document.createElement('canvas');canvas.width=Math.ceil((right-left)*scale);canvas.height=Math.ceil((bottom-top)*scale);const ctx=canvas.getContext('2d',{willReadFrequently:true});
 try{const task=page.render({canvasContext:ctx,viewport:view,transform:[scale,0,0,scale,-left*scale,-top*scale]}),timer=setTimeout(()=>task.cancel(),5000);try{await task.promise;}finally{clearTimeout(timer);}
 for(const line of stamps){const r=line.signatureScreenRect,x=Math.max(0,Math.round((r[0]-left+2)*scale)),y=Math.max(0,Math.round((r[1]-top+1)*scale)),w=Math.min(canvas.width-x,Math.round((r[2]-r[0]-4)*scale)),h=Math.min(canvas.height-y,Math.round((r[3]-r[1]-2)*scale));line.handwriting=inkEvidence(ctx.getImageData(x,y,w,h).data,w,h);}
 }catch(e){console.warn('Signature cell analysis:',e.name,e.message);for(const line of stamps)line.handwriting={status:'unchecked',reason:e.name==='RenderingCancelledException'?'Превышено время проверки изображения. Проверьте графу вручную.':'Не удалось проверить изображение графы. Откройте источник вручную.'};}
 finally{canvas.width=canvas.height=1;}
}
$('analyze').onclick=async()=>{
  const pdfFile=state.files.find(f=>/\.pdf$/i.test(f.name));if(!pdfFile||state.busy)return;
  const pageCount=Number($('page-count').value),pageStart=Number($('page-start').value);
  if($('scope').value==='first'&&(!Number.isInteger(pageCount)||pageCount<1||pageCount>200||!Number.isInteger(pageStart)||pageStart<1)){showError('Укажите начальную страницу и число страниц от 1 до 200.');return;}
  state.busy=true;fileList();$('files').disabled=true;$('scope').disabled=true;$('page-count').disabled=true;$('page-start').disabled=true;$('handwriting-check').disabled=true;$('apply').disabled=true;showError('');
  const run=++state.run;
  try{
    $('progress').textContent='Открываем PDF…';
    const lib=await loadPdfjs();
    const bytes=new Uint8Array(await pdfFile.arrayBuffer());
    const fingerprint=await digestHex('SHA-256',bytes);
    const doc=await lib.getDocument({data:bytes.slice(),isEvalSupported:false,verbosity:0}).promise;
    const first=$('scope').value==='all'?1:pageStart,count=$('scope').value==='all'?doc.numPages:Math.min(pageCount,doc.numPages-first+1);
    if(first>doc.numPages){await doc.destroy();throw Error(`В PDF только ${doc.numPages} страниц.`);}
    if(count>1000){await doc.destroy();throw Error('В документе больше 1000 страниц. Выберите режим «Первые страницы» (до 200).');}
    const lines=[],pages=[];
    for(let offset=0;offset<count;offset++){const i=first+offset;$('progress').textContent=`Фамилии и подписи: страница ${i} (${offset+1} из ${count})…`;const p=await doc.getPage(i);const text=await p.getTextContent();const pageRows=pageLines(text.items,p.getViewport({scale:1}),i);if($('handwriting-check').checked)await inspectHandwriting(p,pageRows);lines.push(...pageRows);pages.push(i);p.cleanup();}
    const errors=[],signers=[];
    const sigs=state.files.filter(f=>!/\.pdf$/i.test(f.name));
    for(const file of sigs){$('progress').textContent=`Читаем ${file.name}…`;try{const cms=decodeCms(new Uint8Array(await file.arrayBuffer()),file.name);if(!cms.detached){errors.push(`${file.name}: присоединённая подпись не сопоставляется с отдельным PDF.`);continue;}for(const s of cms.signers){s.binding=await checkDigest(s,bytes);if(!s.identified)errors.push(`${file.name}: для записи №${s.index} отсутствует сертификат подписанта.`);if(s.binding.status==='mismatch')errors.push(`${file.name}: хеш подписи не соответствует PDF.`);signers.push(s);}}catch(e){errors.push(`${file.name}: ${e.message}`);}}
    const response=await fetch('./vendor/names.json');if(!response.ok)throw Error('Не удалось загрузить словарь фамилий. Повторите проверку.');
    const expected=extractExpected(lines,await response.json());
    if(state.fingerprint===fingerprint)restoreHandwriting(expected,state.expected);
    if(!expected.length)errors.push('Фамилии автоматически не найдены. Проверьте страницы PDF и внесите список вручную. Для сканов требуется предварительное OCR.');
    closePreview();const previous=state.pdf;state.pdf=doc;state.pdfBytes=bytes;state.fingerprint=fingerprint;state.pages=pages;state.expected=expected;state.signers=signers;state.errors=errors;state.name=pdfFile.name;state.mode='actual';
    if(previous)await previous.destroy();
    $('preview-pages').replaceChildren();
    $('progress').textContent='';
    syncEditor();recalculate();
  }catch(e){if(run===state.run)showError(e.name==='PasswordException'?'PDF защищён паролем. Выберите доступную для чтения копию.':`Не удалось выполнить проверку: ${e.message}`);}
  finally{state.busy=false;$('files').disabled=false;$('scope').disabled=false;$('page-count').disabled=false;$('page-start').disabled=false;$('handwriting-check').disabled=false;$('apply').disabled=false;fileList();}
};
let editorOrigins=[];
function syncEditor(){editorOrigins=state.expected.slice();$('expected').value=state.expected.map(p=>p.display+(p.role?` | ${p.role}`:'')).join('\n');}
function recalculate(){
  const usable=state.signers.filter(s=>s.identified&&s.binding?.status!=='mismatch');
  state.rows=matchPeople(state.expected,usable).map(r=>r.status==='missing'&&state.errors.length?{...r,status:'review',reason:'Не все подписи прочитаны: отсутствие подписи нельзя установить'}:r);
  state.rows=state.rows.map(includeHandwriting);
  render();
}
function render(){
  $('count-all').textContent=state.rows.length;
  $('report-filename').textContent=state.name;$('report-filename').hidden=!state.name;
  $('list-notice').textContent=state.errors.join(' ');$('list-notice').hidden=!state.errors.length;
  const counts={all:state.rows.length,missing:state.rows.filter(r=>r.status==='missing').length,review:state.rows.filter(r=>r.status==='review').length};
  for(const button of document.querySelectorAll('[data-filter]')){const key=button.dataset.filter,label={all:'Все',missing:'Без подписи',review:'Проверить'}[key];button.textContent=label+(state.pdf?` ${counts[key]}`:'');}
  const tbody=$('people');tbody.replaceChildren();
  const rows=state.rows.filter(p=>state.filter==='all'||p.status===state.filter);$('table-empty').hidden=!!rows.length;
  $('table-empty').textContent=!state.pdf?'Список появится после обработки PDF.':!state.rows.length?'Фамилии не найдены. Добавьте их через «Изменить список».':'В этой категории записей нет.';
  const pagesLabel=pages=>pages.slice(0,4).join(', ')+(pages.length>4?` и ещё ${pages.length-4}`:'');
  for(const row of rows){
    const index=state.rows.indexOf(row),tr=el('tr'),name=el('td');
    name.append(el('strong',row.display));if(row.role)name.append(el('small',row.role));
    const sources=el('div',undefined,'source-links');
    if(row.pages?.length){
      let extra;
      for(const [i,page] of row.pages.entries()){
        const link=el('button',`стр. ${page}`,'source-link');link.type='button';const places=row.occurrences.filter(o=>o.page===page);link.title=`${row.display}. ${places.some(o=>o.type==='drawing')?'Чертёж: рукописная подпись':'Текстовая часть: SIG'}`;link.onclick=()=>openPreview(page,index);
        if(i<3)sources.append(link);else{if(!extra){const details=el('details',undefined,'more-sources');details.append(el('summary',`Ещё ${row.pages.length-3}`));extra=el('div',undefined,'source-links');details.append(extra);sources.append(details);}extra.append(link);}
      }
    }else sources.append(el('span','Добавлено вручную'));
    name.append(sources);
    const edit=el('button','Исправить','source-link edit-person');edit.type='button';edit.setAttribute('aria-label',`Исправить ${row.display}`);edit.onclick=()=>openPreview(row.pages?.[0]||1,index);name.append(edit);
    const match=el('td');let any=false;
    if(row.sigAppliedPages.length){match.append(el('span',`ЭП · стр. ${pagesLabel(row.sigAppliedPages)}`));any=true;}
    else if(row.matches?.length&&row.sigExcludedFromDrawings){match.append(el('small','SIG не применяется к чертежам'));any=true;}
    for(const [kind,label] of [['present','Рукописная'],['candidates','Проверить росчерк']]){const pages=[...new Set(row.handwriting[kind].map(s=>s.page))];if(pages.length){match.append(el('small',`${label} · стр. ${pagesLabel(pages)}`));any=true;}}
    if(!any)match.append(el('span','—'));
    const details=el('details',undefined,'row-details');details.append(el('summary','Подробнее'),el('p',row.reason));for(const n of new Set((row.matches||[]).map(s=>s.name)))details.append(el('p',`SIG: ${n}`));match.append(details);
    const status=el('td');status.append(el('span',row.evidenceType==='partial'?'Частично':row.evidenceType==='candidate'?'Росчерк?':row.evidenceType==='handwritten'?'Рукописная':row.evidenceType==='combined'?'ЭП + рукописная':row.evidenceType==='electronic'?'ЭП':labels[row.status],`badge ${row.status}`));tr.append(name,match,status);tbody.append(tr);
  }
  $('table-footer').hidden=!state.pdf;
  $('page-source').textContent=state.pdf?`Обработано: ${state.pages.length} стр.`:'';
  $('preview-button').hidden=!state.pdf;$('export').disabled=!state.rows.length;$('edit-list').disabled=!state.pdf;
}
document.querySelectorAll('[data-filter]').forEach(button=>button.onclick=()=>{state.filter=button.dataset.filter;document.querySelectorAll('[data-filter]').forEach(b=>b.classList.toggle('selected',b===button));render();});
$('apply').onclick=()=>{
  const rows=$('expected').value.split('\n').map(s=>s.trim()).filter(Boolean),expected=[];
  const names=new Set(rows.map(row=>row.split('|')[0].trim()));
  for(const [i,row] of rows.entries()){const [name,...role]=row.split('|');const p=parseName(name.trim());if(!p){$('editor-error').textContent=`Не удалось разобрать: ${name}. Пример: Иванов И. И. или Иванов Иван Иванович.`;return;}const old=state.expected.find(s=>s.display===p.display)||(rows.length===editorOrigins.length&&!names.has(editorOrigins[i]?.display)?editorOrigins[i]:null);if(!expected.some(s=>s.display===p.display))expected.push(old?correctExpected(old,p.display,role.join('|').trim()):{...p,role:role.join('|').trim(),pages:[],sources:[]});}
  state.expected=expected;syncEditor();$('editor-error').textContent='';recalculate();$('list-editor').close();
};
function csvCell(value){return '"'+String(value??'').replaceAll('"','""')+'"';}
$('export').onclick=()=>{
  const rows=[['Документ','Фамилия / ФИО из PDF','Должность','Страницы','Результат','Подписант из SIG','Источник ЭП','Текстовые страницы где засчитан SIG','Рукописные на чертежах','Чертежи без рукописной','Чертежи требующие проверки','Примечание'],...state.rows.map(p=>[state.name,p.display,p.role,(p.pages||[]).join(', '),p.evidenceType==='partial'?'Частично':labels[p.status],p.matches?.map(s=>s.name).join('; '),p.matches?.map(s=>s.file).join('; '),p.sigAppliedPages.join(', '),[...new Set(p.handwriting.present.map(s=>s.page))].join(', '),[...new Set(p.occurrences.filter(o=>o.type==='drawing'&&o.status==='missing').map(s=>s.page))].join(', '),[...new Set(p.occurrences.filter(o=>o.type==='drawing'&&o.status==='review').map(s=>s.page))].join(', '),`${p.reason}. Подлинность ЭП не проверена.`])];
  const blob=new Blob(['\ufeff'+rows.map(r=>r.map(csvCell).join(';')).join('\r\n')],{type:'text/csv;charset=utf-8'}),url=URL.createObjectURL(blob),a=el('a');a.href=url;a.download='КДФП_сверка_подписантов.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);
};
let previewIndex=null,previewPage=1,previewGeneration=0,previewRender=null,previewFullPage=false;
function closePreview(){previewGeneration++;previewRender?.cancel();previewRender=null;$('preview').close();}
async function openPreview(number=1,index=previewIndex){
  const generation=++previewGeneration;previewRender?.cancel();previewRender=null;
  if(index!==previewIndex)previewFullPage=false;previewIndex=index;const person=index===null?null:state.expected[index];
  previewPage=Math.max(1,Math.min(Number(number)||1,state.pdf?.numPages||Math.max(...(person?.pages||[1]))));
  $('source-editor').hidden=!person;$('source-error').textContent='';
  if(person){$('source-name').value=person.display;$('source-role').value=person.role||'';const evidence=(person.sources||[]).filter(s=>s.page===previewPage);$('source-text').textContent=evidence.map(s=>s.text+(s.rawText?`\nТекстовый слой CAD: ${s.rawText}`:'')).join('\n')||'Исходная строка для этой страницы не сохранена.';}
  $('source-handwriting').replaceChildren();
  const currentSources=(person?.sources||[]).filter(s=>s.page===previewPage),onDrawing=currentSources.some(s=>s.drawing);
  $('source-help').textContent=onDrawing?'Чертёж · нужна рукописная подпись.':'Текстовая часть · подпись по SIG.';
  if(person&&!onDrawing)$('source-handwriting').append(el('p',state.rows[previewIndex]?.sigAppliedPages.includes(previewPage)?'ЭП из SIG засчитана для этой текстовой страницы.':'ЭП из SIG для этой страницы не засчитана.','signing-rule'));
  for(const source of currentSources){if(!source.drawing)continue;const item=el('div',undefined,'handwriting-item');item.append(el('strong',source.text));const label=el('label','Рукописная подпись'),select=el('select');for(const [value,text] of [['detected','Росчерк обнаружен автоматически'],['unchecked','Не проверено'],['candidate','Есть штрихи — проверить'],['empty','Росчерк автоматически не найден'],['present','Есть рукописная подпись'],['absent','Рукописной подписи нет']]){const option=el('option',text);option.value=value;select.append(option);}select.value=source.handwriting?.status||'unchecked';label.append(select);item.append(label);select.disabled=state.busy;select.onchange=()=>{source.handwriting={...source.handwriting,status:select.value,manual:true};recalculate();};if(source.handwriting?.reason)select.title=source.handwriting.reason;$('source-handwriting').append(item);}
  $('preview-page').value=previewPage;$('preview-page').max=state.pdf?.numPages||previewPage;
  $('preview-page').disabled=!state.pdf;$('page-prev').disabled=!state.pdf||previewPage<=1;$('page-next').disabled=!state.pdf||previewPage>=state.pdf.numPages;
  $('preview-total').textContent=state.pdf?`из ${state.pdf.numPages}`:'';
  const drawingSources=(person?.sources||[]).filter(s=>s.page===previewPage&&s.drawing&&s.signatureRect);$('preview-zoom').hidden=!drawingSources.length;$('preview-zoom').textContent=previewFullPage?'Штамп крупно':'Весь лист';
  $('preview-title').textContent=person?`${person.display} — страница ${previewPage}`:`${state.name} — страница ${previewPage}`;
  $('preview-pages').replaceChildren(el('p',state.pdf?'Открываем страницу…':'Загрузите PDF и соберите список, чтобы увидеть оригинал документа.'));
  if(!$('preview').open)$('preview').showModal();
  if(!state.pdf)return;
  try{
    const page=await state.pdf.getPage(previewPage);if(generation!==previewGeneration)return;
    const base=page.getViewport({scale:1}),focus=drawingSources.length&&!previewFullPage;
    const rects=focus?drawingSources.flatMap(s=>[s.rect,s.signatureRect]).map(r=>base.convertToViewportRectangle(r)):[];
    const clip=focus?[Math.max(0,Math.min(...rects.flatMap(r=>[r[0],r[2]]))-8),Math.max(0,Math.min(...rects.flatMap(r=>[r[1],r[3]]))-35),Math.min(base.width,Math.max(...rects.flatMap(r=>[r[0],r[2]]))+38),Math.min(base.height,Math.max(...rects.flatMap(r=>[r[1],r[3]]))+30)]:[0,0,base.width,base.height];
    const scale=focus?3:Math.min(1.5,1800/Math.max(base.width,base.height)),view=page.getViewport({scale}),originX=clip[0]*scale,originY=clip[1]*scale,canvas=el('canvas'),wrap=el('div',undefined,'pdf-page');canvas.width=Math.ceil((clip[2]-clip[0])*scale);canvas.height=Math.ceil((clip[3]-clip[1])*scale);wrap.style.aspectRatio=`${canvas.width} / ${canvas.height}`;wrap.append(canvas);
    $('preview-pages').replaceChildren(wrap);
    previewRender=page.render({canvasContext:canvas.getContext('2d'),viewport:view,transform:[1,0,0,1,-originX,-originY]});await previewRender.promise;
    if(generation!==previewGeneration)return;previewRender=null;
    for(const source of person?.sources||[]){if(source.page!==previewPage)continue;for(const [field,cls] of [['rect','source-highlight'],['signatureRect','signature-highlight']]){if(!source[field])continue;const r=view.convertToViewportRectangle(source[field]),mark=el('div',undefined,cls);mark.style.left=`${(Math.min(r[0],r[2])-originX)/canvas.width*100}%`;mark.style.top=`${(Math.min(r[1],r[3])-originY)/canvas.height*100}%`;mark.style.width=`${Math.abs(r[2]-r[0])/canvas.width*100}%`;mark.style.height=`${Math.abs(r[3]-r[1])/canvas.height*100}%`;wrap.append(mark);}}
  }catch(e){if(generation===previewGeneration&&e.name!=='RenderingCancelledException')$('preview-pages').replaceChildren(el('p',`Не удалось отобразить страницу: ${e.message}`));}
}
$('preview-button').onclick=()=>openPreview(state.pages[0]||1,null);
$('page-prev').onclick=()=>openPreview(previewPage-1);
$('page-next').onclick=()=>openPreview(previewPage+1);
$('preview-page').onchange=()=>openPreview(Number($('preview-page').value));
$('preview-zoom').onclick=()=>{previewFullPage=!previewFullPage;openPreview(previewPage);};
$('close-preview').onclick=closePreview;
$('preview').addEventListener('cancel',()=>{previewGeneration++;previewRender?.cancel();previewRender=null;});
$('source-save').onclick=()=>{
  if(state.busy||previewIndex===null)return;
  try{state.expected[previewIndex]=correctExpected(state.expected[previewIndex],$('source-name').value,$('source-role').value);syncEditor();recalculate();closePreview();}catch(e){$('source-error').textContent=e.message;}
};
$('source-remove').onclick=()=>{if(state.busy||previewIndex===null)return;state.expected.splice(previewIndex,1);syncEditor();recalculate();closePreview();};
$('edit-list').onclick=()=>{syncEditor();$('editor-error').textContent='';$('list-editor').showModal();};
$('close-list-editor').onclick=()=>$('list-editor').close();
syncEditor();recalculate();fileList();
