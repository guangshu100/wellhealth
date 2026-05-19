import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { patientApi, type Patient, type VitalRecord } from '@/api'

export const usePatientStore = defineStore('patient', () => {
  // 状态
  const patients = ref<Patient[]>([])
  const currentPatient = ref<Patient | null>(null)
  const vitals = ref<VitalRecord[]>([])
  const isLoading = ref(false)
  const total = ref(0)

  // 计算属性
  const patientCount = computed(() => patients.value.length)
  const hasCurrentPatient = computed(() => currentPatient.value !== null)

  // 获取患者列表
  const fetchPatients = async (params?: { page?: number; page_size?: number; search?: string }) => {
    isLoading.value = true
    try {
      const res = await patientApi.getList(params)
      // API返回可能是数组或对象
      if (Array.isArray(res)) {
        patients.value = res
        total.value = res.length
      } else {
        patients.value = res.patients || res || []
        total.value = res.total || patients.value.length
      }
    } catch (error) {
      console.error('Fetch patients failed:', error)
      // 模拟数据
      patients.value = [
        {
          id: '1',
          name: '张三',
          age: 55,
          gender: '男',
          diseases: ['糖尿病', '高血压'],
          medications: ['二甲双胍', '厄贝沙坦'],
          allergies: ['青霉素'],
          created_at: '2024-01-15T10:00:00Z'
        },
        {
          id: '2',
          name: '李四',
          age: 62,
          gender: '女',
          diseases: ['高血压', '冠心病'],
          medications: ['氨氯地平', '阿司匹林'],
          allergies: [],
          created_at: '2024-02-01T14:30:00Z'
        }
      ]
      total.value = 2
    } finally {
      isLoading.value = false
    }
  }

  // 获取单个患者
  const fetchPatient = async (id: string) => {
    isLoading.value = true
    try {
      const res = await patientApi.getById(id)
      currentPatient.value = res
    } catch (error) {
      console.error('Fetch patient failed:', error)
      // 查找本地数据
      currentPatient.value = patients.value.find(p => p.id === id) || null
    } finally {
      isLoading.value = false
    }
  }

  // 创建患者
  const createPatient = async (data: Partial<Patient>) => {
    try {
      const res = await patientApi.create(data)
      patients.value.unshift(res)
      total.value++
      return res
    } catch (error) {
      console.error('Create patient failed:', error)
      throw error
    }
  }

  // 更新患者
  const updatePatient = async (id: string, data: Partial<Patient>) => {
    try {
      const res = await patientApi.update(id, data)
      const index = patients.value.findIndex(p => p.id === id)
      if (index !== -1) {
        patients.value[index] = res
      }
      if (currentPatient.value?.id === id) {
        currentPatient.value = res
      }
      return res
    } catch (error) {
      console.error('Update patient failed:', error)
      throw error
    }
  }

  // 删除患者
  const deletePatient = async (id: string) => {
    try {
      await patientApi.delete(id)
      patients.value = patients.value.filter(p => p.id !== id)
      total.value--
      if (currentPatient.value?.id === id) {
        currentPatient.value = null
      }
    } catch (error) {
      console.error('Delete patient failed:', error)
      throw error
    }
  }

  // 获取生命体征
  const fetchVitals = async (patientId: string, params?: { type?: string; days?: number }) => {
    try {
      const res = await patientApi.getVitals(patientId, params)
      vitals.value = res.records
    } catch (error) {
      console.error('Fetch vitals failed:', error)
      vitals.value = []
    }
  }

  // 添加生命体征
  const addVital = async (patientId: string, data: { type: string; value: number; unit: string }) => {
    try {
      const res = await patientApi.addVital(patientId, data)
      vitals.value.unshift(res)
      return res
    } catch (error) {
      console.error('Add vital failed:', error)
      throw error
    }
  }

  // 设置当前患者
  const setCurrentPatient = (patient: Patient | null) => {
    currentPatient.value = patient
  }

  return {
    // 状态
    patients,
    currentPatient,
    vitals,
    isLoading,
    total,
    // 计算属性
    patientCount,
    hasCurrentPatient,
    // 方法
    fetchPatients,
    fetchPatient,
    createPatient,
    updatePatient,
    deletePatient,
    fetchVitals,
    addVital,
    setCurrentPatient
  }
})
