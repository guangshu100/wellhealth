<template>
  <view class="page">
    <view class="card">
      <text class="section-title">购药记录查询</text>
      <view class="form-item">
        <text class="form-label">姓名</text>
        <input class="input-field" v-model="form.name" placeholder="请输入姓名" />
      </view>
      <view class="form-item">
        <text class="form-label">身份证号</text>
        <input class="input-field" v-model="form.id_card" placeholder="请输入身份证号" />
      </view>
      <view class="btn-primary mt-md" @tap="handleSearch">
        <text style="color:#fff;text-align:center">查询</text>
      </view>
    </view>

    <view v-if="loading" class="flex-center mt-md">
      <text class="text-hint">查询中...</text>
    </view>

    <view v-if="!loading && searched && results.length === 0" class="empty-state mt-md">
      <text class="empty-icon">💊</text>
      <text class="empty-text">未查询到购药记录</text>
    </view>

    <view v-for="item in results" :key="item.id" class="card result-card">
      <view class="flex-row flex-between">
        <text class="text-primary" style="font-weight:600">{{ item.patient_name }}</text>
        <text class="tag tag-primary">{{ item.pharmacy }}</text>
      </view>
      <view class="mt-sm flex-col gap-xs">
        <view class="flex-row">
          <text class="text-hint" style="width:160rpx">药品名称</text>
          <text class="text-secondary">{{ item.drug_name }}</text>
        </view>
        <view class="flex-row">
          <text class="text-hint" style="width:160rpx">规格</text>
          <text class="text-secondary">{{ item.drug_specification }}</text>
        </view>
        <view class="flex-row">
          <text class="text-hint" style="width:160rpx">数量</text>
          <text class="text-secondary">{{ item.quantity }}</text>
        </view>
        <view class="flex-row">
          <text class="text-hint" style="width:160rpx">单价</text>
          <text class="text-secondary">¥{{ item.unit_price }}</text>
        </view>
        <view class="flex-row">
          <text class="text-hint" style="width:160rpx">总金额</text>
          <text class="text-primary" style="font-weight:600">¥{{ item.total_amount }}</text>
        </view>
        <view class="flex-row">
          <text class="text-hint" style="width:160rpx">购买日期</text>
          <text class="text-secondary">{{ item.purchase_date }}</text>
        </view>
        <view v-if="item.prescription_no" class="flex-row">
          <text class="text-hint" style="width:160rpx">处方编号</text>
          <text class="text-secondary">{{ item.prescription_no }}</text>
        </view>
        <view v-if="item.payment_method" class="flex-row">
          <text class="text-hint" style="width:160rpx">支付方式</text>
          <text class="text-secondary">{{ item.payment_method }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import api from '@/utils/api'

const form = ref({
  name: '',
  id_card: '',
})

const results = ref<any[]>([])
const loading = ref(false)
const searched = ref(false)

const handleSearch = async () => {
  if (!form.value.name && !form.value.id_card) {
    uni.showToast({ title: '请至少填写一项查询条件', icon: 'none' })
    return
  }
  loading.value = true
  searched.value = true
  try {
    const res: any = await api.post('/medication-purchases/query', {
      name: form.value.name,
      id_card: form.value.id_card,
    })
    results.value = res.data || []
  } catch (e) {
    uni.showToast({ title: '查询失败', icon: 'none' })
    results.value = []
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.form-item {
  margin-bottom: var(--spacing-md);
}

.form-label {
  font-size: 26rpx;
  color: var(--color-text-secondary);
  margin-bottom: 8rpx;
  display: block;
}

.result-card {
  padding: var(--spacing-md);
}
</style>
