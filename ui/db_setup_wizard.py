"""
Database Setup Wizard - First-run PostgreSQL configuration
Guides user through database setup process
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSpinBox, QTextEdit, QGroupBox, QFormLayout,
    QCheckBox, QMessageBox, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
import psycopg2
import logging

logger = logging.getLogger(__name__)


class DatabaseTestThread(QThread):
    """Thread for testing database connection"""
    
    result = pyqtSignal(bool, str)
    
    def __init__(self, config):
        super().__init__()
        self.config = config
    
    def run(self):
        """Test database connection"""
        try:
            # Try to connect to PostgreSQL
            conn = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                database='postgres',  # Connect to default database first
                user=self.config['user'],
                password=self.config['password']
            )
            conn.close()
            self.result.emit(True, "Connection successful!")
            
        except psycopg2.OperationalError as e:
            self.result.emit(False, f"Connection failed: {str(e)}")
        except Exception as e:
            self.result.emit(False, f"Error: {str(e)}")


class DatabaseSetupWizard(QDialog):
    """First-run database setup wizard"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Database Setup Wizard")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        
        self.config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'email_automation',
            'user': 'postgres',
            'password': ''
        }
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Title
        title = QLabel("🗄️ Database Setup")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Description
        desc = QLabel(
            "Welcome! Let's set up your PostgreSQL database.\n"
            "This is a one-time setup to configure your email automation system."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; padding: 10px;")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
        
        # Database configuration group
        config_group = QGroupBox("PostgreSQL Configuration")
        config_layout = QFormLayout()
        
        # Host
        self.host_input = QLineEdit(self.config['host'])
        self.host_input.setPlaceholderText("localhost or IP address")
        config_layout.addRow("Host:", self.host_input)
        
        # Port
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(self.config['port'])
        config_layout.addRow("Port:", self.port_input)
        
        # Database name
        self.database_input = QLineEdit(self.config['database'])
        self.database_input.setPlaceholderText("email_automation")
        config_layout.addRow("Database Name:", self.database_input)
        
        # Username
        self.user_input = QLineEdit(self.config['user'])
        self.user_input.setPlaceholderText("postgres")
        config_layout.addRow("Username:", self.user_input)
        
        # Password
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Your PostgreSQL password")
        config_layout.addRow("Password:", self.password_input)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Auto-create database option
        self.auto_create_checkbox = QCheckBox(
            "Automatically create database if it doesn't exist"
        )
        self.auto_create_checkbox.setChecked(True)
        layout.addWidget(self.auto_create_checkbox)
        
        # Test connection button
        test_btn_layout = QHBoxLayout()
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
        test_btn_layout.addStretch()
        test_btn_layout.addWidget(self.test_btn)
        test_btn_layout.addStretch()
        layout.addLayout(test_btn_layout)
        
        # Status text
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(100)
        self.status_text.setPlaceholderText("Connection status will appear here...")
        layout.addWidget(self.status_text)
        
        # Help text
        help_label = QLabel(
            "📌 <b>Note:</b> Make sure PostgreSQL is installed and running on your system.<br>"
            "For Windows: Download from <a href='https://www.postgresql.org/download/'>postgresql.org</a>"
        )
        help_label.setOpenExternalLinks(True)
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #666; font-size: 11px; padding: 10px; background-color: #f8f9fa; border-radius: 4px;")
        layout.addWidget(help_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)
        button_layout.addWidget(cancel_btn)
        
        self.save_btn = QPushButton("✓ Save & Continue")
        self.save_btn.clicked.connect(self.save_configuration)
        self.save_btn.setEnabled(False)
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
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def test_connection(self):
        """Test database connection"""
        self.test_btn.setEnabled(False)
        self.test_btn.setText("Testing...")
        self.status_text.clear()
        self.status_text.append("Testing connection to PostgreSQL...")
        
        # Get current configuration
        config = {
            'host': self.host_input.text().strip(),
            'port': self.port_input.value(),
            'database': self.database_input.text().strip(),
            'user': self.user_input.text().strip(),
            'password': self.password_input.text()
        }
        
        # Validate inputs
        if not config['host'] or not config['user'] or not config['password']:
            self.status_text.append("\n❌ Error: Please fill in all required fields")
            self.test_btn.setEnabled(True)
            self.test_btn.setText("🔍 Test Connection")
            return
        
        # Test connection in background thread
        self.test_thread = DatabaseTestThread(config)
        self.test_thread.result.connect(self.handle_test_result)
        self.test_thread.start()
    
    def handle_test_result(self, success, message):
        """Handle connection test result"""
        self.test_btn.setEnabled(True)
        self.test_btn.setText("🔍 Test Connection")
        
        if success:
            self.status_text.append(f"\n✅ {message}")
            self.status_text.append("\nPostgreSQL connection verified successfully!")
            self.save_btn.setEnabled(True)
            
            # Update config
            self.config = {
                'host': self.host_input.text().strip(),
                'port': self.port_input.value(),
                'database': self.database_input.text().strip(),
                'user': self.user_input.text().strip(),
                'password': self.password_input.text()
            }
        else:
            self.status_text.append(f"\n❌ {message}")
            self.status_text.append("\nPlease check your configuration and try again.")
            self.save_btn.setEnabled(False)
    
    def save_configuration(self):
        """Save configuration and close wizard"""
        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Confirm Setup",
            f"This will create the database '{self.config['database']}' and initialize all required tables.\n\n"
            "Do you want to proceed?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.accept()
        
    def get_database_config(self):
        """Return the database configuration"""
        return self.config


class QuickStartDialog(QDialog):
    """Quick start guide after setup"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quick Start Guide")
        self.setMinimumSize(500, 400)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("🎉 Setup Complete!")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        guide_text = """
        <h3>Quick Start Guide:</h3>
        <ol>
            <li><b>Configure SMTP Settings</b><br>
            Click Settings → SMTP Configuration to enter your Gmail credentials</li>
            
            <li><b>Upload Recipients</b><br>
            Prepare an Excel file with Email and Name columns, then upload it</li>
            
            <li><b>Compose Email</b><br>
            Either upload an HTML template or use the built-in editor</li>
            
            <li><b>Preview & Send</b><br>
            Preview your email, then click Send to start the campaign</li>
            
            <li><b>Monitor Progress</b><br>
            Watch real-time progress and check logs for results</li>
        </ol>
        
        <h3>Important Notes:</h3>
        <ul>
            <li>Use Gmail App-specific password (not your regular password)</li>
            <li>Gmail limit: 500 emails/day for regular accounts</li>
            <li>Recommended delay: 2-3 seconds between emails</li>
        </ul>
        """
        
        guide_label = QLabel(guide_text)
        guide_label.setWordWrap(True)
        guide_label.setOpenExternalLinks(True)
        layout.addWidget(guide_label)
        
        layout.addStretch()
        
        close_btn = QPushButton("Got it!")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 10px 30px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)