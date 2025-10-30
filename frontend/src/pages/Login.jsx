import React, { useState } from 'react'
import { Container, Row, Col, Card, Form, Button, Alert } from 'react-bootstrap'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const Login = () => {
  const [formData, setFormData] = useState({
    login_id: '',
    password: ''
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  // Get auth context - this should throw an error if useAuth is used outside provider
  const auth = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const from = location.state?.from?.pathname || '/'

  // Debug: Check if auth context has login function
  React.useEffect(() => {
    console.log('🔍 Auth context:', auth)
    console.log('🔍 Login function available:', typeof auth.login === 'function')
  }, [auth])

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
    // Clear error when user starts typing
    if (error) setError('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!formData.login_id || !formData.password) {
      setError('Please fill in all fields')
      return
    }

    // Check if login function exists
    if (typeof auth.login !== 'function') {
      setError('Authentication system error. Please refresh the page.')
      console.error('Login function not found in auth context:', auth)
      return
    }

    setLoading(true)

    try {
      console.log('🔄 Calling auth.login...')
      const result = await auth.login(formData)
      console.log('✅ Login result:', result)

      if (result.success) {
        console.log('✅ Login successful, redirecting to:', from)
        navigate(from, { replace: true })
      } else {
        setError(result.error || 'Login failed')
      }
    } catch (err) {
      console.error('❌ Login error:', err)
      setError('An unexpected error occurred')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Container className="mt-5">
      <Row className="justify-content-center">
        <Col md={6} lg={4}>
          <Card className="shadow">
            <Card.Body className="p-4">
              <div className="text-center mb-4">
                <h2 className="fw-bold">Login</h2>
                <p className="text-muted">Welcome back to Belo2 Store</p>
              </div>

              {error && (
                <Alert variant="danger" className="mb-3">
                  <i className="fas fa-exclamation-triangle me-2"></i>
                  {error}
                </Alert>
              )}

              <Form onSubmit={handleSubmit}>
                <Form.Group className="mb-3">
                  <Form.Label>Email, Phone, or Username</Form.Label>
                  <Form.Control
                    type="text"
                    name="login_id"
                    value={formData.login_id}
                    onChange={handleChange}
                    required
                    placeholder="Enter your email, phone, or username"
                    disabled={loading}
                  />
                </Form.Group>

                <Form.Group className="mb-4">
                  <Form.Label>Password</Form.Label>
                  <Form.Control
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    required
                    placeholder="Enter your password"
                    disabled={loading}
                  />
                </Form.Group>

                <Button
                  variant="primary"
                  type="submit"
                  className="w-100 py-2"
                  disabled={loading}
                  size="lg"
                >
                  {loading ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2" role="status"></span>
                      Logging in...
                    </>
                  ) : (
                    'Login'
                  )}
                </Button>
              </Form>

              <div className="text-center mt-4">
                <p className="mb-2">
                  Don't have an account? <Link to="/register" className="text-decoration-none">Register here</Link>
                </p>
                <p className="mb-0">
                  <Link to="/forgot-password" className="text-decoration-none">Forgot your password?</Link>
                </p>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  )
}

export default Login