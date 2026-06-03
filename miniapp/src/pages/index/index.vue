<template>
  <view class="page">
    <view class="welcome-section">
      <view class="welcome-greeting">🏥 你好，{{ auth.userName }}</view>
      <view class="welcome-desc">智能慢病管理，为您的健康保驾护航</view>
    </view>

    <view class="section-title">数据概览</view>
    <view class="stats-grid">
      <view class="card stat-card" v-for="stat in stats" :key="stat.label">
        <view class="stat-icon">{{ stat.icon }}</view>
        <view class="stat-value">{{ stat.value }}</view>
        <view class="stat-label">{{ stat.label }}</view>
      </view>
    </view>

    <view class="section-title">快捷功能</view>
    <view class="actions-grid">
      <view
        class="action-item"
        v-for="action in quickActions"
        :key="action.label"
        @tap="navigateTo(action.path)"
      >
        <view class="action-icon">{{ action.icon }}</view>
        <view class="action-label">{{ action.label }}</view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/utils/api'

const auth = useAuthStore()

const stats = ref([
  { icon: '🤖', label: 'AI咨询次数', value: 0 },
  { icon: '📋', label: '健康记录', value: 0 },
  { icon: '💊', label: '用药提醒', value: 0 },
  { icon: '🧠', label: '认知训练', value: 0 }
])

const quickActions = [
  { icon: '🤖', label: 'AI咨询', path: '/pages/chat/index' },
  { icon: '📊', label: '健康数据', path: '/pages/health/index' },
  { icon: '💊', label: '用药提醒', path: '/pages/medication/index' },
  { icon: '🧠', label: '认知训练', path: '/pages/cognitive/training' },
  { icon: '👨‍👩‍👧', label: '家庭关爱', path: '/pages/family/index' },
  { icon: '🔮', label: '健康预测', path: '/pages/prediction/index' },
  { icon: '📝', label: '处方查询', path: '/pages/prescription/index' },
  { icon: '📚', label: '知识库', path: '/pages/knowledge/index' }
]

const loadStats = async () => {
  try {
    const res: any = await api.get('/admin/stats')
    if (res) {
      stats.value[0].value = res.chat_count ?? res.conversation_count ?? 0
      stats.value[1].value = res.health_record_count ?? res.health_count ?? 0
      stats.value[2].value = res.medication_reminder_count ?? res.medication_count ?? 0
      stats.value[3].value = res.cognitive_training_count ?? res.cognitive_count ?? 0
    }
  } catch {
    stats.value[0].value = 0
    stats.value[1].value = 0
    stats.value[2].value = 0
    stats.value[3].value = 0
  }
}

const navigateTo = (path: string) => {
  uni.navigateTo({ url: path })
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.welcome-section {
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-md);
  color: #ffffff;
}

.welcome-greeting {
  font-size: 36rpx;
  font-weight: 600;
  margin-bottom: var(--spacing-xs);
}

.welcome-desc {
  font-size: 26rpx;
  opacity: 0.85;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-md);
  text-align: center;
}

.stat-icon {
  font-size: 48rpx;
  margin-bottom: var(--spacing-xs);
}

.stat-value {
  font-size: 40rpx;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 4rpx;
}

.stat-label {
  font-size: 24rpx;
  color: var(--color-text-secondary);
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-sm);
}

.action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-md) var(--spacing-xs);
  background: var(--color-bg-card);
  border-radius: var(--radius-md);
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}

.action-icon {
  font-size: 52rpx;
  margin-bottom: var(--spacing-xs);
}

.action-label {
  font-size: 24rpx;
  color: var(--color-text-primary);
}
</style>
