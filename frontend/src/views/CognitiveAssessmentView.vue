<template>
  <div class="cognitive-assessment-container">
    <el-card class="header-card">
      <h2>认知评估</h2>
      <p>通过文本和语音分析评估认知健康状况</p>
    </el-card>

    <el-tabs v-model="activeTab" type="border-card">
      <el-tab-pane label="📝 文本分析" name="text">
        <el-card>
          <template #header>
            <span>文本认知分析</span>
          </template>
          <el-form>
            <el-form-item label="输入文本">
              <el-input
                v-model="inputText"
                type="textarea"
                :rows="6"
                placeholder="请输入需要分析的文本内容，如日记、对话记录等..."
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="analyzeText" :loading="analyzing">
                开始评估
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="🎤 语音分析" name="speech">
        <el-card>
          <template #header>
            <span>语音认知分析</span>
          </template>
          <el-form>
            <el-form-item label="上传音频">
              <el-upload
                ref="uploadRef"
                :auto-upload="false"
                :limit="1"
                accept="audio/*"
                :on-change="handleFileChange"
                :on-remove="handleFileRemove"
              >
                <el-button type="primary">选择音频文件</el-button>
                <template #tip>
                  <div class="upload-tip">支持 MP3、WAV、M4A 等音频格式</div>
                </template>
              </el-upload>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="analyzeSpeech" :loading="analyzing" :disabled="!audioFile">
                开始评估
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <div v-if="assessmentResult" class="assessment-result">
      <el-card>
        <template #header>
          <span>评估结果</span>
        </template>

        <div class="score-section">
          <div class="overall-score">
            <div class="score-circle" :style="{ borderColor: getScoreColor(assessmentResult.overall_score) }">
              <span class="score-value" :style="{ color: getScoreColor(assessmentResult.overall_score) }">
                {{ assessmentResult.overall_score }}
              </span>
              <span class="score-label">综合评分</span>
            </div>
            <div class="risk-badge">
              <el-tag :type="getRiskType(assessmentResult.risk_level)" size="large" effect="dark">
                {{ getRiskLabel(assessmentResult.risk_level) }}
              </el-tag>
            </div>
          </div>
        </div>

        <el-divider>四维度评分</el-divider>

        <div class="dimension-scores">
          <div class="dimension-item">
            <div class="dimension-header">
              <span class="dimension-name">语言能力</span>
              <span class="dimension-score">{{ assessmentResult.language_score }}</span>
            </div>
            <el-progress
              :percentage="assessmentResult.language_score"
              :color="getDimensionColor(assessmentResult.language_score)"
              :stroke-width="14"
            />
          </div>
          <div class="dimension-item">
            <div class="dimension-header">
              <span class="dimension-name">记忆能力</span>
              <span class="dimension-score">{{ assessmentResult.memory_score }}</span>
            </div>
            <el-progress
              :percentage="assessmentResult.memory_score"
              :color="getDimensionColor(assessmentResult.memory_score)"
              :stroke-width="14"
            />
          </div>
          <div class="dimension-item">
            <div class="dimension-header">
              <span class="dimension-name">执行功能</span>
              <span class="dimension-score">{{ assessmentResult.executive_function_score }}</span>
            </div>
            <el-progress
              :percentage="assessmentResult.executive_function_score"
              :color="getDimensionColor(assessmentResult.executive_function_score)"
              :stroke-width="14"
            />
          </div>
          <div class="dimension-item">
            <div class="dimension-header">
              <span class="dimension-name">注意力</span>
              <span class="dimension-score">{{ assessmentResult.attention_score }}</span>
            </div>
            <el-progress
              :percentage="assessmentResult.attention_score"
              :color="getDimensionColor(assessmentResult.attention_score)"
              :stroke-width="14"
            />
          </div>
        </div>

        <el-divider>置信度</el-divider>
        <el-progress
          :percentage="Math.round(assessmentResult.confidence * 100)"
          :stroke-width="10"
          color="#5E8B5A"
        />

        <el-divider>建议</el-divider>
        <ul class="recommendations">
          <li v-for="(rec, index) in assessmentResult.recommendations" :key="index">
            {{ rec }}
          </li>
        </ul>
      </el-card>
    </div>

    <el-card class="history-card">
      <template #header>
        <span>历史评估记录</span>
      </template>
      <el-table :data="assessments" style="width: 100%">
        <el-table-column prop="created_at" label="评估日期" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="assessment_type" label="评估类型" width="120">
          <template #default="{ row }">
            <el-tag>{{ getTypeLabel(row.assessment_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="overall_score" label="综合评分" width="120">
          <template #default="{ row }">
            <span :style="{ color: getScoreColor(row.overall_score), fontWeight: 'bold' }">
              {{ row.overall_score }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="risk_level" label="风险等级" width="120">
          <template #default="{ row }">
            <el-tag :type="getRiskType(row.risk_level)">{{ getRiskLabel(row.risk_level) }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="assessments.length === 0" description="暂无评估记录" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { cognitiveApi } from '@/api/cognitive'

const authStore = useAuthStore()

const activeTab = ref('text')
const inputText = ref('')
const audioFile = ref(null)
const analyzing = ref(false)
const assessmentResult = ref(null)
const assessments = ref([])

const handleFileChange = (file) => {
  audioFile.value = file.raw
}

const handleFileRemove = () => {
  audioFile.value = null
}

const analyzeText = async () => {
  if (!inputText.value.trim()) {
    ElMessage.warning('请输入需要分析的文本内容')
    return
  }
  analyzing.value = true
  try {
    const res = await cognitiveApi.analyzeText(inputText.value)
    assessmentResult.value = res
    ElMessage.success('评估完成')
    loadAssessments()
  } catch (e) {
    ElMessage.error('评估失败，请稍后重试')
  } finally {
    analyzing.value = false
  }
}

const analyzeSpeech = async () => {
  if (!audioFile.value) {
    ElMessage.warning('请上传音频文件')
    return
  }
  analyzing.value = true
  try {
    const formData = new FormData()
    formData.append('audio', audioFile.value)
    formData.append('user_id', authStore.userInfo?.id || '')
    const res = await cognitiveApi.analyzeSpeech(formData)
    assessmentResult.value = res
    ElMessage.success('评估完成')
    loadAssessments()
  } catch (e) {
    ElMessage.error('评估失败，请稍后重试')
  } finally {
    analyzing.value = false
  }
}

const loadAssessments = async () => {
  try {
    const res = await cognitiveApi.getAssessments(5)
    assessments.value = res.assessments || res || []
  } catch (e) {
    console.error('加载评估历史失败', e)
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

const getTypeLabel = (type) => {
  const labels = { text: '文本分析', speech: '语音分析' }
  return labels[type] || type
}

const getRiskLabel = (level) => {
  const labels = { low: '低风险', medium: '中等风险', high: '高风险' }
  return labels[level] || level
}

const getRiskType = (level) => {
  const types = { low: 'success', medium: 'warning', high: 'error' }
  return types[level] || 'info'
}

const getScoreColor = (score) => {
  if (score >= 80) return '#67C23A'
  if (score >= 60) return '#E6A23C'
  return '#F56C6C'
}

const getDimensionColor = (score) => {
  if (score >= 80) return '#67C23A'
  if (score >= 60) return '#E6A23C'
  return '#F56C6C'
}

onMounted(() => {
  loadAssessments()
})
</script>

<style scoped>
.cognitive-assessment-container {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
  text-align: center;
}

.header-card h2 {
  color: var(--color-primary, #5E8B5A);
  margin-bottom: 8px;
}

.header-card p {
  color: var(--color-text-secondary, #7F7D74);
}

.assessment-result {
  margin-top: 20px;
}

.score-section {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}

.overall-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.score-circle {
  width: 140px;
  height: 140px;
  border-radius: 50%;
  border: 6px solid;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.score-value {
  font-size: 42px;
  font-weight: bold;
  line-height: 1;
}

.score-label {
  font-size: 13px;
  color: var(--color-text-secondary, #7F7D74);
  margin-top: 4px;
}

.dimension-scores {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.dimension-item {
  padding: 0 10px;
}

.dimension-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.dimension-name {
  font-size: 14px;
  color: var(--color-text-primary, #2F2E2A);
}

.dimension-score {
  font-size: 16px;
  font-weight: bold;
  color: var(--color-primary, #5E8B5A);
}

.recommendations {
  padding-left: 20px;
}

.recommendations li {
  margin-bottom: 8px;
  color: #606266;
  line-height: 1.6;
}

.history-card {
  margin-top: 20px;
}

.upload-tip {
  font-size: 12px;
  color: var(--color-text-secondary, #7F7D74);
  margin-top: 4px;
}
</style>
