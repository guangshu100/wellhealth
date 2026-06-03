<template>
  <view class="page">
    <!-- 新建对话按钮 -->
    <view class="new-chat-section">
      <view class="new-chat-btn" @click="createNewChat">
        <text class="btn-icon">✚</text>
        <text class="btn-text">新建对话</text>
      </view>
    </view>

    <!-- 会话列表 -->
    <scroll-view
      scroll-y
      class="session-list"
      refresher-enabled
      :refresher-triggered="refreshing"
      @refresherrefresh="onRefresh"
      v-if="sessions.length > 0"
    >
      <view
        class="session-item"
        v-for="session in sessions"
        :key="session.id"
        @click="openSession(session)"
      >
        <view class="session-icon">
          <text>{{ getModeIcon(session.agent_type) }}</text>
        </view>
        <view class="session-info">
          <text class="session-title">{{ session.title || '未命名对话' }}</text>
          <view class="session-meta">
            <text class="meta-item">{{ getModeName(session.agent_type) }}</text>
            <text class="meta-divider">·</text>
            <text class="meta-item">{{ session.message_count || 0 }}条消息</text>
            <text class="meta-divider">·</text>
            <text class="meta-item">{{ formatTime(session.updated_at) }}</text>
          </view>
        </view>
        <view class="session-actions">
          <view class="action-btn" @click.stop="deleteSession(session)">
            <text>🗑️</text>
          </view>
        </view>
      </view>
    </scroll-view>

    <!-- 空状态 -->
    <view class="empty-state" v-else-if="!loading">
      <text class="empty-icon">💬</text>
      <text class="empty-title">暂无对话记录</text>
      <text class="empty-desc">点击上方按钮开始新对话</text>
    </view>

    <!-- 加载状态 -->
    <view class="loading-state" v-if="loading">
      <text class="loading-text">加载中...</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { chatApi } from '@/utils/api'

interface Session {
  id: string
  patient_id?: string
  agent_type: 'single' | 'multi' | 'dialogue'
  title?: string
  status: string
  message_count: number
  created_at: string
  updated_at: string
}

const sessions = ref<Session[]>([])
const loading = ref(false)
const refreshing = ref(false)

// 页面首次加载
onMounted(async () => {
  console.log('chat-list onMounted')
  await loadSessions()
})

// 页面每次显示时都重新加载（重要！）
onShow(async () => {
  console.log('chat-list onShow')
  await loadSessions()
})

const loadSessions = async () => {
  // 避免重复加载
  if (loading.value) {
    console.log('Already loading, skip...')
    return
  }

  loading.value = true
  try {
    console.log('=== Loading sessions ===')
    console.log('BASE_URL:', 'http://localhost:8000/api/v1')
    console.log('Calling chatApi.getSessions...')

    const token = uni.getStorageSync('token')
    console.log('Token:', token ? 'exists' : 'none')

    const res = await chatApi.getSessions(undefined, 50)

    console.log('=== Sessions API response ===')
    console.log('Response:', JSON.stringify(res, null, 2))
    console.log('Sessions count:', res.sessions?.length || 0)

    sessions.value = res.sessions || []

    // 按更新时间排序（最新的在前）
    sessions.value.sort((a, b) => {
      const timeA = new Date(a.updated_at).getTime()
      const timeB = new Date(b.updated_at).getTime()
      return timeB - timeA
    })

    console.log('Sorted sessions:', sessions.value.length)
  } catch (e) {
    console.error('=== Load sessions failed ===')
    console.error('Error:', e)
    uni.showToast({ title: '加载失败，请重试', icon: 'none' })
  } finally {
    loading.value = false
    console.log('Loading finished, loading.value =', loading.value)
  }
}

const onRefresh = async () => {
  refreshing.value = true
  try {
    await loadSessions()
  } finally {
    refreshing.value = false
  }
}

const createNewChat = async () => {
  try {
    const res = await chatApi.createSession()

    // 跳转到聊天页面
    uni.navigateTo({
      url: `/pages/chat/chat?sessionId=${res.session_id}&mode=single`
    })
  } catch (e) {
    console.error('创建会话失败:', e)
    uni.showToast({ title: '创建失败', icon: 'none' })
  }
}

const openSession = async (session: Session) => {
  try {
    // 保存当前会话ID
    uni.setStorageSync('current_session_id', session.id)

    // 跳转到聊天页面
    uni.navigateTo({
      url: `/pages/chat/chat?sessionId=${session.id}&mode=${session.agent_type}`
    })
  } catch (e) {
    console.error('打开会话失败:', e)
  }
}

const deleteSession = async (session: Session) => {
  uni.showModal({
    title: '确认删除',
    content: '确定要删除这个对话吗？',
    success: async (res) => {
      if (res.confirm) {
        try {
          await chatApi.deleteSession(session.id)
          uni.showToast({ title: '删除成功', icon: 'success' })
          await loadSessions()
        } catch (e) {
          console.error('删除会话失败:', e)
          uni.showToast({ title: '删除失败', icon: 'none' })
        }
      }
    }
  })
}

const getModeIcon = (type: string): string => {
  const icons: Record<string, string> = {
    single: '🤖',
    multi: '🤝',
    dialogue: '💬'
  }
  return icons[type] || '🤖'
}

const getModeName = (type: string): string => {
  const names: Record<string, string> = {
    single: '单Agent',
    multi: '多Agent会诊',
    dialogue: '专家对话'
  }
  return names[type] || '单Agent'
}

const formatTime = (time: string): string => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  // 小于1小时
  if (diff < 3600000) {
    const minutes = Math.floor(diff / 60000)
    return minutes <= 1 ? '刚刚' : `${minutes}分钟前`
  }
  
  // 小于24小时
  if (diff < 86400000) {
    const hours = Math.floor(diff / 3600000)
    return `${hours}小时前`
  }
  
  // 小于7天
  if (diff < 604800000) {
    const days = Math.floor(diff / 86400000)
    return `${days}天前`
  }
  
  // 其他显示日期
  return `${date.getMonth() + 1}/${date.getDate()}`
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--color-bg-page);
  padding: 20rpx;
  padding-top: 30rpx;  /* 增加顶部间距 */
}

/* 新建对话区域 */
.new-chat-section {
  margin-bottom: 20rpx;
}

.new-chat-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  padding: 24rpx;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
  border-radius: 16rpx;
  color: #FFFFFF;
  box-shadow: 0 4rpx 12rpx rgba(94, 139, 90, 0.2);
}

.new-chat-btn:active {
  transform: scale(0.98);
  opacity: 0.9;
}

.btn-icon {
  font-size: 32rpx;
}

.btn-text {
  font-size: 28rpx;
  font-weight: 500;
}

/* 会话列表 */
.session-list {
  height: calc(100vh - 220rpx);  /* 调整高度 */
}

.session-item {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 24rpx;
  background: #FFFFFF;
  border-radius: 16rpx;
  margin-bottom: 20rpx;
  border: 1rpx solid var(--color-border-light);
  transition: all 0.3s;
}

.session-item:active {
  background: var(--color-bg-hover);
  transform: scale(0.98);
}

.session-icon {
  width: 80rpx;
  height: 80rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-card);
  border-radius: 50%;
  font-size: 40rpx;
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-title {
  display: block;
  font-size: 30rpx;
  color: var(--color-text-primary);
  font-weight: 500;
  margin-bottom: 8rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-meta {
  display: flex;
  align-items: center;
  gap: 8rpx;
  font-size: 22rpx;
  color: var(--color-text-secondary);
}

.meta-divider {
  opacity: 0.5;
}

.session-actions {
  display: flex;
  gap: 16rpx;
}

.action-btn {
  width: 60rpx;
  height: 60rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--color-bg-card);
  font-size: 28rpx;
}

.action-btn:active {
  background: var(--color-bg-hover);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80rpx 60rpx;
  background: #FFFFFF;
  border-radius: 16rpx;
}

.empty-icon {
  font-size: 100rpx;
  margin-bottom: 30rpx;
  opacity: 0.6;
}

.empty-title {
  font-size: 30rpx;
  color: var(--color-text-primary);
  font-weight: 500;
  margin-bottom: 12rpx;
}

.empty-desc {
  font-size: 26rpx;
  color: var(--color-text-secondary);
  text-align: center;
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 100rpx 0;
}

.loading-text {
  font-size: 28rpx;
  color: var(--color-text-secondary);
}
</style>
