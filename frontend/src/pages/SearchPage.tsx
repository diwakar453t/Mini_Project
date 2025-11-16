import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useSearchParams } from 'react-router-dom'
import {
  Search,
  MapPin,
  Filter,
  SlidersHorizontal,
  Map,
  List,
  Navigation,
  X,
  ChevronDown,
  Loader2
} from 'lucide-react'

import mapsService, { sampleChargers } from '@/services/maps'
import ChargerList from '@/components/ChargerList'
import { Charger, SearchFilters, ConnectorType, ChargerType } from '@/types'
import { cn } from '@/utils/cn'

const SearchPage = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const mapContainerRef = useRef<HTMLDivElement>(null)
  const [mapInstance, setMapInstance] = useState<google.maps.Map | null>(null)
  
  // UI State
  const [viewMode, setViewMode] = useState<'map' | 'list' | 'split'>('split')
  const [showFilters, setShowFilters] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  
  // Search State
  const [searchQuery, setSearchQuery] = useState(searchParams.get('q') || '')
  const [chargers, setChargers] = useState<Charger[]>([])
  const [selectedChargerId, setSelectedChargerId] = useState<number | null>(null)
  
  // Filters State
  const [filters, setFilters] = useState<SearchFilters>({
    city: searchParams.get('city') || '',
    radius_km: 10,
    connector_type: searchParams.get('connector') as ConnectorType || undefined,
    charger_type: searchParams.get('type') as ChargerType || undefined,
    available_now: searchParams.get('available') === 'true',
    min_rating: undefined,
    max_price: undefined,
    amenities: []
  })

  // Initialize map
  useEffect(() => {
    if (mapContainerRef.current) {
      mapsService.initializeMap(mapContainerRef.current).then(map => {
        setMapInstance(map)
      })
    }

    return () => {
      mapsService.destroy()
    }
  }, [])

  // Load chargers (using sample data when no API key)
  const loadChargers = useCallback(async () => {
    setIsLoading(true)
    
    try {
      // Use sample data if no API key
      if (!import.meta.env.VITE_GOOGLE_MAPS_API_KEY && !import.meta.env.VITE_MAP_API_KEY) {
        let results = [...sampleChargers]
        
        // Apply filters to sample data
        if (filters.connector_type) {
          results = results.filter(c => c.connector_type === filters.connector_type)
        }
        if (filters.charger_type) {
          results = results.filter(c => c.charger_type === filters.charger_type)
        }
        if (filters.available_now) {
          results = results.filter(c => c.current_status === 'available')
        }
        if (filters.min_rating) {
          results = results.filter(c => c.average_rating >= filters.min_rating!)
        }
        
        setChargers(results)
        
        // Add markers to map
        await mapsService.addChargerMarkers(results, handleMarkerClick)
      } else {
        // TODO: Call real API when implemented
        // const response = await searchChargers(filters)
        // setChargers(response.chargers)
        setChargers([])
      }
    } catch (error) {
      console.error('Failed to load chargers:', error)
    } finally {
      setIsLoading(false)
    }
  }, [filters])

  // Load chargers on mount and filter changes
  useEffect(() => {
    loadChargers()
  }, [loadChargers])

  // Handle search
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (searchQuery.trim()) {
      setIsLoading(true)
      
      // Update URL
      setSearchParams({ q: searchQuery.trim() })
      
      // Geocode and center map
      const location = await mapsService.searchByAddress(searchQuery.trim())
      if (location) {
        // Search for nearby chargers
        const nearbyChargers = mapsService.searchNearby(location, filters.radius_km || 10)
        setChargers(nearbyChargers)
        await mapsService.addChargerMarkers(nearbyChargers, handleMarkerClick)
      }
      
      setIsLoading(false)
    }
  }

  // Handle marker click (highlight in list)
  const handleMarkerClick = useCallback((charger: Charger) => {
    setSelectedChargerId(charger.id)
  }, [])

  // Handle charger hover (highlight on map)
  const handleChargerHover = useCallback((charger: Charger) => {
    mapsService.highlightMarker(charger.id)
  }, [])

  // Handle charger click
  const handleChargerClick = useCallback((charger: Charger) => {
    setSelectedChargerId(charger.id)
    mapsService.highlightMarker(charger.id)
    
    // Navigate to charger details in a real app
    // window.location.href = `/chargers/${charger.id}`
  }, [])

  // Update filters
  const updateFilter = (key: keyof SearchFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  // Clear filters
  const clearFilters = () => {
    setFilters({
      radius_km: 10,
      available_now: false,
      amenities: []
    })
    setSearchParams({})
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-4 py-4 lg:px-6">
        <div className="flex items-center space-x-4">
          {/* Search Bar */}
          <form onSubmit={handleSearch} className="flex-1 max-w-2xl">
            <div className="relative flex items-center bg-gray-50 rounded-xl border border-gray-200 focus-within:border-primary-500 focus-within:ring-1 focus-within:ring-primary-500">
              <MapPin className="w-5 h-5 text-gray-400 ml-4" />
              <input
                type="text"
                placeholder="Search by city, area, or landmark..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1 px-4 py-3 bg-transparent border-0 placeholder-gray-500 focus:outline-none"
              />
              <button
                type="submit"
                disabled={isLoading}
                className="m-1 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors disabled:opacity-50 flex items-center space-x-2"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Search className="w-4 h-4" />
                )}
              </button>
            </div>
          </form>

          {/* Filter Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={cn(
              'flex items-center space-x-2 px-4 py-3 rounded-xl border transition-colors',
              showFilters 
                ? 'bg-primary-50 border-primary-200 text-primary-700' 
                : 'bg-white border-gray-200 hover:border-gray-300'
            )}
          >
            <SlidersHorizontal className="w-4 h-4" />
            <span className="hidden sm:block">Filters</span>
          </button>

          {/* View Mode Toggle */}
          <div className="hidden lg:flex items-center bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode('list')}
              className={cn(
                'p-2 rounded-md transition-colors',
                viewMode === 'list' ? 'bg-white shadow-sm text-primary-600' : 'text-gray-600'
              )}
            >
              <List className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('split')}
              className={cn(
                'p-2 rounded-md transition-colors',
                viewMode === 'split' ? 'bg-white shadow-sm text-primary-600' : 'text-gray-600'
              )}
            >
              <SlidersHorizontal className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('map')}
              className={cn(
                'p-2 rounded-md transition-colors',
                viewMode === 'map' ? 'bg-white shadow-sm text-primary-600' : 'text-gray-600'
              )}
            >
              <Map className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Filters Panel */}
        <AnimatePresence>
          {showFilters && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden mt-4 pt-4 border-t"
            >
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {/* Radius */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Radius
                  </label>
                  <select
                    value={filters.radius_km || 10}
                    onChange={(e) => updateFilter('radius_km', Number(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-200 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  >
                    <option value={5}>5 km</option>
                    <option value={10}>10 km</option>
                    <option value={20}>20 km</option>
                    <option value={50}>50 km</option>
                  </select>
                </div>

                {/* Connector Type */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Connector
                  </label>
                  <select
                    value={filters.connector_type || ''}
                    onChange={(e) => updateFilter('connector_type', e.target.value || undefined)}
                    className="w-full px-3 py-2 border border-gray-200 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  >
                    <option value="">Any</option>
                    <option value="ccs">CCS</option>
                    <option value="chademo">CHAdeMO</option>
                    <option value="nacs">NACS</option>
                    <option value="type2">Type 2</option>
                    <option value="type1">Type 1</option>
                  </select>
                </div>

                {/* Charger Type */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Speed
                  </label>
                  <select
                    value={filters.charger_type || ''}
                    onChange={(e) => updateFilter('charger_type', e.target.value || undefined)}
                    className="w-full px-3 py-2 border border-gray-200 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  >
                    <option value="">Any Speed</option>
                    <option value="level1">Level 1 (Slow)</option>
                    <option value="level2">Level 2 (Fast)</option>
                    <option value="dc_fast">DC Fast</option>
                  </select>
                </div>

                {/* Available Now */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Availability
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={filters.available_now || false}
                      onChange={(e) => updateFilter('available_now', e.target.checked)}
                      className="mr-2 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="text-sm">Available now</span>
                  </label>
                </div>

                {/* Min Rating */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Min Rating
                  </label>
                  <select
                    value={filters.min_rating || ''}
                    onChange={(e) => updateFilter('min_rating', e.target.value ? Number(e.target.value) : undefined)}
                    className="w-full px-3 py-2 border border-gray-200 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  >
                    <option value="">Any</option>
                    <option value={4}>4+ stars</option>
                    <option value={4.5}>4.5+ stars</option>
                  </select>
                </div>

                {/* Clear Filters */}
                <div className="flex items-end">
                  <button
                    onClick={clearFilters}
                    className="w-full px-3 py-2 text-sm text-gray-600 border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
                  >
                    Clear All
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Charger List */}
        <div className={cn(
          'transition-all duration-300 overflow-y-auto',
          viewMode === 'map' ? 'w-0 opacity-0' :
          viewMode === 'list' ? 'w-full' :
          'w-full lg:w-1/2 xl:w-2/5'
        )}>
          <div className="p-4 lg:p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-gray-900">
                {chargers.length} Chargers Found
              </h2>
              
              {chargers.length > 0 && (
                <button className="text-sm text-primary-600 hover:text-primary-700 flex items-center space-x-1">
                  <span>Sort</span>
                  <ChevronDown className="w-4 h-4" />
                </button>
              )}
            </div>

            <ChargerList
              chargers={chargers}
              isLoading={isLoading}
              onChargerClick={handleChargerClick}
              onChargerHover={handleChargerHover}
              selectedChargerId={selectedChargerId || undefined}
            />
          </div>
        </div>

        {/* Map */}
        <div className={cn(
          'transition-all duration-300 bg-gray-100',
          viewMode === 'list' ? 'w-0 opacity-0' :
          viewMode === 'map' ? 'w-full' :
          'w-full lg:w-1/2 xl:w-3/5'
        )}>
          <div 
            ref={mapContainerRef} 
            className="w-full h-full"
          />
        </div>
      </div>

      {/* Mobile View Mode Toggle */}
      <div className="lg:hidden fixed bottom-20 left-1/2 transform -translate-x-1/2 z-40">
        <div className="bg-white rounded-full shadow-lg border flex items-center p-1">
          <button
            onClick={() => setViewMode('list')}
            className={cn(
              'px-4 py-2 rounded-full text-sm font-medium transition-colors',
              viewMode === 'list' ? 'bg-primary-500 text-white' : 'text-gray-600'
            )}
          >
            List
          </button>
          <button
            onClick={() => setViewMode('map')}
            className={cn(
              'px-4 py-2 rounded-full text-sm font-medium transition-colors',
              viewMode === 'map' ? 'bg-primary-500 text-white' : 'text-gray-600'
            )}
          >
            Map
          </button>
        </div>
      </div>
    </div>
  )
}

export default SearchPage