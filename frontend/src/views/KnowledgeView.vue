<template>
  <div class="knowledge-view">
    <el-page-header @back="$router.back()" content="知识库管理" />
    <div class="content">
      <!-- 操作栏 -->
      <el-card class="toolbar-card">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-input v-model="searchKeyword" placeholder="搜索标题/内容" clearable @keyup.enter="loadKnowledge">
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-col>
          <el-col :span="4">
            <el-select v-model="typeFilter" placeholder="知识类型" clearable @change="loadKnowledge">
              <el-option v-for="t in knowledgeTypes" :key="t.value" :label="t.label" :value="t.value">
                <span>{{ t.icon }} {{ t.label }}</span>
              </el-option>
            </el-select>
          </el-col>
          <el-col :span="3">
            <el-select v-model="statusFilter" placeholder="状态" clearable @change="loadKnowledge">
              <el-option label="草稿" value="draft" />
              <el-option label="已发布" value="published" />
              <el-option label="已归档" value="archived" />
            </el-select>
          </el-col>
          <el-col :span="11" style="text-align: right;">
            <el-button type="primary" @click="handleAdd">
              <el-icon><Plus /></el-icon>
              新增知识
            </el-button>
            <el-button @click="loadKnowledge">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </el-col>
        </el-row>
      </el-card>

      <!-- 知识列表 -->
      <el-card>
        <el-table :data="knowledgeList" v-loading="loading" style="width: 100%">
          <el-table-column prop="title" label="标题" min-width="200">
            <template #default="{ row }">
              <div class="title-cell">
                <span class="title-text">{{ row.title }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="type" label="类型" width="100">
            <template #default="{ row }">
              <el-tag :type="getTypeTag(row.type)" size="small">
                {{ getTypeName(row.type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="tags" label="标签" width="180">
            <template #default="{ row }">
              <el-tag v-for="tag in (row.tags || []).slice(0, 3)" :key="tag" size="small" type="info" style="margin-right: 4px;">
                {{ tag }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)" size="small">
                {{ getStatusName(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="view_count" label="浏览" width="60" align="center">
            <template #default="{ row }">
              <span>{{ row.view_count || 0 }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="helpful_count" label="点赞" width="60" align="center">
            <template #default="{ row }">
              <span>{{ row.helpful_count || 0 }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="160">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="handleView(row)">查看</el-button>
              <el-button link type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
              <el-button link type="success" size="small" @click="handlePublish(row)" v-if="row.status === 'draft'">
                发布
              </el-button>
              <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-wrap">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :total="total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @size-change="loadKnowledge"
            @current-change="loadKnowledge"
          />
        </div>
      </el-card>

      <!-- 新增/编辑对话框 -->
      <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑知识' : '新增知识'" width="700px" :close-on-click-modal="false">
        <el-form :model="knowledgeForm" label-width="80px" :rules="formRules" ref="formRef">
          <el-form-item label="标题" prop="title">
            <el-input v-model="knowledgeForm.title" placeholder="请输入知识标题" />
          </el-form-item>
          <el-form-item label="类型" prop="type">
            <el-select v-model="knowledgeForm.type" placeholder="请选择类型" style="width: 100%;">
              <el-option v-for="t in knowledgeTypes" :key="t.value" :label="t.label" :value="t.value">
                <span>{{ t.icon }} {{ t.label }}</span>
              </el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="标签">
            <el-select v-model="knowledgeForm.tags" multiple filterable allow-create placeholder="输入标签后按回车" style="width: 100%;">
              <el-option v-for="tag in commonTags" :key="tag" :label="tag" :value="tag" />
            </el-select>
          </el-form-item>
          <el-form-item label="来源">
            <el-input v-model="knowledgeForm.source" placeholder="知识来源，如指南名称、文献等" />
          </el-form-item>
          <el-form-item label="作者">
            <el-input v-model="knowledgeForm.author" placeholder="作者/审核人" />
          </el-form-item>
          <el-form-item label="内容" prop="content">
            <el-input v-model="knowledgeForm.content" type="textarea" :rows="10" placeholder="请输入知识内容" />
          </el-form-item>
          <el-form-item label="状态" v-if="isEdit">
            <el-radio-group v-model="knowledgeForm.status">
              <el-radio label="draft">草稿</el-radio>
              <el-radio label="published">已发布</el-radio>
              <el-radio label="archived">已归档</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
            {{ isEdit ? '保存' : '创建' }}
          </el-button>
        </template>
      </el-dialog>

      <!-- 查看详情对话框 -->
      <el-dialog v-model="viewVisible" title="知识详情" width="700px">
        <div v-if="currentKnowledge" class="view-content">
          <div class="view-header">
            <h2>{{ currentKnowledge.title }}</h2>
            <div class="view-meta">
              <el-tag :type="getTypeTag(currentKnowledge.type)">{{ getTypeName(currentKnowledge.type) }}</el-tag>
              <el-tag :type="getStatusType(currentKnowledge.status)">{{ getStatusName(currentKnowledge.status) }}</el-tag>
              <span class="meta-item">👁️ {{ currentKnowledge.view_count || 0 }}</span>
              <span class="meta-item">👍 {{ currentKnowledge.helpful_count || 0 }}</span>
            </div>
          </div>
          
          <el-divider />
          
          <div class="view-info">
            <p v-if="currentKnowledge.source"><strong>来源：</strong>{{ currentKnowledge.source }}</p>
            <p v-if="currentKnowledge.author"><strong>作者：</strong>{{ currentKnowledge.author }}</p>
            <p><strong>标签：</strong>
              <el-tag v-for="tag in (currentKnowledge.tags || [])" :key="tag" size="small" type="info" style="margin-right: 4px;">
                {{ tag }}
              </el-tag>
            </p>
          </div>
          
          <div class="view-body">
            <h4>内容</h4>
            <div class="content-text">{{ currentKnowledge.content }}</div>
          </div>
          
          <div class="view-footer">
            <span>创建时间：{{ formatDate(currentKnowledge.created_at) }}</span>
            <span>更新时间：{{ formatDate(currentKnowledge.updated_at) }}</span>
          </div>
        </div>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { knowledgeApi, type KnowledgeItem } from '@/api'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import { Search, Plus, Refresh } from '@element-plus/icons-vue'

const loading = ref(false)
const submitLoading = ref(false)
const knowledgeList = ref<KnowledgeItem[]>([])
const searchKeyword = ref('')
const typeFilter = ref('')
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const dialogVisible = ref(false)
const viewVisible = ref(false)
const isEdit = ref(false)
const currentKnowledgeId = ref('')
const currentKnowledge = ref<KnowledgeItem | null>(null)
const formRef = ref<FormInstance>()

const knowledgeTypes = ref<Array<{ value: string; label: string; icon: string }>>([])

const commonTags = [
  '糖尿病', '高血压', '高血脂', '饮食', '运动', '用药', '血糖', '血压',
  '并发症', '预防', '治疗', '护理', '康复', '检查', '指标'
]

const knowledgeForm = reactive({
  title: '',
  type: 'disease',
  tags: [] as string[],
  source: '',
  author: '',
  content: '',
  status: 'draft'
})

const formRules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  type: [{ required: true, message: '请选择类型', trigger: 'change' }],
  content: [{ required: true, message: '请输入内容', trigger: 'blur' }]
}

onMounted(() => {
  loadKnowledgeTypes()
  loadKnowledge()
})

const loadKnowledgeTypes = async () => {
  try {
    const res = await knowledgeApi.getTypes()
    knowledgeTypes.value = res.types || []
  } catch (e) {
    knowledgeTypes.value = [
      { value: 'disease', label: '疾病知识', icon: '🏥' },
      { value: 'drug', label: '用药知识', icon: '💊' },
      { value: 'food', label: '饮食知识', icon: '🍎' },
      { value: 'exercise', label: '运动知识', icon: '🏃' },
      { value: 'guideline', label: '指南规范', icon: '📋' },
      { value: 'nursing', label: '护理知识', icon: '🏥' },
      { value: 'other', label: '其他', icon: '📖' }
    ]
  }
}

const loadKnowledge = async () => {
  loading.value = true
  try {
    const res = await knowledgeApi.getList({
      search: searchKeyword.value || undefined,
      type: typeFilter.value || undefined,
      status: statusFilter.value || undefined,
      page: currentPage.value,
      page_size: pageSize.value
    })
    knowledgeList.value = res.items || []
    total.value = res.total || 0
  } catch (error) {
    console.error('加载失败:', error)
    knowledgeList.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

const getTypeName = (type: string) => {
  const typeMap: Record<string, string> = {
    disease: '疾病',
    drug: '用药',
    food: '饮食',
    exercise: '运动',
    guideline: '指南',
    nursing: '护理',
    other: '其他'
  }
  return typeMap[type] || type
}

const getTypeTag = (type: string) => {
  const tagMap: Record<string, string> = {
    disease: 'danger',
    drug: 'warning',
    food: 'success',
    exercise: 'primary',
    guideline: 'info',
    nursing: 'warning',
    other: 'info'
  }
  return tagMap[type] || 'info'
}

const getStatusName = (status: string) => {
  const statusMap: Record<string, string> = {
    draft: '草稿',
    published: '已发布',
    archived: '已归档'
  }
  return statusMap[status] || status
}

const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    draft: 'info',
    published: 'success',
    archived: ''
  }
  return typeMap[status] || 'info'
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const handleAdd = () => {
  isEdit.value = false
  currentKnowledgeId.value = ''
  Object.assign(knowledgeForm, {
    title: '',
    type: 'disease',
    tags: [],
    source: '',
    author: '',
    content: '',
    status: 'draft'
  })
  dialogVisible.value = true
}

const handleEdit = (row: KnowledgeItem) => {
  isEdit.value = true
  currentKnowledgeId.value = row.id
  Object.assign(knowledgeForm, {
    title: row.title,
    type: row.type,
    tags: row.tags || [],
    source: row.source || '',
    author: row.author || '',
    content: row.content,
    status: row.status
  })
  dialogVisible.value = true
}

const handleView = async (row: KnowledgeItem) => {
  try {
    const res = await knowledgeApi.getById(row.id)
    currentKnowledge.value = res
  } catch (e) {
    currentKnowledge.value = row
  }
  viewVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  
  submitLoading.value = true
  try {
    if (isEdit.value) {
      await knowledgeApi.update(currentKnowledgeId.value, knowledgeForm)
      ElMessage.success('更新成功')
    } else {
      await knowledgeApi.create(knowledgeForm)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadKnowledge()
  } catch (error) {
    ElMessage.error('操作失败')
  } finally {
    submitLoading.value = false
  }
}

const handlePublish = async (row: KnowledgeItem) => {
  try {
    await knowledgeApi.update(row.id, { status: 'published' })
    ElMessage.success('发布成功')
    loadKnowledge()
  } catch (error) {
    ElMessage.error('发布失败')
  }
}

const handleDelete = (row: KnowledgeItem) => {
  ElMessageBox.confirm(`确定删除知识 "${row.title}" 吗？`, '提示', {
    type: 'warning'
  }).then(async () => {
    try {
      await knowledgeApi.delete(row.id)
      ElMessage.success('删除成功')
      loadKnowledge()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  })
}
</script>

<style scoped>
.content {
  margin-top: 20px;
}

.toolbar-card {
  margin-bottom: 20px;
}

.pagination-wrap {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.title-cell .title-text {
  font-weight: 500;
}

/* 查看详情样式 */
.view-content {
  padding: 10px;
}

.view-header {
  margin-bottom: 20px;
}

.view-header h2 {
  margin: 0 0 15px 0;
  color: #303133;
}

.view-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.meta-item {
  color: #909399;
  font-size: 14px;
}

.view-info {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.view-info p {
  margin: 5px 0;
  color: #606266;
}

.view-body {
  margin-bottom: 20px;
}

.view-body h4 {
  margin: 0 0 10px 0;
  color: #303133;
}

.content-text {
  white-space: pre-wrap;
  line-height: 1.8;
  color: #606266;
  background: #fafafa;
  padding: 15px;
  border-radius: 8px;
}

.view-footer {
  display: flex;
  justify-content: space-between;
  color: #909399;
  font-size: 13px;
  padding-top: 15px;
  border-top: 1px solid #eee;
}
</style>
