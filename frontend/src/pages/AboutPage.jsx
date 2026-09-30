import React from 'react';
import './AboutPage.css'; // custom CSS import

const AboutPage = () => {
  return (
    <div className="about-page">
      <div className="about-container">
        <h1 className="about-title">About Fake News Detector</h1>
        <div className="about-card">
          <p>
            Fake News Detector is a cutting-edge platform that helps users
            identify and analyze potentially misleading information online.
            Using advanced AI algorithms and real-time verification tools, we
            aim to promote responsible sharing and informed decision-making.
          </p>
          <p>
            Our mission is to empower individuals, journalists, and
            organizations with reliable insights and promote digital literacy.
          </p>
          <button className="about-btn">Learn More</button>
        </div>
      </div>
    </div>
  );
};

export default AboutPage;
