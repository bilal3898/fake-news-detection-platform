// src/components/DashboardLayout.jsx
import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './DashboardLayout.css';

const DashboardLayout = ({ children }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const menuItems = [
    { path: '/dashboard', icon: '📊', label: 'Overview', exact: true },
    { path: '/dashboard/analyze', icon: '🔍', label: 'Analyze News' },
    { path: '/dashboard/datasets', icon: '📁', label: 'Datasets' },
    { path: '/dashboard/training', icon: '🤖', label: 'Model Training' },
    { path: '/dashboard/settings', icon: '⚙️', label: 'Settings' },
  ];

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const isActive = (path, exact = false) => {
    return exact ? location.pathname === path : location.pathname.startsWith(path);
  };

  return (
    <div className="dashboard-layout">
      {/* Sidebar */}
      <aside className={`sidebar ${isSidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <h2>Fake News Detector</h2>
          <button 
            className="toggle-btn"
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          >
            {isSidebarOpen ? '◀' : '▶'}
          </button>
        </div>

        <nav className="sidebar-nav">
          {menuItems.map(item => (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-item ${isActive(item.path, item.exact) ? 'active' : ''}`}
            >
              <span className="nav-icon">{item.icon}</span>
              {isSidebarOpen && <span className="nav-label">{item.label}</span>}
            </Link>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">
              {user?.name?.charAt(0) || user?.email?.charAt(0) || 'U'}
            </div>
            {isSidebarOpen && (
              <div className="user-details">
                <span className="user-name">{user?.name || 'User'}</span>
                <span className="user-email">{user?.email}</span>
              </div>
            )}
          </div>
          <button className="logout-btn" onClick={handleLogout}>
            <span className="logout-icon">🚪</span>
            {isSidebarOpen && <span>Logout</span>}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="dashboard-main">
        <header className="dashboard-header">
          <div className="header-left">
            <h1>
              {menuItems.find(item => isActive(item.path, item.exact))?.label || 'Dashboard'}
            </h1>
          </div>
          <div className="header-right">
            <span className="welcome-text">Welcome, {user?.name || 'User'}!</span>
          </div>
        </header>

        <div className="dashboard-content">
          {children}
        </div>
      </main>
    </div>
  );
};

export default DashboardLayout;