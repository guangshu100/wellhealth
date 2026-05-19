<template>
  <div class="game-container">
    <el-card class="game-header">
      <div class="header-content">
        <el-button text @click="router.back()">
          <el-icon><ArrowLeft /></el-icon>返回
        </el-button>
        <h2>🔢 序列排序</h2>
        <div class="game-stats">
          <span v-if="gameState === 'playing'">用时: {{ formatTime(timer) }}</span>
        </div>
      </div>
    </el-card>

    <div v-if="gameState === 'setup'" class="setup-section">
      <el-card>
        <h3>选择难度</h3>
        <el-radio-group v-model="difficulty" size="large">
          <el-radio-button label="beginner">初级</el-radio-button>
          <el-radio-button label="intermediate">中级</el-radio-button>
          <el-radio-button label="advanced">高级</el-radio-button>
        </el-radio-group>
        <div class="setup-info">
          <p>训练目标：将打乱的步骤按正确顺序排列</p>
          <p>认知域：执行功能、序列记忆、逻辑推理</p>
          <p>慢病定制：胰岛素注射流程、就诊准备流程、低血糖急救步骤</p>
        </div>
        <el-button type="primary" size="large" @click="startGame">开始游戏</el-button>
      </el-card>
    </div>

    <div v-else-if="gameState === 'playing'" class="playing-section">
      <el-card class="challenge-card">
        <h3>{{ currentChallenge.title }}</h3>
        <p>{{ currentChallenge.description }}</p>
      </el-card>
      
      <div class="steps-container">
        <div class="steps-list">
          <div
            v-for="(step, index) in shuffledSteps"
            :key="step.id"
            class="step-item"
            :class="{ 'in-correct-position': isInCorrectPosition(index) }"
            draggable="true"
            @dragstart="dragStart(index, $event)"
            @dragover.prevent
            @drop="drop(index)"
          >
            <span class="step-number">{{ index + 1 }}</span>
            <span class="step-text">{{ step.text }}</span>
          </div>
        </div>
      </div>
      
      <div class="actions">
        <el-button type="primary" @click="checkAnswer">提交答案</el-button>
        <el-button @click="startGame">重新开始</el-button>
      </div>
    </div>

    <div v-else-if="gameState === 'completed'" class="result-section">
      <el-card>
        <div class="result-content">
          <h2 :class="score >= 80 ? 'success' : score >= 60 ? 'warning' : 'error'">
            {{ score >= 80 ? '🎉 完美！' : score >= 60 ? '👍 不错！' : '💪 继续努力！' }}
          </h2>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="题目">{{ currentChallenge.title }}</el-descriptions-item>
            <el-descriptions-item label="得分">{{ score }}</el-descriptions-item>
            <el-descriptions-item label="正确位置">{{ correctPositions }}/{{ shuffledSteps.length }}</el-descriptions-item>
            <el-descriptions-item label="用时">{{ formatTime(timer) }}</el-descriptions-item>
          </el-descriptions>
          <div class="correct-answer">
            <h4>正确顺序：</h4>
            <ol>
              <li v-for="step in currentChallenge.steps" :key="step.id">{{ step.text }}</li>
            </ol>
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

const CHALLENGES = {
  beginner: [
    {
      title: '胰岛素注射流程',
      description: '请将胰岛素注射步骤按正确顺序排列',
      steps: [
        { id: 1, text: '洗手并准备注射用品' },
        { id: 2, text: '检查胰岛素是否有效' },
        { id: 3, text: '选择注射部位并消毒' },
        { id: 4, text: '捏起皮肤，垂直进针' },
        { id: 5, text: '推注胰岛素，停留10秒' },
        { id: 6, text: '拔针，按压注射部位' }
      ]
    }
  ],
  intermediate: [
    {
      title: '就诊准备流程',
      description: '请将就诊前的准备步骤按正确顺序排列',
      steps: [
        { id: 1, text: '整理既往病历和检查报告' },
        { id: 2, text: '记录近期症状和用药情况' },
        { id: 3, text: '准备医保卡和身份证' },
        { id: 4, text: '提前预约挂号' },
        { id: 5, text: '列出想咨询医生的问题' }
      ]
    }
  ],
  advanced: [
    {
      title: '低血糖急救步骤',
      description: '请将低血糖急救步骤按正确顺序排列',
      steps: [
        { id: 1, text: '识别低血糖症状（心慌、出汗、手抖）' },
        { id: 2, text: '立即停止当前活动' },
        { id: 3, text: '补充15-20g快速升糖食物' },
        { id: 4, text: '等待15分钟后复测血糖' },
        { id: 5, text: '如未恢复，再次补充糖分' },
        { id: 6, text: '如意识不清，立即拨打120' }
      ]
    }
  ]
}

const difficulty = ref('intermediate')
const gameState = ref('setup')
const currentChallenge = ref({ title: '', description: '', steps: [] })
const shuffledSteps = ref([])
const draggedIndex = ref(null)
const timer = ref(0)
const score = ref(0)
const correctPositions = ref(0)
let timerInterval = null

const shuffleArray = (arr) => {
  const newArr = [...arr]
  for (let i = newArr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [newArr[i], newArr[j]] = [newArr[j], newArr[i]]
  }
  return newArr
}

const startGame = () => {
  const challenges = CHALLENGES[difficulty.value]
  currentChallenge.value = challenges[Math.floor(Math.random() * challenges.length)]
  shuffledSteps.value = shuffleArray([...currentChallenge.value.steps])
  
  timer.value = 0
  score.value = 0
  correctPositions.value = 0
  gameState.value = 'playing'
  
  if (timerInterval) clearInterval(timerInterval)
  timerInterval = setInterval(() => {
    timer.value++
  }, 1000)
}

const dragStart = (index, event) => {
  draggedIndex.value = index
  event.dataTransfer.effectAllowed = 'move'
}

const drop = (targetIndex) => {
  if (draggedIndex.value === null) return
  
  const items = [...shuffledSteps.value]
  const draggedItem = items[draggedIndex.value]
  items.splice(draggedIndex.value, 1)
  items.splice(targetIndex, 0, draggedItem)
  shuffledSteps.value = items
  draggedIndex.value = null
}

const isInCorrectPosition = (index) => {
  const step = shuffledSteps.value[index]
  const correctIndex = currentChallenge.value.steps.findIndex(s => s.id === step.id)
  return index === correctIndex
}

const checkAnswer = async () => {
  if (timerInterval) clearInterval(timerInterval)
  
  let correct = 0
  shuffledSteps.value.forEach((step, index) => {
    const correctIndex = currentChallenge.value.steps.findIndex(s => s.id === step.id)
    if (index === correctIndex) correct++
  })
  
  correctPositions.value = correct
  const accuracy = correct / shuffledSteps.value.length
  const timeBonus = Math.max(0, 30 - timer.value) * 0.5
  score.value = Math.min(100, Math.round(accuracy * 80 + timeBonus))
  
  gameState.value = 'completed'
  
  try {
    await cognitiveApi.submitTraining({
      exercise_type: 'sequence_sorting',
      difficulty: difficulty.value,
      score: score.value,
      accuracy: accuracy,
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

.playing-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.challenge-card {
  text-align: center;
}

.challenge-card h3 {
  color: var(--color-primary, #5E8B5A);
  margin-bottom: 8px;
}

.steps-container {
  background: white;
  padding: 16px;
  border-radius: 8px;
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--color-bg-hover, #E8F0E6);
  border-radius: 8px;
  cursor: move;
  transition: all 0.2s;
}

.step-item:hover {
  background: #d4e8d0;
}

.step-item.in-correct-position {
  background: #c8e6c9;
  border: 2px solid #4caf50;
}

.step-number {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary, #5E8B5A);
  color: white;
  border-radius: 50%;
  font-size: 14px;
  font-weight: bold;
}

.step-text {
  flex: 1;
}

.actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.result-section {
  text-align: center;
}

.result-content h2 {
  margin-bottom: 20px;
}

.result-content h2.success {
  color: #67C23A;
}

.result-content h2.warning {
  color: #E6A23C;
}

.result-content h2.error {
  color: #F56C6C;
}

.correct-answer {
  margin-top: 20px;
  text-align: left;
  padding: 16px;
  background: var(--color-bg-hover, #E8F0E6);
  border-radius: 8px;
}

.correct-answer h4 {
  margin-bottom: 12px;
}

.correct-answer ol {
  margin: 0;
  padding-left: 20px;
}

.correct-answer li {
  margin: 8px 0;
}

.result-actions {
  margin-top: 20px;
  display: flex;
  gap: 12px;
  justify-content: center;
}
</style>
