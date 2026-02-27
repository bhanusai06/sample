import sys
from PyQt6.QtWidgets import QApplication, QSplashScreen, QMainWindow, QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QParallelAnimationGroup
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QLinearGradient
from ui import MainWindow
from utils import is_admin, COLORS
from models import init_db
import ctypes

class AnimatedSplash(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(700, 500)
        self.setWindowOpacity(0.0)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addStretch()  # Add stretch at top to center vertically
        
        # Add visual components
        title = QLabel("EcoWipe")
        title.setFont(QFont("Segoe UI", 56, QFont.Weight.Bold))
        title.setStyleSheet("color: #06B6D4; letter-spacing: 4px; text-shadow: 0 0 20px rgba(6, 182, 212, 0.5);")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        
        subtitle = QLabel("Secure Offline Disk Sanitization")
        subtitle.setFont(QFont("Segoe UI", 14))
        subtitle.setStyleSheet("color: #94A3B8; letter-spacing: 2px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addSpacing(20)
        
        self.status_lbl = QLabel("Initializing Core Engine...")
        self.status_lbl.setFont(QFont("Segoe UI", 11))
        self.status_lbl.setStyleSheet("color: #10B981; font-weight: bold;")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)
        self.progress.setFixedSize(400, 6)
        self.progress.setStyleSheet(f"""
            QProgressBar {{ 
                border: none; 
                background-color: #1E293B; 
                border-radius: 3px; 
            }}
            QProgressBar::chunk {{ 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                           stop:0 #06B6D4,
                                           stop:1 #0EA5E9);
                border-radius: 3px;
            }}
        """)
        layout.addWidget(self.progress, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addStretch()  # Add stretch at bottom to center vertically
        
        self.val = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create gradient background
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, QColor("#0F172A"))
        grad.setColorAt(1.0, QColor("#1E293B"))
        painter.setBrush(grad)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 15, 15)
        
        # Add subtle border
        painter.setPen(QColor("#334155"))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 14, 14)

    def fade_in(self):
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(1000)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.anim.start()
        self.timer.start(40)
        
    def update_progress(self):
        self.val += 1
        self.progress.setValue(self.val)
        if self.val == 30:
            self.status_lbl.setText("Scanning Hardware Interfaces...")
        elif self.val == 60:
            self.status_lbl.setText("Loading Security Protocols...")
        elif self.val == 85:
            self.status_lbl.setText("Mounting Application Dashboard...")
        elif self.val >= 100:
            self.timer.stop()

def main():
    if not is_admin():
        # Try to elevate privileges using ShellExecute with 'runas' verb
        try:
            import os
            import ctypes
            
            # Get the current script/executable path
            script = sys.argv[0]
            params = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else ''
            
            # ShellExecute with 'runas' verb to request admin privileges
            ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", script, params, None, 1)
            
            # If ShellExecute returns > 32, it was successful
            if ret > 32:
                sys.exit(0)
            else:
                # User denied the UAC prompt or ShellExecute failed
                ctypes.windll.user32.MessageBoxW(0, 
                    "EcoWipe requires Administrator privileges to detect and wipe disks.\n\n"
                    "Please grant administrator access when prompted, or right-click the executable and select 'Run as administrator'.", 
                    "Administrator Privileges Required", 0x10)
                sys.exit(1)
        except Exception as e:
            # Fallback: Show error message
            ctypes.windll.user32.MessageBoxW(0, 
                f"Failed to elevate privileges: {str(e)}\n\n"
                "Please right-click the executable and select 'Run as administrator'.", 
                "Elevation Error", 0x10)
            sys.exit(1)
        
    init_db()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    splash = AnimatedSplash()
    splash.show()
    splash.fade_in()
    
    app.processEvents()
    
    main_window = MainWindow()
    
    def close_splash():
        main_window.show()
        splash.close()
        
    QTimer.singleShot(5000, close_splash)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
