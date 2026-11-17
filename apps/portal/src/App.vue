<script setup>
import { computed, onMounted, ref } from 'vue'
import { loadAuth, loadTools, login, logout } from './tools'


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
    <div class="flex min-h-dvh flex-col">
      <header class="flex min-h-20 shrink-0 items-center gap-5 border-b border-default bg-default px-6 sm:px-10">
        <RouterLink to="/" aria-label="КДФП — все инструменты" class="shrink-0"><img src="/brand/kdfp-logo.webp" alt="КДФП Инжиниринг" width="146" height="39"></RouterLink>
        <span class="hidden border-l border-default pl-5 text-lg font-semibold text-highlighted sm:block">Внутренние инструменты КДФП</span>
        <div v-if="session.user" class="ml-auto flex min-w-0 items-center gap-3">
          <UIcon name="i-lucide-circle-user-round" class="size-10 shrink-0 text-muted" />
          <span class="max-w-64 truncate text-sm font-semibold" :title="session.user">{{ session.displayName || session.user }}</span>
          <UButton size="sm" variant="ghost" color="neutral" @click="signOut">Выйти</UButton>
        </div>
      </header>
      <main class="relative flex min-h-0 min-w-0 flex-1 flex-col">
        <RouterView v-if="session.user && tools.length" :tools="tools" />
        <div v-else class="flex flex-1 items-center justify-center p-6">
          <UCard v-if="loaded && !session.user && !error" class="w-full max-w-sm">
            <template #header><p class="text-sm font-semibold">Вход — {{ session.mode === 'ldap' ? 'Active Directory' : 'портал' }}</p></template>
            <form class="flex flex-col gap-3" @submit.prevent="submit">
              <UInput v-model="form.login" aria-label="Логин" placeholder="Логин" autocomplete="username" autofocus />
              <UInput v-model="form.password" aria-label="Пароль" type="password" placeholder="Пароль" autocomplete="current-password" />
              <UAlert v-if="authFailed" color="error" variant="subtle" :description="authError" />
              <UButton type="submit" :loading="authBusy" block>Войти</UButton>
            </form>
          </UCard>
          <UAlert v-else-if="error" color="error" variant="subtle" title="Каталог недоступен" :description="error" class="max-w-md" />
          <p v-else-if="loaded && session.user" class="text-sm text-muted">Нет доступных инструментов — обратитесь к администратору.</p>
          <p v-else class="text-sm text-muted">Загружаю инструменты…</p>
        </div>
      </main>
    </div>
  </UApp>
</template>