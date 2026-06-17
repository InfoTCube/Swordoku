import { Link, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Layout() {
  const { currentUser, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <>
      <nav className="nav">
        <Link className="nav-brand" to="/">Swordoku</Link>
        <div className="nav-links">
          <Link to="/">Home</Link>
          <Link to="/leaderboard">Leaderboard</Link>
          {currentUser ? (
            <>
              <Link to={`/profile/${currentUser.username}`}>Profile</Link>
              <button onClick={handleLogout} className="btn-link">Logout</button>
            </>
          ) : (
            <>
              <Link to="/login">Login</Link>
              <Link to="/register">Register</Link>
            </>
          )}
        </div>
      </nav>
      <main className="main-content">
        <Outlet />
      </main>
    </>
  )
}
