<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/utils/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

type TabKey = 'food' | 'carbs' | 'glucose' | 'tips'

const tabs = [
  { key: 'food' as TabKey, label: '食物查询' },
  { key: 'carbs' as TabKey, label: '碳水计算' },
  { key: 'glucose' as TabKey, label: '血糖分析' },
  { key: 'tips' as TabKey, label: '健康建议' },
]

const activeTab = ref<TabKey>('food')

const foodSearchKeyword = ref('')
const foodResults = ref<any[]>([])
const foodCategories = ref<any[]>([])
const lowGiFoods = ref<any[]>([])
const foodSearching = ref(false)
const foodSearched = ref(false)

const carbsMealItems = ref<any[]>([])
const carbsTotal = ref(0)
const carbsDailyReq = ref<any>(null)
const carbsInsulinRatio = ref<any>(null)
const carbsAddName = ref('')
const carbsAddAmount = ref('')
const carbsAddCarbs = ref('')
const carbsCalculating = ref(false)

const glucoseTrend = ref<any>(null)
const glucosePatterns = ref<any[]>([])
const glucoseLoading = ref(false)
const glucoseDays = ref(30)

const healthTips = ref<any[]>([])
const targetRanges = ref<any>(null)
const tipsLoading = ref(false)

const patientId = computed(() => auth.userInfo?.id || '')

function switchTab(key: TabKey) {
  activeTab.value = key
  if (key === 'food' && !foodCategories.value.length) {
    loadFoodCategories()
    loadLowGiFoods()
  } else if (key === 'glucose' && !glucoseTrend.value) {
    loadGlucoseData()
  } else if (key === 'tips' && !healthTips.value.length) {
    loadHealthTips()
  }
}

async function searchFood() {
  if (!foodSearchKeyword.value.trim()) {
    uni.showToast({ title: '请输入食物名称', icon: 'none' })
    return
  }
  foodSearching.value = true
  foodSearched.value = true
  try {
    const res = await api.get('/chronic/food/search', { keyword: foodSearchKeyword.value })
    foodResults.value = Array.isArray(res) ? res : (res as any)?.foods || (res as any)?.data || []
  } catch (e) {
    console.error(e)
    uni.showToast({ title: '搜索失败', icon: 'none' })
  } finally {
    foodSearching.value = false
  }
}

async function loadFoodCategories() {
  try {
    const res = await api.get('/chronic/food/categories')
    foodCategories.value = Array.isArray(res) ? res : (res as any)?.categories || (res as any)?.data || []
  } catch (e) {
    console.error(e)
  }
}

async function loadLowGiFoods() {
  try {
    const res = await api.get('/chronic/food/low-gi')
    lowGiFoods.value = Array.isArray(res) ? res : (res as any)?.foods || (res as any)?.data || []
  } catch (e) {
    console.error(e)
  }
}

function addCarbsItem() {
  if (!carbsAddName.value.trim()) {
    uni.showToast({ title: '请输入食物名称', icon: 'none' })
    return
  }
  carbsMealItems.value.push({
    name: carbsAddName.value,
    amount: carbsAddAmount.value || '1份',
    carbs: Number(carbsAddCarbs.value) || 0,
  })
  carbsTotal.value = carbsMealItems.value.reduce((s, item) => s + item.carbs, 0)
  carbsAddName.value = ''
  carbsAddAmount.value = ''
  carbsAddCarbs.value = ''
}

function removeCarbsItem(index: number) {
  carbsMealItems.value.splice(index, 1)
  carbsTotal.value = carbsMealItems.value.reduce((s, item) => s + item.carbs, 0)
}

async function calculateMeal() {
  if (!patientId.value) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    return
  }
  if (!carbsMealItems.value.length) {
    uni.showToast({ title: '请先添加食物', icon: 'none' })
    return
  }
  carbsCalculating.value = true
  try {
    const [mealRes, dailyRes, insulinRes] = await Promise.all([
      api.post('/chronic/carbs/meal', {
        patient_id: patientId.value,
        foods: carbsMealItems.value,
      }),
      api.post('/chronic/carbs/daily-requirement', { patient_id: patientId.value }),
      api.post('/chronic/carbs/insulin-ratio', { patient_id: patientId.value, total_carbs: carbsTotal.value }),
    ])
    carbsDailyReq.value = dailyRes
    carbsInsulinRatio.value = insulinRes
  } catch (e) {
    console.error(e)
    uni.showToast({ title: '计算失败', icon: 'none' })
  } finally {
    carbsCalculating.value = false
  }
}

async function loadGlucoseData() {
  if (!patientId.value) return
  glucoseLoading.value = true
  try {
    const [trendRes, patternsRes] = await Promise.all([
      api.post('/chronic/glucose/trend', { patient_id: patientId.value, days: glucoseDays.value }),
      api.post('/chronic/glucose/patterns', { patient_id: patientId.value }),
    ])
    glucoseTrend.value = trendRes
    glucosePatterns.value = Array.isArray(patternsRes) ? patternsRes : (patternsRes as any)?.patterns || []
  } catch (e) {
    console.error(e)
    uni.showToast({ title: '加载血糖数据失败', icon: 'none' })
  } finally {
    glucoseLoading.value = false
  }
}

async function loadHealthTips() {
  tipsLoading.value = true
  try {
    const [tipsRes, rangesRes] = await Promise.all([
      api.get('/chronic/health/tips'),
      api.get('/chronic/glucose/target-ranges'),
    ])
    healthTips.value = Array.isArray(tipsRes) ? tipsRes : (tipsRes as any)?.tips || (tipsRes as any)?.data || []
    targetRanges.value = rangesRes
  } catch (e) {
    console.error(e)
    uni.showToast({ title: '加载建议失败', icon: 'none' })
  } finally {
    tipsLoading.value = false
  }
}

onMounted(() => {
  loadFoodCategories()
  loadLowGiFoods()
})
</script>

<template>
  <view class="page">
    <view class="tab-bar">
      <view
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab-item', { active: activeTab === tab.key }]"
        @tap="switchTab(tab.key)"
      >
        {{ tab.label }}
      </view>
    </view>

    <view v-if="activeTab === 'food'" class="tab-content">
      <view class="card">
        <view class="search-row">
          <input
            v-model="foodSearchKeyword"
            class="input-field search-input"
            placeholder="搜索食物名称"
            confirm-type="search"
            @confirm="searchFood"
          />
          <view class="btn-primary search-btn" @tap="searchFood">搜索</view>
        </view>
      </view>

      <view v-if="foodSearching" class="flex-center mt-md">
        <text class="text-hint">搜索中...</text>
      </view>

      <view v-else-if="foodSearched && foodResults.length" class="card">
        <text class="section-title">搜索结果</text>
        <view v-for="food in foodResults" :key="food.id || food.name" class="food-item">
          <view class="food-info">
            <text class="food-name">{{ food.name }}</text>
            <view class="food-meta">
              <text v-if="food.gi !== undefined" class="food-gi">GI: {{ food.gi }}</text>
              <text v-if="food.gl !== undefined" class="food-gl">GL: {{ food.gl }}</text>
              <text v-if="food.calories" class="food-cal">{{ food.calories }} kcal</text>
            </view>
          </view>
          <view v-if="food.gi !== undefined" class="tag" :class="food.gi <= 55 ? 'tag-success' : food.gi <= 70 ? 'tag-warning' : 'tag-danger'">
            {{ food.gi <= 55 ? '低GI' : food.gi <= 70 ? '中GI' : '高GI' }}
          </view>
        </view>
      </view>

      <view v-if="!foodSearched && lowGiFoods.length" class="card">
        <text class="section-title">低GI食物推荐</text>
        <view v-for="food in lowGiFoods" :key="food.id || food.name" class="food-item">
          <view class="food-info">
            <text class="food-name">{{ food.name }}</text>
            <view class="food-meta">
              <text v-if="food.gi !== undefined" class="food-gi">GI: {{ food.gi }}</text>
              <text v-if="food.gl !== undefined" class="food-gl">GL: {{ food.gl }}</text>
            </view>
          </view>
          <view class="tag tag-success">低GI</view>
        </view>
      </view>

      <view v-if="foodCategories.length" class="card">
        <text class="section-title">食物分类</text>
        <view class="category-grid">
          <view v-for="cat in foodCategories" :key="cat.id || cat.name" class="category-item">
            <text class="category-name">{{ cat.name || cat.label }}</text>
            <text v-if="cat.count" class="category-count">{{ cat.count }}种</text>
          </view>
        </view>
      </view>
    </view>

    <view v-if="activeTab === 'carbs'" class="tab-content">
      <view class="card">
        <text class="section-title">添加食物</text>
        <view class="form-group">
          <text class="form-label">食物名称</text>
          <input v-model="carbsAddName" class="input-field" placeholder="如：米饭" />
        </view>
        <view class="form-row">
          <view class="form-group form-group-half">
            <text class="form-label">份量</text>
            <input v-model="carbsAddAmount" class="input-field" placeholder="如：1碗" />
          </view>
          <view class="form-group form-group-half">
            <text class="form-label">碳水(g)</text>
            <input v-model="carbsAddCarbs" class="input-field" type="digit" placeholder="0" />
          </view>
        </view>
        <view class="btn-primary add-item-btn" @tap="addCarbsItem">添加</view>
      </view>

      <view v-if="carbsMealItems.length" class="card">
        <view class="flex-between mb-sm">
          <text class="section-title" style="margin-bottom: 0;">已添加食物</text>
          <text class="carbs-total">总计: {{ carbsTotal }}g</text>
        </view>
        <view v-for="(item, idx) in carbsMealItems" :key="idx" class="carbs-item">
          <view class="carbs-item-info">
            <text class="carbs-item-name">{{ item.name }}</text>
            <text class="text-hint">{{ item.amount }} · {{ item.carbs }}g</text>
          </view>
          <view class="carbs-item-remove" @tap="removeCarbsItem(idx)">✕</view>
        </view>
        <view class="btn-primary calculate-btn" @tap="calculateMeal">
          {{ carbsCalculating ? '计算中...' : '计算碳水需求' }}
        </view>
      </view>

      <view v-if="carbsDailyReq" class="card">
        <text class="section-title">每日碳水需求</text>
        <view v-for="(val, key) in carbsDailyReq" :key="key" class="info-row flex-row">
          <text class="text-hint" style="width: 200rpx;">{{ key }}</text>
          <text class="text-primary">{{ val }}</text>
        </view>
      </view>

      <view v-if="carbsInsulinRatio" class="card">
        <text class="section-title">胰岛素比值</text>
        <view v-for="(val, key) in carbsInsulinRatio" :key="key" class="info-row flex-row">
          <text class="text-hint" style="width: 200rpx;">{{ key }}</text>
          <text class="text-primary">{{ val }}</text>
        </view>
      </view>
    </view>

    <view v-if="activeTab === 'glucose'" class="tab-content">
      <view v-if="glucoseLoading" class="flex-center mt-md">
        <text class="text-hint">加载中...</text>
      </view>

      <template v-else>
        <view v-if="glucoseTrend" class="card">
          <text class="section-title">血糖趋势</text>
          <view v-if="glucoseTrend.summary" class="trend-summary mb-sm">
            <text class="text-secondary">{{ glucoseTrend.summary }}</text>
          </view>
          <view v-if="glucoseTrend.direction" class="trend-direction flex-row gap-xs mb-sm">
            <text class="text-hint">趋势方向:</text>
            <text class="text-primary" :style="{ color: glucoseTrend.direction === 'up' || glucoseTrend.direction === 'rising' ? 'var(--color-danger)' : glucoseTrend.direction === 'down' || glucoseTrend.direction === 'falling' ? 'var(--color-success)' : 'var(--color-text-hint)' }">
              {{ glucoseTrend.direction === 'up' || glucoseTrend.direction === 'rising' ? '↑ 上升' : glucoseTrend.direction === 'down' || glucoseTrend.direction === 'falling' ? '↓ 下降' : '→ 平稳' }}
            </text>
          </view>
          <view v-if="glucoseTrend.data && glucoseTrend.data.length" class="trend-chart">
            <view v-for="(point, idx) in glucoseTrend.data" :key="idx" class="trend-point">
              <text class="trend-label">{{ point.date || point.time || '' }}</text>
              <view class="trend-bar-wrap">
                <view
                  class="trend-bar"
                  :style="{ width: Math.min((point.value / 20) * 100, 100) + '%', background: point.value > 11.1 ? 'var(--color-danger)' : point.value > 7.8 ? 'var(--color-warning)' : 'var(--color-success)' }"
                />
              </view>
              <text class="trend-val">{{ point.value }}</text>
            </view>
          </view>
          <view v-for="(val, key) in glucoseTrend" :key="key">
            <view v-if="key !== 'summary' && key !== 'direction' && key !== 'data' && typeof val !== 'object'" class="info-row flex-row">
              <text class="text-hint" style="width: 200rpx;">{{ key }}</text>
              <text class="text-primary">{{ val }}</text>
            </view>
          </view>
        </view>

        <view v-if="glucosePatterns.length" class="card">
          <text class="section-title">血糖模式</text>
          <view v-for="(pattern, idx) in glucosePatterns" :key="idx" class="pattern-item">
            <view class="flex-between">
              <text class="text-primary" style="font-weight: 600;">{{ pattern.name || pattern.type || `模式 ${idx + 1}` }}</text>
              <view v-if="pattern.severity" class="tag" :class="pattern.severity === 'high' || pattern.severity === 'danger' ? 'tag-danger' : pattern.severity === 'medium' || pattern.severity === 'warning' ? 'tag-warning' : 'tag-success'">
                {{ pattern.severity === 'high' || pattern.severity === 'danger' ? '需关注' : pattern.severity === 'medium' || pattern.severity === 'warning' ? '注意' : '正常' }}
              </view>
            </view>
            <text v-if="pattern.description" class="text-secondary mt-sm">{{ pattern.description }}</text>
            <text v-if="pattern.time_range || pattern.timeRange" class="text-hint mt-sm">
              时段: {{ pattern.time_range || pattern.timeRange }}
            </text>
          </view>
        </view>

        <view v-if="!glucoseTrend && !glucosePatterns.length" class="empty-state">
          <text class="empty-icon">📊</text>
          <text class="empty-text">暂无血糖分析数据</text>
        </view>
      </template>
    </view>

    <view v-if="activeTab === 'tips'" class="tab-content">
      <view v-if="tipsLoading" class="flex-center mt-md">
        <text class="text-hint">加载中...</text>
      </view>

      <template v-else>
        <view v-if="targetRanges" class="card">
          <text class="section-title">血糖目标范围</text>
          <view v-for="(val, key) in targetRanges" :key="key" class="info-row flex-row">
            <text class="text-hint" style="width: 200rpx;">{{ key }}</text>
            <text class="text-primary">{{ val }}</text>
          </view>
        </view>

        <view v-if="healthTips.length" class="card">
          <text class="section-title">健康建议</text>
          <view v-for="(tip, idx) in healthTips" :key="idx" class="tip-item">
            <view class="flex-row gap-xs">
              <text class="tag tag-primary" style="min-width: 40rpx; text-align: center;">{{ idx + 1 }}</text>
              <view class="tip-content">
                <text class="text-primary" style="font-weight: 600;">{{ tip.title || tip.name || `建议 ${idx + 1}` }}</text>
                <text v-if="tip.content || tip.description" class="text-secondary mt-sm">{{ tip.content || tip.description }}</text>
              </view>
            </view>
          </view>
        </view>

        <view v-if="!healthTips.length && !targetRanges" class="empty-state">
          <text class="empty-icon">💡</text>
          <text class="empty-text">暂无健康建议</text>
        </view>
      </template>
    </view>
  </view>
</template>

<style scoped>
.tab-bar {
  display: flex;
  background: var(--color-bg-card);
  border-radius: var(--radius-md);
  padding: 6rpx;
  margin-bottom: var(--spacing-md);
}

.tab-item {
  flex: 1;
  text-align: center;
  padding: 18rpx 0;
  font-size: 26rpx;
  color: var(--color-text-secondary);
  border-radius: var(--radius-sm);
  transition: all 0.2s;
}

.tab-item.active {
  background: var(--color-primary);
  color: #fff;
  font-weight: 600;
}

.search-row {
  display: flex;
  gap: var(--spacing-sm);
}

.search-input {
  flex: 1;
}

.search-btn {
  padding: 20rpx 32rpx;
  white-space: nowrap;
  font-size: 28rpx;
}

.food-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18rpx 0;
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
  font-weight: 500;
}

.food-meta {
  display: flex;
  gap: var(--spacing-sm);
  margin-top: 6rpx;
}

.food-gi,
.food-gl,
.food-cal {
  font-size: 22rpx;
  color: var(--color-text-hint);
}

.category-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.category-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16rpx 24rpx;
  background: var(--color-bg-page);
  border-radius: var(--radius-md);
  min-width: 120rpx;
}

.category-name {
  font-size: 26rpx;
  color: var(--color-text-primary);
}

.category-count {
  font-size: 22rpx;
  color: var(--color-text-hint);
  margin-top: 4rpx;
}

.form-row {
  display: flex;
  gap: var(--spacing-sm);
}

.form-group-half {
  flex: 1;
}

.form-group {
  margin-bottom: var(--spacing-sm);
}

.form-label {
  font-size: 26rpx;
  color: var(--color-text-secondary);
  margin-bottom: 8rpx;
  display: block;
}

.add-item-btn {
  padding: 20rpx 0;
  text-align: center;
  font-size: 28rpx;
  margin-top: var(--spacing-sm);
}

.carbs-total {
  font-size: 28rpx;
  font-weight: 600;
  color: var(--color-primary);
}

.carbs-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14rpx 0;
  border-bottom: 1rpx solid var(--color-border);
}

.carbs-item:last-of-type {
  border-bottom: none;
}

.carbs-item-info {
  display: flex;
  flex-direction: column;
}

.carbs-item-name {
  font-size: 28rpx;
  color: var(--color-text-primary);
}

.carbs-item-remove {
  font-size: 28rpx;
  color: var(--color-text-hint);
  padding: 10rpx 16rpx;
}

.calculate-btn {
  padding: 24rpx 0;
  text-align: center;
  font-size: 28rpx;
  margin-top: var(--spacing-sm);
}

.info-row {
  padding: 8rpx 0;
}

.trend-chart {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  margin-top: var(--spacing-sm);
}

.trend-point {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.trend-label {
  width: 120rpx;
  font-size: 22rpx;
  color: var(--color-text-hint);
  flex-shrink: 0;
}

.trend-bar-wrap {
  flex: 1;
  height: 20rpx;
  background: var(--color-bg-page);
  border-radius: 10rpx;
  overflow: hidden;
}

.trend-bar {
  height: 100%;
  border-radius: 10rpx;
  transition: width 0.3s;
}

.trend-val {
  width: 80rpx;
  font-size: 22rpx;
  color: var(--color-text-primary);
  text-align: right;
  flex-shrink: 0;
}

.pattern-item {
  padding: 16rpx 0;
  border-bottom: 1rpx solid var(--color-border);
}

.pattern-item:last-child {
  border-bottom: none;
}

.tip-item {
  padding: 12rpx 0;
  border-bottom: 1rpx solid var(--color-border);
}

.tip-item:last-child {
  border-bottom: none;
}

.tip-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}
</style>
