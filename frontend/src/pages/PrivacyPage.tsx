import { Card } from '../components/Ui'

export function PrivacyPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <Card className="space-y-4 text-sm leading-relaxed text-[var(--color-navy-muted)]">
        <h1 className="text-2xl font-bold text-[var(--color-navy)]">Privacy & prototype notice</h1>
        <p>
          NIAT DecisionBridge AI is an independent growth-experiment prototype. It is not an official
          NIAT product, and this page describes how the demo handles information.
        </p>
        <h2 className="text-lg font-semibold text-[var(--color-navy)]">What we collect</h2>
        <ul className="list-disc space-y-2 pl-5">
          <li>Student first name, optional email, education status, preferences, concerns, and language.</li>
          <li>Separate explicit consents for storage and counsellor follow-up.</li>
          <li>Counsellor notes and CRM status updates entered by authenticated staff.</li>
        </ul>
        <h2 className="text-lg font-semibold text-[var(--color-navy)]">What we do not collect</h2>
        <ul className="list-disc space-y-2 pl-5">
          <li>Phone numbers (unless you later add an optional, consented field).</li>
          <li>Passwords for students, identity documents, or financial account details.</li>
        </ul>
        <h2 className="text-lg font-semibold text-[var(--color-navy)]">How data is used</h2>
        <p>
          With storage consent, intake data is stored in Supabase to generate an AI decision brief
          using verified public reference documents. OpenAI processes the question and retrieved
          snippets server-side; API keys never reach the browser.
        </p>
        <p>
          Follow-up consent creates an internal CRM event for counsellors. This prototype does not
          send email, WhatsApp, or phone messages unless you integrate those services separately.
        </p>
        <h2 className="text-lg font-semibold text-[var(--color-navy)]">Demo data</h2>
        <p>
          Seeded records are synthetic, marked <code>is_demo=true</code>, and use{' '}
          <code>@example.invalid</code> emails. They must not be presented as real NIAT performance.
        </p>
      </Card>
    </div>
  )
}
