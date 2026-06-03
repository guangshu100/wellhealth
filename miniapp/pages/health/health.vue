<template>
  <view class="page">
    <!-- 患者信息卡片 -->
    <view class="patient-card" v-if="patient">
      <view class="patient-header">
        <view class="avatar">{{ patient.name?.charAt(0) }}</view>
        <view class="patient-info">
          <text class="name">{{ patient.name }}</text>
          <text class="meta">{{ patient.age }}岁 · {{ patient.gender === 'male' ? '男' : '女' }}</text>
        </view>
        <button class="btn-mini" @click="editProfile">编辑</button>
      </view>
      <view class="patient-detail">
        <view class="detail-item">
          <text class="label">电话</text>
          <text class="value">{{ patient.phone || '-' }}</text>
        </view>
        <view class="detail-item">
          <text class="label">身份证</text>
          <text class="value">{{ patient.id_card ? patient.id_card.substring(0,6)+'****' : '-' }}</text>
        </view>
      </view>
    </view>

    <!-- 快速功能入口 -->
    <view class="quick-actions">
      <view class="action-item" @click="goToPrescription">
        <view class="action-icon">📋</view>
        <text class="action-text">处方查询</text>
      </view>
      <view class="action-item" @click="goToPurchase">
        <view class="action-icon">💊</view>
        <text class="action-text">购药记录</text>
      </view>
      <view class="action-item" @click="goToReport">
        <view class="action-icon">📊</view>
        <text class="action-text">体检报告</text>
      </view>
    </view>

    <!-- 疾病信息 -->
    <view class="section-card">
      <view class="section-header">
        <text class="section-title">我的疾病</text>
      </view>
      <view class="disease-list">
        <view class="disease-tag" v-for="disease in diseases" :key="disease.id">
          <text class="disease-name">{{ disease.disease_name }}</text>
          <text :class="disease.status === 'active' ? 'tag-danger' : 'tag-info'">{{ disease.status === 'active' ? '在治' : '已愈' }}</text>
        </view>
        <view v-if="diseases.length === 0" class="empty-text">暂无疾病记录</view>
      </view>
    </view>

    <!-- 用药信息 -->
    <view class="section-card">
      <view class="section-header">
        <text class="section-title">当前用药</text>
      </view>
      <view class="medication-list">
        <view class="medication-item" v-for="med in medications" :key="med.id">
          <view class="med-info">
            <text class="med-name">{{ med.drug_name }}</text>
            <text class="med-dosage">{{ med.dosage }} · {{ med.frequency }}</text>
          </view>
          <text class="med-doctor">{{ med.prescribing_doctor || '' }}</text>
        </view>
        <view v-if="medications.length === 0" class="empty-text">暂无用药记录</view>
      </view>
    </view>

    <!-- 体征数据 -->
    <view class="section-card">
      <view class="section-header">
        <text class="section-title">最新体征</text>
        <button class="btn-mini" @click="addVitals">记录</button>
      </view>
      <view class="vitals-grid">
        <view class="vital-item" v-for="vital in vitals" :key="vital.id">
          <text class="vital-type">{{ getVitalTypeName(vital.vital_type) }}</text>
          <text class="vital-value">{{ vital.value }}<text class="unit">{{ vital.unit }}</text></text>
          <text class="vital-date">{{ formatDate(vital.recorded_at) }}</text>
        </view>
        <view v-if="vitals.length === 0" class="empty-text">暂无体征记录</view>
      </view>
    </view>

    <!-- 健康建议 -->
    <view class="section-card">
      <view class="section-header">
        <text class="section-title">健康建议</text>
      </view>
      <view class="tips-list">
        <view class="tip-item">
          <text class="tip-icon">💡</text>
          <text class="tip-text">定期监测血糖血压，保持健康生活方式</text>
        </view>
        <view class="tip-item">
          <text class="tip-icon">🏃</text>
          <text class="tip-text">建议每周进行3-5次有氧运动</text>
        </view>
        <view class="tip-item">
          <text class="tip-icon">🥗</text>
          <text class="tip-text">注意低盐低脂饮食，控制碳水化合物摄入</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { patientApi } from '@/utils/api'

interface Patient {
  id: string
  name: string
  age: number
  gender: string
  phone?: string
  id_card?: string
}

interface Disease {
  id: string
  disease_name: string
  status: string
}

interface Medication {
  id: string
  drug_name: string
  dosage: string
  frequency: string
  prescribing_doctor?: string
}

interface Vital {
  id: string
  vital_type: string
  value: number
  unit: string
  recorded_at: string
}

const patient = ref<Patient | null>(null)
const diseases = ref<Disease[]>([])
const medications = ref<Medication[]>([])
const vitals = ref<Vital[]>([])

onMounted(async () => {
  await loadData()
})

const loadData = async () => {
  try {
    const profile = await patientApi.getMyPatient()
    if (profile) {
      patient.value = profile.basic_info
      diseases.value = profile.diseases || []
      medications.value = profile.medications || []
      vitals.value = profile.vitals?.slice(0, 4) || []
    }
  } catch (e) {
    // 模拟数据
    patient.value = { id: 'p1', name: '张三', age: 65, gender: 'male', phone: '13800138001' }
    diseases.value = [
      { id: 'd1', disease_name: '2型糖尿病', status: 'active' },
      { id: 'd2', disease_name: '高血压2级', status: 'active' }
    ]
    medications.value = [
      { id: 'm1', drug_name: '二甲双胍片', dosage: '0.5g', frequency: '每日2次', prescribing_doctor: '李主任' },
      { id: 'm2', drug_name: '厄贝沙坦片', dosage: '150mg', frequency: '每日1次', prescribing_doctor: '王主任' }
    ]
    vitals.value = [
      { id: 'v1', vital_type: 'blood_sugar', value: 6.5, unit: 'mmol/L', recorded_at: '2024-03-15T08:00:00' },
      { id: 'v2', vital_type: 'blood_pressure_systolic', value: 135, unit: 'mmHg', recorded_at: '2024-03-15T08:30:00' }
    ]
  }
}

const getVitalTypeName = (type: string) => {
  const map: Record<string, string> = {
    blood_sugar: '空腹血糖',
    blood_pressure_systolic: '收缩压',
    blood_pressure_diastolic: '舒张压',
    heart_rate: '心率',
    weight: '体重'
  }
  return map[type] || type
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}/${date.getDate()}`
}

const editProfile = () => {
  uni.showToast({ title: '编辑功能开发中', icon: 'none' })
}

const addVitals = () => {
  uni.showToast({ title: '记录功能开发中', icon: 'none' })
}

const goToPrescription = () => {
  uni.navigateTo({ url: '/pages/prescription/prescription' })
}

const goToPurchase = () => {
  uni.showToast({ title: '购药记录开发中', icon: 'none' })
}

const goToReport = () => {
  uni.navigateTo({ url: '/pages/report/report' })
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: var(--color-bg-page);
  padding: 20rpx;
}

.patient-card {
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
  border-radius: 20rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
}

.patient-header {
  display: flex;
  align-items: center;
  margin-bottom: 20rpx;
}

.avatar {
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40rpx;
  color: #fff;
  margin-right: 20rpx;
}

.patient-info {
  flex: 1;
}

.name {
  display: block;
  font-size: 36rpx;
  font-weight: bold;
  color: #fff;
}

.meta {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.8);
}

.patient-detail {
  display: flex;
  gap: 30rpx;
}

.detail-item {
  display: flex;
  flex-direction: column;
}

.detail-item .label {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.7);
}

.detail-item .value {
  font-size: 28rpx;
  color: #fff;
}

.quick-actions {
  display: flex;
  background: #fff;
  border-radius: 15rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
}

.action-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.action-icon {
  font-size: 48rpx;
  margin-bottom: 10rpx;
}

.action-text {
  font-size: 24rpx;
  color: #666;
}

.section-card {
  background: #fff;
  border-radius: 15rpx;
  padding: 25rpx;
  margin-bottom: 20rpx;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: bold;
  color: var(--color-text-primary);
}

.disease-list {
  display: flex;
  flex-wrap: wrap;
  gap: 15rpx;
}

.disease-tag {
  display: flex;
  align-items: center;
  gap: 10rpx;
  background: #E8F0E6;
  padding: 10rpx 20rpx;
  border-radius: 30rpx;
}

.disease-name {
  font-size: 26rpx;
  color: #333;
}

.medication-list {
  display: flex;
  flex-direction: column;
  gap: 15rpx;
}

.medication-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15rpx;
  background: var(--color-bg-page);
  border-radius: 10rpx;
}

.med-info {
  display: flex;
  flex-direction: column;
}

.med-name {
  font-size: 28rpx;
  color: var(--color-text-primary);
  font-weight: 500;
}

.med-dosage {
  font-size: 24rpx;
  color: var(--color-text-secondary);
  margin-top: 5rpx;
}

.med-doctor {
  font-size: 24rpx;
  color: var(--color-primary);
}

.vitals-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20rpx;
}

.vital-item {
  background: var(--color-bg-page);
  padding: 20rpx;
  border-radius: 10rpx;
  text-align: center;
}

.vital-type {
  display: block;
  font-size: 24rpx;
  color: var(--color-text-secondary);
  margin-bottom: 10rpx;
}

.vital-value {
  display: block;
  font-size: 36rpx;
  font-weight: bold;
  color: var(--color-text-primary);
}

.unit {
  font-size: 24rpx;
  font-weight: normal;
  margin-left: 5rpx;
}

.vital-date {
  display: block;
  font-size: 22rpx;
  color: #bbb;
  margin-top: 10rpx;
}

.tips-list {
  display: flex;
  flex-direction: column;
  gap: 15rpx;
}

.tip-item {
  display: flex;
  align-items: flex-start;
  gap: 15rpx;
}

.tip-icon {
  font-size: 30rpx;
}

.tip-text {
  font-size: 26rpx;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.empty-text {
  text-align: center;
  color: var(--color-text-secondary);
  font-size: 26rpx;
  padding: 30rpx;
}

.btn-mini {
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border: none;
  padding: 10rpx 24rpx;
  border-radius: 30rpx;
  font-size: 24rpx;
}

.tag-danger {
  background: #f56c6c;
  color: #fff;
  padding: 4rpx 12rpx;
  border-radius: 20rpx;
  font-size: 20rpx;
}

.tag-info {
  background: #909399;
  color: #fff;
  padding: 4rpx 12rpx;
  border-radius: 20rpx;
  font-size: 20rpx;
}
</style>
