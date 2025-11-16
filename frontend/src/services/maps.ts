import { Loader } from '@googlemaps/js-api-loader'

// Fallback sample data for when API key is missing
export const sampleChargers = [
  {
    id: 1,
    title: "Green Energy Hub - Bandra",
    address: "Bandra West, Mumbai, Maharashtra",
    latitude: 19.0540,
    longitude: 72.8294,
    connector_type: "ccs",
    charger_type: "dc_fast",
    max_power_kw: 120,
    current_status: "available",
    average_rating: 4.8,
    total_bookings: 156,
    pricing: { price_value: 12, pricing_type: "per_kwh" }
  },
  {
    id: 2,
    title: "EcoCharge Station - Andheri",
    address: "Andheri East, Mumbai, Maharashtra", 
    latitude: 19.1197,
    longitude: 72.8464,
    connector_type: "type2",
    charger_type: "level2", 
    max_power_kw: 22,
    current_status: "in_use",
    average_rating: 4.5,
    total_bookings: 89,
    pricing: { price_value: 8, pricing_type: "per_kwh" }
  },
  {
    id: 3,
    title: "Power Plus - Worli",
    address: "Worli, Mumbai, Maharashtra",
    latitude: 19.0176,
    longitude: 72.8181,
    connector_type: "ccs",
    charger_type: "dc_fast",
    max_power_kw: 150,
    current_status: "available",
    average_rating: 4.9,
    total_bookings: 234,
    pricing: { price_value: 15, pricing_type: "per_kwh" }
  },
  {
    id: 4,
    title: "Quick Charge - Powai",
    address: "Powai, Mumbai, Maharashtra",
    latitude: 19.1176,
    longitude: 72.9060,
    connector_type: "chademo",
    charger_type: "dc_fast",
    max_power_kw: 90,
    current_status: "maintenance",
    average_rating: 4.3,
    total_bookings: 67,
    pricing: { price_value: 10, pricing_type: "per_kwh" }
  },
  {
    id: 5,
    title: "Tesla Supercharger - BKC",
    address: "Bandra Kurla Complex, Mumbai, Maharashtra",
    latitude: 19.0670,
    longitude: 72.8777,
    connector_type: "nacs",
    charger_type: "dc_fast",
    max_power_kw: 250,
    current_status: "available",
    average_rating: 4.9,
    total_bookings: 445,
    pricing: { price_value: 18, pricing_type: "per_kwh" }
  }
]

class MapsService {
  private loader: Loader | null = null
  private mapInstance: google.maps.Map | null = null
  private markers: google.maps.Marker[] = []
  private infoWindow: google.maps.InfoWindow | null = null
  private markerClusterer: any = null
  private geocoder: google.maps.Geocoder | null = null
  
  private readonly apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || import.meta.env.VITE_MAP_API_KEY
  private readonly fallbackToSample = !this.apiKey

  constructor() {
    if (this.apiKey) {
      this.loader = new Loader({
        apiKey: this.apiKey,
        version: 'weekly',
        libraries: ['places', 'geometry'],
        region: 'IN',
        language: 'en'
      })
    }
  }

  async initializeMap(container: HTMLElement, options?: google.maps.MapOptions): Promise<google.maps.Map | null> {
    if (this.fallbackToSample) {
      console.warn('MAP_API_KEY not found, using sample data')
      return this.createFallbackMap(container)
    }

    try {
      await this.loader!.load()
      
      const defaultOptions: google.maps.MapOptions = {
        zoom: 12,
        center: { lat: 19.0760, lng: 72.8777 }, // Mumbai
        mapTypeId: google.maps.MapTypeId.ROADMAP,
        styles: this.getMapStyles(),
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: true,
        zoomControl: true,
        gestureHandling: 'cooperative',
        ...options
      }

      this.mapInstance = new google.maps.Map(container, defaultOptions)
      this.infoWindow = new google.maps.InfoWindow()
      this.geocoder = new google.maps.Geocoder()

      return this.mapInstance
    } catch (error) {
      console.error('Failed to load Google Maps:', error)
      return this.createFallbackMap(container)
    }
  }

  private createFallbackMap(container: HTMLElement): null {
    // Create a simple fallback interface
    container.innerHTML = `
      <div class="w-full h-full bg-gray-100 flex items-center justify-center text-center p-8">
        <div>
          <div class="w-16 h-16 bg-gray-300 rounded-full mx-auto mb-4 flex items-center justify-center">
            <svg class="w-8 h-8 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.899a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-gray-700 mb-2">Map View</h3>
          <p class="text-sm text-gray-500">Map requires API key to display.<br>Using sample charger data below.</p>
        </div>
      </div>
    `
    return null
  }

  async addChargerMarkers(chargers: any[], onMarkerClick?: (charger: any) => void): Promise<void> {
    if (this.fallbackToSample || !this.mapInstance) {
      return
    }

    // Clear existing markers
    this.clearMarkers()

    const markers = chargers.map(charger => {
      const marker = new google.maps.Marker({
        position: { lat: charger.latitude, lng: charger.longitude },
        map: this.mapInstance,
        title: charger.title,
        icon: this.getChargerIcon(charger.current_status, charger.charger_type),
        animation: google.maps.Animation.DROP
      })

      // Add click listener
      marker.addListener('click', () => {
        this.showChargerInfo(charger, marker)
        onMarkerClick?.(charger)
      })

      return marker
    })

    this.markers = markers

    // Add marker clustering for better performance
    if (window.MarkerClusterer && markers.length > 10) {
      this.markerClusterer = new window.MarkerClusterer({
        map: this.mapInstance,
        markers: markers,
        gridSize: 60,
        maxZoom: 15
      })
    }

    // Fit map to show all markers
    if (markers.length > 0) {
      const bounds = new google.maps.LatLngBounds()
      markers.forEach(marker => {
        bounds.extend(marker.getPosition()!)
      })
      this.mapInstance.fitBounds(bounds)
    }
  }

  private getChargerIcon(status: string, type: string): google.maps.Icon {
    const baseUrl = '/markers'
    let color = '#10B981' // green for available
    
    switch (status) {
      case 'in_use':
        color = '#F59E0B' // yellow
        break
      case 'maintenance':
      case 'fault':
        color = '#EF4444' // red
        break
      case 'offline':
        color = '#6B7280' // gray
        break
    }

    const iconType = type === 'dc_fast' ? 'fast' : 'standard'
    
    return {
      url: `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(this.createMarkerSVG(color, iconType, status === 'in_use'))}`,
      scaledSize: new google.maps.Size(40, 40),
      anchor: new google.maps.Point(20, 40)
    }
  }

  private createMarkerSVG(color: string, type: string, isInUse: boolean): string {
    const pulseAnimation = isInUse ? `
      <style>
        .pulse { animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
      </style>
    ` : ''
    
    const iconPath = type === 'fast' 
      ? 'M13 2L3 14h9l-1 8 10-12h-9l1-8z' // Lightning bolt for fast charging
      : 'M12 2C8.13 4 5.03 7.1 3 11h6l-1 7 9-7h-6l1-7z' // Standard charging icon

    return `
      <svg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
        ${pulseAnimation}
        <circle cx="20" cy="30" r="8" fill="${color}" stroke="white" stroke-width="2" class="${isInUse ? 'pulse' : ''}" opacity="0.9"/>
        <path d="${iconPath}" transform="translate(8, 8) scale(1.5)" fill="white"/>
      </svg>
    `
  }

  private showChargerInfo(charger: any, marker: google.maps.Marker): void {
    if (!this.infoWindow) return

    const statusBadge = this.getStatusBadge(charger.current_status)
    const priceText = `₹${charger.pricing?.price_value || 0}/${charger.pricing?.pricing_type === 'per_kwh' ? 'kWh' : 'hour'}`

    const content = `
      <div class="p-4 max-w-xs">
        <div class="flex items-start justify-between mb-2">
          <h3 class="font-semibold text-gray-900 text-sm">${charger.title}</h3>
          ${statusBadge}
        </div>
        <p class="text-xs text-gray-600 mb-2">${charger.address}</p>
        <div class="flex items-center justify-between text-xs">
          <span class="text-gray-500">${charger.max_power_kw}kW • ${charger.connector_type.toUpperCase()}</span>
          <span class="font-medium text-primary-600">${priceText}</span>
        </div>
        <div class="flex items-center mt-2">
          <div class="flex text-yellow-400">
            ${'★'.repeat(Math.floor(charger.average_rating))}${'☆'.repeat(5 - Math.floor(charger.average_rating))}
          </div>
          <span class="text-xs text-gray-500 ml-1">(${charger.total_bookings})</span>
        </div>
        <button onclick="window.location.href='/chargers/${charger.id}'" 
                class="mt-3 w-full bg-primary-500 text-white px-3 py-2 rounded-md text-xs font-medium hover:bg-primary-600">
          View Details
        </button>
      </div>
    `

    this.infoWindow.setContent(content)
    this.infoWindow.open(this.mapInstance!, marker)
  }

  private getStatusBadge(status: string): string {
    const badges = {
      available: '<span class="status-available">Available</span>',
      in_use: '<span class="status-in-use">In Use</span>',
      maintenance: '<span class="status-maintenance">Maintenance</span>',
      offline: '<span class="status-offline">Offline</span>',
      fault: '<span class="status-maintenance">Fault</span>'
    }
    return badges[status as keyof typeof badges] || badges.offline
  }

  highlightMarker(chargerId: number): void {
    if (this.fallbackToSample || !this.markers) return
    
    const marker = this.markers.find(m => 
      m.getTitle()?.includes(chargerId.toString())
    )
    
    if (marker) {
      // Briefly animate the marker
      marker.setAnimation(google.maps.Animation.BOUNCE)
      setTimeout(() => marker.setAnimation(null), 2000)
      
      // Center map on marker
      this.mapInstance?.panTo(marker.getPosition()!)
      this.mapInstance?.setZoom(15)
    }
  }

  async searchByAddress(address: string): Promise<google.maps.LatLng | null> {
    if (this.fallbackToSample || !this.geocoder) {
      console.warn('Geocoding not available without API key')
      return null
    }

    try {
      const response = await this.geocoder.geocode({ 
        address: `${address}, India`,
        region: 'IN'
      })
      
      if (response.results[0]) {
        const location = response.results[0].geometry.location
        this.mapInstance?.panTo(location)
        this.mapInstance?.setZoom(13)
        return location
      }
    } catch (error) {
      console.error('Geocoding failed:', error)
    }
    
    return null
  }

  searchNearby(center: google.maps.LatLng, radiusKm: number): any[] {
    if (this.fallbackToSample) {
      // Filter sample data by distance (rough calculation)
      const centerLat = center.lat()
      const centerLng = center.lng()
      
      return sampleChargers.filter(charger => {
        const distance = this.calculateDistance(
          centerLat, centerLng,
          charger.latitude, charger.longitude
        )
        return distance <= radiusKm
      })
    }

    // In real implementation, this would call the backend API
    // with the center coordinates and radius
    return []
  }

  private calculateDistance(lat1: number, lng1: number, lat2: number, lng2: number): number {
    const R = 6371 // Earth's radius in km
    const dLat = this.toRad(lat2 - lat1)
    const dLng = this.toRad(lng2 - lng1)
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(this.toRad(lat1)) * Math.cos(this.toRad(lat2)) *
              Math.sin(dLng/2) * Math.sin(dLng/2)
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
    return R * c
  }

  private toRad(deg: number): number {
    return deg * (Math.PI/180)
  }

  clearMarkers(): void {
    this.markers.forEach(marker => marker.setMap(null))
    this.markers = []
    
    if (this.markerClusterer) {
      this.markerClusterer.clearMarkers()
      this.markerClusterer = null
    }
  }

  private getMapStyles(): google.maps.MapTypeStyle[] {
    return [
      {
        featureType: 'poi',
        elementType: 'labels',
        stylers: [{ visibility: 'off' }]
      },
      {
        featureType: 'transit',
        elementType: 'labels',
        stylers: [{ visibility: 'off' }]
      }
    ]
  }

  getFallbackData(): any[] {
    return sampleChargers
  }

  destroy(): void {
    this.clearMarkers()
    this.mapInstance = null
    this.infoWindow = null
    this.geocoder = null
  }
}

export const mapsService = new MapsService()
export default mapsService