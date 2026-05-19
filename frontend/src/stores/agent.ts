import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { chatApi, patientApi, simulationApi, type Agent, type ChatMessage, type Patient, type SimulationResult } from '@/api'
import api from '@/api'

const STATUS_CACHE_TTL = 5 * 60 * 1000

export const useAgentStore = defineStore('agent', () => {
  const agents = ref<Agent[]>([])
  const currentAgent = ref<Agent | null>(null)
  const sessionId = ref<string>('')
  const messages = ref<ChatMessage[]>([])
  const isLoading = ref(false)
  const multiAgentMode = ref(false)
  const multiAgentResults = ref<Array<{
    agent_type: string
    agent_name: string
    response: string
    sources: Array<{ title: string; content: string }>
  }>>([])

  const statusLastChecked = ref<number>(0)
  const isCheckingStatus = ref(false)

  // 计算属性
  const currentAgentColor = computed(() => currentAgent.value?.color || '#409EFF')
  const currentAgentEmoji = computed(() => currentAgent.value?.emoji || '🤖')

  // 初始化 - 获取所有Agent
  const initAgents = async () => {
    try {
      const res = await chatApi.getAgents()
      agents.value = res.agents
      if (agents.value.length > 0 && !currentAgent.value) {
        currentAgent.value = agents.value.find(a => a.type === 'general') || agents.value[0]
      }
    } catch (error) {
      console.error('Failed to load agents:', error)
      // 备用Agent列表
      agents.value = [
        { type: 'general', name: '健康助手', description: '通用健康咨询', color: '#909399', emoji: '🤖' },
        { type: 'diabetes', name: '糖尿病专科', description: '糖尿病管理专家', color: '#409EFF', emoji: '🩺' },
        { type: 'hypertension', name: '高血压专科', description: '高血压管理专家', color: '#F56C6C', emoji: '💓' },
        { type: 'nutrition', name: '营养咨询', description: '营养饮食指导', color: '#67C23A', emoji: '🥗' },
        { type: 'coach', name: '健康教练', description: '运动处方指导', color: '#E6A23C', emoji: '💪' },
        { type: 'medication', name: '用药咨询', description: '药物知识指导', color: '#9C27B0', emoji: '💊' },
        { type: 'psychology', name: '心理支持', description: '心理健康支持', color: '#E91E63', emoji: '🧠' },
        { type: 'rehabilitation', name: '康复指导', description: '康复训练指导', color: '#4CAF50', emoji: '🏃' },
        { type: 'cognitive', name: '认知评估', description: '认知健康评估与训练建议', color: '#9B59B6', emoji: '🧩' }
      ]
    }
  }

  // 选择Agent
  const selectAgent = (agent: Agent) => {
    currentAgent.value = agent
  }

  // 自动选择Agent
  const autoSelectAgent = async (query: string, patientContext?: Record<string, unknown>) => {
    try {
      const res = await chatApi.selectAgent(query, patientContext)
      const agent = agents.value.find(a => a.type === res.type)
      if (agent) {
        currentAgent.value = agent
      }
    } catch (error) {
      console.error('Auto select agent failed:', error)
    }
  }

  // 创建会话
  const createSession = async (patientId?: string) => {
    try {
      const res = await chatApi.createSession(patientId)
      sessionId.value = res.session_id
      messages.value = []
      // 清除本地存储的重新生成历史
      localStorage.removeItem(`regen_${res.session_id}`)
      // 保存当前会话ID
      localStorage.setItem('current_session_id', res.session_id)
      return res.session_id
    } catch (error) {
      console.error('Create session failed:', error)
      sessionId.value = `session-${Date.now()}`
      localStorage.setItem('current_session_id', sessionId.value)
      return sessionId.value
    }
  }

  // 恢复会话
  const restoreSession = () => {
    const savedSessionId = localStorage.getItem('current_session_id')
    if (savedSessionId) {
      sessionId.value = savedSessionId
      return savedSessionId
    }
    return null
  }

  // 保存重新生成历史到 localStorage
  const saveRegenHistory = (sessionId: string, history: any) => {
    try {
      localStorage.setItem(`regen_${sessionId}`, JSON.stringify(history))
    } catch (e) {
      console.error('Save regen history failed:', e)
    }
  }

  // 从 localStorage 加载重新生成历史
  const loadRegenHistory = (sessionId: string): any => {
    try {
      const data = localStorage.getItem(`regen_${sessionId}`)
      return data ? JSON.parse(data) : null
    } catch (e) {
      console.error('Load regen history failed:', e)
      return null
    }
  }

  // 发送消息
  const sendMessage = async (
    content: string,
    patientId?: string,
    useRag: boolean = true,
    previousContent?: string
  ) => {
    if (!content.trim()) return

    // 确保有会话ID
    if (!sessionId.value) {
      await createSession(patientId)
    }
    
    isLoading.value = true
    
    // 添加用户消息
    messages.value.push({
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    })

    try {
      console.log('[sendMessage] multiAgentMode:', multiAgentMode.value, 'sessionId:', sessionId.value)
      if (multiAgentMode.value) {
        // 多Agent模式
        const res = await chatApi.multiAgentChat({
          session_id: sessionId.value,
          patient_id: patientId,
          message: content,
          use_rag: useRag
        })
        
        // 更新多Agent结果
        multiAgentResults.value = res.individual_results.map((r: any) => ({
          agent_type: r.agent_type,
          agent_name: agents.value.find(a => a.type === r.agent_type)?.name || r.agent_type,
          response: r.response,
          sources: r.sources
        }))

        // 添加助手消息（显示综合结果 + 思考过程）
        const assistantMsg: any = {
          role: 'assistant',
          content: res.summary || res.individual_results[0]?.response || '',
          agentType: 'multi',
          timestamp: new Date().toISOString(),
          thinking: {
            type: 'multi',
            expanded: true,  // 多agent会诊默认展开
            agents: res.individual_results.map((r: any) => ({
              agent_type: r.agent_type,
              agent_name: agents.value.find(a => a.type === r.agent_type)?.name || r.agent_type,
              response: r.response,
              sources: r.sources
            }))
          }
        }
        
        // 如果有上一次的内容，保存到历史记录
        if (previousContent) {
          assistantMsg.regenHistory = [{
            index: 1,
            content: previousContent,
            timestamp: new Date().toISOString()
          }]
          assistantMsg.regenCurrentIndex = 1
        }
        
        // 持久化到 localStorage（保存当前最新回复）
        const currentHistory = assistantMsg.regenHistory || []
        if (currentHistory.length > 0) {
          // 添加当前版本（最新）
          currentHistory.unshift({
            index: 0,
            content: assistantMsg.content,
            timestamp: new Date().toISOString()
          })
          saveRegenHistory(sessionId.value, currentHistory)
        }
        
        messages.value.push(assistantMsg)
      } else {
        // 单Agent模式
        const res = await chatApi.sendMessage({
          session_id: sessionId.value,
          patient_id: patientId,
          message: content,
          agent_type: currentAgent.value?.type,
          use_rag: useRag
        })

        const assistantMsg: any = {
          role: 'assistant',
          content: res.message,
          agentType: res.agent_type,
          timestamp: new Date().toISOString()
        }
        
        // 如果有上一次的内容，保存到历史记录
        if (previousContent) {
          assistantMsg.regenHistory = [{
            index: 1,
            content: previousContent,
            timestamp: new Date().toISOString()
          }]
          assistantMsg.regenCurrentIndex = 1
        }
        
        // 持久化到 localStorage（保存当前最新回复）
        const currentHistory = assistantMsg.regenHistory || []
        if (currentHistory.length > 0) {
          // 添加当前版本（最新）
          currentHistory.unshift({
            index: 0,
            content: assistantMsg.content,
            timestamp: new Date().toISOString()
          })
          saveRegenHistory(sessionId.value, currentHistory)
        }
        
        messages.value.push(assistantMsg)

        // 自动切换到响应的Agent
        if (res.agent_type !== currentAgent.value?.type) {
          const agent = agents.value.find(a => a.type === res.agent_type)
          if (agent) {
            currentAgent.value = agent
          }
        }
      }
    } catch (error) {
      console.error('Send message failed:', error)
      messages.value.push({
        role: 'assistant',
        content: '抱歉，服务暂时不可用，请稍后重试。',
        timestamp: new Date().toISOString()
      })
    } finally {
      isLoading.value = false
    }
  }

  // 切换多Agent模式
  const toggleMultiAgentMode = (enabled: boolean) => {
    multiAgentMode.value = enabled
    multiAgentResults.value = []
    dialogueMode.value = false
    dialogueResults.value = []
  }

  // Agent对话模式
  const dialogueMode = ref(false)
  const dialogueResults = ref<Array<{
    dialogue_id: string
    query: string
    agents: Array<{ type: string; name: string }>
    turns: Array<{
      turn_index: number
      speaker_agent: string
      speaker_name: string
      content: string
      sources: Array<{ title: string; content: string }>
    }>
    summary: string
  }>>([])

  // 切换Agent对话模式
  const toggleDialogueMode = (enabled: boolean) => {
    console.log('toggleDialogueMode called, enabled:', enabled, 'dialogueMode before:', dialogueMode.value)
    dialogueMode.value = enabled
    dialogueResults.value = []
    if (enabled) {
      multiAgentMode.value = false
    }
    console.log('toggleDialogueMode done, dialogueMode after:', dialogueMode.value)
  }

  // 发送Agent对话消息 - SSE流式版本
  const sendDialogueMessage = async (
    content: string,
    patientId?: string,
    agentTypes?: string[],
    maxTurns: number = 2,
    previousContent?: string
  ) => {
    if (!content.trim()) return

    // 确保有会话ID
    if (!sessionId.value) {
      await createSession(patientId)
    }
    
    isLoading.value = true
    
    // 添加用户消息
    messages.value.push({
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    })

    // 如果没有指定Agent，传undefined让后端智能选择
    // 如果指定了，使用指定的Agent列表
    const selectedAgents = agentTypes && Array.isArray(agentTypes) && agentTypes.length > 0 
      ? agentTypes 
      : undefined  // 后端智能选择

    const agentResults: Array<{ agent_type: string; agent_name: string; response: string }> = []
    let currentAgentIndex = -1
    
    // 添加一个空的消息用于流式更新
    const resultMessageIndex = messages.value.length
    const initialMsg: any = {
      role: 'assistant',
      content: '🤔 正在启动Agent对话...',
      agentType: 'dialogue',
      timestamp: new Date().toISOString(),
      thinking: {
        type: 'dialogue',
        expanded: true,
        agents: [],
        summary: ''
      }
    }
    
    // 如果有上一次的内容，保存到历史记录
    if (previousContent) {
      initialMsg.regenHistory = [{
        index: 1,
        content: previousContent,
        timestamp: new Date().toISOString()
      }]
      initialMsg.regenCurrentIndex = 1
    }
    
    messages.value.push(initialMsg)

    // 使用EventSource接收SSE流式数据
    return new Promise<void>((resolve, reject) => {
      try {
        // 构建SSE URL
        const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api/v1'
        let url = `${baseUrl}/chat/agent-dialogue/stream?message=${encodeURIComponent(content)}`
        if (patientId) url += `&patient_id=${patientId}`
        if (sessionId.value) url += `&session_id=${sessionId.value}`
        if (selectedAgents && selectedAgents.length > 0) url += `&agent_types=${encodeURIComponent(JSON.stringify(selectedAgents))}`
        url += `&max_turns=${maxTurns}`
        
        console.log('[SSE] Connecting to:', url)
        
        const eventSource = new EventSource(url)
        
        eventSource.onmessage = (event) => {
          console.log('[SSE] Received:', event.data)
          
          try {
            const data = JSON.parse(event.data)
            
            switch (data.type) {
              case 'start':
                messages.value[resultMessageIndex].content = '🤔 开始Agent对话...'
                break
                
              case 'agent_start':
                currentAgentIndex++
                const agentName = data.agent_name || data.agent_type
                messages.value[resultMessageIndex].content = `🤔 正在咨询 ${agentName}...`
                // 更新thinking中的状态
                if (!messages.value[resultMessageIndex].thinking) {
                  messages.value[resultMessageIndex].thinking = {
                    type: 'dialogue',
                    expanded: true,
                    agents: [],
                    summary: ''
                  }
                }
                messages.value[resultMessageIndex].thinking!.agents.push({
                  agent_type: data.agent_type,
                  agent_name: agentName,
                  response: '正在获取回答...'
                })
                break
                
              case 'agent_response':
                // 更新对应Agent的回答
                if (messages.value[resultMessageIndex].thinking) {
                  const agents = messages.value[resultMessageIndex].thinking!.agents
                  const lastAgent = agents[agents.length - 1]
                  if (lastAgent) {
                    lastAgent.response = data.content
                    lastAgent.sources = data.sources
                    lastAgent.turn_index = data.turn_index || 0
                  }
                }
                messages.value[resultMessageIndex].content = `✅ ${data.agent_name} 已回答`
                
                agentResults.push({
                  agent_type: data.agent_type,
                  agent_name: data.agent_name,
                  response: data.content
                })
                break
                
              case 'round_start':
                messages.value[resultMessageIndex].content = `🤔 第${data.round}轮讨论中...`
                break
                
              case 'agent_error':
                console.error('[SSE] Agent error:', data.error)
                messages.value[resultMessageIndex].content = `⚠️ ${data.agent_type} 回答出错`
                break
                
              case 'summary_start':
                messages.value[resultMessageIndex].content = '🤔 正在生成综合建议...'
                break
                
              case 'summary':
                messages.value[resultMessageIndex].content = data.summary
                messages.value[resultMessageIndex].thinking!.summary = data.summary
                messages.value[resultMessageIndex].thinking!.expanded = false // 默认收起
                messages.value[resultMessageIndex].agentType = 'dialogue'
                break
                
              case 'done':
                eventSource.close()
                isLoading.value = false
                resolve()
                break
            }
          } catch (e) {
            console.error('[SSE] Parse error:', e, event.data)
          }
        }
        
        eventSource.onerror = (error) => {
          console.error('[SSE] Error:', error)
          eventSource.close()
          isLoading.value = false
          
          // 如果没有收到任何结果，显示错误消息
          if (agentResults.length === 0) {
            messages.value[resultMessageIndex].content = '抱歉，Agent对话服务暂时不可用。'
          } else if (messages.value[resultMessageIndex].thinking?.summary) {
            // 如果已有部分结果，使用总结
            messages.value[resultMessageIndex].content = messages.value[resultMessageIndex].thinking.summary
          }
          resolve()
        }
        
      } catch (error) {
        console.error('[SSE] Setup error:', error)
        isLoading.value = false
        messages.value[resultMessageIndex].content = '抱歉，Agent对话服务暂时不可用。'
        resolve()
      }
    })
  }

  const clearMessages = () => {
    messages.value = []
    multiAgentResults.value = []
  }

  const checkAgentStatus = async (force: boolean = false) => {
    const now = Date.now()
    if (!force && statusLastChecked.value && (now - statusLastChecked.value) < STATUS_CACHE_TTL) {
      return
    }
    if (isCheckingStatus.value) return
    isCheckingStatus.value = true

    agents.value.forEach(a => {
      if (!a.status || a.status === 'checking') a.status = 'checking'
    })

    try {
      const res = await api.get('/chat/agents?check_status=true')
      if (res.agents) {
        agents.value.forEach(agent => {
          const updated = res.agents.find((a: any) => a.type === agent.type)
          if (updated) {
            agent.status = updated.status
            agent.status_reason = updated.status_reason
          }
        })
      }
      statusLastChecked.value = Date.now()
    } catch (e) {
      agents.value.forEach(agent => {
        if (agent.status === 'checking') agent.status = 'online'
      })
    } finally {
      isCheckingStatus.value = false
    }
  }

  return {
    agents,
    currentAgent,
    sessionId,
    messages,
    isLoading,
    multiAgentMode,
    multiAgentResults,
    statusLastChecked,
    isCheckingStatus,
    currentAgentColor,
    currentAgentEmoji,
    initAgents,
    selectAgent,
    autoSelectAgent,
    createSession,
    sendMessage,
    toggleMultiAgentMode,
    toggleDialogueMode,
    sendDialogueMessage,
    dialogueMode,
    dialogueResults,
    clearMessages,
    checkAgentStatus
  }
})
