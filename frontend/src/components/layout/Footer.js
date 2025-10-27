import React from 'react';
import { useAuth } from '../../context/AuthContext';

const Footer = () => {
  const { siteSettings } = useAuth();

  return (
    <footer className="bg-dark text-light py-4 mt-5">
      <div className="container">
        <div className="row">
          <div className="col-md-4">
            <h5>{siteSettings.site_name || 'Pavitra Trading'}</h5>
            <p className="text-muted">
              {siteSettings.site_description || 'Your trusted online shopping destination'}
            </p>
          </div>
          <div className="col-md-4">
            <h5>Contact Info</h5>
            <p className="text-muted">
              <i className="bi bi-telephone me-2"></i>
              {siteSettings.site_phone || '+91-9711317009'}
              <br />
              <i className="bi bi-envelope me-2"></i>
              {siteSettings.site_email || 'support@pavitraenterprises.com'}
            </p>
          </div>
          <div className="col-md-4">
            <h5>Business Hours</h5>
            <p className="text-muted">
              {siteSettings.business_hours ? (
                <>
                  Mon-Fri: {siteSettings.business_hours.monday_friday}<br />
                  Sat: {siteSettings.business_hours.saturday}<br />
                  Sun: {siteSettings.business_hours.sunday}
                </>
              ) : (
                '9am-6pm (Mon-Sat)'
              )}
            </p>
          </div>
        </div>
        <hr className="my-3" />
        <div className="text-center text-muted">
          <small>
            &copy; {new Date().getFullYear()} {siteSettings.site_name || 'Pavitra Trading'}. All rights reserved.
          </small>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
