import { useState, useEffect, useCallback } from 'react'
import confetti from 'canvas-confetti'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'

import apiService from '@/services/api'
import { User, LoginForm, RegisterForm } from '@/types'

interface AuthState {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  error: string | null
}

export function useAuth() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isLoading: true,
    isAuthenticated: false,
    error: null,
  })

  // Query to get current user
  const {
    data: user,
    isLoading: userLoading,
    error: userError,
    refetch: refetchUser,
  } = useQuery(
    ['user', 'me'],
    apiService.getCurrentUser,
    {
      enabled: !!localStorage.getItem('chargemitra_auth'),
      retry: false,
      onSuccess: (userData) => {
        setAuthState({
          user: userData,
          isLoading: false,
          isAuthenticated: true,
          error: null,
        })
      },
      onError: (error: any) => {
        console.error('Failed to get user:', error)
        setAuthState({
          user: null,
          isLoading: false,
          isAuthenticated: false,
          error: error.message,
        })
        
        // Clear invalid auth data
        apiService.clearAuth()
      },
    }
  )

  // Login mutation
  const loginMutation = useMutation(
    ({ email, password }: LoginForm) => apiService.login(email, password),
    {
      onSuccess: (data) => {
        toast.success('Welcome back!')
        
        // Refetch user data
        refetchUser()
        
        // Navigate to intended destination or dashboard
        const redirectTo = localStorage.getItem('chargemitra_redirect') || '/'
        localStorage.removeItem('chargemitra_redirect')
        navigate(redirectTo, { replace: true })
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.message || 'Login failed')
      },
    }
  )

  // Register mutation
  const registerMutation = useMutation(
    (userData: RegisterForm) => apiService.register(userData),
    {
      onSuccess: (data) => {
        toast.success('Account created successfully!')
        
        // Refetch user data
        refetchUser()
        
        // Navigate to dashboard
        navigate('/', { replace: true })
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.message || 'Registration failed')
      },
    }
  )

  // Logout mutation
  const logoutMutation = useMutation(
    apiService.logout,
    {
      onSuccess: () => {
        // Clear all cached data
        queryClient.clear()
        
        setAuthState({
          user: null,
          isLoading: false,
          isAuthenticated: false,
          error: null,
        })
        
        toast.success('Logged out successfully')
        navigate('/', { replace: true })
      },
      onError: (error: any) => {
        console.error('Logout error:', error)
        // Still clear auth even if logout request fails
        queryClient.clear()
        apiService.clearAuth()
        
        setAuthState({
          user: null,
          isLoading: false,
          isAuthenticated: false,
          error: null,
        })
        
        navigate('/', { replace: true })
      },
    }
  )

  // Login function
  const login = useCallback(
    (credentials: LoginForm) => {
      loginMutation.mutate(credentials)
    },
    [loginMutation]
  )

  // Register function
  const register = useCallback(
    (userData: RegisterForm) => {
      registerMutation.mutate(userData)
    },
    [registerMutation]
  )

  // Logout function
  const logout = useCallback(() => {
    logoutMutation.mutate()
  }, [logoutMutation])

  // Check if user has specific role
  const hasRole = useCallback(
    (role: string | string[]) => {
      if (!user) return false
      
      if (Array.isArray(role)) {
        return role.includes(user.role)
      }
      
      return user.role === role
    },
    [user]
  )

  // Check if user is host
  const isHost = useCallback(() => {
    return hasRole(['host', 'admin'])
  }, [hasRole])

  // Check if user is admin
  const isAdmin = useCallback(() => {
    return hasRole('admin')
  }, [hasRole])

  // Check if user is verified
  const isVerified = useCallback(() => {
    return user?.is_verified || false
  }, [user])

  // Check if user has completed KYC
  const isKYCVerified = useCallback(() => {
    return user?.kyc_status === 'verified'
  }, [user])

  // Update auth state when localStorage changes (for cross-tab sync)
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'chargemitra_auth') {
        if (!e.newValue) {
          // Auth was cleared in another tab
          setAuthState({
            user: null,
            isLoading: false,
            isAuthenticated: false,
            error: null,
          })
          queryClient.clear()
        } else {
          // Auth was updated in another tab
          refetchUser()
        }
      }
    }

    window.addEventListener('storage', handleStorageChange)
    return () => window.removeEventListener('storage', handleStorageChange)
  }, [queryClient, refetchUser])

  // Check for stored auth on mount
  useEffect(() => {
    const storedAuth = localStorage.getItem('chargemitra_auth')
    if (!storedAuth) {
      setAuthState({
        user: null,
        isLoading: false,
        isAuthenticated: false,
        error: null,
      })
    }
  }, [])

  return {
    // State
    user: authState.user,
    isLoading: authState.isLoading || userLoading,
    isAuthenticated: authState.isAuthenticated,
    error: authState.error || userError,
    
    // Actions
    login,
    register,
    logout,
    refetchUser,
    
    // Permissions
    hasRole,
    isHost,
    isAdmin,
    isVerified,
    isKYCVerified,
    
    // Mutation states
    isLoggingIn: loginMutation.isLoading,
    isRegistering: registerMutation.isLoading,
    isLoggingOut: logoutMutation.isLoading,
    
    // Errors
    loginError: loginMutation.error,
    registerError: registerMutation.error,
    logoutError: logoutMutation.error,
  }
}

export default useAuth