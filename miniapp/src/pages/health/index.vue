<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import api from '@/utils/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

type HealthType = 'blood_sugar' | 'blood_pressure' | 'weight'

const tabs = [
  { key: 'blood_sugar' as HealthType, label: '血糖' },
  { key: 'blood_pressure' as HealthType, label: '血压' },
  { key: 'weight' as HealthType, label: '体重' },
]

const activeTab = ref<HealthType>('blood_sugar')
const records = ref<any[]>([])
const trend = ref<any>(null)
const loading = ref(false)
const showAddDialog = ref(false)

const addForm = ref({
  value1: '',
  value2: '',
  measureTime: '',
  note: '',
})

const tabLabel = computed(() => tabs.find(t => t.key === activeTab.value)?.label || '')

const unitMap: Record<HealthType, string> = {
  blood_sugar: 'mmol/L',
  blood_pressure: 'mmHg',
  weight: 'kg',
}

const currentUnit = computed(() => unitMap[activeTab.value])

const latestRecord = computed(() => {
  if (!records.value.length) return null
  return records.value[0]
})

const latestDisplay = computed(() => {
  if (!latestRecord.value) return '--'
  if (activeTab.value === 'blood_pressure') {
    return `${latestRecord.value.systolic || latestRecord.value.value1 || '--'}/${latestRecord.value.diastolic || latestRecord.value.value2 || '--'}`
  }
  return latestRecord.value.value || latestRecord.value.value1 || '--'
})

const trendDirection = computed(() => {
  if (!trend.value) return ''
  const dir = trend.value.direction || trend.value.trend || ''
  return dir
})

const trendIcon = computed(() => {
  const d = trendDirection.value
  if (d === 'up' || d === 'rising') return '↑'
  if (d === 'down' || d === 'falling') return '↓'
  return '→'
})

const trendColor = computed(() => {
  const d = trendDirection.value
  if (d === 'up' || d === 'rising') return 'var(--color-danger)'
  if (d === 'down' || d === 'falling') return 'var(--color-success)'
  return 'var(--color-text-hint)'
})

function switchTab(key: HealthType) {
  activeTab.value = key
  loadData()
}

async function loadData() {
  const patientId = auth.userInfo?.id || auth.userInfo?.patient_id || ''
  if (!patientId) return
  loading.value = true
  try {
    const [recordsRes, trendRes] = await Promise.all([
      api.get(`/health/records/${patientId}`, { type: activeTab.value, days: 30 }),
      api.get(`/health/trends/${patientId}`, { type: activeTab.value }),
    ])
    records.value = Array.isArray(recordsRes) ? recordsRes : (recordsRes as any)?.records || []
    trend.value = trendRes
  } catch (e) {
    console.error(e)
    uni.showToast({ title: '加载数据失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function openAddDialog() {
  addForm.value = { value1: '', value2: '', measureTime: '', note: '' }
  showAddDialog.value = true
}

function closeAddDialog() {
  showAddDialog.value = false
}

async function submitRecord() {
  const patientId = auth.userInfo?.id || auth.userInfo?.patient_id || ''
  if (!patientId) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    return
  }
  if (!addForm.value.value1) {
    uni.showToast({ title: '请输入数值', icon: 'none' })
    return
  }

  const data: any = {
    patientId,
    type: activeTab.value,
    value: Number(addForm.value.value1),
    measureTime: addForm.value.measureTime || new Date().toISOString(),
    note: addForm.value.note,
  }

  if (activeTab.value === 'blood_pressure') {
    data.systolic = Number(addForm.value.value1)
    data.diastolic = Number(addForm.value.value2)
    data.value = Number(addForm.value.value1)
  }

  try {
    await api.post('/health/record/add', data)
    uni.showToast({ title: '记录成功', icon: 'success' })
    closeAddDialog()
    loadData()
  } catch (e) {
    console.error(e)
    uni.showToast({ title: '记录失败', icon: 'none' })
  }
}

function formatTime(timeStr: string) {
  if (!timeStr) return ''
  const d = new Date(timeStr)
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${m}-${day} ${h}:${min}`
}

onMounted(() => {
  loadData()
})

onShow(() => {
  loadData()
})
</script>

<template>
  <view class="page">
    <view class="tab-bar">
      <view
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab-item', { active: activeTab === tab.key }]"
        @tap="switchTab(tab.key)"
      >
        {{ tab.label }}
      </view>
    </view>

    <view class="card current-card">
      <view class="current-header">
        <text class="current-label">当前{{ tabLabel }}</text>
        <view v-if="trendDirection" class="trend-badge" :style="{ color: trendColor }">
          <text class="trend-icon">{{ trendIcon }}</text>
          <text class="trend-text">{{ trendDirection === 'up' || trendDirection === 'rising' ? '上升' : trendDirection === 'down' || trendDirection === 'falling' ? '下降' : '平稳' }}</text>
        </view>
      </view>
      <view class="current-value-row">
        <text class="current-value">{{ latestDisplay }}</text>
        <text class="current-unit">{{ currentUnit }}</text>
      </view>
      <text v-if="latestRecord?.measureTime" class="current-time">
        {{ formatTime(latestRecord.measureTime || latestRecord.measuredAt || latestRecord.createdAt) }}
      </text>
    </view>

    <view class="add-btn-wrap">
      <view class="btn-primary add-btn" @tap="openAddDialog">
        <text class="add-icon">+</text>
        <text>添加记录</text>
      </view>
    </view>

    <view class="section-title">近期记录</view>

    <view v-if="loading" class="loading-state">
      <text class="text-hint">加载中...</text>
    </view>

    <view v-else-if="!records.length" class="empty-state">
      <text class="empty-icon">📋</text>
      <text class="empty-text">暂无{{ tabLabel }}记录</text>
    </view>

    <view v-else class="record-list">
      <view v-for="(item, idx) in records" :key="idx" class="card record-item">
        <view class="flex-between">
          <view class="record-value-wrap">
            <text class="record-value">
              {{ activeTab === 'blood_pressure'
                ? `${item.systolic || item.value1 || '--'}/${item.diastolic || item.value2 || '--'}`
                : (item.value || item.value1 || '--') }}
            </text>
            <text class="record-unit">{{ currentUnit }}</text>
          </view>
          <text class="record-time text-hint">{{ formatTime(item.measureTime || item.measuredAt || item.createdAt) }}</text>
        </view>
        <text v-if="item.note" class="record-note text-secondary">{{ item.note }}</text>
      </view>
    </view>

    <view v-if="showAddDialog" class="dialog-mask" @tap="closeAddDialog">
      <view class="dialog-content" @tap.stop>
        <view class="dialog-title">添加{{ tabLabel }}记录</view>

        <view class="form-group">
          <text class="form-label">{{ activeTab === 'blood_pressure' ? '收缩压' : tabLabel }}</text>
          <input
            v-model="addForm.value1"
            class="input-field"
            type="digit"
            :placeholder="activeTab === 'blood_pressure' ? '请输入收缩压' : `请输入${tabLabel}值`"
          />
        </view>

        <view v-if="activeTab === 'blood_pressure'" class="form-group">
          <text class="form-label">舒张压</text>
          <input
            v-model="addForm.value2"
            class="input-field"
            type="digit"
            placeholder="请输入舒张压"
          />
        </view>

        <view class="form-group">
          <text class="form-label">测量时间</text>
          <input
            v-model="addForm.measureTime"
            class="input-field"
            placeholder="留空则使用当前时间"
          />
        </view>

        <view class="form-group">
          <text class="form-label">备注</text>
          <input
            v-model="addForm.note"
            class="input-field"
            placeholder="可选备注"
          />
        </view>

        <view class="dialog-actions">
          <view class="btn-secondary dialog-btn" @tap="closeAddDialog">取消</view>
          <view class="btn-primary dialog-btn" @tap="submitRecord">确认</view>
        </view>
      </view>
    </view>
  </view>
</template>

<style scoped>
.tab-bar {
  display: flex;
  background: var(--color-bg-card);
  border-radius: var(--radius-md);
  padding: 6rpx;
  margin-bottom: var(--spacing-md);
}

.tab-item {
  flex: 1;
  text-align: center;
  padding: 18rpx 0;
  font-size: 28rpx;
  color: var(--color-text-secondary);
  border-radius: var(--radius-sm);
  transition: all 0.2s;
}

.tab-item.active {
  background: var(--color-primary);
  color: #fff;
  font-weight: 600;
}

.current-card {
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
  color: #fff;
}

.current-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-sm);
}

.current-label {
  font-size: 28rpx;
  opacity: 0.9;
}

.trend-badge {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.2);
  padding: 6rpx 16rpx;
  border-radius: 20rpx;
  font-size: 24rpx;
}

.trend-icon {
  margin-right: 6rpx;
  font-weight: 700;
}

.current-value-row {
  display: flex;
  align-items: baseline;
  margin-bottom: 8rpx;
}

.current-value {
  font-size: 72rpx;
  font-weight: 700;
  line-height: 1.1;
}

.current-unit {
  font-size: 28rpx;
  margin-left: 12rpx;
  opacity: 0.8;
}

.current-time {
  font-size: 24rpx;
  opacity: 0.7;
}

.add-btn-wrap {
  margin-bottom: var(--spacing-md);
}

.add-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 24rpx 0;
}

.add-icon {
  font-size: 36rpx;
  margin-right: 10rpx;
  font-weight: 700;
}

.loading-state {
  display: flex;
  justify-content: center;
  padding: 80rpx 0;
}

.record-list {
  display: flex;
  flex-direction: column;
}

.record-item {
  padding: var(--spacing-sm) var(--spacing-md);
}

.record-value-wrap {
  display: flex;
  align-items: baseline;
}

.record-value {
  font-size: 36rpx;
  font-weight: 600;
  color: var(--color-text-primary);
}

.record-unit {
  font-size: 22rpx;
  color: var(--color-text-hint);
  margin-left: 8rpx;
}

.record-time {
  font-size: 24rpx;
}

.record-note {
  font-size: 24rpx;
  margin-top: 8rpx;
}

.dialog-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

.dialog-content {
  width: 600rpx;
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.dialog-title {
  font-size: 34rpx;
  font-weight: 600;
  color: var(--color-text-primary);
  text-align: center;
  margin-bottom: var(--spacing-md);
}

.form-group {
  margin-bottom: var(--spacing-sm);
}

.form-label {
  font-size: 26rpx;
  color: var(--color-text-secondary);
  margin-bottom: 8rpx;
  display: block;
}

.dialog-actions {
  display: flex;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-md);
}

.dialog-btn {
  flex: 1;
  padding: 22rpx 0;
}
</style>
