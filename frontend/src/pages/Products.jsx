import React, { useEffect, useState } from 'react';
import { productService } from '../services/productService';
import ProductCard from '../components/common/ProductCard';

const Products = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await productService.getProducts({ limit: 24 });
        setProducts(res.products || []);
      } catch (e) {
        console.error('Failed to load products', e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleAddToCart = (product) => {
    console.log('Add to cart', product.id);
  };

  const handleAddToWishlist = (id) => {
    console.log('Add to wishlist', id);
  };

  if (loading) return <div className="container py-5 text-center">Loading products...</div>;

  return (
    <div className="container py-4">
      <h2>Products</h2>
      <div className="row">
        {products.map((p) => (
          <div className="col-md-3 mb-4" key={p.id}>
            <ProductCard product={p} onAddToCart={handleAddToCart} onAddToWishlist={handleAddToWishlist} />
          </div>
        ))}
      </div>
    </div>
  );
};

export default Products;