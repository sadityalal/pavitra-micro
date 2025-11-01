import React from 'react'
import { Container, Row, Col } from 'react-bootstrap'
import { Link } from 'react-router-dom'
import { useSettings } from '../contexts/SettingsContext'

const Footer = () => {
  const { settings } = useSettings()
  const currentYear = new Date().getFullYear()

  return (
    <footer id="footer" className="footer dark-background">
      <div className="footer-main">
        <Container>
          <Row className="gy-4">
            <Col lg={4} md={6}>
              <div className="footer-widget footer-about">
                <Link to="/" className="logo text-decoration-none">
                  <span className="sitename">{settings.site_name || 'Pavitra Enterprises'}</span>
                </Link>
                <p>Your trusted destination for quality products at great prices. We offer a wide range of electronics, clothing, home goods and more with excellent customer service.</p>
                <div className="social-links mt-4">
                  <h5>Connect With Us</h5>
                  <div className="social-icons">
                    <a href="#" aria-label="Facebook"><i className="bi bi-facebook"></i></a>
                    <a href="#" aria-label="Instagram"><i className="bi bi-instagram"></i></a>
                    <a href="#" aria-label="Twitter"><i className="bi bi-twitter-x"></i></a>
                    <a href="#" aria-label="YouTube"><i className="bi bi-youtube"></i></a>
                  </div>
                </div>
              </div>
            </Col>
            <Col lg={2} md={6} sm={6}>
              <div className="footer-widget">
                <h4>Shop</h4>
                <ul className="footer-links">
                  <li><Link to="/products?new=true">New Arrivals</Link></li>
                  <li><Link to="/products?featured=true">Bestsellers</Link></li>
                  <li><Link to="/products">All Products</Link></li>
                  <li><Link to="/products?sale=true">Sale</Link></li>
                  <li><Link to="/products?featured=true">Featured</Link></li>
                </ul>
              </div>
            </Col>
            <Col lg={2} md={6} sm={6}>
              <div className="footer-widget">
                <h4>Support</h4>
                <ul className="footer-links">
                  <li><Link to="/contact">Help Center</Link></li>
                  <li><Link to="/orders">Order Status</Link></li>
                  <li><Link to="/shipping">Shipping Info</Link></li>
                  <li><Link to="/returns">Returns &amp; Exchanges</Link></li>
                  <li><Link to="/faq">FAQs</Link></li>
                  <li><Link to="/contact">Contact Us</Link></li>
                </ul>
              </div>
            </Col>
            <Col lg={4} md={6}>
              <div className="footer-widget">
                <h4>Contact Information</h4>
                <div className="footer-contact">
                  <div className="contact-item">
                    <i className="bi bi-telephone"></i>
                    <span>{settings.site_phone || '+91-9711317009'}</span>
                  </div>
                  <div className="contact-item">
                    <i className="bi bi-envelope"></i>
                    <span>{settings.site_email || 'support@pavitraenterprises.com'}</span>
                  </div>
                  <div className="contact-item">
                    <i className="bi bi-clock"></i>
                    <span>Monday-Friday: 9am-6pm<br />Saturday: 10am-4pm<br />Sunday: Closed</span>
                  </div>
                  {settings.free_shipping_threshold && (
                    <div className="contact-item">
                      <i className="bi bi-truck"></i>
                      <span>Free shipping on orders over {settings.currency_symbol || '₹'}{settings.free_shipping_threshold}</span>
                    </div>
                  )}
                  <div className="contact-item">
                    <i className="bi bi-building"></i>
                    <span>GST: 07AABCU9603R1ZM</span>
                  </div>
                </div>
              </div>
            </Col>
          </Row>
        </Container>
      </div>
      <div className="footer-bottom">
        <Container>
          <Row className="gy-3 align-items-center">
            <Col lg={6} md={12}>
              <div className="copyright">
                <p>© <span>Copyright</span> <strong className="sitename">{settings.site_name || 'Pavitra Enterprises'}</strong>. All Rights Reserved.</p>
              </div>
            </Col>
            <Col lg={6} md={12}>
              <div className="d-flex flex-wrap justify-content-lg-end justify-content-center align-items-center gap-4">
                <div className="payment-methods">
                  <div className="payment-icons">
                    <i className="bi bi-credit-card" aria-label="Credit Card"></i>
                    <i className="bi bi-cash" aria-label="Cash on Delivery"></i>
                    <i className="bi bi-bank" aria-label="Net Banking"></i>
                  </div>
                </div>
                <div className="legal-links">
                  <Link to="/terms">Terms</Link>
                  <Link to="/privacy">Privacy</Link>
                  <Link to="/returns">Returns</Link>
                </div>
              </div>
            </Col>
          </Row>
        </Container>
      </div>
      <a href="#" id="scroll-top" className="scroll-top d-flex align-items-center justify-content-center">
        <i className="bi bi-arrow-up-short"></i>
      </a>
    </footer>
  )
}

export default Footer