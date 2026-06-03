<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import api from '@/utils/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

type MedStatus = 'taken' | 'missed' | 'pending'

interface MedicationReminder {
  id: string | number
  name: string
  dosage: string
  time: string
  status: MedStatus
  frequency?: string
  notes?: string
}

const reminders = ref<MedicationReminder[]>([])
const loading = ref(false)
const showAddDialog = ref(false)
const addForm = ref({
  name: '',
  dosage: '',
  time: '',
  frequency: 'daily',
  notes: '',
})

const todayStr = computed(() => {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}年${m}月${day}日`
})

const takenCount = computed(() => reminders.value.filter(r => r.status === 'taken').length)
const totalCount = computed(() => reminders.value.length)
const progressPercent = computed(() => {
  if (!totalCount.value) return 0
  return Math.round((takenCount.value / totalCount.value) * 100)
})

const statusMap: Record<MedStatus, { label: string; tagClass: string }> = {
  taken: { label: '已服用', tagClass: 'tag-success' },
  missed: { label: '已错过', tagClass: 'tag-danger' },
  pending: { label: '待服用', tagClass: 'tag-warning' },
}

function getStatusInfo(status: MedStatus) {
  return statusMap[status] || statusMap.pending
}

async function loadReminders() {
  loading.value = true
  try {
    const res = await api.get('/medication-enhanced/reminders')
    reminders.value = Array.isArray(res) ? res : (res as any)?.reminders || (res as any)?.data || []
  } catch (e) {
    console.error(e)
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

async function markTaken(item: MedicationReminder) {
  try {
    await api.post('/medication-enhanced/record', {
      reminderId: item.id,
      status: 'taken',
      takenAt: new Date().toISOString(),
    })
    item.status = 'taken'
    uni.showToast({ title: '已标记为服用', icon: 'success' })
  } catch (e) {
    console.error(e)
    uni.showToast({ title: '操作失败', icon: 'none' })
  }
}

function openAddDialog() {
  addForm.value = { name: '', dosage: '', time: '', frequency: 'daily', notes: '' }
  showAddDialog.value = true
}

function closeAddDialog() {
  showAddDialog.value = false
}

async function submitReminder() {
  if (!addForm.value.name) {
    uni.showToast({ title: '请输入药品名称', icon: 'none' })
    return
  }
  if (!addForm.value.time) {
    uni.showToast({ title: '请选择提醒时间', icon: 'none' })
    return
  }
  try {
    await api.post('/medication-enhanced/reminders', {
      name: addForm.value.name,
      dosage: addForm.value.dosage,
      time: addForm.value.time,
      frequency: addForm.value.frequency,
      notes: addForm.value.notes,
    })
    uni.showToast({ title: '添加成功', icon: 'success' })
    closeAddDialog()
    loadReminders()
  } catch (e) {
    console.error(e)
    uni.showToast({ title: '添加失败', icon: 'none' })
  }
}

function formatTime(timeStr: string) {
  if (!timeStr) return ''
  if (timeStr.includes(':') && timeStr.length <= 5) return timeStr
  const d = new Date(timeStr)
  const h = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${h}:${min}`
}

onMounted(() => {
  loadReminders()
})

onShow(() => {
  loadReminders()
})
</script>

<template>
  <view class="page">
    <view class="card summary-card">
      <view class="summary-date">{{ todayStr }}</view>
      <view class="summary-progress-wrap">
        <view class="progress-bar-bg">
          <view class="progress-bar-fill" :style="{ width: progressPercent + '%' }" />
        </view>
        <text class="progress-text">{{ takenCount }}/{{ totalCount }} 已服用</text>
      </view>
    </view>

    <view class="flex-between" style="margin-bottom: var(--spacing-sm);">
      <text class="section-title" style="margin-bottom: 0;">今日用药</text>
      <view class="btn-text" @tap="openAddDialog">+ 添加提醒</view>
    </view>

    <view v-if="loading" class="loading-state">
      <text class="text-hint">加载中...</text>
    </view>

    <view v-else-if="!reminders.length" class="empty-state">
      <text class="empty-icon">💊</text>
      <text class="empty-text">暂无用药提醒</text>
    </view>

    <view v-else class="med-list">
      <view v-for="item in reminders" :key="item.id" class="card med-item">
        <view class="flex-between">
          <view class="med-info">
            <view class="med-name-row">
              <text class="med-name">{{ item.name }}</text>
              <text :class="['tag', getStatusInfo(item.status).tagClass]">
                {{ getStatusInfo(item.status).label }}
              </text>
            </view>
            <text class="med-dosage text-secondary">{{ item.dosage }}</text>
          </view>
          <view class="med-right">
            <text class="med-time">{{ formatTime(item.time) }}</text>
            <view
              v-if="item.status === 'pending'"
              class="btn-primary take-btn"
              @tap="markTaken(item)"
            >
              服用
            </view>
          </view>
        </view>
        <text v-if="item.notes" class="med-notes text-hint">{{ item.notes }}</text>
      </view>
    </view>

    <view v-if="showAddDialog" class="dialog-mask" @tap="closeAddDialog">
      <view class="dialog-content" @tap.stop>
        <view class="dialog-title">添加用药提醒</view>

        <view class="form-group">
          <text class="form-label">药品名称</text>
          <input v-model="addForm.name" class="input-field" placeholder="请输入药品名称" />
        </view>

        <view class="form-group">
          <text class="form-label">剂量</text>
          <input v-model="addForm.dosage" class="input-field" placeholder="如：1片、10ml" />
        </view>

        <view class="form-group">
          <text class="form-label">提醒时间</text>
          <input v-model="addForm.time" class="input-field" placeholder="如：08:00" />
        </view>

        <view class="form-group">
          <text class="form-label">备注</text>
          <input v-model="addForm.notes" class="input-field" placeholder="可选备注" />
        </view>

        <view class="dialog-actions">
          <view class="btn-secondary dialog-btn" @tap="closeAddDialog">取消</view>
          <view class="btn-primary dialog-btn" @tap="submitReminder">确认</view>
        </view>
      </view>
    </view>
  </view>
</template>

<style scoped>
.summary-card {
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
  color: #fff;
  margin-bottom: var(--spacing-md);
}

.summary-date {
  font-size: 30rpx;
  font-weight: 600;
  margin-bottom: var(--spacing-sm);
}

.summary-progress-wrap {
  display: flex;
  align-items: center;
}

.progress-bar-bg {
  flex: 1;
  height: 16rpx;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 8rpx;
  overflow: hidden;
  margin-right: var(--spacing-sm);
}

.progress-bar-fill {
  height: 100%;
  background: #fff;
  border-radius: 8rpx;
  transition: width 0.3s;
}

.progress-text {
  font-size: 24rpx;
  opacity: 0.9;
  white-space: nowrap;
}

.loading-state {
  display: flex;
  justify-content: center;
  padding: 80rpx 0;
}

.med-list {
  display: flex;
  flex-direction: column;
}

.med-item {
  padding: var(--spacing-sm) var(--spacing-md);
}

.med-info {
  flex: 1;
}

.med-name-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  margin-bottom: 6rpx;
}

.med-name {
  font-size: 30rpx;
  font-weight: 600;
  color: var(--color-text-primary);
}

.med-dosage {
  font-size: 24rpx;
}

.med-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10rpx;
}

.med-time {
  font-size: 28rpx;
  font-weight: 600;
  color: var(--color-primary);
}

.take-btn {
  padding: 10rpx 32rpx;
  font-size: 24rpx;
  border-radius: var(--radius-sm);
}

.med-notes {
  font-size: 22rpx;
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
