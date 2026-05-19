<template>
  <div class="game-container">
    <el-card class="game-header">
      <div class="header-content">
        <el-button text @click="router.back()">
          <el-icon><ArrowLeft /></el-icon>返回
        </el-button>
        <h2>🃏 记忆匹配</h2>
        <div class="game-stats">
          <span>步数: {{ moves }}</span>
          <span>配对: {{ matchedPairs }}/{{ totalPairs }}</span>
          <span v-if="gameState === 'playing'">时间: {{ formatTime(timer) }}</span>
        </div>
      </div>
    </el-card>

    <div v-if="gameState === 'setup'" class="setup-section">
      <el-card>
        <h3>选择难度</h3>
        <el-radio-group v-model="difficulty" size="large">
          <el-radio-button label="beginner">初级 (2×2)</el-radio-button>
          <el-radio-button label="intermediate">中级 (4×4)</el-radio-button>
          <el-radio-button label="advanced">高级 (6×6)</el-radio-button>
        </el-radio-group>
        <div class="setup-info">
          <p>训练目标：找出所有配对的卡片</p>
          <p>认知域：工作记忆、视觉空间注意力</p>
        </div>
        <el-button type="primary" size="large" @click="startGame">开始游戏</el-button>
      </el-card>
    </div>

    <div v-else-if="gameState === 'playing'" class="game-board" :style="gridStyle">
      <div
        v-for="(card, index) in cards"
        :key="index"
        class="card"
        :class="{ flipped: card.flipped, matched: card.matched }"
        @click="flipCard(index)"
      >
        <div class="card-inner">
          <div class="card-front">?</div>
          <div class="card-back">{{ card.emoji }}</div>
        </div>
      </div>
    </div>

    <div v-else-if="gameState === 'completed'" class="result-section">
      <el-card>
        <div class="result-content">
          <h2>🎉 游戏完成！</h2>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="得分">{{ score }}</el-descriptions-item>
            <el-descriptions-item label="准确率">{{ accuracy }}%</el-descriptions-item>
            <el-descriptions-item label="用时">{{ formatTime(timer) }}</el-descriptions-item>
            <el-descriptions-item label="步数">{{ moves }}</el-descriptions-item>
          </el-descriptions>
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

const EMOJIS = ['🍎', '🍊', '🍋', '🍇', '🍓', '🍑', '🥝', '🍒', '🥭', '🍍', '🥥', '🍌', '🍉', '🫐', '🍈', '🍐', '🫒', '🥑']

const difficulty = ref('intermediate')
const gameState = ref('setup')
const cards = ref([])
const flippedIndices = ref([])
const moves = ref(0)
const matchedPairs = ref(0)
const totalPairs = ref(0)
const timer = ref(0)
const score = ref(0)
const accuracy = ref(0)
let timerInterval = null

const gridStyle = computed(() => {
  const sizes = { beginner: '2', intermediate: '4', advanced: '6' }
  const size = sizes[difficulty.value] || '4'
  return {
    gridTemplateColumns: `repeat(${size}, 1fr)`,
    maxWidth: `${parseInt(size) * 100}px`
  }
})

const shuffleArray = (arr) => {
  const newArr = [...arr]
  for (let i = newArr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [newArr[i], newArr[j]] = [newArr[j], newArr[i]]
  }
  return newArr
}

const startGame = () => {
  const pairCounts = { beginner: 2, intermediate: 8, advanced: 18 }
  const pairCount = pairCounts[difficulty.value]
  totalPairs.value = pairCount
  
  const selectedEmojis = shuffleArray(EMOJIS).slice(0, pairCount)
  const cardPairs = [...selectedEmojis, ...selectedEmojis]
  cards.value = shuffleArray(cardPairs).map(emoji => ({
    emoji,
    flipped: false,
    matched: false
  }))
  
  flippedIndices.value = []
  moves.value = 0
  matchedPairs.value = 0
  timer.value = 0
  gameState.value = 'playing'
  
  if (timerInterval) clearInterval(timerInterval)
  timerInterval = setInterval(() => {
    timer.value++
  }, 1000)
}

const flipCard = (index) => {
  if (cards.value[index].flipped || cards.value[index].matched) return
  if (flippedIndices.value.length >= 2) return
  
  cards.value[index].flipped = true
  flippedIndices.value.push(index)
  
  if (flippedIndices.value.length === 2) {
    moves.value++
    const [first, second] = flippedIndices.value
    
    if (cards.value[first].emoji === cards.value[second].emoji) {
      cards.value[first].matched = true
      cards.value[second].matched = true
      matchedPairs.value++
      flippedIndices.value = []
      
      if (matchedPairs.value === totalPairs.value) {
        endGame()
      }
    } else {
      setTimeout(() => {
        cards.value[first].flipped = false
        cards.value[second].flipped = false
        flippedIndices.value = []
      }, 800)
    }
  }
}

const endGame = async () => {
  if (timerInterval) clearInterval(timerInterval)
  
  const idealMoves = totalPairs.value * 2
  const efficiency = Math.max(0, Math.min(100, Math.round((idealMoves / moves.value) * 100)))
  score.value = efficiency
  accuracy.value = Math.round((totalPairs.value / moves.value) * 100)
  
  gameState.value = 'completed'
  
  try {
    await cognitiveApi.submitTraining({
      exercise_type: 'memory_match',
      difficulty: difficulty.value,
      score: score.value,
      accuracy: accuracy.value / 100,
      duration_seconds: timer.value
    })
  } catch (e) {
    console.error('提交训练结果失败', e)
  }
}

const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
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

.game-board {
  display: grid;
  gap: 10px;
  margin: 0 auto;
  justify-content: center;
}

.card {
  width: 80px;
  height: 80px;
  perspective: 1000px;
  cursor: pointer;
}

.card-inner {
  width: 100%;
  height: 100%;
  position: relative;
  transform-style: preserve-3d;
  transition: transform 0.4s;
}

.card.flipped .card-inner,
.card.matched .card-inner {
  transform: rotateY(180deg);
}

.card-front, .card-back {
  position: absolute;
  width: 100%;
  height: 100%;
  backface-visibility: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-size: 32px;
}

.card-front {
  background: linear-gradient(135deg, #5E8B5A, #7CA878);
  color: white;
  font-size: 24px;
}

.card-back {
  background: white;
  transform: rotateY(180deg);
  border: 2px solid var(--color-primary, #5E8B5A);
}

.card.matched .card-back {
  background: var(--color-bg-hover, #E8F0E6);
}

.result-section {
  text-align: center;
}

.result-content h2 {
  color: var(--color-primary, #5E8B5A);
  margin-bottom: 20px;
}

.result-actions {
  margin-top: 20px;
  display: flex;
  gap: 12px;
  justify-content: center;
}
</style>
