<script setup>
import { onMounted, ref } from 'vue'
const error = ref('')
onMounted(async () => {
  for (const id of ['analyze', 'export']) document.querySelector(`.signatures-native #${id}`).disabled = true
  try { await import(/* @vite-ignore */ '/signatures/app.mjs') }
  catch (e) { error.value = 'Не удалось загрузить проверку: ' + e.message }
})
</script>
<template>
<div class="signatures-native">
<UAlert v-if="error" color="error" :description="error" />
<main class="page-shell">
 <div class="page-heading"><div><h1>Проверка подписантов</h1><p>Загрузите PDF-документ, чтобы найти и проверить подписи.</p></div></div>
 <div class="workspace-card">
 <div class="workspace">
 <section id="upload-panel" class="panel upload-panel" aria-labelledby="upload-title">
  <h2 id="upload-title"><span class="step-number">1</span><span class="empty-label">Загрузите документы</span><span class="loaded-label">Документы</span></h2>
  <div id="dropzone" class="dropzone"><span class="upload-icon" aria-hidden="true"><svg viewBox="0 0 64 64" class="file-icon"><path d="M17 5h22l13 13v41H17z"/><path d="M39 5v14h13M24 45c3-7 5-9 7-5 2 5 4 4 8-4"/></svg></span><h3>Перетащите PDF и SIG сюда</h3><p>SIG — необязательно</p><label class="choose">Выбрать файлы<input id="files" type="file" accept=".pdf,.sig,.sgn,.p7s" multiple></label><small>PDF до 100 МБ</small></div>
  <ul id="file-list" class="file-list" aria-label="Выбранные файлы"></ul>
  <UButton id="add-files" class="secondary add-files" type="button" color="neutral" variant="outline">＋ &nbsp;Добавить PDF или SIG</UButton>
  <details class="options"><summary>Параметры</summary><div class="settings"><label for="scope">Страницы</label><select id="scope"><option value="all">Весь документ</option><option value="first">Диапазон страниц</option></select><label for="page-start" id="page-start-label" hidden>Начать со страницы</label><input id="page-start" type="number" min="1" value="1" hidden><label for="page-count" id="page-label" hidden>Число страниц</label><input id="page-count" type="number" min="1" max="200" value="3" hidden><label class="handwriting-setting"><input id="handwriting-check" type="checkbox" checked> Проверять рукописные на чертежах</label></div></details>
  <UButton id="analyze" class="primary" type="button" color="neutral" variant="outline"><span>Проверить подписантов</span><span>↗</span></UButton>
  <p class="process" id="progress" role="status" aria-live="polite"></p><div class="error" id="upload-error" role="alert" hidden></div>
 </section>
 <section class="panel results" aria-labelledby="result-title">
  <div class="list-heading"><div><h2 id="result-title"><span class="step-number">2</span>Результаты проверки <span id="count-all" class="count" hidden>0</span></h2><p id="report-filename" hidden></p></div><div class="result-actions"><UButton class="secondary edit-list-button" id="edit-list" color="neutral" variant="outline">✎&nbsp; Изменить список</UButton></div></div>
  <div class="table-tools"><div class="tabs" role="group" aria-label="Фильтр результата"><UButton class="selected" data-filter="all" color="neutral" variant="outline">Все <b>0</b></UButton><UButton data-filter="missing" color="neutral" variant="ghost">Без подписи <b>0</b></UButton><UButton data-filter="review" color="neutral" variant="ghost">Требуют проверки <b>0</b></UButton></div></div>
  <div class="error list-notice" id="list-notice" role="alert" hidden></div>
  <div class="table-wrap"><table><thead><tr><th scope="col">Фамилия / ФИО</th><th scope="col">Подписи</th><th scope="col">Результат</th></tr></thead><tbody id="people"></tbody></table></div>
  <div class="table-empty" id="table-empty"><span class="empty-result-icon" aria-hidden="true"><svg viewBox="0 0 64 64" class="file-icon"><path d="M17 5h22l13 13v41H17z"/><path d="M39 5v14h13M24 45c3-7 5-9 7-5 2 5 4 4 8-4"/></svg></span><strong>Результаты появятся после обработки</strong><span>Загрузите PDF и запустите проверку</span></div>
  <div class="table-footer" id="table-footer" hidden><span id="page-source"></span><div class="footer-links"><UButton class="text-button" id="export" color="neutral" variant="outline">Скачать CSV ↓</UButton><span class="footer-separator">|</span><UButton class="text-button" id="preview-button" hidden color="neutral" variant="outline">Открыть PDF ↗</UButton></div></div>
 </section>
 </div>
 <div class="workspace-footer"><p>ⓘ&nbsp; <span id="footer-hint">Добавьте PDF для начала проверки</span></p></div>
 </div>
</main>
<dialog id="list-editor" class="list-editor"><div class="dialog-head"><strong>Изменить список</strong><UButton class="text-button" id="close-list-editor" aria-label="Закрыть редактор списка" color="neutral" variant="outline">Закрыть ×</UButton></div><div class="editor-body"><label for="expected">Фамилия / ФИО — одна строка на человека</label><textarea id="expected" rows="9" spellcheck="false"></textarea><UButton class="primary" id="apply" color="neutral" variant="outline">Сохранить список</UButton><p id="editor-error" role="alert"></p></div></dialog>
<dialog id="preview"><div class="dialog-head"><strong id="preview-title">Источник в PDF</strong><UButton class="text-button" id="close-preview" aria-label="Закрыть просмотр" color="neutral" variant="outline">Закрыть ×</UButton></div><div class="source-layout"><div class="source-document"><nav class="page-navigation" aria-label="Страницы PDF"><UButton class="secondary" id="page-prev" aria-label="Предыдущая страница" color="neutral" variant="outline">←</UButton><label for="preview-page">Страница</label><input id="preview-page" type="number" min="1" value="1"><span id="preview-total"></span><UButton id="preview-zoom" class="secondary" hidden color="neutral" variant="outline">Весь лист</UButton><UButton class="secondary" id="page-next" aria-label="Следующая страница" color="neutral" variant="outline">→</UButton></nav><div id="preview-pages"></div></div><section class="source-editor" id="source-editor" aria-label="Исправление фамилии"><h3>Проверить запись</h3><p id="source-help"></p><label>Текст в PDF</label><blockquote id="source-text"></blockquote><div id="source-handwriting"></div><label for="source-name">Фамилия / ФИО</label><input id="source-name" autocomplete="off"><label for="source-role">Должность</label><input id="source-role" autocomplete="off"><UButton class="primary" id="source-save" color="neutral" variant="outline">Сохранить</UButton><UButton class="secondary" id="source-remove" color="neutral" variant="outline">Убрать из списка</UButton><p id="source-error" role="alert"></p></section></div></dialog>

</div>
</template>
<style scoped src="../../signatures/dist/style.css"></style>
<style scoped>
.signatures-native { --ink:var(--ui-text); --muted:var(--ui-text-muted); --orange:var(--ui-primary); --line:var(--ui-border); --paper:var(--ui-bg-muted); --pale:#fff2e8; --green:#276b4e; font-family: var(--font-sans); color: var(--ui-text); }
.page-shell { max-width:1440px; }
.page-heading h1 { font-size:36px; font-weight:700; }
:deep(.primary) { background:var(--ui-primary); color:white; }
:deep(.primary:disabled) { background:#e7ebee; color:#89949b; }
.results .tabs :deep(button) { border:0; border-bottom:2px solid transparent; border-radius:0; box-shadow:none; outline-offset:2px; background:transparent; color:var(--ui-text-muted); padding:12px 16px; }
.results .tabs :deep(button.selected) { background:transparent; border-bottom-color:var(--ui-primary); color:var(--ui-primary); }
.results .tabs :deep(button:hover) { background:var(--ui-bg-muted); }
.result-actions :deep(button), .footer-links :deep(button) { display:inline-flex; align-items:center; justify-content:center; gap:8px; min-height:40px; padding:9px 14px; border-radius:8px; font-size:14px; font-weight:600; line-height:1.4; text-decoration:none; color:var(--ui-text); background:var(--ui-bg); box-shadow:inset 0 0 0 1px var(--ui-border-accented); }
.result-actions :deep(button:hover:not(:disabled)), .footer-links :deep(button:hover:not(:disabled)) { background:var(--ui-bg-muted); color:var(--ui-primary); }
.footer-links { flex-wrap:wrap; gap:12px; }
.footer-separator { display:none; }
.results .table-wrap { overflow-x:auto; }
.results table { min-width:650px; }
.results :deep(td) { padding:24px 20px; vertical-align:top; border-bottom:1px solid var(--ui-border); font-size:14px; line-height:1.7; overflow-wrap:anywhere; }
.results :deep(td strong) { display:block; margin-bottom:8px; font-size:16px; line-height:1.5; font-weight:600; color:var(--ui-text-highlighted); }
.results :deep(td small) { display:block; margin:6px 0; color:var(--ui-text-muted); font-size:13px; }
.results :deep(.source-links) { display:flex; flex-wrap:wrap; align-items:center; gap:8px; margin-top:12px; }
.results :deep(.source-link) { display:inline-flex; align-items:center; padding:4px 10px; border:1px solid var(--ui-border); border-radius:6px; background:var(--ui-bg-muted); color:var(--ui-primary); font-size:13px; font-weight:500; line-height:1.6; text-decoration:underline; text-underline-offset:3px; cursor:pointer; }
.results :deep(.source-link:hover) { background:var(--pale); border-color:var(--ui-primary); }
.results :deep(.edit-person) { margin-top:12px; }
.results :deep(.row-details) { margin-top:14px; font-size:13px; color:var(--ui-text-muted); }
.results :deep(.row-details summary) { cursor:pointer; text-decoration:underline; text-underline-offset:3px; }
.results :deep(.row-details p) { margin-top:8px; }
.results :deep(.badge) { display:inline-block; padding:6px 10px; border-radius:6px; font-size:13px; font-weight:600; line-height:1.5; background:#eaf4ee; color:#276b4e; }
.results :deep(.badge.missing) { background:#ffe1e3; color:#b91c1c; }
.results :deep(.badge.review) { background:#fff0c9; color:#926000; }
:deep(button.primary) { border:0; box-shadow:none; --tw-ring-shadow:0 0 transparent; --tw-inset-ring-shadow:0 0 transparent; }
.handwriting-setting input { appearance:none; width:20px; height:20px; margin:3px 0 0; border:1px solid var(--ui-border-accented); border-radius:4px; background:var(--ui-bg); cursor:pointer; accent-color:var(--ui-primary); }
.handwriting-setting input:checked { border-color:var(--ui-primary); background-color:var(--ui-primary); background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20'%3E%3Cpath d='m5 10 3 3 7-7' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E"); }
.handwriting-setting input:active { border-color:var(--ui-primary); }
.handwriting-setting input:focus-visible { outline:2px solid var(--ui-primary); outline-offset:3px; }
.dialog-head :deep(button) { display:inline-flex; align-items:center; justify-content:center; min-height:38px; padding:8px 14px; border:1px solid var(--ui-border-accented); border-radius:8px; background:var(--ui-bg); color:var(--ui-text); font-size:14px; font-weight:600; line-height:1.4; text-decoration:none; white-space:nowrap; box-shadow:none; }
.dialog-head :deep(button:hover) { background:var(--ui-bg-muted); }
.handwriting-setting input:checked { background-image:none; position:relative; }
.handwriting-setting input:checked::after { content:''; position:absolute; left:6px; top:2px; width:6px; height:11px; border:solid white; border-width:0 2px 2px 0; transform:rotate(45deg); }
.file-list :deep(li) { display:flex; align-items:center; gap:16px; padding:20px; margin-bottom:14px; border:1px solid var(--ui-border); border-radius:12px; background:var(--ui-bg); }
.file-list :deep(.pdf-badge) { position:relative; display:flex; align-items:flex-end; justify-content:center; flex:0 0 52px; width:52px; height:64px; padding-bottom:9px; overflow:hidden; border-radius:6px; background:#ed1c2a; color:white; }
.file-list :deep(.pdf-badge::before) { content:''; position:absolute; right:0; top:0; border-style:solid; border-width:0 17px 17px 0; border-color:transparent white transparent transparent; }
.file-list :deep(.pdf-badge span) { font-size:14px; font-weight:700; line-height:1; }
.file-list :deep(.file-name) { flex:1; min-width:0; font-size:15px; font-weight:600; line-height:1.6; overflow-wrap:anywhere; }
.file-list :deep(li>button) { display:flex; align-items:center; justify-content:center; flex:0 0 34px; width:34px; height:34px; padding:0; border:1px solid var(--ui-border); border-radius:8px; background:var(--ui-bg-muted); color:var(--ui-text-muted); font-size:24px; line-height:1; cursor:pointer; }
.file-list :deep(li>button:hover:not(:disabled)) { background:#fee2e2; border-color:#fca5a5; color:#b91c1c; }
#report-filename { display:none!important; }
dialog { position:fixed; inset:0; margin:auto; max-width:calc(100vw - 32px); max-height:calc(100dvh - 32px); overflow:auto; }
.results .table-footer { color:var(--ui-text-muted); font-size:14px; }
.results .table-footer :deep(#export),.results .table-footer :deep(#preview-button) { display:inline-flex; align-items:center; justify-content:center; gap:8px; align-self:flex-start; height:40px; min-height:40px; padding:8px 14px; border:1px solid var(--ui-border-accented); border-radius:8px; background:var(--ui-bg); color:var(--ui-text); font-size:14px; font-weight:600; line-height:1.4; text-decoration:none; box-shadow:none; }
.results .table-footer :deep(#export:hover:not(:disabled)),.results .table-footer :deep(#preview-button:hover:not(:disabled)) { background:var(--ui-bg-muted); color:var(--ui-primary); }
</style>
