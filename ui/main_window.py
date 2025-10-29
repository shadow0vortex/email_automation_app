import sys
import os
import json
import openpyxl
import logging
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QTabWidget, QFileDialog, QMessageBox, QAction,
    QToolBar, QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget,
    QTableWidgetItem, QTextEdit, QTableWidget, QHeaderView, QDialog,
    QStatusBar, QLineEdit, QHBoxLayout
)
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QIcon, QKeySequence, QColor

# Core & UI module imports
from core.email_sender import EmailSenderThread
from core.excel_processor import ExcelProcessor
from core.template_engine import TemplateEngine
from core.validators import EmailValidator
from ui.settings_dialog import SettingsDialog
from ui.email_editor import PreviewDialog, EmailEditorWidget
from core.database_manager import DatabaseManager


class MainWindow(QMainWindow):
    def __init__(self, db_manager=None):
        super().__init__()
        self.setWindowTitle("Bulk Email Automation System")
        self.db = db_manager if db_manager else DatabaseManager()
        self.setGeometry(100, 100, 1200, 800)

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

    # ---------------------------------------------------------------------- #
    #                              UI SETUP                                 #
    # ---------------------------------------------------------------------- #
    def init_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

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

    # ----------------------------- COMPOSE TAB ----------------------------- #
    def init_compose_tab(self):
        """Initialize compose tab with template selection"""
        from PyQt5.QtWidgets import (
            QGroupBox, QRadioButton, QButtonGroup, QFileDialog, QComboBox
        )

        layout = QVBoxLayout()
        layout.setSpacing(10)

        # ============ TEMPLATE SELECTION GROUP ============
        template_group = QGroupBox("📧 Email Template")
        template_layout = QVBoxLayout()

        self.template_button_group = QButtonGroup()

        self.use_editor_radio = QRadioButton("Use Built-in Editor")
        self.use_editor_radio.setChecked(True)
        self.use_editor_radio.toggled.connect(self.toggle_template_source)
        self.template_button_group.addButton(self.use_editor_radio)
        template_layout.addWidget(self.use_editor_radio)

        self.use_library_radio = QRadioButton("Use Template Library")
        self.use_library_radio.toggled.connect(self.toggle_template_source)
        self.template_button_group.addButton(self.use_library_radio)
        template_layout.addWidget(self.use_library_radio)

        self.use_file_radio = QRadioButton("Upload HTML File")
        self.use_file_radio.toggled.connect(self.toggle_template_source)
        self.template_button_group.addButton(self.use_file_radio)
        template_layout.addWidget(self.use_file_radio)

        # Template library dropdown
        library_layout = QHBoxLayout()
        library_layout.addWidget(QLabel("Select Template:"))
        self.template_library_combo = QComboBox()
        self.template_library_combo.addItems([
            "Professional Business",
            "Simple Clean",
            "Marketing Campaign",
            "Newsletter Style"
        ])
        self.template_library_combo.currentTextChanged.connect(self.load_library_template)
        library_layout.addWidget(self.template_library_combo)
        library_layout.addStretch()
        template_layout.addLayout(library_layout)
        self.template_library_combo.hide()

        # Upload HTML button
        self.upload_template_btn = QPushButton("📁 Browse HTML File")
        self.upload_template_btn.clicked.connect(self.upload_html_template)
        self.upload_template_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        template_layout.addWidget(self.upload_template_btn)
        self.upload_template_btn.hide()

        template_group.setLayout(template_layout)
        layout.addWidget(template_group)

        # ============ SUBJECT LINE ============
        subject_layout = QHBoxLayout()
        subject_layout.addWidget(QLabel("Subject:"))
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText(
            "Enter email subject (you can use {name}, {company}, etc.)"
        )
        subject_layout.addWidget(self.subject_input)
        layout.addLayout(subject_layout)

        # ============ EMAIL BODY ============
        body_label = QLabel("Email Body:")
        body_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(body_label)

        self.body_editor = EmailEditorWidget()
        layout.addWidget(self.body_editor)

        # ============ PLACEHOLDER INFO ============
        placeholder_info = QLabel(
            "💡 <b>Tip:</b> Use placeholders like {name}, {email}, {company} — "
            "they will be replaced with actual recipient data."
        )
        placeholder_info.setWordWrap(True)
        placeholder_info.setStyleSheet("""
            QLabel {
                background-color: #e7f3ff;
                border-left: 4px solid #2196F3;
                padding: 10px;
                border-radius: 4px;
                color: #1976D2;
            }
        """)
        layout.addWidget(placeholder_info)

        # ============ ACTION BUTTONS ============
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.clicked.connect(self.clear_compose)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        button_layout.addWidget(clear_btn)

        preview_btn = QPushButton("👁️ Preview")
        preview_btn.clicked.connect(self.preview_email)
        preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        button_layout.addWidget(preview_btn)

        send_btn = QPushButton("📨 Send Emails")
        send_btn.clicked.connect(self.start_sending)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 8px 30px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        button_layout.addWidget(send_btn)

        layout.addLayout(button_layout)
        self.compose_tab.setLayout(layout)

    # ----------------------------- TEMPLATE LOGIC ----------------------------- #
    def toggle_template_source(self):
        """Switch template source"""
        if self.use_editor_radio.isChecked():
            self.template_library_combo.hide()
            self.upload_template_btn.hide()
            self.body_editor.setEnabled(True)
        elif self.use_library_radio.isChecked():
            self.template_library_combo.show()
            self.upload_template_btn.hide()
            self.body_editor.setEnabled(False)
            self.load_library_template(self.template_library_combo.currentText())
        elif self.use_file_radio.isChecked():
            self.template_library_combo.hide()
            self.upload_template_btn.show()
            self.body_editor.setEnabled(False)

    def load_library_template(self, template_name):
        """Load built-in template"""
        from core.template_engine import TemplateLibrary

        templates = {
            "Professional Business": TemplateLibrary.get_professional_template(),
            "Simple Clean": TemplateLibrary.get_simple_template(),
            "Marketing Campaign": TemplateLibrary.get_marketing_template(),
            "Newsletter Style": TemplateLibrary.get_professional_template(),
        }

        template_html = templates.get(template_name, "")
        if template_html:
            self.body_editor.set_html(template_html)
            self.status_label.setText(f"Loaded template: {template_name}")

    def upload_html_template(self):
        """Upload custom HTML file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select HTML Template", "", "HTML Files (*.html *.htm);;All Files (*.*)"
        )
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            self.body_editor.set_html(html_content)
            self.status_label.setText(f"Loaded template: {os.path.basename(file_path)}")
            QMessageBox.information(
                self, "Template Loaded",
                f"Successfully loaded HTML template:\n{os.path.basename(file_path)}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load template:\n{e}")

    def clear_compose(self):
        """Clear subject and body"""
        reply = QMessageBox.question(
            self, "Clear Compose",
            "Are you sure you want to clear the subject and body?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.subject_input.clear()
            self.body_editor.clear()
            self.status_label.setText("Compose form cleared")



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
        """Initialize campaign history tab"""
        from PyQt5.QtWidgets import QFrame, QAbstractItemView
        from PyQt5.QtCore import QTimer

        layout = QVBoxLayout()

        # Stats cards
        stats_layout = QHBoxLayout()
        total_campaigns_card = self.create_stat_card("📊 Total Campaigns", "0", "#007bff")
        stats_layout.addWidget(total_campaigns_card)
        total_emails_card = self.create_stat_card("📧 Total Emails Sent", "0", "#28a745")
        stats_layout.addWidget(total_emails_card)
        success_rate_card = self.create_stat_card("✓ Success Rate", "0%", "#17a2b8")
        stats_layout.addWidget(success_rate_card)
        layout.addLayout(stats_layout)

        # Controls
        controls_layout = QHBoxLayout()
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_campaigns)
        export_btn = QPushButton("📥 Export Campaigns")
        export_btn.clicked.connect(self.export_campaigns)

        controls_layout.addWidget(refresh_btn)
        controls_layout.addWidget(export_btn)
        controls_layout.addStretch()

        search_label = QLabel("Search:")
        self.campaign_search = QLineEdit()
        self.campaign_search.setPlaceholderText("Search campaigns...")
        self.campaign_search.textChanged.connect(self.filter_campaigns)
        self.campaign_search.setMaximumWidth(250)

        controls_layout.addWidget(search_label)
        controls_layout.addWidget(self.campaign_search)
        layout.addLayout(controls_layout)

        # Table
        self.campaigns_table = QTableWidget()
        self.campaigns_table.setColumnCount(7)
        self.campaigns_table.setHorizontalHeaderLabels([
            "Campaign Name", "Subject", "Total", "Successful",
            "Failed", "Start Time", "Duration"
        ])
        self.campaigns_table.setAlternatingRowColors(True)
        self.campaigns_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.campaigns_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.campaigns_table.horizontalHeader().setStretchLastSection(True)

        self.campaigns_table.doubleClicked.connect(self.view_campaign_details)
        layout.addWidget(self.campaigns_table)

        info_label = QLabel("💡 Double-click a campaign to view detailed logs")
        info_label.setStyleSheet("color:#666; font-style:italic; padding:5px;")
        layout.addWidget(info_label)

        self.campaign_tab.setLayout(layout)

        # Auto-refresh
        self.campaign_refresh_timer = QTimer()
        self.campaign_refresh_timer.timeout.connect(self.load_campaigns)
        self.campaign_refresh_timer.start(30000)

    def create_stat_card(self, title, value, color):
        from PyQt5.QtWidgets import QFrame
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-left: 4px solid {color};
                border-radius: 4px;
                padding: 15px;
            }}
        """)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(title))
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size:24px; font-weight:bold; color:{color};")
        layout.addWidget(value_label)
        card.setLayout(layout)
        return card

    def load_campaigns(self):
        """Load campaigns from DB"""
        try:
            campaigns = self.db.get_recent_campaigns(limit=100)
            self.campaigns_table.setRowCount(0)
            total_campaigns = len(campaigns)
            total_emails, total_successful = 0, 0

            for c in campaigns:
                row = self.campaigns_table.rowCount()
                self.campaigns_table.insertRow(row)
                self.campaigns_table.setItem(row, 0, QTableWidgetItem(c['name']))
                self.campaigns_table.setItem(row, 1, QTableWidgetItem(c.get('subject', 'N/A')))
                total = c['total_emails']
                successful = c['successful']
                total_emails += total
                total_successful += successful
                self.campaigns_table.setItem(row, 2, QTableWidgetItem(str(total)))
                success_item = QTableWidgetItem(str(successful))
                success_item.setForeground(QColor(40, 167, 69))
                self.campaigns_table.setItem(row, 3, success_item)
                failed_item = QTableWidgetItem(str(c['failed']))
                failed_item.setForeground(QColor(220, 53, 69))
                self.campaigns_table.setItem(row, 4, failed_item)
                self.campaigns_table.setItem(row, 5, QTableWidgetItem(str(c.get('start_time', 'N/A'))))
                self.campaigns_table.setItem(row, 6, QTableWidgetItem("N/A"))

            success_rate = (total_successful / total_emails * 100) if total_emails else 0
            self.update_stat_cards(total_campaigns, total_emails, success_rate)
            self.status_label.setText(f"Loaded {total_campaigns} campaigns")
        except Exception as e:
            logging.error(f"Error loading campaigns: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load campaigns:\n{e}")

    def update_stat_cards(self, total_campaigns, total_emails, success_rate):
        """Update statistics display"""
        logging.info(f"Campaigns: {total_campaigns}, Emails: {total_emails}, Rate: {success_rate}%")

    def filter_campaigns(self, text):
        """Filter campaigns"""
        for row in range(self.campaigns_table.rowCount()):
            visible = any(
                text.lower() in (self.campaigns_table.item(row, c).text().lower() if self.campaigns_table.item(row, c) else "")
                for c in range(self.campaigns_table.columnCount())
            )
            self.campaigns_table.setRowHidden(row, not visible)

    def view_campaign_details(self):
        """View campaign logs"""
        row = self.campaigns_table.currentRow()
        if row < 0:
            return
        campaign_name = self.campaigns_table.item(row, 0).text()
        self.tabs.setCurrentWidget(self.log_tab)
        QMessageBox.information(self, "Campaign", f"Viewing logs for: {campaign_name}")

    def export_campaigns(self):
        """Export campaigns"""
        from datetime import datetime
        import csv

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Campaigns",
            f"campaigns_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )
        if not file_path:
            return

        try:
            campaigns = self.db.get_recent_campaigns(limit=1000)
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Campaign Name', 'Subject', 'Total', 'Successful', 'Failed', 'Start', 'End'])
                for c in campaigns:
                    writer.writerow([c['name'], c.get('subject', ''), c['total_emails'],
                                     c['successful'], c['failed'], c.get('start_time', ''), c.get('end_time', '')])
            QMessageBox.information(self, "Export", f"Campaigns exported to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))

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
        """Start sending emails"""
        if not self.validate_before_send():
            return

        # Retrieve SMTP settings from database (stored individually)
        smtp_email = self.db.get_config_value("smtp_email")
        smtp_password = self.db.get_config_value("smtp_password")
        smtp_server = self.db.get_config_value("smtp_server")
        smtp_port = self.db.get_config_value("smtp_port")
    
        # Check if SMTP is configured
        if not smtp_email or not smtp_password or not smtp_server or not smtp_port:
            QMessageBox.warning(
                self, 
                "Missing SMTP Configuration", 
                "Please configure SMTP settings first.\n\nGo to Settings → SMTP Configuration"
            )
            return
    
        # Construct SMTP config dictionary
        smtp_config = {
            'email': smtp_email,
            'password': smtp_password,
            'server': smtp_server,
            'port': int(smtp_port)
        }
    
        # Get delay setting
        delay = float(self.db.get_config_value("default_delay", "2"))
    
        # Create campaign in database
        campaign_name = f"Campaign_{QDateTime.currentDateTime().toString('yyyyMMdd_HHmmss')}"
        campaign_id = self.db.create_campaign(
            name=campaign_name,
            total_emails=len(self.recipients),
            subject=self.subject_input.text()
        )
    
        if not campaign_id:
            QMessageBox.critical(self, "Error", "Failed to create campaign in database.")
            return
    
        # Convert recipients list to DataFrame format expected by EmailSenderThread
        import pandas as pd
        recipients_df = pd.DataFrame(self.recipients)
    
        # Create and start email sender thread
        self.sender_thread = EmailSenderThread(
            smtp_config=smtp_config,
            recipients_df=recipients_df,
            subject=self.subject_input.text(),
            body_html=self.body_editor.get_html(),
            delay=delay,
            campaign_id=campaign_id,
            db_manager=self.db
        )
    
        # Connect signals
        self.sender_thread.log_signal.connect(self.handle_log_signal)
        self.sender_thread.progress.connect(self.update_progress)
        self.sender_thread.status_signal.connect(self.handle_status_signal)
        self.sender_thread.finished.connect(self.on_send_complete)
        
        # Start sending
        self.sender_thread.start()
        self.status_label.setText("Sending emails...")
        self.progress_bar.setValue(0)
        
        # Switch to logs tab to show progress
        self.tabs.setCurrentWidget(self.log_tab)

    def handle_log_signal(self, log_data):
        """Handle log signal from sender thread"""
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        status_icon = "✓" if log_data['status'] == 'Success' else "✗"
    
        log_message = f"[{timestamp}] {status_icon} {log_data['email']} - {log_data['status']}"
        if log_data.get('error'):
            log_message += f" - {log_data['error']}"
    
        self.log_view.append(log_message)

    def handle_status_signal(self, message):
        """Handle status signal from sender thread"""
        self.status_label.setText(message)

    def on_send_complete(self, summary):
        """Handle completion of email sending"""
        self.status_label.setText(
            f"Completed: {summary['successful']} sent, {summary['failed']} failed"
        )
        self.progress_bar.setValue(100)
    
        QMessageBox.information(
            self,
            "Send Complete",
            f"Email sending completed!\n\n"
            f"Successful: {summary['successful']}\n"
            f"Failed: {summary['failed']}\n"
            f"Total Time: {summary['total_time']:.1f} seconds"
        )
    
        # Reload logs and campaigns
        self.load_saved_settings()

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
        """Validate before sending emails"""
        # Check SMTP configuration
        smtp_email = self.db.get_config_value("smtp_email")
        smtp_password = self.db.get_config_value("smtp_password")
        if not smtp_email or not smtp_password:
            QMessageBox.warning(
                self,
                "SMTP Missing",
                "Configure SMTP settings before sending.\n\nGo to Settings → SMTP Configuration"
            )
            return False

        # Check recipients
        if not self.recipients:
            QMessageBox.warning(
                self,
                "No Recipients",
                "Please import recipient list first.\n\nGo to Recipients tab → Import Recipients"
            )
            return False

        # Check subject
        if not self.subject_input.text().strip():
            QMessageBox.warning(
                self,
                "Missing Subject",
                "Please enter an email subject."
            )
            return False

        # Check body
        if not self.body_editor.get_html().strip():
            QMessageBox.warning(
                self,
                "Empty Body",
                "Please compose an email body."
            )
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

