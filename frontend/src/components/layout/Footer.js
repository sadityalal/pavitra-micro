// frontend/src/components/layout/Footer.js
import React from 'react';
import { useSettings } from '../../contexts/SettingsContext';

const Footer = () => {
  const { frontendSettings } = useSettings();
  const currentYear = new Date().getFullYear();

  return (
    <footer id="footer" className="footer dark-background">
      <div className="footer-main">
        <div className="container">
          <div className="row gy-4">
            <div className="col-lg-4 col-md-6">
              <div className="footer-widget footer-about">
                <a href="/" className="logo text-decoration-none">
                  <span className="sitename">{frontendSettings.site_name || 'Pavitra Enterprises'}</span>
                </a>
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
            </div>
            
            <div className="col-lg-2 col-md-6 col-sm-6">
              <div className="footer-widget">
                <h4>Shop</h4>
                <ul className="footer-links">
                  <li><a href="/products?new=true">New Arrivals</a></li>
                  <li><a href="/products?featured=true">Bestsellers</a></li>
                  <li><a href="/products">All Products</a></li>
                  <li><a href="/products?sale=true">Sale</a></li>
                  <li><a href="/products?featured=true">Featured</a></li>
                </ul>
              </div>
            </div>
            
            <div className="col-lg-2 col-md-6 col-sm-6">
              <div className="footer-widget">
                <h4>Support</h4>
                <ul className="footer-links">
                  <li><a href="/contact">Help Center</a></li>
                  <li><a href="/orders">Order Status</a></li>
                  <li><a href="/shipping">Shipping Info</a></li>
                  <li><a href="/returns">Returns &amp; Exchanges</a></li>
                  <li><a href="/faq">FAQs</a></li>
                  <li><a href="/contact">Contact Us</a></li>
                </ul>
              </div>
            </div>
            
            <div className="col-lg-4 col-md-6">
              <div className="footer-widget">
                <h4>Contact Information</h4>
                <div className="footer-contact">
                  <div className="contact-item">
                    <i className="bi bi-telephone"></i>
                    <span>{frontendSettings.site_phone || '+91-9711317009'}</span>
                  </div>
                  <div className="contact-item">
                    <i className="bi bi-envelope"></i>
                    <span>{frontendSettings.site_email || 'support@pavitraenterprises.com'}</span>
                  </div>
                  <div className="contact-item">
                    <i className="bi bi-clock"></i>
                    <span>
                      {frontendSettings.business_hours?.monday_friday || 'Monday-Friday: 9am-6pm'}<br />
                      {frontendSettings.business_hours?.saturday || 'Saturday: 10am-4pm'}<br />
                      {frontendSettings.business_hours?.sunday || 'Sunday: Closed'}
                    </span>
                  </div>
                  {frontendSettings.free_shipping_threshold && (
                    <div className="contact-item">
                      <i className="bi bi-truck"></i>
                      <span>Free shipping on orders over {frontendSettings.currency_symbol || '₹'}{frontendSettings.free_shipping_threshold}</span>
                    </div>
                  )}
                  <div className="contact-item">
                    <i className="bi bi-building"></i>
                    <span>GST: 07AABCU9603R1ZM</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div className="footer-bottom">
        <div className="container">
          <div className="row gy-3 align-items-center">
            <div className="col-lg-6 col-md-12">
              <div className="copyright">
                <p>© <span>Copyright</span> <strong className="sitename">{frontendSettings.site_name || 'Pavitra Enterprises'}</strong>. All Rights Reserved.</p>
              </div>
            </div>
            <div className="col-lg-6 col-md-12">
              <div className="d-flex flex-wrap justify-content-lg-end justify-content-center align-items-center gap-4">
                <div className="payment-methods">
                  <div className="payment-icons">
                    <i className="bi bi-credit-card" aria-label="Credit Card"></i>
                    <i className="bi bi-cash" aria-label="Cash on Delivery"></i>
                    <i className="bi bi-bank" aria-label="Net Banking"></i>
                  </div>
                </div>
                <div className="legal-links">
                  <a href="/terms">Terms</a>
                  <a href="/privacy">Privacy</a>
                  <a href="/returns">Returns</a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <a href="#" id="scroll-top" className="scroll-top d-flex align-items-center justify-content-center">
        <i className="bi bi-arrow-up-short"></i>
      </a>
    </footer>
  );
};

export default Footer;