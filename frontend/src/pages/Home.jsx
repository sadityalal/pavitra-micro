import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { productService } from '../services/products';
import { bannerService } from '../services/banners';

const Home = () => {
  const [featuredProducts, setFeaturedProducts] = useState([]);
  const [newArrivals, setNewArrivals] = useState([]);
  const [bestsellers, setBestsellers] = useState([]);
  const [banners, setBanners] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHomeData = async () => {
      try {
        const [
          featuredData,
          newArrivalsData,
          bestsellersData,
          bannersData,
          categoriesData
        ] = await Promise.all([
          productService.getFeaturedProducts(8),
          productService.getNewArrivals(8),
          productService.getBestsellers(8),
          bannerService.getHomeBanners(),
          productService.getCategories()
        ]);

        setFeaturedProducts(featuredData.products || []);
        setNewArrivals(newArrivalsData.products || []);
        setBestsellers(bestsellersData.products || []);
        setBanners(bannersData);
        setCategories(categoriesData);
      } catch (error) {
        console.error('Error fetching home data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchHomeData();
  }, []);

  if (loading) {
    return (
      <div className="container py-5 text-center">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Hero Banner */}
      <section className="hero-section">
        <div className="container-fluid px-0">
          <div className="hero-slider swiper">
            <div className="swiper-wrapper">
              {banners.map((banner, index) => (
                <div key={banner.id} className="swiper-slide">
                  <div
                    className="hero-banner"
                    style={{
                      backgroundImage: `url(${banner.image_url})`,
                      backgroundSize: 'cover',
                      backgroundPosition: 'center',
                      minHeight: '600px'
                    }}
                  >
                    <div className="container">
                      <div className="hero-content">
                        <h1 className="hero-title">{banner.title}</h1>
                        <p className="hero-description">{banner.description}</p>
                        {banner.target_url && (
                          <Link to={banner.target_url} className="btn btn-primary btn-lg">
                            Shop Now
                          </Link>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <div className="swiper-pagination"></div>
          </div>
        </div>
      </section>

      {/* Featured Categories */}
      <section className="categories-section py-5">
        <div className="container">
          <div className="section-header text-center mb-5">
            <h2 className="section-title">Shop by Category</h2>
            <p className="section-subtitle">Discover our wide range of products</p>
          </div>
          <div className="row g-4">
            {categories.slice(0, 6).map(category => (
              <div key={category.id} className="col-md-4 col-lg-2">
                <Link
                  to={`/category/${category.slug}`}
                  className="category-card text-decoration-none"
                >
                  <div className="card border-0 shadow-sm h-100">
                    <div className="card-body text-center">
                      {category.image_url && (
                        <img
                          src={category.image_url}
                          alt={category.name}
                          className="category-image mb-3"
                          style={{ width: '80px', height: '80px', objectFit: 'cover' }}
                        />
                      )}
                      <h6 className="category-name">{category.name}</h6>
                    </div>
                  </div>
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Products */}
      <section className="featured-products py-5 bg-light">
        <div className="container">
          <div className="section-header text-center mb-5">
            <h2 className="section-title">Featured Products</h2>
            <p className="section-subtitle">Handpicked items just for you</p>
          </div>
          <div className="row g-4">
            {featuredProducts.map(product => (
              <div key={product.id} className="col-sm-6 col-md-4 col-lg-3">
                <ProductCard product={product} />
              </div>
            ))}
          </div>
          <div className="text-center mt-4">
            <Link to="/products?featured=true" className="btn btn-outline-primary">
              View All Featured Products
            </Link>
          </div>
        </div>
      </section>

      {/* New Arrivals */}
      <section className="new-arrivals py-5">
        <div className="container">
          <div className="section-header text-center mb-5">
            <h2 className="section-title">New Arrivals</h2>
            <p className="section-subtitle">Fresh products just arrived</p>
          </div>
          <div className="row g-4">
            {newArrivals.map(product => (
              <div key={product.id} className="col-sm-6 col-md-4 col-lg-3">
                <ProductCard product={product} showNewBadge={true} />
              </div>
            ))}
          </div>
          <div className="text-center mt-4">
            <Link to="/products?new_arrivals=true" className="btn btn-outline-primary">
              View All New Arrivals
            </Link>
          </div>
        </div>
      </section>

      {/* Bestsellers */}
      <section className="bestsellers py-5 bg-light">
        <div className="container">
          <div className="section-header text-center mb-5">
            <h2 className="section-title">Bestsellers</h2>
            <p className="section-subtitle">Most loved by our customers</p>
          </div>
          <div className="row g-4">
            {bestsellers.map(product => (
              <div key={product.id} className="col-sm-6 col-md-4 col-lg-3">
                <ProductCard product={product} showBestsellerBadge={true} />
              </div>
            ))}
          </div>
          <div className="text-center mt-4">
            <Link to="/products?bestseller=true" className="btn btn-outline-primary">
              View All Bestsellers
            </Link>
          </div>
        </div>
      </section>
    </>
  );
};

// Product Card Component
const ProductCard = ({ product, showNewBadge = false, showBestsellerBadge = false }) => {
  const { addToCart } = useCart();

  const handleAddToCart = async () => {
    try {
      await addToCart(product.id, 1);
      // Show success message
    } catch (error) {
      console.error('Error adding to cart:', error);
    }
  };

  return (
    <div className="product-card card border-0 shadow-sm h-100">
      <Link to={`/product/${product.slug}`} className="product-image-link">
        <div className="product-image position-relative">
          <img
            src={product.main_image_url || '/static/img/product/placeholder.jpg'}
            alt={product.name}
            className="card-img-top"
            style={{ height: '200px', objectFit: 'cover' }}
          />
          {showNewBadge && <span className="badge-new position-absolute top-0 start-0">New</span>}
          {showBestsellerBadge && <span className="badge-bestseller position-absolute top-0 start-0">Bestseller</span>}
          {product.compare_price && product.compare_price > product.base_price && (
            <span className="badge-sale position-absolute top-0 end-0">
              -{Math.round((product.compare_price - product.base_price) / product.compare_price * 100)}%
            </span>
          )}
        </div>
      </Link>
      <div className="card-body">
        <h5 className="card-title">
          <Link to={`/product/${product.slug}`} className="text-decoration-none text-dark">
            {product.name}
          </Link>
        </h5>
        <p className="card-text text-muted small">{product.short_description}</p>
        <div className="price mb-2">
          {product.compare_price && product.compare_price > product.base_price ? (
            <>
              <span className="original-price text-muted text-decoration-line-through me-2">
                ₹{product.compare_price.toFixed(2)}
              </span>
              <span className="current-price text-primary fw-bold">
                ₹{product.base_price.toFixed(2)}
              </span>
            </>
          ) : (
            <span className="current-price text-primary fw-bold">
              ₹{product.base_price.toFixed(2)}
            </span>
          )}
        </div>
        <button
          className="btn btn-primary w-100"
          onClick={handleAddToCart}
          disabled={product.stock_status === 'out_of_stock'}
        >
          {product.stock_status === 'out_of_stock' ? 'Out of Stock' : 'Add to Cart'}
        </button>
      </div>
    </div>
  );
};

export default Home;