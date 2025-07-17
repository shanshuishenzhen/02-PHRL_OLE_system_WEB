export interface ExamPaperResponse {
  code: number;
  data: {
    examId: string;
    questions: Array<{
      id: string;
      stem: string;
      options: Record<string, string>;
    }>;
    duration: number;
  };
  timestamp: string;
}

export interface MonitoringEventResponse {
  event_type: 'FACE_DETECTED' | 'TAB_SWITCH';
  screenshot_url: string;
  confidence: number;
}

export interface ScoringResultResponse {
  success: boolean;
  score_details: {
    total: number;
    sections: Array<{
      section_id: string;
      score: number;
      anomalies: string[];
    }>;
  };
  processing_time: number;
}


export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ErrorResponse {
  code: 'ERR_INVALID_INPUT' | 'ERR_SERVER_ERROR';
  message: string;
  details?: Record<string, string>;
}