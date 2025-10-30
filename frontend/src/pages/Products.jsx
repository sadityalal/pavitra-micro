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
      console.log('🔄 Loading products with filters:', filters)

      // Build query parameters
      const params = {}
      if (filters.category_id) params.category_id = filters.category_id
      if (filters.brand_id) params.brand_id = filters.brand_id
      if (filters.min_price) params.min_price = filters.min_price
      if (filters.max_price) params.max_price = filters.max_price
      if (filters.in_stock) params.in_stock = filters.in_stock

      console.log('📡 API call params:', params)

      const response = await API.products.getAll(params)
      console.log('✅ Products API response:', response.data)

      // Handle different response structures
      let productsData = []
      if (response.data.products) {
        productsData = response.data.products
      } else if (Array.isArray(response.data)) {
        productsData = response.data
      } else {
        productsData = []
      }

      console.log(`📦 Processed ${productsData.length} products`)
      setProducts(productsData)
    } catch (err) {
      console.error('❌ Error loading products:', err)
      setError('Failed to load products: ' + (err.response?.data?.detail || err.message))
    } finally {
      setLoading(false)
    }
  }

  const loadCategories = async () => {
    try {
      console.log('🔄 Loading categories...')
      const response = await API.products.getCategories()
      console.log('✅ Categories response:', response.data)

      let categoriesData = []
      if (response.data.categories) {
        categoriesData = response.data.categories
      } else if (Array.isArray(response.data)) {
        categoriesData = response.data
      }

      setCategories(categoriesData)
    } catch (err) {
      console.error('❌ Error loading categories:', err)
      setCategories([])
    }
  }

  const loadBrands = async () => {
    try {
      console.log('🔄 Loading brands...')
      const response = await API.products.getBrands()
      console.log('✅ Brands response:', response.data)

      let brandsData = []
      if (response.data.brands) {
        brandsData = response.data.brands
      } else if (Array.isArray(response.data)) {
        brandsData = response.data
      }

      setBrands(brandsData)
    } catch (err) {
      console.error('❌ Error loading brands:', err)
      setBrands([])
    }
  }

  const handleFilterChange = (key, value) => {
    console.log(`🔧 Filter changed: ${key} = ${value}`)
    setFilters(prev => ({
      ...prev,
      [key]: value
    }))
  }

  const clearFilters = () => {
    console.log('🧹 Clearing filters')
    setFilters({
      category_id: '',
      brand_id: '',
      min_price: '',
      max_price: '',
      in_stock: false
    })
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
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1>All Products</h1>
        <Button variant="outline-primary" onClick={clearFilters}>
          Clear Filters
        </Button>
      </div>

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

          <div className="mb-3">
            <p className="text-muted">
              Showing {products.length} products
              {filters.category_id && ` in selected category`}
              {filters.brand_id && ` from selected brand`}
            </p>
          </div>

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
              <p>Try adjusting your filters or check the console for errors.</p>
              <Button variant="primary" onClick={clearFilters}>
                Clear All Filters
              </Button>
            </div>
          )}
        </Col>
      </Row>
    </Container>
  )
}

export default Products