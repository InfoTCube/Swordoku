import { useEffect, useState } from 'react'
import { Link, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

type Theme = 'light' | 'dark'

function getEffectiveTheme(): Theme {
  const stored = localStorage.getItem('theme')
  if (stored === 'light' || stored === 'dark') return stored
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function applyTheme(theme: Theme) {
  document.documentElement.setAttribute('data-theme', theme)
  localStorage.setItem('theme', theme)
}

export default function Layout() {
  const { currentUser, logout } = useAuth()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)
  const [theme, setTheme] = useState<Theme>(getEffectiveTheme)

  useEffect(() => {
    applyTheme(theme)
  }, [theme])

  function toggleTheme() {
    setTheme(t => (t === 'dark' ? 'light' : 'dark'))
  }

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
          <button
            className="theme-toggle"
            onClick={toggleTheme}
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {theme === 'dark' ? '☀' : '☾'}
          </button>
        </div>
      </nav>
      <main className="main-content">
        <Outlet />
      </main>
    </>
  )
}
