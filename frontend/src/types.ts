export type MediaAsset = {
  id: number
  media_type: string
  role: string
  path: string
  mime_type?: string | null
  width?: number | null
  height?: number | null
  duration_seconds?: number | null
  title?: string | null
  description?: string | null
}

export type AnswerSlot = { key: string; label: string; points: number }
export type Category = { id: number; parent_id?: number | null; name: string; slug: string; description?: string | null; sort_order: number; active: boolean }
export type Answer = { id: number; answer_key: string; answer_text: string; answer_type: string; points: number; required: boolean }
export type QuestionMedia = { id: number; media_asset_id: number; display_order: number; asset: MediaAsset }
export type AdminQuestion = {
  id: number
  primary_category_id?: number | null
  question_type: string
  prompt: string
  explanation?: string | null
  difficulty: number
  obscurity: number
  canadian_relevance: number
  status: string
  answers: Answer[]
  media_links: QuestionMedia[]
}

export type PublicQuestion = {
  id: number
  question_type: string
  prompt: string
  prompt_secondary?: string | null
  difficulty: number
  canadian_relevance: number
  media: MediaAsset[]
  answer_slots: AnswerSlot[]
}

export type Game = {
  id: number
  game_type: string
  score: number
  max_score: number
  question_count: number
  questions: PublicQuestion[]
}

export type GradeResult = {
  correct: boolean
  points_awarded: number
  points_available: number
  canonical_answers: Record<string, string>
  explanation?: string | null
  interesting_fact?: string | null
}

export type Stats = {
  questions: number
  categories: number
  media_assets: number
  attempts: number
  by_type: Record<string, number>
}
