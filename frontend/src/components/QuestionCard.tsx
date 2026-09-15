import { useMemo, useState } from 'react'
import type { GradeResult, PublicQuestion } from '../types'

type Props = {
  question: PublicQuestion
  onSubmit: (answers: Record<string, string>) => Promise<GradeResult>
  onNext: () => void
  isLast: boolean
}

export function QuestionCard({ question, onSubmit, onNext, isLast }: Props) {
  const initial = useMemo(
    () => Object.fromEntries(question.answer_slots.map(slot => [slot.key, ''])),
    [question]
  )
  const [answers, setAnswers] = useState<Record<string, string>>(initial)
  const [result, setResult] = useState<GradeResult | null>(null)
  const [busy, setBusy] = useState(false)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (result || busy) return
    setBusy(true)
    try {
      setResult(await onSubmit(answers))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="question-card">
      <div className="question-meta">
        <span>{question.question_type.replaceAll('_', ' ')}</span>
        <span>Difficulty {question.difficulty.toFixed(1)}</span>
        {question.canadian_relevance >= 0.5 && <span>Canada</span>}
      </div>

      <h2>{question.prompt}</h2>
      {question.prompt_secondary && <p className="secondary">{question.prompt_secondary}</p>}

      <div className="media-stack">
        {question.media.map(media =>
          media.media_type === 'image' ? (
            <img key={media.id} src={`/media/${media.path}`} alt="Trivia clue" />
          ) : media.media_type === 'audio' ? (
            <audio key={media.id} src={`/media/${media.path}`} controls preload="metadata" />
          ) : media.media_type === 'video' ? (
            <video key={media.id} src={`/media/${media.path}`} controls />
          ) : null
        )}
      </div>

      <form onSubmit={submit}>
        {question.answer_slots.map(slot => (
          <label key={slot.key}>
            {slot.label} {slot.points > 1 ? `(${slot.points} pts)` : ''}
            <input
              value={answers[slot.key] || ''}
              disabled={!!result}
              autoComplete="off"
              onChange={e => setAnswers(current => ({ ...current, [slot.key]: e.target.value }))}
            />
          </label>
        ))}
        {!result && <button disabled={busy}>{busy ? 'Checking…' : 'Submit answer'}</button>}
      </form>

      {result && (
        <div className={result.correct ? 'result correct' : 'result incorrect'}>
          <strong>{result.correct ? 'Correct' : 'Not quite'}</strong>
          <span>{result.points_awarded} / {result.points_available} points</span>
          <div className="canonical">
            {Object.entries(result.canonical_answers).map(([key, value]) => (
              <div key={key}><b>{key === 'main' ? 'Answer' : key.replaceAll('_', ' ')}:</b> {value}</div>
            ))}
          </div>
          {result.explanation && <p>{result.explanation}</p>}
          {result.interesting_fact && <p>{result.interesting_fact}</p>}
          <button onClick={onNext}>{isLast ? 'Finish' : 'Next question'}</button>
        </div>
      )}
    </section>
  )
}
