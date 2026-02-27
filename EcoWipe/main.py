"""
Enterprise Data Sanitization Platform
Application Entry Point
"""
import sys
import ctypes
from PyQt6.QtWidgets import QApplication, QMessageBox

# Ensure the current directory is in the path
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow
from core.logging_engine import log_security_event

def is_admin() -> bool:
    """Check if the application is running with Administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() == 1
    except Exception:
        return False

def main():
    app = QApplication(sys.argv)
    
    # Enforce Administrator Privileges
    if not is_admin():
        log_security_event("main", "startup", "Application launched without Administrator privileges. Blocking execution.")
        QMessageBox.critical(
            None, 
            "Access Denied", 
            "EcoWipe Enterprise requires Administrator privileges to access physical drives.\n\n"
            "Please right-click the application and select 'Run as administrator'."
        )
        sys.exit(1)
        
    # Set application style
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
