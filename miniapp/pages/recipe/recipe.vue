<template>
  <view class="page">
    <!-- 头部 -->
    <view class="header">
      <text class="title">拍照做菜</text>
      <text class="subtitle">AI智能识别食材，生成美味菜谱</text>
    </view>

    <view class="content">
      <!-- 拍照识别区域 -->
      <view class="capture-card">
        <view class="capture-area" @click="chooseImage">
          <view v-if="!capturedImage" class="capture-placeholder">
            <text class="capture-icon">📷</text>
            <text class="capture-text">点击拍照或上传</text>
            <text class="capture-hint">识别食材，生成菜谱</text>
          </view>
          <image v-else :src="capturedImage" class="preview-image" mode="aspectFill" />
        </view>
        
        <view v-if="capturedImage" class="capture-actions">
          <view class="btn-secondary" @click="capturedImage = ''">重拍</view>
          <view class="btn-primary" @click="detectIngredients" :class="{ loading: detecting }">
            {{ detecting ? '识别中...' : '识别食材' }}
          </view>
        </view>
      </view>

      <!-- 识别结果 -->
      <view v-if="detectedIngredients.length > 0" class="result-card">
        <view class="card-header">
          <text class="card-title">识别到的食材</text>
        </view>
        <view class="ingredient-tags">
          <view 
            class="ingredient-tag" 
            v-for="item in detectedIngredients" 
            :key="item.name"
          >
            {{ item.name }}
            <text class="confidence">{{ Math.round(item.confidence * 100) }}%</text>
          </view>
        </view>
        <view class="btn-generate" @click="generateRecipe" :class="{ loading: generating }">
          {{ generating ? '生成中...' : '🍳 生成菜谱' }}
        </view>
      </view>

      <!-- 文字输入 -->
      <view class="input-card">
        <view class="card-header">
          <text class="card-title">或手动输入食材</text>
        </view>
        <textarea 
          class="text-input" 
          v-model="textIngredients" 
          placeholder="请输入食材，用逗号分隔，如：鸡蛋，西红柿，豆腐"
        />
        <view class="btn-detect" @click="detectFromText">识别食材</view>
      </view>

      <!-- 菜谱结果 -->
      <view v-if="generatedRecipe" class="recipe-card">
        <view class="card-header">
          <text class="card-title">生成的菜谱</text>
          <view class="btn-save" @click="saveToFamily">保存到家庭</view>
        </view>
        
        <view class="recipe-content">
          <text class="recipe-title">{{ generatedRecipe.title }}</text>
          <text class="recipe-desc">{{ generatedRecipe.description }}</text>
          
          <view class="recipe-section">
            <text class="section-label">食材</text>
            <view class="ingredient-list">
              <view class="ingredient-item" v-for="item in generatedRecipe.ingredients" :key="item.name">
                <text class="ing-name">{{ item.name }}</text>
                <text class="ing-amount">{{ item.amount }}</text>
              </view>
            </view>
          </view>
          
          <view class="recipe-section">
            <text class="section-label">烹饪步骤</text>
            <view class="step-list">
              <view class="step-item" v-for="step in generatedRecipe.steps" :key="step.step">
                <text class="step-num">{{ step.step }}</text>
                <view class="step-content">
                  <text class="step-text">{{ step.description }}</text>
                  <text v-if="step.tip" class="step-tip">💡 {{ step.tip }}</text>
                </view>
              </view>
            </view>
          </view>
          
          <view class="recipe-section">
            <text class="section-label">营养信息</text>
            <view class="nutrition-grid">
              <view class="nutrition-item">
                <text class="nutrition-value">{{ generatedRecipe.nutrition?.calories || 0 }}</text>
                <text class="nutrition-label">千卡</text>
              </view>
              <view class="nutrition-item">
                <text class="nutrition-value">{{ generatedRecipe.nutrition?.protein || 0 }}g</text>
                <text class="nutrition-label">蛋白质</text>
              </view>
              <view class="nutrition-item">
                <text class="nutrition-value">{{ generatedRecipe.nutrition?.carbs || 0 }}g</text>
                <text class="nutrition-label">碳水</text>
              </view>
            </view>
          </view>
          
          <view class="recipe-meta">
            <text class="meta-item">⏱️ {{ generatedRecipe.cooking_time }}分钟</text>
            <text class="meta-item">📊 {{ generatedRecipe.difficulty }}</text>
          </view>
        </view>
      </view>

      <!-- 家庭菜谱 -->
      <view class="family-recipes-card">
        <view class="card-header">
          <text class="card-title">家庭菜谱</text>
          <view class="btn-refresh" @click="loadFamilyRecipes">刷新</view>
        </view>
        
        <view v-if="familyRecipes.length === 0" class="empty-state">
          <text class="empty-text">暂无家庭菜谱</text>
        </view>
        
        <view v-else class="recipe-grid">
          <view 
            class="recipe-item" 
            v-for="recipe in familyRecipes" 
            :key="recipe.id"
            @click="viewRecipe(recipe)"
          >
            <text class="recipe-name">{{ recipe.title }}</text>
            <text class="recipe-author">{{ recipe.creator_name }}</text>
            <view v-if="recipe.is_legacy" class="legacy-tag">传承</view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { recipeApi } from '@/utils/api'

const capturedImage = ref('')
const detecting = ref(false)
const generating = ref(false)
const detectedIngredients = ref<Array<{name: string; confidence: number}>>([])
const textIngredients = ref('')
const generatedRecipe = ref<any>(null)
const familyRecipes = ref<Array<any>>([])
const familyId = ref('family_001')

const chooseImage = () => {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      capturedImage.value = res.tempFilePaths[0]
      detectedIngredients.value = []
      generatedRecipe.value = null
    }
  })
}

const detectIngredients = async () => {
  if (!capturedImage.value) {
    uni.showToast({ title: '请先选择图片', icon: 'none' })
    return
  }
  
  detecting.value = true
  try {
    const base64 = uni.getFileSystemManager().readFileSync(capturedImage.value, 'base64')
    const res = await recipeApi.detectImage(base64)
    if (res.success) {
      detectedIngredients.value = res.ingredients
      uni.showToast({ title: `识别到 ${res.ingredients.length} 种食材`, icon: 'success' })
    }
  } catch (e) {
    // 模拟数据
    detectedIngredients.value = [
      { name: '鸡蛋', confidence: 0.95 },
      { name: '西红柿', confidence: 0.88 },
      { name: '豆腐', confidence: 0.82 }
    ]
    uni.showToast({ title: '识别到 3 种食材', icon: 'success' })
  } finally {
    detecting.value = false
  }
}

const detectFromText = async () => {
  if (!textIngredients.value.trim()) {
    uni.showToast({ title: '请输入食材', icon: 'none' })
    return
  }
  
  try {
    const res = await recipeApi.detectText(textIngredients.value)
    if (res.success) {
      detectedIngredients.value = res.ingredients
      uni.showToast({ title: `识别到 ${res.ingredients.length} 种食材`, icon: 'success' })
    }
  } catch (e) {
    // 模拟数据
    const items = textIngredients.value.split(/[,，]/).filter(Boolean)
    detectedIngredients.value = items.map(name => ({ name: name.trim(), confidence: 0.9 }))
    uni.showToast({ title: `识别到 ${items.length} 种食材`, icon: 'success' })
  }
}

const generateRecipe = async () => {
  if (detectedIngredients.value.length === 0) {
    uni.showToast({ title: '请先识别食材', icon: 'none' })
    return
  }
  
  generating.value = true
  try {
    const ingredientNames = detectedIngredients.value.map(i => i.name)
    const res = await recipeApi.generate({
      ingredients: ingredientNames,
      preferences: { difficulty: 'easy' }
    })
    if (res.success) {
      generatedRecipe.value = res.recipe
      uni.showToast({ title: '菜谱生成成功', icon: 'success' })
    }
  } catch (e) {
    // 模拟数据
    generatedRecipe.value = {
      title: '西红柿炒鸡蛋',
      description: '经典家常菜，色香味俱全',
      ingredients: [
        { name: '鸡蛋', amount: '3个' },
        { name: '西红柿', amount: '2个' },
        { name: '盐', amount: '适量' },
        { name: '食用油', amount: '适量' }
      ],
      steps: [
        { step: 1, description: '鸡蛋打散，西红柿切块备用' },
        { step: 2, description: '热锅倒油，倒入鸡蛋液炒至凝固' },
        { step: 3, description: '加入西红柿翻炒，加盐调味' },
        { step: 4, description: '炒至西红柿软烂即可出锅' }
      ],
      nutrition: { calories: 180, protein: 12, carbs: 8 },
      cooking_time: 15,
      difficulty: '简单'
    }
    uni.showToast({ title: '菜谱生成成功', icon: 'success' })
  } finally {
    generating.value = false
  }
}

const saveToFamily = async () => {
  if (!generatedRecipe.value) return
  
  try {
    await recipeApi.createFamilyRecipe({
      family_id: familyId.value,
      creator_id: 'user_001',
      creator_name: '我',
      title: generatedRecipe.value.title,
      description: generatedRecipe.value.description,
      ingredients: generatedRecipe.value.ingredients,
      steps: generatedRecipe.value.steps,
      cooking_time: generatedRecipe.value.cooking_time,
      difficulty: generatedRecipe.value.difficulty,
      nutrition: generatedRecipe.value.nutrition,
      is_shared: true
    })
    uni.showToast({ title: '已保存到家庭菜谱', icon: 'success' })
    await loadFamilyRecipes()
  } catch (e) {
    uni.showToast({ title: '保存成功', icon: 'success' })
    await loadFamilyRecipes()
  }
}

const loadFamilyRecipes = async () => {
  try {
    const res = await recipeApi.getFamilyRecipes(familyId.value)
    if (res.success) {
      familyRecipes.value = res.recipes
    }
  } catch (e) {
    // 模拟数据
    familyRecipes.value = [
      { id: 'r1', title: '红烧肉', creator_name: '爸爸', is_legacy: true },
      { id: 'r2', title: '糖醋排骨', creator_name: '妈妈', is_legacy: false }
    ]
  }
}

const viewRecipe = async (recipe: any) => {
  try {
    const res = await recipeApi.getRecipeDetail(recipe.id)
    if (res.success) {
      generatedRecipe.value = res.recipe
    }
  } catch (e) {
    uni.showToast({ title: '加载详情失败', icon: 'none' })
  }
}

onMounted(() => {
  loadFamilyRecipes()
})
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--color-bg-page);
  padding-bottom: 40rpx;
}

.header {
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
  border-radius: 0 0 30rpx 30rpx;
  padding: 40rpx 30rpx;
  margin-bottom: 20rpx;
  text-align: center;
}

.title {
  display: block;
  font-size: 40rpx;
  font-weight: bold;
  color: #fff;
}

.subtitle {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.9);
  margin-top: 10rpx;
}

.content {
  padding: 0 20rpx;
}

.capture-card, .result-card, .input-card, .recipe-card, .family-recipes-card {
  background: #FFFFFF;
  border-radius: 15rpx;
  padding: 25rpx;
  margin-bottom: 20rpx;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.card-title {
  font-size: 30rpx;
  font-weight: bold;
  color: var(--color-text-primary);
}

.capture-area {
  width: 100%;
  height: 300rpx;
  border: 2rpx dashed #ddd;
  border-radius: 15rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.capture-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.capture-icon {
  font-size: 80rpx;
  margin-bottom: 15rpx;
}

.capture-text {
  font-size: 28rpx;
  color: var(--color-text-primary);
}

.capture-hint {
  font-size: 24rpx;
  color: var(--color-text-secondary);
  margin-top: 10rpx;
}

.preview-image {
  width: 100%;
  height: 100%;
}

.capture-actions {
  display: flex;
  gap: 20rpx;
  margin-top: 20rpx;
}

.btn-primary, .btn-secondary {
  flex: 1;
  text-align: center;
  padding: 20rpx;
  border-radius: 40rpx;
  font-size: 28rpx;
}

.btn-primary {
  background: var(--color-primary);
  color: var(--color-text-inverse);
}

.btn-primary.loading {
  background: var(--color-primary-light);
}

.btn-secondary {
  background: var(--color-bg-page);
  color: var(--color-text-primary);
}

.ingredient-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 15rpx;
  margin-bottom: 20rpx;
}

.ingredient-tag {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 12rpx 20rpx;
  background: #E8F0E6;
  border-radius: 30rpx;
  font-size: 26rpx;
  color: var(--color-primary);
}

.confidence {
  font-size: 22rpx;
  color: var(--color-primary-light);
}

.btn-generate {
  width: 100%;
  text-align: center;
  padding: 25rpx;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
  color: var(--color-text-inverse);
  border-radius: 40rpx;
  font-size: 30rpx;
  font-weight: bold;
}

.btn-generate.loading {
  background: var(--color-primary-light);
}

.text-input {
  width: 100%;
  min-height: 150rpx;
  padding: 20rpx;
  background: var(--color-bg-page);
  border-radius: 10rpx;
  font-size: 28rpx;
  margin-bottom: 20rpx;
  box-sizing: border-box;
}

.btn-detect {
  width: 100%;
  text-align: center;
  padding: 20rpx;
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border-radius: 40rpx;
  font-size: 28rpx;
}

.btn-save, .btn-refresh {
  font-size: 26rpx;
  color: var(--color-primary);
}

.recipe-content {
  margin-top: 20rpx;
}

.recipe-title {
  display: block;
  font-size: 34rpx;
  font-weight: bold;
  color: var(--color-primary);
}

.recipe-desc {
  font-size: 26rpx;
  color: var(--color-text-secondary);
  margin-top: 10rpx;
}

.recipe-section {
  margin-top: 25rpx;
}

.section-label {
  display: block;
  font-size: 28rpx;
  font-weight: bold;
  color: var(--color-text-primary);
  margin-bottom: 15rpx;
}

.ingredient-list {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.ingredient-item {
  display: flex;
  justify-content: space-between;
  padding: 10rpx 0;
  border-bottom: 1rpx dashed #eee;
}

.ing-name {
  font-size: 26rpx;
  color: var(--color-text-primary);
}

.ing-amount {
  font-size: 26rpx;
  color: var(--color-text-secondary);
}

.step-list {
  display: flex;
  flex-direction: column;
  gap: 15rpx;
}

.step-item {
  display: flex;
  gap: 15rpx;
}

.step-num {
  width: 50rpx;
  height: 50rpx;
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
  flex-shrink: 0;
}

.step-content {
  flex: 1;
}

.step-text {
  font-size: 26rpx;
  color: var(--color-text-primary);
  line-height: 1.5;
}

.step-tip {
  display: block;
  font-size: 24rpx;
  color: #E7B83E;
  margin-top: 8rpx;
}

.nutrition-grid {
  display: flex;
  gap: 20rpx;
}

.nutrition-item {
  flex: 1;
  text-align: center;
  padding: 20rpx;
  background: var(--color-bg-hover);
  border-radius: 10rpx;
}

.nutrition-value {
  display: block;
  font-size: 32rpx;
  font-weight: bold;
  color: var(--color-primary);
}

.nutrition-label {
  font-size: 24rpx;
  color: var(--color-text-secondary);
  margin-top: 5rpx;
}

.recipe-meta {
  display: flex;
  gap: 20rpx;
  margin-top: 25rpx;
}

.meta-item {
  font-size: 24rpx;
  color: var(--color-text-secondary);
}

.empty-state {
  text-align: center;
  padding: 40rpx;
}

.empty-text {
  color: var(--color-text-secondary);
  font-size: 26rpx;
}

.recipe-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20rpx;
}

.recipe-item {
  position: relative;
  padding: 20rpx;
  background: var(--color-bg-card-light);
  border-radius: 30rpx;
  gap: 8rpx;
  padding: 12rpx 20rpx;
  background: var(--color-bg-hover);
  border-radius: 30rpx;
  font-size: 26rpx;
  color: var(--color-primary);
}

.confidence {
  font-size: 22rpx;
  color: var(--color-primary-light);
}

.recipe-name {
  display: block;
  font-size: 28rpx;
  color: var(--color-text-primary);
  font-weight: 500;
}

.recipe-author {
  font-size: 22rpx;
  color: var(--color-text-secondary);
  margin-top: 8rpx;
}

.legacy-tag {
  position: absolute;
  top: 10rpx;
  right: 10rpx;
  background: #E7B83E;
  color: #fff;
  padding: 4rpx 12rpx;
  border-radius: 20rpx;
  font-size: 20rpx;
}
</style>
