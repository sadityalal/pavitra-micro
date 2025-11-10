import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { productService } from '../services/productService';
import { useCartContext } from '../contexts/CartContext';
import { useAuth } from '../contexts/AuthContext';
import { useSettings } from '../contexts/SettingsContext';
import { useToast } from '../contexts/ToastContext';

const ProductDetailPage = () => {
  const { slug } = useParams();
  const navigate = useNavigate();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedImage, setSelectedImage] = useState(0);
  const [quantity, setQuantity] = useState(1);
  const [relatedProducts, setRelatedProducts] = useState([]);

  const { addToCart } = useCartContext();
  const { isAuthenticated } = useAuth();
  const { frontendSettings } = useSettings();
  const { success, error: toastError } = useToast();

  useEffect(() => {
    fetchProduct();
  }, [slug]);

  const fetchProduct = async () => {
    try {
      setLoading(true);
      setError(null);
      const productData = await productService.getProductBySlug(slug);
      setProduct(productData);

      // Fetch related products based on category
      if (productData.category_id) {
        // This would need additional API endpoint for related products
        // For now, we'll use featured products as placeholder
        const featured = await productService.getFeaturedProducts();
        setRelatedProducts(featured.slice(0, 4));
      }
    } catch (err) {
      setError(err.message);
      console.error('Failed to fetch product:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = async () => {
    if (!product) return;

    try {
      await addToCart(product.id, quantity);
      success(`Added ${quantity} ${product.name} to cart!`);
    } catch (error) {
      toastError(error.message || 'Failed to add product to cart');
    }
  };

  const handleQuantityChange = (newQuantity) => {
    if (newQuantity < 1) return;
    if (product.stock_quantity && newQuantity > product.stock_quantity) {
      toastError(`Only ${product.stock_quantity} items available`);
      return;
    }
    setQuantity(newQuantity);
  };

  const handleAddToWishlist = () => {
    if (!isAuthenticated) {
      toastError('Please login to add items to wishlist');
      return;
    }
    // Implement wishlist functionality
    toastError('Wishlist functionality coming soon');
  };

  const getImageUrl = (imagePath) => {
    if (!imagePath || imagePath === 'null' || imagePath === 'undefined') {
      return '/assets/img/product/placeholder.jpg';
    }
    if (imagePath.startsWith('http')) {
      return imagePath;
    }
    if (imagePath.startsWith('/uploads/')) {
      const backendUrl = process.env.REACT_APP_PRODUCT_URL || 'http://localhost:8002';
      return `${backendUrl}${imagePath}`;
    }
    return imagePath;
  };

  if (loading) {
    return (
      <div className="container py-5">
        <div className="text-center">
          <div className="spinner-border" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="container py-5">
        <div className="text-center">
          <i className="bi bi-exclamation-triangle display-1 text-muted"></i>
          <h3 className="mt-3">Product Not Found</h3>
          <p className="text-muted">The product you're looking for doesn't exist.</p>
          <Link to="/products" className="btn btn-primary">Browse Products</Link>
        </div>
      </div>
    );
  }

  const images = product.image_gallery && Array.isArray(product.image_gallery)
    ? product.image_gallery
    : product.main_image_url
      ? [product.main_image_url]
      : [];

  return (
    <>
      {/* Page Title */}
      <div className="page-title light-background">
        <div className="container d-lg-flex justify-content-between align-items-center py-3">
          <h1 data-aos="fade-up">{product.name}</h1>
          <nav className="breadcrumbs">
            <ol>
              <li><Link to="/">Home</Link></li>
              <li><Link to="/products">Products</Link></li>
              <li className="current">{product.name}</li>
            </ol>
          </nav>
        </div>
      </div>

      {/* Product Detail Section */}
      <section className="product-detail-section section pt-4">
        <div className="container">
          <div className="row">
            {/* Product Images */}
            <div className="col-lg-6">
              <div className="product-images" data-aos="fade-right">
                {/* Main Image */}
                <div className="main-image mb-3">
                  <img
                    src={getImageUrl(images[selectedImage] || product.main_image_url)}
                    alt={product.name}
                    className="img-fluid rounded shadow-sm"
                    style={{ width: '100%', height: '400px', objectFit: 'cover' }}
                  />
                </div>

                {/* Image Thumbnails */}
                {images.length > 1 && (
                  <div className="image-thumbnails">
                    <div className="row g-2">
                      {images.map((image, index) => (
                        <div key={index} className="col-3">
                          <img
                            src={getImageUrl(image)}
                            alt={`${product.name} ${index + 1}`}
                            className={`img-fluid rounded cursor-pointer ${selectedImage === index ? 'border border-primary' : ''}`}
                            style={{ height: '80px', objectFit: 'cover', width: '100%' }}
                            onClick={() => setSelectedImage(index)}
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Product Info */}
            <div className="col-lg-6">
              <div className="product-info" data-aos="fade-left">
                {/* Product Badges */}
                <div className="product-badges mb-3">
                  {product.compare_price && product.compare_price > product.base_price && (
                    <span className="badge bg-danger me-2 border-0">
                      -{Math.round(((product.compare_price - product.base_price) / product.compare_price) * 100)}% OFF
                    </span>
                  )}
                  {product.is_featured && (
                    <span className="badge bg-dark me-2 border-0">Featured</span>
                  )}
                  {product.is_bestseller && (
                    <span className="badge bg-warning text-dark me-2 border-0">Best Seller</span>
                  )}
                  {product.stock_status === 'low_stock' && (
                    <span className="badge bg-warning text-dark border-0">Low Stock</span>
                  )}
                  {product.stock_status === 'out_of_stock' && (
                    <span className="badge bg-danger border-0">Out of Stock</span>
                  )}
                </div>

                {/* Product Title */}
                <h1 className="product-title mb-3">{product.name}</h1>

                {/* Rating */}
                <div className="product-rating mb-3">
                  <div className="d-flex align-items-center">
                    <div className="text-warning me-2">
                      {/* Static rating for now - would need reviews API */}
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-fill"></i>
                      <i className="bi bi-star-half"></i>
                    </div>
                    <span className="text-muted">(24 reviews)</span>
                  </div>
                </div>

                {/* Price */}
                <div className="product-price mb-4">
                  {product.compare_price && product.compare_price > product.base_price ? (
                    <>
                      <span className="text-muted text-decoration-line-through h5 me-2">
                        {frontendSettings.currency_symbol}{product.compare_price}
                      </span>
                      <span className="h2 text-dark fw-bold">
                        {frontendSettings.currency_symbol}{product.base_price}
                      </span>
                    </>
                  ) : (
                    <span className="h2 text-dark fw-bold">
                      {frontendSettings.currency_symbol}{product.base_price}
                    </span>
                  )}
                </div>

                {/* Short Description */}
                {product.short_description && (
                  <div className="product-short-description mb-4">
                    <p className="text-muted">{product.short_description}</p>
                  </div>
                )}

                {/* Stock Info */}
                <div className="stock-info mb-4">
                  {product.stock_status === 'in_stock' ? (
                    <div className="text-success">
                      <i className="bi bi-check-circle me-2"></i>
                      In Stock {product.stock_quantity && `(${product.stock_quantity} available)`}
                    </div>
                  ) : product.stock_status === 'low_stock' ? (
                    <div className="text-warning">
                      <i className="bi bi-exclamation-triangle me-2"></i>
                      Low Stock - Only {product.stock_quantity} left!
                    </div>
                  ) : (
                    <div className="text-danger">
                      <i className="bi bi-x-circle me-2"></i>
                      Out of Stock
                    </div>
                  )}
                </div>

                {/* Quantity and Add to Cart */}
                {product.stock_status !== 'out_of_stock' && (
                  <div className="add-to-cart-section mb-4">
                    <div className="row align-items-center">
                      <div className="col-auto">
                        <label className="form-label">Quantity:</label>
                      </div>
                      <div className="col-auto">
                        <div className="input-group" style={{ width: '140px' }}>
                          <button
                            className="btn btn-outline-secondary"
                            type="button"
                            onClick={() => handleQuantityChange(quantity - 1)}
                            disabled={quantity <= 1}
                          >
                            <i className="bi bi-dash"></i>
                          </button>
                          <input
                            type="text"
                            className="form-control text-center"
                            value={quantity}
                            readOnly
                          />
                          <button
                            className="btn btn-outline-secondary"
                            type="button"
                            onClick={() => handleQuantityChange(quantity + 1)}
                            disabled={product.stock_quantity && quantity >= product.stock_quantity}
                          >
                            <i className="bi bi-plus"></i>
                          </button>
                        </div>
                      </div>
                      <div className="col">
                        <button
                          className="btn btn-dark btn-lg w-100"
                          onClick={handleAddToCart}
                          disabled={product.stock_status === 'out_of_stock'}
                        >
                          <i className="bi bi-cart-plus me-2"></i>
                          Add to Cart
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Additional Actions */}
                <div className="product-actions mb-4">
                  <div className="d-flex gap-2">
                    <button
                      className="btn btn-outline-dark"
                      onClick={handleAddToWishlist}
                    >
                      <i className="bi bi-heart me-2"></i>
                      Add to Wishlist
                    </button>
                    <button className="btn btn-outline-dark">
                      <i className="bi bi-share me-2"></i>
                      Share
                    </button>
                  </div>
                </div>

                {/* Product Meta */}
                <div className="product-meta">
                  <div className="row small text-muted">
                    <div className="col-6">
                      <strong>SKU:</strong> {product.sku}
                    </div>
                    <div className="col-6">
                      <strong>GST:</strong> {product.gst_rate}% inclusive
                    </div>
                    <div className="col-6">
                      <strong>Category:</strong> {product.category_name || 'Uncategorized'}
                    </div>
                    <div className="col-6">
                      <strong>Brand:</strong> {product.brand_name || 'No Brand'}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Product Tabs */}
          <div className="row mt-5">
            <div className="col-12">
              <div className="product-tabs" data-aos="fade-up">
                <ul className="nav nav-tabs" id="productTabs" role="tablist">
                  <li className="nav-item" role="presentation">
                    <button
                      className="nav-link active"
                      id="description-tab"
                      data-bs-toggle="tab"
                      data-bs-target="#description"
                      type="button"
                      role="tab"
                    >
                      Description
                    </button>
                  </li>
                  <li className="nav-item" role="presentation">
                    <button
                      className="nav-link"
                      id="specifications-tab"
                      data-bs-toggle="tab"
                      data-bs-target="#specifications"
                      type="button"
                      role="tab"
                    >
                      Specifications
                    </button>
                  </li>
                  <li className="nav-item" role="presentation">
                    <button
                      className="nav-link"
                      id="reviews-tab"
                      data-bs-toggle="tab"
                      data-bs-target="#reviews"
                      type="button"
                      role="tab"
                    >
                      Reviews
                    </button>
                  </li>
                </ul>
                <div className="tab-content p-4 border border-top-0 rounded-bottom">
                  {/* Description Tab */}
                  <div className="tab-pane fade show active" id="description" role="tabpanel">
                    {product.description ? (
                      <div dangerouslySetInnerHTML={{ __html: product.description }} />
                    ) : (
                      <p className="text-muted">No description available.</p>
                    )}
                  </div>

                  {/* Specifications Tab */}
                  <div className="tab-pane fade" id="specifications" role="tabpanel">
                    {product.specification ? (
                      <div className="row">
                        {Object.entries(product.specification).map(([key, value]) => (
                          <div key={key} className="col-md-6 mb-2">
                            <strong>{key.replace(/_/g, ' ').toUpperCase()}:</strong> {value}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-muted">No specifications available.</p>
                    )}
                  </div>

                  {/* Reviews Tab */}
                  <div className="tab-pane fade" id="reviews" role="tabpanel">
                    <div className="text-center py-4">
                      <i className="bi bi-chat-square-text display-1 text-muted"></i>
                      <h4 className="text-muted mt-3">No Reviews Yet</h4>
                      <p className="text-muted">Be the first to review this product!</p>
                      {isAuthenticated ? (
                        <button className="btn btn-primary">Write a Review</button>
                      ) : (
                        <Link to="/auth?form=login" className="btn btn-primary">Login to Review</Link>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Related Products */}
          {relatedProducts.length > 0 && (
            <div className="row mt-5">
              <div className="col-12">
                <div className="related-products" data-aos="fade-up">
                  <h3 className="mb-4">Related Products</h3>
                  <div className="row g-3">
                    {relatedProducts.map(relatedProduct => (
                      <div key={relatedProduct.id} className="col-lg-3 col-md-6">
                        <ProductCard product={relatedProduct} />
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </section>
    </>
  );
};

export default ProductDetailPage;