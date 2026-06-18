import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../context/AuthContext'

type Mode = 'casual' | 'ranked'
type Difficulty = 'easy' | 'medium' | 'hard'

interface LobbyMember {
  user_id: string
  username: string
  joined_at: string
}

interface LobbyState {
  id: string
  code: string
  creator_id: string
  invite_url: string
  mode: Mode
  difficulty: Difficulty
  status: 'waiting' | 'active'
  players: LobbyMember[]
  match_id: string | null
  time_limit_min: number
  mistake_limit: number
}

const POLL_INTERVAL_MS = 2000

export default function Lobby() {
  const { code } = useParams<{ code: string }>()
  const navigate = useNavigate()
  const { currentUser } = useAuth()

  const [lobby, setLobby] = useState<LobbyState | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [startLoading, setStartLoading] = useState(false)
  const [startError, setStartError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const joinedRef = useRef(false)

  useEffect(() => {
    if (!code) return

    async function joinAndFetch() {
      try {
        if (!joinedRef.current) {
          joinedRef.current = true
          await api.post<LobbyState>(`/lobbies/${code}/join`)
        }
        const res = await api.get<LobbyState>(`/lobbies/${code}`)
        setLobby(res.data)
        setError(null)

        if (res.data.status === 'active' && res.data.match_id) {
          navigate(`/game/${res.data.match_id}`)
        }
      } catch (err: unknown) {
        const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
        setError(typeof detail === 'string' ? detail : 'Failed to load lobby.')
      }
    }

    joinAndFetch()
    const timer = setInterval(async () => {
      try {
        const res = await api.get<LobbyState>(`/lobbies/${code}`)
        setLobby(res.data)
        setError(null)
        if (res.data.status === 'active' && res.data.match_id) {
          navigate(`/game/${res.data.match_id}`)
        }
      } catch {
        // keep last known state on transient poll failure
      }
    }, POLL_INTERVAL_MS)

    return () => clearInterval(timer)
  }, [code, navigate])

  async function handleStart() {
    if (!code) return
    setStartError(null)
    setStartLoading(true)
    try {
      const res = await api.post<{ match_id: string }>(`/lobbies/${code}/start`)
      navigate(`/game/${res.data.match_id}`)
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setStartError(typeof detail === 'string' ? detail : 'Failed to start game.')
    } finally {
      setStartLoading(false)
    }
  }

  async function handleCopyInvite() {
    if (!lobby) return
    try {
      await navigator.clipboard.writeText(lobby.invite_url)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // clipboard may be unavailable; show the URL as fallback
    }
  }

  if (error) {
    return (
      <div className="lobby-container">
        <p className="lobby-error">{error}</p>
      </div>
    )
  }

  if (!lobby) {
    return (
      <div className="lobby-container">
        <p className="lobby-loading">Joining lobby…</p>
      </div>
    )
  }

  const isCreator = currentUser?.id === lobby.creator_id
  const canStart = isCreator && lobby.players.length >= 2

  return (
    <div className="lobby-container">
      <div className="lobby-card">
        <h1 className="lobby-title">Waiting Room</h1>

        <div className="lobby-meta">
          <span className="lobby-badge">{lobby.mode}</span>
          <span className="lobby-badge">{lobby.difficulty}</span>
          <span className="lobby-badge">{lobby.time_limit_min} min</span>
          <span className="lobby-badge">{lobby.mistake_limit} mistakes</span>
          <span className="lobby-code">#{lobby.code}</span>
        </div>

        <section className="lobby-invite">
          <span className="lobby-invite-url">{lobby.invite_url}</span>
          <button className="lobby-copy-btn" onClick={handleCopyInvite}>
            {copied ? 'Copied!' : 'Copy link'}
          </button>
        </section>

        <section className="lobby-players">
          <h2 className="lobby-section-title">
            Players ({lobby.players.length} / 4)
          </h2>
          <ul className="lobby-player-list">
            {lobby.players.map((p) => (
              <li key={p.user_id} className="lobby-player-item">
                <span className="lobby-player-name">{p.username}</span>
                {p.user_id === lobby.creator_id && (
                  <span className="lobby-creator-badge">host</span>
                )}
              </li>
            ))}
          </ul>
          {lobby.players.length < 2 && (
            <p className="lobby-hint">Waiting for at least one more player…</p>
          )}
        </section>

        {isCreator && (
          <div className="lobby-start-section">
            {startError && <p className="lobby-error">{startError}</p>}
            <button
              className="lobby-start-btn"
              onClick={handleStart}
              disabled={!canStart || startLoading}
            >
              {startLoading ? 'Starting…' : 'Start game'}
            </button>
            {!canStart && !startLoading && (
              <p className="lobby-hint">Need at least 2 players to start.</p>
            )}
          </div>
        )}

        {!isCreator && (
          <p className="lobby-hint lobby-waiting-msg">Waiting for the host to start the game…</p>
        )}
      </div>
    </div>
  )
}
