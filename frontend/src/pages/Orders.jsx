import React, { useState, useEffect } from 'react'
import { Container, Row, Col, Card, Table, Badge, Button, Dropdown } from 'react-bootstrap'
import { Link } from 'react-router-dom'
import { API } from '../services/api'
import PageHeader from '../components/layout/PageHeader'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorMessage from '../components/common/ErrorMessage'
import EmptyState from '../components/common/EmptyState'
import Pagination from '../components/common/Pagination'

const Orders = () => {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: 10,
    totalCount: 0,
    totalPages: 0
  })

  useEffect(() => {
    loadOrders()
  }, [pagination.page])

  const loadOrders = async () => {
    try {
      setLoading(true)
      const response = await API.orders.getUserOrders({
        page: pagination.page,
        page_size: pagination.pageSize
      })
      setOrders(response.data.orders)
      setPagination(prev => ({
        ...prev,
        totalCount: response.data.total_count,
        totalPages: response.data.total_pages
      }))
    } catch (err) {
      setError('Failed to load orders')
    } finally {
      setLoading(false)
    }
  }

  const getStatusVariant = (status) => {
    const variants = {
      pending: 'warning',
      confirmed: 'info',
      processing: 'primary',
      shipped: 'success',
      delivered: 'success',
      cancelled: 'danger',
      refunded: 'secondary'
    }
    return variants[status] || 'secondary'
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (loading) {
    return (
      <>
        <PageHeader title="My Orders" />
        <LoadingSpinner text="Loading your orders..." />
      </>
    )
  }

  return (
    <>
      <PageHeader title="My Orders" />
      <Container>
        <ErrorMessage error={error} onRetry={loadOrders} />

        {orders.length === 0 ? (
          <EmptyState
            icon="fas fa-shopping-bag"
            title="No orders yet"
            message="You haven't placed any orders yet. Start shopping to see your orders here."
            actionText="Start Shopping"
            onAction={() => window.location.href = '/products'}
          />
        ) : (
          <>
            <Card>
              <Card.Body className="p-0">
                <Table responsive className="mb-0">
                  <thead className="bg-light">
                    <tr>
                      <th>Order #</th>
                      <th>Date</th>
                      <th>Items</th>
                      <th>Total</th>
                      <th>Status</th>
                      <th>Payment</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {orders.map((order) => (
                      <OrderRow
                        key={order.id}
                        order={order}
                        onStatusChange={loadOrders}
                        getStatusVariant={getStatusVariant}
                        formatDate={formatDate}
                      />
                    ))}
                  </tbody>
                </Table>
              </Card.Body>
            </Card>

            {pagination.totalPages > 1 && (
              <div className="d-flex justify-content-center mt-4">
                <Pagination
                  currentPage={pagination.page}
                  totalPages={pagination.totalPages}
                  onPageChange={(page) => setPagination(prev => ({ ...prev, page }))}
                />
              </div>
            )}
          </>
        )}
      </Container>
    </>
  )
}

const OrderRow = ({ order, onStatusChange, getStatusVariant, formatDate }) => {
  const [cancelling, setCancelling] = useState(false)

  const handleCancel = async () => {
    if (!window.confirm('Are you sure you want to cancel this order?')) return

    try {
      setCancelling(true)
      await API.orders.cancel(order.id, 'Cancelled by customer')
      onStatusChange()
    } catch (err) {
      alert('Failed to cancel order')
    } finally {
      setCancelling(false)
    }
  }

  const canCancel = ['pending', 'confirmed'].includes(order.status)

  return (
    <tr>
      <td>
        <Link to={`/orders/${order.id}`} className="fw-bold text-decoration-none">
          {order.order_number}
        </Link>
      </td>
      <td>{formatDate(order.created_at)}</td>
      <td>{order.items?.length || 1} item(s)</td>
      <td>₹{order.total_amount}</td>
      <td>
        <Badge bg={getStatusVariant(order.status)}>
          {order.status.replace('_', ' ').toUpperCase()}
        </Badge>
      </td>
      <td>
        <Badge bg={order.payment_status === 'paid' ? 'success' : 'warning'}>
          {order.payment_status.toUpperCase()}
        </Badge>
      </td>
      <td>
        <Dropdown>
          <Dropdown.Toggle variant="outline-primary" size="sm" id="order-actions">
            Actions
          </Dropdown.Toggle>
          <Dropdown.Menu>
            <Dropdown.Item as={Link} to={`/orders/${order.id}`}>
              <i className="fas fa-eye me-2"></i>View Details
            </Dropdown.Item>
            {canCancel && (
              <Dropdown.Item
                onClick={handleCancel}
                disabled={cancelling}
                className="text-danger"
              >
                <i className="fas fa-times me-2"></i>
                {cancelling ? 'Cancelling...' : 'Cancel Order'}
              </Dropdown.Item>
            )}
            {order.status === 'delivered' && (
              <Dropdown.Item>
                <i className="fas fa-undo me-2"></i>Request Return
              </Dropdown.Item>
            )}
          </Dropdown.Menu>
        </Dropdown>
      </td>
    </tr>
  )
}

export default Order