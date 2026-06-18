import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import GameBoard from '../components/GameBoard'
import OpponentPanel from '../components/OpponentPanel'
import type { ParticipantProgress } from '../components/OpponentPanel'
import { connectToMatch } from '../ws'
import type { WsConnection } from '../ws'
import { useAuth } from '../context/AuthContext'

interface MatchEndState {
  winnerId: string | null
  reason: string
  eloDeltas: Record<string, number> | null
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60).toString().padStart(2, '0')
  const s = (seconds % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}

export default function Game() {
  const { matchId } = useParams<{ matchId: string }>()
  const navigate = useNavigate()
  const { token, currentUser } = useAuth()

  const [givens, setGivens] = useState<number[]>(new Array(81).fill(0))
  const [values, setValues] = useState<number[]>(new Array(81).fill(0))
  const [incorrectCells, setIncorrectCells] = useState<Set<number>>(new Set())
  const [correctCells, setCorrectCells] = useState<Set<number>>(new Set())
  const [blankCount, setBlankCount] = useState(81)
  const [myMistakes, setMyMistakes] = useState(0)
  const [mistakeLimit, setMistakeLimit] = useState(3)
  const [isSelfEliminated, setIsSelfEliminated] = useState(false)
  const [opponents, setOpponents] = useState<ParticipantProgress[]>([])
  const [matchEnd, setMatchEnd] = useState<MatchEndState | null>(null)
  const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting')
  const [timeLeft, setTimeLeft] = useState(600)
  const [timerStarted, setTimerStarted] = useState(false)

  const connRef = useRef<WsConnection | null>(null)
  const unmountedRef = useRef(false)
  const blankCountRef = useRef(81)
  const timeUpSentRef = useRef(false)

  // Countdown timer — starts on first board_state received
  useEffect(() => {
    if (!timerStarted || matchEnd) return
    const interval = setInterval(() => {
      setTimeLeft(prev => (prev > 0 ? prev - 1 : 0))
    }, 1000)
    return () => clearInterval(interval)
  }, [timerStarted, matchEnd])

  // Send time_up to server when timer expires (server finalises the match)
  useEffect(() => {
    if (timeLeft === 0 && timerStarted && !matchEnd && !timeUpSentRef.current) {
      timeUpSentRef.current = true
      connRef.current?.send({ type: 'time_up' })
    }
  }, [timeLeft, timerStarted, matchEnd])

  // WS connection with reconnect
  useEffect(() => {
    if (!matchId || !token) return
    unmountedRef.current = false

    function connect() {
      if (unmountedRef.current) return
      setWsStatus('connecting')

      const conn = connectToMatch(matchId!, token!, {
        onOpen: () => setWsStatus('connected'),
        onClose: (event) => {
          if (!unmountedRef.current) {
            setWsStatus('disconnected')
            if (event.code === 1008) {
              // Match finished, not a participant, or bad token — redirect home
              navigate('/', { state: { notice: 'This game is no longer available — it may have ended or you are not a participant.' } })
            } else {
              setTimeout(() => { if (!unmountedRef.current) connect() }, 3000)
            }
          }
        },
        onError: () => {
          if (!unmountedRef.current) setWsStatus('disconnected')
        },
        onMessage: (msg) => {
          const type = msg.type as string

          if (type === 'board_state') {
            const newGivens = msg.givens as number[]
            const bc = (msg.blank_count as number | undefined) ?? newGivens.filter(g => g === 0).length
            setGivens(newGivens)
            setBlankCount(bc)
            blankCountRef.current = bc

            const serverTimeLimitS = (msg.time_limit_s as number | undefined) ?? 600
            setMistakeLimit((msg.mistake_limit as number | undefined) ?? 3)

            // Sync timer: calculate remaining time from server's started_at
            const startedAt = msg.started_at as number | null | undefined
            if (startedAt != null) {
              const elapsed = Math.floor(Date.now() / 1000 - startedAt)
              setTimeLeft(Math.max(0, serverTimeLimitS - elapsed))
            } else {
              setTimeLeft(serverTimeLimitS)
            }
            setTimerStarted(true)

            // Restore previously filled cells on reconnect
            const restoredBoard = msg.board_state as number[] | undefined
            if (restoredBoard) {
              setValues(restoredBoard)
              const restored = new Set<number>()
              restoredBoard.forEach((v, i) => {
                if (v !== 0 && newGivens[i] === 0) restored.add(i)
              })
              setCorrectCells(restored)
            }
            setMyMistakes((msg.mistakes as number | undefined) ?? 0)

            // Restore eliminated state on reconnect
            const eliminatedIds = (msg.eliminated_user_ids as string[] | undefined) ?? []
            if (currentUser && eliminatedIds.includes(currentUser.id)) {
              setIsSelfEliminated(true)
            }
          }

          else if (type === 'move_result') {
            const cell = msg.cell as number
            const correct = msg.correct as boolean
            if (correct) {
              setCorrectCells(prev => new Set(prev).add(cell))
              setIncorrectCells(prev => {
                const next = new Set(prev)
                next.delete(cell)
                return next
              })
            } else {
              setIncorrectCells(prev => new Set(prev).add(cell))
            }
          }

          else if (type === 'progress') {
            const userId = msg.user_id as string
            const cellsCorrect = msg.cells_correct as number
            const mistakes = msg.mistakes as number

            if (userId === currentUser?.id) {
              setMyMistakes(mistakes)
              return
            }

            setOpponents(prev => {
              const idx = prev.findIndex(p => p.userId === userId)
              const existing = idx !== -1 ? prev[idx] : null
              const entry: ParticipantProgress = {
                userId,
                username: msg.username as string,
                cellsCorrect,
                mistakes,
                finished: cellsCorrect >= blankCountRef.current,
                eliminated: existing?.eliminated ?? false,
              }
              if (idx === -1) return [...prev, entry]
              const next = [...prev]
              next[idx] = entry
              return next
            })
          }

          else if (type === 'player_eliminated') {
            const userId = msg.user_id as string
            if (userId === currentUser?.id) {
              setIsSelfEliminated(true)
            } else {
              setOpponents(prev => prev.map(p =>
                p.userId === userId
                  ? { ...p, eliminated: true }
                  : p
              ))
            }
          }

          else if (type === 'match_end') {
            setMatchEnd({
              winnerId: (msg.winner_id as string | null) ?? null,
              reason: msg.reason as string,
              eloDeltas: (msg.elo_deltas as Record<string, number> | null) ?? null,
            })
          }
        },
      })
      connRef.current = conn
    }

    connect()
    return () => {
      unmountedRef.current = true
      connRef.current?.close()
    }
  }, [matchId, token, currentUser?.id])

  function handleCellChange(cell: number, value: number) {
    if (isSelfEliminated || correctCells.has(cell)) return

    // Typing the same digit that's already in the cell clears it without a mistake
    const effectiveValue = values[cell] === value ? 0 : value

    setValues(prev => {
      const next = [...prev]
      next[cell] = effectiveValue
      return next
    })

    if (effectiveValue === 0) {
      setIncorrectCells(prev => {
        const next = new Set(prev)
        next.delete(cell)
        return next
      })
      return
    }

    connRef.current?.send({ cell, value: effectiveValue })
  }

  function getResult(): 'win' | 'loss' | 'draw' {
    if (!matchEnd || !currentUser) return 'draw'
    if (matchEnd.winnerId === null) return 'draw'
    return matchEnd.winnerId === currentUser.id ? 'win' : 'loss'
  }

  const result = matchEnd ? getResult() : null
  const eloDelta = matchEnd?.eloDeltas && currentUser ? matchEnd.eloDeltas[currentUser.id] : undefined
  const isUrgent = timeLeft <= 60 && !matchEnd
  const isMistakeDanger = myMistakes > 0 && myMistakes >= mistakeLimit - 1

  return (
    <div className="game-container">
      <div className="game-header">
        {wsStatus === 'disconnected' && (
          <div className="game-reconnecting">Reconnecting…</div>
        )}
        <div className="game-header-row">
          <h1 className="game-title">Game</h1>
          <div className="game-header-right">
            {!matchEnd && (
              <div className={`game-timer${isUrgent ? ' game-timer--urgent' : ''}`}>
                {formatTime(timeLeft)}
              </div>
            )}
            {!matchEnd && !isSelfEliminated && (
              <div className={`game-mistakes${isMistakeDanger ? ' game-mistakes--danger' : ''}`}>
                Mistakes: {myMistakes} / {mistakeLimit}
              </div>
            )}
          </div>
        </div>
      </div>

      {isSelfEliminated && !matchEnd && (
        <div className="game-eliminated-banner">
          You've been eliminated — watch the others play!
        </div>
      )}

      {matchEnd && (
        <div className="game-overlay">
          <div className="game-overlay-card">
            <p className={`game-result game-result--${result}`}>
              {result === 'win' ? 'You Win!' : result === 'loss' ? 'You Lose' : 'Draw'}
            </p>
            {eloDelta !== undefined && (
              <p className={`game-elo-delta${eloDelta >= 0 ? ' game-elo-delta--positive' : ' game-elo-delta--negative'}`}>
                {eloDelta >= 0 ? '+' : ''}{eloDelta} ELO
              </p>
            )}
            <p className="game-result-reason">
              {matchEnd.reason === 'completed'
                ? result === 'win' ? 'You completed the puzzle!' : 'Opponent completed the puzzle!'
                : matchEnd.reason === 'mistake_limit'
                  ? result === 'win' ? 'Opponent made too many mistakes!' : 'Too many mistakes!'
                  : 'Time is up!'}
            </p>
            <button className="game-overlay-btn" onClick={() => navigate('/')}>
              Back to home
            </button>
          </div>
        </div>
      )}

      <div className="game-layout">
        <div className="game-board-wrap">
          <GameBoard
            givens={givens}
            values={values}
            incorrectCells={incorrectCells}
            correctCells={correctCells}
            onCellChange={handleCellChange}
          />
        </div>
        <OpponentPanel
          participants={opponents}
          blankCount={blankCount}
          self={currentUser ? {
            userId: currentUser.id,
            username: currentUser.username,
            cellsCorrect: correctCells.size,
            mistakes: myMistakes,
            finished: correctCells.size >= blankCount,
            eliminated: isSelfEliminated,
          } : undefined}
        />
      </div>
    </div>
  )
}
