// frontend/src/hooks/useProducts.js
import { useState, useEffect } from 'react';
import { productService } from '../services/productService';

export const useProducts = (type = 'featured', options = {}) => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchProducts = async () => {
    try {
      setLoading(true);
      setError(null);

      let data;
      switch (type) {
        case 'featured':
          data = await productService.getFeaturedProducts();
          break;
        case 'best-sellers':
          data = await productService.getBestSellers();
          break;
        case 'category':
          data = await productService.getProductsByCategory(options.categoryId);
          break;
        case 'search':
          data = await productService.searchProducts(options.query);
          break;
        default:
          data = await productService.getFeaturedProducts();
      }

      setProducts(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error fetching products:', err);
      setError(err.message);
      // Fallback to empty array instead of mock data
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, [type, options.categoryId, options.query]);

  return { products, loading, error, refetch: fetchProducts };
};