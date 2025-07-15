import axios from 'axios'
import { getToken } from './auth'

const API_BASE = '/api/exam'

interface ExamData {
  id: number
  questions: Array<{
    id: number
    text: string
    options: string[]
  }>
  duration: number
}

interface SubmitData {
  answers: Record<number, string>
}

interface MonitorData {
  status: 'active' | 'paused' | 'finished'
  remaining_time: number
  is_cheating: boolean
}

interface ExamListItem {
  id: number
  name: string
  start_time: string
  end_time: string
  status: 'pending' | 'ongoing' | 'finished'
}

export const getCurrentExam = async (): Promise<ExamData> => {
  const response = await axios.get<ExamData>(`${API_BASE}/current/`, {
    headers: {
      Authorization: `Bearer ${getToken()}`
    }
  })
  return response.data
}

export const submitExam = async (answers: SubmitData): Promise<void> => {
  await axios.post(`${API_BASE}/submit/`, answers, {
    headers: {
      Authorization: `Bearer ${getToken()}`
    }
  })
}

export const monitorExam = async (): Promise<MonitorData> => {
  const response = await axios.get<MonitorData>(`${API_BASE}/monitor/`, {
    headers: {
      Authorization: `Bearer ${getToken()}`
    }
  })
  return response.data
}

export const startExam = async (examId: number): Promise<void> => {
  await axios.post(`${API_BASE}/start/`, { exam_id: examId }, {
    headers: {
      Authorization: `Bearer ${getToken()}`
    }
  })
}

export const endExam = async (examId: number): Promise<void> => {
  await axios.post(`${API_BASE}/end/`, { exam_id: examId }, {
    headers: {
      Authorization: `Bearer ${getToken()}`
    }
  })
}

export const listExams = async (): Promise<ExamListItem[]> => {
  const response = await axios.get<ExamListItem[]>(`${API_BASE}/list/`, {
    headers: {
      Authorization: `Bearer ${getToken()}`
    }
  })
  return response.data
}

export const simulateExamStart = (params: {
  subject: string
  duration: number
}) => {
  return request({
    url: '/exam/simulate-start',
    method: 'POST',
    data: params
  })
}