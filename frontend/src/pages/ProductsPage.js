import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useProducts } from '../hooks/useProducts';
import { useCategories } from '../hooks/useCategories';
import { useCartContext } from '../contexts/CartContext';
import { useAuth } from '../contexts/AuthContext';
import { useSettings } from '../contexts/SettingsContext';
import { useToast } from '../contexts/ToastContext';
import ProductCard from '../components/common/ProductCard';

const ProductsPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [filters, setFilters] = useState({
    category_slug: searchParams.get('category') || '',
    min_price: searchParams.get('min_price') || 0,
    max_price: searchParams.get('max_price') || 100000,
    brands: searchParams.get('brands') ? searchParams.get('brands').split(',') : [],
    stock_status: searchParams.get('stock_status') ? searchParams.get('stock_status').split(',') : [],
    sort_by: searchParams.get('sort_by') || 'created_at',
    sort_order: searchParams.get('sort_order') || 'desc',
    search: searchParams.get('search') || ''
  });

  const { products, loading, error, pagination } = useProducts('all', filters);
  const { categories, loading: categoriesLoading } = useCategories();
  const { addToCart } = useCartContext();
  const { isAuthenticated } = useAuth();
  const { frontendSettings } = useSettings();
  const { success, error: toastError } = useToast();

  // Update URL when filters change
  useEffect(() => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value && (Array.isArray(value) ? value.length > 0 : true)) {
        if (Array.isArray(value)) {
          params.set(key, value.join(','));
        } else {
          params.set(key, value);
        }
      }
    });
    setSearchParams(params);
  }, [filters, setSearchParams]);

  const handleFilterChange = (filterName, value) => {
    setFilters(prev => ({
      ...prev,
      [filterName]: value
    }));
  };

  const handlePriceFilter = () => {
    // Price filter is already applied through state
  };

  const clearAllFilters = () => {
    setFilters({
      category_slug: '',
      min_price: 0,
      max_price: 100000,
      brands: [],
      stock_status: [],
      sort_by: 'created_at',
      sort_order: 'desc',
      search: ''
    });
  };

  const handleSort = (sortBy, sortOrder = 'desc') => {
    setFilters(prev => ({
      ...prev,
      sort_by: sortBy,
      sort_order: sortOrder
    }));
  };

  const handleAddToCart = async (product) => {
    try {
      await addToCart(product.id, 1);
      success('Product added to cart!');
    } catch (error) {
      toastError(error.message || 'Failed to add product to cart');
    }
  };

  const handleAddToWishlist = async (productId) => {
    if (!isAuthenticated) {
      toastError('Please login to add items to wishlist');
      return;
    }
    // Implement wishlist functionality
    toastError('Wishlist functionality coming soon');
  };

  if (loading && !products.length) {
    return (
      <div className="page-title light-background">
        <div className="container d-lg-flex justify-content-between align-items-center py-3">
          <h1>Our Products</h1>
          <div className="spinner-border" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Page Title */}
      <div className="page-title light-background">
        <div className="container d-lg-flex justify-content-between align-items-center py-3">
          <h1 data-aos="fade-up">Our Products</h1>
          <nav className="breadcrumbs">
            <ol>
              <li><Link to="/">Home</Link></li>
              <li className="current">Products</li>
            </ol>
          </nav>
        </div>
      </div>

      {/* Products Section */}
      <section className="products-section section pt-4">
        <div className="container">
          <div className="row">
            {/* Sidebar Filters */}
            <div className="col-lg-3 col-md-4">
              <div className="products-sidebar position-sticky" style={{ top: '100px' }} data-aos="fade-right" data-aos-delay="100">

                {/* Categories Filter */}
                <div className="card shadow-sm border-0 mb-3">
                  <div className="card-header bg-light">
                    <h5 className="mb-0 text-dark"><i className="bi bi-grid-3x3-gap me-2"></i>Categories</h5>
                  </div>
                  <div className="card-body p-0 bg-light">
                    <div className="list-group list-group-flush">
                      <button
                        onClick={() => handleFilterChange('category_slug', '')}
                        className={`list-group-item list-group-item-action d-flex justify-content-between align-items-center border-0 ${!filters.category_slug ? 'active' : ''}`}
                      >
                        All Categories
                        <span className={`badge ${!filters.category_slug ? 'bg-primary' : 'bg-secondary'} rounded-pill`}>
                          {pagination.totalCount || 0}
                        </span>
                      </button>
                      {categories.map(category => (
                        <button
                          key={category.id}
                          onClick={() => handleFilterChange('category_slug', category.slug)}
                          className={`list-group-item list-group-item-action d-flex justify-content-between align-items-center border-0 ${filters.category_slug === category.slug ? 'active' : ''}`}
                        >
                          {category.name}
                          <span className={`badge ${filters.category_slug === category.slug ? 'bg-primary' : 'bg-secondary'} rounded-pill`}>
                            {/* Category count would need additional API endpoint */}
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Price Filter */}
                <div className="card shadow-sm border-0 mb-3" data-aos="fade-right" data-aos-delay="200">
                  <div className="card-header bg-light">
                    <h5 className="mb-0 text-dark"><i className="bi bi-currency-rupee me-2"></i>Price Range</h5>
                  </div>
                  <div className="card-body bg-light">
                    <div className="row g-2 mb-3">
                      <div className="col-6">
                        <label className="form-label small text-dark">Min</label>
                        <div className="input-group input-group-sm">
                          <span className="input-group-text bg-white text-dark border-secondary">
                            {frontendSettings.currency_symbol}
                          </span>
                          <input
                            type="number"
                            className="form-control border-secondary"
                            value={filters.min_price}
                            onChange={(e) => handleFilterChange('min_price', parseInt(e.target.value) || 0)}
                            min="0"
                          />
                        </div>
                      </div>
                      <div className="col-6">
                        <label className="form-label small text-dark">Max</label>
                        <div className="input-group input-group-sm">
                          <span className="input-group-text bg-white text-dark border-secondary">
                            {frontendSettings.currency_symbol}
                          </span>
                          <input
                            type="number"
                            className="form-control border-secondary"
                            value={filters.max_price}
                            onChange={(e) => handleFilterChange('max_price', parseInt(e.target.value) || 100000)}
                            min="0"
                          />
                        </div>
                      </div>
                    </div>
                    <button className="btn btn-dark btn-sm w-100 border-0" onClick={handlePriceFilter}>
                      Apply Filter
                    </button>
                  </div>
                </div>

                {/* Stock Status Filter */}
                <div className="card shadow-sm border-0 mb-3" data-aos="fade-right" data-aos-delay="350">
                  <div className="card-header bg-light">
                    <h5 className="mb-0 text-dark"><i className="bi bi-box me-2"></i>Stock Status</h5>
                  </div>
                  <div className="card-body bg-light">
                    {['in_stock', 'low_stock', 'out_of_stock'].map(status => (
                      <div key={status} className="form-check mb-2">
                        <input
                          className="form-check-input border-primary"
                          type="checkbox"
                          checked={filters.stock_status.includes(status)}
                          onChange={(e) => {
                            const newStatus = e.target.checked
                              ? [...filters.stock_status, status]
                              : filters.stock_status.filter(s => s !== status);
                            handleFilterChange('stock_status', newStatus);
                          }}
                          id={status}
                        />
                        <label className="form-check-label small text-dark" htmlFor={status}>
                          {status.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                        </label>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Clear Filters */}
                <button className="btn btn-outline-dark w-100 border-dark" onClick={clearAllFilters} data-aos="fade-right" data-aos-delay="400">
                  <i className="bi bi-arrow-clockwise me-2"></i>Clear All Filters
                </button>
              </div>
            </div>

            {/* Products Grid */}
            <div className="col-lg-9 col-md-8">
              {/* Products Header */}
              <div className="d-flex flex-column flex-md-row justify-content-between align-items-start align-items-md-center mb-3" data-aos="fade-up">
                <div className="mb-2 mb-md-0">
                  <p className="text-muted mb-0">
                    Showing <strong className="text-dark">{products.length}</strong> of
                    <strong className="text-dark"> {pagination.totalCount}</strong> products
                  </p>
                </div>
                <div className="d-flex gap-2">
                  {/* Sort Options */}
                  <div className="dropdown">
                    <button className="btn btn-outline-dark dropdown-toggle border-dark" type="button" data-bs-toggle="dropdown">
                      <i className="bi bi-sort-down me-2"></i>Sort By
                    </button>
                    <ul className="dropdown-menu">
                      <li><button className="dropdown-item" onClick={() => handleSort('name', 'asc')}>Name: A to Z</button></li>
                      <li><button className="dropdown-item" onClick={() => handleSort('name', 'desc')}>Name: Z to A</button></li>
                      <li><button className="dropdown-item" onClick={() => handleSort('base_price', 'asc')}>Price: Low to High</button></li>
                      <li><button className="dropdown-item" onClick={() => handleSort('base_price', 'desc')}>Price: High to Low</button></li>
                      <li><button className="dropdown-item" onClick={() => handleSort('created_at', 'desc')}>Newest First</button></li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Products Grid */}
              <div className="products-container">
                {error ? (
                  <div className="alert alert-danger text-center">
                    <i className="bi bi-exclamation-triangle me-2"></i>
                    {error}
                  </div>
                ) : products.length === 0 ? (
                  <div className="col-12">
                    <div className="text-center py-4" data-aos="fade-up">
                      <div className="mb-3">
                        <i className="bi bi-search display-1 text-muted"></i>
                      </div>
                      <h3 className="text-muted">No Products Found</h3>
                      <p className="text-muted mb-3">We couldn't find any products matching your criteria.</p>
                      <div className="d-flex justify-content-center gap-2">
                        <button className="btn btn-dark" onClick={clearAllFilters}>Clear All Filters</button>
                        <Link to="/products" className="btn btn-outline-dark">View All Products</Link>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="row g-3" id="productsGrid">
                    {products.map((product, index) => (
                      <div key={product.id} className="col-xl-4 col-lg-6 col-md-6">
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

              {/* Load More Button */}
              {pagination.totalPages > pagination.page && (
                <div className="text-center mt-4" data-aos="fade-up">
                  <button
                    className="btn btn-outline-dark"
                    onClick={() => handleFilterChange('page', pagination.page + 1)}
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2"></span>
                        Loading...
                      </>
                    ) : (
                      <>
                        <i className="bi bi-arrow-down me-2"></i>Load More Products
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>
    </>
  );
};

export default ProductsPage;