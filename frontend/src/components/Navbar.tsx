import { GraduationCap, LayoutDashboard, LogIn, LogOut, Users } from 'lucide-react'
import { Link, NavLink } from 'react-router-dom'
import { useAuth } from '../lib/AuthContext'

type Props = {
  signedIn: boolean
}

export function Navbar({ signedIn }: Props) {
  const { signOut } = useAuth()
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `text-sm font-medium ${isActive ? 'text-[var(--color-accent)]' : 'text-[var(--color-navy-muted)] hover:text-[var(--color-navy)]'}`

  return (
    <header className="sticky top-0 z-40 border-b border-[var(--color-border)] bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
        <Link to="/" className="flex items-center gap-2 no-underline">
          <GraduationCap className="h-6 w-6 text-[var(--color-accent)]" />
          <span className="font-semibold text-[var(--color-navy)]">NIAT DecisionBridge AI</span>
        </Link>
        <nav className="flex flex-wrap items-center gap-4">
          <NavLink to="/intake" className={linkClass}>
            Intake
          </NavLink>
          <NavLink to="/counsellor" className={linkClass}>
            <span className="inline-flex items-center gap-1">
              <Users className="h-4 w-4" /> Counsellor
            </span>
          </NavLink>
          <NavLink to="/dashboard" className={linkClass}>
            <span className="inline-flex items-center gap-1">
              <LayoutDashboard className="h-4 w-4" /> Dashboard
            </span>
          </NavLink>
          <NavLink to="/privacy" className={linkClass}>
            Privacy
          </NavLink>
          {signedIn ? (
            <button
              type="button"
              onClick={() => void signOut()}
              className="inline-flex items-center gap-1 rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-sm"
            >
              <LogOut className="h-4 w-4" /> Sign out
            </button>
          ) : (
            <NavLink to="/login" className={linkClass}>
              <span className="inline-flex items-center gap-1">
                <LogIn className="h-4 w-4" /> Sign in
              </span>
            </NavLink>
          )}
        </nav>
      </div>
    </header>
  )
}
