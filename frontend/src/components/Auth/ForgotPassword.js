import React, { useState } from 'react';
import './Auth.css';

const ForgotPassword = ({ onSwitchToLogin, onResetPassword }) => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleInputChange = (e) => {
    setEmail(e.target.value);
    // Clear error when user starts typing
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!email.trim()) {
      setError('Please enter your email address');
      return;
    }

    if (!email.includes('@')) {
      setError('Please enter a valid email address');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Call the parent component's reset password handler
      await onResetPassword(email);
      setSuccess(true);
    } catch (err) {
      setError(err.message || 'Failed to send reset email. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <div className="auth-header">
            <div className="logo">
              🍽️ KitchenGuard
            </div>
            <h2>Check Your Email</h2>
            <p>We've sent password reset instructions to:</p>
            <strong>{email}</strong>
          </div>

          <div className="success-message">
            <div className="success-icon">📧</div>
            <p>If an account exists with this email, you'll receive a password reset link shortly.</p>
            <p>Don't forget to check your spam folder!</p>
          </div>

          <button 
            type="button" 
            className="auth-button primary"
            onClick={onSwitchToLogin}
          >
            Back to Sign In
          </button>

          <div className="auth-links">
            <button 
              type="button" 
              className="link-button"
              onClick={() => {
                setSuccess(false);
                setEmail('');
              }}
            >
              Try a different email address
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <div className="logo">
            🍽️ KitchenGuard
          </div>
          <h2>Reset Your Password</h2>
          <p>Enter your email address and we'll send you a link to reset your password</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              name="email"
              value={email}
              onChange={handleInputChange}
              placeholder="Enter your email address"
              disabled={loading}
              autoComplete="email"
            />
          </div>

          <button 
            type="submit" 
            className="auth-button primary"
            disabled={loading}
          >
            {loading ? 'Sending Reset Link...' : 'Send Reset Link'}
          </button>
        </form>

        <div className="auth-links">
          <button 
            type="button" 
            className="link-button"
            onClick={onSwitchToLogin}
          >
            ← Back to Sign In
          </button>
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;