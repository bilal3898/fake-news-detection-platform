import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Navbar = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isProfileDropdownOpen, setIsProfileDropdownOpen] = useState(false);
  const { isAuthenticated, user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
      setIsMenuOpen(false);
      setIsProfileDropdownOpen(false);
      navigate('/');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const isActive = (path) => location.pathname === path;

  const closeAllMenus = () => {
    setIsMenuOpen(false);
    setIsProfileDropdownOpen(false);
  };

  // Navigation items
  const navItems = [
    { path: '/', label: 'Home' },
    { path: '/about', label: 'About' },
    { path: '/features', label: 'Features' },
    { path: '/contact', label: 'Contact' },
  ];

  const authNavItems = isAuthenticated
    ? [
        { path: '/dashboard', label: 'Dashboard' },
        { path: '/analyze', label: 'Analyze' },
        { path: '/history', label: 'History' },
      ]
    : [];

  return (
    <nav className="bg-white shadow-lg sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo Section */}
          <div className="flex items-center space-x-3">
            <Link 
              to="/" 
              className="flex items-center space-x-3"
              onClick={closeAllMenus}
            >
              <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-md">
                <span className="text-white font-bold text-lg">FND</span>
              </div>
              <div className="flex flex-col">
                <span className="text-xl font-bold text-gray-900 leading-tight">
                  FakeNewsDetector
                </span>
                <span className="text-xs text-gray-500 -mt-1">
                  AI-Powered Verification
                </span>
              </div>
            </Link>
          </div>

          {/* Desktop Navigation - Center */}
          <div className="hidden lg:flex items-center space-x-1">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                  isActive(item.path)
                    ? 'text-blue-600 bg-blue-50 border border-blue-100'
                    : 'text-gray-700 hover:text-blue-600 hover:bg-gray-50'
                }`}
              >
                {item.label}
              </Link>
            ))}
            
            {isAuthenticated && authNavItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                  isActive(item.path)
                    ? 'text-blue-600 bg-blue-50 border border-blue-100'
                    : 'text-gray-700 hover:text-blue-600 hover:bg-gray-50'
                }`}
              >
                {item.label}
              </Link>
            ))}
          </div>

          {/* Desktop Navigation - Right */}
          <div className="hidden lg:flex items-center space-x-4">
            {isAuthenticated ? (
              <>
                {/* Notifications Bell */}
                <button className="relative p-2 text-gray-600 hover:text-blue-600 hover:bg-gray-50 rounded-lg transition-colors">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5 5v-5zM10.5 3.75a6 6 0 010 8.25m11.5 0A8.98 8.98 0 0018 10a9 9 0 10-9 9" />
                  </svg>
                  <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
                </button>

                {/* Profile Dropdown */}
                <div className="relative">
                  <button
                    onClick={() => setIsProfileDropdownOpen(!isProfileDropdownOpen)}
                    className="flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-sm font-semibold">
                      {user?.name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || 'U'}
                    </div>
                    <div className="flex items-center space-x-1">
                      <span className="text-sm font-medium text-gray-900 max-w-32 truncate">
                        {user?.name || user?.email}
                      </span>
                      <svg 
                        className={`w-4 h-4 text-gray-500 transition-transform ${isProfileDropdownOpen ? 'rotate-180' : ''}`} 
                        fill="none" 
                        stroke="currentColor" 
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  </button>

                  {/* Dropdown Menu */}
                  {isProfileDropdownOpen && (
                    <div className="absolute right-0 mt-2 w-64 bg-white rounded-xl shadow-lg border border-gray-200 py-2 z-50">
                      {/* User Info */}
                      <div className="px-4 py-3 border-b border-gray-100">
                        <p className="text-sm font-semibold text-gray-900 truncate">
                          {user?.name || 'User'}
                        </p>
                        <p className="text-sm text-gray-500 truncate">
                          {user?.email}
                        </p>
                      </div>
                      
                      {/* Menu Items */}
                      <div className="py-2">
                        <Link
                          to="/dashboard/profile"
                          className="flex items-center space-x-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                          onClick={() => setIsProfileDropdownOpen(false)}
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                          </svg>
                          <span>Profile Settings</span>
                        </Link>
                        
                        <Link
                          to="/dashboard/settings"
                          className="flex items-center space-x-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                          onClick={() => setIsProfileDropdownOpen(false)}
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                          <span>Settings</span>
                        </Link>
                        
                        <Link
                          to="/dashboard/history"
                          className="flex items-center space-x-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                          onClick={() => setIsProfileDropdownOpen(false)}
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <span>Analysis History</span>
                        </Link>
                      </div>
                      
                      {/* Logout */}
                      <div className="border-t border-gray-100 pt-2">
                        <button
                          onClick={handleLogout}
                          className="flex items-center space-x-3 w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                          </svg>
                          <span>Logout</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="flex items-center space-x-3">
                <Link
                  to="/login"
                  className="px-4 py-2 text-gray-700 font-medium hover:text-blue-600 transition-colors"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all shadow-md hover:shadow-lg"
                >
                  Get Started
                </Link>
              </div>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="lg:hidden flex items-center">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
              aria-label="Toggle menu"
            >
              <div className="w-6 h-6 relative">
                <span 
                  className={`absolute left-0 top-1/2 w-6 h-0.5 bg-gray-700 transform transition-all duration-300 ${
                    isMenuOpen ? 'rotate-45 translate-y-0' : '-translate-y-2'
                  }`}
                ></span>
                <span 
                  className={`absolute left-0 top-1/2 w-6 h-0.5 bg-gray-700 transition-all duration-300 ${
                    isMenuOpen ? 'opacity-0' : 'opacity-100'
                  }`}
                ></span>
                <span 
                  className={`absolute left-0 top-1/2 w-6 h-0.5 bg-gray-700 transform transition-all duration-300 ${
                    isMenuOpen ? '-rotate-45 translate-y-0' : 'translate-y-2'
                  }`}
                ></span>
              </div>
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <div className="lg:hidden border-t border-gray-200 bg-white">
            <div className="py-4 space-y-1">
              {/* Main Navigation */}
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center space-x-3 px-4 py-3 rounded-lg mx-2 transition-all ${
                    isActive(item.path)
                      ? 'text-blue-600 bg-blue-50 border border-blue-100'
                      : 'text-gray-700 hover:text-blue-600 hover:bg-gray-50'
                  }`}
                  onClick={closeAllMenus}
                >
                  <span>{item.label}</span>
                </Link>
              ))}
              
              {/* Authenticated Navigation */}
              {isAuthenticated && authNavItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center space-x-3 px-4 py-3 rounded-lg mx-2 transition-all ${
                    isActive(item.path)
                      ? 'text-blue-600 bg-blue-50 border border-blue-100'
                      : 'text-gray-700 hover:text-blue-600 hover:bg-gray-50'
                  }`}
                  onClick={closeAllMenus}
                >
                  <span>{item.label}</span>
                </Link>
              ))}
              
              {/* Auth Section */}
              <div className="border-t border-gray-200 pt-4 mt-4">
                {isAuthenticated ? (
                  <>
                    <Link
                      to="/dashboard/profile"
                      className="flex items-center space-x-3 px-4 py-3 text-gray-700 hover:text-blue-600 hover:bg-gray-50 rounded-lg mx-2 transition-colors"
                      onClick={closeAllMenus}
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                      <span>Profile</span>
                    </Link>
                    
                    <button
                      onClick={handleLogout}
                      className="flex items-center space-x-3 w-full px-4 py-3 text-red-600 hover:bg-red-50 rounded-lg mx-2 transition-colors text-left"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                      </svg>
                      <span>Logout</span>
                    </button>
                  </>
                ) : (
                  <div className="space-y-2 px-2">
                    <Link
                      to="/login"
                      className="block px-4 py-3 text-center text-gray-700 font-medium border border-gray-300 rounded-lg hover:border-blue-600 hover:text-blue-600 transition-colors"
                      onClick={closeAllMenus}
                    >
                      Login
                    </Link>
                    <Link
                      to="/register"
                      className="block px-4 py-3 text-center bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all shadow-md"
                      onClick={closeAllMenus}
                    >
                      Get Started Free
                    </Link>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Backdrop for mobile menu */}
      {isMenuOpen && (
        <div 
          className="lg:hidden fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={closeAllMenus}
        ></div>
      )}
    </nav>
  );
};

export default Navbar;