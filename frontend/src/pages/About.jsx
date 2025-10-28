import React from 'react';

const About = () => {
  return (
    <div className="container py-5">
      <div className="row">
        <div className="col-12">
          <div className="page-header mb-4">
            <h1>About Pavitra Enterprises</h1>
            <p className="lead">Your trusted partner for quality products and exceptional service</p>
          </div>
        </div>
      </div>

      <div className="row">
        <div className="col-lg-6">
          <div className="card mb-4">
            <div className="card-body">
              <h3 className="card-title">Our Story</h3>
              <p className="card-text">
                Founded with a vision to revolutionize the shopping experience, Pavitra Enterprises
                has been serving customers with dedication and excellence. We believe in providing
                high-quality products that meet the diverse needs of our valued customers.
              </p>
              <p className="card-text">
                From humble beginnings to becoming a trusted name in the industry, our journey
                has been guided by our core values of integrity, quality, and customer satisfaction.
              </p>
            </div>
          </div>
        </div>

        <div className="col-lg-6">
          <div className="card mb-4">
            <div className="card-body">
              <h3 className="card-title">Our Mission</h3>
              <p className="card-text">
                To provide exceptional value through carefully curated products, competitive pricing,
                and outstanding customer service. We strive to make shopping a seamless and enjoyable
                experience for everyone.
              </p>
              <ul className="list-unstyled">
                <li><i className="bi bi-check-circle text-primary me-2"></i>Quality Products</li>
                <li><i className="bi bi-check-circle text-primary me-2"></i>Competitive Prices</li>
                <li><i className="bi bi-check-circle text-primary me-2"></i>Fast Delivery</li>
                <li><i className="bi bi-check-circle text-primary me-2"></i>Excellent Support</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <div className="row mt-4">
        <div className="col-12">
          <div className="card">
            <div className="card-body">
              <h3 className="card-title">Why Choose Us?</h3>
              <div className="row">
                <div className="col-md-4 text-center mb-3">
                  <div className="feature-icon mb-3">
                    <i className="bi bi-award display-4 text-primary"></i>
                  </div>
                  <h5>Quality Assurance</h5>
                  <p className="text-muted">Every product is carefully selected and quality-checked</p>
                </div>
                <div className="col-md-4 text-center mb-3">
                  <div className="feature-icon mb-3">
                    <i className="bi bi-truck display-4 text-primary"></i>
                  </div>
                  <h5>Fast Shipping</h5>
                  <p className="text-muted">Quick and reliable delivery across the region</p>
                </div>
                <div className="col-md-4 text-center mb-3">
                  <div className="feature-icon mb-3">
                    <i className="bi bi-headset display-4 text-primary"></i>
                  </div>
                  <h5>24/7 Support</h5>
                  <p className="text-muted">Round-the-clock customer service and support</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default About;