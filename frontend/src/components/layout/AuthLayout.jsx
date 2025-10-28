import React from 'react';
import { Link } from 'react-router-dom';

const AuthLayout = ({ title = 'Page', breadcrumb = [], children }) => {
  return (
    <>
      <div className="page-title light-background">
        <div className="container d-lg-flex justify-content-between align-items-center">
          <h1 className="mb-2 mb-lg-0">{title}</h1>
          <nav className="breadcrumbs">
            <ol>
              {breadcrumb.length === 0 ? (
                <li><Link to="/">Home</Link></li>
              ) : (
                breadcrumb.map((b, i) => (
                  <li key={i} className={i === breadcrumb.length - 1 ? 'current' : ''}>
                    {b.to ? <Link to={b.to}>{b.label}</Link> : <span>{b.label}</span>}
                  </li>
                ))
              )}
            </ol>
          </nav>
        </div>
      </div>

      <section id="auth" className="login section">
        <div className="container" data-aos="fade-up" data-aos-delay="100">
          <div className="row justify-content-center">
            <div className="col-lg-6 col-md-8 col-sm-10">
              <div className="auth-container" data-aos="fade-in" data-aos-delay="200">
                {children}
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
};

export default AuthLayout;
