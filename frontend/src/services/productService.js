// frontend/src/services/productService.js
import { productApi } from './api';

class ProductService {
  async getProducts(params = {}) {
    try {
      const queryString = new URLSearchParams(params).toString();
      // Ensure trailing slash to match backend route registration (/api/v1/products/)
      const base = `/api/v1/products/`;
      const endpoint = `${base}${queryString ? `?${queryString}` : ''}`;
      try {
        return await productApi.get(endpoint);
      } catch (err) {
        // Some deployments may accept the path without trailing slash; retry without or with depending on error
        const msg = (err && err.message) ? err.message : String(err);
        if (msg.includes('Method Not Allowed') || msg.includes('405')) {
          const alt = `/api/v1/products${queryString ? `?${queryString}` : ''}`;
          return await productApi.get(alt);
        }
        throw err;
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
        bestsellers: true, 
        limit, 
        status: 'active' 
      });
    } catch (error) {
      console.error('Failed to fetch best sellers:', error);
      return { products: [], total: 0 };
    }
  }

  async getProduct(slug) {
    try {
      return await productApi.get(`/api/v1/products/slug/${slug}`);
    } catch (error) {
      console.error('Failed to fetch product:', error);
      return null;
    }
  }

  async getCategories() {
    try {
      return await productApi.get('/api/v1/products/categories/all');
    } catch (error) {
      console.error('Failed to fetch categories:', error);
      return { categories: [] };
    }
  }

  async searchProducts(query, params = {}) {
    try {
      const searchParams = { q: query, ...params };
      const queryString = new URLSearchParams(searchParams).toString();
      return await productApi.get(`/api/v1/products/search?${queryString}`);
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