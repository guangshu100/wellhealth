<template>
  <view class="page">
    <view class="card user-card">
      <view class="flex-row gap-sm">
        <view class="avatar">
          <text style="color:#fff;font-size:40rpx;font-weight:600">{{ userName[0] }}</text>
        </view>
        <view class="flex-col gap-xs">
          <text class="text-primary" style="font-size:34rpx;font-weight:600">{{ userName }}</text>
          <text class="tag tag-primary">{{ userRole }}</text>
        </view>
      </view>
    </view>

    <view class="card menu-card">
      <view class="menu-item flex-row flex-between" @tap="navigateTo('/pages/profile/info')">
        <view class="flex-row gap-sm">
          <text>👤</text>
          <text class="text-primary">个人信息</text>
        </view>
        <text class="text-hint">›</text>
      </view>
      <view class="menu-item flex-row flex-between" @tap="navigateTo('/pages/health/index')">
        <view class="flex-row gap-sm">
          <text>📋</text>
          <text class="text-primary">健康档案</text>
        </view>
        <text class="text-hint">›</text>
      </view>
      <view class="menu-item flex-row flex-between" @tap="navigateTo('/pages/medication/index')">
        <view class="flex-row gap-sm">
          <text>💊</text>
          <text class="text-primary">用药记录</text>
        </view>
        <text class="text-hint">›</text>
      </view>
      <view class="menu-item flex-row flex-between" @tap="navigateTo('/pages/cognitive/report')">
        <view class="flex-row gap-sm">
          <text>🧠</text>
          <text class="text-primary">认知报告</text>
        </view>
        <text class="text-hint">›</text>
      </view>
      <view class="menu-item flex-row flex-between" @tap="navigateTo('/pages/family/index')">
        <view class="flex-row gap-sm">
          <text>👨‍👩‍👧‍👦</text>
          <text class="text-primary">家庭管理</text>
        </view>
        <text class="text-hint">›</text>
      </view>
      <view class="menu-item flex-row flex-between" @tap="navigateTo('/pages/profile/settings')">
        <view class="flex-row gap-sm">
          <text>⚙️</text>
          <text class="text-primary">系统设置</text>
        </view>
        <text class="text-hint">›</text>
      </view>
      <view class="menu-item flex-row flex-between" @tap="navigateTo('/pages/profile/about')">
        <view class="flex-row gap-sm">
          <text>ℹ️</text>
          <text class="text-primary">关于我们</text>
        </view>
        <text class="text-hint">›</text>
      </view>
    </view>

    <view class="card">
      <view class="menu-item logout-btn flex-center" @tap="handleLogout">
        <text style="color:var(--color-danger);font-weight:600">退出登录</text>
      </view>
    </view>

    <view v-if="showLogoutDialog" class="dialog-mask" @tap="showLogoutDialog = false">
      <view class="dialog-content" @tap.stop>
        <text class="dialog-title">确认退出</text>
        <text class="text-secondary mb-md">确定要退出登录吗？</text>
        <view class="flex-row gap-sm" style="justify-content:flex-end">
          <view class="btn-secondary" @tap="showLogoutDialog = false"><text>取消</text></view>
          <view class="btn-primary" @tap="confirmLogout"><text style="color:#fff">确定</text></view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const userName = computed(() => authStore.userInfo?.name || authStore.userInfo?.username || '用户')
const userRole = computed(() => {
  const role = authStore.userInfo?.role
  if (role === 'doctor') return '医生'
  if (role === 'admin') return '管理员'
  return '用户'
})

const showLogoutDialog = ref(false)

const navigateTo = (url: string) => {
  uni.navigateTo({ url })
}

const handleLogout = () => {
  showLogoutDialog.value = true
}

const confirmLogout = () => {
  showLogoutDialog.value = false
  authStore.logout()
}
</script>

<style scoped>
.user-card {
  padding: var(--spacing-lg);
}

.avatar {
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  background: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.menu-card {
  padding: 0;
}

.menu-item {
  padding: var(--spacing-md);
  border-bottom: 2rpx solid var(--color-border);
}

.menu-item:last-child {
  border-bottom: none;
}

.logout-btn {
  padding: var(--spacing-md);
}

.dialog-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 999;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dialog-content {
  width: 80%;
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.dialog-title {
  font-size: 34rpx;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-md);
  display: block;
}
</style>
