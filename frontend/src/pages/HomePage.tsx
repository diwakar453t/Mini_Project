import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Search,
  Zap,
  MapPin,
  Star,
  TrendingUp,
  Users,
  Shield,
  Smartphone,
  ArrowRight,
  ChevronDown,
} from 'lucide-react'

import { useAuth } from '@/hooks/useAuth'

const HomePage = () => {
  const { isAuthenticated, user } = useAuth()
  const [searchQuery, setSearchQuery] = useState('')

  const stats = [
    { label: 'Active Chargers', value: '2,500+', icon: Zap },
    { label: 'Cities Covered', value: '50+', icon: MapPin },
    { label: 'Happy Users', value: '10,000+', icon: Users },
    { label: 'Average Rating', value: '4.8', icon: Star },
  ]

  const features = [
    {
      title: 'Find Nearby Chargers',
      description: 'Locate EV chargers near you with real-time availability and pricing',
      icon: Search,
      color: 'bg-blue-100 text-blue-600',
    },
    {
      title: 'Instant Booking',
      description: 'Book your charging slot in seconds with secure payments',
      icon: Zap,
      color: 'bg-green-100 text-green-600',
    },
    {
      title: 'Earn by Hosting',
      description: 'Share your charger and earn money from other EV drivers',
      icon: TrendingUp,
      color: 'bg-purple-100 text-purple-600',
    },
    {
      title: 'Trust & Safety',
      description: 'KYC-verified hosts and 24/7 customer support for peace of mind',
      icon: Shield,
      color: 'bg-red-100 text-red-600',
    },
  ]

  const cities = [
    'Mumbai', 'Delhi', 'Bengaluru', 'Chennai', 'Hyderabad', 'Pune',
    'Ahmedabad', 'Kolkata', 'Jaipur', 'Kochi', 'Indore', 'Chandigarh'
  ]

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      window.location.href = `/search?q=${encodeURIComponent(searchQuery.trim())}`
    }
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-primary-50 via-white to-secondary-50">
        {/* Background Pattern */}
        <div className="absolute inset-0 pattern-mandala opacity-30"></div>
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 lg:py-24">
          <div className="text-center">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
            >
              <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
                India's First{' '}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-secondary-600">
                  EV Charger
                </span>
                <br />
                Sharing Platform
              </h1>
              
              <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
                Find, book, and share EV chargers across India. Join thousands of drivers 
                and hosts creating a sustainable future together.
              </p>

              {/* Search Bar */}
              <motion.form
                onSubmit={handleSearch}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.2 }}
                className="max-w-2xl mx-auto mb-8"
              >
                <div className="relative flex items-center bg-white rounded-2xl shadow-lg border border-gray-100">
                  <div className="flex items-center pl-6">
                    <MapPin className="w-5 h-5 text-gray-400" />
                  </div>
                  <input
                    type="text"
                    placeholder="Search by city, area, or landmark..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="flex-1 px-4 py-4 bg-transparent border-0 text-gray-900 placeholder-gray-500 focus:outline-none"
                  />
                  <button
                    type="submit"
                    className="m-2 px-6 py-2 bg-primary-500 text-white rounded-xl hover:bg-primary-600 transition-colors font-medium flex items-center space-x-2"
                  >
                    <Search className="w-4 h-4" />
                    <span>Find Chargers</span>
                  </button>
                </div>
              </motion.form>

              {/* CTA Buttons */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.4 }}
                className="flex flex-col sm:flex-row gap-4 justify-center items-center"
              >
                <Link
                  to="/search"
                  className="btn-primary flex items-center space-x-2"
                >
                  <Zap className="w-5 h-5" />
                  <span>Book a Charger</span>
                </Link>
                
                <Link
                  to={isAuthenticated ? '/profile#become-host' : '/auth'}
                  className="btn-outline flex items-center space-x-2"
                >
                  <TrendingUp className="w-5 h-5" />
                  <span>Become a Host</span>
                </Link>
              </motion.div>
            </motion.div>
          </div>
        </div>

        {/* Scroll Indicator */}
        <motion.div
          animate={{ y: [0, 10, 0] }}
          transition={{ repeat: Infinity, duration: 2 }}
          className="absolute bottom-8 left-1/2 transform -translate-x-1/2"
        >
          <ChevronDown className="w-6 h-6 text-gray-400" />
        </motion.div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className="text-center"
              >
                <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <stat.icon className="w-6 h-6 text-primary-600" />
                </div>
                <div className="text-3xl font-bold text-gray-900 mb-2">
                  {stat.value}
                </div>
                <div className="text-gray-600">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
              Why Choose ChargeMitra?
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Experience the most convenient and reliable EV charging network in India
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className="card-hover text-center"
              >
                <div className={`w-16 h-16 ${feature.color} rounded-2xl flex items-center justify-center mx-auto mb-6`}>
                  <feature.icon className="w-8 h-8" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-4">
                  {feature.title}
                </h3>
                <p className="text-gray-600">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Cities Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
              Available in Major Cities
            </h2>
            <p className="text-xl text-gray-600">
              Growing fast across India with new cities added every month
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {cities.map((city, index) => (
              <motion.div
                key={city}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, delay: index * 0.05 }}
                whileHover={{ scale: 1.05 }}
                className="bg-gray-50 rounded-xl p-6 text-center hover:bg-primary-50 hover:text-primary-600 transition-all cursor-pointer"
                onClick={() => window.location.href = `/search?city=${encodeURIComponent(city)}`}
              >
                <MapPin className="w-6 h-6 mx-auto mb-2 text-current" />
                <div className="font-medium">{city}</div>
              </motion.div>
            ))}
          </div>

          <div className="text-center mt-12">
            <Link
              to="/search"
              className="btn-outline inline-flex items-center space-x-2"
            >
              <span>Explore All Cities</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-br from-primary-500 to-secondary-500 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-6">
              Ready to Start Your EV Journey?
            </h2>
            <p className="text-xl mb-8 opacity-90">
              Join thousands of Indians making the switch to sustainable transportation
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Link
                to="/search"
                className="bg-white text-primary-600 px-8 py-4 rounded-xl font-semibold hover:bg-gray-50 transition-colors flex items-center space-x-2"
              >
                <Smartphone className="w-5 h-5" />
                <span>Download Our App</span>
              </Link>
              
              <Link
                to={isAuthenticated ? '/profile' : '/auth'}
                className="border-2 border-white px-8 py-4 rounded-xl font-semibold hover:bg-white hover:text-primary-600 transition-colors"
              >
                {isAuthenticated ? 'Go to Dashboard' : 'Sign Up Free'}
              </Link>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  )
}

export default HomePage