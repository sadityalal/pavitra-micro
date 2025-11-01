import React, { useEffect, useState } from 'react';
import { productService } from '../../services/productService.js';
import ProductCard from '../common/ProductCard.js';

const BestSellers = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        setLoading(true);
        // Try to get products from API
        const data = await productService.getBestSellers();
        setProducts(data);
      } catch (error) {
        console.warn('Using mock data due to API error:', error);
        // Fallback to mock data
        setProducts(getMockProducts());
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, []);

  const handleAddToCart = (product) => {
    console.log('Add to cart:', product);
  };

  const handleAddToWishlist = (product) => {
    console.log('Add to wishlist:', product);
  };

  if (loading) {
    return (
      <section id="best-sellers" className="best-sellers section">
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

  return (
    <section id="best-sellers" className="best-sellers section">
      <div className="container section-title" data-aos="fade-up">
        <h2>Best Sellers</h2>
        <p>Discover our most popular products loved by customers</p>
      </div>

      <div className="container" data-aos="fade-up" data-aos-delay="100">
        <div className="row g-5">
          {products.map((product) => (
            <div key={product.id} className="col-lg-3 col-md-6">
              <ProductCard 
                product={product}
                onAddToCart={handleAddToCart}
                onAddToWishlist={handleAddToWishlist}
              />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

// Mock data fallback
const getMockProducts = () => [
  {
    id: 1,
    name: "Apple iPhone 14",
    slug: "apple-iphone-14",
    short_description: "Latest iPhone with A15 Bionic chip",
    base_price: 79999.00,
    sale_price: 65000.00,
    main_image_url: "/uploads/products/iphone14-pro.jpg",
    stock_status: "in_stock",
    stock_quantity: 10,
    rating: 4.5,
    review_count: 24
  },
  {
    id: 2,
    name: "Premium Headphones",
    slug: "premium-headphones",
    short_description: "High quality wireless headphones",
    base_price: 299.00,
    sale_price: 199.00,
    main_image_url: "/uploads/products/headphones.jpg",
    stock_status: "in_stock",
    stock_quantity: 15,
    rating: 4.5,
    review_count: 24
  }
];

export default BestSellers;
