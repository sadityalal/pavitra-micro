// frontend/src/services/productService.js
import { productApi } from './api';

class ProductService {
  async getProducts(params = {}) {
    try {
      const queryString = new URLSearchParams(params).toString();
      const endpoint = `/api/v1/products/${queryString ? `?${queryString}` : ''}`;
      const response = await productApi.get(endpoint);

      // Handle different response structures
      if (response.products !== undefined) {
        return response;
      } else if (Array.isArray(response)) {
        return { products: response, total: response.length };
      } else {
        return { products: [], total: 0 };
      }
    } catch (error) {
      console.error('Failed to fetch products:', error);
      return { products: [], total: 0 };
    }
  }

  async getFeaturedProducts(limit = 8) {
    try {
      return await this.getProducts({
        featured: true,
        limit,
        status: 'active'
      });
    } catch (error) {
      console.error('Failed to fetch featured products:', error);
      return { products: [], total: 0 };
    }
  }

  async getNewArrivals(limit = 6) {
    try {
      return await this.getProducts({
        new_arrivals: true,
        limit,
        status: 'active'
      });
    } catch (error) {
      console.error('Failed to fetch new arrivals:', error);
      return { products: [], total: 0 };
    }
  }

  async getBestSellers(limit = 8) {
    try {
      return await this.getProducts({
        bestseller: true,
        limit,
        status: 'active'
      });
    } catch (error) {
      console.error('Failed to fetch best sellers:', error);
      return { products: [], total: 0 };
    }
  }

  async getProduct(id) {
    try {
      // Try by ID first
      return await productApi.get(`/api/v1/products/${id}`);
    } catch (error) {
      console.error('Failed to fetch product by ID:', error);
      // If ID fails, try by slug
      try {
        return await productApi.get(`/api/v1/products/slug/${id}`);
      } catch (slugError) {
        console.error('Failed to fetch product by slug:', slugError);
        return null;
      }
    }
  }

  async getCategories() {
    try {
      const response = await productApi.get('/api/v1/products/categories/all');

      // Handle different response structures
      if (Array.isArray(response)) {
        return response;
      } else if (response.categories) {
        return response.categories;
      } else {
        return [];
      }
    } catch (error) {
      console.error('Failed to fetch categories:', error);
      return [];
    }
  }

  async getCategory(id) {
    try {
      return await productApi.get(`/api/v1/products/categories/${id}`);
    } catch (error) {
      console.error('Failed to fetch category:', error);
      return null;
    }
  }

  async getCategoryBySlug(slug) {
    try {
      return await productApi.get(`/api/v1/products/categories/slug/${slug}`);
    } catch (error) {
      console.error('Failed to fetch category by slug:', error);
      return null;
    }
  }

  async searchProducts(query, params = {}) {
    try {
      const searchParams = { q: query, ...params };
      return await this.getProducts(searchParams);
    } catch (error) {
      console.error('Search failed:', error);
      return { products: [], total: 0 };
    }
  }

  async getRelatedProducts(productId, limit = 4) {
    try {
      return await productApi.get(`/api/v1/products/${productId}/related?limit=${limit}`);
    } catch (error) {
      console.error('Failed to fetch related products:', error);
      return { products: [] };
    }
  }
}

export const productService = new ProductService();