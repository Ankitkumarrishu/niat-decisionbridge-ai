import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'
import { z } from 'zod'
import { Alert, Button, Card } from '../components/Ui'
import { api, ApiError } from '../lib/api'

const schema = z
  .object({
    student_first_name: z.string().min(1, 'First name is required'),
    email: z.string().email('Enter a valid email').optional().or(z.literal('')),
    education_status: z.enum(['completed_class_12', 'in_class_12', 'other']),
    preferred_location: z.string().optional(),
    preferred_campus: z.string().optional(),
    budget_range: z.enum(['undecided', 'below_5_lakh', '5_10_lakh', 'above_10_lakh']),
    primary_concern: z.enum([
      'fees',
      'degree_university',
      'curriculum',
      'placements',
      'campus',
      'admission_eligibility',
      'scholarships',
      'other',
    ]),
    additional_question: z.string().optional(),
    preferred_language: z.enum(['en', 'hi']),
    consent_storage: z.boolean(),
    consent_followup: z.boolean(),
  })
  .superRefine((data, ctx) => {
    if (!data.consent_storage) {
      ctx.addIssue({ code: 'custom', message: 'Storage consent is required', path: ['consent_storage'] })
    }
    if (data.consent_followup && !data.email) {
      ctx.addIssue({
        code: 'custom',
        message: 'Email is required for counsellor follow-up',
        path: ['email'],
      })
    }
  })

type FormValues = z.infer<typeof schema>

const steps = ['Student', 'Preferences', 'Concerns', 'Consent']

const SAVED_LEAD_KEY = 'decisionbridge_lead_id'

export function IntakePage() {
  const [step, setStep] = useState(0)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [savedLeadId, setSavedLeadId] = useState<string | null>(() => sessionStorage.getItem(SAVED_LEAD_KEY))
  const navigate = useNavigate()

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      student_first_name: '',
      email: '',
      education_status: 'in_class_12',
      preferred_location: '',
      preferred_campus: '',
      budget_range: 'undecided',
      primary_concern: 'fees',
      additional_question: '',
      preferred_language: 'en',
      consent_storage: false,
      consent_followup: false,
    },
    mode: 'onBlur',
  })

  const fieldsByStep: (keyof FormValues)[][] = [
    ['student_first_name', 'email', 'education_status', 'preferred_language'],
    ['preferred_location', 'preferred_campus', 'budget_range'],
    ['primary_concern', 'additional_question'],
    ['consent_storage', 'consent_followup'],
  ]

  async function nextStep() {
    const valid = await form.trigger(fieldsByStep[step])
    if (valid) setStep((s) => Math.min(s + 1, steps.length - 1))
  }

  async function onSubmit(values: FormValues) {
    if (submitting) return
    setError(null)
    setSubmitting(true)
    try {
      const payload = {
        ...values,
        email: values.email || undefined,
        preferred_location: values.preferred_location || undefined,
        preferred_campus: values.preferred_campus || undefined,
        additional_question: values.additional_question || undefined,
      }
      let leadId = savedLeadId
      if (!leadId) {
        const intake = await api.submitIntake(payload)
        leadId = intake.lead_id
        sessionStorage.setItem(SAVED_LEAD_KEY, leadId)
        setSavedLeadId(leadId)
      }
      const brief = await api.generateBrief(leadId)
      sessionStorage.removeItem(SAVED_LEAD_KEY)
      setSavedLeadId(null)
      navigate(`/report/${brief.brief_id}`)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('Submission failed. Please try again.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  const { register, formState } = form

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <Card>
        <h1 className="text-2xl font-bold">Student & parent intake</h1>
        <p className="mt-2 text-sm text-[var(--color-navy-muted)]">
          Step {step + 1} of {steps.length}: {steps[step]}
        </p>
        <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full bg-[var(--color-accent)] transition-all"
            style={{ width: `${((step + 1) / steps.length) * 100}%` }}
          />
        </div>

        {error && (
          <div className="mt-4">
            <Alert tone="error">{error}</Alert>
          </div>
        )}
        {savedLeadId && (
          <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-[var(--color-navy-muted)]">
            <p>
              Intake already saved as lead {savedLeadId}. Retrying generates the brief for this lead instead of creating a duplicate.
            </p>
            <button
              type="button"
              className="underline"
              onClick={() => {
                sessionStorage.removeItem(SAVED_LEAD_KEY)
                setSavedLeadId(null)
              }}
            >
              Start a new intake
            </button>
          </div>
        )}

        <form className="mt-6 space-y-4" onSubmit={form.handleSubmit(onSubmit)}>
          {step === 0 && (
            <>
              <Field label="Student first name" error={formState.errors.student_first_name?.message}>
                <input className="mt-1 w-full rounded-xl border border-[var(--color-border)] px-3 py-2" {...register('student_first_name')} />
              </Field>
              <Field label="Email (optional unless follow-up requested)" error={formState.errors.email?.message}>
                <input className="mt-1 w-full rounded-xl border border-[var(--color-border)] px-3 py-2" type="email" {...register('email')} />
              </Field>
              <Field label="Education status">
                <select className="mt-1 w-full rounded-xl border border-[var(--color-border)] px-3 py-2" {...register('education_status')}>
                  <option value="completed_class_12">Completed Class 12</option>
                  <option value="in_class_12">Currently in Class 12</option>
                  <option value="other">Other</option>
                </select>
              </Field>
              <Field label="Preferred language">
                <select className="mt-1 w-full rounded-xl border border-[var(--color-border)] px-3 py-2" {...register('preferred_language')}>
                  <option value="en">English</option>
                  <option value="hi">Hindi</option>
                </select>
              </Field>
            </>
          )}

          {step === 1 && (
            <>
              <Field label="Preferred state or city (optional)">
                <input className="mt-1 w-full rounded-xl border border-[var(--color-border)] px-3 py-2" {...register('preferred_location')} />
              </Field>
              <Field label="Preferred university or campus (optional)">
                <input className="mt-1 w-full rounded-xl border border-[var(--color-border)] px-3 py-2" {...register('preferred_campus')} />
              </Field>
              <Field label="Budget range">
                <select className="mt-1 w-full rounded-xl border border-[var(--color-border)] px-3 py-2" {...register('budget_range')}>
                  <option value="undecided">Undecided</option>
                  <option value="below_5_lakh">Below ₹5 lakh</option>
                  <option value="5_10_lakh">₹5–10 lakh</option>
                  <option value="above_10_lakh">Above ₹10 lakh</option>
                </select>
              </Field>
            </>
          )}

          {step === 2 && (
            <>
              <Field label="Primary concern">
                <select className="mt-1 w-full rounded-xl border border-[var(--color-border)] px-3 py-2" {...register('primary_concern')}>
                  <option value="fees">Fees</option>
                  <option value="degree_university">Degree-awarding university</option>
                  <option value="curriculum">Curriculum</option>
                  <option value="placements">Placements</option>
                  <option value="campus">Campus</option>
                  <option value="admission_eligibility">Admission eligibility</option>
                  <option value="scholarships">Scholarships</option>
                  <option value="other">Other</option>
                </select>
              </Field>
              <Field label="Additional question or concern">
                <textarea className="mt-1 min-h-28 w-full rounded-xl border border-[var(--color-border)] px-3 py-2" {...register('additional_question')} />
              </Field>
            </>
          )}

          {step === 3 && (
            <>
              <label className="flex items-start gap-3 text-sm">
                <input type="checkbox" className="mt-1" {...register('consent_storage')} />
                <span>
                  I consent to storing my responses so DecisionBridge can generate a personalized
                  brief. (Required)
                </span>
              </label>
              {formState.errors.consent_storage && (
                <p className="text-sm text-red-600">{formState.errors.consent_storage.message}</p>
              )}
              <label className="flex items-start gap-3 text-sm">
                <input type="checkbox" className="mt-1" {...register('consent_followup')} />
                <span>
                  I consent to a counsellor follow-up about my questions. Email becomes required if
                  checked.
                </span>
              </label>
              <p className="text-xs text-[var(--color-navy-muted)]">
                We do not collect phone numbers, passwords, identity documents, or payment details in
                this prototype.
              </p>
            </>
          )}

          <div className="flex flex-wrap justify-between gap-3 pt-4">
            <Button variant="secondary" disabled={step === 0 || submitting} onClick={() => setStep((s) => s - 1)}>
              Back
            </Button>
            {step < steps.length - 1 ? (
              <Button onClick={nextStep}>Next</Button>
            ) : (
              <Button type="submit" loading={submitting}>
                Submit & generate brief
              </Button>
            )}
          </div>
        </form>
      </Card>
    </div>
  )
}

function Field({
  label,
  error,
  children,
}: {
  label: string
  error?: string
  children: React.ReactNode
}) {
  return (
    <label className="block text-sm font-medium">
      {label}
      {children}
      {error && <span className="mt-1 block text-red-600">{error}</span>}
    </label>
  )
}
