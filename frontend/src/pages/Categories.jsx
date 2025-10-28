import React, { useEffect, useState } from 'react';
import { productService } from '../services/productService';
import CategoryCard from '../components/common/CategoryCard';

const Categories = () => {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadCategories = async () => {
      setLoading(true);
      setError('');
      try {
        console.log('Loading categories...');
        const categoriesData = await productService.getCategories();
        console.log('Raw categories response:', categoriesData);

        // Handle different response structures
        let categoriesList = [];
        if (Array.isArray(categoriesData)) {
          categoriesList = categoriesData;
        } else if (categoriesData && categoriesData.categories) {
          categoriesList = categoriesData.categories;
        } else if (categoriesData && Array.isArray(categoriesData.data)) {
          categoriesList = categoriesData.data;
        }

        console.log('Processed categories:', categoriesList);
        setCategories(categoriesList);

        if (categoriesList.length === 0) {
          setError('No categories found in the database.');
        }
      } catch (err) {
        console.error('Failed to load categories:', err);
        setError('Failed to load categories. Please check if the product service is running.');
        setCategories([]);
      } finally {
        setLoading(false);
      }
    };

    loadCategories();
  }, []);

  if (loading) {
    return (
      <div className="container py-5">
        <div className="text-center">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="mt-3">Loading categories...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container py-5">
        <div className="alert alert-danger" role="alert">
          <h4 className="alert-heading">Unable to Load Categories</h4>
          <p>{error}</p>
          <hr />
          <p className="mb-0">
            Please check your internet connection and try again.
            If the problem persists, contact support.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="container py-5">
      <div className="row">
        <div className="col-12">
          <div className="page-header mb-4">
            <h1>Product Categories</h1>
            <p className="lead">Browse our wide range of product categories</p>
          </div>
        </div>
      </div>

      {categories.length === 0 ? (
        <div className="text-center py-5">
          <div className="alert alert-warning">
            <h4>No Categories Available</h4>
            <p>There are no product categories available at the moment.</p>
          </div>
        </div>
      ) : (
        <div className="row">
          {categories.map((category) => (
            <div className="col-xl-3 col-lg-4 col-md-6 mb-4" key={category.id}>
              <CategoryCard category={category} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Categories;