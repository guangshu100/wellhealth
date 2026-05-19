<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <h1 class="title">康伴健康</h1>
        <p class="subtitle">智能慢病管理平台</p>
      </div>

      <div class="login-tabs">
        <div 
          class="tab-item" 
          :class="{ active: loginType === 'password' }"
          @click="loginType = 'password'"
        >
          账号登录
        </div>
        <div 
          class="tab-item" 
          :class="{ active: loginType === 'email' }"
          @click="loginType = 'email'"
        >
          邮箱登录
        </div>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <!-- 账号密码登录 -->
        <template v-if="loginType === 'password'">
          <el-form-item prop="username">
            <el-input
              v-model="form.username"
              placeholder="用户名或手机号"
              size="large"
              :prefix-icon="User"
            />
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="密码"
              size="large"
              :prefix-icon="Lock"
              show-password
              @keyup.enter="handleLogin"
            />
          </el-form-item>
        </template>

        <!-- 邮箱验证码登录 -->
        <template v-else>
          <el-form-item prop="email">
            <el-input
              v-model="form.email"
              placeholder="请输入邮箱"
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
                @keyup.enter="handleLogin"
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
        </template>

        <!-- 图形验证码 -->
        <el-form-item prop="captchaCode">
          <div class="captcha-wrapper">
            <el-input
              v-model="form.captchaCode"
              placeholder="请输入图形验证码"
              size="large"
              class="captcha-input"
              maxlength="4"
              @keyup.enter="handleLogin"
            />
            <img
              :src="captchaImage"
              class="captcha-image"
              alt="验证码"
              @click="refreshCaptcha"
            />
          </div>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-button"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <div class="footer-left">
          <el-checkbox v-model="rememberMe">记住登录</el-checkbox>
        </div>
        <div class="footer-right">
          <el-link type="primary" @click="router.push('/register')">注册账号</el-link>
          <el-link type="primary" @click="router.push('/reset-password')">忘记密码?</el-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Message } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { getCaptcha } from '@/api/captcha'
import { login, emailLogin, sendEmailCode } from '@/api/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const formRef = ref()
const loading = ref(false)
const rememberMe = ref(false)
const loginType = ref('password')
const countdown = ref(0)

const captchaKey = ref('')
const captchaImage = ref('')

const form = reactive({
  username: '',
  password: '',
  email: '',
  code: '',
  captchaCode: ''
})

const passwordRules = {
  username: [
    { required: true, message: '请输入用户名或手机号', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  captchaCode: [
    { required: true, message: '请输入图形验证码', trigger: 'blur' },
    { len: 4, message: '验证码为4位', trigger: 'blur' }
  ]
}

const emailRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入邮箱验证码', trigger: 'blur' },
    { len: 6, message: '验证码为6位', trigger: 'blur' }
  ],
  captchaCode: [
    { required: true, message: '请输入图形验证码', trigger: 'blur' },
    { len: 4, message: '验证码为4位', trigger: 'blur' }
  ]
}

const rules = loginType.value === 'password' ? passwordRules : emailRules

watch(loginType, (newType) => {
  form.captchaCode = ''
  if (newType === 'password') {
    rules.username = passwordRules.username
    rules.password = passwordRules.password
  } else {
    rules.email = emailRules.email
    rules.code = emailRules.code
  }
  rules.captchaCode = passwordRules.captchaCode
  formRef.value?.clearValidate()
})

async function refreshCaptcha() {
  try {
    const res = await getCaptcha()
    captchaKey.value = res.captchaKey
    captchaImage.value = res.captchaImage
  } catch (error) {
    console.error('获取验证码失败', error)
    ElMessage.error('获取验证码失败')
  }
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
    await sendEmailCode(form.email, 'login')
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

async function handleLogin() {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid: boolean) => {
    if (!valid) return

    loading.value = true
    try {
      let res
      if (loginType.value === 'password') {
        res = await login(form.username, form.password, captchaKey.value, form.captchaCode)
      } else {
        res = await emailLogin(form.email, form.code, captchaKey.value, form.captchaCode)
      }
      
      authStore.token = res.token
      authStore.userInfo = res.user
      localStorage.setItem('token', res.token)
      localStorage.setItem('tokenType', res.token_type || 'bearer')
      localStorage.setItem('userInfo', JSON.stringify(res.user))
      
      ElMessage.success('登录成功')
      
      const redirect = route.query.redirect as string || '/'
      router.push(redirect)
    } catch (error: any) {
      ElMessage.error(error.message || error.detail || '登录失败')
      form.captchaCode = ''
      refreshCaptcha()
    } finally {
      loading.value = false
    }
  })
}

onMounted(() => {
  refreshCaptcha()
})
</script>

<style scoped lang="scss">
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #FCF8F0 0%, #F5F0E5 100%);
}

.login-container {
  width: 400px;
  padding: 40px;
  background: #FFFFFF;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(60, 55, 45, 0.08);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;

  .title {
    font-size: 28px;
    font-weight: bold;
    color: var(--color-primary);
    margin-bottom: 8px;
  }

  .subtitle {
    font-size: 14px;
    color: #7F7D74;
  }
}

.login-tabs {
  display: flex;
  margin-bottom: 24px;
  border-bottom: 1px solid #E8DFD0;
  
  .tab-item {
    flex: 1;
    padding: 12px;
    text-align: center;
    font-size: 16px;
    color: #7F7D74;
    cursor: pointer;
    position: relative;
    
    &.active {
      color: var(--color-primary);
      font-weight: bold;
      
      &::after {
        content: '';
        position: absolute;
        bottom: -1px;
        left: 50%;
        transform: translateX(-50%);
        width: 60px;
        height: 2px;
        background: var(--color-primary);
      }
    }
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

.captcha-wrapper {
  display: flex;
  gap: 12px;
  width: 100%;

  .captcha-input {
    flex: 1;
  }

  .captcha-image {
    height: 40px;
    border-radius: 8px;
    cursor: pointer;
    border: 1px solid #DDCFB0;
    background: #FCF8F0;
  }
}

.login-form {
  .login-button {
    width: 100%;
    background: var(--color-primary);
    border-color: var(--color-primary);

    &:hover {
      background: var(--color-primary-dark);
      border-color: var(--color-primary-dark);
    }
  }
}

.login-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
  
  .footer-left {
    display: flex;
    align-items: center;
  }
  
  .footer-right {
    display: flex;
    gap: 16px;
  }
}
</style>
