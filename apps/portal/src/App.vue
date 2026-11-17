<script setup>
import { onMounted, ref } from 'vue'
import { loadTools } from './tools'
const tools=ref([]), error=ref('')
onMounted(async()=>{try{tools.value=await loadTools()}catch(e){error.value=e.message}})
</script>
<template>
<UApp>
<div class="flex min-h-dvh flex-col">
<header class="flex min-h-20 shrink-0 items-center gap-5 border-b border-default bg-default px-6 sm:px-10">
<RouterLink to="/" aria-label="КДФП — все инструменты" class="shrink-0"><img src="/brand/kdfp-logo.webp" alt="КДФП Инжиниринг" width="146" height="39"></RouterLink>
<span class="border-l border-default pl-5 text-lg font-semibold text-highlighted">Внутренние инструменты КДФП</span>
<span class="ml-auto flex shrink-0 items-center text-muted" role="img" aria-label="Учетная запись" title="Учетная запись">
<UIcon name="i-lucide-circle-user-round" class="size-10" />
</span>
</header>
<main class="relative flex min-h-0 flex-1 flex-col">
<RouterView v-if="tools.length" :tools="tools" />
<UAlert v-else-if="error" class="m-8" color="error" title="Каталог недоступен" :description="error" />
<p v-else class="p-8 text-muted">Загружаю инструменты…</p>
</main>
</div>
</UApp>
</template>
