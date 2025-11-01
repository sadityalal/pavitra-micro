// frontend/src/components/layout/Header/TopBar.js
import React from 'react';
import { useSettings } from '../../../contexts/SettingsContext';

const TopBar = () => {
  const { frontendSettings, loading } = useSettings();

  if (loading) {
    return (
      <div className="top-bar py-2">
        <div className="container-fluid container-xl">
          <div className="text-center">
            <div className="spinner-border spinner-border-sm" role="status">
              <span className="visually-hidden">Loading...</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="top-bar py-2">
      <div className="container-fluid container-xl">
        <div className="row align-items-center">
          <div className="col-lg-4 d-none d-lg-flex">
            <div className="top-bar-item">
              <i className="bi bi-telephone-fill me-2"></i>
              <span>Need help? Call us: </span>
              <a href={`tel:${frontendSettings.site_phone}`}>
                {frontendSettings.site_phone}
              </a>
            </div>
          </div>

          <div className="col-lg-4 col-md-12 text-center">
            <div className="announcement-slider">
              <div className="swiper-wrapper">
                <div className="swiper-slide">
                  🚚 Free shipping on orders over {frontendSettings.currency_symbol}{frontendSettings.free_shipping_min_amount}
                </div>
                <div className="swiper-slide">
                  💰 {frontendSettings.return_period_days} days money back guarantee
                </div>
                <div className="swiper-slide">
                  🎁 Special offers available
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
                  <li><a className="dropdown-item" href="#">English</a></li>
                  <li><a className="dropdown-item" href="#">Hindi</a></li>
                </ul>
              </div>

              <div className="top-bar-item dropdown">
                <a href="#" className="dropdown-toggle" data-bs-toggle="dropdown">
                  <i className="bi bi-currency-exchange me-2"></i>{frontendSettings.currency}
                </a>
                <ul className="dropdown-menu">
                  <li><a className="dropdown-item" href="#">{frontendSettings.currency}</a></li>
                  <li><a className="dropdown-item" href="#">USD</a></li>
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