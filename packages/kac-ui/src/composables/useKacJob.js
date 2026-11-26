import { ref } from 'vue'

const api = '/kac/api'
const pause = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds))

const chunkBytes = 512 * 1024

async function request(url, options) {
  const response = await fetch(url, options)
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    const error = new Error(data.error ?? (response.status === 413
      ? 'Прокси отклонил часть загрузки.'
      : 'Портал не ответил. Попробуйте ещё раз.'))
    error.status = response.status
    throw error
  }
  return data
}

async function postPart(url, body) {
  // A lost acknowledgment must not append the same data or start a second job.
  for (let attempt = 0; ; attempt++) {
    try {
      return await request(url, { method: 'POST', body })
    } catch (error) {
      if (attempt >= 2 || (error.status && error.status < 500)) throw error
      await pause(500 * (attempt + 1))
    }
  }
}

async function upload(docx, offers, onProgress) {
  const files = offers.map(({ file, path }) => ({ file, path, kind: 'offer' }))
  if (docx) files.unshift({ file: docx, path: docx.name, kind: 'docx' })
  const total = files.reduce((sum, entry) => sum + entry.file.size, 0)
  const { id } = await request(`${api}/uploads`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ files: files.length })
  })
  const base = `${api}/uploads/${id}`
  let sent = 0
  for (const [index, { file, path, kind }] of files.entries()) {
    let offset = 0
    do {
      const chunk = file.slice(offset, offset + chunkBytes)
      const body = new FormData()
      body.append('kind', kind)
      body.append('index', String(index))
      body.append('offset', String(offset))
      body.append('total', String(file.size))
      body.append('chunk', chunk, path)
      await postPart(`${base}/chunk`, body)
      offset += chunk.size
      sent += chunk.size
      onProgress(total ? sent / total : 1)
    } while (offset < file.size)
  }
  return postPart(`${base}/finish`)
}

export function loadHealth() {
  return request(api + '/health')
}

export function useKacJob() {
  const busy = ref(false)
  const progress = ref(0)
  const stage = ref('')
  const job = ref(null)

  async function run({ docx, offers }) {
    busy.value = true
    progress.value = 0
    stage.value = 'upload'
    job.value = null
    try {
      const { id } = await upload(docx, offers, fraction => {
        progress.value = Math.round(fraction * 15)
      })
      stage.value = 'queued'
      progress.value = Math.max(progress.value, 15)
      let current = { status: 'queued', progress: 0.15 }
      do {
        await pause(1200)
        current = await request(`${api}/jobs/${id}`)
        if (current.status === 'error') throw new Error(current.error)
        job.value = current
        stage.value = current.stage ?? (current.status === 'queued' ? 'queued' : 'rendering')
        progress.value = Math.max(progress.value, Math.min(99, Math.round((current.progress ?? 0.15) * 100)))
      } while (current.status !== 'done')
      progress.value = 100
      stage.value = 'done'
      return { ...current, id }
    } finally {
      busy.value = false
    }
  }

  return { busy, progress, stage, job, run }
}
