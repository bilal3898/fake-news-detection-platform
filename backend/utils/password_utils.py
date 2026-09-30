# backend/utils/password_utils.py

import re
import secrets
import string
from typing import Tuple, Optional
from passlib.context import CryptContext
from datetime import datetime, timedelta
import logging
from jose import JWTError, jwt
from backend.utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Password hashing context
pwd_context = CryptContext(
    schemes=["bcrypt", "argon2"],
    default="bcrypt",
    bcrypt__rounds=12,  # Increased rounds for better security
    argon2__time_cost=3,
    argon2__memory_cost=65536,
    argon2__parallelism=2,
    argon2__salt_len=16,
    deprecated="auto"
)

class PasswordStrength:
    """Password strength validation and scoring"""
    
    # Common weak passwords to block
    COMMON_PASSWORDS = {
        "password", "123456", "12345678", "123456789", "qwerty", 
        "abc123", "password1", "admin", "welcome", "monkey",
        "letmein", "login", "passw0rd", "master", "hello"
    }
    
    @classmethod
    def validate_password_strength(cls, password: str) -> Tuple[bool, str]:
        """
        Validate password strength and return (is_valid, message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if len(password) > 128:
            return False, "Password must be less than 128 characters"
        
        # Check for common passwords
        if password.lower() in cls.COMMON_PASSWORDS:
            return False, "Password is too common and easily guessable"
        
        # Check character variety
        checks = {
            'lowercase': re.search(r'[a-z]', password),
            'uppercase': re.search(r'[A-Z]', password),
            'digits': re.search(r'\d', password),
            'special': re.search(r'[!@#$%^&*(),.?":{}|<>]', password)
        }
        
        # Require at least 3 out of 4 character types
        score = sum(1 for check in checks.values() if check)
        if score < 3:
            return False, "Password must include at least 3 of: lowercase, uppercase, digits, special characters"
        
        # Check for sequential characters
        if cls._has_sequential_chars(password):
            return False, "Password contains sequential characters"
        
        # Check for repeated characters
        if cls._has_repeated_chars(password):
            return False, "Password contains too many repeated characters"
        
        return True, "Password is strong"
    
    @classmethod
    def calculate_password_score(cls, password: str) -> int:
        """
        Calculate password strength score (0-100)
        """
        score = 0
        
        # Length score
        if len(password) >= 8:
            score += 10
        if len(password) >= 12:
            score += 10
        if len(password) >= 16:
            score += 10
        
        # Character variety score
        checks = {
            'lowercase': re.search(r'[a-z]', password),
            'uppercase': re.search(r'[A-Z]', password),
            'digits': re.search(r'\d', password),
            'special': re.search(r'[!@#$%^&*(),.?":{}|<>]', password)
        }
        
        score += sum(10 for check in checks.values() if check)
        
        # Entropy bonus
        if len(set(password)) >= len(password) * 0.8:
            score += 10
        
        # Penalties
        if password.lower() in cls.COMMON_PASSWORDS:
            score = 0
        elif cls._has_sequential_chars(password):
            score = max(0, score - 20)
        elif cls._has_repeated_chars(password):
            score = max(0, score - 15)
        
        return min(100, score)
    
    @staticmethod
    def _has_sequential_chars(password: str, min_seq: int = 3) -> bool:
        """Check for sequential characters"""
        for i in range(len(password) - min_seq + 1):
            seq = password[i:i+min_seq]
            if (seq.isalpha() and seq in string.ascii_lowercase) or \
               (seq.isalpha() and seq in string.ascii_uppercase) or \
               (seq.isdigit() and seq in '0123456789'):
                return True
        return False
    
    @staticmethod
    def _has_repeated_chars(password: str, max_repeat: int = 3) -> bool:
        """Check for repeated characters"""
        import itertools
        for char, group in itertools.groupby(password):
            if len(list(group)) > max_repeat:
                return True
        return False

class PasswordGenerator:
    """Secure password generation"""
    
    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        """
        Generate a cryptographically secure random password
        """
        if length < 8:
            raise ValueError("Password length must be at least 8 characters")
        
        # Character sets
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special = '!@#$%^&*()_+-=[]{}|;:,.<>?'
        
        # Ensure at least one character from each set
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(special)
        ]
        
        # Fill the rest with random choices from all sets
        all_chars = lowercase + uppercase + digits + special
        password.extend(secrets.choice(all_chars) for _ in range(length - 4))
        
        # Shuffle the password
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)
    
    @staticmethod
    def generate_memorable_password(word_count: int = 4, separator: str = '-') -> str:
        """
        Generate a memorable but secure password using word list
        """
        # Common word list (you can expand this)
        words = [
            'apple', 'brave', 'cloud', 'dragon', 'eagle', 'flame', 'globe', 'heart',
            'ice', 'jewel', 'knight', 'light', 'mountain', 'night', 'ocean', 'planet',
            'queen', 'river', 'star', 'tiger', 'unity', 'victory', 'water', 'xray',
            'year', 'zenith'
        ]
        
        selected_words = [secrets.choice(words) for _ in range(word_count)]
        return separator.join(selected_words)

class PasswordManager:
    """Comprehensive password management utilities"""
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """
        Hash a password using the configured context
        """
        try:
            return pwd_context.hash(password)
        except Exception as e:
            logger.error(f"Password hashing failed: {str(e)}")
            raise ValueError("Failed to hash password")
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash
        """
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Password verification failed: {str(e)}")
            return False
    
    @staticmethod
    def needs_rehash(hashed_password: str) -> bool:
        """
        Check if password needs rehashing (e.g., after algorithm upgrade)
        """
        return pwd_context.needs_update(hashed_password)
    
    @staticmethod
    def create_password_reset_token(email: str, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a password reset token
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=1)
        
        to_encode = {
            "sub": email,
            "exp": expire,
            "type": "password_reset"
        }
        
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    @staticmethod
    def verify_password_reset_token(token: str) -> Optional[str]:
        """
        Verify password reset token and return email if valid
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            email: str = payload.get("sub")
            token_type: str = payload.get("type")
            
            if email is None or token_type != "password_reset":
                return None
                
            return email
        except JWTError:
            return None
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """
        Generate a cryptographically secure random token
        """
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

class PasswordPolicy:
    """Password policy enforcement"""
    
    def __init__(
        self,
        min_length: int = 8,
        max_length: int = 128,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digits: bool = True,
        require_special: bool = True,
        block_common: bool = True,
        max_age_days: int = 90
    ):
        self.min_length = min_length
        self.max_length = max_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digits = require_digits
        self.require_special = require_special
        self.block_common = block_common
        self.max_age_days = max_age_days
    
    def validate(self, password: str) -> Tuple[bool, str]:
        """
        Validate password against policy
        """
        # Length check
        if len(password) < self.min_length:
            return False, f"Password must be at least {self.min_length} characters long"
        
        if len(password) > self.max_length:
            return False, f"Password must be less than {self.max_length} characters"
        
        # Character requirements
        if self.require_lowercase and not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if self.require_digits and not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        
        if self.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        # Common password check
        if self.block_common and password.lower() in PasswordStrength.COMMON_PASSWORDS:
            return False, "Password is too common and easily guessable"
        
        return True, "Password meets policy requirements"
    
    def is_password_expired(self, last_changed: datetime) -> bool:
        """
        Check if password has expired based on last changed date
        """
        if not last_changed:
            return False
        
        expiry_date = last_changed + timedelta(days=self.max_age_days)
        return datetime.utcnow() > expiry_date

# Default instances for easy import
default_policy = PasswordPolicy()
password_generator = PasswordGenerator()
password_manager = PasswordManager()
password_strength = PasswordStrength()

# Convenience functions
def get_password_hash(password: str) -> str:
    """Convenience function to hash password"""
    return password_manager.get_password_hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Convenience function to verify password"""
    return password_manager.verify_password(plain_password, hashed_password)

def validate_password_strength(password: str) -> Tuple[bool, str]:
    """Convenience function to validate password strength"""
    return password_strength.validate_password_strength(password)

def generate_secure_password(length: int = 16) -> str:
    """Convenience function to generate secure password"""
    return password_generator.generate_secure_password(length)

def create_password_reset_token(email: str) -> str:
    """Convenience function to create password reset token"""
    return password_manager.create_password_reset_token(email)

def verify_password_reset_token(token: str) -> Optional[str]:
    """Convenience function to verify password reset token"""
    return password_manager.verify_password_reset_token(token)

# Password history management (optional feature)
class PasswordHistory:
    """Manage password history to prevent reuse"""
    
    def __init__(self, max_history: int = 5):
        self.max_history = max_history
    
    def can_use_password(self, new_password: str, previous_hashes: list) -> bool:
        """
        Check if new password can be used (not in history)
        """
        for old_hash in previous_hashes:
            if verify_password(new_password, old_hash):
                return False
        return True
    
    def add_to_history(self, password_hash: str, history: list) -> list:
        """
        Add new password hash to history, maintaining max size
        """
        history.insert(0, password_hash)
        return history[:self.max_history]

# Example usage and testing
if __name__ == "__main__":
    # Test password strength
    test_passwords = [
        "weak",
        "password123",
        "StrongPass123!",
        "VeryStrongPassword123!@#",
        "12345678"
    ]
    
    print("Password Strength Test:")
    for pwd in test_passwords:
        is_valid, message = validate_password_strength(pwd)
        score = password_strength.calculate_password_score(pwd)
        print(f"'{pwd}': Valid={is_valid}, Score={score}, Message='{message}'")
    
    # Generate secure passwords
    print("\nGenerated Secure Passwords:")
    for i in range(3):
        pwd = generate_secure_password(12)
        print(f"Password {i+1}: {pwd}")
    
    # Test password hashing and verification
    print("\nPassword Hashing Test:")
    test_password = "MySecurePassword123!"
    hashed = get_password_hash(test_password)
    is_verified = verify_password(test_password, hashed)
    needs_rehash = password_manager.needs_rehash(hashed)
    
    print(f"Original: {test_password}")
    print(f"Hashed: {hashed}")
    print(f"Verified: {is_verified}")
    print(f"Needs Rehash: {needs_rehash}")
    
    # Test password reset token
    print("\nPassword Reset Token Test:")
    email = "test@example.com"
    reset_token = create_password_reset_token(email)
    verified_email = verify_password_reset_token(reset_token)
    
    print(f"Original Email: {email}")
    print(f"Reset Token: {reset_token}")
    print(f"Verified Email: {verified_email}")