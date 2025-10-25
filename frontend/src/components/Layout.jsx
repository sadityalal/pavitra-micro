import { Outlet } from 'react-router-dom';

const Layout = () => {
  return (
    <div>
      {/* Simple header for now */}
      <header className="bg-primary text-white p-3">
        <div className="container">
          <h1>Pavitra Trading</h1>
          <nav>
            <a href="/" className="text-white me-3">Home</a>
            <a href="/products" className="text-white me-3">Products</a>
            <a href="/cart" className="text-white">Cart</a>
          </nav>
        </div>
      </header>

      <main>
        <Outlet />  {/* This renders the page content */}
      </main>

      {/* Simple footer for now */}
      <footer className="bg-dark text-white p-4 text-center">
        <p>&copy; 2024 Pavitra Trading</p>
      </footer>
    </div>
  );
};

export default Layout;