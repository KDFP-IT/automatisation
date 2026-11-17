<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import KacAssemble from '../../../packages/kac-ui/src/KacAssemble.vue'
import SignaturesCheck from './SignaturesCheck.vue'
import BookmarksCheck from './BookmarksCheck.vue'
import ToolsCatalog from './ToolsCatalog.vue'

const props = defineProps({ tools: { type: Array, required: true } })

const route = useRoute()
const router = useRouter()
const mounted = ref(new Set())
const native = { kac: KacAssemble, signatures: SignaturesCheck, bookmarks: BookmarksCheck }

const active = computed(() =>
  props.tools.find(tool => tool.id === route.params.tool))

watch(active, tool => {
  if (tool && route.params.tool !== tool.id) router.replace('/' + tool.id)
}, { immediate: true })

watch(active, tool => {
  if (tool) mounted.value.add(tool.id)
}, { immediate: true })

function source(tool) {
  const url = new URL(tool.url)
  url.searchParams.set('embed', '1')
  return url.href
}
</script>

<template>
  <div class="tool-pages relative flex min-h-0 flex-1 flex-col">
    <Transition name="page" appear>
      <div v-show="!active" class="tool-page">
        <ToolsCatalog :tools="tools" />
      </div>
    </Transition>
    <template v-for="tool in tools" :key="tool.id">
      <Transition v-if="mounted.has(tool.id)" name="page" appear>
        <div v-show="active?.id === tool.id" class="tool-page">
        <component v-if="native[tool.id]" :is="native[tool.id]" />
        <iframe
          v-else
          :src="source(tool)"
          :title="tool.title"
          class="block min-h-[calc(100dvh-80px)] w-full flex-1 border-0"
        />
        </div>
      </Transition>
    </template>
  </div>
</template>

<style>
.tool-page {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
}
.page-enter-active {
  transition: opacity 240ms ease-out 100ms;
}
.page-leave-active {
  position: absolute;
  inset: 0 0 auto;
  pointer-events: none;
  transition: opacity 100ms ease-in;
}
.page-enter-from,
.page-leave-to {
  opacity: 0;
}
@media (prefers-reduced-motion: reduce) {
  .page-enter-active,
  .page-leave-active {
    transition: none;
  }
}
</style>
