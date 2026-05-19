<template>
  <div class="cognitive-report-container">
    <el-card class="header-card">
      <div class="header-content">
        <div>
          <h2>训练报告</h2>
          <p>全面了解您的认知训练进展</p>
        </div>
        <el-button type="primary" @click="handleExport">
          导出报告
        </el-button>
      </div>
    </el-card>

    <el-card class="profile-card">
      <template #header>
        <span>认知能力画像</span>
      </template>
      <div class="profile-scores">
        <div class="profile-item">
          <div class="profile-header">
            <span class="profile-name">语言能力</span>
            <span class="profile-value">{{ profileScores.language }}</span>
          </div>
          <el-progress
            :percentage="profileScores.language"
            :color="getDimensionColor(profileScores.language)"
            :stroke-width="18"
          />
        </div>
        <div class="profile-item">
          <div class="profile-header">
            <span class="profile-name">记忆能力</span>
            <span class="profile-value">{{ profileScores.memory }}</span>
          </div>
          <el-progress
            :percentage="profileScores.memory"
            :color="getDimensionColor(profileScores.memory)"
            :stroke-width="18"
          />
        </div>
        <div class="profile-item">
          <div class="profile-header">
            <span class="profile-name">执行功能</span>
            <span class="profile-value">{{ profileScores.executive }}</span>
          </div>
          <el-progress
            :percentage="profileScores.executive"
            :color="getDimensionColor(profileScores.executive)"
            :stroke-width="18"
          />
        </div>
        <div class="profile-item">
          <div class="profile-header">
            <span class="profile-name">注意力</span>
            <span class="profile-value">{{ profileScores.attention }}</span>
          </div>
          <el-progress
            :percentage="profileScores.attention"
            :color="getDimensionColor(profileScores.attention)"
            :stroke-width="18"
          />
        </div>
      </div>
    </el-card>

    <el-row :gutter="20">
      <el-col :span="14">
        <el-card class="trend-card">
          <template #header>
            <span>训练趋势</span>
          </template>
          <div v-if="trendData.length > 0" class="trend-chart">
            <div class="trend-line">
              <div
                v-for="(point, index) in trendData"
                :key="index"
                class="trend-point"
                :style="{ left: getTrendLeft(index), bottom: getTrendBottom(point.score) }"
              >
                <div class="point-dot" :style="{ background: getScoreColor(point.score) }"></div>
                <div class="point-label">{{ point.score }}</div>
              </div>
              <svg class="trend-svg" :viewBox="`0 0 ${trendData.length * 80} 200`" preserveAspectRatio="none">
                <polyline
                  :points="getTrendPoints()"
                  fill="none"
                  stroke="#5E8B5A"
                  stroke-width="2"
                  stroke-linejoin="round"
                />
              </svg>
            </div>
            <div class="trend-dates">
              <span v-for="(point, index) in trendData" :key="index" class="trend-date">
                {{ point.date.slice(5) }}
              </span>
            </div>
          </div>
          <el-empty v-else description="暂无训练趋势数据" />
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card class="consistency-card">
          <template #header>
            <span>一致性评分</span>
          </template>
          <div class="consistency-content">
            <div class="consistency-circle">
              <span class="consistency-value">{{ consistencyScore }}</span>
              <span class="consistency-label">分</span>
            </div>
            <p class="consistency-desc">
              {{ getConsistencyDesc(consistencyScore) }}
            </p>
          </div>
        </el-card>

        <el-card class="game-performance-card">
          <template #header>
            <span>各游戏表现</span>
          </template>
          <div class="game-performance-list">
            <div v-for="game in gamePerformances" :key="game.name" class="game-perf-item">
              <div class="game-perf-header">
                <span class="game-perf-name">{{ game.icon }} {{ game.name }}</span>
                <span class="game-perf-trend" :class="getTrendClass(game.trend)">
                  {{ getTrendIcon(game.trend) }}
                </span>
              </div>
              <el-progress
                :percentage="game.score"
                :color="getDimensionColor(game.score)"
                :stroke-width="12"
              />
            </div>
          </div>
          <el-empty v-if="gamePerformances.length === 0" description="暂无游戏表现数据" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { cognitiveApi } from '@/api/cognitive'

const profileScores = reactive({
  language: 0,
  memory: 0,
  executive: 0,
  attention: 0
})

const trendData = ref([])
const consistencyScore = ref(0)
const gamePerformances = ref([])

const loadReport = async () => {
  try {
    const res = await cognitiveApi.getProgress()
    const data = res.progress || res

    if (data.profile_scores) {
      Object.assign(profileScores, {
        language: data.profile_scores.language || 0,
        memory: data.profile_scores.memory || 0,
        executive: data.profile_scores.executive_function || data.profile_scores.executive || 0,
        attention: data.profile_scores.attention || 0
      })
    }

    consistencyScore.value = data.consistency_score || 0
    trendData.value = data.performance_trend || []

    if (data.game_performances) {
      gamePerformances.value = data.game_performances
    } else if (data.strengths || data.weaknesses) {
      const allDomains = [
        ...(data.strengths || []).map(s => ({ name: s, score: 80, trend: 'up', icon: '📈' })),
        ...(data.weaknesses || []).map(w => ({ name: w, score: 50, trend: 'down', icon: '📉' }))
      ]
      gamePerformances.value = allDomains
    }
  } catch (e) {
    console.error('加载报告数据失败', e)
  }
}

const handleExport = () => {
  ElMessage.info('报告导出功能开发中，敬请期待')
}

const getDimensionColor = (score) => {
  if (score >= 80) return '#67C23A'
  if (score >= 60) return '#E6A23C'
  return '#F56C6C'
}

const getScoreColor = (score) => {
  if (score >= 80) return '#67C23A'
  if (score >= 60) return '#E6A23C'
  return '#F56C6C'
}

const getConsistencyDesc = (score) => {
  if (score >= 80) return '训练表现非常稳定，继续保持！'
  if (score >= 60) return '训练表现较为稳定，仍有提升空间。'
  return '训练表现波动较大，建议保持规律训练。'
}

const getTrendLeft = (index) => {
  const total = trendData.value.length
  if (total <= 1) return '50%'
  return `${(index / (total - 1)) * 90 + 5}%`
}

const getTrendBottom = (score) => {
  return `${Math.max(score, 5)}%`
}

const getTrendPoints = () => {
  const total = trendData.value.length
  if (total === 0) return ''
  return trendData.value
    .map((point, index) => {
      const x = (index / Math.max(total - 1, 1)) * (total * 80)
      const y = 200 - (point.score / 100) * 180 - 10
      return `${x},${y}`
    })
    .join(' ')
}

const getTrendClass = (trend) => {
  if (trend === 'up') return 'trend-up'
  if (trend === 'down') return 'trend-down'
  return 'trend-stable'
}

const getTrendIcon = (trend) => {
  if (trend === 'up') return '↑ 上升'
  if (trend === 'down') return '↓ 下降'
  return '→ 稳定'
}

onMounted(() => {
  loadReport()
})
</script>

<style scoped>
.cognitive-report-container {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-card h2 {
  color: var(--color-primary, #5E8B5A);
  margin-bottom: 4px;
}

.header-card p {
  color: var(--color-text-secondary, #7F7D74);
}

.profile-card {
  margin-bottom: 20px;
}

.profile-scores {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.profile-item {
  padding: 0 10px;
}

.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.profile-name {
  font-size: 14px;
  color: var(--color-text-primary, #2F2E2A);
  font-weight: 500;
}

.profile-value {
  font-size: 18px;
  font-weight: bold;
  color: var(--color-primary, #5E8B5A);
}

.trend-card {
  margin-bottom: 20px;
}

.trend-chart {
  position: relative;
  height: 220px;
  padding: 10px 0;
}

.trend-line {
  position: relative;
  width: 100%;
  height: 180px;
}

.trend-svg {
  width: 100%;
  height: 100%;
}

.trend-point {
  position: absolute;
  transform: translate(-50%, -50%);
  z-index: 2;
}

.point-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.point-label {
  position: absolute;
  top: -22px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 11px;
  color: var(--color-text-secondary, #7F7D74);
  white-space: nowrap;
}

.trend-dates {
  display: flex;
  justify-content: space-between;
  padding: 8px 5% 0;
}

.trend-date {
  font-size: 11px;
  color: var(--color-text-secondary, #7F7D74);
}

.consistency-card {
  margin-bottom: 20px;
}

.consistency-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
}

.consistency-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  border: 6px solid #5E8B5A;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.consistency-value {
  font-size: 36px;
  font-weight: bold;
  color: #5E8B5A;
  line-height: 1;
}

.consistency-label {
  font-size: 13px;
  color: var(--color-text-secondary, #7F7D74);
  margin-top: 2px;
}

.consistency-desc {
  text-align: center;
  color: var(--color-text-secondary, #7F7D74);
  font-size: 14px;
  line-height: 1.6;
}

.game-performance-card {
  margin-bottom: 20px;
}

.game-performance-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.game-perf-item {
  padding: 0 4px;
}

.game-perf-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.game-perf-name {
  font-size: 14px;
  color: var(--color-text-primary, #2F2E2A);
}

.game-perf-trend {
  font-size: 13px;
  font-weight: 500;
}

.trend-up {
  color: #67C23A;
}

.trend-down {
  color: #F56C6C;
}

.trend-stable {
  color: #909399;
}
</style>
