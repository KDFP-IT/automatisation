import { ref } from 'vue'

const api = '/kac/api'
const pause = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds))

async function request(url, options) {
  const response = await fetch(url, options)
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(data.error ?? (response.status === 413
      ? 'Объём загрузки превышает 200 МБ.'
      : 'Портал не ответил. Попробуйте ещё раз.'))
  }
  return data
}

function upload(url, body, onProgress) {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest()
    request.open('POST', url)
    request.responseType = 'json'
    request.upload.addEventListener('progress', event => {
      if (event.lengthComputable) onProgress(event.loaded / event.total)
    })
    request.addEventListener('load', () => {
      const data = request.response ?? {}
      if (request.status >= 200 && request.status < 300) {
        resolve(data)
      } else {
        reject(new Error(data.error ?? (request.status === 413
          ? 'Объём загрузки превышает 200 МБ.'
          : 'Портал не ответил. Попробуйте ещё раз.')))
      }
    })
    request.addEventListener('error', () => reject(new Error('Портал не ответил. Попробуйте ещё раз.')))
    request.send(body)
  })
}

export function loadHealth() {
  return request(api + '/health')
}

export function useKacJob() {
  const busy = ref(false)
  const progress = ref(0)
  const stage = ref('')
  const job = ref(null)

  async function run({ docx, xlsx, offers }) {
    busy.value = true
    progress.value = 0
    stage.value = 'upload'
    job.value = null
    try {
      const body = new FormData()
      if (docx) body.append('docx', docx)
      if (xlsx) body.append('xlsx', xlsx)
      for (const { file, path } of offers) body.append('offer', file, path)
      const { id } = await upload(`${api}/jobs`, body, fraction => {
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
