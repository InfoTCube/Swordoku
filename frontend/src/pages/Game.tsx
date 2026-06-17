import { useState } from 'react'
import { useParams } from 'react-router-dom'
import GameBoard from '../components/GameBoard'

const EMPTY_GIVENS = new Array(81).fill(0)
const EMPTY_VALUES = new Array(81).fill(0)

export default function Game() {
  const { matchId } = useParams<{ matchId: string }>()
  const [values, setValues] = useState<number[]>(EMPTY_VALUES)

  function handleCellChange(cell: number, value: number) {
    setValues(prev => {
      const next = [...prev]
      next[cell] = value
      return next
    })
  }

  return (
    <div className="game-container">
      <div className="game-header">
        <h1 className="game-title">Game</h1>
        <p className="game-match-id">Match: <strong>{matchId}</strong></p>
      </div>
      <div className="game-layout">
        <div className="game-board-wrap">
          <GameBoard
            givens={EMPTY_GIVENS}
            values={values}
            onCellChange={handleCellChange}
          />
        </div>
      </div>
    </div>
  )
}
