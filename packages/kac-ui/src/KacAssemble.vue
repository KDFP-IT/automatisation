<script setup>
import { computed, onMounted, ref } from 'vue'
// useToast, UApp, UIcon и остальные Nuxt-компоненты резолвит хост через auto-import.
import { analyse, collectDrop, emptyAnalysis, filesFromInput } from './composables/useOffers'
import { loadHealth, useKacJob } from './composables/useKacJob'

const foldersInput = ref()
const docxInput = ref()

const docxFile = ref()
const analysis = ref(emptyAnalysis())
const configuredTemplate = ref()
const available = ref(true)
const dragActive = ref(false)
const docxDragActive = ref(false)
const structureOpen = ref(false)
const compositionOpen = ref(false)
const problems = ref([])
const error = ref('')
const phase = ref('form')
const result = ref()

const toast = useToast()
const { progress, stage, job, run } = useKacJob()

const radius = 52
const circumference = 2 * Math.PI * radius
const dashoffset = computed(() => circumference * (1 - progress.value / 100))

const sourceDocx = computed(() => docxFile.value)
const hasSelection = computed(() => Boolean(analysis.value.totals.pdfs))
const canSubmit = computed(() => Boolean(
  available.value
  && (sourceDocx.value || configuredTemplate.value)
  && analysis.value.totals.pdfs
  && !analysis.value.issues.length
))
const ignoredTotal = computed(() => (
  analysis.value.ignored.reduce((sum, group) => sum + group.count, 0)
  + analysis.value.skipped.length
))

const stageLabel = computed(() => {
  if (stage.value === 'upload') return 'Загружаю файлы'
  if (stage.value === 'queued') return 'Задача в очереди'
  if (stage.value === 'exporting') return 'Собираю PDF и оглавление'
  if (stage.value === 'rendering') {
    const done = job.value?.sections_done ?? 0
    const total = job.value?.sections_total ?? analysis.value.totals.sections
    return total ? `Обрабатываю разделы: ${done} из ${total}` : 'Обрабатываю разделы'
  }
  return 'Собираю комплект'
})

const treeItems = computed(() => analysis.value.sections.map(node => ({
  key: `section-${node.number}`,
  label: node.folder,
  icon: 'i-lucide-folder',
  defaultExpanded: false,
  children: node.files.map(file => ({
    key: `${node.number}:${file.path}`,
    label: `${file.name} · ${formatSize(file.size)}`,
    icon: 'i-lucide-file-text'
  }))
})))

function formatSize(bytes) {
  if (!bytes) return ''
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} МБ`
  return `${Math.max(1, Math.ceil(bytes / 1024))} КБ`
}

function onFolders(event) {
  apply(filesFromInput(event.target))
}

function onDocx(event) {
  const file = event.target.files?.[0]
  if (file) docxFile.value = file
  event.target.value = ''
}

function onDocxDrop(event) {
  docxDragActive.value = false
  const file = Array.from(event.dataTransfer?.files ?? []).find(entry => /\.docx$/i.test(entry.name))
  if (file) {
    docxFile.value = file
    error.value = ''
  } else {
    error.value = 'Перетащите файл проекта в формате DOCX.'
  }
}

function clearDocx() {
  docxFile.value = undefined
  result.value = undefined
}

function apply(files) {
  analysis.value = files.length ? analyse(files) : emptyAnalysis()
  if (analysis.value.docx && !docxFile.value) docxFile.value = analysis.value.docx
  result.value = undefined
  problems.value = []
}

function clearSelection() {
  analysis.value = emptyAnalysis()
  docxFile.value = undefined
  result.value = undefined
  problems.value = []
  error.value = ''
}

async function onDrop(event) {
  dragActive.value = false
  try {
    apply(await collectDrop(event.dataTransfer))
  } catch {
    error.value = 'Не удалось прочитать папки. Выберите их через кнопку загрузки.'
  }
}

function validate() {
  const found = []
  if (!sourceDocx.value && !configuredTemplate.value) found.push('Выберите основной документ DOCX.')
  if (!analysis.value.totals.pdfs) found.push('В выбранных папках нет PDF в папках вида «Раздел 1 - Название».')
  found.push(...analysis.value.issues)
  return found
}

function download(kind) {
  window.location.assign(`/kac/api/jobs/${result.value.id}/${kind}`)
}

function openPdf() {
  window.open(`/kac/api/jobs/${result.value.id}/pdf?inline=1`, '_blank', 'noopener')
}

function notifyDone() {
  toast.add({
    title: 'КАЦ собран',
    description: `Разделов: ${result.value.sections} · страниц КП: ${result.value.pages}`,
    color: 'success',
    icon: 'i-lucide-circle-check',
    duration: 15000,
    actions: [
      { label: 'Скачать PDF', icon: 'i-lucide-download', onClick: () => download('pdf') },
      { label: 'Скачать ZIP', icon: 'i-lucide-download', onClick: () => download('zip') }
    ]
  })
}

async function submit() {
  problems.value = validate()
  if (problems.value.length) return
  error.value = ''
  phase.value = 'progress'
  try {
    result.value = await run({
      docx: sourceDocx.value,
      offers: analysis.value.sections.flatMap(node => node.files)
    })
    phase.value = 'done'
    notifyDone()
  } catch (problem) {
    error.value = problem.message
    phase.value = 'form'
  }
}

function reset() {
  result.value = undefined
  error.value = ''
  phase.value = 'form'
}

onMounted(async () => {
  try {
    const health = await loadHealth()
    available.value = health.available
    configuredTemplate.value = health.template ?? undefined
    if (!health.available) error.value = 'Обработчик КАЦ недоступен. Обратитесь к администратору портала.'
  } catch (problem) {
    error.value = problem.message
  }
})
</script>

<template>
    <main class="mx-auto w-full max-w-[1440px] px-4 py-8 sm:px-8 sm:py-10 xl:px-12">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 class="text-3xl font-bold tracking-[-0.035em] text-highlighted sm:text-4xl">Собрать КАЦ</h1>
          <p class="mt-2 max-w-3xl text-muted">
            Загрузите основной документ и коммерческие предложения, распределённые по разделам.
          </p>
        </div>
        <UButton
          type="button"
          color="neutral"
          variant="outline"
          size="lg"
          icon="i-lucide-info"
          label="Как это работает?"
          @click="structureOpen = true"
        />
      </div>

      <template v-if="phase === 'form'">
        <UAlert
          v-if="error"
          class="mt-6"
          color="error"
          variant="subtle"
          icon="i-lucide-triangle-alert"
          title="Сборка не запущена"
          :description="error"
        />

        <form
          class="mt-7 rounded-2xl border border-default bg-default p-5 sm:p-7"
          @submit.prevent="submit"
        >
          <div class="grid gap-7 lg:grid-cols-2 lg:divide-x lg:divide-default">
            <section class="lg:pr-7">
              <h2 class="flex items-center gap-3 text-xl font-semibold text-highlighted">
                <span class="flex size-8 shrink-0 items-center justify-center rounded-full bg-elevated text-sm font-semibold ring-1 ring-default">1</span>
                Основной документ
              </h2>
              <p v-if="!sourceDocx" class="ml-11 mt-1 text-sm text-muted">Загрузите DOCX проекта</p>

              <div v-if="sourceDocx" class="mt-5 flex min-h-28 items-center justify-between gap-4 rounded-xl border border-default px-5 py-4">
                <div class="flex min-w-0 items-center gap-4">
                  <span class="flex size-14 shrink-0 items-center justify-center rounded-xl border border-blue-200 bg-blue-50">
                    <UIcon name="vscode-icons:file-type-word" class="size-9" />
                  </span>
                  <div class="min-w-0">
                    <p class="truncate font-medium text-highlighted">{{ sourceDocx.name }}</p>
                    <p class="mt-2 flex items-center gap-2 text-sm font-medium text-highlighted">
                      <UIcon name="i-lucide-circle-check" class="size-5 text-success" />
                      Загружен
                    </p>
                  </div>
                </div>
                <UButton type="button" color="neutral" variant="ghost" icon="i-lucide-x" aria-label="Удалить основной документ" @click="clearDocx" />
              </div>
              <div
                v-else
                class="mt-5 flex min-h-64 items-center justify-center rounded-xl border-2 border-dashed px-6 py-8 transition-colors"
                :class="docxDragActive ? 'border-primary bg-primary/5' : 'border-default hover:border-accented hover:bg-zinc-50'"
                @dragenter.prevent="docxDragActive = true"
                @dragover.prevent="docxDragActive = true"
                @dragleave.prevent="docxDragActive = false"
                @drop.prevent="onDocxDrop"
              >
                <div class="grid justify-items-center text-center">
                  <span class="flex size-14 items-center justify-center rounded-xl border border-blue-200 bg-blue-50">
                    <UIcon name="vscode-icons:file-type-word" class="size-9" />
                  </span>
                  <p class="mt-4 text-xl font-semibold text-highlighted">Перетащите DOCX сюда</p>
                  <UButton type="button" color="neutral" variant="outline" icon="i-lucide-file-text" label="Выбрать файл" class="mt-4" @click="docxInput?.click()" />
                  <p class="mt-4 text-sm text-muted">DOCX, не более 50 МБ</p>
                </div>
                <input ref="docxInput" type="file" accept=".docx" class="sr-only" @change="onDocx">
              </div>
              <p v-if="configuredTemplate && !sourceDocx" class="mt-2 text-sm text-muted">
                Без выбранного файла будет использован серверный шаблон «{{ configuredTemplate }}».
              </p>
            </section>

            <section class="lg:pl-7">
              <h2 class="flex items-center gap-3 text-xl font-semibold text-highlighted">
                <span class="flex size-8 shrink-0 items-center justify-center rounded-full bg-elevated text-sm font-semibold ring-1 ring-default">2</span>
                Коммерческие предложения
              </h2>
              <p v-if="!hasSelection" class="ml-11 mt-1 text-sm text-muted">Добавьте общую папку или папки разделов</p>

              <div
                v-if="!hasSelection"
                class="mt-5 grid min-h-64 justify-items-center content-center rounded-xl border-2 border-dashed px-6 py-8 text-center transition-colors"
                :class="dragActive ? 'border-primary bg-primary/5' : 'border-default hover:border-accented hover:bg-zinc-50'"
                @dragenter.prevent="dragActive = true"
                @dragover.prevent="dragActive = true"
                @dragleave.prevent="dragActive = false"
                @drop.prevent="onDrop"
              >
                <span class="flex size-14 items-center justify-center rounded-xl border border-default bg-elevated">
                  <UIcon name="i-lucide-folder-up" class="size-7 text-amber-500" />
                </span>
                <p class="mt-4 text-xl font-semibold text-highlighted">Перетащите папки сюда</p>
                <UButton type="button" color="neutral" variant="outline" icon="i-lucide-folder-open" label="Выбрать папки" class="mt-4" @click="foldersInput?.click()" />
                <p class="mt-4 text-sm text-muted">Папки с PDF-файлами по разделам</p>
              </div>
              <div v-else class="mt-5 flex min-h-28 items-center justify-between gap-4 rounded-xl border border-default px-5 py-4">
                <div>
                  <p class="text-sm text-muted">Найдено разделов: <b class="text-highlighted">{{ analysis.totals.sections }}</b> · PDF: <b class="text-highlighted">{{ analysis.totals.pdfs }}</b></p>
                  <p class="mt-2 flex items-center gap-2 text-sm font-medium text-highlighted"><UIcon name="i-lucide-circle-check" class="size-5 text-success" /> Структура распознана</p>
                </div>
                <UButton type="button" color="neutral" variant="outline" icon="i-lucide-folder-open" label="Изменить папки" @click="foldersInput?.click()" />
              </div>
              <input ref="foldersInput" type="file" webkitdirectory multiple class="sr-only" @change="onFolders">
            </section>
          </div>

          <template v-if="hasSelection">
            <USeparator class="my-7" />
            <section>
              <h2 class="text-xl font-semibold text-highlighted">Разделы и документы</h2>
              <div class="mt-4 overflow-hidden rounded-xl border border-default">
                <details v-for="node in analysis.sections" :key="node.number" class="group border-b border-default last:border-b-0">
                  <summary class="flex list-none items-center gap-3 px-5 py-3 hover:bg-elevated">
                    <UIcon name="i-lucide-folder" class="size-5 text-muted" />
                    <span class="min-w-0 flex-1 truncate font-medium text-highlighted">{{ node.folder }}</span>
                    <span class="w-24 text-sm text-muted">{{ node.files.length }} PDF</span>
                    <span class="flex w-32 items-center gap-2 text-sm"><UIcon name="i-lucide-circle-check" class="size-5 text-success" /> Распознан</span>
                    <UIcon name="i-lucide-chevron-down" class="size-5 text-muted transition-transform group-open:rotate-180" />
                  </summary>
                  <ul class="border-t border-default bg-elevated px-12 py-2">
                    <li v-for="file in node.files" :key="file.path" class="flex items-center gap-2 py-1.5 text-sm text-muted">
                      <UIcon name="i-lucide-file-text" class="size-4" /> {{ file.name }} · {{ formatSize(file.size) }}
                    </li>
                  </ul>
                </details>
              </div>
            </section>
          </template>

          <section
            v-if="analysis.ignored.length || analysis.skipped.length"
            class="mt-6 rounded-xl border border-default bg-elevated p-4"
          >
            <div class="flex items-start gap-3">
              <UIcon name="i-lucide-info" class="mt-0.5 size-4 shrink-0 text-muted" />
              <div class="min-w-0">
                <p class="text-sm font-medium text-highlighted">Не попадёт в сборку · {{ ignoredTotal }} файлов</p>
                <ul class="mt-2 space-y-1 text-sm">
                  <li v-for="group in analysis.ignored" :key="group.folder">
                    <span class="break-all text-default">{{ group.folder }}</span>
                    <span class="text-muted"> — {{ group.count }} PDF в подпапке</span>
                  </li>
                  <li v-for="section in analysis.skipped" :key="section.number">
                    <span class="text-default">{{ section.folder }}</span>{{ ' ' }}
                    <span class="text-muted">— раздел пропущен{{ section.nested.length ? `: PDF только в подпапке «${section.nested.join('», «')}»` : '' }}</span>
                  </li>
                </ul>
                <p class="mt-2 text-xs text-dimmed">
                  PDF читаются только из папки раздела; подпапки «арх», «архив», «Картинки» не используются.
                </p>
              </div>
            </div>
          </section>

          <UAlert
            v-if="problems.length"
            class="mt-6"
            color="error"
            variant="subtle"
            icon="i-lucide-triangle-alert"
            title="Проверьте входные данные"
          >
            <template #description>
              <ul class="list-disc space-y-1 pl-4">
                <li v-for="problem in problems" :key="problem">{{ problem }}</li>
              </ul>
            </template>
          </UAlert>

          <USeparator class="my-7" />
          <div class="flex flex-wrap items-center justify-between gap-4">
            <div class="flex items-center gap-3">
              <UIcon :name="canSubmit ? 'i-lucide-circle-check' : 'i-lucide-info'" class="size-6" :class="canSubmit ? 'text-success' : 'text-muted'" />
              <div>
                <p class="font-semibold text-highlighted">{{ canSubmit ? 'Готово к сборке' : 'Добавьте документы для начала сборки' }}</p>
                <p v-if="canSubmit" class="text-sm text-muted">{{ analysis.totals.sections }} разделов · {{ analysis.totals.pdfs }} PDF</p>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <UButton v-if="hasSelection || sourceDocx" type="button" color="neutral" variant="ghost" label="Очистить" @click="clearSelection" />
              <UButton
                type="submit"
                size="lg"
                trailing-icon="i-lucide-arrow-right"
                label="Собрать КАЦ"
                :disabled="!canSubmit"
                :class="!canSubmit ? 'disabled:bg-zinc-400 disabled:text-white disabled:opacity-100 disabled:ring-0' : ''"
              />
            </div>
          </div>
          <p v-if="!available" class="mt-3 text-sm text-warning">Обработчик КАЦ недоступен.</p>
        </form>
      </template>

      <section v-else-if="phase === 'progress'" class="mt-6 rounded-xl border border-default bg-default px-6 py-10 text-center">
        <div class="relative mx-auto size-36">
          <svg viewBox="0 0 120 120" class="size-36 -rotate-90" aria-hidden="true">
            <circle cx="60" cy="60" :r="radius" fill="none" stroke="var(--ui-border)" stroke-width="8" />
            <circle
              cx="60"
              cy="60"
              :r="radius"
              fill="none"
              stroke="var(--ui-primary)"
              stroke-width="8"
              stroke-linecap="round"
              :stroke-dasharray="circumference"
              :stroke-dashoffset="dashoffset"
              class="transition-[stroke-dashoffset] duration-300 ease-out"
            />
          </svg>
          <span class="absolute inset-0 flex items-center justify-center text-2xl font-semibold text-highlighted">{{ progress }}%</span>
        </div>
        <p class="mt-5 font-medium text-highlighted">{{ stageLabel }}</p>
        <p class="mt-1 text-sm text-muted">Сборка идёт на сервере — не закрывайте вкладку.</p>
      </section>

      <section v-else class="mt-6 rounded-xl border border-default bg-default p-6">
        <div class="flex items-center gap-3">
          <span class="flex size-10 shrink-0 items-center justify-center rounded-full bg-success/10 text-success">
            <UIcon name="i-lucide-circle-check" class="size-5" />
          </span>
          <div class="min-w-0">
            <h2 class="text-lg font-semibold text-highlighted">Готово</h2>
            <p class="text-sm text-muted">Разделов: {{ result.sections }} · страниц КП: {{ result.pages }}</p>
          </div>
        </div>

        <ul class="mt-5 divide-y divide-default overflow-hidden rounded-lg border border-default">
          <li class="flex flex-wrap items-center gap-3 p-3">
            <span class="flex size-9 shrink-0 items-center justify-center rounded-lg bg-red-50 text-red-600">
              <UIcon name="i-lucide-file-text" class="size-4" />
            </span>
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-medium text-highlighted">КАЦ — готовый комплект.pdf</p>
              <p class="text-xs text-muted">PDF · готов к скачиванию</p>
            </div>
            <div class="flex gap-2">
              <UButton size="sm" color="neutral" variant="outline" label="Открыть" @click="openPdf" />
              <UButton size="sm" icon="i-lucide-download" label="Скачать" @click="download('pdf')" />
            </div>
          </li>
          <li class="flex flex-wrap items-center gap-3 p-3">
            <span class="flex size-9 shrink-0 items-center justify-center rounded-lg bg-elevated text-toned ring-1 ring-default">
              <UIcon name="i-lucide-file-archive" class="size-4" />
            </span>
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-medium text-highlighted">КАЦ — картинки по разделам.zip</p>
              <p class="text-xs text-muted">ZIP · готов к скачиванию</p>
            </div>
            <UButton size="sm" icon="i-lucide-download" label="Скачать" @click="download('zip')" />
          </li>
        </ul>

        <div class="mt-5 flex flex-wrap gap-2">
          <UButton color="neutral" variant="outline" icon="i-lucide-files" label="Показать состав" @click="compositionOpen = true" />
          <UButton color="neutral" variant="ghost" label="Собрать ещё" @click="reset" />
        </div>
      </section>

      <UModal v-model:open="structureOpen" title="Как собрать КАЦ" description="Подготовьте документы в два шага" :ui="{ content: 'sm:max-w-3xl' }">
        <template #body>
          <div class="grid gap-3">
            <div class="flex items-center gap-4 rounded-xl border border-default p-4">
              <span class="flex size-8 shrink-0 items-center justify-center rounded-full ring-1 ring-default">1</span>
              <span class="flex size-12 shrink-0 items-center justify-center rounded-xl border border-default"><UIcon name="i-lucide-file-text" class="size-6" /></span>
              <div><h3 class="font-semibold text-highlighted">Загрузите основной документ</h3><p class="text-sm text-muted">Выберите один файл проекта в формате DOCX, не более 50 МБ.</p></div>
            </div>
            <div class="flex items-center gap-4 rounded-xl border border-default p-4">
              <span class="flex size-8 shrink-0 items-center justify-center rounded-full ring-1 ring-default">2</span>
              <span class="flex size-12 shrink-0 items-center justify-center rounded-xl border border-default"><UIcon name="i-lucide-folder-open" class="size-6" /></span>
              <div><h3 class="font-semibold text-highlighted">Добавьте коммерческие предложения</h3><p class="text-sm text-muted">Выберите общую папку или несколько папок разделов с PDF-файлами.</p></div>
            </div>
          </div>
          <h3 class="mt-6 text-lg font-semibold text-highlighted">Требуемая структура папок</h3>
          <pre class="overflow-x-auto rounded-lg bg-elevated p-3 text-xs leading-relaxed text-default">Проект/
├─ Основной документ.docx
├─ Раздел 1 - Контактная сеть/
│  ├─ КП 1.1 Транском.pdf
│  └─ КП 1.2 Арксеть.pdf
└─ Раздел 2 - Наружное освещение/
   └─ КП 1.1 ЭТМ.pdf</pre>
          <ul class="mt-4 list-disc space-y-1 pl-5 text-sm text-muted">
            <li>Папка раздела называется «Раздел N - Название».</li>
            <li>PDF лежат прямо в папке раздела; подпапки «арх» и «Картинки» не учитываются.</li>
            <li>Имя файла начинается с номера КП: «КП 1.1 …». Номера в разделе не повторяются.</li>
            <li>Разделы без PDF пропускаются и перечисляются отдельно.</li>
          </ul>
        </template>
      </UModal>

      <UModal v-model:open="compositionOpen" title="Состав комплекта">
        <template #body>
          <p class="text-sm text-muted">
            Разделов: {{ result?.sections }} · страниц КП: {{ result?.pages }}
          </p>
          <div class="mt-3 rounded-lg border border-default p-2">
            <UTree :items="treeItems" :get-key="item => item.key" />
          </div>
        </template>
      </UModal>
    </main>
</template>
