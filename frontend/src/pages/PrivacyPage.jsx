import React from 'react';
import './PrivacyPage.css';

const PrivacyPage = () => {
  return (
    <div className="privacy-page">
      <div className="privacy-container">
        <h1 className="privacy-title">Privacy Policy</h1>
        <div className="privacy-card">
          <p>
            We value your privacy and are committed to protecting your personal
            data. Our policy explains how we collect, use, and safeguard your
            information while ensuring transparency and trust.
          </p>
          <p>
            We never share your data with unauthorized third parties and follow
            industry standards to keep your information safe.
          </p>
          <button className="privacy-btn">Read Full Policy</button>
        </div>
      </div>
    </div>
  );
};

export default PrivacyPage;
