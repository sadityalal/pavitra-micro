// frontend/src/pages/ProductDetails.js
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { productService } from '../services/productService';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';

const ProductDetails = () => {
  const { id } = useParams();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const { addToCart } = useCart();
  const { isAuthenticated, siteSettings } = useAuth();

  useEffect(() => {
    loadProduct();
  }, [id]);

  const loadProduct = async () => {
    try {
      setLoading(true);
      const productData = await productService.getProduct(id);
      setProduct(productData);
    } catch (error) {
      console.error('Failed to load product:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = async () => {
    try {
      await addToCart(product.id, quantity, product);
      alert('Product added to cart!');
    } catch (error) {
      console.error('Failed to add to cart:', error);
      alert('Failed to add product to cart');
    }
  };

  const handleAddToWishlist = async () => {
    if (!isAuthenticated) {
      alert('Please login to add items to wishlist');
      return;
    }
    // Wishlist functionality would be implemented here
    console.log('Add to wishlist:', product.id);
  };

  const formatPrice = (price) => {
    return `${siteSettings.currency_symbol || '₹'}${parseFloat(price).toFixed(2)}`;
  };

  if (loading) {
    return (
      <div className="container py-5 text-center">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
        <p className="mt-3">Loading product details...</p>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="container py-5 text-center">
        <h2>Product Not Found</h2>
        <p>The product you're looking for doesn't exist.</p>
      </div>
    );
  }

  return (
    <div className="container py-5">
      <div className="row">
        <div className="col-md-6">
          <img
            src={getImageUrl(product.main_image_url)}
            alt={product.name}
            className="img-fluid rounded"
            style={{ maxHeight: '500px', objectFit: 'cover' }}
          />
        </div>
        <div className="col-md-6">
          <h1>{product.name}</h1>
          <p className="text-muted">SKU: {product.sku}</p>

          <div className="product-price mb-3">
            <h3 className="text-primary">{formatPrice(product.base_price)}</h3>
            {product.compare_price && product.compare_price > product.base_price && (
              <del className="text-muted me-2">{formatPrice(product.compare_price)}</del>
            )}
          </div>

          <div className="product-description mb-4">
            <p>{product.description || product.short_description}</p>
          </div>

          <div className="stock-info mb-3">
            {product.stock_quantity > 0 ? (
              <span className="text-success">
                <i className="bi bi-check-circle me-2"></i>
                In Stock ({product.stock_quantity} available)
              </span>
            ) : (
              <span className="text-danger">
                <i className="bi bi-x-circle me-2"></i>
                Out of Stock
              </span>
            )}
          </div>

          <div className="quantity-selector mb-4">
            <label htmlFor="quantity" className="form-label">Quantity:</label>
            <input
              type="number"
              id="quantity"
              className="form-control"
              value={quantity}
              onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
              min="1"
              max={product.stock_quantity}
              style={{ width: '100px' }}
            />
          </div>

          <div className="action-buttons mb-4">
            <button
              className="btn btn-primary me-3"
              onClick={handleAddToCart}
              disabled={product.stock_quantity === 0}
            >
              <i className="bi bi-cart3 me-2"></i>
              Add to Cart
            </button>
            <button
              className="btn btn-outline-secondary"
              onClick={handleAddToWishlist}
            >
              <i className="bi bi-heart me-2"></i>
              Add to Wishlist
            </button>
          </div>

          <div className="product-features">
            <h5>Product Features:</h5>
            <ul>
              <li>Free shipping on orders over {formatPrice(siteSettings.free_shipping_threshold || 999)}</li>
              <li>{siteSettings.return_period_days || 10}-day return policy</li>
              <li>Secure payment processing</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductDetails;