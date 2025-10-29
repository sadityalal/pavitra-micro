import React, { useState, useEffect } from 'react'
import { Container, Row, Col, Card, Button, Form, Spinner, Alert } from 'react-bootstrap'
import { Link } from 'react-router-dom'
import { productsAPI } from '../services/api'

const Products = () => {
  const [products, setProducts] = useState([])
  const [categories, setCategories] = useState([])
  const [brands, setBrands] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filters, setFilters] = useState({
    category_id: '',
    brand_id: '',
    min_price: '',
    max_price: '',
    in_stock: false
  })

  useEffect(() => {
    loadProducts()
    loadCategories()
    loadBrands()
  }, [filters])

  const loadProducts = async () => {
    try {
      setLoading(true)
      const response = await productsAPI.getAll(filters)
      setProducts(response.data.products)
    } catch (err) {
      setError('Failed to load products')
      console.error('Error loading products:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadCategories = async () => {
    try {
      const response = await productsAPI.getCategories()
      setCategories(response.data)
    } catch (err) {
      console.error('Error loading categories:', err)
    }
  }

  const loadBrands = async () => {
    try {
      const response = await productsAPI.getBrands()
      setBrands(response.data)
    } catch (err) {
      console.error('Error loading brands:', err)
    }
  }

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }))
  }

  if (loading) {
    return (
      <Container className="text-center mt-5">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading...</span>
        </Spinner>
      </Container>
    )
  }

  return (
    <Container className="mt-4">
      <Row>
        <Col md={3}>
          <Card>
            <Card.Header>
              <h5>Filters</h5>
            </Card.Header>
            <Card.Body>
              <Form>
                <Form.Group className="mb-3">
                  <Form.Label>Category</Form.Label>
                  <Form.Select
                    value={filters.category_id}
                    onChange={(e) => handleFilterChange('category_id', e.target.value)}
                  >
                    <option value="">All Categories</option>
                    {categories.map(category => (
                      <option key={category.id} value={category.id}>
                        {category.name}
                      </option>
                    ))}
                  </Form.Select>
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Brand</Form.Label>
                  <Form.Select
                    value={filters.brand_id}
                    onChange={(e) => handleFilterChange('brand_id', e.target.value)}
                  >
                    <option value="">All Brands</option>
                    {brands.map(brand => (
                      <option key={brand.id} value={brand.id}>
                        {brand.name}
                      </option>
                    ))}
                  </Form.Select>
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Price Range</Form.Label>
                  <Row>
                    <Col>
                      <Form.Control
                        type="number"
                        placeholder="Min"
                        value={filters.min_price}
                        onChange={(e) => handleFilterChange('min_price', e.target.value)}
                      />
                    </Col>
                    <Col>
                      <Form.Control
                        type="number"
                        placeholder="Max"
                        value={filters.max_price}
                        onChange={(e) => handleFilterChange('max_price', e.target.value)}
                      />
                    </Col>
                  </Row>
                </Form.Group>

                <Form.Check
                  type="checkbox"
                  label="In Stock Only"
                  checked={filters.in_stock}
                  onChange={(e) => handleFilterChange('in_stock', e.target.checked)}
                />
              </Form>
            </Card.Body>
          </Card>
        </Col>

        <Col md={9}>
          {error && <Alert variant="danger">{error}</Alert>}

          <Row>
            {products.map(product => (
              <Col key={product.id} lg={4} md={6} className="mb-4">
                <Card className="product-card h-100">
                  <Card.Img
                    variant="top"
                    src={product.main_image_url || '/placeholder-product.jpg'}
                    style={{ height: '200px', objectFit: 'cover' }}
                  />
                  <Card.Body className="d-flex flex-column">
                    <Card.Title>{product.name}</Card.Title>
                    <Card.Text className="text-muted flex-grow-1">
                      {product.short_description}
                    </Card.Text>
                    <div className="mt-auto">
                      <div className="d-flex justify-content-between align-items-center mb-2">
                        <strong className="text-primary">
                          ₹{product.base_price}
                        </strong>
                        <small className={
                          product.stock_status === 'in_stock' ? 'text-success' : 'text-danger'
                        }>
                          {product.stock_status === 'in_stock' ? 'In Stock' : 'Out of Stock'}
                        </small>
                      </div>
                      <Button
                        as={Link}
                        to={`/products/${product.id}`}
                        variant="primary"
                        className="w-100"
                      >
                        View Details
                      </Button>
                    </div>
                  </Card.Body>
                </Card>
              </Col>
            ))}
          </Row>

          {products.length === 0 && !loading && (
            <div className="text-center mt-5">
              <h4>No products found</h4>
              <p>Try adjusting your filters</p>
            </div>
          )}
        </Col>
      </Row>
    </Container>
  )
}

export default Products