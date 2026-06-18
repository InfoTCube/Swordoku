import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'

interface LeaderboardEntry {
  rank: number
  username: string
  elo_rating: number
  wins: number
  losses: number
}

const PAGE_SIZE = 50

export default function Leaderboard() {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([])
  const [offset, setOffset] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    api.get<LeaderboardEntry[]>('/leaderboard', { params: { limit: PAGE_SIZE, offset: 0 } })
      .then(res => {
        setEntries(res.data)
        setOffset(res.data.length)
        setHasMore(res.data.length === PAGE_SIZE)
      })
      .catch(err => {
        const msg = err.response?.data?.detail ?? 'Failed to load leaderboard'
        setError(typeof msg === 'string' ? msg : 'Failed to load leaderboard')
      })
      .finally(() => setLoading(false))
  }, [])

  const loadMore = useCallback(() => {
    if (loadingMore) return
    setLoadingMore(true)
    api.get<LeaderboardEntry[]>('/leaderboard', { params: { limit: PAGE_SIZE, offset } })
      .then(res => {
        setEntries(prev => [...prev, ...res.data])
        setOffset(prev => prev + res.data.length)
        setHasMore(res.data.length === PAGE_SIZE)
      })
      .finally(() => setLoadingMore(false))
  }, [offset, loadingMore])

  return (
    <div className="lb-container">
      <h1 className="lb-title">Leaderboard</h1>

      {error && <div className="lb-error">{error}</div>}

      {loading ? (
        <div className="lb-loading">Loading…</div>
      ) : entries.length === 0 ? (
        <p className="lb-empty">No players yet.</p>
      ) : (
        <>
          <div className="lb-table-wrap">
            <table className="lb-table">
              <thead>
                <tr>
                  <th className="lb-th lb-th--rank">#</th>
                  <th className="lb-th lb-th--name">Player</th>
                  <th className="lb-th lb-th--elo">ELO</th>
                  <th className="lb-th lb-th--w">W</th>
                  <th className="lb-th lb-th--l">L</th>
                  <th className="lb-th lb-th--wl">W/L %</th>
                </tr>
              </thead>
              <tbody>
                {entries.map(e => <LeaderboardRow key={e.username} entry={e} />)}
              </tbody>
            </table>
          </div>

          {hasMore && (
            <button
              className="lb-load-more"
              onClick={loadMore}
              disabled={loadingMore}
            >
              {loadingMore ? 'Loading…' : 'Load more'}
            </button>
          )}
        </>
      )}
    </div>
  )
}

function LeaderboardRow({ entry: e }: { entry: LeaderboardEntry }) {
  const totalGames = e.wins + e.losses
  const winRate = totalGames > 0 ? Math.round((e.wins / totalGames) * 100) : null

  const rankClass =
    e.rank === 1 ? 'lb-rank lb-rank--gold'
    : e.rank === 2 ? 'lb-rank lb-rank--silver'
    : e.rank === 3 ? 'lb-rank lb-rank--bronze'
    : 'lb-rank'

  return (
    <tr className="lb-row">
      <td className="lb-td lb-td--rank">
        <span className={rankClass}>{e.rank}</span>
      </td>
      <td className="lb-td lb-td--name">
        <Link to={`/profile/${e.username}`} className="lb-player-link">
          {e.username}
        </Link>
      </td>
      <td className="lb-td lb-td--elo">{e.elo_rating}</td>
      <td className="lb-td lb-td--w">{e.wins}</td>
      <td className="lb-td lb-td--l">{e.losses}</td>
      <td className="lb-td lb-td--wl">
        {winRate !== null ? `${winRate}%` : '—'}
      </td>
    </tr>
  )
}
