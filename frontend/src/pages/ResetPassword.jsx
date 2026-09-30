import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import './ResetPassword.css';

const ResetPassword = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const params = new URLSearchParams(location.search);
  const token = params.get('token');

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!newPassword || !confirmPassword) {
      alert('Please fill all fields');
      return;
    }
    if (newPassword !== confirmPassword) {
      alert("Passwords don't match");
      return;
    }

    try {
      await axios.post('http://localhost:8000/api/v1/auth/reset-password', {
        token,
        new_password: newPassword
      });
      setSuccess(true);
    } catch (error) {
      console.error(error);
      alert('Failed to reset password. Link may have expired.');
    }
  };

  if (success) {
    return (
      <div className="reset-success">
        <h2>Password Reset Successfully!</h2>
        <button onClick={() => navigate('/login')}>Go to Login</button>
      </div>
    );
  }

  return (
    <div className="reset-page">
      <div className="reset-container">
        <h2>Reset Your Password</h2>
        <form onSubmit={handleSubmit} className="reset-form">
          <label>New Password</label>
          <input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="Enter new password"
            required
          />
          <label>Confirm Password</label>
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Confirm new password"
            required
          />
          <button type="submit">Reset Password</button>
        </form>
      </div>
    </div>
  );
};

export default ResetPassword;