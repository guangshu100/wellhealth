<template>
  <div class="health-plan-view">
    <div class="page-header">
      <h2>📋 健康计划管理</h2>
      <p>制定、跟踪和管理患者健康计划</p>
    </div>

    <el-card class="search-card">
      <el-form inline>
        <el-form-item label="患者ID">
          <el-input v-model="patientId" placeholder="请输入患者ID" style="width: 200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadPatientData">查询</el-button>
        </el-form-item>
        <el-form-item>
          <el-button type="success" @click="openCreateDialog">创建健康计划</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div v-if="patientName" class="patient-label">
      当前患者: <strong>{{ patientName }}</strong>
    </div>

    <el-card v-if="healthPlans.length > 0" style="margin-top: 16px;">
      <template #header>
        <span>📋 健康计划列表</span>
      </template>
      <el-timeline>
        <el-timeline-item
          v-for="plan in healthPlans"
          :key="plan.id"
          :timestamp="plan.start_date + ' ~ ' + plan.end_date"
          :type="getStatusType(plan.status)"
          :hollow="plan.status === 'paused'"
          placement="top"
        >
          <el-card shadow="hover" class="plan-card">
            <div class="plan-header">
              <div class="plan-title">
                <el-tag :type="getStatusType(plan.status)" effect="dark" size="small">
                  {{ getStatusLabel(plan.status) }}
                </el-tag>
                <span class="plan-type">{{ getPlanTypeLabel(plan.plan_type) }}</span>
              </div>
              <div class="plan-actions">
                <el-button
                  v-if="plan.status === 'active'"
                  type="warning"
                  size="small"
                  @click="pausePlan(plan.id)"
                >暂停</el-button>
                <el-button
                  v-if="plan.status === 'paused'"
                  type="success"
                  size="small"
                  @click="resumePlan(plan.id)"
                >恢复</el-button>
                <el-button
                  v-if="plan.status === 'active'"
                  type="primary"
                  size="small"
                  @click="completePlan(plan.id)"
                >完成</el-button>
              </div>
            </div>

            <div class="plan-goals">
              <h5>🎯 目标</h5>
              <div v-for="(goal, gi) in plan.goals" :key="gi" class="goal-item">
                <el-checkbox
                  :model-value="goal.achieved"
                  @change="toggleGoal(plan.id, gi)"
                  :disabled="plan.status !== 'active'"
                >
                  <span :class="{ 'goal-achieved': goal.achieved }">{{ goal.description }}</span>
                </el-checkbox>
              </div>
            </div>

            <div class="plan-milestones" v-if="plan.milestones.length > 0">
              <h5>🏁 里程碑</h5>
              <div v-for="(ms, mi) in plan.milestones" :key="mi" class="milestone-item">
                <el-tag :type="ms.completed ? 'success' : 'info'" size="small">
                  {{ ms.completed ? '✓' : '○' }}
                </el-tag>
                <span class="milestone-name">{{ ms.description }}</span>
                <span class="milestone-date">{{ ms.target_date }}</span>
              </div>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </el-card>

    <el-card v-else-if="patientName" style="margin-top: 16px;">
      <el-empty description="暂无健康计划，点击上方按钮创建" />
    </el-card>

    <el-dialog v-model="createDialogVisible" title="创建健康计划" width="560px" destroy-on-close>
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="计划类型" required>
          <el-select v-model="createForm.plan_type" style="width: 100%">
            <el-option label="饮食计划" value="饮食" />
            <el-option label="运动计划" value="运动" />
            <el-option label="用药计划" value="用药" />
            <el-option label="综合计划" value="综合" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标(SMART)" required>
          <el-input
            v-model="createForm.goal"
            type="textarea"
            :rows="3"
            placeholder="具体(Specific)、可衡量(Measurable)、可达成(Achievable)、相关性(Relevant)、有时限(Time-bound)"
          />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="开始日期" required>
              <el-date-picker
                v-model="createForm.start_date"
                type="date"
                placeholder="选择开始日期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束日期" required>
              <el-date-picker
                v-model="createForm.end_date"
                type="date"
                placeholder="选择结束日期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="createPlan">确认创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { patientProfileApi, healthPlanApi } from '@/api'
import type { HealthPlanItem, HealthPlanGoal, HealthPlanMilestone } from '@/api'

interface Goal {
  description: string
  achieved: boolean
}

interface Milestone {
  description: string
  target_date: string
  completed: boolean
}

interface HealthPlan {
  id: string
  plan_type: string
  status: 'active' | 'completed' | 'paused'
  goals: Goal[]
  milestones: Milestone[]
  start_date: string
  end_date: string
  created_at: string
}

const patientId = ref('')
const patientName = ref('')
const createDialogVisible = ref(false)
const healthPlans = ref<HealthPlan[]>([])

const createForm = reactive({
  plan_type: '综合',
  goal: '',
  start_date: '',
  end_date: ''
})

const loadPatientData = async () => {
  if (!patientId.value.trim()) {
    ElMessage.warning('请输入患者ID')
    return
  }
  try {
    const [panorama, plansRes] = await Promise.all([
      patientProfileApi.getPanorama(patientId.value.trim()),
      healthPlanApi.getPatientPlans(patientId.value.trim())
    ])
    patientName.value = panorama.patient_name
    healthPlans.value = plansRes.plans.map(mapApiPlan)
    ElMessage.success('患者信息加载成功')
  } catch (error) {
    ElMessage.error('加载患者数据失败')
  }
}

const mapApiPlan = (p: HealthPlanItem): HealthPlan => ({
  id: p.id,
  plan_type: p.plan_type,
  status: p.status as HealthPlan['status'],
  goals: (p.goals || []).map((g: HealthPlanGoal) => ({
    description: g.description,
    achieved: g.achieved
  })),
  milestones: (p.milestones || []).map((m: HealthPlanMilestone) => ({
    description: m.description,
    target_date: m.target_date || '',
    completed: m.completed
  })),
  start_date: p.start_date || '',
  end_date: p.end_date || '',
  created_at: p.created_at || ''
})

const openCreateDialog = () => {
  if (!patientId.value.trim()) {
    ElMessage.warning('请先输入患者ID')
    return
  }
  createForm.plan_type = '综合'
  createForm.goal = ''
  createForm.start_date = new Date().toISOString().slice(0, 10)
  const endDate = new Date()
  endDate.setMonth(endDate.getMonth() + 3)
  createForm.end_date = endDate.toISOString().slice(0, 10)
  createDialogVisible.value = true
}

const createPlan = async () => {
  if (!createForm.plan_type) {
    ElMessage.warning('请选择计划类型')
    return
  }
  if (!createForm.goal.trim()) {
    ElMessage.warning('请输入目标')
    return
  }
  if (!createForm.start_date || !createForm.end_date) {
    ElMessage.warning('请选择开始和结束日期')
    return
  }

  try {
    const milestones = generateMilestones(createForm.start_date, createForm.end_date)
    const created = await healthPlanApi.createPlan({
      patient_id: patientId.value.trim(),
      plan_type: createForm.plan_type,
      goals: [{ description: createForm.goal.trim(), achieved: false }],
      milestones: milestones.map(ms => ({
        description: ms.description,
        target_date: ms.target_date,
        completed: false
      })),
      start_date: createForm.start_date,
      end_date: createForm.end_date
    })
    healthPlans.value.unshift(mapApiPlan(created))
    createDialogVisible.value = false
    ElMessage.success('健康计划创建成功')
  } catch (error) {
    console.error('创建计划失败:', error)
    ElMessage.error('创建计划失败')
  }
}

const generateMilestones = (startDate: string, endDate: string): { description: string; target_date: string; completed: boolean }[] => {
  const start = new Date(startDate)
  const end = new Date(endDate)
  const diffDays = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24))

  const checkpoints = [0.25, 0.5, 0.75, 1.0]
  const labels = ['第一阶段检查', '中期评估', '第三阶段检查', '计划完成']

  return checkpoints.map((ratio, i) => {
    const milestoneDate = new Date(start.getTime() + diffDays * ratio * 24 * 60 * 60 * 1000)
    return {
      description: labels[i],
      target_date: milestoneDate.toISOString().slice(0, 10),
      completed: false
    }
  })
}

const pausePlan = async (planId: string) => {
  try {
    await healthPlanApi.updatePlan(planId, { status: 'paused' })
    const plan = healthPlans.value.find(p => p.id === planId)
    if (plan) plan.status = 'paused'
    ElMessage.info('计划已暂停')
  } catch (error) {
    console.error('暂停计划失败:', error)
    ElMessage.error('暂停计划失败')
  }
}

const resumePlan = async (planId: string) => {
  try {
    await healthPlanApi.updatePlan(planId, { status: 'active' })
    const plan = healthPlans.value.find(p => p.id === planId)
    if (plan) plan.status = 'active'
    ElMessage.success('计划已恢复')
  } catch (error) {
    console.error('恢复计划失败:', error)
    ElMessage.error('恢复计划失败')
  }
}

const completePlan = async (planId: string) => {
  try {
    const plan = healthPlans.value.find(p => p.id === planId)
    if (!plan) return
    const updatedMilestones = plan.milestones.map(ms => ({
      description: ms.description,
      target_date: ms.target_date,
      completed: true
    }))
    await healthPlanApi.updatePlan(planId, { status: 'completed', milestones: updatedMilestones })
    plan.status = 'completed'
    plan.milestones.forEach(ms => { ms.completed = true })
    ElMessage.success('计划已完成')
  } catch (error) {
    console.error('完成计划失败:', error)
    ElMessage.error('完成计划失败')
  }
}

const toggleGoal = async (planId: string, goalIndex: number) => {
  const plan = healthPlans.value.find(p => p.id === planId)
  if (!plan || plan.status !== 'active') return

  const updatedGoals = plan.goals.map((g, i) => ({
    description: g.description,
    achieved: i === goalIndex ? !g.achieved : g.achieved
  }))

  try {
    await healthPlanApi.updatePlan(planId, { goals: updatedGoals })
    plan.goals[goalIndex].achieved = !plan.goals[goalIndex].achieved
  } catch (error) {
    console.error('更新目标失败:', error)
    ElMessage.error('更新目标失败')
  }
}

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    active: 'success',
    completed: 'primary',
    paused: 'info'
  }
  return map[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    active: '进行中',
    completed: '已完成',
    paused: '已暂停'
  }
  return map[status] || status
}

const getPlanTypeLabel = (type: string) => {
  const map: Record<string, string> = {
    '饮食': '🥗 饮食计划',
    '运动': '🏃 运动计划',
    '用药': '💊 用药计划',
    '综合': '🌟 综合计划'
  }
  return map[type] || type
}
</script>

<style scoped>
.health-plan-view {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.page-header p {
  color: #909399;
  margin: 5px 0 0;
}

.search-card {
  margin-bottom: 16px;
}

.patient-label {
  margin-bottom: 12px;
  padding: 8px 16px;
  background: #ecf5ff;
  border-radius: 6px;
  color: #409eff;
  font-size: 14px;
}

.plan-card {
  margin-bottom: 0;
}

.plan-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.plan-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.plan-type {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.plan-actions {
  display: flex;
  gap: 8px;
}

.plan-goals {
  margin-bottom: 12px;
}

.plan-goals h5,
.plan-milestones h5 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #303133;
}

.goal-item {
  padding: 4px 0;
}

.goal-achieved {
  text-decoration: line-through;
  color: #909399;
}

.milestone-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  font-size: 13px;
}

.milestone-name {
  color: #606266;
}

.milestone-date {
  color: #909399;
  font-size: 12px;
  margin-left: auto;
}
</style>
