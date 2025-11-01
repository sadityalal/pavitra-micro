import { productApi, authApi } from './api';
import { getProductImageUrl } from '../utils/helpers';

export const productService = {
  getFeaturedProducts: async () => {
    try {
      const response = await productApi.get('/api/v1/products/featured?page_size=12');
      return response.data.products || [];
    } catch (error) {
      console.error('Error fetching featured products:', error);
      return getMockProducts();
    }
  },

  getBestSellers: async () => {
    try {
      const response = await productApi.get('/api/v1/products/bestsellers?page_size=12');
      return response.data.products || [];
    } catch (error) {
      console.error('Error fetching best sellers:', error);
      return getMockProducts();
    }
  },

  getNewArrivals: async () => {
    try {
      const response = await productApi.get('/api/v1/products/new-arrivals?page_size=12');
      return response.data.products || [];
    } catch (error) {
      console.error('Error fetching new arrivals:', error);
      return getMockProducts();
    }
  },

  getProductById: async (productId) => {
    try {
      const response = await productApi.get(`/api/v1/products/${productId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching product:', error);
      return getMockProducts()[0];
    }
  },

  getProductBySlug: async (productSlug) => {
    try {
      const response = await productApi.get(`/api/v1/products/slug/${productSlug}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching product by slug:', error);
      return getMockProducts()[0];
    }
  },

  getProducts: async (params = {}) => {
    try {
      const response = await productApi.get('/api/v1/products/', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching products:', error);
      return { products: getMockProducts(), total_count: 0, page: 1, page_size: 20 };
    }
  },

  getCategories: async () => {
    try {
      const response = await productApi.get('/api/v1/products/categories/all');
      return response.data;
    } catch (error) {
      console.error('Error fetching categories:', error);
      return [];
    }
  },

  getCategoryBySlug: async (categorySlug) => {
    try {
      const response = await productApi.get(`/api/v1/products/categories/slug/${categorySlug}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching category:', error);
      return null;
    }
  },

  searchProducts: async (query, filters = {}) => {
    try {
      const params = { search: query, ...filters };
      const response = await productApi.get('/api/v1/products/', { params });
      return response.data;
    } catch (error) {
      console.error('Error searching products:', error);
      return { products: [], total_count: 0 };
    }
  }
};

// Fallback mock data (keep as backup)
const getMockProducts = () => [
  {
    id: 1,
    name: "Wireless Bluetooth Headphones",
    slug: "wireless-bluetooth-headphones",
    short_description: "High-quality wireless headphones with noise cancellation",
    base_price: 2999,
    sale_price: 1999,
    main_image_url: "/assets/img/product/product-1.webp",
    stock_status: "in_stock",
    stock_quantity: 15,
    rating: 4.5,
    review_count: 24,
    discount_percentage: 33
  }
];