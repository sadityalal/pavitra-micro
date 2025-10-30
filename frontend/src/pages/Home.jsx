import React, { useState, useEffect } from 'react'
import { Container, Row, Col, Card, Button, Carousel } from 'react-bootstrap'
import { Link } from 'react-router-dom'
import { API } from '../services/api'
import ProductCard from '../components/products/ProductCard'
import LoadingSpinner from '../components/common/LoadingSpinner'

const Home = () => {
  const [featuredProducts, setFeaturedProducts] = useState([])
  const [bestsellers, setBestsellers] = useState([])
  const [newArrivals, setNewArrivals] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadHomeData()
  }, [])

  const loadHomeData = async () => {
    try {
      const [featuredResponse, bestsellersResponse, newArrivalsResponse] = await Promise.all([
        API.products.getFeatured(),
        API.products.getBestsellers(),
        API.products.getNewArrivals()
      ])

      setFeaturedProducts(featuredResponse.data.products || [])
      setBestsellers(bestsellersResponse.data.products || [])
      setNewArrivals(newArrivalsResponse.data.products || [])
    } catch (error) {
      console.error('Error loading home data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <LoadingSpinner text="Loading..." />
  }

  return (
    <>
      {/* Hero Section */}
      <section className="hero-section">
        <Container>
          <Row className="align-items-center">
            <Col lg={6}>
              <h1 className="display-4 fw-bold mb-4">Welcome to Belo2 Store</h1>
              <p className="lead mb-4">
                Discover amazing products at great prices. Quality guaranteed with fast delivery across India.
              </p>
              <Button as={Link} to="/products" variant="light" size="lg">
                Shop Now <i className="fas fa-arrow-right ms-2"></i>
              </Button>
            </Col>
            <Col lg={6}>
              <Carousel>
                <Carousel.Item>
                  <img
                    className="d-block w-100 rounded"
                    src="/images/hero-1.jpg"
                    alt="First slide"
                    style={{ height: '400px', objectFit: 'cover' }}
                  />
                </Carousel.Item>
                <Carousel.Item>
                  <img
                    className="d-block w-100 rounded"
                    src="/images/hero-2.jpg"
                    alt="Second slide"
                    style={{ height: '400px', objectFit: 'cover' }}
                  />
                </Carousel.Item>
              </Carousel>
            </Col>
          </Row>
        </Container>
      </section>

      <Container className="my-5">
        {/* Featured Products */}
        <section className="mb-5">
          <div className="d-flex justify-content-between align-items-center mb-4">
            <h2>Featured Products</h2>
            <Button as={Link} to="/products" variant="outline-primary">
              View All
            </Button>
          </div>
          <Row>
            {featuredProducts.slice(0, 4).map(product => (
              <Col key={product.id} lg={3} md={6} className="mb-4">
                <ProductCard product={product} />
              </Col>
            ))}
          </Row>
        </section>

        {/* Bestsellers */}
        <section className="mb-5">
          <div className="d-flex justify-content-between align-items-center mb-4">
            <h2>Bestsellers</h2>
            <Button as={Link} to="/products" variant="outline-primary">
              View All
            </Button>
          </div>
          <Row>
            {bestsellers.slice(0, 4).map(product => (
              <Col key={product.id} lg={3} md={6} className="mb-4">
                <ProductCard product={product} />
              </Col>
            ))}
          </Row>
        </section>

        {/* New Arrivals */}
        <section className="mb-5">
          <div className="d-flex justify-content-between align-items-center mb-4">
            <h2>New Arrivals</h2>
            <Button as={Link} to="/products" variant="outline-primary">
              View All
            </Button>
          </div>
          <Row>
            {newArrivals.slice(0, 4).map(product => (
              <Col key={product.id} lg={3} md={6} className="mb-4">
                <ProductCard product={product} />
              </Col>
            ))}
          </Row>
        </section>

        {/* Features Section */}
        <section className="my-5">
          <Row>
            <Col md={4} className="text-center mb-4">
              <Card className="border-0">
                <Card.Body>
                  <div className="text-primary mb-3">
                    <i className="fas fa-shipping-fast fa-3x"></i>
                  </div>
                  <Card.Title>Free Shipping</Card.Title>
                  <Card.Text>Free delivery on orders above ₹499</Card.Text>
                </Card.Body>
              </Card>
            </Col>
            <Col md={4} className="text-center mb-4">
              <Card className="border-0">
                <Card.Body>
                  <div className="text-primary mb-3">
                    <i className="fas fa-shield-alt fa-3x"></i>
                  </div>
                  <Card.Title>Secure Payment</Card.Title>
                  <Card.Text>100% secure payment processing</Card.Text>
                </Card.Body>
              </Card>
            </Col>
            <Col md={4} className="text-center mb-4">
              <Card className="border-0">
                <Card.Body>
                  <div className="text-primary mb-3">
                    <i className="fas fa-headset fa-3x"></i>
                  </div>
                  <Card.Title>24/7 Support</Card.Title>
                  <Card.Text>Round-the-clock customer support</Card.Text>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </section>
      </Container>
    </>
  )
}

export default Home