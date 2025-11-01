import { productApi, authApi } from './api';
import { getProductImageUrl } from '../utils/helpers';

export const productService = {
  getFeaturedProducts: async () => {
    try {
      console.log('📦 Fetching featured products...');
      const response = await productApi.get('/api/v1/products/featured?page_size=12');
      console.log('📦 Featured products response received');
      return response.data.products || [];
    } catch (error) {
      console.error('❌ Error fetching featured products:', error);
      
      // Don't return mock data for session/auth issues
      if (error.response?.status === 401 || error.response?.status === 403) {
        throw new Error('Session issue. Please refresh the page.');
      }
      
      if (error.response?.status === 503) {
        throw new Error('Service temporarily unavailable. Please try again later.');
      }
      
      // Only return mock data for network errors, not for session issues
      if (!error.response) {
        console.log('🌐 Network error, returning mock data');
        return getMockProducts();
      }
      
      throw error;
    }
  },

  getBestSellers: async () => {
    try {
      console.log('📦 Fetching best sellers...');
      const response = await productApi.get('/api/v1/products/bestsellers?page_size=12');
      console.log('📦 Best sellers response received');
      return response.data.products || [];
    } catch (error) {
      console.error('❌ Error fetching best sellers:', error);
      
      if (error.response?.status === 401 || error.response?.status === 403) {
        throw new Error('Session issue. Please refresh the page.');
      }
      
      if (error.response?.status === 503) {
        throw new Error('Service temporarily unavailable. Please try again later.');
      }
      
      if (!error.response) {
        console.log('🌐 Network error, returning mock data');
        return getMockProducts();
      }
      
      throw error;
    }
  },

  getNewArrivals: async () => {
    try {
      console.log('📦 Fetching new arrivals...');
      const response = await productApi.get('/api/v1/products/new-arrivals?page_size=12');
      console.log('📦 New arrivals response received');
      return response.data.products || [];
    } catch (error) {
      console.error('❌ Error fetching new arrivals:', error);
      
      if (error.response?.status === 401 || error.response?.status === 403) {
        throw new Error('Session issue. Please refresh the page.');
      }
      
      if (error.response?.status === 503) {
        throw new Error('Service temporarily unavailable. Please try again later.');
      }
      
      if (!error.response) {
        console.log('🌐 Network error, returning mock data');
        return getMockProducts();
      }
      
      throw error;
    }
  },

  getProductById: async (productId) => {
    try {
      console.log(`📦 Fetching product by ID: ${productId}`);
      const response = await productApi.get(`/api/v1/products/${productId}`);
      console.log('📦 Product by ID response received');
      return response.data;
    } catch (error) {
      console.error('❌ Error fetching product:', error);
      
      if (error.response?.status === 404) {
        throw new Error('Product not found.');
      }
      
      if (error.response?.status === 401 || error.response?.status === 403) {
        throw new Error('Session issue. Please refresh the page.');
      }
      
      throw error;
    }
  },

  getProductBySlug: async (productSlug) => {
    try {
      console.log(`📦 Fetching product by slug: ${productSlug}`);
      const response = await productApi.get(`/api/v1/products/slug/${productSlug}`);
      console.log('📦 Product by slug response received');
      return response.data;
    } catch (error) {
      console.error('❌ Error fetching product by slug:', error);
      
      if (error.response?.status === 404) {
        throw new Error('Product not found.');
      }
      
      if (error.response?.status === 401 || error.response?.status === 403) {
        throw new Error('Session issue. Please refresh the page.');
      }
      
      throw error;
    }
  },

  getProducts: async (params = {}) => {
    try {
      console.log('📦 Fetching products with params:', params);
      const response = await productApi.get('/api/v1/products/', { params });
      console.log('📦 Products response received');
      return response.data;
    } catch (error) {
      console.error('❌ Error fetching products:', error);
      
      if (error.response?.status === 401 || error.response?.status === 403) {
        throw new Error('Session issue. Please refresh the page.');
      }
      
      if (error.response?.status === 503) {
        throw new Error('Service temporarily unavailable. Please try again later.');
      }
      
      throw error;
    }
  },

  getCategories: async () => {
    try {
      console.log('📦 Fetching categories...');
      const response = await productApi.get('/api/v1/products/categories/all');
      console.log('📦 Categories response received');
      return response.data;
    } catch (error) {
      console.error('❌ Error fetching categories:', error);
      
      if (error.response?.status === 401 || error.response?.status === 403) {
        throw new Error('Session issue. Please refresh the page.');
      }
      
      // Return empty array instead of throwing for categories to prevent UI breakage
      if (error.response?.status === 503 || !error.response) {
        console.log('🌐 Network error, returning empty categories');
        return [];
      }
      
      throw error;
    }
  },

  getCategoryBySlug: async (categorySlug) => {
    try {
      console.log(`📦 Fetching category by slug: ${categorySlug}`);
      const response = await productApi.get(`/api/v1/products/categories/slug/${categorySlug}`);
      console.log('📦 Category by slug response received');
      return response.data;
    } catch (error) {
      console.error('❌ Error fetching category:', error);
      
      if (error.response?.status === 404) {
        throw new Error('Category not found.');
      }
      
      if (error.response?.status === 401 || error.response?.status === 403) {
        throw new Error('Session issue. Please refresh the page.');
      }
      
      throw error;
    }
  },

  searchProducts: async (query, filters = {}) => {
    try {
      console.log(`📦 Searching products: ${query}`, filters);
      const params = { search: query, ...filters };
      const response = await productApi.get('/api/v1/products/', { params });
      console.log('📦 Search response received');
      return response.data;
    } catch (error) {
      console.error('❌ Error searching products:', error);
      
      if (error.response?.status === 401 || error.response?.status === 403) {
        throw new Error('Session issue. Please refresh the page.');
      }
      
      if (error.response?.status === 503) {
        throw new Error('Service temporarily unavailable. Please try again later.');
      }
      
      // Return empty results for search errors
      return { products: [], total_count: 0 };
    }
  },

  // Helper method to initialize session for guest users
  initializeGuestSession: async () => {
    try {
      console.log('🔄 ProductService: Initializing guest session...');
      const response = await productApi.get('/api/v1/products/featured?page_size=1');
      console.log('✅ ProductService: Guest session initialized');
      return response.data;
    } catch (error) {
      console.error('❌ ProductService: Failed to initialize guest session:', error);
      throw error;
    }
  }
};

// Mock data fallback (only for network errors, not session issues)
const getMockProducts = () => [
  {
    id: 1,
    name: "Wireless Bluetooth Headphones",
    slug: "wireless-bluetooth-headphones",
    short_description: "High-quality wireless headphones with noise cancellation",
    base_price: 2999,
    compare_price: 3999,
    main_image_url: "/assets/img/product/product-1.webp",
    stock_status: "in_stock",
    stock_quantity: 15,
    is_featured: true,
    is_bestseller: true,
    rating: 4.5,
    review_count: 24
  },
  {
    id: 2,
    name: "Smart Fitness Tracker",
    slug: "smart-fitness-tracker",
    short_description: "Track your fitness goals with this advanced smart watch",
    base_price: 1999,
    compare_price: 2499,
    main_image_url: "/assets/img/product/product-2.webp",
    stock_status: "in_stock",
    stock_quantity: 8,
    is_featured: true,
    is_trending: true,
    rating: 4.2,
    review_count: 18
  },
  {
    id: 3,
    name: "Laptop Backpack",
    slug: "laptop-backpack",
    short_description: "Durable and stylish backpack for your laptop",
    base_price: 1299,
    compare_price: null,
    main_image_url: "/assets/img/product/product-3.webp",
    stock_status: "in_stock",
    stock_quantity: 25,
    is_bestseller: true,
    rating: 4.7,
    review_count: 32
  }
];