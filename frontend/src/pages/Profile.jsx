import React, { useState, useEffect } from 'react'
import { Container, Row, Col, Card, Form, Button, Tab, Nav, Alert, Badge } from 'react-bootstrap'
import { API } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import PageHeader from '../components/layout/PageHeader'
import LoadingSpinner from '../components/common/LoadingSpinner'

const Profile = () => {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('profile')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [profileData, setProfileData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    date_of_birth: ''
  })
  const [addresses, setAddresses] = useState([])
  const [newAddress, setNewAddress] = useState({
    full_name: '',
    address_line1: '',
    address_line2: '',
    city: '',
    state: '',
    postal_code: '',
    country: 'India',
    phone: '',
    address_type: 'shipping',
    is_default: false
  })

  useEffect(() => {
    if (user) {
      setProfileData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
        phone: user.phone || '',
        date_of_birth: user.date_of_birth || ''
      })
    }
    loadAddresses()
  }, [user])

  const loadAddresses = async () => {
    try {
      setLoading(true)
      const response = await API.users.getAddresses()
      setAddresses(response.data)
    } catch (error) {
      console.error('Error loading addresses:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleProfileUpdate = async (e) => {
    e.preventDefault()
    try {
      setSaving(true)
      await API.users.updateProfile(profileData)
      setMessage('Profile updated successfully!')
    } catch (error) {
      setMessage('Error updating profile')
    } finally {
      setSaving(false)
    }
  }

  const handleAddAddress = async (e) => {
    e.preventDefault()
    try {
      setSaving(true)
      await API.users.addAddress(newAddress)
      setMessage('Address added successfully!')
      setNewAddress({
        full_name: '',
        address_line1: '',
        address_line2: '',
        city: '',
        state: '',
        postal_code: '',
        country: 'India',
        phone: '',
        address_type: 'shipping',
        is_default: false
      })
      loadAddresses()
    } catch (error) {
      setMessage('Error adding address')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <>
        <PageHeader title="My Profile" />
        <LoadingSpinner text="Loading profile..." />
      </>
    )
  }

  return (
    <>
      <PageHeader title="My Profile" />
      <Container>
        {message && (
          <Alert variant={message.includes('Error') ? 'danger' : 'success'} dismissible onClose={() => setMessage('')}>
            {message}
          </Alert>
        )}

        <Tab.Container activeKey={activeTab} onSelect={setActiveTab}>
          <Row>
            <Col lg={3}>
              <Card>
                <Card.Body>
                  <Nav variant="pills" className="flex-column">
                    <Nav.Item>
                      <Nav.Link eventKey="profile">Profile Information</Nav.Link>
                    </Nav.Item>
                    <Nav.Item>
                      <Nav.Link eventKey="addresses">Addresses</Nav.Link>
                    </Nav.Item>
                    <Nav.Item>
                      <Nav.Link eventKey="security">Security</Nav.Link>
                    </Nav.Item>
                  </Nav>
                </Card.Body>
              </Card>
            </Col>

            <Col lg={9}>
              <Tab.Content>
                {/* Profile Tab */}
                <Tab.Pane eventKey="profile">
                  <Card>
                    <Card.Header>
                      <h5 className="mb-0">Profile Information</h5>
                    </Card.Header>
                    <Card.Body>
                      <Form onSubmit={handleProfileUpdate}>
                        <Row>
                          <Col md={6}>
                            <Form.Group className="mb-3">
                              <Form.Label>First Name</Form.Label>
                              <Form.Control
                                type="text"
                                value={profileData.first_name}
                                onChange={(e) => setProfileData({...profileData, first_name: e.target.value})}
                              />
                            </Form.Group>
                          </Col>
                          <Col md={6}>
                            <Form.Group className="mb-3">
                              <Form.Label>Last Name</Form.Label>
                              <Form.Control
                                type="text"
                                value={profileData.last_name}
                                onChange={(e) => setProfileData({...profileData, last_name: e.target.value})}
                              />
                            </Form.Group>
                          </Col>
                        </Row>

                        <Form.Group className="mb-3">
                          <Form.Label>Email</Form.Label>
                          <Form.Control
                            type="email"
                            value={profileData.email}
                            disabled
                          />
                          <Form.Text className="text-muted">
                            Email cannot be changed
                          </Form.Text>
                        </Form.Group>

                        <Form.Group className="mb-3">
                          <Form.Label>Phone</Form.Label>
                          <Form.Control
                            type="tel"
                            value={profileData.phone}
                            onChange={(e) => setProfileData({...profileData, phone: e.target.value})}
                          />
                        </Form.Group>

                        <Button type="submit" variant="primary" disabled={saving}>
                          {saving ? 'Saving...' : 'Update Profile'}
                        </Button>
                      </Form>
                    </Card.Body>
                  </Card>
                </Tab.Pane>

                {/* Addresses Tab */}
                <Tab.Pane eventKey="addresses">
                  <Card>
                    <Card.Header>
                      <h5 className="mb-0">My Addresses</h5>
                    </Card.Header>
                    <Card.Body>
                      <h6>Add New Address</h6>
                      <Form onSubmit={handleAddAddress} className="mb-4">
                        <Row>
                          <Col md={6}>
                            <Form.Group className="mb-3">
                              <Form.Label>Full Name</Form.Label>
                              <Form.Control
                                type="text"
                                value={newAddress.full_name}
                                onChange={(e) => setNewAddress({...newAddress, full_name: e.target.value})}
                                required
                              />
                            </Form.Group>
                          </Col>
                          <Col md={6}>
                            <Form.Group className="mb-3">
                              <Form.Label>Phone</Form.Label>
                              <Form.Control
                                type="tel"
                                value={newAddress.phone}
                                onChange={(e) => setNewAddress({...newAddress, phone: e.target.value})}
                                required
                              />
                            </Form.Group>
                          </Col>
                        </Row>

                        <Form.Group className="mb-3">
                          <Form.Label>Address Line 1</Form.Label>
                          <Form.Control
                            type="text"
                            value={newAddress.address_line1}
                            onChange={(e) => setNewAddress({...newAddress, address_line1: e.target.value})}
                            required
                          />
                        </Form.Group>

                        <Form.Group className="mb-3">
                          <Form.Label>Address Line 2</Form.Label>
                          <Form.Control
                            type="text"
                            value={newAddress.address_line2}
                            onChange={(e) => setNewAddress({...newAddress, address_line2: e.target.value})}
                          />
                        </Form.Group>

                        <Row>
                          <Col md={4}>
                            <Form.Group className="mb-3">
                              <Form.Label>City</Form.Label>
                              <Form.Control
                                type="text"
                                value={newAddress.city}
                                onChange={(e) => setNewAddress({...newAddress, city: e.target.value})}
                                required
                              />
                            </Form.Group>
                          </Col>
                          <Col md={4}>
                            <Form.Group className="mb-3">
                              <Form.Label>State</Form.Label>
                              <Form.Control
                                type="text"
                                value={newAddress.state}
                                onChange={(e) => setNewAddress({...newAddress, state: e.target.value})}
                                required
                              />
                            </Form.Group>
                          </Col>
                          <Col md={4}>
                            <Form.Group className="mb-3">
                              <Form.Label>Postal Code</Form.Label>
                              <Form.Control
                                type="text"
                                value={newAddress.postal_code}
                                onChange={(e) => setNewAddress({...newAddress, postal_code: e.target.value})}
                                required
                              />
                            </Form.Group>
                          </Col>
                        </Row>

                        <Row>
                          <Col md={6}>
                            <Form.Group className="mb-3">
                              <Form.Label>Address Type</Form.Label>
                              <Form.Select
                                value={newAddress.address_type}
                                onChange={(e) => setNewAddress({...newAddress, address_type: e.target.value})}
                              >
                                <option value="shipping">Shipping</option>
                                <option value="billing">Billing</option>
                                <option value="both">Both</option>
                              </Form.Select>
                            </Form.Group>
                          </Col>
                          <Col md={6}>
                            <Form.Group className="mb-3">
                              <Form.Check
                                type="checkbox"
                                label="Set as default address"
                                checked={newAddress.is_default}
                                onChange={(e) => setNewAddress({...newAddress, is_default: e.target.checked})}
                              />
                            </Form.Group>
                          </Col>
                        </Row>

                        <Button type="submit" variant="primary" disabled={saving}>
                          {saving ? 'Adding...' : 'Add Address'}
                        </Button>
                      </Form>

                      <h6>Saved Addresses</h6>
                      {addresses.map(address => (
                        <Card key={address.id} className="mb-3">
                          <Card.Body>
                            <div className="d-flex justify-content-between">
                              <div>
                                <strong>{address.full_name}</strong>
                                <p className="mb-1">{address.address_line1}</p>
                                {address.address_line2 && <p className="mb-1">{address.address_line2}</p>}
                                <p className="mb-1">{address.city}, {address.state} - {address.postal_code}</p>
                                <p className="mb-1">{address.country}</p>
                                <p className="mb-0">Phone: {address.phone}</p>
                              </div>
                              <div>
                                <Badge bg="secondary" className="me-2">
                                  {address.address_type}
                                </Badge>
                                {address.is_default && (
                                  <Badge bg="primary">Default</Badge>
                                )}
                              </div>
                            </div>
                          </Card.Body>
                        </Card>
                      ))}
                    </Card.Body>
                  </Card>
                </Tab.Pane>

                {/* Security Tab */}
                <Tab.Pane eventKey="security">
                  <Card>
                    <Card.Header>
                      <h5 className="mb-0">Security Settings</h5>
                    </Card.Header>
                    <Card.Body>
                      <p>Security features coming soon...</p>
                    </Card.Body>
                  </Card>
                </Tab.Pane>
              </Tab.Content>
            </Col>
          </Row>
        </Tab.Container>
      </Container>
    </>
  )
}

export default Profile