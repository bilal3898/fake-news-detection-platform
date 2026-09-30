import React from 'react';
import { Link } from 'react-router-dom';
// import './Footer.css';

const Footer = () => {
  return (
    <footer className="footer">
      <div className="footer-container">
        <p className="footer-text">&copy; {new Date().getFullYear()} Fake News Detector. All rights reserved.</p>
        <div className="footer-links">
          <Link to="/privacy">Privacy</Link>
          <Link to="/terms">Terms</Link>
          <Link to="/about">About</Link>
          <Link to="/home">Home</Link>
        </div>
      </div>
    </footer>
  );
};

export default Footer;