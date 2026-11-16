import { fileURLToPath } from 'node:url'
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
            'lucide:bookmark',
            'lucide:circle-check',
            'lucide:download',
            'lucide:file-archive',
            'lucide:file-check',
            'lucide:file-signature',
            'lucide:file-text',
            'lucide:files',
            'lucide:folder',
            'lucide:folder-cog',
            'lucide:folder-open',
            'lucide:folder-up',
            'lucide:info',
            'lucide:loader-circle',
            'lucide:ruler',
            'lucide:triangle-alert',
            'lucide:upload',
            'lucide:x',
            'vscode-icons:file-type-word'
          ]
        }
      }
    })
  ],
  base: '/',
  build: { outDir: 'dist', emptyOutDir: true, assetsInlineLimit: 0 },
  server: {
    fs: { allow: [fileURLToPath(new URL('../../..', import.meta.url))] },
    proxy: {
      '/bookmarks': 'http://127.0.0.1:8090',
      '/signatures': 'http://127.0.0.1:8090',
      '/trench': 'http://127.0.0.1:8090',
      '/kac': 'http://127.0.0.1:8090',
      '/portal/tools.json': 'http://127.0.0.1:8090'
    }
  }
})
