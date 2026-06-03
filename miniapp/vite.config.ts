import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

export default defineConfig({
  plugins: [uni()],
  resolve: {
    alias: {
      '@': '/src'
    }
  },
  build: {
    // uni-app 内部处理，无需特别配置
    sourcemap: false,
    chunkSizeWarningLimit: 2000,
  },
  server: {
    port: 5175,
    host: '0.0.0.0',
    proxy: {
      // 开发环境下，将后端 API 代理到本地后端服务
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
