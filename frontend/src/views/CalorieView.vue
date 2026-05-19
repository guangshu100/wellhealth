<template>
  <div class="calorie-view">
    <div class="page-header">
      <h1>🔥 卡路里跟踪</h1>
      <p>拍照识别或文字描述食物、营养计算、饮食记录</p>
    </div>

    <el-tabs v-model="activeTab" type="border-card">
      <!-- 拍照识别 -->
      <el-tab-pane label="📷 拍照识别" name="camera">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card>
              <template #header>拍摄或上传食物图片</template>
              <div class="upload-area">
                <div v-if="!imagePreview" class="upload-placeholder" @click="triggerUpload">
                  <el-icon :size="60" :style="{ color: 'var(--color-primary)' }"><Camera /></el-icon>
                  <p>点击上传图片</p>
                  <p class="upload-hint">支持 JPG、PNG 格式</p>
                </div>
                <div v-else class="image-preview">
                  <img :src="imagePreview" alt="食物图片" />
                  <el-button type="danger" size="small" class="remove-btn" @click="removeImage">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
                <input
                  ref="fileInput"
                  type="file"
                  accept="image/*"
                  style="display: none"
                  @change="handleFileChange"
                />
              </div>
              <el-button 
                type="primary" 
                @click="analyzeImage" 
                :loading="analyzing"
                :disabled="!imageBase64"
                style="margin-top: 16px; width: 100%;"
              >
                <el-icon v-if="!analyzing"><MagicStick /></el-icon>
                {{ analyzing ? '识别中...' : 'AI智能识别' }}
              </el-button>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card v-if="analysisResult">
              <template #header>识别结果</template>
              <el-table :data="analysisResult.foods" size="small">
                <el-table-column prop="name" label="食物" />
                <el-table-column prop="serving" label="份量(g)" />
                <el-table-column prop="calories" label="热量(kcal)">
                  <template #default="{ row }">
                    <span style="color: #f56c6c; font-weight: bold;">{{ row.calories }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="protein" label="蛋白质(g)" />
                <el-table-column prop="carbs" label="碳水(g)" />
                <el-table-column prop="fat" label="脂肪(g)" />
              </el-table>
              <div class="total-summary">
                <el-statistic title="总热量" :value="analysisResult.total_calories" suffix="kcal" />
                <el-statistic title="总蛋白质" :value="analysisResult.total_protein" suffix="g" />
                <el-statistic title="总碳水" :value="analysisResult.total_carbs" suffix="g" />
                <el-statistic title="总脂肪" :value="analysisResult.total_fat" suffix="g" />
              </div>
              <el-button type="success" @click="saveRecord" style="margin-top: 16px;">
                保存记录
              </el-button>
            </el-card>
            <el-card v-else>
              <el-empty description="上传图片后点击识别">
                <el-button type="primary" @click="triggerUpload">
                  <el-icon><Upload /></el-icon>
                  选择图片
                </el-button>
              </el-empty>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- 文字描述 -->
      <el-tab-pane label="📝 文字描述" name="text">
        <el-card>
          <template #header>描述您吃了什么</template>
          <el-input
            v-model="foodDescription"
            type="textarea"
            :rows="4"
            placeholder="例如：早餐吃了2个馒头和一杯豆浆，午餐吃了炒饭和宫保鸡丁"
          />
          <el-button type="primary" @click="analyzeText" :loading="analyzingText" style="margin-top: 16px;">
            分析食物
          </el-button>
        </el-card>

        <el-card v-if="textAnalysisResult" style="margin-top: 20px;">
          <template #header>分析结果</template>
          <el-table :data="textAnalysisResult.foods" size="small">
            <el-table-column prop="name" label="食物" />
            <el-table-column prop="serving_size" label="份量(g)" />
            <el-table-column prop="calories" label="热量(kcal)">
              <template #default="{ row }">
                <span style="color: #f56c6c; font-weight: bold;">{{ row.calories }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="protein" label="蛋白质(g)" />
            <el-table-column prop="carbs" label="碳水(g)" />
            <el-table-column prop="fat" label="脂肪(g)" />
          </el-table>
          <div class="total-summary">
            <el-statistic title="总热量" :value="textAnalysisResult.nutrition?.calories || 0" suffix="kcal" />
            <el-statistic title="总蛋白质" :value="textAnalysisResult.nutrition?.protein || 0" suffix="g" />
            <el-statistic title="总碳水" :value="textAnalysisResult.nutrition?.carbs || 0" suffix="g" />
            <el-statistic title="总脂肪" :value="textAnalysisResult.nutrition?.fat || 0" suffix="g" />
          </div>
          <el-button type="success" @click="saveTextRecord" style="margin-top: 16px;">
            保存记录
          </el-button>
        </el-card>
      </el-tab-pane>

      <!-- 饮食记录 -->
      <el-tab-pane label="📋 饮食记录" name="records">
        <el-card>
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span>饮食记录</span>
              <el-select v-model="selectedPatientId" placeholder="选择患者" @change="loadRecords" style="width: 200px;">
                <el-option v-for="p in patients" :key="p.id" :label="p.name" :value="p.id" />
              </el-select>
            </div>
          </template>
          <el-table :data="foodRecords" v-loading="recordsLoading">
            <el-table-column prop="meal_type" label="餐次" width="100">
              <template #default="{ row }">
                <el-tag :type="getMealTypeTag(row.meal_type)">{{ getMealTypeName(row.meal_type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="food_name" label="食物" />
            <el-table-column prop="calories" label="热量(kcal)" width="100">
              <template #default="{ row }">
                <span style="color: #f56c6c; font-weight: bold;">{{ row.calories }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="protein" label="蛋白质(g)" width="80" />
            <el-table-column prop="carbs" label="碳水(g)" width="80" />
            <el-table-column prop="fat" label="脂肪(g)" width="80" />
            <el-table-column prop="record_date" label="记录日期" width="120" />
            <el-table-column prop="created_at" label="记录时间" width="180" />
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button type="danger" size="small" @click="deleteRecord(row.id)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!recordsLoading && foodRecords.length === 0" description="暂无饮食记录" />
        </el-card>
      </el-tab-pane>

      <!-- 营养汇总 -->
      <el-tab-pane label="📊 营养汇总" name="summary">
        <el-card>
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span>营养摄入汇总</span>
              <div>
                <el-select v-model="summaryPatientId" placeholder="选择患者" @change="loadSummary" style="width: 200px; margin-right: 10px;">
                  <el-option v-for="p in patients" :key="p.id" :label="p.name" :value="p.id" />
                </el-select>
                <el-select v-model="summaryDays" placeholder="统计天数" @change="loadSummary" style="width: 120px;">
                  <el-option label="最近7天" :value="7" />
                  <el-option label="最近14天" :value="14" />
                  <el-option label="最近30天" :value="30" />
                </el-select>
              </div>
            </div>
          </template>
          <div v-if="nutritionSummary" class="summary-content">
            <el-row :gutter="20">
              <el-col :span="6">
                <el-card shadow="hover">
                  <el-statistic title="平均每日热量" :value="nutritionSummary.average?.calories || 0" suffix="kcal" />
                </el-card>
              </el-col>
              <el-col :span="6">
                <el-card shadow="hover">
                  <el-statistic title="平均每日蛋白质" :value="nutritionSummary.average?.protein || 0" suffix="g" />
                </el-card>
              </el-col>
              <el-col :span="6">
                <el-card shadow="hover">
                  <el-statistic title="平均每日碳水" :value="nutritionSummary.average?.carbs || 0" suffix="g" />
                </el-card>
              </el-col>
              <el-col :span="6">
                <el-card shadow="hover">
                  <el-statistic title="平均每日脂肪" :value="nutritionSummary.average?.fat || 0" suffix="g" />
                </el-card>
              </el-col>
            </el-row>
            <el-row :gutter="20" style="margin-top: 20px;">
              <el-col :span="12">
                <el-card>
                  <template #header>每日热量趋势</template>
                  <div class="trend-chart">
                    <div v-for="(value, date) in nutritionSummary.daily_stats" :key="date" class="trend-item">
                      <span class="trend-date">{{ date }}</span>
                      <div class="trend-bar" :style="{ width: (value.calories / 2500 * 100) + '%' }"></div>
                      <span class="trend-value">{{ value.calories }} kcal</span>
                    </div>
                  </div>
                </el-card>
              </el-col>
              <el-col :span="12">
                <el-card>
                  <template #header>营养建议</template>
                  <div class="suggestions">
                    <el-alert v-if="nutritionSummary.average?.calories > 2000" type="warning" :closable="false">
                      热量摄入偏高，建议适当减少主食和油脂摄入
                    </el-alert>
                    <el-alert v-if="nutritionSummary.average?.calories < 1500" type="warning" :closable="false">
                      热量摄入偏低，建议增加蛋白质和健康脂肪摄入
                    </el-alert>
                    <el-alert v-if="nutritionSummary.average?.protein < 50" type="info" :closable="false">
                      蛋白质摄入不足，建议增加鸡胸肉、鱼、鸡蛋等优质蛋白
                    </el-alert>
                    <el-alert v-if="nutritionSummary.average?.carbs > 300" type="info" :closable="false">
                      碳水化合物摄入偏高，建议用粗粮替代部分精制碳水
                    </el-alert>
                    <el-alert v-if="nutritionSummary.average?.fiber < 20" type="info" :closable="false">
                      膳食纤维摄入不足，建议增加蔬菜和水果摄入
                    </el-alert>
                    <el-alert v-if="nutritionSummary.average?.calories >= 1500 && nutritionSummary.average?.calories <= 2000 && nutritionSummary.average?.protein >= 50" type="success" :closable="false">
                      营养摄入均衡，请继续保持健康的饮食习惯
                    </el-alert>
                  </div>
                </el-card>
              </el-col>
            </el-row>
          </div>
          <el-empty v-else description="请选择患者查看营养汇总" />
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Camera, Delete, Upload, MagicStick } from '@element-plus/icons-vue'

const activeTab = ref('camera')

const fileInput = ref<HTMLInputElement | null>(null)
const imageBase64 = ref('')
const imagePreview = ref('')
const analyzing = ref(false)
const analysisResult = ref<any>(null)

const foodDescription = ref('')
const analyzingText = ref(false)
const textAnalysisResult = ref<any>(null)
const selectedMealType = ref('午餐')

const patients = ref<any[]>([])
const selectedPatientId = ref<number | null>(null)
const summaryPatientId = ref<number | null>(null)
const summaryDays = ref(7)

const foodRecords = ref<any[]>([])
const recordsLoading = ref(false)
const nutritionSummary = ref<any>(null)

const mealTypes = [
  { value: 'breakfast', label: '早餐' },
  { value: 'lunch', label: '午餐' },
  { value: 'dinner', label: '晚餐' },
  { value: 'snack', label: '加餐' },
]

onMounted(() => {
  loadPatients()
})

async function loadPatients() {
  try {
    const res = await fetch('/api/v1/patients')
    const data = await res.json()
    patients.value = data.patients || data || []
    if (patients.value.length > 0) {
      selectedPatientId.value = patients.value[0].id
      summaryPatientId.value = patients.value[0].id
      loadRecords()
      loadSummary()
    }
  } catch (e) {
    console.error('Failed to load patients:', e)
  }
}

function triggerUpload() {
  fileInput.value?.click()
}

function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = (e) => {
    const result = e.target?.result as string
    imagePreview.value = result
    imageBase64.value = result.split(',')[1]
    analysisResult.value = null
  }
  reader.readAsDataURL(file)
}

function removeImage() {
  imagePreview.value = ''
  imageBase64.value = ''
  analysisResult.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

async function analyzeImage() {
  if (!imageBase64.value) {
    ElMessage.warning('请先上传图片')
    return
  }
  analyzing.value = true
  try {
    const formData = new FormData()
    formData.append('image', imageBase64.value)
    if (selectedPatientId.value) {
      formData.append('patient_id', String(selectedPatientId.value))
    }

    const res = await fetch('/api/v1/calorie/analyze-image', {
      method: 'POST',
      body: formData,
    })
    const data = await res.json()
    
    if (data.success) {
      analysisResult.value = data
      ElMessage.success(data.message || '识别成功')
    } else {
      ElMessage.error(data.message || '识别失败')
    }
  } catch (e) {
    ElMessage.error('识别失败，请重试')
  } finally {
    analyzing.value = false
  }
}

async function analyzeText() {
  if (!foodDescription.value.trim()) {
    ElMessage.warning('请输入食物描述')
    return
  }
  analyzingText.value = true
  try {
    const res = await fetch('/api/v1/calorie/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ food_description: foodDescription.value })
    })
    const data = await res.json()
    textAnalysisResult.value = data
  } catch (e) {
    ElMessage.error('分析失败')
  } finally {
    analyzingText.value = false
  }
}

async function saveRecord() {
  if (!analysisResult.value || !selectedPatientId.value) {
    ElMessage.warning('请先识别食物并选择患者')
    return
  }
  try {
    for (const food of analysisResult.value.foods) {
      await fetch('/api/v1/calorie/record', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patient_id: String(selectedPatientId.value),
          food_name: food.name,
          calories: food.calories,
          protein: food.protein || 0,
          carbs: food.carbs || 0,
          fat: food.fat || 0,
          fiber: food.fiber || 0,
          serving_size: food.serving,
          meal_type: selectedMealType.value === '午餐' ? 'lunch' : selectedMealType.value === '早餐' ? 'breakfast' : selectedMealType.value === '晚餐' ? 'dinner' : 'snack',
        })
      })
    }
    ElMessage.success('记录保存成功')
    analysisResult.value = null
    removeImage()
    loadRecords()
    loadSummary()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

async function saveTextRecord() {
  if (!textAnalysisResult.value || !selectedPatientId.value) {
    ElMessage.warning('请先分析食物并选择患者')
    return
  }
  try {
    for (const food of textAnalysisResult.value.foods) {
      await fetch('/api/v1/calorie/record', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patient_id: String(selectedPatientId.value),
          food_name: food.name,
          calories: food.calories,
          protein: food.protein || 0,
          carbs: food.carbs || 0,
          fat: food.fat || 0,
          fiber: food.fiber || 0,
          serving_size: food.serving_size || 100,
          meal_type: selectedMealType.value === '午餐' ? 'lunch' : selectedMealType.value === '早餐' ? 'breakfast' : selectedMealType.value === '晚餐' ? 'dinner' : 'snack',
        })
      })
    }
    ElMessage.success('记录保存成功')
    textAnalysisResult.value = null
    foodDescription.value = ''
    loadRecords()
    loadSummary()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

async function loadRecords() {
  if (!selectedPatientId.value) return
  recordsLoading.value = true
  try {
    const res = await fetch(`/api/v1/calorie/records/${selectedPatientId.value}`)
    const data = await res.json()
    foodRecords.value = data.records || []
  } catch (e) {
    console.error('Failed to load records:', e)
  } finally {
    recordsLoading.value = false
  }
}

async function loadSummary() {
  if (!summaryPatientId.value) return
  try {
    const res = await fetch(`/api/v1/calorie/summary/${summaryPatientId.value}?days=${summaryDays.value}`)
    const data = await res.json()
    nutritionSummary.value = data
  } catch (e) {
    console.error('Failed to load summary:', e)
  }
}

async function deleteRecord(recordId: number) {
  if (!selectedPatientId.value) return
  try {
    await fetch(`/api/v1/calorie/record/${recordId}?patient_id=${selectedPatientId.value}`, { method: 'DELETE' })
    ElMessage.success('删除成功')
    loadRecords()
    loadSummary()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

function getMealTypeTag(type: string) {
  const map: Record<string, string> = {
    'breakfast': 'success',
    'lunch': 'warning',
    'dinner': 'danger',
    'snack': 'info'
  }
  return map[type] || 'info'
}

function getMealTypeName(type: string) {
  const map: Record<string, string> = {
    'breakfast': '早餐',
    'lunch': '午餐',
    'dinner': '晚餐',
    'snack': '加餐'
  }
  return map[type] || type
}
</script>

<style scoped>
.calorie-view {
  padding: 20px;
}

.page-header {
  text-align: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  color: #303133;
}

.page-header p {
  margin: 10px 0 0;
  color: #909399;
}

.upload-area {
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-placeholder {
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  padding: 60px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.upload-placeholder:hover {
  border-color: var(--color-primary);
  background: #f5f7fa;
}

.upload-placeholder p {
  margin-top: 10px;
  color: #606266;
}

.upload-hint {
  font-size: 12px;
  color: #909399;
}

.image-preview {
  position: relative;
  width: 100%;
}

.image-preview img {
  width: 100%;
  max-height: 350px;
  object-fit: contain;
  border-radius: 8px;
}

.remove-btn {
  position: absolute;
  top: 10px;
  right: 10px;
}

.total-summary {
  display: flex;
  justify-content: space-around;
  margin-top: 20px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.food-tag {
  display: inline-block;
  padding: 2px 8px;
  margin: 2px;
  background: #ecf5ff;
  border-radius: 4px;
  font-size: 12px;
  color: var(--color-primary);
}

.trend-chart {
  max-height: 300px;
  overflow-y: auto;
}

.trend-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.trend-date {
  width: 80px;
  font-size: 12px;
  color: #606266;
}

.trend-bar {
  height: 20px;
  background: var(--gradient-button);
  border-radius: 4px;
  margin-right: 10px;
  min-width: 10px;
}

.trend-value {
  font-size: 12px;
  color: #303133;
  font-weight: bold;
}

.suggestions .el-alert {
  margin-bottom: 10px;
}
</style>
