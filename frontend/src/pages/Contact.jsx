import React from 'react';

const Contact = () => {
  return (
    <div className="container py-5">
      <h2>Contact Us</h2>
      <p>For support, email support@pavitraenterprises.com or call +91-9711317009.</p>
      <div className="row">
        <div className="col-md-6">
          <form>
            <div className="mb-3">
              <label className="form-label">Name</label>
              <input className="form-control" />
            </div>
            <div className="mb-3">
              <label className="form-label">Email</label>
              <input className="form-control" />
            </div>
            <div className="mb-3">
              <label className="form-label">Message</label>
              <textarea className="form-control" rows="5" />
            </div>
            <button className="btn btn-primary">Send</button>
          </form>
        </div>
        <div className="col-md-6">
          <h5>Address</h5>
          <p>123 Fashion Street, New Delhi, India</p>
          <h5>Opening Hours</h5>
          <p>Mon-Fri 9am - 6pm</p>
        </div>
      </div>
    </div>
  );
};

export default Contact;
