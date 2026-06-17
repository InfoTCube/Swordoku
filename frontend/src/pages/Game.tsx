import { useParams } from 'react-router-dom'

export default function Game() {
  const { matchId } = useParams<{ matchId: string }>()
  return (
    <div>
      <h1>Game</h1>
      <p>Match ID: <strong>{matchId}</strong></p>
      <p>Game board goes here!</p>
    </div>
  )
}
