"""
Email Editor Widget - Rich text HTML editor
Preview Dialog - Email preview window
"""

import datetime
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QToolBar, QAction, QColorDialog, QDialog,
    QLabel, QTableWidgetItem, QMessageBox
)
from PyQt5.QtGui import QFont, QColor, QTextCharFormat, QTextCursor
from PyQt5.QtCore import Qt
try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    WEB_ENGINE_AVAILABLE = True
except ImportError:
    WEB_ENGINE_AVAILABLE = False
    # Import QWebEngineView if available (already handled above)
    # If you want to use QWebEngineView, ensure you have installed PyQtWebEngine:
    # pip install PyQtWebEngine

class EmailEditorWidget(QWidget):
    """Rich text editor for email composition"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize editor UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        toolbar = QToolBar()
        toolbar.setMovable(False)
        
        # Bold action
        bold_action = QAction("B", self)
        bold_action.setToolTip("Bold")
        bold_action.setCheckable(True)
        bold_action.triggered.connect(self.set_bold)
        bold_font = QFont()
        bold_font.setBold(True)
        bold_action.setFont(bold_font)
        toolbar.addAction(bold_action)
        
        # Italic action
        italic_action = QAction("I", self)
        italic_action.setToolTip("Italic")
        italic_action.setCheckable(True)
        italic_action.triggered.connect(self.set_italic)
        italic_font = QFont()
        italic_font.setItalic(True)
        italic_action.setFont(italic_font)
        toolbar.addAction(italic_action)
        
        # Underline action
        underline_action = QAction("U", self)
        underline_action.setToolTip("Underline")
        underline_action.setCheckable(True)
        underline_action.triggered.connect(self.set_underline)
        underline_font = QFont()
        underline_font.setUnderline(True)
        underline_action.setFont(underline_font)
        toolbar.addAction(underline_action)
        
        toolbar.addSeparator()
        
        # Text color action
        color_action = QAction("🎨 Color", self)
        color_action.setToolTip("Text Color")
        color_action.triggered.connect(self.set_text_color)
        toolbar.addAction(color_action)
        
        toolbar.addSeparator()
        
        # Insert placeholders
        placeholder_action = QAction("📝 Insert Placeholder", self)
        placeholder_action.setToolTip("Insert placeholder like {name}")
        placeholder_action.triggered.connect(self.insert_placeholder_dialog)
        toolbar.addAction(placeholder_action)
        
        toolbar.addSeparator()
        
        # Clear formatting
        clear_action = QAction("🗑️ Clear Format", self)
        clear_action.setToolTip("Clear formatting")
        clear_action.triggered.connect(self.clear_formatting)
        toolbar.addAction(clear_action)
        
        layout.addWidget(toolbar)
        
        # Text editor
        self.text_edit = QTextEdit()
        self.text_edit.setAcceptRichText(True)
        self.text_edit.setPlaceholderText(
            "Compose your email here...\n\n"
            "You can use placeholders like {name}, {email}, {company}, etc.\n"
            "These will be replaced with actual data when sending."
        )
        
        # Set default font
        default_font = QFont("Arial", 11)
        self.text_edit.setFont(default_font)
        
        layout.addWidget(self.text_edit)
        
        self.setLayout(layout)
    
    def set_bold(self):
        """Toggle bold formatting"""
        fmt = self.text_edit.currentCharFormat()
        weight = QFont.Normal if fmt.fontWeight() == QFont.Bold else QFont.Bold
        fmt.setFontWeight(weight)
        self.text_edit.setCurrentCharFormat(fmt)
    
    def set_italic(self):
        """Toggle italic formatting"""
        fmt = self.text_edit.currentCharFormat()
        fmt.setFontItalic(not fmt.fontItalic())
        self.text_edit.setCurrentCharFormat(fmt)
    
    def set_underline(self):
        """Toggle underline formatting"""
        fmt = self.text_edit.currentCharFormat()
        fmt.setFontUnderline(not fmt.fontUnderline())
        self.text_edit.setCurrentCharFormat(fmt)
    
    def set_text_color(self):
        """Set text color"""
        color = QColorDialog.getColor()
        if color.isValid():
            fmt = self.text_edit.currentCharFormat()
            fmt.setForeground(color)
            self.text_edit.setCurrentCharFormat(fmt)
    
    def insert_placeholder_dialog(self):
        """Insert common placeholder"""
        from PyQt5.QtWidgets import QInputDialog
        
        placeholders = [
            "{name}",
            "{email}",
            "{company}",
            "{phone}",
            "{address}",
            "{city}",
            "{state}",
            "{country}"
        ]
        
        placeholder, ok = QInputDialog.getItem(
            self,
            "Insert Placeholder",
            "Select a placeholder to insert:",
            placeholders,
            0,
            False
        )
        
        if ok and placeholder:
            cursor = self.text_edit.textCursor()
            cursor.insertText(placeholder)
    
    def clear_formatting(self):
        """Clear all formatting"""
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            fmt = QTextCharFormat()
            cursor.setCharFormat(fmt)
        else:
            self.text_edit.setCurrentCharFormat(QTextCharFormat())
    
    def get_html(self):
        """Get HTML content"""
        return self.text_edit.toHtml()
    
    def set_html(self, html):
        """Set HTML content"""
        self.text_edit.setHtml(html)
    
    def get_plain_text(self):
        """Get plain text content"""
        return self.text_edit.toPlainText()
    
    def clear(self):
        """Clear editor content"""
        self.text_edit.clear()


class PreviewDialog(QDialog):
    """Email preview dialog"""
    
    def __init__(self, subject, html_body, parent=None):
        super().__init__(parent)
        self.subject = subject
        self.html_body = html_body
        
        self.setWindowTitle("Email Preview")
        self.setMinimumSize(700, 600)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Preview notice
        notice = QLabel("📧 Email Preview - This is how your email will appear to recipients")
        notice.setStyleSheet("""
            QLabel {
                background-color: #d1ecf1;
                border: 1px solid #bee5eb;
                color: #0c5460;
                padding: 12px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        layout.addWidget(notice)
        
        # Subject display
        subject_layout = QHBoxLayout()
        subject_layout.addWidget(QLabel("<b>Subject:</b>"))
        subject_label = QLabel(self.subject)
        # HTML preview using QWebEngineView if available, else fallback to QTextEdit
        if WEB_ENGINE_AVAILABLE:
            self.web_view = QWebEngineView()
            self.web_view.setHtml(self.html_body)
            layout.addWidget(self.web_view)
        else:
            preview_text = QTextEdit()
            preview_text.setReadOnly(True)
            preview_text.setHtml(self.html_body)
            layout.addWidget(preview_text)
            preview_text = QTextEdit()
            preview_text.setReadOnly(True)
            preview_text.setHtml(self.html_body)
            layout.addWidget(preview_text)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
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


# Additional helper methods for MainWindow

def populate_recipients_table(self):
    """Populate recipients table with data"""
    if self.recipients_df is None:
        return
    
    self.recipients_table.setRowCount(0)
    
    for idx, row in self.recipients_df.iterrows():
        row_position = self.recipients_table.rowCount()
        self.recipients_table.insertRow(row_position)
        
        self.recipients_table.setItem(row_position, 0, QTableWidgetItem(row.get('Email', '')))
        self.recipients_table.setItem(row_position, 1, QTableWidgetItem(str(row.get('Name', ''))))
        self.recipients_table.setItem(row_position, 2, QTableWidgetItem(str(row.get('Company', ''))))
        
        status_item = QTableWidgetItem("Valid")
        status_item.setForeground(QColor(40, 167, 69))
        self.recipients_table.setItem(row_position, 3, status_item)
    
    # Update labels
    self.total_recipients_label.setText(f"Total: {len(self.recipients_df)}")
    self.valid_emails_label.setText(f"Valid: {len(self.recipients_df)}")
    self.invalid_emails_label.setText("Invalid: 0")

def load_logs(self):
    """Load email logs from database"""
    status_filter = self.status_filter.currentText()
    
    logs = self.db_manager.get_logs(
        limit=1000,
        campaign_id=None,
        status_filter=status_filter if status_filter != 'All' else None
    )
    
    self.logs_table.setRowCount(0)
    
    for log in logs:
        row = self.logs_table.rowCount()
        self.logs_table.insertRow(row)
        
        self.logs_table.setItem(row, 0, QTableWidgetItem(log['recipient_email']))
        self.logs_table.setItem(row, 1, QTableWidgetItem(log.get('recipient_name', '')))
        self.logs_table.setItem(row, 2, QTableWidgetItem(log.get('subject', '')))
        
        status_item = QTableWidgetItem(log['status'])
        if log['status'] == 'Success':
            status_item.setForeground(QColor(40, 167, 69))
        else:
            status_item.setForeground(QColor(220, 53, 69))
        self.logs_table.setItem(row, 3, status_item)
        
        self.logs_table.setItem(row, 4, QTableWidgetItem(log.get('error_message', '')))
        self.logs_table.setItem(row, 5, QTableWidgetItem(str(log.get('timestamp', ''))))

def load_campaigns(self):
    """Load campaign history"""
    campaigns = self.db_manager.get_recent_campaigns(limit=50)
    
    self.campaigns_table.setRowCount(0)
    
    for campaign in campaigns:
        row = self.campaigns_table.rowCount()
        self.campaigns_table.insertRow(row)
        
        self.campaigns_table.setItem(row, 0, QTableWidgetItem(campaign['name']))
        self.campaigns_table.setItem(row, 1, QTableWidgetItem(str(campaign['total_emails'])))
        self.campaigns_table.setItem(row, 2, QTableWidgetItem(str(campaign['successful'])))
        self.campaigns_table.setItem(row, 3, QTableWidgetItem(str(campaign['failed'])))
        self.campaigns_table.setItem(row, 4, QTableWidgetItem(str(campaign.get('start_time', ''))))
        self.campaigns_table.setItem(row, 5, QTableWidgetItem(str(campaign.get('end_time', ''))))

def export_logs(self):
    """Export logs to CSV"""
    from PyQt5.QtWidgets import QFileDialog
    import csv
    
    file_path, _ = QFileDialog.getSaveFileName(
        self,
        "Export Logs",
        f"email_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "CSV Files (*.csv)"
    )
    
    if file_path:
        try:
            logs = self.db_manager.get_logs(limit=10000)
            
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Email', 'Name', 'Subject', 'Status', 'Error', 'Timestamp'])
                
                for log in logs:
                    writer.writerow([
                        log['recipient_email'],
                        log.get('recipient_name', ''),
                        log.get('subject', ''),
                        log['status'],
                        log.get('error_message', ''),
                        str(log.get('timestamp', ''))
                    ])
            
            QMessageBox.information(self, "Export Complete", f"Logs exported successfully to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Failed to export logs:\n{str(e)}")