import axios from 'axios'

export const api = axios.create({
  baseURL: '/',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let _logout: (() => void) | null = null
export function registerLogoutHandler(fn: () => void): void {
  _logout = fn
}

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && _logout) {
      _logout()
    }
    return Promise.reject(err)
  }
)

function decodePayload(token: string): Record<string, unknown> | null {
  try {
    const payload = token.split('.')[1]
    return JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')))
  } catch {
    return null
  }
}

/** Decode the user_id stored in the JWT `sub` claim without verifying signature. */
export function decodeTokenSub(token: string): string | null {
  const decoded = decodePayload(token)
  if (!decoded) return null
  const sub = decoded.sub
  return typeof sub === 'string' ? sub : sub != null ? String(sub) : null
}

/** Returns true if the token is expired or unparseable. */
export function isTokenExpired(token: string): boolean {
  const decoded = decodePayload(token)
  if (!decoded) return true
  if (typeof decoded.exp !== 'number') return false
  return Date.now() / 1000 > decoded.exp
}
