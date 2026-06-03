<template>
  <view class="page">
    <!-- 头部 -->
    <view class="header">
      <text class="title">亲情账号</text>
      <text class="subtitle">关爱家人，守护健康</text>
    </view>

    <!-- 我的家庭 -->
    <view class="section-card">
      <view class="section-header">
        <text class="section-title">我的家庭</text>
        <view class="btn-add" @click="showCreateFamily">+ 创建</view>
      </view>
      
      <view v-if="families.length === 0" class="empty-state">
        <text class="empty-text">暂无家庭</text>
        <view class="btn-primary" @click="showCreateFamily">创建第一个家庭</view>
      </view>
      
      <view v-else class="family-list">
        <view 
          class="family-item" 
          v-for="family in families" 
          :key="family.id"
          :class="{ active: selectedFamily?.id === family.id }"
          @click="selectFamily(family)"
        >
          <view class="family-icon">👨‍👩‍👧‍👦</view>
          <view class="family-info">
            <text class="family-name">{{ family.name }}</text>
            <text class="family-meta">{{ formatDate(family.created_at) }} 创建</text>
          </view>
          <text class="arrow">›</text>
        </view>
      </view>
    </view>

    <!-- 家庭成员 -->
    <view class="section-card" v-if="selectedFamily">
      <view class="section-header">
        <text class="section-title">家庭成员</text>
        <view class="btn-add" @click="showAddMember">+ 添加</view>
      </view>
      
      <view v-if="members.length === 0" class="empty-state">
        <text class="empty-text">暂无成员</text>
      </view>
      
      <view v-else class="member-list">
        <view class="member-item" v-for="member in members" :key="member.id">
          <view class="member-avatar">{{ member.user_name?.charAt(0) }}</view>
          <view class="member-info">
            <text class="member-name">{{ member.user_name }}</text>
            <view class="member-tags">
              <text class="tag-role" :class="'tag-' + member.role">{{ getRoleLabel(member.role) }}</text>
              <text class="tag-relation">{{ getRelationLabel(member.relationship) }}</text>
            </view>
          </view>
          <view v-if="member.patient_id" class="btn-health" @click="viewMemberHealth(member)">
            查看健康
          </view>
        </view>
      </view>
    </view>

    <!-- 健康概览 -->
    <view class="section-card" v-if="selectedMember && healthSummary">
      <view class="section-header">
        <text class="section-title">{{ selectedMember.user_name }} 的健康状况</text>
        <view class="btn-close" @click="selectedMember = null">关闭</view>
      </view>
      
      <view class="health-summary">
        <view class="health-grid">
          <view class="health-item">
            <text class="health-label">血糖趋势</text>
            <text class="health-value" :class="getTrendClass(healthSummary.trends?.blood_sugar?.trend)">
              {{ healthSummary.trends?.blood_sugar?.trend || '暂无' }}
            </text>
            <text class="health-avg">平均值: {{ healthSummary.trends?.blood_sugar?.avg_value || '-' }}</text>
          </view>
          <view class="health-item">
            <text class="health-label">血压趋势</text>
            <text class="health-value" :class="getTrendClass(healthSummary.trends?.blood_pressure?.trend)">
              {{ healthSummary.trends?.blood_pressure?.trend || '暂无' }}
            </text>
            <text class="health-avg">平均值: {{ healthSummary.trends?.blood_pressure?.avg_value || '-' }}</text>
          </view>
          <view class="health-item">
            <text class="health-label">用药依从性</text>
            <text class="health-value">{{ healthSummary.medication_compliance?.compliance_rate || 0 }}%</text>
            <view class="progress-bar">
              <view class="progress-fill" :style="{width: (healthSummary.medication_compliance?.compliance_rate || 0) + '%'}"></view>
            </view>
          </view>
        </view>
        
        <view v-if="healthSummary.alerts?.length > 0" class="alerts-section">
          <text class="alert-title">⚠️ 健康预警</text>
          <view 
            class="alert-item" 
            v-for="alert in healthSummary.alerts" 
            :key="alert.title"
            :class="'alert-' + alert.severity"
          >
            <text class="alert-title-text">{{ alert.title }}</text>
            <text class="alert-content">{{ alert.content }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 关怀消息 -->
    <view class="section-card">
      <view class="section-header">
        <text class="section-title">关怀消息</text>
        <view v-if="unreadCount > 0" class="badge">{{ unreadCount }}</view>
      </view>
      
      <view v-if="messages.length === 0" class="empty-state">
        <text class="empty-text">暂无消息</text>
      </view>
      
      <view v-else class="message-list">
        <view 
          class="message-item" 
          v-for="msg in messages" 
          :key="msg.id"
          :class="{ unread: !msg.is_read }"
        >
          <view class="message-header">
            <text class="sender">{{ msg.from_user_name }}</text>
            <text class="time">{{ formatDate(msg.created_at) }}</text>
          </view>
          <text class="message-content">{{ msg.content }}</text>
        </view>
      </view>
    </view>

    <!-- 创建家庭弹窗 -->
    <view class="modal" v-if="showCreateModal">
      <view class="modal-mask" @click="showCreateModal = false"></view>
      <view class="modal-content">
        <view class="modal-header">
          <text class="modal-title">创建家庭</text>
          <text class="modal-close" @click="showCreateModal = false">×</text>
        </view>
        <view class="modal-body">
          <input class="input" v-model="newFamilyName" placeholder="请输入家庭名称" />
        </view>
        <view class="modal-footer">
          <view class="btn-cancel" @click="showCreateModal = false">取消</view>
          <view class="btn-confirm" @click="createFamily">创建</view>
        </view>
      </view>
    </view>

    <!-- 添加成员弹窗 -->
    <view class="modal" v-if="showAddModal">
      <view class="modal-mask" @click="showAddModal = false"></view>
      <view class="modal-content">
        <view class="modal-header">
          <text class="modal-title">添加成员</text>
          <text class="modal-close" @click="showAddModal = false">×</text>
        </view>
        <view class="modal-body">
          <input class="input" v-model="newMember.user_name" placeholder="请输入用户名" />
          <picker :range="roleOptions" @change="onRoleChange">
            <view class="picker">{{ newMember.role || '请选择角色' }}</view>
          </picker>
          <picker :range="relationOptions" @change="onRelationChange">
            <view class="picker">{{ newMember.relationship || '请选择关系' }}</view>
          </picker>
        </view>
        <view class="modal-footer">
          <view class="btn-cancel" @click="showAddModal = false">取消</view>
          <view class="btn-confirm" @click="addMember">添加</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { familyApi } from '@/utils/api'

const userId = ref('user_001')

const families = ref<Array<{id: string; name: string; created_at: string}>>([])
const selectedFamily = ref<any>(null)
const members = ref<Array<any>>([])
const selectedMember = ref<any>(null)
const healthSummary = ref<any>(null)
const messages = ref<Array<any>>([])
const unreadCount = ref(0)

const showCreateModal = ref(false)
const showAddModal = ref(false)
const newFamilyName = ref('')
const newMember = ref({ user_name: '', role: '子女', relationship: '儿子' })

const roleOptions = ['父母', '子女']
const relationOptions = ['爸爸', '妈妈', '儿子', '女儿']

const loadFamilies = async () => {
  try {
    const res = await familyApi.getUserFamilies(userId.value)
    if (res.success) {
      families.value = res.families
      if (families.value.length > 0) {
        selectFamily(families.value[0])
      }
    }
  } catch (e) {
    // 模拟数据
    families.value = [
      { id: 'f1', name: '幸福一家', created_at: '2024-01-01' }
    ]
    selectFamily(families.value[0])
  }
}

const selectFamily = async (family: any) => {
  selectedFamily.value = family
  await loadMembers(family.id)
  await loadMessages()
}

const loadMembers = async (familyId: string) => {
  try {
    const res = await familyApi.getFamilyMembers(familyId)
    if (res.success) {
      members.value = res.members
    }
  } catch (e) {
    // 模拟数据
    members.value = [
      { id: 'm1', user_name: '爸爸', role: 'parent', relationship: 'father', patient_id: 'p1' },
      { id: 'm2', user_name: '妈妈', role: 'parent', relationship: 'mother', patient_id: 'p2' }
    ]
  }
}

const viewMemberHealth = async (member: any) => {
  if (!member.patient_id) return
  selectedMember.value = member
  try {
    const res = await familyApi.getPatientHealthSummary(member.patient_id)
    if (res.success) {
      healthSummary.value = res.summary
    }
  } catch (e) {
    // 模拟数据
    healthSummary.value = {
      trends: {
        blood_sugar: { trend: 'stable', avg_value: '6.5 mmol/L' },
        blood_pressure: { trend: 'falling', avg_value: '128/80 mmHg' }
      },
      medication_compliance: { compliance_rate: 85 },
      alerts: [
        { title: '血糖偏高', content: '最近一次血糖值为7.8mmol/L', severity: 'medium' }
      ]
    }
  }
}

const loadMessages = async () => {
  try {
    const res = await familyApi.getUnreadMessages(userId.value)
    if (res.success) {
      messages.value = res.messages
      unreadCount.value = res.messages.filter((m: any) => !m.is_read).length
    }
  } catch (e) {
    // 模拟数据
    messages.value = [
      { id: 'msg1', from_user_name: '爸爸', content: '今天记得吃药', is_read: false, created_at: '2024-03-15' }
    ]
    unreadCount.value = 1
  }
}

const showCreateFamily = () => {
  newFamilyName.value = ''
  showCreateModal.value = true
}

const createFamily = async () => {
  if (!newFamilyName.value) {
    uni.showToast({ title: '请输入家庭名称', icon: 'none' })
    return
  }
  try {
    await familyApi.createFamily({
      name: newFamilyName.value,
      owner_id: userId.value,
      owner_name: '我'
    })
    uni.showToast({ title: '创建成功', icon: 'success' })
    showCreateModal.value = false
    await loadFamilies()
  } catch (e) {
    uni.showToast({ title: '创建失败', icon: 'none' })
  }
}

const showAddMember = () => {
  newMember.value = { user_name: '', role: '子女', relationship: '儿子' }
  showAddModal.value = true
}

const onRoleChange = (e: any) => {
  newMember.value.role = roleOptions[e.detail.value]
}

const onRelationChange = (e: any) => {
  newMember.value.relationship = relationOptions[e.detail.value]
}

const addMember = async () => {
  if (!selectedFamily.value || !newMember.value.user_name) {
    uni.showToast({ title: '请填写完整信息', icon: 'none' })
    return
  }
  try {
    await familyApi.addMember({
      family_id: selectedFamily.value.id,
      user_id: 'user_' + Date.now(),
      user_name: newMember.value.user_name,
      role: newMember.value.role === '父母' ? 'parent' : 'child',
      relationship: newMember.value.relationship
    })
    uni.showToast({ title: '添加成功', icon: 'success' })
    showAddModal.value = false
    await loadMembers(selectedFamily.value.id)
  } catch (e) {
    uni.showToast({ title: '添加失败', icon: 'none' })
  }
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}/${date.getDate()}`
}

const getRoleLabel = (role: string) => {
  const labels: Record<string, string> = { owner: '户主', parent: '父母', child: '子女' }
  return labels[role] || role
}

const getRelationLabel = (relation: string) => {
  const labels: Record<string, string> = { father: '爸爸', mother: '妈妈', son: '儿子', daughter: '女儿' }
  return labels[relation] || relation
}

const getTrendClass = (trend: string) => {
  if (trend === 'falling') return 'trend-good'
  if (trend === 'rising') return 'trend-bad'
  return 'trend-normal'
}

onMounted(() => {
  loadFamilies()
})
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--color-bg-page);
  padding: 20rpx;
  padding-bottom: 40rpx;
}

.header {
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
  border-radius: 20rpx;
  padding: 40rpx 30rpx;
  margin-bottom: 20rpx;
  text-align: center;
}

.title {
  display: block;
  font-size: 40rpx;
  font-weight: bold;
  color: var(--color-text-inverse);
}

.subtitle {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 10rpx;
}

.section-card {
  background: #FFFFFF;
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

.btn-add {
  color: var(--color-primary);
  font-size: 28rpx;
}

.btn-close {
  color: var(--color-text-secondary);
  font-size: 28rpx;
}

.empty-state {
  text-align: center;
  padding: 40rpx;
}

.empty-text {
  color: #999;
  font-size: 26rpx;
  margin-bottom: 20rpx;
}

.btn-primary {
  background: var(--color-primary);
  color: var(--color-text-inverse);
  padding: 20rpx 40rpx;
  border-radius: 40rpx;
  font-size: 28rpx;
  display: inline-block;
}

.family-list, .member-list {
  display: flex;
  flex-direction: column;
  gap: 15rpx;
}

.family-item {
  display: flex;
  align-items: center;
  padding: 20rpx;
  background: #f9f9f9;
  border-radius: 10rpx;
  border: 2rpx solid transparent;
}

.family-item.active {
  border-color: var(--color-primary);
  background: #f0f9ff;
}

.family-icon {
  font-size: 48rpx;
  margin-right: 20rpx;
}

.family-info, .member-info {
  flex: 1;
}

.family-name, .member-name {
  display: block;
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
}

.family-meta {
  font-size: 22rpx;
  color: #999;
}

.member-avatar {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  background: var(--color-primary);
  color: var(--color-text-inverse);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
  margin-right: 20rpx;
}

.member-tags {
  display: flex;
  gap: 10rpx;
  margin-top: 8rpx;
}

.tag-role {
  padding: 4rpx 12rpx;
  border-radius: 20rpx;
  font-size: 20rpx;
  color: #fff;
}

.tag-owner { background: #f56c6c; }
.tag-parent { background: #e6a23c; }
.tag-child { background: var(--color-primary); }

.tag-relation {
  font-size: 22rpx;
  color: #999;
}

.btn-health {
  background: var(--color-primary);
  color: var(--color-text-inverse);
  padding: 10rpx 20rpx;
  border-radius: 30rpx;
  font-size: 24rpx;
}

.arrow {
  color: #ccc;
  font-size: 36rpx;
}

.health-summary {
  margin-top: 20rpx;
}

.health-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20rpx;
}

.health-item {
  text-align: center;
  padding: 20rpx;
  background: #f9f9f9;
  border-radius: 10rpx;
}

.health-label {
  font-size: 24rpx;
  color: #999;
}

.health-value {
  display: block;
  font-size: 30rpx;
  font-weight: bold;
  color: #333;
  margin: 10rpx 0;
}

.health-avg {
  font-size: 22rpx;
  color: #999;
}

.trend-good { color: var(--color-primary); }
.trend-bad { color: #f56c6c; }
.trend-normal { color: var(--color-primary); }

.progress-bar {
  height: 8rpx;
  background: #eee;
  border-radius: 4rpx;
  margin-top: 10rpx;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-primary);
  border-radius: 4rpx;
}

.alerts-section {
  margin-top: 20rpx;
}

.alert-title {
  font-size: 28rpx;
  font-weight: bold;
  color: #f56c6c;
  margin-bottom: 15rpx;
}

.alert-item {
  padding: 15rpx;
  background: #fff5f5;
  border-radius: 10rpx;
  margin-bottom: 10rpx;
  border-left: 4rpx solid #f56c6c;
}

.alert-title-text {
  font-size: 26rpx;
  color: #f56c6c;
  font-weight: 500;
}

.alert-content {
  font-size: 24rpx;
  color: #666;
  margin-top: 8rpx;
}

.badge {
  background: #f56c6c;
  color: #fff;
  padding: 4rpx 12rpx;
  border-radius: 20rpx;
  font-size: 22rpx;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 15rpx;
}

.message-item {
  padding: 15rpx;
  background: #f9f9f9;
  border-radius: 10rpx;
}

.message-item.unread {
  background: #f0f9ff;
}

.message-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8rpx;
}

.sender {
  font-size: 26rpx;
  font-weight: 500;
  color: #333;
}

.time {
  font-size: 22rpx;
  color: #999;
}

.message-content {
  font-size: 24rpx;
  color: #666;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 100;
}

.modal-mask {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
}

.modal-content {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 80%;
  background: #fff;
  border-radius: 20rpx;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 30rpx;
  border-bottom: 1rpx solid #eee;
}

.modal-title {
  font-size: 32rpx;
  font-weight: bold;
}

.modal-close {
  font-size: 40rpx;
  color: #999;
}

.modal-body {
  padding: 30rpx;
}

.input {
  width: 100%;
  padding: 20rpx;
  background: #f5f5f5;
  border-radius: 10rpx;
  margin-bottom: 20rpx;
  font-size: 28rpx;
}

.picker {
  padding: 20rpx;
  background: #f5f5f5;
  border-radius: 10rpx;
  margin-bottom: 20rpx;
  font-size: 28rpx;
  color: #333;
}

.modal-footer {
  display: flex;
  border-top: 1rpx solid #eee;
}

.btn-cancel, .btn-confirm {
  flex: 1;
  text-align: center;
  padding: 30rpx;
  font-size: 30rpx;
}

.btn-cancel {
  color: #666;
  border-right: 1rpx solid #eee;
}

.btn-confirm {
  color: var(--color-primary);
  font-weight: bold;
}
</style>
