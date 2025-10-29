import React from 'react'
import { Card, Button } from 'react-bootstrap'

const EmptyState = ({
  icon = 'fas fa-inbox',
  title = 'No items found',
  message = 'There are no items to display at the moment.',
  actionText,
  onAction,
  className = ''
}) => {
  return (
    <Card className={`text-center ${className}`}>
      <Card.Body className="py-5">
        <i className={`${icon} fa-3x text-muted mb-3`}></i>
        <h5 className="text-muted">{title}</h5>
        <p className="text-muted">{message}</p>
        {actionText && onAction && (
          <Button variant="primary" onClick={onAction}>
            {actionText}
          </Button>
        )}
      </Card.Body>
    </Card>
  )
}

export default EmptyState