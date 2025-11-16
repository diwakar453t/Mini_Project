import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  CreditCard,
  Smartphone,
  Wallet,
  CheckCircle,
  XCircle,
  Loader2,
  ArrowLeft,
  AlertCircle,
  Copy,
  Share2,
  Download
} from 'lucide-react'
import toast from 'react-hot-toast'
import confetti from 'canvas-confetti'

import { useAuth } from '@/hooks/useAuth'
import { cn } from '@/utils/cn'

interface PaymentMethod {
  id: string
  name: string
  description: string
  icon: any
  color: string
  testInfo: string
}

interface PaymentResult {
  success: boolean
  transactionId: string
  amount: number
  message: string
  bookingId: number
}

const DummyPaymentPage = () => {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  
  // Get payment details from URL
  const bookingId = searchParams.get('booking_id')
  const amount = parseFloat(searchParams.get('amount') || '0')
  const paymentId = searchParams.get('payment_id')
  const method = searchParams.get('method') || 'card'
  
  // State
  const [selectedMethod, setSelectedMethod] = useState(method)
  const [isProcessing, setIsProcessing] = useState(false)
  const [paymentResult, setPaymentResult] = useState<PaymentResult | null>(null)
  const [simulateFailure, setSimulateFailure] = useState(false)
  const [networkDelay, setNetworkDelay] = useState(3)
  const [showAdvanced, setShowAdvanced] = useState(false)

  // Developer controls
  const [devMode, setDevMode] = useState(false)

  const paymentMethods: PaymentMethod[] = [
    {
      id: 'upi',
      name: 'UPI',
      description: 'Pay using Google Pay, PhonePe, or any UPI app',
      icon: Smartphone,
      color: 'bg-blue-500',
      testInfo: 'Use success@paytm for success, failure@paytm for failure'
    },
    {
      id: 'card',
      name: 'Credit/Debit Card',
      description: 'Visa, Mastercard, Rupay accepted',
      icon: CreditCard,
      color: 'bg-purple-500',
      testInfo: '4111 1111 1111 1111 (success), 4000 0000 0000 0002 (failure)'
    },
    {
      id: 'wallet',
      name: 'Digital Wallet',
      description: 'Paytm, Amazon Pay, MobiKwik',
      icon: Wallet,
      color: 'bg-green-500',
      testInfo: 'wallet_success_123 (success), wallet_failure_456 (failure)'
    }
  ]

  // Auto-enable dev mode if in development
  useEffect(() => {
    if (import.meta.env.DEV) {
      setDevMode(true)
    }
  }, [])

  // Handle payment processing
  const processPayment = async () => {
    if (!bookingId || !amount) {
      toast.error('Invalid payment parameters')
      return
    }

    setIsProcessing(true)

    try {
      // Simulate network delay
      await new Promise(resolve => setTimeout(resolve, networkDelay * 1000))

      // Generate transaction ID
      const transactionId = `TXN${Date.now()}${Math.random().toString(36).substr(2, 6).toUpperCase()}`

      // Simulate payment processing
      const success = !simulateFailure && Math.random() > 0.1 // 90% success rate by default

      // Call backend to complete payment
      const response = await fetch('/api/v1/payments/dummy/complete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}` // Simplified for demo
        },
        body: JSON.stringify({
          booking_id: parseInt(bookingId),
          status: success ? 'SUCCESS' : 'FAILED',
          transaction_id: transactionId,
          failure_reason: simulateFailure ? 'Simulated failure for testing' : undefined
        })
      })

      const result = await response.json()

      setPaymentResult({
        success,
        transactionId,
        amount,
        message: success ? 'Payment completed successfully!' : 'Payment failed. Please try again.',
        bookingId: parseInt(bookingId)
      })

      // Show confetti on success (respecting reduced motion)
      if (success && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        confetti({
          particleCount: 100,
          spread: 70,
          origin: { y: 0.6 },
          colors: ['#FF9933', '#00695C', '#3F51B5']
        })
      }

    } catch (error) {
      console.error('Payment processing error:', error)
      setPaymentResult({
        success: false,
        transactionId: 'ERROR_' + Date.now(),
        amount,
        message: 'Payment processing failed. Please try again.',
        bookingId: parseInt(bookingId)
      })
    } finally {
      setIsProcessing(false)
    }
  }

  // Handle method selection
  const selectMethod = (methodId: string) => {
    setSelectedMethod(methodId)
  }

  // Handle transaction copy
  const copyTransactionId = () => {
    if (paymentResult?.transactionId) {
      navigator.clipboard.writeText(paymentResult.transactionId)
      toast.success('Transaction ID copied!')
    }
  }

  // Handle payment retry
  const retryPayment = () => {
    setPaymentResult(null)
    setSimulateFailure(false)
  }

  // Handle back navigation
  const handleBack = () => {
    if (paymentResult?.success) {
      navigate(`/bookings/${bookingId}`)
    } else {
      navigate(-1)
    }
  }

  if (!bookingId || !amount) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Invalid Payment Link</h2>
          <p className="text-gray-600 mb-6">The payment link appears to be invalid or expired.</p>
          <button onClick={() => navigate('/')} className="btn-primary">
            Go Home
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <button
            onClick={handleBack}
            className="btn-ghost inline-flex items-center space-x-2"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back</span>
          </button>
          
          {devMode && (
            <div className="bg-yellow-100 border border-yellow-300 rounded-lg px-3 py-2">
              <span className="text-xs font-medium text-yellow-800">
                🧪 DEMO MODE - Test payments only
              </span>
            </div>
          )}
        </div>

        <div className="max-w-md mx-auto">
          <AnimatePresence mode="wait">
            {!paymentResult ? (
              <motion.div
                key="payment-form"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="bg-white rounded-2xl shadow-lg overflow-hidden"
              >
                {/* Payment Header */}
                <div className="bg-gradient-to-r from-primary-500 to-secondary-500 px-6 py-8 text-white text-center">
                  <h1 className="text-2xl font-bold mb-2">Complete Payment</h1>
                  <div className="text-3xl font-bold mb-1">₹{amount.toFixed(2)}</div>
                  <div className="text-primary-100 text-sm">Booking #{bookingId}</div>
                </div>

                <div className="p-6 space-y-6">
                  {/* Payment Methods */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Choose Payment Method</h3>
                    <div className="space-y-3">
                      {paymentMethods.map((method) => (
                        <button
                          key={method.id}
                          onClick={() => selectMethod(method.id)}
                          className={cn(
                            'w-full p-4 border rounded-xl transition-all text-left',
                            selectedMethod === method.id
                              ? 'border-primary-500 bg-primary-50 ring-2 ring-primary-500'
                              : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                          )}
                        >
                          <div className="flex items-center space-x-3">
                            <div className={cn(
                              'w-10 h-10 rounded-lg flex items-center justify-center text-white',
                              method.color
                            )}>
                              <method.icon className="w-5 h-5" />
                            </div>
                            <div className="flex-1">
                              <div className="font-medium text-gray-900">{method.name}</div>
                              <div className="text-sm text-gray-500">{method.description}</div>
                              {devMode && (
                                <div className="text-xs text-gray-400 mt-1 font-mono">
                                  Test: {method.testInfo}
                                </div>
                              )}
                            </div>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Developer Controls */}
                  {devMode && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      className="border border-gray-200 rounded-lg p-4 bg-gray-50"
                    >
                      <button
                        onClick={() => setShowAdvanced(!showAdvanced)}
                        className="flex items-center justify-between w-full text-sm font-medium text-gray-700 mb-2"
                      >
                        <span>🛠️ Developer Controls</span>
                        <span className={cn(
                          'transform transition-transform',
                          showAdvanced ? 'rotate-180' : ''
                        )}>▼</span>
                      </button>
                      
                      <AnimatePresence>
                        {showAdvanced && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            className="space-y-3"
                          >
                            <div>
                              <label className="flex items-center space-x-2">
                                <input
                                  type="checkbox"
                                  checked={simulateFailure}
                                  onChange={(e) => setSimulateFailure(e.target.checked)}
                                  className="rounded border-gray-300"
                                />
                                <span className="text-sm text-gray-600">Simulate payment failure</span>
                              </label>
                            </div>
                            
                            <div>
                              <label className="block text-sm text-gray-600 mb-1">
                                Network delay: {networkDelay}s
                              </label>
                              <input
                                type="range"
                                min="1"
                                max="10"
                                value={networkDelay}
                                onChange={(e) => setNetworkDelay(parseInt(e.target.value))}
                                className="w-full"
                              />
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </motion.div>
                  )}

                  {/* Security Notice */}
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-start space-x-3">
                      <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
                      <div>
                        <h4 className="font-medium text-blue-900">Secure Payment</h4>
                        <p className="text-sm text-blue-700 mt-1">
                          {devMode 
                            ? 'This is a simulated payment for testing. No real money will be charged.'
                            : 'Your payment is secured with 256-bit encryption. We do not store your card details.'
                          }
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Pay Button */}
                  <button
                    onClick={processPayment}
                    disabled={isProcessing}
                    className="w-full btn-primary text-lg py-4 relative overflow-hidden"
                  >
                    <AnimatePresence mode="wait">
                      {isProcessing ? (
                        <motion.div
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          exit={{ opacity: 0 }}
                          className="flex items-center justify-center space-x-2"
                        >
                          <Loader2 className="w-5 h-5 animate-spin" />
                          <span>Processing Payment...</span>
                        </motion.div>
                      ) : (
                        <motion.div
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          exit={{ opacity: 0 }}
                          className="flex items-center justify-center space-x-2"
                        >
                          <span>Pay ₹{amount.toFixed(2)}</span>
                        </motion.div>
                      )}
                    </AnimatePresence>

                    {/* Processing animation overlay */}
                    {isProcessing && (
                      <motion.div
                        initial={{ x: '-100%' }}
                        animate={{ x: '100%' }}
                        transition={{ repeat: Infinity, duration: 1.5 }}
                        className="absolute inset-y-0 w-1/3 bg-gradient-to-r from-transparent via-white/20 to-transparent"
                      />
                    )}
                  </button>

                  {devMode && (
                    <div className="text-xs text-center text-gray-500">
                      This is a dummy payment interface for development testing
                    </div>
                  )}
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="payment-result"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="bg-white rounded-2xl shadow-lg overflow-hidden text-center"
              >
                {/* Result Header */}
                <div className={cn(
                  'px-6 py-8 text-white',
                  paymentResult.success 
                    ? 'bg-gradient-to-r from-green-500 to-emerald-500'
                    : 'bg-gradient-to-r from-red-500 to-pink-500'
                )}>
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
                    className="w-16 h-16 mx-auto mb-4 flex items-center justify-center"
                  >
                    {paymentResult.success ? (
                      <CheckCircle className="w-16 h-16" />
                    ) : (
                      <XCircle className="w-16 h-16" />
                    )}
                  </motion.div>
                  
                  <h2 className="text-2xl font-bold mb-2">
                    {paymentResult.success ? 'Payment Successful!' : 'Payment Failed'}
                  </h2>
                  <p className="opacity-90">{paymentResult.message}</p>
                </div>

                <div className="p-6 space-y-6">
                  {/* Transaction Details */}
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">Amount</span>
                      <span className="font-semibold">₹{paymentResult.amount.toFixed(2)}</span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">Transaction ID</span>
                      <button
                        onClick={copyTransactionId}
                        className="flex items-center space-x-2 text-primary-600 hover:text-primary-700 transition-colors"
                        onLongPress={copyTransactionId}
                      >
                        <span className="font-mono text-sm">{paymentResult.transactionId}</span>
                        <Copy className="w-4 h-4" />
                      </button>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">Booking ID</span>
                      <span className="font-semibold">#{paymentResult.bookingId}</span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">Payment Method</span>
                      <span className="font-medium capitalize">{selectedMethod}</span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">Date & Time</span>
                      <span className="text-sm">{new Date().toLocaleString('en-IN')}</span>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="space-y-3">
                    {paymentResult.success ? (
                      <>
                        <button
                          onClick={() => navigate(`/bookings/${paymentResult.bookingId}`)}
                          className="w-full btn-primary"
                        >
                          View Booking Details
                        </button>
                        
                        <div className="flex space-x-3">
                          <button
                            onClick={() => {/* Share functionality */}}
                            className="flex-1 btn-outline inline-flex items-center justify-center space-x-2"
                          >
                            <Share2 className="w-4 h-4" />
                            <span>Share</span>
                          </button>
                          
                          <button
                            onClick={() => {/* Download receipt */}}
                            className="flex-1 btn-outline inline-flex items-center justify-center space-x-2"
                          >
                            <Download className="w-4 h-4" />
                            <span>Receipt</span>
                          </button>
                        </div>
                      </>
                    ) : (
                      <>
                        <button
                          onClick={retryPayment}
                          className="w-full btn-primary"
                        >
                          Try Again
                        </button>
                        
                        <button
                          onClick={() => navigate(`/chargers`)}
                          className="w-full btn-outline"
                        >
                          Browse Other Chargers
                        </button>
                      </>
                    )}
                  </div>

                  {devMode && paymentResult.success && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <h4 className="font-medium text-green-900 mb-2">✅ Developer Info</h4>
                      <div className="text-sm text-green-700 space-y-1">
                        <div>Payment completed in dummy mode</div>
                        <div>Booking status updated to: CONFIRMED</div>
                        <div>Host will be notified automatically</div>
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}

export default DummyPaymentPage