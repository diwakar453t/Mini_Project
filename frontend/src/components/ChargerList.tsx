import { useRef, useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useInView } from 'react-intersection-observer'
import {
  MapPin,
  Zap,
  Star,
  Clock,
  Navigation,
  Filter,
  Heart,
  Share2,
  ChevronRight
} from 'lucide-react'

import { Charger } from '@/types'
import { cn } from '@/utils/cn'

interface ChargerListProps {
  chargers: Charger[]
  isLoading?: boolean
  onChargerClick?: (charger: Charger) => void
  onChargerHover?: (charger: Charger) => void
  selectedChargerId?: number
  className?: string
}

interface ChargerCardProps {
  charger: Charger
  isSelected?: boolean
  onClick?: () => void
  onHover?: () => void
  index: number
}

const ChargerCard = ({ charger, isSelected, onClick, onHover, index }: ChargerCardProps) => {
  const { ref, inView } = useInView({
    threshold: 0.3,
    triggerOnce: false
  })

  const [isFavorited, setIsFavorited] = useState(false)
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'available': return 'bg-green-100 text-green-800'
      case 'in_use': return 'bg-yellow-100 text-yellow-800'  
      case 'maintenance': return 'bg-red-100 text-red-800'
      case 'offline': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'available': return 'Available'
      case 'in_use': return 'In Use'
      case 'maintenance': return 'Maintenance' 
      case 'offline': return 'Offline'
      default: return 'Unknown'
    }
  }

  const handleShare = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (navigator.share) {
      navigator.share({
        title: charger.title,
        text: `Check out this EV charger: ${charger.title}`,
        url: `${window.location.origin}/chargers/${charger.id}`
      })
    } else {
      navigator.clipboard.writeText(`${window.location.origin}/chargers/${charger.id}`)
    }
  }

  const handleFavorite = (e: React.MouseEvent) => {
    e.stopPropagation()
    setIsFavorited(!isFavorited)
    // TODO: Call API to add/remove from favorites
  }

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 20 }}
      animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className={cn(
        'card-hover cursor-pointer transition-all duration-300',
        isSelected && 'ring-2 ring-primary-500 shadow-lg scale-[1.02]'
      )}
      onClick={onClick}
      onMouseEnter={onHover}
    >
      {/* Header with status and favorite */}
      <div className="flex items-center justify-between mb-4">
        <span className={cn(
          'px-3 py-1 rounded-full text-xs font-medium',
          getStatusColor(charger.current_status)
        )}>
          {getStatusText(charger.current_status)}
        </span>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={handleFavorite}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <Heart 
              className={cn(
                'w-4 h-4',
                isFavorited ? 'text-red-500 fill-current' : 'text-gray-400'
              )} 
            />
          </button>
          
          <button
            onClick={handleShare}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <Share2 className="w-4 h-4 text-gray-400" />
          </button>
        </div>
      </div>

      {/* Charger title and rating */}
      <div className="mb-3">
        <h3 className="font-semibold text-gray-900 mb-1 line-clamp-2">
          {charger.title}
        </h3>
        
        <div className="flex items-center space-x-3">
          <div className="flex items-center">
            <div className="flex text-yellow-400">
              {Array.from({ length: 5 }, (_, i) => (
                <Star 
                  key={i} 
                  className={cn(
                    'w-4 h-4',
                    i < Math.floor(charger.average_rating) ? 'fill-current' : ''
                  )} 
                />
              ))}
            </div>
            <span className="text-sm text-gray-600 ml-1">
              ({charger.rating_count})
            </span>
          </div>
          
          <span className="text-sm text-gray-500">•</span>
          
          <span className="text-sm text-gray-600">
            {charger.total_bookings} bookings
          </span>
        </div>
      </div>

      {/* Location */}
      <div className="flex items-start space-x-2 mb-4">
        <MapPin className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
        <p className="text-sm text-gray-600 line-clamp-2">
          {charger.address}
        </p>
      </div>

      {/* Charger specs */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="flex items-center space-x-2">
          <Zap className="w-4 h-4 text-primary-500" />
          <span className="text-sm font-medium">
            {charger.max_power_kw}kW
          </span>
        </div>
        
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-secondary-100 rounded-full flex items-center justify-center">
            <div className="w-2 h-2 bg-secondary-500 rounded-full"></div>
          </div>
          <span className="text-sm font-medium uppercase">
            {charger.connector_type}
          </span>
        </div>
      </div>

      {/* Amenities */}
      {charger.amenities && Object.keys(charger.amenities).length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {Object.entries(charger.amenities)
            .filter(([_, enabled]) => enabled)
            .slice(0, 3)
            .map(([amenity, _]) => (
              <span 
                key={amenity}
                className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full"
              >
                {amenity.replace('_', ' ')}
              </span>
            ))}
          {Object.values(charger.amenities).filter(Boolean).length > 3 && (
            <span className="text-xs text-gray-500">
              +{Object.values(charger.amenities).filter(Boolean).length - 3} more
            </span>
          )}
        </div>
      )}

      {/* Pricing and CTA */}
      <div className="flex items-center justify-between pt-4 border-t">
        <div>
          {charger.pricing && (
            <div className="flex items-baseline">
              <span className="text-lg font-bold text-primary-600">
                ₹{charger.pricing.price_value}
              </span>
              <span className="text-sm text-gray-500 ml-1">
                /{charger.pricing.pricing_type === 'per_kwh' ? 'kWh' : 'hour'}
              </span>
            </div>
          )}
          {charger.distance && (
            <div className="flex items-center text-xs text-gray-500 mt-1">
              <Navigation className="w-3 h-3 mr-1" />
              {charger.distance.toFixed(1)} km away
            </div>
          )}
        </div>
        
        <div className="flex items-center text-primary-600">
          <span className="text-sm font-medium mr-1">
            {charger.current_status === 'available' ? 'Book Now' : 'View'}
          </span>
          <ChevronRight className="w-4 h-4" />
        </div>
      </div>
    </motion.div>
  )
}

const ChargerListSkeleton = () => (
  <div className="space-y-4">
    {Array.from({ length: 6 }, (_, i) => (
      <div key={i} className="card">
        <div className="animate-pulse">
          <div className="flex justify-between mb-4">
            <div className="h-6 bg-gray-200 rounded w-20"></div>
            <div className="h-6 bg-gray-200 rounded w-6"></div>
          </div>
          <div className="h-6 bg-gray-200 rounded w-3/4 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="h-12 bg-gray-200 rounded mb-4"></div>
          <div className="flex justify-between">
            <div className="h-6 bg-gray-200 rounded w-16"></div>
            <div className="h-6 bg-gray-200 rounded w-20"></div>
          </div>
        </div>
      </div>
    ))}
  </div>
)

const ChargerList = ({ 
  chargers, 
  isLoading, 
  onChargerClick, 
  onChargerHover,
  selectedChargerId,
  className 
}: ChargerListProps) => {
  const listRef = useRef<HTMLDivElement>(null)
  
  // Scroll to selected charger
  useEffect(() => {
    if (selectedChargerId && listRef.current) {
      const selectedElement = listRef.current.querySelector(
        `[data-charger-id="${selectedChargerId}"]`
      )
      if (selectedElement) {
        selectedElement.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'center' 
        })
      }
    }
  }, [selectedChargerId])

  if (isLoading) {
    return (
      <div className={className}>
        <ChargerListSkeleton />
      </div>
    )
  }

  if (chargers.length === 0) {
    return (
      <div className={cn('text-center py-12', className)}>
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <Zap className="w-8 h-8 text-gray-400" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          No chargers found
        </h3>
        <p className="text-gray-500 mb-6">
          Try adjusting your search filters or expanding your search area
        </p>
        <button className="btn-outline">
          <Filter className="w-4 h-4 mr-2" />
          Clear Filters
        </button>
      </div>
    )
  }

  return (
    <div ref={listRef} className={cn('space-y-4', className)}>
      <AnimatePresence>
        {chargers.map((charger, index) => (
          <div key={charger.id} data-charger-id={charger.id}>
            <ChargerCard
              charger={charger}
              isSelected={selectedChargerId === charger.id}
              onClick={() => onChargerClick?.(charger)}
              onHover={() => onChargerHover?.(charger)}
              index={index}
            />
          </div>
        ))}
      </AnimatePresence>
    </div>
  )
}

export default ChargerList