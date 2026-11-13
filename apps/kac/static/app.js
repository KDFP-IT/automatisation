const form = document.querySelector("#assemble");
const template = document.querySelector("#template");
const templateInfo = document.querySelector("#template-info");
const folders = document.querySelector("#folders");
const drop = document.querySelector("#drop");
const selection = document.querySelector("#selection");
const statusNode = document.querySelector("#status");
const submit = document.querySelector("#submit");
const downloads = document.querySelector("#downloads");
const api = "/kac/api";
let offers = [];
let folderTemplate;
let configuredTemplate;

function showTemplate() {
  const name = folderTemplate?.name ?? configuredTemplate;
  templateInfo.textContent = name
    ? `Будет использован ${name}, если не выбрать другой DOCX.`
    : "Выберите DOCX или загрузите папку проекта с основным документом.";
}

function message(text, error = false) {
  statusNode.textContent = text;
  statusNode.classList.toggle("error", error);
}

function setOffers(files) {
  const documents = files.filter(({ path }) => {
    const parts = path.split("/");
    return parts.length === 2 && /\.docx$/i.test(parts[1]) && !parts[1].startsWith("~$");
  });
  folderTemplate = documents.length === 1 ? documents[0].file : undefined;
  showTemplate();
  offers = files.filter(({ path }) => {
    const parts = path.split("/");
    return [2, 3, 4].includes(parts.length) && /\.pdf$/i.test(parts.at(-1))
      && /^Раздел\s+\d+\s*[-–—]\s*\S/iu.test(parts.at(-2));
  });
  const count = new Set(offers.map(({ path }) => path.split("/").at(-2))).size;
  selection.textContent = offers.length
    ? `Папок с КП: ${count}. PDF: ${offers.length}.`
    : "В выбранных папках нет PDF в папках вида «Раздел 1 - Название».";
}

folders.addEventListener("change", () => {
  setOffers(Array.from(folders.files, file => ({ file, path: file.webkitRelativePath })));
});

async function collect(entry, depth = 1) {
  if (entry.isFile) {
    const file = await new Promise((resolve, reject) => entry.file(resolve, reject));
    return [{ file, path: entry.fullPath.slice(1) }];
  }
  if (!entry.isDirectory || depth === 4) return [];
  const reader = entry.createReader();
  const files = [];
  for (;;) {
    const entries = await new Promise((resolve, reject) => reader.readEntries(resolve, reject));
    if (!entries.length) return files;
    for (const child of entries) files.push(...await collect(child, depth + 1));
  }
}

for (const event of ["dragenter", "dragover", "dragleave", "drop"]) {
  drop.addEventListener(event, e => {
    e.preventDefault();
    drop.classList.toggle("active", event === "dragenter" || event === "dragover");
  });
}
drop.addEventListener("drop", async event => {
  const entries = Array.from(event.dataTransfer.items, item => item.webkitGetAsEntry?.()).filter(Boolean);
  try {
    setOffers((await Promise.all(entries.map(entry => collect(entry)))).flat());
  } catch {
    message("Не удалось прочитать папки. Выберите их через кнопку загрузки.", true);
  }
});

async function request(url, options) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error ?? (response.status === 413
      ? "Объём загрузки превышает 200 МБ."
      : "Портал не ответил. Попробуйте ещё раз."));
  }
  return data;
}

form.addEventListener("submit", async event => {
  event.preventDefault();
  const source = template.files[0] ?? folderTemplate;
  if ((!source && !configuredTemplate) || !offers.length) {
    message("Выберите основной DOCX и папки с PDF.", true);
    return;
  }
  submit.disabled = true;
  downloads.hidden = true;
  message("Загружаю документ и КП…");
  try {
    const body = new FormData();
    if (source) body.append("docx", source);
    for (const { file, path } of offers) body.append("offer", file, path);
    const { id } = await request(api + "/jobs", { method: "POST", body });
    let job;
    do {
      await new Promise(resolve => setTimeout(resolve, 2000));
      job = await request(`${api}/jobs/${id}`);
      if (job.status === "error") throw new Error(job.error);
      message(job.status === "queued" ? "Комплект в очереди." : "Собираю PDF и картинки…");
    } while (job.status !== "done");
    for (const kind of ["pdf", "zip"]) {
      document.querySelector("#" + kind).href = `${api}/jobs/${id}/${kind}`;
    }
    downloads.hidden = false;
    message(`Готово. Разделов: ${job.sections}. Страниц КП и картинок: ${job.pages}.`);
  } catch (error) {
    message(error.message, true);
  } finally {
    submit.disabled = false;
  }
});

request(api + "/health").then(({ available, template }) => {
  configuredTemplate = template;
  showTemplate();
  submit.disabled = !available;
  if (!available) message("Обработчик КАЦ недоступен. Обратитесь к администратору портала.", true);
}).catch(error => message(error.message, true));
