"""
Email Sender - SMTP Email Sending with Threading
Handles bulk email sending with rate limiting and error handling
"""

import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from PyQt5.QtCore import QThread, pyqtSignal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailSenderThread(QThread):
    """Background thread for sending emails without blocking UI"""
    
    # Signals for UI updates
    progress = pyqtSignal(int)  # Progress percentage
    log_signal = pyqtSignal(dict)  # Log entry: {email, name, status, error}
    finished = pyqtSignal(dict)  # Summary: {successful, failed, total_time}
    status_signal = pyqtSignal(str)  # Status messages
    
    def __init__(self, smtp_config, recipients_df, subject, body_html, 
                 delay, campaign_id, db_manager):
        super().__init__()
        self.smtp_config = smtp_config
        self.recipients_df = recipients_df
        self.subject = subject
        self.body_html = body_html
        self.delay = delay
        self.campaign_id = campaign_id
        self.db_manager = db_manager
        self.should_stop = False
        self.is_paused = False
        self.successful = 0
        self.failed = 0
        self.start_time = None
    
    def stop(self):
        """Stop the email sending process"""
        self.should_stop = True
        self.status_signal.emit("Stopping email sender...")
    
    def pause(self):
        """Pause the email sending process"""
        self.is_paused = True
        self.status_signal.emit("Email sending paused")
    
    def resume(self):
        """Resume the email sending process"""
        self.is_paused = False
        self.status_signal.emit("Email sending resumed")
    
    def replace_placeholders(self, text, row):
        """Replace placeholders in text with actual data"""
        result = text
        for col in row.index:
            placeholder = f"{{{col.lower()}}}"
            value = str(row[col]) if row[col] is not None else ""
            result = result.replace(placeholder, value)
        return result
    
    def create_email_message(self, recipient_email, personalized_subject, personalized_body):
        """Create MIME email message"""
        msg = MIMEMultipart('alternative')
        msg['From'] = self.smtp_config['email']
        msg['To'] = recipient_email
        msg['Subject'] = personalized_subject
        
        # Attach HTML body
        html_part = MIMEText(personalized_body, 'html', 'utf-8')
        msg.attach(html_part)
        
        return msg
    
    def connect_smtp(self):
        """Establish SMTP connection with retry logic"""
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                if self.smtp_config['port'] == 465:
                    server = smtplib.SMTP_SSL(
                        self.smtp_config['server'], 
                        self.smtp_config['port'],
                        timeout=30
                    )
                else:
                    server = smtplib.SMTP(
                        self.smtp_config['server'], 
                        self.smtp_config['port'],
                        timeout=30
                    )
                    server.starttls()
                
                server.login(self.smtp_config['email'], self.smtp_config['password'])
                self.status_signal.emit(f"Connected to SMTP server")
                return server
                
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"SMTP Authentication failed: {e}")
                self.status_signal.emit(f"Authentication failed. Check credentials.")
                return None
            except Exception as e:
                logger.error(f"SMTP connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    self.status_signal.emit(
                        f"Connection failed, retrying in {retry_delay}s... (Attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(retry_delay)
                else:
                    self.status_signal.emit(f"Failed to connect after {max_retries} attempts")
                    return None
        
        return None
    
    def run(self):
        """Main email sending loop"""
        import time
        self.start_time = time.time()
        total = len(self.recipients_df)
        
        self.status_signal.emit(f"Starting to send {total} emails...")
        
        # Connect to SMTP server
        server = self.connect_smtp()
        if not server:
            self.finished.emit({
                'successful': 0,
                'failed': total,
                'total_time': 0
            })
            return
        
        try:
            for idx, row in self.recipients_df.iterrows():
                # Check if should stop
                if self.should_stop:
                    self.status_signal.emit("Email sending stopped by user")
                    break
                
                # Check if paused
                while self.is_paused and not self.should_stop:
                    time.sleep(0.5)
                
                if self.should_stop:
                    break
                
                recipient_email = None
                recipient_name = ""
                
                try:
                    # Get recipient data
                    recipient_email = row.get('Email', row.get('email', ''))
                    recipient_name = row.get('Name', row.get('name', ''))
                    
                    if not recipient_email:
                        raise ValueError("No email address found")
                    
                    # Replace placeholders
                    personalized_subject = self.replace_placeholders(self.subject, row)
                    personalized_body = self.replace_placeholders(self.body_html, row)
                    
                    # Create email message
                    msg = self.create_email_message(
                        recipient_email, 
                        personalized_subject, 
                        personalized_body
                    )
                    
                    # Send email
                    server.send_message(msg)
                    
                    # Log success
                    self.successful += 1
                    self.db_manager.log_email(
                        recipient_email=recipient_email,
                        recipient_name=str(recipient_name),
                        subject=personalized_subject,
                        status='Success',
                        error_message=None,
                        campaign_id=self.campaign_id
                    )
                    
                    self.log_signal.emit({
                        'email': recipient_email,
                        'name': str(recipient_name),
                        'status': 'Success',
                        'error': ''
                    })
                    
                    self.status_signal.emit(
                        f"Sent to {recipient_email} ({self.successful}/{total})"
                    )
                    
                except smtplib.SMTPException as e:
                    error_msg = f"SMTP Error: {str(e)}"
                    self.handle_failed_email(recipient_email, recipient_name, error_msg)
                    
                except Exception as e:
                    error_msg = str(e)
                    self.handle_failed_email(recipient_email, recipient_name, error_msg)
                
                # Update progress
                progress_percent = int(((idx + 1) / total) * 100)
                self.progress.emit(progress_percent)
                
                # Rate limiting delay
                if idx < total - 1 and not self.should_stop:
                    time.sleep(self.delay)
            
            # Close SMTP connection
            server.quit()
            self.status_signal.emit("SMTP connection closed")
            
        except Exception as e:
            logger.error(f"Critical error in email sender: {e}")
            self.status_signal.emit(f"Critical error: {str(e)}")
        
        # Calculate total time
        total_time = time.time() - self.start_time
        
        # Emit finished signal
        self.finished.emit({
            'successful': self.successful,
            'failed': self.failed,
            'total_time': total_time
        })
        
        self.status_signal.emit(
            f"Completed: {self.successful} successful, {self.failed} failed in {total_time:.1f}s"
        )
    
    def handle_failed_email(self, recipient_email, recipient_name, error_msg):
        """Handle failed email sending"""
        self.failed += 1
        
        if recipient_email:
            self.db_manager.log_email(
                recipient_email=recipient_email or "unknown",
                recipient_name=str(recipient_name),
                subject=self.subject,
                status='Failed',
                error_message=error_msg,
                campaign_id=self.campaign_id
            )
            
            self.log_signal.emit({
                'email': recipient_email,
                'name': str(recipient_name),
                'status': 'Failed',
                'error': error_msg
            })
            
            logger.error(f"Failed to send to {recipient_email}: {error_msg}")


class EmailValidator:
    """Validate email addresses and SMTP configuration"""
    
    @staticmethod
    def validate_email(email):
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_smtp_config(config):
        """Validate SMTP configuration"""
        required_keys = ['email', 'password', 'server', 'port']
        
        for key in required_keys:
            if key not in config or not config[key]:
                return False, f"Missing or empty: {key}"
        
        if not EmailValidator.validate_email(config['email']):
            return False, "Invalid email address"
        
        if not isinstance(config['port'], int) or config['port'] <= 0:
            return False, "Invalid port number"
        
        return True, "Configuration valid"
    
    @staticmethod
    def test_smtp_connection(config):
        """Test SMTP connection"""
        try:
            if config['port'] == 465:
                server = smtplib.SMTP_SSL(config['server'], config['port'], timeout=10)
            else:
                server = smtplib.SMTP(config['server'], config['port'], timeout=10)
                server.starttls()
            
            server.login(config['email'], config['password'])
            server.quit()
            return True, "Connection successful"
            
        except smtplib.SMTPAuthenticationError:
            return False, "Authentication failed. Check email and password."
        except smtplib.SMTPException as e:
            return False, f"SMTP error: {str(e)}"
        except Exception as e:
            return False, f"Connection error: {str(e)}"