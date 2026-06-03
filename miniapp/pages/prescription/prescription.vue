<template>
  <view class="page">
    <!-- 查询表单 -->
    <view class="query-card">
      <view class="card-title">处方查询</view>
      <view class="form-item">
        <text class="label">姓名</text>
        <input class="input" v-model="queryForm.name" placeholder="请输入姓名" />
      </view>
      <view class="form-item">
        <text class="label">身份证号</text>
        <input class="input" v-model="queryForm.id_card" placeholder="请输入身份证号" type="idcard" />
      </view>
      <view class="btn-wrap">
        <button class="btn-primary" :disabled="loading" @click="queryPrescriptions">{{ loading ? '查询中...' : '查询处方' }}</button>
      </view>
    </view>

    <!-- 处方列表 -->
    <view class="result-section" v-if="prescriptions.length > 0">
      <view class="section-title">查询结果 ({{ prescriptions.length }})</view>
      <view class="prescription-list">
        <view class="prescription-card" v-for="item in prescriptions" :key="item.id" @click="viewDetail(item)">
          <view class="prescription-header">
            <text class="prescription-no">{{ item.prescription_no }}</text>
            <text :class="'tag-' + getStatusType(item.status)">{{ getStatusText(item.status) }}</text>
          </view>
          <view class="prescription-body">
            <view class="info-row">
              <text class="label">医院：</text>
              <text class="value">{{ item.hospital }}</text>
            </view>
            <view class="info-row">
              <text class="label">科室：</text>
              <text class="value">{{ item.department }}</text>
            </view>
            <view class="info-row">
              <text class="label">诊断：</text>
              <text class="value">{{ item.diagnosis }}</text>
            </view>
            <view class="info-row">
              <text class="label">日期：</text>
              <text class="value">{{ item.prescription_date }}</text>
            </view>
          </view>
          <view class="prescription-footer">
            <text class="drug-count">药品：{{ item.medications?.length || 0 }}种</text>
            <text class="amount" v-if="item.total_amount">￥{{ item.total_amount }}</text>
          </view>
        </view>
      </view>
    </view>

    <view class="empty-tip" v-else-if="hasQueried && !loading">
      <view class="empty-box">
        <text class="empty-icon">📋</text>
        <text class="empty-text">暂无处方记录</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
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

const loading = ref(false)
const hasQueried = ref(false)
const prescriptions = ref<Prescription[]>([])
const queryForm = reactive({
  name: '',
  id_card: ''
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

const queryPrescriptions = async () => {
  if (!queryForm.name) {
    uni.showToast({ title: '请输入姓名', icon: 'none' })
    return
  }
  if (!queryForm.id_card) {
    uni.showToast({ title: '请输入身份证号', icon: 'none' })
    return
  }
  
  loading.value = true
  hasQueried.value = true
  
  try {
    const res = await prescriptionApi.query(queryForm)
    prescriptions.value = res.data || []
  } catch (e) {
    // 模拟数据
    prescriptions.value = [
      {
        id: 'RX001',
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
          { name: '二甲双胍片', specification: '0.5g*20片', quantity: '2', dosage: '0.5g', usage: '口服，每日2次' }
        ],
        status: 'valid',
        total_amount: 156.80,
        created_at: '2024-03-15 10:30:00'
      }
    ]
  } finally {
    loading.value = false
  }
}

const viewDetail = (item: Prescription) => {
  uni.navigateTo({ url: `/pages/prescription/detail?id=${item.id}` })
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: var(--color-bg-page);
  padding: 20rpx;
}

.query-card {
  background: #FFFFFF;
  border-radius: 15rpx;
  padding: 30rpx;
  margin-bottom: 30rpx;
}

.card-title {
  font-size: 32rpx;
  font-weight: bold;
  color: var(--color-text-primary);
  margin-bottom: 30rpx;
}

.form-item {
  display: flex;
  align-items: center;
  margin-bottom: 20rpx;
}

.label {
  width: 160rpx;
  font-size: 28rpx;
  color: #666;
}

.input {
  flex: 1;
  height: 70rpx;
  background: #f5f5f5;
  border-radius: 10rpx;
  padding: 0 20rpx;
  font-size: 28rpx;
}

.btn-wrap {
  margin-top: 30rpx;
}

.result-section {
  margin-top: 20rpx;
}

.section-title {
  font-size: 28rpx;
  color: #666;
  margin-bottom: 20rpx;
}

.prescription-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.prescription-card {
  background: #fff;
  border-radius: 15rpx;
  padding: 25rpx;
}

.prescription-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
  padding-bottom: 15rpx;
  border-bottom: 1rpx solid #f0f0f0;
}

.prescription-no {
  font-size: 28rpx;
  font-weight: bold;
  color: #333;
}

.prescription-body {
  margin-bottom: 15rpx;
}

.info-row {
  display: flex;
  margin-bottom: 10rpx;
}

.info-row .label {
  width: auto;
  font-size: 26rpx;
  color: #999;
}

.info-row .value {
  font-size: 26rpx;
  color: #333;
}

.prescription-footer {
  display: flex;
  justify-content: space-between;
  font-size: 24rpx;
  color: #999;
}

.drug-count {
  color: #666;
}

.amount {
  color: #ff6b6b;
  font-weight: bold;
}

.empty-tip {
  margin-top: 100rpx;
}

.btn-primary {
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border: none;
  border-radius: 50rpx;
  padding: 24rpx 0;
  font-size: 30rpx;
}

.btn-primary[disabled] {
  background: #a0cfff;
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
