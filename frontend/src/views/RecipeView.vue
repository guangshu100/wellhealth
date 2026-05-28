<template>
  <div class="recipe-container">
    <el-card class="header-card">
      <h2>拍照做菜</h2>
      <p>拍照识别食材，AI智能生成美味菜谱</p>
    </el-card>

    <el-row :gutter="20">
      <!-- 左侧：拍照/识别 -->
      <el-col :span="14">
        <el-card>
          <template #header>
            <span>拍照识别食材</span>
          </template>
          
          <div class="capture-area">
            <div v-if="!capturedImage" class="upload-area" @click="triggerUpload">
              <el-icon :size="60" :style="{ color: 'var(--color-primary)' }"><Camera /></el-icon>
              <p>点击上传图片</p>
              <p class="tip">或拖拽图片到此处</p>
            </div>
            
            <div v-else class="preview-area">
              <img :src="capturedImage" class="preview-image" />
              <div class="preview-actions">
                <el-button @click="capturedImage = null">重新拍照</el-button>
                <el-button type="primary" @click="detectIngredients">识别食材</el-button>
              </div>
            </div>
            
            <input 
              ref="fileInput" 
              type="file" 
              accept="image/*" 
              style="display: none"
              @change="handleFileChange"
            />
          </div>

          <!-- 识别结果 -->
          <div v-if="detectedIngredients.length > 0" class="result-area">
            <el-divider>识别到的食材</el-divider>
            <div class="ingredient-tags">
              <el-tag 
                v-for="item in detectedIngredients" 
                :key="item.name"
                type="success"
                effect="plain"
              >
                {{ item.name }} ({{ Math.round(item.confidence * 100) }}%)
              </el-tag>
            </div>
            
            <el-button 
              type="primary" 
              class="generate-btn"
              :loading="generating"
              @click="generateRecipe"
            >
              生成菜谱
            </el-button>
          </div>

          <!-- 文字输入识别 -->
          <div class="text-input-area">
            <el-divider>或手动输入食材</el-divider>
            <el-input
              v-model="textIngredients"
              type="textarea"
              :rows="3"
              placeholder="请输入食材，用逗号分隔，如：鸡蛋，西红柿，豆腐"
            />
            <el-button type="success" @click="detectFromText" class="text-detect-btn">
              识别食材
            </el-button>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：菜谱结果 -->
      <el-col :span="10">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>生成的菜谱</span>
              <el-button v-if="generatedRecipe" size="small" @click="saveToFamily">
                保存到家庭菜谱
              </el-button>
            </div>
          </template>
          
          <div v-if="!generatedRecipe" class="empty-state">
            <el-empty description="上传食材图片，生成美味菜谱" />
          </div>
          
          <div v-else class="recipe-detail">
            <h3>{{ generatedRecipe.title }}</h3>
            <p class="description">{{ generatedRecipe.description }}</p>
            
            <el-divider>食材</el-divider>
            <ul class="ingredient-list">
              <li v-for="item in generatedRecipe.ingredients" :key="item.name">
                <span>{{ item.name }}</span>
                <span>{{ item.amount }}</span>
              </li>
            </ul>
            
            <el-divider>烹饪步骤</el-divider>
            <ol class="step-list">
              <li v-for="step in generatedRecipe.steps" :key="step.step">
                <p>{{ step.description }}</p>
                <p v-if="step.tip" class="step-tip">💡 {{ step.tip }}</p>
              </li>
            </ol>
            
            <el-divider>营养信息</el-divider>
            <div class="nutrition-info">
              <el-row :gutter="10">
                <el-col :span="8">
                  <div class="nutrition-item">
                    <span class="value">{{ generatedRecipe.nutrition?.calories || 0 }}</span>
                    <span class="label">千卡</span>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="nutrition-item">
                    <span class="value">{{ generatedRecipe.nutrition?.protein || 0 }}g</span>
                    <span class="label">蛋白质</span>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="nutrition-item">
                    <span class="value">{{ generatedRecipe.nutrition?.carbs || 0 }}g</span>
                    <span class="label">碳水</span>
                  </div>
                </el-col>
              </el-row>
            </div>
            
            <div v-if="generatedRecipe.tips?.length > 0" class="tips">
              <el-divider>小贴士</el-divider>
              <ul>
                <li v-for="tip in generatedRecipe.tips" :key="tip">{{ tip }}</li>
              </ul>
            </div>
            
            <div class="recipe-meta">
              <el-tag>⏱️ {{ generatedRecipe.cooking_time }}分钟</el-tag>
              <el-tag type="success">📊 {{ generatedRecipe.difficulty }}</el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 家庭菜谱 -->
    <el-card class="family-recipes-card">
      <template #header>
        <div class="card-header">
          <span>家庭菜谱</span>
          <el-button size="small" @click="loadFamilyRecipes">刷新</el-button>
        </div>
      </template>
      
      <div v-if="familyRecipes.length === 0" class="empty-state">
        <el-empty description="暂无家庭菜谱" />
      </div>
      
      <div v-else class="recipe-grid">
        <el-card 
          v-for="recipe in familyRecipes" 
          :key="recipe.id" 
          class="recipe-card"
          shadow="hover"
          @click="viewRecipeDetail(recipe)"
        >
          <h4>{{ recipe.title }}</h4>
          <p class="recipe-desc">{{ recipe.description || '暂无描述' }}</p>
          <div class="recipe-footer">
            <el-tag v-if="recipe.is_legacy" type="warning" size="small">传承菜谱</el-tag>
            <span class="creator">{{ recipe.creator_name }}</span>
          </div>
        </el-card>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Camera } from '@element-plus/icons-vue'
import api, { familyApi, recipeApi } from '@/api'

const fileInput = ref(null)
const capturedImage = ref(null)
const detectedIngredients = ref([])
const textIngredients = ref('')
const generating = ref(false)
const generatedRecipe = ref(null)
const familyRecipes = ref([])
const familyId = ref('')
const userInfo = ref<any>(null)

const triggerUpload = () => {
  fileInput.value?.click()
}

const handleFileChange = (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  const reader = new FileReader()
  reader.onload = (e) => {
    capturedImage.value = e.target.result
    detectedIngredients.value = []
    generatedRecipe.value = null
  }
  reader.readAsDataURL(file)
}

const detectIngredients = async () => {
  if (!capturedImage.value) {
    ElMessage.warning('请先上传图片')
    return
  }
  try {
    const base64 = capturedImage.value.split(',')[1]
    const res = await recipeApi.detectImage(base64)
    if (res.success) {
      detectedIngredients.value = res.ingredients
      ElMessage.success(`识别到 ${res.ingredients.length} 种食材`)
    } else {
      ElMessage.warning(res.message || '识别失败')
    }
  } catch {
    ElMessage.error('识别失败，请重试')
  }
}

const detectFromText = async () => {
  if (!textIngredients.value.trim()) {
    ElMessage.warning('请输入食材')
    return
  }
  try {
    const res = await recipeApi.detectText(textIngredients.value)
    if (res.success) {
      detectedIngredients.value = res.ingredients
      ElMessage.success(`识别到 ${res.ingredients.length} 种食材`)
    }
  } catch {}
}

const generateRecipe = async () => {
  if (detectedIngredients.value.length === 0) {
    ElMessage.warning('请先识别食材')
    return
  }
  generating.value = true
  try {
    const ingredientNames = detectedIngredients.value.map(i => i.name)
    const res = await recipeApi.generate({ ingredients: ingredientNames, preferences: { difficulty: 'easy' } })
    if (res.success) {
      generatedRecipe.value = res.recipe
      ElMessage.success('菜谱生成成功')
    } else {
      ElMessage.warning('生成失败')
    }
  } catch {
    ElMessage.error('生成失败，请重试')
  } finally {
    generating.value = false
  }
}

const saveToFamily = async () => {
  if (!generatedRecipe.value) return
  if (!familyId.value) {
    ElMessage.warning('未找到家庭信息，请先创建家庭')
    return
  }
  try {
    const res = await recipeApi.createFamilyRecipe({
      family_id: familyId.value,
      creator_id: userInfo.value?.id || '',
      creator_name: userInfo.value?.name || userInfo.value?.username || '未知用户',
      title: generatedRecipe.value.title,
      description: generatedRecipe.value.description,
      ingredients: generatedRecipe.value.ingredients,
      steps: generatedRecipe.value.steps,
      cooking_time: generatedRecipe.value.cooking_time,
      difficulty: generatedRecipe.value.difficulty,
      nutrition: generatedRecipe.value.nutrition,
      is_shared: true
    })
    if (res.success) {
      ElMessage.success('已保存到家庭菜谱')
      await loadFamilyRecipes()
    }
  } catch { ElMessage.error('保存失败') }
}

const loadFamilyRecipes = async () => {
  if (!familyId.value) return
  try {
    const res = await recipeApi.getFamilyRecipes(familyId.value)
    if (res.success) { familyRecipes.value = res.recipes || [] }
  } catch {}
}

const viewRecipeDetail = async (recipe) => {
  try {
    const res = await recipeApi.getRecipeDetail(recipe.id)
    if (res.success) { generatedRecipe.value = res.recipe }
  } catch {}
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const loadUserFamily = async () => {
  try {
    const stored = localStorage.getItem('userInfo')
    if (stored) {
      userInfo.value = JSON.parse(stored)
    }
    if (userInfo.value?.id) {
      const res = await familyApi.getUserFamilies(userInfo.value.id)
      if (res.success && res.families?.length > 0) {
        familyId.value = res.families[0].id
      }
    }
  } catch {}
}

loadUserFamily().then(() => { loadFamilyRecipes() })
</script>

<style scoped>
.recipe-container {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
  text-align: center;
}

.capture-area {
  min-height: 300px;
}

.upload-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 250px;
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.upload-area:hover {
  border-color: var(--color-primary);
  background: #FCF8F0;
}

.upload-area p {
  margin-top: 10px;
  color: #606266;
}

.upload-area .tip {
  font-size: 12px;
  color: #909399;
}

.preview-area {
  text-align: center;
}

.preview-image {
  max-width: 100%;
  max-height: 300px;
  border-radius: 8px;
}

.preview-actions {
  margin-top: 15px;
}

.result-area {
  margin-top: 20px;
}

.ingredient-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 15px 0;
}

.generate-btn {
  width: 100%;
  margin-top: 15px;
}

.text-input-area {
  margin-top: 20px;
}

.text-detect-btn {
  margin-top: 10px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.recipe-detail h3 {
  margin-top: 0;
  color: var(--color-primary);
}

.description {
  color: #606266;
  font-style: italic;
}

.ingredient-list, .step-list {
  padding-left: 20px;
}

.ingredient-list li {
  display: flex;
  justify-content: space-between;
  padding: 5px 0;
  border-bottom: 1px dashed #eee;
}

.step-list li {
  margin-bottom: 15px;
}

.step-tip {
  color: #E6A23C;
  font-size: 12px;
}

.nutrition-info {
  margin: 20px 0;
}

.nutrition-item {
  text-align: center;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 8px;
}

.nutrition-item .value {
  display: block;
  font-size: 20px;
  font-weight: bold;
  color: var(--color-primary);
}

.nutrition-item .label {
  font-size: 12px;
  color: #909399;
}

.tips ul {
  padding-left: 20px;
}

.tips li {
  color: #606266;
  margin-bottom: 5px;
}

.recipe-meta {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.family-recipes-card {
  margin-top: 20px;
}

.recipe-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 15px;
}

.recipe-card {
  cursor: pointer;
}

.recipe-card h4 {
  margin: 0 0 10px;
}

.recipe-desc {
  font-size: 12px;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recipe-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.creator {
  font-size: 12px;
  color: #909399;
}

.empty-state {
  text-align: center;
  padding: 40px;
}
</style>
