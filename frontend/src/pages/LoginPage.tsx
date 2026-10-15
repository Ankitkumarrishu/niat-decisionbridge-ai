import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Alert, Button, Card } from '../components/Ui'
import { useAuth } from '../lib/AuthContext'
import { signIn } from '../lib/authStore'
import { missingFrontendSettings, supabaseConfigured } from '../lib/config'

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { refresh } = useAuth()
  const location = useLocation()
  const from = (location.state as { from?: string })?.from || '/counsellor'

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    if (!supabaseConfigured()) {
      const missing = missingFrontendSettings().join(', ')
      setError(
        `Supabase auth is not configured. Add ${missing} to frontend/.env (copy from .env.example), then restart the Vite dev server.`,
      )
      return
    }
    setLoading(true)
    try {
      await signIn(email, password)
      await refresh()
      navigate(from, { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign in failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-md px-4 py-10">
      <Card>
        <h1 className="mb-2 text-2xl font-bold">Counsellor sign in</h1>
        <p className="mb-6 text-sm text-[var(--color-navy-muted)]">
          Use your Supabase Auth account. Access is limited to emails listed in backend
          COUNSELLOR_EMAILS.
        </p>
        {error && (
          <div className="mb-4">
            <Alert tone="error">{error}</Alert>
          </div>
        )}
        <form className="space-y-4" onSubmit={onSubmit}>
          <label className="block text-sm">
            Email
            <input
              type="email"
              required
              className="mt-1 w-full rounded-xl border border-[var(--color-border)] px-3 py-2"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </label>
          <label className="block text-sm">
            Password
            <input
              type="password"
              required
              className="mt-1 w-full rounded-xl border border-[var(--color-border)] px-3 py-2"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          <Button loading={loading} variant="primary" type="submit">
            Sign in
          </Button>
        </form>
      </Card>
    </div>
  )
}
