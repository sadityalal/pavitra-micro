export const productService = {
  async getFeaturedProducts(limit = 8) {
    try {
      const response = await fetch(`http://localhost:8002/api/v1/products/featured-products?page_size=${limit}`);
      if (!response.ok) throw new Error('Failed to fetch featured products');
      return await response.json();
    } catch (error) {
      console.error('Error fetching featured products:', error);
      return { products: [] };
    }
  },

  async getNewArrivals(limit = 8) {
    try {
      const response = await fetch(`http://localhost:8002/api/v1/products/new-arrivals?page_size=${limit}`);
      if (!response.ok) throw new Error('Failed to fetch new arrivals');
      return await response.json();
    } catch (error) {
      console.error('Error fetching new arrivals:', error);
      return { products: [] };
    }
  },

  async getBestsellers(limit = 8) {
    try {
      const response = await fetch(`http://localhost:8002/api/v1/products/bestseller-products?page_size=${limit}`);
      if (!response.ok) throw new Error('Failed to fetch bestsellers');
      return await response.json();
    } catch (error) {
      console.error('Error fetching bestsellers:', error);
      return { products: [] };
    }
  },

  async getCategories() {
    try {
      const response = await fetch('http://localhost:8002/api/v1/products/categories');
      if (!response.ok) throw new Error('Failed to fetch categories');
      return await response.json();
    } catch (error) {
      console.error('Error fetching categories:', error);
      return [];
    }
  }
};