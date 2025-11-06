// frontend/src/App.js
import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext.js';
import { SettingsProvider } from './contexts/SettingsContext.js';
import { CartProvider } from './contexts/CartContext.js';
import { ToastProvider } from './contexts/ToastContext.js';
import Layout from './components/layout/Layout.js';
import HomePage from './pages/HomePage.js';
import AuthPage from './pages/AuthPage.js';
import CartPage from './pages/CartPage.js';
import { useSession } from './hooks/useSession';


function App() {
  useSession();

  useEffect(() => {
  const handleShowToast = (event) => {
    const { message, type = 'info' } = event.detail;

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast show align-items-center text-bg-${type} border-0`;
    toast.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 9999;
      min-width: 250px;
    `;

    toast.innerHTML = `
      <div class="d-flex">
        <div class="toast-body">
          ${message}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    `;

    document.body.appendChild(toast);

    // Auto remove after 5 seconds
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    }, 5000);

    // Add click to dismiss
    toast.querySelector('.btn-close').addEventListener('click', () => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    });
  };

  document.addEventListener('showToast', handleShowToast);

  return () => {
    document.removeEventListener('showToast', handleShowToast);
    clearTimeout(timer);
  };
}, []);

  return (
    <Router>
      <ToastProvider>
        <AuthProvider>
          <SettingsProvider>
            <CartProvider>
              <Layout>
                <Routes>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/cart" element={<CartPage />} />
                  <Route path="/auth" element={<AuthPage />} />
                  <Route path="/login" element={<AuthPage />} />
                  <Route path="/register" element={<AuthPage />} />
                </Routes>
              </Layout>
            </CartProvider>
          </SettingsProvider>
        </AuthProvider>
      </ToastProvider>
    </Router>
  );
}

export default App;