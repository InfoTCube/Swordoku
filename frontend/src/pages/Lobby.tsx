import { useParams } from 'react-router-dom'

export default function Lobby() {
  const { code } = useParams<{ code: string }>()
  return (
    <div>
      <h1>Lobby</h1>
      <p>Lobby code: <strong>{code}</strong></p>
      <p>Waiting room goes here!</p>
    </div>
  )
}
