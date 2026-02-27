"""
Enterprise Data Sanitization Platform
Secure Wipe Engine
"""
import hashlib
import time
from typing import Optional, Callable, Dict, Any
from PyQt6.QtCore import QThread, pyqtSignal

import sys
import os
# Ensure core and utils can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.state_machine import WipeStateMachine, WipeState
from core.device_validator import DeviceValidator, ValidatedDevice
from core.wipe_strategies import get_strategy, WipeStrategy
from core.exception_types import WipeEngineError, DeviceValidationError
from core.logging_engine import wipe_logger, log_error_event, log_security_event
from utils.win_api import get_device_handle, close_handle, lock_volume, dismount_volume, unlock_volume
from utils.constants import WIPE_BLOCK_SIZE_BYTES, INVALID_HANDLE_VALUE

class WipeEngine(QThread):
    """
    QThread worker that orchestrates the secure wipe process.
    Strictly follows the state machine and uses safe Win32 API calls.
    """
    # Signals for UI updates
    progress_updated = pyqtSignal(int, str)  # percentage, status_message
    wipe_completed = pyqtSignal(dict)        # result_data
    wipe_failed = pyqtSignal(str)            # error_message

    def __init__(self, device_id: str, method_name: str, operator_name: str):
        super().__init__()
        self.device_id = device_id
        self.method_name = method_name
        self.operator_name = operator_name
        
        self.state_machine = WipeStateMachine()
        self.validator = DeviceValidator()
        self.strategy = get_strategy(method_name)
        
        self.device: Optional[ValidatedDevice] = None
        self.handle: int = INVALID_HANDLE_VALUE
        
        self.pre_hash: str = ""
        self.post_hash: str = ""
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        
        self._is_cancelled = False

    def cancel(self):
        """Request cancellation of the wipe process."""
        self._is_cancelled = True
        wipe_logger.warning(f"Wipe cancellation requested for {self.device_id}")

    def run(self):
        """Main execution loop for the QThread."""
        try:
            self.start_time = time.time()
            wipe_logger.info(f"Starting wipe operation on {self.device_id} by {self.operator_name}")
            
            self._validate_device()
            self._lock_and_dismount()
            self._compute_pre_hash()
            self._perform_wipe()
            self._compute_post_hash()
            self._finalize()
            
        except Exception as e:
            log_error_event("wipe_engine", "run", f"Wipe failed: {e}", exc_info=True)
            self.state_machine.transition_to(WipeState.ERROR)
            self.wipe_failed.emit(str(e))
        finally:
            self._safe_release()

    def _validate_device(self):
        """State: IDLE -> DEVICE_VALIDATED"""
        self.progress_updated.emit(0, "Validating device...")
        self.device = self.validator.validate_device_for_wipe(self.device_id)
        self.state_machine.transition_to(WipeState.DEVICE_VALIDATED)

    def _lock_and_dismount(self):
        """State: DEVICE_VALIDATED -> LOCKED"""
        self.progress_updated.emit(5, "Locking and dismounting volume...")
        
        try:
            # Acquire handle with write access
            self.handle = get_device_handle(self.device_id, write_access=True)
            
            # Lock and dismount
            if not lock_volume(self.handle):
                raise WipeEngineError("Failed to lock volume for exclusive access.")
            if not dismount_volume(self.handle):
                raise WipeEngineError("Failed to dismount volume.")
                
            self.state_machine.transition_to(WipeState.LOCKED)
            wipe_logger.info(f"Successfully locked and dismounted {self.device_id}")
            
        except Exception as e:
            raise WipeEngineError(f"Lock/Dismount failed: {e}")

    def _compute_hash(self, phase: str) -> str:
        """Helper to compute SHA-256 of the drive."""
        if self.handle == INVALID_HANDLE_VALUE:
            raise WipeEngineError("Invalid handle during hash computation.")
            
        hasher = hashlib.sha256()
        bytes_read = 0
        total_bytes = self.device.size_bytes
        
        # Seek to beginning
        import ctypes
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel32.SetFilePointer(self.handle, 0, None, 0) # FILE_BEGIN
        
        buffer = ctypes.create_string_buffer(WIPE_BLOCK_SIZE_BYTES)
        bytes_read_out = ctypes.wintypes.DWORD(0)
        
        while bytes_read < total_bytes:
            if self._is_cancelled:
                raise WipeEngineError("Operation cancelled by user.")
                
            read_size = min(WIPE_BLOCK_SIZE_BYTES, total_bytes - bytes_read)
            
            success = kernel32.ReadFile(
                self.handle, buffer, read_size, ctypes.byref(bytes_read_out), None
            )
            
            if not success or bytes_read_out.value == 0:
                error_code = ctypes.get_last_error()
                raise WipeEngineError(f"Failed to read drive for hashing. Error: {error_code}")
                
            hasher.update(buffer.raw[:bytes_read_out.value])
            bytes_read += bytes_read_out.value
            
            # Update progress (0-10% for pre, 90-100% for post)
            if phase == "pre":
                prog = 5 + int((bytes_read / total_bytes) * 5)
                self.progress_updated.emit(prog, f"Computing pre-wipe hash... {int((bytes_read/total_bytes)*100)}%")
            else:
                prog = 90 + int((bytes_read / total_bytes) * 10)
                self.progress_updated.emit(prog, f"Computing post-wipe hash... {int((bytes_read/total_bytes)*100)}%")
                
        return hasher.hexdigest()

    def _compute_pre_hash(self):
        """State: LOCKED -> PRE_HASHED"""
        self.state_machine.assert_state(WipeState.LOCKED)
        self.pre_hash = self._compute_hash("pre")
        wipe_logger.info(f"Pre-wipe hash: {self.pre_hash}")
        self.state_machine.transition_to(WipeState.PRE_HASHED)

    def _perform_wipe(self):
        """State: PRE_HASHED -> OVERWRITING"""
        self.state_machine.assert_state(WipeState.PRE_HASHED)
        self.state_machine.transition_to(WipeState.OVERWRITING)
        
        import ctypes
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        
        total_bytes = self.device.size_bytes
        passes = self.strategy.passes
        
        for pass_idx in range(passes):
            # Seek to beginning for each pass
            kernel32.SetFilePointer(self.handle, 0, None, 0)
            
            bytes_written = 0
            block_data = self.strategy.get_block(pass_idx)
            
            while bytes_written < total_bytes:
                if self._is_cancelled:
                    raise WipeEngineError("Operation cancelled by user.")
                    
                write_size = min(WIPE_BLOCK_SIZE_BYTES, total_bytes - bytes_written)
                bytes_written_out = ctypes.wintypes.DWORD(0)
                
                success = kernel32.WriteFile(
                    self.handle, block_data, write_size, ctypes.byref(bytes_written_out), None
                )
                
                if not success or bytes_written_out.value == 0:
                    error_code = ctypes.get_last_error()
                    raise WipeEngineError(f"Write failed at offset {bytes_written}. Error: {error_code}")
                    
                bytes_written += bytes_written_out.value
                
                # Calculate overall progress (10% to 90%)
                pass_progress = bytes_written / total_bytes
                overall_progress = 10 + int(((pass_idx + pass_progress) / passes) * 80)
                
                self.progress_updated.emit(
                    overall_progress, 
                    f"Wiping (Pass {pass_idx+1}/{passes})... {int(pass_progress*100)}%"
                )
                
            # Flush buffers after each pass
            kernel32.FlushFileBuffers(self.handle)
            wipe_logger.info(f"Completed pass {pass_idx+1}/{passes}")

    def _compute_post_hash(self):
        """State: OVERWRITING -> VERIFYING"""
        self.state_machine.assert_state(WipeState.OVERWRITING)
        self.state_machine.transition_to(WipeState.VERIFYING)
        
        self.post_hash = self._compute_hash("post")
        wipe_logger.info(f"Post-wipe hash: {self.post_hash}")
        
        if self.pre_hash == self.post_hash and self.device.size_bytes > 0:
            # If hashes match, the data didn't change (wipe failed silently)
            raise WipeEngineError("Pre and Post hashes match. Wipe operation failed to modify data.")

    def _finalize(self):
        """State: VERIFYING -> COMPLETED"""
        self.state_machine.assert_state(WipeState.VERIFYING)
        self.end_time = time.time()
        self.state_machine.transition_to(WipeState.COMPLETED)
        
        result = {
            "device_id": self.device.device_id,
            "model": self.device.model,
            "serial": self.device.serial_number,
            "size_bytes": self.device.size_bytes,
            "method": self.strategy.name,
            "passes": self.strategy.passes,
            "nist_standard": self.strategy.nist_standard,
            "operator": self.operator_name,
            "pre_hash": self.pre_hash,
            "post_hash": self.post_hash,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": "SUCCESS"
        }
        
        wipe_logger.info(f"Wipe completed successfully for {self.device_id}")
        self.wipe_completed.emit(result)

    def _safe_release(self):
        """Ensure resources are released regardless of success or failure."""
        try:
            if self.handle != INVALID_HANDLE_VALUE:
                unlock_volume(self.handle)
                close_handle(self.handle)
                self.handle = INVALID_HANDLE_VALUE
                wipe_logger.info(f"Released handle for {self.device_id}")
        except Exception as e:
            log_error_event("wipe_engine", "_safe_release", f"Error releasing handle: {e}")
            
        self.state_machine.transition_to(WipeState.SAFE_RELEASE)
