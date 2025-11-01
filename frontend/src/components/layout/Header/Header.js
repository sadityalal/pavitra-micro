import React from 'react';
import TopBar from './TopBar.js';
import MainHeader from './MainHeader.js';
import Navigation from './Navigation.js';

const Header = () => {
  return (
    <header id="header" className="header sticky-top">
      <TopBar />
      <MainHeader />
      <Navigation />
    </header>
  );
};

export default Header;
