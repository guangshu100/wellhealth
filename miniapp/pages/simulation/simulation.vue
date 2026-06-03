<template>
  <view class="page">
    <!-- 患者信息卡片 -->
    <view class="patient-card" v-if="patient && patient.basic_info">
      <view class="patient-card__info">
        <text class="patient-card__name">{{ patient.basic_info.name }}</text>
        <text class="patient-card__diseases">{{ diseaseNames }}</text>
      </view>
      <view class="patient-card__vitals">
        <view class="patient-card__vital" v-for="(value, key) in currentVitals" :key="key">
          <text class="patient-card__vital-key">{{ key }}</text>
          <text class="patient-card__vital-val">{{ value }}</text>
        </view>
      </view>
      <view class="patient-card__edit" @click="showEditVitals = true">
        <text>✏️ 调整指标</text>
      </view>
    </view>

    <!-- 未绑定患者 -->
    <view class="patient-card" v-else>
      <view class="empty-box">
        <text class="empty-icon">📋</text>
        <text class="empty-text">暂无患者信息</text>
      </view>
    </view>

    <!-- 干预方案选择 -->
    <view class="section">
      <view class="section__header">
        <text class="section__title">💊 选择干预方案</text>
        <text class="section__action" @click="selectAll">
          {{ selectedTypes.length === interventions.length ? '取消全选' : '全选' }}
        </text>
      </view>
      <view class="intervention-list">
        <view
          v-for="item in interventions"
          :key="item.type"
          :class="['intervention-item', { 'intervention-item--active': isSelected(item.type) }]"
          @click="toggleIntervention(item)"
        >
          <text class="intervention-item__icon">{{ item.icon }}</text>
          <view class="intervention-item__content">
            <view class="intervention-item__header">
              <text class="intervention-item__name">{{ item.name }}</text>
              <view class="intervention-item__tags">
                <text class="tag tag--effect">↑{{ item.effectiveness }}%</text>
                <text class="tag tag--risk" :class="`tag--risk-${item.risk}`">{{ item.risk }}</text>
              </view>
            </view>
            <text class="intervention-item__desc">{{ item.description }}</text>
          </view>
          <view class="intervention-item__check" v-if="isSelected(item.type)">
            <text>✓</text>
          </view>
        </view>
      </view>

      <!-- 展开详情 -->
      <view class="detail-panel" v-if="expandedItem">
        <view class="detail-panel__header">
          <text class="detail-panel__title">{{ expandedItem.name }} 详情</text>
          <text class="detail-panel__close" @click="expandedItem = null">✕</text>
        </view>
        
        <view class="detail-panel__section">
          <text class="detail-panel__section-title">📋 执行步骤</text>
          <view class="steps-list">
            <view class="step-item" v-for="(step, idx) in expandedItem.steps" :key="idx">
              <text class="step-num">{{ idx + 1 }}</text>
              <text class="step-text">{{ step }}</text>
            </view>
          </view>
        </view>

        <view class="detail-panel__section">
          <text class="detail-panel__section-title">⚠️ 注意事项</text>
          <view class="precaution-list">
            <text class="precaution-item" v-for="(p, idx) in expandedItem.precautions" :key="idx">
              {{ p }}
            </text>
          </view>
        </view>
      </view>
    </view>

    <!-- 已选方案 -->
    <view class="selected-section" v-if="selectedTypes.length > 0">
      <text class="selected-section__title">✨ 已选择 {{ selectedTypes.length }} 个方案</text>
      <view class="selected-tags">
        <view class="selected-tag" v-for="type in selectedTypes" :key="type">
          <text>{{ getInterventionName(type) }}</text>
          <text class="remove-btn" @click="removeSelection(type)">✕</text>
        </view>
      </view>
    </view>

    <!-- 快速预测按钮 -->
    <view class="action-area">
      <button 
        class="action-area__btn" 
        :disabled="selectedTypes.length === 0 || loading" 
        @click="runPrediction"
      >
        <text v-if="loading">🔄 预测中...</text>
        <text v-else>🎯 开始预测 ({{ selectedTypes.length }}个方案)</text>
      </button>
    </view>

    <!-- 预测结果 -->
    <view class="result-section" v-if="result">
      <view class="result-section__header">
        <text class="result-section__title">📊 预测结果</text>
        <text class="result-section__intervention">{{ result.intervention?.name }}</text>
      </view>

      <!-- 效果概览 -->
      <view class="effect-overview">
        <view class="effect-overview__main">
          <text class="effect-overview__value">{{ result.effectiveness }}%</text>
          <text class="effect-overview__label">预期改善</text>
        </view>
        <view class="effect-overview__stats">
          <view class="stat-item">
            <text class="stat-label">周期</text>
            <text class="stat-value">{{ result.intervention?.duration_days || 30 }}天</text>
          </view>
          <view :class="['effect-overview__risk', `effect-overview__risk--${result.risk_level}`]">
            {{ getRiskText(result.risk_level) }}
          </view>
        </view>
      </view>

      <!-- 指标变化 -->
      <view class="vitals-change">
        <view class="vitals-change__title">📉 指标变化</view>
        <view class="vitals-change__item" v-for="(predicted, key) in result.predicted" :key="key">
          <view class="vitals-change__label-row">
            <text class="vitals-change__label">{{ key }}</text>
            <text class="vitals-change__change" :class="getChangeClass(key) === 'positive' ? 'vitals-change__change-positive' : 'vitals-change__change-negative'">{{ getChangeText(key) }}</text>
          </view>
          <view class="vitals-change__bar">
            <view class="vitals-change__bar-baseline" :style="{ width: '50%' }"></view>
            <view class="vitals-change__bar-fill" :style="{ width: getChangeWidth(key) }"></view>
          </view>
          <view class="vitals-change__values">
            <text class="vitals-change__baseline">{{ result.baseline?.[key] }}</text>
            <text class="vitals-change__arrow">→</text>
            <text class="vitals-change__predicted">{{ predicted }}</text>
          </view>
        </view>
      </view>

      <!-- 30天趋势 -->
      <view class="trend-preview">
        <text class="trend-preview__title">📈 30天趋势</text>
        <view class="trend-preview__timeline">
          <view class="timeline-point" v-for="(point, idx) in result.timeline" :key="idx">
            <view class="timeline-dot" :style="{ background: getTrendColor(idx) }"></view>
            <text class="timeline-day">Day {{ point.day }}</text>
          </view>
        </view>
        <view class="trend-preview__metrics">
          <view class="metric-change" v-for="(predicted, key) in result.predicted" :key="key">
            <text class="metric-name">{{ key }}</text>
            <text class="metric-value" :class="getChangeClass(key) === 'positive' ? 'metric-value-positive' : 'metric-value-negative'">{{ getChangeText(key) }}</text>
          </view>
        </view>
      </view>

      <!-- 建议 -->
      <view class="recommendations" v-if="result.recommendations?.length">
        <text class="recommendations__title">💡 健康建议</text>
        <view class="recommendations__list">
          <text class="recommendations__item" v-for="(rec, idx) in result.recommendations" :key="idx">
            {{ rec }}
          </text>
        </view>
      </view>
    </view>

    <!-- 指标编辑弹窗 -->
    <view class="edit-modal" v-if="showEditVitals" @click="showEditVitals = false">
      <view class="edit-modal__content" @click.stop>
        <view class="edit-modal__header">
          <text class="edit-modal__title">调整当前指标</text>
          <text class="edit-modal__close" @click="showEditVitals = false">✕</text>
        </view>
        <view class="edit-modal__body">
          <view class="vital-edit-item" v-for="(value, key) in editedVitals" :key="key">
            <text class="vital-edit-label">{{ key }}</text>
            <input class="vital-edit-input" type="number" v-model="editedVitals[key]" />
          </view>
        </view>
        <view class="edit-modal__footer">
          <button class="btn-cancel" @click="showEditVitals = false">取消</button>
          <button class="btn-confirm" @click="confirmEditVitals">确定</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { simulationApi, patientApi } from '@/utils/api'

// ============ 常量定义 ============
const DEFAULT_VITALS: Record<string, number> = { '血糖': 9.5, 'HbA1c': 8.5 }
const BAR_MIN_WIDTH = 20
const BAR_MAX_WIDTH = 95
const BAR_DEFAULT_WIDTH = 50

const TREND_COLORS = ['#909399', '#E6A23C', '#67C23A']

const RISK_TEXT_MAP: Record<string, string> = {
  low: '低风险',
  medium: '中等风险',
  high: '高风险'
}

// ============ 类型定义 ============
interface Patient {
  patient_id?: string
  id?: string
  basic_info?: {
    name: string
    age: number
    gender: string
  }
  name?: string
  diseases?: Array<{ id: string; disease_name: string }>
  vitals?: Array<{ vital_type: string; value: number }>
}

interface Intervention {
  type: string
  name: string
  icon: string
  description: string
  effectiveness: string
  duration: string
  color: string
  risk: string
  steps: string[]
  precautions: string[]
}

interface SimulationResult {
  intervention?: {
    type: string
    name: string
    description: string
    duration_days: number
  }
  status: string
  baseline?: Record<string, number>
  predicted?: Record<string, number>
  timeline?: Array<Record<string, number>>
  effectiveness: number
  risk_level: string
  recommendations?: string[]
}

interface ChangeInfo {
  class: 'positive' | 'negative' | ''
  text: string
  width: string
}

// ============ 响应式数据 ============
const patient = ref<Patient | null>(null)
const currentVitals = ref<Record<string, number>>({})
const editedVitals = ref<Record<string, number>>({})
const selectedTypes = ref<string[]>([])
const expandedItem = ref<Intervention | null>(null)
const showEditVitals = ref(false)
const loading = ref(false)
const result = ref<SimulationResult | null>(null)

// 疾病名称列表
const diseaseNames = computed(() => {
  if (!patient.value?.diseases) return '糖尿病'
  return patient.value.diseases.map((d: any) => d.disease_name).join('、')
})

const interventions: Intervention[] = [
  {
    type: 'diet',
    name: '饮食干预',
    icon: '🥗',
    description: '科学饮食，控制糖分摄入，合理搭配营养',
    effectiveness: '15',
    duration: '2-4周',
    color: '#67C23A',
    risk: '低',
    steps: [
      '计算每日总热量需求',
      '制定三大营养素比例（碳水50%、蛋白20%、脂肪30%）',
      '选择低GI食物',
      '分配到每日三餐+加餐',
      '记录饮食日志'
    ],
    precautions: [
      '避免高糖、高脂食物',
      '定时定量进餐',
      '如有不适及时就医'
    ]
  },
  {
    type: 'exercise',
    name: '运动干预',
    icon: '🏃',
    description: '规律运动，提高身体代谢水平',
    effectiveness: '12',
    duration: '2-4周',
    color: '#5E8B5A',
    risk: '低',
    steps: [
      '评估运动耐力',
      '制定运动处方（类型、强度、时间、频率）',
      '从低强度开始逐渐增加',
      '监测运动心率',
      '记录运动数据'
    ],
    precautions: [
      '运动前需热身',
      '避免空腹运动',
      '如有胸闷、心慌等不适停止运动'
    ]
  },
  {
    type: 'medication',
    name: '药物调整',
    icon: '💊',
    description: '遵医嘱调整用药方案',
    effectiveness: '25',
    duration: '1-2周',
    color: '#E6A23C',
    risk: '中',
    steps: [
      '评估当前用药效果',
      '与医生沟通调整方案',
      '了解新药物用法用量',
      '注意药物相互作用',
      '监测用药反应'
    ],
    precautions: [
      '不可自行增减药量',
      '按时服药',
      '注意药物副作用'
    ]
  },
  {
    type: 'combined',
    name: '综合干预',
    icon: '🎯',
    description: '饮食+运动+监测综合方案',
    effectiveness: '35',
    duration: '4-8周',
    color: '#9C27B0',
    risk: '低',
    steps: [
      '综合评估健康状况',
      '制定个性化干预计划',
      '饮食+运动双重管理',
      '定期监测各项指标',
      '根据效果调整方案'
    ],
    precautions: [
      '循序渐进，不要急于求成',
      '坚持记录各项数据',
      '定期复查相关指标'
    ]
  }
]

// ============ 方法 ============
const isSelected = (type: string): boolean => {
  return selectedTypes.value.includes(type)
}

const toggleIntervention = (item: Intervention): void => {
  if (isSelected(item.type)) {
    selectedTypes.value = selectedTypes.value.filter(t => t !== item.type)
  } else {
    selectedTypes.value = [...selectedTypes.value, item.type]
  }
}

const selectAll = (): void => {
  if (selectedTypes.value.length === interventions.length) {
    selectedTypes.value = []
  } else {
    selectedTypes.value = interventions.map(i => i.type)
  }
}

const removeSelection = (type: string): void => {
  selectedTypes.value = selectedTypes.value.filter(t => t !== type)
}

const getInterventionName = (type: string): string => {
  const item = interventions.find(i => i.type === type)
  return item?.name || type
}

const confirmEditVitals = (): void => {
  currentVitals.value = { ...editedVitals.value }
  showEditVitals.value = false
}

const goBack = (): void => {
  uni.navigateBack()
}

const runPrediction = async (): Promise<void> => {
  if (selectedTypes.value.length === 0) return

  loading.value = true
  result.value = null

  try {
    const interventionType = selectedTypes.value.length === 1 
      ? selectedTypes.value[0] 
      : 'combined'
    
    const res = await simulationApi.runSimulation({
      patient_id: patient.value?.patient_id || patient.value?.id || 'default',
      disease: patient.value?.diseases?.[0]?.disease_name || patient.value?.diseases?.[0] || 'diabetes',
      current_vitals: currentVitals.value,
      intervention_type: interventionType
    })

    if (res.success && res.result) {
      result.value = res.result
    }
  } catch (e) {
    console.error('Prediction failed:', e)
    uni.showToast({ title: '预测失败，请重试', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const getRiskText = (level: string): string => {
  return RISK_TEXT_MAP[level] || level
}

/**
 * 获取指标变化信息（合并了 getChangeClass、getChangeText、getChangeWidth 的逻辑）
 */
const getChangeInfo = (key: string): ChangeInfo => {
  const defaultInfo: ChangeInfo = { class: '', text: '无变化', width: `${BAR_DEFAULT_WIDTH}%` }

  if (!result.value) return defaultInfo

  const baseline = result.value.baseline?.[key]
  const predicted = result.value.predicted?.[key]

  if (baseline === undefined || predicted === undefined) return defaultInfo
  if (baseline === 0) return defaultInfo

  const changeRatio = (baseline - predicted) / baseline

  // 计算变化百分比文本
  const changePercent = (Math.abs(changeRatio) * 100).toFixed(1)
  let text = '无变化'
  let changeClass: 'positive' | 'negative' | '' = ''

  if (changeRatio > 0) {
    text = `↓${changePercent}%`
    changeClass = 'positive'
  } else if (changeRatio < 0) {
    text = `↑${changePercent}%`
    changeClass = 'negative'
  }

  // 计算条形图宽度：改善越大，条形越短
  // 假设最大改善50%对应最小宽度BAR_MIN_WIDTH，0%改善对应BAR_DEFAULT_WIDTH
  const improvementFactor = Math.min(changeRatio, 0.5) / 0.5
  const width = Math.max(
    BAR_MIN_WIDTH,
    Math.min(BAR_MAX_WIDTH, BAR_DEFAULT_WIDTH - improvementFactor * 30)
  )

  return { class: changeClass, text, width: `${width}%` }
}

const getChangeClass = (key: string): string => {
  return getChangeInfo(key).class
}

const getChangeText = (key: string): string => {
  return getChangeInfo(key).text
}

const getChangeWidth = (key: string): string => {
  return getChangeInfo(key).width
}

const getTrendColor = (idx: number): string => {
  return TREND_COLORS[Math.min(idx, TREND_COLORS.length - 1)]
}

// ============ 生命周期 ============
onMounted(async (): Promise<void> => {
  try {
    const patientRes = await patientApi.getMyPatient()
    patient.value = patientRes

    if (patientRes?.vitals && patientRes.vitals.length > 0) {
      // 从vitals数组中提取值
      const vitalsMap: Record<string, number> = {}
      patientRes.vitals.forEach((v: any) => {
        if (v.vital_type === 'blood_sugar') vitalsMap['血糖'] = v.value
        else if (v.vital_type === 'blood_pressure_systolic') vitalsMap['收缩压'] = v.value
        else if (v.vital_type === 'blood_pressure_diastolic') vitalsMap['舒张压'] = v.value
        else if (v.vital_type === 'heart_rate') vitalsMap['心率'] = v.value
      })
      currentVitals.value = vitalsMap
      editedVitals.value = { ...vitalsMap }
    } else {
      currentVitals.value = { ...DEFAULT_VITALS }
      editedVitals.value = { ...DEFAULT_VITALS }
    }
  } catch (e) {
    currentVitals.value = { ...DEFAULT_VITALS }
    editedVitals.value = { ...DEFAULT_VITALS }
  }
})
</script>

<style scoped>
/* Page */
.page { min-height: 100vh; background: var(--color-bg-page); padding-bottom: 40rpx; }
.page__header { padding: 40rpx 30rpx 30rpx; background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light)); color: var(--color-text-inverse); }
.header-row { display: flex; align-items: center; gap: 20rpx; }
.back-btn { width: 60rpx; height: 60rpx; display: flex; align-items: center; justify-content: center; }
.back-btn text { font-size: 40rpx; color: #fff; font-weight: bold; }
.header-text { flex: 1; }
.page__title { display: block; font-size: 40rpx; font-weight: bold; margin-bottom: 10rpx; }
.page__subtitle { font-size: 26rpx; opacity: 0.9; }

/* Patient Card */
.patient-card { margin: -30rpx 30rpx 30rpx; padding: 30rpx; background: #FFFFFF; border-radius: 20rpx; box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.08); }
.patient-card__info { display: flex; align-items: center; gap: 20rpx; margin-bottom: 24rpx; }
.patient-card__name { font-size: 32rpx; font-weight: bold; color: #333; }
.patient-card__diseases { font-size: 24rpx; color: #666; background: #E8F0E6; padding: 6rpx 16rpx; border-radius: 20rpx; }
.patient-card__vitals { display: flex; gap: 40rpx; }
.patient-card__vital { display: flex; flex-direction: column; gap: 4rpx; }
.patient-card__vital-key { font-size: 22rpx; color: #999; }
.patient-card__vital-val { font-size: 28rpx; font-weight: 600; color: var(--color-primary); }
.patient-card__edit { margin-top: 16rpx; padding-top: 16rpx; border-top: 1rpx solid #eee; text-align: center; color: var(--color-primary); font-size: 24rpx; }

/* Empty state */
.empty-box { display: flex; flex-direction: column; align-items: center; padding: 60rpx; }
.empty-icon { font-size: 80rpx; margin-bottom: 20rpx; }
.empty-text { font-size: 28rpx; color: #999; }

/* Section */
.section { margin: 0 30rpx 30rpx; }
.section__header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20rpx; }
.section__title { display: block; font-size: 28rpx; font-weight: bold; color: #333; }
.section__action { font-size: 26rpx; color: var(--color-primary); }

/* Intervention List */
.intervention-list { display: flex; flex-direction: column; gap: 20rpx; }
.intervention-item { display: flex; align-items: center; padding: 24rpx; background: #FFFFFF; border-radius: 16rpx; border: 2rpx solid transparent; transition: all 0.3s; }
.intervention-item--active { border-color: var(--color-primary); background: #ecf5ff; }
.intervention-item__icon { font-size: 50rpx; margin-right: 20rpx; }
.intervention-item__content { flex: 1; }
.intervention-item__header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8rpx; }
.intervention-item__name { font-size: 28rpx; font-weight: 600; color: #333; }
.intervention-item__tags { display: flex; gap: 12rpx; }
.intervention-item__desc { display: block; font-size: 24rpx; color: #999; margin-bottom: 12rpx; }
.intervention-item__check { width: 44rpx; height: 44rpx; background: var(--color-primary); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: var(--color-text-inverse); font-size: 24rpx; }

/* Tags */
.tag { font-size: 20rpx; padding: 4rpx 12rpx; border-radius: 8rpx; }
.tag--effect { background: #E8F0E6; color: var(--color-primary); }
.tag--period { background: #E8F0E6; color: var(--color-primary); }
.tag--risk { background: #E8F0E6; color: var(--color-primary); }

/* Selected Section */
.selected-section { margin: 0 30rpx 20rpx; padding: 20rpx; background: #E8F0E6; border-radius: 12rpx; }
.selected-section__title { font-size: 26rpx; color: #333; font-weight: 500; margin-bottom: 16rpx; display: block; }
.selected-tags { display: flex; flex-wrap: wrap; gap: 12rpx; }
.selected-tag { display: flex; align-items: center; gap: 8rpx; padding: 8rpx 16rpx; background: #FFFFFF; border-radius: 20rpx; font-size: 24rpx; color: var(--color-primary); }
.remove-btn { font-size: 20rpx; color: #999; padding: 4rpx; }

/* Detail Panel */
.detail-panel { margin-top: 20rpx; padding: 24rpx; background: #FFFFFF; border-radius: 16rpx; box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.1); }
.detail-panel__header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20rpx; padding-bottom: 16rpx; border-bottom: 1rpx solid #eee; }
.detail-panel__title { font-size: 30rpx; font-weight: bold; color: #333; }
.detail-panel__close { font-size: 32rpx; color: #999; }
.detail-panel__section { margin-bottom: 20rpx; }
.detail-panel__section-title { display: block; font-size: 26rpx; font-weight: 600; color: #333; margin-bottom: 12rpx; }
.steps-list { display: flex; flex-direction: column; gap: 12rpx; }
.step-item { display: flex; align-items: flex-start; gap: 12rpx; }
.step-num { width: 36rpx; height: 36rpx; background: var(--color-primary); color: var(--color-text-inverse); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 22rpx; flex-shrink: 0; }
.step-text { font-size: 24rpx; color: #666; line-height: 1.5; }
.precaution-list { display: flex; flex-direction: column; gap: 8rpx; }
.precaution-item { font-size: 24rpx; color: #e6a23c; padding-left: 20rpx; border-left: 4rpx solid #e6a23c; line-height: 1.5; }

/* Action Area */
.action-area { padding: 0 30rpx; margin-bottom: 30rpx; }
.action-area__btn { width: 100%; height: 88rpx; background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light)); color: var(--color-text-inverse); font-size: 32rpx; font-weight: bold; border-radius: 44rpx; border: none; display: flex; align-items: center; justify-content: center; }

/* Result Section */
.result-section { margin: 0 30rpx; padding: 30rpx; background: #FFFFFF; border-radius: 20rpx; }
.result-section__header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24rpx; }
.result-section__title { font-size: 30rpx; font-weight: bold; color: #333; }
.result-section__intervention { font-size: 24rpx; color: var(--color-primary); background: #E8F0E6; padding: 8rpx 16rpx; border-radius: 20rpx; }

/* Effect Overview */
.effect-overview { display: flex; align-items: center; justify-content: space-between; padding: 30rpx; background: linear-gradient(135deg, #E8F0E6, #E8F0E6); border-radius: 16rpx; margin-bottom: 30rpx; }
.effect-overview__main { display: flex; flex-direction: column; align-items: center; }
.effect-overview__value { font-size: 56rpx; font-weight: bold; color: var(--color-primary); }
.effect-overview__label { font-size: 24rpx; color: #666; margin-top: 8rpx; }
.effect-overview__stats { display: flex; flex-direction: column; gap: 8rpx; align-items: flex-end; }
.effect-overview__risk { padding: 12rpx 24rpx; border-radius: 30rpx; font-size: 24rpx; font-weight: 500; }
.effect-overview__risk--low { background: #E8F0E6; color: var(--color-primary); }
.effect-overview__risk--medium { background: #FDF6EC; color: #e6a23c; }
.effect-overview__risk--high { background: #FEF0F0; color: #f56c6c; }
.stat-item { display: flex; gap: 8rpx; font-size: 22rpx; }
.stat-label { color: #999; }
.stat-value { color: #333; font-weight: 500; }

/* Vitals Change */
.vitals-change { margin-bottom: 30rpx; }
.vitals-change__title { font-size: 28rpx; font-weight: 600; color: #333; margin-bottom: 16rpx; display: block; }
.vitals-change__item { margin-bottom: 24rpx; }
.vitals-change__label-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8rpx; }
.vitals-change__label { display: block; font-size: 26rpx; color: #333; }
.vitals-change__change { font-weight: 600; }
.vitals-change__change-positive { color: var(--color-primary); }
.vitals-change__change-negative { color: #f56c6c; }
.vitals-change__bar { height: 16rpx; background: #e8e8e8; border-radius: 8rpx; margin-bottom: 10rpx; overflow: hidden; position: relative; }
.vitals-change__bar-fill { position: absolute; left: 0; top: 0; height: 100%; background: linear-gradient(90deg, var(--color-primary), var(--color-primary-light)); border-radius: 8rpx; transition: width 0.5s ease; }
.vitals-change__values { display: flex; align-items: center; gap: 12rpx; font-size: 24rpx; }
.vitals-change__baseline { color: #999; }
.vitals-change__arrow { color: #c0c4cc; }
.vitals-change__predicted { color: var(--color-primary); font-weight: 600; }

/* Trend Preview */
.trend-preview { padding: 24rpx; background: #f8f9fa; border-radius: 16rpx; margin-bottom: 30rpx; }
.trend-preview__title { display: block; font-size: 26rpx; font-weight: 600; color: #333; margin-bottom: 16rpx; }
.trend-preview__timeline { display: flex; justify-content: space-between; margin: 20rpx 0; }
.timeline-point { display: flex; flex-direction: column; align-items: center; gap: 8rpx; }
.timeline-dot { width: 24rpx; height: 24rpx; border-radius: 50%; }
.timeline-day { font-size: 22rpx; color: #999; }
.trend-preview__metrics { display: flex; flex-wrap: wrap; gap: 16rpx; margin-top: 16rpx; padding-top: 16rpx; border-top: 1rpx solid #eee; }
.metric-change { display: flex; align-items: center; gap: 8rpx; font-size: 24rpx; }
.metric-name { color: #666; }
.metric-value { font-weight: 600; }
.metric-value-positive { color: var(--color-primary); }
.metric-value-negative { color: #f56c6c; }

/* Recommendations */
.recommendations { padding-top: 24rpx; border-top: 1rpx solid #eee; }
.recommendations__title { display: block; font-size: 26rpx; font-weight: 600; color: #333; margin-bottom: 16rpx; }
.recommendations__list { display: flex; flex-direction: column; gap: 12rpx; }
.recommendations__item { font-size: 26rpx; color: #666; line-height: 1.5; padding-left: 20rpx; border-left: 4rpx solid var(--color-primary); }

/* Edit Modal */
.edit-modal { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.5); display: flex; align-items: center; justify-content: center; z-index: 999; }
.edit-modal__content { width: 80%; background: #FFFFFF; border-radius: 20rpx; overflow: hidden; }
.edit-modal__header { display: flex; justify-content: space-between; align-items: center; padding: 30rpx; border-bottom: 1rpx solid #eee; }
.edit-modal__title { font-size: 32rpx; font-weight: bold; color: #333; }
.edit-modal__close { font-size: 36rpx; color: #999; }
.edit-modal__body { padding: 30rpx; }
.edit-modal__footer { display: flex; gap: 20rpx; padding: 30rpx; border-top: 1rpx solid #eee; }
.vital-edit-item { display: flex; align-items: center; justify-content: space-between; padding: 20rpx 0; border-bottom: 1rpx solid #eee; }
.vital-edit-label { font-size: 28rpx; color: #333; }
.vital-edit-input { width: 200rpx; padding: 12rpx 20rpx; border: 1rpx solid #ddd; border-radius: 10rpx; font-size: 28rpx; text-align: right; }
.btn-cancel { flex: 1; padding: 20rpx; background: var(--color-bg-page); color: var(--color-text-primary); border-radius: 40rpx; border: none; font-size: 28rpx; }
.btn-confirm { flex: 1; padding: 20rpx; background: var(--color-primary); color: var(--color-text-inverse); border-radius: 40rpx; border: none; font-size: 28rpx; }
</style>
