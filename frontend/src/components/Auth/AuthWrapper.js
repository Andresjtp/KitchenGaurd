import React, { useState } from 'react';
import Login from './Login';
import Register from './Register';
import ForgotPassword from './ForgotPassword';

const AuthWrapper = ({ onAuthSuccess }) => {
  const [currentView, setCurrentView] = useState('login'); // 'login', 'register', 'forgot-password'

  const handleLogin = async (username, password) => {
    try {
      const response = await fetch('http://localhost:8000/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': 'kitchenguard-api-key'
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Login failed');
      }

      // Store user session
      localStorage.setItem('kitchenguard_user', JSON.stringify(data.user));
      localStorage.setItem('kitchenguard_token', data.token);
      
      // Call the success handler
      onAuthSuccess(data.user);
    } catch (error) {
      throw new Error(error.message || 'Invalid username or password');
    }
  };

  const handleRegister = async (userData) => {
    try {
      const response = await fetch('http://localhost:8000/api/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': 'kitchenguard-api-key'
        },
        body: JSON.stringify(userData),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Registration failed');
      }

      // Store user session (auto-login after registration)
      localStorage.setItem('kitchenguard_user', JSON.stringify(data.user));
      localStorage.setItem('kitchenguard_token', data.token);
      
      // Call the success handler
      onAuthSuccess(data.user);
    } catch (error) {
      throw new Error(error.message || 'Registration failed. Please try again.');
    }
  };

  const handleResetPassword = async (email) => {
    try {
      const response = await fetch('http://localhost:8000/api/reset-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': 'kitchenguard-api-key'
        },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to send reset email');
      }

      // Password reset email sent (or would be sent in production)
      console.log('Password reset initiated for:', email);
    } catch (error) {
      throw new Error(error.message || 'Failed to send reset email. Please try again.');
    }
  };

  const renderCurrentView = () => {
    switch (currentView) {
      case 'login':
        return (
          <Login
            onSwitchToRegister={() => setCurrentView('register')}
            onSwitchToForgotPassword={() => setCurrentView('forgot-password')}
            onLogin={handleLogin}
          />
        );
      case 'register':
        return (
          <Register
            onSwitchToLogin={() => setCurrentView('login')}
            onRegister={handleRegister}
          />
        );
      case 'forgot-password':
        return (
          <ForgotPassword
            onSwitchToLogin={() => setCurrentView('login')}
            onResetPassword={handleResetPassword}
          />
        );
      default:
        return null;
    }
  };

  return renderCurrentView();
};

export default AuthWrapper;