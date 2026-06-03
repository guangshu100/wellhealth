<template>
  <view class="page">
    <!-- 餐次选择器 -->
    <view class="meal-selector">
      <picker mode="selector" :range="mealTypes" range-key="label" @change="onMealTypeChange">
        <view class="meal-picker">
          <text class="meal-label">当前餐次：</text>
          <text class="meal-value">{{ currentMealType.label }}</text>
          <text class="arrow">▼</text>
        </view>
      </picker>
    </view>

    <!-- Tab切换 -->
    <view class="tab-bar">
      <view
        :class="['tab-item', { active: activeTab === 'camera' }]"
        @click="activeTab = 'camera'"
      >
        📷 拍照识别
      </view>
      <view
        :class="['tab-item', { active: activeTab === 'text' }]"
        @click="activeTab = 'text'"
      >
        📝 文字描述
      </view>
      <view
        :class="['tab-item', { active: activeTab === 'records' }]"
        @click="activeTab = 'records'"
      >
        📋 记录
      </view>
    </view>

    <!-- 拍照识别 -->
    <view class="tab-content" v-if="activeTab === 'camera'">
      <view class="upload-section">
        <!-- 上传区域 -->
        <view class="upload-box" @click="chooseImage">
          <view v-if="!imagePreview" class="upload-placeholder">
            <text class="upload-icon">📷</text>
            <text class="upload-text">点击拍照或上传</text>
            <text class="upload-hint">支持 JPG、PNG 格式</text>
          </view>
          <view v-else class="image-preview">
            <image :src="imagePreview" mode="aspectFit" class="preview-img" />
            <view class="remove-btn" @click.stop="removeImage">
              <text>✕</text>
            </view>
          </view>
        </view>

        <!-- 分析按钮 -->
        <button
          class="btn-analyze"
          :disabled="!imageBase64 || analyzing"
          @click="analyzeImage"
        >
          <text v-if="analyzing">识别中...</text>
          <text v-else>🤖 AI智能识别</text>
        </button>
      </view>

      <!-- 识别结果 -->
      <view class="result-section" v-if="analysisResult">
        <view class="result-header">
          <text class="result-title">识别结果</text>
          <text class="result-count">{{ analysisResult.foods?.length || 0 }} 种食物</text>
        </view>

        <!-- 食物列表 -->
        <view class="food-list">
          <view
            v-for="(food, index) in analysisResult.foods"
            :key="index"
            class="food-item"
          >
            <view class="food-info">
              <text class="food-name">{{ food.name }}</text>
              <text class="food-serving">{{ food.serving }}g</text>
            </view>
            <view class="food-nutrition">
              <view class="nutrition-item">
                <text class="nutrition-value">{{ food.calories }}</text>
                <text class="nutrition-label">千卡</text>
              </view>
              <view class="nutrition-item">
                <text class="nutrition-value">{{ food.protein }}g</text>
                <text class="nutrition-label">蛋白质</text>
              </view>
              <view class="nutrition-item">
                <text class="nutrition-value">{{ food.carbs }}g</text>
                <text class="nutrition-label">碳水</text>
              </view>
              <view class="nutrition-item">
                <text class="nutrition-value">{{ food.fat }}g</text>
                <text class="nutrition-label">脂肪</text>
              </view>
            </view>
          </view>
        </view>

        <!-- 总计 -->
        <view class="total-section">
          <view class="total-header">营养总计</view>
          <view class="total-grid">
            <view class="total-item">
              <text class="total-value">{{ analysisResult.total_calories || 0 }}</text>
              <text class="total-label">千卡</text>
            </view>
            <view class="total-item">
              <text class="total-value">{{ analysisResult.total_protein || 0 }}g</text>
              <text class="total-label">蛋白质</text>
            </view>
            <view class="total-item">
              <text class="total-value">{{ analysisResult.total_carbs || 0 }}g</text>
              <text class="total-label">碳水</text>
            </view>
            <view class="total-item">
              <text class="total-value">{{ analysisResult.total_fat || 0 }}g</text>
              <text class="total-label">脂肪</text>
            </view>
          </view>
        </view>

        <!-- 保存按钮 -->
        <button class="btn-save" @click="saveRecord">💾 保存记录</button>
      </view>
    </view>

    <!-- 文字描述 -->
    <view class="tab-content" v-if="activeTab === 'text'">
      <view class="text-section">
        <textarea
          class="text-input"
          v-model="foodDescription"
          placeholder="描述您吃了什么，例如：早餐吃了2个馒头和一杯豆浆，午餐吃了炒饭和宫保鸡丁"
          :adjust-position="true"
        />
        <button class="btn-analyze" :disabled="!foodDescription.trim() || analyzingText" @click="analyzeText">
          <text v-if="analyzingText">分析中...</text>
          <text v-else>🔍 分析食物</text>
        </button>
      </view>

      <!-- 分析结果 -->
      <view class="result-section" v-if="textResult">
        <view class="result-header">
          <text class="result-title">分析结果</text>
        </view>

        <view class="food-list">
          <view
            v-for="(food, index) in textResult.foods"
            :key="index"
            class="food-item"
          >
            <view class="food-info">
              <text class="food-name">{{ food.name }}</text>
              <text class="food-serving">{{ food.serving_size || 100 }}g</text>
            </view>
            <view class="food-nutrition">
              <view class="nutrition-item highlight">
                <text class="nutrition-value">{{ food.calories }}</text>
                <text class="nutrition-label">千卡</text>
              </view>
            </view>
          </view>
        </view>

        <button class="btn-save" @click="saveTextRecord">💾 保存记录</button>
      </view>
    </view>

    <!-- 饮食记录 -->
    <view class="tab-content" v-if="activeTab === 'records'">
      <view class="records-header">
        <picker mode="selector" :range="patients" range-key="name" @change="onPatientChange">
          <view class="patient-picker">
            <text>{{ currentPatient?.name || '选择患者' }}</text>
            <text class="arrow">▼</text>
          </view>
        </picker>
      </view>

      <scroll-view scroll-y class="records-list">
        <view v-if="records.length === 0" class="empty-records">
          <text>暂无饮食记录</text>
        </view>

        <view
          v-for="record in records"
          :key="record.id"
          class="record-item"
        >
          <view class="record-header">
            <text class="record-meal">{{ getMealTypeName(record.meal_type) }}</text>
            <text class="record-date">{{ record.record_date }}</text>
          </view>
          <view class="record-content">
            <text class="record-food">{{ record.food_name }}</text>
            <text class="record-calories">{{ record.calories }} kcal</text>
          </view>
          <view class="record-actions">
            <view class="action-btn danger" @click="deleteRecord(record.id)">
              <text>🗑️ 删除</text>
            </view>
          </view>
        </view>
      </scroll-view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { calorieApi, patientApi } from '@/utils/api'

const activeTab = ref('camera')
const imageBase64 = ref('')
const imagePreview = ref('')
const analyzing = ref(false)
const analysisResult = ref<any>(null)

const foodDescription = ref('')
const analyzingText = ref(false)
const textResult = ref<any>(null)

const mealTypes = [
  { label: '早餐', value: 'breakfast' },
  { label: '午餐', value: 'lunch' },
  { label: '晚餐', value: 'dinner' },
  { label: '加餐', value: 'snack' }
]
const currentMealType = ref(mealTypes[1])

const patients = ref<any[]>([])
const currentPatient = ref<any>(null)
const records = ref<any[]>([])

onMounted(async () => {
  await loadPatients()
})

const loadPatients = async () => {
  try {
    const res = await patientApi.getPatientList()
    patients.value = res.patients || []
    if (patients.value.length > 0) {
      currentPatient.value = patients.value[0]
      await loadRecords()
    }
  } catch (e) {
    console.error('Load patients failed:', e)
  }
}

const loadRecords = async () => {
  if (!currentPatient.value) return
  try {
    const res = await calorieApi.getRecords(currentPatient.value.id)
    records.value = res.records || []
  } catch (e) {
    console.error('Load records failed:', e)
  }
}

const chooseImage = () => {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['camera', 'album'],
    success: (res) => {
      const tempFile = res.tempFilePaths[0]
      uni.getFileSystemManager().readFile({
        filePath: tempFile,
        encoding: 'base64',
        success: (readRes) => {
          imageBase64.value = readRes.data
          imagePreview.value = tempFile
          analysisResult.value = null
        }
      })
    }
  })
}

const removeImage = () => {
  imageBase64.value = ''
  imagePreview.value = ''
  analysisResult.value = null
}

const analyzeImage = async () => {
  if (!imageBase64.value) {
    uni.showToast({ title: '请先上传图片', icon: 'none' })
    return
  }

  analyzing.value = true
  try {
    const res = await calorieApi.analyzeImage(imageBase64.value)
    if (res.success) {
      analysisResult.value = res
    } else {
      uni.showToast({ title: res.message || '识别失败', icon: 'none' })
    }
  } catch (e) {
    console.error('Analyze image failed:', e)
    uni.showToast({ title: '识别失败，请重试', icon: 'none' })
  } finally {
    analyzing.value = false
  }
}

const analyzeText = async () => {
  if (!foodDescription.value.trim()) return

  analyzingText.value = true
  try {
    const res = await calorieApi.analyzeText(foodDescription.value)
    if (res.success) {
      textResult.value = res
    } else {
      uni.showToast({ title: res.message || '分析失败', icon: 'none' })
    }
  } catch (e) {
    console.error('Analyze text failed:', e)
    uni.showToast({ title: '分析失败', icon: 'none' })
  } finally {
    analyzingText.value = false
  }
}

const saveRecord = async () => {
  if (!analysisResult.value || !currentPatient.value) {
    uni.showToast({ title: '请先识别食物并选择患者', icon: 'none' })
    return
  }

  try {
    for (const food of analysisResult.value.foods) {
      await calorieApi.addRecord({
        patient_id: currentPatient.value.id,
        food_name: food.name,
        calories: food.calories,
        protein: food.protein || 0,
        carbs: food.carbs || 0,
        fat: food.fat || 0,
        fiber: food.fiber || 0,
        serving_size: food.serving,
        meal_type: currentMealType.value.value
      })
    }

    uni.showToast({ title: '保存成功', icon: 'success' })
    analysisResult.value = null
    removeImage()
    await loadRecords()
    activeTab.value = 'records'
  } catch (e) {
    console.error('Save record failed:', e)
    uni.showToast({ title: '保存失败', icon: 'none' })
  }
}

const saveTextRecord = async () => {
  if (!textResult.value || !currentPatient.value) return

  try {
    for (const food of textResult.value.foods) {
      await calorieApi.addRecord({
        patient_id: currentPatient.value.id,
        food_name: food.name,
        calories: food.calories,
        protein: food.protein || 0,
        carbs: food.carbs || 0,
        fat: food.fat || 0,
        fiber: 0,
        serving_size: food.serving_size || 100,
        meal_type: currentMealType.value.value
      })
    }

    uni.showToast({ title: '保存成功', icon: 'success' })
    textResult.value = null
    foodDescription.value = ''
    await loadRecords()
    activeTab.value = 'records'
  } catch (e) {
    console.error('Save text record failed:', e)
    uni.showToast({ title: '保存失败', icon: 'none' })
  }
}

const deleteRecord = async (recordId: string) => {
  if (!currentPatient.value) return

  uni.showModal({
    title: '确认删除',
    content: '确定要删除这条记录吗？',
    success: async (res) => {
      if (res.confirm) {
        try {
          await calorieApi.deleteRecord(currentPatient.value.id, recordId)
          uni.showToast({ title: '删除成功', icon: 'success' })
          await loadRecords()
        } catch (e) {
          uni.showToast({ title: '删除失败', icon: 'none' })
        }
      }
    }
  })
}

const onMealTypeChange = (e: any) => {
  currentMealType.value = mealTypes[e.detail.value]
}

const onPatientChange = async (e: any) => {
  currentPatient.value = patients.value[e.detail.value]
  await loadRecords()
}

const getMealTypeName = (type: string) => {
  const meal = mealTypes.find(m => m.value === type)
  return meal?.label || type
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: var(--color-bg-page);
}

.meal-selector {
  padding: 20rpx 30rpx;
  background: #FFFFFF;
  border-bottom: 1rpx solid var(--color-border-light);
}

.meal-picker {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.meal-label {
  font-size: 26rpx;
  color: var(--color-text-secondary);
}

.meal-value {
  font-size: 28rpx;
  color: var(--color-primary);
  font-weight: 500;
}

.arrow {
  font-size: 20rpx;
  color: var(--color-text-secondary);
}

.patient-picker {
  display: flex;
  align-items: center;
  background: var(--color-bg-card);
  padding: 16rpx 24rpx;
  border-radius: 20rpx;
  font-size: 26rpx;
  color: var(--color-text-primary);
  border: 1rpx solid var(--color-border-light);
}

.tab-bar {
  display: flex;
  background: #FFFFFF;
  border-bottom: 1rpx solid var(--color-border-light);
  padding: 0 30rpx;
}

.tab-item {
  flex: 1;
  text-align: center;
  padding: 28rpx 0;
  font-size: 28rpx;
  color: var(--color-text-secondary);
  border-bottom: 4rpx solid transparent;
  transition: all 0.3s;
}

.tab-item.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
  font-weight: 500;
}

.tab-content {
  padding: 30rpx;
}

.upload-section {
  margin-bottom: 30rpx;
}

.upload-box {
  background: #FFFFFF;
  border-radius: 20rpx;
  overflow: hidden;
  margin-bottom: 30rpx;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 100rpx 0;
}

.upload-icon {
  font-size: 100rpx;
  margin-bottom: 20rpx;
}

.upload-text {
  font-size: 32rpx;
  color: var(--color-text-primary);
  margin-bottom: 10rpx;
}

.upload-hint {
  font-size: 24rpx;
  color: var(--color-text-secondary);
}

.image-preview {
  position: relative;
  padding: 20rpx;
}

.preview-img {
  width: 100%;
  max-height: 500rpx;
}

.remove-btn {
  position: absolute;
  top: 30rpx;
  right: 30rpx;
  width: 60rpx;
  height: 60rpx;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 28rpx;
}

.btn-analyze {
  width: 100%;
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border: none;
  border-radius: 20rpx;
  padding: 28rpx 0;
  font-size: 30rpx;
  font-weight: 500;
}

.btn-analyze[disabled] {
  background: var(--color-border);
}

.result-section {
  background: #FFFFFF;
  border-radius: 20rpx;
  padding: 30rpx;
  margin-top: 30rpx;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30rpx;
  padding-bottom: 20rpx;
  border-bottom: 1rpx solid var(--color-border-light);
}

.result-title {
  font-size: 32rpx;
  font-weight: bold;
  color: var(--color-text-primary);
}

.result-count {
  font-size: 24rpx;
  color: var(--color-primary);
}

.food-list {
  margin-bottom: 30rpx;
}

.food-item {
  padding: 24rpx 0;
  border-bottom: 1rpx solid var(--color-border-light);
}

.food-item:last-child {
  border-bottom: none;
}

.food-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16rpx;
}

.food-name {
  font-size: 30rpx;
  color: var(--color-text-primary);
  font-weight: 500;
}

.food-serving {
  font-size: 24rpx;
  color: var(--color-text-secondary);
}

.food-nutrition {
  display: flex;
  gap: 30rpx;
}

.nutrition-item {
  text-align: center;
}

.nutrition-value {
  display: block;
  font-size: 28rpx;
  color: var(--color-text-primary);
  font-weight: 500;
}

.nutrition-label {
  font-size: 20rpx;
  color: var(--color-text-secondary);
}

.nutrition-item.highlight .nutrition-value {
  color: var(--color-primary);
}

.total-section {
  background: var(--color-bg-card);
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 30rpx;
}

.total-header {
  font-size: 28rpx;
  color: var(--color-text-secondary);
  margin-bottom: 20rpx;
}

.total-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20rpx;
}

.total-item {
  text-align: center;
}

.total-value {
  display: block;
  font-size: 32rpx;
  color: var(--color-primary);
  font-weight: bold;
}

.total-label {
  font-size: 22rpx;
  color: var(--color-text-secondary);
}

.btn-save {
  width: 100%;
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border: none;
  border-radius: 20rpx;
  padding: 28rpx 0;
  font-size: 30rpx;
  font-weight: 500;
}

.text-section {
  background: #FFFFFF;
  border-radius: 20rpx;
  padding: 30rpx;
}

.text-input {
  width: 100%;
  height: 200rpx;
  font-size: 28rpx;
  line-height: 1.6;
  margin-bottom: 30rpx;
}

.records-header {
  margin-bottom: 20rpx;
}

.records-list {
  height: calc(100vh - 400rpx);
}

.empty-records {
  text-align: center;
  padding: 100rpx 0;
  color: var(--color-text-secondary);
  font-size: 28rpx;
}

.record-item {
  background: #FFFFFF;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
  border: 1rpx solid var(--color-border-light);
}

.record-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16rpx;
}

.record-meal {
  font-size: 28rpx;
  color: var(--color-primary);
  font-weight: 500;
}

.record-date {
  font-size: 24rpx;
  color: var(--color-text-secondary);
}

.record-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16rpx;
}

.record-food {
  font-size: 30rpx;
  color: var(--color-text-primary);
}

.record-calories {
  font-size: 32rpx;
  color: var(--color-primary);
  font-weight: bold;
}

.record-actions {
  display: flex;
  justify-content: flex-end;
}

.action-btn {
  font-size: 24rpx;
  color: var(--color-text-secondary);
  padding: 8rpx 16rpx;
}

.action-btn.danger {
  color: var(--color-danger);
}
</style>
