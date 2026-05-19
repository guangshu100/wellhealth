<template>
  <div class="game-container">
    <el-card class="game-header">
      <div class="header-content">
        <el-button text @click="router.back()">
          <el-icon><ArrowLeft /></el-icon>返回
        </el-button>
        <h2>📝 类别命名</h2>
        <div class="game-stats">
          <span>类别: {{ currentCategory }}</span>
          <span v-if="gameState === 'playing'">剩余: {{ timeLeft }}秒</span>
        </div>
      </div>
    </el-card>

    <div v-if="gameState === 'setup'" class="setup-section">
      <el-card>
        <h3>选择难度</h3>
        <el-radio-group v-model="difficulty" size="large">
          <el-radio-button label="beginner">初级 (60秒)</el-radio-button>
          <el-radio-button label="intermediate">中级 (45秒)</el-radio-button>
          <el-radio-button label="advanced">高级 (30秒)</el-radio-button>
        </el-radio-group>
        <div class="setup-info">
          <p>训练目标：在限定时间内，列举尽可能多的指定类别成员</p>
          <p>认知域：语义记忆、语言流畅性</p>
          <p>慢病定制：类别包含降糖食物、降压运动、常用药物等</p>
        </div>
        <el-button type="primary" size="large" @click="startGame">开始游戏</el-button>
      </el-card>
    </div>

    <div v-else-if="gameState === 'playing'" class="playing-section">
      <el-card class="category-card">
        <h3>请列举「{{ currentCategory }}」类别的成员</h3>
        <p class="hint">例如：{{ currentExample }}</p>
      </el-card>
      
      <el-input
        v-model="userInput"
        type="textarea"
        :rows="4"
        placeholder="请输入该类别的成员，用逗号或换行分隔"
        @keydown.enter.prevent="addWord"
      />
      
      <div class="words-section">
        <h4>已输入 ({{ words.length }}个)</h4>
        <div class="words-list">
          <el-tag v-for="(word, idx) in words" :key="idx" closable @close="removeWord(idx)">
            {{ word }}
          </el-tag>
        </div>
      </div>
    </div>

    <div v-else-if="gameState === 'completed'" class="result-section">
      <el-card>
        <div class="result-content">
          <h2>⏰ 时间到！</h2>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="类别">{{ currentCategory }}</el-descriptions-item>
            <el-descriptions-item label="列举数量">{{ words.length }}个</el-descriptions-item>
            <el-descriptions-item label="得分">{{ score }}</el-descriptions-item>
            <el-descriptions-item label="评价">{{ getEvaluation() }}</el-descriptions-item>
          </el-descriptions>
          <div class="your-words">
            <h4>你列举的内容：</h4>
            <div class="words-list">
              <el-tag v-for="word in words" :key="word" type="info">{{ word }}</el-tag>
            </div>
          </div>
          <div class="result-actions">
            <el-button type="primary" @click="startGame">再玩一次</el-button>
            <el-button @click="router.push('/cognitive/training')">返回训练列表</el-button>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { cognitiveApi } from '@/api/cognitive'

const router = useRouter()

const CATEGORIES = {
  beginner: [
    { name: '降糖食物', example: '苦瓜、燕麦、山药' },
    { name: '降压运动', example: '散步、游泳、太极拳' },
    { name: '常见药物', example: '阿司匹林、感冒灵、维生素C' }
  ],
  intermediate: [
    { name: '低GI食物', example: '糙米、全麦面包、苹果' },
    { name: '有氧运动', example: '跑步、骑车、跳绳' },
    { name: '心血管药物', example: '硝酸甘油、倍他乐克、阿托伐他汀' }
  ],
  advanced: [
    { name: '禁忌食物组合', example: '海鲜+维生素C、牛奶+巧克力' },
    { name: '运动禁忌人群', example: '严重心脏病患者、高血压危象患者' },
    { name: '药物相互作用', example: '阿司匹林+华法林、他汀类+葡萄柚' }
  ]
}

const TIME_LIMITS = { beginner: 60, intermediate: 45, advanced: 30 }

const difficulty = ref('intermediate')
const gameState = ref('setup')
const currentCategory = ref('')
const currentExample = ref('')
const userInput = ref('')
const words = ref([])
const timeLeft = ref(0)
const score = ref(0)
let timerInterval = null

const startGame = () => {
  const categories = CATEGORIES[difficulty.value]
  const selected = categories[Math.floor(Math.random() * categories.length)]
  currentCategory.value = selected.name
  currentExample.value = selected.example
  
  words.value = []
  userInput.value = ''
  timeLeft.value = TIME_LIMITS[difficulty.value]
  gameState.value = 'playing'
  
  if (timerInterval) clearInterval(timerInterval)
  timerInterval = setInterval(() => {
    timeLeft.value--
    if (timeLeft.value <= 0) {
      endGame()
    }
  }, 1000)
}

const addWord = () => {
  const input = userInput.value.trim()
  if (!input) return
  
  const newWords = input.split(/[,，、\n]/).map(w => w.trim()).filter(w => w && !words.value.includes(w))
  words.value.push(...newWords)
  userInput.value = ''
}

const removeWord = (index) => {
  words.value.splice(index, 1)
}

const endGame = async () => {
  if (timerInterval) clearInterval(timerInterval)
  
  const baseScore = words.value.length * 5
  const bonus = difficulty.value === 'advanced' ? 20 : difficulty.value === 'intermediate' ? 10 : 0
  score.value = Math.min(100, baseScore + bonus)
  
  gameState.value = 'completed'
  
  try {
    await cognitiveApi.submitTraining({
      exercise_type: 'category_naming',
      difficulty: difficulty.value,
      score: score.value,
      accuracy: words.value.length / 20,
      duration_seconds: TIME_LIMITS[difficulty.value],
      details: { category: currentCategory.value, words: words.value }
    })
  } catch (e) {
    console.error('提交训练结果失败', e)
  }
}

const getEvaluation = () => {
  if (score.value >= 80) return '优秀！词汇量丰富'
  if (score.value >= 60) return '良好，继续加油'
  if (score.value >= 40) return '一般，可以多练习'
  return '需要加强训练'
}

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval)
})
</script>

<style scoped>
.game-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.game-header {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-content h2 {
  margin: 0;
  color: var(--color-primary, #5E8B5A);
}

.game-stats {
  display: flex;
  gap: 20px;
  font-size: 14px;
  color: var(--color-text-secondary, #7F7D74);
}

.setup-section {
  text-align: center;
}

.setup-section h3 {
  margin-bottom: 20px;
}

.setup-info {
  margin: 20px 0;
  text-align: left;
  padding: 16px;
  background: var(--color-bg-hover, #E8F0E6);
  border-radius: 8px;
}

.setup-info p {
  margin: 8px 0;
  color: var(--color-text-secondary, #7F7D74);
}

.playing-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.category-card {
  text-align: center;
}

.category-card h3 {
  color: var(--color-primary, #5E8B5A);
  margin-bottom: 8px;
}

.hint {
  color: var(--color-text-secondary, #7F7D74);
  font-size: 14px;
}

.words-section {
  background: white;
  padding: 16px;
  border-radius: 8px;
}

.words-section h4 {
  margin-bottom: 12px;
  color: var(--color-text-primary, #2F2E2A);
}

.words-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.result-section {
  text-align: center;
}

.result-content h2 {
  color: var(--color-primary, #5E8B5A);
  margin-bottom: 20px;
}

.your-words {
  margin-top: 20px;
  text-align: left;
}

.your-words h4 {
  margin-bottom: 12px;
}

.result-actions {
  margin-top: 20px;
  display: flex;
  gap: 12px;
  justify-content: center;
}
</style>
