<template>
  <div class="patient-view">
    <el-page-header @back="$router.back()" content="患者管理" />
    <div class="content">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>患者列表</span>
            <el-button type="primary" @click="handleAdd">新增患者</el-button>
          </div>
        </template>
        <el-table :data="patients" style="width: 100%">
          <el-table-column prop="name" label="姓名" width="120" />
          <el-table-column prop="age" label="年龄" width="80" />
          <el-table-column prop="gender" label="性别" width="80" />
          <el-table-column prop="phone" label="电话" width="150" />
          <el-table-column label="操作">
            <template #default="scope">
              <el-button link type="primary" @click="handleView(scope.row)">查看</el-button>
              <el-button link type="primary" @click="handleEdit(scope.row)">编辑</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const patients = ref([])

const handleAdd = () => {
  // TODO: 实现新增患者
}

const handleView = (row: any) => {
  // TODO: 实现查看患者
}

const handleEdit = (row: any) => {
  // TODO: 实现编辑患者
}
</script>

<style scoped>
.content {
  margin-top: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
