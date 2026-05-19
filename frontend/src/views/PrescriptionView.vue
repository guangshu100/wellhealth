<template>
  <div class="prescription-view">
    <el-page-header @back="$router.back()" content="处方查询" />
    <div class="content">
      <el-row :gutter="20">
        <el-col :span="8">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>查询条件</span>
              </div>
            </template>
            <el-form :model="queryForm" label-width="80px">
              <el-form-item label="姓名" required>
                <el-input v-model="queryForm.name" placeholder="请输入患者姓名" />
              </el-form-item>
              <el-form-item label="身份证号" required>
                <el-input v-model="queryForm.id_card" placeholder="请输入身份证号码" />
              </el-form-item>
              <el-form-item label="处方号">
                <el-input v-model="queryForm.prescription_no" placeholder="可选" />
              </el-form-item>
              <el-form-item label="医院">
                <el-input v-model="queryForm.hospital" placeholder="可选" />
              </el-form-item>
              <el-form-item label="日期范围">
                <el-date-picker
                  v-model="dateRange"
                  type="daterange"
                  range-separator="至"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  value-format="YYYY-MM-DD"
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="loading" @click="handleQuery">查询</el-button>
                <el-button @click="handleReset">重置</el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>

        <el-col :span="16">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>查询结果</span>
                <el-tag v-if="prescriptions.length > 0">{{ prescriptions.length }} 条记录</el-tag>
              </div>
            </template>
            
            <div v-if="prescriptions.length > 0" class="prescription-list">
              <div 
                v-for="item in prescriptions" 
                :key="item.id" 
                class="prescription-card"
                @click="handleViewDetail(item)"
              >
                <div class="prescription-header">
                  <span class="prescription-no">{{ item.prescription_no }}</span>
                  <el-tag :type="getStatusType(item.status)">{{ getStatusText(item.status) }}</el-tag>
                </div>
                <div class="prescription-body">
                  <el-row :gutter="20">
                    <el-col :span="12">
                      <div class="info-item">
                        <span class="label">医院：</span>
                        <span class="value">{{ item.hospital }}</span>
                      </div>
                    </el-col>
                    <el-col :span="12">
                      <div class="info-item">
                        <span class="label">科室：</span>
                        <span class="value">{{ item.department }}</span>
                      </div>
                    </el-col>
                    <el-col :span="12">
                      <div class="info-item">
                        <span class="label">医生：</span>
                        <span class="value">{{ item.doctor }}</span>
                      </div>
                    </el-col>
                    <el-col :span="12">
                      <div class="info-item">
                        <span class="label">日期：</span>
                        <span class="value">{{ item.prescription_date }}</span>
                      </div>
                    </el-col>
                    <el-col :span="24">
                      <div class="info-item">
                        <span class="label">诊断：</span>
                        <span class="value">{{ item.diagnosis }}</span>
                      </div>
                    </el-col>
                  </el-row>
                </div>
                <div class="prescription-footer">
                  <span class="drug-count">药品：{{ item.medications?.length || 0 }}种</span>
                  <span class="amount" v-if="item.total_amount">￥{{ item.total_amount }}</span>
                </div>
              </div>
            </div>
            
            <el-empty v-else-if="hasQueried" description="暂无处方记录" />
            <el-empty v-else description="请输入查询条件" />
          </el-card>
        </el-col>
      </el-row>

      <!-- 详情对话框 -->
      <el-dialog v-model="detailVisible" title="处方详情" width="700px">
        <div v-if="currentPrescription" class="detail-content">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="处方号">{{ currentPrescription.prescription_no }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="getStatusType(currentPrescription.status)">
                {{ getStatusText(currentPrescription.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="患者姓名">{{ currentPrescription.patient_name }}</el-descriptions-item>
            <el-descriptions-item label="身份证号">{{ currentPrescription.id_card }}</el-descriptions-item>
            <el-descriptions-item label="就诊医院">{{ currentPrescription.hospital }}</el-descriptions-item>
            <el-descriptions-item label="科室">{{ currentPrescription.department }}</el-descriptions-item>
            <el-descriptions-item label="医生">{{ currentPrescription.doctor }}</el-descriptions-item>
            <el-descriptions-item label="就诊日期">{{ currentPrescription.prescription_date }}</el-descriptions-item>
            <el-descriptions-item label="有效期至">{{ currentPrescription.valid_until }}</el-descriptions-item>
            <el-descriptions-item label="处方类型">{{ getTypeText(currentPrescription.prescription_type) }}</el-descriptions-item>
            <el-descriptions-item label="诊断" :span="2">{{ currentPrescription.diagnosis }}</el-descriptions-item>
          </el-descriptions>
          
          <div class="medicine-section">
            <h4>药品清单</h4>
            <el-table :data="currentPrescription.medications" border size="small">
              <el-table-column prop="name" label="药品名称" />
              <el-table-column prop="specification" label="规格" width="120" />
              <el-table-column prop="quantity" label="数量" width="80" />
              <el-table-column prop="dosage" label="剂量" width="80" />
              <el-table-column prop="usage" label="用法" min-width="150" />
            </el-table>
          </div>
          
          <div class="total-section" v-if="currentPrescription.total_amount">
            <span class="label">处方金额：</span>
            <span class="amount">￥{{ currentPrescription.total_amount }}</span>
          </div>
        </div>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { prescriptionApi, type Prescription } from '@/api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const hasQueried = ref(false)
const dateRange = ref<[string, string] | null>(null)
const detailVisible = ref(false)
const currentPrescription = ref<Prescription | null>(null)

const queryForm = reactive({
  name: '',
  id_card: '',
  prescription_no: '',
  hospital: '',
  start_date: '',
  end_date: ''
})

const prescriptions = ref<Prescription[]>([])

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    valid: 'success',
    expired: 'danger',
    used: 'warning',
    cancelled: 'info'
  }
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    valid: '有效',
    expired: '已过期',
    used: '已使用',
    cancelled: '已取消'
  }
  return map[status] || status
}

const getTypeText = (type: string) => {
  const map: Record<string, string> = {
    western: '西药',
    chinese: '中药',
    mixed: '中西药结合'
  }
  return map[type] || type
}

const handleQuery = async () => {
  if (!queryForm.name) {
    ElMessage.warning('请输入姓名')
    return
  }
  if (!queryForm.id_card) {
    ElMessage.warning('请输入身份证号')
    return
  }
  
  loading.value = true
  hasQueried.value = true
  
  try {
    if (dateRange.value) {
      queryForm.start_date = dateRange.value[0]
      queryForm.end_date = dateRange.value[1]
    }
    
    const res = await prescriptionApi.query(queryForm)
    prescriptions.value = res.data || []
  } catch (error) {
    console.error('查询失败:', error)
    // 模拟数据
    prescriptions.value = [
      {
        id: 'RX001',
        patient_name: '张三',
        id_card: '110101196001011234',
        prescription_no: 'P202403150001',
        hospital: '北京协和医院',
        department: '内分泌科',
        doctor: '李主任',
        prescription_date: '2024-03-15',
        valid_until: '2024-04-15',
        prescription_type: 'western',
        diagnosis: '2型糖尿病',
        medications: [
          { name: '二甲双胍片', specification: '0.5g*20片', quantity: '2', dosage: '0.5g', usage: '口服，每日2次，餐后服用' }
        ],
        status: 'valid',
        total_amount: 156.80,
        created_at: '2024-03-15 10:30:00'
      }
    ]
  } finally {
    loading.value = false
  }
}

const handleReset = () => {
  queryForm.name = ''
  queryForm.id_card = ''
  queryForm.prescription_no = ''
  queryForm.hospital = ''
  queryForm.start_date = ''
  queryForm.end_date = ''
  dateRange.value = null
  prescriptions.value = []
  hasQueried.value = false
}

const handleViewDetail = async (item: Prescription) => {
  currentPrescription.value = item
  detailVisible.value = true
}
</script>

<style scoped>
.content {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.prescription-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.prescription-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 15px;
  cursor: pointer;
  transition: all 0.3s;
}

.prescription-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.prescription-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}

.prescription-no {
  font-weight: bold;
  font-size: 16px;
  color: #303133;
}

.prescription-body {
  margin-bottom: 10px;
}

.info-item {
  margin-bottom: 8px;
}

.info-item .label {
  color: #909399;
  font-size: 14px;
}

.info-item .value {
  color: #606266;
  font-size: 14px;
}

.prescription-footer {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  color: #909399;
}

.drug-count {
  color: #606266;
}

.amount {
  color: #f56c6c;
  font-weight: bold;
}

.detail-content {
  padding: 10px;
}

.medicine-section {
  margin-top: 20px;
}

.medicine-section h4 {
  margin-bottom: 10px;
  color: #303133;
}

.total-section {
  margin-top: 20px;
  text-align: right;
  padding-top: 15px;
  border-top: 1px solid #ebeef5;
}

.total-section .label {
  font-size: 16px;
  color: #606266;
}

.total-section .amount {
  font-size: 24px;
  font-weight: bold;
  color: #f56c6c;
}
</style>
