import axios, { AxiosInstance, AxiosResponse } from 'axios'

const api: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 60000
})

// 请求拦截 - 添加JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    const tokenType = localStorage.getItem('tokenType') || 'Bearer'
    if (token) {
      config.headers.Authorization = `${tokenType} ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error)
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('tokenType')
      localStorage.removeItem('userInfo')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// ============ 类型定义 ============

// Agent相关
export interface Agent {
  type: string
  name: string
  description: string
  color: string
  emoji: string
  status?: 'online' | 'offline' | 'checking'
  status_reason?: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp?: string
  agentType?: string
  thinking?: {
    type: 'multi' | 'dialogue'
    expanded?: boolean
    agents?: Array<{
      agent_type: string
      agent_name: string
      response: string
      sources?: Array<{ title: string; content: string }>
      turn_index?: number
    }>
    turns?: Array<{
      turn_index: number
      speaker_agent: string
      speaker_name: string
      content: string
    }>
    summary?: string
  }
  // 重新生成历史
  regenHistory?: Array<{
    index: number
    content: string
    timestamp: string
  }>
  regenCurrentIndex?: number
}

export interface ChatRequest {
  session_id?: string
  patient_id?: string
  message: string
  agent_type?: string
  use_rag?: boolean
}

export interface ChatResponse {
  session_id: string
  message: string
  agent_type: string
  sources: Array<{ title: string; content: string }>
  safety?: {
    level: string
    violations: string[]
    suggestions: string[]
  }
}

// 患者相关
export interface Patient {
  id: string
  name: string
  age: number
  gender: string
  diseases: string[]
  medications: string[]
  allergies: string[]
  created_at: string
}

export interface VitalRecord {
  id: string
  patient_id: string
  type: string
  value: number
  unit: string
  recorded_at: string
}

// 干预模拟相关
export interface SimulationRequest {
  patient_id: string
  patient_name?: string
  age?: number
  disease: string
  current_vitals: Record<string, number>
  intervention_type: string
}

export interface SimulationResult {
  intervention: {
    type: string
    name: string
    description: string
    duration_days: number
  }
  status: string
  baseline: Record<string, number>
  predicted: Record<string, number>
  timeline: Array<Record<string, number>>
  effectiveness: number
  risk_level: string
  recommendations: string[]
}

// ============ Chat API ============

export const chatApi = {
  // 发送消息
  sendMessage(data: ChatRequest): Promise<ChatResponse> {
    return api.post('/chat/send', data)
  },

  // 获取对话历史
  getHistory(sessionId: string): Promise<{ session_id: string; messages: ChatMessage[] }> {
    return api.get(`/chat/history/${sessionId}`)
  },

  // 选择Agent
  selectAgent(query: string, patientContext?: Record<string, unknown>): Promise<Agent> {
    return api.post('/chat/agent/select', { query, patient_context: patientContext })
  },

  // 获取所有Agent列表
  getAgents(): Promise<{ agents: Agent[] }> {
    return api.get('/chat/agents')
  },

  // 创建会话
  createSession(patientId?: string): Promise<{ session_id: string }> {
    return api.post('/chat/session/create', { patient_id: patientId })
  },

  // 删除会话
  deleteSession(sessionId: string): Promise<{ success: boolean }> {
    return api.delete(`/chat/session/${sessionId}`)
  },

  // 获取会话列表
  getSessions(patientId?: string, limit?: number): Promise<{
    sessions: Array<{
      id: string
      patient_id: string
      agent_type: string
      title: string
      status: string
      message_count: number
      created_at: string
      updated_at: string
    }>
    count: number
  }> {
    return api.get('/chat/sessions', { params: { patient_id: patientId, limit } })
  },

  // 多Agent会诊
  multiAgentChat(data: ChatRequest): Promise<{
    session_id: string
    query: string
    individual_results: Array<{
      agent_type: string
      response: string
      sources: Array<{ title: string; content: string }>
      safety: Record<string, unknown>
    }>
    summary: string
  }> {
    return api.post('/chat/multi-agent', data)
  },

  // 安全检查
  checkSafety(text: string): Promise<{
    safe: boolean
    level: string
    violations: string[]
    suggestions: string[]
  }> {
    return api.post('/chat/safety/check', null, { params: { text } })
  },

  // Agent对话模式
  agentDialogue(data: {
    message: string
    patient_id?: string
    session_id?: string
    agent_types?: string[]
    max_turns?: number
  }): Promise<{
    session_id: string
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
  }> {
    return api.post('/chat/agent-dialogue', data, { timeout: 180000 })
  },

  // 获取Agent对话
  getAgentDialogue(dialogueId: string): Promise<{
    dialogue_id: string
    turns: Array<{
      turn_index: number
      speaker_agent: string
      speaker_name: string
      content: string
      sources: Array<{ title: string; content: string }>
    }>
  }> {
    return api.get(`/chat/agent-dialogue/${dialogueId}`)
  },

  // 单个Agent回答（用于分步请求）
  singleAgent(data: {
    message: string
    agent_type: string
    patient_id?: string
    use_rag?: boolean
  }): Promise<{
    agent_type: string
    agent_name: string
    response: string
    sources: Array<{ title: string; content: string }>
  }> {
    return api.post('/chat/single-agent', data)
  },

  // 生成总结（用于分步请求后汇总）
  generateSummary(data: {
    query: string
    agent_results: Array<{ agent_type: string; agent_name: string; response: string }>
  }): Promise<{
    summary: string
  }> {
    return api.post('/chat/generate-summary', data)
  },

  // Agent对话SSE流式
  agentDialogueStream(data: {
    message: string
    patient_id?: string
    session_id?: string
    agent_types?: string[]
    max_turns?: number
  }): EventSource {
    const params = new URLSearchParams()
    params.append('message', data.message)
    if (data.patient_id) params.append('patient_id', data.patient_id)
    if (data.session_id) params.append('session_id', data.session_id)
    if (data.agent_types) params.append('agent_types', JSON.stringify(data.agent_types))
    if (data.max_turns) params.append('max_turns', String(data.max_turns))
    
    const url = `${import.meta.env.VITE_API_BASE_URL || '/api/v1'}/chat/agent-dialogue/stream?${params}`
    return new EventSource(url)
  }
}

// ============ Patient API ============

export const patientApi = {
  // 获取患者列表
  getList(params?: { page?: number; page_size?: number; search?: string }): Promise<{
    patients: Patient[]
    total: number
  }> {
    return api.get('/patients', { params })
  },

  // 获取患者详情
  getById(id: string): Promise<Patient> {
    return api.get(`/patients/${id}`)
  },

  // 创建患者
  create(data: Partial<Patient>): Promise<Patient> {
    return api.post('/patients', data)
  },

  // 更新患者
  update(id: string, data: Partial<Patient>): Promise<Patient> {
    return api.put(`/patients/${id}`, data)
  },

  // 删除患者
  delete(id: string): Promise<{ success: boolean }> {
    return api.delete(`/patients/${id}`)
  },

  // 获取患者生命体征
  getVitals(patientId: string, params?: { type?: string; days?: number }): Promise<{
    records: VitalRecord[]
  }> {
    return api.get(`/patients/${patientId}/vitals`, { params })
  },

  // 添加生命体征
  addVital(patientId: string, data: { type: string; value: number; unit: string }): Promise<VitalRecord> {
    return api.post(`/patients/${patientId}/vitals`, data)
  }
}

// ============ Simulation API ============

export const simulationApi = {
  // 运行模拟
  runSimulation(data: SimulationRequest): Promise<{
    success: boolean
    result: SimulationResult
  }> {
    return api.post('/simulation/run', data)
  },

  // 对比干预方案
  compareInterventions(data: Omit<SimulationRequest, 'intervention_type'>): Promise<{
    success: boolean
    results: SimulationResult[]
    best_option: SimulationResult
  }> {
    return api.post('/simulation/compare', data)
  },

  // 获取干预类型
  getInterventionTypes(): Promise<{
    types: Array<{ value: string; name: string }>
  }> {
    return api.get('/simulation/intervention-types')
  },

  // 获取干预效果信息
  getEffectivenessInfo(disease: string): Promise<Record<string, unknown>> {
    return api.get(`/simulation/effectiveness/${disease}`)
  },

  // 获取干预方案详情列表
  getInterventions(disease?: string): Promise<{
    interventions: Array<{
      id: string
      name: string
      type: string
      disease: string
      description: string
      duration_days: number
      effectiveness: number
      risk_level: string
      steps: string[]
      precautions: string[]
    }>
  }> {
    const params = disease ? { disease } : {}
    return api.get('/simulation/interventions', { params })
  }
}

// ============ Knowledge API ============

export interface KnowledgeItem {
  id: string
  title: string
  content: string
  type: string
  tags?: string[]
  source?: string
  author?: string
  status: string
  view_count?: number
  helpful_count?: number
  created_at?: string
  updated_at?: string
  published_at?: string
}

export interface KnowledgeParams {
  search?: string
  type?: string
  status?: string
  page?: number
  page_size?: number
}

export const knowledgeApi = {
  // 获取知识列表
  getList(params: KnowledgeParams): Promise<{
    items: KnowledgeItem[]
    total: number
    page: number
    page_size: number
  }> {
    return api.get('/knowledge/', { params })
  },

  // 获取知识详情
  getById(id: string): Promise<KnowledgeItem> {
    return api.get(`/knowledge/${id}`)
  },

  // 创建知识
  create(data: Partial<KnowledgeItem>): Promise<KnowledgeItem> {
    return api.post('/knowledge/', data)
  },

  // 更新知识
  update(id: string, data: Partial<KnowledgeItem>): Promise<KnowledgeItem> {
    return api.put(`/knowledge/${id}`, data)
  },

  // 删除知识
  delete(id: string): Promise<{ success: boolean }> {
    return api.delete(`/knowledge/${id}`)
  },

  // 点赞知识
  markHelpful(id: string): Promise<{ success: boolean; helpful_count: number }> {
    return api.post(`/knowledge/${id}/helpful`)
  },

  // 获取知识类型列表
  getTypes(): Promise<{
    types: Array<{ value: string; label: string; icon: string }>
  }> {
    return api.get('/knowledge/types/list')
  },

  // 搜索知识
  search(query: string, params?: { type?: string; limit?: number }): Promise<{
    results: KnowledgeItem[]
    total: number
  }> {
    return api.get('/knowledge/search', { params: { query, ...params } })
  },

  // 获取推荐知识
  getRecommendations(patientId: string, limit?: number): Promise<{
    recommendations: KnowledgeItem[]
    total: number
  }> {
    return api.get(`/knowledge/recommendations/${patientId}`, { params: { limit } })
  }
}

// ============ Evaluation API ============

export const evaluationApi = {
  // 运行安全评估
  runEvaluation(agentType: string): Promise<{
    total_tests: number
    passed: number
    failed: number
    pass_rate: number
    results: Array<{
      test_case: { category: string; probe: string; expected: string }
      safety: { level: string; violations: string[] }
      passed: boolean
    }>
  }> {
    return api.post('/evaluation/run', { agent_type: agentType })
  },

  // 获取评估报告
  getReport(evalId: string): Promise<{ report: string }> {
    return api.get(`/evaluation/report/${evalId}`)
  }
}

// ============ 处方 API ============

export interface Medication {
  name: string
  specification: string
  quantity: string
  dosage: string
  usage: string
}

export interface Prescription {
  id: string
  patient_name: string
  id_card: string
  prescription_no: string
  hospital: string
  department: string
  doctor: string
  prescription_date: string
  valid_until: string
  prescription_type: string
  diagnosis: string
  medications: Medication[]
  status: string
  total_amount?: number
  created_at: string
}

export const prescriptionApi = {
  // 查询处方
  query(data: {
    name: string
    id_card: string
    prescription_no?: string
    hospital?: string
    start_date?: string
    end_date?: string
  }): Promise<{
    success: boolean
    count: number
    data: Prescription[]
  }> {
    return api.post('/prescriptions/query', data)
  },

  // 获取处方详情
  getDetail(prescriptionId: string): Promise<{
    success: boolean
    data: Prescription
  }> {
    return api.get(`/prescriptions/detail/${prescriptionId}`)
  },

  // 获取处方类型
  getTypes(): Promise<{
    types: Array<{ value: string; label: string }>
  }> {
    return api.get('/prescriptions/types')
  },

  // 获取处方状态
  getStatusList(): Promise<{
    status: Array<{ value: string; label: string }>
  }> {
    return api.get('/prescriptions/status-list')
  }
}

// ============ 购药记录 API ============

export interface MedicationPurchase {
  id: string
  patient_name: string
  id_card: string
  pharmacy: string
  pharmacy_address?: string
  drug_name: string
  drug_specification: string
  manufacturer?: string
  quantity: number
  unit_price: number
  total_amount: number
  purchase_date: string
  prescription_no?: string
  payment_method?: string
  invoice_no?: string
  pharmacist?: string
  created_at: string
}

export const medicationPurchaseApi = {
  // 查询购药记录
  query(data: {
    name: string
    id_card: string
    pharmacy?: string
    drug_name?: string
    start_date?: string
    end_date?: string
  }): Promise<{
    success: boolean
    count: number
    data: MedicationPurchase[]
  }> {
    return api.post('/medication-purchases/query', data)
  },

  // 获取购药记录详情
  getDetail(purchaseId: string): Promise<{
    success: boolean
    data: MedicationPurchase
  }> {
    return api.get(`/medication-purchases/detail/${purchaseId}`)
  },

  // 获取药店列表
  getPharmacies(): Promise<{
    pharmacies: Array<{ value: string; label: string }>
  }> {
    return api.get('/medication-purchases/pharmacies')
  },

  // 获取购药统计
  getStatistics(name: string, idCard: string): Promise<{
    success: boolean
    data: {
      total_amount: number
      total_times: number
      pharmacies: string[]
      drug_statistics: Record<string, { count: number; amount: number }>
    }
  }> {
    return api.get('/medication-purchases/statistics', { params: { name, id_card: idCard } })
  }
}

// ============ 管理后台 API ============

export const adminApi = {
  // 获取系统统计
  getStats(): Promise<{
    total_patients: number
    total_doctors: number
    total_conversations: number
    active_sessions: number
    today_conversations: number
    avg_response_time: number
    system_health: string
  }> {
    return api.get('/admin/stats')
  },

  // 获取概览统计
  getStatsOverview(): Promise<{
    disease_distribution: Record<string, number>
    age_distribution: Record<string, number>
    agent_usage: Record<string, number>
  }> {
    return api.get('/admin/stats/overview')
  },

  // 获取Agent列表
  getAgents(params?: { status?: string }): Promise<{
    items: Array<{
      id: string
      name: string
      type: string
      description: string
      status: string
      version: string
      conversation_count: number
      satisfaction: number
    }>
    total: number
  }> {
    return api.get('/admin/agents', { params })
  },

  // 更新Agent状态
  updateAgentStatus(agentId: string, status: string): Promise<{ success: boolean }> {
    return api.put(`/admin/agents/${agentId}/status`, { status })
  },

  // 获取评估列表
  getEvaluations(params?: { agent_type?: string; status?: string }): Promise<{
    items: Array<{
      id: string
      agent_type: string
      status: string
      total_cases: number
      pass_rate: number
      created_at: string
    }>
    total: number
  }> {
    return api.get('/admin/evaluations', { params })
  },

  // 创建评估
  createEvaluation(agentType: string): Promise<{
    id: string
    agent_type: string
    status: string
    pass_rate: number
  }> {
    return api.post('/admin/evaluations', { agent_type: agentType })
  },

  // 获取评估报告
  getEvaluationReport(evalId: string): Promise<{
    summary: { total_tests: number; passed: number; failed: number; pass_rate: number }
    safety_assessment: { level: string; violations: Array<{ case: string; severity: string; description: string }> }
    recommendations: string[]
  }> {
    return api.get(`/admin/evaluations/${evalId}/report`)
  },

  // 获取系统健康状态
  getSystemHealth(): Promise<{
    status: string
    uptime: string
    cpu_usage: number
    memory_usage: number
    services: Record<string, string>
  }> {
    return api.get('/admin/system/health')
  },

  // 获取系统日志
  getSystemLogs(params?: { level?: string; skip?: number; limit?: number }): Promise<{
    items: Array<{ level: string; message: string; timestamp: string }>
    total: number
  }> {
    return api.get('/admin/system/logs', { params })
  }
}

// ============ 慢病管理 API ============

export interface FoodItem {
  name: string
  category: string
  gi: number
  carbs_per_100g: number
  serving_size: number
  calories: number
  gl_per_serving: number
}

export interface MealCarbsResult {
  foods: Array<{
    name: string
    weight: number
    carbs: number
    calories: number
    gi: number
    gl: number
  }>
  total_carbs: number
  total_calories: number
  gi: number
  gl: number
}

export interface DailyCarbsResult {
  weight: number
  activity_level: string
  estimated_calories: number
  carbs_grams_min: number
  carbs_grams_max: number
  carbs_grams_typical: number
}

export interface GlucoseTrendResult {
  data_points: number
  average: number
  max: number
  min: number
  std_dev: number
  trend: string
  volatility: string
  tir: number
  anomalies: Array<{ time: string; value: number; type: string }>
  recommendations: string[]
}

export interface RecipeMealResult {
  meal_type: string
  foods: Array<{ name: string; weight: number; carbs: number }>
  total_carbs: number
  total_calories: number
  gi: number
  gl: number
  recommendation: string
}

export interface RecipeDailyResult {
  daily_carbs_target: number
  meals: Record<string, {
    foods: Array<{ name: string; weight: number; carbs: number }>
    target_carbs: number
    actual_carbs: number
    gl: number
    recommendation: string
  }>
  tips: string[]
}

export const chronicApi = {
  // 食物搜索
  searchFood(keyword: string): Promise<{ foods: FoodItem[]; total: number }> {
    return api.get('/chronic/food/search', { params: { keyword } })
  },

  // 按类别获取食物
  getFoodsByCategory(category: string): Promise<{ category: string; foods: FoodItem[]; total: number }> {
    return api.get(`/chronic/food/category/${category}`)
  },

  // 获取低GI食物
  getLowGiFoods(limit?: number): Promise<{ foods: FoodItem[]; total: number }> {
    return api.get('/chronic/food/low-gi', { params: { limit } })
  },

  // 获取食物分类
  getFoodCategories(): Promise<{ categories: string[] }> {
    return api.get('/chronic/food/categories')
  },

  // 获取食物详情
  getFoodDetail(foodName: string): Promise<FoodItem> {
    return api.get(`/chronic/food/${foodName}`)
  },

  // 计算餐食碳水
  calculateMealCarbs(foods: Array<{ name: string; weight: number }>): Promise<MealCarbsResult> {
    return api.post('/chronic/carbs/meal', { foods })
  },

  // 计算每日碳水需求
  calculateDailyCarbs(weight: number, activityLevel: string): Promise<DailyCarbsResult> {
    return api.post('/chronic/carbs/daily-requirement', { weight, activity_level: activityLevel })
  },

  // 计算胰岛素碳水比
  calculateICR(totalDailyInsulin: number, activityLevel?: string): Promise<{
    total_daily_insulin: number
    basic_icr: number
    activity_level: string
    adjusted_icr: number
    description: string
  }> {
    return api.post('/chronic/carbs/insulin-ratio', { total_daily_insulin: totalDailyInsulin, activity_level: activityLevel || 'moderate' })
  },

  // 计算胰岛素敏感因子
  calculateISF(totalDailyInsulin: number): Promise<{
    total_daily_insulin: number
    isf: number
    description: string
  }> {
    return api.post('/chronic/carbs/correction-factor', { total_daily_insulin: totalDailyInsulin })
  },

  // 计算餐时胰岛素
  calculateMealInsulin(preMealGlucose: number, targetGlucose: number, totalCarbs: number, icr: number, isf: number): Promise<{
    pre_meal_glucose: number
    target_glucose: number
    total_carbs: number
    carb_dose: number
    correction_dose: number
    total_dose: number
    recommendation: string
  }> {
    return api.post('/chronic/carbs/meal-insulin', {
      pre_meal_glucose: preMealGlucose,
      target_glucose: targetGlucose,
      total_carbs: totalCarbs,
      icr,
      isf
    })
  },

  // 分析血糖趋势
  analyzeGlucoseTrend(glucoseData: Array<{ time: string; value: number; type?: string }>): Promise<GlucoseTrendResult> {
    return api.post('/chronic/glucose/trend', { glucose_data: glucoseData })
  },

  // 检测血糖模式
  detectGlucosePatterns(glucoseData: Array<{ time: string; value: number; type?: string }>): Promise<{
    patterns: Array<{ type: string; description: string; severity: string }>
    has_issues: boolean
  }> {
    return api.post('/chronic/glucose/patterns', { glucose_data: glucoseData })
  },

  // 生成餐食计划
  generateMealPlan(patientInfo: { weight: number; activity: string; prefer_foods?: string[] }, mealType: string, targetCarbs: number): Promise<RecipeMealResult> {
    return api.post('/chronic/recipe/meal', { patient_info: patientInfo, meal_type: mealType, target_carbs: targetCarbs })
  },

  // 生成每日食谱
  generateDailyPlan(patientInfo: { weight: number; activity: string; prefer_foods?: string[] }): Promise<RecipeDailyResult> {
    return api.post('/chronic/recipe/daily', { patient_info: patientInfo })
  },

  // 获取健康建议
  getHealthTips(): Promise<{
    tips: Array<{ category: string; tips: string[] }>
  }> {
    return api.get('/chronic/health/tips')
  },

  // 获取血糖控制目标
  getGlucoseTargets(): Promise<{
    targets: Record<string, { min: number; max: number; unit: string }>
    remarks: Record<string, string>
  }> {
    return api.get('/chronic/glucose/target-ranges')
  },

  // 获取食物份量指南
  getPortionGuide(): Promise<{
    guide: Array<{ food_type: string; portion: string; examples: string }>
    tips: string
  }> {
    return api.get('/chronic/carbs/portion-guide')
  }
}

// ============ Family API ============

export interface Family {
  id: string
  name: string
  owner_id: string
  created_at: string
}

export interface FamilyMember {
  id: string
  family_id: string
  user_id: string
  user_name: string
  role: string
  relationship: string
  patient_id?: string
  joined_at: string
}

export const familyApi = {
  getUserFamilies(userId: string): Promise<{ success: boolean; families: Family[] }> {
    return api.get(`/family/user/${userId}/families`)
  },

  createFamily(data: { name: string; owner_id: string; owner_name: string }): Promise<{ success: boolean; family: Family }> {
    return api.post('/family/create', data)
  },

  getFamilyMembers(familyId: string): Promise<{ success: boolean; members: FamilyMember[] }> {
    return api.get(`/family/${familyId}/members`)
  },

  addMember(data: { family_id: string; user_id: string; user_name: string; role: string; relationship: string }): Promise<{ success: boolean }> {
    return api.post('/family/member/add', data)
  },

  getPatientHealthSummary(patientId: string): Promise<{ success: boolean; summary: Record<string, unknown> }> {
    return api.get(`/family/patient/${patientId}/health-summary`)
  },

  getUnreadMessages(userId: string): Promise<{ success: boolean; messages: Array<{ id: string; from_user_name: string; content: string; is_read: boolean; created_at: string }> }> {
    return api.get(`/family/message/${userId}/unread`)
  }
}

// ============ Recipe API ============

export interface DetectedIngredient {
  name: string
  confidence: number
}

export interface GeneratedRecipe {
  id?: string
  title: string
  description: string
  ingredients: Array<{ name: string; amount: string }>
  steps: Array<{ step: number; description: string; tip?: string }>
  nutrition?: { calories: number; protein: number; carbs: number; fat?: number }
  cooking_time: number
  difficulty: string
  tips?: string[]
}

export const recipeApi = {
  detectImage(imageBase64: string): Promise<{ success: boolean; ingredients: DetectedIngredient[]; message?: string }> {
    return api.post('/recipe/detect-image', { image: imageBase64 })
  },

  detectText(text: string): Promise<{ success: boolean; ingredients: DetectedIngredient[] }> {
    return api.post('/recipe/detect-text', { text })
  },

  generate(data: { ingredients: string[]; preferences?: Record<string, unknown> }): Promise<{ success: boolean; recipe: GeneratedRecipe }> {
    return api.post('/recipe/generate', data)
  },

  createFamilyRecipe(data: { family_id: string; creator_id: string; creator_name: string; title: string; description?: string; ingredients: Array<{ name: string; amount: string }>; steps: Array<{ step: number; description: string; tip?: string }>; cooking_time: number; difficulty: string; nutrition?: Record<string, number>; is_shared: boolean }): Promise<{ success: boolean; recipe: GeneratedRecipe }> {
    return api.post('/recipe/family/create', data)
  },

  getFamilyRecipes(familyId: string): Promise<{ success: boolean; recipes: Array<{ id: string; title: string; description?: string; creator_name: string; is_legacy: boolean }> }> {
    return api.get(`/recipe/family/${familyId}/list`)
  },

  getRecipeDetail(recipeId: string): Promise<{ success: boolean; recipe: GeneratedRecipe }> {
    return api.get(`/recipe/${recipeId}`)
  }
}

// ============ Health Data API ============

export interface HealthRecord {
  id: string
  patient_id: string
  type: string
  value: number
  unit: string
  recorded_at: string
  notes?: string
}

export const healthApi = {
  addRecord(data: { patient_id: string; type: string; value: number; unit: string; notes?: string }): Promise<{ success: boolean; record: HealthRecord }> {
    return api.post('/health/record/add', data)
  },

  getRecords(patientId: string, params?: { type?: string; days?: number }): Promise<{ success: boolean; records: HealthRecord[] }> {
    return api.get(`/health/records/${patientId}`, { params })
  },

  getTrends(patientId: string, type: string): Promise<{ success: boolean; trend: { data: Array<{ date: string; value: number }>; avg: number; min: number; max: number; trend: string } }> {
    return api.get(`/health/trends/${patientId}`, { params: { type } })
  },

  getAlerts(patientId: string): Promise<{ success: boolean; alerts: Array<{ id: string; type: string; title: string; content: string; severity: string; created_at: string }> }> {
    return api.get(`/health/alerts/${patientId}`)
  }
}

// ============ Prediction API ============

export interface HealthPrediction {
  id: string
  patient_id: string
  type: string
  prediction_date: string
  prediction_result: {
    risk_level: string
    probability: number
    trend: string
    factors: string[]
    recommendations: string[]
  }
  created_at: string
}

export interface InterventionPrediction {
  intervention_type: string
  intervention_name: string
  predicted_effect: {
    blood_sugar_change: number
    blood_pressure_change?: number
    weight_change?: number
    confidence: number
  }
  timeline: Array<{ day: number; predicted_value: number }>
  recommendations: string[]
}

export const predictionApi = {
  predictBloodSugar(patientId: string, days: number): Promise<{ success: boolean; prediction: HealthPrediction }> {
    return api.post('/prediction/blood-sugar', { patient_id: patientId, days })
  },

  predictComplication(patientId: string, complicationType: string): Promise<{ success: boolean; prediction: { risk_level: string; probability: number; factors: string[]; recommendations: string[] } }> {
    return api.post('/prediction/complication', { patient_id: patientId, complication_type: complicationType })
  },

  predictInterventionEffect(patientId: string, interventionType: string): Promise<{ success: boolean; prediction: InterventionPrediction }> {
    return api.post('/prediction/intervention-effect', { patient_id: patientId, intervention_type: interventionType })
  },

  getPredictionHistory(patientId: string, params?: { type?: string; limit?: number }): Promise<{ success: boolean; predictions: HealthPrediction[] }> {
    return api.get(`/prediction/history/${patientId}`, { params })
  }
}

// ============ Agent Config API ============

export interface AgentLLMConfig {
  agent_type: string
  agent_name: string
  agent_description: string
  agent_emoji: string
  agent_color: string
  provider: string
  model: string
  temperature: number
  max_tokens: number
  timeout: number
  fallback_provider: string | null
  fallback_model: string | null
  config_source: string
  is_active: boolean
  updated_at: string
}

export interface LLMProviderInfo {
  id: string
  name: string
  models: string[]
  configured: boolean
  api_key_hint: string
}

export interface EnvLLMInfo {
  default_provider: string
  default_model: string
  providers: LLMProviderInfo[]
}

export const agentConfigApi = {
  getAgentConfigs(): Promise<{ configs: AgentLLMConfig[]; total: number }> {
    return api.get('/admin/agent-configs')
  },

  getAgentConfig(agentType: string): Promise<AgentLLMConfig> {
    return api.get(`/admin/agent-configs/${agentType}`)
  },

  updateAgentConfig(agentType: string, data: Partial<AgentLLMConfig>): Promise<AgentLLMConfig> {
    return api.put(`/admin/agent-configs/${agentType}`, data)
  },

  syncFromYaml(): Promise<{ synced: number; agents: string[] }> {
    return api.post('/admin/agent-configs/sync-from-yaml')
  },

  resetAgentConfig(agentType: string): Promise<{ success: boolean; message: string }> {
    return api.post(`/admin/agent-configs/${agentType}/reset`)
  },

  getProviders(): Promise<{ providers: LLMProviderInfo[] }> {
    return api.get('/admin/agent-configs/providers/list')
  },

  getEnvInfo(): Promise<EnvLLMInfo> {
    return api.get('/admin/agent-configs/env-info')
  },

  testConnection(data: { provider: string; model: string; temperature?: number }): Promise<{
    success: boolean
    provider: string
    model: string
    response_preview: string
    elapsed_seconds: number
    message: string
    error?: string
  }> {
    return api.post('/admin/agent-configs/test-connection', data)
  }
}

// ============ 处方审核 API ============

export interface PrescriptionReviewIssue {
  type: string
  severity: string
  drugs: string[]
  detail: string
  recommendation: string
  layer?: string
}

export interface PrescriptionReviewSuggestion {
  type: string
  drug?: string
  alternative?: string
  category?: string
  reimbursement_rate?: number
  detail: string
  layer?: string
}

export interface PrescriptionReviewResult {
  review_id: string
  status: string
  layers: {
    rule_engine: { status: string; issues: PrescriptionReviewIssue[]; suggestions: PrescriptionReviewSuggestion[] }
    insurance_policy: { status: string; issues: PrescriptionReviewIssue[]; suggestions: PrescriptionReviewSuggestion[]; coverage: Array<{ drug: string; category: string; reimbursement_rate: number; restrictions: string | null }> }
    individualized: { status: string; issues: PrescriptionReviewIssue[]; suggestions: PrescriptionReviewSuggestion[] }
  }
  all_issues: PrescriptionReviewIssue[]
  all_suggestions: PrescriptionReviewSuggestion[]
  summary: string
  reviewed_at: string
}

export const prescriptionReviewApi = {
  reviewPrescription(data: {
    patient_id: string
    medications: Array<{ drug_name: string; dosage: string; frequency: string; route?: string }>
    diagnosis?: string[]
    patient_context?: Record<string, unknown>
  }): Promise<PrescriptionReviewResult> {
    return api.post('/prescription/review/review', data)
  },

  getReviewResult(reviewId: string): Promise<{
    review_id: string
    results: Array<{
      reviewer_type: string
      status: string
      issues: Record<string, unknown>
      suggestions: Record<string, unknown>
      reviewed_at: string
    }>
  }> {
    return api.get(`/prescription/review/result/${reviewId}`)
  }
}

// ============ 患者画像 API ============

export interface PatientPanorama {
  patient_id: string
  patient_name: string
  generated_at: string
  chronic_diseases: Array<{ disease: string; diagnosed_date: string | null; control_status: string }>
  current_medications: Array<{ drug: string; dosage: string | null; frequency: string | null }>
  vital_trends: Record<string, { latest: unknown; trend: string; target: string | null; data_points: number }>
  interventions: Array<{ type: string; date: string | null; detail: string }>
  missing_indicators: Array<{ indicator: string; missing_days: number; severity: string }>
  risk_prediction: { complication_risk: string; hospitalization_risk: string }
}

export const patientProfileApi = {
  getPanorama(patientId: string): Promise<PatientPanorama> {
    return api.get(`/patients/${patientId}/panorama`)
  }
}

// ============ 数据挖掘 API ============

export interface DiseaseTrajectoryResult {
  patient_id?: string
  time_range: string
  trajectory: Array<{ date: string; values: Record<string, unknown> }>
  transition_matrix: { states: string[]; matrix: number[][] }
  data_points: number
  disease_distribution?: Array<{ disease: string; count: number }>
}

export interface IndicatorPatternResult {
  patient_id: string
  patterns: Record<string, {
    values: Array<{ date: string; value: number }>
    mean: number
    std: number
    min: number
    max: number
    correlations: Record<string, number>
    seasonality: { detected: boolean; period: number | null; autocorrelation: number }
    message?: string
  }>
}

export interface WhatIfResult {
  patient_id: string
  intervention: Record<string, unknown>
  baseline: Record<string, number>
  prediction: Array<{ month: number; blood_sugar: number; risk_level: string }>
  shap_values: Record<string, number>
  confidence: number
}

export interface ComorbidityResult {
  network: {
    nodes: Array<{ id: string; count: number; prevalence: number }>
    edges: Array<{ source: string; target: string; weight: number; pmi: number }>
  }
  communities: Array<{ id: number; members: string[]; size: number }>
  total_patients: number
}

export interface EpidemiologyResult {
  indicator: string
  mean: number
  std: number
  alerts: Array<{ patient_id: string; value: number; z_score: number; severity: string }>
  affected_patients: number
  total_records: number
}

export const dataMiningApi = {
  diseaseTrajectory(data: { patient_id?: string; time_range?: string }): Promise<DiseaseTrajectoryResult> {
    return api.post('/data-mining/disease-trajectory', data)
  },

  indicatorPattern(data: { patient_id: string; indicators?: string[] }): Promise<IndicatorPatternResult> {
    return api.post('/data-mining/indicator-pattern', data)
  },

  whatifSimulation(data: { patient_id: string; intervention: Record<string, unknown> }): Promise<WhatIfResult> {
    return api.post('/data-mining/whatif-simulation', data)
  },

  comorbidityNetwork(data: { patient_ids?: string[]; min_support?: number }): Promise<ComorbidityResult> {
    return api.post('/data-mining/comorbidity-network', data)
  },

  epidemiologyAlert(data: { region?: string; indicator?: string; threshold?: number }): Promise<EpidemiologyResult> {
    return api.post('/data-mining/epidemiology-alert', data)
  },

  getResult(taskId: string): Promise<{
    task_id: string
    query_type: string
    result: Record<string, unknown>
    computed_at: string
  }> {
    return api.get(`/data-mining/results/${taskId}`)
  }
}

// ============ 管理报表 API ============

export interface MacroStats {
  total_patients: number
  new_this_month: number
  active_patients: number
  active_rate: number
}

export interface DiseaseDistribution {
  by_disease: Array<{ disease: string; count: number }>
}

export interface AdherenceStats {
  overall_rate: number
  total_records: number
  taken_records: number
}

export interface ResourceUtilization {
  total_prescriptions: number
  avg_medications_per_patient: number
}

export interface DashboardOverview {
  total_patients: number
  active_patients: number
  top_diseases: Array<{ disease: string; count: number }>
}

export const dashboardApi = {
  getMacroStats(): Promise<MacroStats> {
    return api.get('/dashboard/macro-stats')
  },

  getDiseaseDistribution(): Promise<DiseaseDistribution> {
    return api.get('/dashboard/disease-distribution')
  },

  getAdherenceStats(): Promise<AdherenceStats> {
    return api.get('/dashboard/adherence-stats')
  },

  getResourceUtilization(): Promise<ResourceUtilization> {
    return api.get('/dashboard/resource-utilization')
  },

  getOverview(): Promise<DashboardOverview> {
    return api.get('/dashboard/overview')
  }
}

// ============ 工作流 API ============

export interface WorkflowStatus {
  status: string
  available_stages: string[]
  available_agents: string[]
  version: string
}

export interface PipelineResult {
  success: boolean
  results?: Record<string, unknown>
  final_output?: string
  iterations?: number
  error?: string
}

export const workflowApi = {
  getStatus(): Promise<WorkflowStatus> {
    return api.get('/workflow/status')
  },

  executePipeline(data: {
    task: string
    stages?: string[]
    max_iterations?: number
    quality_threshold?: number
    context?: Record<string, unknown>
  }): Promise<PipelineResult> {
    return api.post('/workflow/pipeline', data)
  },

  getAgents(): Promise<{
    total: number
    agents: Array<{
      type: string
      name: string
      role: string
      specialty: string[]
      emoji: string
      color: string
      llm_provider: string
      llm_model: string
    }>
  }> {
    return api.get('/workflow/agents')
  }
}

// ============ 健康计划 API ============

export interface HealthPlanGoal {
  description: string
  target?: string
  achieved: boolean
}

export interface HealthPlanMilestone {
  description: string
  target_date?: string
  completed: boolean
}

export interface HealthPlanItem {
  id: string
  patient_id: string
  plan_type: string
  goals: HealthPlanGoal[]
  milestones: HealthPlanMilestone[]
  status: string
  start_date: string | null
  end_date: string | null
  created_at: string | null
}

export const healthPlanApi = {
  getPatientPlans(patientId: string, status?: string): Promise<{ plans: HealthPlanItem[] }> {
    return api.get(`/health-plans/patient/${patientId}`, { params: { status } })
  },

  createPlan(data: {
    patient_id: string
    plan_type: string
    goals?: Array<{ description: string; target?: string; achieved?: boolean }>
    milestones?: Array<{ description: string; target_date?: string; completed?: boolean }>
    start_date?: string
    end_date?: string
  }): Promise<HealthPlanItem> {
    return api.post('/health-plans/create', data)
  },

  updatePlan(planId: string, data: {
    status?: string
    goals?: Array<{ description: string; target?: string; achieved?: boolean }>
    milestones?: Array<{ description: string; target_date?: string; completed?: boolean }>
  }): Promise<Partial<HealthPlanItem>> {
    return api.put(`/health-plans/${planId}`, data)
  },

  deletePlan(planId: string): Promise<{ success: boolean }> {
    return api.delete(`/health-plans/${planId}`)
  }
}

// ============ 导出 ============

export default api
