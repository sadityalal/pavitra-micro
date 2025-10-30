import React from 'react'
import { Container, Row, Col } from 'react-bootstrap'
import { Link } from 'react-router-dom'

const Footer = () => {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="bg-dark text-light py-5 mt-5">
      <Container>
        <Row>
          <Col lg={4} md={6} className="mb-4">
            <h5 className="mb-3">
              <i className="fas fa-store me-2"></i>
              Belo2 Store
            </h5>
            <p className="text-muted">
              Your trusted e-commerce partner for quality products, fast delivery,
              and exceptional customer service. Shop with confidence.
            </p>
            <div className="social-links">
              <a href="#" className="text-light me-3">
                <i className="fab fa-facebook-f"></i>
              </a>
              <a href="#" className="text-light me-3">
                <i className="fab fa-twitter"></i>
              </a>
              <a href="#" className="text-light me-3">
                <i className="fab fa-instagram"></i>
              </a>
              <a href="#" className="text-light">
                <i className="fab fa-linkedin-in"></i>
              </a>
            </div>
          </Col>

          <Col lg={2} md={6} className="mb-4">
            <h6 className="mb-3">Quick Links</h6>
            <ul className="list-unstyled">
              <li className="mb-2">
                <Link to="/" className="text-muted text-decoration-none">Home</Link>
              </li>
              <li className="mb-2">
                <Link to="/products" className="text-muted text-decoration-none">Products</Link>
              </li>
              <li className="mb-2">
                <Link to="/about" className="text-muted text-decoration-none">About Us</Link>
              </li>
              <li className="mb-2">
                <Link to="/contact" className="text-muted text-decoration-none">Contact</Link>
              </li>
            </ul>
          </Col>

          <Col lg={3} md={6} className="mb-4">
            <h6 className="mb-3">Customer Service</h6>
            <ul className="list-unstyled">
              <li className="mb-2">
                <Link to="/faq" className="text-muted text-decoration-none">FAQ</Link>
              </li>
              <li className="mb-2">
                <Link to="/shipping" className="text-muted text-decoration-none">Shipping Info</Link>
              </li>
              <li className="mb-2">
                <Link to="/returns" className="text-muted text-decoration-none">Returns & Refunds</Link>
              </li>
              <li className="mb-2">
                <Link to="/privacy" className="text-muted text-decoration-none">Privacy Policy</Link>
              </li>
              <li className="mb-2">
                <Link to="/terms" className="text-muted text-decoration-none">Terms of Service</Link>
              </li>
            </ul>
          </Col>

          <Col lg={3} md={6} className="mb-4">
            <h6 className="mb-3">Contact Info</h6>
            <ul className="list-unstyled text-muted">
              <li className="mb-2">
                <i className="fas fa-map-marker-alt me-2"></i>
                123 Business Street, Mumbai, MH 400001
              </li>
              <li className="mb-2">
                <i className="fas fa-phone me-2"></i>
                +91-9711317009
              </li>
              <li className="mb-2">
                <i className="fas fa-envelope me-2"></i>
                support@pavitraenterprises.com
              </li>
              <li className="mb-2">
                <i className="fas fa-clock me-2"></i>
                Mon-Fri: 9AM-6PM
              </li>
            </ul>
          </Col>
        </Row>

        <hr className="my-4" />

        <Row className="align-items-center">
          <Col md={6}>
            <p className="text-muted mb-0">
              &copy; {currentYear} Belo2 Store. All rights reserved.
            </p>
          </Col>
          <Col md={6} className="text-md-end">
            <div className="payment-methods">
              <span className="text-muted me-2">We accept:</span>
              <i className="fab fa-cc-visa text-muted me-2"></i>
              <i className="fab fa-cc-mastercard text-muted me-2"></i>
              <i className="fab fa-cc-paypal text-muted me-2"></i>
              <i className="fas fa-university text-muted"></i>
            </div>
          </Col>
        </Row>
      </Container>
    </footer>
  )
}

export default Footer