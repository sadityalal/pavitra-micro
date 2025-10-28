import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { productService } from '../services/productService';
import ProductCard from '../components/common/ProductCard';

const CategoryDetail = () => {
  const { id } = useParams();
  const [category, setCategory] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        // productService does not provide getCategory by id; fetch all categories and find
        const res = await productService.getCategories();
        const cats = Array.isArray(res) ? res : (res.categories || []);
        const found = cats.find(c => String(c.slug) === String(id) || String(c.id) === String(id));
        if (found) {
          // ensure products are present; if not, fetch products for this category
          if (!found.products || !found.products.length) {
            const productsResp = await productService.getProducts({ category_id: found.id, limit: 24 });
            found.products = productsResp.products || [];
          }
        }
        setCategory(found || null);
      } catch (e) {
        console.error('Failed to load category', e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id]);

  if (loading) return <div className="container py-5 text-center">Loading category...</div>;
  if (!category) return <div className="container py-5 text-center">Category not found</div>;

  return (
    <div className="container py-4">
      <h2>{category.name}</h2>
      <p>{category.description}</p>
      <div className="row">
        {category.products?.map(p => (
          <div className="col-md-3 mb-4" key={p.id}>
            <ProductCard product={p} />
          </div>
        ))}
      </div>
    </div>
  );
};

export default CategoryDetail;
