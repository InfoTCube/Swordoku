export interface ParticipantProgress {
  userId: string
  username: string
  cellsCorrect: number
  mistakes: number
  finished: boolean
}

interface OpponentPanelProps {
  participants: ParticipantProgress[]
}

export default function OpponentPanel({ participants }: OpponentPanelProps) {
  if (participants.length === 0) {
    return (
      <aside className="opponent-panel">
        <h2 className="opponent-panel-title">Opponents</h2>
        <p className="opponent-panel-empty">Waiting for opponents…</p>
      </aside>
    )
  }

  return (
    <aside className="opponent-panel">
      <h2 className="opponent-panel-title">Opponents</h2>
      <ul className="opponent-list">
        {participants.map((p) => (
          <li key={p.userId} className="opponent-item">
            <div className="opponent-header">
              <span className="opponent-username">{p.username}</span>
              {p.finished && <span className="opponent-finished-badge">Finished!</span>}
            </div>
            <div className="opponent-progress-bar-wrap">
              <div
                className="opponent-progress-bar-fill"
                style={{ width: `${(p.cellsCorrect / 81) * 100}%` }}
              />
            </div>
            <div className="opponent-stats">
              <span className="opponent-cells">{p.cellsCorrect} / 81 cells</span>
              <span className="opponent-mistakes">{p.mistakes} mistake{p.mistakes !== 1 ? 's' : ''}</span>
            </div>
          </li>
        ))}
      </ul>
    </aside>
  )
}
