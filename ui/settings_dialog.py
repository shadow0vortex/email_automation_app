"""
Settings Dialog - SMTP Configuration
Dialog for configuring Gmail SMTP settings
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QSpinBox, QMessageBox,
    QGroupBox, QComboBox
)
from PyQt5.QtCore import Qt
from core.email_sender import EmailValidator
import logging

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """SMTP configuration dialog"""
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        
        self.setWindowTitle("SMTP Configuration")
        self.setMinimumWidth(500)
        self.setModal(True)
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # SMTP Settings Group
        smtp_group = QGroupBox("SMTP Server Settings")
        smtp_layout = QFormLayout()
        
        # Provider selection
        self.provider_combo = QComboBox()
        self.provider_combo.addItems([
            "Gmail",
            "Outlook",
            "Yahoo",
            "Office 365",
            "Custom"
        ])
        self.provider_combo.currentTextChanged.connect(self.provider_changed)
        smtp_layout.addRow("Email Provider:", self.provider_combo)
        
        # Email address
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("your.email@gmail.com")
        smtp_layout.addRow("Email Address:", self.email_input)
        
        # Password
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("App-specific password")
        smtp_layout.addRow("App Password:", self.password_input)
        
        # Server
        self.server_input = QLineEdit()
        self.server_input.setText("smtp.gmail.com")
        smtp_layout.addRow("SMTP Server:", self.server_input)
        
        # Port
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(587)
        smtp_layout.addRow("Port:", self.port_input)
        
        smtp_group.setLayout(smtp_layout)
        layout.addWidget(smtp_group)
        
        # Help text
        help_label = QLabel(
            "<b>⚠️ Important:</b><br>"
            "• Gmail requires an App-specific password<br>"
            "• Enable 2-Factor Authentication first<br>"
            "• Generate App Password at: <a href='https://myaccount.google.com/apppasswords'>myaccount.google.com/apppasswords</a><br>"
            "• Regular Gmail password will NOT work<br>"
            "<br>"
            "<b>Rate Limits:</b><br>"
            "• Gmail: 500 emails/day<br>"
            "• Google Workspace: 2,000 emails/day"
        )
        help_label.setOpenExternalLinks(True)
        help_label.setWordWrap(True)
        help_label.setStyleSheet("""
            QLabel {
                background-color: #fff3cd;
                border: 1px solid #ffc107;
                border-radius: 4px;
                padding: 12px;
                font-size: 11px;
            }
        """)
        layout.addWidget(help_label)
        
        # Test connection button
        test_btn_layout = QHBoxLayout()
        test_btn_layout.addStretch()
        
        self.test_btn = QPushButton("🔍 Test Connection")
        self.test_btn.clicked.connect(self.test_connection)
        self.test_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        test_btn_layout.addWidget(self.test_btn)
        test_btn_layout.addStretch()
        
        layout.addLayout(test_btn_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        self.save_btn = QPushButton("✓ Save")
        self.save_btn.clicked.connect(self.save_settings)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def provider_changed(self, provider):
        """Update server settings based on provider"""
        providers = {
            'Gmail': {'server': 'smtp.gmail.com', 'port': 587},
            'Outlook': {'server': 'smtp-mail.outlook.com', 'port': 587},
            'Yahoo': {'server': 'smtp.mail.yahoo.com', 'port': 587},
            'Office 365': {'server': 'smtp.office365.com', 'port': 587}
        }
        
        if provider in providers:
            self.server_input.setText(providers[provider]['server'])
            self.port_input.setValue(providers[provider]['port'])
    
    def load_settings(self):
        """Load saved settings from database"""
        try:
            email = self.db_manager.get_config_value('smtp_email', '')
            password = self.db_manager.get_config_value('smtp_password', '')
            server = self.db_manager.get_config_value('smtp_server', 'smtp.gmail.com')
            port = int(self.db_manager.get_config_value('smtp_port', '587'))
            
            self.email_input.setText(email)
            self.password_input.setText(password)
            self.server_input.setText(server)
            self.port_input.setValue(port)
            
            # Select provider based on server
            if 'gmail.com' in server:
                self.provider_combo.setCurrentText('Gmail')
            elif 'outlook.com' in server:
                self.provider_combo.setCurrentText('Outlook')
            elif 'yahoo.com' in server:
                self.provider_combo.setCurrentText('Yahoo')
            elif 'office365.com' in server:
                self.provider_combo.setCurrentText('Office 365')
            else:
                self.provider_combo.setCurrentText('Custom')
                
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
    
    def validate_inputs(self):
        """Validate form inputs"""
        email = self.email_input.text().strip()
        password = self.password_input.text()
        server = self.server_input.text().strip()
        
        if not email or not password or not server:
            QMessageBox.warning(
                self,
                "Missing Information",
                "Please fill in all required fields."
            )
            return False
        
        if not EmailValidator.is_valid(email):
            QMessageBox.warning(
                self,
                "Invalid Email",
                "Please enter a valid email address."
            )
            return False
        
        return True
    
    def test_connection(self):
        """Test SMTP connection"""
        if not self.validate_inputs():
            return
        
        self.test_btn.setEnabled(False)
        self.test_btn.setText("Testing...")
        
        config = {
            'email': self.email_input.text().strip(),
            'password': self.password_input.text(),
            'server': self.server_input.text().strip(),
            'port': self.port_input.value()
        }
        
        # Test connection
        from core.email_sender import EmailValidator as SMTPValidator
        success, message = SMTPValidator.test_smtp_connection(config)
        
        self.test_btn.setEnabled(True)
        self.test_btn.setText("🔍 Test Connection")
        
        if success:
            QMessageBox.information(
                self,
                "Connection Successful",
                "SMTP connection test successful!\n\n"
                "Your credentials are valid and the server is accessible."
            )
        else:
            QMessageBox.critical(
                self,
                "Connection Failed",
                f"Failed to connect to SMTP server:\n\n{message}\n\n"
                "Please check your credentials and try again."
            )
    
    def save_settings(self):
        """Save SMTP settings to database"""
        if not self.validate_inputs():
            return
        
        try:
            self.db_manager.save_config_value('smtp_email', self.email_input.text().strip())
            self.db_manager.save_config_value('smtp_password', self.password_input.text())
            self.db_manager.save_config_value('smtp_server', self.server_input.text().strip())
            self.db_manager.save_config_value('smtp_port', str(self.port_input.value()))
            
            QMessageBox.information(
                self,
                "Settings Saved",
                "SMTP settings have been saved successfully!"
            )
            
            self.accept()
            
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            QMessageBox.critical(
                self,
                "Save Failed",
                f"Failed to save settings:\n{str(e)}"
            )
    
    def get_smtp_config(self):
        """Return current SMTP configuration"""
        return {
            'email': self.email_input.text().strip(),
            'password': self.password_input.text(),
            'server': self.server_input.text().strip(),
            'port': self.port_input.value()
        }