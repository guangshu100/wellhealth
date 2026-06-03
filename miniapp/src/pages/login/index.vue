<template>
  <view class="page login-page">
    <view class="login-header">
      <text class="app-title">康伴健康</text>
      <text class="app-subtitle">智能慢病管理平台</text>
    </view>

    <view class="card login-card">
      <view class="form-group">
        <text class="form-label">用户名</text>
        <input
          v-model="form.username"
          class="input-field"
          placeholder="请输入用户名"
          placeholder-class="input-placeholder"
        />
      </view>

      <view class="form-group">
        <text class="form-label">密码</text>
        <input
          v-model="form.password"
          class="input-field"
          type="safe-password"
          password
          placeholder="请输入密码"
          placeholder-class="input-placeholder"
          @confirm="handleLogin"
        />
      </view>

      <button class="btn-primary login-btn" :disabled="loading" @tap="handleLogin">
        {{ loading ? '登录中...' : '登录' }}
      </button>

      <view class="login-links">
        <text class="link-text" @tap="goRegister">注册账号</text>
        <text class="link-text" @tap="goResetPassword">忘记密码</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

async function handleLogin() {
  if (!form.username.trim()) {
    uni.showToast({ title: '请输入用户名', icon: 'none' })
    return
  }
  if (!form.password) {
    uni.showToast({ title: '请输入密码', icon: 'none' })
    return
  }

  loading.value = true
  try {
    const success = await authStore.login(form.username.trim(), form.password)
    if (success) {
      uni.showToast({ title: '登录成功', icon: 'success' })
      setTimeout(() => {
        uni.reLaunch({ url: '/pages/index/index' })
      }, 500)
    } else {
      uni.showToast({ title: '登录失败', icon: 'none' })
    }
  } catch (e: any) {
    uni.showToast({ title: e.message || '登录失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function goRegister() {
  uni.navigateTo({ url: '/pages/register/index' })
}

function goResetPassword() {
  uni.navigateTo({ url: '/pages/reset-password/index' })
}
</script>

<style scoped>
.login-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: var(--spacing-lg);
  background: var(--color-bg-page);
}

.login-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: var(--spacing-xl);
}

.app-title {
  font-size: 48rpx;
  font-weight: 700;
  color: var(--color-primary);
  margin-bottom: var(--spacing-xs);
}

.app-subtitle {
  font-size: 26rpx;
  color: var(--color-text-secondary);
}

.login-card {
  width: 100%;
  max-width: 600rpx;
}

.form-group {
  margin-bottom: var(--spacing-md);
}

.form-label {
  display: block;
  font-size: 26rpx;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-xs);
}

.input-placeholder {
  color: var(--color-text-hint);
}

.login-btn {
  width: 100%;
  margin-top: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.login-btn[disabled] {
  opacity: 0.6;
}

.login-links {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.link-text {
  font-size: 26rpx;
  color: var(--color-primary);
  padding: var(--spacing-xs);
}
</style>
