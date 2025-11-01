// frontend/src/components/layout/Header/Navigation.js
import React from 'react';
import { useAuth } from '../../../contexts/AuthContext';
import { useSettings } from '../../../contexts/SettingsContext';

const Navigation = () => {
  const { isAuthenticated, isAdmin } = useAuth();
  const { frontendSettings } = useSettings();

  return (
    <div className="header-nav">
      <div className="container-fluid container-xl position-relative">
        <nav id="navmenu" className="navmenu">
          <ul>
            <li><a href="/" className="active">Home</a></li>
            <li><a href="/about">About</a></li>

            {/* Products Mega Menu - Similar to your Jinja2 template */}
            <li className="products-megamenu-1">
              <a href="#"><span>Shop</span> <i className="bi bi-chevron-down toggle-dropdown"></i></a>

              {/* Mobile View */}
              <ul className="mobile-megamenu">
                <li><a href="/products">All Products</a></li>
                <li><a href="/products?featured=true">Featured Products</a></li>
                <li><a href="/products?new_arrivals=true">New Arrivals</a></li>
                <li><a href="/products?on_sale=true">On Sale</a></li>
                
                {/* Categories would be dynamically loaded here */}
                <li className="dropdown">
                  <a href="/category/electronics">
                    <span>Electronics</span> <i className="bi bi-chevron-down toggle-dropdown"></i>
                  </a>
                  <ul>
                    <li><a href="/product/smartphone">Smartphone</a></li>
                    <li><a href="/product/laptop">Laptop</a></li>
                    <li><a href="/product/headphones">Headphones</a></li>
                    <li><a href="/category/electronics">View All Electronics</a></li>
                  </ul>
                </li>
                
                <li className="dropdown">
                  <a href="/category/clothing">
                    <span>Clothing</span> <i className="bi bi-chevron-down toggle-dropdown"></i>
                  </a>
                  <ul>
                    <li><a href="/product/t-shirt">T-Shirt</a></li>
                    <li><a href="/product/jeans">Jeans</a></li>
                    <li><a href="/product/dress">Dress</a></li>
                    <li><a href="/category/clothing">View All Clothing</a></li>
                  </ul>
                </li>
              </ul>

              {/* Desktop View */}
              <div className="desktop-megamenu">
                <div className="megamenu-tabs">
                  <ul className="nav nav-tabs" id="productMegaMenuTabs" role="tablist">
                    <li className="nav-item" role="presentation">
                      <button className="nav-link active" id="featured-tab" data-bs-toggle="tab" data-bs-target="#featured-content" type="button" aria-selected="true" role="tab">Featured</button>
                    </li>
                    <li className="nav-item" role="presentation">
                      <button className="nav-link" id="new-tab" data-bs-toggle="tab" data-bs-target="#new-content" type="button" aria-selected="false" tabIndex="-1" role="tab">New Arrivals</button>
                    </li>
                    <li className="nav-item" role="presentation">
                      <button className="nav-link" id="categories-tab" data-bs-toggle="tab" data-bs-target="#categories-content" type="button" aria-selected="false" tabIndex="-1" role="tab">Categories</button>
                    </li>
                  </ul>
                </div>

                {/* Tabs Content */}
                <div className="megamenu-content tab-content">
                  {/* Featured Tab */}
                  <div className="tab-pane fade show active" id="featured-content" role="tabpanel" aria-labelledby="featured-tab">
                    <div className="product-grid">
                      {/* Featured products would be dynamically loaded here */}
                      <div className="product-card">
                        <a href="/product/smartphone" className="product-image-link">
                          <div className="product-image">
                            <img src="/assets/img/product/product-1.webp" alt="Smartphone" loading="lazy" />
                            <span className="badge-sale">-20%</span>
                          </div>
                        </a>
                        <div className="product-info">
                          <h5><a href="/product/smartphone">Premium Smartphone</a></h5>
                          <p className="price">
                            <span className="original-price">₹25,999</span>
                            <span className="current-price">₹20,799</span>
                          </p>
                          <a href="/product/smartphone" className="btn-view">View Product</a>
                        </div>
                      </div>
                      
                      <div className="product-card">
                        <a href="/product/laptop" className="product-image-link">
                          <div className="product-image">
                            <img src="/assets/img/product/product-2.webp" alt="Laptop" loading="lazy" />
                          </div>
                        </a>
                        <div className="product-info">
                          <h5><a href="/product/laptop">Gaming Laptop</a></h5>
                          <p className="price">
                            <span className="current-price">₹89,999</span>
                          </p>
                          <a href="/product/laptop" className="btn-view">View Product</a>
                        </div>
                      </div>
                      
                      {/* Add more featured products */}
                    </div>
                  </div>

                  {/* New Arrivals Tab */}
                  <div className="tab-pane fade" id="new-content" role="tabpanel" aria-labelledby="new-tab">
                    <div className="product-grid">
                      {/* New arrivals would be dynamically loaded here */}
                      <div className="product-card">
                        <a href="/product/smartwatch" className="product-image-link">
                          <div className="product-image">
                            <img src="/assets/img/product/product-3.webp" alt="Smartwatch" loading="lazy" />
                            <span className="badge-new">New</span>
                          </div>
                        </a>
                        <div className="product-info">
                          <h5><a href="/product/smartwatch">Smart Watch</a></h5>
                          <p className="price">
                            <span className="current-price">₹12,999</span>
                          </p>
                          <a href="/product/smartwatch" className="btn-view">View Product</a>
                        </div>
                      </div>
                      
                      {/* Add more new arrivals */}
                    </div>
                  </div>

                  {/* Categories Tab */}
                  <div className="tab-pane fade" id="categories-content" role="tabpanel" aria-labelledby="categories-tab">
                    <div className="category-grid">
                      <div className="category-column">
                        <h4><a href="/category/electronics">Electronics</a></h4>
                        <ul>
                          <li><a href="/product/smartphone">Smartphones</a></li>
                          <li><a href="/product/laptop">Laptops</a></li>
                          <li><a href="/product/headphones">Headphones</a></li>
                          <li><a href="/category/electronics" className="view-all">View all Electronics</a></li>
                        </ul>
                      </div>
                      
                      <div className="category-column">
                        <h4><a href="/category/clothing">Clothing</a></h4>
                        <ul>
                          <li><a href="/product/t-shirt">T-Shirts</a></li>
                          <li><a href="/product/jeans">Jeans</a></li>
                          <li><a href="/product/dress">Dresses</a></li>
                          <li><a href="/category/clothing" className="view-all">View all Clothing</a></li>
                        </ul>
                      </div>
                      
                      <div className="category-column">
                        <h4><a href="/category/home">Home & Living</a></h4>
                        <ul>
                          <li><a href="/product/decor">Home Decor</a></li>
                          <li><a href="/product/kitchen">Kitchen</a></li>
                          <li><a href="/product/furniture">Furniture</a></li>
                          <li><a href="/category/home" className="view-all">View all Home</a></li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </li>

            <li><a href="/contact">Contact</a></li>

            {/* Admin Link - Only show for admin users */}
            {isAuthenticated && isAdmin() && (
              <li><a href="/admin" className="text-warning">Admin</a></li>
            )}
          </ul>
        </nav>
      </div>

      {/* Mobile Search Form */}
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