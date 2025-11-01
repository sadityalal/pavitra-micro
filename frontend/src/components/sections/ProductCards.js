import React from 'react';

const ProductCards = () => {
  return (
    <section id="cards" className="cards section">
      <div className="container" data-aos="fade-up" data-aos-delay="100">
        <div className="row gy-4">
          {/* Trending Now Column */}
          <div className="col-lg-4 col-md-6 mb-5 mb-md-0" data-aos="fade-up" data-aos-delay="200">
            <div className="product-category">
              <h3 className="category-title">
                <i className="bi bi-fire"></i> Trending Now
              </h3>
              <div className="product-list">
                <div className="product-card">
                  <div className="product-image">
                    <img src="assets/img/product/product-1.webp" alt="Premium Leather Tote" className="img-fluid" />
                    <div className="product-badges">
                      <span className="badge-new">New</span>
                    </div>
                  </div>
                  <div className="product-info">
                    <h4 className="product-name">Premium Leather Tote</h4>
                    <div className="product-rating">
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-half"></i>
                      <span>(24)</span>
                    </div>
                    <div className="product-price">
                      <span className="current-price">$87.50</span>
                    </div>
                  </div>
                </div>

                <div className="product-card">
                  <div className="product-image">
                    <img src="assets/img/product/product-3.webp" alt="Statement Earrings" className="img-fluid" />
                  </div>
                  <div className="product-info">
                    <h4 className="product-name">Statement Earrings</h4>
                    <div className="product-rating">
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <span>(41)</span>
                    </div>
                    <div className="product-price">
                      <span className="current-price">$39.99</span>
                    </div>
                  </div>
                </div>

                <div className="product-card">
                  <div className="product-image">
                    <img src="assets/img/product/product-5.webp" alt="Organic Cotton Shirt" className="img-fluid" />
                  </div>
                  <div className="product-info">
                    <h4 className="product-name">Organic Cotton Shirt</h4>
                    <div className="product-rating">
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star"></i>
                      <span>(18)</span>
                    </div>
                    <div className="product-price">
                      <span className="current-price">$45.00</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Best Sellers Column */}
          <div className="col-lg-4 col-md-6 mb-5 mb-md-0" data-aos="fade-up" data-aos-delay="300">
            <div className="product-category">
              <h3 className="category-title">
                <i className="bi bi-award"></i> Best Sellers
              </h3>
              <div className="product-list">
                <div className="product-card">
                  <div className="product-image">
                    <img src="assets/img/product/product-2.webp" alt="Slim Fit Denim" className="img-fluid" />
                    <div className="product-badges">
                      <span className="badge-sale">-15%</span>
                    </div>
                  </div>
                  <div className="product-info">
                    <h4 className="product-name">Slim Fit Denim</h4>
                    <div className="product-rating">
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <span>(87)</span>
                    </div>
                    <div className="product-price">
                      <span className="current-price">$68.00</span>
                      <span className="old-price">$80.00</span>
                    </div>
                  </div>
                </div>

                <div className="product-card">
                  <div className="product-image">
                    <img src="assets/img/product/product-6.webp" alt="Designer Handbag" className="img-fluid" />
                  </div>
                  <div className="product-info">
                    <h4 className="product-name">Designer Handbag</h4>
                    <div className="product-rating">
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-half"></i>
                      <span>(56)</span>
                    </div>
                    <div className="product-price">
                      <span className="current-price">$129.99</span>
                    </div>
                  </div>
                </div>

                <div className="product-card">
                  <div className="product-image">
                    <img src="assets/img/product/product-8.webp" alt="Leather Crossbody" className="img-fluid" />
                    <div className="product-badges">
                      <span className="badge-hot">Hot</span>
                    </div>
                  </div>
                  <div className="product-info">
                    <h4 className="product-name">Leather Crossbody</h4>
                    <div className="product-rating">
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <span>(112)</span>
                    </div>
                    <div className="product-price">
                      <span className="current-price">$95.50</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Featured Items Column */}
          <div className="col-lg-4 col-md-6 mb-5 mb-md-0" data-aos="fade-up" data-aos-delay="400">
            <div className="product-category">
              <h3 className="category-title">
                <i className="bi bi-star"></i> Featured Items
              </h3>
              <div className="product-list">
                <div className="product-card">
                  <div className="product-image">
                    <img src="assets/img/product/product-7.webp" alt="Pleated Midi Skirt" className="img-fluid" />
                  </div>
                  <div className="product-info">
                    <h4 className="product-name">Pleated Midi Skirt</h4>
                    <div className="product-rating">
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star"></i>
                      <span>(32)</span>
                    </div>
                    <div className="product-price">
                      <span className="current-price">$75.00</span>
                    </div>
                  </div>
                </div>

                <div className="product-card">
                  <div className="product-image">
                    <img src="assets/img/product/product-4.webp" alt="Geometric Earrings" className="img-fluid" />
                    <div className="product-badges">
                      <span className="badge-limited">Limited</span>
                    </div>
                  </div>
                  <div className="product-info">
                    <h4 className="product-name">Geometric Earrings</h4>
                    <div className="product-rating">
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-half"></i>
                      <span>(47)</span>
                    </div>
                    <div className="product-price">
                      <span className="current-price">$42.99</span>
                    </div>
                  </div>
                </div>

                <div className="product-card">
                  <div className="product-image">
                    <img src="assets/img/product/product-9.webp" alt="Structured Satchel" className="img-fluid" />
                  </div>
                  <div className="product-info">
                    <h4 className="product-name">Structured Satchel</h4>
                    <div className="product-rating">
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <span>(64)</span>
                    </div>
                    <div className="product-price">
                      <span className="current-price">$89.99</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default ProductCards;
