<template>
  <div class="dashboard-view">
    <div class="dashboard-header">
      <h2>📊 管理仪表盘</h2>
      <div class="header-actions">
        <el-tag type="info" size="small">自动刷新: 30s</el-tag>
        <el-button size="small" @click="refreshAll" :loading="refreshing">手动刷新</el-button>
      </div>
    </div>

    <el-row :gutter="16" class="stat-row">
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: linear-gradient(135deg, #409EFF, #66b1ff);">
            <span>👥</span>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ macroStats?.total_patients ?? '-' }}</div>
            <div class="stat-label">总患者数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: linear-gradient(135deg, #67C23A, #85ce61);">
            <span>📈</span>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ macroStats?.new_this_month ?? '-' }}</div>
            <div class="stat-label">本月新增</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: linear-gradient(135deg, #E6A23C, #ebb563);">
            <span>🩺</span>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ macroStats?.active_patients ?? '-' }}</div>
            <div class="stat-label">活跃患者</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: linear-gradient(135deg, #F56C6C, #f78989);">
            <span>📊</span>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ macroStats ? (macroStats.active_rate * 100).toFixed(1) + '%' : '-' }}</div>
            <div class="stat-label">活跃率</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>🏥 疾病分布</span>
          </template>
          <VChart v-if="diseaseChartOption" :option="diseaseChartOption" style="height: 350px;" autoresize />
          <el-empty v-else description="暂无数据" :image-size="60" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>💊 依从性统计</span>
          </template>
          <div v-if="adherenceStats" class="adherence-content">
            <VChart :option="adherenceGaugeOption" style="height: 280px;" autoresize />
            <el-descriptions :column="2" border size="small" style="margin-top: 12px;">
              <el-descriptions-item label="总记录数">{{ adherenceStats.total_records }}</el-descriptions-item>
              <el-descriptions-item label="已服药记录">{{ adherenceStats.taken_records }}</el-descriptions-item>
            </el-descriptions>
          </div>
          <el-empty v-else description="暂无数据" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 16px;">
      <template #header>
        <span>📦 资源利用</span>
      </template>
      <el-row :gutter="16" v-if="resourceUtilization">
        <el-col :span="12">
          <div class="resource-item">
            <el-statistic title="处方总数" :value="resourceUtilization.total_prescriptions">
              <template #suffix>张</template>
            </el-statistic>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="resource-item">
            <el-statistic title="人均用药数" :value="resourceUtilization.avg_medications_per_patient" :precision="1">
              <template #suffix>种</template>
            </el-statistic>
          </div>
        </el-col>
      </el-row>
      <el-empty v-else description="暂无数据" :image-size="60" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import VChart from 'vue-echarts'
import 'echarts'
import {
  dashboardApi,
  type MacroStats,
  type DiseaseDistribution,
  type AdherenceStats,
  type ResourceUtilization
} from '@/api'

const refreshing = ref(false)
const macroStats = ref<MacroStats | null>(null)
const diseaseDistribution = ref<DiseaseDistribution | null>(null)
const adherenceStats = ref<AdherenceStats | null>(null)
const resourceUtilization = ref<ResourceUtilization | null>(null)

let refreshTimer: ReturnType<typeof setInterval> | null = null

const diseaseChartOption = computed(() => {
  if (!diseaseDistribution.value?.by_disease?.length) return null
  const data = diseaseDistribution.value.by_disease
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { orient: 'vertical', left: 'left', top: 'middle' },
    series: [{
      type: 'pie' as const,
      radius: ['40%', '70%'],
      center: ['60%', '50%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: true, formatter: '{b}\n{d}%' },
      data: data.map(d => ({ name: d.disease, value: d.count }))
    }]
  }
})

const adherenceGaugeOption = computed(() => {
  if (!adherenceStats.value) return {}
  const rate = adherenceStats.value.overall_rate
  return {
    series: [{
      type: 'gauge',
      startAngle: 200,
      endAngle: -20,
      min: 0,
      max: 100,
      progress: { show: true, width: 18 },
      axisLine: { lineStyle: { width: 18 } },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      pointer: { show: false },
      title: { offsetCenter: [0, '70%'], fontSize: 14, color: '#606266' },
      detail: {
        valueAnimation: true,
        offsetCenter: [0, '40%'],
        formatter: '{value}%',
        fontSize: 28,
        fontWeight: 'bold',
        color: rate >= 80 ? '#67C23A' : rate >= 60 ? '#E6A23C' : '#F56C6C'
      },
      data: [{ value: +(rate * 100).toFixed(1), name: '依从率' }]
    }]
  }
})

const loadMacroStats = async () => {
  try {
    macroStats.value = await dashboardApi.getMacroStats()
  } catch (e) {
  }
}

const loadDiseaseDistribution = async () => {
  try {
    diseaseDistribution.value = await dashboardApi.getDiseaseDistribution()
  } catch (e) {
  }
}

const loadAdherenceStats = async () => {
  try {
    adherenceStats.value = await dashboardApi.getAdherenceStats()
  } catch (e) {
  }
}

const loadResourceUtilization = async () => {
  try {
    resourceUtilization.value = await dashboardApi.getResourceUtilization()
  } catch (e) {
  }
}

const refreshAll = async () => {
  refreshing.value = true
  try {
    await Promise.all([
      loadMacroStats(),
      loadDiseaseDistribution(),
      loadAdherenceStats(),
      loadResourceUtilization()
    ])
    ElMessage.success('数据已刷新')
  } finally {
    refreshing.value = false
  }
}

onMounted(() => {
  refreshAll()
  refreshTimer = setInterval(refreshAll, 30000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
})
</script>

<style scoped>
.dashboard-view {
  padding: 20px;
  background: #f0f2f5;
  min-height: calc(100vh - 60px);
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px 24px;
  background: linear-gradient(135deg, #1d1e2c, #2d2e42);
  border-radius: 12px;
  color: white;
}

.dashboard-header h2 {
  margin: 0;
  font-size: 22px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-row {
  margin-bottom: 0;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 0;
}

.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
  padding: 20px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.adherence-content {
  text-align: center;
}

.resource-item {
  text-align: center;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}
</style>
