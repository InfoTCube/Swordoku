import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

type Mode = 'casual' | 'ranked'
type Difficulty = 'easy' | 'medium' | 'hard'

interface LobbyOut {
  code: string
}

export default function Home() {
  const navigate = useNavigate()

  const [mode, setMode] = useState<Mode>('casual')
  const [difficulty, setDifficulty] = useState<Difficulty>('medium')
  const [createLoading, setCreateLoading] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)

  const [joinCode, setJoinCode] = useState('')
  const [joinError, setJoinError] = useState<string | null>(null)

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setCreateError(null)
    setCreateLoading(true)
    try {
      const res = await api.post<LobbyOut>('/lobbies', { mode, difficulty })
      navigate(`/lobby/${res.data.code}`)
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setCreateError(typeof detail === 'string' ? detail : 'Failed to create lobby.')
    } finally {
      setCreateLoading(false)
    }
  }

  function handleJoin(e: React.FormEvent) {
    e.preventDefault()
    setJoinError(null)
    const raw = joinCode.trim()
    if (!raw) {
      setJoinError('Enter an invite code or URL.')
      return
    }
    // Accept either a bare code or a full URL ending in /lobby/<code>
    const match = raw.match(/(?:\/lobby\/)?([A-Za-z0-9]+)$/)
    const code = match ? match[1] : raw
    navigate(`/lobby/${code}`)
  }

  return (
    <div className="home-container">
      <section className="home-card">
        <h2 className="home-card-title">Create a lobby</h2>
        <form className="home-form" onSubmit={handleCreate}>
          {createError && <p className="home-error">{createError}</p>}

          <fieldset className="home-fieldset">
            <legend className="home-legend">Mode</legend>
            <div className="home-radio-group">
              {(['casual', 'ranked'] as Mode[]).map((m) => (
                <label key={m} className="home-radio-label">
                  <input
                    type="radio"
                    name="mode"
                    value={m}
                    checked={mode === m}
                    onChange={() => setMode(m)}
                    disabled={createLoading}
                  />
                  {m.charAt(0).toUpperCase() + m.slice(1)}
                </label>
              ))}
            </div>
          </fieldset>

          <fieldset className="home-fieldset">
            <legend className="home-legend">Difficulty</legend>
            <div className="home-radio-group">
              {(['easy', 'medium', 'hard'] as Difficulty[]).map((d) => (
                <label key={d} className="home-radio-label">
                  <input
                    type="radio"
                    name="difficulty"
                    value={d}
                    checked={difficulty === d}
                    onChange={() => setDifficulty(d)}
                    disabled={createLoading}
                  />
                  {d.charAt(0).toUpperCase() + d.slice(1)}
                </label>
              ))}
            </div>
          </fieldset>

          <button className="home-btn" type="submit" disabled={createLoading}>
            {createLoading ? 'Creating…' : 'Create lobby'}
          </button>
        </form>
      </section>

      <section className="home-card">
        <h2 className="home-card-title">Join a lobby</h2>
        <form className="home-form" onSubmit={handleJoin}>
          {joinError && <p className="home-error">{joinError}</p>}

          <label className="home-label">
            Invite code or URL
            <input
              className="home-input"
              type="text"
              placeholder="e.g. ABC123 or http://…/lobby/ABC123"
              value={joinCode}
              onChange={(e) => setJoinCode(e.target.value)}
            />
          </label>

          <button className="home-btn" type="submit">
            Join lobby
          </button>
        </form>
      </section>
    </div>
  )
}
