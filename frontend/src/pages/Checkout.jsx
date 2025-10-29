import React, { useState, useEffect } from 'react'
import { Container, Row, Col, Card, Form, Button, Alert, ListGroup } from 'react-bootstrap'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useCart } from '../contexts/CartContext'
import { API } from '../services/api'
import PageHeader from '../components/layout/PageHeader'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorMessage from '../components/common/ErrorMessage'

const Checkout = () => {
  const { user } = useAuth()
  const { cart, loadCart } = useCart()
  const navigate = useNavigate()

  const [loading, setLoading] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [error, setError] = useState('')
  const [addresses, setAddresses] = useState([])
  const [paymentMethods, setPaymentMethods] = useState([])

  const [formData, setFormData] = useState({
    shipping_address_id: '',
    billing_address_id: '',
    payment_method: 'cash_on_delivery',
    use_gst_invoice: false,
    gst_number: '',
    customer_note: ''
  })

  useEffect(() => {
    if (cart.items.length === 0) {
      navigate('/cart')
      return
    }
    loadUserData()
  }, [cart])

  const loadUserData = async () => {
    try {
      setLoading(true)
      const [addressesResponse, paymentMethodsResponse] = await Promise.all([
        API.users.getAddresses(),
        API.payments.getMethods()
      ])

      setAddresses(addressesResponse.data)
      setPaymentMethods(paymentMethodsResponse.data)

      // Set default addresses
      const defaultShipping = addressesResponse.data.find(addr => addr.is_default && addr.address_type === 'shipping')
      const defaultBilling = addressesResponse.data.find(addr => addr.is_default && addr.address_type === 'billing')

      setFormData(prev => ({
        ...prev,
        shipping_address_id: defaultShipping?.id || '',
        billing_address_id: defaultBilling?.id || ''
      }))
    } catch (err) {
      setError('Failed to load user data')
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!formData.shipping_address_id) {
      setError('Please select a shipping address')
      return
    }

    try {
      setProcessing(true)
      setError('')

      const orderData = {
        items: cart.items.map(item => ({
          product_id: item.product_id,
          variation_id: item.variation_id,
          quantity: item.quantity,
          unit_price: item.unit_price
        })),
        shipping_address: addresses.find(addr => addr.id === parseInt(formData.shipping_address_id)),
        billing_address: formData.billing_address_id
          ? addresses.find(addr => addr.id === parseInt(formData.billing_address_id))
          : undefined,
        payment_method: formData.payment_method,
        customer_note: formData.customer_note,
        use_gst_invoice: formData.use_gst_invoice,
        gst_number: formData.gst_number || undefined
      }

      const orderResponse = await API.orders.create(orderData)
      const order = orderResponse.data

      // Process payment if not cash on delivery
      if (formData.payment_method !== 'cash_on_delivery') {
        const paymentData = {
          order_id: order.id,
          amount: order.total_amount,
          payment_method: formData.payment_method,
          gateway: formData.payment_method === 'upi' ? 'razorpay' : 'razorpay'
        }

        const paymentResponse = await API.payments.initiate(paymentData)

        if (formData.payment_method === 'upi') {
          // Handle UPI payment
          window.location.href = paymentResponse.data.payment_page_url
        } else {
          // Handle card payment
          // You would integrate with Razorpay/Stripe here
          alert('Payment integration would be implemented here')
        }
      } else {
        // Cash on delivery - order is confirmed
        navigate('/orders', {
          state: { message: 'Order placed successfully!' }
        })
      }

    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to place order')
    } finally {
      setProcessing(false)
    }
  }

  if (loading) {
    return (
      <>
        <PageHeader title="Checkout" />
        <LoadingSpinner text="Loading checkout..." />
      </>
    )
  }

  return (
    <>
      <PageHeader title="Checkout" />
      <Container>
        <ErrorMessage error={error} />

        <Form onSubmit={handleSubmit}>
          <Row>
            <Col lg={8}>
              {/* Shipping Address */}
              <Card className="mb-4">
                <Card.Header>
                  <h5 className="mb-0">Shipping Address</h5>
                </Card.Header>
                <Card.Body>
                  {addresses.filter(addr => addr.address_type === 'shipping').map(address => (
                    <Form.Check
                      key={address.id}
                      type="radio"
                      name="shipping_address_id"
                      value={address.id}
                      checked={formData.shipping_address_id === address.id.toString()}
                      onChange={handleInputChange}
                      label={
                        <div>
                          <strong>{address.full_name}</strong>
                          <br />
                          {address.address_line1}
                          {address.address_line2 && <>, {address.address_line2}</>}
                          <br />
                          {address.city}, {address.state} - {address.postal_code}
                          <br />
                          {address.phone}
                          {address.is_default && <Badge bg="primary" className="ms-2">Default</Badge>}
                        </div>
                      }
                      className="mb-3"
                    />
                  ))}
                  <Button variant="outline-primary" size="sm" as={Link} to="/profile?tab=addresses">
                    <i className="fas fa-plus me-1"></i>Add New Address
                  </Button>
                </Card.Body>
              </Card>

              {/* Billing Address */}
              <Card className="mb-4">
                <Card.Header>
                  <h5 className="mb-0">Billing Address</h5>
                </Card.Header>
                <Card.Body>
                  <Form.Check
                    type="radio"
                    name="billing_address_id"
                    value=""
                    checked={!formData.billing_address_id}
                    onChange={handleInputChange}
                    label="Same as shipping address"
                    className="mb-3"
                  />

                  {addresses.filter(addr => addr.address_type === 'billing').map(address => (
                    <Form.Check
                      key={address.id}
                      type="radio"
                      name="billing_address_id"
                      value={address.id}
                      checked={formData.billing_address_id === address.id.toString()}
                      onChange={handleInputChange}
                      label={
                        <div>
                          <strong>{address.full_name}</strong>
                          <br />
                          {address.address_line1}
                          {address.address_line2 && <>, {address.address_line2}</>}
                          <br />
                          {address.city}, {address.state} - {address.postal_code}
                          <br />
                          {address.phone}
                          {address.is_default && <Badge bg="primary" className="ms-2">Default</Badge>}
                        </div>
                      }
                      className="mb-3"
                    />
                  ))}
                </Card.Body>
              </Card>

              {/* Payment Method */}
              <Card className="mb-4">
                <Card.Header>
                  <h5 className="mb-0">Payment Method</h5>
                </Card.Header>
                <Card.Body>
                  <Form.Check
                    type="radio"
                    name="payment_method"
                    value="cash_on_delivery"
                    checked={formData.payment_method === 'cash_on_delivery'}
                    onChange={handleInputChange}
                    label="Cash on Delivery"
                    className="mb-3"
                  />
                  <Form.Check
                    type="radio"
                    name="payment_method"
                    value="upi"
                    checked={formData.payment_method === 'upi'}
                    onChange={handleInputChange}
                    label="UPI Payment"
                    className="mb-3"
                  />
                  <Form.Check
                    type="radio"
                    name="payment_method"
                    value="credit_card"
                    checked={formData.payment_method === 'credit_card'}
                    onChange={handleInputChange}
                    label="Credit/Debit Card"
                    className="mb-3"
                  />
                </Card.Body>
              </Card>

              {/* Additional Information */}
              <Card className="mb-4">
                <Card.Header>
                  <h5 className="mb-0">Additional Information</h5>
                </Card.Header>
                <Card.Body>
                  <Form.Group className="mb-3">
                    <Form.Label>Order Notes (Optional)</Form.Label>
                    <Form.Control
                      as="textarea"
                      rows={3}
                      name="customer_note"
                      value={formData.customer_note}
                      onChange={handleInputChange}
                      placeholder="Any special instructions for your order..."
                    />
                  </Form.Group>

                  <Form.Check
                    type="checkbox"
                    name="use_gst_invoice"
                    checked={formData.use_gst_invoice}
                    onChange={handleInputChange}
                    label="I need GST invoice"
                    className="mb-3"
                  />

                  {formData.use_gst_invoice && (
                    <Form.Group>
                      <Form.Label>GST Number</Form.Label>
                      <Form.Control
                        type="text"
                        name="gst_number"
                        value={formData.gst_number}
                        onChange={handleInputChange}
                        placeholder="Enter your GST number"
                        pattern="^[0-9A-Z]{15}$"
                      />
                      <Form.Text className="text-muted">
                        15-character GST number (e.g., 07AABCU9603R1ZM)
                      </Form.Text>
                    </Form.Group>
                  )}
                </Card.Body>
              </Card>
            </Col>

            <Col lg={4}>
              {/* Order Summary */}
              <Card className="sticky-top" style={{ top: '100px' }}>
                <Card.Header>
                  <h5 className="mb-0">Order Summary</h5>
                </Card.Header>
                <Card.Body>
                  <ListGroup variant="flush">
                    {cart.items.map(item => (
                      <ListGroup.Item key={item.id} className="px-0">
                        <div className="d-flex justify-content-between align-items-start">
                          <div>
                            <h6 className="mb-1">{item.product_name}</h6>
                            <small className="text-muted">Qty: {item.quantity}</small>
                            {item.variation_attributes && (
                              <div className="text-muted small">
                                {Object.values(item.variation_attributes).join(', ')}
                              </div>
                            )}
                          </div>
                          <div className="text-end">
                            <div>₹{item.total_price}</div>
                          </div>
                        </div>
                      </ListGroup.Item>
                    ))}
                  </ListGroup>

                  <div className="mt-3">
                    <div className="d-flex justify-content-between mb-2">
                      <span>Subtotal:</span>
                      <span>₹{cart.subtotal}</span>
                    </div>
                    <div className="d-flex justify-content-between mb-2">
                      <span>Shipping:</span>
                      <span className="text-success">FREE</span>
                    </div>
                    <div className="d-flex justify-content-between mb-2">
                      <span>Tax (GST):</span>
                      <span>₹{(cart.subtotal * 0.18).toFixed(2)}</span>
                    </div>
                    <hr />
                    <div className="d-flex justify-content-between mb-3">
                      <strong>Total:</strong>
                      <strong>₹{(cart.subtotal * 1.18).toFixed(2)}</strong>
                    </div>

                    <Button
                      variant="primary"
                      size="lg"
                      type="submit"
                      className="w-100"
                      disabled={processing}
                    >
                      {processing ? 'Processing...' : `Place Order - ₹${(cart.subtotal * 1.18).toFixed(2)}`}
                    </Button>
                  </div>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Form>
      </Container>
    </>
  )
}

export default Checkout