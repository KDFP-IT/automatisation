<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({ tools: { type: Array, required: true } })

const route = useRoute()
const router = useRouter()
const mounted = ref(new Set())

const active = computed(() =>
  props.tools.find(tool => tool.id === route.params.tool) ?? props.tools[0])

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
  <template v-for="tool in tools" :key="tool.id">
    <iframe
      v-if="mounted.has(tool.id)"
      v-show="active.id === tool.id"
      :src="source(tool)"
      :title="tool.title"
      class="block h-full w-full border-0"
    />
  </template>
</template>
