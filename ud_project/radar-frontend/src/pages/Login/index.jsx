import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppLogo from '../../assets/images/RR_logo2.png';
import { getLoginDetails } from '../../Util';

const LoginPage = () => {
  const [loginData, setLoginData] = useState({
    email: '',
    password: '',
  });
  const [isDisabled, setIsDisabled] = useState(false);
  const [errors, setErrors] = useState({
    email: '',
    password: '',
  });
  const [hasError, setHasError] = useState('');

  const navigate = useNavigate();

  const validateEmail = (email) => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(String(email).toLowerCase());
  };

  const validateInputs = () => {
    const newErrors = {};
    if (!loginData.email) {
      newErrors.email = 'Please enter your email';
    } else if (!validateEmail(loginData.email)) {
      newErrors.email = 'Please enter a valid email';
    }

    if (!loginData.password) {
      newErrors.password = 'Please enter your password';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleLogin = (event) => {
    if (event.key === 'Enter' || event.type === 'click') {
      event.preventDefault(); // Prevent form submission
      if (!validateInputs()) {
        return;
      }
      setIsDisabled(true);
      getLoginDetails(loginData)
        .then((res) => {
          const user = res.user;
          if (user?.role && user?.role === 'Officer') {
            navigate('/category-details');
          } else if (user?.role === 'SeniorLeader') {
            navigate('/dashboard');
          }
        })
        .catch((e) => {
          console.log('e==', e);
          setHasError(e);
          setIsDisabled(false);
        });
    }
  };

  const handleChanges = (e) => {
    setHasError('');
    const { name, value } = e.target;
    setLoginData((prev) => ({ ...prev, [name]: value }));
  };

  return (
    <div className="login-wrapper">
      <div className="intro-box">
        <img src={AppLogo} alt="App Logo" />
      </div>
      <div className="login-box">
        <div className="login-inputs">
          <h3>Sign In</h3>
          <input
            type="text"
            placeholder="Email"
            name="email"
            value={loginData.email}
            onChange={handleChanges}
            onKeyDown={handleLogin} 
            className={errors.email ? 'error' : null}
          />
          {errors.email && <div className="error-message">{errors.email}</div>}
          <input
            type="password"
            placeholder="Password"
            name="password"
            value={loginData.password}
            onChange={handleChanges}
            onKeyDown={handleLogin}
            className={errors.password ? 'error' : null}
          />
          {errors.password && <div className="error-message">{errors.password}</div>}

          <div className={!!hasError ? "error-container" : 'hide'}>
            <i className='pi pi-info-circle' style={{ color: '#F12D2D', fontSize: 20 }}></i>{hasError}
          </div>
          <div className="forget-password">
            Forgot Password?
          </div>
          <button className="btn btn-light" onClick={handleLogin} disabled={isDisabled} type='submit'>
            Login
          </button>
        </div>
        <div className="or">Or</div>
        <button className="btn btn-outline-light w-100" disabled>
          Sign in with SSO
        </button>
      </div>
    </div>
  );
};

export default LoginPage;
