// src/pages/RegisterPage.jsx
import React, { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { authAPI } from "../services/api";
import "./RegisterPage.css";

const RegisterPage = () => {
  const navigate = useNavigate();
  const { login, isAuthenticated } = useAuth();
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phoneNumber: "",
    password: "",
    confirmPassword: "",
    termsAccepted: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [passwordStrength, setPasswordStrength] = useState("");
  const [showOTPModal, setShowOTPModal] = useState(false);
  const [emailOtp, setEmailOtp] = useState(["", "", "", "", "", ""]);
  const [smsOtp, setSmsOtp] = useState(["", "", "", "", "", ""]);
  const [otpLoading, setOtpLoading] = useState(false);
  const [otpError, setOtpError] = useState("");
  const [resendTimer, setResendTimer] = useState(0);
  const [tempUserData, setTempUserData] = useState(null);
  const [devOtp, setDevOtp] = useState({ email: "", sms: "" });

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate("/dashboard");
    }
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    let timer;
    if (resendTimer > 0) {
      timer = setTimeout(() => setResendTimer(resendTimer - 1), 1000);
    }
    return () => clearTimeout(timer);
  }, [resendTimer]);

  // Safe error handler
  const handleError = (error, context) => {
    console.error(`Error in ${context}:`, error);
    
    let errorMessage = 'An unexpected error occurred';
    
    if (typeof error === 'string') {
      errorMessage = error;
    } else if (error?.message) {
      errorMessage = error.message;
    } else if (error?.detail) {
      errorMessage = error.detail;
    } else if (error?.msg) {
      errorMessage = error.msg;
    } else if (Array.isArray(error)) {
      errorMessage = error.map(err => {
        if (typeof err === 'string') return err;
        if (err?.msg) return err.msg;
        if (err?.message) return err.message;
        if (err?.loc && err?.msg) return `${err.loc.join('.')}: ${err.msg}`;
        return 'Validation error';
      }).join(', ');
    } else if (typeof error === 'object') {
      try {
        if (error.loc && error.msg && error.type) {
          errorMessage = `${error.loc.join('.')}: ${error.msg}`;
        } else {
          errorMessage = 'Validation error occurred';
        }
      } catch {
        errorMessage = 'An error occurred';
      }
    }
    
    return errorMessage;
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === "checkbox" ? checked : value,
    });

    if (error) setError("");

    if (name === "password") {
      checkPasswordStrength(value);
    }
  };

  const checkPasswordStrength = (password) => {
    const strongRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
    const mediumRegex = /^(?=.*[a-zA-Z])(?=.*\d)[A-Za-z\d]{8,}$/;

    if (strongRegex.test(password)) {
      setPasswordStrength("strong");
    } else if (mediumRegex.test(password)) {
      setPasswordStrength("medium");
    } else if (password.length > 0) {
      setPasswordStrength("weak");
    } else {
      setPasswordStrength("");
    }
  };

  const validateForm = () => {
    if (!formData.name || !formData.email || !formData.password || !formData.confirmPassword) {
      setError("All fields are required");
      return false;
    }

    if (formData.name.length < 2) {
      setError("Name must be at least 2 characters long");
      return false;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setError("Please enter a valid email address");
      return false;
    }

    if (formData.password.length < 8) {
      setError("Password must be at least 8 characters long");
      return false;
    }

    if (!/(?=.*[a-z])/.test(formData.password)) {
      setError("Password must contain at least one lowercase letter");
      return false;
    }
    if (!/(?=.*[A-Z])/.test(formData.password)) {
      setError("Password must contain at least one uppercase letter");
      return false;
    }
    if (!/(?=.*\d)/.test(formData.password)) {
      setError("Password must contain at least one number");
      return false;
    }

    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match");
      return false;
    }

    if (!formData.termsAccepted) {
      setError("You must accept the terms and conditions");
      return false;
    }

    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      setLoading(true);
      setError("");

      const otpRequestData = {
        email: formData.email,
        full_name: formData.name,
        phone_number: formData.phoneNumber || null,
      };

      console.log("📧 Sending OTP request:", otpRequestData);

      const result = await authAPI.register(otpRequestData);

      console.log("📨 OTP Response received:", result);
      console.log("🔍 Checking response conditions:");
      console.log("   - result.email_sent:", result.email_sent);
      console.log("   - result.message:", result.message);

      // Check success conditions based on actual backend response structure
      const isSuccess = result.email_sent || 
                       (result.message && result.message.toLowerCase().includes('success')) ||
                       (result.message && result.message.toLowerCase().includes('sent'));

      console.log("✅ Is success?", isSuccess);

      if (isSuccess) {
        console.log("🎯 SUCCESS: Opening OTP modal...");
        
        setTempUserData({
          email: formData.email,
          password: formData.password,
          full_name: formData.name,
          phone_number: formData.phoneNumber || null,
        });
        
        // Store development OTPs if available
        if (result.development_otp) {
          setDevOtp(prev => ({ ...prev, email: result.development_otp }));
          console.log("📧 Development Email OTP:", result.development_otp);
        }
        if (result.sms_development_otp) {
          setDevOtp(prev => ({ ...prev, sms: result.sms_development_otp }));
          console.log("📱 Development SMS OTP:", result.sms_development_otp);
        }
        
        // OPEN THE MODAL
        setShowOTPModal(true);
        setResendTimer(30);
        
        console.log("✅ OTP modal state set to:", true);
        
        // Auto-fill OTPs in development mode
        if (process.env.NODE_ENV === 'development') {
          setTimeout(() => {
            console.log("🔄 Auto-filling OTPs...");
            if (result.development_otp) {
              const otpArray = result.development_otp.split('').slice(0, 6);
              setEmailOtp(otpArray);
              console.log("✅ Auto-filled email OTP:", otpArray);
            }
            if (result.sms_development_otp) {
              const smsOtpArray = result.sms_development_otp.split('').slice(0, 6);
              setSmsOtp(smsOtpArray);
              console.log("✅ Auto-filled SMS OTP:", smsOtpArray);
            }
          }, 100);
        }
      } else {
        const errorMsg = result.message || result.detail || result.error || "Failed to send OTP";
        console.error("❌ OTP request failed:", errorMsg);
        setError(errorMsg);
      }
    } catch (error) {
      console.error("❌ OTP request exception:", error);
      const errorMsg = handleError(error, 'OTP request');
      setError(errorMsg || "An unexpected error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleOtpChange = (otpArray, setOtpArray, type, index, value) => {
    if (value.length <= 1 && /^\d*$/.test(value)) {
      const newOtp = [...otpArray];
      newOtp[index] = value;
      setOtpArray(newOtp);

      // Auto-focus next input
      if (value && index < 5) {
        const nextInput = document.getElementById(`otp-${type}-${index + 1}`);
        if (nextInput) nextInput.focus();
      }
    }
  };

  const handleOtpKeyDown = (otpArray, setOtpArray, type, index, e) => {
    if (e.key === "Backspace" && !otpArray[index] && index > 0) {
      const prevInput = document.getElementById(`otp-${type}-${index - 1}`);
      if (prevInput) prevInput.focus();
    }
  };

  const handleVerifyOTP = async () => {
    const emailOtpString = emailOtp.join("");
    const smsOtpString = smsOtp.join("");
    
    if (emailOtpString.length !== 6) {
      setOtpError("Please enter 6-digit Email OTP");
      return;
    }

    if (tempUserData.phone_number && smsOtpString.length !== 6) {
      setOtpError("Please enter 6-digit SMS OTP");
      return;
    }

    try {
      setOtpLoading(true);
      setOtpError("");

      const verifyData = {
        email: tempUserData.email,
        email_otp: emailOtpString,
        phone_number: tempUserData.phone_number,
        sms_otp: tempUserData.phone_number ? smsOtpString : null,
      };

      console.log("🔐 Verifying OTP:", verifyData);

      let verifyResult;
      try {
        // Try the new method name first
        verifyResult = await authAPI.verifyRegistrationOTP(verifyData);
      } catch (error) {
        // Fallback to old method name
        console.warn('⚠️ verifyRegistrationOTP not found, falling back to verifyOTP');
        verifyResult = await authAPI.verifyOTP(verifyData);
      }

      console.log("✅ OTP Verification Response:", verifyResult);        

      if (verifyResult.success || verifyResult.verified || verifyResult.ready_for_registration) {
        const completeData = {
          email: tempUserData.email,
          password: tempUserData.password,
          full_name: tempUserData.full_name,
          phone_number: tempUserData.phone_number,
          email_otp: emailOtpString,
          sms_otp: tempUserData.phone_number ? smsOtpString : null,
        };

        console.log("🚀 Completing registration:", completeData);

        const completeResult = await authAPI.completeRegistration(completeData);

        console.log("✅ Registration Complete Response:", completeResult);
        
        if (completeResult.success || completeResult.message) {
          try {
            console.log("🔐 Attempting auto-login...");
            const loginResult = await login(tempUserData.email, tempUserData.password);
            
            if (loginResult.success) {
              console.log("✅ Auto-login successful, redirecting to dashboard");
              alert("Registration completed successfully! Welcome to our platform.");
              navigate("/dashboard");
            } else {
              console.log("⚠️ Auto-login failed, redirecting to login page");
              alert("Registration completed! Please login with your credentials.");
              navigate("/login");
            }
          } catch (loginError) {
            console.error("❌ Auto-login failed:", loginError);
            alert("Registration completed! Please login with your credentials.");
            navigate("/login");
          }
        } else {
          const errorMsg = handleError(completeResult.detail || completeResult, 'registration completion');
          setOtpError(errorMsg || "Registration failed!");
        }
      } else {
        const errorMsg = handleError(verifyResult.detail || verifyResult, 'OTP verification');
        setOtpError(errorMsg || "Invalid OTP");
      }
    } catch (error) {
      console.error("❌ OTP verification error:", error);
      const errorMsg = handleError(error, 'OTP verification');
      setOtpError(errorMsg || "Verification failed. Please try again.");
    } finally {
      setOtpLoading(false);
    }
  };

  const handleResendOTP = async () => {
    try {
      setOtpLoading(true);
      setOtpError("");

      const result = await authAPI.register({ 
        email: tempUserData.email,
        full_name: tempUserData.full_name,
        phone_number: tempUserData.phone_number 
      });

      if (result.success || result.message) {
        setResendTimer(30);
        setEmailOtp(["", "", "", "", "", ""]);
        setSmsOtp(["", "", "", "", "", ""]);
        setOtpError("");
        
        if (result.development_otp) {
          setDevOtp(prev => ({ ...prev, email: result.development_otp }));
        }
        if (result.sms_development_otp) {
          setDevOtp(prev => ({ ...prev, sms: result.sms_development_otp }));
        }
        
        const firstInput = document.getElementById("otp-email-0");
        if (firstInput) firstInput.focus();
      } else {
        const errorMsg = handleError(result.detail || result, 'OTP resend');
        setOtpError(errorMsg || "Failed to resend OTP");
      }
    } catch (error) {
      const errorMsg = handleError(error, 'OTP resend');
      setOtpError(errorMsg || "Failed to resend OTP. Please try again.");
    } finally {
      setOtpLoading(false);
    }
  };

  const getPasswordStrengthColor = () => {
    switch (passwordStrength) {
      case "strong": return "#10b981";
      case "medium": return "#f59e0b";
      case "weak": return "#ef4444";
      default: return "#d1d5db";
    }
  };

  const getPasswordStrengthText = () => {
    switch (passwordStrength) {
      case "strong": return "Strong password";
      case "medium": return "Medium strength";
      case "weak": return "Weak password";
      default: return "";
    }
  };

  return (
    <div className="register-page">
      <div className="register-container">
        <div className="register-header">
          <h2>Create your account</h2>
          <p>Join us today and get started</p>
        </div>

        <div className="register-card">
          {error && (
            <div className="error-message">
              <span className="error-icon">⚠</span>
              {error}
            </div>
          )}

          {/* DEBUG BUTTON - Remove in production */}
          {process.env.NODE_ENV === 'development' && (
            <div style={{ 
              marginBottom: '20px', 
              textAlign: 'center',
              padding: '10px',
              background: '#f8f9fa',
              borderRadius: '8px',
              border: '1px dashed #dc3545'
            }}>
              <button 
                type="button"
                onClick={() => {
                  console.log("🐛 DEBUG: Manually opening OTP modal");
                  setTempUserData({
                    email: formData.email || "test@example.com",
                    password: formData.password || "Test123!",
                    full_name: formData.name || "Test User",
                    phone_number: formData.phoneNumber || "+918392905339"
                  });
                  setDevOtp({ email: "123456", sms: "654321" });
                  setShowOTPModal(true);
                  console.log("✅ Modal state set to:", true);
                }}
                style={{
                  background: '#dc3545',
                  color: 'white',
                  padding: '8px 16px',
                  border: 'none',
                  borderRadius: '5px',
                  cursor: 'pointer',
                  fontSize: '12px'
                }}
              >
                🐛 DEBUG: Open OTP Modal
              </button>
              <p style={{ margin: '5px 0 0 0', fontSize: '11px', color: '#666' }}>
                Use this to test if modal opens
              </p>
            </div>
          )}

          <form className="form" onSubmit={handleSubmit} style={{ display: showOTPModal ? 'none' : 'block' }}>
            <div className="form-group">
              <label htmlFor="name">Full Name *</label>
              <input
                id="name"
                name="name"
                type="text"
                required
                value={formData.name}
                onChange={handleChange}
                placeholder="Enter your full name"
                disabled={loading}
                className={error ? "error-input" : ""}
              />
            </div>

            <div className="form-group">
              <label htmlFor="email">Email Address *</label>
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
              <label htmlFor="phoneNumber">Phone Number (Optional)</label>
              <input
                id="phoneNumber"
                name="phoneNumber"
                type="tel"
                value={formData.phoneNumber}
                onChange={handleChange}
                placeholder="+918392905339"
                disabled={loading}
              />
              <small className="phone-hint">
                Include country code. OTP will be sent via SMS if provided.
              </small>
            </div>

            <div className="form-group">
              <label htmlFor="password">Password *</label>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={formData.password}
                onChange={handleChange}
                placeholder="At least 8 characters with uppercase, lowercase, and number"
                disabled={loading}
                className={error ? "error-input" : ""}
              />
              {passwordStrength && (
                <div className="password-strength">
                  <div className="strength-bar">
                    <div 
                      className="strength-fill"
                      style={{
                        width: passwordStrength === "weak" ? "33%" : 
                               passwordStrength === "medium" ? "66%" : "100%",
                        backgroundColor: getPasswordStrengthColor()
                      }}
                    ></div>
                  </div>
                  <span 
                    className="strength-text"
                    style={{ color: getPasswordStrengthColor() }}
                  >
                    {getPasswordStrengthText()}
                  </span>
                </div>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="confirmPassword">Confirm Password *</label>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                required
                value={formData.confirmPassword}
                onChange={handleChange}
                placeholder="Confirm your password"
                disabled={loading}
                className={error ? "error-input" : ""}
              />
            </div>

            <div className="terms-section">
              <div className="terms-checkbox">
                <input
                  id="termsAccepted"
                  name="termsAccepted"
                  type="checkbox"
                  checked={formData.termsAccepted}
                  onChange={handleChange}
                  disabled={loading}
                />
                <label htmlFor="termsAccepted">
                  I agree to the{" "}
                  <Link to="/terms" className="link">
                    Terms of Service
                  </Link>{" "}
                  and{" "}
                  <Link to="/privacy" className="link">
                    Privacy Policy
                  </Link>
                </label>
              </div>
            </div>

            <button 
              type="submit" 
              className={`register-btn ${loading ? 'loading' : ''}`} 
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="spinner"></span>
                  Sending OTP...
                </>
              ) : (
                "Send OTP Verification"
              )}
            </button>
          </form>
        </div>

        <p className="footer-text">
          Already have an account?{" "}
          <Link to="/login" className="link">
            Sign in here
          </Link>
        </p>
      </div>

      {/* OTP Verification Modal */}
      {showOTPModal && (
        <div className="modal-overlay" style={{ zIndex: 9999 }}>
          <div className="otp-modal" style={{ zIndex: 10000 }}>
            <div className="modal-header">
              <h3>Verify Your Account</h3>
              <p>We've sent verification codes to:</p>
              <p><strong>Email:</strong> {tempUserData?.email}</p>
              {tempUserData?.phone_number && (
                <p><strong>SMS:</strong> {tempUserData.phone_number}</p>
              )}
              
              {/* Development OTP Display */}
              {process.env.NODE_ENV === 'development' && (
                <div className="dev-otp-info">
                  <p><strong>Development OTPs:</strong></p>
                  {devOtp.email && <p>📧 Email OTP: <strong>{devOtp.email}</strong></p>}
                  {devOtp.sms && <p>📱 SMS OTP: <strong>{devOtp.sms}</strong></p>}
                </div>
              )}
            </div>

            {/* Email OTP Section */}
            <div className="otp-section">
              <h4>Email Verification Code *</h4>
              <div className="otp-inputs">
                {emailOtp.map((digit, index) => (
                  <input
                    key={index}
                    id={`otp-email-${index}`}
                    type="text"
                    maxLength="1"
                    value={digit}
                    onChange={(e) => handleOtpChange(emailOtp, setEmailOtp, 'email', index, e.target.value)}
                    onKeyDown={(e) => handleOtpKeyDown(emailOtp, setEmailOtp, 'email', index, e)}
                    className="otp-input"
                    disabled={otpLoading}
                  />
                ))}
              </div>
            </div>

            {/* SMS OTP Section (if phone number provided) */}
            {tempUserData?.phone_number && (
              <div className="otp-section">
                <h4>SMS Verification Code *</h4>
                <div className="otp-inputs">
                  {smsOtp.map((digit, index) => (
                    <input
                      key={index}
                      id={`otp-sms-${index}`}
                      type="text"
                      maxLength="1"
                      value={digit}
                      onChange={(e) => handleOtpChange(smsOtp, setSmsOtp, 'sms', index, e.target.value)}
                      onKeyDown={(e) => handleOtpKeyDown(smsOtp, setSmsOtp, 'sms', index, e)}
                      className="otp-input"
                      disabled={otpLoading}
                    />
                  ))}
                </div>
              </div>
            )}

            {otpError && (
              <div className="otp-error">
                {otpError}
              </div>
            )}

            <div className="otp-timer">
              {resendTimer > 0 ? (
                <p>Resend OTP in {resendTimer} seconds</p>
              ) : (
                <button 
                  className="resend-btn" 
                  onClick={handleResendOTP}
                  disabled={otpLoading}
                >
                  Resend OTP
                </button>
              )}
            </div>

            <div className="modal-actions">
              <button 
                className="verify-btn"
                onClick={handleVerifyOTP}
                disabled={otpLoading || 
                  emailOtp.join("").length !== 6 || 
                  (tempUserData?.phone_number && smsOtp.join("").length !== 6)
                }
              >
                {otpLoading ? (
                  <>
                    <span className="spinner"></span>
                    Verifying...
                  </>
                ) : (
                  "Verify & Complete Registration"
                )}
              </button>
              
              <button 
                className="cancel-btn"
                onClick={() => {
                  setShowOTPModal(false);
                  setEmailOtp(["", "", "", "", "", ""]);
                  setSmsOtp(["", "", "", "", "", ""]);
                  setOtpError("");
                  setDevOtp({ email: "", sms: "" });
                }}
                disabled={otpLoading}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RegisterPage;