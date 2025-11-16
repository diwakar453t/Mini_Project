import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Calendar,
  Clock,
  Zap,
  Car,
  CreditCard,
  MapPin,
  Star,
  AlertCircle,
  CheckCircle,
  ArrowLeft,
  ArrowRight,
  QrCode,
  Share2,
  Download
} from 'lucide-react'
import { format, addDays, isAfter, isBefore, addMinutes, differenceInMinutes } from 'date-fns'
import toast from 'react-hot-toast'

import { Charger, Booking, BookingForm } from '@/types'
import { useAuth } from '@/hooks/useAuth'
import { cn } from '@/utils/cn'

interface BookingFlowProps {
  charger: Charger
  onClose: () => void
  onBookingComplete: (booking: Booking) => void
}

interface TimeSlot {
  start: Date
  end: Date
  available: boolean
  price?: number
}

interface PriceEstimate {
  duration_hours: number
  energy_estimate_kwh: number
  subtotal: number
  platform_fee: number
  booking_fee: number
  total: number
  pricing_type: string
  unit_price: number
}

interface BookingStep {
  id: string
  title: string
  completed: boolean
}

const BookingFlow = ({ charger, onClose, onBookingComplete }: BookingFlowProps) => {
  const { user } = useAuth()
  const [currentStep, setCurrentStep] = useState(0)
  const [isLoading, setIsLoading] = useState(false)
  
  // Booking data
  const [selectedDate, setSelectedDate] = useState<Date>(new Date())
  const [startTime, setStartTime] = useState<string>('')
  const [endTime, setEndTime] = useState<string>('')
  const [vehicleInfo, setVehicleInfo] = useState({
    type: '',
    batteryCapacity: '',
    currentCharge: '',
    targetCharge: ''
  })
  const [specialInstructions, setSpecialInstructions] = useState('')
  const [priceEstimate, setPriceEstimate] = useState<PriceEstimate | null>(null)
  const [availableSlots, setAvailableSlots] = useState<TimeSlot[]>([])
  const [completedBooking, setCompletedBooking] = useState<Booking | null>(null)

  const steps: BookingStep[] = [
    { id: 'datetime', title: 'Select Time', completed: false },
    { id: 'details', title: 'Booking Details', completed: false },
    { id: 'payment', title: 'Payment', completed: false },
    { id: 'confirmation', title: 'Confirmation', completed: false }
  ]

  // Generate time slots for the selected date
  const generateTimeSlots = useCallback((date: Date) => {
    const slots: TimeSlot[] = []
    const start = new Date(date)
    start.setHours(6, 0, 0, 0) // Start at 6 AM
    
    const end = new Date(date)
    end.setHours(22, 0, 0, 0) // End at 10 PM

    // Generate 30-minute slots
    let current = new Date(start)
    while (current < end) {
      const slotEnd = addMinutes(current, 30)
      
      // Mock availability - in real app, check against existing bookings
      const available = Math.random() > 0.3 // 70% chance of being available
      
      slots.push({
        start: new Date(current),
        end: slotEnd,
        available
      })
      
      current = slotEnd
    }
    
    return slots
  }, [])

  // Load available slots when date changes
  useEffect(() => {
    const slots = generateTimeSlots(selectedDate)
    setAvailableSlots(slots)
  }, [selectedDate, generateTimeSlots])

  // Calculate price estimate when time selection changes
  useEffect(() => {
    if (startTime && endTime && charger.pricing) {
      calculatePriceEstimate()
    }
  }, [startTime, endTime, vehicleInfo])

  const calculatePriceEstimate = useCallback(() => {
    if (!startTime || !endTime || !charger.pricing) return

    const start = new Date(`${format(selectedDate, 'yyyy-MM-dd')}T${startTime}`)
    const end = new Date(`${format(selectedDate, 'yyyy-MM-dd')}T${endTime}`)
    
    if (end <= start) {
      toast.error('End time must be after start time')
      return
    }

    const durationHours = differenceInMinutes(end, start) / 60
    const minDuration = (charger.pricing.min_session_minutes || 30) / 60
    const maxDuration = (charger.pricing.max_session_minutes || 480) / 60

    if (durationHours < minDuration) {
      toast.error(`Minimum session duration is ${minDuration} hours`)
      return
    }

    if (durationHours > maxDuration) {
      toast.error(`Maximum session duration is ${maxDuration} hours`)
      return
    }

    let subtotal = 0
    let energyEstimate = 0

    if (charger.pricing.pricing_type === 'per_hour') {
      subtotal = durationHours * charger.pricing.price_value
      energyEstimate = durationHours * charger.max_power_kw * 0.8 // 80% efficiency
    } else if (charger.pricing.pricing_type === 'per_kwh') {
      energyEstimate = durationHours * charger.max_power_kw * 0.8
      subtotal = energyEstimate * charger.pricing.price_value
    } else {
      subtotal = charger.pricing.price_value
      energyEstimate = durationHours * charger.max_power_kw * 0.8
    }

    const bookingFee = charger.pricing.booking_fee || 0
    const platformFeeRate = 0.15 // 15% platform commission
    const platformFee = subtotal * platformFeeRate
    const total = subtotal + bookingFee + platformFee

    setPriceEstimate({
      duration_hours: durationHours,
      energy_estimate_kwh: energyEstimate,
      subtotal,
      platform_fee: platformFee,
      booking_fee: bookingFee,
      total,
      pricing_type: charger.pricing.pricing_type,
      unit_price: charger.pricing.price_value
    })
  }, [startTime, endTime, selectedDate, charger.pricing, charger.max_power_kw])

  // Validate time selection
  const validateTimeSelection = () => {
    if (!startTime || !endTime) {
      toast.error('Please select start and end time')
      return false
    }

    const start = new Date(`${format(selectedDate, 'yyyy-MM-dd')}T${startTime}`)
    const end = new Date(`${format(selectedDate, 'yyyy-MM-dd')}T${endTime}`)
    
    if (end <= start) {
      toast.error('End time must be after start time')
      return false
    }

    if (isBefore(start, new Date())) {
      toast.error('Cannot book in the past')
      return false
    }

    return true
  }

  // Submit booking
  const submitBooking = async () => {
    if (!validateTimeSelection() || !priceEstimate) return

    setIsLoading(true)
    
    try {
      const start = new Date(`${format(selectedDate, 'yyyy-MM-dd')}T${startTime}`)
      const end = new Date(`${format(selectedDate, 'yyyy-MM-dd')}T${endTime}`)

      const bookingData: BookingForm = {
        charger_id: charger.id,
        start_time: start.toISOString(),
        end_time: end.toISOString(),
        vehicle_info: vehicleInfo,
        special_instructions: specialInstructions || undefined
      }

      // Simulate booking creation with atomic check
      await new Promise(resolve => setTimeout(resolve, 1500))
      
      // Mock successful booking
      const mockBooking: Booking = {
        id: Math.floor(Math.random() * 10000),
        charger_id: charger.id,
        renter_id: user?.id || 0,
        start_time: start.toISOString(),
        end_time: end.toISOString(),
        status: charger.auto_accept_bookings ? 'confirmed' : 'pending',
        payment_status: 'pending',
        booking_code: `BK${Math.random().toString(36).substr(2, 8).toUpperCase()}`,
        total_amount: priceEstimate.total,
        paid_amount: 0,
        currency: 'INR',
        qr_code_url: generateQRCode(`BK${Math.random().toString(36).substr(2, 8).toUpperCase()}`),
        access_code: Math.random().toString(36).substr(2, 6).toUpperCase(),
        vehicle_info: vehicleInfo,
        special_instructions: specialInstructions,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        charger
      }

      setCompletedBooking(mockBooking)
      setCurrentStep(3) // Go to confirmation
      
      toast.success('Booking created successfully!')
      onBookingComplete(mockBooking)
      
    } catch (error: any) {
      if (error.message?.includes('double booking')) {
        toast.error('This time slot is no longer available. Please select a different time.')
        // Refresh available slots
        const slots = generateTimeSlots(selectedDate)
        setAvailableSlots(slots)
      } else {
        toast.error('Failed to create booking. Please try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const generateQRCode = (bookingCode: string) => {
    // Simple QR code data URL - in real app, use proper QR code library
    return `data:image/svg+xml,${encodeURIComponent(`
      <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
        <rect width="200" height="200" fill="white"/>
        <text x="100" y="100" text-anchor="middle" font-family="monospace" font-size="14" fill="black">
          ${bookingCode}
        </text>
      </svg>
    `)}`
  }

  const handleNext = () => {
    if (currentStep === 0 && !validateTimeSelection()) return
    if (currentStep === 1 && !vehicleInfo.type) {
      toast.error('Please select your vehicle type')
      return
    }
    
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleShareBooking = () => {
    if (navigator.share && completedBooking) {
      navigator.share({
        title: 'ChargeMitra Booking',
        text: `My EV charging session at ${charger.title}`,
        url: `${window.location.origin}/bookings/${completedBooking.id}`
      })
    } else if (completedBooking) {
      navigator.clipboard.writeText(`${window.location.origin}/bookings/${completedBooking.id}`)
      toast.success('Booking link copied to clipboard!')
    }
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:p-0">
        {/* Backdrop */}
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
          onClick={onClose}
        />

        {/* Modal */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="relative w-full max-w-4xl mx-auto bg-white rounded-2xl shadow-xl overflow-hidden"
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-primary-500 to-secondary-500 px-6 py-4 text-white">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold">{charger.title}</h2>
                <div className="flex items-center text-primary-100 text-sm mt-1">
                  <MapPin className="w-4 h-4 mr-1" />
                  {charger.city}, {charger.state}
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
            </div>

            {/* Progress Steps */}
            <div className="mt-6 flex items-center justify-between">
              {steps.map((step, index) => (
                <div key={step.id} className="flex items-center">
                  <div className={cn(
                    'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors',
                    index <= currentStep ? 'bg-white text-primary-600' : 'bg-primary-400 text-white'
                  )}>
                    {index < currentStep ? (
                      <CheckCircle className="w-4 h-4" />
                    ) : (
                      index + 1
                    )}
                  </div>
                  {index < steps.length - 1 && (
                    <div className={cn(
                      'w-16 h-0.5 mx-2 transition-colors',
                      index < currentStep ? 'bg-white' : 'bg-primary-400'
                    )} />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Content */}
          <div className="p-6">
            <AnimatePresence mode="wait">
              {currentStep === 0 && (
                <motion.div
                  key="datetime"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="space-y-6"
                >
                  <h3 className="text-lg font-semibold text-gray-900">Select Date & Time</h3>
                  
                  {/* Date Picker */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Charging Date
                    </label>
                    <div className="flex space-x-2 overflow-x-auto pb-2">
                      {Array.from({ length: 7 }, (_, i) => {
                        const date = addDays(new Date(), i)
                        const isSelected = format(date, 'yyyy-MM-dd') === format(selectedDate, 'yyyy-MM-dd')
                        
                        return (
                          <button
                            key={i}
                            onClick={() => setSelectedDate(date)}
                            className={cn(
                              'flex-shrink-0 p-3 rounded-xl border text-center min-w-[80px] transition-colors',
                              isSelected 
                                ? 'bg-primary-50 border-primary-500 text-primary-700' 
                                : 'bg-white border-gray-200 hover:border-gray-300'
                            )}
                          >
                            <div className="text-xs text-gray-500">{format(date, 'EEE')}</div>
                            <div className="font-medium">{format(date, 'd')}</div>
                            <div className="text-xs text-gray-500">{format(date, 'MMM')}</div>
                          </button>
                        )
                      })}
                    </div>
                  </div>

                  {/* Time Picker */}
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Start Time
                      </label>
                      <input
                        type="time"
                        value={startTime}
                        onChange={(e) => setStartTime(e.target.value)}
                        className="input-field"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        End Time
                      </label>
                      <input
                        type="time"
                        value={endTime}
                        onChange={(e) => setEndTime(e.target.value)}
                        className="input-field"
                      />
                    </div>
                  </div>

                  {/* Price Estimate */}
                  {priceEstimate && (
                    <div className="bg-gray-50 rounded-xl p-4">
                      <h4 className="font-medium text-gray-900 mb-3">Price Estimate</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Duration: {priceEstimate.duration_hours}h</span>
                          <span>~{priceEstimate.energy_estimate_kwh.toFixed(1)} kWh</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Charging cost</span>
                          <span>₹{priceEstimate.subtotal.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Platform fee</span>
                          <span>₹{priceEstimate.platform_fee.toFixed(2)}</span>
                        </div>
                        {priceEstimate.booking_fee > 0 && (
                          <div className="flex justify-between">
                            <span>Booking fee</span>
                            <span>₹{priceEstimate.booking_fee.toFixed(2)}</span>
                          </div>
                        )}
                        <hr />
                        <div className="flex justify-between font-semibold text-lg">
                          <span>Total</span>
                          <span className="text-primary-600">₹{priceEstimate.total.toFixed(2)}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </motion.div>
              )}

              {currentStep === 1 && (
                <motion.div
                  key="details"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="space-y-6"
                >
                  <h3 className="text-lg font-semibold text-gray-900">Booking Details</h3>
                  
                  {/* Vehicle Information */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Vehicle Type *
                    </label>
                    <select
                      value={vehicleInfo.type}
                      onChange={(e) => setVehicleInfo({...vehicleInfo, type: e.target.value})}
                      className="input-field"
                      required
                    >
                      <option value="">Select your vehicle</option>
                      <option value="Tata Nexon EV">Tata Nexon EV</option>
                      <option value="MG ZS EV">MG ZS EV</option>
                      <option value="Hyundai Kona Electric">Hyundai Kona Electric</option>
                      <option value="Mahindra e2o Plus">Mahindra e2o Plus</option>
                      <option value="Other">Other</option>
                    </select>
                  </div>

                  <div className="grid md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Battery Capacity (kWh)
                      </label>
                      <input
                        type="number"
                        placeholder="e.g., 40.5"
                        value={vehicleInfo.batteryCapacity}
                        onChange={(e) => setVehicleInfo({...vehicleInfo, batteryCapacity: e.target.value})}
                        className="input-field"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Current Charge (%)
                      </label>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        placeholder="e.g., 20"
                        value={vehicleInfo.currentCharge}
                        onChange={(e) => setVehicleInfo({...vehicleInfo, currentCharge: e.target.value})}
                        className="input-field"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Target Charge (%)
                      </label>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        placeholder="e.g., 80"
                        value={vehicleInfo.targetCharge}
                        onChange={(e) => setVehicleInfo({...vehicleInfo, targetCharge: e.target.value})}
                        className="input-field"
                      />
                    </div>
                  </div>

                  {/* Special Instructions */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Special Instructions (Optional)
                    </label>
                    <textarea
                      placeholder="Any special requests or instructions for the host..."
                      value={specialInstructions}
                      onChange={(e) => setSpecialInstructions(e.target.value)}
                      className="input-field"
                      rows={3}
                    />
                  </div>

                  {/* Booking Summary */}
                  <div className="bg-gray-50 rounded-xl p-4">
                    <h4 className="font-medium text-gray-900 mb-3">Booking Summary</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>Date & Time</span>
                        <span>{format(selectedDate, 'MMM d, yyyy')} • {startTime} - {endTime}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Charger</span>
                        <span>{charger.max_power_kw}kW {charger.connector_type.toUpperCase()}</span>
                      </div>
                      {priceEstimate && (
                        <div className="flex justify-between font-semibold">
                          <span>Total Amount</span>
                          <span className="text-primary-600">₹{priceEstimate.total.toFixed(2)}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              )}

              {currentStep === 2 && (
                <motion.div
                  key="payment"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="space-y-6"
                >
                  <h3 className="text-lg font-semibold text-gray-900">Payment</h3>
                  
                  <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                    <div className="flex items-start space-x-3">
                      <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
                      <div>
                        <h4 className="font-medium text-blue-900">Secure Payment</h4>
                        <p className="text-sm text-blue-700 mt-1">
                          Your payment will be processed securely. The host will be paid only after your charging session is complete.
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Payment will be handled by the dummy payment page */}
                  <div className="text-center py-8">
                    <button
                      onClick={submitBooking}
                      disabled={isLoading}
                      className="btn-primary inline-flex items-center space-x-2"
                    >
                      {isLoading ? (
                        <motion.div
                          animate={{ rotate: 360 }}
                          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                        >
                          <Loader2 className="w-4 h-4" />
                        </motion.div>
                      ) : (
                        <CreditCard className="w-4 h-4" />
                      )}
                      <span>{isLoading ? 'Creating Booking...' : `Pay ₹${priceEstimate?.total.toFixed(2)}`}</span>
                    </button>
                  </div>
                </motion.div>
              )}

              {currentStep === 3 && completedBooking && (
                <motion.div
                  key="confirmation"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="text-center space-y-6"
                >
                  {/* Success Animation */}
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
                    className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto"
                  >
                    <CheckCircle className="w-10 h-10 text-green-600" />
                  </motion.div>

                  <div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-2">
                      Booking {completedBooking.status === 'confirmed' ? 'Confirmed!' : 'Submitted!'}
                    </h3>
                    <p className="text-gray-600">
                      {completedBooking.status === 'confirmed' 
                        ? 'Your charging slot is confirmed and ready.'
                        : 'Your booking request has been sent to the host for approval.'
                      }
                    </p>
                  </div>

                  {/* Booking Details */}
                  <div className="bg-gray-50 rounded-xl p-6 text-left max-w-md mx-auto">
                    <div className="space-y-4">
                      <div>
                        <div className="font-semibold text-gray-900 text-lg mb-2">
                          Booking Code: {completedBooking.booking_code}
                        </div>
                        <div className="text-sm text-gray-600">
                          {format(new Date(completedBooking.start_time), 'MMM d, yyyy • h:mm a')} - 
                          {format(new Date(completedBooking.end_time), 'h:mm a')}
                        </div>
                      </div>

                      {completedBooking.access_code && (
                        <div>
                          <div className="text-sm font-medium text-gray-700">Access Code</div>
                          <div className="font-mono text-lg bg-white p-2 rounded border">
                            {completedBooking.access_code}
                          </div>
                        </div>
                      )}

                      <div className="text-center py-4">
                        {completedBooking.qr_code_url && (
                          <img 
                            src={completedBooking.qr_code_url} 
                            alt="Booking QR Code"
                            className="w-32 h-32 mx-auto border rounded-lg"
                          />
                        )}
                        <p className="text-xs text-gray-500 mt-2">
                          Show this QR code to access the charger
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex flex-col sm:flex-row gap-3 justify-center">
                    <button
                      onClick={handleShareBooking}
                      className="btn-outline inline-flex items-center space-x-2"
                    >
                      <Share2 className="w-4 h-4" />
                      <span>Share</span>
                    </button>
                    
                    <button
                      onClick={() => window.location.href = `/bookings/${completedBooking.id}`}
                      className="btn-primary inline-flex items-center space-x-2"
                    >
                      <Calendar className="w-4 h-4" />
                      <span>View Booking</span>
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Footer */}
          {currentStep < 3 && (
            <div className="bg-gray-50 px-6 py-4 flex items-center justify-between">
              <button
                onClick={currentStep === 0 ? onClose : handleBack}
                className="btn-ghost inline-flex items-center space-x-2"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>{currentStep === 0 ? 'Cancel' : 'Back'}</span>
              </button>

              {currentStep < 2 && (
                <button
                  onClick={handleNext}
                  className="btn-primary inline-flex items-center space-x-2"
                >
                  <span>Next</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              )}
            </div>
          )}
        </motion.div>
      </div>
    </div>
  )
}

export default BookingFlow