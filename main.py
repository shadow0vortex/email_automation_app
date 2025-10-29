"""
Bulk Email Automation Software - Main Entry Point
Professional email sender with PostgreSQL database and PyQt5 GUI
"""

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QSplashScreen, QMessageBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import core modules
from core.database_manager import DatabaseManager
from core.db_setup import DatabaseSetup, check_database_exists
from ui.main_window import MainWindow
from ui.db_setup_wizard import DatabaseSetupWizard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Application:
    """Main application class"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Bulk Email Automation")
        self.app.setOrganizationName("EmailAutomation")
        
        # Set application style
        self.setup_style()
        
        self.db_manager = None
        self.main_window = None
    
    def setup_style(self):
        """Setup application style"""
        self.app.setStyle('Fusion')
        
        # Set default font
        font = QFont("Segoe UI", 9)
        self.app.setFont(font)
    
    def show_splash_screen(self):
        """Show splash screen during initialization"""
        splash_text = """
        <div style='text-align: center; padding: 50px; font-family: Arial;'>
            <h1 style='color: #007bff; margin: 0;'>Bulk Email Automation</h1>
            <p style='color: #666; font-size: 14px;'>Professional Email Sender</p>
            <p style='color: #999; font-size: 12px;'>Initializing...</p>
        </div>
        """
        
        # Create a simple splash window (without requiring image file)
        from PyQt5.QtWidgets import QLabel
        splash = QLabel(splash_text)
        splash.setAlignment(Qt.AlignCenter)
        splash.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 2px solid #007bff;
                border-radius: 10px;
                min-width: 400px;
                min-height: 200px;
            }
        """)
        splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        splash.show()
        
        return splash
    
    def check_first_run(self):
        """Check if this is the first run"""
        config_file = "config/database.json"
        
        # Check if config exists
        if not os.path.exists(config_file):
            logger.info("First run detected - no config file")
            return True
        
        # Try to load config and check database
        try:
            db_manager = DatabaseManager(config_file)
            if not db_manager.test_connection():
                logger.info("First run detected - database connection failed")
                return True
            
            # Check if tables exist
            if not check_database_exists(db_manager.config):
                logger.info("First run detected - tables don't exist")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking first run: {e}")
            return True
    
    def run_first_time_setup(self):
        """Run first-time database setup wizard"""
        logger.info("Starting first-time setup wizard")
        
        wizard = DatabaseSetupWizard()
        result = wizard.exec_()
        
        if result == wizard.Accepted:
            config = wizard.get_database_config()
            
            # Initialize database
            db_setup = DatabaseSetup(config)
            success = db_setup.setup_complete()
            
            if success:
                # Save configuration
                db_manager = DatabaseManager()
                db_manager.save_config(config)
                
                QMessageBox.information(
                    None,
                    "Setup Complete",
                    "Database has been set up successfully!\nYou can now use the application."
                )
                return True
            else:
                QMessageBox.critical(
                    None,
                    "Setup Failed",
                    "Failed to set up database. Please check your configuration and try again."
                )
                return False
        else:
            logger.info("Setup wizard cancelled by user")
            return False
    
    def initialize_database(self):
        """Initialize database manager"""
        try:
            self.db_manager = DatabaseManager()
            
            if not self.db_manager.test_connection():
                raise Exception("Database connection failed")
            
            logger.info("Database initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            QMessageBox.critical(
                None,
                "Database Error",
                f"Failed to connect to database:\n{str(e)}\n\nPlease check your configuration."
            )
            return False
    
    def create_main_window(self):
        """Create and show main window"""
        try:
            self.main_window = MainWindow(self.db_manager)
            self.main_window.show()
            logger.info("Main window created and displayed")
            return True
        except Exception as e:
            logger.error(f"Failed to create main window: {e}")
            QMessageBox.critical(
                None,
                "Error",
                f"Failed to create main window:\n{str(e)}"
            )
            return False
    
    def run(self):
        """Main application entry point"""
        try:
            # Create logs directory
            os.makedirs('logs', exist_ok=True)
            os.makedirs('config', exist_ok=True)
            os.makedirs('exports', exist_ok=True)
            
            logger.info("="*50)
            logger.info("Starting Bulk Email Automation Software")
            logger.info("="*50)
            
            # Show splash screen
            splash = self.show_splash_screen()
            
            # Small delay for splash screen
            QTimer.singleShot(1000, splash.close)
            self.app.processEvents()
            
            # Check if first run
            if self.check_first_run():
                splash.close()
                logger.info("First run detected - launching setup wizard")
                
                if not self.run_first_time_setup():
                    logger.info("Setup cancelled - exiting application")
                    return 0
            
            # Initialize database
            if not self.initialize_database():
                return 1
            
            # Create main window
            splash.close()
            if not self.create_main_window():
                return 1
            
            logger.info("Application started successfully")
            
            # Run event loop
            return self.app.exec_()
            
        except Exception as e:
            logger.critical(f"Critical error in main application: {e}", exc_info=True)
            QMessageBox.critical(
                None,
                "Critical Error",
                f"A critical error occurred:\n{str(e)}\n\nThe application will now exit."
            )
            return 1
        
        finally:
            # Cleanup
            if self.db_manager:
                self.db_manager.close_all_connections()
            logger.info("Application shut down")


def main():
    """Entry point for the application"""
    app = Application()
    sys.exit(app.run())


if __name__ == "__main__":
    main()