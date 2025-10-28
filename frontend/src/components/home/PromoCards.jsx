import React from 'react';
import { Link } from 'react-router-dom';

const PromoCards = ({ categories = [] }) => {
  return (
    <section id="promo-cards" className="promo-cards section">
      <div className="container" data-aos="fade-up" data-aos-delay="100">
        <div className="row gy-4">
          <div className="col-lg-6">
            {categories[0] && (
              <div className="category-featured" data-aos="fade-right" data-aos-delay="200">
                <div className="category-image">
                  <img src={categories[0].image_url || '/static/img/categories/placeholder.jpg'} alt={categories[0].name} className="img-fluid" onError={(e)=>e.currentTarget.src='/static/img/categories/placeholder.jpg'} />
                </div>
                <div className="category-content">
                  <span className="category-tag">Trending Now</span>
                  <h2>{categories[0].name} Collection</h2>
                  <p>{categories[0].description || 'Discover our latest arrivals.'}</p>
                  <Link to={`/categories/${categories[0].slug || categories[0].id}`} className="btn-shop">Explore Collection <i className="bi bi-arrow-right"></i></Link>
                </div>
              </div>
            )}
          </div>

          <div className="col-lg-6">
            <div className="row gy-4">
              {categories.slice(1,5).map((category, index) => (
                <div className="col-xl-6" key={category.id || index}>
                  <div className={`category-card cat-${category.slug || index}`} data-aos="fade-up" data-aos-delay={300 + index * 100} style={{cursor: 'pointer'}}>
                    <div className="category-image">
                      <img src={category.image_url || '/static/img/categories/placeholder.jpg'} alt={category.name} className="img-fluid" onError={(e)=>e.currentTarget.src='/static/img/categories/placeholder.jpg'} />
                    </div>
                    <div className="category-content">
                      <h4>{category.name}</h4>
                      <p>{category.product_count || 0} products</p>
                      <Link to={`/categories/${category.slug || category.id}`} className="card-link">Shop Now <i className="bi bi-arrow-right"></i></Link>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default PromoCards;
