<template>
  <div class="data-insight-view">
    <div class="page-header">
      <h2>🔬 数据洞察</h2>
      <p>疾病轨迹 · 指标规律 · What-If仿真 · 共病网络 · 流行病学预警</p>
    </div>

    <el-tabs v-model="activeTab" type="border-card">
      <el-tab-pane label="🦠 疾病轨迹" name="trajectory">
        <el-card>
          <el-form inline>
            <el-form-item label="患者ID">
              <el-input v-model="trajectoryForm.patient_id" placeholder="患者ID" style="width: 160px" />
            </el-form-item>
            <el-form-item label="时间范围">
              <el-select v-model="trajectoryForm.time_range" style="width: 140px">
                <el-option label="近3个月" value="3m" />
                <el-option label="近6个月" value="6m" />
                <el-option label="近1年" value="1y" />
                <el-option label="近2年" value="2y" />
                <el-option label="全部" value="all" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="trajectoryLoading" @click="fetchTrajectory">分析</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-row :gutter="16" v-if="trajectoryResult" style="margin-top: 16px;">
          <el-col :span="12">
            <el-card>
              <template #header>📈 疾病轨迹</template>
              <VChart :option="trajectoryChartOption" style="height: 350px;" autoresize />
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card>
              <template #header>🔄 状态转移矩阵</template>
              <VChart :option="transitionMatrixOption" style="height: 350px;" autoresize />
            </el-card>
          </el-col>
        </el-row>

        <el-card v-if="trajectoryResult" style="margin-top: 16px;">
          <el-descriptions :column="3" border>
            <el-descriptions-item label="数据点数">{{ trajectoryResult.data_points }}</el-descriptions-item>
            <el-descriptions-item label="时间范围">{{ trajectoryResult.time_range }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="📊 指标规律" name="indicator">
        <el-card>
          <el-form inline>
            <el-form-item label="患者ID">
              <el-input v-model="indicatorForm.patient_id" placeholder="患者ID" style="width: 160px" />
            </el-form-item>
            <el-form-item label="指标">
              <el-checkbox-group v-model="indicatorForm.indicators">
                <el-checkbox label="blood_sugar">血糖</el-checkbox>
                <el-checkbox label="blood_pressure">血压</el-checkbox>
                <el-checkbox label="heart_rate">心率</el-checkbox>
                <el-checkbox label="weight">体重</el-checkbox>
                <el-checkbox label="HbA1c">糖化血红蛋白</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="indicatorLoading" @click="fetchIndicatorPattern">分析</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-row :gutter="16" v-if="indicatorResult" style="margin-top: 16px;">
          <el-col :span="14">
            <el-card>
              <template #header>📈 指标相关性</template>
              <VChart :option="correlationChartOption" style="height: 350px;" autoresize />
            </el-card>
          </el-col>
          <el-col :span="10">
            <el-card>
              <template #header>📋 指标统计</template>
              <div v-for="(pattern, key) in indicatorResult.patterns" :key="key" class="pattern-item">
                <h4>{{ key }}</h4>
                <el-descriptions :column="2" size="small" border>
                  <el-descriptions-item label="均值">{{ pattern.mean?.toFixed(2) }}</el-descriptions-item>
                  <el-descriptions-item label="标准差">{{ pattern.std?.toFixed(2) }}</el-descriptions-item>
                  <el-descriptions-item label="最小值">{{ pattern.min }}</el-descriptions-item>
                  <el-descriptions-item label="最大值">{{ pattern.max }}</el-descriptions-item>
                  <el-descriptions-item label="季节性">
                    <el-tag :type="pattern.seasonality?.detected ? 'success' : 'info'" size="small">
                      {{ pattern.seasonality?.detected ? '检测到' : '未检测到' }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="周期" v-if="pattern.seasonality?.detected">
                    {{ pattern.seasonality.period }} 天
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <el-tab-pane label="🧪 What-If仿真" name="whatif">
        <el-card>
          <el-form inline>
            <el-form-item label="患者ID">
              <el-input v-model="whatifForm.patient_id" placeholder="患者ID" style="width: 160px" />
            </el-form-item>
            <el-form-item label="干预类型">
              <el-select v-model="whatifForm.intervention_type" style="width: 160px">
                <el-option label="停药" value="stop_medication" />
                <el-option label="增加运动" value="add_exercise" />
                <el-option label="饮食调整" value="diet_change" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="whatifLoading" @click="fetchWhatif">仿真</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-row :gutter="16" v-if="whatifResult" style="margin-top: 16px;">
          <el-col :span="14">
            <el-card>
              <template #header>📈 预测趋势</template>
              <VChart :option="whatifChartOption" style="height: 350px;" autoresize />
            </el-card>
          </el-col>
          <el-col :span="10">
            <el-card>
              <template #header>🔍 SHAP特征重要性</template>
              <VChart :option="shapChartOption" style="height: 350px;" autoresize />
            </el-card>
          </el-col>
        </el-row>

        <el-card v-if="whatifResult" style="margin-top: 16px;">
          <el-descriptions :column="3" border>
            <el-descriptions-item label="置信度">{{ (whatifResult.confidence * 100).toFixed(1) }}%</el-descriptions-item>
            <el-descriptions-item label="基线血糖">{{ whatifResult.baseline?.blood_sugar }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="🕸️ 共病网络" name="comorbidity">
        <el-card>
          <el-form inline>
            <el-form-item label="最小支持度">
              <el-input-number v-model="comorbidityForm.min_support" :min="1" :max="100" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="comorbidityLoading" @click="fetchComorbidity">生成网络</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-row :gutter="16" v-if="comorbidityResult" style="margin-top: 16px;">
          <el-col :span="16">
            <el-card>
              <template #header>🕸️ 共病网络图</template>
              <VChart :option="comorbidityChartOption" style="height: 500px;" autoresize />
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card>
              <template #header>📊 社区发现</template>
              <div v-for="community in comorbidityResult.communities" :key="community.id" class="community-item">
                <h4>社区 {{ community.id + 1 }}（{{ community.size }}个疾病）</h4>
                <div class="community-members">
                  <el-tag v-for="m in community.members" :key="m" size="small" style="margin: 2px;">{{ m }}</el-tag>
                </div>
              </div>
              <el-descriptions :column="1" border style="margin-top: 12px;">
                <el-descriptions-item label="总患者数">{{ comorbidityResult.total_patients }}</el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <el-tab-pane label="🚨 流行病学预警" name="epidemiology">
        <el-card>
          <el-form inline>
            <el-form-item label="监测指标">
              <el-input v-model="epidemiologyForm.indicator" placeholder="如: blood_sugar" style="width: 160px" />
            </el-form-item>
            <el-form-item label="阈值(Z-score)">
              <el-input-number v-model="epidemiologyForm.threshold" :min="1" :max="5" :step="0.5" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="epidemiologyLoading" @click="fetchEpidemiology">检测</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card v-if="epidemiologyResult" style="margin-top: 16px;">
          <template #header>
            <div class="epidemiology-header">
              <span>🚨 预警结果</span>
              <el-tag type="danger">{{ epidemiologyResult.alerts.length }} 条预警</el-tag>
            </div>
          </template>
          <el-descriptions :column="4" border style="margin-bottom: 16px;">
            <el-descriptions-item label="监测指标">{{ epidemiologyResult.indicator }}</el-descriptions-item>
            <el-descriptions-item label="均值">{{ epidemiologyResult.mean?.toFixed(2) }}</el-descriptions-item>
            <el-descriptions-item label="标准差">{{ epidemiologyResult.std?.toFixed(2) }}</el-descriptions-item>
            <el-descriptions-item label="受影响患者">{{ epidemiologyResult.affected_patients }}</el-descriptions-item>
          </el-descriptions>

          <el-table :data="epidemiologyResult.alerts" border size="small">
            <el-table-column prop="patient_id" label="患者ID" />
            <el-table-column prop="value" label="指标值" width="100" />
            <el-table-column prop="z_score" label="Z-Score" width="100">
              <template #default="{ row }">{{ row.z_score?.toFixed(2) }}</template>
            </el-table-column>
            <el-table-column prop="severity" label="严重程度" width="100">
              <template #default="{ row }">
                <el-tag :type="row.severity === 'high' ? 'danger' : row.severity === 'medium' ? 'warning' : 'info'" size="small">
                  {{ row.severity }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import VChart from 'vue-echarts'
import 'echarts'
import {
  dataMiningApi,
  type DiseaseTrajectoryResult,
  type IndicatorPatternResult,
  type WhatIfResult,
  type ComorbidityResult,
  type EpidemiologyResult
} from '@/api'

const activeTab = ref('trajectory')

const trajectoryForm = reactive({ patient_id: '', time_range: '1y' })
const trajectoryLoading = ref(false)
const trajectoryResult = ref<DiseaseTrajectoryResult | null>(null)

const indicatorForm = reactive({ patient_id: '', indicators: ['blood_sugar'] as string[] })
const indicatorLoading = ref(false)
const indicatorResult = ref<IndicatorPatternResult | null>(null)

const whatifForm = reactive({ patient_id: '', intervention_type: 'add_exercise' })
const whatifLoading = ref(false)
const whatifResult = ref<WhatIfResult | null>(null)

const comorbidityForm = reactive({ min_support: 5 })
const comorbidityLoading = ref(false)
const comorbidityResult = ref<ComorbidityResult | null>(null)

const epidemiologyForm = reactive({ indicator: 'blood_sugar', threshold: 2.0 })
const epidemiologyLoading = ref(false)
const epidemiologyResult = ref<EpidemiologyResult | null>(null)

const trajectoryChartOption = computed(() => {
  if (!trajectoryResult.value?.trajectory?.length) return {}
  const data = trajectoryResult.value.trajectory
  const keys = Object.keys(data[0].values || {})
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: keys },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: data.map(d => d.date), boundaryGap: false },
    yAxis: { type: 'value' },
    series: keys.map(key => ({
      name: key,
      type: 'line' as const,
      smooth: true,
      data: data.map(d => (d.values as Record<string, number>)[key])
    }))
  }
})

const transitionMatrixOption = computed(() => {
  if (!trajectoryResult.value?.transition_matrix) return {}
  const { states, matrix } = trajectoryResult.value.transition_matrix
  const data: number[][] = []
  for (let i = 0; i < states.length; i++) {
    for (let j = 0; j < states.length; j++) {
      data.push([i, j, matrix[i]?.[j] || 0])
    }
  }
  return {
    tooltip: {
      formatter: (p: { data: number[] }) => {
        return `${states[p.data[0]]} → ${states[p.data[1]]}: ${(p.data[2] * 100).toFixed(1)}%`
      }
    },
    grid: { left: '15%', right: '10%', bottom: '15%', top: '5%' },
    xAxis: { type: 'category', data: states, splitArea: { show: true } },
    yAxis: { type: 'category', data: states, splitArea: { show: true } },
    visualMap: { min: 0, max: 1, calculable: true, orient: 'horizontal', left: 'center', bottom: '2%' },
    series: [{
      type: 'heatmap' as const,
      data,
      label: { show: true, formatter: (p: { data: number[] }) => (p.data[2] * 100).toFixed(0) + '%' },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
    }]
  }
})

const correlationChartOption = computed(() => {
  if (!indicatorResult.value?.patterns) return {}
  const patterns = indicatorResult.value.patterns
  const keys = Object.keys(patterns)
  const allCorrelations: Array<{ indicator: string; target: string; value: number }> = []
  keys.forEach(key => {
    const corr = patterns[key].correlations || {}
    Object.entries(corr).forEach(([target, value]) => {
      allCorrelations.push({ indicator: key, target, value: value as number })
    })
  })
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: allCorrelations.map(c => `${c.indicator}-${c.target}`) },
    yAxis: { type: 'value', min: -1, max: 1 },
    series: [{
      type: 'bar' as const,
      data: allCorrelations.map(c => ({
        value: c.value,
        itemStyle: { color: c.value >= 0 ? '#67C23A' : '#F56C6C' }
      }))
    }]
  }
})

const whatifChartOption = computed(() => {
  if (!whatifResult.value?.prediction?.length) return {}
  const pred = whatifResult.value.prediction
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: pred.map(p => `第${p.month}月`), boundaryGap: false },
    yAxis: { type: 'value', name: '血糖' },
    series: [{
      type: 'line' as const,
      smooth: true,
      data: pred.map(p => p.blood_sugar),
      areaStyle: { opacity: 0.15 },
      itemStyle: { color: '#409EFF' },
      markLine: {
        data: [{ yAxis: whatifResult.value?.baseline?.blood_sugar, name: '基线' }]
      }
    }]
  }
})

const shapChartOption = computed(() => {
  if (!whatifResult.value?.shap_values) return {}
  const shap = whatifResult.value.shap_values
  const entries = Object.entries(shap).sort(([, a], [, b]) => Math.abs(b as number) - Math.abs(a as number))
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: '25%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'value', name: 'SHAP值' },
    yAxis: { type: 'category', data: entries.map(e => e[0]) },
    series: [{
      type: 'bar' as const,
      data: entries.map(e => ({
        value: e[1],
        itemStyle: { color: (e[1] as number) >= 0 ? '#67C23A' : '#F56C6C' }
      }))
    }]
  }
})

const comorbidityChartOption = computed(() => {
  if (!comorbidityResult.value?.network) return {}
  const { nodes, edges } = comorbidityResult.value.network
  const categories = comorbidityResult.value.communities.map((c, i) => ({ name: `社区${i + 1}` }))
  const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4']

  return {
    tooltip: {},
    legend: { data: categories.map(c => c.name) },
    series: [{
      type: 'graph' as const,
      layout: 'force' as const,
      animation: true,
      draggable: true,
      data: nodes.map((n, i) => ({
        name: n.id,
        value: n.count,
        symbolSize: Math.max(20, Math.min(60, n.prevalence * 200)),
        category: comorbidityResult.value!.communities.findIndex(c => c.members.includes(n.id)),
        itemStyle: { color: colors[i % colors.length] },
        label: { show: true, fontSize: 11 }
      })),
      links: edges.map(e => ({
        source: e.source,
        target: e.target,
        value: e.weight,
        lineStyle: { width: Math.max(1, e.weight * 5), opacity: 0.6 }
      })),
      categories,
      roam: true,
      force: { repulsion: 300, edgeLength: [80, 200], gravity: 0.1 },
      emphasis: { focus: 'adjacency', lineStyle: { width: 4 } }
    }]
  }
})

const fetchTrajectory = async () => {
  if (!trajectoryForm.patient_id) {
    ElMessage.warning('请输入患者ID')
    return
  }
  trajectoryLoading.value = true
  try {
    const result = await dataMiningApi.diseaseTrajectory({
      patient_id: trajectoryForm.patient_id,
      time_range: trajectoryForm.time_range
    })
    trajectoryResult.value = result
    ElMessage.success('分析完成')
  } catch (error) {
    ElMessage.error('分析失败')
  } finally {
    trajectoryLoading.value = false
  }
}

const fetchIndicatorPattern = async () => {
  if (!indicatorForm.patient_id) {
    ElMessage.warning('请输入患者ID')
    return
  }
  if (indicatorForm.indicators.length === 0) {
    ElMessage.warning('请至少选择一个指标')
    return
  }
  indicatorLoading.value = true
  try {
    const result = await dataMiningApi.indicatorPattern({
      patient_id: indicatorForm.patient_id,
      indicators: indicatorForm.indicators
    })
    indicatorResult.value = result
    ElMessage.success('分析完成')
  } catch (error) {
    ElMessage.error('分析失败')
  } finally {
    indicatorLoading.value = false
  }
}

const fetchWhatif = async () => {
  if (!whatifForm.patient_id) {
    ElMessage.warning('请输入患者ID')
    return
  }
  whatifLoading.value = true
  try {
    const result = await dataMiningApi.whatifSimulation({
      patient_id: whatifForm.patient_id,
      intervention: { type: whatifForm.intervention_type }
    })
    whatifResult.value = result
    ElMessage.success('仿真完成')
  } catch (error) {
    ElMessage.error('仿真失败')
  } finally {
    whatifLoading.value = false
  }
}

const fetchComorbidity = async () => {
  comorbidityLoading.value = true
  try {
    const result = await dataMiningApi.comorbidityNetwork({
      min_support: comorbidityForm.min_support
    })
    comorbidityResult.value = result
    ElMessage.success('网络生成完成')
  } catch (error) {
    ElMessage.error('生成失败')
  } finally {
    comorbidityLoading.value = false
  }
}

const fetchEpidemiology = async () => {
  if (!epidemiologyForm.indicator) {
    ElMessage.warning('请输入监测指标')
    return
  }
  epidemiologyLoading.value = true
  try {
    const result = await dataMiningApi.epidemiologyAlert({
      indicator: epidemiologyForm.indicator,
      threshold: epidemiologyForm.threshold
    })
    epidemiologyResult.value = result
    ElMessage.success('检测完成')
  } catch (error) {
    ElMessage.error('检测失败')
  } finally {
    epidemiologyLoading.value = false
  }
}
</script>

<style scoped>
.data-insight-view {
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

.pattern-item {
  margin-bottom: 16px;
}

.pattern-item h4 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 14px;
}

.community-item {
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.community-item:last-child {
  border-bottom: none;
}

.community-item h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #303133;
}

.community-members {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.epidemiology-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
