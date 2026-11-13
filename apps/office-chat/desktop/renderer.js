'use strict';

const $ = id => document.getElementById(id);
const api = window.officeChat;
const statuses = { online: 'В сети', away: 'Отошёл', busy: 'Занят', offline: 'Не в сети' };
const connections = { connecting: 'Подключение…', online: 'Подключено', offline: 'Переподключение…', unauthorized: 'Проверьте ID и токен' };
const clock = new Intl.DateTimeFormat('ru', { hour: '2-digit', minute: '2-digit' });
const date = new Intl.DateTimeFormat('ru', { day: 'numeric', month: 'long' });
const fullDate = new Intl.DateTimeFormat('ru', { dateStyle: 'long' });
const drafts = new Map();
const attempts = new Map();
const unread = new Map();
const sending = new Set();
let state;
let contact = null;
let filter = 'all';
let directoryMode = false;
let paintedContact;
let paintedLastId;

function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text) element.textContent = text;
  if (className) element.className = className;
  return element;
}

function icon(name) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  const use = document.createElementNS(svg.namespaceURI, 'use');
  use.setAttribute('href', '#i-' + name);
  svg.setAttribute('aria-hidden', 'true');
  svg.append(use);
  return svg;
}

function avatar(element, user, status) {
  const name = state.users[user];
  const tone = user ? Number(BigInt(user) % 5n) : 0;
  element.className = `avatar tone-${tone}`;
  if (status) element.dataset.status = status;
  else delete element.dataset.status;
  if (name) element.textContent = name.trim().split(/\s+/).slice(0, 2).map(part => [...part][0]).join('').toUpperCase();
  else element.replaceChildren(icon('people'));
  return element;
}

function statusOf(user) {
  return state.connection === 'online' ? state.presence[user] || 'offline' : 'offline';
}

function counterpart(row) {
  return row.sender === state.user ? row.recipient : row.sender;
}

function shortDate(value) {
  const then = new Date(value);
  return then.toDateString() === new Date().toDateString() ? clock.format(then) : date.format(then);
}

function renderDirectory() {
  if (!state || state.contact) return;
  const latest = new Map();
  for (const row of state.messages) latest.set(counterpart(row), row);
  const query = $('search').value.trim().toLocaleLowerCase('ru');
  const others = Object.keys(state.users).filter(id => id !== state.user);
  const people = others.filter(id => state.users[id].toLocaleLowerCase('ru').includes(query) &&
    (filter !== 'online' || statusOf(id) !== 'offline') && (filter !== 'unread' || unread.has(id)));
  people.sort((a, b) => (!directoryMode && (latest.get(b)?.id || 0) - (latest.get(a)?.id || 0)) ||
    state.users[a].localeCompare(state.users[b], 'ru'));
  const directory = $('directory');
  const scroll = directory.scrollTop;
  const focused = document.activeElement?.dataset.user;
  directory.replaceChildren();
  let previousGroup;
  for (const user of people) {
    const last = latest.get(user);
    const presence = statusOf(user);
    const group = last && !directoryMode ? 'Недавние' : 'Сотрудники';
    if (group !== previousGroup) directory.append(node('div', group, 'directory-label'));
    previousGroup = group;
    const button = node('button', '', user === contact ? 'person current' : 'person');
    button.dataset.user = user;
    button.setAttribute('aria-pressed', String(user === contact));
    button.title = `${state.users[user]} · ${statuses[presence]}`;
    const info = node('span', '', 'person-main');
    const preview = last && !directoryMode ? `${last.sender === state.user ? 'Вы: ' : ''}${last.text}` : statuses[presence];
    info.append(node('strong', state.users[user]), node('span', preview));
    const side = node('span', '', 'person-side');
    if (last && !directoryMode) side.append(node('span', shortDate(last.sent_at)));
    if (unread.has(user)) side.append(node('span', String(unread.get(user)), 'unread'));
    button.append(avatar(node('span'), user, presence), info, side);
    button.addEventListener('click', () => selectContact(user));
    directory.append(button);
    if (focused === user) button.focus({ preventScroll: true });
  }
  if (!people.length) {
    const label = query ? 'Никого не нашли' : filter === 'unread' ? 'Всё прочитано' : filter === 'online' ? 'Коллег пока нет в сети' : 'Список пока пуст';
    directory.append(node('div', label, 'empty-directory'));
  }
  directory.scrollTop = scroll;
  const online = others.filter(id => statusOf(id) !== 'offline').length;
  $('online-count').hidden = state.connection !== 'online';
  $('online-count').textContent = `${online} в сети`;
}

function renderChat() {
  const name = state.users[contact];
  const presence = statusOf(contact);
  $('contact-name').textContent = name || 'Личные сообщения';
  $('contact-status').textContent = name ? statuses[presence] : 'Рабочее пространство';
  $('contact-status').dataset.status = presence;
  avatar($('contact-avatar'), contact, name ? presence : null);
  $('compose').hidden = !name;
  const messages = state.messages.filter(row => counterpart(row) === contact);
  const lastId = messages.at(-1)?.id;
  if (paintedContact === contact && paintedLastId === lastId) return;
  const history = $('timeline');
  const pinnedToBottom = history.scrollHeight - history.scrollTop - history.clientHeight < 60;
  const shouldScroll = paintedContact !== contact || pinnedToBottom || messages.at(-1)?.sender === state.user;
  paintedContact = contact;
  paintedLastId = lastId;
  const previousScroll = history.scrollTop;
  if (!messages.length) {
    const empty = node('div', '', 'empty-chat');
    empty.append(avatar(node('span'), contact), node('h2', name ? 'Начните переписку' : 'Ваши рабочие диалоги'),
      node('p', name ? 'Напишите первое сообщение, чтобы начать личный диалог.' : 'Выберите сотрудника слева, чтобы открыть личный диалог.'));
    history.replaceChildren(empty);
    return;
  }
  const fragment = document.createDocumentFragment();
  let previousDay;
  for (const row of messages) {
    const sentAt = new Date(row.sent_at);
    const day = sentAt.toDateString();
    if (day !== previousDay) fragment.append(node('div', day === new Date().toDateString() ? 'Сегодня' : fullDate.format(sentAt), 'day'));
    previousDay = day;
    const bubble = node('article', '', row.sender === state.user ? 'message own' : 'message');
    const time = node('time', clock.format(sentAt));
    time.dateTime = row.sent_at;
    bubble.append(node('p', row.text), time);
    fragment.append(bubble);
  }
  history.replaceChildren(fragment);
  history.scrollTop = shouldScroll ? history.scrollHeight : previousScroll;
}

function updateComposer() {
  const input = $('message');
  input.disabled = sending.has(contact);
  $('emoji-toggle').disabled = input.disabled;
  $('send').disabled = input.disabled || !input.value.trim() || !contact;
  const attempt = attempts.get(contact);
  $('send-state').textContent = input.disabled ? 'Отправляем…' : attempt?.failed ? 'Не удалось отправить. Повторите попытку.' : '';
}

function selectContact(user, focus = true) {
  if (contact) drafts.set(contact, $('message').value);
  contact = user;
  unread.delete(user);
  $('message').value = drafts.get(user) || '';
  setEmoji(false);
  renderDirectory();
  renderChat();
  updateComposer();
  if (focus) $('message').focus();
}

function receive(next) {
  if (state && next.revision <= state.revision) return;
  if (state && !next.contact) {
    const previous = state.messages.at(-1)?.id || 0;
    for (const row of next.messages) {
      if (row.id > previous && row.recipient === next.user && !(row.sender === contact && document.hasFocus())) {
        unread.set(row.sender, (unread.get(row.sender) || 0) + 1);
      }
    }
  }
  state = next;
  document.body.classList.toggle('dialog', Boolean(state.contact));
  if (state.contact) contact = state.contact;
  else if (!contact && state.messages.length) contact = counterpart(state.messages.at(-1));
  $('self-name').textContent = state.users[state.user] || 'Мой профиль';
  $('status').value = state.status;
  $('connection').textContent = connections[state.connection];
  avatar($('self-avatar'), state.user, state.connection === 'online' ? state.status : 'offline');
  renderDirectory();
  renderChat();
  updateComposer();
}

function setEmoji(open) {
  $('emoji-panel').hidden = !open;
  $('emoji-toggle').setAttribute('aria-expanded', String(open));
}

function setFilter(next) {
  filter = next;
  document.querySelectorAll('[data-filter]').forEach(button => {
    button.classList.toggle('selected', button.dataset.filter === next);
    button.setAttribute('aria-pressed', String(button.dataset.filter === next));
  });
  renderDirectory();
}

function setDirectoryMode(enabled) {
  directoryMode = enabled;
  $('show-chats').classList.toggle('active', !enabled);
  $('show-directory').classList.toggle('active', enabled);
  document.querySelector('h1').textContent = enabled ? 'Сотрудники' : 'Сообщения';
  setFilter('all');
}

for (const emoji of ['😀', '😊', '😂', '👍', '👏', '🙏', '❤️', '🔥', '🎉', '👀', '✅', '🤔', '👋', '🙂', '🚀', '💡', '🤝', '🙌', '💬', '✨', '😅', '👌', '📌', '☕']) {
  const button = node('button', emoji);
  button.type = 'button';
  button.addEventListener('click', () => {
    const input = $('message');
    input.setRangeText(emoji, input.selectionStart, input.selectionEnd, 'end');
    setEmoji(false);
    input.focus();
    updateComposer();
  });
  $('emoji-grid').append(button);
}

$('message-form').addEventListener('submit', async event => {
  event.preventDefault();
  const recipient = contact;
  const input = $('message');
  const text = input.value.trim();
  if (!recipient || !text || sending.has(recipient)) return;
  if ([...text].length > 4000) {
    $('send-state').textContent = 'Максимум 4000 символов.';
    return;
  }
  let attempt = attempts.get(recipient);
  if (!attempt || attempt.text !== text) attempt = { text, nonce: crypto.randomUUID() };
  attempts.set(recipient, attempt);
  sending.add(recipient);
  setEmoji(false);
  updateComposer();
  let sent = false;
  try { sent = await api.send({ recipient, text, nonce: attempt.nonce }); } catch { /* Allow a retry. */ }
  sending.delete(recipient);
  if (sent) {
    attempts.delete(recipient);
    drafts.delete(recipient);
    if (contact === recipient) input.value = '';
  } else {
    attempt.failed = true;
  }
  updateComposer();
  if (contact === recipient) input.focus();
});

$('message').addEventListener('input', updateComposer);
$('message').addEventListener('keydown', event => {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    $('message-form').requestSubmit();
  }
});
$('emoji-toggle').addEventListener('click', () => setEmoji($('emoji-panel').hidden));
$('status').addEventListener('change', event => void api.setStatus(event.target.value));
$('search').addEventListener('input', renderDirectory);
$('show-chats').addEventListener('click', () => setDirectoryMode(false));
$('show-directory').addEventListener('click', () => setDirectoryMode(true));
$('quit').addEventListener('click', () => void api.quit());
document.querySelectorAll('[data-filter]').forEach(button => button.addEventListener('click', () => setFilter(button.dataset.filter)));
document.addEventListener('keydown', event => {
  if (event.key === 'Escape') setEmoji(false);
  if (!state?.contact && event.ctrlKey && event.code === 'KeyK') {
    event.preventDefault();
    $('search').focus();
  }
});
document.addEventListener('click', event => {
  if (!event.target.closest('#emoji-panel, #emoji-toggle')) setEmoji(false);
});
window.addEventListener('focus', () => {
  if (contact && unread.delete(contact)) renderDirectory();
});
api.subscribe(receive);
api.state().then(receive);
