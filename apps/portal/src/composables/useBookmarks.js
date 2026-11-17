import { onMounted, onBeforeUnmount, ref } from 'vue'

// Same job API, file limits and polling policy as the standalone checker.
export function useBookmarks() {
  const file = ref(null), busy = ref(false), error = ref(''), result = ref(null)
  const step = ref(1), progress = ref(''), start = ref(1), end = ref(''), scale = ref('1'), allowIncomplete = ref(false)
  let activeId = null, timer, disposed = false
  function clearResult() {
    result.value = null
    activeId = null
    sessionStorage.removeItem('pdfJob')
  }
  function selectFile(value) {
    if (busy.value || !value) return
    error.value = ''
    if (!value.name.toLowerCase().endsWith('.pdf')) { error.value = 'Выберите файл в формате PDF.'; return }
    if (!value.size) { error.value = 'Файл пустой. Выберите другой PDF.'; return }
    if (value.size > 200 * 1024 * 1024) { error.value = 'Размер файла превышает 200 МБ. Разделите документ на части.'; return }
    file.value = value
    clearResult()
    step.value = 1
  }
  function removeFile() {
    if (busy.value) return
    file.value = null
    error.value = ''
    clearResult()
    step.value = 1
  }
  async function json(response) {
    try { return await response.json() }
    catch { throw Error('Сервер вернул неожиданный ответ. Попробуйте ещё раз или обратитесь к администратору.') }
  }
  async function poll(id) {
    if (disposed || activeId !== id) return
    try {
      const response = await fetch(`/bookmarks/api/jobs/${encodeURIComponent(id)}`, { cache: 'no-store' })
      const data = await json(response)
      if (disposed || activeId !== id) return
      if (!response.ok) throw Error(data.error)
      error.value = ''
      if (data.status === 'done') { result.value = data; busy.value = false; step.value = 3; return }
      if (data.status === 'error') { busy.value = false; step.value = 1; sessionStorage.removeItem('pdfJob'); error.value = data.error; return }
      progress.value = data.status === 'queued' ? 'Документ в очереди' : 'Читаем штампы и закладки'
      timer = setTimeout(() => poll(id), 1500)
    } catch (problem) {
      if (disposed) return
      if (problem.message.includes('не найдено') || problem.message.includes('срок хранения')) {
        sessionStorage.removeItem('pdfJob'); busy.value = false; step.value = 1; error.value = problem.message; return
      }
      error.value = 'Связь с сервером прервалась. Проверим статус повторно через 5 секунд. Не загружайте файл заново.'
      timer = setTimeout(() => poll(id), 5000)
    }
  }
  async function submit() {
    if (!file.value || busy.value) return
    const payload = new FormData()
    payload.set('file', file.value)
    payload.set('start', String(start.value))
    payload.set('end', String(end.value ?? ''))
    payload.set('scale', String(scale.value))
    payload.set('allow_incomplete', allowIncomplete.value ? 'true' : 'false')
    error.value = ''; clearResult(); clearTimeout(timer)
    busy.value = true; step.value = 2; progress.value = 'Загружаем PDF на сервер'
    try {
      const response = await fetch('/bookmarks/api/jobs', { method: 'POST', body: payload, headers: { 'X-PDF-Service': '1' } })
      const data = await json(response)
      if (!response.ok) throw Error(data.error)
      activeId = data.id; sessionStorage.setItem('pdfJob', data.id)
      await poll(data.id)
    } catch (problem) {
      busy.value = false; step.value = 1
      error.value = problem.message === 'Failed to fetch' ? 'Не удалось загрузить файл. Проверьте подключение и повторите попытку.' : problem.message
    }
  }
  onMounted(() => {
    const id = sessionStorage.getItem('pdfJob')
    if (id) { activeId = id; busy.value = true; step.value = 2; poll(id) }
  })
  onBeforeUnmount(() => { disposed = true; clearTimeout(timer) })
  return { file, busy, error, result, step, progress, start, end, scale, allowIncomplete, selectFile, removeFile, submit }
}
