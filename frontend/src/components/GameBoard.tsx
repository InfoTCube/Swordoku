import { useState, useMemo } from 'react'

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
        // Also highlight the conflicting peer if it is also a user-entered cell
        if (givens[j] === 0 && values[j] !== 0) conflicts.add(j)
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
  const [pencilMode, setPencilMode] = useState(false)
  const [candidates, setCandidates] = useState<Set<number>[]>(() =>
    Array.from({ length: 81 }, () => new Set<number>())
  )

  const display = givens.map((g, i) => (g !== 0 ? g : values[i]))
  const conflicts = useMemo(() => getConflicts(givens, values), [givens, values])
  const peers = useMemo(() => selected !== null ? getPeers(selected) : new Set<number>(), [selected])
  const selectedVal = selected !== null ? display[selected] : 0

  const digitCounts = new Array(10).fill(0)
  for (let i = 0; i < 81; i++) {
    if (display[i] !== 0) digitCounts[display[i]]++
  }

  function isCellEditable(i: number): boolean {
    return givens[i] === 0 && !correctCells.has(i)
  }

  function toggleCandidate(cell: number, digit: number) {
    setCandidates(prev => {
      const next = prev.map(s => new Set(s))
      if (next[cell].has(digit)) {
        next[cell].delete(digit)
      } else {
        next[cell].add(digit)
      }
      return next
    })
  }

  function clearCandidates(cell: number) {
    setCandidates(prev => {
      const next = prev.map(s => new Set(s))
      next[cell].clear()
      return next
    })
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLDivElement>) {
    if (selected === null) return

    if (e.key === 'p' || e.key === 'P') {
      e.preventDefault()
      setPencilMode(m => !m)
      return
    }

    if (isCellEditable(selected)) {
      if (e.key >= '1' && e.key <= '9') {
        e.preventDefault()
        const digit = parseInt(e.key)
        if (pencilMode) {
          toggleCandidate(selected, digit)
        } else {
          onCellChange(selected, digit)
          clearCandidates(selected)
        }
        return
      }
      if (e.key === 'Backspace' || e.key === 'Delete' || e.key === '0') {
        e.preventDefault()
        if (pencilMode) {
          clearCandidates(selected)
        } else {
          onCellChange(selected, 0)
        }
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

  function handleNumberPadClick(digit: number) {
    if (selected === null) return
    if (!isCellEditable(selected)) return
    if (pencilMode) {
      toggleCandidate(selected, digit)
    } else {
      onCellChange(selected, digit)
      clearCandidates(selected)
    }
  }

  return (
    <div className="board-with-pad">
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
          const cellCandidates = candidates[i]
          const showCandidates = display[i] === 0 && cellCandidates.size > 0

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
              {showCandidates ? (
                <div className="board-cell-candidates">
                  {[1, 2, 3, 4, 5, 6, 7, 8, 9].map(d => (
                    <span
                      key={d}
                      className={`board-cell-candidate${cellCandidates.has(d) ? ' board-cell-candidate--set' : ''}`}
                    >
                      {d}
                    </span>
                  ))}
                </div>
              ) : (
                display[i] !== 0 ? display[i] : ''
              )}
            </div>
          )
        })}
      </div>
      <div className="board-sidebar">
        <div className="number-pad">
          {[1, 2, 3, 4, 5, 6, 7, 8, 9].map(digit => {
            const selectedHasDigit =
              selected !== null &&
              givens[selected] === 0 &&
              !correctCells.has(selected) &&
              values[selected] === digit
            const exhausted = digitCounts[digit] >= 9 && !selectedHasDigit
            return (
              <button
                key={digit}
                className={`number-pad-btn${exhausted && !pencilMode ? ' number-pad-btn--exhausted' : ''}`}
                onClick={() => handleNumberPadClick(digit)}
                disabled={exhausted && !pencilMode}
                tabIndex={-1}
              >
                {digit}
              </button>
            )
          })}
        </div>
        <button
          className={`pencil-btn${pencilMode ? ' pencil-btn--active' : ''}`}
          onClick={() => setPencilMode(m => !m)}
          tabIndex={-1}
          title="Pencil mode (P)"
        >
          ✏
        </button>
      </div>
    </div>
  )
}
