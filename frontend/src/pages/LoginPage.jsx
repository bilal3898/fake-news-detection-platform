import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import "./LoginPage.css";

const LoginPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    rememberMe: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === "checkbox" ? checked : value,
    });
    // Clear error when user starts typing
    if (error) setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.email || !formData.password) {
      setError("Please enter both email and password");
      return;
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setError("Please enter a valid email address");
      return;
    }

    try {
      setLoading(true);
      setError("");

      // AuthContext ke through login karo
      const result = await login(formData.email, formData.password, formData.rememberMe);

      if (result.success) {
        navigate("/dashboard");
      } else {
        setError(result.error || "Login failed!");
      }
    } catch (error) {
      setError("An unexpected error occurred. Please try again.");
      console.error("Login error:", error);
    } finally {
      setLoading(false);
    }
  };

  // Demo credentials for testing
  const fillDemoCredentials = () => {
    setFormData({
      email: "demo@example.com",
      password: "demopassword",
      rememberMe: false
    });
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <h2>Sign in to your account</h2>
          <p>Enter your credentials to continue</p>
        </div>

        {/* Demo Credentials Button */}
        <div className="demo-section">
          <button 
            type="button" 
            className="demo-btn"
            onClick={fillDemoCredentials}
          >
            Use Demo Credentials
          </button>
        </div>

        <div className="login-card">
          {error && (
            <div className="error-message">
              <span className="error-icon">⚠</span>
              {error}
            </div>
          )}

          <form className="form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="email">Email Address</label>
              <input
                id="email"
                name="email"
                type="email"
                required
                value={formData.email}
                onChange={handleChange}
                placeholder="you@example.com"
                disabled={loading}
                className={error ? "error-input" : ""}
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={formData.password}
                onChange={handleChange}
                placeholder="********"
                disabled={loading}
                className={error ? "error-input" : ""}
              />
            </div>

            <div className="forgot-password">
              <div className="remember">
                <input
                  id="rememberMe"
                  name="rememberMe"
                  type="checkbox"
                  checked={formData.rememberMe}
                  onChange={handleChange}
                  disabled={loading}
                />
                <label htmlFor="rememberMe">Remember me</label>
              </div>
              <Link to="/forgot-password" className="link">
                Forgot your password?
              </Link>
            </div>

            <button 
              type="submit" 
              className={`login-btn ${loading ? 'loading' : ''}`} 
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="spinner"></span>
                  Signing in...
                </>
              ) : (
                "Sign In"
              )}
            </button>
          </form>
        </div>

        <p className="footer-text">
          Don't have an account?{" "}
          <Link to="/register" className="link">
            Register here
          </Link>
        </p>
      </div>
    </div>
  );
};

export default LoginPage;