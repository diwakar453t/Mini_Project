import { useState } from 'react'
import { motion } from 'framer-motion'
import { Eye, EyeOff, Zap, Phone, Mail, User, UserCheck } from 'lucide-react'
import toast from 'react-hot-toast'

import { useAuth } from '@/hooks/useAuth'
import { LoginForm, RegisterForm } from '@/types'

const AuthPage = () => {
  const { login, register, isLoggingIn, isRegistering } = useAuth()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [showPassword, setShowPassword] = useState(false)
  
  const [loginData, setLoginData] = useState<LoginForm>({
    email: '',
    password: '',
  })

  const [registerData, setRegisterData] = useState<RegisterForm>({
    name: '',
    email: '',
    password: '',
    phone: '',
    role: 'renter',
  })

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!loginData.email || !loginData.password) {
      toast.error('Please fill in all fields')
      return
    }

    login(loginData)
  }

  const handleRegister = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!registerData.name || !registerData.email || !registerData.password) {
      toast.error('Please fill in all required fields')
      return
    }

    if (registerData.password.length < 6) {
      toast.error('Password must be at least 6 characters long')
      return
    }

    register(registerData)
  }

  const isLoading = isLoggingIn || isRegistering

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-secondary-50 flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-4xl">
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          <div className="md:flex">
            {/* Left Side - Branding */}
            <div className="md:w-1/2 bg-gradient-to-br from-primary-500 to-secondary-500 p-8 md:p-12 text-white">
              <div className="h-full flex flex-col justify-center">
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.8 }}
                >
                  <div className="flex items-center space-x-3 mb-8">
                    <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                      <Zap className="w-6 h-6" />
                    </div>
                    <span className="text-2xl font-bold">ChargeMitra</span>
                  </div>
                  
                  <h2 className="text-3xl md:text-4xl font-bold mb-6">
                    {mode === 'login' 
                      ? 'Welcome back to the future of EV charging' 
                      : 'Join India\'s EV revolution'}
                  </h2>
                  
                  <p className="text-lg opacity-90 mb-8">
                    {mode === 'login'
                      ? 'Sign in to find chargers, manage bookings, and connect with the EV community.'
                      : 'Create your account and start your sustainable journey with thousands of EV enthusiasts.'}
                  </p>

                  <div className="space-y-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                        <Zap className="w-4 h-4" />
                      </div>
                      <span>50+ cities across India</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                        <UserCheck className="w-4 h-4" />
                      </div>
                      <span>KYC-verified trusted network</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                        <Phone className="w-4 h-4" />
                      </div>
                      <span>24/7 customer support</span>
                    </div>
                  </div>
                </motion.div>
              </div>
            </div>

            {/* Right Side - Forms */}
            <div className="md:w-1/2 p-8 md:p-12">
              <motion.div
                key={mode}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5 }}
              >
                {/* Toggle Buttons */}
                <div className="flex bg-gray-100 rounded-xl p-1 mb-8">
                  <button
                    onClick={() => setMode('login')}
                    className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all ${
                      mode === 'login'
                        ? 'bg-white text-gray-900 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    Sign In
                  </button>
                  <button
                    onClick={() => setMode('register')}
                    className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all ${
                      mode === 'register'
                        ? 'bg-white text-gray-900 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    Sign Up
                  </button>
                </div>

                {mode === 'login' ? (
                  /* Login Form */
                  <form onSubmit={handleLogin} className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Email Address
                      </label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <input
                          type="email"
                          required
                          value={loginData.email}
                          onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
                          className="input-field pl-11"
                          placeholder="Enter your email"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Password
                      </label>
                      <div className="relative">
                        <input
                          type={showPassword ? 'text' : 'password'}
                          required
                          value={loginData.password}
                          onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                          className="input-field pr-11"
                          placeholder="Enter your password"
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                        >
                          {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                        </button>
                      </div>
                    </div>

                    <button
                      type="submit"
                      disabled={isLoading}
                      className="w-full btn-primary"
                    >
                      {isLoggingIn ? 'Signing In...' : 'Sign In'}
                    </button>
                  </form>
                ) : (
                  /* Register Form */
                  <form onSubmit={handleRegister} className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Full Name
                      </label>
                      <div className="relative">
                        <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <input
                          type="text"
                          required
                          value={registerData.name}
                          onChange={(e) => setRegisterData({ ...registerData, name: e.target.value })}
                          className="input-field pl-11"
                          placeholder="Enter your full name"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Email Address
                      </label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <input
                          type="email"
                          required
                          value={registerData.email}
                          onChange={(e) => setRegisterData({ ...registerData, email: e.target.value })}
                          className="input-field pl-11"
                          placeholder="Enter your email"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Phone Number (Optional)
                      </label>
                      <div className="relative">
                        <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <input
                          type="tel"
                          value={registerData.phone}
                          onChange={(e) => setRegisterData({ ...registerData, phone: e.target.value })}
                          className="input-field pl-11"
                          placeholder="+91 98765 43210"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Password
                      </label>
                      <div className="relative">
                        <input
                          type={showPassword ? 'text' : 'password'}
                          required
                          value={registerData.password}
                          onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })}
                          className="input-field pr-11"
                          placeholder="Create a strong password"
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                        >
                          {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                        </button>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        Must be at least 6 characters long
                      </p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        I want to...
                      </label>
                      <div className="grid grid-cols-2 gap-3">
                        <label className={`flex items-center p-4 border rounded-lg cursor-pointer transition-all ${
                          registerData.role === 'renter' 
                            ? 'border-primary-500 bg-primary-50 text-primary-700' 
                            : 'border-gray-200 hover:border-gray-300'
                        }`}>
                          <input
                            type="radio"
                            value="renter"
                            checked={registerData.role === 'renter'}
                            onChange={(e) => setRegisterData({ ...registerData, role: e.target.value as 'renter' | 'host' })}
                            className="sr-only"
                          />
                          <div className="text-center w-full">
                            <Zap className="w-6 h-6 mx-auto mb-2" />
                            <div className="font-medium">Book Chargers</div>
                            <div className="text-xs opacity-75">Find and use EV chargers</div>
                          </div>
                        </label>

                        <label className={`flex items-center p-4 border rounded-lg cursor-pointer transition-all ${
                          registerData.role === 'host' 
                            ? 'border-primary-500 bg-primary-50 text-primary-700' 
                            : 'border-gray-200 hover:border-gray-300'
                        }`}>
                          <input
                            type="radio"
                            value="host"
                            checked={registerData.role === 'host'}
                            onChange={(e) => setRegisterData({ ...registerData, role: e.target.value as 'renter' | 'host' })}
                            className="sr-only"
                          />
                          <div className="text-center w-full">
                            <UserCheck className="w-6 h-6 mx-auto mb-2" />
                            <div className="font-medium">Host Chargers</div>
                            <div className="text-xs opacity-75">Share and earn money</div>
                          </div>
                        </label>
                      </div>
                    </div>

                    <button
                      type="submit"
                      disabled={isLoading}
                      className="w-full btn-primary"
                    >
                      {isRegistering ? 'Creating Account...' : 'Create Account'}
                    </button>

                    <p className="text-xs text-center text-gray-500">
                      By creating an account, you agree to our{' '}
                      <a href="/terms" className="text-primary-600 hover:underline">
                        Terms of Service
                      </a>{' '}
                      and{' '}
                      <a href="/privacy" className="text-primary-600 hover:underline">
                        Privacy Policy
                      </a>
                    </p>
                  </form>
                )}

                <div className="mt-8 pt-8 border-t text-center">
                  <p className="text-sm text-gray-600">
                    Need help?{' '}
                    <a href="/help" className="text-primary-600 hover:underline">
                      Contact Support
                    </a>
                  </p>
                </div>
              </motion.div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AuthPage