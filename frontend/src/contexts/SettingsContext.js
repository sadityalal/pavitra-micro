import React, { createContext, useContext, useState, useEffect } from 'react'
import { API } from '../services/api'

const SettingsContext = createContext()

export const useSettings = () => {
  const context = useContext(SettingsContext)
  if (!context) {
    throw new Error('useSettings must be used within a SettingsProvider')
  }
  return context
}

export const SettingsProvider = ({ children }) => {
  const [settings, setSettings] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchFrontendSettings = async () => {
    try {
      setLoading(true)
      const response = await API.auth.get('/frontend-settings')
      setSettings(response.data)
    } catch (err) {
      console.error('Failed to fetch frontend settings:', err)
      setError('Failed to load settings')
      // Fallback to default settings
      setSettings({
        site_name: 'Pavitra Enterprises',
        currency: 'INR',
        currency_symbol: '₹',
        free_shipping_threshold: 999,
        return_period_days: 10,
        site_phone: '+91-9711317009',
        site_email: 'support@pavitraenterprises.com'
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchFrontendSettings()
  }, [])

  const value = {
    settings,
    loading,
    error,
    refreshSettings: fetchFrontendSettings
  }

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  )
}