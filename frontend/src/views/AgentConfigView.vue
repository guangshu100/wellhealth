<template>
  <div class="agent-config-view">
    <el-page-header @back="$router.back()" content="Agent模型配置" />

    <div class="content">
      <el-card class="toolbar-card">
        <div class="toolbar">
          <div class="toolbar-left">
            <el-button type="primary" @click="handleSyncFromYaml" :loading="syncLoading">
              从YAML同步
            </el-button>
            <el-button @click="handleShowEnvInfo" :loading="envLoading">
              环境变量信息
            </el-button>
          </div>
          <el-button @click="loadConfigs" :loading="loading">
            刷新
          </el-button>
        </div>
      </el-card>

      <el-card class="table-card">
        <el-table :data="configs" v-loading="loading" style="width: 100%">
          <el-table-column label="Agent名称" min-width="160">
            <template #default="{ row }">
              <div class="agent-name-cell">
                <span class="agent-emoji">{{ row.agent_emoji }}</span>
                <span class="agent-name">{{ row.agent_name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="agent_type" label="类型" width="140" />
          <el-table-column prop="provider" label="Provider" width="120">
            <template #default="{ row }">
              <el-tag size="small">{{ row.provider }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="model" label="模型" min-width="180" />
          <el-table-column prop="temperature" label="温度" width="80" align="center" />
          <el-table-column label="配置来源" width="110" align="center">
            <template #default="{ row }">
              <el-tag :type="getSourceTagType(row.config_source)" size="small">
                {{ row.config_source }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="更新时间" width="170">
            <template #default="{ row }">
              <span class="time-text">{{ formatTime(row.updated_at) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click="handleEdit(row)">
                编辑
              </el-button>
              <el-button type="danger" link size="small" @click="handleReset(row)">
                重置
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <el-dialog v-model="editDialogVisible" :title="`编辑 - ${editForm?.agent_name || ''}`" width="560px" destroy-on-close>
      <el-form :model="editForm" label-width="120px" label-position="right">
        <el-form-item label="Provider">
          <el-select v-model="editForm.provider" @change="handleProviderChange" style="width: 100%">
            <el-option v-for="p in providerOptions" :key="p.value" :label="p.label" :value="p.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型">
          <el-select v-model="editForm.model" filterable allow-create style="width: 100%">
            <el-option v-for="m in currentModels" :key="m" :label="m" :value="m" />
          </el-select>
        </el-form-item>
        <el-form-item label="温度">
          <el-slider v-model="editForm.temperature" :min="0" :max="2" :step="0.1" show-input />
        </el-form-item>
        <el-form-item label="Max Tokens">
          <el-input-number v-model="editForm.max_tokens" :min="1" :max="128000" :step="256" style="width: 100%" />
        </el-form-item>
        <el-form-item label="Timeout(ms)">
          <el-input-number v-model="editForm.timeout" :min="1000" :max="300000" :step="5000" style="width: 100%" />
        </el-form-item>
        <el-form-item label="Fallback Provider">
          <el-select v-model="editForm.fallback_provider" clearable @change="handleFallbackProviderChange" style="width: 100%">
            <el-option v-for="p in providerOptions" :key="p.value" :label="p.label" :value="p.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="Fallback Model">
          <el-select v-model="editForm.fallback_model" clearable filterable allow-create style="width: 100%">
            <el-option v-for="m in fallbackModels" :key="m" :label="m" :value="m" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveEdit" :loading="saveLoading">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="envDialogVisible" title="环境变量信息" width="600px" destroy-on-close>
      <div v-if="envInfo" class="env-info-content">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="默认 Provider">{{ envInfo.default_provider }}</el-descriptions-item>
          <el-descriptions-item label="默认 Model">{{ envInfo.default_model }}</el-descriptions-item>
        </el-descriptions>

        <div class="env-providers-title">已配置的 Provider</div>
        <el-table :data="envInfo.providers" style="width: 100%" size="small">
          <el-table-column prop="name" label="Provider" width="120" />
          <el-table-column label="可用模型" min-width="200">
            <template #default="{ row }">
              <el-tag v-for="m in row.models" :key="m" size="small" style="margin: 2px 4px 2px 0;">
                {{ m }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="已配置" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="row.configured ? 'success' : 'danger'" size="small">
                {{ row.configured ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="api_key_hint" label="API Key" width="140" />
        </el-table>
      </div>
      <div v-else class="env-loading">
        加载中...
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { agentConfigApi, type AgentLLMConfig, type EnvLLMInfo } from '@/api'

const providerModelMap: Record<string, string[]> = {
  openai: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
  anthropic: ['claude-3-5-sonnet-20241022', 'claude-3-opus-20240229', 'claude-3-haiku-20240307'],
  siliconflow: ['Qwen/Qwen2.5-7B-Instruct', 'Qwen/Qwen2.5-72B-Instruct', 'deepseek-ai/DeepSeek-V2.5', 'THUDM/glm-4-9b-chat'],
  ollama: ['llama3', 'qwen2', 'glm4', 'mistral'],
  dashscope: ['qwen-plus', 'qwen-turbo', 'qwen-max']
}

const providerOptions = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'siliconflow', label: 'SiliconFlow' },
  { value: 'ollama', label: 'Ollama' },
  { value: 'dashscope', label: 'DashScope' }
]

const configs = ref<AgentLLMConfig[]>([])
const loading = ref(false)
const syncLoading = ref(false)
const envLoading = ref(false)
const saveLoading = ref(false)

const editDialogVisible = ref(false)
const envDialogVisible = ref(false)
const envInfo = ref<EnvLLMInfo | null>(null)

const editForm = ref<Partial<AgentLLMConfig> & { agent_type: string }>({
  agent_type: '',
  provider: '',
  model: '',
  temperature: 0.7,
  max_tokens: 4096,
  timeout: 60000,
  fallback_provider: null,
  fallback_model: null
})

const currentModels = computed(() => {
  return providerModelMap[editForm.value.provider] || []
})

const fallbackModels = computed(() => {
  return providerModelMap[editForm.value.fallback_provider || ''] || []
})

function getSourceTagType(source: string): string {
  switch (source) {
    case 'database': return 'success'
    case 'yaml': return 'info'
    case 'env': return 'warning'
    default: return 'info'
  }
}

function formatTime(timeStr: string): string {
  if (!timeStr) return '-'
  const d = new Date(timeStr)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

async function loadConfigs() {
  loading.value = true
  try {
    const res = await agentConfigApi.getAgentConfigs()
    configs.value = res.configs || []
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '加载配置失败')
  } finally {
    loading.value = false
  }
}

async function handleSyncFromYaml() {
  try {
    await ElMessageBox.confirm('确定要从YAML同步所有Agent配置到数据库吗？这将覆盖数据库中的现有配置。', '确认同步', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }

  syncLoading.value = true
  try {
    const res = await agentConfigApi.syncFromYaml()
    ElMessage.success(`同步成功，共同步 ${res.synced} 个Agent`)
    await loadConfigs()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '同步失败')
  } finally {
    syncLoading.value = false
  }
}

async function handleShowEnvInfo() {
  envDialogVisible.value = true
  envLoading.value = true
  try {
    envInfo.value = await agentConfigApi.getEnvInfo()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '获取环境变量信息失败')
    envDialogVisible.value = false
  } finally {
    envLoading.value = false
  }
}

function handleEdit(row: AgentLLMConfig) {
  editForm.value = {
    agent_type: row.agent_type,
    agent_name: row.agent_name,
    agent_emoji: row.agent_emoji,
    provider: row.provider,
    model: row.model,
    temperature: row.temperature,
    max_tokens: row.max_tokens,
    timeout: row.timeout,
    fallback_provider: row.fallback_provider,
    fallback_model: row.fallback_model
  }
  editDialogVisible.value = true
}

function handleProviderChange() {
  editForm.value.model = ''
}

function handleFallbackProviderChange() {
  editForm.value.fallback_model = null
}

async function handleSaveEdit() {
  if (!editForm.value.provider || !editForm.value.model) {
    ElMessage.warning('请选择Provider和模型')
    return
  }

  saveLoading.value = true
  try {
    await agentConfigApi.updateAgentConfig(editForm.value.agent_type, {
      provider: editForm.value.provider,
      model: editForm.value.model,
      temperature: editForm.value.temperature,
      max_tokens: editForm.value.max_tokens,
      timeout: editForm.value.timeout,
      fallback_provider: editForm.value.fallback_provider,
      fallback_model: editForm.value.fallback_model
    })
    ElMessage.success('保存成功')
    editDialogVisible.value = false
    await loadConfigs()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '保存失败')
  } finally {
    saveLoading.value = false
  }
}

async function handleReset(row: AgentLLMConfig) {
  try {
    await ElMessageBox.confirm(`确定要重置 "${row.agent_name}" 的配置为YAML默认值吗？`, '确认重置', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }

  try {
    const res = await agentConfigApi.resetAgentConfig(row.agent_type)
    ElMessage.success(res.message || '重置成功')
    await loadConfigs()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '重置失败')
  }
}

onMounted(() => {
  loadConfigs()
})
</script>

<style scoped>
.agent-config-view {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
  background: var(--color-bg-page);
  min-height: calc(100vh - 120px);
}

.content {
  margin-top: 20px;
}

.toolbar-card {
  border-radius: 12px;
  background: var(--color-bg-card);
  margin-bottom: 20px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.toolbar-left {
  display: flex;
  gap: 12px;
}

.table-card {
  border-radius: 12px;
  background: var(--color-bg-card);
}

.table-card :deep(.el-table__header-wrapper th) {
  background: var(--color-bg-page);
}

.agent-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.agent-emoji {
  font-size: 20px;
}

.agent-name {
  font-weight: 500;
  color: var(--color-text-primary);
}

.time-text {
  color: var(--color-text-secondary);
  font-size: 13px;
}

.env-info-content {
  padding: 0 4px;
}

.env-providers-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 20px 0 12px;
}

.env-loading {
  text-align: center;
  padding: 40px 0;
  color: var(--color-text-secondary);
}

:deep(.el-dialog) {
  border-radius: 12px;
}

:deep(.el-slider) {
  padding-right: 60px;
}
</style>
