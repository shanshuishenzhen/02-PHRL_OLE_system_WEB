import axios from 'axios';
import { getToken } from './auth';

const API_BASE = '/api/logs';

export interface Log {
    id: number;
    user: { id: number; username: string; } | null;
    action_time: string;
    action_type: string;
    action_type_display: string;
    target_model: string;
    target_id: number;
    description: string;
    status: string;
    ip_address: string;
    user_agent: string;
}

export const getLogs = async (filters: Record<string, any> = {}): Promise<Log[]> => {
    const response = await axios.get<Log[]>(`${API_BASE}/`, {
        headers: {
            Authorization: `Bearer ${getToken()}`
        },
        params: filters
    });
    return response.data;
};

export const exportLogs = async (filters: Record<string, any> = {}): Promise<Blob> => {
    const response = await axios.get(`${API_BASE}/export_logs/`, {
        headers: {
            Authorization: `Bearer ${getToken()}`
        },
        params: filters,
        responseType: 'blob'
    });
    return response.data;
};
