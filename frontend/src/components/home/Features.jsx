import React from 'react';

const Features = ({ siteSettings = {} }) => {
  const formatPrice = (price) => `${siteSettings.currency_symbol || '₹'}${parseFloat(price || 0).toFixed(2)}`;

  return (
    <section id="features" className="cards section">
      <div className="container" data-aos="fade-up" data-aos-delay="100">
        <div className="row g-4">
          <div className="col-lg-3 col-md-6 text-center">
            <div className="feature-icon mb-3">
              <i className="bi bi-truck display-6 text-primary"></i>
            </div>
            <h4>Free Shipping</h4>
            <p className="text-muted">Free shipping on orders over {formatPrice(siteSettings.free_shipping_threshold || 999)}</p>
          </div>
          <div className="col-lg-3 col-md-6 text-center">
            <div className="feature-icon mb-3">
              <i className="bi bi-arrow-clockwise display-6 text-primary"></i>
            </div>
            <h4>Easy Returns</h4>
            <p className="text-muted">{siteSettings.return_period_days || 10}-day return policy</p>
          </div>
          <div className="col-lg-3 col-md-6 text-center">
            <div className="feature-icon mb-3">
              <i className="bi bi-shield-check display-6 text-primary"></i>
            </div>
            <h4>Secure Payment</h4>
            <p className="text-muted">Your payment information is safe with us</p>
          </div>
          <div className="col-lg-3 col-md-6 text-center">
            <div className="feature-icon mb-3">
              <i className="bi bi-headset display-6 text-primary"></i>
            </div>
            <h4>24/7 Support</h4>
            <p className="text-muted">Round-the-clock customer support</p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Features;
