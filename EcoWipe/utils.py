import ctypes
import os
import sys

def is_admin():
    """Check if the program is running with Administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() == 1
    except Exception:
        return False

def get_base_path():
    """Get the base path of the application, handling PyInstaller environment."""
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

# Design Constants
COLORS = {
    "background": "#0A0A0B",
    "panels": "#141417",
    "panel_border": "#27272A",
    "accent": "#0EA5E9",
    "warning": "#EF4444",
    "success": "#10B981",
    "text": "#F8FAFC",
    "text_muted": "#94A3B8"
}
