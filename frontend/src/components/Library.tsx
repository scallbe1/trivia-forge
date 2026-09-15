import { useEffect, useState } from 'react'
import { api } from '../api'
import type { AdminQuestion, Category } from '../types'

const questionTypes = [
  'text', 'image_person', 'image_object', 'image_place', 'image_concept',
  'audio_artist', 'audio_title', 'audio_artist_title', 'multiple_choice', 'connection', 'ordering'
]

export function Library() {
  const [questions, setQuestions] = useState<AdminQuestion[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [selected, setSelected] = useState<AdminQuestion | null>(null)
  const [prompt, setPrompt] = useState('')
  const [answer, setAnswer] = useState('')
  const [type, setType] = useState('text')
  const [categoryId, setCategoryId] = useState<number | ''>('')
  const [difficulty, setDifficulty] = useState(5)
  const [canadian, setCanadian] = useState(0)
  const [file, setFile] = useState<File | null>(null)
  const [clipStart, setClipStart] = useState(30)
  const [clipDuration, setClipDuration] = useState(12)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')

  async function refresh() {
    const [q, c] = await Promise.all([api.questions(), api.categories()])
    setQuestions(q)
    setCategories(c)
    if (selected) setSelected(q.find(item => item.id === selected.id) || null)
  }

  useEffect(() => { refresh().catch(err => setMessage(String(err))) }, [])

  async function createQuestion(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true); setMessage('')
    try {
      await api.createQuestion({
        primary_category_id: categoryId || null,
        question_type: type,
        prompt,
        difficulty,
        obscurity: difficulty,
        canadian_relevance: canadian,
        status: 'active',
        answers: [{ answer_key: 'main', answer_text: answer, answer_type: 'canonical', points: 1 }]
      })
      setPrompt(''); setAnswer('')
      await refresh()
      setMessage('Question created.')
    } catch (err) { setMessage(String(err)) }
    finally { setBusy(false) }
  }

  async function uploadAndAttach() {
    if (!selected || !file) return
    setBusy(true); setMessage('')
    try {
      const uploaded = await api.uploadMedia(file)
      const attachAsset = uploaded.media_type === 'audio'
        ? await api.clipAudio(uploaded.id, clipStart, clipDuration)
        : uploaded
      await api.attachMedia(attachAsset.id, selected.id)
      setFile(null)
      await refresh()
      setMessage(uploaded.media_type === 'audio' ? 'Audio uploaded, clipped and attached.' : 'Media attached.')
    } catch (err) { setMessage(String(err)) }
    finally { setBusy(false) }
  }

  return (
    <div className="library-grid">
      <section className="panel">
        <h2>Add question</h2>
        <form onSubmit={createQuestion}>
          <label>Question type<select value={type} onChange={e => setType(e.target.value)}>{questionTypes.map(v => <option key={v}>{v}</option>)}</select></label>
          <label>Category<select value={categoryId} onChange={e => setCategoryId(e.target.value ? Number(e.target.value) : '')}><option value="">Uncategorized</option>{categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label>
          <label>Prompt<textarea rows={4} value={prompt} onChange={e => setPrompt(e.target.value)} required /></label>
          <label>Canonical answer<input value={answer} onChange={e => setAnswer(e.target.value)} required /></label>
          <div className="two-col">
            <label>Difficulty<input type="number" min="1" max="10" step="0.5" value={difficulty} onChange={e => setDifficulty(Number(e.target.value))} /></label>
            <label>Canadian relevance<input type="number" min="0" max="1" step="0.1" value={canadian} onChange={e => setCanadian(Number(e.target.value))} /></label>
          </div>
          <button disabled={busy}>Create question</button>
        </form>
        {message && <p className="notice">{message}</p>}
      </section>

      <section className="panel question-library">
        <div className="panel-heading"><h2>Question library</h2><span>{questions.length}</span></div>
        <div className="question-list">
          {questions.map(q => (
            <button key={q.id} className={`question-row ${selected?.id === q.id ? 'selected' : ''}`} onClick={() => setSelected(q)}>
              <span><b>#{q.id}</b> {q.prompt}</span>
              <small>{q.question_type.replaceAll('_', ' ')} · D{q.difficulty}</small>
            </button>
          ))}
        </div>
      </section>

      {selected && (
        <section className="panel selected-question">
          <h2>Question #{selected.id}</h2>
          <p>{selected.prompt}</p>
          <p><b>Answer:</b> {selected.answers.filter(a => a.answer_type === 'canonical').map(a => a.answer_text).join(' / ')}</p>
          <div className="media-stack">
            {selected.media_links.map(link => link.asset.media_type === 'image'
              ? <img key={link.id} src={`/media/${link.asset.path}`} alt="Question clue" />
              : link.asset.media_type === 'audio'
                ? <audio key={link.id} src={`/media/${link.asset.path}`} controls />
                : null)}
          </div>
          <h3>Attach image or audio</h3>
          <input type="file" accept="image/*,audio/*" onChange={e => setFile(e.target.files?.[0] || null)} />
          {file?.type.startsWith('audio/') && (
            <div className="two-col">
              <label>Clip start (seconds)<input type="number" min="0" step="1" value={clipStart} onChange={e => setClipStart(Number(e.target.value))} /></label>
              <label>Clip length<input type="number" min="5" max="60" step="1" value={clipDuration} onChange={e => setClipDuration(Number(e.target.value))} /></label>
            </div>
          )}
          <button disabled={!file || busy} onClick={uploadAndAttach}>Upload & attach</button>
        </section>
      )}
    </div>
  )
}
