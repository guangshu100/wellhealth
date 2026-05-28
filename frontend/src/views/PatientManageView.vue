<template>
  <div class="patient-view">
    <el-page-header @back="$router.back()" content="患者管理" />
    <div class="content">
      <!-- 操作栏 -->
      <el-card class="toolbar-card">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-input v-model="searchKeyword" placeholder="搜索患者姓名" clearable>
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-col>
          <el-col :span="4">
            <el-select v-model="diseaseFilter" placeholder="按疾病筛选" clearable>
              <el-option label="糖尿病" value="糖尿病" />
              <el-option label="高血压" value="高血压" />
              <el-option label="高血脂" value="高血脂" />
            </el-select>
          </el-col>
          <el-col :span="14" style="text-align: right;">
            <el-button type="primary" @click="handleAdd">新增患者</el-button>
            <el-button @click="loadPatients">刷新</el-button>
          </el-col>
        </el-row>
      </el-card>

      <!-- 患者列表 -->
      <el-card>
        <el-table :data="patients" v-loading="loading" style="width: 100%">
          <el-table-column prop="name" label="姓名" width="100" />
          <el-table-column prop="age" label="年龄" width="80" />
          <el-table-column prop="gender" label="性别" width="80">
            <template #default="{ row }">
              {{ row.gender === 'male' ? '男' : row.gender === 'female' ? '女' : '其他' }}
            </template>
          </el-table-column>
          <el-table-column prop="phone" label="电话" width="130" />
          <el-table-column prop="id_card" label="身份证号" width="180" />
          <el-table-column prop="address" label="地址" min-width="150" />
          <el-table-column label="操作" width="250" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="handleViewProfile(row)">健康档案</el-button>
              <el-button link type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
              <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-wrap">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :total="total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @size-change="loadPatients"
            @current-change="loadPatients"
          />
        </div>
      </el-card>

      <!-- 新增/编辑对话框 -->
      <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑患者' : '新增患者'" width="500px">
        <el-form :model="patientForm" label-width="100px">
          <el-form-item label="姓名" required>
            <el-input v-model="patientForm.name" />
          </el-form-item>
          <el-form-item label="年龄" required>
            <el-input-number v-model="patientForm.age" :min="1" :max="120" />
          </el-form-item>
          <el-form-item label="性别" required>
            <el-select v-model="patientForm.gender">
              <el-option label="男" value="male" />
              <el-option label="女" value="female" />
              <el-option label="其他" value="other" />
            </el-select>
          </el-form-item>
          <el-form-item label="电话">
            <el-input v-model="patientForm.phone" />
          </el-form-item>
          <el-form-item label="身份证号">
            <el-input v-model="patientForm.id_card" />
          </el-form-item>
          <el-form-item label="地址">
            <el-input v-model="patientForm.address" />
          </el-form-item>
          <el-form-item label="紧急联系人">
            <el-input v-model="patientForm.emergency_contact" />
          </el-form-item>
          <el-form-item label="紧急联系电话">
            <el-input v-model="patientForm.emergency_phone" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit">确定</el-button>
        </template>
      </el-dialog>

      <!-- 健康档案对话框 -->
      <el-dialog v-model="profileVisible" title="患者健康档案" width="800px">
        <div v-if="currentProfile" class="profile-content">
          <!-- 基本信息 -->
          <el-descriptions title="基本信息" :column="2" border>
            <el-descriptions-item label="姓名">{{ currentProfile.basic_info?.name }}</el-descriptions-item>
            <el-descriptions-item label="年龄">{{ currentProfile.basic_info?.age }}</el-descriptions-item>
            <el-descriptions-item label="性别">
              {{ currentProfile.basic_info?.gender === 'male' ? '男' : '女' }}
            </el-descriptions-item>
            <el-descriptions-item label="电话">{{ currentProfile.basic_info?.phone }}</el-descriptions-item>
            <el-descriptions-item label="身份证号" :span="2">{{ currentProfile.basic_info?.id_card }}</el-descriptions-item>
            <el-descriptions-item label="地址" :span="2">{{ currentProfile.basic_info?.address }}</el-descriptions-item>
          </el-descriptions>

          <!-- 疾病记录 -->
          <div class="section">
            <div class="section-header">
              <h4>疾病记录</h4>
              <el-button size="small" type="primary" @click="addDisease">添加</el-button>
            </div>
            <el-table :data="currentProfile.diseases" border size="small" v-if="currentProfile.diseases?.length">
              <el-table-column prop="disease_name" label="疾病名称" />
              <el-table-column prop="diagnosed_date" label="确诊日期" width="120" />
              <el-table-column prop="status" label="状态" width="80">
                <template #default="{ row }">
                  <el-tag :type="row.status === 'active' ? 'danger' : 'info'" size="small">
                    {{ row.status === 'active' ? '在治' : '已愈' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="notes" label="备注" />
            </el-table>
            <el-empty v-else description="暂无疾病记录" :image-size="60" />
          </div>

          <!-- 用药记录 -->
          <div class="section">
            <div class="section-header">
              <h4>用药记录</h4>
              <el-button size="small" type="primary" @click="addMedication">添加</el-button>
            </div>
            <el-table :data="currentProfile.medications" border size="small" v-if="currentProfile.medications?.length">
              <el-table-column prop="drug_name" label="药品名称" />
              <el-table-column prop="specification" label="规格" width="120" />
              <el-table-column prop="dosage" label="剂量" width="80" />
              <el-table-column prop="frequency" label="频次" width="100" />
              <el-table-column prop="prescribing_doctor" label="开药医生" width="100" />
              <el-table-column prop="start_date" label="开始日期" width="100" />
            </el-table>
            <el-empty v-else description="暂无用药记录" :image-size="60" />
          </div>

          <!-- 体征记录 -->
          <div class="section">
            <div class="section-header">
              <h4>最新体征</h4>
              <el-button size="small" type="primary" @click="addVital">添加</el-button>
            </div>
            <el-table :data="currentProfile.vitals" border size="small" v-if="currentProfile.vitals?.length">
              <el-table-column prop="vital_type" label="体征类型" width="150">
                <template #default="{ row }">
                  {{ getVitalTypeName(row.vital_type) }}
                </template>
              </el-table-column>
              <el-table-column prop="value" label="数值" width="100">
                <template #default="{ row }">
                  {{ row.value }} {{ row.unit }}
                </template>
              </el-table-column>
              <el-table-column prop="recorded_at" label="记录时间" width="160" />
              <el-table-column prop="notes" label="备注" />
            </el-table>
            <el-empty v-else description="暂无体征记录" :image-size="60" />
          </div>

          <!-- 生活习惯 -->
          <el-descriptions title="生活习惯" :column="3" border class="mt-20">
            <el-descriptions-item label="吸烟">{{ currentProfile.lifestyle?.smoking || '-' }}</el-descriptions-item>
            <el-descriptions-item label="饮酒">{{ currentProfile.lifestyle?.drinking || '-' }}</el-descriptions-item>
            <el-descriptions-item label="运动">{{ currentProfile.lifestyle?.exercise || '-' }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { patientApi, patientProfileApi, type Patient } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'

const loading = ref(false)
const patients = ref<Patient[]>([])
const searchKeyword = ref('')
const diseaseFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

const dialogVisible = ref(false)
const profileVisible = ref(false)
const isEdit = ref(false)
const currentPatientId = ref('')
const currentProfile = ref<any>(null)

const patientForm = reactive({
  name: '',
  age: 50,
  gender: 'male',
  phone: '',
  id_card: '',
  address: '',
  emergency_contact: '',
  emergency_phone: ''
})

onMounted(() => {
  loadPatients()
})

const loadPatients = async () => {
  loading.value = true
  try {
    const res = await patientApi.getList({
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchKeyword.value || undefined
    })
    // API返回可能是数组或对象
    if (Array.isArray(res)) {
      patients.value = res
      total.value = res.length
    } else {
      patients.value = res.patients || []
      total.value = res.total || 0
    }
  } catch {
    patients.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

const getVitalTypeName = (type: string) => {
  const map: Record<string, string> = {
    blood_sugar: '血糖',
    blood_pressure_systolic: '收缩压',
    blood_pressure_diastolic: '舒张压',
    heart_rate: '心率',
    weight: '体重'
  }
  return map[type] || type
}

const handleAdd = () => {
  isEdit.value = false
  Object.assign(patientForm, {
    name: '', age: 50, gender: 'male', phone: '', id_card: '', 
    address: '', emergency_contact: '', emergency_phone: ''
  })
  dialogVisible.value = true
}

const handleEdit = (row: Patient) => {
  isEdit.value = true
  currentPatientId.value = row.id
  Object.assign(patientForm, row)
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!patientForm.name) {
    ElMessage.warning('请输入姓名')
    return
  }
  
  try {
    if (isEdit.value) {
      await patientApi.update(currentPatientId.value, patientForm)
      ElMessage.success('更新成功')
    } else {
      await patientApi.create(patientForm)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadPatients()
  } catch {
    ElMessage.error('操作失败')
    dialogVisible.value = false
    loadPatients()
  }
}

const handleDelete = (row: Patient) => {
  ElMessageBox.confirm(`确定删除患者 "${row.name}" 吗？`, '提示', {
    type: 'warning'
  }).then(async () => {
    try {
      await patientApi.delete(row.id)
      ElMessage.success('删除成功')
    } catch {
      ElMessage.error('删除失败')
    }
    loadPatients()
  })
}

const handleViewProfile = async (row: Patient) => {
  currentPatientId.value = row.id
  try {
    const [panorama, vitalsRes] = await Promise.all([
      patientProfileApi.getPanorama(row.id).catch(() => null),
      patientApi.getVitals(row.id).catch(() => null)
    ])

    currentProfile.value = {
      basic_info: row,
      diseases: panorama?.chronic_diseases?.map((d: any, i: number) => ({
        id: `d${i}`,
        disease_name: d.disease,
        diagnosed_date: d.diagnosed_date || '',
        status: d.control_status === '良好' ? 'controlled' : 'active',
        notes: d.control_status || ''
      })) || [],
      medications: panorama?.current_medications?.map((m: any, i: number) => ({
        id: `m${i}`,
        drug_name: m.drug,
        specification: m.dosage || '',
        dosage: m.dosage || '',
        frequency: m.frequency || '',
        prescribing_doctor: '',
        start_date: ''
      })) || [],
      vitals: vitalsRes?.records?.map((v: any) => ({
        id: v.id,
        vital_type: v.type,
        value: v.value,
        unit: v.unit,
        recorded_at: v.recorded_at,
        notes: ''
      })) || [],
      lifestyle: { smoking: '-', drinking: '-', exercise: '-' }
    }
  } catch {
    currentProfile.value = {
      basic_info: row,
      diseases: [],
      medications: [],
      vitals: [],
      lifestyle: { smoking: '-', drinking: '-', exercise: '-' }
    }
  }
  profileVisible.value = true
}

const addDisease = () => {
  ElMessage.info('添加疾病功能开发中')
}

const addMedication = () => {
  ElMessage.info('添加用药功能开发中')
}

const addVital = () => {
  ElMessage.info('添加体征功能开发中')
}
</script>

<style scoped>
.content {
  margin-top: 20px;
}

.toolbar-card {
  margin-bottom: 20px;
}

.pagination-wrap {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.profile-content {
  max-height: 600px;
  overflow-y: auto;
}

.section {
  margin-top: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.section-header h4 {
  margin: 0;
  color: #303133;
}

.mt-20 {
  margin-top: 20px;
}
</style>
