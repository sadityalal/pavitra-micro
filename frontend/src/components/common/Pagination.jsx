import React from 'react'
import { Pagination as BootstrapPagination } from 'react-bootstrap'

const Pagination = ({
  currentPage,
  totalPages,
  onPageChange,
  className = '',
  size = 'md'
}) => {
  if (totalPages <= 1) return null

  const items = []
  const maxVisiblePages = 5

  let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2))
  let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1)

  if (endPage - startPage + 1 < maxVisiblePages) {
    startPage = Math.max(1, endPage - maxVisiblePages + 1)
  }

  // First page
  if (startPage > 1) {
    items.push(
      <BootstrapPagination.Item key={1} onClick={() => onPageChange(1)}>
        1
      </BootstrapPagination.Item>
    )
    if (startPage > 2) {
      items.push(<BootstrapPagination.Ellipsis key="start-ellipsis" />)
    }
  }

  // Page numbers
  for (let page = startPage; page <= endPage; page++) {
    items.push(
      <BootstrapPagination.Item
        key={page}
        active={page === currentPage}
        onClick={() => onPageChange(page)}
      >
        {page}
      </BootstrapPagination.Item>
    )
  }

  // Last page
  if (endPage < totalPages) {
    if (endPage < totalPages - 1) {
      items.push(<BootstrapPagination.Ellipsis key="end-ellipsis" />)
    }
    items.push(
      <BootstrapPagination.Item key={totalPages} onClick={() => onPageChange(totalPages)}>
        {totalPages}
      </BootstrapPagination.Item>
    )
  }

  return (
    <BootstrapPagination className={className} size={size}>
      <BootstrapPagination.Prev
        disabled={currentPage === 1}
        onClick={() => onPageChange(currentPage - 1)}
      />
      {items}
      <BootstrapPagination.Next
        disabled={currentPage === totalPages}
        onClick={() => onPageChange(currentPage + 1)}
      />
    </BootstrapPagination>
  )
}

export default Pagination