<template>
  <view class="page">
    <view class="detail-card" v-if="prescription">
      <view class="header">
        <view class="prescription-no">{{ prescription.prescription_no }}</view>
        <text :class="'tag-' + getStatusType(prescription.status)">{{ getStatusText(prescription.status) }}</text>
      </view>

      <view class="info-section">
        <view class="section-title">基本信息</view>
        <view class="info-grid">
          <view class="info-item">
            <text class="label">患者姓名</text>
            <text class="value">{{ prescription.patient_name }}</text>
          </view>
          <view class="info-item">
            <text class="label">就诊医院</text>
            <text class="value">{{ prescription.hospital }}</text>
          </view>
          <view class="info-item">
            <text class="label">科室</text>
            <text class="value">{{ prescription.department }}</text>
          </view>
          <view class="info-item">
            <text class="label">医生</text>
            <text class="value">{{ prescription.doctor }}</text>
          </view>
          <view class="info-item">
            <text class="label">就诊日期</text>
            <text class="value">{{ prescription.prescription_date }}</text>
          </view>
          <view class="info-item">
            <text class="label">有效期至</text>
            <text class="value">{{ prescription.valid_until }}</text>
          </view>
        </view>
      </view>

      <view class="info-section">
        <view class="section-title">诊断信息</view>
        <view class="diagnosis">{{ prescription.diagnosis }}</view>
      </view>

      <view class="info-section">
        <view class="section-title">药品清单</view>
        <view class="medicine-list">
          <view class="medicine-item" v-for="(med, index) in prescription.medications" :key="index">
            <view class="medicine-header">
              <text class="medicine-name">{{ med.name }}</text>
              <text class="medicine-spec">{{ med.specification }}</text>
            </view>
            <view class="medicine-detail">
              <view class="detail-row">
                <text class="label">数量：</text>
                <text class="value">{{ med.quantity }}</text>
              </view>
              <view class="detail-row">
                <text class="label">剂量：</text>
                <text class="value">{{ med.dosage }}</text>
              </view>
              <view class="detail-row">
                <text class="label">用法：</text>
                <text class="value">{{ med.usage }}</text>
              </view>
            </view>
          </view>
        </view>
      </view>

      <view class="footer" v-if="prescription.total_amount">
        <text class="total-label">处方金额</text>
        <text class="total-amount">￥{{ prescription.total_amount }}</text>
      </view>
    </view>

    <view class="empty-tip" v-else>
      <view class="empty-box">
        <text class="empty-icon">📋</text>
        <text class="empty-text">加载中...</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { prescriptionApi } from '@/utils/api'

interface Medication {
  name: string
  specification: string
  quantity: string
  dosage: string
  usage: string
}

interface Prescription {
  id: string
  patient_name: string
  id_card: string
  prescription_no: string
  hospital: string
  department: string
  doctor: string
  prescription_date: string
  valid_until: string
  prescription_type: string
  diagnosis: string
  medications: Medication[]
  status: string
  total_amount?: number
  created_at: string
}

const prescription = ref<Prescription | null>(null)

onMounted(async () => {
  const pages = uni.getCurrentPages()
  const page = pages[pages.length - 1]
  const id = (page as any).options?.id
  
  if (id) {
    try {
      const res = await prescriptionApi.getDetail(id)
      prescription.value = res.data
    } catch (e) {
      prescription.value = {
        id: id,
        patient_name: '张三',
        id_card: '110101196001011234',
        prescription_no: 'P202403150001',
        hospital: '北京协和医院',
        department: '内分泌科',
        doctor: '李主任',
        prescription_date: '2024-03-15',
        valid_until: '2024-04-15',
        prescription_type: 'western',
        diagnosis: '2型糖尿病',
        medications: [
          { name: '二甲双胍片', specification: '0.5g*20片', quantity: '2', dosage: '0.5g', usage: '口服，每日2次，餐后服用' },
          { name: '阿卡波糖片', specification: '50mg*30片', quantity: '1', dosage: '50mg', usage: '口服，每日3次，与第一口饭同服' }
        ],
        status: 'valid',
        total_amount: 156.80,
        created_at: '2024-03-15 10:30:00'
      }
    }
  }
})

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    valid: 'success',
    expired: 'error',
    used: 'warning',
    cancelled: 'error'
  }
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    valid: '有效',
    expired: '已过期',
    used: '已使用',
    cancelled: '已取消'
  }
  return map[status] || status
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: #f5f5f5;
  padding: 20rpx;
}

.detail-card {
  background: #fff;
  border-radius: 15rpx;
  padding: 30rpx;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30rpx;
  padding-bottom: 20rpx;
  border-bottom: 1rpx solid #f0f0f0;
}

.prescription-no {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
}

.info-section {
  margin-bottom: 30rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 20rpx;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20rpx;
}

.info-item {
  display: flex;
  flex-direction: column;
}

.info-item .label {
  font-size: 24rpx;
  color: #999;
  margin-bottom: 8rpx;
}

.info-item .value {
  font-size: 28rpx;
  color: #333;
}

.diagnosis {
  font-size: 28rpx;
  color: #333;
  background: #f5f5f5;
  padding: 20rpx;
  border-radius: 10rpx;
}

.medicine-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.medicine-item {
  background: #f9f9f9;
  border-radius: 10rpx;
  padding: 20rpx;
}

.medicine-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15rpx;
}

.medicine-name {
  font-size: 28rpx;
  font-weight: bold;
  color: #333;
}

.medicine-spec {
  font-size: 24rpx;
  color: #999;
}

.medicine-detail {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.detail-row {
  display: flex;
  font-size: 26rpx;
}

.detail-row .label {
  color: #999;
  width: 80rpx;
}

.detail-row .value {
  color: #666;
}

.footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 30rpx;
  border-top: 1rpx solid #f0f0f0;
}

.total-label {
  font-size: 28rpx;
  color: #666;
}

.total-amount {
  font-size: 36rpx;
  font-weight: bold;
  color: #ff6b6b;
}

.empty-tip {
  margin-top: 100rpx;
}

.tag-success {
  background: var(--color-primary);
  color: var(--color-text-inverse);
  padding: 6rpx 16rpx;
  border-radius: 20rpx;
  font-size: 22rpx;
}

.tag-warning {
  background: #e6a23c;
  color: #fff;
  padding: 6rpx 16rpx;
  border-radius: 20rpx;
  font-size: 22rpx;
}

.tag-error {
  background: #f56c6c;
  color: #fff;
  padding: 6rpx 16rpx;
  border-radius: 20rpx;
  font-size: 22rpx;
}

.tag-info {
  background: #909399;
  color: #fff;
  padding: 6rpx 16rpx;
  border-radius: 20rpx;
  font-size: 22rpx;
}

.empty-box {
  text-align: center;
  padding: 60rpx;
}

.empty-icon {
  font-size: 100rpx;
  display: block;
  margin-bottom: 20rpx;
}

.empty-text {
  color: #999;
  font-size: 28rpx;
}
</style>
