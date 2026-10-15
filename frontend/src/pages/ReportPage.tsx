import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Alert, Button, Card } from '../components/Ui'
import { api, ApiError } from '../lib/api'

type VerifiedFact = { fact: string; source_url: string; last_verified_date: string }

type Brief = {
  summary: string
  student_goals: string[]
  verified_facts: VerifiedFact[]
  source_references: string[]
  primary_objection?: string
  unresolved_questions: string[]
  questions_to_ask_counsellor: string[]
  recommended_next_step: string
  language: string
  verification_notice: string
}

export function ReportPage() {
  const { id } = useParams()
  const [brief, setBrief] = useState<Brief | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    api
      .getBrief(id)
      .then((res) => setBrief(res.brief as Brief))
      .catch((err: ApiError) => setError(err.message))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return <p className="px-4 py-10 text-center text-sm text-[var(--color-navy-muted)]">Loading brief…</p>
  }

  if (error || !brief) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-10">
        <Alert tone="error">{error || 'Brief not found'}</Alert>
        <div className="mt-4">
          <Link to="/intake" className="no-underline">
            <Button>Back to intake</Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 px-4 py-10">
      <Card>
        <p className="text-xs uppercase tracking-wide text-[var(--color-navy-muted)]">Decision brief</p>
        <h1 className="mt-2 text-3xl font-bold">Your personalized education brief</h1>
        <p className="mt-3 text-[var(--color-navy-muted)]">{brief.summary}</p>
        <p className="mt-4 rounded-xl bg-[var(--color-accent-soft)] px-4 py-3 text-sm">{brief.verification_notice}</p>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <h2 className="font-semibold">Student goals inferred</h2>
          <ul className="mt-3 list-disc space-y-1 pl-5 text-sm">
            {(brief.student_goals || []).map((g) => (
              <li key={g}>{g}</li>
            ))}
          </ul>
        </Card>
        <Card>
          <h2 className="font-semibold">Recommended next step</h2>
          <p className="mt-3 text-sm text-[var(--color-navy-muted)]">{brief.recommended_next_step}</p>
          {brief.primary_objection && (
            <p className="mt-3 text-sm">
              <span className="font-medium">Primary concern/objection:</span> {brief.primary_objection}
            </p>
          )}
        </Card>
      </div>

      <Card>
        <h2 className="font-semibold">Verified facts (with sources)</h2>
        {brief.verified_facts?.length ? (
          <ul className="mt-4 space-y-4">
            {brief.verified_facts.map((f) => (
              <li key={`${f.source_url}-${f.fact.slice(0, 24)}`} className="rounded-xl border border-[var(--color-border)] p-4 text-sm">
                <p>{f.fact}</p>
                <p className="mt-2 text-xs text-[var(--color-navy-muted)]">
                  Source:{' '}
                  <a href={f.source_url} target="_blank" rel="noreferrer">
                    {f.source_url}
                  </a>{' '}
                  · Verified {f.last_verified_date}
                </p>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-sm text-[var(--color-navy-muted)]">
            No verified public facts matched your question. Please confirm details with NIAT or the
            relevant university.
          </p>
        )}
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <h2 className="font-semibold">Needs confirmation</h2>
          <ul className="mt-3 list-disc space-y-1 pl-5 text-sm">
            {(brief.unresolved_questions || []).map((q) => (
              <li key={q}>{q}</li>
            ))}
          </ul>
        </Card>
        <Card>
          <h2 className="font-semibold">Questions to ask a counsellor</h2>
          <ul className="mt-3 list-disc space-y-1 pl-5 text-sm">
            {(brief.questions_to_ask_counsellor || []).map((q) => (
              <li key={q}>{q}</li>
            ))}
          </ul>
        </Card>
      </div>

      <div className="flex gap-3">
        <Link to="/intake" className="no-underline">
          <Button variant="secondary">Submit another intake</Button>
        </Link>
      </div>
    </div>
  )
}
