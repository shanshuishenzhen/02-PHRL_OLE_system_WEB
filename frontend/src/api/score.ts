import axios from 'axios';
import { getToken } from './auth';

const API_BASE = '/api/score-management';

// Simplified interface for a Score Sheet
export interface ScoreSheet {
  id: number;
  exam: { id: number; name: string };
  exam_record: { id: number; student: { id: number; username: string; } };
  status: string;
  total_score: number;
  is_passed: boolean;
  marked_at: string | null;
}

export const getScoreSheets = async (filters: Record<string, any> = {}): Promise<ScoreSheet[]> => {
  const response = await axios.get<ScoreSheet[]>(`${API_BASE}/score-sheets/`, {
    headers: {
      Authorization: `Bearer ${getToken()}`
    },
    params: filters
  });
  return response.data;
};

export const exportScores = async (filters: Record<string, any> = {}): Promise<Blob> => {
    const response = await axios.get(`${API_BASE}/score-sheets/export_scores/`, {
        headers: {
            Authorization: `Bearer ${getToken()}`
        },
        params: filters,
        responseType: 'blob'
    });
    return response.data;
};
