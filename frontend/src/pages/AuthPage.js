import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';

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
  const location = useLocation();

  // Handle URL parameters to show correct form
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const formType = searchParams.get('form');

    if (formType === 'register') {
      setIsActive(true); // Show register form
    } else if (formType === 'login') {
      setIsActive(false); // Show login form
    }
  }, [location]);

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

  const togglePasswordVisibility = (field) => {
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
    <div className={`auth-container ${isActive ? 'active' : ''}`} id="container">
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
              placeholder="First Name"
              value={registerData.first_name}
              onChange={(e) => handleRegisterChange('first_name', e.target.value)}
              required
            />
            <input
              type="text"
              placeholder="Last Name"
              value={registerData.last_name}
              onChange={(e) => handleRegisterChange('last_name', e.target.value)}
              required
            />
          </div>

          <input
            type="email"
            placeholder="Email"
            value={registerData.email}
            onChange={(e) => handleRegisterChange('email', e.target.value)}
            required
          />
          <input
            type="text"
            placeholder="Phone (optional)"
            value={registerData.phone}
            onChange={(e) => handleRegisterChange('phone', e.target.value)}
          />
          <input
            type="text"
            placeholder="Username (optional)"
            value={registerData.username}
            onChange={(e) => handleRegisterChange('username', e.target.value)}
          />

          <div className="password-field">
            <input
              type={showPassword.register ? "text" : "password"}
              placeholder="Password"
              value={registerData.password}
              onChange={(e) => handleRegisterChange('password', e.target.value)}
              required
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
              placeholder="Confirm Password"
              value={registerData.confirm_password}
              onChange={(e) => handleRegisterChange('confirm_password', e.target.value)}
              required
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
            placeholder="Email, Phone or Username"
            value={loginData.login_id}
            onChange={(e) => handleLoginChange('login_id', e.target.value)}
            required
          />

          <div className="password-field">
            <input
              type={showPassword.login ? "text" : "password"}
              placeholder="Password"
              value={loginData.password}
              onChange={(e) => handleLoginChange('password', e.target.value)}
              required
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
            <button className="hidden" onClick={togglePanel}>Sign In</button>
          </div>
          <div className="toggle-panel toggle-right">
            <h1>Hello, Welcome!</h1>
            <p>Register with your personal details to use all of site features</p>
            <button className="hidden" onClick={togglePanel}>Sign Up</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;