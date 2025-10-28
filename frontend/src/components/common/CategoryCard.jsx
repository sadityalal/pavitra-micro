import React from 'react';
import { Link } from 'react-router-dom';
import { getCategoryImageUrl } from '../../utils/imageHelper';

const CategoryCard = ({ category }) => {
  const categoryImageUrl = getCategoryImageUrl(category.image_url);

  return (
    <div className="category-card">
      <Link to={`/categories/${category.slug || category.id}`} className="category-image-link">
        <img
          src={categoryImageUrl}
          alt={category.name}
          className="img-fluid"
          onError={(e) => e.currentTarget.src = '/static/img/categories/placeholder.jpg'}
        />
      </Link>
      <div className="category-content">
        <h4><Link to={`/categories/${category.slug || category.id}`}>{category.name}</Link></h4>
        <p>{category.product_count || 0} products</p>
      </div>
    </div>
  );
};

export default CategoryCard;