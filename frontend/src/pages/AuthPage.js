import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const AuthPage = () => {
  const [isActive, setIsActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState({
    login: false,
    register: false,
    confirm: false
  });

  // Login form state
  const [loginData, setLoginData] = useState({
    login_id: '',
    password: ''
  });

  // Register form state
  const [registerData, setRegisterData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    username: '',
    password: '',
    confirm_password: '',
    country_id: 1
  });

  const { login, register } = useAuth();
  const navigate = useNavigate();

  const togglePanel = () => {
    setIsActive(!isActive);
  };

  const handleLoginChange = (field, value) => {
    setLoginData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleRegisterChange = (field, value) => {
    setRegisterData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const togglePasswordVisibility = (formType, field) => {
    setShowPassword(prev => ({
      ...prev,
      [field]: !prev[field]
    }));
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await login(loginData);
      navigate('/');
    } catch (error) {
      console.error('Login failed:', error);
      alert('Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);

    if (registerData.password !== registerData.confirm_password) {
      alert('Passwords do not match');
      setLoading(false);
      return;
    }

    try {
      const registerPayload = {
        first_name: registerData.first_name,
        last_name: registerData.last_name,
        email: registerData.email,
        phone: registerData.phone,
        username: registerData.username,
        password: registerData.password,
        country_id: registerData.country_id,
        auth_type: 'email'
      };

      await register(registerPayload);
      navigate('/');
    } catch (error) {
      console.error('Registration failed:', error);
      alert('Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="auth-section section">
      <div className="container">
        <div className={`auth-container ${isActive ? 'active' : ''}`}>
          {/* Sign Up Form */}
          <div className="auth-form register-form">
            <div className="form-header">
              <h3>Create Account</h3>
              <p>Join us today and get started</p>
            </div>

            <form className="auth-form-content" onSubmit={handleRegister}>
              <div className="social-icons mb-3">
                <a href="#" className="social-icon">
                  <i className="bi bi-google"></i>
                </a>
                <a href="#" className="social-icon">
                  <i className="bi bi-facebook"></i>
                </a>
                <a href="#" className="social-icon">
                  <i className="bi bi-github"></i>
                </a>
                <a href="#" className="social-icon">
                  <i className="bi bi-linkedin"></i>
                </a>
              </div>

              <div className="divider mb-3">
                <span>or use your email for registration</span>
              </div>

              <div className="row mb-3">
                <div className="col-md-6">
                  <div className="input-group">
                    <span className="input-icon">
                      <i className="bi bi-person"></i>
                    </span>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="First Name"
                      required
                      value={registerData.first_name}
                      onChange={(e) => handleRegisterChange('first_name', e.target.value)}
                    />
                  </div>
                </div>
                <div className="col-md-6">
                  <div className="input-group">
                    <span className="input-icon">
                      <i className="bi bi-person"></i>
                    </span>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="Last Name"
                      required
                      value={registerData.last_name}
                      onChange={(e) => handleRegisterChange('last_name', e.target.value)}
                    />
                  </div>
                </div>
              </div>

              <div className="input-group mb-3">
                <span className="input-icon">
                  <i className="bi bi-envelope"></i>
                </span>
                <input
                  type="email"
                  className="form-control"
                  placeholder="Email address"
                  required
                  value={registerData.email}
                  onChange={(e) => handleRegisterChange('email', e.target.value)}
                />
              </div>

              <div className="input-group mb-3">
                <span className="input-icon">
                  <i className="bi bi-phone"></i>
                </span>
                <input
                  type="tel"
                  className="form-control"
                  placeholder="Phone number (optional)"
                  value={registerData.phone}
                  onChange={(e) => handleRegisterChange('phone', e.target.value)}
                />
              </div>

              <div className="input-group mb-3">
                <span className="input-icon">
                  <i className="bi bi-person-badge"></i>
                </span>
                <input
                  type="text"
                  className="form-control"
                  placeholder="Username (optional)"
                  value={registerData.username}
                  onChange={(e) => handleRegisterChange('username', e.target.value)}
                />
              </div>

              <div className="input-group mb-3">
                <span className="input-icon">
                  <i className="bi bi-lock"></i>
                </span>
                <input
                  type={showPassword.register ? "text" : "password"}
                  className="form-control"
                  placeholder="Create password"
                  required
                  value={registerData.password}
                  onChange={(e) => handleRegisterChange('password', e.target.value)}
                />
                <span
                  className="password-toggle"
                  onClick={() => togglePasswordVisibility('register', 'register')}
                >
                  <i className={`bi ${showPassword.register ? 'bi-eye-slash' : 'bi-eye'}`}></i>
                </span>
              </div>

              <div className="input-group mb-3">
                <span className="input-icon">
                  <i className="bi bi-lock-fill"></i>
                </span>
                <input
                  type={showPassword.confirm ? "text" : "password"}
                  className="form-control"
                  placeholder="Confirm password"
                  required
                  value={registerData.confirm_password}
                  onChange={(e) => handleRegisterChange('confirm_password', e.target.value)}
                />
                <span
                  className="password-toggle"
                  onClick={() => togglePasswordVisibility('register', 'confirm')}
                >
                  <i className={`bi ${showPassword.confirm ? 'bi-eye-slash' : 'bi-eye'}`}></i>
                </span>
              </div>

              <div className="terms-check mb-4">
                <input type="checkbox" id="termsRegister" required />
                <label htmlFor="termsRegister">
                  I agree to the <a href="/terms">Terms of Service</a> and <a href="/privacy">Privacy Policy</a>
                </label>
              </div>

              <button
                type="submit"
                className="btn btn-primary w-100 mb-3"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2"></span>
                    Creating Account...
                  </>
                ) : (
                  'Create Account'
                )}
              </button>
            </form>
          </div>

          {/* Sign In Form */}
          <div className="auth-form login-form">
            <div className="form-header">
              <h3>Welcome Back</h3>
              <p>Sign in to your account</p>
            </div>

            <form className="auth-form-content" onSubmit={handleLogin}>
              <div className="social-icons mb-3">
                <a href="#" className="social-icon">
                  <i className="bi bi-google"></i>
                </a>
                <a href="#" className="social-icon">
                  <i className="bi bi-facebook"></i>
                </a>
                <a href="#" className="social-icon">
                  <i className="bi bi-github"></i>
                </a>
                <a href="#" className="social-icon">
                  <i className="bi bi-linkedin"></i>
                </a>
              </div>

              <div className="divider mb-3">
                <span>or use your email and password</span>
              </div>

              <div className="input-group mb-3">
                <span className="input-icon">
                  <i className="bi bi-envelope"></i>
                </span>
                <input
                  type="text"
                  className="form-control"
                  placeholder="Email, phone, or username"
                  required
                  value={loginData.login_id}
                  onChange={(e) => handleLoginChange('login_id', e.target.value)}
                />
              </div>

              <div className="input-group mb-3">
                <span className="input-icon">
                  <i className="bi bi-lock"></i>
                </span>
                <input
                  type={showPassword.login ? "text" : "password"}
                  className="form-control"
                  placeholder="Password"
                  required
                  value={loginData.password}
                  onChange={(e) => handleLoginChange('password', e.target.value)}
                />
                <span
                  className="password-toggle"
                  onClick={() => togglePasswordVisibility('login', 'login')}
                >
                  <i className={`bi ${showPassword.login ? 'bi-eye-slash' : 'bi-eye'}`}></i>
                </span>
              </div>

              <div className="form-options mb-4">
                <div className="remember-me">
                  <input type="checkbox" id="rememberLogin" />
                  <label htmlFor="rememberLogin">Remember me</label>
                </div>
                <a href="#" className="forgot-password">Forgot password?</a>
              </div>

              <button
                type="submit"
                className="btn btn-primary w-100 mb-3"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2"></span>
                    Signing In...
                  </>
                ) : (
                  'Sign In'
                )}
              </button>
            </form>
          </div>

          {/* Toggle Panel */}
          <div className="toggle-panel">
            <div className="toggle-content toggle-left">
              <h3>Welcome Back!</h3>
              <p>Enter your personal details to use all of site features</p>
              <button className="btn btn-outline-light" onClick={togglePanel}>
                Sign In
              </button>
            </div>
            <div className="toggle-content toggle-right">
              <h3>Hello, Welcome!</h3>
              <p>Register with your personal details to use all of site features</p>
              <button className="btn btn-outline-light" onClick={togglePanel}>
                Sign Up
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default AuthPage;