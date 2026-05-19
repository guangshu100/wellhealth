import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

const host = process.env.TAURI_DEV_HOST

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  clearScreen: false,
  server: {
    port: 8443,
    strictPort: true,
    host: host || false,
    hmr: host
      ? {
          protocol: 'ws',
          host,
          port: 5174,
        }
      : undefined,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    target: process.env.TAURI_ENV === 'web' ? undefined : 'esnext',
    minify: process.env.TAURI_ENV === 'web' ? 'esbuild' : false,
    sourcemap: false,
  },
  envPrefix: ['VITE_', 'TAURI_'],
})
