<template>
  <div class="question-bank">
    <h1>试题库管理</h1>
    <div class="module-content">
      <el-card class="function-card">
        <template #header>
          <div class="card-header">
            <h3>试题列表</h3>
            <el-button type="primary" @click="addQuestion">添加试题</el-button>
          </div>
        </template>
        <el-table :data="questions" style="width: 100%">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="type" label="题型" width="100" />
          <el-table-column prop="subject" label="科目" width="120" />
          <el-table-column prop="content" label="题目内容" show-overflow-tooltip />
          <el-table-column prop="difficulty" label="难度" width="100" />
          <el-table-column label="操作" width="200">
            <template #default="scope">
              <el-button size="small" @click="editQuestion(scope.row)">编辑</el-button>
              <el-button size="small" type="danger" @click="deleteQuestion(scope.row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card class="function-card">
        <template #header>
          <div class="card-header">
            <h3>题库分类</h3>
            <el-button type="primary" @click="addCategory">添加分类</el-button>
          </div>
        </template>
        <el-tree
          :data="categories"
          :props="defaultProps"
          @node-click="handleNodeClick"
          default-expand-all
        />
      </el-card>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue'

export default defineComponent({
  name: 'QuestionBank',
  setup() {
    const questions = ref([
      { id: 1, type: '单选题', subject: '计算机基础', content: '以下哪个不是操作系统？', difficulty: '简单' },
      { id: 2, type: '多选题', subject: '网络原理', content: '以下哪些属于网络协议？', difficulty: '中等' },
      { id: 3, type: '判断题', subject: '数据结构', content: '队列是一种先进先出的数据结构', difficulty: '简单' }
    ])

    const categories = ref([
      {
        label: '计算机基础',
        children: [
          { label: '操作系统' },
          { label: '计算机网络' },
          { label: '数据结构' }
        ]
      },
      {
        label: '专业课程',
        children: [
          { label: '软件工程' },
          { label: '数据库原理' },
          { label: '人工智能' }
        ]
      }
    ])

    const defaultProps = {
      children: 'children',
      label: 'label'
    }

    const addQuestion = () => {
      console.log('添加试题')
    }

    const editQuestion = (question: any) => {
      console.log('编辑试题:', question)
    }

    const deleteQuestion = (question: any) => {
      console.log('删除试题:', question)
    }

    const addCategory = () => {
      console.log('添加分类')
    }

    const handleNodeClick = (data: any) => {
      console.log('选中分类:', data)
    }

    return {
      questions,
      categories,
      defaultProps,
      addQuestion,
      editQuestion,
      deleteQuestion,
      addCategory,
      handleNodeClick
    }
  }
})
</script>

<style lang="scss" scoped>
.question-bank {
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
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      h3 {
        margin: 0;
        color: #409EFF;
      }
    }
  }
}
</style>