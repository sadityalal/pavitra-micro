import React from 'react'
import { Container, Breadcrumb } from 'react-bootstrap'
import { Link, useLocation } from 'react-router-dom'

const PageHeader = ({
  title,
  subtitle,
  breadcrumb = true,
  className = ''
}) => {
  const location = useLocation()
  const pathnames = location.pathname.split('/').filter(x => x)

  return (
    <div className={`bg-light py-4 mb-4 ${className}`}>
      <Container>
        {breadcrumb && (
          <Breadcrumb className="mb-2">
            <Breadcrumb.Item linkAs={Link} linkProps={{ to: '/' }}>
              Home
            </Breadcrumb.Item>
            {pathnames.map((name, index) => {
              const routeTo = `/${pathnames.slice(0, index + 1).join('/')}`
              const isLast = index === pathnames.length - 1

              return isLast ? (
                <Breadcrumb.Item active key={name}>
                  {name.charAt(0).toUpperCase() + name.slice(1)}
                </Breadcrumb.Item>
              ) : (
                <Breadcrumb.Item
                  key={name}
                  linkAs={Link}
                  linkProps={{ to: routeTo }}
                >
                  {name.charAt(0).toUpperCase() + name.slice(1)}
                </Breadcrumb.Item>
              )
            })}
          </Breadcrumb>
        )}

        <h1 className="h2 mb-2">{title}</h1>
        {subtitle && <p className="text-muted mb-0">{subtitle}</p>}
      </Container>
    </div>
  )
}

export default PageHeader