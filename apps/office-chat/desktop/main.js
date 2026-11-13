'use strict';

const { app, BrowserWindow, dialog, ipcMain, screen } = require('electron');
const { createHash } = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const { setTimeout: delay } = require('node:timers/promises');

let config;
let mainWindow;
let quitting = false;
const windows = new Map();
const incoming = new Map();
const state = { revision: 0, user: '', users: {}, messages: [], presence: {}, status: 'online', connection: 'connecting' };
const headers = { 'Content-Type': 'application/json' };

function readConfig() {
  const file = process.argv.at(-1);
  if (!file) throw new Error('Укажите файл настроек клиента.');
  const data = JSON.parse(fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, ''));
  const url = new URL(data.server);
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password || url.search || url.hash) {
    throw new Error('В настройках нужен адрес HTTP или HTTPS.');
  }
  if (!/^\d+$/.test(String(data.user)) || typeof data.token !== 'string' || !data.token) {
    throw new Error('Укажите ID сотрудника и токен.');
  }
  return { ...data, user: String(data.user), server: url.href.replace(/\/$/, '') };
}

async function request(route, body, timeout = 5000) {
  const response = await fetch(config.server + route, {
    method: body === undefined ? 'GET' : 'POST', headers,
    body: body === undefined ? undefined : JSON.stringify(body),
    signal: AbortSignal.timeout(timeout), redirect: 'error',
  });
  if (!response.ok) {
    const error = new Error('Chat server returned an error');
    error.status = response.status;
    throw error;
  }
  return response.json();
}

function snapshot(window) {
  const contact = windows.get(window.webContents.id)?.contact;
  if (!contact) return { ...state, contact: null };
  const messages = state.messages.filter(row => row.sender === contact || row.recipient === contact);
  return { ...state, contact, messages };
}

function publish() {
  state.revision += 1;
  for (const { window, ready } of windows.values()) {
    if (ready && !window.isDestroyed()) window.webContents.send('chat:update', snapshot(window));
  }
}

function makeWindow(contact = null) {
  const window = new BrowserWindow({
    width: contact ? 660 : 1140, height: contact ? 580 : 760,
    minWidth: contact ? 430 : 760, minHeight: contact ? 410 : 500,
    show: false, alwaysOnTop: Boolean(contact), autoHideMenuBar: true,
    title: contact ? `${state.users[contact] || 'Диалог'} — Офисный чат` : 'Офисный чат',
    titleBarStyle: 'hidden',
    titleBarOverlay: { color: '#ffffff', symbolColor: '#526075', height: 39 },
    backgroundColor: '#f4f6fb',
    webPreferences: { preload: path.join(__dirname, 'preload.js'), sandbox: true, contextIsolation: true },
  });
  const id = window.webContents.id;
  const view = { window, contact, ready: false };
  windows.set(id, view);
  window.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  window.webContents.on('will-navigate', event => event.preventDefault());
  window.once('ready-to-show', () => {
    if (contact) present(window);
    else window.show();
  });
  window.on('closed', () => {
    windows.delete(id);
    if (contact) incoming.delete(contact);
  });
  window.loadFile(path.join(__dirname, 'index.html')).catch(() => window.close());
  return window;
}

function present(window) {
  if (!window.isVisible() || window.isMinimized()) {
    if (window.isMinimized()) window.restore();
    const { workArea } = screen.getDisplayNearestPoint(screen.getCursorScreenPoint());
    const [width, height] = window.getSize();
    window.setPosition(workArea.x + Math.round((workArea.width - width) / 2),
      workArea.y + Math.round((workArea.height - height) / 2));
  }
  window.showInactive();
  window.moveTop();
}

function openIncoming(contact) {
  const existing = incoming.get(contact);
  if (existing) {
    if (!existing.webContents.isLoading()) present(existing);
    return;
  }
  incoming.set(contact, makeWindow(contact));
}

async function listen() {
  let cursor = null;
  while (!quitting) {
    try {
      if (cursor === null) {
        const initial = await request('/bootstrap');
        state.users = initial.users;
        state.messages = initial.messages;
        cursor = state.messages.at(-1)?.id ?? 0;
      }
      if (state.connection !== 'online') {
        state.connection = 'online';
        publish();
      }
      const rows = await request(`/events?after=${cursor}`, undefined, 22000);
      if (!rows.length) continue;
      cursor = rows.at(-1).id;
      state.messages.push(...rows);
      publish();
      const contacts = new Set(rows.filter(row => row.recipient === state.user).map(row => row.sender));
      for (const contact of contacts) openIncoming(contact);
    } catch (error) {
      const connection = error.status === 401 ? 'unauthorized' : 'offline';
      if (state.connection !== connection) {
        state.connection = connection;
        publish();
      }
      if (connection === 'unauthorized') return;
      await delay(1000);
    }
  }
}

let presenceInFlight = false;
async function heartbeat() {
  if (presenceInFlight || quitting) return;
  presenceInFlight = true;
  const sent = state.status;
  try {
    const presence = await request('/presence', { status: sent });
    if (JSON.stringify(presence) !== JSON.stringify(state.presence)) {
      state.presence = presence;
      publish();
    }
  } catch {
    // Delivery has its own connection indicator and retry loop.
  } finally {
    presenceInFlight = false;
    if (sent !== state.status) void heartbeat();
  }
}

function viewFor(event) {
  const view = windows.get(event.sender.id);
  if (!view || event.senderFrame !== event.sender.mainFrame) throw new Error('Invalid window');
  return view;
}

app.whenReady().then(() => {
  try {
    config = readConfig();
    const profile = createHash('sha256').update(`${config.server}\n${config.user}`).digest('hex').slice(0, 24);
    const dataPath = path.join(app.getPath('appData'), 'OfficeChat', profile);
    fs.mkdirSync(dataPath, { recursive: true });
    app.setPath('userData', dataPath);
  } catch (error) {
    console.error('Office Chat could not start:', error.message);
    dialog.showErrorBox('Офисный чат', error.message);
    app.quit();
    return;
  }
  state.user = config.user;
  headers.Authorization = 'Bearer ' + config.token;
  headers['X-User'] = config.user;
  app.setAppUserModelId('Company.OfficeChat');
  ipcMain.handle('chat:state', event => {
    const view = viewFor(event);
    view.ready = true;
    return snapshot(view.window);
  });
  ipcMain.handle('chat:send', async (event, { recipient, text, nonce }) => {
    const view = viewFor(event);
    if (!Object.hasOwn(state.users, recipient) || recipient === state.user ||
        (view.contact && recipient !== view.contact) || typeof text !== 'string' ||
        !text.trim() || [...text].length > 4000 || typeof nonce !== 'string') return false;
    try {
      await request('/messages', { recipient, text, nonce });
      return true;
    } catch {
      return false;
    }
  });
  ipcMain.handle('chat:status', (event, status) => {
    if (viewFor(event).contact || !['online', 'away', 'busy'].includes(status)) return;
    state.status = status;
    publish();
    void heartbeat();
  });
  ipcMain.handle('chat:quit', event => {
    if (!viewFor(event).contact) app.quit();
  });
  mainWindow = makeWindow();
  mainWindow.on('close', event => {
    if (!quitting) {
      event.preventDefault();
      mainWindow.minimize();
    }
  });
  void listen();
  void heartbeat();
  setInterval(heartbeat, 3000).unref();
});

app.on('before-quit', () => { quitting = true; });
