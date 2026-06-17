import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../context/AuthContext'

export default function Register() {
  const { login } = useAuth()
  const navigate = useNavigate()

  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)

    if (!username.trim()) { setError('Username is required.'); return }
    if (username.trim().length > 32) { setError('Username must be 32 characters or fewer.'); return }
    if (!email.trim()) { setError('Email is required.'); return }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { setError('Enter a valid email address.'); return }
    if (!password) { setError('Password is required.'); return }
    if (password.length < 8) { setError('Password must be at least 8 characters.'); return }

    setLoading(true)
    try {
      await api.post('/auth/register', { username: username.trim(), email: email.trim(), password })

      // Auto-login after registration
      const params = new URLSearchParams({ username: username.trim(), password })
      const tokenRes = await api.post<{ access_token: string }>('/auth/login', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      login(tokenRes.data.access_token, username.trim())
      navigate('/')
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(typeof detail === 'string' ? detail : 'Registration failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-container">
      <h1 className="auth-title">Create account</h1>

      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        {error && <p className="auth-error">{error}</p>}

        <label className="auth-label">
          Username
          <input
            className="auth-input"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            maxLength={32}
            disabled={loading}
          />
        </label>

        <label className="auth-label">
          Email
          <input
            className="auth-input"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            disabled={loading}
          />
        </label>

        <label className="auth-label">
          Password <span className="auth-hint">(min 8 characters)</span>
          <input
            className="auth-input"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
            disabled={loading}
          />
        </label>

        <button className="auth-btn" type="submit" disabled={loading}>
          {loading ? 'Creating account…' : 'Create account'}
        </button>
      </form>

      <p className="auth-switch">
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </div>
  )
}
