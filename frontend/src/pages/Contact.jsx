import React from 'react';
import './Contact.css';

const Contact = () => {
  return (
    <div className="contact-page">
      <div className="contact-container">
        <h1 className="contact-title">Contact Me</h1>
        <p className="contact-subtitle">
          Feel free to reach out for queries, collaborations, or project discussions.
        </p>

        <div className="contact-grid">

          <div className="contact-card">
            <h3>📞 Phone</h3>
            <p>8392905339</p>
          </div>

          <div className="contact-card">
            <h3>📧 Email</h3>
            <p>bilalpasha607@gmail.com</p>
          </div>

          <div className="contact-card">
            <h3>📸 Instagram</h3>
            <a href="https://instagram.com/bilal__pashaa" target="_blank" rel="noreferrer">
              instagram.com/bilal__pashaa
            </a>
          </div>

          <div className="contact-card">
            <h3>🐦 Twitter (X)</h3>
            <a href="https://x.com/Bilal__Pasha" target="_blank" rel="noreferrer">
              x.com/Bilal__Pasha
            </a>
          </div>

          <div className="contact-card">
            <h3>💼 LinkedIn</h3>
            <a href="https://linkedin.com/in/bilal3898" target="_blank" rel="noreferrer">
              linkedin.com/in/bilal3898
            </a>
          </div>

          <div className="contact-card">
            <h3>📘 Facebook</h3>
            <a href="https://facebook.com/bilalpasha3898" target="_blank" rel="noreferrer">
              facebook.com/bilalpasha3898
            </a>
          </div>

        </div>
      </div>
    </div>
  );
};

export default Contact;