"""
Enterprise Data Sanitization Platform
Safe Windows API Wrappers
"""
import ctypes
from ctypes import wintypes
from typing import Optional, Tuple
import os

import sys
# Ensure utils can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.constants import (
    GENERIC_READ, GENERIC_WRITE, FILE_SHARE_READ, FILE_SHARE_WRITE,
    OPEN_EXISTING, INVALID_HANDLE_VALUE, FSCTL_LOCK_VOLUME,
    FSCTL_DISMOUNT_VOLUME, FSCTL_UNLOCK_VOLUME
)

kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

# Define CreateFileW signature
kernel32.CreateFileW.argtypes = [
    wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
    ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE
]
kernel32.CreateFileW.restype = wintypes.HANDLE

# Define DeviceIoControl signature
kernel32.DeviceIoControl.argtypes = [
    wintypes.HANDLE, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD,
    wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p
]
kernel32.DeviceIoControl.restype = wintypes.BOOL

# Define CloseHandle signature
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL

def get_device_handle(device_path: str, write_access: bool = False) -> int:
    """
    Safely acquire a handle to a physical device or volume.
    
    Args:
        device_path: The Windows device path (e.g., '\\\\.\\PhysicalDrive1').
        write_access: Whether to request write access.
        
    Returns:
        A valid Windows handle integer.
        
    Raises:
        OSError: If the handle cannot be acquired.
    """
    access = GENERIC_READ | GENERIC_WRITE if write_access else GENERIC_READ
    share_mode = FILE_SHARE_READ | FILE_SHARE_WRITE
    
    handle = kernel32.CreateFileW(
        device_path,
        access,
        share_mode,
        None,
        OPEN_EXISTING,
        0,
        None
    )
    
    if handle == INVALID_HANDLE_VALUE:
        error_code = ctypes.get_last_error()
        raise OSError(f"Failed to open device {device_path}. Error code: {error_code}")
        
    return handle

def close_handle(handle: int) -> None:
    """
    Safely close a Windows handle.
    
    Args:
        handle: The Windows handle to close.
    """
    if handle and handle != INVALID_HANDLE_VALUE:
        kernel32.CloseHandle(handle)

def _send_ioctl(handle: int, ioctl_code: int) -> bool:
    """
    Send a DeviceIoControl command with no input/output buffers.
    
    Args:
        handle: The device handle.
        ioctl_code: The IOCTL code to send.
        
    Returns:
        True if successful, False otherwise.
    """
    bytes_returned = wintypes.DWORD(0)
    result = kernel32.DeviceIoControl(
        handle,
        ioctl_code,
        None, 0,
        None, 0,
        ctypes.byref(bytes_returned),
        None
    )
    return bool(result)

def lock_volume(handle: int) -> bool:
    """Lock a volume for exclusive access."""
    return _send_ioctl(handle, FSCTL_LOCK_VOLUME)

def dismount_volume(handle: int) -> bool:
    """Dismount a volume."""
    return _send_ioctl(handle, FSCTL_DISMOUNT_VOLUME)

def unlock_volume(handle: int) -> bool:
    """Unlock a previously locked volume."""
    return _send_ioctl(handle, FSCTL_UNLOCK_VOLUME)
