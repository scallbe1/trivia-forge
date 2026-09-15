import type { AdminQuestion, Category, Game, GradeResult, MediaAsset, Stats } from './types'

async function json<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...(options?.headers || {}) },
    ...options
  })
  if (!response.ok) throw new Error(await response.text())
  return response.json() as Promise<T>
}

export const api = {
  stats: () => json<Stats>('/api/stats/summary'),
  categories: () => json<Category[]>('/api/categories'),
  questions: () => json<AdminQuestion[]>('/api/questions?limit=500'),
  createQuestion: (payload: unknown) => json<AdminQuestion>('/api/questions', { method: 'POST', body: JSON.stringify(payload) }),
  createGame: (questionCount = 10) =>
    json<Game>('/api/games', {
      method: 'POST',
      body: JSON.stringify({ question_count: questionCount, canadian_target: 0.15 })
    }),
  answer: (gameId: number, questionId: number, answers: Record<string, string>) =>
    json<GradeResult>(`/api/games/${gameId}/answer`, {
      method: 'POST',
      body: JSON.stringify({ question_id: questionId, answers })
    }),
  async uploadMedia(file: File): Promise<MediaAsset> {
    const form = new FormData()
    form.append('file', file)
    const response = await fetch('/api/media', { method: 'POST', body: form })
    if (!response.ok) throw new Error(await response.text())
    return response.json()
  },
  clipAudio: (mediaId: number, start_seconds: number, duration_seconds: number) =>
    json<MediaAsset>(`/api/media/${mediaId}/clip`, {
      method: 'POST',
      body: JSON.stringify({ start_seconds, duration_seconds, normalize: true, fade: true })
    }),
  async attachMedia(mediaId: number, questionId: number): Promise<void> {
    const response = await fetch(`/api/media/${mediaId}/attach/${questionId}`, { method: 'POST' })
    if (!response.ok) throw new Error(await response.text())
  }
}
