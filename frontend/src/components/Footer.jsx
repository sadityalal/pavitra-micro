import React from 'react'
import { Link } from 'react-router-dom'
import { useSiteSettings } from '../contexts/SiteSettingsContext'

const Footer = () => {
  const { settings } = useSiteSettings()

  return (
    <footer className="footer bg-dark text-light mt-auto">
      <div className="footer-main py-5">
        <div className="container">
          <div className="row gy-4">
            <div className="col-lg-4 col-md-6">
              <div className="footer-widget footer-about">
                <Link to="/" className="logo text-decoration-none">
                  <span className="sitename h4 text-white">{settings.site_name || 'Pavitra Trading'}</span>
                </Link>
                <p className="mt-3">
                  Your trusted destination for quality products at great prices. We offer a wide range of 
                  electronics, clothing, home goods and more with excellent customer service.
                </p>

                <div className="social-links mt-4">
                  <h5>Connect With Us</h5>
                  <div className="social-icons d-flex gap-3 mt-2">
                    <a href="#" className="text-light" aria-label="Facebook"><i className="bi bi-facebook fs-5"></i></a>
                    <a href="#" className="text-light" aria-label="Instagram"><i className="bi bi-instagram fs-5"></i></a>
                    <a href="#" className="text-light" aria-label="Twitter"><i className="bi bi-twitter-x fs-5"></i></a>
                    <a href="#" className="text-light" aria-label="YouTube"><i className="bi bi-youtube fs-5"></i></a>
                  </div>
                </div>
              </div>
            </div>

            <div className="col-lg-2 col-md-6 col-sm-6">
              <div className="footer-widget">
                <h4>Shop</h4>
                <ul className="footer-links list-unstyled">
                  <li><Link to="/products?new=true" className="text-light text-decoration-none">New Arrivals</Link></li>
                  <li><Link to="/products?featured=true" className="text-light text-decoration-none">Bestsellers</Link></li>
                  <li><Link to="/products" className="text-light text-decoration-none">All Products</Link></li>
                  <li><Link to="/products?sale=true" className="text-light text-decoration-none">Sale</Link></li>
                  <li><Link to="/products?featured=true" className="text-light text-decoration-none">Featured</Link></li>
                </ul>
              </div>
            </div>

            <div className="col-lg-2 col-md-6 col-sm-6">
              <div className="footer-widget">
                <h4>Support</h4>
                <ul className="footer-links list-unstyled">
                  <li><Link to="/contact" className="text-light text-decoration-none">Help Center</Link></li>
                  <li><Link to="/account/orders" className="text-light text-decoration-none">Order Status</Link></li>
                  <li><Link to="/shipping" className="text-light text-decoration-none">Shipping Info</Link></li>
                  <li><Link to="/returns" className="text-light text-decoration-none">Returns &amp; Exchanges</Link></li>
                  <li><Link to="/faq" className="text-light text-decoration-none">FAQs</Link></li>
                  <li><Link to="/contact" className="text-light text-decoration-none">Contact Us</Link></li>
                </ul>
              </div>
            </div>

            <div className="col-lg-4 col-md-6">
              <div className="footer-widget">
                <h4>Contact Information</h4>
                <div className="footer-contact">
                  <div className="contact-item d-flex align-items-center mb-2">
                    <i className="bi bi-telephone me-3"></i>
                    <span>+91-9711317009</span>
                  </div>
                  <div className="contact-item d-flex align-items-center mb-2">
                    <i className="bi bi-envelope me-3"></i>
                    <span>support@pavitraenterprises.com</span>
                  </div>
                  <div className="contact-item d-flex align-items-center mb-2">
                    <i className="bi bi-clock me-3"></i>
                    <span>
                      Monday-Friday: 9am-6pm<br />
                      Saturday: 10am-4pm<br />
                      Sunday: Closed
                    </span>
                  </div>
                  {settings.gst_number && (
                    <div className="contact-item d-flex align-items-center mb-2">
                      <i className="bi bi-building me-3"></i>
                      <span>GST: {settings.gst_number}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="footer-bottom py-4 border-top border-secondary">
        <div className="container">
          <div className="row gy-3 align-items-center">
            <div className="col-lg-6 col-md-12">
              <div className="copyright">
                <p className="mb-0">
                  © <span>Copyright</span> <strong className="sitename">{settings.site_name || 'Pavitra Trading'}</strong>. All Rights Reserved.
                </p>
              </div>
            </div>

            <div className="col-lg-6 col-md-12">
              <div className="d-flex flex-wrap justify-content-lg-end justify-content-center align-items-center gap-4">
                <div className="payment-methods">
                  <div className="payment-icons d-flex gap-2">
                    <i className="bi bi-credit-card fs-5" aria-label="Credit Card"></i>
                    <i className="bi bi-cash fs-5" aria-label="Cash on Delivery"></i>
                    <i className="bi bi-bank fs-5" aria-label="Net Banking"></i>
                  </div>
                </div>

                <div className="legal-links d-flex gap-3">
                  <Link to="/terms" className="text-light text-decoration-none">Terms</Link>
                  <Link to="/privacy" className="text-light text-decoration-none">Privacy</Link>
                  <Link to="/returns" className="text-light text-decoration-none">Returns</Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}

export default Footer
