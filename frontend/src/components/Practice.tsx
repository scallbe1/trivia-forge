import { useState } from 'react'
import { api } from '../api'
import type { Game } from '../types'
import { QuestionCard } from './QuestionCard'

export function Practice() {
  const [game, setGame] = useState<Game | null>(null)
  const [index, setIndex] = useState(0)
  const [finished, setFinished] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function start(count: number) {
    setLoading(true)
    setError('')
    try {
      const created = await api.createGame(count)
      setGame(created)
      setIndex(0)
      setFinished(false)
    } catch (err) {
      setError(String(err))
    } finally {
      setLoading(false)
    }
  }

  if (!game) {
    return (
      <section className="panel">
        <h2>Practice</h2>
        <p>Balanced general knowledge with a Canadian weighting and support for text, image and audio questions.</p>
        <div className="button-row">
          {[10, 25, 50].map(n => <button key={n} disabled={loading} onClick={() => start(n)}>{n} questions</button>)}
        </div>
        {error && <p className="error">{error}</p>}
      </section>
    )
  }

  if (finished) {
    return (
      <section className="panel">
        <h2>Session complete</h2>
        <p>Refresh the dashboard to see updated attempt totals.</p>
        <button onClick={() => setGame(null)}>Start another</button>
      </section>
    )
  }

  const question = game.questions[index]
  return (
    <>
      <div className="progress">Question {index + 1} of {game.questions.length}</div>
      <QuestionCard
        key={question.id}
        question={question}
        isLast={index === game.questions.length - 1}
        onSubmit={answers => api.answer(game.id, question.id, answers)}
        onNext={() => {
          if (index === game.questions.length - 1) setFinished(true)
          else setIndex(i => i + 1)
        }}
      />
    </>
  )
}
