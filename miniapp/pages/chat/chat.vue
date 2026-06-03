<template>
  <view class="page">
    <!-- 页面头部 -->
    <view class="page-header">
      <!-- 返回按钮 (有会话时显示) -->
      <view class="header-left" v-if="sessionId" @click="goBack">
        <text class="back-icon">‹</text>
        <text class="back-text">返回</text>
      </view>
      <view class="header-left" v-else>
        <text class="page-title">AI咨询</text>
      </view>

      <!-- 新建对话按钮 -->
      <view class="header-right" @click="createNewChat">
        <text class="header-icon">✚</text>
        <text class="header-text">新建对话</text>
      </view>
    </view>

    <!-- 无会话时显示历史列表 -->
    <view class="history-section" v-if="!sessionId && sessionList.length > 0">
      <view class="history-title">
        <text>历史会话 ({{ sessionList.length }}条)</text>
      </view>
      <scroll-view scroll-y class="history-list">
        <view v-for="session in sessionList" :key="session.id" class="history-item" @click="switchSession(session)">
          <view class="history-item-content">
            <text class="history-item-title">{{ session.title || '新对话' }}</text>
            <text class="history-item-meta">{{ formatSessionDate(session.updated_at) }} · {{ session.message_count
            }}条</text>
          </view>
          <view class="history-item-arrow">›</view>
        </view>
      </scroll-view>
      <view class="history-start" @click="createNewChat">
        <text>开始新对话</text>
      </view>
    </view>

    <!-- 无会话且无历史时 -->
    <view class="empty-section" v-if="!sessionId && sessionList.length === 0">
      <view class="empty-icon">💬</view>
      <view class="empty-title">欢迎使用康伴AI助手</view>
      <view class="empty-desc">我可以帮您管理慢性疾病，提供专业健康咨询</view>
      <view class="empty-start" @click="createNewChat">
        <text>开始对话</text>
      </view>
    </view>

    <!-- 有会话时显示聊天界面 -->
    <view v-else class="chat-container">
      <!-- 模式选择 -->
      <view class="mode-selector">
        <view class="mode-tabs">
          <view v-for="(mode, idx) in modeOptions" :key="mode.value"
            :class="['mode-tab', { active: chatMode === mode.value }]" @click="switchMode(mode.value)">
            <text class="mode-icon">{{ mode.icon }}</text>
            <text class="mode-name">{{ mode.name }}</text>
          </view>
        </view>
      </view>

      <!-- Agent 选择 (单Agent模式显示) -->
      <view class="agent-selector" v-if="chatMode === 'single'">
        <view class="agent-tip">
          <text class="tip-icon">🤖</text>
          <text class="tip-text">选择一位专家为您提供专业建议</text>
        </view>
        <scroll-view scroll-x class="agent-scroll">
          <view class="agent-list">
            <view v-for="agent in agents" :key="agent.type"
              :class="['agent-chip', { active: currentAgent?.type === agent.type }]"
              :style="{ '--agent-color': agent.color }" @click="selectAgent(agent)">
              <text class="agent-emoji">{{ agent.emoji }}</text>
              <text class="agent-name">{{ agent.name }}</text>
            </view>
          </view>
        </scroll-view>
      </view>

      <!-- 多Agent选择提示 -->
      <view class="multi-agent-tip" v-if="chatMode !== 'single'">
        <text class="tip-icon">🤝</text>
        <text class="tip-text">{{ chatMode === 'multi' ? '多专家同时为您会诊' : '多位专家轮询讨论' }}</text>
      </view>

      <!-- 消息列表 -->
      <scroll-view scroll-y class="messages-scroll" :scroll-into-view="scrollIntoView" @scrolltolower="loadMoreHistory">
        <!-- 欢迎消息 -->
        <view class="welcome-msg" v-if="messages.length === 0">
          <text class="welcome-emoji">🏥</text>
          <text class="welcome-title">欢迎使用康伴AI助手</text>
          <text class="welcome-desc">我可以帮您管理慢性疾病，提供专业健康咨询</text>

          <!-- 快捷问题 -->
          <view class="quick-questions">
            <view v-for="q in quickQuestions" :key="q" class="quick-question" @click="sendQuickQuestion(q)">
              {{ q }}
            </view>
          </view>
        </view>

        <!-- 消息组 -->
        <view class="message-group" v-for="(msg, index) in messages" :key="index">
          <!-- 用户消息 -->
          <view v-if="msg.role === 'user'" class="message-item user">
            <view class="message-content">
              <text class="msg-text">{{ msg.content }}</text>
            </view>
          </view>

          <!-- AI消息 -->
          <view v-else class="message-item assistant">
            <view class="msg-content">
              <!-- Agent 标签 -->
              <view class="msg-agent-tag" v-if="msg.agentType">
                <view class="tag-dot" :style="{ background: getAgentColor(msg.agentType) }"></view>
                <text class="tag-name">{{ getAgentName(msg.agentType) }}</text>
              </view>

              <!-- 思考过程/多Agent结果 -->
              <view class="thinking-section" v-if="msg.thinking">
                <view class="thinking-header" @click="toggleThinking(index)">
                  <text class="thinking-icon">{{ msg.thinking.expanded ? '▼' : '▶' }}</text>
                  <text class="thinking-title">
                    {{ msg.thinking.type === 'multi' ? '🤝 多专家会诊' : '💬 专家讨论' }}
                  </text>
                  <text class="thinking-count">{{ msg.thinking.agents?.length || 0 }}位</text>
                </view>

                <!-- 展开内容 -->
                <view class="thinking-body" v-if="msg.thinking.expanded">
                  <!-- 多Agent模式 -->
                  <view v-if="msg.thinking.type === 'multi'" class="multi-agents">
                    <view v-for="(agent, aIdx) in msg.thinking.agents" :key="aIdx" class="agent-card">
                      <view class="agent-header">
                        <text class="agent-emoji">{{ getAgentEmoji(agent.agent_type) }}</text>
                        <text class="agent-name">{{ agent.agent_name }}</text>
                      </view>
                      <view class="agent-response">
                        <rich-text class="response-text" :nodes="parseMarkdown(agent.response)"></rich-text>
                      </view>
                    </view>
                  </view>

                  <!-- 对话模式 -->
                  <view v-if="msg.thinking.type === 'dialogue'" class="dialogue-turns">
                    <view v-for="(turn, tIdx) in msg.thinking.agents" :key="tIdx" class="turn-item">
                      <view class="turn-header">
                        <text class="turn-emoji">{{ getAgentEmoji(turn.agent_type) }}</text>
                        <text class="turn-name">{{ turn.agent_name }}</text>
                        <text class="turn-badge" v-if="turn.turn_index > 0">第{{ turn.turn_index + 1 }}轮</text>
                      </view>
                      <view class="turn-content">
                        <rich-text class="response-text" :nodes="parseMarkdown(turn.response)"></rich-text>
                      </view>
                    </view>
                  </view>

                  <!-- 综合建议 -->
                  <view class="summary-section" v-if="msg.thinking.summary">
                    <view class="summary-label">📋 综合建议</view>
                    <rich-text class="summary-text" :nodes="parseMarkdown(msg.thinking.summary)"></rich-text>
                  </view>
                </view>
              </view>

              <!-- 最终回复 -->
              <view class="final-response">
                <rich-text class="msg-text" :nodes="parseMarkdown(msg.content)"></rich-text>
              </view>

              <!-- 消息时间 -->
              <view class="msg-time" v-if="msg.timestamp">
                <text class="time-text">{{ formatMessageTime(msg.timestamp) }}</text>
              </view>

              <!-- 操作按钮 -->
              <view class="msg-actions" v-if="index === messages.length - 1">
                <view class="action-item" @click="copyMessage(msg.content)">
                  <text class="action-icon">📋</text>
                </view>
                <view class="action-item" @click="goToSimulation">
                  <text class="action-icon">🎯</text>
                </view>
                <view class="action-item" @click="likeMessage(index)">
                  <text class="action-icon">{{ msg.liked ? '👍' : '👍' }}</text>
                </view>
                <view class="action-item" @click="dislikeMessage(index)">
                  <text class="action-icon">👎</text>
                </view>
              </view>
            </view>
          </view>
        </view>

        <!-- 加载中 -->
        <view class="loading-msg" v-if="loading">
          <view class="loading-spinner"></view>
          <text class="loading-text">AI思考中...</text>
        </view>

        <!-- 加载更多 -->
        <view class="load-more" v-if="hasMoreHistory && !loadingMore" @click="loadMoreHistory">
          <text>点击加载更多历史</text>
        </view>
      </scroll-view>

      <!-- 输入区域 (有会话时显示) -->
      <view class="input-area">
        <view class="input-wrapper">
          <textarea class="input" v-model="inputText" placeholder="描述您的症状或问题..." placeholder-class="input-placeholder"
            :auto-height="true" :adjust-position="true" :show-confirm-bar="false" :cursor-spacing="20" :maxlength="500"
            @focus="onInputFocus" @blur="onInputBlur" @confirm="sendMessage" />
        </view>
        <button class="btn-send" :class="{ 'btn-disabled': loading || !inputText.trim() }"
          :disabled="loading || !inputText.trim()" @click="sendMessage">
          <text v-if="!loading">发送</text>
          <text v-else>...</text>
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { onShow, onLoad } from '@dcloudio/uni-app'
import { chatApi, multiAgentApi } from '@/utils/api'

const BASE_URL = 'http://localhost:8000/api/v1'

let pageSessionId = ''
let pageMode = 'single'

onLoad((query: any) => {
  console.log('[onLoad] query:', query)
  if (query.sessionId) {
    pageSessionId = query.sessionId
  }
  if (query.mode) {
    pageMode = query.mode
  }
})

interface Agent {
  type: string
  name: string
  emoji: string
  color: string
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  agentType?: string
  timestamp?: string
  liked?: boolean
  thinking?: {
    type: 'multi' | 'dialogue'
    expanded: boolean
    agents: Array<{
      agent_type: string
      agent_name: string
      response: string
      sources?: any[]
      turn_index: number
    }>
    summary?: string
  }
  regenHistory?: Array<{ index: number; content: string }>
}

interface ChatSession {
  id: string
  patient_id: string
  agent_type: string
  title: string
  status: string
  message_count: number
  created_at: string
  updated_at: string
}

const agents = ref<Agent[]>([])
const currentAgent = ref<Agent | null>(null)
const messages = ref<Message[]>([])
const inputText = ref('')
const loading = ref(false)
const scrollIntoView = ref('')
const sessionId = ref('')
const page = ref(1)
const hasMoreHistory = ref(false)
const loadingMore = ref(false)
const modeIndex = ref(0)

const saveSessionId = (id: string) => {
  if (id) {
    sessionId.value = id
    uni.setStorageSync('current_session_id', id)
  }
}

// 会话历史相关
const sessionList = ref<ChatSession[]>([])
const showSessionPanel = ref(false)
const loadingSessions = ref(false)

const modeOptions = [
  { name: '单Agent', icon: '🤖', value: 'single' },
  { name: '多Agent会诊', icon: '🤝', value: 'multi' },
  { name: '专家对话', icon: '💬', value: 'dialogue' }
]
const chatMode = ref<'single' | 'multi' | 'dialogue'>('single')

const quickQuestions = [
  '如果我坚持运动，血糖会降多少？',
  '调整饮食能让血压恢复正常吗？',
  '药物+运动效果会不会更好？',
  '我的指标多久能看到改善？'
]

onMounted(async () => {
  console.log('[onMounted] Start, sessionId:', sessionId.value, 'pageSessionId:', pageSessionId, 'pageMode:', pageMode)
  loadAgents()
  await loadSessions()

  if (pageSessionId) {
    console.log('[onMounted] Using pageSessionId:', pageSessionId)
    sessionId.value = pageSessionId
    chatMode.value = pageMode as 'single' | 'multi' | 'dialogue'
    await loadHistory()
    pageSessionId = ''
    pageMode = 'single'
  } else {
    await restoreSession()
  }
  console.log('[onMounted] End, sessionId:', sessionId.value, 'chatMode:', chatMode.value)
})

onShow(async () => {
  await loadSessions()
  await restoreSession()
})

const restoreSession = async () => {
  const savedSessionId = uni.getStorageSync('current_session_id')
  console.log('[restoreSession] savedSessionId:', savedSessionId)
  console.log('[restoreSession] sessionList length:', sessionList.value.length)
  if (savedSessionId) {
    const session = sessionList.value.find(s => s.id === savedSessionId)
    console.log('[restoreSession] found session:', session)
    if (session) {
      sessionId.value = savedSessionId
      await loadHistory()
    } else {
      console.log('[restoreSession] session not found, removing savedSessionId')
      uni.removeStorageSync('current_session_id')
    }
  }
}

// 加载会话列表
const loadSessions = async () => {
  loadingSessions.value = true
  try {
    const token = uni.getStorageSync('token')
    console.log('[loadSessions] Token exists:', !!token)
    const res = await chatApi.getSessions(undefined, 50)
    console.log('[loadSessions] Full response object:', res)
    console.log('[loadSessions] res.sessions type:', typeof res.sessions, Array.isArray(res.sessions))
    console.log('[loadSessions] res.sessions length:', res.sessions?.length)
    if (res.sessions && res.sessions.length > 0) {
      console.log('[loadSessions] First session:', JSON.stringify(res.sessions[0]))
    }
    sessionList.value = (res.sessions || []).sort((a: any, b: any) => {
      return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    })
    console.log('[loadSessions] After sort, sessionList length:', sessionList.value.length)
    console.log('[loadSessions] sessionId:', sessionId.value, '!sessionId:', !sessionId.value)
  } catch (e) {
    console.error('Load sessions failed:', e)
  } finally {
    loadingSessions.value = false
  }
}

// 创建新会话
const createNewChat = async () => {
  try {
    const res = await chatApi.createSession()
    saveSessionId(res.session_id)
    messages.value = []
    await loadSessions()
  } catch (e) {
    console.error('Create failed:', e)
    uni.showToast({ title: '创建失败', icon: 'none' })
  }
}

// 切换会话
const switchSession = (session: any) => {
  saveSessionId(session.id)
  loadHistory()
}

// 删除会话
const deleteSession = async (session: ChatSession, event: Event) => {
  event.stopPropagation()

  uni.showModal({
    title: '确认删除',
    content: '确定要删除这个会话吗？',
    success: async (res) => {
      if (res.confirm) {
        try {
          await chatApi.deleteSession(session.id)
          // 从列表中移除
          const index = sessionList.value.findIndex(s => s.id === session.id)
          if (index > -1) {
            sessionList.value.splice(index, 1)
          }
          // 如果删除的是当前会话，清空消息
          if (sessionId.value === session.id) {
            sessionId.value = ''
            messages.value = []
            uni.removeStorageSync('current_session_id')
          }
          uni.showToast({ title: '已删除', icon: 'success' })
        } catch (e) {
          console.error('Delete session failed:', e)
          uni.showToast({ title: '删除失败', icon: 'none' })
        }
      }
    }
  })
}

// 格式化会话时间
const formatSessionDate = (dateStr: string): string => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) {
    const hours = date.getHours().toString().padStart(2, '0')
    const minutes = date.getMinutes().toString().padStart(2, '0')
    return `${hours}:${minutes}`
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return `${days}天前`
  } else {
    const month = (date.getMonth() + 1).toString().padStart(2, '0')
    const day = date.getDate().toString().padStart(2, '0')
    return `${month}/${day}`
  }
}

// 返回
const goBack = () => {
  sessionId.value = ''
  messages.value = []
  uni.removeStorageSync('current_session_id')
  loadSessions()
}

const loadHistory = async () => {
  if (!sessionId.value) return

  loading.value = true
  try {
    const res = await chatApi.getHistory(sessionId.value)
    if (res.messages && Array.isArray(res.messages)) {
      messages.value = res.messages.map((msg: any) => ({
        role: msg.role,
        content: msg.content,
        agentType: msg.agent_type,
        timestamp: msg.timestamp,
        liked: false
      }))

      // 滚动到底部
      scrollToBottom()

      uni.showToast({
        title: `已加载${messages.value.length}条消息`,
        icon: 'none',
        duration: 1500
      })
    }
  } catch (e) {
    console.error('Load history failed:', e)
    uni.showToast({
      title: '加载历史失败',
      icon: 'none'
    })
  } finally {
    loading.value = false
  }
}

const loadAgents = async () => {
  try {
    const res = await chatApi.getAgents()
    if (res.agents && Array.isArray(res.agents)) {
      agents.value = res.agents.map((agent: any) => ({
        type: agent.type || agent.agent_type,
        name: agent.name || agent.agent_name,
        emoji: agent.emoji || getAgentEmojiByType(agent.type || agent.agent_type),
        color: agent.color || getAgentColorByType(agent.type || agent.agent_type)
      }))
      if (agents.value.length > 0) {
        currentAgent.value = agents.value[0]
      }
    }
  } catch (e) {
    console.error('Load agents failed:', e)
    // 使用默认agents
    agents.value = [
      { type: 'diabetes', name: '糖尿病专家', emoji: '👨‍⚕️', color: '#5E8B5A' },
      { type: 'nutrition', name: '营养专家', emoji: '🥗', color: '#7BA7B9' },
      { type: 'exercise', name: '运动专家', emoji: '🏃', color: '#E6A23C' },
      { type: 'cardiology', name: '心血管专家', emoji: '❤️', color: '#F56C6C' }
    ]
    currentAgent.value = agents.value[0]
  }
}

const getAgentEmojiByType = (type: string): string => {
  const emojiMap: Record<string, string> = {
    diabetes: '👨‍⚕️',
    nutrition: '🥗',
    exercise: '🏃',
    cardiology: '❤️',
    general: '🤖'
  }
  return emojiMap[type] || '🤖'
}

const getAgentColorByType = (type: string): string => {
  const colorMap: Record<string, string> = {
    diabetes: '#5E8B5A',
    nutrition: '#7BA7B9',
    exercise: '#E6A23C',
    cardiology: '#F56C6C',
    general: '#909399'
  }
  return colorMap[type] || '#909399'
}

const formatMessageTime = (timestamp: string): string => {
  if (!timestamp) return ''

  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  // 小于1分钟
  if (diff < 60000) {
    return '刚刚'
  }

  // 小于1小时
  if (diff < 3600000) {
    const minutes = Math.floor(diff / 60000)
    return `${minutes}分钟前`
  }

  // 今天
  if (date.toDateString() === now.toDateString()) {
    const hours = date.getHours().toString().padStart(2, '0')
    const minutes = date.getMinutes().toString().padStart(2, '0')
    return `${hours}:${minutes}`
  }

  // 昨天
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  if (date.toDateString() === yesterday.toDateString()) {
    const hours = date.getHours().toString().padStart(2, '0')
    const minutes = date.getMinutes().toString().padStart(2, '0')
    return `昨天 ${hours}:${minutes}`
  }

  // 其他日期
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const day = date.getDate().toString().padStart(2, '0')
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return `${month}/${day} ${hours}:${minutes}`
}

const switchMode = (mode: string) => {
  chatMode.value = mode as 'single' | 'multi' | 'dialogue'
}

const selectAgent = (agent: Agent) => {
  currentAgent.value = agent
}

const onInputFocus = () => {
  // 聚焦时可调整输入框
}

const onInputBlur = () => {
  // 失焦时重置
}

const formatResponse = (text: string): string => {
  if (!text) return ''
  // 简单格式化：处理换行和列表
  return text.trim()
}

const getAgentColor = (type: string): string => {
  const agent = agents.value.find(a => a.type === type)
  return agent?.color || 'var(--color-primary)'
}

const likeMessage = (index: number) => {
  const msg = messages.value[index]
  if (msg) {
    msg.liked = !msg.liked
  }
  uni.showToast({ title: msg.liked ? '已赞' : '取消点赞', icon: 'none' })
}

const dislikeMessage = (index: number) => {
  uni.showToast({ title: '感谢反馈', icon: 'none' })
}

const updateSessionTitle = async (firstMessage: string) => {
  if (!sessionId.value) return

  try {
    // 生成标题：取前20个字符，如果超过则加省略号
    let title = firstMessage.trim()
    if (title.length > 20) {
      title = title.substring(0, 20) + '...'
    }

    // 调用API更新会话标题
    await chatApi.updateSessionTitle(sessionId.value, title)
  } catch (e) {
    console.error('Update session title failed:', e)
  }
}

const sendMessage = async () => {
  if (!inputText.value.trim() || loading.value) return

  const content = inputText.value
  const isFirstMessage = messages.value.length === 0

  // 如果没有会话ID，先创建会话
  if (!sessionId.value) {
    try {
      const res = await chatApi.createSession()
      saveSessionId(res.session_id)
    } catch (e) {
      console.error('Create session failed:', e)
      uni.showToast({ title: '创建会话失败', icon: 'none' })
      return
    }
  }

  messages.value.push({ role: 'user', content: content })
  inputText.value = ''
  loading.value = true
  scrollToBottom()

  // 如果是第一条消息且会话已创建，更新会话标题
  if (isFirstMessage && sessionId.value) {
    try {
      let title = content.trim()
      if (title.length > 20) {
        title = title.substring(0, 20) + '...'
      }
      await chatApi.updateSessionTitle(sessionId.value, title)

      // 更新本地会话列表中的标题
      const session = sessionList.value.find(s => s.id === sessionId.value)
      if (session) {
        session.title = title
        session.message_count = 0
      }
    } catch (e) {
      console.log('Update title failed:', e)
    }
  }

  try {
    let res: any

    if (chatMode.value === 'dialogue') {
      try {
        res = await multiAgentApi.consultation({
          message: content,
          session_id: sessionId.value || undefined,
          patient_id: undefined
        })

        if (res.session_id) {
          saveSessionId(res.session_id)
        }

        const thinkingAgents = res.individual_results?.map((r: any) => ({
          agent_type: r.agent_type,
          agent_name: getAgentName(r.agent_type),
          response: r.response,
          turn_index: 0
        })) || []

        messages.value.push({
          role: 'assistant',
          content: res.summary || (thinkingAgents.length > 0 ? '已收到多位专家的建议，请点击展开查看。' : 'AI正在思考中...'),
          agentType: 'dialogue',
          thinking: {
            type: 'dialogue',
            expanded: false,
            agents: thinkingAgents,
            summary: res.summary
          }
        })
      } catch (e: any) {
        console.error('Dialogue failed:', e)
        uni.showToast({ title: '请求失败，请重试', icon: 'none' })
      }
    } else if (chatMode.value === 'multi') {
      // 多Agent会诊
      res = await multiAgentApi.consultation({
        message: content,
        session_id: sessionId.value || undefined,
        patient_id: undefined
      })

      if (res.session_id) {
        saveSessionId(res.session_id)
      }

      const thinkingAgents = res.individual_results?.map((r: any) => ({
        agent_type: r.agent_type,
        agent_name: getAgentName(r.agent_type),
        response: r.response,
        turn_index: 0
      })) || []

      messages.value.push({
        role: 'assistant',
        content: res.summary || res.individual_results?.map((r: any) => `【${getAgentName(r.agent_type)}】${r.response}`).join('\n\n') || '',
        agentType: 'multi',
        thinking: {
          type: 'multi',
          expanded: false,
          agents: thinkingAgents,
          summary: res.summary
        }
      })
    } else {
      // 单Agent模式
      res = await chatApi.sendMessage({
        session_id: sessionId.value,
        message: content,
        agent_type: currentAgent.value?.type,
        use_rag: true
      })

      if (res.session_id) {
        saveSessionId(res.session_id)
      }

      messages.value.push({
        role: 'assistant',
        content: res.message,
        agentType: res.agent_type
      })

      // 更新会话消息数
      if (sessionId.value) {
        const session = sessionList.value.find(s => s.id === sessionId.value)
        if (session) {
          session.message_count = messages.value.length
        }
      }
    }
  } catch (e) {
    console.error('Send message failed:', e)
    messages.value.push({
      role: 'assistant',
      content: '抱歉，服务暂时不可用，请稍后重试。'
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

const sendQuickQuestion = (question: string) => {
  inputText.value = question
  sendMessage()
}

const toggleThinking = (index: number) => {
  const msg = messages.value[index]
  if (msg.thinking) {
    msg.thinking.expanded = !msg.thinking.expanded
    nextTick(() => scrollToBottom())
  }
}

const copyMessage = (content: string) => {
  uni.setClipboardData({
    data: content.replace(/<[^>]*>/g, ''),
    success: () => {
      uni.showToast({ title: '已复制', icon: 'success' })
    }
  })
}

const regenerateMsg = async () => {
  if (messages.value.length < 2) return
  const lastUserMsg = messages.value[messages.value.length - 2]
  messages.value.pop()
  messages.value.pop()
  inputText.value = lastUserMsg.content
  sendMessage()
}

const goToSimulation = () => {
  uni.navigateTo({ url: '/pages/simulation/simulation' })
}

const getShortResponse = (response: string): string => {
  if (!response) return ''
  // 截取前100个字符
  if (response.length > 100) {
    return response.substring(0, 100) + '...'
  }
  return response
}

const loadMoreHistory = async () => {
  if (loadingMore.value || !hasMoreHistory.value) return
  loadingMore.value = true
  page.value++
  // 实现加载更多历史...
  loadingMore.value = false
}

const scrollToBottom = () => {
  nextTick(() => {
    const index = messages.value.length - 1
    scrollIntoView.value = `msg-${index}`
  })
}

const getAgentEmoji = (type?: string): string => {
  if (!type) return '🤖'
  const agent = agents.value.find(a => a.type === type)
  return agent?.emoji || '🤖'
}

const getAgentName = (type?: string): string => {
  if (!type) return 'AI'
  const agent = agents.value.find(a => a.type === type)
  return agent?.name || type
}

const parseMarkdown = (content: string): string => {
  if (!content) return ''
  let html = content

  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>')
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>')
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>')
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
  html = html.replace(/`(.+?)`/g, '<code style="background:#FCF8F0;padding:2rpx 8rpx;border-radius:4rpx;font-family:monospace;">$1</code>')
  html = html.replace(/^\* (.+)$/gm, '<li>$1</li>')
  html = html.replace(/\n/g, '<br>')

  return html
}
</script>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--color-bg-page);
}

.mode-selector {
  position: sticky;
  top: 0;
  z-index: 10;
  background: #FFFFFF;
  padding: 16rpx 30rpx;
  border-bottom: 1rpx solid var(--color-border-light);
}

.mode-tabs {
  display: flex;
  gap: 12rpx;
}

.mode-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6rpx;
  padding: 10rpx 8rpx;
  background: var(--color-bg-card);
  border-radius: 12rpx;
  border: 1rpx solid transparent;
  transition: all 0.3s;
}

.mode-tab.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
}

.mode-tab .mode-icon {
  font-size: 26rpx;
}

.mode-tab .mode-name {
  font-size: 22rpx;
  color: var(--color-text-secondary);
}

.mode-tab.active .mode-name {
  color: var(--color-text-inverse);
}

/* Agent选择器 */
.agent-selector {
  position: sticky;
  top: 88rpx;
  z-index: 9;
  background: #FFFFFF;
  padding: 12rpx 0;
  border-bottom: 1rpx solid var(--color-border-light);
}

.agent-tip {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
  padding: 8rpx 30rpx 12rpx;
  font-size: 24rpx;
}

.agent-tip .tip-icon {
  font-size: 28rpx;
}

.agent-tip .tip-text {
  color: var(--color-text-secondary);
}

.agent-scroll {
  white-space: nowrap;
  padding: 0 30rpx;
}

.agent-list {
  display: inline-flex;
  gap: 16rpx;
}

.agent-chip {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 10rpx 20rpx;
  background: var(--color-bg-card);
  border-radius: 16rpx;
  border: 1rpx solid var(--color-border-light);
}

.agent-chip.active {
  border-color: var(--agent-color, var(--color-primary));
  background: var(--color-bg-card-light);
}

.agent-chip .agent-emoji {
  font-size: 32rpx;
}

.agent-chip .agent-name {
  font-size: 24rpx;
  color: var(--color-text-secondary);
}

.agent-chip.active .agent-name {
  color: var(--agent-color, var(--color-primary));
  font-weight: 500;
}

/* 多Agent提示 */
.multi-agent-tip {
  position: sticky;
  top: 88rpx;
  z-index: 9;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
  padding: 12rpx 30rpx;
  background: var(--color-bg-card);
  font-size: 24rpx;
}

.tip-icon {
  font-size: 28rpx;
}

.tip-text {
  color: var(--color-text-secondary);
}

.messages-scroll {
  flex: 1;
  padding: 20rpx 30rpx;
}

.welcome-msg {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60rpx 0;
}

.welcome-emoji {
  font-size: 100rpx;
  margin-bottom: 30rpx;
}

.welcome-title {
  font-size: 32rpx;
  font-weight: bold;
  color: var(--color-text-primary);
  margin-bottom: 16rpx;
}

.welcome-desc {
  font-size: 26rpx;
  color: var(--color-text-secondary);
  text-align: center;
  padding: 0 40rpx;
  margin-bottom: 40rpx;
  line-height: 1.5;
}

.quick-questions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 16rpx;
  padding: 0 20rpx;
}

.quick-question {
  padding: 16rpx 24rpx;
  background: var(--color-bg-card);
  border-radius: 16rpx;
  font-size: 24rpx;
  color: var(--color-primary);
  border: 1rpx solid var(--color-border-light);
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
}

.message-item {
  display: flex;
  margin-bottom: 30rpx;
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-item.user .message-content {
  background: var(--color-primary);
  color: var(--color-text-inverse);
  padding: 16rpx 24rpx;
  border-radius: 16rpx;
  max-width: 75%;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.1);
}

.message-group {
  margin-bottom: 20rpx;
}

.msg-agent-tag {
  display: flex;
  align-items: center;
  gap: 8rpx;
  margin-bottom: 12rpx;
}

.tag-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
}

.tag-name {
  font-size: 22rpx;
  font-weight: 500;
}

/* 多Agent卡片 */
.multi-agents {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.agent-card {
  padding: 16rpx;
  background: var(--color-bg-card);
  border-radius: 12rpx;
  border-left: 4rpx solid var(--color-primary);
}

.agent-card .agent-header {
  display: flex;
  align-items: center;
  gap: 8rpx;
  margin-bottom: 10rpx;
}

.agent-card .agent-emoji {
  font-size: 28rpx;
}

.agent-card .agent-name {
  font-size: 24rpx;
  font-weight: 500;
  color: var(--color-text-primary);
}

.agent-card .agent-response {
  padding-left: 36rpx;
}

.agent-card .response-text {
  font-size: 24rpx;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

/* 对话轮次 */
.dialogue-turns {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.turn-item {
  padding: 16rpx;
  background: #fff;
  border-radius: 10rpx;
}

.turn-header {
  display: flex;
  align-items: center;
  gap: 10rpx;
  margin-bottom: 10rpx;
}

.turn-emoji {
  font-size: 28rpx;
}

.turn-name {
  font-size: 24rpx;
  font-weight: 500;
  color: var(--color-text-primary);
}

.turn-badge {
  font-size: 20rpx;
  padding: 4rpx 10rpx;
  background: #f0f0f0;
  color: var(--color-text-secondary);
  border-radius: 8rpx;
}

/* 综合建议 */
.summary-section {
  margin-top: 16rpx;
  padding: 16rpx;
  background: #fff8e6;
  border-radius: 10rpx;
}

.summary-label {
  font-size: 24rpx;
  font-weight: 500;
  color: #e6a23c;
  margin-bottom: 8rpx;
}

.summary-text {
  font-size: 24rpx;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.final-response {
  margin-top: 16rpx;
  padding-top: 16rpx;
  border-top: 1rpx dashed #eee;
}

/* 消息时间 */
.msg-time {
  display: flex;
  justify-content: flex-end;
  margin-top: 12rpx;
}

.time-text {
  font-size: 22rpx;
  color: var(--color-text-secondary);
  opacity: 0.7;
}

/* 操作按钮 */
.msg-actions {
  display: flex;
  justify-content: flex-end;
  gap: 20rpx;
  margin-top: 16rpx;
  padding-top: 16rpx;
  border-top: 1rpx solid var(--color-border-light);
}

.action-item {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 60rpx;
  height: 60rpx;
  border-radius: 50%;
  background: var(--color-bg-card);
  transition: all 0.3s;
}

.action-item:active {
  background: var(--color-bg-hover);
  transform: scale(0.95);
}

.action-icon {
  font-size: 32rpx;
}

.action-label {
  font-size: 20rpx;
  color: var(--color-text-secondary);
}

/* 加载动画 */
.loading-spinner {
  width: 40rpx;
  height: 40rpx;
  border: 4rpx solid #f0f0f0;
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 16rpx;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.msg-avatar {
  font-size: 50rpx;
  margin: 0 15rpx;
}

.msg-content {
  max-width: 75%;
  padding: 20rpx;
  border-radius: 15rpx;
}

.message-item.user .msg-content {
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
  color: var(--color-text-inverse);
}

.message-item.assistant .msg-content {
  background: #fff;
  box-shadow: 0 2rpx 10rpx rgba(0, 0, 0, 0.1);
}

.msg-agent-tag {
  display: inline-block;
  font-size: 22rpx;
  color: var(--color-primary);
  margin-bottom: 8rpx;
  padding: 4rpx 12rpx;
  background: #ecf5ff;
  border-radius: 8rpx;
}

.msg-text {
  font-size: 28rpx;
  line-height: 1.6;
  white-space: pre-wrap;
}

.thinking-section {
  background: #f8f9fa;
  border-radius: 10rpx;
  margin-bottom: 16rpx;
  overflow: hidden;
}

.thinking-header {
  display: flex;
  align-items: center;
  padding: 16rpx 20rpx;
  background: #e8f4fd;
  cursor: pointer;
}

.thinking-icon {
  font-size: 24rpx;
  margin-right: 12rpx;
  color: var(--color-primary);
}

.thinking-title {
  font-size: 24rpx;
  color: var(--color-primary);
  font-weight: 500;
}

.thinking-count {
  font-size: 22rpx;
  color: var(--color-text-secondary);
  margin-left: auto;
}

.thinking-body {
  padding: 20rpx;
}

.thinking-agent {
  margin-bottom: 20rpx;
  padding-bottom: 16rpx;
  border-bottom: 1rpx solid #eee;
}

.thinking-agent:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.agent-header {
  display: flex;
  align-items: center;
  margin-bottom: 8rpx;
}

.agent-emoji-small {
  font-size: 28rpx;
  margin-right: 8rpx;
}

.agent-name-small {
  font-size: 24rpx;
  color: var(--color-text-primary);
  font-weight: 500;
}

.agent-response {
  padding-left: 36rpx;
}

.response-text {
  font-size: 24rpx;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.response-loading {
  color: var(--color-text-secondary);
  font-style: italic;
}

.summary-section {
  background: #fff8e6;
  border-radius: 10rpx;
  padding: 20rpx;
  margin-top: 16rpx;
}

.summary-header {
  font-size: 26rpx;
  color: #e6a23c;
  font-weight: 500;
  margin-bottom: 12rpx;
}

.summary-content {
  font-size: 26rpx;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.msg-actions {
  display: flex;
  gap: 20rpx;
  margin-top: 12rpx;
  padding-top: 12rpx;
  border-top: 1rpx solid #eee;
}

.action-btn {
  display: flex;
  align-items: center;
  font-size: 22rpx;
  color: var(--color-text-secondary);
}

.action-text {
  margin-left: 6rpx;
}

.quick-actions {
  display: flex;
  gap: 16rpx;
  margin-top: 16rpx;
  padding-top: 16rpx;
  border-top: 1rpx solid #eee;
}

.quick-btn {
  display: flex;
  align-items: center;
  gap: 6rpx;
  padding: 10rpx 20rpx;
  background: var(--color-bg-hover);
  border-radius: 30rpx;
  font-size: 24rpx;
  color: var(--color-primary);
}

.loading-msg {
  text-align: center;
  padding: 30rpx;
}

.loading-dots {
  font-size: 28rpx;
  color: var(--color-text-secondary);
  margin-bottom: 16rpx;
}

.typing-indicator {
  display: flex;
  justify-content: center;
  gap: 8rpx;
}

.dot {
  width: 12rpx;
  height: 12rpx;
  background: var(--color-primary);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) {
  animation-delay: -0.32s;
}

.dot:nth-child(2) {
  animation-delay: -0.16s;
}

.dot:nth-child(3) {
  animation-delay: 0s;
}

@keyframes bounce {

  0%,
  80%,
  100% {
    transform: scale(0);
  }

  40% {
    transform: scale(1);
  }
}

.load-more {
  text-align: center;
  padding: 20rpx;
  color: var(--color-primary);
  font-size: 26rpx;
}

.input-area {
  display: flex;
  align-items: flex-end;
  gap: 16rpx;
  padding: 16rpx 30rpx;
  background: #fff;
  border-top: 1rpx solid var(--color-border-light);
}

.input-wrapper {
  flex: 1;
  background: var(--color-bg-card);
  border-radius: 20rpx;
  padding: 14rpx 20rpx;
  box-sizing: border-box;
  border: 1rpx solid var(--color-border-light);
}

.input {
  width: 100%;
  font-size: 28rpx;
  line-height: 40rpx;
  min-height: 40rpx;
  color: var(--color-text-primary);
}

.input-placeholder {
  color: var(--color-text-secondary);
}

.btn-send {
  background: var(--color-primary);
  color: var(--color-text-inverse);
  font-size: 28rpx;
  padding: 0 32rpx;
  height: 68rpx;
  line-height: 68rpx;
  border-radius: 16rpx;
  border: none;
  flex-shrink: 0;
  font-weight: 500;
}

.btn-disabled {
  background: var(--color-border);
}

.btn-send[disabled] {
  background: var(--color-border);
}

/* 顶部栏 */
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16rpx 30rpx;
  background: #fff;
  border-bottom: 1rpx solid var(--color-border-light);
}

.new-chat-btn {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 12rpx 24rpx;
  background: var(--color-primary);
  border-radius: 40rpx;
}

.new-chat-btn .btn-icon {
  font-size: 28rpx;
  color: var(--color-text-inverse);
}

.new-chat-btn .btn-text {
  font-size: 26rpx;
  color: var(--color-text-inverse);
}

.session-list-btn {
  width: 72rpx;
  height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-card);
  border-radius: 16rpx;
  border: 1rpx solid var(--color-border-light);
}

.session-list-btn .btn-icon {
  font-size: 36rpx;
}

/* 会话历史面板 */
.session-panel-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 100;
}

.session-panel {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 80%;
  max-width: 600rpx;
  background: var(--color-bg-card);
  display: flex;
  flex-direction: column;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    transform: translateX(-100%);
  }

  to {
    transform: translateX(0);
  }
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 30rpx;
  border-bottom: 1rpx solid var(--color-border-light);
}

.panel-title {
  font-size: 32rpx;
  font-weight: bold;
  color: var(--color-text-primary);
}

.panel-close {
  width: 60rpx;
  height: 60rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
  color: var(--color-text-secondary);
}

.session-list {
  flex: 1;
}

.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 30rpx;
  border-bottom: 1rpx solid var(--color-border-light);
}

.session-item.active {
  background: var(--color-bg-hover);
}

.session-info {
  flex: 1;
  overflow: hidden;
}

.session-title {
  display: block;
  font-size: 28rpx;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 8rpx;
}

.session-meta {
  font-size: 22rpx;
  color: var(--color-text-secondary);
}

.session-delete {
  width: 60rpx;
  height: 60rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.6;
}

.session-delete:active {
  opacity: 1;
}

.session-empty {
  padding: 60rpx 30rpx;
  text-align: center;
  color: var(--color-text-secondary);
  font-size: 26rpx;
}

.panel-footer {
  padding: 20rpx 30rpx;
  border-top: 1rpx solid var(--color-border-light);
}

.new-btn {
  width: 100%;
  padding: 24rpx;
  background: var(--color-primary);
  border-radius: 16rpx;
  text-align: center;
}

.new-btn text {
  color: var(--color-text-inverse);
  font-size: 28rpx;
}

/* 页面头部 */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 30rpx;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
}

.header-left {
  display: flex;
  align-items: center;
}

.back-icon {
  font-size: 44rpx;
  color: var(--color-text-inverse);
  margin-right: 4rpx;
}

.back-text {
  font-size: 30rpx;
  color: var(--color-text-inverse);
}

.page-title {
  font-size: 36rpx;
  font-weight: bold;
  color: var(--color-text-inverse);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 12rpx 20rpx;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 30rpx;
}

.header-icon {
  font-size: 28rpx;
}

.header-text {
  font-size: 26rpx;
  color: var(--color-text-inverse);
}

/* 历史列表区域 */
.history-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 30rpx;
  background: var(--color-bg-page);
}

.history-title {
  font-size: 32rpx;
  font-weight: bold;
  color: var(--color-text-primary);
  margin-bottom: 20rpx;
}

.history-list {
  flex: 1;
  background: var(--color-bg-card);
  border-radius: 16rpx;
}

.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 30rpx;
  border-bottom: 1rpx solid var(--color-border-light);
}

.history-item:last-child {
  border-bottom: none;
}

.history-item:active {
  background: var(--color-bg-hover);
}

.history-item-content {
  flex: 1;
  overflow: hidden;
}

.history-item-title {
  display: block;
  font-size: 28rpx;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 8rpx;
}

.history-item-meta {
  font-size: 22rpx;
  color: var(--color-text-secondary);
}

.history-item-arrow {
  font-size: 32rpx;
  color: var(--color-text-secondary);
  margin-left: 20rpx;
}

.history-start {
  margin-top: 30rpx;
  padding: 30rpx;
  background: var(--color-primary);
  border-radius: 16rpx;
  text-align: center;
}

.history-start text {
  color: var(--color-text-inverse);
  font-size: 30rpx;
  font-weight: 500;
}

/* 空状态区域 */
.empty-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60rpx;
}

.empty-icon {
  font-size: 120rpx;
  margin-bottom: 30rpx;
}

.empty-title {
  font-size: 36rpx;
  font-weight: bold;
  color: var(--color-text-primary);
  margin-bottom: 16rpx;
}

.empty-desc {
  font-size: 26rpx;
  color: var(--color-text-secondary);
  text-align: center;
  line-height: 1.5;
  margin-bottom: 60rpx;
}

.empty-start {
  padding: 24rpx 80rpx;
  background: var(--color-primary);
  border-radius: 40rpx;
}

.empty-start text {
  color: var(--color-text-inverse);
  font-size: 30rpx;
  font-weight: 500;
}

/* 聊天容器 */
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
}
</style>
