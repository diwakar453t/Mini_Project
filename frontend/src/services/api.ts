import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import toast from 'react-hot-toast'
import { ApiResponse, ApiError } from '@/types'

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const API_VERSION = '/api/v1'

class ApiService {
  private client: AxiosInstance
  private authToken: string | null = null

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE_URL}${API_VERSION}`,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        if (this.authToken) {
          config.headers.Authorization = `Bearer ${this.authToken}`
        }

        // Add request ID for debugging
        config.headers['X-Request-ID'] = this.generateRequestId()

        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        return response
      },
      async (error) => {
        const originalRequest = error.config

        // Handle 401 unauthorized
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true
          
          try {
            await this.refreshToken()
            return this.client(originalRequest)
          } catch (refreshError) {
            this.clearAuth()
            window.location.href = '/auth'
            return Promise.reject(refreshError)
          }
        }

        // Handle other errors
        this.handleError(error)
        return Promise.reject(error)
      }
    )

    // Load token from localStorage on initialization
    this.loadAuthFromStorage()
  }

  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  private loadAuthFromStorage() {
    try {
      const storedAuth = localStorage.getItem('chargemitra_auth')
      if (storedAuth) {
        const authData = JSON.parse(storedAuth)
        if (authData.expiresAt > Date.now()) {
          this.setAuthToken(authData.token)
        } else {
          this.clearAuth()
        }
      }
    } catch (error) {
      console.error('Failed to load auth from storage:', error)
      this.clearAuth()
    }
  }

  private handleError(error: any) {
    if (error.response) {
      // Server responded with error status
      const status = error.response.status
      const message = error.response.data?.message || error.response.data?.detail || 'An error occurred'

      switch (status) {
        case 400:
          toast.error(message)
          break
        case 403:
          toast.error('Access denied')
          break
        case 404:
          toast.error('Resource not found')
          break
        case 422:
          // Validation errors
          if (error.response.data?.errors) {
            const errors = error.response.data.errors
            Object.values(errors).forEach((errorList: any) => {
              if (Array.isArray(errorList)) {
                errorList.forEach((err: string) => toast.error(err))
              }
            })
          } else {
            toast.error(message)
          }
          break
        case 429:
          toast.error('Too many requests. Please try again later.')
          break
        case 500:
          toast.error('Server error. Please try again.')
          break
        default:
          toast.error(message)
      }
    } else if (error.request) {
      // Network error
      toast.error('Network error. Please check your connection.')
    } else {
      // Other error
      toast.error('An unexpected error occurred')
    }
  }

  setAuthToken(token: string) {
    this.authToken = token
  }

  clearAuth() {
    this.authToken = null
    localStorage.removeItem('chargemitra_auth')
  }

  // Generic API methods
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config)
    return response.data
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(url, data, config)
    return response.data
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<T>(url, data, config)
    return response.data
  }

  async patch<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.patch<T>(url, data, config)
    return response.data
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(url, config)
    return response.data
  }

  // Authentication API
  async login(email: string, password: string) {
    const formData = new FormData()
    formData.append('username', email)
    formData.append('password', password)

    const response = await this.client.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })

    const { access_token, refresh_token } = response.data
    
    // Store auth data
    const authData = {
      token: access_token,
      refreshToken: refresh_token,
      expiresAt: Date.now() + 24 * 60 * 60 * 1000, // 24 hours
    }
    
    localStorage.setItem('chargemitra_auth', JSON.stringify(authData))
    this.setAuthToken(access_token)

    return response.data
  }

  async register(userData: {
    name: string
    email: string
    password: string
    phone?: string
    role: string
  }) {
    const response = await this.client.post('/auth/register', userData)
    
    const { access_token, refresh_token } = response.data
    
    // Store auth data
    const authData = {
      token: access_token,
      refreshToken: refresh_token,
      expiresAt: Date.now() + 24 * 60 * 60 * 1000,
    }
    
    localStorage.setItem('chargemitra_auth', JSON.stringify(authData))
    this.setAuthToken(access_token)

    return response.data
  }

  async refreshToken() {
    const storedAuth = localStorage.getItem('chargemitra_auth')
    if (!storedAuth) {
      throw new Error('No refresh token available')
    }

    const authData = JSON.parse(storedAuth)
    const response = await this.client.post('/auth/refresh', {
      refresh_token: authData.refreshToken,
    })

    const { access_token, refresh_token } = response.data
    
    // Update stored auth data
    const newAuthData = {
      token: access_token,
      refreshToken: refresh_token,
      expiresAt: Date.now() + 24 * 60 * 60 * 1000,
    }
    
    localStorage.setItem('chargemitra_auth', JSON.stringify(newAuthData))
    this.setAuthToken(access_token)

    return response.data
  }

  async logout() {
    try {
      await this.client.post('/auth/logout')
    } catch (error) {
      // Ignore logout errors
    } finally {
      this.clearAuth()
    }
  }

  async getCurrentUser() {
    return this.get('/users/me')
  }

  // Charger API
  async searchChargers(params: any) {
    const searchParams = new URLSearchParams()
    Object.keys(params).forEach(key => {
      if (params[key] !== undefined && params[key] !== null) {
        if (Array.isArray(params[key])) {
          params[key].forEach((value: any) => {
            searchParams.append(key, value.toString())
          })
        } else {
          searchParams.append(key, params[key].toString())
        }
      }
    })
    
    return this.get(`/chargers?${searchParams.toString()}`)
  }

  async getCharger(id: number) {
    return this.get(`/chargers/${id}`)
  }

  async createCharger(chargerData: any) {
    return this.post('/chargers', chargerData)
  }

  async updateCharger(id: number, chargerData: any) {
    return this.patch(`/chargers/${id}`, chargerData)
  }

  async deleteCharger(id: number) {
    return this.delete(`/chargers/${id}`)
  }

  async getChargerPricing(chargerId: number) {
    return this.get(`/chargers/${chargerId}/pricing`)
  }

  async setChargerPricing(chargerId: number, pricingData: any) {
    return this.post(`/chargers/${chargerId}/pricing`, pricingData)
  }

  // Booking API
  async createBooking(bookingData: any) {
    return this.post('/bookings', bookingData)
  }

  async getBookings(params?: any) {
    const searchParams = new URLSearchParams(params)
    return this.get(`/bookings?${searchParams.toString()}`)
  }

  async getBooking(id: number) {
    return this.get(`/bookings/${id}`)
  }

  async updateBooking(id: number, updates: any) {
    return this.patch(`/bookings/${id}`, updates)
  }

  async cancelBooking(id: number, reason: string) {
    return this.post(`/bookings/${id}/cancel`, { reason })
  }

  async checkinBooking(id: number) {
    return this.post(`/bookings/${id}/checkin`)
  }

  // Payment API
  async createPayment(bookingId: number, paymentMethod: string) {
    return this.post('/payments/create', {
      booking_id: bookingId,
      payment_method: paymentMethod,
    })
  }

  async confirmPayment(paymentData: any) {
    return this.post('/payments/confirm', paymentData)
  }

  async requestRefund(bookingId: number, amount?: number, reason?: string) {
    return this.post('/payments/refund', {
      booking_id: bookingId,
      amount,
      reason,
    })
  }

  // Review API
  async createReview(bookingId: number, reviewData: any) {
    return this.post(`/reviews/bookings/${bookingId}/review`, reviewData)
  }

  async getChargerReviews(chargerId: number, params?: any) {
    const searchParams = new URLSearchParams(params)
    return this.get(`/reviews/chargers/${chargerId}/reviews?${searchParams.toString()}`)
  }

  async addHostResponse(reviewId: number, response: string) {
    return this.post(`/reviews/${reviewId}/response`, { response })
  }

  async markReviewHelpful(reviewId: number, helpful: boolean) {
    return this.post(`/reviews/${reviewId}/helpful`, { helpful })
  }

  // File Upload API
  async uploadFile(file: File, type: 'avatar' | 'charger' | 'kyc' = 'avatar') {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('type', type)

    return this.post('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  }

  // WebSocket connection helper
  createWebSocket(path: string): WebSocket {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsHost = API_BASE_URL.replace(/^https?:/, '').replace('//', '')
    const token = this.authToken
    
    return new WebSocket(`${wsProtocol}//${wsHost}${API_VERSION}/ws${path}?token=${token}`)
  }
}

// Create singleton instance
const apiService = new ApiService()
export default apiService

// Export specific methods for convenience
export const {
  login,
  register,
  logout,
  getCurrentUser,
  searchChargers,
  getCharger,
  createCharger,
  updateCharger,
  deleteCharger,
  getChargerPricing,
  setChargerPricing,
  createBooking,
  getBookings,
  getBooking,
  updateBooking,
  cancelBooking,
  checkinBooking,
  createPayment,
  confirmPayment,
  requestRefund,
  createReview,
  getChargerReviews,
  addHostResponse,
  markReviewHelpful,
  uploadFile,
} = apiService