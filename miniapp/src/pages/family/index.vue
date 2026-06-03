<template>
  <view class="page">
    <view class="header-card card">
      <view class="flex-between">
        <view class="flex-col gap-xs">
          <text class="header-title">❤️ 家庭关爱圈</text>
          <text class="text-secondary">家人一起，守护健康</text>
        </view>
        <view class="flex-row gap-sm">
          <view class="alert-btn" @tap="showAlertsDialog = true">
            <text class="btn-text">🔔 预警</text>
            <view v-if="alertUnreadCount > 0" class="badge">{{ alertUnreadCount > 99 ? '99+' : alertUnreadCount }}</view>
          </view>
          <view class="btn-primary" @tap="showInviteDialog = true">
            <text style="color:#fff">邀请家人</text>
          </view>
        </view>
      </view>
    </view>

    <view v-if="families.length > 1" class="card family-selector">
      <scroll-view scroll-x class="family-scroll">
        <view
          v-for="family in families"
          :key="family.id"
          class="family-item"
          :class="{ active: selectedFamily?.id === family.id }"
          @tap="selectFamily(family)"
        >
          <text>🏠 {{ family.name }}</text>
        </view>
      </scroll-view>
    </view>

    <view v-if="selectedFamily" class="stats-row flex-row gap-sm">
      <view class="stat-item card flex-col flex-center">
        <text class="stat-icon">👥</text>
        <text class="stat-value">{{ familyStats.member_count || 0 }}</text>
        <text class="stat-label">成员数</text>
      </view>
      <view class="stat-item card flex-col flex-center">
        <text class="stat-icon">🏥</text>
        <text class="stat-value">{{ familyStats.patient_count || 0 }}</text>
        <text class="stat-label">患者数</text>
      </view>
      <view class="stat-item card flex-col flex-center">
        <text class="stat-icon">💌</text>
        <text class="stat-value">{{ familyStats.encourage_count || 0 }}</text>
        <text class="stat-label">鼓励互动</text>
      </view>
      <view class="stat-item card flex-col flex-center">
        <text class="stat-icon">🎮</text>
        <text class="stat-value">{{ familyStats.training_count || 0 }}</text>
        <text class="stat-label">训练完成</text>
      </view>
    </view>

    <view class="tab-bar flex-row">
      <view
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-item"
        :class="{ active: activeTab === tab.key }"
        @tap="activeTab = tab.key"
      >
        <text>{{ tab.label }}</text>
      </view>
    </view>

    <view v-if="activeTab === 'members'" class="tab-content">
      <view v-if="members.length === 0" class="empty-state">
        <text class="empty-icon">👥</text>
        <text class="empty-text">暂无家庭成员</text>
      </view>
      <view v-for="member in members" :key="member.id" class="card member-card">
        <view class="flex-row flex-between">
          <view class="flex-row gap-sm">
            <view class="avatar" :style="{ background: getAvatarColor(member.role) }">
              <text style="color:#fff;font-size:32rpx;font-weight:600">{{ member.user_name?.[0] || '?' }}</text>
            </view>
            <view class="flex-col gap-xs">
              <text class="text-primary" style="font-weight:600">{{ member.user_name }}</text>
              <view class="flex-row gap-xs">
                <text class="tag" :class="getRoleTagClass(member.role)">{{ formatRole(member.role) }}</text>
                <text class="tag tag-info">{{ formatRelationship(member.relationship) }}</text>
              </view>
            </view>
          </view>
        </view>
        <view class="member-actions flex-row gap-sm mt-sm">
          <view class="action-btn" @tap="openEncourageDialog(member)">
            <text>💌 鼓励</text>
          </view>
          <view v-if="member.patient_id" class="action-btn" @tap="viewMemberHealth(member)">
            <text>📊 健康</text>
          </view>
          <view class="action-btn" @tap="openPrivacyDialog(member)">
            <text>🔒 隐私</text>
          </view>
        </view>
      </view>
    </view>

    <view v-if="activeTab === 'activities'" class="tab-content">
      <view v-if="activities.length === 0" class="empty-state">
        <text class="empty-icon">📋</text>
        <text class="empty-text">暂无动态</text>
      </view>
      <view v-for="activity in activities" :key="activity.id" class="card activity-card">
        <view class="flex-row gap-sm">
          <text class="activity-icon">{{ getActivityIcon(activity.activity_type) }}</text>
          <view class="flex-col gap-xs" style="flex:1">
            <text class="text-primary">{{ activity.content }}</text>
            <text class="text-hint" style="font-size:22rpx">{{ formatDateTime(activity.created_at) }}</text>
          </view>
        </view>
      </view>
    </view>

    <view v-if="activeTab === 'messages'" class="tab-content">
      <view class="flex-between mb-sm">
        <view class="flex-row gap-xs">
          <text class="section-title">关怀消息</text>
          <view v-if="unreadCount > 0" class="badge">{{ unreadCount }}</view>
        </view>
        <view class="btn-text" @tap="markAllRead"><text>全部已读</text></view>
      </view>
      <view v-if="messages.length === 0" class="empty-state">
        <text class="empty-icon">💬</text>
        <text class="empty-text">暂无消息</text>
      </view>
      <view
        v-for="msg in messages"
        :key="msg.id"
        class="card message-item"
        :class="{ unread: !msg.is_read, 'encourage-card': msg.message_type === 'encourage_card' }"
      >
        <view class="flex-row flex-between">
          <view class="flex-row gap-xs">
            <text class="text-primary" style="font-weight:600">{{ msg.from_user_name }}</text>
            <text v-if="msg.message_type === 'encourage_card'" class="tag tag-danger">鼓励卡片</text>
            <text v-else-if="msg.message_type === 'alert'" class="tag tag-warning">预警</text>
          </view>
          <text class="text-hint" style="font-size:22rpx">{{ formatDateTime(msg.created_at) }}</text>
        </view>
        <text class="mt-sm text-secondary">{{ msg.content }}</text>
      </view>
    </view>

    <view v-if="activeTab === 'health'" class="tab-content">
      <view v-if="!selectedMember" class="empty-state">
        <text class="empty-icon">📊</text>
        <text class="empty-text">请在成员列表中点击「📊 健康」查看</text>
      </view>
      <view v-else class="health-section">
        <view class="flex-between mb-md">
          <text class="section-title">{{ selectedMember.user_name }} 的健康状况</text>
          <view class="btn-text" @tap="selectedMember = null; healthSummary = null"><text>关闭</text></view>
        </view>
        <view v-if="healthSummary" class="flex-row gap-sm" style="flex-wrap:wrap">
          <view class="health-metric card" style="flex:1;min-width:200rpx">
            <text style="font-weight:600">🩸 血糖趋势</text>
            <text class="trend" :class="getTrendClass(healthSummary.trends?.blood_sugar?.trend)">
              {{ formatTrend(healthSummary.trends?.blood_sugar?.trend) }}
            </text>
            <text class="text-hint" style="font-size:24rpx">平均: {{ healthSummary.trends?.blood_sugar?.avg_value || '-' }}</text>
          </view>
          <view class="health-metric card" style="flex:1;min-width:200rpx">
            <text style="font-weight:600">💓 血压趋势</text>
            <text class="trend" :class="getTrendClass(healthSummary.trends?.blood_pressure?.trend)">
              {{ formatTrend(healthSummary.trends?.blood_pressure?.trend) }}
            </text>
            <text class="text-hint" style="font-size:24rpx">平均: {{ healthSummary.trends?.blood_pressure?.avg_value || '-' }}</text>
          </view>
          <view class="health-metric card" style="flex:1;min-width:200rpx">
            <text style="font-weight:600">💊 用药依从性</text>
            <text class="compliance-value">{{ healthSummary.medication_compliance?.compliance_rate || 0 }}%</text>
            <view class="compliance-bar">
              <view
                class="compliance-fill"
                :style="{
                  width: (healthSummary.medication_compliance?.compliance_rate || 0) + '%',
                  background: getComplianceColor(healthSummary.medication_compliance?.compliance_rate || 0)
                }"
              />
            </view>
          </view>
        </view>
        <view v-if="healthSummary?.alerts?.length > 0" class="card mt-md">
          <text class="section-title">⚠️ 异常预警</text>
          <view v-for="alert in healthSummary.alerts" :key="alert.title" class="alert-row">
            <view class="flex-row gap-xs">
              <text class="tag" :class="getAlertTagClass(alert.severity)">{{ alert.severity }}</text>
              <text class="text-primary" style="font-weight:600">{{ alert.title }}</text>
            </view>
            <text class="text-secondary mt-sm" style="font-size:24rpx">{{ alert.content }}</text>
          </view>
        </view>
      </view>
    </view>

    <view v-if="showEncourageDialog" class="dialog-mask" @tap="showEncourageDialog = false">
      <view class="dialog-content" @tap.stop>
        <text class="dialog-title">发送鼓励</text>
        <text class="mb-md text-secondary">给 {{ encourageTarget?.user_name }} 发送鼓励</text>
        <view class="encourage-grid">
          <view
            v-for="card in encourageCards"
            :key="card.id"
            class="encourage-card-item"
            :class="{ selected: selectedCardId === card.id }"
            @tap="selectedCardId = card.id"
          >
            <text class="card-icon">{{ card.icon }}</text>
            <text class="card-name">{{ card.name }}</text>
            <text class="card-content">{{ card.content }}</text>
          </view>
        </view>
        <view class="flex-row gap-sm mt-md" style="justify-content:flex-end">
          <view class="btn-secondary" @tap="showEncourageDialog = false"><text>取消</text></view>
          <view class="btn-primary" :class="{ disabled: !selectedCardId }" @tap="sendEncourage"><text style="color:#fff">发送鼓励</text></view>
        </view>
      </view>
    </view>

    <view v-if="showInviteDialog" class="dialog-mask" @tap="showInviteDialog = false">
      <view class="dialog-content" @tap.stop>
        <text class="dialog-title">邀请家人</text>
        <view v-if="!selectedFamily" class="empty-state">
          <text class="empty-text">请先选择一个家庭</text>
        </view>
        <view v-else>
          <view class="form-item">
            <text class="form-label">关系</text>
            <picker :range="relationshipOptions" range-key="label" @change="onInviteRelationshipChange">
              <view class="input-field">{{ inviteForm.relationshipLabel }}</view>
            </picker>
          </view>
          <view class="form-item">
            <text class="form-label">有效期</text>
            <picker :range="expiresOptions" range-key="label" @change="onInviteExpiresChange">
              <view class="input-field">{{ inviteForm.expiresLabel }}</view>
            </picker>
          </view>
          <view v-if="inviteCode" class="invite-result mt-md">
            <view class="card" style="background:rgba(91,140,90,0.1)">
              <text class="text-primary" style="font-weight:600">邀请码已生成</text>
              <view class="flex-row flex-between mt-sm">
                <text class="invite-code">{{ inviteCode }}</text>
                <view class="btn-primary" @tap="copyInviteCode"><text style="color:#fff">复制</text></view>
              </view>
              <text class="text-hint mt-sm" style="font-size:22rpx">将此邀请码分享给家人，对方输入即可加入</text>
            </view>
          </view>
        </view>
        <view class="flex-row gap-sm mt-md" style="justify-content:flex-end">
          <view class="btn-secondary" @tap="showInviteDialog = false; inviteCode = ''"><text>关闭</text></view>
          <view class="btn-primary" :class="{ disabled: !selectedFamily }" @tap="createInvite"><text style="color:#fff">生成邀请码</text></view>
        </view>
      </view>
    </view>

    <view v-if="privacyDialogVisible" class="dialog-mask" @tap="privacyDialogVisible = false">
      <view class="dialog-content" @tap.stop>
        <text class="dialog-title">隐私设置</text>
        <text class="mb-md text-secondary">控制 {{ privacyTarget?.user_name }} 可以查看的内容</text>
        <view class="privacy-list">
          <view class="privacy-item flex-row flex-between">
            <text class="text-primary">查看健康数据</text>
            <switch :checked="privacySettings.can_view_health" @change="privacySettings.can_view_health = $event.detail.value" color="var(--color-primary)" />
          </view>
          <view class="privacy-item flex-row flex-between">
            <text class="text-primary">查看用药记录</text>
            <switch :checked="privacySettings.can_view_medication" @change="privacySettings.can_view_medication = $event.detail.value" color="var(--color-primary)" />
          </view>
          <view class="privacy-item flex-row flex-between">
            <text class="text-primary">查看认知评估</text>
            <switch :checked="privacySettings.can_view_cognitive" @change="privacySettings.can_view_cognitive = $event.detail.value" color="var(--color-primary)" />
          </view>
          <view class="privacy-item flex-row flex-between">
            <text class="text-primary">查看训练进度</text>
            <switch :checked="privacySettings.can_view_training" @change="privacySettings.can_view_training = $event.detail.value" color="var(--color-primary)" />
          </view>
          <view class="privacy-item flex-row flex-between">
            <text class="text-primary">发送鼓励</text>
            <switch :checked="privacySettings.can_send_encourage" @change="privacySettings.can_send_encourage = $event.detail.value" color="var(--color-primary)" />
          </view>
          <view class="privacy-item flex-row flex-between">
            <text class="text-primary">接收预警通知</text>
            <switch :checked="privacySettings.can_receive_alerts" @change="privacySettings.can_receive_alerts = $event.detail.value" color="var(--color-primary)" />
          </view>
        </view>
        <view class="flex-row gap-sm mt-md" style="justify-content:flex-end">
          <view class="btn-secondary" @tap="privacyDialogVisible = false"><text>取消</text></view>
          <view class="btn-primary" @tap="savePrivacySettings"><text style="color:#fff">保存</text></view>
        </view>
      </view>
    </view>

    <view v-if="showAlertsDialog" class="dialog-mask" @tap="showAlertsDialog = false">
      <view class="dialog-content" @tap.stop>
        <text class="dialog-title">预警通知</text>
        <view v-if="memberAlerts.length === 0" class="empty-state">
          <text class="empty-icon">🔔</text>
          <text class="empty-text">暂无预警通知</text>
        </view>
        <scroll-view scroll-y style="max-height:600rpx">
          <view v-for="alert in memberAlerts" :key="alert.id" class="card alert-item" :class="{ unread: !alert.is_read }">
            <view class="flex-row flex-between">
              <view class="flex-row gap-xs">
                <text class="tag" :class="getAlertTagClass(alert.severity)">{{ alert.patient_name }}</text>
              </view>
              <text class="text-hint" style="font-size:22rpx">{{ formatDateTime(alert.created_at) }}</text>
            </view>
            <text class="text-primary mt-sm" style="font-weight:600">{{ alert.alert_title }}</text>
            <text class="text-secondary mt-sm" style="font-size:24rpx">{{ alert.alert_content }}</text>
            <view v-if="!alert.is_read" class="btn-text mt-sm" @tap="markAlertRead(alert)">
              <text>标记已读</text>
            </view>
          </view>
        </scroll-view>
        <view class="flex-row gap-sm mt-md" style="justify-content:flex-end">
          <view class="btn-secondary" @tap="showAlertsDialog = false"><text>关闭</text></view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/utils/api'

const authStore = useAuthStore()
const userId = computed(() => authStore.userInfo?.id || '')
const userName = computed(() => authStore.userInfo?.name || authStore.userInfo?.username || '用户')

const families = ref<any[]>([])
const selectedFamily = ref<any>(null)
const members = ref<any[]>([])
const selectedMember = ref<any>(null)
const healthSummary = ref<any>(null)
const messages = ref<any[]>([])
const unreadCount = ref(0)
const activities = ref<any[]>([])
const familyStats = ref<any>({})
const encourageCards = ref<any[]>([])
const memberAlerts = ref<any[]>([])
const alertUnreadCount = ref(0)

const activeTab = ref('members')
const showInviteDialog = ref(false)
const showAlertsDialog = ref(false)
const showEncourageDialog = ref(false)
const privacyDialogVisible = ref(false)

const inviteCode = ref('')
const encourageTarget = ref<any>(null)
const selectedCardId = ref<string | null>(null)
const privacyTarget = ref<any>(null)
const privacySettings = ref({
  can_view_health: true,
  can_view_medication: true,
  can_view_cognitive: false,
  can_view_training: false,
  can_send_encourage: true,
  can_receive_alerts: true,
})

const tabs = [
  { key: 'members', label: '成员' },
  { key: 'activities', label: '动态' },
  { key: 'messages', label: '消息' },
  { key: 'health', label: '健康' },
]

const relationshipOptions = [
  { value: 'child', label: '子女' },
  { value: 'spouse', label: '配偶' },
  { value: 'parent', label: '父母' },
  { value: 'other', label: '其他' },
]

const expiresOptions = [
  { value: 24, label: '24小时' },
  { value: 72, label: '72小时' },
  { value: 168, label: '7天' },
]

const inviteForm = ref({
  relationship: 'child',
  relationshipLabel: '子女',
  expiresHours: 72,
  expiresLabel: '72小时',
})

const ROLE_MAP: Record<string, string> = { owner: '创建者', parent: '父母', child: '子女', spouse: '配偶', member: '成员', other: '其他' }
const RELATIONSHIP_MAP: Record<string, string> = {
  father: '爸爸', mother: '妈妈', son: '儿子', daughter: '女儿',
  husband: '丈夫', wife: '妻子', grandfather: '爷爷', grandmother: '奶奶',
  brother: '兄弟', sister: '姐妹', self: '本人', other: '其他',
}

const formatRole = (role: string) => ROLE_MAP[role] || role
const formatRelationship = (rel: string) => RELATIONSHIP_MAP[rel] || rel

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

const formatTrend = (trend: string) => {
  const map: Record<string, string> = { falling: '↓ 下降', rising: '↑ 上升', stable: '→ 稳定' }
  return map[trend] || '暂无数据'
}

const getRoleTagClass = (role: string) => {
  const map: Record<string, string> = { owner: 'tag-danger', parent: 'tag-warning', child: 'tag-success', spouse: 'tag-primary' }
  return map[role] || 'tag-info'
}

const getAvatarColor = (role: string) => {
  const map: Record<string, string> = { owner: '#f56c6c', parent: '#e6a23c', child: '#67c23a', spouse: '#409eff' }
  return map[role] || '#909399'
}

const getTrendClass = (trend: string) => {
  if (trend === 'falling') return 'good'
  if (trend === 'rising') return 'bad'
  return 'normal'
}

const getComplianceColor = (rate: number) => {
  if (rate >= 80) return '#67c23a'
  if (rate >= 60) return '#e6a23c'
  return '#f56c6c'
}

const getAlertTagClass = (severity: string) => {
  const map: Record<string, string> = { low: 'tag-info', medium: 'tag-warning', high: 'tag-danger', urgent: 'tag-danger' }
  return map[severity] || 'tag-info'
}

const getActivityIcon = (type: string) => {
  const map: Record<string, string> = { encourage_sent: '💌', training_completed: '🎮', medication_taken: '💊', health_improved: '📈', member_joined: '👋' }
  return map[type] || '📌'
}

const onInviteRelationshipChange = (e: any) => {
  const idx = e.detail.value
  inviteForm.value.relationship = relationshipOptions[idx].value
  inviteForm.value.relationshipLabel = relationshipOptions[idx].label
}

const onInviteExpiresChange = (e: any) => {
  const idx = e.detail.value
  inviteForm.value.expiresHours = expiresOptions[idx].value
  inviteForm.value.expiresLabel = expiresOptions[idx].label
}

const loadFamilies = async () => {
  try {
    const res: any = await api.get('/family/my-families')
    families.value = res.families || []
    if (families.value.length > 0 && !selectedFamily.value) {
      await selectFamily(families.value[0])
    }
  } catch (e) {
    console.error('加载家庭失败', e)
  }
}

const selectFamily = async (family: any) => {
  selectedFamily.value = family
  await Promise.all([
    loadMembers(family.id),
    loadMessages(),
    loadActivities(family.id),
    loadFamilyStats(family.id),
  ])
}

const loadMembers = async (familyId: string) => {
  try {
    const res: any = await api.get(`/family/${familyId}/members`)
    members.value = res.members || []
  } catch (e) {
    console.error('加载成员失败', e)
  }
}

const loadActivities = async (familyId: string) => {
  try {
    const res: any = await api.get(`/family/${familyId}/activities?limit=30`)
    activities.value = res.activities || []
  } catch (e) {
    console.error('加载动态失败', e)
  }
}

const loadFamilyStats = async (familyId: string) => {
  try {
    const res: any = await api.get(`/family/${familyId}/stats`)
    familyStats.value = res.stats || {}
  } catch (e) {
    console.error('加载统计失败', e)
  }
}

const loadMessages = async () => {
  if (!userId.value) return
  try {
    const res: any = await api.get(`/family/message/${userId.value}/unread`)
    messages.value = res.messages || []
    unreadCount.value = messages.value.length
  } catch (e) {
    console.error('加载消息失败', e)
  }
}

const loadEncourageCards = async () => {
  try {
    const res: any = await api.get('/family/encourage-cards')
    encourageCards.value = res.cards || []
  } catch (e) {
    console.error('加载鼓励卡片失败', e)
  }
}

const loadMemberAlerts = async () => {
  if (!userId.value) return
  try {
    const res: any = await api.get(`/family/alerts/${userId.value}?unread_only=true`)
    memberAlerts.value = res.alerts || []
    alertUnreadCount.value = res.unread_count || 0
  } catch (e) {
    console.error('加载预警失败', e)
  }
}

const viewMemberHealth = async (member: any) => {
  if (!member.patient_id) return
  selectedMember.value = member
  activeTab.value = 'health'
  try {
    const res: any = await api.get(`/family/patient/${member.patient_id}/health-summary`)
    healthSummary.value = res.summary
  } catch (e) {
    console.error('加载健康数据失败', e)
  }
}

const openEncourageDialog = async (member: any) => {
  encourageTarget.value = member
  selectedCardId.value = null
  await loadEncourageCards()
  showEncourageDialog.value = true
}

const sendEncourage = async () => {
  if (!selectedCardId.value || !encourageTarget.value || !selectedFamily.value) return
  try {
    const res: any = await api.post('/family/encourage-card/send', {
      family_id: selectedFamily.value.id,
      from_user_id: userId.value,
      from_user_name: userName.value,
      to_user_id: encourageTarget.value.user_id,
      to_user_name: encourageTarget.value.user_name,
      card_id: selectedCardId.value,
    })
    if (res.success) {
      uni.showToast({ title: '鼓励已发送！', icon: 'success' })
      showEncourageDialog.value = false
      if (selectedFamily.value) {
        await loadActivities(selectedFamily.value.id)
        await loadFamilyStats(selectedFamily.value.id)
      }
    }
  } catch (e) {
    uni.showToast({ title: '发送失败', icon: 'none' })
  }
}

const createInvite = async () => {
  if (!selectedFamily.value) return
  try {
    const res: any = await api.post('/family/invite/create', {
      family_id: selectedFamily.value.id,
      inviter_id: userId.value,
      inviter_name: userName.value,
      relationship: inviteForm.value.relationship,
      expires_hours: inviteForm.value.expiresHours,
    })
    if (res.success) {
      inviteCode.value = res.invite.invite_code
    }
  } catch (e) {
    uni.showToast({ title: '生成邀请码失败', icon: 'none' })
  }
}

const copyInviteCode = () => {
  uni.setClipboardData({
    data: inviteCode.value,
    success: () => uni.showToast({ title: '已复制到剪贴板', icon: 'success' }),
  })
}

const openPrivacyDialog = async (member: any) => {
  privacyTarget.value = member
  if (selectedFamily.value) {
    try {
      const res: any = await api.get(`/family/${selectedFamily.value.id}/privacy/${member.user_id}`)
      if (res.success && res.settings) {
        privacySettings.value = { ...privacySettings.value, ...res.settings }
      }
    } catch (e) {
      console.error('加载隐私设置失败', e)
    }
  }
  privacyDialogVisible.value = true
}

const savePrivacySettings = async () => {
  if (!selectedFamily.value || !privacyTarget.value) return
  try {
    const res: any = await api.put(`/family/${selectedFamily.value.id}/privacy/${privacyTarget.value.user_id}`, {
      family_id: selectedFamily.value.id,
      user_id: privacyTarget.value.user_id,
      ...privacySettings.value,
    })
    if (res.success) {
      uni.showToast({ title: '隐私设置已更新', icon: 'success' })
      privacyDialogVisible.value = false
    }
  } catch (e) {
    uni.showToast({ title: '保存失败', icon: 'none' })
  }
}

const markAllRead = async () => {
  for (const msg of messages.value.filter(m => !m.is_read)) {
    try {
      await api.post(`/family/message/${msg.id}/read`)
    } catch (_) { /* ignore */ }
  }
  await loadMessages()
}

const markAlertRead = async (alert: any) => {
  try {
    await api.post(`/family/alerts/${alert.id}/read`)
    alert.is_read = true
    alertUnreadCount.value = Math.max(0, alertUnreadCount.value - 1)
  } catch (e) {
    console.error('标记已读失败', e)
  }
}

onMounted(async () => {
  await loadFamilies()
  await loadMemberAlerts()
})
</script>

<style scoped>
.header-card {
  padding: var(--spacing-md);
}

.header-title {
  font-size: 36rpx;
  font-weight: 700;
  color: var(--color-text-primary);
}

.alert-btn {
  position: relative;
  padding: 12rpx 24rpx;
}

.badge {
  position: absolute;
  top: -8rpx;
  right: -8rpx;
  background: var(--color-danger);
  color: #fff;
  font-size: 20rpx;
  min-width: 32rpx;
  height: 32rpx;
  line-height: 32rpx;
  text-align: center;
  border-radius: 16rpx;
  padding: 0 8rpx;
}

.family-selector {
  padding: var(--spacing-sm);
}

.family-scroll {
  white-space: nowrap;
}

.family-item {
  display: inline-block;
  padding: 12rpx 24rpx;
  margin-right: var(--spacing-sm);
  border-radius: var(--radius-md);
  font-size: 26rpx;
  color: var(--color-text-secondary);
  background: var(--color-bg-page);
}

.family-item.active {
  background: var(--color-primary);
  color: #fff;
}

.stats-row {
  margin-bottom: var(--spacing-md);
}

.stat-item {
  flex: 1;
  padding: var(--spacing-sm);
  text-align: center;
}

.stat-icon {
  font-size: 36rpx;
}

.stat-value {
  font-size: 36rpx;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-top: 4rpx;
}

.stat-label {
  font-size: 22rpx;
  color: var(--color-text-hint);
  margin-top: 4rpx;
}

.tab-bar {
  background: var(--color-bg-card);
  border-radius: var(--radius-md);
  padding: 4rpx;
  margin-bottom: var(--spacing-md);
}

.tab-item {
  flex: 1;
  text-align: center;
  padding: 16rpx 0;
  font-size: 26rpx;
  color: var(--color-text-secondary);
  border-radius: var(--radius-sm);
}

.tab-item.active {
  background: var(--color-primary);
  color: #fff;
  font-weight: 600;
}

.tab-content {
  min-height: 400rpx;
}

.member-card {
  padding: var(--spacing-md);
}

.avatar {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.member-actions {
  padding-top: var(--spacing-sm);
  border-top: 2rpx solid var(--color-border);
}

.action-btn {
  padding: 8rpx 20rpx;
  border-radius: var(--radius-sm);
  background: var(--color-bg-page);
  font-size: 24rpx;
  color: var(--color-primary);
}

.activity-card {
  padding: var(--spacing-sm) var(--spacing-md);
}

.activity-icon {
  font-size: 36rpx;
}

.message-item {
  padding: var(--spacing-md);
}

.message-item.unread {
  background: rgba(100, 181, 246, 0.05);
  border-left: 6rpx solid var(--color-info);
}

.message-item.encourage-card {
  background: rgba(229, 115, 115, 0.05);
  border-left: 6rpx solid var(--color-danger);
}

.health-metric {
  padding: var(--spacing-md);
  text-align: center;
}

.trend {
  font-size: 32rpx;
  font-weight: 700;
  margin-top: 8rpx;
  display: block;
}

.trend.good { color: var(--color-success); }
.trend.bad { color: var(--color-danger); }
.trend.normal { color: var(--color-info); }

.compliance-value {
  font-size: 40rpx;
  font-weight: 700;
  color: var(--color-success);
  margin-top: 8rpx;
  display: block;
}

.compliance-bar {
  height: 12rpx;
  background: var(--color-bg-page);
  border-radius: 6rpx;
  margin-top: 8rpx;
  overflow: hidden;
}

.compliance-fill {
  height: 100%;
  border-radius: 6rpx;
  transition: width 0.3s;
}

.alert-row {
  padding: var(--spacing-sm) 0;
  border-bottom: 2rpx solid var(--color-border);
}

.alert-row:last-child {
  border-bottom: none;
}

.dialog-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 999;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dialog-content {
  width: 90%;
  max-height: 80vh;
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  overflow-y: auto;
}

.dialog-title {
  font-size: 34rpx;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-md);
  display: block;
}

.encourage-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.encourage-card-item {
  width: calc(50% - 10rpx);
  padding: 20rpx;
  border: 2rpx solid var(--color-border);
  border-radius: var(--radius-md);
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4rpx;
}

.encourage-card-item.selected {
  border-color: var(--color-primary);
  background: rgba(91, 140, 90, 0.1);
}

.card-icon {
  font-size: 40rpx;
}

.card-name {
  font-size: 24rpx;
  font-weight: 600;
  color: var(--color-text-primary);
}

.card-content {
  font-size: 20rpx;
  color: var(--color-text-hint);
}

.form-item {
  margin-bottom: var(--spacing-md);
}

.form-label {
  font-size: 26rpx;
  color: var(--color-text-secondary);
  margin-bottom: 8rpx;
  display: block;
}

.invite-code {
  font-size: 40rpx;
  font-weight: 700;
  letter-spacing: 4rpx;
  color: var(--color-primary);
}

.privacy-list {
  border-top: 2rpx solid var(--color-border);
}

.privacy-item {
  padding: var(--spacing-sm) 0;
  border-bottom: 2rpx solid var(--color-border);
}

.alert-item.unread {
  background: rgba(255, 183, 77, 0.05);
  border-left: 6rpx solid var(--color-warning);
}

.btn-primary.disabled {
  opacity: 0.5;
}
</style>
