import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Alert, Button, Card } from '../components/Ui'
import { api, ApiError } from '../lib/api'

type Lead = {
  id: string
  student_first_name: string
  email?: string
  primary_concern: string
  follow_up_status: string
  application_status: string
  preferred_language: string
  is_demo: boolean
  latest_decision_brief_id?: string
}

const followUpOptions = [
  'new',
  'brief_generated',
  'follow_up_requested',
  'contacted',
  'application_completed',
  'closed',
]

export function CounsellorPage() {
  const [leads, setLeads] = useState<Lead[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null)
  const [search, setSearch] = useState('')
  const [concern, setConcern] = useState('')
  const [language, setLanguage] = useState('')
  const [status, setStatus] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [note, setNote] = useState('')
  const [loading, setLoading] = useState(true)

  const params = useMemo(() => {
    const p = new URLSearchParams()
    if (search) p.set('search', search)
    if (concern) p.set('concern', concern)
    if (language) p.set('language', language)
    if (status) p.set('follow_up_status', status)
    return p
  }, [search, concern, language, status])

  useEffect(() => {
    setLoading(true)
    api
      .listLeads(params)
      .then((res) => setLeads(res.items as Lead[]))
      .catch((err: ApiError) => setError(err.message))
      .finally(() => setLoading(false))
  }, [params])

  useEffect(() => {
    if (!selectedId) return
    api
      .getLead(selectedId)
      .then(setDetail)
      .catch((err: ApiError) => setError(err.message))
  }, [selectedId])

  async function updateFollowUp(next: string) {
    if (!selectedId) return
    await api.updateFollowUp(selectedId, { follow_up_status: next, note: note || undefined })
    setNote('')
    const refreshed = await api.getLead(selectedId)
    setDetail(refreshed)
    const list = await api.listLeads(params)
    setLeads(list.items as Lead[])
  }

  return (
    <div className="mx-auto grid max-w-6xl gap-6 px-4 py-8 lg:grid-cols-[1fr_1.2fr]">
      <Card className="space-y-4">
        <h1 className="text-2xl font-bold">Counsellor CRM</h1>
        {error && <Alert tone="error">{error}</Alert>}
        <div className="grid gap-2 md:grid-cols-2">
          <input
            placeholder="Search name or email"
            className="rounded-xl border border-[var(--color-border)] px-3 py-2 text-sm"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <select className="rounded-xl border border-[var(--color-border)] px-3 py-2 text-sm" value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">All follow-up statuses</option>
            {followUpOptions.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <select className="rounded-xl border border-[var(--color-border)] px-3 py-2 text-sm" value={concern} onChange={(e) => setConcern(e.target.value)}>
            <option value="">All concerns</option>
            <option value="fees">Fees</option>
            <option value="placements">Placements</option>
            <option value="degree_university">Degree university</option>
          </select>
          <select className="rounded-xl border border-[var(--color-border)] px-3 py-2 text-sm" value={language} onChange={(e) => setLanguage(e.target.value)}>
            <option value="">All languages</option>
            <option value="en">English</option>
            <option value="hi">Hindi</option>
          </select>
        </div>
        {loading ? (
          <p className="text-sm text-[var(--color-navy-muted)]">Loading leads…</p>
        ) : leads.length === 0 ? (
          <p className="text-sm text-[var(--color-navy-muted)]">No leads match your filters.</p>
        ) : (
          <ul className="max-h-[520px] space-y-2 overflow-auto">
            {leads.map((lead) => (
              <li key={lead.id}>
                <button
                  type="button"
                  onClick={() => setSelectedId(lead.id)}
                  className={`w-full rounded-xl border px-3 py-3 text-left text-sm ${
                    selectedId === lead.id ? 'border-[var(--color-accent)] bg-blue-50' : 'border-[var(--color-border)]'
                  }`}
                >
                  <div className="font-semibold">
                    {lead.student_first_name}
                    {lead.is_demo && <span className="ml-2 rounded bg-amber-100 px-2 py-0.5 text-xs">DEMO</span>}
                  </div>
                  <div className="text-[var(--color-navy-muted)]">{lead.follow_up_status}</div>
                </button>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Card>
        {!detail ? (
          <p className="text-sm text-[var(--color-navy-muted)]">Select a lead to review context and update status.</p>
        ) : (
          <div className="space-y-4">
            <div>
              <h2 className="text-xl font-bold">{String(detail.student_first_name)}</h2>
              <p className="text-sm text-[var(--color-navy-muted)]">{String(detail.email || 'No email')}</p>
            </div>
            {detail.latest_decision_brief_id ? (
              <Link className="text-sm" to={`/report/${detail.latest_decision_brief_id}`}>
                Open decision brief
              </Link>
            ) : (
              <p className="text-sm text-[var(--color-navy-muted)]">No brief generated yet.</p>
            )}
            {Boolean(detail.brief) && (
              <div className="rounded-xl border border-[var(--color-border)] p-4 text-sm">
                <p className="font-medium">AI summary</p>
                <p className="mt-2 text-[var(--color-navy-muted)]">{String((detail.brief as { summary?: string }).summary || '')}</p>
                <p className="mt-3 font-medium">Suggested next step</p>
                <p className="text-[var(--color-navy-muted)]">
                  {String((detail.brief as { recommended_next_step?: string }).recommended_next_step || '')}
                </p>
              </div>
            )}
            <label className="block text-sm">
              Note / next action
              <textarea
                className="mt-1 w-full rounded-xl border border-[var(--color-border)] px-3 py-2"
                value={note}
                onChange={(e) => setNote(e.target.value)}
              />
            </label>
            <div className="flex flex-wrap gap-2">
              {followUpOptions.map((s) => (
                <Button key={s} variant="secondary" onClick={() => updateFollowUp(s)}>
                  Mark {s}
                </Button>
              ))}
            </div>
            <div className="flex flex-wrap gap-2">
              {['not_started', 'in_progress', 'completed', 'withdrawn'].map((s) => (
                <Button
                  key={s}
                  variant="secondary"
                  onClick={async () => {
                    if (!selectedId) return
                    await api.updateApplication(selectedId, { application_status: s, note: note || undefined })
                    setNote('')
                    setDetail(await api.getLead(selectedId))
                    const list = await api.listLeads(params)
                    setLeads(list.items as Lead[])
                  }}
                >
                  Application {s}
                </Button>
              ))}
            </div>
            <div>
              <p className="mb-2 text-sm font-medium">Status history</p>
              <ul className="space-y-2 text-xs text-[var(--color-navy-muted)]">
                {((detail.events as Array<{ event_type: string; created_at: string }>) || []).map((ev) => (
                  <li key={`${ev.created_at}-${ev.event_type}`}>
                    {ev.created_at} · {ev.event_type}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </Card>
    </div>
  )
}
