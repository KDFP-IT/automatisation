const nav = document.querySelector(".sidebar nav");
const workspace = document.querySelector("#workspace");
const frames = new Map();
const embedded = [];

function applyToolStyles(frame, tool) {
  const document = frame.contentDocument;
  if (!document || document.location.origin !== location.origin) return;

  document.documentElement.dataset.portalTool = tool;
  const stylesheet = document.createElement("link");
  stylesheet.rel = "stylesheet";
  stylesheet.href = "/portal/embedded.css";
  document.head.append(stylesheet);
}

function selectTool() {
  const active = embedded.find(tool => tool.link.hash === location.hash) ?? embedded[0];
  if (!active) return;

  for (const { link } of embedded) {
    if (link === active.link) {
      link.setAttribute("aria-current", "page");
    } else {
      link.removeAttribute("aria-current");
    }
  }

  if (!frames.has(active.link.hash)) {
    const frame = document.createElement("iframe");
    frame.title = active.link.textContent;
    frame.addEventListener("load", () => applyToolStyles(frame, active.id));
    frame.src = active.url;
    workspace.append(frame);
    frames.set(active.link.hash, frame);
  }

  for (const [hash, frame] of frames) {
    frame.hidden = hash !== active.link.hash;
  }
}

async function loadTools() {
  const response = await fetch("/portal/tools.json", { cache: "no-store" });
  if (!response.ok) throw new Error("Не удалось загрузить меню");
  const ids = new Set();
  for (const tool of await response.json()) {
    if (!/^[a-z][a-z0-9-]*$/.test(tool.id) || !tool.title || !tool.url || ids.has(tool.id)) {
      throw new Error("Проверьте список инструментов");
    }
    const url = new URL(tool.url, location.origin);
    if (!["http:", "https:"].includes(url.protocol)) throw new Error("Проверьте адрес инструмента");
    ids.add(tool.id);
    const link = document.createElement("a");
    link.textContent = tool.title;
    if (tool.embed && url.origin === location.origin) {
      link.href = "#" + tool.id;
      embedded.push({ id: tool.id, link, url: url.href });
    } else {
      link.href = url.href;
      link.target = "_blank";
      link.rel = "noopener";
    }
    nav.append(link);
  }
  window.addEventListener("hashchange", selectTool);
  selectTool();
}

loadTools().catch(error => {
  workspace.textContent = error.message;
});
