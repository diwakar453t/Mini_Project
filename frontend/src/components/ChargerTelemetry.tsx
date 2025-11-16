import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Zap,
  Activity,
  Thermometer,
  Clock,
  Battery,
  Wifi,
  WifiOff,
  AlertTriangle
} from 'lucide-react'

import { useChargerWebSocket, TelemetryUpdate, ChargerStatusUpdate } from '@/hooks/useWebSocket'
import { cn } from '@/utils/cn'

interface ChargerTelemetryProps {
  chargerId: number
  className?: string
}

interface TelemetryData {
  power_output_kw: number
  voltage_v?: number
  current_a?: number
  energy_delivered_kwh: number
  session_duration_minutes: number
  temperature_c?: number
  status: string
  last_update: string
}

const ChargerTelemetry = ({ chargerId, className }: ChargerTelemetryProps) => {
  const [telemetryData, setTelemetryData] = useState<TelemetryData | null>(null)
  const [chargerStatus, setChargerStatus] = useState<string>('offline')
  const [isActive, setIsActive] = useState(false)

  const handleTelemetryUpdate = (data: TelemetryUpdate) => {
    setTelemetryData({
      power_output_kw: data.power_output_kw,
      voltage_v: data.voltage_v,
      current_a: data.current_a,
      energy_delivered_kwh: data.energy_delivered_kwh,
      session_duration_minutes: data.session_duration_minutes,
      temperature_c: data.temperature_c,
      status: data.status,
      last_update: data.timestamp
    })
    setIsActive(true)
  }

  const handleStatusUpdate = (data: ChargerStatusUpdate) => {
    setChargerStatus(data.status)
    setIsActive(data.is_active)
  }

  const { isConnected, isConnecting, lastError, requestTelemetry } = useChargerWebSocket(
    chargerId,
    handleTelemetryUpdate,
    handleStatusUpdate
  )

  // Request initial telemetry data when connected
  useEffect(() => {
    if (isConnected) {
      requestTelemetry()
    }
  }, [isConnected, requestTelemetry])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'available': return 'text-green-600'
      case 'in_use': return 'text-yellow-600'
      case 'maintenance': return 'text-red-600'
      case 'fault': return 'text-red-600'
      case 'offline': return 'text-gray-600'
      default: return 'text-gray-600'
    }
  }

  const getStatusBadge = (status: string) => {
    const baseClasses = 'px-3 py-1 rounded-full text-xs font-medium flex items-center space-x-1'
    
    switch (status) {
      case 'available':
        return (
          <span className={`${baseClasses} bg-green-100 text-green-800`}>
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span>Available</span>
          </span>
        )
      case 'in_use':
        return (
          <span className={`${baseClasses} bg-yellow-100 text-yellow-800`}>
            <motion.div 
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ repeat: Infinity, duration: 2 }}
              className="w-2 h-2 bg-yellow-500 rounded-full"
            ></motion.div>
            <span>In Use</span>
          </span>
        )
      case 'maintenance':
        return (
          <span className={`${baseClasses} bg-orange-100 text-orange-800`}>
            <AlertTriangle className="w-3 h-3" />
            <span>Maintenance</span>
          </span>
        )
      case 'fault':
        return (
          <span className={`${baseClasses} bg-red-100 text-red-800`}>
            <AlertTriangle className="w-3 h-3" />
            <span>Fault</span>
          </span>
        )
      default:
        return (
          <span className={`${baseClasses} bg-gray-100 text-gray-800`}>
            <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
            <span>Offline</span>
          </span>
        )
    }
  }

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`
  }

  if (!isActive && !isConnecting) {
    return (
      <div className={cn('bg-gray-50 rounded-xl p-6 text-center', className)}>
        <WifiOff className="w-8 h-8 text-gray-400 mx-auto mb-3" />
        <h3 className="font-medium text-gray-900 mb-1">Charger Offline</h3>
        <p className="text-sm text-gray-500">
          Real-time data is not available for this charger
        </p>
      </div>
    )
  }

  return (
    <div className={cn('bg-white rounded-xl border border-gray-200 overflow-hidden', className)}>
      {/* Header */}
      <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-gray-900 flex items-center space-x-2">
            <Activity className="w-5 h-5 text-primary-600" />
            <span>Live Telemetry</span>
          </h3>
          
          <div className="flex items-center space-x-3">
            {getStatusBadge(chargerStatus)}
            
            <div className="flex items-center space-x-1 text-xs text-gray-500">
              {isConnected ? (
                <Wifi className="w-4 h-4 text-green-500" />
              ) : (
                <WifiOff className="w-4 h-4 text-gray-400" />
              )}
              <span>{isConnected ? 'Live' : 'Offline'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Connection Status */}
      {isConnecting && (
        <div className="bg-blue-50 border-b border-blue-200 px-6 py-3">
          <div className="flex items-center space-x-2 text-blue-700">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            >
              <Activity className="w-4 h-4" />
            </motion.div>
            <span className="text-sm">Connecting to charger...</span>
          </div>
        </div>
      )}

      {lastError && (
        <div className="bg-red-50 border-b border-red-200 px-6 py-3">
          <div className="flex items-center space-x-2 text-red-700">
            <AlertTriangle className="w-4 h-4" />
            <span className="text-sm">{lastError}</span>
          </div>
        </div>
      )}

      {/* Telemetry Data */}
      <div className="p-6">
        <AnimatePresence>
          {telemetryData ? (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="grid grid-cols-2 md:grid-cols-4 gap-6"
            >
              {/* Power Output */}
              <motion.div 
                className="text-center"
                whileHover={{ scale: 1.05 }}
                transition={{ type: "spring", stiffness: 400 }}
              >
                <div className="w-12 h-12 bg-yellow-100 rounded-xl flex items-center justify-center mx-auto mb-3">
                  <Zap className="w-6 h-6 text-yellow-600" />
                </div>
                <div className="text-2xl font-bold text-gray-900 mb-1">
                  {telemetryData.power_output_kw.toFixed(1)}
                  <span className="text-sm font-normal text-gray-500 ml-1">kW</span>
                </div>
                <div className="text-xs text-gray-600">Power Output</div>
              </motion.div>

              {/* Energy Delivered */}
              <motion.div 
                className="text-center"
                whileHover={{ scale: 1.05 }}
                transition={{ type: "spring", stiffness: 400 }}
              >
                <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mx-auto mb-3">
                  <Battery className="w-6 h-6 text-green-600" />
                </div>
                <div className="text-2xl font-bold text-gray-900 mb-1">
                  {telemetryData.energy_delivered_kwh.toFixed(2)}
                  <span className="text-sm font-normal text-gray-500 ml-1">kWh</span>
                </div>
                <div className="text-xs text-gray-600">Energy Delivered</div>
              </motion.div>

              {/* Session Duration */}
              <motion.div 
                className="text-center"
                whileHover={{ scale: 1.05 }}
                transition={{ type: "spring", stiffness: 400 }}
              >
                <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mx-auto mb-3">
                  <Clock className="w-6 h-6 text-blue-600" />
                </div>
                <div className="text-2xl font-bold text-gray-900 mb-1">
                  {formatDuration(telemetryData.session_duration_minutes)}
                </div>
                <div className="text-xs text-gray-600">Duration</div>
              </motion.div>

              {/* Temperature */}
              {telemetryData.temperature_c && (
                <motion.div 
                  className="text-center"
                  whileHover={{ scale: 1.05 }}
                  transition={{ type: "spring", stiffness: 400 }}
                >
                  <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center mx-auto mb-3">
                    <Thermometer className="w-6 h-6 text-red-600" />
                  </div>
                  <div className="text-2xl font-bold text-gray-900 mb-1">
                    {telemetryData.temperature_c.toFixed(0)}
                    <span className="text-sm font-normal text-gray-500 ml-1">°C</span>
                  </div>
                  <div className="text-xs text-gray-600">Temperature</div>
                </motion.div>
              )}
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-8 text-gray-500"
            >
              <Activity className="w-8 h-8 mx-auto mb-3 opacity-50" />
              <div>Waiting for telemetry data...</div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Technical Details */}
        {telemetryData && (telemetryData.voltage_v || telemetryData.current_a) && (
          <div className="mt-6 pt-6 border-t border-gray-200">
            <h4 className="text-sm font-medium text-gray-900 mb-3">Technical Details</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              {telemetryData.voltage_v && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Voltage:</span>
                  <span className="font-medium">{telemetryData.voltage_v.toFixed(1)} V</span>
                </div>
              )}
              {telemetryData.current_a && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Current:</span>
                  <span className="font-medium">{telemetryData.current_a.toFixed(1)} A</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Last Update */}
        {telemetryData && (
          <div className="mt-4 text-center">
            <div className="text-xs text-gray-500">
              Last updated: {new Date(telemetryData.last_update).toLocaleTimeString()}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default ChargerTelemetry