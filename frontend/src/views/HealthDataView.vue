<template>
  <div class="health-data-container">
    <el-card class="header-card">
      <h2>健康数据</h2>
      <p>记录和管理日常健康指标</p>
    </el-card>

    <el-tabs v-model="activeTab" type="border-card">
      <!-- 数据录入 -->
      <el-tab-pane label="📝 数据录入" name="input">
        <el-card>
          <template #header>添加健康记录</template>
          <el-form :model="newRecord" label-width="100px">
            <el-form-item label="数据类型">
              <el-select v-model="newRecord.type" placeholder="选择数据类型">
                <el-option label="血糖" value="blood_sugar" />
                <el-option label="血压" value="blood_pressure" />
                <el-option label="心率" value="heart_rate" />
                <el-option label="体重" value="weight" />
                <el-option label="体温" value="temperature" />
                <el-option label="血氧" value="blood_oxygen" />
              </el-select>
            </el-form-item>
            
            <el-form-item v-if="newRecord.type === 'blood_pressure'" label="血压值">
              <el-input-number v-model="newRecord.systolic" :min="60" :max="200" placeholder="收缩压" style="width: 120px" />
              <span style="margin: 0 10px">/</span>
              <el-input-number v-model="newRecord.diastolic" :min="40" :max="120" placeholder="舒张压" style="width: 120px" />
              <span style="margin-left: 10px">mmHg</span>
            </el-form-item>
            
            <el-form-item v-else label="数值">
              <el-input-number v-model="newRecord.value" :min="0" :max="500" :step="0.1" />
              <span style="margin-left: 10px">{{ newRecord.unit }}</span>
            </el-form-item>
            
            <el-form-item label="测量时间">
              <el-date-picker
                v-model="newRecord.recorded_at"
                type="datetime"
                placeholder="选择时间"
                format="YYYY-MM-DD HH:mm"
              />
            </el-form-item>
            
            <el-form-item label="备注">
              <el-input v-model="newRecord.notes" type="textarea" :rows="2" placeholder="可选备注" />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="addRecord">保存记录</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 数据趋势 -->
      <el-tab-pane label="📈 数据趋势" name="trends">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>健康趋势</span>
              <el-select v-model="trendType" @change="loadTrends" style="width: 150px">
                <el-option label="血糖" value="blood_sugar" />
                <el-option label="血压" value="blood_pressure" />
                <el-option label="心率" value="heart_rate" />
                <el-option label="体重" value="weight" />
              </el-select>
            </div>
          </template>
          
          <div v-if="trendData.data?.length > 0" class="trend-chart">
            <el-row :gutter="20">
              <el-col :span="6">
                <el-statistic title="平均值" :value="trendData.avg" />
              </el-col>
              <el-col :span="6">
                <el-statistic title="最低值" :value="trendData.min" />
              </el-col>
              <el-col :span="6">
                <el-statistic title="最高值" :value="trendData.max" />
              </el-col>
              <el-col :span="6">
                <el-statistic title="趋势">
                  <template #default>
                    <span :class="getTrendClass(trendData.trend)">{{ getTrendLabel(trendData.trend) }}</span>
                  </template>
                </el-statistic>
              </el-col>
            </el-row>
            
            <div class="chart-placeholder">
              <el-table :data="trendData.data" style="width: 100%; margin-top: 20px">
                <el-table-column prop="date" label="日期" />
                <el-table-column prop="value" label="数值" />
              </el-table>
            </div>
          </div>
          
          <el-empty v-else description="暂无趋势数据" />
        </el-card>
      </el-tab-pane>

      <!-- 健康预警 -->
      <el-tab-pane label="⚠️ 健康预警" name="alerts">
        <el-card>
          <template #header>
            <span>异常提醒</span>
          </template>
          
          <div v-if="alerts.length > 0">
            <el-alert
              v-for="alert in alerts"
              :key="alert.id"
              :title="alert.title"
              :description="alert.content"
              :type="getAlertType(alert.severity)"
              show-icon
              class="alert-item"
            >
              <template #default>
                <span class="alert-time">{{ formatDate(alert.created_at) }}</span>
              </template>
            </el-alert>
          </div>
          
          <el-empty v-else description="暂无预警" />
        </el-card>
      </el-tab-pane>

      <!-- 历史记录 -->
      <el-tab-pane label="📋 历史记录" name="history">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>所有记录</span>
              <el-select v-model="filterType" placeholder="筛选类型" clearable style="width: 150px">
                <el-option label="血糖" value="blood_sugar" />
                <el-option label="血压" value="blood_pressure" />
                <el-option label="心率" value="heart_rate" />
                <el-option label="体重" value="weight" />
                <el-option label="体温" value="temperature" />
                <el-option label="血氧" value="blood_oxygen" />
              </el-select>
            </div>
          </template>
          
          <el-table :data="filteredRecords" style="width: 100%">
            <el-table-column prop="recorded_at" label="时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.recorded_at) }}
              </template>
            </el-table-column>
            <el-table-column prop="type" label="类型" width="120">
              <template #default="{ row }">
                <el-tag>{{ getTypeLabel(row.type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="value" label="数值" width="150">
              <template #default="{ row }">
                {{ formatValue(row) }} {{ row.unit }}
              </template>
            </el-table-column>
            <el-table-column prop="notes" label="备注" />
          </el-table>
          
          <el-empty v-if="filteredRecords.length === 0" description="暂无记录" />
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const patientId = ref('patient_001')

const activeTab = ref('input')
const trendType = ref('blood_sugar')
const filterType = ref('')

const newRecord = ref({
  type: 'blood_sugar',
  value: 6.5,
  systolic: 120,
  diastolic: 80,
  unit: 'mmol/L',
  recorded_at: new Date(),
  notes: ''
})

const records = ref([])
const trendData = ref({})
const alerts = ref([])

const typeUnits = {
  blood_sugar: { unit: 'mmol/L', label: '血糖' },
  blood_pressure: { unit: 'mmHg', label: '血压' },
  heart_rate: { unit: 'bpm', label: '心率' },
  weight: { unit: 'kg', label: '体重' },
  temperature: { unit: '°C', label: '体温' },
  blood_oxygen: { unit: '%', label: '血氧' }
}

const filteredRecords = computed(() => {
  if (!filterType.value) return records.value
  return records.value.filter(r => r.type === filterType.value)
})

const updateUnit = () => {
  if (newRecord.value.type !== 'blood_pressure') {
    newRecord.value.unit = typeUnits[newRecord.value.type]?.unit || ''
  }
}

const addRecord = async () => {
  try {
    let recordData = {
      patient_id: patientId.value,
      type: newRecord.value.type,
      recorded_at: newRecord.value.recorded_at,
      notes: newRecord.value.notes
    }
    
    if (newRecord.value.type === 'blood_pressure') {
      recordData.type = 'blood_pressure'
      recordData.value = `${newRecord.value.systolic}/${newRecord.value.diastolic}`
      recordData.unit = 'mmHg'
    } else {
      recordData.value = newRecord.value.value
      recordData.unit = newRecord.value.unit
    }
    
    const res = await axios.post('/api/v1/health/record/add', recordData)
    if (res.data.success) {
      ElMessage.success('记录保存成功')
      await loadRecords()
    }
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

const loadRecords = async () => {
  try {
    const res = await axios.get(`/api/v1/health/records/${patientId.value}`)
    if (res.data.success) {
      records.value = res.data.records
    }
  } catch (e) {
    console.error('加载记录失败', e)
  }
}

const loadTrends = async () => {
  try {
    const res = await axios.get(`/api/v1/health/trends/${patientId.value}`, {
      params: { type: trendType.value }
    })
    if (res.data.success) {
      trendData.value = res.data.trend
    }
  } catch (e) {
    console.error('加载趋势失败', e)
  }
}

const loadAlerts = async () => {
  try {
    const res = await axios.get(`/api/v1/health/alerts/${patientId.value}`)
    if (res.data.success) {
      alerts.value = res.data.alerts
    }
  } catch (e) {
    console.error('加载预警失败', e)
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

const getTypeLabel = (type) => {
  return typeUnits[type]?.label || type
}

const formatValue = (row) => {
  if (row.type === 'blood_pressure') {
    return row.value
  }
  return row.value
}

const getTrendClass = (trend) => {
  if (trend === 'falling') return 'trend-good'
  if (trend === 'rising') return 'trend-bad'
  return 'trend-normal'
}

const getTrendLabel = (trend) => {
  const labels = { falling: '↓ 下降', rising: '↑ 上升', stable: '→ 稳定' }
  return labels[trend] || trend
}

const getAlertType = (severity) => {
  const types = { low: 'info', medium: 'warning', high: 'error', urgent: 'error' }
  return types[severity] || 'info'
}

onMounted(() => {
  updateUnit()
  loadRecords()
  loadTrends()
  loadAlerts()
})
</script>

<style scoped>
.health-data-container {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
  text-align: center;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.alert-item {
  margin-bottom: 10px;
}

.alert-time {
  font-size: 12px;
  color: #999;
}

.trend-good {
  color: #67C23A;
}

.trend-bad {
  color: #CD8B5B;
}

.trend-normal {
  color: var(--color-primary);
}

.chart-placeholder {
  margin-top: 20px;
}
</style>
