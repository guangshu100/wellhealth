<template>
  <view class="page">
    <!-- 上传报告 -->
    <view class="upload-section">
      <button class="btn-primary" @click="uploadReport">📷 上传体检报告</button>
    </view>

    <!-- 报告列表 -->
    <view class="report-list">
      <view class="report-card" v-for="item in reports" :key="item.id" @click="viewReport(item)">
        <view class="report-icon">📊</view>
        <view class="report-info">
          <text class="report-title">{{ item.title }}</text>
          <text class="report-meta">{{ item.hospital }} · {{ item.exam_date }}</text>
        </view>
        <view class="report-status">
          <text :class="item.status === 'analyzed' ? 'tag-success' : 'tag-warning'">{{ item.status === 'analyzed' ? '已分析' : '待分析' }}</text>
        </view>
      </view>
    </view>

    <view class="empty-tip" v-if="reports.length === 0">
      <view class="empty-box">
        <text class="empty-icon">📊</text>
        <text class="empty-text">暂无体检报告</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { reportApi, patientApi } from '@/utils/api'

interface Report {
  id: string
  title: string
  report_type: string
  hospital?: string
  exam_date: string
  status: string
}

const patientId = ref('')
const reports = ref<Report[]>([])

onMounted(async () => {
  await loadData()
})

const loadData = async () => {
  try {
    const patient = await patientApi.getMyPatient()
    patientId.value = patient?.id
    
    if (patientId.value) {
      const res = await reportApi.getReports(patientId.value)
      reports.value = res || []
    }
  } catch (e) {
    reports.value = [
      { id: '1', title: '年度体检报告', report_type: 'annual', hospital: '市第一医院', exam_date: '2024-03-15', status: 'analyzed' },
      { id: '2', title: '糖尿病专项检查', report_type: 'special', hospital: '市第一医院', exam_date: '2024-01-20', status: 'analyzed' }
    ]
  }
}

const uploadReport = () => {
  uni.chooseImage({
    count: 1,
    success: async (res) => {
      uni.showLoading({ title: '上传中...' })
      
      // 模拟上传
      setTimeout(() => {
        uni.hideLoading()
        uni.showToast({ title: '上传成功，请完善信息' })
        
        // 跳转到手动录入页面
        uni.navigateTo({ url: '/pages/report/manual-input' })
      }, 1500)
    }
  })
}

const viewReport = (item: Report) => {
  uni.navigateTo({ url: `/pages/report/detail?id=${item.id}` })
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: var(--color-bg-page);
  padding: 20rpx;
}

.upload-section {
  margin-bottom: 30rpx;
}

.report-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.report-card {
  display: flex;
  align-items: center;
  background: #FFFFFF;
  border-radius: 15rpx;
  padding: 30rpx;
}

.report-icon {
  font-size: 50rpx;
  margin-right: 20rpx;
}

.report-info {
  flex: 1;
}

.report-title {
  display: block;
  font-size: 30rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 8rpx;
}

.report-meta {
  font-size: 24rpx;
  color: #999;
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
