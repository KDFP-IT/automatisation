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
      url: url.href,
      embed: Boolean(tool.embed) && url.origin === location.origin
    })
  }
  if (!tools.length) throw new Error('Список инструментов пуст')
  return tools
}
