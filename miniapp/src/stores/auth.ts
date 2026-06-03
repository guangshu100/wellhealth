import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/utils/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref('')
  const tokenType = ref('Bearer')
  const userInfo = ref<any>(null)

  const isLoggedIn = computed(() => !!token.value)
  const userId = computed(() => userInfo.value?.id || '')
  const userName = computed(() => userInfo.value?.name || userInfo.value?.username || '用户')

  function init() {
    token.value = uni.getStorageSync('token') || ''
    tokenType.value = uni.getStorageSync('tokenType') || 'Bearer'
    const info = uni.getStorageSync('userInfo')
    if (info) {
      try { userInfo.value = JSON.parse(info) } catch { userInfo.value = null }
    }
  }

  async function login(username: string, password: string) {
    const res: any = await api.postForm('/users/login', { username, password })
    if (res.access_token) {
      token.value = res.access_token
      tokenType.value = res.token_type || 'Bearer'
      uni.setStorageSync('token', token.value)
      uni.setStorageSync('tokenType', tokenType.value)
      await fetchUserInfo()
      return true
    }
    return false
  }

  async function register(data: { username: string; password: string; email?: string; phone?: string }) {
    const res: any = await api.post('/users/register', data)
    return res.success !== false
  }

  async function fetchUserInfo() {
    try {
      const res: any = await api.get('/users/me')
      userInfo.value = res
      uni.setStorageSync('userInfo', JSON.stringify(res))
    } catch (e) {
      console.error('获取用户信息失败', e)
    }
  }

  function logout() {
    token.value = ''
    tokenType.value = 'Bearer'
    userInfo.value = null
    uni.removeStorageSync('token')
    uni.removeStorageSync('tokenType')
    uni.removeStorageSync('userInfo')
    uni.reLaunch({ url: '/pages/login/index' })
  }

  return { token, tokenType, userInfo, isLoggedIn, userId, userName, init, login, register, fetchUserInfo, logout }
})
