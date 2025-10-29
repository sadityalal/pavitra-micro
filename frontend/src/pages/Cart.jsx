import React from 'react'
import { Container, Row, Col, Card, Table, Button, Form, Alert, Badge } from 'react-bootstrap'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useCart } from '../contexts/CartContext'
import PageHeader from '../components/layout/PageHeader'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorMessage from '../components/common/ErrorMessage'
import EmptyState from '../components/common/EmptyState'

const Cart = () => {
  const { isAuthenticated } = useAuth()
  const { cart, loading, error, updateCartItem, removeFromCart, clearCart, loadCart, isGuest } = useCart()
  const navigate = useNavigate()

  const handleQuantityChange = async (itemId, newQuantity) => {
    if (newQuantity < 1) {
      await removeFromCart(itemId)
    } else {
      await updateCartItem(itemId, newQuantity)
    }
  }

  const handleRemoveItem = async (itemId) => {
    await removeFromCart(itemId)
  }

  const handleClearCart = async () => {
    if (window.confirm('Are you sure you want to clear your cart?')) {
      await clearCart()
    }
  }

  const handleCheckout = () => {
    if (!isAuthenticated) {
      navigate('/login', { state: { from: '/checkout' } })
      return
    }
    navigate('/checkout')
  }

  if (loading) {
    return (
      <>
        <PageHeader title="Shopping Cart" />
        <LoadingSpinner text="Loading your cart..." />
      </>
    )
  }

  if (cart.items.length === 0) {
    return (
      <>
        <PageHeader title="Shopping Cart" />
        <Container>
          <EmptyState
            icon="fas fa-shopping-cart"
            title="Your cart is empty"
            message={isGuest ? "Add some products to your cart. Sign in to save your cart." : "Add some products to your cart to see them here."}
            actionText="Browse Products"
            onAction={() => navigate('/products')}
          />
          {isGuest && (
            <div className="text-center mt-3">
              <p className="text-muted">
                <Link to="/login" className="text-decoration-none">
                  Sign in
                </Link> to access your saved cart and checkout.
              </p>
            </div>
          )}
        </Container>
      </>
    )
  }

  return (
    <>
      <PageHeader title="Shopping Cart" />
      <Container>
        <Row>
          <Col lg={8}>
            <Card>
              <Card.Header className="d-flex justify-content-between align-items-center">
                <div>
                  <h5 className="mb-0">
                    Cart Items ({cart.total_items})
                    {isGuest && <Badge bg="warning" className="ms-2">Guest</Badge>}
                  </h5>
                  {isGuest && (
                    <small className="text-muted">
                      <Link to="/login" className="text-decoration-none">
                        Sign in
                      </Link> to save your cart
                    </small>
                  )}
                </div>
                <Button variant="outline-danger" size="sm" onClick={handleClearCart}>
                  Clear Cart
                </Button>
              </Card.Header>
              <Card.Body className="p-0">
                <Table responsive className="mb-0">
                  <thead className="bg-light">
                    <tr>
                      <th>Product</th>
                      <th>Price</th>
                      <th>Quantity</th>
                      <th>Total</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cart.items.map((item) => (
                      <CartItem
                        key={item.id}
                        item={item}
                        onQuantityChange={handleQuantityChange}
                        onRemove={handleRemoveItem}
                      />
                    ))}
                  </tbody>
                </Table>
              </Card.Body>
            </Card>
          </Col>

          <Col lg={4}>
            <Card className="sticky-top" style={{ top: '100px' }}>
              <Card.Header>
                <h5 className="mb-0">Order Summary</h5>
              </Card.Header>
              <Card.Body>
                <div className="d-flex justify-content-between mb-2">
                  <span>Subtotal:</span>
                  <span>₹{cart.subtotal}</span>
                </div>
                <div className="d-flex justify-content-between mb-2">
                  <span>Shipping:</span>
                  <span className="text-muted">Calculated at checkout</span>
                </div>
                <div className="d-flex justify-content-between mb-2">
                  <span>Tax:</span>
                  <span className="text-muted">Calculated at checkout</span>
                </div>
                <hr />
                <div className="d-flex justify-content-between mb-3">
                  <strong>Total:</strong>
                  <strong>₹{cart.subtotal}</strong>
                </div>

                <Button
                  variant="primary"
                  size="lg"
                  className="w-100 mb-2"
                  onClick={handleCheckout}
                >
                  {isAuthenticated ? 'Proceed to Checkout' : 'Sign in to Checkout'}
                </Button>

                <Button
                  variant="outline-primary"
                  className="w-100"
                  as={Link}
                  to="/products"
                >
                  Continue Shopping
                </Button>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </Container>
    </>
  )
}

const CartItem = ({ item, onQuantityChange, onRemove }) => {
  const [updating, setUpdating] = React.useState(false)

  const handleQuantityUpdate = async (newQuantity) => {
    setUpdating(true)
    await onQuantityChange(item.id, newQuantity)
    setUpdating(false)
  }

  return (
    <tr>
      <td>
        <div className="d-flex align-items-center">
          <img
            src={item.product_image || '/images/placeholder-product.jpg'}
            alt={item.product_name}
            style={{ width: '60px', height: '60px', objectFit: 'cover' }}
            className="rounded me-3"
          />
          <div>
            <Link
              to={`/products/${item.product_id}`}
              className="text-decoration-none fw-bold"
            >
              {item.product_name}
            </Link>
            {item.variation_attributes && (
              <div className="text-muted small">
                {Object.entries(item.variation_attributes).map(([key, value]) => (
                  <span key={key} className="me-2">
                    {key}: {value}
                  </span>
                ))}
              </div>
            )}
            <div className="small">
              <Badge bg={item.stock_status === 'in_stock' ? 'success' : 'danger'}>
                {item.stock_status === 'in_stock' ? 'In Stock' : 'Out of Stock'}
              </Badge>
            </div>
          </div>
        </div>
      </td>
      <td>₹{item.unit_price}</td>
      <td>
        <div className="d-flex align-items-center">
          <Button
            variant="outline-secondary"
            size="sm"
            onClick={() => handleQuantityUpdate(item.quantity - 1)}
            disabled={item.quantity <= 1 || updating}
          >
            -
          </Button>
          <Form.Control
            type="number"
            value={item.quantity}
            onChange={(e) => handleQuantityUpdate(parseInt(e.target.value))}
            style={{ width: '70px', margin: '0 8px' }}
            min="1"
            max={item.max_cart_quantity}
            disabled={updating}
          />
          <Button
            variant="outline-secondary"
            size="sm"
            onClick={() => handleQuantityUpdate(item.quantity + 1)}
            disabled={item.quantity >= item.max_cart_quantity || updating}
          >
            +
          </Button>
        </div>
      </td>
      <td className="fw-bold">₹{item.total_price}</td>
      <td>
        <Button
          variant="outline-danger"
          size="sm"
          onClick={() => onRemove(item.id)}
          disabled={updating}
        >
          <i className="fas fa-trash"></i>
        </Button>
      </td>
    </tr>
  )
}

export default Cart