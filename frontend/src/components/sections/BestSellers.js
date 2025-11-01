// frontend/src/components/sections/BestSellers.js
import React from 'react';
import { useProducts } from '../../hooks/useProducts';
import ProductCard from '../common/ProductCard';

const BestSellers = () => {
  const { products, loading, error } = useProducts('best-sellers');

  const handleAddToCart = async (product) => {
    try {
      // You'll need to implement cart service integration
      console.log('Adding to cart:', product);
      // await cartService.addToCart(product.id, 1);
    } catch (error) {
      console.error('Failed to add to cart:', error);
    }
  };

  const handleAddToWishlist = async (product) => {
    try {
      console.log('Adding to wishlist:', product);
      // await userService.addToWishlist(product.id);
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
          <div className="text-center py-5">
            <div className="spinner-border" role="status">
              <span className="visually-hidden">Loading...</span>
            </div>
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
            Unable to load products. Please try again later.
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
        {products.length === 0 ? (
          <div className="text-center py-5">
            <p className="text-muted">No products available at the moment.</p>
          </div>
        ) : (
          <div className="row g-4">
            {products.map((product) => (
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