<template>
  <view class="register-container">
    <view class="header">
      <text class="title">注册账号</text>
      <text class="subtitle">加入康伴健康</text>
    </view>

    <view class="form">
      <view class="input-group">
        <input 
          class="input" 
          v-model="name" 
          placeholder="请输入昵称"
        />
      </view>
      
      <view class="input-group">
        <input 
          class="input" 
          v-model="email" 
          type="text" 
          placeholder="请输入邮箱"
        />
      </view>
      
      <view class="input-group captcha-group">
        <input 
          class="input captcha-input" 
          v-model="code" 
          type="text" 
          placeholder="请输入邮箱验证码" 
          maxlength="6" 
        />
        <button 
          class="captcha-btn" 
          @click="sendCode" 
          :disabled="countdown > 0"
        >
          {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
        </button>
      </view>
      
      <view class="input-group">
        <input 
          class="input" 
          v-model="password" 
          type="password" 
          placeholder="请输入密码 (至少6位)"
        />
      </view>
      
      <view class="input-group">
        <input 
          class="input" 
          v-model="confirmPassword" 
          type="password" 
          placeholder="请再次输入密码"
        />
      </view>
      
      <button 
        class="register-btn" 
        type="primary" 
        @click="handleRegister" 
        :loading="loading"
        :disabled="!canRegister"
      >
        <text v-if="!loading">注册</text>
        <text v-else>注册中...</text>
      </button>
    </view>

    <view class="footer">
      <text>已有账号？</text>
      <text class="link" @click="goLogin">立即登录</text>
    </view>
  </view>
</template>

<script>
import { emailCodeApi } from '@/utils/api'

export default {
  data() {
    return {
      name: '',
      email: '',
      code: '',
      password: '',
      confirmPassword: '',
      loading: false,
      countdown: 0
    }
  },
  computed: {
    canRegister() {
      return this.name.length > 0 && 
             this.email.length > 0 && 
             this.code.length > 0 && 
             this.password.length >= 6 &&
             this.password === this.confirmPassword
    }
  },
  methods: {
    async sendCode() {
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
        await emailCodeApi.sendCode(this.email, 'register')
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
    async handleRegister() {
      if (!this.canRegister) {
        if (this.password !== this.confirmPassword) {
          uni.showToast({ title: '两次输入密码不一致', icon: 'none' })
        } else if (this.password.length < 6) {
          uni.showToast({ title: '密码长度至少6位', icon: 'none' })
        }
        return
      }
      
      this.loading = true
      try {
        const res = await emailCodeApi.registerWithEmail({
          email: this.email,
          code: this.code,
          password: this.password,
          name: this.name
        })
        
        if (res.token) {
          uni.setStorageSync('token', res.token)
          uni.setStorageSync('tokenType', res.token_type || 'bearer')
          uni.setStorageSync('userInfo', res.user)
          
          uni.showToast({ title: '注册成功', icon: 'success' })
          
          setTimeout(() => {
            uni.switchTab({ url: '/pages/index/index' })
          }, 1500)
        }
      } catch (err) {
        uni.showToast({
          title: err.message || err.detail || '注册失败',
          icon: 'none'
        })
      } finally {
        this.loading = false
      }
    },
    goLogin() {
      uni.navigateBack()
    }
  }
}
</script>

<style lang="scss" scoped>
.register-container {
  min-height: 100vh;
  background: linear-gradient(180deg, #FCF8F0 0%, #FFFFFF 40%);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80rpx 60rpx 0;
}

.header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 60rpx;
}

.title {
  font-size: 48rpx;
  font-weight: bold;
  color: var(--color-primary);
  margin-bottom: 16rpx;
}

.subtitle {
  font-size: 28rpx;
  color: var(--color-text-secondary);
}

.form {
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

.register-btn {
  width: 600rpx;
  height: 96rpx;
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border-radius: 48rpx;
  font-size: 32rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 20rpx;
  
  &[disabled] {
    opacity: 0.6;
  }
}

.footer {
  display: flex;
  margin-top: 40rpx;
  font-size: 28rpx;
  color: var(--color-text-secondary);

  .link {
    color: var(--color-primary);
    margin-left: 10rpx;
  }
}
</style>
