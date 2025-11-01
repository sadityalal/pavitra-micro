import { productApi, authApi } from './api';
import { getProductImageUrl } from '../utils/helpers';

export const productService = {
  // Get featured products
  getFeaturedProducts: async () => {
    const response = await productApi.get('/api/v1/products/featured');
    return processProductImages(response.data);
  },

  // Get best sellers
  getBestSellers: async () => {
    const response = await productApi.get('/api/v1/products/best-sellers');
    return processProductImages(response.data);
  },

  // Get products by category
  getProductsByCategory: async (categoryId) => {
    const response = await productApi.get(`/api/v1/products/category/${categoryId}`);
    return processProductImages(response.data);
  },

  // Get product details
  getProductById: async (productId) => {
    const response = await productApi.get(`/api/v1/products/${productId}`);
    return processProductImages(response.data);
  },

  // Search products
  searchProducts: async (query) => {
    const response = await productApi.get(`/api/v1/products/search?q=${query}`);
    return processProductImages(response.data);
  },

  // Get frontend settings from auth service
  getFrontendSettings: async () => {
    const response = await authApi.get('/api/v1/auth/frontend-settings');
    return response.data;
  },

  // Get categories
  getCategories: async () => {
    const response = await productApi.get('/api/v1/products/categories');
    return response.data;
  }
};

// Process product images based on your database structure
const processProductImages = (data) => {
  if (Array.isArray(data)) {
    return data.map(product => ({
      ...product,
      // Handle main_image_url
      main_image_url: getProductImageUrl(product.main_image_url),
      // Handle images array (JSON array in database)
      images: Array.isArray(product.images) 
        ? product.images.map(img => getProductImageUrl(img))
        : [getProductImageUrl(product.main_image_url)],
      // Calculate discount percentage
      discount_percentage: calculateDiscountPercentage(product.base_price, product.sale_price),
      // Format prices
      formatted_base_price: formatCurrency(product.base_price),
      formatted_sale_price: formatCurrency(product.sale_price)
    }));
  }
  
  if (data && typeof data === 'object') {
    return {
      ...data,
      main_image_url: getProductImageUrl(data.main_image_url),
      images: Array.isArray(data.images) 
        ? data.images.map(img => getProductImageUrl(img))
        : [getProductImageUrl(data.main_image_url)],
      discount_percentage: calculateDiscountPercentage(data.base_price, data.sale_price),
      formatted_base_price: formatCurrency(data.base_price),
      formatted_sale_price: formatCurrency(data.sale_price)
    };
  }
  
  return data;
};

// Calculate discount percentage
const calculateDiscountPercentage = (basePrice, salePrice) => {
  if (!basePrice || !salePrice || basePrice <= salePrice) return 0;
  return Math.round(((basePrice - salePrice) / basePrice) * 100);
};

// Simple currency formatting (will be enhanced with settings)
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
  }).format(amount);
};
