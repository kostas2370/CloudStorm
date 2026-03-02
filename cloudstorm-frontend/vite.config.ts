import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// cloudstorm-frontend/vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://api:8000',
        changeOrigin: true,
      },
    },
  },
})