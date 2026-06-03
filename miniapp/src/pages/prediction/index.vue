<template>
  <view class="page">
    <view class="card">
      <text class="section-title">健康预测</text>
      <view class="type-selector flex-row gap-sm">
        <view
          v-for="item in predictionTypes"
          :key="item.value"
          class="type-item"
          :class="{ active: activeType === item.value }"
          @tap="switchType(item.value)"
        >
          <text>{{ item.icon }} {{ item.label }}</text>
        </view>
      </view>
    </view>

    <view v-if="loading" class="flex-center mt-md">
      <text class="text-hint">分析中...</text>
    </view>

    <view v-if="!loading && prediction" class="card">
      <view class="flex-row flex-between mb-md">
        <text class="section-title">{{ currentTypeLabel }}</text>
        <view class="tag" :class="getRiskClass(prediction.risk_level)">{{ formatRiskLevel(prediction.risk_level) }}</view>
      </view>

      <view v-if="prediction.probability !== undefined" class="risk-section mb-md">
        <text class="text-secondary mb-sm">风险概率</text>
        <view class="risk-bar">
          <view class="risk-fill" :style="{ width: (prediction.probability * 100) + '%', background: getRiskColor(prediction.risk_level) }" />
        </view>
        <text class="risk-value" :style="{ color: getRiskColor(prediction.risk_level) }">{{ (prediction.probability * 100).toFixed(1) }}%</text>
      </view>

      <view v-if="prediction.trend" class="info-row flex-row mb-sm">
        <text class="text-hint" style="width:140rpx">趋势</text>
        <text class="text-primary">{{ prediction.trend }}</text>
      </view>

      <view v-if="prediction.factors && prediction.factors.length > 0" class="mb-md">
        <text class="text-primary mb-sm" style="font-weight:600">影响因素</text>
        <view v-for="(factor, idx) in prediction.factors" :key="idx" class="factor-item">
          <text class="text-secondary">• {{ factor }}</text>
        </view>
      </view>

      <view v-if="prediction.recommendations && prediction.recommendations.length > 0">
        <text class="text-primary mb-sm" style="font-weight:600">健康建议</text>
        <view v-for="(rec, idx) in prediction.recommendations" :key="idx" class="rec-item">
          <view class="flex-row gap-xs">
            <text class="tag tag-primary" style="min-width:40rpx;text-align:center">{{ idx + 1 }}</text>
            <text class="text-secondary" style="flex:1">{{ rec }}</text>
          </view>
        </view>
      </view>

      <view v-if="prediction.predicted_effect" class="mt-md">
        <text class="text-primary mb-sm" style="font-weight:600">预测效果</text>
        <view v-if="prediction.predicted_effect.blood_sugar_change !== undefined" class="info-row flex-row mb-sm">
          <text class="text-hint" style="width:200rpx">血糖变化</text>
          <text class="text-primary">{{ prediction.predicted_effect.blood_sugar_change > 0 ? '+' : '' }}{{ prediction.predicted_effect.blood_sugar_change }}</text>
        </view>
        <view v-if="prediction.predicted_effect.blood_pressure_change !== undefined" class="info-row flex-row mb-sm">
          <text class="text-hint" style="width:200rpx">血压变化</text>
          <text class="text-primary">{{ prediction.predicted_effect.blood_pressure_change > 0 ? '+' : '' }}{{ prediction.predicted_effect.blood_pressure_change }}</text>
        </view>
        <view v-if="prediction.predicted_effect.confidence !== undefined" class="info-row flex-row mb-sm">
          <text class="text-hint" style="width:200rpx">置信度</text>
          <text class="text-primary">{{ (prediction.predicted_effect.confidence * 100).toFixed(1) }}%</text>
        </view>
      </view>
    </view>

    <view v-if="!loading && !prediction && searched" class="empty-state mt-md">
      <text class="empty-icon">📊</text>
      <text class="empty-text">暂无预测数据</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/utils/api'

const authStore = useAuthStore()
const patientId = computed(() => authStore.userInfo?.id || '')

const predictionTypes = [
  { value: 'blood_sugar', label: '血糖预测', icon: '🩸' },
  { value: 'complication', label: '并发症风险', icon: '⚠️' },
  { value: 'intervention', label: '干预效果', icon: '💊' },
]

const activeType = ref('blood_sugar')
const prediction = ref<any>(null)
const loading = ref(false)
const searched = ref(false)

const currentTypeLabel = computed(() => {
  return predictionTypes.find(t => t.value === activeType.value)?.label || ''
})

const formatRiskLevel = (level: string) => {
  const map: Record<string, string> = { low: '低风险', medium: '中风险', high: '高风险', urgent: '极高风险' }
  return map[level] || level
}

const getRiskClass = (level: string) => {
  const map: Record<string, string> = { low: 'tag-success', medium: 'tag-warning', high: 'tag-danger', urgent: 'tag-danger' }
  return map[level] || 'tag-info'
}

const getRiskColor = (level: string) => {
  const map: Record<string, string> = { low: '#81C784', medium: '#FFB74D', high: '#E57373', urgent: '#E57373' }
  return map[level] || '#64B5F6'
}

const switchType = (type: string) => {
  activeType.value = type
  prediction.value = null
  searched.value = false
  fetchPrediction()
}

const fetchPrediction = async () => {
  if (!patientId.value) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    return
  }
  loading.value = true
  searched.value = true
  try {
    let res: any
    if (activeType.value === 'blood_sugar') {
      res = await api.post('/prediction/blood-sugar', { patient_id: patientId.value, days: 30 })
    } else if (activeType.value === 'complication') {
      res = await api.post('/prediction/complication', { patient_id: patientId.value, complication_type: 'diabetes' })
    } else {
      res = await api.post('/prediction/intervention-effect', { patient_id: patientId.value, intervention_type: 'medication' })
    }
    prediction.value = res.prediction || res.result || null
  } catch (e) {
    uni.showToast({ title: '预测失败', icon: 'none' })
    prediction.value = null
  } finally {
    loading.value = false
  }
}

fetchPrediction()
</script>

<style scoped>
.type-selector {
  flex-wrap: wrap;
  margin-top: var(--spacing-sm);
}

.type-item {
  padding: 12rpx 24rpx;
  border-radius: var(--radius-md);
  background: var(--color-bg-page);
  font-size: 26rpx;
  color: var(--color-text-secondary);
}

.type-item.active {
  background: var(--color-primary);
  color: #fff;
}

.risk-section {
  padding: var(--spacing-sm) 0;
}

.risk-bar {
  height: 16rpx;
  background: var(--color-bg-page);
  border-radius: 8rpx;
  overflow: hidden;
  margin: var(--spacing-sm) 0;
}

.risk-fill {
  height: 100%;
  border-radius: 8rpx;
  transition: width 0.3s;
}

.risk-value {
  font-size: 36rpx;
  font-weight: 700;
}

.factor-item {
  padding: 8rpx 0;
}

.rec-item {
  padding: 8rpx 0;
}

.info-row {
  padding: 8rpx 0;
}
</style>
