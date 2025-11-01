import { useState, useEffect } from 'react';
import { productService } from '../services/productService';

export const useProducts = (type = 'featured') => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        setLoading(true);
        let data;
        
        switch (type) {
          case 'featured':
            data = await productService.getFeaturedProducts();
            break;
          case 'best-sellers':
            data = await productService.getBestSellers();
            break;
          default:
            data = await productService.getFeaturedProducts();
        }
        
        setProducts(data);
      } catch (err) {
        setError(err.message);
        // Fallback to mock data if API fails
        setProducts(getMockProducts());
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, [type]);

  return { products, loading, error };
};

// Mock data fallback
const getMockProducts = () => [
  {
    id: 1,
    name: 'Premium Headphones',
    price: 129.99,
    image: 'product-1.webp',
    rating: 4.5,
    reviewCount: 24,
    currency: 'INR',
    currency_symbol: '₹'
  },
  {
    id: 2,
    name: 'Smart Watch',
    price: 199.99,
    image: 'product-2.webp',
    rating: 4.8,
    reviewCount: 38,
    currency: 'INR',
    currency_symbol: '₹'
  }
];
