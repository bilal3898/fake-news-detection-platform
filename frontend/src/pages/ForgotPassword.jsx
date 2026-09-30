import React, { useState } from 'react';
import './ForgotPassword.css';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email) {
      alert('Please enter your email address.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/request-password-reset', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email })
      });

      const data = await response.json();

      if (response.ok) {
        // Successful request
        setSubmitted(true);
      } else {
        // Backend returned error
        setError(data.detail || 'Something went wrong. Try again.');
      }
    } catch (err) {
      setError('Network error. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="forgot-page">
      <div className="forgot-container">
        <div className="forgot-header">
          <h2>Forgot Your Password?</h2>
          <p>Enter your email address to reset your password.</p>
        </div>

        {!submitted ? (
          <div className="forgot-card">
            <form onSubmit={handleSubmit} className="forgot-form">
              <label htmlFor="email">Email Address</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
              />
              <button type="submit" className="forgot-btn" disabled={loading}>
                {loading ? 'Sending...' : 'Send Reset Link'}
              </button>
              {error && <p className="error-msg">{error}</p>}
            </form>
          </div>
        ) : (
          <div className="forgot-success">
            <h3>Check Your Inbox!</h3>
            <p>
              If an account exists with <span>{email}</span>, you'll receive a
              password reset link shortly.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ForgotPassword;