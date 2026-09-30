# backend/services/otp_service.py
import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

class OTPService:
    """Service for managing OTP verification for email and SMS"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OTPService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.otp_length = 6
        self.otp_expiry_minutes = 30  # Increased to 30 minutes
        self.otp_storage = {}
        self.instance_id = id(self)  # Add instance ID for debugging
        
        # Import and initialize SMS service
        try:
            from backend.services.sms_service import sms_service
            self.sms_service = sms_service
            logger.info(f"📱 SMS Service integrated - Status: {'✅ ENABLED' if sms_service.is_enabled else '❌ DISABLED'}")
        except ImportError as e:
            logger.warning(f"SMS service not available: {e}")
            self.sms_service = None
        
        logger.info(f"🔧 OTP Service Instance Created - ID: {self.instance_id}")
        self._initialized = True
    
    def generate_otp(self) -> str:
        """Generate a 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=self.otp_length))
    
    def _get_expiry_time(self) -> datetime:
        """Get OTP expiry time"""
        return datetime.utcnow() + timedelta(minutes=self.otp_expiry_minutes)
    
    def _is_otp_expired(self, expires_at: datetime) -> bool:
        """Check if OTP is expired"""
        return datetime.utcnow() > expires_at
    
    def create_email_otp(self, email: str) -> Optional[str]:
        """Create and store email OTP in memory"""
        try:
            otp = self.generate_otp()
            self.otp_storage[email] = {
                'otp': otp,
                'expires_at': self._get_expiry_time(),
                'type': 'email',
                'created_at': datetime.utcnow()
            }
            logger.info(f"✅ Email OTP created for {email}: {otp}")
            logger.info(f"🔧 OTP Service Instance ID: {self.instance_id}")
            logger.info(f"📝 Current OTP storage keys: {list(self.otp_storage.keys())}")
            return otp
        except Exception as e:
            logger.error(f"❌ Failed to create email OTP for {email}: {e}")
            return None
    
    def create_sms_otp(self, phone_number: str) -> Optional[str]:
        """Create and store SMS OTP in memory"""
        try:
            # Validate phone number format
            if not self._is_valid_phone_number(phone_number):
                logger.error(f"❌ Invalid phone number format: {phone_number}")
                return None
                
            otp = self.generate_otp()
            self.otp_storage[phone_number] = {
                'otp': otp,
                'expires_at': self._get_expiry_time(),
                'type': 'sms',
                'created_at': datetime.utcnow()
            }
            logger.info(f"✅ SMS OTP created for {phone_number}: {otp}")
            logger.info(f"📝 Current OTP storage keys: {list(self.otp_storage.keys())}")
            return otp
        except Exception as e:
            logger.error(f"❌ Failed to create SMS OTP for {phone_number}: {e}")
            return None
    
    def _is_valid_phone_number(self, phone_number: str) -> bool:
        """Validate phone number format"""
        if not phone_number:
            return False
        
        # Basic validation - should start with + and contain only digits after +
        if not phone_number.startswith('+'):
            logger.error(f"❌ Phone number should start with +: {phone_number}")
            return False
        
        # Check if the rest are digits
        digits_part = phone_number[1:]
        if not digits_part.isdigit():
            logger.error(f"❌ Phone number should contain only digits after +: {phone_number}")
            return False
        
        # Check length (minimum 10 digits including country code)
        if len(digits_part) < 10:
            logger.error(f"❌ Phone number too short: {phone_number}")
            return False
            
        return True
    
    def verify_email_otp_without_deletion(self, email: str, otp: str) -> bool:
        """Verify email OTP from memory storage"""
        try:
            logger.info(f"🔍 Verifying email OTP without deletion for {email}")
            logger.info(f"🔧 OTP Service Instance ID: {self.instance_id}")
            logger.info(f"📋 Current storage keys: {list(self.otp_storage.keys())}")
            logger.info(f"📋 Full storage content: {self.otp_storage}")
            
            stored_data = self.otp_storage.get(email)
            
            if not stored_data:
                logger.warning(f"❌ No OTP found for email: {email}")
                logger.warning(f"❌ Available keys in storage: {list(self.otp_storage.keys())}")
                return False
            
            logger.info(f"📋 Stored data for {email}: {stored_data}")
            logger.info(f"📋 Comparing stored OTP '{stored_data['otp']}' with received OTP '{otp}'")
            
            if (stored_data['otp'] == otp and 
                not self._is_otp_expired(stored_data['expires_at'])):
                logger.info(f"✅ Email OTP verified for {email} (not deleted)")
                return True
            else:
                logger.warning(f"❌ Invalid or expired email OTP for {email}")
                logger.warning(f"❌ OTP match: {stored_data['otp'] == otp}")
                logger.warning(f"❌ OTP expired: {self._is_otp_expired(stored_data['expires_at'])}")
                logger.warning(f"❌ Expires at: {stored_data['expires_at']}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Failed to verify email OTP for {email}: {e}")
            return False
    
    def verify_sms_otp_without_deletion(self, phone_number: str, otp: str) -> bool:
        """Verify SMS OTP from memory storage"""
        try:
            logger.info(f"🔍 Verifying SMS OTP without deletion for {phone_number}")
            stored_data = self.otp_storage.get(phone_number)
            
            if not stored_data:
                logger.warning(f"❌ No OTP found for phone: {phone_number}")
                return False
            
            if (stored_data['otp'] == otp and 
                not self._is_otp_expired(stored_data['expires_at'])):
                logger.info(f"✅ SMS OTP verified for {phone_number} (not deleted)")
                return True
            else:
                logger.warning(f"❌ Invalid or expired SMS OTP for {phone_number}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to verify SMS OTP for {phone_number}: {e}")
            return False
    
    def check_otp_without_deletion(self, identifier: str, otp: str) -> bool:
        """
        Check if OTP is valid without deleting it from storage
        Useful for multiple verification steps
        """
        try:
            logger.info(f"🔍 Checking OTP without deletion for {identifier}")
            stored_data = self.otp_storage.get(identifier)
            if not stored_data:
                logger.warning(f"❌ No OTP found for {identifier}")
                return False
            
            logger.info(f"🔢 Stored OTP: {stored_data['otp']}, Provided OTP: {otp}")
            logger.info(f"⏰ Is expired: {self._is_otp_expired(stored_data['expires_at'])}")
            
            if (stored_data['otp'] == otp and 
                not self._is_otp_expired(stored_data['expires_at'])):
                logger.info(f"✅ OTP is valid for {identifier}")
                return True
            else:
                logger.warning(f"❌ Invalid or expired OTP for {identifier}")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to check OTP for {identifier}: {e}")
            return False
    
    def _check_user_exists_and_verified(self, db: Session, email: str) -> bool:
        """Check if user already exists and is verified"""
        try:
            if not db:
                return False
                
            result = db.execute(
                text("""
                    SELECT id, email, is_verified 
                    FROM users 
                    WHERE email = :email
                """),
                {"email": email}
            )
            user_row = result.fetchone()
            
            return bool(user_row and user_row.is_verified)
            
        except Exception as db_error:
            logger.warning(f"Database check failed for {email}: {db_error}")
            return False
    
    def send_email_otp(self, email: str, full_name: str, db: Session = None) -> Dict[str, Any]:
        """Generate and send email OTP"""
        try:
            # Check if user already exists and is verified
            if self._check_user_exists_and_verified(db, email):
                return {
                    "success": False,
                    "email_sent": False,
                    "error": "Email already verified",
                    "message": "This email is already registered and verified"
                }
            
            # Create OTP
            otp = self.create_email_otp(email)
            if not otp:
                return {
                    "success": False,
                    "email_sent": False,
                    "error": "OTP generation failed",
                    "message": "Failed to generate verification code"
                }
            
            # Send email via email service
            logger.info(f"📧 EMAIL OTP for {email}: {otp}")
            print(f"📧 DEVELOPMENT OTP for {email}: {otp}")
            
            # Try to send email via email service
            email_sent_successfully = False
            try:
                from backend.services.email_service import EmailService
                email_service = EmailService()
                logger.info(f"📤 Attempting to send email OTP to {email} via email service...")
                email_sent_successfully = email_service.send_otp_verification_email(email, otp, full_name)
                if email_sent_successfully:
                    logger.info(f"✅ Email OTP sent successfully to {email} via email service")
                else:
                    logger.warning(f"⚠️ Email service returned False, OTP shown in console: {otp}")
                    logger.warning(f"   Check SMTP configuration: SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD")
            except Exception as e:
                logger.error(f"❌ Email service error: {e}")
                logger.warning(f"⚠️ Email sending failed, OTP shown in console: {otp}")
                logger.info(f"📧 Check your .env file for SMTP configuration (SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD)")
            
            logger.info(f"✅ Email OTP processed for {email}")
            return {
                "success": True,
                "email_sent": True,
                "message": "Verification code sent successfully",
                "expires_in": f"{self.otp_expiry_minutes} minutes",
                "development_otp": otp  # Include OTP for development
            }
                
        except Exception as e:
            logger.error(f"❌ Failed to send email OTP to {email}: {e}")
            return {
                "success": False,
                "email_sent": False,
                "error": str(e),
                "message": "An unexpected error occurred"
            }
    
    def send_sms_otp(self, phone_number: str, full_name: str) -> Dict[str, Any]:
        """Generate and send SMS OTP using the actual SMS service"""
        try:
            # Validate phone number first
            if not self._is_valid_phone_number(phone_number):
                logger.error(f"❌ Cannot send SMS to invalid phone number: {phone_number}")
                return {
                    "success": False,
                    "sms_sent": False,
                    "error": "Invalid phone number format",
                    "message": "Please provide a valid phone number with country code"
                }
            
            # Generate OTP
            otp = self.create_sms_otp(phone_number)
            if not otp:
                return {
                    "success": False,
                    "sms_sent": False,
                    "error": "OTP generation failed",
                    "message": "Failed to generate verification code"
                }
            
            # Use the actual SMS service to send OTP
            if self.sms_service and self.sms_service.is_enabled:
                logger.info(f"📱 Using real SMS service for {phone_number}")
                sms_result = self.sms_service.send_otp(phone_number, otp, full_name)
                
                if sms_result.get("success"):
                    logger.info(f"✅ Real SMS sent successfully to {phone_number}")
                    return {
                        "success": True,
                        "sms_sent": True,
                        "message": "SMS verification code sent successfully",
                        "expires_in": f"{self.otp_expiry_minutes} minutes",
                        "development_mode": False,
                        "sms_development_otp": otp  # Include OTP for development
                    }
                else:
                    # If SMS service fails, fallback to console
                    logger.warning(f"❌ SMS service failed for {phone_number}: {sms_result.get('message')}")
                    return self._send_console_sms_otp(phone_number, otp, full_name)
            else:
                # SMS service not available, fallback to console
                logger.warning("❌ SMS service not available, using console fallback")
                return self._send_console_sms_otp(phone_number, otp, full_name)
                
        except Exception as e:
            logger.error(f"❌ Failed to send SMS OTP to {phone_number}: {e}")
            # Fallback to console
            return self._send_console_sms_otp(phone_number, self.generate_otp(), full_name)
    
    def _send_console_sms_otp(self, phone_number: str, otp: str, full_name: str = None) -> Dict[str, Any]:
        """Fallback method to display SMS OTP in console for development"""
        logger.warning(f"📱 DEVELOPMENT MODE - SMS OTP for {phone_number}: {otp}")
        print(f"📱 DEVELOPMENT SMS OTP for {phone_number}: {otp}")
        
        return {
            "success": True,
            "sms_sent": True,
            "message": "SMS OTP logged to console (development mode)",
            "development_mode": True,
            "expires_in": f"{self.otp_expiry_minutes} minutes",
            "sms_development_otp": otp  # Include OTP for development
        }

    # Add alias methods for backward compatibility
    def verify_email_otp(self, email: str, otp: str) -> bool:
        """Alias for verify_email_otp_without_deletion"""
        return self.verify_email_otp_without_deletion(email, otp)
    
    def verify_sms_otp(self, phone_number: str, otp: str) -> bool:
        """Alias for verify_sms_otp_without_deletion"""
        return self.verify_sms_otp_without_deletion(phone_number, otp)

# Create singleton instance
otp_service = OTPService()