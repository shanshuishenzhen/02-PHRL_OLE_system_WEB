export interface ExamSimulationState {
  status: 'idle' | 'loading' | 'error';
  paperData: {
    subject: string;
    questions: Question[];
  } | null;
  error: string;
}

export interface MonitoringEvent {
  timestamp: string;
  type: 'face_detection' | 'tab_switch' | 'objection';
  severity: 'high' | 'medium' | 'low';
  screenshot?: string;
}