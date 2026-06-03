<template>
  <view class="page register-page">
    <view class="register-header">
      <text class="page-title">注册账号</text>
      <text class="page-subtitle">加入康伴健康</text>
    </view>

    <view class="card register-card">
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
          placeholder="请输入密码（至少6位）"
          placeholder-class="input-placeholder"
        />
      </view>

      <view class="form-group">
        <text class="form-label">确认密码</text>
        <input
          v-model="form.confirmPassword"
          class="input-field"
          type="safe-password"
          password
          placeholder="请再次输入密码"
          placeholder-class="input-placeholder"
        />
      </view>

      <view class="form-group">
        <text class="form-label">邮箱</text>
        <input
          v-model="form.email"
          class="input-field"
          placeholder="请输入邮箱"
          placeholder-class="input-placeholder"
        />
      </view>

      <view class="form-group">
        <text class="form-label">手机号</text>
        <input
          v-model="form.phone"
          class="input-field"
          type="number"
          placeholder="请输入手机号"
          placeholder-class="input-placeholder"
          @confirm="handleRegister"
        />
      </view>

      <button class="btn-primary register-btn" :disabled="loading" @tap="handleRegister">
        {{ loading ? '注册中...' : '注册' }}
      </button>

      <view class="register-footer">
        <text class="footer-text">已有账号？</text>
        <text class="link-text" @tap="goLogin">立即登录</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import api from '@/utils/api'

const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  email: '',
  phone: ''
})

async function handleRegister() {
  if (!form.username.trim()) {
    uni.showToast({ title: '请输入用户名', icon: 'none' })
    return
  }
  if (!form.password || form.password.length < 6) {
    uni.showToast({ title: '密码长度至少6位', icon: 'none' })
    return
  }
  if (form.password !== form.confirmPassword) {
    uni.showToast({ title: '两次输入密码不一致', icon: 'none' })
    return
  }
  if (form.email && !/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(form.email)) {
    uni.showToast({ title: '请输入正确的邮箱格式', icon: 'none' })
    return
  }
  if (form.phone && !/^1[3-9]\d{9}$/.test(form.phone)) {
    uni.showToast({ title: '请输入正确的手机号', icon: 'none' })
    return
  }

  loading.value = true
  try {
    await api.post('/users/register', {
      username: form.username.trim(),
      password: form.password,
      email: form.email || undefined,
      phone: form.phone || undefined
    })
    uni.showToast({ title: '注册成功', icon: 'success' })
    setTimeout(() => {
      uni.navigateBack()
    }, 500)
  } catch (e: any) {
    uni.showToast({ title: e.message || '注册失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function goLogin() {
  uni.navigateBack()
}
</script>

<style scoped>
.register-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-lg);
  min-height: 100vh;
  background: var(--color-bg-page);
}

.register-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: var(--spacing-xl);
}

.page-title {
  font-size: 44rpx;
  font-weight: 700;
  color: var(--color-primary);
  margin-bottom: var(--spacing-xs);
}

.page-subtitle {
  font-size: 26rpx;
  color: var(--color-text-secondary);
}

.register-card {
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

.register-btn {
  width: 100%;
  margin-top: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.register-btn[disabled] {
  opacity: 0.6;
}

.register-footer {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--spacing-xs);
}

.footer-text {
  font-size: 26rpx;
  color: var(--color-text-hint);
}

.link-text {
  font-size: 26rpx;
  color: var(--color-primary);
  padding: var(--spacing-xs);
}
</style>
