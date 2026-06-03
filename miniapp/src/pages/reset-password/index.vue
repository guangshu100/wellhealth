<template>
  <view class="page reset-page">
    <view class="reset-header">
      <text class="page-title">找回密码</text>
      <text class="page-subtitle">通过邮箱验证码重置密码</text>
    </view>

    <view class="card reset-card">
      <view class="form-group">
        <text class="form-label">邮箱</text>
        <input
          v-model="form.email"
          class="input-field"
          placeholder="请输入注册邮箱"
          placeholder-class="input-placeholder"
        />
      </view>

      <view class="form-group">
        <text class="form-label">验证码</text>
        <view class="code-input-row">
          <input
            v-model="form.code"
            class="input-field code-input"
            placeholder="请输入邮箱验证码"
            placeholder-class="input-placeholder"
          />
          <button
            class="btn-secondary code-btn"
            :disabled="sending || countdown > 0"
            @tap="sendCode"
          >
            {{ countdown > 0 ? `${countdown}s 后重发` : (sending ? '发送中...' : '获取验证码') }}
          </button>
        </view>
      </view>

      <view class="form-group">
        <text class="form-label">新密码</text>
        <input
          v-model="form.newPassword"
          class="input-field"
          type="safe-password"
          password
          placeholder="请输入新密码（至少6位）"
          placeholder-class="input-placeholder"
        />
      </view>

      <view class="form-group">
        <text class="form-label">确认新密码</text>
        <input
          v-model="form.confirmPassword"
          class="input-field"
          type="safe-password"
          password
          placeholder="请再次输入新密码"
          placeholder-class="input-placeholder"
          @confirm="handleReset"
        />
      </view>

      <button class="btn-primary reset-btn" :disabled="loading" @tap="handleReset">
        {{ loading ? '重置中...' : '重置密码' }}
      </button>

      <view class="reset-footer">
        <text class="link-text" @tap="goLogin">返回登录</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, onUnmounted } from 'vue'
import api from '@/utils/api'

const loading = ref(false)
const sending = ref(false)
const countdown = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

const form = reactive({
  email: '',
  code: '',
  newPassword: '',
  confirmPassword: ''
})

function startCountdown() {
  countdown.value = 60
  timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(timer!)
      timer = null
    }
  }, 1000)
}

async function sendCode() {
  if (!form.email) {
    uni.showToast({ title: '请先输入邮箱', icon: 'none' })
    return
  }
  if (!/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(form.email)) {
    uni.showToast({ title: '请输入正确的邮箱格式', icon: 'none' })
    return
  }
  sending.value = true
  try {
    await api.post('/users/email/code', { email: form.email, purpose: 'reset' })
    uni.showToast({ title: '验证码已发送', icon: 'success' })
    startCountdown()
  } catch (e: any) {
    uni.showToast({ title: e.message || '发送失败', icon: 'none' })
  } finally {
    sending.value = false
  }
}

async function handleReset() {
  if (!form.email) {
    uni.showToast({ title: '请输入邮箱', icon: 'none' })
    return
  }
  if (!form.code) {
    uni.showToast({ title: '请输入验证码', icon: 'none' })
    return
  }
  if (!form.newPassword || form.newPassword.length < 6) {
    uni.showToast({ title: '新密码长度至少6位', icon: 'none' })
    return
  }
  if (form.newPassword !== form.confirmPassword) {
    uni.showToast({ title: '两次输入的密码不一致', icon: 'none' })
    return
  }
  loading.value = true
  try {
    await api.post('/users/reset-password', {
      email: form.email,
      code: form.code,
      new_password: form.newPassword
    })
    uni.showToast({ title: '密码重置成功', icon: 'success' })
    setTimeout(() => {
      uni.navigateBack()
    }, 1000)
  } catch (e: any) {
    uni.showToast({ title: e.message || '重置失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function goLogin() {
  uni.navigateBack()
}

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.reset-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-lg);
  min-height: 100vh;
  background: var(--color-bg-page);
}

.reset-header {
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

.reset-card {
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

.code-input-row {
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
}

.code-input {
  flex: 1;
}

.code-btn {
  flex-shrink: 0;
  font-size: 24rpx;
  padding: 16rpx 24rpx;
  white-space: nowrap;
}

.code-btn[disabled] {
  opacity: 0.6;
}

.reset-btn {
  width: 100%;
  margin-top: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.reset-btn[disabled] {
  opacity: 0.6;
}

.reset-footer {
  display: flex;
  justify-content: center;
  align-items: center;
}

.link-text {
  font-size: 26rpx;
  color: var(--color-primary);
  padding: var(--spacing-xs);
}
</style>
