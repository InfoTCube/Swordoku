import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'

interface UserProfile {
  username: string
  elo_rating: number
  wins: number
  losses: number
}

interface MatchEntry {
  match_id: string
  ended_at: string | null
  mode: 'casual' | 'ranked'
  difficulty: string
  result: 'win' | 'loss' | 'draw'
  opponents: string[]
  elo_delta: number | null
  cells_correct: number
  mistakes: number
}

const PAGE_SIZE = 20

export default function Profile() {
  const { username } = useParams<{ username: string }>()
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [matches, setMatches] = useState<MatchEntry[]>([])
  const [offset, setOffset] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)

  useEffect(() => {
    if (!username) return
    setLoading(true)
    setError(null)
    setMatches([])
    setOffset(0)
    setHasMore(true)

    Promise.all([
      api.get<UserProfile>(`/users/${username}`),
      api.get<MatchEntry[]>(`/users/${username}/matches`, { params: { limit: PAGE_SIZE, offset: 0 } }),
    ])
      .then(([profileRes, matchesRes]) => {
        setProfile(profileRes.data)
        setMatches(matchesRes.data)
        setOffset(matchesRes.data.length)
        setHasMore(matchesRes.data.length === PAGE_SIZE)
      })
      .catch(err => {
        const msg = err.response?.data?.detail ?? 'Failed to load profile'
        setError(typeof msg === 'string' ? msg : 'Failed to load profile')
      })
      .finally(() => setLoading(false))
  }, [username])

  const loadMore = useCallback(() => {
    if (!username || loadingMore) return
    setLoadingMore(true)
    api.get<MatchEntry[]>(`/users/${username}/matches`, { params: { limit: PAGE_SIZE, offset } })
      .then(res => {
        setMatches(prev => [...prev, ...res.data])
        setOffset(prev => prev + res.data.length)
        setHasMore(res.data.length === PAGE_SIZE)
      })
      .finally(() => setLoadingMore(false))
  }, [username, offset, loadingMore])

  if (loading) return <div className="profile-loading">Loading…</div>

  if (error) {
    return (
      <div className="profile-container">
        <div className="profile-error">{error}</div>
        <Link to="/" className="profile-back">← Back to home</Link>
      </div>
    )
  }

  if (!profile) return null

  const totalGames = profile.wins + profile.losses
  const winRate = totalGames > 0 ? Math.round((profile.wins / totalGames) * 100) : null

  return (
    <div className="profile-container">
      <div className="profile-card">
        <div className="profile-avatar">{profile.username[0].toUpperCase()}</div>
        <h1 className="profile-username">{profile.username}</h1>

        <div className="profile-stats">
          <div className="profile-stat">
            <span className="profile-stat-value">{profile.elo_rating}</span>
            <span className="profile-stat-label">ELO Rating</span>
          </div>
          <div className="profile-stat">
            <span className="profile-stat-value">{profile.wins}</span>
            <span className="profile-stat-label">Wins</span>
          </div>
          <div className="profile-stat">
            <span className="profile-stat-value">{profile.losses}</span>
            <span className="profile-stat-label">Losses</span>
          </div>
          {winRate !== null && (
            <div className="profile-stat">
              <span className="profile-stat-value">{winRate}%</span>
              <span className="profile-stat-label">Win Rate</span>
            </div>
          )}
        </div>
      </div>

      <div className="profile-history">
        <h2 className="profile-history-title">Match History</h2>
        {matches.length === 0 ? (
          <p className="profile-history-empty">No matches played yet.</p>
        ) : (
          <>
            <div className="profile-history-list">
              {matches.map(m => <MatchRow key={m.match_id} match={m} />)}
            </div>
            {hasMore && (
              <button
                className="profile-load-more"
                onClick={loadMore}
                disabled={loadingMore}
              >
                {loadingMore ? 'Loading…' : 'Load more'}
              </button>
            )}
          </>
        )}
      </div>
    </div>
  )
}

function MatchRow({ match: m }: { match: MatchEntry }) {
  const date = m.ended_at
    ? new Date(m.ended_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
    : '—'

  const eloDeltaStr =
    m.elo_delta !== null
      ? (m.elo_delta >= 0 ? `+${m.elo_delta}` : `${m.elo_delta}`)
      : null

  const opponentsStr = m.opponents.length > 0 ? m.opponents.join(', ') : '—'

  return (
    <div className={`profile-match profile-match--${m.result}`}>
      <span className={`profile-match-result profile-match-result--${m.result}`}>
        {m.result.toUpperCase()}
      </span>

      <div className="profile-match-info">
        <span className="profile-match-vs">vs {opponentsStr}</span>
        <span className="profile-match-meta">
          {m.difficulty} · {m.mode} · {m.cells_correct}/81 cells · {m.mistakes} mistakes
        </span>
      </div>

      <div className="profile-match-right">
        {eloDeltaStr && (
          <span className={`profile-match-elo profile-match-elo--${m.elo_delta! >= 0 ? 'positive' : 'negative'}`}>
            {eloDeltaStr}
          </span>
        )}
        <span className="profile-match-date">{date}</span>
      </div>
    </div>
  )
}
