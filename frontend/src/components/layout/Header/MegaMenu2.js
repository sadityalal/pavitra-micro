import React from 'react';

const MegaMenu2 = () => {
  return (
    <li className="products-megamenu-2">
      <a href="#"><span>Megamenu 2</span> <i className="bi bi-chevron-down toggle-dropdown"></i></a>

      {/* Mobile View */}
      <ul className="mobile-megamenu">
        <li><a href="#">Women</a></li>
        <li><a href="#">Men</a></li>
        <li><a href="#">Kids'</a></li>

        <li className="dropdown">
          <a href="#"><span>Clothing</span> <i className="bi bi-chevron-down toggle-dropdown"></i></a>
          <ul>
            <li><a href="#">Shirts &amp; Tops</a></li>
            <li><a href="#">Coats &amp; Outerwear</a></li>
            <li><a href="#">Underwear</a></li>
            <li><a href="#">Sweatshirts</a></li>
            <li><a href="#">Dresses</a></li>
            <li><a href="#">Swimwear</a></li>
          </ul>
        </li>

        <li className="dropdown">
          <a href="#"><span>Shoes</span> <i className="bi bi-chevron-down toggle-dropdown"></i></a>
          <ul>
            <li><a href="#">Boots</a></li>
            <li><a href="#">Sandals</a></li>
            <li><a href="#">Heels</a></li>
            <li><a href="#">Loafers</a></li>
            <li><a href="#">Slippers</a></li>
            <li><a href="#">Oxfords</a></li>
          </ul>
        </li>

        <li className="dropdown">
          <a href="#"><span>Accessories</span> <i className="bi bi-chevron-down toggle-dropdown"></i></a>
          <ul>
            <li><a href="#">Handbags</a></li>
            <li><a href="#">Eyewear</a></li>
            <li><a href="#">Hats</a></li>
            <li><a href="#">Watches</a></li>
            <li><a href="#">Jewelry</a></li>
            <li><a href="#">Belts</a></li>
          </ul>
        </li>

        <li className="dropdown">
          <a href="#"><span>Specialty Sizes</span> <i className="bi bi-chevron-down toggle-dropdown"></i></a>
          <ul>
            <li><a href="#">Plus Size</a></li>
            <li><a href="#">Petite</a></li>
            <li><a href="#">Wide Shoes</a></li>
            <li><a href="#">Narrow Shoes</a></li>
          </ul>
        </li>
      </ul>

      {/* Desktop View - Simplified for now */}
      <div className="desktop-megamenu">
        <div className="megamenu-tabs">
          <ul className="nav nav-tabs" role="tablist">
            <li className="nav-item" role="presentation">
              <button className="nav-link active" id="womens-tab" data-bs-toggle="tab" data-bs-target="#womens-content-1883" type="button" aria-selected="true" role="tab">WOMEN</button>
            </li>
            <li className="nav-item" role="presentation">
              <button className="nav-link" id="mens-tab" data-bs-toggle="tab" data-bs-target="#mens-content-1883" type="button" aria-selected="false" tabIndex="-1" role="tab">MEN</button>
            </li>
            <li className="nav-item" role="presentation">
              <button className="nav-link" id="kids-tab" data-bs-toggle="tab" data-bs-target="#kids-content-1883" type="button" aria-selected="false" tabIndex="-1" role="tab">KIDS</button>
            </li>
          </ul>
        </div>

        <div className="megamenu-content tab-content">
          <div className="tab-pane fade show active" id="womens-content-1883" role="tabpanel" aria-labelledby="womens-tab">
            <p>Women's fashion content will be loaded here</p>
          </div>
          <div className="tab-pane fade" id="mens-content-1883" role="tabpanel" aria-labelledby="mens-tab">
            <p>Men's fashion content will be loaded here</p>
          </div>
          <div className="tab-pane fade" id="kids-content-1883" role="tabpanel" aria-labelledby="kids-tab">
            <p>Kids fashion content will be loaded here</p>
          </div>
        </div>
      </div>
    </li>
  );
};

export default MegaMenu2;
