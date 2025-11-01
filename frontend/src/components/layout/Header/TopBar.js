import React from 'react';
import { useSettingsContext } from '../../../contexts/SettingsContext.js';

const TopBar = () => {
  const { frontendSettings } = useSettingsContext();

  return (
    <div className="top-bar py-2">
      <div className="container-fluid container-xl">
        <div className="row align-items-center">
          <div className="col-lg-4 d-none d-lg-flex">
            <div className="top-bar-item">
              <i className="bi bi-telephone-fill me-2"></i>
              <span>Need help? Call us: </span>
              <a href={`tel:${frontendSettings?.site_phone || '+1 (234) 567-890'}`}>
                {frontendSettings?.site_phone || '+1 (234) 567-890'}
              </a>
            </div>
          </div>

          <div className="col-lg-4 col-md-12 text-center">
            <div className="announcement-slider swiper init-swiper">
              <div className="swiper-wrapper">
                <div className="swiper-slide">
                  🚚 Free shipping on orders over {frontendSettings?.currency_symbol || '$'}{frontendSettings?.free_shipping_min_amount || '50'}
                </div>
                <div className="swiper-slide">
                  💰 {frontendSettings?.return_period_days || '30'} days money back guarantee.
                </div>
                <div className="swiper-slide">
                  🎁 20% off on your first order
                </div>
              </div>
            </div>
          </div>

          <div className="col-lg-4 d-none d-lg-block">
            <div className="d-flex justify-content-end">
              <div className="top-bar-item dropdown me-3">
                <a href="#" className="dropdown-toggle" data-bs-toggle="dropdown">
                  <i className="bi bi-translate me-2"></i>EN
                </a>
                <ul className="dropdown-menu">
                  <li><a className="dropdown-item" href="#"><i className="bi bi-check2 me-2 selected-icon"></i>English</a></li>
                  <li><a className="dropdown-item" href="#">Español</a></li>
                  <li><a className="dropdown-item" href="#">Français</a></li>
                  <li><a className="dropdown-item" href="#">Deutsch</a></li>
                </ul>
              </div>
              <div className="top-bar-item dropdown">
                <a href="#" className="dropdown-toggle" data-bs-toggle="dropdown">
                  <i className="bi bi-currency-dollar me-2"></i>{frontendSettings?.currency || 'USD'}
                </a>
                <ul className="dropdown-menu">
                  <li><a className="dropdown-item" href="#"><i className="bi bi-check2 me-2 selected-icon"></i>{frontendSettings?.currency || 'USD'}</a></li>
                  <li><a className="dropdown-item" href="#">EUR</a></li>
                  <li><a className="dropdown-item" href="#">GBP</a></li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TopBar;
