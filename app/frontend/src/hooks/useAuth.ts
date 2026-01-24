import { useState, useEffect } from 'react'

interface User {
  id: number
  email: string
  name: string | null
  picture: string | null
  is_admin: boolean
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/auth/me', { credentials: 'include' })
      .then(res => res.json())
      .then(data => {
        setUser(data)
        setLoading(false)
      })
      .catch(() => {
        setUser(null)
        setLoading(false)
      })
  }, [])

  const login = () => {
    window.location.href = '/api/auth/login'
  }

  const logout = () => {
    window.location.href = '/api/auth/logout'
  }

  return { user, loading, login, logout }
}
