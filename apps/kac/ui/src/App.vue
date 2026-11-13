<script setup>
import { computed, onMounted, ref } from 'vue'
import { useToast } from '@nuxt/ui/composables/useToast'
import { analyse, collectDrop, emptyAnalysis, filesFromInput } from './composables/useOffers'
import { loadHealth, useKacJob } from './composables/useKacJob'

const foldersInput = ref()

const docxFile = ref()
const analysis = ref(emptyAnalysis())
const configuredTemplate = ref()
const available = ref(true)
const dragActive = ref(false)
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
  <UApp>
    <main class="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6 sm:py-12">
      <h1 class="text-3xl font-bold tracking-[-0.035em] text-highlighted sm:text-4xl">Собрать КАЦ</h1>
      <p class="mt-2 max-w-2xl text-muted">
        Загрузите основной документ и коммерческие предложения, распределённые по разделам.
      </p>

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
          class="mt-6 grid gap-6 rounded-xl border border-default bg-default p-5 sm:p-7"
          @submit.prevent="submit"
        >
          <section>
            <h2 class="flex items-center gap-3 text-lg font-semibold text-highlighted">
              <span class="flex size-6 shrink-0 items-center justify-center rounded-full bg-elevated text-xs font-semibold text-toned ring-1 ring-default">1</span>
              Основной документ
            </h2>

            <UFileUpload
              v-model="docxFile"
              accept=".docx"
              icon="vscode-icons:file-type-word"
              label="DOCX проекта"
              description="Выберите файл или перетащите его сюда"
              position="inside"
              layout="list"
              :file-image="false"
              class="mt-3 min-h-24"
              :ui="{
                base: sourceDocx
                  ? 'px-4 py-3 border-solid transition-colors hover:border-accented hover:bg-zinc-100'
                  : 'px-4 py-3 transition-colors hover:border-accented hover:bg-zinc-100',
                label: 'mt-2 text-base font-semibold',
                description: 'text-sm',
                fileName: 'text-sm font-medium text-highlighted',
                fileSize: 'text-xs'
              }"
            />
            <p v-if="configuredTemplate && !sourceDocx" class="mt-2 text-sm text-muted">
              Без выбранного файла будет использован серверный шаблон «{{ configuredTemplate }}».
            </p>
          </section>

          <USeparator />

          <section>
            <h2 class="flex items-center gap-3 text-lg font-semibold text-highlighted">
              <span class="flex size-6 shrink-0 items-center justify-center rounded-full bg-elevated text-xs font-semibold text-toned ring-1 ring-default">2</span>
              Коммерческие предложения
            </h2>

            <div
              class="mt-3 grid justify-items-center rounded-xl border-2 border-dashed px-6 py-8 text-center transition-colors"
              :class="dragActive ? 'border-primary bg-primary/5' : 'border-default hover:border-accented hover:bg-zinc-50'"
              @dragenter.prevent="dragActive = true"
              @dragover.prevent="dragActive = true"
              @dragleave.prevent="dragActive = false"
              @drop.prevent="onDrop"
            >
              <span class="flex size-12 items-center justify-center rounded-xl border border-default bg-elevated">
                <UIcon name="i-lucide-folder-up" class="size-6 text-muted" />
              </span>
              <p class="mt-3 text-lg font-semibold text-highlighted">Добавьте папки разделов</p>
              <p class="mt-1 text-sm text-muted">Выберите общую папку или несколько папок с PDF-файлами</p>
              <UButton
                type="button"
                color="neutral"
                variant="outline"
                icon="i-lucide-folder-open"
                label="Выбрать папки"
                class="mt-4"
                @click="foldersInput?.click()"
              />
              <p class="mt-3 text-xs text-dimmed">Или перетащите папки сюда</p>
              <input
                ref="foldersInput"
                type="file"
                webkitdirectory
                multiple
                class="sr-only"
                @change="onFolders"
              >
            </div>

            <UButton
              type="button"
              variant="link"
              color="neutral"
              size="sm"
              class="mt-2 px-0 text-muted underline underline-offset-4"
              label="Требуемая структура папок и пример их названий"
              @click="structureOpen = true"
            />

            <template v-if="hasSelection">
              <div class="mt-4 flex flex-wrap items-center justify-between gap-2">
                <p class="text-sm text-muted">
                  Найдено разделов: <b class="text-highlighted">{{ analysis.totals.sections }}</b> ·
                  PDF: <b class="text-highlighted">{{ analysis.totals.pdfs }}</b>
                </p>
                <UButton
                  type="button"
                  color="neutral"
                  variant="ghost"
                  size="xs"
                  icon="i-lucide-x"
                  label="Очистить"
                  @click="clearSelection"
                />
              </div>
              <div class="mt-2 rounded-lg border border-default p-2">
                <UTree :items="treeItems" :get-key="item => item.key" />
              </div>
            </template>
          </section>

          <USeparator />

          <section
            v-if="analysis.ignored.length || analysis.skipped.length"
            class="rounded-xl border border-default bg-elevated p-4"
          >
            <div class="flex items-start gap-3">
              <UIcon name="i-lucide-info" class="mt-0.5 size-4 shrink-0 text-muted" />
              <div class="min-w-0">
                <p class="text-sm font-medium text-highlighted">Не попадёт в сборку</p>
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

          <UButton
            type="submit"
            block
            size="lg"
            trailing-icon="i-lucide-arrow-right"
            label="Собрать КАЦ"
          />
          <p v-if="!available" class="text-sm text-warning">Обработчик КАЦ недоступен.</p>
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

      <UModal v-model:open="structureOpen" title="Требуемая структура папок">
        <template #body>
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
  </UApp>
</template>
