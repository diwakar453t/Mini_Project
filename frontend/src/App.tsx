import { Routes, Route, Navigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useLocation } from 'react-router-dom'

// Pages
import HomePage from '@/pages/HomePage'
import SearchPage from '@/pages/SearchPage'
import ChargerDetailsPage from '@/pages/ChargerDetailsPage'
import BookingPage from '@/pages/BookingPage'
import BookingsListPage from '@/pages/BookingsListPage'
import ProfilePage from '@/pages/ProfilePage'
import HostDashboard from '@/pages/HostDashboard'
import AdminDashboard from '@/pages/AdminDashboard'
import AuthPage from '@/pages/AuthPage'
import DummyPaymentPage from '@/pages/DummyPaymentPage'
import NotFoundPage from '@/pages/NotFoundPage'

// Components
import Layout from '@/components/Layout'
import ProtectedRoute from '@/components/ProtectedRoute'

// Hooks
import { useAuth } from '@/hooks/useAuth'

// Animation variants for page transitions
const pageVariants = {
  initial: {
    opacity: 0,
    x: 20,
  },
  animate: {
    opacity: 1,
    x: 0,
    transition: {
      duration: 0.3,
      ease: 'easeOut',
    },
  },
  exit: {
    opacity: 0,
    x: -20,
    transition: {
      duration: 0.2,
      ease: 'easeIn',
    },
  },
}

function App() {
  const location = useLocation()
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-secondary-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4"></div>
          <p className="text-gray-600 font-medium">Loading ChargeMitra...</p>
        </div>
      </div>
    )
  }

  return (
    <Layout>
      <AnimatePresence mode="wait" initial={false}>
        <motion.div
          key={location.pathname}
          variants={pageVariants}
          initial="initial"
          animate="animate"
          exit="exit"
          className="min-h-screen"
        >
          <Routes location={location}>
            {/* Public Routes */}
            <Route path="/" element={<HomePage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/chargers/:id" element={<ChargerDetailsPage />} />
            <Route path="/auth" element={<AuthPage />} />
            <Route path="/payments/dummy" element={<DummyPaymentPage />} />
            
            {/* Protected Routes */}
            <Route
              path="/booking/:chargerId"
              element={
                <ProtectedRoute>
                  <BookingPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/bookings"
              element={
                <ProtectedRoute>
                  <BookingsListPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/bookings/:id"
              element={
                <ProtectedRoute>
                  <BookingPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <ProfilePage />
                </ProtectedRoute>
              }
            />
            
            {/* Host Routes */}
            <Route
              path="/host"
              element={
                <ProtectedRoute requiredRole="host">
                  <HostDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/host/*"
              element={
                <ProtectedRoute requiredRole="host">
                  <HostDashboard />
                </ProtectedRoute>
              }
            />
            
            {/* Admin Routes */}
            <Route
              path="/admin"
              element={
                <ProtectedRoute requiredRole="admin">
                  <AdminDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/*"
              element={
                <ProtectedRoute requiredRole="admin">
                  <AdminDashboard />
                </ProtectedRoute>
              }
            />
            
            {/* Redirects */}
            <Route 
              path="/login" 
              element={<Navigate to="/auth" replace />} 
            />
            <Route 
              path="/register" 
              element={<Navigate to="/auth" replace />} 
            />
            
            {/* 404 */}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </motion.div>
      </AnimatePresence>
    </Layout>
  )
}

export default App