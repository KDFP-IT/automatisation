<script setup>
import { ref } from 'vue'
import { useBookmarks } from './composables/useBookmarks'
const { file,busy,error,result,step,progress,start,end,scale,allowIncomplete,selectFile,removeFile,submit }=useBookmarks()
const picker=ref()
function picked(e){selectFile(e.target.files[0]);e.target.value=''}
function dropped(e){if(e.dataTransfer.files.length===1)selectFile(e.dataTransfer.files[0]);else error.value='Загрузите один PDF за раз.'}
</script>
<template><div class="bookmarks-native"><UAlert v-if="error" color="error" :description="error" /><main id="workspace">

  <div class="content">
    <section class="intro"><div><h1>Закладки <span>чертежей</span></h1><p>От штампа к удобной навигации.<br>Загрузите PDF — соберём листы в «Графической части».</p></div><div class="document-art" aria-hidden="true"><div class="art-sheet back"></div><div class="art-sheet front"><div class="art-top"><span>КДФП / КР</span><span>↗</span></div><div class="drawing-grid"><div class="drawing-plan"><i></i><i></i><i></i><i></i></div><span class="dimension horizontal">6 000</span><span class="dimension vertical">4 200</span></div><div class="art-stamp"><span>30/09-ИЛО.КР</span><strong>79</strong></div></div><div class="art-badge">✓ Закладки готовы</div></div></section>
    <section class="how-section" id="how-it-works"><div class="eyebrow">ПРОСТОЙ ПРОЦЕСС</div><h2>Из штампа — в закладки</h2><div class="how-grid"><article><span>01 /</span><h3>Читаем чертежи</h3><p>Находим номер листа, шифр, название объекта и вид работ в штампе.</p></article><article><span>02 /</span><h3>Наводим порядок</h3><p>Сохраняем разделы документа. Заменяем автоматические ветки листов понятными названиями.</p></article><article><span>03 /</span><h3>Готовим отдельную копию</h3><p>Собираем листы в «Графической части» и проверяем сохранение страниц и переходов.</p></article></div></section>
<ol class="steps" aria-label="Этапы обработки"><li id="step1" :class="{current:step===1}"><span>01</span> Загрузите PDF</li><li id="step2" :class="{current:step===2}"><span>02</span> Дождитесь обработки</li><li id="step3" :class="{current:step===3}"><span>03</span> Скачайте результат</li></ol>
    <div class="workspace-grid">
      <section class="work-card" aria-labelledby="upload-heading">
        <div class="card-heading"><div><span class="eyebrow">ВАШ ДОКУМЕНТ</span><h2 id="upload-heading">Добавьте файл проекта</h2></div></div>
        <form id="upload-form" @submit.prevent="submit">
          <div v-if="!file" class="dropzone" id="dropzone" @dragover.prevent @drop.prevent="dropped"><div class="upload-icon" aria-hidden="true">↑</div><h3>Перетащите PDF сюда</h3><p>или выберите файл на компьютере</p><UButton color="neutral" variant="outline" class="choose-button" id="choose-file" type="button" :disabled="busy" @click="picker.click()">Выбрать PDF <span>＋</span></UButton><span class="file-limit">Один файл · до 200 МБ · до 2 500 страниц</span><input ref="picker" type="file" accept=".pdf,application/pdf" :disabled="busy" hidden @change="picked"></div>
          <div id="selected-file" class="selected-file" v-if="file"><div class="pdf-icon">PDF</div><div class="file-info"><strong>{{ file.name }}</strong><small id="file-size"></small></div><UButton color="neutral" variant="outline" id="remove-file" class="icon-button" type="button" :disabled="busy" aria-label="Убрать выбранный файл" @click="removeFile">×</UButton></div>
          <details class="settings" id="settings"><summary>Параметры обработки <span>Необязательно</span></summary><div class="settings-content"><p>По умолчанию обрабатываются все страницы со стандартным штампом.</p><div class="field-grid"><label>Первая страница<UInput v-model="start" type="number" :min="1" :disabled="busy" required /></label><label>Последняя страница<UInput v-model="end" type="number" :min="1" :disabled="busy" placeholder="До конца" /></label><label>Масштаб штампа<USelect v-model="scale" :disabled="busy" :items="[{label:'Обычный, 1:1',value:'1'},{label:'Уменьшенный, 0,5',value:'0.5'},{label:'Увеличенный, 2',value:'2'}]" /></label></div><UCheckbox v-model="allowIncomplete" :disabled="busy" label="Пропускать чертежи с неполными штампами" class="mt-5" /><small>Номера страниц здесь — по порядку в PDF, начиная с 1.</small></div></details>
          <UAlert v-if="error" color="error" :description="error" class="my-4" />
          <UAlert v-if="busy" color="neutral" variant="subtle" icon="i-lucide-loader-circle" :ui="{ icon: 'animate-spin motion-reduce:animate-none' }" :title="progress" description="Оставьте страницу открытой до завершения обработки." class="my-4" />
          <UButton color="neutral" variant="outline" v-if="!busy" class="primary-button" id="submit-button" type="submit" :disabled="!file || busy" :loading="busy"><span>{{ busy ? 'Обрабатываем документ…' : 'Создать закладки' }}</span><span>↗</span></UButton>
          <p class="privacy-note">Исходный файл не изменяется. Вы получите отдельный PDF.</p>
        </form>
      </section>
      <aside class="info-column"><section class="info-card"><div class="eyebrow">ЧТО ПОЛУЧИТСЯ</div><h2>Каждый лист —<br>на своём месте</h2><div class="bookmark-demo"><div class="tree-parent">Графическая часть</div><div class="tree-child"><UIcon name="i-lucide-bookmark" class="bookmark-symbol" aria-hidden="true" /><div><strong>Лист 79 30/09-ИЛО.КР</strong><span>Здание решеток. Армирование стен</span></div></div><div class="tree-child muted"><UIcon name="i-lucide-bookmark" class="bookmark-symbol" aria-hidden="true" /><div><strong>Лист 80 30/09-ИЛО.КР</strong><span>Здание решеток. Сечение 4-4</span></div></div></div><p class="example-caption">Пример названий, сформированных из штампа</p><ul class="benefits"><li><span>✓</span> Содержательные разделы сохраняются</li><li><span>✓</span> Автоматические ветки листов заменяются</li><li><span>✓</span> Наши закладки — в «Графической части»</li></ul></section><UAlert class="mt-5" color="neutral" variant="subtle" icon="i-lucide-info" title="Нужен текстовый слой" description="Подходит стандартный штамп 185 × 55 мм. Если PDF — скан, сначала распознайте текст с помощью OCR." /></aside>
    </div>
    <section class="result-card" id="result" aria-labelledby="result-heading" v-if="result"><div class="result-top"><div><div class="success-label"><UIcon name="i-lucide-circle-check" class="size-5 shrink-0 text-success" /><span>Обработка завершена</span></div><h2 id="result-heading">Документ готов к работе</h2><p id="result-summary">{{ result.filename }} · {{ result.pages }} стр. PDF · Добавлено закладок: {{ result.added }}</p></div><UButton class="download-button" external download :to="'/bookmarks/api/jobs/'+encodeURIComponent(result.id)+'/download/pdf'" id="download-pdf" color="neutral" variant="outline" icon="i-lucide-download">Скачать PDF</UButton></div><UAlert v-if="result.warnings.length" color="warning" :description="result.warnings.join(' ')" class="my-4" /><div class="result-toolbar"><h3>Закладки в «Графической части» <span>{{ result.added }}</span></h3><UButton external download :to="'/bookmarks/api/jobs/'+encodeURIComponent(result.id)+'/download/csv'" id="download-csv" color="neutral" variant="outline" icon="i-lucide-download">Скачать CSV</UButton></div><div class="table-scroll"><table><thead><tr><th>ЛИСТ</th><th>НАЗВАНИЕ ЗАКЛАДКИ</th><th>СТР. PDF</th></tr></thead><tbody><tr v-for="(drawing,index) in result.drawings" :key="index"><td>{{ drawing.sheet }}</td><td>{{ drawing.title }}</td><td>{{ drawing.page }}</td></tr></tbody></table></div></section>


  </div>
</main></div></template>
<style scoped>
.bookmarks-native { color:var(--ui-text); }
#workspace { max-width:1440px; margin:auto; padding:40px 32px; }
.intro h1 { font-size:36px; font-weight:700; line-height:1.2; letter-spacing:-.035em; }
.intro h1 br { display:none; }
.intro p { margin-top:12px; color:var(--ui-text-muted); }
.eyebrow { color:var(--ui-text-muted); font-size:12px; font-weight:600; letter-spacing:.08em; margin-bottom:8px; }
.how-section { margin:28px 0; padding:24px; border:1px solid var(--ui-border); border-radius:12px; background:var(--ui-bg); }
h2 { font-size:22px; font-weight:600; color:var(--ui-text-highlighted); }
h3 { font-weight:600; }
.how-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:24px; margin-top:20px; }
.how-grid article>span { color:var(--ui-primary); font-size:13px; }
.how-grid h3 { margin:8px 0; }
.how-grid p,.privacy-note,.file-limit,.expiry-note { color:var(--ui-text-muted); font-size:14px; line-height:1.7; }
.steps { display:flex; gap:24px; margin:24px 0; padding:0; list-style:none; flex-wrap:wrap; }
.steps li { color:var(--ui-text-muted); }
.steps li.current { color:var(--ui-primary); font-weight:600; }
.steps li span { margin-right:8px; }
.workspace-grid { display:grid; grid-template-columns:minmax(0,1.4fr) minmax(0,1fr); gap:24px; align-items:start; }
.work-card,.info-card,.result-card { padding:24px; border:1px solid var(--ui-border); border-radius:12px; background:var(--ui-bg); }
.card-heading,.result-top { display:flex; justify-content:space-between; gap:16px; }
.dropzone { margin:24px 0; padding:36px 20px; text-align:center; border:2px dashed var(--ui-border-accented); border-radius:12px; }
.upload-icon { color:var(--ui-text-muted); font-size:32px; }
.dropzone p { margin:8px 0 16px; color:var(--ui-text-muted); }
.file-limit { display:block; margin-top:16px; }
.primary-button { display:flex; justify-content:space-between; width:100%; margin-top:20px; padding:12px 16px; background:var(--ui-primary); color:white; border:0; box-shadow:none; }
.primary-button:disabled { background:#aeb4b7; }
.privacy-note { margin-top:12px; }
.settings { margin:20px 0; }
.settings summary { cursor:pointer; font-weight:500; }
.settings-content { margin-top:16px; }
.field-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin:16px 0; }
input:not([type=checkbox]),select { display:block; width:100%; margin-top:6px; padding:8px; border:1px solid var(--ui-border); border-radius:6px; }
input[type=checkbox] { accent-color:var(--ui-primary); }
.bookmark-demo { margin:24px 0 12px; padding:20px; border:1px solid var(--ui-border); border-radius:8px; }
.tree-child { display:flex; gap:12px; padding:12px 0 0 16px; }
.tree-child strong,.tree-child div>span { display:block; }
.tree-child div>span { color:var(--ui-text-muted); font-size:13px; margin-top:4px; }
.info-card :deep(*) { opacity:1; }
.info-card p,.info-card li,.info-card small { color:var(--ui-text-muted); }
.info-card ul { margin-top:20px; padding-left:20px; line-height:2; }
.bookmark-symbol { color:var(--ui-primary); width:20px; height:20px; flex:0 0 20px; margin-top:3px; }
.selected-file { display:flex; gap:16px; align-items:center; margin:20px 0; padding:16px; border:1px solid var(--ui-border); border-radius:8px; }
.file-info { flex:1; min-width:0; overflow-wrap:anywhere; }
.file-info small { display:block; color:var(--ui-text-muted); }
.pdf-icon { background:#ed1c2a; color:white; padding:18px 10px; border-radius:6px; font-weight:700; }
.message,.processing { margin:16px 0; padding:14px; background:var(--ui-bg-muted); border-radius:8px; }
.result-card { margin-top:24px; }
.download-button { color:var(--ui-primary); text-decoration:underline; }
.result-toolbar { display:flex; justify-content:space-between; margin:20px 0; gap:16px; }
.table-scroll { overflow:auto; }
table { width:100%; text-align:left; }
:deep(th),:deep(td) { padding:12px; border-bottom:1px solid var(--ui-border); }
footer { margin-top:32px; color:var(--ui-text-muted); font-size:12px; }
[hidden] { display:none!important; }
@media(max-width:900px){.workspace-grid,.how-grid,.field-grid { grid-template-columns:1fr; } #workspace{padding:24px 16px;}}

.intro { display:flex; align-items:center; justify-content:space-between; gap:24px; }
.document-art { position:relative; width:240px; height:210px; flex-shrink:0; }
.art-sheet { position:absolute; width:150px; height:180px; border:1px solid var(--ui-border-accented); border-radius:8px; background:white; }
.art-sheet.back { top:4px; left:44px; transform:rotate(10deg); background:var(--ui-bg-muted); }
.art-sheet.front { top:12px; left:24px; padding:14px; transform:rotate(-5deg); }
.art-top,.art-stamp { display:flex; justify-content:space-between; font-size:10px; }
.drawing-grid { height:110px; margin:10px 0; background:repeating-linear-gradient(0deg,transparent,transparent 14px,#e4e4e7 15px),repeating-linear-gradient(90deg,transparent,transparent 14px,#e4e4e7 15px); position:relative; }
.drawing-plan { position:absolute; inset:20px; border:3px double var(--ui-text-muted); }
.dimension { font-size:9px; color:var(--ui-text-muted); }
.dimension.vertical { position:absolute; right:0; top:50%; }
.art-badge { position:absolute; bottom:0; right:0; padding:8px 12px; border:1px solid var(--ui-border); border-radius:8px; background:white; color:var(--ui-primary); font-size:12px; }
:deep(button:not(:disabled)) { pointer-events:auto; cursor:pointer; }
@media(max-width:640px){.document-art { display:none; }}

.steps { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:20px; width:100%; }
.steps li { padding:16px 0; border-bottom:2px solid var(--ui-border); line-height:1.5; }
.steps li.current { border-bottom-color:var(--ui-primary); }
.checkbox { display:flex; align-items:flex-start; gap:10px; margin-top:18px; line-height:1.6; }
.checkbox input { flex:0 0 18px; width:18px; height:18px; margin:4px 0 0; }
.settings-content>small { display:block; margin-top:10px; color:var(--ui-text-muted); line-height:1.6; }
.settings summary>span { margin-left:10px; color:var(--ui-text-muted); font-size:13px; }
@media(max-width:640px){.steps { grid-template-columns:1fr; gap:0; }}

.selected-file { padding:20px; border-radius:12px; gap:16px; }
.pdf-icon { position:relative; display:flex; align-items:flex-end; justify-content:center; flex:0 0 52px; width:52px; height:64px; padding:0 0 9px; overflow:hidden; background:#ed1c2a; color:white; border-radius:6px; font-size:14px; font-weight:700; }
.pdf-icon::before { content:''; position:absolute; top:0; right:0; border-style:solid; border-width:0 17px 17px 0; border-color:transparent white transparent transparent; }
.file-info small { display:none; }
:deep(#remove-file) { display:flex; align-items:center; justify-content:center; flex:0 0 34px; width:34px; height:34px; padding:0; border:1px solid var(--ui-border); border-radius:8px; background:var(--ui-bg-muted); color:var(--ui-text-muted); font-size:24px; box-shadow:none; }
:deep(#remove-file:hover:not(:disabled)) { background:#fee2e2; border-color:#fca5a5; color:#b91c1c; }
:deep(#download-pdf),:deep(#download-csv) { display:inline-flex; align-items:center; justify-content:center; gap:8px; min-height:40px; padding:9px 14px; border:1px solid var(--ui-border-accented); border-radius:8px; background:var(--ui-bg); color:var(--ui-text); font-size:14px; font-weight:600; line-height:1.4; text-decoration:none; box-shadow:none; white-space:nowrap; }
:deep(#download-pdf:hover),:deep(#download-csv:hover) { background:var(--ui-bg-muted); color:var(--ui-primary); }
.success-label { display:flex; align-items:center; gap:8px; margin-bottom:12px; font-size:14px; font-weight:600; color:var(--ui-text); }
:deep(#download-pdf),:deep(#download-csv) { align-self:flex-start; flex:0 0 auto; width:auto; height:40px; min-height:40px; padding:8px 14px; }
.checkbox input { appearance:none; position:relative; width:20px; height:20px; flex:0 0 20px; border:1px solid var(--ui-border-accented); border-radius:4px; background:var(--ui-bg); cursor:pointer; }
.checkbox input:checked { background:var(--ui-primary); border-color:var(--ui-primary); }
.checkbox input:checked::after { content:''; position:absolute; left:6px; top:2px; width:6px; height:11px; border:solid white; border-width:0 2px 2px 0; transform:rotate(45deg); }
.checkbox input:active { border-color:var(--ui-primary); }
.checkbox input:focus-visible { outline:2px solid var(--ui-primary); outline-offset:3px; }
#result-summary { margin-top:10px; color:var(--ui-text-muted); line-height:1.7; }
@media(max-width:640px){.result-top,.result-toolbar { flex-direction:column; align-items:flex-start; }}
</style>
