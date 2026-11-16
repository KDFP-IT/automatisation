const CATALOG = '/portal/tools.json'

export async function loadTools() {
  const response = await fetch(CATALOG, { cache: 'no-store' })
  if (!response.ok) throw new Error('Не удалось загрузить меню')

  const seen = new Set()
  const tools = []
  for (const tool of await response.json()) {
    if (!/^[a-z][a-z0-9-]*$/.test(tool.id) || !tool.title || !tool.url || seen.has(tool.id)) {
      throw new Error('Проверьте список инструментов')
    }
    const url = new URL(tool.url, location.origin)
    if (!['http:', 'https:'].includes(url.protocol)) throw new Error('Проверьте адрес инструмента')
    seen.add(tool.id)
    tools.push({
      id: tool.id,
      title: tool.title,
      embed: Boolean(tool.embed) && url.origin === location.origin
    })
  }
  if (!tools.length) throw new Error('Список инструментов пуст')
  return tools
}

async function readJson(response) {
  try {
    return await response.json()
  } catch {
    return {}
  }
}

export async function loadAuth() {
  const modeResponse = await fetch('/auth/mode', { cache: 'no-store' })
  const mode = modeResponse.ok ? (await readJson(modeResponse)).mode ?? 'local' : 'local'
  const meResponse = await fetch('/auth/me', { cache: 'no-store' })
  if (meResponse.status === 401) return { mode, user: null, tools: [] }
  if (!meResponse.ok) throw new Error('Не удалось проверить сессию')
  const me = await readJson(meResponse)
  return { mode, user: me.user ?? null, displayName: me.display_name ?? me.user ?? null, tools: me.tools ?? [], admin: Boolean(me.admin) }
}

export async function login(login, password) {
  const response = await fetch('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ login, password })
  })
  const body = await readJson(response)
  if (!response.ok) {
    throw new Error(
      body.error === 'bad_credentials'
        ? 'Неверный логин или пароль'
        : body.error === 'no_portal_access'
          ? 'Учётная запись не состоит в группе доступа к порталу'
          : body.error === 'ad_unreachable'
            ? 'Контроллер AD недоступен, попробуйте позже'
            : body.error === 'too_many_attempts'
              ? 'Слишком много попыток, подождите 5 минут'
              : 'Вход не удался'
    )
  }
  return { user: body.user ?? null, displayName: body.display_name ?? body.user ?? null, tools: body.tools ?? [], admin: Boolean(body.admin) }
}

export async function logout() {
  await fetch('/auth/logout', { method: 'POST' })
}
