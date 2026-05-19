import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login, getUserInfo, logout as apiLogout } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const userInfo = ref<any>(JSON.parse(localStorage.getItem('userInfo') || 'null'))
  const roles = ref<string[]>(userInfo.value?.role ? [userInfo.value.role] : [])

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => roles.value.includes('admin'))
  const isDoctor = computed(() => roles.value.includes('doctor'))

  async function loginAction(username: string, password: string, captchaKey?: string, captchaCode?: string) {
    const res = await login(username, password, captchaKey, captchaCode)
    token.value = res.token
    userInfo.value = res.user
    roles.value = [res.user.role]
    
    localStorage.setItem('token', res.token)
    localStorage.setItem('tokenType', res.token_type || 'bearer')
    localStorage.setItem('userInfo', JSON.stringify(res.user))
    
    return res
  }

  async function fetchUserInfo() {
    if (!token.value) return null
    try {
      const res = await getUserInfo()
      userInfo.value = res
      roles.value = [res.role]
      localStorage.setItem('userInfo', JSON.stringify(res))
      return res
    } catch (error) {
      logout()
      return null
    }
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    roles.value = []
    localStorage.removeItem('token')
    localStorage.removeItem('tokenType')
    localStorage.removeItem('userInfo')
  }

  function hasPermission(permission: string): boolean {
    const permissions = getPermissionsByRole(userInfo.value?.role)
    return permissions.includes(permission) || permissions.includes('admin:all')
  }

  function getPermissionsByRole(role: string): string[] {
    const rolePermissions: Record<string, string[]> = {
      admin: ['patient:read', 'patient:write', 'patient:delete', 'family:read', 'family:write', 'family:delete', 'health:read', 'health:write', 'prediction:read', 'prediction:write', 'recipe:read', 'recipe:write', 'chat:read', 'chat:write', 'admin:all'],
      doctor: ['patient:read', 'patient:write', 'family:read', 'health:read', 'health:write', 'prediction:read', 'prediction:write', 'chat:read', 'chat:write'],
      patient: ['patient:read:self', 'family:read', 'health:read:self', 'health:write:self', 'prediction:read:self', 'recipe:read', 'recipe:write', 'chat:read', 'chat:write'],
      family: ['patient:read:family', 'family:read', 'family:write', 'health:read:family', 'prediction:read:family', 'chat:read', 'chat:write']
    }
    return rolePermissions[role] || []
  }

  return {
    token,
    userInfo,
    roles,
    isLoggedIn,
    isAdmin,
    isDoctor,
    loginAction,
    fetchUserInfo,
    logout,
    hasPermission
  }
})
