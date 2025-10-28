import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { productService } from '../services/productService';
import ProductCard from '../components/common/ProductCard';

const Products = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const location = useLocation();

  useEffect(() => {
    const loadProducts = async () => {
      setLoading(true);
      setError('');
      try {
        // Get query parameters from URL
        const searchParams = new URLSearchParams(location.search);
        const params = {};

        // Convert URL params to API params
        if (searchParams.get('featured') === 'true') params.featured = true;
        if (searchParams.get('new_arrivals') === 'true') params.new_arrivals = true;
        if (searchParams.get('on_sale') === 'true') params.on_sale = true;
        if (searchParams.get('category_id')) params.category_id = searchParams.get('category_id');

        const response = await productService.getProducts(params);
        console.log('Products response:', response); // Debug log

        setProducts(response.products || response || []);
      } catch (err) {
        console.error('Failed to load products:', err);
        setError('Failed to load products. Please try again later.');
        setProducts([]);
      } finally {
        setLoading(false);
      }
    };

    loadProducts();
  }, [location.search]);

  const handleAddToCart = (product) => {
    console.log('Add to cart', product.id);
    // Implement cart functionality
  };

  const handleAddToWishlist = (id) => {
    console.log('Add to wishlist', id);
    // Implement wishlist functionality
  };

  if (loading) {
    return (
      <div className="container py-5 text-center">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
        <p className="mt-3">Loading products...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container py-5 text-center">
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="container py-4">
      <div className="row">
        <div className="col-12">
          <h2>Products</h2>
          <p className="text-muted">Browse our product collection</p>
        </div>
      </div>

      {products.length === 0 ? (
        <div className="text-center py-5">
          <h4>No products found</h4>
          <p className="text-muted">There are no products available in this category.</p>
        </div>
      ) : (
        <div className="row">
          {products.map((product) => (
            <div className="col-lg-3 col-md-4 col-sm-6 mb-4" key={product.id}>
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
  );
};

export default Products;