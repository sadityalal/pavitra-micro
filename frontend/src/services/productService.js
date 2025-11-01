// frontend/src/services/productService.js
import { productApi, authApi } from './api';
import { getProductImageUrl } from '../utils/helpers';

export const productService = {
  getFeaturedProducts: async () => {
    try {
      // Replace with actual endpoint when available
      // const response = await productApi.get('/api/v1/products/featured');
      // return processProductImages(response.data);
      
      // Temporary mock data - remove when backend is ready
      return getMockProducts();
    } catch (error) {
      console.error('Error fetching featured products:', error);
      return getMockProducts();
    }
  },

  getBestSellers: async () => {
    try {
      // Replace with actual endpoint when available
      // const response = await productApi.get('/api/v1/products/best-sellers');
      // return processProductImages(response.data);
      
      return getMockProducts();
    } catch (error) {
      console.error('Error fetching best sellers:', error);
      return getMockProducts();
    }
  },

  getProductById: async (productId) => {
    try {
      // const response = await productApi.get(`/api/v1/products/${productId}`);
      // return processProductImages(response.data);
      
      const mockProducts = getMockProducts();
      return mockProducts.find(p => p.id === productId) || mockProducts[0];
    } catch (error) {
      console.error('Error fetching product:', error);
      return getMockProducts()[0];
    }
  }
};

// Temporary mock data - remove when backend is ready
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
  },
  {
    id: 2,
    name: "Smart Fitness Watch",
    slug: "smart-fitness-watch",
    short_description: "Track your fitness with this advanced smartwatch",
    base_price: 5999,
    sale_price: null,
    main_image_url: "/assets/img/product/product-2.webp",
    stock_status: "in_stock",
    stock_quantity: 8,
    rating: 4.8,
    review_count: 38,
    discount_percentage: 0
  },
  {
    id: 3,
    name: "Premium Leather Bag",
    slug: "premium-leather-bag",
    short_description: "Genuine leather bag for professionals",
    base_price: 4599,
    sale_price: 3599,
    main_image_url: "/assets/img/product/product-3.webp",
    stock_status: "in_stock",
    stock_quantity: 5,
    rating: 4.3,
    review_count: 12,
    discount_percentage: 22
  },
  {
    id: 4,
    name: "Wireless Earbuds",
    slug: "wireless-earbuds",
    short_description: "Compact wireless earbuds with charging case",
    base_price: 2499,
    sale_price: 1999,
    main_image_url: "/assets/img/product/product-4.webp",
    stock_status: "out_of_stock",
    stock_quantity: 0,
    rating: 4.6,
    review_count: 56,
    discount_percentage: 20
  }
];