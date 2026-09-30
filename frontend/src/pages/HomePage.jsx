import React from 'react';
import { Link } from 'react-router-dom';
import './HomePage.css';

const HomePage = () => {
  return (
    <div className="home-page">
      <header className="hero-section">
        <div className="hero-content">
          <h1 className="hero-title">Welcome to Fake News Detector</h1>
          <p className="hero-subtitle">
            Verify news authenticity instantly using our AI-powered platform.
          </p>
          <div className="hero-buttons">
            <Link to="/register" className="btn-primary">Get Started</Link>
            <Link to="/about" className="btn-secondary">Learn More</Link>
          </div>
        </div>
      </header>

      <section className="features">
        <h2 className="section-title">Why Choose Us</h2>
        <div className="feature-grid">
          <div className="feature-card">
            <h3>AI-Powered Detection</h3>
            <p>Our advanced algorithms analyze content and flag potential misinformation in seconds.</p>
          </div>
          <div className="feature-card">
            <h3>Real-Time Verification</h3>
            <p>Get instant results with accurate and reliable verification tools for trending news.</p>
          </div>
          <div className="feature-card">
            <h3>Secure & Private</h3>
            <p>Your data and searches are safe with industry-leading security measures.</p>
          </div>
        </div>
      </section>

      <footer className="home-footer">
        <p>&copy; {new Date().getFullYear()} Fake News Detector. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default HomePage;