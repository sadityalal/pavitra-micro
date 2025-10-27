// frontend/src/pages/Register.js
import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';

const Register = () => {
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    username: '',
    password: '',
    confirmPassword: '',
    country_id: 1
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [authType, setAuthType] = useState('email'); // 'email', 'phone', 'username'

  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError('');
  };

  const validateForm = () => {
    if (!formData.first_name || !formData.last_name) {
      return 'Please enter your name';
    }

    if (!formData.password) {
      return 'Please enter a password';
    }

    if (formData.password.length < 8) {
      return 'Password must be at least 8 characters long';
    }

    if (formData.password !== formData.confirmPassword) {
      return 'Passwords do not match';
    }

    // Validate based on auth type
    if (authType === 'email' && !formData.email) {
      return 'Please enter your email';
    }

    if (authType === 'phone' && !formData.phone) {
      return 'Please enter your phone number';
    }

    if (authType === 'username' && !formData.username) {
      return 'Please enter a username';
    }

    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Prepare data for backend
      const registrationData = {
        first_name: formData.first_name,
        last_name: formData.last_name,
        password: formData.password,
        auth_type: authType,
        country_id: formData.country_id
      };

      // Add the appropriate identifier based on auth type
      if (authType === 'email') {
        registrationData.email = formData.email;
      } else if (authType === 'phone') {
        registrationData.phone = formData.phone;
      } else if (authType === 'username') {
        registrationData.username = formData.username;
      }

      await register(registrationData);
      navigate('/');
    } catch (error) {
      console.error('Registration error:', error);
      setError(error.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container py-5">
      <div className="row justify-content-center">
        <div className="col-md-8 col-lg-6">
          <div className="card shadow">
            <div className="card-body p-4">
              <h2 className="text-center mb-4">Create Account</h2>

              {error && (
                <div className="alert alert-danger" role="alert">
                  {error}
                </div>
              )}

              {/* Auth Type Selector */}
              <div className="mb-4">
                <label className="form-label fw-bold">Sign up with:</label>
                <div className="d-flex gap-2 flex-wrap">
                  <button
                    type="button"
                    className={`btn ${authType === 'email' ? 'btn-primary' : 'btn-outline-primary'}`}
                    onClick={() => setAuthType('email')}
                  >
                    Email
                  </button>
                  <button
                    type="button"
                    className={`btn ${authType === 'phone' ? 'btn-primary' : 'btn-outline-primary'}`}
                    onClick={() => setAuthType('phone')}
                  >
                    Phone
                  </button>
                  <button
                    type="button"
                    className={`btn ${authType === 'username' ? 'btn-primary' : 'btn-outline-primary'}`}
                    onClick={() => setAuthType('username')}
                  >
                    Username
                  </button>
                </div>
              </div>

              <form onSubmit={handleSubmit}>
                <div className="row">
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label htmlFor="first_name" className="form-label">
                        First Name *
                      </label>
                      <input
                        type="text"
                        className="form-control"
                        id="first_name"
                        name="first_name"
                        value={formData.first_name}
                        onChange={handleChange}
                        required
                        disabled={loading}
                      />
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label htmlFor="last_name" className="form-label">
                        Last Name *
                      </label>
                      <input
                        type="text"
                        className="form-control"
                        id="last_name"
                        name="last_name"
                        value={formData.last_name}
                        onChange={handleChange}
                        required
                        disabled={loading}
                      />
                    </div>
                  </div>
                </div>

                {/* Dynamic field based on auth type */}
                {authType === 'email' && (
                  <div className="mb-3">
                    <label htmlFor="email" className="form-label">
                      Email Address *
                    </label>
                    <input
                      type="email"
                      className="form-control"
                      id="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      required
                      disabled={loading}
                    />
                  </div>
                )}

                {authType === 'phone' && (
                  <div className="mb-3">
                    <label htmlFor="phone" className="form-label">
                      Phone Number *
                    </label>
                    <input
                      type="tel"
                      className="form-control"
                      id="phone"
                      name="phone"
                      value={formData.phone}
                      onChange={handleChange}
                      required
                      disabled={loading}
                      placeholder="+91XXXXXXXXXX"
                    />
                  </div>
                )}

                {authType === 'username' && (
                  <div className="mb-3">
                    <label htmlFor="username" className="form-label">
                      Username *
                    </label>
                    <input
                      type="text"
                      className="form-control"
                      id="username"
                      name="username"
                      value={formData.username}
                      onChange={handleChange}
                      required
                      disabled={loading}
                      placeholder="Choose a username"
                    />
                    <div className="form-text">
                      3-30 characters, letters, numbers, and underscores only
                    </div>
                  </div>
                )}

                <div className="mb-3">
                  <label htmlFor="password" className="form-label">
                    Password *
                  </label>
                  <input
                    type="password"
                    className="form-control"
                    id="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    required
                    disabled={loading}
                  />
                  <div className="form-text">
                    Password must be at least 8 characters long
                  </div>
                </div>

                <div className="mb-3">
                  <label htmlFor="confirmPassword" className="form-label">
                    Confirm Password *
                  </label>
                  <input
                    type="password"
                    className="form-control"
                    id="confirmPassword"
                    name="confirmPassword"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    required
                    disabled={loading}
                  />
                </div>

                <div className="mb-3">
                  <label htmlFor="country_id" className="form-label">
                    Country
                  </label>
                  <select
                    className="form-select"
                    id="country_id"
                    name="country_id"
                    value={formData.country_id}
                    onChange={handleChange}
                    disabled={loading}
                  >
                    <option value="1">India</option>
                    <option value="2">United States</option>
                    <option value="3">United Kingdom</option>
                  </select>
                </div>

                <div className="mb-3 form-check">
                  <input
                    type="checkbox"
                    className="form-check-input"
                    id="terms"
                    required
                  />
                  <label className="form-check-label" htmlFor="terms">
                    I agree to the{' '}
                    <a href="/terms" className="text-decoration-none">
                      Terms of Service
                    </a>{' '}
                    and{' '}
                    <a href="/privacy" className="text-decoration-none">
                      Privacy Policy
                    </a>
                  </label>
                </div>

                <button
                  type="submit"
                  className="btn btn-primary w-100"
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                      Creating Account...
                    </>
                  ) : (
                    'Create Account'
                  )}
                </button>
              </form>

              <hr className="my-4" />

              <div className="text-center">
                <p className="mb-0">
                  Already have an account?{' '}
                  <Link to="/login" className="text-decoration-none fw-bold">
                    Sign in
                  </Link>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Register;