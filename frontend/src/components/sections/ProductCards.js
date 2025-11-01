// frontend/src/components/sections/ProductCards.js
import React from 'react';
import { useProducts } from '../../hooks/useProducts';

const ProductCards = () => {
  const { products: featuredProducts, loading } = useProducts('featured');

  if (loading) {
    return (
      <section id="cards" className="cards section">
        <div className="container text-center py-5">
          <div className="spinner-border" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      </section>
    );
  }

  const featuredItems = featuredProducts.slice(0, 3);
  const trendingItems = featuredProducts.slice(3, 6);
  const bestSellerItems = featuredProducts.slice(6, 9);

  return (
    <section id="cards" className="cards section">
      <div className="container" data-aos="fade-up" data-aos-delay="100">
        <div className="row gy-4">
          {/* Featured Items */}
          <div className="col-lg-4 col-md-6 mb-5 mb-md-0" data-aos="fade-up" data-aos-delay="200">
            <div className="product-category">
              <h3 className="category-title">
                <i className="bi bi-star"></i> Featured Items
              </h3>
              <div className="product-list">
                {featuredItems.map((product) => (
                  <div key={product.id} className="product-card">
                    <div className="product-image">
                      <img 
                        src={product.main_image_url || '/assets/img/product/placeholder.jpg'} 
                        alt={product.name} 
                        className="img-fluid" 
                      />
                    </div>
                    <div className="product-info">
                      <h4 className="product-name">
                        <a href={`/product/${product.slug}`}>{product.name}</a>
                      </h4>
                      <div className="product-price">
                        <span className="current-price">₹{product.base_price}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Trending Now */}
          <div className="col-lg-4 col-md-6 mb-5 mb-md-0" data-aos="fade-up" data-aos-delay="300">
            <div className="product-category">
              <h3 className="category-title">
                <i className="bi bi-fire"></i> Trending Now
              </h3>
              <div className="product-list">
                {trendingItems.map((product) => (
                  <div key={product.id} className="product-card">
                    <div className="product-image">
                      <img 
                        src={product.main_image_url || '/assets/img/product/placeholder.jpg'} 
                        alt={product.name} 
                        className="img-fluid" 
                      />
                    </div>
                    <div className="product-info">
                      <h4 className="product-name">
                        <a href={`/product/${product.slug}`}>{product.name}</a>
                      </h4>
                      <div className="product-price">
                        <span className="current-price">₹{product.base_price}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Best Sellers */}
          <div className="col-lg-4 col-md-6 mb-5 mb-md-0" data-aos="fade-up" data-aos-delay="400">
            <div className="product-category">
              <h3 className="category-title">
                <i className="bi bi-award"></i> Best Sellers
              </h3>
              <div className="product-list">
                {bestSellerItems.map((product) => (
                  <div key={product.id} className="product-card">
                    <div className="product-image">
                      <img 
                        src={product.main_image_url || '/assets/img/product/placeholder.jpg'} 
                        alt={product.name} 
                        className="img-fluid" 
                      />
                    </div>
                    <div className="product-info">
                      <h4 className="product-name">
                        <a href={`/product/${product.slug}`}>{product.name}</a>
                      </h4>
                      <div className="product-price">
                        <span className="current-price">₹{product.base_price}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default ProductCards;