import api from './index'

export interface CognitiveAssessment {
  id: string
  assessment_type: string
  overall_score: number
  risk_level: string
  language_score: number
  memory_score: number
  executive_function_score: number
  attention_score: number
  confidence: number
  recommendations: string[]
  created_at: string
}

export interface TrainingSession {
  id: string
  exercise_type: string
  difficulty: string
  score: number
  accuracy: number
  duration_seconds: number
  created_at: string
}

export interface ProgressMetrics {
  total_sessions: number
  average_score: number
  consistency_score: number
  strengths: string[]
  weaknesses: string[]
  performance_trend: Array<{ date: string; score: number }>
}

export interface ExerciseData {
  exercise_type: string
  difficulty: string
  content: any
}

export const cognitiveApi = {
  analyzeText: (text: string) => api.post('/cognitive/analyze-text', { text }),
  analyzeSpeech: (formData: FormData) => api.post('/cognitive/analyze-speech', formData),
  generateExercise: (exerciseType: string, difficulty: string = 'intermediate') =>
    api.post('/cognitive/training/generate', { exercise_type: exerciseType, difficulty }),
  submitTraining: (data: { exercise_type: string; difficulty: string; score?: number; accuracy?: number; duration_seconds?: number; details?: any }) =>
    api.post('/cognitive/training/submit', data),
  getProgress: () => api.get('/cognitive/training/progress'),
  getAssessments: (limit: number = 10) => api.get(`/cognitive/assessments?limit=${limit}`),
}
