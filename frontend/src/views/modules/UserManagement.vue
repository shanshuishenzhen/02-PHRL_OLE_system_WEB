<template>
  <div class="user-management">
    <h1>用户管理模块</h1>
    <div class="module-content">
      <el-card class="function-card">
        <template #header>
          <h3>用户列表</h3>
        </template>
        <el-table :data="users" style="width: 100%">
          <el-table-column prop="username" label="用户名" />
          <el-table-column prop="role" label="角色" />
          <el-table-column prop="status" label="状态" />
          <el-table-column label="操作">
            <template #default="scope">
              <el-button size="small" @click="editUser(scope.row)">编辑</el-button>
              <el-button size="small" type="danger" @click="deleteUser(scope.row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card class="function-card">
        <template #header>
          <h3>角色管理</h3>
        </template>
        <el-table :data="roles" style="width: 100%">
          <el-table-column prop="name" label="角色名称" />
          <el-table-column prop="description" label="描述" />
          <el-table-column prop="permissions" label="权限" />
          <el-table-column label="操作">
            <template #default="scope">
              <el-button size="small" @click="editRole(scope.row)">编辑</el-button>
              <el-button size="small" type="danger" @click="deleteRole(scope.row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue'

export default defineComponent({
  name: 'UserManagement',
  setup() {
    const users = ref([
      { username: 'admin', role: '管理员', status: '在线' },
      { username: 'teacher1', role: '教师', status: '离线' },
      { username: 'student1', role: '学生', status: '在线' }
    ])

    const roles = ref([
      { name: '管理员', description: '系统管理员', permissions: '全部权限' },
      { name: '教师', description: '教师用户', permissions: '考试管理、成绩管理' },
      { name: '学生', description: '学生用户', permissions: '参加考试、查看成绩' }
    ])

    const editUser = (user: any) => {
      console.log('编辑用户:', user)
    }

    const deleteUser = (user: any) => {
      console.log('删除用户:', user)
    }

    const editRole = (role: any) => {
      console.log('编辑角色:', role)
    }

    const deleteRole = (role: any) => {
      console.log('删除角色:', role)
    }

    return {
      users,
      roles,
      editUser,
      deleteUser,
      editRole,
      deleteRole
    }
  }
})
</script>

<style lang="scss" scoped>
.user-management {
  padding: 20px;

  h1 {
    margin-bottom: 20px;
    color: #303133;
  }

  .module-content {
    display: grid;
    gap: 20px;
  }

  .function-card {
    h3 {
      margin: 0;
      color: #409EFF;
    }
  }
}
</style>