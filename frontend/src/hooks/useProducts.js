import { useState, useEffect } from 'react';
import { productService } from '../services/productService';

export const useProducts = (type = 'featured', options = {}) => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: 12,
    totalCount: 0,
    totalPages: 0
  });

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
        case 'new-arrivals':
          data = await productService.getNewArrivals();
          break;
        case 'category':
          data = await productService.getProducts({
            category_slug: options.categorySlug,
            page: options.page || 1,
            page_size: options.pageSize || 12
          });
          break;
        case 'search':
          data = await productService.searchProducts(options.query, options.filters);
          break;
        case 'all':
          data = await productService.getProducts(options);
          break;
        default:
          data = await productService.getFeaturedProducts();
      }

      // Handle both array and paginated response
      if (Array.isArray(data)) {
        setProducts(data);
        setPagination(prev => ({
          ...prev,
          totalCount: data.length
        }));
      } else if (data && data.products) {
        setProducts(data.products);
        setPagination({
          page: data.page || 1,
          pageSize: data.page_size || 12,
          totalCount: data.total_count || 0,
          totalPages: data.total_pages || 0
        });
      } else {
        setProducts([]);
      }
    } catch (err) {
      console.error('Error fetching products:', err);
      setError(err.message);
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, [type, options.categorySlug, options.query, options.page, options.pageSize]);

  return {
    products,
    loading,
    error,
    pagination,
    refetch: fetchProducts
  };
};