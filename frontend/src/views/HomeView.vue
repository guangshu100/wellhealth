<template>
  <div class="home-view">
    <!-- 欢迎区 -->
    <div class="welcome-section">
      <div class="welcome-content">
        <h1>🏥 欢迎使用康伴AI平台</h1>
        <p>智能慢病管理，多Agent协作，为您的健康保驾护航</p>
      </div>
      <div class="quick-actions">
        <el-button type="primary" size="large" @click="$router.push('/chat')">
          <el-icon><ChatDotRound /></el-icon>
          开始咨询
        </el-button>
        <el-button size="large" @click="$router.push('/simulation')">
          <el-icon><Cpu /></el-icon>
          干预模拟
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: var(--color-primary);">👥</div>
          <div class="stat-info">
            <div class="stat-value">{{ patientCount }}</div>
            <div class="stat-label">患者总数</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: var(--color-primary-light);">🤖</div>
          <div class="stat-info">
            <div class="stat-value">{{ agentCount }}</div>
            <div class="stat-label">AI专家</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: var(--color-accent);">💬</div>
          <div class="stat-info">
            <div class="stat-value">{{ conversationCount }}</div>
            <div class="stat-label">对话次数</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: var(--color-danger);">📊</div>
          <div class="stat-info">
            <div class="stat-value">{{ simulationCount }}</div>
            <div class="stat-label">模拟次数</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 多Agent展示 -->
    <div class="agents-section">
      <div class="agents-section-header">
        <h2>🤝 多智能体协作系统</h2>
        <el-button
          :icon="Refresh"
          :loading="agentStore.isCheckingStatus"
          size="small"
          circle
          @click="handleRefreshStatus"
          title="刷新状态"
        />
      </div>
      <el-row :gutter="20">
        <el-col :span="8" v-for="(agent, index) in agents" :key="agent.type">
          <div 
            class="agent-showcase" 
            :style="{ '--agent-color': agent.color, '--delay': index * 0.1 + 's' }"
            @click="selectAgentAndChat(agent)"
          >
            <div class="agent-avatar">{{ agent.emoji }}</div>
            <div class="agent-details">
              <h3>{{ agent.name }}</h3>
              <p>{{ agent.description }}</p>
            </div>
            <div class="agent-status" v-if="agent.status">
              <el-tag :type="agent.status === 'online' ? 'success' : agent.status === 'offline' ? 'danger' : 'info'" size="small">
                {{ agent.status === 'online' ? '在线' : agent.status === 'offline' ? '离线' : '检测中' }}
              </el-tag>
              <el-tooltip v-if="agent.status_reason" :content="agent.status_reason" placement="top">
                <el-icon style="margin-left: 4px; color: var(--color-text-secondary, #7F7D74);"><QuestionFilled /></el-icon>
              </el-tooltip>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 功能特色 -->
    <div class="features-section">
      <h2>✨ 核心功能</h2>
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="feature-card">
            <div class="feature-icon">🧠</div>
            <h3>多Agent协作</h3>
            <p>7种专科AI助手协同工作，智能路由到最合适的专家</p>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="feature-card">
            <div class="feature-icon">📚</div>
            <h3>RAG知识增强</h3>
            <p>基于医学知识图谱的检索增强，提供准确可靠的健康建议</p>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="feature-card">
            <div class="feature-icon">🛡️</div>
            <h3>医疗安全红线</h3>
            <p>严格遵循医疗合规，不诊断、不开药、紧急情况及时提醒就医</p>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="feature-card">
            <div class="feature-icon">🔬</div>
            <h3>干预效果模拟</h3>
            <p>基于MiroFish理念，模拟不同干预方案的效果，辅助决策</p>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 工作流程 -->
    <div class="workflow-section">
      <h2>🔄 典型工作流程</h2>
      <div class="workflow-steps">
        <div class="workflow-step">
          <div class="step-number">1</div>
          <div class="step-content">
            <h4>选择患者</h4>
            <p>从患者列表中选择或新建患者档案</p>
          </div>
        </div>
        <div class="step-arrow">→</div>
        <div class="workflow-step">
          <div class="step-number">2</div>
          <div class="step-content">
            <h4>AI咨询</h4>
            <p>多Agent协作回答健康问题</p>
          </div>
        </div>
        <div class="step-arrow">→</div>
        <div class="workflow-step">
          <div class="step-number">3</div>
          <div class="step-content">
            <h4>干预模拟</h4>
            <p>模拟不同方案效果，辅助决策</p>
          </div>
        </div>
        <div class="step-arrow">→</div>
        <div class="workflow-step">
          <div class="step-number">4</div>
          <div class="step-content">
            <h4>生成方案</h4>
            <p>制定个性化健康管理方案</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAgentStore } from '@/stores/agent'
import { usePatientStore } from '@/stores/patient'
import { QuestionFilled, Refresh } from '@element-plus/icons-vue'

const router = useRouter()
const agentStore = useAgentStore()
const patientStore = usePatientStore()

const patientCount = ref(156)
const conversationCount = ref(1234)
const simulationCount = ref(89)

const agents = computed(() => agentStore.agents)
const agentCount = computed(() => agentStore.agents.length)

onMounted(async () => {
  await agentStore.initAgents()
  await patientStore.fetchPatients({ page_size: 100 })
  patientCount.value = patientStore.patients.length || 156
})

const handleRefreshStatus = () => {
  agentStore.checkAgentStatus(true)
}

const selectAgentAndChat = (agent: any) => {
  agentStore.selectAgent(agent)
  router.push('/chat')
}
</script>

<style scoped>
.home-view {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

/* 欢迎区 */
.welcome-section {
  background: var(--gradient-header, linear-gradient(135deg, var(--color-primary), var(--color-primary-light)));
  border-radius: 16px;
  padding: 40px;
  color: white;
  text-align: center;
  margin-bottom: 30px;
}

.welcome-content h1 {
  font-size: 32px;
  margin-bottom: 10px;
}

.welcome-content p {
  font-size: 16px;
  opacity: 0.9;
  margin-bottom: 30px;
}

.quick-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
}

/* 统计卡片 */
.stats-row {
  margin-bottom: 30px;
}

.stat-card {
  background: var(--color-bg-card);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 15px;
  box-shadow: var(--shadow-card);
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: var(--color-text-primary);
}

.stat-label {
  color: var(--color-text-secondary);
  font-size: 14px;
}

/* Agent展示 */
.agents-section {
  margin-bottom: 30px;
}

.agents-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.agents-section-header h2 {
  margin: 0;
  color: var(--color-text-primary);
}

.agent-showcase {
  background: var(--color-bg-card);
  border-radius: 12px;
  padding: 25px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 15px;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
  animation: fadeInUp 0.5s ease forwards;
  animation-delay: var(--delay);
  opacity: 0;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.agent-showcase:hover {
  border-color: var(--agent-color);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.agent-avatar {
  font-size: 48px;
}

.agent-details {
  flex: 1;
}

.agent-details h3 {
  margin: 0 0 5px 0;
  color: var(--color-text-primary);
}

.agent-details p {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 13px;
}

/* 功能特色 */
.features-section {
  margin-bottom: 30px;
}

.features-section h2 {
  margin-bottom: 20px;
  color: #303133;
}

.feature-card {
  background: white;
  border-radius: 12px;
  padding: 25px;
  text-align: center;
  height: 100%;
  transition: all 0.3s;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.feature-icon {
  font-size: 40px;
  margin-bottom: 15px;
}

.feature-card h3 {
  margin: 0 0 10px 0;
  color: #303133;
}

.feature-card p {
  margin: 0;
  color: #909399;
  font-size: 13px;
  line-height: 1.6;
}

/* 工作流程 */
.workflow-section h2 {
  margin-bottom: 20px;
  color: #303133;
}

.workflow-steps {
  background: white;
  border-radius: 12px;
  padding: 30px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.workflow-step {
  display: flex;
  align-items: center;
  gap: 15px;
  flex: 1;
}

.step-number {
  width: 40px;
  height: 40px;
  background: var(--gradient-header);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 18px;
}

.step-content h4 {
  margin: 0 0 5px 0;
  color: #303133;
}

.step-content p {
  margin: 0;
  color: #909399;
  font-size: 13px;
}

.step-arrow {
  font-size: 24px;
  color: var(--color-primary);
  padding: 0 10px;
}
</style>
