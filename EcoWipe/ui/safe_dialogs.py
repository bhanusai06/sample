"""
Enterprise Data Sanitization Platform
Safe Confirmation Dialogs
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
    QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class StrictConfirmationDialog(QDialog):
    """
    A dialog that requires the user to type a specific phrase to confirm
    a destructive action. Prevents accidental clicks.
    """
    def __init__(self, device_info: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CRITICAL: Destructive Action Confirmation")
        self.setModal(True)
        self.setMinimumWidth(450)
        
        # The exact phrase the user must type
        self.required_phrase = "I UNDERSTAND THIS WILL DESTROY ALL DATA"
        
        self._setup_ui(device_info)

    def _setup_ui(self, device_info: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Warning Icon/Header
        warning_label = QLabel("⚠️ WARNING: DATA DESTRUCTION ⚠️")
        warning_label.setStyleSheet("color: #DC2626; font-weight: bold; font-size: 16px;")
        warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(warning_label)
        
        # Device Info
        info_label = QLabel(f"You are about to permanently wipe:\n\n{device_info}")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(info_label)
        
        # Instructions
        inst_label = QLabel(f"To proceed, type the following phrase exactly:\n\n<b>{self.required_phrase}</b>")
        inst_label.setWordWrap(True)
        layout.addWidget(inst_label)
        
        # Input Field
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type the phrase here...")
        self.input_field.textChanged.connect(self._validate_input)
        layout.addWidget(self.input_field)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.confirm_btn = QPushButton("WIPE DEVICE")
        self.confirm_btn.setStyleSheet("background-color: #DC2626; color: white; font-weight: bold;")
        self.confirm_btn.setEnabled(False) # Disabled by default
        self.confirm_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.confirm_btn)
        
        layout.addLayout(btn_layout)

    def _validate_input(self, text: str):
        """Enable the confirm button only if the text matches exactly."""
        if text == self.required_phrase:
            self.confirm_btn.setEnabled(True)
        else:
            self.confirm_btn.setEnabled(False)

def show_error_dialog(parent, title: str, message: str):
    """Show a standard error dialog."""
    QMessageBox.critical(parent, title, message)

def show_info_dialog(parent, title: str, message: str):
    """Show a standard info dialog."""
    QMessageBox.information(parent, title, message)
