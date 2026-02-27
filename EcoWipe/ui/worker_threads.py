"""
Enterprise Data Sanitization Platform
UI Worker Threads
"""
from PyQt6.QtCore import QThread, pyqtSignal
import time
from typing import List, Any

import sys
import os
# Ensure core can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.device_validator import DeviceValidator, ValidatedDevice
from core.logging_engine import log_error_event

class DeviceScannerThread(QThread):
    """
    Background thread for continuously scanning for valid USB devices.
    Ensures the UI thread is never blocked by WMI queries.
    """
    drives_updated = pyqtSignal(list)  # Emits List[ValidatedDevice]
    error_occurred = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_running = True
        self._force_refresh = False
        self.validator = DeviceValidator()
        self._last_drives: List[ValidatedDevice] = []

    def run(self):
        """Main loop for the scanner thread."""
        while self._is_running:
            try:
                current_drives = self.validator.get_valid_usb_drives()
                
                # Check if the list of drives has changed (by comparing device IDs)
                current_ids = {d.device_id for d in current_drives}
                last_ids = {d.device_id for d in self._last_drives}
                
                if current_ids != last_ids or self._force_refresh:
                    self.drives_updated.emit(current_drives)
                    self._last_drives = current_drives
                    self._force_refresh = False
                    
            except Exception as e:
                log_error_event("worker_threads", "DeviceScannerThread.run", f"Scanner error: {e}")
                self.error_occurred.emit(str(e))
                
            # Sleep in small increments to allow quick cancellation
            for _ in range(20): # 2 seconds total
                if not self._is_running or self._force_refresh:
                    break
                time.sleep(0.1)

    def trigger_refresh(self):
        """Force an immediate refresh of the device list."""
        self._force_refresh = True

    def stop(self):
        """Safely stop the thread."""
        self._is_running = False
        self.wait()
