import React from 'react';
import Hero from '../components/sections/Hero.js';
import PromoCards from '../components/sections/PromoCards.js';
import BestSellers from '../components/sections/BestSellers.js';
import ProductCards from '../components/sections/ProductCards.js';
import CallToAction from '../components/sections/CallToAction.js';

const HomePage = () => {
  return (
    <main className="main">
      <Hero />
      <PromoCards />
      <BestSellers />
      <ProductCards />
      <CallToAction />
    </main>
  );
};

export default HomePage;
