"use strict";
const $ = (id) => document.getElementById(id);
const form = $("upload-form");
let selected = null;
let busy = false;
let polling = null;
let activeId = null;

function message(text) {
  $("message").textContent = text;
  $("message").hidden = !text;
}
function steps(number) {
  [1, 2, 3].forEach((n) => {
    $("step" + n).classList.toggle("current", n === number);
    if (n === number) $("step" + n).setAttribute("aria-current", "step");
    else $("step" + n).removeAttribute("aria-current");
  });
}
function setBusy(value) {
  busy = value;
  $("submit-button").disabled = value || !selected;
  $("remove-file").disabled = value;
  $("choose-file").disabled = value;
  $("processing").hidden = !value;
  form.querySelectorAll("input,select").forEach((input) => { input.disabled = value; });
  $("submit-button").firstElementChild.textContent = value ? "Обрабатываем документ…" : "Создать закладки";
}
function clearResult() {
  $("result").hidden = true;
  $("bookmarks-body").replaceChildren();
  activeId = null;
  sessionStorage.removeItem("pdfJob");
}
function selectFile(file) {
  if (busy || !file) return;
  message("");
  if (!file.name.toLowerCase().endsWith(".pdf")) return message("Выберите файл в формате PDF.");
  if (!file.size) return message("Файл пустой. Выберите другой PDF.");
  if (file.size > 200 * 1024 * 1024) return message("Размер файла превышает 200 МБ. Разделите документ на части.");
  selected = file;
  clearResult();
  $("file-name").textContent = file.name;
  $("file-size").textContent = (file.size / 1024 / 1024).toLocaleString("ru-RU", {maximumFractionDigits: 1}) + " МБ · Готов к обработке";
  $("selected-file").hidden = false;
  $("dropzone").hidden = true;
  setBusy(false);
  steps(1);
}
$("choose-file").addEventListener("click", () => $("file-input").click());
$("file-input").addEventListener("change", (event) => selectFile(event.target.files[0]));
$("remove-file").addEventListener("click", () => {
  if (busy) return;
  selected = null;
  $("file-input").value = "";
  $("selected-file").hidden = true;
  $("dropzone").hidden = false;
  $("submit-button").disabled = true;
  message("");
  clearResult();
  steps(1);
});
["dragenter", "dragover"].forEach((name) => $("dropzone").addEventListener(name, (event) => {
  event.preventDefault();
  if (!busy) $("dropzone").classList.add("dragging");
}));
["dragleave", "drop"].forEach((name) => $("dropzone").addEventListener(name, (event) => {
  event.preventDefault();
  $("dropzone").classList.remove("dragging");
}));
$("dropzone").addEventListener("drop", (event) => {
  if (event.dataTransfer.files.length !== 1) return message("Загрузите один PDF за раз.");
  selectFile(event.dataTransfer.files[0]);
});

function showResult(data) {
  setBusy(false);
  steps(3);
  $("result-summary").textContent = `${data.filename} · ${data.pages} стр. PDF · Добавлено закладок: ${data.added}`;
  $("bookmark-count").textContent = data.added;
  $("download-pdf").href = `./api/jobs/${encodeURIComponent(data.id)}/download/pdf`;
  $("download-csv").href = `./api/jobs/${encodeURIComponent(data.id)}/download/csv`;
  $("warnings").hidden = !data.warnings.length;
  $("warnings").textContent = data.warnings.join("\n");
  const rows = document.createDocumentFragment();
  data.drawings.forEach((drawing) => {
    const row = document.createElement("tr");
    [drawing.sheet, drawing.title, String(drawing.page)].forEach((text) => {
      const cell = document.createElement("td");
      cell.textContent = text;
      row.appendChild(cell);
    });
    rows.appendChild(row);
  });
  $("bookmarks-body").replaceChildren(rows);
  $("result").hidden = false;
  $("result").scrollIntoView({behavior: "smooth", block: "start"});
}
async function responseJson(response) {
  try { return await response.json(); }
  catch (_) { throw new Error("Сервер вернул неожиданный ответ. Попробуйте ещё раз или обратитесь к администратору."); }
}
async function poll(id) {
  if (id !== activeId) return;
  try {
    const response = await fetch(`./api/jobs/${encodeURIComponent(id)}`, {cache: "no-store"});
    const data = await responseJson(response);
    if (!response.ok) throw new Error(data.error);
    message("");
    if (data.status === "done") return showResult(data);
    if (data.status === "error") {
      setBusy(false);
      steps(1);
      sessionStorage.removeItem("pdfJob");
      return message(data.error);
    }
    $("processing-title").textContent = data.status === "queued" ? "Документ в очереди" : "Читаем штампы и закладки";
    $("processing-text").textContent = data.status === "queued" ? "Начнём, как только освободится обработчик." : "Большой документ может обрабатываться несколько минут.";
    polling = setTimeout(() => poll(id), 1500);
  } catch (error) {
    if (error.message.includes("не найдено") || error.message.includes("срок хранения")) {
      sessionStorage.removeItem("pdfJob");
      setBusy(false);
      steps(1);
      return message(error.message);
    }
    message("Связь с сервером прервалась. Проверим статус повторно через 5 секунд. Не загружайте файл заново.");
    polling = setTimeout(() => poll(id), 5000);
  }
}
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!selected || busy || !form.reportValidity()) return;
  const payload = new FormData(form);
  payload.set("file", selected);
  payload.set("allow_incomplete", form.elements.allow_incomplete.checked ? "true" : "false");
  message("");
  clearResult();
  clearTimeout(polling);
  setBusy(true);
  steps(2);
  $("processing-title").textContent = "Загружаем PDF на сервер";
  $("processing-text").textContent = "Оставьте страницу открытой до завершения загрузки.";
  try {
    const response = await fetch("./api/jobs", {method: "POST", body: payload, headers: {"X-PDF-Service": "1"}});
    const data = await responseJson(response);
    if (!response.ok) throw new Error(data.error);
    activeId = data.id;
    sessionStorage.setItem("pdfJob", data.id);
    await poll(data.id);
  } catch (error) {
    setBusy(false);
    steps(1);
    message(error.message === "Failed to fetch" ? "Не удалось загрузить файл. Проверьте подключение и повторите попытку." : error.message);
  }
});
const savedJob = sessionStorage.getItem("pdfJob");
if (savedJob) {
  activeId = savedJob;
  setBusy(true);
  steps(2);
  poll(savedJob);
}
