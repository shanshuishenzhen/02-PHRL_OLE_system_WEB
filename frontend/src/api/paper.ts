import axios from 'axios';
import { getToken } from './auth';

const API_BASE = '/api/paper-management';

// Define the interface for a Paper object based on the backend serializer
export interface Paper {
  id: number;
  title: string;
  description: string;
  subject: string;
  total_score: number;
  passing_score: number;
  duration: number;
  status: 'draft' | 'published' | 'archived';
  created_at: string;
  updated_at: string;
  published_at: string | null;
  created_by: number;
  template: number | null;
  questions: any[]; // You might want to define a proper interface for questions
}

export const getPapers = async (): Promise<Paper[]> => {
  const response = await axios.get<Paper[]>(`${API_BASE}/papers/`, {
    headers: {
      Authorization: `Bearer ${getToken()}`
    }
  });
  return response.data;
};

export const getPaper = async (id: number): Promise<Paper> => {
    const response = await axios.get<Paper>(`${API_BASE}/papers/${id}/`, {
      headers: {
        Authorization: `Bearer ${getToken()}`
      }
    });
    return response.data;
  };

export const exportExamPlans = async (): Promise<Blob> => {
    const response = await axios.get(`${API_BASE}/papers/export_exam_plans/`, {
        headers: {
            Authorization: `Bearer ${getToken()}`
        },
        responseType: 'blob'
    });
    return response.data;
};

export const importExamPlans = async (file: File): Promise<void> => {
    const formData = new FormData();
    formData.append('file', file);

    await axios.post(`${API_BASE}/papers/import_exam_plans/`, formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
            Authorization: `Bearer ${getToken()}`
        }
    });
};

export const createPaper = async (paperData: Partial<Paper>): Promise<Paper> => {
  const response = await axios.post<Paper>(`${API_BASE}/papers/`, paperData, {
    headers: {
      Authorization: `Bearer ${getToken()}`
    }
  });
  return response.data;
};

export const updatePaper = async (id: number, paperData: Partial<Paper>): Promise<Paper> => {
  const response = await axios.put<Paper>(`${API_BASE}/papers/${id}/`, paperData, {
    headers: {
      Authorization: `Bearer ${getToken()}`
    }
  });
  return response.data;
};

export const deletePaper = async (id: number): Promise<void> => {
  await axios.delete(`${API_BASE}/papers/${id}/`, {
    headers: {
      Authorization: `Bearer ${getToken()}`
    }
  });
};

export const publishPaper = async (id: number): Promise<Paper> => {
    const response = await axios.post<Paper>(`${API_BASE}/papers/${id}/publish/`, {}, {
      headers: {
        Authorization: `Bearer ${getToken()}`
      }
    });
    return response.data;
  };

  export const unpublishPaper = async (id: number): Promise<Paper> => {
    const response = await axios.post<Paper>(`${API_BASE}/papers/${id}/archive/`, {}, {
      headers: {
        Authorization: `Bearer ${getToken()}`
      }
    });
    return response.data;
  };
