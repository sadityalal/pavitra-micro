import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { productService } from '../services/productService';

const ProductDetails = () => {
  const { id } = useParams();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await productService.getProduct(id);
        setProduct(res || null);
      } catch (e) {
        console.error('Failed to load product', e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id]);

  if (loading) return <div className="container py-5 text-center">Loading product...</div>;
  if (!product) return <div className="container py-5 text-center">Product not found</div>;

  return (
    <div className="container py-4">
      <div className="row">
        <div className="col-md-6">
          <img src={product.main_image_url || '/static/img/product/placeholder.jpg'} alt={product.name} className="img-fluid" />
        </div>
        <div className="col-md-6">
          <h2>{product.name}</h2>
          <p className="lead">{product.short_description}</p>
          <h3>{product.currency_symbol || '₹'}{product.base_price}</h3>
          <div dangerouslySetInnerHTML={{ __html: product.description || '' }} />
        </div>
      </div>
    </div>
  );
};

export default ProductDetails;
