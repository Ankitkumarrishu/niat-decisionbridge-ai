function isUnset(value: string | undefined): boolean {
  if (!value) return true
  const v = value.trim()
  if (!v) return true
  const lowered = v.toLowerCase()
  return (
    lowered.includes('your-project.supabase.co') ||
    lowered.includes('your_project') ||
    lowered === 'your-anon-key' ||
    lowered.includes('changeme') ||
    lowered.includes('replace-me')
  )
}

const rawApiBase = import.meta.env.VITE_API_BASE_URL?.trim() || 'http://localhost:8000'

export const API_BASE_URL = rawApiBase.replace(/\/$/, '')
export const SUPABASE_URL = isUnset(import.meta.env.VITE_SUPABASE_URL)
  ? ''
  : import.meta.env.VITE_SUPABASE_URL.trim()
export const SUPABASE_ANON_KEY = isUnset(import.meta.env.VITE_SUPABASE_ANON_KEY)
  ? ''
  : import.meta.env.VITE_SUPABASE_ANON_KEY.trim()

export function supabaseConfigured(): boolean {
  return Boolean(SUPABASE_URL && SUPABASE_ANON_KEY)
}

export function missingFrontendSettings(): string[] {
  const missing: string[] = []
  if (!SUPABASE_URL) missing.push('VITE_SUPABASE_URL')
  if (!SUPABASE_ANON_KEY) missing.push('VITE_SUPABASE_ANON_KEY')
  return missing
}
