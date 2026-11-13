import './assets/main.css'

import { createApp } from 'vue'
import { addIcon } from '@iconify/vue'
import { init as initIcons } from 'virtual:nuxt-ui-icons'
import App from './App.vue'

if (window.self !== window.top || new URLSearchParams(window.location.search).has('embed')) {
  document.documentElement.dataset.embedded = ''
}

initIcons(addIcon)
createApp(App).mount('#app')
