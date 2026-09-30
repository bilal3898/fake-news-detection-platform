import React from 'react';
import './TermsPage.css';

const TermsPage = () => {
  return (
    <div className="terms-page">
      <div className="terms-container">
        <h1 className="terms-title">Terms of Service</h1>
        <div className="terms-card">
          <p>
            By using our platform, you agree to comply with and be bound by the
            following terms and conditions. Please review them carefully before
            using our services.
          </p>
          <p>
            We reserve the right to modify these terms at any time to reflect
            changes in our practices or for other operational, legal, or
            regulatory reasons.
          </p>
          <button className="terms-btn">View Full Terms</button>
        </div>
      </div>
    </div>
  );
};

export default TermsPage;
