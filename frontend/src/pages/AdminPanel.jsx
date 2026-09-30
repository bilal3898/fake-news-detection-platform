// src/pages/AdminPanel.jsx
import React from 'react';
import { withRole } from '../contexts/AuthContext';

const AdminPanel = () => {
  return (
    <div>Admin Panel</div>
  );
};

export default withRole(AdminPanel, 'admin');