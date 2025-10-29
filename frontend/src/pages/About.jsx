import React from 'react'
import { Container, Row, Col, Card } from 'react-bootstrap'
import PageHeader from '../components/layout/PageHeader'

const About = () => {
  return (
    <>
      <PageHeader title="About Belo2" subtitle="Your trusted e-commerce partner" />

      <Container>
        <Row className="mb-5">
          <Col lg={6}>
            <h2>Our Story</h2>
            <p className="lead">
              Belo2 is a modern e-commerce platform built with cutting-edge technology
              to provide the best shopping experience for our customers.
            </p>
            <p>
              Founded with a vision to revolutionize online shopping, we combine
              advanced technology with exceptional customer service to bring you
              a seamless shopping experience.
            </p>
          </Col>
          <Col lg={6}>
            <img
              src="/images/about-hero.jpg"
              alt="About Belo2"
              className="img-fluid rounded"
              style={{ maxHeight: '400px', width: '100%', objectFit: 'cover' }}
            />
          </Col>
        </Row>

        <Row className="mb-5">
          <Col>
            <h2 className="text-center mb-4">Why Choose Belo2?</h2>
            <Row>
              <Col md={4} className="mb-4">
                <Card className="h-100 text-center">
                  <Card.Body>
                    <div className="text-primary mb-3">
                      <i className="fas fa-shipping-fast fa-3x"></i>
                    </div>
                    <Card.Title>Fast Delivery</Card.Title>
                    <Card.Text>
                      Quick and reliable shipping across India with real-time tracking.
                    </Card.Text>
                  </Card.Body>
                </Card>
              </Col>
              <Col md={4} className="mb-4">
                <Card className="h-100 text-center">
                  <Card.Body>
                    <div className="text-primary mb-3">
                      <i className="fas fa-shield-alt fa-3x"></i>
                    </div>
                    <Card.Title>Secure Payments</Card.Title>
                    <Card.Text>
                      Your payments are protected with industry-leading security measures.
                    </Card.Text>
                  </Card.Body>
                </Card>
              </Col>
              <Col md={4} className="mb-4">
                <Card className="h-100 text-center">
                  <Card.Body>
                    <div className="text-primary mb-3">
                      <i className="fas fa-headset fa-3x"></i>
                    </div>
                    <Card.Title>24/7 Support</Card.Title>
                    <Card.Text>
                      Round-the-clock customer support to help you whenever you need.
                    </Card.Text>
                  </Card.Body>
                </Card>
              </Col>
            </Row>
          </Col>
        </Row>

        <Row>
          <Col lg={8} className="mx-auto">
            <Card className="bg-light">
              <Card.Body className="text-center py-5">
                <h3>Our Mission</h3>
                <p className="mb-0">
                  To provide an exceptional online shopping experience through innovative technology,
                  quality products, and outstanding customer service. We believe in making e-commerce
                  accessible, secure, and enjoyable for everyone.
                </p>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </Container>
    </>
  )
}

export default About