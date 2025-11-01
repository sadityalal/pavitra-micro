import React from 'react';
import { useProducts } from '../../hooks/useProducts';
import ProductCard from '../common/ProductCard';

const BestSellers = () => {
  const { products: bestSellers, loading, error } = useProducts('best-sellers');

  const handleAddToCart = async (product) => {
    try {
      console.log('Adding to cart:', product);
      // Implement cart functionality here
    } catch (error) {
      console.error('Failed to add to cart:', error);
    }
  };

  const handleAddToWishlist = async (product) => {
    try {
      console.log('Adding to wishlist:', product);
      // Implement wishlist functionality here
    } catch (error) {
      console.error('Failed to add to wishlist:', error);
    }
  };

  if (loading) {
    return (
      <section id="best-sellers" className="best-sellers section">
        <div className="container">
          <div className="section-title" data-aos="fade-up">
            <h2>Best Sellers</h2>
            <p>Discover our most popular products</p>
          </div>
          <div className="row g-4">
            {Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="col-lg-3 col-md-6 col-sm-6">
                <ProductCard loading={true} />
              </div>
            ))}
          </div>
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section id="best-sellers" className="best-sellers section">
        <div className="container">
          <div className="section-title" data-aos="fade-up">
            <h2>Best Sellers</h2>
          </div>
          <div className="alert alert-warning text-center">
            <i className="bi bi-exclamation-triangle me-2"></i>
            Unable to load best sellers. Please try again later.
          </div>
        </div>
      </section>
    );
  }

  return (
    <section id="best-sellers" className="best-sellers section">
      <div className="container section-title" data-aos="fade-up">
        <h2>Best Sellers</h2>
        <p>Discover our most popular products loved by customers</p>
      </div>
      <div className="container" data-aos="fade-up" data-aos-delay="100">
        {bestSellers.length === 0 ? (
          <div className="text-center py-5">
            <p className="text-muted">No best sellers available at the moment.</p>
            <a href="/products" className="btn btn-primary">Browse All Products</a>
          </div>
        ) : (
          <div className="row g-4">
            {bestSellers.map((product) => (
              <div key={product.id} className="col-lg-3 col-md-6 col-sm-6">
                <ProductCard
                  product={product}
                  onAddToCart={handleAddToCart}
                  onAddToWishlist={handleAddToWishlist}
                />
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
};

export default BestSellers;