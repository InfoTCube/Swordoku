import { useState } from 'react'
import { Link, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Layout() {
  const { currentUser, logout } = useAuth()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)

  function handleLogout() {
    logout()
    navigate('/login')
    setMenuOpen(false)
  }

  function close() { setMenuOpen(false) }

  return (
    <>
      <nav className="nav">
        <Link className="nav-brand" to="/" onClick={close}>Swordoku</Link>
        <button
          className={`nav-burger${menuOpen ? ' nav-burger--open' : ''}`}
          onClick={() => setMenuOpen(o => !o)}
          aria-label={menuOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={menuOpen}
        >
          <span />
          <span />
          <span />
        </button>
        {menuOpen && <div className="nav-overlay" onClick={close} />}
        <div className={`nav-links${menuOpen ? ' nav-links--open' : ''}`}>
          <Link to="/" onClick={close}>Home</Link>
          <Link to="/leaderboard" onClick={close}>Leaderboard</Link>
          {currentUser ? (
            <>
              <Link to={`/profile/${currentUser.username}`} onClick={close}>Profile</Link>
              <button onClick={handleLogout} className="btn-link">Logout</button>
            </>
          ) : (
            <>
              <Link to="/login" onClick={close}>Login</Link>
              <Link to="/register" onClick={close}>Register</Link>
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
