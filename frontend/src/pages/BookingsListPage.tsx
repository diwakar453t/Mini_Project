import { motion } from 'framer-motion'

import { useQuery } from 'react-query'
import apiService from '@/services/api'

const BookingsListPage = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="max-w-7xl mx-auto px-4 py-8"
      >
        <h1 className="text-3xl font-bold text-gray-900 mb-8">My Bookings</h1>
        <div className="text-center py-20 text-gray-500">
          Bookings list coming soon...
        </div>
      </motion.div>
    </div>
  )
}

export default BookingsListPage