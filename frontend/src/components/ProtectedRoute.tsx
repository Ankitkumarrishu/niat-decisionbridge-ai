import { Navigate, useLocation } from 'react-router-dom'

type Props = {
  signedIn: boolean
  children: React.ReactNode
}

export function ProtectedRoute({ signedIn, children }: Props) {
  const location = useLocation()
  if (!signedIn) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }
  return <>{children}</>
}
