// User types
export interface User {
  id: number
  name: string
  email: string
  phone?: string
  role: 'guest' | 'renter' | 'host' | 'admin'
  is_verified: boolean
  kyc_status: 'pending' | 'submitted' | 'verified' | 'rejected'
  avatar_url?: string
  bio?: string
  city?: string
  state?: string
  host_rating?: string
  host_rating_count?: number
  created_at: string
}

// Charger types
export interface Charger {
  id: number
  title: string
  description?: string
  address: string
  city: string
  state: string
  pincode: string
  latitude: number
  longitude: number
  connector_type: ConnectorType
  charger_type: ChargerType
  max_power_kw: number
  amenities: Record<string, boolean>
  features: Record<string, boolean>
  current_status: ChargerStatus
  is_active: boolean
  is_verified: boolean
  auto_accept_bookings: boolean
  average_rating: number
  rating_count: number
  total_bookings: number
  host_id: number
  cover_image?: string
  images: string[]
  created_at: string
  updated_at: string
  
  // Populated fields
  host?: User
  pricing?: ChargerPricing
  distance?: number // In km, when searching by location
}

export type ConnectorType = 'ccs' | 'chademo' | 'nacs' | 'type2' | 'type1'

export type ChargerType = 'level1' | 'level2' | 'dc_fast'

export type ChargerStatus = 'available' | 'in_use' | 'maintenance' | 'offline' | 'fault'

export interface ChargerPricing {
  id: number
  charger_id: number
  pricing_type: 'per_hour' | 'per_kwh' | 'flat_rate'
  price_value: number
  min_session_minutes: number
  max_session_minutes: number
  peak_hours_start?: string
  peak_hours_end?: string
  peak_price_multiplier: number
  weekend_price_multiplier: number
  booking_fee: number
  overstay_fee_per_hour: number
  late_cancellation_fee: number
  advance_booking_hours: number
  same_day_booking: boolean
}

// Booking types
export interface Booking {
  id: number
  charger_id: number
  renter_id: number
  start_time: string
  end_time: string
  status: BookingStatus
  payment_status: PaymentStatus
  booking_code: string
  total_amount: number
  paid_amount: number
  currency: string
  qr_code_url?: string
  access_code?: string
  vehicle_info?: Record<string, any>
  special_instructions?: string
  created_at: string
  updated_at: string
  
  // Populated fields
  charger?: Charger
  renter?: User
  session?: ChargingSession
  review?: Review
}

export type BookingStatus = 
  | 'pending' 
  | 'confirmed' 
  | 'active' 
  | 'completed' 
  | 'cancelled' 
  | 'failed' 
  | 'no_show' 
  | 'expired'

export type PaymentStatus = 
  | 'pending' 
  | 'processing' 
  | 'completed' 
  | 'failed' 
  | 'refunded' 
  | 'partial_refund'

export interface ChargingSession {
  id: number
  booking_id: number
  session_id: string
  status: SessionStatus
  actual_start_time?: string
  actual_end_time?: string
  actual_duration_minutes: number
  energy_delivered_kwh: number
  peak_power_kw: number
  average_power_kw: number
  total_cost: number
  host_payout: number
  platform_fee: number
}

export type SessionStatus = 
  | 'not_started' 
  | 'active' 
  | 'paused' 
  | 'completed' 
  | 'terminated' 
  | 'error'

// Payment types
export interface PaymentIntent {
  payment_id: string
  order_id?: string
  amount: number
  currency: string
  payment_url?: string
  upi_intent?: string
}

export interface PaymentMethod {
  id: string
  type: 'razorpay' | 'stripe' | 'upi'
  name: string
  description: string
  icon: string
  supported_in_india: boolean
}

// Review types
export interface Review {
  id: number
  booking_id: number
  charger_id: number
  reviewer_id: number
  rating: number
  title?: string
  comment?: string
  charger_condition_rating?: number
  location_rating?: number
  host_communication_rating?: number
  value_for_money_rating?: number
  charging_speed_rating?: number
  positive_aspects: string[]
  negative_aspects: string[]
  host_response?: string
  host_responded_at?: string
  is_verified: boolean
  is_public: boolean
  helpful_count: number
  not_helpful_count: number
  created_at: string
  
  // Populated fields
  reviewer_name: string
  reviewer_avatar?: string
}

// Search and filter types
export interface SearchFilters {
  city?: string
  state?: string
  latitude?: number
  longitude?: number
  radius_km?: number
  connector_type?: ConnectorType
  charger_type?: ChargerType
  min_power_kw?: number
  max_price?: number
  available_now?: boolean
  min_rating?: number
  amenities?: string[]
}

export interface SearchResults {
  chargers: Charger[]
  total: number
  skip: number
  limit: number
  filters: SearchFilters
}

// Map types
export interface MapBounds {
  north: number
  south: number
  east: number
  west: number
}

export interface MapCenter {
  lat: number
  lng: number
}

export interface MarkerCluster {
  id: string
  position: MapCenter
  count: number
  chargers: Charger[]
}

// Notification types
export interface Notification {
  id: string
  type: 'booking' | 'payment' | 'session' | 'review' | 'system'
  title: string
  message: string
  data?: Record<string, any>
  read: boolean
  created_at: string
}

// WebSocket message types
export interface WSMessage {
  type: string
  timestamp: string
  [key: string]: any
}

export interface TelemetryUpdate extends WSMessage {
  type: 'telemetry_update'
  charger_id: number
  power_output_kw: number
  voltage_v?: number
  current_a?: number
  energy_delivered_kwh: number
  session_duration_minutes: number
}

export interface BookingUpdate extends WSMessage {
  type: 'booking_update'
  booking_id: number
  status: BookingStatus
  payment_status?: PaymentStatus
}

export interface ChargerStatusUpdate extends WSMessage {
  type: 'charger_update'
  charger_id: number
  status: ChargerStatus
  is_active: boolean
}

// API Response types
export interface ApiResponse<T> {
  data?: T
  message?: string
  error?: string
  errors?: Record<string, string[]>
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  skip: number
  limit: number
  has_more: boolean
}

// Form types
export interface LoginForm {
  email: string
  password: string
}

export interface RegisterForm {
  name: string
  email: string
  password: string
  phone?: string
  role: 'renter' | 'host'
}

export interface BookingForm {
  charger_id: number
  start_time: string
  end_time: string
  vehicle_info?: Record<string, any>
  special_instructions?: string
}

export interface ReviewForm {
  rating: number
  title?: string
  comment?: string
  charger_condition_rating?: number
  location_rating?: number
  host_communication_rating?: number
  value_for_money_rating?: number
  charging_speed_rating?: number
  positive_aspects?: string[]
  negative_aspects?: string[]
}

// Error types
export interface ApiError {
  message: string
  field?: string
  code?: string
  details?: Record<string, any>
}

export interface ValidationError {
  field: string
  message: string
  code: string
}

// Analytics types
export interface AnalyticsEvent {
  event: string
  category: string
  properties?: Record<string, any>
  user_id?: number
  timestamp?: string
}

// Utility types
export type LoadingState = 'idle' | 'loading' | 'success' | 'error'

export interface AsyncState<T> {
  data?: T
  loading: boolean
  error?: string
}

// Local storage types
export interface StoredAuth {
  token: string
  refreshToken: string
  user: User
  expiresAt: number
}

export interface StoredSearch {
  query: string
  filters: SearchFilters
  results: Charger[]
  timestamp: number
}

// PWA types
export interface InstallPrompt {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}