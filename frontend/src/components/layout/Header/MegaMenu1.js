import React from 'react';

const MegaMenu1 = () => {
  return (
    <li className="products-megamenu-1">
      <a href="#"><span>Megamenu 1</span> <i className="bi bi-chevron-down toggle-dropdown"></i></a>

      {/* Mobile View */}
      <ul className="mobile-megamenu">
        <li><a href="#">Featured Products</a></li>
        <li><a href="#">New Arrivals</a></li>
        <li><a href="#">Sale Items</a></li>

        <li className="dropdown">
          <a href="#"><span>Clothing</span> <i className="bi bi-chevron-down toggle-dropdown"></i></a>
          <ul>
            <li><a href="#">Men's Wear</a></li>
            <li><a href="#">Women's Wear</a></li>
            <li><a href="#">Kids Collection</a></li>
            <li><a href="#">Sportswear</a></li>
            <li><a href="#">Accessories</a></li>
          </ul>
        </li>

        <li className="dropdown">
          <a href="#"><span>Electronics</span> <i className="bi bi-chevron-down toggle-dropdown"></i></a>
          <ul>
            <li><a href="#">Smartphones</a></li>
            <li><a href="#">Laptops</a></li>
            <li><a href="#">Audio Devices</a></li>
            <li><a href="#">Smart Home</a></li>
            <li><a href="#">Accessories</a></li>
          </ul>
        </li>

        <li className="dropdown">
          <a href="#"><span>Home &amp; Living</span> <i className="bi bi-chevron-down toggle-dropdown"></i></a>
          <ul>
            <li><a href="#">Furniture</a></li>
            <li><a href="#">Decor</a></li>
            <li><a href="#">Kitchen</a></li>
            <li><a href="#">Bedding</a></li>
            <li><a href="#">Lighting</a></li>
          </ul>
        </li>

        <li className="dropdown">
          <a href="#"><span>Beauty</span> <i className="bi bi-chevron-down toggle-dropdown"></i></a>
          <ul>
            <li><a href="#">Skincare</a></li>
            <li><a href="#">Makeup</a></li>
            <li><a href="#">Haircare</a></li>
            <li><a href="#">Fragrances</a></li>
            <li><a href="#">Personal Care</a></li>
          </ul>
        </li>
      </ul>

      {/* Desktop View */}
      <div className="desktop-megamenu">
        <div className="megamenu-tabs">
          <ul className="nav nav-tabs" id="productMegaMenuTabs" role="tablist">
            <li className="nav-item" role="presentation">
              <button className="nav-link active" id="featured-tab" data-bs-toggle="tab" data-bs-target="#featured-content-1862" type="button" aria-selected="true" role="tab">Featured</button>
            </li>
            <li className="nav-item" role="presentation">
              <button className="nav-link" id="new-tab" data-bs-toggle="tab" data-bs-target="#new-content-1862" type="button" aria-selected="false" tabindex="-1" role="tab">New Arrivals</button>
            </li>
            <li className="nav-item" role="presentation">
              <button className="nav-link" id="sale-tab" data-bs-toggle="tab" data-bs-target="#sale-content-1862" type="button" aria-selected="false" tabindex="-1" role="tab">Sale</button>
            </li>
            <li className="nav-item" role="presentation">
              <button className="nav-link" id="category-tab" data-bs-toggle="tab" data-bs-target="#category-content-1862" type="button" aria-selected="false" tabindex="-1" role="tab">Categories</button>
            </li>
          </ul>
        </div>

        {/* Tabs Content */}
        <div className="megamenu-content tab-content">
          {/* Featured Tab */}
          <div className="tab-pane fade show active" id="featured-content-1862" role="tabpanel" aria-labelledby="featured-tab">
            <div className="product-grid">
              <div className="product-card">
                <div className="product-image">
                  <img src="assets/img/product/product-1.webp" alt="Featured Product" loading="lazy" />
                </div>
                <div className="product-info">
                  <h5>Premium Headphones</h5>
                  <p className="price">$129.99</p>
                  <a href="#" className="btn-view">View Product</a>
                </div>
              </div>
              {/* Add more product cards */}
            </div>
          </div>
          {/* Add other tabs content */}
        </div>
      </div>
    </li>
  );
};

export default MegaMenu1;
