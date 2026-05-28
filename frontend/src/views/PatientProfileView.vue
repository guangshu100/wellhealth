<template>
  <div class="patient-profile-view">
    <div class="page-header">
      <h2>🧬 患者全景画像</h2>
      <p>慢病概览 · 用药全景 · 指标趋势 · 风险预测</p>
    </div>

    <el-card class="search-card">
      <el-form inline>
        <el-form-item label="患者ID">
          <el-input v-model="patientId" placeholder="请输入患者ID" style="width: 200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="loadPanorama">生成画像</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div v-if="panorama" class="profile-content">
      <el-card class="patient-info-card">
        <div class="patient-info">
          <span class="patient-name">{{ panorama.patient_name }}</span>
          <span class="patient-id">ID: {{ panorama.patient_id }}</span>
          <span class="generated-at">生成时间: {{ panorama.generated_at }}</span>
        </div>
      </el-card>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>🏥 慢病概览</span>
            </template>
            <div class="disease-tags">
              <el-tag
                v-for="d in panorama.chronic_diseases"
                :key="d.disease"
                :type="getControlStatusType(d.control_status)"
                size="large"
                class="disease-tag"
              >
                {{ d.disease }}
                <span class="control-status">（{{ d.control_status }}）</span>
              </el-tag>
            </div>
            <el-empty v-if="panorama.chronic_diseases.length === 0" description="暂无慢病记录" :image-size="40" />
          </el-card>
        </el-col>

        <el-col :span="12">
          <el-card>
            <template #header>
              <span>💊 用药全景</span>
            </template>
            <el-table :data="panorama.current_medications" size="small" border v-if="panorama.current_medications.length > 0">
              <el-table-column prop="drug" label="药品" />
              <el-table-column prop="dosage" label="剂量" width="100">
                <template #default="{ row }">{{ row.dosage || '-' }}</template>
              </el-table-column>
              <el-table-column prop="frequency" label="频次" width="120">
                <template #default="{ row }">{{ row.frequency || '-' }}</template>
              </el-table-column>
            </el-table>
            <el-empty v-else description="暂无用药记录" :image-size="40" />
          </el-card>
        </el-col>
      </el-row>

      <el-card style="margin-top: 16px;">
        <template #header>
          <span>📈 指标趋势</span>
        </template>
        <div class="vital-trends">
          <div v-for="(trend, key) in panorama.vital_trends" :key="key" class="vital-trend-item">
            <div class="trend-header">
              <span class="trend-name">{{ key }}</span>
              <el-tag :type="getTrendTagType(trend.trend)" size="small">{{ trend.trend }}</el-tag>
            </div>
            <div class="trend-info">
              <span>最新: {{ trend.latest }}</span>
              <span v-if="trend.target">目标: {{ trend.target }}</span>
              <span>数据点: {{ trend.data_points }}</span>
            </div>
          </div>
        </div>
        <VChart v-if="vitalChartOption" :option="vitalChartOption" style="height: 350px; margin-top: 16px;" autoresize />
      </el-card>

      <el-row :gutter="16" style="margin-top: 16px;">
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>🔍 缺失指标</span>
            </template>
            <div class="missing-indicators" v-if="panorama.missing_indicators.length > 0">
              <el-tag
                v-for="m in panorama.missing_indicators"
                :key="m.indicator"
                :type="getSeverityType(m.severity)"
                class="missing-tag"
              >
                {{ m.indicator }}（缺失{{ m.missing_days }}天）
              </el-tag>
            </div>
            <el-empty v-else description="无缺失指标" :image-size="40" />
          </el-card>
        </el-col>

        <el-col :span="12">
          <el-card>
            <template #header>
              <span>⚠️ 风险预测</span>
            </template>
            <div class="risk-prediction">
              <div class="risk-item">
                <span class="risk-label">并发症风险</span>
                <VChart :option="getGaugeOption(panorama.risk_prediction.complication_risk)" style="height: 180px;" autoresize />
              </div>
              <div class="risk-item">
                <span class="risk-label">住院风险</span>
                <VChart :option="getGaugeOption(panorama.risk_prediction.hospitalization_risk)" style="height: 180px;" autoresize />
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-card v-if="panorama.interventions.length > 0" style="margin-top: 16px;">
        <template #header>
          <span>📋 干预记录</span>
        </template>
        <el-table :data="panorama.interventions" size="small" border>
          <el-table-column prop="type" label="类型" width="120" />
          <el-table-column prop="date" label="日期" width="140">
            <template #default="{ row }">{{ row.date || '-' }}</template>
          </el-table-column>
          <el-table-column prop="detail" label="详情" />
        </el-table>
      </el-card>
    </div>

    <el-card v-else-if="!loading">
      <el-empty description="请输入患者ID生成画像" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import VChart from 'vue-echarts'
import 'echarts'
import { patientProfileApi, type PatientPanorama } from '@/api'

const patientId = ref('')
const loading = ref(false)
const panorama = ref<PatientPanorama | null>(null)

const vitalChartOption = computed(() => {
  if (!panorama.value) return null
  const trends = panorama.value.vital_trends
  const keys = Object.keys(trends)
  if (keys.length === 0) return null

  const nameMap: Record<string, string> = {
    blood_sugar: '血糖',
    blood_pressure: '血压',
    weight: '体重'
  }

  const parseValue = (val: unknown): number | null => {
    if (typeof val === 'number') return val
    if (typeof val === 'string') {
      const match = val.match(/(\d+\.?\d*)/)
      return match ? parseFloat(match[1]) : null
    }
    return null
  }

  const parseTarget = (val: string | null): number | null => {
    if (!val) return null
    const match = val.match(/(\d+\.?\d*)/)
    return match ? parseFloat(match[1]) : null
  }

  const indicators = keys
    .map(key => {
      const current = parseValue(trends[key].latest)
      const target = parseTarget(trends[key].target)
      return { key, name: nameMap[key] || key, current, target }
    })
    .filter(item => item.current !== null)

  if (indicators.length === 0) return null

  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['当前值', '目标值'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: indicators.map(i => i.name)
    },
    yAxis: { type: 'value' },
    series: [
      {
        name: '当前值',
        type: 'bar' as const,
        data: indicators.map(i => i.current),
        itemStyle: { color: '#409EFF' }
      },
      {
        name: '目标值',
        type: 'bar' as const,
        data: indicators.map(i => i.target),
        itemStyle: { color: '#67C23A' }
      }
    ]
  }
})

const getGaugeOption = (riskLevel: string | number) => {
  const valueMap: Record<string, number> = {
    low: 25,
    medium: 55,
    high: 80,
    very_high: 95
  }
  const colorMap: Record<string, string> = {
    low: '#67C23A',
    medium: '#E6A23C',
    high: '#F56C6C',
    very_high: '#F56C6C'
  }
  const labelMap: Record<string, string> = {
    low: '低风险',
    medium: '中风险',
    high: '高风险',
    very_high: '极高风险'
  }
  const val = typeof riskLevel === 'number' ? riskLevel : (valueMap[riskLevel] ?? 50)
  const color = typeof riskLevel === 'number'
    ? (val >= 80 ? '#F56C6C' : val >= 55 ? '#E6A23C' : '#67C23A')
    : (colorMap[riskLevel] ?? '#909399')
  const label = typeof riskLevel === 'number' ? '' : (labelMap[riskLevel] ?? String(riskLevel))

  return {
    series: [{
      type: 'gauge',
      startAngle: 200,
      endAngle: -20,
      min: 0,
      max: 100,
      progress: { show: true, width: 14 },
      axisLine: { lineStyle: { width: 14 } },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      pointer: { show: false },
      title: { offsetCenter: [0, '60%'], fontSize: 14 },
      detail: {
        valueAnimation: true,
        offsetCenter: [0, '30%'],
        formatter: `{value}%`,
        color,
        fontSize: 22,
        fontWeight: 'bold'
      },
      data: [{ value: val, name: label }]
    }]
  }
}

const loadPanorama = async () => {
  if (!patientId.value.trim()) {
    ElMessage.warning('请输入患者ID')
    return
  }
  loading.value = true
  try {
    const result = await patientProfileApi.getPanorama(patientId.value.trim())
    panorama.value = result
    ElMessage.success('画像生成成功')
  } catch (error) {
    ElMessage.error('获取画像失败')
  } finally {
    loading.value = false
  }
}

const getControlStatusType = (status: string) => {
  const map: Record<string, string> = {
    '良好': 'success',
    '一般': 'warning',
    '较差': 'danger'
  }
  return map[status] || 'info'
}

const getTrendTagType = (trend: string) => {
  const map: Record<string, string> = {
    rising: 'danger',
    falling: 'success',
    stable: 'info',
    improving: 'success',
    worsening: 'danger'
  }
  return map[trend] || 'info'
}

const getSeverityType = (severity: string) => {
  const map: Record<string, string> = {
    critical: 'danger',
    important: 'warning',
    general: 'info'
  }
  return map[severity] || 'info'
}
</script>

<style scoped>
.patient-profile-view {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.page-header p {
  color: #909399;
  margin: 5px 0 0;
}

.search-card {
  margin-bottom: 16px;
}

.patient-info-card {
  margin-bottom: 16px;
}

.patient-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.patient-name {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
}

.patient-id {
  color: #606266;
}

.generated-at {
  color: #909399;
  font-size: 12px;
  margin-left: auto;
}

.disease-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.disease-tag {
  font-size: 14px;
}

.control-status {
  font-size: 12px;
  opacity: 0.8;
}

.vital-trends {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.vital-trend-item {
  padding: 10px;
  background: #f5f7fa;
  border-radius: 8px;
}

.trend-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.trend-name {
  font-weight: 600;
  color: #303133;
}

.trend-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 12px;
  color: #909399;
}

.missing-indicators {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.missing-tag {
  margin: 4px;
}

.risk-prediction {
  display: flex;
  justify-content: space-around;
}

.risk-item {
  text-align: center;
  flex: 1;
}

.risk-label {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  display: block;
  margin-bottom: 4px;
}
</style>
