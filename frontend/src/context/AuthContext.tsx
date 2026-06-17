import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import { decodeTokenSub } from '../api'

interface CurrentUser {
  id: string
  username: string
}

interface AuthContextValue {
  token: string | null
  currentUser: CurrentUser | null
  login: (token: string, username: string) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

function loadStoredUser(): { token: string; user: CurrentUser } | null {
  const token = localStorage.getItem('token')
  const raw = localStorage.getItem('currentUser')
  if (!token || !raw) return null
  try {
    return { token, user: JSON.parse(raw) }
  } catch {
    return null
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const stored = loadStoredUser()
  const [token, setToken] = useState<string | null>(stored?.token ?? null)
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(stored?.user ?? null)

  const login = useCallback((newToken: string, username: string) => {
    const id = decodeTokenSub(newToken) ?? ''
    const user: CurrentUser = { id, username }
    localStorage.setItem('token', newToken)
    localStorage.setItem('currentUser', JSON.stringify(user))
    setToken(newToken)
    setCurrentUser(user)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('token')
    localStorage.removeItem('currentUser')
    setToken(null)
    setCurrentUser(null)
  }, [])

  const value = useMemo(() => ({ token, currentUser, login, logout }), [token, currentUser, login, logout])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
