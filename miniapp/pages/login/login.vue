<template>
  <view class="login-container">
    <view class="logo-section">
      <image class="logo" src="/static/images/logo.png" mode="aspectFit" />
      <text class="app-name">康伴健康</text>
      <text class="app-slogan">您的智能慢病管理助手</text>
    </view>

    <view class="login-tabs">
      <view 
        class="tab-item" 
        :class="{ active: loginType === 'password' }"
        @click="loginType = 'password'"
      >
        账号登录
      </view>
      <view 
        class="tab-item" 
        :class="{ active: loginType === 'email' }"
        @click="loginType = 'email'"
      >
        邮箱登录
      </view>
      <view 
        class="tab-item" 
        :class="{ active: loginType === 'wechat' }"
        @click="loginType = 'wechat'"
      >
        微信授权
      </view>
    </view>

    <!-- 账号密码登录 -->
    <view v-if="loginType === 'password'" class="login-form">
      <view class="input-group">
        <input 
          class="input" 
          v-model="username" 
          placeholder="请输入用户名或手机号"
        />
      </view>
      <view class="input-group">
        <input 
          class="input" 
          v-model="password" 
          type="password" 
          placeholder="请输入密码"
        />
      </view>
      
      <!-- 图形验证码 -->
      <view class="input-group captcha-group">
        <input 
          class="input captcha-input" 
          v-model="captchaCode" 
          type="text" 
          placeholder="请输入验证码" 
          maxlength="4" 
        />
        <image 
          class="captcha-img" 
          :src="captchaImage" 
          mode="aspectFit"
          @click="refreshCaptcha"
        />
      </view>
      
      <view class="extra-links">
        <text class="link" @click="goRegister">注册账号</text>
        <text class="link" @click="goResetPassword">忘记密码</text>
      </view>
      <button 
        class="login-btn" 
        type="primary" 
        @click="handlePasswordLogin" 
        :loading="loading"
        :disabled="!canLogin"
      >
        <text v-if="!loading">登录</text>
        <text v-else>登录中...</text>
      </button>
    </view>

    <!-- 邮箱验证码登录 -->
    <view v-else-if="loginType === 'email'" class="login-form">
      <view class="input-group">
        <input 
          class="input" 
          v-model="email" 
          type="text" 
          placeholder="请输入邮箱"
        />
      </view>
      
      <!-- 邮箱验证码 -->
      <view class="input-group captcha-group">
        <input 
          class="input captcha-input" 
          v-model="emailCode" 
          type="text" 
          placeholder="请输入邮箱验证码" 
          maxlength="6" 
        />
        <button 
          class="captcha-btn" 
          @click="sendEmailCode" 
          :disabled="countdown > 0"
        >
          {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
        </button>
      </view>

      <!-- 图形验证码 -->
      <view class="input-group captcha-group">
        <input 
          class="input captcha-input" 
          v-model="captchaCode" 
          type="text" 
          placeholder="请输入图形验证码" 
          maxlength="4" 
        />
        <image 
          class="captcha-img" 
          :src="captchaImage" 
          mode="aspectFit"
          @click="refreshCaptcha"
        />
      </view>
      
      <view class="extra-links">
        <text class="link" @click="goRegister">注册账号</text>
        <text class="link" @click="goResetPassword">忘记密码</text>
      </view>
      <button 
        class="login-btn" 
        type="primary" 
        @click="handleEmailLogin" 
        :loading="loading"
        :disabled="!canEmailLogin"
      >
        <text v-if="!loading">登录</text>
        <text v-else>登录中...</text>
      </button>
    </view>

    <!-- 微信登录 -->
    <view v-else class="login-form">
      <button class="login-btn wechat" type="primary" @click="handleWechatLogin" :loading="loading">
        <text v-if="!loading">微信授权登录</text>
        <text v-else>登录中...</text>
      </button>
    </view>

    <view class="agreement">
      <text>登录即表示同意</text>
      <text class="link" @click="openAgreement('user')">《用户协议》</text>
      <text>和</text>
      <text class="link" @click="openAgreement('privacy')">《隐私政策》</text>
    </view>
  </view>
</template>

<script>
import { userApi, captchaApi, emailCodeApi } from '@/utils/api'

export default {
  data() {
    return {
      loginType: 'password',
      username: '',
      password: '',
      email: '',
      emailCode: '',
      captchaCode: '',
      captchaKey: '',
      captchaImage: '',
      loading: false,
      countdown: 0
    }
  },
  computed: {
    canLogin() {
      return this.username.length > 0 && this.password.length > 0 && this.captchaCode.length > 0
    },
    canEmailLogin() {
      return this.email.length > 0 && this.emailCode.length > 0 && this.captchaCode.length > 0
    }
  },
  onLoad() {
    this.refreshCaptcha()
  },
  methods: {
    async refreshCaptcha() {
      try {
        const res = await captchaApi.getCaptcha()
        this.captchaKey = res.captchaKey
        this.captchaImage = res.captchaImage
        this.captchaCode = ''
      } catch (e) {
        console.error('获取验证码失败', e)
      }
    },
    async sendEmailCode() {
      if (!this.email) {
        uni.showToast({ title: '请输入邮箱', icon: 'none' })
        return
      }
      const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
      if (!emailRegex.test(this.email)) {
        uni.showToast({ title: '请输入正确的邮箱格式', icon: 'none' })
        return
      }
      
      try {
        await emailCodeApi.sendCode(this.email, 'login')
        uni.showToast({ title: '验证码已发送', icon: 'success' })
        this.countdown = 60
        const timer = setInterval(() => {
          this.countdown--
          if (this.countdown <= 0) {
            clearInterval(timer)
          }
        }, 1000)
      } catch (err) {
        uni.showToast({ title: err.message || '发送失败', icon: 'none' })
      }
    },
    async handlePasswordLogin() {
      if (!this.username || !this.password || !this.captchaCode) {
        uni.showToast({ title: '请填写完整信息', icon: 'none' })
        return
      }
      
      this.loading = true
      try {
        const res = await userApi.login(
          this.username, 
          this.password, 
          this.captchaKey, 
          this.captchaCode
        )
        
        if (res.token) {
          this.saveUserInfo(res)
          uni.showToast({ title: '登录成功', icon: 'success' })
          
          setTimeout(() => {
            uni.switchTab({ url: '/pages/index/index' })
          }, 1500)
        }
      } catch (err) {
        uni.showToast({
          title: err.message || err.detail || '登录失败',
          icon: 'none'
        })
        this.refreshCaptcha()
      } finally {
        this.loading = false
      }
    },
    async handleEmailLogin() {
      if (!this.email || !this.emailCode || !this.captchaCode) {
        uni.showToast({ title: '请填写完整信息', icon: 'none' })
        return
      }
      
      this.loading = true
      try {
        const res = await userApi.emailLogin(
          this.email, 
          this.emailCode, 
          this.captchaKey, 
          this.captchaCode
        )
        
        if (res.token) {
          this.saveUserInfo(res)
          uni.showToast({ title: '登录成功', icon: 'success' })
          
          setTimeout(() => {
            uni.switchTab({ url: '/pages/index/index' })
          }, 1500)
        }
      } catch (err) {
        uni.showToast({
          title: err.message || err.detail || '登录失败',
          icon: 'none'
        })
        this.refreshCaptcha()
      } finally {
        this.loading = false
      }
    },
    async handleWechatLogin() {
      this.loading = true
      try {
        const loginRes = await uni.login({ provider: 'weixin' })
        if (!loginRes.code) {
          throw new Error('微信登录失败')
        }

        const res = await userApi.wechatLogin(loginRes.code)
        
        if (res.token) {
          this.saveUserInfo(res)
          uni.showToast({ title: '登录成功', icon: 'success' })
          
          setTimeout(() => {
            uni.switchTab({ url: '/pages/index/index' })
          }, 1500)
        }
      } catch (err) {
        uni.showToast({
          title: err.message || '微信登录失败',
          icon: 'none'
        })
      } finally {
        this.loading = false
      }
    },
    saveUserInfo(res) {
      uni.setStorageSync('token', res.token)
      uni.setStorageSync('tokenType', res.token_type || 'bearer')
      uni.setStorageSync('tokenExpire', Date.now() + (res.expires_in * 1000))
      uni.setStorageSync('userInfo', res.user)
    },
    goRegister() {
      uni.navigateTo({ url: '/pages/register/register' })
    },
    goResetPassword() {
      uni.navigateTo({ url: '/pages/reset-password/reset-password' })
    },
    openAgreement(type) {
      uni.showToast({ title: '协议页面开发中', icon: 'none' })
    }
  }
}
</script>

<style lang="scss" scoped>
.login-container {
  min-height: 100vh;
  background: linear-gradient(180deg, #FCF8F0 0%, #FFFFFF 40%);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 120rpx 60rpx 0;
}

.logo-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 60rpx;
}

.logo {
  width: 180rpx;
  height: 180rpx;
  margin-bottom: 30rpx;
}

.app-name {
  font-size: 48rpx;
  font-weight: bold;
  color: var(--color-primary);
  margin-bottom: 16rpx;
}

.app-slogan {
  font-size: 28rpx;
  color: var(--color-text-secondary);
}

.login-tabs {
  display: flex;
  margin-bottom: 40rpx;
  
  .tab-item {
    padding: 20rpx 40rpx;
    font-size: 30rpx;
    color: var(--color-text-secondary);
    position: relative;
    
    &.active {
      color: var(--color-primary);
      font-weight: bold;
      
      &::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 60rpx;
        height: 6rpx;
        background: var(--color-primary);
        border-radius: 3rpx;
      }
    }
  }
}

.login-form {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.input-group {
  width: 100%;
  margin-bottom: 30rpx;
  
  .input {
    width: 100%;
    height: 96rpx;
    background: #FFFFFF;
    border-radius: 16rpx;
    padding: 0 30rpx;
    font-size: 28rpx;
    border: 2rpx solid #DDCFB0;
    color: var(--color-text-primary);
    
    &:focus {
      border-color: var(--color-primary);
    }
  }
}

.captcha-group {
  display: flex;
  align-items: center;
  border: 2rpx solid #DDCFB0;
  border-radius: 16rpx;
  overflow: hidden;
  
  .captcha-input {
    flex: 1;
    height: 96rpx;
    border: none;
    border-radius: 0;
  }
  
  .captcha-img {
    width: 200rpx;
    height: 96rpx;
    background: #FCF8F0;
    border-left: 2rpx solid #DDCFB0;
  }

  .captcha-btn {
    width: 200rpx;
    height: 96rpx;
    background: var(--color-primary);
    color: var(--color-text-inverse);
    font-size: 24rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    border: none;
    border-left: 2rpx solid #4C7048;
    
    &[disabled] {
      background: #DDCFB0;
      color: var(--color-text-secondary);
      border-left-color: #DDCFB0;
    }
  }
}

.extra-links {
  width: 100%;
  display: flex;
  justify-content: space-between;
  margin-bottom: 40rpx;
  padding: 0 10rpx;
  
  .link {
    color: var(--color-primary);
    font-size: 26rpx;
  }
}

.login-btn {
  width: 600rpx;
  height: 96rpx;
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border-radius: 48rpx;
  font-size: 32rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 40rpx;
  
  &[disabled] {
    opacity: 0.6;
  }
  
  &.wechat {
    background: #07C160;
  }
}

.agreement {
  font-size: 24rpx;
  color: var(--color-text-secondary);
  text-align: center;
  margin-top: 40rpx;

  .link {
    color: var(--color-primary);
    margin: 0 4rpx;
  }
}
</style>
