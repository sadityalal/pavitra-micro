import React, { createContext, useContext, useState, useEffect } from 'react'
import { getSiteSettings } from '../services/api'

const SiteSettingsContext = createContext()

export const useSiteSettings = () => {
  const context = useContext(SiteSettingsContext)
  if (!context) {
    throw new Error('useSiteSettings must be used within a SiteSettingsProvider')
  }
  return context
}

export const SiteSettingsProvider = ({ children }) => {
  const [settings, setSettings] = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const siteSettings = await getSiteSettings()
        setSettings(siteSettings)
      } catch (error) {
        console.error('Failed to fetch site settings:', error)
        // Set default settings if API fails
        setSettings({
          site_name: 'Pavitra Trading',
          currency_symbol: '₹',
          free_shipping_min_amount: '500',
          return_period_days: '30'
        })
      } finally {
        setLoading(false)
      }
    }

    fetchSettings()
  }, [])

  const value = {
    settings,
    loading,
    setSettings
  }

  return (
    <SiteSettingsContext.Provider value={value}>
      {children}
    </SiteSettingsContext.Provider>
  )
}
