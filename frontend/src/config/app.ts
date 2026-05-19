const isTauri = typeof window !== 'undefined' && '__TAURI__' in window

export const API_BASE_URL = isTauri 
  ? 'http://localhost:8000' 
  : import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const APP_CONFIG = {
  name: '康伴健康',
  version: '1.0.0',
  description: '慢病管理AI平台',
}

export const IS_TAURI = isTauri
