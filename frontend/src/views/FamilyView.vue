<template>
  <div class="family-container">
    <el-card class="header-card">
      <div class="header-content">
        <div class="header-left">
          <h2>❤️ 家庭关爱圈</h2>
          <p>家人一起，守护健康</p>
        </div>
        <div class="header-right">
          <el-badge :value="alertUnreadCount" :hidden="alertUnreadCount === 0" :max="99">
            <el-button @click="showAlertsDialog = true" :icon="Bell">预警通知</el-button>
          </el-badge>
          <el-button type="primary" @click="showInviteDialog = true" :icon="Plus">邀请家人</el-button>
        </div>
      </div>
    </el-card>

    <el-row :gutter="20" class="main-row">
      <el-col :span="6">
        <el-card class="family-list-card">
          <template #header>
            <div class="card-header">
              <span>我的家庭</span>
              <el-button type="primary" size="small" @click="showCreateDialog = true">创建</el-button>
            </div>
          </template>
          <div v-if="families.length === 0" class="empty-state">
            <el-empty description="暂无家庭" :image-size="60" />
            <el-button type="primary" size="small" @click="showCreateDialog = true">创建第一个家庭</el-button>
          </div>
          <div
            v-for="family in families"
            :key="family.id"
            class="family-item"
            :class="{ active: selectedFamily?.id === family.id }"
            @click="selectFamily(family)"
          >
            <el-icon :size="28" color="#409EFF"><House /></el-icon>
            <div class="family-item-info">
              <h4>{{ family.name }}</h4>
              <span>{{ formatDate(family.created_at) }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="18">
        <div v-if="!selectedFamily" class="empty-state main-empty">
          <el-empty description="请选择一个家庭" :image-size="100" />
        </div>
        <div v-else>
          <el-row :gutter="16" class="stats-row">
            <el-col :span="6">
              <el-card class="stat-card" shadow="hover">
                <div class="stat-icon" style="background: #e8f5e9; color: #4caf50">👥</div>
                <div class="stat-info">
                  <span class="stat-value">{{ familyStats.member_count || 0 }}</span>
                  <span class="stat-label">家庭成员</span>
                </div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card class="stat-card" shadow="hover">
                <div class="stat-icon" style="background: #fff3e0; color: #ff9800">🏥</div>
                <div class="stat-info">
                  <span class="stat-value">{{ familyStats.patient_count || 0 }}</span>
                  <span class="stat-label">患者成员</span>
                </div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card class="stat-card" shadow="hover">
                <div class="stat-icon" style="background: #fce4ec; color: #e91e63">💌</div>
                <div class="stat-info">
                  <span class="stat-value">{{ familyStats.encourage_count || 0 }}</span>
                  <span class="stat-label">鼓励互动</span>
                </div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card class="stat-card" shadow="hover">
                <div class="stat-icon" style="background: #e3f2fd; color: #2196f3">🎮</div>
                <div class="stat-info">
                  <span class="stat-value">{{ familyStats.training_count || 0 }}</span>
                  <span class="stat-label">训练完成</span>
                </div>
              </el-card>
            </el-col>
          </el-row>

          <el-tabs v-model="activeTab" class="main-tabs">
            <el-tab-pane label="家庭成员" name="members">
              <div class="members-grid">
                <el-card v-for="member in members" :key="member.id" class="member-card" shadow="hover">
                  <div class="member-top">
                    <el-avatar :size="48" :style="{ background: getAvatarColor(member.role) }">
                      {{ member.user_name?.[0] || '?' }}
                    </el-avatar>
                    <div class="member-info">
                      <h4>{{ member.user_name }}</h4>
                      <div class="member-tags">
                        <el-tag :type="getRoleTagType(member.role)" size="small">{{ formatRole(member.role) }}</el-tag>
                        <el-tag type="info" size="small">{{ formatRelationship(member.relationship_type || member.relationship) }}</el-tag>
                      </div>
                    </div>
                  </div>
                  <div class="member-actions">
                    <el-button size="small" type="primary" text @click="showEncourageDialog(member)">
                      💌 鼓励
                    </el-button>
                    <el-button v-if="member.patient_id" size="small" type="success" text @click="viewMemberHealth(member)">
                      📊 健康
                    </el-button>
                    <el-button size="small" type="info" text @click="showPrivacyDialog(member)">
                      🔒 隐私
                    </el-button>
                    <el-button
                      v-if="isOwner && member.role !== 'owner'"
                      size="small"
                      type="danger"
                      text
                      @click="removeMember(member)"
                    >
                      移除
                    </el-button>
                  </div>
                </el-card>
                <el-card class="member-card add-member-card" shadow="hover" @click="showAddMemberDialog = true">
                  <div class="add-member-content">
                    <el-icon :size="40" color="#bbb"><Plus /></el-icon>
                    <span>添加成员</span>
                  </div>
                </el-card>
              </div>
            </el-tab-pane>

            <el-tab-pane label="家庭动态" name="activities">
              <div class="activities-timeline">
                <el-timeline v-if="activities.length > 0">
                  <el-timeline-item
                    v-for="activity in activities"
                    :key="activity.id"
                    :timestamp="formatDateTime(activity.created_at)"
                    :type="getActivityType(activity.activity_type)"
                    placement="top"
                  >
                    <el-card shadow="never" class="activity-card">
                      <div class="activity-content">
                        <span class="activity-icon">{{ getActivityIcon(activity.activity_type) }}</span>
                        <span>{{ activity.content }}</span>
                      </div>
                    </el-card>
                  </el-timeline-item>
                </el-timeline>
                <el-empty v-else description="暂无动态" :image-size="80" />
              </div>
            </el-tab-pane>

            <el-tab-pane label="关怀消息" name="messages">
              <div class="messages-section">
                <div class="messages-header">
                  <el-badge :value="unreadCount" :hidden="unreadCount === 0">
                    <span>未读消息</span>
                  </el-badge>
                  <el-button size="small" @click="markAllRead">全部已读</el-button>
                </div>
                <div v-if="messages.length === 0" class="empty-state">
                  <el-empty description="暂无消息" :image-size="60" />
                </div>
                <div v-else class="message-list">
                  <div
                    v-for="msg in messages"
                    :key="msg.id"
                    class="message-item"
                    :class="{ unread: !msg.is_read, 'encourage-card': msg.message_type === 'encourage_card' }"
                  >
                    <div class="message-header">
                      <span class="sender">{{ msg.from_user_name }}</span>
                      <el-tag v-if="msg.message_type === 'encourage_card'" type="danger" size="small">鼓励卡片</el-tag>
                      <el-tag v-else-if="msg.message_type === 'alert'" type="warning" size="small">预警</el-tag>
                      <span class="time">{{ formatDateTime(msg.created_at) }}</span>
                    </div>
                    <div class="message-content">{{ msg.content }}</div>
                  </div>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane label="健康查看" name="health">
              <div v-if="!selectedMember" class="empty-state">
                <el-empty description="请在成员列表中点击「📊 健康」查看" :image-size="80" />
              </div>
              <div v-else class="health-section">
                <div class="health-header">
                  <h3>{{ selectedMember.user_name }} 的健康状况</h3>
                  <el-button size="small" @click="selectedMember = null; healthSummary = null">关闭</el-button>
                </div>
                <el-row :gutter="16" v-if="healthSummary">
                  <el-col :span="8">
                    <el-card shadow="hover" class="health-metric">
                      <h4>🩸 血糖趋势</h4>
                      <p class="trend" :class="getTrendClass(healthSummary.trends?.blood_sugar?.trend)">
                        {{ formatTrend(healthSummary.trends?.blood_sugar?.trend) }}
                      </p>
                      <p class="avg-value">平均: {{ healthSummary.trends?.blood_sugar?.avg_value || '-' }}</p>
                    </el-card>
                  </el-col>
                  <el-col :span="8">
                    <el-card shadow="hover" class="health-metric">
                      <h4>💓 血压趋势</h4>
                      <p class="trend" :class="getTrendClass(healthSummary.trends?.blood_pressure?.trend)">
                        {{ formatTrend(healthSummary.trends?.blood_pressure?.trend) }}
                      </p>
                      <p class="avg-value">平均: {{ healthSummary.trends?.blood_pressure?.avg_value || '-' }}</p>
                    </el-card>
                  </el-col>
                  <el-col :span="8">
                    <el-card shadow="hover" class="health-metric">
                      <h4>💊 用药依从性</h4>
                      <p class="compliance-value">{{ healthSummary.medication_compliance?.compliance_rate || 0 }}%</p>
                      <el-progress
                        :percentage="healthSummary.medication_compliance?.compliance_rate || 0"
                        :color="getComplianceColor(healthSummary.medication_compliance?.compliance_rate || 0)"
                        :stroke-width="10"
                      />
                    </el-card>
                  </el-col>
                </el-row>
                <el-card v-if="healthSummary?.alerts?.length > 0" class="alerts-card">
                  <template #header><span>⚠️ 异常预警</span></template>
                  <el-alert
                    v-for="alert in healthSummary.alerts"
                    :key="alert.title"
                    :title="alert.title"
                    :description="alert.content"
                    :type="getAlertType(alert.severity)"
                    show-icon
                    class="alert-item"
                  />
                </el-card>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </el-col>
    </el-row>

    <el-dialog v-model="showCreateDialog" title="创建家庭" width="400px">
      <el-form :model="newFamily" label-width="80px">
        <el-form-item label="家庭名称">
          <el-input v-model="newFamily.name" placeholder="如：幸福一家" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createFamily">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showAddMemberDialog" title="添加成员" width="400px">
      <el-form :model="newMember" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="newMember.user_name" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="newMember.role">
            <el-option label="父母" value="parent" />
            <el-option label="子女" value="child" />
            <el-option label="配偶" value="spouse" />
          </el-select>
        </el-form-item>
        <el-form-item label="关系">
          <el-select v-model="newMember.relationship">
            <el-option label="爸爸" value="father" />
            <el-option label="妈妈" value="mother" />
            <el-option label="儿子" value="son" />
            <el-option label="女儿" value="daughter" />
            <el-option label="丈夫" value="husband" />
            <el-option label="妻子" value="wife" />
            <el-option label="兄弟" value="brother" />
            <el-option label="姐妹" value="sister" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddMemberDialog = false">取消</el-button>
        <el-button type="primary" @click="addMember">添加</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showInviteDialog" title="邀请家人" width="450px">
      <div v-if="!selectedFamily" class="empty-state">
        <p>请先选择一个家庭</p>
      </div>
      <div v-else>
        <el-form :model="inviteForm" label-width="80px">
          <el-form-item label="关系">
            <el-select v-model="inviteForm.relationship">
              <el-option label="子女" value="child" />
              <el-option label="配偶" value="spouse" />
              <el-option label="父母" value="parent" />
              <el-option label="其他" value="other" />
            </el-select>
          </el-form-item>
          <el-form-item label="有效期">
            <el-select v-model="inviteForm.expiresHours">
              <el-option label="24小时" :value="24" />
              <el-option label="72小时" :value="72" />
              <el-option label="7天" :value="168" />
            </el-select>
          </el-form-item>
        </el-form>
        <div v-if="inviteCode" class="invite-result">
          <el-alert type="success" :closable="false" show-icon>
            <template #title>邀请码已生成</template>
            <div class="invite-code-display">
              <span class="code-text">{{ inviteCode }}</span>
              <el-button type="primary" size="small" @click="copyInviteCode">复制</el-button>
            </div>
            <p class="invite-tip">将此邀请码分享给家人，对方在「邀请家人」中输入即可加入</p>
          </el-alert>
        </div>
      </div>
      <template #footer>
        <el-button @click="showInviteDialog = false; inviteCode = ''">关闭</el-button>
        <el-button type="primary" @click="createInvite" :disabled="!selectedFamily">生成邀请码</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="encourageDialogVisible" title="发送鼓励" width="500px">
      <div v-if="encourageTarget">
        <p class="encourage-to">给 <strong>{{ encourageTarget.user_name }}</strong> 发送鼓励</p>
        <div class="encourage-cards-grid">
          <div
            v-for="card in encourageCards"
            :key="card.id"
            class="encourage-card-item"
            :class="{ selected: selectedCardId === card.id }"
            @click="selectedCardId = card.id"
          >
            <span class="card-icon">{{ card.icon }}</span>
            <span class="card-name">{{ card.name }}</span>
            <span class="card-content">{{ card.content }}</span>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="encourageDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="sendEncourage" :disabled="!selectedCardId">发送鼓励</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="privacyDialogVisible" title="隐私设置" width="500px">
      <div v-if="privacyTarget">
        <p class="privacy-desc">控制 <strong>{{ privacyTarget.user_name }}</strong> 可以查看的内容</p>
        <el-form label-width="120px">
          <el-form-item label="查看健康数据">
            <el-switch v-model="privacySettings.can_view_health" />
          </el-form-item>
          <el-form-item label="查看用药记录">
            <el-switch v-model="privacySettings.can_view_medication" />
          </el-form-item>
          <el-form-item label="查看认知评估">
            <el-switch v-model="privacySettings.can_view_cognitive" />
          </el-form-item>
          <el-form-item label="查看训练进度">
            <el-switch v-model="privacySettings.can_view_training" />
          </el-form-item>
          <el-form-item label="发送鼓励">
            <el-switch v-model="privacySettings.can_send_encourage" />
          </el-form-item>
          <el-form-item label="接收预警通知">
            <el-switch v-model="privacySettings.can_receive_alerts" />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="privacyDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="savePrivacySettings">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showAlertsDialog" title="预警通知" width="600px">
      <div v-if="memberAlerts.length === 0" class="empty-state">
        <el-empty description="暂无预警通知" :image-size="60" />
      </div>
      <div v-else class="alerts-list">
        <div
          v-for="alert in memberAlerts"
          :key="alert.id"
          class="alert-item"
          :class="{ unread: !alert.is_read }"
        >
          <div class="alert-header">
            <el-tag :type="getAlertType(alert.severity)" size="small">{{ alert.patient_name }}</el-tag>
            <span class="alert-time">{{ formatDateTime(alert.created_at) }}</span>
          </div>
          <h4>{{ alert.alert_title }}</h4>
          <p>{{ alert.alert_content }}</p>
          <el-button v-if="!alert.is_read" size="small" type="primary" text @click="markAlertRead(alert)">标记已读</el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { House, Plus, Bell } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/api'

const authStore = useAuthStore()
const userId = computed(() => authStore.userInfo?.id || '')
const userName = computed(() => authStore.userInfo?.name || authStore.userInfo?.username || '用户')

const families = ref([])
const selectedFamily = ref(null)
const members = ref([])
const selectedMember = ref(null)
const healthSummary = ref(null)
const messages = ref([])
const unreadCount = ref(0)
const activities = ref([])
const familyStats = ref({})
const encourageCards = ref([])
const memberAlerts = ref([])
const alertUnreadCount = ref(0)

const activeTab = ref('members')
const showCreateDialog = ref(false)
const showAddMemberDialog = ref(false)
const showInviteDialog = ref(false)
const showAlertsDialog = ref(false)
const encourageDialogVisible = ref(false)
const privacyDialogVisible = ref(false)

const newFamily = ref({ name: '' })
const newMember = ref({ user_name: '', role: 'child', relationship: 'son' })
const inviteForm = ref({ relationship: 'child', expiresHours: 72 })
const inviteCode = ref('')

const encourageTarget = ref(null)
const selectedCardId = ref(null)

const privacyTarget = ref(null)
const privacySettings = ref({
  can_view_health: true,
  can_view_medication: true,
  can_view_cognitive: false,
  can_view_training: false,
  can_send_encourage: true,
  can_receive_alerts: true,
})

const isOwner = computed(() => selectedFamily.value?.owner_id === userId.value)

const ROLE_MAP = { owner: '创建者', parent: '父母', child: '子女', spouse: '配偶', member: '成员', other: '其他' }
const RELATIONSHIP_MAP = {
  father: '爸爸', mother: '妈妈', son: '儿子', daughter: '女儿',
  husband: '丈夫', wife: '妻子', grandfather: '爷爷', grandmother: '奶奶',
  brother: '兄弟', sister: '姐妹', self: '本人', other: '其他',
}

const formatRole = (role) => ROLE_MAP[role] || role
const formatRelationship = (rel) => RELATIONSHIP_MAP[rel] || rel

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const formatTrend = (trend) => {
  const map = { falling: '↓ 下降', rising: '↑ 上升', stable: '→ 稳定' }
  return map[trend] || '暂无数据'
}

const getRoleTagType = (role) => {
  const types = { owner: 'danger', parent: 'warning', child: 'success', spouse: '' }
  return types[role] || 'info'
}

const getAvatarColor = (role) => {
  const colors = { owner: '#f56c6c', parent: '#e6a23c', child: '#67c23a', spouse: '#409eff' }
  return colors[role] || '#909399'
}

const getTrendClass = (trend) => {
  if (trend === 'falling') return 'good'
  if (trend === 'rising') return 'bad'
  return 'normal'
}

const getComplianceColor = (rate) => {
  if (rate >= 80) return '#67c23a'
  if (rate >= 60) return '#e6a23c'
  return '#f56c6c'
}

const getAlertType = (severity) => {
  const types = { low: 'info', medium: 'warning', high: 'error', urgent: 'error' }
  return types[severity] || 'info'
}

const getActivityType = (type) => {
  const map = { encourage_sent: 'danger', training_completed: 'primary', medication_taken: 'success', health_improved: 'success' }
  return map[type] || 'info'
}

const getActivityIcon = (type) => {
  const map = { encourage_sent: '💌', training_completed: '🎮', medication_taken: '💊', health_improved: '📈', member_joined: '👋' }
  return map[type] || '📌'
}

const loadFamilies = async () => {
  try {
    const res = await api.get('/family/my-families')
    families.value = res.families || []
    if (families.value.length > 0 && !selectedFamily.value) {
      await selectFamily(families.value[0])
    }
  } catch (e) {
    console.error('加载家庭失败', e)
  }
}

const selectFamily = async (family) => {
  selectedFamily.value = family
  await Promise.all([
    loadMembers(family.id),
    loadMessages(),
    loadActivities(family.id),
    loadFamilyStats(family.id),
  ])
}

const loadMembers = async (familyId) => {
  try {
    const res = await api.get(`/family/${familyId}/members`)
    members.value = res.members || []
  } catch (e) {
    console.error('加载成员失败', e)
  }
}

const loadActivities = async (familyId) => {
  try {
    const res = await api.get(`/family/${familyId}/activities?limit=30`)
    activities.value = res.activities || []
  } catch (e) {
    console.error('加载动态失败', e)
  }
}

const loadFamilyStats = async (familyId) => {
  try {
    const res = await api.get(`/family/${familyId}/stats`)
    familyStats.value = res.stats || {}
  } catch (e) {
    console.error('加载统计失败', e)
  }
}

const loadMessages = async () => {
  if (!userId.value) return
  try {
    const res = await api.get(`/family/message/${userId.value}/unread`)
    messages.value = res.messages || []
    unreadCount.value = messages.value.length
  } catch (e) {
    console.error('加载消息失败', e)
  }
}

const loadEncourageCards = async () => {
  try {
    const res = await api.get('/family/encourage-cards')
    encourageCards.value = res.cards || []
  } catch (e) {
    console.error('加载鼓励卡片失败', e)
  }
}

const loadMemberAlerts = async () => {
  if (!userId.value) return
  try {
    const res = await api.get(`/family/alerts/${userId.value}?unread_only=true`)
    memberAlerts.value = res.alerts || []
    alertUnreadCount.value = res.unread_count || 0
  } catch (e) {
    console.error('加载预警失败', e)
  }
}

const viewMemberHealth = async (member) => {
  if (!member.patient_id) return
  selectedMember.value = member
  activeTab.value = 'health'
  try {
    const res = await api.get(`/family/patient/${member.patient_id}/health-summary`)
    healthSummary.value = res.summary
  } catch (e) {
    console.error('加载健康数据失败', e)
  }
}

const createFamily = async () => {
  if (!newFamily.value.name) {
    ElMessage.warning('请输入家庭名称')
    return
  }
  try {
    const res = await api.post('/family/create', {
      name: newFamily.value.name,
      owner_id: userId.value,
      owner_name: userName.value,
    })
    if (res.success) {
      ElMessage.success('创建成功')
      showCreateDialog.value = false
      newFamily.value.name = ''
      await loadFamilies()
    }
  } catch (e) {
    ElMessage.error('创建失败')
  }
}

const addMember = async () => {
  if (!selectedFamily.value) {
    ElMessage.warning('请先选择家庭')
    return
  }
  try {
    const res = await api.post('/family/member/add', {
      family_id: selectedFamily.value.id,
      user_id: `user_${Date.now()}`,
      user_name: newMember.value.user_name,
      role: newMember.value.role,
      relationship: newMember.value.relationship,
    })
    if (res.success) {
      ElMessage.success('添加成功')
      showAddMemberDialog.value = false
      await loadMembers(selectedFamily.value.id)
    }
  } catch (e) {
    ElMessage.error('添加失败')
  }
}

const removeMember = async (member) => {
  try {
    await ElMessageBox.confirm(`确定要移除 ${member.user_name} 吗？`, '确认移除', { type: 'warning' })
    await api.delete(`/family/${selectedFamily.value.id}/member/${member.id}?operator_id=${userId.value}`)
    ElMessage.success('已移除')
    await loadMembers(selectedFamily.value.id)
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('移除失败')
  }
}

const createInvite = async () => {
  if (!selectedFamily.value) return
  try {
    const res = await api.post('/family/invite/create', {
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
    ElMessage.error('生成邀请码失败')
  }
}

const copyInviteCode = () => {
  navigator.clipboard.writeText(inviteCode.value).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    ElMessage.warning('复制失败，请手动复制: ' + inviteCode.value)
  })
}

const showEncourageDialog = async (member) => {
  encourageTarget.value = member
  selectedCardId.value = null
  await loadEncourageCards()
  encourageDialogVisible.value = true
}

const sendEncourage = async () => {
  if (!selectedCardId.value || !encourageTarget.value || !selectedFamily.value) return
  try {
    const res = await api.post('/family/encourage-card/send', {
      family_id: selectedFamily.value.id,
      from_user_id: userId.value,
      from_user_name: userName.value,
      to_user_id: encourageTarget.value.user_id,
      to_user_name: encourageTarget.value.user_name,
      card_id: selectedCardId.value,
    })
    if (res.success) {
      ElMessage.success('鼓励已发送！')
      encourageDialogVisible.value = false
      await loadActivities(selectedFamily.value.id)
      await loadFamilyStats(selectedFamily.value.id)
    }
  } catch (e) {
    ElMessage.error('发送失败')
  }
}

const showPrivacyDialog = async (member) => {
  privacyTarget.value = member
  if (selectedFamily.value) {
    try {
      const res = await api.get(`/family/${selectedFamily.value.id}/privacy/${member.user_id}`)
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
    const res = await api.put(`/family/${selectedFamily.value.id}/privacy/${privacyTarget.value.user_id}`, {
      family_id: selectedFamily.value.id,
      user_id: privacyTarget.value.user_id,
      ...privacySettings.value,
    })
    if (res.success) {
      ElMessage.success('隐私设置已更新')
      privacyDialogVisible.value = false
    }
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

const markAllRead = async () => {
  for (const msg of messages.value.filter(m => !m.is_read)) {
    try {
      await api.post(`/family/message/${msg.id}/read`)
    } catch (e) { /* ignore */ }
  }
  await loadMessages()
}

const markAlertRead = async (alert) => {
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
.family-container { padding: 20px; }

.header-card { margin-bottom: 20px; }
.header-content { display: flex; justify-content: space-between; align-items: center; }
.header-content h2 { margin: 0; font-size: 22px; }
.header-content p { margin: 4px 0 0; color: #999; }
.header-right { display: flex; gap: 10px; }

.main-row { min-height: 600px; }

.family-list-card { height: 100%; }
.card-header { display: flex; justify-content: space-between; align-items: center; }

.family-item {
  display: flex; align-items: center; gap: 12px;
  padding: 12px; border-radius: 8px; cursor: pointer;
  transition: all 0.2s; margin-bottom: 8px;
}
.family-item:hover { background: #f5f7fa; }
.family-item.active { background: #ecf5ff; border: 1px solid #409eff; }
.family-item-info h4 { margin: 0; font-size: 14px; }
.family-item-info span { font-size: 12px; color: #999; }

.stats-row { margin-bottom: 20px; }
.stat-card {
  display: flex; align-items: center; gap: 12px; padding: 4px 0;
}
.stat-icon { width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 22px; }
.stat-info { display: flex; flex-direction: column; }
.stat-value { font-size: 22px; font-weight: 700; color: #303133; }
.stat-label { font-size: 12px; color: #909399; }

.main-tabs :deep(.el-tabs__header) { margin-bottom: 16px; }

.members-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }
.member-card { padding: 4px; }
.member-top { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.member-info h4 { margin: 0 0 4px; font-size: 15px; }
.member-tags { display: flex; gap: 4px; }
.member-actions { display: flex; flex-wrap: wrap; gap: 4px; }

.add-member-card { cursor: pointer; min-height: 120px; display: flex; align-items: center; justify-content: center; }
.add-member-content { display: flex; flex-direction: column; align-items: center; gap: 8px; color: #bbb; }

.activities-timeline { max-height: 500px; overflow-y: auto; padding: 0 10px; }
.activity-card { padding: 4px 8px; }
.activity-content { display: flex; align-items: center; gap: 8px; }
.activity-icon { font-size: 18px; }

.messages-section { max-height: 500px; }
.messages-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.message-list { max-height: 400px; overflow-y: auto; }
.message-item { padding: 12px; border-bottom: 1px solid #f0f0f0; }
.message-item.unread { background: #f0f9ff; }
.message-item.encourage-card { background: #fef0f0; }
.message-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.sender { font-weight: 600; }
.time { color: #999; font-size: 12px; margin-left: auto; }
.message-content { font-size: 14px; line-height: 1.6; }

.health-section { padding: 0 8px; }
.health-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.health-header h3 { margin: 0; }
.health-metric { text-align: center; padding: 8px 0; }
.health-metric h4 { margin-bottom: 8px; font-size: 14px; }
.trend { font-size: 20px; font-weight: 700; }
.trend.good { color: #67c23a; }
.trend.bad { color: #f56c6c; }
.trend.normal { color: #409eff; }
.avg-value { color: #909399; font-size: 13px; margin-top: 4px; }
.compliance-value { font-size: 28px; font-weight: 700; color: #67c23a; margin-bottom: 8px; }
.alerts-card { margin-top: 16px; }
.alert-item { margin-bottom: 8px; }

.encourage-to { margin-bottom: 16px; font-size: 15px; }
.encourage-cards-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; max-height: 400px; overflow-y: auto; }
.encourage-card-item {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  padding: 14px 8px; border: 2px solid #ebeef5; border-radius: 10px;
  cursor: pointer; transition: all 0.2s; text-align: center;
}
.encourage-card-item:hover { border-color: #409eff; background: #f5f7fa; }
.encourage-card-item.selected { border-color: #409eff; background: #ecf5ff; }
.card-icon { font-size: 28px; }
.card-name { font-size: 13px; font-weight: 600; }
.card-content { font-size: 11px; color: #909399; line-height: 1.4; }

.privacy-desc { margin-bottom: 16px; }

.invite-result { margin-top: 16px; }
.invite-code-display { display: flex; align-items: center; gap: 10px; margin: 8px 0; }
.code-text { font-size: 24px; font-weight: 700; letter-spacing: 4px; color: #409eff; }
.invite-tip { font-size: 12px; color: #909399; margin-top: 4px; }

.alerts-list { max-height: 400px; overflow-y: auto; }
.alerts-list .alert-item { padding: 12px; border-bottom: 1px solid #f0f0f0; }
.alerts-list .alert-item.unread { background: #fdf6ec; }
.alerts-list .alert-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.alerts-list .alert-time { font-size: 12px; color: #999; margin-left: auto; }
.alerts-list h4 { margin: 4px 0; font-size: 14px; }
.alerts-list p { margin: 0; font-size: 13px; color: #606266; }

.empty-state { text-align: center; padding: 40px 20px; }
.main-empty { padding-top: 120px; }
</style>
