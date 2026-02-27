"""
Enterprise Data Sanitization Platform
Main UI Window
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QComboBox, QLineEdit, QProgressBar,
    QMessageBox, QFrame, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont
from typing import List, Optional

import sys
import os
# Ensure core and ui can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.device_validator import ValidatedDevice
from core.wipe_engine import WipeEngine
from core.certificate_engine import CertificateEngine
from core.validation_engine import validate_operator_name
from core.exception_types import InvalidInputError
from ui.worker_threads import DeviceScannerThread
from ui.safe_dialogs import StrictConfirmationDialog, show_error_dialog, show_info_dialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EcoWipe Enterprise - Data Sanitization Platform")
        self.setMinimumSize(800, 600)
        
        self.current_drives: List[ValidatedDevice] = []
        self.wipe_thread: Optional[WipeEngine] = None
        self.cert_engine = CertificateEngine()
        
        self._setup_ui()
        self._start_scanner()

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("EcoWipe Enterprise")
        header.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)

        # Operator Input
        op_layout = QHBoxLayout()
        op_label = QLabel("Operator Name:")
        self.operator_input = QLineEdit()
        self.operator_input.setPlaceholderText("Enter operator ID (e.g., John-Doe)")
        op_layout.addWidget(op_label)
        op_layout.addWidget(self.operator_input)
        main_layout.addLayout(op_layout)

        # Device List
        main_layout.addWidget(QLabel("Available USB Devices (System Drives Hidden):"))
        self.device_list = QListWidget()
        self.device_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        main_layout.addWidget(self.device_list)

        # Wipe Method Selection
        method_layout = QHBoxLayout()
        method_layout.addWidget(QLabel("Wipe Method:"))
        self.method_combo = QComboBox()
        self.method_combo.addItems([
            "1-Pass Zero (NIST 800-88 Clear)",
            "1-Pass Random (NIST 800-88 Clear)",
            "DoD 5220.22-M (3-Pass)"
        ])
        method_layout.addWidget(self.method_combo)
        main_layout.addLayout(method_layout)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        main_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        # Action Buttons
        btn_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh Devices")
        self.refresh_btn.clicked.connect(self._force_refresh)
        
        self.wipe_btn = QPushButton("START WIPE")
        self.wipe_btn.setStyleSheet("background-color: #DC2626; color: white; font-weight: bold; padding: 10px;")
        self.wipe_btn.clicked.connect(self._initiate_wipe)
        
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.wipe_btn)
        main_layout.addLayout(btn_layout)

    def _start_scanner(self):
        self.scanner = DeviceScannerThread()
        self.scanner.drives_updated.connect(self._update_device_list)
        self.scanner.error_occurred.connect(self._handle_scanner_error)
        self.scanner.start()

    def _force_refresh(self):
        self.status_label.setText("Scanning for devices...")
        self.scanner.trigger_refresh()

    @pyqtSlot(list)
    def _update_device_list(self, drives: List[ValidatedDevice]):
        self.current_drives = drives
        self.device_list.clear()
        
        if not drives:
            self.device_list.addItem("No valid USB devices found.")
            self.device_list.item(0).setFlags(Qt.ItemFlag.NoItemFlags) # Make unselectable
            return
            
        for drive in drives:
            item_text = f"{drive.device_id} | {drive.model} | {drive.size_gb} GB | S/N: {drive.serial_number}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, drive.device_id)
            self.device_list.addItem(item)
            
        self.status_label.setText(f"Found {len(drives)} valid device(s).")

    @pyqtSlot(str)
    def _handle_scanner_error(self, error_msg: str):
        self.status_label.setText(f"Scanner Error: {error_msg}")

    def _initiate_wipe(self):
        # 1. Validate Operator
        try:
            operator_name = validate_operator_name(self.operator_input.text())
        except InvalidInputError as e:
            show_error_dialog(self, "Validation Error", str(e))
            return

        # 2. Validate Selection
        selected_items = self.device_list.selectedItems()
        if not selected_items or selected_items[0].flags() == Qt.ItemFlag.NoItemFlags:
            show_error_dialog(self, "Selection Error", "Please select a valid device to wipe.")
            return
            
        device_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        device_info = selected_items[0].text()
        method_name = self.method_combo.currentText()

        # 3. Strict Confirmation
        dialog = StrictConfirmationDialog(device_info, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        # 4. Lock UI and Start Wipe
        self._set_ui_locked(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Initializing wipe engine...")
        
        # Stop scanner during wipe to prevent WMI conflicts
        self.scanner.stop()
        
        self.wipe_thread = WipeEngine(device_id, method_name, operator_name)
        self.wipe_thread.progress_updated.connect(self._update_progress)
        self.wipe_thread.wipe_completed.connect(self._handle_wipe_success)
        self.wipe_thread.wipe_failed.connect(self._handle_wipe_failure)
        self.wipe_thread.start()

    def _set_ui_locked(self, locked: bool):
        self.operator_input.setEnabled(not locked)
        self.device_list.setEnabled(not locked)
        self.method_combo.setEnabled(not locked)
        self.refresh_btn.setEnabled(not locked)
        self.wipe_btn.setEnabled(not locked)

    @pyqtSlot(int, str)
    def _update_progress(self, value: int, message: str):
        self.progress_bar.setValue(value)
        self.status_label.setText(message)

    @pyqtSlot(dict)
    def _handle_wipe_success(self, result: dict):
        self.progress_bar.setValue(100)
        self.status_label.setText("Wipe completed successfully. Generating certificate...")
        
        try:
            cert_info = self.cert_engine.generate_certificate(result)
            msg = (
                f"Wipe completed successfully!\n\n"
                f"Certificate ID: {cert_info['certificate_id']}\n"
                f"Saved to: {cert_info['json_path']}\n"
                f"QR Code: {cert_info['qr_path']}"
            )
            show_info_dialog(self, "Success", msg)
        except Exception as e:
            show_error_dialog(self, "Certificate Error", f"Wipe succeeded, but certificate generation failed:\n{e}")
            
        self._cleanup_after_wipe()

    @pyqtSlot(str)
    def _handle_wipe_failure(self, error_msg: str):
        self.progress_bar.setValue(0)
        self.status_label.setText("Wipe failed.")
        show_error_dialog(self, "Wipe Failed", f"A critical error occurred during the wipe process:\n\n{error_msg}")
        self._cleanup_after_wipe()

    def _cleanup_after_wipe(self):
        self.wipe_thread = None
        self._set_ui_locked(False)
        self.status_label.setText("Ready")
        # Restart scanner
        self._start_scanner()

    def closeEvent(self, event):
        """Ensure threads are stopped when closing."""
        if self.wipe_thread and self.wipe_thread.isRunning():
            reply = QMessageBox.question(
                self, 'Warning', 
                'A wipe operation is currently in progress. Are you sure you want to exit? This may leave the drive in an inconsistent state.',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.wipe_thread.cancel()
                self.wipe_thread.wait()
                self.scanner.stop()
                event.accept()
            else:
                event.ignore()
        else:
            self.scanner.stop()
            event.accept()
