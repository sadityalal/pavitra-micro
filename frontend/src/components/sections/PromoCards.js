// frontend/src/components/sections/PromoCards.js
import React from 'react';
import { useCategories } from '../../hooks/useCategories';

const PromoCards = () => {
  const { categories, loading } = useCategories();

  if (loading) {
    return (
      <section id="promo-cards" className="promo-cards section">
        <div className="container">
          <div className="text-center py-5">
            <div className="spinner-border" role="status">
              <span className="visually-hidden">Loading...</span>
            </div>
          </div>
        </div>
      </section>
    );
  }

  const featuredCategory = categories[0];
  const otherCategories = categories.slice(1, 5);

  return (
    <section id="promo-cards" className="promo-cards section">
      <div className="container" data-aos="fade-up" data-aos-delay="100">
        <div className="row gy-4">
          <div className="col-lg-6">
            {featuredCategory ? (
              <div className="category-featured" data-aos="fade-right" data-aos-delay="200">
                <div className="category-image">
                  <img 
                    src={featuredCategory.image_url || '/assets/img/categories/placeholder.jpg'} 
                    alt={featuredCategory.name} 
                    className="img-fluid" 
                  />
                </div>
                <div className="category-content">
                  <span className="category-tag">Trending Now</span>
                  <h2>{featuredCategory.name} Collection</h2>
                  <p>{featuredCategory.description || 'Discover our latest arrivals designed for the modern lifestyle.'}</p>
                  <a href={`/category/${featuredCategory.slug}`} className="btn-shop">
                    Explore Collection <i className="bi bi-arrow-right"></i>
                  </a>
                </div>
              </div>
            ) : (
              <div className="category-featured" data-aos="fade-right" data-aos-delay="200">
                <div className="category-image">
                  <img src="/assets/img/categories/placeholder.jpg" alt="Categories" className="img-fluid" />
                </div>
                <div className="category-content">
                  <span className="category-tag">Coming Soon</span>
                  <h2>New Collections</h2>
                  <p>Exciting new categories coming soon.</p>
                  <a href="/products" className="btn-shop">
                    Browse Products <i className="bi bi-arrow-right"></i>
                  </a>
                </div>
              </div>
            )}
          </div>

          <div className="col-lg-6">
            <div className="row gy-4">
              {otherCategories.length > 0 ? (
                otherCategories.map((category, index) => (
                  <div key={category.id} className="col-xl-6">
                    <div 
                      className="category-card" 
                      data-aos="fade-up" 
                      data-aos-delay={300 + index * 100}
                    >
                      <div className="category-image">
                        <img 
                          src={category.image_url || '/assets/img/categories/placeholder.jpg'} 
                          alt={category.name} 
                          className="img-fluid" 
                        />
                      </div>
                      <div className="category-content">
                        <h4>{category.name}</h4>
                        <p>{category.product_count || 0} products</p>
                        <a href={`/category/${category.slug}`} className="card-link">
                          Shop Now <i className="bi bi-arrow-right"></i>
                        </a>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                // Fallback when no categories
                Array.from({ length: 4 }).map((_, index) => (
                  <div key={index} className="col-xl-6">
                    <div className="category-card" data-aos="fade-up" data-aos-delay={300 + index * 100}>
                      <div className="category-image">
                        <img src="/assets/img/categories/placeholder.jpg" alt="Category" className="img-fluid" />
                      </div>
                      <div className="category-content">
                        <h4>Coming Soon</h4>
                        <p>0 products</p>
                        <a href="/products" className="card-link">
                          Browse Products <i className="bi bi-arrow-right"></i>
                        </a>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default PromoCards;