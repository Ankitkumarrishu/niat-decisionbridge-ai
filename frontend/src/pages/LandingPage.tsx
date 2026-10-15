import { ArrowRight, Brain, LineChart, ShieldCheck } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Button, Card } from '../components/Ui'

export function LandingPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      <div className="grid gap-10 lg:grid-cols-2 lg:items-center">
        <div className="space-y-6">
          <p className="text-sm font-medium uppercase tracking-wide text-[var(--color-navy-muted)]">
            Independent prototype · Track B growth experiment
          </p>
          <h1 className="text-4xl font-bold leading-tight text-[var(--color-navy)] md:text-5xl">
            Help families decide with verified facts, not guesswork.
          </h1>
          <p className="text-lg text-[var(--color-navy-muted)]">
            NIAT DecisionBridge AI turns student and parent questions into sourced decision briefs,
            routes qualified follow-ups to counsellors, and measures experiment outcomes in one
            workflow.
          </p>
          <p className="text-sm text-[var(--color-navy-muted)]">
            This is an independent submission prototype and is not an official NIAT product or
            partnership.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link to="/intake" className="no-underline">
              <Button>
                Start intake <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link to="/counsellor" className="no-underline">
              <Button variant="secondary">Counsellor workspace</Button>
            </Link>
          </div>
        </div>
        <div className="grid gap-4">
          <Card>
            <div className="mb-3 flex items-center gap-2 font-semibold">
              <Brain className="h-5 w-5 text-[var(--color-accent)]" /> AI decision brief
            </div>
            <p className="text-sm text-[var(--color-navy-muted)]">
              Server-side OpenAI generation grounded in a verified public information base with
              source URLs and verification dates.
            </p>
          </Card>
          <Card>
            <div className="mb-3 flex items-center gap-2 font-semibold">
              <ShieldCheck className="h-5 w-5 text-[var(--color-accent)]" /> Consent-first intake
            </div>
            <p className="text-sm text-[var(--color-navy-muted)]">
              Separate storage and follow-up consents, inline validation, and no collection without
              permission.
            </p>
          </Card>
          <Card>
            <div className="mb-3 flex items-center gap-2 font-semibold">
              <LineChart className="h-5 w-5 text-[var(--color-accent)]" /> Growth analytics
            </div>
            <p className="text-sm text-[var(--color-navy-muted)]">
              Funnel, time-series, and control vs treatment cohort views powered by Supabase records.
            </p>
          </Card>
        </div>
      </div>
    </div>
  )
}
