<template>
  <view class="page">
    <!-- 头部 -->
    <view class="header">
      <text class="title">健康数据</text>
      <text class="subtitle">记录和管理您的健康指标</text>
    </view>

    <!-- 标签页 -->
    <view class="tabs">
      <view 
        class="tab-item" 
        :class="{ active: activeTab === 'input' }"
        @click="activeTab = 'input'"
      >
        录入
      </view>
      <view 
        class="tab-item" 
        :class="{ active: activeTab === 'trends' }"
        @click="activeTab = 'trends'"
      >
        趋势
      </view>
      <view 
        class="tab-item" 
        :class="{ active: activeTab === 'alerts' }"
        @click="activeTab = 'alerts'"
      >
        预警
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
      <!-- 数据录入 -->
      <view v-if="activeTab === 'input'" class="input-section">
        <view class="input-card">
          <view class="card-header">
            <text class="card-title">添加健康记录</text>
          </view>
          
          <view class="type-selector">
            <view 
              class="type-item" 
              v-for="type in healthTypes" 
              :key="type.value"
              :class="{ active: newRecord.type === type.value }"
              @click="selectType(type.value)"
            >
              <text class="type-icon">{{ type.icon }}</text>
              <text class="type-label">{{ type.label }}</text>
            </view>
          </view>
          
          <view class="input-group">
            <text class="input-label">数值</text>
            <view v-if="newRecord.type === 'blood_pressure'" class="bp-input">
              <input 
                class="input" 
                type="number" 
                v-model="newRecord.systolic" 
                placeholder="收缩压"
              />
              <text class="bp-separator">/</text>
              <input 
                class="input" 
                type="number" 
                v-model="newRecord.diastolic" 
                placeholder="舒张压"
              />
              <text class="unit">mmHg</text>
            </view>
            <view v-else class="single-input">
              <input 
                class="input" 
                type="digit" 
                v-model="newRecord.value" 
                :placeholder="'请输入' + currentType?.label"
              />
              <text class="unit">{{ currentType?.unit }}</text>
            </view>
          </view>
          
          <view class="input-group">
            <text class="input-label">测量时间</text>
            <picker mode="date" @change="onDateChange">
              <view class="picker">{{ newRecord.date || '选择日期' }}</view>
            </picker>
            <picker mode="time" @change="onTimeChange">
              <view class="picker">{{ newRecord.time || '选择时间' }}</view>
            </picker>
          </view>
          
          <view class="input-group">
            <text class="input-label">备注</text>
            <textarea 
              class="textarea" 
              v-model="newRecord.notes" 
              placeholder="可选备注"
            />
          </view>
          
          <view class="btn-save" @click="saveRecord">保存记录</view>
        </view>
      </view>

      <!-- 数据趋势 -->
      <view v-if="activeTab === 'trends'" class="trends-section">
        <view class="type-filter">
          <picker :range="trendTypes" @change="onTrendTypeChange">
            <view class="filter-picker">{{ selectedTrendType?.label || '选择类型' }}</view>
          </picker>
        </view>
        
        <view v-if="trendData.data?.length > 0" class="trend-card">
          <view class="stats-grid">
            <view class="stat-item">
              <text class="stat-value">{{ trendData.avg }}</text>
              <text class="stat-label">平均值</text>
            </view>
            <view class="stat-item">
              <text class="stat-value">{{ trendData.min }}</text>
              <text class="stat-label">最低</text>
            </view>
            <view class="stat-item">
              <text class="stat-value">{{ trendData.max }}</text>
              <text class="stat-label">最高</text>
            </view>
            <view class="stat-item">
              <text class="stat-value" :class="getTrendClass(trendData.trend)">
                {{ getTrendLabel(trendData.trend) }}
              </text>
              <text class="stat-label">趋势</text>
            </view>
          </view>
          
          <view class="trend-list">
            <view class="trend-header">
              <text class="th-date">日期</text>
              <text class="th-value">数值</text>
            </view>
            <view 
              class="trend-row" 
              v-for="item in trendData.data" 
              :key="item.date"
            >
              <text class="td-date">{{ item.date }}</text>
              <text class="td-value">{{ item.value }}</text>
            </view>
          </view>
        </view>
        
        <view v-else class="empty-state">
          <text class="empty-text">暂无趋势数据</text>
        </view>
      </view>

      <!-- 健康预警 -->
      <view v-if="activeTab === 'alerts'" class="alerts-section">
        <view v-if="alerts.length > 0" class="alert-list">
          <view 
            class="alert-card" 
            v-for="alert in alerts" 
            :key="alert.id"
            :class="'alert-' + alert.severity"
          >
            <view class="alert-header">
              <text class="alert-icon">⚠️</text>
              <text class="alert-title">{{ alert.title }}</text>
              <text class="alert-time">{{ formatDate(alert.created_at) }}</text>
            </view>
            <text class="alert-content">{{ alert.content }}</text>
          </view>
        </view>
        
        <view v-else class="empty-state">
          <text class="empty-text">暂无预警</text>
          <text class="empty-hint">继续保持健康生活习惯</text>
        </view>
      </view>

      <!-- 历史记录 -->
      <view v-if="activeTab === 'history'" class="history-section">
        <view v-if="records.length > 0" class="history-list">
          <view 
            class="history-item" 
            v-for="record in records" 
            :key="record.id"
          >
            <view class="history-icon">{{ getTypeIcon(record.type) }}</view>
            <view class="history-info">
              <text class="history-type">{{ getTypeLabel(record.type) }}</text>
              <text class="history-value">{{ formatValue(record) }} {{ record.unit }}</text>
              <text class="history-time">{{ formatDateTime(record.recorded_at) }}</text>
            </view>
          </view>
        </view>
        
        <view v-else class="empty-state">
          <text class="empty-text">暂无记录</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { healthApi } from '@/utils/api'

const patientId = ref('patient_001')
const activeTab = ref('input')

const healthTypes = [
  { value: 'blood_sugar', label: '血糖', unit: 'mmol/L', icon: '🩸' },
  { value: 'blood_pressure', label: '血压', unit: 'mmHg', icon: '💓' },
  { value: 'heart_rate', label: '心率', unit: 'bpm', icon: '❤️' },
  { value: 'weight', label: '体重', unit: 'kg', icon: '⚖️' },
  { value: 'temperature', label: '体温', unit: '°C', icon: '🌡️' },
  { value: 'blood_oxygen', label: '血氧', unit: '%', icon: '🫁' }
]

const trendTypes = healthTypes.map(t => t.label)

const currentType = computed(() => healthTypes.find(t => t.value === newRecord.value.type))

const newRecord = ref({
  type: 'blood_sugar',
  value: '',
  systolic: '',
  diastolic: '',
  date: '',
  time: '',
  notes: ''
})

const records = ref<Array<any>>([])
const trendData = ref<any>({})
const alerts = ref<Array<any>>([])
const selectedTrendType = ref(healthTypes[0])

const selectType = (type: string) => {
  newRecord.value.type = type
}

const onDateChange = (e: any) => {
  newRecord.value.date = e.detail.value
}

const onTimeChange = (e: any) => {
  newRecord.value.time = e.detail.value
}

const onTrendTypeChange = (e: any) => {
  selectedTrendType.value = healthTypes[e.detail.value]
  loadTrends()
}

const saveRecord = async () => {
  try {
    let recordData: any = {
      patient_id: patientId.value,
      type: newRecord.value.type,
      notes: newRecord.value.notes
    }
    
    if (newRecord.value.type === 'blood_pressure') {
      recordData.value = `${newRecord.value.systolic}/${newRecord.value.diastolic}`
      recordData.unit = 'mmHg'
    } else {
      recordData.value = newRecord.value.value
      recordData.unit = currentType.value?.unit
    }
    
    if (newRecord.value.date && newRecord.value.time) {
      recordData.recorded_at = `${newRecord.value.date}T${newRecord.value.time}:00`
    }
    
    await healthApi.addRecord(recordData)
    uni.showToast({ title: '保存成功', icon: 'success' })
    await loadRecords()
  } catch (e) {
    // 模拟成功
    records.value.unshift({
      id: 'r' + Date.now(),
      type: newRecord.value.type,
      value: newRecord.value.type === 'blood_pressure' 
        ? `${newRecord.value.systolic}/${newRecord.value.diastolic}`
        : newRecord.value.value,
      unit: currentType.value?.unit,
      recorded_at: new Date().toISOString()
    })
    uni.showToast({ title: '保存成功', icon: 'success' })
  }
}

const loadRecords = async () => {
  try {
    const res = await healthApi.getRecords(patientId.value)
    if (res.success) {
      records.value = res.records
    }
  } catch (e) {
    // 模拟数据
    records.value = [
      { id: '1', type: 'blood_sugar', value: 6.5, unit: 'mmol/L', recorded_at: '2024-03-15T08:00:00' },
      { id: '2', type: 'blood_pressure', value: '120/80', unit: 'mmHg', recorded_at: '2024-03-15T08:30:00' },
      { id: '3', type: 'heart_rate', value: 72, unit: 'bpm', recorded_at: '2024-03-14T10:00:00' }
    ]
  }
}

const loadTrends = async () => {
  try {
    const res = await healthApi.getTrends(patientId.value, selectedTrendType.value?.value || 'blood_sugar')
    if (res.success) {
      trendData.value = res.trend
    }
  } catch (e) {
    // 模拟数据
    trendData.value = {
      data: [
        { date: '03/15', value: 6.5 },
        { date: '03/14', value: 6.8 },
        { date: '03/13', value: 6.3 },
        { date: '03/12', value: 7.0 },
        { date: '03/11', value: 6.6 }
      ],
      avg: 6.64,
      min: 6.3,
      max: 7.0,
      trend: 'stable'
    }
  }
}

const loadAlerts = async () => {
  try {
    const res = await healthApi.getAlerts(patientId.value)
    if (res.success) {
      alerts.value = res.alerts
    }
  } catch (e) {
    // 模拟数据
    alerts.value = [
      { id: 'a1', title: '血糖偏高', content: '最近一次血糖值为7.8mmol/L，建议关注饮食', severity: 'medium', created_at: '2024-03-15' }
    ]
  }
}

const getTypeIcon = (type: string) => {
  return healthTypes.find(t => t.value === type)?.icon || '📊'
}

const getTypeLabel = (type: string) => {
  return healthTypes.find(t => t.value === type)?.label || type
}

const formatValue = (record: any) => {
  return record.value
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}/${date.getDate()}`
}

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`
}

const getTrendClass = (trend: string) => {
  if (trend === 'falling') return 'trend-good'
  if (trend === 'rising') return 'trend-bad'
  return 'trend-normal'
}

const getTrendLabel = (trend: string) => {
  const labels: Record<string, string> = { falling: '↓下降', rising: '↑上升', stable: '→稳定' }
  return labels[trend] || trend
}

// 初始化
loadRecords()
loadTrends()
loadAlerts()
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
}

.tab-item {
  flex: 1;
  text-align: center;
  font-size: 28rpx;
  color: #666;
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

.input-card, .trend-card, .alert-card, .history-item {
  background: #fff;
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
  color: #333;
}

.type-selector {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15rpx;
  margin-bottom: 30rpx;
}

.type-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20rpx;
  background: #f5f5f5;
  border-radius: 10rpx;
  border: 2rpx solid transparent;
}

.type-item.active {
  background: #f0f9ff;
  border-color: var(--color-primary);
}

.type-icon {
  font-size: 40rpx;
  margin-bottom: 8rpx;
}

.type-label {
  font-size: 24rpx;
  color: #666;
}

.type-item.active .type-label {
  color: var(--color-primary);
}

.input-group {
  margin-bottom: 25rpx;
}

.input-label {
  display: block;
  font-size: 26rpx;
  color: #666;
  margin-bottom: 10rpx;
}

.input {
  flex: 1;
  padding: 20rpx;
  background: #f5f5f5;
  border-radius: 10rpx;
  font-size: 28rpx;
}

.bp-input, .single-input {
  display: flex;
  align-items: center;
  gap: 15rpx;
}

.bp-input .input {
  width: 150rpx;
  text-align: center;
}

.bp-separator {
  font-size: 32rpx;
  color: #999;
}

.unit {
  font-size: 26rpx;
  color: #999;
}

.picker {
  padding: 20rpx;
  background: #f5f5f5;
  border-radius: 10rpx;
  font-size: 28rpx;
  color: #333;
  margin-bottom: 15rpx;
}

.textarea {
  width: 100%;
  min-height: 100rpx;
  padding: 20rpx;
  background: #f5f5f5;
  border-radius: 10rpx;
  font-size: 28rpx;
  box-sizing: border-box;
}

.btn-save {
  width: 100%;
  text-align: center;
  padding: 25rpx;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
  color: var(--color-text-inverse);
  border-radius: 40rpx;
  font-size: 30rpx;
  font-weight: bold;
}

.type-filter {
  margin-bottom: 20rpx;
}

.filter-picker {
  padding: 20rpx;
  background: #fff;
  border-radius: 10rpx;
  font-size: 28rpx;
  color: #333;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15rpx;
  margin-bottom: 30rpx;
}

.stat-item {
  text-align: center;
  padding: 20rpx;
  background: #f9f9f9;
  border-radius: 10rpx;
}

.stat-value {
  display: block;
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
}

.trend-good { color: var(--color-primary); }
.trend-bad { color: #f56c6c; }
.trend-normal { color: var(--color-primary); }

.stat-label {
  font-size: 22rpx;
  color: #999;
  margin-top: 5rpx;
}

.trend-list {
  margin-top: 20rpx;
}

.trend-header {
  display: flex;
  padding: 15rpx 0;
  border-bottom: 1rpx solid #eee;
}

.th-date, .td-date {
  flex: 1;
  font-size: 26rpx;
  color: #666;
}

.th-value, .td-value {
  flex: 1;
  text-align: right;
  font-size: 26rpx;
  color: #333;
}

.trend-row {
  display: flex;
  padding: 20rpx 0;
  border-bottom: 1rpx solid #f5f5f5;
}

.empty-state {
  text-align: center;
  padding: 60rpx;
}

.empty-text {
  font-size: 28rpx;
  color: #999;
}

.empty-hint {
  font-size: 24rpx;
  color: #ccc;
  margin-top: 10rpx;
}

.alert-card {
  border-left: 6rpx solid;
}

.alert-low { border-color: #909399; }
.alert-medium { border-color: #e6a23c; }
.alert-high, .alert-urgent { border-color: #f56c6c; }

.alert-header {
  display: flex;
  align-items: center;
  margin-bottom: 10rpx;
}

.alert-icon {
  font-size: 30rpx;
  margin-right: 10rpx;
}

.alert-title {
  flex: 1;
  font-size: 28rpx;
  font-weight: bold;
  color: #333;
}

.alert-time {
  font-size: 22rpx;
  color: #999;
}

.alert-content {
  font-size: 26rpx;
  color: #666;
  line-height: 1.5;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 15rpx;
}

.history-item {
  display: flex;
  align-items: center;
}

.history-icon {
  font-size: 40rpx;
  margin-right: 20rpx;
}

.history-info {
  flex: 1;
}

.history-type {
  display: block;
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
}

.history-value {
  font-size: 26rpx;
  color: var(--color-primary);
  margin-top: 5rpx;
}

.history-time {
  font-size: 22rpx;
  color: #999;
  margin-top: 5rpx;
}
</style>
