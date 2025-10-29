import React from 'react'
import { Navbar, Nav, Container, NavDropdown, Badge } from 'react-bootstrap'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useCart } from '../contexts/CartContext'

const NavigationBar = () => {
  const { user, logout, isAuthenticated } = useAuth()
  const { cart } = useCart()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <Navbar bg="dark" variant="dark" expand="lg" sticky="top">
      <Container>
        <Navbar.Brand as={Link} to="/">
          <i className="fas fa-store me-2"></i>
          Belo2 Store
        </Navbar.Brand>

        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="me-auto">
            <Nav.Link as={Link} to="/">Home</Nav.Link>
            <Nav.Link as={Link} to="/products">Products</Nav.Link>
            <Nav.Link as={Link} to="/about">About</Nav.Link>
            <Nav.Link as={Link} to="/contact">Contact</Nav.Link>
            {isAuthenticated && (
              <>
                <Nav.Link as={Link} to="/orders">Orders</Nav.Link>
                <Nav.Link as={Link} to="/wishlist">Wishlist</Nav.Link>
              </>
            )}
          </Nav>

          <Nav>
            <Nav.Link as={Link} to="/cart" className="position-relative">
              <i className="fas fa-shopping-cart"></i>
              {cart.total_items > 0 && (
                <Badge
                  bg="primary"
                  className="position-absolute top-0 start-100 translate-middle"
                  style={{ fontSize: '0.6rem' }}
                >
                  {cart.total_items}
                </Badge>
              )}
            </Nav.Link>

            {isAuthenticated ? (
              <NavDropdown title={user?.first_name || 'User'} id="user-dropdown">
                <NavDropdown.Item as={Link} to="/profile">
                  <i className="fas fa-user me-2"></i>Profile
                </NavDropdown.Item>
                <NavDropdown.Divider />
                <NavDropdown.Item onClick={handleLogout}>
                  <i className="fas fa-sign-out-alt me-2"></i>Logout
                </NavDropdown.Item>
              </NavDropdown>
            ) : (
              <>
                <Nav.Link as={Link} to="/login">Login</Nav.Link>
                <Nav.Link as={Link} to="/register">Register</Nav.Link>
              </>
            )}
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  )
}

export default NavigationBar