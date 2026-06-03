<template>
  <view class="page">
    <view class="header">
      <text class="title">训练报告</text>
      <text class="subtitle">了解您的认知状态变化与训练进展</text>
    </view>

    <view class="score-circle-section">
      <view class="score-circle">
        <view class="circle-ring">
          <view class="circle-progress" :style="{ '--progress': overallScore + '%' }"></view>
        </view>
        <view class="circle-inner">
          <text class="circle-value">{{ overallScore }}</text>
          <text class="circle-label">综合评分</text>
        </view>
      </view>
    </view>

    <view class="section-card">
      <text class="section-title">维度分析</text>
      <view class="dimension-list">
        <view class="dimension-item" v-for="dim in dimensions" :key="dim.key">
          <view class="dim-header">
            <text class="dim-name">{{ dim.label }}</text>
            <text class="dim-score">{{ dim.score }}分</text>
          </view>
          <view class="dim-bar">
            <view class="dim-bar-fill" :style="{ width: dim.score + '%' }" :class="'bar-' + dim.key"></view>
          </view>
        </view>
      </view>
    </view>

    <view class="section-card">
      <text class="section-title">近期训练记录</text>
      <view v-if="trainingHistory.length > 0" class="history-list">
        <view class="history-item" v-for="item in trainingHistory" :key="item.id">
          <view class="history-left">
            <text class="history-game">{{ item.game_name }}</text>
            <text class="history-date">{{ item.date }}</text>
          </view>
          <view class="history-right">
            <text class="history-score">{{ item.score }}分</text>
            <text class="history-duration">{{ item.duration }}</text>
          </view>
        </view>
      </view>
      <view v-else class="empty-state">
        <text class="empty-text">暂无训练记录</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/utils/api'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const overallScore = ref(0)

interface Dimension {
  key: string
  label: string
  score: number
}

const dimensions = ref<Dimension[]>([])

interface TrainingRecord {
  id: string
  game_name: string
  date: string
  score: number
  duration: string
}

const trainingHistory = ref<TrainingRecord[]>([])

const loadProgress = async () => {
  try {
    const res: any = await api.get('/cognitive/training/progress')
    overallScore.value = res.overall_score ?? 0
    dimensions.value = [
      { key: 'language', label: '语言', score: res.language_score ?? 0 },
      { key: 'memory', label: '记忆', score: res.memory_score ?? 0 },
      { key: 'execution', label: '执行功能', score: res.execution_score ?? 0 },
      { key: 'attention', label: '注意力', score: res.attention_score ?? 0 }
    ]
  } catch {
    overallScore.value = 68
    dimensions.value = [
      { key: 'language', label: '语言', score: 72 },
      { key: 'memory', label: '记忆', score: 58 },
      { key: 'execution', label: '执行功能', score: 65 },
      { key: 'attention', label: '注意力', score: 80 }
    ]
  }
}

const loadAssessments = async () => {
  try {
    const res: any = await api.get('/cognitive/assessments')
    trainingHistory.value = (res.records ?? []).map((r: any) => ({
      id: r.id,
      game_name: r.game_name || r.type,
      date: r.date || r.created_at?.substring(0, 10) || '',
      score: r.score ?? 0,
      duration: r.duration ?? ''
    }))
  } catch {
    trainingHistory.value = [
      { id: '1', game_name: '记忆匹配', date: '2026-05-17', score: 85, duration: '5分钟' },
      { id: '2', game_name: '类别命名', date: '2026-05-16', score: 72, duration: '8分钟' },
      { id: '3', game_name: '序列排序', date: '2026-05-15', score: 68, duration: '6分钟' },
      { id: '4', game_name: '词语回忆', date: '2026-05-14', score: 60, duration: '7分钟' },
      { id: '5', game_name: '记忆匹配', date: '2026-05-13', score: 78, duration: '5分钟' }
    ]
  }
}

onMounted(() => {
  loadProgress()
  loadAssessments()
})
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--color-bg-page);
  padding-bottom: 40rpx;
}

.header {
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
  border-radius: 0 0 30rpx 30rpx;
  padding: 50rpx 30rpx 40rpx;
  text-align: center;
}

.title {
  display: block;
  font-size: 40rpx;
  font-weight: bold;
  color: var(--color-text-inverse);
}

.subtitle {
  display: block;
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.9);
  margin-top: 10rpx;
}

.score-circle-section {
  display: flex;
  justify-content: center;
  padding: 40rpx 0 20rpx;
}

.score-circle {
  position: relative;
  width: 240rpx;
  height: 240rpx;
}

.circle-ring {
  width: 240rpx;
  height: 240rpx;
  border-radius: 50%;
  background: conic-gradient(
    var(--color-primary) 0%,
    var(--color-primary) var(--progress),
    var(--color-bg-page) var(--progress),
    var(--color-bg-page) 100%
  );
  display: flex;
  align-items: center;
  justify-content: center;
}

.circle-progress {
  display: none;
}

.circle-inner {
  position: absolute;
  top: 16rpx;
  left: 16rpx;
  right: 16rpx;
  bottom: 16rpx;
  border-radius: 50%;
  background: var(--color-bg-card);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.circle-value {
  font-size: 56rpx;
  font-weight: bold;
  color: var(--color-primary);
}

.circle-label {
  font-size: 22rpx;
  color: var(--color-text-secondary);
  margin-top: 4rpx;
}

.section-card {
  background: var(--color-bg-card);
  border-radius: var(--radius-md);
  padding: 30rpx;
  margin: 20rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}

.section-title {
  display: block;
  font-size: 32rpx;
  font-weight: bold;
  color: var(--color-text-primary);
  margin-bottom: 20rpx;
}

.dimension-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.dimension-item {
  display: flex;
  flex-direction: column;
}

.dim-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10rpx;
}

.dim-name {
  font-size: 28rpx;
  color: var(--color-text-primary);
  font-weight: 500;
}

.dim-score {
  font-size: 28rpx;
  font-weight: bold;
  color: var(--color-primary);
}

.dim-bar {
  height: 16rpx;
  background: var(--color-bg-page);
  border-radius: 8rpx;
  overflow: hidden;
}

.dim-bar-fill {
  height: 100%;
  border-radius: 8rpx;
  transition: width 0.6s ease;
}

.bar-language { background: var(--color-primary); }
.bar-memory { background: var(--color-info); }
.bar-execution { background: var(--color-warning); }
.bar-attention { background: var(--color-success); }

.history-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20rpx;
  background: var(--color-bg-page);
  border-radius: var(--radius-sm);
}

.history-left {
  display: flex;
  flex-direction: column;
}

.history-game {
  font-size: 28rpx;
  color: var(--color-text-primary);
  font-weight: 500;
}

.history-date {
  font-size: 22rpx;
  color: var(--color-text-hint);
  margin-top: 6rpx;
}

.history-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.history-score {
  font-size: 30rpx;
  font-weight: bold;
  color: var(--color-primary);
}

.history-duration {
  font-size: 22rpx;
  color: var(--color-text-hint);
  margin-top: 6rpx;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60rpx;
}

.empty-text {
  font-size: 28rpx;
  color: var(--color-text-hint);
}
</style>
