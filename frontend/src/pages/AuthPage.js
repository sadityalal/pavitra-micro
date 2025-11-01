import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';

const AuthPage = () => {
  const [isActive, setIsActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState({
    login: false,
    register: false,
    confirm: false
  });

  const [loginData, setLoginData] = useState({
    login_id: '',
    password: ''
  });

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
  const location = useLocation();

  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const formType = searchParams.get('form');
    if (formType === 'register') {
      setIsActive(true);
    } else if (formType === 'login') {
      setIsActive(false);
    }
  }, [location]);

  const togglePanel = () => {
    setIsActive(!isActive);
    setError(''); // Clear errors when switching panels
  };

  const handleLoginChange = (field, value) => {
    setLoginData(prev => ({
      ...prev,
      [field]: value
    }));
    setError(''); // Clear errors when user types
  };

  const handleRegisterChange = (field, value) => {
    setRegisterData(prev => ({
      ...prev,
      [field]: value
    }));
    setError(''); // Clear errors when user types
  };

  const togglePasswordVisibility = (field) => {
    setShowPassword(prev => ({
      ...prev,
      [field]: !prev[field]
    }));
  };

  const validateRegisterData = () => {
    if (!registerData.first_name.trim()) {
      return 'First name is required';
    }
    if (!registerData.last_name.trim()) {
      return 'Last name is required';
    }
    if (!registerData.email.trim() && !registerData.phone.trim() && !registerData.username.trim()) {
      return 'Email, phone, or username is required';
    }
    if (registerData.password.length < 8) {
      return 'Password must be at least 8 characters long';
    }
    if (registerData.password !== registerData.confirm_password) {
      return 'Passwords do not match';
    }
    return null;
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await login(loginData);
      navigate('/');
    } catch (error) {
      console.error('Login failed:', error);
      setError(error.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // Validate data before sending
    const validationError = validateRegisterData();
    if (validationError) {
      setError(validationError);
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
        country_id: registerData.country_id
      };

      await register(registerPayload);
      navigate('/');
    } catch (error) {
      console.error('Registration failed:', error);
      setError(error.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`auth-container ${isActive ? 'active' : ''}`} id="container">
      {/* Error Display */}
      {error && (
        <div className="alert alert-danger alert-dismissible fade show" style={{ position: 'fixed', top: '20px', left: '50%', transform: 'translateX(-50%)', zIndex: 1000, minWidth: '300px' }}>
          <strong>Error:</strong> {error}
          <button type="button" className="btn-close" onClick={() => setError('')}></button>
        </div>
      )}

      {/* Sign Up Form */}
      <div className="form-container sign-up">
        <form onSubmit={handleRegister}>
          <h1>Create Account</h1>
          <div className="social-icons">
            <a href="#" className="icon"><i className="fa-brands fa-google-plus-g"></i></a>
            <a href="#" className="icon"><i className="fa-brands fa-facebook-f"></i></a>
            <a href="#" className="icon"><i className="fa-brands fa-github"></i></a>
            <a href="#" className="icon"><i className="fa-brands fa-linkedin-in"></i></a>
          </div>
          <span>or use your email for registration</span>

          <div className="name-fields">
            <input
              type="text"
              placeholder="First Name *"
              value={registerData.first_name}
              onChange={(e) => handleRegisterChange('first_name', e.target.value)}
              required
              disabled={loading}
            />
            <input
              type="text"
              placeholder="Last Name *"
              value={registerData.last_name}
              onChange={(e) => handleRegisterChange('last_name', e.target.value)}
              required
              disabled={loading}
            />
          </div>

          <input
            type="email"
            placeholder="Email"
            value={registerData.email}
            onChange={(e) => handleRegisterChange('email', e.target.value)}
            disabled={loading}
          />

          <input
            type="text"
            placeholder="Phone (optional)"
            value={registerData.phone}
            onChange={(e) => handleRegisterChange('phone', e.target.value)}
            disabled={loading}
          />

          <input
            type="text"
            placeholder="Username (optional)"
            value={registerData.username}
            onChange={(e) => handleRegisterChange('username', e.target.value)}
            disabled={loading}
          />

          <div className="password-field">
            <input
              type={showPassword.register ? "text" : "password"}
              placeholder="Password *"
              value={registerData.password}
              onChange={(e) => handleRegisterChange('password', e.target.value)}
              required
              minLength="8"
              disabled={loading}
            />
            <span
              className="password-toggle"
              onClick={() => togglePasswordVisibility('register')}
            >
              <i className={`fa-solid ${showPassword.register ? 'fa-eye-slash' : 'fa-eye'}`}></i>
            </span>
          </div>

          <div className="password-field">
            <input
              type={showPassword.confirm ? "text" : "password"}
              placeholder="Confirm Password *"
              value={registerData.confirm_password}
              onChange={(e) => handleRegisterChange('confirm_password', e.target.value)}
              required
              disabled={loading}
            />
            <span
              className="password-toggle"
              onClick={() => togglePasswordVisibility('confirm')}
            >
              <i className={`fa-solid ${showPassword.confirm ? 'fa-eye-slash' : 'fa-eye'}`}></i>
            </span>
          </div>

          <button type="submit" disabled={loading}>
            {loading ? 'Creating Account...' : 'Sign Up'}
          </button>
        </form>
      </div>

      {/* Sign In Form */}
      <div className="form-container sign-in">
        <form onSubmit={handleLogin}>
          <h1>Sign In</h1>
          <div className="social-icons">
            <a href="#" className="icon"><i className="fa-brands fa-google-plus-g"></i></a>
            <a href="#" className="icon"><i className="fa-brands fa-facebook-f"></i></a>
            <a href="#" className="icon"><i className="fa-brands fa-github"></i></a>
            <a href="#" className="icon"><i className="fa-brands fa-linkedin-in"></i></a>
          </div>
          <span>or use your email password</span>

          <input
            type="text"
            placeholder="Email, Phone or Username *"
            value={loginData.login_id}
            onChange={(e) => handleLoginChange('login_id', e.target.value)}
            required
            disabled={loading}
          />

          <div className="password-field">
            <input
              type={showPassword.login ? "text" : "password"}
              placeholder="Password *"
              value={loginData.password}
              onChange={(e) => handleLoginChange('password', e.target.value)}
              required
              disabled={loading}
            />
            <span
              className="password-toggle"
              onClick={() => togglePasswordVisibility('login')}
            >
              <i className={`fa-solid ${showPassword.login ? 'fa-eye-slash' : 'fa-eye'}`}></i>
            </span>
          </div>

          <a href="#">Forget Your Password?</a>

          <button type="submit" disabled={loading}>
            {loading ? 'Signing In...' : 'Sign In'}
          </button>
        </form>
      </div>

      {/* Toggle Container */}
      <div className="toggle-container">
        <div className="toggle">
          <div className="toggle-panel toggle-left">
            <h1>Welcome Back!</h1>
            <p>Enter your personal details to use all of site features</p>
            <button className="hidden" onClick={togglePanel} disabled={loading}>
              Sign In
            </button>
          </div>
          <div className="toggle-panel toggle-right">
            <h1>Hello, Welcome!</h1>
            <p>Register with your personal details to use all of site features</p>
            <button className="hidden" onClick={togglePanel} disabled={loading}>
              Sign Up
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;