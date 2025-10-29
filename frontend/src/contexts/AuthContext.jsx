import React, { createContext, useState, useContext, useEffect } from 'react'
import { authAPI } from '../services/api'

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
      // Verify token and get user data
      verifyToken()
    } else {
      setLoading(false)
    }
  }, [token])

  const verifyToken = async () => {
    try {
      const response = await authAPI.refresh()
      const { access_token, user_roles, user_permissions } = response.data

      if (access_token) {
        setToken(access_token)
        localStorage.setItem('token', access_token)

        // Get user profile
        const userResponse = await authAPI.getProfile()
        setUser({
          ...userResponse.data,
          roles: user_roles,
          permissions: user_permissions
        })
      }
    } catch (error) {
      console.error('Token verification failed:', error)
      logout()
    } finally {
      setLoading(false)
    }
  }

  const login = async (credentials) => {
    try {
      const response = await authAPI.login(credentials)
      const { access_token, user_roles, user_permissions } = response.data

      setToken(access_token)
      localStorage.setItem('token', access_token)

      // Get user profile
      const userResponse = await usersAPI.getProfile()
      setUser({
        ...userResponse.data,
        roles: user_roles,
        permissions: user_permissions
      })

      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Login failed'
      }
    }
  }

  const register = async (userData) => {
    try {
      const response = await authAPI.register(userData)
      const { access_token, user_roles, user_permissions } = response.data

      setToken(access_token)
      localStorage.setItem('token', access_token)

      setUser({
        ...userData,
        roles: user_roles,
        permissions: user_permissions
      })

      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Registration failed'
      }
    }
  }

  const logout = async () => {
    try {
      await authAPI.logout()
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
    login,
    register,
    logout,
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