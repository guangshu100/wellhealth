<template>
  <div class="chronic-disease-view">
    <div class="page-header">
      <h1>🌡️ 深度慢病管理</h1>
      <p>GI/GL食物库、碳水计算、血糖分析、食谱推荐</p>
    </div>

    <el-tabs v-model="activeTab" type="border-card">
      <!-- 食物查询 -->
      <el-tab-pane label="🍚 食物查询" name="food">
        <div class="search-section">
          <el-input
            v-model="foodSearchKeyword"
            placeholder="搜索食物名称，如：米饭、苹果..."
            @keyup.enter="searchFood"
            clearable
            size="large"
            style="max-width: 400px"
          >
            <template #append>
              <el-button :icon="Search" @click="searchFood">搜索</el-button>
            </template>
          </el-input>
          <el-select v-model="selectedCategory" placeholder="按分类筛选" @change="filterByCategory" style="margin-left: 10px;">
            <el-option label="全部分类" value="" />
            <el-option v-for="cat in foodCategories" :key="cat" :label="cat" :value="cat" />
          </el-select>
          <el-button @click="loadLowGiFoods">低GI食物</el-button>
        </div>

        <el-row :gutter="20" v-loading="foodLoading">
          <el-col :span="8" v-for="food in foodList" :key="food.name">
            <el-card class="food-card" shadow="hover">
              <template #header>
                <div class="food-header">
                  <span class="food-name">{{ food.name }}</span>
                  <el-tag size="small">{{ food.category }}</el-tag>
                </div>
              </template>
              <div class="food-info">
                <div class="food-gi" :class="getGiClass(food.gi)">
                  GI: {{ food.gi }}
                </div>
                <div class="food-detail">
                  <p>碳水: {{ food.carbs_per_100g }}g/100g</p>
                  <p>份量: {{ food.serving_size }}g</p>
                  <p>热量: {{ food.calories }} kcal</p>
                  <p class="gl-value">GL: {{ food.gl_per_serving }}</p>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <el-empty v-if="!foodLoading && foodList.length === 0" description="搜索食物看看" />
      </el-tab-pane>

      <!-- 碳水计算 -->
      <el-tab-pane label="🔢 碳水计算" name="carbs">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card>
              <template #header>🍽️ 餐食碳水计算</template>
              <div class="carbs-input">
                <div v-for="(item, index) in mealFoods" :key="index" class="food-input-row">
                  <el-input v-model="item.name" placeholder="食物名称" style="width: 200px" />
                  <el-input-number v-model="item.weight" :min="10" :max="1000" placeholder="重量(g)" />
                  <el-button type="danger" :icon="Delete" @click="removeFoodItem(index)" />
                </div>
                <el-button type="primary" @click="addFoodItem">+ 添加食物</el-button>
                <el-button type="success" @click="calculateMealCarbs">计算碳水</el-button>
              </div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card v-if="mealCarbsResult">
              <template #header>计算结果</template>
              <div class="result-summary">
                <el-statistic title="总碳水" :value="mealCarbsResult.total_carbs" suffix="g" />
                <el-statistic title="总热量" :value="mealCarbsResult.total_calories" suffix="kcal" />
                <el-statistic title="平均GI" :value="mealCarbsResult.gi" />
                <el-statistic title="GL" :value="mealCarbsResult.gl" />
              </div>
              <el-table :data="mealCarbsResult.foods" size="small" style="margin-top: 10px;">
                <el-table-column prop="name" label="食物" />
                <el-table-column prop="weight" label="重量(g)" />
                <el-table-column prop="carbs" label="碳水(g)" />
                <el-table-column prop="gi" label="GI" />
                <el-table-column prop="gl" label="GL" />
              </el-table>
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="20" style="margin-top: 20px;">
          <el-col :span="12">
            <el-card>
              <template #header>📊 每日需求计算</template>
              <el-form label-width="100px">
                <el-form-item label="体重(kg)">
                  <el-input-number v-model="dailyWeight" :min="30" :max="200" />
                </el-form-item>
                <el-form-item label="活动水平">
                  <el-select v-model="dailyActivity">
                    <el-option label="久坐" value="sedentary" />
                    <el-option label="轻度活动" value="light" />
                    <el-option label="中度活动" value="moderate" />
                    <el-option label="活跃" value="active" />
                    <el-option label="非常活跃" value="very_active" />
                  </el-select>
                </el-form-item>
                <el-button type="primary" @click="calculateDailyCarbs">计算</el-button>
              </el-form>
              <div v-if="dailyCarbsResult" class="result-summary" style="margin-top: 15px;">
                <p>每日热量需求: {{ dailyCarbsResult.estimated_calories }} kcal</p>
                <p>碳水需求范围: {{ dailyCarbsResult.carbs_grams_min }} - {{ dailyCarbsResult.carbs_grams_max }} g</p>
                <p>建议碳水摄入: {{ dailyCarbsResult.carbs_grams_typical }} g/天</p>
              </div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card>
              <template #header>💉 胰岛素计算</template>
              <el-form label-width="120px">
                <el-form-item label="日胰岛素总量(U)">
                  <el-input-number v-model="totalDailyInsulin" :min="1" :max="200" />
                </el-form-item>
                <el-form-item label="活动水平">
                  <el-select v-model="insulinActivity">
                    <el-option label="久坐" value="sedentary" />
                    <el-option label="轻度活动" value="light" />
                    <el-option label="中度活动" value="moderate" />
                    <el-option label="活跃" value="active" />
                    <el-option label="非常活跃" value="very_active" />
                  </el-select>
                </el-form-item>
                <el-button type="primary" @click="calculateInsulinRatio">计算ICR/ISF</el-button>
              </el-form>
              <div v-if="insulinResult" style="margin-top: 15px;">
                <el-alert :title="insulinResult.description" type="success" />
                <p v-if="isfResult" style="margin-top: 10px;">{{ isfResult.description }}</p>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- 血糖分析 -->
      <el-tab-pane label="📈 血糖分析" name="glucose">
        <el-card>
          <template #header>📝 录入血糖数据</template>
          <div class="glucose-input">
            <div v-for="(item, index) in glucoseData" :key="index" class="glucose-input-row">
              <el-date-picker
                v-model="item.time"
                type="datetime"
                placeholder="测量时间"
                format="YYYY-MM-DD HH:mm"
              />
              <el-input-number v-model="item.value" :min="1" :max="30" :step="0.1" placeholder="血糖值" />
              <el-select v-model="item.type" placeholder="测量类型">
                <el-option label="空腹" value="fasting" />
                <el-option label="餐后" value="postprandial" />
                <el-option label="随机" value="random" />
              </el-select>
              <el-button type="danger" :icon="Delete" @click="removeGlucoseData(index)" />
            </div>
            <el-button type="primary" @click="addGlucoseData">+ 添加记录</el-button>
            <el-button type="success" @click="analyzeGlucose">分析趋势</el-button>
          </div>
        </el-card>

        <el-row :gutter="20" v-if="glucoseTrendResult" style="margin-top: 20px;">
          <el-col :span="6">
            <el-statistic title="平均血糖" :value="glucoseTrendResult.average" suffix="mmol/L" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="最高血糖" :value="glucoseTrendResult.max" suffix="mmol/L" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="最低血糖" :value="glucoseTrendResult.min" suffix="mmol/L" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="TIR(时间范围占比)" :value="glucoseTrendResult.tir" suffix="%" />
          </el-col>
        </el-row>

        <el-row :gutter="20" v-if="glucoseTrendResult" style="margin-top: 20px;">
          <el-col :span="12">
            <el-card>
              <template #header>趋势分析</template>
              <el-descriptions :column="2" border>
                <el-descriptions-item label="趋势">{{ glucoseTrendResult.trend }}</el-descriptions-item>
                <el-descriptions-item label="波动性">{{ glucoseTrendResult.volatility }}</el-descriptions-item>
                <el-descriptions-item label="标准差">{{ glucoseTrendResult.std_dev }} mmol/L</el-descriptions-item>
              </el-descriptions>
              <el-divider />
              <el-alert
                v-for="(rec, idx) in glucoseTrendResult.recommendations"
                :key="idx"
                :title="rec"
                type="info"
                style="margin-bottom: 5px;"
              />
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card>
              <template #header>异常检测</template>
              <el-table :data="glucoseTrendResult.anomalies" v-if="glucoseTrendResult.anomalies.length">
                <el-table-column prop="time" label="时间" />
                <el-table-column prop="value" label="血糖值" />
                <el-table-column prop="type" label="类型">
                  <template #default="{ row }">
                    <el-tag :type="row.type === 'hypoglycemia' ? 'danger' : 'warning'" size="small">
                      {{ row.type === 'hypoglycemia' ? '低血糖' : '高血糖' }}
                    </el-tag>
                  </template>
                </el-table-column>
              </el-table>
              <el-empty v-else description="未检测到异常" />
            </el-card>
          </el-col>
        </el-row>

        <!-- 血糖控制目标 -->
        <el-card style="margin-top: 20px;">
          <template #header>🎯 血糖控制目标</template>
          <el-descriptions border>
            <el-descriptions-item label="空腹血糖">4.4 - 7.0 mmol/L</el-descriptions-item>
            <el-descriptions-item label="餐后血糖">4.4 - 10.0 mmol/L</el-descriptions-item>
            <el-descriptions-item label="睡前血糖">6.0 - 8.0 mmol/L</el-descriptions-item>
            <el-descriptions-item label="HbA1c糖化血红蛋白">< 7.0%</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-tab-pane>

      <!-- 食谱推荐 -->
      <el-tab-pane label="🍽️ 食谱推荐" name="recipe">
        <el-card>
          <template #header>患者信息</template>
          <el-form inline>
            <el-form-item label="体重(kg)">
              <el-input-number v-model="recipeWeight" :min="30" :max="200" />
            </el-form-item>
            <el-form-item label="活动水平">
              <el-select v-model="recipeActivity">
                <el-option label="久坐" value="sedentary" />
                <el-option label="轻度活动" value="light" />
                <el-option label="中度活动" value="moderate" />
                <el-option label="活跃" value="active" />
              </el-select>
            </el-form-item>
            <el-button type="primary" @click="generateDailyRecipe">生成每日食谱</el-button>
          </el-form>
        </el-card>

        <div v-if="dailyRecipeResult" style="margin-top: 20px;">
          <el-alert :title="`每日碳水目标: ${dailyRecipeResult.daily_carbs_target}g`" type="success" />
          
          <el-row :gutter="20" style="margin-top: 20px;">
            <el-col :span="6" v-for="(meal, key) in dailyRecipeResult.meals" :key="key">
              <el-card>
                <template #header>{{ getMealName(key) }}</template>
                <div v-for="food in meal.foods" :key="food.name" class="meal-food-item">
                  {{ food.name }} - {{ food.weight }}g ({{ food.carbs }}g碳水)
                </div>
                <el-divider />
                <p><strong>目标碳水:</strong> {{ meal.target_carbs }}g</p>
                <p><strong>实际碳水:</strong> {{ meal.actual_carbs }}g</p>
                <p><strong>GL值:</strong> {{ meal.gl }}</p>
                <el-alert :title="meal.recommendation" type="info" :closable="false" />
              </el-card>
            </el-col>
          </el-row>

          <el-card style="margin-top: 20px;">
            <template #header>💡 饮食建议</template>
            <ul>
              <li v-for="(tip, idx) in dailyRecipeResult.tips" :key="idx">{{ tip }}</li>
            </ul>
          </el-card>
        </div>
      </el-tab-pane>

      <!-- 健康知识 -->
      <el-tab-pane label="📚 健康知识" name="knowledge">
        <el-row :gutter="20">
          <el-col :span="12" v-for="section in healthTips" :key="section.category">
            <el-card>
              <template #header>{{ section.category }}</template>
              <ul>
                <li v-for="(tip, idx) in section.tips" :key="idx">{{ tip }}</li>
              </ul>
            </el-card>
          </el-col>
        </el-row>

        <el-card style="margin-top: 20px;">
          <template #header>📏 食物份量指南(手掌法则)</template>
          <el-table :data="portionGuide" size="small">
            <el-table-column prop="food_type" label="食物类型" />
            <el-table-column prop="portion" label="份量" />
            <el-table-column prop="examples" label="示例" />
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Search, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { chronicApi, type FoodItem, type MealCarbsResult, type DailyCarbsResult, type GlucoseTrendResult, type RecipeDailyResult } from '@/api'

const activeTab = ref('food')
const foodSearchKeyword = ref('')
const selectedCategory = ref('')
const foodCategories = ref<string[]>([])
const foodList = ref<FoodItem[]>([])
const foodLoading = ref(false)

// 碳水计算
const mealFoods = ref<Array<{ name: string; weight: number }>>([
  { name: '米饭', weight: 150 }
])
const mealCarbsResult = ref<MealCarbsResult | null>(null)
const dailyWeight = ref(70)
const dailyActivity = ref('moderate')
const dailyCarbsResult = ref<DailyCarbsResult | null>(null)

// 胰岛素计算
const totalDailyInsulin = ref(30)
const insulinActivity = ref('moderate')
const insulinResult = ref<{ description: string } | null>(null)
const isfResult = ref<{ description: string } | null>(null)

// 血糖分析
const glucoseData = ref<Array<{ time: string; value: number; type: string }>>([])
const glucoseTrendResult = ref<GlucoseTrendResult | null>(null)

// 食谱推荐
const recipeWeight = ref(70)
const recipeActivity = ref('moderate')
const dailyRecipeResult = ref<RecipeDailyResult | null>(null)

// 健康知识
const healthTips = ref<Array<{ category: string; tips: string[] }>>([])
const portionGuide = ref<Array<{ food_type: string; portion: string; examples: string }>>([])

onMounted(async () => {
  try {
    const cats = await chronicApi.getFoodCategories()
    foodCategories.value = cats.categories
    await loadLowGiFoods()
    
    const tips = await chronicApi.getHealthTips()
    healthTips.value = tips.tips
    
    const guide = await chronicApi.getPortionGuide()
    portionGuide.value = guide.guide
  } catch (e) {
    console.error(e)
  }
})

async function searchFood() {
  if (!foodSearchKeyword.value) return
  foodLoading.value = true
  try {
    const res = await chronicApi.searchFood(foodSearchKeyword.value)
    foodList.value = res.foods
  } catch (e) {
    ElMessage.error('搜索失败')
  } finally {
    foodLoading.value = false
  }
}

async function loadLowGiFoods() {
  foodLoading.value = true
  try {
    const res = await chronicApi.getLowGiFoods(12)
    foodList.value = res.foods
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    foodLoading.value = false
  }
}

async function filterByCategory() {
  if (!selectedCategory.value) {
    await loadLowGiFoods()
    return
  }
  foodLoading.value = true
  try {
    const res = await chronicApi.getFoodsByCategory(selectedCategory.value)
    foodList.value = res.foods
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    foodLoading.value = false
  }
}

function getGiClass(gi: number) {
  if (gi < 55) return 'gi-low'
  if (gi < 70) return 'gi-medium'
  return 'gi-high'
}

function addFoodItem() {
  mealFoods.value.push({ name: '', weight: 100 })
}

function removeFoodItem(index: number) {
  mealFoods.value.splice(index, 1)
}

async function calculateMealCarbs() {
  const validFoods = mealFoods.value.filter(f => f.name)
  if (validFoods.length === 0) {
    ElMessage.warning('请至少添加一种食物')
    return
  }
  try {
    const res = await chronicApi.calculateMealCarbs(validFoods)
    mealCarbsResult.value = res
    ElMessage.success('计算完成')
  } catch (e) {
    ElMessage.error('计算失败')
  }
}

async function calculateDailyCarbs() {
  try {
    const res = await chronicApi.calculateDailyCarbs(dailyWeight.value, dailyActivity.value)
    dailyCarbsResult.value = res
  } catch (e) {
    ElMessage.error('计算失败')
  }
}

async function calculateInsulinRatio() {
  try {
    const [icr, isf] = await Promise.all([
      chronicApi.calculateICR(totalDailyInsulin.value, insulinActivity.value),
      chronicApi.calculateISF(totalDailyInsulin.value)
    ])
    insulinResult.value = { description: icr.description }
    isfResult.value = { description: isf.description }
  } catch (e) {
    ElMessage.error('计算失败')
  }
}

function addGlucoseData() {
  glucoseData.value.push({ time: '', value: 6.5, type: 'fasting' })
}

function removeGlucoseData(index: number) {
  glucoseData.value.splice(index, 1)
}

async function analyzeGlucose() {
  const validData = glucoseData.value.filter(d => d.time && d.value > 0)
  if (validData.length < 2) {
    ElMessage.warning('请至少添加2条血糖记录')
    return
  }
  try {
    const res = await chronicApi.analyzeGlucoseTrend(validData.map(d => ({
      time: typeof d.time === 'string' ? d.time : new Date(d.time).toISOString(),
      value: d.value,
      type: d.type
    })))
    glucoseTrendResult.value = res
    ElMessage.success('分析完成')
  } catch (e) {
    ElMessage.error('分析失败')
  }
}

async function generateDailyRecipe() {
  try {
    const res = await chronicApi.generateDailyPlan({
      weight: recipeWeight.value,
      activity: recipeActivity.value
    })
    dailyRecipeResult.value = res
    ElMessage.success('生成成功')
  } catch (e) {
    ElMessage.error('生成失败')
  }
}

function getMealName(key: string) {
  const names: Record<string, string> = {
    breakfast: '🌅 早餐',
    lunch: '☀️ 午餐',
    dinner: '🌙 晚餐',
    snack: '🍪 零食'
  }
  return names[key] || key
}
</script>

<style scoped>
.chronic-disease-view {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
}

.page-header p {
  color: #666;
  margin: 5px 0 0;
}

.search-section {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}

.food-card {
  margin-bottom: 20px;
}

.food-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.food-name {
  font-weight: bold;
}

.food-gi {
  font-size: 24px;
  font-weight: bold;
  text-align: center;
  padding: 10px;
  border-radius: 8px;
  margin-bottom: 10px;
}

.gi-low { background: #e8f5e9; color: #2e7d32; }
.gi-medium { background: #fff3e0; color: #ef6c00; }
.gi-high { background: #ffebee; color: #c62828; }

.food-detail p {
  margin: 5px 0;
  font-size: 14px;
}

.gl-value {
  font-weight: bold;
  color: var(--color-primary);
}

.carbs-input, .glucose-input {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.food-input-row, .glucose-input-row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.result-summary {
  display: flex;
  justify-content: space-around;
  flex-wrap: wrap;
}

.meal-food-item {
  padding: 5px 0;
  border-bottom: 1px solid #eee;
}
</style>
