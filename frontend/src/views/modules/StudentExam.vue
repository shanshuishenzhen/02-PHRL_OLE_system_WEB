<template>
  <div class="student-exam">
    <div class="exam-header">
      <div class="exam-info">
        <h1>{{ examInfo.name }}</h1>
        <div class="exam-meta">
          <el-tag>总分：{{ examInfo.totalScore }}分</el-tag>
          <el-tag type="warning">时长：{{ examInfo.duration }}分钟</el-tag>
          <el-tag type="info">题目：{{ examInfo.questionCount }}道</el-tag>
        </div>
      </div>

      <div class="exam-timer">
        <div class="timer-label">剩余时间</div>
        <div class="timer-value" :class="{ 'warning': timeRemaining < 600 }">
          {{ formatTime(timeRemaining) }}
        </div>
      </div>
    </div>

    <div class="exam-content">
      <el-row :gutter="20">
        <el-col :span="18">
          <div class="question-area">
            <div
              v-for="question in questions"
              :key="question.id"
              :id="`question-${question.id}`"
              class="question-card"
              :class="{ 'current': currentQuestion.id === question.id }"
            >
              <div class="question-header">
                <span class="question-number">第{{ question.number }}题</span>
                <span class="question-type">{{ question.type }}</span>
                <span class="question-score">{{ question.score }}分</span>
              </div>

              <div class="question-content">
                <div class="question-text" v-html="sanitizeHTML(question.content)"></div>

                <div class="answer-area">
                  <!-- 选择题 -->
                  <template v-if="question.type === '单选题' || question.type === '多选题'">
                    <el-radio-group
                      v-if="question.type === '单选题'"
                      v-model="question.answer"
                      class="option-list"
                    >
                      <el-radio
                        v-for="option in question.options"
                        :key="option.key"
                        :label="option.key"
                        class="option-item"
                      >
                        {{ option.key }}. {{ option.content }}
                      </el-radio>
                    </el-radio-group>

                    <el-checkbox-group
                      v-else
                      v-model="question.answer"
                      class="option-list"
                    >
                      <el-checkbox
                        v-for="option in question.options"
                        :key="option.key"
                        :label="option.key"
                        class="option-item"
                      >
                        {{ option.key }}. {{ option.content }}
                      </el-checkbox>
                    </el-checkbox-group>
                  </template>

                  <!-- 判断题 -->
                  <el-radio-group
                    v-else-if="question.type === '判断题'"
                    v-model="question.answer"
                    class="option-list"
                  >
                    <el-radio label="true">正确</el-radio>
                    <el-radio label="false">错误</el-radio>
                  </el-radio-group>

                  <!-- 填空题 -->
                  <template v-else-if="question.type === '填空题'">
                    <div
                      v-for="(blank, index) in question.blanks"
                      :key="index"
                      class="blank-item"
                    >
                      <span class="blank-number">{{ index + 1 }}.</span>
                      <el-input
                        v-model="question.answer[index]"
                        placeholder="请填写答案"
                      />
                    </div>
                  </template>

                  <!-- 简答题 -->
                  <template v-else-if="question.type === '简答题'">
                    <el-input
                      v-model="question.answer"
                      type="textarea"
                      :rows="6"
                      placeholder="请输入答案"
                    />
                  </template>
                </div>
              </div>

              <div class="question-footer">
                <el-button
                  v-if="question.id !== questions[0].id"
                  @click="navigateQuestion('prev')"
                >
                  上一题
                </el-button>
                <el-button
                  v-if="question.id !== questions[questions.length - 1].id"
                  type="primary"
                  @click="navigateQuestion('next')"
                >
                  下一题
                </el-button>
              </div>
            </div>
          </div>
        </el-col>

        <el-col :span="6">
          <div class="exam-sidebar">
            <el-card class="answer-card">
              <template #header>
                <div class="card-header">
                  <span>答题卡</span>
                  <el-tag>{{ answeredCount }}/{{ questions.length }}</el-tag>
                </div>
              </template>

              <div class="question-grid">
                <div
                  v-for="question in questions"
                  :key="question.id"
                  class="question-item"
                  :class="{
                    'answered': isQuestionAnswered(question),
                    'current': currentQuestion.id === question.id
                  }"
                  @click="jumpToQuestion(question)"
                >
                  {{ question.number }}
                </div>
              </div>

              <div class="action-bar">
                <el-button type="warning" @click="showSubmitConfirm">交卷</el-button>
              </div>
            </el-card>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 交卷确认对话框 -->
    <el-dialog
      v-model="submitDialogVisible"
      title="确认交卷"
      width="30%"
    >
      <div class="submit-confirm">
        <p>您还有 <span class="warning">{{ unansweredCount }}</span> 道题目未作答，确定要交卷吗？</p>
        <div class="time-info">
          剩余时间：{{ formatTime(timeRemaining) }}
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="submitDialogVisible = false">继续答题</el-button>
          <el-button type="primary" @click="submitExam">确认交卷</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { sanitizeHTML } from '@/utils/sanitize'

export default defineComponent({
  name: 'StudentExam',
  setup() {
    const examInfo = ref({
      name: '2024年春季计算机基础期末考试',
      totalScore: 100,
      duration: 120,
      questionCount: 50
    })

    const questions = ref([
      {
        id: '1',
        number: 1,
        type: '单选题',
        content: '以下哪个不是操作系统的基本功能？',
        options: [
          { key: 'A', content: '进程管理' },
          { key: 'B', content: '内存管理' },
          { key: 'C', content: '文件管理' },
          { key: 'D', content: '游戏管理' }
        ],
        score: 2,
        answer: ''
      },
      {
        id: '2',
        number: 2,
        type: '多选题',
        content: '以下哪些是常见的网络协议？',
        options: [
          { key: 'A', content: 'HTTP' },
          { key: 'B', content: 'FTP' },
          { key: 'C', content: 'SMTP' },
          { key: 'D', content: 'XYZ' }
        ],
        score: 4,
        answer: []
      },
      {
        id: '3',
        number: 3,
        type: '判断题',
        content: 'CPU是计算机的大脑，负责处理数据和控制其他硬件设备。',
        score: 2,
        answer: ''
      },
      {
        id: '4',
        number: 4,
        type: '填空题',
        content: '计算机网络按照覆盖范围可以分为____、____和____。',
        blanks: [1, 2, 3],
        score: 6,
        answer: []
      },
      {
        id: '5',
        number: 5,
        type: '简答题',
        content: '请简述计算机操作系统的主要功能。',
        score: 10,
        answer: ''
      }
    ])

    const currentQuestion = ref(questions.value[0])
    const timeRemaining = ref(examInfo.value.duration * 60) // 转换为秒
    const submitDialogVisible = ref(false)

    const timer = ref<number | null>(null)

    const startTimer = () => {
      timer.value = window.setInterval(() => {
        if (timeRemaining.value > 0) {
          timeRemaining.value--
        } else {
          clearInterval(timer.value!)
          submitExam()
        }
      }, 1000)
    }

    onMounted(() => {
      startTimer()
      // 添加页面关闭提醒
      window.addEventListener('beforeunload', beforeUnloadHandler)
    })

    onBeforeUnmount(() => {
      if (timer.value) {
        clearInterval(timer.value)
      }
      window.removeEventListener('beforeunload', beforeUnloadHandler)
    })

    const beforeUnloadHandler = (e: BeforeUnloadEvent) => {
      e.preventDefault()
      e.returnValue = ''
    }

    const formatTime = (seconds: number) => {
      const hours = Math.floor(seconds / 3600)
      const minutes = Math.floor((seconds % 3600) / 60)
      const remainingSeconds = seconds % 60
      return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
    }

    const answeredCount = computed(() => {
      return questions.value.filter(q => isQuestionAnswered(q)).length
    })

    const unansweredCount = computed(() => {
      return questions.value.length - answeredCount.value
    })

    const isQuestionAnswered = (question: any) => {
      if (Array.isArray(question.answer)) {
        return question.answer.length > 0
      }
      return question.answer !== ''
    }

    const navigateQuestion = (direction: 'prev' | 'next') => {
      const currentIndex = questions.value.findIndex(q => q.id === currentQuestion.value.id)
      const targetIndex = direction === 'prev' ? currentIndex - 1 : currentIndex + 1
      if (targetIndex >= 0 && targetIndex < questions.value.length) {
        currentQuestion.value = questions.value[targetIndex]
        scrollToQuestion(currentQuestion.value.id)
      }
    }

    const jumpToQuestion = (question: any) => {
      currentQuestion.value = question
      scrollToQuestion(question.id)
    }

    const scrollToQuestion = (questionId: string) => {
      const element = document.getElementById(`question-${questionId}`)
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' })
      }
    }

    const showSubmitConfirm = () => {
      submitDialogVisible.value = true
    }

    const submitExam = () => {
      console.log('提交试卷')
      // 这里将实现试卷提交逻辑
    }

    return {
      examInfo,
      questions,
      currentQuestion,
      timeRemaining,
      submitDialogVisible,
      answeredCount,
      unansweredCount,
      formatTime,
      isQuestionAnswered,
      navigateQuestion,
      jumpToQuestion,
      showSubmitConfirm,
      submitExam,
      sanitizeHTML
    }
  }
})
</script>

<style lang="scss" scoped>
.student-exam {
  min-height: 100vh;
  background-color: #f5f7fa;
  padding: 20px;

  .exam-header {
    background-color: #fff;
    padding: 20px;
    border-radius: 4px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;

    .exam-info {
      h1 {
        margin: 0 0 10px 0;
        color: #303133;
      }

      .exam-meta {
        display: flex;
        gap: 10px;
      }
    }

    .exam-timer {
      text-align: center;

      .timer-label {
        color: #909399;
        margin-bottom: 5px;
      }

      .timer-value {
        font-size: 24px;
        font-weight: bold;
        color: #409EFF;

        &.warning {
          color: #E6A23C;
        }
      }
    }
  }

  .exam-content {
    .question-area {
      .question-card {
        background-color: #fff;
        border-radius: 4px;
        box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        padding: 20px;

        &.current {
          border: 2px solid #409EFF;
        }

        .question-header {
          margin-bottom: 15px;
          display: flex;
          gap: 15px;
          align-items: center;

          .question-number {
            font-weight: bold;
            color: #303133;
          }

          .question-type {
            color: #909399;
          }

          .question-score {
            color: #F56C6C;
          }
        }

        .question-content {
          .question-text {
            margin-bottom: 20px;
            color: #303133;
          }

          .answer-area {
            .option-list {
              display: flex;
              flex-direction: column;
              gap: 10px;

              .option-item {
                margin: 0;
              }
            }

            .blank-item {
              display: flex;
              align-items: center;
              gap: 10px;
              margin-bottom: 10px;

              .blank-number {
                color: #909399;
              }
            }
          }
        }

        .question-footer {
          margin-top: 20px;
          display: flex;
          justify-content: space-between;
        }
      }
    }

    .exam-sidebar {
      position: sticky;
      top: 20px;

      .answer-card {
        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .question-grid {
          display: grid;
          grid-template-columns: repeat(5, 1fr);
          gap: 10px;
          margin-bottom: 20px;

          .question-item {
            width: 100%;
            aspect-ratio: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            background-color: #f5f7fa;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.3s;

            &:hover {
              background-color: #ecf5ff;
            }

            &.answered {
              background-color: #67C23A;
              color: #fff;
            }

            &.current {
              border: 2px solid #409EFF;
            }
          }
        }

        .action-bar {
          display: flex;
          justify-content: center;
        }
      }
    }
  }

  .submit-confirm {
    text-align: center;

    p {
      margin-bottom: 15px;

      .warning {
        color: #E6A23C;
        font-weight: bold;
      }
    }

    .time-info {
      color: #909399;
    }
  }
}
</style>