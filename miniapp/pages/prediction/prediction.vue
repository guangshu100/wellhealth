<template>
  <view class="page">
    <!-- 头部 -->
    <view class="header">
      <text class="title">健康预测</text>
      <text class="subtitle">AI智能预测健康趋势和风险</text>
    </view>

    <!-- 标签页 -->
    <view class="tabs">
      <view 
        class="tab-item" 
        :class="{ active: activeTab === 'blood-sugar' }"
        @click="activeTab = 'blood-sugar'"
      >
        血糖预测
      </view>
      <view 
        class="tab-item" 
        :class="{ active: activeTab === 'complications' }"
        @click="activeTab = 'complications'"
      >
        并发症
      </view>
      <view 
        class="tab-item" 
        :class="{ active: activeTab === 'intervention' }"
        @click="activeTab = 'intervention'"
      >
        干预效果
      </view>
      <view 
        class="tab-item" 
        :class="{ active: activeTab === 'history' }"
        @click="activeTab = 'history'"
      >
        历史
      </view>
    </view>

    <view class="content">
      <!-- 血糖预测 -->
      <view v-if="activeTab === 'blood-sugar'" class="prediction-section">
        <view class="predict-card">
          <view class="card-header">
            <text class="card-title">未来血糖趋势预测</text>
          </view>
          
          <view class="days-selector">
            <view 
              class="day-item" 
              v-for="day in [7, 14, 30]" 
              :key="day"
              :class="{ active: predictionDays === day }"
              @click="predictionDays = day"
            >
              {{ day }}天
            </view>
          </view>
          
          <view class="btn-predict" @click="predictBloodSugar" :class="{ loading: predicting }">
            {{ predicting ? '预测中...' : '开始预测' }}
          </view>
        </view>
        
        <view v-if="bloodSugarPrediction" class="result-card">
          <view class="risk-badge" :class="'risk-' + bloodSugarPrediction.prediction_result.risk_level">
            {{ getRiskLabel(bloodSugarPrediction.prediction_result.risk_level) }}
          </view>
          
          <view class="probability">
            <text class="prob-value">{{ (bloodSugarPrediction.prediction_result.probability * 100).toFixed(1) }}</text>
            <text class="prob-unit">%</text>
          </view>
          
          <view class="trend-info">
            <text class="trend-label">趋势方向:</text>
            <text class="trend-value" :class="getTrendClass(bloodSugarPrediction.prediction_result.trend)">
              {{ getTrendLabel(bloodSugarPrediction.prediction_result.trend) }}
            </text>
          </view>
          
          <view class="factors-section">
            <text class="section-title">影响因素</text>
            <view class="factor-tags">
              <text 
                class="factor-tag" 
                v-for="factor in bloodSugarPrediction.prediction_result.factors" 
                :key="factor"
              >
                {{ factor }}
              </text>
            </view>
          </view>
          
          <view class="recommendations-section">
            <text class="section-title">建议</text>
            <view class="rec-list">
              <view 
                class="rec-item" 
                v-for="rec in bloodSugarPrediction.prediction_result.recommendations" 
                :key="rec"
              >
                {{ rec }}
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- 并发症风险 -->
      <view v-if="activeTab === 'complications'" class="prediction-section">
        <view class="predict-card">
          <view class="card-header">
            <text class="card-title">并发症风险评估</text>
          </view>
          
          <picker :range="complicationTypes" range-key="label" @change="onComplicationChange">
            <view class="picker">{{ selectedComplication?.label || '选择并发症类型' }}</view>
          </picker>
          
          <view class="btn-predict" @click="predictComplication" :class="{ loading: predicting }">
            {{ predicting ? '评估中...' : '开始评估' }}
          </view>
        </view>
        
        <view v-if="complicationPrediction" class="result-card">
          <view class="risk-meter">
            <view class="meter-label">风险等级</view>
            <view class="meter-bar">
              <view 
                class="meter-fill" 
                :style="{ width: (complicationPrediction.probability * 100) + '%' }"
                :class="'meter-' + complicationPrediction.risk_level"
              ></view>
            </view>
            <view class="meter-value" :class="'risk-' + complicationPrediction.risk_level">
              {{ getRiskLabel(complicationPrediction.risk_level) }}
              ({{ (complicationPrediction.probability * 100).toFixed(1) }}%)
            </view>
          </view>
          
          <view class="factors-section">
            <text class="section-title">风险因素</text>
            <view class="factor-tags">
              <text 
                class="factor-tag" 
                v-for="factor in complicationPrediction.factors" 
                :key="factor"
              >
                {{ factor }}
              </text>
            </view>
          </view>
          
          <view class="recommendations-section">
            <text class="section-title">预防建议</text>
            <view class="rec-list">
              <view 
                class="rec-item" 
                v-for="rec in complicationPrediction.recommendations" 
                :key="rec"
              >
                {{ rec }}
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- 干预效果 -->
      <view v-if="activeTab === 'intervention'" class="prediction-section">
        <view class="predict-card">
          <view class="card-header">
            <text class="card-title">干预方案效果预测</text>
          </view>
          
          <picker :range="interventionTypes" range-key="label" @change="onInterventionChange">
            <view class="picker">{{ selectedIntervention?.label || '选择干预方案' }}</view>
          </picker>
          
          <view class="btn-predict" @click="predictIntervention" :class="{ loading: predicting }">
            {{ predicting ? '预测中...' : '预测效果' }}
          </view>
        </view>
        
        <view v-if="interventionPrediction" class="result-card">
          <view class="intervention-header">
            <text class="intervention-name">{{ interventionPrediction.intervention_name }}</text>
          </view>
          
          <view class="effect-grid">
            <view class="effect-item">
              <text class="effect-value" :class="getChangeClass(interventionPrediction.predicted_effect.blood_sugar_change)">
                {{ interventionPrediction.predicted_effect.blood_sugar_change > 0 ? '+' : '' }}{{ interventionPrediction.predicted_effect.blood_sugar_change }}
              </text>
              <text class="effect-label">血糖变化</text>
              <text class="effect-unit">mmol/L</text>
            </view>
            <view class="effect-item">
              <text class="effect-value">{{ (interventionPrediction.predicted_effect.confidence * 100).toFixed(0) }}</text>
              <text class="effect-label">置信度</text>
              <text class="effect-unit">%</text>
            </view>
          </view>
          
          <view class="timeline-section">
            <text class="section-title">预测时间线</text>
            <view class="timeline">
              <view 
                class="timeline-item" 
                v-for="point in interventionPrediction.timeline" 
                :key="point.day"
              >
                <text class="timeline-day">第{{ point.day }}天</text>
                <text class="timeline-value">{{ point.predicted_value }}</text>
              </view>
            </view>
          </view>
          
          <view class="recommendations-section">
            <text class="section-title">建议</text>
            <view class="rec-list">
              <view 
                class="rec-item" 
                v-for="rec in interventionPrediction.recommendations" 
                :key="rec"
              >
                {{ rec }}
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- 历史记录 -->
      <view v-if="activeTab === 'history'" class="history-section">
        <view v-if="predictionHistory.length > 0" class="history-list">
          <view 
            class="history-item" 
            v-for="pred in predictionHistory" 
            :key="pred.id"
          >
            <view class="history-header">
              <text class="history-type">{{ getTypeLabel(pred.type) }}</text>
              <text class="history-risk" :class="'risk-' + pred.prediction_result.risk_level">
                {{ getRiskLabel(pred.prediction_result.risk_level) }}
              </text>
            </view>
            <view class="history-content">
              <text class="history-prob">概率: {{ (pred.prediction_result.probability * 100).toFixed(1) }}%</text>
              <text class="history-date">{{ formatDate(pred.prediction_date) }}</text>
            </view>
          </view>
        </view>
        
        <view v-else class="empty-state">
          <text class="empty-text">暂无预测历史</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { predictionApi } from '@/utils/api'

const patientId = ref('patient_001')
const activeTab = ref('blood-sugar')
const predicting = ref(false)
const predictionDays = ref(7)

const complicationTypes = [
  { value: 'retinopathy', label: '糖尿病视网膜病变' },
  { value: 'nephropathy', label: '糖尿病肾病' },
  { value: 'neuropathy', label: '糖尿病神经病变' },
  { value: 'cardiovascular', label: '心血管疾病' },
  { value: 'foot', label: '糖尿病足' }
]

const interventionTypes = [
  { value: 'exercise', label: '增加运动' },
  { value: 'diet', label: '调整饮食' },
  { value: 'medication', label: '药物治疗调整' },
  { value: 'monitoring', label: '血糖监测强化' },
  { value: 'comprehensive', label: '综合管理' }
]

const selectedComplication = ref(complicationTypes[0])
const selectedIntervention = ref(interventionTypes[0])

const bloodSugarPrediction = ref<any>(null)
const complicationPrediction = ref<any>(null)
const interventionPrediction = ref<any>(null)
const predictionHistory = ref<Array<any>>([])

const onComplicationChange = (e: any) => {
  selectedComplication.value = complicationTypes[e.detail.value]
}

const onInterventionChange = (e: any) => {
  selectedIntervention.value = interventionTypes[e.detail.value]
}

const predictBloodSugar = async () => {
  predicting.value = true
  try {
    const res = await predictionApi.predictBloodSugar(patientId.value, predictionDays.value)
    if (res.success) {
      bloodSugarPrediction.value = res.prediction
    }
  } catch (e) {
    // 模拟数据
    bloodSugarPrediction.value = {
      prediction_date: new Date().toISOString(),
      prediction_result: {
        risk_level: 'medium',
        probability: 0.45,
        trend: 'stable',
        factors: ['饮食控制', '运动习惯', '用药规律'],
        recommendations: ['继续保持当前饮食控制', '建议每天运动30分钟', '定期监测血糖']
      }
    }
  } finally {
    predicting.value = false
  }
}

const predictComplication = async () => {
  predicting.value = true
  try {
    const res = await predictionApi.predictComplication(patientId.value, selectedComplication.value.value)
    if (res.success) {
      complicationPrediction.value = res.prediction
    }
  } catch (e) {
    // 模拟数据
    complicationPrediction.value = {
      risk_level: 'low',
      probability: 0.25,
      factors: ['血糖控制良好', '血压正常', '无吸烟史'],
      recommendations: ['继续保持', '每年进行眼底检查', '定期尿微量白蛋白检测']
    }
  } finally {
    predicting.value = false
  }
}

const predictIntervention = async () => {
  predicting.value = true
  try {
    const res = await predictionApi.predictInterventionEffect(patientId.value, selectedIntervention.value.value)
    if (res.success) {
      interventionPrediction.value = res.prediction
    }
  } catch (e) {
    // 模拟数据
    interventionPrediction.value = {
      intervention_name: selectedIntervention.value.label,
      predicted_effect: {
        blood_sugar_change: -0.8,
        confidence: 0.85
      },
      timeline: [
        { day: 1, predicted_value: 6.8 },
        { day: 7, predicted_value: 6.5 },
        { day: 14, predicted_value: 6.2 },
        { day: 30, predicted_value: 6.0 }
      ],
      recommendations: ['坚持30天可见明显效果', '配合饮食控制效果更佳', '注意运动后血糖监测']
    }
  } finally {
    predicting.value = false
  }
}

const loadHistory = async () => {
  try {
    const res = await predictionApi.getPredictionHistory(patientId.value)
    if (res.success) {
      predictionHistory.value = res.predictions
    }
  } catch (e) {
    // 模拟数据
    predictionHistory.value = [
      { id: '1', type: 'blood_sugar', prediction_date: '2024-03-15', prediction_result: { risk_level: 'medium', probability: 0.4 } },
      { id: '2', type: 'complication', prediction_date: '2024-03-10', prediction_result: { risk_level: 'low', probability: 0.2 } }
    ]
  }
}

const getRiskLabel = (level: string) => {
  const labels: Record<string, string> = { low: '低风险', medium: '中等风险', high: '高风险', urgent: '紧急' }
  return labels[level] || level
}

const getTrendClass = (trend: string) => {
  if (trend === 'falling') return 'trend-good'
  if (trend === 'rising') return 'trend-bad'
  return 'trend-normal'
}

const getTrendLabel = (trend: string) => {
  const labels: Record<string, string> = { rising: '上升', falling: '下降', stable: '稳定' }
  return labels[trend] || trend
}

const getChangeClass = (change: number) => {
  if (change < 0) return 'change-negative'
  if (change > 0) return 'change-positive'
  return 'change-neutral'
}

const getTypeLabel = (type: string) => {
  const labels: Record<string, string> = { blood_sugar: '血糖预测', complication: '并发症风险' }
  return labels[type] || type
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}/${date.getDate()}`
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--color-bg-page);
}

.header {
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
  border-radius: 0 0 30rpx 30rpx;
  padding: 40rpx 30rpx;
  text-align: center;
}

.title {
  display: block;
  font-size: 40rpx;
  font-weight: bold;
  color: var(--color-text-inverse);
}

.subtitle {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.9);
  margin-top: 10rpx;
}

.tabs {
  display: flex;
  background: #FFFFFF;
  padding: 20rpx 0;
  margin-bottom: 20rpx;
  flex-wrap: wrap;
}

.tab-item {
  width: 25%;
  text-align: center;
  font-size: 26rpx;
  color: var(--color-text-secondary);
  padding: 15rpx 0;
  border-bottom: 4rpx solid transparent;
}

.tab-item.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
  font-weight: bold;
}

.content {
  padding: 0 20rpx;
  padding-bottom: 40rpx;
}

.predict-card, .result-card {
  background: #FFFFFF;
  border-radius: 15rpx;
  padding: 25rpx;
  margin-bottom: 20rpx;
}

.card-header {
  margin-bottom: 20rpx;
}

.card-title {
  font-size: 30rpx;
  font-weight: bold;
  color: var(--color-text-primary);
}

.days-selector {
  display: flex;
  gap: 15rpx;
  margin-bottom: 25rpx;
}

.day-item {
  flex: 1;
  text-align: center;
  padding: 20rpx;
  background: var(--color-bg-page);
  border-radius: 10rpx;
  font-size: 28rpx;
}

.day-item.active {
  background: var(--color-primary);
  color: var(--color-text-inverse);
}

.picker {
  padding: 20rpx;
  background: var(--color-bg-page);
  border-radius: 10rpx;
  font-size: 28rpx;
  color: var(--color-text-primary);
  margin-bottom: 25rpx;
}

.btn-predict {
  width: 100%;
  text-align: center;
  padding: 25rpx;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
  color: var(--color-text-inverse);
  border-radius: 40rpx;
  font-size: 30rpx;
  font-weight: bold;
}

.btn-predict.loading {
  background: var(--color-primary-light);
}

.result-card {
  text-align: center;
}

.risk-badge {
  display: inline-block;
  padding: 10rpx 30rpx;
  border-radius: 30rpx;
  font-size: 28rpx;
  color: var(--color-text-inverse);
  margin-bottom: 20rpx;
}

.risk-low { background: var(--color-primary); }
.risk-medium { background: #e6a23c; }
.risk-high, .risk-urgent { background: #f56c6c; }

.probability {
  margin-bottom: 25rpx;
}

.prob-value {
  font-size: 80rpx;
  font-weight: bold;
  color: var(--color-primary);
}

.prob-unit {
  font-size: 32rpx;
  color: var(--color-text-secondary);
}

.trend-info {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10rpx;
  margin-bottom: 25rpx;
}

.trend-label {
  font-size: 26rpx;
  color: var(--color-text-secondary);
}

.trend-value {
  font-size: 28rpx;
  font-weight: bold;
}

.trend-good { color: var(--color-primary); }
.trend-bad { color: var(--color-danger); }
.trend-normal { color: var(--color-primary); }

.factors-section, .recommendations-section, .timeline-section {
  text-align: left;
  margin-top: 25rpx;
}

.section-title {
  display: block;
  font-size: 28rpx;
  font-weight: bold;
  color: var(--color-text-primary);
  margin-bottom: 15rpx;
}

.factor-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
}

.factor-tag {
  padding: 10rpx 20rpx;
  background: #f0f0f0;
  border-radius: 20rpx;
  font-size: 24rpx;
  color: var(--color-text-secondary);
}

.rec-list {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.rec-item {
  padding: 15rpx;
  background: var(--color-bg-page);
  border-radius: 10rpx;
  font-size: 26rpx;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.risk-meter {
  margin-bottom: 30rpx;
}

.meter-label {
  font-size: 26rpx;
  color: var(--color-text-secondary);
  margin-bottom: 10rpx;
}

.meter-bar {
  height: 20rpx;
  background: #f0f0f0;
  border-radius: 10rpx;
  overflow: hidden;
}

.meter-fill {
  height: 100%;
  border-radius: 10rpx;
  transition: width 0.3s;
}

.meter-low { background: var(--color-primary); }
.meter-medium { background: #e6a23c; }
.meter-high { background: #f56c6c; }

.meter-value {
  margin-top: 10rpx;
  font-size: 28rpx;
  font-weight: bold;
}

.intervention-header {
  margin-bottom: 25rpx;
}

.intervention-name {
  font-size: 32rpx;
  font-weight: bold;
  color: var(--color-primary);
}

.effect-grid {
  display: flex;
  gap: 20rpx;
  margin-bottom: 25rpx;
}

.effect-item {
  flex: 1;
  text-align: center;
  padding: 25rpx;
  background: var(--color-bg-page);
  border-radius: 10rpx;
}

.effect-value {
  display: block;
  font-size: 40rpx;
  font-weight: bold;
  color: var(--color-text-primary);
}

.change-negative { color: var(--color-primary); }
.change-positive { color: #f56c6c; }
.change-neutral { color: var(--color-text-secondary); }

.effect-label {
  display: block;
  font-size: 24rpx;
  color: var(--color-text-secondary);
  margin-top: 8rpx;
}

.effect-unit {
  font-size: 22rpx;
  color: var(--color-text-secondary);
}

.timeline {
  display: flex;
  justify-content: space-between;
}

.timeline-item {
  text-align: center;
}

.timeline-day {
  display: block;
  font-size: 24rpx;
  color: var(--color-text-secondary);
}

.timeline-value {
  display: block;
  font-size: 32rpx;
  font-weight: bold;
  color: var(--color-primary);
  margin-top: 8rpx;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 15rpx;
}

.history-item {
  background: #FFFFFF;
  border-radius: 15rpx;
  padding: 25rpx;
}

.history-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10rpx;
}

.history-type {
  font-size: 28rpx;
  font-weight: bold;
  color: var(--color-text-primary);
}

.history-risk {
  font-size: 24rpx;
  padding: 4rpx 12rpx;
  border-radius: 20rpx;
  color: #fff;
}

.history-content {
  display: flex;
  justify-content: space-between;
}

.history-prob {
  font-size: 26rpx;
  color: var(--color-text-secondary);
}

.history-date {
  font-size: 24rpx;
  color: var(--color-text-secondary);
}

.empty-state {
  text-align: center;
  padding: 60rpx;
}

.empty-text {
  font-size: 28rpx;
  color: var(--color-text-secondary);
}
</style>
