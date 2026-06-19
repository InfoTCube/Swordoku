export interface ParticipantProgress {
  userId: string
  username: string
  cellsCorrect: number
  mistakes: number
  finished: boolean
  eliminated: boolean
}

interface OpponentPanelProps {
  participants: ParticipantProgress[]
  blankCount?: number
  self?: ParticipantProgress
}

function ParticipantRow({ p, givenCount, isYou }: { p: ParticipantProgress; givenCount: number; isYou?: boolean }) {
  const totalKnown = p.cellsCorrect + givenCount
  return (
    <li className={`opponent-item${isYou ? ' opponent-item--self' : ''}`}>
      <div className="opponent-header">
        <span className="opponent-username">
          {p.username}
          {isYou && <span className="opponent-you-tag"> (You)</span>}
        </span>
        {p.finished && <span className="opponent-finished-badge">Finished!</span>}
        {p.eliminated && !p.finished && <span className="opponent-eliminated-badge">Eliminated</span>}
      </div>
      <div className="opponent-progress-bar-wrap">
        <div
          className="opponent-progress-bar-fill"
          style={{ width: `${(totalKnown / 81) * 100}%` }}
        />
      </div>
      <div className="opponent-stats">
        <span className="opponent-cells">{totalKnown} / 81 cells</span>
        <span className="opponent-mistakes">{p.mistakes} mistake{p.mistakes !== 1 ? 's' : ''}</span>
      </div>
    </li>
  )
}

export default function OpponentPanel({ participants, blankCount = 81, self }: OpponentPanelProps) {
  const givenCount = 81 - blankCount

  return (
    <aside className="opponent-panel">
      <h2 className="opponent-panel-title">Progress</h2>
      <ul className="opponent-list">
        {self && <ParticipantRow p={self} givenCount={givenCount} isYou />}
        {participants.length === 0 && !self && (
          <p className="opponent-panel-empty">Waiting for opponents…</p>
        )}
        {participants.map((p) => (
          <ParticipantRow key={p.userId} p={p} givenCount={givenCount} />
        ))}
      </ul>
    </aside>
  )
}
