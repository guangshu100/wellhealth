<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import api from '@/utils/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snack'

interface FoodItem {
  id: string | number
  name: string
  calories: number
  carbs?: number
  protein?: number
  fat?: number
  amount?: string
}

interface MealSection {
  key: MealType
  label: string
  icon: string
  items: FoodItem[]
}

const meals = ref<MealSection[]>([
  { key: 'breakfast', label: '早餐', icon: '🌅', items: [] },
  { key: 'lunch', label: '午餐', icon: '☀️', items: [] },
  { key: 'dinner', label: '晚餐', icon: '🌙', items: [] },
  { key: 'snack', label: '加餐', icon: '🍪', items: [] },
])

const targetCalories = ref(2000)
const loading = ref(false)
const showSearchDialog = ref(false)
const activeMealKey = ref<MealType>('breakfast')
const searchKeyword = ref('')
const searchResults = ref<FoodItem[]>([])
const searching = ref(false)

const totalIntake = computed(() => {
  return meals.value.reduce((sum, meal) => {
    return sum + meal.items.reduce((s, item) => s + (item.calories || 0), 0)
  }, 0)
})

const remainingCalories = computed(() => targetCalories.value - totalIntake.value)

const progressPercent = computed(() => {
  if (!targetCalories.value) return 0
  const pct = Math.round((totalIntake.value / targetCalories.value) * 100)
  return Math.min(pct, 100)
})

const progressColor = computed(() => {
  if (progressPercent.value > 100) return 'var(--color-danger)'
  if (progressPercent.value > 80) return 'var(--color-warning)'
  return 'var(--color-primary)'
})

function getMealCalories(meal: MealSection) {
  return meal.items.reduce((s, item) => s + (item.calories || 0), 0)
}

function openSearch(mealKey: MealType) {
  activeMealKey.value = mealKey
  searchKeyword.value = ''
  searchResults.value = []
  showSearchDialog.value = true
}

function closeSearch() {
  showSearchDialog.value = false
}

async function searchFood() {
  if (!searchKeyword.value.trim()) {
    uni.showToast({ title: '请输入食物名称', icon: 'none' })
    return
  }
  searching.value = true
  try {
    const res = await api.get('/chronic/food/search', { keyword: searchKeyword.value })
    searchResults.value = Array.isArray(res) ? res : (res as any)?.foods || (res as any)?.data || []
  } catch (e) {
    console.error(e)
    uni.showToast({ title: '搜索失败', icon: 'none' })
  } finally {
    searching.value = false
  }
}

async function addFood(food: FoodItem) {
  const meal = meals.value.find(m => m.key === activeMealKey.value)
  if (!meal) return

  try {
    await api.post('/chronic/carbs/meal', {
      mealType: activeMealKey.value,
      foodId: food.id,
      foodName: food.name,
      calories: food.calories,
      carbs: food.carbs,
      protein: food.protein,
      fat: food.fat,
      amount: food.amount || '1份',
    })
    meal.items.push({ ...food })
    uni.showToast({ title: '已添加', icon: 'success' })
  } catch (e) {
    console.error(e)
    meal.items.push({ ...food })
    uni.showToast({ title: '添加失败，已本地暂存', icon: 'none' })
  }
}

function removeFood(mealKey: MealType, index: number) {
  const meal = meals.value.find(m => m.key === mealKey)
  if (meal) {
    meal.items.splice(index, 1)
  }
}

async function loadTodayData() {
  loading.value = true
  try {
    const res = await api.get('/chronic/carbs/meal', { date: new Date().toISOString().split('T')[0] })
    if (res && typeof res === 'object') {
      const data = res as any
      if (data.targetCalories) targetCalories.value = data.targetCalories
      if (data.meals) {
        for (const meal of meals.value) {
          const mealData = data.meals[meal.key]
          if (Array.isArray(mealData)) {
            meal.items = mealData
          }
        }
      }
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadTodayData()
})

onShow(() => {
  loadTodayData()
})
</script>

<template>
  <view class="page">
    <view class="card summary-card">
      <view class="summary-title">今日热量摄入</view>
      <view class="calorie-row">
        <text class="calorie-value" :style="{ color: progressColor }">{{ totalIntake }}</text>
        <text class="calorie-unit">/ {{ targetCalories }} kcal</text>
      </view>
      <view class="progress-bar-bg">
        <view class="progress-bar-fill" :style="{ width: progressPercent + '%', background: progressColor }" />
      </view>
      <view class="summary-footer">
        <text class="text-secondary" style="font-size: 24rpx;">
          剩余 {{ Math.max(remainingCalories, 0) }} kcal
        </text>
      </view>
    </view>

    <view v-for="meal in meals" :key="meal.key" class="meal-section">
      <view class="card meal-card">
        <view class="flex-between meal-header">
          <view class="flex-row gap-xs">
            <text class="meal-icon">{{ meal.icon }}</text>
            <text class="meal-label">{{ meal.label }}</text>
          </view>
          <view class="flex-row gap-sm">
            <text class="meal-cal text-secondary">{{ getMealCalories(meal) }} kcal</text>
            <view class="btn-text add-food-btn" @tap="openSearch(meal.key)">+ 添加</view>
          </view>
        </view>

        <view v-if="!meal.items.length" class="meal-empty text-hint">
          暂无记录
        </view>

        <view v-else class="food-list">
          <view v-for="(food, idx) in meal.items" :key="idx" class="food-item">
            <view class="food-info">
              <text class="food-name">{{ food.name }}</text>
              <text class="food-detail text-hint">{{ food.amount || '1份' }} · {{ food.calories }} kcal</text>
            </view>
            <view class="food-remove" @tap="removeFood(meal.key, idx)">✕</view>
          </view>
        </view>
      </view>
    </view>

    <view v-if="showSearchDialog" class="dialog-mask" @tap="closeSearch">
      <view class="dialog-content" @tap.stop>
        <view class="dialog-title">搜索食物</view>

        <view class="search-row">
          <input
            v-model="searchKeyword"
            class="input-field search-input"
            placeholder="输入食物名称"
            confirm-type="search"
            @confirm="searchFood"
          />
          <view class="btn-primary search-btn" @tap="searchFood">搜索</view>
        </view>

        <view v-if="searching" class="loading-state">
          <text class="text-hint">搜索中...</text>
        </view>

        <view v-else-if="!searchResults.length" class="search-empty text-hint">
          输入关键词搜索食物
        </view>

        <view v-else class="search-results">
          <view
            v-for="food in searchResults"
            :key="food.id"
            class="search-item"
            @tap="addFood(food)"
          >
            <view class="food-info">
              <text class="food-name">{{ food.name }}</text>
              <text class="food-detail text-hint">{{ food.calories }} kcal</text>
            </view>
            <text class="add-icon-text" style="color: var(--color-primary);">+</text>
          </view>
        </view>

        <view class="dialog-actions">
          <view class="btn-secondary dialog-btn" @tap="closeSearch">关闭</view>
        </view>
      </view>
    </view>
  </view>
</template>

<style scoped>
.summary-card {
  margin-bottom: var(--spacing-md);
}

.summary-title {
  font-size: 28rpx;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-xs);
}

.calorie-row {
  display: flex;
  align-items: baseline;
  margin-bottom: var(--spacing-sm);
}

.calorie-value {
  font-size: 64rpx;
  font-weight: 700;
  line-height: 1.1;
}

.calorie-unit {
  font-size: 26rpx;
  color: var(--color-text-hint);
  margin-left: 10rpx;
}

.progress-bar-bg {
  height: 16rpx;
  background: var(--color-border);
  border-radius: 8rpx;
  overflow: hidden;
  margin-bottom: var(--spacing-xs);
}

.progress-bar-fill {
  height: 100%;
  border-radius: 8rpx;
  transition: width 0.3s;
}

.summary-footer {
  display: flex;
  justify-content: flex-end;
}

.meal-section {
  margin-bottom: var(--spacing-sm);
}

.meal-card {
  padding: var(--spacing-sm) var(--spacing-md);
}

.meal-header {
  margin-bottom: var(--spacing-xs);
}

.meal-icon {
  font-size: 32rpx;
}

.meal-label {
  font-size: 30rpx;
  font-weight: 600;
  color: var(--color-text-primary);
}

.meal-cal {
  font-size: 24rpx;
}

.add-food-btn {
  font-size: 26rpx;
  padding: 4rpx 12rpx;
}

.meal-empty {
  font-size: 24rpx;
  padding: 16rpx 0;
  text-align: center;
}

.food-list {
  display: flex;
  flex-direction: column;
}

.food-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14rpx 0;
  border-bottom: 1rpx solid var(--color-border);
}

.food-item:last-child {
  border-bottom: none;
}

.food-info {
  display: flex;
  flex-direction: column;
}

.food-name {
  font-size: 28rpx;
  color: var(--color-text-primary);
}

.food-detail {
  font-size: 22rpx;
  margin-top: 4rpx;
}

.food-remove {
  font-size: 28rpx;
  color: var(--color-text-hint);
  padding: 10rpx 16rpx;
}

.dialog-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

.dialog-content {
  width: 640rpx;
  max-height: 80vh;
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
}

.dialog-title {
  font-size: 34rpx;
  font-weight: 600;
  color: var(--color-text-primary);
  text-align: center;
  margin-bottom: var(--spacing-md);
}

.search-row {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.search-input {
  flex: 1;
}

.search-btn {
  padding: 20rpx 32rpx;
  white-space: nowrap;
  font-size: 28rpx;
}

.loading-state {
  display: flex;
  justify-content: center;
  padding: 60rpx 0;
}

.search-empty {
  text-align: center;
  padding: 60rpx 0;
  font-size: 26rpx;
}

.search-results {
  max-height: 480rpx;
  overflow-y: auto;
}

.search-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx 0;
  border-bottom: 1rpx solid var(--color-border);
}

.search-item:last-child {
  border-bottom: none;
}

.add-icon-text {
  font-size: 36rpx;
  font-weight: 700;
  padding: 0 16rpx;
}

.dialog-actions {
  margin-top: var(--spacing-md);
}

.dialog-btn {
  padding: 22rpx 0;
  text-align: center;
}
</style>
