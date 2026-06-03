<template>
  <view class="page">
    <view class="card">
      <text class="section-title">📸 拍照做菜</text>
      <text class="text-secondary mb-md">拍照识别食材，智能生成健康食谱</text>

      <view class="camera-area flex-center" @tap="takePhoto">
        <view v-if="!imagePath" class="flex-col flex-center gap-sm">
          <text style="font-size:80rpx">📷</text>
          <text class="text-hint">点击拍照或选择图片</text>
        </view>
        <image v-else :src="imagePath" mode="aspectFit" class="preview-image" />
      </view>

      <view v-if="imagePath" class="flex-row gap-sm mt-md">
        <view class="btn-secondary" style="flex:1" @tap="takePhoto"><text>重新拍照</text></view>
        <view class="btn-primary" style="flex:1" @tap="detectImage"><text style="color:#fff">识别食材</text></view>
      </view>
    </view>

    <view v-if="detecting" class="flex-center mt-md">
      <text class="text-hint">识别中...</text>
    </view>

    <view v-if="ingredients.length > 0" class="card">
      <text class="section-title">🥬 识别结果</text>
      <view class="flex-row flex-wrap gap-sm mt-sm">
        <view v-for="item in ingredients" :key="item.name" class="ingredient-tag">
          <text>{{ item.name }}</text>
          <text v-if="item.confidence" class="text-hint" style="font-size:20rpx;margin-left:4rpx">{{ (item.confidence * 100).toFixed(0) }}%</text>
        </view>
      </view>
      <view class="btn-primary mt-md" @tap="generateRecipe">
        <text style="color:#fff;text-align:center">生成食谱</text>
      </view>
    </view>

    <view v-if="generating" class="flex-center mt-md">
      <text class="text-hint">生成食谱中...</text>
    </view>

    <view v-if="recipe" class="card">
      <view class="flex-row flex-between mb-sm">
        <text class="section-title">{{ recipe.title }}</text>
        <text class="tag tag-primary">{{ recipe.difficulty }}</text>
      </view>

      <text v-if="recipe.description" class="text-secondary mb-md">{{ recipe.description }}</text>

      <view v-if="recipe.cooking_time" class="info-row flex-row mb-sm">
        <text class="text-hint" style="width:140rpx">烹饪时间</text>
        <text class="text-primary">{{ recipe.cooking_time }} 分钟</text>
      </view>

      <view class="mb-md">
        <text class="text-primary mb-sm" style="font-weight:600">食材清单</text>
        <view v-for="(ing, idx) in recipe.ingredients" :key="idx" class="ingredient-item flex-row flex-between">
          <text class="text-secondary">{{ ing.name }}</text>
          <text class="text-primary">{{ ing.amount }}</text>
        </view>
      </view>

      <view class="mb-md">
        <text class="text-primary mb-sm" style="font-weight:600">烹饪步骤</text>
        <view v-for="(step, idx) in recipe.steps" :key="idx" class="step-item">
          <view class="flex-row gap-sm">
            <view class="step-num flex-center">
              <text style="color:#fff;font-size:22rpx;font-weight:600">{{ step.step || idx + 1 }}</text>
            </view>
            <view class="flex-col" style="flex:1">
              <text class="text-primary">{{ step.description }}</text>
              <text v-if="step.tip" class="text-hint mt-sm" style="font-size:22rpx">💡 {{ step.tip }}</text>
            </view>
          </view>
        </view>
      </view>

      <view v-if="recipe.nutrition" class="nutrition-section">
        <text class="text-primary mb-sm" style="font-weight:600">营养信息</text>
        <view class="flex-row gap-sm flex-wrap">
          <view v-if="recipe.nutrition.calories" class="nutrition-item flex-col flex-center">
            <text class="nutrition-value">{{ recipe.nutrition.calories }}</text>
            <text class="nutrition-label">千卡</text>
          </view>
          <view v-if="recipe.nutrition.protein" class="nutrition-item flex-col flex-center">
            <text class="nutrition-value">{{ recipe.nutrition.protein }}</text>
            <text class="nutrition-label">蛋白质g</text>
          </view>
          <view v-if="recipe.nutrition.carbs" class="nutrition-item flex-col flex-center">
            <text class="nutrition-value">{{ recipe.nutrition.carbs }}</text>
            <text class="nutrition-label">碳水g</text>
          </view>
          <view v-if="recipe.nutrition.fat" class="nutrition-item flex-col flex-center">
            <text class="nutrition-value">{{ recipe.nutrition.fat }}</text>
            <text class="nutrition-label">脂肪g</text>
          </view>
        </view>
      </view>

      <view v-if="recipe.tips && recipe.tips.length > 0" class="mt-md">
        <text class="text-primary mb-sm" style="font-weight:600">小贴士</text>
        <view v-for="(tip, idx) in recipe.tips" :key="idx" class="tip-item">
          <text class="text-secondary">• {{ tip }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import api from '@/utils/api'

const imagePath = ref('')
const imageBase64 = ref('')
const ingredients = ref<any[]>([])
const recipe = ref<any>(null)
const detecting = ref(false)
const generating = ref(false)

const takePhoto = () => {
  uni.chooseImage({
    count: 1,
    sourceType: ['album', 'camera'],
    success: (res) => {
      const tempPath = res.tempFilePaths[0]
      imagePath.value = tempPath
      ingredients.value = []
      recipe.value = null
      const fs = uni.getFileSystemManager()
      fs.readFile({
        filePath: tempPath,
        encoding: 'base64',
        success: (readRes: any) => {
          imageBase64.value = readRes.data
        },
      })
    },
  })
}

const detectImage = async () => {
  if (!imageBase64.value) {
    uni.showToast({ title: '请先拍照', icon: 'none' })
    return
  }
  detecting.value = true
  try {
    const res: any = await api.post('/recipe/detect-image', { image: imageBase64.value })
    ingredients.value = res.ingredients || []
    if (ingredients.value.length === 0) {
      uni.showToast({ title: '未识别到食材', icon: 'none' })
    }
  } catch (e) {
    uni.showToast({ title: '识别失败', icon: 'none' })
  } finally {
    detecting.value = false
  }
}

const generateRecipe = async () => {
  if (ingredients.value.length === 0) {
    uni.showToast({ title: '请先识别食材', icon: 'none' })
    return
  }
  generating.value = true
  try {
    const res: any = await api.post('/recipe/generate', {
      ingredients: ingredients.value.map(i => i.name),
    })
    recipe.value = res.recipe || null
  } catch (e) {
    uni.showToast({ title: '生成失败', icon: 'none' })
  } finally {
    generating.value = false
  }
}
</script>

<style scoped>
.camera-area {
  width: 100%;
  height: 400rpx;
  border: 4rpx dashed var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-page);
  overflow: hidden;
}

.preview-image {
  width: 100%;
  height: 100%;
}

.ingredient-tag {
  display: inline-flex;
  align-items: center;
  padding: 8rpx 20rpx;
  background: rgba(91, 140, 90, 0.1);
  border-radius: 20rpx;
  font-size: 24rpx;
  color: var(--color-primary);
}

.ingredient-item {
  padding: 12rpx 0;
  border-bottom: 2rpx solid var(--color-border);
}

.ingredient-item:last-child {
  border-bottom: none;
}

.step-item {
  padding: 16rpx 0;
  border-bottom: 2rpx solid var(--color-border);
}

.step-item:last-child {
  border-bottom: none;
}

.step-num {
  width: 44rpx;
  height: 44rpx;
  border-radius: 50%;
  background: var(--color-primary);
  flex-shrink: 0;
}

.nutrition-section {
  padding-top: var(--spacing-sm);
  border-top: 2rpx solid var(--color-border);
}

.nutrition-item {
  flex: 1;
  min-width: 120rpx;
  padding: var(--spacing-sm);
  background: var(--color-bg-page);
  border-radius: var(--radius-sm);
}

.nutrition-value {
  font-size: 32rpx;
  font-weight: 700;
  color: var(--color-primary);
}

.nutrition-label {
  font-size: 20rpx;
  color: var(--color-text-hint);
  margin-top: 4rpx;
}

.tip-item {
  padding: 6rpx 0;
}

.info-row {
  padding: 8rpx 0;
}
</style>
