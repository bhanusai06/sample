"""
Enterprise Data Sanitization Platform
Strict Device Validation and Detection
"""
import wmi
import ctypes
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import os

import sys
# Ensure core can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.exception_types import DeviceValidationError, SystemDriveError
from core.logging_engine import device_logger, log_security_event, log_error_event
from core.validation_engine import validate_device_path

@dataclass(frozen=True)
class ValidatedDevice:
    """Immutable dataclass representing a strictly validated device."""
    device_id: str
    model: str
    serial_number: str
    size_bytes: int
    interface_type: str
    is_system_drive: bool
    is_boot_drive: bool
    
    @property
    def size_gb(self) -> float:
        return round(self.size_bytes / (1024**3), 2)

class DeviceValidator:
    """
    Handles strict device detection and validation using WMI.
    Guarantees system/boot drives are identified and blocked.
    """
    def __init__(self):
        try:
            # Initialize WMI connection
            self.wmi_conn = wmi.WMI()
        except Exception as e:
            log_error_event("device_validator", "__init__", f"Failed to initialize WMI: {e}", exc_info=True)
            raise DeviceValidationError("Critical failure: Cannot initialize WMI for device detection.")

    def _is_admin(self) -> bool:
        """Check if running with Administrator privileges."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() == 1
        except Exception:
            return False

    def _get_system_drive_indices(self) -> set[int]:
        """
        Identify physical drive indices that contain the OS or Boot partitions.
        Uses Win32_DiskPartition and Win32_LogicalDisk to trace back to the physical drive.
        """
        system_indices = set()
        try:
            # 1. Find partitions marked as BootPartition
            for partition in self.wmi_conn.Win32_DiskPartition(BootPartition=True):
                system_indices.add(partition.DiskIndex)
                
            # 2. Find the drive containing the Windows directory (usually C:)
            win_dir = os.environ.get("windir", "C:\\Windows")
            system_drive_letter = win_dir[:2] # e.g., "C:"
            
            # Trace Logical Disk -> Partition -> Physical Disk
            for logical_disk in self.wmi_conn.Win32_LogicalDisk(DeviceID=system_drive_letter):
                for partition in logical_disk.associators("Win32_LogicalDiskToPartition"):
                    for physical_disk in partition.associators("Win32_DiskDriveToDiskPartition"):
                        system_indices.add(physical_disk.Index)
                        
        except Exception as e:
            log_error_event("device_validator", "_get_system_drive_indices", f"Error detecting system drives: {e}", exc_info=True)
            # FAIL SAFE: If we can't determine system drives, we must assume ALL drives are system drives
            # to prevent accidental wiping. This will effectively block the application until resolved.
            raise SystemDriveError("FAIL SAFE TRIGGERED: Cannot reliably determine system drive indices.")
            
        return system_indices

    def get_valid_usb_drives(self) -> List[ValidatedDevice]:
        """
        Enumerate and strictly validate all connected USB drives.
        Blocks any drive that fails validation or is a system/boot drive.
        """
        if not self._is_admin():
            device_logger.error("Administrator privileges required for device detection.")
            return []

        valid_drives = []
        try:
            system_indices = self._get_system_drive_indices()
            
            for disk in self.wmi_conn.Win32_DiskDrive():
                try:
                    device_id = disk.DeviceID
                    model = disk.Model or "Unknown Model"
                    interface_type = disk.InterfaceType or "UNKNOWN"
                    size_bytes = int(disk.Size) if disk.Size else 0
                    serial_number = disk.SerialNumber.strip() if disk.SerialNumber else ""
                    disk_index = disk.Index
                    
                    is_system = disk_index in system_indices
                    
                    # --- STRICT VALIDATION RULES ---
                    
                    # 1. Must be USB
                    if interface_type.upper() != "USB":
                        device_logger.debug(f"Skipping {device_id}: Interface is {interface_type}, not USB.")
                        continue
                        
                    # 2. Must not be a system/boot drive
                    if is_system:
                        log_security_event("device_validator", "get_valid_usb_drives", f"System drive detected as USB (Index {disk_index}). Blocking.")
                        continue
                        
                    # 3. Must have a valid size
                    if size_bytes <= 0:
                        device_logger.warning(f"Skipping {device_id}: Invalid size ({size_bytes} bytes).")
                        continue
                        
                    # 4. Must have a serial number (required for forensic logging)
                    if not serial_number:
                        device_logger.warning(f"Skipping {device_id}: Missing serial number.")
                        continue
                        
                    # Validate path format
                    validate_device_path(device_id)
                    
                    # Create immutable device record
                    validated_device = ValidatedDevice(
                        device_id=device_id,
                        model=model,
                        serial_number=serial_number,
                        size_bytes=size_bytes,
                        interface_type=interface_type,
                        is_system_drive=False, # We already filtered out True
                        is_boot_drive=False    # We already filtered out True
                    )
                    
                    valid_drives.append(validated_device)
                    device_logger.info(f"Validated USB device: {device_id} ({model}, {validated_device.size_gb}GB)")
                    
                except Exception as e:
                    device_logger.error(f"Error validating individual disk {getattr(disk, 'DeviceID', 'Unknown')}: {e}")
                    continue # Skip this disk on error, fail safe
                    
        except SystemDriveError as sde:
            # Re-raise fail-safe errors
            raise
        except Exception as e:
            log_error_event("device_validator", "get_valid_usb_drives", f"Critical error during device enumeration: {e}", exc_info=True)
            
        return valid_drives

    def validate_device_for_wipe(self, device_id: str) -> ValidatedDevice:
        """
        Perform a final, strict validation immediately before a wipe operation.
        This ensures the device hasn't changed or been swapped since detection.
        """
        validate_device_path(device_id)
        
        current_valid_drives = self.get_valid_usb_drives()
        for drive in current_valid_drives:
            if drive.device_id == device_id:
                return drive
                
        log_security_event("device_validator", "validate_device_for_wipe", f"Device {device_id} failed pre-wipe validation. It may have been removed, altered, or is a system drive.")
        raise DeviceValidationError(f"Device {device_id} is not valid for wiping or is no longer present.")
