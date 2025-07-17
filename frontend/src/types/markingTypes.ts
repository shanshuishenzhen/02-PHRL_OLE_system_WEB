export interface ScoringResult {
  paperId: string;
  score: number;
  anomalies: {
    type: 'handwriting' | 'multiple_choice';
    confidence: number;
  }[];
}

type BatchStatus = {
  progress: number;
  failedItems: Array<{
    fileName: string;
    errorCode: string;
  }>;
};