import './assets/main.css'

import { createApp } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import { addIcon } from '@iconify/vue'
import { init as initIcons } from 'virtual:nuxt-ui-icons'
import App from './App.vue'
import ToolHost from './ToolHost.vue'

initIcons(addIcon)

// Старые ссылки вида #bookmarks приводим к #/bookmarks.
if (location.hash && !location.hash.startsWith('#/')) {
  location.replace(`${location.pathname}${location.search}#/${location.hash.slice(1)}`)
}

createApp(App)
  .use(createRouter({
    history: createWebHashHistory(),
    routes: [{ path: '/:tool?', component: ToolHost }]
  }))
  .mount('#app')
