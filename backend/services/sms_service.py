# backend/services/sms_service.py
import os
import logging
import time
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from backend.utils.config import get_settings

logger = logging.getLogger(__name__)

class SMSService:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SMSService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.client = None
        self.twilio_phone = None
        self.is_enabled = False
        logger.info("🔄 Initializing SMS Service...")
        self._initialize_twilio()
        self._initialized = True
    
    def _initialize_twilio(self):
        """Initialize Twilio client with detailed debugging"""
        max_retries = 3
        
        # Debug: Check environment variables directly
        env_sid = os.getenv('TWILIO_ACCOUNT_SID')
        env_token = os.getenv('TWILIO_AUTH_TOKEN')
        env_phone = os.getenv('TWILIO_PHONE_NUMBER')
        
        logger.info(f"🔍 Environment Variables Check:")
        logger.info(f"   TWILIO_ACCOUNT_SID: {'✅ SET' if env_sid else '❌ NOT SET'}")
        logger.info(f"   TWILIO_AUTH_TOKEN: {'✅ SET' if env_token else '❌ NOT SET'}")
        logger.info(f"   TWILIO_PHONE_NUMBER: {'✅ SET' if env_phone else '❌ NOT SET'}")
        
        for attempt in range(max_retries):
            try:
                # Get fresh settings instance
                settings = get_settings()
                
                # Debug settings
                logger.info(f"🔍 Settings Check (Attempt {attempt + 1}):")
                logger.info(f"   TWILIO_ACCOUNT_SID from settings: {getattr(settings, 'TWILIO_ACCOUNT_SID', 'NOT FOUND')}")
                logger.info(f"   TWILIO_AUTH_TOKEN from settings: {'✅ SET' if getattr(settings, 'TWILIO_AUTH_TOKEN', None) else '❌ NOT SET'}")
                logger.info(f"   TWILIO_PHONE_NUMBER from settings: {getattr(settings, 'TWILIO_PHONE_NUMBER', 'NOT FOUND')}")
                
                account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
                auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
                twilio_phone = getattr(settings, 'TWILIO_PHONE_NUMBER', None)
                
                if not all([account_sid, auth_token, twilio_phone]):
                    missing = []
                    if not account_sid: missing.append("TWILIO_ACCOUNT_SID")
                    if not auth_token: missing.append("TWILIO_AUTH_TOKEN") 
                    if not twilio_phone: missing.append("TWILIO_PHONE_NUMBER")
                    
                    logger.warning(f"❌ Missing configuration: {', '.join(missing)}")
                    
                    if attempt == max_retries - 1:
                        # Try direct environment variables as fallback
                        logger.info("🔄 Trying direct environment variables as fallback...")
                        account_sid = env_sid
                        auth_token = env_token
                        twilio_phone = env_phone
                        
                        if all([account_sid, auth_token, twilio_phone]):
                            logger.info("✅ Using environment variables directly")
                        else:
                            self.is_enabled = False
                            logger.error("❌ All configuration attempts failed")
                            return
                    else:
                        time.sleep(1)
                        continue
                
                # Initialize Twilio client
                logger.info("🔧 Initializing Twilio client...")
                self.client = Client(account_sid, auth_token)
                self.twilio_phone = twilio_phone
                
                # Test the client
                logger.info("🧪 Testing Twilio credentials...")
                account = self.client.api.accounts(account_sid).fetch()
                logger.info(f"✅ Twilio account verified: {account.friendly_name}")
                
                self.is_enabled = True
                logger.info("✅ Twilio SMS service initialized successfully")
                return
                
            except Exception as e:
                logger.warning(f"❌ Twilio initialization attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    self.is_enabled = False
                    logger.error("❌ All Twilio initialization attempts failed")
                else:
                    time.sleep(2)
        
    def send_otp(self, phone_number: str, otp: str, full_name: str = None) -> dict:
        """
        Send OTP via SMS
        Returns: dict with success status and message
        """
        try:
            logger.info(f"📱 Sending SMS OTP to {phone_number}...")
            
            if not self.is_enabled:
                logger.warning("SMS service not enabled, falling back to console")
                return self._send_console_otp(phone_number, otp, full_name)
            
            if not self.client:
                logger.error("Twilio client not available")
                return self._send_console_otp(phone_number, otp, full_name)
            
            # Format phone number
            if not phone_number.startswith('+'):
                phone_number = '+' + phone_number
            
            # Create message
            message_body = f"Your Fake News Detection verification code is: {otp}. Valid for 5 minutes."
            if full_name:
                message_body = f"Hi {full_name}, {message_body}"
            
            logger.info(f"📤 Sending SMS via Twilio: {self.twilio_phone} → {phone_number}")
            
            # Send SMS
            message = self.client.messages.create(
                body=message_body,
                from_=self.twilio_phone,
                to=phone_number
            )
            
            logger.info(f"✅ SMS sent successfully! SID: {message.sid}, Status: {message.status}")
            
            return {
                "success": True,
                "message": "SMS sent successfully",
                "message_sid": message.sid,
                "status": message.status,
                "development_mode": False
            }
            
        except TwilioRestException as e:
            logger.error(f"❌ Twilio error: {e.code} - {e.msg}")
            
            # Special handling for trial account restrictions
            if e.code == 21608:  # Unverified number on trial account
                logger.warning(f"⚠️ Trial account restriction: {phone_number} is not verified")
                logger.info(f"💡 Falling back to development mode for unverified number")
                return self._send_console_otp(phone_number, otp, full_name)
            
            # Other Twilio errors
            return {
                "success": False,
                "message": f"Failed to send SMS: {e.msg}",
                "error_code": e.code,
                "development_mode": False
            }
        except Exception as e:
            logger.error(f"❌ Unexpected error sending SMS: {e}")
            return {
                "success": False,
                "message": f"Failed to send SMS: {str(e)}",
                "development_mode": False
            }
    
    def _send_console_otp(self, phone_number: str, otp: str, full_name: str = None) -> dict:
        """Fallback to console output"""
        logger.warning(f"📱 DEVELOPMENT MODE - SMS OTP for {phone_number}: {otp}")
        print(f"📱 DEVELOPMENT SMS OTP for {phone_number}: {otp}")
        
        return {
            "success": False,
            "message": "SMS OTP logged to console (development mode)",
            "development_mode": True,
            "otp": otp
        }

# Create global instance
sms_service = SMSService()