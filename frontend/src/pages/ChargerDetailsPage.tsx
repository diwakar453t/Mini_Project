import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ArrowLeft,
  MapPin,
  Star,
  Zap,
  Clock,
  Wifi,
  Car,
  Shield,
  Phone,
  Share2,
  Heart,
  Calendar
} from 'lucide-react'
import toast from 'react-hot-toast'

import { useAuth } from '@/hooks/useAuth'
import { sampleChargers } from '@/services/maps'
import ChargerTelemetry from '@/components/ChargerTelemetry'
import BookingFlow from '@/components/BookingFlow'
import { Charger } from '@/types'
import { cn } from '@/utils/cn'

const ChargerDetailsPage = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  
  const [charger, setCharger] = useState<Charger | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [showBookingFlow, setShowBookingFlow] = useState(false)
  const [isFavorited, setIsFavorited] = useState(false)

  // Load charger data (using sample data for now)
  useEffect(() => {
    const loadCharger = () => {
      setIsLoading(true)
      
      // Simulate API call delay
      setTimeout(() => {
        const foundCharger = sampleChargers.find(c => c.id === parseInt(id || '0'))
        
        if (foundCharger) {
          // Add some additional mock data
          const enhancedCharger = {
            ...foundCharger,
            host: {
              id: 1,
              name: 'Raj Patel',
              avatar_url: '/avatars/raj.jpg',
              host_rating: '4.8',
              host_rating_count: 156,
              response_time_minutes: 15,
              is_verified: true,
              bio: 'EV enthusiast helping fellow drivers charge conveniently.'
            },
            pricing: {
              price_value: 12,
              pricing_type: 'per_kwh' as const,
              min_session_minutes: 30,
              max_session_minutes: 240,
              booking_fee: 10,
              peak_price_multiplier: 1.2,
              weekend_price_multiplier: 1.0
            },
            amenities: {
              parking: true,
              wifi: true,
              restroom: false,
              security: true,
              cafe: false,
              shelter: true
            },
            features: {
              cable_provided: true,
              weatherproof: true,
              app_control: true,
              rfid_access: false,
              payment_terminal: true
            },
            access_instructions: 'Located in the basement parking. Use the QR code to unlock the charger. Contact host if you need assistance.',
            images: [
              '/images/charger-1.jpg',
              '/images/charger-2.jpg',
              '/images/charger-3.jpg'
            ],
            reviews: [
              {
                id: 1,
                rating: 5,
                comment: 'Excellent charger with fast charging speed. Host was very helpful!',
                reviewer_name: 'Anita Sharma',
                created_at: '2023-12-15',
                helpful_count: 8
              },
              {
                id: 2,
                rating: 4,
                comment: 'Good location and reliable charger. Slightly expensive but worth it.',
                reviewer_name: 'Vikram Singh',
                created_at: '2023-12-10',
                helpful_count: 5
              }
            ]
          }
          
          setCharger(enhancedCharger as any)
        }
        
        setIsLoading(false)
      }, 800)
    }

    if (id) {
      loadCharger()
    }
  }, [id])

  const handleBookNow = () => {
    if (!user) {
      toast.error('Please sign in to book a charger')
      navigate('/auth')
      return
    }
    setShowBookingFlow(true)
  }

  const handleShare = () => {
    if (navigator.share && charger) {
      navigator.share({
        title: charger.title,
        text: `Check out this EV charger: ${charger.title}`,
        url: window.location.href
      })
    } else {
      navigator.clipboard.writeText(window.location.href)
      toast.success('Link copied to clipboard!')
    }
  }

  const handleFavorite = () => {
    setIsFavorited(!isFavorited)
    toast.success(isFavorited ? 'Removed from favorites' : 'Added to favorites')
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="animate-pulse">
          <div className="h-64 bg-gray-200"></div>
          <div className="max-w-7xl mx-auto px-4 py-8">
            <div className="grid lg:grid-cols-3 gap-8">
              <div className="lg:col-span-2 space-y-6">
                <div className="h-8 bg-gray-200 rounded w-3/4"></div>
                <div className="h-32 bg-gray-200 rounded"></div>
                <div className="h-64 bg-gray-200 rounded"></div>
              </div>
              <div className="space-y-4">
                <div className="h-64 bg-gray-200 rounded"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!charger) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Charger Not Found</h2>
          <p className="text-gray-600 mb-6">The charger you're looking for doesn't exist.</p>
          <button onClick={() => navigate('/search')} className="btn-primary">
            Browse Chargers
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section with Images */}
      <div className="relative h-64 md:h-80 bg-gray-200">
        <div className="absolute inset-0 bg-gradient-to-r from-primary-500/20 to-secondary-500/20"></div>
        <div className="absolute top-4 left-4 right-4 flex items-center justify-between z-10">
          <button
            onClick={() => navigate(-1)}
            className="bg-white/90 backdrop-blur-sm p-3 rounded-xl hover:bg-white transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-700" />
          </button>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={handleFavorite}
              className="bg-white/90 backdrop-blur-sm p-3 rounded-xl hover:bg-white transition-colors"
            >
              <Heart 
                className={cn(
                  'w-5 h-5',
                  isFavorited ? 'text-red-500 fill-current' : 'text-gray-700'
                )}
              />
            </button>
            
            <button
              onClick={handleShare}
              className="bg-white/90 backdrop-blur-sm p-3 rounded-xl hover:bg-white transition-colors"
            >
              <Share2 className="w-5 h-5 text-gray-700" />
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-8">
            {/* Header */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-xl p-6 shadow-sm border"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900 mb-2">{charger.title}</h1>
                  <div className="flex items-center text-gray-600 mb-3">
                    <MapPin className="w-4 h-4 mr-1" />
                    <span>{charger.address}</span>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center">
                      <Star className="w-4 h-4 text-yellow-400 fill-current mr-1" />
                      <span className="font-medium">{charger.average_rating}</span>
                      <span className="text-gray-500 ml-1">({charger.total_bookings} reviews)</span>
                    </div>
                    <span className={cn(
                      'px-3 py-1 rounded-full text-xs font-medium',
                      charger.current_status === 'available' ? 'bg-green-100 text-green-800' :
                      charger.current_status === 'in_use' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    )}>
                      {charger.current_status === 'available' ? 'Available' :
                       charger.current_status === 'in_use' ? 'In Use' : 'Unavailable'}
                    </span>
                  </div>
                </div>
                
                <div className="text-right">
                  <div className="text-2xl font-bold text-primary-600">
                    ₹{charger.pricing?.price_value}
                  </div>
                  <div className="text-sm text-gray-500">
                    per {charger.pricing?.pricing_type === 'per_kwh' ? 'kWh' : 'hour'}
                  </div>
                </div>
              </div>

              {/* Specs */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 py-4 border-y">
                <div className="text-center">
                  <Zap className="w-6 h-6 text-primary-500 mx-auto mb-1" />
                  <div className="font-semibold">{charger.max_power_kw}kW</div>
                  <div className="text-xs text-gray-500">Max Power</div>
                </div>
                <div className="text-center">
                  <div className="w-6 h-6 bg-secondary-100 rounded-full mx-auto mb-1 flex items-center justify-center">
                    <div className="w-3 h-3 bg-secondary-500 rounded-full"></div>
                  </div>
                  <div className="font-semibold">{charger.connector_type.toUpperCase()}</div>
                  <div className="text-xs text-gray-500">Connector</div>
                </div>
                <div className="text-center">
                  <Clock className="w-6 h-6 text-blue-500 mx-auto mb-1" />
                  <div className="font-semibold">{charger.pricing?.min_session_minutes}m</div>
                  <div className="text-xs text-gray-500">Min Session</div>
                </div>
                <div className="text-center">
                  <Car className="w-6 h-6 text-green-500 mx-auto mb-1" />
                  <div className="font-semibold">{charger.charger_type === 'dc_fast' ? 'DC Fast' : 'AC'}</div>
                  <div className="text-xs text-gray-500">Type</div>
                </div>
              </div>

              {/* Amenities */}
              {charger.amenities && (
                <div className="mt-4">
                  <h3 className="font-medium text-gray-900 mb-3">Amenities</h3>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(charger.amenities)
                      .filter(([_, enabled]) => enabled)
                      .map(([amenity, _]) => (
                        <span
                          key={amenity}
                          className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                        >
                          {amenity.replace('_', ' ')}
                        </span>
                      ))}
                  </div>
                </div>
              )}
            </motion.div>

            {/* Live Telemetry */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
            >
              <ChargerTelemetry chargerId={charger.id} />
            </motion.div>

            {/* Description & Instructions */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-white rounded-xl p-6 shadow-sm border"
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-4">About This Charger</h3>
              <p className="text-gray-600 mb-6">{charger.description}</p>
              
              {charger.access_instructions && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="font-medium text-blue-900 mb-2">Access Instructions</h4>
                  <p className="text-blue-700 text-sm">{charger.access_instructions}</p>
                </div>
              )}
            </motion.div>

            {/* Host Information */}
            {charger.host && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="bg-white rounded-xl p-6 shadow-sm border"
              >
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Host</h3>
                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center">
                    {charger.host.avatar_url ? (
                      <img 
                        src={charger.host.avatar_url} 
                        alt={charger.host.name}
                        className="w-12 h-12 rounded-full object-cover"
                      />
                    ) : (
                      <span className="text-gray-600 font-medium">
                        {charger.host.name.split(' ').map(n => n[0]).join('')}
                      </span>
                    )}
                  </div>
                  
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <h4 className="font-medium text-gray-900">{charger.host.name}</h4>
                      {charger.host.is_verified && (
                        <Shield className="w-4 h-4 text-green-500" />
                      )}
                    </div>
                    
                    <div className="flex items-center space-x-4 text-sm text-gray-600 mb-2">
                      <div className="flex items-center">
                        <Star className="w-4 h-4 text-yellow-400 fill-current mr-1" />
                        <span>{charger.host.host_rating} ({charger.host.host_rating_count} reviews)</span>
                      </div>
                      <div className="flex items-center">
                        <Clock className="w-4 h-4 mr-1" />
                        <span>Responds in ~{charger.host.response_time_minutes} min</span>
                      </div>
                    </div>
                    
                    <p className="text-gray-600 text-sm">{charger.host.bio}</p>
                    
                    <button className="mt-3 btn-outline text-sm inline-flex items-center space-x-2">
                      <Phone className="w-4 h-4" />
                      <span>Contact Host</span>
                    </button>
                  </div>
                </div>
              </motion.div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Booking Card */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-white rounded-xl p-6 shadow-sm border sticky top-8"
            >
              <div className="text-center mb-6">
                <div className="text-3xl font-bold text-primary-600 mb-1">
                  ₹{charger.pricing?.price_value}
                </div>
                <div className="text-gray-500">
                  per {charger.pricing?.pricing_type === 'per_kwh' ? 'kWh' : 'hour'}
                </div>
              </div>

              <button
                onClick={handleBookNow}
                disabled={charger.current_status !== 'available'}
                className={cn(
                  'w-full py-3 rounded-xl font-semibold transition-colors mb-4',
                  charger.current_status === 'available'
                    ? 'bg-primary-500 text-white hover:bg-primary-600'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                )}
              >
                {charger.current_status === 'available' ? (
                  <span className="flex items-center justify-center space-x-2">
                    <Calendar className="w-4 h-4" />
                    <span>Book Now</span>
                  </span>
                ) : (
                  'Currently Unavailable'
                )}
              </button>

              {charger.pricing && (
                <div className="text-sm space-y-2 text-gray-600">
                  <div className="flex justify-between">
                    <span>Booking fee:</span>
                    <span>₹{charger.pricing.booking_fee}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Min session:</span>
                    <span>{charger.pricing.min_session_minutes} minutes</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Max session:</span>
                    <span>{charger.pricing.max_session_minutes} minutes</span>
                  </div>
                </div>
              )}
            </motion.div>

            {/* Quick Info */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white rounded-xl p-6 shadow-sm border"
            >
              <h3 className="font-semibold text-gray-900 mb-4">Quick Info</h3>
              <div className="space-y-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Total bookings:</span>
                  <span className="font-medium">{charger.total_bookings}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Average rating:</span>
                  <span className="font-medium">{charger.average_rating} ⭐</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Instant booking:</span>
                  <span className="font-medium">
                    {charger.auto_accept_bookings ? '✅' : '❌'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">KYC verified:</span>
                  <span className="font-medium">✅</span>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </div>

      {/* Booking Flow Modal */}
      {showBookingFlow && charger && (
        <BookingFlow
          charger={charger}
          onClose={() => setShowBookingFlow(false)}
          onBookingComplete={(booking) => {
            setShowBookingFlow(false)
            navigate(`/bookings/${booking.id}`)
          }}
        />
      )}
    </div>
  )
}

export default ChargerDetailsPage