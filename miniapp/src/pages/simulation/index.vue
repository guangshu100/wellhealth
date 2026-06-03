<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/utils/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const diseases = [
  { value: 'diabetes', label: '糖尿病' },
  { value: 'hypertension', label: '高血压' },
  { value: 'heart_disease', label: '心脏病' },
]

const interventionTypes = ref<{ value: string; label: string }[]>([
  { value: 'diet', label: '饮食' },
  { value: 'exercise', label: '运动' },
  { value: 'medication', label: '药物' },
  { value: 'comprehensive', label: '综合' },
])

const interventions = ref<any[]>([])

const selectedDisease = ref('diabetes')
const selectedInterventionType = ref('diet')
const loading = ref(false)
const result = ref<any>(null)

const patientId = computed(() => auth.userInfo?.id || '')

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

async function loadInterventionTypes() {
  try {
    const res = await api.get('/simulation/intervention-types')
    if (Array.isArray(res)) {
      interventionTypes.value = res.map((item: any) => ({
        value: item.value || item.key || item.code,
        label: item.label || item.name,
      }))
    } else if (res && typeof res === 'object') {
      const data = res as any
      if (Array.isArray(data.types)) {
        interventionTypes.value = data.types.map((item: any) => ({
          value: item.value || item.key || item.code,
          label: item.label || item.name,
        }))
      }
    }
  } catch (e) {
    console.error(e)
  }
}

async function loadInterventions() {
  try {
    const res = await api.get('/simulation/interventions')
    interventions.value = Array.isArray(res) ? res : (res as any)?.interventions || (res as any)?.data || []
  } catch (e) {
    console.error(e)
  }
}

async function runSimulation() {
  if (!patientId.value) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    return
  }
  loading.value = true
  result.value = null
  try {
    const res = await api.post('/simulation/run', {
      patient_id: patientId.value,
      disease: selectedDisease.value,
      current_vitals: {},
      intervention_type: selectedInterventionType.value,
    })
    result.value = res.simulation || res.result || res
  } catch (e) {
    console.error(e)
    uni.showToast({ title: '模拟失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadInterventionTypes()
  loadInterventions()
})
</script>

<template>
  <view class="page">
    <view class="card">
      <text class="section-title">疾病选择</text>
      <view class="selector-row">
        <view
          v-for="item in diseases"
          :key="item.value"
          class="selector-item"
          :class="{ active: selectedDisease === item.value }"
          @tap="selectedDisease = item.value"
        >
          <text>{{ item.label }}</text>
        </view>
      </view>
    </view>

    <view class="card">
      <text class="section-title">干预方式</text>
      <view class="selector-row">
        <view
          v-for="item in interventionTypes"
          :key="item.value"
          class="selector-item"
          :class="{ active: selectedInterventionType === item.value }"
          @tap="selectedInterventionType = item.value"
        >
          <text>{{ item.label }}</text>
        </view>
      </view>
    </view>

    <view class="btn-primary simulate-btn" @tap="runSimulation">
      <text>开始模拟</text>
    </view>

    <view v-if="loading" class="flex-center mt-md">
      <text class="text-hint">模拟计算中...</text>
    </view>

    <view v-if="!loading && result" class="card result-card">
      <view class="flex-between mb-md">
        <text class="section-title" style="margin-bottom: 0;">模拟结果</text>
        <view v-if="result.risk_level" class="tag" :class="getRiskClass(result.risk_level)">
          {{ formatRiskLevel(result.risk_level) }}
        </view>
      </view>

      <view v-if="result.effectiveness !== undefined" class="effectiveness-section mb-md">
        <text class="text-secondary mb-sm">干预有效性</text>
        <view class="effectiveness-bar">
          <view
            class="effectiveness-fill"
            :style="{ width: Math.min(result.effectiveness * 100, 100) + '%' }"
          />
        </view>
        <text class="effectiveness-value">{{ (result.effectiveness * 100).toFixed(1) }}%</text>
      </view>

      <view v-if="result.baseline && result.predicted" class="comparison-section mb-md">
        <text class="text-primary mb-sm" style="font-weight: 600;">基线 vs 预测对比</text>
        <view class="comparison-table">
          <view class="comparison-header">
            <text class="comparison-cell header-cell">指标</text>
            <text class="comparison-cell header-cell">基线值</text>
            <text class="comparison-cell header-cell">预测值</text>
          </view>
          <view
            v-for="(key, idx) in Object.keys(result.baseline)"
            :key="idx"
            class="comparison-row"
          >
            <text class="comparison-cell">{{ key }}</text>
            <text class="comparison-cell">{{ result.baseline[key] }}</text>
            <text class="comparison-cell predicted">{{ result.predicted[key] }}</text>
          </view>
        </view>
      </view>

      <view v-if="result.recommendations && result.recommendations.length > 0">
        <text class="text-primary mb-sm" style="font-weight: 600;">建议</text>
        <view v-for="(rec, idx) in result.recommendations" :key="idx" class="rec-item">
          <view class="flex-row gap-xs">
            <text class="tag tag-primary" style="min-width: 40rpx; text-align: center;">{{ idx + 1 }}</text>
            <text class="text-secondary" style="flex: 1;">{{ rec }}</text>
          </view>
        </view>
      </view>
    </view>

    <view v-if="!loading && !result" class="empty-state mt-md">
      <text class="empty-icon">🔬</text>
      <text class="empty-text">选择疾病和干预方式后开始模拟</text>
    </view>
  </view>
</template>

<style scoped>
.selector-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-sm);
}

.selector-item {
  padding: 14rpx 28rpx;
  border-radius: var(--radius-md);
  background: var(--color-bg-page);
  font-size: 26rpx;
  color: var(--color-text-secondary);
}

.selector-item.active {
  background: var(--color-primary);
  color: #fff;
}

.simulate-btn {
  width: 100%;
  padding: 28rpx 0;
  font-size: 32rpx;
  font-weight: 600;
  text-align: center;
  margin-bottom: var(--spacing-md);
}

.effectiveness-section {
  padding: var(--spacing-sm) 0;
}

.effectiveness-bar {
  height: 20rpx;
  background: var(--color-bg-page);
  border-radius: 10rpx;
  overflow: hidden;
  margin: var(--spacing-sm) 0;
}

.effectiveness-fill {
  height: 100%;
  background: var(--color-primary);
  border-radius: 10rpx;
  transition: width 0.3s;
}

.effectiveness-value {
  font-size: 36rpx;
  font-weight: 700;
  color: var(--color-primary);
}

.comparison-table {
  border: 2rpx solid var(--color-border);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.comparison-header {
  display: flex;
  background: var(--color-bg-page);
}

.comparison-row {
  display: flex;
  border-top: 2rpx solid var(--color-border);
}

.comparison-cell {
  flex: 1;
  padding: 16rpx 12rpx;
  font-size: 24rpx;
  color: var(--color-text-secondary);
}

.header-cell {
  font-weight: 600;
  color: var(--color-text-primary);
}

.comparison-cell.predicted {
  color: var(--color-primary);
  font-weight: 600;
}

.rec-item {
  padding: 8rpx 0;
}
</style>
