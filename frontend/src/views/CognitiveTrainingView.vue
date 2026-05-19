<template>
  <div class="cognitive-training-container">
    <el-card class="header-card">
      <h2>认知训练</h2>
      <p>科学的认知训练方案，提升各项认知能力</p>
    </el-card>

    <el-row :gutter="20" class="overview-section">
      <el-col :span="8">
        <el-card class="overview-card" shadow="hover">
          <el-statistic title="总会话数" :value="progress.total_sessions">
            <template #suffix>次</template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="overview-card" shadow="hover">
          <el-statistic title="平均分" :value="progress.average_score">
            <template #suffix>分</template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="overview-card" shadow="hover">
          <el-statistic title="一致性评分" :value="progress.consistency_score">
            <template #suffix>分</template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>

    <el-divider>训练项目</el-divider>

    <el-row :gutter="20" class="training-grid">
      <el-col :span="12" v-for="game in trainingGames" :key="game.name">
        <el-card class="game-card" shadow="hover">
          <div class="game-content">
            <div class="game-icon">{{ game.icon }}</div>
            <div class="game-info">
              <h3 class="game-name">{{ game.name }}</h3>
              <p class="game-domain">{{ game.domain }}</p>
              <el-tag size="small" type="info">{{ game.difficulty }}</el-tag>
            </div>
            <el-button type="primary" @click="startTraining(game.route)">
              开始训练
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="progress-card">
      <template #header>
        <span>训练进度</span>
      </template>

      <div v-if="progress.strengths && progress.strengths.length > 0">
        <div class="progress-section">
          <h4 class="progress-title">优势领域</h4>
          <div class="tag-group">
            <el-tag v-for="s in progress.strengths" :key="s" type="success" effect="light" class="progress-tag">
              {{ s }}
            </el-tag>
          </div>
        </div>

        <div class="progress-section">
          <h4 class="progress-title">待提升领域</h4>
          <div class="tag-group">
            <el-tag v-for="w in progress.weaknesses" :key="w" type="warning" effect="light" class="progress-tag">
              {{ w }}
            </el-tag>
          </div>
        </div>

        <div v-if="progress.performance_trend && progress.performance_trend.length > 0" class="progress-section">
          <h4 class="progress-title">近期表现趋势</h4>
          <el-table :data="progress.performance_trend.slice(-7)" style="width: 100%">
            <el-table-column prop="date" label="日期" width="150" />
            <el-table-column prop="score" label="评分" width="120">
              <template #default="{ row }">
                <span :style="{ color: getScoreColor(row.score), fontWeight: 'bold' }">
                  {{ row.score }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <el-empty v-else description="暂无训练进度数据，开始训练吧！" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { cognitiveApi } from '@/api/cognitive'

const router = useRouter()

const trainingGames = [
  { icon: '🃏', name: '记忆匹配', domain: '工作记忆', difficulty: '推荐难度：中级', route: 'memory-match' },
  { icon: '📝', name: '类别命名', domain: '语义记忆', difficulty: '推荐难度：初级', route: 'category-naming' },
  { icon: '🔢', name: '序列排序', domain: '执行功能', difficulty: '推荐难度：中级', route: 'sequence-sort' },
  { icon: '💬', name: '词语回忆', domain: '短期记忆', difficulty: '推荐难度：初级', route: 'word-recall' }
]

const progress = reactive({
  total_sessions: 0,
  average_score: 0,
  consistency_score: 0,
  strengths: [],
  weaknesses: [],
  performance_trend: []
})

const startTraining = (gameRoute) => {
  router.push(`/cognitive/training/${gameRoute}`)
}

const loadProgress = async () => {
  try {
    const res = await cognitiveApi.getProgress()
    const data = res.progress || res
    Object.assign(progress, {
      total_sessions: data.total_sessions || 0,
      average_score: data.average_score || 0,
      consistency_score: data.consistency_score || 0,
      strengths: data.strengths || [],
      weaknesses: data.weaknesses || [],
      performance_trend: data.performance_trend || []
    })
  } catch (e) {
    console.error('加载训练进度失败', e)
  }
}

const getScoreColor = (score) => {
  if (score >= 80) return '#67C23A'
  if (score >= 60) return '#E6A23C'
  return '#F56C6C'
}

onMounted(() => {
  loadProgress()
})
</script>

<style scoped>
.cognitive-training-container {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
  text-align: center;
}

.header-card h2 {
  color: var(--color-primary, #5E8B5A);
  margin-bottom: 8px;
}

.header-card p {
  color: var(--color-text-secondary, #7F7D74);
}

.overview-section {
  margin-bottom: 10px;
}

.overview-card {
  text-align: center;
}

.training-grid {
  margin-bottom: 20px;
}

.game-card {
  margin-bottom: 16px;
}

.game-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.game-icon {
  font-size: 42px;
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-hover, #E8F0E6);
  border-radius: 12px;
  flex-shrink: 0;
}

.game-info {
  flex: 1;
}

.game-name {
  font-size: 16px;
  font-weight: bold;
  color: var(--color-text-primary, #2F2E2A);
  margin-bottom: 4px;
}

.game-domain {
  font-size: 13px;
  color: var(--color-text-secondary, #7F7D74);
  margin-bottom: 6px;
}

.progress-card {
  margin-top: 10px;
}

.progress-section {
  margin-bottom: 20px;
}

.progress-title {
  font-size: 14px;
  color: var(--color-text-primary, #2F2E2A);
  margin-bottom: 10px;
}

.tag-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.progress-tag {
  font-size: 13px;
}
</style>
