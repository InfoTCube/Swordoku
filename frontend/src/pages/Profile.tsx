import { useParams } from 'react-router-dom'

export default function Profile() {
  const { username } = useParams<{ username: string }>()
  return (
    <div>
      <h1>Profile</h1>
      <p>Player: <strong>{username}</strong></p>
      <p>Profile page goes here!</p>
    </div>
  )
}
