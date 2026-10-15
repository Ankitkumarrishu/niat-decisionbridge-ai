import { createClient, type Session } from '@supabase/supabase-js'
import { SUPABASE_ANON_KEY, SUPABASE_URL, supabaseConfigured } from './config'

let session: Session | null = null
let listenerBound = false

export const supabase = supabaseConfigured()
  ? createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
      },
    })
  : null

export function setSession(next: Session | null) {
  session = next
}

export function getAccessToken(): string | null {
  return session?.access_token ?? null
}

export function mapAuthError(error: { message?: string; code?: string } | Error): string {
  const message = (error.message || '').toLowerCase()
  if (message.includes('invalid login credentials')) {
    return 'Invalid email or password.'
  }
  if (message.includes('email not confirmed')) {
    return 'This email is not confirmed yet. Confirm it in Supabase Auth → Users, or disable “Confirm email” in Authentication → Providers → Email for local testing.'
  }
  if (message.includes('user not found')) {
    return 'No account exists for this email. Create the counsellor user in Supabase Auth.'
  }
  return error.message || 'Sign in failed'
}

export async function signIn(email: string, password: string) {
  if (!supabase) {
    throw new Error(
      'Supabase auth is not configured. Create frontend/.env with VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY, then restart npm run dev.',
    )
  }
  const { data, error } = await supabase.auth.signInWithPassword({ email, password })
  if (error) throw new Error(mapAuthError(error))
  if (!data.session) throw new Error('Sign in did not return a session')
  setSession(data.session)
  return data.session
}

export async function signOut() {
  if (supabase) await supabase.auth.signOut()
  setSession(null)
}

export async function initAuth() {
  if (!supabase) return null
  const { data } = await supabase.auth.getSession()
  setSession(data.session)
  if (!listenerBound) {
    listenerBound = true
    supabase.auth.onAuthStateChange((_event, s) => setSession(s))
  }
  return data.session
}
