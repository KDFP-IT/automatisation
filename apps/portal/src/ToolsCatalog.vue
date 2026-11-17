<script setup>
import { computed, ref } from 'vue'
const props=defineProps({tools:{type:Array,required:true}})
const search=ref(''), category=ref('all')
const meta={
 bookmarks:{icon:'i-lucide-bookmark',description:'Создайте удобную навигацию по листам чертежей.',category:'documents'},
 signatures:{icon:'i-lucide-file-signature',description:'Найдите подписи и проверьте список подписантов.',category:'documents'},
 kac:{icon:'i-lucide-folder-cog',description:'Соберите основной документ и коммерческие предложения.',category:'documents'},
 trench:{icon:'i-lucide-ruler',description:'Трассы, колодцы и объёмы земляных работ.',category:'calculations'}
}
const filters=[{label:'Все инструменты',value:'all'},{label:'Документы',value:'documents'},{label:'Расчёты',value:'calculations'}]
const cards=computed(()=>props.tools.map(tool=>({...tool,...(meta[tool.id]??{icon:'i-lucide-files',description:'Откройте инструмент для работы с проектом.',category:'documents'})})).filter(tool=>(category.value==='all'||tool.category===category.value)&&[tool.title,tool.description].join(' ').toLocaleLowerCase('ru').includes(search.value.trim().toLocaleLowerCase('ru'))))
</script>
<template>
<section class="mx-auto w-full max-w-[1520px] px-5 py-9 sm:px-10 sm:py-12">
<h1 class="text-4xl font-bold tracking-tight text-highlighted">Инструменты</h1>
<p class="mt-3 text-lg text-muted">Выберите инструмент для работы с проектными документами.</p>
<UInput v-model="search" aria-label="Найти инструмент" placeholder="Найти инструмент" size="xl" class="mt-8 w-full max-w-4xl" />
<div class="mt-5 flex flex-wrap gap-3" role="group" aria-label="Категории инструментов">
<UButton v-for="filter in filters" :key="filter.value" :color="category===filter.value?'primary':'neutral'" :variant="category===filter.value?'solid':'outline'" :aria-pressed="category===filter.value" @click="category=filter.value">{{filter.label}}</UButton>
</div>
<Transition name="catalog-filter" mode="out-in">
<div :key="category" class="mt-7 grid gap-6 md:grid-cols-2 xl:grid-cols-3">
<article v-for="tool in cards" :key="tool.id" class="tool-card relative flex min-h-64 flex-col overflow-hidden rounded-xl border border-default bg-default p-6">
<div aria-hidden="true" class="card-art pointer-events-none" :class="'card-art-'+tool.id"></div>
<UIcon :name="tool.icon" class="relative mb-5 size-10 text-primary" />
<h2 class="relative text-xl font-bold text-highlighted">{{tool.title}}</h2>
<p class="relative mb-6 mt-2 max-w-sm text-sm leading-relaxed text-muted">{{tool.description}}</p>
<RouterLink :to="'/'+tool.id" :aria-label="'Открыть: '+tool.title" class="tool-link" />
</article>
</div>
</Transition>
<p v-if="!cards.length" class="py-16 text-center text-muted">Инструменты не найдены. Попробуйте другой запрос.</p>

</section>
</template>
<style scoped>
.tool-card { transition:transform 160ms ease,border-color 160ms ease,box-shadow 160ms ease; }
.catalog-filter-enter-active,.catalog-filter-leave-active { transition:opacity 150ms ease; }
.catalog-filter-enter-from,.catalog-filter-leave-to { opacity:0; }
.tool-card:hover,.tool-card:focus-within { border-color:var(--ui-primary); box-shadow:0 6px 18px #1013150b; transform:translateY(-2px); }
.tool-link::after { content:''; position:absolute; inset:0; border-radius:12px; }
.tool-link:focus-visible { outline:none; }
.tool-card:has(.tool-link:focus-visible) { outline:2px solid var(--ui-primary); outline-offset:3px; }
.card-art { position:absolute;inset:0 0 0 32%;container-type:size;overflow:hidden;opacity:.85;background:#f1f2f1;clip-path:polygon(32% 0,100% 0,100% 100%,0 100%);mask-image:linear-gradient(to right,transparent,black 42%); }
.card-art::before { content:'';position:absolute;right:-10px;top:50%;transform:translateY(-50%);width:max(100cqw,100cqh);aspect-ratio:1;background-image:url('/catalog/illustrations-extended.png');background-repeat:no-repeat;background-size:200% 200%;background-position:var(--art-position); }
.card-art-bookmarks { --art-position:0% 0%; }
.card-art-signatures { --art-position:100% 0%; }
.card-art-kac { --art-position:0% 100%; }
.card-art-trench { --art-position:100% 100%; }
.card-art-signatures::before,.card-art-kac::before { right:-25px; }
.tool-card h2,.tool-card p { max-width:72%; }
.tool-card p { font-weight:600;color:var(--ui-text);text-shadow:0 1px 4px white,0 0 10px white; }
.tool-card::before { content:'';position:absolute;inset:0;background:linear-gradient(to right,white 0%,#ffffffed 38%,#ffffff70 65%,transparent 85%);z-index:1;pointer-events:none; }
.tool-card>h2,.tool-card>p,.tool-card>.tool-link,.tool-card>span { z-index:2; }
.tool-link::after { z-index:3; }
@media(max-width:600px){.tool-card h2,.tool-card p{max-width:85%}.card-art{opacity:.35}}
@media(prefers-reduced-motion:reduce){.tool-card,.catalog-filter-enter-active,.catalog-filter-leave-active{transition:none}.tool-card:hover{transform:none}}
</style>
