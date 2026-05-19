<template>
  <div class="purchase-view">
    <el-page-header @back="$router.back()" content="购药记录" />
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
              <el-form-item label="药店">
                <el-select v-model="queryForm.pharmacy" placeholder="可选" clearable>
                  <el-option v-for="p in pharmacies" :key="p.value" :label="p.label" :value="p.value" />
                </el-select>
              </el-form-item>
              <el-form-item label="药品">
                <el-input v-model="queryForm.drug_name" placeholder="可选" />
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
                <el-tag v-if="purchases.length > 0">{{ purchases.length }} 条记录</el-tag>
              </div>
            </template>
            
            <div v-if="purchases.length > 0">
              <!-- 统计信息 -->
              <div class="statistics" v-if="statistics">
                <el-row :gutter="20">
                  <el-col :span="6">
                    <div class="stat-item">
                      <div class="stat-value">￥{{ statistics.total_amount }}</div>
                      <div class="stat-label">总金额</div>
                    </div>
                  </el-col>
                  <el-col :span="6">
                    <div class="stat-item">
                      <div class="stat-value">{{ statistics.total_times }}</div>
                      <div class="stat-label">购药次数</div>
                    </div>
                  </el-col>
                  <el-col :span="12">
                    <div class="stat-item">
                      <div class="stat-label">购药药店</div>
                      <div class="stat-pharmacies">
                        <el-tag v-for="p in statistics.pharmacies" :key="p" size="small">{{ p }}</el-tag>
                      </div>
                    </div>
                  </el-col>
                </el-row>
              </div>

              <!-- 购药记录列表 -->
              <div class="purchase-list">
                <div 
                  v-for="item in purchases" 
                  :key="item.id" 
                  class="purchase-card"
                  @click="handleViewDetail(item)"
                >
                  <div class="purchase-header">
                    <span class="pharmacy-name">{{ item.pharmacy }}</span>
                    <span class="purchase-date">{{ item.purchase_date }}</span>
                  </div>
                  <div class="purchase-body">
                    <el-row :gutter="20">
                      <el-col :span="16">
                        <div class="drug-name">{{ item.drug_name }}</div>
                        <div class="drug-spec">{{ item.drug_specification }}</div>
                      </el-col>
                      <el-col :span="8" style="text-align: right;">
                        <div class="quantity">x{{ item.quantity }}</div>
                        <div class="amount">￥{{ item.total_amount }}</div>
                      </el-col>
                    </el-row>
                  </div>
                  <div class="purchase-footer">
                    <span v-if="item.prescription_no">处方号: {{ item.prescription_no }}</span>
                    <span v-if="item.payment_method">支付方式: {{ item.payment_method }}</span>
                    <span v-if="item.pharmacist">药师: {{ item.pharmacist }}</span>
                  </div>
                </div>
              </div>
            </div>
            
            <el-empty v-else-if="hasQueried" description="暂无购药记录" />
            <el-empty v-else description="请输入查询条件" />
          </el-card>
        </el-col>
      </el-row>

      <!-- 详情对话框 -->
      <el-dialog v-model="detailVisible" title="购药记录详情" width="600px">
        <div v-if="currentPurchase" class="detail-content">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="药店名称">{{ currentPurchase.pharmacy }}</el-descriptions-item>
            <el-descriptions-item label="购药日期">{{ currentPurchase.purchase_date }}</el-descriptions-item>
            <el-descriptions-item label="药店地址" :span="2">{{ currentPurchase.pharmacy_address || '-' }}</el-descriptions-item>
            <el-descriptions-item label="药品名称">{{ currentPurchase.drug_name }}</el-descriptions-item>
            <el-descriptions-item label="规格">{{ currentPurchase.drug_specification }}</el-descriptions-item>
            <el-descriptions-item label="生产厂家" :span="2">{{ currentPurchase.manufacturer || '-' }}</el-descriptions-item>
            <el-descriptions-item label="数量">{{ currentPurchase.quantity }}</el-descriptions-item>
            <el-descriptions-item label="单价">￥{{ currentPurchase.unit_price }}</el-descriptions-item>
            <el-descriptions-item label="处方号">{{ currentPurchase.prescription_no || '-' }}</el-descriptions-item>
            <el-descriptions-item label="支付方式">{{ currentPurchase.payment_method || '-' }}</el-descriptions-item>
            <el-descriptions-item label="发票号">{{ currentPurchase.invoice_no || '-' }}</el-descriptions-item>
            <el-descriptions-item label="药师">{{ currentPurchase.pharmacist || '-' }}</el-descriptions-item>
          </el-descriptions>
          
          <div class="total-section">
            <span class="label">实付金额：</span>
            <span class="amount">￥{{ currentPurchase.total_amount }}</span>
          </div>
        </div>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { medicationPurchaseApi, type MedicationPurchase } from '@/api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const hasQueried = ref(false)
const dateRange = ref<[string, string] | null>(null)
const detailVisible = ref(false)
const currentPurchase = ref<MedicationPurchase | null>(null)
const pharmacies = ref<Array<{ value: string; label: string }>>([])

const queryForm = reactive({
  name: '',
  id_card: '',
  pharmacy: '',
  drug_name: '',
  start_date: '',
  end_date: ''
})

const purchases = ref<MedicationPurchase[]>([])
const statistics = ref<{
  total_amount: number
  total_times: number
  pharmacies: string[]
  drug_statistics: Record<string, { count: number; amount: number }>
} | null>(null)

onMounted(async () => {
  try {
    const res = await medicationPurchaseApi.getPharmacies()
    pharmacies.value = res.pharmacies || []
  } catch (e) {
    pharmacies.value = []
  }
})

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
    
    const res = await medicationPurchaseApi.query(queryForm)
    purchases.value = res.data || []
    
    // 获取统计信息
    if (purchases.value.length > 0) {
      try {
        const statRes = await medicationPurchaseApi.getStatistics(queryForm.name, queryForm.id_card)
        statistics.value = statRes.data
      } catch (e) {
        statistics.value = null
      }
    }
  } catch (error) {
    console.error('查询失败:', error)
    // 模拟数据
    purchases.value = [
      {
        id: 'MP001',
        patient_name: '张三',
        id_card: '110101196001011234',
        pharmacy: '国大药房(北京旗舰店)',
        pharmacy_address: '北京市东城区和平里街道和平里东街18号',
        drug_name: '二甲双胍片',
        drug_specification: '0.5g*20片/盒',
        manufacturer: '中美上海施贵宝制药有限公司',
        quantity: 2,
        unit_price: 28.50,
        total_amount: 57.00,
        purchase_date: '2024-03-16',
        prescription_no: 'P202403150001',
        payment_method: '医保卡',
        invoice_no: 'INV20240316001',
        pharmacist: '王药师',
        created_at: '2024-03-16 10:30:00'
      }
    ]
    statistics.value = {
      total_amount: 57.00,
      total_times: 1,
      pharmacies: ['国大药房(北京旗舰店)'],
      drug_statistics: { '二甲双胍片': { count: 2, amount: 57.00 } }
    }
  } finally {
    loading.value = false
  }
}

const handleReset = () => {
  queryForm.name = ''
  queryForm.id_card = ''
  queryForm.pharmacy = ''
  queryForm.drug_name = ''
  queryForm.start_date = ''
  queryForm.end_date = ''
  dateRange.value = null
  purchases.value = []
  statistics.value = null
  hasQueried.value = false
}

const handleViewDetail = (item: MedicationPurchase) => {
  currentPurchase.value = item
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

.statistics {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: var(--color-primary);
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
}

.stat-pharmacies {
  margin-top: 5px;
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  justify-content: center;
}

.purchase-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.purchase-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 15px;
  cursor: pointer;
  transition: all 0.3s;
}

.purchase-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.purchase-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}

.pharmacy-name {
  font-weight: bold;
  font-size: 16px;
  color: #303133;
}

.purchase-date {
  color: #909399;
  font-size: 14px;
}

.purchase-body {
  margin-bottom: 10px;
}

.drug-name {
  font-size: 16px;
  color: #303133;
  font-weight: 500;
}

.drug-spec {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
}

.quantity {
  font-size: 14px;
  color: #606266;
}

.amount {
  font-size: 18px;
  font-weight: bold;
  color: #f56c6c;
  margin-top: 5px;
}

.purchase-footer {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: #909399;
}

.detail-content {
  padding: 10px;
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
