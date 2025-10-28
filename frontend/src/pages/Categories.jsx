import React, { useEffect, useState } from 'react';
import { productService } from '../services/productService';
import CategoryCard from '../components/common/CategoryCard';

const Categories = () => {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await productService.getCategories();
        setCategories(res || []);
      } catch (e) {
        console.error('Failed to load categories', e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return <div className="container py-5 text-center">Loading categories...</div>;

  return (
    <div className="container py-4">
      <h2>Categories</h2>
      <div className="row">
        {categories.map((c) => (
          <div className="col-md-4 mb-4" key={c.id}>
            <CategoryCard category={c} />
          </div>
        ))}
      </div>
    </div>
  );
};

export default Categories;
