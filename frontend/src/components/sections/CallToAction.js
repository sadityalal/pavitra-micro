import React from 'react';

const CallToAction = () => {
  return (
    <section id="call-to-action" className="call-to-action section">
      <div className="container" data-aos="fade-up" data-aos-delay="100">
        <div className="row">
          <div className="col-lg-8 mx-auto">
            <div className="main-content text-center" data-aos="zoom-in" data-aos-delay="200">
              <div className="offer-badge" data-aos="fade-down" data-aos-delay="250">
                <span className="limited-time">Limited Time</span>
                <span className="offer-text">50% OFF</span>
              </div>

              <h2 data-aos="fade-up" data-aos-delay="300">Exclusive Flash Sale</h2>

              <p className="subtitle" data-aos="fade-up" data-aos-delay="350">
                Don't miss out on our biggest sale of the year. Premium quality products at unbeatable prices for the next 48 hours only.
              </p>

              <div className="countdown-wrapper" data-aos="fade-up" data-aos-delay="400">
                <div className="countdown d-flex justify-content-center" data-count="2025/12/31">
                  <div>
                    <h3 className="count-days">00</h3>
                    <h4>Days</h4>
                  </div>
                  <div>
                    <h3 className="count-hours">00</h3>
                    <h4>Hours</h4>
                  </div>
                  <div>
                    <h3 className="count-minutes">00</h3>
                    <h4>Minutes</h4>
                  </div>
                  <div>
                    <h3 className="count-seconds">00</h3>
                    <h4>Seconds</h4>
                  </div>
                </div>
              </div>

              <div className="action-buttons" data-aos="fade-up" data-aos-delay="450">
                <a href="#" className="btn-shop-now">Shop Now</a>
                <a href="#" className="btn-view-deals">View All Deals</a>
              </div>
            </div>
          </div>
        </div>

        <div className="row featured-products-row" data-aos="fade-up" data-aos-delay="500">
          <div className="col-lg-3 col-md-6" data-aos="zoom-in" data-aos-delay="100">
            <div className="product-showcase">
              <div className="product-image">
                <img src="assets/img/product/product-5.webp" alt="Featured Product" className="img-fluid" />
                <div className="discount-badge">-45%</div>
              </div>
              <div className="product-details">
                <h6>Premium Wireless Headphones</h6>
                <div className="price-section">
                  <span className="original-price">$129</span>
                  <span className="sale-price">$71</span>
                </div>
                <div className="rating-stars">
                  <i className="bi bi-star-fill"></i>
                  <i className="bi bi-star-fill"></i>
                  <i className="bi bi-star-fill"></i>
                  <i className="bi bi-star-fill"></i>
                  <i className="bi bi-star-fill"></i>
                  <span className="rating-count">(324)</span>
                </div>
              </div>
            </div>
          </div>

          <div className="col-lg-3 col-md-6" data-aos="zoom-in" data-aos-delay="150">
            <div className="product-showcase">
              <div className="product-image">
                <img src="assets/img/product/product-7.webp" alt="Featured Product" className="img-fluid" />
                <div className="discount-badge">-60%</div>
              </div>
              <div className="product-details">
                <h6>Smart Fitness Tracker</h6>
                <div className="price-section">
                  <span className="original-price">$89</span>
                  <span className="sale-price">$36</span>
                </div>
                <div className="rating-stars">
                  <i className="bi bi-star-fill"></i>
                  <i className="bi bi-star-fill"></i>
                  <i className="bi bi-star-fill"></i>
                  <i className="bi bi-star-fill"></i>
                  <i className="bi bi-star-half"></i>
                  <span className="rating-count">(198)</span>
                </div>
              </div>
            </div>
          </div>

          <div className="col-lg-3 col-md-6" data-aos="zoom-in" data-aos-delay="200">
            <div className="product-showcase">
              <div className="product-image">
                <img src="assets/img/product/product-11.webp" alt="Featured Product" className="img-fluid" />
                <div className="discount-badge">-35%</div>
              </div>
              <div className="product-details">
                <h6>Luxury Travel Backpack</h6>
                <div className="price-section">
                  <span className="original-price">$159</span>
                  <span className="sale-price">$103</span>
                </div>
                <div className="rating-stars">
                  <i className="bi bi-star-fill"></i>
                  <i className="bi bi-star-fill"></i>
                  <i className="bi bi-star-fill"></i>
                  <i className="bi bi-star-fill"></i>
                  <i className="bi bi-star-fill"></i>
                  <span className="rating-count">(267)</span>
                </div>
              </div>
            </div>
          </div>

          <div className="col-lg-3 col-md-6" data-aos="zoom-in" data-aos-delay="250">
            <div className="product-showcase">
              <div className="product-image">
                <img src="assets/img/product/product-1.webp" alt="Featured Product" className="img-fluid" />
                <div className="discount-badge">-55%</div>
              </div>
              <div className="product-details">
                <h6>Artisan Coffee Mug Set</h6>
                <div className="price-section">
                  <span className="original-price">$75</span>
                  <span className="sale-price">$34</span>
                </div>
                <div className="rating-stars">
                  <i className="bi bi-star-fill"></i>
                  <i className="bi bi-star-fill"></i>
                  <i className="bi bi-star-fill"></i>
                  <i className="bi bi-star-fill"></i>
                  <i className="bi bi-star"></i>
                  <span className="rating-count">(142)</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default CallToAction;
