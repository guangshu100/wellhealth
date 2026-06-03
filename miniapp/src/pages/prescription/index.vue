<template>
  <view class="page">
    <view class="card">
      <text class="section-title">处方查询</text>
      <view class="form-item">
        <text class="form-label">姓名</text>
        <input class="input-field" v-model="form.name" placeholder="请输入姓名" />
      </view>
      <view class="form-item">
        <text class="form-label">身份证号</text>
        <input class="input-field" v-model="form.id_card" placeholder="请输入身份证号" />
      </view>
      <view class="form-item">
        <text class="form-label">处方编号</text>
        <input class="input-field" v-model="form.prescription_no" placeholder="请输入处方编号（选填）" />
      </view>
      <view class="btn-primary mt-md" @tap="handleSearch">
        <text style="color:#fff;text-align:center">查询</text>
      </view>
    </view>

    <view v-if="loading" class="flex-center mt-md">
      <text class="text-hint">查询中...</text>
    </view>

    <view v-if="!loading && searched && results.length === 0" class="empty-state mt-md">
      <text class="empty-icon">📋</text>
      <text class="empty-text">未查询到处方记录</text>
    </view>

    <view v-for="item in results" :key="item.id" class="card result-card">
      <view class="flex-row flex-between">
        <text class="text-primary" style="font-weight:600">{{ item.patient_name }}</text>
        <text class="tag" :class="getStatusClass(item.status)">{{ item.status }}</text>
      </view>
      <view class="mt-sm flex-col gap-xs">
        <view class="flex-row">
          <text class="text-hint" style="width:160rpx">处方编号</text>
          <text class="text-secondary">{{ item.prescription_no }}</text>
        </view>
        <view class="flex-row">
          <text class="text-hint" style="width:160rpx">医院</text>
          <text class="text-secondary">{{ item.hospital }}</text>
        </view>
        <view class="flex-row">
          <text class="text-hint" style="width:160rpx">科室</text>
          <text class="text-secondary">{{ item.department }}</text>
        </view>
        <view class="flex-row">
          <text class="text-hint" style="width:160rpx">医生</text>
          <text class="text-secondary">{{ item.doctor }}</text>
        </view>
        <view class="flex-row">
          <text class="text-hint" style="width:160rpx">诊断</text>
          <text class="text-secondary">{{ item.diagnosis }}</text>
        </view>
        <view class="flex-row">
          <text class="text-hint" style="width:160rpx">处方日期</text>
          <text class="text-secondary">{{ item.prescription_date }}</text>
        </view>
      </view>
      <view v-if="item.medications && item.medications.length > 0" class="mt-sm">
        <text class="text-primary" style="font-weight:600">药品列表</text>
        <view v-for="(med, idx) in item.medications" :key="idx" class="med-item mt-sm">
          <view class="flex-row flex-between">
            <text class="text-primary">{{ med.name }}</text>
            <text class="text-secondary">{{ med.specification }}</text>
          </view>
          <text class="text-hint" style="font-size:22rpx">{{ med.dosage }} | {{ med.usage }}</text>
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
  prescription_no: '',
})

const results = ref<any[]>([])
const loading = ref(false)
const searched = ref(false)

const getStatusClass = (status: string) => {
  const map: Record<string, string> = { active: 'tag-success', expired: 'tag-warning', cancelled: 'tag-danger' }
  return map[status] || 'tag-info'
}

const handleSearch = async () => {
  if (!form.value.name && !form.value.id_card && !form.value.prescription_no) {
    uni.showToast({ title: '请至少填写一项查询条件', icon: 'none' })
    return
  }
  loading.value = true
  searched.value = true
  try {
    const res: any = await api.post('/prescriptions/query', {
      name: form.value.name,
      id_card: form.value.id_card,
      prescription_no: form.value.prescription_no || undefined,
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

.med-item {
  padding: var(--spacing-sm);
  background: var(--color-bg-page);
  border-radius: var(--radius-sm);
}
</style>
