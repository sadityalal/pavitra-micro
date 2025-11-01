import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext.js';
import { SettingsProvider } from './contexts/SettingsContext.js';
import Layout from './components/layout/Layout.js';
import HomePage from './pages/HomePage.js';

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
      }

      // Call any existing initialization functions from your main.js
      if (typeof initSwiper === 'function') {
        initSwiper();
      }
      if (typeof AOS !== 'undefined' && typeof AOS.init === 'function') {
        AOS.init();
      }
    };

    // Initialize after a short delay to ensure DOM is ready
    const timer = setTimeout(initializeScripts, 500);

    return () => clearTimeout(timer);
  }, []);

  return (
    <AuthProvider>
      <SettingsProvider>
        <Router>
          <Layout>
            <Routes>
              <Route path="/" element={<HomePage />} />
            </Routes>
          </Layout>
        </Router>
      </SettingsProvider>
    </AuthProvider>
  );
}

export default App;
