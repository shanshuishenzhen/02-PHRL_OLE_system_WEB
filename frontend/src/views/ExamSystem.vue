<template>
  <div class="exam-system">
    <el-container>
      <el-header>
        <h1>职业技能等级认证考试系统</h1>
        <div class="user-info">
          <span>考生：{{ userInfo.name }}</span>
          <span>剩余时间：{{ formatTime(remainingTime) }}</span>
        </div>
      </el-header>
      
      <el-main>
        <el-card class="exam-card">
          <div slot="header" class="clearfix">
            <span>考试题目</span>
            <el-button style="float: right" type="primary" @click="submitExam">提交试卷</el-button>
          </div>
          
          <el-tabs v-model="activeTab">
            <el-tab-pane 
              v-for="(question, index) in questions" 
              :key="index"
              :label="`第${index+1}题`"
              :name="index.toString()"
            >
              <div class="question-content">
                <p>{{ question.content }}</p>
                <el-radio-group v-model="question.answer">
                  <el-radio 
                    v-for="(option, optIndex) in question.options" 
                    :key="optIndex"
                    :label="optIndex"
                  >
                    {{ option }}
                  </el-radio>
                </el-radio-group>
              </div>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue'
import { initWebSocket, closeWebSocket } from '@/api/websocket'
import axios from 'axios'

export default defineComponent({
  name: 'ExamSystem',
  setup() {
    const userInfo = ref({
      name: '',
      examId: ''
    })

    const remainingTime = ref(0)
    const activeTab = ref('0')
    const questions = ref<any[]>([])
    
    // 获取考试数据
    const fetchExamData = async () => {
      try {
        const response = await axios.get('/api/exam/current')
        const data = response.data
        userInfo.value = {
          name: data.student_name,
          examId: data.exam_id
        }
        remainingTime.value = data.duration
        questions.value = data.questions
        
        // 初始化WebSocket监控
        initWebSocket(data.exam_id)
      } catch (error) {
        console.error('获取考试数据失败:', error)
      }
    }

    const formatTime = (seconds: number) => {
      const h = Math.floor(seconds / 3600)
      const m = Math.floor((seconds % 3600) / 60)
      const s = seconds % 60
      return `${h}:${m}:${s}`
    }

    const submitExam = async () => {
      try {
        await axios.post('/api/exam/submit', {
          exam_id: userInfo.value.examId,
          answers: questions.value.map(q => q.answer)
        })
        closeWebSocket()
        // TODO: 跳转到结果页面
      } catch (error) {
        console.error('提交考试失败:', error)
      }
    }

    onMounted(() => {
      fetchExamData()
    })

    return {
      userInfo,
      remainingTime,
      activeTab,
      questions,
      formatTime,
      submitExam
    }
  }
})
</script>

<style scoped>
.exam-system {
  padding: 20px;
}
.user-info {
  float: right;
}
.exam-card {
  min-height: 500px;
}
.question-content {
  padding: 20px;
}
</style>