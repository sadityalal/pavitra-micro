import React, { useEffect } from 'react';
import Header from './Header/Header.js';
import Footer from './Footer.js';

const Layout = ({ children }) => {
  useEffect(() => {
    // Ensure all external scripts are loaded and initialized
    const loadScripts = () => {
      // This will run after the component mounts
      console.log('Layout mounted - scripts should be available');
    };

    loadScripts();
  }, []);

  return (
    <div className="index-page">
      <Header />
      <main className="main">
        {children}
      </main>
      <Footer />
      
      {/* Scroll Top */}
      <a href="#" id="scroll-top" className="scroll-top d-flex align-items-center justify-content-center">
        <i className="bi bi-arrow-up-short"></i>
      </a>

      {/* Preloader - hidden by default since React loads quickly */}
      <div id="preloader" style={{ display: 'none' }}></div>
    </div>
  );
};

export default Layout;
