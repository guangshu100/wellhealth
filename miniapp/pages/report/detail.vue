<template>
  <view class="detail-page">
    <view class="header">
      <text class="title">{{ report.name }}</text>
      <text class="date">{{ report.date }}</text>
    </view>
    
    <view class="section">
      <text class="section-title">基本信息</text>
      <view class="info-row">
        <text class="label">体检人：</text>
        <text class="value">{{ report.patientName }}</text>
      </view>
      <view class="info-row">
        <text class="label">体检机构：</text>
        <text class="value">{{ report.hospital }}</text>
      </view>
    </view>
    
    <view class="section">
      <text class="section-title">体检项目</text>
      <view class="items">
        <view class="item" v-for="item in report.items" :key="item.name">
          <view class="item-header">
            <text class="item-name">{{ item.name }}</text>
            <text class="item-value" :class="{ abnormal: item.abnormal }">
              {{ item.value }} {{ item.unit }}
            </text>
          </view>
          <view class="item-range">
            正常范围：{{ item.range }}
          </view>
        </view>
      </view>
    </view>
    
    <view class="section">
      <text class="section-title">医生建议</text>
      <text class="advice">{{ report.advice }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const report = ref({
  name: '年度体检报告',
  date: '2024-03-15',
  patientName: '张三',
  hospital: '第一人民医院',
  items: [
    { name: '空腹血糖', value: 6.5, unit: 'mmol/L', range: '3.9-6.1', abnormal: false },
    { name: '糖化血红蛋白', value: 6.8, unit: '%', range: '4.0-6.0', abnormal: true },
    { name: '总胆固醇', value: 5.2, unit: 'mmol/L', range: '3.1-5.7', abnormal: false },
    { name: '甘油三酯', value: 1.8, unit: 'mmol/L', range: '0.4-1.7', abnormal: true },
    { name: '血压', value: '128/82', unit: 'mmHg', range: '90-140/60-90', abnormal: false }
  ],
  advice: '建议控制饮食，减少高糖高脂食物摄入，适当增加运动，定期复查血糖血脂。'
})
</script>

<style scoped lang="scss">
.detail-page {
  min-height: 100vh;
  background: #f5f5f5;
  padding: 20rpx;
}

.header {
  background: #fff;
  padding: 30rpx;
  border-radius: 16rpx;
  margin-bottom: 20rpx;
  
  .title {
    font-size: 36rpx;
    font-weight: bold;
    color: #333;
    display: block;
    margin-bottom: 10rpx;
  }
  
  .date {
    font-size: 26rpx;
    color: #999;
  }
}

.section {
  background: #fff;
  padding: 30rpx;
  border-radius: 16rpx;
  margin-bottom: 20rpx;
  
  .section-title {
    font-size: 32rpx;
    font-weight: bold;
    color: #333;
    display: block;
    margin-bottom: 20rpx;
  }
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 15rpx 0;
  border-bottom: 1rpx solid #f0f0f0;
  
  &:last-child {
    border-bottom: none;
  }
  
  .label {
    color: #666;
    font-size: 28rpx;
  }
  
  .value {
    color: #333;
    font-size: 28rpx;
  }
}

.items {
  .item {
    padding: 20rpx;
    background: #f9f9f9;
    border-radius: 12rpx;
    margin-bottom: 15rpx;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    .item-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10rpx;
    }
    
    .item-name {
      font-size: 28rpx;
      color: #333;
    }
    
    .item-value {
      font-size: 30rpx;
      font-weight: bold;
      color: var(--color-primary);
      
      &.abnormal {
        color: #f56c6c;
      }
    }
    
    .item-range {
      font-size: 24rpx;
      color: #999;
    }
  }
}

.advice {
  font-size: 28rpx;
  color: #666;
  line-height: 1.8;
}
</style>
