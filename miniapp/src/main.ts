import { createSSRApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import { useAuthStore } from './stores/auth'

export function createApp() {
  const app = createSSRApp(App)
  const pinia = createPinia()
  app.use(pinia)

  // 启动时从本地存储恢复登录状态
  const auth = useAuthStore()
  auth.init()

  return { app }
}
