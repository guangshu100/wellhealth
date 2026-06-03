<template>
  <view class="page">
    <view class="header">
      <text class="title">认知训练</text>
      <text class="subtitle">选择训练项目，在趣味游戏中提升认知能力</text>
    </view>

    <view class="game-grid">
      <view
        class="game-card"
        v-for="game in games"
        :key="game.type"
        @click="startGame(game)"
      >
        <view class="game-emoji">{{ game.emoji }}</view>
        <text class="game-name">{{ game.name }}</text>
        <text class="game-desc">{{ game.description }}</text>
        <view class="difficulty-badge" :class="'badge-' + game.difficulty">
          {{ game.difficultyLabel }}
        </view>
      </view>
    </view>

    <view class="section-card" v-if="exerciseData">
      <text class="section-title">今日训练内容</text>
      <view class="exercise-info">
        <text class="exercise-type">{{ exerciseData.game_type }}</text>
        <text class="exercise-detail">{{ exerciseData.description }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/utils/api'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

interface Game {
  type: string
  name: string
  emoji: string
  description: string
  difficulty: string
  difficultyLabel: string
}

const games = ref<Game[]>([
  { type: 'memory-match', name: '记忆匹配', emoji: '🃏', description: '翻转卡片找到配对，锻炼短期记忆', difficulty: 'easy', difficultyLabel: '简单' },
  { type: 'category-naming', name: '类别命名', emoji: '📝', description: '在限定时间内说出指定类别的词语', difficulty: 'medium', difficultyLabel: '中等' },
  { type: 'sequence-sort', name: '序列排序', emoji: '🔢', description: '按逻辑规律排列数字或图形序列', difficulty: 'medium', difficultyLabel: '中等' },
  { type: 'word-recall', name: '词语回忆', emoji: '💬', description: '记忆并回忆展示的词语列表', difficulty: 'hard', difficultyLabel: '困难' }
])

const exerciseData = ref<any>(null)

const loadExercise = async () => {
  try {
    const res: any = await api.get('/cognitive/training/generate')
    exerciseData.value = res
  } catch {
    exerciseData.value = null
  }
}

const startGame = (game: Game) => {
  uni.navigateTo({
    url: `/pages/cognitive/training/game?type=${game.type}`
  })
}

onMounted(() => {
  loadExercise()
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
  padding: 50rpx 30rpx 40rpx;
  text-align: center;
}

.title {
  display: block;
  font-size: 40rpx;
  font-weight: bold;
  color: var(--color-text-inverse);
}

.subtitle {
  display: block;
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.9);
  margin-top: 10rpx;
}

.game-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20rpx;
  padding: 30rpx 20rpx;
}

.game-card {
  background: var(--color-bg-card);
  border-radius: var(--radius-md);
  padding: 30rpx 24rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
  position: relative;
}

.game-emoji {
  font-size: 64rpx;
  margin-bottom: 16rpx;
}

.game-name {
  font-size: 30rpx;
  font-weight: bold;
  color: var(--color-text-primary);
  margin-bottom: 10rpx;
}

.game-desc {
  font-size: 22rpx;
  color: var(--color-text-secondary);
  text-align: center;
  line-height: 1.5;
  margin-bottom: 16rpx;
}

.difficulty-badge {
  display: inline-block;
  padding: 4rpx 20rpx;
  border-radius: 20rpx;
  font-size: 22rpx;
}

.badge-easy {
  background: rgba(129, 199, 132, 0.15);
  color: var(--color-success);
}

.badge-medium {
  background: rgba(255, 183, 77, 0.15);
  color: var(--color-warning);
}

.badge-hard {
  background: rgba(229, 115, 115, 0.15);
  color: var(--color-danger);
}

.section-card {
  background: var(--color-bg-card);
  border-radius: var(--radius-md);
  padding: 30rpx;
  margin: 0 20rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}

.section-title {
  display: block;
  font-size: 32rpx;
  font-weight: bold;
  color: var(--color-text-primary);
  margin-bottom: 20rpx;
}

.exercise-info {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.exercise-type {
  font-size: 28rpx;
  font-weight: 500;
  color: var(--color-primary);
}

.exercise-detail {
  font-size: 26rpx;
  color: var(--color-text-secondary);
  line-height: 1.5;
}
</style>
