// frontend/src/hooks/useSession.js
import { useEffect } from 'react';
import { productService } from '../services/productService';

export const useSession = () => {
  useEffect(() => {
    // Make an initial API call to ensure session is created
    const initializeSession = async () => {
      try {
        // This will trigger the product service to create a session cookie
        await productService.getFeaturedProducts();
        console.log('✅ Session initialized for guest user');
      } catch (error) {
        console.error('❌ Failed to initialize session:', error);
      }
    };

    // Only initialize if no auth token (guest user)
    if (!localStorage.getItem('auth_token')) {
      initializeSession();
    }
  }, []);
};