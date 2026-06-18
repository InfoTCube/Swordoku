import { useState } from 'react'

export interface GameBoardProps {
  givens: number[]
  values: number[]
  incorrectCells?: Set<number>
  correctCells?: Set<number>
  onCellChange: (cell: number, value: number) => void
}

function getRow(i: number) { return Math.floor(i / 9) }
function getCol(i: number) { return i % 9 }
function getBox(i: number) { return Math.floor(getRow(i) / 3) * 3 + Math.floor(getCol(i) / 3) }

function getPeers(i: number): Set<number> {
  const r = getRow(i), c = getCol(i), b = getBox(i)
  const peers = new Set<number>()
  for (let j = 0; j < 81; j++) {
    if (j !== i && (getRow(j) === r || getCol(j) === c || getBox(j) === b)) {
      peers.add(j)
    }
  }
  return peers
}

function getConflicts(givens: number[], values: number[]): Set<number> {
  const display = givens.map((g, i) => (g !== 0 ? g : values[i]))
  const conflicts = new Set<number>()
  for (let i = 0; i < 81; i++) {
    if (givens[i] !== 0 || values[i] === 0) continue
    for (let j = 0; j < 81; j++) {
      if (j === i || display[j] === 0) continue
      if (
        values[i] === display[j] &&
        (getRow(i) === getRow(j) || getCol(i) === getCol(j) || getBox(i) === getBox(j))
      ) {
        conflicts.add(i)
        break
      }
    }
  }
  return conflicts
}

export default function GameBoard({
  givens,
  values,
  incorrectCells = new Set(),
  correctCells = new Set(),
  onCellChange,
}: GameBoardProps) {
  const [selected, setSelected] = useState<number | null>(null)

  const display = givens.map((g, i) => (g !== 0 ? g : values[i]))
  const conflicts = getConflicts(givens, values)
  const peers = selected !== null ? getPeers(selected) : new Set<number>()
  const selectedVal = selected !== null ? display[selected] : 0

  function handleKeyDown(e: React.KeyboardEvent<HTMLDivElement>) {
    if (selected === null) return

    if (givens[selected] === 0 && !correctCells.has(selected)) {
      if (e.key >= '1' && e.key <= '9') {
        e.preventDefault()
        onCellChange(selected, parseInt(e.key))
        return
      }
      if (e.key === 'Backspace' || e.key === 'Delete' || e.key === '0') {
        e.preventDefault()
        onCellChange(selected, 0)
        return
      }
    }

    const r = getRow(selected)
    const c = getCol(selected)
    if (e.key === 'ArrowUp' && r > 0) { e.preventDefault(); setSelected(selected - 9) }
    else if (e.key === 'ArrowDown' && r < 8) { e.preventDefault(); setSelected(selected + 9) }
    else if (e.key === 'ArrowLeft' && c > 0) { e.preventDefault(); setSelected(selected - 1) }
    else if (e.key === 'ArrowRight' && c < 8) { e.preventDefault(); setSelected(selected + 1) }
  }

  return (
    <div
      className="board"
      tabIndex={0}
      onKeyDown={handleKeyDown}
      onFocus={() => { if (selected === null) setSelected(0) }}
    >
      {Array.from({ length: 81 }, (_, i) => {
        const r = getRow(i)
        const c = getCol(i)
        const isGiven = givens[i] !== 0
        const isCorrect = !isGiven && correctCells.has(i)
        const isSelected = selected === i
        const isPeer = !isSelected && peers.has(i)
        const isSameVal = !isSelected && selectedVal !== 0 && display[i] === selectedVal
        const isConflict = conflicts.has(i)
        const isIncorrect = incorrectCells.has(i)

        const cls = [
          'board-cell',
          isGiven && 'board-cell--given',
          isCorrect && 'board-cell--correct',
          isSelected && 'board-cell--selected',
          isPeer && 'board-cell--peer',
          isSameVal && 'board-cell--same-value',
          isConflict && 'board-cell--conflict',
          isIncorrect && 'board-cell--incorrect',
          (c === 2 || c === 5) && 'board-cell--thick-right',
          (r === 2 || r === 5) && 'board-cell--thick-bottom',
        ].filter(Boolean).join(' ')

        return (
          <div
            key={i}
            className={cls}
            onClick={() => setSelected(i)}
          >
            {display[i] !== 0 ? display[i] : ''}
          </div>
        )
      })}
    </div>
  )
}
