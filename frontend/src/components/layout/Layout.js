import React from 'react';
import Header from './Header';
import Footer from './Footer';

const Layout = ({ children }) => {
  return (
    <div className="App">
      <Header />
      <main className="main">
        {/* Flash Messages - we'll implement this later */}
        <div className="container mt-3" id="flash-messages"></div>
        {children}
      </main>
      <Footer />
    </div>
  );
};

export default Layout;
