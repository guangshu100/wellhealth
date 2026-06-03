<template>
  <view class="profile-page">
    <!-- 用户信息头部 -->
    <view class="user-header" @click="goToLogin">
      <view class="avatar">
        <text class="avatar-text">{{ userInfo.name ? userInfo.name.slice(0, 1) : '未登录' }}</text>
      </view>
      <view class="user-info">
        <text class="username">{{ userInfo.name || '点击登录' }}</text>
        <text class="user-role" v-if="userInfo.role">{{ getRoleName(userInfo.role) }}</text>
      </view>
    </view>

    <!-- 健康数据卡片 -->
    <view class="health-cards">
      <view class="health-card" @click="navigateTo('/pages/health/health')">
        <text class="card-icon">💊</text>
        <text class="card-title">健康档案</text>
      </view>
      <view class="health-card" @click="navigateTo('/pages/prescription/prescription')">
        <text class="card-icon">📋</text>
        <text class="card-title">处方查询</text>
      </view>
      <view class="health-card" @click="navigateTo('/pages/report/report')">
        <text class="card-icon">📊</text>
        <text class="card-title">体检报告</text>
      </view>
    </view>

    <!-- 功能菜单 -->
    <view class="menu-section">
      <view class="menu-title">功能服务</view>
      <view class="menu-list">
        <view class="menu-item" @click="navigateTo('/pages/reminder/reminder')">
          <text class="menu-icon">⏰</text>
          <text class="menu-text">用药提醒</text>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-item" @click="navigateTo('/pages/chat/chat')">
          <text class="menu-icon">💬</text>
          <text class="menu-text">AI咨询</text>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-item" @click="navigateTo('/pages/family/family')">
          <text class="menu-icon">👨‍👩‍👧</text>
          <text class="menu-text">亲情账号</text>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-item" @click="navigateTo('/pages/health-data/health-data')">
          <text class="menu-icon">📈</text>
          <text class="menu-text">健康数据</text>
          <text class="menu-arrow">›</text>
        </view>
      </view>
    </view>

    <!-- 设置菜单 -->
    <view class="menu-section">
      <view class="menu-title">设置</view>
      <view class="menu-list">
        <view class="menu-item" @click="switchTheme">
          <text class="menu-icon">🎨</text>
          <text class="menu-text">切换主题</text>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-item" @click="showComingSoon">
          <text class="menu-icon">⚙️</text>
          <text class="menu-text">个人设置</text>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-item" @click="showComingSoon">
          <text class="menu-icon">🔔</text>
          <text class="menu-text">通知设置</text>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-item" @click="showComingSoon">
          <text class="menu-icon">❓</text>
          <text class="menu-text">帮助与反馈</text>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-item" @click="showComingSoon">
          <text class="menu-icon">ℹ️</text>
          <text class="menu-text">关于我们</text>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-item logout" @click="handleLogout" v-if="isLoggedIn">
          <text class="menu-icon">🚪</text>
          <text class="menu-text">退出登录</text>
          <text class="menu-arrow">›</text>
        </view>
      </view>
    </view>

    <!-- 版本信息 -->
    <view class="version-info">
      <text>康伴健康 v1.0.0</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { userApi } from '@/utils/api'
import { getThemeId, getTheme, getThemeCSS } from '@/utils/theme'

const userInfo = ref<{
  name: string
  role: string
  phone: string
  email: string
}>({
  name: '',
  role: '',
  phone: '',
  email: ''
})

const isLoggedIn = ref(false)

onShow(() => {
  loadUserInfo()
  applyCurrentTheme()
})

function applyCurrentTheme() {
  const themeId = getThemeId()
  const theme = getTheme(themeId)

  // 小程序端：通过事件通知页面更新主题
  // 不直接操作页面栈，避免getCurrentPages不可用的问题
  uni.$emit('themeChanged', { themeId, theme: theme.colors })
}

function loadUserInfo() {
  const token = uni.getStorageSync('token')
  const storedUserInfo = uni.getStorageSync('userInfo')
  
  isLoggedIn.value = !!token
  
  if (storedUserInfo) {
    userInfo.value = storedUserInfo
  } else if (token) {
    fetchUserInfo()
  }
}

async function fetchUserInfo() {
  try {
    const res = await userApi.getUserInfo()
    userInfo.value = res
    uni.setStorageSync('userInfo', res)
  } catch (e) {
    console.error('获取用户信息失败', e)
  }
}

function getRoleName(role: string): string {
  const roleMap: Record<string, string> = {
    admin: '管理员',
    doctor: '医生',
    patient: '患者',
    family: '家属'
  }
  return roleMap[role] || role
}

function goToLogin() {
  if (!isLoggedIn.value) {
    uni.navigateTo({
      url: '/pages/login/login'
    })
  }
}

function navigateTo(url: string) {
  uni.navigateTo({
    url
  })
}

function showComingSoon() {
  uni.showToast({
    title: '功能开发中',
    icon: 'none'
  })
}

function switchTheme() {
  const themeList = [
    { id: 'sagegreen', name: '鼠尾草绿' },
    { id: 'mistblue', name: '柔雾蓝' },
    { id: 'cypress', name: '浅杉绿' }
  ]
  const itemList = themeList.map(t => t.name)

  uni.showActionSheet({
    itemList,
    success: (res) => {
      const themeId = themeList[res.tapIndex].id
      const theme = getTheme(themeId)

      // 保存主题
      uni.setStorageSync('app-theme', themeId)

      // 通过事件通知所有页面更新主题
      uni.$emit('themeChanged', { themeId, theme: theme.colors })

      uni.showToast({
        title: `已切换为${theme.name}主题`,
        icon: 'success'
      })
    }
  })
}

function handleLogout() {
  uni.showModal({
    title: '提示',
    content: '确定要退出登录吗？',
    success: (res) => {
      if (res.confirm) {
        uni.removeStorageSync('token')
        uni.removeStorageSync('tokenType')
        uni.removeStorageSync('tokenExpire')
        uni.removeStorageSync('userInfo')
        
        userInfo.value = {
          name: '',
          role: '',
          phone: '',
          email: ''
        }
        isLoggedIn.value = false
        
        uni.showToast({
          title: '已退出登录',
          icon: 'success'
        })
        
        setTimeout(() => {
          uni.reLaunch({
            url: '/pages/login/login'
          })
        }, 1000)
      }
    }
  })
}
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  background: var(--color-bg-page);
  padding-bottom: 120rpx;
}

.user-header {
  display: flex;
  align-items: center;
  padding: 60rpx 40rpx 40rpx;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
}

.avatar {
  width: 120rpx;
  height: 120rpx;
  border-radius: 60rpx;
  background-color: rgba(255, 255, 255, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 30rpx;
}

.avatar-text {
  font-size: 48rpx;
  color: #fff;
  font-weight: bold;
}

.user-info {
  display: flex;
  flex-direction: column;
}

.username {
  font-size: 36rpx;
  color: #fff;
  font-weight: bold;
  margin-bottom: 10rpx;
}

.user-role {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.8);
}

.health-cards {
  display: flex;
  justify-content: space-around;
  padding: 30rpx 20rpx;
  background-color: #FFFFFF;
  margin-bottom: 20rpx;
}

.health-card {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.card-icon {
  font-size: 48rpx;
  margin-bottom: 10rpx;
}

.card-title {
  font-size: 24rpx;
  color: var(--color-text-primary);
}

.menu-section {
  background-color: #FFFFFF;
  margin-bottom: 20rpx;
}

.menu-title {
  padding: 30rpx 40rpx 20rpx;
  font-size: 28rpx;
  color: var(--color-text-secondary);
}

.menu-list {
  padding: 0 40rpx;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 30rpx 0;
  border-bottom: 1rpx solid #eee;
}

.menu-item:last-child {
  border-bottom: none;
}

.menu-item.logout .menu-text {
  color: var(--color-danger);
}

.menu-icon {
  font-size: 40rpx;
  margin-right: 20rpx;
}

.menu-text {
  flex: 1;
  font-size: 30rpx;
  color: var(--color-text-primary);
}

.menu-arrow {
  font-size: 36rpx;
  color: var(--color-text-secondary);
}

.version-info {
  text-align: center;
  padding: 40rpx;
  color: var(--color-text-secondary);
  font-size: 24rpx;
}
</style>
