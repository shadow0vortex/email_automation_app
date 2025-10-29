import sys
import os
import json
import openpyxl 
import logging
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QTabWidget, QFileDialog, QMessageBox, QAction,
    QToolBar, QLabel, QProgressBar, QMenu, QPushButton, QVBoxLayout, QWidget,
    QTableWidgetItem, QTextEdit, QTableWidget, QHeaderView, QInputDialog, QDialog,
    QStatusBar, QLineEdit
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer, QDateTime
from PyQt5.QtGui import QIcon, QKeySequence

# Core & UI module imports (as in your original)
from core.email_sender import EmailSenderThread
from core.excel_processor import ExcelProcessor
from core.template_engine import TemplateEngine
from core.validators import EmailValidator
from ui.settings_dialog import SettingsDialog
from ui.email_editor import PreviewDialog
from ui.email_editor import EmailEditorWidget
#from ui.template_library import TemplateLibrary
from core.database_manager import DatabaseManager


class MainWindow(QMainWindow):
    def __init__(self, db_manager=None):
        super().__init__()
        self.setWindowTitle("Bulk Email Automation System")
        self.db = db_manager if db_manager else DatabaseManager()
        self.setGeometry(100, 100, 1200, 800)
        

        self.db = DatabaseManager()
        self.excel_processor = ExcelProcessor()
        self.template_engine = TemplateEngine()
        self.email_validator = EmailValidator()

        self.recipients = []
        self.logs = []
        self.sender_thread = None

        self.init_ui()
        self.apply_stylesheet()
        self.setup_shortcuts()
        self.load_saved_settings()

    # ------------------------------ UI INITIALIZATION ------------------------------ #

    def init_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Tabs
        self.compose_tab = QWidget()
        self.recipient_tab = QWidget()
        self.log_tab = QWidget()
        self.campaign_tab = QWidget()

        self.tabs.addTab(self.compose_tab, "Compose")
        self.tabs.addTab(self.recipient_tab, "Recipients")
        self.tabs.addTab(self.log_tab, "Logs")
        self.tabs.addTab(self.campaign_tab, "Campaigns")

        self.init_compose_tab()
        self.init_recipient_tab()
        self.init_log_tab()
        self.init_campaign_tab()
        self.init_toolbar()
        self.init_statusbar()

    def init_compose_tab(self):
        layout = QVBoxLayout()
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("Email Subject")
        self.body_editor = EmailEditorWidget()
        layout.addWidget(self.subject_input)
        layout.addWidget(self.body_editor)
        self.compose_tab.setLayout(layout)

    def init_recipient_tab(self):
        layout = QVBoxLayout()
        self.recipient_table = QTableWidget()
        self.recipient_table.setColumnCount(3)
        self.recipient_table.setHorizontalHeaderLabels(["Name", "Email", "Status"])
        self.recipient_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        import_btn = QPushButton("Import Recipients")
        import_btn.clicked.connect(self.import_recipients)

        layout.addWidget(import_btn)
        layout.addWidget(self.recipient_table)
        self.recipient_tab.setLayout(layout)

    def init_log_tab(self):
        layout = QVBoxLayout()
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        layout.addWidget(self.log_view)
        self.log_tab.setLayout(layout)

    def init_campaign_tab(self):
        layout = QVBoxLayout()
        self.campaign_table = QTableWidget()
        self.campaign_table.setColumnCount(4)
        self.campaign_table.setHorizontalHeaderLabels(["Campaign Name", "Date", "Emails Sent", "Status"])
        self.campaign_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.campaign_table)
        self.campaign_tab.setLayout(layout)

    def init_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        send_action = QAction(QIcon("assets/send.png"), "Send Emails", self)
        send_action.triggered.connect(self.start_sending)
        toolbar.addAction(send_action)

        preview_action = QAction(QIcon("assets/preview.png"), "Preview", self)
        preview_action.triggered.connect(self.preview_email)
        toolbar.addAction(preview_action)

        settings_action = QAction(QIcon("assets/settings.png"), "SMTP Settings", self)
        settings_action.triggered.connect(self.open_smtp_settings)
        toolbar.addAction(settings_action)

    def init_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Ready")
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.status_bar.addPermanentWidget(self.status_label)
        self.status_bar.addPermanentWidget(self.progress_bar)

    # ------------------------------ FUNCTIONALITY ------------------------------ #

    def import_recipients(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Excel File", "", "Excel Files (*.xlsx *.csv)")
        if not file_path:
            return

        try:
            self.recipients = self.excel_processor.load_recipients(file_path)
            self.recipient_table.setRowCount(len(self.recipients))
            for i, recipient in enumerate(self.recipients):
                self.recipient_table.setItem(i, 0, QTableWidgetItem(recipient["Name"]))
                self.recipient_table.setItem(i, 1, QTableWidgetItem(recipient["Email"]))
                self.recipient_table.setItem(i, 2, QTableWidgetItem("Pending"))
            self.status_label.setText(f"Imported {len(self.recipients)} recipients.")
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to load recipients:\n{str(e)}")

    def preview_email(self):
        subject = self.subject_input.text()
        body = self.body_editor.get_html()
        if not subject or not body.strip():
            QMessageBox.warning(self, "Empty Fields", "Please fill both subject and body before previewing.")
            return
        preview = PreviewDialog(subject, body)
        preview.exec_()

    def start_sending(self):
        if not self.validate_before_send():
            return

        smtp_config = self.db.get_config_value("smtp_settings")
        if not smtp_config:
            QMessageBox.warning(self, "Missing SMTP", "Please configure SMTP settings first.")
            return

        self.sender_thread = EmailSenderThread(
            smtp_config=smtp_config,
            recipients=self.recipients,
            subject=self.subject_input.text(),
            body=self.body_editor.get_html(),
        )

        self.sender_thread.log_signal.connect(self.append_log)
        self.sender_thread.progress_signal.connect(self.update_progress)
        self.sender_thread.finished_signal.connect(self.on_send_complete)
        self.sender_thread.start()

        self.status_label.setText("Sending emails...")
        self.progress_bar.setValue(0)

    def append_log(self, message):
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        self.log_view.append(f"[{timestamp}] {message}")

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def on_send_complete(self):
        self.status_label.setText("All emails sent successfully.")
        QMessageBox.information(self, "Completed", "All emails have been sent.")

    # ------------------------------ PART 3 METHODS ------------------------------ #

    def load_saved_settings(self):
        try:
            smtp_settings = self.db.get_config_value("smtp_settings")
            if smtp_settings:
                self.status_label.setText("SMTP Config Loaded")
            else:
                self.status_label.setText("No SMTP Config Found")

            last_delay = self.db.get_config_value("default_delay")
            if last_delay:
                logging.info(f"Default delay: {last_delay}")

            last_used_file = self.db.get_config_value("last_excel_path")
            if last_used_file and os.path.exists(last_used_file):
                logging.info(f"Last file loaded: {last_used_file}")

            self.logs = self.db.get_recent_logs(limit=200)
            for log in self.logs:
                self.append_log(f"{log['timestamp']} - {log['message']}")

        except Exception as e:
            logging.error(f"Error loading settings: {e}")

    def open_smtp_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            config = dialog.load_settings()
            self.db.save_config_value("smtp_settings", config)
            QMessageBox.information(self, "Saved", "SMTP Settings updated successfully!")

    def show_about(self):
        QMessageBox.information(
            self,
            "About",
            "Bulk Email Automation System\nVersion 1.0\nDeveloped with ❤️ using PyQt5",
        )

    def show_documentation(self):
        QMessageBox.information(
            self,
            "Documentation",
            "For setup and usage guide, visit:\nhttps://github.com/your-repo/docs",
        )

    def apply_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f9f9f9;
            }
            QTabWidget::pane {
                border: 1px solid #ccc;
                background-color: #fff;
            }
            QPushButton {
                background-color: #0078d7;
                color: white;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #005fa3;
            }
            QStatusBar QLabel {
                font-weight: bold;
            }
        """)

    def closeEvent(self, event):
        if self.sender_thread and self.sender_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Exit Confirmation",
                "Emails are still being sent. Do you really want to exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
            self.sender_thread.terminate()
        self.db.save_config_value("window_geometry", self.saveGeometry())
        event.accept()

    def update_recipient_count(self):
        self.status_label.setText(f"{len(self.recipients)} Recipients Loaded")

    def update_sent_count(self, sent, total):
        self.status_label.setText(f"Sent {sent}/{total} emails")

    def validate_before_send(self):
        if not self.db.get_config_value("smtp_settings"):
            QMessageBox.warning(self, "SMTP Missing", "Configure SMTP settings before sending.")
            return False
        if not self.recipients:
            QMessageBox.warning(self, "No Recipients", "Please import recipient list first.")
            return False
        if not self.subject_input.text().strip():
            QMessageBox.warning(self, "Missing Subject", "Please enter an email subject.")
            return False
        if not self.body_editor.get_html().strip():
            QMessageBox.warning(self, "Empty Body", "Please compose an email body.")
            return False
        return True

    def show_statistics(self):
        stats = self.db.get_log_statistics()
        QMessageBox.information(
            self,
            "Statistics",
            f"Total Sent: {stats['sent']}\nFailed: {stats['failed']}\nPending: {stats['pending']}",
        )

    def clear_logs(self):
        self.db.cleanup_old_logs(days=90)
        self.log_view.clear()
        QMessageBox.information(self, "Logs Cleared", "Old logs have been deleted.")

    def import_recipients_from_db(self):
        data = self.db.get_recipients()
        self.recipient_table.setRowCount(len(data))
        for i, r in enumerate(data):
            self.recipient_table.setItem(i, 0, QTableWidgetItem(r["name"]))
            self.recipient_table.setItem(i, 1, QTableWidgetItem(r["email"]))
            self.recipient_table.setItem(i, 2, QTableWidgetItem(r["status"]))
        self.status_label.setText(f"{len(data)} recipients loaded from database.")

    def save_recipients_to_db(self):
        rows = self.recipient_table.rowCount()
        data = []
        for i in range(rows):
            data.append({
                "name": self.recipient_table.item(i, 0).text(),
                "email": self.recipient_table.item(i, 1).text(),
                "status": self.recipient_table.item(i, 2).text(),
            })
        self.db.save_recipients(data)
        QMessageBox.information(self, "Saved", "Recipients saved to database successfully.")

    def setup_shortcuts(self):
        self.import_shortcut = QAction(self)
        self.import_shortcut.setShortcut(QKeySequence("Ctrl+O"))
        self.import_shortcut.triggered.connect(self.import_recipients)
        self.addAction(self.import_shortcut)

        self.settings_shortcut = QAction(self)
        self.settings_shortcut.setShortcut(QKeySequence("Ctrl+S"))
        self.settings_shortcut.triggered.connect(self.open_smtp_settings)
        self.addAction(self.settings_shortcut)

        self.send_shortcut = QAction(self)
        self.send_shortcut.setShortcut(QKeySequence("Ctrl+Enter"))
        self.send_shortcut.triggered.connect(self.start_sending)
        self.addAction(self.send_shortcut)

        self.preview_shortcut = QAction(self)
        self.preview_shortcut.setShortcut(QKeySequence("Ctrl+P"))
        self.preview_shortcut.triggered.connect(self.preview_email)
        self.addAction(self.preview_shortcut)

        self.refresh_logs_shortcut = QAction(self)
        self.refresh_logs_shortcut.setShortcut(QKeySequence("F5"))
        self.refresh_logs_shortcut.triggered.connect(self.load_saved_settings)
        self.addAction(self.refresh_logs_shortcut)

    def save_config_value(self, key, value):
        """Wrapper to save a configuration key-value pair"""
        try:
            self.db.save_config_value(key, value)
            logging.info(f"Saved config: {key}")
        except Exception as e:
            logging.error(f"Error saving config value: {e}")

    def get_config_value(self, key, default=None):
        """Wrapper to get configuration value"""
        try:
            return self.db.get_config_value(key, default)
        except Exception as e:
            logging.error(f"Error getting config value: {e}")
            return default

# ------------------------------ MAIN ENTRY POINT ------------------------------ #
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

