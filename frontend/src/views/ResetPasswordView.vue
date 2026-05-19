<template>
  <div class="reset-page">
    <div class="reset-container">
      <div class="reset-header">
        <h1 class="title">找回密码</h1>
        <p class="subtitle">通过邮箱验证码重置</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        class="reset-form"
        @submit.prevent="handleReset"
      >
        <el-form-item prop="email">
          <el-input
            v-model="form.email"
            placeholder="请输入注册邮箱"
            size="large"
            :prefix-icon="Message"
          />
        </el-form-item>

        <el-form-item prop="code">
          <div class="code-wrapper">
            <el-input
              v-model="form.code"
              placeholder="请输入邮箱验证码"
              size="large"
              class="code-input"
            />
            <el-button 
              size="large" 
              @click="sendCode" 
              :disabled="countdown > 0"
              class="code-btn"
            >
              {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
            </el-button>
          </div>
        </el-form-item>

        <el-form-item prop="newPassword">
          <el-input
            v-model="form.newPassword"
            type="password"
            placeholder="请输入新密码 (至少6位)"
            size="large"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-form-item prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="请再次输入新密码"
            size="large"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="reset-button"
            @click="handleReset"
          >
            {{ loading ? '重置中...' : '重置密码' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="reset-footer">
        <span>想起密码了？</span>
        <el-link type="primary" @click="router.push('/login')">立即登录</el-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, Message } from '@element-plus/icons-vue'
import { sendEmailCode, resetPassword } from '@/api/auth'

const router = useRouter()

const formRef = ref()
const loading = ref(false)
const countdown = ref(0)

const form = reactive({
  email: '',
  code: '',
  newPassword: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule: any, value: string, callback: any) => {
  if (value !== form.newPassword) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入邮箱验证码', trigger: 'blur' },
    { len: 6, message: '验证码为6位', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

async function sendCode() {
  if (!form.email) {
    ElMessage.warning('请输入邮箱')
    return
  }
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
  if (!emailRegex.test(form.email)) {
    ElMessage.warning('请输入正确的邮箱格式')
    return
  }
  
  try {
    await sendEmailCode(form.email, 'reset')
    ElMessage.success('验证码已发送')
    countdown.value = 60
    const timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) {
        clearInterval(timer)
      }
    }, 1000)
  } catch (error: any) {
    ElMessage.error(error.message || '发送失败')
  }
}

async function handleReset() {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid: boolean) => {
    if (!valid) return

    loading.value = true
    try {
      await resetPassword(form.email, form.code, form.newPassword)
      
      ElMessage.success('密码重置成功')
      router.push('/login')
    } catch (error: any) {
      ElMessage.error(error.message || error.detail || '重置失败')
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped lang="scss">
.reset-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #FCF8F0 0%, #F5F0E5 100%);
}

.reset-container {
  width: 400px;
  padding: 40px;
  background: #FFFFFF;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(60, 55, 45, 0.08);
}

.reset-header {
  text-align: center;
  margin-bottom: 30px;

  .title {
    font-size: 24px;
    font-weight: bold;
    color: var(--color-primary);
    margin-bottom: 8px;
  }

  .subtitle {
    font-size: 14px;
    color: #7F7D74;
  }
}

.code-wrapper {
  display: flex;
  gap: 12px;
  width: 100%;
  
  .code-input {
    flex: 1;
  }
  
  .code-btn {
    min-width: 100px;
    background: var(--color-primary);
    border-color: var(--color-primary);
    color: #fff;
    
    &:hover:not(:disabled) {
      background: var(--color-primary-dark);
      border-color: var(--color-primary-dark);
    }
    
    &:disabled {
      background: #DDCFB0;
      border-color: #DDCFB0;
      color: #7F7D74;
    }
  }
}

.reset-form {
  .reset-button {
    width: 100%;
    background: var(--color-primary);
    border-color: var(--color-primary);

    &:hover {
      background: var(--color-primary-dark);
      border-color: var(--color-primary-dark);
    }
  }
}

.reset-footer {
  text-align: center;
  margin-top: 20px;
  color: #7F7D74;
}
</style>
