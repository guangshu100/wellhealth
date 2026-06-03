// 康伴健康小程序 - API模块
// 对接后端WellHealth API

const BASE_URL = 'http://localhost:8000/api/v1'

interface RequestOptions {
  url: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: any
  header?: Record<string, string>
}

interface ApiResponse<T = any> {
  code: number
  data: T
  message: string
}

// 封装请求方法
const request = <T = any>(options: RequestOptions): Promise<T> => {
  return new Promise((resolve, reject) => {
    const token = uni.getStorageSync('token')

    const data = options.data || {}
    Object.keys(data).forEach(key => {
      if (data[key] === undefined) {
        delete data[key]
      }
    })

    uni.request({
      url: BASE_URL + options.url,
      method: options.method || 'GET',
      data: data,
      header: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
        ...options.header
      },
      success: (res) => {
        if (res.statusCode === 200) {
          resolve(res.data as T)
        } else if (res.statusCode === 401) {
          uni.removeStorageSync('token')
          uni.reLaunch({ url: '/pages/login/login' })
          reject(new Error('未授权'))
        } else {
          uni.showToast({
            title: (res.data as ApiResponse)?.message || '请求失败',
            icon: 'none'
          })
          reject(res.data)
        }
      },
      fail: (err) => {
        uni.showToast({
          title: '网络请求失败',
          icon: 'none'
        })
        reject(err)
      }
    })
  })
}

// ============ 患者端用户API ============
export const userApi = {
  // 微信登录
  wechatLogin: (code: string) => request<{
    token: string
    token_type: string
    expires_in: number
    user: any
  }>({
    url: '/users/wechat-login',
    method: 'POST',
    data: { code }
  }),

  // 账号密码登录
  login: (username: string, password: string, captchaKey?: string, captchaCode?: string) => request<{
    token: string
    token_type: string
    expires_in: number
    user: any
  }>({
    url: '/users/login',
    method: 'POST',
    data: { username, password, captcha_key: captchaKey, captcha_code: captchaCode }
  }),

  // 邮箱验证码登录
  emailLogin: (email: string, code: string, captchaKey?: string, captchaCode?: string) => request<{
    token: string
    token_type: string
    expires_in: number
    user: any
  }>({
    url: '/users/email-login',
    method: 'POST',
    data: { email, code, captcha_key: captchaKey, captcha_code: captchaCode }
  }),

  // 注册
  register: (data: {
    username: string
    password: string
    name: string
    phone?: string
    email?: string
  }) => request<{
    token: string
    token_type: string
    expires_in: number
    user: any
  }>({
    url: '/users/register',
    method: 'POST',
    data
  }),
  
  // 获取用户信息
  getUserInfo: () => request<any>({
    url: '/users/me'
  }),
  
  // 更新用户信息
  updateUserInfo: (data: any) => request<any>({
    url: '/users/me',
    method: 'PUT',
    data
  }),

  // 修改密码
  changePassword: (oldPassword: string, newPassword: string) => request<any>({
    url: '/users/change-password',
    method: 'POST',
    data: { old_password: oldPassword, new_password: newPassword }
  }),
  
  // 绑定患者
  bindPatient: (patientId: string) => request<any>({
    url: `/users/bind-patient?patient_id=${patientId}`,
    method: 'POST'
  })
}

// ============ 患者API ============
export const patientApi = {
  // 获取当前绑定的患者信息
  getMyPatient: () => request<any>({
    url: '/patients/my/detail'
  }),
  
  // 获取患者详情
  getPatientDetail: (id: string) => request<any>({
    url: `/patients/${id}`
  }),
  
  // 获取患者列表
  getPatientList: (params?: { page?: number; page_size?: number; search?: string }) => request<{
    patients: Array<any>
    total: number
  }>({
    url: '/patients',
    method: 'GET',
    data: params
  }),
  
  // 创建患者
  createPatient: (data: any) => request<any>({
    url: '/patients',
    method: 'POST',
    data
  }),
  
  // 更新患者
  updatePatient: (id: string, data: any) => request<any>({
    url: `/patients/${id}`,
    method: 'PUT',
    data
  }),
  
  // 删除患者
  deletePatient: (id: string) => request<any>({
    url: `/patients/${id}`,
    method: 'DELETE'
  }),
  
  // 获取患者健康档案
  getHealthRecord: (patientId: string) => request<any>({
    url: `/patients/${patientId}/profile`
  }),
  
  // 获取患者疾病列表
  getPatientDiseases: (patientId: string) => request<any>({
    url: `/patients/${patientId}/diseases`
  }),
  
  // 获取患者用药列表
  getPatientMedications: (patientId: string) => request<any>({
    url: `/patients/${patientId}/medications`
  }),
  
  // 获取患者体征列表
  getPatientVitals: (patientId: string, params?: { vital_type?: string; days?: number }) => request<any>({
    url: `/patients/${patientId}/vitals`,
    method: 'GET',
    data: params
  }),
  
  // 添加体征记录
  addVital: (patientId: string, data: any) => request<any>({
    url: `/patients/${patientId}/vitals`,
    method: 'POST',
    data
  }),
  
  // 更新健康档案
  updateHealthRecord: (patientId: string, data: any) => request<any>({
    url: `/patients/${patientId}/profile`,
    method: 'PUT',
    data
  })
}

// ============ 生命体征API ============
export const vitalsApi = {
  // 获取生命体征记录
  getVitals: (patientId: string, params?: { type?: string; days?: number }) => request<{
    records: Array<{
      id: string
      type: string
      value: number
      unit: string
      recorded_at: string
    }>
  }>({
    url: `/patients/${patientId}/vitals`,
    method: 'GET',
    data: params
  }),
  
  // 添加生命体征
  addVital: (patientId: string, data: { type: string; value: number; unit: string }) => request<any>({
    url: `/patients/${patientId}/vitals`,
    method: 'POST',
    data
  })
}

// ============ 用药提醒API ============
export const medicationReminderApi = {
  // 获取用药提醒列表
  getReminders: (patientId: string) => request<Array<{
    id: string
    patient_id: string
    drug_name: string
    dosage: string
    frequency: string
    times: string[]
    start_date: string
    end_date?: string
    enabled: boolean
    created_at: string
  }>>({
    url: `/patients/${patientId}/medication-reminders`,
    method: 'GET'
  }),
  
  // 添加用药提醒
  addReminder: (patientId: string, data: {
    drug_name: string
    dosage: string
    frequency: string
    times: string[]
    start_date: string
    end_date?: string
  }) => request<any>({
    url: `/patients/${patientId}/medication-reminders`,
    method: 'POST',
    data
  }),
  
  // 更新用药提醒
  updateReminder: (patientId: string, reminderId: string, data: any) => request<any>({
    url: `/patients/${patientId}/medication-reminders/${reminderId}`,
    method: 'PUT',
    data
  }),
  
  // 删除用药提醒
  deleteReminder: (patientId: string, reminderId: string) => request<any>({
    url: `/patients/${patientId}/medication-reminders/${reminderId}`,
    method: 'DELETE'
  }),
  
  // 标记已服药
  markTaken: (patientId: string, reminderId: string, takenTime: string) => request<any>({
    url: `/patients/${patientId}/medication-reminders/${reminderId}/mark-taken`,
    method: 'POST',
    data: { taken_time: takenTime }
  }),
  
  // 获取服药记录
  getMedicationHistory: (patientId: string, params?: { days?: number }) => request<{
    records: Array<{
      id: string
      drug_name: string
      dosage: string
      scheduled_time: string
      taken_time?: string
      status: string
    }>
  }>({
    url: `/patients/${patientId}/medication-history`,
    method: 'GET',
    data: params
  })
}

// ============ 体检报告API ============
export const reportApi = {
  // 获取体检报告列表
  getReports: (patientId: string) => request<Array<{
    id: string
    patient_id: string
    title: string
    report_type: string
    hospital?: string
    exam_date: string
    status: string
    created_at: string
  }>>({
    url: `/patients/${patientId}/reports`,
    method: 'GET'
  }),
  
  // 获取体检报告详情
  getReportDetail: (patientId: string, reportId: string) => request<{
    id: string
    patient_id: string
    title: string
    report_type: string
    hospital?: string
    exam_date: string
    items: Array<{
      name: string
      value: number
      unit: string
      reference_min: number
      reference_max: number
      status: string
    }>
    ai_analysis?: string
    recommendations?: string[]
    created_at: string
  }>({
    url: `/patients/${patientId}/reports/${reportId}`,
    method: 'GET'
  }),
  
  // 上传体检报告
  uploadReport: (patientId: string, data: {
    title: string
    report_type: string
    hospital?: string
    exam_date: string
    file_path?: string
  }) => request<any>({
    url: `/patients/${patientId}/reports`,
    method: 'POST',
    data
  }),
  
  // AI分析体检报告
  analyzeReport: (patientId: string, reportId: string) => request<{
    analysis: string
    recommendations: string[]
    risk_alerts: string[]
  }>({
    url: `/patients/${patientId}/reports/${reportId}/analyze`,
    method: 'POST'
  }),
  
  // 手动录入体检数据
  manualInput: (patientId: string, reportId: string, items: Array<{
    name: string
    value: number
    unit: string
  }>) => request<any>({
    url: `/patients/${patientId}/reports/${reportId}/manual-input`,
    method: 'POST',
    data: { items }
  })
}

// ============ 问答API ============
export const chatApi = {
  // 创建会话
  createSession: (patientId?: string) => request<{
    session_id: string
  }>({
    url: '/chat/session/create',
    method: 'POST',
    data: { patient_id: patientId }
  }),

  // 获取会话列表
  getSessions: (patientId?: string, limit?: number) => request<{
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
  }>({
    url: '/chat/sessions',
    method: 'GET',
    data: { patient_id: patientId, limit }
  }),

  // 删除会话
  deleteSession: (sessionId: string) => request<{
    success: boolean
  }>({
    url: `/chat/session/${sessionId}`,
    method: 'DELETE'
  }),

  // 更新会话标题
  updateSessionTitle: (sessionId: string, title: string) => request<{
    success: boolean
  }>({
    url: `/chat/session/${sessionId}`,
    method: 'PUT',
    data: { title }
  }),

  // 发送消息
  sendMessage: (data: {
    session_id?: string
    patient_id?: string
    message: string
    agent_type?: string
    use_rag?: boolean
  }) => request<{
    session_id: string
    message: string
    agent_type: string
    sources: Array<{ title: string; content: string }>
  }>({
    url: '/chat/send',
    method: 'POST',
    data
  }),

  // 获取对话历史
  getHistory: (sessionId: string) => request<{
    session_id: string
    messages: Array<{ role: string; content: string; timestamp: string }>
  }>({
    url: `/chat/history/${sessionId}`,
    method: 'GET'
  }),
  
  // 选择合适的Agent
  selectAgent: (query: string, patientContext?: Record<string, any>) => request<{
    agent_type: string
    agent_name: string
    description: string
  }>({
    url: '/chat/agent/select',
    method: 'POST',
    data: { query, patient_context: patientContext }
  }),
  
  // 获取所有Agent列表
  getAgents: () => request<{
    agents: Array<{
      type: string
      name: string
      description: string
      color: string
      emoji: string
    }>
  }>({
    url: '/chat/agents',
    method: 'GET'
  }),
  
  // Agent对话模式 - SSE流式 (GET)
  agentDialogueStream: (data: {
    message: string
    patient_id?: string
    session_id?: string
    agent_types?: string[]
    max_turns?: number
  }): Promise<any> => {
    const params = new URLSearchParams()
    params.append('message', data.message)
    if (data.session_id) params.append('session_id', data.session_id)
    if (data.patient_id) params.append('patient_id', data.patient_id)
    if (data.agent_types) params.append('agent_types', JSON.stringify(data.agent_types))
    if (data.max_turns) params.append('max_turns', String(data.max_turns))
    
    return request({
      url: `/chat/agent-dialogue/stream?${params.toString()}`,
      method: 'GET'
    })
  },

  // Agent对话模式 (兼容POST)
  agentDialogue: (data: {
    message: string
    patient_id?: string
    session_id?: string
    agent_types?: string[]
    max_turns?: number
  }) => request<{
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
  }>({
    url: '/chat/agent-dialogue',
    method: 'POST',
    data
  }),
  
  // 获取Agent对话
  getAgentDialogue: (dialogueId: string) => request<{
    dialogue_id: string
    turns: Array<{
      turn_index: number
      speaker_agent: string
      speaker_name: string
      content: string
      sources: Array<{ title: string; content: string }>
    }>
  }>({
    url: `/chat/agent-dialogue/${dialogueId}`,
    method: 'GET'
  })
}

// ============ 干预模拟API ============
export const simulationApi = {
  // 运行干预效果模拟
  runSimulation: (data: {
    patient_id: string
    disease: string
    current_vitals: Record<string, number>
    intervention_type: string
  }) => request<{
    success: boolean
    result: {
      intervention: { type: string; name: string; description: string; duration_days: number }
      status: string
      baseline: Record<string, number>
      predicted: Record<string, number>
      timeline: Array<Record<string, number>>
      effectiveness: number
      risk_level: string
      recommendations: string[]
    }
  }>({
    url: '/simulation/run',
    method: 'POST',
    data
  }),
  
  // 获取干预类型
  getInterventionTypes: () => request<{
    types: Array<{ value: string; name: string }>
  }>({
    url: '/simulation/intervention-types',
    method: 'GET'
  })
}

// ============ 知识库API ============
export const knowledgeApi = {
  // 搜索知识
  search: (query: string, topK: number = 5) => request<{
    results: Array<{
      id: string
      title: string
      content: string
      type: string
      relevance: number
    }>
  }>({
    url: '/knowledge/search',
    method: 'GET',
    data: { query, top_k: topK }
  }),
  
  // 获取推荐知识
  getRecommendations: (patientId: string) => request<{
    recommendations: Array<{
      id: string
      title: string
      content: string
      reason: string
    }>
  }>({
    url: `/knowledge/recommendations/${patientId}`,
    method: 'GET'
  })
}

// ============ 处方API ============
export const prescriptionApi = {
  // 查询处方列表
  query: (data: {
    name: string
    id_card: string
    prescription_no?: string
    hospital?: string
    start_date?: string
    end_date?: string
  }) => request<{
    success: boolean
    count: number
    data: Array<{
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
      medications: Array<{
        name: string
        specification: string
        quantity: string
        dosage: string
        usage: string
      }>
      status: string
      total_amount?: number
      created_at: string
    }>
  }>({
    url: '/prescriptions/query',
    method: 'POST',
    data
  }),
  
  // 获取处方详情
  getDetail: (prescriptionId: string) => request<{
    success: boolean
    data: {
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
      medications: Array<{
        name: string
        specification: string
        quantity: string
        dosage: string
        usage: string
      }>
      status: string
      total_amount?: number
      created_at: string
    }
  }>({
    url: `/prescriptions/detail/${prescriptionId}`,
    method: 'GET'
  }),
  
  // 获取处方类型列表
  getTypes: () => request<{
    types: Array<{ value: string; label: string }>
  }>({
    url: '/prescriptions/types',
    method: 'GET'
  }),
  
  // 获取处方状态列表
  getStatusList: () => request<{
    status: Array<{ value: string; label: string }>
  }>({
    url: '/prescriptions/status-list',
    method: 'GET'
  })
}

// ============ 购药记录API ============
export const medicationPurchaseApi = {
  // 查询购药记录列表
  query: (data: {
    name: string
    id_card: string
    pharmacy?: string
    drug_name?: string
    start_date?: string
    end_date?: string
  }) => request<{
    success: boolean
    count: number
    data: Array<{
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
    }>
  }>({
    url: '/medication-purchases/query',
    method: 'POST',
    data
  }),
  
  // 获取购药记录详情
  getDetail: (purchaseId: string) => request<{
    success: boolean
    data: {
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
  }>({
    url: `/medication-purchases/detail/${purchaseId}`,
    method: 'GET'
  }),
  
  // 获取药店列表
  getPharmacies: () => request<{
    pharmacies: Array<{ value: string; label: string }>
  }>({
    url: '/medication-purchases/pharmacies',
    method: 'GET'
  }),
  
  // 获取购药统计
  getStatistics: (name: string, idCard: string) => request<{
    success: boolean
    data: {
      total_amount: number
      total_times: number
      pharmacies: string[]
      drug_statistics: Record<string, { count: number; amount: number }>
    }
  }>({
    url: '/medication-purchases/statistics',
    method: 'GET',
    data: { name, id_card: idCard }
  })
}

// ============ 卡路里API ============
export const calorieApi = {
  // 分析食物图片
  analyzeImage: (imageBase64: string) => {
    return new Promise((resolve, reject) => {
      uni.request({
        url: BASE_URL + '/calorie/analyze-image',
        method: 'POST',
        header: {
          'Content-Type': 'multipart/form-data'
        },
        formData: {
          image: imageBase64
        },
        success: (res) => {
          if (res.statusCode === 200) {
            resolve(res.data)
          } else {
            reject(res.data)
          }
        },
        fail: reject
      })
    })
  },

  // 文字分析食物
  analyzeText: (description: string) => request<any>({
    url: '/calorie/analyze',
    method: 'POST',
    data: { food_description: description }
  }),

  // 添加食物记录
  addRecord: (data: {
    patient_id: string
    food_name: string
    calories: number
    protein: number
    carbs: number
    fat: number
    fiber: number
    serving_size: number
    meal_type: string
  }) => request<any>({
    url: '/calorie/record',
    method: 'POST',
    data
  }),

  // 获取食物记录
  getRecords: (patientId: string) => request<{
    records: Array<{
      id: string
      patient_id: string
      food_name: string
      calories: number
      protein: number
      carbs: number
      fat: number
      fiber: number
      serving_size: number
      meal_type: string
      record_date: string
      created_at: string
    }>
  }>({
    url: `/calorie/records/${patientId}`,
    method: 'GET'
  }),

  // 删除食物记录
  deleteRecord: (patientId: string, recordId: string) => request<any>({
    url: `/calorie/record/${recordId}?patient_id=${patientId}`,
    method: 'DELETE'
  }),

  // 获取营养摘要
  getSummary: (patientId: string, days: number = 7) => request<any>({
    url: `/calorie/summary/${patientId}?days=${days}`,
    method: 'GET'
  })
}

// ============ 多Agent会诊API ============
export const multiAgentApi = {
  // 多Agent会诊
  consultation: (data: {
    message: string
    session_id?: string
    patient_id?: string
  }) => request<{
    session_id: string
    query: string
    individual_results: Array<{
      agent_type: string
      response: string
      sources: any[]
      safety: any
    }>
    summary: string
  }>({
    url: '/chat/multi-agent',
    method: 'POST',
    data
  })
}

// ============ 亲情账号API ============
export const familyApi = {
  getUserFamilies: (userId: string) => request<{
    success: boolean
    families: Array<{ id: string; name: string; created_at: string }>
  }>({
    url: `/family/user/${userId}/families`,
    method: 'GET'
  }),

  createFamily: (data: { name: string; owner_id: string; owner_name: string }) => request<{
    success: boolean
    family: { id: string; name: string; created_at: string }
  }>({
    url: '/family/create',
    method: 'POST',
    data
  }),

  getFamilyMembers: (familyId: string) => request<{
    success: boolean
    members: Array<{
      id: string
      family_id: string
      user_id: string
      user_name: string
      role: string
      relationship: string
      patient_id?: string
      joined_at: string
    }>
  }>({
    url: `/family/${familyId}/members`,
    method: 'GET'
  }),

  addMember: (data: {
    family_id: string
    user_id: string
    user_name: string
    role: string
    relationship: string
  }) => request<{ success: boolean }>({
    url: '/family/member/add',
    method: 'POST',
    data
  }),

  getPatientHealthSummary: (patientId: string) => request<{
    success: boolean
    summary: Record<string, any>
  }>({
    url: `/family/patient/${patientId}/health-summary`,
    method: 'GET'
  }),

  getUnreadMessages: (userId: string) => request<{
    success: boolean
    messages: Array<{
      id: string
      from_user_name: string
      content: string
      is_read: boolean
      created_at: string
    }>
  }>({
    url: `/family/message/${userId}/unread`,
    method: 'GET'
  })
}

// ============ 菜谱API ============
export const recipeApi = {
  detectImage: (imageBase64: string) => request<{
    success: boolean
    ingredients: Array<{ name: string; confidence: number }>
    message?: string
  }>({
    url: '/recipe/detect-image',
    method: 'POST',
    data: { image: imageBase64 }
  }),

  detectText: (text: string) => request<{
    success: boolean
    ingredients: Array<{ name: string; confidence: number }>
  }>({
    url: '/recipe/detect-text',
    method: 'POST',
    data: { text }
  }),

  generate: (data: {
    ingredients: string[]
    preferences?: Record<string, any>
  }) => request<{
    success: boolean
    recipe: {
      title: string
      description: string
      ingredients: Array<{ name: string; amount: string }>
      steps: Array<{ step: number; description: string; tip?: string }>
      nutrition?: { calories: number; protein: number; carbs: number }
      cooking_time: number
      difficulty: string
    }
  }>({
    url: '/recipe/generate',
    method: 'POST',
    data
  }),

  createFamilyRecipe: (data: {
    family_id: string
    creator_id: string
    creator_name: string
    title: string
    description?: string
    ingredients: Array<{ name: string; amount: string }>
    steps: Array<{ step: number; description: string; tip?: string }>
    cooking_time: number
    difficulty: string
    nutrition?: Record<string, number>
    is_shared: boolean
  }) => request<{
    success: boolean
    recipe: any
  }>({
    url: '/recipe/family/create',
    method: 'POST',
    data
  }),

  getFamilyRecipes: (familyId: string) => request<{
    success: boolean
    recipes: Array<{
      id: string
      title: string
      description?: string
      creator_name: string
      is_legacy: boolean
    }>
  }>({
    url: `/recipe/family/${familyId}/list`,
    method: 'GET'
  }),

  getRecipeDetail: (recipeId: string) => request<{
    success: boolean
    recipe: any
  }>({
    url: `/recipe/${recipeId}`,
    method: 'GET'
  })
}

// ============ 健康数据API ============
export const healthApi = {
  addRecord: (data: {
    patient_id: string
    type: string
    value: number | string
    unit: string
    notes?: string
    recorded_at?: string
  }) => request<{
    success: boolean
    record: any
  }>({
    url: '/health/record/add',
    method: 'POST',
    data
  }),

  getRecords: (patientId: string, params?: { type?: string; days?: number }) => request<{
    success: boolean
    records: Array<{
      id: string
      patient_id: string
      type: string
      value: number | string
      unit: string
      recorded_at: string
      notes?: string
    }>
  }>({
    url: `/health/records/${patientId}`,
    method: 'GET',
    data: params
  }),

  getTrends: (patientId: string, type: string) => request<{
    success: boolean
    trend: {
      data: Array<{ date: string; value: number }>
      avg: number
      min: number
      max: number
      trend: string
    }
  }>({
    url: `/health/trends/${patientId}`,
    method: 'GET',
    data: { type }
  }),

  getAlerts: (patientId: string) => request<{
    success: boolean
    alerts: Array<{
      id: string
      type: string
      title: string
      content: string
      severity: string
      created_at: string
    }>
  }>({
    url: `/health/alerts/${patientId}`,
    method: 'GET'
  })
}

// ============ 健康预测API ============
export const predictionApi = {
  predictBloodSugar: (patientId: string, days: number) => request<{
    success: boolean
    prediction: {
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
  }>({
    url: '/prediction/blood-sugar',
    method: 'POST',
    data: { patient_id: patientId, days }
  }),

  predictComplication: (patientId: string, complicationType: string) => request<{
    success: boolean
    prediction: {
      risk_level: string
      probability: number
      factors: string[]
      recommendations: string[]
    }
  }>({
    url: '/prediction/complication',
    method: 'POST',
    data: { patient_id: patientId, complication_type: complicationType }
  }),

  predictInterventionEffect: (patientId: string, interventionType: string) => request<{
    success: boolean
    prediction: {
      intervention_type: string
      intervention_name: string
      predicted_effect: {
        blood_sugar_change: number
        confidence: number
      }
      timeline: Array<{ day: number; predicted_value: number }>
      recommendations: string[]
    }
  }>({
    url: '/prediction/intervention-effect',
    method: 'POST',
    data: { patient_id: patientId, intervention_type: interventionType }
  }),

  getPredictionHistory: (patientId: string, params?: { type?: string; limit?: number }) => request<{
    success: boolean
    predictions: Array<{
      id: string
      patient_id: string
      type: string
      prediction_date: string
      prediction_result: {
        risk_level: string
        probability: number
        trend?: string
      }
      created_at: string
    }>
  }>({
    url: `/prediction/history/${patientId}`,
    method: 'GET',
    data: params
  })
}

// ============ 验证码API ============
export const captchaApi = {
  getCaptcha: () => request<{
    captchaKey: string
    captchaImage: string
  }>({
    url: '/captcha/captcha',
    method: 'GET'
  })
}

// ============ 邮箱验证码API ============
export const emailCodeApi = {
  sendCode: (email: string, purpose: string = 'register') => request<{
    success: boolean
    message: string
    email: string
  }>({
    url: '/users/email/code',
    method: 'POST',
    data: { email, purpose }
  }),

  verifyCode: (email: string, code: string) => request<{
    success: boolean
    message: string
  }>({
    url: '/users/email/verify',
    method: 'POST',
    data: { email, code }
  }),

  registerWithEmail: (data: {
    email: string
    code: string
    password: string
    name: string
    phone?: string
  }) => request<{
    token: string
    token_type: string
    expires_in: number
    user: any
  }>({
    url: '/users/register/email',
    method: 'POST',
    data
  }),

  resetPassword: (email: string, code: string, newPassword: string) => request<{
    success: boolean
    message: string
  }>({
    url: '/users/reset-password',
    method: 'POST',
    data: { email, code, new_password: newPassword }
  })
}

export default {
  userApi,
  patientApi,
  vitalsApi,
  medicationReminderApi,
  reportApi,
  chatApi,
  simulationApi,
  knowledgeApi,
  prescriptionApi,
  medicationPurchaseApi,
  calorieApi,
  multiAgentApi,
  familyApi,
  recipeApi,
  healthApi,
  predictionApi,
  captchaApi,
  emailCodeApi
}
