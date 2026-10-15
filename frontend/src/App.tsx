import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Navbar } from './components/Navbar'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AuthProvider, useAuth } from './lib/AuthContext'
import { CounsellorPage } from './pages/CounsellorPage'
import { DashboardPage } from './pages/DashboardPage'
import { IntakePage } from './pages/IntakePage'
import { LandingPage } from './pages/LandingPage'
import { LoginPage } from './pages/LoginPage'
import { PrivacyPage } from './pages/PrivacyPage'
import { ReportPage } from './pages/ReportPage'

function AppRoutes() {
  const { signedIn } = useAuth()

  return (
    <>
      <Navbar signedIn={signedIn} />
      <main>
        <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/intake" element={<IntakePage />} />
            <Route path="/report/:id" element={<ReportPage />} />
            <Route path="/privacy" element={<PrivacyPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/counsellor"
              element={
                <ProtectedRoute signedIn={signedIn}>
                  <CounsellorPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute signedIn={signedIn}>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
      </main>
      <footer className="border-t border-[var(--color-border)] py-6 text-center text-xs text-[var(--color-navy-muted)]">
        Independent prototype for educational decision support · Not affiliated with NIAT
      </footer>
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="min-h-screen">
          <AppRoutes />
        </div>
      </AuthProvider>
    </BrowserRouter>
  )
}
