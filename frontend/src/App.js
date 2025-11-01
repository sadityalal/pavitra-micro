// frontend/src/App.js
import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext.js';
import { SettingsProvider } from './contexts/SettingsContext.js';
import Layout from './components/layout/Layout.js';
import HomePage from './pages/HomePage.js';
import AuthPage from './pages/AuthPage.js';

function App() {
  useEffect(() => {
    // Re-initialize JavaScript after React renders
    const initializeScripts = () => {
      // Re-initialize Bootstrap components
      if (typeof bootstrap !== 'undefined') {
        // Initialize dropdowns
        const dropdowns = document.querySelectorAll('.dropdown-toggle');
        dropdowns.forEach(dropdown => {
          new bootstrap.Dropdown(dropdown);
        });

        // Initialize any other Bootstrap components as needed
        // Initialize tooltips if needed
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        if (tooltipTriggerList.length > 0 && bootstrap.Tooltip) {
          const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
        }

        // Initialize popovers if needed
        const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
        if (popoverTriggerList.length > 0 && bootstrap.Popover) {
          const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
        }
      }

      // Call any existing initialization functions from your main.js
      if (typeof initSwiper === 'function') {
        initSwiper();
      }
      
      // Initialize AOS (Animate On Scroll) if available
      if (typeof AOS !== 'undefined' && typeof AOS.init === 'function') {
        AOS.init({
          duration: 800,
          easing: 'ease-in-out',
          once: true,
          mirror: false
        });
      }

      // Initialize any custom scripts that might be needed
      if (typeof initCustomScripts === 'function') {
        initCustomScripts();
      }

      // Initialize scroll top functionality
      const scrollTop = document.getElementById('scroll-top');
      if (scrollTop) {
        scrollTop.addEventListener('click', (e) => {
          e.preventDefault();
          window.scrollTo({
            top: 0,
            behavior: 'smooth'
          });
        });

        // Show/hide scroll top button based on scroll position
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

      // Initialize mobile navigation toggle
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

      // Close mobile menu when clicking on a link
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

      // Initialize dropdown submenus for mobile
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

      // Initialize search functionality
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

    // Initialize after a short delay to ensure DOM is ready
    const timer = setTimeout(initializeScripts, 500);

    // Also initialize when the component mounts
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'childList') {
          // Re-initialize scripts when new elements are added to DOM
          initializeScripts();
        }
      });
    });

    // Start observing the document body for changes
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    return () => {
      clearTimeout(timer);
      observer.disconnect();
      
      // Cleanup event listeners
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

  // Handle preloader
  useEffect(() => {
    const preloader = document.getElementById('preloader');
    if (preloader) {
      // Hide preloader when component mounts
      setTimeout(() => {
        preloader.style.display = 'none';
      }, 500);
    }
  }, []);

  // Handle page visibility changes
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // Page is hidden
        document.title = 'Come back to ' + (process.env.REACT_APP_SITE_NAME || 'Pavitra Trading');
      } else {
        // Page is visible
        document.title = process.env.REACT_APP_SITE_NAME || 'Pavitra Trading';
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  // Handle online/offline status
  useEffect(() => {
    const handleOnline = () => {
      console.log('App is online');
      // You can show a notification or update UI here
      const event = new CustomEvent('appOnline');
      document.dispatchEvent(event);
    };

    const handleOffline = () => {
      console.log('App is offline');
      // You can show a notification or update UI here
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

  // Error boundary fallback
  useEffect(() => {
    const handleError = (error) => {
      console.error('Application error:', error);
      // You can send this to an error reporting service
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
        <Router>
          <Layout>
            <Routes>
              <Route path="/" element={<HomePage />} />
              {/* You can add more routes here as needed */}
              {/* <Route path="/products" element={<ProductsPage />} /> */}
              {/* <Route path="/category/:id" element={<CategoryPage />} /> */}
              {/* <Route path="/product/:slug" element={<ProductDetailPage />} /> */}
              {/* <Route path="/cart" element={<CartPage />} /> */}
              {/* <Route path="/checkout" element={<CheckoutPage />} /> */}
              {/* <Route path="/account" element={<AccountPage />} /> */}
              <Route path="/auth" element={<AuthPage />} />
              <Route path="/login" element={<AuthPage />} />
              <Route path="/register" element={<AuthPage />} />
            </Routes>
          </Layout>
        </Router>
      </SettingsProvider>
    </AuthProvider>
  );
}

export default App;