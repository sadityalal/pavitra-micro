import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext.js';
import { SettingsProvider } from './contexts/SettingsContext.js';
import { CartProvider } from './contexts/CartContext.js'; // ADD THIS
import Layout from './components/layout/Layout.js';
import HomePage from './pages/HomePage.js';
import AuthPage from './pages/AuthPage.js';
import CartPage from './pages/CartPage.js';
import { useSession } from './hooks/useSession';

function App() {
  useSession(); // Initialize session for guest users
  useEffect(() => {
    const initializeScripts = () => {
      if (typeof bootstrap !== 'undefined') {
        const dropdowns = document.querySelectorAll('.dropdown-toggle');
        dropdowns.forEach(dropdown => {
          new bootstrap.Dropdown(dropdown);
        });
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        if (tooltipTriggerList.length > 0 && bootstrap.Tooltip) {
          const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
        }
        const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
        if (popoverTriggerList.length > 0 && bootstrap.Popover) {
          const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
        }
      }
      if (typeof initSwiper === 'function') {
        initSwiper();
      }
      if (typeof AOS !== 'undefined' && typeof AOS.init === 'function') {
        AOS.init({
          duration: 800,
          easing: 'ease-in-out',
          once: true,
          mirror: false
        });
      }
      if (typeof initCustomScripts === 'function') {
        initCustomScripts();
      }
      const scrollTop = document.getElementById('scroll-top');
      if (scrollTop) {
        scrollTop.addEventListener('click', (e) => {
          e.preventDefault();
          window.scrollTo({
            top: 0,
            behavior: 'smooth'
          });
        });
        const toggleScrollTop = () => {
          if (window.scrollY > 100) {
            scrollTop.classList.add('active');
          } else {
            scrollTop.classList.remove('active');
          }
        };
        window.addEventListener('load', toggleScrollTop);
        document.addEventListener('scroll', toggleScrollTop);
      }
      const mobileNavToggle = document.querySelector('.mobile-nav-toggle');
      const navmenu = document.querySelector('#navmenu');
      if (mobileNavToggle && navmenu) {
        mobileNavToggle.addEventListener('click', function(e) {
          e.preventDefault();
          navmenu.classList.toggle('navmenu-mobile');
          this.classList.toggle('bi-list');
          this.classList.toggle('bi-x');
        });
      }
      const navLinks = document.querySelectorAll('#navmenu .nav-link, #navmenu .dropdown-item');
      navLinks.forEach(link => {
        link.addEventListener('click', () => {
          if (navmenu.classList.contains('navmenu-mobile')) {
            navmenu.classList.remove('navmenu-mobile');
            if (mobileNavToggle) {
              mobileNavToggle.classList.toggle('bi-list');
              mobileNavToggle.classList.toggle('bi-x');
            }
          }
        });
      });
      const dropdownToggles = document.querySelectorAll('.toggle-dropdown');
      dropdownToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
          e.preventDefault();
          const parent = this.closest('li');
          if (parent) {
            parent.classList.toggle('active');
          }
        });
      });
      const searchToggles = document.querySelectorAll('.mobile-search-toggle');
      const mobileSearch = document.getElementById('mobileSearch');
      searchToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
          e.preventDefault();
          if (mobileSearch) {
            mobileSearch.classList.toggle('show');
          }
        });
      });
      console.log('All scripts initialized successfully');
    };

    const timer = setTimeout(initializeScripts, 500);

    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'childList') {
          initializeScripts();
        }
      });
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    return () => {
      clearTimeout(timer);
      observer.disconnect();
      const scrollTop = document.getElementById('scroll-top');
      if (scrollTop) {
        scrollTop.replaceWith(scrollTop.cloneNode(true));
      }
      const mobileNavToggle = document.querySelector('.mobile-nav-toggle');
      if (mobileNavToggle) {
        mobileNavToggle.replaceWith(mobileNavToggle.cloneNode(true));
      }
    };
  }, []);

  // Add cart update event listener
  useEffect(() => {
    const handleCartUpdate = (event) => {
      console.log('Cart updated:', event.detail);
      // You can trigger cart refresh or show notifications here
      // This will be handled by individual components that use the useCart hook
    };

    document.addEventListener('cartUpdated', handleCartUpdate);

    return () => {
      document.removeEventListener('cartUpdated', handleCartUpdate);
    };
  }, []);

  useEffect(() => {
    const preloader = document.getElementById('preloader');
    if (preloader) {
      setTimeout(() => {
        preloader.style.display = 'none';
      }, 500);
    }
  }, []);

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        document.title = 'Come back to ' + (process.env.REACT_APP_SITE_NAME || 'Pavitra Trading');
      } else {
        document.title = process.env.REACT_APP_SITE_NAME || 'Pavitra Trading';
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  useEffect(() => {
    const handleOnline = () => {
      console.log('App is online');
      const event = new CustomEvent('appOnline');
      document.dispatchEvent(event);
    };

    const handleOffline = () => {
      console.log('App is offline');
      const event = new CustomEvent('appOffline');
      document.dispatchEvent(event);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  useEffect(() => {
    const handleError = (error) => {
      console.error('Application error:', error);
    };

    const handleUnhandledRejection = (event) => {
      console.error('Unhandled promise rejection:', event.reason);
      event.preventDefault();
    };

    window.addEventListener('error', handleError);
    window.addEventListener('unhandledrejection', handleUnhandledRejection);

    return () => {
      window.removeEventListener('error', handleError);
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
    };
  }, []);

  return (
    <AuthProvider>
      <SettingsProvider>
        <CartProvider> {/* WRAP WITH CARTPROVIDER */}
          <Router>
            <Layout>
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/cart" element={<CartPage />} />
                <Route path="/auth" element={<AuthPage />} />
                <Route path="/login" element={<AuthPage />} />
                <Route path="/register" element={<AuthPage />} />
              </Routes>
            </Layout>
          </Router>
        </CartProvider>
      </SettingsProvider>
    </AuthProvider>
  );
}

export default App;