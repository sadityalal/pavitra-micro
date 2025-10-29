import React, { useState } from 'react'
import { Container, Row, Col, Card, Form, Button, Alert } from 'react-bootstrap'
import PageHeader from '../components/layout/PageHeader'

const Contact = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: ''
  })
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    // Simulate form submission
    setTimeout(() => {
      setSubmitted(true)
      setLoading(false)
      setFormData({ name: '', email: '', subject: '', message: '' })
    }, 1000)
  }

  return (
    <>
      <PageHeader title="Contact Us" subtitle="We'd love to hear from you" />

      <Container>
        <Row>
          <Col lg={8} className="mx-auto">
            {submitted && (
              <Alert variant="success" className="mb-4">
                Thank you for your message! We'll get back to you soon.
              </Alert>
            )}

            <Card>
              <Card.Body>
                <Form onSubmit={handleSubmit}>
                  <Row>
                    <Col md={6}>
                      <Form.Group className="mb-3">
                        <Form.Label>Full Name *</Form.Label>
                        <Form.Control
                          type="text"
                          name="name"
                          value={formData.name}
                          onChange={handleInputChange}
                          required
                          placeholder="Enter your full name"
                        />
                      </Form.Group>
                    </Col>
                    <Col md={6}>
                      <Form.Group className="mb-3">
                        <Form.Label>Email Address *</Form.Label>
                        <Form.Control
                          type="email"
                          name="email"
                          value={formData.email}
                          onChange={handleInputChange}
                          required
                          placeholder="Enter your email"
                        />
                      </Form.Group>
                    </Col>
                  </Row>

                  <Form.Group className="mb-3">
                    <Form.Label>Subject *</Form.Label>
                    <Form.Control
                      type="text"
                      name="subject"
                      value={formData.subject}
                      onChange={handleInputChange}
                      required
                      placeholder="Enter subject"
                    />
                  </Form.Group>

                  <Form.Group className="mb-4">
                    <Form.Label>Message *</Form.Label>
                    <Form.Control
                      as="textarea"
                      rows={5}
                      name="message"
                      value={formData.message}
                      onChange={handleInputChange}
                      required
                      placeholder="Enter your message"
                    />
                  </Form.Group>

                  <Button
                    variant="primary"
                    type="submit"
                    size="lg"
                    disabled={loading}
                  >
                    {loading ? 'Sending...' : 'Send Message'}
                  </Button>
                </Form>
              </Card.Body>
            </Card>
          </Col>
        </Row>

        <Row className="mt-5">
          <Col md={4} className="text-center mb-4">
            <Card className="h-100 border-0">
              <Card.Body>
                <div className="text-primary mb-3">
                  <i className="fas fa-map-marker-alt fa-2x"></i>
                </div>
                <Card.Title>Our Office</Card.Title>
                <Card.Text>
                  123 Business Street<br />
                  Commerce District<br />
                  Mumbai, MH 400001
                </Card.Text>
              </Card.Body>
            </Card>
          </Col>

          <Col md={4} className="text-center mb-4">
            <Card className="h-100 border-0">
              <Card.Body>
                <div className="text-primary mb-3">
                  <i className="fas fa-phone fa-2x"></i>
                </div>
                <Card.Title>Call Us</Card.Title>
                <Card.Text>
                  +91-9711317009<br />
                  Mon-Fri: 9AM-6PM<br />
                  Sat: 10AM-4PM
                </Card.Text>
              </Card.Body>
            </Card>
          </Col>

          <Col md={4} className="text-center mb-4">
            <Card className="h-100 border-0">
              <Card.Body>
                <div className="text-primary mb-3">
                  <i className="fas fa-envelope fa-2x"></i>
                </div>
                <Card.Title>Email Us</Card.Title>
                <Card.Text>
                  support@pavitraenterprises.com<br />
                  sales@pavitraenterprises.com<br />
                  We reply within 24 hours
                </Card.Text>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </Container>
    </>
  )
}

export default Contact