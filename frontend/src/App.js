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
    const initializeScripts = () => {
      // Your existing script initialization code
      console.log('All scripts initialized successfully');
    };

    const timer = setTimeout(initializeScripts, 500);

    return () => {
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