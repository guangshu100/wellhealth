<template>
  <div class="simulation-view">
    <div class="simulation-header">
      <h2>🎯 干预效果模拟</h2>
      <p class="subtitle">拖拽干预方案到模拟区域，预测不同方案的效果</p>
    </div>

    <el-row :gutter="20">
      <!-- 左侧：干预方案选择 -->
      <el-col :span="8">
        <div class="intervention-panel">
          <div class="panel-title">
            <span>💊 干预方案库</span>
            <el-button type="text" @click="selectAll">
              全选
            </el-button>
          </div>
          
            <el-scrollbar>
            <div class="intervention-list">
              <div
                v-for="item in simulationStore.interventionTypes"
                :key="item.type"
                :class="['intervention-card', { selected: isSelected(item.type), expanded: expandedCard === item.type }]"
                :style="{ '--item-color': item.color }"
                draggable="true"
                @dragstart="handleDragStart($event, item)"
                @click="handleCardClick(item)"
              >
                <!-- 卡片头部 -->
                <div class="card-header" @click.stop="toggleCardExpand(item.type)">
                  <div class="card-icon">{{ item.icon }}</div>
                  <div class="card-content">
                    <div class="card-title">{{ item.name }}</div>
                    <div class="card-desc">{{ item.description }}</div>
                  </div>
                  <div class="card-check">
                    <el-icon v-if="isSelected(item.type)"><Check /></el-icon>
                  </div>
                </div>
                
                <!-- 关键指标预览 -->
                <div class="card-metrics">
                  <div class="metric-item">
                    <span class="metric-label">有效率</span>
                    <span class="metric-value effectiveness">{{ getEffectivenessRange(item.type) }}</span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-label">周期</span>
                    <span class="metric-value">{{ getDurationRange(item.type) }}</span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-label">风险</span>
                    <el-tag size="small" :type="getRiskType(getRiskLevel(item.type))">
                      {{ getRiskText(item.type) }}
                    </el-tag>
                  </div>
                </div>
                
                <!-- 展开详情 -->
                <div class="card-detail" v-if="expandedCard === item.type" @click.stop>
                  <div class="detail-section">
                    <h5>📋 执行步骤</h5>
                    <el-steps direction="vertical" :space="40" :active="getSteps(item.type).length">
                      <el-step 
                        v-for="(step, index) in getSteps(item.type)" 
                        :key="index" 
                        :title="step"
                      />
                    </el-steps>
                  </div>
                  <div class="detail-section">
                    <h5>⚠️ 注意事项</h5>
                    <ul class="precaution-list">
                      <li v-for="(p, index) in getPrecautions(item.type)" :key="index">{{ p }}</li>
                    </ul>
                  </div>
                  <div class="detail-actions">
                    <el-button type="primary" @click.stop="viewDetail(item)">
                      查看完整详情
                    </el-button>
                    <el-button @click.stop="toggleIntervention(item.type)">
                      {{ isSelected(item.type) ? '取消选择' : '添加到模拟' }}
                    </el-button>
                  </div>
                </div>
                
                <!-- 展开提示 -->
                <div class="expand-hint" @click.stop="toggleCardExpand(item.type)">
                  <el-icon v-if="expandedCard !== item.type"><ArrowDown /></el-icon>
                  <el-icon v-else><ArrowUp /></el-icon>
                  <span>{{ expandedCard === item.type ? '收起' : '查看详情' }}</span>
                </div>
              </div>
            </div>
          </el-scrollbar>

          <!-- 操作按钮 -->
          <div class="action-buttons">
            <el-button
              type="primary"
              :loading="simulationStore.isRunning"
              :disabled="!canSimulate"
              @click="runSimulation"
            >
              <el-icon v-if="!simulationStore.isRunning"><Cpu /></el-icon>
              {{ simulationStore.isRunning ? '模拟中...' : '开始模拟' }}
            </el-button>
            <el-button @click="compareAll">
              <el-icon><DataAnalysis /></el-icon>
              对比所有方案
            </el-button>
          </div>
        </div>
      </el-col>

      <!-- 中间：模拟区域 -->
      <el-col :span="10">
        <div
          class="simulation-area"
          @dragover.prevent
          @drop="handleDrop"
          :class="{ 'drop-active': isDragging }"
        >
          <!-- 患者信息 -->
          <div class="patient-section">
            <h4>👤 患者信息</h4>
            <el-form :inline="true" :model="patientForm" class="patient-form">
              <el-form-item label="选择患者">
                <el-select
                  v-model="patientForm.patientId"
                  placeholder="请选择患者"
                  @change="handlePatientChange"
                >
                  <el-option
                    v-for="p in patientStore.patients"
                    :key="p.id"
                    :label="p.name"
                    :value="p.id"
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="疾病类型">
                <el-select v-model="patientForm.disease" @change="handleDiseaseChange">
                  <el-option label="糖尿病" value="diabetes" />
                  <el-option label="高血压" value="hypertension" />
                </el-select>
              </el-form-item>
            </el-form>
          </div>

          <!-- 当前指标 -->
          <div class="vitals-section">
            <h4>📊 当前指标</h4>
            <div class="vitals-grid">
              <div
                v-for="(value, key) in patientForm.vitals"
                :key="key"
                class="vital-card"
              >
                <div class="vital-label">{{ key }}</div>
                <el-input-number
                  v-model="patientForm.vitals[key]"
                  :min="0"
                  :max="300"
                  :step="0.1"
                  size="small"
                />
                <div class="vital-unit">{{ getVitalUnit(key) }}</div>
              </div>
            </div>
          </div>

          <!-- 已选干预方案 -->
          <div class="selected-section">
            <h4>✨ 已选干预方案</h4>
            <div class="selected-list" v-if="simulationStore.selectedInterventions.length > 0">
              <el-tag
                v-for="type in simulationStore.selectedInterventions"
                :key="type"
                :type="getInterventionType(type)"
                closable
                @close="removeIntervention(type)"
              >
                {{ getInterventionName(type) }}
              </el-tag>
            </div>
            <div class="empty-tip" v-else>
              <el-empty description="拖拽干预方案到此处" :image-size="60" />
            </div>
          </div>

          <!-- 模拟引导 -->
          <div class="guide-section" v-if="!simulationStore.hasResult">
            <el-alert
              title="操作引导"
              type="info"
              :closable="false"
            >
              <template #default>
                <ol class="guide-steps">
                  <li>选择或拖拽干预方案到模拟区域</li>
                  <li>确认患者信息和当前指标</li>
                  <li>点击"开始模拟"查看效果预测</li>
                </ol>
              </template>
            </el-alert>
          </div>
        </div>
      </el-col>

      <!-- 右侧：结果展示 -->
      <el-col :span="6">
        <div class="result-panel">
          <div class="panel-title">📈 模拟结果</div>
          
          <el-scrollbar v-if="simulationStore.hasResult">
            <!-- 干预方案信息 -->
            <div class="result-intervention">
              <div class="intervention-badge">
                {{ simulationStore.currentResult?.intervention.name }}
              </div>
              <div class="intervention-desc">
                {{ simulationStore.currentResult?.intervention.description }}
              </div>
            </div>

            <!-- 效果指标 -->
            <div class="effectiveness-card">
              <div class="effect-label">预期效果</div>
              <div class="effect-value">
                <span class="value">{{ simulationStore.currentResult?.effectiveness }}</span>
                <span class="unit">%</span>
              </div>
              <el-progress
                :percentage="simulationStore.currentResult?.effectiveness || 0"
                :color="getEffectivenessColor(simulationStore.currentResult?.effectiveness || 0)"
              />
            </div>

            <!-- 指标对比 -->
            <div class="comparison-card">
              <div class="comparison-title">指标变化预测</div>
              <div
                v-for="(predicted, key) in simulationStore.currentResult?.predicted"
                :key="key"
                class="comparison-item"
              >
                <div class="comp-label">{{ key }}</div>
                <div class="comp-values">
                  <span class="baseline">
                    {{ simulationStore.currentResult?.baseline[key] }}
                  </span>
                  <el-icon class="arrow"><Right /></el-icon>
                  <span class="predicted">
                    {{ predicted }}
                  </span>
                </div>
              </div>
            </div>

            <!-- 风险等级 -->
            <div class="risk-card" :class="simulationStore.currentResult?.risk_level">
              <div class="risk-label">风险等级</div>
              <el-tag :type="getRiskType(simulationStore.currentResult?.risk_level)">
                {{ simulationStore.currentResult?.risk_level === 'low' ? '低风险' : 
                   simulationStore.currentResult?.risk_level === 'medium' ? '中等风险' : '高风险' }}
              </el-tag>
            </div>

            <!-- 建议 -->
            <div class="recommendations-card">
              <div class="rec-title">💡 建议</div>
              <ul class="rec-list">
                <li v-for="(rec, i) in simulationStore.currentResult?.recommendations" :key="i">
                  {{ rec }}
                </li>
              </ul>
            </div>

            <!-- 图形化时间线 -->
            <div class="timeline-card" v-if="simulationStore.currentResult?.timeline && chartMetrics.length">
              <div class="timeline-title">📈 预测趋势图</div>
              
              <!-- 趋势对比展示 -->
              <div class="trend-comparison">
                <div v-for="metric in chartMetrics" :key="metric.key" class="comparison-row">
                  <div class="comparison-label">
                    <span class="label-dot" :style="{ background: metric.color }"></span>
                    <span class="label-text">{{ metric.label }}</span>
                  </div>
                  <div class="comparison-bars">
                    <div class="bar-container">
                      <div class="bar-baseline" :style="{ width: '100%', background: '#e8e8e8' }">
                        <span class="bar-value baseline-val">{{ getBaselineValue(metric.key) }}</span>
                      </div>
                    </div>
                    <div class="bar-arrow">→</div>
                    <div class="bar-container">
                      <div class="bar-predicted" :style="{ 
                        width: getTrendWidth(metric.key),
                        background: `linear-gradient(90deg, ${metric.color}, ${metric.color}cc)`
                      }">
                        <span class="bar-value predicted-val">{{ getPredictedValue(metric.key) }}</span>
                      </div>
                    </div>
                  </div>
                  <div class="comparison-change" :class="getChangeClass(metric.key)">
                    {{ getChangeText(metric.key) }}
                  </div>
                </div>
              </div>

              <!-- 30天趋势线 -->
              <div class="trend-timeline">
                <div class="timeline-header">
                  <span class="timeline-label">30天趋势</span>
                  <span class="timeline-range">Day 0 → Day 30</span>
                </div>
                <div class="timeline-track">
                  <div class="track-start">
                    <div class="track-point gray"></div>
                    <span>初始</span>
                  </div>
                  <div class="track-progress" :style="{ 
                    background: `linear-gradient(90deg, var(--color-success, #67c23a), var(--color-primary))`
                  }"></div>
                  <div class="track-end">
                    <div class="track-point green"></div>
                    <span>预期</span>
                  </div>
                </div>
                <div class="timeline-metrics">
                  <div class="metric-change" v-for="metric in chartMetrics" :key="'tm-'+metric.key">
                    <span class="metric-dot" :style="{ background: metric.color }"></span>
                    <span class="metric-name">{{ metric.label }}</span>
                    <span class="metric-arrow">↓</span>
                    <span class="metric-value" :class="getChangeClass(metric.key)">{{ getChangeText(metric.key) }}</span>
                  </div>
                </div>
              </div>

              <!-- 关键指标卡片 -->
              <div class="metrics-summary">
                <div class="summary-item improvement">
                  <div class="summary-icon">📉</div>
                  <div class="summary-content">
                    <span class="summary-label">预期改善</span>
                    <span class="summary-value">{{ simulationStore.currentResult?.effectiveness }}%</span>
                  </div>
                </div>
                <div class="summary-item duration">
                  <div class="summary-icon">⏱️</div>
                  <div class="summary-content">
                    <span class="summary-label">干预周期</span>
                    <span class="summary-value">30 天</span>
                  </div>
                </div>
                <div class="summary-item risk">
                  <div class="summary-icon">🛡️</div>
                  <div class="summary-content">
                    <span class="summary-label">风险等级</span>
                    <el-tag size="small" :type="getRiskType(simulationStore.currentResult?.risk_level)">
                      {{ simulationStore.currentResult?.risk_level === 'low' ? '低' : simulationStore.currentResult?.risk_level === 'medium' ? '中' : '高' }}
                    </el-tag>
                  </div>
                </div>
              </div>
            </div>
          </el-scrollbar>

          <el-empty v-else description="暂无模拟结果" :image-size="80" />
        </div>
      </el-col>
    </el-row>

    <!-- 对比结果弹窗 -->
    <el-dialog v-model="showCompare" title="📊 干预方案对比" width="80%">
      <el-table :data="simulationStore.compareResults" stripe>
        <el-table-column prop="intervention.name" label="方案" />
        <el-table-column label="预期效果">
          <template #default="{ row }">
            <el-progress :percentage="row.effectiveness" :color="getEffectivenessColor(row.effectiveness)" />
          </template>
        </el-table-column>
        <el-table-column prop="risk_level" label="风险等级">
          <template #default="{ row }">
            <el-tag :type="getRiskType(row.risk_level)">
              {{ row.risk_level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="applySimulation(row)">
              采用此方案
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 干预方案详情弹窗 -->
    <el-dialog v-model="showDetail" :title="interventionDetail?.name || '方案详情'" width="600px">
      <div v-if="interventionDetail" class="detail-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="方案类型">
            <el-tag>{{ interventionDetail.type }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="适用疾病">
            {{ interventionDetail.disease }}
          </el-descriptions-item>
          <el-descriptions-item label="预计周期">
            {{ interventionDetail.duration_days }} 天
          </el-descriptions-item>
          <el-descriptions-item label="有效率">
            <el-tag type="success">{{ interventionDetail.effectiveness }}%</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="风险等级">
            <el-tag :type="getRiskType(interventionDetail.risk_level)">
              {{ interventionDetail.risk_level }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <div class="detail-section">
          <h4>方案描述</h4>
          <p>{{ interventionDetail.description }}</p>
        </div>

        <div class="detail-section">
          <h4>执行步骤</h4>
          <el-steps direction="vertical" :space="60" :active="interventionDetail.steps?.length">
            <el-step 
              v-for="(step, index) in interventionDetail.steps" 
              :key="index" 
              :title="step"
            />
          </el-steps>
        </div>

        <div class="detail-section">
          <h4>注意事项</h4>
          <ul>
            <li v-for="(p, index) in interventionDetail.precautions" :key="index">
              {{ p }}
            </li>
          </ul>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useSimulationStore } from '@/stores/simulation'
import { usePatientStore } from '@/stores/patient'
import { simulationApi } from '@/api'

const simulationStore = useSimulationStore()
const patientStore = usePatientStore()

const isDragging = ref(false)
const showCompare = ref(false)
const showDetail = ref(false)
const interventionDetail = ref<any>(null)
const interventionsList = ref<any[]>([])
const expandedCard = ref<string | null>(null)  // 展开的卡片

// 干预方案详情数据
const interventionDetails: Record<string, {
  effectiveness: string
  duration: string
  risk: string
  steps: string[]
  precautions: string[]
}> = {
  diet: {
    effectiveness: '10-20%',
    duration: '2-4周',
    risk: 'low',
    steps: ['计算每日所需热量', '制定个性化食谱', '准备低GI食材', '记录每日饮食', '每周复盘调整'],
    precautions: ['避免极端节食', '注意营养均衡', '控制碳水化合物摄入', '定时定量用餐']
  },
  exercise: {
    effectiveness: '8-15%',
    duration: '2-4周',
    risk: 'low',
    steps: ['进行体能评估', '制定运动计划', '选择合适运动项目', '循序渐进开始运动', '记录运动数据', '定期评估调整'],
    precautions: ['运动前热身', '避免空腹运动', '注意运动强度', '如有不适停止运动']
  },
  medication: {
    effectiveness: '20-30%',
    duration: '1-2周',
    risk: 'medium',
    steps: ['遵医嘱用药', '按时服药', '观察药物效果', '记录不良反应', '定期复查'],
    precautions: ['遵医嘱用药', '不要自行调整药量', '注意药物相互作用', '定期复查']
  },
  combined: {
    effectiveness: '30-40%',
    duration: '4-8周',
    risk: 'low',
    steps: ['综合评估身体状况', '制定综合干预计划', '执行饮食方案', '执行运动计划', '定期监测指标', '每月复盘调整'],
    precautions: ['循序渐进', '坚持规律', '定期监测', '如有不适及时就医']
  },
  lifestyle: {
    effectiveness: '5-10%',
    duration: '2-4周',
    risk: 'low',
    steps: ['评估生活习惯', '识别风险因素', '制定改善计划', '逐步实施改变', '持续监测效果'],
    precautions: ['保持充足睡眠', '减少久坐时间', '戒烟限酒', '定期体检']
  }
}

// 切换卡片展开
const toggleCardExpand = (type: string) => {
  expandedCard.value = expandedCard.value === type ? null : type
}

// 获取方案详情
const getDetail = (type: string) => interventionDetails[type] || interventionDetails.combined

// 获取有效率范围
const getEffectivenessRange = (type: string) => getDetail(type).effectiveness

// 获取周期范围
const getDurationRange = (type: string) => getDetail(type).duration

// 获取风险等级
const getRiskLevel = (type: string) => getDetail(type).risk

// 获取风险文本
const getRiskText = (type: string) => {
  const map: Record<string, string> = { low: '低', medium: '中', high: '高' }
  return map[getRiskLevel(type)] || '低'
}

// 获取步骤
const getSteps = (type: string) => getDetail(type).steps

// 获取注意事项
const getPrecautions = (type: string) => getDetail(type).precautions

// 图表相关
const chartWidth = 400
const chartHeight = 300
const padding = 35
const hoveredPoint = ref('')

const colorPalette = ['#f56c6c', '#409eff', '#e6a23c', '#67c23a', '#9c27b0', '#00b894', '#fd79a8']

const chartMetrics = computed(() => {
  const timeline = simulationStore.currentResult?.timeline
  if (!timeline || timeline.length === 0) return []
  
  const dataKeys = Object.keys(timeline[0]).filter(k => k !== 'day')
  return dataKeys.map((key, idx) => {
    const values = timeline.map(p => p[key]).filter(v => v !== undefined)
    const min = Math.min(...values)
    const max = Math.max(...values)
    return {
      key,
      label: key,
      color: colorPalette[idx % colorPalette.length],
      unit: '',
      minVal: Math.floor(min * 0.8),
      maxVal: Math.ceil(max * 1.2)
    }
  })
})

const getXPosition = (index: number) => {
  const timeline = simulationStore.currentResult?.timeline
  if (!timeline || timeline.length === 0) return padding
  const step = (chartWidth - 2 * padding) / (timeline.length - 1)
  return padding + index * step
}

const getYPosition = (value: number | undefined, metric: any) => {
  if (value === undefined) return chartHeight / 2
  const range = metric.maxVal - metric.minVal
  const normalized = (value - metric.minVal) / range
  return padding + (1 - normalized) * (chartHeight - 2 * padding)
}

const getLinePoints = (metricKey: string) => {
  const timeline = simulationStore.currentResult?.timeline
  const metrics = chartMetrics
  if (!timeline || !metrics || !Array.isArray(metrics)) return ''
  const metric = metrics.find(m => m.key === metricKey)
  if (!metric) return ''
  return timeline.map((point, i) => {
    const x = getXPosition(i)
    const y = getYPosition(point[metricKey], metric)
    return `${x},${y}`
  }).join(' ')
}

const tooltipX = computed(() => {
  if (!hoveredPoint.value) return 0
  const [mIdx, pIdx] = hoveredPoint.value.split('-').map(Number)
  return getXPosition(pIdx)
})

const tooltipY = computed(() => {
  if (!hoveredPoint.value) return 0
  const [mIdx, pIdx] = hoveredPoint.value.split('-').map(Number)
  const timeline = simulationStore.currentResult?.timeline
  if (!timeline || !timeline[pIdx]) return 0
  const metric = chartMetrics[mIdx]
  return getYPosition(timeline[pIdx][metric.key], metric)
})

const tooltipText = computed(() => {
  if (!hoveredPoint.value) return ''
  const timeline = simulationStore.currentResult?.timeline
  if (!timeline) return ''
  const pIdx = hoveredPoint.value.split('-')[1]
  return `Day ${timeline[pIdx]?.day}`
})

const tooltipValue = computed(() => {
  if (!hoveredPoint.value) return ''
  const [mIdx, pIdx] = hoveredPoint.value.split('-').map(Number)
  const timeline = simulationStore.currentResult?.timeline
  if (!timeline || !timeline[pIdx]) return ''
  const metric = chartMetrics[mIdx]
  const value = timeline[pIdx][metric.key]
  return `${metric.label}: ${value} ${metric.unit}`
})

const getChangeClass = (metricKey: string) => {
  const timeline = simulationStore.currentResult?.timeline
  if (!timeline || timeline.length < 2) return ''
  const baseline = timeline[0][metricKey]
  const predicted = timeline[timeline.length - 1][metricKey]
  if (baseline > predicted) return 'positive'
  if (baseline < predicted) return 'negative'
  return ''
}

const getChangeText = (metricKey: string) => {
  const timeline = simulationStore.currentResult?.timeline
  if (!timeline || timeline.length < 2) return ''
  const baseline = timeline[0][metricKey]
  const predicted = timeline[timeline.length - 1][metricKey]
  if (baseline > predicted) {
    const change = (((baseline - predicted) / baseline) * 100).toFixed(1)
    return `↓${change}%`
  }
  if (baseline < predicted) {
    const change = (((predicted - baseline) / baseline) * 100).toFixed(1)
    return `↑${change}%`
  }
  return '无变化'
}

const getBaselineValue = (metricKey: string) => {
  const timeline = simulationStore.currentResult?.timeline
  if (!timeline || !timeline.length) return '-'
  return timeline[0][metricKey] ?? '-'
}

const getPredictedValue = (metricKey: string) => {
  const timeline = simulationStore.currentResult?.timeline
  if (!timeline || !timeline.length) return '-'
  return timeline[timeline.length - 1][metricKey] ?? '-'
}

const getTrendWidth = (metricKey: string) => {
  const timeline = simulationStore.currentResult?.timeline
  if (!timeline || timeline.length < 2) return '50%'
  const baseline = timeline[0][metricKey]
  const predicted = timeline[timeline.length - 1][metricKey]
  if (!baseline) return '50%'
  const change = ((baseline - predicted) / baseline) * 100
  const minWidth = 20
  const maxWidth = 95
  return Math.min(maxWidth, Math.max(minWidth, 50 + change)) + '%'
}

const patientForm = reactive({
  patientId: '',
  disease: 'diabetes',
  vitals: {
    '血糖': 9.5,
    'HbA1c': 8.5
  }
})

const diabetesVitals = { '血糖': 9.5, 'HbA1c': 8.5 }
const hypertensionVitals = { '收缩压': 155, '舒张压': 95 }

onMounted(async () => {
  await simulationStore.fetchInterventionTypes()
  await patientStore.fetchPatients()
  
  // 获取干预方案详情
  try {
    const res = await simulationApi.getInterventions()
    interventionsList.value = res.interventions
  } catch (e) {
    console.error('Failed to load interventions:', e)
  }
})

const isSelected = (type: string) => {
  return simulationStore.selectedInterventions.includes(type)
}

const toggleIntervention = (type: string) => {
  simulationStore.toggleIntervention(type)
}

const canSimulate = computed(() => {
  return patientForm.patientId && simulationStore.selectedInterventions.length > 0
})

const selectAll = () => {
  simulationStore.interventionTypes.forEach(item => {
    if (!isSelected(item.type)) {
      simulationStore.toggleIntervention(item.type)
    }
  })
}

const handleCardClick = (item: any) => {
  simulationStore.toggleIntervention(item.type)
}

const viewDetail = async (item: any) => {
  // 从列表中找到对应的详情
  const detail = interventionsList.value.find(i => i.type === item.type)
  if (detail) {
    interventionDetail.value = detail
    showDetail.value = true
  }
}

const handleDragStart = (event: DragEvent, item: any) => {
  isDragging.value = true
  event.dataTransfer?.setData('intervention', JSON.stringify(item))
}

const handleDrop = (event: DragEvent) => {
  isDragging.value = false
  const data = event.dataTransfer?.getData('intervention')
  if (data) {
    const item = JSON.parse(data)
    if (!isSelected(item.type)) {
      simulationStore.toggleIntervention(item.type)
      ElMessage.success(`已添加干预方案: ${item.name}`)
    }
  }
}

const removeIntervention = (type: string) => {
  simulationStore.toggleIntervention(type)
}

const handlePatientChange = (patientId: string) => {
  const patient = patientStore.patients.find(p => p.id === patientId)
  if (patient) {
    // 尝试从患者数据获取疾病信息
    const diseases = (patient as any).diseases || patientStore.currentPatient?.diseases || []
    
    if (diseases.length > 0) {
      if (diseases.includes('糖尿病')) {
        patientForm.disease = 'diabetes'
        patientForm.vitals = { ...diabetesVitals }
      } else if (diseases.includes('高血压')) {
        patientForm.disease = 'hypertension'
        patientForm.vitals = { ...hypertensionVitals }
      }
    }
    // 如果没有疾病信息，默认选择糖尿病
    if (!patientForm.disease) {
      patientForm.disease = 'diabetes'
      patientForm.vitals = { ...diabetesVitals }
    }
  }
}

const handleDiseaseChange = (disease: string) => {
  if (disease === 'diabetes') {
    patientForm.vitals = { ...diabetesVitals }
  } else {
    patientForm.vitals = { ...hypertensionVitals }
  }
}

const runSimulation = async () => {
  if (!canSimulate.value) {
    ElMessage.warning('请选择患者和干预方案')
    return
  }

  // 获取患者信息
  const patient = patientStore.patients.find(p => p.id === patientForm.patientId)
  const patientName = patient?.name || '患者'
  const patientAge = patient?.age

  await simulationStore.runSimulation(
    patientForm.patientId,
    patientForm.disease,
    patientForm.vitals,
    simulationStore.selectedInterventions.length === 1 
      ? simulationStore.selectedInterventions[0] 
      : 'combined',
    patientName,
    patientAge
  )

  ElMessage.success('模拟完成!')
}

const compareAll = async () => {
  if (!patientForm.patientId) {
    ElMessage.warning('请先选择患者')
    return
  }

  // 获取患者信息
  const patient = patientStore.patients.find(p => p.id === patientForm.patientId)
  const patientName = patient?.name || '患者'
  const patientAge = patient?.age

  await simulationStore.compareInterventions(
    patientForm.patientId,
    patientForm.disease,
    patientForm.vitals,
    patientName,
    patientAge
  )

  showCompare.value = true
}

const applySimulation = (result: any) => {
  ElMessage.success('方案已应用，请到聊天页面查看详细建议')
  showCompare.value = false
}

const getVitalUnit = (key: string): string => {
  if (key.includes('血糖') || key === 'HbA1c') return 'mmol/L'
  if (key.includes('压')) return 'mmHg'
  return ''
}

const getInterventionName = (type: string): string => {
  const item = simulationStore.interventionTypes.find(i => i.type === type)
  return item?.name || type
}

const getInterventionType = (type: string): string => {
  const map: Record<string, string> = {
    diet: 'success',
    exercise: '',
    medication: 'warning',
    lifestyle: 'info',
    combined: 'danger'
  }
  return map[type] || ''
}

const getEffectivenessColor = (value: number): string => {
  if (value >= 30) return '#67c23a'
  if (value >= 15) return '#e6a23c'
  return '#f56c6c'
}

const getRiskType = (risk?: string): string => {
  if (risk === 'low') return 'success'
  if (risk === 'medium') return 'warning'
  return 'danger'
}
</script>

<style scoped>
.simulation-view {
  padding: 20px;
  background: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.simulation-header {
  margin-bottom: 20px;
}

.simulation-header h2 {
  margin: 0 0 10px 0;
  color: #303133;
}

.subtitle {
  color: #909399;
  margin: 0;
}

/* 干预方案面板 */
.intervention-panel {
  background: white;
  border-radius: 12px;
  padding: 20px;
  height: calc(100vh - 180px);
  display: flex;
  flex-direction: column;
}

.panel-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  margin-bottom: 15px;
  color: #303133;
}

.intervention-list {
  flex: 1;
  overflow-y: auto;
}

.intervention-card {
  position: relative;
  padding: 15px;
  margin-bottom: 12px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
  background: #fafafa;
}

.intervention-card:hover {
  border-color: var(--item-color);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.intervention-card.selected {
  border-color: var(--item-color);
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.1), rgba(64, 158, 255, 0.05));
}

.intervention-card.expanded {
  border-color: var(--item-color);
  background: white;
}

/* 卡片头部 */
.card-header {
  display: flex;
  align-items: center;
}

.card-icon {
  font-size: 32px;
  margin-right: 12px;
}

.card-content {
  flex: 1;
}

.card-title {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.card-desc {
  font-size: 12px;
  color: #909399;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-check {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--item-color);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 关键指标 */
.card-metrics {
  display: flex;
  gap: 12px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #e8e8e8;
}

.metric-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.metric-label {
  font-size: 11px;
  color: #909399;
  margin-bottom: 4px;
}

.metric-value {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
}

.metric-value.effectiveness {
  color: #67c23a;
}

/* 展开详情 */
.card-detail {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #ebeef5;
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.detail-section {
  margin-bottom: 15px;
}

.detail-section h5 {
  margin: 0 0 10px 0;
  font-size: 13px;
  color: #303133;
  font-weight: 600;
}

.precaution-list {
  margin: 0;
  padding-left: 20px;
  color: #606266;
  font-size: 13px;
}

.precaution-list li {
  margin-bottom: 6px;
  line-height: 1.5;
}

.detail-actions {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}

/* 展开提示 */
.expand-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed #e8e8e8;
  color: #909399;
  font-size: 12px;
  cursor: pointer;
}

.expand-hint:hover {
  color: var(--item-color);
}

.action-buttons {
  margin-top: 20px;
  display: flex;
  gap: 10px;
}

/* 模拟区域 */
.simulation-area {
  background: white;
  border-radius: 12px;
  padding: 20px;
  min-height: calc(100vh - 180px);
  border: 2px dashed #dcdfe6;
  transition: all 0.3s;
}

.simulation-area.drop-active {
  border-color: var(--color-primary);
  background: #ecf5ff;
}

.simulation-area h4 {
  margin: 0 0 15px 0;
  color: #303133;
  font-size: 14px;
}

.patient-form {
  margin-bottom: 20px;
}

.patient-form .el-select {
  width: 200px;
}

.vitals-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
  margin-bottom: 20px;
}

.vital-card {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 8px;
  text-align: center;
}

.vital-label {
  font-size: 12px;
  color: #606266;
  margin-bottom: 8px;
}

.vital-unit {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.selected-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.empty-tip {
  padding: 20px;
}

.guide-section {
  margin-top: 20px;
}

.guide-steps {
  margin: 10px 0 0 20px;
  padding: 0;
}

.guide-steps li {
  margin-bottom: 5px;
  color: #606266;
}

/* 结果面板 */
.result-panel {
  background: white;
  border-radius: 12px;
  padding: 20px;
  height: calc(100vh - 180px);
}

.result-intervention {
  text-align: center;
  margin-bottom: 20px;
}

.intervention-badge {
  display: inline-block;
  padding: 8px 20px;
  background: var(--gradient-header);
  color: white;
  border-radius: 20px;
  font-weight: 600;
}

.intervention-desc {
  margin-top: 10px;
  color: #909399;
  font-size: 13px;
}

.effectiveness-card {
  text-align: center;
  padding: 20px;
  background: transparent;
  border-radius: 8px;
  margin-bottom: 15px;
}

.effect-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 10px;
}

.effect-value {
  font-size: 36px;
  font-weight: bold;
  color: var(--color-primary);
}

.effect-value .unit {
  font-size: 16px;
}

.comparison-card {
  padding: 15px;
  background: transparent;
  border-radius: 8px;
  margin-bottom: 15px;
}

.comparison-title {
  font-weight: 600;
  margin-bottom: 10px;
  color: #303133;
}

.comparison-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #eee;
}

.comparison-item:last-child {
  border-bottom: none;
}

.comp-values {
  display: flex;
  align-items: center;
  gap: 10px;
}

.baseline {
  color: #909399;
  text-decoration: line-through;
}

.predicted {
  color: #67c23a;
  font-weight: 600;
}

.arrow {
  color: var(--color-primary);
}

.risk-card {
  padding: 15px;
  border-radius: 8px;
  text-align: center;
  margin-bottom: 15px;
}

.risk-card.low {
  background: #f0f9ff;
}

.risk-card.medium {
  background: #fdf6ec;
}

.risk-card.high {
  background: #fef0f0;
}

.recommendations-card {
  padding: 15px;
  background: transparent;
  border-radius: 8px;
  margin-bottom: 15px;
}

.rec-title {
  font-weight: 600;
  margin-bottom: 10px;
}

.rec-list {
  margin: 0;
  padding-left: 20px;
  color: #606266;
}

.rec-list li {
  margin-bottom: 5px;
  font-size: 13px;
}

.timeline-card {
  padding: 15px;
}

.timeline-title {
  font-weight: 600;
  margin-bottom: 15px;
  color: #303133;
  font-size: 15px;
}

.trend-comparison {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 12px;
}

.comparison-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.comparison-label {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 70px;
}

.label-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.label-text {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
}

.comparison-bars {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.bar-container {
  flex: 1;
  height: 24px;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.bar-baseline {
  height: 100%;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 8px;
}

.bar-predicted {
  height: 100%;
  border-radius: 4px;
  display: flex;
  align-items: center;
  padding-left: 8px;
  transition: width 0.5s ease;
}

.bar-value {
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}

.baseline-val {
  color: #606266;
}

.predicted-val {
  color: white;
}

.bar-arrow {
  color: #c0c4cc;
  font-size: 14px;
  flex-shrink: 0;
}

.comparison-change {
  min-width: 60px;
  font-size: 13px;
  font-weight: 600;
  text-align: right;
}

.comparison-change.positive {
  color: #67c23a;
}

.comparison-change.negative {
  color: #f56c6c;
}

.trend-timeline {
  padding: 15px;
  background: linear-gradient(135deg, #f0f9eb 0%, #e8f4fd 100%);
  border-radius: 12px;
  margin-bottom: 15px;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.timeline-label {
  font-weight: 600;
  color: #303133;
  font-size: 13px;
}

.timeline-range {
  font-size: 11px;
  color: #909399;
}

.timeline-track {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
}

.track-start,
.track-end {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #606266;
}

.track-point {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.track-point.gray {
  background: #909399;
}

.track-point.green {
  background: #67c23a;
}

.track-progress {
  flex: 1;
  height: 4px;
  border-radius: 2px;
  position: relative;
}

.track-progress::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 2px;
  transform: translateY(-50%);
  background: inherit;
  opacity: 0.5;
}

.timeline-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
}

.metric-change {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.metric-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.metric-name {
  color: #606266;
}

.metric-arrow {
  color: #67c23a;
}

.metric-value {
  font-weight: 600;
}

.metric-value.positive {
  color: #67c23a;
}

.metric-value.negative {
  color: #f56c6c;
}

.metrics-summary {
  display: flex;
  justify-content: space-around;
  padding-top: 15px;
  border-top: 1px solid #eee;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.summary-icon {
  font-size: 20px;
}

.summary-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.summary-label {
  font-size: 11px;
  color: #909399;
}

.summary-value {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

/* 方案详情弹窗样式 */
.detail-content {
  padding: 10px;
}

.detail-section {
  margin-top: 20px;
}

.detail-section h4 {
  margin-bottom: 10px;
  color: #303133;
  font-size: 14px;
  font-weight: 600;
}

.detail-section p {
  color: #606266;
  line-height: 1.6;
}

.detail-section ul {
  padding-left: 20px;
  color: #606266;
}

.detail-section li {
  margin-bottom: 8px;
  line-height: 1.6;
}

/* 卡片操作按钮 - 已移除，改为展开详情模式 */</style>
