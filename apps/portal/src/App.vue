<script setup>
import { computed, onMounted, ref } from 'vue'
import { loadTools } from './tools'

const icons = {
  bookmarks: 'i-lucide-bookmark',
  signatures: 'i-lucide-file-signature',
  trench: 'i-lucide-ruler',
  kac: 'i-lucide-folder-cog'
}

const tools = ref([])
const error = ref('')
const loaded = ref(false)

const nav = computed(() => tools.value.map(tool => ({
  label: tool.title,
  to: '/' + tool.id,
  icon: icons[tool.id]
})))

onMounted(async () => {
  try {
    tools.value = await loadTools()
  } catch (problem) {
    error.value = problem.message
  } finally {
    loaded.value = true
  }
})
</script>

<template>
  <UApp>
  <div class="grid min-h-dvh grid-rows-[auto_minmax(0,1fr)] md:grid-cols-[248px_minmax(0,1fr)] md:grid-rows-none">
    <aside class="flex min-h-full flex-col gap-4 border-b border-default bg-default p-3 md:min-h-dvh md:border-b-0 md:border-r">
      <div class="flex items-center gap-3 px-2 pt-1">
        <img src="/brand/kdfp-logo.webp" alt="КДФП Инжиниринг" width="146" height="39">
      </div>
      <p class="-mb-2 hidden px-2 text-sm font-semibold text-highlighted md:block">Рабочее место</p>
      <nav v-if="nav.length" aria-label="Инструменты" class="grid gap-1.5">
        <RouterLink
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-3 rounded-xl border border-transparent px-3 py-2.5 text-sm font-medium text-muted transition-colors hover:border-brand-100 hover:bg-brand-50/60 hover:text-brand-700"
          active-class="border-brand-200 bg-brand-50 text-brand-700 shadow-sm"
        >
          <UIcon :name="item.icon" class="size-5 shrink-0" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
      <p v-else-if="loaded && error" class="px-2 text-sm text-error">{{ error }}</p>
    </aside>

    <main class="relative min-h-0 min-w-0">
      <RouterView v-if="tools.length" :tools="tools" />
      <div v-else class="flex h-full items-center justify-center p-6">
        <UAlert
          v-if="error"
          color="error"
          variant="subtle"
          icon="i-lucide-triangle-alert"
          title="Меню недоступно"
          :description="error"
          class="max-w-md"
        />
        <p v-else class="text-sm text-muted">Загружаю инструменты…</p>
      </div>
    </main>
  </div>
  </UApp>
</template>
