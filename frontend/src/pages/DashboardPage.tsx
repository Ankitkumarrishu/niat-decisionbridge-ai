import { useEffect, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Alert, Card } from '../components/Ui'
import { api, ApiError } from '../lib/api'

type MetricRate = { numerator: number; denominator: number; rate: number | null; label: string }

export function DashboardPage() {
  const [data, setData] = useState<Record<string, unknown> | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  useEffect(() => {
    const params = new URLSearchParams()
    if (dateFrom) params.set('date_from', new Date(dateFrom).toISOString())
    if (dateTo) params.set('date_to', new Date(dateTo).toISOString())
    api
      .dashboard(params)
      .then(setData)
      .catch((err: ApiError) => setError(err.message))
  }, [dateFrom, dateTo])

  if (error) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10">
        <Alert tone="error">{error}</Alert>
      </div>
    )
  }

  if (!data) {
    return <p className="px-4 py-10 text-center text-sm">Loading analytics…</p>
  }

  const funnel = (data.funnel as Array<{ stage: string; count: number }>) || []
  const timeSeries = (data.time_series as Array<{ date: string; leads: number }>) || []
  const experiment = (data.experiment_comparison as Array<Record<string, unknown>>) || []
  const briefRate = data.brief_generation_success_rate as MetricRate
  const convRate = data.lead_to_application_conversion_rate as MetricRate
  const followRate = data.counsellor_follow_up_rate as MetricRate

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Growth analytics</h1>
          <p className="text-sm text-[var(--color-navy-muted)]">
            Range: {String(data.date_from)} → {String(data.date_to)}
          </p>
        </div>
        <div className="flex gap-2">
          <input type="date" className="rounded-xl border px-3 py-2 text-sm" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          <input type="date" className="rounded-xl border px-3 py-2 text-sm" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
        </div>
      </div>

      {(data.notes as string[])?.map((note) => (
        <Alert key={note} tone="info">
          {note}
        </Alert>
      ))}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Consented leads" value={Number(data.total_consented_leads)} />
        <Stat label="Briefs generated" value={Number(data.decision_briefs_generated)} />
        <Stat label="Follow-up requests" value={Number(data.counsellor_follow_up_requests)} />
        <Stat label="Applications completed" value={Number(data.completed_applications)} />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <RateCard title="Brief generation success rate" metric={briefRate} />
        <RateCard title="Lead → application conversion" metric={convRate} />
        <RateCard title="Counsellor follow-up rate" metric={followRate} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <h2 className="mb-4 font-semibold">Funnel</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={funnel}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="stage" hide />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#2563eb" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
        <Card>
          <h2 className="mb-4 font-semibold">Leads over time</h2>
          <div className="h-64">
            {timeSeries.length === 0 ? (
              <p className="text-sm text-[var(--color-navy-muted)]">No leads in selected range.</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={timeSeries}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Line type="monotone" dataKey="leads" stroke="#2563eb" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </Card>
      </div>

      <Card>
        <h2 className="mb-4 font-semibold">Experiment cohort comparison (control vs treatment)</h2>
        <div className="grid gap-4 md:grid-cols-2">
          {experiment.map((cohort) => (
            <div key={String(cohort.group)} className="rounded-xl border border-[var(--color-border)] p-4 text-sm">
              <p className="font-semibold uppercase">{String(cohort.group)}</p>
              <p>Eligible leads: {Number(cohort.eligible_leads)}</p>
              <p>Briefs generated: {Number(cohort.briefs_generated)}</p>
              <p>Follow-up requests: {Number(cohort.follow_up_requests)}</p>
              <p>Applications completed: {Number(cohort.applications_completed)}</p>
              <p>Applications within 7 days: {String(cohort.applications_within_7_days ?? 'n/a')}</p>
              <p className="mt-2 text-xs text-[var(--color-navy-muted)]">
                {String(cohort.applications_within_7_days_note)}
              </p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <Card>
      <p className="text-sm text-[var(--color-navy-muted)]">{label}</p>
      <p className="mt-2 text-3xl font-bold">{value}</p>
    </Card>
  )
}

function RateCard({ title, metric }: { title: string; metric: MetricRate }) {
  const pct = metric.rate == null ? '—' : `${(metric.rate * 100).toFixed(1)}%`
  return (
    <Card>
      <p className="text-sm font-medium">{title}</p>
      <p className="mt-2 text-2xl font-bold">{pct}</p>
      <p className="mt-2 text-xs text-[var(--color-navy-muted)]">
        {metric.numerator} / {metric.denominator} · {metric.label}
      </p>
    </Card>
  )
}
