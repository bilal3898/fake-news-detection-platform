# backend/services/email_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import os
from typing import Optional
from jinja2 import Template
from backend.utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class EmailService:
    def __init__(self):
        self.smtp_server = getattr(settings, 'SMTP_SERVER', os.getenv("SMTP_SERVER", "smtp.gmail.com"))
        self.smtp_port = getattr(settings, 'SMTP_PORT', int(os.getenv("SMTP_PORT", 587)))
        # Distinguish SMTP auth username from From header
        self.smtp_username = getattr(settings, 'SMTP_USERNAME', os.getenv("SMTP_USERNAME"))
        self.sender_email = getattr(settings, 'FROM_EMAIL', os.getenv("FROM_EMAIL", self.smtp_username))
        self.sender_password = getattr(settings, 'SMTP_PASSWORD', os.getenv("SMTP_PASSWORD"))
        self.frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        
        # If using Gmail, align From with smtp_username to avoid DMARC issues
        if self.smtp_server.endswith("gmail.com"):
            if self.smtp_username and self.sender_email and self.sender_email.lower() != self.smtp_username.lower():
                logger.warning("FROM_EMAIL does not match SMTP_USERNAME for Gmail; using SMTP_USERNAME as From to improve deliverability")
                self.sender_email = self.smtp_username
        
        # Verify configuration
        if not all([self.smtp_server, self.smtp_port, self.smtp_username, self.sender_password, self.sender_email]):
            logger.warning("Email service configuration incomplete. Email sending may fail.")
        
        # Hint for Gmail App Passwords
        if self.smtp_server.endswith("gmail.com") and self.smtp_username and self.sender_password and len(self.sender_password) < 12:
            logger.warning("Gmail may require an App Password (16 chars). Ensure you've created and set a Gmail App Password.")
    
    def _send_email(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """
        Internal method to send email
        """
        try:
            message = MIMEMultipart("alternative")
            message["From"] = self.sender_email
            message["To"] = to_email
            message["Subject"] = subject
            
            # Attach both plain text and HTML versions
            message.attach(MIMEText(text_content, "plain"))
            message.attach(MIMEText(html_content, "html"))
            
            # Send email
            # Use SSL if port 465, otherwise STARTTLS
            if int(self.smtp_port) == 465:
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                    server.login(self.smtp_username or self.sender_email, self.sender_password)
                    server.send_message(message)
            else:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_username or self.sender_email, self.sender_password)
                    server.send_message(message)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP authentication failed. Check email credentials.")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error occurred: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_verification_email(self, email: str, full_name: str, token: str) -> bool:
        """
        Send email verification email with token link
        """
        try:
            verification_url = f"{self.frontend_url}/verify-email?token={token}"
            
            subject = "Verify Your Email - Fake News Detection Platform"
            
            # HTML template
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
                    .container { max-width: 600px; margin: 0 auto; background: #ffffff; }
                    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; text-align: center; }
                    .content { padding: 30px; background: #f9f9f9; }
                    .button { display: inline-block; padding: 12px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; font-size: 16px; margin: 20px 0; }
                    .verification-link { background: #f0f0f0; padding: 15px; border-radius: 5px; margin: 15px 0; word-break: break-all; font-family: monospace; }
                    .expiry-note { color: #666; font-size: 14px; text-align: center; margin: 15px 0; }
                    .footer { text-align: center; margin-top: 30px; color: #666; font-size: 12px; padding: 20px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Verify Your Email</h1>
                    </div>
                    <div class="content">
                        <p>Hello <strong>{{ full_name }}</strong>,</p>
                        <p>Thank you for registering with Fake News Detection Platform!</p>
                        <p>Please click the button below to verify your email address:</p>
                        
                        <div style="text-align: center;">
                            <a href="{{ verification_url }}" class="button">Verify Email Address</a>
                        </div>
                        
                        <p>Or copy and paste this link in your browser:</p>
                        <div class="verification-link">{{ verification_url }}</div>
                        
                        <p class="expiry-note">This verification link will expire in 24 hours.</p>
                        
                        <p>If you didn't create an account with us, please ignore this email.</p>
                        
                        <div class="footer">
                            <p>&copy; 2024 Fake News Detection Platform. All rights reserved.</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            text_content = f"""
            Hello {full_name},
            
            Thank you for registering with Fake News Detection Platform!
            
            Please verify your email address by clicking the link below:
            {verification_url}
            
            This verification link will expire in 24 hours.
            
            If you didn't create an account with us, please ignore this email.
            
            Best regards,
            Fake News Detection Platform Team
            """
            
            # Render HTML template
            template = Template(html_template)
            html_content = template.render(
                full_name=full_name,
                verification_url=verification_url
            )
            
            return self._send_email(email, subject, html_content, text_content)
            
        except Exception as e:
            logger.error(f"Failed to prepare verification email for {email}: {e}")
            return False

    def send_otp_verification_email(self, email: str, otp: str, full_name: str) -> bool:
        """
        Send OTP verification email
        """
        try:
            subject = "Your Verification Code - Fake News Detection Platform"
            
            # HTML template
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
                    .container { max-width: 600px; margin: 0 auto; background: #ffffff; }
                    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; text-align: center; }
                    .content { padding: 30px; background: #f9f9f9; }
                    .otp-code { font-size: 42px; font-weight: bold; text-align: center; color: #667eea; margin: 30px 0; letter-spacing: 8px; }
                    .expiry-note { color: #666; font-size: 14px; text-align: center; margin: 15px 0; }
                    .security-note { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }
                    .footer { text-align: center; margin-top: 30px; color: #666; font-size: 12px; padding: 20px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Email Verification</h1>
                    </div>
                    <div class="content">
                        <p>Hello <strong>{{ full_name }}</strong>,</p>
                        <p>Thank you for registering with Fake News Detection Platform. Use the verification code below to complete your registration:</p>
                        
                        <div class="otp-code">{{ otp }}</div>
                        
                        <p class="expiry-note">This code will expire in 5 minutes</p>
                        
                        <div class="security-note">
                            <strong>Security Tip:</strong> Never share this code with anyone. Our team will never ask for your verification code.
                        </div>
                        
                        <p>If you didn't request this verification, please ignore this email.</p>
                        
                        <div class="footer">
                            <p>&copy; 2024 Fake News Detection Platform. All rights reserved.</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            text_content = f"""
            Hello {full_name},
            
            Thank you for registering with Fake News Detection Platform.
            
            Your verification code is: {otp}
            
            This code will expire in 5 minutes.
            
            Security Tip: Never share this code with anyone. Our team will never ask for your verification code.
            
            If you didn't request this verification, please ignore this email.
            
            Best regards,
            Fake News Detection Platform Team
            """
            
            # Render HTML template
            template = Template(html_template)
            html_content = template.render(full_name=full_name, otp=otp)
            
            return self._send_email(email, subject, html_content, text_content)
            
        except Exception as e:
            logger.error(f"Failed to prepare OTP verification email for {email}: {e}")
            return False

    def send_password_reset_email(self, email: str, full_name: str, token: str) -> bool:
        """
        Send password reset email
        """
        try:
            reset_url = f"{self.frontend_url}/reset-password?token={token}"
            
            subject = "Password Reset Request - Fake News Detection Platform"
            
            # HTML template
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
                    .container { max-width: 600px; margin: 0 auto; background: #ffffff; }
                    .header { background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); color: white; padding: 30px 20px; text-align: center; }
                    .content { padding: 30px; background: #f9f9f9; }
                    .button { display: inline-block; padding: 12px 30px; background: #dc3545; color: white; text-decoration: none; border-radius: 5px; font-size: 16px; margin: 20px 0; }
                    .reset-link { background: #f0f0f0; padding: 15px; border-radius: 5px; margin: 15px 0; word-break: break-all; font-family: monospace; }
                    .expiry-note { color: #666; font-size: 14px; text-align: center; margin: 15px 0; }
                    .security-warning { background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 5px; margin: 20px 0; color: #721c24; }
                    .footer { text-align: center; margin-top: 30px; color: #666; font-size: 12px; padding: 20px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Password Reset</h1>
                    </div>
                    <div class="content">
                        <p>Hello <strong>{{ full_name }}</strong>,</p>
                        <p>We received a request to reset your password for your Fake News Detection Platform account.</p>
                        
                        <div style="text-align: center;">
                            <a href="{{ reset_url }}" class="button">Reset Your Password</a>
                        </div>
                        
                        <p>Or copy and paste this link in your browser:</p>
                        <div class="reset-link">{{ reset_url }}</div>
                        
                        <p class="expiry-note">This password reset link will expire in 1 hour.</p>
                        
                        <div class="security-warning">
                            <strong>Important:</strong> If you didn't request this password reset, please ignore this email and ensure your account is secure.
                        </div>
                        
                        <div class="footer">
                            <p>&copy; 2024 Fake News Detection Platform. All rights reserved.</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            text_content = f"""
            Hello {full_name},
            
            We received a request to reset your password for your Fake News Detection Platform account.
            
            Click the link below to reset your password:
            {reset_url}
            
            This password reset link will expire in 1 hour.
            
            Important: If you didn't request this password reset, please ignore this email and ensure your account is secure.
            
            Best regards,
            Fake News Detection Platform Team
            """
            
            # Render HTML template
            template = Template(html_template)
            html_content = template.render(
                full_name=full_name,
                reset_url=reset_url
            )
            
            return self._send_email(email, subject, html_content, text_content)
            
        except Exception as e:
            logger.error(f"Failed to prepare password reset email for {email}: {e}")
            return False

    def send_welcome_email(self, email: str, full_name: str) -> bool:
        """
        Send welcome email after successful verification
        """
        try:
            subject = "Welcome to Fake News Detection Platform!"
            
            # HTML template
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
                    .container { max-width: 600px; margin: 0 auto; background: #ffffff; }
                    .header { background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 30px 20px; text-align: center; }
                    .content { padding: 30px; background: #f9f9f9; }
                    .feature { background: white; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #28a745; }
                    .footer { text-align: center; margin-top: 30px; color: #666; font-size: 12px; padding: 20px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Welcome Aboard!</h1>
                    </div>
                    <div class="content">
                        <p>Hello <strong>{{ full_name }}</strong>,</p>
                        <p>Welcome to Fake News Detection Platform! Your account has been successfully verified and is now active.</p>
                        
                        <p>Here's what you can do with your account:</p>
                        
                        <div class="feature">
                            <strong>🔍 Analyze News Content</strong><br>
                            Check any news article or text for authenticity using our AI-powered detection system.
                        </div>
                        
                        <div class="feature">
                            <strong>📊 View Detailed Reports</strong><br>
                            Get comprehensive analysis with confidence scores and reasoning.
                        </div>
                        
                        <div class="feature">
                            <strong>📱 Real-time Monitoring</strong><br>
                            Stay updated with the latest fake news alerts and trends.
                        </div>
                        
                        <p>We're excited to have you on board and help you navigate the complex world of online information.</p>
                        
                        <p>If you have any questions or need assistance, don't hesitate to contact our support team.</p>
                        
                        <div class="footer">
                            <p>&copy; 2024 Fake News Detection Platform. All rights reserved.</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            text_content = f"""
            Hello {full_name},
            
            Welcome to Fake News Detection Platform! Your account has been successfully verified and is now active.
            
            With your account, you can:
            - Analyze news content for authenticity
            - View detailed reports with confidence scores
            - Access real-time monitoring features
            
            We're excited to have you on board and help you navigate the complex world of online information.
            
            If you have any questions or need assistance, don't hesitate to contact our support team.
            
            Best regards,
            Fake News Detection Platform Team
            """
            
            # Render HTML template
            template = Template(html_template)
            html_content = template.render(full_name=full_name)
            
            return self._send_email(email, subject, html_content, text_content)
            
        except Exception as e:
            logger.error(f"Failed to prepare welcome email for {email}: {e}")
            return False


# Create global instance
email_service = EmailService()

# Legacy functions for backward compatibility
def send_verification_email(email: str, full_name: str, token: str):
    """Legacy function - use EmailService.send_verification_email instead"""
    return email_service.send_verification_email(email, full_name, token)

def send_password_reset_email(email: str, full_name: str, token: str):
    """Legacy function - use EmailService.send_password_reset_email instead"""
    return email_service.send_password_reset_email(email, full_name, token)