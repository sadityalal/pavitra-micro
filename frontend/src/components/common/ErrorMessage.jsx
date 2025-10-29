import React from 'react'
import { Alert, Button } from 'react-bootstrap'

const ErrorMessage = ({
  error,
  onRetry,
  variant = 'danger',
  className = '',
  dismissible = false,
  onDismiss
}) => {
  if (!error) return null

  return (
    <Alert variant={variant} className={className} dismissible={dismissible} onClose={onDismiss}>
      <div className="d-flex justify-content-between align-items-center">
        <span>{typeof error === 'string' ? error : error.message || 'An error occurred'}</span>
        {onRetry && (
          <Button variant="outline-danger" size="sm" onClick={onRetry}>
            Retry
          </Button>
        )}
      </div>
    </Alert>
  )
}

export default ErrorMessage