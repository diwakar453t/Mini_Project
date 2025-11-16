import { ReactNode, useEffect } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Shield, AlertCircle } from 'lucide-react'

import { useAuth } from '@/hooks/useAuth'
import { cn } from '@/utils/cn'

interface ProtectedRouteProps {
  children: ReactNode
  requiredRole?: 'renter' | 'host' | 'admin'
  requireKYC?: boolean
  fallbackPath?: string
}

const ProtectedRoute = ({
  children,
  requiredRole,
  requireKYC = false,
  fallbackPath = '/auth',
}: ProtectedRouteProps) => {
  const { user, isAuthenticated, isLoading, hasRole, isKYCVerified } = useAuth()
  const location = useLocation()

  // Store intended destination for redirect after login
  useEffect(() => {
    if (!isAuthenticated && !isLoading) {
      localStorage.setItem('chargemitra_redirect', location.pathname + location.search)
    }
  }, [isAuthenticated, isLoading, location])

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-secondary-50">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4"></div>
          <p className="text-gray-600 font-medium">Verifying access...</p>
        </motion.div>
      </div>
    )
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to={fallbackPath} state={{ from: location }} replace />
  }

  // Check role requirements
  if (requiredRole && !hasRole(requiredRole)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-orange-50 px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-md w-full bg-white rounded-xl shadow-lg p-8 text-center"
        >
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Shield className="w-8 h-8 text-red-600" />
          </div>
          
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
          <p className="text-gray-600 mb-6">
            You don't have permission to access this page. 
            {requiredRole === 'host' && ' This page is only available to hosts.'}
            {requiredRole === 'admin' && ' This page is only available to administrators.'}
          </p>
          
          <div className="space-y-3">
            {requiredRole === 'host' && user?.role === 'renter' && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="bg-blue-50 border border-blue-200 rounded-lg p-4"
              >
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <AlertCircle className="w-4 h-4 text-blue-600" />
                  </div>
                  <div className="text-left">
                    <p className="text-sm font-medium text-blue-900 mb-1">
                      Want to become a host?
                    </p>
                    <p className="text-sm text-blue-700 mb-3">
                      Share your charger and start earning money by hosting other EV drivers.
                    </p>
                    <button
                      onClick={() => window.location.href = '/profile#become-host'}
                      className="inline-flex items-center px-3 py-1.5 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors"
                    >
                      Apply to be a Host
                    </button>
                  </div>
                </div>
              </motion.div>
            )}
            
            <button
              onClick={() => window.history.back()}
              className="w-full bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Go Back
            </button>
          </div>
        </motion.div>
      </div>
    )
  }

  // Check KYC requirements
  if (requireKYC && !isKYCVerified()) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-yellow-50 to-orange-50 px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-md w-full bg-white rounded-xl shadow-lg p-8 text-center"
        >
          <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-yellow-600" />
          </div>
          
          <h2 className="text-2xl font-bold text-gray-900 mb-2">KYC Verification Required</h2>
          <p className="text-gray-600 mb-6">
            You need to complete KYC verification to access this page. This helps us ensure 
            the security and trustworthiness of our platform.
          </p>
          
          <div className="space-y-3">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-left">
              <h4 className="font-medium text-blue-900 mb-2">What you'll need:</h4>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• Government-issued photo ID</li>
                <li>• Proof of address</li>
                <li>• Bank account details (for hosts)</li>
              </ul>
            </div>
            
            <button
              onClick={() => window.location.href = '/profile#kyc'}
              className="w-full bg-primary-600 text-white px-4 py-3 rounded-lg hover:bg-primary-700 transition-colors font-medium"
            >
              Complete KYC Verification
            </button>
            
            <button
              onClick={() => window.history.back()}
              className="w-full bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Go Back
            </button>
          </div>
        </motion.div>
      </div>
    )
  }

  // Show inactive account warning
  if (user && !user.is_verified) {
    return (
      <div className="bg-yellow-50 border-b border-yellow-200">
        <div className="max-w-7xl mx-auto py-3 px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between flex-wrap">
            <div className="flex-1 flex items-center">
              <span className="flex p-2 rounded-lg bg-yellow-400">
                <AlertCircle className="h-5 w-5 text-yellow-800" />
              </span>
              <p className="ml-3 font-medium text-yellow-800">
                Your account is not verified. Some features may be limited.{' '}
                <a href="/profile#verify" className="underline">
                  Verify now
                </a>
              </p>
            </div>
          </div>
        </div>
        {children}
      </div>
    )
  }

  // Render protected content
  return <>{children}</>
}

export default ProtectedRoute