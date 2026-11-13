import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import ui from '@nuxt/ui/vite'

export default defineConfig({
  plugins: [
    vue(),
    ui({
      dts: false,
      colorMode: false,
      theme: { colors: ['primary', 'success', 'warning', 'error', 'info'] },
      ui: { colors: { primary: 'brand', neutral: 'zinc' } },
      icon: {
        clientBundle: {
          icons: [
            'lucide:arrow-right',
            'lucide:circle-check',
            'lucide:download',
            'lucide:file-archive',
            'lucide:file-check',
            'lucide:file-text',
            'lucide:files',
            'lucide:folder',
            'lucide:folder-open',
            'lucide:folder-up',
            'lucide:info',
            'lucide:loader-circle',
            'lucide:triangle-alert',
            'lucide:upload',
            'lucide:x',
            'vscode-icons:file-type-word'
          ]
        }
      }
    })
  ],
  base: '/kac/ui/',
  build: { outDir: '../static/ui', emptyOutDir: true, assetsInlineLimit: 0 },
  server: {
    proxy: { '/kac': 'http://127.0.0.1:8099' }
  }
})
