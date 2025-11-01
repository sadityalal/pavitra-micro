import React, { useState, useEffect } from 'react';
import { useAuth } from '../../../contexts/AuthContext';
import { useSettings } from '../../../contexts/SettingsContext';
import { useCategories } from '../../../hooks/useCategories';
import { useProducts } from '../../../hooks/useProducts';

const Navigation = () => {
  const { isAuthenticated, isAdmin } = useAuth();
  const { frontendSettings } = useSettings();
  const { categories, loading: categoriesLoading } = useCategories();
  const [activeTab, setActiveTab] = useState('featured');

  // Fetch products for different tabs
  const { products: featuredProducts, loading: featuredLoading } = useProducts('featured');
  const { products: newArrivals, loading: newArrivalsLoading } = useProducts('new-arrivals');
  const { products: bestSellers, loading: bestSellersLoading } = useProducts('best-sellers');

  // Get top-level categories (those without parent_id)
  const topLevelCategories = categories.filter(cat => !cat.parent_id);

  const getImageUrl = (imagePath) => {
    if (!imagePath || imagePath === 'null' || imagePath === 'undefined') {
      return '/assets/img/product/placeholder.jpg';
    }

    if (imagePath.startsWith('http')) {
      return imagePath;
    }

    // If it's a relative path starting with /uploads, use the backend URL
    if (imagePath.startsWith('/uploads/')) {
      const backendUrl = process.env.REACT_APP_PRODUCT_URL || 'http://localhost:8002';
      return `${backendUrl}${imagePath}`;
    }

    return imagePath;
  };

  const renderProductCard = (product) => (
    <div className="product-card" key={product.id}>
      <div className="product-image">
        <img
          src={getImageUrl(product.main_image_url)}
          alt={product.name}
          loading="lazy"
          onError={(e) => {
            e.target.src = '/assets/img/product/placeholder.jpg';
          }}
        />
        {product.compare_price && product.compare_price > product.base_price && (
          <span className="badge-sale">
            -{Math.round(((product.compare_price - product.base_price) / product.compare_price) * 100)}%
          </span>
        )}
        {product.is_featured && <span className="badge-new">New</span>}
      </div>
      <div className="product-info">
        <h5>{product.name}</h5>
        <p className="price">
          {product.compare_price && product.compare_price > product.base_price ? (
            <>
              <span className="original-price">{frontendSettings.currency_symbol}{product.compare_price}</span>
              <span className="current-price">{frontendSettings.currency_symbol}{product.base_price}</span>
            </>
          ) : (
            <span className="current-price">{frontendSettings.currency_symbol}{product.base_price}</span>
          )}
        </p>
        <a href={`/product/${product.slug}`} className="btn-view">View Product</a>
      </div>
    </div>
  );

  const renderProductsGrid = (products, loading) => {
    if (loading) {
      return (
        <div className="product-grid">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="product-card loading">
              <div className="product-image placeholder-glow">
                <div className="placeholder" style={{ height: '200px' }}></div>
              </div>
              <div className="product-info">
                <div className="placeholder placeholder-xs col-8"></div>
                <div className="placeholder placeholder-xs col-6 mt-2"></div>
                <div className="placeholder placeholder-xs col-4 mt-2"></div>
              </div>
            </div>
          ))}
        </div>
      );
    }

    if (!products || products.length === 0) {
      return (
        <div className="text-center py-4">
          <p className="text-muted">No products available</p>
        </div>
      );
    }

    return (
      <div className="product-grid">
        {products.slice(0, 4).map(renderProductCard)}
      </div>
    );
  };

  return (
    <div className="header-nav">
      <div className="container-fluid container-xl position-relative">
        <nav id="navmenu" className="navmenu">
          <ul>
            <li><a href="/" className="active">Home</a></li>
            <li><a href="/about">About</a></li>

            {/* Shop Megamenu */}
            <li className="products-megamenu-1">
              <a href="#"><span>Shop</span> <i className="bi bi-chevron-down toggle-dropdown"></i></a>

              {/* Mobile Megamenu */}
              <ul className="mobile-megamenu">
                <li><a href="/products">All Products</a></li>
                <li><a href="/products?featured=true">Featured Products</a></li>
                <li><a href="/products?new_arrivals=true">New Arrivals</a></li>
                <li><a href="/products?bestseller=true">Best Sellers</a></li>

                {/* Dynamic Categories */}
                {topLevelCategories.map(category => (
                  <li key={category.id} className="dropdown">
                    <a href={`/category/${category.slug}`}>
                      <span>{category.name}</span> <i className="bi bi-chevron-down toggle-dropdown"></i>
                    </a>
                    <ul>
                      <li><a href={`/category/${category.slug}`}>View All {category.name}</a></li>
                    </ul>
                  </li>
                ))}
              </ul>

              {/* Desktop Megamenu */}
              <div className="desktop-megamenu">
                <div className="megamenu-tabs">
                  <ul className="nav nav-tabs" id="productMegaMenuTabs" role="tablist">
                    <li className="nav-item" role="presentation">
                      <button
                        className={`nav-link ${activeTab === 'featured' ? 'active' : ''}`}
                        onClick={() => setActiveTab('featured')}
                      >
                        Featured
                      </button>
                    </li>
                    <li className="nav-item" role="presentation">
                      <button
                        className={`nav-link ${activeTab === 'new' ? 'active' : ''}`}
                        onClick={() => setActiveTab('new')}
                      >
                        New Arrivals
                      </button>
                    </li>
                    <li className="nav-item" role="presentation">
                      <button
                        className={`nav-link ${activeTab === 'bestsellers' ? 'active' : ''}`}
                        onClick={() => setActiveTab('bestsellers')}
                      >
                        Best Sellers
                      </button>
                    </li>
                    <li className="nav-item" role="presentation">
                      <button
                        className={`nav-link ${activeTab === 'categories' ? 'active' : ''}`}
                        onClick={() => setActiveTab('categories')}
                      >
                        Categories
                      </button>
                    </li>
                  </ul>
                </div>

                <div className="megamenu-content tab-content">
                  {/* Featured Tab */}
                  <div className={`tab-pane fade ${activeTab === 'featured' ? 'show active' : ''}`}>
                    {renderProductsGrid(featuredProducts, featuredLoading)}
                  </div>

                  {/* New Arrivals Tab */}
                  <div className={`tab-pane fade ${activeTab === 'new' ? 'show active' : ''}`}>
                    {renderProductsGrid(newArrivals, newArrivalsLoading)}
                  </div>

                  {/* Best Sellers Tab */}
                  <div className={`tab-pane fade ${activeTab === 'bestsellers' ? 'show active' : ''}`}>
                    {renderProductsGrid(bestSellers, bestSellersLoading)}
                  </div>

                  {/* Categories Tab */}
                  <div className={`tab-pane fade ${activeTab === 'categories' ? 'show active' : ''}`}>
                    <div className="category-grid">
                      {categoriesLoading ? (
                        <div className="text-center p-4">
                          <div className="spinner-border" role="status">
                            <span className="visually-hidden">Loading categories...</span>
                          </div>
                        </div>
                      ) : (
                        topLevelCategories.slice(0, 4).map((category) => (
                          <div key={category.id} className="category-column">
                            <h4><a href={`/category/${category.slug}`}>{category.name}</a></h4>
                            <ul>
                              <li><a href={`/category/${category.slug}`}>View All {category.name}</a></li>
                              {/* You can add subcategories here when available */}
                            </ul>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </li>

            <li><a href="/contact">Contact</a></li>

            {/* Admin Link */}
            {isAuthenticated && isAdmin() && (
              <li><a href="/admin" className="text-warning">Admin</a></li>
            )}
          </ul>
        </nav>
      </div>

      {/* Mobile Search */}
      <div className="collapse" id="mobileSearch">
        <div className="container">
          <form className="search-form" action="/search" method="GET">
            <div className="input-group">
              <input type="text" className="form-control" name="q" placeholder="Search for products" />
              <button className="btn" type="submit">
                <i className="bi bi-search"></i>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Navigation;