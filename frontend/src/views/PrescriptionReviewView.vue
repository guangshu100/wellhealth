<template>
  <div class="prescription-review-view">
    <div class="page-header">
      <h2>📋 处方三层审核</h2>
      <p>规则引擎 · 医保策略 · 个体化审核</p>
    </div>

    <el-row :gutter="20">
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>审核信息录入</span>
          </template>
          <el-form :model="reviewForm" label-width="90px" label-position="top">
            <el-form-item label="患者ID" required>
              <el-input v-model="reviewForm.patient_id" placeholder="请输入患者ID" />
            </el-form-item>

            <el-divider content-position="left">药品信息</el-divider>
            <div v-for="(med, index) in reviewForm.medications" :key="index" class="medication-row">
              <el-row :gutter="8">
                <el-col :span="8">
                  <el-input v-model="med.drug_name" placeholder="药品名" size="small" />
                </el-col>
                <el-col :span="6">
                  <el-input v-model="med.dosage" placeholder="剂量" size="small" />
                </el-col>
                <el-col :span="6">
                  <el-input v-model="med.frequency" placeholder="频次" size="small" />
                </el-col>
                <el-col :span="4">
                  <el-button type="danger" size="small" @click="removeMedication(index)" :icon="Delete" circle />
                </el-col>
              </el-row>
            </div>
            <el-button type="primary" link @click="addMedication">+ 添加药品</el-button>

            <el-divider content-position="left">诊断信息</el-divider>
            <el-form-item label="诊断">
              <el-input v-model="diagnosisInput" placeholder="输入诊断，回车添加" @keyup.enter="addDiagnosis" />
              <div class="diagnosis-tags" v-if="reviewForm.diagnosis.length > 0">
                <el-tag v-for="(d, i) in reviewForm.diagnosis" :key="i" closable @close="removeDiagnosis(i)" style="margin: 4px;">
                  {{ d }}
                </el-tag>
              </div>
            </el-form-item>

            <el-divider content-position="left">患者上下文</el-divider>
            <el-row :gutter="10">
              <el-col :span="12">
                <el-form-item label="年龄">
                  <el-input-number v-model="reviewForm.patient_context.age" :min="0" :max="150" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="体重(kg)">
                  <el-input-number v-model="reviewForm.patient_context.weight" :min="1" :max="300" style="width: 100%" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="10">
              <el-col :span="12">
                <el-form-item label="肾功能">
                  <el-select v-model="reviewForm.patient_context.renal_function" style="width: 100%">
                    <el-option label="正常" value="normal" />
                    <el-option label="轻度受损" value="mild_impairment" />
                    <el-option label="中度受损" value="moderate_impairment" />
                    <el-option label="重度受损" value="severe_impairment" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="过敏史">
                  <el-input v-model="allergyInput" placeholder="输入过敏原，回车添加" @keyup.enter="addAllergy" />
                  <div class="diagnosis-tags" v-if="reviewForm.patient_context.allergies.length > 0">
                    <el-tag v-for="(a, i) in reviewForm.patient_context.allergies" :key="i" type="danger" closable @close="removeAllergy(i)" size="small" style="margin: 2px;">
                      {{ a }}
                    </el-tag>
                  </div>
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item>
              <el-button type="primary" :loading="loading" @click="submitReview" style="width: 100%">
                提交审核
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="16">
        <div v-if="reviewResult" class="review-results">
          <el-card class="summary-card">
            <template #header>
              <div class="summary-header">
                <span>审核总结</span>
                <el-tag :type="getStatusType(reviewResult.status)" size="large" effect="dark">
                  {{ getStatusLabel(reviewResult.status) }}
                </el-tag>
              </div>
            </template>
            <el-alert :title="reviewResult.summary" :type="getStatusType(reviewResult.status)" show-icon :closable="false" />
            <div class="review-meta">
              <span>审核ID: {{ reviewResult.review_id }}</span>
              <span>审核时间: {{ reviewResult.reviewed_at }}</span>
            </div>
          </el-card>

          <el-row :gutter="16">
            <el-col :span="8" v-for="(layer, key) in layerConfig" :key="key">
              <el-card class="layer-card" :class="'layer-' + key">
                <template #header>
                  <div class="layer-header">
                    <span>{{ layer.icon }} {{ layer.label }}</span>
                    <el-tag :type="getStatusType(reviewResult.layers[key].status)" effect="dark">
                      {{ getStatusLabel(reviewResult.layers[key].status) }}
                    </el-tag>
                  </div>
                </template>

                <div class="layer-section" v-if="reviewResult.layers[key].issues.length > 0">
                  <h5>⚠️ 发现问题</h5>
                  <div v-for="(issue, i) in reviewResult.layers[key].issues" :key="i" class="issue-item">
                    <el-tag :type="getSeverityType(issue.severity)" size="small">{{ issue.severity }}</el-tag>
                    <span class="issue-detail">{{ issue.detail }}</span>
                    <div class="issue-recommendation" v-if="issue.recommendation">
                      💡 {{ issue.recommendation }}
                    </div>
                  </div>
                </div>
                <el-empty v-else description="无问题" :image-size="40" />

                <el-divider v-if="reviewResult.layers[key].suggestions.length > 0" />

                <div class="layer-section" v-if="reviewResult.layers[key].suggestions.length > 0">
                  <h5>💡 建议</h5>
                  <div v-for="(sug, i) in reviewResult.layers[key].suggestions" :key="i" class="suggestion-item">
                    <el-tag size="small" type="info">{{ sug.type }}</el-tag>
                    <span>{{ sug.detail }}</span>
                    <span v-if="sug.alternative" class="alternative">替代: {{ sug.alternative }}</span>
                  </div>
                </div>

                <div v-if="key === 'insurance_policy' && reviewResult.layers.insurance_policy.coverage" class="coverage-section">
                  <el-divider />
                  <h5>💊 医保覆盖</h5>
                  <el-table :data="reviewResult.layers.insurance_policy.coverage" size="small" border>
                    <el-table-column prop="drug" label="药品" />
                    <el-table-column prop="category" label="分类" width="80" />
                    <el-table-column label="报销比例" width="90">
                      <template #default="{ row }">
                        {{ (row.reimbursement_rate * 100).toFixed(0) }}%
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>

        <el-card v-else>
          <el-empty description="请填写审核信息并提交" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { prescriptionReviewApi, type PrescriptionReviewResult } from '@/api'

const loading = ref(false)
const diagnosisInput = ref('')
const allergyInput = ref('')
const reviewResult = ref<PrescriptionReviewResult | null>(null)

const reviewForm = reactive({
  patient_id: '',
  medications: [
    { drug_name: '', dosage: '', frequency: '' }
  ] as Array<{ drug_name: string; dosage: string; frequency: string }>,
  diagnosis: [] as string[],
  patient_context: {
    age: 60,
    weight: 70,
    renal_function: 'normal',
    allergies: [] as string[]
  }
})

const layerConfig: Record<string, { icon: string; label: string }> = {
  rule_engine: { icon: '⚙️', label: '规则引擎' },
  insurance_policy: { icon: '🏥', label: '医保策略' },
  individualized: { icon: '👤', label: '个体化审核' }
}

const addMedication = () => {
  reviewForm.medications.push({ drug_name: '', dosage: '', frequency: '' })
}

const removeMedication = (index: number) => {
  reviewForm.medications.splice(index, 1)
}

const addDiagnosis = () => {
  const val = diagnosisInput.value.trim()
  if (val && !reviewForm.diagnosis.includes(val)) {
    reviewForm.diagnosis.push(val)
    diagnosisInput.value = ''
  }
}

const removeDiagnosis = (index: number) => {
  reviewForm.diagnosis.splice(index, 1)
}

const addAllergy = () => {
  const val = allergyInput.value.trim()
  if (val && !reviewForm.patient_context.allergies.includes(val)) {
    reviewForm.patient_context.allergies.push(val)
    allergyInput.value = ''
  }
}

const removeAllergy = (index: number) => {
  reviewForm.patient_context.allergies.splice(index, 1)
}

const submitReview = async () => {
  if (!reviewForm.patient_id) {
    ElMessage.warning('请输入患者ID')
    return
  }
  const validMeds = reviewForm.medications.filter(m => m.drug_name)
  if (validMeds.length === 0) {
    ElMessage.warning('请至少添加一种药品')
    return
  }

  loading.value = true
  try {
    const result = await prescriptionReviewApi.reviewPrescription({
      patient_id: reviewForm.patient_id,
      medications: validMeds,
      diagnosis: reviewForm.diagnosis.length > 0 ? reviewForm.diagnosis : undefined,
      patient_context: { ...reviewForm.patient_context }
    })
    reviewResult.value = result
    ElMessage.success('审核完成')
  } catch (error) {
    ElMessage.error('审核请求失败')
  } finally {
    loading.value = false
  }
}

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    pass: 'success',
    warning: 'warning',
    reject: 'danger'
  }
  return map[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    pass: '通过',
    warning: '警告',
    reject: '驳回'
  }
  return map[status] || status
}

const getSeverityType = (severity: string) => {
  const map: Record<string, string> = {
    high: 'danger',
    medium: 'warning',
    low: 'info'
  }
  return map[severity] || 'info'
}
</script>

<style scoped>
.prescription-review-view {
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

.medication-row {
  margin-bottom: 8px;
}

.diagnosis-tags {
  margin-top: 6px;
}

.review-results {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.summary-card {
  margin-bottom: 4px;
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.review-meta {
  margin-top: 12px;
  display: flex;
  gap: 20px;
  font-size: 12px;
  color: #909399;
}

.layer-card {
  min-height: 300px;
}

.layer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.layer-section h5 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #303133;
}

.issue-item {
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.issue-item:last-child {
  border-bottom: none;
}

.issue-detail {
  display: block;
  margin: 4px 0;
  font-size: 13px;
  color: #606266;
}

.issue-recommendation {
  font-size: 12px;
  color: #67c23a;
  margin-top: 4px;
}

.suggestion-item {
  padding: 6px 0;
  font-size: 13px;
  color: #606266;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.alternative {
  color: #409eff;
  font-weight: 500;
}

.coverage-section h5 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #303133;
}
</style>
