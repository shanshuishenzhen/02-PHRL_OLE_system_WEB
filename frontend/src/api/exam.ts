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

export const getCurrentExam = async (): Promise<ExamData> => {
  const response = await axios.get(`${API_BASE}/current/`, {
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
  const response = await axios.get(`${API_BASE}/monitor/`, {
    headers: {
      Authorization: `Bearer ${getToken()}`
    }
  })
  return response.data
}