<template>
  <div class="prediction-container">
    <el-card class="header-card">
      <h2>健康预测</h2>
      <p>AI智能预测健康趋势和并发症风险</p>
    </el-card>

    <el-tabs v-model="activeTab" type="border-card">
      <!-- 血糖预测 -->
      <el-tab-pane label="🩸 血糖预测" name="blood-sugar">
        <el-card>
          <template #header>
            <span>未来血糖趋势预测</span>
          </template>
          
          <el-form inline>
            <el-form-item label="预测天数">
              <el-select v-model="predictionDays" style="width: 120px">
                <el-option label="7天" :value="7" />
                <el-option label="14天" :value="14" />
                <el-option label="30天" :value="30" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="predictBloodSugar" :loading="predicting">
                开始预测
              </el-button>
            </el-form-item>
          </el-form>
          
          <div v-if="bloodSugarPrediction" class="prediction-result">
            <el-alert
              :title="`风险等级: ${getRiskLabel(bloodSugarPrediction.prediction_result.risk_level)}`"
              :type="getRiskType(bloodSugarPrediction.prediction_result.risk_level)"
              :description="`预测概率: ${(bloodSugarPrediction.prediction_result.probability * 100).toFixed(1)}%`"
              show-icon
              class="risk-alert"
            />
            
            <el-divider>趋势分析</el-divider>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="趋势方向">
                <el-tag :type="getTrendTagType(bloodSugarPrediction.prediction_result.trend)">
                  {{ getTrendLabel(bloodSugarPrediction.prediction_result.trend) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="预测日期">
                {{ formatDate(bloodSugarPrediction.prediction_date) }}
              </el-descriptions-item>
            </el-descriptions>
            
            <el-divider>影响因素</el-divider>
            <div class="factors">
              <el-tag v-for="factor in bloodSugarPrediction.prediction_result.factors" :key="factor" class="factor-tag">
                {{ factor }}
              </el-tag>
            </div>
            
            <el-divider>建议</el-divider>
            <ul class="recommendations">
              <li v-for="rec in bloodSugarPrediction.prediction_result.recommendations" :key="rec">
                {{ rec }}
              </li>
            </ul>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 并发症风险 -->
      <el-tab-pane label="⚠️ 并发症风险" name="complications">
        <el-card>
          <template #header>
            <span>并发症风险评估</span>
          </template>
          
          <el-form inline>
            <el-form-item label="并发症类型">
              <el-select v-model="complicationType" style="width: 180px">
                <el-option label="糖尿病视网膜病变" value="retinopathy" />
                <el-option label="糖尿病肾病" value="nephropathy" />
                <el-option label="糖尿病神经病变" value="neuropathy" />
                <el-option label="心血管疾病" value="cardiovascular" />
                <el-option label="糖尿病足" value="foot" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="predictComplication" :loading="predicting">
                评估风险
              </el-button>
            </el-form-item>
          </el-form>
          
          <div v-if="complicationPrediction" class="prediction-result">
            <div class="risk-meter">
              <el-progress
                :percentage="complicationPrediction.probability * 100"
                :color="getRiskColor(complicationPrediction.risk_level)"
                :stroke-width="20"
              />
              <div class="risk-label">
                风险等级: <span :class="`risk-${complicationPrediction.risk_level}`">{{ getRiskLabel(complicationPrediction.risk_level) }}</span>
              </div>
            </div>
            
            <el-divider>风险因素</el-divider>
            <ul class="factor-list">
              <li v-for="factor in complicationPrediction.factors" :key="factor">{{ factor }}</li>
            </ul>
            
            <el-divider>预防建议</el-divider>
            <ul class="recommendations">
              <li v-for="rec in complicationPrediction.recommendations" :key="rec">{{ rec }}</li>
            </ul>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 干预效果预测 -->
      <el-tab-pane label="💊 干预效果" name="intervention">
        <el-card>
          <template #header>
            <span>干预方案效果预测</span>
          </template>
          
          <el-form inline>
            <el-form-item label="干预方案">
              <el-select v-model="interventionType" style="width: 200px">
                <el-option label="增加运动" value="exercise" />
                <el-option label="调整饮食" value="diet" />
                <el-option label="药物治疗调整" value="medication" />
                <el-option label="血糖监测强化" value="monitoring" />
                <el-option label="综合管理" value="comprehensive" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="predictIntervention" :loading="predicting">
                预测效果
              </el-button>
            </el-form-item>
          </el-form>
          
          <div v-if="interventionPrediction" class="prediction-result">
            <el-card>
              <template #header>{{ interventionPrediction.intervention_name }}</template>
              
              <el-row :gutter="20">
                <el-col :span="8">
                  <el-statistic title="血糖变化" :value="interventionPrediction.predicted_effect.blood_sugar_change" suffix="mmol/L">
                    <template #default>
                      <span :class="getChangeClass(interventionPrediction.predicted_effect.blood_sugar_change)">
                        {{ interventionPrediction.predicted_effect.blood_sugar_change > 0 ? '+' : '' }}{{ interventionPrediction.predicted_effect.blood_sugar_change }}
                      </span>
                    </template>
                  </el-statistic>
                </el-col>
                <el-col :span="8">
                  <el-statistic title="预测置信度" :value="interventionPrediction.predicted_effect.confidence * 100" suffix="%" />
                </el-col>
              </el-row>
            </el-card>
            
            <el-divider>预测时间线</el-divider>
            <el-table :data="interventionPrediction.timeline" style="width: 100%">
              <el-table-column prop="day" label="天数" />
              <el-table-column prop="predicted_value" label="预测值" />
            </el-table>
            
            <el-divider>建议</el-divider>
            <ul class="recommendations">
              <li v-for="rec in interventionPrediction.recommendations" :key="rec">{{ rec }}</li>
            </ul>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 预测历史 -->
      <el-tab-pane label="📋 预测历史" name="history">
        <el-card>
          <template #header>
            <span>历史预测记录</span>
          </template>
          
          <el-table :data="predictionHistory" style="width: 100%">
            <el-table-column prop="type" label="预测类型" width="150">
              <template #default="{ row }">
                <el-tag>{{ getTypeLabel(row.type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="prediction_date" label="预测日期" width="180">
              <template #default="{ row }">
                {{ formatDate(row.prediction_date) }}
              </template>
            </el-table-column>
            <el-table-column label="风险等级" width="120">
              <template #default="{ row }">
                <el-tag :type="getRiskType(row.prediction_result.risk_level)">
                  {{ getRiskLabel(row.prediction_result.risk_level) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="prediction_result.probability" label="概率" width="100">
              <template #default="{ row }">
                {{ (row.prediction_result.probability * 100).toFixed(1) }}%
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
          
          <el-empty v-if="predictionHistory.length === 0" description="暂无预测历史" />
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const patientId = ref('patient_001')

const activeTab = ref('blood-sugar')
const predictionDays = ref(7)
const complicationType = ref('retinopathy')
const interventionType = ref('exercise')
const predicting = ref(false)

const bloodSugarPrediction = ref(null)
const complicationPrediction = ref(null)
const interventionPrediction = ref(null)
const predictionHistory = ref([])

const predictBloodSugar = async () => {
  predicting.value = true
  try {
    const res = await axios.post('/api/v1/prediction/blood-sugar', {
      patient_id: patientId.value,
      days: predictionDays.value
    })
    if (res.data.success) {
      bloodSugarPrediction.value = res.data.prediction
      ElMessage.success('预测完成')
    }
  } catch (e) {
    ElMessage.error('预测失败')
  } finally {
    predicting.value = false
  }
}

const predictComplication = async () => {
  predicting.value = true
  try {
    const res = await axios.post('/api/v1/prediction/complication', {
      patient_id: patientId.value,
      complication_type: complicationType.value
    })
    if (res.data.success) {
      complicationPrediction.value = res.data.prediction
      ElMessage.success('评估完成')
    }
  } catch (e) {
    ElMessage.error('评估失败')
  } finally {
    predicting.value = false
  }
}

const predictIntervention = async () => {
  predicting.value = true
  try {
    const res = await axios.post('/api/v1/prediction/intervention-effect', {
      patient_id: patientId.value,
      intervention_type: interventionType.value
    })
    if (res.data.success) {
      interventionPrediction.value = res.data.prediction
      ElMessage.success('预测完成')
    }
  } catch (e) {
    ElMessage.error('预测失败')
  } finally {
    predicting.value = false
  }
}

const loadHistory = async () => {
  try {
    const res = await axios.get(`/api/v1/prediction/history/${patientId.value}`)
    if (res.data.success) {
      predictionHistory.value = res.data.predictions
    }
  } catch (e) {
    console.error('加载历史失败', e)
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

const getTypeLabel = (type) => {
  const labels = {
    blood_sugar: '血糖预测',
    complication: '并发症风险',
    intervention: '干预效果'
  }
  return labels[type] || type
}

const getRiskLabel = (level) => {
  const labels = { low: '低风险', medium: '中等风险', high: '高风险', urgent: '紧急' }
  return labels[level] || level
}

const getRiskType = (level) => {
  const types = { low: 'success', medium: 'warning', high: 'error', urgent: 'error' }
  return types[level] || 'info'
}

const getRiskColor = (level) => {
  const colors = { low: '#67C23A', medium: '#E6A23C', high: '#F56C6C', urgent: '#F56C6C' }
  return colors[level] || '#909399'
}

const getTrendLabel = (trend) => {
  const labels = { rising: '上升', falling: '下降', stable: '稳定' }
  return labels[trend] || trend
}

const getTrendTagType = (trend) => {
  const types = { rising: 'danger', falling: 'success', stable: 'info' }
  return types[trend] || 'info'
}

const getChangeClass = (change) => {
  if (change < 0) return 'change-negative'
  if (change > 0) return 'change-positive'
  return 'change-neutral'
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.prediction-container {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
  text-align: center;
}

.prediction-result {
  margin-top: 20px;
}

.risk-alert {
  margin-bottom: 20px;
}

.risk-meter {
  text-align: center;
  padding: 20px;
}

.risk-label {
  margin-top: 10px;
  font-size: 16px;
}

.risk-low { color: #67C23A; }
.risk-medium { color: #E6A23C; }
.risk-high { color: #F56C6C; }
.risk-urgent { color: #F56C6C; }

.factors {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.factor-tag {
  margin: 5px;
}

.factor-list, .recommendations {
  padding-left: 20px;
}

.factor-list li, .recommendations li {
  margin-bottom: 8px;
  color: #606266;
}

.change-negative {
  color: #67C23A;
}

.change-positive {
  color: #F56C6C;
}

.change-neutral {
  color: #909399;
}
</style>
