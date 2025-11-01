// frontend/src/hooks/useCategories.js
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
      setCategories([]);
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