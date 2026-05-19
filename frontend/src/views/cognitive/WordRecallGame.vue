<template>
  <div class="game-container">
    <el-card class="game-header">
      <div class="header-content">
        <el-button text @click="router.back()">
          <el-icon><ArrowLeft /></el-icon>返回
        </el-button>
        <h2>💬 词语回忆</h2>
        <div class="game-stats">
          <span v-if="gameState === 'memorize'">记忆时间: {{ timeLeft }}秒</span>
          <span v-else-if="gameState === 'recall'">回忆时间: {{ timeLeft }}秒</span>
          <span v-else-if="gameState === 'playing'">目标词: {{ targetWords.length }}个</span>
        </div>
      </div>
    </el-card>

    <div v-if="gameState === 'setup'" class="setup-section">
      <el-card>
        <h3>选择难度</h3>
        <el-radio-group v-model="difficulty" size="large">
          <el-radio-button label="beginner">初级 (5词)</el-radio-button>
          <el-radio-button label="intermediate">中级 (8词)</el-radio-button>
          <el-radio-button label="advanced">高级 (12词)</el-radio-button>
        </el-radio-group>
        <div class="setup-info">
          <p>训练目标：记忆一组词语，然后在回忆阶段尽可能多地写出记住的词</p>
          <p>认知域：短期记忆、工作记忆</p>
        </div>
        <el-button type="primary" size="large" @click="startGame">开始游戏</el-button>
      </el-card>
    </div>

    <div v-else-if="gameState === 'memorize'" class="memorize-section">
      <el-card>
        <h3>请记住以下词语</h3>
        <div class="words-grid">
          <el-tag v-for="word in targetWords" :key="word" size="large" type="primary" effect="dark">
            {{ word }}
          </el-tag>
        </div>
        <el-progress :percentage="memorizeProgress" :show-text="false" class="progress-bar" />
      </el-card>
    </div>

    <div v-else-if="gameState === 'recall'" class="recall-section">
      <el-card>
        <h3>请输入你记住的词语</h3>
        <el-input
          v-model="userInput"
          type="textarea"
          :rows="4"
          placeholder="请输入你记住的词语，用逗号或换行分隔"
        />
        <div class="recall-actions">
          <el-button type="primary" @click="submitRecall">提交答案</el-button>
        </div>
        <el-progress :percentage="recallProgress" :show-text="false" class="progress-bar" />
      </el-card>
    </div>

    <div v-else-if="gameState === 'completed'" class="result-section">
      <el-card>
        <div class="result-content">
          <h2>🎯 回忆完成！</h2>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="目标词数">{{ targetWords.length }}</el-descriptions-item>
            <el-descriptions-item label="回忆词数">{{ recalledWords.length }}</el-descriptions-item>
            <el-descriptions-item label="正确数">{{ correctCount }}</el-descriptions-item>
            <el-descriptions-item label="得分">{{ score }}</el-descriptions-item>
          </el-descriptions>
          
          <div class="words-analysis">
            <div class="analysis-section">
              <h4 class="success">✅ 正确回忆 ({{ correctCount }})</h4>
              <div class="words-list">
                <el-tag v-for="word in correctWords" :key="word" type="success">{{ word }}</el-tag>
              </div>
            </div>
            
            <div class="analysis-section" v-if="missedWords.length > 0">
              <h4 class="warning">❌ 遗漏的词 ({{ missedWords.length }})</h4>
              <div class="words-list">
                <el-tag v-for="word in missedWords" :key="word" type="warning">{{ word }}</el-tag>
              </div>
            </div>
            
            <div class="analysis-section" v-if="extraWords.length > 0">
              <h4 class="info">➕ 额外的词 ({{ extraWords.length }})</h4>
              <div class="words-list">
                <el-tag v-for="word in extraWords" :key="word" type="info">{{ word }}</el-tag>
              </div>
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
import { ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { cognitiveApi } from '@/api/cognitive'

const router = useRouter()

const WORD_POOLS = {
  beginner: ['苹果', '阳光', '书本', '河流', '音乐', '花园', '星星', '咖啡', '风筝', '海洋'],
  intermediate: ['苹果', '阳光', '书本', '河流', '音乐', '花园', '星星', '咖啡', '风筝', '海洋', '森林', '月亮', '彩虹', '蝴蝶', '雪山'],
  advanced: ['苹果', '阳光', '书本', '河流', '音乐', '花园', '星星', '咖啡', '风筝', '海洋', '森林', '月亮', '彩虹', '蝴蝶', '雪山', '沙漠', '瀑布', '珊瑚', '琥珀', '银河']
}

const WORD_COUNTS = { beginner: 5, intermediate: 8, advanced: 12 }
const MEMORIZE_TIME = { beginner: 20, intermediate: 30, advanced: 40 }
const RECALL_TIME = { beginner: 30, intermediate: 45, advanced: 60 }

const difficulty = ref('intermediate')
const gameState = ref('setup')
const targetWords = ref([])
const userInput = ref('')
const recalledWords = ref([])
const timeLeft = ref(0)
const score = ref(0)
let timerInterval = null

const memorizeProgress = computed(() => {
  const total = MEMORIZE_TIME[difficulty.value]
  return ((total - timeLeft.value) / total) * 100
})

const recallProgress = computed(() => {
  const total = RECALL_TIME[difficulty.value]
  return ((total - timeLeft.value) / total) * 100
})

const correctWords = computed(() => {
  return recalledWords.value.filter(w => targetWords.value.includes(w))
})

const missedWords = computed(() => {
  return targetWords.value.filter(w => !recalledWords.value.includes(w))
})

const extraWords = computed(() => {
  return recalledWords.value.filter(w => !targetWords.value.includes(w))
})

const correctCount = computed(() => correctWords.value.length)

const shuffleArray = (arr) => {
  const newArr = [...arr]
  for (let i = newArr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [newArr[i], newArr[j]] = [newArr[j], newArr[i]]
  }
  return newArr
}

const startGame = () => {
  const wordPool = WORD_POOLS[difficulty.value]
  const count = WORD_COUNTS[difficulty.value]
  targetWords.value = shuffleArray(wordPool).slice(0, count)
  
  userInput.value = ''
  recalledWords.value = []
  timeLeft.value = MEMORIZE_TIME[difficulty.value]
  gameState.value = 'memorize'
  
  if (timerInterval) clearInterval(timerInterval)
  timerInterval = setInterval(() => {
    timeLeft.value--
    if (timeLeft.value <= 0) {
      if (gameState.value === 'memorize') {
        startRecall()
      } else if (gameState.value === 'recall') {
        submitRecall()
      }
    }
  }, 1000)
}

const startRecall = () => {
  timeLeft.value = RECALL_TIME[difficulty.value]
  gameState.value = 'recall'
}

const submitRecall = async () => {
  if (timerInterval) clearInterval(timerInterval)
  
  const input = userInput.value.trim()
  const words = input.split(/[,，、\s\n]+/).map(w => w.trim()).filter(w => w)
  recalledWords.value = [...new Set(words)]
  
  const accuracy = correctCount.value / targetWords.value.length
  score.value = Math.round(accuracy * 100)
  
  gameState.value = 'completed'
  
  try {
    await cognitiveApi.submitTraining({
      exercise_type: 'word_recall',
      difficulty: difficulty.value,
      score: score.value,
      accuracy: accuracy,
      details: { 
        target_words: targetWords.value,
        recalled_words: recalledWords.value,
        correct_count: correctCount.value
      }
    })
  } catch (e) {
    console.error('提交训练结果失败', e)
  }
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

.memorize-section h3,
.recall-section h3 {
  text-align: center;
  color: var(--color-primary, #5E8B5A);
  margin-bottom: 20px;
}

.words-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
  margin-bottom: 20px;
}

.words-grid .el-tag {
  font-size: 18px;
  padding: 12px 20px;
}

.progress-bar {
  margin-top: 20px;
}

.recall-section .el-textarea {
  margin-bottom: 16px;
}

.recall-actions {
  display: flex;
  justify-content: center;
}

.result-section {
  text-align: center;
}

.result-content h2 {
  color: var(--color-primary, #5E8B5A);
  margin-bottom: 20px;
}

.words-analysis {
  margin-top: 20px;
  text-align: left;
}

.analysis-section {
  margin-bottom: 16px;
  padding: 12px;
  background: var(--color-bg-hover, #E8F0E6);
  border-radius: 8px;
}

.analysis-section h4 {
  margin-bottom: 12px;
}

.analysis-section h4.success {
  color: #67C23A;
}

.analysis-section h4.warning {
  color: #E6A23C;
}

.analysis-section h4.info {
  color: #909399;
}

.words-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.result-actions {
  margin-top: 20px;
  display: flex;
  gap: 12px;
  justify-content: center;
}
</style>
