// frontend/src/pages/Home.js
import React, { useState, useEffect } from 'react';
import { productService } from '../services/productService';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import Hero from '../components/home/Hero';
import PromoCards from '../components/home/PromoCards';
import BestSellers from '../components/home/BestSellers';
import Features from '../components/home/Features';
import CTA from '../components/home/CTA';

const Home = () => {
  const [featuredProducts, setFeaturedProducts] = useState([]);
  const [newArrivals, setNewArrivals] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const { siteSettings, isAuthenticated } = useAuth();
  const { addToCart, totalItems } = useCart();

  useEffect(() => {
    loadHomeData();
  }, []);

  const loadHomeData = async () => {
    try {
      setLoading(true);
      const [featuredResponse, newArrivalsResponse, categoriesResponse] = await Promise.all([
        productService.getProducts({ featured: true, limit: 8 }),
        productService.getProducts({ new_arrivals: true, limit: 6 }),
        productService.getCategories()
      ]);

      setFeaturedProducts(featuredResponse.products || []);
      setNewArrivals(newArrivalsResponse.products || []);
      setCategories(categoriesResponse || []);
    } catch (error) {
      console.error('Failed to load home page data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = async (product) => {
    try {
      await addToCart(product.id, 1, product);
    } catch (error) {
      console.error('Failed to add product to cart:', error);
    }
  };

  const handleAddToWishlist = async (productId) => {
    if (!isAuthenticated) {
      alert('Please login to add items to wishlist');
      return;
    }
    console.log('Add to wishlist:', productId);
  };

  if (loading) {
    return (
      <div className="container py-5 text-center">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
        <p className="mt-3">Loading amazing products...</p>
      </div>
    );
  }

  return (
    <div className="home-page">
      <Hero featuredProducts={featuredProducts} totalItems={totalItems} siteSettings={siteSettings} isAuthenticated={isAuthenticated} />
      <PromoCards categories={categories} />
      <BestSellers featuredProducts={featuredProducts} siteSettings={siteSettings} onAddToCart={handleAddToCart} onAddToWishlist={handleAddToWishlist} totalItems={totalItems} />
      <Features siteSettings={siteSettings} />
      <CTA />
    </div>
  );
};

export default Home;