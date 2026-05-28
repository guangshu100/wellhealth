<template>
  <div class="chat-view">
    <el-container>
      <!-- 左侧历史面板 -->
      <el-aside width="240px" class="history-panel">
        <div class="history-header">
          <h3>康伴AI</h3>
          <el-button circle size="small" @click="createNewChat" title="新建对话">
            <el-icon><Plus /></el-icon>
          </el-button>
        </div>
        
        <el-scrollbar>
          <div class="history-list">
            <div
              v-for="session in sessionList"
              :key="session.id"
              :class="['history-item', { active: agentStore.sessionId === session.id }]"
              @click="switchSession(session)"
            >
              <div class="history-title">{{ session.title || '新对话' }}</div>
              <div class="history-meta">
                {{ formatDate(session.updated_at) }} · {{ session.message_count }}条
              </div>
            </div>
            <div v-if="sessionList.length === 0" class="history-empty">
              暂无历史对话
            </div>
          </div>
        </el-scrollbar>
        
        <!-- 患者信息 -->
        <div class="patient-card" v-if="patientStore.currentPatient">
          <div class="patient-avatar">
            <el-icon><User /></el-icon>
          </div>
          <div class="patient-info">
            <div class="patient-name">{{ patientStore.currentPatient.name }}</div>
            <div class="patient-tags">
              <el-tag v-for="d in patientStore.currentPatient.diseases" :key="d" size="small">
                {{ d }}
              </el-tag>
            </div>
          </div>
        </div>
      </el-aside>

      <!-- 主聊天区域 -->
      <el-main class="chat-main">
        <!-- 简洁顶部 -->
        <div class="chat-topbar">
          <div class="chat-title" v-if="agentStore.currentAgent">
            <span class="agent-emoji">{{ agentStore.currentAgentEmoji }}</span>
            <span class="agent-name">{{ agentStore.currentAgent?.name }}</span>
          </div>
        </div>

        <!-- 消息区域 -->
        <div class="messages-container" ref="messagesRef">
          <!-- 欢迎消息 -->
          <div class="welcome-message" v-if="agentStore.messages.length === 0">
            <div class="welcome-icon">🏥</div>
            <div class="welcome-title">欢迎使用康伴AI助手</div>
            <div class="welcome-desc">
              我可以帮您管理慢性疾病，提供专业健康咨询
            </div>
            <div class="quick-questions">
              <el-button
                v-for="q in quickQuestions"
                :key="q"
                size="small"
                @click="sendQuickQuestion(q)"
              >
                {{ q }}
              </el-button>
            </div>
          </div>

          <!-- 消息列表 -->
          <div
            v-for="(msg, index) in agentStore.messages"
            :key="index"
            :class="['message-wrapper', msg.role]"
          >
            <!-- 用户消息 -->
            <div class="message user-message" v-if="msg.role === 'user'">
              <div class="message-content">{{ msg.content }}</div>
              <div class="message-avatar">👤</div>
            </div>

            <!-- AI消息 -->
            <div class="message assistant-message" v-else>
              <div class="message-avatar">{{ getAgentEmoji(msg.agentType) }}</div>
              <div class="message-content-wrapper">
                <div class="message-agent-tag" v-if="msg.agentType">
                  <el-tag :color="getAgentColor(msg.agentType)" effect="dark" size="small">
                    {{ getAgentName(msg.agentType) }}
                  </el-tag>
                </div>
                
                <!-- 思考过程 -->
                <div v-if="msg.thinking" class="thinking-process">
                  <div 
                    class="thinking-header" 
                    @click="toggleThinking(index)"
                    :class="{ expanded: msg.thinking.expanded }"
                  >
                    <span class="thinking-icon">{{ msg.thinking.expanded ? '▼' : '▶' }}</span>
                    <span class="thinking-title">
                      {{ msg.thinking.type === 'multi' ? '🤝 多方专家会诊' : '💬 Agent对话讨论' }}
                    </span>
                  </div>
                  <div v-if="msg.thinking.expanded" class="thinking-content">
                    <template v-if="msg.thinking.type === 'multi' && msg.thinking.agents">
                      <div 
                        v-for="agent in msg.thinking.agents" 
                        :key="agent.agent_type"
                        class="thinking-agent"
                      >
                        <div class="agent-header">
                          <span class="agent-emoji">{{ getAgentEmoji(agent.agent_type) }}</span>
                          <span class="agent-name">{{ agent.agent_name }}</span>
                        </div>
                        <div class="agent-response markdown-body" v-html="renderMarkdown(agent.response)"></div>
                      </div>
                    </template>
                    <template v-if="msg.thinking.type === 'dialogue' && msg.thinking.agents">
                      <div 
                        v-for="(agent, agentIdx) in msg.thinking.agents" 
                        :key="`${agent.turn_index}-${agent.agent_type}-${agentIdx}`"
                        class="thinking-turn"
                      >
                        <div class="turn-header">
                          <span class="turn-emoji">{{ getAgentEmoji(agent.agent_type) }}</span>
                          <span class="turn-name">{{ agent.agent_name }}</span>
                          <el-tag v-if="agent.turn_index > 0" size="small" type="info">第{{ agent.turn_index + 1 }}轮</el-tag>
                        </div>
                        <div class="turn-content markdown-body" v-html="renderMarkdown(agent.response)"></div>
                      </div>
                    </template>
                  </div>
                </div>
                
                <!-- 回复内容 -->
                <div class="message-content markdown-body" v-html="renderMarkdown(msg.content)"></div>
                
                <!-- 操作按钮 -->
                <div class="message-actions">
                  <el-button 
                    class="action-btn" 
                    text 
                    size="small" 
                    @click.stop="copyMessage(msg.content)"
                    title="复制"
                  >
                    <el-icon><CopyDocument /></el-icon>
                  </el-button>
                  <el-button 
                    v-if="index === agentStore.messages.length - 1 && msg.role === 'assistant' && !agentStore.isLoading"
                    class="action-btn" 
                    text 
                    size="small" 
                    @click.stop="regenerateMessage(index)"
                    title="重新生成"
                  >
                    <el-icon><Refresh /></el-icon>
                  </el-button>
                  <el-dropdown 
                    v-if="msg.regenHistory && msg.regenHistory.length > 0" 
                    trigger="click"
                    @command="(cmd) => switchToRegenHistory(cmd, index)"
                  >
                    <el-button class="action-btn regen-counter" text size="small">
                      <span class="regen-icon">↺</span>
                      <span class="regen-count">{{ msg.regenHistory.length + 1 }}</span>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item :command="msg.regenCurrentIndex || (msg.regenHistory.length + 1)">
                          最新版本
                        </el-dropdown-item>
                        <el-dropdown-item 
                          v-for="history in msg.regenHistory" 
                          :key="history.index" 
                          :command="history.index"
                        >
                          版本 {{ history.index }}
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                  <el-button 
                    class="action-btn" 
                    text 
                    size="small" 
                    @click.stop="likeMessage(index)"
                    title="喜欢"
                  >
                    <span class="action-icon">👍</span>
                  </el-button>
                  <el-button 
                    class="action-btn" 
                    text 
                    size="small" 
                    @click.stop="dislikeMessage(index)"
                    title="不喜欢"
                  >
                    <span class="action-icon">👎</span>
                  </el-button>
                </div>
              </div>
            </div>
          </div>

          <!-- 加载中 -->
          <div class="loading-message" v-if="agentStore.isLoading">
            <div class="loading-icon">🤔</div>
            <div class="loading-text">AI正在思考中...</div>
          </div>
        </div>

        <!-- 底部输入区域 -->
        <div class="input-area">
          <!-- 模式选择 -->
          <div class="mode-bar">
            <el-radio-group v-model="chatMode" @change="handleModeChange" size="small">
              <el-radio-button label="single">单Agent</el-radio-button>
              <el-radio-button label="multi">多Agent会诊</el-radio-button>
              <el-radio-button label="dialogue">Agent对话</el-radio-button>
            </el-radio-group>
            
            <!-- Agent选择器 -->
            <el-popover
              placement="bottom-start"
              :width="520"
              trigger="click"
              v-if="chatMode !== 'single'"
            >
              <template #reference>
                <el-button size="small" type="primary" plain>
                  {{ selectedAgentNames.length > 0 ? `已选${selectedAgentNames.length}个Agent` : '选择Agent' }}
                  <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                </el-button>
              </template>
              <div class="agent-select-panel">
                <div class="agent-select-header">
                  <el-checkbox 
                    v-model="selectAllAgents" 
                    @change="handleSelectAllAgents"
                  >
                    全选/取消
                  </el-checkbox>
                  <span class="agent-count">{{ selectedAgentNames.length }}/{{ agentStore.agents.length }}</span>
                </div>
                <div class="agent-grid">
                  <div
                    v-for="agent in agentStore.agents"
                    :key="agent.type"
                    class="agent-grid-item"
                    :class="{ 'agent-grid-item--selected': selectedAgents.includes(agent.type) }"
                    @click="toggleAgent(agent.type)"
                  >
                    <span class="agent-emoji-small">{{ agent.emoji }}</span>
                    <span class="agent-grid-name">{{ agent.name }}</span>
                  </div>
                </div>
                <div class="agent-select-footer">
                  <div class="turns-selector">
                    <span>对话轮数:</span>
                    <el-input-number 
                      v-model="dialogueTurns" 
                      :min="1" 
                      :max="5" 
                      size="small"
                    />
                  </div>
                </div>
              </div>
            </el-popover>
            
            <!-- 智能选择开关 -->
            <el-tooltip content="开启后由AI自动选择合适的Agent" placement="top">
              <el-switch
                v-model="autoSelectAgents"
                active-text="AI智能"
                inactive-text="手动选"
                size="small"
                v-if="chatMode !== 'single'"
              />
            </el-tooltip>
          </div>
          
          <!-- 输入框 -->
          <div class="input-wrapper">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :autosize="{ minRows: 1, maxRows: 9 }"
              placeholder="请描述您的症状或问题..."
              @keyup.enter="handleSend"
              :disabled="agentStore.isLoading"
              resize="none"
            >
              <template #prefix>
                <el-icon><ChatDotRound /></el-icon>
              </template>
            </el-input>
            <el-button
              type="primary"
              @click="handleSend"
              :loading="agentStore.isLoading"
              :disabled="!inputMessage.trim()"
            >
              <el-icon><Promotion /></el-icon>
            </el-button>
          </div>
          
          <div class="input-tips">
            <span class="safety-tip">⚠️ 仅供参考，如有紧急情况请就医</span>
          </div>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useAgentStore } from '@/stores/agent'
import { usePatientStore } from '@/stores/patient'
import type { Agent } from '@/api'
import { marked } from 'marked'

// 配置marked
marked.setOptions({
  breaks: true,
  gfm: true
})

const agentStore = useAgentStore()
const patientStore = usePatientStore()

const inputMessage = ref('')
const useRag = ref(true)
const messagesRef = ref<HTMLElement>()
const chatMode = ref<'single' | 'multi' | 'dialogue'>('single')

// Agent选择相关
const selectedAgents = ref<string[]>([])  // 用户选择的Agent
const selectAllAgents = ref(false)  // 是否全选
const autoSelectAgents = ref(true)  // AI智能选择
const dialogueTurns = ref(2)  // 对话轮数

// 计算选中的Agent名称
const selectedAgentNames = computed(() => {
  return agentStore.agents
    .filter(a => selectedAgents.value.includes(a.type))
    .map(a => a.name)
})

// 切换Agent选择
const toggleAgent = (agentType: string) => {
  const index = selectedAgents.value.indexOf(agentType)
  if (index > -1) {
    selectedAgents.value.splice(index, 1)
  } else {
    selectedAgents.value.push(agentType)
  }
  autoSelectAgents.value = false  // 手动选择时关闭AI智能
  selectAllAgents.value = selectedAgents.value.length === agentStore.agents.length
}

// 全选/取消全选
const handleSelectAllAgents = (checked: boolean) => {
  if (checked) {
    selectedAgents.value = agentStore.agents.map(a => a.type)
  } else {
    selectedAgents.value = []
  }
}

// 会话历史列表
const sessionList = ref<Array<{
  id: string
  title: string
  message_count: number
  updated_at: string
}>>([])

// 会诊结果历史
const consultationHistory = ref<Array<{
  id: string
  query: string
  results: any[]
  timestamp: string
}>>([])

// 当前显示的会诊结果
const showConsultation = ref(false)

// 格式化日期
const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN')
}

// 加载会话列表
const loadSessions = async () => {
  try {
    const { chatApi } = await import('@/api')
    const res = await chatApi.getSessions(undefined, 50)
    console.log('[loadSessions] Sessions:', res.sessions?.length, res.sessions?.map(s => ({ id: s.id, title: s.title, message_count: s.message_count })))
    sessionList.value = res.sessions || []
  } catch (e) {
    console.error('加载会话列表失败:', e)
  }
}

// 切换会话
const switchSession = async (session: any) => {
  try {
    const { chatApi } = await import('@/api')
    // 设置当前会话ID
    agentStore.sessionId = session.id
    // 保存到 localStorage
    localStorage.setItem('current_session_id', session.id)
    
    // 根据会话的agent_type设置正确的模式
    if (session.agent_type === 'dialogue') {
      chatMode.value = 'dialogue'
      agentStore.dialogueMode = true
      agentStore.multiAgentMode = false
    } else if (session.agent_type === 'multi') {
      chatMode.value = 'multi'
      agentStore.multiAgentMode = true
      agentStore.dialogueMode = false
    } else {
      chatMode.value = 'single'
      agentStore.multiAgentMode = false
      agentStore.dialogueMode = false
    }
    
    // 加载历史消息
    const res = await chatApi.getHistory(session.id)
    console.log('[switchSession] Raw messages from API:', res.messages?.length, 'messages')
    
    if (res.messages && res.messages.length > 0) {
      // 分析消息，检测是对话模式还是普通模式
      const messages = res.messages
      const hasDialogueMode = messages.some((m: any) => m.agent_type === 'dialogue')
      const hasMultiMode = messages.some((m: any) => m.agent_type === 'multi' || m.agent_type === 'summary')
      console.log('[switchSession] hasDialogueMode:', hasDialogueMode, 'hasMultiMode:', hasMultiMode, 'agent_types:', [...new Set(messages.map((m: any) => m.agent_type))])
      
      if (hasDialogueMode) {
        // 对话模式：重构thinking过程
        const reconstructedMessages = reconstructDialogueMessages(messages)
        console.log('[switchSession] Reconstructed messages:', reconstructedMessages.length)
        agentStore.messages = reconstructedMessages
      } else if (hasMultiMode) {
        // 多Agent模式：重构thinking过程
        const reconstructedMessages = reconstructMultiAgentMessages(messages)
        console.log('[switchSession] MultiAgent reconstructed:', reconstructedMessages.length)
        agentStore.messages = reconstructedMessages
      } else {
        // 普通模式：确保user和assistant消息配对
        const processedMessages: any[] = []
        for (let i = 0; i < messages.length; i++) {
          const msg = messages[i]
          console.log('[switchSession] Processing message:', i, 'role:', msg.role, 'content:', msg.content?.substring(0, 30))
          // 只添加有效的消息（role 为 user 或 assistant）
          if (msg.role === 'user' || msg.role === 'assistant') {
            processedMessages.push({
              role: msg.role,
              content: msg.content,
              agentType: msg.agent_type,
              timestamp: msg.created_at,
              sources: msg.sources
            })
          }
        }
        console.log('[switchSession] Processed messages:', processedMessages.length)
        agentStore.messages = processedMessages
      }
      
      // 从 localStorage 加载重新生成历史
      const regenHistory = localStorage.getItem(`regen_${session.id}`)
      if (regenHistory) {
        try {
          const historyData = JSON.parse(regenHistory)
          // 找到最后一条 assistant 消息，附加历史记录
          for (let i = agentStore.messages.length - 1; i >= 0; i--) {
            if (agentStore.messages[i].role === 'assistant') {
              agentStore.messages[i].regenHistory = historyData
              agentStore.messages[i].regenCurrentIndex = historyData.length > 0 ? historyData.length : 1
              break
            }
          }
        } catch (e) {
          console.error('Parse regen history failed:', e)
        }
      }
    } else {
      agentStore.messages = []
    }
  } catch (e) {
    console.error('加载会话历史失败:', e)
  }
}

// 重构对话模式的消息
const reconstructDialogueMessages = (messages: any[]) => {
  const result: any[] = []
  let currentUserMsg: any = null
  let dialogueAgents: any[] = []
  let dialogueContent: string[] = []
  let summaryContent = ''
  
  for (let i = 0; i < messages.length; i++) {
    const msg = messages[i]
    
    if (msg.role === 'user') {
      // 保存之前的对话（如果有）
      if (dialogueAgents.length > 0) {
        result.push({
          role: 'assistant',
          content: summaryContent || dialogueContent.join('\n\n'),
          agentType: 'dialogue',
          timestamp: currentUserMsg?.created_at || msg.created_at,
          thinking: {
            type: 'dialogue',
            expanded: false,
            agents: [...dialogueAgents],
            summary: summaryContent
          }
        })
        dialogueAgents = []
        dialogueContent = []
        summaryContent = ''
      }
      currentUserMsg = msg
      result.push({
        role: 'user',
        content: msg.content,
        timestamp: msg.created_at
      })
    } else if (msg.role === 'assistant') {
      // 解析agent回答
      const match = msg.content.match(/^【(.+?)】/)
      if (match) {
        const agentName = match[1]
        const agentContent = msg.content.replace(/^【.+?】/, '')
        dialogueAgents.push({
          agent_type: msg.agent_type,
          agent_name: agentName,
          response: agentContent,
          sources: msg.sources,
          turn_index: dialogueAgents.length > 0 ? Math.floor(dialogueAgents.length / 2) : 0
        })
        dialogueContent.push(msg.content)
      } else if (msg.agent_type === 'summary' || msg.content.includes('综合建议')) {
        // 这是总结消息
        summaryContent = msg.content
      }
    }
  }
  
  // 处理最后一组对话
  if (dialogueAgents.length > 0) {
    result.push({
      role: 'assistant',
      content: summaryContent || dialogueContent.join('\n\n'),
      agentType: 'dialogue',
      timestamp: currentUserMsg?.created_at || new Date().toISOString(),
      thinking: {
        type: 'dialogue',
        expanded: false,
        agents: [...dialogueAgents],
        summary: summaryContent
      }
    })
  }
  
  return result
}

// 重构多Agent模式的消息
const reconstructMultiAgentMessages = (messages: any[]) => {
  const result: any[] = []
  let currentUserMsg: any = null
  let multiAgents: any[] = []
  let summaryContent = ''
  
  for (let i = 0; i < messages.length; i++) {
    const msg = messages[i]
    
    if (msg.role === 'user') {
      // 保存之前的多Agent对话（如果有）
      if (multiAgents.length > 0) {
        result.push({
          role: 'assistant',
          content: summaryContent || multiAgents.map(a => `【${a.agent_name}】${a.response}`).join('\n\n'),
          agentType: 'multi',
          timestamp: currentUserMsg?.created_at || msg.created_at,
          thinking: {
            type: 'multi',
            expanded: false,
            agents: [...multiAgents],
            summary: summaryContent
          }
        })
        multiAgents = []
        summaryContent = ''
      }
      currentUserMsg = msg
      result.push({
        role: 'user',
        content: msg.content,
        timestamp: msg.created_at
      })
    } else if (msg.role === 'assistant') {
      // 检测是否是总结消息
      if (msg.agent_type === 'summary') {
        summaryContent = msg.content
      } else {
        // 解析各Agent的回答
        const match = msg.content.match(/^【(.+?)】/)
        if (match) {
          const agentName = match[1]
          const agentContent = msg.content.replace(/^【.+?】/, '')
          multiAgents.push({
            agent_type: msg.agent_type,
            agent_name: agentName,
            response: agentContent,
            sources: msg.sources,
            turn_index: 0
          })
        }
      }
    }
  }
  
  // 处理最后一组多Agent对话
  if (multiAgents.length > 0 || summaryContent) {
    result.push({
      role: 'assistant',
      content: summaryContent || multiAgents.map(a => `【${a.agent_name}】${a.response}`).join('\n\n'),
      agentType: 'multi',
      timestamp: currentUserMsg?.created_at || new Date().toISOString(),
      thinking: {
        type: 'multi',
        expanded: false,
        agents: [...multiAgents],
        summary: summaryContent
      }
    })
  }
  
  return result
}

// 展开/收起思考过程
const toggleThinking = (index: number) => {
  const msg = agentStore.messages[index]
  if (msg.thinking) {
    msg.thinking.expanded = !msg.thinking.expanded
  }
  nextTick(() => {
    scrollToBottom()
  })
}

// Markdown渲染函数
const renderMarkdown = (content: string) => {
  if (!content) return ''
  const cleaned = content
    .replace(/\r\n/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .replace(/^[ \t]+|[ \t]+$/gm, '')
    .trim()
  return marked(cleaned) as string
}

// 复制消息内容
const copyMessage = async (content: string) => {
  try {
    // 提取纯文本用于复制（移除HTML标签）
    const textContent = content.replace(/<[^>]*>/g, '').trim()
    await navigator.clipboard.writeText(textContent)
    ElMessage.success('内容已复制到剪贴板')
  } catch (e) {
    ElMessage.error('复制失败，请手动复制')
  }
}

// 重新生成消息
const regenerateMessage = async (index: number) => {
  const msg = agentStore.messages[index]
  if (msg.role !== 'assistant') return
  
  // 找到对应的用户消息
  const userMsgIndex = index - 1
  if (userMsgIndex < 0 || agentStore.messages[userMsgIndex].role !== 'user') {
    ElMessage.warning('无法找到对应的用户消息')
    return
  }
  
  const userContent = agentStore.messages[userMsgIndex].content
  
  // 保存当前回复到历史记录
  const history = msg.regenHistory || []
  const newHistoryIndex = history.length + 1
  history.push({
    index: newHistoryIndex,
    content: msg.content,
    timestamp: new Date().toISOString()
  })
  msg.regenHistory = history
  msg.regenCurrentIndex = newHistoryIndex
  
  // 持久化到 localStorage
  try {
    localStorage.setItem(`regen_${agentStore.sessionId}`, JSON.stringify(history))
  } catch (e) {
    console.error('Save regen history failed:', e)
  }
  
  // 移除当前AI回复
  agentStore.messages.splice(index, 1)
  
  // 直接调用 store 的发送方法，传递上一次的回复内容
  if (agentStore.dialogueMode) {
    // 后端智能选择Agent
    const agentTypes = undefined
    await agentStore.sendDialogueMessage(
      userContent,
      patientStore.currentPatient?.id,
      agentTypes,
      2,
      msg.content
    )
  } else {
    await agentStore.sendMessage(
      userContent,
      patientStore.currentPatient?.id,
      useRag.value,
      msg.content
    )
  }
}

// 切换到指定的历史回复
const switchToRegenHistory = (index: number, msgIndex: number) => {
  const msg = agentStore.messages[msgIndex]
  if (!msg.regenHistory) return
  
  const historyItem = msg.regenHistory.find(h => h.index === index)
  if (historyItem) {
    msg.content = historyItem.content
    msg.regenCurrentIndex = index
    ElMessage.success('已切换到第 ' + index + ' 个版本')
  }
}

// 喜欢消息
const likeMessage = (index: number) => {
  ElMessage.success('感谢您的反馈！')
}

// 不喜欢消息
const dislikeMessage = (index: number) => {
  ElMessage.info('抱歉给您带来不好的体验，我们会继续优化')
}

// 保存会诊结果到历史
const saveConsultationToHistory = (query: string, results: any[]) => {
  consultationHistory.value.unshift({
    id: Date.now().toString(),
    query,
    results,
    timestamp: new Date().toLocaleString('zh-CN')
  })
}

// 重新查看会诊结果
const viewConsultation = (item: any) => {
  agentStore.multiAgentResults = item.results
  showConsultation.value = true
}

const quickQuestions = [
  '我空腹血糖8.5，餐后血糖14，糖化血红蛋白7.2%，服用二甲双胍和格列美脲，血糖还是控制不好，帮我调整方案',
  '我父亲脑梗康复出院2周了，左侧肢体偏瘫，说话不清，吞咽困难，家庭康复训练怎么做？',
  '最近工作压力大，总是失眠焦虑，血压也不稳定140/90左右，有什么方法可以缓解？',
  '我妈妈有高血压和糖尿病，饮食上要注意什么？哪些食物要多吃，哪些要少吃或避免？',
  '最近总是忘事，刚放下的东西就找不到了，有时候说话说到一半忘了要说什么，是不是认知出了问题？',
  '我父亲今年70岁，有糖尿病10年了，最近记性越来越差，经常忘记吃药，能帮他评估一下认知功能吗？'
]

// 初始化
onMounted(async () => {
  await agentStore.initAgents()
  await patientStore.fetchPatients()
  await loadSessions()
  
  // 优先从 localStorage 恢复会话ID
  const savedSessionId = localStorage.getItem('current_session_id')
  
  if (savedSessionId) {
    // 查找对应的会话
    const targetSession = sessionList.value.find((s: any) => s.id === savedSessionId)
    if (targetSession) {
      await switchSession(targetSession)
    } else if (sessionList.value.length > 0) {
      await switchSession(sessionList.value[0])
    } else {
      await agentStore.createSession()
      agentStore.messages = []
    }
  } else if (sessionList.value.length > 0) {
    // 加载最新的历史会话
    await switchSession(sessionList.value[0])
  } else {
    await agentStore.createSession()
    agentStore.messages = []
  }
})

// 选择Agent
const selectAgent = (agent: Agent) => {
  agentStore.selectAgent(agent)
}

// 发送消息
const handleSend = async () => {
  if (!inputMessage.value.trim() || agentStore.isLoading) return

  // 确保会话ID已保存
  if (agentStore.sessionId) {
    localStorage.setItem('current_session_id', agentStore.sessionId)
  }
  
  console.log('[handleSend] sessionId:', agentStore.sessionId, 'multiAgentMode:', agentStore.multiAgentMode)

  const message = inputMessage.value
  inputMessage.value = ''

  const wasMultiAgent = agentStore.multiAgentMode
  const wasDialogue = agentStore.dialogueMode
  console.log('handleSend - wasDialogue:', wasDialogue, 'wasMultiAgent:', wasMultiAgent, 'chatMode:', chatMode.value)
  
  if (wasDialogue) {
    // Agent对话模式 - 使用SSE流式输出
    // 根据autoSelectAgents决定是智能选择还是使用用户选择的Agent
    const agentTypes = autoSelectAgents.value || selectedAgents.value.length === 0 
      ? undefined  // AI智能选择
      : selectedAgents.value  // 使用用户选择的Agent
    
    console.log('[handleSend] dialogue mode - autoSelect:', autoSelectAgents.value, 'selectedAgents:', selectedAgents.value, 'finalAgentTypes:', agentTypes)
    
    await agentStore.sendDialogueMessage(
      message,
      patientStore.currentPatient?.id,
      agentTypes,
      dialogueTurns.value
    )
  } else {
    // 普通/多Agent模式 - sendMessage内部会根据multiAgentMode自动判断
    await agentStore.sendMessage(
      message,
      patientStore.currentPatient?.id,
      useRag.value
    )
  }

  // 如果是多Agent模式，保存会诊历史
  if (wasMultiAgent && agentStore.multiAgentResults && agentStore.multiAgentResults.length > 0) {
    consultationHistory.value.unshift({
      id: Date.now().toString(),
      query: message,
      results: agentStore.multiAgentResults,
      timestamp: new Date().toLocaleString('zh-CN')
    })
    // 显示会诊结果面板
    showConsultation.value = true
  }

  scrollToBottom()
}

// 快捷问题
const sendQuickQuestion = async (question: string) => {
  inputMessage.value = question
  await handleSend()
}

// 新建对话
const createNewChat = async () => {
  try {
    const hasExistingSession = agentStore.sessionId && agentStore.messages.length > 0
    await agentStore.createSession()
    agentStore.messages = []
    // 重置聊天模式到单Agent
    chatMode.value = 'single'
    agentStore.multiAgentMode = false
    agentStore.dialogueMode = false
    await loadSessions()
    // 只有当之前有有效会话时才提示
    if (hasExistingSession) {
      ElMessage.success('已创建新对话')
    }
  } catch (e) {
    ElMessage.error('创建对话失败')
  }
}

// 清除对话
const clearChat = () => {
  agentStore.clearMessages()
  ElMessage.success('对话已清空')
}

// 模式切换
const handleModeChange = (mode: 'single' | 'multi' | 'dialogue') => {
  console.log('handleModeChange called:', mode)
  if (mode === 'multi') {
    agentStore.multiAgentMode = true
    agentStore.dialogueMode = false
    ElMessage.info('已开启多Agent会诊模式，多位专家将同时为您解答')
  } else if (mode === 'dialogue') {
    console.log('Switching to dialogue mode directly')
    agentStore.dialogueMode = true
    agentStore.multiAgentMode = false
    console.log('After set - dialogueMode:', agentStore.dialogueMode, 'multiAgentMode:', agentStore.multiAgentMode)
    ElMessage.info('已开启Agent对话模式，多位专家将讨论并给出建议')
  } else {
    agentStore.multiAgentMode = false
    agentStore.dialogueMode = false
  }
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

// 辅助函数
const getAgentEmoji = (type?: string): string => {
  if (!type) return '🤖'
  const agent = agentStore.agents.find(a => a.type === type)
  return agent?.emoji || '🤖'
}

const getAgentName = (type?: string): string => {
  if (!type) return 'AI助手'
  const agent = agentStore.agents.find(a => a.type === type)
  return agent?.name || type
}

const getAgentColor = (type?: string): string => {
  if (!type) return '#909399'
  const agent = agentStore.agents.find(a => a.type === type)
  return agent?.color || '#909399'
}

// 监听消息变化自动滚动
watch(() => agentStore.messages.length, () => {
  scrollToBottom()
})
</script>

<style scoped>
.chat-view {
  height: calc(100vh - 60px);
  background: #fafafa;
}

.el-container {
  height: 100%;
}

/* 左侧历史面板 */
.history-panel {
  background: white;
  border-right: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
}

.history-header {
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #f0f0f0;
}

.history-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.history-list {
  flex: 1;
  padding: 8px;
  overflow-y: auto;
}

.history-item {
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 4px;
  transition: all 0.2s;
}

.history-item:hover {
  background: var(--color-bg-hover);
}

.history-item.active {
  background: #ecf5ff;
}

.history-title {
  font-size: 14px;
  color: #303133;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-meta {
  font-size: 12px;
  color: #909399;
}

.history-empty {
  padding: 20px;
  text-align: center;
  color: #909399;
  font-size: 14px;
}

/* 患者信息 */
.patient-card {
  padding: 12px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.patient-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.patient-info {
  flex: 1;
  overflow: hidden;
}

.patient-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.patient-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

/* 主聊天区域 */
.chat-main {
  background: #fafafa;
  display: flex;
  flex-direction: column;
  padding: 0;
}

.chat-topbar {
  padding: 12px 20px;
  background: white;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
}

.chat-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.agent-emoji {
  font-size: 20px;
}

.agent-name {
  font-size: 15px;
  font-weight: 500;
  color: #303133;
}

/* 消息容器 */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.welcome-message {
  text-align: center;
  padding: 60px 20px;
}

.welcome-icon {
  font-size: 48px;
  margin-bottom: 20px;
}

.welcome-title {
  font-size: 22px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 10px;
}

.welcome-desc {
  font-size: 14px;
  color: #909399;
  margin-bottom: 20px;
}

.quick-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.agent-list {
  padding: 15px;
  flex: 1;
}

.agent-card {
  display: flex;
  align-items: center;
  padding: 12px;
  margin-bottom: 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
  background: #fafafa;
}

.agent-card:hover {
  background: #ecf5ff;
  border-color: var(--agent-color);
}

.agent-card.active {
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.1), rgba(64, 158, 255, 0.05));
  border-color: var(--agent-color);
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.2);
}

.agent-icon {
  font-size: 32px;
  margin-right: 12px;
}

.agent-info {
  flex: 1;
}

.agent-name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.agent-desc {
  font-size: 12px;
  color: #909399;
}

/* 会话历史 */
.session-history {
  border-top: 1px solid #e4e7ed;
  padding: 10px 0;
  flex-shrink: 0;
  max-height: 200px;
  display: flex;
  flex-direction: column;
}

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 15px 10px;
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.session-list-scrollbar {
  flex: 1;
  overflow: hidden;
}

.session-list {
  padding: 0 10px;
}

.session-item {
  padding: 10px;
  margin-bottom: 5px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  background: var(--color-bg-hover);
}

.session-item:hover {
  background: #ecf5ff;
}

.session-item.active {
  background: var(--color-primary);
  color: white;
}

.session-item.active .session-meta {
  color: rgba(255, 255, 255, 0.8);
}

.session-title {
  font-size: 14px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 4px;
}

.session-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
}

.session-empty {
  text-align: center;
  padding: 20px;
  color: #909399;
  font-size: 13px;
}

.patient-info {
  padding: 15px;
  border-top: 1px solid #e4e7ed;
}

.patient-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: #f0f9ff;
  border-radius: 8px;
}

.patient-detail {
  flex: 1;
}

.patient-diseases {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
  margin-top: 5px;
}

/* 主聊天区 */
.chat-main {
  display: flex;
  flex-direction: column;
  padding: 0;
  background: var(--color-bg-hover);
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
}

.current-agent {
  display: flex;
  align-items: center;
  gap: 10px;
}

.current-agent .emoji {
  font-size: 24px;
}

.current-agent .name {
  font-weight: 600;
  color: #303133;
}

.multi-agent-badge {
  display: flex;
  align-items: center;
}

/* 消息容器 */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

/* 欢迎消息 */
.welcome-message {
  text-align: center;
  padding: 60px 20px;
}

.welcome-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.welcome-title {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 10px;
}

.welcome-desc {
  color: #606266;
  line-height: 1.8;
  margin-bottom: 30px;
}

.quick-questions {
  display: flex;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap;
}

/* 消息样式 */
.message-wrapper {
  display: flex;
  margin-bottom: 20px;
}

.message-wrapper.user {
  justify-content: flex-end;
}

.message {
  display: flex;
  max-width: 70%;
}

.user-message {
  flex-direction: row-reverse;
}

.message-avatar {
  font-size: 28px;
  flex-shrink: 0;
}

.user-message .message-avatar {
  margin-left: 10px;
}

.assistant-message .message-avatar {
  margin-right: 10px;
}

.message-content-wrapper {
  display: flex;
  flex-direction: column;
  gap: 5px;
  flex: 1;
}

.message-agent-tag {
  display: flex;
}

.message-actions {
  display: flex;
  gap: 4px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 2px;
  color: #909399;
  font-size: 12px;
  padding: 2px 4px;
}

.action-btn:hover {
  color: var(--color-primary);
}

.action-icon {
  font-size: 12px;
}

.regen-counter {
  display: flex;
  align-items: center;
  gap: 2px;
}

.regen-icon {
  font-size: 14px;
}

.regen-count {
  font-size: 11px;
  min-width: 14px;
  text-align: center;
}

.message-content {
  padding: 12px 18px;
  border-radius: 12px;
  line-height: 1.5;
  white-space: normal;
  word-break: break-word;
}

.user-message .message-content {
  background: var(--gradient-button);
  color: white;
}

.assistant-message .message-content-wrapper {
  background: #FFFFFF;
  color: #2F2E2A;
  box-shadow: 0 2px 8px rgba(60, 55, 45, 0.08);
  border-radius: 12px;
  padding: 14px 18px;
  margin-left: 4px;
  max-width: 100%;
}

/* 思考过程样式 */
.thinking-process {
  margin-top: 10px;
  margin-bottom: 12px;
  border-radius: 8px;
  overflow: hidden;
}

.thinking-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: var(--gradient-header);
  color: white;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.3s;
}

.thinking-header:hover {
  opacity: 0.9;
}

.thinking-header.expanded {
  border-radius: 8px 8px 0 0;
}

.thinking-icon {
  font-size: 12px;
}

.thinking-title {
  font-weight: 600;
  font-size: 14px;
}

.thinking-hint {
  font-size: 12px;
  opacity: 0.8;
  margin-left: auto;
}

.thinking-content {
  background: #f8f9fc;
  border-radius: 0 0 8px 8px;
  padding: 16px;
  padding-left: 20px;
  max-height: 400px;
  overflow-y: auto;
}

.thinking-agent {
  background: white;
  border-radius: 8px;
  padding: 14px;
  padding-left: 18px;
  margin-bottom: 12px;
  margin-left: 8px;
  border-left: 3px solid #667eea;
}

.thinking-agent:last-child {
  margin-bottom: 0;
}

.agent-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.agent-emoji {
  font-size: 16px;
}

.agent-name {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}

.agent-response {
  font-size: 13px;
  line-height: 1.6;
  color: #606266;
}

.thinking-turn {
  background: var(--color-bg-card);
;
  border-radius: 8px;
  padding: 14px;
  padding-left: 18px;
  margin-bottom: 12px;
  margin-left: 8px;
  border-left: 3px solid var(--color-primary)
}

.thinking-turn:last-child {
  margin-bottom: 0;
}

.turn-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.turn-emoji {
  font-size: 16px;
}

.turn-name {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}

.turn-content {
  font-size: 13px;
  line-height: 1.6;
  color: #606266;
}

/* 加载中 */
.loading-message {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px;
  color: #909399;
}

.loading-icon {
  font-size: 24px;
  animation: bounce 1s infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

/* 多Agent结果 */
.multi-agent-results {
  background: white;
  border-top: 1px solid #e4e7ed;
  max-height: 300px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  background: #f0f9ff;
  font-weight: 600;
}

.results-content {
  padding: 15px;
  display: flex;
  gap: 15px;
  overflow-x: auto;
}

.result-card {
  min-width: 250px;
  background: #fafafa;
  border-radius: 8px;
  padding: 15px;
}

.result-agent {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  margin-bottom: 10px;
  color: #303133;
}

.result-response {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  max-height: 150px;
  overflow-y: auto;
}

/* 输入区 */
.input-area {
  padding: 20px;
  background: white;
  border-top: 1px solid #e4e7ed;
}

/* 模式选择栏 */
.mode-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

/* Agent选择器 */
.agent-select-panel {
  max-height: 420px;
  display: flex;
  flex-direction: column;
}

.agent-select-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 4px 12px;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 8px;
  flex-shrink: 0;
}

.agent-count {
  font-size: 12px;
  color: #909399;
}

.agent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 6px;
  overflow-y: auto;
  max-height: 320px;
  padding: 4px 0;
  flex: 1;
}

.agent-grid-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 13px;
  border: 1px solid transparent;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.agent-grid-item:hover {
  background-color: #f5f7fa;
  border-color: #dcdfe6;
}

.agent-grid-item--selected {
  background-color: #ecf5ff;
  border-color: #409eff;
  color: #409eff;
}

.agent-grid-item--selected:hover {
  background-color: #d9ecff;
}

.agent-grid-name {
  overflow: hidden;
  text-overflow: ellipsis;
}

.agent-emoji-small {
  font-size: 14px;
  flex-shrink: 0;
}

.agent-select-footer {
  border-top: 1px solid #ebeef5;
  padding-top: 10px;
  margin-top: 8px;
  flex-shrink: 0;
}

.agent-option {
  display: flex;
  align-items: center;
  gap: 6px;
}

.turns-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
}

.turns-selector span {
  font-size: 13px;
  color: #606266;
}

.input-wrapper {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.input-wrapper .el-textarea {
  flex: 1;
}

.input-wrapper .el-textarea textarea {
  max-height: 150px;
}

.input-tips {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
}

.tips-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.safety-tip {
  font-size: 12px;
  color: #e6a23c;
}

/* 过渡动画 */
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.3s ease;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateY(20px);
  opacity: 0;
}

/* Markdown样式 */
.markdown-body {
  line-height: 1.5;
  color: #303133;
}

.markdown-body p {
  margin: 0;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4,
.markdown-body h5,
.markdown-body h6 {
  margin: 8px 0 4px 0;
  color: #1a1a1a;
}

.markdown-body h1 { font-size: 1.4em; }
.markdown-body h2 { font-size: 1.2em; }
.markdown-body h3 { font-size: 1.1em; }

.markdown-body ul,
.markdown-body ol {
  margin: 4px 0;
  padding-left: 18px;
}

.markdown-body li {
  margin: 2px 0;
}

.markdown-body code {
  background: var(--color-bg-hover);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
  color: #e6a23c;
}

.markdown-body pre {
  background: #282c34;
  color: #abb2bf;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
}

.markdown-body pre code {
  background: transparent;
  padding: 0;
  color: inherit;
}

.markdown-body blockquote {
  border-left: 3px solid var(--color-primary);
  margin: 6px 0;
  padding: 6px 12px;
  background: #f0f9ff;
  color: #606266;
}

.markdown-body strong {
  color: #303133;
}

.markdown-body table {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
}

.markdown-body th,
.markdown-body td {
  border: 1px solid #dcdfe6;
  padding: 6px 10px;
  text-align: left;
}

.markdown-body th {
  background: var(--color-bg-hover);
  font-weight: 600;
}

/* 会诊结果头部按钮 */
.results-header .results-actions {
  display: flex;
  align-items: center;
  gap: 5px;
}

/* 会诊历史记录 */
.consultation-history {
  padding: 15px;
  border-top: 1px solid #e4e7ed;
  max-height: 200px;
  overflow-y: auto;
}

.history-title {
  font-size: 14px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 10px;
}

.history-item {
  padding: 10px;
  background: var(--color-bg-hover);
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.history-item:hover {
  background: #ecf5ff;
}

.history-query {
  font-size: 14px;
  color: #303133;
  margin-bottom: 5px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-meta {
  font-size: 12px;
  color: #909399;
  display: flex;
  justify-content: space-between;
}

/* Agent对话结果 */
.dialogue-results {
  background: white;
  border-top: 1px solid #e4e7ed;
  max-height: 400px;
}

.dialogue-content {
  padding: 15px;
}

.dialogue-item {
  margin-bottom: 20px;
}

.dialogue-query {
  background: #f0f9ff;
  padding: 10px 15px;
  border-radius: 6px;
  margin-bottom: 15px;
  font-size: 14px;
}

.dialogue-turns {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.dialogue-turn {
  background: #fafafa;
  border-radius: 8px;
  padding: 12px;
}

.turn-speaker {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.speaker-emoji {
  font-size: 18px;
}

.speaker-name {
  font-weight: 600;
  color: #303133;
}

.turn-content {
  font-size: 14px;
  line-height: 1.6;
  color: #606266;
}

.dialogue-summary {
  margin-top: 15px;
  padding: 15px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: white;
}

.summary-label {
  font-weight: 600;
  margin-bottom: 8px;
}

.summary-content {
  font-size: 14px;
  line-height: 1.6;
}

.summary-content :deep(p) {
  margin: 0;
}
</style>
