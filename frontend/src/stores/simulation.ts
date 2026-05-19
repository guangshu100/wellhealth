import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { simulationApi, type SimulationResult } from '@/api'

export interface InterventionOption {
  type: string
  name: string
  icon: string
  description: string
  color: string
}

export const useSimulationStore = defineStore('simulation', () => {
  // 状态
  const isRunning = ref(false)
  const currentResult = ref<SimulationResult | null>(null)
  const compareResults = ref<SimulationResult[]>([])
  const interventionTypes = ref<InterventionOption[]>([])
  const selectedInterventions = ref<string[]>([])
  const patientVitals = ref<Record<string, number>>({})
  const selectedDisease = ref<string>('')

  // 计算属性
  const hasResult = computed(() => currentResult.value !== null)
  const bestOption = computed(() => {
    if (compareResults.value.length === 0) return null
    return compareResults.value.reduce((best, current) => {
      return (current.effectiveness || 0) > (best.effectiveness || 0) ? current : best
    })
  })

  // 获取干预类型
  const fetchInterventionTypes = async () => {
    try {
      const res = await simulationApi.getInterventionTypes()
      interventionTypes.value = res.types.map(t => ({
        type: t.value,
        name: t.name,
        icon: getInterventionIcon(t.value),
        description: getInterventionDescription(t.value),
        color: getInterventionColor(t.value)
      }))
    } catch (error) {
      console.error('Fetch intervention types failed:', error)
      // 备用数据
      interventionTypes.value = [
        { type: 'diet', name: '饮食干预', icon: '🥗', description: '调整饮食结构，控制热量摄入', color: '#67C23A' },
        { type: 'exercise', name: '运动干预', icon: '🏃', description: '规律运动，提高代谢水平', color: '#409EFF' },
        { type: 'medication', name: '药物调整', icon: '💊', description: '遵医嘱调整用药方案', color: '#9C27B0' },
        { type: 'lifestyle', name: '生活方式', icon: '🌿', description: '改善生活习惯，全面调理', color: '#E6A23C' },
        { type: 'combined', name: '综合干预', icon: '✨', description: '多维度综合干预，效果最佳', color: '#F56C6C' }
      ]
    }
  }

  // 运行模拟
  const runSimulation = async (
    patientId: string,
    disease: string,
    vitals: Record<string, number>,
    interventionType: string = 'combined',
    patientName?: string,
    age?: number
  ) => {
    isRunning.value = true
    selectedDisease.value = disease
    patientVitals.value = vitals

    try {
      const res = await simulationApi.runSimulation({
        patient_id: patientId,
        patient_name: patientName,
        age: age,
        disease,
        current_vitals: vitals,
        intervention_type: interventionType
      })
      currentResult.value = res.result
      return res.result
    } catch (error) {
      console.error('Run simulation failed:', error)
      // 模拟数据
      currentResult.value = createMockResult(disease, vitals, interventionType)
      return currentResult.value
    } finally {
      isRunning.value = false
    }
  }

  // 对比干预方案
  const compareInterventions = async (
    patientId: string,
    disease: string,
    vitals: Record<string, number>,
    patientName?: string,
    age?: number
  ) => {
    isRunning.value = true
    selectedDisease.value = disease
    patientVitals.value = vitals

    try {
      const res = await simulationApi.compareInterventions({
        patient_id: patientId,
        patient_name: patientName,
        age: age,
        disease,
        current_vitals: vitals
      })
      compareResults.value = res.results
      return res.results
    } catch (error) {
      console.error('Compare interventions failed:', error)
      // 模拟数据
      compareResults.value = ['diet', 'exercise', 'medication', 'combined'].map(type => 
        createMockResult(disease, vitals, type)
      )
      return compareResults.value
    } finally {
      isRunning.value = false
    }
  }

  // 选择干预方案（用于拖拽）
  const toggleIntervention = (type: string) => {
    const index = selectedInterventions.value.indexOf(type)
    if (index === -1) {
      selectedInterventions.value.push(type)
    } else {
      selectedInterventions.value.splice(index, 1)
    }
  }

  // 清除结果
  const clearResults = () => {
    currentResult.value = null
    compareResults.value = []
    selectedInterventions.value = []
  }

  // 辅助函数
  function getInterventionIcon(type: string): string {
    const icons: Record<string, string> = {
      diet: '🥗',
      exercise: '🏃',
      medication: '💊',
      lifestyle: '🌿',
      combined: '✨'
    }
    return icons[type] || '💡'
  }

  function getInterventionDescription(type: string): string {
    const descriptions: Record<string, string> = {
      diet: '调整饮食结构，控制热量摄入',
      exercise: '规律运动，提高代谢水平',
      medication: '遵医嘱调整用药方案',
      lifestyle: '改善生活习惯，全面调理',
      combined: '多维度综合干预，效果最佳'
    }
    return descriptions[type] || ''
  }

  function getInterventionColor(type: string): string {
    const colors: Record<string, string> = {
      diet: '#67C23A',
      exercise: '#409EFF',
      medication: '#9C27B0',
      lifestyle: '#E6A23C',
      combined: '#F56C6C'
    }
    return colors[type] || '#409EFF'
  }

  function createMockResult(
    disease: string,
    vitals: Record<string, number>,
    interventionType: string
  ): SimulationResult {
    const effectMap: Record<string, number> = {
      diet: 0.15,
      exercise: 0.12,
      medication: 0.25,
      combined: 0.35
    }
    const effect = effectMap[interventionType] || 0.2

    const predicted: Record<string, number> = {}
    for (const [key, value] of Object.entries(vitals)) {
      predicted[key] = Number((value * (1 - effect)).toFixed(2))
    }

    const timeline = []
    for (let day = 0; day <= 30; day += 7) {
      const progress = day / 30
      const point: Record<string, number> = { day }
      for (const [key, value] of Object.entries(vitals)) {
        point[key] = Number((value + (predicted[key] - value) * progress).toFixed(2))
      }
      timeline.push(point)
    }

    return {
      intervention: {
        type: interventionType,
        name: interventionType === 'combined' ? '综合干预' : 
              interventionType === 'diet' ? '饮食干预' :
              interventionType === 'exercise' ? '运动干预' :
              interventionType === 'medication' ? '药物调整' : '干预方案',
        description: getInterventionDescription(interventionType),
        duration_days: 30
      },
      status: 'completed',
      baseline: vitals,
      predicted,
      timeline,
      effectiveness: Math.round(effect * 100),
      risk_level: interventionType === 'medication' ? 'medium' : 'low',
      recommendations: [
        '坚持干预方案，定期复查',
        '监测关键指标变化',
        '如有不适及时就医'
      ]
    }
  }

  return {
    // 状态
    isRunning,
    currentResult,
    compareResults,
    interventionTypes,
    selectedInterventions,
    patientVitals,
    selectedDisease,
    // 计算属性
    hasResult,
    bestOption,
    // 方法
    fetchInterventionTypes,
    runSimulation,
    compareInterventions,
    toggleIntervention,
    clearResults
  }
})
