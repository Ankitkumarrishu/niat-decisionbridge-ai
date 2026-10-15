import { API_BASE_URL } from './config'
import { getAccessToken } from './authStore'

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

function formatDetail(detail: unknown): string {
  if (!detail) return ''
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'string') return item
        if (item && typeof item === 'object' && 'msg' in item) {
          return String((item as { msg: string }).msg)
        }
        return JSON.stringify(item)
      })
      .join('; ')
  }
  if (typeof detail === 'object') return JSON.stringify(detail)
  return String(detail)
}

async function request<T>(path: string, options: RequestInit = {}, auth = false): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }
  if (auth) {
    const token = getAccessToken()
    if (!token) throw new ApiError('Sign in required', 401)
    headers.Authorization = `Bearer ${token}`
  }

  let res: Response
  try {
    res = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })
  } catch {
    throw new ApiError(
      `Unable to reach the API at ${API_BASE_URL}. Start the FastAPI server and confirm VITE_API_BASE_URL.`,
      0,
    )
  }

  const body = await res.json().catch(() => ({}))
  if (!res.ok) {
    throw new ApiError(formatDetail(body.detail) || `Request failed (${res.status})`, res.status)
  }
  return body as T
}

export const api = {
  health: () =>
    request<{
      status: string
      openai_configured: boolean
      supabase_configured: boolean
      missing_settings?: string[]
    }>('/health'),
  submitIntake: (payload: unknown) =>
    request<{ lead_id: string; experiment_group: string; message: string }>('/api/intake', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  generateBrief: (leadId: string) =>
    request<{ brief_id: string; lead_id: string; brief: Record<string, unknown> }>('/api/decision-brief', {
      method: 'POST',
      body: JSON.stringify({ lead_id: leadId }),
    }),
  getBrief: (briefId: string) =>
    request<{ brief_id: string; lead_id: string; brief: Record<string, unknown> }>(
      `/api/decision-brief/${briefId}`,
    ),
  listLeads: (params: URLSearchParams) =>
    request<{ items: unknown[]; total: number }>(`/api/leads?${params}`, {}, true),
  getLead: (id: string) => request<Record<string, unknown>>(`/api/leads/${id}`, {}, true),
  updateFollowUp: (id: string, payload: unknown) =>
    request(`/api/leads/${id}/follow-up`, { method: 'PATCH', body: JSON.stringify(payload) }, true),
  updateApplication: (id: string, payload: unknown) =>
    request(`/api/leads/${id}/application`, { method: 'PATCH', body: JSON.stringify(payload) }, true),
  dashboard: (params: URLSearchParams) =>
    request<Record<string, unknown>>(`/api/dashboard/analytics?${params}`, {}, true),
}
