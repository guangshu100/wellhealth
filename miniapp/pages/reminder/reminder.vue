<template>
  <view class="page">
    <!-- 今日提醒 -->
    <view class="today-section">
      <view class="section-header">
        <text class="section-title">💊 今日用药提醒</text>
        <text class="section-date">{{ today }}</text>
      </view>
      
      <view class="reminder-list">
        <view class="reminder-item" v-for="item in todayReminders" :key="item.id">
          <view class="reminder-info">
            <text class="drug-name">{{ item.drug_name }}</text>
            <text class="drug-dosage">{{ item.dosage }}</text>
          </view>
          <view class="reminder-times">
            <text
              v-for="time in item.times"
              :key="time"
              :class="['time-tag', { taken: isTaken(item.id, time) }]"
              @click="markTaken(item.id, time)"
            >
              {{ time }}
              <text v-if="isTaken(item.id, time)"> ✓</text>
            </text>
          </view>
        </view>
      </view>

      <view class="empty-tip" v-if="todayReminders.length === 0">
        <text>今日暂无用药提醒</text>
      </view>
    </view>

    <!-- 所有提醒 -->
    <view class="all-section">
      <view class="section-header">
        <text class="section-title">📋 所有提醒</text>
        <button class="btn-mini" @click="addReminder">添加</button>
      </view>

      <view class="reminder-list">
        <view class="reminder-card" v-for="item in reminders" :key="item.id">
          <view class="card-header">
            <text class="drug-name" style="color:#333">{{ item.drug_name }}</text>
            <switch :checked="item.enabled" @change="toggleEnabled(item)" />
          </view>
          <view class="card-body">
            <text class="dosage">{{ item.dosage }}</text>
            <text class="frequency">{{ item.frequency }}</text>
          </view>
          <view class="card-footer">
            <text class="times">{{ item.times.join('、') }}</text>
            <view class="card-actions">
              <button class="btn-mini btn-edit" @click="editReminder(item)">编辑</button>
              <button class="btn-mini btn-danger" @click="deleteReminder(item.id)">删除</button>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- 服药统计 -->
    <view class="stats-section">
      <view class="section-title">📊 本周服药统计</view>
      <view class="stats-grid">
        <view class="stat-item">
          <text class="stat-value">{{ weekStats.total }}</text>
          <text class="stat-label">应服药次数</text>
        </view>
        <view class="stat-item">
          <text class="stat-value">{{ weekStats.taken }}</text>
          <text class="stat-label">已服药次数</text>
        </view>
        <view class="stat-item">
          <text class="stat-value">{{ weekStats.compliance }}%</text>
          <text class="stat-label">遵从率</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { medicationReminderApi, patientApi } from '@/utils/api'

interface Reminder {
  id: string
  drug_name: string
  dosage: string
  frequency: string
  times: string[]
  enabled: boolean
}

const patientId = ref('')
const reminders = ref<Reminder[]>([])
const todayReminders = ref<any[]>([])
const takenRecords = ref<Record<string, boolean>>({})
const today = computed(() => {
  const d = new Date()
  return `${d.getMonth() + 1}月${d.getDate()}日`
})

const weekStats = ref({
  total: 21,
  taken: 18,
  compliance: 86
})

onMounted(async () => {
  await loadData()
})

const loadData = async () => {
  try {
    const patient = await patientApi.getMyPatient()
    patientId.value = patient?.id
    
    if (patientId.value) {
      const res = await medicationReminderApi.getReminders(patientId.value)
      reminders.value = res || []
      todayReminders.value = res?.filter((r: any) => r.enabled) || []
    }
  } catch (e) {
    // 模拟数据
    reminders.value = [
      { id: '1', drug_name: '二甲双胍', dosage: '0.5g', frequency: '每日2次', times: ['08:00', '18:00'], enabled: true },
      { id: '2', drug_name: '厄贝沙坦', dosage: '150mg', frequency: '每日1次', times: ['08:00'], enabled: true }
    ]
    todayReminders.value = reminders.value
  }
}

const isTaken = (reminderId: string, time: string): boolean => {
  return takenRecords.value[`${reminderId}_${time}`] || false
}

const markTaken = async (reminderId: string, time: string) => {
  if (isTaken(reminderId, time)) return
  
  takenRecords.value[`${reminderId}_${time}`] = true
  uni.showToast({ title: '已标记服药', icon: 'success' })
  
  if (patientId.value) {
    try {
      await medicationReminderApi.markTaken(patientId.value, reminderId, time)
    } catch (e) {}
  }
}

const addReminder = () => {
  uni.navigateTo({ url: '/pages/reminder/add' })
}

const editReminder = (item: Reminder) => {
  uni.navigateTo({ url: `/pages/reminder/add?id=${item.id}` })
}

const toggleEnabled = async (item: Reminder) => {
  if (patientId.value) {
    try {
      await medicationReminderApi.updateReminder(patientId.value, item.id, { enabled: item.enabled })
    } catch (e) {}
  }
}

const deleteReminder = async (id: string) => {
  uni.showModal({
    title: '确认删除',
    content: '确定要删除这条用药提醒吗？',
    success: async (res) => {
      if (res.confirm) {
        reminders.value = reminders.value.filter(r => r.id !== id)
        todayReminders.value = reminders.value.filter(r => r.enabled)
        if (patientId.value) {
          try {
            await medicationReminderApi.deleteReminder(patientId.value, id)
          } catch (e) {}
        }
      }
    }
  })
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: var(--color-bg-page);
  padding: 20rpx;
}

.today-section {
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
  border-radius: 20rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #fff;
}

.section-date {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.8);
}

.reminder-list {
  display: flex;
  flex-direction: column;
  gap: 15rpx;
}

.reminder-item {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 15rpx;
  padding: 20rpx;
}

.reminder-info {
  display: flex;
  align-items: center;
  gap: 15rpx;
  margin-bottom: 15rpx;
}

.drug-name {
  font-size: 30rpx;
  font-weight: bold;
  color: #fff;
}

.drug-dosage {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.8);
}

.reminder-times {
  display: flex;
  gap: 15rpx;
}

.time-tag {
  padding: 10rpx 25rpx;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 30rpx;
  font-size: 26rpx;
  color: #fff;
}

.time-tag.taken {
  background: #67C23A;
}

.empty-tip {
  text-align: center;
  padding: 40rpx;
  color: rgba(255, 255, 255, 0.8);
}

.all-section {
  background: #fff;
  border-radius: 20rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
}

.reminder-card {
  border: 1rpx solid #eee;
  border-radius: 15rpx;
  padding: 20rpx;
  margin-bottom: 15rpx;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15rpx;
}

.card-body {
  display: flex;
  gap: 20rpx;
  margin-bottom: 15rpx;
  color: #666;
  font-size: 26rpx;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.times {
  color: var(--color-primary);
  font-size: 24rpx;
}

.card-actions {
  display: flex;
  gap: 10rpx;
}

.stats-section {
  background: #fff;
  border-radius: 20rpx;
  padding: 30rpx;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20rpx;
  margin-top: 20rpx;
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 40rpx;
  font-weight: bold;
  color: var(--color-primary);
}

.stat-label {
  font-size: 24rpx;
  color: #999;
}

.btn-mini {
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border: none;
  padding: 10rpx 24rpx;
  border-radius: 30rpx;
  font-size: 24rpx;
}

.btn-mini.btn-edit {
  background: var(--color-primary);
}

.btn-mini.btn-danger {
  background: #f56c6c;
}
</style>
