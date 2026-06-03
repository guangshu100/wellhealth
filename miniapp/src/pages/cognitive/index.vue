<template>
  <view class="page">
    <view class="header">
      <text class="title">认知健康</text>
      <text class="subtitle">科学评估与训练，守护大脑健康</text>
    </view>

    <view class="card-list">
      <view class="entry-card" @click="goTo('/pages/cognitive/assessment')">
        <view class="card-icon">🧠</view>
        <view class="card-body">
          <text class="card-title">认知评估</text>
          <text class="card-desc">通过AI分析您的认知状态，获取多维度评估报告</text>
        </view>
        <view class="card-arrow">›</view>
      </view>

      <view class="entry-card" @click="goTo('/pages/cognitive/training')">
        <view class="card-icon">🎮</view>
        <view class="card-body">
          <text class="card-title">认知训练</text>
          <text class="card-desc">趣味游戏训练，提升记忆、语言和执行能力</text>
        </view>
        <view class="card-arrow">›</view>
      </view>

      <view class="entry-card" @click="goTo('/pages/cognitive/report')">
        <view class="card-icon">📊</view>
        <view class="card-body">
          <text class="card-title">训练报告</text>
          <text class="card-desc">查看认知评分趋势与训练历史记录</text>
        </view>
        <view class="card-arrow">›</view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
const goTo = (url: string) => {
  uni.navigateTo({ url })
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--color-bg-page);
}

.header {
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
  border-radius: 0 0 30rpx 30rpx;
  padding: 50rpx 30rpx 40rpx;
  text-align: center;
}

.title {
  display: block;
  font-size: 40rpx;
  font-weight: bold;
  color: var(--color-text-inverse);
}

.subtitle {
  display: block;
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.9);
  margin-top: 10rpx;
}

.card-list {
  padding: 30rpx 20rpx;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.entry-card {
  display: flex;
  align-items: center;
  background: var(--color-bg-card);
  border-radius: var(--radius-md);
  padding: 30rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}

.card-icon {
  font-size: 56rpx;
  margin-right: 24rpx;
  flex-shrink: 0;
}

.card-body {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.card-title {
  font-size: 32rpx;
  font-weight: bold;
  color: var(--color-text-primary);
  margin-bottom: 8rpx;
}

.card-desc {
  font-size: 24rpx;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.card-arrow {
  font-size: 40rpx;
  color: var(--color-text-hint);
  margin-left: 16rpx;
  flex-shrink: 0;
}
</style>
