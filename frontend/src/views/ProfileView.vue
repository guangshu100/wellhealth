<template>
  <div class="profile-view">
    <el-card class="profile-card">
      <template #header>
        <div class="card-header">
          <h2>个人中心</h2>
        </div>
      </template>

      <div class="profile-content">
        <div class="avatar-section">
          <div class="avatar-wrapper">
            <el-avatar :size="80" :style="{ background: 'var(--color-primary, #5E8B5A)', fontSize: '32px' }">
              {{ (userInfo.name || '?')[0] }}
            </el-avatar>
          </div>
          <div class="user-brief">
            <h3>{{ userInfo.name || '未设置' }}</h3>
            <el-tag :type="roleTagType" size="small">{{ roleLabel }}</el-tag>
          </div>
        </div>

        <el-tabs v-model="activeTab">
          <el-tab-pane label="基本信息" name="info">
            <el-form :model="form" label-width="80px" class="info-form" :disabled="!editing">
              <el-form-item label="用户名">
                <el-input :value="userInfo.username" disabled />
              </el-form-item>
              <el-form-item label="姓名">
                <el-input v-model="form.name" placeholder="请输入姓名" />
              </el-form-item>
              <el-form-item label="手机号">
                <el-input v-model="form.phone" placeholder="请输入手机号" />
              </el-form-item>
              <el-form-item label="邮箱">
                <el-input v-model="form.email" placeholder="请输入邮箱" />
              </el-form-item>
              <el-form-item label="角色">
                <el-input :value="roleLabel" disabled />
              </el-form-item>
              <el-form-item label="注册时间">
                <el-input :value="formatTime(userInfo.created_at)" disabled />
              </el-form-item>
            </el-form>
            <div class="form-actions">
              <el-button v-if="!editing" type="primary" @click="startEdit">编辑信息</el-button>
              <template v-else>
                <el-button @click="cancelEdit">取消</el-button>
                <el-button type="primary" :loading="saving" @click="saveInfo">保存</el-button>
              </template>
            </div>
          </el-tab-pane>

          <el-tab-pane label="修改密码" name="password">
            <el-form :model="pwdForm" :rules="pwdRules" ref="pwdFormRef" label-width="100px" class="pwd-form">
              <el-form-item label="当前密码" prop="oldPassword">
                <el-input v-model="pwdForm.oldPassword" type="password" show-password placeholder="请输入当前密码" />
              </el-form-item>
              <el-form-item label="新密码" prop="newPassword">
                <el-input v-model="pwdForm.newPassword" type="password" show-password placeholder="请输入新密码（至少6位）" />
              </el-form-item>
              <el-form-item label="确认新密码" prop="confirmPassword">
                <el-input v-model="pwdForm.confirmPassword" type="password" show-password placeholder="请再次输入新密码" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="changingPwd" @click="changePassword">修改密码</el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { updateUserInfo, changePassword as changePasswordApi } from '@/api/auth'
import type { FormInstance, FormRules } from 'element-plus'

const authStore = useAuthStore()

const userInfo = computed(() => authStore.userInfo || {})

const ROLE_MAP: Record<string, string> = {
  patient: '患者',
  family: '家属',
  doctor: '医生',
  admin: '管理员',
}

const roleLabel = computed(() => ROLE_MAP[userInfo.value.role] || userInfo.value.role || '未知')
const roleTagType = computed(() => {
  const map: Record<string, string> = { admin: 'danger', doctor: 'warning', family: 'info', patient: 'success' }
  return map[userInfo.value.role] || 'info'
})

const activeTab = ref('info')
const editing = ref(false)
const saving = ref(false)
const changingPwd = ref(false)

const form = reactive({ name: '', phone: '', email: '' })

const startEdit = () => {
  form.name = userInfo.value.name || ''
  form.phone = userInfo.value.phone || ''
  form.email = userInfo.value.email || ''
  editing.value = true
}

const cancelEdit = () => { editing.value = false }

const saveInfo = async () => {
  saving.value = true
  try {
    const res = await updateUserInfo({ name: form.name, phone: form.phone, email: form.email })
    authStore.userInfo = res
    localStorage.setItem('userInfo', JSON.stringify(res))
    editing.value = false
    ElMessage.success('信息更新成功')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '更新失败')
  } finally {
    saving.value = false
  }
}

const pwdForm = reactive({ oldPassword: '', newPassword: '', confirmPassword: '' })
const pwdFormRef = ref<FormInstance>()

const pwdRules = reactive<FormRules>({
  oldPassword: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (_rule: any, value: string, callback: any) => {
        if (value !== pwdForm.newPassword) callback(new Error('两次输入的密码不一致'))
        else callback()
      },
      trigger: 'blur',
    },
  ],
})

const changePassword = async () => {
  const valid = await pwdFormRef.value?.validate().catch(() => false)
  if (!valid) return
  changingPwd.value = true
  try {
    await changePasswordApi(pwdForm.oldPassword, pwdForm.newPassword)
    ElMessage.success('密码修改成功')
    pwdForm.oldPassword = ''
    pwdForm.newPassword = ''
    pwdForm.confirmPassword = ''
    pwdFormRef.value?.resetFields()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '修改失败')
  } finally {
    changingPwd.value = false
  }
}

const formatTime = (t: string | null) => {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}

onMounted(() => {
  authStore.fetchUserInfo()
})
</script>

<style scoped>
.profile-view {
  padding: 20px;
  max-width: 700px;
  margin: 0 auto;
}

.profile-card {
  border-radius: 12px;
}

.card-header h2 {
  margin: 0;
  color: var(--color-text-primary, #2F2E2A);
}

.avatar-section {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--color-border, #DDCFB0);
}

.user-brief h3 {
  margin: 0 0 6px 0;
  color: var(--color-text-primary, #2F2E2A);
}

.info-form {
  max-width: 500px;
}

.form-actions {
  margin-top: 20px;
  padding-left: 80px;
}

.pwd-form {
  max-width: 500px;
}
</style>
