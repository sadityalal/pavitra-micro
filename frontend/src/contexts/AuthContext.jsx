import React, { createContext, useState, useContext, useEffect } from 'react'
import { authAPI, API } from '../services/api'

const AuthContext = createContext()

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [token, setToken] = useState(localStorage.getItem('token'))

  useEffect(() => {
    if (token) {
      verifyToken()
    } else {
      setLoading(false)
    }
  }, [token])

  const verifyToken = async () => {
    try {
      console.log('🔄 Verifying token...')
      const userResponse = await API.users.getProfile()
      console.log('✅ Token valid, user:', userResponse.data)
      setUser(userResponse.data)
    } catch (error) {
      console.error('❌ Token verification failed:', error)
      logout()
    } finally {
      setLoading(false)
    }
  }

  const login = async (credentials) => {
    try {
      console.log('🔄 Starting login with:', credentials)

      // Clear any existing token first
      localStorage.removeItem('token')

      const response = await authAPI.post('/login', credentials)
      console.log('✅ Auth login successful:', response.data)

      const { access_token, user_roles, user_permissions } = response.data

      if (!access_token) {
        throw new Error('No access token received')
      }

      // Store token
      setToken(access_token)
      localStorage.setItem('token', access_token)
      console.log('✅ Token stored')

      // Create user object from response
      const userData = {
        id: response.data.user_id, // If available in response
        email: credentials.login_id, // Use login_id as fallback
        first_name: '', // Will be populated from profile
        last_name: '', // Will be populated from profile
        roles: user_roles || ['customer'],
        permissions: user_permissions || []
      }

      setUser(userData)
      console.log('✅ Login completed successfully')

      return { success: true }
    } catch (error) {
      console.error('❌ Login failed:', error)

      // Clear token on failure
      localStorage.removeItem('token')
      setToken(null)
      setUser(null)

      const errorMessage = error.response?.data?.detail ||
                          error.response?.data?.message ||
                          error.message ||
                          'Login failed'

      return {
        success: false,
        error: errorMessage
      }
    }
  }

  const register = async (userData) => {
      try {
        console.log('🔄 Starting registration with data:', userData)

        // Clear any existing token first
        localStorage.removeItem('token')

        // Create FormData for registration
        const formData = new FormData()

        // Append all fields to FormData
        Object.keys(userData).forEach(key => {
          if (userData[key] !== null && userData[key] !== undefined) {
            formData.append(key, userData[key])
          }
        })

        console.log('🔄 Sending registration request...')
        const response = await authAPI.post('/register', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })

        console.log('✅ Registration successful:', response.data)

        const { access_token, user_roles, user_permissions } = response.data

        if (!access_token) {
          throw new Error('No access token received')
        }

        // Store token
        setToken(access_token)
        localStorage.setItem('token', access_token)
        console.log('✅ Token stored')

        // Create user object
        const newUser = {
          first_name: userData.first_name,
          last_name: userData.last_name,
          email: userData.email,
          phone: userData.phone,
          username: userData.username,
          roles: user_roles || ['customer'],
          permissions: user_permissions || []
        }

        setUser(newUser)
        console.log('✅ Registration completed successfully')

        return { success: true }
      } catch (error) {
        console.error('❌ Registration failed:', error)

        // Clear token on failure
        localStorage.removeItem('token')
        setToken(null)
        setUser(null)

        const errorMessage = error.response?.data?.detail ||
                            error.response?.data?.message ||
                            error.message ||
                            'Registration failed'

        return {
          success: false,
          error: errorMessage
        }
      }
    }

  const logout = async () => {
    try {
      await authAPI.post('/logout')
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      setUser(null)
      setToken(null)
      localStorage.removeItem('token')
    }
  }

  const value = {
    user,
    token,
    loading,
    login, // Make sure this is included
    register, // Make sure this is included
    logout, // Make sure this is included
    isAuthenticated: !!user && !!token,
    hasRole: (role) => user?.roles?.includes(role),
    hasPermission: (permission) => user?.permissions?.includes(permission)
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}