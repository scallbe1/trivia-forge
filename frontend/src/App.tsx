import { useEffect, useState } from 'react'
import { api } from './api'
import { Practice } from './components/Practice'
import { Library } from './components/Library'
import type { Stats } from './types'

export default function App() {
  const [tab, setTab] = useState<'dashboard' | 'practice' | 'library'>('dashboard')
  const [stats, setStats] = useState<Stats | null>(null)

  useEffect(() => {
    api.stats().then(setStats).catch(() => setStats(null))
  }, [tab])

  return (
    <div className="shell">
      <header>
        <div>
          <div className="eyebrow">SELF-HOSTED MULTIMEDIA TRIVIA</div>
          <h1>Trivia Forge</h1>
        </div>
        <nav>
          <button className={tab === 'dashboard' ? 'active' : ''} onClick={() => setTab('dashboard')}>Dashboard</button>
          <button className={tab === 'practice' ? 'active' : ''} onClick={() => setTab('practice')}>Practice</button>
          <button className={tab === 'library' ? 'active' : ''} onClick={() => setTab('library')}>Library</button>
        </nav>
      </header>

      <main>
        {tab === 'dashboard' ? (
          <>
            <section className="hero">
              <h2>Build a knowledge base that feels like real pub trivia.</h2>
              <p>Text, image and audio recognition are first-class question types. The starter database is deliberately tiny; the hourly ingestion pipeline comes next.</p>
              <button onClick={() => setTab('practice')}>Start practice</button>
            </section>
            <section className="stats-grid">
              <Stat label="Questions" value={stats?.questions ?? '—'} />
              <Stat label="Categories" value={stats?.categories ?? '—'} />
              <Stat label="Media" value={stats?.media_assets ?? '—'} />
              <Stat label="Attempts" value={stats?.attempts ?? '—'} />
            </section>
            <section className="panel">
              <h2>Question formats</h2>
              <div className="type-list">
                {stats && Object.entries(stats.by_type).map(([type, count]) => (
                  <div key={type}><span>{type.replaceAll('_', ' ')}</span><b>{count}</b></div>
                ))}
              </div>
            </section>
          </>
        ) : tab === 'practice' ? <Practice /> : <Library />}
      </main>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return <div className="stat"><span>{label}</span><strong>{value}</strong></div>
}
