import React from 'react';

const PromoCards = () => {
  return (
    <section id="promo-cards" className="promo-cards section">
      <div className="container" data-aos="fade-up" data-aos-delay="100">
        <div className="row gy-4">
          <div className="col-lg-6">
            <div className="category-featured" data-aos="fade-right" data-aos-delay="200">
              <div className="category-image">
                <img src="assets/img/product/product-f-2.webp" alt="Women's Collection" className="img-fluid" />
              </div>
              <div className="category-content">
                <span className="category-tag">Trending Now</span>
                <h2>New Summer Collection</h2>
                <p>Discover our latest arrivals designed for the modern lifestyle. Elegant, comfortable, and sustainable fashion for every occasion.</p>
                <a href="#" className="btn-shop">Explore Collection <i className="bi bi-arrow-right"></i></a>
              </div>
            </div>
          </div>

          <div className="col-lg-6">
            <div className="row gy-4">
              <div className="col-xl-6">
                <div className="category-card cat-men" data-aos="fade-up" data-aos-delay="300">
                  <div className="category-image">
                    <img src="assets/img/product/product-m-5.webp" alt="Men's Fashion" className="img-fluid" />
                  </div>
                  <div className="category-content">
                    <h4>Men's Wear</h4>
                    <p>242 products</p>
                    <a href="#" className="card-link">Shop Now <i className="bi bi-arrow-right"></i></a>
                  </div>
                </div>
              </div>

              <div className="col-xl-6">
                <div className="category-card cat-kids" data-aos="fade-up" data-aos-delay="400">
                  <div className="category-image">
                    <img src="assets/img/product/product-8.webp" alt="Kid's Fashion" className="img-fluid" />
                  </div>
                  <div className="category-content">
                    <h4>Kid's Fashion</h4>
                    <p>185 products</p>
                    <a href="#" className="card-link">Shop Now <i className="bi bi-arrow-right"></i></a>
                  </div>
                </div>
              </div>

              <div className="col-xl-6">
                <div className="category-card cat-cosmetics" data-aos="fade-up" data-aos-delay="500">
                  <div className="category-image">
                    <img src="assets/img/product/product-3.webp" alt="Cosmetics" className="img-fluid" />
                  </div>
                  <div className="category-content">
                    <h4>Beauty Products</h4>
                    <p>127 products</p>
                    <a href="#" className="card-link">Shop Now <i className="bi bi-arrow-right"></i></a>
                  </div>
                </div>
              </div>

              <div className="col-xl-6">
                <div className="category-card cat-accessories" data-aos="fade-up" data-aos-delay="600">
                  <div className="category-image">
                    <img src="assets/img/product/product-12.webp" alt="Accessories" className="img-fluid" />
                  </div>
                  <div className="category-content">
                    <h4>Accessories</h4>
                    <p>308 products</p>
                    <a href="#" className="card-link">Shop Now <i className="bi bi-arrow-right"></i></a>
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

export default PromoCards;
