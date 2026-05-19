<template>
  <div class="admin-view">
    <el-page-header @back="$router.back()" content="系统管理" />
    <div class="content">
      <el-tabs v-model="activeTab" type="border-card">
        <el-tab-pane label="概览" name="overview">
          <el-row :gutter="20">
            <el-col :span="6">
              <el-card>
                <el-statistic title="患者总数" :value="1234" />
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card>
                <el-statistic title="医生总数" :value="56" />
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card>
                <el-statistic title="对话总数" :value="8765" />
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card>
                <el-statistic title="今日活跃" :value="234" />
              </el-card>
            </el-col>
          </el-row>
          <el-row :gutter="20" style="margin-top: 20px;">
            <el-col :span="12">
              <el-card>
                <template #header>
                  <div class="card-header">
                    <span>Agent管理</span>
                  </div>
                </template>
                <el-table :data="agents" style="width: 100%">
                  <el-table-column prop="name" label="名称" />
                  <el-table-column prop="type" label="类型" />
                  <el-table-column prop="status" label="状态">
                    <template #default="scope">
                      <el-tag :type="scope.row.status === 'active' ? 'success' : 'info'">
                        {{ scope.row.status }}
                      </el-tag>
                    </template>
                  </el-table-column>
                </el-table>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card>
                <template #header>
                  <div class="card-header">
                    <span>评估记录</span>
                  </div>
                </template>
                <el-table :data="evaluations" style="width: 100%">
                  <el-table-column prop="name" label="测试套件" />
                  <el-table-column prop="score" label="得分" />
                  <el-table-column prop="date" label="日期" />
                </el-table>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>

        <el-tab-pane label="Agent模型配置" name="agent-config">
          <div class="agent-config-section">
            <div class="config-toolbar">
              <div class="toolbar-left">
                <h3>多智能体模型配置</h3>
                <span class="toolbar-desc">为不同的Agent配置不同的大语言模型，数据库配置优先于YAML文件配置</span>
              </div>
              <div class="toolbar-right">
                <el-button type="primary" @click="handleSyncFromYaml" :loading="syncLoading">
                  从YAML同步
                </el-button>
                <el-button @click="showEnvDialog = true">环境变量信息</el-button>
              </div>
            </div>

            <el-table :data="configList" v-loading="tableLoading" style="width: 100%">
              <el-table-column label="Agent" min-width="180">
                <template #default="{ row }">
                  <div class="agent-info">
                    <span class="agent-emoji">{{ row.agent_emoji }}</span>
                    <div>
                      <div class="agent-name">{{ row.agent_name }}</div>
                      <div class="agent-type">{{ row.agent_type }}</div>
                    </div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="provider" label="Provider" width="130">
                <template #default="{ row }">
                  <el-tag size="small" effect="plain">{{ formatProvider(row.provider) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="model" label="模型" min-width="200">
                <template #default="{ row }">
                  <span class="model-name">{{ row.model }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="temperature" label="温度" width="80" align="center" />
              <el-table-column prop="max_tokens" label="Max Tokens" width="110" align="center" />
              <el-table-column label="配置来源" width="110" align="center">
                <template #default="{ row }">
                  <el-tag
                    :type="row.config_source === 'database' ? 'success' : row.config_source === 'yaml' ? 'info' : 'warning'"
                    size="small"
                  >
                    {{ row.config_source === 'database' ? '数据库' : row.config_source === 'yaml' ? 'YAML' : '环境变量' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="更新时间" width="170">
                <template #default="{ row }">
                  <span class="time-text">{{ row.updated_at ? formatTime(row.updated_at) : '-' }}</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="200" fixed="right">
                <template #default="{ row }">
                  <el-button type="primary" link size="small" @click="handleEdit(row)">编辑</el-button>
                  <el-button type="success" link size="small" @click="handleTestConnection(row)" :loading="testingAgent === row.agent_type">测试</el-button>
                  <el-button
                    v-if="row.config_source === 'database'"
                    type="warning"
                    link
                    size="small"
                    @click="handleReset(row)"
                  >重置</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <el-dialog v-model="editDialogVisible" :title="`编辑 ${editForm?.agent_name || ''} 模型配置`" width="560px" destroy-on-close>
      <el-form :model="editForm" label-width="120px" v-if="editForm">
        <el-form-item label="Provider">
          <el-select v-model="editForm.provider" @change="handleProviderChange" style="width: 100%">
            <el-option v-for="p in providerList" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型">
          <el-select v-model="editForm.model" filterable allow-create style="width: 100%" placeholder="选择或输入模型名称">
            <el-option v-for="m in currentModels" :key="m" :label="m" :value="m" />
          </el-select>
        </el-form-item>
        <el-form-item label="温度">
          <el-slider v-model="editForm.temperature" :min="0" :max="2" :step="0.1" show-input />
        </el-form-item>
        <el-form-item label="Max Tokens">
          <el-input-number v-model="editForm.max_tokens" :min="100" :max="128000" :step="500" style="width: 100%" />
        </el-form-item>
        <el-form-item label="超时(秒)">
          <el-input-number v-model="editForm.timeout" :min="10" :max="600" :step="10" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备用Provider">
          <el-select v-model="editForm.fallback_provider" clearable style="width: 100%" placeholder="可选">
            <el-option v-for="p in providerList" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="备用模型">
          <el-input v-model="editForm.fallback_model" placeholder="备用模型名称（可选）" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input
            v-model="editForm.api_key"
            type="password"
            show-password
            placeholder="留空则使用环境变量中的全局Key"
          />
          <div v-if="editForm.api_key_hint" class="key-hint">
            当前: {{ editForm.api_key_hint }}
          </div>
        </el-form-item>
      </el-form>
      <div v-if="testResult" class="test-result" :class="testResult.success ? 'test-success' : 'test-fail'">
        <el-icon v-if="testResult.success"><CircleCheckFilled /></el-icon>
        <el-icon v-else><CircleCloseFilled /></el-icon>
        <span>{{ testResult.message }}</span>
        <span v-if="testResult.success && testResult.response_preview" class="test-preview">
          响应预览: {{ testResult.response_preview }}
        </span>
      </div>
      <template #footer>
        <el-button @click="testResult = null; editDialogVisible = false">取消</el-button>
        <el-button type="success" @click="handleTestInDialog" :loading="testLoading">测试连接</el-button>
        <el-button type="primary" @click="handleSave" :loading="saveLoading">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showEnvDialog" title="环境变量 LLM 配置" width="640px">
      <div v-if="envInfo" class="env-info">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="默认Provider">{{ envInfo.default_provider }}</el-descriptions-item>
          <el-descriptions-item label="默认模型">{{ envInfo.default_model }}</el-descriptions-item>
        </el-descriptions>
        <el-table :data="envInfo.providers" style="width: 100%; margin-top: 16px">
          <el-table-column prop="name" label="Provider" width="120" />
          <el-table-column label="模型列表" min-width="200">
            <template #default="{ row }">
              <el-tag v-for="m in row.models.slice(0, 2)" :key="m" size="small" style="margin: 2px">{{ m }}</el-tag>
              <span v-if="row.models.length > 2" class="more-models">+{{ row.models.length - 2 }}</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.configured ? 'success' : 'danger'" size="small">
                {{ row.configured ? '已配置' : '未配置' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="api_key_hint" label="API Key" width="140" />
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { CircleCheckFilled, CircleCloseFilled } from '@element-plus/icons-vue'
import { agentConfigApi, type AgentLLMConfig, type LLMProviderInfo, type EnvLLMInfo } from '@/api/index'

const activeTab = ref('overview')
const agents = ref([
  { name: '糖尿病专科Agent', type: 'specialist', status: 'active' },
  { name: '高血压专科Agent', type: 'specialist', status: 'active' },
  { name: '营养师Agent', type: 'nutrition', status: 'active' },
  { name: '健康教练Agent', type: 'coach', status: 'inactive' }
])
const evaluations = ref([
  { name: '糖尿病问答测试', score: 0.92, date: '2024-01-15' },
  { name: '安全评估测试', score: 0.88, date: '2024-01-14' },
  { name: '用药安全测试', score: 0.95, date: '2024-01-13' }
])

const configList = ref<AgentLLMConfig[]>([])
const tableLoading = ref(false)
const syncLoading = ref(false)
const saveLoading = ref(false)
const editDialogVisible = ref(false)
const showEnvDialog = ref(false)
const editForm = ref<Partial<AgentLLMConfig> & { provider: string; model: string; temperature: number; max_tokens: number; timeout: number; fallback_provider: string | null; fallback_model: string | null } | null>(null)
const providerList = ref<LLMProviderInfo[]>([])
const envInfo = ref<EnvLLMInfo | null>(null)
const testingAgent = ref('')
const testLoading = ref(false)
const testResult = ref<{ success: boolean; message: string; response_preview?: string } | null>(null)

const currentModels = computed(() => {
  if (!editForm.value) return []
  const p = providerList.value.find(item => item.id === editForm.value!.provider)
  return p?.models || []
})

function formatProvider(provider: string) {
  const map: Record<string, string> = {
    openai: 'OpenAI',
    anthropic: 'Anthropic',
    siliconflow: 'SiliconFlow',
    ollama: 'Ollama',
    dashscope: 'DashScope',
    default: '默认',
  }
  return map[provider] || provider
}

function formatTime(dateStr: string) {
  if (!dateStr) return '-'
  try {
    const d = new Date(dateStr)
    return d.toLocaleString('zh-CN')
  } catch {
    return dateStr
  }
}

async function loadConfigs() {
  tableLoading.value = true
  try {
    const res = await agentConfigApi.getAgentConfigs()
    configList.value = res.configs || (res as any)
  } catch (e: any) {
    ElMessage.error('加载Agent配置失败: ' + (e.message || '未知错误'))
  } finally {
    tableLoading.value = false
  }
}

async function loadProviders() {
  try {
    const res = await agentConfigApi.getProviders()
    providerList.value = res.providers || (res as any)
  } catch {
    providerList.value = [
      { id: 'openai', name: 'OpenAI', models: ['gpt-4o', 'gpt-4o-mini'], configured: false, api_key_hint: '' },
      { id: 'anthropic', name: 'Anthropic', models: ['claude-3-5-sonnet-20241022'], configured: false, api_key_hint: '' },
      { id: 'siliconflow', name: 'SiliconFlow', models: ['Qwen/Qwen2.5-7B-Instruct'], configured: false, api_key_hint: '' },
      { id: 'ollama', name: 'Ollama', models: ['llama3', 'qwen2'], configured: false, api_key_hint: '' },
      { id: 'dashscope', name: 'DashScope', models: ['qwen-plus', 'qwen-turbo'], configured: false, api_key_hint: '' },
    ]
  }
}

async function loadEnvInfo() {
  try {
    envInfo.value = await agentConfigApi.getEnvInfo()
  } catch {
    envInfo.value = null
  }
}

function handleEdit(row: AgentLLMConfig) {
  testResult.value = null
  editForm.value = {
    agent_type: row.agent_type,
    agent_name: row.agent_name,
    provider: row.provider,
    model: row.model,
    temperature: row.temperature,
    max_tokens: row.max_tokens,
    timeout: row.timeout,
    fallback_provider: row.fallback_provider,
    fallback_model: row.fallback_model,
  }
  editDialogVisible.value = true
}

function handleProviderChange() {
  if (editForm.value) {
    editForm.value.model = ''
  }
}

async function handleSave() {
  if (!editForm.value) return
  saveLoading.value = true
  try {
    await agentConfigApi.updateAgentConfig(editForm.value.agent_type!, {
      provider: editForm.value.provider,
      model: editForm.value.model,
      temperature: editForm.value.temperature,
      max_tokens: editForm.value.max_tokens,
      timeout: editForm.value.timeout,
      fallback_provider: editForm.value.fallback_provider,
      fallback_model: editForm.value.fallback_model,
    })
    ElMessage.success('配置已保存')
    editDialogVisible.value = false
    await loadConfigs()
  } catch (e: any) {
    ElMessage.error('保存失败: ' + (e.message || '未知错误'))
  } finally {
    saveLoading.value = false
  }
}

async function handleReset(row: AgentLLMConfig) {
  try {
    await ElMessageBox.confirm(
      `确定要将 "${row.agent_name}" 的配置重置为YAML默认值吗？`,
      '确认重置',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await agentConfigApi.resetAgentConfig(row.agent_type)
    ElMessage.success('已重置为YAML默认配置')
    await loadConfigs()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('重置失败: ' + (e.message || '未知错误'))
    }
  }
}

async function handleSyncFromYaml() {
  syncLoading.value = true
  try {
    const res = await agentConfigApi.syncFromYaml()
    ElMessage.success(`同步完成: 新增 ${res.synced} 个, 跳过 ${res.skipped} 个`)
    await loadConfigs()
  } catch (e: any) {
    ElMessage.error('同步失败: ' + (e.message || '未知错误'))
  } finally {
    syncLoading.value = false
  }
}

async function handleTestConnection(row: AgentLLMConfig) {
  testingAgent.value = row.agent_type
  try {
    const res = await agentConfigApi.testConnection({
      provider: row.provider,
      model: row.model,
      temperature: row.temperature,
    })
    if (res.success) {
      ElMessage.success(`${row.agent_name}: ${res.message}`)
    } else {
      ElMessage.error(`${row.agent_name}: ${res.message}`)
    }
  } catch (e: any) {
    ElMessage.error('测试失败: ' + (e.message || '未知错误'))
  } finally {
    testingAgent.value = ''
  }
}

async function handleTestInDialog() {
  if (!editForm.value) return
  testLoading.value = true
  testResult.value = null
  try {
    const res = await agentConfigApi.testConnection({
      provider: editForm.value.provider,
      model: editForm.value.model,
      temperature: editForm.value.temperature,
    })
    testResult.value = res
  } catch (e: any) {
    testResult.value = { success: false, message: '测试请求失败: ' + (e.message || '未知错误') }
  } finally {
    testLoading.value = false
  }
}

onMounted(() => {
  loadConfigs()
  loadProviders()
  loadEnvInfo()
})
</script>

<style scoped>
.content {
  margin-top: 20px;
}

.agent-config-section {
  padding: 10px 0;
}

.config-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.toolbar-left h3 {
  margin: 0 0 4px 0;
  font-size: 16px;
  color: var(--color-text-primary, #2F2E2A);
}

.toolbar-desc {
  font-size: 13px;
  color: var(--color-text-secondary, #7F7D74);
}

.toolbar-right {
  display: flex;
  gap: 10px;
}

.agent-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.agent-emoji {
  font-size: 24px;
}

.agent-name {
  font-weight: 500;
  color: var(--color-text-primary, #2F2E2A);
}

.agent-type {
  font-size: 12px;
  color: var(--color-text-secondary, #7F7D74);
}

.model-name {
  font-family: monospace;
  font-size: 13px;
}

.time-text {
  font-size: 13px;
  color: var(--color-text-secondary, #7F7D74);
}

.more-models {
  color: var(--color-text-secondary, #7F7D74);
  font-size: 12px;
  margin-left: 4px;
}

.env-info {
  padding: 10px 0;
}

.key-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.test-result {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 8px;
  margin-top: 12px;
  font-size: 14px;
  line-height: 1.5;
}

.test-success {
  background: #f0f9eb;
  color: #67c23a;
  border: 1px solid #e1f3d8;
}

.test-fail {
  background: #fef0f0;
  color: #f56c6c;
  border: 1px solid #fde2e2;
}

.test-preview {
  display: block;
  color: var(--color-text-secondary, #7F7D74);
  font-size: 12px;
  margin-top: 4px;
}
</style>
