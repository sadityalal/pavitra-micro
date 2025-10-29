import React from 'react'
import { Spinner, Container } from 'react-bootstrap'

const LoadingSpinner = ({
  size = 'lg',
  centered = true,
  text = 'Loading...',
  className = ''
}) => {
  const spinner = (
    <div className={`d-flex align-items-center ${className}`}>
      <Spinner animation="border" size={size} role="status" />
      {text && <span className="ms-2">{text}</span>}
    </div>
  )

  if (centered) {
    return (
      <Container className="d-flex justify-content-center align-items-center" style={{ minHeight: '200px' }}>
        {spinner}
      </Container>
    )
  }

  return spinner
}

export default LoadingSpinner