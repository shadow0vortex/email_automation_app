"""
Validators - Data validation utilities
Email, URL, and input validation functions
"""

import re
from urllib.parse import urlparse


class EmailValidator:
    """Email address validation"""
    
    @staticmethod
    def is_valid(email):
        """Check if email address is valid"""
        if not email or not isinstance(email, str):
            return False
        
        # Basic email pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, email):
            return False
        
        # Additional checks
        if '..' in email:  # No consecutive dots
            return False
        
        if email.startswith('.') or email.endswith('.'):
            return False
        
        local, domain = email.rsplit('@', 1)
        
        if len(local) > 64 or len(domain) > 255:
            return False
        
        return True
    
    @staticmethod
    def get_domain(email):
        """Extract domain from email"""
        if '@' in email:
            return email.split('@')[1]
        return None
    
    @staticmethod
    def is_disposable(email):
        """Check if email is from disposable provider"""
        disposable_domains = [
            'tempmail.com', 'guerrillamail.com', '10minutemail.com',
            'mailinator.com', 'throwaway.email', 'temp-mail.org'
        ]
        
        domain = EmailValidator.get_domain(email)
        return domain in disposable_domains if domain else False


class URLValidator:
    """URL validation"""
    
    @staticmethod
    def is_valid(url):
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    @staticmethod
    def clean_url(url):
        """Clean and normalize URL"""
        url = url.strip()
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        return url


class PhoneValidator:
    """Phone number validation"""
    
    @staticmethod
    def is_valid(phone):
        """Check if phone number is valid (basic check)"""
        if not phone:
            return False
        
        # Remove common formatting
        clean_phone = re.sub(r'[^\d+]', '', phone)
        
        # Check length (minimum 10 digits)
        if len(clean_phone) < 10:
            return False
        
        return True
    
    @staticmethod
    def clean_phone(phone):
        """Clean phone number"""
        return re.sub(r'[^\d+]', '', phone)


class InputValidator:
    """General input validation"""
    
    @staticmethod
    def is_empty(value):
        """Check if value is empty"""
        if value is None:
            return True
        if isinstance(value, str) and value.strip() == '':
            return True
        return False
    
    @staticmethod
    def has_min_length(value, min_length):
        """Check minimum length"""
        if InputValidator.is_empty(value):
            return False
        return len(str(value)) >= min_length
    
    @staticmethod
    def has_max_length(value, max_length):
        """Check maximum length"""
        if InputValidator.is_empty(value):
            return True
        return len(str(value)) <= max_length
    
    @staticmethod
    def is_numeric(value):
        """Check if value is numeric"""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_integer(value):
        """Check if value is integer"""
        try:
            int(value)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_positive(value):
        """Check if value is positive"""
        try:
            return float(value) > 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def contains_html(text):
        """Check if text contains HTML tags"""
        html_pattern = r'<[^>]+>'
        return bool(re.search(html_pattern, text))
    
    @staticmethod
    def sanitize_html(text):
        """Remove potentially dangerous HTML"""
        # Remove script tags
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove event handlers
        text = re.sub(r'on\w+\s*=\s*["\'].*?["\']', '', text, flags=re.IGNORECASE)
        
        return text


class SMTPConfigValidator:
    """SMTP configuration validation"""
    
    @staticmethod
    def validate(config):
        """Validate SMTP configuration"""
        errors = []
        
        # Check required fields
        required_fields = ['email', 'password', 'server', 'port']
        for field in required_fields:
            if field not in config or not config[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate email
        if 'email' in config and config['email']:
            if not EmailValidator.is_valid(config['email']):
                errors.append("Invalid email address")
        
        # Validate port
        if 'port' in config and config['port']:
            try:
                port = int(config['port'])
                if port <= 0 or port > 65535:
                    errors.append("Port must be between 1 and 65535")
            except (ValueError, TypeError):
                errors.append("Port must be a number")
        
        # Validate server
        if 'server' in config and config['server']:
            if not re.match(r'^[a-zA-Z0-9.-]+$', config['server']):
                errors.append("Invalid SMTP server address")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def get_common_smtp_servers():
        """Get list of common SMTP servers"""
        return {
            'Gmail': {'server': 'smtp.gmail.com', 'port': 587},
            'Outlook': {'server': 'smtp-mail.outlook.com', 'port': 587},
            'Yahoo': {'server': 'smtp.mail.yahoo.com', 'port': 587},
            'Office 365': {'server': 'smtp.office365.com', 'port': 587},
            'AOL': {'server': 'smtp.aol.com', 'port': 587},
            'Zoho': {'server': 'smtp.zoho.com', 'port': 587}
        }


class PlaceholderValidator:
    """Placeholder validation in templates"""
    
    @staticmethod
    def extract_placeholders(text):
        """Extract all placeholders from text"""
        pattern = r'\{([a-zA-Z0-9_]+)\}'
        return list(set(re.findall(pattern, text)))
    
    @staticmethod
    def validate_placeholders(text, available_columns):
        """Check if all placeholders have corresponding columns"""
        placeholders = PlaceholderValidator.extract_placeholders(text)
        available_lower = [col.lower() for col in available_columns]
        
        missing = []
        for placeholder in placeholders:
            if placeholder.lower() not in available_lower:
                missing.append(placeholder)
        
        return len(missing) == 0, missing
    
    @staticmethod
    def replace_placeholder(text, placeholder, value):
        """Replace a specific placeholder with value"""
        pattern = r'\{' + re.escape(placeholder) + r'\}'
        return re.sub(pattern, str(value), text, flags=re.IGNORECASE)


class FileValidator:
    """File validation"""
    
    @staticmethod
    def is_valid_excel(file_path):
        """Check if file is valid Excel"""
        valid_extensions = ['.xlsx', '.xls', '.csv']
        return any(file_path.lower().endswith(ext) for ext in valid_extensions)
    
    @staticmethod
    def is_valid_html(file_path):
        """Check if file is valid HTML"""
        return file_path.lower().endswith('.html')
    
    @staticmethod
    def get_file_size_mb(file_path):
        """Get file size in MB"""
        import os
        try:
            size_bytes = os.path.getsize(file_path)
            return size_bytes / (1024 * 1024)
        except Exception:
            return 0
    
    @staticmethod
    def is_file_too_large(file_path, max_size_mb=25):
        """Check if file exceeds size limit"""
        return FileValidator.get_file_size_mb(file_path) > max_size_mb


# Test validators
if __name__ == "__main__":
    # Test email validator
    test_emails = [
        "user@example.com",
        "invalid.email",
        "user@domain",
        "user..name@example.com",
        "valid.email+tag@example.co.uk"
    ]
    
    print("Email Validation Tests:")
    for email in test_emails:
        is_valid = EmailValidator.is_valid(email)
        print(f"{email}: {'✓ Valid' if is_valid else '✗ Invalid'}")
    
    # Test placeholder extraction
    print("\nPlaceholder Extraction Test:")
    template = "Hello {name}, welcome to {company}! Your email is {email}."
    placeholders = PlaceholderValidator.extract_placeholders(template)
    print(f"Template: {template}")
    print(f"Placeholders: {placeholders}")
    
    # Test SMTP config validation
    print("\nSMTP Config Validation Test:")
    config = {
        'email': 'user@gmail.com',
        'password': 'pass123',
        'server': 'smtp.gmail.com',
        'port': 587
    }
    is_valid, errors = SMTPConfigValidator.validate(config)
    print(f"Config valid: {is_valid}")
    if errors:
        print(f"Errors: {errors}")