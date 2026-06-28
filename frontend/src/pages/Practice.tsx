import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api'
import GameBoard, { type GameBoardHandle } from '../components/GameBoard'

type Difficulty = 'easy' | 'medium' | 'hard'

interface PracticeOut {
  id: string
  difficulty: Difficulty
  givens: number[]
  solution: number[]
}

export default function Practice() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const difficulty = (searchParams.get('difficulty') as Difficulty | null) ?? 'medium'

  const [puzzle, setPuzzle] = useState<PracticeOut | null>(null)
  const [values, setValues] = useState<number[]>(new Array(81).fill(0))
  const [incorrectCells, setIncorrectCells] = useState<Set<number>>(new Set())
  const [correctCells, setCorrectCells] = useState<Set<number>>(new Set())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [completed, setCompleted] = useState(false)

  const boardRef = useRef<GameBoardHandle>(null)
  const blankCount = puzzle ? puzzle.givens.filter(g => g === 0).length : 0

  const fetchPuzzle = useCallback(async () => {
    setLoading(true)
    setError(null)
    setCompleted(false)
    setValues(new Array(81).fill(0))
    setIncorrectCells(new Set())
    setCorrectCells(new Set())
    try {
      const res = await api.get<PracticeOut>(`/puzzles/random?difficulty=${difficulty}`)
      setPuzzle(res.data)
    } catch {
      setError('Failed to load puzzle. Make sure puzzles have been seeded.')
    } finally {
      setLoading(false)
    }
  }, [difficulty])

  useEffect(() => {
    fetchPuzzle()
  }, [fetchPuzzle])

  function handleCellChange(cell: number, value: number) {
    if (!puzzle || correctCells.has(cell)) return

    // Clicking the same digit again clears the cell
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

    if (effectiveValue === puzzle.solution[cell]) {
      const nextCorrect = new Set(correctCells).add(cell)
      setCorrectCells(nextCorrect)
      setIncorrectCells(prev => {
        const next = new Set(prev)
        next.delete(cell)
        return next
      })
      boardRef.current?.clearPeerCandidates(cell, effectiveValue)
      if (nextCorrect.size >= blankCount) {
        setCompleted(true)
      }
    } else {
      setIncorrectCells(prev => new Set(prev).add(cell))
    }
  }

  const difficultyLabel = difficulty.charAt(0).toUpperCase() + difficulty.slice(1)

  return (
    <div className="practice-container">
      <div className="practice-header">
        <h1 className="practice-title">Solo Practice</h1>
        <span className="practice-difficulty">{difficultyLabel}</span>
        {!loading && !error && (
          <div className="practice-progress">
            {correctCells.size} / {blankCount} filled
          </div>
        )}
      </div>

      {loading && <p className="practice-loading">Loading puzzle…</p>}
      {error && <p className="practice-error">{error}</p>}

      {completed && (
        <div className="game-overlay">
          <div className="game-overlay-card">
            <p className="game-result game-result--win">Puzzle Complete!</p>
            <p className="game-result-reason">Well done — you solved it!</p>
            <div className="practice-overlay-actions">
              <button className="game-overlay-btn" onClick={fetchPuzzle}>
                New puzzle
              </button>
              <button className="game-overlay-btn practice-overlay-btn--secondary" onClick={() => navigate('/')}>
                Back to home
              </button>
            </div>
          </div>
        </div>
      )}

      {puzzle && !loading && (
        <div className="practice-board-wrap">
          <GameBoard
            ref={boardRef}
            givens={puzzle.givens}
            values={values}
            incorrectCells={incorrectCells}
            correctCells={correctCells}
            onCellChange={handleCellChange}
          />
        </div>
      )}
    </div>
  )
}
