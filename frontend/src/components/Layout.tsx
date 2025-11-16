import { ReactNode, useState, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Menu,
  X,
  Zap,
  Search,
  Calendar,
  User,
  Settings,
  LogOut,
  Bell,
  Home,
  MapPin,
  Car,
  Shield,
} from 'lucide-react'

import { useAuth } from '@/hooks/useAuth'
import { cn } from '@/utils/cn'

interface LayoutProps {
  children: ReactNode
}

const Layout = ({ children }: LayoutProps) => {
  const { user, isAuthenticated, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false)
  const [notifications, setNotifications] = useState(0)

  // Close mobile menu on route change
  useEffect(() => {
    setIsMobileMenuOpen(false)
    setIsProfileMenuOpen(false)
  }, [location.pathname])

  // Navigation items
  const navItems = [
    { name: 'Find Chargers', href: '/search', icon: Search },
    { name: 'My Bookings', href: '/bookings', icon: Calendar, authRequired: true },
    ...(user?.role === 'host' ? [{ name: 'Host Dashboard', href: '/host', icon: Zap }] : []),
    ...(user?.role === 'admin' ? [{ name: 'Admin', href: '/admin', icon: Shield }] : []),
  ]

  // Mobile bottom navigation items
  const bottomNavItems = [
    { name: 'Home', href: '/', icon: Home },
    { name: 'Search', href: '/search', icon: Search },
    { name: 'Bookings', href: '/bookings', icon: Calendar, authRequired: true },
    { name: 'Profile', href: '/profile', icon: User, authRequired: true },
  ]

  const isCurrentPath = (path: string) => {
    if (path === '/') {
      return location.pathname === '/'
    }
    return location.pathname.startsWith(path)
  }

  const handleAuthAction = () => {
    if (isAuthenticated) {
      setIsProfileMenuOpen(!isProfileMenuOpen)
    } else {
      navigate('/auth')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <Link
              to="/"
              className="flex items-center space-x-2 text-xl font-bold text-primary-600"
            >
              <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-lg flex items-center justify-center">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <span className="hidden sm:block">ChargeMitra</span>
            </Link>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center space-x-8">
              {navItems.map((item) => {
                if (item.authRequired && !isAuthenticated) return null
                
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={cn(
                      'flex items-center space-x-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                      isCurrentPath(item.href)
                        ? 'text-primary-600 bg-primary-50'
                        : 'text-gray-600 hover:text-primary-600 hover:bg-gray-50'
                    )}
                  >
                    <item.icon className="w-4 h-4" />
                    <span>{item.name}</span>
                  </Link>
                )
              })}
            </nav>

            {/* Desktop User Menu */}
            <div className="hidden md:flex items-center space-x-4">
              {isAuthenticated && (
                <button className="p-2 text-gray-600 hover:text-primary-600 relative">
                  <Bell className="w-5 h-5" />
                  {notifications > 0 && (
                    <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                      {notifications}
                    </span>
                  )}
                </button>
              )}

              <div className="relative">
                <button
                  onClick={handleAuthAction}
                  className={cn(
                    'flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                    isAuthenticated
                      ? 'text-gray-700 hover:bg-gray-50'
                      : 'bg-primary-500 text-white hover:bg-primary-600'
                  )}
                >
                  {isAuthenticated ? (
                    <>
                      {user?.avatar_url ? (
                        <img
                          src={user.avatar_url}
                          alt={user.name}
                          className="w-6 h-6 rounded-full"
                        />
                      ) : (
                        <User className="w-4 h-4" />
                      )}
                      <span>{user?.name}</span>
                    </>
                  ) : (
                    <span>Sign In</span>
                  )}
                </button>

                {/* Profile Dropdown */}
                <AnimatePresence>
                  {isProfileMenuOpen && isAuthenticated && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border py-2 z-50"
                    >
                      <Link
                        to="/profile"
                        className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                      >
                        <User className="w-4 h-4" />
                        <span>Profile</span>
                      </Link>
                      <Link
                        to="/profile#settings"
                        className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                      >
                        <Settings className="w-4 h-4" />
                        <span>Settings</span>
                      </Link>
                      <hr className="my-2" />
                      <button
                        onClick={logout}
                        className="w-full flex items-center space-x-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                      >
                        <LogOut className="w-4 h-4" />
                        <span>Sign Out</span>
                      </button>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="md:hidden p-2 text-gray-600 hover:text-primary-600"
            >
              {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        <AnimatePresence>
          {isMobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="md:hidden bg-white border-t"
            >
              <div className="px-4 py-2 space-y-1">
                {navItems.map((item) => {
                  if (item.authRequired && !isAuthenticated) return null
                  
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={cn(
                        'flex items-center space-x-3 px-3 py-3 rounded-lg text-sm font-medium',
                        isCurrentPath(item.href)
                          ? 'text-primary-600 bg-primary-50'
                          : 'text-gray-600'
                      )}
                    >
                      <item.icon className="w-5 h-5" />
                      <span>{item.name}</span>
                    </Link>
                  )
                })}

                {!isAuthenticated && (
                  <Link
                    to="/auth"
                    className="flex items-center space-x-3 px-3 py-3 text-sm font-medium text-primary-600"
                  >
                    <User className="w-5 h-5" />
                    <span>Sign In</span>
                  </Link>
                )}

                {isAuthenticated && (
                  <>
                    <hr className="my-2" />
                    <Link
                      to="/profile"
                      className="flex items-center space-x-3 px-3 py-3 rounded-lg text-sm text-gray-600"
                    >
                      <User className="w-5 h-5" />
                      <span>Profile</span>
                    </Link>
                    <button
                      onClick={logout}
                      className="w-full flex items-center space-x-3 px-3 py-3 text-sm text-red-600"
                    >
                      <LogOut className="w-5 h-5" />
                      <span>Sign Out</span>
                    </button>
                  </>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </header>

      {/* Main Content */}
      <main className="pb-16 md:pb-0">
        {children}
      </main>

      {/* Mobile Bottom Navigation */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t z-40 safe-area-pb">
        <nav className="flex items-center justify-around py-2">
          {bottomNavItems.map((item) => {
            if (item.authRequired && !isAuthenticated) return null
            
            const isActive = isCurrentPath(item.href)
            
            return (
              <Link
                key={item.name}
                to={item.href}
                className={cn(
                  'flex flex-col items-center py-2 px-3 min-w-0 flex-1',
                  isActive ? 'text-primary-600' : 'text-gray-600'
                )}
              >
                <item.icon className="w-5 h-5 mb-1" />
                <span className="text-xs font-medium truncate">{item.name}</span>
              </Link>
            )
          })}

          {!isAuthenticated && (
            <Link
              to="/auth"
              className="flex flex-col items-center py-2 px-3 min-w-0 flex-1 text-gray-600"
            >
              <User className="w-5 h-5 mb-1" />
              <span className="text-xs font-medium">Sign In</span>
            </Link>
          )}
        </nav>
      </div>

      {/* Click outside to close menus */}
      {(isMobileMenuOpen || isProfileMenuOpen) && (
        <div
          className="fixed inset-0 z-30"
          onClick={() => {
            setIsMobileMenuOpen(false)
            setIsProfileMenuOpen(false)
          }}
        />
      )}
    </div>
  )
}

import ThemeToggle from './ThemeToggle'

export default Layout