// src/App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import './App.css';
import './index.css';

// Pages
import HomePage from './pages/HomePage';
import Dashboard from './pages/dashboard';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ForgotPassword from './pages/ForgotPassword'; 
import ResetPassword from './pages/ResetPassword';
import AboutPage from './pages/AboutPage';
import PrivacyPage from './pages/PrivacyPage';
import TermsPage from './pages/TermsPage';
import NotFoundPage from './pages/NotFoundPage';
import Features from './pages/Features';  
import Contact from './pages/Contact';   

// Dashboard Pages
import AnalyzeNews from './pages/AnalyzeNews';
import Datasets from './pages/Datasets';
import ModelTraining from './pages/ModelTraining';
import Settings from './pages/Settings';
import Profile from './pages/profile';

// Components
import LoadingSpinner from './components/LoadingSpinner';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import DashboardLayout from './components/DashboardLayout';

/**
 * Main App Content
 */
function AppContent() {
  const { isAuthenticated, isLoading, isInitialized } = useAuth();
  const location = useLocation();

  const ProtectedRoute = ({ children }) => {
    if (isLoading || !isInitialized) {
      return <LoadingSpinner />;
    }
    return isAuthenticated ? children : <Navigate to="/login" replace />;
  };

  const PublicRoute = ({ children }) => {
    if (isLoading || !isInitialized) {
      return <LoadingSpinner />;
    }
    return !isAuthenticated ? children : <Navigate to="/dashboard" replace />;
  };

  const DashboardRoute = ({ children }) => {
    if (isLoading || !isInitialized) {
      return <LoadingSpinner />;
    }
    return isAuthenticated ? (
      <DashboardLayout>{children}</DashboardLayout>
    ) : (
      <Navigate to="/login" replace />
    );
  };

  if (isLoading || !isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  return (
    <div className="App min-h-screen flex flex-col">
      {/* Only show Navbar for non-dashboard routes */}
      {!location.pathname.startsWith('/dashboard') && <Navbar />}

      <main className={`flex-grow ${location.pathname.startsWith('/dashboard') ? '' : ''}`}>
        <Routes>
          {/* ✅ Root Route (conditional) */}
          <Route
            path="/"
            element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <HomePage />}
          />

          {/* Public Routes */}
          <Route path="/about" element={<AboutPage />} />
          <Route path="/features" element={<Features />} />
          <Route path="/privacy" element={<PrivacyPage />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="/terms" element={<TermsPage />} />

          {/* Auth Routes */}
          <Route
            path="/login"
            element={
              <PublicRoute>
                <LoginPage />
              </PublicRoute>
            }
          />
          <Route
            path="/register"
            element={
              <PublicRoute>
                <RegisterPage />
              </PublicRoute>
            }
          />

          {/* ✅ Forgot Password Route */}
          <Route
            path="/forgot-password"
            element={
              <PublicRoute>
                <ForgotPassword />
              </PublicRoute>
            }
          />

          {/* ✅ Reset Password Route */}
          <Route
            path="/reset-password"
            element={
              <PublicRoute>
                <ResetPassword />
              </PublicRoute>
            }
          />

          {/* Dashboard Routes with Layout */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />

          <Route
            path="/dashboard/analyze"
            element={
              <DashboardRoute>
                <AnalyzeNews />
              </DashboardRoute>
            }
          />

          <Route
            path="/dashboard/datasets"
            element={
              <DashboardRoute>
                <Datasets />
              </DashboardRoute>
            }
          />

          <Route
            path="/dashboard/training"
            element={
              <DashboardRoute>
                <ModelTraining />
              </DashboardRoute>
            }
          />

          <Route
            path="/dashboard/settings"
            element={
              <DashboardRoute>
                <Settings />
              </DashboardRoute>
            }
          />

          {/* ✅ New Profile Route */}
          <Route
            path="/dashboard/profile"
            element={
              <DashboardRoute>
                <Profile />
              </DashboardRoute>
            }
          />

          {/* Admin Routes */}
          <Route
            path="/admin/*"
            element={
              <ProtectedRoute>
                <div className="container mx-auto px-4 py-8">
                  <h1 className="text-2xl font-bold mb-4">Admin Panel</h1>
                  <p>Admin features coming soon...</p>
                </div>
              </ProtectedRoute>
            }
          />

          {/* 404 Page */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>

      <Footer />
    </div>
  );
}

/**
 * Root App Component with Providers
 */
function App() {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  );
}

export default App;