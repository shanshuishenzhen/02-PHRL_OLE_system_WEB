<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <h2>在线考试系统</h2>
      </template>

      <el-form
        ref="loginForm"
        :model="loginForm"
        :rules="loginRules"
        label-width="0"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="用户名"
            :prefix-icon="User"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="密码"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            class="login-button"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script lang="ts">
import { defineComponent, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

export default defineComponent({
  name: 'Login',
  setup() {
    const router = useRouter()
    const userStore = useUserStore()
    const loading = ref(false)

    const loginForm = reactive({
      username: '',
      password: ''
    })

    const loginRules = {
      username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
      password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
    }

    const handleLogin = async () => {
      try {
        loading.value = true
        // 这里应该调用后端API进行身份验证
        // 示例：模拟API调用
        await new Promise(resolve => setTimeout(resolve, 1000))

        // 模拟登录成功
        const mockUserData = {
          id: '1',
          username: loginForm.username,
          role: 'student',
          token: 'mock-token'
        }

        userStore.setUser(mockUserData)

        // 根据用户角色重定向到相应页面
        if (mockUserData.role === 'student') {
          router.push('/student-exam')
        } else {
          router.push('/debug-dashboard')
        }

        ElMessage.success('登录成功')
      } catch (error) {
        ElMessage.error('登录失败，请重试')
      } finally {
        loading.value = false
      }
    }

    return {
      loginForm,
      loginRules,
      loading,
      handleLogin,
      User,
      Lock
    }
  }
})
</script>

<style lang="scss" scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f7fa;

  .login-card {
    width: 400px;

    :deep(.el-card__header) {
      text-align: center;
      padding: 20px;

      h2 {
        margin: 0;
        color: #303133;
      }
    }

    .login-button {
      width: 100%;
    }
  }
}
</style>