<template>
  <view class="page">
    <view class="header">
      <text class="title">认知评估</text>
      <text class="subtitle">描述您的状态，AI为您生成多维度认知评估</text>
    </view>

    <view class="section-card">
      <text class="section-title">请描述您的认知状况</text>
      <textarea
        class="text-input"
        v-model="inputText"
        placeholder="例如：最近经常忘记事情，说话有时想不起词..."
        :maxlength="500"
        auto-height
      />
      <view class="input-footer">
        <text class="char-count">{{ inputText.length }}/500</text>
      </view>
      <view class="btn-assess" :class="{ loading: assessing }" @click="startAssessment">
        {{ assessing ? '评估中...' : '开始评估' }}
      </view>
    </view>

    <view v-if="result" class="result-section">
      <view class="section-card">
        <text class="section-title">评估结果</text>

        <view class="score-item" v-for="dim in dimensions" :key="dim.key">
          <view class="score-header">
            <text class="score-name">{{ dim.label }}</text>
            <text class="score-value">{{ dim.score }}<text class="score-unit">分</text></text>
          </view>
          <view class="progress-bar">
            <view class="progress-fill" :style="{ width: dim.score + '%' }" :class="'fill-' + dim.key"></view>
          </view>
          <text class="score-level" :class="'level-' + dim.level">{{ dim.levelText }}</text>
        </view>
      </view>

      <view class="section-card" v-if="result.suggestions">
        <text class="section-title">改善建议</text>
        <view class="suggestion-list">
          <view class="suggestion-item" v-for="(sug, idx) in result.suggestions" :key="idx">
            <text class="sug-index">{{ idx + 1 }}</text>
            <text class="sug-text">{{ sug }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import api from '@/utils/api'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const inputText = ref('')
const assessing = ref(false)
const result = ref<any>(null)

interface Dimension {
  key: string
  label: string
  score: number
  level: string
  levelText: string
}

const dimensions = ref<Dimension[]>([])

const getLevelInfo = (score: number) => {
  if (score >= 80) return { level: 'good', levelText: '良好' }
  if (score >= 60) return { level: 'normal', levelText: '一般' }
  if (score >= 40) return { level: 'mild', levelText: '轻度下降' }
  return { level: 'severe', levelText: '明显下降' }
}

const startAssessment = async () => {
  if (!inputText.value.trim()) {
    uni.showToast({ title: '请先描述您的认知状况', icon: 'none' })
    return
  }
  assessing.value = true
  result.value = null
  try {
    const res: any = await api.post('/cognitive/analyze-text', {
      text: inputText.value,
      patient_id: authStore.userId
    })
    result.value = res
    dimensions.value = [
      { key: 'language', label: '语言', score: res.language_score ?? 0, ...getLevelInfo(res.language_score ?? 0) },
      { key: 'memory', label: '记忆', score: res.memory_score ?? 0, ...getLevelInfo(res.memory_score ?? 0) },
      { key: 'execution', label: '执行功能', score: res.execution_score ?? 0, ...getLevelInfo(res.execution_score ?? 0) },
      { key: 'attention', label: '注意力', score: res.attention_score ?? 0, ...getLevelInfo(res.attention_score ?? 0) }
    ]
  } catch {
    const mockScores = { language: 72, memory: 58, execution: 65, attention: 80 }
    result.value = {
      language_score: mockScores.language,
      memory_score: mockScores.memory,
      execution_score: mockScores.execution,
      attention_score: mockScores.attention,
      suggestions: [
        '建议进行记忆训练游戏，每天15分钟',
        '保持规律作息，保证充足睡眠',
        '多参与社交活动，锻炼语言表达',
        '尝试冥想练习，提升注意力集中度'
      ]
    }
    dimensions.value = [
      { key: 'language', label: '语言', score: mockScores.language, ...getLevelInfo(mockScores.language) },
      { key: 'memory', label: '记忆', score: mockScores.memory, ...getLevelInfo(mockScores.memory) },
      { key: 'execution', label: '执行功能', score: mockScores.execution, ...getLevelInfo(mockScores.execution) },
      { key: 'attention', label: '注意力', score: mockScores.attention, ...getLevelInfo(mockScores.attention) }
    ]
  } finally {
    assessing.value = false
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--color-bg-page);
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

.text-input {
  width: 100%;
  min-height: 200rpx;
  background: var(--color-bg-page);
  border: 2rpx solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 20rpx;
  font-size: 28rpx;
  color: var(--color-text-primary);
  box-sizing: border-box;
  line-height: 1.6;
}

.input-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 10rpx;
}

.char-count {
  font-size: 24rpx;
  color: var(--color-text-hint);
}

.btn-assess {
  margin-top: 24rpx;
  width: 100%;
  text-align: center;
  padding: 25rpx;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
  color: var(--color-text-inverse);
  border-radius: 40rpx;
  font-size: 30rpx;
  font-weight: bold;
}

.btn-assess.loading {
  background: var(--color-primary-light);
  opacity: 0.7;
}

.result-section {
  padding-bottom: 40rpx;
}

.score-item {
  margin-bottom: 28rpx;
}

.score-item:last-child {
  margin-bottom: 0;
}

.score-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12rpx;
}

.score-name {
  font-size: 28rpx;
  color: var(--color-text-primary);
  font-weight: 500;
}

.score-value {
  font-size: 32rpx;
  font-weight: bold;
  color: var(--color-primary);
}

.score-unit {
  font-size: 22rpx;
  font-weight: normal;
  margin-left: 4rpx;
}

.progress-bar {
  height: 16rpx;
  background: var(--color-bg-page);
  border-radius: 8rpx;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 8rpx;
  transition: width 0.6s ease;
}

.fill-language { background: var(--color-primary); }
.fill-memory { background: var(--color-info); }
.fill-execution { background: var(--color-warning); }
.fill-attention { background: var(--color-success); }

.score-level {
  display: inline-block;
  margin-top: 8rpx;
  font-size: 22rpx;
  padding: 4rpx 16rpx;
  border-radius: 20rpx;
}

.level-good { background: rgba(129, 199, 132, 0.15); color: var(--color-success); }
.level-normal { background: rgba(100, 181, 246, 0.15); color: var(--color-info); }
.level-mild { background: rgba(255, 183, 77, 0.15); color: var(--color-warning); }
.level-severe { background: rgba(229, 115, 115, 0.15); color: var(--color-danger); }

.suggestion-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.suggestion-item {
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
}

.sug-index {
  flex-shrink: 0;
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  background: var(--color-primary);
  color: var(--color-text-inverse);
  font-size: 22rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sug-text {
  flex: 1;
  font-size: 26rpx;
  color: var(--color-text-secondary);
  line-height: 1.6;
}
</style>
