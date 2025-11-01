import { useState, useEffect } from 'react';
import { productService } from '../services/productService';

export const useCategories = () => {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchCategories = async () => {
    try {
      setLoading(true);
      setError(null);
      const categoriesData = await productService.getCategories();
      setCategories(categoriesData);
    } catch (err) {
      console.error('Failed to fetch categories:', err);
      setError(err.message);
      setCategories(getMockCategories());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, []);

  return {
    categories,
    loading,
    error,
    refetch: fetchCategories
  };
};

// Fallback mock categories
const getMockCategories = () => [
  {
    id: 1,
    name: 'Electronics',
    slug: 'electronics',
    description: 'Latest electronic gadgets and devices',
    image_url: '/assets/img/categories/electronics.jpg'
  },
  {
    id: 2,
    name: 'Clothing',
    slug: 'clothing',
    description: 'Fashionable clothing for all',
    image_url: '/assets/img/categories/clothing.jpg'
  }
];