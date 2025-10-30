import React, { useState, useEffect } from 'react'
import { Container, Row, Col, Card, Button, Form, Spinner, Alert } from 'react-bootstrap'
import { Link } from 'react-router-dom'
import { API } from '../services/api'
import ProductCard from '../components/products/ProductCard'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorMessage from '../components/common/ErrorMessage'

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
      const response = await API.products.getAll(filters)
      // Handle different response structures
      const productsData = response.data.products || response.data || []
      setProducts(productsData)
    } catch (err) {
      setError('Failed to load products')
      console.error('Error loading products:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadCategories = async () => {
    try {
      const response = await API.products.getCategories()
      const categoriesData = response.data.categories || response.data || []
      setCategories(categoriesData)
    } catch (err) {
      console.error('Error loading categories:', err)
      setCategories([])
    }
  }

  const loadBrands = async () => {
    try {
      const response = await API.products.getBrands()
      const brandsData = response.data.brands || response.data || []
      setBrands(brandsData)
    } catch (err) {
      console.error('Error loading brands:', err)
      setBrands([])
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
      <Container className="mt-4">
        <LoadingSpinner text="Loading products..." />
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
          <ErrorMessage error={error} onRetry={loadProducts} />
          <Row>
            {products.map(product => (
              <Col key={product.id} lg={4} md={6} className="mb-4">
                <ProductCard product={product} />
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
