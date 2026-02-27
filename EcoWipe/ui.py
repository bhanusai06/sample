from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QComboBox, QLineEdit, QProgressBar, 
    QDialog, QCheckBox, QMessageBox, QFrame, QStackedWidget,
    QGridLayout, QTextEdit, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, pyqtProperty, pyqtSignal, QThread, QUrl
from PyQt6.QtGui import QFont, QColor, QPixmap, QImage, QDesktopServices
from utils import COLORS
from styles import MODERN_COLORS, MODERN_BUTTON_STYLE, MODERN_PANEL_STYLE, MODERN_LIST_STYLE, MODERN_COMBO_STYLE, MODERN_INPUT_STYLE, MODERN_PROGRESS_STYLE, ACCENT_TEXT_STYLE, MUTED_TEXT_STYLE, PRIMARY_TEXT_STYLE
from engine import get_available_drives, WiperThread
from models import generate_certificate
from datetime import datetime
import os
import threading
import shutil
import time

class DriveScanner(QThread):
    drives_updated = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True
        self.refresh_event = threading.Event()
        self.force_update = False

    def run(self):
        from engine import get_available_drives
        last_drives = None
        scan_counter = 0
        while self.running:
            try:
                scan_counter += 1
                print(f"[SCANNER] Scan #{scan_counter} - Checking for devices...")
                
                drives = get_available_drives()
                print(f"[SCANNER] Found {len(drives)} drive(s)")
                
                if drives != last_drives or self.force_update:
                    # Determine added/removed for logging
                    if last_drives is not None and not self.force_update:
                        current_paths = {d['path']: d for d in drives if not d.get('is_system')}
                        last_paths = {d['path']: d for d in last_drives if not d.get('is_system')}
                        
                        added = set(current_paths.keys()) - set(last_paths.keys())
                        removed = set(last_paths.keys()) - set(current_paths.keys())
                        
                        for p in added:
                            model = current_paths[p].get('model', 'Unknown')
                            size = current_paths[p].get('size_str', 'Unknown')
                            print(f"[UI_LOG] [+] Device Connected: {p} - {model} ({size})")
                        for p in removed:
                            model = last_paths[p].get('model', 'Unknown')
                            print(f"[UI_LOG] [-] Device Disconnected: {p} - {model}")

                    print(f"[SCANNER] Emitting signal with {len(drives)} drive(s)")
                    self.drives_updated.emit(drives)
                    last_drives = drives
                    self.force_update = False
            except Exception as e:
                print(f"[SCANNER] Error: {e}")
            
            # Check more frequently for device changes (every 1 second)
            if self.refresh_event.wait(1.0):
                self.refresh_event.clear()
                print(f"[SCANNER] Manual refresh triggered")


    def trigger_refresh(self):
        self.force_update = True
        self.refresh_event.set()

    def stop(self):
        self.running = False
        self.refresh_event.set()
        self.wait()

class StylishButton(QPushButton):
    def __init__(self, text, color=MODERN_COLORS["accent_primary"], parent=None):
        super().__init__(text, parent)
        self.color = color
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.setMinimumHeight(44)
        
        # Create gradient colors
        if color == MODERN_COLORS["accent_primary"]:
            color_start, color_end = "#06B6D4", "#0EA5E9"
            color_start_hover, color_end_hover = "#00D9FF", "#06B6D4"
            color_start_press, color_end_press = "#0099CC", "#006B99"
        elif "warning" in str(color) or color == "#F59E0B":
            color_start, color_end = "#F59E0B", "#D97706"
            color_start_hover, color_end_hover = "#FCD34D", "#F59E0B"
            color_start_press, color_end_press = "#D97706", "#B45309"
        elif "danger" in str(color) or color == "#EF4444":
            color_start, color_end = "#EF4444", "#DC2626"
            color_start_hover, color_end_hover = "#F87171", "#EF4444"
            color_start_press, color_end_press = "#DC2626", "#991B1B"
        elif "success" in str(color) or color == "#10B981":
            color_start, color_end = "#10B981", "#059669"
            color_start_hover, color_end_hover = "#6EE7B7", "#10B981"
            color_start_press, color_end_press = "#059669", "#047857"
        else:
            color_start, color_end = color, color
            color_start_hover, color_end_hover = color, color
            color_start_press, color_end_press = color, color
        
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                            stop:0 {color_start}, 
                                            stop:1 {color_end});
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 10px 28px;
                font-weight: bold;
                font-size: 11px;
                letter-spacing: 0.5px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                            stop:0 {color_start_hover}, 
                                            stop:1 {color_end_hover});
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                            stop:0 {color_start_press}, 
                                            stop:1 {color_end_press});
            }}
            QPushButton:disabled {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                            stop:0 #1e293b, 
                                            stop:1 #0f172a);
                color: #64748B;
                border: 1px solid #475569;
            }}
        """)

class TermsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Authorization Required")
        self.setFixedSize(500, 360)
        self.setStyleSheet(f"background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1e293b, stop:1 #0f172a); color: #F1F5F9;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)
        
        warning_lbl = QLabel("<b>WARNING: IRREVERSIBLE DATA DESTRUCTION</b>")
        warning_lbl.setStyleSheet(f"color: {COLORS['warning']}; font-size: 14px; letter-spacing: 0.5px;")
        warning_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(warning_lbl)
        
        desc = QLabel(
            "• This action permanently destroys all data on the target device.\n"
            "• Data recovery will be cryptographically impossible.\n"
            "• Ensure the correct physical device is selected.\n"
            "• Operating organization assumes full accountability."
        )
        desc.setFont(QFont("Segoe UI", 10))
        desc.setStyleSheet(f"color: {COLORS['text_muted']}; line-height: 1.5;")
        layout.addWidget(desc)
        
        self.checkbox = QCheckBox("I understand the consequences and authorize this operation")
        self.checkbox.setFont(QFont("Segoe UI", 10))
        self.checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {COLORS['text']};
                spacing: 10px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid {COLORS['panel_border']};
                background-color: {COLORS['background']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {COLORS['warning']};
                border: 2px solid {COLORS['warning']};
            }}
        """)
        self.checkbox.stateChanged.connect(self.check_state)
        layout.addWidget(self.checkbox)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        self.cancel_btn = StylishButton("Cancel", COLORS["panel_border"])
        self.cancel_btn.setStyleSheet(self.cancel_btn.styleSheet().replace(
            "color: #FFFFFF;", f"color: {COLORS['text']};"
        ).replace(
            f"background-color: {COLORS['panel_border']};", 
            f"background-color: transparent;"
        ))
        self.cancel_btn.clicked.connect(self.reject)
        
        self.confirm_btn = StylishButton("AUTHORIZE", COLORS["warning"])
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.confirm_btn)
        layout.addLayout(btn_layout)
        
    def check_state(self, state):
        self.confirm_btn.setEnabled(state == Qt.CheckState.Checked.value)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EcoWipe - Secure Offline Disk Sanitization")
        self.setMinimumSize(1000, 650)
        self.resize(1200, 750)
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: #121212;
            }}
        """)
        
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)
        
        self.init_dashboard()
        self.init_wipe_screen()
        self.init_result_screen()
        
        self.central_widget.setCurrentIndex(0)
        self.wiper_thread = None
        self.selected_drive = None
        self.start_time = None
        
        self.drives = []
        self.scanner = DriveScanner(self)
        self.scanner.drives_updated.connect(self.on_drives_updated)
        self.scanner.start()

    def closeEvent(self, event):
        self.scanner.stop()
        super().closeEvent(event)

    def init_dashboard(self):
        page = QWidget()
        page.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)
        layout = QHBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        # Left Panel (Drive List)
        left_panel = QFrame()
        left_panel.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                            stop:0 #1e293b,
                                            stop:1 #0f172a);
                border: 1px solid #334155;
                border-radius: 12px;
            }}
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(24, 24, 24, 24)
        left_layout.setSpacing(16)
        
        lbl_select = QLabel("📦 Select Devices")
        lbl_select.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        lbl_select.setStyleSheet("color: #06B6D4; letter-spacing: 1px;")
        left_layout.addWidget(lbl_select)
        
        self.drive_list = QListWidget()
        self.drive_list.setFont(QFont("Consolas", 10))
        self.drive_list.setStyleSheet(f"""
            QListWidget {{
                background-color: #0F172A;
                color: #F1F5F9;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 8px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 12px;
                border-radius: 6px;
                margin-bottom: 4px;
                background-color: transparent;
                border-left: 3px solid transparent;
            }}
            QListWidget::item:hover {{
                background-color: #1E293B;
                border-left: 3px solid #06B6D4;
            }}
            QListWidget::item:selected {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #06B6D4,
                                            stop:1 #0EA5E9);
                color: #FFFFFF;
                border-left: 3px solid #00D9FF;
            }}
        """)
        self.drive_list.itemSelectionChanged.connect(self.on_drive_selected)
        left_layout.addWidget(self.drive_list)
        
        # Terminal Log
        self.terminal_log = QTextEdit()
        self.terminal_log.setReadOnly(True)
        self.terminal_log.setFont(QFont("Consolas", 10))
        self.terminal_log.setStyleSheet(f"""
            QTextEdit {{
                background-color: #000000;
                color: #00FF00;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 8px;
            }}
        """)
        self.terminal_log.setFixedHeight(120)
        
        # Add admin status indicator
        from utils import is_admin
        admin_status = "✓ Admin" if is_admin() else "✗ User"
        admin_color = "#10B981" if is_admin() else "#EF4444"
        self.terminal_log.append("User@EcoWipe:~$ engine start")
        self.terminal_log.append(f"[*] Privilege Level: <span style='color: {admin_color};'>{admin_status}</span>")
        self.terminal_log.append("[*] Scanning for connected devices...")
        left_layout.addWidget(self.terminal_log)
        
        # Refresh and Test Mode buttons
        btn_layout = QHBoxLayout()
        self.btn_refresh = StylishButton("↺ Refresh Devices", COLORS["accent"])
        self.btn_refresh.clicked.connect(self.refresh_drives)
        btn_layout.addWidget(self.btn_refresh)
        
        self.btn_test_mode = StylishButton("⚙️ Test Mode", "#F59E0B")
        self.btn_test_mode.clicked.connect(self.toggle_test_mode)
        btn_layout.addWidget(self.btn_test_mode)
        left_layout.addLayout(btn_layout)
        
        layout.addWidget(left_panel, 1)
        
        # Right Panel (Details & Actions)
        right_panel = QFrame()
        right_panel.setStyleSheet(f"background-color: {COLORS['panels']}; border-radius: 12px; border: 1px solid {COLORS['panel_border']};")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(30, 30, 30, 30)
        
        # Identity Icon Graphic
        self.icon_lbl = QLabel("🔌")
        self.icon_lbl.setFont(QFont("Segoe UI", 48))
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.icon_lbl)
        
        self.drive_info_lbl = QLabel("Waiting for device selection...")
        self.drive_info_lbl.setFont(QFont("Segoe UI", 11))
        self.drive_info_lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
        self.drive_info_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.drive_info_lbl)
        
        right_layout.addSpacing(30)
        
        # Settings Grid
        lbl_method = QLabel("WIPE ALGORITHM")
        lbl_method.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_method.setStyleSheet(f"color: {COLORS['text_muted']}; letter-spacing: 1px;")
        right_layout.addWidget(lbl_method)
        
        self.method_combo = QComboBox()
        self.method_combo.addItems(["1-Pass Zero", "3-Pass DoD (Zero/One/Random)", "Fast Random"])
        self.method_combo.setFont(QFont("Segoe UI", 12))
        self.method_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['background']};
                color: {COLORS['text']};
                padding: 10px; border-radius: 6px; border: 1px solid {COLORS['panel_border']};
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS['panels']};
                color: {COLORS['text']};
                selection-background-color: {COLORS['accent']};
                border: 1px solid {COLORS['panel_border']};
                outline: none;
            }}
        """)
        right_layout.addWidget(self.method_combo)
        
        right_layout.addSpacing(20)
        
        lbl_op = QLabel("OPERATOR IDENTITY")
        lbl_op.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl_op.setStyleSheet(f"color: {COLORS['text_muted']}; letter-spacing: 1px;")
        right_layout.addWidget(lbl_op)
        
        self.operator_input = QLineEdit()
        self.operator_input.setPlaceholderText("e.g. TECH-01")
        self.operator_input.setFont(QFont("Segoe UI", 12))
        self.operator_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['background']};
                color: {COLORS['text']};
                padding: 10px; border-radius: 6px; border: 1px solid {COLORS['panel_border']};
            }}
            QLineEdit:focus {{ border: 1px solid {COLORS['accent']}; }}
        """)
        right_layout.addWidget(self.operator_input)
        
        right_layout.addStretch()
        
        self.start_btn = StylishButton("⚡ INITIALIZE WIPE", COLORS["warning"])
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self.attempt_start)
        right_layout.addWidget(self.start_btn)
        
        layout.addWidget(right_panel, 1)
        self.central_widget.addWidget(page)

    def init_wipe_screen(self):
        page = QFrame()
        page.setStyleSheet(f"background-color: {COLORS['panels']};")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # TOP SECTION: Info
        self.wipe_title = QLabel("Secure Wipe in Progress")
        self.wipe_title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        self.wipe_title.setStyleSheet(f"color: {COLORS['warning']}; letter-spacing: 1px;")
        layout.addWidget(self.wipe_title, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Details Grid
        details_grid = QGridLayout()
        details_grid.setContentsMargins(0, 20, 0, 30)
        details_grid.setVerticalSpacing(10)
        details_grid.setHorizontalSpacing(20)
        
        self.lbl_w_device = QLabel()
        self.lbl_w_size = QLabel()
        self.lbl_w_method = QLabel()
        self.lbl_w_operator = QLabel()
        
        for i, (lbl_title, lbl_val) in enumerate([
            ("Device:", self.lbl_w_device),
            ("Size:", self.lbl_w_size),
            ("Method:", self.lbl_w_method),
            ("Operator:", self.lbl_w_operator)
        ]):
            t_lbl = QLabel(lbl_title)
            t_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            t_lbl.setStyleSheet(f"color: {COLORS['text_muted']};")
            t_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            
            lbl_val.setFont(QFont("Segoe UI", 12))
            lbl_val.setStyleSheet(f"color: {COLORS['text']};")
            
            details_grid.addWidget(t_lbl, i, 0)
            details_grid.addWidget(lbl_val, i, 1)
            
        layout.addLayout(details_grid)
        
        # MIDDLE SECTION: Progress
        self.lbl_progress_pct = QLabel("0%")
        self.lbl_progress_pct.setFont(QFont("Segoe UI", 36, QFont.Weight.Bold))
        self.lbl_progress_pct.setStyleSheet(f"color: {COLORS['accent']};")
        layout.addWidget(self.lbl_progress_pct, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_pass_info = QLabel("Pass 1")
        self.lbl_pass_info.setFont(QFont("Segoe UI", 14))
        self.lbl_pass_info.setStyleSheet(f"color: {COLORS['text_muted']};")
        layout.addWidget(self.lbl_pass_info, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addSpacing(10)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: {COLORS['background']};
                border-radius: 6px;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['success']}; 
                border-radius: 6px;
            }}
        """)
        layout.addWidget(self.progress_bar)
        
        layout.addSpacing(20)
        
        # Status Log
        self.wipe_status_log = QTextEdit()
        self.wipe_status_log.setReadOnly(True)
        self.wipe_status_log.setFont(QFont("Consolas", 10))
        self.wipe_status_log.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['background']};
                color: {COLORS['text_muted']};
                border: 1px solid {COLORS['panel_border']};
                border-radius: 6px;
                padding: 10px;
            }}
        """)
        self.wipe_status_log.setFixedHeight(120)
        layout.addWidget(self.wipe_status_log)
        
        layout.addStretch()
        
        # BOTTOM SECTION: Cancel
        self.cancel_wipe_btn = StylishButton("ABORT OPERATION", "#B91C1C") # Dark red
        self.cancel_wipe_btn.clicked.connect(self.cancel_wipe)
        layout.addWidget(self.cancel_wipe_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        warning_lbl = QLabel("Do not disconnect the device during wipe.")
        warning_lbl.setFont(QFont("Segoe UI", 10))
        warning_lbl.setStyleSheet(f"color: {COLORS['warning']}; margin-top: 5px;")
        layout.addWidget(warning_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.central_widget.addWidget(page)

        
    def init_result_screen(self):
        page = QFrame()
        page.setStyleSheet(f"background-color: {COLORS['panels']};")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # TOP SECTION
        self.res_icon = QLabel("✓")
        self.res_icon.setFont(QFont("Segoe UI", 48, QFont.Weight.Bold))
        self.res_icon.setStyleSheet(f"color: {COLORS['success']};")
        layout.addWidget(self.res_icon, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.res_title = QLabel("Wipe Completed Successfully")
        self.res_title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        self.res_title.setStyleSheet(f"color: {COLORS['text']}; letter-spacing: 1px;")
        layout.addWidget(self.res_title, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.res_subtitle = QLabel("Device sanitized and verified.")
        self.res_subtitle.setFont(QFont("Segoe UI", 12))
        self.res_subtitle.setStyleSheet(f"color: {COLORS['text_muted']};")
        layout.addWidget(self.res_subtitle, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addSpacing(20)
        
        # MIDDLE SECTION - Split Layout (Details | QR)
        mid_layout = QHBoxLayout()
        mid_layout.setSpacing(40)
        
        # Details Left
        details_frame = QFrame()
        details_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['background']};
                border: 1px solid {COLORS['panel_border']};
                border-radius: 8px;
            }}
        """)
        details_layout = QGridLayout(details_frame)
        details_layout.setContentsMargins(20, 20, 20, 20)
        details_layout.setVerticalSpacing(8)
        details_layout.setHorizontalSpacing(15)
        
        self.lbl_res_device = QLabel()
        self.lbl_res_size = QLabel()
        self.lbl_res_method = QLabel()
        self.lbl_res_operator = QLabel()
        self.lbl_res_start = QLabel()
        self.lbl_res_end = QLabel()
        self.lbl_res_verify = QLabel()
        
        details = [
            ("Device:", self.lbl_res_device),
            ("Size:", self.lbl_res_size),
            ("Method:", self.lbl_res_method),
            ("Operator:", self.lbl_res_operator),
            ("Start Time:", self.lbl_res_start),
            ("End Time:", self.lbl_res_end),
            ("Verification:", self.lbl_res_verify)
        ]
        
        for i, (k, v) in enumerate(details):
            lb_k = QLabel(k)
            lb_k.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            lb_k.setStyleSheet(f"color: {COLORS['text_muted']}; border: none;")
            lb_k.setAlignment(Qt.AlignmentFlag.AlignRight)
            
            v.setFont(QFont("Segoe UI", 10))
            v.setStyleSheet(f"color: {COLORS['text']}; border: none;")
            
            details_layout.addWidget(lb_k, i, 0)
            details_layout.addWidget(v, i, 1)
            
        # SHA Hash at bottom of details
        lb_hash = QLabel("SHA-256:")
        lb_hash.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lb_hash.setStyleSheet(f"color: {COLORS['text_muted']}; border: none; margin-top: 10px;")
        details_layout.addWidget(lb_hash, len(details), 0, alignment=Qt.AlignmentFlag.AlignRight)
        
        self.lbl_res_hash = QLineEdit()
        self.lbl_res_hash.setReadOnly(True)
        self.lbl_res_hash.setFont(QFont("Consolas", 9))
        self.lbl_res_hash.setStyleSheet(f"""
            QLineEdit {{
                background-color: transparent;
                color: {COLORS['accent']};
                border: none;
                margin-top: 10px;
            }}
        """)
        details_layout.addWidget(self.lbl_res_hash, len(details), 1)
        
        mid_layout.addWidget(details_frame, 2)
        
        # QR Right
        qr_layout = QVBoxLayout()
        qr_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.qr_label = QLabel()
        self.qr_label.setFixedSize(180, 180)
        self.qr_label.setStyleSheet(f"background-color: white; border-radius: 8px; padding: 10px;")
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qr_layout.addWidget(self.qr_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        qr_sub = QLabel("Scan to verify wipe certificate")
        qr_sub.setFont(QFont("Segoe UI", 10))
        qr_sub.setStyleSheet(f"color: {COLORS['text_muted']}; margin-top: 10px;")
        qr_layout.addWidget(qr_sub, alignment=Qt.AlignmentFlag.AlignCenter)
        
        mid_layout.addLayout(qr_layout, 1)
        
        layout.addLayout(mid_layout)
        layout.addStretch()
        
        # BOTTOM SECTION - Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        self.btn_open_cert = StylishButton("Open Certificate File", COLORS["panel_border"])
        self.btn_open_cert.setStyleSheet(self.btn_open_cert.styleSheet().replace(
            f"background-color: {COLORS['panel_border']};", 
            f"background-color: transparent;"
        ).replace(
            "color: #FFFFFF;", f"color: {COLORS['text']};"
        ))
        
        self.btn_save_qr = StylishButton("Save QR as Image", COLORS["panel_border"])
        self.btn_save_qr.setStyleSheet(self.btn_save_qr.styleSheet().replace(
            f"background-color: {COLORS['panel_border']};", 
            f"background-color: transparent;"
        ).replace(
            "color: #FFFFFF;", f"color: {COLORS['text']};"
        ))
        
        self.btn_return = StylishButton("Return to Dashboard", COLORS["success"])
        self.btn_return.clicked.connect(self.return_to_dashboard)
        
        btn_layout.addWidget(self.btn_open_cert)
        btn_layout.addWidget(self.btn_save_qr)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_return)
        
        layout.addLayout(btn_layout)
        
        self.central_widget.addWidget(page)

    def refresh_drives(self):
        # Trigger an immediate manual refresh via the thread
        if hasattr(self, 'btn_refresh'):
            self.btn_refresh.setText("⏳ Refreshing...")
            self.btn_refresh.setEnabled(False)
        self.scanner.trigger_refresh()

    def toggle_test_mode(self):
        """Toggle test mode to allow system drive selection"""
        import engine
        if engine.TEST_MODE_ALLOW_SYSTEM_DRIVE:
            # Disable test mode
            engine.TEST_MODE_ALLOW_SYSTEM_DRIVE = False
            self.btn_test_mode.setStyleSheet(self.btn_test_mode.styleSheet().replace(
                f"color: {COLORS['warning']};",
                f"color: {COLORS['text_muted']};"
            ))
            msg = "Test Mode DISABLED\n\nSystem drives are now protected."
        else:
            # Enable test mode
            engine.TEST_MODE_ALLOW_SYSTEM_DRIVE = True
            self.btn_test_mode.setStyleSheet(self.btn_test_mode.styleSheet().replace(
                f"color: {COLORS['text_muted']};",
                f"color: {COLORS['warning']};"
            ))
            msg = "⚠️ Test Mode ENABLED\n\nYou can now select your system drive for testing.\n\nACTUAL WIPE IS STILL DISABLED (Simulation Mode).\n\nClick Refresh to see your system drive."
        
        QMessageBox.information(self, "Test Mode", msg)
        self.refresh_drives()

    def on_drives_updated(self, drives):
        print(f"[UI] on_drives_updated called with {len(drives)} drive(s)")
        
        if hasattr(self, 'btn_refresh'):
            self.btn_refresh.setText("↺ Refresh Devices")
            self.btn_refresh.setEnabled(True)
        
        # Update test mode button color based on engine state
        import engine
        if engine.TEST_MODE_ALLOW_SYSTEM_DRIVE:
            if hasattr(self, 'btn_test_mode'):
                self.btn_test_mode.setStyleSheet(self.btn_test_mode.styleSheet().replace(
                    f"color: {COLORS['text_muted']};",
                    f"color: {COLORS['warning']};"
                ))
            
        # Check output from scanner thread printed to stdout and append to UI log
        if hasattr(self, 'drives') and self.drives:
            current_paths = {d['path']: d for d in drives if not d.get('is_system')}
            last_paths = {d['path']: d for d in self.drives if not d.get('is_system')}
            
            added = set(current_paths.keys()) - set(last_paths.keys())
            removed = set(last_paths.keys()) - set(current_paths.keys())
            
            for p in added:
                model = current_paths[p].get('model', 'Unknown')
                size = current_paths[p].get('size_str', 'Unknown')
                self.terminal_log.append(f"[+] Device Connected: {p} - {model} ({size})")
            for p in removed:
                model = last_paths[p].get('model', 'Unknown')
                self.terminal_log.append(f"[-] Device Disconnected: {p} - {model}")

        # Preserve current selection
        current_sel_path = self.selected_drive["path"] if self.selected_drive else None
        
        # Avoid blinking the UI unnecessarily if nothing changed
        if hasattr(self, 'drives') and self.drives == drives and not self.drive_list.count() == 0:
            print(f"[UI] No changes detected, skipping UI update")
            return
        
        print(f"[UI] Updating drive list UI")
        self.drive_list.clear() # type: ignore
        self.drives = drives
        
        non_system_drives = []
        
        # Check if no drives found
        if not drives:
            print(f"[UI] No drives detected - showing empty message")
            self.drive_list.addItem("⚠️ No Devices Detected") # type: ignore
            
            for i in range(self.drive_list.count()):
                item = self.drive_list.item(i) # type: ignore
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable) # type: ignore
                item.setForeground(QColor("#EF4444")) # type: ignore
            return
        
        print(f"[UI] Adding {len(drives)} drive(s) to list")
        for i, d in enumerate(self.drives):
            icon = "💾" if d.get("is_system") else "💽"
            
            # Format: Disk [Path - Model | Size]
            device_display = f"{icon}  [{d['path']}]"
            device_display += f"\n     └─ Model: {d['model']}"
            device_display += f" | Size: {d['size_str']}"
            
            if d.get("is_system"):
                if engine.TEST_MODE_ALLOW_SYSTEM_DRIVE:
                    device_display += " [AVAILABLE FOR TESTING]"
                else:
                    device_display += " [SYSTEM DISK - PROTECTED]"
            else:
                non_system_drives.append((i, d))
                device_display += " [SAFE TO WIPE]"
                
            self.drive_list.addItem(device_display) # type: ignore
            # Disable selection if system (unless test mode)
            if d.get("is_system") and not engine.TEST_MODE_ALLOW_SYSTEM_DRIVE:
                item = self.drive_list.item(i) # type: ignore
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable) # type: ignore
                item.setForeground(QColor("#EF4444")) # type: ignore
                item.setBackground(QColor("#18181B")) # type: ignore
            else:
                item = self.drive_list.item(i) # type: ignore
                item.setForeground(QColor("#06B6D4")) # type: ignore

        # Show info about available devices
        if len(non_system_drives) == 0:
            print(f"[UI] No external drives found - showing action required")
            self.drive_list.addItem("⚠️ No External Devices Found") # type: ignore
            for i in range(len(self.drives), self.drive_list.count()):
                item = self.drive_list.item(i) # type: ignore
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable) # type: ignore
                    item.setForeground(QColor("#F59E0B")) # type: ignore
        
        # Auto-select single device or restore selection
        elif len(non_system_drives) == 1:
            idx = non_system_drives[0][0]
            print(f"[UI] Auto-selecting single device at index {idx}")
            self.drive_list.setCurrentRow(idx)
            print(f"[DEBUG] Auto-selected single device: {self.drives[idx]['path']}")
        elif current_sel_path:
            for i, d in enumerate(self.drives):
                if d["path"] == current_sel_path and not d.get("is_system"):
                    self.drive_list.setCurrentRow(i)
                    break

    def on_drive_selected(self):
        sel = self.drive_list.selectedIndexes() # type: ignore
        if sel:
            idx = sel[0].row()
            d = self.drives[idx]
            if not d.get("is_system"):
                self.selected_drive = d
                self.icon_lbl.setText("✅")
                self.icon_lbl.setStyleSheet(f"color: {COLORS['success']};")
                
                # Enhanced device info display
                device_info = f"""<b>✓ DEVICE SELECTED</b>
<br/>━━━━━━━━━━━━━━━━━━━━━━━━
<br/><b>Device Path:</b> <span style='color:{COLORS['accent']}'>{d['path']}</span>
<br/><b>Model:</b> {d['model']}
<br/><b>Size:</b> <span style='color:{COLORS['success']}'>{d['size_str']}</span>
<br/><b>Type:</b> External Drive
<br/>━━━━━━━━━━━━━━━━━━━━━━━━
<br/><span style='color:{COLORS['warning']}; font-size: 10px;'>⚠️ All data will be permanently erased</span>"""
                
                self.drive_info_lbl.setText(device_info)
                self.start_btn.setEnabled(True)
                return
                
        self.start_btn.setEnabled(False)
        self.selected_drive = None
        self.icon_lbl.setText("🔌")
        self.icon_lbl.setStyleSheet(f"color: white;")
        self.drive_info_lbl.setText("Waiting for device selection...")


    def attempt_start(self):
        if not self.selected_drive: return
        op_id = self.operator_input.text().strip()
        if not op_id:
            QMessageBox.warning(self, "Input Required", "Please enter an Operator ID.")
            return

        dialog = TermsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Ask for explicit application access to the selected device
            reply = QMessageBox.question(
                self,
                "Allow Device Access",
                f"Do you allow EcoWipe to access and modify the following device?\n\n{self.selected_drive['path']} - {self.selected_drive['model']}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.start_wipe()

    def start_wipe(self):
        self.central_widget.setCurrentIndex(1)
        self.progress_bar.setValue(0)
        self.lbl_progress_pct.setText("0%")
        self.wipe_status_log.clear()
        self.wipe_status_log.append("Starting wipe engine...")
        
        self.start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        method = self.method_combo.currentText()
        op = self.operator_input.text().strip()
        
        # Update Info in Wipe Screen
        self.lbl_w_device.setText(f"{self.selected_drive['path']} - {self.selected_drive['model']}")
        self.lbl_w_size.setText(self.selected_drive['size_str'])
        self.lbl_w_method.setText(method)
        self.lbl_w_operator.setText(op)
        
        # Number of passes info
        if "3-Pass" in method:
            self.lbl_pass_info.setText("Pass 1 of 3")
        else:
            self.lbl_pass_info.setText("Pass 1 of 1")
            
        self.cancel_wipe_btn.setEnabled(True)
        self.wipe_title.setText("Secure Wipe in Progress")
        self.wipe_title.setStyleSheet(f"color: {COLORS['warning']};")
        
        self.wiper_thread = WiperThread(
            self.selected_drive["path"],
            self.selected_drive["size_bytes"],
            method,
            op
        )
        self.wiper_thread.progress.connect(self.update_progress)
        self.wiper_thread.status.connect(self.update_status)
        self.wiper_thread.finished_wipe.connect(self.on_wipe_finished)
        self.wiper_thread.start()

    def update_progress(self, val):
        self.progress_bar.setValue(val)
        self.lbl_progress_pct.setText(f"{val}%")

    def update_status(self, msg):
        self.wipe_status_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
        # Auto-scroll
        self.wipe_status_log.verticalScrollBar().setValue(self.wipe_status_log.verticalScrollBar().maximum())
        
        # Check for verification phase
        if "Verification" in msg:
            self.wipe_title.setText("Verifying wipe integrity...")
            self.wipe_title.setStyleSheet(f"color: {COLORS['accent']};")

    def cancel_wipe(self):
        if self.wiper_thread and self.wiper_thread.isRunning():
            self.cancel_wipe_btn.setEnabled(False)
            self.update_status("Cancelling... Please wait for current block to finish.")
            self.wiper_thread.cancel()

    def on_wipe_finished(self, success, message, ver_status):
        self.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if success:
            self.central_widget.setCurrentIndex(2) # Success Screen
            self.qr_label.clear()
            
            # Generate Certificate with new format
            device_model = self.selected_drive.get('model', 'Unknown')
            device_serial = self.selected_drive.get('serial', 'UNKNOWN')
            self.cert_file, self.qr_file, p_hash, c_id = generate_certificate(
                self.selected_drive["path"],
                device_model,
                device_serial,
                self.selected_drive["size_str"],
                self.method_combo.currentText(),
                self.operator_input.text().strip(),
                self.start_time,
                self.end_time,
                ver_status
            )
            
            # Populate Detail Screen
            self.lbl_res_device.setText(f"{self.selected_drive['path']} - {self.selected_drive['model']}")
            self.lbl_res_size.setText(self.selected_drive['size_str'])
            self.lbl_res_method.setText(self.method_combo.currentText())
            self.lbl_res_operator.setText(self.operator_input.text().strip())
            self.lbl_res_start.setText(self.start_time)
            self.lbl_res_end.setText(self.end_time)
            
            ver_color = COLORS['success'] if ver_status == "SUCCESS" else COLORS['warning']
            self.lbl_res_verify.setText(ver_status)
            self.lbl_res_verify.setStyleSheet(f"color: {ver_color}; border: none;")
            
            self.lbl_res_hash.setText(p_hash)
            
            # Actions Setup
            self.btn_open_cert.clicked.disconnect() if hasattr(self, '_open_cert_conn') else None
            self._open_cert_conn = self.btn_open_cert.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(self.cert_file))))
            
            self.btn_save_qr.clicked.disconnect() if hasattr(self, '_save_qr_conn') else None
            self._save_qr_conn = self.btn_save_qr.clicked.connect(self.save_qr_image)
            
            # Display QR
            if os.path.exists(self.qr_file):
                pixmap = QPixmap(self.qr_file)
                self.qr_label.setPixmap(pixmap.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio))
                
        else:
            # Wipe was interrupted
            self.wipe_title.setText("WIPE INTERRUPTED")
            self.wipe_title.setStyleSheet("color: #DC2626;") # Red
            self.update_status("Wipe interrupted. Device may not be secure. No certificate generated.")
            self.cancel_wipe_btn.setText("RETURN TO DASHBOARD")
            self.cancel_wipe_btn.setEnabled(True)
            self.cancel_wipe_btn.clicked.disconnect()
            self.cancel_wipe_btn.clicked.connect(self.return_to_dashboard)

    def save_qr_image(self):
        if hasattr(self, 'qr_file') and os.path.exists(self.qr_file):
            save_path, _ = QFileDialog.getSaveFileName(self, "Save QR Code", "ecowipe_qr.png", "Images (*.png)")
            if save_path:
                shutil.copy2(self.qr_file, save_path)
                QMessageBox.information(self, "Saved", f"QR Code saved to:\n{save_path}")

    def return_to_dashboard(self):
        # Reset State and UI
        self.selected_drive = None
        self.start_btn.setEnabled(False)
        self.drive_info_lbl.setText("Waiting for device selection...")
        self.icon_lbl.setText("🔌")
        self.icon_lbl.setStyleSheet(f"color: white;")
        
        self.operator_input.clear()
        
        # Re-attach cancel event correctly for next run
        try: self.cancel_wipe_btn.clicked.disconnect()
        except Exception: pass
        self.cancel_wipe_btn.clicked.connect(self.cancel_wipe)
        self.cancel_wipe_btn.setText("ABORT OPERATION")
        
        # Force redraw list
        if self.drive_list.count() > 0:
            self.drive_list.clearSelection() # type: ignore
            
        self.central_widget.setCurrentIndex(0)
        self.refresh_drives()
