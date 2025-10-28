import React, { useState } from 'react';

const Contact = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: ''
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // For now, just show alert. You can connect to backend later
    alert('Thank you for your message! We will get back to you soon.');
    setFormData({ name: '', email: '', subject: '', message: '' });
  };

  return (
    <div className="container py-5">
      <div className="row">
        <div className="col-12">
          <div className="page-header mb-4">
            <h1>Contact Us</h1>
            <p className="lead">We'd love to hear from you. Get in touch with our team.</p>
          </div>
        </div>
      </div>

      <div className="row">
        <div className="col-lg-8">
          <div className="card">
            <div className="card-body">
              <h3 className="card-title">Send us a Message</h3>
              <form onSubmit={handleSubmit}>
                <div className="row">
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label htmlFor="name" className="form-label">Full Name *</label>
                      <input
                        type="text"
                        className="form-control"
                        id="name"
                        name="name"
                        value={formData.name}
                        onChange={handleChange}
                        required
                        placeholder="Enter your full name"
                      />
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label htmlFor="email" className="form-label">Email Address *</label>
                      <input
                        type="email"
                        className="form-control"
                        id="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        required
                        placeholder="Enter your email"
                      />
                    </div>
                  </div>
                </div>

                <div className="mb-3">
                  <label htmlFor="subject" className="form-label">Subject *</label>
                  <input
                    type="text"
                    className="form-control"
                    id="subject"
                    name="subject"
                    value={formData.subject}
                    onChange={handleChange}
                    required
                    placeholder="What is this regarding?"
                  />
                </div>

                <div className="mb-3">
                  <label htmlFor="message" className="form-label">Message *</label>
                  <textarea
                    className="form-control"
                    id="message"
                    name="message"
                    rows="6"
                    value={formData.message}
                    onChange={handleChange}
                    required
                    placeholder="Tell us how we can help you..."
                  ></textarea>
                </div>

                <button type="submit" className="btn btn-primary btn-lg">
                  Send Message
                </button>
              </form>
            </div>
          </div>
        </div>

        <div className="col-lg-4">
          <div className="card mb-4">
            <div className="card-body">
              <h4 className="card-title">Contact Information</h4>

              <div className="contact-item mb-3">
                <div className="d-flex align-items-center">
                  <i className="bi bi-telephone text-primary me-3 fs-5"></i>
                  <div>
                    <h6 className="mb-1">Phone</h6>
                    <p className="mb-0 text-muted">+91-9711317009</p>
                  </div>
                </div>
              </div>

              <div className="contact-item mb-3">
                <div className="d-flex align-items-center">
                  <i className="bi bi-envelope text-primary me-3 fs-5"></i>
                  <div>
                    <h6 className="mb-1">Email</h6>
                    <p className="mb-0 text-muted">support@pavitraenterprises.com</p>
                  </div>
                </div>
              </div>

              <div className="contact-item mb-3">
                <div className="d-flex align-items-center">
                  <i className="bi bi-clock text-primary me-3 fs-5"></i>
                  <div>
                    <h6 className="mb-1">Business Hours</h6>
                    <p className="mb-1 text-muted">Monday - Friday: 9:00 AM - 6:00 PM</p>
                    <p className="mb-1 text-muted">Saturday: 10:00 AM - 4:00 PM</p>
                    <p className="mb-0 text-muted">Sunday: Closed</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-body">
              <h4 className="card-title">Quick Support</h4>
              <p className="card-text">
                For immediate assistance with your orders or any urgent queries,
                feel free to call us during business hours or email us anytime.
              </p>
              <div className="alert alert-info">
                <small>
                  <i className="bi bi-info-circle me-2"></i>
                  We typically respond to emails within 24 hours.
                </small>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Contact;