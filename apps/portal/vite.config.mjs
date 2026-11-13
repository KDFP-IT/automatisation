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
            'lucide:bookmark',
            'lucide:file-signature',
            'lucide:ruler',
            'lucide:folder-cog',
            'lucide:triangle-alert'
          ]
        }
      }
    })
  ],
  base: '/',
  build: { outDir: 'dist', emptyOutDir: true, assetsInlineLimit: 0 },
  server: {
    proxy: {
      '/bookmarks': 'http://127.0.0.1:8090',
      '/signatures': 'http://127.0.0.1:8090',
      '/trench': 'http://127.0.0.1:8090',
      '/kac': 'http://127.0.0.1:8090',
      '/portal/tools.json': 'http://127.0.0.1:8090'
    }
  }
})
