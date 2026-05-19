<template>
  <div class="reminder-view">
    <el-page-header @back="$router.back()" content="用药提醒" />
    <div class="content">
      <el-row :gutter="20">
        <!-- 左侧：患者选择和提醒列表 -->
        <el-col :span="14">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>用药提醒列表</span>
                <el-button type="primary" @click="showAddDialog = true">
                  <el-icon><Plus /></el-icon>
                  添加提醒
                </el-button>
              </div>
            </template>
            
            <el-form :inline="true" :model="queryForm" class="query-form">
              <el-form-item label="选择患者">
                <el-select v-model="queryForm.patient_id" placeholder="请选择患者" @change="loadReminders">
                  <el-option v-for="p in patients" :key="p.id" :label="p.name" :value="p.id" />
                </el-select>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="loadReminders">查询</el-button>
              </el-form-item>
            </el-form>

            <el-table :data="reminders" v-loading="loading" stripe>
              <el-table-column prop="drug_name" label="药品名称" min-width="120" />
              <el-table-column prop="dosage" label="剂量" width="100" />
              <el-table-column prop="frequency" label="频率" width="100" />
              <el-table-column label="提醒时间" width="180">
                <template #default="{ row }">
                  <el-tag v-for="time in row.times" :key="time" size="small" style="margin-right: 4px">
                    {{ time }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="start_date" label="开始日期" width="120" />
              <el-table-column prop="end_date" label="结束日期" width="120" />
              <el-table-column label="状态" width="80">
                <template #default="{ row }">
                  <el-tag :type="row.status === 'active' ? 'success' : 'info'">
                    {{ row.status === 'active' ? '生效中' : '已暂停' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="150" fixed="right">
                <template #default="{ row }">
                  <el-button type="primary" size="small" text @click="editReminder(row)">编辑</el-button>
                  <el-button type="danger" size="small" text @click="deleteReminder(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>

        <!-- 右侧：今日提醒 -->
        <el-col :span="10">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>今日提醒</span>
                <el-tag type="info">{{ todayDate }}</el-tag>
              </div>
            </template>
            
            <div v-if="todayReminders.length === 0" class="empty-tip">
              <el-empty description="今日暂无提醒" />
            </div>
            
            <div v-else class="today-reminders">
              <el-timeline>
                <el-timeline-item
                  v-for="item in todayReminders"
                  :key="item.id"
                  :timestamp="item.time"
                  placement="top"
                  :type="item.taken ? 'success' : 'primary'"
                >
                  <el-card class="reminder-card">
                    <div class="reminder-header">
                      <span class="drug-name">{{ item.drug_name }}</span>
                      <el-tag size="small">{{ item.dosage }}</el-tag>
                    </div>
                    <div class="reminder-body">
                      <span class="frequency">{{ item.frequency }}</span>
                    </div>
                    <div class="reminder-actions">
                      <el-button 
                        v-if="!item.taken" 
                        type="primary" 
                        size="small" 
                        @click="markTaken(item)"
                      >
                        标记已服用
                      </el-button>
                      <el-tag v-else type="success">已服用</el-tag>
                    </div>
                  </el-card>
                </el-timeline-item>
              </el-timeline>
            </div>
          </el-card>

          <!-- 统计信息 -->
          <el-card class="stats-card">
            <template #header>
              <span>提醒统计</span>
            </template>
            <el-row :gutter="20">
              <el-col :span="8">
                <div class="stat-item">
                  <div class="stat-value">{{ stats.total }}</div>
                  <div class="stat-label">总提醒数</div>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="stat-item">
                  <div class="stat-value">{{ stats.today }}</div>
                  <div class="stat-label">今日提醒</div>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="stat-item">
                  <div class="stat-value">{{ stats.completed }}</div>
                  <div class="stat-label">已完成</div>
                </div>
              </el-col>
            </el-row>
          </el-card>
        </el-col>
      </el-row>

      <!-- 添加/编辑提醒弹窗 -->
      <el-dialog 
        v-model="showAddDialog" 
        :title="editingReminder ? '编辑提醒' : '添加提醒'" 
        width="500px"
      >
        <el-form :model="reminderForm" label-width="100px">
          <el-form-item label="选择患者" required>
            <el-select v-model="reminderForm.patient_id" placeholder="请选择患者">
              <el-option v-for="p in patients" :key="p.id" :label="p.name" :value="p.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="药品名称" required>
            <el-input v-model="reminderForm.drug_name" placeholder="如：二甲双胍片" />
          </el-form-item>
          <el-form-item label="剂量">
            <el-input v-model="reminderForm.dosage" placeholder="如：0.5g" />
          </el-form-item>
          <el-form-item label="用药频率" required>
            <el-select v-model="reminderForm.frequency" placeholder="请选择频率">
              <el-option label="每日1次" value="每日1次" />
              <el-option label="每日2次" value="每日2次" />
              <el-option label="每日3次" value="每日3次" />
              <el-option label="每日4次" value="每日4次" />
              <el-option label="每周1次" value="每周1次" />
              <el-option label="每周2次" value="每周2次" />
              <el-option label="必要时" value="必要时" />
            </el-select>
          </el-form-item>
          <el-form-item label="提醒时间" required>
            <el-select v-model="reminderForm.times" multiple placeholder="选择提醒时间">
              <el-option label="早餐前" value="早餐前" />
              <el-option label="早餐后" value="早餐后" />
              <el-option label="午餐前" value="午餐前" />
              <el-option label="午餐后" value="午餐后" />
              <el-option label="晚餐前" value="晚餐前" />
              <el-option label="晚餐后" value="晚餐后" />
              <el-option label="睡前" value="睡前" />
            </el-select>
          </el-form-item>
          <el-form-item label="开始日期">
            <el-date-picker v-model="reminderForm.start_date" type="date" placeholder="选择开始日期" value-format="YYYY-MM-DD" />
          </el-form-item>
          <el-form-item label="结束日期">
            <el-date-picker v-model="reminderForm.end_date" type="date" placeholder="选择结束日期" value-format="YYYY-MM-DD" />
          </el-form-item>
          <el-form-item label="备注">
            <el-input v-model="reminderForm.notes" type="textarea" rows="2" placeholder="可选备注" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showAddDialog = false">取消</el-button>
          <el-button type="primary" @click="saveReminder">确定</el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { patientApi } from '@/api'

interface Reminder {
  id: string
  patient_id: string
  drug_name: string
  dosage: string
  frequency: string
  times: string[]
  start_date: string
  end_date?: string
  notes?: string
  status: string
  created_at: string
}

interface Patient {
  id: string
  name: string
}

const patients = ref<Patient[]>([])
const reminders = ref<Reminder[]>([])
const loading = ref(false)
const showAddDialog = ref(false)
const editingReminder = ref<Reminder | null>(null)

const queryForm = reactive({
  patient_id: ''
})

const reminderForm = reactive({
  patient_id: '',
  drug_name: '',
  dosage: '',
  frequency: '',
  times: [] as string[],
  start_date: '',
  end_date: '',
  notes: ''
})

const todayDate = new Date().toLocaleDateString('zh-CN', { 
  year: 'numeric', 
  month: 'long', 
  day: 'numeric' 
})

const todayReminders = computed(() => {
  // 模拟今日提醒数据
  return [
    { id: '1', drug_name: '二甲双胍片', dosage: '0.5g', frequency: '每日2次', time: '08:00', taken: true },
    { id: '2', drug_name: '二甲双胍片', dosage: '0.5g', frequency: '每日2次', time: '18:00', taken: false },
    { id: '3', drug_name: '厄贝沙坦', dosage: '150mg', frequency: '每日1次', time: '08:00', taken: true },
  ]
})

const stats = computed(() => ({
  total: reminders.value.length,
  today: todayReminders.value.length,
  completed: todayReminders.value.filter(r => r.taken).length
}))

onMounted(async () => {
  await loadPatients()
  if (patients.value.length > 0) {
    queryForm.patient_id = patients.value[0].id
    await loadReminders()
  }
})

const loadPatients = async () => {
  try {
    const res = await patientApi.getList()
    if (Array.isArray(res)) {
      patients.value = res
    } else {
      patients.value = res.patients || []
    }
  } catch (e) {
    // 使用备用数据
    patients.value = [
      { id: '1', name: '张三' },
      { id: '2', name: '李四' }
    ]
  }
}

const loadReminders = async () => {
  if (!queryForm.patient_id) return
  
  loading.value = true
  try {
    // 模拟数据
    reminders.value = [
      {
        id: '1',
        patient_id: queryForm.patient_id,
        drug_name: '二甲双胍片',
        dosage: '0.5g',
        frequency: '每日2次',
        times: ['早餐后', '晚餐后'],
        start_date: '2024-03-01',
        end_date: '2024-06-01',
        status: 'active',
        created_at: '2024-03-01'
      },
      {
        id: '2',
        patient_id: queryForm.patient_id,
        drug_name: '厄贝沙坦片',
        dosage: '150mg',
        frequency: '每日1次',
        times: ['早餐后'],
        start_date: '2024-03-01',
        status: 'active',
        created_at: '2024-03-01'
      }
    ]
  } finally {
    loading.value = false
  }
}

const editReminder = (row: Reminder) => {
  editingReminder.value = row
  reminderForm.patient_id = row.patient_id
  reminderForm.drug_name = row.drug_name
  reminderForm.dosage = row.dosage
  reminderForm.frequency = row.frequency
  reminderForm.times = [...row.times]
  reminderForm.start_date = row.start_date
  reminderForm.end_date = row.end_date || ''
  reminderForm.notes = row.notes || ''
  showAddDialog.value = true
}

const deleteReminder = async (row: Reminder) => {
  await ElMessageBox.confirm('确定要删除这条提醒吗？', '提示', {
    type: 'warning'
  })
  reminders.value = reminders.value.filter(r => r.id !== row.id)
  ElMessage.success('删除成功')
}

const saveReminder = () => {
  if (!reminderForm.patient_id || !reminderForm.drug_name || !reminderForm.frequency) {
    ElMessage.warning('请填写必要信息')
    return
  }
  
  if (editingReminder.value) {
    // 更新
    const idx = reminders.value.findIndex(r => r.id === editingReminder.value!.id)
    if (idx !== -1) {
      reminders.value[idx] = {
        ...reminders.value[idx],
        ...reminderForm
      }
    }
    ElMessage.success('更新成功')
  } else {
    // 新增
    reminders.value.push({
      id: Date.now().toString(),
      ...reminderForm,
      status: 'active',
      created_at: new Date().toISOString().split('T')[0]
    })
    ElMessage.success('添加成功')
  }
  
  showAddDialog.value = false
  resetForm()
}

const resetForm = () => {
  editingReminder.value = null
  reminderForm.patient_id = ''
  reminderForm.drug_name = ''
  reminderForm.dosage = ''
  reminderForm.frequency = ''
  reminderForm.times = []
  reminderForm.start_date = ''
  reminderForm.end_date = ''
  reminderForm.notes = ''
}

const markTaken = (item: any) => {
  item.taken = true
  ElMessage.success('已标记为已服用')
}
</script>

<style scoped>
.reminder-view {
  padding: 20px;
}

.content {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.query-form {
  margin-bottom: 20px;
}

.empty-tip {
  padding: 40px 0;
}

.today-reminders {
  max-height: 400px;
  overflow-y: auto;
}

.reminder-card {
  padding: 10px;
}

.reminder-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.drug-name {
  font-weight: 600;
  color: #303133;
}

.reminder-body {
  margin-bottom: 10px;
  color: #606266;
  font-size: 13px;
}

.reminder-actions {
  text-align: right;
}

.stats-card {
  margin-top: 20px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-primary);
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
