"""
Enterprise Data Sanitization Platform
Constants and Magic Numbers
"""
from typing import Final

# Wipe Configuration
WIPE_BLOCK_SIZE_BYTES: Final[int] = 4 * 1024 * 1024  # 4MB constant block size
MAX_DRIVE_SIZE_BYTES: Final[int] = 100 * 1024**4     # 100 TB max supported

# Logging Configuration
LOG_DIR: Final[str] = "logs"
LOG_FORMAT: Final[str] = "[%(asctime)s] [%(levelname)s] [%(module)s] [%(funcName)s] %(message)s"
DATE_FORMAT: Final[str] = "%Y-%m-%dT%H:%M:%SZ"

# Cryptography
RSA_KEY_SIZE: Final[int] = 4096

# QR Code
QR_BOX_SIZE: Final[int] = 12
QR_BORDER: Final[int] = 4

# Win32 API Constants
GENERIC_READ: Final[int] = 0x80000000
GENERIC_WRITE: Final[int] = 0x40000000
FILE_SHARE_READ: Final[int] = 0x00000001
FILE_SHARE_WRITE: Final[int] = 0x00000002
OPEN_EXISTING: Final[int] = 3
INVALID_HANDLE_VALUE: Final[int] = -1

# IOCTL Codes
FSCTL_LOCK_VOLUME: Final[int] = 0x00090018
FSCTL_UNLOCK_VOLUME: Final[int] = 0x0009001C
FSCTL_DISMOUNT_VOLUME: Final[int] = 0x00090020
IOCTL_DISK_GET_DRIVE_GEOMETRY_EX: Final[int] = 0x000700A0
