<script setup>
import { computed, onMounted, ref } from 'vue'
import { loadAuth, loadTools, login, logout } from './tools'

const icons = {
  bookmarks: 'i-lucide-bookmark',
  signatures: 'i-lucide-file-signature',
  trench: 'i-lucide-ruler',
  kac: 'i-lucide-folder-cog'
}

const session = ref({ mode: 'local', user: null, tools: [] })
const catalog = ref([])
const error = ref('')
const loaded = ref(false)

const authFailed = ref(false)
const authBusy = ref(false)
const authError = ref('')
const form = ref({ login: '', password: '' })

const tools = computed(() => {
  const allowed = new Set(session.value.tools)
  return catalog.value.filter(tool => allowed.has(tool.id))
})

const nav = computed(() => tools.value.map(tool => ({
  label: tool.title,
  to: '/' + tool.id,
  icon: icons[tool.id]
})))

async function refresh() {
  loaded.value = false
  error.value = ''
  try {
    session.value = await loadAuth()
    if (session.value.user) catalog.value = await loadTools()
  } catch (problem) {
    error.value = problem.message
  } finally {
    loaded.value = true
  }
}

onMounted(refresh)

async function submit() {
  if (authBusy.value) return
  authBusy.value = true
  authError.value = ''
  try {
    const me = await login(form.value.login.trim(), form.value.password)
    form.value.password = ''
    authFailed.value = false
    session.value = { mode: session.value.mode, ...me }
    catalog.value = await loadTools()
  } catch (problem) {
    authFailed.value = true
    authError.value = problem.message
    form.value.password = ''
  } finally {
    authBusy.value = false
  }
}

async function signOut() {
  await logout()
  session.value = { mode: session.value.mode, user: null, tools: [] }
  catalog.value = []
}
</script>

<template>
  <UApp>
  <div class="grid h-dvh grid-rows-[auto_minmax(0,1fr)] md:grid-cols-[248px_minmax(0,1fr)] md:grid-rows-none">
    <aside class="flex flex-col gap-4 border-b border-default bg-default p-3 md:border-b-0 md:border-r">
      <div class="flex items-center gap-3 px-2 pt-1">
        <img src="/brand/kdfp-logo.webp" alt="КДФП Инжиниринг" width="146" height="39">
      </div>
      <p class="-mb-2 hidden px-2 text-sm font-semibold text-highlighted md:block">Рабочее место</p>
      <UNavigationMenu
        v-if="session.user && nav.length"
        :items="nav"
        orientation="vertical"
        :highlight="true"
        class="w-full"
      />
      <p v-else-if="session.user && loaded && !nav.length" class="px-2 text-sm text-muted">Нет доступных инструментов — обратитесь к администратору.</p>
      <div v-if="session.user" class="mt-auto flex items-center gap-2 px-2 pb-1">
        <p class="min-w-0 flex-1 truncate text-xs text-muted" :title="session.user">{{ session.displayName || session.user }}</p>
        <UButton size="xs" variant="ghost" color="neutral" :loading="false" @click="signOut">Выйти</UButton>
      </div>
      <p v-else-if="loaded && error" class="px-2 text-sm text-error">{{ error }}</p>
    </aside>

    <main class="relative min-h-0 min-w-0">
      <RouterView v-if="session.user && tools.length" :tools="tools" />
      <div v-else class="flex h-full items-center justify-center p-6">
        <UCard v-if="loaded && !session.user && !error" class="w-full max-w-sm">
          <template #header>
            <p class="text-sm font-semibold">Вход — {{ session.mode === 'ldap' ? 'Active Directory' : 'портал' }}</p>
          </template>
          <form class="flex flex-col gap-3" @submit.prevent="submit">
            <UInput v-model="form.login" placeholder="Логин" autocomplete="username" autofocus />
            <UInput v-model="form.password" type="password" placeholder="Пароль" autocomplete="current-password" />
            <UAlert v-if="authFailed" color="error" variant="subtle" :description="authError" />
            <UButton type="submit" :loading="authBusy" block>Войти</UButton>
          </form>
        </UCard>
        <UAlert
          v-else-if="error"
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
