import React from "react";
import "./Features.css";

const Features = () => {
  const featureList = [
    {
      title: "Real-Time Prediction",
      desc: "Analyze any news article URL and instantly detect whether it is real or fake.",
      icon: "⚡",
    },
    {
      title: "Multi-Model Analysis",
      desc: "Uses Kaggle, TF-IDF, LSTM, and other AI models to ensure accurate predictions.",
      icon: "🧠",
    },
    {
      title: "URL + Text Support",
      desc: "Predict authenticity using article text or entire web URLs.",
      icon: "🔗",
    },
    {
      title: "Detailed Confidence Scores",
      desc: "Displays prediction confidence, probabilities, and model insights.",
      icon: "📊",
    },
    {
      title: "User Activity Tracking",
      desc: "Secure dashboard showing all past predictions with timestamps.",
      icon: "🗂️",
    },
    {
      title: "Secure Authentication",
      desc: "Token-based login system with email verification for added security.",
      icon: "🔒",
    }
  ];

  return (
    <section className="features-section">
      <h2 className="features-heading">Powerful Features</h2>
      <p className="features-subheading">
        Explore what makes our Fake News Detection Platform smarter and reliable.
      </p>

      <div className="features-container">
        {featureList.map((item, idx) => (
          <div key={idx} className="feature-card">
            <div className="feature-icon">{item.icon}</div>
            <h3 className="feature-title">{item.title}</h3>
            <p className="feature-desc">{item.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
};

export default Features;
