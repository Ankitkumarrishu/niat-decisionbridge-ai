import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { initAuth, signOut as supabaseSignOut } from './authStore'

type AuthContextValue = {
  signedIn: boolean
  refresh: () => Promise<void>
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [signedIn, setSignedIn] = useState(false)

  async function refresh() {
    const session = await initAuth()
    setSignedIn(Boolean(session))
  }

  useEffect(() => {
    refresh()
  }, [])

  const value = useMemo(
    () => ({
      signedIn,
      refresh,
      signOut: async () => {
        await supabaseSignOut()
        setSignedIn(false)
      },
    }),
    [signedIn],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
